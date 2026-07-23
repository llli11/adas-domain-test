from fastapi import APIRouter

from app.controllers.target import router as target_controller_router

target_api_router = APIRouter()
target_api_router.include_router(target_controller_router, prefix="", tags=["基线管理"])