import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BooksList } from "./BooksList";
import { getToken, setToken } from "../auth/tokenStore";
import { jsonResponse, makeBook, renderWithAuth } from "../test/utils";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

function bookListResponse(items: ReturnType<typeof makeBook>[]) {
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

  it("clears the session when signing out", async () => {
    setToken("tok");
    fetchMock.mockResolvedValue(bookListResponse([]));
    const user = userEvent.setup();
    renderWithAuth(<BooksList />);

    await screen.findByText("No books found.");
    await user.click(screen.getByRole("button", { name: "Sign out" }));

    expect(getToken()).toBeNull();
  });
});
