# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 91.4 | 78.7 |
| Deaths per week | 3.4 | 4.1 |
| How the weeks ended | reckoning 1, still going 6, ultimatum 1 | raft 1, still going 6, ultimatum 1 |
| Deaths by cause | died in the Reckoning 8, murdered 7, wrongly executed 4, escaped the island 4, executed after the trial 2, was poisoned 1, killed 1 | murdered 12, executed after the trial 9, killed 4, wrongly executed 3, escaped the island 3, escaped on a raft 2 |
| Trials (all weeks) | 6 | 12 |
| Verdicts right / wrong / none | 2 / 4 / 0 | 9 / 3 / 0 |
| Average sanity of survivors at the end of the week | 60.3 | 61.4 |
| Median sanity at the end of each week | 51.0 / 71.0 / nobody left / 64.5 / 68 / 64.0 / 58.5 / 55.5 | 56.5 / 62.0 / 62 / 64.0 / 62 / 62 / 75.5 / nobody left |
| Aimless share of free-time activities | 0.36 | 0.32 |
| Meal attendance (share of the living) | 0.67 | 0.68 |
| Calm meals (share) | 0.52 | 0.59 |
| Night blocks where everyone sleeps (share) | 0.39 | 0.39 |
| People awake per night block | 1.35 | 1.25 |
| Exhausted at dawn (share of the living) | 0.07 | 0.08 |
| Beliefs per survivor at the end | 79.6 | 80.0 |
| False beliefs (share) | 0.001 | 0.0 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 8 / 0 |
| Secret meetings per week | 2.2 | 2.5 |
| Snooping per week / snoopers caught (all weeks) | 4.4 / 10 | 1.2 / 3 |
