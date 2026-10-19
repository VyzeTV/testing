"""One real-AI evening to check the dialogue fixes (phase A): 16:00 to dawn with a couple and close friends, then counts of what Day 3 got wrong.
Checks: nobody answers their own line, no "morning" after noon, a pet name at most once per person per scene, few remarks on looks, amigo/amiga by gender.
Writes every live conversation to a JSON file for reading.
Run:  python tests/real_evening.py [out.json]     (uses the claude CLI, roughly 50-80 calls; never touches your saves)"""
import collections
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_realeve_")

from murder.engine import DayRunner              # noqa: E402
from murder.llm import LLM                       # noqa: E402
from murder.world import World, new_state        # noqa: E402

out_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(tempfile.gettempdir(), "mc_real_evening.json")
llm = LLM(backend=os.environ.get("MC_BACKEND", "cli"))
w = World(new_state(4, shuffle_rooms=True))
w.state["revealed"] = True
w.state["intro_done"] = True
for x, y in (("noah", "cail"), ("cail", "noah"), ("chloe", "ayden"), ("ayden", "chloe")):
    w.agents[x]["aff"][y] = 9
w.state.setdefault("bonds", []).append({"a": "noah", "b": "cail", "kind": "romance", "since": 3})
ticks = []
r = DayRunner(w, llm, ticks.append, step=2, murders=False, rule_mode="roulette", confessionals=False, seed=int(os.environ.get("MC_SEED", "93")))
try:
    r.run(resume_after=14)
except Exception as e:  # noqa: BLE001
    import traceback
    traceback.print_exc()
    print("RUN FAILED:", repr(e))

PET = re.compile(r"\b(babe|amigo|amiga|darling|sweetheart|honey|dude|bro)\b", re.I)
LOOKS = re.compile(r"\b(hair|outfit|dress|shirt|jacket|hat|fedora|ribbon|glasses|scarf|earring|looks? (great|good|nice|cute|amazing))\b", re.I)
convs, own, mornings, pets_over, looks_n, amigo_wrong, lines_n = [], 0, [], [], 0, [], 0
for t in ticks:
    for g in t.get("talk") or []:
        ls = g["lines"]
        lines_n += len(ls)
        hour = t["hour"]
        convs.append({"day": t["day"], "hour": hour % 24, "room": g["room"], "why": g.get("why"), "members": g.get("members"),
                      "lines": [{"who": l["speaker"], "ex": l.get("ex"), "cont": l.get("cont"), "move": l.get("move"), "kind": l["kind"], "text": l["text"]} for l in ls]})
        ex = [l for l in ls if "ex" in l]
        own += sum(1 for x, y in zip(ex, ex[1:]) if x["speaker"] == y["speaker"] and (x["ex"] == y["ex"] or not y.get("cont")))
        per = collections.Counter()
        for l in ls:
            hh = hour % 24 + (l.get("m") or 0) / 60
            if 12 <= hh < 29 and re.search(r"\bmorning\b", l["text"], re.I) and not re.search(r"tomorrow morning|this morning|in the morning", l["text"], re.I):
                mornings.append(f"{int(hh) % 24:02d}h {l['speaker']}: {l['text']}")
            for p in PET.findall(l["text"]):
                per[(l["speaker"], p.lower())] += 1
            if LOOKS.search(l["text"]):
                looks_n += 1
            if re.search(r"\bamigo\b", l["text"], re.I) and l["speaker"] == "noah":
                to = sorted({x["speaker"] for x in ls if x["speaker"] != "noah"})
                if to and all(w.cast[m].get("gender") == "female" for m in to if m in w.cast):
                    amigo_wrong.append(l["text"])
        pets_over += [f"{k[0]} '{k[1]}' x{v} in the {g['room']}" for k, v in per.items() if v > 1]
report = {"calls": llm.usage["calls"], "conversations": len(convs), "lines": lines_n, "own_replies": own, "morning_after_noon": mornings,
          "pet_name_repeats": pets_over, "looks_remarks": looks_n, "amigo_to_women": amigo_wrong,
          "errors": [e for t in ticks for e in t.get("errors", [])][:8]}
json.dump({"report": report, "conversations": convs}, open(out_path, "w"), indent=1, default=str)
print(json.dumps(report, indent=1))
print("written:", out_path)
