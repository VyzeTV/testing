# Murder Channel: agent guide

The engine owns events; models voice dialogue and scenes. Develop in the existing checkout. Work branch: `claude/gallant-rubin-5645qr`; never push to `main`, and ask before pushing. Cloud tasks are already isolated: do not create a worktree unless asked.

## Run and check

Follow [README.md](README.md) for setup. Python 3.10+, dependencies in `requirements.txt`; Node.js 18+ for JavaScript checks, pinned Playwright in `package-lock.json` for browser checks. The server uses port 8766. Never depend on a hardcoded global Node/Playwright path.

Run `python tools/check.py` for core offline regressions. Run `python tools/check.py --browser --metrics` for the full offline regression workflow and baseline/balance/pacing reports. Browser tests need a free port 8766 and Chromium. Use scratch `MC_DATA_DIR` for manual checks, and stop only the server processes you started. Do not use report scripts' `--write` option unless intentionally refreshing documentation. Real AI calls consume usage; ask before running them.

Test counts and runtimes are reported by the commands. Browser checks need exclusive use of their scratch server; opening another viewer stops its active live session. `docs/BASELINE.md` is the historical yardstick (about 91.7 model calls/day); investigate material changes rather than overwriting it to hide a regression. Mixin method names must be unique; smoke checks enforce that. Iterate sorted collections wherever order influences seeded randomness.

## Architecture and current work

`DayRunner` in `murder/engine.py` composes 81 mixins. The day/night clock, partial streaming, beliefs, murder planner, trials and director upgrade are implemented; Phase F is complete. Current behavior is described by [docs/GAME_DESIGN.md](docs/GAME_DESIGN.md). [docs/NEXT_STEPS.md](docs/NEXT_STEPS.md) retains run findings and the remaining feature backlog.

Extract responsibilities gradually in areas you change. Bond policy/history lives in `relationships.py`, plan transition history in `plan_history.py`, persistent obligations and their engine adapter in `commitments.py`, named emotions and event appraisal in `emotions.py`, seeded offline character policy in `mock_policy.py`, checked model requests and stated motives in `decisions.py`, atomic save rotation/recovery in `saves.py`, and generation-state derivation in `diagnostics.py`. Keep runner-specific world interactions in adapters; do not add mixins just to house independent policy. Plan changes require reasons and physical method requirements cannot be bypassed silently.

The user's current request authorizes relationship and plan continuity, save recovery/diagnostics, dependency manifests, a single offline check command, documentation cleanup, and focused extraction in these areas. Ask before starting unrelated feature phases. Preserve user changes. Prefer commits with tests passing; do not push without authorization. Comments and prose should be plain and concise.

Historical run details and comic tooling decisions are preserved in [docs/HANDOFF_HISTORY.md](docs/HANDOFF_HISTORY.md). Comic generation is optional and outside offline setup: never put `ATLASCLOUD_API_KEY` in chat/source, state costs before a batch, and ask when a requested scene is refused instead of silently changing it. Preserve the user's Nano Banana → Seedream → Qwen model preference and portrait references if that work is resumed.
