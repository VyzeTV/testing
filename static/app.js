"use strict";
const $ = (s) => document.querySelector(s);
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const ZONE = { roof: "#27394d", second: "#30315a", first: "#383761", ground: "#2b4a45", basement: "#3b3030", grounds: "#27432c" };
const FLOORS = [["ROOF", 55], ["2F", 175], ["1F", 335], ["GF", 495], ["B", 655]];
const WORLD_W = 1400, WORLD_H = 760;
const ORDER = ["szymon", "seul", "vixen", "noah", "ayden", "shintaro", "chloe", "cail", "neovi"];
const RED_KINDS = ["body", "trial", "deadline", "reveal", "finale", "verdict"];

const S = {
  W: null, status: null, session: null, ticks: [], cursor: -1, paused: false, speed: 1, ff: false, gm: false,
  selected: null, selRoom: null, token: 0, clock: 0, done: false, error: null, mode: null, usage: null,
  state: null, thoughts: {}, pos: {}, rad: {}, endMap: {}, moveAnim: null, bubbles: [], talkRoom: null,
  waiters: [], endShown: false, hour: 8, day: 0, step: 2, imgs: {}, view: { scale: 1, ox: 0, oy: 0 }, playIdx: -1, flashes: [], dread: 0, confessions: [], ears: [], parts: [], shakeUntil: 0, shakeAmp: 0, flash: null, weather: null, weatherRoom: null, sound: false,
};

// ---------- helpers ----------
function info(id) { return S.W.characters[id] || S.W.hosts[id] || { name: id, short: id, color: "#999" }; }
function img(id) {
  if (!S.imgs[id]) { const i = new Image(); i.src = `portraits/${id}.png`; S.imgs[id] = i; }
  return S.imgs[id];
}
function rc(rid) { const r = S.W.rooms[rid]; return [r.x + r.w / 2, r.y + r.h / 2]; }
function itemName(id) { return (S.W.items[id] || { name: id }).name; }
function isWeapon(id) { return ((S.W.items[id] || {}).tags || []).includes("weapon"); }
function esc(s) { return String(s).replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c])); }
function bcList(t) { return t.broadcasts || (t.broadcast ? [t.broadcast] : []); }
function orderIdx(id) {
  const k = ORDER.indexOf(id);
  if (k >= 0) return k;
  return 20 + Object.keys(S.W.characters).indexOf(id);
}
function alive(a) { return !a.status || a.status === "alive"; }

// Arrange occupants of each room on a small grid. map: id -> room id. Returns {pos, rad}.
function slots(map) {
  const byRoom = {};
  for (const id of Object.keys(map)) (byRoom[map[id]] = byRoom[map[id]] || []).push(id);
  const pos = {}, rad = {};
  for (const rid of Object.keys(byRoom)) {
    const r = S.W.rooms[rid];
    if (!r) continue;
    const ids = byRoom[rid].sort((a, b) => orderIdx(a) - orderIdx(b));
    const n = ids.length;
    const aw = r.w - 12, ah = r.h - 40;
    let cols = Math.max(1, Math.min(n, Math.floor(aw / 34)));
    let rows = Math.ceil(n / cols);
    while (rows * 34 > ah && cols < n) { cols++; rows = Math.ceil(n / cols); }
    const cw = aw / cols, ch = ah / rows;
    const rr = Math.max(9, Math.min(16, cw / 2 - 1, ch / 2 - 1));
    ids.forEach((id, k) => {
      const c = k % cols, rw = Math.floor(k / cols);
      const inRow = rw === rows - 1 ? n - rw * cols : cols;
      const off = (cols - inRow) * cw / 2;
      pos[id] = [r.x + 6 + off + cw * (c + 0.5), r.y + 32 + ch * (rw + 0.5)];
      rad[id] = rr;
    });
  }
  return { pos, rad };
}

function homeMap() {
  const m = {};
  for (const [id, c] of Object.entries(S.W.characters)) if (!c.status || c.status === "alive") m[id] = c.home;
  m.neovi = "laundry";
  return m;
}
function mapFromState(st) {
  const m = {};
  for (const [id, a] of Object.entries(st.agents)) if (alive(a)) m[id] = a.room;
  for (const [id, n] of Object.entries(st.npcs || {})) if (S.W.rooms[n.room]) m[id] = n.room;
  return m;
}
function setPositions(map) {
  const s = slots(map);
  S.endMap = map; S.pos = s.pos; S.rad = s.rad;
}

// ---------- clock and waiting (pause and speed aware) ----------
function waitClock(ms) {
  if (S.ff) return Promise.resolve();
  return new Promise((res) => S.waiters.push({ t: S.clock + ms, res }));
}
// The logic clock runs on a timer (not on display frames) so playback stays real-time even if rendering is throttled.
let lastStep = performance.now();
function clockStep() {
  const now = performance.now();
  const dt = Math.min(1500, now - lastStep); lastStep = now;
  if (!S.paused) S.clock += dt * S.speed;
  const keep = [];
  for (const w of S.waiters) { if (S.ff || S.clock >= w.t) w.res(); else keep.push(w); }
  S.waiters = keep;
}
setInterval(clockStep, 40);
function frame() {
  if (S.freeTick && S.freeTick.hold != null) S.curMin = S.freeTick.hold;
  else if (S.freeTick) { const f = S.freeTick; S.curMin = Math.max(0, Math.min(f.dur, (S.clock - f.start) / f.per)); if (S.mapMode === "tiles" && window.TileMap && TileMap.ready() && !S.tileAnim) TileMap.setMinute(S.curMin); }
  else if (S.mapMode === "tiles" && window.TileMap && TileMap.ready()) S.curMin = TileMap.minute();
  if (S.tileAnim && window.TileMap) { const a = S.tileAnim, k = Math.max(0, Math.min(1, (S.clock - a.start) / a.dur)); TileMap.setMinute(a.from + (a.to - a.from) * k); }
  if (S.mapMode === "tiles" && window.TileMap && TileMap.ready()) TileMap.draw(); else draw();
  requestAnimationFrame(frame);
}
S.pace = (() => { try { return Number(localStorage.getItem("mcPace")) || 50; } catch (e) { return 50; } })();      // real seconds per game hour in a free-time block
S.rosterOn = (() => { try { const v = localStorage.getItem("mcRoster"); return v === null ? null : v === "1"; } catch (e) { return null; } })();
S.said = {}; S.freeTick = null; S.curMin = 0;
// The island is drawn as the tile map; the old room schematic only stands in when the tile map cannot load. The tile map is told the turn and the minute within it.
S.mapMode = "tiles";
function setMapMode(m) {
  const tiles = m === "tiles" && window.TileMap && TileMap.ready();
  S.mapMode = tiles ? "tiles" : "rooms";
  $("#map").style.display = tiles ? "none" : "block"; if (window.TileMap && TileMap.ready()) TileMap.show(tiles);
}
const onTiles = () => S.mapMode === "tiles" && window.TileMap && TileMap.ready();
function tileTo(m, ms) { if (!window.TileMap || S.mapMode !== "tiles") return; const from = S.tileAnim ? TileMap.minute() : TileMap.minute(); S.tileAnim = { start: S.clock, dur: Math.max(60, ms), from, to: m }; }

// ---------- drawing ----------
const cv = $("#map"), ctx = cv.getContext("2d");
function resize() {
  const r = cv.parentElement.getBoundingClientRect();
  const dpr = window.devicePixelRatio || 1;
  cv.width = Math.floor(r.width * dpr); cv.height = Math.floor(r.height * dpr);
  const scale = Math.min(r.width / WORLD_W, r.height / WORLD_H);
  S.view = { scale, ox: (r.width - WORLD_W * scale) / 2, oy: (r.height - WORLD_H * scale) / 2, dpr };
}
window.addEventListener("resize", resize);

function along(p, t) {
  const d = p.total * t;
  for (let i = 1; i < p.pts.length; i++) {
    if (d <= p.cum[i] || i === p.pts.length - 1) {
      const seg = p.cum[i] - p.cum[i - 1] || 1;
      const f = Math.max(0, Math.min(1, (d - p.cum[i - 1]) / seg));
      return [p.pts[i - 1][0] + (p.pts[i][0] - p.pts[i - 1][0]) * f, p.pts[i - 1][1] + (p.pts[i][1] - p.pts[i - 1][1]) * f];
    }
  }
  return p.pts[p.pts.length - 1];
}
function agentPos(id) {
  const m = S.moveAnim;
  if (m && m.paths[id]) {
    const t = Math.max(0, Math.min(1, (S.clock - m.start) / m.dur));
    return along(m.paths[id], t * t * (3 - 2 * t));
  }
  return S.pos[id];
}
function wrap(text, maxW) {
  const words = text.split(" "), lines = []; let cur = "";
  for (const w of words) {
    const t = cur ? cur + " " + w : w;
    if (ctx.measureText(t).width > maxW && cur) { lines.push(cur); cur = w; } else cur = t;
  }
  if (cur) lines.push(cur);
  return lines;
}

function draw() {
  if (!S.W) return;
  const v = S.view;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = "#0f1016"; ctx.fillRect(0, 0, cv.width, cv.height);
  const shk = S.clock < S.shakeUntil ? S.shakeAmp * (S.shakeUntil - S.clock) / 700 : 0;
  ctx.setTransform(v.dpr * v.scale, 0, 0, v.dpr * v.scale, (v.ox + (Math.random() - 0.5) * shk) * v.dpr, (v.oy + (Math.random() - 0.5) * shk) * v.dpr);
  const st = S.state;
  ctx.fillStyle = "#14161f"; ctx.strokeStyle = "#252a3c"; ctx.lineWidth = 2;
  roundRect(30, 8, 860, 736, 14); ctx.fill(); ctx.stroke();
  roundRect(900, 8, 495, 736, 14); ctx.fill(); ctx.stroke();
  ctx.fillStyle = "#4a5070"; ctx.font = "bold 11px system-ui"; ctx.textAlign = "center";
  for (const [lbl, y] of FLOORS) { ctx.save(); ctx.translate(20, y); ctx.rotate(-Math.PI / 2); ctx.fillText(lbl, 0, 0); ctx.restore(); }
  ctx.lineWidth = 1.5; ctx.strokeStyle = "rgba(255,255,255,.07)";
  for (const e of S.W.edges) {
    if (e.hidden) continue;
    const a = rc(e.a), b = rc(e.b);
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
  }
  const found = st ? st.found_edges : [];
  if (st && st.built && st.built.length) {
    ctx.lineWidth = 3; ctx.strokeStyle = "#ffb347";
    for (const b of st.built) {
      const a = rc(b.a), c2 = rc(b.b);
      ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(c2[0], c2[1]); ctx.stroke();
      ctx.fillStyle = "#ffb347"; ctx.font = "bold 10px system-ui"; ctx.textAlign = "center";
      ctx.fillText(b.kind, (a[0] + c2[0]) / 2, (a[1] + c2[1]) / 2 - 5);
    }
  }
  ctx.setLineDash([6, 5]); ctx.lineWidth = 2;
  for (const e of S.W.edges) {
    if (!e.hidden) continue;
    const known = found.includes(e.id);
    if (!known && !S.gm) continue;
    const a = rc(e.a), b = rc(e.b);
    ctx.strokeStyle = known ? "#ff5fa2" : "rgba(255,95,162,.35)";
    ctx.beginPath(); ctx.moveTo(a[0], a[1]); ctx.lineTo(b[0], b[1]); ctx.stroke();
    ctx.setLineDash([]); ctx.fillStyle = ctx.strokeStyle; ctx.font = "bold 10px system-ui";
    ctx.fillText(e.id, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2 - 4); ctx.setLineDash([6, 5]);
  }
  ctx.setLineDash([]);
  const unlocked = st ? st.unlocked : [];
  const lockedRooms = {};
  for (const e of S.W.edges) if (e.locked && !e.hidden && !unlocked.includes(e.id)) lockedRooms[e.b] = true;
  const brokenRooms = {}, barredRooms = {}, keyedRooms = {};
  if (st) for (const r of (st.keyed_locks || [])) keyedRooms[r] = true;
  if (st) { for (const r of Object.keys(st.locks || {})) lockedRooms[r] = true; for (const r of (st.broken_doors || [])) brokenRooms[r] = true; for (const b of (st.barricades || [])) barredRooms[b.inside] = true; }
  const cs = st && st.case;
  for (const [rid, r] of Object.entries(S.W.rooms)) {
    if (r.secret && !S.gm && !(st && st.found_edges.includes("SP-5"))) continue;
    const talk = S.talkRoom === rid, sel = S.selRoom === rid;
    ctx.fillStyle = ZONE[r.zone] || "#333";
    roundRect(r.x, r.y, r.w, r.h, 8); ctx.fill();
    const crime = cs && cs.room === rid && (cs.announced || S.gm);
    ctx.lineWidth = talk || sel || crime ? 3 : 1.5;
    ctx.strokeStyle = crime ? "#ff4d6d" : talk ? "#3ee0d0" : sel ? "#ffffff" : "rgba(255,255,255,.14)"; ctx.stroke();
    ctx.fillStyle = "rgba(255,255,255,.82)"; ctx.font = "600 11px system-ui"; ctx.textAlign = "left";
    ctx.fillText((keyedRooms[rid] ? "⛓ " : lockedRooms[rid] ? "\u{1F512} " : "") + (barredRooms[rid] ? "\u{1F6A7} " : "") + (brokenRooms[rid] ? "\u{1F4A5} " : "") + r.name, r.x + 7, r.y + 16);
    const blood = st && st.blood ? st.blood[rid] || 0 : 0;
    if (blood > 0) {
      ctx.fillStyle = "rgba(190,20,40,.75)";
      for (let i = 0; i < Math.min(blood, 6); i++) { ctx.beginPath(); ctx.arc(r.x + 12 + i * 9, r.y + r.h - 12 - (i % 2) * 5, 2.5 + (i % 3) * 0.6, 0, 6.283); ctx.fill(); }
    }
    const items = st && st.room_items[rid] ? Object.keys(st.room_items[rid]).length : 0;
    if (items) {
      ctx.fillStyle = "rgba(255,255,255,.5)"; ctx.font = "10px system-ui"; ctx.textAlign = "right";
      ctx.fillText(items + " item types", r.x + r.w - 6, r.y + r.h - 6);
    }
    if (S.gm && st && st.hidden_items && st.hidden_items[rid]) {
      ctx.fillStyle = "#ffb347"; ctx.font = "10px system-ui"; ctx.textAlign = "left";
      ctx.fillText("★ hidden", r.x + 7, r.y + r.h - 6);
    }
    if (st && st.bodies) {
      st.bodies.filter((b) => b.room === rid).forEach((b, k) => {
        ctx.font = "15px system-ui"; ctx.textAlign = "center"; ctx.globalAlpha = 0.85;
        ctx.fillText("\u{1F480}", r.x + r.w - 20 - k * 20, r.y + 40); ctx.globalAlpha = 1;
      });
    }
    if (cs && cs.body && cs.room === rid && (cs.discovered > 0 || cs.announced || S.gm)) {
      const bx = r.x + r.w - 22, by = r.y + 26;
      const im = img(cs.victim);
      ctx.save(); ctx.globalAlpha = 0.55; ctx.beginPath(); ctx.arc(bx, by, 12, 0, 7); ctx.clip();
      if (im.complete && im.naturalWidth) { ctx.filter = "grayscale(1)"; ctx.drawImage(im, bx - 12, by - 12, 24, 24); }
      ctx.restore();
      ctx.font = "16px system-ui"; ctx.textAlign = "center"; ctx.fillText("\u{1F480}", bx, by + 6);
    }
  }
  const ids = Object.keys(S.pos).sort((a, b) => (agentPos(a) || [0, 0])[1] - (agentPos(b) || [0, 0])[1]);
  for (const id of ids) {
    const p = agentPos(id); if (!p) continue;
    const r = S.rad[id] || 14, c = info(id).color;
    ctx.save(); ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 7); ctx.clip();
    if (st && st.agents[id] && st.agents[id].hiding) ctx.globalAlpha = 0.35;
    else if (st && st.agents[id] && st.agents[id].out) ctx.globalAlpha = 0.5;
    const im = img(id);
    if (im.complete && im.naturalWidth) ctx.drawImage(im, p[0] - r, p[1] - r, 2 * r, 2 * r);
    else { ctx.fillStyle = c; ctx.fill(); ctx.fillStyle = "#000"; ctx.font = "bold 12px system-ui"; ctx.textAlign = "center"; ctx.fillText((info(id).short || "?")[0], p[0], p[1] + 4); }
    ctx.restore();
    ctx.lineWidth = id === S.selected ? 4 : 2.5; ctx.strokeStyle = id === S.selected ? "#fff" : c;
    ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 7); ctx.stroke();
    if (st && st.agents[id] && st.agents[id].hp < 40) { ctx.strokeStyle = "#ff6b6b"; ctx.lineWidth = 1.5; ctx.beginPath(); ctx.arc(p[0], p[1], r + 3, 0, 7); ctx.stroke(); }
    ctx.font = "bold 9px system-ui"; ctx.textAlign = "center"; ctx.lineWidth = 3; ctx.strokeStyle = "#000";
    const nm = (info(id).short || info(id).name);
    ctx.strokeText(nm, p[0], p[1] + r + 10); ctx.fillStyle = "#fff"; ctx.fillText(nm, p[0], p[1] + r + 10);
    if (st && st.agents[id]) {
      const sa = st.agents[id].sanity;
      const em = sa < 10 ? "\u{1F608}" : sa < 20 ? "\u{1F92F}" : sa < 35 ? "\u{1F620}" : sa < 55 ? "\u{1F61F}" : "";
      if (em) { ctx.font = "13px system-ui"; ctx.textAlign = "center"; ctx.fillStyle = "#fff"; ctx.fillText(em, p[0] + r * 0.95, p[1] - r * 0.6); }
    }
  }
  S.flashes = S.flashes.filter((f) => S.clock < f.until);
  for (const f of S.flashes) {
    const p = agentPos(f.id); if (!p) continue;
    const r = (S.rad[f.id] || 14) + 5, on = Math.floor(S.clock / 90) % 2 === 0;
    ctx.strokeStyle = on ? "#fff36b" : "#ff9d2e"; ctx.lineWidth = 4;
    ctx.beginPath(); ctx.arc(p[0], p[1], r, 0, 7); ctx.stroke();
    ctx.font = "22px system-ui"; ctx.textAlign = "center"; ctx.fillStyle = "#fff36b";
    ctx.fillText("\u26A1", p[0] + (on ? -3 : 3), p[1] - r - 2);
  }
  S.bubbles = S.bubbles.filter((b) => S.clock < b.until);
  for (const b of S.bubbles) {
    const p = agentPos(b.id) || (b.id === "terevi" && b.room && S.W.rooms[b.room] ? [rc(b.room)[0], S.W.rooms[b.room].y + 46] : null);
    if (!p) continue;
    if (b.id === "terevi" && !agentPos(b.id)) {
      const im = img("terevi");
      ctx.save(); ctx.beginPath(); ctx.arc(p[0], p[1], 12, 0, 7); ctx.clip();
      if (im.complete && im.naturalWidth) ctx.drawImage(im, p[0] - 12, p[1] - 12, 24, 24);
      ctx.restore(); ctx.strokeStyle = "#3ee0d0"; ctx.lineWidth = 2; ctx.beginPath(); ctx.arc(p[0], p[1], 12, 0, 7); ctx.stroke();
    }
    ctx.font = b.act ? "italic 12px system-ui" : "12px system-ui";
    const lines = wrap(b.text, 190);
    const w = Math.max(...lines.map((l) => ctx.measureText(l).width)) + 16, h = lines.length * 15 + 12;
    let x = Math.max(6, Math.min(WORLD_W - w - 6, p[0] - w / 2)), y = p[1] - (S.rad[b.id] || 14) - h - 10;
    if (y < 4) y = p[1] + (S.rad[b.id] || 14) + 16;
    ctx.fillStyle = b.act ? "rgba(255,244,200,.97)" : "rgba(255,255,255,.96)"; ctx.strokeStyle = info(b.id).color; ctx.lineWidth = 2;
    ctx.setLineDash(b.act ? [4, 3] : []);
    roundRect(x, y, w, h, 9); ctx.fill(); ctx.stroke(); ctx.setLineDash([]);
    ctx.fillStyle = "#111"; ctx.textAlign = "left";
    lines.forEach((l, k) => ctx.fillText(l, x + 8, y + 17 + k * 15));
  }
  const hr = S.hour;
  const a = hr >= 22 ? 0.38 : hr >= 20 ? 0.2 : hr >= 18 ? 0.08 : 0;
  if (a) { ctx.fillStyle = `rgba(5,8,40,${a})`; ctx.fillRect(0, 0, WORLD_W, WORLD_H); }
  const dr = S.dread || 0;
  if (dr >= 2) {
    const pulse = dr >= 4 ? 0.5 + 0.5 * Math.sin(S.clock / 450) : 0.7;
    const g = ctx.createRadialGradient(WORLD_W / 2, WORLD_H / 2, WORLD_H * 0.32, WORLD_W / 2, WORLD_H / 2, WORLD_W * 0.62);
    g.addColorStop(0, "rgba(130,0,25,0)"); g.addColorStop(1, `rgba(130,0,25,${Math.min(0.6, 0.075 * dr * (0.55 + 0.45 * pulse))})`);
    ctx.fillStyle = g; ctx.fillRect(0, 0, WORLD_W, WORLD_H);
  }
  drawFx();
}
function drawFx() {
  const now = S.clock, wx = S.weather;
  if (wx === "storm") {
    ctx.fillStyle = "rgba(10,14,40,.35)"; ctx.fillRect(0, 0, WORLD_W, WORLD_H);
    ctx.strokeStyle = "rgba(180,200,255,.5)"; ctx.lineWidth = 1.2; ctx.beginPath();
    for (let i = 0; i < 140; i++) { const x = ((i * 97 + now * 0.6) % (WORLD_W + 200)) - 100, y = ((i * 53 + now * 1.1) % (WORLD_H + 100)) - 50; ctx.moveTo(x, y); ctx.lineTo(x - 10, y + 22); }
    ctx.stroke();
    if (now % 3400 < 110) { ctx.fillStyle = "rgba(255,255,255,.35)"; ctx.fillRect(0, 0, WORLD_W, WORLD_H); }
  } else if (wx === "fog") {
    const g = ctx.createLinearGradient(0, 0, 0, WORLD_H); g.addColorStop(0, "rgba(220,230,240,.22)"); g.addColorStop(1, "rgba(220,230,240,.38)");
    ctx.fillStyle = g; ctx.fillRect(0, 0, WORLD_W, WORLD_H);
  } else if (wx === "power") {
    ctx.fillStyle = "rgba(0,0,8,.55)"; ctx.fillRect(0, 0, WORLD_W, WORLD_H);
  } else if (wx === "fire" && S.W.rooms.kitchen) {
    const r = S.W.rooms.kitchen; ctx.fillStyle = `rgba(255,120,20,${0.25 + 0.15 * Math.sin(now / 120)})`; ctx.fillRect(r.x, r.y, r.w, r.h);
    ctx.font = "22px system-ui"; ctx.textAlign = "center"; ctx.fillText("\u{1F525}", r.x + r.w / 2, r.y + r.h / 2 + 6);
  } else if (wx === "cat" && S.weatherRoom && S.W.rooms[S.weatherRoom]) {
    const [cx, cy] = rc(S.weatherRoom); ctx.font = "22px system-ui"; ctx.textAlign = "center"; ctx.fillText("\u{1F408}", cx, cy + 8);
  }
  if (S.flash && now < S.flash.until) {
    ctx.fillStyle = S.flash.color.replace("A", String((0.45 * (S.flash.until - now) / S.flash.dur).toFixed(3))); ctx.fillRect(0, 0, WORLD_W, WORLD_H);
  }
  S.parts = S.parts.filter((p) => now - p.born < p.life);
  for (const p of S.parts) {
    const age = (now - p.born) / 1000, x = p.x + p.vx * age, y = p.y + p.vy * age + 120 * age * age * p.g;
    ctx.globalAlpha = Math.max(0, 1 - (now - p.born) / p.life);
    if (p.e) { ctx.font = p.s + "px system-ui"; ctx.textAlign = "center"; ctx.fillText(p.e, x, y); } else { ctx.fillStyle = p.c; ctx.fillRect(x, y, 6, 6); }
  }
  ctx.globalAlpha = 1;
}
function triggerFx(list) {
  for (const f of list || []) {
    const room = f.room && S.W.rooms[f.room] ? S.W.rooms[f.room] : null;
    const cx = room ? room.x + room.w / 2 : WORLD_W / 2, cy = room ? room.y + room.h / 2 : WORLD_H / 2;
    if (f.kind === "shake") { S.shakeUntil = S.clock + 700; S.shakeAmp = 10; sfx("thud"); }
    else if (f.kind === "flash") { S.flash = { until: S.clock + 700, dur: 700, color: "rgba(255,40,70,A)" }; sfx("sting"); }
    else if (f.kind === "hearts") {
      for (let i = 0; i < 9; i++) S.parts.push({ x: cx + (Math.random() - 0.5) * 60, y: cy, vx: (Math.random() - 0.5) * 30, vy: -40 - Math.random() * 50, g: 0, life: 2200, born: S.clock, e: "\u2764\uFE0F", s: 14 + Math.random() * 10 });
      sfx("chime");
    } else if (f.kind === "confetti") {
      for (let i = 0; i < 40; i++) S.parts.push({ x: cx + (Math.random() - 0.5) * 80, y: cy - 20, vx: (Math.random() - 0.5) * 160, vy: -90 - Math.random() * 90, g: 1, life: 2200, born: S.clock, c: ["#ff5fa2", "#3ee0d0", "#ffd36b", "#9ec8ff", "#9fe6a0"][i % 5] });
      sfx("party");
    }
  }
}
// ---------- sound (optional, synthesized) ----------
const Voice = { on: false, list: [], byId: {}, used: { female: 0, male: 0 } };
function voiceLoad() { Voice.list = window.speechSynthesis ? speechSynthesis.getVoices().filter((v) => /^en/i.test(v.lang)) : []; }
if (window.speechSynthesis) { speechSynthesis.onvoiceschanged = voiceLoad; voiceLoad(); }
const FEM = /(zira|jenny|aria|hazel|susan|samantha|victoria|karen|moira|fiona|female|libby|sonia|natasha|clara|catherine|heera|emma|amy)/i;
const MAL = /(david|mark|guy|daniel|alex|george|ryan|james|male|thomas|oliver|christopher|eric|liam|brian|richard|ravi)/i;
function voiceFor(id) {
  if (Voice.byId[id]) return Voice.byId[id];
  const host = id === "terevi" || id === "neovi";
  const g = host ? "female" : ((S.W.characters[id] || {}).gender || "female");
  const pool = Voice.list.filter((v) => (g === "female" ? FEM : MAL).test(v.name));
  const base = pool.length ? pool : Voice.list;
  const h = Math.abs([...id].reduce((a, c) => a * 31 + c.charCodeAt(0), 7));
  const voice = base.length ? base[(host ? 0 : Voice.used[g]++) % base.length] : null;
  let pitch = 0.85 + (h % 40) / 100, rate = 0.95 + (h % 15) / 100;
  if (id === "terevi") { pitch = 0.62; rate = 0.86; }
  if (id === "neovi") { pitch = 1.25; rate = 0.84; }
  return (Voice.byId[id] = { voice, pitch, rate });
}
function speak(id, text, opts) {
  if (!Voice.on || !window.speechSynthesis || S.ff || !text) return Promise.resolve();
  return new Promise((res) => {
    const u = new SpeechSynthesisUtterance(String(text).replace(/\s+/g, " "));
    const v = voiceFor(id);
    if (v.voice) u.voice = v.voice;
    u.pitch = v.pitch; u.rate = Math.min(2, v.rate * ((opts && opts.rate) || 1) * Math.min(1.8, S.speed));
    const done = () => res();
    u.onend = done; u.onerror = done;
    setTimeout(done, Math.max(5000, String(text).length * 110));
    speechSynthesis.cancel();
    speechSynthesis.speak(u);
  });
}
function stopSpeech() { if (window.speechSynthesis) speechSynthesis.cancel(); }
const Snd = { ctx: null, drone: null, gain: null };
function sndInit() {
  if (Snd.ctx) return;
  try { Snd.ctx = new (window.AudioContext || window.webkitAudioContext)(); } catch (e) { Snd.ctx = null; }
}
function setDrone() {
  if (!Snd.ctx) return;
  if (!S.sound) { if (Snd.gain) Snd.gain.gain.value = 0; return; }
  if (!Snd.drone) {
    Snd.drone = Snd.ctx.createOscillator(); Snd.gain = Snd.ctx.createGain(); Snd.drone.type = "sine"; Snd.drone.frequency.value = 52;
    Snd.gain.gain.value = 0; Snd.drone.connect(Snd.gain); Snd.gain.connect(Snd.ctx.destination); Snd.drone.start();
  }
  Snd.gain.gain.value = Math.min(0.09, 0.012 * (S.dread || 0));
}
function sfx(kind) {
  if (!S.sound || !Snd.ctx) return;
  const c = Snd.ctx, t = c.currentTime;
  const tone = (f, d, type, v, slideTo, delay) => {
    const o = c.createOscillator(), g = c.createGain(), t0 = t + (delay || 0);
    o.type = type || "sine"; o.frequency.setValueAtTime(f, t0);
    if (slideTo) o.frequency.exponentialRampToValueAtTime(slideTo, t0 + d);
    g.gain.setValueAtTime(v || 0.12, t0); g.gain.exponentialRampToValueAtTime(0.0001, t0 + d);
    o.connect(g); g.connect(c.destination); o.start(t0); o.stop(t0 + d + 0.02);
  };
  if (kind === "thud") tone(90, 0.35, "triangle", 0.4, 40);
  else if (kind === "heartbeat") { tone(70, 0.2, "sine", 0.5, 45); tone(70, 0.2, "sine", 0.4, 45, 0.3); tone(70, 0.2, "sine", 0.5, 45, 1.1); tone(70, 0.2, "sine", 0.4, 45, 1.4); }
  else if (kind === "sting") { tone(220, 0.5, "sawtooth", 0.1, 110); tone(233, 0.5, "sawtooth", 0.08, 117); }
  else if (kind === "chime") { tone(660, 0.6, "sine", 0.1); tone(990, 0.7, "sine", 0.07, null, 0.12); }
  else if (kind === "party") [523, 659, 784, 1046].forEach((f, i) => tone(f, 0.25, "triangle", 0.1, null, i * 0.09));
  else if (kind === "boom") tone(60, 1.2, "sine", 0.5, 28);
  else if (kind === "betray") { tone(440, 0.8, "sawtooth", 0.1, 220); tone(415, 0.8, "sawtooth", 0.08, 207, 0.05); }
  else if (kind === "madness") { tone(311, 0.9, "square", 0.05, 233); tone(330, 0.9, "square", 0.05, 247, 0.1); }
  else if (kind === "cry") { tone(880, 0.12, "square", 0.12, 1320); tone(196, 0.35, "sawtooth", 0.12, 98, 0.08); }
  else if (kind === "reveal") { tone(330, 0.15, "sine", 0.1); tone(392, 0.15, "sine", 0.1, null, 0.12); tone(494, 0.4, "sine", 0.12, null, 0.24); }
}
function eventSfx(e) {
  if (e.type === "betrayal") sfx("betray");
  else if (e.type === "madness") sfx("madness");
  else if (e.type === "leak") sfx("reveal");
  else if (e.type === "island") sfx("boom");
}
// ---------- relationship web ----------
function renderWeb() {
  const el = $("#webWrap"), st = S.state;
  renderBoard(); renderStats(); renderChronicle();
  if (!st) { el.innerHTML = '<i style="color:var(--muted)">Start a day to see the web.</i>'; return; }
  const ids = Object.keys(st.agents).filter((id) => alive(st.agents[id])).sort((a, b) => orderIdx(a) - orderIdx(b));
  const n = ids.length, cx = 180, cy = 180, R = 132, pos = {};
  ids.forEach((id, i) => { const ang = -Math.PI / 2 + (i * 2 * Math.PI) / Math.max(1, n); pos[id] = [cx + R * Math.cos(ang), cy + R * Math.sin(ang)]; });
  let edges = "", marks = "";
  for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) {
    const A = ids[i], B = ids[j], a = st.agents[A].aff[B] || 0, b = st.agents[B].aff[A] || 0, avg = (a + b) / 2;
    const bond = (st.bonds || []).find((x) => (x.a === A && x.b === B) || (x.a === B && x.b === A));
    if (Math.abs(avg) < 2 && !bond) continue;
    const col = avg >= 0 ? "#6be38f" : "#ff6b6b", w = 1 + Math.min(5, Math.abs(avg) / 2);
    edges += `<line x1="${pos[A][0]}" y1="${pos[A][1]}" x2="${pos[B][0]}" y2="${pos[B][1]}" stroke="${col}" stroke-width="${w}" opacity="0.75" ${Math.abs(a - b) >= 4 ? 'stroke-dasharray="5 4"' : ""}/>`;
    if (bond) marks += `<text x="${(pos[A][0] + pos[B][0]) / 2}" y="${(pos[A][1] + pos[B][1]) / 2 + 4}" style="font-size:14px;stroke-width:0">${bond.kind === "romance" ? "\u2665" : bond.kind === "feud" ? "\u2694" : "\u{1F91D}"}</text>`;
  }
  const nodes = ids.map((id, i) => {
    const [x, y] = pos[id], sa = st.agents[id].sanity, ring = sa < 20 ? "#ff5f5f" : sa < 55 ? "#ffd36b" : "#6be38f";
    return `<g class="node" onclick="selectChar('${id}')"><clipPath id="wc${i}"><circle cx="${x}" cy="${y}" r="20"/></clipPath>
      <circle cx="${x}" cy="${y}" r="23" fill="${info(id).color}" stroke="${ring}" stroke-width="4"/>
      <image href="portraits/${id}.png" x="${x - 20}" y="${y - 20}" width="40" height="40" clip-path="url(#wc${i})" preserveAspectRatio="xMidYMid slice"/>
      <text x="${x}" y="${y + 36}">${esc(info(id).short || id)}</text></g>`;
  }).join("");
  const fac = (st.factions || []).map((f) => `<span class="pill">${esc(f.name)}</span>`).join("");
  el.innerHTML = `<svg viewBox="0 0 360 360">${edges}${marks}${nodes}</svg>` + (fac ? `<div class="row">Alliances: ${fac}</div>` : "");
}
function selectChar(id) { S.selected = id; setTab("cast"); renderCast(); }

// ---------- tension ----------
function tensionValue(st) {
  const ags = Object.values(st.agents).filter(alive);
  if (!ags.length) return 0;
  const avg = ags.reduce((s, a) => s + a.sanity, 0) / ags.length, mad = ags.filter((a) => a.sanity < 35).length;
  let haters = 0;
  for (const a of ags) for (const v of Object.values(a.aff || {})) if (v <= -4) haters++;
  return Math.max(0, Math.min(100, Math.round((S.dread || 0) * 8 + (100 - avg) * 0.35 + mad * 4 + haters * 1.5)));
}
function roundRect(x, y, w, h, r) {
  ctx.beginPath(); ctx.moveTo(x + r, y); ctx.arcTo(x + w, y, x + w, y + h, r); ctx.arcTo(x + w, y + h, x, y + h, r);
  ctx.arcTo(x, y + h, x, y, r); ctx.arcTo(x, y, x + w, y, r); ctx.closePath();
}

// ---------- feed ----------
const feed = $("#feed");
function feedAdd(html, cls) {
  const near = feed.parentElement.scrollHeight - feed.parentElement.scrollTop - feed.parentElement.clientHeight < 120;
  const d = document.createElement("div"); d.className = cls || ""; d.innerHTML = html; feed.appendChild(d);
  while (feed.children.length > 900) feed.removeChild(feed.firstChild);
  if (near) feed.parentElement.scrollTop = feed.parentElement.scrollHeight;
  return d;
}
function feedTime(t) { feedAdd(`Day ${t.day} · ${t.time} · ${t.phase}`, "time"); }
function feedBroadcast(b) { feedAdd(`<div class="n">TereVi, ${b.kind === "tease" ? "on the monitor" : esc(b.kind) + " broadcast"}</div>${esc(b.text)}`, "bc"); }
function feedEvent(e) {
  if (e.type === "arrive") return;
  const d = feedAdd(esc(e.text) + (e.vis === "gm" ? " [GM]" : ""), "event" + (e.vis === "gm" ? " gm" : "") + (e.type === "punish" ? " punish" : "") + (["occasion", "tease", "experiment", "mercy", "assault", "outburst", "madness", "betrayal", "leak", "sabotage", "island", "drive", "plot", "incite", "rumor", "build", "mishap", "director", "hide", "stash", "conceal", "frisk", "withhold", "friction", "reaction", "vigil", "door", "breakin", "craft", "alliance", "betrayal", "hook", "rifle", "inspection", "condition", "faint", "treat", "carry", "rob", "frame"].includes(e.type) ? " " + e.type : ""));
  // clicking an event shows where it happened
  if (d && (e.room || e.who)) { d.classList.add("goto"); d.title = "Show on the map"; d.onclick = () => { if (!onTiles()) return; if (e.who && S.W.characters[e.who] && e.type !== "death") TileMap.focusOn(e.who); else if (e.room) TileMap.focusRoom(e.room); }; }
}
function feedRecap(r) {
  const aw = (r.awards || []).map((a) => `${esc(a.title)}: <b>${esc(info(a.who).short || a.who)}</b> (${esc(a.why)})`).join("<br>");
  feedAdd(`<div class="n">Episode recap \u00b7 ${esc(r.title)}</div>${esc(r.recap)}${aw ? "<div style='margin-top:6px;font-style:normal'>" + aw + "</div>" : ""}`, "recap");
}
function feedConf(c) {
  const i = info(c.id);
  feedAdd(`<div class="n">Confessional · ${esc(i.name)}</div>${esc(c.text)}`, "conf");
}
function feedLine(id, text, kind, heard) {
  const i = info(id);
  const ov = heard && S.gm ? Object.entries(heard).filter(([, v]) => v !== "saw").map(([c, v]) => `${info(c).short || c}${v === "part" ? " (in part)" : ""}`) : [];
  if (ov.length) text = text + `  [overheard by ${ov.join(", ")}]`;
  if (kind === "act") { feedAdd(`<b style="--c:${i.color}">${esc(i.short || i.name)}</b> ${esc(text)}`, "actrow"); return; }
  feedAdd(`<img src="portraits/${id}.png" onerror="this.style.visibility='hidden'" style="--c:${i.color}"><div><div class="n" style="--c:${i.color}">${esc(i.name)}</div>${esc(text)}</div>`, "line");
}
function feedVote(v) {
  feedAdd(`${esc(info(v.voter).short)} votes for <b>${esc(info(v.target).short)}</b>${v.reason ? ": " + esc(v.reason) : ""}`, "vote");
}
function feedRule(ra) {
  feedAdd(`<div class="n">RULE OF THE DAY: ${esc(ra.title)}</div>${esc(ra.text)}`, "bc");
}
function feedExec(ex) {
  const label = ex.reason === "verdict" ? "EXECUTION (verdict)" : ex.reason === "wrongful" ? "WRONGFUL EXECUTION" : "EXECUTION (deadline)";
  feedAdd(`<div class="n">${label}: ${esc(info(ex.id).name)}</div>${esc(ex.scene)}`, "ex");
}
function feedEscape(es) { feedAdd(`<div class="n">THE KILLER ESCAPES: ${esc(info(es.id).name)}</div>${esc(es.text)}`, "ex"); }
function rebuildFeed(upTo) {
  feed.innerHTML = ""; S.confessions = [];
  for (let k = 0; k <= upTo; k++) feedTickInstant(S.ticks[k]);
}
function feedTickInstant(t) {
  feedTime(t);
  bcList(t).forEach(feedBroadcast);
  if (t.rule_announce) feedRule(t.rule_announce);
  t.events.forEach(feedEvent);
  t.talk.forEach((g) => g.lines.forEach((l) => feedLine(l.speaker, l.text, l.kind)));
  (t.confessionals || []).forEach((c) => { feedConf(c); S.confessions.push({ ...c, day: t.day, time: t.time }); });
  if (t.recap) feedRecap(t.recap);
  if (t.trial) t.trial.votes.forEach(feedVote);
  if (t.execution) feedExec(t.execution);
  if (t.escape) feedEscape(t.escape);
}

// ---------- playback ----------
function buildPaths(t) {
  const startMap = {}, endMap = {};
  for (const [id, m] of Object.entries(t.moves)) { startMap[id] = m.from; endMap[id] = m.to; }
  const s0 = slots(startMap), s1 = slots(endMap);
  const paths = {};
  for (const [id, m] of Object.entries(t.moves)) {
    const pts = [s0.pos[id]];
    for (let k = 1; k < m.path.length - 1; k++) pts.push(rc(m.path[k]));
    pts.push(s1.pos[id]);
    const cum = [0];
    for (let k = 1; k < pts.length; k++) cum.push(cum[k - 1] + Math.hypot(pts[k][0] - pts[k - 1][0], pts[k][1] - pts[k - 1][1]));
    paths[id] = { pts, cum, total: cum[cum.length - 1] || 1 };
  }
  return { paths, s1, endMap };
}
function applyState(t) {
  if (window.TileMap && S.mapMode === "tiles") { S.tileAnim = null; TileMap.setTick(t, t.live ? t.live.dur : 120); }
  S.state = t.state; S.hour = t.hour; S.day = t.day; S.thoughts = t.thoughts || {}; S.dread = t.dread || 0;
  if ($("#tab-chron") && $("#tab-chron").classList.contains("on")) renderChronicle();
  S.weather = t.island ? t.island.id : null; S.weatherRoom = t.island ? t.island.room : null;
  setPositions(mapFromState(t.state));
  renderCast(); renderRoom(); renderBooth(); renderWeb();
}
function hideScene() { $("#scene").style.display = "none"; $("#banner").style.display = "none"; }
async function showBroadcast(b, tok) {
  $("#bannerImg").src = "portraits/terevi.png";
  $("#bannerWho").textContent = b.kind === "tease" ? "TereVi · on the monitor" : "TereVi · " + b.kind + " broadcast";
  $("#bannerTxt").textContent = b.text;
  $("#banner").classList.toggle("red", RED_KINDS.includes(b.kind));
  $("#banner").classList.toggle("tease", b.kind === "tease");
  $("#banner").style.display = "flex";
  feedBroadcast(b);
  await Promise.all([waitClock(Math.max(2500, b.text.length * 42)), speak("terevi", b.text)]);
  if (tok === S.token) $("#banner").style.display = "none";
}
async function typeInto(el, text, tok, step, delay) {
  let i = 0;
  while (i < text.length) {
    i = Math.min(text.length, i + (step || 4));
    el.textContent = text.slice(0, i);
    await waitClock(delay || 45);
    if (tok !== S.token) return false;
  }
  return true;
}
async function playRule(ra, tok) {
  const sc = $("#scene"), titles = (S.W.rules || []).map((r) => r.title);
  sc.innerHTML = `<div class="sc"><div class="stitle" style="color:#ffd36b">THE ROULETTE SPINS</div><div class="roulette" id="roul"></div><div class="stext" id="sceneText" style="display:none"></div></div>`;
  sc.style.display = "flex";
  const el = $("#roul");
  let gap = 70;
  for (let i = 0; i < 16 && titles.length; i++) {
    el.textContent = titles[(i * 7 + Math.floor(Math.random() * 3)) % titles.length];
    await waitClock(gap); gap += 18;
    if (tok !== S.token) return;
  }
  el.textContent = ra.title; el.classList.add("done");
  const tx = $("#sceneText"); tx.style.display = ""; tx.textContent = ra.text;
  feedRule(ra);
  await waitClock(Math.max(3500, ra.text.length * 38));
  if (tok !== S.token) return;
  sc.style.display = "none";
}
async function playExecution(ex, tok) {
  sfx("boom");
  const i = info(ex.id), sc = $("#scene");
  const title = ex.reason === "verdict" ? "GUILTY · EXECUTION" : ex.reason === "wrongful" ? "WRONGFULLY CONDEMNED · EXECUTION" : "THE DEADLINE · EXECUTION";
  sc.innerHTML = `<div class="sc exec"><div class="stitle">${title}</div><img class="big shake" src="portraits/${ex.id}.png" onerror="this.style.visibility='hidden'"><div class="sname" style="color:${i.color}">${esc(i.name)}</div><div class="stext" id="sceneText"></div></div>`;
  sc.style.display = "flex";
  feedExec(ex);
  const spx = speak("terevi", ex.scene, { rate: 0.9 });
  if (!(await typeInto($("#sceneText"), ex.scene, tok, 2, 70))) return;
  await spx;
  await waitClock(2200);
  if (tok !== S.token) return;
  sc.style.display = "none";
  delete S.pos[ex.id]; delete S.endMap[ex.id];
}
async function playEscape(es, tok) {
  const i = info(es.id), sc = $("#scene");
  sc.innerHTML = `<div class="sc"><div class="stitle">THE KILLER ESCAPES</div><img class="big" src="portraits/${es.id}.png" onerror="this.style.visibility='hidden'"><div class="sname" style="color:${i.color}">${esc(i.name)}</div><div class="stext" id="sceneText"></div></div>`;
  sc.style.display = "flex";
  feedEscape(es);
  if (!(await typeInto($("#sceneText"), es.text, tok))) return;
  await waitClock(2200);
  if (tok !== S.token) return;
  sc.style.display = "none";
  delete S.pos[es.id]; delete S.endMap[es.id];
}
async function playVotes(t, tok) {
  const tr = t.trial, sc = $("#scene");
  $("#tally").style.display = "none";
  sc.innerHTML = `<div class="sc"><div class="stitle">CLASS TRIAL · THE VOTE</div><div id="vrows"></div><div id="vsum"></div></div>`;
  sc.style.display = "flex";
  for (const v of tr.votes) {
    const a = info(v.voter), b = info(v.target);
    const row = document.createElement("div"); row.className = "vrow"; row.style.setProperty("--c", a.color);
    row.innerHTML = `<img src="portraits/${v.voter}.png" style="--c:${a.color}" onerror="this.style.visibility='hidden'"><div class="r"><b>${esc(a.short)}</b> votes for <b>${esc(b.short)}</b>: ${esc(v.reason || "")}</div><img src="portraits/${v.target}.png" style="--c:${b.color}" onerror="this.style.visibility='hidden'">`;
    $("#vrows").appendChild(row);
    feedVote(v);
    await waitClock(1500);
    if (tok !== S.token) return;
  }
  const tally = Object.entries(tr.tally).sort((x, y) => y[1] - x[1]).map(([k, n]) => `<span style="color:${info(k).color}">${esc(info(k).short)}: ${n}</span>`).join("");
  const accused = tr.accused && tr.accused !== "nobody" ? info(tr.accused).name : null;
  const kn = tr.killer ? info(tr.killer).name : null;
  const what = tr.kind === "suicide" ? "a suicide" : tr.kind === "accident" ? "an accident" : "a death";
  const good = tr.found || tr.nobody || (!tr.killer && !tr.accused);
  const verdict = tr.found ? `${esc(accused)} is accused. CORRECT: ${esc(kn)} delivered the killing blow${tr.kind === "manslaughter" ? " (by mistake)" : ""}.`
    : tr.nobody ? `The cast says nobody is to blame. CORRECT: it was ${what}.`
      : tr.wrongful ? (kn ? `${esc(accused)} is accused. WRONG: ${esc(accused)} is innocent and will be executed, while the real culprit, ${esc(kn)}, walks free.`
        : `${esc(accused)} is accused. WRONG: nobody was guilty (it was ${what}) and ${esc(accused)} will be executed for nothing.`)
        : tr.accused === "nobody" ? `The cast says nobody is to blame. WRONG: ${esc(kn)} is responsible and walks free.`
          : kn ? `No majority. Nobody is executed, and the real culprit, ${esc(kn)}, walks free.` : `No majority. Nobody is executed (and nobody was guilty anyway).`;
  $("#vsum").innerHTML = `<div class="tally">${tally}</div><div class="verdict" style="color:${good ? "#6be38f" : "#ff8da1"}">${verdict}</div>`;
  const rep = tr.report;
  if (rep) {
    // truth against belief: what really happened, how each person voted, and who knew something and kept quiet (claimtrial.py)
    const rows = rep.rows.map((r) => `${r.right ? "\u2713" : "\u2717"} ${esc(info(r.id).short || r.id)} voted ${esc(info(r.voted).short || r.voted)}` + (r.silent ? ` (kept ${r.silent} thing${r.silent > 1 ? "s" : ""} to themselves)` : "") + (r.lied ? ` (caught lying ${r.lied}x)` : "")).join("<br>");
    feedAdd(`<b>Truth vs belief</b> \u00b7 ${rep.right}/${rep.of} voted right<br>${esc(rep.truth)}` + (S.gm ? `<br><span style="opacity:.8">${rows}</span>` : ""), "segment");
  }
  await waitClock(4000);
  if (tok !== S.token) return;
  sc.style.display = "none";
}
async function playSegment(seg, tok) {
  const sc = $("#scene"), subj = seg.subject ? info(seg.subject) : null;
  let sub = "", faces = "";
  if (seg.kind === "hotseat" && subj) { sub = `Suspicion falls on ${esc(subj.name)}`; faces = `<img class="big" src="portraits/${seg.subject}.png" onerror="this.style.visibility='hidden'" style="width:120px;height:120px">`; }
  else if ((seg.kind === "duel" || seg.kind === "closing") && seg.debaters) {
    const [a, b] = seg.debaters.length > 1 ? seg.debaters.map(info) : [info(seg.debaters[0]), info(seg.debaters[0])];
    sub = seg.kind === "closing" ? `${esc(a.name)}${seg.debaters.length > 1 ? " and " + esc(b.name) : ""}: the final plea` : `${esc(a.name)} vs ${esc(b.name)}: two ideas that cannot both be true`;
    faces = seg.debaters.map((d, i) => `<img src="portraits/${d}.png" onerror="this.style.visibility='hidden'" style="width:96px;height:96px;border-radius:50%;object-fit:cover;border:3px solid ${i ? b.color : a.color};margin:4px">`).join("");
  } else if (seg.kind === "brainstorm") sub = "Something does not add up. Ideas fly.";
  else if (seg.title === "THEORY CHOSEN") sub = "The room settles on a working theory";
  else sub = "Everyone presents what they have";
  sc.innerHTML = `<div class="sc"><div class="stitle">${esc(seg.title)}</div><div>${faces}</div><div class="stext">${sub}</div><div style="color:var(--muted);font-size:12px">Trial time: segment ${seg.n} of ${seg.of}</div></div>`;
  sc.style.display = "flex";
  feedAdd(`<div class="n">${esc(seg.title)}</div>${sub}`, "bc");
  await waitClock(2300);
  if (tok !== S.token) return;
  sc.style.display = "none";
}
async function playBodyScene(sb, tok) {
  sfx("heartbeat");
  const v = info(sb.victim), sc = $("#scene");
  sc.innerHTML = `<div class="sc dread"><div class="stitle">A BODY</div><img class="big gray" src="portraits/${sb.victim}.png" onerror="this.style.visibility='hidden'"><div class="sname" style="color:#ff8da1">${esc(v.name)}</div><div class="stext" id="sceneText"></div></div>`;
  sc.style.display = "flex";
  triggerFx([{ kind: "shake" }, { kind: "flash" }]);
  const text = `${info(sb.by).short} finds ${v.short}. ${sb.desc}`;
  if (!(await typeInto($("#sceneText"), text, tok, 2, 60))) return;
  await waitClock(2600);
  if (tok !== S.token) return;
  sc.style.display = "none";
}
async function playBattle(bt, tok) {
  sfx("boom");
  const sc = $("#scene");
  sc.innerHTML = `<div class="sc exec"><div class="stitle">THE LAST BATTLE</div><div id="brounds" style="text-align:left;max-width:520px"></div></div>`;
  sc.style.display = "flex";
  for (const r of bt.rounds) {
    const a = info(r.a), b = info(r.b), w2 = info(r.winner), l2 = r.winner === r.a ? b : a;
    const row = document.createElement("div"); row.style.margin = "8px 0";
    row.innerHTML = `<b style="color:${w2.color}">${esc(w2.name)}</b> overpowers <b style="color:${l2.color}">${esc(l2.name)}</b> and takes a savage ${r.dmg} damage doing it.`;
    $("#brounds").appendChild(row);
    sfx("thud"); triggerFx([{ kind: "shake" }]);
    await waitClock(2400);
    if (tok !== S.token) return;
  }
  const end = document.createElement("div"); end.style.marginTop = "12px";
  end.innerHTML = bt.survivors.length ? `<b>${esc(info(bt.survivors[0]).name)}</b> is the last one standing.` : "<b>Nobody is left standing.</b>";
  $("#brounds").appendChild(end);
  await waitClock(3000);
  if (tok !== S.token) return;
  sc.style.display = "none";
}
async function playRaft(rf, tok) {
  const sc = $("#scene");
  const faces = rf.ids.map((id) => `<img src="portraits/${id}.png" style="width:64px;height:64px;border-radius:50%;object-fit:cover;border:3px solid ${info(id).color};margin:3px" onerror="this.style.visibility='hidden'">`).join("");
  sc.innerHTML = `<div class="sc"><div class="stitle">THE RAFT SAILS</div><div>${faces}</div><div class="stext" id="sceneText"></div></div>`;
  sc.style.display = "flex";
  if (!(await typeInto($("#sceneText"), rf.text, tok))) return;
  await waitClock(2200);
  if (tok !== S.token) return;
  sc.style.display = "none";
  rf.ids.forEach((id) => { delete S.pos[id]; delete S.endMap[id]; });
}
async function playReckoning(rk, tok) {
  sfx("boom");
  const sc = $("#scene");
  const faces = rk.ids.map((id) => `<img src="portraits/${id}.png" style="width:64px;height:64px;border-radius:50%;object-fit:cover;border:3px solid ${info(id).color};margin:3px" onerror="this.style.visibility='hidden'">`).join("");
  sc.innerHTML = `<div class="sc"><div class="stitle">THE RECKONING</div><div>${faces}</div><div class="stext" id="sceneText"></div></div>`;
  sc.style.display = "flex";
  feedAdd(`<div class="n">THE RECKONING: nobody died, so everyone does</div>${esc(rk.scene)}`, "ex");
  if (!(await typeInto($("#sceneText"), rk.scene, tok))) return;
  await waitClock(2600);
  if (tok !== S.token) return;
  sc.style.display = "none";
  rk.ids.forEach((id) => { delete S.pos[id]; delete S.endMap[id]; });
}
function showSeasonEnd(en) {
  const faces = (en.ids || []).map((id) => `<img src="portraits/${id}.png" style="width:48px;height:48px;border-radius:50%;object-fit:cover;border:3px solid ${info(id).color};margin:2px" onerror="this.style.visibility='hidden'">`).join("");
  const truth = en.kind !== "reckoning";
  $("#overlayCard").innerHTML = `<div class="recapcard"><div class="ep">${truth ? "The season ends" : "The season is over"}</div><h2>${esc(en.title)}</h2>
    <div>${faces}</div><p>${esc(en.text)}</p>
    <p class="warn">${({ truth: "The world is listening. Rescue is on its way.", shutdown: "TereVi is gone and the doors stand open.", ultimatum: "TereVi gave in: the show is over.", raft: "The last of them sailed away.", reckoning: "Nobody died before the deadline, so everyone did." })[en.kind] || ""} Start a new game to play another season.</p></div>
    <div class="actions"><button id="ovClose">Close</button><button id="ovNext" class="primary">New game</button></div>`;
  $("#overlay").style.display = "flex";
  $("#ovClose").onclick = () => ($("#overlay").style.display = "none");
  $("#ovNext").onclick = () => { $("#overlay").style.display = "none"; openModal(); };
  refreshStatus();
}
// A booth confessional during the turn: a short card in the corner and a bubble over the person in the booth, while everybody else carries on.
function showBooth(t, c) {
  const bo = $("#booth"), i = info(c.id), lines = c.lines || [c.text];
  bo.innerHTML = `<img src="portraits/${c.id}.png" onerror="this.style.visibility='hidden'"><div><div class="rec">\u25CF REC \u00b7 CONFESSIONAL</div><div class="who" style="color:${i.color}">${esc(i.name)}</div><div class="txt">${lines.map(esc).join("<br>")}</div></div>`;
  bo.style.display = "flex";
  feedConf(c); S.confessions.push({ ...c, day: t.day, time: t.time }); renderBooth();
  const ms = Math.max(2600, lines.join(" ").length * 55);
  S.bubbles = S.bubbles.filter((b) => b.id !== c.id);
  S.bubbles.push({ id: c.id, room: c.room || null, act: false, booth: true, text: lines[0], until: S.clock + ms });
  speak(c.id, lines.join(" "), { rate: 0.95 });
  const until = S.clock + ms;
  waitClock(ms).then(() => { if (S.clock >= until - 50) bo.style.display = "none"; });
  return ms;
}
async function playConfessionals(t, tok) {
  const bo = $("#booth");
  for (const c of t.confessionals.filter((x) => x.m == null || !t._confShown)) {
    const i = info(c.id);
    bo.innerHTML = `<img src="portraits/${c.id}.png" onerror="this.style.visibility='hidden'"><div><div class="rec">\u25CF REC \u00b7 CONFESSIONAL</div><div class="who" style="color:${i.color}">${esc(i.name)}</div><div class="txt" id="boothTxt"></div></div>`;
    bo.style.display = "flex";
    feedConf(c); S.confessions.push({ ...c, day: t.day, time: t.time }); renderBooth();
    const spc = speak(c.id, c.text, { rate: 0.92 });
    if (!(await typeInto($("#boothTxt"), c.text, tok))) { bo.style.display = "none"; return; }
    await spc;
    await waitClock(1800);
    if (tok !== S.token) { bo.style.display = "none"; return; }
  }
  bo.style.display = "none";
}
function renderBooth() {
  const el = $("#boothList");
  if (!S.confessions.length) { el.innerHTML = '<i style="color:var(--muted)">Nothing recorded yet.</i>'; return; }
  el.innerHTML = S.confessions.slice().reverse().map((c) => {
    const i = info(c.id);
    return `<div class="entry"><div class="h"><img src="portraits/${c.id}.png" onerror="this.style.visibility='hidden'"> ${esc(i.name)} \u00b7 Day ${c.day}, ${esc(c.time)}</div><div class="t">${esc(c.text)}</div></div>`;
  }).join("");
}
// ---------- free-time blocks play out over real time: people walk from activity to activity, things happen at their minute, important ones pause ----------
function actAt(id, m) {
  const segs = S.freeActs && S.freeActs[id];
  if (!segs) return null;
  return segs.find((sg) => sg[0] <= m && m < sg[1]) || segs[segs.length - 1];
}
function syncSchematic(min) {
  const f = S.freeTick; if (!f) return;
  const prev = S.endMap || {}, map = { ...prev }, moves = {};
  let any = false;
  for (const [id, segs] of Object.entries(f.acts)) {
    let room = null; for (const sg of segs) if (sg[0] <= min) room = sg[4];
    if (room && map[id] !== room) { moves[id] = { from: map[id] || room, path: [map[id] || room, room], to: room }; map[id] = room; any = true; }
  }
  if (!any) return;
  if (S.moveAnim && f.pending) { S.pos = f.pending.s1.pos; S.rad = f.pending.s1.rad; S.moveAnim = null; }
  const all = {};
  for (const id of Object.keys(map)) all[id] = moves[id] || { from: map[id], path: [map[id]], to: map[id] };
  const b = buildPaths({ moves: all });
  S.moveAnim = { start: S.clock, dur: 900, paths: b.paths }; S.endMap = map; f.pending = b;
  S.pos = S.pos || b.s1.pos;
}
async function playFree(t, tok, tiles, played) {
  const live = t.live, dur = live.dur, per = Math.max(60, S.pace * 1000 / 60);
  const talkAt = live.talk && live.talk.length ? Math.min(...live.talk.map((x) => x.m)) - 1 : dur - 12;
  const endMin = Math.max(10, Math.min(dur - 2, talkAt));
  const t0 = S.clock;
  S.freeTick = { acts: live.acts, start: t0, per, dur, t, pending: null }; S.freeActs = live.acts;
  S.endMap = S.endMap || {};
  const untimed = t.events.filter((e) => e.m === undefined || e.m === null), timed = t.events.filter((e) => e.m !== undefined && e.m !== null);
  untimed.forEach((e) => { feedEvent(e); eventSfx(e); });
  if (window.TileMap) { await TileMap.dialogFor(t, { untimed: true }); if (tok !== S.token) return; }
  S.freeTick.start = S.clock;
  if (tiles) { S.tileAnim = { start: S.clock, dur: endMin * per, from: 0, to: endMin }; }
  else { syncSchematic(0); }
  const marks = [...new Set(timed.map((e) => e.m))].filter((m) => m <= endMin).sort((a, b) => a - b);
  const waitUntil = async (m) => { const rem = S.freeTick.start + m * per - S.clock; if (rem > 0) await waitClock(rem); };
  const sched = [...marks];
  for (const seg of Object.values(live.acts)) for (const sg of seg) if (sg[0] > 0 && sg[0] <= endMin) sched.push(sg[0]);
  const chats = (live.groups || []).filter((g) => g.chat && g.m <= endMin + 30 && t.talk[g.g] && t.talk[g.g].lines.length);
  for (const c of chats) sched.push(c.m);
  const times = [...new Set(sched)].sort((a, b) => a - b);
  for (const m of times) {
    await waitUntil(m); if (tok !== S.token) return;
    if (!tiles) syncSchematic(m);
    const here = timed.filter((e) => e.m === m);
    here.forEach((e) => { feedEvent(e); eventSfx(e); });
    if (here.length && window.TileMap) { await TileMap.dialogFor(t, { from: m, to: m + 0.001 }); if (tok !== S.token) return; }
    for (const c of chats.filter((x) => x.m === m)) { await playChat(t, c.g, t.talk[c.g], m, tok); if (tok !== S.token) return; played.add(c.g); }
  }
  await waitUntil(endMin); if (tok !== S.token) return;
  if (S.freeTick && S.freeTick.pending) { S.pos = S.freeTick.pending.s1.pos; S.rad = S.freeTick.pending.s1.rad; S.moveAnim = null; }
  S.tileAnim = null; if (window.TileMap) TileMap.setMinute(endMin);
  S.freeTick = null; S.curMin = endMin;
}
function roomName(id) { return (S.W.rooms[id] || {}).name || id; }
function renderRoster() {
  const box = $("#roster");
  if (!box || !$("#stage").classList.contains("roster-on") || !S.W) return;
  const st = S.state || {}, ag = st.agents || {}, m = S.curMin || 0, now = S.clock;
  const rows = Object.keys(S.W.characters).map((id) => {
    const a = ag[id]; if (!a) return "";
    const dead = (a.status || "alive") !== "alive";
    const act = !dead ? actAt(id, m) : null;
    const room = act ? act[4] : a.room;
    const said = S.said[id] && S.said[id].until > now ? S.said[id] : null;
    const label = dead ? "dead" : act ? act[3] || act[2] : (a.activity || "");
    const i = info(id);
    return `<div class="rr ${dead ? "dead" : ""} ${S.selected === id ? "sel" : ""}" data-id="${id}" style="--c:${i.color}"><img src="portraits/${id}.png" onerror="this.style.visibility='hidden'"><div><b>${esc(i.short || i.name)}</b> <span class="rm">${esc(roomName(room))}</span></div><div class="ra">${esc(String(label).slice(0, 70))}</div>${said ? `<div class="rs">${said.act ? "" : "“"}${esc(said.text.slice(0, 90))}${said.act ? "" : "”"}</div>` : ""}</div>`;
  }).join("");
  const key = rows;
  if (box._key !== key) { box.innerHTML = `<div class="rh">Who's where · ${String(Math.floor(((S.hour || 8) * 60 + m) / 60) % 24).padStart(2, "0")}:${String(Math.floor(((S.hour || 8) * 60 + m) % 60)).padStart(2, "0")}</div>` + rows; box._key = key; box.querySelectorAll(".rr").forEach((r) => (r.onclick = () => { S.selected = r.dataset.id; if (onTiles()) TileMap.focusOn(r.dataset.id); setTab("cast"); renderCast(); })); }
}
function setRoster(on) {
  S.rosterOn = !!on; try { localStorage.setItem("mcRoster", on ? "1" : "0"); } catch (e) { /* private mode */ }
  $("#stage").classList.toggle("roster-on", !!on); $("#btnRoster").classList.toggle("on", !!on); const b = $("#roster"); if (b) b._key = null;
}
setInterval(() => { try { renderRoster(); } catch (e) { /* the roster never blocks playback */ } }, 400);
async function playLine(g, l, tok) {
  if (l.move === "cry") showCry(l);
  feedLine(l.speaker, l.text, l.kind);
  const dur = Math.max(2000, l.text.length * 55);
  const isAct = l.kind === "act";
  S.bubbles = S.bubbles.filter((b) => b.id !== l.speaker);
  S.bubbles.push({ id: l.speaker, room: g.room, act: isAct, text: isAct ? `${info(l.speaker).short || ""} ${l.text}` : l.text, until: S.clock + dur + 400 });
  S.said[l.speaker] = { text: l.text, act: isAct, until: S.clock + dur + 4000 };
  await Promise.all([waitClock(dur), isAct ? Promise.resolve() : speak(l.speaker, l.text)]);
}
// ---------- continuous playback ----------
// A turn plays as one continuous stretch of game minutes at the chosen pace. Events, speech and chats happen at their minute; nobody stops while others talk. When lines come
// faster than they can be read, the clock slows down (everybody keeps moving, only slower) until the line has been on screen long enough. Pause dialogs and staged scenes
// (a body, a trial segment) still pause playback, as the pause settings say.
const readMs = (l) => Math.max(1800, (l.text || "").length * 45);
async function animateTo(m, minMs, per, tok) {
  const from = TileMap.minute();
  if (m <= from + 1e-6 && minMs <= 0) return;
  // waiting for a line to be read never stops the world: the clock creeps on (a fraction of what it would cover at full pace)
  if (minMs > 0) m = Math.max(m, from + Math.min(0.6, (minMs / per) * 0.3));
  const span = Math.max((m - from) * per, minMs);
  S.tileAnim = { start: S.clock, dur: Math.max(1, span), from, to: Math.max(from, m) };
  await waitClock(span);
  if (tok === S.token) { S.tileAnim = null; TileMap.setMinute(Math.max(from, m)); }
}
function showCry(l) {
  // "Objection!": a contradiction was caught. The speaker's cry is stamped over the map for a moment.
  const el = $("#crycard");
  el.innerHTML = `${esc(l.text)}<small>${esc((info(l.speaker).short || l.speaker).toUpperCase())}</small>`;
  el.style.display = "none"; void el.offsetWidth; el.style.display = "block";
  sfx("cry");
  clearTimeout(S.cryT); S.cryT = setTimeout(() => (el.style.display = "none"), 1300);
}
function showLine(g, l) {
  if (l.move === "cry") showCry(l);
  feedLine(l.speaker, l.text, l.kind, l.heard);
  if (l.heard) for (const [id, lvl] of Object.entries(l.heard)) S.ears.push({ id, from: l.speaker, lvl, until: S.clock + readMs(l) });
  const isAct = l.kind === "act", ms = readMs(l);
  S.bubbles = S.bubbles.filter((b) => b.id !== l.speaker);
  S.bubbles.push({ id: l.speaker, room: g.room, act: isAct, text: isAct ? `${info(l.speaker).short || ""} ${l.text}` : l.text, until: S.clock + ms + 400 });
  S.said[l.speaker] = { text: l.text, act: isAct, until: S.clock + ms + 4000 };
  if (!isAct) speak(l.speaker, l.text);
  return ms;
}
async function playWindow(t, tok, late) {
  const L = t.live, dur = L.dur, per = Math.max(40, S.pace * 1000 / 60);
  S.freeActs = L.acts && Object.keys(L.acts).length ? L.acts : null;
  TileMap.setTick(t, 0);
  const byText = {};
  for (const e of L.events || []) byText[e.text.slice(0, 200)] = e.m;
  const items = [];
  t.events.forEach((e, i) => { if (!late.includes(e)) items.push({ m: e.m != null ? e.m : (byText[e.text.slice(0, 200)] != null ? byText[e.text.slice(0, 200)] : 0), o: i, k: "ev", e }); });
  const lineIdx = {};
  (L.talk || []).forEach((x, i) => { const g = t.talk[x.g]; if (!g) return; const li = lineIdx[x.g] = (lineIdx[x.g] || 0); lineIdx[x.g]++; if (g.lines[li]) items.push({ m: x.m, o: 1000 + i, k: "line", g, l: g.lines[li], gi: x.g, first: li === 0 }); });
  t.talk.forEach((g, gi) => { if (!(gi in lineIdx)) { let m = Math.min(dur - 2, dur * 0.5 + gi); g.lines.forEach((l, li) => items.push({ m: m + li * 2, o: 2000 + gi * 100 + li, k: "line", g, l, gi, first: li === 0 })); } });
  for (const f of t.fx || []) items.push({ m: f.m != null ? f.m : 0, o: 3000, k: "fx", f });
  if (t.scene_body) { const be = t.events.find((e) => e.type === "body"); items.push({ m: be && be.m != null ? be.m + 0.05 : 1, o: 4000, k: "body" }); }
  (t.confessionals || []).forEach((c, i) => { if (c.m != null) items.push({ m: c.m, o: 5000 + i, k: "conf", c }); });
  t._confShown = true;
  items.sort((a, b) => a.m - b.m || a.o - b.o);
  t.events.filter((e) => e.m == null && !late.includes(e)).length && (await TileMap.dialogFor(t, { untimed: true }));
  if (tok !== S.token) return;
  let readUntil = S.clock, lastDlg = -1;
  const chatGroups = new Set((L.groups || []).filter((g) => g.chat).map((g) => g.g));
  for (const it of items) {
    const m = Math.min(it.m, dur - 0.05);
    await animateTo(m, it.k === "line" ? readUntil - S.clock : 0, per, tok);
    if (tok !== S.token) return;
    if (it.k === "ev") {
      feedEvent(it.e); eventSfx(it.e);
      if (it.e.type === "punish") S.flashes.push({ id: it.e.who, until: S.clock + 2200 });
      if (m > lastDlg) { await TileMap.dialogFor(t, { from: lastDlg < 0 ? 0 : lastDlg, to: m + 0.001 }); lastDlg = m + 0.001; if (tok !== S.token) return; }
    } else if (it.k === "line") {
      if (it.first) {
        S.talkRoom = it.g.room;
        if (chatGroups.has(it.gi)) { await TileMap.chatDialog(t, it.g); if (tok !== S.token) return; }
        if (it.g.segment) { await playSegment(it.g.segment, tok); if (tok !== S.token) return; renderTally(it.g.segment); }
      }
      readUntil = S.clock + showLine(it.g, it.l);
    } else if (it.k === "fx") {
      triggerFx([it.f]);
    } else if (it.k === "body") {
      await playBodyScene(t.scene_body, tok); if (tok !== S.token) return;
    } else if (it.k === "conf") {
      readUntil = Math.max(readUntil, S.clock + showBooth(t, it.c));
    }
  }
  await animateTo(dur, Math.max(0, readUntil - S.clock), per, tok);
  if (tok !== S.token) return;
  S.talkRoom = null; S.bubbles = [];
}
// A chat that starts during a free-time block is played where and when it happens: the day's clock stands still while they talk.
async function playChat(t, gi, g, minute, tok) {
  S.talkRoom = g.room;
  if (window.TileMap) { await TileMap.chatDialog(t, g); if (tok !== S.token) return; }
  const f = S.freeTick, keep = S.tileAnim, c0 = S.clock;
  if (f) f.hold = minute;
  if (keep) S.tileAnim = null;
  if (window.TileMap && S.mapMode === "tiles") TileMap.setMinute(minute);
  for (const l of g.lines) { await playLine(g, l, tok); if (tok !== S.token) return; }
  const dt = S.clock - c0;
  if (S.freeTick) { S.freeTick.start += dt; S.freeTick.hold = null; }
  if (keep) S.tileAnim = { ...keep, start: keep.start + dt };
  S.talkRoom = null; S.bubbles = [];
}
// A short title card when a new part of the day begins (free time, a gathering, night). It can be turned off in the pause settings.
async function showSegment(t, tok) {
  const m = t.segment_msg;
  if (!m || (window.TileMap && !TileMap.segMsgOn())) return;
  const hh = String(t.hour % 24).padStart(2, "0") + ":00";
  feedAdd(`<b>${esc(m.title)}</b> \u00b7 ${hh}<br><span style="opacity:.75">${esc(m.sub || "")}</span>`, "segment");
  const el = $("#segcard");
  el.innerHTML = `<div class="st">${esc(m.title)}</div><div class="ss">Day ${t.day} \u00b7 ${hh}${m.sub ? " \u00b7 " + esc(m.sub) : ""}</div>`;
  el.className = m.free ? "free" : "turn"; el.style.display = "block";
  await waitClock(m.free ? 1900 : 1500);
  if (tok === S.token) el.style.display = "none";
}
async function playTick(i, tok) {
  const t = S.ticks[i];
  S.tileAnim = null; S.freeTick = null; S.freeActs = null; if (window.TileMap) TileMap.setTick(t, 0);
  S.hour = t.hour; S.day = t.day; S.thoughts = t.thoughts || {}; S.dread = t.dread || 0;
  S.weather = t.island ? t.island.id : null; S.weatherRoom = t.island ? t.island.room : null; setDrone();
  feedTime(t); updateUI(); $("#tally").style.display = "none";
  await showSegment(t, tok); if (tok !== S.token) return;
  for (const b of bcList(t)) { await showBroadcast(b, tok); if (tok !== S.token) return; }
  if (t.rule_announce) { await playRule(t.rule_announce, tok); if (tok !== S.token) return; }
  // Result lines would spoil the verdict, so they are held back until the scene has played.
  const late = (t.trial || t.execution) ? t.events.filter((e) => e.type === "system_notable") : [];
  if (t.execution && !t.trial) { await playExecution(t.execution, tok); if (tok !== S.token) return; late.forEach(feedEvent); }
  const { paths, s1, endMap } = buildPaths(t);
  const tiles = S.mapMode === "tiles" && window.TileMap && TileMap.ready(), mdur = tiles ? 4200 : 2600;
  if (tiles && t.live && !t.live_error) {
    // the continuous player: the whole turn on one clock, talk included
    await playWindow(t, tok, late);
    if (tok !== S.token) return;
    S.pos = s1.pos; S.rad = s1.rad; S.endMap = endMap;
    if (!t.trial) { S.state = t.state; renderCast(); renderRoom(); renderWeb(); }
    return finishTick(t, tok, late);
  }
  const free = !!(t.live && t.live.segment === "free" && t.live.acts && Object.keys(t.live.acts).length);
  const played = new Set();
  if (free) {
    await playFree(t, tok, tiles, played);
    if (tok !== S.token) return;
  } else {
    S.moveAnim = { start: S.clock, dur: mdur, paths };
    t.events.filter((e) => !late.includes(e)).forEach((e) => { feedEvent(e); eventSfx(e); });
    if (tiles) { await TileMap.dialogFor(t); if (tok !== S.token) return; S.moveAnim.start = S.clock; S.tileAnim = { start: S.clock, dur: mdur, from: 0, to: 56 }; }
    await waitClock(mdur);
    if (tok !== S.token) return;
    S.tileAnim = null; if (window.TileMap) TileMap.setMinute(58);
  }
  S.moveAnim = null; S.pos = s1.pos; S.rad = s1.rad; S.endMap = endMap;
  if (!t.trial) { S.state = t.state; renderCast(); renderRoom(); renderWeb(); }
  if ((t.fx || []).length) {
    triggerFx(t.fx);
    if (t.fx.some((f) => f.kind === "shake" || f.kind === "flash")) { await waitClock(900); if (tok !== S.token) return; }
  }
  if (t.scene_body) { await playBodyScene(t.scene_body, tok); if (tok !== S.token) return; }
  const pun = t.events.filter((e) => e.type === "punish");
  if (pun.length) {
    pun.forEach((e) => S.flashes.push({ id: e.who, until: S.clock + 2200 }));
    await waitClock(1800);
    if (tok !== S.token) return;
  }
  for (let gi = 0; gi < t.talk.length; gi++) {
    const g = t.talk[gi];
    if (played.has(gi)) continue;
    const mins = t.live && t.live.talk ? t.live.talk.filter((x) => x.g === gi).map((x) => x.m) : [];
    S.talkRoom = g.room;
    if (g.segment) { await playSegment(g.segment, tok); if (tok !== S.token) return; renderTally(g.segment); }
    let li = 0;
    for (const l of g.lines) {
      if (mins[li] !== undefined) tileTo(mins[li], 500);
      li++;
      await playLine(g, l, tok);
      if (tok !== S.token) return;
    }
  }
  S.talkRoom = null; S.bubbles = []; S.freeTick = null;
  if (window.TileMap) { S.tileAnim = null; TileMap.setMinute(TileMap.duration()); }
  return finishTick(t, tok, late);
}
// What follows a turn's window: the recap, confessionals and the big staged scenes.
async function finishTick(t, tok, late) {
  if (t.recap) feedRecap(t.recap);
  if (t.confessionals && t.confessionals.length) { await playConfessionals(t, tok); if (tok !== S.token) return; }
  if (t.reckoning) { await playReckoning(t.reckoning, tok); if (tok !== S.token) return; }
  if (t.raft) { await playRaft(t.raft, tok); if (tok !== S.token) return; }
  if (t.battle) { await playBattle(t.battle, tok); if (tok !== S.token) return; }
  if (t.trial) {
    await playVotes(t, tok); if (tok !== S.token) return;
    if (t.execution) { await playExecution(t.execution, tok); if (tok !== S.token) return; }
    if (t.escape) await playEscape(t.escape, tok);
    if (tok !== S.token) return;
    late.forEach(feedEvent);
    applyState(t);
  }
  await waitClock(500);
}
function applyInstant(i) {
  const t = S.ticks[i];
  feedTickInstant(t);
  S.moveAnim = null; S.bubbles = []; S.talkRoom = null; S.freeTick = null; S.freeActs = null;
  hideScene();
  applyState(t);
}
function jumpTo(i) {
  stopSpeech();
  S.token++; S.moveAnim = null; S.bubbles = []; S.talkRoom = null; S.freeTick = null; S.freeActs = null;
  S.waiters.forEach((w) => w.res()); S.waiters = [];
  hideScene();
  S.cursor = i; S.endShown = false; $("#overlay").style.display = "none";
  rebuildFeed(i); applyState(S.ticks[i]); updateUI();
}
async function playLoop() {
  for (;;) {
    await sleep(60);
    if (!S.session) continue;
    if (S.paused) continue;
    const next = S.cursor + 1;
    if (next >= S.ticks.length) {
      if (S.done && S.ticks.length) { onDayEnd(); $("#wait").style.display = "none"; }
      else if (!S.error) {
        const w = $("#wait");
        w.textContent = S.ff ? "Fast-forwarding: the island is simulating the rest of the day..." : "The island is thinking about the next hour...";
        w.style.display = S.ticks.length || S.mode === "live" ? "block" : "none";
      }
      continue;
    }
    $("#wait").style.display = "none";
    const tok = S.token;
    S.playIdx = next;
    if (S.ff) { applyInstant(next); S.cursor = next; updateUI(); continue; }
    if (!S.ticks[next].quiet) S.skipQuiet = false;                  // the GM skip never runs past a block where something happens
    else if (await quietSkip(S.ticks[next], tok)) { if (tok === S.token) { applyInstant(next); S.cursor = next; updateUI(); } continue; }
    await playTick(next, tok);
    if (tok === S.token) { S.cursor = next; updateUI(); }
  }
}
// A night block where the whole house is asleep: skip it (the viewer's setting, the choice made for this night, or the GM's skip button) or watch it.
async function quietSkip(t, tok) {
  if (S.skipQuiet) return true;
  const mode = window.TileMap ? TileMap.quietNight() : "auto";
  if (mode === "watch") return false;
  if (S.quietChoice && S.quietChoice.day === t.day) return S.quietChoice.skip;
  if (mode === "ask") {
    const skip = await new Promise((res) => {
      TileMap.modal(`<div class="kind">Day ${t.day} ${t.time}</div><h2>The house sleeps</h2><div class="sub">Nobody is awake. Skip the quiet stretches of tonight? (Anything that happens still plays.)</div>
        <div class="btns"><button class="pri" id="qnSkip">Skip quiet stretches</button><button id="qnWatch">Watch the night</button></div>
        <div class="sub" style="margin-top:6px"><label><input type="checkbox" id="qnKeep"> Remember my choice (change it in the pause settings)</label></div>`);
      const was = S.paused; S.paused = true;
      const done = (v) => { if ($("#qnKeep").checked) TileMap.setQuietNight(v ? "auto" : "watch"); TileMap.closeModal(); S.paused = was; res(v); };
      $("#qnSkip").onclick = () => done(true);
      $("#qnWatch").onclick = () => done(false);
    });
    S.quietChoice = { day: t.day, skip };
    if (!skip) return false;
  }
  await houseSleeps(t, tok);
  return true;
}
async function houseSleeps(t, tok) {
  const hh = String(t.hour % 24).padStart(2, "0") + ":00";
  feedAdd(`<b>The house sleeps</b> \u00b7 ${hh}`, "segment");
  const el = $("#segcard");
  el.innerHTML = `<div class="st">The house sleeps</div><div class="ss">Day ${t.day} \u00b7 ${hh} \u00b7 nobody is awake</div>`;
  el.className = "turn"; el.style.display = "block";
  await waitClock(900);
  if (tok === S.token) el.style.display = "none";
}
function onDayEnd() {
  if (S.endShown) return;
  S.endShown = true; S.ff = false;
  const endTick = S.ticks.find((t) => t.ending);
  if (endTick) { showSeasonEnd(endTick.ending); return; }
  const u = S.usage ? `<p class="warn">AI calls: ${S.usage.calls} · tokens: ${Math.round((S.usage.input + S.usage.output) / 1000)}k</p>` : "";
  const st = S.state;
  const gone = st ? Object.entries(st.agents).filter(([, a]) => !alive(a)).length : 0;
  const note = st && st.vacancies && st.vacancies.length ? `<p class="warn">${st.vacancies.length} vacancy(ies) on the cast. Add newcomers before the next new week.</p>` : "";
  const rc2 = (S.ticks[S.ticks.length - 1] || {}).recap;
  const recapHtml = rc2 ? `<div class="recapcard"><div class="ep">Episode of Day ${S.day}</div><h2>${esc(rc2.title)}</h2><p>${esc(rc2.recap)}</p>`
    + (rc2.awards || []).map((a) => `<div class="aw" style="--c:${info(a.who).color}"><img src="portraits/${a.who}.png" onerror="this.style.visibility='hidden'"><div><b>${esc(a.title)}</b>: ${esc(info(a.who).name)}<br><span style="color:var(--muted)">${esc(a.why)}</span></div></div>`).join("") + "</div>" : "";
  $("#overlayCard").innerHTML = `${recapHtml}<h2 style="margin-top:0">Day ${S.day} complete</h2>
    <p style="color:var(--muted)">${S.mode === "live" ? "The day has been recorded and the world has moved on to the next morning." : "End of the recording."}</p>${u}${note}
    <div class="actions"><button id="ovClose">Close</button><button id="ovNext" class="primary">Start a day</button></div>`;
  $("#overlay").style.display = "flex";
  $("#ovClose").onclick = () => ($("#overlay").style.display = "none");
  $("#ovNext").onclick = () => { $("#overlay").style.display = "none"; openModal(); };
  refreshStatus();
}
function showError(msg, title) {
  $("#overlayCard").innerHTML = `<h2 style="margin-top:0">${title || "The simulation stopped"}</h2><p style="color:var(--bad)">${esc(msg)}</p>
    <p style="color:var(--muted)">Nothing from this unfinished day was saved. You can start the day again.</p>
    <div class="actions"><button id="ovClose">Close</button><button id="ovNext" class="primary">Start a day</button></div>`;
  $("#overlay").style.display = "flex";
  $("#ovClose").onclick = () => ($("#overlay").style.display = "none");
  $("#ovNext").onclick = () => { $("#overlay").style.display = "none"; openModal(); };
}

// ---------- polling ----------
let polling = false;
async function poll() {
  for (;;) {
    await sleep(700);
    if (!S.session || polling) continue;
    polling = true;
    try {
      const r = await (await fetch(`/api/ticks?since=${S.ticks.length}&pos=${Math.max(S.cursor, S.playIdx, -1)}`)).json();
      for (const t of r.ticks) {
        for (const k of Object.keys(t.moves || {})) if ((t.moves[k].path || []).some((x) => !S.W.rooms[x])) delete t.moves[k];
        S.ticks.push(t);
      }
      S.done = r.done; S.usage = r.usage || S.usage; S.mode = r.mode || S.mode;
      if (r.error && !S.error) { S.error = r.error; showError(r.error); }
      if (r.aborted && !S.error) { S.error = "stopped"; }
      updateUI();
    } catch (e) { /* server restarting */ }
    polling = false;
  }
}

// ---------- UI ----------
function updateUI() {
  const n = S.ticks.length;
  const cur = S.ticks[Math.max(0, Math.min(S.cursor, n - 1))] || S.ticks[0];
  $("#clock").innerHTML = S.session
    ? `Day ${S.day || (cur && cur.day) || ""} · ${String(S.hour % 24).padStart(2, "0")}:00<small>${cur ? cur.phase : ""}</small>`
    : "No session<small></small>";
  const chip = $("#modeChip");
  if (S.session) { chip.style.display = ""; chip.textContent = S.mode === "live" ? "LIVE" : "REPLAY"; chip.className = "chip " + (S.mode === "live" ? "live" : "replay"); }
  else chip.style.display = "none";
  const dl = $("#deadlineChip"), cc = $("#caseChip"), st = S.state;
  if (S.session && st && st.deadline_day && st.revealed !== false) {
    const left = st.deadline_day - S.day;
    dl.style.display = ""; dl.className = "chip deadline" + (left <= 1 ? " hot" : "");
    dl.textContent = (left <= 0 ? "DEADLINE TODAY" : `Deadline: Day ${st.deadline_day} (${left}d)`) + (S.dread ? ` \u00b7 dread ${S.dread}/5` : "");
  } else dl.style.display = "none";
  if (S.session && st && st.case && st.case.announced) {
    cc.style.display = ""; cc.textContent = `INVESTIGATION · vote Day ${st.case.vote_day} ${String(st.case.vote_hour).padStart(2, "0")}:00`;
  } else if (S.session && S.gm && st && st.case) { cc.style.display = ""; cc.textContent = "Case open (GM): body not announced"; }
  else cc.style.display = "none";
  const rc_ = $("#ruleChip");
  if (S.session && st && st.rule) { rc_.style.display = ""; rc_.textContent = "Rule: " + st.rule.title + " \u00b7 " + st.rule.short; rc_.title = st.rule.text; }
  else rc_.style.display = "none";
  const oc_ = $("#occChip"), es_ = $("#escChip");
  if (S.session && st && st.occasion && S.W.rooms[st.occasion.where]) { oc_.style.display = ""; oc_.textContent = `${st.occasion.kind} in the ${S.W.rooms[st.occasion.where].name} \u00b7 host ${info(st.occasion.host).short}`; }
  else oc_.style.display = "none";
  if (S.session && S.gm && st && st.escape && st.escape.progress > 0) { es_.style.display = ""; es_.textContent = `Escape plan ${st.escape.progress}%`; }
  else es_.style.display = "none";
  const tn = $("#tensionChip");
  if (S.session && st) { const tv = tensionValue(st); tn.style.display = ""; tn.textContent = `Tension ${tv}%`; tn.style.setProperty("--v", tv + "%"); }
  else tn.style.display = "none";
  const sch = $("#scenChip");
  if (S.session && st && st.scenario && st.scenario.title) { sch.style.display = ""; sch.textContent = st.scenario.title; sch.title = st.scenario.premise || ""; } else sch.style.display = "none";
  const pc = $("#plotChip"), np = st && st.plots ? st.plots.length : 0;
  if (S.session && np) { pc.style.display = ""; pc.textContent = np === 1 ? "A plot is unfolding" : `${np} plots unfolding`; } else pc.style.display = "none";
  const sc = $("#scrub");
  sc.max = Math.max(0, n - 1); sc.value = Math.max(0, S.cursor); sc.disabled = n < 2;
  $("#scrubLabel").textContent = S.session ? `Turn ${Math.max(0, S.cursor) + 1} / ${S.done ? n : n + "+"}` : "Turn 0/0";
  $("#btnPause").disabled = !S.session; $("#btnPause").textContent = S.paused ? "Resume" : "Pause";
  const canFF = S.session && !(S.done && S.cursor >= n - 1);
  $("#btnFF").disabled = !canFF;
  const quietNow = [S.playIdx, S.cursor + 1].some((i) => S.ticks[i] && S.ticks[i].quiet);
  $("#btnSkipNight").style.display = S.session && $("#gm").checked && quietNow && !S.skipQuiet ? "" : "none";
  $("#btnStop").style.display = S.session && S.mode === "live" && !S.done && !S.error ? "" : "none";
  const u = $("#usageChip");
  if (S.usage && S.mode === "live") { u.style.display = ""; u.textContent = `${S.usage.calls} AI calls · ${Math.round((S.usage.input + S.usage.output) / 1000)}k tokens`; }
  else u.style.display = "none";
}
function bar(cls, v) { return `<div class="bar ${cls}"><i style="width:${Math.max(0, Math.min(100, v))}%"></i></div>`; }
function charCard(id, a, gone) {
  const c = S.W.characters[id] || info(id);
  const room = S.W.rooms[a.room] ? S.W.rooms[a.room].name : "";
  const sub = gone ? `${esc(a.status)}` : `${esc(room)}: ${esc(a.activity)}`;
  return `<div class="char ${S.selected === id ? "sel" : ""} ${gone ? "gone" : ""}" data-id="${id}" style="--c:${c.color}">
      <img src="portraits/${id}.png" onerror="this.style.visibility='hidden'"><div><div class="nm">${esc(c.name)} <span class="sub">${esc(c.role)}</span></div>
      <div class="sub">${sub}</div>
      ${gone ? "" : bar("hp", a.hp) + bar("sa", a.sanity) + `<div class="sub">HP ${a.hp} · Sanity ${a.sanity}${a.mind ? " · stress " + a.mind.stress : ""}${a.conds && a.conds.length ? " · " + a.conds.map((x) => esc(x.name)).join(", ") : ""}${a.out ? " · unconscious" : ""}</div>` + needBars(a.mind)}</div></div>`;
}
const NEED_COL = { social: "#6c7bd6", rest: "#5bc0de", safety: "#6be38f", purpose: "#ffb347", privacy: "#c58af9" };
function needBars(m) {
  if (!m) return "";
  return '<div class="needs">' + Object.entries(m.needs).map(([k, v]) => `<span title="${k} ${v}" class="nb"><i style="width:${Math.max(3, v)}%;background:${v < 30 ? "#ff4d6d" : NEED_COL[k]}"></i></span>`).join("") + "</div>" +
    (m.thoughts && m.thoughts.length ? `<div class="sub" style="font-size:11px">${m.thoughts.map((t) => esc(t[0]) + " " + (t[1] > 0 ? "+" : "") + t[1]).join(" · ")}</div>` : "");
}
function renderHosts(st) {
  const el = $("#hostPanel");
  if (!S.gm || !st) { el.innerHTML = ""; return; }
  const nv = (st.npcs || {}).neovi || {};
  const aff = Object.entries(nv.aff || {}).filter(([k]) => st.agents[k] && alive(st.agents[k])).sort((x, y) => y[1] - x[1])
    .map(([k, v]) => `<span class="pill">${esc(info(k).short || k)} ${v > 0 ? "+" : ""}${v}</span>`).join("") || "<i>none</i>";
  const inv = Object.entries(nv.inv || {}).map(([k, q]) => `<span class="pill">${esc(itemName(k))}${q > 1 ? " x" + q : ""}</span>`).join("") || "<i>nothing</i>";
  const esc_ = st.escape || { progress: 0, clues: [] };
  const planBars = Object.entries(esc_.routes || {}).map(([rid, plan]) => {
    const meta = (S.W.routes || {})[rid] || { title: rid };
    return `<div class="row"><b>${esc(meta.title)}</b></div>` + Object.entries(plan).map(([k, v]) => `<div class="planrow"><span>${esc(k)}</span>${bar("pl", v)}<em>${v}%</em></div>`).join("");
  }).join("");
  const clues = (esc_.clues || []).slice(-4).map((c) => `<div class="row">\u2022 ${esc(info(c.by).short || c.by)}: ${esc(c.text)}</div>`).join("");
  el.innerHTML = `<div class="hdr2" style="margin-top:0">Hosts (GM view)</div>
    <div class="row"><b>NeoVi</b> in the ${esc((S.W.rooms[nv.room] || {}).name || "?")} \u00b7 fear ${nv.fear ?? "?"}/10</div>
    <div class="thought">${esc(nv.scheme || "No scheme yet.")}</div>
    <div class="row">Feelings: ${aff}</div><div class="row">Pockets: ${inv}</div>
    <div class="row"><b>Ways out</b>: best route at ${esc_.progress}% (any can fail)</div>${planBars}${clues}
    ${st.challenge ? `<div class="row"><b>TereVi's challenge</b>: ${esc(st.challenge.text)}</div>` : ""}
    ${(st.threats || []).filter((t) => t.status === "active").map((t) => `<div class="row"><b>Active threat</b> on ${esc(info(t.target).short || t.target)} (due Day ${t.due_day}, ${String(t.due_hour).padStart(2, "0")}:00): ${esc(t.demand)}</div>`).join("")}
    ${st.island ? `<div class="row"><b>Island event</b>: ${esc(st.island.title)}</div>` : ""}`;
}
function renderTally(seg) {
  const el = $("#tally");
  if (!seg || ((!seg.susp || !Object.keys(seg.susp).length) && !Object.keys(seg.meter || {}).length)) { el.style.display = "none"; return; }
  const cnt = {};
  Object.values(seg.susp).forEach((t) => (cnt[t] = (cnt[t] || 0) + 1));
  const total = Object.values(cnt).reduce((a, b) => a + b, 0);
  const rows = Object.entries(cnt).sort((a, b) => b[1] - a[1]).map(([t, n]) => `<div class="trow"><img src="portraits/${t}.png" onerror="this.style.visibility='hidden'"><span>${esc(info(t).short || t)}</span><div class="tbar"><i style="width:${(n / total) * 100}%"></i></div><b>${n}</b></div>`).join("");
  // the claim trial's public suspicion meter: how hard the evidence on the table points at each person (claimtrial.py)
  const mt = seg.meter || {}, mmax = Math.max(1, ...Object.values(mt));
  const meter = Object.keys(mt).length ? `<div class="tt" style="margin-top:6px">EVIDENCE AGAINST</div>` + Object.entries(mt).slice(0, 5).map(([t, v]) => `<div class="trow"><img src="portraits/${t}.png" onerror="this.style.visibility='hidden'"><span>${esc(info(t).short || t)}</span><div class="tbar"><i style="width:${(v / mmax) * 100}%;background:#ff4d6d"></i></div><b>${v}</b></div>`).join("") : "";
  el.innerHTML = `<div class="tt">SUSPICION</div>${rows}${meter}${seg.theory ? `<div class="tth">Working theory: ${esc(seg.theory)}</div>` : ""}`;
  el.style.display = "block";
}
function renderBoard() {
  const el = $("#boardWrap"), st = S.state;
  const c = st && st.case;
  if (!st || !c || !c.announced) {
    const hk = st && S.gm ? (st.hooks || []).filter((x) => x.status === "open").map((x) => `<div class="row">• ${esc(x.text)} <i>(culprit: ${esc(info(x.culprit).short || "none")}; evidence ${x.evidence}/3)</i></div>`).join("") : "";
    el.innerHTML = '<i style="color:var(--muted)">No open case. When a body is announced and the investigation starts, the evidence board appears here.</i>' + (hk ? `<div class="hdr2">Open hooks (GM)</div>${hk}` : "");
    return;
  }
  const ids = Object.keys(st.agents).filter((id) => alive(st.agents[id])).sort((a, b) => orderIdx(a) - orderIdx(b));
  const n = ids.length, cx = 180, cy = 185, R = 148, pos = {};
  ids.forEach((id, i) => { const a = -Math.PI / 2 + (i * 2 * Math.PI) / Math.max(1, n); pos[id] = [cx + R * Math.cos(a), cy + R * Math.sin(a)]; });
  const mentions = (txt) => ids.filter((id) => new RegExp("\\b" + (info(id).short || id) + "\\b").test(txt));
  const items = [];
  (c.evidence || []).forEach((e, i) => items.push({ k: "C" + (i + 1), cls: "", text: e.text, links: mentions(e.text), col: "#d9b44a" }));
  (c.testimonies || []).forEach((t, i) => items.push({ k: "T" + (i + 1), cls: "t", text: `${info(t.by).short}: ${t.claim}`, links: [t.by, ...mentions(t.claim).filter((x) => x !== t.by)], col: "#7ac0e8" }));
  (st.withheld || []).filter((x) => S.gm && x.status === "held").forEach((x, i) => items.push({ k: "H" + (i + 1), cls: "x", text: `(held back by ${info(x.by).short}: ${x.why}) ${x.text}`, links: [x.by], col: "#b08cff", dash: true }));
  (c.contradictions || []).forEach((x, i) => items.push({ k: "!" + (i + 1), cls: "x", text: x.text, links: [x.by], col: "#ff4d6d", dash: true }));
  (st.alliances || []).filter((x) => S.gm && x.status === "active").forEach((x, i) => items.push({ k: "A" + (i + 1), cls: "t", text: `alliance: ${x.members.map((m) => info(m).short).join(" + ")} (strength ${x.strength}${x.secret ? ", secret" : ""})`, links: x.members, col: "#6be0a0", dash: true }));
  (st.hooks || []).filter((x) => S.gm && x.status === "open").forEach((x, i) => items.push({ k: "?" + (i + 1), cls: "x", text: `hook: ${x.text} (culprit: ${info(x.culprit).short || "none"}, evidence ${x.evidence}/3)`, links: [...(x.victims || []), x.culprit].filter(Boolean), col: "#e0a0ff", dash: true }));
  const m = items.length;
  items.forEach((it, i) => { const ring = m > 9 ? (i % 2 ? 92 : 58) : 70; const a = -Math.PI / 2 + (i * 2 * Math.PI) / Math.max(1, m) + 0.2; it.p = [cx + ring * Math.cos(a), cy + ring * Math.sin(a)]; });
  let strings = "", notes = "";
  items.forEach((it) => {
    it.links.forEach((id, k) => { if (pos[id]) strings += `<line x1="${it.p[0]}" y1="${it.p[1]}" x2="${pos[id][0]}" y2="${pos[id][1]}" stroke="${it.col}" stroke-width="${k ? 1 : 1.8}" opacity="${k ? 0.45 : 0.85}" ${it.dash ? 'stroke-dasharray="5 4"' : ""}/>`; });
    notes += `<g><circle cx="${it.p[0]}" cy="${it.p[1]}" r="11" fill="#1c1a12" stroke="${it.col}" stroke-width="2"/><text x="${it.p[0]}" y="${it.p[1] + 4}" fill="${it.col}" style="font-size:10px;font-weight:800;stroke-width:0">${it.k}</text></g>`;
  });
  const nodes = ids.map((id, i) => {
    const [x, y] = pos[id], sa = st.agents[id].sanity, ring = sa < 20 ? "#ff5f5f" : sa < 55 ? "#ffd36b" : "#6be38f";
    return `<g class="node" onclick="selectChar('${id}')"><clipPath id="bc${i}"><circle cx="${x}" cy="${y}" r="19"/></clipPath><circle cx="${x}" cy="${y}" r="22" fill="${info(id).color}" stroke="${ring}" stroke-width="3"/>
      <image href="portraits/${id}.png" x="${x - 19}" y="${y - 19}" width="38" height="38" clip-path="url(#bc${i})" preserveAspectRatio="xMidYMid slice"/><text x="${x}" y="${y + 34}">${esc(info(id).short || id)}</text></g>`;
  }).join("");
  const vic = `<clipPath id="bcv"><circle cx="${cx}" cy="${cy}" r="24"/></clipPath><circle cx="${cx}" cy="${cy}" r="27" fill="#3a1620" stroke="#a3243b" stroke-width="3"/>
    <image href="portraits/${c.victim}.png" x="${cx - 24}" y="${cy - 24}" width="48" height="48" clip-path="url(#bcv)" preserveAspectRatio="xMidYMid slice" style="filter:grayscale(1)"/>`;
  const legend = items.map((it) => `<div class="bleg ${it.cls}"><b>${it.k}</b><span>${esc(it.text)}</span></div>`).join("") || '<div class="row"><i>Nothing found yet. Investigators gather evidence and testimonies.</i></div>';
  el.innerHTML = `<div class="row" style="color:var(--muted);font-size:12px">${esc(info(c.victim).name)} is dead. Yellow = clues, blue = testimonies, red dashed = a lie that was caught. Strings go to the people each item names.</div>
    <svg viewBox="0 0 360 380">${strings}${vic}${notes}${nodes}</svg>${legend}`;
}
function sparkline(h, cur) {
  if (!h || h.length < 2) return `<svg width="120" height="28"><text x="2" y="18" style="font-size:10px;fill:#8a90ad;stroke-width:0">${cur} sanity</text></svg>`;
  const pts = h.map((p, i) => `${(i / (h.length - 1)) * 116 + 2},${26 - (p[1] / 100) * 24}`).join(" ");
  const col = cur < 20 ? "#ff5f5f" : cur < 55 ? "#ffd36b" : "#6be38f";
  return `<svg width="120" height="28"><polyline points="${pts}" fill="none" stroke="${col}" stroke-width="2"/></svg>`;
}
function renderStats() {
  const el = $("#statsWrap"), st = S.state;
  if (!st) { el.innerHTML = '<i style="color:var(--muted)">Start a day to see the statistics.</i>'; return; }
  const stats = st.stats || {}, hist = st.san_hist || {};
  const ids = Object.keys(st.agents).sort((a, b) => orderIdx(a) - orderIdx(b));
  const living = ids.filter((id) => alive(st.agents[id])).length;
  const LAB = [["kills", "Kills", "red"], ["assaults", "Assaults", "red"], ["plots", "Plots", "red"], ["sabotages", "Sabotage", "red"], ["manipulations", "Manipulations", "red"],
    ["betrayals", "Betrayed others", "red"], ["betrayed", "Betrayed by others", ""], ["leaks", "Leaks", ""], ["rumors", "Rumours", ""],
    ["votes_right", "Right votes", "grn"], ["votes_wrong", "Wrong votes", "red"], ["wrongly_accused", "Wrongly accused", "red"],
    ["route_steps", "Way-out steps", "grn"], ["experiments", "Experiments", ""], ["builds", "Builds", ""]];
  const cards = ids.map((id) => {
    const a = st.agents[id], c = S.W.characters[id] || info(id), s_ = stats[id] || {}, gone = !alive(a);
    const badges = LAB.filter(([k]) => s_[k]).map(([k, l, cls]) => `<span class="badge ${cls}">${l}: ${s_[k]}</span>`).join("") || '<span class="badge">Nothing notable yet</span>';
    const aff = Object.entries(a.aff || {}).filter(([k]) => st.agents[k] && alive(st.agents[k]) && k !== id).sort((x, y) => y[1] - x[1]);
    const rel = aff.length ? `Closest: ${esc(info(aff[0][0]).short)} (${aff[0][1] > 0 ? "+" : ""}${aff[0][1]}) \u00b7 Rival: ${esc(info(aff[aff.length - 1][0]).short)} (${aff[aff.length - 1][1]})` : "";
    return `<div class="scard ${gone ? "gone" : ""}" style="--c:${c.color}" onclick="selectChar('${id}')"><img src="portraits/${id}.png" onerror="this.style.visibility='hidden'"><div>
      <div class="nm">${esc(c.name)} <span class="sub">${gone ? esc(a.status) : esc(c.role)}</span></div>
      ${gone ? "" : sparkline(hist[id], a.sanity) + `<div class="sub">HP ${a.hp} \u00b7 Sanity ${a.sanity}</div>`}
      <div class="badges">${badges}</div><div class="sub">${rel}</div></div></div>`;
  }).join("");
  const tel = Object.entries(st.telemetry || {}).filter(([k]) => !k.startsWith("action:") || ["action:experiment", "action:craft", "action:lock", "action:pick", "action:break", "action:barricade", "action:frisk", "action:hide", "action:spy", "action:stash", "action:interrogate"].includes(k))
    .sort((x, y) => (y[1].model + y[1].engine) - (x[1].model + x[1].engine)).map(([k, v]) => `<tr><td>${esc(k.replace("action:", ""))}</td><td>${v.model}</td><td>${v.engine}</td></tr>`).join("");
  const telTable = tel ? `<div class="hdr2">Optional mechanics today (chosen by the model / done by the engine)</div><table class="tel"><tr><th></th><th>model</th><th>engine</th></tr>${tel}</table>` : "";
  el.innerHTML = `<div class="row">Alive: <b>${living}</b> of ${ids.length} \u00b7 Departed: <b>${ids.length - living}</b>${st.spree ? ' \u00b7 <b style="color:#ff4d6d">a killing spree is on</b>' : ""}</div>${telTable}${cards}`;
}
async function showPrevious(day) {
  if (day <= 1 || localStorage.getItem("mc_skip_recap") === "1") return;
  let d = null;
  try { d = (await (await fetch("/api/previously?day=" + day)).json()).data; } catch (e) { /* no recap */ }
  if (!d) return;
  S.paused = true; updateUI();
  const rc = d.recap;
  const aw = rc ? (rc.awards || []).slice(0, 3).map((a) => `<li><b>${esc(a.title)}</b>: ${esc(info(a.who).name)} (${esc(a.why)})</li>`).join("") : "";
  const hi = (d.highlights || []).map((h) => `<li>${esc(h)}</li>`).join("");
  const dead = (d.deaths || []).map((x) => `<span>${esc(x.name)}: ${esc(x.how)}</span>`).join("");
  $("#overlayCard").innerHTML = `<div class="prev"><div class="ep">Previously on Murder Channel</div><h2>${rc ? esc(rc.title) : "Day " + d.day}</h2>
    ${rc ? `<p>${esc(rc.recap)}</p>` : ""}${aw ? `<ul>${aw}</ul>` : ""}${hi ? `<div class="ep" style="margin-top:8px">What happened</div><ul>${hi}</ul>` : ""}
    ${dead ? `<div class="ep">Lost</div><div class="dead">${dead}</div>` : ""}
    <p style="color:var(--muted);font-size:13px">${d.alive != null ? d.alive + " alive" : ""}${d.deadline ? " \u00b7 deadline Day " + d.deadline : ""}</p>
    <label style="font-size:12px;color:var(--muted)"><input type="checkbox" id="skipRecap"> Do not show recaps</label></div>
    <div class="actions"><span></span><button id="prevGo" class="primary">Continue to Day ${day}</button></div>`;
  $("#overlay").style.display = "flex";
  await new Promise((res) => { $("#prevGo").onclick = () => { if ($("#skipRecap").checked) localStorage.setItem("mc_skip_recap", "1"); $("#overlay").style.display = "none"; res(); }; });
  S.paused = false; updateUI();
}
function renderCaseBoard(st) {
  const el = $("#caseBoard");
  const c = st.case;
  if (!c || !c.announced) { el.innerHTML = ""; return; }
  const ev = (c.evidence || []).map((e) => `<div class="row">\u2022 ${esc(e.text)}${e.by.length ? ` <i>(${e.by.map((b) => esc(info(b).short || b)).join(", ")})</i>` : ""}</div>`).join("") || '<div class="row"><i>No evidence found yet.</i></div>';
  const ts = (c.testimonies || []).map((t) => `<div class="row">\u201C ${esc(info(t.by).short || t.by)}: ${esc(t.claim)}</div>`).join("") || '<div class="row"><i>No testimonies yet.</i></div>';
  el.innerHTML = `<div class="hdr2" style="margin-top:0">Case file: ${esc(info(c.victim).name)}</div><div class="casebox"><b>Evidence</b>${ev}<b>Testimonies</b>${ts}</div>`;
}
function renderPlots(st) {
  const el = $("#plotPanel");
  const pl = st.plots || [];
  if (!pl.length) { el.innerHTML = ""; return; }
  el.innerHTML = `<div class="hdr2" style="margin-top:0">Scheming</div>` + pl.map((p) => `<div class="plotcard"><img src="portraits/${p.who}.png" onerror="this.style.visibility='hidden'" style="--c:${info(p.who).color}">
    <div><b style="color:${info(p.who).color}">${esc(info(p.who).short)}</b> plots against <b style="color:${info(p.target).color}">${esc(info(p.target).short)}</b> <span class="stage st-${p.stage}">${esc(p.stage)}</span>
    <div class="sub">${esc(p.step || p.method || "")}</div>${p.cover ? `<div class="sub"><i>Cover: ${esc(p.cover)}</i></div>` : ""}</div></div>`).join("");
}
function renderCast() {
  const st = S.state; if (!st) return;
  renderCaseBoard(st);
  renderPlots(st);
  renderHosts(st);
  const list = $("#castList");
  const ids = Object.keys(st.agents).sort((a, b) => orderIdx(a) - orderIdx(b));
  const living = ids.filter((id) => alive(st.agents[id])), gone = ids.filter((id) => !alive(st.agents[id]));
  list.innerHTML = living.map((id) => charCard(id, st.agents[id], false)).join("")
    + (gone.length ? `<div class="hdr2">Departed</div>` + gone.map((id) => charCard(id, st.agents[id], true)).join("") : "");
  list.querySelectorAll(".char").forEach((el) => el.onclick = () => { S.selected = S.selected === el.dataset.id ? null : el.dataset.id; renderCast(); });
  const d = $("#castDetail");
  if (!S.selected || !st.agents[S.selected]) { d.innerHTML = ""; return; }
  const id = S.selected, c = S.W.characters[id] || info(id), a = st.agents[id];
  const inv = Object.entries(a.inv).map(([k, q]) => `<span class="pill ${isWeapon(k) ? "w" : ""}">${esc(itemName(k))}${q > 1 ? " x" + q : ""}${S.gm && (a.concealed || []).includes(k) ? " (concealed)" : ""}</span>`).join("") || "<i>nothing</i>";
  const aff = Object.entries(a.aff).sort((x, y) => y[1] - x[1]).map(([k, v]) => `<span class="pill">${esc(info(k).short || k)} ${v > 0 ? "+" : ""}${v}</span>`).join("");
  const th = S.gm && S.thoughts[id] ? `<div class="thought">${esc(S.thoughts[id])}</div>` : "";
  const DRV = { survivor: "Survivor", protector: "Protector", saboteur: "Saboteur", schemer: "Schemer", avenger: "Avenger", thrill: "Thrill-seeker", romantic: "Romantic", seeker: "Seeker", nihilist: "Nihilist", martyr: "Martyr" };
  const dv = a.drive || {};
  const gmx = S.gm && alive(a) ? `<div class="row"><b>Secret drive</b>: ${esc(DRV[dv.id] || dv.id || "?")}${dv.target ? " \u2192 " + esc(info(dv.target).short || dv.target) : ""}${dv.arc ? "<br><i>" + esc(dv.arc) + "</i>" : ""}</div>`
    + ((a.secrets || []).length ? `<div class="row">Knows: ${(a.secrets || []).map((k) => `<span class="pill">${esc(info(k.of).short || k.of)}'s secret</span>`).join("")}</div>` : "") : "";
  const bonds = (st.bonds || []).filter((b) => b.a === id || b.b === id).map((b) => {
    const o = b.a === id ? b.b : b.a;
    return `<span class="pill">${b.kind === "romance" ? "\u2665 romance with" : b.kind === "pact" ? "\u{1F91D} pact with" : "\u2694 feud with"} ${esc(info(o).short || o)}</span>`;
  }).join("");
  d.innerHTML = `<h3 style="color:${c.color}">${esc(c.name)}</h3>
    <div class="row">${esc(c.role)} · ${esc(c.origin || "")} · age ${c.age || "?"}${alive(a) ? "" : " · <b>" + esc(a.status) + "</b>"}</div>
    ${alive(a) ? `<div class="row">Now: <b>${esc(a.activity)}</b> in ${esc(S.W.rooms[a.room].name)}</div>` : ""}
    ${(a.lost || []).length ? `<div class="row">Carries the loss of: <b>${a.lost.map(esc).join(", ")}</b></div>` : ""}
    ${S.gm && (a.moments || []).length ? `<div class="row"><b>Defining moments</b><br>${a.moments.map((m) => "\u2022 " + esc(m)).join("<br>")}</div>` : ""}
    ${S.gm && a.quirk ? `<div class="row"><b>Lately</b>: <i>${esc(a.quirk)}</i></div>` : ""}
    ${S.gm && a.brain && a.brain.plan && a.brain.plan.length ? `<div class="row"><b>Plan</b><br>${a.brain.plan.map((it) => "\u2022 " + (it.done ? "<s>" : "") + esc(it.do) + (it.who ? " " + esc(info(it.who).short || it.who) : "") + (it.where ? " @ " + esc((S.W.rooms[it.where] || {}).name || it.where) : "") + ": " + esc(it.why || "") + (it.done ? "</s>" : "")).join("<br>")}</div>` : ""}
    ${S.gm && a.beliefs && a.beliefs.length ? `<div class="row"><b>Believes</b><br>${a.beliefs.map((b) => "\u2022 " + (b.false ? '<span style="color:#ff6b6b" title="not true">\u2717</span> ' : "") + esc(b.text) + ` <span style="opacity:.6">(${esc(b.src)}${b.by ? " from " + esc(info(b.by).short || b.by) : ""}, ${Math.round(b.c * 100)}%)</span>`).join("<br>")}</div>` : ""}
    ${S.gm && a.brain && a.brain.mem && a.brain.mem.length ? `<div class="row"><b>On their mind</b><br>${a.brain.mem.map((m) => "\u2022 " + esc(m)).join("<br>")}</div>` : ""}
    ${(a.conds || []).length || a.out ? `<div class="row">Body: ${a.out ? `<b>unconscious (${esc(a.out)})</b> ` : ""}${(a.conds || []).map((x) => `<span class="pill ${x.sev >= 3 ? "w" : ""}">${esc(x.name)}${x.sev > 1 ? " " + "\u2605".repeat(x.sev - 1) : ""}</span>`).join("")}</div>` : ""}
    ${th}${gmx}<div class="row">Carrying: ${inv}</div><div class="row">Feelings toward: ${aff}</div>${bonds ? `<div class="row">Bonds: ${bonds}</div>` : ""}
    ${c.card ? `<img class="card" src="cards/${c.card}.webp">` : ""}`;
}
function renderRoom() {
  const st = S.state, el = $("#roomInfo");
  if (!S.selRoom || !st) { el.innerHTML = "Click a room on the map."; return; }
  const r = S.W.rooms[S.selRoom];
  const who = Object.entries(S.endMap).filter(([, rid]) => rid === S.selRoom).map(([id]) => esc(info(id).short || info(id).name));
  const items = Object.entries(st.room_items[S.selRoom] || {}).map(([k, q]) => `<span class="pill ${isWeapon(k) ? "w" : ""}">${esc(itemName(k))}${q > 1 ? " x" + q : ""}</span>`).join("") || "<i>nothing</i>";
  let hid = "";
  if (S.gm) {
    const h = Object.entries((st.hidden_items || {})[S.selRoom] || {}).map(([k, q]) => `<span class="pill">${esc(itemName(k))}${q > 1 ? " x" + q : ""}</span>`).join("");
    const sp = S.W.edges.filter((e) => e.hidden && (e.a === S.selRoom || e.b === S.selRoom)).map((e) => `<span class="pill">${e.id}${st.found_edges.includes(e.id) ? " (found)" : " (secret)"}</span>`).join("");
    hid = `<div class="row">Hidden items: ${h || "<i>none</i>"}</div><div class="row">Secret passages: ${sp || "<i>none</i>"}</div>`
      + ((st.stash || []).filter((x) => x.room === S.selRoom).map((x) => `<div class="row">Stash ${esc(x.spot)} (by ${esc(info(x.by).short || x.by)}): ${Object.entries(x.items).map(([k, q]) => esc(itemName(k)) + (q > 1 ? " x" + q : "")).join(", ")}</div>`).join(""));
  }
  const doors = [];
  if ((st.locks || {})[S.selRoom] !== undefined) doors.push(`locked${S.gm && st.locks[S.selRoom] ? " by " + esc(info(st.locks[S.selRoom]).short || st.locks[S.selRoom]) : ""}`);
  if ((st.broken_doors || []).includes(S.selRoom)) doors.push("door broken (NeoVi mends it next week)");
  for (const b of (st.barricades || [])) if (b.inside === S.selRoom) doors.push(`a door is barricaded with ${esc(b.prop)}`);
  const dr = doors.length ? `<div class="row">Doors: ${doors.join("; ")}</div>` : "";
  el.innerHTML = `<h3>${esc(r.name)}</h3><div class="row">Here: <b>${who.join(", ") || "nobody"}</b></div><div class="row">Items: ${items}</div>${((S.W.common || {})[S.selRoom] || []).length ? `<div class="row">Unlimited supplies: ${S.W.common[S.selRoom].map((k) => `<span class="pill">${esc(itemName(k))}</span>`).join("")}</div>` : ""}${dr}${hid}`;
}

// map interaction
function toWorld(ev) {
  const b = cv.getBoundingClientRect();
  return [(ev.clientX - b.left - S.view.ox) / S.view.scale, (ev.clientY - b.top - S.view.oy) / S.view.scale];
}
function hit(ev) {
  const [x, y] = toWorld(ev);
  for (const id of Object.keys(S.pos)) {
    const p = agentPos(id); if (!p) continue;
    if (Math.hypot(p[0] - x, p[1] - y) <= (S.rad[id] || 14) + 2) return { agent: id };
  }
  for (const [rid, r] of Object.entries(S.W.rooms)) if (x >= r.x && x <= r.x + r.w && y >= r.y && y <= r.y + r.h) return { room: rid };
  return {};
}
cv.addEventListener("mousemove", (ev) => {
  if (!S.W) return;
  const h = hit(ev), tip = $("#tip"), st = S.state;
  const b = cv.parentElement.getBoundingClientRect();
  let html = "";
  if (h.agent && st && st.agents[h.agent]) {
    const a = st.agents[h.agent], c = info(h.agent);
    html = `<b>${esc(c.name)}</b><br>${esc(c.role)}<br>HP ${a.hp} · Sanity ${a.sanity}<br><i>${esc(a.activity)}</i>`;
  } else if (h.agent) { html = `<b>${esc(info(h.agent).name)}</b>`; }
  else if (h.room) {
    const items = st ? Object.entries(st.room_items[h.room] || {}).slice(0, 8).map(([k, q]) => esc(itemName(k)) + (q > 1 ? " x" + q : "")).join(", ") : "";
    html = `<b>${esc(S.W.rooms[h.room].name)}</b>${items ? "<br>" + items : ""}`;
  }
  if (html) { tip.innerHTML = html; tip.style.display = "block"; tip.style.left = Math.min(b.width - 290, ev.clientX - b.left + 14) + "px"; tip.style.top = Math.max(4, ev.clientY - b.top + 14) + "px"; }
  else tip.style.display = "none";
});
cv.addEventListener("mouseleave", () => ($("#tip").style.display = "none"));
cv.addEventListener("click", (ev) => {
  const h = hit(ev);
  if (h.agent && S.W.characters[h.agent]) { S.selected = h.agent; setTab("cast"); renderCast(); }
  else if (h.room) { S.selRoom = h.room; setTab("room"); renderRoom(); }
});

// ---------- chronicle (typed record of everything that happened) ----------
const CHRON = { past: [], pastDay: -1, filters: { day: "", who: "", cls: "notable", q: "" } };
const CH_RANK = { critical: 3, important: 2, notable: 1, background: 0 };
function chronEntries() {
  const seen = new Set(), out = [];
  const add = (e) => { if (!seen.has(e.id)) { seen.add(e.id); out.push(e); } };
  CHRON.past.forEach(add);
  S.ticks.slice(0, Math.max(0, S.cursor + 1)).forEach((t) => (t.chron || []).forEach(add));
  return out.sort((a, b) => a.id - b.id);
}
async function chronLoadPast() {
  if (!S.session && !S.day) return;
  try {
    const r = await (await fetch("/api/chronicle?limit=4000" + (S.gm ? "" : "&gm=0"))).json();
    if (r.ok) { CHRON.past = r.entries; CHRON.pastDay = S.day; }
  } catch (e) { /* offline */ }
  renderChronicle();
}
function renderChronicle() {
  const wrap = $("#chronWrap");
  if (!wrap || !$("#tab-chron").classList.contains("on")) return;
  const all = chronEntries().filter((e) => S.gm || e.vis !== "gm");
  const days = [...new Set(all.map((e) => e.day))].sort((a, b) => a - b);
  const dSel = $("#chDay"), wSel = $("#chWho");
  const f = CHRON.filters;
  dSel.innerHTML = '<option value="">All days</option>' + days.map((d) => `<option value="${d}" ${String(f.day) === String(d) ? "selected" : ""}>Day ${d}</option>`).join("");
  const people = S.W ? Object.keys(S.W.characters).concat(Object.keys(S.W.hosts || {})) : [];
  wSel.innerHTML = '<option value="">Everyone</option>' + people.map((id) => `<option value="${id}" ${f.who === id ? "selected" : ""}>${esc(info(id).name)}</option>`).join("");
  const min = f.cls ? CH_RANK[f.cls] : 0, q = f.q.toLowerCase();
  const rows = all.filter((e) => (!f.day || String(e.day) === String(f.day)) && CH_RANK[e.cls] >= min
    && (!f.who || e.who === f.who || (e.with || []).includes(f.who) || (e.people || []).includes(f.who)) && (!q || e.text.toLowerCase().includes(q)));
  if (!rows.length) { wrap.innerHTML = '<i style="color:var(--muted)">Nothing recorded for these filters yet.</i>'; return; }
  let html = "", day = null;
  for (const e of rows.slice(-600)) {
    if (e.day !== day) { day = e.day; html += `<div class="chday">Day ${day}</div>`; }
    const who = e.who && (S.W.characters[e.who] || (S.W.hosts || {})[e.who]) ? `<img class="chav" src="portraits/${e.who}.png" onerror="this.style.visibility='hidden'">` : '<span class="chav"></span>';
    html += `<div class="chrow ${e.cls} ${e.vis === "gm" ? "gmonly" : ""}" ${e.room && S.W.rooms[e.room] ? `onclick="S.selRoom='${e.room}';setTab('room');renderRoom()"` : ""}>
      <span class="chtime">${String(e.hour % 24).padStart(2, "0")}:00</span>${who}<span class="chtype">${esc(e.type)}</span><span class="chtext">${esc(e.text)}</span></div>`;
  }
  wrap.innerHTML = html;
}
$("#chDay").onchange = (e) => { CHRON.filters.day = e.target.value; renderChronicle(); };
$("#chWho").onchange = (e) => { CHRON.filters.who = e.target.value; renderChronicle(); };
$("#chCls").onchange = (e) => { CHRON.filters.cls = e.target.value; renderChronicle(); };
$("#chQ").oninput = (e) => { CHRON.filters.q = e.target.value; renderChronicle(); };

function setTab(name) {
  document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  document.querySelectorAll(".tabpane").forEach((p) => p.classList.toggle("on", p.id === "tab-" + name));
  if (name === "chron") chronLoadPast();
}
document.querySelectorAll(".tabs button").forEach((b) => (b.onclick = () => setTab(b.dataset.tab)));
$("#gm").onchange = (e) => { S.gm = e.target.checked; $("#fGm").checked = S.gm; applyFilters(); renderCast(); renderRoom(); updateUI(); };
function applyFilters() {
  feed.classList.toggle("hide-talk", !$("#fTalk").checked);
  feed.classList.toggle("hide-events", !$("#fEvents").checked);
  feed.classList.toggle("hide-gm", !$("#fGm").checked);
}
["fTalk", "fEvents", "fGm"].forEach((id) => ($("#" + id).onchange = applyFilters));
$("#btnPause").onclick = () => { S.paused = !S.paused; updateUI(); };
$("#autodir").onchange = async (e) => { await fetch("/api/autodir", { method: "POST", body: JSON.stringify({ on: e.target.checked }) }); };
$("#voices").onchange = (e) => {
  Voice.on = e.target.checked;
  if (Voice.on && window.speechSynthesis) { voiceLoad(); speechSynthesis.speak(new SpeechSynthesisUtterance("")); }
  else stopSpeech();
};
$("#sound").onchange = (e) => { S.sound = e.target.checked; if (S.sound) { sndInit(); if (Snd.ctx && Snd.ctx.resume) Snd.ctx.resume(); } setDrone(); };
$("#speed").onchange = (e) => (S.speed = parseFloat(e.target.value));
$("#btnSkipNight").onclick = () => {
  S.skipQuiet = true;                                               // skips quiet night blocks until the first one where something happens
  const cur = S.ticks[S.playIdx];
  if (cur && cur.quiet && S.playIdx > S.cursor) jumpTo(S.playIdx);
  updateUI();
};
$("#btnFF").onclick = async () => {
  S.ff = true; S.waiters.forEach((w) => w.res());
  if (S.mode === "live") await fetch("/api/ff", { method: "POST", body: "{}" });
  updateUI();
};
$("#btnStop").onclick = async () => {
  if (!confirm("Stop this live day? Nothing from it will be saved.")) return;
  await fetch("/api/stop", { method: "POST", body: "{}" });
  resetSession(); $("#wait").style.display = "none"; refreshStatus();
};
$("#scrub").oninput = (e) => { const i = parseInt(e.target.value, 10); if (i < S.ticks.length) { S.paused = true; jumpTo(i); } };

// ---------- start modal ----------
let modalMode = "live";
async function refreshStatus() { S.status = await (await fetch("/api/status")).json(); return S.status; }
async function reloadWorld() {
  S.W = await (await fetch("/api/world")).json();
  for (const id of [...Object.keys(S.W.characters), "neovi", "terevi"]) img(id);
}
async function openModal() {
  const st = await refreshStatus();
  $("#modalErr").textContent = "";
  const hasRec = st.recorded.length > 0;
  $("#liveHint").textContent = `Simulate Day ${st.next_day} now and watch it unfold.`;
  $("#replayHint").textContent = hasRec ? `${st.recorded.length} recorded day(s) available.` : "Nothing recorded yet.";
  document.querySelector('.opt[data-mode="replay"]').classList.toggle("off", !hasRec);
  $("#replayDay").innerHTML = st.recorded.map((r) => `<option value="${r.day}">Day ${r.day} (${r.ticks} turns)</option>`).join("");
  $("#replayDay").value = st.recorded.length ? st.recorded[st.recorded.length - 1].day : "";
  const b = $("#backend"); b.innerHTML = "";
  const add = (v, t) => { const o = document.createElement("option"); o.value = v; o.textContent = t; b.appendChild(o); };
  if (st.backends.cli) add("cli", "Claude subscription (Claude Code CLI)");
  if (st.backends.api) add("api", "Anthropic API (needs credits)");
  add("mock", "Mock AI (free, scripted, for testing)");
  const rs = $("#rule");
  rs.innerHTML = `<option value="roulette">Roulette: TereVi invents a new rule each day</option><option value="custom">My own rule (I will type it)</option><option value="none">No rule today</option>`
    + `<optgroup label="Presets (checked precisely by the game)">` + (S.W.rules || []).map((r) => `<option value="${r.id}">${esc(r.title)}</option>`).join("") + `</optgroup>`;
  updateRuleWarn();
  const vb = $("#vacBox");
  if (st.vacancies && st.vacancies.length) {
    const f = st.vacancies.filter((v) => v.gender === "female").length, m = st.vacancies.length - f;
    const need = [f ? `${f} female` : "", m ? `${m} male` : ""].filter(Boolean).join(" and ");
    vb.innerHTML = `<b>Newcomers needed: ${need}.</b> The show always has 8 participants.${st.new_week ? ` A new week begins on Day ${st.next_day}, so they must be added before you can start.` : " They can join at the start of the next week (or earlier if you like)."}<br><button id="btnAddNew" class="primary">Add a newcomer</button>`;
    vb.style.display = "";
    $("#btnAddNew").onclick = openNewcomer;
  } else vb.style.display = "none";
  setModalMode(modalMode === "replay" && !hasRec ? "live" : modalMode);
  const ob = $("#overBox");
  if (st.over) { ob.innerHTML = `<b>The season is over: ${esc(st.over.title)}.</b> Start a new game to play again, or replay and export the days you have.`; ob.style.display = ""; $("#btnGo").disabled = modalMode === "live"; }
  else { ob.style.display = "none"; $("#btnGo").disabled = false; }
  $("#btnRewind").style.display = st.can_rewind ? "" : "none";
  $("#btnExport").style.display = hasRec ? "" : "none";
  $("#autodir").checked = !!st.autodir;
  $("#slotSel").innerHTML = (st.slots || []).map((x) => `<option value="${esc(x.name)}">${esc(x.name)} (Day ${x.day}, ${x.alive} alive, ${esc(x.saved_at)})</option>`).join("") || "<option value=''>No saves yet</option>";
  $("#dayStartSel").innerHTML = (st.day_starts || []).map((d) => `<option value="${d}">Start of Day ${d}</option>`).join("") || "<option value=''>No earlier days</option>";
  $("#resumeBox").innerHTML = st.checkpoint ? `<div class="warn">Day ${st.checkpoint.day} was interrupted after ${String(st.checkpoint.hour % 24).padStart(2, "0")}:00. <button id="btnResume" class="primary">Resume it</button></div>` : "";
  if ($("#btnResume")) $("#btnResume").onclick = () => { S.resumeNext = true; $("#btnGo").click(); };
  $("#seasonInfo").textContent = hasRec ? `This season so far: ${st.season_calls || 0} AI calls over ${st.recorded.length} recorded day(s).` : "";
  $("#modal").style.display = "flex";
}
function setModalMode(m) {
  modalMode = m;
  document.querySelectorAll("#modeOpts .opt").forEach((o) => o.classList.toggle("on", o.dataset.mode === m));
  $("#replayField").style.display = m === "replay" ? "" : "none";
  for (const id of ["backendField", "stepField", "murderField", "dramaField", "chaosField", "lengthField", "budgetField", "variationField", "ruleField", "motiveField"]) $("#" + id).style.display = m === "live" ? "" : "none";
  updateBackendWarn();
}
function updateBackendWarn() {
  const v = $("#backend").value, w = $("#backendWarn");
  w.textContent = v === "cli" ? "Uses your Claude plan's usage allowance. A 2-hour-pace day is roughly 90 short calls; a trial day adds a few more." : v === "mock" ? "No AI is used. Characters wander randomly; good for checking the viewer." : "";
}
function updateRuleWarn() {
  const v = $("#rule").value, ta = $("#ruleText"), w = $("#ruleWarn");
  const ai = v === "roulette" || v === "custom";
  ta.style.display = ai ? "" : "none";
  ta.placeholder = v === "custom" ? "Type the rule in plain words, e.g. Nobody may say the word babe today."
    : "Optional theme or constraints, e.g. something about silence, or nothing near the pool";
  w.textContent = v === "none" ? "" : ai
    ? "A referee model reads what everyone did each turn and NeoVi punishes clear violations (about 7 extra short AI calls per day)."
    : "Checked directly by the game. NeoVi tases or detains anyone who breaks it. The leader rule makes the leader move first.";
}
$("#rule").onchange = updateRuleWarn;
document.querySelectorAll("#modeOpts .opt").forEach((o) => (o.onclick = () => { if (!o.classList.contains("off")) setModalMode(o.dataset.mode); }));
$("#backend").onchange = updateBackendWarn;
$("#btnNew").onclick = openModal;
$("#btnCancel").onclick = () => ($("#modal").style.display = "none");
async function slotCall(body, msg) {
  const r = await (await fetch("/api/slot", { method: "POST", body: JSON.stringify(body) })).json();
  if (!r.ok) { $("#modalErr").textContent = r.error; return false; }
  $("#modalErr").textContent = msg || "";
  return true;
}
$("#slotSave").onclick = async () => { if (await slotCall({ action: "save", name: $("#slotName").value }, "Saved.")) { $("#slotName").value = ""; await openModal(); } };
$("#slotLoad").onclick = async () => {
  const n = $("#slotSel").value; if (!n) return;
  if (!confirm(`Load "${n}"? The current game and recordings are replaced.`)) return;
  if (await slotCall({ action: "load", name: n })) { resetSession(); await reloadWorld(); await openModal(); }
};
$("#slotDel").onclick = async () => { const n = $("#slotSel").value; if (n && confirm(`Delete the save "${n}"?`) && await slotCall({ action: "delete", name: n })) await openModal(); };
$("#dayStartGo").onclick = async () => {
  const d = $("#dayStartSel").value; if (!d) return;
  if (!confirm(`Go back to the start of Day ${d}? Later recordings are set aside.`)) return;
  if (await slotCall({ action: "daystart", day: d })) { resetSession(); await reloadWorld(); await openModal(); }
};
// ---------- scenario editor ----------
let SCN = null;
function opts(map, sel) { return Object.entries(map).map(([k, v]) => `<option value="${esc(k)}" ${k === sel ? "selected" : ""}>${esc(v)}</option>`).join(""); }
function rowDel(el) { return `<button type="button" onclick="this.parentElement.remove()">\u00d7</button>`; }
function addRel(r) {
  r = r || {};
  const d = document.createElement("div"); d.className = "scrow";
  d.innerHTML = `<select class="ra">${opts(SCN.cast, r.a)}</select><select class="rb">${opts(SCN.cast, r.b)}</select><select class="rk">${SCN.kinds.map((k) => `<option ${k === (r.kind || "rivals") ? "selected" : ""}>${esc(k)}</option>`).join("")}</select><input class="rt" placeholder="Their history" value="${esc(r.text || "")}">${rowDel()}`;
  $("#scRels").appendChild(d);
}
function addSec(r) {
  r = r || {};
  const d = document.createElement("div"); d.className = "scrow two";
  d.innerHTML = `<select class="si">${opts(SCN.cast, r.id)}</select><input class="st" placeholder="An extra secret they carry" value="${esc(r.text || "")}">${rowDel()}`;
  $("#scSecrets").appendChild(d);
}
function addItem(r) {
  r = r || {};
  const d = document.createElement("div"); d.className = "scrow two";
  d.innerHTML = `<select class="ir">${opts(SCN.rooms, r.room)}</select><input class="in" placeholder="Item name" value="${esc(r.name || "")}">${rowDel()}`;
  $("#scItems").appendChild(d);
}
let SCN_EXTRA = { events: [], meta: null };
function fillScenario(sc) {
  sc = sc || {};
  SCN_EXTRA = { events: sc.events || [], meta: sc._meta || null };
  $("#scGenInfo").textContent = SCN_EXTRA.events.length ? "Scheduled events: " + SCN_EXTRA.events.map((e) => `day ${e.day} ${String(e.hour).padStart(2, "0")}:00 ${e.kind}${e.room ? " (" + e.room + ")" : ""}`).join(", ") + (SCN_EXTRA.meta ? `. Difficulty ${SCN_EXTRA.meta.difficulty}, ${SCN_EXTRA.meta.spent} of ${SCN_EXTRA.meta.budget} points.` : ".") : "";
  $("#scTitle").value = sc.title || ""; $("#scPremise").value = sc.premise || "";
  $("#scTwist").value = (sc.twist && sc.twist.text) || ""; $("#scTwistDay").value = (sc.twist && sc.twist.day) || 4;
  $("#scDeadline").value = sc.deadline_days || ""; $("#scRules").value = (sc.rules || []).join("\n");
  $("#scRels").innerHTML = ""; $("#scSecrets").innerHTML = ""; $("#scItems").innerHTML = "";
  (sc.relationships || []).forEach(addRel); (sc.secrets || []).forEach(addSec); (sc.items || []).forEach(addItem);
}
async function openScenario() {
  SCN = await (await fetch("/api/scenario")).json();
  $("#scTpl").innerHTML = SCN.templates.map((t) => `<option value="${esc(t.id)}">${esc(t.name)}</option>`).join("");
  fillScenario(SCN.scenario); $("#scErr").textContent = "";
  $("#smodal").style.display = "flex";
}
$("#btnScenario").onclick = openScenario;
$("#scAddRel").onclick = () => addRel(); $("#scAddSec").onclick = () => addSec(); $("#scAddItem").onclick = () => addItem();
$("#scGen").onclick = async () => {
  const q2 = `difficulty=${encodeURIComponent($("#scGenDiff").value)}&seed=${encodeURIComponent($("#scGenSeed").value)}&secrets=${$("#scGenSec").checked ? 1 : 0}`;
  const r = await (await fetch("/api/scenario/generate?" + q2)).json();
  if (!r.ok) { $("#scErr").textContent = r.error || "Could not generate."; return; }
  $("#scErr").textContent = ""; fillScenario(r.scenario); $("#scGenSeed").value = r.meta.seed;
};
$("#scLoadTpl").onclick = () => { const t = SCN.templates.find((x) => x.id === $("#scTpl").value); if (t) fillScenario(t.scenario); };
$("#scCancel").onclick = () => ($("#smodal").style.display = "none");
function collectScenario() {
  return {
    events: SCN_EXTRA.events, _meta: SCN_EXTRA.meta,
    title: $("#scTitle").value, premise: $("#scPremise").value, deadline_days: $("#scDeadline").value,
    twist: $("#scTwist").value.trim() ? { text: $("#scTwist").value, day: parseInt($("#scTwistDay").value, 10) || 4 } : null,
    rules: $("#scRules").value.split("\n").map((x) => x.trim()).filter(Boolean),
    relationships: [...document.querySelectorAll("#scRels .scrow")].map((d) => ({ a: d.querySelector(".ra").value, b: d.querySelector(".rb").value, kind: d.querySelector(".rk").value, text: d.querySelector(".rt").value })),
    secrets: [...document.querySelectorAll("#scSecrets .scrow")].map((d) => ({ id: d.querySelector(".si").value, text: d.querySelector(".st").value })),
    items: [...document.querySelectorAll("#scItems .scrow")].map((d) => ({ room: d.querySelector(".ir").value, name: d.querySelector(".in").value })),
  };
}
async function saveScenario(sc) {
  const r = await (await fetch("/api/scenario", { method: "POST", body: JSON.stringify({ scenario: sc }) })).json();
  if (!r.ok) { $("#scErr").textContent = r.error; return false; }
  $("#smodal").style.display = "none"; await openModal(); return true;
}
$("#scSave").onclick = () => saveScenario(collectScenario());
$("#scClear").onclick = () => { if (confirm("Clear the scenario and the house rules?")) saveScenario({}); };
$("#variation").oninput = (e) => { const v = parseInt(e.target.value, 10); $("#variationVal").textContent = v ? (v < 34 ? "slight (" + v + ")" : v < 67 ? "noticeable (" + v + ")" : "strong (" + v + ")") : "off"; };
$("#btnRewind").onclick = async () => {
  if (!confirm("Undo the last recorded day? The world goes back to the start of that day and the recording is set aside.")) return;
  const r = await (await fetch("/api/rewind", { method: "POST", body: "{}" })).json();
  if (!r.ok) { $("#modalErr").textContent = r.error; return; }
  resetSession(); await reloadWorld(); await openModal();
};
$("#btnNewGame").onclick = async () => {
  const d = prompt("Erase ALL recorded days, deaths and newcomers, and start a new game.\nStart at which day?\n1 = a fresh season: Day 1 is introductions and presentations, and the truth is revealed that evening\n3 = continue the chat story (the cast already knows the truth)", "1");
  if (!d) return;
  const keep = S.status && S.status.scenario ? confirm(`Keep your scenario "${S.status.scenario}" (premise, twist, house rules, seeded relationships) for the new game?`) : true;
  await fetch("/api/newgame", { method: "POST", body: JSON.stringify({ start_day: parseInt(d, 10) || 3, keep_scenario: keep }) });
  resetSession(); await reloadWorld(); await openModal();
};
function resetSession() {
  stopSpeech();
  S.token++; S.session = false; S.ticks = []; S.cursor = -1; S.ff = false; S.state = null; S.done = false; S.error = null;
  S.endShown = false; S.paused = false; S.playIdx = -1; S.confessions = []; S.dread = 0; S.weather = null; S.parts = []; S.flash = null; setDrone(); renderWeb(); $("#overlay").style.display = "none"; hideScene(); $("#booth").style.display = "none"; renderBooth();
  setPositions(homeMap()); feed.innerHTML = ""; $("#castList").innerHTML = ""; $("#castDetail").innerHTML = ""; updateUI();
}
$("#btnGo").onclick = async () => {
  const st = S.status;
  const body = modalMode === "live"
    ? { mode: "live", day: st.next_day, backend: $("#backend").value, step: parseInt($("#step").value, 10),
        murders: $("#murders").value === "1", motive: $("#motive").value.trim(), rule: $("#rule").value, rule_text: $("#ruleText").value.trim(),
        mischief: $("#mischief").value, confessionals: $("#confessionals").value === "1", chaos: $("#chaos").value, variation: parseInt($("#variation").value, 10) || 0, lean: $("#lean").value === "1", call_cap: parseInt($("#callCap").value, 10) || 0, autodir: $("#autodir").checked, week_len: parseInt($("#weekLen").value, 10) || 0, resume: !!S.resumeNext }
    : { mode: "replay", day: parseInt($("#replayDay").value, 10) };
  if (body.rule === "custom" && !body.rule_text) { $("#modalErr").textContent = "Type your rule in the box, or pick another rule option."; return; }
  S.resumeNext = false;
  const r = await (await fetch("/api/start", { method: "POST", body: JSON.stringify(body) })).json();
  if (!r.ok) { $("#modalErr").textContent = r.error; return; }
  await reloadWorld();
  resetSession();
  S.session = true; S.mode = body.mode; S.day = body.day; S.hour = 8;
  $("#modal").style.display = "none";
  updateUI();
  await showPrevious(body.day);
};

// ---------- newcomer modal ----------
function openNewcomer() {
  const st = S.status;
  const genders = [...new Set((st.vacancies || []).map((v) => v.gender))];
  $("#nGender").innerHTML = genders.map((g) => `<option value="${g}">${g}</option>`).join("");
  $("#nErr").textContent = "";
  const nb = $("#nBackend"); nb.innerHTML = "";
  [["cli", "Claude subscription", st.backends.cli], ["api", "Anthropic API", st.backends.api], ["mock", "Mock AI (test stub)", true]].filter((x) => x[2]).forEach((x) => { const o = document.createElement("option"); o.value = x[0]; o.textContent = x[1]; nb.appendChild(o); });
  $("#nmodal").style.display = "flex";
}
$("#nCancel").onclick = () => ($("#nmodal").style.display = "none");
$("#nDevelop").onclick = async () => {
  const body = { name: $("#nName").value, gender: $("#nGender").value, role: $("#nRole").value, age: $("#nAge").value, origin: $("#nOrigin").value,
    persona: $("#nPersona").value, secret: $("#nSecret").value, likes: $("#nLikes").value, dislikes: $("#nDislikes").value,
    speech: $("#nSpeech").value, goals: $("#nGoals").value, items: $("#nItems").value, backend: $("#nBackend").value };
  $("#nErr").textContent = "The AI is writing...";
  $("#nDevelop").disabled = true;
  try {
    const r = await (await fetch("/api/newcomer/develop", { method: "POST", body: JSON.stringify(body) })).json();
    if (!r.ok) { $("#nErr").textContent = r.error; return; }
    const f = r.fields, map = { role: "nRole", age: "nAge", origin: "nOrigin", items: "nItems", persona: "nPersona", secret: "nSecret", likes: "nLikes", dislikes: "nDislikes", speech: "nSpeech", goals: "nGoals" };
    for (const [k, id] of Object.entries(map)) if (f[k] !== undefined) { const el = $("#" + id); if (!String(el.value).trim() || (k === "age" && el.value === "26")) el.value = f[k]; }
    $("#nErr").textContent = "Filled in the blanks. Edit anything you like, then add them to the cast." + (f.drive ? " (Hidden drive: " + f.drive + ")" : "");
    $("#nAi").checked = false;
  } catch (e) { $("#nErr").textContent = "Could not reach the AI: " + e; }
  finally { $("#nDevelop").disabled = false; }
};
$("#nGo").onclick = async () => {
  const body = {
    name: $("#nName").value, gender: $("#nGender").value, role: $("#nRole").value, age: $("#nAge").value, origin: $("#nOrigin").value,
    persona: $("#nPersona").value, secret: $("#nSecret").value, likes: $("#nLikes").value, dislikes: $("#nDislikes").value,
    speech: $("#nSpeech").value, goals: $("#nGoals").value, items: $("#nItems").value,
    ai: $("#nAi").checked, backend: $("#nBackend").value,
  };
  const f = $("#nPortrait").files[0];
  if (f) body.portrait = await new Promise((res) => { const fr = new FileReader(); fr.onload = () => res(fr.result); fr.readAsDataURL(f); });
  const r = await (await fetch("/api/newcomer", { method: "POST", body: JSON.stringify(body) })).json();
  if (!r.ok) { $("#nErr").textContent = r.error; return; }
  $("#nmodal").style.display = "none";
  ["nName", "nRole", "nOrigin", "nPersona", "nSecret", "nLikes", "nDislikes", "nSpeech", "nGoals", "nItems"].forEach((id) => ($("#" + id).value = ""));
  $("#nPortrait").value = "";
  S.imgs[r.id] = null;
  await reloadWorld(); await openModal();
};

// ---------- director ----------
function dirSync() {
  const t = $("#dType").value;
  const show = (id, v) => ($("#" + id).style.display = v ? "" : "none");
  show("dToF", t === "whisper" || t === "rumor"); show("dAboutF", t === "rumor"); show("dRoomF", t === "item" || (t === "schedule" && $("#dSOp").value !== "cancel")); show("dEvF", t === "event");
  show("dSchedF", t === "schedule"); show("dSId", t === "schedule" && $("#dSOp").value !== "add"); show("dSAt", t === "schedule" && $("#dSOp").value !== "cancel");
  show("dTextF", t !== "event" && !(t === "schedule" && $("#dSOp").value !== "add"));
  $("#dToL").textContent = t === "rumor" ? "Who hears it" : "To";
  $("#dTextL").textContent = t === "schedule" ? "What it is for (optional)" : t === "item" ? "Item name" : t === "rumor" ? "The rumor" : t === "whisper" ? "The note" : t === "announce" ? "What TereVi says" : "Hint for TereVi (optional)";
}
$("#dType").onchange = dirSync;
$("#dSOp").onchange = dirSync;
$("#btnDirector").onclick = () => {
  const alive_ = Object.keys(S.W.characters).filter((id) => (S.W.characters[id].status || "alive") === "alive" && !(S.state && S.state.agents[id] && !alive(S.state.agents[id])));
  const opts = alive_.map((id) => `<option value="${id}">${esc(info(id).name)}</option>`).join("");
  $("#dTo").innerHTML = `<option value="all">Everyone</option>` + opts; $("#dAbout").innerHTML = opts;
  $("#dRoom").innerHTML = Object.entries(S.W.rooms).map(([id, r]) => `<option value="${id}">${esc(r.name)}</option>`).join("");
  $("#dErr").textContent = ""; $("#dText").value = ""; dirSync();
  $("#dmodal").style.display = "flex";
};
$("#dClose").onclick = () => ($("#dmodal").style.display = "none");
$("#dSend").onclick = async () => {
  const t = $("#dType").value, text = $("#dText").value.trim();
  const body = { type: t };
  if (t === "whisper") { if ($("#dTo").value === "all") { $("#dErr").textContent = "Pick one person."; return; } body.to = $("#dTo").value; body.text = text; }
  else if (t === "rumor") { body.about = $("#dAbout").value; body.claim = text; body.to = $("#dTo").value; }
  else if (t === "item") { body.room = $("#dRoom").value; body.name = text; }
  else if (t === "event") body.id = $("#dEv").value;
  else if (t === "schedule") { const [hh, mm] = ($("#dSAt").value || "15:30").split(":").map(Number); body.op = $("#dSOp").value; body.id = $("#dSId").value; body.at = hh * 60 + mm; body.room = $("#dRoom").value; body.text = text; }
  else body.text = text;
  if ((t === "whisper" || t === "rumor" || t === "item" || t === "announce") && !text) { $("#dErr").textContent = "Write something first."; return; }
  const r = await (await fetch("/api/gm", { method: "POST", body: JSON.stringify(body) })).json();
  $("#dErr").textContent = r.ok ? "Sent: " + r.note + "." : r.error;
  if (r.ok) $("#dText").value = "";
};

// ---------- boot ----------
async function boot() {
  await reloadWorld();
  resize(); setPositions(homeMap());
  try { await TileMap.init(); } catch (e) { S.mapMode = "rooms"; }
  setMapMode(S.mapMode);
  $("#pace").value = String(S.pace); if (!$("#pace").value) $("#pace").value = "50";
  $("#pace").onchange = (e) => { S.pace = Number(e.target.value) || 50; try { localStorage.setItem("mcPace", String(S.pace)); } catch (x) { /* private mode */ } };
  $("#btnRoster").onclick = () => setRoster(!$("#stage").classList.contains("roster-on"));
  setRoster(S.rosterOn === null ? true : S.rosterOn);
  requestAnimationFrame(frame);
  playLoop(); poll(); updateUI();
  const st = await refreshStatus();
  if (st.session && !st.session.aborted) await fetch("/api/stop", { method: "POST", body: "{}" });
  openModal();
}
boot();

// ---- tuning panel
let TUNE = null;
async function openTuning() {
  TUNE = await (await fetch("/api/tuning")).json();
  const groups = {};
  TUNE.settings.forEach((x) => (groups[x.group] = groups[x.group] || []).push(x));
  $("#tuneBody").innerHTML = Object.entries(groups).map(([g, xs]) => `<div class="hdr2">${esc(g)}</div>` + xs.map((x) => {
    const v = TUNE.values[x.key];
    return `<div class="field"><label class="t">${esc(x.label)}: <b id="tv_${x.key}">${v}</b></label>
      <input type="range" data-k="${x.key}" min="${x.min}" max="${x.max}" step="${x.step}" value="${v}" style="width:100%">
      <div class="warn">${esc(x.help)}${x.default !== undefined ? ` (default ${x.default})` : ""}</div></div>`;
  }).join("")).join("");
  $("#tuneBody").querySelectorAll("input[type=range]").forEach((el) => (el.oninput = () => ($("#tv_" + el.dataset.k).textContent = el.value)));
  $("#tErr").textContent = "";
  $("#tmodal").style.display = "flex";
}
$("#btnTuning").onclick = openTuning;
$("#tClose").onclick = () => ($("#tmodal").style.display = "none");
$("#tDefaults").onclick = () => {
  TUNE.settings.forEach((x) => { const el = $("#tuneBody").querySelector(`input[data-k="${x.key}"]`); if (el) { el.value = x.default; $("#tv_" + x.key).textContent = x.default; } });
};
$("#tSave").onclick = async () => {
  const values = {};
  $("#tuneBody").querySelectorAll("input[type=range]").forEach((el) => (values[el.dataset.k] = parseFloat(el.value)));
  const r = await (await fetch("/api/tuning", { method: "POST", body: JSON.stringify({ values }) })).json();
  if (!r.ok) { $("#tErr").textContent = r.error || "Could not save."; return; }
  $("#tmodal").style.display = "none";
};
