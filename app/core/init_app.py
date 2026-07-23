import os
import shutil
from pathlib import Path
from typing import List

from aerich import Command
from aerich.exceptions import AerichError
from fastapi import FastAPI
from fastapi.middleware import Middleware
from fastapi.middleware.cors import CORSMiddleware
from tortoise import Tortoise, connections
from tortoise.expressions import Q

from app.api import api_router
from app.controllers.api import api_controller
from app.controllers.user import UserCreate, user_controller
from app.core.exceptions import (
    DoesNotExist,
    DoesNotExistHandle,
    HTTPException,
    HttpExcHandle,
    IntegrityError,
    IntegrityHandle,
    RequestValidationError,
    RequestValidationHandle,
    ResponseValidationError,
    ResponseValidationHandle,
)
from app.log import logger
from app.models.admin import Api, Menu, Role
from app.schemas.menus import MenuType
from app.settings.config import settings

from .middlewares import BackGroundTaskMiddleware, HttpAuditLogMiddleware


def make_middlewares():
    middleware = [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
            allow_methods=settings.CORS_ALLOW_METHODS,
            allow_headers=settings.CORS_ALLOW_HEADERS,
        ),
        Middleware(BackGroundTaskMiddleware),
        Middleware(
            HttpAuditLogMiddleware,
            methods=["GET", "POST", "PUT", "DELETE"],
            exclude_paths=getattr(settings, "AUDIT_EXCLUDE_PATHS", [
                "/api/v1/base/access_token",
                "/api/v1/tool/image",
				"/api/v1/vehicle/import/template",
                "/docs",
                "/openapi.json",
                "/assets/",
                "/resource/",
                "/favicon.svg",
                "^/$",
                "/settlement/driver/export",
                "/settlement/engineer/export",
				"/uploads",
                "/api/v1/ecu/target/template",
                "/api/v1/ecu/target/update",
            ]),
        ),
    ]
    return middleware


def register_exceptions(app: FastAPI):
    app.add_exception_handler(DoesNotExist, DoesNotExistHandle)
    app.add_exception_handler(HTTPException, HttpExcHandle)
    app.add_exception_handler(IntegrityError, IntegrityHandle)
    app.add_exception_handler(RequestValidationError, RequestValidationHandle)
    app.add_exception_handler(ResponseValidationError, ResponseValidationHandle)


def register_routers(app: FastAPI, prefix: str = "/api"):
    app.include_router(api_router, prefix=prefix)
    register_static(app)


def register_static(app: FastAPI):
    """挂载前端静态文件和上传目录"""

    from fastapi.staticfiles import StaticFiles


    # 挂载上传目录
    uploads_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static", "uploads")
    os.makedirs(uploads_path, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

    # 挂载前端打包文件
    web_dist_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "web", "dist"
    )
    app.mount("/", StaticFiles(directory=web_dist_path, html=True), name="web")

async def init_superuser():
    user = await user_controller.model.exists()
    if not user:
        await user_controller.create_user(
            UserCreate(
                username="admin",
                email="admin@admin.com",
                password="123456",
                is_active=True,
                is_superuser=True,
            )
        )


async def _create_ecu_menus() -> None:
    """创建ECU相关菜单"""
    ecu_menu = await Menu.create(
        menu_type=MenuType.MENU,
        name="整车ECU版本管理",
        path="/ecu",
        order=10,
        parent_id=0,
        icon="mdi-alert-box-outline",
        is_hidden=False,
        component="/ecu",
        keepalive=False,
        redirect="",
    )
    ecu_children = [
        Menu(
            menu_type=MenuType.MENU,
            name="车辆列表",
            path="",
            order=0,
            parent_id=ecu_menu.id,
            icon="car",
            is_hidden=False,
            component="/ecu",
            keepalive=True,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="ECU详情",
            path="detail/:vin",
            order=1,
            parent_id=ecu_menu.id,
            icon="car",
            is_hidden=True,
            component="/ecu/detail",
            keepalive=True,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="基线列表",
            path="target",
            order=2,
            parent_id=ecu_menu.id,
            icon="list",
            is_hidden=False,
            component="/ecu/target",
            keepalive=True,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="目标详情",
            path="target/detail/:target_name",
            order=3,
            parent_id=ecu_menu.id,
            icon="detail",
            is_hidden=True,
            component="/ecu/target/detail",
            keepalive=True,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="操作记录",
            path="logs",
            order=4,
            parent_id=ecu_menu.id,
            icon="history",
            is_hidden=False,
            component="/ecu/logs",
            keepalive=True,
        ),
    ]
    await Menu.bulk_create(ecu_children)
    # logger.info("ECU菜单创建成功")

async def _create_test_route_menus() -> None:
    """创建测试路线相关菜单"""
    testroute_menu = await Menu.create(
        menu_type=MenuType.CATALOG,
        name="测试路线管理",
        path="/testroute",
        order=5,
        parent_id=0,
        icon="material-symbols:route",
        is_hidden=False,
        component="Layout",
        keepalive=False,
        redirect="/testroute/mapway",
    )
    testroute_children = [
        Menu(
            menu_type=MenuType.MENU,
            name="测试路线",
            path="mapway",
            order=0,
            parent_id=testroute_menu.id,
            icon="material-symbols:map",
            is_hidden=False,
            component="/testroute/mapway",
            keepalive=True,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="测试路线城市详情",
            path="city/:city",
            order=1,
            parent_id=testroute_menu.id,
            icon="",
            is_hidden=True,
            component="/testroute/mapway/cityDetail",
            keepalive=True,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="自研项目",
            path="selfdeveloped",
            order=2,
            parent_id=testroute_menu.id,
            icon="material-symbols:science",
            is_hidden=True,
            component="/testroute/selfdeveloped",
            keepalive=True,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="自研城市详情",
            path="selfdeveloped/city/:city",
            order=3,
            parent_id=testroute_menu.id,
            icon="",
            is_hidden=True,
            component="/testroute/selfdeveloped/cityDetail",
            keepalive=True,
        ),
    ]
    await Menu.bulk_create(testroute_children)

# ===================== 新增：版本管理菜单创建函数（参数完全匹配截图） =====================
async def _create_version_menus() -> None:
    """创建版本管理一级菜单，参数完全对齐编辑菜单弹窗截图"""
    await Menu.create(
        # 菜单类型：单选【菜单】对应 MenuType.MENU
        menu_type=MenuType.MENU,
        # 菜单名称
        name="版本管理",
        # 访问路径
        path="/versionIndex",
        # 显示排序
        order=13,
        # 上级菜单：根目录 parent_id=0
        parent_id=0,
        # 菜单图标
        icon="ph:user-list-bold",
        # 是否隐藏：开关关闭=False
        is_hidden=False,
        # 组件路径
        component="/versionIndex",
        # KeepAlive：开关关闭=False
        keepalive=False,
        # 跳转路径：输入框为空
        redirect="",
    )
# ======================================================================

async def init_menus() -> None:
    """初始化菜单"""
    menus = await Menu.exists()
    if not menus:
        parent_menu = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="系统管理",
            path="/system",
            order=1,
            parent_id=0,
            icon="carbon:gui-management",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/system/user",
        )
        children_menu = [
            Menu(
                menu_type=MenuType.MENU,
                name="用户管理",
                path="user",
                order=1,
                parent_id=parent_menu.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/system/user",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="角色管理",
                path="role",
                order=2,
                parent_id=parent_menu.id,
                icon="carbon:user-role",
                is_hidden=False,
                component="/system/role",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="菜单管理",
                path="menu",
                order=3,
                parent_id=parent_menu.id,
                icon="material-symbols:list-alt-outline",
                is_hidden=False,
                component="/system/menu",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="API管理",
                path="api",
                order=4,
                parent_id=parent_menu.id,
                icon="ant-design:api-outlined",
                is_hidden=False,
                component="/system/api",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="部门管理",
                path="dept",
                order=5,
                parent_id=parent_menu.id,
                icon="mingcute:department-line",
                is_hidden=False,
                component="/system/dept",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="审计日志",
                path="auditlog",
                order=6,
                parent_id=parent_menu.id,
                icon="ph:clipboard-text-bold",
                is_hidden=False,
                component="/system/auditlog",
                keepalive=False,
            ),
]
        await Menu.bulk_create(children_menu)
        # 创建测试路线菜单
        await _create_test_route_menus()
        await Menu.create(
            menu_type=MenuType.MENU,
            name="一级菜单",
            path="/top-menu",
            order=2,
            parent_id=0,
            icon="material-symbols:featured-play-list-outline",
            is_hidden=False,
            component="/top-menu",
            keepalive=False,
            redirect="",
        )
        await _create_ecu_menus()

        # 车辆管理菜单（不展开子菜单，主页面内Tab切换）
        await Menu.create(
            menu_type=MenuType.MENU,
            name="车辆管理",
            path="/vehicle",
            order=3,
            parent_id=0,
            icon="mdi:car-multiple",
            is_hidden=False,
            component="/vehicle",
            keepalive=True,
            redirect="",
        )

        # 外委管理目录
        contractor_parent = await Menu.create(
            menu_type=MenuType.CATALOG,
            name="外委管理",
            path="/contractor",
            order=4,
            parent_id=0,
            icon="material-symbols:engineering-outline",
            is_hidden=False,
            component="Layout",
            keepalive=False,
            redirect="/contractor/staff",
        )
        contractor_children = [
            Menu(
                menu_type=MenuType.MENU,
                name="人员台账",
                path="staff",
                order=1,
                parent_id=contractor_parent.id,
                icon="material-symbols:person-outline-rounded",
                is_hidden=False,
                component="/contractor/staff",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="状态看板",
                path="status",
                order=2,
                parent_id=contractor_parent.id,
                icon="material-symbols:dashboard-outline",
                is_hidden=False,
                component="/contractor/status",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="需求管理",
                path="requirement",
                order=3,
                parent_id=contractor_parent.id,
                icon="material-symbols:request-page-outline",
                is_hidden=False,
                component="/contractor/requirement",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="流动管理",
                path="transfer",
                order=4,
                parent_id=contractor_parent.id,
                icon="material-symbols:sync-outline",
                is_hidden=False,
                component="/contractor/transfer",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="工作日志审核",
                path="worklog",
                order=5,
                parent_id=contractor_parent.id,
                icon="material-symbols:assignment-turned-in-outline",
                is_hidden=False,
                component="/contractor/worklog",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="请假管理",
                path="leave",
                order=6,
                parent_id=contractor_parent.id,
                icon="material-symbols:time-off-outline",
                is_hidden=False,
                component="/contractor/leave",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="考评管理",
                path="evaluation",
                order=7,
                parent_id=contractor_parent.id,
                icon="material-symbols:star-outline",
                is_hidden=False,
                component="/contractor/evaluation",
                keepalive=False,
            ),
        ]
        await Menu.bulk_create(contractor_children)
        # 首次初始化时创建版本管理菜单
        await _create_version_menus()
    else:
        # 检查并补充缺失的ECU菜单
        ecu_menu = await Menu.get_or_none(path="/ecu")
        if not ecu_menu:
            await _create_ecu_menus()
            logger.info("补充创建ECU菜单")
        # 检查并补充缺失的测试路线菜单
        testroute_menu = await Menu.get_or_none(path="/testroute")
        if not testroute_menu:
            await _create_test_route_menus()
            logger.info("补充创建测试路线菜单")
        else:
            # 补充缺失的城市详情菜单（隐藏页）
            cooperative_detail = await Menu.get_or_none(path="city/:city", parent_id=testroute_menu.id)
            if not cooperative_detail:
                await Menu.create(
                    menu_type=MenuType.MENU,
                    name="测试路线城市详情",
                    path="city/:city",
                    order=1,
                    parent_id=testroute_menu.id,
                    icon="",
                    is_hidden=True,
                    component="/testroute/mapway/cityDetail",
                    keepalive=True,
                )
                logger.info("补充创建测试路线城市详情菜单")
            self_developed_detail = await Menu.get_or_none(path="selfdeveloped/city/:city", parent_id=testroute_menu.id)
            if not self_developed_detail:
                await Menu.create(
                    menu_type=MenuType.MENU,
                    name="自研城市详情",
                    path="selfdeveloped/city/:city",
                    order=3,
                    parent_id=testroute_menu.id,
                    icon="",
                    is_hidden=True,
                    component="/testroute/selfdeveloped/cityDetail",
                    keepalive=True,
                )
                logger.info("补充创建自研城市详情菜单")
        # 已有菜单时自动补全版本管理菜单
        version_menu = await Menu.get_or_none(path="/versionIndex")
        if not version_menu:
            await _create_version_menus()
            logger.info("补充创建版本管理菜单")

async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db() -> None:
    """初始化数据库并执行自动迁移"""
    try:
        # 先初始化Tortoise（不自动生成schema）
        await Tortoise.init(config=settings.TORTOISE_ORM)
        
        # 创建Command实例
        command = Command(tortoise_config=settings.TORTOISE_ORM, app="models")
        
        # 检查migrations目录
        dirname = Path("migrations", "models")
        migrations_exist = dirname.exists() and list(dirname.glob("[0-9]*.py"))
        
        if not migrations_exist:
            # 首次初始化，删除可能存在的残留文件
            if dirname.exists():
                shutil.rmtree(dirname, ignore_errors=True)
            # 使用 aerich 初始化数据库，避免重复创建表
            await command.init_db(safe=True)
            logger.info("数据库首次初始化完成")
        else:
            # 已有迁移文件，不自动生成 schemas，完全由 aerich 管理
            logger.info("使用 aerich 管理数据库 schema")
        
        # 初始化 aerich
        await command.init()
        
        # 生成新的迁移文件（如果模型有变化）
        try:
            migration_name = await command.migrate()
            if migration_name:
                logger.info(f"生成迁移文件: {migration_name}")
            else:
                logger.info("没有检测到模型变化")
        except AerichError as e:
            logger.warning(f"生成迁移文件时出现警告: {e}")
        except Exception as e:
            logger.error(f"生成迁移文件失败: {e}")
        
        # 执行迁移
        try:
            await command.upgrade(run_in_transaction=True)
            logger.info("数据库迁移执行成功")
        except AerichError as e:
            logger.warning(f"执行迁移时出现警告: {e}")
        except Exception as e:
            logger.error(f"执行迁移失败: {e}")
        
        # 重要：移除 Tortoise.generate_schemas() 调用，完全由 aerich 管理表结构
        
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        # 不抛出异常，允许服务继续运行


async def init_roles():
    roles = await Role.exists()
    if not roles:
        admin_role = await Role.create(
            name="管理员",
            desc="管理员角色",
        )
        user_role = await Role.create(
            name="普通用户",
            desc="普通用户角色",
        )

        # 分配所有API给管理员角色
        all_apis = await Api.all()
        await admin_role.apis.add(*all_apis)
        # 分配所有菜单给管理员和普通用户
        all_menus = await Menu.all()
        await admin_role.menus.add(*all_menus)
        await user_role.menus.add(*all_menus)

        # 为普通用户分配基本API
        basic_apis = await Api.filter(Q(method__in=["GET"]) | Q(tags="基础模块"))
        await user_role.apis.add(*basic_apis)


async def init_data():
    await init_db()
    await init_superuser()
    await init_menus()
    await init_apis()
    await init_roles()