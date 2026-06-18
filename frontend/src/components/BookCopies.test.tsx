import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { BookCopies } from "./BookCopies";
import { setToken } from "../auth/tokenStore";
import { jsonResponse, makeBook, makeBookCopy, makeUser, renderWithAuth } from "../test/utils";
import type { BookCopy, UserRole } from "../api/types";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

function copyListResponse(items: BookCopy[]) {
  return jsonResponse({ items, total: items.length, page: 1, size: 100, pages: 1 });
}

function renderCopies() {
  return renderWithAuth(
    <Routes>
      <Route path="/books/:id/copies" element={<BookCopies />} />
    </Routes>,
    { initialEntries: ["/books/b1/copies"] },
  );
}

/**
 * Route `GET /auth/me` to the given role, `GET /books/b1` to a book, and
 * `GET /book-copies` to a mutable list. `POST /book-copies` appends, and
 * `DELETE /book-copies/{id}` removes (or fails when `mutateStatus` is set), so an
 * invalidated refetch reflects the change.
 */
function mockCopies(role: UserRole, options: { initial?: BookCopy[]; mutateStatus?: number } = {}) {
  let copies: BookCopy[] = options.initial ?? [makeBookCopy({ id: "c1", barcode: "BC-1" })];
  fetchMock.mockImplementation((url, init) => {
    const u = String(url);
    const method = init?.method ?? "GET";
    if (u.includes("/auth/me")) return Promise.resolve(jsonResponse(makeUser({ role })));
    if (u.includes("/books/b1")) return Promise.resolve(jsonResponse(makeBook({ id: "b1" })));
    if (u.includes("/book-copies") && method === "POST") {
      if (options.mutateStatus) {
        return Promise.resolve(
          jsonResponse({ detail: "Barcode already registered" }, options.mutateStatus),
        );
      }
      copies = [...copies, makeBookCopy({ id: "c2", barcode: "BC-2" })];
      return Promise.resolve(jsonResponse(copies[copies.length - 1], 201));
    }
    if (u.includes("/book-copies/c1") && method === "DELETE") {
      if (options.mutateStatus) {
        return Promise.resolve(
          jsonResponse({ detail: "Cannot remove a borrowed copy" }, options.mutateStatus),
        );
      }
      copies = copies.filter((c) => c.id !== "c1");
      return Promise.resolve(new Response(null, { status: 204 }));
    }
    if (u.includes("/book-copies")) return Promise.resolve(copyListResponse(copies));
    return Promise.resolve(jsonResponse({}, 404));
  });
}

beforeEach(() => {
  fetchMock.mockReset();
  setToken("tok");
});

describe("BookCopies", () => {
  it("shows a loading state, then renders the book's title, availability, and copies", async () => {
    mockCopies("staff");
    renderCopies();

    expect(screen.getByText("Loading copies…")).toBeInTheDocument();

    expect(await screen.findByText(/Copies of/)).toHaveTextContent("The Pragmatic Programmer");
    expect(screen.getByText("2 of 3 available")).toBeInTheDocument();
    expect(screen.getByText("BC-1")).toBeInTheDocument();
  });

  it("shows an empty state when the book has no copies", async () => {
    mockCopies("staff", { initial: [] });
    renderCopies();

    expect(await screen.findByText("No copies yet.")).toBeInTheDocument();
  });

  it("shows an error message when the copies request fails", async () => {
    fetchMock.mockImplementation((url) => {
      const u = String(url);
      if (u.includes("/auth/me")) return Promise.resolve(jsonResponse(makeUser({ role: "staff" })));
      if (u.includes("/books/b1") && !u.includes("/book-copies"))
        return Promise.resolve(jsonResponse(makeBook({ id: "b1" })));
      return Promise.resolve(jsonResponse({ detail: "Server error" }, 500));
    });
    renderCopies();

    expect(await screen.findByRole("alert")).toHaveTextContent("Server error");
  });

  it("hides the add form and remove controls for a member", async () => {
    mockCopies("member");
    renderCopies();

    expect(await screen.findByText("BC-1")).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    expect(screen.queryByRole("button", { name: "Add copy" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Remove" })).not.toBeInTheDocument();
  });

  it("adds a copy and shows it after the list refreshes", async () => {
    mockCopies("staff");
    const user = userEvent.setup();
    renderCopies();

    await user.type(await screen.findByLabelText("Barcode"), "BC-2");
    await user.click(screen.getByRole("button", { name: "Add copy" }));

    expect(await screen.findByText("BC-2")).toBeInTheDocument();
  });

  it("validates that a barcode is required before posting", async () => {
    mockCopies("staff");
    const user = userEvent.setup();
    renderCopies();

    await user.click(await screen.findByRole("button", { name: "Add copy" }));

    expect(await screen.findByText("Barcode is required.")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("surfaces a duplicate-barcode conflict on add", async () => {
    mockCopies("staff", { mutateStatus: 409 });
    const user = userEvent.setup();
    renderCopies();

    await user.type(await screen.findByLabelText("Barcode"), "BC-1");
    await user.click(screen.getByRole("button", { name: "Add copy" }));

    expect(await screen.findByText("Barcode already registered")).toBeInTheDocument();
  });

  it("removes a copy after inline confirmation and refreshes the list", async () => {
    mockCopies("staff");
    const user = userEvent.setup();
    renderCopies();

    await user.click(await screen.findByRole("button", { name: "Remove" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    await waitFor(() => expect(screen.queryByText("BC-1")).not.toBeInTheDocument());
    expect(screen.getByText("No copies yet.")).toBeInTheDocument();
  });

  it("surfaces an error and keeps the copy when remove fails", async () => {
    mockCopies("staff", { mutateStatus: 409 });
    const user = userEvent.setup();
    renderCopies();

    await user.click(await screen.findByRole("button", { name: "Remove" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(await screen.findByText("Cannot remove a borrowed copy")).toBeInTheDocument();
    expect(screen.getByText("BC-1")).toBeInTheDocument();
  });
});
