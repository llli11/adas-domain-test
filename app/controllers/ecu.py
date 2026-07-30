import asyncio
import json
import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.ecu import ECUBaselineSelect, ECUIgnore, EcuOperationLog, ReleaseInfo, ReleaseInfoHistory, ReleaseTargetInfo
from app.settings.config import settings
from app.utils.get_ecu_full_info import parse_ecu_file

router = APIRouter()
logger = logging.getLogger(__name__)

PLAYW_TIMEOUT = 120  # 2 minutes


@router.get("/list", summary="获取ECU列表")
async def get_ecu_list(search: Optional[str] = None) -> Dict[str, Any]:
    try:
        q = ReleaseInfo.all().order_by("-updated_at")
        if search:
            q = ReleaseInfo.filter(
                Q(vin__contains=search) | Q(remark__contains=search)
            ).order_by("-updated_at")
        results = await q.values(
            "id", "vin", "ecu_info", "data_source", "remark", "modified_at", "created_at", "updated_at"
        )
        return {"code": 200, "data": results, "msg": "OK"}
    except Exception as e:
        logger.error(f"ECU list error: {e}")
        return {"code": 500, "data": [], "msg": f"数据库错误: {str(e)}"}


@router.get("/detail/{vin}", summary="获取ECU详情")
async def get_ecu_detail(vin: str) -> Dict[str, Any]:
    record = await ReleaseInfo.get_or_none(vin=vin)
    if not record:
        raise HTTPException(status_code=404, detail="未找到该VIN的记录")
    return {
        "code": 200,
        "data": {
            "id": record.id,
            "vin": record.vin,
            "ecu_info": record.ecu_info,
            "data_source": record.data_source,
            "remark": record.remark,
            "modified_at": record.modified_at,
            "created_at": record.created_at,
            "updated_at": record.updated_at,
        },
        "msg": "OK",
    }


@router.post("/update", summary="更新ECU信息")
async def update_ecu_info(vin: str = Form(...), file: UploadFile = File(...)) -> Dict[str, Any]:
    file_content = await file.read()
    ecu_data = parse_ecu_file(file_content)

    if "error" in ecu_data:
        raise HTTPException(status_code=400, detail=ecu_data["error"])

    html_date_str = ecu_data.pop("_html_date", None)
    html_date = datetime.strptime(html_date_str, "%Y-%m-%d %H:%M:%S") if html_date_str else datetime.now()

    existing = await ReleaseInfo.get_or_none(vin=vin)

    has_changed = False
    if existing and existing.ecu_info is not None:
        has_changed = existing.ecu_info != ecu_data

    async with in_transaction("mysql"):
        if existing:
            if has_changed:
                await ReleaseInfoHistory.create(
                    vin=vin,
                    ecu_info=existing.ecu_info,
                    data_source=existing.data_source,
                    modified_at=html_date,
                )

                count = await ReleaseInfoHistory.filter(vin=vin).count()
                if count > 10:
                    keep_ids = await ReleaseInfoHistory.filter(vin=vin).order_by(
                        "-created_at"
                    ).limit(10).values_list("id", flat=True)
                    await ReleaseInfoHistory.filter(vin=vin).exclude(id__in=keep_ids).delete()

                existing.ecu_info = ecu_data
                existing.modified_at = html_date
                existing.updated_at = html_date
                await existing.save()
            else:
                existing.ecu_info = ecu_data
                await existing.save()
        else:
            await ReleaseInfo.create(
                vin=vin, ecu_info=ecu_data,
                created_at=html_date, updated_at=html_date,
            )

    return {"code": 200, "data": {"message": "更新成功", "vin": vin}, "msg": "OK"}


@router.delete("/delete/{vin}", summary="删除ECU信息")
async def delete_ecu_info(vin: str) -> Dict[str, Any]:
    await ReleaseInfo.filter(vin=vin).delete()
    await ReleaseInfoHistory.filter(vin=vin).delete()
    await ECUIgnore.filter(vin=vin).delete()
    return {"code": 200, "data": {"message": "删除成功"}, "msg": "OK"}


@router.get("/history/{vin}", summary="获取历史记录列表")
async def get_ecu_history(vin: str) -> Dict[str, Any]:
    results = await ReleaseInfoHistory.filter(vin=vin).order_by("-created_at").values("id", "created_at")
    return {"code": 200, "data": results, "msg": "OK"}


@router.get("/history/{vin}/{history_id}", summary="获取历史版本详情")
async def get_ecu_history_detail(vin: str, history_id: int) -> Dict[str, Any]:
    record = await ReleaseInfoHistory.get_or_none(id=history_id, vin=vin)
    if not record:
        raise HTTPException(status_code=404, detail="未找到该历史记录")
    return {
        "code": 200,
        "data": {
            "id": record.id,
            "vin": record.vin,
            "ecu_info": record.ecu_info,
            "data_source": record.data_source,
            "created_at": record.created_at,
        },
        "msg": "OK",
    }


@router.post("/restore/{vin}/{history_id}", summary="恢复历史版本")
async def restore_ecu_version(vin: str, history_id: int) -> Dict[str, Any]:
    logger.info(f"Restore request: vin={vin}, history_id={history_id}")
    history_record = await ReleaseInfoHistory.get_or_none(id=history_id, vin=vin)
    logger.info(f"History record: {history_record}")

    if not history_record:
        raise HTTPException(status_code=404, detail="未找到该历史记录")

    current = await ReleaseInfo.get_or_none(vin=vin)

    async with in_transaction("mysql"):
        if current and current.ecu_info is not None:
            if current.ecu_info != history_record.ecu_info:
                await ReleaseInfoHistory.create(
                    vin=vin,
                    ecu_info=current.ecu_info,
                    data_source=current.data_source or "vdc_export",
                    modified_at=datetime.now(),
                    updated_at=current.updated_at,
                )

                count = await ReleaseInfoHistory.filter(vin=vin).count()
                if count > 10:
                    keep_ids = await ReleaseInfoHistory.filter(vin=vin).order_by(
                        "-created_at"
                    ).limit(10).values_list("id", flat=True)
                    await ReleaseInfoHistory.filter(vin=vin).exclude(id__in=keep_ids).delete()

        if current:
            current.ecu_info = history_record.ecu_info
            current.modified_at = datetime.now()
            await current.save()
        else:
            await ReleaseInfo.create(
                vin=vin,
                ecu_info=history_record.ecu_info,
                data_source=history_record.data_source,
            )

    return {"code": 200, "data": {"message": "恢复成功", "vin": vin}, "msg": "OK"}


@router.post("/remark/{vin}", summary="更新备注信息")
async def update_remark(vin: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    remark = body.get("remark", "")
    record = await ReleaseInfo.get_or_none(vin=vin)
    if record:
        record.remark = remark
        await record.save()
    return {"code": 200, "data": {"message": "备注更新成功"}, "msg": "OK"}


@router.post("/ignore/{vin}", summary="忽略ECU")
async def ignore_ecu(vin: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    ecu_name = body.get("ecu_name")
    if not ecu_name:
        raise HTTPException(status_code=400, detail="ecu_name is required")
    await ECUIgnore.get_or_create(vin=vin, ecu_name=ecu_name)
    return {"code": 200, "data": {"message": "忽略成功"}, "msg": "OK"}


@router.post("/ignore/{vin}/restore", summary="恢复忽略的ECU")
async def restore_ignore_ecu(vin: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    ecu_name = body.get("ecu_name")
    if not ecu_name:
        raise HTTPException(status_code=400, detail="ecu_name is required")
    await ECUIgnore.filter(vin=vin, ecu_name=ecu_name).delete()
    return {"code": 200, "data": {"message": "恢复成功"}, "msg": "OK"}


@router.get("/ignore/{vin}", summary="获取忽略的ECU列表")
async def get_ignore_list(vin: str) -> Dict[str, Any]:
    records = await ECUIgnore.filter(vin=vin).values("ecu_name", "created_at")
    return {"code": 200, "data": records, "msg": "OK"}


@router.post("/ignore/{vin}/reset", summary="重置所有忽略的ECU")
async def reset_ignore_list(vin: str) -> Dict[str, Any]:
    await ECUIgnore.filter(vin=vin).delete()
    return {"code": 200, "data": {"message": "重置成功"}, "msg": "OK"}


@router.post("/baseline-select/{vin}", summary="选定基线版本")
async def select_baseline(vin: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    ecu_name = body.get("ecu_name")
    baseline_name = body.get("baseline_name")
    if not ecu_name or not baseline_name:
        raise HTTPException(status_code=400, detail="ecu_name and baseline_name are required")
    existing = await ECUBaselineSelect.get_or_none(vin=vin, ecu_name=ecu_name)
    if existing:
        existing.selected_baseline_name = baseline_name
        await existing.save()
    else:
        await ECUBaselineSelect.create(vin=vin, ecu_name=ecu_name, selected_baseline_name=baseline_name)
    return {"code": 200, "data": {"message": "选定成功"}, "msg": "OK"}


@router.post("/baseline-select/{vin}/deselect", summary="取消选定基线版本")
async def deselect_baseline(vin: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    ecu_name = body.get("ecu_name")
    if not ecu_name:
        raise HTTPException(status_code=400, detail="ecu_name is required")
    await ECUBaselineSelect.filter(vin=vin, ecu_name=ecu_name).delete()
    return {"code": 200, "data": {"message": "取消选定成功"}, "msg": "OK"}


@router.get("/baseline-select/{vin}", summary="获取基线选定列表")
async def get_baseline_select_list(vin: str) -> Dict[str, Any]:
    records = await ECUBaselineSelect.filter(vin=vin).values("ecu_name", "selected_baseline_name", "created_at")
    return {"code": 200, "data": records, "msg": "OK"}


@router.post("/baseline-select/{vin}/reset", summary="重置所有基线选定")
async def reset_baseline_select_list(vin: str) -> Dict[str, Any]:
    await ECUBaselineSelect.filter(vin=vin).delete()
    return {"code": 200, "data": {"message": "重置成功"}, "msg": "OK"}


@router.post("/log", summary="记录操作日志")
async def add_operation_log(body: Dict[str, Any]) -> Dict[str, Any]:
    await EcuOperationLog.create(
        operation_type=body.get("operation_type"),
        target_vin=body.get("target_vin"),
        target_name=body.get("target_name"),
        operator=body.get("operator"),
    )
    return {"code": 200, "data": {"message": "记录成功"}, "msg": "OK"}


@router.get("/log/stats", summary="获取操作统计数据")
async def get_operation_stats() -> Dict[str, Any]:
    today = date.today()
    first_day_of_month = today.replace(day=1)
    start_of_today = datetime(today.year, today.month, today.day)

    vehicle_total = await ReleaseInfo.all().count()
    vehicle_today = await ReleaseInfo.filter(updated_at__gte=start_of_today).count()
    vehicle_month = await ReleaseInfo.filter(updated_at__gte=first_day_of_month).count()

    target_total = await ReleaseTargetInfo.all().count()
    target_today = await ReleaseTargetInfo.filter(updated_at__gte=start_of_today).count()
    target_month = await ReleaseTargetInfo.filter(updated_at__gte=first_day_of_month).count()

    return {
        "code": 200,
        "data": {
            "vehicle_total": vehicle_total,
            "vehicle_today": vehicle_today,
            "vehicle_month": vehicle_month,
            "target_total": target_total,
            "target_today": target_today,
            "target_month": target_month,
        },
        "msg": "OK",
    }


@router.get("/log/chart", summary="获取每日操作次数图表数据")
async def get_operation_chart(days: int = 30) -> Dict[str, Any]:
    end_date = date.today()
    start_date = end_date - timedelta(days=days - 1)

    operation_types = ["更新车辆", "对比基线", "删除车辆", "新建基线", "更新基线", "删除基线"]

    result = []
    for i in range(days):
        current_date = start_date + timedelta(days=i)
        day_start = datetime(current_date.year, current_date.month, current_date.day)
        day_end = day_start + timedelta(days=1)
        day_str = current_date.strftime("%Y-%m-%d")
        day_data: Dict[str, Any] = {"date": day_str}
        for op_type in operation_types:
            count = await EcuOperationLog.filter(
                operation_type=op_type, created_at__gte=day_start, created_at__lt=day_end
            ).count()
            day_data[op_type] = count
        result.append(day_data)

    return {"code": 200, "data": result, "msg": "OK"}


@router.get("/log/list", summary="获取操作日志列表")
async def get_operation_log_list(
    page: int = 1,
    page_size: int = 20,
    operation_type: Optional[str] = None,
    operator: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    filters = Q()
    if operation_type:
        filters &= Q(operation_type=operation_type)
    if operator:
        filters &= Q(operator__contains=operator)
    if start_date:
        dt = datetime.strptime(start_date, "%Y-%m-%d")
        filters &= Q(created_at__gte=dt)
    if end_date:
        dt = datetime.strptime(end_date, "%Y-%m-%d") + timedelta(days=1)
        filters &= Q(created_at__lt=dt)

    total = await EcuOperationLog.filter(filters).count()
    offset = (page - 1) * page_size
    results = (
        await EcuOperationLog.filter(filters)
        .order_by("-created_at")
        .offset(offset)
        .limit(page_size)
        .values("id", "operation_type", "target_vin", "target_name", "operator", "created_at")
    )

    return {"code": 200, "data": results, "msg": "OK", "total": total, "page": page, "page_size": page_size}


@router.get("/log/operators", summary="获取所有操作账号")
async def get_log_operators() -> Dict[str, Any]:
    rows = await EcuOperationLog.exclude(operator__isnull=True).order_by("operator").values("operator")
    seen = set()
    operators = []
    for r in rows:
        op = r.get("operator")
        if op and op not in seen:
            seen.add(op)
            operators.append(op)
    return {"code": 200, "data": operators, "msg": "OK"}


def _convert_online_ecu_data(ecu_data: Dict[str, Any]) -> Dict[str, Any]:
    """将 playw 在线接口返回的 ECU 数据转换为 DID-based 格式（与 HTML 上传格式一致）"""
    raw_data = dict(ecu_data)
    did_map = raw_data.pop("_did_map", {})

    # 反向映射: description → DID
    desc_to_did = {v: k for k, v in did_map.items()}

    result = {}
    for ecu_name, attrs in raw_data.items():
        converted = {}
        ota_update_t = None
        for key, value in attrs.items():
            if key == "OTA_UPDATE_T":
                ota_update_t = value
                continue
            did = desc_to_did.get(key, key)
            converted[did] = value
        if ota_update_t:
            converted["OTA_UPDATE_T"] = ota_update_t
        result[ecu_name] = converted

    result["_did_map"] = did_map
    return result


@router.post("/online-update/{vin}", summary="在线获取ECU更新信息")
async def online_update_ecu(vin: str) -> Dict[str, Any]:
    """调用 playw 接口获取该 VIN 的在线 ECU 版本信息，并与数据库中的 updated_at 对比"""
    record = await ReleaseInfo.get_or_none(vin=vin)
    if not record:
        raise HTTPException(status_code=404, detail="未找到该VIN的记录")

    try:
        playw_url = f"http://{settings.PLAYW_HOST}:{settings.PLAYW_PORT}/run"
        request_body = json.dumps({"script": "ota_ecu_update", "params": {"vin": vin}})
        proc = await asyncio.create_subprocess_exec(
            "curl", "-sS", "--connect-timeout", str(PLAYW_TIMEOUT), "-X", "POST", playw_url,
            "-H", "Content-Type: application/json",
            "-d", request_body,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(
            proc.communicate(), timeout=PLAYW_TIMEOUT
        )
        if proc.returncode != 0:
            err_msg = stderr.decode("utf-8", errors="replace").strip() or "curl 返回非零退出码"
            raise Exception(err_msg)
        api_result = json.loads(stdout.decode("utf-8"))
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="在线更新接口超时（2分钟）")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Online update API error for VIN {vin}: {e}")
        raise HTTPException(status_code=502, detail=f"在线更新接口调用失败: {str(e)}")

    if not api_result.get("ok") or not api_result.get("data", {}).get("success"):
        error_msg = api_result.get("error") or "接口返回失败"
        raise HTTPException(status_code=502, detail=error_msg)

    ecu_data_raw = api_result["data"].get("ecu_data", {})
    if not ecu_data_raw:
        raise HTTPException(status_code=502, detail="接口未返回ECU数据")

    # 转换为 DID-based 格式
    converted_data = _convert_online_ecu_data(ecu_data_raw)

    # 对比每个 ECU 的 OTA_UPDATE_T 与数据库的 updated_at
    db_updated_at = record.updated_at
    db_ecu_info = record.ecu_info or {}
    did_map = converted_data.get("_did_map", {})
    sw_did = None
    for did, desc in did_map.items():
        if desc == "VOYAH SoftwareVersion":
            sw_did = did
            break

    updated_ecus = []
    skipped_ecus = []
    all_ota_times = []

    for ecu_name, attrs in converted_data.items():
        if ecu_name == "_did_map":
            continue
        ota_time_str = attrs.pop("OTA_UPDATE_T", None)
        if ota_time_str:
            try:
                ota_time = datetime.fromisoformat(ota_time_str)
                if ota_time.tzinfo is not None:
                    ota_time = ota_time.replace(tzinfo=None)
            except (ValueError, TypeError):
                ota_time = None
        else:
            ota_time = None

        current_db_ecu = db_ecu_info.get(ecu_name, {}) or {}
        current_version = current_db_ecu.get(sw_did, "") if sw_did else ""
        ota_version = attrs.get(sw_did, "") if sw_did else ""

        if ota_time:
            all_ota_times.append(ota_time)
            if db_updated_at and ota_time.replace(tzinfo=None) <= db_updated_at.replace(tzinfo=None):
                skipped_ecus.append({
                    "ecu_name": ecu_name,
                    "current_db_time": db_updated_at.replace(tzinfo=None, microsecond=0).isoformat() if db_updated_at else None,
                    "current_version": current_version,
                    "ota_update_time": ota_time_str,
                    "ota_version": ota_version,
                })
            else:
                updated_ecus.append({
                    "ecu_name": ecu_name,
                    "current_db_time": db_updated_at.replace(tzinfo=None, microsecond=0).isoformat() if db_updated_at else None,
                    "current_version": current_version,
                    "ota_update_time": ota_time_str,
                    "ota_version": ota_version,
                    "new_versions": attrs,
                })
        else:
            skipped_ecus.append({
                "ecu_name": ecu_name,
                "current_db_time": db_updated_at.replace(tzinfo=None, microsecond=0).isoformat() if db_updated_at else None,
                "current_version": current_version,
                "ota_update_time": None,
                "ota_version": ota_version,
            })

    latest_ota_time = max(all_ota_times).isoformat() if all_ota_times else None

    return {
        "code": 200,
        "data": {
            "vin": vin,
            "updated_ecus": updated_ecus,
            "skipped_ecus": skipped_ecus,
            "total_updated": len(updated_ecus),
            "total_skipped": len(skipped_ecus),
            "latest_ota_time": latest_ota_time,
            "converted_ecu_data": converted_data,
            "current_data_source": record.data_source,
            "current_updated_at": db_updated_at.replace(tzinfo=None, microsecond=0).isoformat() if db_updated_at else None,
        },
        "msg": "OK",
    }


@router.post("/online-update/confirm/{vin}", summary="确认在线更新ECU信息到数据库")
async def confirm_online_update(vin: str, body: Dict[str, Any] = Body(...)) -> Dict[str, Any]:
    """确认将在线获取的 ECU 版本信息写入数据库"""
    record = await ReleaseInfo.get_or_none(vin=vin)
    if not record:
        raise HTTPException(status_code=404, detail="未找到该VIN的记录")

    ecu_data = body.get("ecu_data", {})
    latest_ota_time_str = body.get("latest_ota_time")

    if not ecu_data:
        raise HTTPException(status_code=400, detail="缺少 ecu_data")

    existing_ecu_info = record.ecu_info or {}
    db_updated_at = record.updated_at

    # 对比并更新每个 ECU
    new_ecu_info = dict(existing_ecu_info)
    # 合并 _did_map（优先使用新的）
    if "_did_map" in ecu_data:
        existing_did_map = existing_ecu_info.get("_did_map", {})
        merged_did_map = dict(existing_did_map)
        merged_did_map.update(ecu_data["_did_map"])
        new_ecu_info["_did_map"] = merged_did_map

    has_any_update = False
    for ecu_name, attrs in ecu_data.items():
        if ecu_name == "_did_map":
            continue
        ota_time_str = attrs.pop("OTA_UPDATE_T", None) if isinstance(attrs, dict) else None
        if ota_time_str:
            try:
                ota_time = datetime.fromisoformat(ota_time_str)
                if ota_time.tzinfo is not None:
                    ota_time = ota_time.replace(tzinfo=None)
            except (ValueError, TypeError):
                ota_time = None
        else:
            ota_time = None

        version_data = {k: v for k, v in (attrs.items() if isinstance(attrs, dict) else {})}

        if ota_time and (not db_updated_at or ota_time.replace(tzinfo=None) > db_updated_at.replace(tzinfo=None)):
            new_ecu_info[ecu_name] = version_data
            has_any_update = True

    # 解析最新的 OTA 时间
    if latest_ota_time_str:
        try:
            latest_ota_time = datetime.fromisoformat(latest_ota_time_str)
        except (ValueError, TypeError):
            latest_ota_time = datetime.now()
    else:
        latest_ota_time = datetime.now()

    async with in_transaction("mysql"):
        if record.ecu_info is not None:
            await ReleaseInfoHistory.create(
                vin=vin,
                ecu_info=record.ecu_info,
                data_source=record.data_source or "vdc_export",
                modified_at=datetime.now(),
                updated_at=record.updated_at,
            )

            count = await ReleaseInfoHistory.filter(vin=vin).count()
            if count > 10:
                keep_ids = await ReleaseInfoHistory.filter(vin=vin).order_by(
                    "-created_at"
                ).limit(10).values_list("id", flat=True)
                await ReleaseInfoHistory.filter(vin=vin).exclude(id__in=keep_ids).delete()

        # 使用 filter().update() 绕过 auto_now=True 对 updated_at 的覆盖
        await ReleaseInfo.filter(vin=vin).update(
            ecu_info=new_ecu_info,
            data_source="ota_online",
            updated_at=latest_ota_time,
            modified_at=datetime.now(),
        )

    return {
        "code": 200,
        "data": {
            "message": "在线更新成功",
            "vin": vin,
            "updated_ecu_count": len([e for e in ecu_data if e != "_did_map"]),
            "new_data_source": "ota_online",
            "new_updated_at": latest_ota_time.isoformat() if latest_ota_time else None,
        },
        "msg": "OK",
    }
