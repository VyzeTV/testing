"""Mock days with the brain dial off and on: model decisions vs engine decisions, plans made and carried out, memory sizes, chats.
Run:  python tests/brain_compare.py [days]      (mock backend only; never touches your saves)"""
import collections
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_brain_")

from murder.engine import DayRunner   # noqa: E402
from murder.llm import LLM            # noqa: E402
from murder.world import World, new_state   # noqa: E402

days = int(sys.argv[1]) if len(sys.argv) > 1 else 3
for brain in (0, 1):
    w = World(new_state(3))
    ticks = []
    model = engine = plans = done = 0
    for d in range(3, 3 + days):
        w.state["day"] = d
        r = DayRunner(w, LLM(backend="mock"), ticks.append, step=2, murders=True, rule_mode="none", confessionals=False, seed=7 + d)
        r.tuning_get = lambda: {"brain": brain}
        r.run()
        t = w.state.get("telemetry", {}).get(str(d), {}).get("decision", {})
        model += t.get("model", 0)
        engine += t.get("engine", 0)
        if w.state.get("over"):
            break
    bs = w.state.get("brain_stats", {})
    plans = sum(v["made"] for v in bs.values())
    done = sum(v["done"] for v in bs.values())
    acts = collections.Counter(sg["act"] for t in ticks for sgs in (t.get("free") or {}).values() for sg in sgs)
    chats = sum(len(t.get("free_chats") or []) for t in ticks)
    mem = [len(a.get("mem") or []) for a in w.agents.values()]
    why = collections.Counter(sg["label"][:24] for t in ticks for sgs in (t.get("free") or {}).values() for sg in sgs if sg["act"] in ("explore", "tinker", "chat"))
    print(f"brain={brain}: decisions model/engine {model}/{engine}, chats {chats}, plan items made/done {plans}/{done}, memories per character {min(mem) if mem else 0}-{max(mem) if mem else 0}, plan-driven acts: explore {acts['explore']} tinker {acts['tinker']} chat {acts['chat']}")
    if brain:
        a0 = next(iter(w.agents.values()))
        print("  sample plan:", (a0.get("plan") or {}).get("items"))
        print("  sample memories:", [m["t"][:60] for m in (a0.get("mem") or [])[-4:]])
