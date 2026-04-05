# backend/tests/unit/test_iter24_schemas.py
"""Schema smoke tests for Sprint 10 assist schemas."""
from apliqa.schemas.cv_sections import (
    AssistStartRequest,
    AssistStartResponse,
    AssistAnswerRequest,
    AssistAnswerResponse,
    SectionPatchResponse,
)


def test_assist_start_request():
    r = AssistStartRequest(gap_id="Python")
    assert r.gap_id == "Python"


def test_assist_start_response():
    r = AssistStartResponse(session_id="abc", question="Wie lange nutzen Sie Python?")
    assert r.session_id == "abc"
    assert r.question == "Wie lange nutzen Sie Python?"


def test_assist_answer_request():
    r = AssistAnswerRequest(session_id="abc", answer="5 Jahre")
    assert r.session_id == "abc"


def test_assist_answer_response():
    r = AssistAnswerResponse(suggestion="Erfahrener Python-Entwickler mit 5 Jahren Erfahrung.")
    assert "Python" in r.suggestion


def test_section_patch_response_has_resolved_gaps_default():
    r = SectionPatchResponse(html="<html/>", overrides_applied=["introduction"])
    assert r.resolved_gaps == []


def test_section_patch_response_with_resolved_gaps():
    r = SectionPatchResponse(
        html="<html/>",
        overrides_applied=["introduction"],
        resolved_gaps=["Python", "AWS"],
    )
    assert len(r.resolved_gaps) == 2
