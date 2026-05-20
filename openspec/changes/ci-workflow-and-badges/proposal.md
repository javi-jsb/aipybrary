## Why

The project has no automated CI pipeline: tests only run locally and there is no public signal of build health or coverage. Adding GitHub Actions CI and README badges closes that gap, giving contributors and reviewers immediate confidence in the state of the codebase.

## What Changes

- New GitHub Actions workflow that runs on every push and pull request to `main`
- Workflow runs linting (`make check`) and the full test suite (`make coverage`) against a Postgres 17 service container
- Coverage percentage written to a secret Gist via `Schneegans/dynamic-badges-action` (PAT scope: `gist` only — no broad OAuth)
- Two badges added to `README.md`: workflow status and coverage percentage

## Capabilities

### New Capabilities

- `ci-pipeline`: GitHub Actions workflow file (`.github/workflows/ci.yml`) — lint, test, coverage upload against a real Postgres service container
- `readme-badges`: Coverage, workflow-status, and test badges displayed at the top of `README.md`

### Modified Capabilities

<!-- none -->

## Impact

- New file: `.github/workflows/ci.yml`
- Modified file: `README.md` (badge links added)
- New external dependency: `Schneegans/dynamic-badges-action` + a secret Gist for hosting the coverage data; shields.io renders the badge from the Gist endpoint
- No changes to application code, tests, or database schema
