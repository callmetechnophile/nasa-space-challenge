import { chromium } from "playwright";

async function traceBuffers() {
  const browser = await chromium.launch({
    channel: "msedge",
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader", "--enable-webgl"],
  });
  const page = await browser.newPage();
  await page.goto("http://localhost:3000", { waitUntil: "networkidle" });
  await page.waitForTimeout(4000); // Wait for initial scene to settle

  await page.evaluate(() => {
    const canvas = document.querySelector("canvas");
    const gl = canvas.getContext("webgl2") || canvas.getContext("webgl");

    window.__events = [];
    window.__buffers = new Map();
    let nextId = 1;

    const origCreateBuf = gl.createBuffer.bind(gl);
    gl.createBuffer = function () {
      const b = origCreateBuf();
      b.__id = nextId++;
      const stack = new Error().stack.split("\n").slice(2, 6).map(s => s.trim()).join(" -> ");
      window.__buffers.set(b.__id, { id: b.__id, stack, bytes: 0, target: null, type: "unknown" });
      window.__events.push({ type: "create", id: b.__id, stack });
      return b;
    };

    const origBindBuf = gl.bindBuffer.bind(gl);
    gl.bindBuffer = function (target, b) {
      if (b && b.__id) {
        const info = window.__buffers.get(b.__id);
        if (info) info.target = target;
      }
      return origBindBuf(target, b);
    };

    const origBufData = gl.bufferData.bind(gl);
    gl.bufferData = function (target, dataOrSize, usage) {
      // Find currently bound buffer or target
      const res = origBufData(target, dataOrSize, usage);
      const byteLen = typeof dataOrSize === "number" ? dataOrSize : (dataOrSize ? dataOrSize.byteLength : 0);
      window.__events.push({ type: "bufferData", target, byteLen, usage });
      return res;
    };

    const origDeleteBuf = gl.deleteBuffer.bind(gl);
    gl.deleteBuffer = function (b) {
      if (b && b.__id) {
        const info = window.__buffers.get(b.__id);
        window.__events.push({ type: "delete", id: b.__id, info });
        window.__buffers.delete(b.__id);
      }
      return origDeleteBuf(b);
    };
  });

  console.log("Ready to record events for 1 load/unload cycle");
  const sampleSelect = page.locator("select").first();
  await sampleSelect.selectOption("wise-0855");

  // Load
  const loadBtn = page.locator("button:has-text('Load')").first();
  await loadBtn.click();

  const removeBtn = page.locator("button[title='Remove Image Layer']").first();
  await removeBtn.waitFor({ state: "visible", timeout: 8000 });
  await page.waitForTimeout(1000);

  // Snapshot after load
  const afterLoad = await page.evaluate(() => {
    return {
      events: window.__events.splice(0),
      activeCount: window.__buffers.size,
    };
  });
  console.log(`\n=== AFTER LOAD (Events: ${afterLoad.events.length}, Active: ${afterLoad.activeCount}) ===`);
  for (const e of afterLoad.events) {
    if (e.type === "create") {
      console.log(`  CREATE [${e.id}]: ${e.stack}`);
    } else if (e.type === "delete") {
      console.log(`  DELETE [${e.id}]`);
    } else {
      console.log(`  DATA: target=${e.target}, bytes=${e.byteLen}`);
    }
  }

  // Remove
  await removeBtn.click();
  await removeBtn.waitFor({ state: "hidden", timeout: 8000 });
  await page.waitForTimeout(1000);

  // Snapshot after remove
  const afterRemove = await page.evaluate(() => {
    return {
      events: window.__events.splice(0),
      activeCount: window.__buffers.size,
      remainingBuffers: Array.from(window.__buffers.values()),
    };
  });
  console.log(`\n=== AFTER REMOVE (Events: ${afterRemove.events.length}, Active: ${afterRemove.activeCount}) ===`);
  for (const e of afterRemove.events) {
    if (e.type === "create") {
      console.log(`  CREATE [${e.id}]: ${e.stack}`);
    } else if (e.type === "delete") {
      console.log(`  DELETE [${e.id}]`);
    }
  }
  if (afterRemove.remainingBuffers.length > 0) {
    console.log("\nREMAINING BUFFERS NOT DELETED:");
    for (const b of afterRemove.remainingBuffers) {
      console.log(`  Remaining Buffer [${b.id}]: ${b.stack}`);
    }
  }

  await browser.close();
}

traceBuffers().catch(console.error);
