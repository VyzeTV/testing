"""One full real-AI day with free time, plus a scheduled fire, then a report on what the new systems did.
Run:  python tests/real_free_day.py      (uses the claude CLI, roughly 70-110 calls; never touches your saves)"""
import collections
import os
import statistics
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_realfree_")

from murder import scenario as scn              # noqa: E402
from murder.data_world import ROOMS             # noqa: E402
from murder.engine import DayRunner             # noqa: E402
from murder.llm import LLM                      # noqa: E402
from murder.world import World, new_state       # noqa: E402

llm = LLM(backend="cli")
w = World(new_state(3, shuffle_rooms=True))
sc = {"title": "Free Time Check", "premise": "A quiet day, until something catches fire.", "twist": None, "rules": [], "relationships": [], "secrets": [], "items": [], "deadline_days": None,
      "events": [{"day": 3, "hour": 14, "kind": "fire", "room": "lounge", "text": "A candle falls in the Lounge and the carpet catches."}]}
w.state["scenario"] = scn.clean(sc, set(w.agents), set(ROOMS))
ticks = []
r = DayRunner(w, llm, ticks.append, step=2, murders=True, rule_mode="none", confessionals=False, seed=33)
san0 = {c: a["sanity"] for c, a in w.agents.items()}
try:
    r.run()
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    print("RUN FAILED:", repr(e))
cnt = collections.Counter(e["type"] for t in ticks for e in t.get("events", []))
acts = collections.Counter(sg["act"] for t in ticks for sgs in (t.get("free") or {}).values() for sg in sgs)
per = collections.defaultdict(collections.Counter)
for t in ticks:
    for cid, sgs in (t.get("free") or {}).items():
        for sg in sgs:
            per[cid][sg["act"]] += 1
tele = w.state.get("telemetry", {}).get("3", {}).get("decision", {})
print("ticks", len(ticks), "free", sum(1 for t in ticks if t.get("segment") == "free"), "| calls:", llm.usage["calls"], "cost $%.2f" % llm.usage["cost_usd"],
      "| decisions model/engine:", tele.get("model", 0), "/", tele.get("engine", 0))
print("tick errors:", [e for t in ticks for e in t.get("errors", [])][:6], "| layer errors:", [(k, t[k]) for t in ticks for k in ("live_error", "env_error", "mind_error") if t.get(k)])
gm = [(t["hour"], e["text"][:110]) for t in ticks for e in t["events"] if e["type"] == "system" and e["vis"] == "gm" and ("could not" in e["text"] or "cannot" in e["text"] or "failed" in e["text"])]
print("GM complaints:", gm)
print("activities:", dict(acts.most_common()))
print("aimless (look/stay/walk):", round(sum(acts[k] for k in ("look", "stay", "walk")) / max(1, sum(acts.values())), 2))
for cid, c in per.items():
    print("  ", cid, dict(c.most_common(7)))
chats = [(t["hour"], c["room"], c["m"], c["members"], c["why"], c.get("matters")) for t in ticks for c in (t.get("free_chats") or [])]
print("chats:", len(chats))
for c in chats:
    print("  ", c)
print("talk groups:", sum(len(t["talk"]) for t in ticks), "lines:", sum(len(g["lines"]) for t in ticks for g in t["talk"]))
print("environment events:", {k: cnt[k] for k in ("fire", "wreck", "reaction", "condition", "faint") if cnt[k]})
for t in ticks:
    for e in t["events"]:
        if e["type"] in ("fire", "reaction", "faint", "condition", "stat") and (e["type"] != "stat" or ("flames" in e["text"] or "smoke" in e["text"])) and t["hour"] in (14, 16):
            print("  ", t["hour"], e.get("m"), e["type"], e["text"][:120])
print("deaths:", [e["text"] for t in ticks for e in t.get("chron", []) if e["type"] == "death" and e["vis"] == "gm"])
san1 = {c: a["sanity"] for c, a in w.agents.items()}
print("hp", {c: a["hp"] for c, a in w.agents.items()})
print("sanity start median", statistics.median(san0.values()), "-> end", statistics.median(san1.values()), "| lowest", min(san1.values()))
print("embarrassed/snap/attack/plot:", {k: cnt[k] for k in ("embarrassed", "snap", "attack", "assault", "plot", "craft", "experiment") if cnt[k]})
print("sample conversation lines:")
for t in ticks:
    for g in t["talk"]:
        if g.get("m") is not None:
            for l in g["lines"][:4]:
                print("   [%s %s] %s: %s" % (t["hour"], g["room"], l["speaker"], l["text"][:110]))
            break
