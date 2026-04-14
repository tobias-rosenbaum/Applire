import os

# Interview orchestrator thresholds and limits (ADR 004, Iteration 14)

# Mode auto-detection: completeness_score below this → MODE B (Guided Build)
MODE_B_COMPLETENESS_THRESHOLD: float = 0.3

# Hard ceilings — session ends after this many questions even if gaps remain
INTERVIEW_HARD_CEILING_TARGETED: int = 12  # MODE A
INTERVIEW_HARD_CEILING_GUIDED: int = 20    # MODE B

# Soft targets — informational only, used for estimated_questions in response
INTERVIEW_TARGET_MIN_TARGETED: int = 3
INTERVIEW_TARGET_MIN_GUIDED: int = 5

# Per-gap question ceiling (Sprint 15): max questions asked for a single gap
# before force-advancing to the next one. Includes the initial question.
# Set INTERVIEW_MAX_QUESTIONS_PER_GAP in environment to override (e.g. in docker-compose.yml).
INTERVIEW_MAX_QUESTIONS_PER_GAP: int = int(
    os.environ.get("INTERVIEW_MAX_QUESTIONS_PER_GAP", "3")
)

# LLM review layer — retry ceiling (ADR-021, Sprint 20)
# Set LLM_REVIEW_MAX_RETRIES=0 to disable the review layer entirely.
LLM_REVIEW_MAX_RETRIES: int = int(
    os.environ.get("LLM_REVIEW_MAX_RETRIES", "2")
)

# GDPR retention TTLs — configurable via environment variables (ADR-005 amendment, Sprint 25)
GENERATED_DOCUMENTS_TTL_DAYS: int = int(os.environ.get("GENERATED_DOCUMENTS_TTL_DAYS", "90"))
INTERVIEW_SESSION_TTL_DAYS: int = int(os.environ.get("INTERVIEW_SESSION_TTL_DAYS", "30"))
UPLOAD_TTL_DAYS: int = int(os.environ.get("UPLOAD_TTL_DAYS", "7"))
PROFILE_INACTIVITY_TTL_DAYS: int = int(os.environ.get("PROFILE_INACTIVITY_TTL_DAYS", "730"))
