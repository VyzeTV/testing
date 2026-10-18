# Murder Channel: handoff notes for the next agent

A Danganronpa-style killing-game simulation. **The engine decides what happens; a language model only voices it** (dialogue lines, diaries, a few decisions). Python engine in `murder/`, a static browser viewer in `static/`, `server.py` serves both.

## Where things stand (2026-10-16)

- Work branch: **`claude/gallant-rubin-5645qr`** (all work is pushed there; `main` is the user's, never push to it; no PR has been opened).
- The rebuild plan lives in a Claude Docs doc, **"Murder Channel: Rebuild Plan"**: https://claude.ai/code/artifact/4e557715-028c-42d6-a8dd-1b01d3671bc5 (its Roadmap section lists phases 0-8 with a gate for each; done phases say "Done: ..."). A companion doc, "Engine-First Design", explains the philosophy. In-repo design docs: `docs/GAME_DESIGN.md` (the authoritative description of how the game works), `docs/DESIGN.md`, `docs/BASELINE.md`, `README.md`.
- **Phases 0-4 are done**:
  0. Prep (baseline metrics, determinism).
  1. Map v4: floor-plan files for every level plus a compact island, a validator, and A* across levels (`mapgen.py`, `gridmap.py`, `gridnav.py`).
  2. Continuous simulation: a minute clock (`clock.py`), tile positions as engine state (`sim.py`), falls (`falls.py`), chunk streaming, and continuous viewer playback.
  3. Live conversations: engine-resolved social moves (`social.py`), conversations that people join, leave and interrupt on the clock (`convo.py`), per-line overhearing, a template or model voice (`voice.py`), and the confessional booth (`booth.py`).
  4. The day and nights:
     - `schedule.py`: meals in the Dining Hall with calm/tense rewards, skip costs, a news ledger, GM schedule edits, and NeoVi fetching stragglers.
     - `night.py`: bedtime at 22:00, night blocks at hours 23/25/27/29 (they run past midnight so time only moves forward; displayed with `% 24`), dawn at 31 (07:00) with diaries and the day increment. Sleep is a task, waking has reasons, and a short night leaves someone exhausted.
     - Deadline-day hourly sanity loss (`engine.tick_dread`/`deadline_hours`).
     - Viewer quiet-night skip (ask / auto / watch) and a GM "Skip quiet night" button.
- **Phase 5 is done**: the code-health step (hash-seed determinism, the duplicate-method test, old-save conversion via `session.resume_hour`, `viewer_check.js` now plays into a night; the trial is not reached in the browser check) and **belief bases** (`beliefs.py`; see `docs/GAME_DESIGN.md` section 6, "Beliefs"). Still open from phase 5's plan: night uses of beliefs (snooping, secret meetings; moved into phase 6) and a real-model day. A real day needs no API key: the default `cli` backend uses the `claude` command and the user's subscription (about 90 calls a day), so ask the user before running one.
- **Phase 6 is done**: night snooping and secret meetings (`nightlife.py`), the murder planner (`planner.py`), fights in blows with hit locations (`combat.py`), hands, pockets and item capabilities (`carry.py`), and captivity wear tuning sanity to about 60 at the end of a week (`mind.mind_wear`, dial `wear`). Also done: gear (`gear.py`: gloves and prints, a coat that takes the blood, bags and a holster) and item combinations in the planner (`planner.COMBOS`: a rope to stage a hanging, sleeping pills and the bath). Not done: showing the wounds in the autopsy and trial (stored in `case["wounds"]`, `case["wound_text"]`; prints in `case["prints"]`) for phase 7.
- After phase 6: evidence rules (`evidence.py`: no TereVi footage for the cast, NeoVi stills, personal cameras; TereVi's structured Case File `case["cf"]` updated by `file_learn`, clues by `update_clue`), silencing (gags, hand over the mouth, drowning; `combat.py`), and more planner schemes (lure, trap, drown, subdue first). Lethality is deliberately low; with it, a default mock week sometimes reaches the reckoning.
- **Phase 7 has begun**: the claim-based trial (`claimtrial.py`, dial `claim_trial`): claims, weak points, willingness, lie planner, credibility, a public suspicion meter, sequences (debate, hot seat, clash, brainstorm, closing) and computed votes; one voicing call per sequence. Not done yet from phase 7: the later sequences (cross-examination, split court, the climax reconstruction), a truth-versus-belief report after each trial, and special scenes as live practices (the trial still runs as a staged scene).
- Later phases (see the plan doc):
  - 6: affordances and a murder planner, plus fights in blows, carrying slots, hit locations and a small catalogue of distinct items (listed under "Phase 6 additions").
  - 7: a claim-based trial, which is also where special scenes become live "practices" instead of being written whole.
  - 8: a director upgrade.

## Running and checking

- Tests (mock LLM, no network): `python tests/smoke.py` (915 checks, about 45 seconds; must end `N/N passed`) and `python tests/baseline.py` (mock calls a day; keep it at or below about 91.7. It is about 90 now: close to the ceiling).
- Balance numbers: `python tests/balance.py --write` (about 30 seconds) writes `docs/BALANCE.md`: deaths and how weeks end, trials and verdicts, sanity, idle time, meals, nights, beliefs and lies caught. Report them at every phase gate.
- Browser check: `MC_DATA_DIR=<scratch dir> python server.py &` then `node tests/viewer_check.js` (expects `frozen: 0`, `errors: []`). Use a fresh data dir: a leftover session or an old server on port 8766 gives misleading results. Stop the server with `pkill -f "[s]erver.py"` in its own shell call (an unbracketed pattern kills the shell itself).
- Playwright and Chromium are preinstalled (`/opt/node22/lib/node_modules/playwright`).
- A game must not depend on Python's hash seed: never let set order drive a choice (iterate `sorted(...)` instead). `smoke.py` runs three mock days under `PYTHONHASHSEED=1` and `=2` and fails if they differ, and also fails if two mixins define the same method name.
- Checks that rely on chance (for example "a trial happens in this mock week") should force the outcome (`murder.llm.LLM.mock_murder_prob`, `murders=False`) rather than hope for it.

## How the engine is put together (quick map)

- `engine.py`: `DayRunner` is built from about 45 mixins (one per file).
- `run()` loop: the day's turns at 8..20 in 2-hour steps (`run_tick`), special scenes when due (trial, vigil, last call, presentations, reveal, endgame, finales), then `run_bedtime`, the night blocks (`run_night_block`) and `run_dawn`.
- `run_night()` is a one-tick compatibility version used by tests.
- `emit(tick)` finalises every tick: env, mind, positions, hearing and the deadline hours.
- `run_tick` runs on a minute cursor:

  | Minute | What runs |
  |---|---|
  | 0 | Decisions, then arrivals (`arrive_and_act`) |
  | 15 | Passive systems |
  | Meet minute | Attacks |
  | 20 | Assaults |
  | About 30 | Meal call |
  | Free blocks | Free time (`freetime.py`, 15-minute slices) |
  | 40 / 90 | Hazards |
  | 60 | Dread and drains |
  | 56 / 92 | Live conversations |

  After the conversations: voice, then `meal_settle`, reactions and the booth.
- **Free time** (`freetime.free_pick`) scores activities from needs and facets.
  - At night only `NIGHT_ACTS` are allowed, plus a `sleep` act.
  - `add(..., far=True)` lets a real need search beyond the normal reach.
- **Method names collide silently across mixins.** Before adding a method, grep for its name; `ConditionMixin.wake_up` (coming round from unconsciousness) was nearly shadowed; `smoke.py` now checks for this.
- **Tuning dials:** `settings.py` (`self.tune(key)`).
- **GM actions:** `session.GM_TYPES` → `story.apply_gm`.
- **Conventions:** comments are sparse and plain; docstrings explain intent. Docs are written in plain, short sentences. Commit messages end with the session's attribution lines.

## The user

They steer feature by feature and ask "what is phase N?" questions; answer concisely and ask before starting a new phase. They prefer that each step is committed with tests passing.
