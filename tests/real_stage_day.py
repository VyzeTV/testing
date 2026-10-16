"""One full real-AI day with the dramatic pieces staged, to see that they play out with the real model: a plotter who is already striking, someone about to snap, and an underwear rule (embarrassment).
Run:  python tests/real_stage_day.py      (uses the claude CLI, roughly 70-110 calls; never touches your saves)"""
import collections
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_realstage_")

from murder.engine import DayRunner              # noqa: E402
from murder.llm import LLM                       # noqa: E402
from murder.world import World, new_state        # noqa: E402

llm = LLM(backend="cli")
w = World(new_state(4, shuffle_rooms=True))
w.state["revealed"] = True
ids = list(w.agents)
plotter, target, snapper, hated = ids[1], ids[6], ids[7], ids[3]     # shintaro, chloe, cail, noah in the default cast order
w.state["plots"] = {plotter: {"target": target, "stage": "striking", "motive": "hatred", "stage_ticks": 0, "weapon": None, "method": "", "step": "", "cover": "", "log": [], "quiet": 0, "reason": "hatred: staged for the test"}}
w.agents[plotter]["aff"][target] = -8
w.agents[target]["aff"][plotter] = -6
w.agents[snapper]["sanity"] = 9
w.agents[snapper]["aff"][hated] = -9
w.agents[hated]["aff"][snapper] = -5
print("staged:", {"plotter": plotter, "target": target, "snapper": snapper, "hated": hated})
ticks = []
r = DayRunner(w, llm, ticks.append, step=2, murders=True, rule_mode="custom", rule_text="Everyone must only wear underwear today", confessionals=False, seed=44)
try:
    r.run()
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    print("RUN FAILED:", repr(e))
cnt = collections.Counter(e["type"] for t in ticks for e in t.get("events", []))
print("ticks", len(ticks), "| calls:", llm.usage["calls"], "cost $%.2f" % llm.usage["cost_usd"])
print("tick errors:", [e for t in ticks for e in t.get("errors", [])][:6], "| layer errors:", [(k, t[k]) for t in ticks for k in ("live_error", "env_error", "mind_error") if t.get(k)])
print("GM complaints:", [(t["hour"], e["text"][:110]) for t in ticks for e in t["events"] if e["type"] == "system" and e["vis"] == "gm" and ("could not" in e["text"] or "cannot" in e["text"])])
print("event counts:", {k: cnt[k] for k in ("plot", "attack", "assault", "snap", "embarrassed", "clothes", "punish", "mercy", "faint", "friction", "reaction") if cnt[k]})
for t in ticks:
    for e in t["events"]:
        if e["type"] in ("attack", "assault", "snap", "embarrassed", "plot", "mercy") or (e["type"] == "system" and "Director" in e["text"]):
            print("  ", t["hour"], e.get("m"), e["type"], e["who"], e["room"], "|", e["text"][:130])
print("deaths:", [e["text"] for t in ticks for e in t.get("chron", []) if e["type"] == "death" and e["vis"] == "gm"])
print("case:", {k: (w.state["case"] or {}).get(k) for k in ("kind", "killer", "victim", "snap", "note")} if w.state.get("case") else None)
print("plot waits:", {c: (p.get("stage"), round(p.get("wait", 0), 1)) for c, p in w.state.get("plots", {}).items()}, "| nudges:", len(w.state.get("nudges", [])))
print("final hp/sanity:", {c: (a["hp"], a["sanity"]) for c, a in w.agents.items()})
acts = collections.Counter(sg["act"] for t in ticks for sgs in (t.get("free") or {}).values() for sg in sgs)
print("activities:", dict(acts.most_common(14)))
chats = [(t["hour"], c["room"], c["members"], c["why"], c.get("matters")) for t in ticks for c in (t.get("free_chats") or [])]
print("chats:", len(chats))
for c in chats:
    print("  ", c)
