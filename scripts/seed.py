"""Seed the database with example users, members, books, book copies, and loans.

Idempotent per entity: each block is seeded only if no records of that type
exist — seeding one entity type is never skipped because another has data.
Seeding order: users → members → books → book copies → loans.
"""

import asyncio
import os
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sqlmodel import select  # noqa: E402

from app.book_copies.domain.book_copy_model import BookCopy  # noqa: E402
from app.books.domain.book_model import Book, BookCreate  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import async_session  # noqa: E402
from app.loans.domain.loan_model import Loan  # noqa: E402
from app.members.domain.member_model import Member, MemberStatus  # noqa: E402
from app.users.domain.user_model import User, UserRole  # noqa: E402


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


# ---------------------------------------------------------------------------
# Users — admin and staff bootstrap accounts
# ---------------------------------------------------------------------------

# Single password for every seeded account — this is throwaway test data, not
# a secret. Keeps local logins trivial to remember.
_SEED_PASSWORD = "pass"

_ADMIN_EMAIL = os.environ.get("SEED_ADMIN_EMAIL", "admin@aipybrary.dev")

# Obvious demo logins for exercising role-aware UI: one staff (catalog
# management) and one member (read-only). The member is provisioned with its
# linked Member record in the members block below, not here.
_STAFF_EMAIL = "staff@aipybrary.dev"
_MEMBER_EMAIL = "member@aipybrary.dev"

SAMPLE_USERS = [
    {
        "email": _ADMIN_EMAIL,
        "role": UserRole.admin,
    },
    {
        "email": _STAFF_EMAIL,
        "role": UserRole.staff,
    },
    {
        "email": "alice.smith@aipybrary.dev",
        "role": UserRole.staff,
    },
    {
        "email": "bob.jones@aipybrary.dev",
        "role": UserRole.staff,
    },
]


# ---------------------------------------------------------------------------
# Members — each paired with a member-role User
# ---------------------------------------------------------------------------

SAMPLE_MEMBERS = [
    # Obvious demo member login (read-only role) — see _MEMBER_EMAIL above.
    {"full_name": "Demo Member", "email": _MEMBER_EMAIL, "status": MemberStatus.active},
    {"full_name": "Ada Lovelace", "email": "ada.lovelace@example.com", "status": MemberStatus.active},
    {"full_name": "Alan Turing", "email": "alan.turing@example.com", "status": MemberStatus.active},
    {"full_name": "Grace Hopper", "email": "grace.hopper@example.com", "status": MemberStatus.active},
    {"full_name": "Katherine Johnson", "email": "katherine.johnson@example.com", "status": MemberStatus.active},
    {"full_name": "Edsger Dijkstra", "email": "edsger.dijkstra@example.com", "status": MemberStatus.active},
    {"full_name": "Barbara Liskov", "email": "barbara.liskov@example.com", "status": MemberStatus.active},
    {"full_name": "Donald Knuth", "email": "donald.knuth@example.com", "status": MemberStatus.active},
    {"full_name": "Margaret Hamilton", "email": "margaret.hamilton@example.com", "status": MemberStatus.active},
    {"full_name": "Tim Berners-Lee", "email": "tim.bernerslee@example.com", "status": MemberStatus.active},
    # Suspended members — exercise status filtering/sorting
    {"full_name": "Ken Thompson", "email": "ken.thompson@example.com", "status": MemberStatus.suspended},
    {"full_name": "Dennis Ritchie", "email": "dennis.ritchie@example.com", "status": MemberStatus.suspended},
    {"full_name": "Linus Torvalds", "email": "linus.torvalds@example.com", "status": MemberStatus.suspended},
]


# ---------------------------------------------------------------------------
# Books
# ---------------------------------------------------------------------------

SAMPLE_BOOKS = [
    # Hispanic literature
    BookCreate(
        title="Don Quixote",
        author="Miguel de Cervantes",
        isbn="9780060934347",
        publication_year=1605,
        synopsis=("The adventures of an idealistic nobleman who believes himself to be a knight-errant."),
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
        synopsis=("A boy discovers a mysterious book whose author seems to have been erased from history."),
    ),
    # European literature
    BookCreate(
        title="Crime and Punishment",
        author="Fyodor Dostoevsky",
        isbn="9780140449136",
        publication_year=1866,
        synopsis=("A young student commits a murder and wrestles with guilt and redemption in St. Petersburg."),
    ),
    BookCreate(
        title="The Trial",
        author="Franz Kafka",
        publication_year=1925,
        synopsis=("Josef K. is arrested and prosecuted by a remote, inaccessible authority for an unstated crime."),
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
        synopsis=("Twins in Kerala, India, whose lives are changed by the events of one day in December 1969."),
    ),
    # North American literature
    BookCreate(
        title="Beloved",
        author="Toni Morrison",
        isbn="9781400033416",
        publication_year=1987,
        synopsis=("A former enslaved woman is haunted by the ghost of her dead daughter in post-Civil War Ohio."),
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
        synopsis=("An envoy from an interplanetary league visits a world whose inhabitants have no fixed gender."),
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
        synopsis=("An epistolary novel about two Senegalese women coping with polygamy and its aftermath."),
    ),
    # Science fiction / fantasy
    BookCreate(
        title="Solaris",
        author="Stanisław Lem",
        isbn="9780156837507",
        publication_year=1961,
        synopsis=(
            "Scientists on a space station struggle to communicate with the oceanic alien intelligence of Solaris."
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
        synopsis=("A man travels to a ghost town in Mexico searching for his father and encounters the dead."),
    ),
]


async def seed() -> None:
    async with async_session() as session:
        # ----- Users (admin + staff) -----
        if (await session.exec(select(User).limit(1))).first() is not None:
            print("Database already contains users — skipping user seed.")
        else:
            for u in SAMPLE_USERS:
                session.add(
                    User(
                        email=u["email"],
                        password_hash=hash_password(_SEED_PASSWORD),
                        role=u["role"],
                        is_active=True,
                    )
                )
            await session.commit()
            print(f"Seeded {len(SAMPLE_USERS)} users (admin + staff). Password for all: {_SEED_PASSWORD}")
            print(f"  Admin login: {_ADMIN_EMAIL}")
            print(f"  Staff login: {_STAFF_EMAIL}")

        # ----- Members (each with a linked member-role User) -----
        if (await session.exec(select(Member).limit(1))).first() is not None:
            print("Database already contains members — skipping member seed.")
        else:
            for m in SAMPLE_MEMBERS:
                user = User(
                    email=m["email"],
                    password_hash=hash_password(_SEED_PASSWORD),
                    role=UserRole.member,
                    is_active=True,
                )
                session.add(user)
                await session.flush()  # get user.id before creating the member
                member = Member(full_name=m["full_name"], status=m["status"], user_id=user.id)
                session.add(member)
            await session.commit()
            print(f"Seeded {len(SAMPLE_MEMBERS)} members with linked member-role users.")
            print(f"  Member login: {_MEMBER_EMAIL}")

        # ----- Books -----
        if (await session.exec(select(Book).limit(1))).first() is not None:
            print("Database already contains books — skipping book seed.")
        else:
            for book_data in SAMPLE_BOOKS:
                session.add(Book.model_validate(book_data))
            await session.commit()
            print(f"Seeded {len(SAMPLE_BOOKS)} books.")

        # ----- Book copies -----
        if (await session.exec(select(BookCopy).limit(1))).first() is not None:
            print("Database already contains book copies — skipping book copy seed.")
        else:
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

        # ----- Loans -----
        if (await session.exec(select(Loan).limit(1))).first() is not None:
            print("Database already contains loans — skipping loan seed.")
        else:
            now = _utcnow()

            async def _member_by_email(email: str) -> Member | None:
                user = (await session.exec(select(User).where(User.email == email))).first()
                if user is None:
                    return None
                return (await session.exec(select(Member).where(Member.user_id == user.id))).first()

            ada = await _member_by_email("ada.lovelace@example.com")
            alan = await _member_by_email("alan.turing@example.com")
            grace = await _member_by_email("grace.hopper@example.com")

            copy_dq1 = (await session.exec(select(BookCopy).where(BookCopy.barcode == "DQ-001"))).first()
            copy_ohy1 = (await session.exec(select(BookCopy).where(BookCopy.barcode == "OHY-001"))).first()
            copy_cp1 = (await session.exec(select(BookCopy).where(BookCopy.barcode == "CP-001"))).first()

            loans_added = 0
            if ada and copy_dq1:
                session.add(Loan(member_id=ada.id, book_copy_id=copy_dq1.id, due_date=now + timedelta(days=10)))
                loans_added += 1
            if alan and copy_ohy1:
                session.add(Loan(member_id=alan.id, book_copy_id=copy_ohy1.id, due_date=now - timedelta(days=5)))
                loans_added += 1
            if grace and copy_cp1:
                session.add(
                    Loan(
                        member_id=grace.id,
                        book_copy_id=copy_cp1.id,
                        due_date=now - timedelta(days=20),
                        returned_at=now - timedelta(days=3),
                    )
                )
                loans_added += 1
            await session.commit()
            print(f"Seeded {loans_added} loans.")


if __name__ == "__main__":
    asyncio.run(seed())
