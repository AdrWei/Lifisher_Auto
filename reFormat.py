import os  # 导入 os 模块
import gspread
from google.oauth2.service_account import Credentials
from gspread_formatting import *

# Google Sheets API setup
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
SERVICE_ACCOUNT_FILE = 'credentials.json'  # Path to your service account JSON file

# Authenticate with Google Sheets API
creds = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
client = gspread.authorize(creds)

# Open the Google Sheet
SPREADSHEET_ID = os.getenv("SHEET_ID")
spreadsheet = client.open_by_key(SPREADSHEET_ID)

# 遍历所有工作表
for sheet in spreadsheet.worksheets():
    print(f"正在更新工作表: {sheet.title}")

    # 定义格式化规则
    cell_format = CellFormat(
        textFormat=TextFormat(
            fontSize=10,
            foregroundColor=Color(0, 0, 0)  # Black color
        )
    )

    # 应用格式化到所有行
    rows = sheet.row_count
    format_range = f"A1:{chr(64 + sheet.col_count)}{rows}"  # Full sheet range
    format_cell_range(sheet, format_range, cell_format)

    # 设置行高
    for row in range(1, rows + 1):
        set_row_height(sheet, row, 21)

print("Google Sheet 更新成功！")
