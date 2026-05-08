# Copyright (C) 2024-2026 Tobias Rosenbaum
#
# This file is part of Applire.
#
# Applire is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Applire is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with Applire. If not, see <https://www.gnu.org/licenses/>.

from abc import ABC, abstractmethod

from fastapi import Request

from applire.models.user import User


class AuthProvider(ABC):
    """Base class for all auth provider implementations (ADR 008)."""

    @abstractmethod
    async def get_current_user(self, request: Request) -> User | None:
        """Return the authenticated User for this request, or None if unauthenticated."""
