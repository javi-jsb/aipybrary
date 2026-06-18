import { expect, test } from "./fixtures";

/**
 * Role-aware visibility (#98, task 3.6): admin/staff see the management
 * controls; a member sees the same screens read-only (controls hidden). This is
 * UX-only gating — see `src/auth/roles.ts`.
 */
test.describe("Role-aware visibility", () => {
  test("an admin sees the management controls", async ({ page, loginAs }) => {
    await loginAs("admin");

    await page.goto("/books");
    await expect(page.getByRole("link", { name: "New book" })).toBeVisible();

    await page.goto("/members");
    await expect(page.getByRole("link", { name: "New member" })).toBeVisible();

    await page.goto("/loans");
    await expect(page.getByRole("link", { name: "New loan" })).toBeVisible();
  });

  test("a member sees the screens read-only", async ({ page, loginAs }) => {
    await loginAs("member");

    await page.goto("/books");
    await expect(page.getByRole("heading", { name: "Books" })).toBeVisible();
    await expect(page.getByRole("link", { name: "New book" })).toHaveCount(0);
    await expect(page.getByRole("link", { name: "Edit" })).toHaveCount(0);

    await page.goto("/members");
    await expect(page.getByRole("heading", { name: "Members" })).toBeVisible();
    await expect(page.getByRole("link", { name: "New member" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Delete" })).toHaveCount(0);

    await page.goto("/loans");
    await expect(page.getByRole("heading", { name: "Loans" })).toBeVisible();
    await expect(page.getByRole("link", { name: "New loan" })).toHaveCount(0);
    await expect(page.getByRole("button", { name: "Return" })).toHaveCount(0);
  });
});
