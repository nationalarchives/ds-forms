import { test, expect } from "@playwright/test";
import validateHtml from "../lib/validate-html.ts";
import checkAccessibility from "../lib/check-accessibility.ts";

const errors = {
  emptyIaid: /Enter the record IAID/,
  invalidIaid: /Enter a valid record IAID/,
  emptyDescription: /Enter a description of the error/,
  emptyCorrectInformation: /Enter the correct information/,
  invalidEmail:
    /Enter an email address in the correct format, like name@example.com/,
};

test("validate HTML and check accessibility", async ({ page }) => {
  await page.goto("/catalogue/report-an-issue/");
  await validateHtml(page);
  await checkAccessibility(page);
});

test("empty data", async ({ page }) => {
  await page.goto("/catalogue/report-an-issue/");

  await page.getByRole("button", { name: "Submit issue" }).click();
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await expect(page.locator("main")).toHaveText(errors.emptyIaid);
  await expect(page.locator("main")).toHaveText(errors.emptyDescription);
  await expect(page.locator("main")).toHaveText(errors.emptyCorrectInformation);
  await expect(page.locator("main")).not.toHaveText(errors.invalidEmail);

  await page.goto("/catalogue/report-an-issue/complete/");
  await expect(page).toHaveURL(/\/catalogue\/report-an-issue\//);
});

test("invalid IAID", async ({ page }) => {
  await page.goto("/catalogue/report-an-issue/");

  await page.getByLabel("Record IAID").fill("invalid");
  await page.getByRole("button", { name: "Submit issue" }).click();
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await expect(page.locator("main")).toHaveText(errors.invalidIaid);
});

test("invalid email", async ({ page }) => {
  await page.goto("/catalogue/report-an-issue/");

  await page.getByLabel("Email address").fill("invalid");
  await page.getByRole("button", { name: "Submit issue" }).click();
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await expect(page.locator("main")).toHaveText(errors.invalidEmail);
});

test("prefilled IAID", async ({ page }) => {
  await page.goto("/catalogue/report-an-issue/?iaid=C4");

  await expect(page.locator("main")).toHaveText(/Selected record/);
  await expect(page.locator("main")).toHaveText(/C4/);
  await expect(page.locator("main")).toHaveText(/Reference number/);
  await expect(page.locator("main")).toHaveText(/ADM/);
});

test("complete", async ({ page }) => {
  await page.goto("/catalogue/report-an-issue/");

  await page.getByLabel("Record IAID").fill("C1234");
  await page.getByLabel("What is the error?").fill("Something");
  await page.getByLabel("What is the correct information?").fill("Nothing");
  await page.getByRole("button", { name: "Submit issue" }).click();
  await expect(page).toHaveURL(/\/catalogue\/report-an-issue\/complete\//);
  await expect(page.locator("main")).toHaveText(/Issue submitted/);
  await expect(page.locator("main")).toHaveText(
    /Thank you for taking the time to help us improve the catalogue\. We may contact you within the next 10 days if we need further information\./,
  );
  await expect(page.locator("main")).toHaveText(
    /We will not be able to notify you if your suggestion is successful\. This is due to the high volume of suggestions we receive\./,
  );
  await validateHtml(page);
  await checkAccessibility(page);

  await page.getByRole("link", { name: "Submit another issue" }).click();
  await expect(page).toHaveURL(/\/catalogue\/report-an-issue\//);

  await page.goto("/catalogue/report-an-issue/complete/");
  await expect(page).toHaveURL(/\/catalogue\/report-an-issue\//);
});
