# Socrato

## Local Development Setup

This project uses:
- FastAPI for the backend
- Next.js for the frontend
- .env for keys

Follow the steps below to run the project locally.

---

## .env Format

```env
# Backend
DATABASE_URL=
JWT_SECRET=
ENV=development
GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

# Frontend
NEXT_PUBLIC_API_URL=
```

---

## Prerequisites

- Python 3.10+
- Node.js 18+
- npm or yarn
- Git

---

## Frontend Setup 

```bash
cd frontend
npm install
npm run dev
```

---

## Backend Start venv

```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Mac: source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```
