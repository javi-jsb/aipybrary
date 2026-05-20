### Requirement: Workflow triggers
The CI workflow SHALL run on every push and pull request targeting the `main` branch.

#### Scenario: Push to main triggers workflow
- **WHEN** a commit is pushed to `main`
- **THEN** the CI workflow starts automatically

#### Scenario: Pull request targeting main triggers workflow
- **WHEN** a pull request is opened or updated against `main`
- **THEN** the CI workflow starts automatically

### Requirement: PostgreSQL service container
The workflow SHALL start a `postgres:17` service container with a health check before any job steps run. The database name SHALL be `aipybrary_test`, matching the value used by `POSTGRES_TEST_DB`.

#### Scenario: Service is healthy before steps run
- **WHEN** the job starts
- **THEN** the Postgres container passes `pg_isready` before any step executes

### Requirement: Lint step
The workflow SHALL run `make check` and fail the job if linting or format verification fails.

#### Scenario: Lint passes
- **WHEN** all source files conform to Ruff rules
- **THEN** the lint step exits with code 0

#### Scenario: Lint fails
- **WHEN** a source file violates a Ruff rule or formatting check
- **THEN** the lint step exits with a non-zero code and the job is marked failed

### Requirement: Test and coverage step
The workflow SHALL run `make coverage`, which executes the full test suite and produces a coverage XML report. The job SHALL fail if any test fails.

#### Scenario: All tests pass
- **WHEN** every test in the suite passes
- **THEN** the test step exits with code 0 and a coverage XML report is written

#### Scenario: A test fails
- **WHEN** one or more tests fail
- **THEN** the test step exits with a non-zero code and the job is marked failed

### Requirement: Coverage badge update
After the test step, the workflow SHALL extract the total coverage percentage and write it to a secret Gist using `Schneegans/dynamic-badges-action`. This step SHALL run only on push to `main` (not on pull requests).

#### Scenario: Coverage badge updated on push to main
- **WHEN** a push to `main` triggers the workflow and all tests pass
- **THEN** the Gist is updated with the new coverage percentage and the shields.io badge reflects it

#### Scenario: Coverage badge not updated on pull request
- **WHEN** a pull request triggers the workflow
- **THEN** tests and coverage extraction run but the Gist is not updated
