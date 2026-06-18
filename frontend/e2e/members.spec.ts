import { expect, test } from "./fixtures";

/**
 * Members flow (#98, task 3.3): creating a member surfaces the one-time initial
 * password once, and it is not shown again on a subsequent read.
 */
test.describe("Members", () => {
  test("creating a member shows the initial password once", async ({ page, loginAs }) => {
    await loginAs("admin");
    await page.goto("/members");

    await page.getByRole("link", { name: "New member" }).click();
    await expect(page).toHaveURL(/\/members\/new$/);
    await page.getByLabel("Full name").fill("E2E New Member");
    await page.getByLabel("Email").fill("e2e.new.member@example.com");
    await page.getByRole("button", { name: "Save" }).click();

    // The one-time initial password is shown on the creation confirmation.
    await expect(page.getByRole("heading", { name: "Member created" })).toBeVisible();
    await expect(page.getByText("Initial password")).toBeVisible();

    // Opening the member afterwards must not expose the password again.
    await page.getByRole("link", { name: "View member" }).click();
    await expect(page).toHaveURL(/\/members\/.+$/);
    await expect(page.getByRole("heading", { name: "E2E New Member" })).toBeVisible();
    await expect(page.getByText("Initial password")).toHaveCount(0);
  });
});
