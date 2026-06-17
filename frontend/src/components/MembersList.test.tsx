import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MembersList } from "./MembersList";
import { setToken } from "../auth/tokenStore";
import { jsonResponse, makeMember, makeUser, renderWithAuth } from "../test/utils";
import type { Member, UserRole } from "../api/types";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

function memberListResponse(items: Member[]) {
  return jsonResponse({ items, total: items.length, page: 1, size: 20, pages: 1 });
}

beforeEach(() => {
  fetchMock.mockReset();
});

describe("MembersList", () => {
  it("shows a loading state, then renders the members with links to detail", async () => {
    fetchMock.mockResolvedValue(memberListResponse([makeMember({ id: "m1" })]));
    renderWithAuth(<MembersList />);

    expect(screen.getByText("Loading members…")).toBeInTheDocument();

    expect(await screen.findByText("Ada Lovelace")).toBeInTheDocument();
    expect(screen.getByText("ada@example.com")).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Ada Lovelace/ })).toHaveAttribute(
      "href",
      "/members/m1",
    );
  });

  it("shows an empty state when there are no members", async () => {
    fetchMock.mockResolvedValue(memberListResponse([]));
    renderWithAuth(<MembersList />);

    expect(await screen.findByText("No members found.")).toBeInTheDocument();
  });

  it("shows an error message when the request fails", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Server error" }, 500));
    renderWithAuth(<MembersList />);

    expect(await screen.findByRole("alert")).toHaveTextContent("Server error");
  });
});

/**
 * Route `GET /auth/me` to the given role and `GET /members` to a mutable list;
 * `DELETE /members/{id}` removes from that list (or fails when `deleteStatus` is
 * set) so an invalidated refetch reflects the change.
 */
function mockManagement(role: UserRole, options: { deleteStatus?: number } = {}) {
  let members: Member[] = [makeMember({ id: "m1", full_name: "Deletable Member" })];
  fetchMock.mockImplementation((url, init) => {
    const u = String(url);
    const method = init?.method ?? "GET";
    if (u.includes("/auth/me")) return Promise.resolve(jsonResponse(makeUser({ role })));
    if (u.endsWith("/members/m1") && method === "DELETE") {
      if (options.deleteStatus) {
        return Promise.resolve(
          jsonResponse({ detail: "Member has loans and cannot be deleted" }, options.deleteStatus),
        );
      }
      members = [];
      return Promise.resolve(new Response(null, { status: 204 }));
    }
    if (u.endsWith("/members")) return Promise.resolve(memberListResponse(members));
    return Promise.resolve(jsonResponse({}, 404));
  });
}

describe("MembersList — role-gated management", () => {
  it("shows New and Edit but not Delete for a staff user (delete is admin-only)", async () => {
    setToken("tok");
    mockManagement("staff");
    renderWithAuth(<MembersList />);

    expect(await screen.findByText("Deletable Member")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "New member" })).toHaveAttribute(
      "href",
      "/members/new",
    );
    expect(screen.getByRole("link", { name: "Edit" })).toHaveAttribute("href", "/members/m1/edit");
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
  });

  it("shows the Delete control for an admin user", async () => {
    setToken("tok");
    mockManagement("admin");
    renderWithAuth(<MembersList />);

    expect(await screen.findByText("Deletable Member")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Delete" })).toBeInTheDocument();
  });

  it("hides all management controls for a member", async () => {
    setToken("tok");
    mockManagement("member");
    renderWithAuth(<MembersList />);

    expect(await screen.findByText("Deletable Member")).toBeInTheDocument();
    await waitFor(() => expect(fetchMock).toHaveBeenCalledTimes(2));
    expect(screen.queryByRole("link", { name: "New member" })).not.toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "Edit" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Delete" })).not.toBeInTheDocument();
  });

  it("deletes a member after inline confirmation and refreshes the list", async () => {
    setToken("tok");
    mockManagement("admin");
    const user = userEvent.setup();
    renderWithAuth(<MembersList />);

    await user.click(await screen.findByRole("button", { name: "Delete" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(await screen.findByText("No members found.")).toBeInTheDocument();
    expect(screen.queryByText("Deletable Member")).not.toBeInTheDocument();
  });

  it("surfaces the has-loans conflict and keeps the member when delete fails", async () => {
    setToken("tok");
    mockManagement("admin", { deleteStatus: 409 });
    const user = userEvent.setup();
    renderWithAuth(<MembersList />);

    await user.click(await screen.findByRole("button", { name: "Delete" }));
    await user.click(screen.getByRole("button", { name: "Confirm" }));

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Member has loans and cannot be deleted",
    );
    expect(screen.getByText("Deletable Member")).toBeInTheDocument();
  });
});
