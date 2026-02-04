from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, field_validator


app = FastAPI(title="Socrato")

# Enable CORS for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================
# REQUEST/RESPONSE SCHEMAS
# Mirrors shared/types.ts contract
# ============================================

class GenerateRequest(BaseModel):
    """
    Request body for POST /api/v1/generate
    - text: The user's study notes to process
    """
    text: str

    @field_validator("text")
    @classmethod
    def text_must_not_be_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("text must not be empty")
        return v


class QuizQuestion(BaseModel):
    """A single quiz question with multiple choice options"""
    question: str
    options: list[str]
    answer: str


class GenerateResponse(BaseModel):
    """
    Response from POST /api/v1/generate
    - summary: Array of bullet point summaries
    - quiz: Array of quiz questions with options and answers
    """
    summary: list[str]
    quiz: list[QuizQuestion]


# ============================================
# ROUTES
# ============================================

@app.get("/")
def root():
    return {}


@app.get("/health")
def check_health():
    return {"status": "ok"}


@app.post("/api/v1/generate", response_model=GenerateResponse)
def generate_study_materials(request: GenerateRequest):
    """
    Generate study materials from user notes.
    
    Request body:
        - text (string): The user's study notes to process
    
    Returns:
        - summary (string[]): Array of bullet point summaries
        - quiz (QuizQuestion[]): Array of quiz questions
    """
    # TODO: Integrate with AI service to generate actual content
    # For now, return a placeholder response to verify the contract
    return GenerateResponse(
        summary=[
            "Placeholder summary point 1",
            "Placeholder summary point 2",
        ],
        quiz=[
            QuizQuestion(
                question="Placeholder question?",
                options=["Option A", "Option B", "Option C", "Option D"],
                answer="Option A"
            )
        ]
    )