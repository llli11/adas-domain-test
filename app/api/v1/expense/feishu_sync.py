"""飞书多维表格同步服务"""
import asyncio
import json
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

import time
import httpx
from tortoise.expressions import Q

from app.controllers.vehicle import vehicle_controller
from app.log import logger
from app.schemas.vehicles import VehicleCreate


# 飞书 tenant_access_token 进程内缓存（飞书 token 有效期约 2 小时，避免每次请求都重新获取）
_TOKEN_CACHE: Dict[str, Dict[str, Any]] = {}


# 默认飞书配置（数据源1：预定车辆信息表）
DEFAULT_FEISHU_CONFIG = {
    "APP_ID": "cli_a90024aeadb81bcc",
    "APP_SECRET": "niCTFud9R2cpOxc9mApN0oJdBCXXHbzz",
    "BASE_ID": "COj6bs7p9ap6znsJ23Fcr2rnnlf",
    "TABLE_IDS": {
        "VEHICLES": "tblLWwxtCzoFkcqh",
        "DAILY_TASKS": "tblnotoTknWAKkcu",
    },
}

# 费用管理飞书配置（数据源：考勤日志收集表 + 人员关系表）
EXPENSE_FEISHU_CONFIG = {
    "APP_ID": "cli_a90024aeadb81bcc",
    "APP_SECRET": "niCTFud9R2cpOxc9mApN0oJdBCXXHbzz",
    "BASE_ID": "SpnObQT0ka1sdosw84Qcurfan3d",
    "TABLE_IDS": {
        "ENGINEER": "tbl1aVib9ds3DcIp",       # 工程师日志表
        "DRIVER": "tbllTJvADTSaJeNw",         # 驾驶员日志表
        "PERSONNEL": "tblTBn7ayRUm2LyM",      # 试验单号与人员关系表
        "EXPENSE_CODE": "tblPlTpUn9noDXs6",   # 费用号看板表
    },
}

# 飞书字段 → Vehicle模型字段映射（预设20个字段）
FEISHU_FIELD_MAP = {
    "车辆VN": "vn",
    "车辆编号": "vehicle_code",
    "车型项目": "vehicle_model",
    "动力类型": "power_type",
    "颜色": "color",
    "是否有管制物品": "has_controlled_items",
    "借用人": "borrower",
    "借用到期时间": "borrow_expire_date",
    "临牌到期时间": "temp_plate_expire_date",
    "保险区域": "insurance_area",
    "试验日期": "test_date",
    "任务状态": "task_status",
    "试验任务": "test_task",
    "测试人员": "tester",
    "驾驶人员": "driver",
    "出差状态": "travel_status",
    "试验城市": "test_city",
    "出门单": "exit_permit",
    "停车位": "parking_spot",
    "位置信息": "location_info",
    "纬度": "latitude",
    "经度": "longitude",
}

# 飞书字段 → 工程师考勤模型字段映射
# 注意：工程师表没有直接的"试验需求编号"字段，使用公式字段"根据填写人选择，生成试验单号"
FEISHU_ENG_ATTENDANCE_FIELD_MAP = {
    "日期": "record_date",
    "填写人": "person_name",
    "填写人-人名": "person_name",
    # 工程师表的"查询填写人项目需求编号"和"根据填写人选择，生成试验单号"都是关联字段，返回token
    "查询填写人项目需求编号": "requirement_code_token",
    "根据填写人选择，生成试验单号": "requirement_code_token",
    "试验版本": "test_version",
    "试验任务": "test_task",
    "车辆编号": "car_number",
    "上班时间": "start_time",
    "下班时间": "end_time",
    "是否加班": "is_overtime",
    "当天是否加班": "is_overtime",
    "加班时长": "overtime_hours",
    "当天加班时长(h)": "overtime_hours",
    "工作日时长": "work_duration",
    "当天工作日时长(h)": "work_duration",
    "总工时": "total_hours",
    "当天总工时(h)": "total_hours",
    "出差状态": "travel_status",
    "工作地点": "work_location",
    "当天工作量": "workload",
    "当天工作量(次/km)": "workload",
    "发现问题数": "problems_found",
    "行车泊车发现问题数": "problems_found",
    "检查用例数": "check_cases",
    "点检用例数": "check_cases",
    "刷写软件数": "software_flash_count",
    "整备车辆刷写软件数量": "software_flash_count",
    "问题明细": "issue_detail",
    "定位位置": "location_coords",
    "审批人1审批结果": "approver1_result",
    "审批人2审核结果": "approver2_result",
    # 车型项目（飞书表单中选择的项目，直接映射到 expense_project）
    "填写人选择填写车型项目": "_project_name",
    "查询填写人所在车型项目": "_project_name",
    "所属项目": "_project_name",
    "所属项目信息-详细": "_project_name",
}

# 飞书字段 → 驾驶员考勤模型字段映射
FEISHU_DRV_ATTENDANCE_FIELD_MAP = {
    "日期": "record_date",
    "填写人": "person_name",
    "填写人-人名": "person_name",
    # 驾驶员表的"试验需求编号"和"根据填写人选择，生成试验单号"都是关联字段，返回token
    "试验需求编号": "requirement_code_token",
    "根据填写人选择，生成试验单号": "requirement_code_token",
    "查询填写人项目需求编号": "requirement_code_text",
    "试验版本": "test_version",
    "试验任务": "test_task",
    "车辆编号": "car_number",
    "上班时间": "start_time",
    "下班时间": "end_time",
    "是否加班": "is_overtime",
    "当天是否加班": "is_overtime",
    "加班时长": "overtime_hours",
    "当天加班时长(h)": "overtime_hours",
    "工作日时长": "work_duration",
    "当天工作日时长(h)": "work_duration",
    "总工时": "total_hours",
    "当天总工时(h)": "total_hours",
    "出差状态": "travel_status",
    "工作地点": "work_location",
    "初始里程": "vehicle_initial_mileage",
    "车辆初始里程": "vehicle_initial_mileage",
    "结束里程": "vehicle_end_mileage",
    "车辆结束里程": "vehicle_end_mileage",
    "测试里程": "vehicle_test_mileage",
    "车辆测试里程（km）": "vehicle_test_mileage",
    "垫付费用": "daily_advance_total",
    "当日垫付费用总计：": "daily_advance_total",
    "定位位置": "location_coords",
    "审批人1审批结果": "approver1_result",
    "审批人2审核结果": "approver2_result",
    # 车型项目（飞书表单中选择的项目，直接映射到 expense_project）
    "填写人选择填写车型项目": "_project_name",
    "查询填写人所在车型项目": "_project_name",
    "所属项目": "_project_name",
    "所属项目-详细": "_project_name",
}

# 费用号表字段映射（来自飞书多维表格，用于同步费用号看板数据）
FEISHU_EXPENSE_CODE_FIELD_MAP = {
    "费用号": "expense_code",
    "费用号总金额": "total_amount",
    "责任人": "responsible_person",
    # 以下字段用于层级查找（项目→预算号→费用号），不直接映射到 ExpenseCode 模型字段
    # "系列名称" → ExpenseProject.series_name
    # "类别" → ExpenseProject.category
    # "项目名称" → ExpenseProject.project_name
    # "所属预算号" → BudgetCode.budget_code
    # "试验任务单号" → TestOrder.test_order_no
}


class FeishuSyncService:
    """飞书多维表格同步服务"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or DEFAULT_FEISHU_CONFIG
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """惰性获取HTTP客户端，用完不关闭"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=600.0)
        return self._client

    async def get_tenant_access_token(self, config: Optional[Dict[str, Any]] = None) -> str:
        """获取飞书 tenant_access_token（带进程内缓存，避免每次请求都重新获取）"""
        cfg = config or self.config
        _app_id = cfg["APP_ID"]
        _now = time.time()
        _cached = _TOKEN_CACHE.get(_app_id)
        if _cached and _cached["exp"] > _now + 60:
            return _cached["token"]
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": cfg["APP_ID"],
            "app_secret": cfg["APP_SECRET"],
        }
        logger.info(f"[Feishu] 正在获取 token, APP_ID={cfg['APP_ID'][:10]}...")
        try:
            response = await self.http_client.post(url, json=payload)
            data = response.json()
            logger.info(f"[Feishu] Token响应: code={data.get('code')}, msg={data.get('msg')}")
            if data.get("code") == 0:
                token = data["tenant_access_token"]
                _expire = data.get("expire", 7200)
                _TOKEN_CACHE[_app_id] = {"token": token, "exp": _now + _expire}
                logger.info("[Feishu] Tenant access token 获取成功(已缓存)")
                return token
            else:
                err_msg = data.get('msg', 'unknown')
                logger.error(f"[Feishu] 获取token失败: code={data.get('code')}, msg={err_msg}")
                if data.get('code') == 99991663:
                    raise Exception("飞书应用权限不足，请确认应用已开通多维表格(bitable)权限")
                raise Exception(f"获取飞书token失败: {err_msg} (code={data.get('code')})")
        except httpx.HTTPError as e:
            logger.error(f"[Feishu] Token请求网络异常: {e}")
            raise Exception(f"飞书API网络异常: {str(e)}")
        except Exception as e:
            if "获取飞书token失败" in str(e):
                raise
            logger.error(f"[Feishu] 获取token异常: {e}")
            raise

    async def get_bitable_records(
        self, token: str, table_id: str, page_token: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None, filter_formula: Optional[str] = None,
        field_names: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """获取飞书多维表格所有记录（由 Python 端进行日期过滤），遇瞬态错误自动重试

        field_names: 仅返回指定字段，可显著减小响应体积、降低单次请求耗时。
        """
        cfg = config or self.config
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{cfg['BASE_ID']}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token
        if filter_formula:
            params["filter"] = filter_formula
        if field_names:
            params["field_names"] = field_names

        max_retries = 6          # 最多重试 6 次（每次 1 秒，共 6 秒，瞬态错误通常更快恢复）
        retry_delay = 1.0        # 每次重试间隔 1 秒
        for attempt in range(max_retries):
            logger.info(f"[Feishu] 读取表格: URL={url}")
            try:
                response = await self.http_client.get(url, headers=headers, params=params)
                data = response.json()
                code = data.get("code", -1)
                msg = data.get("msg", "")
                logger.info(f"[Feishu] 表格响应: code={code}, msg={msg}")

                if code == 0:
                    return data.get("data") or {}
                elif code == 1254105:
                    raise Exception(f"多维表格不存在或无权限访问 (code=1254105)，请检查BASE_ID和TABLE_ID是否正确，并确认应用已添加到多维表格的文档应用中")
                elif code == 1254607:
                    # 飞书临时错误：数据未就绪，自动重试（最多 6 次 × 1 秒 = 6 秒）
                    if attempt < max_retries - 1:
                        logger.warning(f"[Feishu] 数据未就绪 (code=1254607)，第 {attempt + 1}/{max_retries} 次重试，{retry_delay}秒后...")
                        await asyncio.sleep(retry_delay)
                        continue
                    raise Exception(f"获取飞书记录失败: 数据未就绪，重试 {max_retries} 次后仍失败 (code=1254607)")
                else:
                    logger.error(f"[Feishu] 获取记录失败: {data}")
                    raise Exception(f"获取飞书记录失败: {msg} (code={code})")
            except httpx.HTTPError as e:
                logger.error(f"[Feishu] 记录请求网络异常: {e}")
                raise Exception(f"飞书API网络异常: {str(e)}")
            except Exception as e:
                if "获取飞书记录失败" in str(e) or "多维表格不存在" in str(e) or "飞书API网络异常" in str(e):
                    raise
                logger.error(f"[Feishu] 获取记录异常: {e}")
                raise

    async def get_table_fields(self, token: str, table_id: str, config: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """获取飞书多维表格的字段列表，用于验证字段名匹配"""
        cfg = config or self.config
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{cfg['BASE_ID']}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        logger.info(f"[Feishu] 获取表格字段列表: TABLE_ID={table_id}")
        try:
            response = await self.http_client.get(url, headers=headers)
            data = response.json()
            code = data.get("code", -1)
            if code == 0:
                items = data.get("data", {}).get("items", [])
                logger.info(f"[Feishu] 表格共有 {len(items)} 个字段:")
                for item in items:
                    field_name = item.get("field_name", "")
                    field_type = item.get("type", "")
                    logger.info(f"  - 字段名: '{field_name}', 类型: {field_type}, "
                               f"代码映射: '{FEISHU_FIELD_MAP.get(field_name, '❌ 未映射')}'")
                # 检查未映射的字段
                unmapped = [item.get("field_name") for item in items
                           if item.get("field_name") not in FEISHU_FIELD_MAP]
                if unmapped:
                    logger.warning(f"[Feishu] ⚠️ 以下 {len(unmapped)} 个字段未在FEISHU_FIELD_MAP中映射: {unmapped}")
                return items
            else:
                logger.warning(f"[Feishu] 获取字段列表失败: code={code}, msg={data.get('msg')}")
                return []
        except Exception as e:
            logger.warning(f"[Feishu] 获取字段列表异常: {e}")
            return []

    def _map_feishu_record_to_vehicle(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """将飞书多维表格记录字段映射为Vehicle模型字典"""
        fields = record.get("fields", {})
        record_id = record.get("record_id", "unknown")
        vehicle_data: Dict[str, Any] = {"data_source": "feishu"}

        # 详细日志：记录飞书表格中的原始字段名和值（取前5条采样避免日志爆炸）
        logger.debug(f"[Feishu] 记录 {record_id} 原始字段: {json.dumps(fields, ensure_ascii=False, default=str)[:500]}")

        mapped_count = 0
        for feishu_field, vehicle_field in FEISHU_FIELD_MAP.items():
            value = fields.get(feishu_field)
            if value is not None:
                # 处理飞书多维表格特殊类型
                if isinstance(value, list) and len(value) > 0:
                    # 可能是附件/多选等
                    if isinstance(value[0], dict):
                        value = value[0].get("text", str(value[0]))
                    else:
                        value = str(value[0])
                elif isinstance(value, (int, float)):
                    # 日期字段：飞书返回毫秒时间戳，需转为 date 对象
                    if vehicle_field in ('borrow_expire_date', 'temp_plate_expire_date', 'test_date'):
                        if value > 10000000000:  # 毫秒时间戳
                            value = date.fromtimestamp(value / 1000)
                        elif value > 0:  # 秒级时间戳
                            value = date.fromtimestamp(value)
                        else:
                            value = None
                    else:
                        value = value
                vehicle_data[vehicle_field] = value
                mapped_count += 1

        logger.debug(f"[Feishu] 记录 {record_id} 成功映射 {mapped_count}/{len(FEISHU_FIELD_MAP)} 个字段, "
                     f"VN={vehicle_data.get('vn')}, "
                     f"任务状态={vehicle_data.get('task_status')}, "
                     f"试验任务={vehicle_data.get('test_task')}")

        # 确保必填字段有默认值
        vehicle_data.setdefault("vn", "")
        vehicle_data.setdefault("vehicle_code", vehicle_data.get("vn", ""))
        vehicle_data.setdefault("vehicle_model", "")
        vehicle_data.setdefault("power_type", "")
        vehicle_data.setdefault("color", "")

        return vehicle_data

    async def sync_vehicles_from_feishu(self, table_id: Optional[str] = None) -> Dict[str, Any]:
        """同步飞书多维表格数据到本地数据库
        先同步车辆信息表（基础字段），再同步每日任务表（任务状态字段），通过VN匹配合并
        Args:
            table_id: 可选的自定义表格ID（数据源2用），不传则使用默认VEHICLES表
        """
        try:
            token = await self.get_tenant_access_token()
        except Exception as e:
            logger.error(f"[Feishu] 同步失败 - 获取token失败: {e}")
            return {"success": False, "message": f"获取飞书token失败: {str(e)}", "created": 0, "updated": 0}

        created_count = 0
        updated_count = 0
        total_records = 0

        # ===== 第一步：同步车辆信息表（基础字段）=====
        vehicle_table_id = table_id or self.config["TABLE_IDS"]["VEHICLES"]
        try:
            records = await self._fetch_all_records(token, vehicle_table_id)
            total_records += len(records)
            logger.info(f"[Feishu] 车辆信息表: {len(records)} 条记录")

            for record in records:
                vehicle_data = self._map_feishu_record_to_vehicle(record)
                if not vehicle_data.get("vn") or not vehicle_data["vn"].strip():
                    continue
                try:
                    existing = await vehicle_controller.get_by_vn(vehicle_data["vn"])
                    if existing: updated_count += 1
                    else: created_count += 1
                    await vehicle_controller.upsert_by_vn(VehicleCreate(**vehicle_data))
                except Exception as e:
                    logger.error(f"[Feishu] 车辆信息同步失败 VN={vehicle_data.get('vn')}: {e}")
        except Exception as e:
            logger.error(f"[Feishu] 车辆信息表同步异常: {e}")

        # ===== 第二步：同步每日任务表（任务状态字段），通过VN匹配更新 =====
        if not table_id:
            daily_table_id = self.config["TABLE_IDS"]["DAILY_TASKS"]
            try:
                task_records = await self._fetch_all_records(token, daily_table_id)
                total_records += len(task_records)
                logger.info(f"[Feishu] 每日任务表: {len(task_records)} 条记录")
                task_updated = 0
                for record in task_records:
                    task_data = self._map_feishu_record_to_vehicle(record)
                    vn = task_data.get("vn", "").strip()
                    if not vn:
                        continue
                    # 只提取任务相关字段，通过VN匹配已有车辆记录更新
                    task_fields = {
                        k: v for k, v in task_data.items()
                        if k in ("task_status", "test_task", "tester", "driver",
                                 "travel_status", "test_city", "location_info",
                                 "latitude", "longitude") and v is not None
                    }
                    if task_fields:
                        existing = await vehicle_controller.get_by_vn(vn)
                        if existing:
                            existing.update_from_dict(task_fields)
                            await existing.save()
                            task_updated += 1
                logger.info(f"[Feishu] 每日任务表: 合并更新 {task_updated} 条车辆任务状态")
            except Exception as e:
                logger.warning(f"[Feishu] 每日任务表同步异常（车辆信息已同步）: {e}")

        message = f"同步完成: 共读取 {total_records} 条，新增 {created_count}，更新 {updated_count}"
        logger.info(f"[Feishu] {message}")
        return {
            "success": True, "message": message,
            "total_records": total_records,
            "created": created_count, "updated": updated_count,
        }

    async def sync_expense_from_feishu(
        self, table_id: str, record_type: str,
        date_start: Optional[str] = None, date_end: Optional[str] = None,
        token_to_test_order: Optional[Dict[str, str]] = None,
        person_to_test_order: Optional[Dict[str, Any]] = None,
        project_to_test_order: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """从飞书多维表格同步考勤数据到本地数据库
        Args:
            table_id: 飞书多维表格的 TABLE_ID
            record_type: "engineer" 或 "driver"
            date_start: 可选，筛选起始日期 (YYYY-MM-DD)
            date_end: 可选，筛选结束日期 (YYYY-MM-DD)
            token_to_test_order: 可选，预加载的 PERSONNEL_record_id→试验单号映射表
            person_to_test_order: 可选，预加载的 person_name→[{"test_order_no","start_date","end_date"}] 映射表
        """
        from app.models.expense import EngineerAttendance, DriverAttendance, ExpenseProject

        # 使用独立配置，不修改 self.config 以避免并行竞态
        cfg = EXPENSE_FEISHU_CONFIG
        try:
            token = await self.get_tenant_access_token(config=cfg)
        except Exception as e:
            logger.error(f"[Feishu] 同步失败 - 获取token失败: {e}")
            return {"success": False, "message": f"获取飞书token失败: {str(e)}", "created": 0, "updated": 0}

        field_map = FEISHU_ENG_ATTENDANCE_FIELD_MAP if record_type == "engineer" else FEISHU_DRV_ATTENDANCE_FIELD_MAP
        AttendanceModel = EngineerAttendance if record_type == "engineer" else DriverAttendance

        try:
            # 使用 TODATE() 函数在飞书 API 层做日期过滤（仅拉取近期数据，大幅减少分页次数）
            records = await self._fetch_all_records(
                token, table_id, config=cfg,
                date_field="日期",
                date_start=date_start, date_end=date_end,
            )
        except Exception as e:
            logger.error(f"[Feishu] 获取表格记录失败: {e}")
            return {"success": False, "message": f"获取表格记录失败: {str(e)}", "created": 0, "updated": 0}

        # ═══════════════════════════════════════════════════════════
        # ★ 预加载阶段：将所有需要 DB 查询的数据一次性加载到内存
        # ═══════════════════════════════════════════════════════════

        # ★ 预加载1：所有已有项目，用于直接从飞书项目名称查找
        all_projects = await ExpenseProject.all().values("id", "project_name")
        proj_cache = list(all_projects)  # 内存缓存，新增项目也追加到此列表
        created_proj = 0  # 新增项目计数

        # ★ 预加载2：未匹配项目（兜底用）
        unmatched_project = await ExpenseProject.filter(project_name="未匹配").first()
        if not unmatched_project:
            unmatched_project = await ExpenseProject.create(
                series_name="未匹配", project_name="未匹配", category="未匹配",
            )
        unmatched_project_id = unmatched_project.id

        # 预加载3：所有已有考勤记录，按 (record_date, person_name) 索引
        existing_records = await AttendanceModel.all().values("id", "record_date", "person_name")
        existing_map = {}
        for r in existing_records:
            rd = str(r["record_date"])
            pn = r["person_name"]
            existing_map[(rd, pn)] = r["id"]
        logger.info(f"[Feishu] 预加载已有考勤记录: {len(existing_map)} 条")

        # ★ 预加载4：token → 试验单号映射
        # 优先使用传入的预加载映射（避免重复拉取PERSONNEL表），否则自行加载
        if token_to_test_order is not None:
            _token_to_test_order = token_to_test_order
            logger.info(f"[Feishu] 使用传入的 token→试验单号映射: {len(_token_to_test_order)} 条")
        else:
            _token_to_test_order = {}
            try:
                personnel_table_id = EXPENSE_FEISHU_CONFIG["TABLE_IDS"]["PERSONNEL"]
                personnel_records = await self._fetch_all_records(token, personnel_table_id, config=cfg)
                for pr in personnel_records:
                    pr_fields = pr.get("fields", {})
                    pr_id = pr.get("record_id", "")
                    tno = ""
                    tno_val = pr_fields.get("试验需求编号") or pr_fields.get("试验单号")
                    if isinstance(tno_val, list) and len(tno_val) > 0:
                        if isinstance(tno_val[0], dict):
                            tno = str(tno_val[0].get("text", ""))
                        else:
                            tno = str(tno_val[0])
                    elif isinstance(tno_val, str):
                        tno = tno_val
                    if tno and pr_id:
                        _token_to_test_order[pr_id] = tno
                logger.info(f"[Feishu] 自行加载 token→试验单号映射: {len(_token_to_test_order)} 条")
            except Exception as e:
                logger.warning(f"[Feishu] 预加载PERSONNEL映射失败: {e}，将跳过token解析")

        # ═══════════════════════════════════════════════════════════
        # ★ 处理阶段：纯内存操作，不再有 DB 查询
        # ═══════════════════════════════════════════════════════════

        to_create = []
        to_update = []  # list of (id, defaults)
        skipped_count = 0
        _debug_logged = 0  # 调试计数器（审批字段）
        _proj_debug_logged = 0  # 调试计数器（项目映射）
        _token_debug_logged = 0  # 调试计数器（token解析）

        for record in records:
            fields = record.get("fields", {})
            record_id = record.get("record_id", "unknown")

            # 映射字段
            mapped = {}
            for feishu_field, model_field in field_map.items():
                value = fields.get(feishu_field)
                if value is not None:
                    if isinstance(value, list) and len(value) > 0:
                        if isinstance(value[0], dict):
                            # 飞书用户字段：{"name":"张三","avatar_url":"..."}
                            if "name" in value[0]:
                                value = str(value[0]["name"])
                            elif "text" in value[0]:
                                value = str(value[0]["text"])
                            elif "link" in value[0]:
                                # 飞书关联字段：{"link":{"token":"...","app_token":"..."},"text":"H56E-202606073"}
                                value = str(value[0].get("text", ""))
                            else:
                                value = str(value[0])
                        else:
                            value = str(value[0])
                    elif isinstance(value, dict):
                        if "name" in value:
                            value = str(value["name"])
                        elif "text" in value:
                            value = str(value["text"])
                        elif "link" in value:
                            value = str(value.get("text", ""))
                        else:
                            value = str(value)
                    mapped[model_field] = value
            
            person_name = mapped.get("person_name", "").strip()
            record_date_str = mapped.get("record_date")

            # 调试：打印时间字段原始值（前5条）
            if _debug_logged < 5:
                _debug_logged += 1
                raw_start = fields.get("上班时间")
                raw_end = fields.get("下班时间")
                logger.info(f"[Feishu] 时间字段原始值: person={person_name}, start={raw_start!r}, end={raw_end!r}, mapped_start={mapped.get('start_time')!r}, mapped_end={mapped.get('end_time')!r}")

            # 调试：打印审批字段原始值（前3条）
            if _debug_logged <= 5:
                appr1_raw = fields.get("审批人1审批结果")
                appr2_raw = fields.get("审批人2审核结果")
                appr1_mapped = mapped.get("approver1_result")
                appr2_mapped = mapped.get("approver2_result")
                if appr1_raw is not None or appr2_raw is not None:
                    logger.info(
                        f"[Feishu] 审批字段原始值: person={person_name}, date={record_date_str}, "
                        f"raw_appr1={appr1_raw!r}, raw_appr2={appr2_raw!r}, "
                        f"mapped_appr1={appr1_mapped!r}, mapped_appr2={appr2_mapped!r}"
                    )

            if not person_name or not record_date_str:
                skipped_count += 1
                continue

            # ★ 先处理日期（把飞书返回的数值/字符串转为 Date 对象）
            try:
                if isinstance(record_date_str, (int, float)):
                    if record_date_str > 10000000000:
                        record_date = date.fromtimestamp(record_date_str / 1000)
                    else:
                        record_date = date.fromtimestamp(record_date_str)
                elif isinstance(record_date_str, str):
                    record_date = date.fromisoformat(record_date_str[:10])
                else:
                    skipped_count += 1
                    continue
            except Exception:
                skipped_count += 1
                continue

            # ★ 用 Date 对象做日期过滤（避免字符串比较导致时间戳被错误排除）
            if date_start and record_date < date.fromisoformat(date_start):
                skipped_count += 1
                continue
            if date_end and record_date > date.fromisoformat(date_end):
                skipped_count += 1
                continue

            # 处理数值字段
            def safe_float(val, default=0):
                try:
                    return float(val) if val is not None else default
                except (ValueError, TypeError):
                    return default

            def safe_int(val, default=0):
                try:
                    return int(float(val)) if val is not None else default
                except (ValueError, TypeError):
                    return default

            def safe_time(val):
                """安全解析时间值，返回 datetime.time 或 None

                飞书时间字段可能有多种格式:
                1. 毫秒 Unix 时间戳 (> 1000000000000): 如 1783038600000 → datetime 时间部分
                2. 秒数自午夜 (< 86400): 如 32400 → 09:00:00
                3. Excel 时间格式 (0 < val < 1): 如 0.5 → 12:00:00
                4. 字符串格式: "09:00:00" 等
                """
                import datetime as dt
                if val is None:
                    return None
                if isinstance(val, dt.time):
                    return val
                if isinstance(val, (int, float)):
                    try:
                        # 飞书日期时间戳（毫秒 Unix 时间戳），提取时间部分
                        # 如 1783038600000 → 2026-07-03 06:30:00 CST → 06:30:00
                        if val > 1000000000000:
                            dt_obj = dt.datetime.fromtimestamp(val / 1000)
                            return dt_obj.time()
                        # Excel 时间格式：小数表示一天中的时间（0.0 = 00:00, 0.5 = 12:00）
                        if 0 < val < 1:
                            total_seconds = round(val * 24 * 3600)
                        else:
                            # 秒数自午夜（如 32400 = 9:00）
                            total_seconds = int(val)
                        hours = total_seconds // 3600
                        minutes = (total_seconds // 60) % 60
                        seconds = total_seconds % 60
                        return dt.time(hours, minutes, seconds)
                    except (ValueError, OverflowError):
                        return None
                if isinstance(val, str):
                    val = val.strip()
                    if not val:
                        return None
                    # 尝试多种时间格式
                    for fmt in ["%H:%M:%S", "%H:%M", "%H%M%S", "%H%M"]:
                        try:
                            t = dt.datetime.strptime(val, fmt).time()
                            return t
                        except ValueError:
                            continue
                    # 尝试 fromisoformat
                    try:
                        return dt.time.fromisoformat(val)
                    except ValueError:
                        pass
                    # 尝试解析为数字（可能是 Excel 时间格式的小数）
                    try:
                        num = float(val)
                        return safe_time(num)
                    except ValueError:
                        pass
                return None

            def _norm_approval(raw):
                """标准化审批状态：飞书值 → 系统值"""
                if raw is None or (isinstance(raw, str) and not raw.strip()):
                    return None
                raw = str(raw).strip()
                if raw in ("通过", "批准", "已通过", "同意", "审核通过", "已审批"):
                    return "通过"
                if raw in ("驳回", "已驳回", "拒绝", "不通过", "未通过"):
                    return "驳回"
                return raw

            # 构建数据
            defaults = {
                "person_name": person_name,
                "record_date": record_date,
                "requirement_code": str(mapped.get("requirement_code", "") or ""),
                "test_version": str(mapped.get("test_version", "") or ""),
                "test_task": str(mapped.get("test_task", "") or ""),
                "car_number": (str(mapped.get("car_number", "") or "") or "")[:200],
                "start_time": safe_time(mapped.get("start_time")),
                "end_time": safe_time(mapped.get("end_time")),
                "work_duration": safe_float(mapped.get("work_duration"), 0),
                "overtime_hours": safe_float(mapped.get("overtime_hours"), 0),
                "total_hours": safe_float(mapped.get("total_hours"), safe_float(mapped.get("work_duration"), 0) + safe_float(mapped.get("overtime_hours"), 0)),
                "travel_status": str(mapped.get("travel_status", "") or ""),
                "work_location": str(mapped.get("work_location", "") or ""),
                "location_coords": str(mapped.get("location_coords", "") or ""),
                "approver1_result": _norm_approval(mapped.get("approver1_result")),
                "approver2_result": _norm_approval(mapped.get("approver2_result")),
            }

            # 调试：打印标准化后的审批值（仅前3条有审批数据的记录）
            if _debug_logged <= 6:
                logger.info(
                    f"[Feishu] 标准化审批值: person={person_name}, date={record_date}, "
                    f"norm_appr1={defaults['approver1_result']!r}, norm_appr2={defaults['approver2_result']!r}"
                )

            if record_type == "engineer":
                defaults["is_overtime"] = str(mapped.get("is_overtime", "")).strip() in ("是", "true", "True", "1", "加班")
                defaults["workload"] = str(mapped.get("workload", "") or "")[:500]
                defaults["problems_found"] = safe_int(mapped.get("problems_found"), 0)
                defaults["check_cases"] = safe_int(mapped.get("check_cases"), 0)
                defaults["software_flash_count"] = safe_int(mapped.get("software_flash_count"), 0)
                defaults["issue_detail"] = str(mapped.get("issue_detail", "") or "")
            else:
                defaults["is_overtime"] = str(mapped.get("is_overtime", "")).strip() in ("是", "true", "True", "1", "加班")
                defaults["vehicle_initial_mileage"] = safe_float(mapped.get("vehicle_initial_mileage"), 0)
                defaults["vehicle_end_mileage"] = safe_float(mapped.get("vehicle_end_mileage"), 0)
                defaults["vehicle_test_mileage"] = safe_float(mapped.get("vehicle_test_mileage"), 0)
                defaults["daily_advance_total"] = safe_float(mapped.get("daily_advance_total"), 0)

            # ★ 直接从飞书字段获取项目和试验单号（不再通过本地DB关联查找）
            # 优先用"填写人选择填写车型项目"文本（field_map 中"查询填写人所在车型项目"返回 opt token 会覆盖文本，
            # 车型项目匹配 PERSONNEL"车型项目-选项"需文本）
            _proj_text = fields.get("填写人选择填写车型项目")
            if isinstance(_proj_text, str) and _proj_text.strip():
                raw_project = _proj_text.strip()
            elif isinstance(_proj_text, list) and _proj_text and isinstance(_proj_text[0], str):
                raw_project = _proj_text[0].strip()
            else:
                raw_project = str(mapped.get("_project_name", "") or "")
            
            # ★★★ 关键修复：从飞书关联字段中提取 link.token（而非 text）
            # 飞书关联字段结构：[{"link": {"token": "optjE1WUyq"}, "text": "H56E-202606073"}]
            # 之前取 text 作为查找 key 导致永远匹配不上 PERSONNEL 表映射（key 是 record_id）
            _link_token = ""
            _text_fallback = str(mapped.get("requirement_code_token", "") or "")
            for _req_field_name in ("查询填写人项目需求编号", "根据填写人选择，生成试验单号", "试验需求编号"):
                _req_raw = fields.get(_req_field_name)
                if _req_raw and isinstance(_req_raw, list) and len(_req_raw) > 0 and isinstance(_req_raw[0], dict):
                    _link_info = _req_raw[0].get("link")
                    if _link_info and isinstance(_link_info, dict):
                        _link_token = str(_link_info.get("token", ""))
                        if _link_token:
                            break
            # 如果关联字段不存在 link.token 结构（可能是普通文本字段），用 text 值作为 fallback
            if not _link_token:
                _link_token = _text_fallback
            
            # 解析试验单号：
            # 1) 优先通过 PERSONNEL 表 token 映射查找
            # 2) 失败则用飞书关联字段的 text 值（可能是直接文本）
            # 注意：飞书该天数据试验需求编号为空时，不再按人员绑定关系兜底匹配，
            # 避免人员跨月调动后历史工时被错误关联到最新试验单
            requirement_code = ""
            if _link_token and _link_token not in ("None", "未匹配", ""):
                requirement_code = _token_to_test_order.get(_link_token, "")
            # text 兜底（当关联字段 text 就是试验单号时）
            if not requirement_code and _text_fallback and _text_fallback not in ("None", "未匹配", ""):
                # 如果 text 值看起来像 token（以opt/rec开头），不要直接用它
                if not (_text_fallback.startswith("opt") and len(_text_fallback) < 20):
                    requirement_code = _text_fallback
            # opt token 与 PERSONNEL record_id(recv) 体系不匹配、解析失败时，
            # 用考勤"填写人选择填写车型项目"匹配 PERSONNEL"车型项目-选项"→试验单号
            # 用考勤"填写人选择填写车型项目"匹配 PERSONNEL"车型项目-选项"→试验单号
            # 条件：raw_project 非空（考勤选了车型项目即认为应关联试验单）
            if not requirement_code and project_to_test_order and raw_project:
                # raw_project 可能是 PERSONNEL 车型项目-选项 的简写前缀
                # （如 H47A-ZY-JSY 匹配 H47A-ZY-JSY 和 H47A-ZY-JSY-0701-36）
                _proj_candidates = []
                for _k, _v in project_to_test_order.items():
                    if _k == raw_project or _k.startswith(raw_project + "-"):
                        _proj_candidates.extend(_v)
                # 车型项目匹配到试验单即关联（飞书 lookup 按车型项目查试验单，不做日期消歧）
                if _proj_candidates:
                    requirement_code = _proj_candidates[0]["test_order_no"]
            if not requirement_code or requirement_code in ("None", "未匹配"):
                requirement_code = ""
            
            # ★ 调试：前10条打印 token 解析细节（含原始字段完整结构，成功/失败都打印）
            if _token_debug_logged < 10:
                _token_debug_logged += 1
                _sample_ptokens = list(_token_to_test_order.keys())[:5] if _token_to_test_order else []
                _raw_query_struct = fields.get("查询填写人项目需求编号")
                _raw_gen_struct = fields.get("根据填写人选择，生成试验单号")
                _raw_req_struct = fields.get("试验需求编号")
                logger.info(
                    f"[Feishu] TOKEN解析[{record_type}]: person={person_name}, date={record_date}, "
                    f"link_token={_link_token!r}, text_fb={_text_fallback!r}, req_code结果={requirement_code!r}, "
                    f"PERSONNEL样例tokens={_sample_ptokens}, "
                    f"raw_查询需求编号={json.dumps(_raw_query_struct, ensure_ascii=False) if _raw_query_struct else 'None'}, "
                    f"raw_生成试验单号={json.dumps(_raw_gen_struct, ensure_ascii=False) if _raw_gen_struct else 'None'}, "
                    f"raw_试验需求编号={json.dumps(_raw_req_struct, ensure_ascii=False) if _raw_req_struct else 'None'}"
                )

            # ★ 优先使用飞书字段中的项目名称，直接查找/创建项目
            if raw_project and raw_project not in ("", "None"):
                # 在内存中查找已有项目
                project_id = None
                for p in proj_cache:
                    if p["project_name"] == raw_project:
                        project_id = p["id"]
                        break
                if project_id is None:
                    # 创建新项目
                    new_proj = await ExpenseProject.create(
                        series_name=raw_project, project_name=raw_project, category="自研",
                    )
                    project_id = new_proj.id
                    proj_cache.append({"id": new_proj.id, "project_name": raw_project})
                    created_proj += 1
                defaults["project_id"] = project_id

            # ★ 使用飞书字段中的试验单号，搜不到就为空
            if requirement_code and requirement_code not in ("", "None", "未匹配"):
                defaults["requirement_code"] = requirement_code
            else:
                defaults["requirement_code"] = ""

            # 兜底：如果还没有项目，用未匹配项目
            if not defaults.get("project_id"):
                defaults["project_id"] = unmatched_project_id
                project_source = "from_unmatched"
            else:
                project_source = "from_feishu" if raw_project and raw_project not in ("", "None") else "from_requirement"

            # 调试：打印前10条记录的详细映射过程（含原始字段值）
            if _proj_debug_logged < 10:
                _proj_debug_logged += 1
                # 打印关键原始字段，帮助诊断字段名/值是否匹配
                _raw_query = fields.get("查询填写人项目需求编号")
                _raw_gen = fields.get("根据填写人选择，生成试验单号")
                _raw_req = fields.get("试验需求编号")
                _raw_proj_sel = fields.get("填写人选择填写车型项目")
                _raw_proj_query = fields.get("查询填写人所在车型项目")
                _raw_proj_belong = fields.get("所属项目")
                _raw_proj_detail = fields.get("所属项目信息-详细")
                logger.info(
                    f"[Feishu] 项目映射(新): person={person_name}, date={record_date}, "
                    f"link_token={_link_token!r}, text_fb={_text_fallback!r}, req_code={requirement_code!r}, "
                    f"raw_project={raw_project!r}, final_project_id={defaults.get('project_id')}, source={project_source}, "
                    f"raw_query_ppl=[{_raw_query!r}], raw_gen_order=[{_raw_gen!r}], raw_req_no=[{_raw_req!r}], "
                    f"raw_proj_sel=[{_raw_proj_sel!r}], raw_proj_query=[{_raw_proj_query!r}], "
                    f"raw_proj_belong=[{_raw_proj_belong!r}], raw_proj_detail=[{_raw_proj_detail!r}]"
                )

            # ★ 内存查找已有记录
            existing_id = existing_map.get((str(record_date), person_name))
            if existing_id:
                to_update.append((existing_id, defaults))
            else:
                to_create.append(defaults)

        # ═══════════════════════════════════════════════════════════
        # ★ 批量写入阶段
        # ═══════════════════════════════════════════════════════════

        created_count = 0
        updated_count = 0

        if to_create:
            objects = [AttendanceModel(**d) for d in to_create]
            await AttendanceModel.bulk_create(objects, batch_size=500)
            created_count = len(to_create)
            logger.info(f"[Feishu] 批量创建 {created_count} 条记录")

        if to_update:
            import asyncio as _asyncio
            # 并发批量更新，每批 100 条，最多 20 个并发
            semaphore = _asyncio.Semaphore(20)
            async def _update_one(eid, upd):
                async with semaphore:
                    await AttendanceModel.filter(id=eid).update(**upd)
            await _asyncio.gather(*[_update_one(eid, upd) for eid, upd in to_update])
            updated_count = len(to_update)
            logger.info(f"[Feishu] 批量更新 {updated_count} 条记录")

        message = f"同步完成: 共读取 {len(records)} 条，新增 {created_count}，更新 {updated_count}，跳过 {skipped_count}，新增项目 {created_proj}"
        logger.info(f"[Feishu] {message}")
        return {
            "success": True, "message": message,
            "total_records": len(records),
            "created": created_count, "updated": updated_count, "skipped": skipped_count,
            "project_created": created_proj,
        }

    async def sync_personnel_from_feishu(self, table_id: str) -> Dict[str, Any]:
        """从飞书多维表格同步试验单号与人员绑定关系，同时更新 TestOrder 表的试验金额/时间/人数/供应商
        Args:
            table_id: 飞书多维表格的 TABLE_ID
        """
        from app.models.expense import RequirementPersonnel, TestOrder

        # 使用独立配置，不修改 self.config 以避免并行竞态
        cfg = EXPENSE_FEISHU_CONFIG

        try:
            token = await self.get_tenant_access_token(config=cfg)
        except Exception as e:
            logger.error(f"[Feishu] 人员绑定同步 - 获取token失败: {e}")
            return {"success": False, "message": f"获取飞书token失败: {str(e)}", "created": 0, "updated": 0}

        # 诊断：获取飞书表格的实际字段名列表
        try:
            field_items = await self.get_table_fields(token, table_id, config=cfg)
            field_names = [f.get("field_name") for f in field_items]
            logger.info(f"[Feishu] 人员绑定表实际字段名: {field_names}")
        except Exception as e:
            logger.warning(f"[Feishu] 人员绑定表 - 获取字段列表失败: {e}")

        try:
            records = await self._fetch_all_records(token, table_id, config=cfg)
        except Exception as e:
            logger.error(f"[Feishu] 人员绑定同步 - 获取记录失败: {e}")
            return {"success": False, "message": f"获取表格记录失败: {str(e)}", "created": 0, "updated": 0}

        created_count = 0
        updated_count = 0
        to_updated_count = 0  # TestOrder 更新数
        to_missing_count = 0  # 匹配失败的试验单数
        to_created_count = 0  # 新增试验单数（如果启用自动创建）

        # 诊断：打印前 3 条记录的关键字段原始值，帮助排查字段结构
        if records:
            for i, rec in enumerate(records[:3]):
                rec_fields = rec.get("fields", {})
                logger.info(f"[Feishu] 人员绑定表第{i+1}条记录字段名: {list(rec_fields.keys())}")
                # 重点打印负责人字段的原始类型和值
                for key in ("负责人", "responsible_person", "供应商", "supplier",
                            "委外人员", "outsourced_personnel", "人员", "试验需求编号", "试验单号"):
                    if key in rec_fields:
                        raw = rec_fields[key]
                        logger.info(f"  [{key}] type={type(raw).__name__}, repr={repr(raw)[:200]}")

        # ★ 清理历史脏数据：把之前存成 dict 字符串的负责人字段清掉，让新同步写入正确值
        try:
            bad_rp = await RequirementPersonnel.filter(responsible_person__contains="avatar_url").count()
            if bad_rp > 0:
                await RequirementPersonnel.filter(responsible_person__contains="avatar_url").update(responsible_person="")
                logger.info(f"[Feishu] 清理人员绑定表中 {bad_rp} 条脏数据(responsible_person)")
            bad_to = await TestOrder.filter(responsible_person__contains="avatar_url").count()
            if bad_to > 0:
                await TestOrder.filter(responsible_person__contains="avatar_url").update(responsible_person="")
                logger.info(f"[Feishu] 清理试验单表中 {bad_to} 条脏数据(responsible_person)")
        except Exception as e:
            logger.warning(f"[Feishu] 清理脏数据异常: {e}")

        for record in records:
            fields = record.get("fields", {})
            record_id = record.get("record_id", "unknown")

            # 取字段值（处理飞书多维表格特殊类型）
            def get_field(field_name, default=""):
                value = fields.get(field_name)
                if value is None:
                    return default
                if isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], dict):
                        # 飞书多人字段：[{"name":"张三"},{"name":"李四"}] → "张三,李四"
                        if all(isinstance(v, dict) and "name" in v for v in value):
                            return ",".join(str(v["name"]) for v in value)
                        # 飞书用户字段：{"name":"张三","avatar_url":"..."}
                        if "name" in value[0]:
                            return str(value[0]["name"])
                        # 飞书文本字段：{"text":"...","type":"text"}
                        if "text" in value[0]:
                            return str(value[0]["text"])
                        return str(value[0])
                    # 字符串数组：["张三","李四","王五"] → "张三,李四,王五"
                    return ",".join(str(v) for v in value)
                # 兜底：如果是 dict 类型（非列表包裹的用户字段）
                if isinstance(value, dict):
                    if "name" in value:
                        return str(value["name"])
                    if "text" in value:
                        return str(value["text"])
                    return str(value)
                return str(value) if value is not None else default

            def get_number(field_name, default=0):
                """读取数值字段，支持字符串和数字"""
                value = fields.get(field_name)
                if value is None:
                    return default
                if isinstance(value, (int, float)):
                    return value
                if isinstance(value, str):
                    try:
                        return float(value) if '.' in value else int(value)
                    except (ValueError, TypeError):
                        return default
                if isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], (int, float)):
                        return value[0]
                    if isinstance(value[0], dict):
                        v = value[0].get("text", str(value[0]))
                    else:
                        v = str(value[0])
                    try:
                        return float(v) if '.' in v else int(v)
                    except (ValueError, TypeError):
                        return default
                return default

            def get_date(field_name):
                """读取日期字段，返回 date 对象或 None"""
                value = fields.get(field_name)
                if value is None:
                    return None
                if isinstance(value, (int, float)):
                    if value > 10000000000:
                        return date.fromtimestamp(value / 1000)
                    elif value > 0:
                        return date.fromtimestamp(value)
                    return None
                if isinstance(value, str):
                    try:
                        return date.fromisoformat(value[:10])
                    except Exception:
                        return None
                if isinstance(value, list) and len(value) > 0:
                    v = value[0]
                    if isinstance(v, (int, float)):
                        if v > 10000000000:
                            return date.fromtimestamp(v / 1000)
                        return date.fromtimestamp(v) if v > 0 else None
                    if isinstance(v, dict):
                        v = v.get("text", "")
                    if isinstance(v, str):
                        try:
                            return date.fromisoformat(v[:10])
                        except Exception:
                            return None
                return None

            # ── 人员绑定字段 ──
            test_order_no = get_field("试验需求编号") or get_field("试验单号") or get_field("test_order_no")
            # 供应商：飞书表格无直接字段，尝试从所属项目推断
            supplier = get_field("供应商") or get_field("supplier") or ""
            # 委外人员：合并驾驶员和工程师字段
            driver_names = get_field("驾驶员")
            engineer_names = get_field("工程师")
            outsourced_parts = []
            if driver_names:
                outsourced_parts.append(driver_names)
            if engineer_names:
                outsourced_parts.append(engineer_names)
            outsourced_personnel = ",".join(outsourced_parts) if outsourced_parts else (
                get_field("委外人员") or get_field("outsourced_personnel") or get_field("人员")
            )
            # 负责人：飞书字段名为"车型项目负责人"
            responsible_person = get_field("车型项目负责人") or get_field("负责人") or get_field("responsible_person")
            # 截断超过 50 字符的值（字段 max_length=50）
            supplier = supplier[:50] if supplier and len(supplier) > 50 else supplier
            responsible_person = responsible_person[:50] if responsible_person and len(responsible_person) > 50 else responsible_person

            # 首次读取到负责人时打印日志，确认字段解析是否正确
            if responsible_person and not hasattr(self, '_rp_logged'):
                self._rp_logged = True
                logger.info(f"[Feishu] 负责人字段解析结果: '{responsible_person}' (len={len(responsible_person)})")

            # ── 试验单号扩展字段（从飞书同步到 TestOrder 表）──
            # 打印前3条记录的所有字段原始值，用于诊断字段名和数据类型
            if not hasattr(self, '_fields_debug_count'):
                self._fields_debug_count = 0
            if self._fields_debug_count < 3:
                self._fields_debug_count += 1
                # 只打印与金额相关的字段
                money_fields = {k: v for k, v in fields.items() if any(kw in k for kw in ['金额', '花费', '费用', '价格', 'price', 'cost', 'amount'])}
                logger.info(f"[Feishu] 记录#{record_id} 金额相关字段: {money_fields}")
                logger.info(f"[Feishu] 记录#{record_id} 所有字段名: {list(fields.keys())}")
            # 金额：试验金额 = 飞书预算列（试验单的总预算金额）
            total_price = get_number("预算", 0)
            # 打印金额字段调试信息（仅首次）
            if not hasattr(self, '_price_logged'):
                self._price_logged = True
                logger.info(f"[Feishu] 金额字段解析：总和={get_number('车型项目中-工程师和驾驶员费用总和（元）')}, 工程师={get_number('车型项目中-工程师总费用（元）')}, 驾驶员={get_number('车型项目中-驾驶员总费用（元）')}, 最终值={total_price}")
            # 时间：飞书字段名为"试验开始日期"/"试验结束日期"
            planned_start = get_date("试验开始日期") or get_date("计划开展时间") or get_date("计划开始时间") or get_date("planned_start_time")
            planned_end = get_date("试验结束日期") or get_date("计划完成时间") or get_date("计划结束时间") or get_date("planned_end_time")
            actual_start = get_date("实际开展时间") or get_date("实际开始时间") or get_date("actual_start_time")
            actual_end = get_date("实际完成时间") or get_date("实际结束时间") or get_date("actual_end_time")
            # 根据工程师单价推断试验需求通过日期：1040元/天 = 4月1日后新单价（达安旧1280、其他旧1440等均为旧单价）
            eng_unit_price = get_number("工程师不含税单价（元/天）")
            if eng_unit_price and int(float(eng_unit_price)) == 1040:
                requirement_date = date(2026, 4, 1)
            else:
                requirement_date = None
            # 人数：合并工程师个数和驾驶员个数
            eng_count = get_number("工程师个数") or 0
            drv_count = get_number("驾驶员个数") or 0
            outsourced_count = (int(eng_count) + int(drv_count)) if (eng_count or drv_count) else (get_number("委外人数") or get_number("人数") or get_number("outsourced_count") or 0)

            if not test_order_no:
                logger.warning(f"[Feishu] 人员绑定 - 记录 {record_id} 跳过: 试验需求编号为空, 实际字段名: {list(fields.keys())}")
                continue

            # ── 同步到 RequirementPersonnel ──
            existing = await RequirementPersonnel.filter(test_order_no=test_order_no).first()
            if existing:
                if supplier:
                    existing.supplier = supplier
                if outsourced_personnel:
                    existing.outsourced_personnel = outsourced_personnel
                if responsible_person:
                    existing.responsible_person = responsible_person
                if outsourced_count:
                    existing.outsourced_count = int(outsourced_count)
                existing.requirement_date = requirement_date
                await existing.save()
                updated_count += 1
            else:
                await RequirementPersonnel.create(
                    test_order_no=test_order_no,
                    supplier=supplier,
                    outsourced_personnel=outsourced_personnel,
                    responsible_person=responsible_person,
                    outsourced_count=int(outsourced_count) if outsourced_count else 0,
                    requirement_date=requirement_date,
                )
                created_count += 1

            # ── 同步到 TestOrder（更新试验单）──
            test_order = await TestOrder.filter(test_order_no=test_order_no).first()
            if test_order:
                updated = False
                if total_price is not None:
                    old_price = test_order.total_price
                    test_order.total_price = float(total_price) if total_price else 0.0
                    updated = True
                if planned_start:
                    test_order.planned_start_time = planned_start
                    updated = True
                if planned_end:
                    test_order.planned_end_time = planned_end
                    updated = True
                if actual_start:
                    test_order.actual_start_time = actual_start
                    updated = True
                if actual_end:
                    test_order.actual_end_time = actual_end
                    updated = True
                if supplier:
                    test_order.supplier = supplier
                    updated = True
                if outsourced_count:
                    test_order.outsourced_count = int(outsourced_count)
                    updated = True
                if responsible_person:
                    test_order.responsible_person = responsible_person
                    updated = True
                if updated:
                    await test_order.save()
                    to_updated_count += 1
            else:
                if not hasattr(self, '_to_missing_list'):
                    self._to_missing_list = []
                if len(self._to_missing_list) < 5:
                    self._to_missing_list.append(test_order_no)
                to_missing_count += 1

        # 诊断：飞书值 vs DB 值对比
        missing_sample = []
        db_samples = []
        if to_missing_count > 0:
            missing_sample = getattr(self, '_to_missing_list', [])
            try:
                db_samples = await TestOrder.all().limit(5).values_list("test_order_no", flat=True)
            except Exception:
                db_samples = []

        message = f"人员绑定同步完成: 共 {len(records)} 条，新增人员绑定 {created_count}，更新人员绑定 {updated_count}，更新试验单 {to_updated_count}，未匹配 {to_missing_count}"
        if missing_sample:
            message += f"。飞书例值: {missing_sample[:3]}"
        if db_samples:
            message += f"。DB例值: {list(db_samples)}"
        logger.info(f"[Feishu] {message}")
        return {
            "success": True, "message": message,
            "total_records": len(records),
            "created": created_count, "updated": updated_count,
            "test_order_updated": to_updated_count,
        }

    async def sync_expense_code_from_feishu(self, table_id: str) -> Dict[str, Any]:
        """从飞书多维表格同步费用号数据（自动创建缺失的项目和预算号）"""
        from app.models.expense import (
            ExpenseProject, BudgetCode, ExpenseCode, TestOrder,
        )
        cfg = EXPENSE_FEISHU_CONFIG

        try:
            token = await self.get_tenant_access_token(config=cfg)
        except Exception as e:
            return {"success": False, "message": f"获取token失败: {str(e)}", "created": 0, "updated": 0}

        try:
            records = await self._fetch_all_records(token, table_id, config=cfg)
        except Exception as e:
            return {"success": False, "message": f"获取记录失败: {str(e)}", "created": 0, "updated": 0}

        # 预加载已有数据
        proj_map = {}  # (series_name, project_name, category) -> ExpenseProject
        for p in await ExpenseProject.all():
            proj_map[(p.series_name, p.project_name, p.category)] = p

        budget_map = {}  # budget_code -> BudgetCode
        for b in await BudgetCode.all():
            budget_map[b.budget_code] = b

        ec_map = {}  # expense_code -> ExpenseCode
        for e in await ExpenseCode.all():
            ec_map[e.expense_code] = e

        to_map = {}  # test_order_no -> TestOrder
        for t in await TestOrder.all():
            to_map[t.test_order_no] = t

        created_proj = 0
        created_budget = 0
        created_ec = 0
        updated_ec = 0
        skipped = 0

        for record in records:
            fields = record.get("fields", {})
            series_name = (fields.get("系列名称") or "").strip()
            category = (fields.get("类别") or "").strip()
            project_name = (fields.get("项目名称") or "").strip()
            budget_code = (fields.get("所属预算号") or "").strip()
            expense_code_val = (fields.get("费用号") or "").strip()
            total_amt = fields.get("费用号总金额")
            resp_person = (fields.get("责任人") or "").strip()
            test_order_no = (fields.get("试验任务单号") or "").strip()

            if not project_name or not series_name:
                skipped += 1
                continue

            # 1. 查找/创建 ExpenseProject
            key = (series_name, project_name, category)
            project = proj_map.get(key)
            if not project:
                project = await ExpenseProject.create(
                    series_name=series_name, project_name=project_name,
                    category=category or "自研",
                )
                proj_map[key] = project
                created_proj += 1

            # 2. 查找/创建 BudgetCode（如果有预算号）
            budget_obj = None
            if budget_code:
                budget_obj = budget_map.get(budget_code)
                if not budget_obj:
                    budget_obj = await BudgetCode.create(
                        project=project, budget_code=budget_code,
                    )
                    budget_map[budget_code] = budget_obj
                    created_budget += 1

            # 3. 处理费用号
            if expense_code_val:
                ec = ec_map.get(expense_code_val)
                if ec:
                    # 更新已有费用号
                    changed = False
                    if total_amt is not None:
                        try:
                            dec_val = float(total_amt)
                            if ec.total_amount != dec_val:
                                ec.total_amount = dec_val
                                changed = True
                        except (ValueError, TypeError):
                            pass
                    if resp_person and ec.responsible_person != resp_person:
                        ec.responsible_person = resp_person
                        changed = True
                    if budget_obj and ec.budget_id != budget_obj.id:
                        ec.budget = budget_obj
                        changed = True
                    if changed:
                        await ec.save()
                        updated_ec += 1
                else:
                    # 创建新费用号
                    ec = await ExpenseCode.create(
                        budget=budget_obj or (await BudgetCode.first()) or project,
                        expense_code=expense_code_val,
                        total_amount=float(total_amt) if total_amt is not None and str(total_amt).strip() else 0,
                        responsible_person=resp_person or None,
                    )
                    ec_map[expense_code_val] = ec
                    created_ec += 1

                # 4. 如果有试验任务单号，链接到费用号
                if test_order_no and ec:
                    to = to_map.get(test_order_no)
                    if to and to.expense_code_id != ec.id:
                        to.expense_code = ec
                        await to.save()
                        to_map[test_order_no] = to

        message = f"同步完成: 共 {len(records)} 条，新增项目 {created_proj}，新增预算号 {created_budget}，新增费用号 {created_ec}，更新费用号 {updated_ec}，跳过 {skipped}"
        logger.info(f"[Feishu] 费用号同步: {message}")
        return {
            "success": True, "message": message,
            "total_records": len(records),
            "created": created_ec, "updated": updated_ec,
            "project_created": created_proj,
            "budget_created": created_budget,
        }

    async def sync_test_order_from_feishu(self, table_id: str) -> Dict[str, Any]:
        """从飞书多维表格同步试验单数据（同时关联费用号看板，自动计算已使用金额）"""
        from app.models.expense import (
            ExpenseProject, BudgetCode, ExpenseCode, TestOrder, DailyRecord,
        )
        cfg = EXPENSE_FEISHU_CONFIG

        try:
            token = await self.get_tenant_access_token(config=cfg)
        except Exception as e:
            return {"success": False, "message": f"获取token失败: {str(e)}", "created": 0, "updated": 0}

        # 1. 读取试验单表数据
        try:
            records = await self._fetch_all_records(token, table_id, config=cfg)
        except Exception as e:
            return {"success": False, "message": f"获取试验单记录失败: {str(e)}", "created": 0, "updated": 0}

        # 2. 读取费用号看板数据，建立试验任务单号 → 费用号/预算号映射
        expense_code_map = {}  # test_order_no -> {expense_code, budget_code, project_info}
        try:
            ec_table_id = cfg["TABLE_IDS"]["EXPENSE_CODE"]
            ec_records = await self._fetch_all_records(token, ec_table_id, config=cfg)
            def _parse_val(value):
                if value is None:
                    return ""
                if isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], dict):
                        if "name" in value[0]:
                            return str(value[0]["name"])
                        if "text" in value[0]:
                            return str(value[0]["text"])
                        return str(value[0])
                    return str(value[0])
                if isinstance(value, dict):
                    if "name" in value:
                        return str(value["name"])
                    if "text" in value:
                        return str(value["text"])
                    return str(value)
                return str(value)
            for rec in ec_records:
                fields = rec.get("fields", {})
                to_no_raw = _parse_val(fields.get("试验任务单号", "")).strip()
                # 一个费用号可能包含多个试验单号（中文/英文分号隔开）
                to_no_list = [s.strip() for s in to_no_raw.replace("；", ";").split(";") if s.strip()]
                ec_info = {
                    "expense_code": _parse_val(fields.get("费用号", "")).strip(),
                    "budget_code": _parse_val(fields.get("所属预算号", "")).strip(),
                    "series_name": _parse_val(fields.get("系列名称", "")).strip(),
                    "project_name": _parse_val(fields.get("项目名称", "")).strip(),
                    "category": _parse_val(fields.get("类别", "")).strip(),
                }
                for to_no in to_no_list:
                    expense_code_map[to_no] = ec_info
            logger.info(f"[Feishu] 费用号看板数据: 共 {len(ec_records)} 条，可关联 {len(expense_code_map)} 条试验单")
        except Exception as e:
            logger.warning(f"[Feishu] 读取费用号看板失败: {e}")

        # 3. 预加载DB数据
        proj_map = {}
        for p in await ExpenseProject.all():
            proj_map[(p.series_name, p.project_name, p.category)] = p

        budget_map = {}
        for b in await BudgetCode.all():
            budget_map[b.budget_code] = b

        ec_map = {}
        for e in await ExpenseCode.all():
            ec_map[e.expense_code] = e

        to_map = {}
        for t in await TestOrder.all():
            to_map[t.test_order_no] = t

        created_proj = 0
        created_budget = 0
        created_ec = 0
        created_to = 0
        updated_to = 0
        skipped = 0
        linked_ec = 0

        for record in records:
            fields = record.get("fields", {})
            # 使用 get_field 处理飞书字段（支持数组/字典/字符串）
            def get_field_val(field_name, default=""):
                value = fields.get(field_name)
                if value is None:
                    return default
                if isinstance(value, list) and len(value) > 0:
                    if isinstance(value[0], dict):
                        if "name" in value[0]:
                            return str(value[0]["name"])
                        if "text" in value[0]:
                            return str(value[0]["text"])
                        return str(value[0])
                    return str(value[0])
                if isinstance(value, dict):
                    if "name" in value:
                        return str(value["name"])
                    if "text" in value:
                        return str(value["text"])
                    return str(value)
                return str(value)

            def get_number(field_name, default=0):
                """读取数值字段，支持数组、字符串、数字和飞书dict格式"""
                value = fields.get(field_name)
                if value is None:
                    return default
                if isinstance(value, (int, float)):
                    return float(value)
                if isinstance(value, str):
                    try:
                        return float(value.replace(",", "").strip())
                    except (ValueError, TypeError):
                        return default
                # 飞书数值字段常见的 dict 格式：{"text": "50000", "type": "number"}
                if isinstance(value, dict):
                    v = value.get("text", str(value))
                    try:
                        return float(str(v).replace(",", "").strip())
                    except (ValueError, TypeError):
                        return default
                if isinstance(value, list) and len(value) > 0:
                    v = value[0]
                    if isinstance(v, (int, float)):
                        return float(v)
                    if isinstance(v, str):
                        try:
                            return float(v.replace(",", "").strip())
                        except (ValueError, TypeError):
                            return default
                    # 飞书列表中的 dict 元素：["text": "50000"]
                    if isinstance(v, dict):
                        v = v.get("text", str(v))
                        try:
                            return float(str(v).replace(",", "").strip())
                        except (ValueError, TypeError):
                            return default
                return default

            test_order_no = get_field_val("试验需求编号", "").strip()
            if not test_order_no:
                skipped += 1
                continue

            # 基本信息
            project_option = get_field_val("车型项目-选项", "")
            supplier = get_field_val("供应商", "")
            responsible_person = get_field_val("车型项目负责人", "")
            if isinstance(responsible_person, list) and len(responsible_person) > 0 and isinstance(responsible_person[0], dict):
                responsible_person = responsible_person[0].get("name", "")
            responsible_person = str(responsible_person)[:50] if responsible_person else ""

            # 金额：试验金额 = 飞书预算列（试验单的总预算金额）
            total_price = get_number("预算", 0)
            # 预算字段：同步到预算号的预算金额
            budget_amount = get_number("预算", 0)

            # 日期
            planned_start = None
            planned_end = None
            start_date = fields.get("试验开始日期")
            end_date = fields.get("试验结束日期")
            if isinstance(start_date, (int, float)) and start_date > 10000000000:
                planned_start = date.fromtimestamp(start_date / 1000)
            elif isinstance(start_date, str):
                try: planned_start = date.fromisoformat(start_date[:10])
                except: pass
            if isinstance(end_date, (int, float)) and end_date > 10000000000:
                planned_end = date.fromtimestamp(end_date / 1000)
            elif isinstance(end_date, str):
                try: planned_end = date.fromisoformat(end_date[:10])
                except: pass

            # 人数
            eng_count = 0
            drv_count = 0
            try: eng_count = int(fields.get("工程师个数", 0) or 0)
            except: pass
            try: drv_count = int(fields.get("驾驶员个数", 0) or 0)
            except: pass
            outsourced_count = eng_count + drv_count

            # 查找/关联费用号看板数据
            ec_info = expense_code_map.get(test_order_no)
            expense_code_obj = None
            if ec_info:
                # 使用费用号看板的项目信息
                series_name = ec_info.get("series_name", "")
                project_name = ec_info.get("project_name", "")
                category = ec_info.get("category", "")
                budget_code = ec_info.get("budget_code", "")
                expense_code_val = ec_info.get("expense_code", "")

                # 查找/创建项目
                if project_name and series_name:
                    key = (series_name, project_name, category)
                    project = proj_map.get(key)
                    if not project:
                        project = await ExpenseProject.create(
                            series_name=series_name, project_name=project_name,
                            category=category or "自研",
                        )
                        proj_map[key] = project
                        created_proj += 1

                    # 查找/创建预算号
                    if budget_code:
                        budget_obj = budget_map.get(budget_code)
                        if not budget_obj:
                            budget_obj = await BudgetCode.create(
                                project=project, budget_code=budget_code,
                            )
                            budget_map[budget_code] = budget_obj
                            created_budget += 1
                        # 同步预算金额到预算号
                        if budget_amount and float(budget_obj.budget_amount or 0) != budget_amount:
                            budget_obj.budget_amount = budget_amount
                            await budget_obj.save()

                    # 查找/创建费用号
                    if expense_code_val:
                        expense_code_obj = ec_map.get(expense_code_val)
                        if not expense_code_obj:
                            # 确保有默认项目和预算号（兜底）
                            default_budget = None
                            if budget_code:
                                default_budget = budget_map.get(budget_code)
                            if not default_budget:
                                default_budget = await BudgetCode.first()
                                if not default_budget:
                                    # 连默认预算号都没有，先用默认项目
                                    default_project = project or await ExpenseProject.first()
                                    if default_project:
                                        default_budget = await BudgetCode.create(
                                            project=default_project,
                                            budget_code=budget_code or "未分类",
                                        )
                                        budget_map[default_budget.budget_code] = default_budget
                                        created_budget += 1
                            if default_budget:
                                expense_code_obj = await ExpenseCode.create(
                                    budget=default_budget, expense_code=expense_code_val,
                                )
                                ec_map[expense_code_val] = expense_code_obj
                                created_ec += 1
                            created_ec += 1

                        # 关联试验单到费用号
                        if expense_code_obj:
                            linked_ec += 1

            # 创建/更新试验单
            to = to_map.get(test_order_no)
            if to:
                # 更新
                changed = False
                if total_price != float(to.total_price or 0):
                    to.total_price = total_price
                    changed = True
                if planned_start and to.planned_start_time != planned_start:
                    to.planned_start_time = planned_start
                    changed = True
                if planned_end and to.planned_end_time != planned_end:
                    to.planned_end_time = planned_end
                    changed = True
                if supplier and to.supplier != supplier:
                    to.supplier = supplier
                    changed = True
                if responsible_person and to.responsible_person != responsible_person:
                    to.responsible_person = responsible_person
                    changed = True
                if outsourced_count > 0 and to.outsourced_count != outsourced_count:
                    to.outsourced_count = outsourced_count
                    changed = True
                # 更新费用号关联（无关联时清除旧关联，不再兜底）
                if expense_code_obj and to.expense_code_id != expense_code_obj.id:
                    to.expense_code = expense_code_obj
                    changed = True
                elif not expense_code_obj and to.expense_code_id:
                    to.expense_code = None
                    changed = True
                if changed:
                    await to.save()
                    updated_to += 1
            else:
                # 创建新试验单（无费用号关联时设为 None，但 DB 字段不允许 null 则跳过关联）
                to = await TestOrder.create(
                    test_order_no=test_order_no,
                    expense_code=expense_code_obj or None,
                    total_price=total_price,
                    supplier=supplier[:50] if supplier else None,
                    responsible_person=responsible_person,
                    planned_start_time=planned_start,
                    planned_end_time=planned_end,
                    outsourced_count=outsourced_count,
                )
                to_map[test_order_no] = to
                created_to += 1

        # ★ 批量计算已使用金额：从每日费用汇总
        updated_used = 0
        for to in await TestOrder.all():
            try:
                drs = await DailyRecord.filter(test_order_id=to.id).exclude(approval_status="驳回").all()
                used = sum(float(r.total_amount or 0) for r in drs)
                if float(to.used_amount or 0) != used:
                    to.used_amount = used
                    await to.save()
                    updated_used += 1
            except Exception:
                pass

        message = f"试验单同步完成: 共 {len(records)} 条，新增试验单 {created_to}，更新试验单 {updated_to}，计算已使用金额 {updated_used}，关联费用号 {linked_ec}，新增项目 {created_proj}，新增预算号 {created_budget}，新增费用号 {created_ec}，跳过 {skipped}"
        logger.info(f"[Feishu] {message}")
        return {
            "success": True, "message": message,
            "total_records": len(records),
            "created": created_to, "updated": updated_to,
            "used_amount_updated": updated_used,
            "linked_expense_code": linked_ec,
            "project_created": created_proj,
            "budget_created": created_budget,
            "expense_code_created": created_ec,
        }

    async def _fetch_all_records(self, token: str, table_id: str, config: Optional[Dict[str, Any]] = None,
                                  date_field: Optional[str] = None, date_start: Optional[str] = None,
                                  date_end: Optional[str] = None,
                                  field_names: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """分页获取某张表格的所有记录（支持服务端日期过滤，大幅减少数据传输量）

        field_names: 仅拉取业务所需字段，减小载荷。
        """
        filter_formula = None
        if date_start and date_field:
            # 飞书API日期字段必须用 TODATE() 函数，不能直接用字符串
            cond = f'CurrentValue.[{date_field}] >= TODATE("{date_start}")'
            if date_end:
                cond += f' && CurrentValue.[{date_field}] < TODATE("{date_end}")'
            filter_formula = cond
            logger.info(f"[Feishu] 使用服务端日期过滤: {filter_formula}")

        all_records = []
        page_token = None
        while True:
            result = await self.get_bitable_records(token, table_id, page_token, config=config,
                                                    filter_formula=filter_formula, field_names=field_names)
            if result is None:
                logger.error(f"[Feishu] 表格 {table_id} 返回空结果，终止分页")
                break
            records = result.get("items") or []
            all_records.extend(records)
            page_token = result.get("has_more") and result.get("page_token")
            if not page_token:
                break
        return all_records


    def _extract_feishu_field_value(self, fields: Dict[str, Any], field_name: str) -> str:
        """从飞书记录的 fields 中提取字段值，处理数组/dict/字符串等多种格式"""
        value = fields.get(field_name)
        if value is None:
            return ""
        if isinstance(value, list) and len(value) > 0:
            if isinstance(value[0], dict):
                if "name" in value[0]:
                    return str(value[0]["name"])
                if "text" in value[0]:
                    return str(value[0]["text"])
                return str(value[0])
            return str(value[0])
        if isinstance(value, dict):
            if "name" in value:
                return str(value["name"])
            if "text" in value:
                return str(value["text"])
            return str(value)
        return str(value)

    async def get_project_and_requirement_from_feishu(
        self, person_names: Optional[List[str]] = None,
        date_start: Optional[str] = None, date_end: Optional[str] = None,
    ) -> Dict[str, Dict[str, str]]:
        """从飞书多维表格直接查询项目和试验需求编号

        根据飞书实际表结构：
        - 工程师表：项目用"填写人选择填写车型项目"/"查询填写人所在车型项目"/"所属项目"，
          试验单号用"根据填写人选择，生成试验单号"（公式字段）
        - 驾驶员表：项目用"填写人选择填写车型项目"/"查询填写人所在车型项目"/"所属项目"，
          试验需求编号用"试验需求编号"/"根据填写人选择，生成试验单号"

        Args:
            person_names: 可选，指定要查询的人员名单，不传则查所有
            date_start: 可选，起始日期 YYYY-MM-DD
            date_end: 可选，结束日期 YYYY-MM-DD

        Returns:
            Dict[(person_name, record_date_str)] -> {"project_name": ..., "requirement_code": ...}
        """
        cfg = EXPENSE_FEISHU_CONFIG
        result: Dict[str, Dict[str, str]] = {}

        try:
            token = await self.get_tenant_access_token(config=cfg)
        except Exception as e:
            logger.error(f"[Feishu] 获取token失败: {e}")
            return result

        # 分别查询工程师和驾驶员两张表
        for table_key, label in [
            ("ENGINEER", "工程师"),
            ("DRIVER", "驾驶员"),
        ]:
            table_id = cfg["TABLE_IDS"].get(table_key)
            if not table_id:
                continue

            try:
                records = await self._fetch_all_records(
                    token, table_id, config=cfg,
                    date_field="日期",
                    date_start=date_start, date_end=date_end,
                )
            except Exception as e:
                logger.warning(f"[Feishu] 查询{table_key}表失败: {e}")
                continue

            for record in records:
                fields = record.get("fields", {})

                # 提取日期
                raw_date = fields.get("日期")
                if raw_date is None:
                    continue
                try:
                    if isinstance(raw_date, (int, float)):
                        record_date = date.fromtimestamp(raw_date / 1000) if raw_date > 10000000000 else date.fromtimestamp(raw_date)
                    elif isinstance(raw_date, str):
                        record_date = date.fromisoformat(raw_date[:10])
                    else:
                        continue
                except Exception:
                    continue

                # 提取填写人（使用"填写人-人名"字段，工程师表没有"填写人"字段）
                person_name = self._extract_feishu_field_value(fields, "填写人-人名")
                if not person_name:
                    person_name = self._extract_feishu_field_value(fields, "填写人")
                if not person_name:
                    continue

                # 如果指定了人员名单，跳过不匹配的
                if person_names and person_name not in person_names:
                    continue

                date_key = str(record_date)
                cache_key = f"{person_name}:{date_key}"

                # 提取项目名称（优先使用公式字段"查询填写人所在车型项目"或"所属项目"）
                project_name = ""
                for proj_field in ["查询填写人所在车型项目", "所属项目", "所属项目信息-详细",
                                    "所属项目-详细", "填写人选择填写车型项目"]:
                    raw_proj = fields.get(proj_field)
                    if raw_proj is not None:
                        if isinstance(raw_proj, list) and len(raw_proj) > 0:
                            if isinstance(raw_proj[0], dict):
                                project_name = str(raw_proj[0].get("text", raw_proj[0].get("name", "")))
                            else:
                                project_name = str(raw_proj[0])
                        elif isinstance(raw_proj, dict):
                            project_name = str(raw_proj.get("text", raw_proj.get("name", "")))
                        else:
                            project_name = str(raw_proj)
                        if project_name:
                            break

                # 提取试验需求编号
                # 工程师表：用"根据填写人选择，生成试验单号"（公式字段）
                # 驾驶员表：用"试验需求编号"或"根据填写人选择，生成试验单号"
                requirement_code = ""
                for req_field in ["试验需求编号", "根据填写人选择，生成试验单号",
                                   "查询填写人项目需求编号"]:
                    raw_req = fields.get(req_field)
                    if raw_req is not None:
                        if isinstance(raw_req, list) and len(raw_req) > 0:
                            if isinstance(raw_req[0], dict):
                                requirement_code = str(raw_req[0].get("text", raw_req[0].get("name", "")))
                            else:
                                requirement_code = str(raw_req[0])
                        elif isinstance(raw_req, dict):
                            requirement_code = str(raw_req.get("text", raw_req.get("name", "")))
                        else:
                            requirement_code = str(raw_req)
                        if requirement_code:
                            break

                if cache_key not in result:
                    result[cache_key] = {}
                if project_name:
                    result[cache_key]["project_name"] = project_name
                if requirement_code:
                    result[cache_key]["requirement_code"] = requirement_code

        logger.info(f"[Feishu] 从飞书查询到 {len(result)} 条项目和试验需求记录")
        return result


feishu_sync_service = FeishuSyncService()
