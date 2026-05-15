import uuid

from httpx import AsyncClient


async def test_list_books_empty(client: AsyncClient) -> None:
    response = await client.get("/books")
    assert response.status_code == 200
    assert response.json() == []


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


async def test_get_book(client: AsyncClient) -> None:
    create = await client.post("/books", json={"title": "Get Me", "author": "Author"})
    book_id = create.json()["id"]

    response = await client.get(f"/books/{book_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Get Me"


async def test_get_book_not_found(client: AsyncClient) -> None:
    response = await client.get(f"/books/{uuid.uuid4()}")
    assert response.status_code == 404


async def test_list_books_after_create(client: AsyncClient) -> None:
    await client.post("/books", json={"title": "Book A", "author": "Author A"})
    await client.post("/books", json={"title": "Book B", "author": "Author B"})

    response = await client.get("/books")
    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_update_book(client: AsyncClient) -> None:
    create = await client.post("/books", json={"title": "Old", "author": "Author"})
    book_id = create.json()["id"]

    response = await client.patch(f"/books/{book_id}", json={"title": "New"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "New"
    assert data["author"] == "Author"


async def test_update_book_not_found(client: AsyncClient) -> None:
    response = await client.patch(f"/books/{uuid.uuid4()}", json={"title": "X"})
    assert response.status_code == 404


async def test_delete_book(client: AsyncClient) -> None:
    create = await client.post("/books", json={"title": "Delete Me", "author": "Author"})
    book_id = create.json()["id"]

    response = await client.delete(f"/books/{book_id}")
    assert response.status_code == 204

    response = await client.get(f"/books/{book_id}")
    assert response.status_code == 404


async def test_delete_book_not_found(client: AsyncClient) -> None:
    response = await client.delete(f"/books/{uuid.uuid4()}")
    assert response.status_code == 404
