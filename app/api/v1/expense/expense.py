import os
import asyncio
import time as _time
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from io import BytesIO
from typing import Optional
from urllib.parse import quote

from fastapi import APIRouter, Query, UploadFile, File, Body, Header
from fastapi.responses import StreamingResponse
from app.log import logger
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Font, Alignment, Border, Side
from openpyxl.utils import get_column_letter
from tortoise.expressions import Q

from app.controllers.expense import (
    expense_project_controller,
    budget_code_controller,
    expense_code_controller,
    test_order_controller,
    daily_record_controller,
    monthly_settlement_controller,
    requirement_personnel_controller,
    engineer_attendance_controller,
    driver_attendance_controller,
    supplier_rate_controller,
)
from app.core.ctx import CTX_USER_ID
from app.models.expense import (
    ExpenseProject, BudgetCode, ExpenseCode, TestOrder,
    DailyRecord, MonthlySettlement, SettlementAttachment, ExpenseDiffRecord,
    RequirementPersonnel, EngineerAttendance, DriverAttendance, SupplierRate,
)
from app.models.admin import User
from app.schemas import Success, Fail, SuccessExtra
from app.schemas.expense import (
    ExpenseProjectCreate, ExpenseProjectUpdate,
    BudgetCodeCreate, BudgetCodeUpdate,
    ExpenseCodeCreate, ExpenseCodeUpdate,
    TestOrderCreate, TestOrderUpdate,
    DailyRecordCreate, DailyRecordUpdate,
    MonthlySettlementCreate, MonthlySettlementUpdate,
    SettlementAttachmentCreate, ExpenseDiffRecordCreate, ExpenseDiffRecordUpdate,
    RequirementPersonnelCreate, RequirementPersonnelUpdate,
    DriverAttendanceCreate, DriverAttendanceUpdate,
    EngineerAttendanceCreate, EngineerAttendanceUpdate,
    SupplierRateCreate, SupplierRateUpdate,
)
from app.models.admin import Menu
from app.schemas.menus import MenuType
from app.core.dependency import AuthControl

router = APIRouter(tags=["费用管理"])

async def _auto_sync_daily():
    """自动同步每日费用（优化版：仅处理最近60天，大幅减少处理量）"""
    import asyncio as _asyncio
    try:
        from app.models.expense import EngineerAttendance, DriverAttendance
        from decimal import Decimal as D

        # ★ 仅处理最近 10 天的考勤记录（手动同步只拉近期数据，快）
        ten_days_ago = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

        sr_list = await SupplierRate.all()
        # 按供应商名称分组，每组的记录按 effective_from 排序
        RATES_BY_DATE = {}
        for sr in sr_list:
            RATES_BY_DATE.setdefault(sr.name, []).append({
                "local": float(sr.local_rate), "trip": float(sr.trip_rate),
                "unit": sr.unit,
                "effective_from": sr.effective_from,
                "effective_to": sr.effective_to,
            })
        for rates in RATES_BY_DATE.values():
            rates.sort(key=lambda r: (r["effective_from"] or date.min, r["effective_to"] or date.max))

        def _calc_total(supplier_name, travel_status, normal_h, overtime_h, advance, record_date=None, requirement_date=None):
            """计算费用总额，根据供应商和日期从 SupplierRate 表取对应时间生效的单价。
            达安：按试验需求通过日期（requirement_date）取单价；
            育喆/驰恒：按工时产生日期（record_date）取单价。
            """
            sup = (supplier_name or "").strip()
            all_rates = RATES_BY_DATE.get(sup, RATES_BY_DATE.get("育喆", []))
            # 达安优先使用需求通过日期，否则退回到工时产生日期
            price_date = requirement_date if (sup == "达安" and requirement_date) else record_date
            cfg = None
            for r in all_rates:
                ef = r["effective_from"]
                et = r["effective_to"]
                if price_date:
                    if (ef is None or price_date >= ef) and (et is None or price_date <= et):
                        cfg = r
                        break
                else:
                    cfg = r
            if not cfg:
                cfg = all_rates[-1] if all_rates else {"local": 290, "trip": 356, "unit": "day"}
            is_trip = str(travel_status) == "出差" if travel_status else False
            r = cfg["trip"] if is_trip else cfg["local"]
            effective = r / 8 if cfg["unit"] == "day" else r
            return round((normal_h + overtime_h) * effective + advance, 2)

        # ★ 预加载：人员绑定关系 (test_order_no, person_name) -> supplier / requirement_date
        all_rp = await RequirementPersonnel.all().values("test_order_no", "outsourced_personnel", "supplier", "requirement_date", "start_date", "end_date")
        # 构建内存查找: test_order_no -> {person_name: supplier}
        rp_map = {}
        # 人员姓名 -> supplier（兜底用，处理 requirement_code 为"未匹配"导致按试验单查不到的情况）
        person_supplier = {}
        for rp in all_rp:
            tno = rp["test_order_no"]
            supplier = rp["supplier"] or ""
            personnel = (rp["outsourced_personnel"] or "").replace("，", ",").replace("、", ",").split(",")
            personnel = [n.strip() for n in personnel if n.strip()]
            if tno not in rp_map:
                rp_map[tno] = {}
            for pn in personnel:
                rp_map[tno][pn] = supplier
                if pn not in person_supplier and supplier:
                    person_supplier[pn] = supplier
        # 试验单号 -> 试验需求通过日期
        req_date_map = {}
        for rp in all_rp:
            tno = rp["test_order_no"]
            if tno and rp.get("requirement_date"):
                req_date_map[tno] = rp["requirement_date"]
        # ★ 人员姓名 → 试验单号列表（当考勤记录 requirement_code 为空时的兜底匹配）
        # 每条记录包含 test_order_no + 日期范围，用于按人员+日期匹配试验单
        person_to_test_order_map = {}
        for rp in all_rp:
            tno = rp["test_order_no"]
            if not tno:
                continue
            personnel = (rp["outsourced_personnel"] or "").replace("，", ",").replace("、", ",").split(",")
            personnel = [n.strip() for n in personnel if n.strip()]
            rec_info = {
                "test_order_no": tno,
                "start_date": rp.get("start_date"),
                "end_date": rp.get("end_date"),
            }
            for pn in personnel:
                person_to_test_order_map.setdefault(pn, []).append(rec_info)
        def _get_test_order_by_person(pname, rec_date):
            """根据人员姓名和日期，从人员绑定表中查找匹配的试验单号"""
            recs = person_to_test_order_map.get(pname, [])
            if not recs:
                return None
            # 优先匹配日期在范围内的记录
            for pr in recs:
                sd = pr.get("start_date")
                ed = pr.get("end_date")
                if sd and ed and sd <= rec_date <= ed:
                    return pr["test_order_no"]
            # 没有日期范围匹配，返回第一条
            return recs[0]["test_order_no"]
        def _get_supplier_fast(test_order_no, person_name, fallback):
            if test_order_no and test_order_no in rp_map:
                s = rp_map[test_order_no].get(person_name)
                if s:
                    return s
            # 按试验单查不到时，兜底按人员姓名查其所属供应商（保持工程师/驾驶员类别一致）
            if person_name in person_supplier:
                return person_supplier[person_name]
            return fallback or ""

        # ★ 预加载：全部已有 DailyRecord 用于去重（避免跨次/同次同步产生重复记录）
        # 去重 key：按 (person_name, record_date) 唯一 —— 同一人同一天只应有一条每日记录，
        # 即使多次同步解析到不同 project_id/test_order_id，也应更新已有记录而非新建。
        existing_daily = await DailyRecord.all().values("id", "project_id", "record_date", "person_name", "test_order_id", "source_id", "source_type")
        daily_index = {}          # (person_name, record_date) -> record dict
        daily_by_source = {}      # (source_id, source_type) -> record dict
        for d in existing_daily:
            pk = (d["person_name"], str(d["record_date"]))
            cur = daily_index.get(pk)
            # 存在重复时优先保留 id 最大者：与末尾清理 SQL 的 MAX(id) 保留策略一致，
            # 避免命中即将被删除的小 id 记录、导致最终保留的 MAX(id) 记录未被更新（test_order_id 残留为空等）
            if cur is None or d["id"] > cur["id"]:
                daily_index[pk] = d
            if d.get("source_id") and d.get("source_type"):
                sk = (d["source_id"], d["source_type"])
                cur2 = daily_by_source.get(sk)
                if cur2 is None or d["id"] > cur2["id"]:
                    daily_by_source[sk] = d
        # 同一次运行内待创建的 key 集合（防止同人同天被处理两次时重复建记录）
        pending_create = {}

        # ★ 预加载：仅最近 10 天的考勤记录
        engs = await EngineerAttendance.filter(record_date__gte=ten_days_ago).prefetch_related("project", "test_order")
        drvs = await DriverAttendance.filter(record_date__gte=ten_days_ago).prefetch_related("project", "test_order")
        # ★ 预加载：试验单号映射（用于通过 requirement_code 查找 test_order_id）
        to_by_req = {}
        to_project_map = {}  # test_order_id -> project_id（通过 TestOrder -> ExpenseCode -> Budget -> Project 链）
        # ★ 前缀索引：飞书 requirement_code 可能是简写（如 "H56D"），需前缀匹配完整 test_order_no
        to_by_prefix = {}
        for t in await TestOrder.all().prefetch_related("expense_code__budget__project"):
            to_by_req[t.test_order_no] = t.id
            if t.expense_code and t.expense_code.budget and t.expense_code.budget.project:
                to_project_map[t.id] = t.expense_code.budget.project.id
            # 提取前缀（如 H56D-202605199 → H56D），用于飞书简写需求编号的前缀匹配
            prefix = t.test_order_no.split("-")[0] if "-" in t.test_order_no else ""
            if prefix:
                to_by_prefix.setdefault(prefix, []).append(t.id)

        def _resolve_test_order_id(req_code, existing_to_id):
            """解析 requirement_code → test_order_id，支持精确匹配 + 前缀匹配。
            req_code 为空（飞书该天试验需求编号为空）时不关联试验单，避免错误关联到其他试验单。
            不使用考勤旧 test_order_id（existing_to_id），避免旧错误关联残留。"""
            if not req_code or req_code == "未匹配":
                # 飞书该天试验需求编号为空：不关联试验单
                return None
            # 精确匹配（不使用考勤旧 test_order_id，避免错误关联残留）
            tid = to_by_req.get(req_code)
            if tid:
                return tid
            # 3) 前缀匹配（飞书简写如 H56D → 匹配 H56D-202605199）
            prefix = req_code.split("-")[0] if "-" in req_code else req_code
            candidates = to_by_prefix.get(prefix, [])
            if candidates:
                # 如果只有一个，直接使用；多个时取第一个（如有日期/人员信息可进一步过滤）
                return candidates[0]
            return None

        # ── 第一阶段：内存中构建所有 DailyRecord 数据 ──
        to_create = []    # 待创建的 defaults dict
        to_update = []    # 待更新的 (existing_id, defaults)

        def _get_approval(appr1, appr2):
            """审批状态：任一通过即通过，任一驳回即驳回，否则待审批"""
            a1 = (appr1 or "").strip()
            a2 = (appr2 or "").strip()
            if a1 in ("通过", "批准", "已通过", "同意", "审核通过", "已审批") or \
               a2 in ("通过", "批准", "已通过", "同意", "审核通过", "已审批"):
                return "通过"
            if a1 in ("驳回", "已驳回", "拒绝", "不通过", "未通过") or \
               a2 in ("驳回", "已驳回", "拒绝", "不通过", "未通过"):
                return "驳回"
            return "待审批"

        # 处理工程师
        _eng_logged = 0
        _eng_skipped_no_project = 0
        for eng in engs:
            if not eng.project_id:
                _eng_skipped_no_project += 1
                if _eng_skipped_no_project <= 5:
                    logger.warning(
                        f"[DailySync] 工程师无项目(使用兜底id=1): person={eng.person_name}, date={eng.record_date}, "
                        f"requirement_code={eng.requirement_code}, test_order_id={eng.test_order_id}"
                    )
                # 不再跳过，继续处理（project_id 兜底为 1）
            if _eng_logged < 3:
                _eng_logged += 1
                logger.info(
                    f"[DailySync] 工程师审批: person={eng.person_name}, date={eng.record_date}, "
                    f"appr1={eng.approver1_result!r}, appr2={eng.approver2_result!r}, "
                    f"approval={_get_approval(eng.approver1_result, eng.approver2_result)!r}"
                )
            no_h = float(eng.work_duration or 0)
            ot_h = float(eng.overtime_hours or 0)
            th = float(eng.total_hours or 0) or (no_h + ot_h)
            # 试验需求编号优先使用考勤记录里填写的 requirement_code（飞书表格原始值），
            # 如果解析不到对应 TestOrder 则保持为空，不能按人员绑定或项目兜底，
            # 避免人员跨月调动后历史工时错误归属到最新试验单。
            # 注意：即使 eng.test_order_id 有旧值，只要 requirement_code 为空/未匹配，
            # 就强制清空 test_order_id，防止飞书数据被清除后仍错误关联旧试验单。
            req_code = (eng.requirement_code or "").strip()
            eng_to_id = _resolve_test_order_id(req_code, eng.test_order_id)
            # ★ 通过 test_order_id 覆盖 project_id（使用试验单号看板中的项目信息）
            eng_proj_id = eng.project_id or 1  # 无项目时兜底为1
            if eng_to_id and to_project_map.get(eng_to_id):
                eng_proj_id = to_project_map[eng_to_id]
            tno = eng.test_order.test_order_no if eng.test_order else (req_code if eng_to_id else "")
            supp = _get_supplier_fast(tno, eng.person_name, "")
            ptype = "驾驶员" if supp in ("万嘉禾", "育喆", "驰恒") else "工程师"
            defaults = {
                "test_order_id": eng_to_id, "person_type": ptype,
                "normal_hours": no_h, "overtime_hours": ot_h, "work_hours": th,
                "is_overtime": bool(eng.is_overtime),
                "travel_status": eng.travel_status or "N/A", "advance_payment": 0,
                "total_amount": _calc_total(supp, eng.travel_status or "", no_h, ot_h, 0, eng.record_date, req_date_map.get(tno)),
                "approval_status": _get_approval(eng.approver1_result, eng.approver2_result),
                "source_id": eng.id, "source_type": "engineer", "source": "飞书", "supplier": supp,
            }
            # ★ 去重：按 (person_name, record_date) 唯一，同一源考勤记录不重复创建
            person_key = (eng.person_name, str(eng.record_date))
            # 优先按源记录去重（同一考勤记录不重复生成每日记录）
            src_key = (eng.id, "engineer")
            existing = daily_by_source.get(src_key) or daily_index.get(person_key)
            if existing and existing.get("id"):
                # 已有记录，更新（保留更有信息的 test_order_id）
                if not existing.get("test_order_id") and eng_to_id:
                    defaults["test_order_id"] = eng_to_id
                    defaults["project_id"] = eng_proj_id if eng_to_id in to_project_map else existing.get("project_id", eng_proj_id)
                elif existing.get("test_order_id") and not eng_to_id:
                    defaults["test_order_id"] = None  # 飞书该天无试验需求编号，清空旧关联
                to_update.append((existing["id"], defaults))
                # 更新内存索引，防止同一次运行再次匹配
                daily_index[person_key] = existing
                daily_by_source[src_key] = existing
            else:
                defaults.update({"project_id": eng_proj_id, "record_date": eng.record_date, "person_name": eng.person_name})
                pending_create[person_key] = (defaults, src_key)
        if _eng_skipped_no_project > 0:
            logger.info(f"[DailySync] 工程师无项目记录(已兜底处理): {_eng_skipped_no_project} 条")

        # 处理驾驶员
        _drv_logged = 0
        _drv_skipped_no_project = 0
        for drv in drvs:
            if not drv.project_id:
                _drv_skipped_no_project += 1
                if _drv_skipped_no_project <= 5:
                    logger.warning(
                        f"[DailySync] 驾驶员无项目(使用兜底id=1): person={drv.person_name}, date={drv.record_date}, "
                        f"requirement_code={drv.requirement_code}, test_order_id={drv.test_order_id}"
                    )
            # 调试：打印前3条驾驶员的审批值
            if _drv_logged < 3:
                _drv_logged += 1
                logger.info(
                    f"[DailySync] 驾驶员审批: person={drv.person_name}, date={drv.record_date}, "
                    f"appr1={drv.approver1_result!r}, appr2={drv.approver2_result!r}, "
                    f"approval={_get_approval(drv.approver1_result, drv.approver2_result)!r}"
                )
            no_h = float(drv.work_duration or 0)
            ot_h = float(drv.overtime_hours or 0)
            th = float(drv.total_hours or 0) or (no_h + ot_h)
            # 试验需求编号优先使用考勤记录里填写的 requirement_code（飞书表格原始值），
            # 如果解析不到对应 TestOrder 则保持为空，不能按人员绑定或项目兜底。
            # 注意：即使 drv.test_order_id 有旧值，只要 requirement_code 为空/未匹配，
            # 就强制清空 test_order_id，防止飞书数据被清除后仍错误关联旧试验单。
            req_code = (drv.requirement_code or "").strip()
            drv_to_id = _resolve_test_order_id(req_code, drv.test_order_id)
            # ★ 通过 test_order_id 覆盖 project_id（使用试验单号看板中的项目信息）
            drv_proj_id = drv.project_id or 1  # 无项目时兜底为1
            if drv_to_id and to_project_map.get(drv_to_id):
                drv_proj_id = to_project_map[drv_to_id]
            tno = drv.test_order.test_order_no if drv.test_order else (req_code if drv_to_id else "")
            supp = _get_supplier_fast(tno, drv.person_name, "")
            adv = float(drv.daily_advance_total or 0)
            if supp in ("万嘉禾", "育喆", "驰恒"):
                ptype = "驾驶员"
            elif supp:
                ptype = "工程师"
            else:
                # 供应商未知（人员未登记在 RequirementPersonnel），但来源是驾驶员考勤，按驾驶员处理
                ptype = "驾驶员"
            defaults = {
                "test_order_id": drv_to_id, "person_type": ptype,
                "normal_hours": no_h, "overtime_hours": ot_h, "work_hours": th,
                "is_overtime": bool(drv.is_overtime) if drv.is_overtime else False,
                "travel_status": drv.travel_status or "N/A", "advance_payment": adv,
                "total_amount": _calc_total(supp, drv.travel_status or "", no_h, ot_h, adv, drv.record_date, req_date_map.get(tno)),
                "approval_status": _get_approval(drv.approver1_result, drv.approver2_result),
                "source_id": drv.id, "source_type": "driver", "source": "飞书", "supplier": supp,
            }
            # ★ 去重：按 (person_name, record_date) 唯一，同一源考勤记录不重复创建
            person_key = (drv.person_name, str(drv.record_date))
            src_key = (drv.id, "driver")
            existing = daily_by_source.get(src_key) or daily_index.get(person_key)
            if existing and existing.get("id"):
                if not existing.get("test_order_id") and drv_to_id:
                    defaults["test_order_id"] = drv_to_id
                    defaults["project_id"] = drv_proj_id if drv_to_id in to_project_map else existing.get("project_id", drv_proj_id)
                elif existing.get("test_order_id") and not drv_to_id:
                    defaults["test_order_id"] = None  # 飞书该天无试验需求编号，清空旧关联
                to_update.append((existing["id"], defaults))
                daily_index[person_key] = existing
                daily_by_source[src_key] = existing
            else:
                defaults.update({"project_id": drv_proj_id, "record_date": drv.record_date, "person_name": drv.person_name})
                pending_create[person_key] = (defaults, src_key)
        if _drv_skipped_no_project > 0:
            logger.info(f"[DailySync] 驾驶员无项目记录(已兜底处理): {_drv_skipped_no_project} 条")

        # ── 第二阶段：批量写入数据库 ──
        to_create = [d for d, _ in pending_create.values()]
        if to_create:
            objects = [DailyRecord(**d) for d in to_create]
            await DailyRecord.bulk_create(objects, batch_size=500)
            logger.info(f"[DailySync] 批量创建 {len(to_create)} 条每日记录")

        if to_update:
            semaphore = _asyncio.Semaphore(20)
            updated_cnt = 0
            skipped_cnt = 0

            async def _update_one(eid, upd):
                nonlocal updated_cnt, skipped_cnt
                async with semaphore:
                    try:
                        await DailyRecord.filter(id=eid).update(**upd)
                        updated_cnt += 1
                    except Exception as e:
                        # 单条更新失败（如唯一索引冲突：同 project/date/person 已有带 test_order_id 的记录）
                        # 不应中断整批，跳过该条继续
                        skipped_cnt += 1
                        logger.warning(f"[DailySync] 跳过更新 id={eid}: {e}")

            await _asyncio.gather(*[_update_one(eid, upd) for eid, upd in to_update])
            logger.info(f"[DailySync] 批量更新 {updated_cnt} 条每日记录，跳过 {skipped_cnt} 条")

        # ── 第二阶段附加：清理重复记录（同人同天保留最新一条）──
        # DELETE JOIN：不引用目标表子查询，规避 MySQL Error 1093
        # （DELETE 的 NOT IN 子查询不能引用目标表；旧版"套一层 derived table"在 MySQL 8 derived merge 下仍可能报 1093，被外层 except 静默吞掉，导致重复记录未被清理）
        from tortoise import connections
        conn = connections.get("mysql")
        try:
            await conn.execute_query(
                "DELETE t1 FROM expense_daily_record t1 "
                "INNER JOIN expense_daily_record t2 "
                "ON t1.person_name = t2.person_name "
                "AND t1.record_date = t2.record_date "
                "AND t1.id < t2.id"
            )
            logger.info("[DailySync] 重复记录清理完成")
        except Exception as e:
            logger.error(f"[DailySync] 重复记录清理失败: {e}")

        # ── 第三阶段：结算汇总 ──
        # 已使用金额 = 该试验单下【非审批驳回】的每日费用记录合计（含待审批、通过），
        # 审批驳回的记录不计入费用统计与预算预警；与“每日费用”明细列表口径保持一致。
        approved = await DailyRecord.filter(approval_status__not="驳回").values("test_order_id", "total_amount")
        to_amounts = {}
        for dr in approved:
            tid = dr["test_order_id"]
            if tid:
                to_amounts[tid] = to_amounts.get(tid, D("0")) + D(str(dr["total_amount"] or 0))
        for to_id, total in to_amounts.items():
            await TestOrder.filter(id=to_id).update(used_amount=float(total))

        test_orders = await TestOrder.filter(id__in=list(to_amounts.keys())).all().values("id", "expense_code_id", "used_amount")
        ec_amounts = {}
        for to in test_orders:
            ec_id = to["expense_code_id"]
            if ec_id:
                ec_amounts[ec_id] = ec_amounts.get(ec_id, D("0")) + D(str(to["used_amount"] or 0))
        for ec_id, total in ec_amounts.items():
            await ExpenseCode.filter(id=ec_id).update(used_amount=float(total))

        logger.info(f"[DailySync] 同步完成: 新建 {len(to_create)}, 更新 {len(to_update)}, 结算 {len(to_amounts)} 个试验单, "
                     f"无项目(已兜底): 工程师{_eng_skipped_no_project}条, 驾驶员{_drv_skipped_no_project}条")
    except Exception as e:
        import traceback
        logger.error(f"[DailySync] 同步失败: {traceback.format_exc()}")
        print(f"Auto sync daily failed: {e}")





@router.post("/init-menus", summary="初始化费用管理菜单")
async def init_expense_menus():
    """初始化费用管理菜单（可重复调用：父/子菜单已存在则跳过，仅补建缺失项）。

    注意：父菜单 redirect 指向 /expense-management/dashboard，因此必须存在
    path=dashboard 的子菜单，否则点击「费用管理」会因 redirect 目标无路由而落到 404。
    """
    expense_menu = await Menu.get_or_none(name="费用管理", parent_id=0)
    if not expense_menu:
        expense_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="费用管理",
            path="/expense-management",
            order=5,
            parent_id=0,
            icon="material-symbols:payments-outline",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/expense-management/dashboard",
        )

    # (path, name, component, icon, order)
    # dashboard 必须存在：父菜单 redirect 指向 /expense-management/dashboard
    children_def = [
        ("dashboard", "费用概览", "/expense-management/dashboard", "material-symbols:dashboard-outline", 1),
        ("daily-record", "每日记录", "/expense-management/daily-record", "material-symbols:edit-note-outline", 2),
        ("monthly-settlement", "月度结算", "/expense-management/monthly-settlement", "material-symbols:receipt-long-outline", 3),
        ("budget-alert", "预算预警", "/expense-management/budget-alert", "material-symbols:warning-outline", 4),
    ]
    existing_paths = {m.path for m in await Menu.filter(parent_id=expense_menu.id)}
    to_create = [
        Menu(
            menu_type=MenuType.MENU,
            name=name,
            path=path,
            order=order,
            parent_id=expense_menu.id,
            icon=icon,
            is_hidden=False,
            component=component,
            keepalive=False,
        )
        for path, name, component, icon, order in children_def
        if path not in existing_paths
    ]
    if to_create:
        await Menu.bulk_create(to_create)
    return Success(msg=f"费用管理菜单就绪，本次新建 {len(to_create)} 个子项")


@router.post("/rename-menu", summary="清理旧菜单：删除试验需求菜单，恢复业务支持")
async def rename_expense_menus():
    """删除试验需求与人员菜单，确保业务支持为普通菜单"""
    updated = []

    # 1. 删除"试验需求与人员"
    m = await Menu.filter(name="试验需求与人员").first()
    if m:
        await m.delete()
        updated.append("删除: 试验需求与人员")

    # 2. 确保"业务支持"是普通 MENU
    biz = await Menu.filter(name="业务支持").first()
    if biz:
        # 如果是 CATALOG 改为 MENU
        if biz.menu_type == MenuType.CATALOG or biz.component == "Layout":
            biz.menu_type = MenuType.MENU
            biz.component = "/expense-management/daily-record"
            biz.path = "daily-record"
            biz.redirect = ""
            await biz.save()
            updated.append("修复: 业务支持→MENU(daily-record)")
        else:
            updated.append("业务支持已是 MENU")
        # 删除业务支持下的子菜单（如果有残留）
        for child in await Menu.filter(parent_id=biz.id):
            await child.delete()
            updated.append(f"删除业务支持子菜单: {child.name}")
    else:
        # 如果业务支持不存在，在马甲下创建
        parent = await Menu.filter(name="费用管理").first()
        if parent:
            await Menu.create(
                menu_type=MenuType.MENU, name="业务支持", path="daily-record",
                order=2, parent_id=parent.id, icon="material-symbols:edit-calendar",
                is_hidden=False, component="/expense-management/daily-record", keepalive=False,
            )
            updated.append("创建: 业务支持")

    # 3. 清理可能残留的独立菜单（工程师日志/驾驶员日志）
    for name in ["工程师日志", "驾驶员日志"]:
        m = await Menu.filter(name=name).first()
        if m:
            await m.delete()
            updated.append(f"删除残留菜单: {name}")

    if updated:
        return Success(msg=f"菜单已更新: {', '.join(updated)}")
    return Success(msg="无需更新")


# ==================== 项目管理 ====================
@router.get("/project/list", summary="查看项目列表")
async def list_projects(
    series_name: str = Query(None, description="系列名称"),
    project_name: str = Query(None, description="项目名称"),
    category: str = Query(None, description="类别"),
):
    projects = await expense_project_controller.search(
        series_name=series_name, project_name=project_name, category=category
    )
    data = [await p.to_dict() for p in projects]
    return Success(data=data)


@router.post("/project/create", summary="创建项目")
async def create_project(project_in: ExpenseProjectCreate):
    await expense_project_controller.create(obj_in=project_in)
    return Success(msg="创建成功")


@router.post("/project/update", summary="更新项目")
async def update_project(id: int = Query(...), project_in: ExpenseProjectUpdate = Body(...)):
    await expense_project_controller.update(id=id, obj_in=project_in)
    return Success(msg="更新成功")


@router.delete("/project/delete", summary="删除项目")
async def delete_project(id: int = Query(...)):
    await expense_project_controller.remove(id=id)
    return Success(msg="删除成功")


# ==================== 预算号管理 ====================
@router.get("/budget-code/list", summary="查看预算号列表")
async def list_budget_codes(
    project_id: int = Query(None, description="项目ID"),
    budget_code: str = Query(None, description="预算号"),
):
    items = await budget_code_controller.search(project_id=project_id, budget_code=budget_code)
    data = []
    for item in items:
        d = await item.to_dict()
        d["project_name"] = item.project.project_name if item.project else ""
        data.append(d)
    return Success(data=data)


@router.post("/budget-code/create", summary="创建预算号")
async def create_budget_code(item_in: BudgetCodeCreate):
    exist = await budget_code_controller.model.filter(budget_code=item_in.budget_code).first()
    if exist:
        return Fail(msg="预算号已存在")
    await budget_code_controller.create(obj_in=item_in)
    return Success(msg="创建成功")


@router.post("/budget-code/update", summary="更新预算号")
async def update_budget_code(id: int = Query(...), item_in: BudgetCodeUpdate = Body(...)):
    await budget_code_controller.update(id=id, obj_in=item_in)
    return Success(msg="更新成功")


@router.delete("/budget-code/delete", summary="删除预算号")
async def delete_budget_code(id: int = Query(...)):
    await budget_code_controller.remove(id=id)
    return Success(msg="删除成功")


# ==================== 费用号管理 ====================
@router.get("/expense-code/list", summary="查看费用号列表")
async def list_expense_codes(
    budget_id: int = Query(None, description="预算号ID"),
    expense_code: str = Query(None, description="费用号"),
    budget_code: str = Query(None, description="预算号"),
    project_keyword: str = Query(None, description="项目关键词"),
    responsible_person: str = Query(None, description="负责人"),
    category: str = Query(None, description="类别"),
):
    items = await expense_code_controller.search(budget_id=budget_id, expense_code=expense_code, responsible_person=responsible_person)
    data = []
    for item in items:
        d = await item.to_dict()
        d["budget_code"] = item.budget.budget_code if item.budget else ""
        d["project_id"] = item.budget.project_id if item.budget else None
        project = await item.budget.project if item.budget else None
        d["project_name"] = project.project_name if project else ""
        d["series_name"] = project.series_name if project else ""
        d["category"] = project.category if project else ""
        d["responsible_person"] = item.responsible_person or ""

        # 预算号筛选
        if budget_code and budget_code not in (d.get("budget_code") or ""):
            continue
        # 类别筛选
        if category and (d.get("category") or "") != category:
            continue
        # 项目关键词筛选
        if project_keyword:
            kw = project_keyword.strip()
            match = False
            if kw in (d.get("project_name") or ""):
                match = True
            if kw in (d.get("series_name") or ""):
                match = True
            full = f"{d.get('series_name', '')} - {d.get('project_name', '')}"
            if kw in full:
                match = True
            if not match:
                continue

        # 计算关联试验单号的统计
        test_orders = await TestOrder.filter(expense_code=item)
        test_orders_total = sum(float(t.total_price) for t in test_orders)
        test_orders_used = sum(float(t.used_amount) for t in test_orders)
        test_orders_settled = sum(float(t.settlement_amount or 0) for t in test_orders)
        d["test_orders_total"] = test_orders_total
        d["test_orders_used"] = test_orders_used
        d["test_orders_settled"] = test_orders_settled

        exp_total = d["total_amount"] = float(d["total_amount"])
        d["used_amount"] = float(d["used_amount"])

        # 启动率 = 试验单号总金额 / 费用号金额
        if exp_total > 0:
            d["start_rate"] = round(test_orders_total / exp_total * 100, 1)
        else:
            d["start_rate"] = 0

        # 使用率 = 试验单号已使用金额 / 费用号金额
        if exp_total > 0:
            d["main_usage_rate"] = round(test_orders_used / exp_total * 100, 1)
        else:
            d["main_usage_rate"] = 0

        d["remaining"] = float(d["total_amount"]) - float(d["used_amount"])
        data.append(d)
    return Success(data=data)


@router.post("/expense-code/create", summary="创建费用号")
async def create_expense_code(item_in: ExpenseCodeCreate):
    if not item_in.budget_id:
        return Fail(msg="未指定预算号")
    exist = await expense_code_controller.model.filter(expense_code=item_in.expense_code).first()
    if exist:
        return Fail(msg="费用号已存在")
    await expense_code_controller.create(obj_in=item_in)
    return Success(msg="创建成功")


@router.post("/expense-code/update", summary="更新费用号")
async def update_expense_code(id: int = Query(...), item_in: ExpenseCodeUpdate = Body(...)):
    await expense_code_controller.update(id=id, obj_in=item_in)
    return Success(msg="更新成功")


@router.delete("/expense-code/delete", summary="删除费用号")
async def delete_expense_code(id: int = Query(...)):
    await expense_code_controller.remove(id=id)
    return Success(msg="删除成功")


# ==================== 试验单号管理 ====================
@router.get("/test-order/list", summary="查看试验单号列表")
async def list_test_orders(
    expense_code_id: int = Query(None, description="费用号ID"),
    test_order_no: str = Query(None, description="试验单号"),
    is_used: bool = Query(None, description="是否已使用"),
    responsible_person: str = Query(None, description="负责人"),
    project_keyword: str = Query(None, description="项目关键词"),
):
    items = await test_order_controller.search(
        expense_code_id=expense_code_id, test_order_no=test_order_no,
        is_used=is_used, responsible_person=responsible_person,
        project_keyword=project_keyword,
    )
    data = []
    for item in items:
        d = await item.to_dict()
        # 关联费用号
        exp_code = item.expense_code
        d["expense_code"] = exp_code.expense_code if exp_code else ""
        d["expense_code_id"] = exp_code.id if exp_code else None
        d["expense_total_amount"] = float(exp_code.total_amount) if exp_code else 0
        d["expense_used_amount"] = float(exp_code.used_amount) if exp_code else 0
        d["expense_responsible_person"] = exp_code.responsible_person or "" if exp_code else ""
        # 关联预算号
        budget = await exp_code.budget if exp_code else None
        d["budget_code"] = budget.budget_code if budget else ""
        d["budget_amount"] = float(budget.budget_amount) if budget else 0
        d["budget_used_amount"] = float(budget.used_amount) if budget else 0
        # 关联项目
        project = await budget.project if budget else None
        d["project_id"] = project.id if project else None
        d["project_name"] = project.project_name if project else ""
        d["series_name"] = project.series_name if project else ""

        # 项目关键词筛选（后端过滤）
        if project_keyword:
            kw = project_keyword.strip()
            match = False
            if kw in (d.get("project_name") or ""):
                match = True
            if kw in (d.get("series_name") or ""):
                match = True
            full = f"{d.get('series_name', '')} - {d.get('project_name', '')}"
            if kw in full:
                match = True
            if not match:
                continue

        # 统计该试验单号的每日记录汇总
        daily_records = await DailyRecord.filter(test_order=item)
        d["total_work_hours"] = sum(float(r.work_hours) for r in daily_records)
        d["total_advance_payment"] = sum(float(r.advance_payment) for r in daily_records)
        # 实时已使用 = 截止到上月已结算 + 本月每日费用; 无结算数据时 = 所有每日费用
        # 截止到上月已结算: 手动输入优先, 无则默认=截止到上月已使用(上月及之前每日费用汇总)
        now = datetime.now()
        non_rejected = [r for r in daily_records if r.approval_status != "驳回"]
        last_month_records = [r for r in non_rejected if r.record_date and (r.record_date.year < now.year or (r.record_date.year == now.year and r.record_date.month < now.month))]
        last_month_sum = sum(float(r.total_amount or 0) for r in last_month_records)
        settlement = item.settlement_amount
        if settlement is not None:
            settlement_val = float(settlement)
        else:
            settlement_val = last_month_sum  # 默认=截止到上月已使用
        current_month_used = sum(float(r.total_amount or 0) for r in non_rejected if r.record_date and r.record_date.year == now.year and r.record_date.month == now.month)
        d["used_amount"] = settlement_val + current_month_used
        d["settlement_amount"] = settlement_val
        persons = set(r.person_name for r in daily_records)
        d["person_count"] = len(persons)
        d["person_types"] = list(set(r.person_type for r in daily_records))
        data.append(d)
    return Success(data=data)


@router.post("/test-order/create", summary="创建试验单号")
async def create_test_order(item_in: TestOrderCreate):
    exist = await test_order_controller.model.filter(test_order_no=item_in.test_order_no).first()
    if exist:
        return Fail(msg="试验单号已存在")
    await test_order_controller.create(obj_in=item_in)
    return Success(msg="创建成功")


@router.post("/test-order/update", summary="更新试验单号")
async def update_test_order(id: int = Query(...), item_in: TestOrderUpdate = Body(...)):
    await test_order_controller.update(id=id, obj_in=item_in)
    return Success(msg="更新成功")


@router.get("/test-order/detail", summary="试验单号详情（含每日记录）")
async def get_test_order_detail(id: int = Query(..., description="试验单号ID")):
    item = await TestOrder.get(id=id).prefetch_related("expense_code")
    if not item:
        return Fail(msg="试验单号不存在")

    d = await item.to_dict()
    exp_code = item.expense_code
    d["expense_code"] = exp_code.expense_code if exp_code else ""
    d["expense_total_amount"] = float(exp_code.total_amount) if exp_code else 0
    d["expense_used_amount"] = float(exp_code.used_amount) if exp_code else 0

    budget = await exp_code.budget if exp_code else None
    d["budget_code"] = budget.budget_code if budget else ""
    d["budget_amount"] = float(budget.budget_amount) if budget else 0
    d["budget_used_amount"] = float(budget.used_amount) if budget else 0

    project = await budget.project if budget else None
    d["project_id"] = project.id if project else None
    d["project_name"] = project.project_name if project else ""
    d["series_name"] = project.series_name if project else ""

    # 获取该试验单号的所有每日记录（按人员分类）
    daily_records = await DailyRecord.filter(test_order=item).order_by("-record_date")
    record_list = []
    for r in daily_records:
        rd = await r.to_dict()
        rd["project_name"] = r.project.project_name if r.project else ""
        record_list.append(rd)

    d["daily_records"] = record_list
    d["total_work_hours"] = sum(float(r.work_hours) for r in daily_records)
    d["total_advance_payment"] = sum(float(r.advance_payment) for r in daily_records)

    # 按人员统计
    from collections import defaultdict
    person_stats = defaultdict(lambda: {"work_hours": 0, "advance": 0, "person_type": ""})
    for r in daily_records:
        person_stats[r.person_name]["work_hours"] += float(r.work_hours)
        person_stats[r.person_name]["advance"] += float(r.advance_payment)
        person_stats[r.person_name]["person_type"] = r.person_type
    d["person_stats"] = [{"person_name": k, **v} for k, v in person_stats.items()]
    d["person_count"] = len(person_stats)

    return Success(data=d)


@router.delete("/test-order/delete", summary="删除试验单号")
async def delete_test_order(id: int = Query(...)):
    await test_order_controller.remove(id=id)
    return Success(msg="删除成功")


# ==================== 每日费用记录 ====================
@router.get("/daily-record/list", summary="查看每日记录")
async def list_daily_records(
    project_name: str = Query(None, description="项目名称"),
    person_name: str = Query(None, description="人员姓名"),
    person_type: str = Query(None, description="人员类型"),
    record_date: str = Query(None, description="日期 YYYY-MM-DD"),
    record_date_start: str = Query(None, description="起始日期"),
    record_date_end: str = Query(None, description="截止日期"),
    test_order_no: str = Query(None, description="试验单号"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(50, ge=1, le=500, description="每页条数"),
):
    q = Q()
    if project_name:
        q &= Q(project__project_name__contains=project_name)
    if person_name:
        q &= Q(person_name__contains=person_name)
    if person_type:
        q &= Q(person_type=person_type)
    if record_date:
        q &= Q(record_date=record_date)
    if record_date_start:
        q &= Q(record_date__gte=record_date_start)
    if record_date_end:
        q &= Q(record_date__lte=record_date_end)
    if test_order_no:
        q &= Q(test_order__test_order_no__contains=test_order_no)

    # 筛选后总费用（包含所有匹配记录）
    from app.log import logger
    logger.info("[API] DailyRecord list - start query")
    sum_records = await DailyRecord.filter(q).values("total_amount")
    filtered_total_amount = sum(float(r["total_amount"] or 0) for r in sum_records)
    logger.info(f"[API] DailyRecord list - filtered_total: {filtered_total_amount}")
    total = await DailyRecord.filter(q).count()
    logger.info(f"[API] DailyRecord list - total: {total}")

    # 分页查询，避免一次性加载全量数据导致前端崩溃
    offset = (page - 1) * page_size
    items = await DailyRecord.filter(q).order_by("-record_date").offset(offset).limit(page_size).prefetch_related("project", "test_order")
    logger.info(f"[API] DailyRecord list - items count: {len(items)}")

    # ★ 预加载：批量加载所有需要补 supplier 的人员绑定关系，避免 N+1 查询
    need_supplier = [it for it in items if not getattr(it, "supplier", None)]
    supplier_map: dict = {}
    if need_supplier:
        all_rp = await RequirementPersonnel.all().values("test_order_no", "outsourced_personnel", "supplier")
        # 构建 O(1) 查找字典，避免 O(N*M) 嵌套循环
        for rp in all_rp:
            tno = rp["test_order_no"] or ""
            sup = rp["supplier"] or ""
            out_p = rp["outsourced_personnel"] or ""
            if tno and sup and out_p:
                for name in out_p.split(","):
                    name = name.strip()
                    if name:
                        supplier_map[(tno, name)] = sup

    data = []
    for item in items:
        d = await item.to_dict()
        # 直接从本地DB读取（同步时已写入飞书字段值）
        d["project_name"] = item.project.project_name if item.project else ""
        d["test_order_no"] = item.test_order.test_order_no if item.test_order else ""
        # 优先用同步时存储的supplier，为空再从预加载的 supplier_map 查
        if not d.get("supplier"):
            tno = d.get("test_order_no", "")
            pname = item.person_name
            sup = supplier_map.get((tno, pname), "")
            if not sup and item.test_order:
                sup = item.test_order.supplier or ""
            d["supplier"] = sup
        data.append(d)
    logger.info(f"[API] DailyRecord list - data built, count: {len(data)}")
    return SuccessExtra(data=data, total=total, filtered_total=filtered_total_amount)


@router.post("/daily-record/sync", summary="从考勤日志同步每日费用")
async def sync_daily_records():
    """从工程师日志和驾驶员日志同步生成每日费用记录（优化版：批量预加载+批量写入）"""
    import asyncio as _asyncio

    # ★ 预加载：供应商费率
    sr_list = await SupplierRate.all()
    RATES_BY_DATE = {}
    for sr in sr_list:
        RATES_BY_DATE.setdefault(sr.name, []).append({
            "local": float(sr.local_rate), "trip": float(sr.trip_rate),
            "unit": sr.unit,
            "effective_from": sr.effective_from,
            "effective_to": sr.effective_to,
        })
    for rates in RATES_BY_DATE.values():
        rates.sort(key=lambda r: (r["effective_from"] or date.min, r["effective_to"] or date.max))
    from datetime import date as dt_date

    def _calc_total(supplier_name, travel_status, normal_h, overtime_h, advance, record_date=None, requirement_date=None):
        """计算费用总额，根据供应商和日期从 SupplierRate 表取对应时间生效的单价。
        达安：按试验需求通过日期（requirement_date）取单价；
        育喆/驰恒：按工时产生日期（record_date）取单价。
        """
        sup = (supplier_name or "").strip()
        all_rates = RATES_BY_DATE.get(sup, RATES_BY_DATE.get("育喆", []))
        price_date = requirement_date if (sup == "达安" and requirement_date) else record_date
        cfg = None
        for r in all_rates:
            ef = r["effective_from"]
            et = r["effective_to"]
            if price_date:
                if (ef is None or price_date >= ef) and (et is None or price_date <= et):
                    cfg = r; break
            else:
                cfg = r
        if not cfg:
            cfg = all_rates[-1] if all_rates else {"local": 290, "trip": 356, "unit": "day"}
        is_trip = str(travel_status) == "出差" if travel_status else False
        rv = cfg["trip"] if is_trip else cfg["local"]
        effective = rv / 8 if cfg["unit"] == "day" else rv
        return round((normal_h + overtime_h) * effective + advance, 2)

    # ★ 预加载：所有人员绑定关系 → (试验单号, 人名) → 供应商 / requirement_date
    all_rp = await RequirementPersonnel.all().values("test_order_no", "outsourced_personnel", "supplier", "requirement_date")
    rp_list = []
    req_date_map = {}
    for rp in all_rp:
        tno = rp["test_order_no"]
        if tno and rp.get("requirement_date"):
            req_date_map[tno] = rp["requirement_date"]
        personnel = (rp["outsourced_personnel"] or "").replace("，", ",").replace("、", ",").split(",")
        personnel = [n.strip() for n in personnel if n.strip()]
        for pn in personnel:
            rp_list.append((tno, pn, rp["supplier"] or ""))

    def _find_supplier(test_order_no, person_name, fallback=""):
        for tno, pn, sup in rp_list:
            if tno == test_order_no and pn == person_name:
                return sup or fallback
        return fallback or ""

    # ★ 预加载：所有已有 DailyRecord → (project_id, record_date, person_name) → id
    existing_daily = await DailyRecord.all().values("id", "project_id", "record_date", "person_name")
    daily_index = {}
    for d in existing_daily:
        key = (d["project_id"], str(d["record_date"]), d["person_name"])
        daily_index[key] = d["id"]

    # ★ 预加载：试验单 → supplier
    all_tos = await TestOrder.all().values("id", "test_order_no", "supplier")
    to_supplier = {t["test_order_no"]: t["supplier"] or "" for t in all_tos}

    # ═══════════════════════════════════════════════════════════
    # ★ 处理阶段：纯内存操作，构建 to_create / to_update
    # ═══════════════════════════════════════════════════════════
    to_create = []
    to_update = []

    def _process_attendance(records, source_type):
        """处理考勤记录，添加到 to_create/to_update"""
        for att in records:
            normal_hours = float(att.work_duration or 0)
            overtime_hours = float(att.overtime_hours or 0)
            total_work_hours = float(att.total_hours or 0) or (normal_hours + overtime_hours)
            travel_status = att.travel_status or "未出差"
            advance = float(att.daily_advance_total or 0) if source_type == "driver" else 0
            tno = att.test_order.test_order_no if att.test_order else ""
            supplier = _find_supplier(tno, att.person_name, to_supplier.get(tno, ""))

            ptype = "驾驶员" if supplier in ("万嘉禾", "育喆", "驰恒") else "工程师"

            # 审批状态
            approval = "待审批"
            a1 = (att.approver1_result or "").strip()
            a2 = (att.approver2_result or "").strip()
            if a1 in ("通过", "批准", "已通过", "同意", "审核通过", "已审批") or \
               a2 in ("通过", "批准", "已通过", "同意", "审核通过", "已审批"):
                approval = "通过"
            elif a1 in ("驳回", "已驳回", "拒绝", "不通过", "未通过") or \
                 a2 in ("驳回", "已驳回", "拒绝", "不通过", "未通过"):
                approval = "驳回"

            defaults = {
                "test_order_id": att.test_order_id,
                "person_type": ptype,
                "normal_hours": normal_hours,
                "overtime_hours": overtime_hours,
                "work_hours": total_work_hours,
                "is_overtime": bool(att.is_overtime) if hasattr(att, 'is_overtime') and att.is_overtime else False,
                "travel_status": travel_status,
                "advance_payment": advance,
                "total_amount": _calc_total(supplier, travel_status, normal_hours, overtime_hours, advance, att.record_date, req_date_map.get(tno)),
                "approval_status": approval,
                "source_id": att.id,
                "source_type": source_type,
                "source": "飞书",
                "supplier": supplier,
            }

            key = (att.project_id, str(att.record_date), att.person_name)
            existing_id = daily_index.get(key)
            if existing_id:
                to_update.append((existing_id, defaults))
            else:
                defaults.update({
                    "project_id": att.project_id,
                    "record_date": att.record_date,
                    "person_name": att.person_name,
                })
                to_create.append(defaults)

    # 处理工程师 + 驾驶员
    eng_records = await engineer_attendance_controller.model.all().prefetch_related("project", "test_order")
    _process_attendance(eng_records, "engineer")

    drv_records = await driver_attendance_controller.model.all().prefetch_related("project", "test_order")
    _process_attendance(drv_records, "driver")

    # ═══════════════════════════════════════════════════════════
    # ★ 批量写入阶段
    # ═══════════════════════════════════════════════════════════
    if to_create:
        objects = [DailyRecord(**d) for d in to_create]
        await DailyRecord.bulk_create(objects, batch_size=500)
    if to_update:
        semaphore = _asyncio.Semaphore(20)
        async def _update_one(eid, upd):
            async with semaphore:
                await DailyRecord.filter(id=eid).update(**upd)
        await _asyncio.gather(*[_update_one(eid, upd) for eid, upd in to_update])

    synced = len(to_create) + len(to_update)

    # 结算：汇总【非审批驳回】的每日费用到试验单和费用号（含待审批、通过）
    from decimal import Decimal as D
    approved = await DailyRecord.filter(approval_status__not="驳回").values("test_order_id", "total_amount")
    to_amounts = {}
    for dr in approved:
        tid = dr["test_order_id"]
        if tid:
            to_amounts[tid] = to_amounts.get(tid, D("0")) + D(str(dr["total_amount"] or 0))
    for to_id, total in to_amounts.items():
        await TestOrder.filter(id=to_id).update(used_amount=float(total))
    test_orders = await TestOrder.filter(id__in=list(to_amounts.keys())).values("id", "expense_code_id", "used_amount")
    ec_amounts = {}
    for to in test_orders:
        if to["expense_code_id"]:
            ec_amounts[to["expense_code_id"]] = ec_amounts.get(to["expense_code_id"], D("0")) + D(str(to["used_amount"] or 0))
    for ec_id, total in ec_amounts.items():
        await ExpenseCode.filter(id=ec_id).update(used_amount=float(total))
    return Success(msg=f"同步完成，共 {synced} 条记录")


@router.post("/daily-record/create", summary="创建每日记录")
async def create_daily_record(item_in: DailyRecordCreate):
    existing = await DailyRecord.filter(
        project_id=item_in.project_id,
        record_date=item_in.record_date,
        person_name=item_in.person_name,
        test_order_id=item_in.test_order_id,
    ).first()
    if existing:
        return Fail(msg=f"已存在重复记录：{item_in.person_name} 在 {item_in.record_date} 已有每日费用记录（ID: {existing.id}），请勿重复创建")
    await daily_record_controller.create(obj_in=item_in)
    return Success(msg="创建成功")


@router.post("/daily-record/batch-create", summary="批量创建每日记录")
async def batch_create_daily_records(records: list[DailyRecordCreate]):
    created = 0
    skipped = 0
    for record in records:
        existing = await DailyRecord.filter(
            project_id=record.project_id,
            record_date=record.record_date,
            person_name=record.person_name,
            test_order_id=record.test_order_id,
        ).first()
        if existing:
            skipped += 1
        else:
            await daily_record_controller.create(obj_in=record)
            created += 1
    return Success(msg=f"成功创建 {created} 条记录，跳过 {skipped} 条重复记录")


@router.post("/daily-record/update", summary="更新每日记录")
async def update_daily_record(id: int = Query(...), item_in: DailyRecordUpdate = Body(...)):
    await daily_record_controller.update(id=id, obj_in=item_in)
    return Success(msg="更新成功")


@router.delete("/daily-record/delete", summary="删除每日记录")
async def delete_daily_record(id: int = Query(...)):
    await daily_record_controller.remove(id=id)
    return Success(msg="删除成功")


@router.get("/daily-record/export", summary="导出每日记录(Excel)")
async def export_daily_records(
    record_date_start: str = Query(None, description="起始日期"),
    record_date_end: str = Query(None, description="截止日期"),
):
    q = Q()
    if record_date_start:
        q &= Q(record_date__gte=record_date_start)
    if record_date_end:
        q &= Q(record_date__lte=record_date_end)
    records = await daily_record_controller.model.filter(q).order_by("-record_date").prefetch_related("project", "test_order")

    wb = Workbook()
    ws = wb.active
    ws.title = "每日费用记录"
    ws.append(["日期", "项目名称", "试验单号", "人员姓名", "人员类型", "工时", "垫付金额", "备注"])

    for r in records:
        ws.append([
            str(r.record_date),
            r.project.project_name if r.project else "",
            r.test_order.test_order_no if r.test_order else "",
            r.person_name,
            r.person_type,
            float(r.work_hours),
            float(r.advance_payment),
            r.remark or "",
        ])

    output = BytesIO()
    wb.save(output)
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=daily_records.xlsx"},
    )


@router.post("/daily-record/import", summary="导入每日记录(Excel)")
async def import_daily_records(file: UploadFile = File(...)):
    try:
        content = await file.read()
        wb = load_workbook(BytesIO(content))
        ws = wb.active

        header_row = next(ws.iter_rows(min_row=1, max_row=1, values_only=True), None)
        if not header_row:
            return Fail(msg="Excel 文件格式错误")

        header_names = {
            "日期": "record_date",
            "项目名称": "project_name",
            "试验单号": "test_order_no",
            "人员姓名": "person_name",
            "人员类型": "person_type",
            "工时": "work_hours",
            "垫付金额": "advance_payment",
            "备注": "remark",
        }
        col_map = {}
        for idx, cell in enumerate(header_row):
            if cell and str(cell).strip() in header_names:
                col_map[header_names[str(cell).strip()]] = idx

        required_cols = ["record_date", "person_name"]
        for col in required_cols:
            if col not in col_map:
                return Fail(msg=f"Excel 缺少必要列")

        def get_val(row, field, default=None):
            idx = col_map.get(field)
            if idx is None or idx >= len(row):
                return default
            val = row[idx]
            if val is None:
                return default
            cleaned = str(val).strip()
            return cleaned if cleaned != "None" else default

        success_count = 0
        fail_count = 0
        skip_count = 0
        errors = []

        for row_num, row in enumerate(ws.iter_rows(min_row=2, values_only=True), start=2):
            try:
                record_date_str = get_val(row, "record_date")
                person_name = get_val(row, "person_name")
                if not record_date_str or not person_name:
                    continue

                project_name = get_val(row, "project_name", "")
                test_order_no = get_val(row, "test_order_no", "")

                record_date = date.fromisoformat(str(record_date_str)) if record_date_str else date.today()

                project = None
                if project_name:
                    project = await ExpenseProject.filter(project_name=project_name).first()

                test_order = None
                if test_order_no:
                    test_order = await TestOrder.filter(test_order_no=test_order_no).first()

                proj_id = project.id if project else 1
                to_id = test_order.id if test_order else None

                # 导入去重检查
                dedup_q = Q(project_id=proj_id, record_date=record_date, person_name=person_name)
                if to_id is not None:
                    dedup_q &= Q(test_order_id=to_id)
                else:
                    dedup_q &= Q(test_order_id__isnull=True)
                if await DailyRecord.filter(dedup_q).exists():
                    skip_count += 1
                    continue

                person_type = get_val(row, "person_type", "工程师")
                work_hours = float(get_val(row, "work_hours", 0) or 0)
                advance_payment = float(get_val(row, "advance_payment", 0) or 0)
                remark = get_val(row, "remark", "")

                await daily_record_controller.create(obj_in=DailyRecordCreate(
                    project_id=proj_id,
                    test_order_id=to_id,
                    record_date=record_date,
                    person_name=person_name,
                    person_type=person_type,
                    work_hours=work_hours,
                    advance_payment=advance_payment,
                    remark=remark,
                ))
                success_count += 1
            except Exception as e:
                fail_count += 1
                errors.append(f"第{row_num}行：{str(e)}")

        msg = f"导入完成，成功 {success_count} 条，跳过重复 {skip_count} 条，失败 {fail_count} 条"
        if errors:
            msg += "\n" + "\n".join(errors[:10])
        return Success(msg=msg)
    except Exception as e:
        return Fail(msg=f"导入失败：{str(e)}")


# ==================== 工程师日志（考勤打卡明细） ====================
@router.get("/engineer-attendance/list", summary="查看工程师日志")
async def list_engineer_attendance(
    test_order_no: str = Query(None, description="试验单号"),
    person_name: str = Query(None, description="人员姓名"),
    record_date_start: str = Query(None, description="起始日期"),
    record_date_end: str = Query(None, description="截止日期"),
):
    q = Q()
    if test_order_no:
        q &= Q(test_order__test_order_no__contains=test_order_no)
    if person_name:
        q &= Q(person_name__contains=person_name)
    if record_date_start:
        q &= Q(record_date__gte=record_date_start)
    if record_date_end:
        q &= Q(record_date__lte=record_date_end)

    items = await EngineerAttendance.filter(q).order_by("-record_date").select_related("project", "test_order")
    data = []
    from datetime import time as dt_time, timedelta
    def _fmt_t(v):
        if isinstance(v, dt_time):
            return v.strftime("%H:%M")
        elif isinstance(v, timedelta):
            total_secs = int(v.total_seconds())
            return f"{total_secs // 3600:02d}:{(total_secs % 3600) // 60:02d}"
        return str(v) if v else ""

    for item in items:
        d = await item.to_dict()
        d["start_time"] = _fmt_t(d.get("start_time"))
        d["end_time"] = _fmt_t(d.get("end_time"))
        # 直接从本地DB读取（同步时已写入飞书字段值）
        d["project_name"] = item.project.project_name if item.project else ""
        d["test_order_no"] = item.test_order.test_order_no if item.test_order else (getattr(item, "requirement_code", "") or "")
        data.append(d)
    return Success(data=data)


@router.post("/engineer-attendance/create", summary="创建工程师考勤")
async def create_engineer_attendance(item_in: EngineerAttendanceCreate):
    """手动创建工程师考勤记录"""
    dict_in = item_in.model_dump(exclude_unset=True)

    # 如果没有指定 project_id，自动从人员姓名关联的试验单号中查找
    if not dict_in.get("project_id") and item_in.person_name:
        rp = await RequirementPersonnel.all()
        for p in rp:
            names = (p.outsourced_personnel or "").replace("，", ",").replace("、", ",").split(",")
            names = [n.strip() for n in names if n.strip()]
            if item_in.person_name in names:
                test_order = await TestOrder.filter(test_order_no=p.test_order_no).first()
                if test_order:
                    expense_code = await test_order.expense_code
                    if expense_code:
                        budget = await expense_code.budget
                        if budget and budget.project_id:
                            dict_in["project_id"] = budget.project_id
                            if not dict_in.get("test_order_id"):
                                dict_in["test_order_id"] = test_order.id
                            break

    # 自动设置审批人2（优先取试验单号负责人，其次取项目审批人）
    if not dict_in.get("approver2"):
        test_order_id = dict_in.get("test_order_id")
        if test_order_id:
            test_order = await TestOrder.get_or_none(id=test_order_id)
            if test_order and test_order.responsible_person:
                dict_in["approver2"] = test_order.responsible_person
        if not dict_in.get("approver2") and dict_in.get("project_id"):
            project = await ExpenseProject.get_or_none(id=dict_in["project_id"])
            if project and project.approver:
                dict_in["approver2"] = project.approver
    dict_in["approver2_result"] = "待审批"

    obj = await engineer_attendance_controller.create(obj_in=dict_in)
    await _auto_sync_daily()
    return Success(msg="创建成功")


@router.post("/engineer-attendance/update", summary="更新工程师考勤")
async def update_engineer_attendance(id: int = Query(...), item_in: dict = Body(...)):
    item_in.pop("id", None)
    # 字符串转日期/时间对象
    if "record_date" in item_in and isinstance(item_in["record_date"], str):
        item_in["record_date"] = date.fromisoformat(item_in["record_date"])
    for field_name in ("start_time", "end_time"):
        if field_name in item_in and isinstance(item_in[field_name], str):
            h, m = item_in[field_name].split(":")
            item_in[field_name] = time(int(h), int(m))
    # 移除 None 值避免 Tortoise 外键报错
    item_in = {k: v for k, v in item_in.items() if v is not None}
    await engineer_attendance_controller.update(id=id, obj_in=item_in)
    await _auto_sync_daily()
    return Success(msg="更新成功")


@router.delete("/engineer-attendance/delete", summary="删除工程师考勤")
async def delete_engineer_attendance(id: int = Query(...)):
    await engineer_attendance_controller.remove(id=id)
    await _auto_sync_daily()
    return Success(msg="删除成功")


# ==================== 驾驶员日志 ====================
@router.get("/driver-record/list", summary="查看驾驶员日志")
async def list_driver_records(
    project_id: int = Query(None, description="项目ID"),
    test_order_id: int = Query(None, description="试验单号ID"),
    person_name: str = Query(None, description="人员姓名"),
    record_date_start: str = Query(None, description="起始日期"),
    record_date_end: str = Query(None, description="截止日期"),
):
    items = await daily_record_controller.search(
        project_id=project_id, test_order_id=test_order_id,
        person_name=person_name, person_type="驾驶员",
        record_date_start=record_date_start, record_date_end=record_date_end,
    )
    data = []
    for item in items:
        d = await item.to_dict()
        d["project_name"] = item.project.project_name if item.project else ""
        d["test_order_no"] = item.test_order.test_order_no if item.test_order else ""
        data.append(d)
    return Success(data=data)


# ==================== 驾驶员考勤打卡（新模型） ====================
@router.get("/driver-attendance/list", summary="查看驾驶员考勤列表")
async def list_driver_attendance(
    project_id: int = Query(None, description="项目ID"),
    test_order_id: int = Query(None, description="试验单号ID"),
    test_order_no: str = Query(None, description="试验单号"),
    person_name: str = Query(None, description="人员姓名"),
    record_date_start: str = Query(None, description="起始日期"),
    record_date_end: str = Query(None, description="截止日期"),
):
    q = Q()
    if project_id:
        q &= Q(project_id=project_id)
    if test_order_id:
        q &= Q(test_order_id=test_order_id)
    if test_order_no:
        q &= Q(test_order__test_order_no__contains=test_order_no)
    if person_name:
        q &= Q(person_name__contains=person_name)
    if record_date_start:
        q &= Q(record_date__gte=record_date_start)
    if record_date_end:
        q &= Q(record_date__lte=record_date_end)

    items = await DriverAttendance.filter(q).order_by("-record_date").select_related("project", "test_order")
    data = []
    from datetime import time as dt_time, timedelta
    def _fmt_t(v):
        if isinstance(v, dt_time):
            return v.strftime("%H:%M")
        elif isinstance(v, timedelta):
            total_secs = int(v.total_seconds())
            return f"{total_secs // 3600:02d}:{(total_secs % 3600) // 60:02d}"
        return str(v) if v else ""

    for item in items:
        d = await item.to_dict()
        d["start_time"] = _fmt_t(d.get("start_time"))
        d["end_time"] = _fmt_t(d.get("end_time"))
        # 自动计算测试里程
        init_m = d.get("vehicle_initial_mileage")
        end_m = d.get("vehicle_end_mileage")
        test_m = d.get("vehicle_test_mileage")
        if test_m is None and init_m is not None and end_m is not None:
            d["vehicle_test_mileage"] = max(0, float(Decimal(str(end_m)) - Decimal(str(init_m))))
        # 直接从本地DB读取（同步时已写入飞书字段值）
        d["project_name"] = item.project.project_name if item.project else ""
        d["test_order_no"] = item.test_order.test_order_no if item.test_order else (getattr(item, "requirement_code", "") or "")
        data.append(d)
    return Success(data=data)


@router.post("/driver-attendance/create", summary="创建驾驶员考勤")
async def create_driver_attendance(item_in: DriverAttendanceCreate):
    dict_in = item_in.model_dump(exclude_unset=True)

    # 自动计算测试里程
    init_m = dict_in.get("vehicle_initial_mileage")
    end_m = dict_in.get("vehicle_end_mileage")
    if init_m is not None and end_m is not None:
        dict_in["vehicle_test_mileage"] = max(0, float(Decimal(str(end_m)) - Decimal(str(init_m))))

    # 如果没有指定 project_id，自动从人员姓名关联的试验单号中查找
    if not dict_in.get("project_id") and item_in.person_name:
        rp = await RequirementPersonnel.all()
        for p in rp:
            names = (p.outsourced_personnel or "").replace("，", ",").replace("、", ",").split(",")
            names = [n.strip() for n in names if n.strip()]
            if item_in.person_name in names:
                test_order = await TestOrder.filter(test_order_no=p.test_order_no).first()
                if test_order:
                    expense_code = await test_order.expense_code
                    if expense_code:
                        budget = await expense_code.budget
                        if budget and budget.project_id:
                            dict_in["project_id"] = budget.project_id
                            if not dict_in.get("test_order_id"):
                                dict_in["test_order_id"] = test_order.id
                            break

    # 自动设置审批人2（优先取试验单号负责人，其次取项目审批人）
    if not dict_in.get("approver2"):
        test_order_id = dict_in.get("test_order_id")
        if test_order_id:
            test_order = await TestOrder.get_or_none(id=test_order_id)
            if test_order and test_order.responsible_person:
                dict_in["approver2"] = test_order.responsible_person
        if not dict_in.get("approver2") and dict_in.get("project_id"):
            project = await ExpenseProject.get_or_none(id=dict_in["project_id"])
            if project and project.approver:
                dict_in["approver2"] = project.approver
    dict_in["approver2_result"] = "待审批"

    await driver_attendance_controller.create(obj_in=dict_in)
    await _auto_sync_daily()
    return Success(msg="创建成功")


@router.post("/driver-attendance/update", summary="更新驾驶员考勤")
async def update_driver_attendance(id: int = Query(...), item_in: dict = Body(...)):
    item_in.pop("id", None)
    # 字符串转日期/时间对象
    if "record_date" in item_in and isinstance(item_in["record_date"], str):
        item_in["record_date"] = date.fromisoformat(item_in["record_date"])
    for field_name in ("start_time", "end_time"):
        if field_name in item_in and isinstance(item_in[field_name], str):
            h, m = item_in[field_name].split(":")
            item_in[field_name] = time(int(h), int(m))
    # 自动计算测试里程
    init_m = item_in.get("vehicle_initial_mileage")
    end_m = item_in.get("vehicle_end_mileage")
    if init_m is not None and end_m is not None:
        item_in["vehicle_test_mileage"] = max(0, float(Decimal(str(end_m)) - Decimal(str(init_m))))
    # 移除 None 值避免 Tortoise 外键报错
    item_in = {k: v for k, v in item_in.items() if v is not None}
    await driver_attendance_controller.update(id=id, obj_in=item_in)
    await _auto_sync_daily()
    return Success(msg="更新成功")


@router.delete("/driver-attendance/delete", summary="删除驾驶员考勤")
async def delete_driver_attendance(id: int = Query(...)):
    await driver_attendance_controller.remove(id=id)
    await _auto_sync_daily()
    return Success(msg="删除成功")


# ==================== 供应商单价 ====================
@router.get("/supplier/list", summary="供应商单价列表")
async def list_supplier_rates():
    items = await supplier_rate_controller.model.all()
    data = [await i.to_dict() for i in items]
    return Success(data=data)


@router.post("/supplier/create", summary="新增供应商")
async def create_supplier_rate(item_in: SupplierRateCreate = Body(...)):
    await supplier_rate_controller.create(obj_in=item_in)
    return Success(msg="创建成功")


@router.post("/supplier/update", summary="更新供应商单价")
async def update_supplier_rate(id: int = Query(...), item_in: SupplierRateUpdate = Body(...)):
    await supplier_rate_controller.update(id=id, obj_in=item_in)
    return Success(msg="更新成功")


@router.delete("/supplier/delete", summary="删除供应商")
async def delete_supplier_rate(id: int = Query(...)):
    await supplier_rate_controller.remove(id=id)
    return Success(msg="删除成功")


# ==================== 飞书同步 ====================
@router.post("/feishu-sync", summary="从飞书拉取考勤日志")
async def feishu_sync_expense(
    record_type: str = Query(..., description="engineer 或 driver"),
    date_start: Optional[str] = Query(None, description="起始日期 YYYY-MM-DD"),
    date_end: Optional[str] = Query(None, description="结束日期 YYYY-MM-DD"),
):
    """从飞书多维表格同步工程师/驾驶员考勤日志到本地数据库"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    if record_type not in ("engineer", "driver"):
        return Fail(msg="record_type 必须是 engineer 或 driver")
    table_id = EXPENSE_FEISHU_CONFIG["TABLE_IDS"]["ENGINEER" if record_type == "engineer" else "DRIVER"]
    result = await feishu_sync_service.sync_expense_from_feishu(
        table_id=table_id, record_type=record_type,
        date_start=date_start, date_end=date_end,
    )
    if result.get("success"):
        await _auto_sync_daily()
        return Success(data=result, msg=result.get("message"))
    return Fail(msg=result.get("message", "同步失败"))


@router.post("/feishu-sync-personnel", summary="从飞书拉取人员绑定关系")
async def feishu_sync_personnel():
    """从飞书多维表格同步试验单号与人员绑定关系到本地数据库"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    table_id = EXPENSE_FEISHU_CONFIG["TABLE_IDS"]["PERSONNEL"]
    result = await feishu_sync_service.sync_personnel_from_feishu(table_id=table_id)
    if result.get("success"):
        return Success(data=result, msg=result.get("message"))
    return Fail(msg=result.get("message", "同步失败"))


@router.get("/feishu-table-fields", summary="探查飞书表字段名")
async def feishu_table_fields(
    table_key: str = Query("EXPENSE_CODE", description="配置中的TABLE_ID键名, 如 EXPENSE_CODE"),
):
    """探查飞书表实际字段名，用于构建 FEISHU_FIELD_MAP"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    cfg = EXPENSE_FEISHU_CONFIG
    try:
        token = await feishu_sync_service.get_tenant_access_token(config=cfg)
    except Exception as e:
        return Fail(msg=f"获取token失败: {e}")
    table_id = cfg["TABLE_IDS"].get(table_key)
    if not table_id:
        return Fail(msg=f"未找到 table_key={table_key}")
    from app.log import logger
    try:
        field_items = await feishu_sync_service.get_table_fields(token, table_id, config=cfg)
        fields = [{"field_name": f.get("field_name"), "type": f.get("type")} for f in field_items]
        logger.info(f"[Feishu] 探查表 {table_key} 字段: {[f['field_name'] for f in fields]}")
        return Success(data={"table_key": table_key, "table_id": table_id, "fields": fields})
    except Exception as e:
        return Fail(msg=f"获取字段列表失败: {e}")


@router.get("/feishu-debug-budget", summary="调试：探查试验单预算字段的原始值")
async def feishu_debug_budget(
    test_order_no: str = Query(..., description="试验单号"),
):
    """直接探查飞书表格中某条记录的原始字段值，用于调试预算字段格式"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    from app.models.expense import TestOrder
    cfg = EXPENSE_FEISHU_CONFIG
    try:
        token = await feishu_sync_service.get_tenant_access_token(config=cfg)
    except Exception as e:
        return Fail(msg=f"获取token失败: {e}")

    table_id = cfg["TABLE_IDS"]["PERSONNEL"]
    try:
        records = await feishu_sync_service._fetch_all_records(token, table_id, config=cfg)
    except Exception as e:
        return Fail(msg=f"获取记录失败: {e}")

    # 查找匹配的记录
    match_record = None
    for rec in records:
        fields = rec.get("fields", {})
        raw_val = fields.get("试验需求编号")
        raw_test_no = ""
        if isinstance(raw_val, list) and len(raw_val) > 0:
            if isinstance(raw_val[0], dict):
                raw_test_no = str(raw_val[0].get("text", ""))
            else:
                raw_test_no = str(raw_val[0])
        else:
            raw_test_no = str(raw_val or "")
        if test_order_no in raw_test_no:
            match_record = rec
            break

    if not match_record:
        return Fail(msg=f"飞书表中未找到试验单号: {test_order_no}")

    fields = match_record.get("fields", {})
    budget_raw = fields.get("预算")

    # 取DB当前值
    db_order = await TestOrder.filter(test_order_no=test_order_no).first()
    db_total_price = float(db_order.total_price) if db_order else None

    return Success(data={
        "test_order_no": test_order_no,
        "db_total_price": db_total_price,
        "budget_raw_type": type(budget_raw).__name__,
        "budget_raw_value": repr(budget_raw)[:500],
        "all_field_names": list(fields.keys()),
        "budget_parsed_by_get_number": (
            await _test_get_number(fields, "预算")
        ),
    })


async def _test_get_number(fields, field_name, default=0):
    """模拟 get_number 的解析逻辑"""
    value = fields.get(field_name)
    if value is None:
        return {"raw": None, "parsed": default, "note": "字段不存在"}
    if isinstance(value, (int, float)):
        return {"raw": repr(value), "parsed": float(value), "note": "直接数字"}
    if isinstance(value, str):
        try:
            return {"raw": repr(value), "parsed": float(value.replace(",", "").strip()), "note": "字符串"}
        except (ValueError, TypeError):
            return {"raw": repr(value), "parsed": default, "note": "字符串解析失败"}
    if isinstance(value, dict):
        v = value.get("text", str(value))
        try:
            return {"raw": repr(value), "parsed": float(str(v).replace(",", "").strip()), "note": "dict"}
        except (ValueError, TypeError):
            return {"raw": repr(value), "parsed": default, "note": "dict解析失败"}
    if isinstance(value, list) and len(value) > 0:
        v = value[0]
        if isinstance(v, (int, float)):
            return {"raw": repr(value), "parsed": float(v), "note": "list->数字"}
        if isinstance(v, str):
            try:
                return {"raw": repr(value), "parsed": float(v.replace(",", "").strip()), "note": "list->字符串"}
            except (ValueError, TypeError):
                return {"raw": repr(value), "parsed": default, "note": "list->字符串解析失败"}
        if isinstance(v, dict):
            v = v.get("text", str(v))
            try:
                return {"raw": repr(value), "parsed": float(str(v).replace(",", "").strip()), "note": "list->dict"}
            except (ValueError, TypeError):
                return {"raw": repr(value), "parsed": default, "note": "list->dict解析失败"}
    return {"raw": repr(value), "parsed": default, "note": f"未知类型: {type(value).__name__}"}


@router.post("/feishu-sync-expense-code", summary="从飞书拉取费用号看板数据")
async def feishu_sync_expense_code():
    """从飞书多维表格同步费用号数据到本地数据库（自动创建项目/预算号）"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    table_id = EXPENSE_FEISHU_CONFIG["TABLE_IDS"]["EXPENSE_CODE"]
    result = await feishu_sync_service.sync_expense_code_from_feishu(table_id=table_id)
    if result.get("success"):
        return Success(data=result, msg=result.get("message"))
    return Fail(msg=result.get("message", "同步失败"))


@router.post("/feishu-sync-test-order", summary="从飞书拉取试验单数据")
async def feishu_sync_test_order():
    """从飞书同步试验单数据（人员绑定+试验单+每日记录一次性完成）"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    import traceback as _tb
    try:
        personnel_table = EXPENSE_FEISHU_CONFIG["TABLE_IDS"]["PERSONNEL"]

        # 1. 同步人员绑定（建立人员→试验单号映射）
        await feishu_sync_service.sync_personnel_from_feishu(table_id=personnel_table)

        # 2. 同步试验单数据
        result = await feishu_sync_service.sync_test_order_from_feishu(table_id=personnel_table)

        # 3. 重新生成每日记录（自动关联试验需求编号）
        try:
            await _auto_sync_daily()
            result["daily"] = "每日记录已更新"
        except Exception as e:
            result["daily"] = f"每日记录更新失败: {str(e)}"

        if result.get("success"):
            return Success(data=result, msg=result.get("message"))
        return Fail(msg=result.get("message", "同步失败"))
    except Exception as e:
        logger.error(f"[Feishu] 试验单同步异常: {_tb.format_exc()}")
        return Fail(msg=f"同步异常: {str(e)}")


# 同步状态存储（简单内存状态，用于查询进度）
@router.post("/feishu-sync/engineer", summary="手动同步工程师飞书考勤")
async def sync_engineer_feishu():
    """同步工程师考勤表（新架构：直接调 feishu_sync_service，不依赖外部脚本）"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    try:
        cfg = EXPENSE_FEISHU_CONFIG
        await feishu_sync_service.sync_expense_from_feishu(
            table_id=cfg["TABLE_IDS"]["ENGINEER"], record_type="engineer"
        )
        return Success(msg="工程师考勤同步完成")
    except Exception as e:
        logger.error(f"[飞书同步] 工程师同步失败: {e}")
        return Fail(msg=f"同步失败: {str(e)}")


@router.post("/feishu-sync/driver", summary="手动同步驾驶员飞书考勤")
async def sync_driver_feishu():
    """同步驾驶员考勤表"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    try:
        cfg = EXPENSE_FEISHU_CONFIG
        await feishu_sync_service.sync_expense_from_feishu(
            table_id=cfg["TABLE_IDS"]["DRIVER"], record_type="driver"
        )
        return Success(msg="驾驶员考勤同步完成")
    except Exception as e:
        logger.error(f"[飞书同步] 驾驶员同步失败: {e}")
        return Fail(msg=f"同步失败: {str(e)}")


@router.post("/feishu-sync/all", summary="手动同步全部飞书考勤并刷新每日费用")
async def sync_all_feishu():
    """同步工程师+驾驶员考勤，并重新生成每日费用记录"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    try:
        cfg = EXPENSE_FEISHU_CONFIG
        await feishu_sync_service.sync_expense_from_feishu(
            table_id=cfg["TABLE_IDS"]["ENGINEER"], record_type="engineer"
        )
        await feishu_sync_service.sync_expense_from_feishu(
            table_id=cfg["TABLE_IDS"]["DRIVER"], record_type="driver"
        )
        await _auto_sync_daily()
        return Success(msg="全部考勤同步完成")
    except Exception as e:
        logger.error(f"[飞书同步] 全部同步失败: {e}")
        return Fail(msg=f"同步失败: {str(e)}")


_sync_status = {"running": False, "results": {}, "start_time": None, "end_time": None}

@router.post("/feishu-auto-sync", summary="自动从飞书同步所有数据（后台异步）")
async def feishu_auto_sync():
    """自动同步：人员绑定 ∥ 工程师考勤 ∥ 驾驶员考勤 → 每日费用（后台并行执行，立即返回）"""
    import asyncio as _asyncio
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG

    if _sync_status["running"]:
        return Success(data={
            "status": "running",
            "start_time": str(_sync_status["start_time"]),
        }, msg="同步正在进行中，请稍后查看结果")

    # 标记为运行中
    _sync_status["running"] = True
    _sync_status["results"] = {}
    _sync_status["start_time"] = datetime.now()
    _sync_status["end_time"] = None

    async def _run_sync():
        results = {}
        try:
            # 只同步最近 10 天的数据（快）；午夜同步会拉全量
            ten_days_ago = (datetime.now() - timedelta(days=10)).strftime("%Y-%m-%d")

            # ★ 第一阶段：同步项目层级（费用号看板 → 项目/预算号/费用号）
            # 必须先同步，因为后续考勤同步依赖 TestOrder → ExpenseCode → Budget → Project 链解析项目
            async def sync_expense_code():
                try:
                    return await feishu_sync_service.sync_expense_code_from_feishu(
                        table_id=EXPENSE_FEISHU_CONFIG["TABLE_IDS"]["EXPENSE_CODE"]
                    )
                except Exception as e:
                    import traceback
                    logger.error(f"[Feishu] 费用号同步异常: {traceback.format_exc()}")
                    return {"success": False, "message": str(e)}

            async def sync_test_order():
                try:
                    personnel_table = EXPENSE_FEISHU_CONFIG["TABLE_IDS"]["PERSONNEL"]
                    # 先同步人员绑定（建立人员→试验单号映射）
                    await feishu_sync_service.sync_personnel_from_feishu(table_id=personnel_table)
                    # 再同步试验单数据（关联费用号看板，创建 TestOrder 并链接到 ExpenseCode）
                    return await feishu_sync_service.sync_test_order_from_feishu(table_id=personnel_table)
                except Exception as e:
                    import traceback
                    logger.error(f"[Feishu] 试验单同步异常: {traceback.format_exc()}")
                    return {"success": False, "message": str(e)}

            # 费用号和试验单串行执行（试验单依赖费用号的项目层级）
            ec_result = await sync_expense_code()
            results["expense_code"] = ec_result
            to_result = await sync_test_order()
            results["test_order"] = to_result

            # ★ 预加载：飞书PERSONNEL表 人员姓名→试验单号映射（供考勤同步使用）
            # 策略：用 PERSONNEL 表的「驾驶员」「工程师」字段列出的人员姓名匹配考勤记录
            # 过滤逻辑：通过试验需求编号 Lookup 字段是否包含 tokens 来过滤记录
            #   - 保留：字段值为 array，且其中的 Lookup token 以 "opt" 开头（已关联单据的记录）
            #   - 丢弃：字段值为空、字符串或 token 不以 "opt" 开头（占位引用或未关联的记录）
            # 原因：TYPE_ORDER 表通过 Lookup 关联到 TEST_APPLY 表，只有当关联存在时 token 才会是有效值，
            #   否则飞书会将字段置为空或占位符引用。按此过滤可避免把未关联的"空记录"误匹配到考勤。
            person_to_test_order = {}  # person_name -> [{"test_order_no", "start_date", "end_date"}]
            token_to_test_order = {}   # PERSONNEL_record_id -> test_order_no（供 sync_expense_from_feishu 使用）
            project_to_test_order = {} # 车型项目-选项 -> [同上]（opt token 不匹配时按车型项目匹配试验单）
            try:
                from app.api.v1.expense.feishu_sync import EXPENSE_FEISHU_CONFIG as _CFG
                _ptoken = await feishu_sync_service.get_tenant_access_token(config=_CFG)
                _precords = await feishu_sync_service._fetch_all_records(
                    _ptoken, _CFG["TABLE_IDS"]["PERSONNEL"], config=_CFG
                )
                for _pr in _precords:
                    _pr_fields = _pr.get("fields", {})
                    _pr_id = _pr.get("record_id", "")
                    # 提取试验需求编号
                    _tno_val = _pr_fields.get("试验需求编号") or _pr_fields.get("试验单号")
                    _tno = ""
                    if isinstance(_tno_val, list) and len(_tno_val) > 0:
                        if isinstance(_tno_val[0], dict):
                            _tno = str(_tno_val[0].get("text", ""))
                        else:
                            _tno = str(_tno_val[0])
                    elif isinstance(_tno_val, str):
                        _tno = _tno_val
                    if _tno and _pr_id:
                        token_to_test_order[_pr_id] = _tno
                    if not _tno:
                        continue
                    # 提取人员名单（驾驶员 + 工程师）
                    def _extract_names(val):
                        if not val:
                            return []
                        if isinstance(val, list):
                            return [str(v).strip() for v in val if isinstance(v, str) and v.strip()]
                        if isinstance(val, str):
                            return [n.strip() for n in val.split(",") if n.strip()]
                        return []
                    _drv_names = _extract_names(_pr_fields.get("驾驶员"))
                    _eng_names = _extract_names(_pr_fields.get("工程师"))
                    _all_names = list(set(_drv_names + _eng_names))
                    # 提取日期范围（用于日期匹配消歧义）
                    _start_date = None
                    _end_date = None
                    _start_raw = _pr_fields.get("试验开始日期")
                    _end_raw = _pr_fields.get("试验结束日期")
                    if isinstance(_start_raw, (int, float)) and _start_raw > 10000000000:
                        _start_date = date.fromtimestamp(_start_raw / 1000)
                    if isinstance(_end_raw, (int, float)) and _end_raw > 10000000000:
                        _end_date = date.fromtimestamp(_end_raw / 1000)
                    _rec_info = {"test_order_no": _tno, "start_date": _start_date, "end_date": _end_date, "personnel": list(_all_names)}
                    for _name in _all_names:
                        person_to_test_order.setdefault(_name, []).append(_rec_info)
                    # 车型项目-选项 -> 试验单（opt token 不匹配时按车型项目匹配）
                    _proj_val = _pr_fields.get("车型项目-选项")
                    _proj = str(_proj_val).strip() if _proj_val else ""
                    if _proj:
                        project_to_test_order.setdefault(_proj, []).append(_rec_info)
                # 调试：打印前 5 条 token_to_test_order 样例
                _sample_tokens = list(token_to_test_order.items())[:5]
                logger.info(f"[Feishu] 预加载 人员→试验单号映射: {len(person_to_test_order)} 人, {sum(len(v) for v in person_to_test_order.values())} 条关联; token→试验单号: {len(token_to_test_order)} 条, 样例: {_sample_tokens}")
            except Exception as _e:
                logger.warning(f"[Feishu] 预加载人员映射失败: {_e}")
                person_to_test_order = {}
                token_to_test_order = {}

            # ★ 第二阶段：并行同步考勤（此时项目层级已就绪，可正确解析项目）
            async def sync_engineer():
                try:
                    return await feishu_sync_service.sync_expense_from_feishu(
                        table_id=EXPENSE_FEISHU_CONFIG["TABLE_IDS"]["ENGINEER"],
                        record_type="engineer",
                        date_start=ten_days_ago,
                        token_to_test_order=token_to_test_order,
                        person_to_test_order=person_to_test_order,
                        project_to_test_order=project_to_test_order,
                    )
                except Exception as e:
                    import traceback
                    logger.error(f"[Feishu] 工程师同步异常: {traceback.format_exc()}")
                    return {"success": False, "message": str(e)}

            async def sync_driver():
                try:
                    return await feishu_sync_service.sync_expense_from_feishu(
                        table_id=EXPENSE_FEISHU_CONFIG["TABLE_IDS"]["DRIVER"],
                        record_type="driver",
                        date_start=ten_days_ago,
                        token_to_test_order=token_to_test_order,
                        person_to_test_order=person_to_test_order,
                        project_to_test_order=project_to_test_order,
                    )
                except Exception as e:
                    import traceback
                    logger.error(f"[Feishu] 驾驶员同步异常: {traceback.format_exc()}")
                    return {"success": False, "message": str(e)}

            # 并行执行工程师和驾驶员考勤同步
            e_result, d_result = await _asyncio.gather(
                sync_engineer(), sync_driver(),
                return_exceptions=True  # 改为 True 防止单个异常导致整体失败
            )
            # 处理 gather 返回的异常
            if isinstance(e_result, BaseException):
                logger.error(f"[Feishu] 工程师同步 gather 异常: {e_result}")
                results["engineer"] = {"success": False, "message": str(e_result)}
            else:
                results["engineer"] = e_result
            if isinstance(d_result, BaseException):
                logger.error(f"[Feishu] 驾驶员同步 gather 异常: {d_result}")
                results["driver"] = {"success": False, "message": str(d_result)}
            else:
                results["driver"] = d_result

            # ★ 第三阶段：每日费用依赖前面的同步结果，串行执行
            try:
                await _auto_sync_daily()
                results["daily"] = {"success": True, "message": "每日费用同步完成"}
            except Exception as e:
                results["daily"] = {"success": False, "message": str(e)}
                logger.error(f"[Feishu] 每日费用同步异常: {e}")

        except BaseException as e:
            import traceback
            logger.error(f"[Feishu] 自动同步异常(BaseException): {traceback.format_exc()}")
            results["_error"] = str(e)
        finally:
            _sync_status["results"] = results
            _sync_status["end_time"] = datetime.now()
            _sync_status["running"] = False
            logger.info(f"[Feishu] 同步状态已更新: running=False, results_keys={list(results.keys())}")

    # 后台运行，带超时保护（最长 300 秒）
    async def _run_with_timeout():
        try:
            await _asyncio.wait_for(_run_sync(), timeout=300)
        except _asyncio.TimeoutError:
            logger.error("[Feishu] 同步超时（超过300秒）")
            _sync_status["results"] = {"error": "同步超时（超过5分钟），请稍后重试"}
            _sync_status["end_time"] = datetime.now()
            _sync_status["running"] = False
        except Exception as e:
            import traceback
            logger.error(f"[Feishu] _run_with_timeout 异常: {traceback.format_exc()}")
            _sync_status["results"] = {"error": f"同步异常: {str(e)}"}
            _sync_status["end_time"] = datetime.now()
            _sync_status["running"] = False

    _asyncio.ensure_future(_run_with_timeout())

    return Success(data={
        "status": "started",
        "start_time": str(_sync_status["start_time"]),
    }, msg="同步任务已启动，正在后台执行中")


@router.get("/feishu-auto-sync/status", summary="查询飞书同步进度")
async def feishu_auto_sync_status():
    """查询后台同步任务的状态和结果"""
    try:
        running = _sync_status.get("running", False)
        start_time = _sync_status.get("start_time")
        end_time = _sync_status.get("end_time")
        results = _sync_status.get("results", {})

        # 自动恢复：如果同步标记为运行中但已超过 10 分钟，视为卡死，自动重置
        if running and start_time:
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > 600:
                logger.warning(f"[Feishu] 同步状态卡死超过 10 分钟，自动重置 (elapsed={elapsed:.0f}s)")
                _sync_status["running"] = False
                _sync_status["results"] = {"error": "上次同步超时或异常，状态已自动重置"}
                _sync_status["end_time"] = datetime.now()
                running = False
                results = _sync_status["results"]

        return Success(data={
            "running": running,
            "start_time": str(start_time) if start_time else None,
            "end_time": str(end_time) if end_time else None,
            "results": results,
        })
    except Exception as e:
        import traceback
        logger.error(f"[Feishu] 同步状态查询异常: {traceback.format_exc()}")
        # 返回安全的默认状态
        return Success(data={
            "running": False,
            "start_time": None,
            "end_time": None,
            "results": {"error": f"状态查询异常: {str(e)}"},
        })


@router.post("/feishu-auto-sync/reset", summary="强制重置飞书同步状态")
async def feishu_auto_sync_reset():
    """当同步卡住时，强制重置同步状态，允许重新同步"""
    was_running = _sync_status["running"]
    _sync_status["running"] = False
    _sync_status["results"] = {}
    _sync_status["start_time"] = None
    _sync_status["end_time"] = None
    logger.info(f"[Feishu] 同步状态已强制重置 (之前 {'正在运行' if was_running else '已停止'})")
    return Success(data={"was_running": was_running}, msg="同步状态已重置，可重新发起同步")


# ==================== 飞书实时查询（直连飞书 API，获取原始字段值含公式计算结果） ====================
@router.get("/feishu-engineer-log", summary="从飞书直接查询工程师日志")
async def feishu_engineer_log(
    person_name: str = Query(None, description="填写人筛选"),
    record_date_start: str = Query(None, description="起始日期 YYYY-MM-DD"),
    record_date_end: str = Query(None, description="截止日期 YYYY-MM-DD"),
    test_order_no: str = Query(None, description="试验需求编号筛选"),
    page_size: int = Query(500, description="每页条数"),
    page_token: str = Query(None, description="分页标记"),
):
    """直连飞书多维表格，读取工程师日志原始数据（含公式字段计算结果）"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    cfg = EXPENSE_FEISHU_CONFIG
    try:
        token = await feishu_sync_service.get_tenant_access_token(config=cfg)
    except Exception as e:
        return Fail(msg=f"获取飞书token失败: {str(e)}")

    table_id = cfg["TABLE_IDS"]["ENGINEER"]
    filter_formula = None
    conditions = []
    if record_date_start:
        conditions.append(f'CurrentValue.[日期] >= TODATE("{record_date_start}")')
    if record_date_end:
        conditions.append(f'CurrentValue.[日期] <= TODATE("{record_date_end}")')
    if conditions:
        filter_formula = " && ".join(conditions)

    try:
        result = await feishu_sync_service.get_bitable_records(
            token, table_id, page_token=page_token, config=cfg, filter_formula=filter_formula,
        )
        records = result.get("items") or []
        has_more = result.get("has_more", False)
        next_page_token = result.get("page_token", "")

        # 返回原始字段值（飞书 API 已包含公式字段的计算结果）
        def _extract(val):
            """提取飞书字段的显示值"""
            if val is None:
                return None
            # 处理大整数时间戳（毫秒级，>10^12 约为 2001 年）
            if isinstance(val, int) and val > 1000000000000:
                try:
                    return datetime.fromtimestamp(val / 1000).strftime("%Y-%m-%d %H:%M:%S")
                except (OSError, ValueError):
                    return val
            if isinstance(val, list) and len(val) > 0:
                if isinstance(val[0], dict):
                    if "name" in val[0]:
                        return [v["name"] for v in val] if len(val) > 1 else val[0]["name"]
                    if "text" in val[0]:
                        return val[0]["text"]
                    return str(val[0])
                return val[0] if len(val) == 1 else [v for v in val]
            if isinstance(val, dict):
                # 飞书人员字段: {'users': [{'name': '徐光龙', ...}]}
                if "users" in val:
                    users = val["users"]
                    if isinstance(users, list) and len(users) > 0:
                        names = [u.get("name", str(u)) for u in users if isinstance(u, dict)]
                        return names[0] if len(names) == 1 else names
                return val.get("text") or val.get("name") or str(val)
            return val

        data_rows = []
        for record in records:
            raw_fields = record.get("fields", {})
            row = {
                "record_id": record.get("record_id", ""),
            }
            for field_name, field_value in raw_fields.items():
                row[field_name] = _extract(field_value)
            data_rows.append(row)

        # 客户端侧按人名/试验单号做简单过滤（飞书 API filter 不支持这些非日期字段）
        if person_name:
            data_rows = [r for r in data_rows if person_name in str(r.get("填写人", "") or r.get("填写人-人名", ""))]
        if test_order_no:
            data_rows = [r for r in data_rows if test_order_no in str(r.get("根据填写人选择，生成试验单号", ""))]

        return Success(data={
            "records": data_rows,
            "total": len(data_rows),
            "has_more": has_more,
            "page_token": next_page_token,
            "source": "feishu_realtime",
        })
    except Exception as e:
        logger.error(f"[Feishu] 实时查询工程师日志失败: {e}")
        return Fail(msg=f"查询飞书失败: {str(e)}")


@router.get("/feishu-driver-log", summary="从飞书直接查询驾驶员日志")
async def feishu_driver_log(
    person_name: str = Query(None, description="填写人筛选"),
    record_date_start: str = Query(None, description="起始日期 YYYY-MM-DD"),
    record_date_end: str = Query(None, description="截止日期 YYYY-MM-DD"),
    test_order_no: str = Query(None, description="试验需求单号筛选"),
    page_size: int = Query(500, description="每页条数"),
    page_token: str = Query(None, description="分页标记"),
):
    """直连飞书多维表格，读取驾驶员日志原始数据（含公式字段计算结果）"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    cfg = EXPENSE_FEISHU_CONFIG
    try:
        token = await feishu_sync_service.get_tenant_access_token(config=cfg)
    except Exception as e:
        return Fail(msg=f"获取飞书token失败: {str(e)}")

    table_id = cfg["TABLE_IDS"]["DRIVER"]
    filter_formula = None
    conditions = []
    if record_date_start:
        conditions.append(f'CurrentValue.[日期] >= TODATE("{record_date_start}")')
    if record_date_end:
        conditions.append(f'CurrentValue.[日期] <= TODATE("{record_date_end}")')
    if conditions:
        filter_formula = " && ".join(conditions)

    try:
        result = await feishu_sync_service.get_bitable_records(
            token, table_id, page_token=page_token, config=cfg, filter_formula=filter_formula,
        )
        records = result.get("items") or []
        has_more = result.get("has_more", False)
        next_page_token = result.get("page_token", "")

        def _extract(val):
            if val is None:
                return None
            # 处理大整数时间戳（毫秒级，>10^12 约为 2001 年）
            if isinstance(val, int) and val > 1000000000000:
                try:
                    return datetime.fromtimestamp(val / 1000).strftime("%Y-%m-%d %H:%M:%S")
                except (OSError, ValueError):
                    return val
            if isinstance(val, list) and len(val) > 0:
                if isinstance(val[0], dict):
                    if "name" in val[0]:
                        return [v["name"] for v in val] if len(val) > 1 else val[0]["name"]
                    if "text" in val[0]:
                        return val[0]["text"]
                    return str(val[0])
                return val[0] if len(val) == 1 else [v for v in val]
            if isinstance(val, dict):
                # 飞书人员字段: {'users': [{'name': '徐光龙', ...}]}
                if "users" in val:
                    users = val["users"]
                    if isinstance(users, list) and len(users) > 0:
                        names = [u.get("name", str(u)) for u in users if isinstance(u, dict)]
                        return names[0] if len(names) == 1 else names
                return val.get("text") or val.get("name") or str(val)
            return val

        data_rows = []
        for record in records:
            raw_fields = record.get("fields", {})
            row = {
                "record_id": record.get("record_id", ""),
            }
            for field_name, field_value in raw_fields.items():
                row[field_name] = _extract(field_value)
            data_rows.append(row)

        if person_name:
            data_rows = [r for r in data_rows if person_name in str(r.get("填写人", "") or r.get("填写人-人名", ""))]
        if test_order_no:
            data_rows = [r for r in data_rows if test_order_no in str(r.get("试验需求编号", "") or r.get("根据填写人选择，生成试验单号", ""))]

        return Success(data={
            "records": data_rows,
            "total": len(data_rows),
            "has_more": has_more,
            "page_token": next_page_token,
            "source": "feishu_realtime",
        })
    except Exception as e:
        logger.error(f"[Feishu] 实时查询驾驶员日志失败: {e}")
        return Fail(msg=f"查询飞书失败: {str(e)}")


# ==================== 飞书实时每日费用 ====================
# ── 每日费用（飞书实时）响应缓存 ──
# 飞书数据仅午夜同步，短TTL可把"重复加载"从 ~70s 降到毫秒级；不同查询参数独立缓存
_FEISHU_DAILY_RECORD_CACHE: dict = {}
_FEISHU_DAILY_RECORD_TTL = 90  # 秒

# ── 人员→试验需求编号 飞书映射缓存（用于每日费用列表）──
_PERSONNEL_MAP_CACHE: dict = {}
_PERSONNEL_MAP_TTL = 120  # 2分钟，飞书数据变化不频繁，短TTL平衡实时性与性能


async def _get_personnel_test_order_map():
    """从飞书 PERSONNEL 表获取 人员→试验需求编号 映射（含缓存）"""
    _cache_key = "_personnel_map"
    _hit = _PERSONNEL_MAP_CACHE.get(_cache_key)
    if _hit is not None and _time.time() < _hit[0]:
        return _hit[1]

    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG
    cfg = EXPENSE_FEISHU_CONFIG

    try:
        token = await feishu_sync_service.get_tenant_access_token(config=cfg)
    except Exception as e:
        logger.warning(f"[Feishu] 获取PERSONNEL表token失败: {e}")
        return {}

    _PERSONNEL_FIELDS = ["试验需求编号", "试验单号", "委外人员", "外包人员"]
    try:
        records = await feishu_sync_service._fetch_all_records(
            token, cfg["TABLE_IDS"]["PERSONNEL"], config=cfg, field_names=_PERSONNEL_FIELDS)
    except Exception as e:
        logger.warning(f"[Feishu] 获取PERSONNEL表记录失败: {e}")
        return {}

    mapping = {}
    for rec in records:
        f = rec.get("fields", {})
        # 提取试验需求编号
        tno = feishu_sync_service._extract_feishu_field_value(f, "试验需求编号")
        if not tno:
            continue
        tno = str(tno).strip()
        # 提取试验单号（独立字段，优先级更高）
        tsno = feishu_sync_service._extract_feishu_field_value(f, "试验单号")
        final_tno = (str(tsno).strip() or tno) if tsno else tno
        if not final_tno:
            continue

        # 提取人员名单（委外人员/外包人员）
        pers_raw = f.get("委外人员", "") or f.get("外包人员", "") or ""
        if isinstance(pers_raw, list):
            persons = []
            for item in pers_raw:
                if isinstance(item, dict):
                    persons.append(str(item.get("name", item.get("text", str(item)))))
                else:
                    persons.append(str(item))
        else:
            persons = str(pers_raw).replace("，", ",").replace("、", ",").split(",")

        for pn in persons:
            pn = str(pn).strip()
            if pn and final_tno:
                mapping[pn] = final_tno

    _PERSONNEL_MAP_CACHE[_cache_key] = (_time.time() + _PERSONNEL_MAP_TTL, mapping)
    logger.info(f"[Feishu] 人员→试验需求编号映射已加载: {len(mapping)} 条")
    return mapping


@router.get("/feishu-daily-record", summary="从飞书直接查询每日费用")
async def feishu_daily_record(
        person_name: str = Query(None, description="人员筛选"),
        record_date_start: str = Query(None, description="起始日期 YYYY-MM-DD"),
        record_date_end: str = Query(None, description="截止日期 YYYY-MM-DD"),
        test_order_no: str = Query(None, description="试验需求编号筛选"),
        project_name: str = Query(None, description="项目名称筛选"),
        refresh: bool = Query(False, description="强制刷新，跳过缓存重新从飞书拉取"),
):
    """从飞书工程师+驾驶员日志表直接计算每日费用（含试验需求编号，不依赖本地DB）"""
    from app.api.v1.expense.feishu_sync import feishu_sync_service, EXPENSE_FEISHU_CONFIG

    cfg = EXPENSE_FEISHU_CONFIG

    # ── 默认日期窗口 + 响应缓存 ──
    # 无日期时默认"当月1号~今天"，避免对 ENGINEER/DRIVER 全表扫描（实测无日期 >120s 超时）
    today = date.today()
    if not record_date_start:
        record_date_start = today.replace(day=1).strftime("%Y-%m-%d")
    if not record_date_end:
        record_date_end = today.strftime("%Y-%m-%d")
    _cache_key = "|".join([
        str(record_date_start), str(record_date_end),
        str(person_name or ""), str(test_order_no or ""), str(project_name or ""),
    ])
    _hit = _FEISHU_DAILY_RECORD_CACHE.get(_cache_key)
    if _hit is not None and not refresh and _time.time() < _hit[0]:
        cached = _hit[1]
        return Success(data=cached["records"], total=cached["total"],
                       filtered_total=cached["filtered_total"], source=cached.get("source", "feishu_realtime"))
    try:
        token = await feishu_sync_service.get_tenant_access_token(config=cfg)
    except Exception as e:
        return Fail(msg=f"获取飞书token失败: {str(e)}")

    # ── 通用提取函数 ──
    def _extract(val):
        if val is None:
            return None
        if isinstance(val, int) and val > 1000000000000:
            try:
                return datetime.fromtimestamp(val / 1000).strftime("%Y-%m-%d %H:%M:%S")
            except (OSError, ValueError):
                return val
        if isinstance(val, list) and len(val) > 0:
            if isinstance(val[0], dict):
                if "name" in val[0]:
                    return [v["name"] for v in val] if len(val) > 1 else val[0]["name"]
                if "text" in val[0]:
                    return val[0]["text"]
                return str(val[0])
            return val[0] if len(val) == 1 else [v for v in val]
        if isinstance(val, dict):
            if "users" in val:
                users = val["users"]
                if isinstance(users, list) and len(users) > 0:
                    names = [u.get("name", str(u)) for u in users if isinstance(u, dict)]
                    return names[0] if len(names) == 1 else names
            return val.get("text") or val.get("name") or str(val)
        return val

    # ── 1. 并行预取三张表（人员绑定 / 工程师 / 驾驶员）──
    # 用 ensure_future 让三张表的飞书请求并发执行，后续各自 await，把"串行 3 次"压成"最慢 1 次"
    _PERSONNEL_FIELDS = ["试验需求编号", "供应商名称", "委外人员", "外包人员",
                         "试验单号", "项目", "车型项目", "所属项目", "填写人选择填写车型项目",
                         "查询填写人所在车型项目"]
    _ENGINEER_FIELDS = ["填写人", "日期", "试验需求编号", "根据填写人选择，生成试验单号",
                        "工作日时长", "加班时长", "出差状态", "审批人1审批结果", "审批人2审核结果"]
    _DRIVER_FIELDS = ["填写人", "日期", "试验需求编号", "根据填写人选择，生成试验单号",
                      "工作日时长", "加班时长", "出差状态", "垫付费用", "审批人1审批结果", "审批人2审核结果"]

    _task_p = asyncio.ensure_future(feishu_sync_service._fetch_all_records(
        token, cfg["TABLE_IDS"]["PERSONNEL"], config=cfg, field_names=_PERSONNEL_FIELDS))
    _task_e = asyncio.ensure_future(feishu_sync_service._fetch_all_records(
        token, cfg["TABLE_IDS"]["ENGINEER"], config=cfg,
        date_field="日期", date_start=record_date_start, date_end=record_date_end,
        field_names=_ENGINEER_FIELDS))
    _task_d = asyncio.ensure_future(feishu_sync_service._fetch_all_records(
        token, cfg["TABLE_IDS"]["DRIVER"], config=cfg,
        date_field="日期", date_start=record_date_start, date_end=record_date_end,
        field_names=_DRIVER_FIELDS))

    # ── 1. 读取人员绑定表（试验单号 → 供应商、人员）──
    personnel_entries = []  # [(test_order_no, person_name, supplier), ...]
    # ★ 反向映射：根据人员姓名查找试验单号和项目
    _personnel_map: dict = {}  # person_name → {test_order_no, project_name}
    pers_records = []
    try:
        pers_records = await _task_p
        # 调试：打印前3条记录的字段名，确认飞书返回的字段名与代码一致
        for idx, rec in enumerate(pers_records[:3]):
            logger.info(f"[Feishu] PERSONNEL 第{idx+1}行字段: {sorted(rec.get('fields', {}).keys())}")
        for rec in pers_records:
            f = rec.get("fields", {})
            tno = _extract(f.get("试验需求编号", "")) or ""
            if isinstance(tno, list):
                tno = tno[0] if tno else ""
            tno = str(tno).strip()
            supplier = _extract(f.get("供应商名称", "")) or ""
            if isinstance(supplier, list):
                supplier = supplier[0] if supplier else ""
            supplier = str(supplier).strip()
            # ★ 从 PERSONNEL 表读取试验单号（独立于试验需求编号）
            tsno = _extract(f.get("试验单号", "")) or ""
            if isinstance(tsno, list):
                tsno = tsno[0] if tsno else ""
            tsno = str(tsno).strip()
            # ★ 从 PERSONNEL 表读取项目（尝试多个可能的字段名）
            proj = ""
            for proj_key in ("项目", "车型项目", "所属项目", "填写人选择填写车型项目", "查询填写人所在车型项目"):
                proj_val = _extract(f.get(proj_key, "")) or ""
                if proj_val and str(proj_val).strip() and str(proj_val).strip().lower() != "none":
                    proj = str(proj_val).strip()
                    break
            pers_raw = f.get("委外人员", "") or f.get("外包人员", "") or ""
            pers_val = _extract(pers_raw) or ""
            if isinstance(pers_val, list):
                persons = pers_val
            else:
                persons = str(pers_val).replace("，", ",").replace("、", ",").split(",")
            for pn in persons:
                pn = str(pn).strip()
                if pn:
                    if tno:
                        personnel_entries.append((tno, pn, supplier))
                    # ★ 反向映射：人员姓名 → 试验单号 + 项目（不依赖试验需求编号是否为空）
                    effective_tno = tsno or tno
                    if effective_tno and (pn not in _personnel_map):
                        _personnel_map[pn] = {"test_order_no": effective_tno, "project_name": proj}
                    elif pn not in _personnel_map:
                        _personnel_map[pn] = {"test_order_no": "", "project_name": proj}
    except Exception as e:
        logger.warning(f"[Feishu] 获取人员绑定表失败: {e}")

    logger.info(f"[Feishu] PERSONNEL 表共 {len(pers_records)} 行，"
                f"人员映射 {len(_personnel_map)} 人，"
                f"供应商绑定 {len(personnel_entries)} 条")

    def _find_supplier(tno, pn):
        for t, p, s in personnel_entries:
            if t == tno and p == pn:
                return s
        return ""

    def _find_personnel_info(pn):
        """根据人员姓名从 PERSONNEL 表查找试验单号和项目"""
        return _personnel_map.get(pn, {})

    # ── 2. 读取工程师日志 ──
    eng_rows = []
    try:
        eng_records = await _task_e
        for rec in eng_records:
            f = rec.get("fields", {})
            person = _extract(f.get("填写人", "")) or ""
            if isinstance(person, list):
                person = person[0] if person else ""
            person = str(person).strip()
            rec_date = _extract(f.get("日期", ""))
            if isinstance(rec_date, str) and len(rec_date) >= 10:
                rec_date = rec_date[:10]
            else:
                rec_date = ""
            tno = _extract(f.get("试验需求编号", "")) or _extract(f.get("根据填写人选择，生成试验单号", "")) or ""
            if isinstance(tno, list):
                tno = tno[0] if tno else ""
            tno = str(tno).strip()
            eng_rows.append({
                "person": person, "date": rec_date, "tno": tno,
                "normal_hours": float(f.get("工作日时长", 0) or 0),
                "overtime_hours": float(f.get("加班时长", 0) or 0),
                "travel_status": str(_extract(f.get("出差状态", "")) or "未出差"),
                "approval1": str(_extract(f.get("审批人1审批结果", "")) or ""),
                "approval2": str(_extract(f.get("审批人2审核结果", "")) or ""),
                "source": "engineer",
            })
    except Exception as e:
        logger.warning(f"[Feishu] 获取工程师表失败: {e}")

    # ── 3. 读取驾驶员日志 ──
    drv_rows = []
    try:
        drv_records = await _task_d
        for rec in drv_records:
            f = rec.get("fields", {})
            person = _extract(f.get("填写人", "")) or ""
            if isinstance(person, list):
                person = person[0] if person else ""
            person = str(person).strip()
            rec_date = _extract(f.get("日期", ""))
            if isinstance(rec_date, str) and len(rec_date) >= 10:
                rec_date = rec_date[:10]
            else:
                rec_date = ""
            tno = _extract(f.get("试验需求编号", "")) or _extract(f.get("根据填写人选择，生成试验单号", "")) or ""
            if isinstance(tno, list):
                tno = tno[0] if tno else ""
            tno = str(tno).strip()
            advance = 0
            adv_val = _extract(f.get("垫付费用", "")) or 0
            if isinstance(adv_val, (int, float)):
                advance = float(adv_val)
            drv_rows.append({
                "person": person, "date": rec_date, "tno": tno,
                "normal_hours": float(f.get("工作日时长", 0) or 0),
                "overtime_hours": float(f.get("加班时长", 0) or 0),
                "travel_status": str(_extract(f.get("出差状态", "")) or "未出差"),
                "advance": advance,
                "approval1": str(_extract(f.get("审批人1审批结果", "")) or ""),
                "approval2": str(_extract(f.get("审批人2审核结果", "")) or ""),
                "source": "driver",
            })
    except Exception as e:
        logger.warning(f"[Feishu] 获取驾驶员表失败: {e}")

    # ── 4. 读取供应商单价 ──
    sr_list = await SupplierRate.all()
    RATES_BY_DATE = {}
    for sr in sr_list:
        RATES_BY_DATE.setdefault(sr.name, []).append({
            "local": float(sr.local_rate), "trip": float(sr.trip_rate),
            "unit": sr.unit,
            "effective_from": sr.effective_from,
            "effective_to": sr.effective_to,
        })
    for rates in RATES_BY_DATE.values():
        rates.sort(key=lambda r: (r["effective_from"] or date.min, r["effective_to"] or date.max))

    def _calc_total(supplier_name, travel_status, normal_h, overtime_h, advance, rec_date):
        sup = (supplier_name or "").strip()
        all_rates = RATES_BY_DATE.get(sup, RATES_BY_DATE.get("育喆", []))
        cfg_rate = None
        for r in all_rates:
            ef = r["effective_from"]
            et = r["effective_to"]
            if rec_date:
                if (ef is None or rec_date >= str(ef)) and (et is None or rec_date <= str(et)):
                    cfg_rate = r; break
            else:
                cfg_rate = r
        if not cfg_rate:
            cfg_rate = all_rates[-1] if all_rates else {"local": 290, "trip": 356, "unit": "day"}
        is_trip = str(travel_status) == "出差"
        rv = cfg_rate["trip"] if is_trip else cfg_rate["local"]
        effective = rv / 8 if cfg_rate["unit"] == "day" else rv
        return round((normal_h + overtime_h) * effective + advance, 2)

    def _get_approval(a1, a2):
        a1s = str(a1 or "").strip()
        a2s = str(a2 or "").strip()
        approved = {"通过", "批准", "已通过", "同意", "审核通过", "已审批"}
        rejected = {"驳回", "已驳回", "拒绝", "不通过", "未通过"}
        if a1s in approved or a2s in approved:
            return "通过"
        if a1s in rejected or a2s in rejected:
            return "驳回"
        return "待审批"

    # ── 5. 合并生成每日费用 ──
    # ★ 先根据人员姓名补充试验单号，避免同一天同一人因原始 tno 为空而被分成多条
    all_rows = eng_rows + drv_rows
    for row in all_rows:
        pn_info = _find_personnel_info(row["person"])
        if pn_info.get("test_order_no"):
            row["tno"] = pn_info["test_order_no"]
    
    merged = {}  # key: (date, person, tno) -> merged row
    for row in all_rows:
        key = (row["date"], row["person"], row["tno"])
        if key not in merged:
            merged[key] = {
                "record_date": row["date"],
                "person_name": row["person"],
                "test_order_no": row["tno"],
                "normal_hours": 0, "overtime_hours": 0,
                "advance_payment": 0, "travel_status": "未出差",
                "approval1": "", "approval2": "",
                "sources": set(),
            }
        m = merged[key]
        m["normal_hours"] += row["normal_hours"]
        m["overtime_hours"] += row["overtime_hours"]
        m["advance_payment"] += row.get("advance", 0)
        if row.get("travel_status") and row["travel_status"] != "未出差":
            m["travel_status"] = row["travel_status"]
        if row.get("approval1"):
            m["approval1"] = row["approval1"]
        if row.get("approval2"):
            m["approval2"] = row["approval2"]
        m["sources"].add(row["source"])

    daily_list = []
    for key, m in merged.items():
        sup = _find_supplier(m["test_order_no"], m["person_name"])
        if not sup:
            # 没有绑定时根据人员来源推断
            if "driver" in m["sources"] and "engineer" not in m["sources"]:
                sup = "育喆"
        # ★ 从 PERSONNEL 表按人员姓名补充试验单号和项目（PERSONNEL 表为权威来源）
        pn_info = _find_personnel_info(m["person_name"])
        final_tno = pn_info.get("test_order_no", "") or m["test_order_no"]
        final_project = pn_info.get("project_name", "")
        ptype = "驾驶员" if sup in ("万嘉禾", "育喆", "驰恒") or "driver" in m["sources"] else "工程师"
        total = _calc_total(sup or "", m["travel_status"], m["normal_hours"],
                            m["overtime_hours"], m["advance_payment"], m["record_date"])
        daily_list.append({
            "record_date": m["record_date"],
            "person_name": m["person_name"],
            "test_order_no": final_tno,
            "project_name": final_project,
            "supplier": sup or "",
            "person_type": ptype,
            "normal_hours": m["normal_hours"],
            "overtime_hours": m["overtime_hours"],
            "advance_payment": m["advance_payment"],
            "travel_status": m["travel_status"],
            "total_amount": total,
            "approval_status": _get_approval(m["approval1"], m["approval2"]),
            "source": "飞书",
        })

    # ── 6. 筛选 ──
    if person_name:
        daily_list = [d for d in daily_list if person_name in d["person_name"]]
    if test_order_no:
        daily_list = [d for d in daily_list if test_order_no in d["test_order_no"]]
    if project_name:
        daily_list = [d for d in daily_list if project_name in d.get("project_name", "")]

    # 按日期倒序
    daily_list.sort(key=lambda d: d["record_date"] or "", reverse=True)

    filtered_total = sum(d["total_amount"] for d in daily_list)

    _feishu_daily_data = {
        "records": daily_list,
        "total": len(daily_list),
        "filtered_total": filtered_total,
        "source": "feishu_realtime",
    }
    _FEISHU_DAILY_RECORD_CACHE[_cache_key] = (_time.time() + _FEISHU_DAILY_RECORD_TTL, _feishu_daily_data)
    # 返回格式兼容前端：data=records数组，total/filtered_total/source 作为顶级字段
    return Success(data=daily_list, total=len(daily_list), filtered_total=filtered_total, source="feishu_realtime")


# ==================== 审批待办 ====================
@router.get("/pending-approval/list", summary="查看待审批列表")
async def list_pending_approvals(
    token: str = Header(None),
):
    """查询所有待审批的工程师/驾驶员考勤记录"""
    eng_pending = await EngineerAttendance.filter(approver2_result="待审批").order_by("-record_date").prefetch_related("project", "test_order")
    drv_pending = await DriverAttendance.filter(approver2_result="待审批").order_by("-record_date").prefetch_related("project", "test_order")

    from datetime import time as dt_time

    def fmt_time(t):
        return t.strftime("%H:%M") if isinstance(t, dt_time) else (str(t) if t else "")

    eng_data = []
    for item in eng_pending:
        d = await item.to_dict()
        d["project_name"] = item.project.project_name if item.project else ""
        d["test_order_no"] = item.test_order.test_order_no if item.test_order else ""
        d["start_time"] = fmt_time(d.get("start_time"))
        d["end_time"] = fmt_time(d.get("end_time"))
        d["record_type"] = "工程师"
        d["record_model"] = "engineer"
        eng_data.append(d)

    drv_data = []
    for item in drv_pending:
        d = await item.to_dict()
        d["project_name"] = item.project.project_name if item.project else ""
        d["test_order_no"] = item.test_order.test_order_no if item.test_order else ""
        d["start_time"] = fmt_time(d.get("start_time"))
        d["end_time"] = fmt_time(d.get("end_time"))
        d["record_type"] = "驾驶员"
        d["record_model"] = "driver"
        drv_data.append(d)

    all_data = eng_data + drv_data
    all_data.sort(key=lambda x: x.get("record_date", ""), reverse=True)
    return Success(data=all_data)


@router.post("/pending-approval/approve", summary="审批通过")
async def approve_record(
    record_id: int = Query(..., description="记录ID"),
    record_model: str = Query(..., description="engineer 或 driver"),
):
    if record_model == "engineer":
        rec = await EngineerAttendance.get(id=record_id)
        rec.approver2_result = "通过"
        await rec.save()
    elif record_model == "driver":
        rec = await DriverAttendance.get(id=record_id)
        rec.approver2_result = "通过"
        await rec.save()
    else:
        return Fail(msg="无效的记录类型")
    # 审批通过后自动同步到每日费用
    await _auto_sync_daily()
    return Success(msg="已通过")


@router.post("/pending-approval/reject", summary="审批驳回")
async def reject_record(
    record_id: int = Query(..., description="记录ID"),
    record_model: str = Query(..., description="engineer 或 driver"),
):
    if record_model == "engineer":
        rec = await EngineerAttendance.get(id=record_id)
        rec.approver2_result = "驳回"
        await rec.save()
    elif record_model == "driver":
        rec = await DriverAttendance.get(id=record_id)
        rec.approver2_result = "驳回"
        await rec.save()
    else:
        return Fail(msg="无效的记录类型")
    # 驳回后也同步更新每日费用状态
    await _auto_sync_daily()
    return Success(msg="已驳回")


# ==================== 归档材料 ====================
@router.post("/attachment/upload", summary="上传归档材料")
async def upload_attachment(
    settlement_id: int = Query(...),
    attachment_type: str = Query(...),
    file: UploadFile = File(...),
):
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    upload_dir = os.path.join(base_dir, "static", "uploads", "attachments")
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f"{timestamp}_{file.filename}"
    filepath = os.path.join(upload_dir, filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    url = f"/uploads/attachments/{filename}"
    await SettlementAttachment.create(
        settlement_id=settlement_id,
        attachment_type=attachment_type,
        file_name=file.filename,
        file_url=url,
    )
    return Success(msg="上传成功", data={"url": url})


@router.post("/attachment/upload-file", summary="通用文件上传")
async def upload_file(
    file: UploadFile = File(...),
    type: str = Query("", description="文件类型标识"),
):
    """通用文件上传，返回文件访问 URL"""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    upload_dir = os.path.join(base_dir, "static", "uploads", "attachments")
    os.makedirs(upload_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    safe_name = file.filename.replace(" ", "_") if file.filename else "file"
    filename = f"{timestamp}_{safe_name}"
    filepath = os.path.join(upload_dir, filename)

    contents = await file.read()
    with open(filepath, "wb") as f:
        f.write(contents)

    url = f"/uploads/attachments/{filename}"
    return Success(msg="上传成功", data={"url": url})


@router.get("/attachment/list", summary="查看归档材料列表")
async def list_attachments(settlement_id: int = Query(...)):
    attachments = await SettlementAttachment.filter(settlement_id=settlement_id).order_by("-upload_time")
    data = [await a.to_dict() for a in attachments]
    return Success(data=data)


@router.delete("/attachment/delete", summary="删除归档材料")
async def delete_attachment(id: int = Query(...)):
    attachment = await SettlementAttachment.get(id=id)
    file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "static", attachment.file_url.lstrip("/"),
    )
    if os.path.exists(file_path):
        os.remove(file_path)
    await attachment.delete()
    return Success(msg="删除成功")


# ==================== 差异记录 ====================
@router.post("/diff-record/create", summary="创建差异记录")
async def create_diff_record(item_in: ExpenseDiffRecordCreate):
    await ExpenseDiffRecord.create(**item_in.model_dump())
    return Success(msg="已创建差异提醒")


@router.get("/diff-record/list", summary="查看差异记录")
async def list_diff_records(
    settlement_id: int = Query(None),
    status: str = Query(None),
    responsible_person: str = Query(None),
):
    q = Q()
    if settlement_id:
        q &= Q(settlement_id=settlement_id)
    if status:
        q &= Q(status=status)
    if responsible_person:
        q &= Q(responsible_person=responsible_person)
    diff_records = await ExpenseDiffRecord.filter(q).order_by("-id")
    data = [await d.to_dict() for d in diff_records]
    return Success(data=data)


@router.post("/diff-record/handle", summary="处理差异记录")
async def handle_diff_record(id: int = Query(...)):
    await ExpenseDiffRecord.filter(id=id).update(
        status="已处理", handle_time=datetime.now()
    )
    return Success(msg="处理完成")


# ==================== 试验需求与人员 ====================
@router.get("/requirement-personnel/list", summary="查看试验需求与人员列表")
async def list_requirement_personnel(
    test_order_no: str = Query(None, description="试验单号"),
    supplier: str = Query(None, description="供应商"),
    responsible_person: str = Query(None, description="负责人"),
    outsourced_personnel: str = Query(None, description="委外人员名称"),
    has_outsourced: str = Query(None, description="只显示委外人员非空(true/false)"),
):
    items = await requirement_personnel_controller.search(
        test_order_no=test_order_no, supplier=supplier,
        responsible_person=responsible_person,
        outsourced_personnel=outsourced_personnel,
        has_outsourced=has_outsourced,
    )
    data = [await item.to_dict() for item in items]
    return Success(data=data)


@router.post("/requirement-personnel/create", summary="创建试验需求与人员")
async def create_requirement_personnel(item_in: RequirementPersonnelCreate):
    await requirement_personnel_controller.create(obj_in=item_in)
    return Success(msg="创建成功")


@router.post("/requirement-personnel/update", summary="更新试验需求与人员")
async def update_requirement_personnel(id: int = Query(...), item_in: RequirementPersonnelUpdate = Body(...)):
    await requirement_personnel_controller.update(id=id, obj_in=item_in)
    return Success(msg="更新成功")


@router.delete("/requirement-personnel/delete", summary="删除试验需求与人员")
async def delete_requirement_personnel(id: int = Query(...)):
    await requirement_personnel_controller.remove(id=id)
    return Success(msg="删除成功")


# ==================== 看板统计 ====================
@router.get("/dashboard/stats", summary="看板统计")
async def dashboard_stats():
    # 项目数量
    project_count = await ExpenseProject.all().count()
    budget_count = await BudgetCode.all().count()
    expense_code_count = await ExpenseCode.all().count()
    test_order_count = await TestOrder.all().count()

    # 费用号使用率统计
    expense_codes = await ExpenseCode.all()
    total_budget = sum(float(e.total_amount) for e in expense_codes)
    total_used = sum(float(e.used_amount) for e in expense_codes)

    # 试验单号使用统计
    total_test_orders = test_order_count
    used_test_orders = await TestOrder.filter(is_used=True).count()

    # 月度汇总
    current_month = datetime.now().strftime("%Y-%m")
    now = datetime.now()
    month_start = date(now.year, now.month, 1)
    if now.month == 12:
        month_end = date(now.year + 1, 1, 1)
    else:
        month_end = date(now.year, now.month + 1, 1)
    month_records = await DailyRecord.filter(
        record_date__gte=month_start,
        record_date__lt=month_end,
    )
    month_work_hours = sum(float(r.work_hours) for r in month_records)
    month_advance = sum(float(r.advance_payment) for r in month_records)

    # 各项目费用统计
    projects = await ExpenseProject.all()
    project_stats = []
    for p in projects:
        budgets = await BudgetCode.filter(project_id=p.id)
        budget_total = sum(float(b.budget_amount) for b in budgets)
        budget_used = sum(float(b.used_amount) for b in budgets)
        # 工时统计
        daily_count = await DailyRecord.filter(project_id=p.id).count()
        project_stats.append({
            "project_id": p.id,
            "project_name": p.project_name,
            "series_name": p.series_name,
            "budget_total": budget_total,
            "budget_used": budget_used,
            "daily_record_count": daily_count,
        })

    return Success(data={
        "project_count": project_count,
        "budget_count": budget_count,
        "expense_code_count": expense_code_count,
        "test_order_count": test_order_count,
        "total_budget": total_budget,
        "total_used": total_used,
        "usage_rate": round(total_used / total_budget * 100, 1) if total_budget > 0 else 0,
        "total_test_orders": total_test_orders,
        "used_test_orders": used_test_orders,
        "test_order_usage_rate": round(used_test_orders / total_test_orders * 100, 1) if total_test_orders > 0 else 0,
        "month_work_hours": month_work_hours,
        "month_advance": month_advance,
        "project_stats": project_stats,
    })


@router.get("/dashboard/trend", summary="月度趋势数据")
async def dashboard_trend():
    """获取近12个月的费用趋势"""
    from collections import defaultdict
    current = datetime.now()
    monthly_data = defaultdict(lambda: {"labor": 0, "advance": 0, "total": 0})

    records = await DailyRecord.all().exclude(approval_status="驳回")
    for r in records:
        key = r.record_date.strftime("%Y-%m")
        monthly_data[key]["labor"] += float(r.work_hours) * 50
        monthly_data[key]["advance"] += float(r.advance_payment)
        monthly_data[key]["total"] += float(r.work_hours) * 50 + float(r.advance_payment)

    months = []
    for i in range(11, -1, -1):
        m = current.month - i
        y = current.year
        while m <= 0:
            m += 12
            y -= 1
        key = f"{y}-{m:02d}"
        months.append({
            "month": key,
            **monthly_data.get(key, {"labor": 0, "advance": 0, "total": 0}),
        })

    return Success(data=months)


# ==================== 月度结算单导出 ====================
# (已迁移至 app/api/v1/settlement/)

SUPPLIER_RATES = {
    "达安": {"local": 130, "trip": 130},
    "育喆": {"local": 36.25, "trip": 44.50},
    "万嘉禾": {"local": 35.13, "trip": 44.50},
}

REIMBURSE_ITEMS = [
    "停车费", "洗车费", "拖车救援费用", "加油费", "充电费",
    "过路过桥费", "维修保养费",
]


@router.get("/monthly-settlement/export", summary="导出月度结算单Excel")
async def export_monthly_settlement(
    year_month: str = Query(..., description="结算月份 YYYY-MM"),
    supplier: str = Query(..., description="供应商名称: 达安/育喆/万嘉禾"),
    test_order_no: str = Query(None, description="试验单号(可选)"),
):
    # 解析月份范围
    ym = year_month.split("-")
    y, m = int(ym[0]), int(ym[1])
    month_start = date(y, m, 1)
    if m == 12:
        month_end = date(y + 1, 1, 1)
    else:
        month_end = date(y, m + 1, 1)

    # 供应商 → 人员类型
    if supplier == "达安":
        person_type = "工程师"
    else:
        person_type = "驾驶员"

    # 查找供应商的试验单号
    torder_q = Q(supplier=supplier)
    if test_order_no:
        torder_q &= Q(test_order_no__contains=test_order_no)
    test_orders = await TestOrder.filter(torder_q).prefetch_related("expense_code__budget__project").all()

    # 收集所有记录
    all_records = []
    to_ids = [to.id for to in test_orders if to.id]
    if to_ids:
        records = await DailyRecord.filter(
            test_order_id__in=to_ids,
            record_date__gte=month_start,
            record_date__lt=month_end,
            person_type=person_type,
        ).prefetch_related("test_order").order_by("record_date", "person_name").all()
        all_records = list(records)

    # 按试验单号分组
    groups = defaultdict(list)
    for rec in all_records:
        groups[rec.test_order_id].append(rec)

    # 构建Excel
    wb = Workbook()
    # 把默认sheet留作结算单
    ws = wb.active
    ws.title = f"{y}年{m}月结算单"

    # 样式
    title_font = Font(name="Arial", size=14, bold=True)
    header_font = Font(name="Arial", size=10, bold=True)
    cell_font = Font(name="Arial", size=10)
    thin_border = Border(
        left=Side(style="thin"), right=Side(style="thin"),
        top=Side(style="thin"), bottom=Side(style="thin"),
    )

    row = 1
    # 标题
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=11)
    cell = ws.cell(row=row, column=1, value=f"费用结算单-{supplier} {supplier}  {person_type}")
    cell.font = title_font
    cell.alignment = Alignment(horizontal="center")
    row += 2

    # 表头
    headers = ["序号", "", "费用项目", "费用标准", "", "项目数量", "", "", "", "小计（元）", "备注"]
    for ci, h in enumerate(headers, 1):
        c = ws.cell(row=row, column=ci, value=h)
        c.font = header_font
        c.alignment = Alignment(horizontal="center")
        c.border = thin_border
    row += 1

    rates = SUPPLIER_RATES.get(supplier, SUPPLIER_RATES["万嘉禾"])

    # 含税费用行
    total_shifts = 0
    for tid, recs in groups.items():
        # 统计班次：一个人一天=1个班次
        shifts = len(set((r.person_name, str(r.record_date)) for r in recs))
        total_shifts += shifts

    # 按定额标准计算工作地点（简单处理：统计出差/未出差的工时）
    local_hours = Decimal("0")
    trip_hours = Decimal("0")
    for rec in all_records:
        if rec.remark and "出差" in str(rec.remark):
            trip_hours += Decimal(str(rec.work_hours))
        else:
            local_hours += Decimal(str(rec.work_hours))

    local_total = float(local_hours) * rates["local"]
    trip_total = float(trip_hours) * rates["trip"]
    labor_total = local_total + trip_total

    ws.cell(row=row, column=1, value="含税费用").font = cell_font
    ws.cell(row=row, column=2, value=1).font = cell_font
    ws.cell(row=row, column=3, value=f"武汉{person_type}").font = cell_font
    ws.cell(row=row, column=4, value=rates["local"]).font = cell_font
    ws.cell(row=row, column=5, value="元/时").font = cell_font
    ws.cell(row=row, column=6, value=float(local_hours)).font = cell_font
    ws.cell(row=row, column=10, value=round(local_total, 2)).font = cell_font
    ws.cell(row=row, column=11, value="见附件考勤表").font = cell_font
    for ci in range(1, 12):
        ws.cell(row=row, column=ci).border = thin_border
    row += 1

    if trip_hours > 0:
        ws.cell(row=row, column=1, value="含税费用").font = cell_font
        ws.cell(row=row, column=2, value=2).font = cell_font
        ws.cell(row=row, column=3, value=f"出差{person_type}").font = cell_font
        ws.cell(row=row, column=4, value=rates["trip"]).font = cell_font
        ws.cell(row=row, column=5, value="元/时").font = cell_font
        ws.cell(row=row, column=6, value=float(trip_hours)).font = cell_font
        ws.cell(row=row, column=10, value=round(trip_total, 2)).font = cell_font
        ws.cell(row=row, column=11, value="见附件考勤表").font = cell_font
        for ci in range(1, 12):
            ws.cell(row=row, column=ci).border = thin_border
        row += 1

    # 代垫付和开票项目
    section_start = row
    ws.cell(row=row, column=1, value="代垫付和开票项目").font = cell_font
    for ci in range(1, 12):
        ws.cell(row=row, column=ci).border = thin_border

    advance_items = []
    for rec in all_records:
        if rec.advance_payment and float(rec.advance_payment) > 0:
            advance_items.append(rec)

    total_advance = sum(float(r.advance_payment or 0) for r in all_records)
    ws.cell(row=row, column=2, value=1).font = cell_font
    ws.cell(row=row, column=3, value="垫付费用合计").font = cell_font
    ws.cell(row=row, column=4, value="据实结算").font = cell_font
    ws.cell(row=row, column=10, value=round(total_advance, 2)).font = cell_font
    ws.cell(row=row, column=11, value="见附件明细").font = cell_font
    for ci in range(1, 12):
        ws.cell(row=row, column=ci).border = thin_border
    row += 1

    # 开票税费
    tax_rate = 0.06
    tax_amount = labor_total * tax_rate
    ws.cell(row=row, column=2, value=row - section_start + 1).font = cell_font
    ws.cell(row=row, column=3, value="开票税费").font = cell_font
    ws.cell(row=row, column=4, value=tax_rate).font = cell_font
    ws.cell(row=row, column=6, value=0).font = cell_font
    ws.cell(row=row, column=8, value="元").font = cell_font
    ws.cell(row=row, column=10, value=round(tax_amount, 2)).font = cell_font
    for ci in range(1, 12):
        ws.cell(row=row, column=ci).border = thin_border
    row += 1

    # 合计
    grand_total = labor_total + total_advance + tax_amount
    ws.cell(row=row, column=1, value=f"合计（元）").font = Font(name="Arial", size=11, bold=True)
    ws.cell(row=row, column=10, value=round(grand_total, 2)).font = Font(name="Arial", size=11, bold=True)
    for ci in range(1, 12):
        ws.cell(row=row, column=ci).border = thin_border
    row += 2

    ws.cell(row=row, column=1, value="说明：各单项费用结算金额四舍五入保留两位小数。").font = cell_font
    row += 1

    ws.cell(row=row, column=1, value="岚图汽车科技有限公司").font = cell_font
    ws.cell(row=row, column=9, value=f"{supplier}").font = cell_font
    row += 1
    ws.cell(row=row, column=1, value="经办人（签字）：").font = cell_font
    ws.cell(row=row, column=9, value="经办人（签字）：").font = cell_font
    row += 1
    ws.cell(row=row, column=1, value=f"年   月   日").font = cell_font
    ws.cell(row=row, column=9, value=f"年   月   日").font = cell_font

    # === Sheet 2: 月考勤 ===
    ws2 = wb.create_sheet(f"{y}年{m}月考勤")
    ws2.cell(row=1, column=1, value=f"支持服务工时记录表").font = title_font
    ws2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=3)
    ws2.cell(row=2, column=1, value=f"需求专业：智驾域测试").font = cell_font

    # 考勤表头
    att_row = 4
    ws2.cell(row=att_row, column=1, value="序号").font = header_font
    ws2.cell(row=att_row, column=2, value="姓名").font = header_font
    ws2.cell(row=att_row, column=3, value="专业/岗位").font = header_font
    ws2.cell(row=att_row, column=4, value="项目/试验单号").font = header_font

    # 日期列：该月所有天
    days_in_month = (month_end - month_start).days
    for d in range(1, days_in_month + 1):
        col = d + 4
        ws2.cell(row=att_row, column=col, value=d).font = header_font
        ws2.cell(row=att_row, column=col).alignment = Alignment(horizontal="center")

    total_col = days_in_month + 5
    ws2.cell(row=att_row, column=total_col, value="合计(h)").font = header_font
    ws2.cell(row=att_row, column=total_col + 1, value="备注").font = header_font

    # 填充考勤数据
    att_row += 1
    all_persons = sorted(set(r.person_name for r in all_records))
    for pi, pname in enumerate(all_persons):
        person_recs = [r for r in all_records if r.person_name == pname]
        ws2.cell(row=att_row, column=1, value=pi + 1).font = cell_font
        ws2.cell(row=att_row, column=2, value=pname).font = cell_font
        ws2.cell(row=att_row, column=3, value=person_type).font = cell_font

        # 获取该人员关联的试验单号
        tns = set()
        for rec in person_recs:
            to_obj = await TestOrder.filter(id=rec.test_order_id).first()
            if to_obj:
                tns.add(to_obj.test_order_no)
        ws2.cell(row=att_row, column=4, value="\n".join(tns) if tns else "").font = cell_font

        daily = {}
        for rec in person_recs:
            d = rec.record_date.day
            daily[d] = float(rec.work_hours or 0)

        total_h = 0
        for d in range(1, days_in_month + 1):
            h = daily.get(d, 0)
            if h > 0:
                ws2.cell(row=att_row, column=d + 4, value=h).font = cell_font
            total_h += h

        ws2.cell(row=att_row, column=total_col, value=total_h).font = Font(name="Arial", size=10, bold=True)
        att_row += 1

    # 列宽
    ws.column_dimensions["A"].width = 15
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["J"].width = 14
    for ci in range(1, total_col + 2):
        if ci <= 5:
            ws2.column_dimensions[get_column_letter(ci)].width = 12 if ci > 3 else 8
        else:
            ws2.column_dimensions[get_column_letter(ci)].width = 5

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    filename = f"月度结算单-{supplier}-{year_month}.xlsx"
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


# ==================== 预算预警 ====================
@router.get("/alert/list", summary="预算预警列表")
async def budget_alert_list():
    """查询试验需求和费用号的使用率预警（与试验单号看板口径一致：实时=settlement_amount+当月）"""
    now = datetime.now()
    month_start = date(now.year, now.month, 1)
    month_end = date(now.year + 1, 1, 1) if now.month == 12 else date(now.year, now.month + 1, 1)
    test_orders = await TestOrder.filter(is_used=False).prefetch_related("expense_code__budget__project")
    expense_codes = await ExpenseCode.filter(is_used=False).prefetch_related("budget__project")

    # 试验需求预警
    to_alerts = []
    for to in test_orders:
        total = float(to.total_price or 0)
        # 实时已使用 = settlement_amount(非null) + 当月每日费用, 否则所有每日费用
        if to.settlement_amount is not None:
            current_month = await DailyRecord.filter(
                Q(test_order_id=to.id) & Q(record_date__gte=str(month_start)) & Q(record_date__lt=str(month_end))
                & ~Q(approval_status="驳回")
            )
            used = float(to.settlement_amount) + sum(float(r.total_amount or 0) for r in current_month)
        else:
            all_dr = await DailyRecord.filter(
                Q(test_order_id=to.id) & ~Q(approval_status="驳回")
            )
            used = sum(float(r.total_amount or 0) for r in all_dr)
        rate = round(used / total * 100, 1) if total > 0 else 0
        if rate >= 70:
            level = "严重" if rate >= 95 else "警告"
            project_name = ""
            exp_code = ""
            if to.expense_code:
                exp_code = to.expense_code.expense_code or ""
                if to.expense_code.budget and to.expense_code.budget.project:
                    project_name = to.expense_code.budget.project.project_name or ""
            to_alerts.append({
                "type": "试验需求",
                "code": to.test_order_no or "",
                "name": project_name,
                "responsible": to.responsible_person or "",
                "total": total,
                "used": round(used, 2),
                "rate": rate,
                "level": level,
                "expense_code": exp_code,
            })

    # 费用号预警（使用率 = 该费用号下所有试验单实时已使用合计 / 费用号总金额）
    # 先按 expense_code_id 分组试验单的实时 used
    ec_to_used = {}
    for to in test_orders:
        ec_id = to.expense_code_id
        if not ec_id:
            continue
        total = float(to.total_price or 0)
        if to.settlement_amount is not None:
            cm = await DailyRecord.filter(
                Q(test_order_id=to.id) & Q(record_date__gte=str(month_start)) & Q(record_date__lt=str(month_end))
                & ~Q(approval_status="驳回")
            )
            used = float(to.settlement_amount) + sum(float(r.total_amount or 0) for r in cm)
        else:
            all_dr = await DailyRecord.filter(
                Q(test_order_id=to.id) & ~Q(approval_status="驳回")
            )
            used = sum(float(r.total_amount or 0) for r in all_dr)
        ec_to_used[ec_id] = ec_to_used.get(ec_id, 0) + used

    ec_alerts = []
    for ec in expense_codes:
        total = float(ec.total_amount or 0)
        used = ec_to_used.get(ec.id, 0)
        rate = round(used / total * 100, 1) if total > 0 else 0
        if rate >= 50:
            level = "严重" if rate >= 70 else "警告"
            project_name = ""
            if ec.budget and ec.budget.project:
                project_name = ec.budget.project.project_name or ""
            ec_alerts.append({
                "type": "费用号",
                "code": ec.expense_code or "",
                "name": project_name,
                "responsible": ec.responsible_person or "",
                "total": total,
                "used": round(used, 2),
                "rate": rate,
                "level": level,
                "expense_code": "",
            })

    # 按使用率降序排序
    to_alerts.sort(key=lambda x: x["rate"], reverse=True)
    ec_alerts.sort(key=lambda x: x["rate"], reverse=True)

    return Success(data={
        "test_order_alerts": to_alerts,
        "expense_code_alerts": ec_alerts,
    })
