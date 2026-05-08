import { request } from "@playwright/test";

const BACKEND_URL = "http://localhost:8001";

async function globalSetup(): Promise<void> {
  const ctx = await request.newContext({ baseURL: BACKEND_URL });
  try {
    const res = await ctx.get("/health");
    if (!res.ok()) {
      throw new Error(
        `Backend health check returned HTTP ${res.status()}. Is the Docker stack running?`
      );
    }
    const body = await res.json();
    if (body.llm_provider !== "mock") {
      throw new Error(
        `E2E tests require LLM_PROVIDER=mock but the backend reports "${body.llm_provider}".\n` +
          `Start the CI stack before running tests:\n` +
          `  docker compose -f docker-compose.yml -f docker-compose.ci.yml up -d --build`
      );
    }
  } finally {
    await ctx.dispose();
  }
}

export default globalSetup;
