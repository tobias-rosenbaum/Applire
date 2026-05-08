---
name: Sprint 14 — Profile Photo Management
description: Design spec for CV profile photo upload, storage, rendering, and GDPR handling
type: project
---

# Sprint 14 — Profile Photo Management

**Date:** 2026-04-07
**Status:** Approved
**Author:** Brainstormed with Tobias Rosenbaum

---

## Problem Statement

German CVs (Lebenslauf) conventionally include a professional headshot. Applire already has `PersonalInfo.photo_url` in the schema, but it is entirely orphaned — never set, never merged, never rendered in any template. Users have no way to add a photo to their CV today.

This sprint wires up the complete photo lifecycle: upload → store → embed → render.

---

## Scope

**In scope:**
- Direct photo upload by the user (JPEG, PNG, WebP, ≤5 MB)
- Profile sidebar management UI (view, replace, delete)
- CV generation step prompt for first-time users without a photo
- Base64 inline embedding into both CV templates
- GDPR-compliant explicit consent capture and storage
- Photo deletion on GDPR erasure
- `show_photo` flag in `TailoredCVData` as country-aware rendering hook

**Out of scope (deferred):**
- Automatic photo extraction from uploaded CV PDFs
- Country lookup table for `show_photo` (flag defaults to `True` for all DACH jobs; table is a Sprint 15+ concern)
- Photo crop / resize UI (accept as-is; rely on CSS `object-fit: cover`)

---

## User Journey Updates

### Marcus (New Customer) — Updated Step 3 (CV Generation)

After completing the interview and before CV generation, a new optional step is inserted when the user has no profile photo:

> **"Add a profile photo?"**
> German employers typically expect a professional photo on your CV. It's optional but recommended for DACH applications.
> [📷 Upload photo — saved to your profile] [⏭ Skip for now]

If the user already has a photo on their profile, this step is replaced with a confirmation banner ("Profile photo ✓ — will be included in your CV") and a "Change photo ↗" link.

### Emma (Returning Power User) — Profile Sidebar

Emma manages her photo from Profile → Photo. She sees her current photo thumbnail, an upload date, and Replace / Delete actions. No re-consent required on Replace (existing consent covers re-uploads; consent_at is refreshed).

### Priya (International Relocator) — Addressed Pain Point

Priya's persona explicitly lists "The photo question — Should she include one? What kind?" as a pain point. The CV generation step copy addresses this directly: *"German employers typically expect a professional photo on your CV."* This is the first in-product cultural guidance for Priya on photos.

---

## Epics and User Stories

### Epic: Profile Photo Management

**US-14-01 — Upload a profile photo**
> As a user, I want to upload a professional photo so it appears on my generated CV.

Acceptance criteria:
- `POST /api/profile/photo` accepts JPEG, PNG, WebP up to 5 MB
- File is validated (format + size); helpful error returned if invalid
- Consent checkbox must be checked before upload button activates
- `personal_info.photo_url` is set in the master profile after successful upload
- `user.photo_consent = True`, `user.photo_consent_at = now()` are persisted
- Frontend shows the uploaded photo thumbnail immediately after upload

**US-14-02 — Replace or delete profile photo**
> As a user, I want to replace or delete my profile photo so I stay in control of my data.

Acceptance criteria:
- Replace: `POST /api/profile/photo` again — overwrites file at `photos/{user_id}.jpg`, refreshes `photo_consent_at`
- Delete: `DELETE /api/profile/photo` — removes file from storage, clears `photo_url`, sets `photo_consent = False`
- After deletion, the profile sidebar returns to the empty state

**US-14-03 — Photo appears on generated CV**
> As a user, when I generate a CV for a DACH role and have a profile photo, I want it to appear in the CV output.

Acceptance criteria:
- CV generation service reads photo bytes from storage, converts to base64 data URI
- Both `lebenslauf.html.j2` and `modern_swiss.html.j2` render the photo when `show_photo = True` and `photo_url` is set
- `show_photo` is `True` by default for all DACH job locations
- CV preview (srcDoc iframe) correctly displays the photo
- Generated PDF contains the photo

**US-14-04 — First-time photo prompt in CV generation flow**
> As a first-time user without a photo, I want to be prompted to add one during CV generation so I don't miss the convention by accident.

Acceptance criteria:
- Photo prompt step is shown only when `personal_info.photo_url` is null
- Step is skipped (shows confirmation banner) when photo already exists
- Skipping continues the flow without interruption
- "You can add a photo later in Profile → Photo" hint is shown on skip

**US-14-05 — GDPR: photo included in data erasure**
> As a user exercising my right to erasure, I want my profile photo deleted as part of the full account deletion.

Acceptance criteria:
- `DELETE /api/profile` erasure flow deletes the photo file from storage
- `photo_consent` and `photo_consent_at` are cleared with the user record
- Storage deletion failure is non-blocking (logged, will be reaped by retention worker)

---

## Architecture Decision: ADR-021

**Title:** Profile Photo Storage and Rendering Strategy

**Context:** `PersonalInfo.photo_url` exists but is unused. Photos are GDPR special category data (Art. 9) requiring explicit consent. The CV rendering pipeline uses Playwright headless Chromium to render Jinja2 HTML templates into PDFs.

**Decision:**
1. Store photos via existing `StorageProvider` at path `photos/{user_id}.jpg`. One photo per user; re-upload overwrites.
2. Add `photo_consent: bool` and `photo_consent_at: datetime | None` to the `users` table. Consent is captured inline at upload time via a checkbox in the UI.
3. Embed photos as base64 data URIs in Jinja2 templates at CV generation time. The generation service reads the photo bytes, converts them, and passes the data URI as a template variable. This avoids any HTTP dependency during Playwright rendering.
4. Add `show_photo: bool` to `TailoredCVData`. Defaults to `True` for DACH job locations. Templates render the photo only when both `show_photo` is `True` and a photo is present. This field is the hook for future country-aware cultural intelligence.
5. Photo is excluded from the `personal_info` completeness score — it is genuinely optional.

**Consequences:**
- Positive: No changes to StorageProvider interface; base64 approach is zero-dependency for Playwright.
- Positive: `show_photo` flag future-proofs the rendering layer for European expansion.
- Positive: Consent is trackable and auditable per user.
- Negative: Base64 images inflate the HTML string size (~50–100 KB for a typical headshot). Acceptable for CV use; preview srcDoc is already large.
- Negative: One photo per user means no per-CV photo variation. Acceptable for MVP.

---

## Data Model Changes

### StorageProvider extension (`backend/applire/storage/base.py`)
Add `read(file_path: str) -> bytes` abstract method. Required by the CV generation service to load photo bytes for base64 encoding. Implement in `local.py` (read from filesystem path).

```python
@abstractmethod
async def read(self, file_path: str) -> bytes:
    """Return the raw bytes of the file at *file_path*. Raises FileNotFoundError if absent."""
```

### Alembic migration (new)
```sql
ALTER TABLE users ADD COLUMN photo_consent BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE users ADD COLUMN photo_consent_at TIMESTAMPTZ NULL;
```

### PersonalInfo (no schema change needed)
`photo_url: str | None` already exists in `backend/applire/schemas/profile.py:26`. It will now be populated by the upload endpoint.

### Merge service update (`backend/applire/services/profile/merge.py`)
Add `photo_url` to the gap-fill attributes list (line ~272). Rule: fill if empty, never overwrite an existing photo URL with an incoming one (photo is user-managed, not LLM-extracted).

### TailoredCVData (new field)
```python
show_photo: bool = True
```
Set by the CV generation service based on `job.location` country code. DACH countries (`DE`, `AT`, `CH`) → `True`. All others → `False` until the country table is built.

---

## API Design

### `POST /api/profile/photo`
- **Auth:** required
- **Body:** `multipart/form-data` — `file: UploadFile`, `consent: bool`
- **Validation:** JPEG/PNG/WebP only; ≤5 MB; `consent` must be `True` **OR** `user.photo_consent` already `True` (Replace path — no re-consent needed)
- **Response 200:** `{ "photo_url": "photos/abc123.jpg", "consent_at": "2026-04-07T..." }`
- **Response 400:** format/size/consent errors with helpful messages
- **Side effects:** saves file, sets `personal_info.photo_url`, sets `user.photo_consent = True`, refreshes `photo_consent_at`
- **Replace behaviour:** frontend sends `consent=True` implicitly on Replace (user already consented; the Replace button itself signals intent). The API treats both first-upload and replace identically.

### `DELETE /api/profile/photo`
- **Auth:** required
- **Response 204:** no body
- **Side effects:** deletes file from storage, clears `personal_info.photo_url`, sets `user.photo_consent = False`

### `GET /api/profile/photo`
- **Auth:** required
- **Response 200:** raw image bytes with correct `Content-Type`
- **Response 404:** no photo on file
- **Purpose:** GDPR data portability; not used in CV rendering pipeline

---

## Frontend Components

### `PhotoManager` (new — `frontend/components/profile/PhotoManager.tsx`)
- Empty state: dashed upload dropzone + consent checkbox + disabled upload button (activates on consent tick)
- Filled state: photo thumbnail, filename, upload date, Replace + Delete buttons
- Sits in the Profile sidebar as its own section between Personal Info and Experience

### `PhotoPromptStep` (new — `frontend/components/cv/PhotoPromptStep.tsx`)
- Shown in CV generation wizard when `profile.personal_info.photo_url` is null and job is DACH
- Two choices: Upload (opens inline upload flow) or Skip
- On skip: flow continues, photo omitted from CV
- On upload: same `PhotoManager` upload flow inline; on success continues to next step

---

## CV Template Changes

### `lebenslauf.html.j2`
Add photo block in the header, top-right position (classic German Lebenslauf convention):
```html
{% if show_photo and cv.contact.photo_url %}
<div class="header-photo">
  <img src="{{ cv.contact.photo_url }}" alt="Bewerbungsfoto"
       style="width:45mm; height:55mm; object-fit:cover; object-position:center top;">
</div>
{% endif %}
```
`photo_url` will contain the base64 data URI at render time.

### `modern_swiss.html.j2`
Add circular avatar in the header (top-right):
```html
{% if show_photo and cv.contact.photo_url %}
<div class="header-avatar">
  <img src="{{ cv.contact.photo_url }}" alt="Profile photo"
       style="width:36mm; height:36mm; border-radius:50%; object-fit:cover; object-position:center top;">
</div>
{% endif %}
```

---

## GDPR

| Requirement | Implementation |
|---|---|
| Art. 9(2)(a) explicit consent | `consent` boolean required at upload; stored as `photo_consent + photo_consent_at` on `users` table |
| Art. 17 right to erasure | `DELETE /api/profile` erasure flow deletes photo file; consent fields cleared with user record |
| Art. 25 privacy by design | Photo excluded from completeness score; optional everywhere; clear delete path |
| Retention | Photo TTL = master profile TTL (730d inactivity). Deleted on GDPR erasure. |

---

## Testing Strategy

### Unit tests
- `POST /api/profile/photo` — valid upload, format rejection, size rejection, missing consent
- `DELETE /api/profile/photo` — clears URL and consent; storage delete called
- CV generation: photo present → base64 injected; photo absent → no img tag rendered; `show_photo=False` → no img tag even if photo present
- Merge: `photo_url` gap-fill (empty → filled); no overwrite (existing → unchanged)

### E2E tests
- Upload photo via Profile sidebar → CV preview shows photo
- Delete photo → CV preview shows no photo
- First-time generation prompt → skip → CV generates without photo
- GDPR erasure → photo file deleted from storage

---

## Open Questions

| # | Question | Status |
|---|---|---|
| 1 | Country lookup table for `show_photo` (Europe beyond DACH)? | Deferred to Sprint 15+ |
| 2 | Photo extraction from uploaded CV PDFs? | Deferred to Sprint 15 |
| 3 | Photo crop/resize UI? | Deferred; CSS `object-fit` handles most cases |
| 4 | Per-CV photo variation (different photo per application)? | Deferred; one photo per user for MVP |
