import uuid
from abc import ABC, abstractmethod
from datetime import datetime

from app.core.sorting import SortOrder
from app.loans.domain.loan_model import Loan, LoanCreate, LoanStatus, SortBy


class LoanRepository(ABC):
    @abstractmethod
    async def create(self, data: LoanCreate, due_date: datetime) -> Loan: ...

    @abstractmethod
    async def get_by_id(self, loan_id: uuid.UUID) -> Loan | None: ...

    @abstractmethod
    async def get_filtered(
        self,
        member_id: uuid.UUID | None,
        book_copy_id: uuid.UUID | None,
        status: LoanStatus | None,
        sort_by: SortBy,
        order: SortOrder,
        page: int,
        size: int,
    ) -> tuple[list[Loan], int]: ...

    @abstractmethod
    async def mark_returned(self, loan: Loan) -> Loan: ...

    @abstractmethod
    async def undo_return(self, loan: Loan) -> Loan: ...

    @abstractmethod
    async def delete(self, loan: Loan) -> None: ...

    @abstractmethod
    async def count_active_for_member(self, member_id: uuid.UUID) -> int: ...

    @abstractmethod
    async def get_active_for_copy(self, book_copy_id: uuid.UUID) -> Loan | None: ...
