/** Mirrors backend `services/gamification.py` quiz_attempt_xp_breakdown (preview / UI). */

import type { XpAwardLine } from "@/types/api";

export const XP_QUIZ_PER_CORRECT = 25;
export const XP_QUIZ_PERFECT_BONUS = 15;

export function quizAttemptXpBreakdown(
  correct: number,
  total: number,
): { xp: number; lines: XpAwardLine[] } {
  if (total <= 0) return { xp: 0, lines: [] };
  const fromCorrect = correct * XP_QUIZ_PER_CORRECT;
  const perfect = correct === total && total > 0;
  const bonus = perfect ? XP_QUIZ_PERFECT_BONUS : 0;
  const xp = fromCorrect + bonus;
  const lines: XpAwardLine[] = [];
  if (fromCorrect > 0) {
    const q = correct === 1 ? "question" : "questions";
    lines.push({ reason: `Correct answers (${correct} ${q})`, xp: fromCorrect });
  }
  if (bonus > 0) {
    lines.push({ reason: "Perfect score bonus", xp: bonus });
  }
  return { xp, lines };
}
