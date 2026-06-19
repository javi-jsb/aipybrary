import { describe, it, expect, vi, beforeEach } from "vitest";
import { apiClient, ApiError, setUnauthorizedHandler } from "./client";
import { setToken } from "../auth/tokenStore";
import { jsonResponse } from "../test/utils";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

/** The init object passed to fetch on the first (only) call. */
function lastInit(): RequestInit {
  return fetchMock.mock.calls[0][1] as RequestInit;
}

describe("apiClient", () => {
  beforeEach(() => {
    fetchMock.mockReset();
  });

  it("prepends the base URL and defaults to GET", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ ok: true }));

    const data = await apiClient<{ ok: boolean }>("/books");

    expect(fetchMock).toHaveBeenCalledOnce();
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8077/books");
    expect(lastInit().method).toBe("GET");
    expect(data).toEqual({ ok: true });
  });

  it("attaches the bearer token when one is stored", async () => {
    setToken("tok-123");
    fetchMock.mockResolvedValue(jsonResponse({}));

    await apiClient("/books");

    const headers = lastInit().headers as Headers;
    expect(headers.get("Authorization")).toBe("Bearer tok-123");
  });

  it("omits the Authorization header when no token is stored", async () => {
    fetchMock.mockResolvedValue(jsonResponse({}));

    await apiClient("/books");

    const headers = lastInit().headers as Headers;
    expect(headers.has("Authorization")).toBe(false);
  });

  it("throws ApiError carrying the backend detail message on non-success", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Duplicate ISBN" }, 409));

    const error = await apiClient("/books").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 409, message: "Duplicate ISBN" });
  });

  it("falls back to a generic message when the error body is not JSON", async () => {
    fetchMock.mockResolvedValue(new Response("boom", { status: 500 }));

    const error = await apiClient("/books").catch((e: unknown) => e);

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 500, message: "Request failed with status 500" });
  });

  it("returns undefined for a 204 No Content response", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(apiClient("/books/1")).resolves.toBeUndefined();
  });

  it("invokes the registered unauthorized handler on a 401 (then still throws)", async () => {
    const onUnauthorized = vi.fn();
    setUnauthorizedHandler(onUnauthorized);
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Not authenticated" }, 401));

    const error = await apiClient("/auth/me").catch((e: unknown) => e);

    expect(onUnauthorized).toHaveBeenCalledOnce();
    expect(error).toMatchObject({ status: 401 });
    setUnauthorizedHandler(null);
  });

  it("does not invoke the unauthorized handler on a 403", async () => {
    const onUnauthorized = vi.fn();
    setUnauthorizedHandler(onUnauthorized);
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Insufficient permissions" }, 403));

    await apiClient("/members").catch(() => undefined);

    expect(onUnauthorized).not.toHaveBeenCalled();
    setUnauthorizedHandler(null);
  });
});
