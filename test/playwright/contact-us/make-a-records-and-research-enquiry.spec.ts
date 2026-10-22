import { test, expect } from "@playwright/test";
import validateHtml from "../lib/validate-html.ts";
import checkAccessibility from "../lib/check-accessibility.ts";

const errors = {
  emptyFirstName: /Enter your first name/,
  emptySurname: /Enter your surname/,
  emptyEmail: /Enter your email address/,
  invalidEmail:
    /Enter an email address in the correct format, like name@example.com/,
  emptyEnquiry: /Enter details of your enquiry/,
  altchaNotVerified: /Check the box to confirm that you are human/,
};

test("validate HTML and check accessibility", async ({ page }) => {
  await page.goto("/contact-us/make-a-records-and-research-enquiry/");
  // Ignore invalid IDs because ALTCHA inserts a style block with the invalid ID "__altcha-css"
  await validateHtml(page, { "valid-id": ["error", { relaxed: true }] });
  await checkAccessibility(page);
});

test("empty data", async ({ page }) => {
  await page.goto("/contact-us/make-a-records-and-research-enquiry/");

  await page.waitForTimeout(3000);
  await page.getByRole("button", { name: "Submit" }).click();
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await expect(page.locator("main")).toHaveText(errors.emptyFirstName);
  await expect(page.locator("main")).toHaveText(errors.emptySurname);
  await expect(page.locator("main")).toHaveText(errors.emptyEmail);
  await expect(page.locator("main")).toHaveText(errors.emptyEnquiry);
  // await expect(page.locator("main")).toHaveText(errors.altchaNotVerified);

  await page.goto("/contact-us/make-a-records-and-research-enquiry/complete/");
  await expect(page).toHaveURL(
    /\/contact-us\/make-a-records-and-research-enquiry\//,
  );
});

test("invalid email", async ({ page }) => {
  await page.goto("/contact-us/make-a-records-and-research-enquiry/");

  await page.waitForTimeout(3000);
  await page.getByLabel("Email").fill("foobar");
  await page.getByRole("button", { name: "Submit" }).click();

  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await expect(page.locator("main")).toHaveText(errors.invalidEmail);
});

test("complete", async ({ page }) => {
  await page.goto("/contact-us/make-a-records-and-research-enquiry/");

  await page.waitForTimeout(3000);
  await page.getByLabel("First name").fill("Joe");
  await page.getByLabel("Surname").fill("Bloggs");
  await page.getByLabel("Email").fill("test@example.com");
  await page.getByLabel("Enquiry").fill("Help me");
  await page.getByRole("button", { name: "Submit" }).click();
  await validateHtml(page, { "valid-id": ["error", { relaxed: true }] });
  await checkAccessibility(page);
  await expect(page.locator("main")).toHaveText(/Request submitted/);

  await page.goto("http://localhost:65512");
  await page.waitForTimeout(1000);
  await expect(page.locator("#content")).toHaveText(/\? FOI DIRECT GENAA/);
});
