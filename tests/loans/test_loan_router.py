import uuid
from datetime import UTC, datetime

from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


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


async def _create_member(client: AsyncClient, **kwargs) -> dict:
    payload = {
        "full_name": "Test Member",
        "email": f"member-{uuid.uuid4()}@example.com",
        **kwargs,
    }
    r = await client.post("/members", json=payload)
    assert r.status_code == 201
    return r.json()


async def _borrow(client: AsyncClient, member_id: str, book_copy_id: str) -> dict:
    r = await client.post("/loans", json={"member_id": member_id, "book_copy_id": book_copy_id})
    assert r.status_code == 201
    return r.json()


# ---------------------------------------------------------------------------
# POST /loans (borrow)
# ---------------------------------------------------------------------------


async def test_borrow_success(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client)
    r = await client.post("/loans", json={"member_id": member["id"], "book_copy_id": copy["id"]})
    assert r.status_code == 201
    data = r.json()
    assert data["member_id"] == member["id"]
    assert data["book_copy_id"] == copy["id"]
    assert data["returned_at"] is None
    assert data["status"] == "active"
    assert "id" in data
    assert "due_date" in data


async def test_borrow_member_not_found(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    r = await client.post("/loans", json={"member_id": str(uuid.uuid4()), "book_copy_id": copy["id"]})
    assert r.status_code == 404


async def test_borrow_suspended_member(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client, status="suspended")
    r = await client.post("/loans", json={"member_id": member["id"], "book_copy_id": copy["id"]})
    assert r.status_code == 422


async def test_borrow_copy_not_found(client: AsyncClient) -> None:
    member = await _create_member(client)
    r = await client.post("/loans", json={"member_id": member["id"], "book_copy_id": str(uuid.uuid4())})
    assert r.status_code == 404


async def test_borrow_copy_already_on_loan(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member1 = await _create_member(client)
    member2 = await _create_member(client)
    await _borrow(client, member1["id"], copy["id"])
    r = await client.post("/loans", json={"member_id": member2["id"], "book_copy_id": copy["id"]})
    assert r.status_code == 409


async def test_borrow_loan_limit_exceeded(client: AsyncClient) -> None:
    book = await _create_book(client)
    member = await _create_member(client)
    # Borrow 3 copies (default limit)
    for _ in range(3):
        copy = await _create_copy(client, book["id"])
        await _borrow(client, member["id"], copy["id"])
    # 4th borrow should fail
    copy4 = await _create_copy(client, book["id"])
    r = await client.post("/loans", json={"member_id": member["id"], "book_copy_id": copy4["id"]})
    assert r.status_code == 422


# ---------------------------------------------------------------------------
# POST /loans/{loan_id}/return
# ---------------------------------------------------------------------------


async def test_return_success(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client)
    loan = await _borrow(client, member["id"], copy["id"])
    r = await client.post(f"/loans/{loan['id']}/return")
    assert r.status_code == 200
    data = r.json()
    assert data["returned_at"] is not None
    assert data["status"] == "returned"


async def test_return_not_found(client: AsyncClient) -> None:
    r = await client.post(f"/loans/{uuid.uuid4()}/return")
    assert r.status_code == 404


async def test_return_already_returned(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client)
    loan = await _borrow(client, member["id"], copy["id"])
    await client.post(f"/loans/{loan['id']}/return")
    r = await client.post(f"/loans/{loan['id']}/return")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /loans/{loan_id}/return (undo return)
# ---------------------------------------------------------------------------


async def test_undo_return_success(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client)
    loan = await _borrow(client, member["id"], copy["id"])
    await client.post(f"/loans/{loan['id']}/return")
    r = await client.delete(f"/loans/{loan['id']}/return")
    assert r.status_code == 200
    data = r.json()
    assert data["returned_at"] is None


async def test_undo_return_not_found(client: AsyncClient) -> None:
    r = await client.delete(f"/loans/{uuid.uuid4()}/return")
    assert r.status_code == 404


async def test_undo_return_not_returned(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client)
    loan = await _borrow(client, member["id"], copy["id"])
    r = await client.delete(f"/loans/{loan['id']}/return")
    assert r.status_code == 409


# ---------------------------------------------------------------------------
# DELETE /loans/{loan_id} (cancel)
# ---------------------------------------------------------------------------


async def test_cancel_success(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client)
    loan = await _borrow(client, member["id"], copy["id"])
    r = await client.delete(f"/loans/{loan['id']}")
    assert r.status_code == 204
    r2 = await client.get(f"/loans/{loan['id']}")
    assert r2.status_code == 404


async def test_cancel_not_found(client: AsyncClient) -> None:
    r = await client.delete(f"/loans/{uuid.uuid4()}")
    assert r.status_code == 404


async def test_cancel_already_returned(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client)
    loan = await _borrow(client, member["id"], copy["id"])
    await client.post(f"/loans/{loan['id']}/return")
    r = await client.delete(f"/loans/{loan['id']}")
    assert r.status_code == 409
    # Loan still exists
    r2 = await client.get(f"/loans/{loan['id']}")
    assert r2.status_code == 200


# ---------------------------------------------------------------------------
# GET /loans/{loan_id}
# ---------------------------------------------------------------------------


async def test_get_loan_found(client: AsyncClient) -> None:
    book = await _create_book(client)
    copy = await _create_copy(client, book["id"])
    member = await _create_member(client)
    loan = await _borrow(client, member["id"], copy["id"])
    r = await client.get(f"/loans/{loan['id']}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == loan["id"]
    assert data["status"] == "active"


async def test_get_loan_not_found(client: AsyncClient) -> None:
    r = await client.get(f"/loans/{uuid.uuid4()}")
    assert r.status_code == 404


# ---------------------------------------------------------------------------
# GET /loans (list)
# ---------------------------------------------------------------------------


async def test_list_loans_empty(client: AsyncClient) -> None:
    r = await client.get("/loans")
    assert r.status_code == 200
    data = r.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0


async def test_list_loans_default_pagination(client: AsyncClient) -> None:
    book = await _create_book(client)
    member = await _create_member(client)
    for _ in range(3):
        copy = await _create_copy(client, book["id"])
        await _borrow(client, member["id"], copy["id"])
    r = await client.get("/loans")
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["size"] == 20


async def test_list_loans_filter_by_member_id(client: AsyncClient) -> None:
    book = await _create_book(client)
    member1 = await _create_member(client)
    member2 = await _create_member(client)
    copy1 = await _create_copy(client, book["id"])
    copy2 = await _create_copy(client, book["id"])
    copy3 = await _create_copy(client, book["id"])
    await _borrow(client, member1["id"], copy1["id"])
    await _borrow(client, member1["id"], copy2["id"])
    await _borrow(client, member2["id"], copy3["id"])
    r = await client.get(f"/loans?member_id={member1['id']}")
    assert r.status_code == 200
    assert r.json()["total"] == 2


async def test_list_loans_filter_by_book_copy_id(client: AsyncClient) -> None:
    book = await _create_book(client)
    member = await _create_member(client)
    copy1 = await _create_copy(client, book["id"])
    copy2 = await _create_copy(client, book["id"])
    await _borrow(client, member["id"], copy1["id"])
    r = await client.get(f"/loans?book_copy_id={copy1['id']}")
    assert r.status_code == 200
    assert r.json()["total"] == 1
    r2 = await client.get(f"/loans?book_copy_id={copy2['id']}")
    assert r2.json()["total"] == 0


async def test_list_loans_filter_by_status_active(client: AsyncClient) -> None:
    book = await _create_book(client)
    member = await _create_member(client)
    copy1 = await _create_copy(client, book["id"])
    copy2 = await _create_copy(client, book["id"])
    loan1 = await _borrow(client, member["id"], copy1["id"])
    loan2 = await _borrow(client, member["id"], copy2["id"])
    await client.post(f"/loans/{loan2['id']}/return")
    r = await client.get("/loans?status=active")
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()["items"]]
    assert loan1["id"] in ids
    assert loan2["id"] not in ids


async def test_list_loans_filter_by_status_returned(client: AsyncClient) -> None:
    book = await _create_book(client)
    member = await _create_member(client)
    copy1 = await _create_copy(client, book["id"])
    copy2 = await _create_copy(client, book["id"])
    loan1 = await _borrow(client, member["id"], copy1["id"])
    loan2 = await _borrow(client, member["id"], copy2["id"])
    await client.post(f"/loans/{loan2['id']}/return")
    r = await client.get("/loans?status=returned")
    assert r.status_code == 200
    ids = [item["id"] for item in r.json()["items"]]
    assert loan2["id"] in ids
    assert loan1["id"] not in ids


async def test_list_loans_filter_by_status_overdue(client: AsyncClient) -> None:
    """Overdue loans cannot be created through the API (due_date is computed from
    now + period_days). We verify the status=overdue filter returns 0 for fresh
    loans and that the filter param is accepted without error."""
    book = await _create_book(client)
    member = await _create_member(client)
    copy = await _create_copy(client, book["id"])
    await _borrow(client, member["id"], copy["id"])
    r = await client.get("/loans?status=overdue")
    assert r.status_code == 200
    assert r.json()["total"] == 0


async def test_list_loans_sort_by_due_date(client: AsyncClient) -> None:
    book = await _create_book(client)
    member = await _create_member(client)
    for _ in range(3):
        copy = await _create_copy(client, book["id"])
        await _borrow(client, member["id"], copy["id"])
    r = await client.get("/loans?sort_by=due_date&order=asc")
    assert r.status_code == 200
    items = r.json()["items"]
    due_dates = [item["due_date"] for item in items]
    assert due_dates == sorted(due_dates)


async def test_list_loans_sort_by_returned_at(client: AsyncClient) -> None:
    book = await _create_book(client)
    member = await _create_member(client)
    copy1 = await _create_copy(client, book["id"])
    copy2 = await _create_copy(client, book["id"])
    loan1 = await _borrow(client, member["id"], copy1["id"])
    loan2 = await _borrow(client, member["id"], copy2["id"])
    await client.post(f"/loans/{loan1['id']}/return")
    await client.post(f"/loans/{loan2['id']}/return")
    r = await client.get("/loans?status=returned&sort_by=returned_at&order=desc")
    assert r.status_code == 200
    items = r.json()["items"]
    assert len(items) == 2
