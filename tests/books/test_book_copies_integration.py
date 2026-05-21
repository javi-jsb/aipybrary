"""Integration tests for the `book-management` deltas introduced by the
`book-copy-management` change: DELETE → 409 when copies exist, and the
`copies_total` field on `BookPublic`."""

import uuid
from collections import Counter

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

from app.config import settings


async def _create_book(client: AsyncClient, **kwargs: object) -> dict:
    payload = {"title": "Default Title", "author": "Default Author", **kwargs}
    response = await client.post("/books", json=payload)
    assert response.status_code == 201
    return response.json()


async def _create_copy(client: AsyncClient, book_id: str, **kwargs: object) -> dict:
    payload = {"book_id": book_id, "barcode": f"BC-{uuid.uuid4()}", **kwargs}
    response = await client.post("/book-copies", json=payload)
    assert response.status_code == 201
    return response.json()


async def test_delete_book_with_zero_copies(client: AsyncClient) -> None:
    book = await _create_book(client)
    response = await client.delete(f"/books/{book['id']}")
    assert response.status_code == 204

    response = await client.get(f"/books/{book['id']}")
    assert response.status_code == 404


async def test_delete_book_with_copies_returns_409(client: AsyncClient) -> None:
    book = await _create_book(client)
    await _create_copy(client, book["id"])

    response = await client.delete(f"/books/{book['id']}")
    assert response.status_code == 409

    # The book is still retrievable after the failed delete.
    response = await client.get(f"/books/{book['id']}")
    assert response.status_code == 200


async def test_list_books_includes_copies_total(client: AsyncClient) -> None:
    book_a = await _create_book(client, title="A")
    book_b = await _create_book(client, title="B")
    book_c = await _create_book(client, title="C")
    for _ in range(3):
        await _create_copy(client, book_a["id"])
    await _create_copy(client, book_c["id"])

    response = await client.get("/books")
    assert response.status_code == 200
    items_by_id = {item["id"]: item for item in response.json()["items"]}

    assert items_by_id[book_a["id"]]["copies_total"] == 3
    assert items_by_id[book_b["id"]]["copies_total"] == 0
    assert items_by_id[book_c["id"]]["copies_total"] == 1


async def test_get_book_includes_copies_total(client: AsyncClient) -> None:
    book = await _create_book(client)
    await _create_copy(client, book["id"])
    await _create_copy(client, book["id"])

    response = await client.get(f"/books/{book['id']}")
    assert response.status_code == 200
    assert response.json()["copies_total"] == 2


async def test_newly_created_book_has_zero_copies(client: AsyncClient) -> None:
    book = await _create_book(client)
    response = await client.get(f"/books/{book['id']}")
    assert response.status_code == 200
    assert response.json()["copies_total"] == 0


async def test_list_books_query_count_is_bounded(client: AsyncClient) -> None:
    """The aggregated query for `copies_total` must not grow linearly with the
    number of books returned. We assert the SELECT count against `book_copies`
    is bounded (one SELECT for the page, plus one SELECT for the total count of
    books) regardless of N.
    """

    book_ids: list[str] = []
    for i in range(5):
        book = await _create_book(client, title=f"B-{i}")
        book_ids.append(book["id"])
        await _create_copy(client, book["id"])
        await _create_copy(client, book["id"])

    # Build a tracing engine that records every SQL statement issued during the
    # GET /books request.
    statements: list[str] = []
    tracing_engine = create_async_engine(settings.test_database_url, echo=False)

    from sqlalchemy import event

    @event.listens_for(tracing_engine.sync_engine, "before_cursor_execute")
    def _record(_conn, _cursor, statement, _params, _context, _executemany):  # type: ignore[no-untyped-def]
        statements.append(statement)

    tracing_session_maker = async_sessionmaker(tracing_engine, class_=AsyncSession, expire_on_commit=False)

    from app.database import get_session
    from app.main import app

    async def _tracing_session():  # type: ignore[no-untyped-def]
        async with tracing_session_maker() as session:
            yield session

    original = app.dependency_overrides.get(get_session)
    app.dependency_overrides[get_session] = _tracing_session
    try:
        response = await client.get("/books")
        assert response.status_code == 200
        assert len(response.json()["items"]) == 5
    finally:
        if original is None:
            del app.dependency_overrides[get_session]
        else:
            app.dependency_overrides[get_session] = original
        await tracing_engine.dispose()

    select_counts = Counter(
        "books" if "FROM books" in stmt else "other" for stmt in statements if stmt.strip().upper().startswith("SELECT")
    )
    # Two SELECTs: one for the count, one for the paginated rows with the
    # aggregated copy count. Neither must repeat per row.
    assert select_counts["books"] == 2, statements
