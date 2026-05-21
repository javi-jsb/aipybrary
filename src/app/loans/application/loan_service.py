import uuid
from datetime import timedelta

from app.book_copies.domain.book_copy_repository import BookCopyRepository
from app.config import settings
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
    LoanListResponse,
    LoanPublic,
    LoanStatus,
    SortBy,
    SortOrder,
    _utcnow,
)
from app.loans.domain.loan_repository import LoanRepository
from app.members.domain.member_model import MemberStatus
from app.members.domain.member_repository import MemberRepository


class LoanService:
    def __init__(
        self,
        loan_repository: LoanRepository,
        member_repository: MemberRepository,
        book_copy_repository: BookCopyRepository,
    ) -> None:
        self._loan_repository = loan_repository
        self._member_repository = member_repository
        self._book_copy_repository = book_copy_repository

    async def borrow(self, member_id: uuid.UUID, book_copy_id: uuid.UUID) -> Loan:
        member = await self._member_repository.get_by_id(member_id)
        if member is None:
            raise MemberNotFoundError

        if member.status == MemberStatus.suspended:
            raise MemberSuspendedError

        copy = await self._book_copy_repository.get_by_id(book_copy_id)
        if copy is None:
            raise BookCopyNotFoundError

        active_loan = await self._loan_repository.get_active_for_copy(book_copy_id)
        if active_loan is not None:
            raise BookCopyNotAvailableError

        active_count = await self._loan_repository.count_active_for_member(member_id)
        if active_count >= settings.LOAN_MAX_ACTIVE:
            raise LoanLimitExceededError

        due_date = _utcnow() + timedelta(days=settings.LOAN_PERIOD_DAYS)
        return await self._loan_repository.create(LoanCreate(member_id=member_id, book_copy_id=book_copy_id), due_date)

    async def return_loan(self, loan_id: uuid.UUID) -> Loan | None:
        loan = await self._loan_repository.get_by_id(loan_id)
        if loan is None:
            return None
        if loan.returned_at is not None:
            raise LoanAlreadyReturnedError
        return await self._loan_repository.mark_returned(loan)

    async def undo_return(self, loan_id: uuid.UUID) -> Loan | None:
        loan = await self._loan_repository.get_by_id(loan_id)
        if loan is None:
            return None
        if loan.returned_at is None:
            raise LoanNotReturnedError
        return await self._loan_repository.undo_return(loan)

    async def cancel(self, loan_id: uuid.UUID) -> bool:
        loan = await self._loan_repository.get_by_id(loan_id)
        if loan is None:
            return False
        if loan.returned_at is not None:
            raise LoanAlreadyReturnedCancelError
        await self._loan_repository.delete(loan)
        return True

    async def get_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        return await self._loan_repository.get_by_id(loan_id)

    async def get_filtered(
        self,
        member_id: uuid.UUID | None,
        book_copy_id: uuid.UUID | None,
        status: LoanStatus | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> LoanListResponse:
        loans, total = await self._loan_repository.get_filtered(
            member_id, book_copy_id, status, sort_by, order, page, size
        )
        items = [LoanPublic.model_validate(loan) for loan in loans]
        return LoanListResponse(items=items, total=total, page=page, size=size)
