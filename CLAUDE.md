# aipybrary

Book library REST API built with Python, FastAPI, and SQLModel.

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.13 |
| Framework | FastAPI (`fastapi[standard]`) |
| ORM | SQLModel |
| Database | PostgreSQL (Docker for local dev) |
| Package manager | uv |
| Linting & formatting | Ruff |
| Testing | pytest + pytest-asyncio |

## Development Conventions

### Commits — Conventional Commits

```
<type>(<optional scope>): <short description>
```

| Type | When |
|---|---|
| `feat` | New feature |
| `fix` | Bug fix |
| `chore` | Maintenance (deps, config, tooling) |
| `refactor` | Code restructuring without behavior change |
| `docs` | Documentation only |
| `test` | Tests only |

### Branch naming

```
<type>/<issue-number>-<short-description>
```

Examples: `feat/5-add-book-endpoint`, `fix/12-null-author-crash`, `chore/1-create-claude-md`

### Pull Requests

- Every PR must reference its issue: `Closes #N`
- PR title follows the same Conventional Commits format as the branch
- Merge strategy: **squash merge** — keeps `main` history linear; GitHub uses the PR title as the resulting commit message

## Language

All public-facing content must be written in **English**: issues, PR titles and descriptions, commit messages, code, comments, and documentation.

## AI Collaboration Rules

**Debate before executing.** If something seems wrong, missing, inconsistent, or improvable, raise it and discuss options before proceeding. Do not execute blindly.

**Keep this file up to date.** If during development a decision is made, a convention is added, or anything worth documenting changes, update `CLAUDE.md` accordingly in the same PR where the change happens.
