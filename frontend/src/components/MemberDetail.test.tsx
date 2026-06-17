import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import { Route, Routes } from "react-router";
import { MemberDetail } from "./MemberDetail";
import { setToken } from "../auth/tokenStore";
import { jsonResponse, makeMember, makeUser, renderWithAuth } from "../test/utils";
import type { UserRole } from "../api/types";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

function renderDetail() {
  return renderWithAuth(
    <Routes>
      <Route path="/members/:id" element={<MemberDetail />} />
    </Routes>,
    { initialEntries: ["/members/m1"] },
  );
}

/** Route `GET /auth/me` to the given role and `GET /members/m1` to a member. */
function mockDetailAs(role: UserRole) {
  fetchMock.mockImplementation((url) => {
    const u = String(url);
    if (u.includes("/auth/me")) return Promise.resolve(jsonResponse(makeUser({ role })));
    return Promise.resolve(jsonResponse(makeMember({ id: "m1", status: "suspended" })));
  });
}

beforeEach(() => {
  fetchMock.mockReset();
  setToken("tok");
});

describe("MemberDetail", () => {
  it("renders the fetched member's fields", async () => {
    mockDetailAs("staff");
    renderDetail();

    expect(await screen.findByRole("heading", { name: "Ada Lovelace" })).toBeInTheDocument();
    expect(screen.getByText("ada@example.com")).toBeInTheDocument();
    expect(screen.getByText("suspended")).toBeInTheDocument();
  });

  it("shows the Edit control for a staff user", async () => {
    mockDetailAs("staff");
    renderDetail();

    expect(await screen.findByRole("link", { name: "Edit" })).toHaveAttribute(
      "href",
      "/members/m1/edit",
    );
  });

  it("hides the Edit control for a member", async () => {
    mockDetailAs("member");
    renderDetail();

    expect(await screen.findByRole("heading", { name: "Ada Lovelace" })).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole("link", { name: "Edit" })).not.toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    // Fresh response per call so the auth/me request does not consume the body
    // the member request needs to read its `detail` from.
    fetchMock.mockImplementation(() =>
      Promise.resolve(jsonResponse({ detail: "Member not found" }, 404)),
    );
    renderDetail();

    expect(await screen.findByRole("alert")).toHaveTextContent("Member not found");
  });
});
