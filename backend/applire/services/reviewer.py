"""LLM Review Layer — reviewer-guided retry loop (ADR-021, Sprint 20).

review_and_refine() runs a reviewer LLM call after the initial generator output.
If the reviewer rejects the draft it feeds the critique back to the generator
and retries, up to max_retries times.

Never raises — on retry exhaustion the last draft is returned and a WARNING
is logged so the issue is observable without breaking the caller's flow.
"""

import logging
from collections.abc import Callable
from typing import Any

from applire.providers.llm.base import LLMProvider

logger = logging.getLogger(__name__)


async def review_and_refine(
    source: str,
    draft: dict[str, Any],
    generator_prompt_fn: Callable[[str, dict[str, Any], str], str],
    generator_system: str,
    reviewer_prompt_fn: Callable[[str, dict[str, Any]], str],
    reviewer_system: str,
    provider: LLMProvider,
    max_retries: int,
) -> dict[str, Any]:
    """Run a reviewer-guided retry loop over an LLM generator output.

    Args:
        source: The original source material the reviewer checks the draft against
                (raw CV text for extraction; serialised profile JSON for tailoring).
        draft: The initial generator output to be reviewed.
        generator_prompt_fn: Called as fn(source, previous_draft, feedback) -> str.
                             Used to build the retry user prompt.
        generator_system: The generator's system prompt (unchanged across retries).
        reviewer_prompt_fn: Called as fn(source, draft) -> str.
        reviewer_system: The reviewer's system prompt.
        provider: LLM provider — same instance used by the calling service.
        max_retries: Maximum number of generator retries. 0 = review layer disabled.

    Returns:
        The approved draft, or the last generated draft if retries are exhausted.
    """
    if max_retries <= 0:
        return draft

    current_draft = draft
    last_issues: list[str] = []

    for attempt in range(max_retries):
        review: dict = await provider.aparse_json(
            reviewer_prompt_fn(source, current_draft),
            system=reviewer_system,
            temperature=0.1,
        )

        if review.get("approved", False):
            return current_draft

        last_issues = review.get("issues", [])
        feedback = review.get("feedback", "")
        logger.debug(
            "review_and_refine attempt %d/%d rejected. Issues: %r",
            attempt + 1,
            max_retries,
            last_issues,
        )

        current_draft = await provider.aparse_json(
            generator_prompt_fn(source, current_draft, feedback),
            system=generator_system,
            temperature=0.1,
        )

    # Exhausted all retries — return the last generated draft unreviewed.
    # This is intentional: degraded output is preferable to a broken flow
    # (spec: ADR-021; worst-case call count = 2 * max_retries).
    logger.warning(
        "review_and_refine: %d retries exhausted. Last known issues: %r",
        max_retries,
        last_issues,
    )
    return current_draft
