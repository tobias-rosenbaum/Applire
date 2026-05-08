# Traceability Matrix

Maps functional specification items (Epic/User Story IDs from the Product Spec) to test IDs at each V-model tier. Extend this table when adding new features.

**Source:** `Documents/Product Specifications/Epic_and_User_Story_Tracker.csv`

| FS Item | Description | Unit (DQ) | IQ | OQ | PQ |
|---|---|---|---|---|---|
| US001 | Upload single or multiple CVs | `test_cv_upload.py` | `startup.spec.ts` — upload file input present | `upload-flow.spec.ts` — submit button enables after uploading | `marcus-new-user-journey.spec.ts` |
| US002 | Smart auto-merge of multiple CVs | `test_profile_service.py` | — | — | `marcus-new-user-journey.spec.ts` |
| US005 | Parse JD from URL or text | `test_jd_analysis.py` | — | `upload-flow.spec.ts` — submitting shows processing overlay | `marcus-new-user-journey.spec.ts` |
| US006 | Analyze JD for required skills | `test_gap_analysis.py` | — | `gaps-page.spec.ts` — shows correct gap counts | `marcus-new-user-journey.spec.ts` |
| US007 | Gap detection: category A/B/C | `test_gap_analysis.py` | — | `gaps-page.spec.ts` — renders gap categories with correct severity dot colors | `marcus-new-user-journey.spec.ts` |
| APP-19.3 | Generate CV Now button advances flow | — | — | `gaps-page.spec.ts` — Generate CV Now button advances flow and navigates | `marcus-new-user-journey.spec.ts` |
| APP-19.1 | Quick Interview button starts interview | — | — | `gaps-page.spec.ts` — Quick Interview button visible for new user | `marcus-new-user-journey.spec.ts` |
| APP-16 | Match page job cards | — | — | `match-page.spec.ts` | — |
| APP-23 | CV section editor (FineTuner) | — | — | `cv-section-editor.spec.ts` | — |
| APP-14 | Photo management | `test_photo_service.py` | — | `photo-management.spec.ts` | — |

## How to Extend

When implementing a new feature:
1. Add a row for each User Story or APP ticket the feature implements.
2. Link to the test file + test name (or `—` if not covered at that tier).
3. OQ coverage is required for all UI-facing features before merge.
4. PQ coverage is added when the feature is part of a user journey (Marcus, Emma, etc.).
