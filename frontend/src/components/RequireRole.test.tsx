import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import { Route, Routes } from "react-router";
import { RequireRole } from "./RequireRole";
import { canViewMembers } from "../auth/roles";
import { setToken } from "../auth/tokenStore";
import { jsonResponse, makeUser, renderWithAuth } from "../test/utils";
import type { UserRole } from "../api/types";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

/** A guarded `/members` route (allowing `canViewMembers`) plus a fallback, so we
 * can assert the guard renders the page, the forbidden screen, or nothing. */
function renderGuarded() {
  return renderWithAuth(
    <Routes>
      <Route element={<RequireRole allow={canViewMembers} />}>
        <Route path="/members" element={<div>Members content</div>} />
      </Route>
    </Routes>,
    { initialEntries: ["/members"] },
  );
}

function mockRole(role: UserRole) {
  fetchMock.mockResolvedValue(jsonResponse(makeUser({ role })));
}

beforeEach(() => {
  fetchMock.mockReset();
  setToken("tok");
});

describe("RequireRole", () => {
  it("renders the guarded route when the role is allowed", async () => {
    mockRole("staff");
    renderGuarded();

    expect(await screen.findByText("Members content")).toBeInTheDocument();
    expect(screen.queryByText("Not allowed")).not.toBeInTheDocument();
  });

  it("renders the forbidden screen when the role is not allowed", async () => {
    mockRole("member");
    renderGuarded();

    expect(await screen.findByText("Not allowed")).toBeInTheDocument();
    expect(screen.queryByText("Members content")).not.toBeInTheDocument();
    // A way back out is offered rather than a dead end.
    expect(screen.getByRole("link", { name: "Back to books" })).toBeInTheDocument();
  });
});
