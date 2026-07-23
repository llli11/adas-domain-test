from tortoise import fields, models


class ReleaseInfo(models.Model):
    id = fields.IntField(pk=True)
    vin = fields.CharField(max_length=50, unique=True, index=True)
    ecu_info = fields.JSONField(null=True)
    data_source = fields.CharField(max_length=50, default="vdc_export")
    remark = fields.TextField(null=True)
    modified_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "t_release_info"


class ReleaseTargetInfo(models.Model):
    id = fields.IntField(pk=True)
    target_name = fields.CharField(max_length=100, unique=True, index=True)
    ecu_info = fields.JSONField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "t_release_target_info"


class ReleaseInfoHistory(models.Model):
    id = fields.IntField(pk=True)
    vin = fields.CharField(max_length=50, index=True)
    ecu_info = fields.JSONField(null=True)
    data_source = fields.CharField(max_length=50, default="vdc_export")
    modified_at = fields.DatetimeField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(null=True)

    class Meta:
        table = "t_release_info_h"


class EcuOperationLog(models.Model):
    id = fields.IntField(pk=True)
    operation_type = fields.CharField(max_length=50)
    target_vin = fields.CharField(max_length=50, null=True)
    target_name = fields.CharField(max_length=100, null=True)
    operator = fields.CharField(max_length=100, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "t_ecu_operation_log"


class ECUIgnore(models.Model):
    id = fields.IntField(pk=True)
    vin = fields.CharField(max_length=50, index=True)
    ecu_name = fields.CharField(max_length=200)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "t_ecu_ignore"
        unique_together = (("vin", "ecu_name"),)
