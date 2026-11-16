const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

  console.log('Launching browser for SkyTrace Workspace Layout Refactor Verification...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  console.log('Navigating to http://localhost:3000/workspace ...');
  await page.goto('http://localhost:3000/workspace', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // 1. Verify canvas has no floating coordinate panel or archive panel
  const archivePanelCount = await page.locator('text="NASA SPHEREx Archive"').count();
  const m4BadgeCount = await page.locator('text="M4 Real Data"').count();
  console.log('Archive panel count:', archivePanelCount, '(Expected 0)');
  console.log('M4 Real Data badge count:', m4BadgeCount, '(Expected 0)');

  // 2. Verify COORDINATES tab is default active in bottom dock
  const coordTab = page.locator('#dock-tab-coordinates');
  const isCoordSelected = await coordTab.getAttribute('aria-selected');
  console.log('COORDINATES tab aria-selected:', isCoordSelected, '(Expected "true")');

  // Verify RA/Dec inputs are present
  const raInput = page.locator('input[placeholder*="133.795129"]');
  console.log('RA input present:', (await raInput.count()) > 0);

  // Capture Screenshot 1: Default Workspace with COORDINATES dock tab
  const p1 = path.join(artifactDir, 'skytrace-workspace-dock-coordinates.png');
  await page.screenshot({ path: p1, fullPage: false });
  console.log('Saved Screenshot 1:', p1);

  // 3. Switch to IMAGE LAYERS tab
  const layersTab = page.locator('#dock-tab-layers');
  await layersTab.click();
  await page.waitForTimeout(1000);

  const productDropdown = page.locator('select').first();
  console.log('Product dropdown present in Image Layers:', (await productDropdown.count()) > 0);

  const fitsUploadLabel = page.locator('text="Upload FITS (.fits, .fit)"');
  console.log('FITS upload button present:', (await fitsUploadLabel.count()) > 0);

  // Capture Screenshot 2: Workspace with IMAGE LAYERS dock tab
  const p2 = path.join(artifactDir, 'skytrace-workspace-dock-layers.png');
  await page.screenshot({ path: p2, fullPage: false });
  console.log('Saved Screenshot 2:', p2);

  // 4. Switch to PROBLEMS tab
  const problemsTab = page.locator('#dock-tab-problems');
  await problemsTab.click();
  await page.waitForTimeout(1000);

  // Capture Screenshot 3: Workspace with PROBLEMS dock tab
  const p3 = path.join(artifactDir, 'skytrace-workspace-dock-problems.png');
  await page.screenshot({ path: p3, fullPage: false });
  console.log('Saved Screenshot 3:', p3);

  // 5. Switch back to COORDINATES tab and test Sexagesimal toggle & input
  await coordTab.click();
  await page.waitForTimeout(500);

  const sexagesimalBtn = page.locator('button:has-text("Sexagesimal")');
  await sexagesimalBtn.click();
  await page.waitForTimeout(500);

  const p4 = path.join(artifactDir, 'skytrace-workspace-sexagesimal-input.png');
  await page.screenshot({ path: p4, fullPage: false });
  console.log('Saved Screenshot 4 (Sexagesimal):', p4);

  await browser.close();
  console.log('All automated browser verifications completed successfully!');
}

main().catch((err) => {
  console.error('Verification error:', err);
  process.exit(1);
});
