// Pacing in a real browser: play the first daytime blocks of a mock live day with the quick clock off and at 4x, and report the real seconds each block took
// and how long the map stood still at each block start (the title card and TereVi's broadcasts no longer stop the clock).
// Needs a running server on a scratch data directory (see viewer_check.js), then:  node tests/pace_check.js
const pw = (() => { try { return require("playwright"); } catch (e) { return require(require("path").join(process.execPath, "..", "..", "lib", "node_modules", "playwright")); } })();
const BLOCKS = Number(process.env.MC_BLOCKS || 3);

async function run(b, quick) {
  const p = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = [];
  p.on("pageerror", (e) => errs.push("pageerror: " + e.message));
  await p.goto(process.env.MC_URL || "http://localhost:8766/");
  await p.evaluate((q) => localStorage.setItem("mcLiveSettings", JSON.stringify({ classes: { critical: "log", important: "log", notable: "log", background: "log" }, pauseTalk: "off", segMsg: true, quietNight: "auto", quickClock: q })), quick);
  await p.reload();
  await p.waitForTimeout(1500);
  await p.selectOption("#backend", "mock");
  await p.selectOption("#pace", "10");
  await p.click('.opt[data-mode="live"]');
  await p.click("#btnGo");
  const starts = {}, still = {};
  let last = -2, t0 = null;
  for (let i = 0; i < 2400; i++) {
    const s = await p.evaluate(() => ({ cur: S.cursor, play: S.playIdx, m: window.TileMap ? TileMap.minute() : 0, now: Date.now() }));
    if (s.play !== last && s.play != null && s.play >= 0) { last = s.play; starts[s.play] = s.now; t0 = s.now; }
    if (t0 && still[last] == null && s.m > 0.5) still[last] = s.now - t0;
    if (s.cur >= BLOCKS - 1 && s.play >= BLOCKS) break;
    await p.waitForTimeout(100);
  }
  const secs = [];
  for (let k = 0; k < BLOCKS; k++) if (starts[k] && starts[k + 1]) secs.push(Math.round((starts[k + 1] - starts[k]) / 100) / 10);
  await p.close();
  return { quick, blockSeconds: secs, total: Math.round(secs.reduce((a, x) => a + x, 0) * 10) / 10, mapStillMsAtStart: Object.values(still).slice(0, BLOCKS), errors: errs };
}

(async () => {
  const b = await pw.chromium.launch({ args: ["--no-sandbox"] });
  const out = [];
  for (const q of [1, 4]) out.push(await run(b, q));
  console.log(JSON.stringify(out, null, 1));
  await b.close();
})();
