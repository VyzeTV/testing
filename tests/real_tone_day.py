"""One real-AI day to read the tone (phase 7b step 6): lovers, a jealous third, a fraying mind and a plotter already striking, then the trial if
somebody dies. Writes everything said, shown and thought to a JSON file for reading.
Run:  python tests/real_tone_day.py [out.json]     (uses the claude CLI, roughly 90-120 calls; never touches your saves)"""
import collections
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_realtone_")

from murder.engine import DayRunner              # noqa: E402
from murder.llm import LLM                       # noqa: E402
from murder.world import World, new_state        # noqa: E402

out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "mc_real_tone.json")
llm = LLM(backend="cli")
w = World(new_state(5, shuffle_rooms=True))
w.state["revealed"] = True
ids = list(w.agents)
lover_a, lover_b, jealous, fraying, plotter, target = ids[0], ids[2], ids[4], ids[5], ids[1], ids[6]
for x, y in ((lover_a, lover_b), (lover_b, lover_a)):
    w.agents[x]["aff"][y] = 9
w.state.setdefault("bonds", []).append({"a": lover_a, "b": lover_b, "kind": "romance", "since": 3})
w.agents[jealous]["aff"][lover_a] = 9
w.agents[fraying]["sanity"] = 18
w.state["plots"] = {plotter: {"target": target, "stage": "striking", "motive": "hatred", "stage_ticks": 0, "weapon": None, "method": "", "step": "", "cover": "", "log": [],
                              "quiet": 0, "reason": "hatred: staged for the test"}}
w.agents[plotter]["aff"][target] = -8
staged = {"lovers": [lover_a, lover_b], "jealous": jealous, "fraying": fraying, "plotter": plotter, "target": target}
print("staged:", staged)
ticks = []
for day in (5, 6):
    if w.state.get("over") or not w.agents:
        break
    w.state["day"] = day
    r = DayRunner(w, llm, ticks.append, step=2, murders=True, rule_mode="roulette", confessionals=True, seed=60 + day)
    try:
        r.run()
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("RUN FAILED:", repr(e))
        break
    if day == 5 and not any(t.get("type") == "trial" for t in ticks) and not w.state.get("case"):
        break                                                     # nobody died: one day is enough
    if llm.usage["calls"] > 140:
        break
keep = []
for t in ticks:
    keep.append({"day": t.get("day"), "hour": t.get("hour"), "type": t.get("type"),
                 "broadcasts": t.get("broadcasts"), "events": [e for e in t.get("events", []) if e.get("vis") in ("public", "viewer")],
                 "talk": [{"room": g.get("room"), "lines": g.get("lines"), "segment": (g.get("segment") or {}).get("kind")} for g in t.get("talk", [])],
                 "confessionals": t.get("confessionals"), "inner": t.get("inner"), "execution": t.get("execution"), "scene_body": t.get("scene_body")})
json.dump({"staged": staged, "ticks": keep, "twists": w.state.get("twists"), "intimacy": w.state.get("intimacy"), "mind": w.state.get("mind_stats")},
          open(out_path, "w"), indent=1, default=str)
cnt = collections.Counter(e["type"] for t in ticks for e in t.get("events", []))
print("ticks", len(ticks), "| calls:", llm.usage["calls"], "| written:", out_path)
print("tick errors:", [e for t in ticks for e in t.get("errors", [])][:6])
print("event counts:", {k: cnt[k] for k in ("romance", "attack", "body", "plot", "outburst", "punish") if cnt[k]})
