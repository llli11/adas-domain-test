from fastapi import APIRouter

from app.controllers.ecu import router as ecu_router

ecu_api_router = APIRouter()
ecu_api_router.include_router(ecu_router, prefix="", tags=["ECU管理"])