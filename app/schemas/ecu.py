from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel


class EcuInfoCreate(BaseModel):
    vin: str
    ecu_info: Dict[str, Any]


class EcuInfoUpdate(BaseModel):
    vin: str
    ecu_info: Dict[str, Any]


class ReleaseInfoOut(BaseModel):
    id: int
    vin: str
    ecu_info: Optional[Dict[str, Any]] = None
    data_source: str = "vdc_export"
    remark: Optional[str] = None
    modified_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class TargetInfoCreate(BaseModel):
    target_name: str
    ecu_info: Dict[str, Any]


class TargetInfoUpdate(BaseModel):
    target_name: str
    ecu_info: Dict[str, Any]


class OperationLogCreate(BaseModel):
    operation_type: str
    target_vin: Optional[str] = None
    target_name: Optional[str] = None
    operator: Optional[str] = None
