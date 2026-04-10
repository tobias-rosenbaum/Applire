## Summary

<!-- What does this PR do? (1-3 bullet points) -->

## Test plan

- [ ] Backend unit tests pass (`pytest tests/unit/ --cov-fail-under=75`)
- [ ] Frontend unit tests pass (`cd frontend && npm test`)
- [ ] OQ Playwright tests pass (`npx playwright test`)
- [ ] PQ tests run locally and passed — OR — changes do not affect LLM-dependent flows

  To run PQ tests locally:
  ```bash
  OPENROUTER_API_KEY=<your-key> npx playwright test --config=playwright.config.pq.ts
  ```

## Notes

<!-- Anything reviewers should know -->
