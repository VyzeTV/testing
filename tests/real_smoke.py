"""One real-AI turn (about 10 calls, a few cents of plan usage): checks that prompts build, replies parse and the new systems do not crash with the real models.
Run:  python tests/real_smoke.py      (uses the claude CLI; never touches your saves)"""
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_real_")

from murder.engine import DayRunner   # noqa: E402
from murder.llm import LLM            # noqa: E402
from murder.world import World, new_state   # noqa: E402

llm = LLM(backend="cli")
w = World(new_state(4, shuffle_rooms=True))
ticks = []
r = DayRunner(w, llm, ticks.append, step=2, murders=True, rule_mode="roulette", confessionals=False, seed=3)
r.ensure_wardrobe()
r.seed_belongings()
r.setup_rule()
t = r.run_tick(14, None)
errs = t["errors"]
print("calls:", llm.usage["calls"], "errors:", errs or "none")
print("rule:", (w.state["rule"] or {}).get("title"), (w.state["rule"] or {}).get("chk", {}).get("kind"))
print("actions:", {k: v for k, v in r.usage_summary().items() if k.startswith("action:")})
for cid in list(w.agents)[:2]:
    print("--- prompt extras for", cid)
    for ln in r.story_decision_lines(cid, 14)[-6:]:
        print("  ", ln[:160])
sys.exit(1 if any("fatal" in e.lower() for e in errs) else 0)
