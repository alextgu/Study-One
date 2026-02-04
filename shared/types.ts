/**
 * Shared API Contract for Socrato V1 (To be extended)
 * 
 * This file defines the request/response schemas for communication
 * between the frontend and backend. 
 */

// ============================================
// REQUEST SCHEMA
// ============================================

/**
 * Request body for POST /api/v1/generate
 * @property text - The user's study notes to process
 */
export interface GenerateRequest {
  text: string;
}

// ============================================
// RESPONSE SCHEMA
// ============================================

/**
 * A single quiz question with multiple choice options
 */
export interface QuizQuestion {
  question: string;
  options: string[];
  answer: string;
}

/**
 * Response from POST /api/v1/generate
 * @property summary - Array of bullet point summaries
 * @property quiz - Array of quiz questions with options and answers
 */
export interface GenerateResponse {
  summary: string[];
  quiz: QuizQuestion[];
}
