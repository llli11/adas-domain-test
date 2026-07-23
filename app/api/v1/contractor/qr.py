"""
二维码公开 API（免登录）

所有接口通过 QR Token 识别外委人员身份。
QR Token 使用 PyJWT 生成，包含 staff_id 和过期时间，有效期 24 小时。
"""

import os
import time
import uuid

import jwt
from fastapi import APIRouter, Body, File, Form, UploadFile

from app.controllers.contractor import (
    contractor_leave_controller,
    contractor_vehicle_status_controller,
    contractor_work_log_controller,
)
from app.models.contractor import ContractorStaff, ContractorWorkLog
from app.schemas.base import Fail, Success
from app.schemas.contractor import QRDepartReturn, QRLeaveSubmit, QRWorkLogSubmit
from app.settings.config import settings

router = APIRouter()

QR_TOKEN_MAX_AGE = 86400  # 24 小时


def create_qr_token(staff_id: int) -> str:
    """生成二维码 Token"""
    payload = {"staff_id": staff_id, "exp": int(time.time()) + QR_TOKEN_MAX_AGE, "type": "qr"}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_qr_token(token: str) -> int:
    """解析二维码 Token，返回 staff_id"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
        if payload.get("type") != "qr":
            raise ValueError("invalid token type")
        return int(payload["staff_id"])
    except Exception:
        raise ValueError("invalid or expired token")


@router.get("/info", summary="二维码页面获取人员信息")
async def qr_info(token: str):
    try:
        staff_id = decode_qr_token(token)
    except ValueError:
        return Fail(msg="二维码已过期或无效")

    staff = await ContractorStaff.get_or_none(id=staff_id)
    if not staff:
        return Fail(msg="人员不存在")

    data = await staff.to_dict()
    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")
    log = await ContractorWorkLog.filter(staff_id=staff_id, work_date=today).first()
    data["today_worklog_submitted"] = bool(log)
    return Success(data=data)


@router.post("/depart", summary="二维码出发")
async def qr_depart(data: QRDepartReturn = Body(...)):
    try:
        staff_id = decode_qr_token(data.token)
    except ValueError:
        return Fail(msg="二维码已过期或无效")

    staff = await ContractorStaff.get_or_none(id=staff_id)
    if not staff:
        return Fail(msg="人员不存在")

    staff.task_status = "任务中"
    staff.is_idle = False
    staff.current_vehicle = data.vehicle_name
    staff.current_task = data.task_type
    await staff.save()

    from datetime import datetime
    await contractor_vehicle_status_controller.create({
        "staff_id": staff_id,
        "vehicle_name": data.vehicle_name,
        "task_type": data.task_type,
        "action": "出发",
        "action_time": datetime.now(),
    })

    return Success(msg="出发登记成功")


@router.post("/return", summary="二维码返回")
async def qr_return(data: QRDepartReturn = Body(...)):
    try:
        staff_id = decode_qr_token(data.token)
    except ValueError:
        return Fail(msg="二维码已过期或无效")

    staff = await ContractorStaff.get_or_none(id=staff_id)
    if not staff:
        return Fail(msg="人员不存在")

    staff.task_status = "空闲"
    staff.is_idle = True
    staff.current_vehicle = None
    staff.current_task = None
    await staff.save()

    from datetime import datetime
    await contractor_vehicle_status_controller.create({
        "staff_id": staff_id,
        "vehicle_name": data.vehicle_name,
        "task_type": data.task_type,
        "action": "返回",
        "action_time": datetime.now(),
    })

    return Success(msg="返回登记成功")


@router.post("/worklog", summary="二维码提交工作日志")
async def qr_worklog(data: QRWorkLogSubmit = Body(...)):
    try:
        staff_id = decode_qr_token(data.token)
    except ValueError:
        return Fail(msg="二维码已过期或无效")

    staff = await ContractorStaff.get_or_none(id=staff_id)
    if not staff:
        return Fail(msg="人员不存在")

    from datetime import datetime
    today = datetime.now().strftime("%Y-%m-%d")

    existing_log = await ContractorWorkLog.filter(staff_id=staff_id, work_date=today).first()
    if existing_log:
        await contractor_work_log_controller.update(existing_log.id, {
            "check_out_time": data.check_out_time,
            "check_out_image": data.check_out_image,
            "normal_hours": data.normal_hours,
            "overtime_hours": data.overtime_hours,
            "work_content": data.work_content,
            "project_id": data.project_id,
            "advance_payment": data.advance_payment,
            "advance_payment_image": data.advance_payment_image,
        })
    else:
        await contractor_work_log_controller.create({
            "staff_id": staff_id,
            "work_date": today,
            "check_out_time": data.check_out_time,
            "check_out_image": data.check_out_image,
            "normal_hours": data.normal_hours,
            "overtime_hours": data.overtime_hours,
            "work_content": data.work_content,
            "project_id": data.project_id,
            "advance_payment": data.advance_payment,
            "advance_payment_image": data.advance_payment_image,
        })

    return Success(msg="工作日志提交成功")


@router.post("/leave", summary="二维码提交请假申请")
async def qr_leave(data: QRLeaveSubmit = Body(...)):
    try:
        staff_id = decode_qr_token(data.token)
    except ValueError:
        return Fail(msg="二维码已过期或无效")

    staff = await ContractorStaff.get_or_none(id=staff_id)
    if not staff:
        return Fail(msg="人员不存在")

    await contractor_leave_controller.create({
        "staff_id": staff_id,
        "leave_date": data.leave_date,
        "leave_type": data.leave_type,
        "reason": data.reason,
    })

    return Success(msg="请假申请提交成功")


@router.post("/upload", summary="二维码上传图片（打卡截图/垫付证明）")
async def qr_upload(
    token: str = Form(..., description="QR Token"),
    file: UploadFile = File(..., description="图片文件"),
):
    try:
        staff_id = decode_qr_token(token)
    except ValueError:
        return Fail(msg="二维码已过期或无效")

    allowed_types = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}
    if file.content_type not in allowed_types:
        return Fail(msg=f"不支持的文件类型: {file.content_type}，仅支持 jpg/png/gif/webp/bmp")

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        return Fail(msg="文件大小不能超过 10MB")

    ext = os.path.splitext(file.filename)[1] if file.filename else ".jpg"
    if not ext:
        ext = ".jpg"
    filename = f"{uuid.uuid4().hex}{ext}"

    upload_dir = os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "uploads")
    upload_dir = os.path.abspath(upload_dir)
    os.makedirs(upload_dir, exist_ok=True)
    file_path = os.path.join(upload_dir, filename)

    with open(file_path, "wb") as f:
        f.write(contents)

    url = f"/uploads/{filename}"
    return Success(data={"url": url, "filename": filename})
