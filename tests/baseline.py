"""Baseline metrics on mock weeks, the yardstick the rebuild's phase gates compare against.

Run:  python tests/baseline.py            (mock backend only; never touches your saves; a few minutes)
      python tests/baseline.py --write    (also writes docs/BASELINE.md)

Two configurations: the default mock cast, and a violent one where mock characters plot and attack now and then, so cases, trials and verdicts happen.
Model calls are counted for every kind of call the engine makes; the mock backend answers them, but a real backend would be asked the same number of times.
"""
import json
import os
import statistics
import sys
import tempfile
import time
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_baseline_")

from murder.engine import DayRunner          # noqa: E402
from murder.llm import LLM                   # noqa: E402
from murder.world import World, new_state    # noqa: E402

KINDS = ("decide", "converse", "voice", "react", "summarize", "host_json", "reflect", "adjudicate", "confess", "neovi_plan", "judge", "vote", "broadcast", "propose")
AIMLESS = {"look", "stay", "walk", "explore"}
SEEDS = (11, 22, 33)
DAYS = 7


class Counting(LLM):
    """The mock backend, counting each kind of call."""

    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.counts = Counter()


def _counted(kind):
    def call(self, *a, **k):
        self.counts[kind] += 1
        return getattr(LLM, kind)(self, *a, **k)
    return call


for _k in KINDS:
    setattr(Counting, _k, _counted(_k))


def run_week(seed, violent):
    LLM.mock_plot_prob = 0.04 if violent else 0.0
    LLM.mock_murder_prob = 0.02 if violent else 0.0
    w = World(new_state(3))
    out = {"days": 0, "calls": Counter(), "ticks": 0, "talk_groups": 0, "chats": 0, "free_blocks": 0, "segments": 0, "aimless": 0,
           "deaths": 0, "trials": 0, "verdict_right": 0, "verdict_wrong": 0, "verdict_none": 0, "sanity_median_end": None, "seconds": 0.0}
    for d in range(3, 3 + DAYS):
        if w.state.get("over") or not w.agents:
            break
        llm = Counting(backend="mock")
        ticks = []
        t0 = time.time()
        DayRunner(w, llm, lambda t: ticks.append(json.loads(json.dumps(t, default=str))), step=2, murders=True, rule_mode="roulette", seed=seed * 100 + d).run()
        out["seconds"] += time.time() - t0
        out["days"] += 1
        out["calls"] += llm.counts
        for t in ticks:
            out["ticks"] += 1
            out["talk_groups"] += len(t.get("talk") or [])
            if t.get("free"):
                out["free_blocks"] += 1
                out["chats"] += len(t.get("free_chats") or [])
                for segs in t["free"].values():
                    for sg in segs:
                        if sg.get("kind") == "main":
                            continue
                        out["segments"] += 1
                        out["aimless"] += sg.get("act") in AIMLESS
            tr = t.get("trial")
            if tr:
                out["trials"] += 1
                out["verdict_right"] += bool(tr.get("found"))
                out["verdict_wrong"] += bool(tr.get("wrongful"))
                out["verdict_none"] += not tr.get("found") and not tr.get("wrongful")
    out["deaths"] = len(w.state.get("graveyard", []))
    san = [a["sanity"] for a in w.agents.values()]
    out["sanity_median_end"] = statistics.median(san) if san else None
    return out


def summarize(label, weeks):
    days = sum(x["days"] for x in weeks)
    calls = sum((x["calls"] for x in weeks), Counter())
    fb = sum(x["free_blocks"] for x in weeks)
    segs = sum(x["segments"] for x in weeks)
    return {
        "label": label, "weeks": len(weeks), "days": days,
        "calls_per_day": round(sum(calls.values()) / max(1, days), 1),
        "calls_by_kind_per_day": {k: round(v / max(1, days), 1) for k, v in sorted(calls.items(), key=lambda kv: -kv[1])},
        "talk_groups_per_day": round(sum(x["talk_groups"] for x in weeks) / max(1, days), 1),
        "chats_per_free_block": round(sum(x["chats"] for x in weeks) / max(1, fb), 2),
        "aimless_share": round(sum(x["aimless"] for x in weeks) / max(1, segs), 2),
        "deaths_per_week": round(sum(x["deaths"] for x in weeks) / len(weeks), 1),
        "trials": sum(x["trials"] for x in weeks),
        "verdicts": {"right": sum(x["verdict_right"] for x in weeks), "wrong": sum(x["verdict_wrong"] for x in weeks), "none": sum(x["verdict_none"] for x in weeks)},
        "sanity_median_end": [x["sanity_median_end"] for x in weeks],
        "seconds_per_day": round(sum(x["seconds"] for x in weeks) / max(1, days), 1),
    }


def markdown(results):
    rows = [("Model calls per day", "calls_per_day"), ("Conversation groups per day", "talk_groups_per_day"), ("Chats per free block", "chats_per_free_block"),
            ("Aimless share of free-time activities", "aimless_share"), ("Deaths per week", "deaths_per_week"), ("Trials (all weeks)", "trials"),
            ("Verdicts right / wrong / none", "verdicts"), ("Median sanity at the end of each week", "sanity_median_end"), ("Engine seconds per day (mock)", "seconds_per_day")]
    head = "| Metric | " + " | ".join(r["label"] for r in results) + " |\n| --- | " + " | ".join("---" for _ in results) + " |\n"
    body = ""
    for name, key in rows:
        vals = []
        for r in results:
            v = r[key]
            vals.append(f"{v['right']} / {v['wrong']} / {v['none']}" if key == "verdicts" else ", ".join("nobody left" if x is None else str(x) for x in v) if isinstance(v, list) else str(v))
        body += f"| {name} | " + " | ".join(vals) + " |\n"
    kinds = "\n".join(f"- **{r['label']}:** " + ", ".join(f"{k} {v}" for k, v in r["calls_by_kind_per_day"].items()) for r in results)
    return ("# Baseline metrics\n\n"
            f"Mock weeks before the rebuild, the yardstick for its phase gates. {len(SEEDS)} weeks of {DAYS} days per configuration (seeds {', '.join(map(str, SEEDS))}), "
            "default tuning. Regenerate with `python tests/baseline.py --write`.\n\n"
            "The mock backend answers every model call, so call counts are what a real backend would be asked; the content of mock answers is scripted, "
            "so drama metrics (deaths, verdicts) only show that the machinery runs. Deaths include the deadline reckoning, which kills everyone when nobody has died by the deadline.\n\n" + head + body + "\n## Model calls per day, by kind\n\n" + kinds + "\n")


if __name__ == "__main__":
    results = []
    for label, violent in (("Default", False), ("Violent mock cast", True)):
        weeks = [run_week(s, violent) for s in SEEDS]
        results.append(summarize(label, weeks))
        print(json.dumps(results[-1], indent=1))
    if "--write" in sys.argv:
        path = os.path.join(ROOT, "docs", "BASELINE.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(markdown(results))
        print("wrote", path)
