# E2E Test Failure Baseline (pre-Sprint 28)

**Date recorded:** 2026-04-16  
**Branch verified on:** `main` and `sprint-27` (failures identical on both — all pre-existing)  
**Runner:** Chromium only (Firefox binary missing — see Infrastructure section)

---

## Infrastructure Issue

**Firefox browser binary missing.**  
All Firefox tests fail immediately with:
```
Error: browserType.launch: Executable doesn't exist at
~/.cache/ms-playwright/firefox-1509/firefox/firefox
```
Fix: `npx playwright install firefox`

---

## Failing Tests (Chromium — 33 total)

### `tests/e2e/oq/cv-section-editor.spec.ts` — 8 failures

| Line | Test |
|------|------|
| 138 | `CV Section Editor — Browse/Edit/Save › refinement panel loads with gap count and section list` |
| 160 | `CV Section Editor — Browse/Edit/Save › clicking a section in Browse opens Edit mode with textarea` |
| 182 | `CV Section Editor — Browse/Edit/Save › editing + saving updates the preview iframe` |
| 228 | `CV Section Editor — Browse/Edit/Save › unsaved edits trigger window.confirm when clicking back to overview` |
| 259 | `CV Section Editor — Browse/Edit/Save › clicking a gap card opens Edit mode for owning section` |
| 320 | `CV Section Editor — KaileChat Rewrite › 'Kaile hilft' -> free-text -> rewrite -> suggestion appears -> Apply` |
| 367 | `CV Section Editor — KaileChat Rewrite › gap chips are rendered and toggleable in KaileChat` |
| 415 | `CV Section Editor — Actions Tab › Actions tab shows match score and download button` |

---

### `tests/e2e/oq/gaps-page.spec.ts` — 5 failures

| Line | Test |
|------|------|
| 60 | `Gaps page › renders gap categories with correct severity dot colors` |
| 80 | `Gaps page › shows correct gap counts in badges` |
| 93 | `Gaps page › Generate CV Now button advances flow and navigates to CV page` |
| 111 | `Gaps page › Quick Interview button visible for new user with gaps and navigates to interview` |
| 136 | `Gaps page › shows error message when advance API fails` |

---

### `tests/e2e/oq/jd-url-error.spec.ts` — 5 failures

| Line | Test |
|------|------|
| 82 | `Branch F — JD URL fetch failure › overlay shows JD step as skipped and redirects with ?jd_status=fetch_failed` |
| 121 | `Branch F — JD URL fetch failure › amber recovery banner is visible on gaps page with correct copy` |
| 136 | `Branch F — JD URL fetch failure › amber recovery banner shows url_invalid copy for jd_status=url_invalid` |
| 147 | `Branch F — JD URL fetch failure › CTA navigates to home page` |
| 157 | `Branch F — JD URL fetch failure › dismiss button hides the banner` |

---

### `tests/e2e/oq/match-page.spec.ts` — 4 failures

| Line | Test |
|------|------|
| 45 | `/match page › shows job cards when API returns results` |
| 85 | `/match page › 'Run gap analysis' CTA navigates to /?job_id=…` |
| 107 | `/match page › shows empty state when API returns no jobs` |
| 123 | `/match page › redirects to '/' when API returns 404 (no profile)` |

---

### `tests/e2e/oq/photo-management.spec.ts` — 4 failures

| Line | Test |
|------|------|
| 50 | `Sprint 14: Profile Photo — CV flow photo prompt › shows photo prompt step when user has no photo, skipping goes to template select` |
| 108 | `Sprint 14: Profile Photo — Profile page PhotoManager › renders upload UI and consent checkbox when no photo exists` |
| 144 | `Sprint 14: Profile Photo — Profile page PhotoManager › shows filled state with Replace/Delete buttons after upload` |
| 205 | `Sprint 14: Profile Photo — Profile page PhotoManager › reverts to empty state after delete` |

---

### `tests/e2e/oq/upload-flow.spec.ts` — 4 failures

| Line | Test |
|------|------|
| 76 | `Upload flow › submit button is disabled without a CV file` |
| 84 | `Upload flow › submit button enables after uploading a CV file` |
| 96 | `Upload flow › submitting shows processing overlay and navigates to gaps page` |
| 118 | `Upload flow › shows error when JD analysis API fails` |

---

### `tests/e2e/test_admin_appearance.spec.ts` — 3 failures

| Line | Test |
|------|------|
| 4 | `Admin appearance page › loads the appearance page with scheme editor and preview` |
| 19 | `Admin appearance page › settings page footer has Admin link` |
| 27 | `Admin appearance page › ThemeProvider injects CSS custom properties on app load` |

---

## Passing Tests (Chromium)

- `tests/e2e/iq/startup.spec.ts` — 2/2 pass (backend health + file input present)
- `tests/e2e/oq/cv-color.spec.ts` — 5/5 pass (Design tab, color swatches, PATCH)
- `tests/e2e/oq/cv-preview.spec.ts` — 4/4 pass (iframe srcdoc, text content, panel, download)

---

## Notes

- Common root cause for most failures: tests require authenticated session state that the mock setup does not fully satisfy in the local dev environment.
- `jd-url-error.spec.ts` failures likely related to the same auth/mock issue affecting the gaps page (the banner tests navigate to `/flow/:id/gaps`).
- `test_admin_appearance.spec.ts` failures likely require the Docker stack running with the backend (admin API).
- Artifact screenshots and videos for each failure are in `test-results-pq/`.
