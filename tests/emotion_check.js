// GM emotion detail, escaping and public-view privacy in an isolated scratch viewer.
const assert = require('node:assert/strict');
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ args: ['--no-sandbox'] });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on('pageerror', e => errors.push(e.message));
    await page.goto('http://127.0.0.1:8766/');
    await page.waitForSelector('#btnGo', { state: 'visible' });
    await page.waitForSelector('#rule optgroup', { state: 'attached' });
    await page.selectOption('#backend', 'mock');
    await page.click('.opt[data-mode="live"]');
    await page.click('#btnGo');
    await page.waitForFunction(() => S.session && S.ticks.length > 0);
    const result = await page.evaluate(() => {
      S.state = S.ticks[0].state;
      const id = Object.keys(S.state.agents)[0], a = S.state.agents[id];
      const fromSnapshot = Array.isArray(a.emotions);
      a.emotions = [{ kind: 'grief <img src=x onerror=alert(1)>', intensity: 7.25, cause: 'A friend & a painful memory.' }];
      S.selected = id; S.gm = true; renderCast();
      const detail = document.querySelector('#castDetail');
      const visible = detail.textContent.includes('Lasting emotions') && detail.textContent.includes('7.3/10') && detail.textContent.includes('A friend & a painful memory.');
      const escaped = detail.textContent.includes('<img src=x onerror=alert(1)>') && !detail.querySelector('img[src="x"]');
      S.gm = false; renderCast();
      const hidden = !detail.textContent.includes('Lasting emotions') && !detail.textContent.includes('painful memory');
      return { fromSnapshot, visible, escaped, hidden };
    });
    assert.deepEqual(result, { fromSnapshot: true, visible: true, escaped: true, hidden: true });
    assert.deepEqual(errors, []);
    console.log('Emotion snapshot, GM details, escaping and public-view privacy passed');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
