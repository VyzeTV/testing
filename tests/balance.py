"""Balance numbers on mock weeks: how the game plays, not only whether it runs. Every phase gate from phase 5 on reports these.
Run:  python tests/balance.py            (mock backend only; never touches your saves; about a minute)
      python tests/balance.py --write    (also writes docs/BALANCE.md)
Two configurations, as in baseline.py: the default mock cast, and a violent one where mock characters plot and attack now and then.
The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave (meals, nights, beliefs,
the deadline); story quality needs a real-model day.
"""
import json
import os
import statistics
import sys
import tempfile
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_balance_")

from baseline import Counting, AIMLESS        # noqa: E402
from murder.engine import DayRunner          # noqa: E402
from murder.llm import LLM                   # noqa: E402
from murder.world import World, new_state    # noqa: E402

SEEDS = (11, 22, 33, 44)
DAYS = 7


def run_week(seed, violent):
    LLM.mock_plot_prob = 0.04 if violent else 0.0
    LLM.mock_murder_prob = 0.02 if violent else 0.0
    w = World(new_state(3))
    o = Counter()
    for d in range(3, 3 + DAYS):
        if w.state.get("over") or not w.agents:
            break
        llm = Counting(backend="mock")
        ticks = []
        DayRunner(w, llm, lambda t: ticks.append(json.loads(json.dumps(t, default=str))), step=2, murders=True, rule_mode="roulette", seed=seed * 100 + d).run()
        o["days"] += 1
        o["calls"] += sum(llm.counts.values())
        for t in ticks:
            for segs in (t.get("free") or {}).values() if t.get("phase") != "night" else []:
                for sg in segs:
                    if sg.get("kind") != "main":
                        o["segments"] += 1
                        o["aimless"] += sg.get("act") in AIMLESS
            m = t.get("meal")
            if m:
                o["meals"] += 1
                o["meal_seats"] += len(m["came"])
                o["meal_people"] += len(m["came"]) + len(m["skipped"])
                o["meals_calm"] += bool(m.get("calm"))
            if t.get("phase") == "night" and t["hour"] in (23, 25, 27, 29):
                o["night_blocks"] += 1
                o["night_quiet"] += bool(t.get("quiet"))
                o["night_awake"] += len(t.get("awake") or [])
            if t.get("phase") == "night" and t["hour"] == 31:
                for a in (t.get("state") or {}).get("agents", {}).values():
                    if a.get("status", "alive") == "alive":
                        o["dawn_people"] += 1
                        o["dawn_exhausted"] += any(c.get("id") == "exhausted" for c in a.get("conds") or [])
            tr = t.get("trial")
            if tr:
                o["trials"] += 1
                o["right"] += bool(tr.get("found"))
                o["wrong"] += bool(tr.get("wrongful"))
    o["deaths"] = len(w.state.get("graveyard", []))
    for g in w.state.get("graveyard", []):
        o["how:" + str(g.get("how") or g.get("status"))[:30]] += 1
    over = (w.state.get("over") or {}).get("kind")
    o["end:" + (over or "still going")] += 1
    for a in w.agents.values():
        bs = a.get("beliefs") or []
        o["believers"] += 1
        o["beliefs"] += len(bs)
        o["beliefs_false"] += sum(1 for b in bs if not b.get("true", True))
    lies = w.state.get("lies_caught") or []
    o["lies_real"] += sum(1 for x in lies if x.get("true_lie"))
    o["lies_false"] += sum(1 for x in lies if not x.get("true_lie"))
    san = [a["sanity"] for a in w.agents.values()]
    o["san_sum"], o["san_n"] = sum(san), len(san)
    return o, (statistics.median(san) if san else None)


def summarize(label, weeks):
    t = sum((x for x, _ in weeks), Counter())
    n = len(weeks)
    r = lambda a, b, k=2: round(t[a] / max(1, t[b]), k)
    return {
        "label": label, "weeks": n, "days": t["days"],
        "calls_per_day": r("calls", "days", 1),
        "deaths_per_week": round(t["deaths"] / n, 1),
        "how_weeks_ended": {k[4:]: v for k, v in sorted(t.items()) if k.startswith("end:")},
        "deaths_by_cause": {k[4:]: v for k, v in sorted(t.items(), key=lambda kv: -kv[1]) if k.startswith("how:")},
        "trials": t["trials"], "verdicts_right_wrong_none": [t["right"], t["wrong"], t["trials"] - t["right"] - t["wrong"]],
        "sanity_median_end": [s for _, s in weeks],
        "sanity_mean_end": round(statistics.mean([x["san_sum"] / x["san_n"] for x, _ in weeks if x["san_n"]]), 1) if any(x["san_n"] for x, _ in weeks) else None,
        "aimless_share": r("aimless", "segments"),
        "meal_attendance": r("meal_seats", "meal_people"),
        "calm_meal_share": r("meals_calm", "meals"),
        "quiet_night_share": r("night_quiet", "night_blocks"),
        "awake_per_night_block": r("night_awake", "night_blocks"),
        "exhausted_at_dawn": r("dawn_exhausted", "dawn_people"),
        "beliefs_per_survivor": r("beliefs", "believers", 1),
        "false_belief_share": r("beliefs_false", "beliefs", 3),
        "lies_caught_real_false": [t["lies_real"], t["lies_false"]],
    }


ROWS = [("Model calls per day", "calls_per_day"), ("Deaths per week", "deaths_per_week"), ("How the weeks ended", "how_weeks_ended"),
        ("Deaths by cause", "deaths_by_cause"), ("Trials (all weeks)", "trials"), ("Verdicts right / wrong / none", "verdicts_right_wrong_none"),
        ("Average sanity of survivors at the end of the week", "sanity_mean_end"), ("Median sanity at the end of each week", "sanity_median_end"), ("Aimless share of free-time activities", "aimless_share"),
        ("Meal attendance (share of the living)", "meal_attendance"), ("Calm meals (share)", "calm_meal_share"),
        ("Night blocks where everyone sleeps (share)", "quiet_night_share"), ("People awake per night block", "awake_per_night_block"),
        ("Exhausted at dawn (share of the living)", "exhausted_at_dawn"), ("Beliefs per survivor at the end", "beliefs_per_survivor"),
        ("False beliefs (share)", "false_belief_share"), ("Lies caught: real / honest people wrongly caught", "lies_caught_real_false")]


def fmt(v):
    if isinstance(v, dict):
        return ", ".join(f"{k} {x}" for k, x in v.items()) or "none"
    if isinstance(v, list):
        return " / ".join("nobody left" if x is None else str(x) for x in v)
    return str(v)


def markdown(results):
    head = "| Metric | " + " | ".join(r["label"] for r in results) + " |\n| --- | " + " | ".join("---" for _ in results) + " |\n"
    body = "".join(f"| {name} | " + " | ".join(fmt(r[key]) for r in results) + " |\n" for name, key in ROWS)
    return ("# Balance numbers\n\n"
            f"How the game plays on mock weeks: {len(SEEDS)} weeks of up to {DAYS} days per configuration (seeds {', '.join(map(str, SEEDS))}), default tuning. "
            "Regenerate with `python tests/balance.py --write`; every phase gate from phase 5 on reports these. `docs/BASELINE.md` is the pre-rebuild yardstick for model calls.\n\n"
            "The mock backend scripts what characters say and decide, so these numbers show how the engine's own systems behave. Story quality needs a real-model day "
            "(`python tests/real_day.py`, about 90 model calls).\n\n" + head + body)


if __name__ == "__main__":
    results = []
    for label, violent in (("Default", False), ("Violent mock cast", True)):
        results.append(summarize(label, [run_week(s, violent) for s in SEEDS]))
        print(json.dumps(results[-1], indent=1))
    if "--write" in sys.argv:
        with open(os.path.join(ROOT, "docs", "BALANCE.md"), "w", encoding="utf-8") as f:
            f.write(markdown(results))
