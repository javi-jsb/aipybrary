import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel.ext.asyncio.session import AsyncSession

from app.book_copies.infrastructure.sql_book_copy_repository import SqlModelBookCopyRepository
from app.core.sorting import SortOrder
from app.database import get_session
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
    LoanCreate,
    LoanListResponse,
    LoanPublic,
    LoanStatus,
    SortBy,
)
from app.loans.infrastructure.sql_loan_repository import SqlModelLoanRepository
from app.members.infrastructure.sql_member_repository import SqlModelMemberRepository
from app.users.infrastructure.authz import FORBIDDEN, STAFF_ROLES, CurrentUser, MemberRepoDep, staff_only

router = APIRouter(prefix="/loans", tags=["loans"])

# Borrow/return/cancel are admin/staff only; reads are scoped to the caller's own
# loans when the caller is a member.
_STAFF_ONLY = [Depends(staff_only)]


def _get_service(session: Annotated[AsyncSession, Depends(get_session)]) -> LoanService:
    return LoanService(
        SqlModelLoanRepository(session),
        SqlModelMemberRepository(session),
        SqlModelBookCopyRepository(session),
    )


ServiceDep = Annotated[LoanService, Depends(_get_service)]


@router.get("", response_model=LoanListResponse)
async def list_loans(
    service: ServiceDep,
    current_user: CurrentUser,
    member_repo: MemberRepoDep,
    page: Annotated[int, Query(ge=1)] = 1,
    size: Annotated[int, Query(ge=1, le=100)] = 20,
    member_id: uuid.UUID | None = None,
    book_copy_id: uuid.UUID | None = None,
    status: LoanStatus | None = None,
    sort_by: SortBy = SortBy.created_at,
    order: SortOrder = SortOrder.desc,
) -> LoanListResponse:
    # A member sees only their own loans: force the member_id filter to their own
    # member, overriding any supplied value. Staff/admin keep free filtering.
    if current_user.role not in STAFF_ROLES:
        own = await member_repo.get_by_user_id(current_user.id)
        if own is None:
            raise FORBIDDEN
        member_id = own.id
    return await service.get_filtered(member_id, book_copy_id, status, sort_by, order, page, size)


@router.get("/{loan_id}", response_model=LoanPublic)
async def get_loan(
    loan_id: uuid.UUID,
    service: ServiceDep,
    current_user: CurrentUser,
    member_repo: MemberRepoDep,
) -> LoanPublic:
    loan = await service.get_by_id(loan_id)
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    # A member may read only their own loans; another member's loan is forbidden.
    if current_user.role not in STAFF_ROLES:
        own = await member_repo.get_by_user_id(current_user.id)
        if own is None or loan.member_id != own.id:
            raise FORBIDDEN
    return LoanPublic.model_validate(loan)


@router.post("", response_model=LoanPublic, status_code=status.HTTP_201_CREATED, dependencies=_STAFF_ONLY)
async def borrow(data: LoanCreate, service: ServiceDep) -> LoanPublic:
    try:
        loan = await service.borrow(data.member_id, data.book_copy_id)
    except MemberNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found") from None
    except MemberSuspendedError:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="Member is suspended") from None
    except BookCopyNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Book copy not found") from None
    except BookCopyNotAvailableError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Book copy is already on loan") from None
    except LoanLimitExceededError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Member has reached the active loan limit",
        ) from None
    return LoanPublic.model_validate(loan)


@router.post("/{loan_id}/return", response_model=LoanPublic, dependencies=_STAFF_ONLY)
async def return_loan(loan_id: uuid.UUID, service: ServiceDep) -> LoanPublic:
    try:
        loan = await service.return_loan(loan_id)
    except LoanAlreadyReturnedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Loan is already returned") from None
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return LoanPublic.model_validate(loan)


@router.delete("/{loan_id}/return", response_model=LoanPublic, dependencies=_STAFF_ONLY)
async def undo_return(loan_id: uuid.UUID, service: ServiceDep) -> LoanPublic:
    try:
        loan = await service.undo_return(loan_id)
    except LoanNotReturnedError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Loan is not returned") from None
    if loan is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
    return LoanPublic.model_validate(loan)


@router.delete("/{loan_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=_STAFF_ONLY)
async def cancel_loan(loan_id: uuid.UUID, service: ServiceDep) -> None:
    try:
        deleted = await service.cancel(loan_id)
    except LoanAlreadyReturnedCancelError:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Cannot cancel a returned loan") from None
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Loan not found")
