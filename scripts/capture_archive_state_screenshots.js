const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

  console.log('Launching Edge for Archive Discovery validation screenshots...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();

  console.log('Navigating to http://localhost:3000/workspace ...');
  await page.goto('http://localhost:3000/workspace', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // Switch to Temporal tab
  console.log('Switching to epoch_compare file tab...');
  const epochCompareTab = page.locator('button:has-text("epoch_compare")').first();
  if (await epochCompareTab.isVisible()) {
    await epochCompareTab.click();
  }

  // Wait 12 seconds for initial discovery query across DR1 and QR3 to resolve
  console.log('Waiting 12 seconds for initial query to complete...');
  await page.waitForTimeout(12000);

  const shot1 = path.join(artifactDir, 'spherex-archive-query-failed-unverified.png');
  await page.screenshot({ path: shot1, fullPage: false });
  console.log('Captured:', shot1);

  await browser.close();
  console.log('Done.');
}

main().catch((err) => {
  console.error('Error during screenshot capture:', err);
  process.exit(1);
});
