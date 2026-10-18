# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 84.0 | 82.3 |
| Deaths per week | 3.0 | 3.5 |
| How the weeks ended | still going 7, winners 1 | battle 1, still going 6, ultimatum 1 |
| Deaths by cause | murdered 9, executed after the trial 6, wrongly executed 3, escaped the island 3, escaped on a raft 2, died in an accident 1 | murdered 11, executed after the trial 8, wrongly executed 2, escaped the island 2, escaped on a raft 2, died in the final battle 1, died in an accident 1, killed 1 |
| Trials (all weeks) | 9 | 10 |
| Verdicts right / wrong / none | 6 / 3 / 0 | 8 / 2 / 0 |
| Average sanity of survivors at the end of the week | 61.0 | 60.8 |
| Median sanity at the end of each week | 61.0 / 68.0 / 68 / 44.0 / 64.0 / 67 / 67.0 / 68 | 62 / 67.0 / 65 / 60 / 70.0 / 63.0 / 51 / 65.0 |
| Aimless share of free-time activities | 0.32 | 0.3 |
| Meal attendance (share of the living) | 0.68 | 0.66 |
| Calm meals (share) | 0.65 | 0.61 |
| Night blocks where everyone sleeps (share) | 0.48 | 0.28 |
| People awake per night block | 1.42 | 1.85 |
| Exhausted at dawn (share of the living) | 0.11 | 0.16 |
| Beliefs per survivor at the end | 78.6 | 79.7 |
| False beliefs (share) | 0.001 | 0.001 |
| Lies caught: real / honest people wrongly caught | 0 / 0 | 2 / 0 |
| Secret meetings per week | 2.8 | 2.4 |
| Snooping per week / snoopers caught (all weeks) | 3.5 / 5 | 3.0 / 1 |
