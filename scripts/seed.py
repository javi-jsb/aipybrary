"""Seed the database with example books. Idempotent — skips if books already exist."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlmodel import select  # noqa: E402

from app.books.domain.book_model import Book, BookCreate  # noqa: E402
from app.database import async_session  # noqa: E402

SAMPLE_BOOKS = [
    # Hispanic literature
    BookCreate(
        title="Don Quixote",
        author="Miguel de Cervantes",
        isbn="9780060934347",
        publication_year=1605,
        synopsis=(
            "The adventures of an idealistic nobleman who believes himself to be a knight-errant."
        ),
    ),
    BookCreate(
        title="One Hundred Years of Solitude",
        author="Gabriel García Márquez",
        isbn="9780060883287",
        publication_year=1967,
        synopsis="Seven generations of the Buendía family in the mythical town of Macondo.",
    ),
    BookCreate(
        title="Rayuela",
        author="Julio Cortázar",
        isbn="9788437604572",
        publication_year=1963,
        synopsis="An experimental novel that can be read in multiple orders.",
    ),
    BookCreate(
        title="Ficciones",
        author="Jorge Luis Borges",
        isbn="9780802130303",
        publication_year=1944,
    ),
    BookCreate(
        title="The Shadow of the Wind",
        author="Carlos Ruiz Zafón",
        isbn="9780143034902",
        publication_year=2001,
        synopsis=(
            "A boy discovers a mysterious book whose author seems to have been erased from history."
        ),
    ),
    # European literature
    BookCreate(
        title="Crime and Punishment",
        author="Fyodor Dostoevsky",
        isbn="9780140449136",
        publication_year=1866,
        synopsis=(
            "A young student commits a murder and wrestles with guilt and redemption"
            " in St. Petersburg."
        ),
    ),
    BookCreate(
        title="The Trial",
        author="Franz Kafka",
        publication_year=1925,
        synopsis=(
            "Josef K. is arrested and prosecuted by a remote, inaccessible authority"
            " for an unstated crime."
        ),
    ),
    BookCreate(
        title="Middlemarch",
        author="George Eliot",
        isbn="9780141439549",
        publication_year=1871,
    ),
    BookCreate(
        title="Steppenwolf",
        author="Hermann Hesse",
    ),
    # Asian literature
    BookCreate(
        title="The Sound of Waves",
        author="Yukio Mishima",
        isbn="9780679752738",
        publication_year=1954,
        synopsis="A simple, romantic story of two young people on a remote Japanese island.",
    ),
    BookCreate(
        title="Snow Country",
        author="Yasunari Kawabata",
        isbn="9780679761075",
        publication_year=1956,
    ),
    BookCreate(
        title="The God of Small Things",
        author="Arundhati Roy",
        publication_year=1997,
        synopsis=(
            "Twins in Kerala, India, whose lives are changed by the events of one day"
            " in December 1969."
        ),
    ),
    # North American literature
    BookCreate(
        title="Beloved",
        author="Toni Morrison",
        isbn="9781400033416",
        publication_year=1987,
        synopsis=(
            "A former enslaved woman is haunted by the ghost of her dead daughter"
            " in post-Civil War Ohio."
        ),
    ),
    BookCreate(
        title="Blood Meridian",
        author="Cormac McCarthy",
        publication_year=1985,
    ),
    BookCreate(
        title="The Left Hand of Darkness",
        author="Ursula K. Le Guin",
        isbn="9780441478125",
        publication_year=1969,
        synopsis=(
            "An envoy from an interplanetary league visits a world whose inhabitants"
            " have no fixed gender."
        ),
    ),
    # African literature
    BookCreate(
        title="Things Fall Apart",
        author="Chinua Achebe",
        isbn="9780385474542",
        publication_year=1958,
        synopsis="The story of Okonkwo, a leader in Igboland, and the arrival of colonialism.",
    ),
    BookCreate(
        title="So Long a Letter",
        author="Mariama Bâ",
        synopsis=(
            "An epistolary novel about two Senegalese women coping with polygamy and its aftermath."
        ),
    ),
    # Science fiction / fantasy
    BookCreate(
        title="Solaris",
        author="Stanisław Lem",
        isbn="9780156837507",
        publication_year=1961,
        synopsis=(
            "Scientists on a space station struggle to communicate with the oceanic"
            " alien intelligence of Solaris."
        ),
    ),
    BookCreate(
        title="The Name of the Rose",
        author="Umberto Eco",
        isbn="9780156001311",
        publication_year=1980,
    ),
    # No isbn, no year — edge-case coverage
    BookCreate(
        title="Pedro Páramo",
        author="Juan Rulfo",
        synopsis=(
            "A man travels to a ghost town in Mexico searching for his father"
            " and encounters the dead."
        ),
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
