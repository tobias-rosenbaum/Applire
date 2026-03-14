"""
Iteration 7 — MCP Server: tool tests (unit)

Each tool handler is a plain async function and can be called directly without
going through the MCP protocol.  Services and the DB session are mocked.

Run:
    pytest tests/unit/test_iter7_mcp_tools.py -v
"""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mcp.shared.exceptions import McpError

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _mock_db():
    """Return a context-manager mock for apliqa.mcp.deps.get_db."""
    mock_session = AsyncMock()
    cm = MagicMock()
    cm.__aenter__ = AsyncMock(return_value=mock_session)
    cm.__aexit__ = AsyncMock(return_value=False)
    return cm, mock_session


def _mock_result(**kwargs) -> MagicMock:
    """Build a Pydantic-like result mock whose model_dump(mode='json') returns kwargs."""
    m = MagicMock()
    m.model_dump.return_value = kwargs
    return m


# ---------------------------------------------------------------------------
# analyze_jd
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_jd_happy_path():
    from apliqa.mcp.server import analyze_jd

    cm, _ = _mock_db()
    mock_result = _mock_result(id=str(uuid.uuid4()), role_title="Backend Engineer")

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch("apliqa.mcp.server.get_provider"),
        patch("apliqa.mcp.server.job_svc.analyze_jd", AsyncMock(return_value=mock_result)),
    ):
        result = await analyze_jd(text="Senior Backend Engineer at Acme GmbH")

    assert result["role_title"] == "Backend Engineer"


@pytest.mark.asyncio
async def test_analyze_jd_empty_text_raises():
    from apliqa.mcp.server import analyze_jd

    with pytest.raises(McpError) as exc_info:
        await analyze_jd(text="   ")

    assert exc_info.value.error.code == -32602


# ---------------------------------------------------------------------------
# get_profile
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_profile_happy_path():
    from apliqa.mcp.server import get_profile

    cm, _ = _mock_db()
    mock_result = _mock_result(id=str(uuid.uuid4()), completeness=80)

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch("apliqa.mcp.server.profile_svc.get_profile", AsyncMock(return_value=mock_result)),
    ):
        result = await get_profile()

    assert result["completeness"] == 80


@pytest.mark.asyncio
async def test_get_profile_no_profile_raises():
    from apliqa.mcp.server import get_profile

    cm, _ = _mock_db()

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch("apliqa.mcp.server.profile_svc.get_profile", AsyncMock(return_value=None)),
    ):
        with pytest.raises(McpError) as exc_info:
            await get_profile()

    assert exc_info.value.error.code == -32001


# ---------------------------------------------------------------------------
# update_profile
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_profile_happy_path():
    from apliqa.mcp.server import update_profile

    cm, _ = _mock_db()
    mock_result = _mock_result(id=str(uuid.uuid4()), completeness=90)

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch(
            "apliqa.mcp.server.profile_svc.patch_profile_section",
            AsyncMock(return_value=mock_result),
        ),
    ):
        result = await update_profile(section="skills", data=["Python", "FastAPI"])

    assert result["completeness"] == 90


@pytest.mark.asyncio
async def test_update_profile_invalid_section_raises():
    from apliqa.mcp.server import update_profile

    cm, _ = _mock_db()

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch(
            "apliqa.mcp.server.profile_svc.patch_profile_section",
            AsyncMock(side_effect=ValueError("Invalid section 'bad_section'")),
        ),
    ):
        with pytest.raises(McpError) as exc_info:
            await update_profile(section="bad_section", data={})

    assert exc_info.value.error.code == -32602


@pytest.mark.asyncio
async def test_update_profile_no_profile_raises():
    from apliqa.mcp.server import update_profile

    cm, _ = _mock_db()

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch(
            "apliqa.mcp.server.profile_svc.patch_profile_section",
            AsyncMock(side_effect=LookupError("No profile found")),
        ),
    ):
        with pytest.raises(McpError) as exc_info:
            await update_profile(section="skills", data=[])

    assert exc_info.value.error.code == -32001


# ---------------------------------------------------------------------------
# analyze_gaps
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_analyze_gaps_happy_path():
    from apliqa.mcp.server import analyze_gaps

    job_id = str(uuid.uuid4())
    cm, _ = _mock_db()
    mock_result = _mock_result(match_score=72, critical_gaps=["Kubernetes"])

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch("apliqa.mcp.server.get_provider"),
        patch("apliqa.mcp.server.gap_svc.analyze_gaps", AsyncMock(return_value=mock_result)),
    ):
        result = await analyze_gaps(job_id=job_id)

    assert result["match_score"] == 72


@pytest.mark.asyncio
async def test_analyze_gaps_invalid_uuid_raises():
    from apliqa.mcp.server import analyze_gaps

    with pytest.raises(McpError) as exc_info:
        await analyze_gaps(job_id="not-a-uuid")

    assert exc_info.value.error.code == -32602


@pytest.mark.asyncio
async def test_analyze_gaps_job_not_found_raises():
    from apliqa.mcp.server import analyze_gaps

    job_id = str(uuid.uuid4())
    cm, _ = _mock_db()

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch("apliqa.mcp.server.get_provider"),
        patch(
            "apliqa.mcp.server.gap_svc.analyze_gaps",
            AsyncMock(side_effect=LookupError("Job analysis not found")),
        ),
    ):
        with pytest.raises(McpError) as exc_info:
            await analyze_gaps(job_id=job_id)

    assert exc_info.value.error.code == -32001


# ---------------------------------------------------------------------------
# run_interview
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_run_interview_happy_path():
    from apliqa.mcp.server import run_interview

    job_id = str(uuid.uuid4())
    session_id = uuid.uuid4()
    cm, _ = _mock_db()
    mock_result = _mock_result(
        session_id=str(session_id),
        question="Describe your experience with Kubernetes.",
        gaps_total=3,
        gaps_remaining=3,
    )

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch("apliqa.mcp.server.get_provider"),
        patch(
            "apliqa.mcp.server.session_svc.create_session",
            AsyncMock(return_value=mock_result),
        ),
    ):
        result = await run_interview(job_id=job_id)

    assert "session_id" in result
    assert "question" in result


@pytest.mark.asyncio
async def test_run_interview_invalid_uuid_raises():
    from apliqa.mcp.server import run_interview

    with pytest.raises(McpError) as exc_info:
        await run_interview(job_id="bad-uuid")

    assert exc_info.value.error.code == -32602


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_send_message_returns_next_question():
    from apliqa.mcp.server import send_message

    session_id = str(uuid.uuid4())
    cm, _ = _mock_db()
    mock_result = _mock_result(complete=False, question="What was your team size?", gaps_remaining=2)

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch("apliqa.mcp.server.get_provider"),
        patch(
            "apliqa.mcp.server.session_svc.send_message",
            AsyncMock(return_value=mock_result),
        ),
    ):
        result = await send_message(session_id=session_id, message="I used Kubernetes for 2 years.")

    assert result["complete"] is False


@pytest.mark.asyncio
async def test_send_message_returns_complete():
    from apliqa.mcp.server import send_message

    session_id = str(uuid.uuid4())
    cm, _ = _mock_db()
    mock_result = _mock_result(complete=True, question=None, gaps_remaining=None)

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch("apliqa.mcp.server.get_provider"),
        patch(
            "apliqa.mcp.server.session_svc.send_message",
            AsyncMock(return_value=mock_result),
        ),
    ):
        result = await send_message(session_id=session_id, message="done")

    assert result["complete"] is True


@pytest.mark.asyncio
async def test_send_message_empty_message_raises():
    from apliqa.mcp.server import send_message

    with pytest.raises(McpError) as exc_info:
        await send_message(session_id=str(uuid.uuid4()), message="  ")

    assert exc_info.value.error.code == -32602


@pytest.mark.asyncio
async def test_send_message_already_complete_raises():
    from apliqa.mcp.server import send_message

    session_id = str(uuid.uuid4())
    cm, _ = _mock_db()

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch("apliqa.mcp.server.get_provider"),
        patch(
            "apliqa.mcp.server.session_svc.send_message",
            AsyncMock(side_effect=ValueError("Session is already complete")),
        ),
    ):
        with pytest.raises(McpError) as exc_info:
            await send_message(session_id=session_id, message="hello")

    assert exc_info.value.error.code == -32602


# ---------------------------------------------------------------------------
# generate_cv
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_generate_cv_happy_path():
    from apliqa.mcp.server import generate_cv

    job_id = str(uuid.uuid4())
    cv_id = uuid.uuid4()
    cm, _ = _mock_db()
    mock_result = _mock_result(
        cv_id=str(cv_id),
        html_url=f"http://localhost:8001/api/cv/{cv_id}/html",
        pdf_url=f"http://localhost:8001/api/cv/{cv_id}/pdf",
    )

    with (
        patch("apliqa.mcp.server.get_db", return_value=cm),
        patch("apliqa.mcp.server.get_provider"),
        patch("apliqa.mcp.server.cv_svc.generate_cv", AsyncMock(return_value=mock_result)),
    ):
        result = await generate_cv(job_id=job_id)

    assert "cv_id" in result
    assert "html_url" in result
    assert "pdf_url" in result


@pytest.mark.asyncio
async def test_generate_cv_invalid_uuid_raises():
    from apliqa.mcp.server import generate_cv

    with pytest.raises(McpError) as exc_info:
        await generate_cv(job_id="not-a-uuid")

    assert exc_info.value.error.code == -32602
