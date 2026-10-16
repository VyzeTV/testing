"use strict";
// The tile map as a mode of the main viewer: light tileset drawn in code, five levels, portrait tokens walking the live plan of each turn, fire, smoke, water, marks and items,
// darkness, noise, perception overlay, a map editor, and pause dialogs for important events. Exposes window.TileMap; app.js owns the playback and tells it the turn and the minute.
(function () {
  const REN = 32;
  const G = { map: null, plane: "ground", gm: false, view: { s: 12, ox: 0, oy: 0 }, atlas: new Map(), rows: {}, rooms: [], drag: null, hover: null };
  // ---------- tile painters (light tileset) ----------
function hash(x, y, k) { let h = (x * 374761393 + y * 668265263 + (k || 0) * 2147483647) | 0; h = (h ^ (h >>> 13)) * 1274126177; return ((h ^ (h >>> 16)) >>> 0) / 4294967295; }
function rgb(c, d) { const n = parseInt(c.slice(1), 16); const f = (v) => Math.max(0, Math.min(255, v + d)); return `rgb(${f(n >> 16)},${f((n >> 8) & 255)},${f(n & 255)})`; }

// ---------- tile painters (light tileset) ----------
const PAINT = {
  w(c, v) { c.fillStyle = "#c9a878"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#a98756"; c.lineWidth = 1; for (let i = 0; i < 4; i++) { const y = i * 8 + 0.5; c.beginPath(); c.moveTo(0, y); c.lineTo(REN, y); c.stroke(); const x = 6 + ((i * 11 + v * 7) % 20); c.beginPath(); c.moveTo(x, y); c.lineTo(x, y + 8); c.stroke(); } grain(c, v, "#b79866"); },
  k(c, v) { c.fillStyle = "#dfe6e4"; c.fillRect(0, 0, REN, REN); c.fillStyle = "#c9d3d0"; c.fillRect(0, 0, 16, 16); c.fillRect(16, 16, 16, 16); c.strokeStyle = "#aab6b3"; c.lineWidth = 1; c.strokeRect(0.5, 0.5, 15, 15); c.strokeRect(16.5, 16.5, 15, 15); },
  c(c, v) { c.fillStyle = "#8c4a55"; c.fillRect(0, 0, REN, REN); c.fillStyle = "#a35d69"; for (let i = 0; i < 14; i++) c.fillRect((hash(i, v, 1) * 30) | 0, (hash(i, v, 2) * 30) | 0, 2, 2); c.strokeStyle = "#7a3d47"; c.strokeRect(2.5, 2.5, REN - 5, REN - 5); },
  r(c, v) { c.fillStyle = "#9a9aa0"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#7d7d84"; c.lineWidth = 1; c.strokeRect(0.5, 0.5, 15, 15); c.strokeRect(16.5, 0.5, 15, 15); c.strokeRect(8.5, 16.5, 15, 15); c.strokeRect(0.5, 16.5, 7, 15); c.strokeRect(24.5, 16.5, 7, 15); grain(c, v, "#8a8a91"); },
  m(c, v) { c.fillStyle = "#6c7278"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#565c62"; c.strokeRect(1.5, 1.5, REN - 3, REN - 3); c.fillStyle = "#8d949a"; [[4, 4], [26, 4], [4, 26], [26, 26]].forEach(([x, y]) => { c.beginPath(); c.arc(x, y, 1.6, 0, 6.3); c.fill(); }); },
  ",": (c, v) => { c.fillStyle = "#6f9a4c"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#5c8640"; c.lineWidth = 1.3; for (let i = 0; i < 7; i++) { const x = hash(i, v, 3) * 30 + 1, y = hash(i, v, 4) * 28 + 3; c.beginPath(); c.moveTo(x, y); c.lineTo(x - 1.5, y - 4); c.moveTo(x, y); c.lineTo(x + 1.5, y - 4); c.stroke(); } },
  g: (c, v) => { c.fillStyle = v % 2 ? "#86b95c" : "#7db155"; c.fillRect(0, 0, REN, REN); c.fillStyle = "rgba(255,255,255,.07)"; c.fillRect(0, 0, REN, 16); },
  s: (c, v) => { c.fillStyle = "#e8d6a0"; c.fillRect(0, 0, REN, REN); c.fillStyle = "#d2bd85"; for (let i = 0; i < 12; i++) c.fillRect((hash(i, v, 5) * 30) | 0, (hash(i, v, 6) * 30) | 0, 2, 1); },
  "~": (c, v) => { c.fillStyle = "#4f9bd9"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#a6d3f2"; c.lineWidth = 1.4; for (let r = 0; r < 2; r++) { c.beginPath(); const y = 10 + r * 14; c.moveTo(1, y); c.quadraticCurveTo(8, y - 5, 16, y); c.quadraticCurveTo(24, y + 5, 31, y); c.stroke(); } },
  ":": (c, v) => { c.fillStyle = "#e4d2b0"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#c7b28a"; for (let i = 0; i < 4; i++) { c.beginPath(); c.moveTo(0, i * 8 + 0.5); c.lineTo(REN, i * 8 + 0.5); c.stroke(); } },
  p: (c, v) => { c.fillStyle = "#b39a76"; c.fillRect(0, 0, REN, REN); c.fillStyle = "#9c8561"; for (let i = 0; i < 6; i++) { c.beginPath(); c.ellipse(hash(i, v, 7) * 26 + 3, hash(i, v, 8) * 26 + 3, 4.5, 3.2, hash(i, v, 9) * 3, 0, 6.3); c.fill(); } },
};
Object.assign(PAINT, {
  a: (c, v) => { c.fillStyle = "#6fb7dd"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "rgba(255,255,255,.45)"; c.lineWidth = 1.2; c.beginPath(); const y = 10 + (v % 3) * 6; c.moveTo(3, y); c.quadraticCurveTo(12, y - 3, 20, y); c.quadraticCurveTo(26, y + 3, 30, y); c.stroke(); },
  n: (c, v) => { PAINT.s(c, v); c.strokeStyle = "#8a9a55"; c.lineWidth = 1.2; for (let i = 0; i < 4; i++) { const x = hash(i, v, 13) * 28 + 2, y = hash(i, v, 14) * 26 + 4; c.beginPath(); c.moveTo(x, y); c.lineTo(x - 2, y - 5); c.moveTo(x, y); c.lineTo(x + 2, y - 5); c.stroke(); } },
  q: (c, v) => { c.fillStyle = "#8d8a82"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#6f6c65"; c.lineWidth = 1; c.beginPath(); c.moveTo(hash(1, v, 15) * 32, 0); c.lineTo(hash(2, v, 15) * 32, 16); c.lineTo(hash(3, v, 15) * 32, 32); c.stroke(); grain(c, v, "#a29e95"); },
  f: (c, v) => { c.fillStyle = "#6b4a2e"; c.fillRect(0, 0, REN, REN); const cols = ["#e85d75", "#f5c542", "#b37be8", "#f2f2f2"]; for (let i = 0; i < 6; i++) { c.fillStyle = cols[(i + v) % 4]; c.beginPath(); c.arc(hash(i, v, 16) * 26 + 3, hash(i, v, 17) * 26 + 3, 2.4, 0, 6.3); c.fill(); } },
  B: (c, v) => { c.fillStyle = "#b08a5a"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#8a6a40"; for (let i = 0; i < 4; i++) { c.beginPath(); c.moveTo(i * 8 + 0.5, 0); c.lineTo(i * 8 + 0.5, REN); c.stroke(); } },
  j: (c, v) => { c.fillStyle = "#7a5a38"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#5a3f22"; for (let i = 0; i < 4; i++) { c.beginPath(); c.moveTo(0, i * 8 + 0.5); c.lineTo(REN, i * 8 + 0.5); c.stroke(); } c.fillStyle = "#4a3218"; c.fillRect(1, 1, 3, 3); c.fillRect(28, 28, 3, 3); },
  T: (c, v) => { PAINT[","](c, v); c.fillStyle = "#24572b"; c.beginPath(); c.arc(16, 16, 15, 0, 6.3); c.fill(); c.fillStyle = "#2f6e36"; c.beginPath(); c.arc(12 + (v % 2) * 3, 12, 8, 0, 6.3); c.fill(); c.fillStyle = "rgba(255,255,255,.08)"; c.beginPath(); c.arc(10, 9, 4, 0, 6.3); c.fill(); },
  b: (c, v) => { PAINT[","](c, v); c.fillStyle = "#3d7d3a"; c.beginPath(); c.arc(16, 17, 10, 0, 6.3); c.fill(); c.fillStyle = "#4f944a"; c.beginPath(); c.arc(13, 14, 5, 0, 6.3); c.fill(); },
  H: (c, v) => { c.fillStyle = "#1f4d25"; c.fillRect(0, 0, REN, REN); c.fillStyle = "#2b6331"; for (let i = 0; i < 8; i++) { c.beginPath(); c.arc(hash(i, v, 18) * 30 + 1, hash(i, v, 19) * 30 + 1, 4, 0, 6.3); c.fill(); } },
  C: (c, v) => { c.fillStyle = "#5a5650"; c.fillRect(0, 0, REN, REN); c.fillStyle = "#3c3935"; c.fillRect(0, 18, REN, 14); c.strokeStyle = "#2a2724"; c.lineWidth = 2; c.beginPath(); c.moveTo(0, 18); for (let x = 0; x <= REN; x += 8) c.lineTo(x, 16 + ((x / 8 + v) % 2) * 4); c.stroke(); },
  K: (c, v) => { c.fillStyle = "#a9a08f"; c.fillRect(0, 0, REN, REN); for (let i = 0; i < 4; i++) { c.fillStyle = `rgb(${150 + i * 20},${142 + i * 20},${126 + i * 18})`; c.fillRect(0, i * 8, REN, 7); } },
  S: (c, v) => { c.fillStyle = "#8c4a3a"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#6d3729"; c.lineWidth = 1; for (let r = 0; r < 4; r++) { const y = r * 8 + 0.5; c.beginPath(); c.moveTo(0, y); c.lineTo(REN, y); c.stroke(); const off = r % 2 ? 6 : 0; for (let x = off; x < REN; x += 12) { c.beginPath(); c.moveTo(x + 0.5, y); c.lineTo(x + 0.5, y + 8); c.stroke(); } } },
  v: (c, v) => { c.fillStyle = "#15161c"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "rgba(255,255,255,.07)"; c.lineWidth = 1; for (let i = -REN; i < REN; i += 8) { c.beginPath(); c.moveTo(i, REN); c.lineTo(i + REN, 0); c.stroke(); } },
  x: (c, v) => { c.fillStyle = "#e4d2b0"; c.fillRect(0, 0, REN, REN); c.strokeStyle = "#6e4a1f"; c.lineWidth = 3; c.beginPath(); c.moveTo(0, 16); c.lineTo(32, 16); c.stroke(); c.lineWidth = 2; for (let i = 4; i < 32; i += 8) { c.beginPath(); c.moveTo(i, 10); c.lineTo(i, 22); c.stroke(); } },
  l: (c, v) => { PAINT.r(c, v); c.strokeStyle = "#6e4a1f"; c.lineWidth = 3; c.beginPath(); c.moveTo(9, 0); c.lineTo(9, 32); c.moveTo(23, 0); c.lineTo(23, 32); c.stroke(); c.lineWidth = 2; for (let y = 4; y < 32; y += 7) { c.beginPath(); c.moveTo(9, y); c.lineTo(23, y); c.stroke(); } },
});
function grain(c, v, col) { c.fillStyle = col; for (let i = 0; i < 5; i++) c.fillRect((hash(i, v, 11) * 28) | 0, (hash(i, v, 12) * 28) | 0, 3, 1); }
function wallPaint(c, v, mask) {
  c.fillStyle = "#b8b3a6"; c.fillRect(0, 0, REN, REN);
  c.strokeStyle = "#8f8a7d"; c.lineWidth = 1;
  for (let r = 0; r < 4; r++) { const y = r * 8 + 0.5; c.beginPath(); c.moveTo(0, y); c.lineTo(REN, y); c.stroke(); const off = r % 2 ? 8 : 0; for (let x = off; x < REN; x += 16) { c.beginPath(); c.moveTo(x + 0.5, y); c.lineTo(x + 0.5, y + 8); c.stroke(); } }
  c.fillStyle = "rgba(255,255,255,.35)"; if (mask & 1) c.fillRect(0, 0, REN, 5);         // north neighbour is open: lit top edge
  c.fillStyle = "rgba(0,0,0,.18)"; if (mask & 2) c.fillRect(0, REN - 4, REN, 4);          // south neighbour is open: shaded base
}
function doorPaint(c, v, vertical, locked) {
  PAINT.w(c, v);
  c.fillStyle = "#8a5a2b"; c.strokeStyle = "#5e3b17"; c.lineWidth = 2;
  if (vertical) { c.fillRect(3, 9, 26, 14); c.strokeRect(3, 9, 26, 14); } else { c.fillRect(9, 3, 14, 26); c.strokeRect(9, 3, 14, 26); }
  c.fillStyle = "#fac775"; c.beginPath(); c.arc(vertical ? 24 : 20, vertical ? 16 : 18, 2.2, 0, 6.3); c.fill();
  if (locked) { c.fillStyle = "#f0c040"; c.strokeStyle = "#7a5c00"; c.lineWidth = 1.5; c.fillRect(11, 13, 10, 9); c.strokeRect(11, 13, 10, 9); c.beginPath(); c.arc(16, 13, 4, Math.PI, 0); c.stroke(); }
}
function windowPaint(c, v, mask) {
  wallPaint(c, v, mask); c.fillStyle = "#cfe9f7"; c.strokeStyle = "#5e6a72"; c.lineWidth = 2; c.fillRect(5, 8, 22, 16); c.strokeRect(5, 8, 22, 16);
  c.beginPath(); c.moveTo(16, 8); c.lineTo(16, 24); c.moveTo(5, 16); c.lineTo(27, 16); c.stroke();
}
function stairPaint(c, v, down) {
  PAINT.r(c, v); c.fillStyle = "#6e6a62"; for (let i = 0; i < 5; i++) { c.fillStyle = `rgb(${120 + i * 22},${116 + i * 22},${108 + i * 20})`; c.fillRect(2, 3 + i * 5.6, REN - 4, 5); }
  c.fillStyle = "#222"; c.font = "bold 14px system-ui"; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText(down ? "▼" : "▲", 16, 16);
}
function hatchPaint(c, v, gm, floorCh) {
  (PAINT[floorCh] || PAINT.w)(c, v);
  if (!gm) return;
  c.strokeStyle = "#ff4dd2"; c.lineWidth = 2.2; c.strokeRect(5, 5, 22, 22); c.beginPath(); c.moveTo(5, 5); c.lineTo(27, 27); c.moveTo(27, 5); c.lineTo(5, 27); c.stroke();
}

// ---------- furniture sprites ----------
const FURN = {
  bed: (c) => { rr(c, 4, 3, 24, 26, "#d9d2c4", "#7d6f58"); rr(c, 6, 5, 20, 7, "#fff", "#aaa"); rr(c, 4, 14, 24, 15, "#5f86c4", "#3c5b8f"); },
  wardrobe: (c) => { rr(c, 3, 4, 26, 24, "#8a5a2b", "#5e3b17"); c.strokeStyle = "#5e3b17"; c.beginPath(); c.moveTo(16, 4); c.lineTo(16, 28); c.stroke(); dot(c, 13, 16, "#fac775"); dot(c, 19, 16, "#fac775"); },
  desk: (c) => { rr(c, 3, 7, 26, 18, "#a87238", "#6e4a1f"); rr(c, 8, 10, 10, 6, "#f4f1e6", "#999"); },
  table: (c) => { rr(c, 2, 5, 28, 22, "#a87238", "#6e4a1f"); c.fillStyle = "rgba(255,255,255,.12)"; c.fillRect(4, 7, 24, 4); },
  chair: (c) => { rr(c, 8, 8, 16, 16, "#8a5a2b", "#5e3b17"); rr(c, 8, 5, 16, 5, "#6e4a1f", "#4a2f10"); },
  shelf: (c) => { rr(c, 2, 5, 28, 22, "#7a4e22", "#4a2f10"); const cols = ["#c0392b", "#2e86c1", "#27ae60", "#f1c40f", "#8e44ad"]; for (let r = 0; r < 2; r++) for (let i = 0; i < 6; i++) { c.fillStyle = cols[(i + r * 2) % 5]; c.fillRect(4 + i * 4.4, 7 + r * 10, 3.4, 8); } },
  sofa: (c) => { rr(c, 2, 8, 28, 18, "#b84a5a", "#7a2d39"); rr(c, 2, 6, 28, 6, "#a03a49", "#7a2d39"); },
  stove: (c) => { rr(c, 3, 4, 26, 24, "#444a50", "#22272b"); [[10, 11], [22, 11], [10, 21], [22, 21]].forEach(([x, y]) => { c.strokeStyle = "#999"; c.lineWidth = 1.6; c.beginPath(); c.arc(x, y, 4, 0, 6.3); c.stroke(); }); },
  sink: (c) => { rr(c, 3, 5, 26, 22, "#e8ecef", "#9aa4ab"); rr(c, 8, 9, 16, 13, "#bcd6e6", "#7a98ab"); dot(c, 16, 7, "#777"); },
  barrel: (c) => { c.fillStyle = "#8a5a2b"; c.strokeStyle = "#4a2f10"; c.lineWidth = 2; c.beginPath(); c.arc(16, 16, 12, 0, 6.3); c.fill(); c.stroke(); c.strokeStyle = "#c7a15a"; c.beginPath(); c.arc(16, 16, 7, 0, 6.3); c.stroke(); },
  crate: (c) => { rr(c, 4, 4, 24, 24, "#b98c4e", "#6e4a1f"); c.strokeStyle = "#6e4a1f"; c.beginPath(); c.moveTo(4, 4); c.lineTo(28, 28); c.moveTo(28, 4); c.lineTo(4, 28); c.stroke(); },
  chest: (c) => { rr(c, 3, 9, 26, 16, "#7a4e22", "#4a2f10"); rr(c, 3, 9, 26, 6, "#946129", "#4a2f10"); dot(c, 16, 16, "#fac775"); },
  plant: (c) => { rr(c, 11, 19, 10, 9, "#a86a3a", "#6e4a1f"); c.fillStyle = "#3f8f3f"; [[16, 12, 8], [10, 15, 6], [22, 15, 6]].forEach(([x, y, r]) => { c.beginPath(); c.arc(x, y, r, 0, 6.3); c.fill(); }); },
  piano: (c) => { rr(c, 2, 4, 28, 24, "#1f1f24", "#000"); c.fillStyle = "#fff"; for (let i = 0; i < 7; i++) c.fillRect(4 + i * 3.6, 16, 3, 9); c.fillStyle = "#000"; for (let i = 0; i < 6; i++) c.fillRect(6 + i * 3.6, 16, 2, 5); },
  easel: (c) => { c.strokeStyle = "#6e4a1f"; c.lineWidth = 2; c.beginPath(); c.moveTo(8, 28); c.lineTo(16, 6); c.lineTo(24, 28); c.stroke(); rr(c, 9, 8, 14, 12, "#f4f1e6", "#999"); c.fillStyle = "#e57373"; c.fillRect(11, 11, 5, 5); c.fillStyle = "#64b5f6"; c.fillRect(17, 13, 4, 5); },
  telescope: (c) => { c.strokeStyle = "#333"; c.lineWidth = 2; c.beginPath(); c.moveTo(16, 18); c.lineTo(9, 29); c.moveTo(16, 18); c.lineTo(23, 29); c.stroke(); c.save(); c.translate(16, 14); c.rotate(-0.7); rr(c, -10, -4, 22, 8, "#3b5b8f", "#1d2f4d"); c.restore(); },
  railing: (c) => { c.strokeStyle = "#7a5a3a"; c.lineWidth = 3; c.beginPath(); c.moveTo(0, 16); c.lineTo(32, 16); c.stroke(); c.lineWidth = 2; for (let i = 3; i < 32; i += 8) { c.beginPath(); c.moveTo(i, 10); c.lineTo(i, 22); c.stroke(); } },
  poolTable: (c) => { rr(c, 2, 5, 28, 22, "#2f7a4a", "#5e3b17"); c.fillStyle = "#fff"; c.beginPath(); c.arc(11, 16, 2.4, 0, 6.3); c.fill(); c.fillStyle = "#c0392b"; c.beginPath(); c.arc(21, 14, 2.4, 0, 6.3); c.fill(); },
  washer: (c) => { rr(c, 4, 4, 24, 24, "#e8ecef", "#9aa4ab"); c.strokeStyle = "#7a98ab"; c.lineWidth = 2; c.beginPath(); c.arc(16, 17, 7, 0, 6.3); c.stroke(); dot(c, 8, 8, "#c0392b"); },
  tub: (c) => { rr(c, 2, 6, 28, 20, "#e8ecef", "#9aa4ab"); rr(c, 5, 9, 22, 14, "#b6d7ea", "#7a98ab"); },
  cabinet: (c) => { rr(c, 4, 5, 24, 22, "#d6d2c8", "#8f8a7d"); c.fillStyle = "#c0392b"; c.fillRect(14, 9, 4, 14); c.fillRect(11, 14, 10, 4); },
  radio: (c) => { rr(c, 5, 9, 22, 14, "#3d3d44", "#1b1b20"); c.strokeStyle = "#9aa"; c.beginPath(); c.moveTo(22, 9); c.lineTo(27, 2); c.stroke(); dot(c, 11, 16, "#ffb347"); dot(c, 17, 16, "#6be38f"); },
  boiler: (c) => { rr(c, 6, 3, 20, 26, "#6c7278", "#3a3f44"); dot(c, 16, 11, "#ff8a4c"); dot(c, 16, 21, "#aaa"); },
  fuseBox: (c) => { rr(c, 8, 6, 16, 20, "#575d63", "#2a2e32"); c.fillStyle = "#ffd54f"; c.beginPath(); c.moveTo(17, 9); c.lineTo(12, 17); c.lineTo(16, 17); c.lineTo(14, 24); c.lineTo(21, 15); c.lineTo(17, 15); c.closePath(); c.fill(); },
  workbench: (c) => { rr(c, 2, 8, 28, 16, "#8a5a2b", "#4a2f10"); c.fillStyle = "#aaa"; c.fillRect(6, 11, 8, 3); c.fillRect(18, 15, 6, 6); },
  freezer: (c) => { rr(c, 3, 4, 26, 24, "#cfe9f7", "#7a98ab"); c.strokeStyle = "#7a98ab"; c.beginPath(); c.moveTo(3, 16); c.lineTo(29, 16); c.stroke(); },
  terminal: (c) => { rr(c, 6, 6, 20, 14, "#20262b", "#000"); c.fillStyle = "#6be38f"; c.fillRect(8, 8, 16, 2); c.fillRect(8, 12, 10, 2); rr(c, 10, 22, 12, 5, "#555", "#222"); },
  locker: (c) => { rr(c, 4, 3, 24, 26, "#7a8a96", "#3d4850"); c.strokeStyle = "#3d4850"; c.beginPath(); c.moveTo(16, 3); c.lineTo(16, 29); c.stroke(); dot(c, 13, 16, "#ddd"); dot(c, 19, 16, "#ddd"); },
  lamp: (c) => { c.fillStyle = "rgba(255,220,120,.35)"; c.beginPath(); c.arc(16, 16, 14, 0, 6.3); c.fill(); dot(c, 16, 16, "#ffd54f"); c.strokeStyle = "#a07000"; c.beginPath(); c.arc(16, 16, 5, 0, 6.3); c.stroke(); },
  generator: (c) => { rr(c, 3, 5, 26, 22, "#a8442f", "#5e2214"); c.fillStyle = "#ffd54f"; c.fillRect(7, 9, 8, 6); rr(c, 18, 9, 8, 14, "#444", "#222"); },
  plantBed: (c) => { rr(c, 2, 4, 28, 24, "#6e4a1f", "#3e2a10"); c.fillStyle = "#4caf50"; for (let i = 0; i < 6; i++) { c.beginPath(); c.arc(7 + (i % 3) * 9, 10 + ((i / 3) | 0) * 11, 4, 0, 6.3); c.fill(); } },
  boat: (c) => { c.fillStyle = "#8a5a2b"; c.strokeStyle = "#4a2f10"; c.lineWidth = 2; c.beginPath(); c.moveTo(2, 14); c.quadraticCurveTo(16, 32, 30, 14); c.lineTo(2, 14); c.fill(); c.stroke(); c.strokeStyle = "#ddd"; c.beginPath(); c.moveTo(16, 14); c.lineTo(16, 2); c.stroke(); },
  podium: (c) => { rr(c, 6, 6, 20, 20, "#6c4a8c", "#3a2650"); c.fillStyle = "#e0d0f0"; c.fillRect(10, 10, 12, 3); },
  monitor: (c) => { rr(c, 3, 5, 26, 18, "#101418", "#000"); c.fillStyle = "#ff5fa2"; c.fillRect(6, 8, 20, 12); c.fillStyle = "#fff"; c.font = "bold 9px system-ui"; c.textAlign = "center"; c.fillText("TV", 16, 18); },
  tree: (c) => { c.fillStyle = "#6e4a1f"; c.fillRect(14, 20, 5, 10); c.fillStyle = "#2f7a3a"; c.beginPath(); c.arc(16, 14, 13, 0, 6.3); c.fill(); c.fillStyle = "#3f9a4a"; c.beginPath(); c.arc(12, 11, 6, 0, 6.3); c.fill(); },
  bench: (c) => { rr(c, 2, 11, 28, 8, "#a87238", "#6e4a1f"); },
  deckChair: (c) => { rr(c, 6, 4, 20, 24, "#f4f1e6", "#aaa"); c.fillStyle = "#e57373"; c.fillRect(6, 10, 20, 4); c.fillRect(6, 18, 20, 4); },
  driftwood: (c) => { c.strokeStyle = "#8b7355"; c.lineWidth = 4; c.lineCap = "round"; c.beginPath(); c.moveTo(5, 22); c.lineTo(26, 9); c.stroke(); c.lineWidth = 2; c.beginPath(); c.moveTo(14, 16); c.lineTo(10, 8); c.stroke(); },
  armchair: (c) => { rr(c, 5, 6, 22, 20, "#7a5a8c", "#4d3860"); rr(c, 5, 4, 22, 7, "#6a4a7c", "#4d3860"); rr(c, 3, 10, 5, 14, "#6a4a7c", "#4d3860"); rr(c, 24, 10, 5, 14, "#6a4a7c", "#4d3860"); },
  fireplace: (c) => { rr(c, 2, 3, 28, 24, "#8a8f94", "#4a4f54"); rr(c, 8, 10, 16, 15, "#241a14", "#111"); c.fillStyle = "#ff8a30"; c.beginPath(); c.moveTo(16, 12); c.quadraticCurveTo(22, 19, 16, 24); c.quadraticCurveTo(10, 19, 16, 12); c.fill(); },
  chessTable: (c) => { rr(c, 4, 4, 24, 24, "#6e4a1f", "#3e2a10"); for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { c.fillStyle = (i + j) % 2 ? "#f1e6c8" : "#2b2b2b"; c.fillRect(8 + i * 4, 8 + j * 4, 4, 4); } },
  dartboard: (c) => { c.fillStyle = "#2b2b2b"; c.beginPath(); c.arc(16, 16, 11, 0, 6.3); c.fill(); c.fillStyle = "#c0392b"; c.beginPath(); c.arc(16, 16, 8, 0, 6.3); c.fill(); c.fillStyle = "#f4f1e6"; c.beginPath(); c.arc(16, 16, 5, 0, 6.3); c.fill(); dot(c, 16, 16, "#27ae60"); },
  mirror: (c) => { rr(c, 8, 3, 16, 26, "#8a5a2b", "#4a2f10"); rr(c, 10, 5, 12, 22, "#cfe9f7", "#9ab"); c.strokeStyle = "rgba(255,255,255,.7)"; c.beginPath(); c.moveTo(12, 9); c.lineTo(18, 5); c.stroke(); },
  fridge: (c) => { rr(c, 6, 3, 20, 26, "#e8ecef", "#9aa4ab"); c.strokeStyle = "#9aa4ab"; c.beginPath(); c.moveTo(6, 13); c.lineTo(26, 13); c.stroke(); c.fillStyle = "#789"; c.fillRect(22, 6, 2, 5); c.fillRect(22, 16, 2, 8); },
  hammock: (c) => { c.strokeStyle = "#6e4a1f"; c.lineWidth = 2; c.beginPath(); c.moveTo(2, 8); c.lineTo(2, 24); c.moveTo(30, 8); c.lineTo(30, 24); c.stroke(); c.fillStyle = "#e5a64a"; c.beginPath(); c.moveTo(3, 12); c.quadraticCurveTo(16, 28, 29, 12); c.lineTo(29, 15); c.quadraticCurveTo(16, 31, 3, 15); c.fill(); },
  firepit: (c) => { c.fillStyle = "#6c7278"; c.beginPath(); c.arc(16, 16, 12, 0, 6.3); c.fill(); c.fillStyle = "#241a14"; c.beginPath(); c.arc(16, 16, 8, 0, 6.3); c.fill(); c.fillStyle = "#ff8a30"; c.beginPath(); c.moveTo(16, 8); c.quadraticCurveTo(22, 16, 16, 23); c.quadraticCurveTo(10, 16, 16, 8); c.fill(); },
  jukebox: (c) => { rr(c, 6, 3, 20, 26, "#b0406a", "#6a2040"); c.fillStyle = "#ffd54f"; c.beginPath(); c.arc(16, 12, 7, Math.PI, 0); c.fill(); rr(c, 10, 18, 12, 7, "#3a1a28"); },
  camera: (c) => { c.fillStyle = "rgba(255,95,162,.9)"; c.beginPath(); c.moveTo(16, 4); c.lineTo(29, 11); c.lineTo(16, 18); c.lineTo(3, 11); c.closePath(); c.fill(); dot(c, 16, 11, "#fff"); },
};
function rr(c, x, y, w, h, fill, stroke) { c.fillStyle = fill; c.fillRect(x, y, w, h); if (stroke) { c.strokeStyle = stroke; c.lineWidth = 1.6; c.strokeRect(x + 0.8, y + 0.8, w - 1.6, h - 1.6); } }
function dot(c, x, y, col) { c.fillStyle = col; c.beginPath(); c.arc(x, y, 2.4, 0, 6.3); c.fill(); }

function sprite(key, painter) {
  let cv = G.atlas.get(key);
  if (!cv) { cv = document.createElement("canvas"); cv.width = cv.height = REN; const c = cv.getContext("2d"); painter(c); G.atlas.set(key, cv); }
  return cv;
}

// ---------- map access ----------
const planeRows = (id) => G.map.planes.find((p) => p.id === id).rows;
function ch(plane, x, y) { const r = G.rows[plane]; return y < 0 || y >= r.length || x < 0 || x >= r[y].length ? " " : r[y][x]; }
const isWall = (p, x, y) => "#=+L".includes(ch(p, x, y)) && ch(p, x, y) !== " ";
const isOpenFloor = (p, x, y) => !"#=+L S~TH".includes(ch(p, x, y));

function tileImage(plane, x, y) {
  const t = ch(plane, x, y), v = Math.floor(hash(x, y, 1) * 4);
  if (t === " ") return null;
  if (t === "#") { const m = (isOpenFloor(plane, x, y - 1) ? 1 : 0) | (isOpenFloor(plane, x, y + 1) ? 2 : 0); return sprite("#" + v + m, (c) => wallPaint(c, v, m)); }
  if (t === "=") { const m = (isOpenFloor(plane, x, y - 1) ? 1 : 0) | (isOpenFloor(plane, x, y + 1) ? 2 : 0); return sprite("=" + m, (c) => windowPaint(c, v, m)); }
  if (t === "+" || t === "L") { const vertical = isWall(plane, x, y - 1) && isWall(plane, x, y + 1); return sprite(t + vertical + v, (c) => doorPaint(c, v, vertical, t === "L")); }
  if (t === "U" || t === "D") return sprite(t + v, (c) => stairPaint(c, v, t === "D"));
  if (t === "h") { const f = floorBeside(plane, x, y); return sprite("h" + G.gm + f + v, (c) => hatchPaint(c, v, G.gm, f)); }
  const painter = PAINT[t];
  return painter ? sprite(t + (t === "g" ? (x + y) % 2 : v), (c) => painter(c, t === "g" ? (x + y) % 2 : v)) : null;
}
function floorBeside(plane, x, y) { for (const [dx, dy] of [[1, 0], [-1, 0], [0, 1], [0, -1]]) { const t = ch(plane, x + dx, y + dy); if ("wkcrmgsq,".includes(t) && t !== " ") return t; } return "r"; }


  // ======================================================================== the tile map as a mode of the main viewer
  // All the levels are drawn at once: the island (ground level) on the left, the house's other levels in a column beside it, each cropped to what is on it
  // (map.view). A tile (plane, x, y) is drawn at world position (view.ox + x - view.x0, view.oy + y - view.y0); G.view turns world positions into pixels.
  const LY = { labels: true, furn: true, cam: false, tint: false, grid: false, items: true, marks: true, light: true, noise: true, perc: false };
  const T = { tick: null, m: 0, follow: null, visible: false, dialogOpen: false };
  const ITEM_COL = { weapon: "#d9534f", food: "#f0ad4e", drink: "#5bc0de", medical: "#5cb85c", tool: "#999", key: "#f1c40f", drug: "#9b59b6", clothing: "#b08968", paper: "#f4f1e6", poison: "#8e44ad" };
  const PLANE_LABEL = { roof: "Roof", second: "Second floor", first: "First floor", ground: "Island and ground floor", basement: "Cellars and tunnels" };
  const PLANE_SHORT = { roof: "Roof", second: "Second", first: "First", ground: "Island", basement: "Cellar" };
  const NAMES = Object.assign({}, { "#": "wall", " ": "nothing" });
  const ZONE_TINT = { roof: "#4a7bbf", second: "#6a5acd", first: "#8a6ad0", ground: "#3aa58a", grounds: "#4aa55a", basement: "#c0644a" };
  const CLS_COL = { critical: "#ff4d6d", important: "#ffb347", notable: "#6c7bd6", background: "#8a8fa8" };
  const CT = 8;                                                     // pixels per tile in the cached picture of each level (used when zoomed out)
  const q = (s) => document.querySelector(s);
  let cv, ctx, tip;

  // ---------------------------------------------------------------- level layout
  const V = (p) => (G.map.view && G.map.view[p]) || { x0: 0, y0: 0, x1: G.map.w, y1: G.map.h, ox: 0, oy: 0 };
  const WX = (p, x) => V(p).ox + x - V(p).x0, WY = (p, y) => V(p).oy + y - V(p).y0;
  const SX = (p, x) => G.view.ox + WX(p, x) * G.view.s, SY = (p, y) => G.view.oy + WY(p, y) * G.view.s;
  function pickAt(px, py) {
    const { s, ox, oy } = G.view, wx = (px - ox) / s, wy = (py - oy) / s;
    for (const p of G.planeIds) {
      const v = V(p);
      if (wx >= v.ox && wx < v.ox + v.x1 - v.x0 && wy >= v.oy && wy < v.oy + v.y1 - v.y0) return { p, x: Math.floor(wx - v.ox + v.x0), y: Math.floor(wy - v.oy + v.y0), fx: wx - v.ox + v.x0, fy: wy - v.oy + v.y0 };
    }
    return null;
  }
  function worldSize() { let w = 0, h = 0; for (const p of G.planeIds) { const v = V(p); w = Math.max(w, v.ox + v.x1 - v.x0); h = Math.max(h, v.oy + v.y1 - v.y0); } return [w, h]; }
  const roomOf = (p, x, y) => { const z = G.zones[p]; if (!z || y < 0 || y >= z.length || x < 0 || x >= z[y].length) return null; return G.map.zone_codes[z[y][x]] || null; };

  // ---------------------------------------------------------------- positions from the live plan
  function trackPos(tr, t) {
    if (!tr || !tr.length) return null;
    if (t <= tr[0][0]) return { plane: tr[0][1], x: tr[0][2], y: tr[0][3] };
    for (let i = 1; i < tr.length; i++) {
      if (t < tr[i][0]) {
        const a = tr[i - 1], b = tr[i];
        if (a[1] !== b[1]) return { plane: a[1], x: a[2], y: a[3] };
        const k = (t - a[0]) / Math.max(0.01, b[0] - a[0]);
        return { plane: a[1], x: a[2] + (b[2] - a[2]) * k, y: a[3] + (b[3] - a[3]) * k };
      }
    }
    const z = tr[tr.length - 1];
    return { plane: z[1], x: z[2], y: z[3] };
  }
  function fallbackPositions(t) {
    // ticks recorded before the live plan existed: stand everyone at their room's label
    const out = {}, per = {};
    for (const [id, a] of Object.entries((t.state && t.state.agents) || {})) {
      const r = G.map.rooms[a.room]; if (!r) continue;
      const n = per[a.room] = (per[a.room] || 0) + 1, c = roomCentre(a.room);
      out[id] = { plane: r.plane, x: c[0] - 1 + ((n - 1) % 3), y: c[1] + Math.floor((n - 1) / 3), dead: a.status && a.status !== "alive", out: !!a.out };
    }
    return out;
  }
  function positions() {
    const t = T.tick; if (!t) return {};
    if (!t.live) return fallbackPositions(t);
    const out = {};
    for (const [cid, tr] of Object.entries(t.live.tracks)) { const p = trackPos(tr, T.m); if (p) out[cid] = { ...p, ...(t.live.flags[cid] || {}) }; }
    return out;
  }
  const info2 = (id) => (window.info ? window.info(id) : { name: id, short: id, color: "#999" });
  const nameOf = (id) => { const c = info2(id); return c.short || c.name || id; };
  function roomCentre(rid) { const r = G.map.rooms[rid]; if (!r) return [0, 0]; if (r.open && r.label) return r.label; const [x0, y0, x1, y1] = r.rect; return [(x0 + x1) / 2 - 0.5, (y0 + y1) / 2 - 0.5]; }

  // ---------------------------------------------------------------- cached pictures of each level, and overlays drawn over whole rooms
  function levelCache(p) {
    const key = p + "|" + G.gm;
    const c0 = G.cache[p];
    if (c0 && c0.key === key) return c0.cv;
    const v = V(p), w = v.x1 - v.x0, h = v.y1 - v.y0, cc = document.createElement("canvas");
    cc.width = w * CT; cc.height = h * CT;
    const c = cc.getContext("2d");
    for (let y = v.y0; y < v.y1; y++) for (let x = v.x0; x < v.x1; x++) { const im = tileImage(p, x, y); if (im) c.drawImage(im, (x - v.x0) * CT, (y - v.y0) * CT, CT, CT); }
    G.cache[p] = { key, cv: cc };
    return cc;
  }
  function patchCache(p, x, y) { const c0 = G.cache[p]; if (!c0) return; const v = V(p), c = c0.cv.getContext("2d"); const im = tileImage(p, x, y); c.clearRect((x - v.x0) * CT, (y - v.y0) * CT, CT, CT); if (im) c.drawImage(im, (x - v.x0) * CT, (y - v.y0) * CT, CT, CT); }
  // fills over whole rooms (light, zone tint), cached per level until what they show changes
  function roomOverlay(p, name, sig, colorOf) {
    const k = name + p, c0 = G.over[k];
    if (c0 && c0.sig === sig) return c0.cv;
    const v = V(p), cc = document.createElement("canvas"); cc.width = (v.x1 - v.x0) * CT; cc.height = (v.y1 - v.y0) * CT;
    const c = cc.getContext("2d");
    for (const [rid, tiles] of Object.entries(G.roomTiles)) {
      const col = colorOf(rid); if (!col) continue;
      c.fillStyle = col;
      for (const [pp, x, y] of tiles) if (pp === p) c.fillRect((x - v.x0) * CT, (y - v.y0) * CT, CT, CT);
    }
    G.over[k] = { sig, cv: cc };
    return cc;
  }
  function drawOverlay(c, p, im) { const v = V(p), s = G.view.s; c.drawImage(im, SX(p, v.x0), SY(p, v.y0), (v.x1 - v.x0) * s, (v.y1 - v.y0) * s); }

  // ---------------------------------------------------------------- overlays
  function itemColor(id) { const tags = ((S.W && S.W.items[id]) || {}).tags || []; for (const t of tags) if (ITEM_COL[t]) return ITEM_COL[t]; return "#c9a878"; }
  function envFrame(t) { const fr = t && t.env && t.env.frames; if (!fr || !fr.length) return null; let f = fr[0]; for (const x of fr) if (x.m <= T.m + 1e-6) f = x; return f; }
  const onScreen = (p, x, y) => { const s = G.view.s, X = SX(p, x), Y = SY(p, y); return X > -s && X < cv.width && Y > -s && Y < cv.height; };
  function drawEnv(c, t) {
    if (!t || !t.env) return;
    const s = G.view.s, now = performance.now(), E = t.env, f = envFrame(t);
    if (LY.light && E.light) {
      const sig = JSON.stringify(E.light);
      for (const p of G.planeIds) drawOverlay(c, p, roomOverlay(p, "light", sig, (rid) => (E.light[rid] === "dark" ? "rgba(4,5,12,.55)" : E.light[rid] ? "rgba(4,5,12,.28)" : null)));
    }
    for (const [p, x, y, st] of E.struct || []) {
      if (!onScreen(p, x, y)) continue; const X = SX(p, x), Y = SY(p, y);
      if (st === "burned") { c.fillStyle = "rgba(20,15,12,.7)"; c.fillRect(X, Y, s, s); } else {
        c.fillStyle = "rgba(60,40,20,.75)"; c.fillRect(X + s * 0.1, Y + s * 0.1, s * 0.8, s * 0.8);
        c.strokeStyle = "#c9a878"; c.lineWidth = Math.max(1, s * 0.06); c.beginPath(); c.moveTo(X + s * 0.15, Y + s * 0.8); c.lineTo(X + s * 0.5, Y + s * 0.2); c.moveTo(X + s * 0.5, Y + s * 0.85); c.lineTo(X + s * 0.85, Y + s * 0.3); c.stroke();
      }
    }
    if (LY.marks) for (const m of E.marks || []) {
      if (!onScreen(m.p, m.x, m.y)) continue; const X = SX(m.p, m.x) + s / 2, Y = SY(m.p, m.y) + s / 2;
      if (m.k === "blood") { c.fillStyle = "rgba(150,10,25,.8)"; c.beginPath(); c.arc(X, Y, s * (0.18 + 0.05 * (m.n || 1)), 0, 6.3); c.fill(); }
      else if (m.k === "drag") { c.strokeStyle = "rgba(110,25,35,.7)"; c.lineWidth = Math.max(1.5, s * 0.14); c.beginPath(); c.moveTo(X - s * 0.4, Y + s * 0.15); c.lineTo(X + s * 0.4, Y - s * 0.15); c.stroke(); }
      else if (m.k === "soot") { c.fillStyle = "rgba(25,22,20,.55)"; c.beginPath(); c.arc(X, Y, s * 0.36, 0, 6.3); c.fill(); }
      else { c.fillStyle = m.k === "glass" ? "rgba(190,230,245,.9)" : "rgba(190,150,100,.9)"; for (let i = 0; i < 4; i++) c.fillRect(X + Math.cos(i * 1.7) * s * 0.28, Y + Math.sin(i * 2.3) * s * 0.28, Math.max(1.5, s * 0.1), Math.max(1.5, s * 0.1)); }
    }
    if (LY.items && s >= 5) for (const it of E.items || []) {
      if (!onScreen(it.p, it.x, it.y)) continue; const X = SX(it.p, it.x), Y = SY(it.p, it.y), k = s * 0.36;
      c.fillStyle = itemColor(it.i); c.strokeStyle = "rgba(0,0,0,.6)"; c.lineWidth = 1; c.beginPath(); c.moveTo(X + s / 2, Y + s / 2 - k / 2 - 1); c.lineTo(X + s / 2 + k / 2, Y + s / 2); c.lineTo(X + s / 2, Y + s / 2 + k / 2 + 1); c.lineTo(X + s / 2 - k / 2, Y + s / 2); c.closePath(); c.fill(); c.stroke();
      if (s >= 22) { c.fillStyle = "#111"; c.font = `700 ${Math.max(8, s * 0.3)}px system-ui`; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText((((S.W && S.W.items[it.i]) || { name: it.i }).name || it.i)[0], X + s / 2, Y + s / 2 + 1); }
    }
    if (f) {
      for (const [p, x, y, d] of f.water || []) if (onScreen(p, x, y)) { c.fillStyle = `rgba(60,140,230,${Math.min(0.6, 0.2 + 0.07 * d)})`; c.fillRect(SX(p, x), SY(p, y), s + 0.5, s + 0.5); }
      for (const [p, x, y, d] of f.smoke || []) if (onScreen(p, x, y)) { c.fillStyle = `rgba(55,55,60,${Math.min(0.65, d / 11)})`; c.fillRect(SX(p, x), SY(p, y), s + 0.5, s + 0.5); }
      for (const [p, x, y, i] of f.fire || []) if (onScreen(p, x, y)) {
        const X = SX(p, x) + s / 2, Y = SY(p, y) + s / 2, fl = 0.8 + 0.25 * Math.sin(now / 90 + x * 3 + y * 5), h = s * (0.35 + 0.18 * i) * fl;
        c.fillStyle = "rgba(255,120,30,.28)"; c.beginPath(); c.arc(X, Y, s * (0.7 + 0.15 * i), 0, 6.3); c.fill();
        c.fillStyle = "#e8541f"; c.beginPath(); c.moveTo(X - s * 0.28, Y + s * 0.35); c.quadraticCurveTo(X - s * 0.3, Y - h * 0.4, X, Y - h); c.quadraticCurveTo(X + s * 0.3, Y - h * 0.4, X + s * 0.28, Y + s * 0.35); c.closePath(); c.fill();
        c.fillStyle = "#ffd54f"; c.beginPath(); c.moveTo(X - s * 0.14, Y + s * 0.35); c.quadraticCurveTo(X - s * 0.14, Y - h * 0.1, X, Y - h * 0.5); c.quadraticCurveTo(X + s * 0.14, Y - h * 0.1, X + s * 0.14, Y + s * 0.35); c.closePath(); c.fill();
      }
    }
    if (LY.noise && T.m < 24) for (const n of E.noises || []) {
      if (n.day !== t.day || n.hour !== t.hour || !G.rows[n.p]) continue;
      const r = ({ whisper: 2, quiet: 3.5, normal: 8, loud: 14, shout: 18 }[n.loud] || 6) * s * (((now / 900) % 1) * 0.85 + 0.15);
      c.strokeStyle = `rgba(255,200,80,${0.6 * (1 - ((now / 900) % 1))})`; c.lineWidth = 2; c.beginPath(); c.arc(SX(n.p, n.x) + s / 2, SY(n.p, n.y) + s / 2, r, 0, 6.3); c.stroke();
    }
  }
  const PERC = { key: "", data: null, pending: false };
  function drawPerception(c, P) {
    const who = T.follow || S.selected;
    if (!LY.perc || !who || !P[who]) return;
    const p = P[who], light = q("#tmLight").value, x = Math.round(p.x), y = Math.round(p.y), key = `${p.plane},${x},${y},${light}`;
    if (key !== PERC.key && !PERC.pending) {
      PERC.pending = true;
      fetch(`/api/perception?plane=${p.plane}&x=${x}&y=${y}&light=${light}&loud=normal`).then((r) => r.json()).then((d) => { PERC.key = key; PERC.data = d; PERC.plane = p.plane; PERC.pending = false; }).catch(() => (PERC.pending = false));
    }
    const d = PERC.data; if (!d || !d.ok) return;
    const s = G.view.s, pl = PERC.plane || p.plane;
    c.fillStyle = "rgba(80,170,255,.22)"; for (const [vx, vy] of d.visible) c.fillRect(SX(pl, vx), SY(pl, vy), s + 0.5, s + 0.5);
    c.fillStyle = "rgba(255,160,60,.75)"; for (const [hx, hy, v] of d.heard) { const r = Math.max(1.5, s * 0.12 * Math.min(1.6, v / 3)); c.beginPath(); c.arc(SX(pl, hx) + s / 2, SY(pl, hy) + s / 2, r, 0, 6.3); c.fill(); }
  }
  function drawCameras(c) {
    if (!LY.cam) return;
    const s = G.view.s;
    for (const p of G.planeIds) drawOverlay(c, p, roomOverlay(p, "cam", "cam", (rid) => { const r = G.map.rooms[rid]; return !r || r.open ? null : r.camera ? "rgba(255,95,162,.16)" : "rgba(0,0,0,.28)"; }));
    for (const f of G.map.furniture) if (f.k === "camera" && onScreen(f.plane, f.x, f.y)) c.drawImage(sprite("fcamera", (cc) => FURN.camera(cc)), SX(f.plane, f.x), SY(f.plane, f.y), s, s);
  }

  // ---------------------------------------------------------------- the camera
  function resize() {
    if (!cv) return;
    const r = cv.parentElement.getBoundingClientRect();
    cv.width = Math.max(100, Math.floor(r.width)); cv.height = Math.max(100, Math.floor(r.height));
  }
  function fitWorld(x0, y0, x1, y1, maxS) {
    const s = Math.max(2, Math.min(maxS || 40, Math.min(cv.width / (x1 - x0 + 4), cv.height / (y1 - y0 + 4))));
    G.view = { s, ox: cv.width / 2 - ((x0 + x1) / 2) * s, oy: cv.height / 2 - ((y0 + y1) / 2) * s };
  }
  function fit() { const [w, h] = worldSize(); fitWorld(0, 0, w, h); }
  function fitPlane(p) { const v = V(p); fitWorld(v.ox, v.oy, v.ox + v.x1 - v.x0, v.oy + v.y1 - v.y0); }
  function fitHouse() {
    const ts = Object.entries(G.map.rooms).filter(([, r]) => r.plane === "ground" && !r.open && ["ground"].includes(r.zone)).map(([, r]) => r.rect);
    if (!ts.length) return fitPlane("ground");
    const x0 = Math.min(...ts.map((r) => r[0])), y0 = Math.min(...ts.map((r) => r[1])), x1 = Math.max(...ts.map((r) => r[2])), y1 = Math.max(...ts.map((r) => r[3]));
    fitWorld(WX("ground", x0), WY("ground", y0), WX("ground", x1), WY("ground", y1));
  }
  function fitLevels() { const ps = G.planeIds.filter((p) => p !== "ground"); if (!ps.length) return; fitWorld(Math.min(...ps.map((p) => V(p).ox)), 0, Math.max(...ps.map((p) => V(p).ox + V(p).x1 - V(p).x0)), Math.max(...ps.map((p) => V(p).oy + V(p).y1 - V(p).y0))); }
  function centerOn(p, x, y) { G.view.ox = cv.width / 2 - (WX(p, x) + 0.5) * G.view.s; G.view.oy = cv.height / 2 - (WY(p, y) + 0.5) * G.view.s; }
  function focusRoom(rid) {
    const r = G.map.rooms[rid]; if (!r) return;
    T.follow = null; T.touched = true;
    if (r.open) { const [x, y] = r.label || roomCentre(rid); G.view.s = Math.max(G.view.s, 10); centerOn(r.plane, x, y); return; }
    const [x0, y0, x1, y1] = r.rect;
    fitWorld(WX(r.plane, x0), WY(r.plane, y0), WX(r.plane, x1), WY(r.plane, y1), 34);
  }
  function focusOn(id) { const P = positions(); if (P[id]) { T.follow = id; T.touched = true; G.view.s = Math.max(G.view.s, 14); centerOn(P[id].plane, P[id].x, P[id].y); } }

  // ---------------------------------------------------------------- pings: where something just happened
  function ping(e) {
    if (!G.map || !e) return;
    const P = positions(); let at = null;
    if (e.who && P[e.who]) at = [P[e.who].plane, P[e.who].x, P[e.who].y];
    else if (e.room && G.map.rooms[e.room]) { const c = roomCentre(e.room); at = [G.map.rooms[e.room].plane, c[0], c[1]]; }
    if (!at) return;
    G.pings.push({ p: at[0], x: at[1], y: at[2], col: CLS_COL[e.cls] || CLS_COL.notable, t0: performance.now(), text: (e.text || "").slice(0, 60), cls: e.cls });
    while (G.pings.length > 12) G.pings.shift();
  }
  function drawPings(c) {
    const now = performance.now(), s = G.view.s;
    G.pings = G.pings.filter((pg) => now - pg.t0 < 6000);
    for (const pg of G.pings) {
      const k = ((now - pg.t0) % 1500) / 1500, X = SX(pg.p, pg.x) + s / 2, Y = SY(pg.p, pg.y) + s / 2;
      c.strokeStyle = pg.col; c.globalAlpha = 1 - k; c.lineWidth = 3; c.beginPath(); c.arc(X, Y, 6 + k * Math.max(24, s * 3), 0, 6.3); c.stroke(); c.globalAlpha = 1;
    }
  }
  // arrows at the edge of the screen pointing to what is off it: the followed person, live conversations, recent pings
  function drawPointers(c, P, talks) {
    const pts = [];
    if (T.follow && P[T.follow]) pts.push({ p: P[T.follow].plane, x: P[T.follow].x, y: P[T.follow].y, col: info2(T.follow).color || "#fff", text: nameOf(T.follow) });
    for (const g of talks) pts.push({ p: g.p, x: g.x, y: g.y, col: "#ffd36b", text: "talking: " + g.names });
    for (const pg of G.pings) if (pg.cls === "critical" || pg.cls === "important") pts.push({ p: pg.p, x: pg.x, y: pg.y, col: pg.col, text: pg.text });
    const W = cv.width, H = cv.height, m = 18, cx = W / 2, cy = H / 2, s = G.view.s;
    c.font = "600 11px system-ui"; c.textBaseline = "middle";
    for (const t of pts) {
      const X = SX(t.p, t.x) + s / 2, Y = SY(t.p, t.y) + s / 2;
      if (X >= 0 && X <= W && Y >= 0 && Y <= H) continue;
      const dx = X - cx, dy = Y - cy, k = Math.min((W / 2 - m) / Math.abs(dx || 1e-6), (H / 2 - m) / Math.abs(dy || 1e-6)), ex = cx + dx * k, ey = cy + dy * k, a = Math.atan2(dy, dx);
      c.save(); c.translate(ex, ey); c.rotate(a); c.fillStyle = t.col; c.beginPath(); c.moveTo(10, 0); c.lineTo(-6, -7); c.lineTo(-6, 7); c.closePath(); c.fill(); c.restore();
      const tw = Math.min(160, c.measureText(t.text).width), lx = Math.max(4, Math.min(W - tw - 4, ex - (dx > 0 ? tw + 16 : -16))), ly = Math.max(10, Math.min(H - 10, ey + (dy > 0 ? -14 : 14)));
      c.fillStyle = "rgba(10,12,18,.8)"; c.fillRect(lx - 3, ly - 8, tw + 6, 16); c.fillStyle = t.col; c.textAlign = "left"; c.fillText(t.text.slice(0, 28), lx, ly);
    }
  }
  // the conversations going on right now: whoever has a speech bubble up, grouped by room
  function activeTalks(P) {
    const by = {};
    for (const b of S.bubbles || []) {
      if (b.until < S.clock || !P[b.id]) continue;
      const k = b.room || "?"; (by[k] = by[k] || []).push(b.id);
    }
    return Object.entries(by).map(([room, ids]) => { const p = P[ids[0]]; return { room, ids, p: p.plane, x: p.x, y: p.y, names: ids.map(nameOf).join(", ") }; });
  }

  // ---------------------------------------------------------------- drawing
  function drawBubbles(c, P) {
    const now = S.clock, s = G.view.s;
    for (const b of S.bubbles || []) {
      if (b.until < now) continue;
      const p = P[b.id]; if (!p) continue;
      const px = SX(p.plane, p.x) + s / 2, py = SY(p.plane, p.y) + s / 2 - Math.max(7, s * 0.46) - 6, txt = b.act ? "* " + b.text : b.text;
      c.font = "12px system-ui"; const words = txt.split(" "), lines = []; let cl = "";
      for (const w of words) { if (c.measureText(cl + " " + w).width > 190 && cl) { lines.push(cl); cl = w; } else cl = cl ? cl + " " + w : w; }
      lines.push(cl); const lh = 14, w = Math.min(200, Math.max(...lines.map((l) => c.measureText(l).width)) + 12), h = lines.length * lh + 8, bx = px - w / 2, by = py - h;
      c.fillStyle = "rgba(255,255,255,.95)"; c.strokeStyle = "#333"; c.lineWidth = 1; c.beginPath(); c.roundRect ? c.roundRect(bx, by, w, h, 6) : c.rect(bx, by, w, h); c.fill(); c.stroke();
      c.beginPath(); c.moveTo(px - 5, py - 1); c.lineTo(px, py + 5); c.lineTo(px + 5, py - 1); c.fillStyle = "rgba(255,255,255,.95)"; c.fill();
      c.fillStyle = "#14161f"; c.textAlign = "left"; c.textBaseline = "top"; lines.forEach((l, i) => c.fillText(l, bx + 6, by + 4 + i * lh));
    }
  }
  function drawTokens(c, P) {
    const s = G.view.s, t = T.tick, agents = t && t.state ? t.state.agents : {};
    const who = T.follow || S.selected;
    if (T.follow && P[T.follow] && !G.drag && !ED.on) {
      const p = P[T.follow], tx = cv.width / 2 - (WX(p.plane, p.x) + 0.5) * s, ty = cv.height / 2 - (WY(p.plane, p.y) + 0.5) * s;
      G.view.ox += (tx - G.view.ox) * 0.12; G.view.oy += (ty - G.view.oy) * 0.12;
    }
    const flash = new Set((S.flashes || []).filter((f) => f.until > S.clock).map((f) => f.id));
    for (const [id, p] of Object.entries(P).sort((a, b) => a[1].y - b[1].y)) {
      const col = info2(id).color || "#999", r = Math.max(5, s * 0.46), px = SX(p.plane, p.x) + s / 2, py = SY(p.plane, p.y) + s / 2;
      if (px < -r || py < -r || px > cv.width + r || py > cv.height + r) continue;
      c.save(); c.globalAlpha = p.dead ? 0.55 : p.hiding ? 0.45 : 1;
      c.beginPath(); c.arc(px, py, r, 0, 6.3); c.closePath(); c.fillStyle = col; c.fill(); c.save(); c.clip();
      const im = window.img ? img(id) : null; if (im && im.complete && im.naturalWidth) { if (p.dead || p.out) c.filter = "grayscale(1)"; c.drawImage(im, px - r, py - r, r * 2, r * 2); }
      c.restore(); c.beginPath(); c.arc(px, py, r, 0, 6.3); c.lineWidth = who === id ? 4 : flash.has(id) ? 4 : 2.5; c.strokeStyle = who === id ? "#ffffff" : flash.has(id) ? "#ff4d6d" : p.dead ? "#777" : col; c.stroke();
      if (p.dead || p.out) { c.fillStyle = "rgba(0,0,0,.65)"; c.font = `700 ${Math.max(10, r * 0.9)}px system-ui`; c.textAlign = "center"; c.textBaseline = "middle"; c.fillText(p.dead ? "✕" : "z", px, py); }
      const a = agents[id]; if (a && a.conds && a.conds.length && !p.dead) { c.fillStyle = "#ff4d6d"; c.beginPath(); c.arc(px + r * 0.8, py - r * 0.8, Math.max(3, r * 0.28), 0, 6.3); c.fill(); }
      c.restore();
      if (s >= 10 || who === id) { c.font = `600 ${Math.max(9, Math.min(12, s * 0.45))}px system-ui`; c.textAlign = "center"; c.textBaseline = "top"; c.lineWidth = 3; c.strokeStyle = "rgba(0,0,0,.7)"; c.fillStyle = "#fff"; c.strokeText(nameOf(id), px, py + r + 1); c.fillText(nameOf(id), px, py + r + 1); }
    }
  }
  function drawLevelFrames(c) {
    const s = G.view.s;
    for (const p of G.planeIds) {
      const v = V(p), X = SX(p, v.x0), Y = SY(p, v.y0), w = (v.x1 - v.x0) * s, h = (v.y1 - v.y0) * s;
      if (X > cv.width || Y > cv.height || X + w < 0 || Y + h < 0) continue;
      c.fillStyle = "#171a24"; c.fillRect(X - 3, Y - 3, w + 6, h + 6);
      c.font = "700 12px system-ui"; c.textAlign = "left"; c.textBaseline = "bottom"; c.fillStyle = "#9aa3c7"; c.fillText(PLANE_LABEL[p] || p, X, Y - 5);
    }
  }
  function drawTiles(c) {
    const s = G.view.s;
    for (const p of G.planeIds) {
      const v = V(p);
      const X = SX(p, v.x0), Y = SY(p, v.y0), w = (v.x1 - v.x0) * s, h = (v.y1 - v.y0) * s;
      if (X > cv.width || Y > cv.height || X + w < 0 || Y + h < 0) continue;
      if (s <= 14) { c.imageSmoothingEnabled = s < CT; c.drawImage(levelCache(p), X, Y, w, h); continue; }
      c.imageSmoothingEnabled = s < REN;
      const x0 = Math.max(v.x0, v.x0 + Math.floor(-X / s)), y0 = Math.max(v.y0, v.y0 + Math.floor(-Y / s)), x1 = Math.min(v.x1, v.x0 + Math.ceil((cv.width - X) / s)), y1 = Math.min(v.y1, v.y0 + Math.ceil((cv.height - Y) / s));
      for (let y = y0; y < y1; y++) for (let x = x0; x < x1; x++) { const im = tileImage(p, x, y); if (im) c.drawImage(im, SX(p, x), SY(p, y), s + 0.6, s + 0.6); }
      if (LY.grid && s >= 10) { c.strokeStyle = "rgba(0,0,0,.18)"; c.lineWidth = 1; c.beginPath(); for (let x = x0; x <= x1; x++) { c.moveTo(SX(p, x) + 0.5, SY(p, y0)); c.lineTo(SX(p, x) + 0.5, SY(p, y1)); } for (let y = y0; y <= y1; y++) { c.moveTo(SX(p, x0), SY(p, y) + 0.5); c.lineTo(SX(p, x1), SY(p, y) + 0.5); } c.stroke(); }
    }
  }
  function drawLabels(c) {
    const s = G.view.s;
    c.textAlign = "center"; c.textBaseline = "middle";
    for (const r of G.rooms) {
      const [cx0, cy0] = roomCentre(r.id), cx = SX(r.plane, cx0) + s / 2, cy = SY(r.plane, cy0) + s / 2;
      if (cx < -80 || cy < -20 || cx > cv.width + 80 || cy > cv.height + 20) continue;
      const big = r.open, fs = big ? Math.max(11, Math.min(18, s * 1.2)) : Math.max(8, Math.min(15, s * 0.55));
      const maxw = big ? 400 : (r.rect[2] - r.rect[0]) * s + 6;
      c.font = `700 ${fs}px system-ui`;
      const lines = []; let cur = "";
      for (const wd of r.name.split(" ")) { const tx = cur ? cur + " " + wd : wd; if (cur && c.measureText(tx).width > maxw) { lines.push(cur); cur = wd; } else cur = tx; }
      lines.push(cur);
      if (!big && (lines.length > 3 || Math.max(...lines.map((l) => c.measureText(l).width)) > maxw * 1.3)) continue;
      c.lineWidth = 3; c.strokeStyle = "rgba(0,0,0,.6)"; c.fillStyle = big ? "rgba(255,255,255,.75)" : "rgba(255,255,255,.92)";
      const yy = cy - ((lines.length - 1) * fs * 1.1) / 2;
      lines.forEach((ln, i) => { c.strokeText(ln, cx, yy + i * fs * 1.1); c.fillText(ln, cx, yy + i * fs * 1.1); });
    }
  }
  function draw() {
    if (!G.map || !cv || !T.visible) return;
    const gm = !!(q("#gm") && q("#gm").checked);
    if (gm !== G.gm) { G.gm = gm; }
    const c = ctx, s = G.view.s;
    c.fillStyle = "#101118"; c.fillRect(0, 0, cv.width, cv.height);
    drawLevelFrames(c);
    drawTiles(c);
    c.imageSmoothingEnabled = s < REN;
    if (LY.tint) for (const p of G.planeIds) drawOverlay(c, p, roomOverlay(p, "tint", "tint", (rid) => { const r = G.map.rooms[rid]; return r ? (ZONE_TINT[r.zone] || "#888888") + "44" : null; }));
    if (LY.furn) for (const f of G.map.furniture) { if (f.k === "camera" || !onScreen(f.plane, f.x, f.y)) continue; c.drawImage(sprite("f" + f.k, (cc) => FURN[f.k] && FURN[f.k](cc)), SX(f.plane, f.x), SY(f.plane, f.y), s * (f.w || 1), s * (f.h || 1)); }
    if (G.gm) for (const l of G.map.links.filter((k) => k.kind === "secret")) for (const e of Object.values(l.ends)) if (onScreen(e[0], e[1], e[2])) { c.fillStyle = "#ff4dd2"; c.font = `bold ${Math.max(9, s * 0.45)}px system-ui`; c.textAlign = "center"; c.textBaseline = "bottom"; c.fillText(l.id, SX(e[0], e[1]) + s / 2, SY(e[0], e[2])); }
    if (LY.labels) drawLabels(c);
    const P = positions(), talks = activeTalks(P);
    drawCameras(c); drawEnv(c, T.tick); drawPerception(c, P); drawPings(c); drawTokens(c, P); drawBubbles(c, P); drawPointers(c, P, talks);
    if (G.hover) { const [hp, hx, hy] = G.hover; c.strokeStyle = "#3ee0d0"; c.lineWidth = 2; c.strokeRect(SX(hp, hx), SY(hp, hy), s, s); }
    G.talks = talks;
  }

  // ---------------------------------------------------------------- interaction
  function evXY(ev) { const r = cv.getBoundingClientRect(); return [ev.clientX - r.left, ev.clientY - r.top]; }
  function tileAt(ev) { const [x, y] = evXY(ev); return pickAt(x, y); }
  function tokenAt(ev) {
    const [mx, my] = evXY(ev), P = positions(), s = G.view.s; let best = null, bd = Math.max(10, s * 0.8);
    for (const [id, p] of Object.entries(P)) { const d = Math.hypot(SX(p.plane, p.x) + s / 2 - mx, SY(p.plane, p.y) + s / 2 - my); if (d < bd) { bd = d; best = id; } }
    return best;
  }
  const nameRoom = (rid) => (G.map.rooms[rid] || { name: rid }).name;
  function describe(p, x, y) {
    const t = ch(p, x, y), rid = roomOf(p, x, y);
    let html = `<b>${(G.map.legend && G.map.legend[t]) || t}</b> (${PLANE_SHORT[p] || p} ${x}, ${y})` + (rid ? `<br>${nameRoom(rid)}` : "");
    const d = G.map.doors.find((k) => k.plane === p && k.tiles.some((tt) => tt[0] === x && tt[1] === y));
    if (d) html += `<br>${nameRoom(d.a)} ↔ ${nameRoom(d.b)} (${d.kind}${d.locked ? ", locked" : ""}${d.keys.length ? ", key: " + d.keys.join(", ") : ""})`;
    const l = G.map.links.find((k) => Object.values(k.ends).some((e) => e[0] === p && e[1] === x && e[2] === y));
    if (l && (l.kind === "stairs" || G.gm)) html += `<br>${l.kind === "secret" ? "<b>Hidden</b>: " : ""}${nameRoom(l.a)} ↔ ${nameRoom(l.b)} (${l.id}${l.locked ? ", locked" : ""})` + (G.gm && (l.note || (l.discover && l.discover.text)) ? `<br><i>${l.note || l.discover.text}</i>` : "") + "<br>click to jump to the other end";
    const fs = G.map.furniture.filter((f) => f.plane === p && f.k !== "camera" && x >= f.x && x < f.x + (f.w || 1) && y >= f.y && y < f.y + (f.h || 1)).map((f) => f.k);
    if (fs.length) html += `<br>${fs.join(", ")}`;
    const it = ((T.tick && T.tick.env && T.tick.env.items) || []).filter((i) => i.p === p && i.x === x && i.y === y).map((i) => ((S.W && S.W.items[i.i]) || { name: i.i }).name + (i.q > 1 ? " x" + i.q : ""));
    if (it.length) html += `<br>Lying here: ${it.join(", ")}`;
    return html;
  }
  function bindCanvas() {
    cv.addEventListener("contextmenu", (ev) => { if (ED.on) ev.preventDefault(); });
    cv.addEventListener("mousedown", (ev) => {
      if (ED.on && ev.button === 0) { ED.painting = true; ED.batch = []; edAt(ev); return; }
      if (ED.on && ev.button !== 2) return;
      G.drag = { x: ev.clientX, y: ev.clientY, ox: G.view.ox, oy: G.view.oy }; T.touched = true;
    });
    cv.addEventListener("mousemove", (ev) => {
      const at = tileAt(ev);
      if (ED.painting) { edAt(ev); G.hover = at ? [at.p, at.x, at.y] : null; return; }
      if (G.drag) { G.view.ox = G.drag.ox + ev.clientX - G.drag.x; G.view.oy = G.drag.oy + ev.clientY - G.drag.y; if (Math.abs(ev.clientX - G.drag.x) + Math.abs(ev.clientY - G.drag.y) > 4) T.follow = null; return; }
      G.hover = at ? [at.p, at.x, at.y] : null;
      const tk = tokenAt(ev), st = T.tick && T.tick.state;
      if (tk && st && st.agents[tk]) { const a = st.agents[tk], cc = info2(tk); tip.innerHTML = `<b>${esc(cc.name)}</b><br>${esc(cc.role || "")}<br>HP ${a.hp} · Sanity ${a.sanity}${a.mind ? " · stress " + a.mind.stress : ""}<br><i>${esc(a.activity || "")}</i>`; }
      else if (at && ch(at.p, at.x, at.y) !== " ") tip.innerHTML = describe(at.p, at.x, at.y); else { tip.style.display = "none"; return; }
      const b = cv.parentElement.getBoundingClientRect(); tip.style.display = "block"; tip.style.left = Math.min(b.width - 300, ev.clientX - b.left + 14) + "px"; tip.style.top = Math.max(4, ev.clientY - b.top - 40) + "px";
    });
    cv.addEventListener("mouseleave", () => { G.hover = null; tip.style.display = "none"; });
    addEventListener("mouseup", (ev) => {
      if (ED.painting) { ED.painting = false; if (ED.batch && ED.batch.length) ED.undo.push(ED.batch); ED.batch = null; return; }
      if (G.drag && Math.abs(ev.clientX - G.drag.x) + Math.abs(ev.clientY - G.drag.y) < 4 && !ED.on) clickAt(ev);
      G.drag = null;
    });
    cv.addEventListener("wheel", (ev) => {
      ev.preventDefault(); T.touched = true; const [mx, my] = evXY(ev), v = G.view;
      const k = ev.deltaY < 0 ? 1.15 : 1 / 1.15, ns = Math.max(2, Math.min(64, v.s * k));
      v.ox = mx - (mx - v.ox) * (ns / v.s); v.oy = my - (my - v.oy) * (ns / v.s); v.s = ns;
    }, { passive: false });
  }
  // touch: one finger pans (or paints in the editor), a tap selects, two fingers pinch to zoom
  function bindTouch() {
    let mode = null, last = null, start = null, pinch = null;
    const pt = (t) => ({ clientX: t.clientX, clientY: t.clientY });
    const dist = (a, b) => Math.hypot(a.clientX - b.clientX, a.clientY - b.clientY);
    cv.addEventListener("touchstart", (ev) => {
      ev.preventDefault(); T.touched = true;
      if (ev.touches.length === 2) { mode = "pinch"; pinch = { d: dist(ev.touches[0], ev.touches[1]), s: G.view.s, ox: G.view.ox, oy: G.view.oy }; return; }
      const p = pt(ev.touches[0]); start = { ...p, t: Date.now() }; last = p;
      if (ED.on) { mode = "paint"; ED.painting = true; ED.batch = []; edAt(p); } else mode = "pan";
    }, { passive: false });
    cv.addEventListener("touchmove", (ev) => {
      ev.preventDefault();
      if (mode === "pinch" && ev.touches.length === 2) {
        const r = cv.getBoundingClientRect(), a = ev.touches[0], b = ev.touches[1], cx = (a.clientX + b.clientX) / 2 - r.left, cy = (a.clientY + b.clientY) / 2 - r.top;
        const ns = Math.max(2, Math.min(64, pinch.s * dist(a, b) / pinch.d)), v = G.view;
        v.ox = cx - (cx - pinch.ox) * (ns / pinch.s); v.oy = cy - (cy - pinch.oy) * (ns / pinch.s); v.s = ns; return;
      }
      if (!ev.touches.length) return;
      const p = pt(ev.touches[0]);
      if (mode === "paint") edAt(p);
      else if (mode === "pan" && last) { G.view.ox += p.clientX - last.clientX; G.view.oy += p.clientY - last.clientY; T.follow = null; }
      last = p;
    }, { passive: false });
    cv.addEventListener("touchend", (ev) => {
      ev.preventDefault();
      if (mode === "paint") { ED.painting = false; if (ED.batch && ED.batch.length) ED.undo.push(ED.batch); ED.batch = null; }
      else if (mode === "pan" && start && last && Date.now() - start.t < 350 && Math.hypot(last.clientX - start.clientX, last.clientY - start.clientY) < 10) clickAt(start);
      if (!ev.touches.length) { mode = null; start = null; }
    }, { passive: false });
  }
  function clickAt(ev) {
    const tk = tokenAt(ev);
    if (tk) { T.follow = T.follow === tk ? null : tk; if (S.W && S.W.characters[tk]) { S.selected = tk; setTab("cast"); renderCast(); } return; }
    const at = tileAt(ev); if (!at) return;
    const l = G.map.links.find((k) => (k.kind === "stairs" || G.gm) && Object.values(k.ends).some((e) => e[0] === at.p && e[1] === at.x && e[2] === at.y));
    if (l) { const other = Object.values(l.ends).find((e) => !(e[0] === at.p && e[1] === at.x && e[2] === at.y)) || Object.values(l.ends)[0]; T.follow = null; centerOn(other[0], other[1], other[2]); G.pings.push({ p: other[0], x: other[1], y: other[2], col: "#3ee0d0", t0: performance.now(), text: "" }); return; }
    const rid = roomOf(at.p, at.x, at.y);
    if (rid && S.W && S.W.rooms[rid]) { S.selRoom = rid; setTab("room"); renderRoom(); }
  }

  // ---------------------------------------------------------------- map editor (paints tiles and furniture on any level; the server rebuilds the map from them and checks it)
  const ED = { on: false, painting: false, batch: null, undo: [], protect: new Set() };
  function edBuildProtect() {
    ED.protect = new Set();
    for (const d of G.map.doors) if (d.via !== "open") for (const t of d.tiles) ED.protect.add(`${d.plane},${t[0]},${t[1]}`);
    for (const l of G.map.links) for (const e of Object.values(l.ends)) ED.protect.add(`${e[0]},${e[1]},${e[2]}`);
  }
  function edMsg(t, cls) { const m = q("#edMsg"); m.textContent = t; m.className = cls || ""; }
  function edSet(plane, x, y, c2) { const rows = G.rows[plane]; rows[y] = rows[y].slice(0, x) + c2 + rows[y].slice(x + 1); for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) patchCache(plane, x + dx, y + dy); }
  function edPaint(plane, x, y, c2) {
    if (x < 0 || y < 0 || x >= G.map.w || y >= G.map.h || ED.protect.has(`${plane},${x},${y}`)) return;
    const old = G.rows[plane][y][x];
    if (old === c2) return;
    if (G.map.furniture.some((f) => f.plane === plane && f.k !== "camera" && x >= f.x && x < f.x + (f.w || 1) && y >= f.y && y < f.y + (f.h || 1)) && "# ~TH".includes(c2)) return;
    edSet(plane, x, y, c2);
    ED.batch.push({ t: "tile", plane, x, y, old });
  }
  function edAt(ev) {
    const at = tileAt(ev); if (!at) return;
    const { p, x, y } = at, [kind, arg] = q("#edTool").value.split(":");
    if (kind === "t") edPaint(p, x, y, arg);
    else if (arg === "add") {
      const rid = roomOf(p, x, y), c2 = ch(p, x, y), k = q("#edFurn").value;
      if (!rid || "# ~+L=UDhlvSTH".includes(c2) || ED.protect.has(`${p},${x},${y}`) || G.map.furniture.some((f) => f.plane === p && f.x === x && f.y === y && f.k === k)) return;
      G.map.furniture.push({ k, plane: p, x, y, w: 1, h: 1, room: rid }); ED.batch.push({ t: "add", k, plane: p, x, y });
    } else {
      const gone = G.map.furniture.filter((f) => f.plane === p && f.k !== "camera" && x >= f.x && x < f.x + (f.w || 1) && y >= f.y && y < f.y + (f.h || 1));
      if (!gone.length) return;
      G.map.furniture = G.map.furniture.filter((f) => !gone.includes(f)); for (const f of gone) ED.batch.push({ t: "del", f });
    }
  }
  function edUndo() {
    const b = ED.undo.pop(); if (!b) return;
    for (const op of b.reverse()) {
      if (op.t === "tile") edSet(op.plane, op.x, op.y, op.old);
      else if (op.t === "add") G.map.furniture = G.map.furniture.filter((f) => !(f.k === op.k && f.plane === op.plane && f.x === op.x && f.y === op.y));
      else G.map.furniture.push(op.f);
    }
  }
  const edPost = async (path) => (await fetch(path, { method: "POST", body: JSON.stringify({ map: G.map }) })).json();

  // ---------------------------------------------------------------- pause settings and dialogs for important events
  const CLASSES = [["critical", "Critical", "Deaths, bodies, cases, trials, verdicts, announcements about the deadline"], ["important", "Important", "Plot strikes, breakdowns, knockouts, punishments, fires and the like"], ["notable", "Notable", "Quarrels, alliances, betrayals, treatment, experiments"], ["background", "Background", "Walking, meals, routine"]];
  const RESPONSES = [["dialog", "Pause with a dialog"], ["toast", "Small notice, keep going"], ["log", "Feed only"]];
  const DEFAULTS = { classes: { critical: "dialog", important: "dialog", notable: "toast", background: "log" }, kinds: {}, pauseTalk: "matters", segMsg: true };
  const KIND_LABEL = { death: "Someone has died", body: "A body has been found", discover: "A discovery", attack: "An attack", verdict: "A verdict", broadcast: "TereVi is speaking", plot: "A plot is moving", madness: "A mind has broken", faint: "Someone has collapsed",
    punish: "NeoVi is punishing someone", frame: "Someone is being framed", carry: "Someone is being dragged away", rob: "Someone is being robbed", assault: "A fight", sabotage: "Sabotage", outburst: "An outburst", island: "Something has happened on the island",
    system_notable: "Something important has happened", inspection: "NeoVi is inspecting a room", condition: "Someone is hurt or ill", friction: "A quarrel", hook: "Something is wrong", alliance: "An alliance", betrayal: "A betrayal", treat: "Someone is being treated",
    fire: "A fire", flood: "A flood", wreck: "Something has been wrecked", interrogation: "An interrogation", snap: "Someone has snapped", embarrassed: "Someone is mortified" };
  let SET = null;
  const segMsgOn = () => { if (!SET) loadSettings(); return SET.segMsg !== false; };
  function loadSettings() { let s = null; try { s = JSON.parse(localStorage.getItem("mcLiveSettings") || "null"); } catch (e) { s = null; } SET = { classes: { ...DEFAULTS.classes, ...((s || {}).classes || {}) }, kinds: { ...((s || {}).kinds || {}) }, pauseTalk: (s || {}).pauseTalk || DEFAULTS.pauseTalk, segMsg: (s || {}).segMsg !== false }; }
  function saveSettings() { try { localStorage.setItem("mcLiveSettings", JSON.stringify(SET)); } catch (e) { /* private mode */ } }
  const response = (e) => SET.kinds[e.type] || SET.classes[e.cls] || "log";
  function toast(text, cls) {
    const box = q("#tmtoasts"), el = document.createElement("div"); el.className = "tmtoast"; el.style.borderLeftColor = cls === "critical" ? "#ff4d6d" : cls === "important" ? "#ffb347" : "#6c7bd6"; el.textContent = text.slice(0, 160);
    box.appendChild(el); setTimeout(() => el.remove(), 4500); while (box.children.length > 4) box.firstChild.remove();
  }
  function modal(html) { const m = q("#tmmodal"); q("#tmcard").innerHTML = html; m.style.display = "flex"; return m; }
  function closeModal() { q("#tmmodal").style.display = "none"; }
  // Resolves when the user has dealt with the dialog. Called by the playback for each turn; nothing happens (and nothing waits) if no event of that turn is set to pause.
  function dialogFor(t, win) {
    if (!SET) loadSettings();
    const gm = !!(q("#gm") && q("#gm").checked);
    const items = [];
    for (const e of t.chron || []) {
      if (e.type === "move" || e.type === "arrive" || e.type === "talk" || (e.vis === "gm" && !gm)) continue;
      if (win) { const timed = e.m !== undefined && e.m !== null; if (win.untimed ? timed : (!timed || e.m < win.from || e.m >= win.to)) continue; }
      if (win && !win.untimed && e.cls !== "background") ping(e);
      const r = response(e);
      if (r === "dialog" && e.vis !== "gm") items.push(e); else if (r === "toast" && e.vis !== "gm") toast(e.text, e.cls);
    }
    if (!items.length) return Promise.resolve();
    const truth = gm ? (t.chron || []).filter((e) => e.vis === "gm" && items.some((i) => i.type === e.type && i.room === e.room)) : [];
    const first = items[0];
    return new Promise((res) => {
      const title = items.length > 1 ? "Several things are happening" : KIND_LABEL[first.type] || "Something important is going on";
      modal(`<div class="kind">Day ${t.day} ${t.time}</div><h2>${esc(title)}</h2><div class="sub">Something important is going on. The game is paused.</div>` +
        items.slice(0, 6).map((e) => `<div class="item"><b>${esc(KIND_LABEL[e.type] || e.type)}</b><br>${esc(e.text)}</div>`).join("") + truth.map((e) => `<div class="item gm">${esc(e.text)}</div>`).join("") +
        `<div class="btns"><button class="pri" id="tmCont">Continue</button><button id="tmShow">Show me</button><button id="tmSlow">Slow down</button><button id="tmMute">Don't pause for "${esc(first.type)}" again</button></div>`);
      T.dialogOpen = true; const wasPaused = S.paused; S.paused = true;
      const done = () => { closeModal(); T.dialogOpen = false; S.paused = wasPaused; res(); };
      q("#tmCont").onclick = done;
      q("#tmShow").onclick = () => { const e = items.find((i) => i.room && G.map.rooms[i.room]) || items[0]; if (e.who && positions()[e.who]) focusOn(e.who); else if (G.map.rooms[e.room]) focusRoom(e.room); q("#tmmodal").style.display = "none"; setTimeout(() => { if (T.dialogOpen) q("#tmmodal").style.display = "flex"; }, 3500); };
      q("#tmSlow").onclick = () => { S.speed = 1; const sp = q("#speed"); if (sp) sp.value = "1"; done(); };
      q("#tmMute").onclick = () => { for (const e of items) SET.kinds[e.type] = "toast"; saveSettings(); done(); };
    });
  }
  // Called when a conversation starts during a free-time block. Resolves when the viewer has dealt with it (immediately unless the setting says to pause).
  function chatDialog(t, g) {
    if (!SET) loadSettings();
    const mode = SET.pauseTalk || "matters", matters = (g.matters || []).length > 0;
    const names = (g.members || []).map((id) => (S.W.characters[id] || {}).name || id);
    if (mode === "off" || (mode === "matters" && !matters)) { if (mode !== "off") toast(`${names.join(" and ")} start talking in the ${(S.W.rooms[g.room] || {}).name || g.room}.`, "notable"); return Promise.resolve(); }
    const gm = !!(q("#gm") && q("#gm").checked);
    return new Promise((res) => {
      const why = g.why ? `<div class="sub">${esc(g.why)}</div>` : "";
      const tag = (g.matters || []).map((m2) => ({ plot: "a murder plot is in play between them", feud: "there is bad blood between them", secret: "one of them knows a secret about the other", hook: "a loose end lies between them", romance: "there is a spark between them", purpose: "one of them has a purpose" }[m2] || m2)).join("; ");
      modal(`<div class="kind">Day ${t.day} ${t.time}</div><h2>${esc(names.join(" and "))} start talking</h2><div class="sub">In the ${esc((S.W.rooms[g.room] || {}).name || g.room)}. The game is paused.</div>${why}` +
        (gm && tag ? `<div class="item gm">${esc(tag)}</div>` : "") +
        `<div class="btns"><button class="pri" id="tmCont">Listen in</button><button id="tmShow">Show me</button><button id="tmSlow">Slow down</button><button id="tmMute">Stop pausing for conversations</button></div>`);
      T.dialogOpen = true; const wasPaused = S.paused; S.paused = true;
      const done = () => { closeModal(); T.dialogOpen = false; S.paused = wasPaused; res(); };
      q("#tmCont").onclick = done;
      q("#tmShow").onclick = () => { if ((g.members || [])[0] && positions()[g.members[0]]) focusOn(g.members[0]); else focusRoom(g.room); q("#tmmodal").style.display = "none"; setTimeout(() => { if (T.dialogOpen) q("#tmmodal").style.display = "flex"; }, 3500); };
      q("#tmSlow").onclick = () => { S.speed = 1; const sp = q("#speed"); if (sp) sp.value = "1"; done(); };
      q("#tmMute").onclick = () => { SET.pauseTalk = "off"; saveSettings(); done(); };
    });
  }
  function openSettings() {
    if (!SET) loadSettings();
    const kinds = Object.keys(KIND_LABEL).sort();
    const sel = (id, val, withDefault) => `<select id="${id}">${withDefault ? '<option value="">class default</option>' : ""}${RESPONSES.map(([v, l]) => `<option value="${v}" ${val === v ? "selected" : ""}>${l}</option>`).join("")}</select>`;
    modal(`<h2>Pause settings</h2><div class="sub">What happens when an event of each class occurs on the map. A kind can override its class.</div>
      <table><tr><td><b>Class</b></td><td></td><td><b>When it happens</b></td></tr>${CLASSES.map(([k, n, d]) => `<tr><td>${n}</td><td class="sub">${d}</td><td>${sel("tmcl_" + k, SET.classes[k])}</td></tr>`).join("")}</table>
      <table style="margin-top:6px"><tr><td>Conversations in free time</td><td><select id="tmTalk"><option value="off" ${SET.pauseTalk === "off" ? "selected" : ""}>Never pause</option><option value="matters" ${(SET.pauseTalk || "matters") === "matters" ? "selected" : ""}>Pause when it matters (a plot, a feud, a secret, a loose end, a spark)</option><option value="all" ${SET.pauseTalk === "all" ? "selected" : ""}>Pause at every conversation</option></select></td></tr></table>
      <table style="margin-top:6px"><tr><td>Title card when a new part of the day starts</td><td><label><input type="checkbox" id="tmSeg" ${SET.segMsg !== false ? "checked" : ""}> show it</label></td></tr></table>
      <details style="margin-top:8px"><summary>Per kind of event (${kinds.length})</summary><table>${kinds.map((k) => `<tr><td>${esc(k)}</td><td>${sel("tmkd_" + k, SET.kinds[k] || "", true)}</td></tr>`).join("")}</table></details>
      <div class="btns"><button class="pri" id="tmSave">Save</button><button id="tmReset">Reset to defaults</button><button id="tmCancel">Cancel</button></div>`);
    q("#tmCancel").onclick = closeModal;
    q("#tmReset").onclick = () => { SET = JSON.parse(JSON.stringify(DEFAULTS)); saveSettings(); closeModal(); };
    q("#tmSave").onclick = () => { SET.pauseTalk = q("#tmTalk").value; SET.segMsg = q("#tmSeg").checked; for (const [k] of CLASSES) SET.classes[k] = q("#tmcl_" + k).value; SET.kinds = {}; for (const k of kinds) { const v = q("#tmkd_" + k).value; if (v) SET.kinds[k] = v; } saveSettings(); closeModal(); };
  }

  // ---------------------------------------------------------------- the toolbar and panels the map brings with it
  const FURN_KINDS = ["bed", "wardrobe", "desk", "table", "chair", "shelf", "sofa", "stove", "sink", "barrel", "crate", "chest", "plant", "piano", "easel", "telescope", "railing", "poolTable", "washer", "tub", "cabinet", "radio", "boiler", "fuseBox", "workbench", "freezer", "terminal", "locker", "lamp", "generator", "plantBed", "boat", "podium", "monitor", "tree", "bench", "deckChair", "driftwood", "armchair", "fireplace", "chessTable", "dartboard", "mirror", "fridge", "hammock", "firepit", "jukebox"];
  const TILES = [["w", "wood floor"], ["k", "tiles"], ["c", "carpet"], ["r", "stone"], ["m", "metal"], ["#", "wall"], ["+", "door"], ["L", "locked door"], ["=", "window"], ["U", "stairs up"], ["D", "stairs down"], ["l", "ladder"],
    ["g", "lawn"], [",", "wild grass"], ["T", "tree"], ["b", "bush"], ["H", "hedge"], ["f", "flower bed"], ["s", "sand"], ["n", "dunes"], ["q", "rock"], ["C", "cliff"], ["K", "steps"], ["a", "shallow water"], ["~", "deep water"],
    [":", "deck"], ["B", "boardwalk"], ["j", "jetty"], ["p", "path"], ["S", "roof"], ["x", "railing"], ["v", "open to the floor below"]];
  const PAINTABLE = new Set(["w", "k", "c", "r", "m", "#", "=", "g", ",", "T", "b", "H", "f", "s", "n", "q", "C", "K", "a", "~", ":", "B", "j", "p", "S", "x", "v"]);
  function tileFor(k) {
    const v = 0;
    if (k === "#") return sprite("#00", (c) => wallPaint(c, v, 0));
    if (k === "=") return sprite("=0", (c) => windowPaint(c, v, 0));
    if (k === "+" || k === "L") return sprite("lg" + k, (c) => doorPaint(c, v, false, k === "L"));
    if (k === "U" || k === "D") return sprite("lg" + k, (c) => stairPaint(c, v, k === "D"));
    return PAINT[k] ? sprite("lg" + k, (c) => PAINT[k](c, v)) : null;
  }

  // find a person, a room or an item lying somewhere
  function searchHits(text) {
    const qq = text.trim().toLowerCase(); if (!qq) return [];
    const out = [], st = (T.tick && T.tick.state) || {}, P = positions();
    for (const id of Object.keys((S.W && S.W.characters) || {})) { const i = info2(id); if ((i.name || id).toLowerCase().includes(qq) || (i.short || "").toLowerCase().includes(qq)) out.push({ kind: "person", id, label: i.name || id, sub: P[id] ? roomLabel(roomOf(P[id].plane, Math.round(P[id].x), Math.round(P[id].y))) : "not on the map" }); }
    for (const r of G.rooms) { const nm = roomLabel(r.id); if (nm.toLowerCase().includes(qq) || r.id.toLowerCase().includes(qq)) out.push({ kind: "room", id: r.id, label: nm, sub: PLANE_LABEL[r.plane] || r.plane }); }
    const iname = (k) => (window.itemName ? window.itemName(k) : k), seen = new Set();
    for (const [rid, pool] of Object.entries(st.room_items || {})) for (const k of Object.keys(pool || {})) { const nm = iname(k); if (G.map.rooms[rid] && (nm.toLowerCase().includes(qq) || k.includes(qq)) && !seen.has(k + rid)) { seen.add(k + rid); out.push({ kind: "room", id: rid, label: nm, sub: "item · " + roomLabel(rid) }); } }
    for (const [cid, a] of Object.entries(st.agents || {})) for (const [k, n] of Object.entries(a.inv || {})) { const nm = iname(k); if (n > 0 && (nm.toLowerCase().includes(qq) || k.includes(qq))) out.push({ kind: "person", id: cid, label: nm, sub: "carried by " + nameOf(cid) }); }
    return out.slice(0, 12);
  }
  const roomLabel = (rid) => (rid && ((S.W && S.W.rooms[rid] && S.W.rooms[rid].name) || (G.map.rooms[rid] && G.map.rooms[rid].name))) || rid || "outside";
  function goHit(h) { if (h.kind === "person") focusOn(h.id); else focusRoom(h.id); }

  // the minimap: every level in miniature, the part on screen outlined; click to jump there
  function drawMini() {
    const mc = q("#tmmini"); if (!mc || mc.style.display === "none") return;
    const now = performance.now(); if (G.miniAt && now - G.miniAt < 150) return; G.miniAt = now;
    const [ww, wh] = worldSize(), k = Math.min(mc.width / ww, mc.height / wh), c = mc.getContext("2d");
    G.mini = { k, ox: (mc.width - ww * k) / 2, oy: (mc.height - wh * k) / 2 };
    c.fillStyle = "#0b0c12"; c.fillRect(0, 0, mc.width, mc.height); c.imageSmoothingEnabled = true;
    for (const p of G.planeIds) { const v = V(p); c.drawImage(levelCache(p), G.mini.ox + v.ox * k, G.mini.oy + v.oy * k, (v.x1 - v.x0) * k, (v.y1 - v.y0) * k); }
    const P = positions();
    for (const [id, p] of Object.entries(P)) { if (p.dead) continue; c.fillStyle = info2(id).color || "#fff"; c.fillRect(G.mini.ox + WX(p.plane, p.x) * k - 1.5, G.mini.oy + WY(p.plane, p.y) * k - 1.5, 3, 3); }
    for (const g of G.talks || []) { c.strokeStyle = "#ffd36b"; c.lineWidth = 1.5; c.beginPath(); c.arc(G.mini.ox + WX(g.p, g.x) * k, G.mini.oy + WY(g.p, g.y) * k, 4, 0, 6.3); c.stroke(); }
    const s = G.view.s, vx = -G.view.ox / s, vy = -G.view.oy / s;
    c.strokeStyle = "#3ee0d0"; c.lineWidth = 1.5; c.strokeRect(G.mini.ox + vx * k, G.mini.oy + vy * k, (cv.width / s) * k, (cv.height / s) * k);
  }
  // who is talking right now, where; click to go there
  function drawTalkPanel() {
    const box = q("#tmtalk"); if (!box) return;
    const talks = G.talks || [], key = talks.map((g) => g.room + ":" + g.ids.join(",")).join("|");
    if (box._key === key) return; box._key = key;
    box.style.display = talks.length ? "block" : "none";
    box.innerHTML = '<div class="th">Talking now</div>' + talks.map((g, i) => `<div class="tt" data-i="${i}"><b>${esc2(roomLabel(g.room))}</b> ${esc2(g.names)}</div>`).join("");
    box.querySelectorAll(".tt").forEach((d) => (d.onclick = () => { const g = talks[+d.dataset.i]; if (g) focusOn(g.ids[0]); }));
  }
  const esc2 = (x) => String(x).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" })[c]);
  function frame() { draw(); if (!T.visible) return; drawMini(); drawTalkPanel(); }
  function focusSelectedRoom() {
    const id = T.follow || S.selected, P = positions();
    if (id && P[id]) { const rid = roomOf(P[id].plane, Math.round(P[id].x), Math.round(P[id].y)); if (rid) return focusRoom(rid); }
    if (S.selRoom && G.map.rooms[S.selRoom]) focusRoom(S.selRoom);
  }

  function buildDom() {
    const stage = q("#stage");
    cv = document.createElement("canvas"); cv.id = "tmap"; q("#map").after(cv); ctx = cv.getContext("2d");
    tip = document.createElement("div"); tip.id = "tmtip"; stage.appendChild(tip);
    const bar = document.createElement("div"); bar.id = "tmbar";
    bar.innerHTML = `<div class="tmgrp" id="tmzoom"><button data-z="all" title="Every level at once">Whole map</button><button data-z="island" title="The island and the ground floor">Island</button><button data-z="house" title="The house's ground floor">House</button><button data-z="levels" title="The upper floors, the roof and the cellars">Levels</button><button data-z="room" title="The room of whoever is selected">Room</button></div>
      <div class="tmgrp" id="tmplanes">${G.planeIds.filter((p) => p !== "ground").map((p) => `<button data-p="${p}" title="${PLANE_LABEL[p] || p}">${PLANE_SHORT[p] || p}</button>`).join("")}</div>
      <div id="tmfindw"><input id="tmfind" type="search" placeholder="Find someone, a room, an item" autocomplete="off"><div id="tmhits"></div></div>
      <button id="tmLayersBtn" title="Layers and tools">Layers</button><button id="tmSettingsBtn" title="Which events pause the game">Pause settings</button>
      <div id="tmLayers"><label><input type="checkbox" data-l="labels" checked> Room names</label><label><input type="checkbox" data-l="furn" checked> Furniture</label><label><input type="checkbox" data-l="items" checked> Items</label><label><input type="checkbox" data-l="marks" checked> Marks</label>
      <label><input type="checkbox" data-l="light" checked> Light</label><label><input type="checkbox" data-l="noise" checked> Noise</label><label><input type="checkbox" data-l="cam"> Cameras</label><label><input type="checkbox" data-l="tint"> Zone tint</label><label><input type="checkbox" data-l="grid"> Grid lines</label>
      <label><input type="checkbox" data-l="perc"> What the selected person sees and hears</label><select id="tmLight"><option value="lit">lit</option><option value="dim">dim</option><option value="dark">dark</option></select>
      <label><input type="checkbox" id="tmMiniOn" checked> Minimap</label><label><input type="checkbox" id="tmEdit"> Edit map (GM)</label><label><input type="checkbox" id="tmLegend"> Legend</label></div>`;
    stage.appendChild(bar);
    const mini = document.createElement("canvas"); mini.id = "tmmini"; mini.width = 220; mini.height = 130; mini.title = "Click to jump there"; stage.appendChild(mini);
    const talk = document.createElement("div"); talk.id = "tmtalk"; stage.appendChild(talk);
    const ed = document.createElement("div"); ed.id = "tmedit";
    ed.innerHTML = `<h3>Map editor</h3><div class="sub">Left-drag paints on any level, right-drag pans. Doors, stairs and hatches are protected.</div>
      <select id="edTool">${TILES.filter(([k]) => PAINTABLE.has(k)).map(([k, n]) => `<option value="t:${k}">${n[0].toUpperCase() + n.slice(1)}</option>`).join("")}<option value="t: ">Nothing</option><option value="f:add">Place furniture</option><option value="f:del">Remove furniture</option></select>
      <select id="edFurn">${FURN_KINDS.map((k) => `<option>${k}</option>`).join("")}</select><div><button id="edUndo">Undo</button><button id="edCheck">Validate</button><button id="edSave">Save</button><button id="edReset">Reset to generated</button></div><div id="edMsg"></div>`;
    stage.appendChild(ed);
    const lg = document.createElement("div"); lg.id = "tmlegend"; lg.innerHTML = "<h3>Legend</h3>" + TILES.map(([k, n]) => `<div class="lg"><canvas data-k="${k}" width="${REN}" height="${REN}"></canvas>${n}</div>`).join("") + `<div class="lg"><canvas data-k="h" width="${REN}" height="${REN}"></canvas>hidden hatch (GM view)</div>`;
    stage.appendChild(lg);
    const tt = document.createElement("div"); tt.id = "tmtoasts"; stage.appendChild(tt);
    const md = document.createElement("div"); md.id = "tmmodal"; md.innerHTML = '<div class="card" id="tmcard"></div>'; document.body.appendChild(md);
    lg.querySelectorAll("canvas").forEach((c2) => { const k = c2.dataset.k, im = k === "h" ? (() => { const t2 = document.createElement("canvas"); t2.width = t2.height = REN; hatchPaint(t2.getContext("2d"), 0, true, "r"); return t2; })() : tileFor(k); if (im) c2.getContext("2d").drawImage(im, 0, 0); });
    const zoom = { all: fit, island: () => fitPlane("ground"), house: fitHouse, levels: fitLevels, room: focusSelectedRoom };
    bar.querySelectorAll("#tmzoom button").forEach((b) => (b.onclick = () => { if (b.dataset.z !== "room") T.follow = null; T.touched = true; zoom[b.dataset.z](); }));
    bar.querySelectorAll("#tmplanes button").forEach((b) => (b.onclick = () => { T.follow = null; T.touched = true; fitPlane(b.dataset.p); }));
    const find = q("#tmfind"), hits = q("#tmhits");
    const showHits = () => { const hs = searchHits(find.value); G.hits = hs; hits.innerHTML = hs.map((h, i) => `<div class="hit" data-i="${i}"><b>${esc2(h.label)}</b> <span>${esc2(h.sub)}</span></div>`).join(""); hits.style.display = hs.length ? "block" : "none"; hits.querySelectorAll(".hit").forEach((d) => (d.onmousedown = (ev) => { ev.preventDefault(); goHit(hs[+d.dataset.i]); hits.style.display = "none"; find.blur(); })); };
    find.oninput = showHits; find.onfocus = showHits; find.onblur = () => setTimeout(() => (hits.style.display = "none"), 150);
    find.onkeydown = (ev) => { if (ev.key === "Enter" && G.hits && G.hits[0]) { goHit(G.hits[0]); hits.style.display = "none"; find.blur(); } if (ev.key === "Escape") find.blur(); ev.stopPropagation(); };
    mini.onclick = (ev) => { if (!G.mini) return; const r = mini.getBoundingClientRect(), wx = ((ev.clientX - r.left) * (mini.width / r.width) - G.mini.ox) / G.mini.k, wy = ((ev.clientY - r.top) * (mini.height / r.height) - G.mini.oy) / G.mini.k; T.follow = null; T.touched = true; G.view.ox = cv.width / 2 - wx * G.view.s; G.view.oy = cv.height / 2 - wy * G.view.s; G.miniAt = 0; };
    q("#tmMiniOn").onchange = (e) => (mini.style.display = e.target.checked ? "block" : "none");
    q("#tmLayersBtn").onclick = () => q("#tmLayers").classList.toggle("open");
    q("#tmSettingsBtn").onclick = openSettings;
    bar.querySelectorAll("[data-l]").forEach((i) => (i.onchange = () => (LY[i.dataset.l] = i.checked)));
    q("#tmLegend").onchange = (e) => (lg.style.display = e.target.checked ? "block" : "none");
    q("#tmEdit").onchange = (e) => { ED.on = e.target.checked; stage.classList.toggle("tm-edit", ED.on); if (ED.on) { edBuildProtect(); edMsg(G.map.custom ? "Editing your saved map." : "Editing the generated map."); } cv.style.cursor = ED.on ? "crosshair" : "grab"; };
    q("#edUndo").onclick = edUndo;
    q("#edCheck").onclick = async () => { const r = await edPost("/api/gridmap/validate"); edMsg(r.problems.length ? r.problems.join("\n") : "The map is valid.", r.problems.length ? "bad" : "good"); };
    q("#edSave").onclick = async () => { const r = await edPost("/api/gridmap/save"); edMsg(r.ok ? "Saved. It applies to the next live day you start." : r.problems.join("\n"), r.ok ? "good" : "bad"); };
    q("#edReset").onclick = async () => { await fetch("/api/gridmap/reset", { method: "POST", body: "{}" }); await loadMap(); edBuildProtect(); edMsg("Back to the generated map.", "good"); };
    bindCanvas(); bindTouch();
    new ResizeObserver(() => { resize(); if (T.visible && (!T.fitted || !T.touched)) { fit(); T.fitted = true; } }).observe(stage);
  }
  async function loadMap() {
    try { const r = await (await fetch("/api/gridmap")).json(); G.map = r.map; G.map.custom = r.custom; } catch (e) { G.map = await (await fetch("grid_map.json?" + Date.now())).json(); }
    G.rows = {}; G.zones = {}; G.map.planes.forEach((p) => { G.rows[p.id] = p.rows; G.zones[p.id] = p.zones || null; });
    const order = ["ground", "roof", "second", "first", "basement"], ids = G.map.planes.map((p) => p.id);
    G.planeIds = [...order.filter((p) => ids.includes(p)), ...ids.filter((p) => !order.includes(p))];
    G.rooms = Object.entries(G.map.rooms).map(([id, r]) => ({ id, ...r }));
    G.roomTiles = {};
    for (const p of G.map.planes) (p.zones || []).forEach((row, y) => { for (let x = 0; x < row.length; x++) { const rid = G.map.zone_codes[row[x]]; if (rid) (G.roomTiles[rid] = G.roomTiles[rid] || []).push([p.id, x, y]); } });
    G.cache = {}; G.over = {}; G.pings = []; G.talks = []; ED.undo = [];
  }

  // ---------------------------------------------------------------- what the main viewer uses
  window.TileMap = {
    async init() { await loadMap(); buildDom(); loadSettings(); resize(); fit(); T.ready = true; },
    ready: () => !!T.ready,
    show(on) { T.visible = !!on; if (cv) { const d = on ? "block" : "none"; cv.style.display = d; q("#tmbar").style.display = on ? "flex" : "none"; q("#tmmini").style.display = on && q("#tmMiniOn").checked ? "block" : "none"; if (on) { resize(); if (!T.fitted) { fit(); T.fitted = true; } } else { q("#tmedit").style.display = "none"; q("#tmlegend").style.display = "none"; q("#tmtalk").style.display = "none"; } } },
    setTick(t, m) { T.tick = t; if (m !== undefined) T.m = m; },
    setMinute(m) { T.m = m; },
    minute: () => T.m,
    duration() { return T.tick && T.tick.live ? T.tick.live.dur : 120; },
    talkMinutes() { return T.tick && T.tick.live ? T.tick.live.talk.map((s) => s.m) : []; },
    dialogFor,
    chatDialog,
    segMsgOn,
    openSettings,
    draw: frame,
    follow(id) { T.follow = id; },
    ping,
    focusRoom,
    focusOn(id) { if (positions()[id]) focusOn(id); else { const a = T.tick && T.tick.state && T.tick.state.agents[id]; if (a && G.map.rooms[a.room]) focusRoom(a.room); } },
  };
})();
