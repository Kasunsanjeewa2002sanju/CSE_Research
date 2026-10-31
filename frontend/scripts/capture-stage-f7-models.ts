import { chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const OUT_DIR = path.resolve(__dirname, '../docs/screenshots');
const ARTIFACT_DIR = path.resolve(
  'C:/Users/rpc/.gemini/antigravity-ide/brain/43284273-e808-45a4-a96a-704935be10d9/screenshots'
);

if (!fs.existsSync(OUT_DIR)) {
  fs.mkdirSync(OUT_DIR, { recursive: true });
}
if (!fs.existsSync(ARTIFACT_DIR)) {
  fs.mkdirSync(ARTIFACT_DIR, { recursive: true });
}

async function capture() {
  console.log('Launching browser (msedge channel)...');
  const browser = await chromium.launch({
    channel: 'msedge',
    headless: true,
  });

  // 1. Desktop (1280px) Views
  const desktopRoutes = [
    { url: 'http://localhost:3000/models', filename: 'models-leaderboard-1280.png' },
    { url: 'http://localhost:3000/models/catboost_reg_c_h5', filename: 'models-detail-1280.png' },
    { url: 'http://localhost:3000/models/compare', filename: 'models-compare-1280.png' },
    { url: 'http://localhost:3000/models/statistics', filename: 'models-statistics-1280.png' },
    { url: 'http://localhost:3000/models/final', filename: 'models-final-1280.png' },
  ];

  for (const item of desktopRoutes) {
    const page = await browser.newPage({
      viewport: { width: 1280, height: 950 },
    });
    console.log(`Navigating to ${item.url} at 1280px...`);
    try {
      await page.goto(item.url, { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(2000);
      console.log(`Capturing ${item.filename}...`);
      const outPath = path.join(OUT_DIR, item.filename);
      const artPath = path.join(ARTIFACT_DIR, item.filename);
      await page.screenshot({ path: outPath, fullPage: false });
      fs.copyFileSync(outPath, artPath);
      console.log(`Saved: ${item.filename}`);
    } catch (err) {
      console.error(`Error capturing ${item.filename}:`, err);
    } finally {
      await page.close();
    }
  }

  // 2. Tablet (768px) View
  {
    const page = await browser.newPage({
      viewport: { width: 768, height: 1024 },
    });
    console.log('Navigating to http://localhost:3000/models at 768px...');
    try {
      await page.goto('http://localhost:3000/models', { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(2000);
      const filename = 'models-768.png';
      const outPath = path.join(OUT_DIR, filename);
      const artPath = path.join(ARTIFACT_DIR, filename);
      await page.screenshot({ path: outPath, fullPage: false });
      fs.copyFileSync(outPath, artPath);
      console.log(`Saved: ${filename}`);
    } catch (err) {
      console.error('Error capturing tablet screenshot:', err);
    } finally {
      await page.close();
    }
  }

  // 3. Mobile (360px) View
  {
    const page = await browser.newPage({
      viewport: { width: 360, height: 800 },
    });
    console.log('Navigating to http://localhost:3000/models at 360px...');
    try {
      await page.goto('http://localhost:3000/models', { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(2000);
      const filename = 'models-360.png';
      const outPath = path.join(OUT_DIR, filename);
      const artPath = path.join(ARTIFACT_DIR, filename);
      await page.screenshot({ path: outPath, fullPage: false });
      fs.copyFileSync(outPath, artPath);
      console.log(`Saved: ${filename}`);
    } catch (err) {
      console.error('Error capturing mobile screenshot:', err);
    } finally {
      await page.close();
    }
  }

  await browser.close();
  console.log('All Stage F7 screenshots captured successfully!');
}

capture().catch((err) => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
