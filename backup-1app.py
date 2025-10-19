import streamlit as st
from rag_engine import (
    load_pdfs,
    create_vector_db,
    generate_with_gemini,
    build_prompt,
    export_to_pdf
)
import json
import re

import streamlit_authenticator as stauth
stauth.Hasher(["your_password"]).generate()

conn = st.connection("gsheets", type="gspread")
worksheet = conn.open("Sheet1")
worksheet.append_row([student_name, topic, level, score])

st.set_page_config(page_title="AI Learning Assistant", layout="wide")
st.title("📚 AI Learning Assistant powered by Gemini")

# 🔐 Login role selection
role = st.radio("Who are you?", ["Student", "Teacher"], horizontal=True)

# =========================
# 👩‍🏫 TEACHER FLOW
# =========================
if role == "Teacher":
    st.header("📂 Upload PDFs to Train the RAG Engine")
    uploaded_files = st.file_uploader("Upload AI-related PDFs", type="pdf", accept_multiple_files=True)
    if uploaded_files:
        with st.spinner("🔍 Indexing content..."):
            texts = load_pdfs(uploaded_files)
            vector_db = create_vector_db(texts)
        st.success("✅ Files processed and indexed successfully!")

# =========================
# 👩‍🎓 STUDENT FLOW
# =========================
elif role == "Student":
    st.header("🎓 Welcome, Student!")
    student_name = st.text_input("Enter your name to begin:")

    if student_name:
        level = st.selectbox("Choose your learning level:", ["Basic", "Advanced"])

        topics = {
            "Basic": [
                "What is AI?",
                "Applications of AI",
                "Advantages and Disadvantages",
                "Ethics in AI"
            ],
            "Advanced": [
                "Machine Learning",
                "Deep Learning",
                "Generative AI",
                "Prompt Engineering",
                "Responsible AI"
            ]
        }[level]

        topic = st.selectbox("Choose a topic to learn:", topics)

        if st.button("Generate Learning Content"):
            query = build_prompt(level, topic)
            content = generate_with_gemini(query)
            st.subheader(f"{topic} ({level})")
            st.write(content)

            # PDF download
            pdf_bytes = export_to_pdf(content, filename=f"{topic}_{level}.pdf")
            st.download_button("Download Content as PDF", data=pdf_bytes, file_name=f"{topic}_{level}.pdf", mime="application/pdf")

            # Ask if student wants quiz
            take_quiz = st.radio("Would you like to take a quiz on this topic?", ["Yes", "No"], horizontal=True)

            if take_quiz == "Yes":
                st.session_state["quiz_ready"] = True
                st.session_state["level"] = level
                st.session_state["topic"] = topic
                st.session_state["content"] = content
                st.session_state["student_name"] = student_name
                st.experimental_rerun()

# =========================
# 🧠 QUIZ PAGE
# =========================
if st.session_state.get("quiz_ready"):
    st.header("📝 Self-Assessment Quiz")
    level = st.session_state["level"]
    topic = st.session_state["topic"]
    content = st.session_state["content"]
    student_name = st.session_state["student_name"]

    quiz_prompt = f"""
Generate 5 multiple-choice questions for a {level} learner on the topic "{topic}" based on the following content:

{content}

Return only a valid JSON array like this:
[
  {{
    "question": "What is AI?",
    "options": ["A. Artificial Intelligence", "B. Animal Instinct", "C. Automated Input", "D. Analog Interface"],
    "answer": "A"
  }},
  ...
]
"""
    with st.spinner("Generating quiz..."):
        quiz_raw = generate_with_gemini(quiz_prompt)

    try:
        match = re.search(r"\[\s*{.*}\s*]", quiz_raw, re.DOTALL)
        quiz_data = json.loads(match.group()) if match else []
        score = 0
        responses = {}

        for i, q in enumerate(quiz_data):
            st.markdown(f"**Q{i+1}: {q['question']}**")
            user_answer = st.radio(f"Your answer for Q{i+1}", q["options"], key=f"q{i}")
            correct = q["answer"]
            if user_answer.startswith(correct):
                score += 1
            responses[f"Q{i+1}"] = {
                "question": q["question"],
                "your_answer": user_answer,
                "correct_answer": correct
            }

        st.markdown(f"### ✅ {student_name}, your score: {score}/5")

        # 🎯 Adaptive feedback
        if level == "Basic" and score >= 4:
            st.success("Great job! You're ready to take on the Advanced level.")
        elif level == "Advanced" and score <= 2:
            st.warning("Consider revisiting the topic before moving forward.")

        st.markdown("#### Your Performance Summary")
        st.json(responses)

        # Reset quiz state
        if st.button("Finish"):
            st.session_state["quiz_ready"] = False
            st.experimental_rerun()

    except Exception as e:
        st.error(f"Could not parse quiz: {e}")
        st.code(quiz_raw, language="json")
