import streamlit as st
import fitz  # PyMuPDF
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF
import base64
import unicodedata

import spacy
import subprocess
import importlib.util

# Check if the model is installed, if not download it
model_name = "en_core_web_sm"
if importlib.util.find_spec(model_name) is None:
    subprocess.run(["python", "-m", "spacy", "download", model_name])

nlp = spacy.load(model_name)


# --------------------------
# Ideal Skills Dictionary
# --------------------------
career_skills = {
    "Data Scientist": {"python", "machine learning", "statistics", "data analysis", "pandas", "numpy", "sql", "deep learning"},
    "Backend Developer": {"java", "python", "api", "databases", "sql", "node.js", "django", "spring"},
    "Frontend Developer": {"html", "css", "javascript", "react", "angular", "ui", "ux", "web design"},
    "Business Analyst": {"excel", "sql", "power bi", "data visualization", "stakeholder", "requirement", "analysis"},
    "Project Manager": {"scrum", "agile", "planning", "budgeting", "risk management", "team management"},
    "DevOps Engineer": {"docker", "kubernetes", "ci/cd", "jenkins", "cloud", "aws", "terraform", "linux"},
    "UI/UX Designer": {"figma", "adobe xd", "wireframe", "user research", "prototyping", "design thinking"},
    "Digital Marketer": {"seo", "sem", "social media", "content", "analytics", "email marketing"},
    "HR Manager": {"recruitment", "onboarding", "payroll", "employee engagement", "compliance", "training"},
    "Content Writer": {"writing", "editing", "proofreading", "seo", "blog", "creative writing", "grammar"}
}

# --------------------------
# Helper Functions
# --------------------------
def extract_text_from_pdf(pdf_file):
    text = ""
    with fitz.open(stream=pdf_file.read(), filetype="pdf") as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_skills_from_text(text):
    doc = nlp(text.lower())
    tokens = {token.text for token in doc if not token.is_stop and not token.is_punct}
    return tokens

def sanitize_text(text):
    return unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")

def generate_pdf_report(name, top_roles, selected_role, match_score, matched_skills, missing_skills):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(200, 10, sanitize_text("AI Resume–Job Match Report"), ln=True, align='C')

    pdf.set_font("Arial", "", 12)
    pdf.ln(10)
    pdf.cell(200, 10, sanitize_text(f"Candidate Name: {name}"), ln=True)
    
    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, sanitize_text("Top 3 Career Suggestions:"), ln=True)
    pdf.set_font("Arial", "", 12)
    for i, (role, score) in enumerate(top_roles, 1):
        pdf.cell(200, 10, sanitize_text(f"{i}. {role} — {score}%"), ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, sanitize_text(f"Selected Career: {selected_role} — {match_score}%"), ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, sanitize_text(f"Skills You Have ({len(matched_skills)}):"), ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, sanitize_text(", ".join(matched_skills) or "None"))

    pdf.set_font("Arial", "B", 12)
    pdf.cell(200, 10, sanitize_text(f"Skills You're Missing ({len(missing_skills)}):"), ln=True)
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, sanitize_text(", ".join(missing_skills) or "None"))

    return pdf.output(dest='S').encode('latin1')

# --------------------------
# Streamlit App
# --------------------------
st.set_page_config(page_title="AI Resume–Job Matcher", layout="centered")
st.title("🧠 AI Resume–Job Matcher")
st.markdown("Upload your resume and get matched to ideal careers or real job descriptions.")

uploaded_file = st.file_uploader("📄 Upload your Resume (PDF only)", type=["pdf"])

if uploaded_file:
    resume_text = extract_text_from_pdf(uploaded_file)
    extracted_resume_skills = extract_skills_from_text(resume_text)

    # ----------------------
    # Built-in Career Match
    # ----------------------
    st.markdown("---")
    st.markdown("### 🔮 Top 3 Career Suggestions")
    scores = {}
    for role, required_skills in career_skills.items():
        matched = extracted_resume_skills & required_skills
        score = int((len(matched) / len(required_skills)) * 100) if required_skills else 0
        scores[role] = score

    top_roles = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:3]
    for i, (role, score) in enumerate(top_roles, start=1):
        st.markdown(f"**{i}. {role}** — {score}% match")

    # ----------------------
    # Career Role Picker
    # ----------------------
    st.markdown("---")
    selected_career = st.selectbox("📌 Choose a career role to view detailed comparison", list(career_skills.keys()))

    matched_skills = extracted_resume_skills & career_skills[selected_career]
    missing_skills = career_skills[selected_career] - extracted_resume_skills
    selected_score = int((len(matched_skills) / len(career_skills[selected_career])) * 100) if career_skills[selected_career] else 0

    st.markdown(f"### 🎯 Match Score for **{selected_career}**: `{selected_score}%`")
    st.markdown(f"✅ **Skills You Have ({len(matched_skills)}):**")
    st.write(', '.join(matched_skills) if matched_skills else "None")
    st.markdown(f"❌ **Skills Missing ({len(missing_skills)}):**")
    st.write(', '.join(missing_skills) if missing_skills else "None")

    # ----------------------
    # Career Match Chart
    # ----------------------
    st.markdown("---")
    st.markdown("### 📊 Match Score Across All Careers")
    fig, ax = plt.subplots()
    ax.bar(scores.keys(), scores.values(), color="skyblue")
    plt.xticks(rotation=45, ha='right')
    plt.ylabel("Match Score (%)")
    plt.tight_layout()
    st.pyplot(fig)

    # ----------------------
    # Job Description Upload
    # ----------------------
    st.markdown("---")
    st.subheader("📄 Upload a Job Description or Paste Below")
    job_text = None
    uploaded_jd = st.file_uploader("📎 Upload Job Description (PDF/TXT)", type=["pdf", "txt"])

    if uploaded_jd is not None:
        if uploaded_jd.type == "application/pdf":
            job_text = extract_text_from_pdf(uploaded_jd)
        else:
            job_text = uploaded_jd.read().decode('utf-8')

    if not uploaded_jd:
        job_text = st.text_area("Or paste the job description here:")

    # ----------------------
    # Resume to JD Comparison
    # ----------------------
    if job_text:
        st.markdown("### 🤝 Resume vs Job Description")
        jd_skills = extract_skills_from_text(job_text)
        resume_matched = extracted_resume_skills & jd_skills
        resume_missing = jd_skills - extracted_resume_skills
        resume_score = int((len(resume_matched) / len(jd_skills)) * 100) if jd_skills else 0

        st.markdown(f"**💼 Match Score: `{resume_score}%`**")
        st.markdown(f"✅ **Skills You Have ({len(resume_matched)}):**")
        st.write(', '.join(resume_matched) if resume_matched else "None")
        st.markdown(f"❌ **Skills Missing ({len(resume_missing)}):**")
        st.write(', '.join(resume_missing) if resume_missing else "None")

    # ----------------------
    # PDF Report Download
    # ----------------------
    st.markdown("---")
    st.subheader("📥 Download Career Match Report")
    name = st.text_input("Enter your name for the report:")
    if name and st.button("Generate PDF Report"):
        pdf_bytes = generate_pdf_report(name, top_roles, selected_career, selected_score, matched_skills, missing_skills)
        b64_pdf = base64.b64encode(pdf_bytes).decode('utf-8')
        href = f'<a href="data:application/octet-stream;base64,{b64_pdf}" download="{name}_Career_Match_Report.pdf">📄 Click here to download your report</a>'
        st.markdown(href, unsafe_allow_html=True)

else:
    st.info("👆 Please upload your resume to begin.")

