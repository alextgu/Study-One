/**
 * API Service for Socrato Frontend
 *
 * Handles communication with the backend API.
 * Automatically attaches the Supabase auth token when available.
 */

import type {
  AnkiRating,
  FlashcardHistoryResponse,
  FlashcardResponse,
  FlashcardSessionCompleteResponse,
  GenerateRequest,
  GenerateResponse,
  GenerateQuizResponse,
  SlideStudyPackResponse,
  QuizResultResponse,
  QuizExplanationResponse,
  QuizSubmitRequest,
  QuizSubmitResponse,
} from "../types/api";
import { getAccessToken } from "./auth";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function authHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };

  let token: string | null;
  try {
    token = await getAccessToken();
  } catch (err) {
    console.error("Failed to retrieve access token:", err);
    token = null;
  }

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  return headers;
}

/**
 * Generates study materials (summary and quiz) from user notes.
 *
 * @param text - The user's study notes to process
 * @returns Promise containing summary bullet points and quiz questions
 * @throws Error if the request fails or validation fails
 */
export async function generateStudyMaterials(
  text: string,
): Promise<GenerateResponse> {
  const request: GenerateRequest = { text };

  const response = await fetch(`${API_BASE_URL}/api/v1/generate`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.detail || `Request failed with status ${response.status}`,
    );
  }

  return response.json();
}

/**
 * Generates study pack from user notes.
 * 
 * @param text - The user's study notes to process
 * @returns Promise containing summary bullet points and quiz questions
 * @throws Error if the request fails or validation fails
 */
export async function generateStudyPack(
  text: string
): Promise<GenerateResponse>{
  const request : GenerateRequest = { text };

  const response = await fetch(`${API_BASE_URL}/generate-study-pack`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok){
    const error = await response.json().catch(()=>({}));
    const errorMessage = error.detail?.[0]?.msg || error.detail || `Request failed with status ${response.status}`;
    throw new Error(errorMessage);
  }
  return response.json();
}

export async function generateStudyPackFromSlides(
  file: File,
): Promise<SlideStudyPackResponse> {
  const formData = new FormData();
  formData.append("file", file);

  let token: string | null;
  try {
    token = await getAccessToken();
  } catch (err) {
    console.error("Failed to retrieve access token:", err);
    token = null;
  }

  const headers: Record<string, string> = {};
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1/slides/study-pack`, {
      method: "POST",
      headers,
      body: formData,
    });
  } catch {
    throw new Error(
      `Cannot reach backend at ${API_BASE_URL}. Check that the API is running and CORS allows this frontend origin.`,
    );
  }

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Generates a flashcard set from user notes or topic.
 * Stores the set in Supabase and returns the cards plus set id.
 */
export async function generateFlashcards(
  text: string,
  topic?: string,
  options?: { includeAuth?: boolean },
): Promise<FlashcardResponse> {
  const body: { text?: string; topic?: string } = {};
  if (text.trim()) body.text = text.trim();
  if (topic && topic.trim()) body.topic = topic.trim();

  const includeAuth = options?.includeAuth ?? true;
  const headers = includeAuth
    ? await authHeaders()
    : { "Content-Type": "application/json" };

  const response = await fetch(`${API_BASE_URL}/api/v1/flashcards`, {
    method: "POST",
    headers,
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.detail || `Request failed with status ${response.status}`,
    );
  }

  return response.json();
}

/**
 * Submit an Anki-style rating for a single flashcard.
 */
export async function submitFlashcardReview(
  flashcardSetId: string,
  cardIndex: number,
  rating: AnkiRating,
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/v1/flashcards/review`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({
      flashcard_set_id: flashcardSetId,
      card_index: cardIndex,
      rating,
    }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed with status ${response.status}`);
  }
}

/**
 * Generates quiz questions from user notes via POST /api/v1/quiz.
 */
export async function generateQuizQuestions(
  text: string
): Promise<GenerateQuizResponse> {
  const normalized = text.trim();
  if (normalized.length < 10) {
    throw new Error("Please provide at least 10 characters to generate a quiz.");
  }
  const payloadText = normalized.slice(0, 10000);

  const response = await fetch(`${API_BASE_URL}/api/v1/quiz`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ text: payloadText }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Regenerates quiz questions from extracted slide text via POST /api/v1/slides/quiz/regenerate.
 */
export async function regenerateSlideQuizQuestions(
  text: string
): Promise<GenerateQuizResponse> {
  const normalized = text.trim();
  if (normalized.length < 10) {
    throw new Error("Please provide at least 10 characters to generate a quiz.");
  }

  const response = await fetch(`${API_BASE_URL}/api/v1/slides/quiz/regenerate`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify({ text: normalized }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Submits quiz answers for grading. Returns score and per-question results.
 */
export async function submitQuiz(
  request: QuizSubmitRequest
): Promise<QuizSubmitResponse> {
  const response = await fetch(`${API_BASE_URL}/api/v1/quiz/attempt`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify(request),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Fetch the latest rating per card for a flashcard set.
 */
export async function fetchFlashcardHistory(
  flashcardSetId: string,
): Promise<FlashcardHistoryResponse> {
  const response = await fetch(
    `${API_BASE_URL}/api/v1/flashcards/${encodeURIComponent(flashcardSetId)}/history`,
    {
      method: "GET",
      headers: await authHeaders(),
    },
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || `Request failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Records flashcard session completion for XP. Awards 10 XP. Idempotent per day
 * (one session per day counts). Call when the user finishes a flashcard session.
 */
export async function submitFlashcardSessionComplete(
  flashcardSetId: string,
  sessionDurationS?: number,
): Promise<FlashcardSessionCompleteResponse> {
  const body: { flashcard_set_id: string; session_duration_s?: number } = {
    flashcard_set_id: flashcardSetId,
  };
  if (sessionDurationS !== undefined) body.session_duration_s = sessionDurationS;

  const response = await fetch(
    `${API_BASE_URL}/api/v1/flashcards/session-complete`,
    {
      method: "POST",
      headers: await authHeaders(),
      body: JSON.stringify(body),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.detail || `Request failed with status ${response.status}`
    );
  }

  return response.json();
}

/**
 * @deprecated Quiz XP is applied in `submitQuiz` (POST /api/v1/quiz/attempt).
 * This endpoint only returns current user stats without awarding XP.
 */
export async function submitQuizResult(
  correct: number,
  total: number,
  quizId?: string
): Promise<QuizResultResponse> {
  const body: { correct: number; total: number; quiz_id?: string } = {
    correct,
    total,
  };
  if (quizId) body.quiz_id = quizId;

  const response = await fetch(`${API_BASE_URL}/api/v1/quiz/result`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.detail || `Request failed with status ${response.status}`
    );
  }

  return response.json();
}

/**
 * Requests an AI explanation for a specific quiz question, optionally with a follow-up prompt.
 */
export async function requestQuizExplanation(params: {
  question: string;
  options: string[];
  answer: string;
  userAnswer?: string | null;
  correctionExplanation?: string | null;
  followupPrompt?: string | null;
}): Promise<QuizExplanationResponse> {
  const body = {
    question: params.question,
    options: params.options,
    answer: params.answer,
    user_answer: params.userAnswer ?? null,
    correction_explanation: params.correctionExplanation ?? null,
    followup_prompt: params.followupPrompt?.trim() || null,
  };

  const response = await fetch(`${API_BASE_URL}/api/v1/quiz/explain`, {
    method: "POST",
    headers: await authHeaders(),
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.detail || `Request failed with status ${response.status}`
    );
  }

  return response.json();
}

/**
 * Logs that a user started a study session (flashcard set or quiz).
 */
export async function logSessionStart(
  resourceId: string,
  resourceType: "flashcard_set" | "quiz",
): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/api/v1/study/session-start`, {
      method: "POST",
      headers: await authHeaders(),
      body: JSON.stringify({ resource_id: resourceId, resource_type: resourceType }),
    });
  } catch {
    // Fire-and-forget; never surface errors to the user
  }
}

/**
 * Logs that a user abandoned a study session mid-way.
 * Uses fetch with keepalive:true so it completes even if the page is unloading.
 */
export function logSessionAbandon(
  resourceId: string,
  resourceType: "flashcard_set" | "quiz",
  payload: {
    sessionDurationS?: number;
    cardsReviewed?: number;
    questionsAnswered?: number;
    totalQuestions?: number;
  },
  token: string | null,
): void {
  const body = JSON.stringify({
    resource_id: resourceId,
    resource_type: resourceType,
    session_duration_s: payload.sessionDurationS,
    cards_reviewed: payload.cardsReviewed,
    questions_answered: payload.questionsAnswered,
    total_questions: payload.totalQuestions,
  });

  // keepalive:true ensures the request completes even during beforeunload
  fetch(`${API_BASE_URL}/api/v1/study/abandon`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body,
    keepalive: true,
  }).catch(() => {
    // Fire-and-forget
  });
}