// Viewer check in a real browser: start a mock live day, play it for two minutes, and report script errors and whether the game clock kept moving while people talked;
// then fast-forward to the night and check that a quiet night block is offered for skipping and skipped. (The trial needs several days and is not reached here.)
// Needs Node with Playwright and a running server on a scratch data directory, e.g.:
//   MC_DATA_DIR=/tmp/mc_view python server.py &      then      node tests/viewer_check.js
// Exits non-zero if there were script errors or the clock froze during a conversation.
const pw = (() => { try { return require("playwright"); } catch (e) { return require(require("path").join(process.execPath, "..", "..", "lib", "node_modules", "playwright")); } })();
const assert = require("node:assert/strict");
(async () => {
  const b = await pw.chromium.launch({ args: ["--no-sandbox"] });
  const p = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = [];
  p.on("pageerror", (e) => errs.push("pageerror: " + e.message));
  p.on("console", (m) => { if (m.type() === "error" && !m.text().includes("404")) errs.push("console: " + m.text()); });
  await p.goto(process.env.MC_URL || "http://localhost:8766/");
  await p.waitForTimeout(2000);
  await p.selectOption("#backend", "mock");
  await p.selectOption("#pace", "10");
  await p.click('.opt[data-mode="live"]');
  await p.click("#btnGo");
  const samples = [];
  let thoughtShot = false;
  for (let i = 0; i < 240; i++) {
    await p.evaluate(() => {
      const m = document.querySelector("#tmmodal"); if (m && m.style.display === "flex") { const btn = m.querySelector("button"); if (btn) btn.click(); }
      const ov = document.querySelector("#overlay"); if (ov && ov.style.display === "flex") { const c = document.querySelector("#ovClose"); if (c) c.click(); }
    });
    samples.push(await p.evaluate(() => ({ m: window.TileMap ? TileMap.minute() : null, talking: (S.bubbles || []).filter((x) => x.until > S.clock && !x.think).length, cursor: S.cursor,
      thinking: (S.bubbles || []).filter((x) => x.until > S.clock && x.think).length })));
    if (process.env.MC_SHOT && samples[samples.length - 1].thinking && !thoughtShot) { thoughtShot = true; await p.screenshot({ path: process.env.MC_SHOT }); }
    await p.waitForTimeout(500);
  }
  let talkPairs = 0, frozen = 0;
  for (let i = 1; i < samples.length; i++) {
    const a = samples[i - 1], c = samples[i];
    if (a.talking && c.talking && a.cursor === c.cursor) { talkPairs++; if (c.m === a.m) frozen++; }
  }
  // then the night: fast-forward the rest of the day, step back to just before the first quiet night block, and check the "house sleeps" prompt skips it
  const thoughts = await p.evaluate(() => document.querySelectorAll("#feed .thought").length);
  async function dismissPlaybackDialogs() {
    if (await p.locator("#tmmodal").isVisible()) await p.locator("#tmmodal button").first().click({ timeout: 1000 });
    if (await p.locator("#ovClose").isVisible()) await p.locator("#ovClose").click({ timeout: 1000 });
  }
  let forwarded = false;
  for (let i = 0; i < 10 && !forwarded; i++) {
    try {
      await dismissPlaybackDialogs();
      await p.click("#btnFF", { timeout: 1000 });
      forwarded = await p.evaluate(() => S.ff);
    } catch (e) { /* a newly opened playback dialog needs closing first */ }
  }
  assert.ok(forwarded, "the fast-forward button must actually be activated");
  for (let i = 0; i < 120; i++) {
    if (await p.evaluate(() => S.done && S.cursor >= S.ticks.length - 1)) break;
    await dismissPlaybackDialogs();
    await p.waitForTimeout(500);
  }
  const completion = await p.evaluate(async () => ({ done: S.done, error: S.error, cursor: S.cursor, ticks: S.ticks.length,
    ff: S.ff, status: await (await fetch('/api/diagnostics')).json() }));
  assert.ok(completion.done && !completion.error, "the mock day must finish without an engine error: " + JSON.stringify(completion));
  await p.evaluate(() => { const c = document.querySelector("#ovClose"); if (c) c.click(); });
  const qi = await p.evaluate(() => S.ticks.findIndex((t) => t.quiet));
  let night = { quietBlocks: await p.evaluate(() => S.ticks.filter((t) => t.quiet).length), asked: false, skipped: false };
  if (qi > 0) {
    await p.evaluate(() => { try { localStorage.removeItem("mcLiveSettings"); TileMap.setQuietNight("ask"); } catch (e) { /* private mode */ } });
    await p.evaluate((i) => { S.endShown = true; jumpTo(i - 1); S.paused = false; S.ff = false; S.quietChoice = null; }, qi);
    for (let i = 0; i < 80 && !night.asked; i++) {
      const txt = await p.evaluate(() => { const m = document.querySelector("#tmmodal"); return m && m.style.display === "flex" ? m.innerText.toLowerCase() : ""; });
      if (txt.includes("the house sleeps")) night.asked = true;
      else if (txt) await p.evaluate(() => document.querySelector("#tmmodal button").click());
      else await p.waitForTimeout(250);
    }
    if (night.asked) { await p.click("#qnSkip"); await p.waitForTimeout(1500); night.skipped = await p.evaluate((i) => S.cursor >= i, qi); }
  }
  const out = { turnsPlayed: samples[samples.length - 1].cursor, talkPairs, frozen, thoughts, thoughtBubbles: samples.filter((x) => x.thinking).length, generationCompleted: await p.evaluate(() => S.done), night, errors: errs };
  console.log(JSON.stringify(out, null, 1));
  await b.close();
  process.exit(errs.length || frozen || (qi > 0 && !night.skipped) ? 1 : 0);
})();
