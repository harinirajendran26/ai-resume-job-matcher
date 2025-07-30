import streamlit as st
st.set_page_config(page_title="AI Resume–Job Matcher", layout="centered")

import PyPDF2
import spacy
import json
from io import BytesIO
from fpdf import FPDF
import matplotlib.pyplot as plt

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# Load known skills from a JSON file
with open("career_roles.json", "r") as f:
    career_skills = json.load(f)

# Flatten all known skills into a set
all_known_skills = set()
for skills in career_skills.values():
    all_known_skills.update([s.lower() for s in skills])

# Function to extract text from uploaded PDF
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

# Extract skills using NLP and keyword match
def extract_skills_from_text(text):
    doc = nlp(text)
    tokens = [token.text.lower() for token in doc if not token.is_stop and not token.is_punct]
    matched_skills = list(set(tokens) & all_known_skills)
    return matched_skills

# Generate downloadable PDF report
def generate_pdf_report(name, top_roles, selected_role, selected_score, matched_skills, missing_skills):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Resume Skill Match Report", ln=True, align='C')
    pdf.ln(10)
    pdf.cell(200, 10, txt=f"Candidate: {name}", ln=True)

    pdf.ln(5)
    pdf.cell(200, 10, txt="Top Career Matches:", ln=True)
    for role, score in top_roles:
        pdf.cell(200, 10, txt=f"{role} - {score}%", ln=True)

    pdf.ln(5)
    pdf.cell(200, 10, txt=f"Selected Career Role: {selected_role} ({selected_score}%)", ln=True)

    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Matched Skills: {', '.join(matched_skills) if matched_skills else 'None'}")
    pdf.ln(5)
    pdf.multi_cell(0, 10, txt=f"Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}")

    return pdf.output(dest='S').encode('latin1')


# Streamlit app
st.title("🧠 AI Resume–Job Matcher")
st.write("Upload your resume (PDF), select your desired career, and find your match!")

name = st.text_input("Enter your name")

uploaded_file = st.file_uploader("📄 Upload your resume (PDF)", type="pdf")

career_option = st.selectbox("🎯 Select your career goal", list(career_skills.keys()))

if uploaded_file and name and career_option:
    resume_text = extract_text_from_pdf(uploaded_file)
    extracted_skills = extract_skills_from_text(resume_text)

    scores = []
    for role, ideal_skills in career_skills.items():
        ideal_skills_lower = [s.lower() for s in ideal_skills]
        matched = set(extracted_skills) & set(ideal_skills_lower)
        score = int(len(matched) / len(set(ideal_skills_lower)) * 100) if ideal_skills else 0
        scores.append((role, score))

    # Sort by top matches
    top_roles = sorted(scores, key=lambda x: x[1], reverse=True)
    selected_score = dict(scores).get(career_option, 0)

    # Display results
    st.subheader("🎓 Top Career Matches")
    for role, score in top_roles[:5]:
        st.write(f"🔹 {role}: {score}% match")

    # Skill gap analysis
    selected_ideal_skills = set([s.lower() for s in career_skills[career_option]])
    extracted_skills_set = set(extracted_skills)
    matched_skills = list(selected_ideal_skills & extracted_skills_set)
    missing_skills = list(selected_ideal_skills - extracted_skills_set)

    st.subheader(f"🧩 Skill Match for {career_option}")
    st.write(f"✅ Matched Skills: {', '.join(matched_skills) if matched_skills else 'None'}")
    st.write(f"❌ Missing Skills: {', '.join(missing_skills) if missing_skills else 'None'}")

    # Bar chart of match scores
    st.subheader("📊 Match Score Across All Careers")
    roles = [r for r, _ in top_roles]
    scores_only = [s for _, s in top_roles]
    fig, ax = plt.subplots()
    ax.barh(roles[::-1], scores_only[::-1], color='skyblue')
    ax.set_xlabel("Match Score (%)")
    ax.set_ylabel("Career Role")
    st.pyplot(fig)

    # Generate report
    pdf_bytes = generate_pdf_report(name, top_roles[:5], career_option, selected_score, matched_skills, missing_skills)
    st.download_button(label="📥 Download PDF Report", data=pdf_bytes, file_name=f"{name}_match_report.pdf", mime="application/pdf")



