import uuid

from httpx import AsyncClient

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _create_member(client: AsyncClient, **kwargs: object) -> dict:
    payload = {
        "full_name": "Default Name",
        "email": f"user-{uuid.uuid4()}@example.com",
        **kwargs,
    }
    response = await client.post("/members", json=payload)
    assert response.status_code == 201
    return response.json()


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def test_create_member(client: AsyncClient) -> None:
    response = await client.post("/members", json={"full_name": "Ada Lovelace", "email": "ada@example.com"})
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "Ada Lovelace"
    assert data["email"] == "ada@example.com"
    assert data["status"] == "active"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_create_member_with_explicit_status(client: AsyncClient) -> None:
    response = await client.post(
        "/members",
        json={"full_name": "Grace", "email": "grace@example.com", "status": "suspended"},
    )
    assert response.status_code == 201
    assert response.json()["status"] == "suspended"


async def test_create_member_missing_required_fields(client: AsyncClient) -> None:
    response = await client.post("/members", json={"full_name": "No Email"})
    assert response.status_code == 422


async def test_create_member_invalid_status(client: AsyncClient) -> None:
    response = await client.post(
        "/members",
        json={"full_name": "Bad", "email": "bad@example.com", "status": "banned"},
    )
    assert response.status_code == 422


async def test_create_member_duplicate_email(client: AsyncClient) -> None:
    await _create_member(client, email="dup@example.com")
    response = await client.post("/members", json={"full_name": "Other", "email": "dup@example.com"})
    assert response.status_code == 409


async def test_create_member_invalid_email(client: AsyncClient) -> None:
    response = await client.post("/members", json={"full_name": "Bad", "email": "not-an-email"})
    assert response.status_code == 422


async def test_create_member_normalizes_email(client: AsyncClient) -> None:
    response = await client.post("/members", json={"full_name": "Ada", "email": "  Ada@Example.COM  "})
    assert response.status_code == 201
    assert response.json()["email"] == "ada@example.com"


async def test_create_member_duplicate_email_is_case_insensitive(client: AsyncClient) -> None:
    await _create_member(client, email="case@example.com")
    response = await client.post("/members", json={"full_name": "Other", "email": "CASE@example.com"})
    assert response.status_code == 409


# ---------------------------------------------------------------------------
# Read single
# ---------------------------------------------------------------------------


async def test_get_member(client: AsyncClient) -> None:
    data = await _create_member(client, full_name="Get Me")
    response = await client.get(f"/members/{data['id']}")
    assert response.status_code == 200
    assert response.json()["full_name"] == "Get Me"


async def test_get_member_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/members/{uuid.uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# List — pagination
# ---------------------------------------------------------------------------


async def test_list_members_empty(client: AsyncClient) -> None:
    response = await client.get("/members")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0


async def test_list_members_default_pagination(client: AsyncClient) -> None:
    for _ in range(25):
        await _create_member(client)

    response = await client.get("/members")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 20
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["size"] == 20
    assert data["pages"] == 2


async def test_list_members_second_page(client: AsyncClient) -> None:
    for _ in range(25):
        await _create_member(client)

    response = await client.get("/members?page=2&size=20")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2


async def test_list_members_page_zero_rejected(client: AsyncClient) -> None:
    response = await client.get("/members?page=0")
    assert response.status_code == 422


async def test_list_members_size_over_max_rejected(client: AsyncClient) -> None:
    response = await client.get("/members?size=101")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List — filtering
# ---------------------------------------------------------------------------


async def test_list_members_filter_by_full_name(client: AsyncClient) -> None:
    await _create_member(client, full_name="Ana Garcia")
    await _create_member(client, full_name="Other Person")

    response = await client.get("/members?full_name=garcia")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["full_name"] == "Ana Garcia"


async def test_list_members_filter_by_email(client: AsyncClient) -> None:
    await _create_member(client, email="alice@corp.example")
    await _create_member(client, email="bob@other.test")

    response = await client.get("/members?email=corp.example")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "alice@corp.example"


async def test_list_members_filter_combined(client: AsyncClient) -> None:
    await _create_member(client, full_name="Ana García", email="ana@corp.example")
    await _create_member(client, full_name="Ana García", email="ana2@other.test")
    await _create_member(client, full_name="Bob", email="bob@corp.example")

    response = await client.get("/members?full_name=ana&email=corp.example")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["email"] == "ana@corp.example"


async def test_list_members_filter_no_matches(client: AsyncClient) -> None:
    await _create_member(client)

    response = await client.get("/members?full_name=zzznomatch")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


async def test_list_members_filter_by_status(client: AsyncClient) -> None:
    await _create_member(client, full_name="Active One")
    await _create_member(client, full_name="Suspended One", status="suspended")

    response = await client.get("/members?status=suspended")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["full_name"] == "Suspended One"


async def test_list_members_filter_by_status_combined_with_name(client: AsyncClient) -> None:
    await _create_member(client, full_name="Ana", status="suspended")
    await _create_member(client, full_name="Ana", status="active")
    await _create_member(client, full_name="Bob", status="suspended")

    response = await client.get("/members?full_name=ana&status=suspended")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["status"] == "suspended"


async def test_list_members_invalid_status_rejected(client: AsyncClient) -> None:
    response = await client.get("/members?status=banned")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List — sorting
# ---------------------------------------------------------------------------


async def test_list_members_sort_by_full_name_asc(client: AsyncClient) -> None:
    await _create_member(client, full_name="Zebra")
    await _create_member(client, full_name="Apple")
    await _create_member(client, full_name="Mango")

    response = await client.get("/members?sort_by=full_name&order=asc")
    assert response.status_code == 200
    names = [item["full_name"] for item in response.json()["items"]]
    assert names == sorted(names)


async def test_list_members_default_sort_created_at_desc(client: AsyncClient) -> None:
    first = await _create_member(client, full_name="First")
    second = await _create_member(client, full_name="Second")

    response = await client.get("/members")
    assert response.status_code == 200
    items = response.json()["items"]
    assert items[0]["id"] == second["id"]
    assert items[1]["id"] == first["id"]


async def test_list_members_sort_by_status_asc(client: AsyncClient) -> None:
    await _create_member(client, full_name="S", status="suspended")
    await _create_member(client, full_name="A", status="active")

    response = await client.get("/members?sort_by=status&order=asc")
    assert response.status_code == 200
    statuses = [item["status"] for item in response.json()["items"]]
    assert statuses == ["active", "suspended"]


async def test_list_members_sort_by_email_asc(client: AsyncClient) -> None:
    await _create_member(client, full_name="Z", email="z@example.com")
    await _create_member(client, full_name="A", email="a@example.com")

    response = await client.get("/members?sort_by=email&order=asc")
    assert response.status_code == 200
    emails = [item["email"] for item in response.json()["items"]]
    assert emails == sorted(emails)


async def test_list_members_invalid_sort_by_rejected(client: AsyncClient) -> None:
    response = await client.get("/members?sort_by=invalid")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


async def test_update_member(client: AsyncClient) -> None:
    data = await _create_member(client, full_name="Old")
    response = await client.patch(f"/members/{data['id']}", json={"full_name": "New"})
    assert response.status_code == 200
    result = response.json()
    assert result["full_name"] == "New"
    assert result["email"] == data["email"]


async def test_update_member_suspend(client: AsyncClient) -> None:
    data = await _create_member(client)
    response = await client.patch(f"/members/{data['id']}", json={"status": "suspended"})
    assert response.status_code == 200
    assert response.json()["status"] == "suspended"


async def test_update_member_invalid_status(client: AsyncClient) -> None:
    data = await _create_member(client)
    response = await client.patch(f"/members/{data['id']}", json={"status": "banned"})
    assert response.status_code == 422


async def test_update_member_not_found(client: AsyncClient) -> None:
    response = await client.patch(f"/members/{uuid.uuid4()}", json={"full_name": "X"})
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


async def test_delete_member(client: AsyncClient) -> None:
    data = await _create_member(client, full_name="Delete Me")
    response = await client.delete(f"/members/{data['id']}")
    assert response.status_code == 204

    response = await client.get(f"/members/{data['id']}")
    assert response.status_code == 404


async def test_delete_member_not_found(client: AsyncClient) -> None:
    response = await client.delete(f"/members/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_delete_member_with_loans_conflict(client: AsyncClient) -> None:
    member = await _create_member(client, full_name="Borrower")
    book = await client.post("/books", json={"title": "T", "author": "A"})
    copy = await client.post(
        "/book-copies",
        json={"book_id": book.json()["id"], "barcode": f"BC-{uuid.uuid4()}"},
    )
    borrow = await client.post(
        "/loans",
        json={"member_id": member["id"], "book_copy_id": copy.json()["id"]},
    )
    assert borrow.status_code == 201

    response = await client.delete(f"/members/{member['id']}")
    assert response.status_code == 409

    # The member is still there after the blocked delete.
    assert (await client.get(f"/members/{member['id']}")).status_code == 200
