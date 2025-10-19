import fitz
import streamlit as st
import google.generativeai as genai
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
#from langchain.embeddings import HuggingFaceEmbeddings
from langchain_community.embeddings import HuggingFaceEmbeddings
from fpdf import FPDF
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np

##from langchain.text_splitter import RecursiveCharacterTextSplitter
##from langchain_community.vectorstores import FAISS
##from langchain_community.embeddings import HuggingFaceEmbeddings
##from sklearn.cluster import KMeans
##from sklearn.feature_extraction.text import TfidfVectorizer
##import numpy as np
##import google.generativeai as genai




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




def synthesize_topics(chunks, level="Basic"):
    context = "\n\n".join(chunks[:3])  # limit to 3 chunks for prompt length

    if level == "Basic":
        prompt = f"""
You are an AI educator designing a beginner-friendly learning module for Indian students.

Here are some excerpts from a teacher-uploaded document:
{context}

Based on this, generate a clear and simple topic title that:
- Uses everyday language
- Avoids technical jargon
- Is suitable for students with no prior exposure

Keep the title short and focused.
"""
    else:
        prompt = f"""
You are an AI instructor preparing an advanced learning module for Indian students with prior exposure to AI and data science.

Here are some excerpts from a teacher-uploaded document:
{context}

Based on this, generate a precise and technically rich topic title that:
- Reflects the depth of the content
- May include frameworks, models, or domain-specific terms
- Is suitable for advanced learners

Keep the title concise but academically relevant.
"""

    try:
        response = gemini_model.generate_content(prompt)
        return response.text.strip().split("\n")[0]
    except Exception as e:
        return "Untitled Topic"





def extract_topics(chunks, level="Basic", top_n=15):
    # Example: filter and extract top N keywords or headings
    from sklearn.feature_extraction.text import TfidfVectorizer
    import numpy as np

    # Filter out short or noisy chunks
    filtered = [c for c in chunks if len(c.split()) > 5]

    # TF-IDF to extract top terms
    vectorizer = TfidfVectorizer(stop_words="english", max_features=1000)
    X = vectorizer.fit_transform(filtered)
    scores = np.asarray(X.sum(axis=0)).flatten()
    terms = vectorizer.get_feature_names_out()
    ranked = sorted(zip(terms, scores), key=lambda x: x[1], reverse=True)

    # Return top N terms as topics
    return [term.title() for term, _ in ranked[:top_n]]




def create_vector_db(chunks, level="Basic"):
    from langchain.vectorstores import FAISS
    from langchain.embeddings import HuggingFaceEmbeddings
    from langchain.schema import Document

    # Convert chunks to LangChain Documents
    docs = [Document(page_content=chunk) for chunk in chunks]

    # Create FAISS index
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    faiss_index = FAISS.from_documents(docs, embeddings)

    # Extract topics from chunks
    topics = extract_topics(chunks, level=level)

    return faiss_index, topics





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
