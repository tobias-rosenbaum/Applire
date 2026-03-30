# Agent Guidance

## Important Rules
- Always read files before editing — never guess at content.
- Run tests after making changes to verify nothing is broken.
- Maintain strict type safety — avoid `any` unless there is no alternative.
- Follow existing type patterns in the codebase.
- Follow existing component patterns when creating new UI components.
- Keep components focused — prefer composition over large monolithic components.
- Check Docker container status and logs when debugging deployment issues.

## Common Patterns
- Check existing implementations before creating new utilities — avoid duplication.
- Follow the existing project structure when adding new files.
- Use the project's established import style (relative vs absolute paths).

## Known Gotchas
_No known gotchas yet. Add issues as they are discovered._

## File Editing Notes
The following files are complex (1000+ lines) — edit with care and use targeted edits rather than full rewrites:
- `Solution/backend/apliqa/schemas/profile.py`
- `Solution/backend/tests/unit/test_iter11_profile.py`
- `Solution/tests/unit/test_iter11_profile.py`
- `Solution/tests/unit/test_iter13_gap.py`
- `Solution/tests/unit/test_iter12_upload.py`
- `Solution/tests/test_iter2_profile_import.py`
- `Solution/tests/test_iter5_cv_generation.py`
- `Solution/tests/test_iter9_second_template_linkedin.py`
- `Solution/tests/unit/test_iter15_flow_orchestrator.py`
- `Solution/tests/unit/test_iter17_application.py`


## Testing Notes
- Use `npm test` to run the test suite.
