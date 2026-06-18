"""End-to-end test database lifecycle: provision and reset.

The E2E suite (Playwright) runs the real API against a dedicated logical
database, kept separate from the dev and backend-pytest databases. The target
database name comes from ``POSTGRES_DB`` — the Playwright harness (global setup
and the reset fixture) sets it to the dedicated E2E database before invoking
this script.

Commands:
- ``provision``: create the database if missing, migrate it to ``head``, then
  load the deterministic seed (truncate + insert).
- ``reset``: truncate and re-seed an already-provisioned database. Called
  between specs so each test starts from the same known state.

Safety guard: every command refuses to run unless ``POSTGRES_DB`` names an E2E
database, so it can never touch dev/test data even if misconfigured.
"""

import argparse
import asyncio
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path

import psycopg
from alembic.config import Config
from sqlalchemy import text

from alembic import command

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from app.book_copies.domain.book_copy_model import BookCopy  # noqa: E402
from app.books.domain.book_model import Book, BookCreate  # noqa: E402
from app.config import settings  # noqa: E402
from app.core.security import hash_password  # noqa: E402
from app.database import async_session  # noqa: E402
from app.loans.domain.loan_model import Loan  # noqa: E402
from app.members.domain.member_model import Member, MemberStatus  # noqa: E402
from app.users.domain.user_model import User, UserRole  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Shared password for every seeded account — throwaway test data, not a secret.
# The login fixture (e2e/fixtures.ts) authenticates with these credentials.
E2E_PASSWORD = "pass"
ADMIN_EMAIL = "admin@aipybrary.dev"
STAFF_EMAIL = "staff@aipybrary.dev"
MEMBER_EMAIL = "member@aipybrary.dev"

# Tables truncated on every reset (alembic_version is intentionally preserved).
_DATA_TABLES = ("loans", "book_copies", "books", "members", "users")


def _utcnow() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _require_e2e_database() -> None:
    """Abort unless the configured database is an E2E one — a destructive-op guard."""
    if not settings.POSTGRES_DB.endswith("e2e"):
        sys.exit(
            f"refusing to run: POSTGRES_DB={settings.POSTGRES_DB!r} is not an E2E database. "
            "It is set by the Playwright harness; run the suite with `make e2e-frontend`."
        )


def _create_database_if_missing() -> None:
    """Create the E2E database if it does not exist (connects to the maintenance DB)."""
    conninfo = (
        f"host={settings.POSTGRES_HOST} port={settings.POSTGRES_PORT} "
        f"user={settings.POSTGRES_USER} password={settings.POSTGRES_PASSWORD} dbname=postgres"
    )
    with psycopg.connect(conninfo, autocommit=True) as conn:
        exists = conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", [settings.POSTGRES_DB]).fetchone()
        if exists is None:
            # Identifier can't be parameterised; the name is validated by the E2E guard above.
            conn.execute(f'CREATE DATABASE "{settings.POSTGRES_DB}"')
            print(f"Created E2E database {settings.POSTGRES_DB!r}.")
        else:
            print(f"E2E database {settings.POSTGRES_DB!r} already exists.")


def _migrate() -> None:
    """Apply Alembic migrations to head. env.py reads the URL from settings (POSTGRES_DB)."""
    command.upgrade(Config(str(_REPO_ROOT / "alembic.ini")), "head")


async def _truncate_and_seed() -> None:
    async with async_session() as session:
        connection = await session.connection()
        await connection.execute(text(f"TRUNCATE {', '.join(_DATA_TABLES)} RESTART IDENTITY CASCADE"))

        password_hash = hash_password(E2E_PASSWORD)  # hashed once and reused — keeps reset fast

        # ----- Users: one per role -----
        admin = User(email=ADMIN_EMAIL, password_hash=password_hash, role=UserRole.admin, is_active=True)
        staff = User(email=STAFF_EMAIL, password_hash=password_hash, role=UserRole.staff, is_active=True)
        member_user = User(email=MEMBER_EMAIL, password_hash=password_hash, role=UserRole.member, is_active=True)
        ada_user = User(email="ada@e2e.test", password_hash=password_hash, role=UserRole.member, is_active=True)
        maxed_user = User(email="maxed@e2e.test", password_hash=password_hash, role=UserRole.member, is_active=True)
        session.add_all([admin, staff, member_user, ada_user, maxed_user])
        await session.flush()  # assign user ids before linking members

        # ----- Members: linked to the member-role users -----
        demo_member = Member(full_name="Demo Member", status=MemberStatus.active, user_id=member_user.id)
        ada = Member(full_name="Ada Lovelace", status=MemberStatus.active, user_id=ada_user.id)
        # "Maxed Member" already holds the maximum active loans, so a further
        # borrow attempt surfaces the loan-limit business-rule error in the UI.
        maxed = Member(full_name="Maxed Member", status=MemberStatus.active, user_id=maxed_user.id)
        session.add_all([demo_member, ada, maxed])

        # ----- Books -----
        quixote = Book.model_validate(
            BookCreate(
                title="Don Quixote",
                author="Miguel de Cervantes",
                isbn="9780060934347",
                publication_year=1605,
            )
        )
        crime = Book.model_validate(
            BookCreate(
                title="Crime and Punishment",
                author="Fyodor Dostoevsky",
                isbn="9780140449136",
                publication_year=1866,
            )
        )
        session.add_all([quixote, crime])
        await session.flush()  # assign book ids before linking copies

        # ----- Book copies: one on loan, two available, three held by Maxed Member -----
        dq_on_loan = BookCopy(book_id=quixote.id, barcode="DQ-001")
        dq_available = BookCopy(book_id=quixote.id, barcode="DQ-002")
        cp_available = BookCopy(book_id=crime.id, barcode="CP-001")
        maxed_copies = [BookCopy(book_id=crime.id, barcode=f"MX-{n:03d}") for n in range(1, 4)]
        session.add_all([dq_on_loan, dq_available, cp_available, *maxed_copies])
        await session.flush()  # assign copy ids before linking loans

        # ----- Loans -----
        due = _utcnow() + timedelta(days=10)
        # One active loan (DQ-001) to exercise the return flow; DQ-002 and CP-001
        # stay available to exercise the borrow flow.
        session.add(Loan(member_id=ada.id, book_copy_id=dq_on_loan.id, due_date=due))
        # Maxed Member at the active-loan limit — drives the loan-limit error path.
        session.add_all([Loan(member_id=maxed.id, book_copy_id=copy.id, due_date=due) for copy in maxed_copies])

        await session.commit()
    print("Seeded E2E database (5 users, 3 members, 2 books, 6 copies, 4 active loans).")


def provision() -> None:
    _require_e2e_database()
    _create_database_if_missing()
    _migrate()
    asyncio.run(_truncate_and_seed())


def reset() -> None:
    _require_e2e_database()
    asyncio.run(_truncate_and_seed())


def main() -> None:
    parser = argparse.ArgumentParser(description="E2E test database lifecycle.")
    parser.add_argument("command", choices=["provision", "reset"])
    args = parser.parse_args()
    {"provision": provision, "reset": reset}[args.command]()


if __name__ == "__main__":
    main()
