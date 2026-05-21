import uuid
from datetime import UTC, datetime

from app.loans.domain.loan_model import (
    Loan,
    LoanCreate,
    LoanStatus,
    SortBy,
    SortOrder,
)
from app.loans.domain.loan_repository import LoanRepository


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _loan_status(loan: Loan) -> LoanStatus:
    if loan.returned_at is not None:
        return LoanStatus.returned
    if loan.due_date < _utcnow():
        return LoanStatus.overdue
    return LoanStatus.active


class FakeLoanRepository(LoanRepository):
    def __init__(self) -> None:
        self._loans: dict[uuid.UUID, Loan] = {}
        self._active_count: dict[uuid.UUID, int] = {}

    def add(self, loan: Loan) -> None:
        self._loans[loan.id] = loan

    def set_active_count(self, member_id: uuid.UUID, count: int) -> None:
        self._active_count[member_id] = count

    async def create(self, data: LoanCreate, due_date: datetime) -> Loan:
        loan = Loan(member_id=data.member_id, book_copy_id=data.book_copy_id, due_date=due_date)
        self._loans[loan.id] = loan
        return loan

    async def get_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        return self._loans.get(loan_id)

    async def get_filtered(
        self,
        member_id: uuid.UUID | None,
        book_copy_id: uuid.UUID | None,
        status: LoanStatus | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[Loan], int]:
        loans = list(self._loans.values())
        if member_id is not None:
            loans = [ln for ln in loans if ln.member_id == member_id]
        if book_copy_id is not None:
            loans = [ln for ln in loans if ln.book_copy_id == book_copy_id]
        if status is not None:
            loans = [ln for ln in loans if _loan_status(ln) == status]
        total = len(loans)
        offset = (page - 1) * size
        return loans[offset : offset + size], total

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
