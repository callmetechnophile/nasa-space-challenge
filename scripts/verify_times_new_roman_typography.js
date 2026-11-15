const path = require('path');
const fs = require('fs');
const { chromium } = require(path.resolve(__dirname, '../frontend/node_modules/playwright'));

async function main() {
  console.log('Launching browser for Times New Roman typography verification...');
  const edgePath = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe';
  const browser = await chromium.launch({
    headless: true,
    executablePath: fs.existsSync(edgePath) ? edgePath : undefined,
  });

  const routes = [
    { url: 'http://localhost:3000/', name: 'Home' },
    { url: 'http://localhost:3000/spherex', name: 'SPHEREx' },
    { url: 'http://localhost:3000/spherex/instrument', name: 'Instrument' },
    { url: 'http://localhost:3000/spherex/spectral-bands', name: 'Spectral Bands' },
    { url: 'http://localhost:3000/planet-x', name: 'Planet X' },
    { url: 'http://localhost:3000/planet-x/evidence', name: 'Evidence & Search' },
    { url: 'http://localhost:3000/science', name: 'Science & Methodology' },
  ];

  // Desktop context (1440x900)
  const desktopContext = await browser.newContext({
    viewport: { width: 1440, height: 900 },
  });
  const desktopPage = await desktopContext.newPage();

  console.log('\n=== DESKTOP TYPOGRAPHY AUDIT ===');
  for (const r of routes) {
    await desktopPage.goto(r.url, { waitUntil: 'domcontentloaded' });
    await desktopPage.waitForTimeout(1000);

    const report = await desktopPage.evaluate(() => {
      const pElements = Array.from(document.querySelectorAll('main p'));
      const pFonts = pElements.map(p => {
        const style = window.getComputedStyle(p);
        return {
          fontFamily: style.fontFamily,
          fontSize: style.fontSize,
          lineHeight: style.lineHeight,
          fontWeight: style.fontWeight,
          sampleText: p.textContent?.trim().slice(0, 45) + '...',
        };
      });

      const h1 = document.querySelector('h1');
      const h1Font = h1 ? window.getComputedStyle(h1).fontFamily : 'None';

      const wordmark = document.querySelector('.font-corpta');
      const wordmarkFont = wordmark ? window.getComputedStyle(wordmark).fontFamily : 'None';

      return {
        totalParagraphs: pElements.length,
        h1Font,
        wordmarkFont,
        samples: pFonts.slice(0, 3),
        allUseTimes: pFonts.every(p => p.fontFamily.toLowerCase().includes('times new roman') || p.fontFamily.toLowerCase().includes('times')),
      };
    });

    console.log(`\nRoute: ${r.name} (${r.url})`);
    console.log(`  H1 Font: ${report.h1Font}`);
    console.log(`  Wordmark Font: ${report.wordmarkFont}`);
    console.log(`  Total Paragraphs: ${report.totalParagraphs}`);
    console.log(`  All Paragraphs use Times New Roman: ${report.allUseTimes ? 'PASS (100%)' : 'FAIL'}`);
    report.samples.forEach((s, idx) => {
      console.log(`    [P${idx + 1}] font-family: "${s.fontFamily}", size: ${s.fontSize}, line-height: ${s.lineHeight}, weight: ${s.fontWeight}`);
      console.log(`         text: "${s.sampleText}"`);
    });

    if (!report.allUseTimes) {
      throw new Error(`Route ${r.name} has paragraphs not using Times New Roman!`);
    }
  }

  // Mobile context (390x844)
  console.log('\n=== MOBILE TYPOGRAPHY AUDIT ===');
  const mobileContext = await browser.newContext({
    viewport: { width: 390, height: 844 },
    isMobile: true,
  });
  const mobilePage = await mobileContext.newPage();
  await mobilePage.goto('http://localhost:3000/spherex', { waitUntil: 'domcontentloaded' });
  await mobilePage.waitForTimeout(1000);

  const mobileReport = await mobilePage.evaluate(() => {
    const p = document.querySelector('main p');
    if (!p) return null;
    const style = window.getComputedStyle(p);
    return {
      fontFamily: style.fontFamily,
      fontSize: style.fontSize,
      lineHeight: style.lineHeight,
      fontWeight: style.fontWeight,
    };
  });
  console.log('Mobile Paragraph Sample (/spherex):');
  console.log(`  font-family: "${mobileReport?.fontFamily}"`);
  console.log(`  font-size: ${mobileReport?.fontSize}`);
  console.log(`  line-height: ${mobileReport?.lineHeight}`);

  // Workspace IDE check
  console.log('\n=== WORKSPACE IDE ISOLATION AUDIT ===');
  await desktopPage.goto('http://localhost:3000/workspace', { waitUntil: 'domcontentloaded' });
  await desktopPage.waitForTimeout(2000);

  const ideReport = await desktopPage.evaluate(() => {
    const ideRoot = document.querySelector('.astro-ide-root');
    const ideFont = ideRoot ? window.getComputedStyle(ideRoot).fontFamily : 'None';
    const ideButtons = Array.from(document.querySelectorAll('.astro-ide-root button')).slice(0, 3);
    const buttonFonts = ideButtons.map(b => window.getComputedStyle(b).fontFamily);
    const ideUsesTimes = ideFont.toLowerCase().includes('times') || buttonFonts.some(f => f.toLowerCase().includes('times'));
    return {
      ideFont,
      buttonFonts,
      ideUsesTimes,
    };
  });
  console.log(`  IDE Root Font: ${ideReport.ideFont}`);
  console.log(`  IDE Buttons Font: ${ideReport.buttonFonts.join(', ')}`);
  console.log(`  IDE Preserved (NO Times New Roman): ${!ideReport.ideUsesTimes ? 'PASS' : 'FAIL'}`);

  if (ideReport.ideUsesTimes) {
    throw new Error('IDE incorrectly inherited Times New Roman!');
  }

  await browser.close();
  console.log('\nALL TYPOGRAPHY VALIDATIONS PASSED CLEANLY.');
}

main().catch(err => {
  console.error('Validation failed:', err);
  process.exit(1);
});
