# AI Study Planner

Full-stack spaced repetition study planner built with **FastAPI**, **Next.js**, and **machine learning**.

This application helps students organize courses, plan study sessions using spaced repetition, and track learning progress. It also includes a simple ML model that predicts which study sessions are likely to be difficult and recommends earlier review.

---

## Features

- Create courses and topics
- Deadline-aware study planning
- Generate spaced repetition study schedules
- Daily study queue for focused learning
- Mark sessions as completed with difficulty ratings
- Track study analytics in a dashboard
- Machine learning prediction of difficult study sessions

---

## Tech Stack

### Frontend
- Next.js
- React
- TypeScript

### Backend
- FastAPI
- SQLAlchemy
- SQLite / PostgreSQL

### Machine Learning
- scikit-learn
- Logistic Regression model

---

## Architecture
User → Next.js Frontend → FastAPI Backend → Database
↓
ML Model

---

## Project Structure
ai-study-planner/
│
├── api/        # FastAPI backend
│   ├── routers
│   ├── models
│   ├── schemas
│   └── main.py
│
├── web/        # Next.js frontend
│   ├── src/app
│   │   ├── courses
│   │   ├── today
│   │   └── dashboard
│   └── lib/api.ts
│
└── README.md

---

## How It Works

1. Users create courses and add study topics.
2. The backend generates spaced repetition schedules based on deadlines.
3. Each day the user sees a study queue.
4. When a session is completed, difficulty and study time are recorded.
5. This data is used to train a simple machine learning model.
6. The model predicts whether future sessions are likely to be difficult and suggests earlier review.

---

## Running Locally

### Backend
cd api
source .venv/bin/activate
uvicorn main:app –reload –port 8000

Backend API docs:
http://127.0.0.1:8000/docs

---

### Frontend
cd web
npm install
npm run dev

Frontend runs at:
http://localhost:3000

---

## What This Project Demonstrates

- Full-stack web development
- REST API design
- Database modeling with SQLAlchemy
- React state management
- Machine learning model training and inference
- Analytics dashboard creation

---

## Author

Rudhmila Hoque
