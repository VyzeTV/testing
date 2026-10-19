"""One real-AI afternoon and evening to hear NeoVi (phase D): 12:00 to dawn, with someone she trusts (Chloe), someone who dislikes her (Szymon) and
someone fond of her (Ayden). Writes every conversation she is in, and her scenes, to a JSON file.
Run:  python tests/real_neovi_day.py [out.json]     (uses the claude CLI, roughly 50-70 calls; never touches your saves)"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_realnv_")

from murder.engine import DayRunner              # noqa: E402
from murder.llm import LLM                       # noqa: E402
from murder.world import World, new_state        # noqa: E402

out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "mc_real_neovi.json")
llm = LLM(backend=os.environ.get("MC_BACKEND", "cli"))
w = World(new_state(5, shuffle_rooms=True))
w.state["revealed"] = True
w.state["intro_done"] = True
nv = w.state["npcs"]["neovi"]
nv.setdefault("aff", {}).update({"chloe": 6, "ayden": 3, "szymon": -2})
for c, v in (("chloe", 6), ("ayden", 5), ("szymon", -5)):
    w.agents[c]["nv_aff"] = v
ticks = []
r = DayRunner(w, llm, ticks.append, step=2, murders=False, rule_mode="roulette", confessionals=False, seed=int(os.environ.get("MC_SEED", "95")))
try:
    r.run(resume_after=10)
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    print("RUN FAILED:", repr(e))
convs = []
for t in ticks:
    for g in t.get("talk") or []:
        if any(l["speaker"] == "neovi" for l in g["lines"]):
            convs.append({"hour": t["hour"] % 24, "room": g["room"], "why": g.get("why"), "scene": (g.get("scene") or {}).get("kind"),
                          "lines": [{"who": l["speaker"], "move": l.get("move"), "kind": l["kind"], "text": l["text"]} for l in g["lines"]]})
report = {"calls": llm.usage["calls"], "conversations_with_neovi": len(convs), "neovi_lines": sum(1 for c in convs for l in c["lines"] if l["who"] == "neovi"),
          "nv_talk": w.state.get("nv_talk"), "errors": [e for t in ticks for e in t.get("errors", [])][:8]}
json.dump({"report": report, "conversations": convs}, open(out_path, "w"), indent=1, default=str)
print(json.dumps(report, indent=1))
print("written:", out_path)
