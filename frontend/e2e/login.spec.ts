import { test, expect } from "@playwright/test";

test.describe("Login page", () => {
  test("renders branded sign-in form", async ({ page }) => {
    await page.goto("/login");

    await expect(page.getByRole("heading", { name: "Attendance AI" })).toBeVisible();
    await expect(page.getByLabel("Email")).toBeVisible();
    await expect(page.getByLabel("Password")).toBeVisible();
    await expect(page.getByRole("button", { name: "Sign in" })).toBeVisible();
    await expect(page.getByText("admin@example.com")).toBeVisible();
  });

  test("keeps user on login when credentials are rejected", async ({ page }) => {
    await page.goto("/login");

    await page.getByLabel("Email").fill("nobody@example.com");
    await page.getByLabel("Password").fill("wrong-password");
    await page.getByRole("button", { name: "Sign in" }).click();

    // Without a live API this still stays on /login; with API it shows an error toast.
    await expect(page).toHaveURL(/\/login/);
    await expect(page.getByRole("heading", { name: "Attendance AI" })).toBeVisible();
  });
});
