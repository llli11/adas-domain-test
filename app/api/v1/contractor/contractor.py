from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Body, Query
from tortoise.expressions import Q

from app.controllers.contractor import (
    contractor_assessment_record_controller,
    contractor_attendance_controller,
    contractor_evaluation_controller,
    contractor_performance_controller,
    contractor_project_controller,
    contractor_resignation_controller,
    contractor_staff_controller,
    contractor_vehicle_status_controller,
    contractor_work_log_controller,
)
from app.models.admin import User
from app.models.contractor import (
    ContractorAssessmentRecord,
    ContractorEvaluation,
    ContractorProject,
    ContractorStaff,
    ContractorWorkLog,
)
from app.schemas.base import Fail, Success, SuccessExtra
from app.schemas.contractor import (
    ContractorAssessmentRecordCreate,
    ContractorAttendanceCreate,
    ContractorAttendanceUpdate,
    ContractorEvaluationCreate,
    ContractorEvaluationGenerate,
    ContractorEvaluationUpdate,
    ContractorPerformanceCreate,
    ContractorPerformanceUpdate,
    ContractorProjectCreate,
    ContractorProjectUpdate,
    ContractorResignationApprove,
    ContractorResignationCreate,
    ContractorResignationUpdate,
    ContractorStaffCreate,
    ContractorStaffUpdate,
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
        projects = await ContractorProject.filter(id__in=project_ids).all()
        project_map = {p.id: p.name for p in projects}
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
    project_list = await ContractorProject.filter(id__in=project_ids).all() if project_ids else []
    project_map = {p.id: p.name for p in project_list}

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
        projects = await ContractorProject.filter(id__in=project_ids).all()
        project_map = {p.id: p.name for p in projects}
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


# ==================== 考核管理 ====================
@router.get("/assessment/list", summary="考核记录列表")
async def list_assessment(
    page: int = Query(1, description="页码"),
    page_size: int = Query(10, description="每页数量"),
    staff_id: Optional[int] = Query(None, description="人员ID"),
    type: str = Query("", description="类型（mistake/reward）"),
    record_date: str = Query("", description="记录日期"),
):
    q = Q()
    if staff_id is not None:
        q &= Q(staff_id=staff_id)
    if type:
        q &= Q(type=type)
    if record_date:
        q &= Q(record_date=record_date)
    total, objs = await contractor_assessment_record_controller.list(page=page, page_size=page_size, search=q)
    data = [await obj.to_dict() for obj in objs]

    staff_ids = list({d["staff_id"] for d in data if d.get("staff_id")})
    staff_map = {}
    if staff_ids:
        staffs = await ContractorStaff.filter(id__in=staff_ids).all()
        staff_map = {s.id: s.name for s in staffs}
    for d in data:
        d["staff_name"] = staff_map.get(d.get("staff_id"), "")

    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.post("/assessment/create", summary="新增考核记录")
async def create_assessment(record_in: ContractorAssessmentRecordCreate):
    record = await contractor_assessment_record_controller.create(record_in)
    return Success(msg="记录成功", data={"id": record.id})


@router.delete("/assessment/delete", summary="删除考核记录")
async def delete_assessment(record_id: int = Query(..., description="记录ID")):
    await contractor_assessment_record_controller.remove(record_id)
    return Success(msg="删除成功")


@router.get("/assessment/staff_scores", summary="人员考核分数汇总")
async def staff_scores():
    """计算所有在职人员的加减分汇总"""
    staffs = await ContractorStaff.filter(status="在职").all()
    records = await ContractorAssessmentRecord.all()

    result = {}
    for s in staffs:
        result[s.id] = {"staff_id": s.id, "staff_name": s.name, "mistake_count": 0, "reward_count": 0, "score": 10.0}

    for r in records:
        sid = r.staff_id
        if sid not in result:
            continue
        if r.type == "mistake":
            result[sid]["mistake_count"] += r.count
            result[sid]["score"] = round(result[sid]["score"] - r.count * 0.1, 2)
        elif r.type == "reward":
            result[sid]["reward_count"] += r.count
            result[sid]["score"] = round(result[sid]["score"] + r.count * 0.1, 2)

    return Success(data=list(result.values()))


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
    """基于考核记录(assessment)自动生成月度考评，不传staff_id则为所有在职人员生成"""
    staff_ids = [gen_in.staff_id] if gen_in.staff_id else [
        s.id for s in await ContractorStaff.filter(status="在职").all()
    ]

    results = []
    for sid in staff_ids:
        # 当月考核记录
        month_records = await ContractorAssessmentRecord.filter(
            staff_id=sid,
            record_date__startswith=gen_in.evaluation_month,
        ).all()

        # 当月统计
        mistake_total = sum(r.count for r in month_records if r.type == "mistake")
        reward_total = sum(r.count for r in month_records if r.type == "reward")
        mistake_deduction = round(mistake_total * 0.1, 2)
        reward_bonus = round(reward_total * 0.1, 2)

        # 累积统计（所有考核记录）
        all_records = await ContractorAssessmentRecord.filter(staff_id=sid).all()
        all_mistake = sum(r.count for r in all_records if r.type == "mistake")
        all_reward = sum(r.count for r in all_records if r.type == "reward")
        all_deduction = round(all_mistake * 0.1, 2)
        all_bonus = round(all_reward * 0.1, 2)
        cumulative_score = round(max(0, 10 + all_bonus - all_deduction), 2)

        existing = await ContractorEvaluation.filter(
            staff_id=sid, evaluation_month=gen_in.evaluation_month
        ).first()
        # 计算最终得分：质量分(60%) + 已有主观评分均值的(40%)，如未评分则直接用质量分
        existing_attrs = {"attitude_score": 0, "ability_score": 0, "achievement_score": 0}
        if existing:
            existing_attrs = {k: float(existing.__dict__.get(k, 0) or 0) for k in existing_attrs}
        subjective_avg = (existing_attrs["attitude_score"] + existing_attrs["ability_score"] + existing_attrs["achievement_score"]) / 3
        if subjective_avg > 0:
            final_score = round(cumulative_score * 0.6 + subjective_avg * 0.4, 2)
        else:
            final_score = cumulative_score

        if existing:
            existing.mistake_total = mistake_total
            existing.mistake_deduction = mistake_deduction
            existing.reward_total = reward_total
            existing.reward_bonus = reward_bonus
            existing.quality_score = cumulative_score
            existing.final_score = final_score
            await existing.save()
            results.append({"staff_id": sid, "id": existing.id, "action": "updated"})
        else:
            eval_obj = await contractor_evaluation_controller.create({
                "staff_id": sid,
                "evaluation_month": gen_in.evaluation_month,
                "mistake_total": mistake_total,
                "mistake_deduction": mistake_deduction,
                "reward_total": reward_total,
                "reward_bonus": reward_bonus,
                "quality_score": cumulative_score,
                "final_score": final_score,
            })
            results.append({"staff_id": sid, "id": eval_obj.id, "action": "created"})

    return Success(msg=f"已为 {len(results)} 名人员生成考评", data={"results": results})


@router.post("/evaluation/rate", summary="月度考评分")
async def rate_evaluation(eval_in: ContractorEvaluationCreate):
    """填写主观评分（态度/能力/达成），自动结合考核数据计算最终得分"""
    existing = await ContractorEvaluation.filter(
        staff_id=eval_in.staff_id, evaluation_month=eval_in.evaluation_month
    ).first()

    # 从考核记录计算的质量分
    if existing:
        quality_score = float(existing.quality_score or 0)
    else:
        all_records = await ContractorAssessmentRecord.filter(staff_id=eval_in.staff_id).all()
        all_mistake = sum(r.count for r in all_records if r.type == "mistake")
        all_reward = sum(r.count for r in all_records if r.type == "reward")
        quality_score = round(max(0, 10 + all_reward * 0.1 - all_mistake * 0.1), 2)

    # 最终得分 = 质量分(60%) + 主观评分均值(40%)
    subj_scores = [float(eval_in.attitude_score or 0), float(eval_in.ability_score or 0), float(eval_in.achievement_score or 0)]
    subjective_avg = sum(subj_scores) / 3
    final_score = round(quality_score * 0.6 + subjective_avg * 0.4, 2) if subjective_avg > 0 else quality_score

    if existing:
        await contractor_evaluation_controller.update(existing.id, {**eval_in.model_dump(), "final_score": final_score})
        return Success(msg="评分已更新", data={"id": existing.id, "final_score": final_score})
    eval_obj = await contractor_evaluation_controller.create({**eval_in.model_dump(), "final_score": final_score})
    return Success(msg="评分成功", data={"id": eval_obj.id, "final_score": final_score})


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


# ==================== 项目管理 ====================
@router.get("/project/list", summary="项目列表")
async def list_project(
    page: int = Query(1, description="页码"),
    page_size: int = Query(100, description="每页数量"),
    name: str = Query("", description="项目名称"),
):
    q = Q(is_active=True)
    if name:
        q &= Q(name__contains=name)
    total, objs = await contractor_project_controller.list(page=page, page_size=page_size, search=q, order=["order", "-id"])
    data = [{"id": obj.id, "name": obj.name, "desc": obj.desc, "order": obj.order, "is_active": obj.is_active, "responsible_user_id": obj.responsible_user_id} for obj in objs]
    # 查询责任人名字
    uids = list({d["responsible_user_id"] for d in data if d["responsible_user_id"]})
    if uids:
        users = await User.filter(id__in=uids).all()
        umap = {u.id: (u.alias or u.username) for u in users}
        for d in data:
            d["responsible_user_name"] = umap.get(d["responsible_user_id"], "")
    return SuccessExtra(data=data, total=total, page=page, page_size=page_size)


@router.get("/project/get", summary="查看项目")
async def get_project(id: int = Query(..., description="项目ID")):
    obj = await contractor_project_controller.get(id)
    if not obj:
        return Fail(msg="项目不存在")
    return Success(data={"id": obj.id, "name": obj.name, "desc": obj.desc, "order": obj.order, "is_active": obj.is_active})


@router.post("/project/create", summary="创建项目")
async def create_project(proj_in: ContractorProjectCreate):
    obj = await contractor_project_controller.create(proj_in)
    return Success(msg="创建成功", data={"id": obj.id})


@router.post("/project/update", summary="更新项目")
async def update_project(proj_in: ContractorProjectUpdate):
    await contractor_project_controller.update(proj_in.id, proj_in)
    return Success(msg="更新成功")


@router.delete("/project/delete", summary="删除项目")
async def delete_project(proj_id: int = Query(..., description="项目ID")):
    await contractor_project_controller.remove(proj_id)
    return Success(msg="删除成功")

