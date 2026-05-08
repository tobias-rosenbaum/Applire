# 🧪 Applire Test Infrastructure

## Overview

Applire has a comprehensive three-tier testing strategy:

1. **Unit Tests** - Fast, isolated component testing
2. **Integration Tests** - API and service interaction testing
3. **E2E Tests** - Full user journey testing with Playwright

---

## Unit Tests

### Location
`Solution/tests/unit/`

### Running Locally
```bash
cd Solution
pytest tests/unit/ -v --cov=applire --cov-report=html
```

### Test Files

| File | Coverage |
|------|----------|
| `test_iter6_llm_providers.py` | LLM provider abstraction |
| `test_iter7_mcp_tools.py` | MCP server tools |
| `test_iter7_mcp_resources.py` | MCP server resources |
| `test_iter8_scraper.py` | JD URL scraping |
| `test_iter9_linkedin_parser.py` | LinkedIn JD parsing |
| `test_iter10_auth.py` | NoAuthProvider |
| `test_iter10_retention.py` | GDPR retention worker |
| `test_iter11_profile.py` | Master Profile: schema, merge, conflicts |
| `test_iter12_upload.py` | CV upload handling |
| `test_iter13_gap.py` | Gap detection logic |
| `test_iter15_flow_orchestrator.py` | Flow state machine |
| `test_iter16_llm_provider.py` | LLM provider integration |
| `test_iter17_application.py` | Application service |
| `test_iter17_retention.py` | Retention service |

### Notes

- Unit tests run without Docker — `tests/unit/conftest.py` overrides the Docker fixture and adds `backend/` to `sys.path`.
- `backend/tests/conftest.py` is an in-container variant used by CI (connects to `backend:8000` instead of `localhost:8001`).

---

## Integration Tests

### Location
`Solution/tests/` (API tests) and `Solution/tests/integration/` (full-stack LLM tests)

### Running Locally
```bash
# API tests (no LLM required) — spins up Docker stack automatically
cd Solution
pytest tests/test_iter*.py -v

# Full happy-path test (requires real LLM key)
INTEGRATION_LLM=1 pytest tests/integration/test_happy_path.py -v
```

### Test Coverage

#### API tests (`tests/test_iter*.py`)
Per-iteration endpoint tests covering: health, JD analysis, profile import, gap analysis, interview, CV generation, LLM providers, MCP server, JD URL intake, LinkedIn parsing, auth/retention, CV upload, gap detection, flow orchestrator, application service.

Each test file corresponds to its iteration and uses the Docker-managed API at `localhost:8001`.

#### `tests/integration/test_happy_path.py` (1 test — Sprint 4 task 18.12)
- ⏭️ `test_happy_path_new_user` — CV upload → JD analysis → flow creation → gap analysis → state verification. Skipped unless `INTEGRATION_LLM=1`.

---

## E2E Tests

### Location
`Solution/tests/e2e/`

### Current Status
- **Total**: 1 test file, 8 test cases
- **Status**: ✅ Ready to run
- **Framework**: Playwright (TypeScript)

### Test Files

#### marcus-persona.spec.ts (8 tests)
- Landing page and upload area visibility
- CV upload enabling submit button
- Progress bar and step text during processing
- Full flow: upload → processing overlay → gaps page
- Match score and gaps display
- Generate CV navigation to CV page and download
- Error state graceful handling
- Submit disabled without CV

### Running Locally
```bash
cd Solution/frontend
npm install -D @playwright/test
npx playwright install chromium
npx playwright test
```

### Playwright Configuration
- **Config**: `Solution/playwright.config.ts`
- **Browser**: Chromium
- **Timeout**: 30 seconds per test
- **Retries**: 2 (in CI)

### Viewing Results
```bash
npx playwright show-report
```

---

## Module System

Apliqa uses **ES modules** (`"type": "module"`) for all JavaScript/TypeScript code.

- Use `import` statements — never `require()`
- Vitest and Playwright are ES module-native; they require `"type": "module"` in `package.json`
- All test files (`.spec.ts`, `.test.ts`) must use ES module syntax
- Both `package.json` (root) and `frontend/package.json` declare `"type": "module"`
- A CI/CD gate (`module-system-check` job) enforces this on every push

---

## CI/CD Pipeline

### GitHub Actions Workflow
**File**: `.github/workflows/test.yml`

### Jobs

#### 1. Backend Unit Tests
- **Trigger**: Push to `main`, `develop`, `sprint-4`
- **Runtime**: ~2 minutes
- **Coverage Threshold**: 75%
- **Artifacts**: HTML coverage report

#### 2. Backend Integration Tests
- **Trigger**: After unit tests pass
- **Runtime**: ~10 minutes
- **Services**: Docker Compose (PostgreSQL, Backend, Frontend)
- **Timeout**: 20 minutes

#### 3. E2E Tests
- **Trigger**: After integration tests pass
- **Runtime**: ~5 minutes
- **Dependencies**: Node.js 20, Playwright
- **Artifacts**: Test reports and videos

#### 4. Test Summary
- **Trigger**: After all tests complete
- **Status**: Consolidated report
- **Failure**: Exits with code 1 if any test fails

### Workflow Triggers
```yaml
on:
  push:
    branches: [ main, develop, sprint-4 ]
  pull_request:
    branches: [ main, develop, sprint-4 ]
```

---

## Test Fixtures

### Location
`Solution/tests/fixtures/`

### Available Fixtures

#### Profiles
- `sample_cv.pdf` - Sample CV for upload testing
- `SAMPLE_CV_INSTRUCTIONS.md` - CV parsing instructions

#### Job Descriptions
- `jd.txt` - Sample job description for analysis

#### Downloads
- Test file storage for upload/download tests

---

## Test Data

### Mock Data Strategy
- Use realistic, representative data
- Avoid real personal information
- Create fixtures for common scenarios
- Document data structure in test files

### Example: JD Analysis
```python
JD_FILE = Path(__file__).parent / "files" / "jd.txt"
jd_text = JD_FILE.read_text()
response = requests.post(f"{api}/jd/analyze", json={"text": jd_text})
```

---

## Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Backend Unit | 75% | ~70% |
| Backend Integration | 80% | ~85% |
| E2E Coverage | 60% | ~50% |
| **Overall** | **70%** | **~68%** |

---

## Troubleshooting

### Unit Tests Fail
```bash
# Check Python version
python --version  # Should be 3.12.3

# Reinstall dependencies
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-mock

# Run with verbose output
pytest tests/unit/ -vv --tb=long
```

### Integration Tests Fail
```bash
# Check Docker is running
docker ps

# View service logs
docker-compose logs backend
docker-compose logs postgres

# Rebuild services
docker-compose down -v
docker-compose up -d --build
```

### E2E Tests Fail
```bash
# Check Node.js version
node --version  # Should be 20+

# Reinstall Playwright
npx playwright install --with-deps chromium

# Run in headed mode to see browser
npx playwright test --headed

# Debug specific test
npx playwright test marcus-persona.spec.ts --debug
```

---

## Best Practices

### Writing Tests
1. ✅ Use descriptive test names
2. ✅ Test one thing per test
3. ✅ Use fixtures for setup/teardown
4. ✅ Mock external dependencies
5. ✅ Include both happy path and error cases

### Test Organization
```
tests/
├── unit/              # Fast, isolated tests (no Docker)
│   └── conftest.py    # Overrides Docker fixture; adds backend/ to sys.path
├── integration/       # Full-stack LLM tests (INTEGRATION_LLM=1)
├── e2e/               # Playwright E2E tests
├── fixtures/          # Test data (CVs, JDs, downloads)
├── files/             # Files used by integration tests (cv.pdf, jd.txt)
├── test_iter*.py      # Per-iteration API tests
└── conftest.py        # Session fixture: starts Docker stack, waits for API

backend/tests/
└── conftest.py        # In-container CI variant (connects to backend:8000)
```

### Naming Convention
- `test_<feature>_<scenario>.py`
- `test_<action>_<expected_result>`
- Example: `test_analyze_returns_200`

---

## Performance

### Test Execution Time
| Level | Time | Count |
|-------|------|-------|
| Unit | ~2-5s | ~60+ (14 files) |
| API integration | ~5-15s | 16 files |
| E2E | ~5-10s | 8 |
| LLM integration | ~2-5min | 1 (INTEGRATION_LLM=1) |

### Optimization Tips
- Run unit tests first (fastest feedback)
- Use Docker layer caching for integration tests
- Parallelize E2E tests if possible
- Cache dependencies in CI/CD

---

## Continuous Integration

### GitHub Actions Status
- **Workflow**: `.github/workflows/test.yml`
- **Status Badge**: Add to README.md
- **Artifacts**: Automatically uploaded for 30 days

### Monitoring
1. Check workflow runs: https://github.com/tobias-rosenbaum/Applire/actions
2. Review coverage reports in artifacts
3. Monitor test trends over time
4. Set up notifications for failures

---

## Future Improvements

### Planned
- [ ] Increase unit test coverage to 80%
- [ ] Add performance benchmarks
- [ ] Implement visual regression testing
- [ ] Add accessibility testing (axe)
- [ ] Create test data factories
- [ ] Add mutation testing

### Under Consideration
- [ ] Parallel test execution
- [ ] Test result dashboard
- [ ] Automated test report generation
- [ ] Load testing with k6
- [ ] Security scanning (SAST/DAST)

---

## Resources

- [Pytest Documentation](https://docs.pytest.org/)
- [Playwright Documentation](https://playwright.dev/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

---

**Last Updated**: March 26, 2026
**Maintained By**: Terrie Tester (QA Lead)
