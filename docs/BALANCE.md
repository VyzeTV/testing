# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 89.9 | 75.5 |
| Deaths per week | 3.8 | 3.6 |
| How the weeks ended | battle 1, sole 1, still going 6 | shutdown 2, still going 4, ultimatum 1, winners 1 |
| Deaths by cause | escaped on a raft 7, murdered 6, executed after the trial 5, wrongly executed 2, escaped the island 2, killed 2, died in an accident 2, executed by TereVi's whim 2, died in the final battle 2 | murdered 11, executed after the trial 9, killed 4, escaped the island 3, wrongly executed 2 |
| Trials (all weeks) | 7 | 12 |
| Verdicts right / wrong / none | 5 / 2 / 0 | 9 / 2 / 1 |
| Average sanity of survivors at the end of the week | 59.6 | 60.1 |
| Median sanity at the end of each week | 68.0 / 63.0 / 68 / 59.5 / 68 / 39 / 57.0 / 75 | 60.5 / 50 / 61 / 65.0 / 75 / 56 / 55 / 70.5 |
| Aimless share of free-time activities | 0.33 | 0.26 |
| Meal attendance (share of the living) | 0.69 | 0.64 |
| Calm meals (share) | 0.5 | 0.6 |
| Night blocks where everyone sleeps (share) | 0.38 | 0.31 |
| People awake per night block | 1.69 | 1.64 |
| Exhausted at dawn (share of the living) | 0.1 | 0.17 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.001 |
| Lies caught: real / honest people wrongly caught | 4 / 0 | 3 / 0 |
| Secret meetings per week | 1.9 | 1.8 |
| Snooping per week / snoopers caught (all weeks) | 2.4 / 2 | 2.6 / 2 |
