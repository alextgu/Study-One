from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from typing import Any

from services.supabase import get_supabase


XP_FLASHCARD_SESSION = 10
XP_QUIZ_COMPLETION = 25
XP_PERFECT_QUIZ_BONUS = 15

# Graded quiz submit (POST /api/v1/quiz/attempt) — per-correct + perfect bonus
XP_QUIZ_PER_CORRECT = 25
XP_QUIZ_PERFECT_BONUS = 15

# Level-from-XP formula: L2 at 100 XP, then +120, +140, +160, +180, ... (L3=220, L4=360, L5=520)
# MUST match public.xp_to_level() in 20250302000002_level_from_xp.sql


def xp_to_level(xp_total: int) -> int:
    """Return level (>= 1) for a given total XP. L2=100, L3=220, L4=360, L5=520, ..."""
    import math
    if xp_total <= 0:
        return 1
    # Inverse of xp_for_level(L) = (L-1)*(80 + 10*L)
    level = int((-70 + math.sqrt(8100 + 40.0 * xp_total)) / 20)
    return max(1, level)


def xp_for_level(level: int) -> int:
    """Minimum total XP required to reach this level. L1=0, L2=100, L3=220, L4=360, L5=520, ..."""
    if level <= 1:
        return 0
    return (level - 1) * (80 + 10 * level)  # 100, 220, 360, 520, 700, ...


def _utc_day(dt: datetime) -> date:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).date()


@dataclass(frozen=True)
class StreakUpdate:
    current_streak_days: int
    longest_streak_days: int


def compute_streak_update(
    *,
    last_active_at: datetime | None,
    current_streak_days: int,
    longest_streak_days: int,
    occurred_at: datetime,
) -> StreakUpdate:
    """
    Pure streak logic (UTC-day based). Used for unit tests only.
    MUST stay in sync with public.apply_activity() in 20250302000001_xp_streak_engine.sql.
    - Same day: no streak change
    - Next consecutive day: +1
    - Any gap: reset to 1
    """
    activity_day = _utc_day(occurred_at)
    if last_active_at is None:
        new_current = 1
    else:
        last_day = _utc_day(last_active_at)
        if activity_day == last_day:
            new_current = max(current_streak_days, 1)
        elif activity_day == (last_day + timedelta(days=1)):
            new_current = max(current_streak_days, 0) + 1
        else:
            new_current = 1

    new_longest = max(longest_streak_days, new_current)
    return StreakUpdate(current_streak_days=new_current, longest_streak_days=new_longest)


def quiz_attempt_xp_breakdown(*, correct: int, total: int) -> tuple[int, list[dict[str, Any]]]:
    """
    XP for a graded quiz: (XP per correct answer) + optional perfect-score bonus.
    Returns (total_xp, lines for UI/analytics metadata).
    """
    if total <= 0:
        return 0, []
    if correct < 0 or correct > total:
        raise ValueError("correct must be within [0, total]")

    from_correct = correct * XP_QUIZ_PER_CORRECT
    perfect = correct == total and total > 0
    bonus = XP_QUIZ_PERFECT_BONUS if perfect else 0
    total_xp = from_correct + bonus

    lines: list[dict[str, Any]] = []
    if from_correct > 0:
        q = "question" if correct == 1 else "questions"
        lines.append(
            {
                "reason": f"Correct answers ({correct} {q})",
                "xp": from_correct,
            }
        )
    if bonus > 0:
        lines.append({"reason": "Perfect score bonus", "xp": bonus})

    return total_xp, lines


def record_quiz_attempt_xp(
    *,
    user_id: str,
    xp_awarded: int,
    occurred_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Persist quiz_attempt activity and update aggregates when xp_awarded > 0.
    Returns { xp_awarded, user_stats } (user_stats may be null if user has no stats row and xp is 0).
    """
    if xp_awarded < 0:
        raise ValueError("xp_awarded must be >= 0")

    sb = get_supabase()
    payload = {
        "p_user_id": user_id,
        "p_xp_awarded": xp_awarded,
        "p_occurred_at": (occurred_at or datetime.now(timezone.utc)).isoformat(),
        "p_metadata": metadata or {},
    }
    res = sb.rpc("apply_quiz_attempt_record", payload).execute()
    if res.data is None:
        raise RuntimeError(f"apply_quiz_attempt_record failed: {res}")
    return res.data


def apply_activity(
    *,
    user_id: str,
    activity_type: str,
    xp_awarded: int,
    occurred_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Idempotently apply a daily activity and return:
      { applied: bool, xp_awarded: int, user_stats: {...} }
    """
    if xp_awarded < 0:
        raise ValueError("xp_awarded must be >= 0")

    sb = get_supabase()
    payload = {
        "p_user_id": user_id,
        "p_activity_type": activity_type,
        "p_xp_awarded": xp_awarded,
        "p_occurred_at": (occurred_at or datetime.now(timezone.utc)).isoformat(),
        "p_metadata": metadata or {},
    }
    res = sb.rpc("apply_activity", payload).execute()
    # supabase-py returns {"data": <jsonb>, "error": ...} shape via PostgREST
    if res.data is None:
        raise RuntimeError(f"apply_activity failed: {res}")
    return res.data


def award_flashcard_session_xp(
    *,
    user_id: str,
    occurred_at: datetime | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    md: dict[str, Any] = {
        "xp_breakdown": [
            {"reason": "Flashcard session completed", "xp": XP_FLASHCARD_SESSION},
        ],
    }
    if session_id:
        md["session_id"] = session_id
    return apply_activity(
        user_id=user_id,
        activity_type="flashcard_session",
        xp_awarded=XP_FLASHCARD_SESSION,
        occurred_at=occurred_at,
        metadata=md,
    )


def award_quiz_completion_xp(
    *,
    user_id: str,
    correct: int,
    total: int,
    occurred_at: datetime | None = None,
    quiz_id: str | None = None,
) -> dict[str, Any]:
    if total <= 0:
        raise ValueError("total must be > 0")
    if correct < 0 or correct > total:
        raise ValueError("correct must be within [0, total]")

    perfect = correct == total
    xp = XP_QUIZ_COMPLETION + (XP_PERFECT_QUIZ_BONUS if perfect else 0)
    md: dict[str, Any] = {"correct": correct, "total": total, "perfect": perfect}
    if quiz_id:
        md["quiz_id"] = quiz_id
    return apply_activity(
        user_id=user_id,
        activity_type="quiz_completion",
        xp_awarded=xp,
        occurred_at=occurred_at,
        metadata=md,
    )

