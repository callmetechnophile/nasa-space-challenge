import { chromium } from "playwright";

async function test10Cycles() {
  const browser = await chromium.launch({
    channel: "msedge",
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-webgl"],
  });
  const page = await browser.newPage();
  await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
  await page.waitForTimeout(5000); // Wait for API calls & targets to settle

  // 1 warmup load/unload cycle before recording baseline
  const sampleSelect = page.locator("select").first();
  await sampleSelect.selectOption("wise-0855");

  const loadBtn = page.locator("button:has-text('Load')").first();
  await loadBtn.click();
  const removeBtn = page.locator("button[title='Remove Image Layer']").first();
  await removeBtn.waitFor({ state: "visible", timeout: 8000 });
  await page.waitForTimeout(500);
  await removeBtn.click();
  await removeBtn.waitFor({ state: "hidden", timeout: 8000 });
  await page.waitForTimeout(500);

  // Now attach GPU instrumentation
  await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");

    window.__tracker = {
      bufCreated: 0,
      bufDeleted: 0,
      texCreated: 0,
      texDeleted: 0,
      activeBufs: new Set(),
      activeTexs: new Set(),
    };

    const origCreateBuf = gl.createBuffer.bind(gl);
    gl.createBuffer = function () {
      const b = origCreateBuf();
      window.__tracker.bufCreated++;
      window.__tracker.activeBufs.add(b);
      return b;
    };

    const origDeleteBuf = gl.deleteBuffer.bind(gl);
    gl.deleteBuffer = function (b) {
      window.__tracker.bufDeleted++;
      window.__tracker.activeBufs.delete(b);
      return origDeleteBuf(b);
    };

    const origCreateTex = gl.createTexture.bind(gl);
    gl.createTexture = function () {
      const t = origCreateTex();
      window.__tracker.texCreated++;
      window.__tracker.activeTexs.add(t);
      return t;
    };

    const origDeleteTex = gl.deleteTexture.bind(gl);
    gl.deleteTexture = function (t) {
      window.__tracker.texDeleted++;
      window.__tracker.activeTexs.delete(t);
      return origDeleteTex(t);
    };
  });

  console.log("Starting 10 sequential load/unload cycles after baseline warmup...");

  for (let c = 1; c <= 10; c++) {
    // 1. Load
    await loadBtn.click();
    await removeBtn.waitFor({ state: "visible", timeout: 8000 });
    await page.waitForTimeout(400);

    const loaded = await page.evaluate(() => ({
      activeBuf: window.__tracker.activeBufs.size,
      createdBuf: window.__tracker.bufCreated,
      deletedBuf: window.__tracker.bufDeleted,
      activeTex: window.__tracker.activeTexs.size,
    }));

    // 2. Remove
    await removeBtn.click();
    await removeBtn.waitFor({ state: "hidden", timeout: 8000 });
    await page.waitForTimeout(400);

    const unloaded = await page.evaluate(() => ({
      activeBuf: window.__tracker.activeBufs.size,
      createdBuf: window.__tracker.bufCreated,
      deletedBuf: window.__tracker.bufDeleted,
      activeTex: window.__tracker.activeTexs.size,
    }));

    console.log(`[Cycle ${c.toString().padStart(2)}] LOADED: activeBuf=${loaded.activeBuf} (created=${loaded.createdBuf}, deleted=${loaded.deletedBuf}) | UNLOADED: activeBuf=${unloaded.activeBuf} (deleted=${unloaded.deletedBuf}) | Active Tex: ${unloaded.activeTex}`);
  }

  await browser.close();
}

test10Cycles().catch(console.error);
