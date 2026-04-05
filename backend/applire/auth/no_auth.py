import uuid
from datetime import datetime, timezone

from fastapi import Request

from applire.auth.base import AuthProvider
from applire.models.user import User

# Stable stub identity for single-user Community Edition deployments.
_STUB_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")
_STUB_EMAIL = "local@apliqa.community"


class NoAuthProvider(AuthProvider):
    """No-enforcement auth provider for Community Edition (ADR 008).

    Returns a fixed single-user stub. No tokens, no sessions, no enforcement.
    Behaviour is identical to pre-auth MVP — existing routes are unaffected.
    """

    async def get_current_user(self, request: Request) -> User:  # type: ignore[override]
        return User(
            id=_STUB_USER_ID,
            email=_STUB_EMAIL,
            created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
            deleted_at=None,
        )
