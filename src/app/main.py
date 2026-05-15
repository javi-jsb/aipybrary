from fastapi import FastAPI

from app.books.infrastructure.book_router import router as books_router

app = FastAPI(title="aipybrary")
app.include_router(books_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
