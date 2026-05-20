import uuid

from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_book(client: AsyncClient, **kwargs: object) -> dict:
    payload = {"title": "Default Title", "author": "Default Author", **kwargs}
    response = await client.post("/books", json=payload)
    assert response.status_code == 201
    return response.json()


async def _create_copy(client: AsyncClient, book_id: str, **kwargs: object) -> dict:
    payload = {
        "book_id": book_id,
        "barcode": f"BC-{uuid.uuid4()}",
        **kwargs,
    }
    response = await client.post("/book-copies", json=payload)
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def test_create_book_copy(client: AsyncClient) -> None:
    book = await _create_book(client)
    response = await client.post(
        "/book-copies",
        json={"book_id": book["id"], "barcode": "ABC-001", "location": "shelf-A"},
    )
    assert response.status_code == 201
    data = response.json()
    assert data["book_id"] == book["id"]
    assert data["barcode"] == "ABC-001"
    assert data["location"] == "shelf-A"
    assert data["notes"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_create_book_copy_missing_required_fields(client: AsyncClient) -> None:
    response = await client.post("/book-copies", json={"barcode": "X"})
    assert response.status_code == 422

    book = await _create_book(client)
    response = await client.post("/book-copies", json={"book_id": book["id"]})
    assert response.status_code == 422


async def test_create_book_copy_nonexistent_book(client: AsyncClient) -> None:
    response = await client.post(
        "/book-copies", json={"book_id": str(uuid.uuid4()), "barcode": "ABC"}
    )
    assert response.status_code == 422


async def test_create_book_copy_duplicate_barcode(client: AsyncClient) -> None:
    book = await _create_book(client)
    await _create_copy(client, book["id"], barcode="DUPE-1")
    response = await client.post("/book-copies", json={"book_id": book["id"], "barcode": "DUPE-1"})
    assert response.status_code == 409


async def test_create_book_copy_invalid_book_id(client: AsyncClient) -> None:
    response = await client.post("/book-copies", json={"book_id": "not-a-uuid", "barcode": "X"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Read single
# ---------------------------------------------------------------------------


async def test_get_book_copy(client: AsyncClient) -> None:
    book = await _create_book(client)
    created = await _create_copy(client, book["id"], barcode="GET-1")
    response = await client.get(f"/book-copies/{created['id']}")
    assert response.status_code == 200
    assert response.json()["barcode"] == "GET-1"


async def test_get_book_copy_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/book-copies/{uuid.uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# List — pagination
# ---------------------------------------------------------------------------


async def test_list_book_copies_empty(client: AsyncClient) -> None:
    response = await client.get("/book-copies")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0


async def test_list_book_copies_default_pagination(client: AsyncClient) -> None:
    book = await _create_book(client)
    for _ in range(25):
        await _create_copy(client, book["id"])

    response = await client.get("/book-copies")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 20
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["size"] == 20
    assert data["pages"] == 2


async def test_list_book_copies_second_page(client: AsyncClient) -> None:
    book = await _create_book(client)
    for _ in range(25):
        await _create_copy(client, book["id"])

    response = await client.get("/book-copies?page=2&size=20")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2


async def test_list_book_copies_page_zero_rejected(client: AsyncClient) -> None:
    response = await client.get("/book-copies?page=0")
    assert response.status_code == 422


async def test_list_book_copies_size_over_max_rejected(client: AsyncClient) -> None:
    response = await client.get("/book-copies?size=101")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List — filtering
# ---------------------------------------------------------------------------


async def test_list_book_copies_filter_by_book_id(client: AsyncClient) -> None:
    book_a = await _create_book(client, title="A")
    book_b = await _create_book(client, title="B")
    await _create_copy(client, book_a["id"])
    await _create_copy(client, book_a["id"])
    await _create_copy(client, book_a["id"])
    await _create_copy(client, book_b["id"])

    response = await client.get(f"/book-copies?book_id={book_a['id']}")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3


async def test_list_book_copies_filter_by_barcode(client: AsyncClient) -> None:
    book = await _create_book(client)
    await _create_copy(client, book["id"], barcode="ABC-target-1")
    await _create_copy(client, book["id"], barcode="zzz-other-1")

    response = await client.get("/book-copies?barcode=target")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["barcode"] == "ABC-target-1"


async def test_list_book_copies_filter_by_location(client: AsyncClient) -> None:
    book = await _create_book(client)
    await _create_copy(client, book["id"], location="floor-2-shelf-A")
    await _create_copy(client, book["id"], location="floor-1-shelf-B")

    response = await client.get("/book-copies?location=floor-2")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


async def test_list_book_copies_filter_invalid_book_id(client: AsyncClient) -> None:
    response = await client.get("/book-copies?book_id=not-a-uuid")
    assert response.status_code == 422


async def test_list_book_copies_filter_combined(client: AsyncClient) -> None:
    book_a = await _create_book(client, title="A")
    book_b = await _create_book(client, title="B")
    await _create_copy(client, book_a["id"], location="shelf-A")
    await _create_copy(client, book_a["id"], location="shelf-B")
    await _create_copy(client, book_b["id"], location="shelf-A")

    response = await client.get(f"/book-copies?book_id={book_a['id']}&location=shelf-A")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1


async def test_list_book_copies_filter_no_matches(client: AsyncClient) -> None:
    book = await _create_book(client)
    await _create_copy(client, book["id"], barcode="real-one")

    response = await client.get("/book-copies?barcode=zzznomatch")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


# ---------------------------------------------------------------------------
# List — sorting
# ---------------------------------------------------------------------------


async def test_list_book_copies_sort_by_barcode_asc(client: AsyncClient) -> None:
    book = await _create_book(client)
    await _create_copy(client, book["id"], barcode="C-z")
    await _create_copy(client, book["id"], barcode="A-x")
    await _create_copy(client, book["id"], barcode="B-y")

    response = await client.get("/book-copies?sort_by=barcode&order=asc")
    assert response.status_code == 200
    barcodes = [item["barcode"] for item in response.json()["items"]]
    assert barcodes == sorted(barcodes)


async def test_list_book_copies_default_sort_created_at_desc(client: AsyncClient) -> None:
    book = await _create_book(client)
    first = await _create_copy(client, book["id"], barcode="FIRST")
    second = await _create_copy(client, book["id"], barcode="SECOND")

    response = await client.get("/book-copies")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["id"] == second["id"]
    assert items[1]["id"] == first["id"]


async def test_list_book_copies_invalid_sort_by_rejected(client: AsyncClient) -> None:
    response = await client.get("/book-copies?sort_by=invalid")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


async def test_update_book_copy_partial(client: AsyncClient) -> None:
    book = await _create_book(client)
    created = await _create_copy(client, book["id"], barcode="OLD", location="shelf-A")
    response = await client.patch(f"/book-copies/{created['id']}", json={"barcode": "NEW"})
    assert response.status_code == 200
    data = response.json()
    assert data["barcode"] == "NEW"
    assert data["location"] == "shelf-A"


async def test_update_book_copy_not_found(client: AsyncClient) -> None:
    response = await client.patch(f"/book-copies/{uuid.uuid4()}", json={"barcode": "X"})
    assert response.status_code == 404


async def test_update_book_copy_duplicate_barcode(client: AsyncClient) -> None:
    book = await _create_book(client)
    first = await _create_copy(client, book["id"], barcode="FIRST-BC")
    second = await _create_copy(client, book["id"], barcode="SECOND-BC")

    response = await client.patch(
        f"/book-copies/{second['id']}", json={"barcode": first["barcode"]}
    )
    assert response.status_code == 409


async def test_update_book_copy_rejects_book_id(client: AsyncClient) -> None:
    book = await _create_book(client)
    created = await _create_copy(client, book["id"])
    other = await _create_book(client, title="Other")

    response = await client.patch(f"/book-copies/{created['id']}", json={"book_id": other["id"]})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


async def test_delete_book_copy(client: AsyncClient) -> None:
    book = await _create_book(client)
    created = await _create_copy(client, book["id"])
    response = await client.delete(f"/book-copies/{created['id']}")
    assert response.status_code == 204

    response = await client.get(f"/book-copies/{created['id']}")
    assert response.status_code == 404


async def test_delete_book_copy_not_found(client: AsyncClient) -> None:
    response = await client.delete(f"/book-copies/{uuid.uuid4()}")
    assert response.status_code == 404
