# Murder Channel: Live Edition

A local killing-game simulation with a Python engine and a browser viewer. The engine decides what happens; a model voices dialogue and scenes. The free Mock backend runs without credentials or network access.

## Install and run

Requires Python 3.10+ (validated with 3.12). From this checkout:

```sh
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python server.py --no-browser
```

The viewer listens on port **8766**. Open it locally and choose **Start a day → Mock**. The default backend is Claude CLI, which requires the `claude` command and its login. The optional Anthropic API backend requires `ANTHROPIC_API_KEY`; enter credentials through your environment settings, never in source files. Real-model checks consume usage and are separate from offline checks.

`start.bat` starts the same server on Windows. `start_remote.bat` enables password-protected network access; use only a trusted private network. Do not forward the port publicly.

## Offline checks

Requires Node.js 18+ as well as Python. Run all core regressions with one command:

```sh
python tools/check.py
```

This runs the engine smoke suite (including hash-seed determinism and duplicate mixin-method checks), session lifecycle, story, trial, persistence/recovery/diagnostics, casting, mock-behavior and decision-reason regressions, JavaScript syntax checks and HTML escaping checks. It stops with a nonzero exit status on failure. Saves use temporary directories.

To include all regression checks, including local browser playback and the diagnostics UI:

```sh
npm ci
npx playwright install chromium
python tools/check.py --browser
```

The runner starts and stops a fresh local server for each browser check; port 8766 must be free. A prepared machine's system Chromium can be used when Playwright's browser is absent (`MC_CHROMIUM=/path/to/chromium`; common Linux paths are detected). Mock mode makes no AI calls. Browser tests take a few minutes.

Add `--metrics` to also report baseline usage, balance, pacing and mock behavior without rewriting tracked documents. `tests/season.py`, `tests/cast_stats.py` and `tests/seed_finder.py` are optional simulation/report tools. `tests/pace_check.js` and `tests/stream_check.js` are optional timing experiments; the latter uses a server started with `MC_MOCK_LATENCY=4`. Test counts and runtimes come from the current runner, not old feature notes.

## Saves, recovery and diagnostics

The server writes `state/current.json` atomically and rotates the three previous valid saves as `state/current.backup-1.json` through `-3.json`. On a corrupt or missing current save it restores the newest readable, structurally valid backup. A damaged current save is preserved as `state/current.corrupt.json`. If no valid version remains, startup fails with a recovery message rather than starting a new season. Named save slots and day-start saves remain available. Automatic recovery may lose progress since the backup; use the Diagnostics report to see which day was recovered.

The header shows whether generation is computing, waiting for viewer playback, waiting on an AI call, waiting on a GM decision, complete, stopped or in error. **Diagnostics → Copy report** provides generation state, active-call timing, usage, checkpoint and backup health, plus the Python version and platform. It excludes prompts, dialogue, game secrets, credentials and raw provider error bodies. When clipboard access is unavailable, the report can be selected and copied manually.

Use `MC_DATA_DIR` to put saves and recordings outside the checkout. Tests always use scratch saves. A checkpoint supports resuming the last completed turn of an unfinished day.

## Starting cast

Each new season randomly fills **four female casting slots from ten candidates and four male casting slots from ten candidates**. Itsumi, Tsutsumi, Soura, Akira, Nao and Ivette join Seul, Vixen, Chloe and Cail in the female pool. Accio, Jackal, Vincent, Nathan and Katsuo join Szymon, Noah, Ayden, Shintaro and Reiko in the male slot pool. Reiko retains the female identity and she/her pronouns shown on her card; `casting_slot` controls allocation and vacancies independently. Selection is without duplicates, and each participant gets a separate bedroom. Starting another day, replaying, restarting the server or loading a save preserves that season's selected cast. Use **New game** to draw a fresh cast; an independent random draw can occasionally repeat a previous lineup.

The twelve added sheets include their backstories, private secrets, speech, stress responses, facets, values, starting belongings and appearance/outfit records. Akira and Vincent recognize their childhood friendship when both are selected. This does not create a starting romance or force either into the lineup. Soura's role-personas share her memories and relationships; their descriptions inform the existing character prompts rather than introducing separate participants.

Ivette and Reiko retain the cards’ country, birthday, height, weight, likes and dislikes. Ages (29 and 24) and private conflicts are writing defaults. Reiko has a persistent blind trait and a white mobility cane. Visual sightings, eyewitness evidence and direct reading of forensic clues are blocked; she can hear conversation, receive testimony and remember her own movements. Ordinary movement uses the existing map/navigation system, without a separate accessibility route solver.

Newly cast seasons begin with neutral relationship scores and empty diaries instead of importing encounters from the old fixed cast. Explicit backstory connections, such as Akira and Vincent’s childhood friendship, remain part of their character prompts. Keeping a scenario preserves its premise and applicable seeds; relationships and secret overrides referring to absent participants are removed. Both pools support further additions through the same selection logic.

Reference images from chat are not present as workspace files. The new characters currently have labeled initials as portrait placeholders; installing `static/portraits/<id>.png` replaces each placeholder automatically. Their appearance and clothing descriptions already follow the reference art.

For reproducible historical tests and report scripts, `new_state()` retains the original eight by default. Live season creation explicitly uses `randomize_cast=True`; callers can also pass a seeded `random.Random` instance through `rng` to reproduce a lineup and bedrooms. `tests/casting_check.py` exercises every added character in complete mock days, selection, old-save compatibility and future male-roster expansion. `--browser` also tests the New game UI and portrait fallback.

## Dialogue tone

Newly generated dialogue allows uncensored swearing, affectionate roasting, suggestive teasing and adult innuendo in each character’s own voice, including on Day 1. The existing **Flirtation** and **Banter and crude jokes** sliders control intensity. Sexual themes stay between consenting adults and fade to black before sexual activity; teasing does not create a romance or change an engine-decided outcome. Quiet conversations, awkwardness and serious moments still have room. Mock/fallback dialogue also uses the stronger register when relationships and settings support it.

## Mock behavior

The free backend now chooses from personality, needs, lasting feelings and active commitments. It prefers familiar company, avoids feared people and painful places, follows through on promises, and keeps existing murder plans with the planner. Reactions weigh helping against fleeing; nightly drives change only when a strong known feeling supports the change. Ordinary plan proposals use checked offers; impossible proposals remain explicit regression fixtures.

Choices use the existing per-prompt seeded random source, so parallel calls remain reproducible. `python tests/mock_metrics.py` reports short-run plotting, escape participation and conversation joiners; `--brain` also checks the optional memory/plan dial. See [I7 validation](docs/I7_VALIDATION.md) for measured changes and limits of comparison with real-model runs.

## Story continuity

Romances require mutual affection of at least 7, trust on both sides, and welcomed encounters on three different days spanning at least 48 hours within the past week. Trust grows at most once per relationship per game day and falls immediately when feelings sour. A current partner prevents another unacknowledged romance; affairs use the explicit night/discovery system. A person waits at least 24 game hours before forming another romance; a broken positive bond has a 48-hour reconciliation cooldown, extended to 72 hours after betrayal or an affair. History survives save/load. Existing bonds are not announced again; romances and pacts may coexist. First nights and NeoVi visits follow the same progression and cooldown rules. Betrayal memories last 21 game days, make confiding less likely, and slow trust repair. A diary entry can begin a repair without erasing that history. If both people in an affair have partners, each partner can discover it and react once. NeoVi becoming participant Kumiko preserves her relationship history.

Murder schemes keep their physical requirements: a push needs the planned edge, poison must be carried, and an electrical attack needs a powered bath and a live item. Urgency or ten unsuccessful striking turns can lead to an explicit change to an opportunistic attack. Changes and abandonments retain the previous scheme and a reason in persistent history and the GM feed. A model's null plot or different target needs `plot_reason`; omitting it keeps the plan. Failed special methods do not silently become unrelated assaults.

Hosting, plots, pacts, accepted dares, protection vows, promises and reflection intentions also persist as commitments. Repeating one keeps its original deadline; replacing or dropping one needs a concrete reason, and casual reversals wait at least two game hours. Abandoning an obligation costs composure and can cost the recipient's trust. Follow-through is checked against actual attendance, speech, gifts or arrivals; an apology can be rejected while still counting as an attempt. Injuries, departures and investigations can cancel obligations with a reason. The GM character panel shows active commitments and recent outcomes. Private plans stay out of shared dialogue prompts.

Known events now also leave lasting grief, guilt, fear, anger, shame, relief, attraction and loneliness. These feelings decay over days, survive save/load and influence ordinary choices, conversation and trial behavior. Revisiting a relevant person or place can briefly bring a feeling forward without resetting its lifetime. Private causes stay out of shared voice prompts. The GM character panel shows each emotion’s strength and cause; the existing sanity system still owns sanity changes.

## Choices and stated motives

Non-routine AI choices now select from checked request IDs and give a short private reason. The saved history distinguishes selection, attempted action, blocked movement, engine changes and accepted proposals; none of these claims success. The GM character panel shows recent motives and changes. Missing reasons in older responses stay visibly missing.

Later decisions and diaries can recall a person's own reasons. Shared scenes and trial voicing receive only reasons the person explicitly said aloud to the relevant listeners. Reasons may be self-serving and never create evidence, sightings or alibis. Dawn reflections can retain, abandon or request commitments through the existing ownership, cooldown and consequence rules; they cannot declare a promise fulfilled.

[The I6 report](docs/I6_VALIDATION.md) records offline coverage and the pending real-model review. `python tests/real_decision_day.py --backend mock --output /tmp/i6-day.json` produces a free scratch review day. Real backends require configuration and authorization because they consume usage.

## Maintenance map

`murder/engine.py` composes 81 mixins. Extract responsibilities when touching them instead of expanding the inheritance tree: `relationships.py` owns bond eligibility/history, `plan_history.py` records plan transitions, `commitments.py` stores obligations and checks their outcomes, `emotions.py` appraises known events and owns lasting feelings, `mock_policy.py` makes seeded mock character choices, `decisions.py` checks model requests and stores stated motives, `saves.py` handles atomic saves and recovery, and `diagnostics.py` derives generation status. Runner adapters remain in the existing mixins.

See [game design](docs/GAME_DESIGN.md) for mechanics and [next steps](docs/NEXT_STEPS.md) for the development backlog. [Historical feature notes](docs/FEATURE_HISTORY.md) and [historical handoff notes](docs/HANDOFF_HISTORY.md) preserve previous runs and design decisions; they are not setup instructions.
