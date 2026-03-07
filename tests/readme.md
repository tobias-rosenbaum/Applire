# Test Suite

## Integration tests (Docker required)

```
python -m pytest tests/ -v
```

Run from the project root. Each iteration gets its own `test_iterN_*.py` file.
`conftest.py` handles build → up → wait → migrate automatically, once per session.
Test fixture files (PDFs, ZIPs, etc.) live in `tests/files/`.

## Unit tests (no Docker)

```
pytest tests/unit/ -v
```

Mock-based tests that do not require a running API or database.
Introduced from Iteration 6 onwards for components that are impractical to
test end-to-end (e.g. alternative LLM providers without real API keys).
Each iteration that has unit tests gets a corresponding file in `tests/unit/`.