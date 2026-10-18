# Who kills and who dies

Per-character counts over 80 mock weeks (seeds 101-140, the default and the violent mock cast of `tests/balance.py`). For curiosity, not a gate. Regenerate with `python tests/cast_stats.py --write` (a few minutes).

135 deaths opened a case: murder 114, manslaughter 19, suicide 1, accident 1. 101 reached a trial: 75 right verdicts, 24 wrong, 2 with no verdict.

| Character | Victim | Killer (murder + manslaughter) | Caught at trial | Got away at trial | Executed in someone else's place |
| --- | --- | --- | --- | --- | --- |
| Ayden | 6 | 25 (21 + 4) | 14 | 3 | 2 |
| Szymon | 14 | 23 (21 + 2) | 10 | 2 | 0 |
| Cail | 21 | 19 (16 + 3) | 10 | 3 | 5 |
| Noah | 16 | 17 (15 + 2) | 11 | 6 | 10 |
| Vixen | 20 | 16 (15 + 1) | 6 | 6 | 3 |
| Seul | 27 | 14 (11 + 3) | 13 | 0 | 1 |
| Shintaro | 17 | 14 (12 + 2) | 7 | 6 | 1 |
| Chloe | 14 | 5 (3 + 2) | 4 | 0 | 2 |

"Got away at trial" means a wrong verdict or none, so the killer survived. Killings that never reached a trial (the mock week ended before the trial, or the killing happened during a frenzy, which has no trial) count only as kills.

Most frequent pairs: Szymon killing Vixen (7), Ayden killing Seul (6), Cail killing Shintaro (6), Shintaro killing Noah (5), Ayden killing Szymon (5).

## Notes on this run (2026-10-18, after phase 7)

These notes are written by hand and are not regenerated.

- Ayden kills the most and dies the least. He has one of the highest cruelty scores (67) and starts as the best liked (+11 from the others combined), so few turn on him.
- Seul dies the most. She starts as the least liked (+2 from the others combined).
- Chloe rarely kills: she has the lowest cruelty score (47), which fits her timid personality.
- Noah is executed in someone else's place 10 times, more than anyone. He is tall with short blond hair, so he often matches the same traces as Szymon.
- Vixen and Shintaro get away at trial most often for the number of their kills.
- Of the 133 killings with a culprit, 101 reached a trial, 19 were still being investigated when the mock week ended, and 13 happened during a killing frenzy.
- 18 of the 19 manslaughters were self-defence: the person attacked killed their attacker.
