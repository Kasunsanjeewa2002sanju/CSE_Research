import { test, expect } from '@playwright/test';

test.describe('Dashboard Smoke Tests', () => {
  test('loads home page and displays institutional header', async ({ page }) => {
    await page.goto('/');

    // Check header branding
    await expect(page.locator('h1')).toContainText('Colombo Stock Exchange (CSE) Research');

    // Check main navigation links exist
    const nav = page.locator('nav[aria-label="Main Navigation"]');
    await expect(nav).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Overview' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Data Explorer' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Political Events' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Event Study' })).toBeVisible();
    await expect(nav.getByRole('link', { name: 'Model Lab' })).toBeVisible();
  });

  test('navigates to data explorer page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Data Explorer' }).click();
    await expect(page).toHaveURL(/.*data-explorer/);
    await expect(page.locator('h2')).toContainText('ASPI Data Explorer');
  });

  test('navigates to political events page', async ({ page }) => {
    await page.goto('/');
    await page.getByRole('link', { name: 'Political Events' }).click();
    await expect(page).toHaveURL(/.*events/);
    await expect(page.locator('h2')).toContainText('Political Events Catalog');
  });
});
