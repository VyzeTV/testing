"""One real-AI day to check the director upgrade (phase 8): a stalled plot the model proposes a plan for, someone in crisis who gets a
proposed move, a GM goal, lovers and a rival, then the trial if somebody dies. Writes what was said and shown, every proposal with the
engine's verdict, the night's reflection choices and the stories in play to a JSON file.
Run:  python tests/real_director_day.py [out.json]     (uses the claude CLI, roughly 90-140 calls; never touches your saves)"""
import collections
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_realdir_")

from murder.engine import DayRunner              # noqa: E402
from murder.llm import LLM                       # noqa: E402
from murder.world import World, new_state        # noqa: E402

out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "mc_real_director.json")
llm = LLM(backend=os.environ.get("MC_BACKEND", "cli"))
proposals = []
_propose = llm.propose


def propose(system, user, ctx):
    r = _propose(system, user, ctx)
    proposals.append({"kind": ctx.get("kind"), "who": ctx.get("cid"), "prompt": user, "answer": r})
    return r


llm.propose = propose
w = World(new_state(5, shuffle_rooms=True))
w.state["revealed"] = True
ids = list(w.agents)
lover_a, lover_b, rival, crisis, plotter, target, friend_a, friend_b = ids[0], ids[2], ids[4], ids[5], ids[1], ids[6], ids[3], ids[7]
for x, y in ((lover_a, lover_b), (lover_b, lover_a)):
    w.agents[x]["aff"][y] = 9
w.state.setdefault("bonds", []).append({"a": lover_a, "b": lover_b, "kind": "romance", "since": 3})
w.agents[rival]["aff"][lover_a] = 9
w.agents[crisis]["sanity"] = 17
w.state["plots"] = {plotter: {"target": target, "stage": "striking", "motive": "hatred", "stage_ticks": 5, "weapon": None, "method": "", "step": "", "cover": "", "log": [], "quiet": 0, "plan": [], "reason": "hatred: staged for the test",
                              "scheme": {"kind": "alone", "room": "observatory", "when": "day", "why": "catch them alone in the Observatory (never happens)"}}}
w.agents[plotter]["aff"][target] = -8
staged = {"lovers": [lover_a, lover_b], "rival": rival, "crisis": crisis, "plotter": plotter, "target": target, "goal_friends": [friend_a, friend_b]}
print("staged:", staged)
ticks = []
for day in (5, 6):
    if w.state.get("over") or not w.agents:
        break
    w.state["day"] = day
    r = DayRunner(w, llm, ticks.append, step=2, murders=True, rule_mode="roulette", confessionals=True, seed=80 + day)
    if day == 5:
        r.set_goal(r.new_tick(8), {"type": "goal", "kind": "friends", "a": friend_a, "b": friend_b, "days": 2}, 8)
    try:
        r.run()
    except Exception as e:  # noqa: BLE001
        import traceback
        traceback.print_exc()
        print("RUN FAILED:", repr(e))
        break
    if day == 5 and not any(t.get("type") == "trial" for t in ticks) and not w.state.get("case"):
        break                                                     # nobody died: one day is enough
    if llm.usage["calls"] > 150:
        break
keep = []
for t in ticks:
    keep.append({"day": t.get("day"), "hour": t.get("hour"), "type": t.get("type"), "broadcasts": t.get("broadcasts"),
                 "events": [e for e in t.get("events", []) if e.get("vis") in ("public", "viewer")],
                 "gm": [e["text"] for e in t.get("events", []) if e.get("vis") == "gm" and e.get("type") in ("director", "drive", "plot")],
                 "talk": [{"room": g.get("room"), "lines": g.get("lines"), "segment": (g.get("segment") or {}).get("kind")} for g in t.get("talk", [])],
                 "diaries": t.get("diaries"), "inner": t.get("inner"), "stories": t.get("stories"), "goals": t.get("goals"), "execution": t.get("execution")})
json.dump({"staged": staged, "proposals": proposals, "proposer_stats": w.state.get("proposer_stats"), "reflect_stats": w.state.get("reflect_stats"),
           "goals": w.state.get("goals"), "plots": w.state.get("plots"), "ticks": keep}, open(out_path, "w"), indent=1, default=str)
cnt = collections.Counter(e["type"] for t in ticks for e in t.get("events", []))
print("ticks", len(ticks), "| calls:", llm.usage["calls"], "| written:", out_path)
print("tick errors:", [e for t in ticks for e in t.get("errors", [])][:6])
print("proposals:", w.state.get("proposer_stats"), "| reflections:", w.state.get("reflect_stats"))
print("event counts:", {k: cnt[k] for k in ("romance", "attack", "body", "plot", "outburst", "punish", "mercy") if cnt[k]})
