from tortoise.expressions import Q

from app.core.crud import CRUDBase
from app.models.expense import (
    ExpenseProject, BudgetCode, ExpenseCode, TestOrder,
    DailyRecord, MonthlySettlement, SettlementAttachment, ExpenseDiffRecord,
    RequirementPersonnel, EngineerAttendance, DriverAttendance,
    SupplierRate,
)
from app.schemas.expense import (
    ExpenseProjectCreate, ExpenseProjectUpdate,
    BudgetCodeCreate, BudgetCodeUpdate,
    ExpenseCodeCreate, ExpenseCodeUpdate,
    TestOrderCreate, TestOrderUpdate,
    DailyRecordCreate, DailyRecordUpdate,
    RequirementPersonnelCreate, RequirementPersonnelUpdate,
    EngineerAttendanceCreate, EngineerAttendanceUpdate,
    DriverAttendanceCreate, DriverAttendanceUpdate,
    SupplierRateCreate, SupplierRateUpdate,
    MonthlySettlementCreate, MonthlySettlementUpdate,
)


class ExpenseProjectController(CRUDBase[ExpenseProject, ExpenseProjectCreate, ExpenseProjectUpdate]):
    def __init__(self):
        super().__init__(model=ExpenseProject)

    async def search(self, series_name=None, project_name=None, category=None):
        q = Q()
        if series_name: q &= Q(series_name__contains=series_name)
        if project_name: q &= Q(project_name__contains=project_name)
        if category: q &= Q(category=category)
        return await self.model.filter(q).order_by("-id")


expense_project_controller = ExpenseProjectController()


class BudgetCodeController(CRUDBase[BudgetCode, BudgetCodeCreate, BudgetCodeUpdate]):
    def __init__(self):
        super().__init__(model=BudgetCode)

    async def search(self, project_id=None, budget_code=None):
        q = Q()
        if project_id: q &= Q(project_id=project_id)
        if budget_code: q &= Q(budget_code__contains=budget_code)
        return await self.model.filter(q).prefetch_related("project").order_by("-id")


budget_code_controller = BudgetCodeController()


class ExpenseCodeController(CRUDBase[ExpenseCode, ExpenseCodeCreate, ExpenseCodeUpdate]):
    def __init__(self):
        super().__init__(model=ExpenseCode)

    async def search(self, budget_id=None, expense_code=None, responsible_person=None):
        q = Q()
        if budget_id: q &= Q(budget_id=budget_id)
        if expense_code: q &= Q(expense_code__contains=expense_code)
        if responsible_person: q &= Q(responsible_person__contains=responsible_person)
        return await self.model.filter(q).prefetch_related("budget").order_by("-id")


expense_code_controller = ExpenseCodeController()


class TestOrderController(CRUDBase[TestOrder, TestOrderCreate, TestOrderUpdate]):
    def __init__(self):
        super().__init__(model=TestOrder)

    async def search(self, expense_code_id=None, test_order_no=None, is_used=None, responsible_person=None, project_id=None, project_keyword=None):
        q = Q()
        if expense_code_id: q &= Q(expense_code_id=expense_code_id)
        if test_order_no: q &= Q(test_order_no__contains=test_order_no)
        if project_keyword: q &= Q(test_order_no__startswith=project_keyword)
        if is_used is not None: q &= Q(is_used=is_used)
        if responsible_person: q &= Q(responsible_person__contains=responsible_person)
        if project_id:
            from app.models.expense import ExpenseCode
            code_ids = await ExpenseCode.filter(budget__project_id=project_id).values_list("id", flat=True)
            q &= Q(expense_code_id__in=code_ids)
        return await self.model.filter(q).prefetch_related("expense_code").order_by("-id")


test_order_controller = TestOrderController()


class DailyRecordController(CRUDBase[DailyRecord, DailyRecordCreate, DailyRecordUpdate]):
    def __init__(self):
        super().__init__(model=DailyRecord)

    async def search(self, project_id=None, test_order_id=None, person_name=None, person_type=None,
                     record_date_start=None, record_date_end=None):
        q = Q()
        if project_id: q &= Q(project_id=project_id)
        if test_order_id: q &= Q(test_order_id=test_order_id)
        if person_name: q &= Q(person_name__contains=person_name)
        if person_type: q &= Q(person_type=person_type)
        if record_date_start: q &= Q(record_date__gte=record_date_start)
        if record_date_end: q &= Q(record_date__lte=record_date_end)
        return await self.model.filter(q).prefetch_related("project", "test_order").order_by("-record_date")

    async def create(self, obj_in, upsert: bool = False):
        """
        创建每日记录，自动去重。
        upsert=True：存在则更新，不存在则创建。
        upsert=False（默认）：存在则跳过，返回已有记录。
        
        去重规则：按 (project_id, test_order_id, record_date, person_name) 判断重复。
        为避免 NULL test_order_id 导致多条记录（MySQL UNIQUE 对 NULL 视为不同值），
        使用应用层去重。
        """
        from tortoise.expressions import Q as TQ
        from datetime import date as dt_date

        if isinstance(obj_in, dict):
            proj_id = obj_in.get("project_id")
            to_id = obj_in.get("test_order_id")
            rec_date = obj_in.get("record_date")
            pname = obj_in.get("person_name")
        else:
            proj_id = obj_in.project_id
            to_id = getattr(obj_in, "test_order_id", None)
            rec_date = obj_in.record_date
            pname = obj_in.person_name

        # 构建去重查询条件
        dedup_q = TQ(project_id=proj_id, record_date=rec_date, person_name=pname)
        if to_id is not None:
            dedup_q &= TQ(test_order_id=to_id)
        else:
            dedup_q &= TQ(test_order_id__isnull=True)

        existing = await self.model.filter(dedup_q).first()
        if existing:
            if upsert:
                if isinstance(obj_in, dict):
                    await existing.update_from_dict(obj_in).save()
                else:
                    update_dict = obj_in.model_dump(exclude_unset=True)
                    await existing.update_from_dict(update_dict).save()
            return existing

        return await super().create(obj_in=obj_in)


daily_record_controller = DailyRecordController()


class MonthlySettlementController(CRUDBase[MonthlySettlement, MonthlySettlementCreate, MonthlySettlementUpdate]):
    def __init__(self):
        super().__init__(model=MonthlySettlement)

    async def search(self, year_month=None, status=None, test_order_id=None):
        q = Q()
        if year_month: q &= Q(year_month=year_month)
        if status: q &= Q(status=status)
        if test_order_id: q &= Q(test_order_id=test_order_id)
        return await self.model.filter(q).prefetch_related("test_order").order_by("-year_month")


monthly_settlement_controller = MonthlySettlementController()


class RequirementPersonnelController(CRUDBase[RequirementPersonnel, RequirementPersonnelCreate, RequirementPersonnelUpdate]):
    def __init__(self):
        super().__init__(model=RequirementPersonnel)

    async def search(self, test_order_no=None, supplier=None, responsible_person=None, has_outsourced=None, outsourced_personnel=None):
        q = Q()
        if test_order_no: q &= Q(test_order_no__contains=test_order_no)
        if supplier: q &= Q(supplier__contains=supplier)
        if responsible_person: q &= Q(responsible_person__contains=responsible_person)
        if outsourced_personnel: q &= Q(outsourced_personnel__contains=outsourced_personnel)
        if has_outsourced == 'true': q &= ~Q(outsourced_personnel='') & Q(outsourced_personnel__isnull=False)
        return await self.model.filter(q).order_by("-id")


requirement_personnel_controller = RequirementPersonnelController()


class EngineerAttendanceController(CRUDBase[EngineerAttendance, EngineerAttendanceCreate, EngineerAttendanceUpdate]):
    def __init__(self):
        super().__init__(model=EngineerAttendance)

    async def create(self, obj_in):
        if isinstance(obj_in, dict):
            return await self.model.create(**obj_in)
        return await super().create(obj_in=obj_in)


engineer_attendance_controller = EngineerAttendanceController()


class DriverAttendanceController(CRUDBase[DriverAttendance, DriverAttendanceCreate, DriverAttendanceUpdate]):
    def __init__(self):
        super().__init__(model=DriverAttendance)

    async def create(self, obj_in):
        if isinstance(obj_in, dict):
            return await self.model.create(**obj_in)
        return await super().create(obj_in=obj_in)


driver_attendance_controller = DriverAttendanceController()


class SupplierRateController(CRUDBase[SupplierRate, SupplierRateCreate, SupplierRateUpdate]):
    def __init__(self):
        super().__init__(model=SupplierRate)


supplier_rate_controller = SupplierRateController()
