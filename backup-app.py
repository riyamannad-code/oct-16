import streamlit as st
from rag_engine import load_pdfs, create_vector_db, generate_with_gemini
from rag_engine import generate_with_gemini
import json
    
import re
#response = generate_with_gemini(query)
# Page setup
st.set_page_config(page_title="AI Learning Assistant", layout="wide")
st.title("📚 AI Learning Assistant powered by Gemini")

# PDF upload
uploaded_files = st.file_uploader("Upload AI-related PDFs", type="pdf", accept_multiple_files=True)

if uploaded_files:
    with st.spinner("🔍 Extracting and indexing content..."):
        texts = load_pdfs(uploaded_files)
        vector_db = create_vector_db(texts)

    # Learning level selection
    level = st.selectbox("Select your learning level:", ["Basic", "Advanced"])

    # Topic selection based on level
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

    # Generate content
    if st.button("Generate Learning Content"):
        query = f"Generate educational content for a {level} learner on the topic: {topic}. Include explanations, examples, and diagrams."
        with st.spinner("🧠 Generating content using Gemini..."):
            content = generate_with_gemini(query)
            st.subheader(f"{topic} ({level})")
            st.write(content)

        # Generate quiz
        quiz_prompt = f"""
        Generate 3 multiple-choice questions based on the following content:

        {content}

        Return the output as a valid JSON array with this format:

    [
  {{
    "question": "What is AI?",
    "options": ["A. Artificial Intelligence", "B. Animal Instinct", "C. Automated Input", "D. Analog Interface"],
    "answer": "A"
  }},
  ...
]
Only return the JSON array. Do not include any explanation or extra text.
"""


        with st.spinner("📝 Creating quiz..."):
            quiz = generate_with_gemini(quiz_prompt)
            st.subheader("Self-Assessment Quiz")
            st.code(quiz, language="json")
            

       

        st.subheader("📝 Self-Assessment Quiz")

        try:
            # Extract JSON array using regex in case Gemini adds extra text
            match = re.search(r"\[\s*{.*}\s*]", quiz, re.DOTALL)
            if match:
                quiz_data = json.loads(match.group())
                for i, q in enumerate(quiz_data):
                    st.markdown(f"**Q{i+1}: {q['question']}**")
                    for opt in q["options"]:
                        st.markdown(f"- {opt}")
                    st.markdown(f"✅ **Answer:** {q['answer']}")
                    st.markdown("---")
            else:
                raise ValueError("No JSON array found in response.")
        except Exception as e:
            st.error(f"Could not parse quiz: {e}")
            st.code(quiz, language="json")



            
        # Optional download
        st.download_button("Download Content as PDF", content.encode("utf-8"), file_name=f"{topic}_{level}.pdf")
