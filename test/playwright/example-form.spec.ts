import { test, expect } from "@playwright/test";
import acceptAllCookies from "./lib/accept-all-cookies.ts";
import validateHtml from "./lib/validate-html.ts";
import checkAccessibility from "./lib/check-accessibility.ts";

acceptAllCookies();

test("landing page", async ({ page }) => {
  await page.goto("/example-form/");
  await expect(page.locator("h1")).toHaveText(
    /Do you prefer pizza or chocolate?/,
  );
  await validateHtml(page);
  await checkAccessibility(page);
});
