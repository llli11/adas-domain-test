import json
import base64
import io
from typing import Optional
from datetime import datetime
from tortoise.expressions import Q
from app.core.crud import CRUDBase
from app.models.mapway import Mapway, RouteDetail, RouteDetailSelfDeveloped
from app.schemas.mapway import MapwayCreate, MapwayUpdate, RouteDetailCreate, RouteDetailUpdate, \
    RouteDetailSelfDevelopedCreate, RouteDetailSelfDevelopedUpdate


def generate_thumbnails_from_base64(image_json_str, max_size=100, quality=50):
    if not image_json_str:
        return []
    try:
        images = json.loads(image_json_str) if isinstance(image_json_str, str) else image_json_str
    except (json.JSONDecodeError, TypeError):
        return []
    if not isinstance(images, list):
        return []
    try:
        from PIL import Image
    except ImportError:
        import logging
        logging.warning("Pillow 未安装，无法生成缩略图，请执行: pip install Pillow")
        return []
    thumbnails = []
    for img_b64 in images:
        if not img_b64 or not isinstance(img_b64, str):
            thumbnails.append('')
            continue
        try:
            if img_b64.startswith('data:'):
                _, b64data = img_b64.split(',', 1)
            else:
                b64data = img_b64
            img_bytes = base64.b64decode(b64data)
            img = Image.open(io.BytesIO(img_bytes))
            img.thumbnail((max_size, max_size))
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')
            buf = io.BytesIO()
            img.save(buf, format='JPEG', quality=quality)
            thumb_b64 = 'data:image/jpeg;base64,' + base64.b64encode(buf.getvalue()).decode()
            thumbnails.append(thumb_b64)
        except Exception as e:
            import logging
            logging.warning(f"生成缩略图失败: {e}, 原始数据前50字符: {str(img_b64)[:50]}")
            thumbnails.append('')
    return thumbnails


def serialize_values(data):
    if isinstance(data, list):
        return [serialize_values(item) for item in data]
    if isinstance(data, dict):
        return {k: v.isoformat() if isinstance(v, datetime) else v for k, v in data.items()}
    return data


class MapwayController(CRUDBase[Mapway, MapwayCreate, MapwayUpdate]):
    """区域数据 CRUD 控制器"""

    def __init__(self):
        super().__init__(model=Mapway)

    async def get_by_name(self, area: str, project_type: str = "cooperative") -> Optional[Mapway]:
        """根据区域名称和项目类型查询"""
        return await self.model.filter(area=area, project_type=project_type).first()

    async def search(self, keyword: str, project_type: str = "cooperative", page: int = 1, page_size: int = 10):
        """模糊搜索区域（按名称或城市匹配，按项目类型过滤）"""
        q = Q(project_type=project_type)
        if keyword:
            q &= Q(area__contains=keyword) | Q(city__contains=keyword)
        return await self.list(page=page, page_size=page_size, search=q)
    
    """城市手动拖动"""
    async def move_city(self, city: str, from_area_id: int, to_area_id: int):
        # 获取源区域和目标区域
        from_area = await self.model.filter(id=from_area_id).first()
        to_area = await self.model.filter(id=to_area_id).first()
        if not from_area or not to_area:
            raise ValueError("区域不存在")
        
        from_cities = from_area.city.split('、') if from_area.city else []
        to_cities = to_area.city.split('、') if to_area.city else []
        
        # 城市必须在源区域中，且不在目标区域中
        if city not in from_cities:
            raise ValueError(f"城市 {city} 不在源区域中")
        if city in to_cities:
            raise ValueError(f"城市 {city} 已在目标区域中")
        
        # 移除并添加
        from_cities.remove(city)
        to_cities.append(city)
        
        from_area.city = '、'.join(from_cities)
        to_area.city = '、'.join(to_cities)
        
        await from_area.save()
        await to_area.save()

# ★ 对外暴露的单例实例，供 API 路由层直接引用
mapway_controller = MapwayController()


class RouteDetailController(CRUDBase[RouteDetail, RouteDetailCreate, RouteDetailUpdate]):
    def __init__(self):
        super().__init__(model=RouteDetail)

    async def list_by_city(self, city: str, page: int = 1, page_size: int = 100):
        q = Q(city=city)
        total = await self.model.filter(q).count()
        exclude = ['route_image', 'created_at', 'updated_at']
        select_fields = [f for f in self.model._meta.db_fields if f not in exclude]
        objs = await self.model.filter(q).order_by('id').offset((page - 1) * page_size).limit(page_size).values(*select_fields)
        return total, serialize_values(objs)

    async def list_by_city_with_thumbnails(self, city: str, page: int = 1, page_size: int = 100):
        q = Q(city=city)
        total = await self.model.filter(q).count()
        exclude = ['created_at', 'updated_at']
        select_fields = [f for f in self.model._meta.db_fields if f not in exclude]
        objs = await self.model.filter(q).order_by('id').offset((page - 1) * page_size).limit(page_size).values(*select_fields)
        for obj in objs:
            img_val = obj.pop('route_image', None)
            if img_val:
                try:
                    obj['image_count'] = len(json.loads(img_val)) if isinstance(img_val, str) else 0
                except (json.JSONDecodeError, TypeError):
                    obj['image_count'] = 1 if img_val else 0
            else:
                obj['image_count'] = 0
        return total, serialize_values(objs)

    async def list_by_city_grouped(self, city: str, page: int = 1, page_size: int = 100):
        q = Q(city=city)
        total = await self.model.filter(q).count()
        exclude = ['created_at', 'updated_at']
        select_fields = [f for f in self.model._meta.db_fields if f not in exclude]
        objs = await self.model.filter(q).order_by('id').offset((page - 1) * page_size).limit(page_size).values(*select_fields)
        for obj in objs:
            img_val = obj.pop('route_image', None)
            if img_val:
                try:
                    obj['image_count'] = len(json.loads(img_val)) if isinstance(img_val, str) else 0
                except (json.JSONDecodeError, TypeError):
                    obj['image_count'] = 1 if img_val else 0
            else:
                obj['image_count'] = 0

        groups = {"CNCA": [], "HNCA": []}
        for obj in objs:
            rt = (obj.get('route_type') or '').strip()
            if '高速' in rt:
                groups["HNCA"].append(obj)
            else:
                groups["CNCA"].append(obj)

        result = []
        for key in ["CNCA", "HNCA"]:
            result.append({"route_type": key, "items": groups[key]})

        return total, result

    async def get_route_image(self, route_id: int):
        obj = await self.model.filter(id=route_id).first()
        if not obj:
            return None
        return await obj.to_dict(exclude_fields=[f for f in self.model._meta.db_fields if f not in ('id', 'route_image')])
    
    async def search_by_field(self, field: str, keyword: str = None, page: int = 1, page_size: int = 20, order: str = "desc"):
        # 合法字段白名单（与 editableFields 对应）
        SEARCHABLE_FIELDS = [
            'route_order', 'priority', 'author', 'route_type', 'mileage', 'duration',
            'waypoints', 'route_preference', 'near_store', 'merge_in_num', 'merge_out_num',
            'y_intersection_num', 'roundabout_num', 'u_turn_num', 'straight_intersection_num',
            'protected_left_num', 'unprotected_left_num', 'protected_right_num',
            'unprotected_right_num', 'normal_traffic_light_num', 'flashing_yellow_num',
            'disabled_traffic_light_num', 'special_traffic_light_num', 'main_side_switch_num',
            'right_turn_lane_num', 'variable_lane_num', 'waiting_lane_num', 'complexity', 'remark'
        ]
        # 数值类型字段集合（整数字段）
        NUMERIC_FIELDS = {
            'merge_in_num', 'merge_out_num', 'y_intersection_num', 'roundabout_num',
            'u_turn_num', 'straight_intersection_num', 'protected_left_num', 'unprotected_left_num',
            'protected_right_num', 'unprotected_right_num', 'normal_traffic_light_num',
            'flashing_yellow_num', 'disabled_traffic_light_num', 'special_traffic_light_num',
            'main_side_switch_num', 'right_turn_lane_num', 'variable_lane_num', 'waiting_lane_num'
        }

        if field not in SEARCHABLE_FIELDS:
            raise ValueError(f"不支持检索的字段: {field}")
        
        q = Q()
        if keyword:
            # 判断是否为数字，且字段是数值类型
            if field in NUMERIC_FIELDS:
                try:
                    num_val = int(keyword)
                    q &= Q(**{field: num_val})
                except ValueError:
                    # 如果输入的不是数字，回退到模糊搜索
                    q &= Q(**{f"{field}__icontains": keyword})
            else:
                q &= Q(**{f"{field}__icontains": keyword})
        
        is_desc = order != 'asc'
        queryset = self.model.filter(q)
        total = await queryset.count()
        select_fields = ['id', 'route_order', 'city', field]

        STRING_NUMERIC_FIELDS = {'duration', 'mileage', 'priority'}
        if field in STRING_NUMERIC_FIELDS:
            all_data = await queryset.values(*select_fields)
            if field == 'duration':
                all_data.sort(key=lambda x: float(x.get('duration') or 0), reverse=is_desc)
            elif field == 'mileage':
                all_data.sort(key=lambda x: float(x.get('mileage') or 0), reverse=is_desc)
            elif field == 'priority':
                priority_order = {'L0': 0, 'L1': 1, 'L2': 2}
                all_data.sort(key=lambda x: priority_order.get(x.get('priority'), 99), reverse=is_desc)
            data = all_data
        else:
            order_by = f"-{field}" if (is_desc and field in NUMERIC_FIELDS) else (field if field in NUMERIC_FIELDS else "-id" if is_desc else "id")
            data = await queryset.order_by(order_by).values(*select_fields)
            if not is_desc and field in NUMERIC_FIELDS:
                data = sorted(data, key=lambda x: x.get(field) or 0)

        return total, serialize_values(data)

    async def filter_routes(self, conditions: list, logic: str = "and", page: int = 1, page_size: int = 20):
        SEARCHABLE_FIELDS = [
            'route_order', 'priority', 'author', 'route_type', 'mileage', 'duration',
            'waypoints', 'route_preference', 'near_store', 'merge_in_num', 'merge_out_num',
            'y_intersection_num', 'roundabout_num', 'u_turn_num', 'straight_intersection_num',
            'protected_left_num', 'unprotected_left_num', 'protected_right_num',
            'unprotected_right_num', 'normal_traffic_light_num', 'flashing_yellow_num',
            'disabled_traffic_light_num', 'special_traffic_light_num', 'main_side_switch_num',
            'right_turn_lane_num', 'variable_lane_num', 'waiting_lane_num', 'complexity', 'remark'
        ]
        STRING_NUMERIC_FIELDS = {'duration', 'mileage', 'priority'}
        NUMERIC_FIELDS = {
            'merge_in_num', 'merge_out_num', 'y_intersection_num', 'roundabout_num',
            'u_turn_num', 'straight_intersection_num', 'protected_left_num', 'unprotected_left_num',
            'protected_right_num', 'unprotected_right_num', 'normal_traffic_light_num',
            'flashing_yellow_num', 'disabled_traffic_light_num', 'special_traffic_light_num',
            'main_side_switch_num', 'right_turn_lane_num', 'variable_lane_num', 'waiting_lane_num'
        }

        q_filters = []
        python_filters = []
        select_fields_set = {'id', 'route_order', 'city', 'route_type'}

        for cond in conditions:
            field = cond.get('field', '')
            operator = cond.get('operator', '')
            value = cond.get('value', '')

            if field not in SEARCHABLE_FIELDS:
                continue
            if not operator:
                continue

            select_fields_set.add(field)

            if operator == 'is_empty':
                q = Q(**{field: ''}) | Q(**{f"{field}__isnull": True})
                q_filters.append(q)
            elif operator == 'is_not_empty':
                q = ~Q(**{field: ''}) & ~Q(**{f"{field}__isnull": True})
                q_filters.append(q)
            elif operator in ('equals', 'not_equals', 'contains', 'not_contains', 'greater_than', 'less_than'):
                if not value and operator not in ('is_empty', 'is_not_empty'):
                    continue
                if field in NUMERIC_FIELDS:
                    try:
                        num_val = int(value)
                    except (ValueError, TypeError):
                        num_val = None
                    if operator == 'equals':
                        q_filters.append(Q(**{field: num_val}))
                    elif operator == 'not_equals':
                        q_filters.append(~Q(**{field: num_val}))
                    elif operator == 'greater_than' and num_val is not None:
                        q_filters.append(Q(**{f"{field}__gt": num_val}))
                    elif operator == 'less_than' and num_val is not None:
                        q_filters.append(Q(**{f"{field}__lt": num_val}))
                    elif operator == 'contains':
                        q_filters.append(Q(**{f"{field}__icontains": value}))
                    elif operator == 'not_contains':
                        q_filters.append(~Q(**{f"{field}__icontains": value}))
                else:
                    if field in STRING_NUMERIC_FIELDS and operator in ('greater_than', 'less_than'):
                        python_filters.append((field, operator, value))
                    elif operator == 'equals':
                        q_filters.append(Q(**{field: value}))
                    elif operator == 'not_equals':
                        q_filters.append(~Q(**{field: value}))
                    elif operator == 'contains':
                        q_filters.append(Q(**{f"{field}__icontains": value}))
                    elif operator == 'not_contains':
                        q_filters.append(~Q(**{f"{field}__icontains": value}))
                    elif operator == 'greater_than':
                        q_filters.append(Q(**{f"{field}__gt": value}))
                    elif operator == 'less_than':
                        q_filters.append(Q(**{f"{field}__lt": value}))

        if not q_filters and not python_filters:
            return 0, []

        select_fields = list(select_fields_set)

        # 当 OR 逻辑且有 python_filters 时，全部在 Python 层统一判断
        # 避免 q_filters 先过滤导致实际变成 AND 语义
        if python_filters and logic == 'or':
            queryset = self.model.all()
            total = await queryset.count()
            objs = await queryset.order_by('id').offset((page - 1) * page_size).limit(page_size).values(*select_fields)
            filtered = []
            for obj in objs:
                results = []
                for cond in conditions:
                    field = cond.get('field', '')
                    operator = cond.get('operator', '')
                    value = cond.get('value', '')
                    if field not in SEARCHABLE_FIELDS or not operator:
                        results.append(True)
                        continue
                    obj_val = obj.get(field)
                    if operator == 'is_empty':
                        results.append(obj_val is None or obj_val == '')
                    elif operator == 'is_not_empty':
                        results.append(obj_val is not None and obj_val != '')
                    elif operator == 'equals':
                        results.append(str(obj_val or '') == str(value))
                    elif operator == 'not_equals':
                        results.append(str(obj_val or '') != str(value))
                    elif operator == 'contains':
                        results.append(str(value) in str(obj_val or ''))
                    elif operator == 'not_contains':
                        results.append(str(value) not in str(obj_val or ''))
                    elif operator == 'greater_than':
                        try:
                            results.append(float(obj_val or 0) > float(value))
                        except (ValueError, TypeError):
                            results.append(False)
                    elif operator == 'less_than':
                        try:
                            results.append(float(obj_val or 0) < float(value))
                        except (ValueError, TypeError):
                            results.append(False)
                    else:
                        results.append(True)
                if any(results):
                    filtered.append(obj)
            objs = filtered
            total = len(filtered)
        elif q_filters:
            combined_q = q_filters[0]
            for q in q_filters[1:]:
                if logic == 'or':
                    combined_q |= q
                else:
                    combined_q &= q
            queryset = self.model.filter(combined_q)
            total = await queryset.count()
            objs = await queryset.order_by('id').offset((page - 1) * page_size).limit(page_size).values(*select_fields)
            if python_filters:
                filtered = []
                for obj in objs:
                    results = []
                    for pf_field, pf_op, pf_val in python_filters:
                        try:
                            obj_val = float(obj.get(pf_field) or 0)
                            cmp_val = float(pf_val)
                        except (ValueError, TypeError):
                            results.append(False)
                            continue
                        if pf_op == 'greater_than':
                            results.append(obj_val > cmp_val)
                        elif pf_op == 'less_than':
                            results.append(obj_val < cmp_val)
                        else:
                            results.append(True)
                    if all(results):
                        filtered.append(obj)
                objs = filtered
                total = len(filtered)
        else:
            queryset = self.model.all()
            total = await queryset.count()
            objs = await queryset.order_by('id').offset((page - 1) * page_size).limit(page_size).values(*select_fields)
            if python_filters:
                filtered = []
                for obj in objs:
                    results = []
                    for pf_field, pf_op, pf_val in python_filters:
                        try:
                            obj_val = float(obj.get(pf_field) or 0)
                            cmp_val = float(pf_val)
                        except (ValueError, TypeError):
                            results.append(False)
                            continue
                        if pf_op == 'greater_than':
                            results.append(obj_val > cmp_val)
                        elif pf_op == 'less_than':
                            results.append(obj_val < cmp_val)
                        else:
                            results.append(True)
                    if logic == 'or':
                        if any(results):
                            filtered.append(obj)
                    else:
                        if all(results):
                            filtered.append(obj)
                objs = filtered
                total = len(filtered)
        return total, serialize_values(objs)

route_detail_controller = RouteDetailController()


class RouteDetailSelfDevelopedController(CRUDBase[RouteDetailSelfDeveloped, RouteDetailSelfDevelopedCreate, RouteDetailSelfDevelopedUpdate]):
    def __init__(self):
        super().__init__(model=RouteDetailSelfDeveloped)

    async def list_by_city_grouped(self, city: str, page: int = 1, page_size: int = 100):
        q = Q(city=city)
        total = await self.model.filter(q).count()
        exclude = ['created_at', 'updated_at']
        select_fields = [f for f in self.model._meta.db_fields if f not in exclude]
        rows = await self.model.filter(q).offset((page - 1) * page_size).limit(page_size).values(*select_fields)
        rows = serialize_values(rows)

        groups = {"HNOA": [], "CNOA": [], "LCC": []}
        for row in rows:
            img_val = row.pop('baidu_map_screenshot', None)
            if img_val:
                try:
                    row['image_count'] = len(json.loads(img_val)) if isinstance(img_val, str) else 0
                except (json.JSONDecodeError, TypeError):
                    row['image_count'] = 1 if img_val else 0
            else:
                row['image_count'] = 0
            rt = row.get('route_type') or "LCC"
            if rt in groups:
                groups[rt].append(row)

        result = []
        dimension_order = {'高': 1, '中': 2, '低': 3}
        for rt_key in ["HNOA", "CNOA", "LCC"]:
            if groups[rt_key]:
                groups[rt_key].sort(key=lambda x: dimension_order.get(x.get('recommend_dimension'), 4))
                result.append({"route_type": rt_key, "items": groups[rt_key]})

        return total, result

    async def get_self_developed_route_image(self, route_id: int):
        obj = await self.model.filter(id=route_id).first()
        if not obj:
            return None
        d = await obj.to_dict()
        return {'id': d.get('id'), 'baidu_map_screenshot': d.get('baidu_map_screenshot')}

    async def search_by_field(self, field: str, keyword: str = None, page: int = 1, page_size: int = 20, order: str = "desc"):
        SEARCHABLE_FIELDS = ['recommend_dimension', 'mileage', 'toll_station', 'service_area', 'ramp', 'construction_scene']
        NUMERIC_FIELDS = {'toll_station', 'service_area', 'ramp', 'construction_scene'}

        if field not in SEARCHABLE_FIELDS:
            raise ValueError(f"不支持检索的字段: {field}")

        q = Q()
        if keyword:
            if field in NUMERIC_FIELDS:
                try:
                    num_val = int(keyword)
                    q &= Q(**{field: num_val})
                except ValueError:
                    q &= Q(**{f"{field}__icontains": keyword})
            else:
                q &= Q(**{f"{field}__icontains": keyword})

        is_desc = order != 'asc'
        queryset = self.model.filter(q)
        total = await queryset.count()
        select_fields = ['id', 'route_code', 'city', 'route_type', field]
        if field in ('mileage', 'recommend_dimension'):
            all_data = await queryset.values(*select_fields)
            if field == 'mileage':
                all_data = sorted(all_data, key=lambda x: float(x.get('mileage') or 0), reverse=is_desc)
            elif field == 'recommend_dimension':
                dimension_order = {'高': 1, '中': 2, '低': 3}
                all_data = sorted(all_data, key=lambda x: dimension_order.get(x.get('recommend_dimension'), 4), reverse=not is_desc)
            data = all_data
        else:
            if is_desc:
                order_by = f"-{field}"
            else:
                order_by = "id"
            data = await queryset.order_by(order_by).values(*select_fields)
            if not is_desc and field in NUMERIC_FIELDS:
                data = sorted(data, key=lambda x: x.get(field) or 0)
        return total, serialize_values(data)

route_detail_self_developed_controller = RouteDetailSelfDevelopedController()