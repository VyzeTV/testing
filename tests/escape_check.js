// Run: node tests/escape_check.js
const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const source = fs.readFileSync(path.join(__dirname, "../static/app.js"), "utf8");
const helper = source.split(/\r?\n/).find((line) => line.startsWith("function esc(s)"));
assert.ok(helper, "viewer escaping helper exists");
const context = vm.createContext({});
vm.runInContext(helper, context);
const escape = context.esc;
assert.equal(escape('&<>"\''), "&amp;&lt;&gt;&quot;&#39;");
assert.equal(escape('Alice "Ace" O\'Brien'), "Alice &quot;Ace&quot; O&#39;Brien");
const payload = '" onmouseover="alert(1)';
const html = `<img title="${escape(payload)}">`;
assert.equal((html.match(/"/g) || []).length, 2, "name cannot introduce attributes");
assert.equal(escape(42), "42");
console.log("HTML escaping checks passed");
