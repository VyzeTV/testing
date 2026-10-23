// Offline browser regression for status, report content, and copy behavior.
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ args: ["--no-sandbox"] });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", e => errors.push(e.message));
    await page.goto("http://127.0.0.1:8766/");
    await page.waitForSelector("#btnCancel", { state: "visible" });
    await page.click("#btnCancel");
    await page.click("#btnDiagnostics");
    await page.waitForFunction(() => document.querySelector("#diagnosticsDialog").open);
    const report = JSON.parse(await page.inputValue("#diagnosticReport"));
    assert.equal(report.generation.state, "idle");
    assert.equal(report.format, 1);
    assert.ok(!("agents" in report));
    // Exercise the copy button without depending on the host clipboard permission.
    await page.evaluate(() => {
      window.copiedReport = null;
      Object.defineProperty(navigator, "clipboard", { configurable: true, value: {
        writeText: async text => { window.copiedReport = text; }
      }});
    });
    await page.click("#btnCopyDiagnostics");
    assert.equal(await page.evaluate(() => window.copiedReport), JSON.stringify(report, null, 2));
    await page.evaluate(() => Object.defineProperty(navigator, "clipboard", { configurable: true, value: undefined }));
    await page.click("#btnCopyDiagnostics");
    assert.equal(await page.evaluate(() => {
      const f = document.querySelector("#diagnosticReport");
      return f.selectionStart === 0 && f.selectionEnd === f.value.length;
    }), true);
    await page.click("#btnCloseDiagnostics");
    await page.click("#btnNew");
    await page.selectOption("#backend", "mock");
    await page.click('.opt[data-mode="live"]');
    await page.click("#btnGo");
    await page.waitForFunction(() => /Generating|waiting on|complete/i.test(document.querySelector("#generationStatus").textContent));
    await page.click("#btnDiagnostics");
    await page.waitForFunction(() => document.querySelector("#diagnosticsDialog").open);
    const active = JSON.parse(await page.inputValue("#diagnosticReport"));
    assert.equal(active.session.backend, "mock");
    assert.notEqual(active.generation.state, "idle");
    assert.deepEqual(errors, []);
    console.log("Diagnostics status, report and copy checks passed");
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
