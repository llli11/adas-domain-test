from contextlib import asynccontextmanager
import os

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

# UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "static", "uploads")
# os.makedirs(UPLOAD_DIR, exist_ok=True)
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_data()
    except Exception as e:
        logger.warning(f"Database initialization failed (some features may be unavailable): {e}")
    yield
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
	
	# 挂载静态文件
    web_dist_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "web", "dist")
    app.mount("/", StaticFiles(directory=web_dist_path, html=True), name="web")
	
	# app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")
    
    return app


app = create_app()