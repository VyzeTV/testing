"""Headless mock days with free time: what people did, how many segments, plots, snaps, nudges.
Run:  python tests/free_day.py [days]      (mock backend only; never touches your saves)"""
import collections
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_free_")

from murder.engine import DayRunner   # noqa: E402
from murder.llm import LLM            # noqa: E402
from murder.world import World, new_state   # noqa: E402

days = int(sys.argv[1]) if len(sys.argv) > 1 else 3
w = World(new_state(3))
ticks = []
for d in range(3, 3 + days):
    w.state["day"] = d
    r = DayRunner(w, LLM(backend="mock"), ticks.append, step=2, murders=True, rule_mode="none", seed=7 + d)
    r.run()
    if w.state.get("over"):
        break
acts = collections.Counter()
errs = collections.Counter()
ev = collections.Counter()
for t in ticks:
    for cid, segs in (t.get("free") or {}).items():
        for sg in segs:
            acts[sg["act"]] += 1
    for e in t.get("errors", []):
        errs[str(e)[:80]] += 1
    for e in t.get("events", []):
        ev[e["type"]] += 1
        if e["type"] == "system" and e["vis"] == "gm" and "could not" in e["text"]:
            errs[e["text"][:80]] += 1
print("ticks", len(ticks), "free ticks", sum(1 for t in ticks if t.get("segment") == "free"))
print("activities", dict(acts.most_common()))
print("errors/gm", dict(errs.most_common(8)))
print("events", {k: v for k, v in ev.most_common(40)})
print("sanity", sorted(a["sanity"] for a in w.agents.values()))
print("deaths", [e["text"] for t in ticks for e in t.get("chron", []) if e["type"] == "death" and e["vis"] == "gm"])

bad = 0
for t in ticks:
    if t.get("live_error") or t.get("env_error") or t.get("mind_error"):
        print("ERR", t.get("live_error"), t.get("env_error"), t.get("mind_error"))
    lv = t.get("live") or {}
    for cid, tr in (lv.get("tracks") or {}).items():
        ts = [p[0] for p in tr]
        if ts != sorted(ts):
            bad += 1
print("non-monotonic tracks:", bad, "| free ticks with acts:", sum(1 for t in ticks if (t.get("live") or {}).get("acts")))

chats = [(t["day"], t["hour"], c["room"], c["m"], c["members"], c["why"]) for t in ticks for c in (t.get("free_chats") or [])]
print("chats", len(chats), "per free tick", round(len(chats) / max(1, sum(1 for t in ticks if t.get("segment") == "free")), 2))
for c in chats[:8]:
    print("  ", c)
groups = [(g.get("m"), g["room"], len(g["lines"])) for t in ticks for g in t["talk"]]
print("talk groups", len(groups), "of which chats", sum(1 for g in groups if g[0] is not None))
tot = sum(acts.values()) or 1
print("aimless share (look/stay/walk/explore w/o purpose):", round(sum(acts[k] for k in ("look", "stay", "walk")) / tot, 2))
