const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  const evidenceDir = path.resolve(__dirname, '../evidence/landing/screenshots');
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  fs.mkdirSync(evidenceDir, { recursive: true });

  console.log('Launching browser for SkyTrace Landing & Workspace validation...');
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const savedFiles = [];

  // Desktop context
  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  console.log('Navigating to http://localhost:3000 ...');
  await page.goto('http://localhost:3000', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // 1. Hero
  const p1 = path.join(evidenceDir, 'skytrace-01-hero.png');
  await page.screenshot({ path: p1, fullPage: false });
  savedFiles.push(p1);
  console.log('Saved:', p1);

  // 2. Multi-Spectral (Act II)
  const act2 = page.locator('#invisible-universe');
  if (await act2.count() > 0) {
    await act2.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    const p2 = path.join(evidenceDir, 'skytrace-02-multispectral.png');
    await page.screenshot({ path: p2, fullPage: false });
    savedFiles.push(p2);
    console.log('Saved:', p2);
  }

  // 3. Temporal (Act III)
  const act3 = page.locator('#temporal');
  if (await act3.count() > 0) {
    await act3.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    const p3 = path.join(evidenceDir, 'skytrace-03-temporal.png');
    await page.screenshot({ path: p3, fullPage: false });
    savedFiles.push(p3);
    console.log('Saved:', p3);
  }

  // 4. Spectral (Act IV)
  const act4 = page.locator('#spectral');
  if (await act4.count() > 0) {
    await act4.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    const p4 = path.join(evidenceDir, 'skytrace-04-spectral.png');
    await page.screenshot({ path: p4, fullPage: false });
    savedFiles.push(p4);
    console.log('Saved:', p4);
  }

  // 5. Workspace Showcase (Act V)
  const act5 = page.locator('#investigation');
  if (await act5.count() > 0) {
    await act5.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    const p5 = path.join(evidenceDir, 'skytrace-05-investigation.png');
    await page.screenshot({ path: p5, fullPage: false });
    savedFiles.push(p5);
    console.log('Saved:', p5);
  }

  // 6. CTA & Footer (Act VI)
  const act6 = page.locator('#enter-skytrace');
  if (await act6.count() > 0) {
    await act6.scrollIntoViewIfNeeded();
    await page.waitForTimeout(1000);
    const p6 = path.join(evidenceDir, 'skytrace-06-cta-footer.png');
    await page.screenshot({ path: p6, fullPage: false });
    savedFiles.push(p6);
    console.log('Saved:', p6);
  }

  // 7. Workspace IDE route
  console.log('Navigating to http://localhost:3000/workspace ...');
  await page.goto('http://localhost:3000/workspace', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(4000);
  const p7 = path.join(evidenceDir, 'skytrace-07-workspace-ide.png');
  await page.screenshot({ path: p7, fullPage: false });
  savedFiles.push(p7);
  console.log('Saved:', p7);

  // 8. Mobile viewport test
  console.log('Navigating to http://localhost:3000 on mobile viewport...');
  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    deviceScaleFactor: 2,
    isMobile: true,
  });
  const mobilePage = await mobileContext.newPage();
  await mobilePage.goto('http://localhost:3000', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await mobilePage.waitForTimeout(3000);
  const p8 = path.join(evidenceDir, 'skytrace-08-mobile.png');
  await mobilePage.screenshot({ path: p8, fullPage: false });
  savedFiles.push(p8);
  console.log('Saved:', p8);

  // Copy all saved files to artifact directory
  for (const src of savedFiles) {
    if (fs.existsSync(src)) {
      const dest = path.join(artifactDir, path.basename(src));
      fs.copyFileSync(src, dest);
      console.log('Copied to artifact:', dest);
    }
  }

  await browser.close();
  console.log(`All ${savedFiles.length} screenshots captured and copied successfully.`);
}

main().catch(err => {
  console.error('Error during screenshot capture:', err);
  process.exit(1);
});
