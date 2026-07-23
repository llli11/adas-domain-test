from tortoise import fields

from .base import BaseModel, TimestampMixin


class ContractorStaff(BaseModel, TimestampMixin):
    """外委人员信息表（人力台账）"""

    name = fields.CharField(max_length=20, description="姓名")
    type = fields.CharField(max_length=20, null=True, description="属性（工程师/驾驶员）")
    gender = fields.CharField(max_length=10, null=True, description="性别")
    id_card = fields.CharField(max_length=18, null=True, description="身份证号")
    phone = fields.CharField(max_length=20, null=True, description="电话号码")
    company = fields.CharField(max_length=100, null=True, description="公司")
    position = fields.CharField(max_length=50, null=True, description="岗位")

    project_id = fields.IntField(null=True, description="所属项目（关联dept）")
    responsible_user_id = fields.IntField(null=True, description="责任人（关联user）")

    entry_date = fields.DatetimeField(null=True, description="入职时间")
    resignation_date = fields.DatetimeField(null=True, description="离职时间")
    status = fields.CharField(max_length=20, default="在职", description="状态（在职/离职中/离职）")

    current_task = fields.CharField(max_length=50, null=True, description="当前任务（泊车/行车/LO/L1）")
    current_vehicle = fields.CharField(max_length=50, null=True, description="当前所在车辆")
    task_status = fields.CharField(max_length=20, default="空闲", description="任务状态（空闲/任务中）")
    is_idle = fields.BooleanField(default=True, description="是否空闲")

    resignation_id = fields.IntField(null=True, description="关联离职记录ID")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "contractor_staff"


class ContractorAttendance(BaseModel, TimestampMixin):
    """外委考勤表（旧版，保留兼容）"""

    staff_id = fields.IntField(description="人员ID")
    date = fields.CharField(max_length=10, description="日期 YYYY-MM-DD")
    check_in = fields.CharField(max_length=20, null=True, description="签到时间")
    check_out = fields.CharField(max_length=20, null=True, description="签退时间")
    work_hours = fields.FloatField(null=True, description="工作时长")
    status = fields.CharField(max_length=20, default="正常", description="状态")
    location = fields.CharField(max_length=255, null=True, description="打卡地点")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "contractor_attendance"


class ContractorVehicleStatus(BaseModel, TimestampMixin):
    """外委车辆/任务状态记录（扫码出发/返回流水）"""

    staff_id = fields.IntField(description="人员ID")
    vehicle_name = fields.CharField(max_length=50, null=True, description="当前车辆")
    task_type = fields.CharField(max_length=50, null=True, description="任务类型（泊车/行车/LO/L1）")
    action = fields.CharField(max_length=20, description="动作（出发/返回）")
    action_time = fields.DatetimeField(null=True, description="动作时间")
    location = fields.CharField(max_length=255, null=True, description="地点")

    class Meta:
        table = "contractor_vehicle_status"


class ContractorRequirement(BaseModel, TimestampMixin):
    """外委需求单"""

    project_id = fields.IntField(null=True, description="需求项目")
    type = fields.CharField(max_length=20, description="需求类型（驾驶员/工程师）")
    demand_date = fields.CharField(max_length=10, null=True, description="需求时间")
    quantity = fields.IntField(default=1, description="数量")
    period = fields.CharField(max_length=100, null=True, description="周期")
    status = fields.CharField(max_length=20, default="待审批", description="审批状态")
    approver_user_id = fields.IntField(null=True, description="审批人")
    approval_time = fields.DatetimeField(null=True, description="审批时间")
    created_by_user_id = fields.IntField(null=True, description="创建人")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "contractor_requirement"


class ContractorTransfer(BaseModel, TimestampMixin):
    """外委人员流转记录（入/转/离）"""

    staff_id = fields.IntField(description="人员ID")
    transfer_type = fields.CharField(max_length=20, description="流转类型（入职/流转/离职）")
    from_project_id = fields.IntField(null=True, description="原项目")
    to_project_id = fields.IntField(null=True, description="目标项目")
    initiator_user_id = fields.IntField(null=True, description="发起人")
    confirm_user_id = fields.IntField(null=True, description="确认人")
    status = fields.CharField(max_length=20, default="待确认", description="状态（待确认/已确认/已驳回）")
    confirmed_at = fields.DatetimeField(null=True, description="确认时间")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "contractor_transfer"


class ContractorWorkLog(BaseModel, TimestampMixin):
    """外委每日工作日志"""

    staff_id = fields.IntField(description="人员ID")
    work_date = fields.CharField(max_length=10, description="工作日期 YYYY-MM-DD")
    check_out_time = fields.CharField(max_length=20, null=True, description="下班时间")
    check_out_image = fields.CharField(max_length=500, null=True, description="打卡截图URL")
    normal_hours = fields.FloatField(default=8.0, description="正常工时")
    overtime_hours = fields.FloatField(default=0.0, description="加班工时")
    work_content = fields.CharField(max_length=50, null=True, description="工作内容（泊车/行车）")
    project_id = fields.IntField(null=True, description="今日工作的车型项目")
    advance_payment = fields.FloatField(default=0.0, description="垫付费用")
    advance_payment_image = fields.CharField(max_length=500, null=True, description="垫付费用证明图片URL")
    leave_type = fields.CharField(max_length=50, null=True, description="请假类型（空表示未请假）")
    status = fields.CharField(max_length=20, default="待确认", description="状态（待确认/已确认）")
    confirmed_by_user_id = fields.IntField(null=True, description="确认人")
    mistake_count = fields.IntField(default=0, description="当天犯错次数")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "contractor_work_log"


class ContractorLeave(BaseModel, TimestampMixin):
    """外委请假申请"""

    staff_id = fields.IntField(description="人员ID")
    leave_date = fields.CharField(max_length=10, null=True, description="请假日期")
    leave_type = fields.CharField(max_length=50, null=True, description="请假类型")
    reason = fields.TextField(null=True, description="请假原因")
    status = fields.CharField(max_length=20, default="待审批", description="状态（待审批/已批准/已驳回）")
    approved_by_user_id = fields.IntField(null=True, description="审批人")
    approved_at = fields.DatetimeField(null=True, description="审批时间")

    class Meta:
        table = "contractor_leave"


class ContractorEvaluation(BaseModel, TimestampMixin):
    """外委月度考评记录"""

    staff_id = fields.IntField(description="人员ID")
    evaluation_month = fields.CharField(max_length=7, description="考核周期 YYYY-MM")
    attitude_score = fields.FloatField(null=True, description="工作态度评分（0-10）")
    ability_score = fields.FloatField(null=True, description="工作能力评分（0-10）")
    achievement_score = fields.FloatField(null=True, description="工作达成评分（0-10）")
    quality_score = fields.FloatField(null=True, description="任务质量评分（自动计算）")
    mistake_total = fields.IntField(default=0, description="当月犯错总次数")
    mistake_deduction = fields.FloatField(default=0.0, description="犯错减分（自动计算）")
    final_score = fields.FloatField(null=True, description="月度绩效分数（自动计算）")
    assessor = fields.CharField(max_length=50, null=True, description="考核人")
    assessment_date = fields.DatetimeField(null=True, description="考核日期")

    class Meta:
        table = "contractor_evaluation"


class ContractorPerformance(BaseModel, TimestampMixin):
    """外委绩效表（旧版，保留兼容）"""

    staff_id = fields.IntField(description="人员ID")
    assessment_period = fields.CharField(max_length=7, description="考核周期 YYYY-MM")
    quality_score = fields.FloatField(null=True, description="工作质量评分")
    efficiency_score = fields.FloatField(null=True, description="工作效率评分")
    teamwork_score = fields.FloatField(null=True, description="团队协作评分")
    overall_score = fields.FloatField(null=True, description="综合评分")
    comment = fields.TextField(null=True, description="评语")
    assessor = fields.CharField(max_length=50, null=True, description="考核人")
    assessment_date = fields.DatetimeField(null=True, description="考核日期")

    class Meta:
        table = "contractor_performance"


class ContractorResignation(BaseModel, TimestampMixin):
    """外委离职表"""

    staff_id = fields.IntField(description="人员ID")
    application_date = fields.DatetimeField(null=True, description="申请日期")
    expected_date = fields.DatetimeField(null=True, description="预计离职日期")
    actual_date = fields.DatetimeField(null=True, description="实际离职日期")
    reason = fields.TextField(null=True, description="离职原因")
    handover_status = fields.CharField(max_length=50, null=True, description="交接状态")
    approval_status = fields.CharField(max_length=20, default="待审批", description="审批状态")
    approver = fields.CharField(max_length=50, null=True, description="审批人")
    approval_date = fields.DatetimeField(null=True, description="审批日期")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "contractor_resignation"
