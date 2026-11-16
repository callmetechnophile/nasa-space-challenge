const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  const artifactDir = 'C:/Users/worka/.gemini/antigravity/brain/4caccf68-379b-4aca-b442-5eeb4701650e';
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';

  console.log('Launching browser for SkyTrace Local Frontend-Backend Connection Verification...');
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 },
    deviceScaleFactor: 1,
  });
  const page = await context.newPage();

  const networkLog = [];
  const consoleMessages = [];
  const errors = [];

  page.on('console', msg => {
    consoleMessages.push({ type: msg.type(), text: msg.text() });
    if (msg.type() === 'error') {
      console.error(`[Browser Console ERROR] ${msg.text()}`);
    }
  });

  page.on('pageerror', err => {
    errors.push(err.toString());
    console.error(`[Browser PageError] ${err}`);
  });

  page.on('request', req => {
    if (req.url().includes(':8000') || req.url().includes('/api/')) {
      networkLog.push({
        type: 'request',
        url: req.url(),
        method: req.method(),
        postData: req.postData(),
        time: Date.now()
      });
    }
  });

  page.on('response', async res => {
    if (res.url().includes(':8000') || res.url().includes('/api/')) {
      let bodyPreview = '';
      try {
        const text = await res.text();
        bodyPreview = text.slice(0, 150);
      } catch (e) {
        bodyPreview = '[binary/consumed]';
      }
      networkLog.push({
        type: 'response',
        url: res.url(),
        method: res.request().method(),
        status: res.status(),
        statusText: res.statusText(),
        corsHeader: res.headers()['access-control-allow-origin'] || 'NONE',
        bodyPreview: bodyPreview,
        time: Date.now()
      });
      console.log(`[HTTP ${res.status()}] ${res.request().method()} ${res.url()} (CORS: ${res.headers()['access-control-allow-origin'] || 'None'})`);
    }
  });

  console.log('Navigating to http://localhost:3000/workspace ...');
  await page.goto('http://localhost:3000/workspace', { waitUntil: 'domcontentloaded', timeout: 30000 });
  await page.waitForTimeout(3000);

  // 1. Test Coordinate Navigation Search & Fly (which hits coordinate parse / validation)
  console.log('Interacting with COORDINATES dock tab...');
  const raInput = page.locator('input[placeholder*="133.795129"]');
  if (await raInput.count() > 0) {
    await raInput.fill('133.7951');
    const decInput = page.locator('input[placeholder*="-7.245139"]');
    if (await decInput.count() > 0) {
      await decInput.fill('-7.2451');
    }
    const searchBtn = page.locator('button:has-text("Search & Fly")');
    if (await searchBtn.count() > 0) {
      console.log('Clicking Search & Fly...');
      await searchBtn.click();
      await page.waitForTimeout(2000);
    }
  }

  // 2. Test IMAGE LAYERS tab
  console.log('Switching to IMAGE LAYERS tab...');
  const layersTab = page.locator('#dock-tab-layers');
  if (await layersTab.count() > 0) {
    await layersTab.click();
    await page.waitForTimeout(1000);

    const productDropdown = page.locator('select').first();
    if (await productDropdown.count() > 0) {
      console.log('Product dropdown found in Image Layers.');
    }
  }

  // 3. Test Direct API fetch from inside the page context (evaluating client fetch through apiConfig)
  console.log('Executing client-side API verification inside page context...');
  const inPageClientResults = await page.evaluate(async () => {
    const results = [];
    
    // Test 1: Fetch Targets
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/targets');
      const data = await res.json();
      results.push({ endpoint: '/targets', status: res.status, ok: res.ok, count: Array.isArray(data) ? data.length : 1 });
    } catch (e) {
      results.push({ endpoint: '/targets', error: e.message });
    }

    // Test 2: Fetch Spectral Bands
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/spectral/bands');
      const data = await res.json();
      results.push({ endpoint: '/spectral/bands', status: res.status, ok: res.ok, count: Array.isArray(data) ? data.length : 0 });
    } catch (e) {
      results.push({ endpoint: '/spectral/bands', error: e.message });
    }

    // Test 3: Coordinate Parse
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/coordinates/parse', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ra: '133.7951', dec: '-7.2451' })
      });
      const data = await res.json();
      results.push({ endpoint: '/coordinates/parse', status: res.status, ok: res.ok, valid: data.valid });
    } catch (e) {
      results.push({ endpoint: '/coordinates/parse', error: e.message });
    }

    // Test 4: Image Sample
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/images/sample/wise-0855?stretch=asinh');
      const data = await res.json();
      results.push({ endpoint: '/images/sample/wise-0855', status: res.status, ok: res.ok, hasTexture: !!data.texture_data_uri });
    } catch (e) {
      results.push({ endpoint: '/images/sample/wise-0855', error: e.message });
    }

    // Test 5: Temporal Benchmark Pairs
    try {
      const res = await fetch('http://127.0.0.1:8000/api/v1/temporal/benchmark-pairs');
      const data = await res.json();
      results.push({ endpoint: '/temporal/benchmark-pairs', status: res.status, ok: res.ok, count: Array.isArray(data) ? data.length : 0 });
    } catch (e) {
      results.push({ endpoint: '/temporal/benchmark-pairs', error: e.message });
    }

    return results;
  });

  console.log('In-page fetch results from frontend browser session:');
  console.log(JSON.stringify(inPageClientResults, null, 2));

  // Take visual verification screenshot
  const screenshotPath = path.join(artifactDir, 'skytrace-local-connection-active.png');
  await page.screenshot({ path: screenshotPath, fullPage: false });
  console.log(`Saved screenshot to ${screenshotPath}`);

  const evidence = {
    timestamp: new Date().toISOString(),
    frontendUrl: 'http://localhost:3000/workspace',
    backendUrl: 'http://127.0.0.1:8000',
    browserInPageFetches: inPageClientResults,
    networkEventsCount: networkLog.length,
    responses: networkLog.filter(n => n.type === 'response'),
    consoleErrorsCount: consoleMessages.filter(c => c.type === 'error').length,
    uncaughtErrorsCount: errors.length
  };

  fs.writeFileSync('browser_network_evidence.json', JSON.stringify(evidence, null, 2), 'utf8');
  console.log('Saved browser network evidence to browser_network_evidence.json');

  await browser.close();
}

main().catch(err => {
  console.error('Browser test failed:', err);
  process.exit(1);
});
