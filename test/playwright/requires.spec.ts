import { test, expect } from "@playwright/test";

test("single require", async ({ page }) => {
  await page.goto("/test/requires/alpha/");
  await expect(page).toHaveURL("/test/requires/");

  await page.getByRole("radio", { name: "Alpha" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/requires/alpha/");

  await page.goto("/test/requires/alpha/");
  await expect(page).toHaveURL("/test/requires/alpha/");
});

test("multiple requires", async ({ page }) => {
  await page.goto("/test/requires/beta/");
  await expect(page).toHaveURL("/test/requires/");

  await page.getByRole("radio", { name: "Alpha" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/requires/alpha/");

  await page.goto("/test/requires/beta/");
  await expect(page).toHaveURL("/test/requires/alpha/");
  await page.getByRole("radio", { name: "Alpha" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/requires/beta/");
});

test("requiresAny", async ({ page }) => {
  await page.goto("/test/requires-any/alpha/");
  await expect(page).toHaveURL("/test/requires-any/");

  await page.getByRole("radio", { name: "Alpha" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/requires-any/alpha/");

  await page.goto("/test/requires-any/alpha/");
  await expect(page).toHaveURL("/test/requires-any/alpha/");
});

test("requiresAny with multiple", async ({ page }) => {
  await page.goto("/test/requires-any/beta/");
  await expect(page).toHaveURL("/test/requires-any/");

  await page.getByRole("radio", { name: "Alpha" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/requires-any/alpha/");

  await page.goto("/test/requires-any/beta/");
  await expect(page).toHaveURL("/test/requires-any/beta/");
});

test("requiresAny with redirectIfNotComplete", async ({ page }) => {
  await page.goto("/test/requires-any/gamma/");
  await expect(page).toHaveURL("/test/requires-any/");

  await page.getByRole("radio", { name: "Alpha" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/requires-any/alpha/");

  await page.goto("/test/requires-any/gamma/");
  await expect(page).toHaveURL("/test/requires-any/gamma/");
});

test("nested requiresAny", async ({ page }) => {
  await page.goto("/test/requires-any/final/");
  await expect(page).toHaveURL("/test/requires-any/");

  await page.getByRole("radio", { name: "Alpha" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/requires-any/alpha/");

  await page.goto("/test/requires-any/final/");
  await expect(page).toHaveURL("/test/requires-any/beta/");

  await page.getByRole("radio", { name: "Alpha" }).check();
  await page.getByRole("button", { name: "Continue" }).click();
  await expect(page).toHaveURL("/test/requires-any/final/");

  await page.goto("/test/requires-any/final/");
  await expect(page).toHaveURL("/test/requires-any/final/");
});

// requireResponse
