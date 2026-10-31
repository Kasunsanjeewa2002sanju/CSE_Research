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

async function captureContract() {
  console.log('Launching browser to capture /_contract...');
  const browser = await chromium.launch({
    channel: 'msedge',
    headless: true,
  });

  const page = await browser.newPage({
    viewport: { width: 1280, height: 950 },
  });

  await page.goto('http://localhost:3000/_contract', { waitUntil: 'networkidle' });
  await page.waitForTimeout(1500);

  const filename = 'contract-catalog-1280.png';
  const outPath = path.join(OUT_DIR, filename);
  const artifactPath = path.join(ARTIFACT_DIR, filename);

  await page.screenshot({ path: outPath, fullPage: false });
  fs.copyFileSync(outPath, artifactPath);
  console.log(`Saved: ${filename}`);

  await page.close();
  await browser.close();
}

captureContract().catch((err) => {
  console.error('Failed capturing /_contract:', err);
  process.exit(1);
});
