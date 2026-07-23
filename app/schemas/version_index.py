from pydantic import BaseModel
from typing import Dict, Optional
from datetime import datetime

# ==================== 基础响应模型（列表下拉返回） ====================
class ProjectType(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class CarModel(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# 新增版本号返回模型
class VersionCodeSchema(BaseModel):
    id: int
    code: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IndexCategory(BaseModel):
    id: int
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IndexSubItem(BaseModel):
    id: int
    category_id: int
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class IndexItem(BaseModel):
    id: int
    sub_id: int
    name: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class VersionIndexData(BaseModel):
    id: int
    project_id: int
    car_id: int
    version_code: str
    category_id: int
    sub_id: int
    indicator_name: str
    indicator_value: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# ==================== 新增提交校验模型 ====================
class ProjectTypeCreate(BaseModel):
    name: str

class CarModelCreate(BaseModel):
    name: str

# 新增版本号新增提交模型
class VersionCodeCreate(BaseModel):
    code: str

class IndexCategoryCreate(BaseModel):
    name: str

class IndexSubItemCreate(BaseModel):
    category_id: int
    name: str

class IndexItemCreate(BaseModel):
    sub_id: int
    name: str

class VersionIndexDataSave(BaseModel):
    project_id: int
    car_id: int
    version_code: str
    category_id: int
    sub_id: int
    indicator_data: Dict[str, str]