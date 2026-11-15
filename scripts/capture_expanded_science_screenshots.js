const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  const evidenceDir = path.resolve(__dirname, '../evidence/landing/screenshots');
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  fs.mkdirSync(evidenceDir, { recursive: true });

  console.log('Launching browser for Expanded Science Pages screenshot validation...');
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const savedFiles = [];

  // Desktop context (1440x900)
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  const pagesToCapture = [
    { url: 'http://localhost:3000/spherex', name: 'skytrace-science-01-spherex.png', desc: 'SPHEREx Mission Page' },
    { url: 'http://localhost:3000/spherex/instrument', name: 'skytrace-science-02-instrument.png', desc: 'Instrument Architecture' },
    { url: 'http://localhost:3000/spherex/spectral-bands', name: 'skytrace-science-03-spectral-bands.png', desc: '102 Spectral Bands' },
    { url: 'http://localhost:3000/planet-x', name: 'skytrace-science-04-planet-x.png', desc: 'Planet X Hypothesis' },
    { url: 'http://localhost:3000/planet-x/evidence', name: 'skytrace-science-05-planet-x-evidence.png', desc: 'Planet Nine Evidence' },
    { url: 'http://localhost:3000/science', name: 'skytrace-science-06-science-methodology.png', desc: 'Science & Methodology' },
  ];

  for (const item of pagesToCapture) {
    console.log(`Navigating to ${item.url} (${item.desc})...`);
    await page.goto(item.url, { waitUntil: 'domcontentloaded', timeout: 30000 });
    await page.waitForTimeout(2500);
    const destPath = path.join(evidenceDir, item.name);
    await page.screenshot({ path: destPath, fullPage: false });
    savedFiles.push(destPath);
    console.log(`Saved: ${destPath}`);
  }

  // Mobile Context (390x844 iPhone 14 style)
  console.log('Testing Mobile Viewport & Navigation Drawer...');
  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    isMobile: true,
  });
  const mobilePage = await mobileContext.newPage();
  await mobilePage.goto('http://localhost:3000/spherex', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await mobilePage.waitForTimeout(2000);

  // Click mobile hamburger menu
  const menuBtn = mobilePage.locator('button[aria-label="Toggle navigation menu"]');
  if (await menuBtn.count() > 0) {
    await menuBtn.click();
    await mobilePage.waitForTimeout(1000);
    const mobileDrawerPath = path.join(evidenceDir, 'skytrace-science-07-mobile-drawer.png');
    await mobilePage.screenshot({ path: mobileDrawerPath, fullPage: false });
    savedFiles.push(mobileDrawerPath);
    console.log(`Saved: ${mobileDrawerPath}`);
  }

  await browser.close();

  // Copy screenshots to artifact directory for rendering in Antigravity chat
  console.log(`Copying screenshots to artifact directory: ${artifactDir}`);
  for (const f of savedFiles) {
    const filename = path.basename(f);
    const target = path.join(artifactDir, filename);
    fs.copyFileSync(f, target);
    console.log(`Artifact copied: ${target}`);
  }

  console.log('All science page screenshots captured successfully.');
}

main().catch((err) => {
  console.error('Screenshot capture failed:', err);
  process.exit(1);
});
