"""车辆管理 - Pydantic Schemas"""
from datetime import date
from typing import Optional

from pydantic import BaseModel, Field


class VehicleBase(BaseModel):
    """车辆基础字段 — 所有字段可选以适应多数据源"""
    model_config = {"extra": "ignore"}

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
    temp_plate_area: Optional[str] = Field(None, description="临牌区域")
    temp_plate_valid_area: Optional[str] = Field(None, description="临牌有效区域")
    borrower_7day_rate: Optional[float] = Field(None, description="当前借用人7日利用率(%)")
    vehicle_status: Optional[str] = Field(None, description="车辆状态")
    vehicle_status_note: Optional[str] = Field(None, description="车辆状态备注")
    key_location: Optional[str] = Field(None, description="钥匙位置")
    vehicle_manager: Optional[str] = Field(None, description="车管")
    vehicle_manager_id: Optional[str] = Field(None, description="车管ID")
    borrow_days: Optional[int] = Field(None, description="借用天数")
    borrow_time: Optional[str] = Field(None, description="借车时间")
    vehicle_phase: Optional[str] = Field(None, description="车辆阶段")
    vehicle_model_config: Optional[str] = Field(None, description="车型配置")
    temp_plate_info: Optional[str] = Field(None, description="临牌信息")
    temp_plate_insurance_count: Optional[int] = Field(None, description="临牌&保险办理次数")
    borrower_account: Optional[str] = Field(None, description="借车人账号")
    borrower_id: Optional[str] = Field(None, description="借车人ID")
    borrower_phone: Optional[str] = Field(None, description="电话")
    dept_l1: Optional[str] = Field(None, description="一级部门")
    dept_l2: Optional[str] = Field(None, description="二级部门")
    storage_days: Optional[int] = Field(None, description="在库时长")
    qr_code: Optional[str] = Field(None, description="二维码")
    province: Optional[str] = Field(None, description="车辆所在省")
    city: Optional[str] = Field(None, description="车辆所在市")
    address_detail: Optional[str] = Field(None, description="详细地址")
    is_monitored: Optional[str] = Field(None, description="是否监控")
    monitor_method: Optional[str] = Field(None, description="监控方式")
    is_first_vin_record: Optional[str] = Field(None, description="是否VIN最早记录")
    battery_pack_status: Optional[str] = Field(None, description="电池包状态")
    engine_no: Optional[str] = Field(None, description="发动机号")
    battery_pack_trace: Optional[str] = Field(None, description="电池包溯源码")
    front_motor_no: Optional[str] = Field(None, description="前电机号")
    rear_motor_no: Optional[str] = Field(None, description="后电机号")
    battery_pack_part_no: Optional[str] = Field(None, description="电池包零件号")
    battery_pack_rated: Optional[str] = Field(None, description="电池包额定电量")
    trial_plan: Optional[str] = Field(None, description="试验策划")
    trial_plan_id: Optional[str] = Field(None, description="试验策划ID")
    is_under_modification: Optional[str] = Field(None, description="改制中")
    feishu_record_id: Optional[str] = Field(None, description="飞书记录ID")


class VehicleCreate(VehicleBase):
    """创建车辆"""
    pass


class VehicleUpdate(BaseModel):
    """更新车辆"""
    model_config = {"extra": "ignore"}

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
    temp_plate_area: Optional[str] = Field(None)
    temp_plate_valid_area: Optional[str] = Field(None)
    borrower_7day_rate: Optional[float] = Field(None)
    vehicle_status: Optional[str] = Field(None)
    vehicle_status_note: Optional[str] = Field(None)
    key_location: Optional[str] = Field(None)
    vehicle_manager: Optional[str] = Field(None)
    vehicle_manager_id: Optional[str] = Field(None)
    borrow_days: Optional[int] = Field(None)
    borrow_time: Optional[str] = Field(None)
    vehicle_phase: Optional[str] = Field(None)
    vehicle_model_config: Optional[str] = Field(None)
    temp_plate_info: Optional[str] = Field(None)
    temp_plate_insurance_count: Optional[int] = Field(None)
    borrower_account: Optional[str] = Field(None)
    borrower_id: Optional[str] = Field(None)
    borrower_phone: Optional[str] = Field(None)
    dept_l1: Optional[str] = Field(None)
    dept_l2: Optional[str] = Field(None)
    storage_days: Optional[int] = Field(None)
    qr_code: Optional[str] = Field(None)
    province: Optional[str] = Field(None)
    city: Optional[str] = Field(None)
    address_detail: Optional[str] = Field(None)
    is_monitored: Optional[str] = Field(None)
    monitor_method: Optional[str] = Field(None)
    is_first_vin_record: Optional[str] = Field(None)
    battery_pack_status: Optional[str] = Field(None)
    engine_no: Optional[str] = Field(None)
    battery_pack_trace: Optional[str] = Field(None)
    front_motor_no: Optional[str] = Field(None)
    rear_motor_no: Optional[str] = Field(None)
    battery_pack_part_no: Optional[str] = Field(None)
    battery_pack_rated: Optional[str] = Field(None)
    trial_plan: Optional[str] = Field(None)
    trial_plan_id: Optional[str] = Field(None)
    is_under_modification: Optional[str] = Field(None)
    feishu_record_id: Optional[str] = Field(None)


class VehicleUpsert(VehicleBase):
    """车辆去重导入"""
    model_config = {"extra": "ignore"}


class VehicleExpiringQuery(BaseModel):
    type: str = Field(default="temp_plate", description="提醒类型: temp_plate | borrow")


class FeishuSyncConfig(BaseModel):
    app_id: str = Field("")
    app_secret: str = Field("")
    base_id: str = Field("")
    table_id: str = Field("")
