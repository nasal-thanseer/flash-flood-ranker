# 🌊 Flash Flood Street Ranker

**Final Submission Project: AI Strategy & Business Intelligence Internship @ IBM**

## 📖 Overview
The **Flash Flood Street Ranker** is an AI-powered agentic system engineered to pre-emptively rank street-level vulnerabilities in informal settlements during heavy rainfalls. By synthesizing real-time meteorological data with topographical street layouts, the Agent autonomously designates which streets require priority evacuations *before* water arrives.

This MVP evaluates areas dynamically without reliance on costly closed-source map datasets, fulfilling business intelligence requirements for highly scalable, zero-cost societal impact deployments.

## 🏗️ Architecture & Tech Stack
- **AI Agent Orchestration:** `LangChain` & `LangGraph` built on Python.
- **Large Language Model Engine:** Multi-Model Cascade mapping via Google **Gemini** endpoints (`gemini-2.0-flash` / `gemini-2.5-flash`), natively bypassing strict generative free-tier request limits.
- **Meteorological Live Fetch:** `Open-Meteo` APIs providing live coordinate-based current & expected 24h precipitation.
- **Topographical Map Fetch:** `OpenStreetMap` (Overpass API) extracting street parameters utilizing lightning-fast coordinate bounding box geometry and multi-server cascade redundancy.
- **Frontend Dashboard:** Rapid iteration, highly robust web app engineered via `Streamlit`.

## ⚙️ Setup Instructions
**1. Environment Setup**
Initialize a virtual environment to house Python dependencies:
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**2. API Key Configuration**
Rename the included `.env.example` file to `.env`:
```bash
mv .env.example .env
```
Inside `.env`, provide a valid Google Generative Language API key:
```env
GEMINI_API_KEY="AIza..."
```
*(Your key is safely hidden from version control via `.gitignore`.)*

## 🚀 Execution
Run the primary **Streamlit Dashboard** for full UI and dynamic location interaction:
```bash
streamlit run app.py
```

Alternatively, to trigger the background processing agent purely from terminal output:
```bash
python cli.py --location Chavakkad --lat 10.53 --lon 76.02
```
