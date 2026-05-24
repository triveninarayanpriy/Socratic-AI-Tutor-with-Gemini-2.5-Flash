# 🎓 Socratic Learning Lab — AI Tutor with Gemini 2.5 Flash

> An intelligent, Socratic-method AI tutor built with Google Gemini
> 2.5 Flash. Guides students through concepts using probing questions
> — never giving direct answers. Two modes: CLI and Gradio web app.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Gemini](https://img.shields.io/badge/Google-Gemini%202.5%20Flash-red)
![Gradio](https://img.shields.io/badge/UI-Gradio-orange)

## 📌 Overview

Two modes:
- socraticai.py — Lightweight CLI tutor
- hi.py — Full Gradio web app with live RPM/RPD dashboard

Both use Gemini 2.5 Flash with a system prompt that enforces
strict Socratic teaching: ask, scaffold, guide — never tell.

## ✨ Key Features

- Gemini 2.5 Flash via official google-genai SDK
- Stateful multi-turn sessions (full conversation context)
- Strict Socratic persona (system-prompted)
- Live rate-limit dashboard (15 RPM / 1,500 RPD)
- Session reset button
- Graceful error handling and friendly limit alerts

## ⚙️ Prerequisites

- Python 3.10+
- Gemini API key from https://aistudio.google.com/app/apikey

## 🚀 Getting Started

1. Clone the repo
   git clone https://github.com/your-username/socratic-learning-lab.git

2. Install dependencies
   pip install google-genai gradio python-dotenv

3. Create .env file:
   GEMINI_API_KEY=your_key_here

4a. Run CLI:  python socraticai.py
4b. Run Web:  python hi.py  → open http://127.0.0.1:7860

## 💬 Example

You: How does binary search work?
AI:  What do you think makes searching a *sorted* list different
     from an unsorted one? What advantage does sorting give you?

## 📁 Project Structure

socratic-learning-lab/
├── socraticai.py     # CLI tutor
├── hi.py             # Gradio web app
├── .env              # API key (not committed)
├── .gitignore
└── README.md
