PRD: YouTube Learning AI App (MVP)
1. Overview & Goal

Goal: Build a productivity-focused AI app to help users efficiently learn from YouTube videos by summarizing content, enabling interactive Q&A, and storing knowledge in a personal vector database. The app demonstrates understanding of AI, RAG, embeddings, and full-stack deployment for portfolio purposes.

MVP Scope:

Minimal user base (self + a few testers)

Polished, interactive UI

Core functionality: subtitle extraction → summarization → RAG Q&A → personal knowledge storage

2. Target Users

Primary Users: Yourself and a few test users (friends, mentors)

User Needs: Efficiently extract knowledge from long-form video content, save time, and interact with content for deeper learning

Recruiter/Portfolio Angle: Demonstrates AI skills (RAG, embeddings, summarization), full-stack development (React frontend, FAISS backend, Vercel deployment), and business value awareness

3. Core Features
Feature	Description	User Story	Recruiter Impact
YouTube Subtitle Extraction	Automatically fetch subtitles from user-provided YouTube URL	As a user, I want to input a YouTube link and get subtitles automatically	Shows integration with external APIs / data extraction
Summarization	Quick overview or detailed analysis options	As a user, I want to choose a summary level (quick vs deep)	Demonstrates LLM prompt engineering, NLP, business value focus
RAG-based Q&A	Ask questions about video content using FAISS embeddings	As a user, I want to ask questions and get answers grounded in video content	Shows advanced AI skills (vector DB, retrieval-augmented generation)
Personal Knowledge Storage	Store embeddings locally per user session	As a user, I want to revisit previously processed videos	Shows understanding of persistent data storage and information retrieval
Polished Interactive UI	Clean, modern React frontend with user-friendly interactions	As a user, I want a visually appealing interface	Demonstrates frontend skills and design awareness
Deployment	Full-stack deployment on Vercel	As a user, I want a hosted web app I can access	Shows ability to deploy and maintain web applications
4. Technical Architecture

Frontend: React (polished, interactive, user-friendly)
Backend: Python (FastAPI)
Vector Database: FAISS for embeddings storage and RAG retrieval
LLM: OpenAI GPT or similar for summarization and Q&A
Deployment: Vercel (frontend) + simple backend hosting (could be serverless or Render)

Data Flow:

User inputs YouTube URL

Backend extracts subtitles

LLM generates summary (quick or detailed)

Subtitles → embeddings → stored in FAISS

User asks questions → embeddings + LLM → answer displayed

5. Success Metrics

Functional: Users can summarize a video and ask at least 3 questions accurately

Portfolio / Recruiter Impact: Demonstrates end-to-end AI workflow, full-stack development, and deployment skills

User Value: Saves time in extracting knowledge from videos and provides actionable insights

6. MVP vs Future Enhancements

MVP:

Single-video input

Subtitle extraction + summarization + Q&A

Personal knowledge storage

Polished React frontend

Future Enhancements:

Multi-video knowledge base

Flashcard generation / spaced repetition

Learning analytics (topic tracking, frequently asked questions)

Collaborative knowledge base