import { describe, it, expect } from "vitest";
import { screen, within } from "@testing-library/react";
import { HelpScreen } from "./HelpScreen";
import { renderWithAuth } from "../test/utils";

/** Find the matrix row whose first cell matches the given capability label. */
function rowFor(label: string): HTMLElement {
  const cell = screen.getByText(label);
  const row = cell.closest("tr");
  if (!row) throw new Error(`No row found for capability "${label}"`);
  return row;
}

describe("HelpScreen", () => {
  it("renders the feature overview and a role column per role", () => {
    renderWithAuth(<HelpScreen />);

    expect(screen.getByRole("heading", { name: "Help", level: 1 })).toBeInTheDocument();
    // One feature note per area.
    expect(screen.getByRole("columnheader", { name: "admin" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "staff" })).toBeInTheDocument();
    expect(screen.getByRole("columnheader", { name: "member" })).toBeInTheDocument();
  });

  it("derives the matrix from the real role gating", () => {
    renderWithAuth(<HelpScreen />);

    // Read capability: open to every role.
    const view = within(rowFor("View the catalog")).getAllByLabelText("allowed");
    expect(view).toHaveLength(3);

    // admin/staff manage books; member does not.
    const manageBooks = rowFor("Create, edit, delete books");
    expect(within(manageBooks).getAllByLabelText("allowed")).toHaveLength(2);
    expect(within(manageBooks).getAllByLabelText("not allowed")).toHaveLength(1);

    // Deleting members is admin-only.
    const deleteMembers = rowFor("Delete members");
    expect(within(deleteMembers).getAllByLabelText("allowed")).toHaveLength(1);
    expect(within(deleteMembers).getAllByLabelText("not allowed")).toHaveLength(2);
  });

  it("flags the gating as UX-only, not a security boundary", () => {
    renderWithAuth(<HelpScreen />);

    expect(screen.getByText(/not a security/i)).toBeInTheDocument();
  });
});
