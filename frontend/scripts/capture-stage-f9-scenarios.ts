import { chromium } from '@playwright/test';
import path from 'path';
import fs from 'fs';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const OUT_DIR = path.resolve(__dirname, '../screenshots');
const DOCS_OUT_DIR = path.resolve(__dirname, '../docs/screenshots');
const ARTIFACT_DIR = path.resolve(
  'C:/Users/rpc/.gemini/antigravity-ide/brain/4f11b22c-a317-43b8-8564-d91330e5992e'
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

  const page = await browser.newPage({
    viewport: { width: 1280, height: 950 },
  });

  // 1. Initial Empty State with Presets and Latest ASPI Used
  {
    console.log('1. Capturing Initial Empty State (/predictor)...');
    await page.goto('http://localhost:3000/predictor', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(2000);
    const filename = 'scenario-empty-1280.png';
    const outPath = path.join(OUT_DIR, filename);
    await page.screenshot({ path: outPath, fullPage: false });
    copyToAll(outPath, filename);
    console.log(`Saved: ${filename}`);
  }

  // 2. Loading State with 3-Phase Stepper
  {
    console.log('2. Capturing Stepper Loading State...');
    // Intercept POST /api/v1/scenario to introduce a 4s delay so stepper is visible
    await page.route('**/api/v1/scenario', async (route) => {
      await new Promise((resolve) => setTimeout(resolve, 3500));
      try {
        await route.continue();
      } catch {
        // safe ignore if page navigated or cancelled
      }
    });

    const headlineInput = page.locator('#scenario-headline');
    await headlineInput.fill('Central Bank of Sri Lanka Cuts Policy Rates by 50bps');
    const submitBtn = page.getByRole('button', { name: /Simulate Counterfactual Scenarios/i });
    await submitBtn.click();
    await page.waitForTimeout(1000);

    const filename = 'scenario-loading-1280.png';
    const outPath = path.join(OUT_DIR, filename);
    await page.screenshot({ path: outPath, fullPage: false });
    copyToAll(outPath, filename);
    console.log(`Saved: ${filename}`);

    // Wait for the delayed response to complete before unrouting
    try {
      await page.waitForResponse((res) => res.url().includes('/api/v1/scenario'), { timeout: 10000 });
    } catch {
      // ignore timeout
    }
    await page.unroute('**/api/v1/scenario');
    await page.waitForTimeout(1000);
  }

  // 3. Active Result State (Summary Band, Three Panels, Fan Chart, Matrix, Evidence, Back-tests)
  {
    console.log('3. Capturing Result State...');
    // Reload and run clean simulation
    await page.goto('http://localhost:3000/predictor', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1500);

    // Click the first preset: "Presidential Election Declaration"
    const firstPreset = page.locator('.group.cursor-pointer').first();
    await firstPreset.click();

    // Wait for result panels to render
    await page.waitForSelector('text=Current Baseline', { timeout: 15000 });
    await page.waitForTimeout(2500);

    const filename = 'scenario-result-1280.png';
    const outPath = path.join(OUT_DIR, filename);
    await page.screenshot({ path: outPath, fullPage: false });
    copyToAll(outPath, filename);
    console.log(`Saved: ${filename}`);
  }

  // 4. Irrelevant News State ("No Material Impact Detected")
  {
    console.log('4. Capturing Irrelevant News State...');
    await page.goto('http://localhost:3000/predictor', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1500);

    // Intercept to ensure is_material_impact is false
    await page.route('**/api/v1/scenario', async (route) => {
      const response = await route.fetch();
      const json = await response.json();
      json.is_material_impact = false;
      json.material_impact_summary =
        'No material impact detected: TRUE and FALSE outcomes project essentially identical market trajectories.';
      await route.fulfill({ json });
    });

    // Fill an irrelevant headline and simulate
    const headlineInput = page.locator('#scenario-headline');
    await headlineInput.fill('Local district badminton tournament finals conclude in Gampaha');
    const submitBtn = page.getByRole('button', { name: /Simulate Counterfactual Scenarios/i });
    await submitBtn.click();

    await page.waitForSelector('text=No Material Impact Detected', { timeout: 15000 });
    await page.waitForTimeout(1500);

    const filename = 'scenario-irrelevant-1280.png';
    const outPath = path.join(OUT_DIR, filename);
    await page.screenshot({ path: outPath, fullPage: false });
    copyToAll(outPath, filename);
    console.log(`Saved: ${filename}`);

    await page.unroute('**/api/v1/scenario');
  }

  // 5. Stale Data Warning State
  {
    console.log('5. Capturing Stale Data Warning State...');
    await page.goto('http://localhost:3000/predictor', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1500);

    // Intercept to return stale flag and warning
    await page.route('**/api/v1/scenario', async (route) => {
      const response = await route.fetch();
      const json = await response.json();
      json.is_stale = true;
      json.stale_warning =
        'Market reference baseline is older than 24 business hours (latest close 2025-12-31). Projections are anchored to latest available close.';
      await route.fulfill({ json });
    });

    const headlineInput = page.locator('#scenario-headline');
    await headlineInput.fill('Government introduces supplementary appropriation bill in Parliament');
    const submitBtn = page.getByRole('button', { name: /Simulate Counterfactual Scenarios/i });
    await submitBtn.click();

    await page.waitForSelector('text=Market Baseline Warning', { timeout: 15000 });
    await page.waitForTimeout(1500);

    const filename = 'scenario-stale-1280.png';
    const outPath = path.join(OUT_DIR, filename);
    await page.screenshot({ path: outPath, fullPage: false });
    copyToAll(outPath, filename);
    console.log(`Saved: ${filename}`);

    await page.unroute('**/api/v1/scenario');
  }

  // 6. Contract Error State
  {
    console.log('6. Capturing Error State...');
    await page.goto('http://localhost:3000/predictor', { waitUntil: 'networkidle', timeout: 30000 });
    await page.waitForTimeout(1500);

    // Intercept to return a 500 error
    await page.route('**/api/v1/scenario', async (route) => {
      await route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          detail: 'Econometric inference service timeout: Conformal distribution matrix failed to converge.',
        }),
      });
    });

    const headlineInput = page.locator('#scenario-headline');
    await headlineInput.fill('Test Scenario triggering contract error boundary');
    const submitBtn = page.getByRole('button', { name: /Simulate Counterfactual Scenarios/i });
    await submitBtn.click();

    await page.waitForSelector('[role="alert"]', { timeout: 10000 });
    await page.waitForTimeout(1500);

    const filename = 'scenario-error-1280.png';
    const outPath = path.join(OUT_DIR, filename);
    await page.screenshot({ path: outPath, fullPage: false });
    copyToAll(outPath, filename);
    console.log(`Saved: ${filename}`);

    await page.unroute('**/api/v1/scenario');
  }

  await browser.close();
  console.log('All Stage F9 screenshots captured successfully.');
}

capture().catch((err) => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
