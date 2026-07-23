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

    async def upsert_by_vn(self, obj_in: VehicleCreate) -> Vehicle:
        """根据VN去重，存在则更新，不存在则创建（核心方法）"""
        existing = await self.get_by_vn(obj_in.vn)
        if existing:
            obj_dict = obj_in.model_dump(exclude_unset=False)
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
            q &= Q(vn__contains=keyword) | Q(vehicle_code__contains=keyword) | Q(vehicle_model__contains=keyword) | Q(borrower__contains=keyword)

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


vehicle_controller = VehicleController()
