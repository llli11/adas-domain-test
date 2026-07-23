from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, time, datetime
from decimal import Decimal


class ExpenseProjectCreate(BaseModel):
    series_name: Optional[str] = Field(None, description="系列名称")
    project_name: str = Field(..., description="项目名称")
    category: Optional[str] = Field("自研", description="类别：自研/合作")
    engineer: Optional[str] = Field(None, description="工程师")
    driver: Optional[str] = Field(None, description="驾驶员")
    approver: Optional[str] = Field(None, description="审批人")
    remark: Optional[str] = Field(None, description="备注")


class ExpenseProjectUpdate(BaseModel):
    series_name: Optional[str] = Field(None, description="系列名称")
    project_name: Optional[str] = Field(None, description="项目名称")
    category: Optional[str] = Field(None, description="类别：自研/合作")
    engineer: Optional[str] = Field(None, description="工程师")
    driver: Optional[str] = Field(None, description="驾驶员")
    approver: Optional[str] = Field(None, description="审批人")
    remark: Optional[str] = Field(None, description="备注")


class BudgetCodeCreate(BaseModel):
    project_id: int = Field(..., description="项目 ID")
    budget_code: str = Field(..., description="预算号")
    budget_name: Optional[str] = Field(None, description="预算名称")
    budget_amount: float = Field(0, description="预算金额")
    used_amount: float = Field(0, description="已使用金额")
    remark: Optional[str] = Field(None, description="备注")


class BudgetCodeUpdate(BaseModel):
    project_id: Optional[int] = Field(None, description="项目 ID")
    budget_code: Optional[str] = Field(None, description="预算号")
    budget_name: Optional[str] = Field(None, description="预算名称")
    budget_amount: Optional[float] = Field(None, description="预算金额")
    used_amount: Optional[float] = Field(None, description="已使用金额")
    remark: Optional[str] = Field(None, description="备注")


class ExpenseCodeCreate(BaseModel):
    budget_id: int = Field(..., description="预算号 ID")
    expense_code: str = Field(..., description="费用号")
    expense_name: Optional[str] = Field(None, description="费用名称")
    total_amount: float = Field(0, description="总额")
    used_amount: float = Field(0, description="已使用金额")
    responsible_person: Optional[str] = Field(None, description="负责人")
    is_used: bool = Field(False, description="是否已使用")
    remark: Optional[str] = Field(None, description="备注")


class ExpenseCodeUpdate(BaseModel):
    budget_id: Optional[int] = Field(None, description="预算号 ID")
    expense_code: Optional[str] = Field(None, description="费用号")
    expense_name: Optional[str] = Field(None, description="费用名称")
    total_amount: Optional[float] = Field(None, description="总额")
    used_amount: Optional[float] = Field(None, description="已使用金额")
    responsible_person: Optional[str] = Field(None, description="负责人")
    is_used: Optional[bool] = Field(None, description="是否已使用")
    remark: Optional[str] = Field(None, description="备注")


class TestOrderCreate(BaseModel):
    expense_code_id: int = Field(..., description="费用号 ID")
    test_order_no: str = Field(..., description="试验单号")
    test_order_name: Optional[str] = Field(None, description="试验单名称")
    total_price: float = Field(0, description="试验总金额")
    used_amount: float = Field(0, description="已使用金额")
    planned_start_time: Optional[date] = Field(None, description="计划开展时间")
    planned_end_time: Optional[date] = Field(None, description="计划结束时间")
    actual_start_time: Optional[date] = Field(None, description="实际开展时间")
    actual_end_time: Optional[date] = Field(None, description="实际结束时间")
    supplier: Optional[str] = Field(None, description="供应商")
    outsourced_count: int = Field(0, description="委外人数")
    responsible_person: Optional[str] = Field(None, description="负责人")
    is_used: bool = Field(False, description="是否已使用")
    remark: Optional[str] = Field(None, description="备注")


class TestOrderUpdate(BaseModel):
    expense_code_id: Optional[int] = Field(None, description="费用号 ID")
    test_order_no: Optional[str] = Field(None, description="试验单号")
    test_order_name: Optional[str] = Field(None, description="试验单名称")
    total_price: Optional[float] = Field(None, description="试验总金额")
    used_amount: Optional[float] = Field(None, description="已使用金额(实时)")
    settlement_amount: Optional[float] = Field(None, description="结算数据(手动输入)")
    planned_start_time: Optional[date] = Field(None, description="计划开展时间")
    planned_end_time: Optional[date] = Field(None, description="计划结束时间")
    actual_start_time: Optional[date] = Field(None, description="实际开展时间")
    actual_end_time: Optional[date] = Field(None, description="实际结束时间")
    supplier: Optional[str] = Field(None, description="供应商")
    outsourced_count: Optional[int] = Field(None, description="委外人数")
    responsible_person: Optional[str] = Field(None, description="负责人")
    is_used: Optional[bool] = Field(None, description="是否已使用")
    remark: Optional[str] = Field(None, description="备注")


class DailyRecordCreate(BaseModel):
    project_id: int = Field(..., description="项目 ID")
    test_order_id: Optional[int] = Field(None, description="试验单号 ID")
    record_date: date = Field(..., description="日期")
    person_name: str = Field(..., description="人员姓名")
    person_type: str = Field(..., description="人员类型：工程师/驾驶员")
    normal_hours: float = Field(0, description="正常工时")
    overtime_hours: float = Field(0, description="加班工时")
    work_hours: float = Field(0, description="总工时（自动计算）")
    is_overtime: bool = Field(False, description="是否加班")
    travel_status: Optional[str] = Field("未出差", description="出差状态")
    advance_payment: float = Field(0, description="垫付金额")
    total_amount: float = Field(0, description="每日合计")
    approval_status: Optional[str] = Field("待审批", description="审批状态")
    source: Optional[str] = Field("手动", description="数据来源: 手动/飞书")
    remark: Optional[str] = Field(None, description="备注")


class DailyRecordUpdate(BaseModel):
    project_id: Optional[int] = Field(None, description="项目 ID")
    test_order_id: Optional[int] = Field(None, description="试验单号 ID")
    record_date: Optional[date] = Field(None, description="日期")
    person_name: Optional[str] = Field(None, description="人员姓名")
    person_type: Optional[str] = Field(None, description="人员类型：工程师/驾驶员")
    normal_hours: Optional[float] = Field(None, description="正常工时")
    overtime_hours: Optional[float] = Field(None, description="加班工时")
    work_hours: Optional[float] = Field(None, description="总工时")
    is_overtime: Optional[bool] = Field(None, description="是否加班")
    travel_status: Optional[str] = Field(None, description="出差状态")
    advance_payment: Optional[float] = Field(None, description="垫付金额")
    total_amount: Optional[float] = Field(None, description="每日合计")
    approval_status: Optional[str] = Field(None, description="审批状态")
    remark: Optional[str] = Field(None, description="备注")


class RequirementPersonnelCreate(BaseModel):
    test_order_no: str = Field(..., description="试验单号")
    supplier: Optional[str] = Field(None, description="供应商")
    outsourced_personnel: Optional[str] = Field(None, description="委外人员 (逗号分隔)")
    responsible_person: Optional[str] = Field(None, description="负责人")
    requirement_date: Optional[date] = Field(None, description="试验需求通过日期")
    remark: Optional[str] = Field(None, description="备注")


class RequirementPersonnelUpdate(BaseModel):
    test_order_no: Optional[str] = Field(None, description="试验单号")
    supplier: Optional[str] = Field(None, description="供应商")
    outsourced_personnel: Optional[str] = Field(None, description="委外人员 (逗号分隔)")
    responsible_person: Optional[str] = Field(None, description="负责人")
    requirement_date: Optional[date] = Field(None, description="试验需求通过日期")
    remark: Optional[str] = Field(None, description="备注")


class EngineerAttendanceCreate(BaseModel):
    project_id: Optional[int] = Field(None, description="项目 ID")
    test_order_id: Optional[int] = Field(None, description="试验单号 ID")
    record_date: date = Field(..., description="日期")
    person_name: str = Field(..., description="填写人")
    test_task: Optional[str] = Field(None, description="试验任务")
    car_number: Optional[str] = Field(None, description="车辆编号")
    start_time: Optional[str] = Field(None, description="上班时间")
    end_time: Optional[str] = Field(None, description="下班时间")
    is_overtime: bool = Field(False, description="是否加班")
    overtime_hours: float = Field(0, description="加班时长")
    work_duration: float = Field(0, description="工作日时长")
    total_hours: float = Field(0, description="总工时")
    travel_status: Optional[str] = Field(None, description="出差状态")
    work_location: Optional[str] = Field(None, description="工作地点")
    location_coords: Optional[str] = Field(None, description="定位位置")
    workload: Optional[str] = Field(None, description="工作量")
    problems_found: int = Field(0, description="发现问题数")
    check_cases: int = Field(0, description="点检用例数")
    software_flash_count: int = Field(0, description="刷写软件数")
    approver1: Optional[str] = Field(None, description="审批人 1")
    approver1_result: Optional[str] = Field(None, description="审批人 1 结果")
    approver2: Optional[str] = Field(None, description="审批人 2")
    approver2_result: Optional[str] = Field(None, description="审批人 2 结果")
    issue_detail: Optional[str] = Field(None, description="问题明细")
    test_version: Optional[str] = Field(None, description="试验版本")
    attachment_url: Optional[str] = Field(None, description="附件")
    approve_type: Optional[str] = Field(None, description="审批类型")
    task_status: Optional[str] = Field("待审批", description="任务状态")


class EngineerAttendanceUpdate(EngineerAttendanceCreate):
    pass


class DriverAttendanceCreate(BaseModel):
    project_id: Optional[int] = Field(None, description="项目 ID")
    test_order_id: Optional[int] = Field(None, description="试验单号 ID")
    record_date: date = Field(..., description="日期")
    person_name: str = Field(..., description="填写人")
    requirement_code: Optional[str] = Field(None, description="试验需求编号")
    expense_settle_project: Optional[str] = Field(None, description="垫付费用结算项目")
    test_version: Optional[str] = Field(None, description="试验版本")
    test_task: Optional[str] = Field(None, description="试验任务")
    car_number: Optional[str] = Field(None, description="车辆编号")
    start_time: Optional[str] = Field(None, description="上班时间")
    end_time: Optional[str] = Field(None, description="下班时间")
    is_overtime: Optional[str] = Field("否", description="是否加班")
    work_duration: float = Field(0, description="工作日时长")
    overtime_hours: float = Field(0, description="加班时长")
    total_hours: float = Field(0, description="总工时")
    travel_status: Optional[str] = Field(None, description="出差状态")
    work_location: Optional[str] = Field(None, description="工作地点")
    location_coords: Optional[str] = Field(None, description="定位位置")
    vehicle_initial_mileage: Optional[float] = Field(None, description="车辆初始里程")
    vehicle_end_mileage: Optional[float] = Field(None, description="车辆结束里程")
    vehicle_test_mileage: Optional[float] = Field(None, description="车辆测试里程")
    daily_advance_total: float = Field(0, description="当日垫付费用总计")
    expense_details: Optional[list] = Field(None, description="费用明细")
    attachment_url: Optional[str] = Field(None, description="附件")
    expense_attachment_url: Optional[str] = Field(None, description="垫付费用附件")
    approver1: Optional[str] = Field(None, description="审批人 1")
    approver1_result: Optional[str] = Field(None, description="审批人 1 结果")
    approver2: Optional[str] = Field(None, description="审批人 2")
    approver2_result: Optional[str] = Field("待审批", description="审批人 2 结果")


class DriverAttendanceUpdate(DriverAttendanceCreate):
    pass


class MonthlySettlementCreate(BaseModel):
    year_month: str = Field(..., description="结算月份 YYYY-MM")
    test_order_id: int = Field(..., description="试验单号 ID")
    labor_cost: Decimal = Field(Decimal("0"), description="人工费用")
    advance_payment: Decimal = Field(Decimal("0"), description="垫付费用")
    total_amount: Decimal = Field(Decimal("0"), description="总金额")
    remark: Optional[str] = Field(None, description="备注")


class MonthlySettlementUpdate(MonthlySettlementCreate):
    pass


class SettlementAttachmentCreate(BaseModel):
    settlement_id: int = Field(..., description="结算 ID")
    filename: str = Field(..., description="文件名")
    file_url: str = Field(..., description="文件 URL")


class ExpenseDiffRecordCreate(BaseModel):
    year_month: str = Field(..., description="月份")
    test_order_id: int = Field(..., description="试验单号 ID")
    diff_amount: Decimal = Field(Decimal("0"), description="差异金额")
    diff_reason: Optional[str] = Field(None, description="差异原因")
    status: Optional[str] = Field("待处理", description="状态")
    remark: Optional[str] = Field(None, description="备注")


class ExpenseDiffRecordUpdate(ExpenseDiffRecordCreate):
    pass


# ==================== 供应商单价 ====================
class SupplierRateCreate(BaseModel):
    name: str = Field(..., description="供应商名称")
    local_rate: float = Field(0, description="本地单价")
    trip_rate: float = Field(0, description="出差单价")
    unit: str = Field("hour", description="单位: hour/day")
    effective_from: Optional[date] = Field(None, description="生效起始日期（含）")
    effective_to: Optional[date] = Field(None, description="生效截止日期（含），NULL 表示无截止")
    contract_no: Optional[str] = Field(None, description="合同号")
    code_local: Optional[str] = Field(None, description="未出差服务编号")
    code_trip: Optional[str] = Field(None, description="出差服务编号")


class SupplierRateUpdate(BaseModel):
    name: Optional[str] = Field(None, description="供应商名称")
    local_rate: Optional[float] = Field(None, description="本地单价")
    trip_rate: Optional[float] = Field(None, description="出差单价")
    unit: Optional[str] = Field(None, description="单位: hour/day")
    effective_from: Optional[date] = Field(None, description="生效起始日期（含）")
    effective_to: Optional[date] = Field(None, description="生效截止日期（含），NULL 表示无截止")
    contract_no: Optional[str] = Field(None, description="合同号")
    code_local: Optional[str] = Field(None, description="未出差服务编号")
    code_trip: Optional[str] = Field(None, description="出差服务编号")
