# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 89.0 | 76.6 |
| Deaths per week | 2.8 | 4.4 |
| How the weeks ended | still going 8 | battle 1, rescue 1, still going 2, ultimatum 2, winners 2 |
| Deaths by cause | murdered 9, executed after the trial 4, wrongly executed 2, escaped the island 2, took their own life 2, escaped on a raft 2, was poisoned 1 | murdered 9, executed after the trial 8, killed 4, wrongly executed 4, escaped the island 4, escaped on a raft 2, died in the final battle 2, died of their injuries 2 |
| Trials (all weeks) | 6 | 12 |
| Verdicts right / wrong / none | 4 / 2 / 0 | 8 / 4 / 0 |
| Average sanity of survivors at the end of the week | 62.2 | 56.2 |
| Median sanity at the end of each week | 62 / 65.0 / 68.0 / 68 / 62.0 / 68 / 68 / 56.5 | 59.5 / 46 / 49 / 59.0 / 53 / 71 / 59 / 54.5 |
| Aimless share of free-time activities | 0.32 | 0.28 |
| Meal attendance (share of the living) | 0.67 | 0.67 |
| Calm meals (share) | 0.55 | 0.6 |
| Night blocks where everyone sleeps (share) | 0.36 | 0.34 |
| People awake per night block | 1.64 | 1.59 |
| Exhausted at dawn (share of the living) | 0.11 | 0.13 |
| Beliefs per survivor at the end | 80.0 | 79.9 |
| False beliefs (share) | 0.001 | 0.001 |
| Lies caught: real / honest people wrongly caught | 2 / 0 | 8 / 1 |
| Secret meetings per week | 2.8 | 2.2 |
| Snooping per week / snoopers caught (all weeks) | 3.6 / 3 | 2.9 / 2 |
