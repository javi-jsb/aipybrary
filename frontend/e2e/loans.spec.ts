import { expect, test } from "./fixtures";

/**
 * Loans flow (#98, task 3.5): borrow an available copy, return an active loan,
 * and surface a business-rule error (the active-loan limit).
 */
test.describe("Loans", () => {
  test("borrow an available copy", async ({ page, loginAs }) => {
    await loginAs("admin");
    await page.goto("/loans/new");

    await page.getByLabel("Member").selectOption({ label: "Demo Member" });
    await page.getByLabel("Book").selectOption({ label: "Crime and Punishment" });
    await page.getByLabel("Available copy").selectOption({ label: "CP-001" });
    await page.getByRole("button", { name: "Borrow" }).click();

    await expect(page).toHaveURL(/\/loans$/);
    const loan = page.getByRole("listitem").filter({ hasText: "Demo Member" });
    await expect(loan).toBeVisible();
    await expect(loan.getByText("CP-001")).toBeVisible();
  });

  test("return an active loan", async ({ page, loginAs }) => {
    await loginAs("admin");
    await page.goto("/loans");

    // Ada Lovelace holds the single returnable seeded loan (DQ-001).
    const adaLoan = page.getByRole("listitem").filter({ hasText: "Ada Lovelace" });
    await adaLoan.getByRole("button", { name: "Return" }).click();

    await expect(adaLoan.getByText(/Returned/)).toBeVisible();
    await expect(adaLoan.getByRole("button", { name: "Return" })).toHaveCount(0);
  });

  test("borrowing past the active-loan limit surfaces a business-rule error", async ({
    page,
    loginAs,
  }) => {
    await loginAs("admin");
    await page.goto("/loans/new");

    // "Maxed Member" is seeded at the active-loan limit.
    await page.getByLabel("Member").selectOption({ label: "Maxed Member" });
    await page.getByLabel("Book").selectOption({ label: "Crime and Punishment" });
    await page.getByLabel("Available copy").selectOption({ label: "CP-001" });
    await page.getByRole("button", { name: "Borrow" }).click();

    await expect(page.getByRole("alert")).toContainText(/active loan limit/i);
    await expect(page).toHaveURL(/\/loans\/new$/);
  });
});
