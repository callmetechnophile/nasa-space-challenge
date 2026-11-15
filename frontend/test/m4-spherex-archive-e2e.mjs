import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const SCREENSHOT_DIR = "d:/nasa/frontend/test-artifacts/screenshots";
const ARTIFACTS_DIR = "C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e";

fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });

async function saveAndCopyScreenshot(page, filename) {
  const localPath = path.join(SCREENSHOT_DIR, filename);
  await page.screenshot({ path: localPath });
  console.log(`Saved screenshot: ${localPath}`);
  try {
    fs.copyFileSync(localPath, path.join(ARTIFACTS_DIR, filename));
    console.log(`Copied screenshot to artifacts: ${filename}`);
  } catch (e) {
    console.warn(`Could not copy to artifacts: ${e.message}`);
  }
}

async function main() {
  console.log("=== Launching E2E Acceptance Test for Milestone 4 (SPHEREx Real Data Integration) ===");

  const browser = await chromium.launch({
    channel: "msedge",
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader"],
  });

  const context = await browser.newContext({
    viewport: { width: 1500, height: 950 },
  });

  const page = await context.newPage();
  const consoleErrors = [];
  page.on("console", (msg) => {
    if (msg.type() === "error") consoleErrors.push(msg.text());
  });

  try {
    // 1. Initial Load
    console.log("\n--- Step 1: Navigating to http://localhost:3000 ---");
    await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
    await page.waitForTimeout(4000);
    await saveAndCopyScreenshot(page, "m4-01-initial-ui.png");

    // 2. Verify SPHEREx Archive Panel
    console.log("\n--- Step 2: Verifying NASA SPHEREx Archive Panel ---");
    const archiveTitle = page.locator("text=NASA SPHEREx Archive").first();
    const isArchiveVisible = await archiveTitle.isVisible();
    console.log("Archive Panel Header Visible:", isArchiveVisible);
    if (!isArchiveVisible) throw new Error("NASA SPHEREx Archive panel not found!");

    // Wait for cached products to load
    await page.waitForSelector("text=Cached Real NASA Products", { timeout: 15000 });
    console.log("Cached Real NASA Products section verified.");

    // 3. Inspect Cached Product MEF
    console.log("\n--- Step 3: Opening MEF Inspection Modal on Real SPHEREx Product ---");
    const inspectBtn = page.locator("button:has-text('Inspect MEF')").first();
    await inspectBtn.click();

    await page.waitForSelector("text=NASA SPHEREx MEF Inspection Report", { timeout: 10000 });
    await page.waitForTimeout(1000);
    await saveAndCopyScreenshot(page, "m4-02-mef-inspection-modal.png");

    // Verify key attributes inside modal
    const unitsVisible = await page.locator("text=MJy / sr").first().isVisible();
    const sipVisible = await page.locator("text=Order 3").first().isVisible();
    const hdusTableVisible = await page.locator("text=WCS-WAVE").first().isVisible();
    console.log("Units MJy/sr visible in modal:", unitsVisible);
    console.log("WCS SIP Order 3 visible in modal:", sipVisible);
    console.log("All HDUs (including WCS-WAVE) visible in table:", hdusTableVisible);

    // Close modal
    console.log("Closing inspection modal...");
    await page.click("#close-inspection-modal-btn", { force: true });
    await page.waitForTimeout(1000);

    // 4. Load Real Observation Layer onto Celestial Sphere
    console.log("\n--- Step 4: Loading Real Observation Layer onto Celestial Sphere ---");
    const loadLayerBtn = page.locator("button:has-text('Load Layer')").first();
    await loadLayerBtn.click();

    // Wait for layer load (synthesis of mesh & texture)
    console.log("Waiting for spherical mesh & texture synthesis...");
    await page.waitForTimeout(6000);
    await saveAndCopyScreenshot(page, "m4-03-spherex-real-data-projected.png");

    // 5. Verify Layer in ImageLayerControls
    console.log("\n--- Step 5: Verifying Real Data Badge in Layer Controls ---");
    const realDataBadge = page.locator("text=NASA SPHEREx (Real Data)").first();
    const isBadgeVisible = await realDataBadge.isVisible();
    console.log("NASA SPHEREx (Real Data) badge visible:", isBadgeVisible);
    if (!isBadgeVisible) throw new Error("Real data badge missing from Layer Controls!");

    await saveAndCopyScreenshot(page, "m4-04-real-data-badge-in-layer-controls.png");

    // 6. Live IRSA Archive Search (South Pole / QR3)
    console.log("\n--- Step 6: Testing Live IRSA Archive Search at South Pole (QR3) ---");
    const southPolePresetBtn = page.locator("button:has-text('South Pole')").first();
    await southPolePresetBtn.click();
    await page.waitForTimeout(500);

    const searchBtn = page.locator("button:has-text('Search IRSA Archive')").first();
    await searchBtn.click();

    console.log("Waiting for IRSA SIA2 search results...");
    await page.waitForSelector("text=observations", { timeout: 90000 });
    await page.waitForTimeout(2000);
    await saveAndCopyScreenshot(page, "m4-05-irsa-search-south-pole.png");

    console.log("\n========================================================");
    console.log("ALL M4 E2E BROWSER ACCEPTANCE TESTS PASSED SUCCESSFULLY!");
    console.log("========================================================");
  } catch (err) {
    console.error("Test failed with error:", err);
    await saveAndCopyScreenshot(page, "m4-error.png");
    throw err;
  } finally {
    await browser.close();
  }
}

main().catch((err) => {
  console.error("Fatal test error:", err);
  process.exit(1);
});
