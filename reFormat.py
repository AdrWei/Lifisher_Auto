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
SPREADSHEET_ID = 'your-spreadsheet-id'  # Replace with your Google Sheet ID
sheet = client.open_by_key(SPREADSHEET_ID).sheet1  # Update to the specific sheet if needed

# Define the formatting rules
cell_format = CellFormat(
    textFormat=TextFormat(
        fontSize=10,
        foregroundColor=Color(0, 0, 0)  # Black color
    )
)

# Apply formatting to all rows
rows = sheet.row_count
format_range = f"A1:{chr(64 + sheet.col_count)}{rows}"  # Full sheet range
format_cell_range(sheet, format_range, cell_format)

# Set row height
for row in range(1, rows + 1):
    set_row_height(sheet, row, 21)

print("Google Sheet updated successfully!")
