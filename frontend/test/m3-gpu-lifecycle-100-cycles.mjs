import { chromium } from "playwright";
import fs from "fs";
import path from "path";

async function runGpuLifecycleAudit() {
  console.log("==========================================================================");
  console.log("  SPHEREx M3 — Comprehensive GPU Resource Lifecycle Audit (100 Cycles)   ");
  console.log("==========================================================================\n");

  const browser = await chromium.launch({
    channel: "msedge",
    headless: true,
    args: [
      "--use-gl=angle",
      "--use-angle=swiftshader",
      "--enable-webgl",
      "--ignore-gpu-blocklist",
      "--js-flags=--expose-gc",
    ],
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });

  const page = await context.newPage();

  console.log("Navigating to http://localhost:3000 and settling baseline scene...");
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(4000); // Allow all background targets & celestial spheres to render

  const sampleSelect = page.locator("select").first();
  await sampleSelect.selectOption("wise-0855");

  // 1 Warmup cycle to ensure first-render shader compilation and UI caches are initialized
  const loadBtn = page.locator("button:has-text('Load')").first();
  await loadBtn.click();
  const removeBtn = page.locator("button[title='Remove Image Layer']").first();
  await removeBtn.waitFor({ state: "visible", timeout: 8000 });
  await page.waitForTimeout(600);
  await removeBtn.click();
  await removeBtn.waitFor({ state: "hidden", timeout: 8000 });
  await page.waitForTimeout(800);

  // Inject strict WebGL resource lifecycle tracking
  const baselineInfo = await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    if (!canvas) throw new Error("Canvas element not found");
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");
    if (!gl) throw new Error("WebGL context not found");

    window.__gpuTracker = {
      bufferIdSeq: 0,
      textureIdSeq: 0,
      activeBuffers: new Map(),
      activeTextures: new Map(),
      totalBuffersCreated: 0,
      totalBuffersDeleted: 0,
      totalTexturesCreated: 0,
      totalTexturesDeleted: 0,
      imageLayerBuffersCreated: 0,
      imageLayerBuffersDeleted: 0,
      imageLayerTexturesCreated: 0,
      imageLayerTexturesDeleted: 0,
      contextLossCount: 0,
      isImageLayerActive: false,
    };

    canvas.addEventListener("webglcontextlost", () => {
      window.__gpuTracker.contextLossCount++;
    });

    const origCreateBuf = gl.createBuffer.bind(gl);
    gl.createBuffer = function () {
      const b = origCreateBuf();
      const id = ++window.__gpuTracker.bufferIdSeq;
      b.__bufId = id;
      b.__isImageLayer = window.__gpuTracker.isImageLayerActive;
      window.__gpuTracker.totalBuffersCreated++;
      if (b.__isImageLayer) {
        window.__gpuTracker.imageLayerBuffersCreated++;
      }
      window.__gpuTracker.activeBuffers.set(id, {
        id,
        isImageLayer: b.__isImageLayer,
        createdAt: Date.now(),
      });
      return b;
    };

    const origDeleteBuf = gl.deleteBuffer.bind(gl);
    gl.deleteBuffer = function (b) {
      if (b && b.__bufId) {
        window.__gpuTracker.activeBuffers.delete(b.__bufId);
        if (b.__isImageLayer) {
          window.__gpuTracker.imageLayerBuffersDeleted++;
        }
      }
      window.__gpuTracker.totalBuffersDeleted++;
      return origDeleteBuf(b);
    };

    const origCreateTex = gl.createTexture.bind(gl);
    gl.createTexture = function () {
      const t = origCreateTex();
      const id = ++window.__gpuTracker.textureIdSeq;
      t.__texId = id;
      t.__isImageLayer = window.__gpuTracker.isImageLayerActive;
      window.__gpuTracker.totalTexturesCreated++;
      if (t.__isImageLayer) {
        window.__gpuTracker.imageLayerTexturesCreated++;
      }
      window.__gpuTracker.activeTextures.set(id, {
        id,
        isImageLayer: t.__isImageLayer,
        createdAt: Date.now(),
      });
      return t;
    };

    const origDeleteTex = gl.deleteTexture.bind(gl);
    gl.deleteTexture = function (t) {
      if (t && t.__texId) {
        window.__gpuTracker.activeTextures.delete(t.__texId);
        if (t.__isImageLayer) {
          window.__gpuTracker.imageLayerTexturesDeleted++;
        }
      }
      window.__gpuTracker.totalTexturesDeleted++;
      return origDeleteTex(t);
    };

    const mem = (performance && performance.memory) ? {
      usedJSHeapMB: Math.round(performance.memory.usedJSHeapSize / (1024 * 1024)),
      totalJSHeapMB: Math.round(performance.memory.totalJSHeapSize / (1024 * 1024)),
    } : null;

    return {
      activeBuffers: window.__gpuTracker.activeBuffers.size,
      activeTextures: window.__gpuTracker.activeTextures.size,
      mem,
    };
  });

  console.log(`Baseline Persistent Resources Recorded:`);
  console.log(`  - Baseline Active Buffers:  ${baselineInfo.activeBuffers}`);
  console.log(`  - Baseline Active Textures: ${baselineInfo.activeTextures}`);
  if (baselineInfo.mem) {
    console.log(`  - Baseline JS Heap:         ${baselineInfo.mem.usedJSHeapMB} MB used / ${baselineInfo.mem.totalJSHeapMB} MB total\n`);
  }

  const TOTAL_CYCLES = 100;
  const cycleSnapshots = [];
  const startTime = Date.now();

  console.log(`Executing ${TOTAL_CYCLES} sequential Load / Unload cycles...\n`);

  for (let cycle = 1; cycle <= TOTAL_CYCLES; cycle++) {
    // Flag image layer loading active
    await page.evaluate(() => { window.__gpuTracker.isImageLayerActive = true; });

    // 1. Click Load
    await loadBtn.click();
    await removeBtn.waitFor({ state: "visible", timeout: 8000 });
    await page.waitForTimeout(300);

    // End image layer load phase
    await page.evaluate(() => { window.__gpuTracker.isImageLayerActive = false; });

    // 2. Click Remove
    await removeBtn.click();
    await removeBtn.waitFor({ state: "hidden", timeout: 8000 });
    await page.waitForTimeout(350);

    // Snapshot state every 20 cycles or at end
    if (cycle % 20 === 0 || cycle === TOTAL_CYCLES) {
      const snap = await page.evaluate((c) => {
        let activeImageBufs = 0;
        let activeImageTexs = 0;
        for (const [id, info] of window.__gpuTracker.activeBuffers) {
          if (info.isImageLayer) activeImageBufs++;
        }
        for (const [id, info] of window.__gpuTracker.activeTextures) {
          if (info.isImageLayer) activeImageTexs++;
        }

        const mem = (performance && performance.memory) ? {
          usedJSHeapMB: Math.round(performance.memory.usedJSHeapSize / (1024 * 1024)),
          totalJSHeapMB: Math.round(performance.memory.totalJSHeapSize / (1024 * 1024)),
        } : null;

        return {
          cycle: c,
          totalBuffersCreated: window.__gpuTracker.totalBuffersCreated,
          totalBuffersDeleted: window.__gpuTracker.totalBuffersDeleted,
          activeBuffers: window.__gpuTracker.activeBuffers.size,
          activeImageBuffers: activeImageBufs,
          totalTexturesCreated: window.__gpuTracker.totalTexturesCreated,
          totalTexturesDeleted: window.__gpuTracker.totalTexturesDeleted,
          activeTextures: window.__gpuTracker.activeTextures.size,
          activeImageTextures: activeImageTexs,
          contextLossCount: window.__gpuTracker.contextLossCount,
          mem,
        };
      }, cycle);

      const elapsed = ((Date.now() - startTime) / 1000).toFixed(1);
      snap.elapsedSec = elapsed;
      cycleSnapshots.push(snap);

      console.log(
        `[Cycle ${cycle.toString().padStart(3)}/100] ` +
        `Active Buf: ${snap.activeBuffers} (ImgBufs: ${snap.activeImageBuffers}) | ` +
        `Active Tex: ${snap.activeTextures} (ImgTexs: ${snap.activeImageTextures}) | ` +
        `Context Loss: ${snap.contextLossCount} | ` +
        (snap.mem ? `Heap: ${snap.mem.usedJSHeapMB} MB | ` : "") +
        `Elapsed: ${elapsed}s`
      );
    }
  }

  // Final detailed analysis
  const finalReport = await page.evaluate(() => {
    let activeImageBufs = 0;
    let activeImageTexs = 0;
    const remainingBufDetails = [];
    for (const [id, info] of window.__gpuTracker.activeBuffers) {
      if (info.isImageLayer) {
        activeImageBufs++;
        remainingBufDetails.push(info);
      }
    }
    for (const [id, info] of window.__gpuTracker.activeTextures) {
      if (info.isImageLayer) activeImageTexs++;
    }

    const mem = (performance && performance.memory) ? {
      usedJSHeapMB: Math.round(performance.memory.usedJSHeapSize / (1024 * 1024)),
      totalJSHeapMB: Math.round(performance.memory.totalJSHeapSize / (1024 * 1024)),
    } : null;

    return {
      totalBuffersCreated: window.__gpuTracker.totalBuffersCreated,
      totalBuffersDeleted: window.__gpuTracker.totalBuffersDeleted,
      netActiveBuffers: window.__gpuTracker.activeBuffers.size,
      imageLayerBuffersCreated: window.__gpuTracker.imageLayerBuffersCreated,
      imageLayerBuffersDeleted: window.__gpuTracker.imageLayerBuffersDeleted,
      netActiveImageBuffers: activeImageBufs,
      totalTexturesCreated: window.__gpuTracker.totalTexturesCreated,
      totalTexturesDeleted: window.__gpuTracker.totalTexturesDeleted,
      netActiveTextures: window.__gpuTracker.activeTextures.size,
      imageLayerTexturesCreated: window.__gpuTracker.imageLayerTexturesCreated,
      imageLayerTexturesDeleted: window.__gpuTracker.imageLayerTexturesDeleted,
      netActiveImageTextures: activeImageTexs,
      contextLossCount: window.__gpuTracker.contextLossCount,
      remainingBufDetails,
      mem,
    };
  });

  await browser.close();

  console.log("\n==========================================================================");
  console.log("  SPHEREx M3 — GPU Lifecycle 100-Cycle Audit Final Results                ");
  console.log("==========================================================================");
  console.log(`Image-Layer Buffers Created:    ${finalReport.imageLayerBuffersCreated}`);
  console.log(`Image-Layer Buffers Deleted:    ${finalReport.imageLayerBuffersDeleted}`);
  console.log(`Net Active Image-Layer Buffers: ${finalReport.netActiveImageBuffers} (Target: 0)`);
  console.log(`Image-Layer Textures Created:   ${finalReport.imageLayerTexturesCreated}`);
  console.log(`Image-Layer Textures Deleted:   ${finalReport.imageLayerTexturesDeleted}`);
  console.log(`Net Active Image Textures:      ${finalReport.netActiveImageTextures} (Target: 0)`);
  console.log(`Persistent Baseline Buffers:    ${finalReport.netActiveBuffers - finalReport.netActiveImageBuffers}`);
  console.log(`Total WebGL Context Losses:     ${finalReport.contextLossCount} (Target: 0)`);
  if (finalReport.mem) {
    console.log(`Final JavaScript Heap:          ${finalReport.mem.usedJSHeapMB} MB`);
  }
  console.log("==========================================================================\n");

  const telemetryPath = path.resolve("data/fits/m3_gpu_lifecycle_100_cycles_telemetry.json");
  fs.writeFileSync(telemetryPath, JSON.stringify({
    baselineInfo,
    snapshots: cycleSnapshots,
    finalReport,
  }, null, 2));
  console.log(`Telemetry successfully written to: ${telemetryPath}`);

  return { baselineInfo, cycleSnapshots, finalReport };
}

runGpuLifecycleAudit().catch(console.error);
