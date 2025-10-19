import streamlit as st
import bcrypt
import gspread
import pandas as pd
from rag_engine import (
    load_pdfs,
    create_vector_db,
    generate_with_gemini,
    build_prompt,
    export_to_pdf
)
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# -------------------------------
# 🔐 Google Sheets Authentication
# -------------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)
sheet = client.open("masaiproject").worksheet("ragscore")

# 🔐 Load student credentials from Google Sheet
student_sheet = client.open("student_credentials").sheet1
student_data = student_sheet.get_all_records()

# Convert to dictionary format for login
student_credentials = {
    row["Username"]: {
        "name": row["Name"],
        "password": row["HashedPassword"]
    }
    for row in student_data
}


# -------------------------------
# 🔐 Credentials
# -------------------------------
teacher_credentials = {
    "teacher": {
        "name": "Riya",
        "password": "$2b$12$WW5WvcaCWW.zaZ3BRZMs0O5b4vTqhaH41cgR7eJDzmD8lV9NCYSi."  # hash of ldc12345
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
# -------------------------------
# 🔐 Login Section Based on Role
# -------------------------------

if role == "Student":
    st.subheader("Student Login")
    student_username = st.text_input("Student Username")
    student_password = st.text_input("Student Password", type="password")
    student_login = st.button("Login as Student")

    if student_login:
        if student_username in student_credentials:
            stored_hash = student_credentials[student_username]["password"]
            if bcrypt.checkpw(student_password.encode(), stored_hash.encode()):
                st.success(f"Welcome, {student_credentials[student_username]['name']}!")
                st.session_state["student"] = student_username
            else:
                st.error("Incorrect password.")
        else:
            st.error("Username not found.")


##    if st.button("Login as Student"):
##        if username in student_credentials:
##            stored_hash = student_credentials[username]["password"]
##            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
##                st.success(f"Welcome, {student_credentials[username]['name']}!")
##                st.session_state["student"] = username
##            else:
##                st.error("Incorrect password.")
##        else:
##            st.error("Username not found.")



            

    if "student" in st.session_state:
        st.subheader("📚 Select Topic and Level")
        topic = st.selectbox("Choose a topic:", ["Artificial Intelligence", "Machine Learning", "Data Science"])
        level = st.selectbox("Choose your level:", ["Basic", "Intermediate", "Advanced"])
        if st.button("Generate Content"):


            query = build_prompt(level, topic)
            content = generate_with_gemini(query)
            st.subheader(f"{topic} ({level})")
            st.write(content)
            st.write(f"Here’s an overview of {topic} at {level} level...")
            st.video("https://www.youtube.com/watch?v=JMUxmLyrhSk")  # example video

            # PDF download
            pdf_bytes = export_to_pdf(content, filename=f"{topic}_{level}.pdf")
            st.download_button("Download Content as PDF", data=pdf_bytes, file_name=f"{topic}_{level}.pdf", mime="application/pdf")
            
            #st.markdown(f"### Learning Content: {topic} ({level})")
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

##        st.subheader("📊 Your Past Scores")
##        records = sheet.get_all_records()
##        student_name = student_credentials[st.session_state["student"]]["name"]
##        student_scores = [r for r in records if r["Student Name"] == student_name]
##        if student_scores:
##            st.dataframe(pd.DataFrame(student_scores))
##        else:
##            st.info("No scores found yet.")

# -------------------------------
# 🧑‍🏫 Teacher Login & Dashboard
# -------------------------------
##if role == "Teacher":
##    st.subheader("Teacher Login")
##    username = st.text_input("Teacher Username")
##    password = st.text_input("Teacher Password", type="password")
##    if st.button("Login as Teacher"):
##        if username in teacher_credentials:
##            stored_hash = teacher_credentials[username]["password"]
##            if bcrypt.checkpw(password.encode(), stored_hash.encode()):
##                st.success(f"Welcome, {teacher_credentials[username]['name']}!")
##                st.session_state["teacher"] = username
##            else:
##                st.error("Incorrect password.")
##        else:
##            st.error("Username not found.")
elif role == "Teacher":
    st.subheader("Teacher Login")
    teacher_username = st.text_input("Teacher Username")
    teacher_password = st.text_input("Teacher Password", type="password")
    teacher_login = st.button("Login as Teacher")

    if teacher_login:
        if teacher_username in teacher_credentials:
            stored_hash = teacher_credentials[teacher_username]["password"]
            if bcrypt.checkpw(teacher_password.encode(), stored_hash.encode()):
                st.success(f"Welcome, {teacher_credentials[teacher_username]['name']}!")
                st.session_state["teacher"] = teacher_username
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
