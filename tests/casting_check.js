// Exercise the new-season button, the displayed cast, and portrait fallbacks.
const assert = require("node:assert/strict");
const { chromium } = require("playwright");
(async () => {
  const browser = await chromium.launch({ args: ["--no-sandbox"] });
  try {
    const page = await browser.newPage();
    const errors = [];
    page.on("pageerror", e => errors.push(e.message));
    await page.goto("http://127.0.0.1:8766/");
    await page.waitForSelector("#btnNewGame", { state: "visible" });
    page.on("dialog", dialog => dialog.accept(dialog.type() === "prompt" ? "1" : undefined));
    const reset = page.waitForResponse(r => r.url().endsWith("/api/newgame") && r.request().method() === "POST");
    await page.click("#btnNewGame");
    assert.equal((await (await reset).json()).ok, true);
    await page.waitForFunction(() => S.status && S.status.next_day === 1 && S.W && Object.keys(S.W.characters).length === 8);
    const cast = await page.evaluate(() => S.W.characters);
    assert.equal(Object.values(cast).filter(c => (c.casting_slot || c.gender) === "female").length, 4);
    assert.equal(Object.values(cast).filter(c => (c.casting_slot || c.gender) === "male").length, 4);
    assert.equal(new Set(Object.values(cast).map(c => c.home)).size, 8);
    const world = await (await page.request.get("http://127.0.0.1:8766/api/world")).json();
    assert.deepEqual(Object.keys(cast), Object.keys(world.characters));
    for (const id of ["itsumi", "tsutsumi", "soura", "akira", "nao", "ivette", "reiko", "accio", "jackal", "vincent", "nathan", "katsuo"]) {
      const response = await page.request.get(`http://127.0.0.1:8766/portraits/${id}.png`);
      assert.equal(response.status(), 200);
      assert.match(response.headers()["content-type"], /^image\//);
    }
    await page.reload();
    await page.waitForFunction(() => S.W && Object.keys(S.W.characters).length === 8);
    assert.deepEqual(await page.evaluate(() => Object.keys(S.W.characters)), Object.keys(cast));
    assert.deepEqual(errors, []);
    console.log("New-season casting, persistent roster and portrait fallback checks passed");
  } finally {
    await browser.close();
  }
})().catch(e => { console.error(e); process.exitCode = 1; });
