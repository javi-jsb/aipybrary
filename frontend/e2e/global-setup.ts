import { execSync } from "node:child_process";
import { resolve } from "node:path";

/**
 * Provision the dedicated E2E database once before the suite: create it if
 * missing, migrate to head, and load the deterministic seed. The per-test
 * reset (truncate + re-seed) lives in `fixtures.ts`.
 *
 * Delegates to the Makefile target, which sets `POSTGRES_DB` to the E2E
 * database; Postgres itself must already be running (`make db-up`).
 */
export default function globalSetup() {
  const repoRoot = resolve(process.cwd(), "..");
  execSync("make db-e2e-provision", { cwd: repoRoot, stdio: "inherit" });
}
