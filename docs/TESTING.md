# Applire Test Infrastructure

## V-Model Tier Structure

Applire uses a V-model-aligned test structure with four tiers:

| Tier | Scope | Runs in CI | LLM | Blocking |
|---|---|---|---|---|
| **Unit (DQ)** | Individual functions and components in isolation | Yes | No | Yes |
| **IQ** | Docker stack starts cleanly; health endpoint responds; UI reachable | Yes | No | Yes |
| **OQ** | Critical UI flows, all API routes mocked via `page.route()` | Yes | No | Yes |
| **PQ** | Marcus happy-path end-to-end with real LLM (OpenRouter) | Manual only | Yes | No |

**LLM boundary rule:** OQ tests never call an LLM. All backend routes are intercepted with `page.route()` and return deterministic fixtures. PQ tests always call a real LLM and are never run in the standard CI job.

---

## Folder Structure

```
tests/
├── unit/                        # Unit tests (DQ tier) — no Docker
│   ├── conftest.py              # Overrides Docker fixture; adds backend/ to sys.path
│   ├── test_gap_analysis.py
│   ├── test_flow_orchestrator.py
│   └── ...                      # One file per module
├── integration/                 # Full-stack LLM tests (PQ tier)
│   └── test_happy_path.py       # Requires INTEGRATION_LLM=1
├── e2e/
│   ├── iq/
│   │   └── startup.spec.ts      # Health + UI reachable
│   ├── oq/
│   │   ├── gaps-page.spec.ts    # Gaps page critical flows (mocked)
│   │   ├── upload-flow.spec.ts  # Home → processing → gaps (mocked)
│   │   ├── match-page.spec.ts   # Match page (mocked)
│   │   ├── cv-preview.spec.ts   # CV preview iframe (mocked)
│   │   ├── cv-section-editor.spec.ts  # FineTuner section editing (mocked)
│   │   └── photo-management.spec.ts   # Photo upload/crop (mocked)
│   └── pq/
│       └── marcus-new-user-journey.spec.ts  # Full happy path (real LLM)
├── fixtures/
│   ├── profiles/sample_cv.pdf
│   └── JDs/sample_jd.txt
├── test_health.py               # Integration: health endpoint
├── test_jd_analysis.py          # Integration: JD analysis API
├── test_gap_analysis.py         # Integration: gap detection API
└── ...                          # One file per backend module

backend/tests/
└── conftest.py                  # In-container CI variant (connects to backend:8000)
```

---

## Running Tests

### Unit tests (no Docker)

```bash
cd Solution
PYTHONPATH=backend pytest tests/unit/ -v \
  --cov=applire --cov-config=backend/.coveragerc \
  --cov-report=html:backend/htmlcov \
  --cov-fail-under=75
```

Coverage threshold: **≥ 75%** (enforced in CI).

### Frontend unit tests (Vitest)

```bash
cd frontend && npm test
```

### IQ + OQ Playwright tests (requires running frontend)

```bash
# Start frontend dev server first:
cd frontend && npm run dev

# Run IQ + OQ (excludes pq/ automatically):
npx playwright test

# Run a specific spec:
npx playwright test tests/e2e/oq/gaps-page.spec.ts --headed
```

### Integration tests (requires Docker stack)

```bash
docker compose up -d
pytest tests/ --ignore=tests/e2e --ignore=tests/unit -v
```

### PQ tests (requires Docker stack + OpenRouter API key)

```bash
docker compose up -d
OPENROUTER_API_KEY=<your-key> npx playwright test --config=playwright.config.pq.ts
```

Or trigger via GitHub Actions:
1. Go to **Actions → PQ Tests (Manual)**
2. Click **Run workflow**
3. Requires `OPENROUTER_API_KEY` secret to be configured in the repository

---

## Naming Convention

Test files are named after the module they test, not the sprint they were written in.

| Tier | Pattern | Example |
|---|---|---|
| Backend unit | `test_<module>.py` | `test_gap_analysis.py` |
| Backend integration | `test_<module>.py` | `test_cv_generation.py` |
| E2E OQ | `<page-or-feature>.spec.ts` | `gaps-page.spec.ts` |
| E2E PQ | `<persona>-<journey>.spec.ts` | `marcus-new-user-journey.spec.ts` |

---

## Coverage Gate

- Backend unit: **≥ 75%** (`--cov-fail-under=75`)
- No coverage gate on E2E tests (covered by traceability matrix instead)

See `docs/TRACEABILITY.md` for mapping of functional spec items to test IDs.

---

## Personas in PQ Tests

| Persona | Journey | PQ spec | Status |
|---|---|---|---|
| Marcus | New user: upload → gaps → interview → CV | `pq/marcus-new-user-journey.spec.ts` | Active |
| Emma | Returning user: dashboard → one-click tailoring | To be added when returning-user flow is built | Planned |
| Priya | International relocator: cultural adaptation | To be added | Planned |

---

## Troubleshooting

**Unit tests fail:**
```bash
python --version   # must be 3.12.3
pip install -r backend/requirements.txt
pytest tests/unit/ -vv --tb=long
```

**Playwright OQ tests fail:**
```bash
node --version     # must be 20+
npx playwright install --with-deps chromium firefox
npx playwright test --headed    # see browser
npx playwright test --debug     # step through
```

**PQ tests skip most cases:**
Verify `OPENROUTER_API_KEY` is set and the Docker stack is fully running.
```bash
curl http://localhost:8001/health
curl http://localhost:3000
```

---

*Last updated: 2026-04-10*
