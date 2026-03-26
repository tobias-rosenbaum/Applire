# 🧪 Apliqa Test Infrastructure

## Overview

Apliqa has a comprehensive three-tier testing strategy:

1. **Unit Tests** - Fast, isolated component testing
2. **Integration Tests** - API and service interaction testing
3. **E2E Tests** - Full user journey testing with Playwright

---

## Unit Tests

### Location
`Solution/backend/tests/unit/`

### Current Status
- **Total**: 51 tests
- **Passing**: 47 ✅
- **Errors**: 4 ⚠️ (SQLite persistence setup issues)
- **Coverage**: ~70%

### Running Locally
```bash
cd Solution/backend
pytest tests/unit/ -v --cov=apliqa --cov-report=html
```

### Test Categories

#### TestSchemaModels (4 tests)
- Profile schema validation
- Default value handling
- Field type checking

#### TestLegacyMigration (4 tests)
- Data migration from old format
- Field mapping validation
- Backward compatibility

#### TestCompletenessScore (5 tests)
- Profile completeness calculation
- Weight distribution
- Rounding behavior

#### TestDateHelpers (7 tests)
- Date overlap detection
- Contradiction detection
- Date range handling

#### TestMergeWorkExperience (9 tests)
- Work history merging logic
- Conflict detection
- Deduplication

#### TestMergeSkills (6 tests)
- Skill proficiency merging
- Experience years handling
- Case-insensitive dedup

#### TestMergeProfiles (8 tests)
- Profile merging logic
- Enrichment tracking
- Conflict flagging

#### TestConflictSchema (3 tests)
- Conflict UUID generation
- Resolution request validation

### Known Issues

**SQLite Persistence Tests (4 errors)**
- Foreign key constraint: `uploads.user_id` → `users.id`
- Occurs during in-memory SQLite setup
- **Fix**: Mock the foreign key constraint or use PostgreSQL for these tests

---

## Integration Tests

### Location
`Solution/tests/integration/`

### Current Status
- **Total**: 7 tests
- **Passing**: 6 ✅
- **Skipped**: 1 ⏭️ (requires `INTEGRATION_LLM=1`)

### Running Locally
```bash
cd Solution
docker-compose up -d
docker-compose exec -T backend python -m pytest tests/ --ignore=tests/e2e -v
```

### Test Coverage

#### test_iter0_skeleton.py (2 tests)
- ✅ `test_health_returns_200` - API health endpoint
- ✅ `test_health_body` - Health response structure

#### test_iter1_jd_analysis.py (4 tests)
- ✅ `test_analyze_returns_200` - JD analysis endpoint
- ✅ `test_analyze_response_structure` - Response format validation
- ✅ `test_analyze_deduplication` - Skill deduplication
- ✅ `test_analyze_rejects_empty_text` - Input validation

#### test_happy_path.py (1 test)
- ⏭️ `test_happy_path_new_user` - Full user flow (requires LLM)

### Running with LLM
```bash
cd Solution
INTEGRATION_LLM=1 docker-compose exec -T backend python -m pytest tests/integration/ -v
```

---

## E2E Tests

### Location
`Solution/tests/e2e/`

### Current Status
- **Total**: 1 test file
- **Status**: ✅ Ready to run
- **Framework**: Playwright (TypeScript)

### Test Files

#### marcus-persona.spec.ts
- User journey testing
- UI interaction validation
- Full application flow

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

## CI/CD Pipeline

### GitHub Actions Workflow
**File**: `.github/workflows/test.yml`

### Jobs

#### 1. Backend Unit Tests
- **Trigger**: Push to `main`, `develop`, `sprint-4`
- **Runtime**: ~2 minutes
- **Coverage Threshold**: 70%
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
├── unit/              # Fast, isolated tests
├── integration/       # API and service tests
├── e2e/              # Full user journey tests
├── fixtures/         # Test data and files
└── conftest.py       # Shared fixtures
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
| Unit | ~1.3s | 51 |
| Integration | ~2.6s | 6 |
| E2E | ~5-10s | 1 |
| **Total** | **~10-15s** | **58** |

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
1. Check workflow runs: https://github.com/tobias-rosenbaum/Apliqa/actions
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
