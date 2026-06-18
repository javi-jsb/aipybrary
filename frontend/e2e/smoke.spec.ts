import { expect, test } from "@playwright/test";

/**
 * Harness smoke test (#96): proves the E2E tooling can boot the SPA and drive it
 * in a real browser. It asserts the login screen renders without touching the
 * API — backend-dependent flows arrive with the data/isolation slice (#97).
 */
test("login screen renders for an unauthenticated visitor", async ({ page }) => {
  await page.goto("/login");

  await expect(page.getByRole("heading", { name: "aipybrary" })).toBeVisible();
  await expect(page.getByText("Sign in to continue")).toBeVisible();
  await expect(page.getByLabel("Email")).toBeVisible();
  await expect(page.getByLabel("Password")).toBeVisible();
  await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
});
