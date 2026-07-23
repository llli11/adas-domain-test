"""车辆管理API路由注册"""
from fastapi import APIRouter

from .vehicles import router

vehicles_router = APIRouter()
vehicles_router.include_router(router, tags=["车辆管理"])

__all__ = ["vehicles_router"]
