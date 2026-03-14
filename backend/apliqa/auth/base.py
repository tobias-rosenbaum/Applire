from abc import ABC, abstractmethod

from fastapi import Request

from apliqa.models.user import User


class AuthProvider(ABC):
    """Base class for all auth provider implementations (ADR 008)."""

    @abstractmethod
    async def get_current_user(self, request: Request) -> User | None:
        """Return the authenticated User for this request, or None if unauthenticated."""
