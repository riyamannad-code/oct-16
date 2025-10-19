import streamlit as st
import bcrypt
import gspread
import pandas as pd
from datetime import datetime
import re
import json
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
cluster_sheet = client.open("masaiproject").worksheet("clustered_topics")
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
#-------------


if "student" in st.session_state:
    # ✅ Initialize session state keys if missing
    for key in ["quiz_questions", "quiz_attempts", "show_quiz"]:
        if key not in st.session_state:
            st.session_state[key] = None if key == "quiz_questions" else []
    
    # Helper to sanitize filenames
    def sanitize_filename(name):
        return re.sub(r'[\\/*?:"<>|()\n\r]', "", name).strip()[:50]

    # Load subtopics from Google Sheets
    try:
        topic_sheet = client.open("masaiproject").worksheet("clustered_topics")
        subtopic_df = pd.DataFrame(topic_sheet.get_all_records())
        subtopic_list = sorted(subtopic_df["Subtopic"].dropna().unique())
    except Exception as e:
        st.error(f"❌ Failed to load subtopics: {e}")
        subtopic_list = []


    # UI: Subtopic and level selection
    selected_subtopic = st.selectbox("Choose a subtopic", subtopic_list)
    level = st.radio("Select level", ["Basic", "Advanced"])

    # Button row
    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        generate_clicked = st.button("Generate Content", key="generate_btn")

    with col2:
        download_ready = "generated_pdf" in st.session_state
        if download_ready:
            st.download_button(
                "Download PDF",
                data=st.session_state["generated_pdf"],
                file_name=st.session_state["generated_filename"],
                mime="application/pdf",
                key="download_btn"
            )
        else:
            st.markdown("⬇️ PDF will appear here after generation")

    with col3:
        quiz_enabled = "generated_content" in st.session_state
        quiz_clicked = st.button("Take Quiz", key="quiz_btn", disabled=not quiz_enabled)

        if quiz_clicked:
            st.session_state["quiz_triggered"] = True
    
            
    def parse_quiz_from_text(raw_text):
            questions = []
            blocks = re.split(r"\n(?=\d+\.\s)", raw_text.strip())  # Split by numbered questions

            for block in blocks:
                lines = block.strip().split("\n")
                if len(lines) < 3:
                    continue

                # Extract question
                q_match = re.match(r"\d+\.\s*(.*)", lines[0])
                question = q_match.group(1).strip() if q_match else lines[0].strip()

                # Extract options
                options = []
                for line in lines[1:]:
                    opt_match = re.match(r"[A-Da-d][\).:-]?\s*(.+)", line.strip())
                    if opt_match:
                        options.append(opt_match.group(1).strip())

                # Extract answer
                answer_line = next((l for l in lines if "answer" in l.lower()), "")
                ans_match = re.search(r"answer\s*[:\-]?\s*([A-Da-d])", answer_line, re.IGNORECASE)
                if ans_match:
                    answer_letter = ans_match.group(1).upper()
                    answer_index = ord(answer_letter) - ord("A")
                else:
                    answer_index = 0  # fallback to first option

                if question and len(options) >= 2:
                    questions.append({
                        "question": question,
                        "options": options,
                        "answer": answer_index
                    })

            return questions
    
    def build_quiz_prompt(topic, level):

        return f"""
        Create a 5-question multiple-choice quiz for Indian students on the topic '{topic}' at a {level.lower()} level.

        Format each question like this:
        1. Question text
        A) Option A
        B) Option B
        C) Option C
        D) Option D
        Answer: B

        Make sure:
        - Each question has exactly 4 options labeled A to D.
        - The correct answer is clearly marked as 'Answer: X' (e.g., Answer: C).
        - The correct answer should appear in a **random position** among the options — do NOT always place it in the same slot.
        - Do NOT return JSON, markdown, or any explanation — only plain text.
        """


##        return f"""
##        Create a 5-question multiple-choice quiz for students on the topic '{topic}' at a {level.lower()} level.
##        Format each question like this:
##        1. Question text
##        A) Option A
##        B) Option B
##        C) Option C
##        D) Option D
##        Answer: B
##
##        Return only plain text. No JSON, no explanation.
##        """
##    
    #content generation
    if generate_clicked:
        query = build_prompt(level, selected_subtopic)
        content = generate_with_gemini(query)
        st.session_state["generated_content"] = content

        st.subheader(f"{selected_subtopic} ({level})")
        st.write(content)

        # Export PDF
        safe_name = sanitize_filename(selected_subtopic)
        filename = f"{safe_name}_{level}.pdf"
        pdf_bytes = export_to_pdf(content, filename=filename)
        st.session_state["generated_pdf"] = pdf_bytes
        st.session_state["generated_filename"] = filename

        # ✅ Auto-generate quiz based on topic and level
        quiz_prompt = build_quiz_prompt(selected_subtopic, level)
        quiz_raw = generate_with_gemini(quiz_prompt)
        #st.text_area("📄 Gemini Raw Quiz Output", quiz_raw, height=300)

           
        #if not parsed_quiz:
        parsed_quiz = parse_quiz_from_text(quiz_raw)

        if parsed_quiz:
            st.session_state["quiz_questions"] = parsed_quiz
            st.session_state["quiz_attempts"] = []
            st.session_state["show_quiz"] = True
        else:
            st.error("❌ Could not parse quiz. Please check Gemini output.")
            st.text_area("📄 Gemini Raw Quiz Output", str(quiz_raw), height=300)


    if st.session_state.get("show_quiz") and st.session_state.get("quiz_questions"):
        st.subheader("📝 Quiz Time!")
        user_answers = []
        for i, q in enumerate(st.session_state["quiz_questions"]):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            selected = st.radio(
                label="Choose your answer:",
                options=q["options"],
                key=f"quiz_q{i}"
            )
            user_answers.append(selected)

        if st.button("Submit Quiz", key="submit_btn"):
            score = 0
            results = []
            for i, q in enumerate(st.session_state["quiz_questions"]):
                correct = q["options"][q["answer"]]
                user_ans = user_answers[i]
                is_correct = user_ans == correct
                results.append((i+1, user_ans, correct, is_correct))
                if is_correct:
                    score += 1
            st.session_state["quiz_attempts"].append(score)
            st.session_state["show_quiz"] = False
            st.session_state["last_score"] = score
            st.session_state["last_results"] = results


            st.subheader("📊 Results")
            for q_num, user_ans, correct_ans, is_correct in results:
                if is_correct:
                    st.success(f"Q{q_num}: ✅ Correct")
                else:
                    st.error(f"Q{q_num}: ❌ Incorrect — You chose '{user_ans}', correct answer is '{correct_ans}'")

            st.markdown(f"### 🏆 Your Score: {score} / {len(st.session_state['quiz_questions'])}")


    # Log to Google Sheets
            try:
                score_sheet = client.open("masaiproject").worksheet("quiz_scores")
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                score_row = [
                    st.session_state["student"],
                    selected_subtopic,
                    level,
                    st.session_state["last_score"],
                    now
                ]
                score_sheet.append_row(score_row, value_input_option="USER_ENTERED")
                st.success("✅ Your score has been logged!")
            except Exception as e:
                st.error(f"❌ Failed to log score: {e}")

            # Show attempt history
            if len(st.session_state["quiz_attempts"]) > 1:
                st.subheader("📈 Attempt History")
                scores_df = pd.DataFrame({
                    "Attempt": list(range(1, len(st.session_state["quiz_attempts"]) + 1)),
                    "Score": st.session_state["quiz_attempts"]
                })
                st.line_chart(scores_df.set_index("Attempt"))

##



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
        st.subheader("📁 Upload PDFs to Extract and Cluster Topics")
        uploaded_files = st.file_uploader("Choose PDFs", type="pdf", accept_multiple_files=True)

        if uploaded_files and st.button("Upload PDF"):
            with st.spinner("Extracting and clustering topics..."):
                text_chunks = load_pdfs(uploaded_files)
                faiss_index, named_clusters = create_vector_db(text_chunks, level="Basic")

                if named_clusters:
                    st.session_state["faiss_index"] = faiss_index
                    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    rows = []
                    for theme, subtopics in named_clusters.items():
                        for topic in subtopics:
                            rows.append([theme, topic, "Basic", teacher_username, now])

                    try:
                        cluster_sheet.append_rows(rows, value_input_option="USER_ENTERED")
                        st.success("✅ Clustered topics saved to Google Sheet!")
                    except Exception as e:
                        st.error(f"❌ Failed to save clustered topics: {e}")
                else:
                    st.warning("No valid topics to save.")



    if "show_dashboard" not in st.session_state:
        st.session_state["show_dashboard"] = False

    if st.button("📊 Dashboard", key="dashboard_btn"):
        st.session_state["show_dashboard"] = True

    if st.session_state["show_dashboard"]:
        try:
            score_sheet = client.open("masaiproject").worksheet("quiz_scores")
            score_data = score_sheet.get_all_records()
            score_df = pd.DataFrame(score_data)

            if score_df.empty:
                st.warning("No quiz scores found.")
            else:
                st.subheader("📈 Student Performance Dashboard")

                # Show full table
                st.dataframe(score_df)
                score_df = pd.DataFrame(score_sheet.get_all_records())
                score_df.columns = [col.strip().lower() for col in score_df.columns]

                # Average score per student
                avg_scores = score_df.groupby("student")["Score"].mean().reset_index()
                st.markdown("### 🧮 Average Scores by Student")
                st.dataframe(avg_scores)

                # Attempt count per student
                attempt_counts = score_df.groupby("student")["Score"].count().reset_index(name="Attempts")
                st.markdown("### 📉 Attempt Trends")
                st.bar_chart(attempt_counts.set_index("Student"))

        except Exception as e:
            st.error(f"❌ Failed to load dashboard: {e}")


