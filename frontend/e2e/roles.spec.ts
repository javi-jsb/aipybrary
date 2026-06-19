import { expect, test } from "./fixtures";

/**
 * Role-aware visibility against the real stack. The backend now *enforces* the
 * permission matrix (the `enforce-role-based-authorization` change), and the SPA
 * mirrors it: admin/staff see the management controls and the members area; a
 * member sees the catalog and their own loans read-only, has no members
 * navigation, and is sent to a "not allowed" screen if they deep-link a route
 * their role can't use. See `src/auth/roles.ts`.
 */
test.describe("Role-aware visibility", () => {
  test("an admin sees the management controls and the members area", async ({ page, loginAs }) => {
    await loginAs("admin");

    await page.goto("/books");
    await expect(page.getByRole("link", { name: "Members" })).toBeVisible();
    await expect(page.getByRole("link", { name: "New book" })).toBeVisible();

    await page.goto("/members");
    await expect(page.getByRole("link", { name: "New member" })).toBeVisible();

    await page.goto("/loans");
    await expect(page.getByRole("link", { name: "New loan" })).toBeVisible();
  });

  test("a member views the catalog read-only", async ({ page, loginAs }) => {
    await loginAs("member");

    await page.goto("/books");
    await expect(page.getByRole("heading", { name: "Books" })).toBeVisible();
    await expect(page.getByRole("link", { name: "New book" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Edit" })).toHaveCount(0);
    // The members navigation entry is hidden for a member.
    await expect(page.getByRole("link", { name: "Members" })).toHaveCount(0);
  });

  test("a member is denied the members area, even by deep link", async ({ page, loginAs }) => {
    await loginAs("member");

    await page.goto("/members");
    await expect(page.getByRole("heading", { name: "Not allowed" })).toBeVisible();
    await expect(page.getByRole("heading", { name: "Members" })).toHaveCount(0);

    // The single-member routes are guarded the same way.
    await page.goto("/members/new");
    await expect(page.getByRole("heading", { name: "Not allowed" })).toBeVisible();
  });

  test("a member sees only their own loans, with no management controls", async ({
    page,
    loginAs,
  }) => {
    await loginAs("member");

    await page.goto("/loans");
    await expect(page.getByRole("heading", { name: "Loans" })).toBeVisible();
    // The seeded member ("Demo Member") holds no loans; the four seeded loans
    // belong to other members, so the backend scoping hides them entirely.
    await expect(page.getByText("No loans yet.")).toBeVisible();
    await expect(page.getByRole("link", { name: "New loan" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Return" })).toHaveCount(0);

    // Deep-linking the borrow form is forbidden, not just hidden.
    await page.goto("/loans/new");
    await expect(page.getByRole("heading", { name: "Not allowed" })).toBeVisible();
  });
});
