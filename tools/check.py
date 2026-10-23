"""Run the offline regressions, optionally including local browser checks and metrics."""
import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
PYTHON_CHECKS = ("smoke", "session_check", "story_check", "trial_check", "reliability_check", "casting_check", "commitment_check", "relationship_check", "emotion_check", "mock_check", "decision_check")
BROWSER_CHECKS = ("casting_check", "diagnostics_check", "emotion_check", "decision_check", "viewer_check")


def run(command, env):
    print("\n" + " ".join(map(str, command)), flush=True)
    subprocess.run(command, cwd=ROOT, env=env, check=True)


def browser_check(name, env):
    # Each script gets a fresh world. Refuse to test an unrelated server.
    try:
        urllib.request.urlopen("http://127.0.0.1:8766/api/status", timeout=1).close()
    except OSError:
        pass
    else:
        raise RuntimeError("Port 8766 is already in use; stop that server before running browser checks.")
    with tempfile.TemporaryDirectory(prefix="mc_browser_") as tmp:
        child_env = dict(env, MC_DATA_DIR=tmp)
        with open(Path(tmp) / "server.log", "w+", encoding="utf-8") as log:
            server = subprocess.Popen([sys.executable, "-u", "server.py", "--no-browser"], cwd=ROOT, env=child_env, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    if server.poll() is not None:
                        log.seek(0)
                        raise RuntimeError(log.read())
                    try:
                        with urllib.request.urlopen("http://127.0.0.1:8766/api/status", timeout=1):
                            break
                    except OSError:
                        time.sleep(.1)
                else:
                    raise RuntimeError("Test server did not become ready")
                run(["node", "--require", str(ROOT / "tools/browser-runtime.cjs"), f"tests/{name}.js"], child_env)
            finally:
                server.terminate()
                try:
                    server.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    server.kill()
                    server.wait()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--browser", action="store_true", help="also run casting, emotion details, viewer and diagnostics in local Chromium")
    parser.add_argument("--metrics", action="store_true", help="also report baseline, balance, pacing and mock behavior without rewriting docs")
    args = parser.parse_args()
    env = dict(os.environ)
    # Inherited mock knobs must not silently weaken or destabilize the suite.
    for key in list(env):
        if key.startswith("MC_MOCK_"):
            del env[key]
    env.pop("MC_URL", None)
    if not shutil.which("node"):
        raise RuntimeError("Node.js is required for the offline JavaScript checks")
    for name in PYTHON_CHECKS:
        run([sys.executable, f"tests/{name}.py"], env)
    for path in sorted((ROOT / "static").glob("*.js")):
        run(["node", "--check", str(path)], env)
    run(["node", "tests/escape_check.js"], env)
    if args.metrics:
        for name in ("baseline", "balance", "pacing", "mock_metrics"):
            run([sys.executable, f"tests/{name}.py"], env)
    if args.browser:
        if not env.get("MC_CHROMIUM"):
            chromium = shutil.which("chromium") or shutil.which("google-chrome")
            if chromium:
                env["MC_CHROMIUM"] = chromium
        for name in BROWSER_CHECKS:
            browser_check(name, env)
    print("\nAll selected offline checks passed.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except (subprocess.CalledProcessError, RuntimeError) as exc:
        print(f"\nOffline checks failed: {exc}", file=sys.stderr)
        sys.exit(exc.returncode if isinstance(exc, subprocess.CalledProcessError) else 1)
