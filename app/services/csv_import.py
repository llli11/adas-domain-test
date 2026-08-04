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
    "车辆阶段",
    "车型配置",
    "车辆状态",
    "车辆状态备注",
    "任务状态",
    "试验任务",
    "测试人员",
    "驾驶人员",
    "借用人",
    "借车人账号",
    "借车人电话",
    "借车时间",
    "一级部门",
    "二级部门",
    "临牌到期时间",
    "借用到期时间",
    "借用天数",
    "临牌区域",
    "临牌有效区域",
    "临牌信息",
    "临牌&保险办理次数",
    "出差状态",
    "试验城市",
    "出门单",
    "停车位",
    "钥匙位置",
    "车管",
    "车管ID",
    "是否有管制物品",
    "试验日期",
    "所在省",
    "所在市",
    "详细地址",
    "是否监控",
    "监控方式",
    "7日利用率(%)",
    "在库时长",
    "试验策划",
    "试验策划ID",
    "保险区域",
    "纬度",
    "经度",
    "位置信息",
    "电池包状态",
    "电池包溯源码",
    "电池包零件号",
    "电池包额定电量",
    "发动机号",
    "前电机号",
    "后电机号",
    "借车人ID",
    "二维码",
    "是否VIN最早记录",
    "改制中",
    "数据来源",
    "飞书记录ID",
]

# CSV字段映射 → Vehicle模型字段
CSV_FIELD_MAP = {
    "车辆VN(*必填)": "vn",
    "车辆编号": "vehicle_code",
    "车型项目": "vehicle_model",
    "动力类型": "power_type",
    "颜色": "color",
    "车辆阶段": "vehicle_phase",
    "车型配置": "vehicle_model_config",
    "车辆状态": "vehicle_status",
    "车辆状态备注": "vehicle_status_note",
    "任务状态": "task_status",
    "试验任务": "test_task",
    "测试人员": "tester",
    "驾驶人员": "driver",
    "借用人": "borrower",
    "借车人账号": "borrower_account",
    "借车人电话": "borrower_phone",
    "借车时间": "borrow_time",
    "一级部门": "dept_l1",
    "二级部门": "dept_l2",
    "临牌到期时间": "temp_plate_expire_date",
    "借用到期时间": "borrow_expire_date",
    "借用天数": "borrow_days",
    "临牌区域": "temp_plate_area",
    "临牌有效区域": "temp_plate_valid_area",
    "临牌信息": "temp_plate_info",
    "临牌&保险办理次数": "temp_plate_insurance_count",
    "出差状态": "travel_status",
    "试验城市": "test_city",
    "出门单": "exit_permit",
    "停车位": "parking_spot",
    "钥匙位置": "key_location",
    "车管": "vehicle_manager",
    "车管ID": "vehicle_manager_id",
    "是否有管制物品": "has_controlled_items",
    "试验日期": "test_date",
    "所在省": "province",
    "所在市": "city",
    "详细地址": "address_detail",
    "是否监控": "is_monitored",
    "监控方式": "monitor_method",
    "7日利用率(%)": "borrower_7day_rate",
    "在库时长": "storage_days",
    "试验策划": "trial_plan",
    "试验策划ID": "trial_plan_id",
    "保险区域": "insurance_area",
    "纬度": "latitude",
    "经度": "longitude",
    "位置信息": "location_info",
    "电池包状态": "battery_pack_status",
    "电池包溯源码": "battery_pack_trace",
    "电池包零件号": "battery_pack_part_no",
    "电池包额定电量": "battery_pack_rated",
    "发动机号": "engine_no",
    "前电机号": "front_motor_no",
    "后电机号": "rear_motor_no",
    "借车人ID": "borrower_id",
    "二维码": "qr_code",
    "是否VIN最早记录": "is_first_vin_record",
    "改制中": "is_under_modification",
    "数据来源": "data_source",
    "飞书记录ID": "feishu_record_id",
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
        "P1", "标配", "正常", "",
        "待开始", "城市NCA", "李四", "王五",
        "张三", "zhangsan", "13800138000", "2025-03-01",
        "产品验证中心", "智驾域测试",
        "2025-06-30", "2025-12-31", "30",
        "湖北湖南", "湖北", "鄂A12345", "2",
        "未出差", "武汉", "EP2025001", "A-001",
        "门卫室", "王车管", "G001",
        "无", "2025-03-15",
        "湖北", "武汉", "XX路XX号",
        "是", "GPS",
        "85", "180", "试验策划A", "TPL001",
        "华东", "30.5", "114.1", "某停车场",
        "正常", "BS001", "BP001", "50kWh",
        "EN2025001", "FM001", "RM001",
        "B001", "QR001", "是", "否",
        "feishu", "rec_abc123",
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
            elif vehicle_field in ("latitude", "longitude", "borrower_7day_rate"):
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
            await vehicle_controller.upsert_by_vn(VehicleCreate(**row))
            if existing:
                updated_count += 1
            else:
                created_count += 1
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
