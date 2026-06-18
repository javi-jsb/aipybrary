import { describe, it, expect, vi, beforeEach } from "vitest";
import { borrowLoan, getLoans, returnLoan } from "./loans";
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

describe("loans API call functions", () => {
  it("getLoans requests the list endpoint asking for a full page", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ items: [], total: 0, page: 1, size: 100, pages: 0 }),
    );

    await getLoans();

    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8077/loans?size=100");
    expect(fetchMock.mock.calls[0][1]?.method ?? "GET").toBe("GET");
  });

  it("borrowLoan POSTs JSON to /loans", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "l1" }, 201));
    const payload = { member_id: "m1", book_copy_id: "c1" };

    await borrowLoan(payload);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8077/loans");
    expect(init?.method).toBe("POST");
    expect((init?.headers as Headers).get("Content-Type")).toBe("application/json");
    expect(JSON.parse(init?.body as string)).toEqual(payload);
  });

  it("returnLoan POSTs to /loans/{id}/return", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "l1", returned_at: "2026-06-18T00:00:00Z" }));

    await returnLoan("l1");

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8077/loans/l1/return");
    expect(init?.method).toBe("POST");
  });

  it("surfaces a borrow conflict as an ApiError carrying the backend detail", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Book copy is already on loan" }, 409));

    await expect(borrowLoan({ member_id: "m1", book_copy_id: "c1" })).rejects.toMatchObject({
      status: 409,
      message: "Book copy is already on loan",
    });
  });

  it("surfaces an already-returned conflict as an ApiError", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Loan is already returned" }, 409));

    await expect(returnLoan("l1")).rejects.toBeInstanceOf(ApiError);
  });
});
