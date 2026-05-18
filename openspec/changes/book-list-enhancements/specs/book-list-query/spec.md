## ADDED Requirements

### Requirement: Paginated book list

The API SHALL expose `GET /books` that returns a paginated envelope instead of a flat array.

The response body SHALL conform to:

| Field | Type | Description |
|---|---|---|
| `items` | `list[BookPublic]` | Books on the current page |
| `total` | `int` | Total matching records across all pages |
| `page` | `int` | Current page number (1-based) |
| `size` | `int` | Requested page size |
| `pages` | `int` | Total number of pages (`ceil(total / size)`) |

Query parameters:

| Parameter | Type | Default | Constraints |
|---|---|---|---|
| `page` | `int` | `1` | `>= 1` |
| `size` | `int` | `20` | `>= 1`, `<= 100` |

#### Scenario: Default pagination on non-empty database

- **WHEN** a client sends `GET /books` with no query parameters
- **AND** the database contains 25 books
- **THEN** the response status is `200`
- **AND** `items` contains 20 books
- **AND** `total` is `25`
- **AND** `page` is `1`
- **AND** `size` is `20`
- **AND** `pages` is `2`

#### Scenario: Second page

- **WHEN** a client sends `GET /books?page=2&size=20`
- **AND** the database contains 25 books
- **THEN** `items` contains 5 books
- **AND** `page` is `2`

#### Scenario: Empty result

- **WHEN** a client sends `GET /books` with no query parameters
- **AND** the database is empty
- **THEN** `items` is `[]`
- **AND** `total` is `0`
- **AND** `pages` is `0`

#### Scenario: page out of range

- **WHEN** a client sends `GET /books?page=0`
- **THEN** the response status is `422`

#### Scenario: size exceeds maximum

- **WHEN** a client sends `GET /books?size=101`
- **THEN** the response status is `422`

### Requirement: Filter books by title and author

`GET /books` SHALL accept optional `title` and `author` query parameters that filter results using a case-insensitive partial match (SQL `ILIKE`).

Both filters are independent and additive (AND logic when both are provided).

#### Scenario: Filter by author

- **WHEN** a client sends `GET /books?author=borges`
- **AND** the database contains books with author "Jorge Luis Borges" and others
- **THEN** only books whose author field contains "borges" (case-insensitive) are returned
- **AND** `total` reflects only the matching count

#### Scenario: Filter by title

- **WHEN** a client sends `GET /books?title=quix`
- **THEN** only books whose title contains "quix" (case-insensitive) are returned

#### Scenario: Combined filters

- **WHEN** a client sends `GET /books?author=garcia&title=solitude`
- **THEN** only books matching BOTH filters are returned

#### Scenario: No matches

- **WHEN** a client sends `GET /books?author=zzznomatch`
- **THEN** the response status is `200`
- **AND** `items` is `[]`
- **AND** `total` is `0`

### Requirement: Sort book list

`GET /books` SHALL accept `sort_by` and `order` query parameters.

| Parameter | Allowed values | Default |
|---|---|---|
| `sort_by` | `title`, `author`, `publication_year`, `created_at` | `created_at` |
| `order` | `asc`, `desc` | `desc` |

#### Scenario: Sort by title ascending

- **WHEN** a client sends `GET /books?sort_by=title&order=asc`
- **THEN** the response status is `200`
- **AND** `items` are ordered alphabetically by title

#### Scenario: Default sort

- **WHEN** a client sends `GET /books` with no sort parameters
- **THEN** books are ordered by `created_at` descending (newest first)

#### Scenario: Invalid sort_by value

- **WHEN** a client sends `GET /books?sort_by=invalid`
- **THEN** the response status is `422`
