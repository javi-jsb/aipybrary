"""End-to-end authorization matrix: each role against each protected route.

Drives the real routers through the HTTP stack with the role fixtures from
conftest (`client` = staff, `admin_client`, `member_client`, `member_account`,
and `auth_client` for the unauthenticated case). Asserts the security boundary
enforced by `app/users/infrastructure/authz.py`: reads are open, writes are
admin/staff, and members are scoped to their own records.
"""

import uuid
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from app.book_copies.domain.book_copy_model import BookCopy
from app.books.domain.book_model import Book, BookCreate
from app.core.entity import _utcnow
from app.loans.domain.loan_model import Loan
from app.members.domain.member_model import Member, MemberStatus
from app.users.domain.user_model import User, UserRole

_BOOK_PAYLOAD = {"title": "Test Book", "author": "Test Author"}


async def _seed_book_with_copy(session: AsyncSession) -> BookCopy:
    book = Book.model_validate(BookCreate(title="Seeded", author="Author"))
    session.add(book)
    await session.flush()
    copy = BookCopy(book_id=book.id, barcode=f"BC-{uuid.uuid4().hex[:8]}")
    session.add(copy)
    await session.flush()
    return copy


# --- 401 vs 403 distinction -------------------------------------------------


async def test_unauthenticated_write_is_401(auth_client: AsyncClient) -> None:
    resp = await auth_client.post("/books", json=_BOOK_PAYLOAD)
    assert resp.status_code == 401


async def test_member_write_is_403_not_401(member_client: AsyncClient) -> None:
    resp = await member_client.post("/books", json=_BOOK_PAYLOAD)
    assert resp.status_code == 403


# --- Books and copies: read open, write admin/staff -------------------------


async def test_member_can_read_books(member_client: AsyncClient) -> None:
    resp = await member_client.get("/books")
    assert resp.status_code == 200


@pytest.mark.parametrize("method,path", [("patch", "/books/{id}"), ("delete", "/books/{id}")])
async def test_member_cannot_mutate_books(member_client: AsyncClient, method: str, path: str) -> None:
    url = path.format(id=uuid.uuid4())
    resp = await member_client.request(method.upper(), url, json=_BOOK_PAYLOAD if method == "patch" else None)
    assert resp.status_code == 403


async def test_staff_can_create_book(client: AsyncClient) -> None:
    resp = await client.post("/books", json=_BOOK_PAYLOAD)
    assert resp.status_code == 201


async def test_admin_can_create_book(admin_client: AsyncClient) -> None:
    resp = await admin_client.post("/books", json={"title": "Admin Book", "author": "A"})
    assert resp.status_code == 201


async def test_member_can_read_copies(member_client: AsyncClient) -> None:
    resp = await member_client.get("/book-copies")
    assert resp.status_code == 200


async def test_member_cannot_create_copy(member_client: AsyncClient) -> None:
    resp = await member_client.post("/book-copies", json={"book_id": str(uuid.uuid4()), "barcode": "X1"})
    assert resp.status_code == 403


# --- Members: staff-only list/manage, member reads only own profile ---------


async def test_member_cannot_list_members(member_client: AsyncClient) -> None:
    resp = await member_client.get("/members")
    assert resp.status_code == 403


async def test_staff_can_list_members(client: AsyncClient) -> None:
    resp = await client.get("/members")
    assert resp.status_code == 200


@pytest.mark.parametrize(
    "method,body",
    [
        ("post", {"full_name": "N", "email": "n@example.com"}),
        ("patch", {"full_name": "N"}),
        ("delete", None),
    ],
)
async def test_member_cannot_manage_members(member_client: AsyncClient, method: str, body: dict | None) -> None:
    url = "/members" if method == "post" else f"/members/{uuid.uuid4()}"
    resp = await member_client.request(method.upper(), url, json=body)
    assert resp.status_code == 403


async def test_member_reads_own_profile(member_account: tuple[AsyncClient, Member]) -> None:
    client, member = member_account
    resp = await client.get(f"/members/{member.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(member.id)


async def test_member_cannot_read_other_profile(member_account: tuple[AsyncClient, Member]) -> None:
    client, _ = member_account
    resp = await client.get(f"/members/{uuid.uuid4()}")
    assert resp.status_code == 403


# --- Loans: staff-only writes, member reads scoped to self ------------------


@pytest.mark.parametrize(
    "method,path",
    [
        ("post", "/loans"),
        ("post", "/loans/{id}/return"),
        ("delete", "/loans/{id}/return"),
        ("delete", "/loans/{id}"),
    ],
)
async def test_member_cannot_manage_loans(member_client: AsyncClient, method: str, path: str) -> None:
    url = path.format(id=uuid.uuid4())
    body = {"member_id": str(uuid.uuid4()), "book_copy_id": str(uuid.uuid4())} if path == "/loans" else None
    resp = await member_client.request(method.upper(), url, json=body)
    assert resp.status_code == 403


async def test_member_without_account_cannot_list_loans(member_client: AsyncClient) -> None:
    # A member-role user with no linked Member row owns nothing → forbidden.
    resp = await member_client.get("/loans")
    assert resp.status_code == 403


async def test_member_loans_list_scoped_to_self(
    session: AsyncSession, member_account: tuple[AsyncClient, Member]
) -> None:
    client, member = member_account
    due = _utcnow() + timedelta(days=10)

    own_copy = await _seed_book_with_copy(session)
    session.add(Loan(member_id=member.id, book_copy_id=own_copy.id, due_date=due))

    other_user = User(email="other@test.example", password_hash="x", role=UserRole.member, is_active=True)
    session.add(other_user)
    await session.flush()
    other_member = Member(full_name="Other", status=MemberStatus.active, user_id=other_user.id)
    session.add(other_member)
    await session.flush()
    other_copy = await _seed_book_with_copy(session)
    session.add(Loan(member_id=other_member.id, book_copy_id=other_copy.id, due_date=due))
    await session.flush()

    resp = await client.get("/loans")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert len(items) == 1
    assert all(item["member_id"] == str(member.id) for item in items)


async def test_member_loans_list_ignores_foreign_member_filter(
    session: AsyncSession, member_account: tuple[AsyncClient, Member]
) -> None:
    client, member = member_account
    due = _utcnow() + timedelta(days=10)
    own_copy = await _seed_book_with_copy(session)
    session.add(Loan(member_id=member.id, book_copy_id=own_copy.id, due_date=due))
    await session.flush()

    # Attempting to filter by another member is overridden back to self.
    resp = await client.get(f"/loans?member_id={uuid.uuid4()}")
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(item["member_id"] == str(member.id) for item in items)


async def test_member_reads_own_loan(session: AsyncSession, member_account: tuple[AsyncClient, Member]) -> None:
    client, member = member_account
    copy = await _seed_book_with_copy(session)
    loan = Loan(member_id=member.id, book_copy_id=copy.id, due_date=_utcnow() + timedelta(days=10))
    session.add(loan)
    await session.flush()

    resp = await client.get(f"/loans/{loan.id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == str(loan.id)


async def test_member_cannot_read_other_loan(session: AsyncSession, member_account: tuple[AsyncClient, Member]) -> None:
    client, _ = member_account
    other_user = User(email="other2@test.example", password_hash="x", role=UserRole.member, is_active=True)
    session.add(other_user)
    await session.flush()
    other_member = Member(full_name="Other2", status=MemberStatus.active, user_id=other_user.id)
    session.add(other_member)
    await session.flush()
    copy = await _seed_book_with_copy(session)
    loan = Loan(member_id=other_member.id, book_copy_id=copy.id, due_date=_utcnow() + timedelta(days=10))
    session.add(loan)
    await session.flush()

    resp = await client.get(f"/loans/{loan.id}")
    assert resp.status_code == 403


async def test_staff_borrow_and_return(client: AsyncClient, session: AsyncSession) -> None:
    user = User(email="m@test.example", password_hash="x", role=UserRole.member, is_active=True)
    session.add(user)
    await session.flush()
    member = Member(full_name="Borrower", status=MemberStatus.active, user_id=user.id)
    session.add(member)
    copy = await _seed_book_with_copy(session)
    await session.flush()

    borrow = await client.post("/loans", json={"member_id": str(member.id), "book_copy_id": str(copy.id)})
    assert borrow.status_code == 201
    loan_id = borrow.json()["id"]

    returned = await client.post(f"/loans/{loan_id}/return")
    assert returned.status_code == 200
    assert returned.json()["status"] == "returned"
