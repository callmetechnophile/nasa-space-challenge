const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function run() {
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

  console.log('Launching browser with msedge...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  console.log('Navigating to http://localhost:3000/workspace...');
  await page.goto('http://localhost:3000/workspace', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // 1. Verify top bar has STATUS control
  const statusTrigger = page.locator('.astro-status-trigger');
  await statusTrigger.waitFor({ state: 'visible', timeout: 5000 });
  const statusText = await statusTrigger.innerText();
  console.log('Top-bar status trigger text:', statusText.trim());

  // 2. Verify top navigation bar does NOT contain DEMONSTRATION MODE
  const topNav = page.locator('header.astro-titlebar');
  const topNavText = await topNav.innerText();
  const hasDemoInTopNav = topNavText.includes('DEMONSTRATION MODE');
  console.log('Top-bar contains DEMONSTRATION MODE:', hasDemoInTopNav);
  if (hasDemoInTopNav) throw new Error('DEMONSTRATION MODE still found in top navigation bar!');

  // 3. Verify canvas bottom-left has no floating telemetry panel
  const canvasBottomLeft = page.locator('.astro-canvas-bottom-left');
  const canvasBottomLeftCount = await canvasBottomLeft.count();
  console.log('Canvas bottom-left container count:', canvasBottomLeftCount);

  // Verify no StatusPanel floating in canvas
  const canvasFloatingStatus = page.locator('.astro-canvas .astro-status-popover, .astro-canvas-bottom-left');
  const canvasFloatingCount = await canvasFloatingStatus.count();
  console.log('Canvas floating telemetry panel count:', canvasFloatingCount);
  if (canvasFloatingCount > 0) throw new Error('Floating telemetry card still exists in 3D canvas!');

  // 4. Click STATUS to open popover
  console.log('Clicking STATUS button...');
  await statusTrigger.click();
  await page.waitForTimeout(600);

  const popover = page.locator('.astro-status-popover');
  await popover.waitFor({ state: 'visible', timeout: 5000 });
  const popoverText = await popover.innerText();
  console.log('\n--- POPOVER CONTENTS ---');
  console.log(popoverText);
  console.log('------------------------\n');

  // Verify telemetry fields
  const checks = [
    'SYSTEM STATUS & TELEMETRY',
    'ACTIVE',
    'Three.js (WebGL)',
    'Demo Stars:',
    'Distance:',
    'FOV:',
    'Polar (θ):',
    'Azimuth (φ):',
    'Data Source: Synthetic demonstration data (Procedural ICRS)',
  ];

  for (const check of checks) {
    const passed = popoverText.includes(check);
    console.log(`Field check [${check}]: ${passed ? 'PASS' : 'FAIL'}`);
    if (!passed) throw new Error(`Missing field: ${check}`);
  }

  // Capture desktop screenshot with popover open
  const desktopScreenshot = path.join(artifactDir, 'skytrace-workspace-status-popover-desktop.png');
  await page.screenshot({ path: desktopScreenshot });
  console.log('Saved desktop screenshot to', desktopScreenshot);

  // 5. Test Escape key closes popover
  console.log('Testing Escape key to close popover...');
  await page.keyboard.press('Escape');
  await page.waitForTimeout(400);
  const isVisibleAfterEscape = await popover.isVisible();
  console.log('Popover visible after Escape:', isVisibleAfterEscape);
  if (isVisibleAfterEscape) throw new Error('Popover did not close on Escape');

  // 6. Test Click outside closes popover
  console.log('Re-opening popover...');
  await statusTrigger.click();
  await page.waitForTimeout(400);
  console.log('Clicking outside on brand logo...');
  await page.locator('.astro-brand').click();
  await page.waitForTimeout(400);
  const isVisibleAfterClickOutside = await popover.isVisible();
  console.log('Popover visible after click outside:', isVisibleAfterClickOutside);
  if (isVisibleAfterClickOutside) throw new Error('Popover did not close on click outside');

  // 7. Test Clicking STATUS toggles it open and closed
  console.log('Testing toggle by clicking STATUS twice...');
  await statusTrigger.click();
  await page.waitForTimeout(300);
  if (!(await popover.isVisible())) throw new Error('Popover should be visible after click 1');
  await statusTrigger.click();
  await page.waitForTimeout(300);
  if (await popover.isVisible()) throw new Error('Popover should be closed after click 2');

  // 8. Test Mobile Viewport
  console.log('\n--- Testing Mobile Viewport (375x667) ---');
  await page.setViewportSize({ width: 375, height: 667 });
  await page.waitForTimeout(500);

  const mobileStatusTrigger = page.locator('.astro-status-trigger');
  const isMobileStatusVisible = await mobileStatusTrigger.isVisible();
  console.log('Mobile STATUS trigger visible:', isMobileStatusVisible);
  if (!isMobileStatusVisible) throw new Error('STATUS trigger not visible on mobile');

  await mobileStatusTrigger.click();
  await page.waitForTimeout(500);

  const mobilePopover = page.locator('.astro-status-popover');
  const isMobilePopoverVisible = await mobilePopover.isVisible();
  console.log('Mobile popover visible:', isMobilePopoverVisible);
  if (!isMobilePopoverVisible) throw new Error('Popover did not open on mobile');

  // Check bounding box on mobile to ensure no horizontal clipping
  const box = await mobilePopover.boundingBox();
  console.log('Mobile popover bounding box:', box);
  if (box.x < 0 || box.x + box.width > 375 + 10) {
    console.warn('Warning: mobile popover may be clipped horizontally:', box);
  }

  const mobileScreenshot = path.join(artifactDir, 'skytrace-workspace-status-popover-mobile.png');
  await page.screenshot({ path: mobileScreenshot });
  console.log('Saved mobile screenshot to', mobileScreenshot);

  await browser.close();
  console.log('\n=========================================');
  console.log('ALL VERIFICATION CHECKS PASSED PERFECTLY!');
  console.log('=========================================');
}

run().catch((err) => {
  console.error('Verification failed:', err);
  process.exit(1);
});
