from fastapi import APIRouter, Query
from typing import Optional, List
from tortoise.expressions import Q
from app.schemas.base import Success, SuccessExtra, Fail
from pydantic import BaseModel
from app.controllers.mapway import mapway_controller, route_detail_controller, route_detail_self_developed_controller
from app.schemas.mapway import MapwayCreate, MapwayUpdate, RouteDetailCreate, RouteDetailUpdate, \
    RouteDetailSelfDevelopedCreate, RouteDetailSelfDevelopedUpdate

router = APIRouter(tags=["测试线路管理"])

@router.get("/list", summary="查看区域列表")
async def list_mapway(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    area: str = Query("", description="地点名称（模糊搜索）"),
    project_type: str = Query("cooperative", description="项目类型"),
):
    """获取区域分页列表"""
    # q = Q()
    # if area:
    #     q &= Q(area__contains=area)
    total, mapway_objs = await mapway_controller.search(keyword=area, project_type=project_type, page=page, page_size=page_size)
    data = [await obj.to_dict(exclude_fields=['project_type']) for obj in mapway_objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)

@router.get("/get", summary="查看单个区域")
async def get_mapway(mapway_id: int = Query(..., description="区域ID"),
):
    """根据ID获取区域详情"""
    mapway_obj = await mapway_controller.get(id=mapway_id)
    if not mapway_obj:
        return Fail(code=404, msg="区域不存在")
    return Success(data=await mapway_obj.to_dict(exclude_fields=['project_type']))

@router.post("/create", summary="创建区域")
async def create_mapway(mapway_in: MapwayCreate):
    """创建新的区域"""
    # 可以在这里添加一些业务校验，例如名称是否重复
    area = await mapway_controller.get_by_name(mapway_in.area)
    if area:
        return Fail(code=400, msg=f"区域 '{mapway_in.area}' 已存在")
    # print("✅ 后端收到的数据：", mapway_in.dict())
    new_mapway = await mapway_controller.create(obj_in=mapway_in)
    return Success(msg="创建成功")

@router.post("/update", summary="更新区域")
async def update_mapway(mapway_in: MapwayUpdate):
    """更新已有的区域"""
    await mapway_controller.update(id=mapway_in.id, obj_in=mapway_in)
    return Success(msg="更新成功")

@router.delete("/delete", summary="删除区域（逻辑删除）")
async def delete_mapway(mapway_id: int = Query(..., description="区域ID"),
):
    """逻辑删除泛化区域"""
    await mapway_controller.remove(id=mapway_id)
    return Success(msg="删除成功")


# 城市路线CRUD 接口
@router.get("/route/list", summary="城市路线列表（按类型分组）")
async def list_route_details(
    city: str = Query(..., description="城市名"),
    page: int = Query(1),
    page_size: int = Query(100),
):
    total, groups = await route_detail_controller.list_by_city_grouped(city, page, page_size)
    return SuccessExtra(data=groups, total=total, page=page, page_size=page_size)


@router.get("/route/image", summary="获取单条路线的原图")
async def get_route_image(route_id: int = Query(..., description="路线ID")):
    data = await route_detail_controller.get_route_image(route_id)
    if not data:
        return Fail(code=404, msg="路线不存在")
    return Success(data=data)

@router.post("/route/create", summary="新增路线")
async def create_route_detail(rd_in: RouteDetailCreate):
    await route_detail_controller.create(obj_in=rd_in)
    return Success(msg="创建成功")

@router.post("/route/update", summary="更新路线")
async def update_route_detail(rd_in: RouteDetailUpdate):
    await route_detail_controller.update(id=rd_in.id, obj_in=rd_in)
    return Success(msg="更新成功")

@router.delete("/route/delete", summary="删除路线")
async def delete_route_detail(route_id: int = Query(..., description="路线ID")):
    await route_detail_controller.remove(id=route_id)
    return Success(msg="删除成功")


# 城市详情搜索
@router.get("/route/search", summary="高级检索路线详情")
async def search_route_detail(
    field: str = Query(..., description="检索字段名"),
    keyword: str = Query("", description="检索关键词"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(100, description="每页数量"),
    order: str = Query("desc", description="排序方式: asc/desc"),
):
    try:
        total, objs = await route_detail_controller.search_by_field(
            field=field, keyword=keyword, page=page, page_size=page_size, order=order
        )
        actual_page_size = len(objs) if total == len(objs) else page_size
        return SuccessExtra(data=objs, total=total, page=page, page_size=actual_page_size)
    except ValueError as e:
        return Fail(code=400, msg=str(e))


class FilterCondition(BaseModel):
    field: str
    operator: str
    value: Optional[str] = ""


@router.post("/route/filter", summary="多条件筛选路线")
async def filter_routes(
    conditions: List[FilterCondition],
    logic: str = Query("and", description="组合逻辑: and/or"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(20, description="每页数量"),
):
    try:
        cond_list = [c.model_dump() for c in conditions]
        total, objs = await route_detail_controller.filter_routes(
            conditions=cond_list, logic=logic, page=page, page_size=page_size
        )
        return SuccessExtra(data=objs, total=total, page=page, page_size=page_size)
    except ValueError as e:
        return Fail(code=400, msg=str(e))
    

@router.post("/move_city", summary="移动城市到另一区域")
async def move_city(
    city: str = Query(..., description="城市名称"),
    from_area_id: int = Query(..., description="源区域ID"),
    to_area_id: int = Query(..., description="目标区域ID"),
):
    try:
        await mapway_controller.move_city(city, from_area_id, to_area_id)
        return Success(msg="移动成功")
    except ValueError as e:
        return Fail(code=400, msg=str(e))

# ===================== 自研项目路线接口 =====================

@router.get("/self-developed/route/list", summary="自研项目 - 城市路线列表（按类型分组）")
async def list_route_details_self_developed(
    city: str = Query(..., description="城市名"),
    page: int = Query(1),
    page_size: int = Query(100),
):
    total, groups = await route_detail_self_developed_controller.list_by_city_grouped(city, page, page_size)
    return SuccessExtra(data=groups, total=total, page=page, page_size=page_size)


@router.get("/self-developed/route/image", summary="自研项目 - 获取单条路线的原图")
async def get_self_developed_route_image(route_id: int = Query(..., description="路线ID")):
    data = await route_detail_self_developed_controller.get_self_developed_route_image(route_id)
    if not data:
        return Fail(code=404, msg="路线不存在")
    return Success(data=data)

@router.post("/self-developed/route/create", summary="自研项目 - 新增路线")
async def create_route_detail_self_developed(rd_in: RouteDetailSelfDevelopedCreate):
    await route_detail_self_developed_controller.create(obj_in=rd_in)
    return Success(msg="创建成功")

@router.post("/self-developed/route/update", summary="自研项目 - 更新路线")
async def update_route_detail_self_developed(rd_in: RouteDetailSelfDevelopedUpdate):
    await route_detail_self_developed_controller.update(id=rd_in.id, obj_in=rd_in)
    return Success(msg="更新成功")

@router.delete("/self-developed/route/delete", summary="自研项目 - 删除路线")
async def delete_route_detail_self_developed(route_id: int = Query(..., description="路线ID")):
    await route_detail_self_developed_controller.remove(id=route_id)
    return Success(msg="删除成功")

@router.get("/self-developed/route/search", summary="自研项目 - 高级检索路线详情")
async def search_route_detail_self_developed(
    field: str = Query(..., description="检索字段名"),
    keyword: str = Query("", description="检索关键词"),
    page: int = Query(1, description="页码"),
    page_size: int = Query(100, description="每页数量"),
    order: str = Query("desc", description="排序方式: asc/desc"),
):
    try:
        total, objs = await route_detail_self_developed_controller.search_by_field(
            field=field, keyword=keyword, page=page, page_size=page_size, order=order
        )
        actual_page_size = len(objs) if total == len(objs) else page_size
        return SuccessExtra(data=objs, total=total, page=page, page_size=actual_page_size)
    except ValueError as e:
        return Fail(code=400, msg=str(e))