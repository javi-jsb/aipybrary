import { describe, it, expect, vi, beforeEach } from "vitest";
import { createMember, deleteMember, getMember, getMembers, updateMember } from "./members";
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

describe("members API call functions", () => {
  it("getMembers requests the list endpoint", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ items: [], total: 0, page: 1, size: 20, pages: 0 }));

    await getMembers();

    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8077/members");
    expect(fetchMock.mock.calls[0][1]?.method ?? "GET").toBe("GET");
  });

  it("getMember requests the single-member endpoint", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "m1", full_name: "N" }));

    await getMember("m1");

    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8077/members/m1");
  });

  it("createMember POSTs JSON to /members", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "m1", initial_password: "secret" }, 201));
    const payload = { full_name: "Ada", email: "ada@example.com", status: "active" as const };

    await createMember(payload);

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8077/members");
    expect(init?.method).toBe("POST");
    expect((init?.headers as Headers).get("Content-Type")).toBe("application/json");
    expect(JSON.parse(init?.body as string)).toEqual(payload);
  });

  it("updateMember PATCHes JSON to /members/{id}", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ id: "m1" }));

    await updateMember("m1", { full_name: "New name", status: "suspended" });

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8077/members/m1");
    expect(init?.method).toBe("PATCH");
    expect(JSON.parse(init?.body as string)).toEqual({
      full_name: "New name",
      status: "suspended",
    });
  });

  it("deleteMember DELETEs /members/{id} and resolves on 204", async () => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }));

    await expect(deleteMember("m1")).resolves.toBeUndefined();
    expect(fetchMock.mock.calls[0][0]).toBe("http://localhost:8077/members/m1");
    expect(fetchMock.mock.calls[0][1]?.method).toBe("DELETE");
  });

  it("surfaces a 409 conflict as an ApiError carrying the backend detail", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Email already registered" }, 409));

    await expect(
      createMember({ full_name: "Ada", email: "ada@example.com", status: "active" }),
    ).rejects.toMatchObject({ status: 409, message: "Email already registered" });
    await expect(deleteMember("m1")).rejects.toBeInstanceOf(ApiError);
  });
});
