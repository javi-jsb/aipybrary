import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { LoansList } from "./LoansList";
import { setToken } from "../auth/tokenStore";
import {
  jsonResponse,
  makeBook,
  makeBookCopy,
  makeLoan,
  makeMember,
  makeUser,
  renderWithAuth,
} from "../test/utils";
import type { Loan, UserRole } from "../api/types";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

function listResponse(items: unknown[]) {
  return jsonResponse({ items, total: items.length, page: 1, size: 100, pages: 1 });
}

function renderLoans() {
  return renderWithAuth(
    <Routes>
      <Route path="/loans" element={<LoansList />} />
    </Routes>,
    { initialEntries: ["/loans"] },
  );
}

/**
 * Wire the endpoints the loans view reads: the current user's role, the loans
 * list (mutable so a return refetch reflects the change), members and books for
 * name resolution, and each loan's copy by id. `POST /loans/{id}/return` marks
 * the loan returned (or fails when `returnStatus` is set).
 */
function mockLoans(
  role: UserRole,
  options: { initial?: Loan[]; returnStatus?: number; email?: string } = {},
) {
  let loans: Loan[] = options.initial ?? [makeLoan({ id: "loan-1" })];
  fetchMock.mockImplementation((url, init) => {
    const u = String(url);
    const method = init?.method ?? "GET";
    if (u.includes("/auth/me"))
      return Promise.resolve(
        jsonResponse(makeUser(options.email ? { role, email: options.email } : { role })),
      );
    if (u.includes("/loans/") && method === "POST") {
      if (options.returnStatus) {
        return Promise.resolve(
          jsonResponse({ detail: "Loan is already returned" }, options.returnStatus),
        );
      }
      loans = loans.map((l) =>
        l.id === "loan-1" ? { ...l, returned_at: "2026-06-18T00:00:00Z", status: "returned" } : l,
      );
      return Promise.resolve(jsonResponse(loans.find((l) => l.id === "loan-1")));
    }
    if (u.includes("/loans")) return Promise.resolve(listResponse(loans));
    if (u.includes("/members")) return Promise.resolve(listResponse([makeMember()]));
    if (u.includes("/book-copies/"))
      return Promise.resolve(jsonResponse(makeBookCopy({ id: "copy-1", barcode: "BC-0001" })));
    if (u.includes("/books")) return Promise.resolve(listResponse([makeBook()]));
    return Promise.resolve(jsonResponse({}, 404));
  });
}

beforeEach(() => {
  fetchMock.mockReset();
  setToken("tok");
});

describe("LoansList", () => {
  it("shows a loading state, then renders each loan with member, copy, and book", async () => {
    mockLoans("staff");
    renderLoans();

    expect(screen.getByText("Loading loans…")).toBeInTheDocument();

    expect(await screen.findByText("Ada Lovelace")).toBeInTheDocument();
    expect(await screen.findByText("BC-0001")).toBeInTheDocument();
    expect(screen.getByText(/The Pragmatic Programmer/)).toBeInTheDocument();
    expect(screen.getByText("active")).toBeInTheDocument();
  });

  it("shows an empty state when there are no loans", async () => {
    mockLoans("staff", { initial: [] });
    renderLoans();

    expect(await screen.findByText("No loans yet.")).toBeInTheDocument();
  });

  it("shows an error message when the loans request fails", async () => {
    fetchMock.mockImplementation((url) => {
      const u = String(url);
      if (u.includes("/auth/me")) return Promise.resolve(jsonResponse(makeUser({ role: "staff" })));
      if (u.includes("/loans"))
        return Promise.resolve(jsonResponse({ detail: "Server error" }, 500));
      return Promise.resolve(jsonResponse({}, 404));
    });
    renderLoans();

    expect(await screen.findByRole("alert")).toHaveTextContent("Server error");
  });

  it("hides the new-loan link and return controls for a member", async () => {
    mockLoans("member", { email: "member@example.com" });
    renderLoans();

    // The member's own loans render (scoped server-side); labelled by their
    // email since they can't list members to resolve names.
    expect(await screen.findByText("member@example.com")).toBeInTheDocument();
    expect(screen.queryByRole("link", { name: "New loan" })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Return" })).not.toBeInTheDocument();
  });

  it("does not request the members list for a member (it would 403)", async () => {
    mockLoans("member", { email: "member@example.com" });
    renderLoans();

    await screen.findByText("member@example.com");
    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const requestedMembers = fetchMock.mock.calls.some(([url]) => String(url).includes("/members"));
    expect(requestedMembers).toBe(false);
  });

  it("returns a loan and reflects it as returned after the list refreshes", async () => {
    mockLoans("staff");
    const user = userEvent.setup();
    renderLoans();

    await user.click(await screen.findByRole("button", { name: "Return" }));

    expect(await screen.findByText("returned")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Return" })).not.toBeInTheDocument();
  });

  it("surfaces an error when the return fails", async () => {
    mockLoans("staff", { returnStatus: 409 });
    const user = userEvent.setup();
    renderLoans();

    await user.click(await screen.findByRole("button", { name: "Return" }));

    expect(await screen.findByText("Loan is already returned")).toBeInTheDocument();
  });
});
