import streamlit as st
import PyPDF2
import spacy
import json
import base64
from fpdf import FPDF
import matplotlib.pyplot as plt

# Load SpaCy model
model_name = "en_core_web_sm"
try:
    nlp = spacy.load(model_name)
except:
    st.error(f"Failed to load SpaCy model '{model_name}'. Please install it via setup.")
    st.stop()

# Load known career skills from JSON
@st.cache_data
def load_known_skills():
    with open("known_skills.json", "r") as f:
        return json.load(f)

career_skills = load_known_skills()
career_options = list(career_skills.keys())

# Extract text from uploaded PDF
def extract_text_from_pdf(pdf_file):
    reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# Skill extraction using SpaCy
def extract_skills(text):
    doc = nlp(text.lower())
    skills = set()
    for token in doc:
        if token.text in all_skills_set:
            skills.add(token.text)
    return list(skills)

# Generate downloadable PDF report
def generate_pdf_report(name, top_roles, selected_role, selected_score, matched_skills, missing_skills):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt=f"Resume Analysis Report for {name}", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "B", size=12)
    pdf.cell(200, 10, txt="Top Matching Roles:", ln=True)
    pdf.set_font("Arial", size=12)
    for role, score in top_roles:
        pdf.cell(200, 10, txt=f"{role}: {score}%", ln=True)

    pdf.ln(5)
    pdf.set_font("Arial", "B", size=12)
    pdf.cell(200, 10, txt=f"Selected Role Match - {selected_role}: {selected_score}%", ln=True)
    pdf.ln(5)

    pdf.set_font("Arial", "B", size=12)
    pdf.cell(200, 10, txt="Matched Skills:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=", ".join(matched_skills) if matched_skills else "None")

    pdf.ln(3)
    pdf.set_font("Arial", "B", size=12)
    pdf.cell(200, 10, txt="Missing Skills:", ln=True)
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, txt=", ".join(missing_skills) if missing_skills else "None")

    return pdf.output(dest="S").encode("latin-1")

# UI starts here
st.set_page_config(page_title="AI Resume–Job Matcher", layout="centered")
st.title("🤖 AI Resume–Job Matcher")
st.write("Upload your resume PDF and select your career goal to see how well your skills match!")

uploaded_resume = st.file_uploader("📄 Upload your Resume (PDF)", type=["pdf"])
career_option = st.selectbox("🎯 Choose your Career Role", career_options)

if uploaded_resume and career_option:
    resume_text = extract_text_from_pdf(uploaded_resume)
    all_skills_set = set(skill.lower() for sublist in career_skills.values() for skill in sublist)
    extracted_skills = extract_skills(resume_text)

    # Calculate match score
    match_score = 0
    matched_skills = []
    missing_skills = []

    if career_option in career_skills:
        matched_skills = list(set(extracted_skills).intersection(set(career_skills[career_option])))
        missing_skills = list(set(career_skills[career_option]).difference(set(extracted_skills)))
        if career_skills[career_option]:
            match_score = int(len(matched_skills) / len(career_skills[career_option]) * 100)

    # Sort and show match scores for all roles
    all_scores = []
    for role, skills in career_skills.items():
        role_matched = set(extracted_skills).intersection(set(skills))
        score = int(len(role_matched) / len(skills) * 100) if skills else 0
        all_scores.append((role, score))

    all_scores.sort(key=lambda x: x[1], reverse=True)
    top_roles = all_scores[:5]

    # Display results
    st.subheader("📊 Match Results")
    st.success(f"**Match Score for {career_option}: {match_score}%**")
    st.markdown(f"**Matched Skills:** {', '.join(matched_skills) if matched_skills else 'None'}")
    st.markdown(f"**Missing Skills:** {', '.join(missing_skills) if missing_skills else 'None'}")

    # Show bar chart
    st.subheader("📈 Match Scores Across All Careers")
    roles, scores = zip(*top_roles)
    fig, ax = plt.subplots()
    ax.barh(roles, scores, color='skyblue')
    ax.invert_yaxis()
    ax.set_xlabel("Match Score (%)")
    ax.set_title("Top Career Role Matches")
    st.pyplot(fig)

    # Generate PDF report
    name = uploaded_resume.name.replace(".pdf", "")
    pdf_bytes = generate_pdf_report(name, top_roles, career_option, match_score, matched_skills, missing_skills)
    b64 = base64.b64encode(pdf_bytes).decode()
    href = f'<a href="data:application/pdf;base64,{b64}" download="{name}_report.pdf">📥 Download PDF Report</a>'
    st.markdown(href, unsafe_allow_html=True)


