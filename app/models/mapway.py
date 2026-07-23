from tortoise import fields
from .base import BaseModel, TimestampMixin

class Mapway(BaseModel, TimestampMixin):
    """
    泛化路线模型，定义地点表结构。
    """
    # name = fields.CharField(max_length=50, unique=True, description="泛化路线管理")
    area = fields.CharField(max_length=255, null=True, description="泛化区域")
    # areaid = fields.IntField(null=True, description="区域ID")
    city = fields.TextField(description="城市列表（逗号分隔）")
    # 可以根据需要继续添加字段
    project_type = fields.CharField(max_length=32, default="cooperative", index=True,
        description="项目类型: cooperative(合作项目) / self_developed(自研)")

    class Meta:
        table = "mapwaytable" # 数据库中的表名
        table_description = "区域数据表"



class RouteDetail(BaseModel, TimestampMixin):
    """城市测试路线详情"""
    city = fields.CharField(max_length=64, description="城市名称", index=True)
    recommend_days = fields.CharField(max_length=32, null=True, description="推荐测试天数")
    route_order = fields.CharField(max_length=32, null=True, description="路线序号")
    priority = fields.CharField(max_length=32, null=True, description="优先级")
    author = fields.CharField(max_length=64, null=True, description="编写人")
    route_type = fields.CharField(max_length=64, null=True, description="路线类型")
    mileage = fields.CharField(max_length=32, null=True, description="路线里程数")
    duration = fields.CharField(max_length=32, null=True, description="路线时长")
    waypoints = fields.TextField(null=True, description="途经点信息")
    # route_image = fields.CharField(max_length=500, null=True, description="路线示意图URL")
    route_image = fields.TextField(null=True, description="路线示意图URL")
    route_preference = fields.CharField(max_length=64, null=True, description="路线偏好")
    near_store = fields.CharField(max_length=16, null=True, description="是否通过门店附近")
    merge_in_num = fields.IntField(null=True, description="汇入匝道个数")
    merge_out_num = fields.IntField(null=True, description="汇出匝道个数")
    y_intersection_num = fields.IntField(null=True, description="Y型路口个数")
    roundabout_num = fields.IntField(null=True, description="环岛个数")
    u_turn_num = fields.IntField(null=True, description="掉头次数")
    straight_intersection_num = fields.IntField(null=True, description="直行路口个数")
    protected_left_num = fields.IntField(null=True, description="有保护左转路口个数")
    unprotected_left_num = fields.IntField(null=True, description="无保护左转路口个数")
    protected_right_num = fields.IntField(null=True, description="有保护右转路口个数")
    unprotected_right_num = fields.IntField(null=True, description="无保护右转路口个数")
    normal_traffic_light_num = fields.IntField(null=True, description="正常红绿灯个数")
    flashing_yellow_num = fields.IntField(null=True, description="黄灯常闪或常亮个数")
    disabled_traffic_light_num = fields.IntField(null=True, description="未启用红绿灯个数")
    special_traffic_light_num = fields.IntField(null=True, description="特殊红绿灯个数")
    main_side_switch_num = fields.IntField(null=True, description="主辅路切换个数")
    right_turn_lane_num = fields.IntField(null=True, description="右转专用道个数")
    variable_lane_num = fields.IntField(null=True, description="可变车道个数")
    waiting_lane_num = fields.IntField(null=True, description="待转车道个数")
    complexity = fields.CharField(max_length=32, null=True, description="路线复杂程度")
    remark = fields.CharField(max_length=500, null=True, description="备注")
    class Meta:
        table = "route_detail"

class RouteDetailSelfDeveloped(BaseModel, TimestampMixin):
    """自研项目 - 城市测试路线详情"""
    city = fields.CharField(max_length=64, description="城市名称", index=True)
    route_code = fields.CharField(max_length=32, null=True, description="路线编号")
    recommend_dimension = fields.CharField(max_length=8, null=True, description="推荐维度: 高/中/低")
    route_type = fields.CharField(max_length=8, null=True, description="路线类型: HNOA/CNOA/LCC")
    route_link = fields.TextField(null=True, description="路线链接")
    baidu_map_screenshot = fields.TextField(null=True, description="百度地图截图")
    mileage = fields.CharField(max_length=32, null=True, description="里程KM")
    start_point = fields.CharField(max_length=128, null=True, description="起点")
    end_point = fields.CharField(max_length=128, null=True, description="终点")
    toll_station = fields.IntField(null=True, description="收费站个数")
    service_area = fields.IntField(null=True, description="服务区个数")
    ramp = fields.IntField(null=True, description="匝道个数")
    construction_scene = fields.IntField(null=True, description="施工场景个数")

    class Meta:
        table = "route_detail_self_developed"
        table_description = "自研项目 - 城市测试路线详情表"