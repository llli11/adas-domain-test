"""车辆管理 - Vehicle Model"""
from tortoise import fields

from .base import BaseModel, TimestampMixin


class Vehicle(BaseModel, TimestampMixin):
    """车辆信息表"""

    vn = fields.CharField(max_length=50, unique=True, index=True, description="车辆VN（去重主键）")
    vehicle_code = fields.CharField(max_length=50, index=True, description="车辆编号")
    vehicle_model = fields.CharField(max_length=100, description="车型项目")
    power_type = fields.CharField(max_length=50, description="动力类型")
    color = fields.CharField(max_length=50, description="颜色")
    has_controlled_items = fields.CharField(max_length=100, null=True, description="是否有管制物品")
    borrower = fields.CharField(max_length=50, null=True, description="借用人")
    borrow_expire_date = fields.DateField(null=True, description="借用到期时间")
    temp_plate_expire_date = fields.DateField(null=True, description="临牌到期时间")
    insurance_area = fields.CharField(max_length=100, null=True, description="保险区域")
    test_date = fields.DateField(null=True, description="试验日期")
    task_status = fields.CharField(max_length=50, null=True, description="任务状态")
    test_task = fields.CharField(max_length=100, null=True, description="试验任务")
    tester = fields.CharField(max_length=50, null=True, description="测试人员")
    driver = fields.CharField(max_length=50, null=True, description="驾驶人员")
    travel_status = fields.CharField(max_length=50, null=True, description="出差状态")
    test_city = fields.CharField(max_length=100, null=True, description="试验城市")
    exit_permit = fields.CharField(max_length=100, null=True, description="出门单")
    parking_spot = fields.CharField(max_length=100, null=True, description="停车位")
    location_info = fields.CharField(max_length=255, null=True, description="位置信息")
    latitude = fields.FloatField(null=True, description="纬度")
    longitude = fields.FloatField(null=True, description="经度")
    data_source = fields.CharField(max_length=50, default="manual", description="数据来源")

    class Meta:
        table = "vehicle"
