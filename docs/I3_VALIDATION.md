# I3: emotions from events

Implemented on 2026-10-22. `murder/emotions.py` owns the persistent store, event appraisal and adapters; the runner still composes 81 mixins.

## What changes

Known losses, violence, betrayal, humiliation, help, accepted flirtation and prolonged waking isolation leave named emotions. They retain causes, people and places, decay in game time and survive save/load. Read operations do not refresh a feeling. Repeated appraisal is deduplicated; comfort and reminders cannot repeatedly erase or renew a feeling within a block.

| Feeling | Half-life | Maximum life |
| --- | ---: | ---: |
| Grief | 3 days | 14 days |
| Guilt | 4 days | 14 days |
| Fear | 2 days | 10 days |
| Anger | 2 days | 10 days |
| Shame | 1.5 days | 7 days |
| Relief | 1.5 days | 5 days |
| Attraction | 3 days | 10 days |
| Loneliness | 2 days | 7 days |

Grief and loneliness bias company seeking; guilt encourages the booth or helping through cooking. Fear discourages approaching the threat, reduces receptivity, and can lead to locking a bedroom or, for a bold and vengeful person, planning against a known threat. Anger encourages confrontation; attraction strengthens already available flirt options. Urgent care, danger, privacy and commitments retain priority. Reminders briefly bring an existing feeling forward without extending its lifetime.

Decisions, diaries, inner thoughts, shared voice cards and trial behavior read these same records. Private causes stay private; hidden deaths, unseen attackers and unaware killers do not acquire factual knowledge from emotion appraisal. Trial bias is bounded and requires existing support. Feelings change no evidence, consent, romance eligibility or sanity directly. GM details display named strengths and causes.

## Checks

Run `python tools/check.py --browser --metrics` for core regressions, viewer checks and call/balance/pacing reports. `tests/emotion_check.py` covers persistence, analytic decay, repeated events, privacy, medical needs, room privacy, reminders, social moves, trial behavior and consistency between diaries and inner thoughts. `tests/emotion_check.js` checks snapshot fields, GM display, escaping and public-view privacy in an isolated browser.

The I4 reference is the previously captured 80-season sample, seeds 1–40 in both configurations. The I3 comparison uses the same full-season runner and seed set:

```bash
python tests/relationship_seasons.py --seeds 40 --output /tmp/i3-seasons.json
```

Core validation passes: **1,189/1,189 smoke assertions**, **198 focused Python tests** (36 emotion, 26 relationship, 31 commitment, 18 session, 30 story, 20 trial, 20 reliability and 17 casting), JavaScript syntax and escaping checks. Chromium casting, diagnostics and day/night playback checks pass. The separate emotion-panel browser check confirms real snapshot fields, GM strength/cause display, markup escaping and hidden details in public mode.

The smoke reflection sample now stops when its season ends instead of trying to run a finished season. Its original assertion that nightly reflection produces choices remains intact.

### Full-season comparison

| Configuration | Good before → after | Bittersweet before → after | Bad before → after |
| --- | ---: | ---: | ---: |
| Default, 40 seasons | 11 → 16 | 11 → 14 | 18 → 10 |
| Violent, 40 seasons | 9 → 9 | 15 → 19 | 16 → 12 |
| All 80 seasons | 20 → 25 | 26 → 33 | 34 → 22 |

All seasons finished. The verified sample performed **745,925 story checks with zero remaining violations**. The initial batch exposed one existing paired-death summary tagged with a deceased person as its active actor (violent seed 2). The summary now explicitly records deceased subjects without an active actor. A forced regression covers that path; the affected full season was rerun and substituted into the verified sample. Every outcome field was unchanged, and its story-check violation disappeared. The other 79 runs were unaffected; no other paired-death scene occurred in the sample.

Bad endings dropped from 42.5% to **27.5%**. Good endings are 31.25% and bittersweet endings 41.25%, against the documented 40% / 30% / 30% target. This improves the bad-ending share without establishing that survival balance is finished. No ending or escape settings were changed.

I4’s relationship guarantees remain intact: new romances are 76 Default / 63 Violent, with zero duplicate formations and at most two new romances for one person in either configuration. The preceding I4 sample had 74 / 70 and maxima 3 / 2. Emotion does not bypass relationship eligibility.

The final call baseline is **88.1 calls/day Default** (17 simulated days) and **69.8 Violent** (21 days), using seeds 11, 22 and 33. Both are below the historical 91.7 calls/day reference. The prior I4 measurement was 89.0 / 81.2. Changed trajectories and season lengths affect these averages; there is no added model-call site.

## Limits

All validation uses the mock backend or forced scenarios; no paid model calls were made. This is a deterministic appraisal layer for meaningful checked events, not a natural-language emotion detector. Shared voicing cannot expose a private cause, but only a real-model review can assess how naturally a model expresses it. I6’s general model reasoning and I7’s broader mock decision overhaul remain separate work.

Emotion changes alter later choices, survivors, evidence and season lengths. Matched seeds therefore describe resulting trajectories rather than isolating one emotional mechanism. Ending and escape settings are retained for the comparison; any survival-balance tuning remains a separate pass.
