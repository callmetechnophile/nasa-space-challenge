const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  console.log('========================================================================');
  console.log('SKYTRACE TYPOGRAPHY AUDIT: CAMBRIA MATH & HIERARCHY VERIFICATION');
  console.log('========================================================================\n');

  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const routes = [
    { url: 'http://localhost:3000/', name: 'Home' },
    { url: 'http://localhost:3000/spherex', name: 'SPHEREx Mission' },
    { url: 'http://localhost:3000/spherex/instrument', name: 'Instrument Architecture' },
    { url: 'http://localhost:3000/spherex/spectral-bands', name: '102 Spectral Bands' },
    { url: 'http://localhost:3000/planet-x', name: 'Planet X Hypothesis' },
    { url: 'http://localhost:3000/planet-x/evidence', name: 'Evidence & Search' },
    { url: 'http://localhost:3000/science', name: 'Science & Methodology' },
  ];

  const desktopContext = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const page = await desktopContext.newPage();

  let totalMathChecked = 0;
  let totalParagraphsChecked = 0;

  for (const r of routes) {
    console.log(`\n------------------------------------------------------------------------`);
    console.log(`Auditing Route: ${r.name} (${r.url})`);
    console.log(`------------------------------------------------------------------------`);

    await page.goto(r.url, { waitUntil: 'domcontentloaded' });
    await page.waitForTimeout(1000);

    const audit = await page.evaluate(() => {
      // 1. Math elements (.math-inline, .math-display, .katex, math)
      const mathElements = Array.from(document.querySelectorAll('.math-inline, .math-display, .katex, math, .scientific-equation'));
      const mathDetails = mathElements.map((el, i) => {
        const style = window.getComputedStyle(el);
        return {
          tag: el.tagName.toLowerCase(),
          className: el.className,
          fontFamily: style.fontFamily,
          fontSize: style.fontSize,
          text: (el.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 50),
        };
      });

      // 2. Paragraphs (main p)
      const pElements = Array.from(document.querySelectorAll('main p'));
      const pDetails = pElements.map(p => {
        const style = window.getComputedStyle(p);
        return {
          fontFamily: style.fontFamily,
          fontSize: style.fontSize,
          text: (p.textContent || '').trim().replace(/\s+/g, ' ').slice(0, 45),
        };
      });

      // 3. Headings (h1, h2, h3)
      const h1 = document.querySelector('h1');
      const h1Font = h1 ? window.getComputedStyle(h1).fontFamily : 'None';

      const h2 = document.querySelector('h2');
      const h2Font = h2 ? window.getComputedStyle(h2).fontFamily : 'None';

      // 4. Wordmark
      const wordmark = document.querySelector('.font-corpta');
      const wordmarkFont = wordmark ? window.getComputedStyle(wordmark).fontFamily : 'None';

      return {
        mathCount: mathElements.length,
        mathDetails: mathDetails.slice(0, 4),
        mathAllCambriaOrStix: mathDetails.every(m => {
          const lower = m.fontFamily.toLowerCase();
          return lower.includes('cambria math') || lower.includes('stix two math') || lower.includes('latin modern math');
        }),
        pCount: pElements.length,
        pDetails: pDetails.slice(0, 3),
        pAllTimes: pDetails.every(p => {
          const lower = p.fontFamily.toLowerCase();
          return lower.includes('times new roman') || lower.includes('times');
        }),
        h1Font,
        h2Font,
        wordmarkFont,
      };
    });

    console.log(`  H1 Font Family: ${audit.h1Font}`);
    console.log(`  H2 Font Family: ${audit.h2Font}`);
    console.log(`  Wordmark Font: ${audit.wordmarkFont}`);
    console.log(`  Paragraphs Count: ${audit.pCount}`);
    console.log(`  All Paragraphs use Times New Roman: ${audit.pAllTimes ? '✓ PASS' : '✗ FAIL'}`);
    console.log(`  Math Elements Found: ${audit.mathCount}`);
    console.log(`  All Math Elements use Cambria Math (or STIX fallback): ${audit.mathAllCambriaOrStix ? '✓ PASS' : '✗ FAIL'}`);

    if (audit.mathCount > 0) {
      console.log(`  Sample Math Expressions:`);
      audit.mathDetails.forEach((m, idx) => {
        console.log(`    [Math ${idx + 1}] font-family: "${m.fontFamily}", size: ${m.fontSize}`);
        console.log(`           expression: "${m.text}"`);
      });
    }

    if (!audit.pAllTimes) {
      throw new Error(`Route ${r.name} has paragraphs not using Times New Roman!`);
    }
    if (audit.mathCount > 0 && !audit.mathAllCambriaOrStix) {
      throw new Error(`Route ${r.name} has math elements not using Cambria Math / STIX Two Math!`);
    }

    totalMathChecked += audit.mathCount;
    totalParagraphsChecked += audit.pCount;
  }

  // Verify Workspace Isolation
  console.log(`\n------------------------------------------------------------------------`);
  console.log(`Auditing Route: Scientific IDE (/workspace) Isolation`);
  console.log(`------------------------------------------------------------------------`);
  await page.goto('http://localhost:3000/workspace', { waitUntil: 'domcontentloaded' });
  await page.waitForTimeout(1500);

  const workspaceAudit = await page.evaluate(() => {
    const buttons = Array.from(document.querySelectorAll('button'));
    const buttonFonts = buttons.slice(0, 5).map(b => window.getComputedStyle(b).fontFamily);
    const bodyFont = window.getComputedStyle(document.body).fontFamily;
    const isUsingTimes = buttonFonts.some(f => f.toLowerCase().includes('times new roman'));
    const isUsingCambria = buttonFonts.some(f => f.toLowerCase().includes('cambria math'));
    return {
      bodyFont,
      sampleButtonFont: buttonFonts[0],
      isolatedFromTimes: !isUsingTimes,
      isolatedFromCambria: !isUsingCambria,
    };
  });

  console.log(`  Workspace Body Font: ${workspaceAudit.bodyFont}`);
  console.log(`  Workspace Control Font: ${workspaceAudit.sampleButtonFont}`);
  console.log(`  Workspace Isolated from Times New Roman: ${workspaceAudit.isolatedFromTimes ? '✓ PASS' : '✗ FAIL'}`);
  console.log(`  Workspace Isolated from Cambria Math: ${workspaceAudit.isolatedFromCambria ? '✓ PASS' : '✗ FAIL'}`);

  if (!workspaceAudit.isolatedFromTimes || !workspaceAudit.isolatedFromCambria) {
    throw new Error('Workspace IDE typography leaked public serif/math fonts!');
  }

  await browser.close();

  console.log(`\n========================================================================`);
  console.log(`ALL VERIFICATIONS PASSED!`);
  console.log(`  Total Math Elements Audited: ${totalMathChecked}`);
  console.log(`  Total Paragraphs Audited: ${totalParagraphsChecked}`);
  console.log(`  Typography Hierarchy Adherence: 100%`);
  console.log(`========================================================================\n`);
}

main().catch(err => {
  console.error('VERIFICATION FAILED:', err);
  process.exit(1);
});
