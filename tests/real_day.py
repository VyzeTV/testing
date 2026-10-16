"""One full real-AI day with a few injuries and a collapsed person seeded at the start, then a summary of what the models did with the body mechanics.
Run:  python tests/real_day.py      (uses the claude CLI, roughly 90+ calls; never touches your saves)"""
import collections
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_realday_")

from murder.engine import DayRunner   # noqa: E402
from murder.llm import LLM            # noqa: E402
from murder.world import World, new_state   # noqa: E402

llm = LLM(backend="cli")
w = World(new_state(3, shuffle_rooms=True))
ticks = []
r = DayRunner(w, llm, ticks.append, step=2, murders=True, rule_mode="roulette", confessionals=False, seed=11)
ids = list(w.agents)
orig = r.condition_tick
seeded = []


def seeded_tick(tick, hour):
    if not seeded and hour >= 10:
        seeded.append(1)
        a, b, c = ids[0], ids[1], ids[2]
        r.add_cond(tick, a, "bleeding", 2, "a fall on the stairs")
        r.add_cond(tick, b, "broken_leg", 1, "a fall", "leg")
        w.agents[c]["room"] = w.agents[ids[3]]["room"]
        r.knock_out(tick, c, "knocked out", 3, by=ids[3])
    return orig(tick, hour)


r.condition_tick = seeded_tick
try:
    r.run()
except Exception as e:  # noqa: BLE001
    print("RUN FAILED:", repr(e))
cnt = collections.Counter(e["type"] for t in ticks for e in t.get("events", []))
print("calls:", llm.usage["calls"], "errors:", sum(len(t.get("errors", [])) for t in ticks))
print({k: cnt[k] for k in ("condition", "faint", "treat", "carry", "rob", "frame", "attack", "friction") if cnt[k]})
print({k: v for k, v in r.usage_summary().items() if k.split(":")[-1] in ("treat", "wake", "knockout", "carry", "rob", "stage", "seek_care")})
for t in ticks:
    for e in t.get("events", []):
        if e["type"] in ("treat", "carry", "rob", "frame", "faint") and "comes round" not in e.get("text", ""):
            print(t.get("time"), e["type"], "|", e.get("text", "")[:130])
