import { test, expect } from "@playwright/test";
import validateHtml from "./lib/validate-html.ts";
import checkAccessibility from "./lib/check-accessibility.ts";

test("form not complete", async ({ page }) => {
  await page.goto("/test/redirect-when-complete/");
  await validateHtml(page);
  await checkAccessibility(page);
  await expect(page.locator("main")).not.toHaveText(/There is a problem/);

  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/redirect-when-complete/");
  await expect(page.locator("main")).toHaveText(/There is a problem/);
});

test("page redirect", async ({ page }) => {
  await page.goto("/test/redirect-when-complete/");

  await page.getByRole("radio", { name: "Alpha" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/redirect-when-complete/alpha/");
});

test("final page redirect", async ({ page }) => {
  await page.goto("/test/redirect-when-complete/");

  await page.getByRole("radio", { name: "Beta" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/redirect-when-complete/beta/");
});

test("external redirect", async ({ page }) => {
  await page.goto("/test/redirect-when-complete/");

  await page.getByRole("radio", { name: "Gamma" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL(
    "https://design-system.nationalarchives.gov.uk/",
  );
});

test("any page redirect", async ({ page }) => {
  await page.goto("/test/redirect-when-complete/alpha/");

  await page.getByRole("radio", { name: "Alpha" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/redirect-when-complete/beta/");

  await page.goto("/test/redirect-when-complete/alpha/");

  await page.getByRole("radio", { name: "Beta" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/redirect-when-complete/beta/");

  await page.goto("/test/redirect-when-complete/alpha/");

  await page.getByRole("radio", { name: "Gamma" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/redirect-when-complete/beta/");
});
