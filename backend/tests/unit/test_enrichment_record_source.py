# Copyright (C) 2024-2026 Tobias Rosenbaum
# SPDX-License-Identifier: AGPL-3.0-or-later
"""EnrichmentRecord.source accepts the new manual_role_add value."""
from datetime import datetime, timezone

from applire.schemas.profile import EnrichmentRecord


def test_source_accepts_manual_role_add():
    rec = EnrichmentRecord(
        timestamp=datetime.now(timezone.utc),
        source="manual_role_add",
    )
    assert rec.source == "manual_role_add"
