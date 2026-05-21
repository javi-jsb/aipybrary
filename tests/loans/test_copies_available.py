import uuid

from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_book(client: AsyncClient, **kwargs) -> dict:
    payload = {"title": "Default Title", "author": "Default Author", **kwargs}
    r = await client.post("/books", json=payload)
    assert r.status_code == 201
    return r.json()


async def _create_copy(client: AsyncClient, book_id: str, **kwargs) -> dict:
    payload = {"book_id": book_id, "barcode": f"BC-{uuid.uuid4()}", **kwargs}
    r = await client.post("/book-copies", json=payload)
    assert r.status_code == 201
    return r.json()


async def _create_member(client: AsyncClient) -> dict:
    payload = {"full_name": "Test User", "email": f"u-{uuid.uuid4()}@example.com"}
    r = await client.post("/members", json=payload)
    assert r.status_code == 201
    return r.json()


async def _borrow(client: AsyncClient, member_id: str, book_copy_id: str) -> dict:
    r = await client.post("/loans", json={"member_id": member_id, "book_copy_id": book_copy_id})
    assert r.status_code == 201
    return r.json()


# ---------------------------------------------------------------------------
# GET /books — copies_available
# ---------------------------------------------------------------------------


async def test_new_book_has_zero_copies_available(client: AsyncClient) -> None:
    book = await _create_book(client)
    r = await client.get(f"/books/{book['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["copies_total"] == 0
    assert data["copies_available"] == 0


async def test_copies_available_decreases_on_borrow(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy1 = await _create_copy(client, book["id"])
    copy2 = await _create_copy(client, book["id"])
    await _create_copy(client, book["id"])
    member = await _create_member(client)
    # Borrow 2 of 3 copies
    await _borrow(client, member["id"], copy1["id"])
    await _borrow(client, member["id"], copy2["id"])
    r = await client.get(f"/books/{book['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["copies_total"] == 3
    assert data["copies_available"] == 1


async def test_copies_available_increases_on_return(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client)
    loan = await _borrow(client, member["id"], copy["id"])
    # Before return: 0 available
    r = await client.get(f"/books/{book['id']}")
    assert r.json()["copies_available"] == 0
    # After return: 1 available
    await client.post(f"/loans/{loan['id']}/return")
    r = await client.get(f"/books/{book['id']}")
    assert r.json()["copies_available"] == 1


async def test_copies_available_in_list_books(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy1 = await _create_copy(client, book["id"])
    await _create_copy(client, book["id"])
    member = await _create_member(client)
    await _borrow(client, member["id"], copy1["id"])
    r = await client.get("/books")
    assert r.status_code == 200
    items = {item["id"]: item for item in r.json()["items"]}
    assert items[book["id"]]["copies_total"] == 2
    assert items[book["id"]]["copies_available"] == 1


async def test_returned_loan_counts_as_available(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client)
    loan = await _borrow(client, member["id"], copy["id"])
    await client.post(f"/loans/{loan['id']}/return")
    r = await client.get(f"/books/{book['id']}")
    assert r.json()["copies_available"] == 1
