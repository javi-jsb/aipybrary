import { describe, it, expect, vi, beforeEach } from "vitest";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { Route, Routes } from "react-router";
import { MemberForm } from "./MemberForm";
import { setToken } from "../auth/tokenStore";
import { jsonResponse, makeMember, renderWithAuth } from "../test/utils";

const fetchMock = vi.fn<typeof fetch>();
vi.stubGlobal("fetch", fetchMock);

/** Render the form route alongside stub list/detail routes so navigation on
 * success is observable. */
function renderForm(initialEntries: string[]) {
  return renderWithAuth(
    <Routes>
      <Route path="/members" element={<div>Members list</div>} />
      <Route path="/members/new" element={<MemberForm />} />
      <Route path="/members/:id" element={<div>Member detail</div>} />
      <Route path="/members/:id/edit" element={<MemberForm />} />
    </Routes>,
    { initialEntries },
  );
}

beforeEach(() => {
  fetchMock.mockReset();
  setToken("tok");
});

describe("MemberForm — create", () => {
  it("POSTs the new member and shows the one-time initial password without navigating", async () => {
    fetchMock.mockResolvedValue(
      jsonResponse({ ...makeMember({ id: "m1" }), initial_password: "Sup3rSecret!" }, 201),
    );
    const user = userEvent.setup();
    renderForm(["/members/new"]);

    await user.type(screen.getByLabelText("Full name"), "Ada Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.click(screen.getByRole("button", { name: "Save" }));

    // The one-time password is shown on the success panel, not navigated away.
    expect(await screen.findByText("Sup3rSecret!")).toBeInTheDocument();
    expect(screen.getByText("Member created")).toBeInTheDocument();
    expect(screen.queryByText("Members list")).not.toBeInTheDocument();

    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("http://localhost:8077/members");
    expect(init?.method).toBe("POST");
    expect(JSON.parse(init?.body as string)).toEqual({
      full_name: "Ada Lovelace",
      email: "ada@example.com",
      status: "active",
    });
  });

  it("blocks submission on an invalid email without calling the API", async () => {
    const user = userEvent.setup();
    renderForm(["/members/new"]);

    await user.type(screen.getByLabelText("Full name"), "Ada Lovelace");
    await user.type(screen.getByLabelText("Email"), "not-an-email");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Invalid email format.")).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("surfaces a duplicate-email conflict on the form and preserves input", async () => {
    fetchMock.mockResolvedValue(jsonResponse({ detail: "Email already registered" }, 409));
    const user = userEvent.setup();
    renderForm(["/members/new"]);

    await user.type(screen.getByLabelText("Full name"), "Ada Lovelace");
    await user.type(screen.getByLabelText("Email"), "ada@example.com");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByRole("alert")).toHaveTextContent("Email already registered");
    expect(screen.queryByText("Member created")).not.toBeInTheDocument();
    expect(screen.getByLabelText("Full name")).toHaveValue("Ada Lovelace");
  });
});

describe("MemberForm — edit", () => {
  it("prefills from the fetched member, keeps email read-only, PATCHes, then navigates to detail", async () => {
    const member = makeMember({ id: "m1", full_name: "Old name", status: "active" });
    fetchMock.mockImplementation((_url, init) => {
      const method = init?.method ?? "GET";
      if (method === "PATCH") {
        return Promise.resolve(jsonResponse({ ...member, full_name: "New name" }));
      }
      return Promise.resolve(jsonResponse(member));
    });
    const user = userEvent.setup();
    renderForm(["/members/m1/edit"]);

    const nameInput = await screen.findByLabelText("Full name");
    expect(nameInput).toHaveValue("Old name");
    // Email is not an editable input in edit mode.
    expect(screen.queryByRole("textbox", { name: "Email" })).not.toBeInTheDocument();
    expect(screen.getByText("ada@example.com")).toBeInTheDocument();

    await user.clear(nameInput);
    await user.type(nameInput, "New name");
    await user.click(screen.getByRole("button", { name: "Save" }));

    expect(await screen.findByText("Member detail")).toBeInTheDocument();
    const patchCall = fetchMock.mock.calls.find(([, init]) => init?.method === "PATCH");
    expect(patchCall?.[0]).toBe("http://localhost:8077/members/m1");
    expect(JSON.parse(patchCall?.[1]?.body as string)).toEqual({
      full_name: "New name",
      status: "active",
    });
  });
});
