// Viewer check in a real browser: start a mock live day, play it for two minutes, and report script errors and whether the game clock kept moving while people talked.
// Needs Node with Playwright and a running server on a scratch data directory, e.g.:
//   MC_DATA_DIR=/tmp/mc_view python server.py &      then      node tests/viewer_check.js
// Exits non-zero if there were script errors or the clock froze during a conversation.
const pw = (() => { try { return require("playwright"); } catch (e) { return require(require("path").join(process.execPath, "..", "..", "lib", "node_modules", "playwright")); } })();
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
  for (let i = 0; i < 240; i++) {
    await p.evaluate(() => {
      const m = document.querySelector("#tmmodal"); if (m && m.style.display === "flex") { const btn = m.querySelector("button"); if (btn) btn.click(); }
      const ov = document.querySelector("#overlay"); if (ov && ov.style.display === "flex") { const c = document.querySelector("#ovClose"); if (c) c.click(); }
    });
    samples.push(await p.evaluate(() => ({ m: window.TileMap ? TileMap.minute() : null, talking: (S.bubbles || []).filter((x) => x.until > S.clock).length, cursor: S.cursor })));
    await p.waitForTimeout(500);
  }
  let talkPairs = 0, frozen = 0;
  for (let i = 1; i < samples.length; i++) {
    const a = samples[i - 1], c = samples[i];
    if (a.talking && c.talking && a.cursor === c.cursor) { talkPairs++; if (c.m === a.m) frozen++; }
  }
  const out = { turnsPlayed: samples[samples.length - 1].cursor, talkPairs, frozen, errors: errs };
  console.log(JSON.stringify(out, null, 1));
  await b.close();
  process.exit(errs.length || frozen ? 1 : 0);
})();
