"""车辆管理 - Pydantic Schemas"""
from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class VehicleBase(BaseModel):
    """车辆基础字段 — 所有字段可选以适应多数据源"""

    vn: Optional[str] = Field(None, description="车辆VN")
    vehicle_code: Optional[str] = Field(None, description="车辆编号")
    vehicle_model: Optional[str] = Field(None, description="车型项目")
    power_type: Optional[str] = Field(None, description="动力类型")
    color: Optional[str] = Field(None, description="颜色")
    has_controlled_items: Optional[str] = Field(None, description="是否有管制物品")
    borrower: Optional[str] = Field(None, description="借用人")
    borrow_expire_date: Optional[date] = Field(None, description="借用到期时间")
    temp_plate_expire_date: Optional[date] = Field(None, description="临牌到期时间")
    insurance_area: Optional[str] = Field(None, description="保险区域")
    test_date: Optional[date] = Field(None, description="试验日期")
    task_status: Optional[str] = Field(None, description="任务状态")
    test_task: Optional[str] = Field(None, description="试验任务")
    tester: Optional[str] = Field(None, description="测试人员")
    driver: Optional[str] = Field(None, description="驾驶人员")
    travel_status: Optional[str] = Field(None, description="出差状态")
    test_city: Optional[str] = Field(None, description="试验城市")
    exit_permit: Optional[str] = Field(None, description="出门单")
    parking_spot: Optional[str] = Field(None, description="停车位")
    location_info: Optional[str] = Field(None, description="位置信息")
    latitude: Optional[float] = Field(None, description="纬度")
    longitude: Optional[float] = Field(None, description="经度")
    data_source: Optional[str] = Field(default="manual", description="数据来源")


class VehicleCreate(VehicleBase):
    """创建车辆"""
    pass


class VehicleUpdate(BaseModel):
    """更新车辆"""

    id: int
    vn: Optional[str] = Field(None)
    vehicle_code: Optional[str] = Field(None)
    vehicle_model: Optional[str] = Field(None)
    power_type: Optional[str] = Field(None)
    color: Optional[str] = Field(None)
    has_controlled_items: Optional[str] = Field(None)
    borrower: Optional[str] = Field(None)
    borrow_expire_date: Optional[date] = Field(None)
    temp_plate_expire_date: Optional[date] = Field(None)
    insurance_area: Optional[str] = Field(None)
    test_date: Optional[date] = Field(None)
    task_status: Optional[str] = Field(None)
    test_task: Optional[str] = Field(None)
    tester: Optional[str] = Field(None)
    driver: Optional[str] = Field(None)
    travel_status: Optional[str] = Field(None)
    test_city: Optional[str] = Field(None)
    exit_permit: Optional[str] = Field(None)
    parking_spot: Optional[str] = Field(None)
    location_info: Optional[str] = Field(None)
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)
    data_source: Optional[str] = Field(None)


class VehicleUpsert(VehicleBase):
    pass


class VehicleExpiringQuery(BaseModel):
    type: str = Field(default="temp_plate", description="提醒类型: temp_plate | borrow")


class FeishuSyncConfig(BaseModel):
    app_id: str = Field("")
    app_secret: str = Field("")
    base_id: str = Field("")
    table_id: str = Field("")
