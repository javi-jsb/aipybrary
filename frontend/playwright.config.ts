import { defineConfig, devices } from "@playwright/test";

/**
 * End-to-end test configuration.
 *
 * These tests drive the real SPA in a real browser (see the `e2e-playwright-tests`
 * OpenSpec change). This harness slice (#96) boots only the Vite-served SPA via
 * `webServer`; orchestrating the FastAPI server and a dedicated E2E database lands
 * in #97, where backend and data isolation are introduced together.
 */
export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  fullyParallel: true,
  reporter: "list",
  use: {
    baseURL: "http://localhost:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "pnpm dev",
    url: "http://localhost:5173",
    reuseExistingServer: true,
    timeout: 120_000,
  },
});
