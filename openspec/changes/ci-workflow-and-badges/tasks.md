## 1. GitHub Actions workflow

- [x] 1.1 Create `.github/workflows/ci.yml` with `postgres:17` service container (health check, `POSTGRES_DB=aipybrary_test`)
- [x] 1.2 Add `make check` step to the workflow
- [x] 1.3 Add `make coverage` step with the required `POSTGRES_*` env vars
- [x] 1.4 Add `codecov/codecov-action` step to upload the coverage XML report

## 2. README badges

- [x] 2.1 Add workflow status badge to `README.md` (links to Actions page)
- [x] 2.2 Add Codecov coverage badge to `README.md` (links to Codecov report)

## 3. Coverage badge setup via Gist (manual)

- [x] 3.1 Create a secret Gist (`aipybrary-coverage.json`) and a PAT with `gist` scope only
- [x] 3.2 Add `GIST_TOKEN` as a GitHub Actions repository secret
