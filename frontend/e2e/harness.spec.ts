import { expect, test, type Role } from "./fixtures";

/**
 * Verifies the #97 harness end-to-end: the real API runs against the dedicated
 * E2E database, the deterministic seed is present, and the role-scoped login
 * fixture produces an authenticated session. The per-area UI flows arrive in
 * #98.
 */
const ROLES: Role[] = ["admin", "staff", "member"];

test.describe("E2E harness", () => {
  test("an authenticated user sees the seeded books", async ({ page, loginAs }) => {
    await loginAs("admin");
    await page.goto("/books");

    await expect(page.getByRole("heading", { name: "Books" })).toBeVisible();
    await expect(page.getByText("Don Quixote")).toBeVisible();
    await expect(page.getByText("Crime and Punishment")).toBeVisible();
  });

  for (const role of ROLES) {
    test(`a ${role} can authenticate against the real API`, async ({ page, loginAs }) => {
      await loginAs(role);
      await page.goto("/books");

      // Reaching /books (not redirected to /login) proves the session is valid.
      await expect(page).toHaveURL(/\/books$/);
      await expect(page.getByRole("heading", { name: "Books" })).toBeVisible();
    });
  }
});
