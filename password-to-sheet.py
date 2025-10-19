import gspread
import csv
from oauth2client.service_account import ServiceAccountCredentials

# Authenticate
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# Open the target sheet
sheet = client.open("student_credentials").sheet1

# Clear existing content (optional)
sheet.clear()

# Read CSV and upload
with open("student_credentials.csv", "r") as file:
    reader = csv.reader(file)
    data = list(reader)
    sheet.update("A1", data)

print("✅ Uploaded student credentials to Google Sheet.")
