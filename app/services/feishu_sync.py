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
    "BASE_ID": "COj6bs7p9ap6znsJ23Fcr2rnnlf",
    "TABLE_IDS": {
        "VEHICLES": "tblLWwxtCzoFkcqh",
        "DAILY_TASKS": "tblnotoTknWAKkcu",
    },
}

# 飞书字段 → Vehicle模型字段映射（预设20个字段）
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
    "试验日期": "test_date",
    "任务状态": "task_status",
    "试验任务": "test_task",
    "测试人员": "tester",
    "驾驶人员": "driver",
    "出差状态": "travel_status",
    "试验城市": "test_city",
    "出门单": "exit_permit",
    "停车位": "parking_spot",
    "位置信息": "location_info",
    "纬度": "latitude",
    "经度": "longitude",
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
            self._client = httpx.AsyncClient(timeout=30.0)
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

    def _map_feishu_record_to_vehicle(self, record: Dict[str, Any]) -> Dict[str, Any]:
        """将飞书多维表格记录字段映射为Vehicle模型字典"""
        fields = record.get("fields", {})
        record_id = record.get("record_id", "unknown")
        vehicle_data: Dict[str, Any] = {"data_source": "feishu"}

        # 详细日志：记录飞书表格中的原始字段名和值（取前5条采样避免日志爆炸）
        logger.debug(f"[Feishu] 记录 {record_id} 原始字段: {json.dumps(fields, ensure_ascii=False, default=str)[:500]}")

        mapped_count = 0
        for feishu_field, vehicle_field in FEISHU_FIELD_MAP.items():
            value = fields.get(feishu_field)
            if value is not None:
                # 处理飞书多维表格特殊类型
                if isinstance(value, list) and len(value) > 0:
                    # 可能是附件/多选等
                    if isinstance(value[0], dict):
                        value = value[0].get("text", str(value[0]))
                    else:
                        value = str(value[0])
                elif isinstance(value, (int, float)):
                    # 日期字段：飞书返回毫秒时间戳，需转为 date 对象
                    if vehicle_field in ('borrow_expire_date', 'temp_plate_expire_date', 'test_date'):
                        if value > 10000000000:  # 毫秒时间戳
                            value = date.fromtimestamp(value / 1000)
                        elif value > 0:  # 秒级时间戳
                            value = date.fromtimestamp(value)
                        else:
                            value = None
                    else:
                        value = value
                vehicle_data[vehicle_field] = value
                mapped_count += 1

        logger.debug(f"[Feishu] 记录 {record_id} 成功映射 {mapped_count}/{len(FEISHU_FIELD_MAP)} 个字段, "
                     f"VN={vehicle_data.get('vn')}, "
                     f"任务状态={vehicle_data.get('task_status')}, "
                     f"试验任务={vehicle_data.get('test_task')}")

        # 确保必填字段有默认值
        vehicle_data.setdefault("vn", "")
        vehicle_data.setdefault("vehicle_code", vehicle_data.get("vn", ""))
        vehicle_data.setdefault("vehicle_model", "")
        vehicle_data.setdefault("power_type", "")
        vehicle_data.setdefault("color", "")

        return vehicle_data

    async def sync_vehicles_from_feishu(self, table_id: Optional[str] = None) -> Dict[str, Any]:
        """同步飞书多维表格数据到本地数据库
        先同步车辆信息表（基础字段），再同步每日任务表（任务状态字段），通过VN匹配合并
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
        total_records = 0

        # ===== 第一步：同步车辆信息表（基础字段）=====
        vehicle_table_id = table_id or self.config["TABLE_IDS"]["VEHICLES"]
        try:
            records = await self._fetch_all_records(token, vehicle_table_id)
            total_records += len(records)
            logger.info(f"[Feishu] 车辆信息表: {len(records)} 条记录")

            for record in records:
                vehicle_data = self._map_feishu_record_to_vehicle(record)
                if not vehicle_data.get("vn") or not vehicle_data["vn"].strip():
                    continue
                try:
                    existing = await vehicle_controller.get_by_vn(vehicle_data["vn"])
                    if existing: updated_count += 1
                    else: created_count += 1
                    await vehicle_controller.upsert_by_vn(VehicleCreate(**vehicle_data))
                except Exception as e:
                    logger.error(f"[Feishu] 车辆信息同步失败 VN={vehicle_data.get('vn')}: {e}")
        except Exception as e:
            logger.error(f"[Feishu] 车辆信息表同步异常: {e}")

        # ===== 第二步：同步每日任务表（任务状态字段），通过VN匹配更新 =====
        if not table_id:
            daily_table_id = self.config["TABLE_IDS"]["DAILY_TASKS"]
            try:
                task_records = await self._fetch_all_records(token, daily_table_id)
                total_records += len(task_records)
                logger.info(f"[Feishu] 每日任务表: {len(task_records)} 条记录")
                task_updated = 0
                for record in task_records:
                    task_data = self._map_feishu_record_to_vehicle(record)
                    vn = task_data.get("vn", "").strip()
                    if not vn:
                        continue
                    # 只提取任务相关字段，通过VN匹配已有车辆记录更新
                    task_fields = {
                        k: v for k, v in task_data.items()
                        if k in ("task_status", "test_task", "tester", "driver",
                                 "travel_status", "test_city", "location_info",
                                 "latitude", "longitude") and v is not None
                    }
                    if task_fields:
                        existing = await vehicle_controller.get_by_vn(vn)
                        if existing:
                            existing.update_from_dict(task_fields)
                            await existing.save()
                            task_updated += 1
                logger.info(f"[Feishu] 每日任务表: 合并更新 {task_updated} 条车辆任务状态")
            except Exception as e:
                logger.warning(f"[Feishu] 每日任务表同步异常（车辆信息已同步）: {e}")

        message = f"同步完成: 共读取 {total_records} 条，新增 {created_count}，更新 {updated_count}"
        logger.info(f"[Feishu] {message}")
        return {
            "success": True, "message": message,
            "total_records": total_records,
            "created": created_count, "updated": updated_count,
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
