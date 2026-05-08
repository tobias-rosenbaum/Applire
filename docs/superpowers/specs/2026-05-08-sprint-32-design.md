# Sprint-32 Design Spec
**Date:** 2026-05-08  
**Scope:** applire-core frontend + one minor backend addition  
**Items:** Sidebar logo, sidebar footer, profile upload page overhaul

---

## 1. Sidebar — Logo

**Change:** Replace the gradient placeholder box (`view_cozy` icon) with the real Applire icon.

- Copy `Icons/applire_icon.png` (repo root) into `frontend/public/applire-icon.png`
- In `AppSidebar.tsx`, replace the `<div>` gradient block with `<img src="/applire-icon.png" alt="Applire" className="w-[34px] h-[34px] rounded-[9px] object-contain" />`
- The "Applire" wordmark `<span>` next to it remains unchanged

---

## 2. Sidebar — Footer

**Change:** Remove the "Hilfe & Support" help button. Replace with a static version string.

- Remove the `<button onClick={() => router.push("/help")} ...>` block entirely
- Replace with: `<p className="text-[10px] text-center text-outline-variant">{process.env.NEXT_PUBLIC_APP_VERSION}</p>`
- In `next.config.ts`, add `env: { NEXT_PUBLIC_APP_VERSION: process.env.npm_package_version ?? "dev" }` so the version is read from `package.json` at build time
- Remove the `t("help")` translation key usage (key can stay in messages files, just unused)

---

## 3. Sidebar — New Nav Item

**Change:** Add "Profil aktualisieren" as a nav entry.

- Add `{ key: "import", href: "/profile/upload", icon: "upload_file" }` to `NAV_ITEMS` in `AppSidebar.tsx`, positioned between `profile` and `documents`
- Extend the `key` union type accordingly
- Add translation keys:
  - `de.json` → `shell.import`: `"Profil aktualisieren"`
  - `en.json` → `shell.import`: `"Update Profile"`

---

## 4. ProfileImportView — Shared Component

**New file:** `frontend/components/profile/ProfileImportView.tsx`

### Props
```ts
interface ProfileImportViewProps {
  flowId?: string; // present when used as flow fallback
}
```

### Layout
Two-column grid (`grid-cols-1 lg:grid-cols-[1fr_320px]`):

**Left column:**
1. **Glass dropzone** — wraps the existing `Dropzone` component. Accepts `.pdf,.docx,.doc,.zip`. Styled with `bg-white/90 backdrop-blur-md border-2 border-dashed border-outline-variant rounded-xl` and `shadow-[0_0_40px_-10px_rgba(0,51,153,0.12)]`. Contains:
   - Gradient icon container (navy circle, `cloud_upload` Material Symbol, scales on hover)
   - Title: "Datei hier ablegen"
   - Subtitle: "Lebenslauf als PDF oder DOCX — oder LinkedIn-Export als ZIP. Das Format wird automatisch erkannt."
   - Browse button (pill-shaped, `bg-primary-container text-primary`)
   - Format hint: "PDF · DOCX · ZIP bis 10 MB"
2. **LinkedIn secondary card** — below the dropzone. Opens a file picker pre-filtered to `.zip,.pdf` and routes to `/api/profile/import`. Purely a shortcut for users with a LinkedIn ZIP; clicking it programmatically triggers a hidden `<input type="file" accept=".zip,.pdf">`.
3. **Status strip** — shown after upload, hidden before:
   - Success: green strip with completeness score (`bg-[#dcfce7] border border-[#86efac]`)
   - Error: red strip with API error message (`bg-red-50 border border-red-200`)

**Right column:**
1. **Upload history panel** — glass card. Fetches `GET /api/profile/uploads` on mount. Shows last 3 entries (filename, relative date, completeness %). All row action icons (download on CV rows, refresh on LinkedIn rows) are decorative — no click handler. LinkedIn entries show a `link` icon instead of `description`. Empty state: "Noch keine Uploads" with a muted icon.
2. **AI context card** — navy (`bg-primary text-white`). Static content:
   - Tag: `auto_awesome` icon + "Profil-Intelligenz" label
   - Title: "Warum aktualisieren?"
   - Body: "Ein aktueller Lebenslauf verbessert die Treffsicherheit aller KI-Analysen — von der Lückenanalyse bis zur CV-Generierung. Änderungen werden sofort im Masterprofil zusammengeführt."

### Upload routing logic
```
file.name.endsWith(".zip") → POST /api/profile/import
otherwise                  → POST /api/profile/upload
```
Both via `multipart/form-data` with `file` field. On success, store the completeness score in local state and show the success strip. On error, surface the API `detail` string in the error strip.

### Post-upload navigation
- `flowId` present: run gap analysis (`POST /api/job/{job_id}/gaps`) then `advanceFlow(flowId, "gap_analysis", gapData.id)` → navigate to `/flow/${flowId}/gaps`
- `flowId` absent: navigate to `/profile`

The gap-analysis logic (currently duplicated in the old flow import page) moves into a private helper inside the component and is only invoked when `flowId` is set.

### Translation namespace
New namespace `profileImport` in `de.json` / `en.json`:
```json
"profileImport": {
  "title": "Profil aktualisieren",
  "subtitle": "Lebenslauf als PDF oder DOCX — oder LinkedIn-Export als ZIP. Das Format wird automatisch erkannt.",
  "dropTitle": "Datei hier ablegen",
  "browse": "Datei auswählen",
  "formats": "PDF · DOCX · ZIP bis 10 MB",
  "linkedinCardTitle": "LinkedIn-Datenexport hochladen",
  "linkedinCardDesc": "Vollständiges Archiv (ZIP) aus den LinkedIn-Datenschutzeinstellungen — enthält strukturierte Profildaten für präzisere Extraktion.",
  "uploading": "Wird hochgeladen …",
  "successPrefix": "Profil aktualisiert — Vollständigkeit: ",
  "historyTitle": "Letzte Uploads",
  "historyEmpty": "Noch keine Uploads",
  "viewAll": "Alle anzeigen",
  "whyTitle": "Warum aktualisieren?",
  "whyBody": "Ein aktueller Lebenslauf verbessert die Treffsicherheit aller KI-Analysen — von der Lückenanalyse bis zur CV-Generierung. Änderungen werden sofort im Masterprofil zusammengeführt."
}
```

---

## 5. Pages

### New: `frontend/app/(shell)/profile/upload/page.tsx`
```tsx
export default function ProfileUploadPage() {
  return <ProfileImportView />;
}
```
Minimal wrapper. Inherits shell layout from `app/(shell)/layout.tsx`.

### Refactored: `frontend/app/(shell)/flow/[flowId]/import/page.tsx`
Replace all inline-style logic with:
```tsx
export default function ImportPage({ params }: { params: Promise<{ flowId: string }> }) {
  const { flowId } = use(params);
  return <ProfileImportView flowId={flowId} />;
}
```
The existing page's fetch logic, error handling, and inline styles are all removed — they move into `ProfileImportView`.

---

## 6. Backend — Upload History Endpoint

**New endpoint:** `GET /api/profile/uploads`  
**File:** `backend/applire/routers/profile.py`

Returns the last 10 `UploadRecord` rows for the current user, ordered by `created_at desc`.

Response schema (new `UploadHistoryItem` in `schemas/profile.py`):
```python
class UploadHistoryItem(BaseModel):
    id: UUID
    original_filename: str
    mime_type: str
    byte_size: int
    created_at: datetime
    completeness_score: float | None  # from profile metadata if available
```

`completeness_score` is best-effort: if the upload record has a linked completeness score (from the `CVUploadResponse` at time of upload), return it; otherwise `null`. For the MVP it is acceptable to always return `null` and add the linkage later.

---

## Out of scope for this sprint
- XING integration (noted for future investigation)
- Re-upload / refresh action on history items (decorative only)
- Help & Support page (footer link removed entirely)
- Upload history "View All" page (button present, navigates to `/profile/uploads` — page not built yet, 404 acceptable for now)

---

## Files changed

| File | Action |
|---|---|
| `frontend/public/applire-icon.png` | New (copy from `Icons/`) |
| `frontend/next.config.ts` | Add `env.NEXT_PUBLIC_APP_VERSION` |
| `frontend/components/shell/AppSidebar.tsx` | Logo, footer, nav item |
| `frontend/messages/de.json` | Add `shell.import`, `profileImport.*` |
| `frontend/messages/en.json` | Add `shell.import`, `profileImport.*` |
| `frontend/components/profile/ProfileImportView.tsx` | New component |
| `frontend/app/(shell)/profile/upload/page.tsx` | New page |
| `frontend/app/(shell)/flow/[flowId]/import/page.tsx` | Refactor to thin wrapper |
| `backend/applire/schemas/profile.py` | Add `UploadHistoryItem` |
| `backend/applire/routers/profile.py` | Add `GET /api/profile/uploads` |
