from datetime import date, datetime, time

from fastapi import APIRouter, Body, Query
from tortoise.expressions import Q

from app.controllers.expense import daily_record_controller, engineer_attendance_controller, driver_attendance_controller
from app.models.expense import (
    RequirementPersonnel, TestOrder, EngineerAttendance, ExpenseProject,
)
from app.schemas import Success, Fail

router = APIRouter(tags=["费用管理"])


def _determine_person_type(supplier: str) -> str:
    """根据供应商判断人员类型"""
    if supplier in ("万嘉禾", "育喆"):
        return "驾驶员"
    return "工程师"


def _parse_personnel_names(outsourced_personnel: str) -> list:
    """解析委外人员姓名列表"""
    names = []
    if outsourced_personnel:
        for n in outsourced_personnel.replace("，", ",").replace("、", ",").split(","):
            n = n.strip()
            if n:
                names.append(n)
    return names


@router.get("/clock-in/test-orders", summary="获取可打卡的试验单号列表（公开）")
async def get_clock_in_test_orders(
    keyword: str = Query(None, description="搜索关键词"),
):
    """返回有委外人员配置的试验单号，供外委人员扫码选择"""
    personnel = await RequirementPersonnel.all().order_by("-id")
    data = []
    for p in personnel:
        test_order = await TestOrder.filter(test_order_no=p.test_order_no).first()
        if not test_order:
            continue
        names = _parse_personnel_names(p.outsourced_personnel)
        if not names:
            continue

        person_type = _determine_person_type(p.supplier or "")

        item = {
            "test_order_no": p.test_order_no,
            "test_order_id": test_order.id,
            "supplier": p.supplier or "",
            "person_type": person_type,
            "personnel_names": names,
        }

        if keyword:
            kw = keyword.strip()
            if kw not in p.test_order_no and kw not in (p.supplier or ""):
                continue

        # 获取项目信息
        expense_code = await test_order.expense_code
        if expense_code:
            budget = await expense_code.budget
            if budget:
                project = await budget.project
                if project:
                    item["project_name"] = project.project_name
                    item["series_name"] = project.series_name
                    item["project_id"] = project.id

        data.append(item)

    return Success(data=data)


@router.post("/clock-in/submit", summary="外委打卡提交（公开）")
async def clock_in_submit(
    test_order_no: str = Body(..., description="试验单号"),
    person_name: str = Body(..., description="人员姓名"),
    record_date: str = Body(..., description="日期 YYYY-MM-DD"),
    work_hours: float = Body(0, description="工时"),
    advance_payment: float = Body(0, description="垫付金额"),
):
    test_order = await TestOrder.filter(test_order_no=test_order_no).first()
    if not test_order:
        return Fail(msg="试验单号不存在")

    expense_code = await test_order.expense_code
    if not expense_code:
        return Fail(msg="费用号不存在")

    budget = await expense_code.budget
    if not budget:
        return Fail(msg="预算号不存在")

    try:
        parsed_date = date.fromisoformat(record_date)
    except ValueError:
        return Fail(msg="日期格式错误，应为 YYYY-MM-DD")

    # 补充：查找 RequirementPersonnel 确定人员类型
    rp = await RequirementPersonnel.filter(test_order_no=test_order_no).first()
    person_type = _determine_person_type(rp.supplier) if rp else "工程师"

    from app.schemas.expense import DailyRecordCreate

    record_in = DailyRecordCreate(
        project_id=budget.project_id,
        test_order_id=test_order.id,
        record_date=parsed_date,
        person_name=person_name,
        person_type=person_type,
        work_hours=work_hours,
        advance_payment=advance_payment,
        remark=f"外委扫码打卡({person_type})",
    )
    await daily_record_controller.create(obj_in=record_in)
    return Success(msg="打卡成功")


@router.post("/clock-in/engineer-submit", summary="工程师考勤打卡提交（公开）")
async def engineer_clock_in_submit(
    project_id: int = Body(..., description="项目ID"),
    test_order_no: str = Body(None, description="试验单号"),
    record_date: str = Body(..., description="日期 YYYY-MM-DD"),
    person_name: str = Body(..., description="填写人"),
    test_task: str = Body(None, description="试验任务"),
    car_number: str = Body(None, description="车辆编号"),
    start_time: str = Body(None, description="上班时间 HH:mm"),
    end_time: str = Body(None, description="下班时间 HH:mm"),
    is_overtime: bool = Body(None, description="是否加班"),
    overtime_hours: float = Body(None, description="加班时长(h)"),
    work_duration: float = Body(None, description="工作日时长(h)"),
    total_hours: float = Body(None, description="当天总工时(h)"),
    travel_status: str = Body(None, description="出差状态"),
    work_location: str = Body(None, description="工作地点"),
    location_coords: str = Body(None, description="定位位置"),
    workload: str = Body(None, description="当天工作量(次/km)"),
    problems_found: int = Body(None, description="行车泊车发现问题数"),
    check_cases: int = Body(None, description="点检用例数"),
    software_flash_count: int = Body(None, description="整备车辆刷写软件数量"),
    approver1: str = Body(None, description="审批人1"),
    approver2: str = Body(None, description="审批人2"),
    issue_detail: str = Body(None, description="问题明细"),
    test_version: str = Body(None, description="试验版本"),
):
    try:
        parsed_date = date.fromisoformat(record_date)
    except ValueError:
        return Fail(msg="日期格式错误，应为 YYYY-MM-DD")

    # 查找 test_order
    test_order_id = None
    if test_order_no:
        test_order = await TestOrder.filter(test_order_no=test_order_no).first()
        if not test_order:
            return Fail(msg="试验单号不存在")
        test_order_id = test_order.id

    # 转换时间字符串为 time 对象
    parsed_start = None
    if start_time:
        try:
            h, m = start_time.split(":")
            parsed_start = time(int(h), int(m))
        except (ValueError, TypeError):
            pass

    parsed_end = None
    if end_time:
        try:
            h, m = end_time.split(":")
            parsed_end = time(int(h), int(m))
        except (ValueError, TypeError):
            pass

    # 自动获取项目审批人
    project = await ExpenseProject.get_or_none(id=project_id)
    auto_approver2 = project.approver if project and project.approver else (approver2 or "")

    # 构建数据字典
    record_data = {
        "project_id": project_id,
        "test_order_id": test_order_id,
        "record_date": parsed_date,
        "person_name": person_name,
        "test_task": test_task,
        "car_number": car_number,
        "start_time": parsed_start,
        "end_time": parsed_end,
        "is_overtime": bool(is_overtime) if is_overtime is not None else False,
        "overtime_hours": overtime_hours or 0,
        "work_duration": work_duration or 0,
        "total_hours": total_hours or 0,
        "travel_status": travel_status,
        "work_location": work_location,
        "location_coords": location_coords,
        "workload": workload,
        "problems_found": problems_found or 0,
        "check_cases": check_cases or 0,
        "software_flash_count": software_flash_count or 0,
        "approver1": approver1 or "",
        "approver1_result": "",
        "approver2": auto_approver2,
        "approver2_result": "待审批",
        "issue_detail": issue_detail,
        "test_version": test_version,
        "attachment_url": "",
        "approve_type": "外委打卡",
        "task_status": "待审批",
    }
    await engineer_attendance_controller.create(obj_in=record_data)

    # 同时写入 DailyRecord 用于统一费用归集
    from app.schemas.expense import DailyRecordCreate

    daily_in = DailyRecordCreate(
        project_id=project_id,
        test_order_id=test_order_id,
        record_date=parsed_date,
        person_name=person_name,
        person_type="工程师",
        work_hours=total_hours or 0,
        advance_payment=0,
        remark=f"工程师考勤打卡 - {test_task or ''}",
    )
    await daily_record_controller.create(obj_in=daily_in)

    return Success(msg="打卡成功")


@router.post("/clock-in/driver-submit", summary="驾驶员考勤打卡提交（公开）")
async def driver_clock_in_submit(
    test_order_no: str = Body(None, description="试验单号（可选，用试验需求编号代替）"),
    person_name: str = Body(..., description="填写人"),
    record_date: str = Body(..., description="日期 YYYY-MM-DD"),
    requirement_code: str = Body(None, description="试验需求编号"),
    expense_settle_project: str = Body(None, description="垫付费用结算项目"),
    test_version: str = Body(None, description="试验版本"),
    test_task: str = Body(None, description="试验任务"),
    car_number: str = Body(None, description="车辆编号"),
    start_time: str = Body(None, description="上班时间 HH:mm"),
    end_time: str = Body(None, description="下班时间 HH:mm"),
    is_overtime: str = Body("否", description="是否加班: 是/否"),
    work_duration: float = Body(0, description="工作日时长(h)"),
    overtime_hours: float = Body(0, description="加班时长(h)"),
    total_hours: float = Body(0, description="当天总工时"),
    travel_status: str = Body(None, description="出差状态"),
    work_location: str = Body(None, description="工作地点"),
    location_coords: str = Body(None, description="定位位置"),
    vehicle_initial_mileage: float = Body(None, description="车辆初始里程"),
    vehicle_end_mileage: float = Body(None, description="车辆结束里程"),
    daily_advance_total: float = Body(0, description="当日垫付费用总计"),
    expense_details: list = Body(None, description="费用明细: [{type,amount,attachment}]"),
    attachment_url: str = Body("", description="考勤打卡附件"),
    expense_attachment_url: str = Body("", description="垫付费用附件"),
):
    try:
        parsed_date = date.fromisoformat(record_date)
    except ValueError:
        return Fail(msg="日期格式错误，应为 YYYY-MM-DD")

    # 查找 test_order
    test_order_id = None
    project_id = None
    if test_order_no:
        test_order = await TestOrder.filter(test_order_no=test_order_no).first()
        if test_order:
            test_order_id = test_order.id
            expense_code = await test_order.expense_code
            if expense_code:
                budget = await expense_code.budget
                if budget:
                    project_id = budget.project_id

    # 转换时间
    parsed_start = None
    if start_time:
        try:
            h, m = start_time.split(":")
            parsed_start = time(int(h), int(m))
        except (ValueError, TypeError):
            pass

    parsed_end = None
    if end_time:
        try:
            h, m = end_time.split(":")
            parsed_end = time(int(h), int(m))
        except (ValueError, TypeError):
            pass

    if not project_id:
        rp = await RequirementPersonnel.filter(test_order_no=test_order_no).first()
        if rp:
            projects = await ExpenseProject.filter(
                project_name__contains=test_order_no.split("-")[0] if "-" in test_order_no else ""
            ).first()
            project_id = projects.id if projects else 1

    # 自动获取审批人（优先取试验单号负责人，其次取项目审批人）
    auto_approver2 = ""
    if test_order_id:
        test_order = await TestOrder.get_or_none(id=test_order_id)
        if test_order and test_order.responsible_person:
            auto_approver2 = test_order.responsible_person
    if not auto_approver2 and project_id:
        project = await ExpenseProject.get_or_none(id=project_id)
        if project and project.approver:
            auto_approver2 = project.approver

    record_data = {
        "project_id": project_id or 1,
        "test_order_id": test_order_id,
        "record_date": parsed_date,
        "person_name": person_name,
        "requirement_code": requirement_code,
        "expense_settle_project": expense_settle_project,
        "test_version": test_version,
        "test_task": test_task,
        "car_number": car_number,
        "start_time": parsed_start,
        "end_time": parsed_end,
        "is_overtime": is_overtime,
        "work_duration": work_duration,
        "overtime_hours": overtime_hours,
        "total_hours": total_hours,
        "travel_status": travel_status,
        "work_location": work_location,
        "location_coords": location_coords,
        "vehicle_initial_mileage": vehicle_initial_mileage,
        "vehicle_end_mileage": vehicle_end_mileage,
        "daily_advance_total": daily_advance_total,
        "expense_details": expense_details,
        "attachment_url": attachment_url or "",
        "expense_attachment_url": expense_attachment_url or "",
        "approver2": auto_approver2,
        "approver2_result": "待审批",
    }
    await driver_attendance_controller.create(obj_in=record_data)
    return Success(msg="打卡成功")
