import asyncio
import os
from contextlib import asynccontextmanager
from datetime import date, timedelta

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from tortoise import Tortoise
from app.log import logger
from app.core.exceptions import SettingNotFound
from app.core.init_app import (
    init_data,
    make_middlewares,
    register_exceptions,
    register_routers,
)

try:
    from app.settings.config import settings
except ImportError:
    raise SettingNotFound("Can not import settings")

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "..", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)


async def _daily_staff_reset():
    """每日凌晨重置所有外委人员状态为空闲"""
    from app.models.contractor import ContractorStaff

    today = date.today()
    while True:
        now = date.today()
        if now != today:
            count = await ContractorStaff.filter(task_status="任务中").update(
                task_status="空闲", is_idle=True, current_vehicle=None, current_task=None
            )
            if count:
                logger.info(f"每日状态刷新: 已重置 {count} 名外委人员为空闲")
            today = now
        # 距离明天0点的秒数 + 60秒缓冲
        tomorrow = date.today() + timedelta(days=1)
        sleep_seconds = (tomorrow - date.today()).total_seconds() + 60
        await asyncio.sleep(min(sleep_seconds, 3600))  # 最多每小时检查一次


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_data()
    except Exception as e:
        logger.warning(f"Database initialization failed (some features may be unavailable): {e}")
    reset_task = asyncio.create_task(_daily_staff_reset())
    yield
    reset_task.cancel()
    try:
        await reset_task
    except asyncio.CancelledError:
        pass
    await Tortoise.close_connections()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_TITLE,
        description=settings.APP_DESCRIPTION,
        version=settings.VERSION,
        openapi_url="/openapi.json",
        middleware=make_middlewares(),
        lifespan=lifespan,
    )
    register_exceptions(app)
    register_routers(app, prefix="/api")
    # 挂载上传目录
    uploads_path = os.path.join(os.path.dirname(__file__), "static", "uploads")
    os.makedirs(uploads_path, exist_ok=True)
    app.mount("/uploads", StaticFiles(directory=uploads_path), name="uploads")

    return app


app = create_app()
