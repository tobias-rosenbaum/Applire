# Interview orchestrator thresholds and limits (ADR 004, Iteration 14)

# Mode auto-detection: completeness_score below this → MODE B (Guided Build)
MODE_B_COMPLETENESS_THRESHOLD: float = 0.3

# Hard ceilings — session ends after this many questions even if gaps remain
INTERVIEW_HARD_CEILING_TARGETED: int = 12  # MODE A
INTERVIEW_HARD_CEILING_GUIDED: int = 20    # MODE B

# Soft targets — informational only, used for estimated_questions in response
INTERVIEW_TARGET_MIN_TARGETED: int = 3
INTERVIEW_TARGET_MIN_GUIDED: int = 5
