import { chromium } from "playwright";

async function dryRun() {
  const browser = await chromium.launch({
    channel: "msedge",
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-webgl"],
  });
  const page = await browser.newPage();
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);

  const tracker = await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");

    window.__tracker = {
      bufIdSeq: 0,
      activeBuffers: new Map(),
      createdBuffers: 0,
      deletedBuffers: 0,
      activeTextures: new Set(),
      createdTextures: 0,
      deletedTextures: 0,
    };

    const origCreateBuf = gl.createBuffer.bind(gl);
    gl.createBuffer = function () {
      const b = origCreateBuf();
      const id = ++window.__tracker.bufIdSeq;
      b.__id = id;
      window.__tracker.activeBuffers.set(id, { id, time: Date.now() });
      window.__tracker.createdBuffers++;
      return b;
    };

    const origDeleteBuf = gl.deleteBuffer.bind(gl);
    gl.deleteBuffer = function (b) {
      if (b && b.__id) {
        window.__tracker.activeBuffers.delete(b.__id);
      }
      window.__tracker.deletedBuffers++;
      return origDeleteBuf(b);
    };

    const origCreateTex = gl.createTexture.bind(gl);
    gl.createTexture = function () {
      const t = origCreateTex();
      window.__tracker.activeTextures.add(t);
      window.__tracker.createdTextures++;
      return t;
    };

    const origDeleteTex = gl.deleteTexture.bind(gl);
    gl.deleteTexture = function (t) {
      window.__tracker.activeTextures.delete(t);
      window.__tracker.deletedTextures++;
      return origDeleteTex(t);
    };

    return {
      activeBuf: window.__tracker.activeBuffers.size,
      activeTex: window.__tracker.activeTextures.size,
    };
  });

  console.log("Initial baseline active buffers:", tracker.activeBuf, "active textures:", tracker.activeTex);

  const sampleSelect = page.locator("select").first();
  await sampleSelect.selectOption("wise-0855");

  for (let c = 1; c <= 3; c++) {
    // Load
    const loadBtn = page.locator("button:has-text('Load')").first();
    await loadBtn.click();

    const removeBtn = page.locator("button[title='Remove Image Layer']").first();
    await removeBtn.waitFor({ state: "visible", timeout: 8000 });
    await page.waitForTimeout(400);

    const loadedMetrics = await page.evaluate(() => ({
      activeBuf: window.__tracker.activeBuffers.size,
      createdBuf: window.__tracker.createdBuffers,
      deletedBuf: window.__tracker.deletedBuffers,
      activeTex: window.__tracker.activeTextures.size,
    }));
    console.log(`[Cycle ${c} - LOADED] Active Buf: ${loadedMetrics.activeBuf} (Created: ${loadedMetrics.createdBuf}, Deleted: ${loadedMetrics.deletedBuf}) | Active Tex: ${loadedMetrics.activeTex}`);

    // Remove
    await removeBtn.click();
    await removeBtn.waitFor({ state: "hidden", timeout: 8000 });
    await page.waitForTimeout(600);

    const unloadedMetrics = await page.evaluate(() => ({
      activeBuf: window.__tracker.activeBuffers.size,
      createdBuf: window.__tracker.createdBuffers,
      deletedBuf: window.__tracker.deletedBuffers,
      activeTex: window.__tracker.activeTextures.size,
    }));
    console.log(`[Cycle ${c} - UNLOADED] Active Buf: ${unloadedMetrics.activeBuf} (Created: ${unloadedMetrics.createdBuf}, Deleted: ${unloadedMetrics.deletedBuf}) | Active Tex: ${unloadedMetrics.activeTex}`);
  }

  await browser.close();
}

dryRun().catch(console.error);
