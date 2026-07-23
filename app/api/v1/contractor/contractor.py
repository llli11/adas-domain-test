from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Query
from tortoise.expressions import Q

from app.controllers.contractor import (
    contractor_attendance_controller,
    contractor_evaluation_controller,
    contractor_leave_controller,
    contractor_performance_controller,
    contractor_resignation_controller,
    contractor_requirement_controller,
    contractor_staff_controller,
    contractor_transfer_controller,
    contractor_vehicle_status_controller,
    contractor_work_log_controller,
)
from app.models.admin import Dept, User
from app.models.contractor import (
    ContractorEvaluation,
    ContractorLeave,
    ContractorRequirement,
    ContractorStaff,
    ContractorTransfer,
    ContractorWorkLog,
)
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.contractor import (
    ContractorAttendanceCreate,
    ContractorAttendanceUpdate,
    ContractorEvaluationCreate,
    ContractorEvaluationGenerate,
    ContractorEvaluationUpdate,
    ContractorLeaveApprove,
    ContractorLeaveCreate,
    ContractorLeaveUpdate,
    ContractorPerformanceCreate,
    ContractorPerformanceUpdate,
    ContractorRequirementApprove,
    ContractorRequirementCreate,
    ContractorRequirementUpdate,
    ContractorResignationApprove,
    ContractorResignationCreate,
    ContractorResignationUpdate,
    ContractorStaffCreate,
    ContractorStaffUpdate,
    ContractorTransferConfirm,
    ContractorTransferCreate,
    ContractorTransferUpdate,
    ContractorWorkLogConfirm,
    ContractorWorkLogCreate,
    ContractorWorkLogUpdate,
)

router = APIRouter()


# ==================== 人员台账 ====================
@router.get("/staff/list", summary="外委人员列表")
async def list_staff(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    name: str = Query("", description="姓名"),
    company: str = Query("", description="所属公司"),
    project_id: Optional[int] = Query(None, description="所属项目ID"),
    task_status: str = Query("", description="任务状态"),
    status: str = Query("", description="状态"),
):
    q = Q()
    if name:
        q &= Q(name__contains=name)
    if company:
        q &= Q(company__contains=company)
    if project_id is not None:
        q &= Q(project_id=project_id)
    if task_status:
        q &= Q(task_status=task_status)
    if status:
        q &= Q(status=status)

    total = await ContractorStaff.filter(q).count()
    objs = await ContractorStaff.filter(q).offset((page - 1) * page_size).limit(page_size).all()
    data = [await obj.to_dict() for obj in objs]

    project_ids = list({d["project_id"] for d in data if d.get("project_id")})
    user_ids = list({d["responsible_user_id"] for d in data if d.get("responsible_user_id")})
    project_map = {}
    user_map = {}
    if project_ids:
        depts = await Dept.filter(id__in=project_ids).all()
        project_map = {d.id: d.name for d in depts}
    if user_ids:
        users = await User.filter(id__in=user_ids).all()
        user_map = {u.id: (u.alias or u.username) for u in users}
    for d in data:
        d["project_name"] = project_map.get(d.get("project_id"), "")
        d["responsible_user_name"] = user_map.get(d.get("responsible_user_id"), "")

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/staff/get", summary="查看外委人员")
async def get_staff(staff_id: int = Query(..., description="人员ID")):
    staff = await ContractorStaff.get_or_none(id=staff_id)
    if not staff:
        return Fail(msg="人员不存在")
    return Success(data=await staff.to_dict())


@router.get("/staff/dashboard", summary="人员看板统计")
async def staff_dashboard():
    staffs = await ContractorStaff.filter(status="在职").all()
    project_ids = list({s.project_id for s in staffs if s.project_id})
    dept_list = await Dept.filter(id__in=project_ids).all() if project_ids else []
    project_map = {d.id: d.name for d in dept_list}

    result = {}
    for s in staffs:
        pid = s.project_id or 0
        if pid not in result:
            result[pid] = {"project_id": pid, "project_name": project_map.get(pid, "未分配"), "total": 0, "idle": 0, "busy": 0}
        result[pid]["total"] += 1
        if s.is_idle:
            result[pid]["idle"] += 1
        else:
            result[pid]["busy"] += 1
    return Success(data=list(result.values()))


@router.post("/staff/create", summary="新增外委人员")
async def create_staff(staff_in: ContractorStaffCreate):
    staff = await contractor_staff_controller.create(staff_in)
    return Success(msg="新增成功", data={"id": staff.id})


@router.post("/staff/update", summary="更新外委人员")
async def update_staff(staff_in: ContractorStaffUpdate):
    await contractor_staff_controller.update(staff_in.id, staff_in)
    return Success(msg="更新成功")


@router.delete("/staff/delete", summary="删除外委人员")
async def delete_staff(staff_id: int = Query(..., description="人员ID")):
    await contractor_staff_controller.remove(staff_id)
    return Success(msg="删除成功")


@router.post("/staff/resign", summary="人员离职")
async def resign_staff(staff_id: int = Body(..., description="人员ID", embed=True)):
    staff = await ContractorStaff.get_or_none(id=staff_id)
    if not staff:
        return Fail(msg="人员不存在")
    staff.status = "离职"
    staff.resignation_date = datetime.now()
    await staff.save()
    return Success(msg="离职操作成功")


@router.post("/staff/qr_token", summary="生成人员二维码Token")
async def generate_qr_token(staff_id: int = Body(..., description="人员ID", embed=True)):
    staff = await ContractorStaff.get_or_none(id=staff_id)
    if not staff:
        return Fail(msg="人员不存在")
    from app.api.v1.contractor.qr import create_qr_token
    token = create_qr_token(staff_id)
    qr_page_url = f"/#/qr-contractor?token={token}"
    return Success(data={"token": token, "qr_page_url": qr_page_url, "staff_name": staff.name})


# ==================== 需求管理 ====================
@router.get("/requirement/list", summary="需求列表")
async def list_requirement(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    status: str = Query("", description="审批状态"),
):
    q = Q()
    if project_id is not None:
        q &= Q(project_id=project_id)
    if status:
        q &= Q(status=status)
    total, objs = await contractor_requirement_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/requirement/create", summary="新增需求")
async def create_requirement(req_in: ContractorRequirementCreate):
    req = await contractor_requirement_controller.create(req_in)
    return Success(msg="提交成功", data={"id": req.id})


@router.post("/requirement/update", summary="更新需求")
async def update_requirement(req_in: ContractorRequirementUpdate):
    await contractor_requirement_controller.update(req_in.id, req_in)
    return Success(msg="更新成功")


@router.delete("/requirement/delete", summary="删除需求")
async def delete_requirement(req_id: int = Query(..., description="需求ID")):
    await contractor_requirement_controller.remove(req_id)
    return Success(msg="删除成功")


@router.post("/requirement/approve", summary="审批需求")
async def approve_requirement(approve_in: ContractorRequirementApprove):
    req = await ContractorRequirement.get_or_none(id=approve_in.id)
    if not req:
        return Fail(msg="需求不存在")
    req.status = approve_in.status
    req.approver_user_id = approve_in.approver_user_id
    req.approval_time = datetime.now()
    await req.save()
    return Success(msg="审批完成")


# ==================== 流转管理 ====================
@router.get("/transfer/list", summary="流转列表")
async def list_transfer(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    staff_id: Optional[int] = Query(None, description="人员ID"),
    status: str = Query("", description="状态"),
):
    q = Q()
    if staff_id is not None:
        q &= Q(staff_id=staff_id)
    if status:
        q &= Q(status=status)
    total, objs = await contractor_transfer_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in objs]
    staff_ids = list({d["staff_id"] for d in data if d.get("staff_id")})
    staff_map = {}
    if staff_ids:
        staffs = await ContractorStaff.filter(id__in=staff_ids).all()
        staff_map = {s.id: s.name for s in staffs}
    for d in data:
        d["staff_name"] = staff_map.get(d.get("staff_id"), "")
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/transfer/apply", summary="申请流转")
async def apply_transfer(transfer_in: ContractorTransferCreate):
    transfer = await contractor_transfer_controller.create(transfer_in)
    return Success(msg="流转申请已提交", data={"id": transfer.id})


@router.post("/transfer/update", summary="更新流转")
async def update_transfer(transfer_in: ContractorTransferUpdate):
    await contractor_transfer_controller.update(transfer_in.id, transfer_in)
    return Success(msg="更新成功")


@router.delete("/transfer/delete", summary="删除流转")
async def delete_transfer(transfer_id: int = Query(..., description="流转ID")):
    await contractor_transfer_controller.remove(transfer_id)
    return Success(msg="删除成功")


@router.post("/transfer/confirm", summary="确认流转")
async def confirm_transfer(confirm_in: ContractorTransferConfirm):
    transfer = await ContractorTransfer.get_or_none(id=confirm_in.id)
    if not transfer:
        return Fail(msg="流转记录不存在")
    transfer.status = confirm_in.status
    transfer.confirm_user_id = confirm_in.confirm_user_id
    transfer.confirmed_at = datetime.now()
    await transfer.save()
    if confirm_in.status == "已确认":
        staff = await ContractorStaff.get_or_none(id=transfer.staff_id)
        if staff:
            if transfer.transfer_type == "离职":
                staff.status = "离职"
                staff.resignation_date = datetime.now()
            elif transfer.transfer_type == "流转":
                staff.status = "流转中"
            await staff.save()
    return Success(msg="确认完成")


# ==================== 车辆/任务状态 ====================
@router.get("/vehicle_status/list", summary="车辆状态流水列表")
async def list_vehicle_status(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    staff_id: Optional[int] = Query(None, description="人员ID"),
):
    q = Q()
    if staff_id is not None:
        q &= Q(staff_id=staff_id)
    total, objs = await contractor_vehicle_status_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


# ==================== 工作日志 ====================
@router.get("/worklog/list", summary="工作日志列表")
async def list_worklog(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    staff_id: Optional[int] = Query(None, description="人员ID"),
    project_id: Optional[int] = Query(None, description="项目ID"),
    work_date: str = Query("", description="工作日期"),
    status: str = Query("", description="状态"),
):
    q = Q()
    if staff_id is not None:
        q &= Q(staff_id=staff_id)
    if project_id is not None:
        q &= Q(project_id=project_id)
    if work_date:
        q &= Q(work_date=work_date)
    if status:
        q &= Q(status=status)
    total, objs = await contractor_work_log_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in objs]

    staff_ids = list({d["staff_id"] for d in data if d.get("staff_id")})
    project_ids = list({d["project_id"] for d in data if d.get("project_id")})
    user_ids = list({d["confirmed_by_user_id"] for d in data if d.get("confirmed_by_user_id")})

    staff_map = {}
    project_map = {}
    user_map = {}
    if staff_ids:
        staffs = await ContractorStaff.filter(id__in=staff_ids).all()
        staff_map = {s.id: s.name for s in staffs}
    if project_ids:
        depts = await Dept.filter(id__in=project_ids).all()
        project_map = {d.id: d.name for d in depts}
    if user_ids:
        users = await User.filter(id__in=user_ids).all()
        user_map = {u.id: (u.alias or u.username) for u in users}

    for d in data:
        d["staff_name"] = staff_map.get(d.get("staff_id"), "")
        d["project_name"] = project_map.get(d.get("project_id"), "")
        d["confirmed_by_user_name"] = user_map.get(d.get("confirmed_by_user_id"), "")

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/worklog/create", summary="新增工作日志")
async def create_worklog(log_in: ContractorWorkLogCreate):
    log = await contractor_work_log_controller.create(log_in)
    return Success(msg="提交成功", data={"id": log.id})


@router.post("/worklog/update", summary="更新工作日志")
async def update_worklog(log_in: ContractorWorkLogUpdate):
    await contractor_work_log_controller.update(log_in.id, log_in)
    return Success(msg="更新成功")


@router.delete("/worklog/delete", summary="删除工作日志")
async def delete_worklog(log_id: int = Query(..., description="日志ID", alias="log_id")):
    await contractor_work_log_controller.remove(log_id)
    return Success(msg="删除成功")


@router.post("/worklog/confirm", summary="确认工作日志")
async def confirm_worklog(confirm_in: ContractorWorkLogConfirm):
    log = await ContractorWorkLog.get_or_none(id=confirm_in.id)
    if not log:
        return Fail(msg="日志不存在")
    log.status = "已确认"
    log.confirmed_by_user_id = confirm_in.confirmed_by_user_id
    log.mistake_count = confirm_in.mistake_count
    await log.save()
    return Success(msg="确认成功")


@router.post("/worklog/batch_notify", summary="统一通知确认工作日志")
async def batch_notify_worklog(
    project_id: int = Body(..., description="项目ID"),
    work_date: str = Body(..., description="日期 YYYY-MM-DD"),
):
    count = await ContractorWorkLog.filter(
        project_id=project_id, work_date=work_date, status="待确认"
    ).count()
    return Success(msg=f"当日共有 {count} 条工作日志待确认", data={"pending_count": count})


# ==================== 请假管理 ====================
@router.get("/leave/list", summary="请假列表")
async def list_leave(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    staff_id: Optional[int] = Query(None, description="人员ID"),
    status: str = Query("", description="状态"),
):
    q = Q()
    if staff_id is not None:
        q &= Q(staff_id=staff_id)
    if status:
        q &= Q(status=status)
    total, objs = await contractor_leave_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in objs]

    staff_ids = list({d["staff_id"] for d in data if d.get("staff_id")})
    user_ids = list({d["approved_by_user_id"] for d in data if d.get("approved_by_user_id")})
    staff_map = {}
    user_map = {}
    if staff_ids:
        staffs = await ContractorStaff.filter(id__in=staff_ids).all()
        staff_map = {s.id: s.name for s in staffs}
    if user_ids:
        users = await User.filter(id__in=user_ids).all()
        user_map = {u.id: (u.alias or u.username) for u in users}
    for d in data:
        d["staff_name"] = staff_map.get(d.get("staff_id"), "")
        d["approved_by_user_name"] = user_map.get(d.get("approved_by_user_id"), "")

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/leave/create", summary="新增请假")
async def create_leave(leave_in: ContractorLeaveCreate):
    leave = await contractor_leave_controller.create(leave_in)
    return Success(msg="提交成功", data={"id": leave.id})


@router.post("/leave/approve", summary="审批请假")
async def approve_leave(approve_in: ContractorLeaveApprove):
    leave = await ContractorLeave.get_or_none(id=approve_in.id)
    if not leave:
        return Fail(msg="请假记录不存在")
    leave.status = approve_in.status
    leave.approved_by_user_id = approve_in.approved_by_user_id
    leave.approved_at = datetime.now()
    await leave.save()
    return Success(msg="审批完成")


@router.post("/leave/update", summary="更新请假")
async def update_leave(leave_in: ContractorLeaveUpdate):
    await contractor_leave_controller.update(leave_in.id, leave_in)
    return Success(msg="更新成功")


@router.delete("/leave/delete", summary="删除请假")
async def delete_leave(leave_id: int = Query(..., description="请假ID")):
    await contractor_leave_controller.remove(leave_id)
    return Success(msg="删除成功")


# ==================== 考评管理 ====================
@router.get("/evaluation/list", summary="月度考评列表")
async def list_evaluation(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    staff_id: Optional[int] = Query(None, description="人员ID"),
    evaluation_month: str = Query("", description="考核周期 YYYY-MM"),
):
    q = Q()
    if staff_id is not None:
        q &= Q(staff_id=staff_id)
    if evaluation_month:
        q &= Q(evaluation_month=evaluation_month)
    total, objs = await contractor_evaluation_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in objs]
    staff_ids = list({d["staff_id"] for d in data if d.get("staff_id")})
    staff_map = {}
    if staff_ids:
        staffs = await ContractorStaff.filter(id__in=staff_ids).all()
        staff_map = {s.id: s.name for s in staffs}
    for d in data:
        d["staff_name"] = staff_map.get(d.get("staff_id"), "")
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/evaluation/generate", summary="生成月度考评")
async def generate_evaluation(gen_in: ContractorEvaluationGenerate):
    logs = await ContractorWorkLog.filter(
        staff_id=gen_in.staff_id,
        work_date__startswith=gen_in.evaluation_month,
        status="已确认",
    ).all()

    mistake_total = sum(log.mistake_count for log in logs)
    mistake_deduction = mistake_total * 0.5
    total_work_days = len(set(log.work_date for log in logs))
    quality_score = max(0, 10 - mistake_deduction) if total_work_days > 0 else 0

    existing = await ContractorEvaluation.filter(
        staff_id=gen_in.staff_id, evaluation_month=gen_in.evaluation_month
    ).first()
    if existing:
        existing.mistake_total = mistake_total
        existing.mistake_deduction = mistake_deduction
        existing.quality_score = quality_score
        await existing.save()
        return Success(msg="考评已更新", data={"id": existing.id})

    eval_obj = await contractor_evaluation_controller.create({
        "staff_id": gen_in.staff_id,
        "evaluation_month": gen_in.evaluation_month,
        "mistake_total": mistake_total,
        "mistake_deduction": mistake_deduction,
        "quality_score": quality_score,
    })
    return Success(msg="考评生成成功", data={"id": eval_obj.id})


@router.post("/evaluation/rate", summary="月度考评分")
async def rate_evaluation(eval_in: ContractorEvaluationCreate):
    existing = await ContractorEvaluation.filter(
        staff_id=eval_in.staff_id, evaluation_month=eval_in.evaluation_month
    ).first()
    if existing:
        await contractor_evaluation_controller.update(existing.id, eval_in)
        return Success(msg="评分已更新", data={"id": existing.id})
    eval_obj = await contractor_evaluation_controller.create(eval_in)
    return Success(msg="评分成功", data={"id": eval_obj.id})


@router.post("/evaluation/update", summary="更新考评")
async def update_evaluation(eval_in: ContractorEvaluationUpdate):
    await contractor_evaluation_controller.update(eval_in.id, eval_in)
    return Success(msg="更新成功")


@router.delete("/evaluation/delete", summary="删除考评")
async def delete_evaluation(eval_id: int = Query(..., description="考评ID")):
    await contractor_evaluation_controller.remove(eval_id)
    return Success(msg="删除成功")


# ==================== 考勤/绩效/离职（旧版兼容） ====================
@router.get("/attendance/list", summary="考勤列表")
async def list_attendance(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    staff_id: Optional[int] = Query(None, description="人员ID"),
):
    q = Q()
    if staff_id is not None:
        q &= Q(staff_id=staff_id)
    total, objs = await contractor_attendance_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/attendance/create", summary="新增考勤")
async def create_attendance(att_in: ContractorAttendanceCreate):
    att = await contractor_attendance_controller.create(att_in)
    return Success(msg="提交成功", data={"id": att.id})


@router.post("/attendance/batch", summary="批量考勤")
async def batch_attendance(records: list = Body(..., description="考勤记录列表")):
    for r in records:
        await contractor_attendance_controller.create(r)
    return Success(msg="批量提交成功")


@router.post("/attendance/update", summary="更新考勤")
async def update_attendance(att_in: ContractorAttendanceUpdate):
    await contractor_attendance_controller.update(att_in.id, att_in)
    return Success(msg="更新成功")


@router.delete("/attendance/delete", summary="删除考勤")
async def delete_attendance(att_id: int = Query(..., description="考勤ID")):
    await contractor_attendance_controller.remove(att_id)
    return Success(msg="删除成功")


@router.get("/performance/list", summary="绩效列表")
async def list_performance(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    staff_id: Optional[int] = Query(None, description="人员ID"),
):
    q = Q()
    if staff_id is not None:
        q &= Q(staff_id=staff_id)
    total, objs = await contractor_performance_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/performance/create", summary="新增绩效")
async def create_performance(perf_in: ContractorPerformanceCreate):
    perf = await contractor_performance_controller.create(perf_in)
    return Success(msg="提交成功", data={"id": perf.id})


@router.post("/performance/update", summary="更新绩效")
async def update_performance(perf_in: ContractorPerformanceUpdate):
    await contractor_performance_controller.update(perf_in.id, perf_in)
    return Success(msg="更新成功")


@router.delete("/performance/delete", summary="删除绩效")
async def delete_performance(perf_id: int = Query(..., description="绩效ID")):
    await contractor_performance_controller.remove(perf_id)
    return Success(msg="删除成功")


@router.get("/resignation/list", summary="离职列表")
async def list_resignation(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    staff_id: Optional[int] = Query(None, description="人员ID"),
):
    q = Q()
    if staff_id is not None:
        q &= Q(staff_id=staff_id)
    total, objs = await contractor_resignation_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in objs]
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/resignation/create", summary="新增离职申请")
async def create_resignation(res_in: ContractorResignationCreate):
    res = await contractor_resignation_controller.create(res_in)
    return Success(msg="提交成功", data={"id": res.id})


@router.post("/resignation/approve", summary="审批离职")
async def approve_resignation(approve_in: ContractorResignationApprove):
    res = await contractor_resignation_controller.get(approve_in.id)
    if not res:
        return Fail(msg="离职记录不存在")
    res.approval_status = approve_in.status
    res.approver = approve_in.approver
    res.approval_date = datetime.now()
    await res.save()
    return Success(msg="审批完成")


@router.post("/resignation/update", summary="更新离职")
async def update_resignation(res_in: ContractorResignationUpdate):
    await contractor_resignation_controller.update(res_in.id, res_in)
    return Success(msg="更新成功")


@router.delete("/resignation/delete", summary="删除离职记录")
async def delete_resignation(res_id: int = Query(..., description="离职记录ID")):
    await contractor_resignation_controller.remove(res_id)
    return Success(msg="删除成功")
