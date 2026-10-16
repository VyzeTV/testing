"""One full real-AI day with a generated scenario whose events are scheduled for that same day, then a report on what the new systems did.
Run:  python tests/real_scenario_day.py      (uses the claude CLI, roughly 60-100 calls; never touches your saves)"""
import collections
import os
import statistics
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_realscn_")

from murder import scengen, scenario as scn   # noqa: E402
from murder.data_world import ROOMS            # noqa: E402
from murder.engine import DayRunner            # noqa: E402
from murder.llm import LLM                     # noqa: E402
from murder.world import World, new_state      # noqa: E402

llm = LLM(backend="cli")
w = World(new_state(3, shuffle_rooms=True))
gen = scengen.generate("real-day", 6, start_day=3)
sc = gen["scenario"]
for i, ev in enumerate(sc["events"]):
    ev["day"], ev["hour"] = 3, [12, 14, 16][i % 3]
sc["twist"]["day"] = 3
w.state["scenario"] = scn.clean({**sc, "_meta": gen["meta"]}, set(w.agents), set(ROOMS))
scn.apply_seeds(w.state)
ticks = []
r = DayRunner(w, llm, ticks.append, step=2, murders=True, rule_mode="none", confessionals=False, seed=21)
san0 = {c: a["sanity"] for c, a in w.agents.items()}
try:
    r.run()
except Exception as e:  # noqa: BLE001
    print("RUN FAILED:", repr(e))
cnt = collections.Counter(e["type"] for t in ticks for e in t.get("events", []))
tele = w.state.get("telemetry", {}).get("3", {}).get("decision", {})
print("SCENARIO:", sc["title"], "| rules:", sc["rules"], "| events:", [(e["kind"], e["hour"], e.get("room")) for e in sc["events"]], "| budget", gen["meta"]["spent"], "/", gen["meta"]["budget"])
print("calls:", llm.usage["calls"], "cost $%.2f" % llm.usage["cost_usd"], "| errors:", sum(len(t.get("errors", [])) for t in ticks), "| live/env/mind errors:", [k for t in ticks for k in ("live_error", "env_error", "mind_error") if t.get(k)])
print("decisions model/engine:", tele.get("model", 0), "/", tele.get("engine", 0))
print("environment events:", {k: cnt[k] for k in ("fire", "flood", "wreck") if cnt[k]}, "| scenario events fired:", w.state["scenario"].get("_fired"))
print("other events:", {k: cnt[k] for k in ("plot", "attack", "assault", "faint", "treat", "friction", "madness", "interrogation") if cnt[k]})
chron = w.state.get("chronicle", [])
print("chronicle entries:", len(chron), "| with witnesses:", sum(1 for e in chron if e.get("seen")), "| deaths:", [e["text"] for e in chron if e["type"] == "death" and e["vis"] == "gm"])
san1 = {c: a["sanity"] for c, a in w.agents.items()}
print("sanity start median", statistics.median(san0.values()), "-> end median", statistics.median(san1.values()), "| lowest", min(san1.values()), "| stress:", {c: a.get("mind", {}).get("stress") for c, a in w.agents.items()})
for t in ticks:
    for e in t.get("events", []):
        if e["type"] in ("fire", "flood", "wreck", "interrogation") or (e["type"] == "island" and "terevi" == e["who"]):
            print(t.get("time"), e["type"], "|", e["text"][:140])
