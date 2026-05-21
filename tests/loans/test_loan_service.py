import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.book_copies.domain.book_copy_model import BookCopy
from app.loans.application.loan_service import LoanService
from app.loans.domain.loan_exceptions import (
    BookCopyNotAvailableError,
    BookCopyNotFoundError,
    LoanAlreadyReturnedCancelError,
    LoanAlreadyReturnedError,
    LoanLimitExceededError,
    LoanNotReturnedError,
    MemberNotFoundError,
    MemberSuspendedError,
)
from app.loans.domain.loan_model import (
    Loan,
    LoanStatus,
    SortBy,
    SortOrder,
)
from app.members.domain.member_model import Member, MemberStatus
from tests.fakes.book_copy_fakes import FakeBookCopyRepository
from tests.fakes.loan_fakes import FakeLoanRepository
from tests.fakes.member_fakes import FakeMemberRepository


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _make_service() -> tuple[LoanService, FakeLoanRepository, FakeMemberRepository, FakeBookCopyRepository]:
    loan_repo = FakeLoanRepository()
    member_repo = FakeMemberRepository()
    copy_repo = FakeBookCopyRepository()
    return LoanService(loan_repo, member_repo, copy_repo), loan_repo, member_repo, copy_repo


def _active_member() -> Member:
    return Member(full_name="Test User", email="test@example.com", status=MemberStatus.active)


def _suspended_member() -> Member:
    return Member(full_name="Suspended User", email="sus@example.com", status=MemberStatus.suspended)


def _copy() -> BookCopy:
    return BookCopy(book_id=uuid.uuid4(), barcode="BC-001")


# ---------------------------------------------------------------------------
# borrow() — invariant tests
# ---------------------------------------------------------------------------


async def test_borrow_member_not_found() -> None:
    service, _, _, _ = _make_service()
    with pytest.raises(MemberNotFoundError):
        await service.borrow(uuid.uuid4(), uuid.uuid4())


async def test_borrow_suspended_member() -> None:
    service, _, member_repo, _ = _make_service()
    member = _suspended_member()
    member_repo.add(member)
    with pytest.raises(MemberSuspendedError):
        await service.borrow(member.id, uuid.uuid4())


async def test_borrow_copy_not_found() -> None:
    service, _, member_repo, _ = _make_service()
    member = _active_member()
    member_repo.add(member)
    with pytest.raises(BookCopyNotFoundError):
        await service.borrow(member.id, uuid.uuid4())


async def test_borrow_copy_not_available() -> None:
    service, loan_repo, member_repo, copy_repo = _make_service()
    member = _active_member()
    member_repo.add(member)
    copy = _copy()
    copy_repo.add(copy)
    # Pre-existing active loan for the copy
    existing = Loan(member_id=uuid.uuid4(), book_copy_id=copy.id, due_date=_utcnow())
    loan_repo.add(existing)
    with pytest.raises(BookCopyNotAvailableError):
        await service.borrow(member.id, copy.id)


async def test_borrow_loan_limit_exceeded() -> None:
    service, loan_repo, member_repo, copy_repo = _make_service()
    member = _active_member()
    member_repo.add(member)
    copy = _copy()
    copy_repo.add(copy)
    loan_repo.set_active_count(member.id, 3)  # at default limit
    with pytest.raises(LoanLimitExceededError):
        await service.borrow(member.id, copy.id)


async def test_borrow_success() -> None:
    service, _, member_repo, copy_repo = _make_service()
    member = _active_member()
    member_repo.add(member)
    copy = _copy()
    copy_repo.add(copy)
    loan = await service.borrow(member.id, copy.id)
    assert loan.member_id == member.id
    assert loan.book_copy_id == copy.id
    assert loan.returned_at is None
    assert loan.due_date > _utcnow()


# ---------------------------------------------------------------------------
# return_loan()
# ---------------------------------------------------------------------------


async def test_return_loan_not_found() -> None:
    service, _, _, _ = _make_service()
    result = await service.return_loan(uuid.uuid4())
    assert result is None


async def test_return_loan_already_returned() -> None:
    service, loan_repo, _, _ = _make_service()
    loan = Loan(member_id=uuid.uuid4(), book_copy_id=uuid.uuid4(), due_date=_utcnow(), returned_at=_utcnow())
    loan_repo.add(loan)
    with pytest.raises(LoanAlreadyReturnedError):
        await service.return_loan(loan.id)


async def test_return_loan_success() -> None:
    service, loan_repo, _, _ = _make_service()
    loan = Loan(member_id=uuid.uuid4(), book_copy_id=uuid.uuid4(), due_date=_utcnow() + timedelta(days=5))
    loan_repo.add(loan)
    result = await service.return_loan(loan.id)
    assert result is not None
    assert result.returned_at is not None


# ---------------------------------------------------------------------------
# undo_return()
# ---------------------------------------------------------------------------


async def test_undo_return_not_found() -> None:
    service, _, _, _ = _make_service()
    result = await service.undo_return(uuid.uuid4())
    assert result is None


async def test_undo_return_not_returned() -> None:
    service, loan_repo, _, _ = _make_service()
    loan = Loan(member_id=uuid.uuid4(), book_copy_id=uuid.uuid4(), due_date=_utcnow() + timedelta(days=5))
    loan_repo.add(loan)
    with pytest.raises(LoanNotReturnedError):
        await service.undo_return(loan.id)


async def test_undo_return_success() -> None:
    service, loan_repo, _, _ = _make_service()
    loan = Loan(member_id=uuid.uuid4(), book_copy_id=uuid.uuid4(), due_date=_utcnow(), returned_at=_utcnow())
    loan_repo.add(loan)
    result = await service.undo_return(loan.id)
    assert result is not None
    assert result.returned_at is None


# ---------------------------------------------------------------------------
# cancel()
# ---------------------------------------------------------------------------


async def test_cancel_not_found() -> None:
    service, _, _, _ = _make_service()
    result = await service.cancel(uuid.uuid4())
    assert result is False


async def test_cancel_already_returned() -> None:
    service, loan_repo, _, _ = _make_service()
    loan = Loan(member_id=uuid.uuid4(), book_copy_id=uuid.uuid4(), due_date=_utcnow(), returned_at=_utcnow())
    loan_repo.add(loan)
    with pytest.raises(LoanAlreadyReturnedCancelError):
        await service.cancel(loan.id)


async def test_cancel_success() -> None:
    service, loan_repo, _, _ = _make_service()
    loan = Loan(member_id=uuid.uuid4(), book_copy_id=uuid.uuid4(), due_date=_utcnow() + timedelta(days=5))
    loan_repo.add(loan)
    result = await service.cancel(loan.id)
    assert result is True
    assert await service.get_by_id(loan.id) is None


# ---------------------------------------------------------------------------
# get_filtered()
# ---------------------------------------------------------------------------


async def test_get_filtered_empty() -> None:
    service, _, _, _ = _make_service()
    result = await service.get_filtered(None, None, None, SortBy.created_at, SortOrder.desc, 1, 20)
    assert result.items == []
    assert result.total == 0
    assert result.pages == 0


async def test_get_filtered_by_member() -> None:
    service, loan_repo, member_repo, copy_repo = _make_service()
    member = _active_member()
    member_repo.add(member)
    copy = _copy()
    copy_repo.add(copy)
    loan = await service.borrow(member.id, copy.id)
    result = await service.get_filtered(member.id, None, None, SortBy.created_at, SortOrder.asc, 1, 20)
    assert result.total == 1
    assert result.items[0].id == loan.id


async def test_get_filtered_by_status() -> None:
    service, loan_repo, _, _ = _make_service()
    active_loan = Loan(
        member_id=uuid.uuid4(),
        book_copy_id=uuid.uuid4(),
        due_date=_utcnow() + timedelta(days=5),
    )
    returned_loan = Loan(
        member_id=uuid.uuid4(),
        book_copy_id=uuid.uuid4(),
        due_date=_utcnow(),
        returned_at=_utcnow(),
    )
    loan_repo.add(active_loan)
    loan_repo.add(returned_loan)
    result = await service.get_filtered(None, None, LoanStatus.returned, SortBy.created_at, SortOrder.desc, 1, 20)
    assert result.total == 1
    assert result.items[0].id == returned_loan.id
