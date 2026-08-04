"""飞书多维表格同步服务"""
import json
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import httpx

from app.controllers.vehicle import vehicle_controller
from app.log import logger
from app.schemas.vehicles import VehicleCreate


# 默认飞书配置（数据源1：预定车辆信息表）
DEFAULT_FEISHU_CONFIG = {
    "APP_ID": "cli_a90024aeadb81bcc",
    "APP_SECRET": "niCTFud9R2cpOxc9mApN0oJdBCXXHbzz",
    "BASE_ID": "QjBvbZ6t4avKfNsYN1icwqJ4nKv",
    "TABLE_IDS": {
        "VEHICLES": "tblmuYWfpnWu0ntH",
        "DAILY_TASKS": "tblcxNXj1Y7kj6QK",
    },
}

# ================================================================
# 本地任务字段（仅手动填写，飞书同步绝不覆盖）
#   这些字段来自 Vehicle 模型，但数据不在飞书车辆信息表(tblmuYWfpnWu0ntH)中
#   由使用者在前端手动填写并保存到本地数据库，飞书同步时必须保护不覆盖
# ================================================================
VEHICLE_TASK_FIELDS = {
    "task_status",        # 任务状态
    "test_task",          # 试验任务
    "tester",             # 测试人员
    "driver",             # 驾驶人员
    "travel_status",      # 出差状态
    "test_city",          # 试验城市
    "exit_permit",        # 出门单
    "parking_spot",       # 停车位
    "location_info",      # 位置信息
    "latitude",           # 纬度
    "longitude",          # 经度
    "test_date",          # 试验日期
}

# ================================================================
# 飞书字段 → Vehicle模型字段映射
# ★ 仅映射车辆信息表中的静态字段，不包含 VEHICLE_TASK_FIELDS 中的任务字段
#   任务字段由用户手动填写，不从飞书同步
# ================================================================
FEISHU_FIELD_MAP = {
    "车辆VN": "vn",
    "车辆编号": "vehicle_code",
    "车型项目": "vehicle_model",
    "动力类型": "power_type",
    "颜色": "color",
    "是否有管制物品": "has_controlled_items",
    "借用人": "borrower",
    "借用到期时间": "borrow_expire_date",
    "临牌到期时间": "temp_plate_expire_date",
    "保险区域": "insurance_area",
    "当前借用人7日利用率": "borrower_7day_rate",
    # 临牌区域（飞书表中字段名可能是"临牌有效区域"或"临牌区域"）
    "临牌区域": "temp_plate_area",
    "临牌有效区域": "temp_plate_area",
    "改制中": "is_under_modification",
    "SourceID": "feishu_record_id",
    "车辆状态": "vehicle_status",
    "车辆状态备注": "vehicle_status_note",
    "钥匙位置": "key_location",
    "车管": "vehicle_manager",
    "车管ID": "vehicle_manager_id",
    "借用天数": "borrow_days",
    "借车时间": "borrow_time",
    "车辆阶段": "vehicle_phase",
    "车型配置": "vehicle_model_config",
    "临牌信息": "temp_plate_info",
    "临牌&保险办理次数": "temp_plate_insurance_count",
    "借车人": "borrower",
    "借车人账号": "borrower_account",
    "借车人ID": "borrower_id",
    "电话": "borrower_phone",
    "一级部门": "dept_l1",
    "二级部门": "dept_l2",
    "在库时长": "storage_days",
    "二维码": "qr_code",
    "车辆所在省": "province",
    "车辆所在市": "city",
    "详细地址": "address_detail",
    "是否监控": "is_monitored",
    "监控方式": "monitor_method",
    "是否VIN最早记录": "is_first_vin_record",
    "电池包状态": "battery_pack_status",
    "发动机号": "engine_no",
    "电池包溯源码": "battery_pack_trace",
    "前电机号": "front_motor_no",
    "后电机号": "rear_motor_no",
    "电池包零件号": "battery_pack_part_no",
    "电池包额定电量": "battery_pack_rated",
    "试验策划": "trial_plan",
    "试验策划ID": "trial_plan_id",
    # 同字段别名（飞书列名可能与旧名不同）
    "VIN": "vn",
    "动力配置": "power_type",
    "预计归还时间": "borrow_expire_date",
    "临牌&保险截止时间": "temp_plate_expire_date",
}


class FeishuSyncService:
    """飞书多维表格同步服务"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or DEFAULT_FEISHU_CONFIG
        self._client: Optional[httpx.AsyncClient] = None

    @property
    def http_client(self) -> httpx.AsyncClient:
        """惰性获取HTTP客户端，用完不关闭"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=300.0)
        return self._client

    async def get_tenant_access_token(self) -> str:
        """获取飞书 tenant_access_token"""
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
        payload = {
            "app_id": self.config["APP_ID"],
            "app_secret": self.config["APP_SECRET"],
        }
        logger.info(f"[Feishu] 正在获取 token, APP_ID={self.config['APP_ID'][:10]}...")
        try:
            response = await self.http_client.post(url, json=payload)
            data = response.json()
            logger.info(f"[Feishu] Token响应: code={data.get('code')}, msg={data.get('msg')}")
            if data.get("code") == 0:
                token = data["tenant_access_token"]
                logger.info("[Feishu] Tenant access token 获取成功")
                return token
            else:
                err_msg = data.get('msg', 'unknown')
                logger.error(f"[Feishu] 获取token失败: code={data.get('code')}, msg={err_msg}")
                if data.get('code') == 99991663:
                    raise Exception("飞书应用权限不足，请确认应用已开通多维表格(bitable)权限")
                raise Exception(f"获取飞书token失败: {err_msg} (code={data.get('code')})")
        except httpx.HTTPError as e:
            logger.error(f"[Feishu] Token请求网络异常: {e}")
            raise Exception(f"飞书API网络异常: {str(e)}")
        except Exception as e:
            if "获取飞书token失败" in str(e):
                raise
            logger.error(f"[Feishu] 获取token异常: {e}")
            raise

    async def get_bitable_records(
        self, token: str, table_id: str, page_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """获取飞书多维表格记录（分页）"""
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.config['BASE_ID']}/tables/{table_id}/records"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token

        logger.info(f"[Feishu] 读取表格: BASE_ID={self.config['BASE_ID']}, TABLE_ID={table_id}")
        try:
            response = await self.http_client.get(url, headers=headers, params=params)
            data = response.json()
            code = data.get("code", -1)
            msg = data.get("msg", "")
            logger.info(f"[Feishu] 表格响应: code={code}, msg={msg}")

            if code == 0:
                return data.get("data", {})
            elif code == 1254105:
                raise Exception(f"多维表格不存在或无权限访问 (code=1254105)，请检查BASE_ID和TABLE_ID是否正确，并确认应用已添加到多维表格的文档应用中")
            else:
                logger.error(f"[Feishu] 获取记录失败: {data}")
                raise Exception(f"获取飞书记录失败: {msg} (code={code})")
        except httpx.HTTPError as e:
            logger.error(f"[Feishu] 记录请求网络异常: {e}")
            raise Exception(f"飞书API网络异常: {str(e)}")
        except Exception as e:
            if "获取飞书记录失败" in str(e) or "多维表格不存在" in str(e):
                raise
            logger.error(f"[Feishu] 获取记录异常: {e}")
            raise

    async def get_table_fields(self, token: str, table_id: str) -> List[Dict[str, Any]]:
        """获取飞书多维表格的字段列表，用于验证字段名匹配"""
        url = f"https://open.feishu.cn/open-apis/bitable/v1/apps/{self.config['BASE_ID']}/tables/{table_id}/fields"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        logger.info(f"[Feishu] 获取表格字段列表: TABLE_ID={table_id}")
        try:
            response = await self.http_client.get(url, headers=headers)
            data = response.json()
            code = data.get("code", -1)
            if code == 0:
                items = data.get("data", {}).get("items", [])
                logger.info(f"[Feishu] 表格共有 {len(items)} 个字段:")
                for item in items:
                    field_name = item.get("field_name", "")
                    field_type = item.get("type", "")
                    logger.info(f"  - 字段名: '{field_name}', 类型: {field_type}, "
                               f"代码映射: '{FEISHU_FIELD_MAP.get(field_name, '❌ 未映射')}'")
                # 检查未映射的字段
                unmapped = [item.get("field_name") for item in items
                           if item.get("field_name") not in FEISHU_FIELD_MAP]
                if unmapped:
                    logger.warning(f"[Feishu] ⚠️ 以下 {len(unmapped)} 个字段未在FEISHU_FIELD_MAP中映射: {unmapped}")
                return items
            else:
                logger.warning(f"[Feishu] 获取字段列表失败: code={code}, msg={data.get('msg')}")
                return []
        except Exception as e:
            logger.warning(f"[Feishu] 获取字段列表异常: {e}")
            return []

    @staticmethod
    def _extract_user_value(user_obj: Dict[str, Any], vehicle_field: str) -> str:
        """从飞书人员字段对象中提取合适的值
        - vehicle_manager_id, trial_plan_id, borrower_id: 人员字段→提取人名
        - 其他 _id 字段 → 提取 id
        """
        if vehicle_field in ("vehicle_manager_id", "trial_plan_id", "borrower_id"):
            return user_obj.get("name", user_obj.get("id", str(user_obj)))
        if vehicle_field.endswith("_id"):
            return user_obj.get("id", str(user_obj))
        if vehicle_field in ("borrower_account",):
            return user_obj.get("email") or user_obj.get("name", str(user_obj))
        return user_obj.get("name", str(user_obj))

    def _map_feishu_record_to_vehicle(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """将飞书多维表格记录字段映射为Vehicle模型字典"""
        fields = record.get("fields", {})
        record_id = record.get("record_id", "unknown")
        vehicle_data: Dict[str, Any] = {"data_source": "feishu"}

        logger.debug(f"[Feishu] 记录 {record_id} 原始字段: {json.dumps(fields, ensure_ascii=False, default=str)[:500]}")

        mapped_count = 0
        for feishu_field, vehicle_field in FEISHU_FIELD_MAP.items():
            value = fields.get(feishu_field)
            if value is None:
                continue

            # 1. 飞书人员字段 → 可能是 dict（单人）或 list[dict]（多人）
            if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
                first = value[0]
                # 人员对象: {id, name, email, avatar_url, en_name, ...}
                if "id" in first and "name" in first:
                    value = self._extract_user_value(first, vehicle_field)
                # 文本类对象: {text, type, ...}
                elif "text" in first:
                    value = first.get("text", str(first))
                # 其他: 取 text 兜底
                elif "text" in (first.get("field_value") or {}):
                    value = first.get("field_value", {}).get("text", str(first))
                else:
                    value = str(first)
            elif isinstance(value, dict):
                # 单人人员对象: {id, name, email, ...}
                if "id" in value and "name" in value:
                    value = self._extract_user_value(value, vehicle_field)
                elif "text" in value:
                    value = value.get("text")
            elif isinstance(value, (int, float)):
                # 日期字段：飞书返回毫秒时间戳，需转为 date 对象
                if vehicle_field in ('borrow_expire_date', 'temp_plate_expire_date'):
                    if value > 10000000000:
                        value = date.fromtimestamp(value / 1000)
                    elif value > 0:
                        value = date.fromtimestamp(value)
                    else:
                        value = None
                # 文本字段收数字 → 转字符串或日期
                elif vehicle_field == 'borrow_time' and value > 10000000:
                    value = str(date.fromtimestamp(value / 1000))  # UTC毫秒 → YYYY-MM-DD
                elif vehicle_field in ('borrow_time', 'qr_code', 'borrower_phone', 'borrower_account', 'borrower_id'):
                    value = str(int(value)) if value > 0 else None

            vehicle_data[vehicle_field] = value
            mapped_count += 1

        logger.debug(f"[Feishu] 记录 {record_id} 成功映射 {mapped_count}/{len(FEISHU_FIELD_MAP)} 个字段, "
                     f"VN={vehicle_data.get('vn')}, "
                     f"车型={vehicle_data.get('vehicle_model')}, "
                     f"车辆编号={vehicle_data.get('vehicle_code')}")

        # ★ 安全防护：显式剔除所有本地任务字段
        # 即使 FEISHU_FIELD_MAP 误映射了任务字段（如"车位": "parking_spot"别名），
        # 这里也强制移除，确保飞书同步绝不覆盖用户手动填写的任务数据
        for field in VEHICLE_TASK_FIELDS:
            vehicle_data.pop(field, None)

        # 确保必填字段有默认值
        vehicle_data.setdefault("vn", "")
        vehicle_data.setdefault("vehicle_code", vehicle_data.get("vn", ""))
        vehicle_data.setdefault("vehicle_model", "")
        vehicle_data.setdefault("power_type", "")
        vehicle_data.setdefault("color", "")

        return vehicle_data

    async def sync_vehicles_from_feishu(self, table_id: Optional[str] = None) -> Dict[str, Any]:
        """同步飞书多维表格数据到本地数据库
        仅同步车辆信息表中的静态字段（VN、车型、借用人等）。
        ★ 不包含任务状态/测试人员/驾驶人员等任务字段 ——
          这些字段由用户手动填写编辑，不从飞书同步以免覆盖。
        Args:
            table_id: 可选的自定义表格ID（数据源2用），不传则使用默认VEHICLES表
        """
        try:
            token = await self.get_tenant_access_token()
        except Exception as e:
            logger.error(f"[Feishu] 同步失败 - 获取token失败: {e}")
            return {"success": False, "message": f"获取飞书token失败: {str(e)}", "created": 0, "updated": 0}

        created_count = 0
        updated_count = 0
        skipped_empty_vn = 0
        failed_count = 0
        total_records = 0

        # ===== 第一步：同步车辆信息表（仅静态字段，不含任务状态/测试人员/驾驶人员等）=====
        vehicle_table_id = table_id or self.config["TABLE_IDS"]["VEHICLES"]
        try:
            # 打印表格字段映射表（诊断用）
            await self.get_table_fields(token, vehicle_table_id)

            records = await self._fetch_all_records(token, vehicle_table_id)
            total_records += len(records)
            logger.info(f"[Feishu] 车辆信息表: 共读取 {len(records)} 条记录 (TABLE_ID={vehicle_table_id})")

            # 采样打印前3条记录的原始数据结构（诊断用）
            for i, record in enumerate(records[:3]):
                fields = record.get("fields", {})
                record_id = record.get("record_id", "?")
                logger.info(f"[Feishu] 采样记录[{i+1}] record_id={record_id}, "
                           f"field_names={list(fields.keys())[:10]}..., "
                           f"VN_raw={repr(fields.get('车辆VN', 'MISSING'))}")

            for record in records:
                vehicle_data = self._map_feishu_record_to_vehicle(record)
                vn = (vehicle_data.get("vn") or "").strip()
                if not vn:
                    skipped_empty_vn += 1
                    # 打印被跳过的记录详情（前10条）
                    if skipped_empty_vn <= 10:
                        fields = record.get("fields", {})
                        logger.warning(
                            f"[Feishu] 跳过空VN记录 [{skipped_empty_vn}]: "
                            f"record_id={record.get('record_id', '?')}, "
                            f"fields_keys={list(fields.keys())[:15]}, "
                            f"mapped_vn='{vehicle_data.get('vn')}'"
                        )
                    continue
                try:
                    existing = await vehicle_controller.get_by_vn(vn)
                    await vehicle_controller.upsert_by_vn(VehicleCreate(**vehicle_data))
                    if existing:
                        updated_count += 1
                    else:
                        created_count += 1
                except Exception as e:
                    failed_count += 1
                    logger.error(
                        f"[Feishu] 车辆信息同步失败 VN={vn}: {type(e).__name__}: {e}, "
                        f"vehicle_data_keys={list(vehicle_data.keys())[:10]}"
                    )
                    if failed_count <= 3:
                        logger.error(f"[Feishu] 失败数据采样: {json.dumps(vehicle_data, ensure_ascii=False, default=str)[:500]}")
        except Exception as e:
            logger.error(f"[Feishu] 车辆信息表同步异常: {type(e).__name__}: {e}", exc_info=True)

        # ===== 诊断摘要 =====
        diag_parts = [f"共读取 {total_records} 条", f"新增 {created_count}", f"更新 {updated_count}"]
        if skipped_empty_vn:
            diag_parts.append(f"跳过空VN {skipped_empty_vn} 条")
        if failed_count:
            diag_parts.append(f"失败 {failed_count} 条")

        message = "同步完成: " + "，".join(diag_parts)
        logger.info(f"[Feishu] ===== {message} =====")
        if skipped_empty_vn > 0:
            logger.warning(
                f"[Feishu] ⚠️ 有 {skipped_empty_vn} 条记录因VN为空被跳过。"
                f"请检查飞书表格中 '车辆VN' 列是否有数据，或字段名是否匹配。"
            )

        return {
            "success": True, "message": message,
            "total_records": total_records,
            "created": created_count, "updated": updated_count,
            "skipped_empty_vn": skipped_empty_vn,
            "failed": failed_count,
        }

    async def _fetch_all_records(self, token: str, table_id: str) -> List[Dict[str, Any]]:
        """分页获取某张表格的所有记录"""
        all_records = []
        page_token = None
        while True:
            result = await self.get_bitable_records(token, table_id, page_token)
            records = result.get("items", [])
            all_records.extend(records)
            page_token = result.get("has_more") and result.get("page_token")
            if not page_token:
                break
        return all_records


feishu_sync_service = FeishuSyncService()
