"""One real-AI turn in a staged scene: someone unconscious, someone bleeding, a grudge. Shows whether the models use treat/wake/carry/rob/knockout.
Run:  python tests/real_body.py"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_realbody_")

from murder.engine import DayRunner   # noqa: E402
from murder.llm import LLM            # noqa: E402
from murder.world import World, new_state   # noqa: E402

llm = LLM(backend="cli")
w = World(new_state(4, shuffle_rooms=True))
ticks = []
r = DayRunner(w, llm, ticks.append, step=2, murders=True, rule_mode="none", confessionals=False, seed=5)
r.init_item_log()
r.ensure_wardrobe()
ids = list(w.agents)
a, b, c = ids[0], ids[1], ids[2]
for x in ids:
    w.agents[x]["room"] = "garden"
for x in (a, b, c):
    w.agents[x]["room"] = "bathroom"
tk = r.new_tick(14)
r.knock_out(tk, b, "knocked out", 4, by=c)
r.add_cond(tk, a, "bleeding", 2, "a cut", "arm")
r.add_cond(tk, a, "broken_arm", 1, "a blow", "arm")
w.agents[a]["aff"][c] = -6
w.agents[c]["aff"][a] = -6
t = r.run_tick(14, None)
print("calls:", llm.usage["calls"], "errors:", t["errors"] or "none")
for e in t.get("events", []):
    print(e["type"], "|", e.get("text", "")[:140])
print({k: v for k, v in r.usage_summary().items() if k.startswith("action:")})
for x in (a, c):
    print("---", x)
    for ln in r.story_decision_lines(x, 14)[-8:]:
        print("  ", ln[:200])
