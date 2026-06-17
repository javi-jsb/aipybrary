import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { BookForm } from "./BookForm";
import { setToken } from "../auth/tokenStore";
import { jsonResponse, makeBook, renderWithAuth } from "../test/utils";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

/** Render the form route alongside a stub `/books` list so navigation on
 * success is observable. */
function renderForm(initialEntries: string[]) {
  return renderWithAuth(
    <Routes>
      <Route path="/books" element={<div>Books list</div>} />
      <Route path="/books/new" element={<BookForm />} />
      <Route path="/books/:id/edit" element={<BookForm />} />
    </Routes>,
    { initialEntries },
  );
}

beforeEach(() => {
  fetchMock.mockReset();
  setToken("tok");
});

describe("BookForm — create", () => {
  it("POSTs the new book, normalizing blanks, then navigates to the list", async () => {
    fetchMock.mockResolvedValue(jsonResponse(makeBook(), 201));
    const user = userEvent.setup();
    renderForm(["/books/new"]);

    await user.type(screen.getByLabelText("Title"), "Dune");
    await user.type(screen.getByLabelText("Author"), "Frank Herbert");
    await user.type(screen.getByLabelText("Publication year"), "1965");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Books list")).toBeInTheDocument();
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8077/books");
    expect(init?.method).toBe("POST");
    expect(JSON.parse(init?.body as string)).toEqual({
      title: "Dune",
      author: "Frank Herbert",
      isbn: null,
      publication_year: 1965,
      synopsis: null,
    });
  });

  it("surfaces a duplicate-ISBN conflict on the form and preserves input", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "ISBN already registered" }, 409));
    const user = userEvent.setup();
    renderForm(["/books/new"]);

    await user.type(screen.getByLabelText("Title"), "Dune");
    await user.type(screen.getByLabelText("Author"), "Frank Herbert");
    await user.type(screen.getByLabelText("ISBN"), "9780000000000");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("ISBN already registered");
    expect(screen.queryByText("Books list")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Title")).toHaveValue("Dune");
    expect(screen.getByLabelText("ISBN")).toHaveValue("9780000000000");
  });
});

describe("BookForm — edit", () => {
  it("prefills from the fetched book, PATCHes changes, then navigates", async () => {
    const book = makeBook({ id: "b1", title: "Old title", author: "Author" });
    fetchMock.mockImplementation((_url, init) => {
      const method = init?.method ?? "GET";
      if (method === "PATCH") return Promise.resolve(jsonResponse({ ...book, title: "New title" }));
      return Promise.resolve(jsonResponse(book));
    });
    const user = userEvent.setup();
    renderForm(["/books/b1/edit"]);

    const titleInput = await screen.findByLabelText("Title");
    expect(titleInput).toHaveValue("Old title");

    await user.clear(titleInput);
    await user.type(titleInput, "New title");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Books list")).toBeInTheDocument();
    const patchCall = fetchMock.mock.calls.find(([, init]) => init?.method === "PATCH");
    expect(patchCall?.[0]).toBe("http://localhost:8077/books/b1");
    expect(JSON.parse(patchCall?.[1]?.body as string)).toMatchObject({ title: "New title" });
  });
});
