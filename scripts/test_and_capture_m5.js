const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

  console.log('Launching browser for M5 Difference Imaging verification...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  console.log('Navigating to http://localhost:3000/workspace ...');
  await page.goto('http://localhost:3000/workspace', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // Switch to Temporal tab
  console.log('Switching to epoch_compare file tab...');
  const epochCompareTab = page.locator('button:has-text("epoch_compare")').first();
  if (await epochCompareTab.isVisible()) {
    await epochCompareTab.click();
    await page.waitForTimeout(1000);
  }

  // Switch to M5 Difference Imaging mode
  console.log('Clicking M5 Difference Imaging mode button...');
  const diffModeBtn = page.getByRole('button', { name: /M5 Difference Imaging/i });
  await diffModeBtn.waitFor({ state: 'visible', timeout: 10000 });
  await diffModeBtn.click();
  await page.waitForTimeout(1000);

  // Capture Initial State
  const initialShot = path.join(artifactDir, 'm5-real-spherex-initial-config.png');
  await page.screenshot({ path: initialShot, fullPage: false });
  console.log('Captured initial config:', initialShot);

  // Run Difference Pipeline
  console.log('Clicking "Run Scientific Differencing"...');
  const runBtn = page.getByRole('button', { name: /Run Scientific Differencing/i });
  await runBtn.click();

  // Wait for the results to appear on screen
  console.log('Waiting for results (Temporal Baseline)...');
  await page.waitForSelector('text=Temporal Baseline', { timeout: 30000 });
  await page.waitForTimeout(2000);

  const successShot = path.join(artifactDir, 'm5-real-spherex-difference-imaging-success.png');
  await page.screenshot({ path: successShot, fullPage: false });
  console.log('Captured successful difference imaging:', successShot);

  // Click Significance S layer
  console.log('Clicking "Significance S" button...');
  const sigBtn = page.getByRole('button', { name: 'Significance S' });
  if (await sigBtn.isVisible()) {
    await sigBtn.click();
    await page.waitForTimeout(1000);
    const sigShot = path.join(artifactDir, 'm5-significance-map-verified.png');
    await page.screenshot({ path: sigShot, fullPage: false });
    console.log('Captured significance map layer:', sigShot);
  }

  // Click Blink layer
  console.log('Clicking "Blink (1↔2)" button...');
  const blinkBtn = page.getByRole('button', { name: 'Blink (1↔2)' });
  if (await blinkBtn.isVisible()) {
    await blinkBtn.click();
    await page.waitForTimeout(1200);
    const blinkShot = path.join(artifactDir, 'm5-blink-comparator-verified.png');
    await page.screenshot({ path: blinkShot, fullPage: false });
    console.log('Captured blink comparator layer:', blinkShot);
  }

  // Intercept the /temporal/compare endpoint to return structured 404 error
  console.log('Enabling route mock to test Actionable Error card...');
  await page.route('**/temporal/compare', route => {
    route.fulfill({
      status: 404,
      contentType: 'application/json',
      body: JSON.stringify({
        detail: {
          message: 'Reference observation file not found or could not be retrieved from storage or archive: level2_missing_flight_frame.fits',
          filename: 'level2_missing_flight_frame.fits',
          stage: 'FILE_INGESTION',
          category: 'MISSING_INPUT_FILE',
        }
      })
    });
  });

  console.log('Triggering failed run to capture Actionable Error Card...');
  await runBtn.click();
  await page.waitForSelector('text=M5 Differencing Pipeline Error', { timeout: 10000 });
  await page.waitForTimeout(1000);

  const errorShot = path.join(artifactDir, 'm5-actionable-error-state.png');
  await page.screenshot({ path: errorShot, fullPage: false });
  console.log('Captured actionable error card:', errorShot);

  await browser.close();
  console.log('All tests and screenshots completed successfully!');
}

main().catch(err => {
  console.error('Screenshot test error:', err);
  process.exit(1);
});
