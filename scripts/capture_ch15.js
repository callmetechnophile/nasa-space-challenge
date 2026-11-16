const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const browser = await chromium.launch({ headless: true, executablePath: fs.existsSync(edgePath) ? edgePath : undefined });
  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  await page.goto('http://localhost:3000/workspace?tab=spectral&ra=133.7951&dec=-7.2451');
  await page.waitForTimeout(3000);
  const btn15 = page.locator('button:text-is("15")').first();
  if (await btn15.isVisible()) {
    await btn15.click();
    await page.waitForTimeout(1500);
  }
  const shotPath = path.join(artifactDir, 'spectral-cube-measured-channel-15.png');
  await page.screenshot({ path: shotPath });
  console.log('Captured measured channel 15:', shotPath);
  await browser.close();
}

main().catch(console.error);
