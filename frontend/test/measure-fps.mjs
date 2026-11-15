import { chromium } from "playwright";

async function main() {
  const browser = await chromium.launch({
    channel: "msedge",
    headless: true,
    args: ["--use-gl=angle", "--use-angle=swiftshader"],
  });

  const context = await browser.newContext({
    viewport: { width: 1500, height: 950 },
  });
  const page = await context.newPage();

  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded" });
  await page.waitForTimeout(3000);

  // Measure delta times while dragging orbit controls across canvas
  const canvas = page.locator("canvas").first();
  const box = await canvas.boundingBox();

  const fps = await page.evaluate(async () => {
    return new Promise((resolve) => {
      const deltas = [];
      let last = performance.now();
      let frames = 0;

      function step(now) {
        const dt = now - last;
        last = now;
        if (dt > 0) deltas.push(1000 / dt);
        frames++;
        if (frames < 60) {
          requestAnimationFrame(step);
        } else {
          deltas.sort((a, b) => a - b);
          resolve({
            count: deltas.length,
            min: deltas[0],
            median: deltas[Math.floor(deltas.length / 2)],
            mean: deltas.reduce((a, b) => a + b, 0) / deltas.length,
            max: deltas[deltas.length - 1],
          });
        }
      }
      requestAnimationFrame(step);
    });
  });

  console.log("Measured Frame Rate:");
  console.log(`  Count: ${fps.count}`);
  console.log(`  Median: ${fps.median.toFixed(1)} FPS`);
  console.log(`  Mean:   ${fps.mean.toFixed(1)} FPS`);
  console.log(`  Min:    ${fps.min.toFixed(1)} FPS`);
  console.log(`  Max:    ${fps.max.toFixed(1)} FPS`);

  await browser.close();
}

main().catch(console.error);
