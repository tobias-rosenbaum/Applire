# Deterministic done-signal detection — no LLM call, runs before ResponseParser.

TERMINATION_SIGNALS: frozenset[str] = frozenset(
    {
        # English
        "done",
        "skip",
        "that's all",
        "finish",
        "end",
        # German
        "fertig",
        "überspringen",
        "das war's",
        "abschließen",
        "ende",
    }
)


def is_termination_signal(message: str) -> bool:
    """Return True if the message is a recognised session-end signal.

    Case-insensitive, trims leading/trailing whitespace.
    Intentionally kept as a simple set lookup — no LLM, no regex.
    """
    return message.strip().lower() in TERMINATION_SIGNALS
