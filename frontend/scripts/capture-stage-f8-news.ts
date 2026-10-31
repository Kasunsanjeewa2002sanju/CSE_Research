import { chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const OUT_DIR = path.resolve(__dirname, '../screenshots');
const DOCS_OUT_DIR = path.resolve(__dirname, '../docs/screenshots');
const ARTIFACT_DIR = path.resolve(
  'C:/Users/rpc/.gemini/antigravity-ide/brain/7d601939-d1e8-49de-a37a-b2201bd62b6a'
);

[OUT_DIR, DOCS_OUT_DIR, ARTIFACT_DIR].forEach((dir) => {
  if (!fs.existsSync(dir)) {
    fs.mkdirSync(dir, { recursive: true });
  }
});

function copyToAll(srcPath: string, filename: string) {
  const docsPath = path.join(DOCS_OUT_DIR, filename);
  const artPath = path.join(ARTIFACT_DIR, filename);
  fs.copyFileSync(srcPath, docsPath);
  fs.copyFileSync(srcPath, artPath);
}

async function capture() {
  console.log('Launching browser (msedge channel)...');
  const browser = await chromium.launch({
    channel: 'msedge',
    headless: true,
  });

  // 1. Desktop (1280px) Views
  // 1.1 /news feed
  {
    const page = await browser.newPage({
      viewport: { width: 1280, height: 950 },
    });
    console.log('Navigating to http://localhost:3000/news at 1280px...');
    try {
      await page.goto('http://localhost:3000/news', { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(2500);
      const filename = 'news-feed-1280.png';
      const outPath = path.join(OUT_DIR, filename);
      await page.screenshot({ path: outPath, fullPage: false });
      copyToAll(outPath, filename);
      console.log(`Saved: ${filename}`);

      // 1.2 Open detail drawer by clicking on the first news card title
      console.log('Opening detail drawer...');
      const firstCard = page.locator('article h3').first();
      await firstCard.click();
      await page.waitForTimeout(1500);

      const drawerFilename = 'news-detail-drawer-1280.png';
      const drawerOutPath = path.join(OUT_DIR, drawerFilename);
      await page.screenshot({ path: drawerOutPath, fullPage: false });
      copyToAll(drawerOutPath, drawerFilename);
      console.log(`Saved: ${drawerFilename}`);
    } catch (err) {
      console.error('Error capturing news feed / drawer:', err);
    } finally {
      await page.close();
    }
  }

  // 1.3 /news/pipeline monitor
  {
    const page = await browser.newPage({
      viewport: { width: 1280, height: 1100 },
    });
    console.log('Navigating to http://localhost:3000/news/pipeline at 1280px...');
    try {
      await page.goto('http://localhost:3000/news/pipeline', { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(3000);
      const filename = 'news-pipeline-1280.png';
      const outPath = path.join(OUT_DIR, filename);
      await page.screenshot({ path: outPath, fullPage: false });
      copyToAll(outPath, filename);
      console.log(`Saved: ${filename}`);

      // Also capture full page view
      const fullFilename = 'news-pipeline-full-1280.png';
      const fullOutPath = path.join(OUT_DIR, fullFilename);
      await page.screenshot({ path: fullOutPath, fullPage: true });
      copyToAll(fullOutPath, fullFilename);
      console.log(`Saved: ${fullFilename}`);

      // Also scroll to charts and failures section
      await page.evaluate(() => window.scrollBy(0, 950));
      await page.waitForTimeout(1000);
      const chartsFilename = 'news-pipeline-charts-1280.png';
      const chartsOutPath = path.join(OUT_DIR, chartsFilename);
      await page.screenshot({ path: chartsOutPath, fullPage: false });
      copyToAll(chartsOutPath, chartsFilename);
      console.log(`Saved: ${chartsFilename}`);
    } catch (err) {
      console.error('Error capturing news pipeline monitor:', err);
    } finally {
      await page.close();
    }
  }

  // 2. Tablet (768px) Views
  {
    const page = await browser.newPage({
      viewport: { width: 768, height: 1024 },
    });
    console.log('Navigating to http://localhost:3000/news at 768px...');
    try {
      await page.goto('http://localhost:3000/news', { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(2000);
      const filename = 'news-feed-768.png';
      const outPath = path.join(OUT_DIR, filename);
      await page.screenshot({ path: outPath, fullPage: false });
      copyToAll(outPath, filename);
      console.log(`Saved: ${filename}`);
    } catch (err) {
      console.error('Error capturing tablet news feed:', err);
    } finally {
      await page.close();
    }
  }

  // 3. Mobile (360px) Views
  {
    const page = await browser.newPage({
      viewport: { width: 360, height: 800 },
    });
    console.log('Navigating to http://localhost:3000/news at 360px...');
    try {
      await page.goto('http://localhost:3000/news', { waitUntil: 'networkidle', timeout: 30000 });
      await page.waitForTimeout(2000);
      const filename = 'news-feed-360.png';
      const outPath = path.join(OUT_DIR, filename);
      await page.screenshot({ path: outPath, fullPage: false });
      copyToAll(outPath, filename);
      console.log(`Saved: ${filename}`);
    } catch (err) {
      console.error('Error capturing mobile news feed:', err);
    } finally {
      await page.close();
    }
  }

  await browser.close();
  console.log('All Stage F8 screenshots captured successfully!');
}

capture().catch((err) => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
