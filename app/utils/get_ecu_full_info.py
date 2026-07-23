import json
import re
from bs4 import BeautifulSoup
from typing import Dict, List, Any, Optional
from collections import defaultdict

class ECUFullInfoExtractor:
    """提取每个 ECU 的所有属性信息并序列化为 JSON"""

    def __init__(self, html_content: str):
        self.soup = BeautifulSoup(html_content, 'html.parser')
        self.ecu_data: Dict[str, Dict[str, Any]] = {}
        self.did_description_map: Dict[str, str] = {}

    def extract_all_ecu_info(self) -> Dict[str, Dict[str, Any]]:
        """
        提取所有 ECU 的所有属性信息

        Returns:
            {
                'ACU': {
                    'F187': 'H77A3607800AB',
                    'F189': 'H77A3607802AE',
                    'F089': 'H77A3607801AA',
                    'F195': 'SW_DFM_H77_BL1.00_01_20250825',
                    'F193': 'H77A16FL',
                    'F180': '',
                    'F190': 'LDP95H961SY003583',
                    'F010': 'FFCF0477073F2004'
                },
                'ARHUD': {...},
                'AMP': {...}
            }
        """
        table = self.soup.find('table')
        if not table:
            print("警告：未找到表格")
            return {}

        rows = table.find_all('tr')

        for row in rows:
            cells = row.find_all('td')
            if len(cells) < 4:
                continue

            ecu = cells[0].get_text(strip=True)
            did = cells[1].get_text(strip=True)
            description = cells[2].get_text(strip=True)
            value = cells[3].get_text(strip=True)

            # 跳过分隔行
            if ecu == '-------' or not ecu:
                continue

            # 初始化 ECU 条目
            if ecu not in self.ecu_data:
                self.ecu_data[ecu] = {}

            # 存储属性值（DID 为 key）
            cleaned_value = self._clean_value(value)
            self.ecu_data[ecu][did] = cleaned_value

            # 建立 DID 与描述的映射
            if did not in self.did_description_map:
                self.did_description_map[did] = description

        return self.ecu_data

    def _clean_value(self, value: str) -> str:
        """清理属性值，去除多余空格和换行"""
        if not value:
            return ""
        cleaned = ' '.join(value.split())
        return cleaned

    def to_json(self, indent: int = 2, ensure_ascii: bool = False) -> str:
        """
        将提取的数据序列化为 JSON 字符串，包含 _did_map
        """
        if not self.ecu_data:
            self.extract_all_ecu_info()

        output = dict(self.ecu_data)
        output['_did_map'] = dict(self.did_description_map)
        return json.dumps(output, indent=indent, ensure_ascii=ensure_ascii)

    def save_to_file(self, filepath: str, indent: int = 2):
        """保存 JSON 数据到文件"""
        json_str = self.to_json(indent=indent)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(json_str)
        print(f"数据已保存到: {filepath}")

    def get_ecu_list(self) -> List[str]:
        """获取所有 ECU 名称列表"""
        if not self.ecu_data:
            self.extract_all_ecu_info()
        return list(self.ecu_data.keys())

    def get_ecu_info(self, ecu_name: str) -> Optional[Dict[str, Any]]:
        """获取指定 ECU 的信息"""
        if not self.ecu_data:
            self.extract_all_ecu_info()
        return self.ecu_data.get(ecu_name)

    def get_did_description_map(self) -> Dict[str, str]:
        """获取 DID 与描述的映射关系"""
        if not self.did_description_map:
            self.extract_all_ecu_info()
        return dict(self.did_description_map)

    def get_version_by_type(self, version_type: str) -> Dict[str, str]:
        """
        根据版本类型获取所有 ECU 的该版本值

        Args:
            version_type: 版本类型，如 'VOYAH SoftwareVersion'

        Returns:
            {ecu_name: version_value} 的字典
        """
        if not self.ecu_data:
            self.extract_all_ecu_info()

        did = None
        for d, desc in self.did_description_map.items():
            if desc == version_type:
                did = d
                break

        if not did:
            return {}

        result = {}
        for ecu, attributes in self.ecu_data.items():
            if did in attributes:
                result[ecu] = attributes[did]

        return result

    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.ecu_data:
            self.extract_all_ecu_info()

        stats = {
            'total_ecus': len(self.ecu_data),
            'ecu_names': list(self.ecu_data.keys()),
            'did_list': list(self.did_description_map.keys()),
            'empty_values': 0,
            'total_attributes': 0
        }

        for ecu, attributes in self.ecu_data.items():
            stats['total_attributes'] += len(attributes)

            for value in attributes.values():
                if not value:
                    stats['empty_values'] += 1

        return stats


class ECUDataProcessor:
    """ECU 数据处理器，用于额外的数据处理逻辑"""

    def __init__(self, ecu_data: Dict[str, Dict[str, Any]], did_map: Optional[Dict[str, str]] = None):
        """
        初始化处理器

        Args:
            ecu_data: 从 ECUFullInfoExtractor 提取的原始数据
            did_map: DID 与描述的映射关系
        """
        self.raw_data = ecu_data
        self.did_map = did_map or {}
        self.processed_data = {}

    def filter_by_version_pattern(self, pattern: str) -> Dict[str, Dict[str, Any]]:
        """
        根据版本号模式过滤 ECU

        Args:
            pattern: 正则表达式模式，如 r'H77.*'

        Returns:
            匹配模式的 ECU 数据
        """
        result = {}

        for ecu, attributes in self.raw_data.items():
            matched = False
            for key, value in attributes.items():
                desc = self.did_map.get(key, key)
                if 'Version' in desc and re.search(pattern, value):
                    matched = True
                    break

            if matched:
                result[ecu] = attributes

        return result

    def compare_ecu_versions(self, ecu1: str, ecu2: str) -> Dict[str, Any]:
        """
        比较两个 ECU 的版本信息

        Returns:
            比较结果字典
        """
        if ecu1 not in self.raw_data or ecu2 not in self.raw_data:
            return {'error': 'ECU not found'}

        data1 = self.raw_data[ecu1]
        data2 = self.raw_data[ecu2]

        comparison = {
            'ecu1': ecu1,
            'ecu2': ecu2,
            'common_attributes': [],
            'different_attributes': [],
            'only_in_ecu1': [],
            'only_in_ecu2': []
        }

        all_keys = set(data1.keys()) | set(data2.keys())

        for key in all_keys:
            val1 = data1.get(key, 'N/A')
            val2 = data2.get(key, 'N/A')

            if key in data1 and key in data2:
                if val1 == val2:
                    comparison['common_attributes'].append({
                        'did': key,
                        'description': self.did_map.get(key, key),
                        'value': val1
                    })
                else:
                    comparison['different_attributes'].append({
                        'did': key,
                        'description': self.did_map.get(key, key),
                        'value1': val1,
                        'value2': val2
                    })
            elif key in data1:
                comparison['only_in_ecu1'].append({key: val1})
            else:
                comparison['only_in_ecu2'].append({key: val2})

        return comparison

    def export_custom_json(self, output_path: str, include_stats: bool = True):
        """
        导出自定义格式的 JSON（包含统计信息）

        Args:
            output_path: 输出文件路径
            include_stats: 是否包含统计信息
        """
        output_data = {
            'ecu_data': self.raw_data,
            '_did_map': self.did_map
        }

        if include_stats:
            stats = {
                'total_ecus': len(self.raw_data),
                'total_attributes': sum(len(attrs) for attrs in self.raw_data.values()),
                'ecu_list': list(self.raw_data.keys())
            }
            output_data['statistics'] = stats

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)

        print(f"数据已导出到: {output_path}")


def read_html_file(filepath: str) -> str:
    """读取 HTML 文件内容"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        print(f"文件未找到: {filepath}")
        return ""


def parse_ecu_file(file_content: bytes) -> Dict[str, Any]:
    """
    解析上传的ECU文件内容并返回JSON数据（包含 _did_map）

    Args:
        file_content: 上传的文件字节内容

    Returns:
        解析后的ECU数据字典，包含 _did_map
    """
    try:
        html_content = file_content.decode("utf-8")
    except UnicodeDecodeError:
        try:
            html_content = file_content.decode("gbk")
        except UnicodeDecodeError:
            return {"error": "无法解析文件编码"}

    extractor = ECUFullInfoExtractor(html_content)
    ecu_data = extractor.extract_all_ecu_info()

    if not ecu_data:
        return {"error": "未能从文件中提取到ECU数据"}

    ecu_data['_did_map'] = extractor.get_did_description_map()
    return ecu_data


def get_ecu_data_from_html(html_content: str) -> Dict[str, Dict[str, Any]]:
    """
    供外部调用的接口函数

    Args:
        html_content: HTML 内容字符串

    Returns:
        ECU 完整数据字典
    """
    extractor = ECUFullInfoExtractor(html_content)
    return extractor.extract_all_ecu_info()


def get_ecu_software_versions(html_content: str) -> Dict[str, str]:
    """
    快速获取 VOYAH SoftwareVersion

    Args:
        html_content: HTML 内容字符串

    Returns:
        {ecu_name: software_version} 字典
    """
    extractor = ECUFullInfoExtractor(html_content)
    extractor.extract_all_ecu_info()
    return extractor.get_version_by_type('VOYAH SoftwareVersion')


# 已知的描述到 DID 的映射（用于 Excel/CSV 解析时的转换）
DESCRIPTION_TO_DID = {
    "VOYAH PartVersion": "F187",
    "VOYAH SoftwareVersion": "F189",
    "VOYAH HardwareVersion": "F089",
    "Supplier SoftwareVersion": "F195",
    "Supplier HardwareVersion": "F193",
    "BootloaderVersion": "F180",
    "整车标识符(VIN)": "F190",
    "Configuration": "F010",
}

DID_TO_DESCRIPTION = {v: k for k, v in DESCRIPTION_TO_DID.items()}


def convert_description_based_to_did_based(data: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    """
    将 description-based 的数据转换为 DID-based 格式

    Args:
        data: { ecu: { description: value } }

    Returns:
        { ecu: { did: value }, _did_map: { did: description } }
    """
    result = {}
    did_map = {}

    for ecu, attrs in data.items():
        result[ecu] = {}
        for desc, value in attrs.items():
            did = DESCRIPTION_TO_DID.get(desc, desc)
            result[ecu][did] = value
            if did not in did_map:
                did_map[did] = desc

    result['_did_map'] = did_map
    return result


if __name__ == "__main__":
    html_file = 'report.html'
    html_content = read_html_file(html_file)

    if not html_content:
        print("使用内置 HTML 示例数据...")
        html_content = """
        <html>
            <body>
                <div class='htmlReport'>
                    <table border='0' cellpadding='2' cellspacing='0' width='100%'>
                        <tbody>
                            <tr><td>ACU</td><td>F187</td><td>VOYAH PartVersion</td><td>H77A3607800AB</td></tr>
                            <tr><td>ACU</td><td>F189</td><td>VOYAH SoftwareVersion</td><td>H77A3607802AE</td></tr>
                            <tr><td>ACU</td><td>F089</td><td>VOYAH HardwareVersion</td><td>H77A3607801AA</td></tr>
                            <tr><td>ARHUD</td><td>F187</td><td>VOYAH PartVersion</td><td>H77A3620809AB</td></tr>
                            <tr><td>ARHUD</td><td>F189</td><td>VOYAH SoftwareVersion</td><td>H77A3620826AH</td></tr>
                            <tr><td>AMP</td><td>F187</td><td>VOYAH PartVersion</td><td>H97N7909044BB</td></tr>
                            <tr><td>AMP</td><td>F189</td><td>VOYAH SoftwareVersion</td><td>H97N7909055AB</td></tr>
                        </tbody>
                    </table>
                </div>
            </body>
        </html>
        """

    extractor = ECUFullInfoExtractor(html_content)
    ecu_data = extractor.extract_all_ecu_info()

    print("\n" + "="*60)
    print("提取的 ECU 数据 (DID-based):")
    print("="*60)
    json_output = extractor.to_json(indent=2, ensure_ascii=False)
    print(json_output)

    extractor.save_to_file('ecu_full_info.json')

    print("\n" + "="*60)
    print("DID 描述映射:")
    print("="*60)
    print(json.dumps(extractor.get_did_description_map(), indent=2, ensure_ascii=False))

    stats = extractor.get_statistics()
    print("\n" + "="*60)
    print("统计信息:")
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    acu_info = extractor.get_ecu_info('ACU')
    print("\n" + "="*60)
    print("ACU 详细信息:")
    print(json.dumps(acu_info, indent=2, ensure_ascii=False))

    software_versions = extractor.get_version_by_type('VOYAH SoftwareVersion')
    print("\n" + "="*60)
    print("所有 ECU 的 VOYAH SoftwareVersion:")
    print(json.dumps(software_versions, indent=2, ensure_ascii=False))

    processor = ECUDataProcessor(ecu_data, extractor.get_did_description_map())

    filtered = processor.filter_by_version_pattern(r'H77.*')
    print("\n" + "="*60)
    print("版本匹配 H77* 的 ECU:")
    print(json.dumps(list(filtered.keys()), indent=2))

    if len(ecu_data) >= 2:
        ecu_names = list(ecu_data.keys())
        comparison = processor.compare_ecu_versions(ecu_names[0], ecu_names[1])
        print("\n" + "="*60)
        print(f"比较 {ecu_names[0]} 和 {ecu_names[1]}:")
        print(json.dumps(comparison, indent=2, ensure_ascii=False))

    processor.export_custom_json('ecu_processed_data.json', include_stats=True)
