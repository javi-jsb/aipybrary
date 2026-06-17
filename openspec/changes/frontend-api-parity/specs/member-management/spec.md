## MODIFIED Requirements

### Requirement: Delete a member

The API SHALL expose `DELETE /members/{member_id}` that removes a member.

A member that is still referenced by a `Loan` SHALL NOT be deletable: the `loans.member_id` foreign key is `ON DELETE RESTRICT`. The SQL repository SHALL catch the resulting `IntegrityError`, recognise the `fk_loans_member_id_members` constraint via `is_constraint_violated`, and translate it into a `MemberHasLoansError` domain exception, mirroring the `BookHasCopiesError` pattern. The router SHALL map that exception to `409 Conflict`. The constraint name SHALL be exposed as `MEMBER_FK_CONSTRAINT` in `app.loans.domain.loan_model` so the member repository can reference it without hardcoding the string (an infrastructure-to-domain cross-slice import, which is acceptable; the constraint is that domain layers do not import from other slices).

#### Scenario: Member exists

- **WHEN** a client sends `DELETE /members/{member_id}` with a valid existing ID
- **THEN** the response status code is `204`
- **AND** the member is no longer retrievable via `GET /members/{member_id}`

#### Scenario: Member does not exist

- **WHEN** a client sends `DELETE /members/{member_id}` with a non-existent ID
- **THEN** the response status code is `404`

#### Scenario: Member has loans

- **WHEN** a client sends `DELETE /members/{member_id}` for a member that is still referenced by at least one `Loan`
- **THEN** the response status code is `409`
- **AND** the member is still retrievable via `GET /members/{member_id}`
