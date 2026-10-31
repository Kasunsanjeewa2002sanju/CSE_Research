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

  const viewports = [
    { name: '360', width: 360, height: 800 },
    { name: '768', width: 768, height: 1024 },
    { name: '1280', width: 1280, height: 850 },
  ];

  // 1. Capture Shell on Overview Page
  for (const vp of viewports) {
    const page = await browser.newPage({
      viewport: { width: vp.width, height: vp.height },
    });
    console.log(`Capturing Shell at ${vp.name}px...`);
    await page.goto('http://localhost:3000/', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    const filename = `shell-${vp.name}.png`;
    const outPath = path.join(OUT_DIR, filename);
    const artifactPath = path.join(ARTIFACT_DIR, filename);

    await page.screenshot({ path: outPath, fullPage: false });
    fs.copyFileSync(outPath, artifactPath);
    console.log(`Saved: ${filename}`);
    await page.close();
  }

  // 2. Capture Design Preview Page (Components tab)
  for (const vp of viewports) {
    const page = await browser.newPage({
      viewport: { width: vp.width, height: vp.height },
    });
    console.log(`Capturing Design Preview (Components) at ${vp.name}px...`);
    await page.goto('http://localhost:3000/_design', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    const filename = `design-preview-${vp.name}.png`;
    const outPath = path.join(OUT_DIR, filename);
    const artifactPath = path.join(ARTIFACT_DIR, filename);

    await page.screenshot({ path: outPath, fullPage: false });
    fs.copyFileSync(outPath, artifactPath);
    console.log(`Saved: ${filename}`);
    await page.close();
  }

  // 3. Capture Design Preview Page (Charts tab) at 1280px
  {
    const page = await browser.newPage({
      viewport: { width: 1280, height: 950 },
    });
    console.log(`Capturing Design Preview (ECharts Token Foundation) at 1280px...`);
    await page.goto('http://localhost:3000/_design', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1000);

    // Click on the Charts tab
    const chartTab = page.locator('button[role="tab"]:has-text("ECharts Token Foundation")');
    if (await chartTab.isVisible()) {
      await chartTab.click();
      await page.waitForTimeout(1500);
    }

    const filename = `design-preview-charts-1280.png`;
    const outPath = path.join(OUT_DIR, filename);
    const artifactPath = path.join(ARTIFACT_DIR, filename);

    await page.screenshot({ path: outPath, fullPage: false });
    fs.copyFileSync(outPath, artifactPath);
    console.log(`Saved: ${filename}`);
    await page.close();
  }

  await browser.close();
  console.log('All Stage F1 screenshots captured successfully!');
}

capture().catch((err) => {
  console.error('Capture failed:', err);
  process.exit(1);
});
