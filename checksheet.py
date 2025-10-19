import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# 🔐 Authenticate with Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)

# 📄 Open the sheet and tab
sheet = client.open("masaiproject").worksheet("ragscore")

# 🧪 Streamlit quiz result input
st.title("Quiz Score Logger")

name = st.text_input("Enter your name")
score = st.number_input("Enter your quiz score", min_value=0, max_value=100)
submit = st.button("Submit Score")

if submit and name:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sheet.append_row([timestamp, name, score])
    st.success(f"✅ Score submitted for {name}!")
