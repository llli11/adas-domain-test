from fastapi import APIRouter, Query, HTTPException
import json

# 导入模型（新增VersionCode）
from app.models.version_index import (
    ProjectType, CarModel, VersionCode, IndexCategory, IndexSubItem, IndexItem, VersionIndexData
)

# 导入校验schema（新增VersionCodeCreate）
from app.schemas.version_index import (
    ProjectTypeCreate, CarModelCreate, VersionCodeCreate, IndexCategoryCreate,
    IndexSubItemCreate, IndexItemCreate, VersionIndexDataSave
)

router = APIRouter(tags=["版本指标管理"])

# ========== 项目类型 ==========
@router.get("/project-type/list", summary="获取项目类型下拉列表")
async def get_project_type_list():
    data = await ProjectType.all().values("id", "name")
    data = [{"id": row["id"], "name": row["name"]} for row in data]
    return {"code": 200, "data": data}

@router.post("/project-type/add", summary="新增项目类型")
async def add_project_type(body: ProjectTypeCreate):
    exists = await ProjectType.exists(name=body.name)
    if exists:
        raise HTTPException(status_code=400, detail="项目类型已存在")
    await ProjectType.create(name=body.name)
    return {"code": 200, "msg": "新增成功"}

@router.delete("/project-type/delete/{id}", summary="删除项目类型")
async def delete_project_type(id: int):
    await ProjectType.filter(id=id).delete()
    return {"code": 200, "msg": "删除成功"}

# ========== 车型 ==========
@router.get("/car-model/list", summary="获取车型下拉列表")
async def get_car_model_list():
    data = await CarModel.all().values("id", "name")
    data = [{"id": row["id"], "name": row["name"]} for row in data]
    return {"code": 200, "data": data}

@router.post("/car-model/add", summary="新增车型")
async def add_car_model(body: CarModelCreate):
    exists = await CarModel.exists(name=body.name)
    if exists:
        raise HTTPException(status_code=400, detail="车型已存在")
    await CarModel.create(name=body.name)
    return {"code": 200, "msg": "新增成功"}

@router.delete("/car-model/delete/{id}", summary="删除车型")
async def delete_car_model(id: int):
    await CarModel.filter(id=id).delete()
    return {"code": 200, "msg": "删除成功"}

# ========== 版本号全套接口 ==========
@router.get("/version-code/list", summary="获取版本号下拉列表")
async def get_version_code_list():
    data = await VersionCode.all().values("id", "code")
    data = [{"id": row["id"], "name": row["code"]} for row in data]
    return {"code": 200, "data": data}

@router.post("/version-code/add", summary="新增版本号")
async def add_version_code(body: VersionCodeCreate):
    exists = await VersionCode.exists(code=body.code)
    if exists:
        raise HTTPException(status_code=400, detail="该版本号已存在")
    await VersionCode.create(code=body.code)
    return {"code": 200, "msg": "新增成功"}

@router.delete("/version-code/delete/{id}", summary="删除版本号")
async def delete_version_code(id: int):
    await VersionCode.filter(id=id).delete()
    return {"code": 200, "msg": "删除成功"}

# ========== 指标大类 ==========
@router.get("/index-category/list", summary="获取指标大类下拉列表")
async def get_index_category_list():
    data = await IndexCategory.all().values("id", "name")
    data = [{"id": row["id"], "name": row["name"]} for row in data]
    return {"code": 200, "data": data}

@router.post("/index-category/add", summary="新增指标大类")
async def add_index_category(body: IndexCategoryCreate):
    exists = await IndexCategory.exists(name=body.name)
    if exists:
        raise HTTPException(status_code=400, detail="指标大类已存在")
    await IndexCategory.create(name=body.name)
    return {"code": 200, "msg": "新增成功"}

@router.delete("/index-category/delete/{id}", summary="删除指标大类")
async def delete_index_category(id: int):
    await IndexCategory.filter(id=id).delete()
    return {"code": 200, "msg": "删除成功"}

# ========== 指标子项 ==========
@router.get("/index-sub/list", summary="根据大类ID获取指标子项列表")
async def get_index_sub_list(category_id: int = Query(..., description="指标大类ID")):
    data = await IndexSubItem.filter(category_id=category_id).values("id", "name")
    data = [{"id": row["id"], "name": row["name"]} for row in data]
    return {"code": 200, "data": data}

@router.post("/index-sub/add", summary="新增指标子项")
async def add_index_sub_item(body: IndexSubItemCreate):
    await IndexSubItem.create(category_id=body.category_id, name=body.name)
    return {"code": 200, "msg": "新增成功"}

@router.delete("/index-sub/delete/{id}", summary="删除指标子项")
async def delete_index_sub_item(id: int):
    await IndexSubItem.filter(id=id).delete()
    return {"code": 200, "msg": "删除成功"}

# ========== 具体指标 ==========
@router.get("/index-item/list", summary="根据子项ID获取具体指标列表")
async def get_index_item_list(sub_id: int = Query(..., description="指标子项ID")):
    data = await IndexItem.filter(sub_id=sub_id).values("id", "name")
    data = [{"id": row["id"], "name": row["name"]} for row in data]
    return {"code": 200, "data": data}

@router.post("/index-item/add", summary="新增具体指标")
async def add_index_item(body: IndexItemCreate):
    await IndexItem.create(sub_id=body.sub_id, name=body.name)
    return {"code": 200, "msg": "新增成功"}

@router.delete("/index-item/delete/{id}", summary="删除具体指标")
async def delete_index_item(id: int):
    await IndexItem.filter(id=id).delete()
    return {"code": 200, "msg": "删除成功"}

# ========== 保存版本指标数据（自动存入版本号字典） ==========
@router.post("/data/save", summary="批量保存版本指标填写数据")
async def save_version_index_data(body: VersionIndexDataSave):
    if not await VersionCode.exists(code=body.version_code):
        await VersionCode.create(code=body.version_code)

    for name, value in body.indicator_data.items():
        await VersionIndexData.create(
            project_id=body.project_id,
            car_id=body.car_id,
            version_code=body.version_code,
            category_id=body.category_id,
            sub_id=body.sub_id,
            indicator_name=name,
            indicator_value=value
        )
    return {"code": 200, "msg": "指标数据保存成功"}

# ========== 查询已保存版本指标数据 ==========
@router.get("/data/list", summary="按项目+车型+版本查询已存指标数据")
async def get_saved_version_data(
    project_id: int = Query(..., description="项目类型ID"),
    car_id: int = Query(..., description="车型ID"),
    version_code: str = Query(..., description="版本编号")
    ):
    queryset = VersionIndexData.filter(
        project_id=project_id,
        car_id=car_id,
        version_code=version_code
    )
    total = await queryset.count()
    data = await queryset.values("id", "indicator_name", "indicator_value")
    return {"code": 200, "total": total, "data": data}