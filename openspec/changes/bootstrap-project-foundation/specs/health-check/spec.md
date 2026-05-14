## ADDED Requirements

### Requirement: Service health endpoint

The application SHALL expose an HTTP `GET /health` endpoint that reports whether the service process is currently running and able to handle requests.

The response MUST be a `200 OK` with a JSON body where the `status` field equals `"ok"`.

The endpoint MUST NOT require authentication.

The endpoint MUST NOT check the availability of external systems (database, cache, message broker). It is a liveness probe of the application process only; readiness or dependency checks belong to a separate endpoint introduced by a later change.

#### Scenario: Service is up

- **WHEN** a client sends `GET /health`
- **THEN** the response status code is `200`
- **AND** the response body is JSON with `status` equal to `"ok"`

#### Scenario: Health is independent of downstream services

- **WHEN** a client sends `GET /health` while external dependencies (e.g. Postgres) are unreachable
- **THEN** the response is still `200` with `status` equal to `"ok"`
