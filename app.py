import streamlit as st
st.set_page_config(page_title="AI Resume Intelligence Platform", layout="wide", page_icon="🧠")

import PyPDF2
import json
import numpy as np
from fpdf import FPDF
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import pandas as pd
from collections import Counter
import anthropic

# ─────────────────────────────────────────────
# Load career skills data
# ─────────────────────────────────────────────
with open("career_roles.json", "r") as f:
    career_skills = json.load(f)

# ─────────────────────────────────────────────
# PDF extraction
# ─────────────────────────────────────────────
def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"
    return text.strip()

# ─────────────────────────────────────────────
# Semantic skill extraction via Claude
# ─────────────────────────────────────────────
def extract_skills_with_claude(resume_text, client):
    all_skills = set()
    for skills in career_skills.values():
        all_skills.update([s.lower() for s in skills])

    prompt = f"""You are a resume parser. Extract skills from this resume text that match or are semantically similar to these known skills:

Known skills: {', '.join(sorted(all_skills))}

Resume text:
{resume_text[:3000]}

Return ONLY a JSON array of matched skill strings (lowercase), using the exact known skill names where there is a semantic match.
Example: ["python", "machine learning", "sql"]
Return [] if nothing matches. No explanation, just the JSON array."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = message.content[0].text.strip()
    try:
        skills = json.loads(raw)
        return [s.lower() for s in skills if isinstance(s, str)]
    except Exception:
        text_lower = resume_text.lower()
        return [s for s in all_skills if s in text_lower]

# ─────────────────────────────────────────────
# Keyword fallback extraction
# ─────────────────────────────────────────────
def extract_skills_keyword(resume_text):
    all_skills = set()
    for skills in career_skills.values():
        all_skills.update([s.lower() for s in skills])
    return [s for s in all_skills if s in resume_text.lower()]

# ─────────────────────────────────────────────
# Score all roles
# ─────────────────────────────────────────────
def score_all_roles(extracted_skills):
    results = {}
    for role, ideal_skills in career_skills.items():
        ideal_lower = [s.lower() for s in ideal_skills]
        matched = list(set(extracted_skills) & set(ideal_lower))
        missing = list(set(ideal_lower) - set(extracted_skills))
        score = int(len(matched) / len(set(ideal_lower)) * 100) if ideal_lower else 0
        results[role] = {
            "score": score,
            "matched": matched,
            "missing": missing,
            "total_required": len(set(ideal_lower))
        }
    return dict(sorted(results.items(), key=lambda x: x[1]["score"], reverse=True))

# ─────────────────────────────────────────────
# AI roadmap via Claude (streaming)
# ─────────────────────────────────────────────
def generate_roadmap(role, matched_skills, missing_skills, candidate_name, client):
    prompt = f"""You are a senior career coach. Create a detailed, actionable 90-day learning roadmap.

Candidate: {candidate_name}
Target role: {role}
Skills they already have: {', '.join(matched_skills) if matched_skills else 'None identified'}
Skills they need to learn: {', '.join(missing_skills) if missing_skills else 'None - they are ready!'}

Generate a structured roadmap with:
1. **30-day milestone** - Foundations (specific free resources, what to build)
2. **60-day milestone** - Applied projects (portfolio project idea, tools to use)
3. **90-day milestone** - Job-ready (interview prep, GitHub/LinkedIn tips)

Also include:
- 3 specific project ideas that signal this role to recruiters
- Top 3 free courses (with platform names like Coursera, YouTube, fast.ai, etc.)
- One certification recommendation if relevant
- Resume bullet point template they can fill in

Keep it specific, practical, and motivating. Format with clear headers and bullet points."""

    with client.messages.stream(
        model="claude-opus-4-5",
        max_tokens=1200,
        messages=[{"role": "user", "content": prompt}]
    ) as stream:
        for text in stream.text_stream:
            yield text

# ─────────────────────────────────────────────
# Cross-role insight via Claude
# ─────────────────────────────────────────────
def generate_comparison_insight(scores_dict, extracted_skills, client):
    prompt = f"""Career advisor analysis. A candidate has these skill match scores:

{chr(10).join([f"- {role}: {data['score']}% ({len(data['matched'])} of {data['total_required']} skills)" for role, data in scores_dict.items()])}

Their detected skills: {', '.join(extracted_skills) if extracted_skills else 'None detected'}

In 3-4 sentences give an insightful analysis covering: what their skill profile reveals, smartest pivot with least upskilling, transferable skills, and one honest recommendation. Be direct and specific. No bullet points - flowing prose only."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=300,
        messages=[{"role": "user", "content": prompt}]
    )
    return message.content[0].text.strip()

# ─────────────────────────────────────────────
# PDF report
# ─────────────────────────────────────────────
def generate_pdf_report(name, target_role, score, matched, missing, scores_dict, roadmap_text=""):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(20, 20, 20)

    pdf.set_fill_color(15, 15, 15)
    pdf.rect(0, 0, 210, 42, "F")
    pdf.set_font("Arial", "B", 18)
    pdf.set_text_color(255, 255, 255)
    pdf.set_y(12)
    pdf.cell(0, 10, "Resume Intelligence Report", ln=True, align="C")
    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Candidate: {name}", ln=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(10)

    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 8, f"Target Role: {target_role}", ln=True)
    color = (34, 139, 34) if score >= 60 else (255, 140, 0) if score >= 35 else (200, 50, 50)
    pdf.set_text_color(*color)
    pdf.set_font("Arial", "B", 28)
    pdf.cell(0, 14, f"{score}% Match", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Matched Skills:", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(34, 139, 34)
    pdf.multi_cell(0, 7, ", ".join(matched) if matched else "None detected")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Skills to Develop:", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.set_text_color(180, 50, 50)
    pdf.multi_cell(0, 7, ", ".join(missing) if missing else "None - you are fully ready!")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Match Scores - All Roles", ln=True)
    pdf.ln(2)
    pdf.set_font("Arial", "B", 11)
    pdf.set_fill_color(230, 230, 230)
    pdf.cell(120, 8, "Role", border=1, fill=True)
    pdf.cell(60, 8, "Match Score", border=1, fill=True, ln=True)
    pdf.set_font("Arial", "", 11)
    for role_name, data in scores_dict.items():
        pdf.cell(120, 7, role_name, border=1)
        pdf.cell(60, 7, f"{data['score']}%", border=1, ln=True)

    if roadmap_text:
        pdf.add_page()
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Your 90-Day Learning Roadmap", ln=True)
        pdf.ln(2)
        pdf.set_font("Arial", "", 10)
        clean = roadmap_text.replace("**", "").replace("*", "").replace("#", "")
        pdf.multi_cell(0, 6, clean[:3500])

    return pdf.output(dest="S").encode("latin1")

# ─────────────────────────────────────────────
# Visualisations
# ─────────────────────────────────────────────
def plot_match_bars(scores_dict):
    roles = list(scores_dict.keys())
    scores_vals = [v["score"] for v in scores_dict.values()]
    colors = ["#22C55E" if s >= 60 else "#F59E0B" if s >= 35 else "#EF4444" for s in scores_vals]
    fig, ax = plt.subplots(figsize=(9, max(4, len(roles) * 0.6)))
    fig.patch.set_facecolor("#0F0F0F")
    ax.set_facecolor("#0F0F0F")
    bars = ax.barh(roles[::-1], scores_vals[::-1], color=colors[::-1], height=0.6)
    ax.set_xlabel("Match Score (%)", color="#CCCCCC", fontsize=11)
    ax.set_xlim(0, 110)
    ax.tick_params(colors="#CCCCCC", labelsize=10)
    for spine in ax.spines.values():
        spine.set_color("#333333")
    for bar, s in zip(bars, scores_vals[::-1]):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{s}%", va="center", ha="left", color="white", fontsize=10, fontweight="bold")
    legend_patches = [
        mpatches.Patch(color="#22C55E", label="Strong (60%+)"),
        mpatches.Patch(color="#F59E0B", label="Moderate (35-59%)"),
        mpatches.Patch(color="#EF4444", label="Gap (< 35%)"),
    ]
    ax.legend(handles=legend_patches, loc="lower right", facecolor="#1A1A1A", labelcolor="white", fontsize=9)
    plt.title("Career Match Scores", color="white", fontsize=13, pad=12)
    plt.tight_layout()
    return fig

def plot_skill_radar(role, matched, missing):
    all_skills = matched + missing
    if len(all_skills) < 3:
        return None
    N = len(all_skills)
    values = [1 if s in matched else 0 for s in all_skills] + [1 if all_skills[0] in matched else 0]
    angles = [n / float(N) * 2 * np.pi for n in range(N)] + [0]
    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    fig.patch.set_facecolor("#0F0F0F")
    ax.set_facecolor("#111111")
    ax.plot(angles, values, "o-", linewidth=2, color="#22C55E")
    ax.fill(angles, values, alpha=0.25, color="#22C55E")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(all_skills, size=8, color="white")
    ax.set_yticks([])
    ax.spines["polar"].set_color("#333333")
    ax.grid(color="#333333")
    plt.title(f"Skill Coverage: {role}", color="white", fontsize=11, pad=15)
    return fig

# ─────────────────────────────────────────────
# Custom CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
.stApp { background-color: #0A0A0A; color: #E5E5E5; }
h1 { font-size: 2.2rem !important; font-weight: 700 !important; }
.metric-card {
    background: #161616; border: 1px solid #2A2A2A;
    border-radius: 12px; padding: 1.2rem 1.5rem; text-align: center;
}
.metric-value { font-size: 2.4rem; font-weight: 700; }
.metric-label { font-size: 0.8rem; color: #888; margin-top: 4px; text-transform: uppercase; letter-spacing: 0.05em; }
.skill-match { display:inline-block; background:#14532D; color:#86EFAC; border-radius:20px; padding:4px 12px; font-size:0.82rem; margin:3px; border:1px solid #166534; }
.skill-miss { display:inline-block; background:#450A0A; color:#FCA5A5; border-radius:20px; padding:4px 12px; font-size:0.82rem; margin:3px; border:1px solid #7F1D1D; }
.info-box { background:#111827; border:1px solid #1E3A5F; border-left:4px solid #3B82F6; border-radius:8px; padding:1rem 1.25rem; color:#BFDBFE; font-size:0.92rem; line-height:1.7; }
.stButton > button { background:#FFFFFF; color:#000000; border-radius:8px; font-weight:600; padding:0.6rem 2rem; border:none; font-size:0.95rem; width:100%; }
.stButton > button:hover { background:#E5E5E5; }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# App header
# ─────────────────────────────────────────────
col_h1, col_h2 = st.columns([3, 1])
with col_h1:
    st.markdown("# 🧠 Resume Intelligence Platform")
    st.markdown("##### AI-powered career matching · Skill gap analysis · Personalised 90-day roadmap")
with col_h2:
    api_key = st.text_input("Anthropic API Key", type="password", placeholder="sk-ant-...")

st.divider()

# Sidebar
with st.sidebar:
    st.markdown("## 📋 Your profile")
    candidate_name = st.text_input("Your name", placeholder="e.g. Harini Rajendran")
    uploaded_file = st.file_uploader("Upload resume (PDF)", type="pdf")
    resume_text_input = st.text_area("Or paste resume text", height=180,
        placeholder="Paste your resume content here...")
    target_role = st.selectbox("Target career role", [""] + list(career_skills.keys()))
    analyze_btn = st.button("🔍 Analyze My Resume", use_container_width=True)
    st.divider()
    st.caption("Fill your profile and click Analyze. Add an Anthropic API key for semantic AI matching and roadmap generation.")

# Session state
for key in ["results", "roadmap", "extracted_skills"]:
    if key not in st.session_state:
        st.session_state[key] = None if key == "results" else ([] if key == "extracted_skills" else "")

# ─────────────────────────────────────────────
# Run analysis
# ─────────────────────────────────────────────
if analyze_btn:
    if not candidate_name or not target_role or (not uploaded_file and not resume_text_input.strip()):
        st.error("Please fill in your name, select a role, and provide resume content.")
    else:
        resume_text = ""
        if uploaded_file:
            resume_text = extract_text_from_pdf(uploaded_file)
        if resume_text_input.strip():
            resume_text += "\n" + resume_text_input.strip()

        with st.spinner("Analyzing your resume..."):
            try:
                if api_key:
                    client = anthropic.Anthropic(api_key=api_key)
                    extracted = extract_skills_with_claude(resume_text, client)
                else:
                    extracted = extract_skills_keyword(resume_text)
                    st.info("Add an Anthropic API key for semantic skill matching and AI roadmap generation.")

                scores = score_all_roles(extracted)
                st.session_state.results = {
                    "scores": scores, "target_role": target_role,
                    "name": candidate_name, "resume_text": resume_text,
                }
                st.session_state.extracted_skills = extracted
                st.session_state.roadmap = ""
            except Exception as e:
                st.error(f"Analysis error: {e}")

# ─────────────────────────────────────────────
# Show results
# ─────────────────────────────────────────────
if st.session_state.results:
    res = st.session_state.results
    scores = res["scores"]
    role = res["target_role"]
    name = res["name"]
    extracted = st.session_state.extracted_skills
    matched = scores[role]["matched"]
    missing = scores[role]["missing"]
    score = scores[role]["score"]

    tab1, tab2, tab3, tab4 = st.tabs(["📊 Match Analysis", "🗺️ Career Roadmap", "🔄 Role Comparison", "📥 Export"])

    with tab1:
        c1, c2, c3, c4 = st.columns(4)
        sc = "#22C55E" if score >= 60 else "#F59E0B" if score >= 35 else "#EF4444"
        with c1:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:{sc}">{score}%</div><div class="metric-label">Match score</div></div>', unsafe_allow_html=True)
        with c2:
            st.markdown(f'<div class="metric-card"><div class="metric-value">{len(extracted)}</div><div class="metric-label">Skills detected</div></div>', unsafe_allow_html=True)
        with c3:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#22C55E">{len(matched)}</div><div class="metric-label">Matched</div></div>', unsafe_allow_html=True)
        with c4:
            st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#EF4444">{len(missing)}</div><div class="metric-label">Skill gaps</div></div>', unsafe_allow_html=True)

        st.markdown("---")
        col_l, col_r = st.columns([1.3, 1])

        with col_l:
            st.markdown("### ✅ Matched skills")
            if matched:
                st.markdown(" ".join([f'<span class="skill-match">{s}</span>' for s in matched]), unsafe_allow_html=True)
            else:
                st.caption("No matches found — try pasting more resume content.")

            st.markdown("### ❌ Skills to develop")
            if missing:
                st.markdown(" ".join([f'<span class="skill-miss">{s}</span>' for s in missing]), unsafe_allow_html=True)
            else:
                st.success("All key skills present — you are ready to apply!")

            st.markdown("### 📈 All roles")
            st.pyplot(plot_match_bars(scores), use_container_width=True)

        with col_r:
            st.markdown("### 🕸️ Skill radar")
            fig_r = plot_skill_radar(role, matched, missing)
            if fig_r:
                st.pyplot(fig_r, use_container_width=True)
            else:
                st.caption("Add more resume content for radar chart.")

            if api_key:
                st.markdown("### 🤖 AI insight")
                with st.spinner("Generating..."):
                    try:
                        client = anthropic.Anthropic(api_key=api_key)
                        insight = generate_comparison_insight(scores, extracted, client)
                        st.markdown(f'<div class="info-box">{insight}</div>', unsafe_allow_html=True)
                    except Exception:
                        pass

    with tab2:
        st.markdown(f"### 🗺️ 90-Day Roadmap to become a {role}")
        if missing:
            st.markdown("Focus skills: " + " ".join([f'<span class="skill-miss">{s}</span>' for s in missing[:6]]), unsafe_allow_html=True)
        else:
            st.success("You already have all core skills! Your roadmap will focus on depth and portfolio.")

        if not api_key:
            st.warning("Add your Anthropic API key to generate a personalised AI roadmap.")
        else:
            if st.button("✨ Generate my AI roadmap"):
                st.session_state.roadmap = ""
                client = anthropic.Anthropic(api_key=api_key)
                placeholder = st.empty()
                full_text = ""
                for chunk in generate_roadmap(role, matched, missing, name, client):
                    full_text += chunk
                    placeholder.markdown(full_text)
                st.session_state.roadmap = full_text

        if st.session_state.roadmap:
            st.divider()
            st.markdown(st.session_state.roadmap)

    with tab3:
        st.markdown("### 🔄 Cross-role comparison")
        sorted_roles = list(scores.items())
        best_role, best_data = sorted_roles[0]
        if best_role != role:
            st.info(f"Your best fit is **{best_role}** at {best_data['score']}% — higher than your target {role} ({score}%).")

        rows = []
        for r, data in scores.items():
            readiness = "🟢 Ready" if data["score"] >= 60 else "🟡 Close" if data["score"] >= 35 else "🔴 Gap"
            rows.append({"Role": r, "Score": f"{data['score']}%", "Matched": len(data["matched"]),
                         "Gaps": len(data["missing"]), "Readiness": readiness})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

        st.markdown("### 🔗 Transferable skills (in 3+ roles)")
        skill_count = Counter()
        for data in scores.values():
            for s in data["matched"]:
                skill_count[s] += 1
        transferable = [s for s, c in skill_count.items() if c >= 3]
        if transferable:
            st.markdown(" ".join([f'<span class="skill-match">{s}</span>' for s in transferable]), unsafe_allow_html=True)
        else:
            st.caption("Build more skills to unlock transferable advantages.")

    with tab4:
        st.markdown("### 📥 Download your report")
        pdf_bytes = generate_pdf_report(name, role, score, matched, missing, scores, st.session_state.roadmap)
        st.download_button("📥 Download PDF Report", data=pdf_bytes,
            file_name=f"{name.replace(' ', '_')}_report.pdf", mime="application/pdf", use_container_width=True)

        st.divider()
        st.markdown("### 📋 Resume bullet (copy this into your resume)")
        bullet = f"Built an AI-powered career intelligence platform using Claude (Anthropic) API for semantic skill extraction, match scoring across {len(career_skills)} career roles, and streaming AI-generated 90-day learning roadmaps. Deployed on Streamlit Cloud with radar chart visualisations and PDF export."
        st.code(bullet, language=None)

else:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("**🔍 Semantic AI matching**\n\nClaude reads your resume like a recruiter — 'data analysis' matches 'analyzing datasets'.")
    with col2:
        st.markdown("**📊 Multi-role scoring**\n\nSee your match score across all careers with transferable skill detection.")
    with col3:
        st.markdown("**🗺️ AI roadmap**\n\nGet a real 30/60/90-day plan with courses, project ideas, and portfolio tips.")