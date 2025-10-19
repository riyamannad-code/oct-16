import fitz
import streamlit as st
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.embeddings import HuggingFaceEmbeddings
from fpdf import FPDF

# 🔐 Gemini setup
genai.configure(api_key=st.secrets["GOOGLE_API_KEY"])
gemini_model = genai.GenerativeModel("gemini-2.5-flash")

def generate_with_gemini(prompt):
    try:
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Error generating content: {e}"

def build_prompt(level, topic):
    if level == "Basic":
        return f"""
You are an AI tutor helping a beginner student in India understand the topic: "{topic}".

Please explain the topic in simple language, using relatable examples and analogies relevant to Indian learners.

Include:
- A short definition
- 2–3 real-world examples
- A diagram description (text only)
- A summary in bullet points

Avoid technical jargon. Keep it conversational and culturally relevant.
"""
    else:
        return f"""
You are an AI instructor preparing advanced learning material for Indian students on the topic: "{topic}".

Provide:
- A detailed explanation with technical depth
- Relevant algorithms, models, or frameworks
- Use cases in Indian industries or education
- A diagram description (text only)
- Summary in bullet points

Use precise terminology and assume the learner has prior exposure to AI concepts.
"""

def load_pdfs(uploaded_files):
    all_text = []
    for uploaded_file in uploaded_files:
        try:
            doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text()
            all_text.append(text)
            doc.close()
        except Exception as e:
            print(f"Error processing file: {e}")
    return all_text

def create_vector_db(text_chunks):
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    docs = splitter.create_documents(text_chunks)
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    return FAISS.from_documents(docs, embeddings)

from fpdf import FPDF

def export_to_pdf(text, filename="output.pdf"):
    def clean_text(s):
        return (
            s.replace("–", "-")
             .replace("—", "-")
             .replace("“", '"')
             .replace("”", '"')
             .replace("‘", "'")
             .replace("’", "'")
             .replace("•", "-")
             .encode("latin-1", "ignore")
             .decode("latin-1")
        )

    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    for line in text.split("\n"):
        pdf.multi_cell(0, 10, clean_text(line))

    pdf.output(filename)
    with open(filename, "rb") as f:
        return f.read()
