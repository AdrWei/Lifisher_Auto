import os
import json
import time
import requests
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from requests.exceptions import RequestException

# 自定义函数：移除空列或空行
def remove_empty(df, which="cols"):
    if which == "cols":
        df = df.dropna(axis=1, how="all")  # 移除空列
    elif which == "rows":
        df = df.dropna(axis=0, how="all")  # 移除空行
    return df

# 从 Google Sheets 提取数据
def fetch_sheet_data(sheet_id, sheet_name, columns_to_extract):
    # 获取 Google Sheets 客户端
    credentials = Credentials.from_service_account_file("credentials.json")
    client = build("sheets", "v4", credentials=credentials)
    
    # 获取表格数据
    sheet = client.spreadsheets().values().get(spreadsheetId=sheet_id, range=sheet_name).execute()
    data = sheet.get("values", [])  # 获取所有数据
    
    # 转换为 DataFrame
    df = pd.DataFrame(data[1:], columns=data[0])  # 第一行为列名，其余为数据
    return df[columns_to_extract]  # 提取指定列

try:
    # 环境变量
    lifisher_codes = os.getenv("LIFISHER_CODES")
    lifisher_token = os.getenv("LIFISHER_TOKEN")
    lifisher_variables = os.getenv("LIFISHER_VARIABLES")
    mySHEET_ID = os.getenv("SHEET_ID")
    lifisherSHEET_ID = os.getenv("LIFISHER_SHEET_ID")

    # 解析 JSON
    codes = json.loads(lifisher_codes)
    constants = json.loads(lifisher_variables)

    # 提取 JSON 中的值
    USERNAME = codes["USERNAME"]
    PASSWORD = codes["PASSWORD"]
    APPKEY = codes["APPKEY"]

    # 重组 TOKEN
    TOKEN = lifisher_token
    
    # 常量定义
    LOGIN_URL = constants["LOGIN_URL"]
    DOMAIN = constants["DOMAIN"]
    REFERER = constants["REFERER"]
    SITE_ID = constants["SITE_ID"]
    BASE_URL = constants["BASE_URL"]

except Exception as e:
    raise ValueError(f"初始化失败: {str(e)}")

# 请求头配置
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "appkey": APPKEY,
    "token": TOKEN,
    "domain": DOMAIN,
    "Referer": REFERER,
    "timestamp": str(int(time.time() * 1000))
}

# 登录逻辑
try:
    # 发送登录请求（GET 方法）
    login_response = requests.get(
        LOGIN_URL,
        params={"username": USERNAME, "password": PASSWORD},
        headers={"User-Agent": "Mozilla/5.0"},
        verify=False  # 忽略 SSL 验证
    )
    login_response.raise_for_status()  # 检查请求是否成功

    # 提取 Cookies 并转换为字典
    cookies_dict = {cookie.name: cookie.value for cookie in login_response.cookies}

    # 验证 Cookies 格式
    print("Cookies 字典：", cookies_dict)

    # 使用 Cookies 访问受保护页面
    protected_page_url = "https://admin.lifisher.com/home/index"
    protected_page_response = requests.get(
        protected_page_url,
        cookies=cookies_dict,  # 传递 Cookies 字典
        headers={"User-Agent": "Mozilla/5.0"},
        verify=False  # 忽略 SSL 验证
    )
except Exception as e:
    print(f"登录失败: {str(e)}")
    exit(1)

# 分页获取所有数据
PAGE_SIZE = 200
MAX_PAGES = 100  # 安全阈值，防止无限循环
all_data = pd.DataFrame()
page = 1
has_more = True

# 分页获取所有数据
while has_more and page <= MAX_PAGES:
    params = {
        "is_junk": 0,
        "site_id": SITE_ID,
        "page_number": page,
        "page_size": PAGE_SIZE
    }
    try:
        response = requests.get(
            BASE_URL,
            headers=HEADERS,
            params=params,
            cookies=cookies_dict,
            verify=False
        )
        response.raise_for_status()  # 检查请求是否成功
        res_data = response.json()

        # 检查是否有数据
        if "data" in res_data and len(res_data["data"]) > 0:
            current_page_data = pd.DataFrame(res_data["data"])
            all_data = pd.concat([all_data, current_page_data], ignore_index=True)
            print(f"成功获取第 {page} 页，累计 {len(all_data)} 条记录")
            page += 1
        else:
            has_more = False
            print(f"第 {page} 页无数据，终止分页")
    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        print(f"响应内容: {response.text}")
        break

    time.sleep(0.5)  # 控制请求频率

# 移除空列或空行
all_data = remove_empty(all_data, which="cols")

# 按 create_time 列排序
all_data["create_time"] = pd.to_datetime(all_data["create_time"], format="%Y-%m-%d %H:%M:%S")
all_data_sorted = all_data.sort_values(by="create_time", ascending=False)  # 降序排序

# 筛选 source 为 4、7 或 20 的行
filtered_data = all_data_sorted[all_data_sorted["source"].isin([4, 7, 20])]

# 筛选指定列
columns_to_extract = ["opearing_system", "access_device", "screen", "brower", "first_visitor_url", "page_url"]
filtered_data = filtered_data[columns_to_extract]

# 从 Google Sheets 提取数据
sheet_id = mySHEET_ID  # 替换为你的 Google Sheet ID
sheet_name = "orderWeb"  # 替换为你的 sheet 名称
columns_to_extract_sheet = ["询盘时间", "联系人", "国家", "客户分类", "跟进进程", "跟进情况"]  # 替换为你的列名
extracted_data = fetch_sheet_data(sheet_id, sheet_name, columns_to_extract_sheet)
extracted_data_social = fetch_sheet_data(sheet_id, "orderSocial", columns_to_extract_sheet)

# 水平合并两个表格
merged_df = pd.concat([extracted_data.reset_index(drop=True), filtered_data.reset_index(drop=True)], axis=1)

try:
    # 检查 credentials.json 是否存在
    if not os.path.exists("credentials.json"):
        raise FileNotFoundError("credentials.json 文件不存在")

    # 认证 Google Sheets API
    creds = Credentials.from_service_account_file(
        "credentials.json",
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
    )
    client = gspread.authorize(creds)

    # 打开目标 Google Sheet
    target_spreadsheet_id = lifisherSHEET_ID  # 替换为你的目标 Google Sheet ID
    target_sheet = client.open_by_key(target_spreadsheet_id).worksheet("orderWeb")  # 假设使用第一个工作表

    # 写入 merged_df 到 orderWeb 表
    target_sheet_web = target_spreadsheet.worksheet("orderWeb")  # 打开 orderWeb 表
    target_sheet_web.clear()  # 清空现有数据
    target_sheet_web.append_row(merged_df.columns.tolist())  # 写入表头
    data_to_write_web = merged_df.values.tolist()  # 转换为二维列表

    # 分批写入数据到 orderWeb
    batch_size = 50  # 每批写入 50 行
    for i in range(0, len(data_to_write_web), batch_size):
        batch = data_to_write_web[i:i + batch_size]
        target_sheet_web.append_rows(batch)  # 使用 append_rows 批量写入
        print(f"成功写入 {len(batch)} 行数据到 orderWeb")
        time.sleep(10)  # 每批写入后等待 10 秒，避免超限

    # 写入 extracted_data_social 到 orderSocial 表
    target_sheet_social = target_spreadsheet.worksheet("orderSocial")  # 打开 orderSocial 表
    target_sheet_social.clear()  # 清空现有数据
    target_sheet_social.append_row(extracted_data_social.columns.tolist())  # 写入表头
    data_to_write_social = extracted_data_social.values.tolist()  # 转换为二维列表

    # 分批写入数据到 orderSocial
    for i in range(0, len(data_to_write_social), batch_size):
        batch = data_to_write_social[i:i + batch_size]
        target_sheet_social.append_rows(batch)  # 使用 append_rows 批量写入
        print(f"成功写入 {len(batch)} 行数据到 orderSocial")
        time.sleep(10)  # 每批写入后等待 10 秒，避免超限

    print("数据成功写入 Google Sheet！")

except Exception as e:
    print(f"写入 Google Sheet 失败: {str(e)}")
