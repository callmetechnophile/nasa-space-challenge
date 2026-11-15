const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  const evidenceDir = path.resolve(__dirname, '../evidence/m6/screenshots');
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  fs.mkdirSync(evidenceDir, { recursive: true });

  console.log('Launching browser for M6 Challenge Completion validation screenshots...');
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();

  console.log('Navigating to http://localhost:3000 ...');
  await page.goto('http://localhost:3000', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(4000);

  // 1. Initial Time-Series Player View (WISE 0855 default)
  const p1 = path.join(evidenceDir, 'm6-01-time-series-player-wise0855.png');
  await page.screenshot({ path: p1, fullPage: false });
  console.log('Saved:', p1);

  // 2. Click Barnard's Star preset
  console.log('Clicking Barnard\'s Star preset...');
  const barnardBtn = page.getByRole('button', { name: /Barnard's Star/i }).last();
  if (await barnardBtn.isVisible()) {
    await barnardBtn.click();
    await page.waitForTimeout(2500);
    const p2 = path.join(evidenceDir, 'm6-02-barnards-star-target-view.png');
    await page.screenshot({ path: p2, fullPage: false });
    console.log('Saved:', p2);
  }

  // 3. Click Epsilon Indi B preset
  console.log('Clicking Epsilon Indi B preset...');
  const epsBtn = page.getByRole('button', { name: /Epsilon Indi B/i }).last();
  if (await epsBtn.isVisible()) {
    await epsBtn.click();
    await page.waitForTimeout(2500);
    const p3 = path.join(evidenceDir, 'm6-03-epsilon-indi-b-unresolved.png');
    await page.screenshot({ path: p3, fullPage: false });
    console.log('Saved:', p3);
  }

  // 4. Click R Draconis preset
  console.log('Clicking R Draconis preset...');
  const rDraBtn = page.getByRole('button', { name: /R Draconis/i }).last();
  if (await rDraBtn.isVisible()) {
    await rDraBtn.click();
    await page.waitForTimeout(2500);
    const p4 = path.join(evidenceDir, 'm6-04-r-draconis-variable-target.png');
    await page.screenshot({ path: p4, fullPage: false });
    console.log('Saved:', p4);
  }

  // 5. Switch to M5 Scientific Differencing Mode in bottom panel
  console.log('Switching to M5 Difference Imaging mode...');
  const m5DiffBtn = page.getByRole('button', { name: /M5 Difference Imaging/i });
  if (await m5DiffBtn.isVisible()) {
    await m5DiffBtn.click();
    await page.waitForTimeout(2000);
    const p5 = path.join(evidenceDir, 'm6-05-m5-scientific-difference-mode.png');
    await page.screenshot({ path: p5, fullPage: false });
    console.log('Saved:', p5);
  }

  // 6. Switch to NASA 5-Targets Top Navigation View
  console.log('Switching to Targets Tab...');
  const targetsTabBtn = page.getByRole('button', { name: /Target Calibration/i });
  if (await targetsTabBtn.isVisible()) {
    await targetsTabBtn.click();
    await page.waitForTimeout(2000);
    const p6 = path.join(evidenceDir, 'm6-06-nasa-5-targets-validation-tab.png');
    await page.screenshot({ path: p6, fullPage: false });
    console.log('Saved:', p6);
  }

  await browser.close();

  // Copy to Brain Artifacts directory
  const files = fs.readdirSync(evidenceDir);
  for (const f of files) {
    if (f.endsWith('.png')) {
      fs.copyFileSync(path.join(evidenceDir, f), path.join(artifactDir, f));
    }
  }
  console.log('All M6 screenshots copied to artifacts directory.');
}

main().catch((err) => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
