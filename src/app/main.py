from fastapi import Depends, FastAPI

from app.book_copies.infrastructure.book_copy_router import router as book_copies_router
from app.books.infrastructure.book_router import router as books_router
from app.loans.infrastructure.loan_router import router as loans_router
from app.members.infrastructure.member_router import router as members_router
from app.users.infrastructure.auth_router import get_current_user
from app.users.infrastructure.auth_router import router as auth_router

app = FastAPI(title="aipybrary")

app.include_router(auth_router)

_auth_gate = [Depends(get_current_user)]
app.include_router(books_router, dependencies=_auth_gate)
app.include_router(book_copies_router, dependencies=_auth_gate)
app.include_router(members_router, dependencies=_auth_gate)
app.include_router(loans_router, dependencies=_auth_gate)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
