import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { LoanForm } from "./LoanForm";
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

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

function listResponse(items: unknown[]) {
  return jsonResponse({ items, total: items.length, page: 1, size: 100, pages: 1 });
}

function renderForm() {
  return renderWithAuth(
    <Routes>
      <Route path="/loans/new" element={<LoanForm />} />
      <Route path="/loans" element={<div>Loans landing</div>} />
    </Routes>,
    { initialEntries: ["/loans/new"] },
  );
}

/**
 * Wire the form's data sources: members (one active, one suspended), a single
 * book with two copies, and an active loan holding `copy-1` so only `copy-2`
 * is offered. `POST /loans` succeeds (201) unless `borrowStatus`/`detail` model
 * a backend rejection.
 */
function mockForm(options: { borrowStatus?: number; detail?: string } = {}) {
  fetchMock.mockImplementation((url, init) => {
    const u = String(url);
    const method = init?.method ?? "GET";
    if (u.includes("/auth/me")) return Promise.resolve(jsonResponse(makeUser({ role: "staff" })));
    if (u.includes("/loans") && method === "POST") {
      if (options.borrowStatus) {
        return Promise.resolve(jsonResponse({ detail: options.detail }, options.borrowStatus));
      }
      return Promise.resolve(jsonResponse(makeLoan({ id: "loan-new" }), 201));
    }
    if (u.includes("/loans"))
      return Promise.resolve(listResponse([makeLoan({ id: "loan-1", book_copy_id: "copy-1" })]));
    if (u.includes("/members"))
      return Promise.resolve(
        listResponse([
          makeMember({ id: "member-1", full_name: "Ada Lovelace", status: "active" }),
          makeMember({ id: "member-2", full_name: "Bob Suspended", status: "suspended" }),
        ]),
      );
    if (u.includes("/book-copies"))
      return Promise.resolve(
        listResponse([
          makeBookCopy({ id: "copy-1", barcode: "BC-0001" }),
          makeBookCopy({ id: "copy-2", barcode: "BC-0002" }),
        ]),
      );
    if (u.includes("/books"))
      return Promise.resolve(listResponse([makeBook({ id: "book-1", title: "Clean Code" })]));
    return Promise.resolve(jsonResponse({}, 404));
  });
}

beforeEach(() => {
  fetchMock.mockReset();
  setToken("tok");
});

describe("LoanForm", () => {
  it("requires a member before submitting", async () => {
    mockForm();
    const user = userEvent.setup();
    renderForm();

    await user.click(await screen.findByRole("button", { name: "Borrow" }));

    expect(await screen.findByText("Select a member.")).toBeInTheDocument();
    expect(fetchMock.mock.calls.some(([, init]) => init?.method === "POST")).toBe(false);
  });

  it("offers only active members and only available copies", async () => {
    mockForm();
    const user = userEvent.setup();
    renderForm();

    expect(await screen.findByRole("option", { name: "Ada Lovelace" })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: "Bob Suspended" })).not.toBeInTheDocument();

    await user.selectOptions(await screen.findByLabelText("Member"), "member-1");
    await user.selectOptions(await screen.findByLabelText("Book"), "book-1");

    // copy-1 is on an active loan, so only copy-2 is offered.
    expect(await screen.findByRole("option", { name: /BC-0002/ })).toBeInTheDocument();
    expect(screen.queryByRole("option", { name: /BC-0001/ })).not.toBeInTheDocument();
  });

  it("borrows the selected copy and navigates back to the loans list", async () => {
    mockForm();
    const user = userEvent.setup();
    renderForm();

    await screen.findByRole("option", { name: "Ada Lovelace" });
    await user.selectOptions(await screen.findByLabelText("Member"), "member-1");
    await user.selectOptions(await screen.findByLabelText("Book"), "book-1");
    await user.selectOptions(await screen.findByLabelText("Available copy"), "copy-2");
    await user.click(screen.getByRole("button", { name: "Borrow" }));

    expect(await screen.findByText("Loans landing")).toBeInTheDocument();
    const post = fetchMock.mock.calls.find(([, init]) => init?.method === "POST");
    expect(JSON.parse(post?.[1]?.body as string)).toEqual({
      member_id: "member-1",
      book_copy_id: "copy-2",
    });
  });

  it("surfaces a business-rule error from the backend", async () => {
    mockForm({ borrowStatus: 422, detail: "Member has reached the active loan limit" });
    const user = userEvent.setup();
    renderForm();

    await screen.findByRole("option", { name: "Ada Lovelace" });
    await user.selectOptions(await screen.findByLabelText("Member"), "member-1");
    await user.selectOptions(await screen.findByLabelText("Book"), "book-1");
    await user.selectOptions(await screen.findByLabelText("Available copy"), "copy-2");
    await user.click(screen.getByRole("button", { name: "Borrow" }));

    expect(await screen.findByText("Member has reached the active loan limit")).toBeInTheDocument();
    expect(screen.queryByText("Loans landing")).not.toBeInTheDocument();
  });
});
