from fastapi import FastAPI

from app.book_copies.infrastructure.book_copy_router import router as book_copies_router
from app.books.infrastructure.book_router import router as books_router
from app.members.infrastructure.member_router import router as members_router

app = FastAPI(title="aipybrary")
app.include_router(books_router)
app.include_router(book_copies_router)
app.include_router(members_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
