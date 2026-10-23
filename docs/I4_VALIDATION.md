# I4: relationships with inertia

Implemented on 2026-10-22 in `murder/relationships.py` and adapters in the existing engine modules. The runner still composes 81 mixins.

## Behavior

Romance requires mutual affection of at least 7, directional trust of at least 2, and welcomed encounters on three separate days spanning 48 hours within the preceding week. Ordinary welcomed social moves, mutually warm staged scenes and intimate moments can build shared history. Unrelated affinity bonuses and private reflection do not invent encounters. Existing romances in old saves remain valid.

Trust is separate from affection and the character's trust facet. It grows at most once per relationship per game day; encounters and reflection share that budget. Negative affinity changes reduce trust immediately. Betrayal sharply reduces the victim's trust, clears their recent closeness, and records a named memory for 21 days. Repair gains only a quarter point per day during that period. Wariness affects receptivity, confiding, grounds for suspicion and eligibility for positive bonds. A diary cannot declare the betrayal forgotten. New betrayals invalidate the affected person's prefetched decision.

Current partners prevent an unacknowledged second romance. Affairs remain possible through the existing night system. Both betrayed partners are tracked when both people have partners; each discovery applies its consequences once. NeoVi follows the progression gate and can discover an affair. Becoming participant Kumiko preserves her trust, history, partner and romance age.

Private decisions and diaries include remembered reasons. Shared voicing cards communicate guarded attitudes without exposing the private incident. Bond history carries sequence IDs; the story checker detects a repeated romance formation without an intervening ending.

## Validation

Forced regressions are in `tests/relationship_check.py` and run with `python tools/check.py`. Browser and simulation reports run with `python tools/check.py --browser --metrics`.

The season comparison uses seeds 1–40 for each of the default and violent configurations, starting on Day 1 and using the standard newcomer/ending settings. `tests/relationship_seasons.py` wraps bond recording to count all new romance formations, including ones that later ended; this is not the number of romances remaining at the ending. NeoVi and participant Kumiko count as one person. Reproduce a current sample with:

```bash
python tests/relationship_seasons.py --seeds 40 --output /tmp/i4-seasons.json
```

Core checks pass: **1,189/1,189 smoke assertions** and **162 focused Python tests**, including 26 I4 regressions. JavaScript syntax/escaping and Chromium casting, diagnostics and continuous playback checks pass. The browser run finished the day, reported zero script errors or frozen conversation samples, and successfully skipped a quiet-night block. The final checks also cover NeoVi’s identity transition; that final change has no viewer-code changes.

Across the matched 80-season samples:

| Configuration | New romances before | New romances after | Highest count for one person before → after |
| --- | ---: | ---: | ---: |
| Default, 40 seasons | 149 | 74 | 6 → 3 |
| Violent, 40 seasons | 101 | 70 | 4 → 2 |
| Total | 250 | 144 | |

New romance formations fell **42.4% overall**. The final sample performed **708,176 story checks with zero violations** and **zero duplicate romance formations without an ending**. The baseline sample also had zero duplicate formations; I4 preserves that existing guarantee while reducing churn.

The current call baseline is **89.0 calls/day default** (21 simulated days) and **81.2 violent** (18 days), using seeds 11, 22 and 33. Both are below the historical 91.7 calls/day reference, but above the preceding I2 snapshot of 81.4 / 75.4. No model-call site was added. Different survivors and season lengths, plus invalidating decisions after a betrayal, affect usage.

**Balance follow-up:** the full-season ending mix moved from 36 good / 24 bittersweet / 20 bad to **20 good / 26 bittersweet / 34 bad**. Default has 11 good / 11 bittersweet / 18 bad; violent has 9 / 15 / 16. Relationship changes affect social support and later choices; these measurements do not isolate which mechanism caused the ending shift. Keep ending and escape tuning as a separate pass, and recheck after I3. No ending or escape settings were changed to hide the shift.

The perception smoke check was corrected to honor recorded burned/broken doors when checking line of sight. It still rejects observations blocked by intact structure.

## Limits

All checks use the mock backend or forced scenarios; no paid model calls were made. The same seeds do not guarantee the same later survivors, cases or season lengths after relationship choices change. Ending and verdict comparisons describe the resulting trajectories. Lasting emotions (I3) and general model decision reasoning (I6) remain separate work.
