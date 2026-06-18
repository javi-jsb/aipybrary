import { defineConfig, devices } from "@playwright/test";
import {
  API_BASE_URL,
  API_PORT,
  APP_BASE_URL,
  APP_PORT,
  backendEnv,
  REPO_ROOT,
} from "./e2e/config";

/**
 * End-to-end test configuration.
 *
 * These tests drive the real SPA in a real browser against the real API and a
 * dedicated E2E Postgres database (see the archived `e2e-playwright-tests`
 * change / the `e2e-testing` spec). The harness is self-contained: `webServer`
 * spawns both tiers directly (no Makefile indirection) on dedicated ports so it
 * never collides with a running `make dev` / `make dev-frontend`:
 *   - the FastAPI API on :8078, pointed at the `aipybrary_e2e` database;
 *   - the Vite-served SPA on :5273, configured to call that API.
 *
 * `globalSetup` provisions the E2E database (create + migrate + seed) once;
 * the per-test reset lives in `e2e/fixtures.ts`. Postgres itself must be
 * running (`make db-up`).
 */
export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  globalSetup: "./e2e/global-setup.ts",
  fullyParallel: false,
  workers: 1,
  reporter: "list",
  use: {
    baseURL: APP_BASE_URL,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: [
    {
      command: `uv run fastapi dev --port ${API_PORT}`,
      cwd: REPO_ROOT,
      env: backendEnv,
      url: `${API_BASE_URL}/health`,
      reuseExistingServer: false,
      timeout: 120_000,
    },
    {
      command: `pnpm dev --port ${APP_PORT} --strictPort`,
      env: { ...process.env, VITE_API_BASE_URL: API_BASE_URL },
      url: APP_BASE_URL,
      reuseExistingServer: false,
      timeout: 120_000,
    },
  ],
});
