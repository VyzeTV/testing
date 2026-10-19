# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 89.4 | 76.4 |
| Deaths per week | 2.6 | 3.5 |
| How the weeks ended | still going 8 | battle 1, shutdown 1, still going 5, ultimatum 1 |
| Deaths by cause | executed after the trial 7, murdered 5, killed 3, was poisoned 2, escaped on a raft 2, wrongly executed 1, escaped the island 1 | executed after the trial 10, murdered 9, killed 3, wrongly executed 2, escaped the island 2, died in the final battle 2 |
| Trials (all weeks) | 8 | 12 |
| Verdicts right / wrong / none | 7 / 1 / 0 | 10 / 2 / 0 |
| Average sanity of survivors at the end of the week | 61.6 | 60.7 |
| Median sanity at the end of each week | 61.0 / 68 / 68 / 66 / 64.0 / 60 / 67.5 / 68.0 | 74.5 / 55.5 / 60 / 59.5 / 68.0 / 70.5 / 65.0 / 49 |
| Aimless share of free-time activities | 0.31 | 0.26 |
| Meal attendance (share of the living) | 0.67 | 0.66 |
| Calm meals (share) | 0.51 | 0.58 |
| Night blocks where everyone sleeps (share) | 0.27 | 0.3 |
| People awake per night block | 1.92 | 1.71 |
| Exhausted at dawn (share of the living) | 0.15 | 0.15 |
| Beliefs per survivor at the end | 78.5 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 5 / 0 | 5 / 0 |
| Secret meetings per week | 3.4 | 1.5 |
| Snooping per week / snoopers caught (all weeks) | 3.9 / 4 | 3.1 / 4 |
