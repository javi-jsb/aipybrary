"""Seed the database with example books, members, book copies, and loans.

Idempotent per entity: each block is seeded only if no records of that type
exist — seeding one entity type is never skipped because another has data.
Seeding order: books → members → book copies → loans.
"""

import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlmodel import select  # noqa: E402

from app.book_copies.domain.book_copy_model import BookCopy  # noqa: E402
from app.books.domain.book_model import Book, BookCreate  # noqa: E402
from app.database import async_session  # noqa: E402
from app.loans.domain.loan_model import Loan  # noqa: E402
from app.members.domain.member_model import (  # noqa: E402
    Member,
    MemberCreate,
    MemberStatus,
)


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


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


SAMPLE_MEMBERS = [
    MemberCreate(full_name="Ada Lovelace", email="ada.lovelace@example.com"),
    MemberCreate(full_name="Alan Turing", email="alan.turing@example.com"),
    MemberCreate(full_name="Grace Hopper", email="grace.hopper@example.com"),
    MemberCreate(full_name="Katherine Johnson", email="katherine.johnson@example.com"),
    MemberCreate(full_name="Edsger Dijkstra", email="edsger.dijkstra@example.com"),
    MemberCreate(full_name="Barbara Liskov", email="barbara.liskov@example.com"),
    MemberCreate(full_name="Donald Knuth", email="donald.knuth@example.com"),
    MemberCreate(full_name="Margaret Hamilton", email="margaret.hamilton@example.com"),
    MemberCreate(full_name="Tim Berners-Lee", email="tim.bernerslee@example.com"),
    # Suspended members — exercise status filtering/sorting
    MemberCreate(
        full_name="Ken Thompson",
        email="ken.thompson@example.com",
        status=MemberStatus.suspended,
    ),
    MemberCreate(
        full_name="Dennis Ritchie",
        email="dennis.ritchie@example.com",
        status=MemberStatus.suspended,
    ),
    MemberCreate(
        full_name="Linus Torvalds",
        email="linus.torvalds@example.com",
        status=MemberStatus.suspended,
    ),
]


async def seed() -> None:
    async with async_session() as session:
        if (await session.exec(select(Book).limit(1))).first() is not None:
            print("Database already contains books — skipping book seed.")
        else:
            for book_data in SAMPLE_BOOKS:
                session.add(Book.model_validate(book_data))
            await session.commit()
            print(f"Seeded {len(SAMPLE_BOOKS)} books.")

        if (await session.exec(select(Member).limit(1))).first() is not None:
            print("Database already contains members — skipping member seed.")
        else:
            for member_data in SAMPLE_MEMBERS:
                session.add(Member.model_validate(member_data))
            await session.commit()
            print(f"Seeded {len(SAMPLE_MEMBERS)} members.")

        if (await session.exec(select(BookCopy).limit(1))).first() is not None:
            print("Database already contains book copies — skipping book copy seed.")
        else:
            # Look up book ISBNs to find specific book IDs for the copies.
            books_by_isbn: dict[str, Book] = {}
            for book in (await session.exec(select(Book))).all():
                if book.isbn:
                    books_by_isbn[book.isbn] = book

            copies_added = 0
            copy_specs = [
                # Don Quixote — 2 copies
                ("9780060934347", "DQ-001"),
                ("9780060934347", "DQ-002"),
                # One Hundred Years — 2 copies
                ("9780060883287", "OHY-001"),
                ("9780060883287", "OHY-002"),
                # Crime and Punishment — 2 copies
                ("9780140449136", "CP-001"),
                ("9780140449136", "CP-002"),
                # Solaris — 1 copy
                ("9780156837507", "SOL-001"),
            ]
            for isbn, barcode in copy_specs:
                book = books_by_isbn.get(isbn)
                if book is not None:
                    session.add(BookCopy(book_id=book.id, barcode=barcode))
                    copies_added += 1
            await session.commit()
            print(f"Seeded {copies_added} book copies.")

        if (await session.exec(select(Loan).limit(1))).first() is not None:
            print("Database already contains loans — skipping loan seed.")
        else:
            now = _utcnow()

            # Look up members and copies by known values.
            ada = (
                await session.exec(select(Member).where(Member.email == "ada.lovelace@example.com"))
            ).first()
            alan = (
                await session.exec(select(Member).where(Member.email == "alan.turing@example.com"))
            ).first()
            grace = (
                await session.exec(select(Member).where(Member.email == "grace.hopper@example.com"))
            ).first()

            copy_dq1 = (
                await session.exec(select(BookCopy).where(BookCopy.barcode == "DQ-001"))
            ).first()
            copy_ohy1 = (
                await session.exec(select(BookCopy).where(BookCopy.barcode == "OHY-001"))
            ).first()
            copy_cp1 = (
                await session.exec(select(BookCopy).where(BookCopy.barcode == "CP-001"))
            ).first()

            loans_added = 0
            if ada and copy_dq1:
                # Active loan: due in future
                session.add(
                    Loan(
                        member_id=ada.id,
                        book_copy_id=copy_dq1.id,
                        due_date=now + timedelta(days=10),
                    )
                )
                loans_added += 1
            if alan and copy_ohy1:
                # Overdue loan: due in the past, not returned
                session.add(
                    Loan(
                        member_id=alan.id,
                        book_copy_id=copy_ohy1.id,
                        due_date=now - timedelta(days=5),
                    )
                )
                loans_added += 1
            if grace and copy_cp1:
                # Returned loan
                returned_loan = Loan(
                    member_id=grace.id,
                    book_copy_id=copy_cp1.id,
                    due_date=now - timedelta(days=20),
                    returned_at=now - timedelta(days=3),
                )
                session.add(returned_loan)
                loans_added += 1
            await session.commit()
            print(f"Seeded {loans_added} loans.")


if __name__ == "__main__":
    asyncio.run(seed())
