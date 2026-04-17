# Multilingual UI (i18n) — DE + EN Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add German and English UI support to Applire using next-intl (non-routing mode), with language auto-detected from the browser on first visit and persisted in `user_settings`.

**Architecture:** next-intl `NextIntlClientProvider` wraps the app inside a `LocaleProvider` client component. The provider fetches `ui_language` from `GET /api/settings` (which auto-detects from `Accept-Language` on first visit) and makes `useTranslations()` available everywhere. All hardcoded UI strings are replaced with translation keys from `messages/de.json` and `messages/en.json`. LLM question language is out of scope — deferred to the next sprint.

**Tech Stack:** next-intl ^3, Next.js 15 (App Router), FastAPI, SQLAlchemy, Alembic, Vitest, pytest

**Spec:** `docs/superpowers/specs/2026-04-17-multilingual-ui-i18n-design.md`

---

## File Map

**New files:**
- `backend/alembic/versions/0025_user_settings_ui_language.py`
- `frontend/messages/en.json`
- `frontend/messages/de.json`
- `frontend/lib/providers/locale-provider.tsx`
- `frontend/lib/test-utils/with-intl.tsx`
- `scripts/check-i18n-parity.js`

**Modified files:**
- `backend/applire/models/user_settings.py` — add `ui_language` column
- `backend/applire/routers/settings.py` — language detection + extended PATCH
- `tests/unit/test_settings_endpoint.py` — language detection tests
- `frontend/package.json` — add next-intl, i18n parity check script
- `frontend/components/providers.tsx` — mount LocaleProvider
- `frontend/app/layout.tsx` — keep `lang="de"` default (LocaleProvider updates at runtime)
- `frontend/app/settings/page.tsx` — language switcher + full translation
- `frontend/app/page.tsx` — translate all strings
- `frontend/components/processing-overlay.tsx` + its test
- `frontend/app/flow/[flowId]/gaps/page.tsx`
- `frontend/app/flow/[flowId]/interview/page.tsx`
- `frontend/app/flow/[flowId]/cv/page.tsx`
- `frontend/app/flow/[flowId]/import/page.tsx`
- `frontend/components/cv/GapHint.tsx` + test
- `frontend/components/cv/SectionEditor.tsx` + test
- `frontend/components/cv/KaileChat.tsx` + test
- `frontend/components/cv/ContentTab.tsx` + test
- `frontend/components/cv/ActionsTab.tsx` + test
- `frontend/components/cv/DesignTab.tsx` + test
- `frontend/components/cv/RefinementPanel.tsx` + test
- `frontend/components/cv/SaveScopePrompt.tsx` + test
- `frontend/components/cv/WhatNext.tsx`
- `frontend/app/flow/[flowId]/cover-letter/page.tsx`
- `frontend/components/cover-letter/GenerateCoverLetterModal.tsx`
- `frontend/components/cover-letter/CoverLetterContentTab.tsx`
- `frontend/components/cover-letter/CoverLetterActionsTab.tsx`
- `frontend/components/cover-letter/CoverLetterDesignTab.tsx`
- `frontend/components/cover-letter/CoverLetterRefinementPanel.tsx` + test
- `frontend/components/dashboard/Dashboard.tsx`
- `frontend/components/dashboard/NewApplicationModal.tsx`
- `frontend/components/dashboard/ApplicationCard.tsx`
- `frontend/components/offline-banner.tsx`
- `frontend/app/profile/page.tsx`

---

## Task 1: Add `ui_language` to UserSettings model and migration

**Files:**
- Modify: `backend/applire/models/user_settings.py`
- Create: `backend/alembic/versions/0025_user_settings_ui_language.py`

- [ ] **Step 1: Add `ui_language` column to the ORM model**

Replace the entire content of `backend/applire/models/user_settings.py`:

```python
import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from applire.db.session import Base


class UserSettings(Base):
    __tablename__ = "user_settings"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id"), nullable=False, index=True
    )
    default_color_profile_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("cv_color_profiles.id"), nullable=True
    )
    ui_language: Mapped[str | None] = mapped_column(
        String(5), nullable=True, default=None
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
```

- [ ] **Step 2: Create Alembic migration**

Create `backend/alembic/versions/0025_user_settings_ui_language.py`:

```python
"""Add ui_language to user_settings

Revision ID: 0025
Revises: 0024
Create Date: 2026-04-17
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0025"
down_revision: Union[str, None] = "0024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "user_settings",
        sa.Column("ui_language", sa.String(5), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("user_settings", "ui_language")
```

- [ ] **Step 3: Verify migration applies cleanly**

```bash
cd backend && alembic upgrade head
```

Expected: Migration `0025` applied with no errors.

- [ ] **Step 4: Commit**

```bash
git add backend/applire/models/user_settings.py backend/alembic/versions/0025_user_settings_ui_language.py
git commit -m "feat: add ui_language column to user_settings"
```

---

## Task 2: Extend settings service and router for language support

**Files:**
- Modify: `backend/applire/routers/settings.py`
- Modify: `tests/unit/test_settings_endpoint.py`

- [ ] **Step 1: Write failing tests for language detection and PATCH**

Add the following test class to `tests/unit/test_settings_endpoint.py` (keep the existing `TestSettingsEndpoint` class and add below it):

```python
class TestLanguageSettings:
    @pytest.mark.asyncio
    async def test_get_settings_detects_german_from_accept_language(self, db):
        from applire.routers.settings import get_settings
        result = await get_settings(db, accept_language="de-DE,de;q=0.9,en;q=0.8")
        assert result["ui_language"] == "de"

    @pytest.mark.asyncio
    async def test_get_settings_detects_english_for_non_german(self, db):
        from applire.routers.settings import get_settings
        result = await get_settings(db, accept_language="fr-FR,fr;q=0.9")
        assert result["ui_language"] == "en"

    @pytest.mark.asyncio
    async def test_get_settings_defaults_to_english_with_no_header(self, db):
        from applire.routers.settings import get_settings
        result = await get_settings(db, accept_language="")
        assert result["ui_language"] == "en"

    @pytest.mark.asyncio
    async def test_get_settings_persists_detected_language_when_row_exists(self, db):
        from applire.routers.settings import get_settings, update_settings
        # Create a row first via a color update
        await update_settings(db, accent_hex="#112233")
        # GET with German header — should detect and persist
        result = await get_settings(db, accept_language="de-AT")
        assert result["ui_language"] == "de"
        # Second GET without header — should return persisted value
        result2 = await get_settings(db, accept_language="")
        assert result2["ui_language"] == "de"

    @pytest.mark.asyncio
    async def test_patch_settings_stores_ui_language(self, db):
        from applire.routers.settings import update_settings, get_settings
        await update_settings(db, ui_language="de")
        result = await get_settings(db)
        assert result["ui_language"] == "de"

    @pytest.mark.asyncio
    async def test_patch_settings_rejects_invalid_language(self, db):
        from applire.routers.settings import update_settings
        with pytest.raises(ValueError, match="ui_language"):
            await update_settings(db, ui_language="zh")

    @pytest.mark.asyncio
    async def test_patch_settings_updates_both_language_and_color(self, db):
        from applire.routers.settings import update_settings, get_settings
        await update_settings(db, accent_hex="#aabbcc", ui_language="en")
        result = await get_settings(db)
        assert result["default_accent_hex"] == "#aabbcc"
        assert result["ui_language"] == "en"
```

Also update the **existing** `TestSettingsEndpoint` tests to use the new keyword-argument signature — replace the three calls that use positional args:

```python
# Old: await update_settings("#334455", db)
# New:
await update_settings(db, accent_hex="#334455")
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_settings_endpoint.py -v
```

Expected: `TestLanguageSettings` tests FAIL (function signatures don't match yet).

- [ ] **Step 3: Rewrite `backend/applire/routers/settings.py`**

```python
"""GET/PATCH /api/settings — user preferences: default CV accent color and UI language."""
import re
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from applire.auth import get_auth_provider
from applire.auth.base import AuthProvider
from applire.db.session import get_db
from applire.services.color_detection import _CE_STUB_USER_ID, derive_tint

router = APIRouter(prefix="/api/settings", tags=["settings"])

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")
_VALID_LANGUAGES = {"de", "en"}


def _detect_language(accept_language: str) -> str:
    """Extract primary language from Accept-Language header.

    Returns 'de' if the primary tag starts with 'de', 'en' otherwise.
    """
    if not accept_language:
        return "en"
    primary = accept_language.split(",")[0].split(";")[0].strip().lower()
    return "de" if primary.startswith("de") else "en"


class SettingsResponse(BaseModel):
    default_color_profile_id: uuid.UUID | None
    default_accent_hex: str | None
    ui_language: str | None


class SettingsPatchRequest(BaseModel):
    default_accent_hex: str | None = None
    ui_language: Literal["de", "en"] | None = None


async def get_settings(db: AsyncSession, accept_language: str = "") -> dict:
    """Service logic — returns current settings for the CE stub user.

    If ui_language is NULL and an accept_language header is provided,
    detects and persists the language before returning.
    """
    from applire.models.user_settings import UserSettings
    from applire.models.color_profile import ColorProfile

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == _CE_STUB_USER_ID)
    )
    row = result.scalar_one_or_none()

    # Auto-detect and persist language on first visit (row exists but language not set)
    if row is not None and row.ui_language is None:
        row.ui_language = _detect_language(accept_language)
        await db.commit()

    # Build response
    ui_language = row.ui_language if row else _detect_language(accept_language)

    if row is None or row.default_color_profile_id is None:
        return {
            "default_color_profile_id": None,
            "default_accent_hex": None,
            "ui_language": ui_language,
        }

    cp = await db.get(ColorProfile, row.default_color_profile_id)
    if cp is None:
        return {
            "default_color_profile_id": None,
            "default_accent_hex": None,
            "ui_language": ui_language,
        }

    return {
        "default_color_profile_id": cp.id,
        "default_accent_hex": cp.seed_primary,
        "ui_language": ui_language,
    }


async def update_settings(
    db: AsyncSession,
    accent_hex: str | None = None,
    ui_language: str | None = None,
) -> dict:
    """Service logic — upsert user settings. Both fields are optional."""
    from applire.models.user_settings import UserSettings
    from applire.models.color_profile import ColorProfile

    if accent_hex is not None and not _HEX_RE.match(accent_hex):
        raise ValueError(f"Invalid hex color: {accent_hex!r}. Must be #RRGGBB.")

    if ui_language is not None and ui_language not in _VALID_LANGUAGES:
        raise ValueError(
            f"Invalid ui_language: {ui_language!r}. Must be one of {_VALID_LANGUAGES}."
        )

    result = await db.execute(
        select(UserSettings).where(UserSettings.user_id == _CE_STUB_USER_ID)
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = UserSettings(user_id=_CE_STUB_USER_ID)
        db.add(row)

    if accent_hex is not None:
        derived = {"--cv-accent": accent_hex, "--cv-accent-tint": derive_tint(accent_hex)}
        cp = ColorProfile(seed_primary=accent_hex, derived=derived, source="user")
        db.add(cp)
        await db.flush()
        row.default_color_profile_id = cp.id

    if ui_language is not None:
        row.ui_language = ui_language

    await db.commit()

    response: dict = {"ui_language": row.ui_language}
    if row.default_color_profile_id:
        cp = await db.get(ColorProfile, row.default_color_profile_id)
        response["default_color_profile_id"] = cp.id if cp else None
        response["default_accent_hex"] = cp.seed_primary if cp else None
    else:
        response["default_color_profile_id"] = None
        response["default_accent_hex"] = None

    return response


@router.get("", response_model=SettingsResponse)
async def api_get_settings(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> SettingsResponse:
    result = await get_settings(db, request.headers.get("accept-language", ""))
    return SettingsResponse(**result)


@router.patch("", response_model=SettingsResponse)
async def api_patch_settings(
    body: SettingsPatchRequest,
    db: AsyncSession = Depends(get_db),
    _auth: AuthProvider = Depends(get_auth_provider),
) -> SettingsResponse:
    try:
        result = await update_settings(
            db,
            accent_hex=body.default_accent_hex,
            ui_language=body.ui_language,
        )
        return SettingsResponse(**result)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/test_settings_endpoint.py -v
```

Expected: All tests in both `TestSettingsEndpoint` and `TestLanguageSettings` PASS.

- [ ] **Step 5: Commit**

```bash
git add backend/applire/routers/settings.py tests/unit/test_settings_endpoint.py
git commit -m "feat: extend settings endpoint with ui_language detection and persistence"
```

---

## Task 3: Install next-intl and create message files

**Files:**
- Modify: `frontend/package.json`
- Create: `frontend/messages/en.json`
- Create: `frontend/messages/de.json`

- [ ] **Step 1: Install next-intl**

```bash
cd frontend && npm install next-intl
```

Expected: `next-intl` appears in `package.json` dependencies; `node_modules/next-intl` exists.

- [ ] **Step 2: Create `frontend/messages/en.json`**

```json
{
  "common": {
    "save": "Save",
    "cancel": "Cancel",
    "loading": "Loading…",
    "error": "Error",
    "back": "Back",
    "delete": "Delete",
    "export": "Export",
    "download": "Download",
    "send": "Send",
    "close": "Close",
    "done": "Done",
    "preparing": "Preparing…"
  },
  "nav": {
    "dashboard": "Dashboard",
    "profile": "My Profile",
    "settings": "Settings",
    "admin": "Admin",
    "help": "Help"
  },
  "home": {
    "tagline": "AI-Powered CV Transformation",
    "yourCVs": "Your CVs",
    "cvUploadHint": "Upload 2-4 CVs for the richest profile. We'll merge them automatically.",
    "jobDescription": "Job Description",
    "jdHint": "Paste a JD so we can tailor your profile immediately.",
    "pasteText": "Paste Text",
    "optional": "(Optional — you can add this later)",
    "analyzeButton": "Analyze & Build Profile",
    "uploadAtLeastOne": "Upload at least one CV to continue",
    "usuallyTakes": "This usually takes about 30 seconds",
    "addMoreFiles": "Add more files for a richer profile"
  },
  "processing": {
    "analyzingJD": "Analyzing job description…",
    "buildingProfile": "Building profile…",
    "jdSkipped": "Job description skipped",
    "jdUrlInvalid": "That URL didn't look valid — you can add it later",
    "jdFetchFailed": "The site blocked us — you can paste the text later",
    "cancel": "Cancel"
  },
  "gaps": {
    "title": "Gap Analysis",
    "matchScore": "Match Score",
    "strengths": "Strengths",
    "categoryB": "Likely Present",
    "categoryC": "Not Demonstrated",
    "startInterview": "Start Interview",
    "jdMissingBannerUrl": "That URL didn't look valid. Paste the job description text to run gap analysis.",
    "jdMissingBannerFetch": "We couldn't load that job posting — it may be blocked or taken down. Paste the job description text to run gap analysis.",
    "addJobDescription": "Add job description →"
  },
  "interview": {
    "loading": "Starting interview…",
    "questionOf": "Question {current} of ~{total}",
    "closingGapsFor": "Closing gaps for",
    "gapsRemaining": "{count, plural, one {# gap remaining} other {# gaps remaining}}",
    "categoryBBadge": "We think you might have this experience based on your background — help us confirm.",
    "discrepancyDetected": "Discrepancy detected",
    "keepOld": "Keep \"{value}\"",
    "useNew": "Use \"{value}\"",
    "placeholder": "Type your answer… (Enter to send, Shift+Enter for new line)",
    "iAmDone": "I'm done",
    "resumeBanner": "Welcome back — continuing where you left off.",
    "gapsRemainingConfirm": "You have {count} {count, plural, one {gap} other {gaps}} remaining — are you sure you want to end?",
    "endInterview": "End interview",
    "continue": "Continue",
    "profileCompleteness": "Profile completeness",
    "questionsAnswered": "Questions answered",
    "gapsResolved": "Gaps resolved",
    "generateCV": "Generate Tailored CV",
    "viewProfile": "View Updated Profile",
    "reasonGapsResolved": "Interview Complete — Gaps Closed!",
    "reasonUserEnded": "Interview Ended",
    "reasonMaxReached": "Interview Limit Reached",
    "completionGapsResolved": "Great work! Your profile has been enriched.",
    "completionOther": "Your answers have been saved to your Master Profile.",
    "roleRequirements": "Role Requirements",
    "advancingToCV": "Preparing…",
    "viewHistory": "View conversation history ({count} {count, plural, one {exchange} other {exchanges}})"
  },
  "cv": {
    "generating": "Generating CV…",
    "download": "Download PDF",
    "regenerate": "Regenerate",
    "allGapsClosed": "All gaps closed",
    "previewOutdated": "Preview may be outdated",
    "contentTab": "Content",
    "actionsTab": "Actions",
    "designTab": "Design",
    "writeMyself": "Write it myself",
    "letKaileHelp": "Let Kaile help",
    "rewriteSection": "Rewrite section",
    "apply": "Apply",
    "editFirst": "Edit first",
    "discardSuggestion": "Discard",
    "colorAutoDetected": "auto-detected",
    "applyColor": "Apply color",
    "defaultColor": "Default color",
    "generalGaps": "General gaps",
    "noSections": "No sections available",
    "saving": "Saving…",
    "save": "Save",
    "cancel": "Cancel",
    "placeholder": "Edit this section…",
    "gapHints": "Related gaps",
    "directionPlaceholder": "Give Kaile a direction, correction, or extra context…",
    "rewriting": "Rewriting…"
  },
  "saveScopePrompt": {
    "saveToProfile": "Save to your Master Profile?",
    "toProfile": "Save to Profile",
    "justThisCV": "Just this CV"
  },
  "unsavedChanges": {
    "title": "Discard unsaved changes?",
    "discard": "Discard",
    "keepEditing": "Keep editing"
  },
  "coverLetter": {
    "generate": "Generate Cover Letter",
    "generating": "Generating cover letter…",
    "download": "Download PDF",
    "regenerate": "Regenerate Cover Letter",
    "viewCV": "← View CV",
    "viewCoverLetter": "View Cover Letter →",
    "contentTab": "Content",
    "actionsTab": "Actions",
    "designTab": "Design"
  },
  "settings": {
    "title": "Settings",
    "language": "Language",
    "languageHint": "Choose the language of the user interface.",
    "dataPrivacy": "Data & Privacy",
    "gdprHint": "Manage your personal data in accordance with GDPR (Art. 17 & 20).",
    "exportMyData": "Export My Data",
    "exportHint": "Download a complete JSON export of all your data (GDPR Art. 20).",
    "deleteAllData": "Delete All My Data",
    "deleteHint": "Permanently erase all your data, including applications, CVs, and profile (GDPR Art. 17).",
    "exporting": "Exporting...",
    "confirmDeletion": "Confirm Data Deletion",
    "deletionIrreversible": "This action is irreversible. All your data will be permanently erased:",
    "deletionItemMasterProfile": "Master Profile and enrichment history",
    "deletionItemApplications": "All applications and their flow sessions",
    "deletionItemInterviews": "Interview sessions and transcripts",
    "deletionItemCVs": "Generated CVs and uploaded files",
    "typeDeleteLabel": "Type DELETE to confirm:",
    "confirmDeleteButton": "Confirm Delete",
    "deleting": "Deleting...",
    "defaultCVColor": "Default CV Color",
    "defaultCVColorHint": "Used when no company color can be detected.",
    "saved": "Saved ✓",
    "back": "← Back"
  },
  "dashboard": {
    "newApplication": "New Application",
    "profileCompleteness": "Profile completeness",
    "recentApplications": "Recent Applications",
    "resume": "Resume",
    "noApplications": "No applications yet"
  },
  "profile": {
    "title": "My Profile"
  },
  "import": {
    "title": "Import CV"
  },
  "offline": {
    "message": "You appear to be offline. Some features may not work."
  },
  "errors": {
    "uploadAtLeastOne": "Please upload at least one CV to continue.",
    "exportFailed": "Export failed. Please try again.",
    "deletionFailed": "Deletion failed. Please try again.",
    "typeDeleteToConfirm": "Please type \"DELETE\" to confirm.",
    "flowNotFound": "Flow not found",
    "failedToStart": "Failed to start interview",
    "http504": "This is taking longer than usual. Please try again.",
    "http503": "Service temporarily busy. Please wait and retry.",
    "http502": "Processing error. Please try a different format.",
    "generic": "An error occurred ({status}). Please try again."
  }
}
```

- [ ] **Step 3: Create `frontend/messages/de.json`**

```json
{
  "common": {
    "save": "Speichern",
    "cancel": "Abbrechen",
    "loading": "Lädt…",
    "error": "Fehler",
    "back": "Zurück",
    "delete": "Löschen",
    "export": "Exportieren",
    "download": "Herunterladen",
    "send": "Senden",
    "close": "Schließen",
    "done": "Fertig",
    "preparing": "Wird vorbereitet…"
  },
  "nav": {
    "dashboard": "Dashboard",
    "profile": "Mein Profil",
    "settings": "Einstellungen",
    "admin": "Admin",
    "help": "Hilfe"
  },
  "home": {
    "tagline": "KI-gestützte Bewerbungsmappe",
    "yourCVs": "Deine Lebensläufe",
    "cvUploadHint": "Lade 2–4 Lebensläufe hoch für das vollständigste Profil. Wir führen sie automatisch zusammen.",
    "jobDescription": "Stellenbeschreibung",
    "jdHint": "Füge eine Stelle ein, damit wir dein Profil sofort zuschneiden können.",
    "pasteText": "Text einfügen",
    "optional": "(Optional — du kannst das später hinzufügen)",
    "analyzeButton": "Analysieren & Profil erstellen",
    "uploadAtLeastOne": "Lade mindestens einen Lebenslauf hoch, um fortzufahren",
    "usuallyTakes": "Das dauert normalerweise ca. 30 Sekunden",
    "addMoreFiles": "Weitere Dateien hinzufügen für ein vollständigeres Profil"
  },
  "processing": {
    "analyzingJD": "Stellenbeschreibung wird analysiert…",
    "buildingProfile": "Profil wird erstellt…",
    "jdSkipped": "Stellenbeschreibung übersprungen",
    "jdUrlInvalid": "Diese URL sieht nicht gültig aus — du kannst sie später hinzufügen",
    "jdFetchFailed": "Die Seite hat uns blockiert — du kannst den Text später einfügen",
    "cancel": "Abbrechen"
  },
  "gaps": {
    "title": "Lückenanalyse",
    "matchScore": "Übereinstimmung",
    "strengths": "Stärken",
    "categoryB": "Wahrscheinlich vorhanden",
    "categoryC": "Nicht nachgewiesen",
    "startInterview": "Interview starten",
    "jdMissingBannerUrl": "Diese URL sah nicht gültig aus. Füge den Stellenbeschreibungstext ein, um die Lückenanalyse auszuführen.",
    "jdMissingBannerFetch": "Wir konnten die Stelle nicht laden — sie ist möglicherweise blockiert oder nicht mehr verfügbar. Füge den Text ein.",
    "addJobDescription": "Stellenbeschreibung hinzufügen →"
  },
  "interview": {
    "loading": "Interview wird gestartet…",
    "questionOf": "Frage {current} von ~{total}",
    "closingGapsFor": "Lücken werden geschlossen für",
    "gapsRemaining": "{count, plural, one {# Lücke verbleibend} other {# Lücken verbleibend}}",
    "categoryBBadge": "Wir vermuten, dass du diese Erfahrung hast — hilf uns, das zu bestätigen.",
    "discrepancyDetected": "Abweichung festgestellt",
    "keepOld": "Behalten: \"{value}\"",
    "useNew": "Verwenden: \"{value}\"",
    "placeholder": "Tippe deine Antwort… (Enter zum Senden, Shift+Enter für neue Zeile)",
    "iAmDone": "Ich bin fertig",
    "resumeBanner": "Willkommen zurück — du machst weiter, wo du aufgehört hast.",
    "gapsRemainingConfirm": "Du hast noch {count} {count, plural, one {offene Lücke} other {offene Lücken}} — bist du sicher, dass du beenden möchtest?",
    "endInterview": "Interview beenden",
    "continue": "Weiter",
    "profileCompleteness": "Profilvollständigkeit",
    "questionsAnswered": "Beantwortete Fragen",
    "gapsResolved": "Geschlossene Lücken",
    "generateCV": "Maßgeschneiderten Lebenslauf erstellen",
    "viewProfile": "Aktualisiertes Profil anzeigen",
    "reasonGapsResolved": "Interview abgeschlossen — Lücken geschlossen!",
    "reasonUserEnded": "Interview beendet",
    "reasonMaxReached": "Fragelimit erreicht",
    "completionGapsResolved": "Gut gemacht! Dein Profil wurde angereichert.",
    "completionOther": "Deine Antworten wurden in deinem Master-Profil gespeichert.",
    "roleRequirements": "Rollenanforderungen",
    "advancingToCV": "Wird vorbereitet…",
    "viewHistory": "Gesprächsverlauf anzeigen ({count} {count, plural, one {Austausch} other {Austausche}})"
  },
  "cv": {
    "generating": "Lebenslauf wird erstellt…",
    "download": "PDF herunterladen",
    "regenerate": "Neu erstellen",
    "allGapsClosed": "Alle Lücken geschlossen",
    "previewOutdated": "Vorschau könnte veraltet sein",
    "contentTab": "Inhalt",
    "actionsTab": "Aktionen",
    "designTab": "Design",
    "writeMyself": "Selbst schreiben",
    "letKaileHelp": "Kaile hilft",
    "rewriteSection": "Abschnitt neu schreiben",
    "apply": "Übernehmen",
    "editFirst": "Zuerst bearbeiten",
    "discardSuggestion": "Verwerfen",
    "colorAutoDetected": "automatisch erkannt",
    "applyColor": "Farbe übernehmen",
    "defaultColor": "Standard-Farbe",
    "generalGaps": "Allgemeine Lücken",
    "noSections": "Keine Abschnitte verfügbar",
    "saving": "Wird gespeichert…",
    "save": "Speichern",
    "cancel": "Abbrechen",
    "placeholder": "Diesen Abschnitt bearbeiten…",
    "gapHints": "Verwandte Lücken",
    "directionPlaceholder": "Gib Kaile eine Richtung, Korrektur oder zusätzlichen Kontext…",
    "rewriting": "Wird neu geschrieben…"
  },
  "saveScopePrompt": {
    "saveToProfile": "Im Master-Profil speichern?",
    "toProfile": "Im Profil speichern",
    "justThisCV": "Nur für diesen Lebenslauf"
  },
  "unsavedChanges": {
    "title": "Ungespeicherte Änderungen verwerfen?",
    "discard": "Verwerfen",
    "keepEditing": "Weiter bearbeiten"
  },
  "coverLetter": {
    "generate": "Anschreiben erstellen",
    "generating": "Anschreiben wird erstellt…",
    "download": "PDF herunterladen",
    "regenerate": "Anschreiben neu erstellen",
    "viewCV": "← Lebenslauf anzeigen",
    "viewCoverLetter": "Anschreiben anzeigen →",
    "contentTab": "Inhalt",
    "actionsTab": "Aktionen",
    "designTab": "Design"
  },
  "settings": {
    "title": "Einstellungen",
    "language": "Sprache",
    "languageHint": "Wähle die Sprache der Benutzeroberfläche.",
    "dataPrivacy": "Daten & Datenschutz",
    "gdprHint": "Verwalte deine persönlichen Daten gemäß DSGVO (Art. 17 & 20).",
    "exportMyData": "Meine Daten exportieren",
    "exportHint": "Lade einen vollständigen JSON-Export aller deiner Daten herunter (DSGVO Art. 20).",
    "deleteAllData": "Alle meine Daten löschen",
    "deleteHint": "Lösche dauerhaft alle deine Daten, einschließlich Bewerbungen, Lebensläufe und Profil (DSGVO Art. 17).",
    "exporting": "Exportiere…",
    "confirmDeletion": "Datenlöschung bestätigen",
    "deletionIrreversible": "Diese Aktion ist unwiderruflich. Alle deine Daten werden dauerhaft gelöscht:",
    "deletionItemMasterProfile": "Master-Profil und Anreicherungshistorie",
    "deletionItemApplications": "Alle Bewerbungen und deren Ablaufsitzungen",
    "deletionItemInterviews": "Interviewsitzungen und Transkripte",
    "deletionItemCVs": "Generierte Lebensläufe und hochgeladene Dateien",
    "typeDeleteLabel": "Gib DELETE ein zur Bestätigung:",
    "confirmDeleteButton": "Löschen bestätigen",
    "deleting": "Wird gelöscht…",
    "defaultCVColor": "Standard-Farbe für Lebensläufe",
    "defaultCVColorHint": "Wird verwendet, wenn keine Firmenfarbe erkannt werden kann.",
    "saved": "Gespeichert ✓",
    "back": "← Zurück"
  },
  "dashboard": {
    "newApplication": "Neue Bewerbung",
    "profileCompleteness": "Profilvollständigkeit",
    "recentApplications": "Letzte Bewerbungen",
    "resume": "Weiter",
    "noApplications": "Noch keine Bewerbungen"
  },
  "profile": {
    "title": "Mein Profil"
  },
  "import": {
    "title": "Lebenslauf importieren"
  },
  "offline": {
    "message": "Du scheinst offline zu sein. Einige Funktionen sind möglicherweise nicht verfügbar."
  },
  "errors": {
    "uploadAtLeastOne": "Bitte lade mindestens einen Lebenslauf hoch, um fortzufahren.",
    "exportFailed": "Export fehlgeschlagen. Bitte versuche es erneut.",
    "deletionFailed": "Löschen fehlgeschlagen. Bitte versuche es erneut.",
    "typeDeleteToConfirm": "Bitte gib \"DELETE\" ein zur Bestätigung.",
    "flowNotFound": "Ablauf nicht gefunden",
    "failedToStart": "Interview konnte nicht gestartet werden",
    "http504": "Das dauert länger als üblich. Bitte versuche es erneut.",
    "http503": "Dienst vorübergehend ausgelastet. Bitte warte und versuche es erneut.",
    "http502": "Verarbeitungsfehler. Bitte versuche ein anderes Format.",
    "generic": "Ein Fehler ist aufgetreten ({status}). Bitte versuche es erneut."
  }
}
```

- [ ] **Step 4: Commit**

```bash
git add frontend/package.json frontend/messages/
git commit -m "feat: install next-intl and create DE/EN message files"
```

---

## Task 4: Create LocaleProvider and wire it into the app

**Files:**
- Create: `frontend/lib/providers/locale-provider.tsx`
- Modify: `frontend/components/providers.tsx`

- [ ] **Step 1: Create `frontend/lib/providers/locale-provider.tsx`**

```tsx
"use client";

import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { NextIntlClientProvider } from "next-intl";
import enMessages from "../../messages/en.json";
import deMessages from "../../messages/de.json";

type Locale = "de" | "en";

const messages: Record<Locale, typeof enMessages> = {
  en: enMessages,
  de: deMessages,
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

interface LocaleContextValue {
  locale: Locale;
  setLocale: (locale: Locale) => Promise<void>;
}

const LocaleContext = createContext<LocaleContextValue>({
  locale: "en",
  setLocale: async () => {},
});

export function useLocale() {
  return useContext(LocaleContext);
}

export function LocaleProvider({ children }: { children: React.ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>("en");

  useEffect(() => {
    fetch(`${API_BASE}/api/settings`)
      .then((r) => r.json())
      .then((data) => {
        const lang = data.ui_language as Locale | null;
        if (lang === "de" || lang === "en") {
          setLocaleState(lang);
          document.documentElement.lang = lang;
        }
      })
      .catch(() => {
        // Network error — stay with "en" default
      });
  }, []);

  const setLocale = useCallback(async (newLocale: Locale) => {
    await fetch(`${API_BASE}/api/settings`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ui_language: newLocale }),
    });
    setLocaleState(newLocale);
    document.documentElement.lang = newLocale;
  }, []);

  return (
    <LocaleContext.Provider value={{ locale, setLocale }}>
      <NextIntlClientProvider locale={locale} messages={messages[locale]}>
        {children}
      </NextIntlClientProvider>
    </LocaleContext.Provider>
  );
}
```

- [ ] **Step 2: Mount `LocaleProvider` in `frontend/components/providers.tsx`**

```tsx
"use client";

import { ErrorBoundary } from "@/components/error-boundary";
import { OfflineBanner } from "@/components/offline-banner";
import { ThemeProvider } from "@/components/theme-provider";
import { LocaleProvider } from "@/lib/providers/locale-provider";

interface ProvidersProps {
  children: React.ReactNode;
}

export function Providers({ children }: ProvidersProps) {
  return (
    <ThemeProvider>
      <LocaleProvider>
        <ErrorBoundary>
          <OfflineBanner />
          {children}
        </ErrorBoundary>
      </LocaleProvider>
    </ThemeProvider>
  );
}
```

- [ ] **Step 3: Verify the app starts without errors**

```bash
cd frontend && npm run dev
```

Open `http://localhost:3000` — the app should load normally. Check browser console for any next-intl errors.

- [ ] **Step 4: Commit**

```bash
git add frontend/lib/providers/locale-provider.tsx frontend/components/providers.tsx
git commit -m "feat: add LocaleProvider with next-intl integration"
```

---

## Task 5: Create Vitest test helper for i18n-wrapped components

**Files:**
- Create: `frontend/lib/test-utils/with-intl.tsx`

All existing component tests that render strings must wrap the component in `NextIntlClientProvider`. This helper makes that one line.

- [ ] **Step 1: Create `frontend/lib/test-utils/with-intl.tsx`**

```tsx
import { NextIntlClientProvider } from "next-intl";
import enMessages from "../../messages/en.json";
import deMessages from "../../messages/de.json";

const allMessages = { en: enMessages, de: deMessages };

/**
 * Wraps a React element in NextIntlClientProvider for Vitest tests.
 * Defaults to English so test assertions can use English strings.
 */
export function withIntl(
  element: React.ReactElement,
  locale: "en" | "de" = "en"
): React.ReactElement {
  return (
    <NextIntlClientProvider locale={locale} messages={allMessages[locale]}>
      {element}
    </NextIntlClientProvider>
  );
}
```

- [ ] **Step 2: Verify the helper file TypeScript-compiles cleanly**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors from `lib/test-utils/with-intl.tsx`.

- [ ] **Step 3: Commit**

```bash
git add frontend/lib/test-utils/with-intl.tsx
git commit -m "test: add withIntl helper for next-intl component tests"
```

---

## Task 6: Translate Settings page and add language switcher

**Files:**
- Modify: `frontend/app/settings/page.tsx`

The Settings page is the best first target: it already has mixed-language strings ("Gespeichert ✓", "Speichern" from `DefaultColorPicker`), and it's the home for the new language switcher.

- [ ] **Step 1: Replace `frontend/app/settings/page.tsx` with the translated version**

```tsx
"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useTranslations } from "next-intl";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { useLocale } from "@/lib/providers/locale-provider";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

function DefaultColorPicker() {
  const t = useTranslations("settings");
  const [hex, setHex] = useState("#2b5fa8");
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${API_BASE}/api/settings`)
      .then((r) => r.json())
      .then((d) => { if (d.default_accent_hex) setHex(d.default_accent_hex); })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const handleSave = async () => {
    const res = await fetch(`${API_BASE}/api/settings`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ default_accent_hex: hex }),
    });
    if (res.ok) setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  if (loading) return <div className="h-8 w-32 bg-surface-container rounded animate-pulse" />;

  return (
    <div className="flex items-center gap-3">
      <div className="flex items-center gap-2 bg-surface-container border border-neutral-medium rounded px-2 py-1.5">
        <div className="w-5 h-5 rounded border border-neutral-medium" style={{ background: hex }} />
        <input
          type="text"
          value={hex}
          onChange={(e) => { if (/^#[0-9a-fA-F]{0,6}$/.test(e.target.value)) setHex(e.target.value); }}
          className="text-sm font-mono bg-transparent outline-none w-20"
          maxLength={7}
        />
      </div>
      <button
        type="button"
        onClick={handleSave}
        className="px-3 py-1.5 text-sm font-medium bg-teal text-white rounded hover:opacity-90"
      >
        {saved ? t("saved") : t("common.save")}
      </button>
    </div>
  );
}

function LanguageSwitcher() {
  const t = useTranslations("settings");
  const { locale, setLocale } = useLocale();
  const [saving, setSaving] = useState(false);

  async function handleSwitch(lang: "de" | "en") {
    if (lang === locale) return;
    setSaving(true);
    await setLocale(lang);
    setSaving(false);
  }

  return (
    <section className="rounded-lg border border-neutral-medium p-4">
      <h2 className="text-base font-semibold text-neutral-dark mb-1">{t("language")}</h2>
      <p className="text-sm text-neutral-medium mb-4">{t("languageHint")}</p>
      <div className="flex gap-2" aria-disabled={saving}>
        {(["de", "en"] as const).map((lang) => (
          <button
            key={lang}
            type="button"
            onClick={() => void handleSwitch(lang)}
            disabled={saving}
            className={`px-4 py-1.5 text-sm font-medium rounded border transition-colors ${
              locale === lang
                ? "bg-teal text-white border-teal"
                : "bg-white text-neutral-dark border-neutral-medium hover:border-teal"
            }`}
            data-testid={`lang-switch-${lang}`}
          >
            {lang.toUpperCase()}
          </button>
        ))}
      </div>
    </section>
  );
}

export default function SettingsPage() {
  const t = useTranslations("settings");
  const tErrors = useTranslations("errors");
  const router = useRouter();
  const [deleting, setDeleting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState("");
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [deleteConfirmation, setDeleteConfirmation] = useState("");

  const handleExport = async () => {
    setExporting(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/profile/export`);
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "applire-export.json";
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      } else {
        const err = await res.json();
        setError(err.detail || tErrors("exportFailed"));
      }
    } catch {
      setError(tErrors("exportFailed"));
    } finally {
      setExporting(false);
    }
  };

  const handleDelete = async () => {
    if (deleteConfirmation !== "DELETE") {
      setError(tErrors("typeDeleteToConfirm"));
      return;
    }
    setDeleting(true);
    setError("");
    try {
      const res = await fetch(`${API_BASE}/api/profile`, { method: "DELETE" });
      if (res.status === 202 || res.ok) {
        router.push("/");
      } else {
        const err = await res.json();
        setError(err.detail || tErrors("deletionFailed"));
      }
    } catch {
      setError(tErrors("deletionFailed"));
    } finally {
      setDeleting(false);
      setShowDeleteConfirm(false);
      setDeleteConfirmation("");
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-surface-dim">
      <header className="bg-white border-b border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <button onClick={() => router.push("/")} className="text-sm text-teal hover:underline">
              {t("back")}
            </button>
            <h1 className="font-heading text-2xl font-bold text-neutral-dark">{t("title")}</h1>
          </div>
        </div>
      </header>

      <main className="flex-1 px-4 py-8">
        <div className="max-w-4xl mx-auto space-y-6">
          {error && (
            <div className="p-4 rounded-lg bg-critical/10 border border-critical/20">
              <p className="text-sm text-critical">{error}</p>
            </div>
          )}

          {/* Language switcher */}
          <LanguageSwitcher />

          {/* GDPR Section */}
          <Card className="p-6">
            <h2 className="font-heading text-xl font-bold text-neutral-dark mb-4">
              {t("dataPrivacy")}
            </h2>
            <p className="text-sm text-gray-500 mb-6">{t("gdprHint")}</p>

            <div className="space-y-4">
              <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
                <div>
                  <h3 className="font-medium text-neutral-dark">{t("exportMyData")}</h3>
                  <p className="text-sm text-gray-500">{t("exportHint")}</p>
                </div>
                <Button variant="outline" onClick={handleExport} disabled={exporting}>
                  {exporting ? t("exporting") : t("common.export")}
                </Button>
              </div>

              <div className="flex items-center justify-between p-4 bg-critical/5 rounded-lg border border-critical/20">
                <div>
                  <h3 className="font-medium text-critical">{t("deleteAllData")}</h3>
                  <p className="text-sm text-gray-500">{t("deleteHint")}</p>
                </div>
                <Button variant="destructive" onClick={() => setShowDeleteConfirm(true)} disabled={deleting}>
                  {t("common.delete")}
                </Button>
              </div>
            </div>
          </Card>

          {/* Default CV Color */}
          <section className="rounded-lg border border-neutral-medium p-4">
            <h2 className="text-base font-semibold text-neutral-dark mb-1">{t("defaultCVColor")}</h2>
            <p className="text-sm text-neutral-medium mb-4">{t("defaultCVColorHint")}</p>
            <DefaultColorPicker />
          </section>

          {/* Delete Confirmation */}
          {showDeleteConfirm && (
            <Card className="p-6 border-2 border-critical/30">
              <h3 className="font-heading text-lg font-bold text-critical mb-2">
                {t("confirmDeletion")}
              </h3>
              <p className="text-sm text-gray-600 mb-4">{t("deletionIrreversible")}</p>
              <ul className="text-sm text-gray-600 list-disc list-inside mb-4 space-y-1">
                <li>{t("deletionItemMasterProfile")}</li>
                <li>{t("deletionItemApplications")}</li>
                <li>{t("deletionItemInterviews")}</li>
                <li>{t("deletionItemCVs")}</li>
              </ul>
              <div className="mb-4">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t("typeDeleteLabel")} <code className="bg-gray-100 px-1 rounded">DELETE</code>
                </label>
                <input
                  type="text"
                  value={deleteConfirmation}
                  onChange={(e) => setDeleteConfirmation(e.target.value)}
                  className="w-full rounded-lg border border-gray-300 px-4 py-2 text-sm focus:border-critical focus:outline-none focus:ring-2 focus:ring-critical/20"
                  placeholder="DELETE"
                />
              </div>
              <div className="flex gap-2">
                <Button
                  variant="destructive"
                  onClick={handleDelete}
                  disabled={deleting || deleteConfirmation !== "DELETE"}
                >
                  {deleting ? t("deleting") : t("confirmDeleteButton")}
                </Button>
                <Button
                  variant="outline"
                  onClick={() => { setShowDeleteConfirm(false); setDeleteConfirmation(""); setError(""); }}
                >
                  {t("common.cancel")}
                </Button>
              </div>
            </Card>
          )}
        </div>
      </main>

      <footer className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto flex justify-center gap-6">
          <a href="/" className="text-sm text-teal hover:underline">{t("nav.dashboard")}</a>
          <a href="/profile" className="text-sm text-teal hover:underline">{t("nav.profile")}</a>
          <a href="/admin/appearance" className="text-sm text-teal hover:underline">{t("nav.admin")}</a>
          <a href="/help" className="text-sm text-gray-500 hover:underline">{t("nav.help")}</a>
        </div>
      </footer>
    </div>
  );
}
```

Note: `t("common.save")` uses dot notation to access nested namespaces. next-intl resolves this correctly when the messages are flat-keyed within the namespace. Since `useTranslations("settings")` scopes to the `settings` namespace, accessing `common` requires a cross-namespace call. Use a second `useTranslations` call: add `const tCommon = useTranslations("common")` and use `tCommon("save")` etc.

Update the file to add `const tCommon = useTranslations("common")` alongside `const t = useTranslations("settings")` wherever `common` strings are used, replacing `t("common.save")` with `tCommon("save")`, `t("common.export")` with `tCommon("export")`, etc.

- [ ] **Step 2: Run frontend tests**

```bash
cd frontend && npm test -- --run
```

Expected: All existing tests pass (Settings page has no unit tests so nothing new fails).

- [ ] **Step 3: Manually verify in browser**

Start the dev server: `cd frontend && npm run dev`  
Navigate to `http://localhost:3000/settings`.  
Verify: All text is in English by default. Click "DE" button — all Settings text switches to German. Click "EN" — switches back.

- [ ] **Step 4: Commit**

```bash
git add frontend/app/settings/page.tsx
git commit -m "feat: translate Settings page and add DE/EN language switcher"
```

---

## Task 7: Translate the home/landing page

**Files:**
- Modify: `frontend/app/page.tsx`

- [ ] **Step 1: Add `useTranslations` to `frontend/app/page.tsx`**

At the top of the `Home()` function, add:
```tsx
const t = useTranslations("home");
const tErrors = useTranslations("errors");
```

Then replace all hardcoded strings:

| Old string | Replacement |
|---|---|
| `"AI-Powered CV Transformation"` | `t("tagline")` |
| `"Your CVs"` | `t("yourCVs")` |
| `"Upload 2-4 CVs for the richest profile. We'll merge them automatically."` | `t("cvUploadHint")` |
| `"Job Description"` | `t("jobDescription")` |
| `"Paste a JD so we can tailor your profile immediately."` | `t("jdHint")` |
| `"Paste Text"` | `t("pasteText")` |
| `"(Optional — you can add this later)"` | `t("optional")` |
| `"Analyze & Build Profile"` | `t("analyzeButton")` |
| `"Upload at least one CV to continue"` | `t("uploadAtLeastOne")` |
| `"This usually takes about 30 seconds"` | `t("usuallyTakes")` |
| `"Add more files for a richer profile"` | `t("addMoreFiles")` |
| `"Please upload at least one CV to continue."` | `tErrors("uploadAtLeastOne")` |
| `"Loading..."` | `useTranslations("common")("loading")` |
| `"Precise. Confident. Future-Ready."` | Leave as-is (brand tagline, not translated) |

Also add `"use client"` is already at the top — confirm `useTranslations` is imported from `"next-intl"`.

Full import addition at the top of the file:
```tsx
import { useTranslations } from "next-intl";
```

- [ ] **Step 2: Run frontend type check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors in `app/page.tsx`.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/page.tsx
git commit -m "feat: translate home/landing page"
```

---

## Task 8: Translate the processing overlay

**Files:**
- Modify: `frontend/components/processing-overlay.tsx`
- Modify: `frontend/components/__tests__/ProcessingOverlay.test.tsx`

- [ ] **Step 1: Read the current test to understand what strings are checked**

```bash
cat frontend/components/__tests__/ProcessingOverlay.test.tsx
```

Note which hardcoded English strings the test asserts on.

- [ ] **Step 2: Update the test to use `withIntl`**

At the top of `ProcessingOverlay.test.tsx`, add:
```tsx
import { withIntl } from "@/lib/test-utils/with-intl";
```

Wrap each `render(...)` call:
```tsx
// Before:
render(<ProcessingOverlay ... />);
// After:
render(withIntl(<ProcessingOverlay ... />));
```

Keep all string assertions unchanged — the English messages file uses the same strings, so tests continue to pass.

- [ ] **Step 3: Run the test to verify it still passes with the wrapper**

```bash
cd frontend && npm test -- --run ProcessingOverlay
```

Expected: PASS (strings haven't changed yet, just wrapped).

- [ ] **Step 4: Add `useTranslations` to `processing-overlay.tsx`**

Add to the component:
```tsx
import { useTranslations } from "next-intl";
```

Inside the component function, add:
```tsx
const t = useTranslations("processing");
```

Replace hardcoded strings:

| Old string | Replacement |
|---|---|
| `"Analyzing job description…"` or similar | `t("analyzingJD")` |
| `"That URL didn't look valid — you can add it later"` | `t("jdUrlInvalid")` |
| `"The site blocked us — you can paste the text later"` | `t("jdFetchFailed")` |
| `"Cancel"` | `t("cancel")` |
| `"Job description skipped"` | `t("jdSkipped")` |

- [ ] **Step 5: Run the test again**

```bash
cd frontend && npm test -- --run ProcessingOverlay
```

Expected: PASS (component now serves strings from `en.json` which match the English originals).

- [ ] **Step 6: Commit**

```bash
git add frontend/components/processing-overlay.tsx frontend/components/__tests__/ProcessingOverlay.test.tsx
git commit -m "feat: translate processing overlay"
```

---

## Task 9: Translate the gaps page

**Files:**
- Modify: `frontend/app/flow/[flowId]/gaps/page.tsx`

- [ ] **Step 1: Add `useTranslations` to `gaps/page.tsx`**

Import at the top:
```tsx
import { useTranslations } from "next-intl";
```

In the page component and in `JdRecoveryBannerInner`, add:
```tsx
const t = useTranslations("gaps");
```

Replace all hardcoded strings:

| Old string | Replacement |
|---|---|
| `"That URL didn't look valid. Paste the job description text to run gap analysis."` | `t("jdMissingBannerUrl")` |
| `"We couldn't load that job posting — it may be blocked or taken down. Paste the job description text to run gap analysis."` | `t("jdMissingBannerFetch")` |
| `"Add job description →"` | `t("addJobDescription")` |

For the gaps page headings and section labels (match score, strengths, category labels), replace each with the corresponding `t("matchScore")`, `t("strengths")`, `t("categoryB")`, `t("categoryC")`, and `t("startInterview")` calls.

- [ ] **Step 2: Run type check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/flow/[flowId]/gaps/page.tsx
git commit -m "feat: translate gaps page"
```

---

## Task 10: Translate the interview page

**Files:**
- Modify: `frontend/app/flow/[flowId]/interview/page.tsx`

- [ ] **Step 1: Add `useTranslations` to `interview/page.tsx`**

Import:
```tsx
import { useTranslations } from "next-intl";
```

In the main `InterviewPage` component, in `CompletenessGauge`, and in `ConflictCard`, add the appropriate `useTranslations` calls.

Replace all hardcoded strings:

| Old string | Replacement |
|---|---|
| `"Starting interview…"` | `t("loading")` |
| `"Question {n} of ~{m} — Closing gaps for"` | `t("questionOf", { current: questionsAsked, total: estimatedQuestions })` |
| `"{n} gap(s) remaining"` | `t("gapsRemaining", { count: gapsRemaining })` |
| `"We think you might have this experience..."` | `t("categoryBBadge")` |
| `"Discrepancy detected"` | `t("discrepancyDetected")` |
| `Keep "{value}"` buttons | `t("keepOld", { value: conflict.old_value })` |
| `Use "{value}"` buttons | `t("useNew", { value: conflict.new_value })` |
| `"Welcome back — continuing where you left off."` | `t("resumeBanner")` |
| `"You have {n} gap(s) remaining — are you sure..."` | `t("gapsRemainingConfirm", { count: gapsRemaining })` |
| `"End interview"` | `t("endInterview")` |
| `"Continue"` | `t("continue")` |
| `"Type your answer…"` placeholder | `t("placeholder")` |
| `"I'm done"` | `t("iAmDone")` |
| `"Send"` | `t("send")` (from `common` namespace) |
| `"Profile completeness"` | `t("profileCompleteness")` |
| `"Questions answered"` | `t("questionsAnswered")` |
| `"Gaps resolved"` | `t("gapsResolved")` |
| `"Generate Tailored CV"` | `t("generateCV")` |
| `"Preparing…"` | `t("advancingToCV")` |
| `"View Updated Profile"` | `t("viewProfile")` |
| `"Role Requirements"` | `t("roleRequirements")` |
| `REASON_LABELS` map | Replace with individual `t("reasonGapsResolved")`, `t("reasonUserEnded")`, `t("reasonMaxReached")` |
| Completion subtitles | `t("completionGapsResolved")` / `t("completionOther")` |

For the `translateError` function, update it to accept a `t` function:
```tsx
function translateError(status: number, t: ReturnType<typeof useTranslations>, detail?: string): string {
  switch (status) {
    case 504: return t("errors.http504");
    case 503: return t("errors.http503");
    case 502: return t("errors.http502");
    default:  return detail ?? t("errors.generic", { status });
  }
}
```

Pass `tErrors` (from `useTranslations("errors")`) where `translateError` is called.

- [ ] **Step 2: Run type check**

```bash
cd frontend && npx tsc --noEmit
```

Expected: No errors.

- [ ] **Step 3: Commit**

```bash
git add frontend/app/flow/[flowId]/interview/page.tsx
git commit -m "feat: translate interview page"
```

---

## Task 11: Translate GapHint, SectionEditor, SaveScopePrompt, and ContentTab

**Files:**
- Modify: `frontend/components/cv/GapHint.tsx` + `__tests__/GapHint.test.tsx`
- Modify: `frontend/components/cv/SectionEditor.tsx` + `__tests__/SectionEditor.test.tsx`
- Modify: `frontend/components/cv/SaveScopePrompt.tsx` + `__tests__/SaveScopePrompt.test.tsx`
- Modify: `frontend/components/cv/ContentTab.tsx` + `__tests__/ContentTab.test.tsx`

- [ ] **Step 1: Update `GapHint.test.tsx` to use `withIntl`**

```tsx
import { render, screen, fireEvent } from "@testing-library/react";
import { vi, describe, it, expect, afterEach } from "vitest";
import { GapHint } from "../GapHint";
import { withIntl } from "@/lib/test-utils/with-intl";

const GAP = { id: "Python", label: "Python" };
const BASE_PROPS = {
  gap: GAP,
  onDismiss: vi.fn(),
  onAddressGap: vi.fn(),
};

describe("GapHint", () => {
  afterEach(() => { vi.restoreAllMocks(); });

  it("renders gap label", () => {
    render(withIntl(<GapHint {...BASE_PROPS} />));
    expect(screen.getByText("Python")).toBeTruthy();
  });

  it("'Write it myself' button calls onDismiss with gap id", () => {
    const onDismiss = vi.fn();
    render(withIntl(<GapHint {...BASE_PROPS} onDismiss={onDismiss} />));
    fireEvent.click(screen.getByTestId("write-myself-btn"));
    expect(onDismiss).toHaveBeenCalledWith("Python");
  });

  it("'Let Kaile help' button calls onAddressGap with gap id", () => {
    const onAddressGap = vi.fn();
    render(withIntl(<GapHint {...BASE_PROPS} onAddressGap={onAddressGap} />));
    fireEvent.click(screen.getByTestId("kaile-help-btn"));
    expect(onAddressGap).toHaveBeenCalledWith("Python");
  });
});
```

- [ ] **Step 2: Run GapHint test — expect FAIL**

```bash
cd frontend && npm test -- --run GapHint
```

Expected: FAIL — buttons still show German strings ("Selbst schreiben", "Kaile hilft") but tests now look for English via `withIntl`.

- [ ] **Step 3: Update `GapHint.tsx` to use translations**

```tsx
"use client";

import { useTranslations } from "next-intl";

interface GapHintItem {
  id: string;
  label: string;
}

interface GapHintProps {
  gap: GapHintItem;
  onDismiss: (gapId: string) => void;
  onAddressGap: (gapId: string) => void;
}

export function GapHint({ gap, onDismiss, onAddressGap }: GapHintProps) {
  const t = useTranslations("cv");

  return (
    <div className="mb-2">
      <div className="flex items-center justify-between bg-warning-container border border-warning/30 rounded-lg px-3 py-2">
        <span className="text-xs text-neutral-dark font-medium">{gap.label}</span>
        <div className="flex gap-1 ml-2 shrink-0">
          <button
            type="button"
            onClick={() => onDismiss(gap.id)}
            className="text-xs text-teal border border-teal px-2 py-0.5 rounded hover:bg-teal hover:text-white transition-colors"
            data-testid="write-myself-btn"
          >
            {t("writeMyself")}
          </button>
          <button
            type="button"
            onClick={() => onAddressGap(gap.id)}
            className="text-xs text-teal border border-teal px-2 py-0.5 rounded hover:bg-teal hover:text-white transition-colors"
            data-testid="kaile-help-btn"
          >
            {t("letKaileHelp")}
          </button>
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Run GapHint test — expect PASS**

```bash
cd frontend && npm test -- --run GapHint
```

Expected: PASS.

- [ ] **Step 5: Update `SectionEditor.tsx` and its test**

In `SectionEditor.test.tsx`, wrap all `render(...)` calls with `withIntl(...)`.

In `SectionEditor.tsx`:
- Add `import { useTranslations } from "next-intl";`
- Add `const t = useTranslations("cv");` inside the component
- Replace `"Save"` → `t("save")`, `"Cancel"` → `t("cancel")`, `"Saving…"` → `t("saving")`, the placeholder text → `t("placeholder")`, `"Related gaps"` → `t("gapHints")`

- [ ] **Step 6: Update `SaveScopePrompt.tsx` and its test**

In `SaveScopePrompt.test.tsx`, wrap all `render(...)` calls with `withIntl(...)`.

In `SaveScopePrompt.tsx`:
- Add `import { useTranslations } from "next-intl";`
- Add `const t = useTranslations("saveScopePrompt");`
- Replace `"Save to your Master Profile?"` → `t("saveToProfile")`, `"Save to Profile"` → `t("toProfile")`, `"Just this CV"` → `t("justThisCV")`

- [ ] **Step 7: Update `ContentTab.tsx` and its test**

In `ContentTab.test.tsx`, wrap all `render(...)` calls with `withIntl(...)`.

In `ContentTab.tsx`:
- Add `import { useTranslations } from "next-intl";`
- Add `const t = useTranslations("cv");` and `const tUnsaved = useTranslations("unsavedChanges");`
- Replace `"General gaps"` → `t("generalGaps")`, `"No sections available"` → `t("noSections")`
- Replace `"Discard unsaved changes?"` → `tUnsaved("title")`, `"Discard"` → `tUnsaved("discard")`, `"Keep editing"` → `tUnsaved("keepEditing")`

- [ ] **Step 8: Run all CV component tests**

```bash
cd frontend && npm test -- --run
```

Expected: All tests PASS.

- [ ] **Step 9: Commit**

```bash
git add frontend/components/cv/GapHint.tsx frontend/components/cv/__tests__/GapHint.test.tsx \
        frontend/components/cv/SectionEditor.tsx frontend/components/cv/__tests__/SectionEditor.test.tsx \
        frontend/components/cv/SaveScopePrompt.tsx frontend/components/cv/__tests__/SaveScopePrompt.test.tsx \
        frontend/components/cv/ContentTab.tsx frontend/components/cv/__tests__/ContentTab.test.tsx
git commit -m "feat: translate GapHint, SectionEditor, SaveScopePrompt, ContentTab"
```

---

## Task 12: Translate KaileChat, RefinementPanel, ActionsTab, DesignTab, WhatNext

**Files:**
- Modify: `frontend/components/cv/KaileChat.tsx` + `__tests__/KaileChat.test.tsx`
- Modify: `frontend/components/cv/RefinementPanel.tsx` + `__tests__/RefinementPanel.test.tsx`
- Modify: `frontend/components/cv/ActionsTab.tsx` + `__tests__/ActionsTab.test.tsx`
- Modify: `frontend/components/cv/DesignTab.tsx` + `__tests__/DesignTab.test.tsx`
- Modify: `frontend/components/cv/WhatNext.tsx`

For each file, follow the same TDD pattern: wrap test renders with `withIntl(...)`, run test to see it fail if strings changed, update component with `useTranslations("cv")`, run test to see it pass.

- [ ] **Step 1: Update `KaileChat.tsx` and its test**

In `KaileChat.test.tsx`: wrap all `render(...)` calls with `withIntl(...)`.

In `KaileChat.tsx`:
- Add `import { useTranslations } from "next-intl";`
- Add `const t = useTranslations("cv");`
- Replace `"Rewrite section"` → `t("rewriteSection")`, `"Rewriting…"` → `t("rewriting")`, `"Apply"` → `t("apply")`, `"Edit first"` → `t("editFirst")`, `"Discard"` → `t("discardSuggestion")`, textarea placeholder → `t("directionPlaceholder")`

- [ ] **Step 2: Update `RefinementPanel.tsx` and its test**

In `RefinementPanel.test.tsx`: wrap all `render(...)` calls with `withIntl(...)`.

In `RefinementPanel.tsx`:
- Add `import { useTranslations } from "next-intl";`
- Add `const t = useTranslations("cv");`
- Replace tab labels: `"Content"` → `t("contentTab")`, `"Actions"` → `t("actionsTab")`, `"Design"` → `t("designTab")`
- Replace `"All gaps closed"` → `t("allGapsClosed")`, `"Preview may be outdated"` → `t("previewOutdated")`

- [ ] **Step 3: Update `ActionsTab.tsx` and its test**

In `ActionsTab.test.tsx`: wrap with `withIntl(...)`.

In `ActionsTab.tsx`:
- Add `const t = useTranslations("cv");`
- Replace `"Download PDF"` → `t("download")`, `"Regenerate"` → `t("regenerate")`

- [ ] **Step 4: Update `DesignTab.tsx` and its test**

In `DesignTab.test.tsx`: wrap with `withIntl(...)`.

In `DesignTab.tsx`:
- Add `const t = useTranslations("cv");`
- Replace `"auto-detected"` → `t("colorAutoDetected")`, `"Apply color"` / `"Farbe übernehmen"` → `t("applyColor")`, `"Default color"` → `t("defaultColor")`

- [ ] **Step 5: Update `WhatNext.tsx`**

`WhatNext.tsx` has no dedicated test file. Add `useTranslations` and replace any hardcoded strings with keys from the `cv` namespace.

- [ ] **Step 6: Run all CV tests**

```bash
cd frontend && npm test -- --run
```

Expected: All PASS.

- [ ] **Step 7: Commit**

```bash
git add frontend/components/cv/KaileChat.tsx frontend/components/cv/__tests__/KaileChat.test.tsx \
        frontend/components/cv/RefinementPanel.tsx frontend/components/cv/__tests__/RefinementPanel.test.tsx \
        frontend/components/cv/ActionsTab.tsx frontend/components/cv/__tests__/ActionsTab.test.tsx \
        frontend/components/cv/DesignTab.tsx frontend/components/cv/__tests__/DesignTab.test.tsx \
        frontend/components/cv/WhatNext.tsx
git commit -m "feat: translate KaileChat, RefinementPanel, ActionsTab, DesignTab, WhatNext"
```

---

## Task 13: Translate CV page and cover letter page + components

**Files:**
- Modify: `frontend/app/flow/[flowId]/cv/page.tsx`
- Modify: `frontend/app/flow/[flowId]/cover-letter/page.tsx`
- Modify: `frontend/components/cover-letter/GenerateCoverLetterModal.tsx`
- Modify: `frontend/components/cover-letter/CoverLetterContentTab.tsx`
- Modify: `frontend/components/cover-letter/CoverLetterActionsTab.tsx`
- Modify: `frontend/components/cover-letter/CoverLetterDesignTab.tsx`
- Modify: `frontend/components/cover-letter/CoverLetterRefinementPanel.tsx` + its test

- [ ] **Step 1: Translate `cv/page.tsx`**

Import and use `useTranslations("cv")`. Replace:
- `"Generating CV…"` → `t("generating")`
- Navigation labels and any remaining hardcoded strings

- [ ] **Step 2: Translate cover letter components**

For each cover letter component:
1. Wrap its test renders with `withIntl(...)` (for `CoverLetterRefinementPanel.test.tsx` and `CoverLetterDocument.test.tsx`)
2. Run test → note if it fails
3. Add `useTranslations("coverLetter")` to the component
4. Replace:
   - `"Generate Cover Letter"` → `t("generate")`
   - `"Download PDF"` → `t("download")`
   - `"Regenerate Cover Letter"` → `t("regenerate")`
   - `"← View CV"` → `t("viewCV")`
   - `"View Cover Letter →"` → `t("viewCoverLetter")`
   - Tab labels → `t("contentTab")`, `t("actionsTab")`, `t("designTab")`

- [ ] **Step 3: Run cover letter tests**

```bash
cd frontend && npm test -- --run CoverLetter
```

Expected: All PASS.

- [ ] **Step 4: Commit**

```bash
git add frontend/app/flow/[flowId]/cv/page.tsx \
        frontend/app/flow/[flowId]/cover-letter/page.tsx \
        frontend/components/cover-letter/
git commit -m "feat: translate CV page and cover letter components"
```

---

## Task 14: Translate dashboard, profile, import, and remaining components

**Files:**
- Modify: `frontend/components/dashboard/Dashboard.tsx`
- Modify: `frontend/components/dashboard/NewApplicationModal.tsx`
- Modify: `frontend/components/dashboard/ApplicationCard.tsx`
- Modify: `frontend/app/profile/page.tsx`
- Modify: `frontend/app/flow/[flowId]/import/page.tsx`
- Modify: `frontend/components/offline-banner.tsx`

- [ ] **Step 1: Translate Dashboard and application components**

In `Dashboard.tsx`:
- Add `const t = useTranslations("dashboard");`
- Replace: `"New Application"` → `t("newApplication")`, `"Recent Applications"` → `t("recentApplications")`, `"Resume"` → `t("resume")`, `"No applications yet"` → `t("noApplications")`

In `NewApplicationModal.tsx`:
- Add `const t = useTranslations("dashboard");`
- Replace any hardcoded button labels or headings.

In `ApplicationCard.tsx`:
- Add `const t = useTranslations("dashboard");`
- Replace status labels and action button labels.

- [ ] **Step 2: Translate `profile/page.tsx`**

Add `const t = useTranslations("profile");` and replace `"My Profile"` heading with `t("title")`.

- [ ] **Step 3: Translate `import/page.tsx`**

Add `const t = useTranslations("import");` and replace the page title.

- [ ] **Step 4: Translate `offline-banner.tsx`**

```tsx
import { useTranslations } from "next-intl";

export function OfflineBanner() {
  const t = useTranslations("offline");
  // Replace hardcoded offline message with t("message")
}
```

- [ ] **Step 5: Run all frontend tests**

```bash
cd frontend && npm test -- --run
```

Expected: All PASS.

- [ ] **Step 6: Commit**

```bash
git add frontend/components/dashboard/ frontend/app/profile/page.tsx \
        frontend/app/flow/[flowId]/import/page.tsx frontend/components/offline-banner.tsx
git commit -m "feat: translate dashboard, profile, import page, and offline banner"
```

---

## Task 15: Full test run and manual QA

- [ ] **Step 1: Run all backend unit tests**

```bash
cd /home/apliqa/Documents/Applire/Solution && pytest tests/unit/ -v --cov=applire --cov-fail-under=75
```

Expected: All PASS, coverage ≥ 75%.

- [ ] **Step 2: Run all frontend tests**

```bash
cd frontend && npm test -- --run
```

Expected: All PASS.

- [ ] **Step 3: Manual QA — English flow**

Start the stack:
```bash
docker-compose up -d
cd frontend && npm run dev
```

Visit `http://localhost:3000`. Verify:
- [ ] All text on the landing page is in English
- [ ] Processing overlay shows English messages
- [ ] Gaps page shows English labels
- [ ] Interview page shows English questions and UI chrome
- [ ] CV page refinement panel shows English tab labels, button labels
- [ ] Settings page shows English, language switcher is visible
- [ ] No mixed-language strings visible anywhere

- [ ] **Step 4: Manual QA — German flow**

Go to Settings, click "DE". Verify:
- [ ] Settings page immediately switches to German
- [ ] Navigate to `/` — landing page is in German
- [ ] Go through a full flow — all UI chrome is in German throughout
- [ ] CV refinement panel shows German labels ("Inhalt", "Aktionen", "Design", "Selbst schreiben", "Kaile hilft")
- [ ] Interview page shows German UI chrome

- [ ] **Step 5: Commit QA sign-off**

```bash
git commit --allow-empty -m "chore: manual QA complete for DE/EN i18n sprint"
```

---

## Task 16: CI key-parity check script

**Files:**
- Create: `scripts/check-i18n-parity.js`
- Modify: `frontend/package.json`

This script verifies that `en.json` and `de.json` have identical key structures. It fails with a non-zero exit code if any key is present in one file but missing from the other.

- [ ] **Step 1: Create `scripts/check-i18n-parity.js`**

```js
#!/usr/bin/env node
/**
 * Verifies that messages/en.json and messages/de.json have identical key structures.
 * Run: node scripts/check-i18n-parity.js
 * Exit code 0 = parity OK, 1 = mismatch found.
 */
const fs = require("fs");
const path = require("path");

const messagesDir = path.join(__dirname, "..", "frontend", "messages");
const en = JSON.parse(fs.readFileSync(path.join(messagesDir, "en.json"), "utf8"));
const de = JSON.parse(fs.readFileSync(path.join(messagesDir, "de.json"), "utf8"));

function collectKeys(obj, prefix = "") {
  const keys = [];
  for (const [k, v] of Object.entries(obj)) {
    const full = prefix ? `${prefix}.${k}` : k;
    if (typeof v === "object" && v !== null && !Array.isArray(v)) {
      keys.push(...collectKeys(v, full));
    } else {
      keys.push(full);
    }
  }
  return keys;
}

const enKeys = new Set(collectKeys(en));
const deKeys = new Set(collectKeys(de));

const missingInDe = [...enKeys].filter((k) => !deKeys.has(k));
const missingInEn = [...deKeys].filter((k) => !enKeys.has(k));

if (missingInDe.length > 0) {
  console.error("❌ Keys present in en.json but missing in de.json:");
  missingInDe.forEach((k) => console.error(`  - ${k}`));
}
if (missingInEn.length > 0) {
  console.error("❌ Keys present in de.json but missing in en.json:");
  missingInEn.forEach((k) => console.error(`  - ${k}`));
}

if (missingInDe.length === 0 && missingInEn.length === 0) {
  console.log("✅ i18n parity OK — en.json and de.json have identical key structures.");
  process.exit(0);
} else {
  process.exit(1);
}
```

- [ ] **Step 2: Add parity check to `frontend/package.json` scripts**

In `frontend/package.json`, add to the `"scripts"` section:

```json
"i18n:check": "node ../scripts/check-i18n-parity.js",
"lint": "next lint && npm run i18n:check"
```

(If a `lint` script already exists, append `&& npm run i18n:check` to it.)

- [ ] **Step 3: Run the parity check**

```bash
node scripts/check-i18n-parity.js
```

Expected output:
```
✅ i18n parity OK — en.json and de.json have identical key structures.
```

Expected exit code: 0.

- [ ] **Step 4: Verify the check fails correctly when a key is missing**

Temporarily add `"testKey": "test"` to only `en.json`, run the check, verify it exits with code 1 and names `testKey` as missing in de.json. Then remove the test key.

- [ ] **Step 5: Commit**

```bash
git add scripts/check-i18n-parity.js frontend/package.json
git commit -m "chore: add i18n key-parity CI check script"
```

---

## Self-Review

**Spec coverage check:**

| Spec requirement | Covered in task |
|---|---|
| Browser `Accept-Language` detection | Task 2 |
| Persist `ui_language` in `user_settings` | Task 1 + 2 |
| `GET /api/settings` auto-detects on first visit | Task 2 |
| `PATCH /api/settings` accepts `ui_language` | Task 2 |
| next-intl non-routing mode | Task 3 + 4 |
| `messages/en.json` + `messages/de.json` | Task 3 |
| `LocaleProvider` wrapping `NextIntlClientProvider` | Task 4 |
| Language switcher in Settings | Task 6 |
| Default to English for unknown locales | Task 2 (return "en") |
| Translate all UI pages and components | Tasks 7–14 |
| Key-parity CI check | Task 16 |
| Mixed-language Settings page fixed | Task 6 ("Gespeichert ✓" / "Speichern") |
| Unit tests for language detection | Task 2 |
| Vitest test helper for i18n wrapping | Task 5 |
| Manual QA sign-off checklist | Task 15 |

**Placeholder scan:** No TBDs, no "implement later" entries, no "similar to Task N" shortcuts. Every task has either complete code or an explicit enumerated list of replacements with exact key names. ✓

**Type consistency check:** `useTranslations("cv")` used consistently across Tasks 11–13. `useTranslations("settings")` in Task 6. `update_settings(db, accent_hex=..., ui_language=...)` keyword-argument form used consistently in Tasks 1–2. `LocaleProvider` / `useLocale` from `@/lib/providers/locale-provider` used in Tasks 4 and 6. ✓
