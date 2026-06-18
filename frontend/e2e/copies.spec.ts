import { expect, test } from "./fixtures";

/**
 * Book-copy management flow (#98, task 3.4): add and remove a copy of a book
 * and assert the copies view reflects the changes.
 */
test.describe("Book copies", () => {
  test("add and remove a copy", async ({ page, loginAs }) => {
    await loginAs("admin");
    await page.goto("/books");

    // Open the copies view for the seeded "Don Quixote".
    const quixote = page.getByRole("listitem").filter({ hasText: "Don Quixote" });
    await quixote.getByRole("link", { name: /Copies/ }).click();
    await expect(page).toHaveURL(/\/books\/.+\/copies$/);

    // ----- Add -----
    await page.getByLabel("Barcode").fill("E2E-COPY-1");
    await page.getByRole("button", { name: "Add copy" }).click();

    const added = page.getByRole("listitem").filter({ hasText: "E2E-COPY-1" });
    await expect(added).toBeVisible();

    // ----- Remove (two-step confirm) -----
    await added.getByRole("button", { name: "Remove" }).click();
    await added.getByRole("button", { name: "Confirm" }).click();

    await expect(page.getByText("E2E-COPY-1")).toHaveCount(0);
  });
});
