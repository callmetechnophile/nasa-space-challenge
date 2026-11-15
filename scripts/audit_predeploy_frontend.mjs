/**
 * Pre-Deployment Stage 1: Frontend Integrity & WebGL Diagnostics Audit.
 * Tests Next.js app rendering, Three.js canvas initialization,
 * WebGL context stability, API connectivity, and browser console errors.
 */

import { chromium } from "file:///D:/nasa/frontend/node_modules/playwright/index.mjs";

console.log("================================================================================");
console.log("STAGE 1 — FRONTEND INTEGRITY & WEBGL DIAGNOSTICS AUDIT");
console.log("================================================================================");

async function main() {
  console.log("Launching headless Microsoft Edge with hardware-accelerated WebGL...");
  const browser = await chromium.launch({
    channel: "msedge",
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader"],
  });

  const context = await browser.newContext({
    viewport: { width: 1400, height: 900 },
  });

  const page = await context.newPage();
  
  const consoleMessages = [];
  const consoleErrors = [];
  const consoleWarnings = [];

  page.on("console", (msg) => {
    const text = msg.text();
    const type = msg.type();
    consoleMessages.push({ type, text });
    if (type === "error") {
      consoleErrors.push(text);
    } else if (type === "warning") {
      consoleWarnings.push(text);
    }
  });

  page.on("pageerror", (err) => {
    consoleErrors.push(err.toString());
  });

  // 1. Navigate to frontend root
  console.log("1. Navigating to http://localhost:3000 ...");
  const response = await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
  console.log(`   HTTP Response Status: ${response.status()} (${response.statusText()})`);
  assert(response.status() === 200, "Frontend did not return HTTP 200");

  await page.waitForTimeout(3000);

  // 2. DOM & Canvas Inspection
  console.log("\n2. Inspecting DOM & WebGL Three.js Canvas...");
  const title = await page.title();
  console.log(`   Page Title: "${title}"`);

  const canvasCount = await page.locator("canvas").count();
  console.log(`   Canvas Elements Found: ${canvasCount}`);
  assert(canvasCount >= 1, "No Three.js canvas element found on page");

  // 3. WebGL Context Evaluation
  console.log("\n3. Evaluating WebGL Context Stability...");
  const webglDiag = await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    if (!canvas) return { error: "No canvas element" };
    
    // Check if webgl or webgl2 context exists
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
    if (!gl) return { error: "Failed to acquire WebGL context" };

    const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
    const vendor = debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR);
    const renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    const version = gl.getParameter(gl.VERSION);
    const isContextLost = gl.isContextLost();

    return {
      version,
      vendor,
      renderer,
      isContextLost,
      viewportWidth: gl.drawingBufferWidth,
      viewportHeight: gl.drawingBufferHeight,
    };
  });

  console.log("   WebGL Diagnostics:");
  console.log(`     Version:      ${webglDiag.version}`);
  console.log(`     Vendor:       ${webglDiag.vendor}`);
  console.log(`     Renderer:     ${webglDiag.renderer}`);
  console.log(`     Buffer Size:  ${webglDiag.viewportWidth} x ${webglDiag.viewportHeight}`);
  console.log(`     Context Lost: ${webglDiag.isContextLost}`);
  assert(!webglDiag.isContextLost, "WebGL context is lost!");

  // 4. API Connectivity Test from Browser Context
  console.log("\n4. Testing Browser-to-Backend API Connectivity (127.0.0.1:8000)...");
  const apiCheck = await page.evaluate(async () => {
    try {
      const res = await fetch("http://127.0.0.1:8000/health");
      const data = await res.json();
      return { ok: res.ok, status: res.status, data };
    } catch (e) {
      return { ok: false, error: e.toString() };
    }
  });
  console.log(`   Backend /health Fetch: ok=${apiCheck.ok}, status=${apiCheck.status}, data=${JSON.stringify(apiCheck.data)}`);
  assert(apiCheck.ok, "Frontend failed to connect to backend /health");

  // 5. Console Error & Warning Audit
  console.log("\n5. Browser Console Error Audit...");
  console.log(`   Total Console Messages: ${consoleMessages.length}`);
  console.log(`   Console Warnings:       ${consoleWarnings.length}`);
  console.log(`   Console Errors:         ${consoleErrors.length}`);

  if (consoleErrors.length > 0) {
    console.log("   Console Errors Encountered:");
    consoleErrors.forEach((err, idx) => console.log(`     [${idx+1}] ${err}`));
  } else {
    console.log("   Zero fatal console errors encountered during Three.js canvas rendering.");
  }

  // Filter ignorable warnings (e.g. Next.js hydration dev notice if any)
  const fatalErrors = consoleErrors.filter(e => !e.includes("favicon"));
  assert(fatalErrors.length === 0, `Fatal browser console errors: ${fatalErrors.join("; ")}`);

  await browser.close();
  console.log("\n================================================================================");
  console.log("FRONTEND INTEGRITY & WEBGL AUDIT: PASS (0 ERRORS, WEBGL STABLE)");
  console.log("================================================================================");
}

function assert(condition, message) {
  if (!condition) {
    console.error(`ASSERTION FAILED: ${message}`);
    process.exit(1);
  }
}

main().catch(err => {
  console.error("Audit Execution Failed:", err);
  process.exit(1);
});
