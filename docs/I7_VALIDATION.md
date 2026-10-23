# I7: a mock that behaves like people

Implemented on 2026-10-22. `murder/mock_policy.py` owns the offline character policy and its context adapter; `llm.py` retains model transport. The engine still composes 81 mixins.

## Behavior

Non-routine decisions now weigh facets, needs, relationships, lasting feelings and commitments. Sociable or lonely people seek company; attraction favors the relevant person; fear discourages approaching its target; grief discourages visiting its known place. Curious people favor investigation and offered escape work. Ordinary social choices yield to recovery and due obligations. Existing plots remain with the checked planner rather than acquiring a new victim, stage or incidental attack from the mock.

Reactions weigh kindness, courage, distress, known hostility and protection promises. A kind protector is more likely to help someone hurt; a fearful person is more likely to flee. Nightly goal changes require a strong known feeling that supports the new drive and retain existing commitments. Diaries name the same known emotion and cause. Staged conversation effects reflect participants' feelings, with no random friendly-to-hostile affinity swing or fabricated hearsay. Normal plan proposals select checked offers; invalid schemes, rooms, items and verbs remain explicit regression fixtures.

Character contexts exclude remote positions and other people's private feelings. Blindness, blackouts, hidden people, sleeping people and uncertain disguises restrict immediate targets. Shared scene profiles exclude private causes, obligations, drives and plans. Context building does not roll disguise recognition. Policy queries do not mutate the snapshot; save/load retains the information used to choose. All sampling uses the existing per-prompt seeded generator, with stable option ordering. Real-model prompts and call sites are unchanged.

## Verification

```sh
python tools/check.py --browser --metrics
python tests/mock_metrics.py --output /tmp/i7-days.json
python tests/mock_metrics.py --brain --output /tmp/i7-brain-days.json
python tests/relationship_seasons.py --seeds 40 --output /tmp/i7-seasons.json
```

The offline smoke suite passes **1,189/1,189**, including seeded day and Python hash-seed determinism, duplicate mixin methods and unchanged early prompt preparation. Focused suites pass **226 tests**, including **28 new mock checks**. These use repeated matched random samples to test behavioral differences, plus forced checks for promise priority, host timing, existing plots, medical needs, private rooms, invisible targets, reactions, goal continuity, checked proposals, save/load, read-only snapshots and reversed parallel call/option order.

Chromium checks pass for randomized casting, diagnostics and copying, emotion details/privacy, and viewer playback. The viewer completes generation without errors or a frozen clock during conversations. Its sampled day had no quiet night block, so that conditional skip branch was not exercised in this run.

The new checks are included in `python tools/check.py`. `--metrics` also includes `mock_metrics.py`. Browser checks used isolated scratch servers. All runs used the free backend; no paid AI calls were made.

The final smoke pass initially reported 160 changed past positions in seed 909. A focused trace showed every mismatch came from a closed Sim (`forward=False`) during a finale transition, while the test labeled it with the previous block's hour. The check now snapshots only open forward blocks, retaining its minimum coverage assertion and comparisons of past positions. No playback or engine positioning behavior was changed to address this false positive.

## Short runs and archived real-model observations

Six matching starts use seeds 11, 22 and 33 in Default and Violent configurations, from Day 1 for up to five days. The pre-change report was captured before changing the mock. Default tuning leaves the optional brain dial off. Runs stop at an ending, so the after sample contains 27 days rather than 30; rates use each sample's actual decision count.

| Measurement | Before | After |
| --- | ---: | ---: |
| Model decision opportunities | 1,457 | 1,241 |
| Mock-declared plots / decision | 0.75% | 0.32% |
| Mock attacks / decision | 0.27% | 0.40% |
| Hosting proposals / decision | 6.11% | 2.26% |
| Experiments / decision | 5.15% | 5.16% |
| Explicit talk intentions / decision | 0% | 6.45% |
| Escape contributors per run | 7, 6, 8, 8, 6, 7 | 8, 8, 8, 8, 8, 8 |
| Distinct cast speakers per run | 8 in all six | 8 in all six |
| Engine errors | 0 | 0 |

After the change, **33 of 115 live conversations (28.7%)** gain a joiner. This field was added to the report after the before capture, so there is no matching before rate. The design notes' older mock reference is about one conversation in six.

The optional brain sample completes all 30 days without errors: 1,503 decisions, 88 talk intentions, 72 work intentions, 73 experiments, 15 hosting proposals, nine mock-declared plots and three mock attacks. Escape contributors number 7–8 per run; all eight cast members speak. **57 of 134 conversations (42.5%)** gain a joiner. This is a supplementary configuration, not a before/after result.

The archived five-day real-model season in `NEXT_STEPS.md` reports **all eight helping with escape**, one plotter and no completed murder. The after sample reproduces broad escape participation. Its Default runs have 0–2 plotters, counting engine-started plots as well as mock declarations; Violent runs each have two. The brain sample's Default runs have 1–2 plotters; Violent runs have 1–5. These are qualitative comparisons: the real season used a five-day week, while this report uses default week length and earlier endings. The archived real day in `REAL_RUN.md` demonstrates purposeful company seeking and supportive interaction but does not provide a measured conversation-join rate. No new real-model run or statistical calibration is claimed.

## Whole-season continuity and balance

The same seeds 1–40 in both configurations were compared with I3's verified reference. All **80 seasons finish**, with **532,257 story checks and zero violations**, including zero duplicate romance formations. New romances number 62 in Default and 64 in Violent; the maximum per person is two in either configuration.

| Sample | Good | Bittersweet | Bad |
| --- | ---: | ---: | ---: |
| I3 reference, 80 seasons | 25 | 33 | 22 |
| I7 Default, 40 seasons | 17 | 13 | 10 |
| I7 Violent, 40 seasons | 25 | 8 | 7 |
| I7 combined | **42** | **21** | **17** |

The larger good-ending share accompanies more consistent participation and different survival paths. It exceeds the historical 40% target and warrants a separate balance pass. No escape rates, ending costs, lethality settings or romance gates were tuned to produce these results. The configurations are stress-test profiles, not a guarantee that Violent must always end worse.

The call baseline reports **72.2 calls/day in Default (12 days)** and **76.9 in Violent (15 days)**, from seeds 11, 22 and 33. I3 reported 88.1 / 69.8 and the historical yardstick is 91.7. The Violent increase remains below that yardstick; changed choices, early endings and surviving casts change the number and kind of calls. No new call sites were introduced, and these descriptive rates do not estimate real-model token usage.

## Limits

This is an interpretable offline policy, not a replacement for a language model. Wording, host/NPC/rule stubs, experimental rulings and the trial accuracy test knob remain scripted. Character contexts do not receive the true killer; the existing trial fixture's killer knob remains available for controlled tests. Seed-finder choices and old mock recordings will differ because the policy changed, while repeatability within this version remains covered. I6's stored model reasons and the remaining I8 preparation/cover-up work are still pending.
