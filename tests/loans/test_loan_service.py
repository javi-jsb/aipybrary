import uuid
from datetime import UTC, datetime, timedelta

import pytest

from app.book_copies.domain.book_copy_model import BookCopy, BookCopyCreate
from app.book_copies.domain.book_copy_repository import BookCopyRepository
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
    LoanCreate,
)
from app.loans.domain.loan_repository import LoanRepository
from app.members.domain.member_model import Member, MemberCreate, MemberStatus
from app.members.domain.member_repository import MemberRepository


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Fake repositories
# ---------------------------------------------------------------------------


class FakeMemberRepository(MemberRepository):
    def __init__(self) -> None:
        self._members: dict[uuid.UUID, Member] = {}

    def add(self, member: Member) -> None:
        self._members[member.id] = member

    async def create(self, data: MemberCreate) -> Member:  # pragma: no cover
        member = Member.model_validate(data)
        self._members[member.id] = member
        return member

    async def get_by_id(self, member_id: uuid.UUID) -> Member | None:
        return self._members.get(member_id)

    async def get_filtered(self, full_name, email, status, sort_by, order, page, size):  # pragma: no cover
        return [], 0

    async def update(self, member, data):  # pragma: no cover
        return member

    async def delete(self, member):  # pragma: no cover
        self._members.pop(member.id, None)


class FakeBookCopyRepository(BookCopyRepository):
    def __init__(self) -> None:
        self._copies: dict[uuid.UUID, BookCopy] = {}

    def add(self, copy: BookCopy) -> None:
        self._copies[copy.id] = copy

    async def create(self, data: BookCopyCreate) -> BookCopy:  # pragma: no cover
        copy = BookCopy.model_validate(data)
        self._copies[copy.id] = copy
        return copy

    async def get_by_id(self, copy_id: uuid.UUID) -> BookCopy | None:
        return self._copies.get(copy_id)

    async def get_filtered(self, book_id, barcode, location, sort_by, order, page, size):  # pragma: no cover
        return [], 0

    async def update(self, copy, data):  # pragma: no cover
        return copy

    async def delete(self, copy):  # pragma: no cover
        self._copies.pop(copy.id, None)

    async def count_by_book_id(self, book_id):  # pragma: no cover
        return 0


class FakeLoanRepository(LoanRepository):
    def __init__(self) -> None:
        self._loans: dict[uuid.UUID, Loan] = {}
        self._active_count: dict[uuid.UUID, int] = {}

    def add(self, loan: Loan) -> None:
        self._loans[loan.id] = loan

    async def create(self, data: LoanCreate, due_date: datetime) -> Loan:
        loan = Loan(member_id=data.member_id, book_copy_id=data.book_copy_id, due_date=due_date)
        self._loans[loan.id] = loan
        return loan

    async def get_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        return self._loans.get(loan_id)

    async def get_filtered(self, member_id, book_copy_id, status, sort_by, order, page, size):  # pragma: no cover
        return [], 0

    async def mark_returned(self, loan: Loan) -> Loan:
        loan.returned_at = _utcnow()
        loan.updated_at = _utcnow()
        return loan

    async def undo_return(self, loan: Loan) -> Loan:
        loan.returned_at = None
        loan.updated_at = _utcnow()
        return loan

    async def delete(self, loan: Loan) -> None:
        self._loans.pop(loan.id, None)

    async def count_active_for_member(self, member_id: uuid.UUID) -> int:
        return self._active_count.get(member_id, 0)

    async def get_active_for_copy(self, book_copy_id: uuid.UUID) -> Loan | None:
        for loan in self._loans.values():
            if loan.book_copy_id == book_copy_id and loan.returned_at is None:
                return loan
        return None

    def set_active_count(self, member_id: uuid.UUID, count: int) -> None:
        self._active_count[member_id] = count


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
