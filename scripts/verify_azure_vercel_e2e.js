const { chromium } = require('d:/nasa/frontend/node_modules/playwright');
const fs = require('fs');
const path = require('path');

async function run() {
  console.log('Launching headless browser...');
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
    args: ['--no-sandbox', '--disable-setuid-sandbox']
  });

  const context = await browser.newContext({
    viewport: { width: 1440, height: 900 }
  });

  const page = await context.newPage();

  const networkTraffic = [];
  const backendCalls = [];

  page.on('request', request => {
    const url = request.url();
    if (url.includes('azurecontainerapps.io') || url.includes('/api/')) {
      console.log(`[REQUEST] ${request.method()} ${url}`);
    }
  });

  page.on('response', async response => {
    const url = response.url();
    const status = response.status();
    const isBackend = url.includes('azurecontainerapps.io');
    const isApi = url.includes('/api/');

    if (isBackend || isApi) {
      console.log(`[RESPONSE] ${status} ${url}`);
      let bodyPreview = '';
      try {
        const text = await response.text();
        bodyPreview = text.slice(0, 300);
      } catch (e) {
        bodyPreview = '<binary or unreadable>';
      }

      const item = {
        url,
        status,
        statusText: response.statusText(),
        headers: response.headers(),
        bodyPreview
      };

      networkTraffic.push(item);
      if (isBackend) {
        backendCalls.push(item);
      }
    }
  });

  page.on('console', msg => {
    const text = msg.text();
    if (text.toLowerCase().includes('error') || text.toLowerCase().includes('fail')) {
      console.log(`[BROWSER CONSOLE] ${msg.type()}: ${text}`);
    }
  });

  console.log('Navigating to Vercel production frontend: https://skytracebysplinets.vercel.app ...');
  try {
    await page.goto('https://skytracebysplinets.vercel.app', { waitUntil: 'networkidle', timeout: 30000 });
  } catch (e) {
    console.log('Initial navigation timeout or partial idle, continuing:', e.message);
  }

  // Wait 4 seconds for any async initial data fetches
  await page.waitForTimeout(4000);

  // Take landing page screenshot
  const screenshotPath = 'C:\\Users\\worka\\.gemini\\antigravity\\brain\\4caccf68-379b-4aca-b442-5eeb4701650e\\skytrace-vercel-landing-live.png';
  await page.screenshot({ path: screenshotPath, fullPage: false });
  console.log(`Landing screenshot saved: ${screenshotPath}`);

  // Now navigate to /workspace
  console.log('Navigating to workspace: https://skytracebysplinets.vercel.app/workspace ...');
  try {
    await page.goto('https://skytracebysplinets.vercel.app/workspace', { waitUntil: 'networkidle', timeout: 35000 });
  } catch (e) {
    console.log('Workspace navigation timeout or partial idle, continuing:', e.message);
  }

  // Wait 6 seconds for workspace state, Three.js canvas, and API calls to settle
  await page.waitForTimeout(6000);

  const workspaceScreenshotPath = 'C:\\Users\\worka\\.gemini\\antigravity\\brain\\4caccf68-379b-4aca-b442-5eeb4701650e\\skytrace-vercel-workspace-live.png';
  await page.screenshot({ path: workspaceScreenshotPath, fullPage: false });
  console.log(`Workspace screenshot saved: ${workspaceScreenshotPath}`);

  // Test direct browser fetch to Azure backend from the page context to test CORS in real browser
  const browserCorsTest = await page.evaluate(async () => {
    try {
      const resp = await fetch('https://skytrace-backend.bravewave-3f2f8e7c.eastus.azurecontainerapps.io/api/v1/targets', {
        headers: { 'Accept': 'application/json' }
      });
      const data = await resp.json();
      return {
        success: true,
        status: resp.status,
        headers: Object.fromEntries(resp.headers.entries()),
        dataLength: Array.isArray(data) ? data.length : typeof data
      };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  console.log('In-page CORS test result:', JSON.stringify(browserCorsTest, null, 2));

  // Test direct browser fetch to coordinates conversion
  const browserCoordsTest = await page.evaluate(async () => {
    try {
      const resp = await fetch('https://skytrace-backend.bravewave-3f2f8e7c.eastus.azurecontainerapps.io/api/v1/coordinates/convert?ra=269.452083&dec=4.693333');
      const data = await resp.json();
      return {
        success: true,
        status: resp.status,
        data
      };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  console.log('In-page Coordinates test result:', JSON.stringify(browserCoordsTest, null, 2));

  // Also test spectral bands
  const browserSpectralTest = await page.evaluate(async () => {
    try {
      const resp = await fetch('https://skytrace-backend.bravewave-3f2f8e7c.eastus.azurecontainerapps.io/api/v1/spectral/bands');
      const data = await resp.json();
      return {
        success: true,
        status: resp.status,
        bandsCount: Array.isArray(data) ? data.length : 0
      };
    } catch (err) {
      return { success: false, error: err.message };
    }
  });

  console.log('In-page Spectral test result:', JSON.stringify(browserSpectralTest, null, 2));

  const evidence = {
    timestamp: new Date().toISOString(),
    frontendUrl: 'https://skytracebysplinets.vercel.app',
    backendUrl: 'https://skytrace-backend.bravewave-3f2f8e7c.eastus.azurecontainerapps.io',
    browserCorsTest,
    browserCoordsTest,
    browserSpectralTest,
    networkTraffic,
    backendCalls
  };

  fs.writeFileSync('d:\\nasa\\vercel_azure_e2e_evidence.json', JSON.stringify(evidence, null, 2));
  console.log('Evidence saved to d:\\nasa\\vercel_azure_e2e_evidence.json');

  await browser.close();
  console.log('Verification completed successfully!');
}

run().catch(err => {
  console.error('Fatal error during verification:', err);
  process.exit(1);
});
