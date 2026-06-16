# README Badges

## Purpose

Define the status badges shown in `README.md` that surface the project's CI and coverage health at a glance: the CI workflow status badge and the coverage badge, each linking to its source report.

## Requirements

### Requirement: Workflow status badge
`README.md` SHALL display a badge that reflects the current status of the CI workflow on `main` (passing / failing). The badge SHALL link to the Actions page for the workflow.

#### Scenario: Badge reflects passing build
- **WHEN** the latest CI run on `main` passed
- **THEN** the badge shows a green "passing" state

#### Scenario: Badge reflects failing build
- **WHEN** the latest CI run on `main` failed
- **THEN** the badge shows a red "failing" state

### Requirement: Coverage badge
`README.md` SHALL display a Codecov badge showing the current coverage percentage for `main`. The badge SHALL link to the Codecov report page for the repository.

#### Scenario: Badge reflects current coverage
- **WHEN** Codecov has received a coverage report for the latest commit on `main`
- **THEN** the badge displays the up-to-date coverage percentage
