from tortoise import fields
from .base import BaseModel, TimestampMixin

# 项目类型
class ProjectType(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=50, unique=True, description="项目类型")

    class Meta:
        table = "version_project_type"

# 车型
class CarModel(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=50, unique=True, description="车型名称")

    class Meta:
        table = "version_car_model"

# 新增：版本号独立字典表
class VersionCode(BaseModel, TimestampMixin):
    code = fields.CharField(max_length=50, unique=True, description="版本号字符串")

    class Meta:
        table = "version_code"

# 指标大类
class IndexCategory(BaseModel, TimestampMixin):
    name = fields.CharField(max_length=50, unique=True, description="指标大类")

    class Meta:
        table = "version_index_category"

# 指标子项
class IndexSubItem(BaseModel, TimestampMixin):
    category_id = fields.IntField(description="所属大类ID")
    name = fields.CharField(max_length=50, description="子项名称")

    class Meta:
        table = "version_index_sub_item"

# 具体指标
class IndexItem(BaseModel, TimestampMixin):
    sub_id = fields.IntField(description="所属子项ID")
    name = fields.CharField(max_length=100, description="指标名称")

    class Meta:
        table = "version_index_item"

# 版本指标业务数据表
class VersionIndexData(BaseModel, TimestampMixin):
    project_id = fields.IntField()
    car_id = fields.IntField()
    version_code = fields.CharField(max_length=50)
    category_id = fields.IntField()
    sub_id = fields.IntField()
    indicator_name = fields.CharField(max_length=100)
    indicator_value = fields.CharField(max_length=200, null=True)

    class Meta:
        table = "version_index_data"