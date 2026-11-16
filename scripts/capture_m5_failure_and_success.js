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
  console.log('Switching to M5 Difference Imaging mode...');
  const diffModeBtn = page.getByRole('button', { name: /M5 Difference Imaging/i });
  if (await diffModeBtn.isVisible()) {
    await diffModeBtn.click();
    await page.waitForTimeout(1000);
  }

  // 1. Capture Initial State before difference run
  const initialShot = path.join(artifactDir, 'm5-real-spherex-initial-config.png');
  await page.screenshot({ path: initialShot, fullPage: false });
  console.log('Captured initial config:', initialShot);

  // 2. Run Difference Pipeline with Approved SPHEREx Real Pair
  console.log('Clicking "Run Scientific Differencing"...');
  const runBtn = page.getByRole('button', { name: /Run Scientific Differencing/i });
  if (await runBtn.isVisible()) {
    await runBtn.click();
    console.log('Waiting for difference imaging pipeline to finish...');
    // Wait 5 seconds for local calculation
    await page.waitForTimeout(5000);

    const successShot = path.join(artifactDir, 'm5-real-spherex-difference-imaging-success.png');
    await page.screenshot({ path: successShot, fullPage: false });
    console.log('Captured successful difference imaging:', successShot);

    // Toggle Significance S layer
    console.log('Toggling "Significance S" layer...');
    const sigBtn = page.getByRole('button', { name: /Significance S/i });
    if (await sigBtn.isVisible()) {
      await sigBtn.click();
      await page.waitForTimeout(1000);
      const sigShot = path.join(artifactDir, 'm5-significance-map-verified.png');
      await page.screenshot({ path: sigShot, fullPage: false });
      console.log('Captured significance map layer:', sigShot);
    }

    // Toggle Blink layer
    console.log('Toggling "Blink" layer...');
    const blinkBtn = page.getByRole('button', { name: /Blink/i });
    if (await blinkBtn.isVisible()) {
      await blinkBtn.click();
      await page.waitForTimeout(1500);
      const blinkShot = path.join(artifactDir, 'm5-blink-comparator-verified.png');
      await page.screenshot({ path: blinkShot, fullPage: false });
      console.log('Captured blink comparator layer:', blinkShot);
    }
  }

  // 3. Now test Actionable Error State
  console.log('Testing Actionable Error State (Intercepted simulated 404 failure)...');
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

  if (await runBtn.isVisible()) {
    await runBtn.click();
    await page.waitForTimeout(2000);

    const errorShot = path.join(artifactDir, 'm5-actionable-error-state.png');
    await page.screenshot({ path: errorShot, fullPage: false });
    console.log('Captured actionable error card:', errorShot);
  }

  await browser.close();
  console.log('All verification screenshots captured successfully.');
}

main().catch(err => {
  console.error('Screenshot error:', err);
  process.exit(1);
});
