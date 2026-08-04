"""车辆管理 - Controller"""
from datetime import date, datetime, timedelta
from typing import List, Optional, Tuple

from tortoise.expressions import Q

from app.core.crud import CRUDBase
from app.log import logger
from app.models.vehicle import Vehicle
from app.schemas.vehicles import VehicleCreate, VehicleUpdate


class VehicleController(CRUDBase[Vehicle, VehicleCreate, VehicleUpdate]):
    """车辆管理控制器"""

    def __init__(self):
        super().__init__(model=Vehicle)

    async def get_by_vn(self, vn: str) -> Optional[Vehicle]:
        """根据VN查询车辆"""
        return await self.model.filter(vn=vn).first()

    async def create_vehicle(self, obj_in: VehicleCreate) -> Vehicle:
        """创建车辆"""
        return await self.create(obj_in)

    async def update_vehicle(self, id: int, obj_in: VehicleUpdate) -> Vehicle:
        """更新车辆"""
        return await self.update(id, obj_in)

    async def delete_vehicle(self, id: int) -> None:
        """删除车辆"""
        await self.remove(id)

    async def batch_delete(self, ids: List[int]) -> int:
        """批量删除车辆，返回删除数量"""
        count = await self.model.filter(id__in=ids).delete()
        logger.info(f"[Vehicle] 批量删除 {count} 条")
        return count

    async def upsert_by_vn(self, obj_in: VehicleCreate) -> Vehicle:
        """根据VN去重，存在则更新，不存在则创建（核心方法）"""
        existing = await self.get_by_vn(obj_in.vn)
        if existing:
            # exclude_none: 只更新飞书实际返回的字段，不把 null 写入数据库中已有的手动填写数据
            obj_dict = obj_in.model_dump(exclude_none=True)
            existing = existing.update_from_dict(obj_dict)
            await existing.save()
            logger.info(f"[Vehicle] Upsert (update): VN={obj_in.vn}")
            return existing
        else:
            obj = await self.create(obj_in)
            logger.info(f"[Vehicle] Upsert (create): VN={obj_in.vn}")
            return obj

    async def list_with_filter(
        self,
        page: int = 1,
        page_size: int = 20,
        task_status: Optional[str] = None,
        vehicle_model: Optional[str] = None,
        borrower: Optional[str] = None,
        power_type: Optional[str] = None,
        travel_status: Optional[str] = None,
        test_city: Optional[str] = None,
        vn: Optional[str] = None,
        vehicle_code: Optional[str] = None,
        data_source: Optional[str] = None,
        keyword: Optional[str] = None,
        dept_l1: Optional[str] = None,
        dept_l2: Optional[str] = None,
        # 通用字段过滤（字段名+值，最多3组）
        field1: Optional[str] = None,
        value1: Optional[str] = None,
        field2: Optional[str] = None,
        value2: Optional[str] = None,
        field3: Optional[str] = None,
        value3: Optional[str] = None,
        order: Optional[list] = None,
    ) -> Tuple[int, List[Vehicle]]:
        """多条件分页筛选"""
        q = Q()
        if task_status:
            q &= Q(task_status=task_status)
        if vehicle_model:
            q &= Q(vehicle_model=vehicle_model)
        if borrower:
            q &= Q(borrower__contains=borrower)
        if power_type:
            q &= Q(power_type=power_type)
        if travel_status:
            q &= Q(travel_status=travel_status)
        if test_city:
            q &= Q(test_city__contains=test_city)
        if vn:
            q &= Q(vn__contains=vn)
        if vehicle_code:
            q &= Q(vehicle_code__contains=vehicle_code)
        if data_source:
            q &= Q(data_source=data_source)
        if keyword:
            # 多关键词空格分割 → OR 组合（支持 3 个搜索框联动）
            kw_list = [kw.strip() for kw in keyword.split() if kw.strip()]
            keyword_q = Q()
            for kw in kw_list:
                keyword_q |= (
                    Q(vn__contains=kw) | Q(vehicle_code__contains=kw) |
                    Q(vehicle_model__contains=kw) | Q(borrower__contains=kw) |
                    Q(power_type__contains=kw) | Q(color__contains=kw) |
                    Q(task_status__contains=kw) | Q(test_task__contains=kw) |
                    Q(tester__contains=kw) | Q(driver__contains=kw) |
                    Q(travel_status__contains=kw) | Q(test_city__contains=kw) |
                    Q(exit_permit__contains=kw) | Q(parking_spot__contains=kw) |
                    Q(location_info__contains=kw) | Q(insurance_area__contains=kw) |
                    Q(temp_plate_area__contains=kw) | Q(temp_plate_valid_area__contains=kw) |
                    Q(vehicle_status__contains=kw) | Q(vehicle_status_note__contains=kw) |
                    Q(key_location__contains=kw) | Q(vehicle_manager__contains=kw) |
                    Q(vehicle_phase__contains=kw) | Q(vehicle_model_config__contains=kw) |
                    Q(temp_plate_info__contains=kw) | Q(borrower_account__contains=kw) |
                    Q(borrower_phone__contains=kw) | Q(dept_l1__contains=kw) |
                    Q(dept_l2__contains=kw) | Q(province__contains=kw) |
                    Q(city__contains=kw) | Q(address_detail__contains=kw) |
                    Q(monitor_method__contains=kw) | Q(battery_pack_status__contains=kw) |
                    Q(engine_no__contains=kw) | Q(battery_pack_trace__contains=kw) |
                    Q(front_motor_no__contains=kw) | Q(rear_motor_no__contains=kw) |
                    Q(battery_pack_part_no__contains=kw) | Q(battery_pack_rated__contains=kw) |
                    Q(trial_plan__contains=kw) | Q(has_controlled_items__contains=kw) |
                    Q(is_monitored__contains=kw) | Q(is_first_vin_record__contains=kw) |
                    Q(borrow_time__contains=kw) | Q(qr_code__contains=kw)
                )
            q &= keyword_q

        if dept_l1:
            q &= Q(dept_l1=dept_l1)
        if dept_l2:
            q &= Q(dept_l2=dept_l2)

        # 通用字段过滤（字段名+值下拉选择，白名单防注入）
        _ALLOWED = {
            "vn", "vehicle_code", "vehicle_model", "power_type", "color",
            "has_controlled_items", "borrower", "insurance_area", "task_status",
            "test_task", "tester", "driver", "travel_status", "test_city",
            "exit_permit", "parking_spot", "location_info", "temp_plate_area",
            "temp_plate_valid_area", "vehicle_status", "vehicle_status_note",
            "key_location", "vehicle_manager", "vehicle_manager_id",
            "vehicle_phase", "vehicle_model_config", "temp_plate_info",
            "borrower_account", "borrower_id", "borrower_phone", "dept_l1",
            "dept_l2", "province", "city", "address_detail",
            "is_monitored", "monitor_method", "is_first_vin_record",
            "battery_pack_status", "engine_no", "battery_pack_trace",
            "front_motor_no", "rear_motor_no", "battery_pack_part_no",
            "battery_pack_rated", "trial_plan", "trial_plan_id",
            "data_source", "borrow_time", "qr_code",
            "is_under_modification", "feishu_record_id",
        }
        for f_name, f_val in [(field1, value1), (field2, value2), (field3, value3)]:
            if f_name and f_name in _ALLOWED and f_val and f_val.strip():
                q &= Q(**{f"{f_name}__contains": f_val.strip()})

        order_by = order or ["-created_at"]
        total, objs = await self.list(page=page, page_size=page_size, search=q, order=order_by)
        return total, objs

    async def get_expiring_vehicles(
        self,
        alert_type: str = "temp_plate",
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[int, List[Vehicle]]:
        """获取到期提醒车辆列表
        alert_type: temp_plate (临牌到期) | borrow (借用到期)
        """
        today = date.today()
        thirty_days_later = today + timedelta(days=30)
        q = Q()

        if alert_type == "temp_plate":
            # 临牌到期时间不为空，且在30天内（含已过期）
            q &= Q(temp_plate_expire_date__not_isnull=True)
            q &= Q(temp_plate_expire_date__lte=thirty_days_later)
            order = ["temp_plate_expire_date"]
        elif alert_type == "borrow":
            q &= Q(borrow_expire_date__not_isnull=True)
            q &= Q(borrow_expire_date__lte=thirty_days_later)
            order = ["borrow_expire_date"]
        else:
            order = ["-created_at"]

        total, objs = await self.list(page=page, page_size=page_size, search=q, order=order)
        return total, objs

    async def get_status_map_data(self) -> List[Vehicle]:
        """获取车辆任务状态（带位置信息的数据，用于地图展示）"""
        vehicles = await self.model.filter(
            Q(latitude__not_isnull=True) & Q(longitude__not_isnull=True)
        ).all()
        return vehicles

    async def get_vehicles_by_task_status(self) -> dict:
        """按任务状态分组统计"""
        statuses = ["待开始", "空", "进行中", "已完成", "故障或事故"]
        result = {}
        for status in statuses:
            count = await self.model.filter(task_status=status).count()
            result[status] = count
        return result

    async def get_field_distinct_values(
        self, field_name: str, keyword: Optional[str] = None, limit: int = 50
    ) -> List[str]:
        """获取某字段的去重值列表（下拉联想用），支持关键字过滤"""
        # 白名单：只允许查询 Vehicle 模型上的字段
        allowed_fields = {
            "vn", "vehicle_code", "vehicle_model", "power_type", "color",
            "has_controlled_items", "borrower", "insurance_area", "task_status",
            "test_task", "tester", "driver", "travel_status", "test_city",
            "exit_permit", "parking_spot", "location_info", "temp_plate_area",
            "temp_plate_valid_area", "vehicle_status", "vehicle_status_note",
            "key_location", "vehicle_manager", "vehicle_manager_id",
            "vehicle_phase", "vehicle_model_config", "temp_plate_info",
            "borrower_account", "borrower_id", "borrower_phone", "dept_l1",
            "dept_l2", "province", "city", "address_detail",
            "is_monitored", "monitor_method", "is_first_vin_record",
            "battery_pack_status", "engine_no", "battery_pack_trace",
            "front_motor_no", "rear_motor_no", "battery_pack_part_no",
            "battery_pack_rated", "trial_plan", "trial_plan_id",
            "data_source", "borrow_time", "qr_code",
            "is_under_modification", "feishu_record_id",
        }
        if field_name not in allowed_fields:
            logger.warning(f"[Vehicle] 非法字段查询: {field_name}")
            return []

        qs = self.model.filter(**{f"{field_name}__not_isnull": True})
        if keyword:
            qs = qs.filter(**{f"{field_name}__contains": keyword})

        records = await qs.limit(limit * 5).values(field_name)
        values = sorted(set(
            str(r[field_name]) for r in records
            if r[field_name] is not None and str(r[field_name]).strip()
        ))
        return values[:limit]


vehicle_controller = VehicleController()
