import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BooksList } from "./BooksList";
import { setToken } from "../auth/tokenStore";
import { jsonResponse, makeBook, makeUser, renderWithAuth } from "../test/utils";
import type { Book, UserRole } from "../api/types";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

function bookListResponse(items: Book[]) {
  return jsonResponse({ items, total: items.length, page: 1, size: 50, pages: 1 });
}

beforeEach(() => {
  fetchMock.mockReset();
});

describe("BooksList", () => {
  it("shows a loading state, then renders the books from the API", async () => {
    fetchMock.mockResolvedValue(bookListResponse([makeBook()]));
    renderWithAuth(<BooksList />);

    expect(screen.getByText("Loading books…")).toBeInTheDocument();

    expect(await screen.findByText("The Pragmatic Programmer")).toBeInTheDocument();
    expect(screen.getByText("Hunt & Thomas")).toBeInTheDocument();
    expect(screen.getByText("1999")).toBeInTheDocument();
  });

  it("shows an empty state when there are no books", async () => {
    fetchMock.mockResolvedValue(bookListResponse([]));
    renderWithAuth(<BooksList />);

    expect(await screen.findByText("No books found.")).toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Server error" }, 500));
    renderWithAuth(<BooksList />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Server error");
  });
});

/**
 * Route `GET /auth/me` to a user of the given role and `GET /books` to a
 * mutable list; `DELETE /books/{id}` removes from that list (or fails when
 * `deleteStatus` is set) so an invalidated refetch reflects the change.
 */
function mockManagement(role: UserRole, options: { deleteStatus?: number } = {}) {
  let books: Book[] = [makeBook({ id: "b1", title: "Deletable Book" })];
  fetchMock.mockImplementation((url, init) => {
    const u = String(url);
    const method = init?.method ?? "GET";
    if (u.includes("/auth/me")) return Promise.resolve(jsonResponse(makeUser({ role })));
    if (u.endsWith("/books/b1") && method === "DELETE") {
      if (options.deleteStatus) {
        return Promise.resolve(
          jsonResponse({ detail: "Book has copies and cannot be deleted" }, options.deleteStatus),
        );
      }
      books = [];
      return Promise.resolve(new Response(null, { status: 204 }));
    }
    if (u.endsWith("/books")) return Promise.resolve(bookListResponse(books));
    return Promise.resolve(jsonResponse({}, 404));
  });
}

describe("BooksList — role-gated management", () => {
  it("shows New/Edit/Delete controls for a staff user", async () => {
    setToken("tok");
    mockManagement("staff");
    renderWithAuth(<BooksList />);

    expect(await screen.findByText("Deletable Book")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "New book" })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Edit" })).toHaveAttribute("href", "/books/b1/edit");
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
  });

  it("hides management controls for a member", async () => {
    setToken("tok");
    mockManagement("member");
    renderWithAuth(<BooksList />);

    expect(await screen.findByText("Deletable Book")).toBeInTheDocument();
    // Wait for the role to resolve so we are not just asserting a not-yet-rendered control.
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole("link", { name: "New book" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Edit" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
  });

  it("deletes a book after inline confirmation and refreshes the list", async () => {
    setToken("tok");
    mockManagement("staff");
    const user = userEvent.setup();
    renderWithAuth(<BooksList />);

    await user.click(await screen.findByRole("button", { name: "Delete" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(await screen.findByText("No books found.")).toBeInTheDocument();
    expect(screen.queryByText("Deletable Book")).not.toBeInTheDocument();
  });

  it("surfaces the has-copies conflict and keeps the book when delete fails", async () => {
    setToken("tok");
    mockManagement("staff", { deleteStatus: 409 });
    const user = userEvent.setup();
    renderWithAuth(<BooksList />);

    await user.click(await screen.findByRole("button", { name: "Delete" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Book has copies and cannot be deleted",
    );
    expect(screen.getByText("Deletable Book")).toBeInTheDocument();
  });
});
