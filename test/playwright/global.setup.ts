import { test as setup, expect } from "@playwright/test";

setup("clear out previous emails", async ({ page }) => {
  await page.goto("http://localhost:65512");
  await page.getByRole("button", { name: "Clear" }).click();
  await expect(page.locator("#content > .email")).toHaveCount(0);
});
