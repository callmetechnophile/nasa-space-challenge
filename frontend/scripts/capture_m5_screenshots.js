const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../node_modules/playwright'));

async function main() {
  const evidenceDir = path.resolve(__dirname, '../../evidence/m5/screenshots');
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  fs.mkdirSync(evidenceDir, { recursive: true });

  console.log('Launching browser for M5 scientific validation screenshots...');
  const browser = await chromium.launch({
    executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
    headless: true,
  });
  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();

  console.log('Navigating to http://localhost:3000 ...');
  await page.goto('http://localhost:3000', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // 1. Initial Temporal Panel View
  const p1 = path.join(evidenceDir, 'm5-01-temporal-panel-initial.png');
  await page.screenshot({ path: p1, fullPage: false });
  console.log('Saved:', p1);

  // 2. Click "Run Scientific Differencing" button
  console.log('Clicking "Run Scientific Differencing"...');
  const runBtn = page.getByRole('button', { name: /Run Scientific Differencing/i });
  if (await runBtn.isVisible()) {
    await runBtn.click();
    console.log('Waiting for difference results...');
    await page.waitForTimeout(4000);

    const p2 = path.join(evidenceDir, 'm5-02-difference-imaging-results.png');
    await page.screenshot({ path: p2, fullPage: false });
    console.log('Saved:', p2);

    // 3. Toggle Significance S layer
    console.log('Toggling "Significance S" layer...');
    const sigBtn = page.getByRole('button', { name: /Significance S/i });
    if (await sigBtn.isVisible()) {
      await sigBtn.click();
      await page.waitForTimeout(1000);
      const p3 = path.join(evidenceDir, 'm5-03-significance-heatmap-layer.png');
      await page.screenshot({ path: p3, fullPage: false });
      console.log('Saved:', p3);
    }

    // 4. Toggle Blink mode
    console.log('Toggling "Blink" layer...');
    const blinkBtn = page.getByRole('button', { name: /Blink/i });
    if (await blinkBtn.isVisible()) {
      await blinkBtn.click();
      await page.waitForTimeout(1200);
      const p4 = path.join(evidenceDir, 'm5-04-blink-comparator-mode.png');
      await page.screenshot({ path: p4, fullPage: false });
      console.log('Saved:', p4);
    }
  } else {
    console.warn('Run button not visible!');
  }

  await browser.close();
  console.log('Screenshots completed successfully.');

  // Copy to artifact directory
  const files = fs.readdirSync(evidenceDir);
  for (const f of files) {
    if (f.endsWith('.png')) {
      const src = path.join(evidenceDir, f);
      const dst = path.join(artifactDir, f);
      fs.copyFileSync(src, dst);
      console.log(`Copied to artifact dir: ${dst}`);
    }
  }
}

main().catch(err => {
  console.error('Screenshot error:', err);
  process.exit(1);
});
