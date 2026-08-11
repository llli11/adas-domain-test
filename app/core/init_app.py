import os
import shutil
from pathlib import Path
from typing import List

from aerich import Command
try:
    from aerich.exceptions import AerichError
except ImportError:
    AerichError = Exception
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

async def _create_vehicle_menus() -> None:
    """创建车辆管理目录及 4 个子菜单"""
    vehicle_parent = await Menu.create(
        menu_type=MenuType.CATALOG,
        name="车辆管理",
        path="/vehicle",
        order=3,
        parent_id=0,
        icon="mdi:car-multiple",
        is_hidden=False,
        component="Layout",
        keepalive=False,
        redirect="/vehicle/task-status",
    )
    vehicle_children = [
        Menu(
            menu_type=MenuType.MENU,
            name="车辆任务状态",
            path="task-status",
            order=1,
            parent_id=vehicle_parent.id,
            icon="material-symbols:task-alt",
            is_hidden=False,
            component="/vehicle/task-status",
            keepalive=True,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="车辆数据详情",
            path="data-detail",
            order=2,
            parent_id=vehicle_parent.id,
            icon="material-symbols:table-rows",
            is_hidden=False,
            component="/vehicle/data-detail",
            keepalive=True,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="异常状态提醒",
            path="expiry-alerts",
            order=3,
            parent_id=vehicle_parent.id,
            icon="material-symbols:notifications-active",
            is_hidden=False,
            component="/vehicle/expiry-alerts",
            keepalive=True,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="数据源管理",
            path="data-source",
            order=4,
            parent_id=vehicle_parent.id,
            icon="material-symbols:cloud-sync",
            is_hidden=False,
            component="/vehicle/data-source",
            keepalive=True,
        ),
    ]
    await Menu.bulk_create(vehicle_children)

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
        await _create_ecu_menus()

        # 车辆管理目录（4 个子菜单）
        await _create_vehicle_menus()

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
                name="人员考核管理",
                path="assessment",
                order=2,
                parent_id=contractor_parent.id,
                icon="material-symbols:assignment-turned-in-outline",
                is_hidden=False,
                component="/contractor/assessment",
                keepalive=False,
            ),
            Menu(
                menu_type=MenuType.MENU,
                name="考评管理",
                path="evaluation",
                order=3,
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
        # 检查并补充缺失的测试路线菜单
        testroute_menu = await Menu.get_or_none(path="/testroute")
        if not testroute_menu:
            await _create_test_route_menus()
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
        # 已有菜单时自动补全版本管理菜单
        version_menu = await Menu.get_or_none(path="/versionIndex")
        if not version_menu:
            await _create_version_menus()

        # 车辆管理菜单迁移：旧 MENU(Tab 容器) → CATALOG + 4 子菜单
        vehicle_menu = await Menu.get_or_none(path="/vehicle")
        if vehicle_menu:
            if vehicle_menu.component == "/vehicle":
                vehicle_menu.menu_type = MenuType.CATALOG
                vehicle_menu.component = "Layout"
                vehicle_menu.redirect = "/vehicle/task-status"
                vehicle_menu.keepalive = False
                await vehicle_menu.save()
            vehicle_children = [
                ("车辆任务状态", "task-status", 1, "material-symbols:task-alt", "/vehicle/task-status"),
                ("车辆数据详情", "data-detail", 2, "material-symbols:table-rows", "/vehicle/data-detail"),
                ("异常状态提醒", "expiry-alerts", 3, "material-symbols:notifications-active", "/vehicle/expiry-alerts"),
                ("数据源管理", "data-source", 4, "material-symbols:cloud-sync", "/vehicle/data-source"),
            ]
            for name, path, order, icon, component in vehicle_children:
                exists = await Menu.filter(path=path, parent_id=vehicle_menu.id).exists()
                if not exists:
                    await Menu.create(
                        menu_type=MenuType.MENU,
                        name=name,
                        path=path,
                        order=order,
                        parent_id=vehicle_menu.id,
                        icon=icon,
                        is_hidden=False,
                        component=component,
                        keepalive=True,
                    )

        # 外委管理菜单迁移：删除废弃菜单（状态看板/需求/流转/工作日志/请假），补充考核管理
        contractor_menu = await Menu.get_or_none(path="/contractor")
        if contractor_menu:
            # 删除已废弃的子菜单
            deprecated_paths = ["status", "requirement", "transfer", "worklog", "leave"]
            for dp in deprecated_paths:
                await Menu.filter(path=dp, parent_id=contractor_menu.id).delete()
            # 补充缺失的考核管理菜单
            if not await Menu.filter(path="assessment", parent_id=contractor_menu.id).exists():
                await Menu.create(
                    menu_type=MenuType.MENU,
                    name="人员考核管理",
                    path="assessment",
                    order=2,
                    parent_id=contractor_menu.id,
                    icon="material-symbols:assignment-turned-in-outline",
                    is_hidden=False,
                    component="/contractor/assessment",
                    keepalive=False,
                )

        # 清理重复的父级菜单（保留最早创建的）
        await _dedup_parent_menus(["/expense-management", "/tool-management"])

        # 费用管理菜单初始化
        expense_parent = await Menu.get_or_none(path="/expense-management")
        if not expense_parent:
            await _create_expense_management_menus()
        else:
            # 补充缺失的子菜单（只补创建，不删除，不重复创建父菜单）
            expense_children = [
                ("工作台", "dashboard", 1, "material-symbols:dashboard", "/expense-management/dashboard", False),
                ("每日记录", "daily-record", 2, "material-symbols:calendar-today", "/expense-management/daily-record", False),
                ("月度结算", "monthly-settlement", 3, "material-symbols:receipt-long", "/expense-management/monthly-settlement", False),
                ("费用看板", "expense-board", 4, "material-symbols:finance", "/expense-management/expense-board", False),
                ("试验单费用看板", "test-order-board", 5, "material-symbols:chart-data", "/expense-management/test-order-board", False),
                ("费用确认", "monthly-board", 6, "material-symbols:verified", "/expense-management/monthly-board", False),
            ]
            for name, path, order, icon, component, keepalive in expense_children:
                if not await Menu.filter(path=path, parent_id=expense_parent.id).exists():
                    await Menu.create(
                        menu_type=MenuType.MENU,
                        name=name,
                        path=path,
                        order=order,
                        parent_id=expense_parent.id,
                        icon=icon,
                        is_hidden=False,
                        component=component,
                        keepalive=keepalive,
                    )
            # 确保redirect指向工作台
            if expense_parent.redirect != "/expense-management/dashboard":
                expense_parent.redirect = "/expense-management/dashboard"
                await expense_parent.save()

        # 工具管理菜单初始化
        tool_parent = await Menu.get_or_none(path="/tool-management")
        if not tool_parent:
            await _create_tool_management_menus()


async def _dedup_parent_menus(paths: list):
    """删除重复的父级菜单，保留最早创建的（最小ID），只在 parent_id=0 层级去重"""
    for path in paths:
        parents = await Menu.filter(path=path, parent_id=0).all()
        if len(parents) > 1:
            keep = min(parents, key=lambda m: m.id)
            for m in parents:
                if m.id != keep.id:
                    await Menu.filter(parent_id=m.id).delete()
                    await m.delete()
            logger.warning(f"[Menu] 清理了 {len(parents) - 1} 个重复的 {path} 菜单，保留 id={keep.id}")


async def _create_tool_management_menus():
    """创建工具管理菜单"""
    parent = await Menu.create(
        menu_type=MenuType.CATALOG,
        name="工具管理",
        path="/tool-management",
        order=10,
        icon="material-symbols:handyman-outline",
        component="Layout",
        redirect="/tool-management/tool-ledger",
        keepalive=True,
    )
    children = [
        Menu(
            menu_type=MenuType.MENU,
            name="工具台账",
            path="tool-ledger",
            order=1,
            parent_id=parent.id,
            icon="material-symbols:inventory-2-outline",
            is_hidden=False,
            component="/tool-management/tool-ledger",
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="工具借用",
            path="tool-borrow",
            order=2,
            parent_id=parent.id,
            icon="material-symbols:swap-horiz",
            is_hidden=False,
            component="/tool-management/tool-borrow",
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="工具盘点",
            path="tool-inventory",
            order=3,
            parent_id=parent.id,
            icon="material-symbols:list-alt-outline",
            is_hidden=False,
            component="/tool-management/tool-inventory",
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="工具需求",
            path="tool-requirement",
            order=4,
            parent_id=parent.id,
            icon="material-symbols:assignment-add-outline",
            is_hidden=False,
            component="/tool-management/tool-requirement",
            keepalive=False,
        ),
    ]
    await Menu.bulk_create(children)


async def _create_expense_management_menus():
    """创建费用管理菜单"""
    parent = await Menu.create(
        menu_type=MenuType.CATALOG,
        name="费用管理",
        path="/expense-management",
        order=9,
        icon="material-symbols:attach-money",
        component="Layout",
        redirect="/expense-management/dashboard",
        keepalive=True,
    )
    children = [
        Menu(
            menu_type=MenuType.MENU,
            name="工作台",
            path="dashboard",
            order=1,
            parent_id=parent.id,
            icon="material-symbols:dashboard",
            is_hidden=False,
            component="/expense-management/dashboard",
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="每日记录",
            path="daily-record",
            order=2,
            parent_id=parent.id,
            icon="material-symbols:calendar-today",
            is_hidden=False,
            component="/expense-management/daily-record",
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="月度结算",
            path="monthly-settlement",
            order=3,
            parent_id=parent.id,
            icon="material-symbols:receipt-long",
            is_hidden=False,
            component="/expense-management/monthly-settlement",
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="费用看板",
            path="expense-board",
            order=4,
            parent_id=parent.id,
            icon="material-symbols:finance",
            is_hidden=False,
            component="/expense-management/expense-board",
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="试验单费用看板",
            path="test-order-board",
            order=5,
            parent_id=parent.id,
            icon="material-symbols:chart-data",
            is_hidden=False,
            component="/expense-management/test-order-board",
            keepalive=False,
        ),
        Menu(
            menu_type=MenuType.MENU,
            name="费用确认",
            path="monthly-board",
            order=6,
            parent_id=parent.id,
            icon="material-symbols:verified",
            is_hidden=False,
            component="/expense-management/monthly-board",
            keepalive=False,
        ),
    ]
    await Menu.bulk_create(children)


async def init_apis():
    apis = await api_controller.model.exists()
    if not apis:
        await api_controller.refresh_api()


async def init_db() -> None:
    """初始化数据库并执行迁移（日志驱动，结果可见）"""
    try:
        logger.info("[DB] 开始数据库初始化")

        # 1. 初始化 Tortoise ORM
        await Tortoise.init(config=settings.TORTOISE_ORM)
        logger.debug("[DB] Tortoise ORM 初始化完成")

        command = Command(tortoise_config=settings.TORTOISE_ORM, app="models")

        migrations_dir = Path("migrations", "models")
        has_migrations = migrations_dir.exists() and any(migrations_dir.glob("[0-9]*.py"))

        # 2. 首次初始化
        if not has_migrations:
            logger.info("[DB] 未检测到迁移文件，执行首次初始化")

            if migrations_dir.exists():
                shutil.rmtree(migrations_dir, ignore_errors=True)

            await command.init_db(safe=True)
            logger.info("[DB] 数据库首次初始化完成")
            return

        # 3. 增量迁移
        logger.info("[DB] 检测到已有迁移文件，进入增量迁移模式")
        await command.init()

        # 3.1 生成迁移
        try:
            migration_name = await command.migrate()
            if migration_name:
                logger.info(f"[DB] 检测到模型变更，生成迁移: {migration_name}")
            else:
                logger.info("[DB] 未检测到模型变更")
        except AerichError as e:
            logger.warning(f"[DB] migrate 警告: {e}")
        except Exception as e:
            logger.error(f"[DB] migrate 失败: {e}")
            raise

        # 3.2 执行迁移
        try:
            await command.upgrade(run_in_transaction=True)
            logger.info("[DB] 数据库迁移执行成功")
        except AerichError as e:
            logger.warning(f"[DB] upgrade 警告: {e}")
        except Exception as e:
            logger.error(f"[DB] upgrade 失败: {e}")
            raise

        logger.info("[DB] 数据库初始化完成")

    except Exception as e:
        logger.error(f"[DB] 数据库初始化异常: {e}", exc_info=True)
        # 保持原有行为：不抛异常，允许服务继续运行


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


async def reset_contractor_staff_status():
    """启动时重置所有外委人员状态为空闲"""
    from app.models.contractor import ContractorStaff

    count = await ContractorStaff.filter(task_status="任务中").update(
        task_status="空闲", is_idle=True, current_vehicle=None, current_task=None
    )
    if count:
        logger.info(f"服务启动: 已重置 {count} 名外委人员为空闲状态")


async def init_data():
    await init_db()
    await init_superuser()
    await init_menus()
    await init_apis()
    await init_roles()
    await reset_contractor_staff_status()