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

  // 1. Capture Desktop (1280px) tabs
  {
    const page = await browser.newPage({
      viewport: { width: 1280, height: 950 },
    });
    console.log('Navigating to http://localhost:3000/methodology at 1280px...');
    await page.goto('http://localhost:3000/methodology', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    // Tab 1: Protocol
    console.log('Capturing Protocol tab (1280px)...');
    let filename = 'methodology-protocol-1280.png';
    await page.screenshot({ path: path.join(OUT_DIR, filename) });
    fs.copyFileSync(path.join(OUT_DIR, filename), path.join(ARTIFACT_DIR, filename));
    console.log(`Saved: ${filename}`);

    // Tab 2: Pipeline
    console.log('Capturing Pipeline tab (1280px)...');
    const pipelineTab = page.locator('button[role="tab"]:has-text("Pipeline Flow")');
    if (await pipelineTab.isVisible()) {
      await pipelineTab.click();
      await page.waitForTimeout(1000);
      filename = 'methodology-pipeline-1280.png';
      await page.screenshot({ path: path.join(OUT_DIR, filename) });
      fs.copyFileSync(path.join(OUT_DIR, filename), path.join(ARTIFACT_DIR, filename));
      console.log(`Saved: ${filename}`);
    }

    // Tab 3: Feature Sets
    console.log('Capturing Feature Sets tab (1280px)...');
    const featuresTab = page.locator('button[role="tab"]:has-text("Feature Sets")');
    if (await featuresTab.isVisible()) {
      await featuresTab.click();
      await page.waitForTimeout(1000);
      filename = 'methodology-features-1280.png';
      await page.screenshot({ path: path.join(OUT_DIR, filename) });
      fs.copyFileSync(path.join(OUT_DIR, filename), path.join(ARTIFACT_DIR, filename));
      console.log(`Saved: ${filename}`);
    }

    // Tab 4: Leakage Tests
    console.log('Capturing Leakage Tests tab (1280px)...');
    const leakageTab = page.locator('button[role="tab"]:has-text("Leakage Board")');
    if (await leakageTab.isVisible()) {
      await leakageTab.click();
      await page.waitForTimeout(1000);
      filename = 'methodology-leakage-1280.png';
      await page.screenshot({ path: path.join(OUT_DIR, filename) });
      fs.copyFileSync(path.join(OUT_DIR, filename), path.join(ARTIFACT_DIR, filename));
      console.log(`Saved: ${filename}`);
    }

    // Tab 5: Baselines & Glossary
    console.log('Capturing Baselines & Glossary tab (1280px)...');
    const baselinesTab = page.locator('button[role="tab"]:has-text("Baselines & Glossary")');
    if (await baselinesTab.isVisible()) {
      await baselinesTab.click();
      await page.waitForTimeout(1000);
      filename = 'methodology-baselines-1280.png';
      await page.screenshot({ path: path.join(OUT_DIR, filename) });
      fs.copyFileSync(path.join(OUT_DIR, filename), path.join(ARTIFACT_DIR, filename));
      console.log(`Saved: ${filename}`);
    }

    await page.close();
  }

  // 2. Capture Tablet (768px)
  {
    const page = await browser.newPage({
      viewport: { width: 768, height: 1024 },
    });
    console.log('Capturing Tablet (768px)...');
    await page.goto('http://localhost:3000/methodology', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    const filename = 'methodology-768.png';
    await page.screenshot({ path: path.join(OUT_DIR, filename) });
    fs.copyFileSync(path.join(OUT_DIR, filename), path.join(ARTIFACT_DIR, filename));
    console.log(`Saved: ${filename}`);
    await page.close();
  }

  // 3. Capture Mobile (360px)
  {
    const page = await browser.newPage({
      viewport: { width: 360, height: 800 },
    });
    console.log('Capturing Mobile (360px)...');
    await page.goto('http://localhost:3000/methodology', { waitUntil: 'networkidle' });
    await page.waitForTimeout(1500);

    const filename = 'methodology-360.png';
    await page.screenshot({ path: path.join(OUT_DIR, filename) });
    fs.copyFileSync(path.join(OUT_DIR, filename), path.join(ARTIFACT_DIR, filename));
    console.log(`Saved: ${filename}`);
    await page.close();
  }

  await browser.close();
  console.log('All Stage F6 Methodology screenshots captured successfully!');
}

capture().catch((err) => {
  console.error('Error capturing screenshots:', err);
  process.exit(1);
});
