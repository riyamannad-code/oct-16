import streamlit as st
import bcrypt
import gspread
import pandas as pd
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
# 🔐 Credentials
# -------------------------------
teacher_credentials = {
    "teacher": {
        "name": "Riya",
        "password": "$2b$12$WW5WvcaCWW.zaZ3BRZMs0O5b4vTqhaH41cgR7eJDzmD8lV9NCYSi."  # hash of ldc12345
    }
}

student_credentials = {
    "student1": {
        "name": "Aarav",
        "password": "$2b$12$abc123..."  # replace with actual hash
    },
    "student2": {
        "name": "Meera",
        "password": "$2b$12$xyz456..."  # replace with actual hash
    }
}

# -------------------------------
# 🎭 Role Selector
# -------------------------------
st.title("RAGmasAI Learning Portal")
role = st.radio("Select your role:", ["Student", "Teacher"])

# -------------------------------
# 🧑‍🎓 Student Login & Dashboard
# -------------------------------
if role == "Student":
    st.subheader("Student Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login as Student"):
        if username in student_credentials:
            stored_hash = student_credentials[username]["password"]
            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                st.success(f"Welcome, {student_credentials[username]['name']}!")
                st.session_state["student"] = username
            else:
                st.error("Incorrect password.")
        else:
            st.error("Username not found.")

    if "student" in st.session_state:
        st.subheader("📚 Select Topic and Level")
        topic = st.selectbox("Choose a topic:", ["Artificial Intelligence", "Machine Learning", "Data Science"])
        level = st.selectbox("Choose your level:", ["Basic", "Intermediate", "Advanced"])
        if st.button("Generate Content"):
            st.markdown(f"### Learning Content: {topic} ({level})")
            st.write(f"Here’s an overview of {topic} at {level} level...")
            st.video("https://www.youtube.com/watch?v=JMUxmLyrhSk")  # example video

            if st.button("Take Quiz"):
                st.subheader("📝 Quiz")
                questions = [
                    {"q": "What is AI?", "options": ["Art Intelligence", "Artificial Intelligence", "Actual Intelligence", "None"], "a": 1},
                    {"q": "AI is used in?", "options": ["Healthcare", "Finance", "Education", "All of the above"], "a": 3},
                    {"q": "Which is an AI language?", "options": ["Python", "HTML", "CSS", "SQL"], "a": 0},
                    {"q": "AI can learn from?", "options": ["Data", "Code", "Music", "None"], "a": 0},
                    {"q": "AI stands for?", "options": ["Advanced Internet", "Artificial Intelligence", "Automated Interface", "None"], "a": 1}
                ]
                score = 0
                for i, q in enumerate(questions):
                    st.write(f"Q{i+1}: {q['q']}")
                    user_ans = st.radio(f"Answer Q{i+1}", q["options"], key=f"q{i}")
                    if user_ans == q["options"][q["a"]]:
                        score += 1
                if st.button("Submit Quiz"):
                    st.success(f"Your score: {score}/5")
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    student_name = student_credentials[st.session_state["student"]]["name"]
                    sheet.append_row([timestamp, student_name, topic, score])

        st.subheader("📊 Your Past Scores")
        records = sheet.get_all_records()
        student_name = student_credentials[st.session_state["student"]]["name"]
        student_scores = [r for r in records if r["Student Name"] == student_name]
        if student_scores:
            st.dataframe(pd.DataFrame(student_scores))
        else:
            st.info("No scores found yet.")

# -------------------------------
# 🧑‍🏫 Teacher Login & Dashboard
# -------------------------------
if role == "Teacher":
    st.subheader("Teacher Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login as Teacher"):
        if username in teacher_credentials:
            stored_hash = teacher_credentials[username]["password"]
            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
                st.success(f"Welcome, {teacher_credentials[username]['name']}!")
                st.session_state["teacher"] = username
            else:
                st.error("Incorrect password.")
        else:
            st.error("Username not found.")

    if "teacher" in st.session_state:
        st.subheader("📁 Upload Student File")
        uploaded_file = st.file_uploader("Upload CSV or Excel file")
        if uploaded_file:
            st.success("File uploaded successfully!")

        st.subheader("📊 Student Performance Dashboard")
        records = sheet.get_all_records()
        df = pd.DataFrame(records)
        st.dataframe(df)

        st.download_button(
            label="Download Full Report",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="student_scores.csv",
            mime="text/csv"
        )
