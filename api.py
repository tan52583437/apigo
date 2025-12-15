import csv
import os
import json
from collections import defaultdict
from flask import Flask, request, Response
from flask_cors import CORS

# 创建Flask应用实例
app = Flask(__name__)
# 启用CORS支持
CORS(app)

# 设置JSON编码配置，确保中文正常显示
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_MIMETYPE'] = 'application/json; charset=utf-8'

# 设置API版本
API_VERSION = "v1"

# 默认数据源根目录
DEFAULT_SOURCE_ROOT = r"C:\Users\Administrator\Desktop\api-p\apifile"


def read_csv_data(csv_path):
    seg_data = defaultdict(list)
    encodings = ["utf-8-sig", "GBK"]
    for encoding in encodings:
        try:
            with open(csv_path, "r", encoding=encoding, errors="ignore") as f:
                reader = csv.DictReader(f)
                seg_cols = [col for col in reader.fieldnames if " 号段" in col]
                if not seg_cols:
                    return None
                for row in reader:
                    for col in seg_cols:
                        seg7 = row[col].strip()
                        if seg7 and len(seg7) == 7 and seg7.isdigit():
                            three_seg = col.replace(" 号段", "").strip()
                            if seg7 not in seg_data[three_seg]:
                                seg_data[three_seg].append(seg7)
            return seg_data if seg_data else None
        except Exception:
            continue
    return None


def get_mobile_segment_data(source_root):
    """
    读取手机号段数据的核心API函数
    :param source_root: 数据源根目录路径
    :return: 标准化结果字典
        - success: 布尔值，是否成功获取数据
        - message: 字符串，结果描述信息
        - data: 字典，结构化号段数据 {城市: {运营商: {三位号段: [七位数据列表]}}}
        - fail_files: 列表，读取失败的文件路径（相对路径）
        - statistics: 字典，统计信息 {cities: 城市数量, groups: 城市+运营商组数, buttons: 号段按钮数}
    """
    # 校验目录是否存在
    if not os.path.exists(source_root):
        return {
            "success": False,
            "message": f"Source directory does not exist: {source_root}",
            "data": None,
            "fail_files": [],
            "statistics": {"cities": 0, "groups": 0, "buttons": 0}
        }

    # 初始化数据容器
    city_data = defaultdict(dict)
    city_folders = [f for f in os.listdir(source_root) if os.path.isdir(os.path.join(source_root, f))]

    # 校验是否有城市文件夹
    if not city_folders:
        return {
            "success": False,
            "message": "No city folders found",
            "data": None,
            "fail_files": [],
            "statistics": {"cities": 0, "groups": 0, "buttons": 0}
        }

    # 统计变量
    total_groups = 0
    total_buttons = 0
    fail_files = []

    # 遍历城市和CSV文件
    for city in sorted(city_folders):
        city_dir = os.path.join(source_root, city)
        for filename in os.listdir(city_dir):
            if "_修改后.csv" in filename and "号段数据" in filename:
                operator = filename.replace("号段数据_修改后.csv", "").strip()
                csv_path = os.path.join(city_dir, filename)
                seg_data = read_csv_data(csv_path)
                
                if seg_data:
                    city_data[city][operator] = seg_data
                    total_groups += 1
                    total_buttons += len(seg_data)
                else:
                    fail_files.append(f"{city}/{filename}")

    # 校验是否有有效数据
    if not city_data:
        return {
            "success": False,
            "message": "No valid data found",
            "data": None,
            "fail_files": fail_files,
            "statistics": {"cities": 0, "groups": 0, "buttons": 0}
        }

    # 转换defaultdict为普通字典（便于序列化）
    result_data = {}
    for city, operators in city_data.items():
        result_data[city] = {}
        for operator, segs in operators.items():
            result_data[city][operator] = {seg: segs_list for seg, segs_list in segs.items()}

    # 返回成功结果
    return {
        "success": True,
        "message": "Data retrieved successfully",
        "data": result_data,
        "fail_files": fail_files,
        "statistics": {
            "cities": len(city_folders),
            "groups": total_groups,
            "buttons": total_buttons
        }
    }


# ---------------------- API路由 ----------------------

@app.route(f"/api/{API_VERSION}/mobile-segments", methods=["GET"])
def api_get_mobile_segments():
    """
    获取手机号段数据的API接口
    
    查询参数:
    - source_root: 可选，数据源根目录路径，默认使用DEFAULT_SOURCE_ROOT
    
    返回:
    JSON格式的响应数据，与get_mobile_segment_data函数返回格式一致
    """
    # 获取请求参数
    source_root = request.args.get("source_root", DEFAULT_SOURCE_ROOT)
    
    # 调用核心函数获取数据
    result = get_mobile_segment_data(source_root)
    
    # 手动序列化JSON，确保中文正常显示
    json_data = json.dumps(result, ensure_ascii=False, indent=2)
    
    # 返回响应，设置正确的Content-Type
    return Response(
        json_data,
        content_type='application/json; charset=utf-8'
    )


@app.route(f"/api/{API_VERSION}/mobile-segments/query", methods=["GET"])
def api_query_mobile():
    """
    查询单个手机号的归属地和运营商信息
    
    查询参数:
    - mobile: 必填，要查询的手机号（11位数字）
    - source_root: 可选，数据源根目录路径，默认使用DEFAULT_SOURCE_ROOT
    
    返回:
    JSON格式的响应数据，包含手机号的归属信息
    """
    # 获取请求参数
    mobile = request.args.get("mobile")
    source_root = request.args.get("source_root", DEFAULT_SOURCE_ROOT)
    
    # 验证手机号格式
    if not mobile or len(mobile) != 11 or not mobile.isdigit():
        response_data = {
            "success": False,
            "message": "Invalid mobile number format. Must be 11 digits.",
            "data": None
        }
    else:
        # 提取号段信息
        three_seg = mobile[:3]  # 前三位号段
        seven_seg = mobile[:7]   # 前七位号段
        
        # 获取所有号段数据
        result = get_mobile_segment_data(source_root)
        
        if not result["success"]:
            response_data = {
                "success": False,
                "message": result["message"],
                "data": None
            }
        else:
            # 查找匹配的号段信息
            found = False
            city = ""
            operator = ""
            
            # 遍历所有城市和运营商数据
            for c, operators in result["data"].items():
                for op, segs in operators.items():
                    if three_seg in segs and seven_seg in segs[three_seg]:
                        city = c
                        operator = op
                        found = True
                        break
                if found:
                    break
            
            if found:
                response_data = {
                    "success": True,
                    "message": "Mobile number information found.",
                    "data": {
                        "mobile": mobile,
                        "city": city,
                        "operator": operator,
                        "three_segment": three_seg,
                        "seven_segment": seven_seg
                    }
                }
            else:
                response_data = {
                    "success": False,
                    "message": "Mobile number information not found in the database.",
                    "data": None
                }
    
    # 手动序列化JSON，确保中文正常显示
    json_data = json.dumps(response_data, ensure_ascii=False, indent=2)
    
    # 返回响应，设置正确的Content-Type
    return Response(
        json_data,
        content_type='application/json; charset=utf-8'
    )


# ---------------------- 应用启动 ----------------------
if __name__ == "__main__":
    # 启动Flask应用
    app.run(
        host="0.0.0.0",  # 允许所有网络接口访问
        port=5000,       # 默认端口
        debug=True       # 开发模式
    )