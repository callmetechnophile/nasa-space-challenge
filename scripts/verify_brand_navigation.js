const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
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
  await page.waitForTimeout(2500);

  // 1. Verify top-left brand link element
  const brandLink = page.locator('header.astro-titlebar .astro-brand-link');
  await brandLink.waitFor({ state: 'visible', timeout: 5000 });
  
  const href = await brandLink.getAttribute('href');
  console.log('Brand link href:', href);
  if (href !== '/') throw new Error(`Brand link href is "${href}", expected "/"`);

  const ariaLabel = await brandLink.getAttribute('aria-label');
  console.log('Brand link aria-label:', ariaLabel);
  if (ariaLabel !== 'SkyTrace Home') throw new Error(`Brand link aria-label is "${ariaLabel}", expected "SkyTrace Home"`);

  // Verify generic Atom icon is gone and custom SVG is present
  const hasAtom = await page.locator('.astro-brand .lucide-atom').count();
  console.log('Generic Atom icon count in brand:', hasAtom);
  if (hasAtom > 0) throw new Error('Generic Atom icon is still present in branding area!');

  const brandMarkSvg = brandLink.locator('svg');
  const svgCount = await brandMarkSvg.count();
  console.log('Brand mark SVG count:', svgCount);
  if (svgCount === 0) throw new Error('Custom brand mark SVG is missing!');

  // Verify project selector is separate and outside the link
  const projectSwitchInsideLink = await brandLink.locator('.astro-project-switch').count();
  console.log('Project switch nested inside link:', projectSwitchInsideLink);
  if (projectSwitchInsideLink > 0) throw new Error('Project switch is nested inside Home link!');

  const projectSwitch = page.locator('header.astro-titlebar .astro-project-switch');
  await projectSwitch.waitFor({ state: 'visible', timeout: 5000 });
  console.log('Independent project switch text:', (await projectSwitch.innerText()).trim());

  // Capture screenshot of desktop workspace topbar with custom brand mark
  const topbarScreenshot = path.join(artifactDir, 'skytrace-brand-navigation-desktop.png');
  await page.screenshot({ path: topbarScreenshot });
  console.log('Saved desktop topbar screenshot to', topbarScreenshot);

  // 2. Test clicking the custom icon navigates to /
  console.log('\n--- Test 1: Clicking brand mark icon ---');
  const brandIcon = brandLink.locator('.astro-brand-mark');
  await brandIcon.click();
  await page.waitForURL('http://localhost:3000/', { timeout: 10000 });
  console.log('Successfully navigated to landing page! Current URL:', page.url());

  // 3. Test clicking wordmark from /workspace
  console.log('\n--- Test 2: Clicking wordmark text from /workspace ---');
  await page.goto('http://localhost:3000/workspace', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(1500);

  const wordmark = page.locator('header.astro-titlebar .astro-brand-name');
  await wordmark.click();
  await page.waitForURL('http://localhost:3000/', { timeout: 10000 });
  console.log('Successfully navigated to landing page! Current URL:', page.url());

  // 4. Test clicking project switch does NOT navigate away
  console.log('\n--- Test 3: Clicking project selector button ---');
  await page.goto('http://localhost:3000/workspace', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(1500);

  await page.locator('header.astro-titlebar .astro-project-switch').click();
  await page.waitForTimeout(500);
  console.log('Current URL after project switch click:', page.url());
  if (!page.url().includes('/workspace')) throw new Error('Project switch incorrectly navigated away!');

  // 5. Test command search still works
  console.log('\n--- Test 4: Verifying command search ---');
  const searchBtn = page.locator('.astro-command-search');
  await searchBtn.click();
  await page.waitForTimeout(300);
  const quickMenu = page.locator('.astro-quick-menu');
  const isMenuVisible = await quickMenu.isVisible();
  console.log('Quick menu visible after search click:', isMenuVisible);
  if (!isMenuVisible) throw new Error('Command search menu did not open!');
  await page.keyboard.press('Escape');

  // 6. Test STATUS popover still works
  console.log('\n--- Test 5: Verifying STATUS popover ---');
  const statusTrigger = page.locator('.astro-status-trigger');
  await statusTrigger.click();
  await page.waitForTimeout(300);
  const statusPopover = page.locator('.astro-status-popover');
  const isStatusOpen = await statusPopover.isVisible();
  console.log('STATUS popover visible:', isStatusOpen);
  if (!isStatusOpen) throw new Error('STATUS popover did not open!');
  await page.keyboard.press('Escape');

  // 7. Test Mobile layout (375x667)
  console.log('\n--- Test 6: Mobile Viewport (375x667) ---');
  await page.setViewportSize({ width: 375, height: 667 });
  await page.waitForTimeout(500);

  const mobileBrandLink = page.locator('header.astro-titlebar .astro-brand-link');
  const isMobileBrandVisible = await mobileBrandLink.isVisible();
  console.log('Mobile brand link visible:', isMobileBrandVisible);
  if (!isMobileBrandVisible) throw new Error('Brand link not visible on mobile!');

  const mobileScreenshot = path.join(artifactDir, 'skytrace-brand-navigation-mobile.png');
  await page.screenshot({ path: mobileScreenshot });
  console.log('Saved mobile screenshot to', mobileScreenshot);

  // Click mobile brand link
  await mobileBrandLink.click();
  await page.waitForURL('http://localhost:3000/', { timeout: 10000 });
  console.log('Mobile click successfully navigated to landing page! Current URL:', page.url());

  await browser.close();
  console.log('\n=========================================');
  console.log('ALL BRAND NAVIGATION CHECKS PASSED 100%!');
  console.log('=========================================');
}

main().catch((err) => {
  console.error('Verification failed:', err);
  process.exit(1);
});
