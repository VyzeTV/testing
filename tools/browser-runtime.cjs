// Prefer Playwright's browser; allow a system Chromium in prepared environments.
const fs = require("node:fs");
const pw = require("playwright");
if (process.env.MC_CHROMIUM && !fs.existsSync(pw.chromium.executablePath())) {
  const launch = pw.chromium.launch.bind(pw.chromium);
  pw.chromium.launch = (options = {}) => launch({ ...options, executablePath: process.env.MC_CHROMIUM });
}
