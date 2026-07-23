"""用户飞书配置模型"""
from tortoise import fields

from .base import BaseModel, TimestampMixin


class UserFeishuConfig(BaseModel, TimestampMixin):
    """用户自定义飞书多维表格配置"""

    user_id = fields.BigIntField(index=True, description="用户ID")
    base_id = fields.CharField(max_length=200, description="飞书多维表格Base ID")
    table_id = fields.CharField(max_length=200, description="飞书多维表格Table ID")

    class Meta:
        table = "user_feishu_config"
        unique_together = ("user_id",)
