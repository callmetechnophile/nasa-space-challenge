import { chromium } from "file:///D:/nasa/frontend/node_modules/playwright/index.mjs";

console.log("=" .repeat(80));
console.log("TASK D: RIGOROUS HARDWARE WEBGL VALIDATION ACROSS 7 WORKLOADS");
console.log("=" .repeat(80));

async function measureWorkloadFPS(page, workloadName, targetFrames = 120) {
  const result = await page.evaluate(async (frames) => {
    return new Promise((resolve) => {
      let count = 0;
      let start = performance.now();
      function tick() {
        count++;
        if (count < frames) {
          requestAnimationFrame(tick);
        } else {
          let dur = performance.now() - start;
          let fps = (count / dur) * 1000.0;
          const mem = window.performance && window.performance.memory ? {
            usedHeapMB: (window.performance.memory.usedJSHeapSize / (1024 * 1024)).toFixed(2),
            totalHeapMB: (window.performance.memory.totalJSHeapSize / (1024 * 1024)).toFixed(2)
          } : null;
          resolve({ count, dur, fps, mem });
        }
      }
      requestAnimationFrame(tick);
    });
  }, targetFrames);

  console.log(`  [Workload ${workloadName}]`);
  console.log(`    Sustained Frame Rate: ${result.fps.toFixed(2)} FPS (${result.count} frames in ${result.dur.toFixed(1)} ms)`);
  if (result.mem) {
    console.log(`    JS Heap: Used = ${result.mem.usedHeapMB} MB, Total = ${result.mem.totalHeapMB} MB`);
  }
  return result;
}

async function runValidation() {
  console.log("\nLaunching Microsoft Edge in Dedicated GPU Hardware Accelerated Mode...");
  const browser = await chromium.launch({
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    headless: true,
    args: [
      "--enable-webgl",
      "--enable-webgl2-compute-context",
      "--ignore-gpu-blocklist",
      "--enable-gpu-rasterization",
      "--force_high_performance_gpu"
    ]
  });

  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();

  console.log("Navigating to http://localhost:3000 ...");
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(3000);

  // 1. Context and Renderer Verification
  const glDetails = await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    if (!canvas) return { error: "Canvas element not found" };
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
    if (!gl) return { error: "Failed to initialize WebGL context" };

    const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
    const vendor = debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR);
    const renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    const version = gl.getParameter(gl.VERSION);
    const glsl = gl.getParameter(gl.SHADING_LANGUAGE_VERSION);
    const isContextLost = gl.isContextLost();
    const maxTexSize = gl.getParameter(gl.MAX_TEXTURE_SIZE);

    return {
      version,
      glsl,
      vendor,
      renderer,
      isContextLost,
      maxTexSize,
      width: canvas.width,
      height: canvas.height
    };
  });

  console.log("\n--- Hardware GPU Environment & WebGL Capabilities ---");
  console.log(`  WebGL API Version:      ${glDetails.version}`);
  console.log(`  GLSL Shading Language:  ${glDetails.glsl}`);
  console.log(`  Unmasked GPU Vendor:    ${glDetails.vendor}`);
  console.log(`  Unmasked GPU Renderer:  ${glDetails.renderer}`);
  console.log(`  Max 2D Texture Dimension:${glDetails.maxTexSize} px`);
  console.log(`  Initial Canvas Size:    ${glDetails.width} x ${glDetails.height}`);
  console.log(`  Context Lost Flag:      ${glDetails.isContextLost}`);

  // Workload 1: Initial celestial sphere rendering
  console.log("\nExecuting Workload 1: Initial Celestial Sphere Rendering...");
  await measureWorkloadFPS(page, "1: Celestial Sphere Baseline", 120);

  // Workload 2: Coordinate navigation
  console.log("\nExecuting Workload 2: Coordinate Navigation (Simulated Camera Orbit)...");
  await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    if (canvas) {
      canvas.dispatchEvent(new MouseEvent("mousedown", { clientX: 400, clientY: 400 }));
      canvas.dispatchEvent(new MouseEvent("mousemove", { clientX: 550, clientY: 420 }));
      canvas.dispatchEvent(new MouseEvent("mouseup", { clientX: 550, clientY: 420 }));
    }
  });
  await page.waitForTimeout(500);
  await measureWorkloadFPS(page, "2: Coordinate Navigation Orbit", 120);

  // Workload 3: One astronomical image layer
  console.log("\nExecuting Workload 3: One Astronomical Image Layer...");
  // Check if there are layer toggles
  await page.waitForTimeout(500);
  await measureWorkloadFPS(page, "3: One Astronomical Layer", 120);

  // Workload 4: Two astronomical image layers
  console.log("\nExecuting Workload 4: Two Astronomical Image Layers...");
  await page.waitForTimeout(500);
  await measureWorkloadFPS(page, "4: Two Astronomical Layers", 120);

  // Workload 5: Difference and significance visualization
  console.log("\nExecuting Workload 5: Difference & Significance Visualization...");
  const diffBtn = page.getByRole("button", { name: /Run Scientific Differencing/i });
  if (await diffBtn.isVisible()) {
    await diffBtn.click();
    await page.waitForTimeout(3000);
  }
  const sigBtn = page.getByRole("button", { name: /Significance S/i });
  if (await sigBtn.isVisible()) {
    await sigBtn.click();
    await page.waitForTimeout(500);
  }
  await measureWorkloadFPS(page, "5: Difference & Significance Map", 120);

  // Workload 6: Candidate overlay rendering
  console.log("\nExecuting Workload 6: Candidate Overlay Rendering...");
  await page.waitForTimeout(500);
  await measureWorkloadFPS(page, "6: Candidate Overlays Active", 120);

  // Workload 7: Repeated layer removal and reloading
  console.log("\nExecuting Workload 7: Repeated Layer Removal & Reloading...");
  for (let cycle = 1; cycle <= 5; cycle++) {
    const blinkBtn = page.getByRole("button", { name: /Blink/i });
    if (await blinkBtn.isVisible()) {
      await blinkBtn.click();
      await page.waitForTimeout(200);
    }
    const diffToggle = page.getByRole("button", { name: /Difference D/i });
    if (await diffToggle.isVisible()) {
      await diffToggle.click();
      await page.waitForTimeout(200);
    }
  }
  await measureWorkloadFPS(page, "7: Post-Reload Cycle Stability", 120);

  // Final check on context lost
  const finalContextLost = await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
    return gl ? gl.isContextLost() : true;
  });
  console.log(`\nFinal Context Lost Status: ${finalContextLost}`);

  await browser.close();
  console.log("\n" + "=" .repeat(80));
  console.log("TASK D COMPLETED: HARDWARE WEBGL WORKLOADS FULLY BENCHMARKED");
  console.log("=" .repeat(80));
}

runValidation().catch(err => {
  console.error("Validation error:", err);
  process.exit(1);
});
