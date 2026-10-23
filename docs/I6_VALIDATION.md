# I6: choices with recorded reasons

Implemented on 2026-10-23. Offline verification is complete. **The real-model prose review remains pending:** this cloud environment has neither Claude CLI nor Anthropic API credentials configured. No paid calls were made.

## What changed

`murder/decisions.py` owns checked request menus, response binding, persistent stated motives, disclosure and dawn commitment updates. Model transport stays in `llm.py`; the runner still composes 81 mixins.

Non-routine decision prompts provide stable option IDs, action availability, reachable destinations, conversation intentions, available items, existing commitments and the person's strongest emotions. The response schema includes an option, a private first-person reason, optional references to owned active commitments/emotions, and an explicit disclosure flag. Fixed option fields cannot be contradicted. Consuming a response rechecks availability, including stale early answers. Advanced action requests still undergo their mechanic's parameter, physical and outcome checks. The menu does not promise success.

Each record preserves the selected request and reason, backend source, validated reference IDs and status. The history distinguishes selection, attempted action, blocked travel, unconsciousness, engine changes and accepted proposals. Attempts and accepted proposals are not completed actions. Invalid requests get a safe fallback without another model call; their original reason is not attached to the fallback as its motive. Old responses remain compatible, with missing reasons explicitly missing.

The store keeps at most 48 records per person and prunes entries older than 30 days on writes. Private prompts recall three recent motives from the last week; the GM panel shows eight records. Save/load retains the history and stable IDs. NeoVi/Kumiko identity changes preserve participants and known audiences.

Reasons remain private unless a character explicitly says one aloud. That produces a spoken event for checked listeners. Shared dialogue and trial cards only receive motives known to the entire group. Private decisions and diaries can recall the person's own reasons. Diary/private memory entries are excluded from shared brain cards, closing an indirect disclosure path. Reasons are labelled intentions and may be lies: they never add evidence, sightings, alibis or suspicion scores. The existing trial scoring is unchanged.

Reactions now receive checked reaction kinds, commitments, emotions and motive context, and retain their own reason. Proposals receive that personal context and record why the person wants the proposed plan or social move. Acceptance is distinguished from performance. No new model-call sites were added. Decision replies have a 450-token output budget, previously 350, to accommodate the extra fields.

At dawn, explicit commitment updates pass through the existing I2 rules. Keeping an obligation never refreshes its deadline; abandoning requires ownership and a concrete reason and retains the existing cost. New personal requests respect cooldowns and wait until morning when appropriate. A diary cannot make a spoken promise or declare follow-through. Early diaries become stale when that person's motive, commitment or major emotion context changes.

## Offline checks

```sh
python tools/check.py --browser --metrics
python tests/decision_seasons.py --seeds 40 --output /tmp/i6-seasons.json
python tests/mock_metrics.py --brain --output /tmp/i6-brain.json
python tests/real_decision_day.py --backend mock --output /tmp/i6-review.json
```

Core smoke passes **1,189/1,189**, and focused suites pass **262 tests**, including **36 I6 cases**. The new cases cover option contracts, stale targets/items, blind item menus, malformed replies, legacy responses, bounded storage, persistence, reference ownership, private/shared contexts, disclosure, actual engine overrides, blocked movement, dawn application, proposal/reaction reasons, diary recall and unchanged trial evidence/suspicion. Prompt preparation remains read-only in the normal prefetch lifecycle.

Chromium coverage passes for casting, diagnostics, emotions, stated motives and playback. The motive check uses an actual mock request, verifies API snapshot records, and checks GM-only display, status changes and escaped text. The viewer completes generation with no errors or frozen conversation frames; two quiet night blocks are generated, and the skip prompt is offered and successfully used.

A preliminary smoke pass exposed a probabilistic test setup: the GM-roll check expected a spontaneous strike before the cast escaped. The test now opens a real, valid strike window through `plot_slice` and checks the GM hook directly, without carrying out the killing. No simulation behavior was changed to repair that setup. The final full offline command includes this correction.

## Whole-season results

The observer in `decision_seasons.py` retains references to all decision records until a season ends, including records removed from the bounded save history. It does not change choices. The sample uses the same seeds 1–40 and Default/Violent configurations as I7.

All **80 seasons finish**, with **537,621 story checks and zero violations**. Across **30,824 records**, every non-rejected request has a reason. There are **zero rejected primary decisions**. Three no-offer murder-plan proposals return no scheme and are rejected; the existing planner remains in control.

| Record kind | Count |
| --- | ---: |
| Ordinary model decisions | 30,092 |
| Reactions | 550 |
| Proposals | 182 |

| Final recorded status | Count |
| --- | ---: |
| Attempted | 28,091 |
| Selected, without a recorded attempt | 1,833 |
| Blocked | 345 |
| Changed by engine direction | 373 |
| Proposal accepted | 179 |
| Rejected | 3 |

Selected records intentionally remain intentions; they are not presented as completed actions. Structured checks do not establish that a free-prose reason is psychologically convincing or truthful.

| Sample | Good | Bittersweet | Bad |
| --- | ---: | ---: | ---: |
| I7 reference, 80 seasons | 42 | 21 | 17 |
| I6 Default, 40 seasons | 24 | 8 | 8 |
| I6 Violent, 40 seasons | 20 | 15 | 5 |
| I6 combined | **44** | **23** | **13** |

New romances number 76 in Default and 66 in Violent, with no duplicate formations. The maximum per person is four in Default and two in Violent, compared with two in both I7 samples. Trust/history/cooldown gates were unchanged; longer individual histories still warrant qualitative review. The 55% good-ending share exceeds the historical 40% target. No escape, ending, romance or lethality settings were tuned in I6. Changed prompt text also changes seeded mock answers, so these trajectory differences are descriptive rather than evidence that storing reasons improves survival.

## Calls and remaining calibration

The matching baseline reports **87.3 calls/day Default** and **93.0 Violent**, each over 21 days. I7 reported 72.2 over 12 days and 76.9 over 15 days. Violent is 1.3 calls/day above the historical 91.7 yardstick.

The breakdown explains where the increase occurs: Default decisions/voicing rise from 36.8/8.9 to 46.1/11.8 per day; Violent rises from 40.1/9.6 to 49.3/12.0. The new sample completes all three seven-day weeks in both configurations, whereas the I7 sample stopped several weeks early. An inspected Violent week (seed 11) retains eight people through its first four days and has only **one** wasted early diary across seven days. Increased decision opportunities and conversation work dominate; this is not a new call-site loop. The larger usage and shifted ending balance deserve a separate cost/balance pass. Actual token cost remains unmeasured because no real backend was run.

The supplementary brain-on sample completes 30 days without errors, with 1,550 decisions, 183 talk intentions, 51 work intentions, 72 experiments and 19 hosting proposals. All eight participants speak in every run; 58 of 195 live conversations gain a joiner. This is an additional configuration, not a comparison with real-model frequencies.

## Pending real-model review

`tests/real_decision_day.py` defaults to the free backend and was exercised on a scratch day: 25 decisions, no engine errors or missing reasons, with 23 attempts, one blocked request and one engine change. One reason explicitly references the prepared commitment. It saves the offered requests, actual answers, motive records, later dialogue, diaries, statuses and usage. Its setup includes a personal commitment and a lasting emotion. A zero exit status only establishes that the day ran without engine errors; semantic review is explicitly required.

Once a real backend is configured and usage is authorized, run the same harness with `--backend cli` or `--backend api`, then review whether reasons fit their selected requests, later diary lines refer to them accurately, and characters keep private motives private. It uses roughly 60–120 calls and accepts the existing daily call-cap setting. Repository instructions require asking before usage-consuming real calls; the offline command never invokes them.

I8's remaining murder preparation and cover-up work is the next implementation step. Real-model reason quality and the usage/balance follow-up remain separate open gates.
