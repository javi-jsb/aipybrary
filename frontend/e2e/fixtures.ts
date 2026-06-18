import { execSync } from "node:child_process";
import { resolve } from "node:path";
import { test as base, expect, type APIRequestContext } from "@playwright/test";

/**
 * Shared E2E fixtures (see the `e2e-playwright-tests` OpenSpec change):
 *
 * - `resetDb` (auto): truncates + re-seeds the E2E database before every test,
 *   so each test starts from the same deterministic baseline and specs are
 *   order-independent.
 * - `loginAs`: authenticates against the real API as a given role and injects
 *   the access token into the SPA's token store, so the next navigation lands
 *   in the authenticated app without driving the login form each time.
 *
 * Import `test`/`expect` from this module (not `@playwright/test`) in any spec
 * that needs a clean database or an authenticated session.
 */
const repoRoot = resolve(process.cwd(), "..");

// Must match playwright.config.ts (API port) and the seed (e2e_db.py credentials).
const API_BASE_URL = "http://localhost:8078";
const TOKEN_KEY = "aipybrary.access_token";
const E2E_PASSWORD = "pass";

export type Role = "admin" | "staff" | "member";

const EMAIL_BY_ROLE: Record<Role, string> = {
  admin: "admin@aipybrary.dev",
  staff: "staff@aipybrary.dev",
  member: "member@aipybrary.dev",
};

async function fetchToken(request: APIRequestContext, role: Role): Promise<string> {
  const response = await request.post(`${API_BASE_URL}/auth/login`, {
    form: { username: EMAIL_BY_ROLE[role], password: E2E_PASSWORD },
  });
  if (!response.ok()) {
    throw new Error(`E2E login failed for ${role}: HTTP ${response.status()}`);
  }
  return (await response.json()).access_token as string;
}

type Fixtures = {
  resetDb: void;
  loginAs: (role: Role) => Promise<void>;
};

export const test = base.extend<Fixtures>({
  resetDb: [
    // eslint-disable-next-line no-empty-pattern -- auto fixture takes no dependencies
    async ({}, use) => {
      execSync("make db-e2e-reset", { cwd: repoRoot, stdio: "pipe" });
      await use();
    },
    { auto: true },
  ],
  loginAs: async ({ page, request }, use) => {
    await use(async (role: Role) => {
      const token = await fetchToken(request, role);
      await page.addInitScript(([key, value]) => window.localStorage.setItem(key, value), [
        TOKEN_KEY,
        token,
      ] as const);
    });
  },
});

export { expect };
