import { describe, it, expect, vi, beforeEach } from "vitest";
import { createBookCopy, deleteBookCopy, getBookCopies } from "./bookCopies";
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

describe("book-copies API call functions", () => {
  it("getBookCopies filters by book_id and requests a full page", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ items: [], total: 0, page: 1, size: 100, pages: 0 }),
    );

    await getBookCopies("b1");

    const url = new URL(fetchMock.mock.calls[0][0] as string);
    expect(url.pathname).toBe("/book-copies");
    expect(url.searchParams.get("book_id")).toBe("b1");
    expect(url.searchParams.get("size")).toBe("100");
    expect(fetchMock.mock.calls[0][1]?.method ?? "GET").toBe("GET");
  });

  it("createBookCopy POSTs JSON to /book-copies", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "c1" }, 201));
    const payload = { book_id: "b1", barcode: "ABC-1", location: "Shelf 3", notes: null };

    await createBookCopy(payload);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8077/book-copies");
    expect(init?.method).toBe("POST");
    expect((init?.headers as Headers).get("Content-Type")).toBe("application/json");
    expect(JSON.parse(init?.body as string)).toEqual(payload);
  });

  it("deleteBookCopy DELETEs /book-copies/{id} and resolves on 204", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(deleteBookCopy("c1")).resolves.toBeUndefined();
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8077/book-copies/c1");
    expect(fetchMock.mock.calls[0][1]?.method).toBe("DELETE");
  });

  it("surfaces a duplicate-barcode 409 as an ApiError carrying the backend detail", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Barcode already registered" }, 409));

    await expect(
      createBookCopy({ book_id: "b1", barcode: "ABC-1", location: null, notes: null }),
    ).rejects.toMatchObject({ status: 409, message: "Barcode already registered" });
    await expect(
      createBookCopy({ book_id: "b1", barcode: "ABC-1", location: null, notes: null }),
    ).rejects.toBeInstanceOf(ApiError);
  });
});
