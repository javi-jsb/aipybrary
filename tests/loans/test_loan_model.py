import uuid
from datetime import UTC, datetime, timedelta

from app.loans.domain.loan_model import Loan, LoanPublic, LoanStatus


def _utcnow_aware() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _make_loan(**kwargs) -> Loan:
    defaults = dict(
        member_id=uuid.uuid4(),
        book_copy_id=uuid.uuid4(),
        due_date=_utcnow_aware() + timedelta(days=14),
    )
    defaults.update(kwargs)
    return Loan(**defaults)


def test_loan_defaults() -> None:
    loan = _make_loan()
    assert loan.id is not None
    assert loan.returned_at is None
    assert loan.created_at is not None
    assert loan.updated_at is not None


def test_loan_status_active() -> None:
    loan = _make_loan(due_date=_utcnow_aware() + timedelta(days=5))
    public = LoanPublic.model_validate(loan)
    assert public.status == LoanStatus.active


def test_loan_status_overdue() -> None:
    loan = _make_loan(due_date=_utcnow_aware() - timedelta(days=1))
    public = LoanPublic.model_validate(loan)
    assert public.status == LoanStatus.overdue


def test_loan_status_returned() -> None:
    loan = _make_loan(
        due_date=_utcnow_aware() - timedelta(days=10),
        returned_at=_utcnow_aware() - timedelta(days=3),
    )
    public = LoanPublic.model_validate(loan)
    assert public.status == LoanStatus.returned


def test_loan_status_returned_overrides_due_date() -> None:
    # Even if due_date is in the future, returned_at takes precedence.
    loan = _make_loan(
        due_date=_utcnow_aware() + timedelta(days=5),
        returned_at=_utcnow_aware(),
    )
    public = LoanPublic.model_validate(loan)
    assert public.status == LoanStatus.returned


def test_loan_public_fields() -> None:
    member_id = uuid.uuid4()
    book_copy_id = uuid.uuid4()
    due = _utcnow_aware() + timedelta(days=7)
    loan = _make_loan(member_id=member_id, book_copy_id=book_copy_id, due_date=due)
    public = LoanPublic.model_validate(loan)
    assert public.member_id == member_id
    assert public.book_copy_id == book_copy_id
    assert public.due_date == due
    assert public.returned_at is None
