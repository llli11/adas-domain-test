from app.controllers.base import CRUDBase
from app.models.version_index import *
from app.schemas.version_index import *

# 项目类型控制器
class ProjectTypeCrud(CRUDBase[ProjectType, ProjectTypeCreate, ProjectTypeCreate]):
    pass

# 车型控制器
class CarModelCrud(CRUDBase[CarModel, CarModelCreate, CarModelCreate]):
    pass

# 新增版本号CRUD控制器
class VersionCodeCrud(CRUDBase[VersionCode, VersionCodeCreate, VersionCodeCreate]):
    pass

# 指标大类控制器
class IndexCategoryCrud(CRUDBase[IndexCategory, IndexCategoryCreate, IndexCategoryCreate]):
    pass

# 指标子项控制器
class IndexSubItemCrud(CRUDBase[IndexSubItem, IndexSubItemCreate, IndexSubItemCreate]):
    pass

# 具体指标控制器
class IndexItemCrud(CRUDBase[IndexItem, IndexItemCreate, IndexItemCreate]):
    pass

# 实例化所有控制器
project_type_crud = ProjectTypeCrud(ProjectType)
car_model_crud = CarModelCrud(CarModel)
version_code_crud = VersionCodeCrud(VersionCode)
index_category_crud = IndexCategoryCrud(IndexCategory)
index_sub_item_crud = IndexSubItemCrud(IndexSubItem)
index_item_crud = IndexItemCrud(IndexItem)