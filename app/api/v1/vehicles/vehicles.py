"""车辆管理 - API路由"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Body, File, Query, UploadFile

from app.controllers.vehicle import vehicle_controller
from app.core.ctx import CTX_USER_ID
from app.log import logger
from app.models.user_feishu_config import UserFeishuConfig
from app.schemas.base import Success, SuccessExtra
from app.schemas.vehicles import (
    VehicleCreate,
    VehicleUpdate,
    VehicleUpsert,
)
from app.services.csv_import import generate_csv_template, import_csv_to_db
from app.services.feishu_sync import DEFAULT_FEISHU_CONFIG, FeishuSyncService, feishu_sync_service

router = APIRouter()


# ==================== 基础CRUD ====================


@router.get("/list", summary="车辆列表（分页+筛选）")
async def list_vehicles(
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
    task_status: Optional[str] = Query(None, description="任务状态"),
    vehicle_model: Optional[str] = Query(None, description="车型项目"),
    borrower: Optional[str] = Query(None, description="借用人"),
    power_type: Optional[str] = Query(None, description="动力类型"),
    travel_status: Optional[str] = Query(None, description="出差状态"),
    test_city: Optional[str] = Query(None, description="试验城市"),
    vn: Optional[str] = Query(None, description="车辆VN"),
    vehicle_code: Optional[str] = Query(None, description="车辆编号"),
    data_source: Optional[str] = Query(None, description="数据来源"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    dept_l1: Optional[str] = Query(None, description="一级部门"),
    dept_l2: Optional[str] = Query(None, description="二级部门"),
    # 通用字段过滤（字段名+值下拉选择）
    field1: Optional[str] = Query(None, description="过滤字段1"),
    value1: Optional[str] = Query(None, description="过滤值1"),
    field2: Optional[str] = Query(None, description="过滤字段2"),
    value2: Optional[str] = Query(None, description="过滤值2"),
    field3: Optional[str] = Query(None, description="过滤字段3"),
    value3: Optional[str] = Query(None, description="过滤值3"),
):
    total, objs = await vehicle_controller.list_with_filter(
        page=page,
        page_size=page_size,
        task_status=task_status,
        vehicle_model=vehicle_model,
        borrower=borrower,
        power_type=power_type,
        travel_status=travel_status,
        test_city=test_city,
        vn=vn,
        vehicle_code=vehicle_code,
        data_source=data_source,
        keyword=keyword,
        dept_l1=dept_l1, dept_l2=dept_l2,
        field1=field1, value1=value1,
        field2=field2, value2=value2,
        field3=field3, value3=value3,
    )
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/get", summary="查看车辆详情")
async def get_vehicle(
    vehicle_id: int = Query(..., description="车辆ID"),
):
    obj = await vehicle_controller.get(id=vehicle_id)
    data = await obj.to_dict()
    return Success(data=data)


@router.post("/create", summary="新增车辆")
async def create_vehicle(
    vehicle_in: VehicleCreate,
):
    await vehicle_controller.create_vehicle(vehicle_in)
    return Success(msg="新增成功")


@router.post("/update", summary="更新车辆")
async def update_vehicle(
    vehicle_in: VehicleUpdate,
):
    await vehicle_controller.update_vehicle(id=vehicle_in.id, obj_in=vehicle_in)
    return Success(msg="更新成功")


@router.delete("/delete", summary="删除车辆")
async def delete_vehicle(
    vehicle_id: int = Query(..., description="车辆ID"),
):
    await vehicle_controller.delete_vehicle(id=vehicle_id)
    return Success(msg="删除成功")


@router.delete("/batch-delete", summary="批量删除车辆")
async def batch_delete_vehicles(
    ids: list[int] = Body(..., description="车辆ID列表", embed=True),
):
    count = await vehicle_controller.batch_delete(ids=ids)
    return Success(msg=f"批量删除成功，共删除 {count} 条", data={"deleted": count})


@router.get("/field-values", summary="获取字段去重值（下拉联想用）")
async def get_field_values(
    field: str = Query(..., description="字段名（如 vn, borrower, test_city）"),
    keyword: Optional[str] = Query(None, description="模糊过滤关键字"),
):
    values = await vehicle_controller.get_field_distinct_values(
        field_name=field, keyword=keyword, limit=50
    )
    return Success(data={"field": field, "values": values})


# ==================== Upsert 批量导入 ====================


@router.post("/upsert", summary="按VN去重导入（批量/单条）")
async def upsert_vehicle(
    vehicle_in: VehicleUpsert | list[VehicleUpsert],
):
    """支持单条JSON对象或JSON数组批量导入"""
    items = vehicle_in if isinstance(vehicle_in, list) else [vehicle_in]
    created = 0
    updated = 0
    errors = []

    for item in items:
        try:
            existing = await vehicle_controller.get_by_vn(item.vn)
            await vehicle_controller.upsert_by_vn(VehicleCreate(**item.model_dump()))
            if existing:
                updated += 1
            else:
                created += 1
        except Exception as e:
            errors.append(f"VN={item.vn}: {str(e)}")
            logger.error(f"[Vehicle Upsert] 导入失败 VN={item.vn}: {e}")

    return Success(
        data={
            "created": created,
            "updated": updated,
            "errors": errors,
        },
        msg=f"导入完成: 新增{created}条, 更新{updated}条",
    )


# ==================== 到期提醒 ====================


@router.get("/alerts/expiring", summary="到期提醒")
async def get_expiring_vehicles(
    type: str = Query("temp_plate", description="提醒类型: temp_plate | borrow"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(50, description="每页数量"),
):
    total, objs = await vehicle_controller.get_expiring_vehicles(
        alert_type=type,
        page=page,
        page_size=page_size,
    )
    today = date.today()
    data = []
    for obj in objs:
        item = await obj.to_dict()
        expire_field = "temp_plate_expire_date" if type == "temp_plate" else "borrow_expire_date"
        expire_date_val = getattr(obj, expire_field, None)
        if expire_date_val:
            item["days_remaining"] = (expire_date_val - today).days
        else:
            item["days_remaining"] = None
        data.append(item)

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


# ==================== 状态地图数据 ====================


@router.get("/status-map", summary="车辆任务状态地图数据")
async def get_status_map():
    """返回带位置信息且任务状态不为空的车辆，用于地图展示"""
    objs = await vehicle_controller.get_status_map_data()
    data = [await obj.to_dict() for obj in objs]

    # 统计各状态数量
    status_stats = await vehicle_controller.get_vehicles_by_task_status()

    return Success(
        data={
            "vehicles": data,
            "stats": status_stats,
        }
    )


# ==================== 飞书同步（数据源1 + 数据源2） ====================


# 内存中暂存最近一次同步结果，供前端轮询
_last_sync_result: dict = {"success": False, "message": "尚未同步", "running": False}


@router.post("/sync/feishu", summary="数据源1：从预置飞书表格同步")
async def sync_from_feishu(background_tasks: BackgroundTasks):
    """从预置的飞书多维表格（试验车辆任务状态小程序）同步车辆数据（后台异步执行）"""
    global _last_sync_result
    if _last_sync_result.get("running"):
        return Success(data=_last_sync_result, msg="同步正在进行中，请稍后查看结果")

    _last_sync_result = {"success": False, "message": "同步已启动，正在后台执行…", "running": True}

    async def _do_sync():
        global _last_sync_result
        try:
            logger.info("[Feishu Sync] 后台同步开始...")
            result = await feishu_sync_service.sync_vehicles_from_feishu()
            logger.info(f"[Feishu Sync] 后台同步结果: {result}")
            _last_sync_result = {**result, "running": False}
        except Exception as e:
            logger.error(f"[Feishu Sync] 后台同步异常: {e}")
            _last_sync_result = {"success": False, "message": f"同步异常: {str(e)}", "running": False}

    background_tasks.add_task(_do_sync)
    return Success(data=_last_sync_result, msg="同步任务已提交")


@router.get("/sync/feishu/status", summary="查询同步状态")
async def sync_status():
    """获取最近一次同步结果"""
    return Success(data=_last_sync_result, msg=_last_sync_result.get("message", ""))


@router.get("/reverse-geocode", summary="逆地理编码（经纬度转地址）")
async def reverse_geocode(
    lat: float = Query(..., description="纬度"),
    lng: float = Query(..., description="经度"),
):
    """通过 Nominatim 将经纬度转为行政地址"""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://nominatim.openstreetmap.org/reverse",
                params={
                    "format": "json", "lat": lat, "lon": lng,
                    "zoom": 18, "addressdetails": 1, "accept-language": "zh",
                },
                headers={"User-Agent": "VueFastAPIAdmin/1.0"},
            )
            data = resp.json()
            addr = data.get("display_name", "")
            return Success(data={"address": addr, "lat": lat, "lng": lng})
    except Exception as e:
        logger.warning(f"[ReverseGeocode] 失败: {e}")
        return Success(data={"address": "", "lat": lat, "lng": lng})


@router.post("/sync/feishu/config/save", summary="数据源2：保存用户飞书配置并自动同步")
async def save_feishu_config(
    base_id: str = Body(..., description="用户飞书多维表格的Base ID"),
    table_id: str = Body(..., description="用户飞书多维表格的Table ID"),
):
    """数据源2：保存用户自定义飞书多维表格配置到数据库，并自动触发同步
    
    授权说明：用户需要在飞书多维表格中，点击右上角"···"→"更多"→"添加文档应用"，
    搜索"试验车辆任务状态小程序"并添加，确保应用有读取多维表格的权限
    """
    try:
        user_id = CTX_USER_ID.get()
        logger.info(f"[Feishu Config] 用户 {user_id} 保存配置: BASE_ID={base_id}, TABLE_ID={table_id}")

        # 保存到数据库（按user_id去重）
        config, created = await UserFeishuConfig.update_or_create(
            defaults={"base_id": base_id, "table_id": table_id},
            user_id=user_id,
        )
        logger.info(f"[Feishu Config] 配置{'创建' if created else '更新'}成功")

        # 自动触发同步
        logger.info(f"[Feishu Sync] 数据源2自动同步开始 BASE_ID={base_id}, TABLE_ID={table_id}")
        custom_config = {
            "APP_ID": DEFAULT_FEISHU_CONFIG["APP_ID"],
            "APP_SECRET": DEFAULT_FEISHU_CONFIG["APP_SECRET"],
            "BASE_ID": base_id,
            "TABLE_IDS": {
                "VEHICLES": table_id,
                "DAILY_TASKS": DEFAULT_FEISHU_CONFIG["TABLE_IDS"]["DAILY_TASKS"],
            },
        }
        custom_service = FeishuSyncService(config=custom_config)
        result = await custom_service.sync_vehicles_from_feishu(table_id=table_id)
        logger.info(f"[Feishu Sync] 数据源2同步结果: {result}")
        return Success(
            data={
                "config_saved": True,
                "sync_result": result,
            },
            msg=f"配置保存成功，{result.get('message', '同步完成')}",
        )
    except Exception as e:
        logger.error(f"[Feishu Config] 保存或同步异常: {e}")
        return Success(code=500, msg=f"保存或同步失败: {str(e)}", data={"success": False})


@router.post("/sync/feishu/config", summary="数据源2：用户自定义飞书表格同步")
async def config_and_sync_feishu(
    base_id: str = Body(..., description="用户飞书多维表格的Base ID"),
    table_id: str = Body(..., description="用户飞书多维表格的Table ID"),
):
    """数据源2：用户配置自己的飞书多维表格并同步（不保存配置，仅触发同步）"""
    try:
        logger.info(f"[Feishu Sync] 数据源2同步开始 BASE_ID={base_id}, TABLE_ID={table_id}")
        custom_config = {
            "APP_ID": DEFAULT_FEISHU_CONFIG["APP_ID"],
            "APP_SECRET": DEFAULT_FEISHU_CONFIG["APP_SECRET"],
            "BASE_ID": base_id,
            "TABLE_IDS": {
                "VEHICLES": table_id,
                "DAILY_TASKS": DEFAULT_FEISHU_CONFIG["TABLE_IDS"]["DAILY_TASKS"],
            },
        }
        custom_service = FeishuSyncService(config=custom_config)
        result = await custom_service.sync_vehicles_from_feishu(table_id=table_id)
        logger.info(f"[Feishu Sync] 数据源2同步结果: {result}")
        return Success(data=result, msg=result.get("message", ""))
    except Exception as e:
        logger.error(f"[Feishu Sync] 数据源2同步异常: {e}")
        return Success(code=500, msg=f"同步异常: {str(e)}", data={"success": False})


@router.get("/sync/feishu/config/get", summary="获取当前用户保存的飞书配置")
async def get_feishu_config():
    """获取当前登录用户保存的飞书多维表格配置"""
    try:
        user_id = CTX_USER_ID.get()
        config = await UserFeishuConfig.filter(user_id=user_id).first()
        if config:
            return Success(data={
                "base_id": config.base_id,
                "table_id": config.table_id,
            }, msg="获取配置成功")
        else:
            return Success(data=None, msg="用户未保存飞书配置")
    except Exception as e:
        logger.error(f"[Feishu Config] 获取配置异常: {e}")
        return Success(code=500, msg=f"获取配置失败: {str(e)}", data=None)


@router.get("/sync/feishu/health", summary="飞书连接健康检查")
async def feishu_health_check():
    """检查飞书API连接是否正常"""
    try:
        token = await feishu_sync_service.get_tenant_access_token()
        return Success(data={"connected": True, "token_valid": True}, msg="飞书连接正常")
    except Exception as e:
        return Success(data={"connected": False, "token_valid": False, "error": str(e)}, msg=f"飞书连接失败: {str(e)}")


# ==================== CSV导入（数据源3） ====================


@router.post("/import/csv", summary="数据源3：CSV文件导入")
async def import_csv(
    file: UploadFile = File(..., description="CSV文件"),
):
    """上传CSV文件导入车辆数据（数据源3）
    支持UTF-8-BOM和GBK编码，根据VN自动去重更新
    """
    try:
        content = await file.read()
        try:
            csv_text = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            try:
                csv_text = content.decode("gbk")
            except Exception as e:
                logger.error(f"[CSV Import] 文件编码错误: {e}")
                return Success(code=400, msg="文件编码错误，请使用UTF-8或GBK编码保存", data={"success": False})

        result = await import_csv_to_db(csv_text)
        return Success(data=result, msg=result.get("message", ""))
    except Exception as e:
        logger.error(f"[CSV Import] 导入异常: {e}")
        return Success(code=500, msg=f"导入异常: {str(e)}", data={"success": False})


@router.get("/import/template", summary="下载CSV导入模板")
async def download_csv_template():
    """下载CSV模板文件（UTF-8 BOM 编码，Excel 直接打开不乱码）"""
    from fastapi.responses import Response

    template_content = generate_csv_template()
    # 使用 UTF-8 BOM 编码为 bytes，确保 Excel 正确识别中文
    content_bytes = template_content.encode("utf-8-sig")
    return Response(
        content=content_bytes,
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename*=UTF-8''vehicle_import_template.csv",
        },
    )
