import { describe, it, expect, vi, beforeEach } from "vitest";
import { createBook, deleteBook, getBook, updateBook } from "./books";
import { ApiError } from "./client";
import { setToken } from "../auth/tokenStore";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

function jsonResponse(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

beforeEach(() => {
  fetchMock.mockReset();
  setToken("tok");
});

describe("books API call functions", () => {
  it("getBook requests the single-book endpoint", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "b1", title: "T" }));

    await getBook("b1");

    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8077/books/b1");
    expect(fetchMock.mock.calls[0][1]?.method ?? "GET").toBe("GET");
  });

  it("createBook POSTs JSON to /books", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "b1" }, 201));
    const payload = {
      title: "Dune",
      author: "Herbert",
      isbn: null,
      publication_year: 1965,
      synopsis: null,
    };

    await createBook(payload);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8077/books");
    expect(init?.method).toBe("POST");
    expect((init?.headers as Headers).get("Content-Type")).toBe("application/json");
    expect(JSON.parse(init?.body as string)).toEqual(payload);
  });

  it("updateBook PATCHes JSON to /books/{id}", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "b1" }));

    await updateBook("b1", { title: "New title" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8077/books/b1");
    expect(init?.method).toBe("PATCH");
    expect(JSON.parse(init?.body as string)).toEqual({ title: "New title" });
  });

  it("deleteBook DELETEs /books/{id} and resolves on 204", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(deleteBook("b1")).resolves.toBeUndefined();
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8077/books/b1");
    expect(fetchMock.mock.calls[0][1]?.method).toBe("DELETE");
  });

  it("surfaces a 409 conflict as an ApiError carrying the backend detail", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "ISBN already registered" }, 409));

    await expect(
      createBook({ title: "T", author: "A", isbn: "x", publication_year: null, synopsis: null }),
    ).rejects.toMatchObject({ status: 409, message: "ISBN already registered" });
    await expect(deleteBook("b1")).rejects.toBeInstanceOf(ApiError);
  });
});
