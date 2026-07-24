"""费用管理模块 - 数据模型"""
from tortoise import fields
from .base import BaseModel, TimestampMixin


class ExpenseProject(BaseModel, TimestampMixin):
    """项目"""
    series_name = fields.CharField(max_length=100, description="系列名称", index=True)
    project_name = fields.CharField(max_length=200, description="项目名称", index=True)
    category = fields.CharField(max_length=50, default="自研", description="类别: 自研/合作")
    engineer = fields.CharField(max_length=50, null=True, description="工程师")
    driver = fields.CharField(max_length=50, null=True, description="驾驶员")
    approver = fields.CharField(max_length=50, null=True, description="审批人")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "expense_project"


class BudgetCode(BaseModel, TimestampMixin):
    """预算号"""
    project = fields.ForeignKeyField("models.ExpenseProject", related_name="budget_codes", description="所属项目")
    budget_code = fields.CharField(max_length=100, unique=True, description="预算号", index=True)
    budget_amount = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="预算金额")
    used_amount = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="已用金额")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "expense_budget_code"


class ExpenseCode(BaseModel, TimestampMixin):
    """费用号"""
    budget = fields.ForeignKeyField("models.BudgetCode", related_name="expense_codes", description="所属预算号")
    expense_code = fields.CharField(max_length=100, unique=True, description="费用号", index=True)
    total_amount = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="费用总金额")
    used_amount = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="已用金额")
    responsible_person = fields.CharField(max_length=50, null=True, description="负责人")
    is_used = fields.BooleanField(default=False, description="是否已结束")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "expense_code"


class TestOrder(BaseModel, TimestampMixin):
    """试验单号"""
    expense_code = fields.ForeignKeyField("models.ExpenseCode", related_name="test_orders", null=True, description="所属费用号")
    test_order_no = fields.CharField(max_length=100, unique=True, description="试验单号", index=True)
    total_price = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="总金额")
    used_amount = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="已使用金额(实时)")
    settlement_amount = fields.DecimalField(max_digits=12, decimal_places=2, null=True, default=None, description="结算数据(手动输入)")
    last_month_used = fields.DecimalField(max_digits=12, decimal_places=2, null=True, default=None, description="截止到上月已使用")
    planned_start_time = fields.DateField(null=True, description="计划开展时间")
    planned_end_time = fields.DateField(null=True, description="计划结束时间")
    actual_start_time = fields.DateField(null=True, description="实际开展时间")
    actual_end_time = fields.DateField(null=True, description="实际结束时间")
    supplier = fields.CharField(max_length=50, null=True, description="供应商")
    outsourced_count = fields.IntField(default=0, description="委外人数")
    responsible_person = fields.CharField(max_length=50, null=True, description="负责人")
    is_used = fields.BooleanField(default=False, description="是否已使用")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "expense_test_order"


class DailyRecord(BaseModel, TimestampMixin):
    """每日费用记录"""
    project = fields.ForeignKeyField("models.ExpenseProject", related_name="daily_records", description="所属项目")
    test_order = fields.ForeignKeyField("models.TestOrder", related_name="daily_records", null=True, description="所属试验单号")
    record_date = fields.DateField(description="日期", index=True)
    person_name = fields.CharField(max_length=50, description="人员姓名")
    person_type = fields.CharField(max_length=20, default="工程师", description="人员类型: 工程师/驾驶员")
    normal_hours = fields.DecimalField(max_digits=5, decimal_places=1, default=0, description="正常工时")
    overtime_hours = fields.DecimalField(max_digits=5, decimal_places=1, default=0, description="加班工时")
    work_hours = fields.DecimalField(max_digits=6, decimal_places=1, default=0, description="总工时(自动计算)")
    is_overtime = fields.BooleanField(default=False, description="是否加班")
    travel_status = fields.CharField(max_length=20, null=True, default="未出差", description="出差状态")
    advance_payment = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description="垫付金额")
    total_amount = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description="合计金额")
    approval_status = fields.CharField(max_length=20, null=True, default="待审批", description="审批状态")
    source_id = fields.IntField(null=True, default=None, description="来源考勤记录ID")
    source_type = fields.CharField(max_length=20, null=True, default=None, description="来源类型: engineer/driver")
    source = fields.CharField(max_length=20, default="手动", description="数据来源: 手动/飞书")
    supplier = fields.CharField(max_length=50, null=True, default=None, description="供应商（从人员绑定同步）")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "expense_daily_record"


class MonthlySettlement(BaseModel, TimestampMixin):
    """月度结算"""
    test_order = fields.ForeignKeyField("models.TestOrder", related_name="monthly_settlements", description="所属试验单号")
    year_month = fields.CharField(max_length=7, description="结算月份(YYYY-MM)", index=True)
    labor_cost = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="人工费用")
    advance_payment = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="垫付费用")
    total_amount = fields.DecimalField(max_digits=12, decimal_places=2, default=0, description="总金额")
    status = fields.CharField(max_length=20, default="待比对", description="状态: 待比对/已确认/有差异", index=True)
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "expense_monthly_settlement"


class SettlementAttachment(BaseModel, TimestampMixin):
    """归档材料"""
    settlement = fields.ForeignKeyField("models.MonthlySettlement", related_name="attachments", description="所属结算单")
    attachment_type = fields.CharField(max_length=50, description="材料类型: 考勤表/垫付明细/交付验收单/面试评价表/测试总结")
    file_name = fields.CharField(max_length=200, description="文件名")
    file_url = fields.CharField(max_length=500, description="文件路径")
    upload_time = fields.DatetimeField(auto_now_add=True, description="上传时间")

    class Meta:
        table = "expense_settlement_attachment"


class ExpenseDiffRecord(BaseModel, TimestampMixin):
    """差异记录"""
    settlement = fields.ForeignKeyField("models.MonthlySettlement", related_name="diff_records", description="所属结算单")
    diff_description = fields.TextField(description="差异描述")
    responsible_person = fields.CharField(max_length=50, description="责任人")
    status = fields.CharField(max_length=20, default="待处理", description="状态: 待处理/已处理", index=True)
    handle_time = fields.DatetimeField(null=True, description="处理时间")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "expense_diff_record"


class RequirementPersonnel(BaseModel, TimestampMixin):
    """试验需求与人员关系"""
    test_order_no = fields.CharField(max_length=100, description="试验单号", index=True)
    supplier = fields.CharField(max_length=50, null=True, description="供应商")
    outsourced_count = fields.IntField(default=0, description="委外人数")
    outsourced_personnel = fields.TextField(null=True, description="委外人员姓名（逗号分隔）")
    responsible_person = fields.CharField(max_length=50, null=True, description="负责人")
    requirement_date = fields.DateField(null=True, description="发起试验需求日期")
    start_date = fields.DateField(null=True, description="试验开始日期（从飞书同步）")
    end_date = fields.DateField(null=True, description="试验结束日期（从飞书同步）")

    class Meta:
        table = "expense_requirement_personnel"


class EngineerAttendance(BaseModel, TimestampMixin):
    """工程师考勤打卡"""
    project = fields.ForeignKeyField("models.ExpenseProject", related_name="engineer_attendances", description="所属项目")
    test_order = fields.ForeignKeyField("models.TestOrder", related_name="engineer_attendances", null=True, description="试验单号")
    record_date = fields.DateField(description="日期", index=True)
    person_name = fields.CharField(max_length=50, description="填写人")
    test_task = fields.CharField(max_length=50, null=True, description="试验任务: 行车/泊车/用例点检/车辆整备")
    car_number = fields.CharField(max_length=200, null=True, description="车辆编号")
    start_time = fields.TimeField(null=True, description="上班时间")
    end_time = fields.TimeField(null=True, description="下班时间")
    is_overtime = fields.BooleanField(default=False, description="是否加班")
    overtime_hours = fields.DecimalField(max_digits=4, decimal_places=1, default=0, description="加班时长(h)")
    work_duration = fields.DecimalField(max_digits=4, decimal_places=1, default=0, description="工作日时长(h)")
    total_hours = fields.DecimalField(max_digits=4, decimal_places=1, default=0, description="当天总工时(h)")
    travel_status = fields.CharField(max_length=50, null=True, description="出差状态")
    work_location = fields.CharField(max_length=200, null=True, description="工作地点")
    location_coords = fields.CharField(max_length=100, null=True, description="定位位置")
    workload = fields.CharField(max_length=500, null=True, description="当天工作量(次/km)")
    problems_found = fields.IntField(default=0, description="行车泊车发现问题数")
    check_cases = fields.IntField(default=0, description="点检用例数")
    software_flash_count = fields.IntField(default=0, description="整备车辆刷写软件数量")
    approver1 = fields.CharField(max_length=50, null=True, description="审批人1")
    approver1_result = fields.CharField(max_length=20, null=True, description="审批人1审核结果")
    approver2 = fields.CharField(max_length=50, null=True, description="审批人2")
    approver2_result = fields.CharField(max_length=20, null=True, description="审批人2审核结果")
    issue_detail = fields.TextField(null=True, description="问题明细")
    requirement_code = fields.CharField(max_length=100, null=True, description="试验需求编号")
    test_version = fields.CharField(max_length=100, null=True, description="试验版本")
    attachment_url = fields.CharField(max_length=500, null=True, description="考勤打卡附件")
    approve_type = fields.CharField(max_length=50, null=True, description="审批类型")
    task_status = fields.CharField(max_length=50, null=True, description="任务单状态")

    class Meta:
        table = "expense_engineer_attendance"


class DriverAttendance(BaseModel, TimestampMixin):
    """驾驶员考勤打卡"""
    project = fields.ForeignKeyField("models.ExpenseProject", related_name="driver_attendances", description="所在车型项目")
    test_order = fields.ForeignKeyField("models.TestOrder", related_name="driver_attendances", null=True, description="试验单号")
    record_date = fields.DateField(description="日期", index=True)
    person_name = fields.CharField(max_length=50, description="填写人")
    requirement_code = fields.CharField(max_length=100, null=True, description="试验需求编号")
    expense_settle_project = fields.CharField(max_length=200, null=True, description="垫付费用结算项目")
    test_version = fields.CharField(max_length=100, null=True, description="试验版本")
    test_task = fields.CharField(max_length=50, null=True, description="试验任务")
    car_number = fields.CharField(max_length=200, null=True, description="车辆编号")
    start_time = fields.TimeField(null=True, description="上班时间")
    end_time = fields.TimeField(null=True, description="下班时间")
    is_overtime = fields.CharField(max_length=10, default="否", description="当前是否加班")
    work_duration = fields.DecimalField(max_digits=4, decimal_places=1, default=0, description="当天工作日时长(h)")
    overtime_hours = fields.DecimalField(max_digits=4, decimal_places=1, default=0, description="当前加班时长(h)")
    total_hours = fields.DecimalField(max_digits=4, decimal_places=1, default=0, description="当天总工时")
    travel_status = fields.CharField(max_length=50, null=True, description="出差状态")
    work_location = fields.CharField(max_length=200, null=True, description="工作地点")
    location_coords = fields.CharField(max_length=100, null=True, description="定位位置")
    vehicle_initial_mileage = fields.DecimalField(max_digits=8, decimal_places=1, null=True, description="车辆初始里程")
    vehicle_end_mileage = fields.DecimalField(max_digits=8, decimal_places=1, null=True, description="车辆结束里程")
    vehicle_test_mileage = fields.DecimalField(max_digits=8, decimal_places=1, null=True, description="车辆测试里程")
    daily_advance_total = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description="当日垫付费用总计")
    expense_details = fields.JSONField(null=True, description="费用明细: [{\"type\":\"过路费\",\"amount\":0,\"attachment\":\"\"},...]")
    approver1 = fields.CharField(max_length=50, null=True, description="审批人1")
    approver1_result = fields.CharField(max_length=20, null=True, description="审批人1审核结果")
    approver2 = fields.CharField(max_length=50, null=True, description="审批人2")
    approver2_result = fields.CharField(max_length=20, null=True, description="审核结果")
    attachment_url = fields.CharField(max_length=500, null=True, description="考勤打卡附件")
    expense_attachment_url = fields.CharField(max_length=500, null=True, description="垫付费用附件")

    class Meta:
        table = "expense_driver_attendance"


class SupplierRate(BaseModel, TimestampMixin):
    """供应商单价（支持按时间生效，同一个供应商多行代表不同时段的价格）"""
    name = fields.CharField(max_length=50, description="供应商名称")
    local_rate = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description="本地单价")
    trip_rate = fields.DecimalField(max_digits=10, decimal_places=2, default=0, description="出差单价")
    unit = fields.CharField(max_length=10, default="hour", description="单位: hour/day")
    effective_from = fields.DateField(null=True, description="生效起始日期（含）")
    effective_to = fields.DateField(null=True, description="生效截止日期（含），NULL 表示无截止")
    contract_no = fields.CharField(max_length=100, null=True, default=None, description="合同号")
    code_local = fields.CharField(max_length=50, null=True, default=None, description="未出差服务编号")
    code_trip = fields.CharField(max_length=50, null=True, default=None, description="出差服务编号")

    class Meta:
        table = "expense_supplier_rate"
