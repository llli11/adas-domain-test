from tortoise import fields

from .base import BaseModel, TimestampMixin


class Tool(BaseModel, TimestampMixin):
    tool_code = fields.CharField(max_length=100, unique=True, description="设备编号", index=True)
    tool_name = fields.CharField(max_length=100, description="设备名称", index=True)
    tool_type = fields.CharField(max_length=50, description="设备类别", index=True)
    specification = fields.CharField(max_length=200, null=True, description="规格型号")
    brand = fields.CharField(max_length=50, null=True, description="品牌")
    quantity = fields.IntField(default=1, description="设备数量")
    unit = fields.CharField(max_length=20, default="个", description="单位")
    location = fields.CharField(max_length=100, null=True, description="存放位置")
    status = fields.CharField(max_length=100, default="可用", description="状态: 可用/借出/维修/报废", index=True)
    purchase_date = fields.DateField(null=True, description="购买日期")
    warranty_period = fields.CharField(max_length=50, null=True, description="保修期限")
    responsible_person = fields.CharField(max_length=50, null=True, description="负责人")
    image_url = fields.CharField(max_length=500, null=True, description="设备图片URL")
    current_user = fields.CharField(max_length=50, null=True, description="当前使用者")
    is_in_stock = fields.BooleanField(default=True, description="是否在库", index=True)
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "tool"


class ToolBorrow(BaseModel, TimestampMixin):
    tool_id = fields.IntField(description="工具ID", index=True)
    tool_code = fields.CharField(max_length=100, description="工具编码", index=True)
    tool_name = fields.CharField(max_length=100, description="工具名称")
    borrower_id = fields.IntField(description="借用人ID", index=True)
    borrower_name = fields.CharField(max_length=50, description="借用人姓名", index=True)
    borrow_date = fields.DatetimeField(description="借用时间", index=True)
    expected_return_date = fields.DatetimeField(null=True, description="预计归还时间")
    actual_return_date = fields.DatetimeField(null=True, description="实际归还时间")
    status = fields.CharField(max_length=20, default="借用中", description="状态: 借用中/已归还/逾期", index=True)
    purpose = fields.CharField(max_length=200, null=True, description="借用用途")
    approver_id = fields.IntField(null=True, description="审批人ID")
    approver_name = fields.CharField(max_length=50, null=True, description="审批人姓名")
    approve_status = fields.CharField(max_length=20, default="待审批", description="审批状态: 待审批/已通过/已拒绝", index=True)
    approve_time = fields.DatetimeField(null=True, description="审批时间")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "tool_borrow"


class ToolInventory(BaseModel, TimestampMixin):
    task_code = fields.CharField(max_length=50, unique=True, description="盘点任务编码", index=True)
    task_name = fields.CharField(max_length=100, description="盘点任务名称", index=True)
    inventory_date = fields.DateField(description="盘点日期", index=True)
    status = fields.CharField(max_length=20, default="待盘点", description="状态: 待盘点/进行中/已完成", index=True)
    responsible_person = fields.CharField(max_length=50, null=True, description="责任人姓名")
    total_count = fields.IntField(default=0, description="应盘数量")
    actual_count = fields.IntField(default=0, description="实盘数量")
    diff_count = fields.IntField(default=0, description="差异数量")
    diff_explanation = fields.TextField(null=True, description="差异说明")
    complete_time = fields.DatetimeField(null=True, description="完成时间")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "tool_inventory"


class ToolInventoryDetail(BaseModel, TimestampMixin):
    inventory_id = fields.IntField(description="盘点任务ID", index=True)
    tool_id = fields.IntField(description="工具ID", index=True)
    tool_code = fields.CharField(max_length=100, description="工具编码")
    tool_name = fields.CharField(max_length=100, description="工具名称")
    book_quantity = fields.IntField(default=0, description="账面数量")
    actual_quantity = fields.IntField(default=0, description="实际数量")
    diff_quantity = fields.IntField(default=0, description="差异数量")
    status = fields.CharField(max_length=20, default="正常", description="状态: 正常/盘盈/盘亏")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "tool_inventory_detail"


class ToolRequirement(BaseModel, TimestampMixin):
    tool_name = fields.CharField(max_length=100, description="工具名称", index=True)
    tool_type = fields.CharField(max_length=50, description="工具类型", index=True)
    specification = fields.CharField(max_length=200, null=True, description="规格型号")
    quantity = fields.IntField(default=1, description="需求数量")
    requester_id = fields.IntField(description="需求人ID", index=True)
    requester_name = fields.CharField(max_length=50, description="需求人姓名")
    request_date = fields.DatetimeField(description="需求日期", index=True)
    reason = fields.TextField(null=True, description="需求原因")
    status = fields.CharField(max_length=20, default="待处理", description="状态: 待处理/已采购/已拒绝", index=True)
    handler_id = fields.IntField(null=True, description="处理人ID")
    handler_name = fields.CharField(max_length=50, null=True, description="处理人姓名")
    handle_time = fields.DatetimeField(null=True, description="处理时间")
    remark = fields.TextField(null=True, description="备注")

    class Meta:
        table = "tool_requirement"
