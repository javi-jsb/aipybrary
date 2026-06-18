import { expect, test } from "./fixtures";

/**
 * Books CRUD flow (#98, task 3.2): create, edit, and delete a book through the
 * SPA, asserting each operation is reflected in the list.
 */
test.describe("Books CRUD", () => {
  test("create, edit, and delete a book", async ({ page, loginAs }) => {
    await loginAs("admin");
    await page.goto("/books");

    // ----- Create -----
    await page.getByRole("link", { name: "New book" }).click();
    await expect(page).toHaveURL(/\/books\/new$/);
    await page.getByLabel("Title").fill("E2E Test Book");
    await page.getByLabel("Author").fill("E2E Author");
    await page.getByRole("button", { name: "Save" }).click();

    await expect(page).toHaveURL(/\/books$/);
    const created = page.getByRole("listitem").filter({ hasText: "E2E Test Book" });
    await expect(created).toBeVisible();

    // ----- Edit -----
    await created.getByRole("link", { name: "Edit" }).click();
    await expect(page).toHaveURL(/\/books\/.+\/edit$/);
    await page.getByLabel("Title").fill("E2E Edited Book");
    await page.getByRole("button", { name: "Save" }).click();

    await expect(page).toHaveURL(/\/books$/);
    await expect(page.getByText("E2E Edited Book")).toBeVisible();
    await expect(page.getByText("E2E Test Book")).toHaveCount(0);

    // ----- Delete (two-step confirm) -----
    const edited = page.getByRole("listitem").filter({ hasText: "E2E Edited Book" });
    await edited.getByRole("button", { name: "Delete" }).click();
    await edited.getByRole("button", { name: "Confirm" }).click();

    await expect(page.getByText("E2E Edited Book")).toHaveCount(0);
  });
});
