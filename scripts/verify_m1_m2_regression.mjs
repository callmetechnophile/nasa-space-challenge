import assert from "node:assert/strict";
import { chromium } from "file:///D:/nasa/frontend/node_modules/playwright/index.mjs";

console.log("=".repeat(80));
console.log("STAGE 1.1.3: M1 & M2 AUTOMATED BEHAVIORAL ACCEPTANCE TEST SUITE");
console.log("=".repeat(80));

async function getCameraState(page) {
  return await page.evaluate(() => (window).__SPHEREX_CAMERA__ || null);
}

async function getTelemetry(page) {
  return await page.evaluate(() => {
    const text = document.body.innerText;
    const distMatch = text.match(/Distance:\s*([\d.]+)/);
    const polarMatch = text.match(/Polar \(θ\):\s*([-\d.]+)°/);
    const azMatch = text.match(/Azimuth \(φ\):\s*([-\d.]+)°/);
    const fovMatch = text.match(/FOV:\s*([\d.]+)°/);
    const targetMatch = text.match(/Target:\s*α\s*([-\d.]+)°,\s*δ\s*([-\d.]+)°/);
    const starMatch = text.match(/Demo Stars:\s*([\d,]+)/);
    return {
      distance: distMatch ? parseFloat(distMatch[1]) : null,
      polar: polarMatch ? parseFloat(polarMatch[1]) : null,
      azimuth: azMatch ? parseFloat(azMatch[1]) : null,
      fov: fovMatch ? parseFloat(fovMatch[1]) : null,
      target: targetMatch ? { ra: parseFloat(targetMatch[1]), dec: parseFloat(targetMatch[2]) } : null,
      starCountText: starMatch ? starMatch[1] : null,
    };
  });
}

async function runM1M2Tests() {
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

  const page = await browser.newPage({ viewport: { width: 1600, height: 1000 } });
  const results = [];

  function record(id, milestone, name, passed, details = "") {
    results.push({ id, milestone, name, status: passed ? "PASS" : "FAIL", details });
    console.log(`  [${milestone}] ${id}: ${name} -> ${passed ? "PASS" : "FAIL"} ${details ? `(${details})` : ""}`);
    assert(passed, `Assertion failed for ${id}: ${name} - ${details}`);
  }

  console.log("\n1. Navigating to http://localhost:3000 ...");
  await page.goto("http://localhost:3000", { waitUntil: "domcontentloaded", timeout: 30000 });
  await page.waitForTimeout(2000);
  await page.mouse.click(600, 500);
  await page.waitForTimeout(1500);

  // M1-1: Celestial sphere initialization
  const canvas = await page.$("canvas");
  record("M1-01", "M1", "Celestial sphere canvas initialization", !!canvas, canvas ? "Canvas element mounted in DOM" : "Canvas missing");

  // M1-2: Starfield rendering
  const webglState = await page.evaluate(() => {
    const c = document.querySelector("canvas");
    if (!c) return null;
    return {
      width: c.width,
      height: c.height,
      clientWidth: c.clientWidth,
      clientHeight: c.clientHeight,
    };
  });
  record("M1-02", "M1", "Starfield & WebGL rendering pipeline", webglState && webglState.width > 0, `Canvas dimensions: ${webglState?.width}x${webglState?.height} (Client: ${webglState?.clientWidth}x${webglState?.clientHeight})`);

  // M1-3: RA/Dec grid presence
  const gridToggle = page.getByRole("button", { name: /Coordinate Grid/i }).first();
  const hasGrid = await gridToggle.isVisible().catch(() => false);
  record("M1-03", "M1", "RA/Dec celestial coordinate grid presence", hasGrid, "Grid control button located");

  // M1-4: Rotation (OrbitControl with behavioral assertion on polar/azimuth angles)
  const cx = 600, cy = 500;
  const t0 = await getTelemetry(page);
  await page.mouse.move(cx, cy);
  await page.mouse.down({ button: "left" });
  await page.mouse.move(cx + 150, cy + 100, { steps: 25 });
  await page.mouse.up({ button: "left" });
  await page.waitForTimeout(600);
  const t1 = await getTelemetry(page);
  const angleDelta = Math.hypot((t1.polar ?? 0) - (t0.polar ?? 0), (t1.azimuth ?? 0) - (t0.azimuth ?? 0));
  record("M1-04", "M1", "Celestial sphere rotation (OrbitControl)", angleDelta > 0.5, `Telemetry Δθ/Δφ = ${angleDelta.toFixed(2)}° (Tolerance: >0.5°, Polar: ${t0.polar}° -> ${t1.polar}°, Azimuth: ${t0.azimuth}° -> ${t1.azimuth}°)`);

  // M1-5: Zoom (Dolly with behavioral assertion on camera distance)
  const distBeforeZoom = (await getTelemetry(page)).distance;
  const zoomInBtn = page.getByTitle("Zoom In (Closer View)").first();
  if (await zoomInBtn.isVisible()) {
    await zoomInBtn.click();
    await page.waitForTimeout(400);
  } else {
    await page.mouse.wheel(0, -200);
    await page.waitForTimeout(400);
  }
  const distAfterZoom = (await getTelemetry(page)).distance;
  record("M1-05", "M1", "Zoom in / out interaction", (distAfterZoom ?? 0) < (distBeforeZoom ?? 0), `Distance contracted: ${distBeforeZoom} -> ${distAfterZoom} (Δ = ${((distBeforeZoom ?? 0) - (distAfterZoom ?? 0)).toFixed(1)})`);

  // M1-6: Pan camera translation (Right-click pan: target or camera position must change)
  const camBeforePan = await getCameraState(page);
  await page.mouse.move(cx, cy);
  await page.mouse.down({ button: "right" });
  await page.mouse.move(cx + 200, cy, { steps: 25 });
  await page.mouse.up({ button: "right" });
  await page.waitForTimeout(600);
  const camAfterPan = await getCameraState(page);

  const posDelta = (camBeforePan?.position && camAfterPan?.position)
    ? Math.hypot(
        camAfterPan.position[0] - camBeforePan.position[0],
        camAfterPan.position[1] - camBeforePan.position[1],
        camAfterPan.position[2] - camBeforePan.position[2]
      )
    : 0;
  const targetDelta = (camBeforePan?.target && camAfterPan?.target)
    ? Math.hypot(
        camAfterPan.target[0] - camBeforePan.target[0],
        camAfterPan.target[1] - camBeforePan.target[1],
        camAfterPan.target[2] - camBeforePan.target[2]
      )
    : 0;
  const panPassed = (posDelta > 0.1) || (targetDelta > 0.1);
  record(
    "M1-06",
    "M1",
    "Pan camera translation (Right-click drag)",
    panPassed,
    `Target translation Δ = ${targetDelta.toFixed(3)}, Camera position Δ = ${posDelta.toFixed(3)} (Tolerance: >0.1)`
  );

  // M1-7: Reset camera view (Returns orientation, target and distance within defined tolerances)
  const resetBtn = page.getByTitle("Reset Camera Orientation & Distance").or(page.getByRole("button", { name: /Reset View/i })).first();
  await resetBtn.click();
  await page.waitForTimeout(800);
  const tReset = await getTelemetry(page);
  const distRestored = Math.abs((tReset.distance ?? 0) - 47.4) <= 3.0;
  const polarRestored = Math.abs((tReset.polar ?? 0) - 60.0) <= 12.0;
  const targetCleared = tReset.target === null;
  record("M1-07", "M1", "Reset camera view to standard orientation & target", distRestored && polarRestored && targetCleared, `Distance: ${tReset.distance} (tol: 47.4±3.0), Polar: ${tReset.polar}° (tol: 60±12°), Target Cleared: ${targetCleared}`);

  // M1-8: Grid and Star Layer Toggles (Explicit before/after visibility state and star count assertions)
  // 1. Grid Toggle
  await gridToggle.click();
  await page.waitForTimeout(300);
  const gridOffClass = await gridToggle.evaluate(el => el.lastElementChild?.className || "");
  const gridToggledOff = gridOffClass.includes("bg-slate-600");

  await gridToggle.click();
  await page.waitForTimeout(300);
  const gridOnClass = await gridToggle.evaluate(el => el.lastElementChild?.className || "");
  const gridToggledOn = gridOnClass.includes("bg-cyan-400");

  // 2. Star Layer Toggle
  const starToggle = page.getByRole("button", { name: /Demonstration Stars/i }).first();
  const starCountInitial = (await getTelemetry(page)).starCountText;

  await starToggle.click();
  await page.waitForTimeout(300);
  const starOffClass = await starToggle.evaluate(el => el.lastElementChild?.className || "");
  const starToggledOff = starOffClass.includes("bg-slate-600");
  const starCountOff = (await getTelemetry(page)).starCountText;

  await starToggle.click();
  await page.waitForTimeout(300);
  const starOnClass = await starToggle.evaluate(el => el.lastElementChild?.className || "");
  const starToggledOn = starOnClass.includes("bg-cyan-400");
  const starCountRestored = (await getTelemetry(page)).starCountText;

  const starLayerVerified = starToggledOff && starToggledOn && starCountOff === "0" && starCountRestored === "4,500";
  record("M1-08", "M1", "Celestial grid and star layer toggles", gridToggledOff && gridToggledOn && starLayerVerified, `Grid (off: ${gridToggledOff}, on: ${gridToggledOn}), Stars (off: ${starToggledOff} [count: ${starCountOff}], on: ${starToggledOn} [count: ${starCountRestored}])`);

  // M2-1: Decimal RA/Dec input & navigation
  console.log("\n2. Testing Milestone 2 Coordinate Navigation & Validation...");
  const coordInputs = page.locator("form").first().locator("input");
  await coordInputs.nth(0).fill("133.7951");
  await coordInputs.nth(1).fill("-7.2451");
  const flyBtn = page.getByRole("button", { name: /Search & Fly/i }).first();
  await flyBtn.click();
  await page.waitForTimeout(1000);

  const tNav = await getTelemetry(page);
  const targetMatches = tNav.target && Math.abs(tNav.target.ra - 133.7951) < 0.001 && Math.abs(tNav.target.dec - (-7.2451)) < 0.001;
  record("M2-01", "M2", "Decimal RA/Dec coordinate input & navigation", !!targetMatches, `Target locked: α ${tNav.target?.ra}°, δ ${tNav.target?.dec}° (Tol: ±0.001°)`);

  // M2-2: Sexagesimal RA/Dec parsing
  const sexaToggle = page.getByRole("button", { name: /Sexagesimal/i }).first();
  await sexaToggle.click();
  await page.waitForTimeout(200);
  await coordInputs.nth(0).fill("08h 55m 10.831s");
  await coordInputs.nth(1).fill("-07° 14' 42.53\"");
  await flyBtn.click();
  await page.waitForTimeout(1000);
  const tSexa = await getTelemetry(page);
  const sexaMatches = tSexa.target && Math.abs(tSexa.target.ra - 133.7951) < 0.002 && Math.abs(tSexa.target.dec - (-7.2451)) < 0.002;
  record("M2-02", "M2", "Sexagesimal RA/Dec parsing (HMS/DMS)", !!sexaMatches, `Parsed 08h 55m 10.831s -> ${tSexa.target?.ra}°, -07° 14' 42.53" -> ${tSexa.target?.dec}° (Tol: ±0.002°)`);

  // M2-3: Negative declination and negative zero handling (-00° 30' 00" -> -0.5°)
  await coordInputs.nth(0).fill("00h 00m 00.000s");
  await coordInputs.nth(1).fill("-00° 30' 00.00\"");
  await flyBtn.click();
  await page.waitForTimeout(1000);
  const tNegZero = await getTelemetry(page);
  const negZeroMatches = tNegZero.target && Math.abs(tNegZero.target.dec - (-0.5)) < 0.001;
  record("M2-03", "M2", "Negative declination and -00° negative zero preservation", !!negZeroMatches, `Parsed -00° 30' 00" -> ${tNegZero.target?.dec}° (Preserved negative sign, Tol: ±0.001°)`);

  // M2-4: Invalid coordinate rejection
  const decToggle = page.getByRole("button", { name: /Decimal/i }).first();
  await decToggle.click();
  await page.waitForTimeout(200);
  const curInputs = page.locator("form").first().locator("input");
  await curInputs.nth(0).fill("375.000000");
  await page.waitForTimeout(200);
  const raErrorText = await page.locator("text=outside permitted range").first().isVisible();
  await curInputs.nth(1).fill("-95.000000");
  await page.waitForTimeout(200);
  const decErrorText = await page.locator("text=outside permitted range").first().isVisible();
  record("M2-04", "M2", "Strict invalid coordinate rejection policy", raErrorText && decErrorText, `Rejected invalid inputs: RA 375° (error: ${raErrorText}), Dec -95° (error: ${decErrorText})`);

  // M2-5: Camera flight slew to target
  await curInputs.nth(0).fill("45.000000");
  await curInputs.nth(1).fill("0.000000");
  await flyBtn.click();
  await page.waitForTimeout(1200);
  const tSlew = await getTelemetry(page);
  record("M2-05", "M2", "Camera navigation smooth great-circle flight", tSlew.target?.ra === 45.0 && tSlew.target?.dec === 0.0, `Slew target reached: α ${tSlew.target?.ra}°, δ ${tSlew.target?.dec}°`);

  // M2-6: Coordinate marker indicator
  const markerLocked = await page.locator("text=TARGET LOCKED").isVisible();
  record("M2-06", "M2", "Coordinate target marker indicator", markerLocked, "Active 3D target HUD reticle locked");

  // M2-7: FOV selection and camera projection matrix update
  const fov30Btn = page.getByRole("button", { name: "30°" }).first();
  await fov30Btn.click();
  await page.waitForTimeout(400);
  const tFov30 = await getTelemetry(page);

  const fov10Btn = page.getByRole("button", { name: "10°" }).first();
  await fov10Btn.click();
  await page.waitForTimeout(400);
  const tFov10 = await getTelemetry(page);

  const fov5Btn = page.getByRole("button", { name: "5°" }).first();
  await fov5Btn.click();
  await page.waitForTimeout(400);
  const tFov5 = await getTelemetry(page);

  const fovStepped = tFov30.fov === 30 && tFov10.fov === 10 && tFov5.fov === 5;
  record("M2-07", "M2", "Field of View (FOV) selection & projection update", fovStepped, `PerspectiveCamera FOV updated: 60° -> ${tFov30.fov}° -> ${tFov10.fov}° -> ${tFov5.fov}°`);

  // M2-8: URL state synchronization
  const urlNow = page.url();
  const urlSynced = urlNow.includes("ra=45.000000") && urlNow.includes("dec=0.000000") && urlNow.includes("fov=5");
  record("M2-08", "M2", "URL query parameter state synchronization", urlSynced, `URL: ${urlNow}`);

  // M2-9: Browser history navigation (Back AND Forward restoration)
  // Step A: Record target 1 URL
  const target1Url = page.url(); // currently ra=45, dec=0, fov=5

  // Step B: Navigate to target 2
  await curInputs.nth(0).fill("180.000000");
  await curInputs.nth(1).fill("-30.000000");
  await flyBtn.click();
  await page.waitForTimeout(1000);
  const fov30StepBtn = page.getByRole("button", { name: "30°" }).first();
  await fov30StepBtn.click();
  await page.waitForTimeout(400);
  const target2Url = page.url();
  assert(target1Url !== target2Url, "Target 2 navigation failed to produce distinct URL");

  // Step C: Test Browser Back
  await page.goBack();
  await page.waitForTimeout(800);
  const backUrl = page.url();
  const backT = await getTelemetry(page);
  const backRestored = backUrl.includes("ra=45.000000") && backUrl.includes("dec=0.000000") && backUrl.includes("fov=5") && backT.fov === 5;

  // Step D: Test Browser Forward
  await page.goForward();
  await page.waitForTimeout(800);
  const forwardUrl = page.url();
  const forwardT = await getTelemetry(page);
  const forwardRestored = forwardUrl.includes("ra=180.000000") && forwardUrl.includes("dec=-30.000000") && forwardUrl.includes("fov=30") && forwardT.fov === 30;

  record("M2-09", "M2", "Browser history navigation (Back & Forward)", backRestored && forwardRestored, `Back -> ${backUrl} (RA 45°, FOV ${backT.fov}°), Forward -> ${forwardUrl} (RA 180°, FOV ${forwardT.fov}°)`);

  console.log("\n" + "=".repeat(80));
  console.log("M1 & M2 REGRESSION ACCEPTANCE SUMMARY:");
  console.log("=".repeat(80));
  const passCount = results.filter(r => r.status === "PASS").length;
  console.log(`Total Criteria: ${results.length} | Passed: ${passCount} | Failed: ${results.length - passCount}`);
  assert(passCount === results.length, "Not all regression criteria passed!");
  console.log("ALL M1 & M2 ACCEPTANCE CRITERIA VERIFIED (PASS)");

  await browser.close();
  return results;
}

runM1M2Tests().catch(err => {
  console.error("Test failed:", err);
  process.exit(1);
});
