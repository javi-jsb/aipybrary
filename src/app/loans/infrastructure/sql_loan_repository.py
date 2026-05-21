import uuid
from datetime import datetime

from sqlalchemy import func
from sqlmodel import col, select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.loans.domain.loan_model import Loan, LoanCreate, LoanStatus, SortBy, SortOrder, _utcnow
from app.loans.domain.loan_repository import LoanRepository


class SqlModelLoanRepository(LoanRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, data: LoanCreate, due_date: datetime) -> Loan:
        loan = Loan(
            member_id=data.member_id,
            book_copy_id=data.book_copy_id,
            due_date=due_date,
        )
        self._session.add(loan)
        await self._session.commit()
        await self._session.refresh(loan)
        return loan

    async def get_by_id(self, loan_id: uuid.UUID) -> Loan | None:
        return await self._session.get(Loan, loan_id)

    async def delete(self, loan: Loan) -> None:
        await self._session.delete(loan)
        await self._session.commit()

    async def count_active_for_member(self, member_id: uuid.UUID) -> int:
        stmt = select(func.count(col(Loan.id))).where(
            col(Loan.member_id) == member_id,
            col(Loan.returned_at).is_(None),
        )
        return (await self._session.exec(stmt)).one()

    async def get_active_for_copy(self, book_copy_id: uuid.UUID) -> Loan | None:
        stmt = select(Loan).where(
            col(Loan.book_copy_id) == book_copy_id,
            col(Loan.returned_at).is_(None),
        )
        return (await self._session.exec(stmt)).first()

    async def mark_returned(self, loan: Loan) -> Loan:
        now = _utcnow()
        loan.returned_at = now
        loan.updated_at = now
        self._session.add(loan)
        await self._session.commit()
        await self._session.refresh(loan)
        return loan

    async def undo_return(self, loan: Loan) -> Loan:
        now = _utcnow()
        loan.returned_at = None
        loan.updated_at = now
        self._session.add(loan)
        await self._session.commit()
        await self._session.refresh(loan)
        return loan

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
        conditions = []
        if member_id is not None:
            conditions.append(col(Loan.member_id) == member_id)
        if book_copy_id is not None:
            conditions.append(col(Loan.book_copy_id) == book_copy_id)
        if status is not None:
            now = func.now()
            if status == LoanStatus.active:
                conditions.append(col(Loan.returned_at).is_(None))
                conditions.append(col(Loan.due_date) >= now)
            elif status == LoanStatus.overdue:
                conditions.append(col(Loan.returned_at).is_(None))
                conditions.append(col(Loan.due_date) < now)
            else:  # LoanStatus.returned
                conditions.append(col(Loan.returned_at).isnot(None))

        sort_attr = getattr(Loan, sort_by.value)
        ordered = sort_attr.desc() if order == SortOrder.desc else sort_attr.asc()

        count_stmt = select(func.count(col(Loan.id)))
        if conditions:
            count_stmt = count_stmt.where(*conditions)
        total: int = (await self._session.exec(count_stmt)).one()

        stmt = select(Loan)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(ordered).offset((page - 1) * size).limit(size)
        result = await self._session.exec(stmt)
        return list(result.all()), total
