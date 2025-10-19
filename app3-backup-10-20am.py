import streamlit as st
import bcrypt
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# -------------------------------
# 🔐 Google Sheets Authentication
# -------------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)
sheet = client.open("masaiproject").worksheet("ragscore")

# -------------------------------
# 🔐 Teacher Credentials (Hashed)
# -------------------------------
hashed_passwords = [
    "$2b$12$WW5WvcaCWW.zaZ3BRZMs0O5b4vTqhaH41cgR7eJDzmD8lV9NCYSi."  # hash of "ldc12345"
]

credentials = {
    "usernames": {
        "teacher": {
            "name": "Riya",
            "password": hashed_passwords[0]
        }
    }
}

# -------------------------------
# 🧑‍🏫 Teacher Login UI
# -------------------------------
st.title("Teacher Login")

username_input = st.text_input("Username")
password_input = st.text_input("Password", type="password")
login_button = st.button("Login")

if login_button:
    if username_input in credentials["usernames"]:
        stored_hash = credentials["usernames"][username_input]["password"]
        if bcrypt.checkpw(password_input.encode(), stored_hash.encode()):
            st.success(f"Welcome, {credentials['usernames'][username_input]['name']}!")

            # -------------------------------
            # 📝 Score Submission Form
            # -------------------------------
            st.subheader("Log a Student's Quiz Score")

            student_name = st.text_input("Student Name")
            quiz_topic = st.text_input("Quiz Topic")
            score = st.number_input("Score", min_value=0, max_value=100)
            submit_score = st.button("Submit Score")

            if submit_score and student_name and quiz_topic:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sheet.append_row([timestamp, student_name, quiz_topic, score])
                st.success(f"✅ Score for {student_name} logged successfully!")
                st.rerun()

        else:
            st.error("❌ Incorrect password.")
    else:
        st.error("❌ Username not found.")
