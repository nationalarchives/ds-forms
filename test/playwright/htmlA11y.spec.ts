import { test, expect } from "@playwright/test";
import validateHtml from "./lib/validate-html.ts";
import checkAccessibility from "./lib/check-accessibility.ts";

test("validate HTML and check accessibility", async ({ page }) => {
  await page.goto("/test/redirect-when-complete/");
  await expect(page.locator("main")).not.toHaveText(/There is a problem/);
  await validateHtml(page);
  await checkAccessibility(page);

  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await validateHtml(page);
  await checkAccessibility(page);
});
