"""
Iteration 10 — Auth Abstraction (unit tests)
Factory, NoAuthProvider stub shape, and get_current_user() contract.
No Docker or real DB required.

Run:
    pytest tests/unit/ -v
"""
import uuid
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Factory tests
# ---------------------------------------------------------------------------


def test_factory_returns_no_auth_provider_by_default():
    from apliqa.auth import get_auth_provider
    from apliqa.auth.no_auth import NoAuthProvider

    with patch("apliqa.auth.settings") as mock_settings:
        mock_settings.auth_provider = "none"
        provider = get_auth_provider()
    assert isinstance(provider, NoAuthProvider)


def test_factory_is_case_insensitive():
    from apliqa.auth import get_auth_provider
    from apliqa.auth.no_auth import NoAuthProvider

    with patch("apliqa.auth.settings") as mock_settings:
        mock_settings.auth_provider = "None"
        provider = get_auth_provider()
    assert isinstance(provider, NoAuthProvider)


def test_factory_raises_on_unknown_provider():
    from apliqa.auth import get_auth_provider

    with patch("apliqa.auth.settings") as mock_settings:
        mock_settings.auth_provider = "magic"
        with pytest.raises(ValueError, match="Unknown AUTH_PROVIDER"):
            get_auth_provider()


# ---------------------------------------------------------------------------
# NoAuthProvider tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_no_auth_returns_user():
    from apliqa.auth.no_auth import NoAuthProvider
    from apliqa.models.user import User

    provider = NoAuthProvider()
    user = await provider.get_current_user(MagicMock())
    assert isinstance(user, User)


@pytest.mark.asyncio
async def test_no_auth_stub_has_stable_id():
    from apliqa.auth.no_auth import NoAuthProvider, _STUB_USER_ID

    provider = NoAuthProvider()
    user = await provider.get_current_user(MagicMock())
    assert user.id == _STUB_USER_ID


@pytest.mark.asyncio
async def test_no_auth_stub_has_expected_email():
    from apliqa.auth.no_auth import NoAuthProvider, _STUB_EMAIL

    provider = NoAuthProvider()
    user = await provider.get_current_user(MagicMock())
    assert user.email == _STUB_EMAIL


@pytest.mark.asyncio
async def test_no_auth_returns_same_user_on_repeated_calls():
    from apliqa.auth.no_auth import NoAuthProvider

    provider = NoAuthProvider()
    user1 = await provider.get_current_user(MagicMock())
    user2 = await provider.get_current_user(MagicMock())
    assert user1.id == user2.id
    assert user1.email == user2.email


@pytest.mark.asyncio
async def test_no_auth_user_is_not_deleted():
    from apliqa.auth.no_auth import NoAuthProvider

    provider = NoAuthProvider()
    user = await provider.get_current_user(MagicMock())
    assert user.deleted_at is None


# ---------------------------------------------------------------------------
# AuthProvider ABC contract
# ---------------------------------------------------------------------------


def test_auth_provider_is_abstract():
    from apliqa.auth.base import AuthProvider

    with pytest.raises(TypeError):
        AuthProvider()  # type: ignore[abstract]
