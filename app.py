import streamlit as st
import pandas as pd
import spacy
import subprocess
import importlib.util
import PyPDF2
import io
import matplotlib.pyplot as plt
from fpdf import FPDF

# 1. 🧠 Ensure spaCy model is available
model_name = "en_core_web_sm"
if importlib.util.find_spec(model_name) is None:
    subprocess.run(["python", "-m", "spacy", "download", model_name])
nlp = spacy.load(model_name)

# 2. 📂 Ideal skills for career roles
import json

with open("career_roles.json", "r") as f:
    career_skills = json.load(f)


# 3. 📄 Resume PDF to text
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    resume_text = ""
    for page in pdf_reader.pages:
        resume_text += page.extract_text()
    return resume_text

# 4. 🧠 Extract skills using spaCy
def extract_skills(text):
    doc = nlp(text.lower())
    return list(set([token.text for token in doc if token.pos_ in ["NOUN", "PROPN"]]))

# 5. 🧾 Generate PDF report
def generate_pdf_report(name, top_roles, selected_career, selected_score, matched, missing):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Resume Match Report for {name}", ln=True)

    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"\nSelected Career Role: {selected_career}", ln=True)
    pdf.cell(0, 10, f"Match Score: {selected_score}%", ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "\nTop 3 Career Matches:", ln=True)
    pdf.set_font("Arial", "", 12)
    for role, score in top_roles:
        pdf.cell(0, 10, f"{role}: {score}%", ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "\nMatched Skills:", ln=True)
    pdf.set_font("Arial", "", 12)
    for skill in matched:
        pdf.cell(0, 10, f"- {skill}", ln=True)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "\nMissing Skills:", ln=True)
    pdf.set_font("Arial", "", 12)
    for skill in missing:
        pdf.cell(0, 10, f"- {skill}", ln=True)

    return pdf.output(dest="S").encode("latin1", "replace")

# 6. 🚀 Streamlit UI
st.set_page_config(page_title="AI Resume–Career Matcher", layout="centered")

st.title("💼 AI Resume–Career Matcher")
st.markdown("Upload your **resume (PDF)** and choose a career path to see how well you match!")

pdf_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
career_option = st.selectbox("Choose your desired career role", list(career_skills.keys()))

if pdf_file and career_option:
    resume_text = extract_text_from_pdf(pdf_file)
    extracted_skills = extract_skills(resume_text)

    st.subheader("🔍 Extracted Skills from Resume")
    st.write(", ".join(extracted_skills) if extracted_skills else "No skills detected.")

    # 🎯 Match logic
    scores = {}
    for role, skills in career_skills.items():
        matched = set(extracted_skills).intersection(skills)
        score = int((len(matched) / len(skills)) * 100)
        scores[role] = score

    # 📊 Results
    selected_score = scores[career_option]
    matched_skills = list(set(extracted_skills).intersection(career_skills[career_option]))
    missing_skills = list(career_skills[career_option].difference(extracted_skills))

    st.subheader("✅ Match Results")
    st.write(f"**{career_option}** Match Score: **{selected_score}%**")
    st.write(f"**Matched Skills:** {', '.join(matched_skills) if matched_skills else 'None'}")
    st.write(f"**Missing Skills:** {', '.join(missing_skills) if missing_skills else 'None'}")

    # 📉 Bar chart
    st.subheader("📈 Match Score Comparison Across Careers")
    score_df = pd.DataFrame(list(scores.items()), columns=["Career Role", "Match Score"])
    st.bar_chart(score_df.set_index("Career Role"))

    # 🧾 PDF Report Download
    name = pdf_file.name.replace(".pdf", "")
    top_3 = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    pdf_bytes = generate_pdf_report(name, top_3, career_option, selected_score, matched_skills, missing_skills)

    st.download_button(
        label="📥 Download Match Report (PDF)",
        data=pdf_bytes,
        file_name=f"{name}_resume_match_report.pdf",
        mime="application/pdf"
    )
