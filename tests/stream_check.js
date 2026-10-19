// Streaming check (phase F5): with a slow mock model the viewer catches up with the engine, and should play each block piece by piece as it is made instead of
// waiting for the whole block. Start the server with a slow mock, on a scratch data directory:
//   MC_MOCK_LATENCY=4 MC_DATA_DIR=/tmp/mc_stream python server.py --no-browser &      then      node tests/stream_check.js
// Reports how many blocks were started from a piece, the longest the map stood still while the viewer was waiting, and script errors.
const pw = (() => { try { return require("playwright"); } catch (e) { return require(require("path").join(process.execPath, "..", "..", "lib", "node_modules", "playwright")); } })();
(async () => {
  const b = await pw.chromium.launch({ args: ["--no-sandbox"] });
  const p = await b.newPage({ viewport: { width: 1500, height: 900 } });
  const errs = [];
  p.on("pageerror", (e) => errs.push("pageerror: " + e.message));
  p.on("console", (m) => { if (m.type() === "error" && !m.text().includes("404")) errs.push("console: " + m.text()); });
  await p.goto((process.env.MC_URL || "http://localhost:8766/") + (process.env.MC_NOSTREAM ? "?nostream" : ""));
  await p.waitForTimeout(2000);
  await p.selectOption("#backend", process.env.MC_BACKEND || "mock");
  await p.selectOption("#pace", process.env.MC_PACE || "25");
  await p.click('.opt[data-mode="live"]');
  await p.click("#btnGo");
  const secs = Number(process.env.MC_SECS || 180);
  let still = 0, longest = 0, lastM = null, waitingSamples = 0;
  const waits = {};                                                   // seconds spent waiting, by the block being waited for
  for (let i = 0; i < secs * 4; i++) {
    if (process.env.MC_UNTIL_DONE && await p.evaluate(() => S.done && S.cursor >= S.ticks.length - 1)) break;
    await p.evaluate(() => {
      const m = document.querySelector("#tmmodal"); if (m && m.style.display === "flex") { const btn = m.querySelector("button"); if (btn) btn.click(); }
      const ov = document.querySelector("#overlay"); if (ov && ov.style.display === "flex") { const c = document.querySelector("#ovClose"); if (c) c.click(); }
    });
    const s = await p.evaluate(() => ({ m: window.TileMap ? TileMap.minute() : null, cur: S.cursor, wait: document.querySelector("#wait").style.display === "block" }));
    if (s.wait) { waitingSamples++; const k = await p.evaluate(() => { const t = S.ticks[S.cursor + 1] || S.partial; return `${S.cursor + 1}${t ? " " + t.time + " " + (t.type || t.phase) : ""}`; }); waits[k] = (waits[k] || 0) + 0.25; }
    const key = `${s.cur}:${s.m}`;
    if (key === lastM && s.cur >= 0) { still++; longest = Math.max(longest, still); } else still = 0;
    lastM = key;
    await p.waitForTimeout(250);
  }
  const out = await p.evaluate(() => ({ blocksPlayed: S.cursor + 1, streamed: S.streamed || 0, generated: S.ticks.length, calls: (S.usage || {}).calls, done: S.done }));
  Object.assign(out, { longestStillSeconds: longest / 4, waitingSeconds: waitingSamples / 4, waitsByBlock: waits, errors: errs });
  console.log(JSON.stringify(out, null, 1));
  await b.close();
  process.exit(errs.length ? 1 : 0);
})();
