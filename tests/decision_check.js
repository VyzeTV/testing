// Stated motives stay in GM details, preserve statuses and escape generated text.
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
    // This test needs a real model request in the first buffered block.
    const tuning = await page.request.post('http://127.0.0.1:8766/api/tuning', { data: { values: { engine_decisions: 0 } } });
    assert.equal(tuning.ok(), true);
    await page.selectOption('#backend', 'mock');
    await page.click('.opt[data-mode="live"]');
    await page.click('#btnGo');
    await page.waitForFunction(() => S.session && S.ticks.length > 0);
    const result = await page.evaluate(() => {
      S.state = S.ticks[0].state;
      const id = Object.keys(S.state.agents)[0], a = S.state.agents[id];
      const fromSnapshot = Array.isArray(a.decisions);
      const actualReason = Object.values(S.state.agents).some(a => (a.decisions || []).some(d => d.reason));
      a.decisions = [{ option: 'act:rest', selected: { action: 'rest' }, reason: 'Private <img src=x onerror=alert(1)> & motive',
        status: 'changed', change: 'Urgent care took priority.' }];
      S.selected = id; S.gm = true; renderCast();
      const detail = document.querySelector('#castDetail');
      const visible = detail.textContent.includes('Stated motives') && detail.textContent.includes('(changed)') && detail.textContent.includes('Urgent care took priority.');
      const escaped = detail.textContent.includes('<img src=x onerror=alert(1)>') && !detail.querySelector('img[src="x"]');
      S.gm = false; renderCast();
      const hidden = !detail.textContent.includes('Stated motives') && !detail.textContent.includes('Private <img');
      return { fromSnapshot, actualReason, visible, escaped, hidden };
    });
    assert.deepEqual(result, { fromSnapshot: true, actualReason: true, visible: true, escaped: true, hidden: true });
    assert.deepEqual(errors, []);
    console.log('Decision snapshot, GM motives, overrides, escaping and public-view privacy passed');
  } finally { await browser.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
