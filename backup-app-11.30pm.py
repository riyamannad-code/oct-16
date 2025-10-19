import streamlit as st
import bcrypt
import gspread
import pandas as pd
from datetime import datetime
from oauth2client.service_account import ServiceAccountCredentials
from rag_engine import (
    load_pdfs,
    create_vector_db,
    generate_with_gemini,
    build_prompt,
    export_to_pdf
)

# -------------------------------
# 🔐 Google Sheets Setup
# -------------------------------
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("service_account.json", scope)
client = gspread.authorize(creds)
topic_sheet = client.open("masaiproject").worksheet("topics")
student_sheet = client.open("student_credentials").sheet1

# -------------------------------
# 🔐 Credentials
# -------------------------------
student_data = student_sheet.get_all_records()
student_credentials = {
    row["Username"]: {
        "name": row["Name"],
        "password": row["HashedPassword"]
    }
    for row in student_data
}

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
                st.rerun()
            else:
                st.error("Incorrect password.")
        else:
            st.error("Username not found.")

    if "student" in st.session_state:
        st.subheader("📚 Topics from Teacher")

        try:
            topic_data = topic_sheet.get_all_records()
            st.session_state["topics"] = [
                str(row["Topic Title"]).strip()
                for row in topic_data
                if str(row["Topic Title"]).strip()
            ]
            #st.session_state["topics"] = [row["Topic Title"] for row in topic_data if row["Topic Title"].strip()]
        except Exception as e:
            st.session_state["topics"] = []
            st.warning(f"Could not load topics. Error: {e}")

        topics = st.session_state.get("topics", [])

        if topics:
            for topic in topics:
                st.markdown(f"- {topic}")
        else:
            st.warning("No topics available yet.")

        st.subheader("✍️ Choose or Type a Topic")
        typed_topic = st.text_input("Enter a topic you'd like to learn about", placeholder="e.g., Neural Networks")
        level = st.selectbox("Choose your level:", ["Basic", "Advanced"])

        selected_topic = typed_topic
        if st.button("Generate Content"):
            if not selected_topic:
                st.warning("Please enter a topic.")
            else:
                query = build_prompt(level, selected_topic)
                content = generate_with_gemini(query)

                st.subheader(f"{selected_topic} ({level})")
                st.write(content)

                pdf_bytes = export_to_pdf(content, filename=f"{selected_topic}_{level}.pdf")
                st.download_button("Download PDF", data=pdf_bytes, file_name=f"{selected_topic}_{level}.pdf", mime="application/pdf")

        if st.button("Puzzle"):
            st.subheader("🧩 Crossword Puzzle")

            # Sample terms and clues
            crossword_terms = {
                "token": "A single unit of text used in NLP models",
                "prompt": "Input text that guides a generative model",
                "bias": "Systematic error in model predictions",
                "embedding": "Vector representation of words or phrases",
                "fine-tune": "Adjusting a pre-trained model on new data"
            }

            user_answers = {}
            for i, (term, clue) in enumerate(crossword_terms.items(), 1):
                st.markdown(f"**{i}.** {clue} ({len(term)} letters)")
                user_input = st.text_input(f"Your answer for clue {i}:", key=f"cw_{i}")
                user_answers[term] = user_input.strip().lower()

            if st.button("Submit Crossword"):
                score = 0
                st.subheader("📝 Results")
                for i, (correct_term, clue) in enumerate(crossword_terms.items(), 1):
                    user_term = user_answers[correct_term]
                    if user_term == correct_term:
                        st.success(f"{i}. ✅ Correct: {correct_term}")
                        score += 1
                    else:
                        st.error(f"{i}. ❌ Incorrect. You wrote '{user_term}', correct was '{correct_term}'")

                st.markdown(f"### 🏆 Your Score: {score} / {len(crossword_terms)}")

# -------------------------------
# 👩‍🏫 Teacher Login & Upload
# -------------------------------
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
        st.subheader("📁 Upload PDFs to Extract Topics")
        uploaded_files = st.file_uploader("Choose PDFs", type="pdf", accept_multiple_files=True)

        if uploaded_files and st.button("Upload PDF"):
            with st.spinner("Extracting topics..."):
                text_chunks = load_pdfs(uploaded_files)
                faiss_index, topics = create_vector_db(text_chunks, level="Basic")

                if topics:
                    st.session_state["topics"] = topics
                    st.session_state["faiss_index"] = faiss_index

                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    rows_to_append = []
                    for t in topics:
                        if isinstance(t, str) and t.strip():
                            rows_to_append.append([t.strip(), "Basic", teacher_username, now])
                    print("Extracted topics:", topics)
                    if rows_to_append:
                        try:
                            topic_sheet.append_rows(rows_to_append, value_input_option="USER_ENTERED")
                            st.success("✅ Topics saved to Google Sheet!")
                        except Exception as e:
                            st.error(f"❌ Failed to save topics: {e}")
                    else:
                        st.warning("No valid topics to save.")
