# Balance numbers

How the game plays on mock weeks: 8 weeks of up to 7 days per configuration (seeds 11, 22, 33, 44, 55, 66, 77, 88), default tuning. Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.

The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day (`python tests/real_day.py`, about 90 model calls).

| Metric | Default | Violent mock cast |
| --- | --- | --- |
| Model calls per day | 89.8 | 81.3 |
| Deaths per week | 3.4 | 4.0 |
| How the weeks ended | battle 1, reckoning 1, still going 6 | still going 7, winners 1 |
| Deaths by cause | died in the Reckoning 8, executed after the trial 5, killed 4, murdered 4, escaped the island 3, died in the final battle 2, wrongly executed 1 | murdered 12, executed after the trial 8, killed 5, escaped the island 4, wrongly executed 2, died of their injuries 1 |
| Trials (all weeks) | 8 | 12 |
| Verdicts right / wrong / none | 5 / 1 / 2 | 8 / 2 / 2 |
| Average sanity of survivors at the end of the week | 62.6 | 57.6 |
| Median sanity at the end of each week | 65.0 / 64.0 / 68.0 / nobody left / 61 / 68.0 / 64.0 / 61.0 | 59.0 / 65.0 / 46.0 / 68.0 / 65.0 / 50 / 64.0 / 60 |
| Aimless share of free-time activities | 0.17 | 0.17 |
| Meal attendance (share of the living) | 0.64 | 0.68 |
| Calm meals (share) | 0.55 | 0.62 |
| Night blocks where everyone sleeps (share) | 0.37 | 0.42 |
| People awake per night block | 1.55 | 1.25 |
| Exhausted at dawn (share of the living) | 0.09 | 0.11 |
| Beliefs per survivor at the end | 80.0 | 80.0 |
| False beliefs (share) | 0.0 | 0.0 |
| Lies caught: real / honest people wrongly caught | 1 / 0 | 11 / 0 |
| Secret meetings per week | 2.0 | 2.0 |
| Snooping per week / snoopers caught (all weeks) | 5.9 / 7 | 3.8 / 4 |
