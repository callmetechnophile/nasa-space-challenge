import { chromium } from "file:///D:/nasa/frontend/node_modules/playwright/index.mjs";

console.log("=" .repeat(80));
console.log("TASK 3: IN-DEPTH BROWSER PERFORMANCE PROFILING ACROSS WORKLOADS");
console.log("=" .repeat(80));

async function getCDPMetrics(client) {
  const { metrics } = await client.send("Performance.getMetrics");
  const result = {};
  for (const m of metrics) {
    result[m.name] = m.value;
  }
  return result;
}

async function countDOMNodes(page) {
  return await page.evaluate(() => {
    const totalNodes = document.querySelectorAll("*").length;
    const svgCount = document.querySelectorAll("svg").length;
    const pingCount = document.querySelectorAll(".animate-ping").length;
    const canvasCount = document.querySelectorAll("canvas").length;
    const imgCount = document.querySelectorAll("img").length;
    return { totalNodes, svgCount, pingCount, canvasCount, imgCount };
  });
}

async function measureFPS(page, durationMs = 3000) {
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
          // Sort frame durations for percentiles
          frameDurs.sort((a, b) => a - b);
          const median = frameDurs[Math.floor(frameDurs.length / 2)];
          const p95 = frameDurs[Math.floor(frameDurs.length * 0.95)];
          const min = frameDurs[0];
          const max = frameDurs[frameDurs.length - 1];
          resolve({
            frames,
            totalTime,
            fps,
            medianDeltaMs: median,
            p95DeltaMs: p95,
            minDeltaMs: min,
            maxDeltaMs: max
          });
        }
      }
      requestAnimationFrame(loop);
    });
  }, durationMs);
}

async function runProfile() {
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

  const results = {};

  // Workload 1: Baseline Celestial Sphere
  console.log("\n--- Profiling Workload 1: Baseline Celestial Sphere ---");
  const m1_start = await getCDPMetrics(client);
  const dom1 = await countDOMNodes(page);
  const fps1 = await measureFPS(page, 3000);
  const m1_end = await getCDPMetrics(client);
  results["1_baseline"] = { dom: dom1, fps: fps1, scriptDur: m1_end.ScriptDuration - m1_start.ScriptDuration, layoutDur: m1_end.LayoutDuration - m1_start.LayoutDuration, recalcDur: m1_end.RecalcStyleDuration - m1_start.RecalcStyleDuration };
  console.log(`  FPS: ${fps1.fps.toFixed(1)} (median: ${fps1.medianDeltaMs.toFixed(1)}ms, p95: ${fps1.p95DeltaMs.toFixed(1)}ms) | Nodes: ${dom1.totalNodes} (SVGs: ${dom1.svgCount})`);

  // Workload 2: Single Astronomical Image Layer
  console.log("\n--- Profiling Workload 2: Single Astronomical Image Layer ---");
  const m2_start = await getCDPMetrics(client);
  const dom2 = await countDOMNodes(page);
  const fps2 = await measureFPS(page, 3000);
  const m2_end = await getCDPMetrics(client);
  results["2_single_layer"] = { dom: dom2, fps: fps2, scriptDur: m2_end.ScriptDuration - m2_start.ScriptDuration, layoutDur: m2_end.LayoutDuration - m2_start.LayoutDuration, recalcDur: m2_end.RecalcStyleDuration - m2_start.RecalcStyleDuration };
  console.log(`  FPS: ${fps2.fps.toFixed(1)} (median: ${fps2.medianDeltaMs.toFixed(1)}ms, p95: ${fps2.p95DeltaMs.toFixed(1)}ms) | Nodes: ${dom2.totalNodes}`);

  // Workload 3: Candidate Overlay (trigger Differencing)
  console.log("\n--- Profiling Workload 3: Differencing & Candidate Overlays ---");
  const diffBtn = page.getByRole("button", { name: /Run Scientific Differencing/i });
  if (await diffBtn.isVisible()) {
    console.log("  Clicking 'Run Scientific Differencing'...");
    await diffBtn.click();
    // Wait for the button to return to non-loading state
    await page.waitForFunction(() => {
      const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent && b.textContent.includes("Run Scientific Differencing"));
      return btn && !btn.disabled && !btn.textContent.includes("Processing");
    }, { timeout: 15000 });
    console.log("  Differencing completed on backend!");
  }

  const m3_start = await getCDPMetrics(client);
  const dom3 = await countDOMNodes(page);
  const fps3 = await measureFPS(page, 3000);
  const m3_end = await getCDPMetrics(client);
  results["3_candidate_overlay"] = { dom: dom3, fps: fps3, scriptDur: m3_end.ScriptDuration - m3_start.ScriptDuration, layoutDur: m3_end.LayoutDuration - m3_start.LayoutDuration, recalcDur: m3_end.RecalcStyleDuration - m3_start.RecalcStyleDuration };
  console.log(`  FPS: ${fps3.fps.toFixed(1)} (median: ${fps3.medianDeltaMs.toFixed(1)}ms, p95: ${fps3.p95DeltaMs.toFixed(1)}ms) | Nodes: ${dom3.totalNodes} (Ping markers: ${dom3.pingCount})`);

  // Workload 4: Blink Comparator
  console.log("\n--- Profiling Workload 4: Blink Comparator Active ---");
  const blinkBtn = page.getByRole("button", { name: /^Blink/i });
  if (await blinkBtn.isVisible()) {
    console.log("  Activating Blink Mode...");
    await blinkBtn.click();
    await page.waitForTimeout(1000);
  }

  const m4_start = await getCDPMetrics(client);
  const dom4 = await countDOMNodes(page);
  const fps4 = await measureFPS(page, 3000);
  const m4_end = await getCDPMetrics(client);
  results["4_blink_comparator"] = { dom: dom4, fps: fps4, scriptDur: m4_end.ScriptDuration - m4_start.ScriptDuration, layoutDur: m4_end.LayoutDuration - m4_start.LayoutDuration, recalcDur: m4_end.RecalcStyleDuration - m4_start.RecalcStyleDuration };
  console.log(`  FPS: ${fps4.fps.toFixed(1)} (median: ${fps4.medianDeltaMs.toFixed(1)}ms, p95: ${fps4.p95DeltaMs.toFixed(1)}ms) | Nodes: ${dom4.totalNodes}`);

  // Workload 5: Difference and Significance Display
  console.log("\n--- Profiling Workload 5: Significance S Heatmap Display ---");
  const sigBtn = page.getByRole("button", { name: /Significance S/i });
  if (await sigBtn.isVisible()) {
    console.log("  Switching to Significance S Display...");
    await sigBtn.click();
    await page.waitForTimeout(1000);
  }

  const m5_start = await getCDPMetrics(client);
  const dom5 = await countDOMNodes(page);
  const fps5 = await measureFPS(page, 3000);
  const m5_end = await getCDPMetrics(client);
  results["5_significance_display"] = { dom: dom5, fps: fps5, scriptDur: m5_end.ScriptDuration - m5_start.ScriptDuration, layoutDur: m5_end.LayoutDuration - m5_start.LayoutDuration, recalcDur: m5_end.RecalcStyleDuration - m5_start.RecalcStyleDuration };
  console.log(`  FPS: ${fps5.fps.toFixed(1)} (median: ${fps5.medianDeltaMs.toFixed(1)}ms, p95: ${fps5.p95DeltaMs.toFixed(1)}ms) | Nodes: ${dom5.totalNodes}`);

  console.log("\n" + "=" .repeat(80));
  console.log("PROFILING SUMMARY TABLE:");
  console.log("=" .repeat(80));
  console.log(JSON.stringify(results, null, 2));

  await browser.close();
}

runProfile().catch(err => {
  console.error("Profiling error:", err);
  process.exit(1);
});
