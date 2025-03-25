import os
import warnings
import json
import random
import requests
import time
from requests.exceptions import RequestException

warnings.filterwarnings("ignore")

try:
    # 环境变量
    lifisher_codes = os.getenv("LIFISHER_CODES")
    lifisher_token = os.getenv("LIFISHER_TOKEN")
    lifisher_variables = os.getenv("LIFISHER_VARIABLES")
    lifisher_staff_codes = os.getenv("LIFISHER_STAFF_CODES")

    # 解析 JSON
    codes = json.loads(lifisher_codes)
    constants = json.loads(lifisher_variables)
    AGENTS = json.loads(lifisher_staff_codes)

    # 提取 JSON 中的值
    USERNAME = codes["USERNAME"]
    PASSWORD = codes["PASSWORD"]
    APPKEY = codes["APPKEY"]

    # 重命名 TOKEN
    TOKEN = lifisher_token
    
    # 常量定义
    LOGIN_URL = constants["LOGIN_URL"]
    INQUIRY_LIST_URL = constants["INQUIRY_LIST_URL"]
    ASSIGN_URL = constants["ASSIGN_URL"]
    DOMAIN = constants["DOMAIN"]
    REFERER = constants["REFERER"]
    SITE_ID = constants["SITE_ID"]

except Exception as e:
    print(f"初始化失败: {str(e)}")
    exit(1)

# 发送 GET 请求登录
login_response = requests.get(
    LOGIN_URL,
    params={"username": USERNAME, "password": PASSWORD},
    headers={"User-Agent": "Mozilla/5.0"},
    verify=False  # 忽略 SSL 验证
)

# 检查登录是否成功
if login_response.status_code == 200:
    print("登录成功！")
    
    # 提取 cookies
    cookies_dict = login_response.cookies.get_dict()
    cookies_header = "; ".join([f"{k}={v}" for k, v in cookies_dict.items()])
else:
    raise Exception("登录失败！")


# 请求参数
inquiry_list_params = {
    "return_source": 1,
    "is_junk": 0,
    "site_id": 5735,
    "page_size": 200,
    "page_number": 1,
    "status": 0,
    "sort": "create_time desc"
}

# 请求头
inquiry_list_headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "appkey": APPKEY,
    "token": TOKEN,
    "domain": DOMAIN,
    "Referer": REFERER,
    "timestamp": str(int(time.time() * 1000)),
    "X-Trace-Id": "bb898ceed2b5f5e4"
}

# 发送 GET 请求
inquiry_list_response = requests.get(
    INQUIRY_LIST_URL,
    headers=inquiry_list_headers,
    params=inquiry_list_params,
    verify=False  # 忽略 SSL 验证
)

# 检查获取询盘列表是否成功
if inquiry_list_response.status_code == 200:
    print("获取询盘列表成功！")
    
    # 解析询盘列表
    inquiry_list_data = inquiry_list_response.json()
    inquiry_list = inquiry_list_data.get("data", {}).get("list", [])
    
    # 检查是否有询盘数据
    if not inquiry_list:
        print("筛选后的询盘列表为空。")
    else:
        # 提取询盘 ID
        inquiry_ids = [item["id"] for item in inquiry_list]
        print(f"筛选后的询盘列表包含 {len(inquiry_ids)} 个询盘。")
else:
    print(f"获取询盘列表失败，状态码：{inquiry_list_response.status_code}")

# 3. 开始询盘分配
try:
    # 请求头（使用与获取询盘列表相同的请求头）
    assign_headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "appkey": APPKEY,
        "token": TOKEN,
        "domain": DOMAIN,
        "Referer": REFERER,
        "timestamp": str(int(time.time() * 1000)),
        "X-Trace-Id": "bb898ceed2b5f5e4"
    }

    # 将询盘列表平均分配给两个业务员
    for inquiry_id in inquiry_ids:
        # 随机选择一个业务员
        assign_to = random.choice(AGENTS)

        # 请求体
        body = {
            "id": str(inquiry_id),
            "client_account_id": str(assign_to),
            "site_id": str(SITE_ID)
        }

        # 发送 POST 请求
        assign_response = requests.post(
            ASSIGN_URL,
            headers=assign_headers,
            json=body,
            cookies=cookies_dict,
            verify=False
        )
        assign_response.raise_for_status()  # 检查请求是否成功

    print("询盘分配完成。")

except RequestException as e:
    print(f"询盘分配失败: {str(e)}")
    exit(1)
