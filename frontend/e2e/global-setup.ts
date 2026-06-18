import { execSync } from "node:child_process";
import { backendEnv, REPO_ROOT } from "./config";

/**
 * Provision the dedicated E2E database once before the suite: create it if
 * missing, migrate to head, and load the deterministic seed. The per-test
 * reset (truncate + re-seed) lives in `fixtures.ts`.
 *
 * Spawns the backend script directly (POSTGRES_DB points at the E2E database
 * via `backendEnv`); Postgres itself must already be running (`make db-up`).
 */
export default function globalSetup() {
  execSync("uv run python scripts/e2e_db.py provision", {
    cwd: REPO_ROOT,
    stdio: "inherit",
    env: backendEnv,
  });
}
