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
