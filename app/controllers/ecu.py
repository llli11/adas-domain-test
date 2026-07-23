import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, File, Form, HTTPException, UploadFile
from tortoise.expressions import Q
from tortoise.transactions import in_transaction

from app.models.ecu import ECUIgnore, EcuOperationLog, ReleaseInfo, ReleaseInfoHistory, ReleaseTargetInfo
from app.utils.get_ecu_full_info import parse_ecu_file

router = APIRouter()
logger = logging.getLogger(__name__)


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
                    modified_at=datetime.now(),
                )

                count = await ReleaseInfoHistory.filter(vin=vin).count()
                if count > 10:
                    keep_ids = await ReleaseInfoHistory.filter(vin=vin).order_by(
                        "-created_at"
                    ).limit(10).values_list("id", flat=True)
                    await ReleaseInfoHistory.filter(vin=vin).exclude(id__in=keep_ids).delete()

                existing.ecu_info = ecu_data
                existing.modified_at = datetime.now()
                await existing.save()
            else:
                existing.ecu_info = ecu_data
                await existing.save()
        else:
            await ReleaseInfo.create(vin=vin, ecu_info=ecu_data)

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
