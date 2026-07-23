from fastapi import APIRouter

from app.core.dependency import DependPermission

from .apis import apis_router
from .auditlog import auditlog_router
from .base import base_router
from .depts import depts_router
from .menus import menus_router
from .contractor import contractor_router, qr_router
from .roles import roles_router
from .users import users_router

from .mapway import mapway_router
from .tool import tool_router, image_router
from .expense import expense_router
from .settlement import engineer_router, driver_router, confirmation_router

from .vehicles import vehicles_router
from .version_index.version_index import router as version_index_router

from .ecu import ecu_api_router
from .target import target_api_router

v1_router = APIRouter()

v1_router.include_router(base_router, prefix="/base")
v1_router.include_router(users_router, prefix="/user", dependencies=[DependPermission])
v1_router.include_router(roles_router, prefix="/role", dependencies=[DependPermission])
v1_router.include_router(menus_router, prefix="/menu", dependencies=[DependPermission])
v1_router.include_router(apis_router, prefix="/api", dependencies=[DependPermission])
v1_router.include_router(depts_router, prefix="/dept", dependencies=[DependPermission])
v1_router.include_router(auditlog_router, prefix="/auditlog", dependencies=[DependPermission])

v1_router.include_router(mapway_router, prefix="/mapway", dependencies=[DependPermission])
v1_router.include_router(tool_router, prefix="/tool", dependencies=[DependPermission])
v1_router.include_router(image_router, prefix="/tool/image")  # 图片访问无需认证
v1_router.include_router(expense_router, prefix="/expense", dependencies=[DependPermission])

v1_router.include_router(engineer_router, prefix="/settlement/engineer", dependencies=[DependPermission])
v1_router.include_router(driver_router, prefix="/settlement/driver", dependencies=[DependPermission])

v1_router.include_router(confirmation_router, prefix="/settlement/confirmation", dependencies=[DependPermission])

v1_router.include_router(vehicles_router, prefix="/vehicle", dependencies=[DependPermission])
v1_router.include_router(contractor_router, prefix="/contractor", dependencies=[DependPermission], tags=["外委管理"])
# 二维码公开接口（免登录）
v1_router.include_router(qr_router, prefix="/contractor/qr")
v1_router.include_router(version_index_router, prefix="/version_index")

v1_router.include_router(ecu_api_router, prefix="/ecu")
v1_router.include_router(target_api_router, prefix="/ecu")
