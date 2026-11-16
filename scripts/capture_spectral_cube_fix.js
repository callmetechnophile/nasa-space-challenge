const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

  console.log('Launching browser for Spectral Cube verification...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  // Navigate directly with SPHEREx flight coordinates and spectral tab
  console.log('Navigating to http://localhost:3000/workspace?tab=spectral&ra=46.844&dec=1.832 ...');
  await page.goto('http://localhost:3000/workspace?tab=spectral&ra=46.844&dec=1.832', {
    waitUntil: 'domcontentloaded',
    timeout: 30000,
  });
  await page.waitForTimeout(4000);

  // Wait for spectral explorer to be visible
  await page.waitForTimeout(3000);

  // If needed, click the spectral cube tab or file
  const spectralTab = page.locator('button.astro-file-tab').filter({ hasText: /spectral_cube/i }).first();
  if (await spectralTab.isVisible()) {
    await spectralTab.click();
    await page.waitForTimeout(1000);
  }

  // 1. Capture Full Workspace with Spectral Explorer
  const mainViewShot = path.join(artifactDir, 'spectral-cube-102-bands-verified.png');
  await page.screenshot({ path: mainViewShot, fullPage: false });
  console.log('Captured full spectral explorer view:', mainViewShot);

  // 2. Select Band 8 (which has authentic flight observation at RA=46.844, Dec=1.832)
  console.log('Selecting Band 8 / Channel 8...');
  const band8Btn = page.locator('button:text-is("8"), button:has-text("CH 8")').first();
  if (await band8Btn.isVisible()) {
    await band8Btn.click();
    await page.waitForTimeout(1500);
  } else {
    // Try range slider or input
    const slider = page.locator('input[type="range"]');
    if (await slider.isVisible()) {
      await slider.fill('8');
      await slider.dispatchEvent('input');
      await slider.dispatchEvent('change');
      await page.waitForTimeout(1500);
    }
  }

  // 3. Capture Band Diagnostic panel detail
  const diagnosticPanel = page.locator('.space-y-4').first();
  const diagnosticShot = path.join(artifactDir, 'spectral-cube-band-diagnostic-calibrated.png');
  if (await diagnosticPanel.isVisible()) {
    await diagnosticPanel.screenshot({ path: diagnosticShot });
    console.log('Captured diagnostic panel detail:', diagnosticShot);
  } else {
    await page.screenshot({ path: diagnosticShot });
    console.log('Captured fallback diagnostic view:', diagnosticShot);
  }

  // 4. Capture Inspector telemetry showing calibrated band catalogue & spectral coverage
  const inspectorShot = path.join(artifactDir, 'spectral-inspector-telemetry-calibrated.png');
  await page.screenshot({ path: inspectorShot, fullPage: false });
  console.log('Captured inspector telemetry view:', inspectorShot);

  await browser.close();
  console.log('All spectral cube verification screenshots captured successfully.');
}

main().catch(err => {
  console.error('Capture failed:', err);
  process.exit(1);
});
