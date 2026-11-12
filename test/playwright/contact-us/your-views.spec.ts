import { test, expect } from "@playwright/test";
import validateHtml from "../lib/validate-html.ts";
import checkAccessibility from "../lib/check-accessibility.ts";

const errors = {
  invalidEmail:
    /Enter an email address in the correct format, like name@example.com/,
  emptyReason: /Enter details of your enquiry/,
  emptyEnquiry: /Enter details of your enquiry/,
};

test("validate HTML and check accessibility", async ({ page }) => {
  await page.goto("/contact-us/your-views/");
  await checkAccessibility(page);
});

test("empty data", async ({ page }) => {
  await page.goto("/contact-us/your-views/");

  await page.waitForTimeout(3000);
  await page.getByRole("button", { name: "Submit" }).click();
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await expect(page.locator("main")).toHaveText(errors.emptyReason);
  await expect(page.locator("main")).toHaveText(errors.emptyEnquiry);

  await page.goto("/contact-us/your-views/complete/");
  await expect(page).toHaveURL(/\/contact-us\/your-views\//);
});

test("invalid email", async ({ page }) => {
  await page.goto("/contact-us/your-views/");

  await page.waitForTimeout(3000);
  await page.getByLabel("Email").fill("foobar");
  await page.getByRole("button", { name: "Submit" }).click();

  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await expect(page.locator("main")).toHaveText(errors.invalidEmail);
});

test("complete", async ({ page }) => {
  await page.goto("/contact-us/your-views/");

  await page.waitForTimeout(3000);
  await page.getByLabel("Name").fill("Joe Bloggs");
  await page.getByLabel("Email").fill("test@example.com");
  await page.getByLabel("Suggestion or comment").check();
  await page.getByLabel("Enquiry").fill("Good");
  await page.getByRole("button", { name: "Submit" }).click();
  await validateHtml(page, { "valid-id": ["error", { relaxed: true }] });
  await checkAccessibility(page);
  await expect(page.locator("main")).toHaveText(/Your view was submitted/);

  //   await page.goto("http://localhost:65512");
  //   await page.waitForTimeout(1000);
  //   await expect(page.locator("#content")).toHaveText(/\? FOI DIRECT GENAA/);
});
