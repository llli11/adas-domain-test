"""车辆管理 - API路由"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Body, File, Query, UploadFile

from app.controllers.vehicle import vehicle_controller
from app.core.ctx import CTX_USER_ID
from app.log import logger
from app.models.user_feishu_config import UserFeishuConfig
from app.schemas.base import Success, SuccessExtra
from app.schemas.vehicles import (
    FeishuSyncConfig,
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
            if existing:
                updated += 1
            else:
                created += 1
            await vehicle_controller.upsert_by_vn(VehicleCreate(**item.model_dump()))
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


@router.post("/sync/feishu", summary="数据源1：从预置飞书表格同步")
async def sync_from_feishu():
    """从预置的飞书多维表格（试验车辆任务状态小程序）同步车辆数据
    使用默认配置的 APP_ID/APP_SECRET/BASE_ID/TABLE_ID
    """
    try:
        logger.info("[Feishu Sync] 数据源1同步开始...")
        result = await feishu_sync_service.sync_vehicles_from_feishu()
        logger.info(f"[Feishu Sync] 数据源1同步结果: {result}")
        return Success(data=result, msg=result.get("message", ""))
    except Exception as e:
        logger.error(f"[Feishu Sync API] 同步异常: {e}")
        return Success(code=500, msg=f"同步异常: {str(e)}", data={"success": False})


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
        await feishu_sync_service.http_client.aclose()
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
