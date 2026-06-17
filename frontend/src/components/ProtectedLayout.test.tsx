import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { ProtectedLayout } from "./ProtectedLayout";
import { getToken, setToken } from "../auth/tokenStore";
import { jsonResponse, renderWithAuth } from "../test/utils";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

function meResponse() {
  return jsonResponse({
    id: "user-1",
    email: "staff@example.com",
    role: "staff",
    is_active: true,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
  });
}

/** A protected route tree: the layout wraps a stub view; `/login` is a sibling. */
function renderLayout(initialEntries = ["/books"]) {
  return renderWithAuth(
    <Routes>
      <Route element={<ProtectedLayout />}>
        <Route path="/books" element={<div>Books content</div>} />
      </Route>
      <Route path="/login" element={<div>Login route</div>} />
    </Routes>,
    { initialEntries },
  );
}

beforeEach(() => {
  fetchMock.mockReset();
});

describe("ProtectedLayout", () => {
  it("redirects to /login and renders nothing protected when unauthenticated", () => {
    renderLayout();

    expect(screen.getByText("Login route")).toBeInTheDocument();
    expect(screen.queryByText("Books content")).not.toBeInTheDocument();
    // No protected request (including GET /auth/me) is issued without a session.
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders the nav shell, the outlet, and the current user when authenticated", async () => {
    setToken("tok");
    fetchMock.mockResolvedValue(meResponse());
    renderLayout();

    expect(screen.getByText("Books content")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Sign out" })).toBeInTheDocument();
    // The role resolved from GET /auth/me drives the UI gating display.
    expect(await screen.findByText("staff@example.com")).toBeInTheDocument();
    expect(screen.getByText("staff")).toBeInTheDocument();
  });

  it("clears the session and redirects to /login on sign out", async () => {
    setToken("tok");
    fetchMock.mockResolvedValue(meResponse());
    const user = userEvent.setup();
    renderLayout();

    await user.click(screen.getByRole("button", { name: "Sign out" }));

    expect(getToken()).toBeNull();
    expect(screen.getByText("Login route")).toBeInTheDocument();
  });
});
