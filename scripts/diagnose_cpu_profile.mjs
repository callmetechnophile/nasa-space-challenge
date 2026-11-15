import { chromium } from "file:///D:/nasa/frontend/node_modules/playwright/index.mjs";

async function profileCPU() {
  const browser = await chromium.launch({
    executablePath: "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
    headless: true,
    args: ["--enable-webgl", "--enable-webgl2-compute-context", "--ignore-gpu-blocklist"]
  });

  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const client = await page.context().newCDPSession(page);

  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(3000);

  const diffBtn = page.getByRole("button", { name: /Run Scientific Differencing/i });
  if (await diffBtn.isVisible()) {
    console.log("Triggering Scientific Differencing...");
    await diffBtn.click();
    await page.waitForFunction(() => {
      const btn = Array.from(document.querySelectorAll("button")).find(b => b.textContent && b.textContent.includes("Run Scientific Differencing"));
      return btn && !btn.disabled && !btn.textContent.includes("Processing");
    }, { timeout: 15000 });
    console.log("Differencing finished!");
  }

  // Start CDP Profiler
  await client.send("Profiler.enable");
  await client.send("Profiler.start");
  console.log("Profiling CPU for 3 seconds...");
  await page.waitForTimeout(3000);
  const { profile } = await client.send("Profiler.stop");

  // Aggregate top functions by hitCount / time
  const nodeMap = new Map();
  for (const node of profile.nodes) {
    nodeMap.set(node.id, node);
  }

  const fnHits = new Map();
  for (const sample of profile.samples) {
    const node = nodeMap.get(sample);
    if (!node) continue;
    const callFrame = node.callFrame;
    const name = `${callFrame.functionName || '(anonymous)'} @ ${callFrame.url.split('/').pop()}:${callFrame.lineNumber}`;
    fnHits.set(name, (fnHits.get(name) || 0) + 1);
  }

  const sorted = Array.from(fnHits.entries()).sort((a, b) => b[1] - a[1]);
  console.log("\n--- Top 20 CPU Functions by Sample Count ---");
  for (let i = 0; i < Math.min(20, sorted.length); i++) {
    const [name, count] = sorted[i];
    const pct = ((count / profile.samples.length) * 100).toFixed(1);
    console.log(`  ${pct.padStart(5)}% (${count.toString().padStart(4)} samples): ${name}`);
  }

  await browser.close();
}

profileCPU().catch(console.error);
