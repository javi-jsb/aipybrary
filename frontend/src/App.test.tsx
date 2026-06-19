import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import App from "./App";
import { setToken } from "./auth/tokenStore";
import { jsonResponse, renderWithAuth } from "./test/utils";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

beforeEach(() => {
  fetchMock.mockReset();
});

describe("App routing and auth gating", () => {
  it("redirects to the login screen when no token is stored", () => {
    renderWithAuth(<App />);

    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    // The protected view must not mount, so no books request is issued.
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("redirects a protected deep link to login when unauthenticated", () => {
    renderWithAuth(<App />, { initialEntries: ["/books"] });

    expect(screen.getByRole("button", { name: "Sign in" })).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders the books view at /books when a token is present", async () => {
    setToken("tok");
    fetchMock.mockResolvedValue(jsonResponse({ items: [], total: 0, page: 1, size: 50, pages: 0 }));
    renderWithAuth(<App />, { initialEntries: ["/books"] });

    expect(await screen.findByRole("heading", { name: "Books" })).toBeInTheDocument();
  });

  it("shows the forbidden screen when a member deep-links to /members", async () => {
    setToken("tok");
    // The member's role resolves; the members route is guarded, so a direct hit
    // lands on the "not allowed" screen instead of issuing the (403) list request.
    fetchMock.mockImplementation((url) => {
      const u = String(url);
      if (u.includes("/auth/me"))
        return Promise.resolve(
          jsonResponse({
            id: "u1",
            email: "member@example.com",
            role: "member",
            is_active: true,
            created_at: "2026-01-01T00:00:00Z",
            updated_at: "2026-01-01T00:00:00Z",
          }),
        );
      return Promise.resolve(jsonResponse({}, 404));
    });
    renderWithAuth(<App />, { initialEntries: ["/members"] });

    expect(await screen.findByText("Not allowed")).toBeInTheDocument();
    const requestedMembersList = fetchMock.mock.calls.some(([url]) =>
      String(url).match(/\/members(\?|$)/),
    );
    expect(requestedMembersList).toBe(false);
  });
});
