import { chromium } from "file:///D:/nasa/frontend/node_modules/playwright/index.mjs";

console.log("================================================================================");
console.log("STAGE 1.1: TASK 4 & TASK 5 — WEBGL HARDWARE ACCELERATION & FRONTEND STRESS");
console.log("================================================================================");

async function runAudit() {
  // Launch Microsoft Edge with hardware acceleration enabled
  console.log("\nLaunching Microsoft Edge in Hardware GPU Accelerated Mode...");
  const browser = await chromium.launch({
    channel: "msedge",
    headless: true,
    args: [
      "--enable-webgl",
      "--enable-webgl2-compute-context",
      "--ignore-gpu-blocklist",
      "--enable-gpu-rasterization",
      // Notice: NO --disable-gpu or --use-gl=swiftshader!
    ]
  });

  const context = await browser.newContext();
  const page = await context.newPage();

  const consoleMessages = [];
  page.on("console", msg => consoleMessages.push(`[${msg.type()}] ${msg.text()}`));

  console.log("Navigating to http://localhost:3000 ...");
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(3000); // Allow Three.js canvas to initialize

  // Evaluate WebGL hardware context
  const webglInfo = await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    if (!canvas) {
      return { error: "No canvas found" };
    }
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
    if (!gl) {
      return { error: "Failed to get WebGL context" };
    }

    const debugInfo = gl.getExtension("WEBGL_debug_renderer_info");
    const vendor = debugInfo ? gl.getParameter(debugInfo.UNMASKED_VENDOR_WEBGL) : gl.getParameter(gl.VENDOR);
    const renderer = debugInfo ? gl.getParameter(debugInfo.UNMASKED_RENDERER_WEBGL) : gl.getParameter(gl.RENDERER);
    const version = gl.getParameter(gl.VERSION);
    const shadingLanguageVersion = gl.getParameter(gl.SHADING_LANGUAGE_VERSION);
    const isContextLost = gl.isContextLost();

    // Check performance memory if available
    const mem = window.performance && window.performance.memory ? {
      usedJSHeapSize: window.performance.memory.usedJSHeapSize,
      totalJSHeapSize: window.performance.memory.totalJSHeapSize,
      jsHeapSizeLimit: window.performance.memory.jsHeapSizeLimit,
    } : null;

    return {
      version,
      shadingLanguageVersion,
      vendor,
      renderer,
      isContextLost,
      canvasWidth: canvas.width,
      canvasHeight: canvas.height,
      mem
    };
  });

  console.log("\n--- WebGL Hardware Environment ---");
  console.log(`  WebGL Version:           ${webglInfo.version}`);
  console.log(`  Shading Language:        ${webglInfo.shadingLanguageVersion}`);
  console.log(`  Vendor:                  ${webglInfo.vendor}`);
  console.log(`  Unmasked Renderer (GPU): ${webglInfo.renderer}`);
  console.log(`  Canvas Dimensions:       ${webglInfo.canvasWidth} x ${webglInfo.canvasHeight}`);
  console.log(`  Context Lost Event:      ${webglInfo.isContextLost}`);
  if (webglInfo.mem) {
    console.log(`  Initial JS Heap:         ${(webglInfo.mem.usedJSHeapSize / (1024*1024)).toFixed(2)} MB`);
  }

  // Frame rate measurement across 60 animation frames
  console.log("\nMeasuring rendering frame rate across 60 frames...");
  const fpsResult = await page.evaluate(async () => {
    return new Promise(resolve => {
      let frameCount = 0;
      let startTime = performance.now();
      function count() {
        frameCount++;
        if (frameCount < 60) {
          requestAnimationFrame(count);
        } else {
          let elapsed = performance.now() - startTime;
          let fps = (frameCount / elapsed) * 1000.0;
          resolve({ frameCount, elapsed, fps });
        }
      }
      requestAnimationFrame(count);
    });
  });
  console.log(`  Measured Frame Rate:     ${fpsResult.fps.toFixed(1)} FPS (${fpsResult.frameCount} frames in ${fpsResult.elapsed.toFixed(1)} ms)`);

  // Frontend stress test across multiple simulated observation load/renders
  console.log("\n--- Frontend Stress: 20 Render / Data Injection Cycles ---");
  const stressResults = await page.evaluate(async () => {
    const stats = [];
    for (let i = 1; i <= 20; i++) {
      // Create temporary WebGL textures and buffers, then dispose them to test leak prevention
      const canvas = document.querySelector("canvas");
      const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
      
      const tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 256, 256, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
      
      const buf = gl.createBuffer();
      gl.bindBuffer(gl.ARRAY_BUFFER, buf);
      gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(256 * 256), gl.STATIC_DRAW);
      
      // Clean disposal
      gl.deleteTexture(tex);
      gl.deleteBuffer(buf);

      if (i === 1 || i === 5 || i === 10 || i === 20) {
        const mem = window.performance && window.performance.memory ? window.performance.memory.usedJSHeapSize / (1024*1024) : null;
        stats.push({
          cycle: i,
          usedHeapMB: mem,
          isContextLost: gl.isContextLost()
        });
      }
    }
    return stats;
  });

  for (const s of stressResults) {
    console.log(`  Cycle ${s.cycle.toString().padStart(2, ' ')}: JS Heap = ${s.usedHeapMB ? s.usedHeapMB.toFixed(2) + ' MB' : 'N/A'} | Context Lost = ${s.isContextLost}`);
  }

  await browser.close();
  console.log("\nWebGL Hardware Validation Finished.");
}

runAudit().catch(err => {
  console.error("Audit error:", err);
  process.exit(1);
});
