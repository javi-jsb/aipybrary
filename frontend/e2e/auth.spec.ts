import { expect, test } from "./fixtures";

/**
 * Authentication flow (#98, task 3.1): the real login form against the real
 * API — valid credentials land in the app, invalid ones surface an error.
 */
test.describe("Authentication", () => {
  test("valid credentials sign in and land on Books", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("admin@aipybrary.dev");
    await page.getByLabel("Password").fill("pass");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page).toHaveURL(/\/books$/);
    await expect(page.getByRole("heading", { name: "Books" })).toBeVisible();
  });

  test("invalid credentials surface an error and stay on login", async ({ page }) => {
    await page.goto("/login");
    await page.getByLabel("Email").fill("admin@aipybrary.dev");
    await page.getByLabel("Password").fill("wrong-password");
    await page.getByRole("button", { name: "Sign in" }).click();

    await expect(page.getByRole("alert")).toBeVisible();
    await expect(page).toHaveURL(/\/login$/);
  });
});
