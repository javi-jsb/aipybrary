"""Seed the database with example books. Idempotent — skips if books already exist."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlmodel import select  # noqa: E402

from app.books.domain.book_model import Book, BookCreate  # noqa: E402
from app.database import async_session  # noqa: E402

SAMPLE_BOOKS = [
    BookCreate(
        title="Don Quixote",
        author="Miguel de Cervantes",
        isbn="9780060934347",
        publication_year=1605,
    ),
    BookCreate(
        title="One Hundred Years of Solitude",
        author="Gabriel García Márquez",
        isbn="9780060883287",
        publication_year=1967,
    ),
    BookCreate(
        title="The Shadow of the Wind",
        author="Carlos Ruiz Zafón",
        isbn="9780143034902",
        publication_year=2001,
    ),
    BookCreate(
        title="Rayuela",
        author="Julio Cortázar",
        isbn="9788437604572",
        publication_year=1963,
    ),
    BookCreate(
        title="Ficciones",
        author="Jorge Luis Borges",
        isbn="9780802130303",
        publication_year=1944,
    ),
]


async def seed() -> None:
    async with async_session() as session:
        result = await session.exec(select(Book).limit(1))
        if result.first() is not None:
            print("Database already contains books — skipping seed.")
            return

        for data in SAMPLE_BOOKS:
            book = Book.model_validate(data)
            session.add(book)

        await session.commit()
        print(f"Seeded {len(SAMPLE_BOOKS)} books.")


if __name__ == "__main__":
    asyncio.run(seed())
