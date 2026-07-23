from fastapi import APIRouter
from .mapway import router


mapway_router = APIRouter()
mapway_router.include_router(router, tags=["测试线路管理"])


__all__ = ["mapway_router"]
