from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class ToolBase(BaseModel):
    tool_code: str = Field(..., description="设备编号", example="TOOL001")
    tool_name: str = Field(..., description="设备名称", example="万用表")
    tool_type: str = Field(..., description="设备类别", example="测量工具")
    specification: Optional[str] = Field(None, description="规格型号")
    brand: Optional[str] = Field(None, description="品牌")
    quantity: int = Field(default=1, description="设备数量")
    unit: str = Field(default="个", description="单位")
    location: Optional[str] = Field(None, description="存放位置")
    status: str = Field(default="可用", description="状态")
    purchase_date: Optional[date] = Field(None, description="购买日期")
    warranty_period: Optional[str] = Field(None, description="保修期限")
    responsible_person: Optional[str] = Field(None, description="负责人")
    image_url: Optional[str] = Field(None, description="设备图片URL")
    current_user: Optional[str] = Field(None, description="当前使用者")
    is_in_stock: bool = Field(default=True, description="是否在库")
    remark: Optional[str] = Field(None, description="备注")


class ToolCreate(ToolBase):
    pass


class ToolUpdate(BaseModel):
    tool_name: Optional[str] = None
    tool_type: Optional[str] = None
    specification: Optional[str] = None
    brand: Optional[str] = None
    quantity: Optional[int] = None
    unit: Optional[str] = None
    location: Optional[str] = None
    status: Optional[str] = None
    purchase_date: Optional[date] = None
    warranty_period: Optional[str] = None
    responsible_person: Optional[str] = None
    image_url: Optional[str] = None
    current_user: Optional[str] = None
    is_in_stock: Optional[bool] = None
    remark: Optional[str] = None


class ToolBorrowBase(BaseModel):
    tool_id: int = Field(..., description="工具ID")
    tool_code: str = Field(..., description="工具编码")
    tool_name: str = Field(..., description="工具名称")
    borrower_id: int = Field(..., description="借用人ID")
    borrower_name: str = Field(..., description="借用人姓名")
    borrow_date: datetime = Field(..., description="借用时间")
    expected_return_date: Optional[datetime] = Field(None, description="预计归还时间")
    purpose: Optional[str] = Field(None, description="借用用途")
    approver_id: Optional[int] = Field(None, description="审批人ID")
    approver_name: Optional[str] = Field(None, description="审批人姓名")
    remark: Optional[str] = Field(None, description="备注")


class ToolBorrowCreate(ToolBorrowBase):
    pass


class ToolBorrowUpdate(BaseModel):
    expected_return_date: Optional[datetime] = None
    actual_return_date: Optional[datetime] = None
    status: Optional[str] = None
    approve_status: Optional[str] = None
    approver_id: Optional[int] = None
    approver_name: Optional[str] = None
    approve_time: Optional[datetime] = None
    remark: Optional[str] = None


class ToolInventoryBase(BaseModel):
    task_code: str = Field(..., description="盘点任务编码")
    task_name: str = Field(..., description="盘点任务名称")
    inventory_date: date = Field(..., description="盘点日期")
    responsible_person: str = Field(..., description="责任人姓名")
    remark: Optional[str] = Field(None, description="备注")


class ToolInventoryCreate(ToolInventoryBase):
    pass


class ToolInventoryUpdate(BaseModel):
    task_name: Optional[str] = None
    inventory_date: Optional[date] = None
    status: Optional[str] = None
    total_count: Optional[int] = None
    actual_count: Optional[int] = None
    diff_count: Optional[int] = None
    diff_explanation: Optional[str] = None
    complete_time: Optional[datetime] = None
    remark: Optional[str] = None


class ToolInventoryDetailBase(BaseModel):
    inventory_id: int = Field(..., description="盘点任务ID")
    tool_id: int = Field(..., description="工具ID")
    tool_code: str = Field(..., description="工具编码")
    tool_name: str = Field(..., description="工具名称")
    book_quantity: int = Field(default=0, description="账面数量")
    actual_quantity: int = Field(default=0, description="实际数量")
    diff_quantity: int = Field(default=0, description="差异数量")
    status: str = Field(default="正常", description="状态")
    remark: Optional[str] = Field(None, description="备注")


class ToolInventoryDetailCreate(ToolInventoryDetailBase):
    pass


class ToolRequirementBase(BaseModel):
    tool_name: str = Field(..., description="工具名称")
    tool_type: str = Field(..., description="工具类型")
    specification: Optional[str] = Field(None, description="规格型号")
    quantity: int = Field(default=1, description="需求数量")
    requester_id: int = Field(..., description="需求人ID")
    requester_name: str = Field(..., description="需求人姓名")
    request_date: datetime = Field(..., description="需求日期")
    reason: Optional[str] = Field(None, description="需求原因")
    remark: Optional[str] = Field(None, description="备注")


class ToolRequirementCreate(ToolRequirementBase):
    pass


class ToolRequirementUpdate(BaseModel):
    status: Optional[str] = None
    handler_id: Optional[int] = None
    handler_name: Optional[str] = None
    handle_time: Optional[datetime] = None
    remark: Optional[str] = None
