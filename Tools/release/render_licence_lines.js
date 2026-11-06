// Render Kaggle pages in Chromium (Playwright) and print their licence lines. Usage: node render_licence_lines.js URL [URL ...]
// Used on 2026-11-06 to read the licence each notebook page displays (the Kaggle API does not expose it).
const { chromium } = require('playwright');
(async () => {
  const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined;
  const browser = await chromium.launch({ proxy });
  const page = await browser.newPage({ ignoreHTTPSErrors: false });
  for (const url of process.argv.slice(2)) {
    try {
      await page.goto(url, { waitUntil: "domcontentloaded", timeout: 90000 });
      await page.waitForTimeout(15000);
      const text = await page.evaluate(() => document.body.innerText);
      const lines = text.split('\n').filter(l => /licen[sc]e|apache/i.test(l));
      console.log('=== ' + url + ' (' + text.length + ' chars)');
      lines.slice(0, 15).forEach(l => console.log('  ' + l.slice(0, 400)));
    } catch (e) { console.log('=== ' + url + ' ERROR ' + e.message.slice(0, 200)); }
  }
  await browser.close();
})();
