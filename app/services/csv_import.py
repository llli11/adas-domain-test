"""CSV导入服务"""
import csv
import io
from datetime import date, datetime
from typing import Any, Dict, List

from app.controllers.vehicle import vehicle_controller
from app.log import logger
from app.schemas.vehicles import VehicleCreate

# CSV模板表头（与车辆数据详情页表格列完全一致，除"操作"和"来源"外）
CSV_TEMPLATE_HEADERS = [
    "车辆VN(*必填)",
    "车辆编号",
    "车型项目",
    "动力类型",
    "颜色",
    "任务状态",
    "试验任务",
    "测试人员",
    "驾驶人员",
    "借用人",
    "临牌到期时间",
    "借用到期时间",
    "保险区域",
    "出差状态",
    "试验城市",
    "出门单",
    "停车位",
    "是否有管制物品",
    "试验日期",
]

# CSV字段映射 → Vehicle模型字段
CSV_FIELD_MAP = {
    "车辆VN(*必填)": "vn",
    "车辆编号": "vehicle_code",
    "车型项目": "vehicle_model",
    "动力类型": "power_type",
    "颜色": "color",
    "任务状态": "task_status",
    "试验任务": "test_task",
    "测试人员": "tester",
    "驾驶人员": "driver",
    "借用人": "borrower",
    "临牌到期时间": "temp_plate_expire_date",
    "借用到期时间": "borrow_expire_date",
    "保险区域": "insurance_area",
    "出差状态": "travel_status",
    "试验城市": "test_city",
    "出门单": "exit_permit",
    "停车位": "parking_spot",
    "是否有管制物品": "has_controlled_items",
    "试验日期": "test_date",
}


def _parse_date(value: str) -> date | None:
    """解析日期字符串，支持多种格式"""
    if not value or not value.strip():
        return None
    value = value.strip()
    formats = [
        "%Y-%m-%d",
        "%Y/%m/%d",
        "%Y.%m.%d",
        "%Y%m%d",
        "%m/%d/%Y",
        "%d/%m/%Y",
    ]
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _parse_float(value: str) -> float | None:
    """解析浮点数"""
    if not value or not value.strip():
        return None
    try:
        return float(value.strip())
    except (ValueError, TypeError):
        return None


def generate_csv_template() -> str:
    """生成CSV模板内容（UTF-8 BOM 编码）"""
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(CSV_TEMPLATE_HEADERS)
    # 示例行：完整数据
    writer.writerow([
        "VN20250001", "4101#", "项目A", "纯电", "白",
        "待开始", "城市NCA", "李四", "王五",
        "张三", "2025-06-30", "2025-12-31", "华东",
        "未出差", "上海", "EP2025001", "A-001",
        "无", "2025-03-15",
    ])
    return output.getvalue()


def parse_csv_content(content: str) -> tuple[List[Dict[str, Any]], List[str]]:
    """解析CSV内容，返回 (成功解析的数据行, 错误信息列表)"""
    reader = csv.DictReader(io.StringIO(content))
    errors: List[str] = []
    rows: List[Dict[str, Any]] = []

    for line_num, row in enumerate(reader, start=2):  # 第1行是表头
        vehicle_data: Dict[str, Any] = {}
        has_error = False

        for csv_field, vehicle_field in CSV_FIELD_MAP.items():
            raw_value = row.get(csv_field, "").strip()

            if vehicle_field in ("borrow_expire_date", "temp_plate_expire_date", "test_date"):
                vehicle_data[vehicle_field] = _parse_date(raw_value)
            elif vehicle_field in ("latitude", "longitude"):
                vehicle_data[vehicle_field] = _parse_float(raw_value)
            else:
                vehicle_data[vehicle_field] = raw_value if raw_value else None

        # 验证必填字段
        if not vehicle_data.get("vn"):
            errors.append(f"第{line_num}行: 车辆VN不能为空")
            has_error = True
        if not vehicle_data.get("vehicle_code"):
            vehicle_data["vehicle_code"] = vehicle_data.get("vn", "")

        # 设置默认值
        vehicle_data.setdefault("vehicle_model", "")
        vehicle_data.setdefault("power_type", "")
        vehicle_data.setdefault("color", "")
        vehicle_data.setdefault("location_info", None)
        vehicle_data.setdefault("latitude", None)
        vehicle_data.setdefault("longitude", None)
        vehicle_data["data_source"] = "csv"

        if not has_error:
            rows.append(vehicle_data)

    return rows, errors


async def import_csv_to_db(content: str) -> Dict[str, Any]:
    """将CSV内容导入数据库（逐行upsert_by_vn）"""
    rows, parse_errors = parse_csv_content(content)
    if not rows:
        return {
            "success": False,
            "message": f"没有有效的CSV数据。解析错误: {'; '.join(parse_errors)}",
            "created": 0,
            "updated": 0,
            "errors": parse_errors,
        }

    created_count = 0
    updated_count = 0
    import_errors: List[str] = list(parse_errors)

    for row in rows:
        vn = row.get("vn", "")
        try:
            existing = await vehicle_controller.get_by_vn(vn)
            if existing:
                updated_count += 1
            else:
                created_count += 1
            await vehicle_controller.upsert_by_vn(VehicleCreate(**row))
        except Exception as e:
            msg = f"导入失败 VN={vn}: {str(e)}"
            import_errors.append(msg)
            logger.error(f"[CSV Import] {msg}")

    total = created_count + updated_count
    message = f"导入完成: 共 {total} 条（新增 {created_count}, 更新 {updated_count}）"
    if import_errors:
        message += f"，{len(import_errors)} 条错误"

    logger.info(f"[CSV Import] {message}")
    return {
        "success": True,
        "message": message,
        "created": created_count,
        "updated": updated_count,
        "errors": import_errors,
    }
