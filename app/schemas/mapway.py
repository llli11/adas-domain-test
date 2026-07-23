from typing import Optional, List, Union
from pydantic import BaseModel, Field

class MapwayBase(BaseModel):
    """创建请求体校验"""
    # id: int
    area: Optional[str] = Field(..., description="泛化区域", max_length=100)
    city: Optional[str] = Field(..., description="泛化城市", max_length=100)
    project_type: str = Field(default="cooperative", description="项目类型")

# 创建区域请求体
class MapwayCreate(MapwayBase):
    pass

# 更新区域请求体
class MapwayUpdate(MapwayBase):
    id: int
    # area: Optional[str] = Field(None, description="区域名称", max_length=50)
    # city: Optional[str] = Field(None, description="城市列表，逗号分隔")


class RouteDetailBase(BaseModel):
    city: str = Field(..., description="城市名称")
    recommend_days: Optional[str] = None
    route_order: Optional[str] = None
    priority: Optional[str] = None
    author: Optional[str] = None
    route_type: Optional[str] = None
    mileage: Optional[str] = None
    duration: Optional[str] = None
    waypoints: Optional[str] = None
    route_image: Optional[str] = None
    route_preference: Optional[str] = None
    near_store: Optional[str] = None
    merge_in_num: Optional[int] = None
    merge_out_num: Optional[int] = None
    y_intersection_num: Optional[int] = None
    roundabout_num: Optional[int] = None
    u_turn_num: Optional[int] = None
    straight_intersection_num: Optional[int] = None
    protected_left_num: Optional[int] = None
    unprotected_left_num: Optional[int] = None
    protected_right_num: Optional[int] = None
    unprotected_right_num: Optional[int] = None
    normal_traffic_light_num: Optional[int] = None
    flashing_yellow_num: Optional[int] = None
    disabled_traffic_light_num: Optional[int] = None
    special_traffic_light_num: Optional[int] = None
    main_side_switch_num: Optional[int] = None
    right_turn_lane_num: Optional[int] = None
    variable_lane_num: Optional[int] = None
    waiting_lane_num: Optional[int] = None
    complexity: Optional[str] = None
    remark: Optional[str] = None

class RouteDetailCreate(RouteDetailBase):
    pass

class RouteDetailUpdate(BaseModel):
    id: int
    city: Optional[str] = None          # 可选，一般不修改
    recommend_days: Optional[str] = None
    route_order: Optional[str] = None
    priority: Optional[str] = None
    author: Optional[str] = None
    route_type: Optional[str] = None
    mileage: Optional[str] = None
    duration: Optional[str] = None
    waypoints: Optional[str] = None
    # route_image: Optional[str] = None
    route_image: Optional[Union[str, List[str]]] = None  # 支持单个字符串或字符串列表
    route_preference: Optional[str] = None
    near_store: Optional[str] = None
    merge_in_num: Optional[int] = None
    merge_out_num: Optional[int] = None
    y_intersection_num: Optional[int] = None
    roundabout_num: Optional[int] = None
    u_turn_num: Optional[int] = None
    straight_intersection_num: Optional[int] = None
    protected_left_num: Optional[int] = None
    unprotected_left_num: Optional[int] = None
    protected_right_num: Optional[int] = None
    unprotected_right_num: Optional[int] = None
    normal_traffic_light_num: Optional[int] = None
    flashing_yellow_num: Optional[int] = None
    disabled_traffic_light_num: Optional[int] = None
    special_traffic_light_num: Optional[int] = None
    main_side_switch_num: Optional[int] = None
    right_turn_lane_num: Optional[int] = None
    variable_lane_num: Optional[int] = None
    waiting_lane_num: Optional[int] = None
    complexity: Optional[str] = None
    remark: Optional[str] = None

class RouteDetailOut(RouteDetailBase):
    id: int
    # created_at: datetime
    # updated_at: datetime
    class Config:
        from_attributes = True

# ===================== 自研项目 Schema =====================

class RouteDetailSelfDevelopedBase(BaseModel):
    city: str = Field(..., description="城市名称")
    route_code: Optional[str] = None
    recommend_dimension: Optional[str] = None
    route_type: Optional[str] = None
    route_link: Optional[str] = None
    baidu_map_screenshot: Optional[str] = None
    mileage: Optional[str] = None
    start_point: Optional[str] = None
    end_point: Optional[str] = None
    toll_station: Optional[int] = None
    service_area: Optional[int] = None
    ramp: Optional[int] = None
    construction_scene: Optional[int] = None

class RouteDetailSelfDevelopedCreate(RouteDetailSelfDevelopedBase):
    pass

class RouteDetailSelfDevelopedUpdate(BaseModel):
    id: int
    city: Optional[str] = None
    route_code: Optional[str] = None
    recommend_dimension: Optional[str] = None
    route_type: Optional[str] = None
    route_link: Optional[str] = None
    baidu_map_screenshot: Optional[Union[str, List[str]]] = None
    mileage: Optional[str] = None
    start_point: Optional[str] = None
    end_point: Optional[str] = None
    toll_station: Optional[int] = None
    service_area: Optional[int] = None
    ramp: Optional[int] = None
    construction_scene: Optional[int] = None

class RouteDetailSelfDevelopedOut(RouteDetailSelfDevelopedBase):
    id: int
    class Config:
        from_attributes = True