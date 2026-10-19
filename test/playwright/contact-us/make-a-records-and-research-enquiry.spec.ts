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
  await validateHtml(page, { "valid-id": "warn" });
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
  await expect(page.locator("main")).toHaveText(errors.altchaNotVerified);

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

// test("complete", async ({ page }) => {
//   await page.goto("/contact-us/make-a-records-and-research-enquiry/");

//   await page.waitForTimeout(3000);

//   await page.getByLabel("Record IAID").fill("C1234");
//   await page.getByLabel("What is the error?").fill("Something");
//   await page.getByLabel("What is the correct information?").fill("Nothing");
//   await page.getByRole("button", { name: "Submit" }).click();
//   await expect(page).toHaveURL(/\/contact-us\/make-a-records-and-research-enquiry\/complete\//);
//   await expect(page.locator("main")).toHaveText(/Request submitted/);
//   await expect(page.locator("main")).toHaveText(
//     /Thank you for taking the time to help us improve the catalogue\. We may contact you within the next 10 days if we need further information\./,
//   );
//   await expect(page.locator("main")).toHaveText(
//     /We will not be able to notify you if your suggestion is successful\. This is due to the high volume of suggestions we receive\./,
//   );
//   await validateHtml(page);
//   await checkAccessibility(page);

//   await page.getByRole("link", { name: "Submit another enquiry" }).click();
//   await expect(page).toHaveURL(/\/contact-us\/make-a-records-and-research-enquiry\//);

//   await page.goto("/contact-us/make-a-records-and-research-enquiry/complete/");
//   await expect(page).toHaveURL(/\/contact-us\/make-a-records-and-research-enquiry\//);
// });
