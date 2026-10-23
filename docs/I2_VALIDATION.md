# I2: persistent commitments

Implemented on 2026-10-22. `murder/commitments.py` owns the persistent store and its engine adapter; the runner still composes 81 mixins.

## Behavior checked

- Hosting, plots, pacts, accepted dares, protection, promises and reflection intentions survive save/load, including adoption from older saves.
- Stable IDs and original deadlines prevent repeated requests from refreshing an obligation. A concrete reason is required for voluntary replacement or abandonment. Casual reversals wait two hours; ended intentions have a 24-hour restart cooldown. Refused changes record wavering at most once per day.
- Reflection follow-ups wait until morning and complete through actual social moves. An attempted apology can be rebuffed. Promises require an awake recipient present and complete only on actual speech, transfer or arrival.
- Hosts attend their announced venue. Injury, danger, unreachable venues, departures and investigations can cancel obligations with recorded reasons. Voluntary abandonment has a composure cost and, for a known recipient, a relationship cost; existing pact/dare sanctions remain in their original systems.
- Decision and diary prompts include personal obligations. Shared voice cards respect who knows each obligation. GM character details show active obligations and recent outcomes. Only the affected person's commitments invalidate their prefetched decision.
- The story checker detects reopening, duplicate terminal events and unexplained endings. Commitment events retain their minute. Staged occasion conversations retain their prompts when keeping a run for later voicing.

## Offline validation

`python tools/check.py --browser --metrics` runs the smoke suite, focused Python regressions, JavaScript syntax/escaping, simulation reports and Chromium checks. `tests/commitment_check.py` adds 31 forced regressions. Full-season balance is checked separately with `python tests/season.py --seeds 40` (80 seasons across both configurations).

Core regressions pass: **1,189/1,189 smoke assertions** and **136 focused Python tests** (31 commitment, 18 session, 30 story, 20 trial, 20 reliability, 17 casting), plus JavaScript syntax and escaping checks.

A Chromium spot check with an injected commitment confirmed that the GM character panel displays terminal reasons, escapes markup in titles, and hides those details when GM mode is off.

Chromium casting and diagnostics regressions pass. The isolated viewer regression also passes: the day finishes, conversations do not freeze the clock, and the quiet-night prompt skips its block. Browser playback checks need exclusive use of their server: opening another viewer stops the active live session.

Current call baseline: **81.4 calls/day default** (16 simulated days), **75.4 violent** (20 days), using the baseline script's seeds 11, 22 and 33. Both are below the historical 91.7 calls/day yardstick. No new model-call sites were introduced; commitments change trajectories and how long a run lasts, so these figures are descriptive rather than a controlled estimate of savings.

Eighty full mock seasons (seeds 1–40 in each configuration) performed **566,497 story checks with zero violations**. All seasons finished.

| Configuration | Good | Bittersweet | Bad |
| --- | ---: | ---: | ---: |
| Default | 16 | 14 | 10 |
| Violent | 20 | 10 | 10 |
| Total | 36 (45%) | 24 (30%) | 20 (25%) |

The documented target is 40% good / 30% bittersweet / 30% bad. This sample is close enough to retain the existing ending settings; no ending or escape tuning was changed.

## Limits

These checks use the mock backend and deterministic forced scenarios. No paid model calls were made. They verify persistence and checked outcomes, rather than proving that a real model's dialogue feels more coherent. I3's lasting emotions, I6's general decision reasoning and the wider relationship/ending balance pass remain separate work. Plots retain their existing planning stages and physical requirements; this change does not claim a measured increase in planned killings. The season sample is a current result, not a matched before/after experiment.
