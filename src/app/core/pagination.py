from math import ceil

from pydantic import computed_field
from sqlmodel import SQLModel


class PaginatedResponse[T](SQLModel):
    items: list[T]
    total: int
    page: int
    size: int

    @computed_field
    @property
    def pages(self) -> int:
        return ceil(self.total / self.size) if self.total > 0 else 0
