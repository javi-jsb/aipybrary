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


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


async def test_create_book(client: AsyncClient) -> None:
    response = await client.post("/books", json={"title": "Test Book", "author": "Test Author"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Book"
    assert data["author"] == "Test Author"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


async def test_create_book_with_optional_fields(client: AsyncClient) -> None:
    response = await client.post(
        "/books",
        json={
            "title": "Full Book",
            "author": "Full Author",
            "isbn": "9780060934347",
            "publication_year": 2024,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["isbn"] == "9780060934347"
    assert data["publication_year"] == 2024


async def test_create_book_missing_required_fields(client: AsyncClient) -> None:
    response = await client.post("/books", json={"title": "No Author"})
    assert response.status_code == 422


async def test_create_book_with_synopsis(client: AsyncClient) -> None:
    response = await client.post(
        "/books",
        json={"title": "With Synopsis", "author": "Author", "synopsis": "A great story."},
    )
    assert response.status_code == 201
    assert response.json()["synopsis"] == "A great story."


async def test_create_book_without_synopsis(client: AsyncClient) -> None:
    response = await client.post("/books", json={"title": "No Synopsis", "author": "Author"})
    assert response.status_code == 201
    assert response.json()["synopsis"] is None


# ---------------------------------------------------------------------------
# Read single
# ---------------------------------------------------------------------------


async def test_get_book(client: AsyncClient) -> None:
    data = await _create_book(client, title="Get Me")
    response = await client.get(f"/books/{data['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me"


async def test_get_book_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/books/{uuid.uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# List — pagination (task 8.2)
# ---------------------------------------------------------------------------


async def test_list_books_empty(client: AsyncClient) -> None:
    response = await client.get("/books")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0
    assert data["pages"] == 0


async def test_list_books_default_pagination(client: AsyncClient) -> None:
    for i in range(25):
        await _create_book(client, title=f"Book {i:02d}")

    response = await client.get("/books")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 20
    assert data["total"] == 25
    assert data["page"] == 1
    assert data["size"] == 20
    assert data["pages"] == 2


async def test_list_books_second_page(client: AsyncClient) -> None:
    for i in range(25):
        await _create_book(client, title=f"Book {i:02d}")

    response = await client.get("/books?page=2&size=20")
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 5
    assert data["page"] == 2


async def test_list_books_page_zero_rejected(client: AsyncClient) -> None:
    response = await client.get("/books?page=0")
    assert response.status_code == 422


async def test_list_books_size_over_max_rejected(client: AsyncClient) -> None:
    response = await client.get("/books?size=101")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# List — filtering (task 8.3)
# ---------------------------------------------------------------------------


async def test_list_books_filter_by_author(client: AsyncClient) -> None:
    await _create_book(client, title="Ficciones", author="Jorge Luis Borges")
    await _create_book(client, title="Other Book", author="Other Author")

    response = await client.get("/books?author=borges")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["author"] == "Jorge Luis Borges"


async def test_list_books_filter_by_title(client: AsyncClient) -> None:
    await _create_book(client, title="Don Quixote")
    await _create_book(client, title="Other Book")

    response = await client.get("/books?title=quix")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "Don Quixote"


async def test_list_books_filter_combined(client: AsyncClient) -> None:
    await _create_book(client, title="One Hundred Years of Solitude", author="Gabriel García Márquez")
    await _create_book(client, title="Love in the Time of Cholera", author="Gabriel García Márquez")
    await _create_book(client, title="Solitude", author="Another Author")

    response = await client.get("/books?author=gabriel&title=solitude")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "One Hundred Years of Solitude"


async def test_list_books_filter_no_matches(client: AsyncClient) -> None:
    await _create_book(client)

    response = await client.get("/books?author=zzznomatch")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


# ---------------------------------------------------------------------------
# List — sorting (task 8.4)
# ---------------------------------------------------------------------------


async def test_list_books_sort_by_title_asc(client: AsyncClient) -> None:
    await _create_book(client, title="Zebra")
    await _create_book(client, title="Apple")
    await _create_book(client, title="Mango")

    response = await client.get("/books?sort_by=title&order=asc")
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["items"]]
    assert titles == sorted(titles)


async def test_list_books_default_sort_created_at_desc(client: AsyncClient) -> None:
    first = await _create_book(client, title="First")
    second = await _create_book(client, title="Second")

    response = await client.get("/books")
    assert response.status_code == 200
    items = response.json()["items"]
    # newest first
    assert items[0]["id"] == second["id"]
    assert items[1]["id"] == first["id"]


async def test_list_books_invalid_sort_by_rejected(client: AsyncClient) -> None:
    response = await client.get("/books?sort_by=invalid")
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


async def test_update_book(client: AsyncClient) -> None:
    data = await _create_book(client, title="Old")
    response = await client.patch(f"/books/{data['id']}", json={"title": "New"})
    assert response.status_code == 200
    result = response.json()
    assert result["title"] == "New"
    assert result["author"] == "Default Author"


async def test_update_book_not_found(client: AsyncClient) -> None:
    response = await client.patch(f"/books/{uuid.uuid4()}", json={"title": "X"})
    assert response.status_code == 404


async def test_update_book_with_valid_isbn(client: AsyncClient) -> None:
    data = await _create_book(client)
    response = await client.patch(f"/books/{data['id']}", json={"isbn": "0-306-40615-2"})
    assert response.status_code == 200
    assert response.json()["isbn"] == "0306406152"


async def test_update_book_with_invalid_isbn(client: AsyncClient) -> None:
    data = await _create_book(client)
    response = await client.patch(f"/books/{data['id']}", json={"isbn": "9780000000000"})
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------


async def test_delete_book(client: AsyncClient) -> None:
    data = await _create_book(client, title="Delete Me")
    response = await client.delete(f"/books/{data['id']}")
    assert response.status_code == 204

    response = await client.get(f"/books/{data['id']}")
    assert response.status_code == 404


async def test_delete_book_not_found(client: AsyncClient) -> None:
    response = await client.delete(f"/books/{uuid.uuid4()}")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# Duplicate ISBN (409)
# ---------------------------------------------------------------------------


async def test_create_book_duplicate_isbn(client: AsyncClient) -> None:
    await _create_book(client, isbn="9780060934347")
    response = await client.post(
        "/books",
        json={"title": "Other", "author": "Other", "isbn": "9780060934347"},
    )
    assert response.status_code == 409


async def test_update_book_duplicate_isbn(client: AsyncClient) -> None:
    await _create_book(client, title="First", isbn="9780060934347")
    second = await _create_book(client, title="Second", isbn="0306406152")

    response = await client.patch(f"/books/{second['id']}", json={"isbn": "9780060934347"})
    assert response.status_code == 409


async def test_create_books_with_distinct_isbns(client: AsyncClient) -> None:
    first = await _create_book(client, isbn="9780060934347")
    second = await _create_book(client, isbn="0306406152")
    assert first["isbn"] == "9780060934347"
    assert second["isbn"] == "0306406152"


async def test_create_books_without_isbn_allows_multiple(client: AsyncClient) -> None:
    first = await _create_book(client, title="No ISBN A")
    second = await _create_book(client, title="No ISBN B")
    assert first["isbn"] is None
    assert second["isbn"] is None
