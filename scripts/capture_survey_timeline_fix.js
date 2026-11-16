const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

  console.log('Launching browser for Survey Timeline verification...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();

  page.on('console', msg => console.log('PAGE LOG:', msg.text()));
  page.on('pageerror', err => console.log('PAGE ERROR:', err.message));

  console.log('Navigating to http://localhost:3000/workspace?tab=temporal ...');
  await page.goto('http://localhost:3000/workspace?tab=temporal', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(4000);

  // Switch to Survey Timeline tab if not already active
  console.log('Switching to Survey Timeline mode...');
  const timelineModeBtn = page.getByRole('button', { name: /Survey Timeline/i });
  if (await timelineModeBtn.isVisible()) {
    await timelineModeBtn.click();
    await page.waitForTimeout(2000);
  }

  // 1. Capture Real Flight Observation & Calibrated Cutout View
  const timelineShot = path.join(artifactDir, 'timeline-real-flight-observation.png');
  await page.screenshot({ path: timelineShot, fullPage: false });
  console.log('Captured timeline real flight view:', timelineShot);

  // 2. Click "Project on Sky (3D)" to project authentic FITS onto Three.js sphere
  console.log('Projecting layer onto Three.js sphere...');
  const projectBtn = page.getByRole('button', { name: /Project on Sky \(3D\)/i });
  if (await projectBtn.isVisible()) {
    await projectBtn.click();
    await page.waitForTimeout(3000);
  }

  // 3. Capture Inspector telemetry showing Image layers: 1, Band Catalogue: CALIBRATED, Authentic Flight Data
  const inspectorShot = path.join(artifactDir, 'timeline-inspector-telemetry-calibrated.png');
  await page.screenshot({ path: inspectorShot, fullPage: false });
  console.log('Captured inspector telemetry with 3D layer:', inspectorShot);

  // 4. Capture zoomed cutout element
  const cutoutContainer = page.locator('.relative.w-36.h-36');
  if (await cutoutContainer.isVisible()) {
    const cutoutShot = path.join(artifactDir, 'timeline-calibrated-infrared-cutout.png');
    await cutoutContainer.screenshot({ path: cutoutShot });
    console.log('Captured cutout detail:', cutoutShot);
  }

  await browser.close();
  console.log('All survey timeline verification screenshots captured successfully.');
}

main().catch(err => {
  console.error('Capture failed:', err);
  process.exit(1);
});
