# Socrato

### AI that makes you *think*, not think for you.

---

## The Problem

Generative AI is eroding critical thinking in education. Students increasingly turn to ChatGPT and similar tools to complete assignments verbatim, bypassing the learning process entirely. The result is a generation that can prompt an AI but struggles to reason through problems independently. Institutions are scrambling to ban these tools, but the genie is out of the bottle — AI isn't going away.

## Our Approach

Instead of fighting AI, **Socrato flips the script**: it uses large language models and gamification as tools *for* studying, not *instead of* it. Paste your notes, and Socrato transforms them into structured summaries, interactive quizzes, and flashcards — then rewards you with XP and badges for actually engaging with the material. The AI does the formatting; you do the thinking.

The core insight is simple: AI is great at generating practice material, but the learning still has to happen in the student's head. Socrato sits in that gap.

---

## How It Works

1. **Paste your notes** into the app.
2. **Gemini 2.5 Flash** generates summaries, multiple-choice quizzes (with topic tagging and correction explanations), and flashcards — all from a single input.
3. **Take the quiz**, get instant grading and per-question AI explanations. Ask follow-up questions if you don't understand why an answer is wrong.
4. **Review flashcards** with an Anki-style spaced repetition system (Again / Hard / Good / Easy).
5. **Earn XP and badges** for completing quizzes and flashcard sessions. A gamification engine tracks streaks, awards bonuses for perfect scores, and evaluates badge triggers after every activity.

Everything is persisted — quizzes, attempts, scores, flashcard reviews, XP — so progress carries across sessions.

---

## Tech Stack

| Layer | Technology | Role |
|-------|-----------|------|
| **Frontend** | Next.js 16, React 19, TypeScript, Tailwind CSS | App UI, auth state, API client |
| **Backend** | Python, FastAPI | REST API, prompt orchestration, response validation |
| **AI** | Google Gemini 2.5 Flash | Study pack, quiz, flashcard, and explanation generation |
| **Database** | Supabase (PostgreSQL) | User data, quiz storage, attempt tracking, XP, badges |
| **Auth** | Supabase Auth + JWT | Sign up/in, token-based route protection |

### Architecture

```
┌──────────────┐       Bearer token       ┌──────────────────┐      async      ┌─────────────┐
│   Next.js    │  ──────────────────────►  │    FastAPI        │  ────────────►  │   Gemini    │
│   Frontend   │  ◄──────────────────────  │    Backend        │  ◄────────────  │   2.5 Flash │
└──────────────┘       JSON response       └────────┬─────────┘    structured   └─────────────┘
                                                    │              JSON
                                                    │
                                               ┌────▼────┐
                                               │ Supabase │
                                               │ Postgres │
                                               └─────────┘
```

The backend uses a **versioned prompt template system** (`prompts/study_gen_v1.py`, `quiz_gen_v1.py`, `flashcard_gen_v1.py`) with few-shot examples and strict JSON output constraints. Every LLM response passes through schema validation (field presence, type checking, option-answer consistency) before reaching the client or database.

---

## Project Structure

```
Study-One/
├── frontend/          → Next.js web app (React, TypeScript, Tailwind)
├── backend/           → FastAPI server (Python)
│   ├── middleware/     → JWT authentication
│   ├── prompts/       → Versioned prompt templates for Gemini
│   ├── services/      → Gemini AI client, Supabase client, gamification engine
│   └── tests/         → Unit and integration tests
├── shared/            → Shared type definitions (API contract)
└── .env               → Environment variables (git-ignored)
```

---

## Getting Started

### Prerequisites

- **Node.js** 18+
- **Python** 3.11+
- A [Supabase](https://supabase.com) project
- A [Gemini API key](https://aistudio.google.com/apikey)

### Clone

```bash
git clone https://github.com/utmgdsc/Study-One.git
cd Study-One
```

### Environment Variables

**Backend** — create `Study-One/.env`:

```env
GEMINI_API_KEY="your-gemini-key"

# Supabase — Dashboard → Settings → API
SUPABASE_URL="https://<project-ref>.supabase.co"
SUPABASE_SERVICE_ROLE_KEY="eyJ..."
SUPABASE_JWT_SECRET="your-jwt-secret"
```

**Frontend** — copy `frontend/.env.example` to `frontend/.env.local`:

```env
NEXT_PUBLIC_SUPABASE_URL="https://<project-ref>.supabase.co"
NEXT_PUBLIC_SUPABASE_ANON_KEY="eyJ..."
```

> `.env` files are git-ignored and must never be committed.

### Run the Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate        # macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload       # → http://localhost:8000
```

### Run the Frontend

```bash
cd frontend
npm install
npm run dev                     # → http://localhost:3000
```

Run both for full functionality.

---

## API Overview

All endpoints (except `/health`) require `Authorization: Bearer <token>`.

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check (public) |
| `GET` | `/api/v1/me` | Authenticated user identity |
| `POST` | `/api/v1/generate` | Generate summary + quiz from notes |
| `POST` | `/generate-study-pack` | Generate study pack (stricter validation) |
| `POST` | `/api/v1/quiz` | Generate and store a graded quiz |
| `POST` | `/api/v1/quiz/attempt` | Submit quiz answers, get grading + XP |
| `POST` | `/api/v1/quiz/explain` | AI explanation for a quiz question |
| `POST` | `/api/v1/quiz/result` | Record quiz completion for XP/badges |
| `POST` | `/api/v1/flashcards` | Generate and store flashcards |
| `POST` | `/api/v1/flashcards/review` | Submit Anki-style card rating |
| `POST` | `/api/v1/flashcards/session-complete` | Record session for XP/badges |
| `GET` | `/api/v1/flashcards/:id/history` | Card review history |

---

## Running Tests

```bash
cd backend
python -m pytest tests/ -v
```

Tests use real JWT tokens signed with your `SUPABASE_JWT_SECRET`. All Gemini calls are mocked — no API quota consumed.

---

## Team

Built by Arhum, Alex, Jessie, Sean and Usha under Professor Mahmoud.
