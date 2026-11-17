import { expect, test as base } from "@playwright/test";

export const test = base.extend<{ clearCookies: void }>({
  clearCookies: [
    async ({ context }, use) => {
      await context.clearCookies();
      await use();
    },
    { auto: true },
  ],
});

export { expect };
