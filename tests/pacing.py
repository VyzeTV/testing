"""Dead air per block: how many of a block's 24 five-minute stretches have no walking, no talk and no events, on mock days.
Run:  python tests/pacing.py [--days N]     (mock backend, about a minute)"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))

from murder.engine import DayRunner              # noqa: E402
from murder.llm import LLM                       # noqa: E402
from murder.world import World, new_state        # noqa: E402

STRETCH = 5


def dead_stretches(live):
    """Count the five-minute stretches of a block in which nothing at all happens."""
    n = int(live["dur"] // STRETCH)
    busy = [False] * n
    mark = lambda m: busy.__setitem__(min(n - 1, max(0, int(m // STRETCH))), True)
    for tr in live["tracks"].values():
        for a, b in zip(tr, tr[1:]):
            if a[1:] != b[1:]:
                for k in range(int(a[0] // STRETCH), int(b[0] // STRETCH) + 1):
                    if k < n:
                        busy[k] = True
    for x in live.get("talk") or []:
        mark(x["m"])
    for e in live.get("events") or []:
        if e.get("m") is not None:
            mark(e["m"])
    return busy.count(False)


def measure(seeds=(5, 6, 7), days=(3, 4)):
    per = {}
    for seed in seeds:
        w = World(new_state(days[0]))
        ticks = []
        for d in days:
            w.state["day"] = d
            DayRunner(w, LLM(backend="mock"), ticks.append, step=2, murders=False, rule_mode="roulette", seed=seed * 10 + d).run()
        for t in ticks:
            h = t["hour"]
            if 8 <= h <= 20 and t.get("live") and t.get("type") in (None, "turn"):
                per.setdefault(h, []).append(dead_stretches(t["live"]))
    return {h: round(sum(v) / len(v), 1) for h, v in sorted(per.items())}


if __name__ == "__main__":
    res = measure()
    for h, v in res.items():
        print(f"{h:02d}:00  dead stretches {v:4.1f} of 24")
