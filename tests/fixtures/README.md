# Test Fixtures

This directory contains test data files used by the Applire automated test suite.

## Directory Structure

```
Solution/tests/fixtures/
├── profiles/          # Sample CV/resume files
│   └── sample_cv.pdf
├── JDs/              # Sample job descriptions
│   └── sample_jd.txt
├── downloads/        # Temporary location for downloaded files during E2E tests
└── README.md         # This file
```

## Purpose

These fixtures provide realistic, production-like test data for:

- **Backend integration tests** (`Solution/tests/test_iter*.py`)
- **E2E tests** (`Solution/tests/e2e/*.spec.ts`)
- **Local development and debugging**

All fixtures are committed to version control to ensure:
- Reproducible test results across all environments
- Consistent behavior in CI/CD pipelines
- Easy onboarding for new developers

## Current Fixtures

### Profiles (`profiles/`)

- **`sample_cv.pdf`**: A realistic sample CV/resume for a software engineer
  - Used to test CV upload and parsing functionality
  - Contains: contact info, work experience, education, skills
  - Format: PDF (compatible with the CV parser)

### Job Descriptions (`JDs/`)

- **`sample_jd.txt`**: A sample job posting for a Senior Software Engineer position
  - Used to test job description intake and gap analysis
  - Contains: role title, responsibilities, requirements, nice-to-haves
  - Format: Plain text

### Downloads (`downloads/`)

- This directory is used temporarily during E2E tests to store downloaded files
- Files here are automatically generated during test runs
- This directory may be empty when checked out from Git (`.gitkeep` file maintains it)

## Adding Custom Test Data

You can add your own test data files to these directories:

### Adding a CV/Profile:
1. Place your PDF file in `profiles/`
2. Name it descriptively (e.g., `john_doe_cv.pdf`, `senior_dev_profile.pdf`)
3. Update your test files to reference the new fixture path

### Adding a Job Description:
1. Place your text file in `JDs/`
2. Name it descriptively (e.g., `backend_engineer_jd.txt`, `ml_scientist_jd.txt`)
3. Update your test files to reference the new fixture path

### Best Practices:
- Use **realistic data** that resembles actual user input
- **Anonymize** any real personal information
- Keep files **reasonably sized** (CVs: 1-3 pages, JDs: 1-2 pages)
- Use **common formats** (PDF for CVs, TXT/MD for JDs)
- **Document** what makes each fixture special (edge cases, specific formats, etc.)

## Usage in Tests

### Integration Tests (pytest)
```python
import os

# Reference fixture file
cv_path = os.path.join(os.path.dirname(__file__), 'fixtures/profiles/sample_cv.pdf')

with open(cv_path, 'rb') as f:
    response = client.post('/upload/cv', files={'file': f})
```

### E2E Tests (Playwright)
```typescript
import path from 'path';

const cvFilePath = path.join(__dirname, '../fixtures/profiles/sample_cv.pdf');
await page.locator('input[type="file"]').setInputFiles(cvFilePath);
```

## Maintenance

- Review fixtures quarterly to ensure they remain realistic and relevant
- Update fixtures when the application's data requirements change
- Remove obsolete fixtures that are no longer referenced by any tests
- Keep this README up to date when adding/removing fixtures

## Questions?

If you're unsure which fixture to use for a specific test, or need help creating a new one, reach out to the QA team or check the existing test files for examples.
