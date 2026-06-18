import { resolve } from "node:path";

/**
 * Single source of truth for the E2E harness wiring, shared by the Playwright
 * config, global setup, and fixtures so the suite is self-contained (it spawns
 * the backend directly rather than going through the Makefile).
 *
 * Dedicated ports/database keep the E2E stack from colliding with a running
 * `make dev` / `make dev-frontend` (8077 / 5173).
 */
export const REPO_ROOT = resolve(process.cwd(), "..");

export const E2E_DB = "aipybrary_e2e";
export const API_PORT = 8078;
export const APP_PORT = 5273;
export const API_BASE_URL = `http://localhost:${API_PORT}`;
export const APP_BASE_URL = `http://localhost:${APP_PORT}`;

/**
 * Environment for every backend process the harness spawns: point it at the
 * dedicated E2E database and allow the E2E SPA origin. Everything else
 * (credentials, JWT, …) comes from the repo-root `.env`. Spreads `process.env`
 * so `execSync` keeps PATH and friends.
 */
export const backendEnv = {
  ...process.env,
  POSTGRES_DB: E2E_DB,
  CORS_ALLOW_ORIGINS: APP_BASE_URL,
};
