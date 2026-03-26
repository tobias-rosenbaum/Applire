# Test Fixtures

This directory contains test fixtures for E2E testing with Playwright.

## Directory Structure

```
fixtures/
├── profiles/          # Sample CV files for testing
│   ├── sample_cv.pdf  # Marcus Chen's CV (primary test fixture)
│   └── SAMPLE_CV_INSTRUCTIONS.md
├── JDs/               # Sample Job Descriptions
│   └── sample_jd.txt  # Senior Full-Stack Developer JD
└── downloads/         # Downloaded files during tests
    └── .gitkeep       # Keeps directory in git
```

## Sample CV (Marcus Chen)

The primary test fixture is `profiles/sample_cv.pdf` - a CV for Marcus Chen, a fictional persona:

**Persona Details:**
- Name: Marcus Chen
- Role: Senior Software Engineer
- Experience: 8 years
- Tech Stack: Python, Django, React, AWS, Kubernetes, PostgreSQL
- Education: M.S. Computer Science, TU Berlin

This CV is used to test:
- CV upload functionality
- Profile extraction and parsing
- Gap analysis against job descriptions
- Download of processed profiles

## Sample Job Description

`JDs/sample_jd.txt` contains a job description for a Senior Full-Stack Developer position at TechCorp GmbH.

This JD is used to test:
- Gap analysis functionality
- Skill matching
- Missing qualification identification

## Adding New Fixtures

When adding new test fixtures:

1. **CVs**: Add to `profiles/` directory
   - Use fictional personas only
   - Include diverse backgrounds and skill sets
   - Document the persona in a corresponding `.md` file

2. **Job Descriptions**: Add to `JDs/` directory
   - Use fictional companies
   - Vary industries and requirements

3. **Downloads**: The `downloads/` directory is for files downloaded during test execution
   - Files here are ignored by git (except .gitkeep)
   - Clean up after test runs

## Notes

- Never use real personal information in test fixtures
- Keep fixtures realistic but fictional
- Document any assumptions about the fixture data
