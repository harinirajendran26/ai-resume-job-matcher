AI Resume–Career Matcher

A smart AI-powered web app that analyzes your resume, matches it to your ideal career path, and gives you a personalized report — all in seconds.

🔗 **Live Demo** → [Click here to try it on Streamlit](https://harinirajendran26-ai-resume-job-matcher.streamlit.app/)

---

Key Features

✅ Upload your **resume as PDF**  
✅ Choose from **multiple career roles** (tech + non-tech)  
✅ Extract your skills using **spaCy NLP**  
✅ View your **match score**, matched and missing skills  
✅ See how you match with **all other career roles**  
✅ Download a personalized **PDF report**  
✅ **No login, no signup — just works!**

---

Demo Screenshots

### 🔘 Upload Resume & Choose Role
![Upload Resume](https://github.com/harinirajendran26/ai-resume-job-matcher/blob/main/screenshots/upload_and_select.png)

### 🎯 Match Result with Skill Analysis
![Match Score](https://github.com/harinirajendran26/ai-resume-job-matcher/blob/main/screenshots/match_results.png)

### 📈 Career Match Bar Chart
![Bar Chart](https://github.com/harinirajendran26/ai-resume-job-matcher/blob/main/screenshots/bar_chart.png)

### 📥 Download Personalized PDF Report
![PDF Report](https://github.com/harinirajendran26/ai-resume-job-matcher/blob/main/screenshots/pdf_report_button.png)

---

How It Works

1. Resume is parsed using `PyPDF2`
2. Skills are extracted with `spaCy` NLP engine
3. Compared against curated skillsets for each career
4. Displays match % + missing skills + suggestions
5. Offers a PDF report of your results

---

Career Roles Supported

Includes both technical and non-technical roles:

- Data Analyst  
- Data Scientist  
- Machine Learning Engineer  
- Software Engineer  
- Product Manager  
- UI/UX Designer  
- HR Manager  
- Business Analyst  
- Marketing Analyst  

---

Tech Stack

- Python
- Streamlit (frontend)
- spaCy (skill extraction)
- PyPDF2 (PDF reader)
- Matplotlib (visualizations)
- FPDF (report generation)

---

💻 Run It Locally

```bash
git clone https://github.com/harinirajendran26/ai-resume-job-matcher.git
cd ai-resume-job-matcher
pip install -r requirements.txt
streamlit run app.py
----

What I Learned

This wasn’t just a technical project. It taught me:
- How to use **NLP to extract real meaning from text**
- How to simulate **real-world job matching logic**
- That **visual storytelling** can make or break a good idea

---

Use Case

This tool could help:
- ✅ Job seekers understand what skills they lack
- ✅ Recruiters shortlist the right candidates faster
- ✅ Career counselors give tailored advice

---

Resume Description You Can Use

> Built an AI-powered resume–job matching system using NLP, match scoring, and data visualization. Extracted skills from unstructured text, identified best-fit roles, and highlighted missing skills for career improvement.

---

Made by Harini Rajendran

Third-year Artificial Intelligence Engineering student with a love for projects that *solve real problems*.  
Always open to opportunities in AI, data, or product thinking.  
Let’s build something meaningful.

