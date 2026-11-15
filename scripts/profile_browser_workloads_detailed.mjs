import { chromium } from "file:///D:/nasa/frontend/node_modules/playwright/index.mjs";

console.log("=".repeat(80));
console.log("STAGE 1.1.3: DETAILED BROWSER PERFORMANCE VERIFICATION ACROSS 5 WORKLOADS");
console.log("=".repeat(80));

async function getCDPMetrics(client) {
  const { metrics } = await client.send("Performance.getMetrics");
  const result = {};
  for (const m of metrics) {
    result[m.name] = m.value;
  }
  return result;
}

async function getWebGLInfo(page) {
  return await page.evaluate(() => {
    const c = document.querySelector("canvas");
    if (!c) return { error: "No canvas element found" };
    const gl = c.getContext("webgl2") || c.getContext("webgl");
    if (!gl) return { error: "Could not acquire WebGL context" };

    const dbgRenderInfo = gl.getExtension("WEBGL_debug_renderer_info");
    const unmaskedVendor = dbgRenderInfo ? gl.getParameter(dbgRenderInfo.UNMASKED_VENDOR_WEBGL) : "N/A";
    const unmaskedRenderer = dbgRenderInfo ? gl.getParameter(dbgRenderInfo.UNMASKED_RENDERER_WEBGL) : "N/A";
    const vendor = gl.getParameter(gl.VENDOR);
    const renderer = gl.getParameter(gl.RENDERER);
    const version = gl.getParameter(gl.VERSION);
    const shadingLanguageVersion = gl.getParameter(gl.SHADING_LANGUAGE_VERSION);

    return {
      unmaskedVendor,
      unmaskedRenderer,
      vendor,
      renderer,
      version,
      shadingLanguageVersion,
      drawingBufferWidth: gl.drawingBufferWidth,
      drawingBufferHeight: gl.drawingBufferHeight
    };
  });
}

async function measureDetailedFPS(page, durationMs = 3000) {
  return await page.evaluate((ms) => {
    return new Promise((resolve) => {
      let frames = 0;
      let frameDurs = [];
      let lastTime = performance.now();
      let startTime = lastTime;

      function loop(now) {
        frames++;
        const delta = now - lastTime;
        frameDurs.push(delta);
        lastTime = now;

        if (now - startTime < ms) {
          requestAnimationFrame(loop);
        } else {
          const totalTime = now - startTime;
          const fps = (frames / totalTime) * 1000;

          // Filter out initialization anomaly if delta <= 0
          const validDurs = frameDurs.filter(d => d > 0);
          validDurs.sort((a, b) => a - b);

          const median = validDurs[Math.floor(validDurs.length * 0.50)];
          const p95 = validDurs[Math.floor(validDurs.length * 0.95)];
          const p99 = validDurs[Math.floor(validDurs.length * 0.99)];
          const min = validDurs[0];
          const max = validDurs[validDurs.length - 1];

          // 30 FPS threshold is 33.333 ms
          const droppedFrames30fps = validDurs.filter(d => d > 33.333).length;
          const droppedPercentage30fps = (droppedFrames30fps / validDurs.length) * 100;

          // 60 FPS threshold is 16.667 ms
          const droppedFrames60fps = validDurs.filter(d => d > 16.667).length;
          const droppedPercentage60fps = (droppedFrames60fps / validDurs.length) * 100;

          resolve({
            totalFrames: frames,
            validSampleCount: validDurs.length,
            totalDurationMs: totalTime,
            meanFps: fps,
            medianFrameTimeMs: median,
            p95FrameTimeMs: p95,
            p99FrameTimeMs: p99,
            minFrameTimeMs: min,
            maxFrameTimeMs: max,
            droppedFramesCount30fps: droppedFrames30fps,
            droppedPercentage30fps: droppedPercentage30fps,
            droppedFramesCount60fps: droppedFrames60fps,
            droppedPercentage60fps: droppedPercentage60fps,
            sustained30fpsTarget: p95 <= 33.333
          });
        }
      }
      requestAnimationFrame(loop);
    });
  }, durationMs);
}

async function runDetailedProfiling() {
  const browser = await chromium.launch({
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    headless: true,
    args: [
      "--enable-webgl",
      "--enable-webgl2-compute-context",
      "--ignore-gpu-blocklist",
      "--enable-gpu-rasterization",
      "--force_high_performance_gpu",
      "--disable-background-timer-throttling",
      "--disable-backgrounding-occluded-windows",
      "--disable-renderer-backgrounding"
    ]
  });

  const context = await browser.newContext({ viewport: { width: 1600, height: 1000 } });
  const page = await context.newPage();
  const client = await page.context().newCDPSession(page);
  await client.send("Performance.enable");

  console.log("Navigating to http://localhost:3000 ...");
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(3000);

  const webglInfo = await getWebGLInfo(page);
  console.log("\nBrowser Hardware WebGL Environment:");
  console.log("  Renderer:", webglInfo.unmaskedRenderer || webglInfo.renderer);
  console.log("  Vendor:", webglInfo.unmaskedVendor || webglInfo.vendor);
  console.log("  WebGL Version:", webglInfo.version);
  console.log("  Drawing Buffer:", `${webglInfo.drawingBufferWidth}x${webglInfo.drawingBufferHeight}`);

  const results = {};

  // Workload 1: Baseline Celestial Sphere
  console.log("\n--- Profiling Workload 1: Baseline Celestial Sphere ---");
  const m1_start = await getCDPMetrics(client);
  const perf1 = await measureDetailedFPS(page, 3000);
  const m1_end = await getCDPMetrics(client);
  results["WL1_Baseline"] = {
    ...perf1,
    scriptDurationSec: m1_end.ScriptDuration - m1_start.ScriptDuration,
    layoutDurationSec: m1_end.LayoutDuration - m1_start.LayoutDuration,
    recalcStyleDurationSec: m1_end.RecalcStyleDuration - m1_start.RecalcStyleDuration
  };
  console.log(`  Mean FPS: ${perf1.meanFps.toFixed(1)} | Median: ${perf1.medianFrameTimeMs.toFixed(1)}ms | P95: ${perf1.p95FrameTimeMs.toFixed(1)}ms | P99: ${perf1.p99FrameTimeMs.toFixed(1)}ms`);
  console.log(`  Dropped Frames (>33.3ms): ${perf1.droppedPercentage30fps.toFixed(1)}% | Sustained 30 FPS: ${perf1.sustained30fpsTarget ? "YES" : "NO"}`);

  // Workload 2: Single Astronomical Image Layer
  console.log("\n--- Profiling Workload 2: Single Astronomical Image Layer ---");
  const m2_start = await getCDPMetrics(client);
  const perf2 = await measureDetailedFPS(page, 3000);
  const m2_end = await getCDPMetrics(client);
  results["WL2_SingleLayer"] = {
    ...perf2,
    scriptDurationSec: m2_end.ScriptDuration - m2_start.ScriptDuration,
    layoutDurationSec: m2_end.LayoutDuration - m2_start.LayoutDuration,
    recalcStyleDurationSec: m2_end.RecalcStyleDuration - m2_start.RecalcStyleDuration
  };
  console.log(`  Mean FPS: ${perf2.meanFps.toFixed(1)} | Median: ${perf2.medianFrameTimeMs.toFixed(1)}ms | P95: ${perf2.p95FrameTimeMs.toFixed(1)}ms | P99: ${perf2.p99FrameTimeMs.toFixed(1)}ms`);
  console.log(`  Dropped Frames (>33.3ms): ${perf2.droppedPercentage30fps.toFixed(1)}% | Sustained 30 FPS: ${perf2.sustained30fpsTarget ? "YES" : "NO"}`);

  // Workload 3: Candidate Overlay (trigger Differencing)
  console.log("\n--- Profiling Workload 3: Differencing & Candidate Overlays (416 candidates) ---");
  const diffBtn = page.getByRole("button", { name: /Run Scientific Differencing/i });
  if (await diffBtn.isVisible()) {
    console.log("  Executing Scientific Differencing Pipeline...");
    await diffBtn.click();
    await page.waitForFunction(() => {
      const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent && b.textContent.includes("Run Scientific Differencing"));
      return btn && !btn.disabled && !btn.textContent.includes("Processing");
    }, { timeout: 15000 });
    console.log("  Differencing completed!");
    await page.waitForTimeout(1000);
  }

  const m3_start = await getCDPMetrics(client);
  const perf3 = await measureDetailedFPS(page, 3000);
  const m3_end = await getCDPMetrics(client);
  results["WL3_CandidateOverlay"] = {
    ...perf3,
    scriptDurationSec: m3_end.ScriptDuration - m3_start.ScriptDuration,
    layoutDurationSec: m3_end.LayoutDuration - m3_start.LayoutDuration,
    recalcStyleDurationSec: m3_end.RecalcStyleDuration - m3_start.RecalcStyleDuration
  };
  console.log(`  Mean FPS: ${perf3.meanFps.toFixed(1)} | Median: ${perf3.medianFrameTimeMs.toFixed(1)}ms | P95: ${perf3.p95FrameTimeMs.toFixed(1)}ms | P99: ${perf3.p99FrameTimeMs.toFixed(1)}ms`);
  console.log(`  Dropped Frames (>33.3ms): ${perf3.droppedPercentage30fps.toFixed(1)}% | Sustained 30 FPS: ${perf3.sustained30fpsTarget ? "YES" : "NO"}`);

  // Workload 4: Blink Comparator Active
  console.log("\n--- Profiling Workload 4: Blink Comparator Active (500ms toggle) ---");
  const blinkBtn = page.getByRole("button", { name: /^Blink/i });
  if (await blinkBtn.isVisible()) {
    await blinkBtn.click();
    await page.waitForTimeout(1000);
  }

  const m4_start = await getCDPMetrics(client);
  const perf4 = await measureDetailedFPS(page, 3000);
  const m4_end = await getCDPMetrics(client);
  results["WL4_BlinkComparator"] = {
    ...perf4,
    scriptDurationSec: m4_end.ScriptDuration - m4_start.ScriptDuration,
    layoutDurationSec: m4_end.LayoutDuration - m4_start.LayoutDuration,
    recalcStyleDurationSec: m4_end.RecalcStyleDuration - m4_start.RecalcStyleDuration
  };
  console.log(`  Mean FPS: ${perf4.meanFps.toFixed(1)} | Median: ${perf4.medianFrameTimeMs.toFixed(1)}ms | P95: ${perf4.p95FrameTimeMs.toFixed(1)}ms | P99: ${perf4.p99FrameTimeMs.toFixed(1)}ms`);
  console.log(`  Dropped Frames (>33.3ms): ${perf4.droppedPercentage30fps.toFixed(1)}% | Sustained 30 FPS: ${perf4.sustained30fpsTarget ? "YES" : "NO"}`);

  // Workload 5: Significance Heatmap Display
  console.log("\n--- Profiling Workload 5: Significance S Heatmap Display ---");
  const sigBtn = page.getByRole("button", { name: /Significance S/i });
  if (await sigBtn.isVisible()) {
    await sigBtn.click();
    await page.waitForTimeout(1000);
  }

  const m5_start = await getCDPMetrics(client);
  const perf5 = await measureDetailedFPS(page, 3000);
  const m5_end = await getCDPMetrics(client);
  results["WL5_SignificanceDisplay"] = {
    ...perf5,
    scriptDurationSec: m5_end.ScriptDuration - m5_start.ScriptDuration,
    layoutDurationSec: m5_end.LayoutDuration - m5_start.LayoutDuration,
    recalcStyleDurationSec: m5_end.RecalcStyleDuration - m5_start.RecalcStyleDuration
  };
  console.log(`  Mean FPS: ${perf5.meanFps.toFixed(1)} | Median: ${perf5.medianFrameTimeMs.toFixed(1)}ms | P95: ${perf5.p95FrameTimeMs.toFixed(1)}ms | P99: ${perf5.p99FrameTimeMs.toFixed(1)}ms`);
  console.log(`  Dropped Frames (>33.3ms): ${perf5.droppedPercentage30fps.toFixed(1)}% | Sustained 30 FPS: ${perf5.sustained30fpsTarget ? "YES" : "NO"}`);

  console.log("\n" + "=".repeat(80));
  console.log("COMPLETE PERFORMANCE RESULTS JSON:");
  console.log("=".repeat(80));
  console.log(JSON.stringify({ webglInfo, results }, null, 2));

  await browser.close();
  return { webglInfo, results };
}

runDetailedProfiling().catch(err => {
  console.error("Profiling failure:", err);
  process.exit(1);
});
