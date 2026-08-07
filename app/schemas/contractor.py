from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ==================== ContractorStaff ====================

class ContractorStaffCreate(BaseModel):
    name: str = Field(..., max_length=20, description="姓名")
    type: Optional[str] = Field(None, description="属性（工程师/驾驶员）")
    gender: Optional[str] = Field(None, description="性别")
    id_card: Optional[str] = Field(None, description="身份证号")
    phone: Optional[str] = Field(None, description="电话号码")
    company: Optional[str] = Field(None, description="公司")
    position: Optional[str] = Field(None, description="岗位")
    project_id: Optional[int] = Field(None, description="所属项目ID")
    responsible_user_id: Optional[int] = Field(None, description="责任人ID")
    entry_date: Optional[datetime] = Field(None, description="入职时间")
    resignation_date: Optional[datetime] = Field(None, description="离职时间")
    status: str = Field("在职", description="状态")
    current_task: Optional[str] = Field(None, description="当前任务")
    current_vehicle: Optional[str] = Field(None, description="当前所在车辆")
    task_status: str = Field("空闲", description="任务状态")
    is_idle: bool = Field(True, description="是否空闲")
    remark: Optional[str] = Field(None, description="备注")


class ContractorStaffUpdate(ContractorStaffCreate):
    id: int


# ==================== ContractorAttendance (legacy) ====================

class ContractorAttendanceCreate(BaseModel):
    staff_id: int = Field(..., description="人员ID")
    date: str = Field(..., description="日期 YYYY-MM-DD")
    check_in: Optional[str] = Field(None, description="签到时间")
    check_out: Optional[str] = Field(None, description="签退时间")
    work_hours: Optional[float] = Field(None, description="工作时长")
    status: str = Field("正常", description="状态")
    location: Optional[str] = Field(None, description="打卡地点")
    remark: Optional[str] = Field(None, description="备注")


class ContractorAttendanceUpdate(ContractorAttendanceCreate):
    id: int


# ==================== ContractorVehicleStatus ====================

class ContractorVehicleStatusCreate(BaseModel):
    staff_id: int = Field(..., description="人员ID")
    vehicle_name: Optional[str] = Field(None, description="当前车辆")
    task_type: Optional[str] = Field(None, description="任务类型")
    action: str = Field(..., description="动作（出发/返回）")
    action_time: Optional[datetime] = Field(None, description="动作时间")
    location: Optional[str] = Field(None, description="地点")


class ContractorVehicleStatusUpdate(ContractorVehicleStatusCreate):
    id: int


# ==================== ContractorRequirement ====================

# ==================== ContractorWorkLog ====================

class ContractorWorkLogCreate(BaseModel):
    staff_id: int = Field(..., description="人员ID")
    work_date: str = Field(..., description="工作日期 YYYY-MM-DD")
    check_out_time: Optional[str] = Field(None, description="下班时间")
    check_out_image: Optional[str] = Field(None, description="打卡截图URL")
    normal_hours: float = Field(8.0, description="正常工时")
    overtime_hours: float = Field(0.0, description="加班工时")
    work_content: Optional[str] = Field(None, description="工作内容")
    project_id: Optional[int] = Field(None, description="今日工作的车型项目ID")
    advance_payment: float = Field(0.0, description="垫付费用")
    advance_payment_image: Optional[str] = Field(None, description="垫付费用证明图片URL")
    leave_type: Optional[str] = Field(None, description="请假类型")
    remark: Optional[str] = Field(None, description="备注")


class ContractorWorkLogUpdate(BaseModel):
    id: int
    check_out_time: Optional[str] = Field(None, description="下班时间")
    check_out_image: Optional[str] = Field(None, description="打卡截图URL")
    normal_hours: Optional[float] = Field(None, description="正常工时")
    overtime_hours: Optional[float] = Field(None, description="加班工时")
    work_content: Optional[str] = Field(None, description="工作内容")
    project_id: Optional[int] = Field(None, description="今日工作的车型项目ID")
    advance_payment: Optional[float] = Field(None, description="垫付费用")
    advance_payment_image: Optional[str] = Field(None, description="垫付费用证明图片URL")
    leave_type: Optional[str] = Field(None, description="请假类型")
    remark: Optional[str] = Field(None, description="备注")


# ==================== ContractorAssessmentRecord ====================

class ContractorAssessmentRecordCreate(BaseModel):
    staff_id: int = Field(..., description="人员ID")
    type: str = Field(..., description="类型（mistake=犯错 / reward=奖励）")
    count: int = Field(1, description="次数")
    record_date: Optional[str] = Field(None, description="记录日期 YYYY-MM-DD")
    remark: Optional[str] = Field(None, description="备注")


class ContractorAssessmentRecordUpdate(BaseModel):
    id: int
    type: Optional[str] = Field(None, description="类型")
    count: Optional[int] = Field(None, description="次数")
    record_date: Optional[str] = Field(None, description="记录日期")
    remark: Optional[str] = Field(None, description="备注")


# ==================== ContractorEvaluation ====================

class ContractorEvaluationCreate(BaseModel):
    staff_id: int = Field(..., description="人员ID")
    evaluation_month: str = Field(..., description="考核周期 YYYY-MM")
    attitude_score: Optional[float] = Field(None, ge=0, le=10, description="工作态度评分")
    ability_score: Optional[float] = Field(None, ge=0, le=10, description="工作能力评分")
    achievement_score: Optional[float] = Field(None, ge=0, le=10, description="工作达成评分")
    assessor: Optional[str] = Field(None, description="考核人")
    assessment_date: Optional[datetime] = Field(None, description="考核日期")


class ContractorEvaluationUpdate(ContractorEvaluationCreate):
    id: int


class ContractorEvaluationGenerate(BaseModel):
    staff_id: Optional[int] = Field(None, description="人员ID，为空则生成所有在职人员")
    evaluation_month: str = Field(..., description="考核周期 YYYY-MM")


# ==================== ContractorPerformance (legacy) ====================

class ContractorPerformanceCreate(BaseModel):
    staff_id: int = Field(..., description="人员ID")
    assessment_period: str = Field(..., description="考核周期 YYYY-MM")
    quality_score: Optional[float] = Field(None, ge=0, le=100, description="工作质量评分")
    efficiency_score: Optional[float] = Field(None, ge=0, le=100, description="工作效率评分")
    teamwork_score: Optional[float] = Field(None, ge=0, le=100, description="团队协作评分")
    overall_score: Optional[float] = Field(None, ge=0, le=100, description="综合评分")
    comment: Optional[str] = Field(None, description="评语")
    assessor: Optional[str] = Field(None, description="考核人")
    assessment_date: Optional[datetime] = Field(None, description="考核日期")


class ContractorPerformanceUpdate(ContractorPerformanceCreate):
    id: int


# ==================== ContractorResignation (legacy) ====================

class ContractorResignationCreate(BaseModel):
    staff_id: int = Field(..., description="人员ID")
    application_date: Optional[datetime] = Field(None, description="申请日期")
    expected_date: Optional[datetime] = Field(None, description="预计离职日期")
    actual_date: Optional[datetime] = Field(None, description="实际离职日期")
    reason: Optional[str] = Field(None, description="离职原因")
    handover_status: Optional[str] = Field(None, description="交接状态")
    approval_status: str = Field("待审批", description="审批状态")
    approver: Optional[str] = Field(None, description="审批人")
    approval_date: Optional[datetime] = Field(None, description="审批日期")
    remark: Optional[str] = Field(None, description="备注")


class ContractorResignationUpdate(ContractorResignationCreate):
    id: int


class ContractorResignationApprove(BaseModel):
    id: int
    approval_status: str = Field(..., description="审批状态：已通过/已驳回")
    approver: str = Field(..., description="审批人")


# ==================== ContractorProject ====================
class ContractorProjectCreate(BaseModel):
    name: str = Field(..., description="项目名称")
    desc: Optional[str] = Field(None, description="项目描述")
    order: int = Field(0, description="排序")
    is_active: bool = Field(True, description="是否启用")
    responsible_user_id: Optional[int] = Field(None, description="责任人ID")


class ContractorProjectUpdate(ContractorProjectCreate):
    id: int
