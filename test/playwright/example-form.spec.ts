import { test, expect, Page } from "@playwright/test";
import acceptAllCookies from "./lib/accept-all-cookies.ts";
import validateHtml from "./lib/validate-html.ts";
import checkAccessibility from "./lib/check-accessibility.ts";

acceptAllCookies();

const checkPageRedirections: (
  page: Page,
  redirectChecks: Array<Array<string>>,
) => void = async (page, redirectChecks) => {
  for (const check of redirectChecks) {
    await expectPageRedirection(page, check[0], check[1]);
  }
};

const expectPageRedirection: (
  page: Page,
  url: string,
  expectRedirectedURL?: string,
) => void = async (page, url, expectRedirectedURL) => {
  await page.goto(url);
  if (expectRedirectedURL) {
    await expect(page).toHaveURL(expectRedirectedURL);
  } else {
    await expect(page).toHaveURL(url);
  }
};

test("landing page", async ({ page }) => {
  await page.goto("/example-form/");
  await expect(page).toHaveURL("/example-form/pizza-or-chocolate/");
  await expect(page.locator("h1")).toHaveText(
    /Do you prefer pizza or chocolate?/,
  );
  await validateHtml(page);
  await checkAccessibility(page);
});

test("page redirects - pizza path", async ({ page }) => {
  await page.goto("/example-form/pizza-or-chocolate/");
  await checkPageRedirections(page, [
    ["/example-form/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/pizza-or-chocolate/"],
    ["/example-form/neither/"],
    ["/example-form/pizza-topping/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/pizza-brand/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/address/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/type-of-chocolate/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/final-page/", "/example-form/pizza-or-chocolate/"],
  ]);

  await page.goto("/example-form/pizza-or-chocolate/");
  await expect(page.locator("main")).not.toHaveText(/There is a problem/);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/pizza-or-chocolate/");
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await page.getByLabel("Pizza").check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/pizza-topping/");
  await checkPageRedirections(page, [
    ["/example-form/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/pizza-or-chocolate/"],
    ["/example-form/neither/"],
    ["/example-form/pizza-topping/"],
    ["/example-form/pizza-brand/", "/example-form/pizza-topping/"],
    ["/example-form/address/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/type-of-chocolate/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/final-page/", "/example-form/pizza-or-chocolate/"],
  ]);

  await page.goto("/example-form/pizza-topping/");
  await expect(page.locator("main")).not.toHaveText(/There is a problem/);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/pizza-topping/");
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await page.getByLabel("Plain cheese").check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/pizza-brand/");
  await checkPageRedirections(page, [
    ["/example-form/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/pizza-or-chocolate/"],
    ["/example-form/neither/"],
    ["/example-form/pizza-topping/"],
    ["/example-form/pizza-brand/"],
    ["/example-form/address/"],
    ["/example-form/type-of-chocolate/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/final-page/", "/example-form/address/"],
  ]);

  await page.goto("/example-form/address/");
  await expect(page.locator("main")).not.toHaveText(/There is a problem/);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/address/");
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await page.getByLabel("Address line 1").fill("123 Main St");
  await page.getByLabel("Town or city").fill("Testville");
  await page.getByLabel("Postcode").fill("SW1A 1AA");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/final-page/");
  await checkPageRedirections(page, [
    ["/example-form/", "/example-form/final-page/"],
    ["/example-form/pizza-or-chocolate/", "/example-form/final-page/"],
    ["/example-form/neither/", "/example-form/final-page/"],
    ["/example-form/pizza-topping/", "/example-form/final-page/"],
    ["/example-form/pizza-brand/", "/example-form/final-page/"],
    ["/example-form/address/", "/example-form/final-page/"],
    ["/example-form/type-of-chocolate/", "/example-form/final-page/"],
    ["/example-form/final-page/"],
  ]);
});

test("page redirects - chocolate path", async ({ page }) => {
  await page.goto("/example-form/pizza-or-chocolate/");
  await expect(page.locator("main")).not.toHaveText(/There is a problem/);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/pizza-or-chocolate/");
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await page.getByLabel("Chocolate").check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/type-of-chocolate/");
  await checkPageRedirections(page, [
    ["/example-form/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/pizza-or-chocolate/"],
    ["/example-form/neither/"],
    ["/example-form/pizza-topping/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/pizza-brand/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/address/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/type-of-chocolate/"],
    ["/example-form/final-page/", "/example-form/pizza-or-chocolate/"],
  ]);

  await page.goto("/example-form/type-of-chocolate/");
  await expect(page.locator("main")).not.toHaveText(/There is a problem/);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/type-of-chocolate/");
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await page.getByLabel("White chocolate").check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/address/");
  await checkPageRedirections(page, [
    ["/example-form/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/pizza-or-chocolate/"],
    ["/example-form/neither/"],
    ["/example-form/pizza-topping/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/pizza-brand/", "/example-form/pizza-or-chocolate/"],
    ["/example-form/address/"],
    ["/example-form/type-of-chocolate/"],
    ["/example-form/final-page/", "/example-form/address/"],
  ]);

  await page.goto("/example-form/address/");
  await expect(page.locator("main")).not.toHaveText(/There is a problem/);
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/address/");
  await expect(page.locator("main")).toHaveText(/There is a problem/);
  await page.getByLabel("Address line 1").fill("123 Main St");
  await page.getByLabel("Town or city").fill("Testville");
  await page.getByLabel("Postcode").fill("SW1A 1AA");
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/example-form/final-page/");
  await checkPageRedirections(page, [
    ["/example-form/", "/example-form/final-page/"],
    ["/example-form/pizza-or-chocolate/", "/example-form/final-page/"],
    ["/example-form/neither/", "/example-form/final-page/"],
    ["/example-form/pizza-topping/", "/example-form/final-page/"],
    ["/example-form/pizza-brand/", "/example-form/final-page/"],
    ["/example-form/address/", "/example-form/final-page/"],
    ["/example-form/type-of-chocolate/", "/example-form/final-page/"],
    ["/example-form/final-page/"],
  ]);
});
