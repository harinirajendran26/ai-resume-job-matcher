# 🧠 Resume Intelligence Platform

An AI-powered career matching system using **Claude (Anthropic) API** for semantic skill extraction, multi-role match scoring, and streaming AI-generated 90-day learning roadmaps.

🔗 **Live Demo** → [Try it on Streamlit Cloud](https://harinirajendran26-ai-resume-job-matcher.streamlit.app/)

---

## What makes this different

Most resume matchers do simple keyword intersection. This uses **Claude AI for semantic understanding** — "data analysis experience" correctly matches "data analysis" even when phrased differently. It also generates a fully personalised 90-day career roadmap.

---

## Features

| Feature | Technology |
|---|---|
| Semantic skill extraction | Claude (Anthropic) API |
| PDF resume parsing | PyPDF2 |
| Match scoring across 13 career roles | Custom scoring engine |
| Radar chart + bar chart | Matplotlib |
| Streaming AI roadmap | Claude streaming API |
| Cross-role transferable skill detection | Python Counter |
| PDF report download | FPDF |

---

## Architecture

```
Resume (PDF / text)
        │
        ▼
Claude API — semantic skill extraction
        │
        ▼
Match engine — scores all 13 roles
        │
        ├── Match analysis (radar + bar charts)
        ├── Skill gap breakdown
        ├── Cross-role comparison
        └── Claude streaming — 90-day roadmap → PDF export
```

---

## Tech Stack

Python · Streamlit · Anthropic Claude API · PyPDF2 · Matplotlib · FPDF · Pandas

---

## 13 Career Roles Supported

Data Analyst · Data Scientist · Machine Learning Engineer · Software Engineer · Full Stack Developer · Frontend Developer · Backend Developer · Product Manager · UI/UX Designer · DevOps Engineer · Business Analyst · HR Manager · Marketing Analyst

---

## Run locally

```bash
git clone https://github.com/harinirajendran26/ai-resume-job-matcher.git
cd ai-resume-job-matcher
pip install -r requirements.txt
streamlit run app.py

---

Made by - Harini Rajendran (B.E in Artificial Intelligence and Machine Learning)