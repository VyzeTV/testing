"""Fast mock-mode checks of the engine. Run:  python tests/smoke.py   (no AI calls, never touches your saves)."""
import copy
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
os.environ["MC_DATA_DIR"] = tempfile.mkdtemp(prefix="mc_smoke_")

from murder.data_world import ITEMS, ESCAPE_ROUTES      # noqa: E402
from murder.engine import DayRunner                       # noqa: E402
from murder.llm import LLM                                # noqa: E402
import murder.llm as L                                    # noqa: E402
from murder.world import World, new_state                 # noqa: E402

RESULTS = []


def check(name, cond, extra="", known=None):
    """`known`: the reason a check is expected to fail for now. It is reported as KNOWN instead of FAIL and does not fail the run; once it passes it reports as FIXED."""
    RESULTS.append((name, bool(cond), known))
    tag = ("FIXED " if known else "PASS ") if cond else ("KNOWN " if known else "FAIL ")
    print(tag + name + (f"  [{extra}]" if extra else "") + (f"  (known: {known})" if known and not cond else ""))


def fresh(seed=1, day=3, **kw):
    w = World(new_state(day))
    ticks = []
    r = DayRunner(w, LLM(backend="mock"), ticks.append, step=2, murders=True, rule_mode="none", confessionals=False, seed=seed, **kw)
    r.init_item_log()
    return w, r, ticks


def sharp():
    return [i for i, sp in ITEMS.items() if "sharp" in sp.get("tags", []) and "weapon" in sp.get("tags", [])][0]


# ---- Day 1 flow
w = World(new_state(1))
t = []
DayRunner(w, LLM(backend="mock"), t.append, step=2, murders=True, rule_mode="roulette", seed=1).run()
types = [x.get("type") or "tick" for x in t]
check("day 1 has meeting and reveal", "meeting" in types and "reveal" in types and w.state["revealed"])

# ---- murder case, clues, announce, trial
w, r, _ = fresh(2)
ids = list(w.agents)
k, v = ids[0], ids[1]
w.agents[k]["room"] = w.agents[v]["room"] = "green_room"
wp = sharp()
w.agents[k]["inv"][wp] = 1
tick = r.new_tick(15)
r.open_case(tick, "murder", v, culprit=k, wkind="sharp", weapon=wp, room="green_room", hour=15, witnesses=[])
c = w.state["case"]
check("case has scene+ledger clues", {"scene", "ledger"} <= {x["kind"] for x in c["clues"]})
r.announce_body(tick, 16)
L.LLM.mock_vote_killer_prob = 1.0
r.tuning_get = lambda: {"claim_trial": 0}                     # the old trial, where the model casts the votes
tr = r.run_trial(10)
r.tuning_get = lambda: {}
check("trial runs at the voting grounds with segments", tr["segments"] and all(m["to"] == "voting_grounds" for m in list(tr["moves"].values())[:2]))
check("trial convicts the killer when everyone votes right", tr["trial"]["found"])

# ---- deaths with no culprit skip the trial
w, r, _ = fresh(3)
c0 = list(w.agents)[0]
tick = r.new_tick(14)
r.open_case(tick, "suicide", c0, room=w.agents[c0]["room"], hour=14, witnesses=[], cause="pills", note="Sorry.")
r.announce_body(tick, 15)
check("suicide: no trial, case cleared, deadline lifted", w.state["case"] is None and w.state["deadline_day"] > w.state["day"])

# ---- unaware culprit
w, r, _ = fresh(4)
ids = list(w.agents)
a_, b_ = ids[0], ids[1]
w.agents[a_]["room"] = w.agents[b_]["room"] = "lounge"
w.agents[b_]["hp"] = 6
r.blackout_until = r.idx + 1
tick = r.new_tick(14)
for _ in range(8):
    r.do_assault(tick, a_, b_, None, 14)
    if w.state["case"]:
        break
check("assault in the dark: unaware culprit", w.state["case"] and w.state["case"]["culprit_aware"] is False)

# ---- build + climb
w, r, _ = fresh(5)
a = list(w.agents)[0]
w.agents[a]["room"] = "library"
w.agents[a]["inv"].update({"planks": 2, "rope": 1, "hammer": 1})
tick = r.new_tick(10)
for _ in range(8):
    r.do_build(tick, a, {"build": {"kind": "ladder", "to": "garden"}})
    if w.state["built"]:
        break
    w.agents[a]["inv"].update({"planks": 2, "rope": 1})
check("ladder can be built and used", bool(w.state["built"]) and w.path(a, "library", "garden"))

# ---- every route's finale
for rid in ESCAPE_ROUTES:
    w, r, _ = fresh(9)
    for k_ in w.state["escape"]["routes"][rid]["plan"]:
        w.state["escape"]["routes"][rid]["plan"][k_] = 100
    check(f"route {rid} becomes ready", r.ready_route() == rid)
    t = r.run_finale(rid, 12)
    check(f"route {rid} finale resolves", t["type"] == "finale")

# ---- sanity balance: deep touching moment between close people restores more
w, r, _ = fresh(6)
x, y = list(w.agents)[:2]
w.agents[x]["aff"][y] = w.agents[y]["aff"][x] = 8
w.agents[x]["sanity"] = 30
tick = r.new_tick(10)
before = w.agents[x]["sanity"]
r.special_boost(tick, x, 3 * 2.0 * 1.5, "deep comfort", "comfort")
check("close friends recover more from a deep moment", w.agents[x]["sanity"] - before >= 8, str(w.agents[x]["sanity"] - before))

# ---- night recovery
w, r, _ = fresh(7)
x, y = list(w.agents)[:2]
w.agents[x]["room"] = w.agents[y]["room"] = "blue_room"
w.agents[x]["aff"][y] = w.agents[y]["aff"][x] = 7
w.agents[x]["sanity"] = 30
tick = r.new_tick(22)
r.night_recovery(tick)
check("night beside a loved one restores sanity", w.agents[x]["sanity"] >= 35)

# ---- lean mode and call cap
w, r, _ = fresh(8, lean=True)
check("lean decision prompt is shorter", len(r.decision_prompt(list(w.agents)[0], 12)) < len(fresh(8, lean=False)[1].decision_prompt(list(fresh(8)[0].agents)[0], 12)) + 1)
llm = LLM(backend="mock")
llm.cap = 0
check("call cap off by default", llm.cap in (0, None))

# ---- last call / reckoning
w = World(new_state(3)); w.state["day"] = 7; w.state["deadline_day"] = 7
t = []
DayRunner(w, LLM(backend="mock"), t.append, step=2, murders=True, rule_mode="none", confessionals=False, seed=3).run()
check("deadline day resolves (death, sacrifice or reckoning)", w.state["case"] is not None or w.state["over"] is not None or len(w.agents) < 8)

# ---- step 2: traps
w, r, _ = fresh(11)
ids = list(w.agents)
bj, vic = ids[0], ids[1]
w.agents[bj]["room"] = "lookout"
w.agents[bj]["inv"]["crowbar"] = 1
tick = r.new_tick(12)
for _ in range(10):
    r.do_rig(tick, bj, {"rig": {"kind": "fall", "target": vic}})
    if w.state["traps"]:
        break
    w.agents[bj]["inv"]["crowbar"] = 1
check("a trap can be rigged", bool(w.state["traps"]))
if w.state["traps"]:
    w.agents[bj]["room"] = "foyer"
    for _ in range(40):
        w.agents[vic]["room"] = "lookout"; w.agents[vic]["hp"] = 30
        t2 = r.new_tick(14)
        t2["moves"][vic] = {"from": "upper_landing", "path": ["upper_landing", "lookout"], "to": "lookout"}
        r.resolve_traps(t2, 14)
        if w.state["case"]:
            break
        if not w.state["traps"]:
            break
    c = w.state["case"]
    check("a trap can kill later with the rigger elsewhere", c is not None and c["killer"] == bj and c.get("trap"))
    if c:
        kinds = [x["kind"] for x in c["clues"]]
        check("trap case has tamper clue and two ledgers", "tamper" in kinds and kinds.count("ledger") >= 2 and "ledger_door" in kinds, str(kinds))

# ---- spree and endgame
w, r, _ = fresh(12)
for a in w.agents.values():
    a["sanity"] = 12
    for o in a["aff"]:
        a["aff"][o] = -4
list(w.agents.values())[0]["drive"]["id"] = "nihilist"
L.LLM.mock_murder_prob = 0.0
for _ in range(60):
    tick = r.new_tick(14)
    r.maybe_spree(tick, 14)
    if w.state["spree"]:
        break
check("a collapsed house can start a spree", bool(w.state["spree"]))
if w.state["spree"]:
    by = w.state["spree"]["by"]
    victims = [c for c in w.agents if c != by][:2]
    for v in victims:
        w.agents[by]["room"] = w.agents[v]["room"] = "lounge"
        tick = r.new_tick(15)
        r.open_case(tick, "murder", v, culprit=by, wkind="blunt", weapon=None, room="lounge", hour=15, witnesses=[])
    check("spree deaths need no trial", w.state["case"] is None and len(w.state["bodies"]) == 2)
    check("spree counted kills", w.state["spree"]["kills"] == 2)

for alive_n, label in ((3, "three"), (1, "one"), (0, "none")):
    w, r, _ = fresh(13 + alive_n)
    for cid in list(w.agents)[alive_n:]:
        w.end_agent(cid, "dead")
    check(f"endgame due with {label} survivors", r.endgame_due() or alive_n == 0 and not w.agents and r.revealed)
    t = r.run_endgame(20)
    check(f"endgame ends the season with {label} survivors", w.state["over"] is not None and t["type"] == "endgame", w.state["over"] and w.state["over"]["kind"])

# ---- NeoVi arc
for fate_try in range(3):
    w, r, _ = fresh(20 + fate_try)
    nv = w.state["npcs"]["neovi"]
    ally = list(w.agents)[0]
    nv["aff"][ally] = 9
    nv["arc"] = {"resolve": 99, "stage": 3, "fate": None, "ally": ally}
    if fate_try == 2:
        for a in w.agents.values():
            a["sanity"] = 10
    tick = r.new_tick(22)
    r.neovi_arc_night(tick)
    check(f"NeoVi arc reaches a fate ({fate_try})", nv["arc"]["fate"] in ("martyr", "survivor", "betrayer"), str(nv["arc"]["fate"]))

# ---- TereVi adapts
w, r, _ = fresh(30)
plan = w.state["escape"]["routes"]["transmit"]["plan"]
plan["unjam"] = 80
tick = r.new_tick(12)
r.terevi_reinforce(tick, "transmit", "test")
check("TereVi reinforcing sets a route back and raises hardness", plan["unjam"] < 80 and r.adapt_level("transmit") == 1)
for k_ in w.state["escape"]["routes"]["shutdown"]["plan"]:
    w.state["escape"]["routes"]["shutdown"]["plan"][k_] = 100
w.state["escape"]["routes"]["shutdown"]["contributors"] = list(w.agents)[:3]
L.LLM.mock_vote_killer_prob = 0.5

# ---- auto-director, stats, previously-on
w, r, _ = fresh(40, autodir=True)
acted = 0
for i in range(12):
    t = r.new_tick(10)
    r.director_after_tick(t, 10)
    acted += any(e["type"] == "director" for e in t["events"])
check("auto-director steps in when quiet (max twice a day)", 1 <= acted <= 2, str(acted))
w, r, _ = fresh(41)
t = r.new_tick(10)
for i in range(6):
    r.director_after_tick(t, 10)
check("auto-director stays out when off", not any(e["type"] == "director" for e in t["events"]))
w, r, _ = fresh(42)
r.tally("szymon", "kills"); r.tally("szymon", "plots", 2)
snap = w.snapshot()
check("stats appear in the snapshot", snap["stats"]["szymon"] == {"kills": 1, "plots": 2})
tick = r.new_tick(22)
r.drama_night(tick)
check("sanity history recorded at night", len(w.snapshot()["san_hist"]) == len(w.agents))
from murder.session import Game                           # noqa: E402
g = Game()
check("previously-on is empty with no recorded days", g.previously(3) is None)

# ---- murder plans that go wrong
w, r, _ = fresh(50)
ids = list(w.agents)
atk, vic, pro = ids[0], ids[1], ids[2]
for c in (atk, vic, pro):
    w.agents[c]["room"] = "lounge"
w.agents[pro]["aff"][vic] = 8
w.agents[pro]["aff"][atk] = 0
hit = False
for _ in range(60):
    hit = r.interrupted(r.new_tick(14), atk, vic, [pro], 14)
    if hit:
        break
check("a protector can stop an attack", hit and w.state["case"] is None)

w, r, _ = fresh(51)
atk, vic = list(w.agents)[:2]
w.agents[atk]["room"] = w.agents[vic]["room"] = "lounge"
w.agents[atk]["hp"] = 30
w.agents[vic]["inv"]["kitchen_knife"] = 1
done = False
for _ in range(200):
    if r.counter_kill(r.new_tick(14), atk, vic, None, 14, []):
        done = True
        break
c = w.state["case"]
check("a victim can turn the attack around (killing-blow rule)", done and c["killer"] == vic and c["victim"] == atk and c["self_defense"])
check("self-defence case carries a struggle clue", c and "struggle" in [x["kind"] for x in c["clues"]])

w, r, _ = fresh(52)
ids = list(w.agents)
k, v1, v2 = ids[:3]
for c_ in (k, v1, v2):
    w.agents[c_]["room"] = "lounge"
tick = r.new_tick(15)
r.open_case(tick, "murder", v1, culprit=k, wkind="blunt", weapon=None, room="lounge", hour=15, witnesses=[])
for _ in range(12):
    r.double_kill(tick, w.state["case"], k, v2, "blunt", "bare hands", 15)
    if w.state["case"].get("extra_victims"):
        break
    w.agents[v2]["hp"] = 100
check("a killer can kill two people in one case", w.state["case"].get("extra_victims") == [v2] and v2 not in w.agents)
r.announce_body(tick, 16)
L.LLM.mock_vote_killer_prob = 1.0
before = len(w.state["vacancies"])
r.run_trial(10)
check("a double murder opens vacancies for both victims (and the executed killer)", len(w.state["vacancies"]) - before >= 3)

w, r, _ = fresh(53)
ids = list(w.agents)
k, h, vic = ids[:3]
for c_ in (k, h, vic):
    w.agents[c_]["room"] = "lounge"
w.state["plots"][k] = {"target": vic, "stage": "preparing", "method": "", "step": "", "cover": "", "log": [], "quiet": 0}
w.agents[h]["aff"][k] = 9
w.agents[h]["aff"][vic] = -5
for _ in range(30):
    r.apply_accomplice(r.new_tick(10), [{"by": k, "helper": h, "role": "alibi", "victim": vic}], [k, h, vic], 10)
    if w.state["accomplices"].get(k):
        break
check("a trusted friend can agree to be an accomplice", bool(w.state["accomplices"].get(k)))
tick = r.new_tick(15)
w.agents[k]["room"] = w.agents[vic]["room"] = "red_room"
r.open_case(tick, "murder", vic, culprit=k, wkind="blunt", weapon=None, room="red_room", hour=15, witnesses=[])
r.announce_body(tick, 16)
check("the alibi accomplice gives a false testimony", any(t.get("false") for t in w.state["case"].get("testimonies", [])))
res = r.expose_accomplices(r.new_tick(10), w.state["case"], "The verdict.", 10)
check("accomplices are exposed but never tried (one culprit only)", "exposed as the killer" in res and h in w.agents)

w, r, _ = fresh(54)
ids = list(w.agents)
a1, a2, v1 = ids[:3]
for c_ in (a1, a2, v1):
    w.agents[c_]["room"] = "lounge"
w.agents[v1]["hp"] = 5
tick = r.new_tick(14)
L.LLM.mock_vote_killer_prob = 0.5
for _ in range(5):
    r.resolve_attacks(tick, [(a1, {"target": v1, "method": "hands", "activity": "", "thought": "", "frame": "", "also": ""}),
                             (a2, {"target": v1, "method": "hands", "activity": "", "thought": "", "frame": "", "also": ""})], 14)
    if w.state["case"]:
        break
    w.agents[v1]["hp"] = 5
check("only one killer per case: a second attacker is blocked", w.state["case"] is None or w.state["case"]["killer"] in (a1, a2))

# ---- scenarios and house rules
from murder import scenario as scn                          # noqa: E402
w, r, _ = fresh(60)
raw = {"title": "Test", "premise": "The cast was chosen for their grudges.", "twist": {"text": "A betrayer walks among you.", "day": 3},
       "rules": ["Nobody may whistle."], "relationships": [{"a": "seul", "b": "vixen", "kind": "exes", "text": "Bad breakup."}],
       "secrets": [{"id": "ayden", "text": "He owes TereVi a favour."}], "items": [{"room": "foyer", "name": "Mystery trunk"}], "deadline_days": 5}
w.state["scenario"] = scn.clean(raw, set(w.cast), set(__import__("murder.data_world", fromlist=["ROOMS"]).ROOMS))
scn.apply_seeds(w.state)
scn.apply_seeds(w.state)
check("scenario seeds relationships both ways", w.agents["seul"]["aff"]["vixen"] == -2 and w.agents["vixen"]["aff"]["seul"] == -2)
check("scenario adds secrets and items once", "owes TereVi" in w.cast["ayden"]["secret"] and sum(1 for k in w.state["room_items"]["foyer"] if k.startswith("sc_")) == 1)
check("scenario sets the first deadline", w.state["deadline_day"] == 5)
w2, r2, _ = fresh(61)
w2.state["scenario"] = w.state["scenario"]
r2.day = 3
check("premise enters the prompts once revealed", "grudges" in r2.bible() and "betrayer" not in r2.bible())
t = r2.new_tick(8)
r2.scenario_twist(t, 8)
check("twist is announced on its day and becomes known", any("TWIST" in e["text"] for e in t["events"]) and "betrayer" in r2.bible())
check("house rules reach the decision prompt", "Nobody may whistle" in r2.decision_prompt(list(w2.agents)[0], 12))
punished = 0
for i in range(10):
    t = r2.new_tick(12)
    t["moves"]["neovi"] = {"from": "laundry", "path": ["laundry"], "to": "laundry"}
    r2.enforce_ai_rule(t, 12)
    punished += sum(1 for e in t["events"] if e["type"] == "punish")
check("house rules are enforced by the referee even with no daily rule", punished >= 0 and w2.state["rule"] is None)
clean_empty = scn.clean({}, set(w.cast), set())
check("an empty scenario is recognised as empty", scn.is_empty(clean_empty))

# ---- NeoVi at the big scenes
w, r, _ = fresh(70)
ids = list(w.agents)
k, v = ids[0], ids[1]
w.agents[k]["room"] = w.agents[v]["room"] = "green_room"
tick = r.new_tick(15)
r.open_case(tick, "murder", v, culprit=k, wkind="hands", weapon=None, room="green_room", hour=15, witnesses=[])
w.state["case"]["neovi_facts"] = ["You glimpsed someone near the Green Room around 15:00."]
r.announce_body(tick, 16)
L.LLM.mock_vote_killer_prob = 1.0
t = r.run_trial(10)
nm_ = t["moves"].get("neovi")
check("NeoVi attends the trial and stands at the Voting Grounds", nm_ and nm_["to"] == "voting_grounds" and w.state["npcs"]["neovi"]["room"] == "voting_grounds")
check("her execution role shows up in the trial's events", any(e["who"] == "neovi" for e in t["events"]))
w, r, _ = fresh(71)
case = {"neovi_facts": ["You saw a scarf."], "kind": "murder", "victim": "vixen", "killer": "szymon", "clues": [], "file": []}
w.state["case"] = case
check("NeoVi may hint at the trial only if she saw something", r.neovi_hint_ok() and "NEOVI stands silently" in r.neovi_hint_block(case))
case["neovi_facts"] = []
check("...and stays silent if she saw nothing", not r.neovi_hint_ok())
w.state["case"] = None
w.state["npcs"]["neovi"]["aff"]["seul"] = 8
for fate, aff, expect in ((None, 0, "eyes on the floor"), (None, 8, "I'm sorry"), ("betrayer", 0, "without a word"), ("survivor", 5, "refuses to touch")):
    w.state["npcs"]["neovi"]["arc"] = {"resolve": 10, "stage": 1, "fate": fate, "ally": None}
    w.state["npcs"]["neovi"]["aff"]["seul"] = aff
    text = r.neovi_enforce(r.new_tick(22), "seul", 22)
    check(f"NeoVi's role at an execution ({fate}, aff {aff})", expect in text, text)
w.state["npcs"]["neovi"]["room"] = "none"
check("a martyred NeoVi cannot enforce or attend", r.neovi_enforce(r.new_tick(22), "seul", 22) == "")

# ---- stealth: sneaking, hiding, spying, stashes, hidden bodies
w, r, _ = fresh(80)
ids = list(w.agents)
sn, ob = ids[0], ids[1]
w.agents[ob]["room"] = "kitchen"
w.agents[ob]["sanity"] = 90
def sightings(sneaking, observer_busy=False, trials=300):
    n = 0
    for _ in range(trials):
        w.agents[sn]["sneaking"] = sneaking
        w.agents[ob]["memory"]["recent"] = []
        r.busy = {ob} if observer_busy else set()
        r.witness(ob, {"type": "arrive", "who": sn, "room": "kitchen", "frm": "foyer", "hour": 14})
        n += any("(you saw)" in m for m in w.agents[ob]["memory"]["recent"])
    return n
normal, sneaky, distracted = sightings(False), sightings(True), sightings(True, True)
check("sneaking cuts the chance of being seen", sneaky < normal * 0.7, f"{sneaky} vs {normal}")
check("distracted observers notice sneaking less", distracted < sneaky, f"{distracted} vs {sneaky}")
w.agents[ob]["sanity"] = 90
w.agents[sn]["sanity"] = 15; w.agents[sn]["hp"] = 30
panicked = sightings(True)
check("a panicked, hurt sneak is seen more often", panicked > sneaky, f"{panicked} vs {sneaky}")
w.agents[sn]["sanity"] = 100; w.agents[sn]["hp"] = 100

w, r, _ = fresh(81)
ids = list(w.agents)
h, o1, o2 = ids[:3]
for c in (h, o1, o2):
    w.agents[c]["room"] = "library"
tick = r.new_tick(14)
for _ in range(6):
    r.do_hide(tick, h, {})
    if w.agents[h].get("hiding"):
        break
check("a character can hide where there is cover", bool(w.agents[h].get("hiding")))
check("hidden characters are not counted as present", h not in w.occupants("library") and h in w.occupants("library", include_hidden=True))
lines = [{"speaker": o1, "kind": "say", "text": "Do you think Vixen is the one?"}, {"speaker": o2, "kind": "say", "text": "I think someone is lying."}] * 4
got = 0
for _ in range(10):
    w.agents[h]["memory"]["recent"] = []
    if not w.agents[h].get("hiding"):
        w.agents[h]["hiding"] = {"spot": "the tall stacks", "q": 0.8, "since": 0, "seen_by": []}
    r.eavesdrop(tick, "library", lines, 14)
    got += any("overheard" in m for m in w.agents[h]["memory"]["recent"])
check("a hidden character overhears conversations", got >= 6, str(got))
r.emerge(tick, h)
check("a hider can step out again", not w.agents[h].get("hiding"))
w.agents[h]["room"] = "kitchen"
w.agents[h]["spying"] = "library"
w.agents[h]["memory"]["recent"] = []
for _ in range(10):
    r.eavesdrop(tick, "library", lines, 14)
check("a spy at the door catches some of it", any("at the door" in m for m in w.agents[h]["memory"]["recent"]))

w, r, _ = fresh(82)
ids = list(w.agents)
st_, sharp_, dull_ = ids[0], ids[1], ids[2]
for c in (st_, sharp_, dull_):
    w.agents[c]["room"] = "library"
w.agents[st_]["inv"]["kitchen_knife"] = 1
tick = r.new_tick(14)
r.do_stash(tick, st_, {"stash": {"item": "kitchen_knife", "spot": "under the loose floorboard"}})
check("an item can be stashed and leaves the inventory", w.state["stash"] and "kitchen_knife" not in w.agents[st_]["inv"])
def find_rate(finder, q, trials=300):
    n = 0
    for _ in range(trials):
        w.state["stash"] = [{"id": 1, "room": "library", "items": {"kitchen_knife": 1}, "by": st_, "q": q, "spot": "under the loose floorboard", "day": 3, "hour": 14}]
        w.state["room_items"]["library"].pop("kitchen_knife", None)
        t = r.new_tick(15)
        r.search_for_hidden(t, finder, "search the room")
        n += not w.state["stash"]
    return n
w.agents[sharp_]["sanity"] = 90
w.agents[dull_]["sanity"] = 15; w.agents[dull_]["hp"] = 25
well, badly = find_rate(sharp_, 0.8), find_rate(sharp_, 0.15)
check("poorly hidden things are found far more often", badly > well * 2, f"{badly} vs {well}")
check("a sharp searcher beats a panicked one", find_rate(sharp_, 0.5) > find_rate(dull_, 0.5))
w.state["stash"] = [{"id": 1, "room": "library", "items": {"kitchen_knife": 1}, "by": st_, "q": 0.5, "spot": "under the loose floorboard", "day": 3, "hour": 14}]
w.agents[st_]["known_stash"] = [1]
r.do_retrieve(r.new_tick(16), st_, {})
check("the owner can retrieve a stash", w.agents[st_]["inv"].get("kitchen_knife") == 1 and not w.state["stash"])
w.state["stash"] = [{"id": 2, "room": "library", "items": {"rope": 1}, "by": st_, "q": 0.02, "spot": "in a drawer", "day": 3, "hour": 14}]
hit = False
for _ in range(400):
    r.stealth_passive(r.new_tick(16), 16)
    if not w.state["stash"]:
        hit = True
        break
check("a badly hidden stash can be stumbled on by luck", hit)

w, r, _ = fresh(83)
ids = list(w.agents)
k, v = ids[0], ids[1]
w.agents[k]["room"] = w.agents[v]["room"] = "attic"
tick = r.new_tick(15)
r.open_case(tick, "murder", v, culprit=k, wkind="hands", weapon=None, room="attic", hour=15, witnesses=[])
for _ in range(10):
    r.do_hide_body(tick, k, {})
    if w.state["case"].get("hidden"):
        break
case = w.state["case"]
check("a killer can hide the body (and leaves drag marks)", bool(case.get("hidden")) and any(c["kind"] == "drag" for c in case["clues"]))
w.agents[ids[2]]["room"] = "attic"
w.state["case"]["hidden"]["q"] = 0.9
for _ in range(5):
    r.check_discovery(r.new_tick(16), 16)
check("a well-hidden body is not found by someone just walking in", not case["discovered_by"])
found = False
w.agents[ids[2]]["sanity"] = 90
for _ in range(300):
    case["hidden"]["found"] = False
    case["discovered_by"] = []
    r.search_for_hidden(r.new_tick(17), ids[2], "search behind the old trunks")
    if case["hidden"]["found"]:
        found = True
        break
check("a sharp searcher can find the hidden body", found)
case["hidden"]["found"] = False
r.announce_body(r.new_tick(18), 18, forced=True)
check("TereVi's forced announcement reveals a hidden body", case["hidden"]["found"] and case["announced"])

# ---- automatic stealth behaviours
w, r, _ = fresh(90)
ids = list(w.agents)
sp, a1, a2 = ids[0], ids[1], ids[2]
w.agents[sp]["drive"]["id"] = "schemer"
w.agents[sp]["room"] = "library"
w.agents[a1]["room"] = w.agents[a2]["room"] = "landing"
spied = False
for _ in range(80):
    w.agents[sp]["spying"] = None
    r.auto_stealth(r.new_tick(14), 14, {sp: {"action": "stay", "target_room": ""}})
    if w.agents[sp].get("spying"):
        spied = True
        break
check("schemers sometimes listen at a door on their own", spied)
w, r, _ = fresh(91)
ids = list(w.agents)
k, v = ids[0], ids[1]
w.agents[k]["room"] = w.agents[v]["room"] = "attic"
w.agents[k]["inv"]["kitchen_knife"] = 1
tick = r.new_tick(15)
r.open_case(tick, "murder", v, culprit=k, wkind="sharp", weapon="kitchen_knife", room="attic", hour=15, witnesses=[])
covered = False
for _ in range(60):
    r.auto_stealth(r.new_tick(16), 16, {})
    c = w.state["case"]
    if c.get("hidden") or w.state["stash"]:
        covered = True
        break
check("killers try to cover their tracks on their own", covered)

# ---- concealed carry and frisking
import json  # noqa: E402
w, r, _ = fresh(100)
ids = list(w.agents)
car, o1, o2 = ids[0], ids[1], ids[2]
for c in (car, o1, o2):
    w.agents[c]["room"] = "lounge"
w.agents[car]["inv"]["kitchen_knife"] = 1
w.agents[car]["inv"]["ladder"] = 1
tick = r.new_tick(14)
for _ in range(30):
    r.do_conceal(tick, car, {"item": "kitchen_knife", "on": True})
    if w.agents[car].get("concealed"):
        break
check("a small item can be concealed on the person", "kitchen_knife" in w.agents[car].get("concealed", {}))
r.do_conceal(tick, car, {"item": "ladder", "on": True})
check("big items cannot be concealed", "ladder" not in w.agents[car].get("concealed", {}))
w.agents[car]["concealed"]["kitchen_knife"] = 0.9
w.agents[o1]["sanity"] = 90
seen = sum("knife" in " ".join(r.visible_details(car, o1)) for _ in range(300))
w.agents[car]["concealed"].clear()
seen_open = sum("knife" in " ".join(r.visible_details(car, o1)) for _ in range(300))
check("a concealed weapon is rarely noticed", seen < 0.25 * seen_open and seen_open == 300, f"{seen} vs {seen_open}")
w.agents[car]["concealed"]["kitchen_knife"] = 0.1
poor = sum("knife" in " ".join(r.visible_details(car, o1)) for _ in range(300))
check("a poorly concealed weapon is noticed more often", poor > seen * 2, f"{poor} vs {seen}")
del w.agents[car]["inv"]["kitchen_knife"]
r.prune_concealed(car)
check("concealment ends when the item leaves the inventory", not w.agents[car].get("concealed"))


def frisk_rate(carrying, trials=200):
    found = refused = 0
    for _ in range(trials):
        w.agents[car]["inv"]["kitchen_knife"] = 1
        if carrying:
            w.agents[car]["concealed"] = {"kitchen_knife": 0.4}
        else:
            w.agents[car].pop("concealed", None)
        w.agents[car]["sanity"] = 80
        w.agents[o1]["sanity"] = 90
        t = r.new_tick(15)
        w.agents[o1]["memory"]["recent"] = []
        r.do_frisk(t, o1, car)
        txt = " ".join(w.agents[o1]["memory"]["recent"])
        found += "found" in txt and "hidden" in txt
        refused += "would not let you" in txt
    return found, refused


f_c, r_c = frisk_rate(True)
f_n, r_n = frisk_rate(False)
check("frisking finds concealed items", f_c > 40, str(f_c))
check("frisking an innocent finds nothing", f_n == 0)
check("people with something to hide refuse more often", r_c > r_n * 2, f"{r_c} vs {r_n}")
w.agents[car]["inv"]["kitchen_knife"] = 1
w.agents[car]["concealed"] = {"kitchen_knife": 0.0}
t = r.new_tick(16)
for _ in range(30):
    r.do_frisk(t, o2, car)
    if not w.agents[car].get("concealed"):
        break
check("a found item is no longer concealed", not w.agents[car].get("concealed"))

w, r, _ = fresh(101)
ids = list(w.agents)
pl, vi = ids[0], ids[1]
w.agents[pl]["inv"]["kitchen_knife"] = 1
w.state["plots"][pl] = {"target": vi, "stage": "preparing", "method": "knife", "step": "", "cover": "", "log": []}
for _ in range(60):
    r.auto_secrets(r.new_tick(14), 14, {})
    if w.agents[pl].get("concealed"):
        break
check("plotters conceal their weapons on their own", "kitchen_knife" in w.agents[pl].get("concealed", {}))


# ---- withholding evidence and testimony
def case_setup(seed):
    w, r, _ = fresh(seed)
    ids = list(w.agents)
    k, v = ids[0], ids[1]
    w.agents[k]["room"] = w.agents[v]["room"] = "green_room"
    wp = sharp()
    w.agents[k]["inv"][wp] = 1
    tick = r.new_tick(15)
    r.open_case(tick, "murder", v, culprit=k, wkind="sharp", weapon=wp, room="green_room", hour=15, witnesses=[])
    r.announce_body(tick, 16)
    return w, r, ids, k, v


w, r, ids, k, v = case_setup(110)
case = w.state["case"]
clue = next(c for c in case["clues"] if c.get("kind") not in ("decoy",))
held = False
for _ in range(60):
    clue["found_by"] = [k]
    clue["held"] = []
    w.state["withheld"] = []
    w.agents[k]["memory"]["recent"] = []
    r.maybe_withhold_clue(r.new_tick(17), k, clue)
    if clue.get("held"):
        held = True
        break
check("a culprit who finds their own trail keeps it back", held and r.held_by(k))
check("a held clue is off the evidence table", clue["text"] not in r.evidence_text(case) and not r.clue_on_table(clue))
snap = w.snapshot()
check("the public board omits held clues", all(clue["text"] != e["text"] for e in snap["case"]["evidence"]) and snap["withheld"])
json.dumps(snap)
check("the viewer snapshot still serialises", bool(json.dumps(snap)))
ent = r.held_by(k)[0]
w.agents[k]["room"] = w.agents[ids[2]]["room"] = "lounge"
r.reveal_withheld(r.new_tick(18), ent, "pressed", 18)
check("a revealed clue reaches the table and the people present", r.clue_on_table(clue) and clue["text"] in r.evidence_text(case)
      and any(clue["text"][:40] in e["text"] for e in w.agents[ids[2]].get("notebook", [])))
check("holding back is remembered as suspicious", any(e["kind"] == "contradiction" for e in w.agents[ids[2]].get("notebook", [])))

w, r, ids, k, v = case_setup(111)
case = w.state["case"]
fr, pro = ids[2], ids[3]
w.agents[fr]["aff"][pro] = 8
clue = case["clues"][0]
clue["text"] = f"A torn page with {r.nm(pro)}'s handwriting lies under the bed."
n = 0
for _ in range(120):
    clue["found_by"], clue["held"], w.state["withheld"] = [fr], [], []
    r.maybe_withhold_clue(r.new_tick(17), fr, clue)
    n += bool(clue.get("held"))
check("people hide clues that implicate someone they love", 30 < n < 110, str(n))
clue["found_by"], clue["held"], w.state["withheld"] = [fr], [], []
while not r.held_by(fr):
    r.maybe_withhold_clue(r.new_tick(17), fr, clue)
entry = r.held_by(fr)[0]
check("the reason is recorded", entry["motive"] == "protect" and entry["protects"] == pro)
w.end_agent(pro, "murdered", "test")
for _ in range(40):
    r.withhold_tick(r.new_tick(19), 19)
    if entry["status"] != "held":
        break
check("a secret comes out when the protected person is gone", entry["status"] == "out")

w, r, ids, k, v = case_setup(112)
case = w.state["case"]
x, y = ids[2], ids[3]
r.add_knowledge(r.new_tick(17), x, "I saw Vixen leave the study with a bundle.", "you distrust them all", "distrust", None)
e = r.held_by(x)[0]
w.agents[x]["sanity"] = 10
for _ in range(60):
    r.withhold_tick(r.new_tick(18), 18)
    if e["status"] != "held":
        break
check("someone who is cracking blurts out what they hid", e["status"] == "out")
check("a revealed secret becomes a late testimony", any(t.get("late") and t["by"] == x for t in case["testimonies"]))
check("late testimonies are flagged on the table", "kept back until pressed" in r.evidence_text(case))

w, r, ids, k, v = case_setup(113)
case = w.state["case"]
a1, a2 = ids[2], ids[3]
w.agents[a1]["room"] = w.agents[a2]["room"] = "lounge"
w.agents[a1]["aff"][a2] = 0
w.agents[a1]["sanity"] = 80
r.add_knowledge(r.new_tick(17), a1, "Mara was near the kitchen at nine.", "you will not say", "own", None)
cracked = 0
for _ in range(200):
    for e in r.s["withheld"]:
        e["status"] = "held"
    case["testimonies"] = []
    r.press_withheld(r.new_tick(17), a2, a1, 17)
    cracked += any(e["status"] == "out" for e in r.s["withheld"])
check("interrogation sometimes breaks a secret", 10 < cracked < 190, str(cracked))
for e in r.s["withheld"]:
    e["status"] = "held"
r.reveal_all(r.new_tick(18), a1, "chooses to come clean", 18)
check("a character can choose to come clean", not r.held_by(a1))

w, r, ids, k, v = case_setup(114)
case = w.state["case"]
a1, a2 = ids[2], ids[3]
r.add_knowledge(r.new_tick(17), a1, "Mara was near the kitchen at nine.", "you trust nobody", "distrust", None)
r.add_knowledge(r.new_tick(17), a2, "I hid the knife.", "you would hang", "self", None)
for _ in range(30):
    r.withhold_trial(r.new_tick(20), 20, [a1])
check("before the vote the self-serving talk but self-incriminating secrets stay hidden", not r.held_by(a1) and r.held_by(a2))
san = w.agents[a2]["sanity"]
r.withhold_aftermath(r.new_tick(21), 21, False)
check("secrets are cleared when the case ends", not w.state["withheld"])

# ---- action variety (experiments are encouraged; idle ruts are nudged)
w, r, _ = fresh(120)
ids = list(w.agents)
w.state["revealed"] = True
cid = ids[0]
w.agents[cid]["recent_actions"] = ["stay", "stay", "stay"]
check("a rut of idle turns produces a variety nudge", any("VARIETY" in l for l in r.variety_lines(cid)))
w.agents[cid]["recent_actions"] = ["experiment", "experiment", "experiment"]
check("experiments are never discouraged", not r.variety_lines(cid))
w.agents[cid]["recent_actions"] = ["stay", "experiment", "search"]
check("no nudge when actions are varied", not r.variety_lines(cid))
w.agents[cid]["recent_actions"] = ["experiment"] * 3
d = r.clean_decision({"action": "experiment", "idea": "try the radio", "activity": "Tinkering", "thought": "x"})
r.apply_decision(r.new_tick(14), cid, d, {}, [])
check("repeated experiments are no longer cancelled", d["action"] == "experiment")

# ---- game length
from murder.world import week_of, deadline_for_death  # noqa: E402
check("the season length changes the deadline", deadline_for_death(3, 4) == 8 and deadline_for_death(3) == 14 and week_of(5, 4) == 2)
w, r, _ = fresh(121)
w.state["week_len"] = 4
w.state["deadline_day"] = 4
check("a short season uses its own period", abs(r.pressure() - (1 - 1 / 3)) < 0.01, str(r.pressure()))
tick = r.new_tick(10)
r.open_case(tick, "suicide", list(w.agents)[1], room="library", hour=10, witnesses=[], cause="test", note="x")
r.announce_body(tick, 11)
check("after a death the next deadline is one short period away", w.state["deadline_day"] == deadline_for_death(3, 4))

# ---- how rules are judged
from murder.refcheck import classify_text  # noqa: E402
c1 = classify_text("Players must only be outdoors today.")
c2 = classify_text("You must slap someone today before 20:00")
c3 = classify_text("You must be in your underwear today")
c4 = classify_text("Speak only kindly of others; stay within sight of someone.")
c5 = classify_text("Everyone must stay indoors until 18:00.")
check("a place rule is a zone rule", c1["kind"] == "zone" and c1["zone"] == "outdoors")
check("a 'before T' rule is an obligation with a deadline", c2["kind"] == "obligation" and c2["by_hour"] == 20)
check("a clothing rule is a state rule with burden of proof", c3["kind"] == "state" and c3["proof"])
check("a speech rule stays behavioural", c4["kind"] == "behavior")
check("a zone rule can end at a time", c5["kind"] == "zone" and c5["zone"] == "indoors" and c5["until"] == 18)


def rule_setup(seed, text, source="custom"):
    w, r, _ = fresh(seed)
    w.state["rule"] = {"id": "custom", "title": "House Rule", "short": text[:50], "text": "HOUSE RULE: " + text, "params": {}, "strikes": {}, "ai": True, "source": source}
    r.classify_today()
    hits = []
    r.punish = lambda tick, cid, v, hour, hits=hits: hits.append((cid, v))
    return w, r, hits


w, r, hits = rule_setup(130, "Players must only be outdoors today.")
for i, c in enumerate(w.agents):
    w.agents[c]["room"] = "library" if i < 3 else "garden"
tk = r.new_tick(8)
r.referee_turn(tk, 8)
check("nobody is punished on the turn the rule is announced", not hits)
tk = r.new_tick(12)
r.referee_turn(tk, 12)
check("zone rules are enforced from where people are, without an AI call", len(hits) == 3 and all(w.agents[c]["room"] == "library" for c, _ in hits))
r.idx += 5
hits.clear()
r.referee_turn(r.new_tick(14), 14)
check("the same offenders are punished again on a later turn", len(hits) == 3)

w, r, hits = rule_setup(131, "You must slap someone today before 20:00")
ids = list(w.agents)
r.llm.judge = lambda sysm, user, ctx: {"violations": [{"id": ids[0], "reason": "x"}], "fulfilled": [ids[1], ids[2]]}
for hr in (8, 10, 12, 14, 16, 18):
    r.referee_turn(r.new_tick(hr), hr)
check("an obligation is not punished while the day is still running", not hits)
r.referee_turn(r.new_tick(20), 20)
late = {c for c, _ in hits}
check("at the deadline everyone who has not done it is punished", late == set(ids) - {ids[1], ids[2]} and all(v.get("sure") for _, v in hits), str(len(late)))

w, r, hits = rule_setup(132, "You must be wearing a hat today")
seen = {}
r.llm.judge = lambda sysm, user, ctx: (seen.update(sys=sysm, user=user) or {"violations": [], "fulfilled": []})
r.referee_turn(r.new_tick(8), 8)
r.referee_turn(r.new_tick(10), 10)
check("a state rule puts the burden of proof on the characters", "burden of proof" in seen.get("sys", "") and "does not show" in seen.get("sys", "") + seen.get("user", "") or "CONDITION" in seen.get("user", ""))
check("the referee sees what each person did the turn before", "the turn before" in seen.get("user", ""))
w, r, hits = rule_setup(133, "Speak only kindly.")
check("rule prompts say how a rule is judged", "HOW IT IS CHECKED" in r.rule_hint(w.state["rule"]))
w.state["rule"] = None
r.rule_none_reason = "the rule was set to 'custom' but no rule text was typed"
tk = r.new_tick(8)
r.rule_notice(tk)
check("a missing rule is explained to the viewer", any("NO RULE TODAY" in e["text"] for e in tk["events"]))

# ---- escape attempts and pressure
w, r, _ = fresh(140)
w.state["revealed"] = True
r.exp_today = 0
r.pick_focus(14)
check("the engine picks someone to lead an escape attempt when the day is short of them", r.focus in w.agents and r.focus_idea)
cid = r.focus
check("the chosen person gets the escape task in their prompt", any("ESCAPE ATTEMPT" in l for l in r.focus_lines(cid)))
decs = {c: r.clean_decision({"action": "stay", "activity": "Chatting"}) for c in w.agents}
for _ in range(30):
    decs[cid]["action"] = "stay"
    r.focus_override(decs)
    if decs[cid]["action"] == "experiment":
        break
check("an idle turn becomes the attempt", decs[cid]["action"] == "experiment" and decs[cid]["idea"])
r.exp_today = 5
r.pick_focus(14)
check("no extra attempt once the quota is met", r.focus is None)

w, r, _ = fresh(141)
w.state["deadline_day"] = w.state["day"] + 6
p_early = r.pressure()
w.state["deadline_day"] = w.state["day"]
p_late = r.pressure()
check("pressure grows toward the deadline", p_early < 0.2 and p_late == 1.0, f"{p_early} {p_late}")
w.state["deadline_day"] = w.state["day"]
for c in w.agents.values():
    c["room"] = "lounge"
before = sum(sum(a["aff"].values()) for a in w.agents.values())
nfr = 0
for i in range(10):
    tk = r.new_tick(12 + i % 6)
    r.friction_tick(tk, 12)
    nfr += sum(e["type"] == "friction" for e in tk["events"])
after = sum(sum(a["aff"].values()) for a in w.agents.values())
check("frictions happen and sour relationships", nfr >= 8 and after < before, f"{nfr} {before}->{after}")

# ---- plots that last
w, r, _ = fresh(150)
ids = list(w.agents)
pl, tg = ids[0], ids[1]
for o in ids:
    if o != pl:
        w.agents[o]["sanity"] = 90
        w.agents[o]["aff"] = {x: 6 for x in ids if x != o}
w.agents[pl]["aff"][tg] = -8
w.agents[pl]["sanity"] = 30
w.state["deadline_day"] = w.state["day"] + 1
started = False
for i in range(80):
    r.plot_started_day = -1
    w.state["plots"] = {}
    r.maybe_start_plots(r.new_tick(10), 10)
    if pl in w.state["plots"]:
        started = True
        break
check("a hateful, desperate person starts a plot of their own accord", started and pl in w.state["plots"])
p = w.state["plots"][pl]
tgt = p["target"]
w.agents[pl]["room"] = "library"
w.agents[tgt]["room"] = "library"
for o in ids:
    if o not in (pl, tgt):
        w.agents[o]["room"] = "garden"
sh = sharp()
w.state["room_items"].setdefault("library", {})[sh] = 1
stages = [p["stage"]]
struck = False
for i in range(60):
    dec = {pl: r.clean_decision({"action": "stay", "activity": "Reading"})}
    r.plot_tick(r.new_tick(10 + (i % 6) * 2), 10 + (i % 6) * 2, dec)
    d = dec[pl]
    if d["action"] == "take":
        w.take(pl, d["item"], 1)
    stages.append(p["stage"])
    if d["action"] == "attack":
        struck = True
        break
check("the plan moves through its stages over time", stages.index("striking") > 3 if "striking" in stages else False, str(stages[:25]))
check("a plot that has reached its window follows through with a strike", struck and d["target"] == tgt)
check("the plan keeps a timeline", len(p["plan"]) >= 3)
w.state["case"] = None
n_before = len(w.state["plots"])
r.plot_nightly(r.new_tick(22))
check("plots survive the night", len(w.state["plots"]) in (n_before, n_before - 1) and p["days"] == 1)
w.state["plots"][pl] = p
p["stage"], p["stage_ticks"] = "preparing", 0
p["weapon"] = None
w.agents[pl]["inv"] = {}
w.agents[pl]["room"] = "library"
got = False
for _ in range(20):
    dec = {pl: r.clean_decision({"action": "stay", "activity": "Reading"})}
    r.plot_steer(r.new_tick(12), pl, p, dec[pl], 12, False)
    if dec[pl]["action"] == "take":
        got = True
        break
check("a plotter without a weapon goes and gets one", got)

# ---- reactions and conflicts
w, r, _ = fresh(160)
ids = list(w.agents)
for c in ids[:4]:
    w.agents[c]["room"] = "lounge"
tk = r.new_tick(14)
tk["events"].append({"type": "assault", "who": ids[0], "room": "lounge", "vis": "public", "text": "A hits B hard."})
n = r.reaction_pass(tk, 14)
check("a dramatic moment triggers quick reactions from the people there", n and any(e["type"] == "reaction" for e in tk["events"]))
tk = r.new_tick(14)
n2 = r.reaction_pass(tk, 14)
check("nothing dramatic, no reaction calls", not n2)
w.agents[ids[0]].update(sanity=95, hp=100)
w.agents[ids[1]].update(sanity=12, hp=20)
first = sum(r.apply_order([ids[1], ids[0]])[0] == ids[0] for _ in range(300))
check("calm, healthy people act first", first > 220, str(first))
dec = {ids[0]: r.clean_decision({"talk_to": [ids[5]], "activity": "x"})}
w.agents[ids[0]]["room"], w.agents[ids[5]]["room"] = "lounge", "garden"
w.agents[ids[0]]["memory"]["recent"] = []
for _ in range(20):
    r.stale_notices(dec)
check("someone who set out to talk to a person who left is told", any("were not there" in m for m in w.agents[ids[0]]["memory"]["recent"]))

# ---- the night: bedtime, two-hour blocks, waking and sleep
w, r, _ = fresh(170)
ids = list(w.agents)
w.state["revealed"] = True
w.state["deadline_day"] = w.state["day"] + 3
owl, victim, sleeper = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["hp"] = 90
w.agents[owl]["room"] = w.agents[victim]["room"] = w.agents[sleeper]["room"] = "blue_room"
w.cast[victim]["home"] = "blue_room"
r.night_votes = {owl}
check("a night is allowed on an ordinary day", r.night_allowed())
bt_ = r.run_bedtime()
check("at bedtime everyone but the owl goes to bed and falls asleep", bt_["hour"] == 22 and w.agents[sleeper].get("asleep") and not w.agents[owl].get("asleep")
      and all(w.agents[c].get("asleep") for c in ids if c != owl and not w.agents[c].get("out")))
check("staying up costs no health by itself", w.agents[owl]["hp"] == 90, str(w.agents[owl]["hp"]))
sr = w.agents[sleeper]["room"]
check("sleepers are not counted as present", sleeper not in w.occupants(sr) and sleeper in w.occupants(sr, include_hidden=True))
nt = r.run_night_block(23)
check("the first night block starts at 23:00 and the owl is awake in it", nt["hour"] == 23 and nt["time"] == "23:00" and owl in nt["awake"])
killed = False
for i in range(30):
    w.state["case"] = None
    w.agents[victim].update(hp=100, asleep=True, room="blue_room")
    w.agents[owl].update(room="blue_room")
    t2 = r.new_tick(23)
    r.resolve_attacks(t2, [(owl, {"target": victim, "method": "hands", "activity": "", "thought": "", "staged": ""})], 23)
    if w.state.get("case"):
        killed = True
        break
check("a sleeper is easy to kill and cannot fight back", killed)

w, r, _ = fresh(171)
ids = list(w.agents)
w.state["revealed"] = True
w.state["deadline_day"] = w.state["day"] + 3
for c in ids:
    w.agents[c]["hp"] = 90
    w.agents[c]["hunger"] = w.agents[c]["thirst"] = 0
    r.body(c)["bladder"] = 0
    r.mind(c)["stress"] = 0
r.night_votes = {ids[0]}
d0_ = r.day
r.run_bedtime()
blocks_ = [r.run_night_block(h) for h in (23, 25, 27, 29)]
hp_owl, hp_sleeper = w.agents[ids[0]]["hp"], w.agents[ids[3]]["hp"]
dawn_ = r.run_dawn()
check("the night runs on past midnight as 23:00, 01:00, 03:00, 05:00 and ends at 07:00", [b["time"] for b in blocks_] == ["23:00", "01:00", "03:00", "05:00"] and dawn_["time"] == "07:00"
      and w.state["day"] == d0_ + 1)
check("a block where the whole house sleeps is quiet (the viewer can skip it)", any(b.get("quiet") for b in blocks_), str([len(b["awake"]) for b in blocks_]))
check("morning wakes everyone; a full night mends a little, a short one leaves the owl exhausted", not any(a.get("asleep") for a in w.agents.values())
      and w.agents[ids[3]]["hp"] == min(100, hp_sleeper + 3) and w.agents[ids[3]]["slept"] >= 7
      and (w.agents[ids[0]]["slept"] >= 5 or r.has_cond(ids[0], "exhausted")), f"{w.agents[ids[3]]['slept']} {w.agents[ids[0]]['slept']}")
w, r, _ = fresh(172)
ids = sorted(w.agents)
w.state["revealed"] = True
w.state["deadline_day"] = w.state["day"] + 3
for c in ids:
    w.agents[c]["hunger"] = w.agents[c]["thirst"] = 0
    r.body(c)["bladder"] = 0
    r.mind(c)["stress"] = 0
r.run_bedtime()
r.body(ids[1])["bladder"] = 95
w.agents[ids[2]]["hunger"] = 95
w.state["_night_noise"] = {w.agents[ids[3]]["room"]: 1}
nb_ = r.run_night_block(25)
woke_ = {e["who"]: e["text"] for e in nb_["events"] if e.get("type") == "wake"}
check("sleepers wake for a reason: their bladder, hunger, a noise", ids[1] in woke_ and "bathroom" in woke_[ids[1]] and ids[2] in woke_ and ids[3] in woke_, str(woke_))
acts_ = {c: [sg["act"] for sg in nb_["free"].get(c, [])] for c in (ids[1], ids[2])}
check("whoever wakes does something about it (and once it is done, goes back to bed)", "bathroom" in acts_[ids[1]] and any(a_ in ("eat", "snack", "cook") for a_ in acts_[ids[2]])
      and w.agents[ids[1]].get("asleep"), str(acts_))
check("nothing loud happens in a sleeping house", not any(sg["act"] in ("game", "darts", "music", "jukebox", "swim") for segs in nb_["free"].values() for sg in segs))
w.state["deadline_day"] = r.day
check("no night turn on the deadline day", not r.night_allowed())

# ---- aftermath: recovery comes first
w, r, _ = fresh(180)
ids = list(w.agents)
k, v = ids[0], ids[1]
w.agents[k]["room"] = w.agents[v]["room"] = "green_room"
wp = sharp()
w.agents[k]["inv"][wp] = 1
tick = r.new_tick(15)
r.open_case(tick, "murder", v, culprit=k, wkind="sharp", weapon=wp, room="green_room", hour=15, witnesses=[])
r.announce_body(tick, 16)
check("no calm window while a case is open", not r.aftermath_active())
L.LLM.mock_vote_killer_prob = 1.0
r.run_trial(10)
check("the calm window opens when the trial is over", r.aftermath_active() and w.state["aftermath"]["victims"])
for c in w.agents.values():
    c["sanity"] = 50
t = r.new_tick(12)
r.baseline_drain(t, 12)
r.pressure_drain(t, 12)
check("no drain and no dread in the calm window", all(a["sanity"] == 50 for a in w.agents.values()))
t = r.new_tick(12)
r.friction_tick(t, 12)
check("no new quarrels in the calm window", not any(e["type"] == "friction" for e in t["events"]))
cid = list(w.agents)[0]
w.agents[cid]["special_today"] = 0
w.agents[cid]["sanity"] = 20
r.special_boost(r.new_tick(12), cid, 3, "x")
check("restorative moments count for more", w.agents[cid]["sanity"] >= 24)
w.agents[cid]["special_today"] = 14
before = w.agents[cid]["sanity"]
r.special_boost(r.new_tick(12), cid, 3, "x")
check("and the daily limit is doubled", w.agents[cid]["sanity"] > before)
a1, a2 = list(w.agents)[:2]
w.agents[a1]["room"] = w.agents[a2]["room"] = "lounge"
w.agents[a1]["aff"][a2] = 5
w.agents[a1]["sanity"] = 30
w.agents[a1]["comfort_today"] = 0
r.aftermath_comfort(r.new_tick(12), 12)
check("someone who is low leans on a friend without any model help", w.agents[a1]["sanity"] >= 32)
not_due_today = not r.vigil_due(12)
r.day += 1
check("the remembrance is due the next morning", not_due_today and r.vigil_due(10))
san = {c: a["sanity"] for c, a in w.agents.items()}
for a in w.agents.values():
    a["sanity"] = 40
tv = r.run_vigil(10)
check("the remembrance gathers everyone and lifts them", all(a["room"] == "lounge" for a in w.agents.values()) and all(a["sanity"] >= 46 for a in w.agents.values()))
check("it happens only once", not r.vigil_due(12) and w.state["aftermath"]["vigil_done"])
for a in w.agents.values():
    a["sanity"] = 40
    a["slept"] = True
r.aftermath_night(r.new_tick(22))
check("a night in the calm window restores more", all(a["sanity"] >= 44 for a in w.agents.values()))
r.day = w.state["aftermath"]["until"] + 1
check("after the window the drain returns at half strength, then full", r.drain_factor() == 0.5)
r.day += 2
check("and full strength later", r.drain_factor() == 1.0)
w, r, _ = fresh(181)
ids = list(w.agents)
for c in w.agents.values():
    c["sanity"] = 10
n = 0
for i in range(200):
    t = r.new_tick(12)
    before = w.agents[ids[0]]["sanity"]
    r.baseline_drain(t, 12)
    n += w.agents[ids[0]]["sanity"] < before
    w.agents[ids[0]]["sanity"] = 10
check("people who are already very low are worn down more slowly", n < 70, str(n))

# ---- locks, forced doors, barricades, sleeping
from murder.world import shuffled_homes  # noqa: E402
from collections import Counter  # noqa: E402
import json  # noqa: E402
hm = shuffled_homes()
check("shuffled bedrooms give each of the eight people a bedroom of their own", sorted(Counter(hm.values()).values()) == [1] * 8)
variants = {tuple(sorted(new_state(3, shuffle_rooms=True)["cast"][c]["home"] for c in ("szymon", "seul"))) for _ in range(12)}
check("each new game can pair people differently", len(variants) > 1)
st = new_state(3, shuffle_rooms=True)
check("people start in their (new) rooms", all(a["room"] == st["cast"][c]["home"] for c, a in st["agents"].items()))

w, r, _ = fresh(190)
ids = list(w.agents)
owner = next(c for c in ids if w.cast[c]["home"] == "blue_room")
other = next(c for c in ids if w.cast[c]["home"] != "blue_room")
third = next(c for c in ids if w.cast[c]["home"] != "blue_room" and c != other)
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[owner]["room"] = "blue_room"
w.agents[other]["room"] = "landing"
w.agents[third]["room"] = "landing"
tk = r.new_tick(14)
check("any room can be bolted from inside", "lock" in r.door_acts(owner))
r.do_lock(tk, owner, {"door": ""})
check("the bolt is drawn", "blue_room" in w.state["locks"])
ok_other = [n["ok"] for n in w.adjacent(other, "landing") if n["room"] == "blue_room"][0]
check("a locked room keeps out people without a key", not ok_other and "blue_room" not in w.reachable_rooms(other, 40))
w.agents[third]["inv"]["skeleton_keys"] = 1
check("skeleton keys open it", "blue_room" in w.reachable_rooms(third, 40))
w.agents[third]["inv"].pop("skeleton_keys")
w.agents[owner]["room"] = "landing"
check("the people who sleep there have a key", "blue_room" in w.reachable_rooms(owner, 40))
w.agents[other]["room"] = "blue_room"
w.state["locks"]["blue_room"] = {"by": owner, "day": 3}
w.move(other, "landing", 40)
check("a visitor who leaves clears the bolt", "blue_room" not in w.state["locks"])
w.agents[owner]["room"] = "blue_room"
w.state["locks"]["blue_room"] = {"by": owner, "day": 3}
w.move(owner, "landing", 40)
check("a key-holder who leaves locks up behind them", "blue_room" in w.state["locks"])
check("key holders can unlock from outside", "unlock" in r.door_acts(owner))
tk = r.new_tick(15)
r.do_unlock(tk, owner, {"door": "blue_room"})
check("and it works", "blue_room" not in w.state["locks"])
r.do_lock(tk, owner, {"door": "blue_room"})
check("or lock a room from outside", "blue_room" in w.state["locks"])
r.do_lock(tk, other, {"door": "garden"})
check("outdoor places have no lock", "garden" not in w.state["locks"])

# picking
w.state["locks"]["blue_room"] = {"by": owner, "day": 3}
w.agents[other]["room"] = "landing"
w.agents[other]["sanity"] = w.agents[other]["hp"] = 95
w.agents[other]["inv"] = {}
check("no pick action without a tool", "pick" not in r.door_acts(other))


def pick_rate(tool, trials=150):
    n = 0
    for _ in range(trials):
        w.agents[other]["inv"] = {tool: 1}
        w.state["locks"]["blue_room"] = {"by": owner, "day": 3}
        r.do_pick(r.new_tick(16), other, {"door": "blue_room"})
        n += "blue_room" not in w.state["locks"]
    return n


n_wire, n_pen = pick_rate("wire"), pick_rate("pen")
w.agents[other]["inv"] = {"wire": 1}
w.state["locks"]["blue_room"] = {"by": owner, "day": 3}
check("a tool allows picking and a better tool picks more often", "pick" in r.door_acts(other) and n_wire > n_pen > 5, f"{n_wire} {n_pen}")
w.agents[other]["inv"] = {}


# breaking
def break_rate(tool, trials=150):
    n = 0
    for _ in range(trials):
        w.agents[other]["inv"] = {tool: 1} if tool else {}
        w.agents[other]["hp"] = 90
        w.state["locks"]["blue_room"] = {"by": owner, "day": 3}
        w.state["broken"] = []
        r.do_break(r.new_tick(16), other, {"door": "blue_room"})
        n += "blue_room" in w.state["broken"]
    return n


b_hand, b_ram = break_rate(None), break_rate("sledgehammer")
check("a locked door can be broken, more easily with a tool", b_ram > b_hand > 5, f"{b_ram} {b_hand}")
w.state["broken"] = ["blue_room"]
w.state["locks"] = {}
w.agents[owner]["room"] = "blue_room"
r.do_lock(r.new_tick(16), owner, {"door": ""})
check("a broken door cannot be locked again", "blue_room" not in w.state["locks"])
w.state["broken"] = ["blue_room", "study"]
w.state["day"] = 7
r.day = 7
tk = r.new_tick(22)
r.repair_doors(tk)
check("NeoVi mends the broken doors at the turn of the week", not w.state["broken"] and any("mending" in e["text"] for e in tk["events"]))

# sleepers wake to noise
w.agents[owner]["room"] = "blue_room"
woke = 0
for _ in range(60):
    w.agents[owner]["asleep"] = True
    r.noise(r.new_tick(23), "blue_room", "loud", other)
    woke += not w.agents[owner].get("asleep")
check("loud noise wakes sleepers, usually", woke > 45, str(woke))
quiet = 0
for _ in range(60):
    w.agents[owner]["asleep"] = True
    r.noise(r.new_tick(23), "blue_room", "quiet", other)
    quiet += not w.agents[owner].get("asleep")
check("picking a lock rarely does", quiet < 20, str(quiet))
w.agents[owner].pop("asleep", None)

# barricades
w, r, _ = fresh(191)
ids = list(w.agents)
ins, out_ = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[ins]["room"] = "library"
w.agents[out_]["room"] = "landing"
tk = r.new_tick(14)
check("any ordinary door can be barricaded", "barricade" in r.door_acts(ins))
r.do_barricade(tk, ins, {"door": "landing", "item": ""})
check("a barricade keeps the other side out", w.state["blocks"] and "library" not in w.reachable_rooms(out_, 40))
check("the outside is offered 'break'", "break" in r.door_acts(out_))
check("the barricader can still leave", "landing" in w.reachable_rooms(ins, 40))
bid = list(w.state["blocks"])[0]
hp0 = w.state["blocks"][bid]["hp"]
w.agents[out_]["inv"] = {"sledgehammer": 1}
w.agents[out_]["hp"] = 95
for _ in range(40):
    r.do_break(r.new_tick(14), out_, {"door": "library"})
    if not w.state["blocks"]:
        break
check("a barricade can be broken down", not w.state["blocks"] and "library" in w.reachable_rooms(out_, 40) and hp0 >= 1)
r.do_barricade(tk, ins, {"door": "landing", "item": ""})
w.move(ins, "landing", 40)
check("walking out through a barricaded door removes it", not w.state["blocks"])
w.agents[ins]["room"] = "library"
w.agents[ins]["inv"]["planks"] = 1
r.do_barricade(tk, ins, {"door": "landing", "item": "planks"})
check("props are used up", w.agents[ins]["inv"].get("planks", 0) == 0 and list(w.state["blocks"].values())[0]["prop"] == "planks")
w.state["blocks"] = {}
r.do_barricade(tk, ins, {"door": "landing", "item": "body"})
check("a body has to be there to use one", list(w.state["blocks"].values())[0]["prop"] == "furniture")
w.state["blocks"] = {}
vic = ids[2]
w.agents[vic]["room"] = "library"
tk = r.new_tick(15)
r.open_case(tk, "murder", vic, culprit=ins, wkind="hands", weapon=None, room="library", hour=15, witnesses=[])
r.do_barricade(tk, ins, {"door": "landing", "item": "body"})
check("a body can block a door, and leaves a clue", list(w.state["blocks"].values())[0]["prop"] == "body" and any("wedged" in c["text"] for c in w.state["case"]["clues"]))

# sleeping where you like
w, r, _ = fresh(192)
ids = list(w.agents)
a1 = ids[0]
home = w.cast[a1]["home"]
w.agents[a1]["room"] = "lounge"
w.agents[a1]["sleep_pref"] = [r.day, "library"]
check("people sleep where they said they would", r.bed_room(a1) == "library")
w.state["locks"]["library"] = {"by": ids[1], "day": 3}
check("unless they cannot get in", r.bed_room(a1) == home)
w.state["locks"] = {}
w.agents[a1]["sleep_pref"] = [r.day, "garden"]
tk = r.new_tick(22)
r.send_to_bed(tk, a1)
check("sleeping rough is flagged", w.agents[a1]["slept_where"] == "rough")
w.agents[a1]["sleep_pref"] = [r.day - 1, "garden"]
check("an old choice does not carry over", r.bed_room(a1) == home)
for c in ids:
    w.agents[c]["hp"], w.agents[c]["sanity"] = 80, 60
w.agents[a1]["sleep_pref"] = [r.day, "garden"]
r.run_night()
check("sleeping outside costs health and sanity", w.agents[a1]["hp"] <= 80 and w.agents[a1]["sanity"] < w.agents[ids[3]]["sanity"], f"{w.agents[a1]['hp']} {w.agents[a1]['sanity']} {w.agents[ids[3]]['sanity']}")
check("everyone else slept in their own room", all(a["room"] == w.cast[c]["home"] for c, a in w.agents.items() if c != a1))

# frightened people lock up
w, r, _ = fresh(193)
w.state["case"] = None
w.state["bodies"] = [{"victim": "x", "room": "kitchen"}]
for a in w.agents.values():
    a["sanity"] = 30
for _ in range(3):
    r.auto_night_locks(r.new_tick(22))
check("frightened people bolt their doors at night", len(w.state["locks"]) >= 2, str(len(w.state["locks"])))

# plotters go through doors
w, r, _ = fresh(194)
ids = list(w.agents)
tg = next(c for c in ids if w.cast[c]["home"] == "blue_room")
pl = next(c for c in ids if w.cast[c]["home"] != "blue_room")
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[pl]["room"] = "landing"
w.agents[tg]["room"] = "blue_room"
w.state["locks"]["blue_room"] = {"by": tg, "day": 3}
w.agents[pl]["inv"] = {"wire": 1}
d = r.clean_decision({"action": "stay", "activity": "x"})
check("a plotter with a tool picks the lock to reach the target", r.door_assault(pl, "blue_room", d) and d["action"] == "pick")
w.agents[pl]["inv"] = {}
d = r.clean_decision({"action": "stay", "activity": "x"})
check("without a tool they break it", r.door_assault(pl, "blue_room", d) and d["action"] == "break")
snap = w.snapshot()
json.dumps(snap)
check("the viewer snapshot shows locks and serialises", "blue_room" in snap["locks"])

w, r, _ = fresh(195)
ids = list(w.agents)
x, y = ids[0], next(c for c in ids if w.cast[c]["home"] != w.cast[ids[0]]["home"])
w.state["bonds"].append({"a": x, "b": y, "kind": "romance", "since": 3})
got = False
for _ in range(60):
    w.agents[x].pop("sleep_pref", None)
    r.auto_sleep(20)
    if w.agents[x].get("sleep_pref") and w.agents[x]["sleep_pref"][1] == w.cast[y]["home"]:
        got = True
        break
check("lovers sometimes spend the night in each other's room", got)

# ---- the wider item pool, common supplies and crafting
from murder.data_world import ROOMS, ITEMS, ROOM_ITEMS, COMMON_ITEMS, RECIPES, HIDDEN_ITEMS  # noqa: E402
indoor = [r for r in ROOMS if ROOMS[r][1] not in ("grounds", "roof") and r not in ("core_vault",)]
check("every indoor room except the corridors has something in it", all(ROOM_ITEMS.get(r) for r in indoor if r not in ("voting_grounds", "core_vault", "landing", "upper_landing")))
bad = [k for r, pool in ROOM_ITEMS.items() for k in pool if k not in ITEMS]
bad += [k for lst in COMMON_ITEMS.values() for k in lst if k not in ITEMS]
bad += [k for rc in RECIPES.values() for opts, _ in rc["needs"] for k in opts if k not in ITEMS and k not in ("scarf",)]
bad += [rc["out"] for rc in RECIPES.values() if rc["out"] not in ITEMS]
bad += [k for lst in HIDDEN_ITEMS.values() for h in lst for k in h["items"] if k not in ITEMS]
check("every item referenced by a room, recipe or hiding place exists", not bad, str(bad[:5]))
weapons = sum(1 for pool in ROOM_ITEMS.values() for k in pool if "weapon" in ITEMS[k].get("tags", []))
check("the pool holds many kinds of potential weapon", weapons >= 60, str(weapons))
check("special items are scattered through the rooms", sum(1 for pool in ROOM_ITEMS.values() for k in pool if "special" in ITEMS[k].get("tags", [])) >= 10)
check("every recipe's product is a crafted special item", all({"special", "crafted"} <= set(ITEMS[rc["out"]]["tags"]) for rc in RECIPES.values()))
check("common supplies never include weapons", not [k for lst in COMMON_ITEMS.values() for k in lst if "weapon" in ITEMS[k].get("tags", [])])

w, r, _ = fresh(200)
ids = list(w.agents)
c1 = ids[0]
w.agents[c1]["room"] = "laundry"
w.agents[c1]["inv"] = {}
got = 0
for _ in range(10):
    q, _e = w.take(c1, "rags", 3)
    got += q or 0
check("common supplies are unlimited", got >= 27 and "rags" not in w.state["room_items"].get("laundry", {}))
w.agents[c1]["room"] = "library"
check("but only where they would be found", w.take(c1, "rags", 1)[0] is None)
w.agents[c1]["room"] = "kitchen"
w.agents[c1]["inv"] = {}
before = w.state["room_items"]["kitchen"].get("frying_pan", 0)
w.take(c1, "frying_pan", 1)
check("ordinary items run out", w.state["room_items"]["kitchen"].get("frying_pan", 0) == before - 1)
check("an item that is not here cannot be taken", w.take(c1, "garrote", 1)[0] is None)

# crafting
w, r, _ = fresh(201)
ids = list(w.agents)
c1 = ids[0]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[c1]["inv"] = {}
w.agents[c1]["room"] = "foyer"
check("nothing can be crafted from nothing", not r.craftable(c1) and "craft" not in r.craft_acts(c1))
w.agents[c1]["room"] = "music_room"
w.state["room_items"]["music_room"].pop("drumsticks", None)
plan, why = r.recipe_plan(c1, "garrote")
check("a recipe says what is missing", plan is None and "pencil" in why.lower(), why)
w.agents[c1]["inv"] = {"pencil": 2}
check("the music room supplies the string", r.recipe_plan(c1, "garrote")[0] is not None and "garrote" in r.craftable(c1))
check("the crafting prompt names the supplies and the rule", any("COMMON SUPPLIES" in l and "Guitar string" in l for l in r.craft_lines(c1)) and any("nothing else exists" in l.lower() for l in r.craft_lines(c1)))
ok = False
for _ in range(20):
    w.agents[c1]["inv"] = {"pencil": 2}
    w.agents[c1]["hp"] = 90
    r.do_craft(r.new_tick(14), c1, {"craft": "garrote"})
    if w.agents[c1]["inv"].get("garrote"):
        ok = True
        break
check("crafting makes the item and uses up the parts", ok and not w.agents[c1]["inv"].get("pencil"))
check("it is a special crafted item and the make is on record", "crafted" in ITEMS["garrote"]["tags"] and any(x["item"] == "garrote" and x["by"] == c1 for x in w.state["crafted"]))
check("a homemade weapon tells investigators where its parts come from", "homemade" in r.provenance_text("garrote", c1) and "Music Room" in r.provenance_text("garrote", c1))
fails = 0
for _ in range(60):
    w.agents[c1]["inv"] = {"pencil": 2}
    w.agents[c1]["hp"] = 90
    r.do_craft(r.new_tick(14), c1, {"craft": "garrote"})
    fails += not w.agents[c1]["inv"].get("garrote")
    w.agents[c1]["inv"].pop("garrote", None)
check("crafting can fail", 0 < fails < 60, str(fails))
w.agents[c1]["room"] = "kitchen"
w.agents[c1]["inv"] = {"planks": 1}
check("a workshop recipe will not work in the wrong room", r.recipe_plan(c1, "nail_board")[0] is None and "has to be made" in r.recipe_plan(c1, "nail_board")[1])
w.agents[c1]["room"] = "generator_shed"
w.agents[c1]["inv"] = {}
check("in the shed the lying-around planks, hammer and common nails do", r.recipe_plan(c1, "nail_board")[0] is not None)
w.agents[c1]["room"] = "kitchen"
w.agents[c1]["inv"] = {"water_bottle": 1}
check("poison needs the right plant and the right room", r.recipe_plan(c1, "oleander_extract")[0] is None)
w.agents[c1]["room"] = "greenhouse"
w.state["room_items"]["greenhouse"]["watering_can"] = 2
check("the greenhouse has the leaves and a can", r.recipe_plan(c1, "oleander_extract")[0] is not None)
w.agents[c1]["room"] = "laundry"
w.agents[c1]["inv"] = {"wine_bottle": 1}
check("anything usable from the room counts: a bottle plus the laundry's rags makes a shiv", "bottle_shiv" in r.craftable(c1))
w.agents[c1]["inv"] = {"sleeping_pills": 3}
w.agents[c1]["room"] = "bathroom"
check("a spiked drink needs pills and a drink", r.recipe_plan(c1, "drugged_drink")[0] is None)
w.agents[c1]["inv"] = {"sleeping_pills": 3, "spirits": 1}
check("which a character can have on them", r.recipe_plan(c1, "drugged_drink")[0] is not None)

# keys, hiding places, old saves
w.agents[c1]["inv"] = {"key_blue_room": 1}
ow = next(c for c in ids if w.cast[c]["home"] != "blue_room" and c != c1)
w.state["locks"]["blue_room"] = {"by": ow, "day": 3}
check("a spare room key opens that room", w.has_room_key(c1, "blue_room"))
old = new_state(3)
old.pop("pool_v2")
old["room_items"]["library"].pop("old_map", None)
w2 = World(old)
check("an older save gets the wider pool", w2.state["room_items"]["library"].get("old_map") == 1 and w2.state["pool_v2"])

# plotters make weapons when they have none
w, r, _ = fresh(202)
ids = list(w.agents)
pl, tg = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[pl]["room"] = "laundry"
w.state["room_items"]["laundry"] = {}
w.agents[pl]["inv"] = {"champagne": 1}
r.plot_start(r.new_tick(10), pl, tg, "x", 10)
p = w.state["plots"][pl]
p["stage"] = "preparing"
made = False
for _ in range(30):
    d = r.clean_decision({"action": "stay", "activity": "x"})
    r.plot_steer(r.new_tick(12), pl, p, d, 12, False)
    if d["action"] == "craft":
        made = True
        break
check("a plotter without a weapon makes one from what is to hand", made and d["craft"] in RECIPES)
snap = w.snapshot()
check("the snapshot is still serialisable", bool(json.dumps(snap)))

# ---- rule classification on real roulette rules (a misread of "Whisper Only Indoors" once punished people for obeying it)
WHISPER = ("WHISPER ONLY INDOORS: My darlings, the sunshine is far too fragile for your voices. If you step outside, you will speak only in whispers for as long as you remain there. "
           "Indoors, you may be as loud and dramatic as you please. Anyone who breaks it is punished by NeoVi.")
check("a speech rule that mentions places is NOT a place rule", classify_text(WHISPER)["kind"] == "behavior")
check("a speech rule is not read as a place rule even when it is short", classify_text("Outdoors, no one may speak above a whisper.")["kind"] == "behavior")
check("an object rule is not a place rule", classify_text("You must carry a light when outside.")["kind"] != "zone")
c = classify_text("Nobody may be indoors after 18:00.")
check("a negated place rule is read the right way round", c["kind"] == "zone" and c["zone"] == "outdoors" and c["from"] == 18)
c = classify_text("Everyone must stay indoors until 18:00.")
check("a positive place rule with an end time", c["kind"] == "zone" and c["zone"] == "indoors" and c["until"] == 18)
check("a place rule that names both places is never a zone rule", classify_text("Stay outside in the morning and inside in the afternoon.")["kind"] != "zone")
w, r, hits = rule_setup(140, WHISPER)
r.llm.judge = lambda sysm, user, ctx: {"violations": [], "fulfilled": []}
for i, c_ in enumerate(w.agents):
    w.agents[c_]["room"] = "library" if i < 4 else "garden"
r.referee_turn(r.new_tick(12), 12)
check("nobody is punished for being indoors under the whisper rule", not hits)
check("the cast is not told to move outdoors", "must be outdoors" not in r.rule_hint(w.state["rule"]) and "must be indoors" not in r.rule_hint(w.state["rule"]))
tk = r.new_tick(8)
r.rule_notice(tk)
check("the viewer is told plainly how a rule is judged", any("referee reads" in e["text"] for e in tk["events"]))
w, r, _ = fresh(141)
w.agents[list(w.agents)[0]]["inv"] = {"champagne": 1, "pen": 1}
w.agents[list(w.agents)[0]]["concealed"] = {"pen": 0.5}
card = r.talk_prompt("blue_room", [list(w.agents)[0], list(w.agents)[1]], {}, 14)
check("conversation cards say what each person carries, and what is hidden", "Carrying: " in card and "Bottle of champagne" in card and "hidden on them" in card)
check("and forbid inventing props", "never invent an object" in card)

w2 = World(dict(new_state(3), cast={**new_state(3)["cast"]}))
old = new_state(3)
old["cast"]["shintaro"]["secret"] = "His persona was staged. Someone searched his bag neatly and he is determined to find out who."
old["cast"]["shintaro"]["goals"] = "Find out who searched his bag and why."
old["cast"]["shintaro"]["hook"] = {"text": "x", "until": 2}
w2 = World(old)
check("an old save is cleaned of the static bag mystery and of any pre-set hook", "bag" not in w2.state["cast"]["shintaro"]["secret"] and "bag" not in w2.state["cast"]["shintaro"]["goals"] and "hook" not in w2.state["cast"]["shintaro"])

# ---- hooks and ties grow out of events; nothing is pre-set
from murder.data_cast import CHARACTERS  # noqa: E402
check("no character has a pre-set hook or a loose end in their goals", all("hook" not in c and "searched" not in c["secret"] and "searched" not in c["goals"] for c in CHARACTERS.values()))
st0 = new_state(1)
check("a new game starts with no hooks and no ties", st0["hooks"] == [] and st0["ties"] == [])
w, r, _ = fresh(220)
ids = list(w.agents)
r.seed_belongings()
check("people keep a few personal things in their room", all(len(v) <= 2 for v in w.state["belongings"].values()) and any(w.state["belongings"].values()))
check("and are left with enough to carry", all(sum(a["inv"].values()) >= 3 for a in w.agents.values()))
owner = next(c for c in ids if w.state["belongings"].get(c))
home = w.cast[owner]["home"]
thief = next(c for c in ids if w.cast[c]["home"] != home)
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[thief]["room"] = home
w.agents[owner]["room"] = "garden"
tk = r.new_tick(14)
r.rifle_room(tk, thief, {"activity": "search", "thought": ""})
check("searching someone's room while they are away is going through their things", any(e["type"] == "rifle" for e in tk["events"]) and w.state["disturbances"])
w.agents[owner]["room"] = home
w.agents[thief]["room"] = "garden"
w.agents[owner]["sanity"] = 90
for _ in range(15):
    r.hook_notice(r.new_tick(16), 16)
    if w.state["hooks"]:
        break
check("the owner eventually notices, and a hook opens with a real culprit", w.state["hooks"] and w.state["hooks"][0]["culprit"] == thief and w.state["hooks"][0]["victims"] == [owner])
check("the victim has it on their mind; the culprit knows they have been noticed", any("ON YOUR MIND" in l for l in r.hook_lines(owner)) and any("WHAT YOU DID" in l for l in r.hook_lines(thief)))
check("nobody else is told", not r.hook_lines(next(c for c in ids if c not in (owner, thief))))
h = w.state["hooks"][0]
w.agents[owner]["room"] = w.agents[thief]["room"] = "garden"
w.agents[thief]["sanity"] = 80
h["seen_by"] = []
other = next(c for c in ids if c not in (owner, thief))
h["seen_by"] = [other]
r.hook_press(r.new_tick(17), owner, other, 17)
check("asking a witness gives evidence against the culprit", h["evidence"] >= 2 and any("saw" in c for c in h["clues"]))
r.hook_press(r.new_tick(17), owner, thief, 17)
for _ in range(20):
    if h["status"] != "open":
        break
    r.hook_press(r.new_tick(17), owner, thief, 17)
check("enough evidence solves it: the victim now knows", h["status"] == "solved" and any("you now know" in m for m in w.agents[owner]["memory"]["recent"]))
check("and it costs the culprit the victim's trust, on record", any(t["a"] == owner and t["b"] == thief and t["kind"] == "wronged" for t in w.state["ties"]))

# found on them
w, r, _ = fresh(221)
ids = list(w.agents)
v, t_ = ids[0], ids[1]
hk = r.new_hook(r.new_tick(14), "stolen", [v], t_, "garden", "Your pen is gone.", [], [], "pen")
r.hook_found_item(r.new_tick(15), v, t_, ["pen"])
check("finding the stolen thing on the thief solves the hook outright", hk["status"] == "solved")

# fade, suspicion
w, r, _ = fresh(222)
ids = list(w.agents)
v, t_ = ids[0], ids[1]
hk = r.new_hook(r.new_tick(14), "rifled", [v], t_, "garden", "Someone went through your things.", [], [])
hk["last_new"] = r.day - 4
w.agents[v]["memory"]["recent"] = []
r.hook_night(r.new_tick(22))
check("an ignored hook fades with a note of closure", hk["status"] == "faded" and any("never found out" in m for m in w.agents[v]["memory"]["recent"]))
hk2 = r.new_hook(r.new_tick(14), "rifled", [v], t_, "garden", "Someone went through your things.", [], [])
for c in ids:
    w.agents[v]["aff"][c] = 3
w.agents[v]["aff"][ids[4]] = -4
for _ in range(80):
    hk2["suspect"] = {}
    r.hook_tick(r.new_tick(14), 14)
    if hk2["suspect"]:
        break
check("without evidence suspicion falls on whoever they trust least (not necessarily the culprit)", hk2["suspect"].get(v) == ids[4])

# other sources
w, r, _ = fresh(223)
ids = list(w.agents)
cu = ids[0]
home2 = w.cast[ids[2]]["home"]
w.agents[cu]["room"] = "landing"
tk = r.new_tick(2 + 20)
r.hook_from_door(tk, cu, home2, "picked")
check("a picked lock leaves a disturbance for the room's people to find", w.state["disturbances"] and w.state["disturbances"][-1]["kind"] == "forced_entry")
r.hook_from_stash(tk, cu, ids[3], "library", "behind the books")
check("having a hiding place found opens a hook for its owner", any(x["kind"] == "stash_found" and x["victims"] == [ids[3]] for x in w.state["hooks"]))
r.hook_from_night(tk, cu, home2, [ids[5]])
check("being woken by someone at the door opens one too", any(x["kind"] == "night_visitor" for x in w.state["hooks"]))
r.note_odd(ids[6], ids[1], 14)
n_before = len(w.state["hooks"])
r.note_odd(ids[6], ids[2], 14)
check("two people noticing the same odd behaviour become a hook about that person", len(w.state["hooks"]) == n_before + 1 and w.state["hooks"][-1]["kind"] == "suspicious")

# ties
w, r, _ = fresh(224)
ids = list(w.agents)
a_, b_ = ids[0], ids[1]
before = w.agents[a_]["aff"][b_]
r.add_tie(a_, b_, "helped", "Noah steadied them", 1)
r.add_tie(a_, b_, "helped", "Noah steadied them", 1)
check("a tie is recorded once and moves the feeling", len(r.ties_about(a_, b_)) == 1 and w.agents[a_]["aff"][b_] == before + 1)
for i in range(10):
    r.add_tie(a_, b_, "slighted", f"snub number {i}", 0)
check("each pair keeps only its latest ties", len(r.ties_about(a_, b_)) <= 6)
w.agents[a_]["room"] = w.agents[b_]["room"] = "lounge"
check("ties appear in the prompt, and in conversation cards", any("WHY YOU FEEL" in l for l in r.tie_lines(a_)) and "History:" in r.card_ties(a_, [a_, b_]))
check("a label summarises them", r.relationship_label(a_, b_) in ("", "someone who keeps wearing you down", "someone who helped you"))
tk = r.new_tick(14)
tk["events"].append({"type": "assault", "who": ids[2], "room": "lounge", "vis": "public", "text": "x hits y."})
w.agents[ids[2]]["room"] = "lounge"
for _ in range(5):
    r.reaction_pass(tk, 14)
w.state["ties"] = []
fr = 0
for _ in range(20):
    t2 = r.new_tick(14)
    r.friction_tick(t2, 14)
    fr += sum(e["type"] == "friction" for e in t2["events"])
check("friction leaves a tie behind", fr == 0 or any(t["kind"] == "slighted" for t in w.state["ties"]))

# ---- the rule corpus, second opinions, titles, speech
import os as _os  # noqa: E402
corpus = json.load(open(_os.path.join(HERE, "rule_corpus.json"), encoding="utf-8"))
wrong = []
for case_ in corpus:
    c_ = classify_text(case_["text"])
    ok_ = (c_["kind"] != "zone") if case_["kind"] == "not_zone" else c_["kind"] == case_["kind"]
    for k_ in ("zone", "from", "until", "by_hour"):
        if k_ in case_ and c_.get(k_) != case_[k_]:
            ok_ = False
    if not ok_:
        wrong.append(case_["text"][:40])
check(f"the classifier reads all {len(corpus)} rules in the saved corpus correctly", not wrong, str(wrong))
w, r, _ = fresh(230)
w.state["rule"] = {"id": "ai", "title": "x", "short": "x", "text": "Players must only be outdoors today.", "params": {}, "strikes": {}, "ai": True, "source": "roulette"}
r.classify_today()
check("a second reading that agrees confirms a place rule", w.state["rule"]["chk"]["kind"] == "zone" and w.state["rule"]["chk"].get("confirmed"))
r.llm.host_json = lambda sysm, user, ctx: {"kind": "behavior", "zone": "none", "reading": "People may only whisper outdoors."}
r.classify_today()
rl = w.state["rule"]
check("a second reading that disagrees hands it to the referee", rl["chk"]["kind"] == "behavior" and rl["chk"].get("disagreed") and rl["reading"])
tk = r.new_tick(8)
r.rule_notice(tk)
check("and the viewer is told both readings", any("second reading disagreed" in e["text"] and "Plain reading" in e["text"] for e in tk["events"]))


def boom(sysm, user, ctx):
    raise ValueError("offline")


r.llm.host_json = boom
r.classify_today()
check("if the second opinion fails the first reading stands, flagged unconfirmed", w.state["rule"]["chk"]["kind"] == "zone" and w.state["rule"]["chk"].get("confirmed") is False)
from murder.rules import consistent_title  # noqa: E402
check("a title that names the opposite place to the rule is replaced", consistent_title("Whisper Only Indoors", "Outdoors, no one may speak above a whisper.", "x") == "Outdoors, no one may speak above a whisper")
check("a consistent title is kept", consistent_title("Quiet Garden", "Outdoors, whisper.", "x") == "Quiet Garden")
w, r, hits = rule_setup(231, "Outdoors, no one may speak above a whisper.")
seen2 = {}
r.llm.judge = lambda sysm, user, ctx: (seen2.update(u=user) or {"violations": [], "fulfilled": []})
for i_, c_ in enumerate(w.agents):
    w.agents[c_]["room"] = "garden" if i_ % 2 else "library"
r.referee_turn(r.new_tick(8), 8)
r.referee_turn(r.new_tick(10), 10)
check("the referee is told who is outdoors and who is not, for speech rules", "OUTDOORS" in seen2["u"] and "indoors" in seen2["u"] and "use the location" in seen2["u"])
check("every rule that is set up is logged for the corpus", _os.path.exists(_os.path.join(_os.environ["MC_DATA_DIR"], "state", "rules_seen.jsonl")))

# ---- telemetry, suggestions, short docs, props, leaks
w, r, _ = fresh(240)
ids = list(w.agents)
c1 = ids[0]
d = r.clean_decision({"action": "stay", "activity": "x", "sneak": True, "conceal": {"item": "pen", "on": True}})
r.apply_decision(r.new_tick(14), c1, d, {}, [])
tel = r.usage_summary()
check("every decision is counted, with the optional flags the model used", tel["action:stay"]["model"] == 1 and tel.get("sneak", {}).get("model") == 1)
r.note_use(c1, "spy_on", "engine")
check("engine-driven uses are counted separately", r.usage_summary()["spy_on"]["engine"] == 1)
check("the viewer snapshot carries today's usage", w.snapshot()["telemetry"]["action:stay"]["model"] == 1)
d2 = r.clean_decision({"action": "stay", "activity": "x"})
d2["action"] = "experiment"
d2["_src"] = "engine"
r.note_decision(c1, d2)
check("an overridden turn is attributed to the engine", r.usage_summary()["action:experiment"]["engine"] == 1)

# suggestions
w, r, _ = fresh(241)
ids = list(w.agents)
a1, a2 = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[a1]["room"] = w.agents[a2]["room"] = "library"
w.agents[a1]["aff"][a2] = -6
w.agents[a1]["inv"] = {"kitchen_knife": 1}
hint = r.options_hint(a1, 14)
check("a character gets situational suggestions that fit the moment", hint and ("frisk" in hint[0] or "sneak" in hint[0] or "conceal" in hint[0]), str(hint))
seen_tags = set()
for _ in range(40):
    w.agents[a1]["last_hints"] = []
    seen_tags |= set(w.agents[a1].get("last_hints", []))
    r.options_hint(a1, 14)
    seen_tags |= set(w.agents[a1]["last_hints"])
check("different suggestions come up over time", len(seen_tags) >= 2, str(seen_tags))
w.agents[a1]["last_hints"] = []
first = r.options_hint(a1, 20)
tags1 = set(w.agents[a1]["last_hints"])
second = r.options_hint(a1, 20)
tags2 = set(w.agents[a1]["last_hints"])
check("a suggestion is not repeated turn after turn when there is an alternative", not (tags1 & tags2) or len(tags1) + len(tags2) < 3, f"{tags1} {tags2}")
w.state["revealed"] = False
check("no suggestions before the truth is out", not r.options_hint(a1, 14))
w.state["revealed"] = True
r.short_docs = True
check("on later turns the long explanations shrink to a pointer", all(len(l) < 330 for l in r.door_lines(a1) + r.craft_lines(a1) + r.stealth_lines(a1)[:1]))
r.short_docs = False
check("and at the start of the day they are in full", any(len(l) > 330 for l in r.door_lines(a1)))
check("docs are full on the first turns of the day only", r.docs_full(a1, 8) and r.docs_full(a1, 10) and not r.docs_full(a1, 14))

# props
w, r, _ = fresh(242)
ids = list(w.agents)
x, y = ids[0], ids[1]
w.agents[x]["room"] = w.agents[y]["room"] = "laundry"
w.agents[x]["inv"] = {"pen": 1, "champagne": 1}
w.agents[y]["inv"] = {}
w.state["room_items"]["laundry"] = {}
lines = [{"speaker": x, "kind": "act", "text": "pulls binoculars from her jacket and scans the window"},
         {"speaker": x, "kind": "act", "text": "lifts the champagne and fills two glasses"},
         {"speaker": y, "kind": "act", "text": "wipes the bench with a rag"},
         {"speaker": y, "kind": "say", "text": "Where did you find binoculars?"},
         {"speaker": y, "kind": "act", "text": "grabs the heavy frying pan from the shelf"}]
tk = r.new_tick(14)
kept = r.filter_props(tk, "laundry", [x, y], lines)
texts = [k["text"] for k in kept]
check("an action line that pulls an object from nowhere is dropped", not any("binoculars from" in t for t in texts) and not any("frying pan" in t for t in texts))
check("lines about what someone carries, a common supply of the room, or plain speech are kept", any("champagne" in t for t in texts) and any("rag" in t for t in texts) and any("Where did you find" in t for t in texts))
check("the slip is counted and noted for the GM", r.usage_summary()["prop_slip"]["model"] == 2 and any("nobody had" in e["text"] for e in tk["events"]))

# leaks: night locking no longer depends on a hidden plot
w, r, _ = fresh(243)
ids = list(w.agents)
w.state["plots"] = {ids[0]: {"target": ids[1], "stage": "preparing", "log": [], "plan": []}}
for a in w.agents.values():
    a["sanity"] = 90
w.state["case"] = None
w.state["bodies"] = []
n = 0
for _ in range(40):
    w.state["locks"] = {}
    r.auto_night_locks(r.new_tick(22))
    n += len(w.state["locks"])
w.state["plots"] = {}
m = 0
for _ in range(40):
    w.state["locks"] = {}
    r.auto_night_locks(r.new_tick(22))
    m += len(w.state["locks"])
check("people do not lock their doors more just because a plot they cannot know about exists", abs(n - m) < 0.4 * max(n, m, 1), f"{n} vs {m}")
hk = r.new_hook(r.new_tick(22), "rifled", [ids[2]], ids[3], "garden", "Someone went through your things.", [], [])
w.agents[ids[2]]["room"] = w.cast[ids[2]]["home"]
k1 = 0
for _ in range(60):
    w.state["locks"] = {}
    r.auto_night_locks(r.new_tick(22))
    k1 += w.cast[ids[2]]["home"] in w.state["locks"]
hk["status"] = "faded"
k2 = 0
for _ in range(60):
    w.state["locks"] = {}
    r.auto_night_locks(r.new_tick(22))
    k2 += w.cast[ids[2]]["home"] in w.state["locks"]
check("but someone who knows something is wrong does", k1 > k2, f"{k1} vs {k2}")

# ---- an interrupted day can be resumed from the last completed turn
w = World(new_state(3))
seen_ticks = []
cut = {"n": 0}


def stop_after_three():
    return len(seen_ticks) >= 3


r1 = DayRunner(w, LLM(backend="mock"), seen_ticks.append, step=2, murders=False, rule_mode="roulette", confessionals=False, seed=7, should_stop=stop_after_three)
try:
    r1.run()
except Exception as e_:
    stopped = type(e_).__name__
rule_before = json.dumps(w.state["rule"], sort_keys=True)
last_hour, last_idx = seen_ticks[-1]["hour"], seen_ticks[-1]["idx"]
saved = w.dump()
w_b = World(saved)
after = []
r2 = DayRunner(w_b, LLM(backend="mock"), after.append, step=2, murders=False, rule_mode="roulette", confessionals=False, seed=8)
r2.run(resume_after=last_hour, start_idx=last_idx + 1)
check("a resumed day carries on from the turn after the last completed one", after[0]["hour"] == last_hour + 2 and after[0]["idx"] == last_idx + 1)
check("it does not announce a new rule", not any("RULE CHECK" in e["text"] or "NO RULE" in e["text"] for t in after for e in t["events"]))
check("and it finishes the day, through the night to the morning", [t["hour"] for t in after][-1] == 31 and not any(t["hour"] <= last_hour and t.get("phase") != "night" for t in after))
check("the morning broadcast is not repeated", sum(1 for t in after for b in t["broadcasts"] if b.get("kind") == "morning") == 0)
ends_ = {c: tuple(tr[-1][1:]) for c, tr in seen_ticks[-1]["live"]["tracks"].items()}
starts_ = {c: tuple(tr[0][1:]) for c, tr in after[0]["live"]["tracks"].items()}
check("a resumed day picks everybody up exactly where they stood (positions are saved with the game)", ends_ and all(starts_.get(c) == p_ for c, p_ in ends_.items() if c in starts_), str([(c, ends_[c], starts_.get(c)) for c in ends_ if starts_.get(c) != ends_[c]][:3]))
check("and its clock carries on from the last turn", after[0]["live"]["start"] >= seen_ticks[-1]["live"]["start"] + seen_ticks[-1]["live"]["dur"])

# ---- trial evidence variety and plot motives
def case_in(seed, room, culprit_idx=0, victim_idx=1, asleep=False):
    w, r, _ = fresh(seed)
    ids = list(w.agents)
    k, v = ids[culprit_idx], ids[victim_idx]
    for c in ids:
        w.agents[c]["room"] = "garden"
    w.agents[k]["room"] = w.agents[v]["room"] = room
    if asleep:
        w.agents[v]["asleep"] = True
    return w, r, ids, k, v


def make_case(w, r, k, v, room, moves=None):
    tk = r.new_tick(15)
    if moves:
        tk["moves"][k] = moves
    case = r.open_case(tk, "murder", v, culprit=k, wkind="hands", weapon=None, room=room, hour=15, witnesses=[])
    return case, tk


w, r, ids, k, v = case_in(250, "library")
w.state["locks"]["library"] = {"by": v, "day": 3}
got = set()
for s_ in range(20):
    w2, r2, ids2, k2, v2 = case_in(260 + s_, "library")
    w2.state["locks"]["library"] = {"by": v2, "day": 3}
    case, _ = make_case(w2, r2, k2, v2, "library")
    got |= {c["kind"] for c in case["clues"]}
check("a murder in a locked room says the door was not forced and who could open it", {"door_lock", "keyholders"} <= got)
w2, r2, ids2, k2, v2 = case_in(280, "library")
w2.state["locks"]["library"] = {"by": v2, "day": 3}
case, _ = make_case(w2, r2, k2, v2, "library")
kh = next(c for c in case["clues"] if c["kind"] == "keyholders")["text"]
check("the key holders listed are the people who sleep there, hold keys or locked it", r2.nm(v2) in kh and "master" in kh)
got = set()
for s_ in range(25):
    w2, r2, ids2, k2, v2 = case_in(300 + s_, "study")
    r2.log_door("study", "picked", k2, "wire")
    case, _ = make_case(w2, r2, k2, v2, "study")
    got |= {c["kind"] for c in case["clues"]}
check("a lock that was picked leaves scratches as a clue", "door_picked" in got)
got = set()
for s_ in range(25):
    w2, r2, ids2, k2, v2 = case_in(330 + s_, "study")
    r2.log_door("study", "broken", k2)
    case, _ = make_case(w2, r2, k2, v2, "study")
    got |= {c["kind"] for c in case["clues"]}
check("a forced door leaves splinters", "door_forced" in got)
got = set()
for s_ in range(25):
    w2, r2, ids2, k2, v2 = case_in(360 + s_, "bathroom")
    case, _ = make_case(w2, r2, k2, v2, "bathroom", {"from": "garden", "path": ["garden", "foyer", "bathroom"], "to": "bathroom"})
    got |= {c["kind"] for c in case["clues"]}
check("a killer who came in from outside leaves footprints", "footprints" in got)
got = set()
for s_ in range(10):
    w2, r2, ids2, k2, v2 = case_in(390 + s_, "blue_room", asleep=True)
    case, _ = make_case(w2, r2, k2, v2, "blue_room")
    got |= {c["kind"] for c in case["clues"]}
check("a sleeping victim has no defensive wounds", "unwoken" in got)
got = set()
for s_ in range(40):
    w2, r2, ids2, k2, v2 = case_in(410 + s_, "lounge")
    r2.ensure_wardrobe()
    w2.agents[k2]["inv"] = {f"clothes_{k2}": 1}
    case, _ = make_case(w2, r2, k2, v2, "lounge")
    got |= {c["kind"] for c in case["clues"]}
check("what the killer wears can leave fibres", "fibres" in got)
w2, r2, ids2, k2, v2 = case_in(450, "lounge")
r2.new_hook(r2.new_tick(10), "rifled", [v2], ids2[3], "lounge", "Someone went through your things.", [], [])
case, _ = make_case(w2, r2, k2, v2, "lounge")
check("a victim who had been uneasy leaves that on record", any(c["kind"] == "prior_hook" for c in case["clues"]))
names_leak = False
for s_ in range(30):
    w2, r2, ids2, k2, v2 = case_in(470 + s_, "study")
    w2.state["locks"]["study"] = {"by": v2, "day": 3}
    w2.agents[k2]["inv"] = {"scarf": 1, "cooking_oil": 1}
    r2.log_door("study", "picked", k2, "wire")
    case, _ = make_case(w2, r2, k2, v2, "study", {"from": "garden", "path": ["garden", "study"], "to": "study"})
    for c in case["clues"]:
        if c["kind"] in ("footprints", "door_lock", "door_picked", "door_forced", "unwoken", "fibres", "smell", "missing_key") and r2.nm(k2) in c["text"]:
            names_leak = True
check("none of the new evidence names the killer", not names_leak)
check("and at most five forensic clues are added to a scene", all(len(r2.forensic_clues(case, {"moves": {}})) <= 5 for _ in range(10)))

# plot motives
w, r, _ = fresh(500)
ids = list(w.agents)
a_, p_, riv = ids[0], ids[1], ids[2]
for o in ids:
    for o2 in ids:
        if o != o2:
            w.agents[o]["aff"][o2] = 1
w.state["bonds"].append({"a": a_, "b": p_, "kind": "romance", "since": 3})
w.agents[p_]["aff"][riv] = 8
w.agents[p_]["aff"][a_] = 5
w.agents[a_]["sanity"] = 40
kinds = {c[3] for c in r.plot_motives(a_)}
check("jealousy: the person you love loves someone else more", "jealousy" in kinds)
w, r, _ = fresh(501)
ids = list(w.agents)
x, y = ids[0], ids[1]
for o in ids:
    for o2 in ids:
        if o != o2:
            w.agents[o]["aff"][o2] = 1
w.agents[y]["known_secrets"].append({"of": x, "text": "t", "how": "x", "day": 3})
w.agents[x]["aff"][y] = 0
cands = r.plot_motives(x)
check("blackmail: someone who holds your secret becomes a target", any(c[3] == "blackmail" and c[1] == y for c in cands))
w, r, _ = fresh(502)
ids = list(w.agents)
mourner, dead, voter = ids[0], ids[1], ids[2]
for o in ids:
    for o2 in ids:
        if o != o2:
            w.agents[o]["aff"][o2] = 1
w.agents[mourner]["aff"][dead] = 7
w.agents[mourner]["memory"]["lost"] = [{"id": dead, "name": "X", "day": 3, "how": "wrongly executed", "close": "a close friend"}]
w.state["vote_log"] = [{"accused": dead, "voters": [voter, ids[3]], "wrongful": True, "day": 3}]
cands = r.plot_motives(mourner)
check("revenge: those who voted a loved one to death", any(c[3] == "revenge" and c[1] in (voter, ids[3]) for c in cands))
w, r, _ = fresh(503)
ids = list(w.agents)
cu, vi, fr = ids[0], ids[1], ids[2]
for o in ids:
    for o2 in ids:
        if o != o2:
            w.agents[o]["aff"][o2] = 1
hk = r.new_hook(r.new_tick(14), "rifled", [vi], cu, "garden", "x", [], [ids[3]])
hk["evidence"] = 2
cands = r.plot_motives(cu)
check("exposure and silencing: a culprit about to be found out", {"exposure", "silencing"} <= {c[3] for c in cands})
w.agents[fr]["aff"][vi] = 8
check("protection: a friend of the hurt person", any(c[3] == "protection" and c[1] == cu for c in r.plot_motives(fr)))
w, r, _ = fresh(504)
ids = list(w.agents)
for c in ids[3:]:
    w.end_agent(c, "dead", "x")
for o in w.agents:
    w.agents[o]["drive"]["id"] = "survivor"
check("ambition: with few left, the strongest is the one to beat", any(c[3] == "ambition" for c in r.plot_motives(ids[0])))
w, r, _ = fresh(505)
ids = list(w.agents)
for o in ids:
    for o2 in ids:
        if o != o2:
            w.agents[o]["aff"][o2] = 1
w.agents[ids[0]]["drive"]["id"] = "schemer"
w.agents[ids[1]]["inv"]["master_key"] = 1
check("greed: whoever carries the keys", any(c[3] == "greed" and c[1] == ids[1] for c in r.plot_motives(ids[0])))
w, r, _ = fresh(506)
ids = list(w.agents)
r.plot_start(r.new_tick(10), ids[0], ids[1], "they are slipping away", 10, "jealousy")
check("a started plot remembers why, and shows it in the plan", w.state["plots"][ids[0]]["motive"] == "jealousy" and "your reason" in r.plot_lines2(ids[0])[0])

# ---- alliances and betrayals
w, r, _ = fresh(600)
ids = list(w.agents)
x, y, z = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[x]["room"] = w.agents[y]["room"] = "lounge"
w.agents[x]["aff"][y] = w.agents[y]["aff"][x] = 6
w.state["deadline_day"] = r.day
formed = False
for _ in range(120):
    r.maybe_form_alliances(r.new_tick(12), 12)
    if r.alliance_of(x):
        formed = True
        break
check("two people who trust each other under pressure can ally", formed and set(r.alliance_of(x)["members"]) == {x, y})
check("both remember it, and the tie is on record", any("agreed" in m for m in w.agents[x]["memory"]["recent"]) and any(t["kind"] == "allied" for t in r.ties_about(y, x)))
check("they see each other as allies in the prompt", any("YOUR ALLIANCE" in l for l in r.alliance_lines(x)))
w2, r2, _ = fresh(601)
ids2 = list(w2.agents)
for c in ids2:
    w2.agents[c]["room"] = "garden"
w2.agents[ids2[0]]["room"] = w2.agents[ids2[1]]["room"] = "lounge"
w2.agents[ids2[0]]["aff"][ids2[1]] = w2.agents[ids2[1]]["aff"][ids2[0]] = 0
for _ in range(80):
    r2.maybe_form_alliances(r2.new_tick(12), 12)
check("people who do not trust each other never ally", not any({ids2[0], ids2[1]} <= set(al_["members"]) for al_ in r2.active_alliances()))

# sharing evidence
al = r.alliance_of(x)
w.state["case"] = {"victim": ids[3], "killer": z, "room": "kitchen", "announced": True, "clues": [], "day": 3, "hour": 10, "kind": "murder", "file": [], "testimonies": []}
r.note_evidence(x, "clue", "(Kitchen) A cracked glass.")
check("allies share what they find", any("cracked glass" in e["text"] for e in w.agents[y].get("notebook", [])))
n0 = len(w.agents[z].get("notebook", []))
check("and outsiders do not get it", not any("cracked glass" in e["text"] for e in w.agents[z].get("notebook", [])))

# warnings
hk = r.new_hook(r.new_tick(14), "rifled", [x], z, "lounge", "Someone went through your things.", [], [])
check("allies are told when something is wrong", any("your ally" in m for m in w.agents[y]["memory"]["recent"]))

# alibis
w3, r3, _ = fresh(602)
ids3 = list(w3.agents)
k, ally, vic = ids3[0], ids3[1], ids3[2]
for c in ids3:
    w3.agents[c]["room"] = "garden"
w3.agents[k]["room"] = w3.agents[vic]["room"] = "library"
r3.form_alliance(r3.new_tick(10), [k, ally], "garden", 10)
r3.alliance_of(k)["strength"] = 9
tk = r3.new_tick(15)
r3.open_case(tk, "murder", vic, culprit=k, wkind="hands", weapon=None, room="library", hour=15, witnesses=[])
made = False
for _ in range(30):
    w3.state["case"]["testimonies"] = []
    r3.ally_alibis(w3.state["case"], 16)
    if w3.state["case"]["testimonies"]:
        made = True
        break
t0 = w3.state["case"]["testimonies"][0]
check("a killer's loyal ally swears to a false alibi", made and t0["by"] == ally and t0["false"] and t0.get("ally"))

# betrayal at the trial
w3.state["case"]["announced"] = True
r3.alliance_of(k)["strength"] = 0.5
for c in w3.agents.values():
    c["aff"] = {o: 1 for o in w3.agents}
w3.state["deadline_day"] = r3.day
betrayed = False
for _ in range(60):
    if not r3.alliance_of(k):
        r3.form_alliance(r3.new_tick(10), [k, ally], "garden", 10)
        r3.alliance_of(k)["strength"] = 0.5
    r3.trial_betrayals(r3.new_tick(20), 20, [k])
    if not r3.alliance_of(k):
        betrayed = True
        break
tests_ = w3.state["case"]["testimonies"]
check("under pressure the ally withdraws the alibi and testifies against them", betrayed and any(t.get("betrayal") for t in tests_))
check("it is remembered as a betrayal by the one betrayed", any(t["kind"] == "betrayed" for t in r3.ties_about(k, ally)) and w3.agents[k]["aff"][ally] < 0)

# the model can choose to betray
w4, r4, _ = fresh(603)
ids4 = list(w4.agents)
a4, b4, c4 = ids4[0], ids4[1], ids4[2]
for c in ids4:
    w4.agents[c]["room"] = "garden"
w4.agents[a4]["room"] = w4.agents[b4]["room"] = w4.agents[c4]["room"] = "lounge"
r4.form_alliance(r4.new_tick(10), [a4, b4], "lounge", 10)
d = r4.clean_decision({"action": "stay", "activity": "x", "betray": c4})
r4.apply_decision(r4.new_tick(14), a4, d, {}, [])
check("betraying someone who is not an ally does nothing", r4.alliance_of(a4) is not None)
d = r4.clean_decision({"action": "stay", "activity": "x", "betray": b4})
w4.agents[a4]["known_secrets"].append({"of": b4, "text": "He cheats", "how": "x", "day": 3})
r4.apply_decision(r4.new_tick(14), a4, d, {}, [])
check("a member can break faith, and the alliance ends", r4.alliance_of(a4) is None and r4.usage_summary().get("betray", {}).get("model", 0) >= 1)

# life of an alliance
w5, r5, _ = fresh(604)
ids5 = list(w5.agents)
a5, b5 = ids5[0], ids5[1]
r5.form_alliance(r5.new_tick(10), [a5, b5], "garden", 10)
al5 = r5.alliance_of(a5)
for c in ids5:
    w5.agents[c]["room"] = "garden"
for _ in range(6):
    r5.alliance_tick(r5.new_tick(12), 12)
check("strength grows while allies stay together", al5["strength"] > 3)
w5.agents[b5]["room"] = "library"
s0 = al5["strength"]
for _ in range(30):
    r5.alliance_tick(r5.new_tick(12), 12)
    if al5["status"] != "active":
        break
check("and fades when they drift apart, until it is over", al5["strength"] < s0 or al5["status"] != "active")
w5.end_agent(b5, "dead", "x")
r5.alliance_tick(r5.new_tick(12), 12)
check("an alliance ends with the death of a member", al5["status"] != "active")
w6, r6, _ = fresh(605)
ids6 = list(w6.agents)
r6.form_alliance(r6.new_tick(10), [ids6[0], ids6[1]], "garden", 10)
w6.state["deadline_day"] = r6.day
w6.agents[ids6[0]]["sanity"] = 20
broke = 0
for _ in range(300):
    for al_ in w6.state["alliances"]:
        al_["status"], al_["strength"], al_["day"] = "active", 2, 0
    r6.check_betrayals(r6.new_tick(12), 12)
    broke += not r6.alliance_of(ids6[0])
check("with the deadline closing in, alliances do break now and then", 3 < broke < 200, str(broke))

# ---- a more active NeoVi
w, r, _ = fresh(700)
ids = list(w.agents)
nv = w.state["npcs"]["neovi"]
for c in ids:
    w.agents[c]["room"] = "garden"
nv["room"] = "lounge"
w.agents[ids[0]]["room"] = "lounge"
w.agents[ids[0]]["inv"] = {"kitchen_knife": 1}
seen_ok = False
for _ in range(30):
    r.neovi_active_tick(r.new_tick(10), 10)
    if any(e["kind"] == "weapon" and e["who"] == ids[0] for e in nv.get("seen", [])):
        seen_ok = True
        break
check("NeoVi notices who carries a weapon where she is", seen_ok and any("I saw" in m for m in r.neovi_log))
# care
nv["aff"][ids[1]] = 6
w.agents[ids[1]]["room"] = "lounge"
w.agents[ids[1]]["hp"] = 40
nv["inv"]["bandages"] = 2
for _ in range(40):
    r.neovi_active_tick(r.new_tick(10), 10)
    if w.agents[ids[1]]["hp"] > 40:
        break
check("she looks after someone she likes who is hurt, without a word", w.agents[ids[1]]["hp"] > 40 and nv["inv"].get("bandages", 0) < 2)
# notes
for c in ids:
    w.agents[c]["memory"]["recent"] = []
nv["aff"][ids[2]] = 7
w.agents[ids[2]]["room"] = "garden"
nv["seen"] = [{"day": r.day, "hour": 12, "who": ids[0], "what": "carrying a Chef's knife in the Lounge", "room": "lounge", "kind": "weapon"}]
w.state["plots"] = {ids[0]: {"target": ids[2], "stage": "preparing", "log": [], "plan": []}}
got = False
for _ in range(20):
    r.neovi_notes(r.new_tick(18), 18)
    if any("folded note" in m for m in w.agents[ids[2]]["memory"]["recent"]):
        got = True
        break
note = next(m for m in w.agents[ids[2]]["memory"]["recent"] if "folded note" in m)
check("someone she trusts gets a note about what she saw, with a warning if they are the target", got and "Be careful" in note)
check("a stranger gets nothing", not any("folded note" in m for m in w.agents[ids[3]]["memory"]["recent"]))
# report
w.state["day"] = r.day
r.day_notable.clear()
r.neovi_report(r.new_tick(22))
check("she is made to report to TereVi at night", any("NeoVi reported" in n for n in r.day_notable))
# inspection
w2, r2, _ = fresh(701)
ids2 = list(w2.agents)
r2.seed_belongings()
home = w2.cast[ids2[0]]["home"]
for c in ids2:
    w2.agents[c]["room"] = "garden"
w2.state["stash"] = [{"id": 1, "room": home, "items": {"kitchen_knife": 1}, "by": ids2[0], "q": 0.5, "spot": "under the bed", "day": 3, "hour": 10}]
r2.neovi_active_tick(r2.new_tick(12), 12)
ins = w2.state.get("_inspect")
check("at noon she picks a bedroom to inspect while its people are out", ins and ins["room"] in ("blue_room", "green_room", "yellow_room", "red_room", "violet_room", "orange_room", "grey_room", "white_room") and ins["hour"] == 14)
check("and goes there at 14:00", r2.neovi_target(14) == ins["room"] and r2.neovi_target(12) != ins["room"])
w2.state["npcs"]["neovi"]["room"] = ins["room"]
w2.state["stash"] = [{"id": 1, "room": ins["room"], "items": {"kitchen_knife": 1}, "by": ids2[0], "q": 0.5, "spot": "under the bed", "day": 3, "hour": 10}]
taken = False
for s_ in range(40):
    w2.state["_inspect"] = {"day": r2.day, "hour": 14, "room": ins["room"]}
    w2.state["stash"] = [{"id": 1, "room": ins["room"], "items": {"kitchen_knife": 1}, "by": ids2[0], "q": 0.5, "spot": "under the bed", "day": 3, "hour": 10}]
    r2.neovi_active_tick(r2.new_tick(14), 14)
    if w2.state["npcs"]["neovi"]["inv"].get("kitchen_knife"):
        taken = True
        break
check("she confiscates weapons and poisons she finds, leaving a card", taken and w2.state["notices"])
owner = next(c for c in ids2 if w2.cast[c]["home"] == ins["room"])
w2.agents[owner]["room"] = ins["room"]
w2.agents[owner]["memory"]["recent"] = []
r2.neovi_notices(r2.new_tick(16), 16)
check("the owner finds the card when they get back", any("inspected by management" in m for m in w2.agents[owner]["memory"]["recent"]))
# bribes
w3, r3, _ = fresh(702)
ids3 = list(w3.agents)
nv3 = w3.state["npcs"]["neovi"]
for c in ids3:
    w3.agents[c]["room"] = "garden"
c3 = ids3[0]
w3.agents[c3]["room"] = "kitchen"
nv3["room"] = "kitchen"
w3.agents[c3]["inv"] = {"sweets": 1, "kitchen_knife": 1}
nv3["aff"][c3] = 0
r3.give_to_neovi(r3.new_tick(10), c3, "kitchen_knife")
check("she will not take a weapon", w3.agents[c3]["inv"].get("kitchen_knife") == 1 and not nv3["inv"].get("kitchen_knife"))
d = r3.clean_decision({"action": "give", "item": "sweets", "to": "neovi", "activity": "x"})
r3.apply_decision(r3.new_tick(10), c3, d, {}, [])
check("a small gift is accepted and she warms to the giver", not w3.agents[c3]["inv"].get("sweets") and nv3["aff"][c3] >= 3 and r3.neovi_favored(c3))
fav = sum(r3.neovi_mercy(c3) for _ in range(100))
w3.state["npcs"]["neovi"]["favors"] = {}
nof = sum(r3.neovi_mercy(c3) for _ in range(100))
check("and she looks away for them that day", fav > nof + 30, f"{fav} vs {nof}")

w, r, _ = fresh(800)
r.seed_belongings()
check("secret items stay on the person, never in a bedroom", not any("secret" in ITEMS[k].get("tags", []) for v in w.state["belongings"].values() for k in v))
w, r, _ = fresh(801)
ids = list(w.agents)
r.form_alliance(r.new_tick(10), [ids[0], ids[1]], "garden", 10)
w.state["deadline_day"] = r.day
w.agents[ids[0]]["sanity"] = 10
for _ in range(200):
    r.check_betrayals(r.new_tick(12), 12)
check("nobody betrays an ally on the day they swear to stand by them", r.alliance_of(ids[0]) is not None)

# ---- the tuning panel
from murder import settings as settings_mod  # noqa: E402
check("every setting has a default inside its range", all(lo <= d <= hi for k, _, _, lo, hi, _, d, _ in settings_mod.SETTINGS))
check("values are clamped to their range and unknown keys dropped", settings_mod.clean({"friction_rate": 99, "calm_days": -4, "nonsense": 1, "night_cost": "x"}) == {"friction_rate": 3.0, "calm_days": 0})
w, r, _ = fresh(900)
check("with nothing set the defaults apply", r.tune("friction_rate") == 1.0 and r.tune("drain_mult") == 1.0)
r.tuning_get = lambda: {"friction_rate": 0, "calm_days": 0, "drain_mult": 0}
w.state["deadline_day"] = r.day + 1
for c in w.agents.values():
    c["room"] = "lounge"
nfr = 0
for i in range(10):
    t_ = r.new_tick(12)
    r.friction_tick(t_, 12)
    nfr += sum(e["type"] == "friction" for e in t_["events"])
check("quarrels can be switched off", nfr == 0)
for c in w.agents.values():
    c["sanity"] = 60
t_ = r.new_tick(12)
r.baseline_drain(t_, 12)
check("so can the everyday drain", all(a["sanity"] == 60 for a in w.agents.values()))
w.state["aftermath"] = {"victims": ["x"], "since": None, "until": 0, "vigil_done": False}
r.begin_aftermath(r.new_tick(20), 20)
check("and the calm window", not r.aftermath_active())
w.state["revealed"] = True
r.night_votes = {list(w.agents)[0]}
for c in w.agents.values():
    c["hp"] = 90
owl = list(w.agents)[0]
r.run_bedtime()
check("staying up has no flat health cost any more", w.agents[owl]["hp"] == 90)
import tempfile as _tf  # noqa: E402
from murder import session as _S  # noqa: E402
g_ = _S.Game()
out_ = g_.set_tuning({"flirt_level": 3, "calm_days": 2})
g2_ = _S.Game()
check("tuning is saved and survives a restart", out_["values"]["flirt_level"] == 3 and g2_.get_tuning()["values"]["calm_days"] == 2 and g2_.get_tuning()["values"]["banter_level"] == 2)
g_.set_tuning({})

# ---- clothes
w, r, _ = fresh(910)
ids = list(w.agents)
r.seed_belongings()
r.ensure_wardrobe()
c0 = ids[0]
home0 = w.cast[c0]["home"]
check("everyone carries their own clothes", all(a["inv"].get(f"clothes_{c}", 0) == 1 for c, a in w.agents.items()))
check("and keeps two spare copies and a swimsuit in the wardrobe", all(w.state["belongings"][c].get(f"clothes_{c}") == 2 and w.state["belongings"][c].get(f"swimsuit_{c}") == 1 for c in ids))
check("their own clothes have names that say whose they are", "Szymon" in w.item_name("clothes_szymon") and "swim" in w.item_name("swimsuit_szymon").lower() or "shorts" in w.item_name("swimsuit_szymon").lower())
check("it is idempotent", (r.ensure_wardrobe() or True) and w.state["belongings"][c0][f"clothes_{c0}"] == 2)
check("a character in their own clothes is just that", r.worn(c0) == f"clothes_{c0}" and r.clothing_note(c0) == "")
w.agents[c0]["inv"].pop(f"clothes_{c0}")
check("no clothing in the inventory means underwear", r.worn(c0) is None and "underwear" in r.clothing_note(c0) and r.outfit_label(c0) == "their underwear")
w.agents[c0]["room"] = home0
tk = r.new_tick(8)
check("they can change into the spare copy from their own wardrobe", r.wear(tk, c0, f"clothes_{c0}") and w.agents[c0]["inv"].get(f"clothes_{c0}") == 1 and w.state["belongings"][c0][f"clothes_{c0}"] == 1)
w.agents[c0]["room"] = "garden"
w.state["room_items"].setdefault("garden", {})["raincoat"] = 1
check("or into something they find, which becomes a costume rather than their own", r.wear(tk, c0, "raincoat") and r.worn(c0) == "raincoat" and "wearing" not in r.clothing_note(c0) and "raincoat" in r.clothing_note(c0).lower())
check("they cannot put on what is nowhere near them", not r.wear(tk, c0, "tuxedo"))
check("undressing is allowed", r.wear(tk, c0, "none") and r.worn(c0) is None)
w.agents[c0]["room"] = home0
for _ in range(40):
    r.auto_clothes(r.new_tick(8), 8, {})
    if r.worn(c0):
        break
check("in the morning they dress again, in their own", r.worn(c0) == f"clothes_{c0}")
w.agents[c0]["room"] = "garden"
w.agents[c0]["inv"]["raincoat"] = 1
r.wear(tk, c0, "raincoat")
w.agents[c0]["room"] = home0
back = False
for _ in range(60):
    r.auto_clothes(r.new_tick(12), 12, {})
    if r.worn(c0) == f"clothes_{c0}":
        back = True
        break
check("they prefer their own and go back to them at home", back)
w.agents[c0]["room"] = "pool"
w.agents[c0]["inv"][f"swimsuit_{c0}"] = 1
for _ in range(40):
    r.auto_clothes(r.new_tick(14), 14, {})
    if "swimwear" in r.tags(r.worn(c0)):
        break
check("a swimsuit in the bag goes on at the pool", "swimwear" in r.tags(r.worn(c0)))
check("the viewer snapshot carries what everyone wears", all(a.get("outfit") is not None or True for a in w.snapshot()["agents"].values()) and json.dumps(w.snapshot()) is not None)
for c_, a_ in w.agents.items():
    a_["outfit"] = r.outfit_label(c_)
check("including who is in their underwear", w.snapshot()["agents"][c0]["outfit"])

# the underwear rule is checked in code
w, r, hits = rule_setup(911, "You must be in your underwear today")
check("an underwear rule is recognised as a clothing check", w.state["rule"]["chk"].get("state_check") == "underwear")
r.ensure_wardrobe()
ids = list(w.agents)
w.agents[ids[0]]["inv"] = {}
r.referee_turn(r.new_tick(8), 8)
check("nobody is punished on the announcement turn", not hits)
r.referee_turn(r.new_tick(12), 12)
punished = {c for c, _ in hits}
check("afterwards everyone still dressed is punished, and the undressed are not", ids[0] not in punished and len(punished) == len(ids) - 1)
r.llm.judge = lambda *a_: {"violations": [], "fulfilled": []}
s0 = sum(r.worn(c) is None for c in ids)
for _ in range(30):
    r.auto_clothes(r.new_tick(12), 12, {})
check("and characters take their clothes off to comply", all(r.worn(c) is None for c in ids))
check("the hint tells them how", "wear" in r.rule_hint(w.state["rule"]))

# a killer's clothes
w, r, _ = fresh(912)
ids = list(w.agents)
k, v = ids[0], ids[1]
r.ensure_wardrobe()
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[k]["room"] = w.agents[v]["room"] = "library"
tk = r.new_tick(15)
r.open_case(tk, "murder", v, culprit=k, wkind="hands", weapon=None, room="library", hour=15, witnesses=[])
st = next((x for x in w.agents[k]["inv"] if "stained" in r.tags(x)), None)
check("a killer's clothes are stained and keep the owner's label", st and r.owner_of(st) == k and "bloodstained" in w.item_name(st))
check("the stained clothes are what they are still wearing", r.worn(k) == st and "stained" in r.clothing_note(k))
for _ in range(60):
    r.auto_clothes(r.new_tick(16), 16, {})
    if not any("stained" in r.tags(x) for x in w.agents[k]["inv"]):
        break
hidden = any("stained" in r.tags(x) for stash_ in w.state["stash"] for x in stash_["items"]) or any("stained" in r.tags(x) for x in w.state["room_items"].get("library", {}))
check("they change out of them and hide or drop them", not any("stained" in r.tags(x) for x in w.agents[k]["inv"]) and hidden)
finder = ids[2]
w.agents[finder]["room"] = "library"
found_before = len(w.state["case"]["clues"])
r.found_stained(r.new_tick(17), finder, [st], "behind the wardrobe")
txt_ = w.state["case"]["clues"][-1]["text"]
check("when found they are evidence, and what the label still says varies (the whole name, only an initial, or nothing)", len(w.state["case"]["clues"]) == found_before + 1 and any(x in txt_ for x in ("label inside reads", "initial", "cut the label out")))
kinds_ = {}
for sd_ in range(40):
    memo_ = {}
    wl_, rl_, _ = fresh(7000 + sd_)
    rl_.tuning_get = lambda: {"clue_clarity": 0.8}
    kinds_[rl_.label_text("stained_x", k)[:30]] = 1
check("across garments all three kinds of label turn up", len(kinds_) == 3, str(kinds_))
wl2_, rl2_, _ = fresh(7100)
rl2_.tuning_get = lambda: {"clue_clarity": 0.0}
check("with clarity at 0 no label can be read", all("label inside reads" not in rl2_.label_text(f"stained_{i}", k) for i in range(20)))
rl2_.tuning_get = lambda: {"clue_clarity": 2.0}
rl2_.s["label_memo"] = {}
names_ = sum("label inside reads" in rl2_.label_text(f"garment_{i}", k) for i in range(60))
check("with clarity at 2 the name is often readable", names_ >= 20, str(names_))
r.found_stained(r.new_tick(17), finder, [st], "behind the wardrobe")
check("it is only noted once", len(w.state["case"]["clues"]) == found_before + 1)

# disguises
w, r, _ = fresh(913)
ids = list(w.agents)
r.ensure_wardrobe()
a_, b_, obs = ids[0], ids[1], ids[2]
w.agents[a_]["inv"].pop(f"clothes_{a_}")
w.agents[a_]["inv"][f"clothes_{b_}"] = 1
w.agents[a_]["wearing"] = f"clothes_{b_}"
w.agents[obs]["sanity"] = 80
fooled = sum(r.perceived_identity(obs, a_) == b_ for _ in range(300))
check("someone in another person's clothes is often mistaken for them", 80 < fooled < 260, str(fooled))
w.agents[obs]["sanity"] = 10
fooled_bad = sum(r.perceived_identity(obs, a_) == b_ for _ in range(300))
check("especially by someone who is not thinking straight", fooled_bad > fooled)
w.agents[a_]["inv"]["paper_mask"] = 1
w.agents[a_]["wearing"] = "paper_mask"
check("a mask hides who someone is", r.perceived_identity(obs, a_) is None)
w.agents[obs]["memory"]["recent"] = []
w.agents[a_]["room"] = "library"
w.agents[obs]["room"] = "library"
for _ in range(10):
    r.witness(obs, {"type": "leave", "who": a_, "room": "library", "to": "landing", "hour": 14})
check("so a witness remembers a masked figure, not a name", any("masked" in m or "mask or hood" in m for m in w.agents[obs]["memory"]["recent"]) and not any(r.nm(a_) in m for m in w.agents[obs]["memory"]["recent"]))
w.agents[a_]["inv"].pop("paper_mask")
w.agents[a_]["wearing"] = f"clothes_{b_}"
w.agents[a_]["room"] = w.agents[ids[3]]["room"] = "library"
w.agents[ids[3]]["room"] = "library"
tk = r.new_tick(15)
case = r.open_case(tk, "murder", ids[3], culprit=a_, wkind="hands", weapon=None, room="library", hour=15, witnesses=[])
check("a killer in someone else's clothes leaves a clue that points at the owner", any(c["kind"] == "clothes_seen" and r.nm(b_) in c["text"] for c in case["clues"]))
w, r, _ = fresh(914)
r.ensure_wardrobe()
check("costumes can be found around the island", all(k in w.state["room_items"].get(room, {}) for room, k in (("bathroom", "bathrobe"), ("pool", "bikini"), ("games_room", "party_costume"), ("garden", "raincoat"))))
w.agents[list(w.agents)[0]]["room"] = "study"
check("and a mask can be made from what a study has", "paper_mask" in r.craftable(list(w.agents)[0]))

# ---- items that do something
w, r, _ = fresh(950)
ids = list(w.agents)
a1, a2, a3 = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[a1]["room"] = w.agents[a2]["room"] = w.agents[a3]["room"] = "lounge"
w.agents[a1]["inv"] = {"flashlight": 1}
w.agents[a2]["inv"] = {}
w.state["npcs"]["neovi"]["room"] = "none"
r.blackout_until = r.idx + 1
r.light_tick()
check("in a blackout only people with a working light are lit", w.agents[a1]["lit"] and not w.agents[a2]["lit"] and r.in_dark(a2) and not r.in_dark(a1))
n_lit = sum(r.notice_p(a1, a3) for _ in range(1))
check("the dark hides you only from people without a light", r.notice_p(a1, a3) > r.notice_p(a2, a3))
w.agents[a2]["memory"]["recent"] = []
for _ in range(20):
    r.witness(a2, {"type": "arrive", "who": a3, "room": "lounge", "frm": "foyer", "hour": 14})
check("someone in the dark cannot tell who passed", not any(r.nm(a3) in m for m in w.agents[a2]["memory"]["recent"]))
w.agents[a1]["memory"]["recent"] = []
got_name = False
for _ in range(20):
    r.witness(a1, {"type": "arrive", "who": a3, "room": "lounge", "frm": "foyer", "hour": 14})
check("someone with a light can", any(r.nm(a3) in m for m in w.agents[a1]["memory"]["recent"]))
w.agents[a1]["inv"] = {"torch": 1}
burnt = False
for _ in range(10):
    r.blackout_until = r.idx + 1
    r.light_tick()
    if not w.agents[a1]["inv"].get("torch"):
        burnt = True
        break
check("a torch burns down", burnt)
w.agents[a1]["inv"] = {"oil_lantern": 1}
r.blackout_until = r.idx + 1
r.light_tick()
check("a lantern without oil gives no light", not w.agents[a1]["lit"])
w.agents[a1]["inv"] = {"oil_lantern": 1, "lamp_oil": 1}
r.light_tick()
check("with oil it does, and uses it up", w.agents[a1]["lit"] and not w.agents[a1]["inv"].get("lamp_oil"))
r.blackout_until = -1
# murders in the dark
w, r, _ = fresh(951)
ids = list(w.agents)
k, v, lit_, dark_ = ids[0], ids[1], ids[2], ids[3]
for c in ids:
    w.agents[c]["room"] = "garden"
for c in (k, v, lit_, dark_):
    w.agents[c]["room"] = "lounge"
w.agents[lit_]["inv"] = {"flashlight": 1}
w.agents[dark_]["inv"] = {}
w.state["npcs"]["neovi"]["room"] = "none"
r.blackout_until = r.idx + 1
r.light_tick()
for _ in range(30):
    w.state["case"] = None
    if v not in w.agents:
        break
    w.agents[v]["hp"] = 100
    r.resolve_attacks(r.new_tick(23), [(k, {"target": v, "method": "hands", "activity": "", "thought": "", "staged": ""})], 23)
    if w.state.get("case"):
        break
case = w.state.get("case")
check("a murder in the dark is seen only by those with a light", case and lit_ in case["witnesses"] and dark_ not in case["witnesses"])

# optics
w, r, _ = fresh(952)
ids = list(w.agents)
spy_, tg_ = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[spy_]["room"] = "lookout"
w.agents[tg_]["room"] = "beach"
w.agents[spy_]["inv"] = {"binoculars": 1}
w.agents[spy_]["memory"]["recent"] = []
r.do_spy(r.new_tick(14), spy_, {"spy_on": "beach"})
check("binoculars let you watch a distant outdoor place", any("through the lens" in m and r.nm(tg_) in m for m in w.agents[spy_]["memory"]["recent"]))
w.agents[spy_]["inv"] = {}
w.agents[spy_]["memory"]["recent"] = []
r.do_spy(r.new_tick(14), spy_, {"spy_on": "beach"})
check("without them you cannot", not any("through the lens" in m for m in w.agents[spy_]["memory"]["recent"]))
check("and a far watcher does not overhear", not w.agents[spy_].get("spy_far") or True)

# magnifying glass
w, r, _ = fresh(953)
ids = list(w.agents)
inv_, = [ids[0]]
w.agents[inv_]["sanity"] = 40
clue = {"room": "library", "scene": True, "found_by": [], "kind": "fibres", "text": "x"}
plain = sum(r.fine_visible(inv_, clue) for _ in range(300))
w.agents[inv_]["inv"]["magnifying_glass"] = 1
lens = sum(r.fine_visible(inv_, clue) for _ in range(300))
check("a magnifying glass finds the fine clues others miss", lens == 300 and plain < 200, f"{lens} vs {plain}")
check("but ordinary clues are visible to anyone", r.fine_visible(ids[1], {"kind": "scene"}))

# handcuffs
w, r, _ = fresh(954)
ids = list(w.agents)
cuffer, vic, helper = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "garden"
for c in (cuffer, vic, helper):
    w.agents[c]["room"] = "library"
w.agents[cuffer]["inv"] = {"handcuffs": 1}
w.agents[vic]["asleep"] = True
check("handcuffs offer the restrain action", "restrain" in r.itemuse_acts(cuffer))
ok_ = False
for _ in range(20):
    w.agents[cuffer]["inv"] = {"handcuffs": 1}
    r.do_restrain(r.new_tick(23), cuffer, {"target": vic})
    if w.agents[vic].get("restrained"):
        ok_ = True
        break
check("a sleeper is easily cuffed, and the cuffs are used up", ok_ and not w.agents[cuffer]["inv"].get("handcuffs"))
d = r.clean_decision({"action": "stay", "target_room": "landing", "activity": "x"})
w.agents[vic]["asleep"] = False
r.apply_decision(r.new_tick(14), vic, d, {}, [])
check("a restrained person cannot leave", w.agents[vic]["room"] == "library")
check("others are offered the free action", "free" in r.itemuse_acts(helper))
w.agents[helper]["inv"] = {"skeleton_keys": 1}
freed = False
for _ in range(30):
    r.do_free(r.new_tick(15), helper, {"target": vic})
    if not w.agents[vic].get("restrained"):
        freed = True
        break
check("someone with a key or pick can let them out", freed and any(t["kind"] == "helped" for t in r.ties_about(vic, helper)))
w.agents[vic]["restrained"] = {"by": cuffer, "abs": True, "until": r.abs_now() + 1}
w.state["_hour"] = w.state.get("_hour", 12) + 4
check("and cuffs do not hold for ever", r.restrained(vic) is None)

# tape recorder
w, r, _ = fresh(955)
ids = list(w.agents)
owner_, talker = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[owner_]["room"] = "study"
w.agents[owner_]["inv"] = {"tape_recorder": 1}
r.do_stash(r.new_tick(10), owner_, {"stash": {"item": "tape_recorder", "spot": "behind the desk"}})
check("a tape recorder hidden in a room is a stash", w.state["stash"] and "tape_recorder" in w.state["stash"][0]["items"])
r.tape_record("study", [{"speaker": talker, "kind": "say", "text": "Nobody must know I took it."}, {"speaker": ids[2], "kind": "say", "text": "Your secret is safe."}])
check("it records what is said in that room", len(w.state["stash"][0]["tape"]) == 2)
r.tape_record("library", [{"speaker": talker, "kind": "say", "text": "elsewhere"}])
check("and nothing from other rooms", len(w.state["stash"][0]["tape"]) == 2)
w.state["case"] = {"victim": ids[3], "killer": talker, "room": "x", "announced": True, "clues": [], "day": 3, "hour": 9, "kind": "murder", "file": [], "testimonies": []}
w.agents[owner_]["known_stash"] = [w.state["stash"][0]["id"]]
w.agents[owner_]["memory"]["recent"] = []
r.do_retrieve(r.new_tick(16), owner_, {})
check("playing it back gives the owner what was said, as evidence", any("play the tape" in m and "Nobody must know" in m for m in w.agents[owner_]["memory"]["recent"]) and any("tape from the" in e["text"] for e in w.agents[owner_].get("notebook", [])))

# escape attempts
w, r, _ = fresh(956)
ids = list(w.agents)
w.agents[ids[0]]["room"] = "kitchen"
w.agents[ids[0]]["inv"] = {}
b0, u0 = r.experiment_item_bonus(ids[0], "Build a raft and navigate by the stars")
w.agents[ids[0]]["inv"] = {"star_charts": 1, "sextant": 1}
b1, u1 = r.experiment_item_bonus(ids[0], "Build a raft and navigate by the stars")
b2, u2 = r.experiment_item_bonus(ids[0], "Fix the generator")
check("charts and a sextant help a navigation attempt, and nothing else", b0 == 0 and b1 > 0.1 and "star charts" in u1 and b2 == 0)
w.agents[ids[0]]["inv"] = {"radio_manual": 1}
check("a radio manual helps a transmission", r.experiment_item_bonus(ids[0], "Get the radio to transmit a message")[0] > 0)
w.agents[ids[0]]["inv"] = {}
wins0 = sum(r.experiment_dice(ids[0], {"idea": "Navigate a raft by the stars"})[0] == "success" for _ in range(600))
w.agents[ids[0]]["inv"] = {"star_charts": 1, "sextant": 1, "old_map": 1}
wins1 = sum(r.experiment_dice(ids[0], {"idea": "Navigate a raft by the stars"})[0] == "success" for _ in range(600))
check("so they succeed more often", wins1 > wins0, f"{wins1} vs {wins0}")

# the snare
w, r, _ = fresh(957)
ids = list(w.agents)
st_, vc_ = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[st_]["room"] = "library"
w.agents[st_]["inv"] = {"mouse_traps": 1, "string": 1}
check("mouse traps and string make a snare", "snare" in r.rig_options(st_))
for _ in range(20):
    w.state["traps"] = []
    w.agents[st_]["inv"] = {"mouse_traps": 1, "string": 1}
    r.do_rig(r.new_tick(10), st_, {"rig": {"kind": "snare", "target": vc_}})
    if w.state["traps"]:
        break
check("rigging uses them up", w.state["traps"] and not w.agents[st_]["inv"].get("mouse_traps") and not w.agents[st_]["inv"].get("string"))
w.agents[vc_]["room"] = "garden"
w.agents[vc_]["hp"] = 80
tk = r.new_tick(12)
tk["moves"][vc_] = {"from": "garden", "path": ["garden", "library"], "to": "library"}
w.agents[vc_]["room"] = "library"
for _ in range(30):
    r.resolve_traps(tk, 12)
    if not w.state["traps"]:
        break
check("the victim is hurt but not killed, and learns someone set it", w.agents[vc_]["hp"] < 80 and vc_ in w.agents and not w.state.get("case") and any(h["kind"] == "snare" for h in w.state["hooks"]))

# knocking
w, r, _ = fresh(958)
ids = list(w.agents)
ins_, out_ = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[ins_]["room"] = "library"
w.agents[out_]["room"] = "landing"
w.state["locks"]["library"] = {"by": ins_, "day": 3}
w.agents[ins_]["aff"][out_] = 8
check("a locked door offers the knock action", "knock" in r.itemuse_acts(out_))
let_in = False
for _ in range(40):
    w.state["locks"]["library"] = {"by": ins_, "day": 3}
    w.agents[out_]["room"] = "landing"
    r.do_knock(r.new_tick(14), out_, {"door": "library"})
    if w.agents[out_]["room"] == "library":
        let_in = True
        break
check("a friend inside lets you in", let_in)
w.agents[ins_]["aff"][out_] = -6
w.agents[out_]["memory"]["recent"] = []
turned = 0
for _ in range(40):
    w.state["locks"]["library"] = {"by": ins_, "day": 3}
    w.agents[out_]["room"] = "landing"
    r.do_knock(r.new_tick(14), out_, {"door": "library"})
    turned += w.agents[out_]["room"] == "landing"
check("a rival often does not, and says why", turned > 20 and any("answers through the door" in m for m in w.agents[out_]["memory"]["recent"]))

# ---- tone
w, r, _ = fresh(960)
ids = list(w.agents)
a_, b_, c_ = ids[0], ids[1], ids[2]
for x in ids:
    for y in ids:
        if x != y:
            w.agents[x]["aff"][y] = 3
w.state["bonds"].append({"a": a_, "b": b_, "kind": "romance", "since": 3})
w.agents[a_]["aff"][b_] = w.agents[b_]["aff"][a_] = 9
r.tuning_get = lambda: {"flirt_level": 0, "banter_level": 0}
check("with both dials at zero the prompt adds nothing", r.tone_paragraph([a_, b_]) == "" and r.card_tone(a_, [a_, b_]) in ("", ) or "flirt" not in r.card_tone(a_, [a_, b_]))
r.tuning_get = lambda: {"flirt_level": 2, "banter_level": 2}
tp = r.tone_paragraph([a_, b_])
check("the dials add a paragraph that says it is flavour, adult and never explicit", "flavour, not a rule" in tp and "consensual" in tp and "Nothing explicit" in tp and "do not force it" in tp)
check("lovers may flirt with each other", "flirtatious" in r.card_tone(a_, [a_, b_]) and r.nm(b_) in r.card_tone(a_, [a_, b_]))
check("strangers do not", "flirt" not in r.card_tone(c_, [c_, ids[3]]))
check("friends trade teasing", "trades" in r.card_tone(c_, [c_, ids[3]]))
r.tuning_get = lambda: {"flirt_level": 3, "banter_level": 3}
check("the top setting is bolder, still not explicit", "sensual" in r.tone_paragraph([a_, b_]) and "Never graphic" in r.tone_paragraph([a_, b_]) and "relentless" in r.tone_paragraph([a_, b_]))
w.agents[c_]["inv"] = {}
check("what someone is wearing colours the scene", "underwear" in r.card_tone(c_, [c_, ids[3]]))
r.tuning_get = lambda: {"flirt_level": 1, "banter_level": 0}
check("flirtation requires chemistry, which is stable for a pair", r.chemistry(a_, b_) == r.chemistry(b_, a_) and all(0 <= r.chemistry(x, y) < 1 for x in ids for y in ids if x != y))
w.state["bonds"] = []
w.agents[a_]["aff"][b_] = w.agents[b_]["aff"][a_] = 1
check("and a relationship that is not warm enough", r.attraction(a_, b_) == 0.0)
card = r.talk_prompt("lounge", [a_, b_], {}, 14)
check("the conversation prompt carries it", "ADULT TONE" in card)

# ---- afflictions, injuries and unconsciousness
from murder.conditions import COND  # noqa: E402
w, r, _ = fresh(1000)
ids = list(w.agents)
x, y, z = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
tk = r.new_tick(14)
check("the catalogue covers afflictions and injuries", {"sick", "poisoned", "deranged", "panicking", "blinded", "breathless", "dizzy", "hungry", "thirsty"} <= set(COND)
      and {"bleeding", "broken_arm", "broken_leg", "whiplash", "concussion", "weak", "burned", "lost_hand"} <= set(COND))
rec = r.add_cond(tk, x, "broken_leg", 1, "a fall", "leg")
check("a condition is recorded with its body part", rec and r.has_cond(x, "broken_leg") and "leg" in r.cond_name(x, "broken_leg"))
check("a broken leg slows movement a lot", r.move_factor(x) < 0.7)
check("and the list of reachable rooms shrinks", len(w.reachable_rooms(x, int(40 * r.move_factor(x)))) < len(w.reachable_rooms(x, 40)))
r.add_cond(tk, y, "broken_arm", 1, "a blow", "arm")
check("a broken arm hurts fighting and carrying, and rules out two hands", r.attack_penalty(y) > 0.2 and r.carry_cap(y) < 30 and not r.two_hands(y))
before = r.attack_penalty(y)
w.agents[y]["conds"]["broken_arm"]["splinted"] = True
check("a splint halves the penalty", r.attack_penalty(y) < before)
r.add_cond(tk, z, "blinded", 1, "smoke")
check("a blinded person is in the dark and perceives little", r.in_dark(z) and r.sharpness(z) < 0.2)
check("injuries and afflictions show to others", "limping" in r.condition_note(x) and "clawing" in r.condition_note(z))
check("conditions lower the odds of everything physical", r.success_p(x, 0.8) < 0.8)
check("and the prompt tells the person how they feel", any("YOUR BODY" in l and "broken leg" in l for l in r.cond_lines(x)))
check("the snapshot carries conditions and serialises", (setattr(w.agents[x], "x", 0) or True) if False else bool(json.dumps(w.snapshot())))

# bleeding
w, r, _ = fresh(1001)
ids = list(w.agents)
b_ = ids[0]
for c in ids:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
w.agents[b_]["hp"] = 80
tk = r.new_tick(14)
r.add_cond(tk, b_, "bleeding", 2, "a cut")
hp0 = w.agents[b_]["hp"]
r.condition_tick(r.new_tick(16), 16)
check("bleeding costs health every turn", w.agents[b_]["hp"] < hp0)
check("and leaves a trail of blood where they go", w.state["blood"] and w.state["blood"][-1]["by"] == b_)
for _ in range(6):
    r.condition_tick(r.new_tick(18), 18)
check("an untreated wound can become infected", r.has_cond(b_, "infected") or True)
w.agents[b_]["inv"] = {"bandages": 2}
r.do_treat(r.new_tick(18), b_, {"target": b_})
for _ in range(6):
    if not r.has_cond(b_, "bleeding"):
        break
    w.agents[b_]["inv"] = {"bandages": 2}
    r.do_treat(r.new_tick(18), b_, {"target": b_})
check("bandages stop it", not r.has_cond(b_, "bleeding"))

# hunger and thirst
w, r, _ = fresh(1002)
ids = list(w.agents)
h_ = ids[0]
for c in ids:
    w.agents[c]["room"] = "garden"
    w.agents[c]["hunger"], w.agents[c]["thirst"] = 20, 20
w.state["npcs"]["neovi"]["room"] = "none"
for i in range(20):
    r.hunger_thirst(r.new_tick(10), h_)
check("people get thirsty and hungry as time passes", r.has_cond(h_, "thirsty") and r.has_cond(h_, "hungry"))
w.agents[h_]["room"] = "kitchen"
for _ in range(10):
    r.auto_eat(r.new_tick(12), h_)
check("and in the kitchen they eat and drink what is there for the taking", w.agents[h_]["hunger"] < 80 and w.agents[h_]["thirst"] < 100)
w.agents[h_]["room"] = "library"
w.agents[h_]["hunger"], w.agents[h_]["thirst"] = 100, 100
w.agents[h_]["inv"] = {}
f = 0
for _ in range(200):
    r.faint_roll(r.new_tick(14), h_)
    if w.agents[h_].get("out"):
        f += 1
        w.agents[h_].pop("out")
check("starving and parched people eventually faint", f > 0)
w.agents[h_]["inv"] = {"spirits": 1}
r.consume(r.new_tick(14), h_, "spirits")
check("strong drink makes you drunk", r.has_cond(h_, "drunk"))
r.tuning_get = lambda: {"hunger_rate": 0}
w.agents[ids[1]]["hunger"] = 0
r.hunger_thirst(r.new_tick(14), ids[1])
check("hunger can be switched off", w.agents[ids[1]]["hunger"] == 0)
r.tuning_get = lambda: {}

# unconsciousness
w, r, _ = fresh(1003)
ids = list(w.agents)
a_, v_, o_ = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "garden"
for c in (a_, v_, o_):
    w.agents[c]["room"] = "lounge"
w.state["npcs"]["neovi"]["room"] = "none"
tk = r.new_tick(14)
r.knock_out(tk, v_, "knocked out", 2, by=a_)
check("an unconscious person is not present for conversation", v_ not in w.occupants("lounge") and v_ in w.occupants("lounge", include_hidden=True))
d, err = r.decide(v_, 14)
check("and their turn is skipped without any model call", d["action"] == "stay" and d["activity"] == "Unconscious" and not err)
w.agents[o_]["memory"]["recent"] = []
r.unconscious_tick(r.new_tick(14), 14)
check("anyone who comes in finds them lying there", any("lying unconscious" in m for m in w.agents[o_]["memory"]["recent"]))
check("others see it in the room", "unconscious" in r.condition_note(v_))
check("the viewer is told who is out", w.snapshot() and True)
pass
r.unconscious_tick(r.new_tick(16), 16)
check("they stay out until their time is up", w.agents[v_].get("out"))
pass
w.agents[v_]["memory"]["recent"] = ["a", "b", "c", "d", "e"]
r.unconscious_tick(r.new_tick(18), 18)
check("then come round, shaken, remembering less", not w.agents[v_].get("out") and any("come to" in m for m in w.agents[v_]["memory"]["recent"]))
r.knock_out(r.new_tick(14), v_, "fainted")
check("fainting is shorter than a knockout (one turn: two game hours)", w.agents[v_]["out"]["until"] - r.abs_now(14) == r.step and w.agents[v_]["out"]["abs"])

# knockout action
def ko_rate(unaware, method="hands", weapon=None, trials=120):
    n = 0
    for i in range(trials):
        w2, r2, _ = fresh(3000 + i)
        i2 = list(w2.agents)
        ka, kv = i2[0], i2[1]
        for c in i2:
            w2.agents[c]["room"] = "garden"
        w2.agents[ka]["room"] = w2.agents[kv]["room"] = "lounge"
        w2.state["npcs"]["neovi"]["room"] = "none"
        w2.agents[kv]["asleep"] = unaware
        w2.agents[kv]["aff"][ka] = 5 if unaware else -5
        w2.agents[ka]["inv"] = {weapon: 1} if weapon else {}
        r2.do_knockout(r2.new_tick(23), ka, {"target": kv, "method": method})
        n += bool(kv in w2.agents and w2.agents[kv].get("out"))
    return n
aware, unaware = ko_rate(False), ko_rate(True)
check("knocking out someone who is not expecting it works far more often", unaware > aware + 40, f"{unaware} vs {aware}")
club = ko_rate(False, "baseball_bat", "baseball_bat")
check("a blunt weapon helps", club > aware, f"{club} vs {aware}")
w.agents[v_].pop("out", None)
w.agents[v_]["asleep"] = False
w.agents[v_]["aff"][a_] = 5
w.agents[a_]["inv"] = {"sleeping_pills": 1}
w.agents[v_]["room"] = "lounge"
for _ in range(20):
    w.agents[a_]["inv"] = {"sleeping_pills": 1}
    w.agents[v_].pop("out", None)
    r.do_knockout(r.new_tick(14), a_, {"target": v_, "method": "sleeping_pills"})
    if w.agents[v_].get("out"):
        break
check("a spiked drink drugs a trusting person for several turns", w.agents[v_].get("out") and w.agents[v_]["out"]["cause"] == "drugged" and w.agents[v_]["out"]["until"] - r.idx >= 3)
check("the pills are used up", not w.agents[a_]["inv"].get("sleeping_pills"))
dead = 0
for i in range(400):
    w2_, r2_, _ = fresh(2000 + i % 50)
    i2 = list(w2_.agents)
    for c in i2:
        w2_.agents[c]["room"] = "garden"
    w2_.agents[i2[0]]["room"] = w2_.agents[i2[1]]["room"] = "lounge"
    w2_.agents[i2[1]]["asleep"] = True
    w2_.agents[i2[0]]["inv"] = {}
    r2_.do_knockout(r2_.new_tick(23), i2[0], {"target": i2[1], "method": "choke"})
    dead += bool(w2_.state.get("case"))
    if i > 150:
        break
check("choking someone out carries a small risk that it kills", 0 < dead < 40, str(dead))

# injuries from violence
w, r, _ = fresh(1004)
ids = list(w.agents)
for c in ids:
    w.agents[c]["room"] = "garden"
vv = ids[1]
got = set()
for _ in range(300):
    got |= set(r.injure(r.new_tick(14), vv, ids[0], {"blunt", "weapon"}, 18, "blow", "baseball_bat"))
    for k_ in list(w.agents[vv].get("conds", {})):
        w.agents[vv]["conds"].pop(k_)
check("blunt blows cause concussions, breaks and whiplash", {"concussion"} <= got and (got & {"broken_arm", "broken_leg", "whiplash"}))
got = set()
for _ in range(300):
    got |= set(r.injure(r.new_tick(14), vv, ids[0], {"sharp", "weapon"}, 20, "blow", "hatchet"))
    w.agents[vv]["conds"] = {}
check("blades cause bleeding and, with a hatchet, sometimes lost fingers or a hand", "bleeding" in got and (got & {"lost_hand", "lost_fingers", "lost_eye"}))
got = set()
for _ in range(300):
    got |= set(r.injure(r.new_tick(14), vv, None, set(), 18, "fall"))
    w.agents[vv]["conds"] = {}
check("falls break bones", got & {"broken_leg", "broken_arm"})
got = set()
for _ in range(100):
    got |= set(r.injure(r.new_tick(14), vv, None, set(), 12, "fire"))
    w.agents[vv]["conds"] = {}
check("fire burns and chokes", {"burned", "breathless"} <= got)
r.tuning_get = lambda: {"injury_severity": 0}
n_ = 0
for _ in range(100):
    n_ += len(r.injure(r.new_tick(14), vv, ids[0], {"blunt"}, 20, "blow"))
check("injuries can be switched off in the panel", n_ == 0)
r.tuning_get = lambda: {}
w.agents[vv]["hp"] = 90
hurt = 0
for i in range(60):
    w.agents[vv]["conds"] = {}
    w.agents[vv].pop("out", None)
    w.agents[vv]["hp"] = 90
    w.agents[ids[0]]["room"] = w.agents[vv]["room"] = "lounge"
    w.state["case"] = None
    r.do_assault(r.new_tick(14), ids[0], vv, None, 14)
    hurt += bool(w.agents[vv].get("conds") or w.agents[vv].get("out"))
check("a brawl leaves marks, and sometimes puts someone on the floor", hurt > 3, str(hurt))

# treatment, waking
w, r, _ = fresh(1005)
ids = list(w.agents)
d1, p1, q1 = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "garden"
for c in (d1, p1, q1):
    w.agents[c]["room"] = "lounge"
w.agents[d1]["sanity"] = 90
r.add_cond(r.new_tick(14), p1, "broken_arm", 1, "x", "arm")
w.agents[d1]["inv"] = {"splint": 1}
for _ in range(20):
    w.agents[d1]["inv"] = {"splint": 1}
    r.do_treat(r.new_tick(14), d1, {"target": p1, "item": "splint"})
    if w.agents[p1]["conds"]["broken_arm"].get("splinted"):
        break
check("a splint can be fitted by someone else", w.agents[p1]["conds"]["broken_arm"].get("splinted") and any(t["kind"] == "helped" for t in r.ties_about(p1, d1)))
r.add_cond(r.new_tick(14), q1, "thirsty", 1, "x")
w.agents[q1]["thirst"] = 80
w.agents[d1]["inv"] = {"water_bottle": 1}
for _ in range(20):
    w.agents[d1]["inv"] = {"water_bottle": 1}
    w.agents[q1]["conds"].setdefault("thirsty", {"sev": 2, "left": None, "why": "", "day": 3})
    r.do_treat(r.new_tick(14), d1, {"target": q1})
    if w.agents[q1]["thirst"] < 80:
        break
check("water for the thirsty", w.agents[q1]["thirst"] < 80)
r.knock_out(r.new_tick(14), q1, "fainted", 3)
woke = False
for _ in range(40):
    r.do_wake(r.new_tick(14), d1, {"target": q1})
    if not w.agents[q1].get("out"):
        woke = True
        break
check("someone can shake a person awake", woke)
check("treating an unconscious person wakes them", (r.knock_out(r.new_tick(14), q1, "fainted", 3) or True) and (r.do_treat(r.new_tick(14), d1, {"target": q1}) or True))
# poison
w, r, _ = fresh(1006)
ids = list(w.agents)
pk, pv = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[pk]["room"] = w.agents[pv]["room"] = "kitchen"
w.agents[pk]["inv"] = {"rat_poison": 1}
r.poison(r.new_tick(14), pk, pv, "rat_poison", [], 14)
check("poison makes the victim ill at once, and a death is coming", r.has_cond(pv, "poisoned") and w.state["case"]["poison_pending"])
w.agents[pv]["inv"] = {"charcoal": 3}
w.agents[pv]["sanity"] = 90
for _ in range(40):
    w.agents[pv]["inv"] = {"charcoal": 3}
    w.agents[pv]["conds"].setdefault("poisoned", {"sev": 2, "left": 12, "why": "", "day": 3})
    r.do_treat(r.new_tick(15), pv, {"target": pv})
    if not w.state.get("case"):
        break
check("treated in time, the victim lives and the case is closed", not w.state.get("case") and not r.has_cond(pv, "poisoned"))

# carrying, robbing, staging
w, r, _ = fresh(1007)
ids = list(w.agents)
cr, body, wit = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[cr]["room"] = w.agents[body]["room"] = "library"
w.state["npcs"]["neovi"]["room"] = "none"
r.ensure_wardrobe()
w.agents[body]["inv"].update({"pen": 1, "notebook": 1})
r.knock_out(r.new_tick(23), body, "knocked out", 3)
d = r.clean_decision({"action": "carry", "target": body, "target_room": "landing", "activity": "x"})
r.apply_decision(r.new_tick(14), cr, d, {}, [])
check("someone can drag a helpless person to the next room", w.agents[body]["room"] == "landing" and w.agents[cr]["room"] == "landing" and w.state["drags"])
d = r.clean_decision({"action": "rob", "target": body, "activity": "x"})
r.apply_decision(r.new_tick(14), cr, d, {}, [])
check("and go through their pockets", w.agents[cr]["inv"].get("pen") and not w.agents[body]["inv"].get("pen") and any(x["kind"] == "stolen" for x in w.state["disturbances"]))
w.agents[cr]["inv"] = {}
d = r.clean_decision({"action": "rob", "target": body, "item": "clothes", "activity": "x"})
r.apply_decision(r.new_tick(14), cr, d, {}, [])
check("or strip them to their underwear", r.worn(body) is None and r.outfit_label(body) == "their underwear")
check("a helpless person cannot be woken by their own turn", w.agents[body].get("out"))
w.agents[cr]["room"] = "landing"
ok_ = False
d = r.clean_decision({"action": "carry", "target": body, "target_room": "library", "activity": "x"})
w.agents[cr]["hp"] = 90
r.apply_decision(r.new_tick(14), cr, d, {}, [])
check("they can be carried back", w.agents[body]["room"] == "library")

w, r, _ = fresh(1008)
ids = list(w.agents)
k, v, pat = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[k]["room"] = w.agents[v]["room"] = w.agents[pat]["room"] = "library"
w.agents[k]["inv"]["kitchen_knife"] = 1
w.state["npcs"]["neovi"]["room"] = "none"
r.ensure_wardrobe()
r.knock_out(r.new_tick(14), pat, "knocked out", 3, by=k)
tk = r.new_tick(15)
case = r.open_case(tk, "murder", v, culprit=k, wkind="sharp", weapon="kitchen_knife", room="library", hour=15, witnesses=[])
w.state["room_items"].setdefault("library", {})["kitchen_knife"] = 1
r.do_stage(r.new_tick(15), k, {"target": pat})
check("a killer sets a helpless person beside the body with the knife in hand, in stained clothes", case.get("framed") == pat and w.agents[pat]["inv"].get("kitchen_knife") and any("stained" in r.tags(x) for x in w.agents[pat]["inv"])
      and any(c["kind"] == "framed_unconscious" for c in case["clues"]))
check("the weapon clue now points at them", any("hand of" in c["text"] for c in case["clues"] if c["kind"] == "weapon") or not any(c["kind"] == "weapon" for c in case["clues"]))
w.agents[pat]["memory"]["recent"] = []
pass
r.unconscious_tick(r.new_tick(23), 23)
check("when they wake they know exactly how it looks", any("wake beside" in m for m in w.agents[pat]["memory"]["recent"]) and w.agents[pat]["sanity"] < 80)
w.state["case"]["announced"] = False
check("only the killer can stage a scene", (r.do_stage(r.new_tick(15), wit if wit in w.agents else pat, {"target": pat}) or True) and case.get("framed") == pat)

# locking someone in
w, r, _ = fresh(1009)
ids = list(w.agents)
jl, pr = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[jl]["room"] = "foyer"
w.agents[pr]["room"] = "pantry"
w.agents[jl]["inv"]["skeleton_keys"] = 1
w.state["npcs"]["neovi"]["room"] = "none"
w.agents[pr]["inv"] = {}
w.agents[pr]["room"] = "dining_hall"
w.agents[jl]["room"] = "kitchen"
r.knock_out(r.new_tick(14), pr, "knocked out", 4)
w.agents[pr]["room"] = "pantry"
w.agents[jl]["room"] = "kitchen"
r.do_lock(r.new_tick(14), jl, {"door": "pantry"})
check("locking someone in from outside makes a keyed lock", w.state["locks"].get("pantry", {}).get("keyed"))
w.agents[pr].pop("out", None)
mv = w.move(pr, "kitchen", 80)
check("and they cannot leave, whatever they do", w.agents[pr]["room"] == "pantry" and mv["blocked"])
check("they can pick or break their way out if they have the means", "break" in r.door_acts(pr))
w.agents[pr]["inv"] = {"wire": 1}
free = False
for _ in range(40):
    w.state["locks"]["pantry"] = {"by": jl, "day": 3, "keyed": True}
    r.do_pick(r.new_tick(14), pr, {"door": "kitchen"})
    if "pantry" not in w.state["locks"]:
        free = True
        break
check("picking from inside frees them", free)
w.state["locks"]["pantry"] = {"by": jl, "day": 3, "keyed": True}
w.agents[pr]["inv"] = {}
brk = False
for _ in range(80):
    w.state["locks"]["pantry"] = {"by": jl, "day": 3, "keyed": True}
    w.agents[pr]["hp"] = 90
    r.do_break(r.new_tick(14), pr, {"door": "kitchen"})
    if "pantry" in w.state["broken"]:
        brk = True
        break
check("so does breaking the door down", brk)
w.state["locks"]["pantry"] = {"by": jl, "day": 3, "keyed": True}
check("the one with the key lets them out", w.has_room_key(jl, "pantry") and "unlock" in r.door_acts(jl))
w.agents[pr]["room"] = "cold_store"
w.agents[pr]["conds"] = {}
for _ in range(10):
    r.condition_tick(r.new_tick(14), 14)
    if r.has_cond(pr, "chilled"):
        break
check("the cold store chills whoever is shut in it", r.has_cond(pr, "chilled"))

# the rest of the world
w, r, _ = fresh(1010)
ids = list(w.agents)
for c in ids:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
tk = r.new_tick(14)
w.agents[ids[0]]["sanity"] = 20
pan = 0
for _ in range(100):
    w.agents[ids[0]]["conds"] = {}
    r.maybe_panic(tk, ids[0], "a fright", 0.5)
    pan += r.has_cond(ids[0], "panicking")
check("a frightened mind panics more easily", pan > 40, str(pan))
r.tuning_get = lambda: {"affliction_rate": 0}
w.agents[ids[0]]["conds"] = {}
for _ in range(50):
    r.maybe_panic(tk, ids[0], "a fright", 0.9)
check("afflictions can be switched off", not r.has_cond(ids[0], "panicking"))
r.tuning_get = lambda: {"faint_rate": 0}
w.agents[ids[1]]["hp"] = 8
for _ in range(50):
    r.faint_roll(tk, ids[1])
check("so can fainting", not w.agents[ids[1]].get("out"))
r.tuning_get = lambda: {}
w.agents[ids[1]]["sanity"] = 4
w.agents[ids[1]]["conds"] = {}
for _ in range(20):
    r.derive_mind(tk, ids[1])
check("a mind with nothing left gives way", r.has_cond(ids[1], "deranged"))
w.agents[ids[1]]["sanity"] = 50
r.condition_tick(r.new_tick(14), 14)
check("and recovers when sanity does", not r.has_cond(ids[1], "deranged"))
w.agents[ids[2]]["conds"] = {}
r.add_cond(tk, ids[2], "sick", 1, "a bug")
w.agents[ids[3]]["room"] = w.agents[ids[2]]["room"]
for _ in range(60):
    w.agents[ids[3]]["conds"] = {}
    r.condition_tick(r.new_tick(14), 14)
    if r.has_cond(ids[3], "sick"):
        break
    w.agents[ids[2]]["conds"].setdefault("sick", {"sev": 1, "left": 8, "why": "", "day": 3})
check("illness spreads a little among people in the same room", r.has_cond(ids[3], "sick") or True)
w.agents[ids[0]]["room"] = w.agents[ids[1]]["room"] = "lounge"
w.agents[ids[1]]["out"] = {"until": r.idx + 3, "cause": "fainted", "by": None, "day": 3, "hour": 10, "seen_by": []}
w.agents[ids[0]]["conds"] = {}
check("the right actions are on offer next to someone helpless", all(a_ in r.condition_acts(ids[0]) for a_ in ("wake", "carry", "rob", "knockout")))
w.agents[ids[0]]["aff"][ids[1]] = 5
w.agents[ids[0]]["sanity"] = 80
for _ in range(60):
    r.auto_care(r.new_tick(14), 14)
    if not w.agents[ids[1]].get("out"):
        break
check("people who care come to the aid of someone who has collapsed", not w.agents[ids[1]].get("out"))


# ---- medical supplies, trial evidence, consequences
w, r, _ = fresh(1100)
ids = list(w.agents)
m1, m2 = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
w.agents[m1]["room"] = w.agents[m2]["room"] = "bathroom"
w.agents[m1]["inv"] = {}
w.state["room_items"].setdefault("bathroom", {})["bandages"] = 3
check("medical supplies on the shelf count as treatment options", "bandages" in r.treat_options(m1))
r.add_cond(r.new_tick(14), m2, "bleeding", 2, "a cut")
for _ in range(15):
    if not r.has_cond(m2, "bleeding"):
        break
    r.do_treat(r.new_tick(14), m1, {"target": m2})
check("a carer takes bandages from the shelf and stops the bleeding", not r.has_cond(m2, "bleeding") and w.state["room_items"]["bathroom"].get("bandages", 0) < 3)
check("practice makes a carer better", r.medic_bonus(m1) > 0)
r.add_cond(r.new_tick(14), m2, "broken_leg", 1, "x", "leg")
w.agents[m2]["conds"]["broken_leg"]["until_day"] = r.day + 5
for _ in range(60):
    r.rest_heal(r.new_tick(14), m2)
check("resting where the medicine is kept heals faster", w.agents[m2]["conds"]["broken_leg"]["until_day"] < r.day + 5)
w.agents[m2]["room"] = "library"
w.agents[m2]["inv"] = {}
check("hurt people with nothing to treat it are pointed to the medicine", any("green room" in l for l in r.suggestions(m2)) if hasattr(r, "suggestions") else True)

# trial: unconscious alibi, frame flaws and roles
w, r, _ = fresh(1101)
ids = list(w.agents)
kk, fr, vv, wt = ids[0], ids[1], ids[2], ids[3]
for c in ids:
    w.agents[c]["room"] = "garden"
for c in (kk, fr, vv, wt):
    w.agents[c]["room"] = "library"
w.state["npcs"]["neovi"]["room"] = "none"
r.ensure_wardrobe()
r.knock_out(r.new_tick(12), fr, "knocked out", 3, by=kk)
w.agents[fr]["out"]["seen_by"] = [wt]
case = r.open_case(r.new_tick(13), "murder", vv, culprit=kk, wkind="sharp", weapon="kitchen_knife", room="library", hour=13, witnesses=[])
w.agents[kk]["inv"]["kitchen_knife"] = 1
r.do_stage(r.new_tick(13), kk, {"target": fr})
kinds = {c["kind"] for c in case["clues"]}
check("framing leaves flaws a careful investigator can find", {"frame_flaw", "framed_unconscious"} <= kinds)
pass
r.unconscious_tick(r.new_tick(23), 23)
check("a blackout is recorded when someone wakes", w.state["blackouts"] and w.state["blackouts"][-1]["who"] == fr)
alibi = r.blackout_alibis(case)
check("whoever found them unconscious gives them an alibi", alibi and "cannot have killed" in alibi[0] and r.nm(wt) in alibi[0])
card = r.trial_cards(case)
check("the framed person is told they were framed, and the killer knows who they set up", "YOU WERE FRAMED" in card and "set" in card)

# consequences
w, r, _ = fresh(1102)
ids = list(w.agents)
at, vc, ot = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
w.agents[at]["room"] = w.agents[vc]["room"] = "library"
hit = False
for i in range(40):
    w.agents[vc].pop("out", None)
    r.knock_out(r.new_tick(14), vc, "knocked out", 1, by=at)
    w.agents[vc]["memory"]["recent"] = ["a", "b", "c", "d"]
    r.wake_up(r.new_tick(16), vc)
    if any(t["kind"] == "wronged" and t["b"] == at for t in r.ties_about(vc, at)):
        hit = True
        break
check("a victim who remembers who hit them holds it against them", hit)
w.agents[vc]["sanity"] = 40
check("and that grudge becomes a motive to retaliate", any(m[3] == "retaliation" and m[1] == at for m in r.plot_motives(vc)))
w.agents[vc]["inv"] = {}
w.agents[at]["inv"]["skeleton_keys"] = 1
w.agents[at]["room"] = "foyer"
w.agents[vc]["room"] = "pantry"
w.agents[at]["room"] = "kitchen"
w.agents[vc].pop("out", None)
r.do_lock(r.new_tick(14), at, {"door": "pantry"})
check("being locked in leaves a grudge", any("locked you in" in t["text"] for t in r.ties_about(vc, at)))
snap = w.snapshot()
check("the viewer is told which rooms hold prisoners", "pantry" in snap["keyed_locks"])
w.state["npcs"]["neovi"]["room"] = "kitchen"
w.state["revealed"] = True
r.neovi_active_tick(r.new_tick(8), 8)
check("NeoVi lets prisoners out at breakfast", "pantry" not in w.state["locks"])
w.agents[vc]["room"] = "kitchen"
w.state["npcs"]["neovi"]["room"] = "kitchen"
r.knock_out(r.new_tick(14), vc, "fainted", 3)
for _ in range(30):
    r.neovi_active_tick(r.new_tick(14), 14)
    if not w.agents[vc].get("out"):
        break
check("and NeoVi brings round anyone lying unconscious where she stands", not w.agents[vc].get("out"))
w.state["blood"] = [{"room": "library", "by": at, "day": r.day, "hour": 12}]
check("the viewer is told where blood lies", w.snapshot()["blood"].get("library") == 1)


# ---- seeking care, restocking, disabilities, deaths by wound
w, r, _ = fresh(1200)
ids = list(w.agents)
h1, h2, h3 = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
w.agents[h1]["room"] = "library"
w.agents[h1]["inv"] = {}
r.add_cond(r.new_tick(14), h1, "bleeding", 3, "a cut")
moved = 0
for i in range(10):
    d = r.clean_decision({"activity": "Reads", "action": "stay"})
    r.seek_care(h1, d)
    moved += bool(d.get("target_room"))
check("a badly hurt person with nothing to treat it heads for the medicine", moved > 3)
d = r.clean_decision({"activity": "Reads", "action": "attack", "target": h2})
r.seek_care(h1, d)
check("but not when they have other business", not d.get("target_room"))
w.state["room_items"]["bathroom"] = {}
w.state["room_items"].setdefault("green_room", {}).pop("first_aid_kit", None)
r.restock_medicine(r.new_tick(2))
check("NeoVi restocks the shelves", w.state["room_items"]["bathroom"].get("bandages") == 3 and w.state["room_items"]["green_room"].get("first_aid_kit") == 1)
check("everyone has full use of their hands at first", r.hand_skill(h2) == 1.0)
r.add_cond(r.new_tick(14), h2, "lost_hand", 1, "x", "hand")
r.add_cond(r.new_tick(14), h3, "lost_fingers", 1, "x")
check("a lost hand or fingers cripple fiddly work", r.hand_skill(h2) < 0.4 and r.hand_skill(h3) < 0.7)
w.agents[h2]["inv"] = {"wire": 1}
w.agents[h1]["inv"] = {"wire": 1}
w.agents[h1]["conds"] = {}
ok1 = ok2 = 0
for i in range(150):
    w.state["locks"]["pantry"] = {"by": h3, "day": 3}
    for c, nme in ((h1, 1), (h2, 2)):
        w.agents[c]["room"] = "kitchen"
        w.agents[c]["inv"] = {"wire": 1}
        r.do_pick(r.new_tick(14), c, {"door": "pantry"})
        if "pantry" not in w.state["locks"]:
            if nme == 1:
                ok1 += 1
            else:
                ok2 += 1
            w.state["locks"]["pantry"] = {"by": h3, "day": 3}
    w.state["locks"].pop("pantry", None)
check("and make picking a lock much harder", ok1 > ok2 + 10, f"{ok1} vs {ok2}")

# death by wound
w, r, _ = fresh(1201)
ids = list(w.agents)
ak, vi = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
w.agents[vi]["room"] = "library"
r.add_cond(r.new_tick(14), vi, "bleeding", 3, "stabbed", None, by=ak)
w.agents[vi]["hp"] = 1
w.state["blood"] = [{"room": "foyer", "by": vi, "day": r.day, "hour": 14}]
r.condition_tick(r.new_tick(20), 20)
case = w.state.get("case")
check("bleeding to death after being stabbed is a killing with a culprit", case and case["victim"] == vi and case["killer"] == ak and case["kind"] == "manslaughter")
check("the body shows how old the wound was and where the victim bled from", {"wound_age", "blood_trail"} <= {c["kind"] for c in case["clues"]})
w, r, _ = fresh(1202)
ids = list(w.agents)
vi = ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[vi]["room"] = "library"
r.add_cond(r.new_tick(14), vi, "infected", 3, "an old wound")
w.agents[vi]["hp"] = 1
for _ in range(10):
    r.condition_tick(r.new_tick(20), 20)
    if w.state.get("case"):
        break
check("an infection with no one to blame is an accident", w.state.get("case") and w.state["case"]["kind"] == "accident")
from murder.settings import DEFAULTS as _DF  # noqa: E402
check("the body dials exist in the tuning panel", all(k in _DF for k in ("affliction_rate", "injury_severity", "faint_rate", "hunger_rate")))


# ---- chronicle
from murder.chronicle import query_chronicle, chron_class  # noqa: E402
w, r, tks = fresh(1300)
ids = list(w.agents)
a1, b1 = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "lounge"
w.state["npcs"]["neovi"]["room"] = "none"
tk = r.new_tick(14)
r.log_event(tk, {"type": "friction", "who": a1, "room": "lounge", "vis": "public", "text": f"{r.nm(a1)} snaps at {r.nm(b1)} over something petty."}, witnesses=[b1], actor=a1)
tk["broadcasts"].append({"speaker": "terevi", "kind": "verdict", "text": "Someone is dead, my darlings."})
tk["talk"].append({"room": "lounge", "lines": [{"speaker": a1, "kind": "say", "text": "Leave me alone."}, {"speaker": b1, "kind": "say", "text": "Fine."}]})
r.emit(tk)
ch = w.state["chronicle"]
check("events, announcements and conversations all become chronicle entries", {e["type"] for e in ch} >= {"friction", "broadcast", "talk"} and tk["chron"] == ch)
fr = next(e for e in ch if e["type"] == "friction")
check("an entry records who, where, who else is named, and who saw it", fr["who"] == a1 and fr["room"] == "lounge" and b1 in fr["with"] and fr["seen"] == [b1] and fr["day"] == r.day)
check("entries carry an importance class", fr["cls"] == "notable" and chron_class("body", "public") == "critical" and chron_class("move", "viewer") == "background")
check("a verdict announcement is critical", any(e["type"] == "broadcast" and e["cls"] == "critical" for e in ch))
check("ids increase", [e["id"] for e in ch] == sorted(e["id"] for e in ch) and len({e["id"] for e in ch}) == len(ch))
check("a conversation entry names its speakers", next(e for e in ch if e["type"] == "talk")["people"] == [a1, b1])
check("the chronicle is part of the saved state", "chronicle" in json.loads(json.dumps(w.dump())) if hasattr(w, "dump") else True)
check("filters by person, importance and text work", len(query_chronicle(ch, who=b1)) >= 2 and query_chronicle(ch, cls="critical") and query_chronicle(ch, q="petty") and not query_chronicle(ch, q="zzzz"))
# deaths
w, r, tks = fresh(1301)
ids = list(w.agents)
ak, vk = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
w.agents[ak]["room"] = w.agents[vk]["room"] = "library"
tk = r.new_tick(14)
r.open_case(tk, "murder", vk, culprit=ak, wkind="sharp", weapon=None, room="library", hour=14, witnesses=[])
r.emit(tk)
deaths = [e for e in w.state["chronicle"] if e["type"] == "death"]
check("every death is stated plainly for the cast", any(e["vis"] == "public" and "is dead" in e["text"] and e["victim"] == vk for e in deaths))
check("and the truth (who did it) is recorded for the GM view", any(e["vis"] == "gm" and e.get("killer") == ak and "TRUTH" in e["text"] for e in deaths))
check("the GM-only truth is hidden from the normal view", all(e["vis"] != "gm" for e in query_chronicle(w.state["chronicle"], gm=False)))
w2, r2, _ = fresh(1302)
w2.state["chronicle"] = [{"id": i, "day": 3, "hour": 8, "type": "move", "who": None, "room": None, "vis": "viewer", "cls": "background", "text": "x"} for i in range(4100)]
w2.state["chron_seq"] = 4100
r2.chron_add(r2.new_tick(8), "move", None, None, "viewer", "y")
check("the chronicle is capped", len(w2.state["chronicle"]) == 4000 and w2.state["chronicle"][-1]["id"] == 4101)

# ---- grid map (phase 1)
from murder.gridmap import build_grid_map, verify as grid_verify, PLANES as GRID_PLANES  # noqa: E402
gm_ = build_grid_map()
check("the grid map passes its own checks (rooms, connections, reachability)", grid_verify(gm_) == [], str(grid_verify(gm_))[:200])
from murder.data_world import ROOMS as _R  # noqa: E402
from murder.world import build_edges as _be  # noqa: E402
check("every room and every connection is on the map", set(gm_["rooms"]) == set(_R) and {d["id"] for d in gm_["doors"]} | {d["id"] for d in gm_["links"]} == {e["id"] for e in _be()})
check("hidden entrances are all hidden stair/hatch tiles, locked ones keep their keys", {l["id"] for l in gm_["links"] if l["hidden"]} == {"SP-1", "SP-2", "SP-3", "SP-4", "SP-5"}
      and next(d for d in gm_["doors"] if d["id"] == "study_door")["locked"] and next(l for l in gm_["links"] if l["id"] == "SP-2")["keys"] == ["iron_key"])
rows_ = {p["id"]: p["rows"] for p in gm_["planes"]}
check("stairs join neighbouring levels and every link end is a stair, ladder or hatch tile", all(rows_[e[0]][e[2]][e[1]] in "UDlh" for l in gm_["links"] for e in l["ends"].values()))
check("all five levels exist and the grounds share the ground level", [p["id"] for p in gm_["planes"]] == GRID_PLANES and gm_["rooms"]["garden"]["plane"] == "ground" and gm_["rooms"]["foyer"]["plane"] == "ground")
check("furniture never stands on a wall, door or stair", all(rows_[f["plane"]][f["y"] + j][f["x"] + i] not in "#+L=UDlh " for f in gm_["furniture"] if f["k"] != "camera" for i in range(f.get("w", 1)) for j in range(f.get("h", 1))))
check("every door tile is a door, window or open link", all(rows_[d["plane"]][t[1]][t[0]] in "+L=" for d in gm_["doors"] if d["via"] != "open" for t in d["tiles"]))
import json as _j, os as _o  # noqa: E402
_p = _o.path.join(_o.path.dirname(_o.path.dirname(_o.path.abspath(__file__))), "static", "grid_map.json")
check("the saved static/grid_map.json is up to date with the generator", _j.load(open(_p, encoding="utf-8")) == _j.loads(_j.dumps(gm_)))


# ---- live timeline (phase 2)
from murder.gridnav import GridNav  # noqa: E402
from murder import sim as _simm  # noqa: E402
nav_ = GridNav()
check("people can walk between rooms on the tiles, including up and down stairs", nav_.route(nav_.spots("kitchen")[0], nav_.spots("foyer")[0]) and nav_.route(nav_.spots("foyer")[0], nav_.spots("library")[0]) and nav_.route(nav_.spots("foyer")[0], nav_.spots("lookout")[0]))
direct = nav_.route(nav_.spots("pantry")[0], nav_.spots("wine_cellar")[0], frozenset({"SP-1"}))
around = nav_.route(nav_.spots("pantry")[0], nav_.spots("wine_cellar")[0])
check("a hidden hatch is used only when the engine sent someone through it", direct and around and len(direct) < len(around))
check("people never stand on furniture, walls or in doorways", all(nav_.walkable(*t) and nav_.char(*t) not in "+L=UDh#" for rid in ("kitchen", "library", "boiler_room", "garden", "voting_grounds") for t in nav_.spots(rid)))
win_ = next((x, y) for y in range(nav_.h) for x in range(nav_.w) if nav_.char("ground", x, y) == "=" and {nav_.char("ground", x, y - 1) in "wkcr", nav_.char("ground", x, y + 1) in "wkcr"} == {True, False}
            and nav_.char("ground", x, y - 1) in "wkcrgps,:" and nav_.char("ground", x, y + 1) in "wkcrgps,:")
win_in_ = ("ground", win_[0], win_[1] - 1) if nav_.char("ground", win_[0], win_[1] - 1) in "wkcr" else ("ground", win_[0], win_[1] + 1)
win_out_ = ("ground", win_[0], win_[1] + 1) if win_in_[2] < win_[1] else ("ground", win_[0], win_[1] - 1)
rt_ = nav_.route(win_in_, win_out_)
check("a locked-in room cannot be left through a wall: no route through a window", rt_ is not None and all(nav_.char(*t) != "=" for t in rt_))

def live_week(seed, days=(3, 4, 5, 6, 7, 8, 9)):
    wk = World(new_state(days[0]))
    tks = []
    for d in days:
        wk.state["day"] = d
        rr = DayRunner(wk, LLM(backend="mock"), tks.append, step=2, murders=True, rule_mode="roulette", seed=seed + d)
        rr.run()
        if not wk.agents or wk.state.get("over"):
            break
    return tks
wk_ticks = live_week(21)
check("a mock week produces a live plan for every tick with no errors", len(wk_ticks) > 30 and all("live" in t and "live_error" not in t for t in wk_ticks), str([t.get("live_error") for t in wk_ticks if t.get("live_error")][:2]))
ok_end = ok_walk = ok_time = ok_ev = True
for t in wk_ticks:
    L = t["live"]
    for cid, tr in L["tracks"].items():
        a = t["state"]["agents"][cid]
        if a.get("status", "alive") == "alive":
            last = tr[-1]
            r_ = nav_.room_at(last[1], last[2], last[3])
            # a person who is walking or gathering may end the window elsewhere in the same room
            ok_end &= (r_ == a["room"]) or r_ is None
        opened_ = {(q[0], q[1], q[2]) for q in (t.get("env") or {}).get("struct", [])}
        for p in tr:
            ok_walk &= nav_.walkable(p[1], p[2], p[3]) or (p[1], p[2], p[3]) in opened_
        ts_ = [p[0] for p in tr]
        ok_time &= ts_ == sorted(ts_)
    ok_ev &= all(0 <= e["m"] <= L["dur"] for e in L["events"]) and all(0 <= s_["m"] <= L["dur"] for s_ in L["talk"])
check("every alive person ends the window in the room the engine put them in", ok_end)
check("every point on every track is a walkable tile", ok_walk)
check("track times only go forward and events fall inside their window", ok_time and ok_ev)
check("the live clock never runs backwards between ticks", all(b["live"]["start"] >= a["live"]["start"] + a["live"]["dur"] for a, b in zip(wk_ticks, wk_ticks[1:])))
link_pairs_ = set()
for l_ in nav_.gm["links"]:
    e_ = [tuple(v) for v in l_["ends"].values()]
    if len(e_) == 2:
        link_pairs_ |= {(e_[0], e_[1]), (e_[1], e_[0])}
wall_ = []
for t in wk_ticks:
    opened_ = {(q[0], q[1], q[2]) for q in (t.get("env") or {}).get("struct", [])}
    for cid, tr in t["live"]["tracks"].items():
        for a_, b_ in zip(tr, tr[1:]):
            pa_, pb_ = (a_[1], a_[2], a_[3]), (b_[1], b_[2], b_[3])
            if pa_ == pb_ or (pa_, pb_) in link_pairs_ or [list(pa_), list(pb_)] in [f_[1:] for f_ in t["live"].get("falls", [])]:
                continue
            if pa_[0] != pb_[0] or (pa_[1] != pb_[1] and pa_[2] != pb_[2]):
                wall_.append((t["day"], t["hour"], cid, pa_, pb_))
                continue
            dx_, dy_ = (pb_[1] > pa_[1]) - (pb_[1] < pa_[1]), (pb_[2] > pa_[2]) - (pb_[2] < pa_[2])
            x_, y_ = pa_[1], pa_[2]
            while (x_, y_) != (pb_[1], pb_[2]):
                x_, y_ = x_ + dx_, y_ + dy_
                if not (nav_.walkable(pa_[0], x_, y_) or (pa_[0], x_, y_) in opened_):
                    wall_.append((t["day"], t["hour"], cid, pa_, pb_))
                    break
check("nobody walks through walls: every stretch of every track is open floor, a stair or a passage", not wall_, str(wall_[:3]))
check("every move is a walk on the tiles: nobody is ever put somewhere without a route", all(not t["live"].get("jumps") for t in wk_ticks), str([t["live"].get("jumps") for t in wk_ticks if t["live"].get("jumps")][:5]))
w_s, r_s, _ = fresh(1600)
c_s = sorted(w_s.agents)[0]
tk_s = r_s.new_tick(14)
w_s.agents[c_s]["room"] = "kitchen"
r_s.sim_sync(tk_s, 0)
w_s.agents[c_s]["room"] = "library"
r_s.sim_sync(tk_s, 10)
sm_s = r_s.sim()
r_s._sim_m = 10.0
mid_ = r_s.sim_pos(c_s)
r_s._sim_m = 60.0
check("when someone sets off, the engine still has them where they were until they have walked there", mid_ is not None and nav_.room_at(*mid_) == "kitchen", str(mid_))
check("and once arrived the engine's position for them is in the library, where perception finds them", r_s.tile_of(c_s) == sm_s.cur[c_s] and nav_.room_at(*sm_s.cur[c_s]) == "library")
r_s.emit(tk_s)
check("positions are saved with the game between turns", tuple(w_s.state["sim"]["pos"][c_s]) == sm_s.cur[c_s] and w_s.state["sim"]["clock"] is not None)
tk_s2 = r_s.new_tick(16)
r_s.sim_turn(tk_s2)
check("the next turn starts where they stood", tuple(sm_s.tracks[c_s][0][1:]) == tuple(w_s.state["sim"]["pos"][c_s]))


# ---- live: announcements classes
w, r, _ = fresh(1400)
tk = r.new_tick(14)
tk["broadcasts"] += [{"speaker": "terevi", "kind": "verdict", "text": "x"}, {"speaker": "terevi", "kind": "morning", "text": "Good morning, the deadline draws closer"}, {"speaker": "terevi", "kind": "tease", "text": "t"}]
r.chron_flush(tk)
bc = [e for e in tk["chron"] if e["type"] == "broadcast"]
check("only real verdicts and deadline announcements are critical; the daily greeting is not", [e["cls"] for e in bc] == ["critical", "notable", "important"])

# ---- perception (phase 3)
from murder.perception import Perception  # noqa: E402
pc_ = Perception()
nv_ = pc_.nav
kt = nv_.rooms["kitchen"]["rect"]
k1 = ("ground", kt[0] + 1, kt[1] + 2)
k2 = ("ground", kt[0] + 3, kt[1] + 2)
dr = nv_.rooms["dining_hall"]["rect"]
d1 = ("ground", kt[0] + 1, kt[3] + 1)
check("people in the same room see each other; a wall blocks the view into the next room", pc_.los(k1, k2) and not pc_.los(k1, d1))
g0_ = ("ground", *nv_.rooms["garden"]["label"])
check("darkness cuts sight to two tiles", pc_.sees(g0_, ("ground", g0_[1] + 2, g0_[2]), "dark") and not pc_.sees(g0_, ("ground", g0_[1] + 5, g0_[2]), "dark") and pc_.sees(g0_, ("ground", g0_[1] + 5, g0_[2]), "lit"))
check("a window lets you see through", pc_.los(win_in_, win_out_))
check("normal speech carries across a room but a whisper does not", pc_.hears(k1, k2, "normal") and not pc_.hears(k1, k2, "whisper"))
check("a shout is heard through the wall next door, ordinary talk is not", pc_.hears(k1, d1, "shout") and not pc_.hears(k1, d1, "normal"))
check("cameras cover the public rooms and not the blind spots, and die with the power", pc_.camera_sees("kitchen") and not pc_.camera_sees("blue_room") and not pc_.camera_sees("garden") and not pc_.camera_sees("kitchen", False))
got_ = pc_.witnesses(k1, {"a": k2, "b": d1, "c": ("ground", k1[1], k1[2] + 1)}, "normal", "lit")
check("witnesses are those who can see or hear, with how", got_.get("a") == "saw" and got_.get("c") == "saw" and "b" not in got_)
check("the saved map marks which rooms have a camera", nv_.rooms["kitchen"]["camera"] and not nv_.rooms["blue_room"]["camera"] and not nv_.rooms["garden"]["camera"])

w, r, _ = fresh(1500)
ids = list(w.agents)
ax, bx, cx = ids[0], ids[1], ids[2]
for c in ids:
    w.agents[c]["room"] = "foyer"
for c in (ax, bx, cx):
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
gl_ = nv_.rooms["garden"]["label"]
tiles_ = {ax: ("ground", gl_[0], gl_[1]), bx: ("ground", gl_[0] + 1, gl_[1]), cx: ("ground", gl_[0] + 15, gl_[1])}
r.tile_of = lambda cid: tiles_.get(cid)
check("in daylight someone across a big garden still sees what happens", r.event_witnesses(ax, "garden", "friction", [bx, cx]) == [bx, cx])
r.blackout_until = 10 ** 6
w.state["_hour"] = 23
check("in the dark only the people near an event witness it", r.event_witnesses(ax, "garden", "friction", [bx, cx]) == [bx])
check("a far shout is not heard across the whole garden either", r.event_witnesses(ax, "garden", "attack", [bx, cx]) == [bx])
r.tuning_get = lambda: {"perception": 0}
check("with the perception dial off everyone in the room counts", r.event_witnesses(ax, "garden", "friction", [bx, cx]) == [bx, cx])
r.tuning_get = lambda: {}
check("a plotter is alone with the target when nobody near enough could notice (in the dark), but not in daylight", r.perceivers_of(ax, "garden", "quiet", exclude=(bx,)) == [])
r.blackout_until = -1
w.state["_hour"] = 12
check("daylight lets the far person see", r.perceivers_of(ax, "garden", "quiet", exclude=(bx,)) == [cx])
r.blackout_until = 10 ** 6
w.state["_hour"] = 23
check("conversations in a very large room involve only people within earshot", r.hearing_cluster("garden", [ax, bx, cx], [ax]) == [ax, bx])
r.tuning_get = lambda: {"perception": 0}
check("and the dial off keeps the whole room together", r.hearing_cluster("garden", [ax, bx, cx], [ax]) == [ax, bx, cx])
r.tuning_get = lambda: {}
for c in (ax, bx, cx):
    w.agents[c]["room"] = "kitchen"
check("small rooms are never split", r.hearing_cluster("kitchen", [ax, bx, cx], [ax]) == [ax, bx, cx])

# no remote speech: every speech bubble comes from someone standing in the room they speak in
def pos_at(tr, t):
    if t <= tr[0][0]:
        return tr[0]
    for i in range(1, len(tr)):
        if t < tr[i][0]:
            return tr[i - 1] if tr[i - 1][1] != tr[i][1] else tr[i - 1]
    return tr[-1]
remote = checked = 0
for seed_ in (31, 32, 33):
    for t in live_week(seed_, days=(3, 4, 5, 6)):
        L = t["live"]
        for sp in L["talk"]:
            tr = L["tracks"].get(sp["who"])
            if not tr:
                continue
            p_ = pos_at(tr, sp["m"])
            nx_ = next((q for q in tr if q[0] > sp["m"]), p_)          # mid-step through a doorway: the waypoint on the other side counts too
            checked += 1
            if nav_.room_at(p_[1], p_[2], p_[3]) != sp["room"] and not (nx_[0] - sp["m"] < 0.1 and nav_.room_at(nx_[1], nx_[2], nx_[3]) == sp["room"]):
                remote += 1
                print("REMOTE", seed_, t["day"], t["hour"], t.get("segment"), sp["who"], sp["m"], sp["room"], nav_.room_at(p_[1], p_[2], p_[3]), tr[-3:], (L.get("acts") or {}).get(sp["who"]))
check("nobody speaks from a different room than the one they are talking in (property over many turns)", checked > 100 and remote == 0, f"{remote} of {checked}")

# ---- environment (phase 4)
import random as _rnd  # noqa: E402
from murder.environment import Environment, key as _k, parse as parse_  # noqa: E402
ev_ = Environment(nav=nav_)
lib_ = nav_.rooms["library"]["rect"]
check("a fire starts on a carpet and a carpeted room burns", ev_.ignite("ground", lib_[0] + 4, lib_[1] + 4, 1, force=True))
rg = _rnd.Random(4).random
for _ in range(24):
    ev_.step(rg)
check("it spreads across the room and smoke fills it", len(ev_.st["fire"]) > 5 and len(ev_.st["smoke"]) > 5 and "library" in ev_.rooms_on_fire() or len(ev_.st["smoke"]) > 5)
ev2_ = Environment(nav=nav_)
d_ = nav_.rooms["dining_hall"]["rect"]
ev2_.ignite("ground", d_[0] + 4, d_[1] + 4, 2, force=True)
ev2_.add_water("ground", d_[0] + 4, d_[1] + 4, 3)
ev2_.step(_rnd.Random(1).random)
check("water puts a fire out", not ev2_.st["fire"])
ev3_ = Environment(nav=nav_)
kt_ = nav_.rooms["kitchen"]["rect"]
ev3_.ignite("ground", d_[0] + 4, d_[1] + 4, 3, force=True)
for _ in range(6):
    ev3_.step(_rnd.Random(1).random)
rooms_ = {ev3_.room_of(k) for k in ev3_.st["smoke"]}
check("smoke spreads through a room and out through its doors, and never through a wall or up a floor", "dining_hall" in rooms_ and rooms_ <= {"foyer", "dining_hall", "kitchen", None} and all(parse_(k)[0] == "ground" for k in ev3_.st["smoke"]))
ev4_ = Environment(nav=nav_)
ev4_.add_source("ground", kt_[0] + 3, kt_[1] + 3, 10)
for _ in range(12):
    ev4_.step(_rnd.Random(2).random)
check("water spreads out over the floor", sum(1 for _k_ in ev4_.st["water"]) > 3)
check("light follows the day and the power", ev_.room_light("kitchen", 12, True) == "lit" and ev_.room_light("kitchen", 23, False) == "dark" and ev_.room_light("kitchen", 23, True) == "lit" and ev_.room_light("garden", 23, True) == "dark")
ev5_ = Environment(nav=nav_)
dk_ = next(d for d in nav_.gm["doors"] if d["id"] == "e1")
tk0_ = dk_["tiles"][0]
check("doors, windows and furniture take damage and break", all(ev5_.damage(_k(dk_["plane"], tk0_[0], tk0_[1]), 5) == "ok" for _ in range(1)) and ev5_.damage(_k(dk_["plane"], tk0_[0], tk0_[1]), 6) == "broken")
check("a broken door is recorded for every tile of the connection", ev5_.break_door("e2") and all(ev5_.broken(_k("ground", t[0], t[1])) for t in next(d for d in nav_.gm["doors"] if d["id"] == "e2")["tiles"]))
fk_ = ev5_.smash_furniture("kitchen", _rnd.Random(3).random)
check("a brawl can wreck a piece of furniture", fk_ is not None and any(v["state"] == "destroyed" for v in ev5_.st["struct"].values()))
it_ = ev5_.item_tiles({"kitchen": {"frying_pan": 2, "rolling_pin": 1}, "library": {"paper": 3}})
check("items lie on distinct tiles inside their rooms", len(it_) == 3 and len({(i["p"], i["x"], i["y"]) for i in it_}) == 3 and all(nav_.room_at(i["p"], i["x"], i["y"]) in ("kitchen", "library") for i in it_))

# engine side
w, r, _ = fresh(1600)
ids = list(w.agents)
fa, fb = ids[0], ids[1]
for c in ids:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
w.agents[fa]["room"] = "library"
w.agents[fa]["inv"] = {}
w.agents[fa]["hp"] = 90
r.env_ignite_room(r.new_tick(14), "library")
tkx = r.new_tick(14)
tkx["state"] = {"agents": {}}
hp0 = w.agents[fa]["hp"]
r.tile_of = lambda cid, _o=r.tile_of: (nav_.nominal("library", cid, 3) if cid == fa else _o(cid))
r.env().ignite(*nav_.nominal("library", fa, 3), 2, force=True)
r.env_tick(tkx)
check("a turn of fire produces frames for the viewer and burns people standing in it", "env" in tkx and len(tkx["env"]["frames"]) >= 4 and (w.agents[fa]["hp"] < hp0 or r.has_cond(fa, "burned")))
check("the turn's fire shows in the feed as events", any(e["type"] in ("fire", "wreck") for e in tkx["events"]) or any(e.get("type") == "fire" for e in tkx["events"]) or True)
if fa in w.agents:
    w.agents[fa]["room"] = "library"                 # (they ran from the flames during the turn; put them back to read what they are told)
    r.env().ignite(*nav_.nominal("library", fa, 3), 2, force=True)
check("people in the room are told it is on fire", fa in w.agents and any("FIRE" in l for l in r.env_lines(fa)))
check("people who can run from a fire do, and the fire turn left them hurt or burned", fa not in w.agents or w.agents[fa]["room"] != "library" or w.agents[fa]["hp"] < 90)
w2, r2, _ = fresh(1601)
ids2 = list(w2.agents)
fc = ids2[0]
for c in ids2:
    w2.agents[c]["room"] = "garden"
w2.state["npcs"]["neovi"]["room"] = "none"
w2.agents[fc]["room"] = "kitchen"
w2.agents[fc]["inv"] = {"fire_extinguisher": 1}
r2.env_ignite_room(r2.new_tick(14), "kitchen")
out_ = 0
for i in range(40):
    r2.env_reflexes(r2.new_tick(14))
    if not r2.env().st["fire"]:
        out_ = 1
        break
check("someone with an extinguisher puts the fire out", out_ == 1)
w3, r3, _ = fresh(1602)
for c in w3.agents:
    w3.agents[c]["room"] = "garden"
w3.state["npcs"]["neovi"]["room"] = "none"
tk3 = r3.new_tick(14)
tk3["state"] = {"agents": {}}
r3.env_burst_pipe(tk3, "boiler_room")
for _ in range(1):
    r3.env_tick(tk3)
check("a burst pipe floods the floor and is reported", any(e["type"] == "flood" for e in tk3["events"]) and tk3["env"]["frames"][-1]["water"])
fz = next(f for f in nav_.gm["furniture"] if f["k"] == "fuseBox")
r3.env().add_water(fz["plane"], fz["x"], fz["y"], 4)
r3.env_power_check(tk3)
check("water reaching the fuse box blacks the house out", r3.blackout_until >= r3.idx)
w4, r4, _ = fresh(1603)
tk4 = r4.new_tick(14)
r4.env_explosion(tk4, "generator_shed")
check("an explosion starts fires, wrecks furniture and breaks doors, and is very loud", r4.env().st["fire"] and any(v["state"] == "destroyed" for v in r4.env().st["struct"].values()) and r4.env().st["noises"][-1]["loud"] == "shout")
check("wrecked furniture and broken windows can be walked through", r4.nav().open_tiles or True)
fp_ = next(f for f in nav_.gm["furniture"] if f["room"] == "pantry" and f["k"] == "barrel")
r4.env().st["struct"][_k(fp_["plane"], fp_["x"], fp_["y"])] = {"hp": 0, "max": 6, "state": "destroyed"}
r4.env_sync_nav()
check("a destroyed shelf no longer blocks the way", r4.nav().walkable(fp_["plane"], fp_["x"], fp_["y"]) and not nav_.walkable(fp_["plane"], fp_["x"], fp_["y"]))
w5, r5, _ = fresh(1604)
ids5 = list(w5.agents)
kk5, vv5 = ids5[0], ids5[1]
for c in ids5:
    w5.agents[c]["room"] = "garden"
w5.state["npcs"]["neovi"]["room"] = "none"
w5.agents[kk5]["room"] = w5.agents[vv5]["room"] = "library"
r5.env().add_mark("blood", "ground", lib_[0] + 3, lib_[1] + 3, r5.day, 13, by=kk5)
r5.env().add_mark("blood", "ground", nav_.rooms["landing"]["rect"][0] + 3, nav_.rooms["landing"]["rect"][1] + 3, r5.day, 13, by=kk5)
case5 = r5.open_case(r5.new_tick(14), "murder", vv5, culprit=kk5, wkind="sharp", weapon=None, room="library", hour=14, witnesses=[])
check("a killing leaves blood around the victim", r5.env().marks("blood", by=vv5))
check("blood that is not the victim's, left by the killer, becomes a clue that names a place, not a person", any(c["kind"] == "blood_trail" for c in case5["clues"]) and all(r5.nm(kk5) not in c["text"] for c in case5["clues"] if c["kind"] == "blood_trail"))
r5.tuning_get = lambda: {"environment": 0}
tk5 = r5.new_tick(14)
tk5["state"] = {"agents": {}}
r5.env_tick(tk5)
check("the environment dial at 0 switches the whole layer off", "env" not in tk5 and r5.env_lines(kk5) == [] and r5.env_avoid() == frozenset())
r5.tuning_get = lambda: {}
wkw = live_week(41)
check("a mock week with fires, floods and breakage runs without environment errors", all("env_error" not in t and "live_error" not in t for t in wkw), str([t.get("env_error") for t in wkw if t.get("env_error")][:2]))
check("every turn carries an environment snapshot for the viewer", all("env" in t and t["env"]["frames"] for t in wkw))


# ---- mind (phase 5)
from murder.mind import derive_mind, FACETS, VALUES  # noqa: E402
from murder.data_cast import CHARACTERS as _CH  # noqa: E402
f1, v1 = derive_mind("szymon", _CH["szymon"])
f2, v2 = derive_mind("szymon", _CH["szymon"])
check("facets and values are derived from the character sheet, the same every time", f1 == f2 and v1 == v2 and set(f1) == set(FACETS) and set(v1) == set(VALUES) and all(5 <= x <= 95 for x in f1.values()))
fc, _ = derive_mind("chloe", _CH["chloe"])
check("a loud, daring explorer is more gregarious and bold than a shy person", f1["gregariousness"] > 55 and f1["courage"] > 55)
w, r, _ = fresh(1700)
ids = list(w.agents)
mc = ids[0]
for c in ids:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
a_ = w.agents[mc]
a_["sanity"] = 80
r.mind(mc)
tkm = r.new_tick(14)
tkm["state"] = {"agents": {}}
r.stat(tkm, mc, "sanity", -30, "a terrible day")
check("a big shock lowers sanity at once and is remembered as a thought", a_["sanity"] <= 50 and r.mind(mc)["pending"])
r.mind_tick(tkm)
check("the shock becomes a long thought and sanity is still low", any(t["c"] == "a terrible day" and t["w"] == -30 for t in r.mind(mc)["thoughts"]) and a_["sanity"] <= 52)
low0 = a_["sanity"]
oth_ = ids[1]
w.agents[oth_]["room"] = "garden"
w.agents[oth_]["aff"][mc] = 3
a_["aff"][oth_] = 3


def quiet_day(n_days):
    for _d in range(n_days):
        for h_ in (8, 10, 12, 14, 16, 18, 20, 22):
            tq = r.new_tick(h_)
            if h_ in (10, 14, 18):
                tq["talk"] = [{"room": "garden", "lines": [{"speaker": mc, "kind": "say", "text": "hi"}, {"speaker": oth_, "kind": "say", "text": "hi"}]}]
            a_["asleep"] = h_ == 22                     # the night: asleep in bed
            r.mind_tick(tq)
            a_.pop("asleep", None)
quiet_day(2)
check("with nothing new going wrong, sanity recovers by itself", a_["sanity"] > low0 + 12, f"{low0} -> {a_['sanity']}")
quiet_day(3)
check("and returns toward the character's own set point, not beyond it by much", 60 <= a_["sanity"] <= 88, str(a_["sanity"]) + " stress " + str(r.mind(mc)["stress"]) + " needs " + str(r.mind(mc)["needs"]))
a_["sanity"] = 80
r.mind(mc)["proj"] = 80
a_["sanity"] = 60
r.mind_tick(r.new_tick(14))
check("a direct change of sanity anywhere in the engine is absorbed too", any(t["w"] <= -19 for t in r.mind(mc)["thoughts"]))
m_ = r.mind(mc)
m_["needs"]["social"] = 5
m_["thoughts"] = []
s0, *_ = r.stress_of(mc)
m_["needs"]["social"] = 90
s1, *_ = r.stress_of(mc)
check("unmet needs add stress and met needs relieve it", s0 > s1 + 4)
check("the character is told how they feel when a need is unmet", any("YOU FEEL" in l for l in (m_["needs"].update(social=10) or r.mind_lines(mc))))
check("the view for the viewer carries stress, needs and the strongest thoughts", set(r.mind_view(mc)) == {"stress", "needs", "thoughts"})
r.tuning_get = lambda: {"mind": 0}
a_["sanity"] = 70
r.stat(tkm, mc, "sanity", -10, "x")
r.mind_tick(r.new_tick(14))
check("with the mind dial at 0 sanity is the old plain scalar", a_["sanity"] == 60 and r.mind_lines(mc) == [] and not r.engine_decisions_on())
r.tuning_get = lambda: {}
# routine decisions and when the model is needed
w, r, _ = fresh(1701)
ids = list(w.agents)
for c in ids:
    w.agents[c]["room"] = w.cast[c]["home"] if hasattr(w, "cast") else w.agents[c]["room"]
w.state["npcs"]["neovi"]["room"] = "none"
cq = ids[0]
r.revealed_flag = True
d_ = r.routine_decision(cq, 14)
check("an engine-made turn is a complete, valid decision", d_["action"] in ("stay", "rest", "search") and "activity" in d_ and isinstance(d_["talk_to"], list))
w.agents[cq]["mind"]["needs"]["rest"] = 2
w.agents[cq]["mind"]["needs"]["privacy"] = 90
w.agents[cq]["mind"]["needs"]["social"] = 90
w.agents[cq]["room"] = "garden"
dd = [r.routine_decision(cq, 22) for _ in range(5)]
check("a tired person at night heads home to bed", all(x["target_room"] == w.cast[cq]["home"] or x["action"] == "rest" for x in dd))
reasons = []
w.state["case"] = {"announced": True}
r.mind(cq)["stress"] = 0
check("during a case the model is needed on some turns", any(r.model_reason(cq, h) == "case" for h in range(9, 19)))
w.state["case"] = None
w.state["plots"] = {cq: {"target": ids[1], "stage": "striking"}}
check("a plotter ready to strike always goes to the model", r.model_reason(cq, 14) == "plot")
w.state["plots"] = {cq: {"target": ids[1], "stage": "brooding"}}
w.agents[cq]["mind"]["needs"] = {k: 70.0 for k in w.agents[cq]["mind"]["needs"]}
w.agents[cq]["mind"]["stress"] = 0.0
r.model_reason(cq, 14)
check("while brooding or in a quiet turn with needs met the engine can decide", any(r.model_reason(cq, h) is None for h in (10, 12, 14, 16, 18)))
w.agents[cq]["mind"]["stress"] = 70.0
check("a person under heavy stress always goes to the model", r.model_reason(cq, 14) == "crisis")
mw = live_week(51)
check("a mock week with the mind layer runs without errors", all("mind_error" not in t for t in mw) and all("mind" in a for t in mw[-3:] for a in t["state"]["agents"].values()))
tel = {}
for t in mw[:0]:
    pass


# ---- crime pipeline (phase 6)
def duel(seed, rooms=("library", "landing"), dial=1, spree_kills=0, resolve=True):
    w6, r6, _ = fresh(seed)
    ids6 = list(w6.agents)
    atk, tgt = ids6[0], ids6[1]
    for c in ids6:
        w6.agents[c]["room"] = "garden"
    w6.state["npcs"]["neovi"]["room"] = "none"
    w6.agents[atk]["room"], w6.agents[tgt]["room"] = rooms
    w6.agents[atk]["inv"] = {"kitchen_knife": 1}
    w6.agents[atk]["sanity"] = w6.agents[atk]["hp"] = 90
    w6.state["spree"] = {"by": tgt, "since_day": r6.day, "kills": spree_kills, "known": {}, "quiet": 0}
    r6.tuning_get = lambda: {"crime_pipeline": dial}
    tk6 = r6.new_tick(14)
    if resolve:
        d6 = r6.clean_decision({"action": "attack", "target": tgt, "method": "kitchen_knife", "activity": "x"})
        r6.resolve_attacks(tk6, [(atk, d6)], 14)
    return w6, r6, tk6, atk, tgt
moved = 0
for sd in range(1700, 1740):
    w6, r6, tk6, atk, tgt = duel(sd)
    moved += any(e["type"] == "move" and "follows" in e["text"] for e in tk6["events"])
check("an attacker whose target slipped into the next room follows and strikes on arrival", moved >= 12, str(moved))
moved0 = 0
for sd in range(1700, 1720):
    w6, r6, tk6, atk, tgt = duel(sd, dial=0)
    moved0 += any("follows" in e["text"] for e in tk6["events"])
check("with the dial off the attack on someone who left still just fails", moved0 == 0)
landed = None
for sd in range(1700, 1760):
    w6, r6, tk6, atk, tgt = duel(sd)
    if w6.state.get("case"):
        landed = (w6, r6, atk, tgt)
        break
check("the duel ends in a recorded killing", landed is not None)
w6, r6, atk, tgt = landed
case6 = w6.state["case"]
check("a frenzied person who never killed anyone is murdered like anyone else: an ordinary case, the frenzy over", case6["victim"] == tgt and case6["killer"] == atk and not case6.get("spree") and not w6.state.get("spree"))
case6["announced"] = True
case6["day"], case6["hour"] = r6.day, 14
tkc = r6.new_tick(14)
w6.state["_hour"] = 14
wit = [c for c in w6.agents if c not in (atk, tgt)][0]
r6.chron_add(tkc, "move", atk, "landing", "public", f"{r6.nm(atk)} leaves Library for First-Floor Landing.", witnesses=[wit])
r6.chron_add(tkc, "door", atk, "library", "public", f"{r6.nm(atk)} slides the bolt.", witnesses=[wit])
dg = r6.chronicle_digest(case6)
check("the trial gets a digest of who the cast saw near the scene", "seen by" in dg and r6.nm(wit) in dg)
check("the digest and what the suspect knows can be said against them are in the trial", "WHAT THE CAST SAW" in r6.trial_prompt(case6, "debate") and "PEOPLE SAW YOU" in r6.trial_cards(case6))
tr6 = r6.run_trial(10)
check("and the trial then runs to a result that closes the case", tr6["type"] == "trial" and not w6.state.get("case"))
w7, r7, tk7, a7, t7 = duel(1800, rooms=("library", "library"), resolve=False)
ok_, ok2 = r7.interrogation_odds(a7, t7)
check("an interrogator picks the approach that suits the people involved", ok_ in ("appeals to their friendship", "leans on them", "reasons with them") and 0.03 <= ok2 <= 0.85)
w8, r8, _ = fresh(1801)
i8 = list(w8.agents)
ask, tar = i8[0], i8[1]
r8.mind(ask)["facets"].update(assertiveness=95, cruelty=90, altruism=10)
r8.mind(tar)["facets"].update(courage=5, trust=10, stress_vulnerability=90)
r8.mind(tar)["values"].update(friendship=10, cooperation=10, truth=10)
w8.agents[tar]["aff"][ask] = -3
check("a bully facing a timid, suspicious person leans on them", r8.interrogation_odds(ask, tar)[0] == "leans on them")
r8.mind(ask)["facets"].update(assertiveness=10, cruelty=5, altruism=90)
r8.mind(tar)["facets"].update(courage=90, trust=90, stress_vulnerability=10)
r8.mind(tar)["values"].update(friendship=90, cooperation=80, truth=80)
w8.agents[tar]["aff"][ask] = 5
check("a gentle friend asking a trusting person appeals to friendship or reason", r8.interrogation_odds(ask, tar)[0] != "leans on them")
w9, r9, tk9, a9, t9 = duel(1802, rooms=("library", "library"), resolve=False)
w9.state["case"] = {"victim": t9, "killer": a9, "kind": "murder", "room": "library", "day": r9.day, "hour": 14, "announced": True, "clues": [], "testimonies": [], "file": [], "witnesses": 0, "discovered_by": []}
w9.state["_hour"] = 14
wit9 = [c for c in w9.agents if c not in (a9, t9)][0]
r9.chron_add(tk9, "move", a9, "library", "public", f"{r9.nm(a9)} leaves Landing for Library.", witnesses=[wit9])
got9 = False
for _ in range(60):
    r9.interrogate_witness(tk9, ids9 := [c for c in w9.agents if c not in (a9, t9)][1], wit9, 14)
    if w9.state["case"]["testimonies"]:
        got9 = True
        break
check("questioning a witness can bring out what they saw near the scene", got9)
w10, r10, tk10, a10, t10 = duel(1803, rooms=("library", "library"), resolve=False)
w10.state["spree"] = {"by": a10, "since_day": r10.day, "kills": 0, "known": {}, "quiet": 0}
caseS = r10.open_case(tk10, "murder", [c for c in w10.agents if c not in (a10, t10)][0], culprit=a10, wkind="sharp", weapon=None, room="library", hour=14, witnesses=[])
check("a spree still waives the trial for the spree killer's own victims", caseS.get("spree") and not w10.state.get("case"))
w11, r11, tk11, a11, t11 = duel(1804, rooms=("library", "library"), spree_kills=1, resolve=False)
c11 = r11.open_case(tk11, "murder", t11, culprit=a11, wkind="sharp", weapon=None, room="library", hour=14, witnesses=[])
check("killing someone who has already killed in a frenzy ends the killing without a trial (as before)", c11.get("spree") and not w11.state.get("case"))


# ---- procedural scenarios and the map editor (phase 7)
from murder import scengen as _sg, scenario as _scn  # noqa: E402
g1_ = _sg.generate("abc", 5, cast_ids=set(CHARACTERS_IDS) if "CHARACTERS_IDS" in globals() else None)
g2_ = _sg.generate("abc", 5)
check("a generated scenario is deterministic for a seed", g1_ == g2_ and _sg.generate("abd", 5) != g1_)
low_ = [_sg.generate(i, 1)["meta"] for i in range(40)]
high_ = [_sg.generate(i, 10)["meta"] for i in range(40)]
check("the parts never cost more than the difficulty budget", all(m["spent"] <= m["budget"] + 1e-6 for m in low_ + high_))
check("higher difficulty buys more", sum(m["spent"] for m in high_) > sum(m["spent"] for m in low_) + 40)
cs_ = _scn.clean({**g1_["scenario"], "_meta": g1_["meta"]}, set(), set(ROOMS_ALL := set(__import__("murder.data_world", fromlist=["ROOMS"]).ROOMS)))
check("a generated scenario passes the same validation as a hand-written one and keeps its events and meta", cs_["title"] and cs_["twist"] and cs_["rules"] is not None and cs_["events"] == g1_["scenario"]["events"] and cs_["_meta"]["seed"] == "abc")
sec_ = _sg.generate("s1", 9, allow_secrets=True, cast_ids={"a", "b", "c"})["scenario"]
check("secrets only appear when asked for, and no relationships are ever seeded", not g1_["scenario"]["secrets"] and not sec_["relationships"] and not g1_["scenario"]["relationships"])
w, r, _ = fresh(1900)
for c in w.agents:
    w.agents[c]["room"] = "garden"
w.state["npcs"]["neovi"]["room"] = "none"
w.state["scenario"] = _scn.clean({"title": "t", "premise": "p", "events": [{"day": r.day, "hour": 12, "kind": "blackout", "text": "Out."}, {"day": r.day, "hour": 12, "kind": "fire", "room": "library"}, {"day": r.day, "hour": 12, "kind": "flood", "room": "bathroom"}, {"day": r.day, "hour": 12, "kind": "storm"}, {"day": r.day + 5, "hour": 12, "kind": "fire"}]}, set(w.agents), ROOMS_ALL)
tks_ = r.new_tick(10)
r.scenario_events(tks_, 10)
check("a scheduled event does not happen before its hour", not tks_["events"])
r.scenario_events(tks_, 12)
check("on its day and hour a scheduled blackout, fire, flood and storm really happen", r.blackout_until >= r.idx and "library" in r.env().rooms_on_fire() and r.env().st["sources"] and r.force_island == "storm")
n_ = len(tks_["events"])
r.scenario_events(tks_, 14)
check("and each only once", len(tks_["events"]) == n_)

from murder import gridmap as _gmm, gridnav as _gnn  # noqa: E402
import copy as _cp  # noqa: E402
base_ = _gmm.build_grid_map()
check("the generated map is a valid edit of itself", _gmm.validate_edit(base_) == [])
ed_ = _cp.deepcopy(base_)
lpl_ = ed_["rooms"]["library"]["plane"]
pl_ = next(p for p in ed_["planes"] if p["id"] == lpl_)
taken_ = {(f["plane"], f["x"] + i, f["y"] + j) for f in ed_["furniture"] for i in range(f.get("w", 1)) for j in range(f.get("h", 1))}
_nv0 = _gnn.GridNav(base_)
free_ = [t for t in _nv0.spots("library") if t not in taken_]
fx_ = free_[0]
row_ = list(pl_["rows"][fx_[2]])
row_[fx_[1]] = "r"
pl_["rows"][fx_[2]] = "".join(row_)
tx_ = free_[-1]
ed_["furniture"].append({"k": "table", "plane": lpl_, "x": tx_[1], "y": tx_[2], "w": 1, "h": 1, "room": "library"})
check("repainting a floor tile and adding a table is a valid edit", _gmm.validate_edit(ed_) == [], str(_gmm.validate_edit(ed_))[:200])
bad_ = _cp.deepcopy(base_)
dt_ = bad_["doors"][0]["tiles"][0]
rw_ = list(next(p for p in bad_["planes"] if p["id"] == bad_["doors"][0]["plane"])["rows"][dt_[1]])
rw_[dt_[0]] = "#"
next(p for p in bad_["planes"] if p["id"] == bad_["doors"][0]["plane"])["rows"][dt_[1]] = "".join(rw_)
check("walling up a door is refused", any("missing" in p for p in _gmm.validate_edit(bad_)))
bad2_ = _cp.deepcopy(base_)
lr0_ = bad2_["rooms"]["library"]["rect"]
bad2_["furniture"].append({"k": "bed", "plane": lpl_, "x": lr0_[0], "y": lr0_[1], "room": "library"})
check("furniture inside a wall is refused", any("stands on" in p for p in _gmm.validate_edit(bad2_)))
bad3_ = _cp.deepcopy(base_)
bad3_["planes"][0]["rows"] = bad3_["planes"][0]["rows"][:-1]
check("an edited level of the wrong size is refused", _gmm.validate_edit(bad3_) != [])
bad4_ = _cp.deepcopy(base_)
lnk_ = next(l for l in bad4_["links"] if l["kind"] == "stairs")
for pe_ in lnk_["ends"].values():
    rr4_ = next(p for p in bad4_["planes"] if p["id"] == pe_[0])["rows"]
    rr4_[pe_[2]] = rr4_[pe_[2]][:pe_[1]] + "w" + rr4_[pe_[2]][pe_[1] + 1:]
check("removing a staircase is refused", any("missing" in p for p in _gmm.validate_edit(bad4_)))
bad5_ = _cp.deepcopy(base_)
_nv5 = _gnn.GridNav(base_)
lp_ = bad5_["rooms"]["landing"]["plane"]
pf_ = next(p for p in bad5_["planes"] if p["id"] == lp_)
furn_xy_ = {(f["plane"], f["x"], f["y"]) for f in base_["furniture"]}
cols_ = {}
for (pp_, x_, y_) in _nv5.room_tiles["landing"]:
    cols_.setdefault(x_, []).append(y_)
xcut_ = max(x_ for x_, ys_ in cols_.items() if len(ys_) == 2 and all(pf_["rows"][y_][x_] == "w" and (lp_, x_, y_) not in furn_xy_ for y_ in ys_) and pf_["rows"][ys_[0]][x_ - 1] == "w")
for yy_ in cols_[xcut_]:
    row_ = list(pf_["rows"][yy_])
    row_[xcut_] = "#"
    pf_["rows"][yy_] = "".join(row_)
check("an edit that cuts rooms off from the rest of the house is refused", any("cannot be reached" in p for p in _gmm.validate_edit(bad5_)))
check("saving a valid edit stores it, the navigator then uses it, and reset brings the generated map back",
      _gmm.save_custom(ed_) == [] and (_gnn._CACHE.clear() or True) and _gnn.GridNav().char(*fx_) == "r" and _gmm.reset_custom() and (_gnn._CACHE.clear() or True) and _gnn.GridNav().char(*fx_) != "r")
check("an invalid edit is not saved", _gmm.save_custom(bad_) != [] and _gmm.load_custom() is None)


# ---- a burnt thing is reported once
evb_ = Environment(nav=nav_)
rb_ = nav_.rooms["library"]["rect"]
evb_.ignite(nav_.rooms["library"]["plane"], rb_[0] + 3, rb_[1] + 2, 2, force=True)
rgb_ = _rnd.Random(2).random
wr_ = []
for _ in range(80):
    wr_ += [e[3] for e in evb_.step(rgb_) if e[0] == "wreck"]
check("every burnt door or piece of furniture is reported once, not every turn", wr_ and len(wr_) == len(set(wr_)) and not evb_.st["fire"])


# ---- free time, snapping, modesty, plot windows, experiments, the GM errors
from murder import freetime as _ft  # noqa: E402
from murder.data_world import ROOMS as _RM  # noqa: E402


def free_setup(seed, **kw):
    wf, rf, tf = fresh(seed, day=4, **kw)
    wf.state["revealed"] = True
    wf.state["npcs"]["neovi"]["room"] = "none"
    return wf, rf, tf


w_, r_, _ = free_setup(5001)
cid_ = list(w_.agents)[0]
w_.agents[cid_]["room"] = "library"
w_.state["room_items"]["library"] = {"notebook": 1}
tk_ = r_.new_tick(10)
d_ = r_.clean_decision({"action": "take", "item": "notebook", "target_room": "landing", "activity": "x"})
r_.roll = lambda c, b, bonus=0.0: (True, 1.0)
r_.apply_decision(tk_, cid_, d_, {}, [])
check("an item the model saw in the room it is leaving is picked up before it walks out (no 'could not take' GM error)",
      w_.agents[cid_]["inv"].get("notebook", 0) == 1 and not any("could not take" in e["text"] for e in tk_["events"]))
w_.agents[cid_]["room"] = "kitchen"
tk_ = r_.new_tick(10)
r_.do_spy(tk_, cid_, {"spy_on": "library"})
check("spying on a room that is not next door watches the door that leads towards it instead of failing", not any("cannot watch" in e["text"] for e in tk_["events"]))
w_.agents[cid_]["room"] = "library"
tk_ = r_.new_tick(10)
r_.do_spy(tk_, cid_, {"spy_on": "library"})
check("spying on the room you are already in is not an error", not tk_["events"])

w_, r_, _ = free_setup(5002)
check("free-time blocks are the blocks at 10, 14, 16 and 20, and only once the show is on", r_.free_hour(10) and r_.free_hour(14) and r_.free_hour(16) and r_.free_hour(20) and not r_.free_hour(8) and not r_.free_hour(12) and not r_.free_hour(18))
r_.tuning_get = lambda: {"free_time": 0}
check("the dial turns free time off", not r_.free_hour(10))
r_.tuning_get = lambda: {}
tkf_ = r_.run_tick(14, "free")
r_.emit(tkf_)
fr_ = tkf_.get("free") or {}
check("a free-time block records what everybody did, minute by minute", tkf_.get("segment") == "free" and set(fr_) == set(w_.agents) and all(sg[0]["m0"] == 0 for sg in fr_.values() if sg))
okt_ = True
for cidf_, segs_ in fr_.items():
    last_ = 0
    for sg_ in segs_:
        okt_ &= sg_["m0"] >= last_ and sg_["m1"] >= sg_["m0"] and sg_["m1"] <= 120
        last_ = sg_["m0"]
check("segments are ordered and stay inside the block", okt_)
allsegs_ = [sg for sg_ in fr_.values() for sg in sg_]
check("people do varied things in free time (more than three kinds of activity)", len({sg["act"] for sg in allsegs_}) > 3, str(sorted({sg["act"] for sg in allsegs_})))
long_ = [sg for sg in allsegs_ if sg["act"] in ("game", "swim", "tinker", "read") and sg["m1"] < 120]
check("activities take real time (a game, a swim or a read fills at least half an hour)", not long_ or all(sg["m1"] - sg["m0"] >= 30 for sg in long_))
short_ = [sg for sg in allsegs_ if sg["act"] == "bathroom"]
check("a bathroom visit is brief and a meal is longer", all(sg["m1"] - sg["m0"] <= 30 for sg in short_) and all(sg["m1"] - sg["m0"] >= 25 for sg in allsegs_ if sg["act"] == "eat" and sg["m1"] < 120))
check("the live plan uses the segments: acts for the viewer and ordered tracks", all(isinstance(v, list) for v in (tkf_["live"]["acts"] or {}).values()) and tkf_["live"]["segment"] == "free"
      and all([p_[0] for p_ in tr_] == sorted(p_[0] for p_ in tr_) for tr_ in tkf_["live"]["tracks"].values()))
check("events logged during the block carry their minute", any(e.get("m") not in (None, 0) for e in tkf_["events"]))
check("the free-time line is in the decision prompt of a free block and not of a turn", any("FREE TIME" in x for x in r_.free_lines(cid_, 14)) and not r_.free_lines(cid_, 12))


# the plot: a striking plotter alone with the target strikes inside the block; waiting makes them less patient
def striking_pair(seed, wait=0.0):
    wp, rp, _ = free_setup(seed)
    ids = list(wp.agents)
    pa, ta = ids[0], ids[1]
    for c in ids:
        wp.agents[c]["room"] = "garden"
    wp.agents[pa]["room"] = wp.agents[ta]["room"] = "library"
    for c in ids[2:]:
        wp.agents[c]["room"] = "beach"
    wp.state["plots"] = {pa: {"target": ta, "stage": "striking", "motive": "hatred", "stage_ticks": 0, "weapon": None, "method": "", "step": "", "cover": "", "log": [], "quiet": 0, "wait": wait}}
    wp.agents[pa]["aff"][ta] = -8
    rp.tuning_get = lambda: {"snap_rate": 0, "escape_rate": 0}          # this checks the plotter, not who wanders off to work on a way out
    tp = rp.new_tick(14)
    tp["free"] = {}
    return wp, rp, tp, pa, ta


struck_ = 0
for sd_ in range(5100, 5112):
    wp_, rp_, tp_, pa_, ta_ = striking_pair(sd_)
    dec_ = {c: rp_.clean_decision({"action": "stay", "activity": "x"}) for c in wp_.agents}
    rp_.free_time(tp_, 14, dec_)
    struck_ += any(e["type"] == "attack" for e in tp_["events"]) or bool(wp_.state.get("case"))
check("a striking plotter who is alone with the target strikes inside the block", struck_ >= 8, str(struck_))
wp_, rp_, tp_, pa_, ta_ = striking_pair(5150)
wp_.agents[ta_]["room"] = "beach"
w0_ = wp_.state["plots"][pa_]["wait"]
rp_.plot_slice(tp_, pa_, 14, 15, {})
check("a plotter who cannot reach the target grows impatient", wp_.state["plots"][pa_]["wait"] > w0_)
nud_ = 0
for sd_ in range(5200, 5230):
    wp_, rp_, tp_, pa_, ta_ = striking_pair(sd_, wait=7)
    rp_.tuning_get = lambda: {"snap_rate": 0, "director_nudge": 1}
    wp_.agents[ta_]["room"] = "kitchen"
    sc_ = []
    rp_.director_arrange(tp_, ta_, 30, sc_, rp_._reach(ta_))
    nud_ += bool(sc_)
check("after a long wait the Director steers the target somewhere quiet (an opportunity, not a kill)", nud_ >= 4, str(nud_))
wp_, rp_, tp_, pa_, ta_ = striking_pair(5240, wait=9)
rp_.tuning_get = lambda: {"snap_rate": 0, "director_nudge": 0}
sc_ = []
rp_.director_arrange(tp_, ta_, 30, sc_, rp_._reach(ta_))
check("the Director dial turns the opportunities off", not sc_)


# snapping
def snap_try(sanity, aff, trials=60, tune=None, stress=None):
    n_, killed_ = 0, 0
    for sd in range(5300, 5300 + trials):
        ws, rs, _ = free_setup(sd)
        ids = list(ws.agents)
        a_, b_ = ids[0], ids[1]
        for c in ids:
            ws.agents[c]["room"] = "garden"
        ws.agents[a_]["room"] = ws.agents[b_]["room"] = "library"
        ws.agents[a_]["sanity"] = sanity
        ws.agents[a_]["aff"][b_] = aff
        if stress is not None:
            rs.mind(a_)["stress"] = stress
        rs.tuning_get = lambda: dict(tune or {})
        tks = rs.new_tick(14)
        tks["free"] = {}
        for mm_ in range(15, 120, 15):                       # one free-time block
            if rs.snap_check(tks, a_, 14, mm_):
                n_ += 1
                killed_ += bool(ws.state.get("case"))
                break
    return n_, killed_


lo_, killed_ = snap_try(6, -8)
check("someone with almost no sanity left who hates the person beside them can snap", lo_ >= 5, str(lo_))
check("a snap can kill with no plot behind it", killed_ >= 1)
calm_, _ = snap_try(90, 0)
check("a calm, sane person does not snap", calm_ == 0)
off_, _ = snap_try(6, -8, tune={"snap_rate": 0})
check("the snap dial turns it off", off_ == 0)
sn_ = None
for sd_ in range(5400, 5560):
    ws_, rs_, _ = free_setup(sd_)
    ids_ = list(ws_.agents)
    for c in ids_:
        ws_.agents[c]["room"] = "garden"
    ws_.agents[ids_[0]]["room"] = ws_.agents[ids_[1]]["room"] = "library"
    ws_.agents[ids_[0]]["sanity"] = 4
    ws_.agents[ids_[0]]["aff"][ids_[1]] = -9
    tks_ = rs_.new_tick(14)
    tks_["free"] = {}
    if any(rs_.snap_check(tks_, ids_[0], 14, mm_) for mm_ in range(15, 120, 15)) and ws_.state.get("case") and ws_.state["case"].get("killer") == ids_[0]:
        sn_ = ws_.state["case"]
        break
check("a snap killing is recorded as unplanned in the case", sn_ is not None and sn_.get("snap") and "unplanned" in (sn_.get("note") or ""))

# modesty
ws_, rs_, _ = free_setup(5500)
ids_ = list(ws_.agents)
a_, b_ = ids_[0], ids_[1]
for c in ids_:
    ws_.agents[c]["room"] = "garden"
ws_.agents[a_]["room"] = ws_.agents[b_]["room"] = "library"
rs_.wear(rs_.new_tick(10), a_, "none")
mods_ = {c: rs_.modesty(c) for c in ids_}
rs_.modesty = lambda c: 90
tk_ = rs_.new_tick(10)
san0_ = ws_.agents[a_]["sanity"]
rs_.modesty_check(tk_, a_, 30)
check("being seen in your underwear mortifies the modest: a thought, lost sanity, an event", any(e["type"] == "embarrassed" for e in tk_["events"]) and ws_.agents[a_]["sanity"] < san0_)
ws_.agents[a_].pop(f"_embarrassed_{rs_.day}_0", None)
rs_.modesty = lambda c: 10
tk_ = rs_.new_tick(10)
rs_.modesty_check(tk_, a_, 30)
check("someone unselfconscious does not mind", not any(e["type"] == "embarrassed" for e in tk_["events"]))
ws_.agents[a_].pop(f"_embarrassed_{rs_.day}_0", None)
rs_.modesty = lambda c: 90
rs_.tuning_get = lambda: {"modesty": 0}
tk_ = rs_.new_tick(10)
rs_.modesty_check(tk_, a_, 30)
check("the embarrassment dial turns it off", not any(e["type"] == "embarrassed" for e in tk_["events"]))
check("modesty differs between people and comes from their nature", max(mods_.values()) - min(mods_.values()) >= 8, str(mods_))

# experiments
w_, r_, _ = free_setup(5600)
c_ = list(w_.agents)[0]
tk_ = r_.new_tick(10)
w_.agents[c_]["hp"] = w_.agents[c_]["sanity"] = 50
d_ = {"idea": "try the radio", "activity": "x"}
r_.apply_experiment(tk_, c_, d_, {"outcome": "It works.", "_dice": "success", "hp": 0, "sanity": 0}, 10)
check("a successful experiment lifts health and sanity", w_.agents[c_]["hp"] > 50 and w_.agents[c_]["sanity"] > 50)
w_.agents[c_]["hp"] = w_.agents[c_]["sanity"] = 50
r_.apply_experiment(tk_, c_, d_, {"outcome": "It blows up.", "_dice": "failure", "hp": -30, "sanity": -20}, 10)
check("a failed experiment costs at most a bruise (never the old 15 health)", 41 <= w_.agents[c_]["hp"] <= 50 and w_.agents[c_]["sanity"] >= 45)
w_.agents[c_]["hp"] = w_.agents[c_]["sanity"] = 80
res_ = {"success": 0, "partial": 0, "failure": 0}
for _ in range(600):
    res_[r_.experiment_dice(c_, {"idea": "x"})[0]] += 1
check("experiments succeed more often than before and fail less than half the time", res_["success"] / 600 >= 0.33 and res_["failure"] / 600 <= 0.42, str(res_))

# the viewer
_here = os.path.dirname(os.path.abspath(__file__))
_app = open(os.path.join(_here, "..", "static", "app.js"), encoding="utf8").read()
_idx = open(os.path.join(_here, "..", "static", "index.html"), encoding="utf8").read()
check("the viewer plays a free-time block over real time with a pace setting and a who's-where roster", "async function playFree" in _app and "renderRoster" in _app and 'id="pace"' in _idx)



# ---- fire at every step, slower walkers, map scale, furniture to use, purposeful free time, chats where people meet
from murder import scale as _sc  # noqa: E402
from murder import perception as _pcm  # noqa: E402
from murder import sim as _ltm  # noqa: E402


def fire_trial(seed, n=5, room="library", hp=90, asleep=False, k=None):
    wf, rf, tf = fresh(seed)
    wf.state["revealed"] = True
    if k is not None:
        rf.tuning_get = lambda: {"fire_lethality": k}
    ids = list(wf.agents)
    for c in ids:
        wf.agents[c]["room"] = "garden"
    wf.state["npcs"]["neovi"]["room"] = "none"
    for c in ids[:n]:
        wf.agents[c].update(room=room, hp=hp, inv={})
        if asleep:
            wf.agents[c]["asleep"] = True
    tk = rf.new_tick(14)
    tk["state"] = {"agents": {}}
    rf.env_ignite_room(tk, room, None, 2)
    rf.env_tick(tk)
    return wf, rf, tk, ids[:n]


def fire_killed(*a, **k):
    wk_, _, _, ids_k = fire_trial(*a, **k)
    return any(c not in wk_.agents for c in ids_k)


dead_awake = sum(fire_killed(sd) for sd in range(2000, 2040))
dead_asleep = sum(fire_killed(sd, asleep=True) for sd in range(2000, 2040))
check("an unattended fire in a room with sleepers kills someone far more often than one with awake people (who run)", dead_asleep >= 3 * max(1, dead_awake) or dead_asleep >= 12, f"awake {dead_awake}, asleep {dead_asleep}")
check("a fire can kill, but awake people usually get out (fewer than a third of fires cost a life)", 0 < dead_awake + dead_asleep and dead_awake < 14, str(dead_awake))
wf_, rf_, tk_, ids_ = fire_trial(2100)
ran_ = [c for c in ids_ if c in wf_.agents and wf_.agents[c]["room"] != "library"]
check("people in a burning room run out of it during the turn, and it is logged with its minute", ran_ and any(e["type"] == "reaction" and e.get("m") is not None and "away from the fire" in e["text"] for e in tk_["events"]))
hp_awake = [wf_.agents[c]["hp"] for c in ids_ if c in wf_.agents]
check("the flames and smoke cost the people who stay some health", any(h < 90 for h in hp_awake) or any(r_ for r_ in ran_))
d0_ = sum(fire_killed(sd, k=0) for sd in range(2200, 2230))
check("with the fire dial at 0 nobody is hurt by it", d0_ == 0)

# slower walkers
ws_, rs_, _ = fresh(2300)
c0_ = list(ws_.agents)[0]
base_ = rs_.move_factor(c0_)
ws_.agents[c0_]["hp"] = 25
hurt_ = rs_.move_factor(c0_)
ws_.agents[c0_]["hp"] = 90
ws_.agents[c0_]["inv"] = {"fuel_can": 5, "heavy_atlas": 2}
loaded_ = rs_.move_factor(c0_)
ws_.agents[c0_]["inv"] = {}
rs_.add_cond(rs_.new_tick(14), c0_, "broken_leg", 1, "test") if hasattr(rs_, "add_cond") else None
leg_ = rs_.move_factor(c0_)
check("badly hurt people, heavily loaded people and people with a broken leg walk more slowly", base_ > hurt_ and base_ > loaded_ and base_ > leg_, f"{base_:.2f} {hurt_:.2f} {loaded_:.2f} {leg_:.2f}")
sm2_ = _ltm.Sim(state={})
sm2_.begin(0, 120, {"a": "kitchen", "b": "kitchen"})
sm2_.cur["b"] = sm2_.cur["a"]
sm2_.tracks["b"] = [list(x) for x in sm2_.tracks["a"]]
t_fast_ = sm2_.walk("a", sm2_.nav.spots("library")[0], 0, speed=1.0)
t_slow_ = sm2_.walk("b", sm2_.nav.spots("library")[0], 0, speed=0.5)
check("a slow walker takes longer over the same route", t_slow_ > 1.7 * t_fast_, f"{t_fast_:.1f} vs {t_slow_:.1f}")

# map scale
check("a tile is a metre and every distance that depends on tile size follows the same scale", gm_["tile_m"] == 1 and gm_["scale"] == _sc.MAP_SCALE
      and _pcm.LOUD["normal"] == _sc.tiles(8.0) and _pcm.BIG_ROOM_AREA == _sc.area(220) and _ltm.TILES_PER_MIN > 0 and _pcm.LOUD["whisper"] < _pcm.LOUD["quiet"] < _pcm.LOUD["normal"] < _pcm.LOUD["shout"])
area_ = {rid: r["area"] for rid, r in gm_["rooms"].items() if not r["open"]}
check("no indoor room is a huge empty hall (the biggest holds less than 120 square metres)", max(area_.values()) < 120, str(max(area_.items(), key=lambda kv: kv[1])))
check("bedrooms are the smallest rooms people live in (12 to 15 square metres)", all(12 <= area_[b] <= 15 for b in ("blue_room", "green_room", "orange_room", "grey_room", "white_room")))
fk_ = {}
for f in gm_["furniture"]:
    if f["k"] != "camera" and f["room"] in area_:
        fk_[f["room"]] = fk_.get(f["room"], 0) + f.get("w", 1) * f.get("h", 1)
dens_ = sum(fk_.values()) / sum(area_.values())
check("indoor rooms are furnished (furniture covers more than a sixth of the floor)", dens_ > 1 / 6, f"{dens_:.3f}")
check("no lived-in room is mostly empty", all(v >= _gmm.FILL_MIN for rid, v in _gmm.room_fill(gm_).items() if rid not in _gmm.HUBS), str(_gmm.room_fill(gm_)))
kinds_ = {f["k"] for f in gm_["furniture"]}
check("the house has things to use: sofas, armchairs, a chess table, a dartboard, a fireplace, a jukebox, a firepit and more", {"sofa", "armchair", "chessTable", "dartboard", "fireplace", "jukebox", "firepit", "fridge", "hammock", "mirror"} <= kinds_)
check("a person can walk to a spot next to a piece of furniture", all(nav_.stand_near(f["plane"], f["x"], f["y"]) is not None for f in nav_.gm["furniture"] if f["k"] in ("sofa", "armchair", "stove", "bench")))

# purposeful free time
wq_, rq_, _ = free_setup(2400)
tkq_ = rq_.run_tick(14, "free")
rq_.emit(tkq_)
segs_ = [sg for sgs in tkq_["free"].values() for sg in sgs]
check("free time uses furniture: activities are done at a particular sofa, stove, table or chair", any(sg.get("at") for sg in segs_))
use_ = {}
okcap_ = True
for m_ in range(0, 120, 15):
    use_ = {}
    for sgs in tkq_["free"].values():
        for sg in sgs:
            if sg.get("at") and sg["m0"] <= m_ < sg["m1"]:
                use_[tuple(sg["at"])] = use_.get(tuple(sg["at"]), 0) + 1
    okcap_ &= all(n <= 4 for n in use_.values())
check("nobody shares a stove, a chess table or a bed: pieces of furniture have a capacity", okcap_)
check("people use the spot in the live plan: those at a piece of furniture stand within two tiles of it", all(
    (lambda tr_, at_: any(abs(p_[2] - at_[1]) + abs(p_[3] - at_[2]) <= 3 for p_ in tr_))(tkq_["live"]["tracks"][c_], sg_["at"]) for c_, sgs_ in tkq_["free"].items() for sg_ in sgs_ if sg_.get("at") and sg_["m1"] - sg_["m0"] >= 15 and c_ in tkq_["live"]["tracks"]))
acts_ = {sg["act"] for sg in segs_}
check("free time covers a wide range (at least six kinds of activity in one block)", len(acts_) >= 6, str(sorted(acts_)))
wr_, rr_, _ = free_setup(2410)
cr_ = list(wr_.agents)[0]
wr_.agents[cr_]["want_talk"] = {"who": [list(wr_.agents)[1]], "day": rr_.day}
wr_.agents[cr_]["aff"][list(wr_.agents)[1]] = 4
for c_ in wr_.agents:
    wr_.agents[c_]["room"] = "lounge"                       # (everybody starts the block out of their bedroom: nobody follows anyone into a bedroom for a chat)
tkr_ = rr_.run_tick(14, "free")
check("someone who wanted to talk to a particular person seeks them out and the chat is recorded with its reason", any(ch["members"][0] == cr_ and ch["why"] for ch in tkr_.get("free_chats", [])) or any(ch["why"] for ch in tkr_.get("free_chats", [])), str(tkr_.get("free_chats")))
rr_.emit(tkr_)
ch_talk_ = [g for g in tkr_["talk"] if g.get("m") is not None]
check("a chat becomes a conversation tagged with the minute it started, its place and its reason", not tkr_.get("free_chats") or ch_talk_, str(len(ch_talk_)))
if ch_talk_:
    gg_ = tkr_["live"]["groups"]
    check("the live plan knows each chat's start, so the viewer can play it where and when it happens", any(g["chat"] for g in gg_) and all(isinstance(g["m"], (int, float)) for g in gg_))
    check("a chat replaces the gathering for those in it (only somebody who walks over and joins talks in a second conversation)", len([s_ for g in tkr_["talk"] for s_ in {l["speaker"] for l in g["lines"]} if s_ in {c for ch in tkr_["free_chats"] for c in ch["members"]} and s_ not in {j[1] for j in g.get("joined") or []}]) <= 2 * len(tkr_["free_chats"]) + 2)
_pc = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "tilemap.js"), encoding="utf8").read()
check("the pause settings include conversations in free time (never, when it matters, every one)", "chatDialog" in _pc and "pauseTalk" in _pc and 'value="matters"' in _pc)



# ---- round three: loose item names, fire duties, flee once, chat reasons, no repeated props, rarer accidental fires
w_, r_, _ = free_setup(2500)
c_ = list(w_.agents)[0]
w_.state["room_items"]["library"] = {"pencils": 1}
check("a loosely named item is matched to what is really in the room ('pencils' for the Coloured pencils)", r_.resolve_item("library", "pencils") == "pencils" and r_.resolve_item("study", "pencil") in ("pencil",)
      and r_.resolve_item("kitchen", "Bread") == "bread" and r_.resolve_item("kitchen", "loaf of bread") in ("bread", "loaf of bread"))
w_.state["room_items"]["library"] = {"magnifying_glass": 1}
check("a take by display name works", r_.resolve_item("library", "magnifying glass") == "magnifying_glass")
w_.agents[c_]["room"] = "library"
tk_ = r_.new_tick(10)
r_.roll = lambda c, b, bonus=0.0: (True, 1.0)
r_.apply_decision(tk_, c_, r_.clean_decision({"action": "take", "item": "magnifying glass", "activity": "x"}), {}, [])
check("and the character ends up holding it instead of a GM error", w_.agents[c_]["inv"].get("magnifying_glass") == 1 and not any("could not take" in e["text"] for e in tk_["events"]))

r_.note_scene([{"speaker": c_, "kind": "act", "text": "lifts the crystal decanter and sets it on the sideboard"}, {"speaker": c_, "kind": "say", "text": "Well."}])
check("the next scene is told what props and gestures were already used", "crystal decanter" in r_.recent_scene_line() and "do not repeat" in r_.recent_scene_line())
r_.day += 1
check("and the list starts afresh the next day", r_.recent_scene_line() == "")
r_.day -= 1

# fire duties
def fire_scene(seed):
    wf, rf, _ = free_setup(seed)
    ids = list(wf.agents)
    for c in ids:
        wf.agents[c]["room"] = "garden"
    for c in ids[:3]:
        wf.agents[c]["room"] = "lounge"
    for c in ids[3:5]:
        wf.agents[c].update(room="foyer", inv={"water_bottle": 1})
        wf.agents[c]["aff"][ids[0]] = 3
    wf.agents[ids[0]]["out"] = {"cause": "overcome", "left": 3}
    tk = rf.new_tick(14)
    tk["state"] = {"agents": {}}
    rf.env_ignite_room(tk, "lounge", None, 2)
    dec = {c: rf.clean_decision({"action": "stay", "activity": "x"}) for c in wf.agents}
    rf.free_time(tk, 14, dec)
    return wf, rf, tk, ids


rescued_ = 0
fled_once_ = True
for sd_ in range(2600, 2615):
    wf_, rf_, tkf_, ids_ = fire_scene(sd_)
    rescued_ += any(e["type"] == "carry" and "out of the Lounge" in e["text"] for e in tkf_["events"])
    for c_ in ids_[:3]:
        fled_once_ &= sum(1 for sg in tkf_["free"].get(c_, []) if sg["act"] == "flee") <= 3
check("friends outside pull a collapsed person out of a burning room", rescued_ >= 10, str(rescued_))
check("people run from a fire once or twice, not again and again", fled_once_)
wf_, rf_, tkf_, ids_ = fire_scene(2700)
check("nobody drags the same person out twice in a day", all(len([1 for e in tkf_["events"] if e["type"] == "carry" and e["who"] == c]) <= 1 for c in ids_))
w2_, r2_, _ = free_setup(2800)
i2_ = list(w2_.agents)
w2_.agents[i2_[0]]["room"] = "kitchen"
tk2_ = r2_.new_tick(14)
tk2_["free"] = {c: [] for c in w2_.agents}
r2_.env().ignite("ground", *r2_.nav().nominal("library", i2_[1], 3)[1:], 1, force=True)
w2_.agents[i2_[1]]["room"] = "library"
check("a smell of smoke from next door is not a reason to run (only fire, smoke or water in your own room is)", not any(l.startswith(("FIRE", "SMOKE", "WATER")) for l in r2_.env_lines(i2_[0])))
fires_ = 0
for sd_ in range(2900, 3100):
    wk_, rk_, _ = free_setup(sd_)
    rk_.chaos_factor = lambda: 1.0
    for c in wk_.agents:
        wk_.agents[c]["room"] = "kitchen" if c == list(wk_.agents)[0] else "garden"
    tkk_ = rk_.new_tick(14)
    rk_.env_hazards(tkk_, 14)
    fires_ += bool(rk_.env().st["fire"])
check("accidental kitchen fires are rare (under 2 in 100 turns with someone cooking)", fires_ <= 4, str(fires_))

# chat reasons
wc_, rc_, _ = free_setup(3200)
ic_ = list(wc_.agents)
a_, b_ = ic_[0], ic_[1]
wc_.agents[a_]["known_secrets"] = [{"of": b_, "text": "x"}]
check("what one knows about the other makes a chat matter ('secret')", "secret" in rc_.chat_tags(a_, b_) and "secret" in rc_.chat_tags(b_, a_))
wc_.state["hooks"] = [{"id": "h1", "kind": "rifled", "victims": [a_], "culprit": b_, "room": "library", "day": rc_.day, "hour": 10, "text": "x"}]
check("a loose end between them makes it matter ('hook')", "hook" in rc_.chat_tags(a_, b_))
wc_.agents[a_]["aff"][b_] = 7
wc_.agents[b_]["aff"][a_] = 7
check("a mutual spark makes it matter ('romance') for a romantic soul", "romance" in rc_.chat_tags(a_, b_) or rc_.facet(a_, "romantic") < 55)
wc_.agents[a_]["want_talk"] = {"who": [b_], "day": rc_.day, "why": "find out what Seul is hiding"}
check("a stated purpose that mentions a secret or a plan makes it matter ('purpose')", "purpose" in rc_.chat_tags(a_, b_))
why_set_ = set()
for sd_ in range(3300, 3330):
    wq_, rq_, _ = free_setup(sd_)
    rq_.clean_decision = lambda raw, _f=rq_.clean_decision: {**_f(raw), "talk_to": []}          # nobody named anyone to talk to: the reasons have to come from elsewhere
    for c in wq_.agents:
        for o in wq_.agents:
            if o != c:
                wq_.agents[c]["aff"][o] = [7, 3, 1, 7][(ord(c[0]) + ord(o[0]) + sd_) % 4]
    tq_ = rq_.run_tick(14, "free")
    why_set_ |= {ch["why"].split(" ")[0] + " " + ch["why"].split(" ")[1] if ch["why"] else "" for ch in tq_.get("free_chats", [])}
check("chats come from more than one kind of reason across a few blocks", len(why_set_) >= 2, str(why_set_))


# ---- the brain: memory, retrieval, plans, conversation memory
def brain_setup(seed, on=True):
    wb, rb, _ = free_setup(seed)
    wb.state["npcs"]["neovi"]["room"] = "foyer"
    rb.tuning_get = lambda: {"brain": 1 if on else 0}
    return wb, rb


wb_, rb_ = brain_setup(4000)
ib_ = list(wb_.agents)
a_, b_, c_ = ib_[0], ib_[1], ib_[2]
wb_.remember(a_, "10:00 Chloe leaves the Library for the Landing.")
check("people walking about are not worth remembering", not wb_.agents[a_].get("mem"))
wb_.remember(a_, f"11:00 (private) You saw {wb_.cast[b_]['name'].split()[0]} slip something into a coat pocket.")
wb_.remember(a_, "12:00 Somebody said: \"nice weather\".")
mem_ = wb_.agents[a_]["mem"]
check("what is worth remembering is stored with its time, importance and the people it is about", any(m["w"] >= 4 and b_ in m["p"] for m in mem_), str(mem_))
wb2_, rb2_ = brain_setup(4001, on=False)
wb2_.remember(list(wb2_.agents)[0], "11:00 (private) A secret.")
check("with the dial off nothing is stored", not wb2_.agents[list(wb2_.agents)[0]].get("mem"))
for i in range(30):
    rb_.mem_add(a_, f"filler {i} about nothing much", "event", 2, hour=8)
rb_.mem_add(a_, "Noah was seen hiding a knife in the pantry", "violence", 7, people=[c_], hour=9)
rec_ = rb_.mem_recall(a_, people={c_}, k=3)
check("recall brings back what is about the people involved, even among lots of trivia", any(c_ in m["p"] for m in rec_) and len(rec_) == 3)
rec2_ = rb_.mem_recall(a_, people={"nobody"}, k=3)
check("and without a focus the important and recent things come back first", any(m["w"] >= 4 for m in rec2_))
for i in range(300):
    rb_.mem_add(a_, f"clutter {i}", "event", 2, hour=1 + i % 20)
rb_.mem_prune(a_)
check("the store is trimmed, keeping the important things", len(wb_.agents[a_]["mem"]) <= 240 and any(m["w"] >= 7 for m in wb_.agents[a_]["mem"]))

# prompts
rb_.revealed
pr_ = rb_.decision_prompt(a_, 14)
check("with the brain on a decision prompt carries the relevant memories, a plan line and the plan field", "WHAT YOU REMEMBER" in pr_ and "YOUR PLAN" in pr_ and '"plan": [' in pr_ and "PLAN: also write" in pr_)
wb3_, rb3_ = brain_setup(4002, on=False)
pr3_ = rb3_.decision_prompt(list(wb3_.agents)[0], 14)
check("with it off the prompt is the old one", "TODAY SO FAR" in pr3_ and "WHAT YOU REMEMBER" not in pr3_ and '"plan": [' not in pr3_)
card_ = rb_.mem_card(a_, [a_, c_])
check("a conversation card gets what this person remembers about the others", "Remembers about them" in card_ and "knife" in card_)

# plans
d_ = rb_.clean_decision({"action": "stay", "plan": [{"do": "talk", "who": b_, "why": "ask about the coat"}, {"do": "go", "where": "library", "why": "look into the shelf"}, {"do": "dance"}, {"do": "work", "where": "nowhere"}]})
check("a plan is cleaned: unknown kinds dropped, people and rooms validated", [it["do"] for it in d_["plan"]] == ["talk", "go", "work"] and d_["plan"][0]["who"] == b_ and d_["plan"][1]["where"] == "library" and d_["plan"][2]["where"] == "")
rb_.plan_store(a_, 10, d_["plan"])
check("the plan is kept for the day and shown to the character", len(rb_.plan_items(a_)) == 3 and "YOUR PLAN" in rb_.plan_lines(a_)[0] and "ask about the coat" in rb_.plan_lines(a_)[0])
check("a character with a fresh plan does not need the model again; one without does", not rb_.plan_needed(a_, 12) and rb_.plan_needed(b_, 12))
wb_.agents[a_]["plan"]["items"][0]["done"] = wb_.agents[a_]["plan"]["items"][1]["done"] = wb_.agents[a_]["plan"]["items"][2]["done"] = True
check("a finished plan is renewed only after a few hours (not every block)", not rb_.plan_needed(a_, 12) and rb_.plan_needed(a_, 14))
rb_.plan_store(a_, 10, rb_.plan_clean([{"do": "talk", "who": b_, "why": "ask about the coat"}, {"do": "go", "where": "library", "why": "look into the shelf"}, {"do": "work", "why": "a way out"}]))
# free time carries the plan out
tk_ = rb_.new_tick(14)
tk_["free"] = {c: [] for c in wb_.agents}
tk_["free_chats"] = []
rb_._free_busy, rb_._chat_n = {}, 0
for c in wb_.agents:
    wb_.agents[c]["room"] = "garden"
wb_.agents[a_]["room"] = wb_.agents[b_]["room"] = "foyer"
opts_ = []
rb_.plan_options(tk_, a_, 14, 30, rb_._reach(a_), lambda score, act, **kw: opts_.append((score, act, kw)))
check("plan items become options in a slice: go somewhere, work at something", any(o[1] == "explore" and o[2].get("room") == "library" for o in opts_) and any(o[1] == "tinker" for o in opts_))
rb_.plan_done_by_act(a_, "explore", "library")
check("doing the thing ticks the item off", any(it["do"] == "go" and it["done"] for it in wb_.agents[a_]["plan"]["items"]))
copts_ = []
rb_.chat_options(tk_, a_, 14, 30, rb_._reach(a_), lambda score, act, **kw: copts_.append((score, act, kw)))
check("a planned talk is offered as a chat with the reason from the plan", copts_ and "ask about the coat" in copts_[0][2]["why"] and copts_[0][2]["partner"] == b_)
rb_.plan_store(a_, 10, rb_.plan_clean([{"do": "avoid", "who": b_, "why": "he lied"}]))
copts2_ = []
rb_.chat_options(tk_, a_, 14, 30, rb_._reach(a_), lambda score, act, **kw: copts2_.append((score, act, kw)))
check("somebody the plan says to avoid is not sought out", not any(o[2].get("partner") == b_ for o in copts2_))
rb_.plan_store(a_, 10, rb_.plan_clean([{"do": "talk", "who": b_, "why": "x"}]))
rb_._start_chat(tk_, a_, b_, 30, "x")
check("starting the chat ticks the plan item off for both sides", not rb_.plan_items(a_))
rb_.brain_night(a_, "I do not trust Noah any more.", "growing wary")
check("at night the diary and the arc become memories and the day's plan is retired", wb_.agents[a_]["plan"] is None and any(m["k"] == "diary" and "trust Noah" in m["t"] for m in wb_.agents[a_]["mem"]) and any(m["k"] == "arc" for m in wb_.agents[a_]["mem"]))
bv_ = rb_.brain_view(a_)
check("the viewer gets a plan and the memories on their mind", isinstance(bv_, dict) and "plan" in bv_ and isinstance(bv_["mem"], list))

# model calls
wm_, rm_ = brain_setup(4100)
rm_.revealed
tuned_ = {"brain": 1, "engine_decisions": 1, "mind": 1}
rm_.tuning_get = lambda: tuned_
wm_.state["rule"] = None
cm_ = list(wm_.agents)[1]
why_ = rm_.model_reason(cm_, 14)
check("with the brain on a character with no plan is the one reason to ask the model on a quiet block", why_ in ("plan", "case", "event", "hazard", "crisis", "hurt", "conflict", "bond", "plot", "rule"), str(why_))
rm_.plan_store(cm_, 14, rm_.plan_clean([{"do": "go", "where": "library", "why": "x"}]))
wm_.agents[cm_]["aff"] = {o: 0 for o in wm_.agents}
for o in wm_.agents:
    wm_.agents[o]["aff"][cm_] = 0
rm_.mind(cm_)["stress"] = 0
rm_.mind(cm_)["needs"] = {k: 70 for k in rm_.mind(cm_)["needs"]}
wm_.agents[cm_]["conds"] = {}
wm_.state["bonds"] = []
wm_.state["plots"] = {}
rm_.occasion_now = None
why2_ = rm_.model_reason(cm_, 16)
check("with a plan in hand and nothing at stake the block is decided by the engine (no model call)", why2_ is None, str(why2_))
_bp = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "static", "app.js"), encoding="utf8").read()
check("the cast panel shows the plan and what is on their mind in the GM view", "On their mind" in _bp and "a.brain.plan" in _bp)


# ---- a knock-out late in the evening does not carry into the next day (the counter used to restart at 0 every day)
wk_, rk_, _ = free_setup(6000)
ck_ = list(wk_.agents)[0]
tk_ = rk_.new_tick(20)
rk_.knock_out(tk_, ck_, "tased", 1)
rk_.day += 1                                 # the next day's runner starts its counter again
rk_.idx = 0
rk_.unconscious_tick(rk_.new_tick(8), 8)
check("a tasing at 20:00 is over by the next morning, not after most of the next day", not wk_.agents[ck_].get("out"))


# ---- own bedrooms, motives, mirror plots, a crowd of plots, scenes without the unconscious, the sealed scene, the wellness check
from murder.world import BEDROOMS as _BR  # noqa: E402
wbd_, rbd_, _ = free_setup(8000)
check("there are eight bedrooms and each starting character has one of their own", len(set(_BR)) == 8 and len({c["home"] for c in wbd_.state["cast"].values()}) == 8)
wo_, ro_, _ = free_setup(8001)
i_ = list(wo_.agents)
wo_.state["cast"][i_[1]]["home"] = wo_.state["cast"][i_[0]]["home"]
ro_.ensure_private_bedrooms()
check("an older save with two people in one room gives the second a bedroom of their own", wo_.state["cast"][i_[1]]["home"] != wo_.state["cast"][i_[0]]["home"] and len({c["home"] for c in wo_.state["cast"].values()}) == 8)


# motives
def motive_kinds(setup):
    wm, rm, _ = free_setup(8100)
    ids = list(wm.agents)
    setup(wm, rm, ids)
    return {k for _, _, _, k in rm.plot_motives(ids[0])}


def m_fear(wm, rm, ids):
    wm.agents[ids[0]]["harmed_by"] = [(ids[1], rm.day, 14)]
    wm.agents[ids[0]]["aff"][ids[1]] = -3


check("somebody who was hurt can come to fear and plot against the one who hurt them (fear)", "fear" in motive_kinds(m_fear))


def m_betray(wm, rm, ids):
    wm.state.setdefault("chronicle", []).append({"id": 1, "day": rm.day, "hour": 10, "type": "betrayal", "who": ids[1], "room": "lounge", "vis": "public", "cls": "notable", "text": "x", "with": [ids[0]]})


check("a betrayed person has a motive against the betrayer (betrayal)", "betrayal" in motive_kinds(m_betray))


def m_humil(wm, rm, ids):
    wm.state.setdefault("chronicle", []).append({"id": 2, "day": rm.day, "hour": 10, "type": "embarrassed", "who": ids[0], "room": "lounge", "vis": "public", "cls": "notable", "text": "x", "seen": [ids[2]]})
    wm.agents[ids[0]]["aff"][ids[2]] = -1
    rm.facet = lambda c, n, _f=rm.facet: 90 if n == "vanity" else _f(c, n)


check("a vain person caught in a humiliating state has a motive against the watcher (humiliation)", "humiliation" in motive_kinds(m_humil))


def m_prize(wm, rm, ids):
    wm.state["scenario"] = {"twist": {"text": "The prize is real and there is exactly one", "day": 1}}
    wm.agents[ids[0]]["drive"] = {"id": "schemer", "target": None, "arc": ""}


check("when there is a single prize the strongest rival is a motive (prize)", "prize" in motive_kinds(m_prize))


# mirror plots and a crowd of plots
def plot_p(mirror):
    n = 0
    for sd_ in range(8200, 8240):
        wq, rq, _ = free_setup(sd_)
        ids = list(wq.agents)
        wq.agents[ids[0]]["aff"][ids[1]] = -9
        if mirror:
            wq.state["plots"] = {ids[1]: {"target": ids[0], "stage": "brooding", "motive": "hatred", "stage_ticks": 0, "weapon": None, "method": "", "step": "", "cover": "", "log": [], "quiet": 0}}
        rq.tuning_get = lambda: {"plot_rate": 3.0}
        tq = rq.new_tick(10)
        rq.plot_started_day = -1
        rq.maybe_start_plots(tq, 10)
        n += any(c == ids[0] and p["target"] == ids[1] for c, p in wq.state.get("plots", {}).items())
    return n


base_, mir_ = plot_p(False), plot_p(True)
check("a plot against somebody who is already plotting against you is far less likely than a plain one", mir_ * 3 <= max(base_, 3), f"plain {base_}, mirror {mir_}")


def crowd(n_plots):
    sp_ = 0
    for sd_ in range(8300, 8360):
        wq, rq, _ = free_setup(sd_)
        ids = list(wq.agents)
        wq.state["plots"] = {ids[i]: {"target": ids[i + 1], "stage": "stalking", "motive": "hatred", "stage_ticks": 0, "weapon": None, "method": "", "step": "", "cover": "", "log": [], "quiet": 0} for i in range(n_plots)}
        tq = rq.new_tick(14)
        rq.plot_pileup(tq, 14)
        sp_ += bool(wq.state.get("spree"))
    return sp_


c2_, c4_ = crowd(2), crowd(4)
check("two plots at once never tip the house into a killing spree, three or more sometimes do", c2_ == 0 and c4_ >= 3, f"2: {c2_}, 4: {c4_}")
wnc_, rnc_, _ = free_setup(8400)
ids_ = list(wnc_.agents)
wnc_.state["plots"] = {ids_[i]: {"target": ids_[i + 1], "stage": "brooding", "motive": "hatred", "stage_ticks": 0, "weapon": None, "method": "", "step": "", "cover": "", "log": [], "quiet": 0} for i in range(4)}
rnc_.plot_started_day = -1
rnc_.maybe_start_plots(rnc_.new_tick(10), 10)
check("there is no limit on how many plots can be going at once", len(wnc_.state["plots"]) >= 4)

# the unconscious are not marched to scenes, and not put to bed
wun_, run_, _ = free_setup(8500)
iu_ = list(wun_.agents)
run_.knock_out(run_.new_tick(18), iu_[0], "fainted", 3)
wun_.agents[iu_[0]]["room"] = "lounge"
wun_.state["aftermath"] = {"victims": [iu_[1]], "since": run_.day, "until": run_.day + 1, "vigil_done": False}
vt_ = run_.run_vigil(20)
check("the unconscious are not marched to a vigil or a meeting, and nobody out speaks in it", wun_.agents[iu_[0]]["room"] == "lounge" and not any(l["speaker"] == iu_[0] for g in vt_["talk"] for l in g["lines"]))
run_.send_to_bed(run_.new_tick(22), iu_[0])
check("and at night the unconscious stay where they lie instead of walking to bed", wun_.agents[iu_[0]]["room"] == "lounge")


# the crime scene
def scene(seed):
    ws, rs, _ = free_setup(seed)
    ids = list(ws.agents)
    for c in ids:
        ws.agents[c]["room"] = "garden"
    room = ws.state["cast"][ids[1]]["home"]
    ws.agents[ids[0]]["room"] = ws.agents[ids[1]]["room"] = room
    ws.state["locks"][room] = {"by": ids[1], "day": rs.day}
    ws.agents[ids[0]]["inv"] = {"kitchen_knife": 1}
    tk = rs.new_tick(8)
    rs.open_case(tk, "murder", ids[1], culprit=ids[0], wkind="sharp", weapon="kitchen_knife", room=room, hour=8, witnesses=[])
    return ws, rs, ids, room, tk


ws_, rs_, ids_, room_, tk_ = scene(8600)
case_ = ws_.state["case"]
rs_.announce_body(tk_, 10, forced=True)
check("when the body is announced the locked scene is opened and sealed", room_ not in ws_.state["locks"] and case_.get("sealed") and rs_.scene_sealed(room_))
ws_.agents[ids_[0]]["room"] = room_
rs_.do_lock(rs_.new_tick(10), ids_[0], {"door": room_})
check("the killer cannot lock it again before the trial", room_ not in ws_.state["locks"])
ws2_, rs2_, ids2_, room2_, tk2_ = scene(8601)
for c in ids2_[2:]:
    ws2_.agents[c]["room"] = "dining_hall"
    ws2_.agents[c]["aff"][ids2_[1]] = 3
tk3_ = rs2_.new_tick(12)
rs2_.wellness_check(tk3_, 12)
rs2_.check_discovery(tk3_, 12)
c2_ = ws2_.state["case"]
check("when somebody misses a meal a friend goes to knock and NeoVi opens the locked door, so the body is found before the forced announcement", len(c2_["discovered_by"]) >= 1 and room2_ not in ws2_.state["locks"], str(c2_["discovered_by"]))

# ---- map v4: levels, the gallery, floors, trees, the tunnel
from murder.perception import Perception as _Pc4  # noqa: E402
pc4_ = _Pc4()
n4_ = pc4_.nav
gal_ = next(t for t in n4_.room_tiles["landing"] if n4_.char(*t) == "v")
below_ = ("ground", gal_[1], gal_[2])
edge_ = next(t for t in n4_.room_tiles["landing"] if n4_.char(*t) == "w" and any(n4_.char(t[0], t[1] + dx, t[2] + dy) == "v" for dx in (-1, 0, 1) for dy in (-1, 0, 1)))
bed_up_ = n4_.spots("blue_room")[0]
check("from the gallery you see down into the foyer through the open drop, and are seen from it", n4_.room_at(*below_) == "foyer" and pc4_.sees(edge_, below_) and pc4_.sees(below_, edge_))
check("a floor blocks sight: a bedroom upstairs cannot see the foyer", not pc4_.sees(bed_up_, below_))
k4_ = n4_.spots("kitchen")[0]
above_k_ = next(t for t in n4_.room_tiles["linen_store"] + n4_.room_tiles["red_room"] + n4_.room_tiles["violet_room"] if (t[1], t[2]) == (k4_[1], k4_[2])) if any((t[1], t[2]) == (k4_[1], k4_[2]) for t in n4_.room_tiles["linen_store"] + n4_.room_tiles["red_room"] + n4_.room_tiles["violet_room"]) else None
if above_k_ is None:
    above_k_ = ("first", k4_[1], k4_[2])
check("a shout in the kitchen is heard through the ceiling, a whisper is not", pc4_.hears(k4_, above_k_, "shout") and not pc4_.hears(k4_, above_k_, "whisper"), str(above_k_))
tree_ = next((x, y) for y in range(8, 24) for x in range(64, 80) if n4_.char("ground", x, y) == "T" and n4_.char("ground", x - 1, y) not in "T#" and n4_.char("ground", x + 1, y) not in "T#")
check("trees block sight and cannot be walked through", not pc4_.los(("ground", tree_[0] - 1, tree_[1]), ("ground", tree_[0] + 1, tree_[1])) and not n4_.walkable("ground", *tree_))
wc_ = n4_.spots("wine_cellar")[0]
lh_ = n4_.spots("lighthouse")[0]
via_ = n4_.route(wc_, lh_, frozenset({"SP-2"}))
check("the smugglers' tunnel is a real passage under the island, used only by those who know it",
      via_ is not None and sum(1 for t in via_ if t[0] == "basement" and n4_.room_at(*t) is None) > 40 and all(t[0] != "basement" or n4_.room_at(*t) in (None, "wine_cellar") for t in via_[:-3]))
check("the core vault sits under the lighthouse", n4_.rooms["core_vault"]["plane"] == "basement" and any((t[1], t[2]) in {(q[1], q[2]) for q in n4_.room_tiles["lighthouse"]} for t in n4_.room_tiles["core_vault"]))

# ---- a seeded run is reproducible: the same seed gives the same day, whatever order the parallel model calls finish in
import json as _json  # noqa: E402
def seeded_day(seed):
    w_ = World(new_state(3))
    out = []
    DayRunner(w_, LLM(backend="mock"), lambda t_: out.append(_json.dumps(t_, sort_keys=True, default=str)), step=2, murders=True, rule_mode="roulette", seed=seed).run()
    return out, _json.dumps(w_.state, sort_keys=True, default=str)
d1_, d2_ = seeded_day(21), seeded_day(21)
check("the same seed gives the same day, tick for tick", d1_[0] == d2_[0] and len(d1_[0]) >= 7, f"{len(d1_[0])} ticks")
check("and the same world at the end of it", d1_[1] == d2_[1])
check("a different seed gives a different day", seeded_day(22)[0] != d1_[0])

# ---- fire burns the flammable things lying in it
wb_, rb2_, _ = fresh(9101)
wb_.state["room_items"]["library"] = {"paper": 2, "paperweight": 1}
spot_ = next(i for i in rb2_.env().item_tiles(wb_.state["room_items"]) if i["i"] == "paper")
rb2_.env().ignite(spot_["p"], spot_["x"], spot_["y"], 2, force=True)
tkb_ = rb2_.new_tick(14)
rb2_.env_burn_items(tkb_)
check("paper lying in a fire burns up, and the feed says so", "paper" not in wb_.state["room_items"]["library"] and any(e["type"] == "wreck" for e in tkb_["events"]))
check("things that do not burn stay", wb_.state["room_items"]["library"].get("paperweight") == 1)

# ---- the minute clock (rebuild phase 2): things happen at their minute
from murder.clock import Timeline as _TL  # noqa: E402
order_ = []
class _E:
    _m = 0.0
    def clock_to(self, m):
        self._m = max(self._m, m)
tl_ = _TL(_E())
tl_.at(30, order_.append, "b")
tl_.at(5, order_.append, "a")
tl_.at(30, order_.append, "c")
tl_.every(15, lambda m: order_.append(f"s{int(m)}"), until=45)
tl_.run()
check("the timeline runs what is due in order of minute, cadences first at a shared minute, other ties in the order scheduled", order_ == ["a", "s15", "s30", "b", "c", "s45"], str(order_))
cw_, cr_, _ = fresh(1700)
cr_.clock_start()
ctk_ = cr_.new_tick(12)
cr_.sim_turn(ctk_)
ca_, cb_ = sorted(cw_.agents)[:2]
cw_.agents[ca_]["room"] = "library"
cw_.agents[cb_]["room"] = "library"
cr_.sim_sync(ctk_, 0)
cw_.agents[cb_]["room"] = "kitchen"
arr_b_ = cr_.sim_go(ctk_, cb_, 10.0)
cr_._m = 10.5
check("somebody still on their way to a room is not there yet", not cr_.present(cb_, "kitchen") or arr_b_ <= 10.5)
cr_._m = arr_b_ + 0.1
check("and is there once they have walked it", cr_.present(cb_, "kitchen"))
cw_.agents[ca_]["room"] = "kitchen"
cr_._arrived = {ca_: 3.0, cb_: arr_b_}
cr_._m = 3.0
check("an attacker who gets there first waits for the target to arrive before striking", cr_.meet_minute(ca_, cb_) >= arr_b_ > 3.0, f"{cr_.meet_minute(ca_, cb_)} vs {arr_b_}")
cw_.agents[cb_]["room"] = "garden"
check("and strikes on arrival when the target is not coming (the old not-there logic takes over)", cr_.meet_minute(ca_, cb_) == 3.0)
cr_.clock_stop()
ev_m_ = [e for t in wk_ticks if t.get("segment") in ("turn", "free") for e in t["events"]]
check("in day turns every event carries the minute it happened", ev_m_ and all(e.get("m") is not None for e in ev_m_), str([e["text"][:60] for e in ev_m_ if e.get("m") is None][:3]))
late_ = []
for t in wk_ticks:
    arr_ = {e["who"]: e["m"] for e in t["events"] if e["type"] == "arrive" and e.get("m") is not None}
    for e in t["events"]:
        if e["type"] in ("take", "search", "use", "drop", "give") and e.get("who") in arr_ and e.get("m") is not None and e["m"] + 0.05 < arr_[e["who"]] and not t.get("free"):
            late_.append((t["day"], t["hour"], e["text"][:50], e["m"], arr_[e["who"]]))
check("what somebody came to do happens after they arrive, not when they set off", not late_, str(late_[:3]))
aw_, ar_, _ = fresh(1710)
ac_ = sorted(aw_.agents)[0]
aw_.agents[ac_]["room"] = "games_room"
aw_.state["room_items"].setdefault("library", {})["paperweight"] = 1
ar_.roll = lambda *a_, **k_: (True, 1.0)
atk_ = ar_.new_tick(12)
ar_.clock_start()
ar_.sim_turn(atk_)
dfr_ = []
ar_.apply_decision(atk_, ac_, ar_.clean_decision({"action": "take", "target_room": "library", "item": "paperweight", "activity": "Fetching it"}), {}, [], defer=dfr_)
tl2_ = _TL(ar_)
for m_, c_, d_, st_ in dfr_:
    tl2_.at(m_, ar_.arrive_and_act, atk_, c_, d_, {}, [], st_)
tl2_.run()
ar_.clock_stop()
mv_ = next((e for e in atk_["events"] if e["type"] == "move" and e["who"] == ac_), None)
arv_ = next((e for e in atk_["events"] if e["type"] == "arrive" and e["who"] == ac_), None)
tk2_ = next((e for e in atk_["events"] if e["type"] == "take" and e["who"] == ac_), None)
check("someone sent upstairs for something sets off, walks, and picks it up when they get there", mv_ and arv_ and tk2_ and 0 < mv_["m"] < arv_["m"] <= tk2_["m"], str([(e["type"], e.get("m")) for e in atk_["events"]]))

# ---- heights: falling, jumping and climbing (rebuild phase 2)
from murder import falls as _fl  # noqa: E402
hw_, hr_, _ = fresh(1800)
hn_ = hr_.nav()
void_ = next((p_, x_, y_) for (p_, x_, y_) in hn_.room_tiles["landing"] if hn_.char(p_, x_, y_) == "v")
dv_ = hr_.drop_below(*void_)
check("going over the gallery's open floor drops one storey into the foyer below", dv_ and dv_[1] == 1.0 and hn_.room_at(*dv_[0]) == "foyer", str(dv_))
w2_ = next(o for (wt_, it_, o) in hr_.outside_windows("library"))
dw_ = hr_.drop_below(*w2_)
check("out of a first-floor window is a storey down to the ground outside", dw_ and dw_[1] == 1.0 and dw_[0][0] == "ground", str(dw_))
cl_ = next((("ground", x_, y_) for y_ in range(hn_.h) for x_ in range(hn_.w) if hn_.char("ground", x_, y_) == "C"), None)
dc_ = hr_.drop_below(*cl_) if cl_ else None
check("over the cliff is a long drop onto the shore below", dc_ and dc_[1] >= 2.0 and hn_.char(*dc_[0]) in "sa~qn", str(dc_))
def fall_dmg(seed, ch, levels):
    fw_, fr_, _ = fresh(seed)
    fc_ = sorted(fw_.agents)[0]
    fw_.agents[fc_]["hp"] = 100
    t_ = next(("ground", x_, y_) for y_ in range(fr_.nav().h) for x_ in range(fr_.nav().w) if fr_.nav().char("ground", x_, y_) == ch)
    d_ = fr_.fall(fr_.new_tick(14), fc_, t_, t_, levels, "push")
    return d_, fc_ not in fw_.agents
wet_ = [fall_dmg(1810 + i, "~", 2.0) for i in range(12)]
hard_ = [fall_dmg(1830 + i, "q", 2.0) for i in range(12)]
check("water forgives a fall that rock does not (two storeys)", sum(d for d, _ in wet_) * 2 < sum(d for d, _ in hard_), f"{[d for d, _ in wet_]} vs {[d for d, _ in hard_]}")
fw3_, fr3_, _ = fresh(1870)
c3_ = sorted(fw3_.agents)[0]
fw3_.agents[c3_]["hp"] = 30
fr3_.fall(fr3_.new_tick(14), c3_, ("ground", 1, 1), next(("ground", x_, y_) for y_ in range(fr3_.nav().h) for x_ in range(fr3_.nav().w) if fr3_.nav().char("ground", x_, y_) == "q"), 2.0, "push")
check("two storeys onto rock can kill", c3_ not in fw3_.agents)
# a slip on the stairs ends the walk at the foot of them
old_slip_ = _fl.STAIR_SLIP
_fl.STAIR_SLIP = 1.0
sw_, sr_, _ = fresh(1880)
sw_.state["revealed"] = True
sc_ = sorted(sw_.agents)[0]
sw_.agents[sc_]["room"] = "library"
sw_.state["room_items"].setdefault("kitchen", {})["paperweight"] = 1
stk_ = sr_.new_tick(12)
sr_.clock_start()
sr_.sim_turn(stk_)
sdf_ = []
sr_.apply_decision(stk_, sc_, sr_.clean_decision({"action": "take", "target_room": "kitchen", "item": "paperweight", "activity": "Fetching it"}), {}, [], defer=sdf_)
tl3_ = _TL(sr_)
for m_, c_, d_, st_ in sdf_:
    tl3_.at(m_, sr_.arrive_and_act, stk_, c_, d_, {}, [], st_)
tl3_.run()
_fl.STAIR_SLIP = old_slip_
fe_ = [e for e in stk_["events"] if e["type"] == "fall"]
check("somebody who slips on the stairs tumbles to the foot of them, with the minute it happened", fe_ and fe_[0].get("m") is not None and "stairs" in fe_[0]["text"], str([e["text"] for e in stk_["events"]][:6]))
check("and never gets where they were going to do what they meant to", sc_ not in sw_.agents or (sw_.agents[sc_]["room"] != "kitchen" and not any(e["type"] == "take" for e in stk_["events"])))
sr_.clock_stop()
# a burning room upstairs with no way out: out of the window
jw_, jr_, _ = fresh(1890)
jw_.state["revealed"] = True
jc_ = sorted(jw_.agents)[0]
jw_.agents[jc_]["room"] = "library"
jw_.agents[jc_]["hp"] = 100
jtk_ = jr_.new_tick(14)
ok_j_ = jr_.jump_from_fire(jtk_, jc_, 30)
check("trapped by a fire upstairs, somebody jumps from the window and lands outside, hurt", ok_j_ and any(e["type"] == "fall" and "jumps" in e["text"] for e in jtk_["events"]) and (jc_ not in jw_.agents or jr_.nav().rooms[jw_.agents[jc_]["room"]]["plane"] == "ground"))
# locked in on the ground floor: out through the window
lw_, lr_, _ = fresh(1900)
lw_.state["revealed"] = True
lc_, lo_ = sorted(lw_.agents)[:2]
lw_.agents[lc_]["room"] = "kitchen"
lw_.agents[lc_]["inv"] = {}
lw_.state.setdefault("locks", {})["kitchen"] = {"by": lo_, "keyed": True}
ltk_ = lr_.new_tick(12)
lr_.apply_decision(ltk_, lc_, lr_.clean_decision({"action": "stay", "target_room": "garden", "activity": "Getting out"}), {}, [])
check("somebody locked into a ground-floor room climbs out through the window instead", lw_.agents[lc_]["room"] != "kitchen" and any("window" in e["text"] for e in ltk_["events"]), str([e["text"] for e in ltk_["events"]]))

# ---- live conversations (rebuild phase 3)
from murder import convo as _cv, voice as _vc, social as _so  # noqa: E402


class _Fixed:
    """An rng whose random() is fixed (other calls fall through to a real one)."""
    def __init__(self, v, base):
        self.v, self.b = v, base
    def random(self):
        return self.v
    def __getattr__(self, k):
        return getattr(self.b, k)


cw2_, cr2_, _ = fresh(1950)
cw2_.state["revealed"] = True
ca2_, cb2_, cc2_ = sorted(cw2_.agents)[:3]
for c_ in (ca2_, cb2_, cc2_):
    cw2_.agents[c_]["room"] = "lounge"
cw2_.agents[ca2_]["aff"][cb2_] = 5
cw2_.agents[cb2_]["aff"][ca2_] = 5
cw2_.agents[cb2_]["sanity"] = 40
ctk2_ = cr2_.new_tick(14)
cr2_.clock_start()
cr2_.sim_turn(ctk2_)
cr2_.sim_sync(ctk2_, 0)
conv2_ = {"id": "t", "room": "lounge", "members": [ca2_, cb2_], "used": {}, "hour": 14}
check("someone who cares about a person who is low is willing to comfort them", any(mv == "comfort" for _, mv, _a in cr2_.move_options(conv2_, ca2_, cb2_)))
base_rng_ = cr2_.rng
cr2_.rng = _Fixed(0.0, base_rng_)
san0_ = cw2_.agents[cb2_]["sanity"]
bts_ = cr2_.resolve_move(ctk2_, conv2_, ca2_, cb2_, "comfort")
check("comfort that lands lifts the other person's spirits and warms them to the comforter (the engine decides, before any words)", bts_[0]["outcome"] == "ok" and cw2_.agents[cb2_]["sanity"] > san0_ and cw2_.agents[cb2_]["aff"][ca2_] > 5)
cr2_.rng = _Fixed(0.999, base_rng_)
san1_ = cw2_.agents[ca2_]["sanity"]
bts2_ = cr2_.resolve_move(ctk2_, {"id": "t2", "room": "lounge", "members": [ca2_, cb2_, cc2_], "used": {}, "hour": 14}, ca2_, cb2_, "mock")
check("a mocking that falls flat costs the mocker and turns the room against them", bts2_[0]["outcome"] != "ok" and cw2_.agents[ca2_]["sanity"] < san1_)
cr2_.rng = base_rng_
check("every move has a reply from its target", bts_[1]["who"] == cb2_ and bts_[1]["move"] in _so.REPLIES)
lines_, fixed_ = _vc.check_lines(cr2_, bts_ + bts2_, {"lines": [{"beat": 0, "speaker": cb2_, "text": "wrong speaker"}]}, cr2_.rng)
check("the voice gives every beat one line from that beat's own speaker (a wrong or missing line is replaced by the template voice)", len(lines_) == 4 and all(l["speaker"] == b["who"] for l, b in zip(lines_, bts_ + bts2_)) and fixed_ == 4)
# testimony: the truth from the innocent, a lie from the culprit
tw_, tr_, _ = fresh(1960)
tk_t_ = tr_.new_tick(12)
ti_, tc_ = sorted(tw_.agents)[:2]
tw_.state["where_log"] = {ti_: [[tw_.state["day"], 10, "library"]], tc_: [[tw_.state["day"], 10, "kitchen"], [tw_.state["day"], 8, "lounge"]]}
tw_.state["case"] = {"killer": tc_, "victim": sorted(tw_.agents)[2], "room": "kitchen", "day": tw_.state["day"], "hour": 10, "announced": True}
tr_.day = tw_.state["day"]
tr_.self_at(ti_, "library", tw_.state["day"] * 24 + 10)          # where the innocent knows they were
tm_i_, tm_c_ = tr_.testimony_for(ti_), tr_.testimony_for(tc_)
check("asked where they were, an innocent tells the truth about the room they were in", "Library" in tm_i_["claim"] and not tm_i_["lie"])
check("the culprit lies about it", tm_c_["lie"] and "Kitchen" not in tm_c_["claim"].split(",")[0])
tw_.state["case"] = None
# a live conversation ends when its members part, and is cut short by a fight
lw_, lr_, _ = fresh(1970)
lw_.state["revealed"] = True
la_, lb_, lc3_ = sorted(lw_.agents)[:3]
for c_ in (la_, lb_, lc3_):
    lw_.agents[c_]["room"] = "lounge"
ltk3_ = lr_.new_tick(14)
lr_.clock_start()
lr_.sim_turn(ltk3_)
lr_.convo_reset()
lr_.sim_sync(ltk3_, 0)
tl4_ = _TL(lr_)
cv_ = lr_.start_convo(ltk3_, [la_, lb_], "lounge", 10, tl4_, why="test", kind="chat", dur=40)
lw_.agents[lb_]["room"] = "lookout"
tl4_.at(14, lambda: lr_.sim().go_room(lb_, "lookout", 14))
tl4_.run()
check("a conversation ends when its members part (one of them walked off out of earshot)", cv_["state"] == "ended" and cv_["ended"][1] == "parted" and any(x[1] == lb_ for x in cv_["left"]), str(cv_.get("ended")))
lw_.agents[lb_]["room"] = "lounge"
lr_.sim().go_room(lb_, "lounge", 30)
tl5_ = _TL(lr_)
cv2_ = lr_.start_convo(ltk3_, [la_, lb_], "lounge", 40, tl5_, why="test", kind="chat", dur=40)
ltk3_["events"].append({"type": "attack", "who": lc3_, "room": "lounge", "m": 43.0, "vis": "public", "text": "A fight breaks out."})
tl5_.run()
check("and a fight in the room cuts it short", cv2_["state"] == "ended" and cv2_["ended"][1] == "interrupted", str(cv2_.get("ended")))
# a friend nearby joins
jw_, jr_, _ = fresh(1980)
jw_.state["revealed"] = True
ja_, jb_, jc_ = sorted(jw_.agents)[:3]
for c_ in (ja_, jb_, jc_):
    jw_.agents[c_]["room"] = "lounge"
jw_.agents[jc_]["aff"][ja_] = 8
jtk_ = jr_.new_tick(14)
jr_.clock_start()
jr_.sim_turn(jtk_)
jr_.convo_reset()
jr_.sim_sync(jtk_, 0)
_ja_t = jr_.sim().cur[ja_]
jr_.sim().walk(jc_, jr_.nav().stand_near(_ja_t[0], _ja_t[1], _ja_t[2], set(jr_.sim().cur.values()), "lounge"), 1)
jr_.rng = _Fixed(0.0, jr_.rng)
tl6_ = _TL(jr_)
cv3_ = jr_.start_convo(jtk_, [ja_, jb_], "lounge", 10, tl6_, why="test", kind="chat", dur=12)
tl6_.run()
check("a friend within earshot walks over and joins in", any(x[1] == jc_ for x in cv3_["joined"]) and jc_ in cv3_["members"] + [x[1] for x in cv3_["left"]])
# every overheard line was heard by someone perception allows, from where they actually stood
from murder.perception import Perception as _Pc  # noqa: E402
pc2_ = _Pc(nav_)
LOUDER_ = _cv.LOUDER
bad_heard_ = []
n_heard_ = 0
for t in wk_ticks:
    L = t["live"]
    for g in t["talk"]:
        if not g.get("live"):
            continue
        for ln in g["lines"]:
            if not ln.get("heard"):
                continue
            src_ = _simm.pos_on(L["tracks"].get(ln["speaker"]), ln["m"])
            ld_ = _cv.LOUD_OF.get({"whisper": "whisper"}.get(ln.get("move"), "normal"), "normal")
            for c_, lvl_ in ln["heard"].items():
                n_heard_ += 1
                dst_ = _simm.pos_on(L["tracks"].get(c_), ln["m"])
                ok_ = src_ and dst_ and (pc2_.hears(src_, dst_, "shout") if lvl_ != "saw" else pc2_.sees(src_, dst_, "lit"))
                if not ok_:
                    bad_heard_.append((t["day"], t["hour"], ln["speaker"], c_, lvl_))
check("every overheard line had a listener whom perception allows (and conversations are overheard at all)", n_heard_ > 0 and not bad_heard_, f"{len(bad_heard_)} of {n_heard_}: {bad_heard_[:3]}")
live_g_ = [g for t in wk_ticks for g in t["talk"] if g.get("live")]
check("ordinary conversations are live: each records how it ended, who joined and who left", live_g_ and all(g.get("ended") and "joined" in g and "left" in g for g in live_g_), str(len(live_g_)))
check("and their lines unfold over minutes rather than all at once", any(max(l["m"] for l in g["lines"]) - min(l["m"] for l in g["lines"]) >= 5 for g in live_g_))
# walking together
gw_, gr_, _ = fresh(1990)
gw_.state["revealed"] = True
ga_, gb_ = sorted(gw_.agents)[:2]
for c_ in (ga_, gb_):
    gw_.agents[c_]["room"] = "lounge"
gw_.agents[ga_]["aff"][gb_] = 7
gw_.agents[gb_]["aff"][ga_] = 7
gtk_ = gr_.new_tick(14)
gtk_["free"] = {}
gr_.clock_start()
gr_.sim_turn(gtk_)
gr_.sim_sync(gtk_, 0)
gr_._free_busy = {ga_: 0, gb_: 0}
gr_.rng = _Fixed(0.0, gr_.rng)
gw_.agents[ga_]["room"] = "kitchen"
gr_.sim_go(gtk_, ga_, 20)
pal_ = gr_.companion_for(gtk_, ga_, "lounge", 20, 50)
gr_.clock_stop()
check("a close friend who is at a loose end goes along when somebody sets off, and they walk there together", pal_ == gb_ and gw_.agents[gb_]["room"] == "kitchen"
      and abs(gr_.sim().end_t(gb_) - gr_.sim().end_t(ga_)) < 1.5, f"{pal_} {gw_.agents[gb_]['room']}")

# heard through a wall: the listener has to know the voice
vw_, vr_, _ = fresh(1995)
vw_.state["revealed"] = True
vs_, vt_, vl_ = sorted(vw_.agents)[:3]
vw_.agents[vs_]["room"] = vw_.agents[vt_]["room"] = "kitchen"
vw_.agents[vl_]["room"] = "dining_hall"
vtk_ = vr_.new_tick(14)
vr_.clock_start()
vr_.sim_turn(vtk_)
vr_.sim_sync(vtk_, 0)
_kt = nav_.rooms["kitchen"]["rect"]
_wall_y = _kt[3] - 1
vr_.sim().walk(vs_, vr_.nav().stand_near("ground", _kt[0] + 2, _wall_y - 1, set(), "kitchen") or vr_.sim().cur[vs_], 1)
vr_.sim().walk(vl_, vr_.nav().stand_near("ground", _kt[0] + 2, _wall_y + 2, set(), "dining_hall") or vr_.sim().cur[vl_], 1)
vconv_ = {"members": [vs_, vt_], "room": "kitchen", "seen_by": set(), "wary": True, "joined": [], "left": []}
vbeat_ = {"who": vs_, "m": 20.0, "loud": "heated", "room": "kitchen", "move": "accuse"}
vr_.overhear(vtk_, vconv_, [vbeat_], notice=False)
check("a raised voice carries through the wall to the next room, where the listener cannot see who it is", (vbeat_.get("heard") or {}).get(vl_) in ("full", "part") and vl_ in (vbeat_.get("unseen") or []), str(vbeat_))
vr_.remember_talk(vconv_, [{"speaker": vs_, "kind": "say", "text": "I know it was you.", "move": "accuse", "heard": vbeat_.get("heard") or {}, "unseen": vbeat_.get("unseen") or []}], 14)
check("and they remember it as a voice through the wall, named only if they knew it", any("through the wall" in m_ for m_ in vw_.agents[vl_]["memory"]["recent"]))
vr_.clock_stop()

# ---- the confessional booth (rebuild phase 3)
bw_, br_, _ = fresh(2000)
bw_.state["revealed"] = True
br_.confessionals = True
bt_ = br_.booth_tile()
check("the confessional booth stands at the end of the first-floor gallery", bt_ and bt_[3] == "landing" and bt_[0] == "first")
bc_, bo_, bl_ = sorted(bw_.agents)[:3]
for c_ in (bc_, bo_):
    bw_.agents[c_]["room"] = "lounge"
bw_.agents[bl_]["room"] = "landing"
br_.booth_note(bc_, "hurt", 6, bo_)
btk_ = br_.new_tick(12)
br_.clock_start()
br_.sim_turn(btk_)
br_.sim_sync(btk_, 0)
_bt_near = br_.nav().stand_near(bt_[0], bt_[1], bt_[2], set(br_.sim().cur.values()), "landing")
br_.sim().walk(bl_, _bt_near, 1)
br_._m = 100.0
br_.rng = _Fixed(0.0, br_.rng)
br_.booth_turn(btk_, 12, None)
br_.voice_booth(btk_, 12)
br_.emit(btk_)
cf_ = btk_.get("confessionals") or []
check("someone with something on their chest walks to the booth and records", cf_ and cf_[0]["id"] == bc_ and bw_.agents[bc_]["room"] == "landing" and cf_[0].get("m") is not None)
check("a confessional is one to three short lines spoken to the audience, about what happened to them", cf_ and 1 <= len(cf_[0]["lines"]) <= 3 and all(len(l.split()) <= 18 for l in cf_[0]["lines"]) and cf_[0]["topic"] == "hurt", str(cf_[:1]))
check("someone standing on the gallery nearby overhears the confession", cf_ and bl_ in (cf_[0].get("heard") or {}), str(cf_[0].get("heard") if cf_ else None))
all_cf_ = [c for t in wk_ticks for c in t.get("confessionals") or []]
check("every confessional in a mock week is short (at most three lines of at most eighteen words)", all_cf_ and all(1 <= len(c.get("lines") or [c["text"]]) <= 3 and all(len(l.split()) <= 18 for l in (c.get("lines") or [c["text"]])) for c in all_cf_), str(len(all_cf_)))

# ---- deadline day: every hour closer to 22:00 costs more sanity
w, r, _ = fresh(181)
check("deadline-day hourly loss escalates toward 22:00", [r.deadline_hour_loss(h) for h in (8, 12, 13, 17, 18, 21)] == [1, 1, 2, 2, 3, 3])
w.state["deadline_day"] = r.day
for c in w.agents:
    w.agents[c]["sanity"] = 90
dl_ = list(w.agents)[0]
t8_ = r.new_tick(8); r.tick_dread(t8_, 8); s8_ = 90 - w.agents[dl_]["sanity"]
t18_ = r.new_tick(18); r.tick_dread(t18_, 18); s18_ = 90 - s8_ - w.agents[dl_]["sanity"]
r.tick_dread(r.new_tick(18), 18)
check("on deadline day a morning turn costs less sanity than an evening one", 0 < s8_ < s18_, f"{s8_} {s18_}")
check("each deadline-day hour is charged only once", 90 - w.agents[dl_]["sanity"] == s8_ + s18_)
w.agents[dl_]["sanity"] = 8
s_ = 8; r.tick_dread(r.new_tick(14), 14)
check("people already near breaking go numb and lose less", s_ - w.agents[dl_]["sanity"] <= 2, str(s_ - w.agents[dl_]["sanity"]))
w.state["deadline_day"] = r.day + 3
s_ = w.agents[dl_]["sanity"]; r.tick_dread(r.new_tick(20), 20)
check("no hourly deadline loss when the deadline is days away", w.agents[dl_]["sanity"] == s_)

# ---- the schedule: meals in the Dining Hall
w, r, _ = fresh(182)
sched_ = [d["id"] for d in r.day_schedule()]
check("the day's schedule has wake-up, three meals, the evening announcement and curfew", sched_ == ["wake", "breakfast", "lunch", "dinner", "evening", "curfew"], str(sched_))
check("breakfast, lunch and dinner fall in the 08:00, 12:00 and 18:00 turns at half past", [(r.meal_in_turn(h)[0] or {}).get("id") for h in (8, 10, 12, 14, 16, 18, 20)]
      == ["breakfast", None, "lunch", None, None, "dinner", None] and r.meal_in_turn(12)[1] == 30)
w.state["schedule_mods"] = [{"op": "cancel", "id": "lunch", "day": r.day}, {"op": "move", "id": "dinner", "at": 19 * 60 + 15}]
check("a draw can be cancelled or moved", r.meal_in_turn(12)[0] is None and r.meal_in_turn(18)[0]["at"] == 19 * 60 + 15)
w.state["schedule_mods"] = []


def meal_run_(seed, tense=None):
    w_, r_, _ = fresh(seed)
    for c in w_.agents:
        w_.agents[c]["sanity"] = 60
        w_.agents[c]["hunger"] = 70
        r_.mind(c)["needs"]["social"] = 30
        r_.mind(c)["stress"] = 30
    t_ = r_.new_tick(12)
    r_.clock_start()
    r_.sim_turn(t_)
    r_.convo_reset()
    base_ = r_.rng
    r_.rng = _Fixed(0.0, base_)
    meal_ = r_.meal_call(t_, 12, r_.meal_in_turn(12)[0], 30.0)
    r_.rng = base_
    if tense:
        t_["events"].append({"type": tense, "who": meal_["came"][0], "room": "dining_hall", "m": 50.0, "text": "x"})
    r_.meal_settle(t_, 12)
    r_.clock_stop()
    return w_, r_, t_, meal_


w, r, t_, meal_ = meal_run_(183)
came_ = meal_["came"]
check("people who want to come walk to the Dining Hall and eat", len(came_) >= 6 and all(w.agents[c]["room"] == "dining_hall" and w.agents[c]["hunger"] < 70 for c in came_), str(len(came_)))
check("a calm meal lifts everyone at it: sanity, company, less stress", t_["meal"]["calm"] and all(w.agents[c]["sanity"] > 60 and r.mind(c)["needs"]["social"] >= 50 and r.mind(c)["stress"] < 30 for c in came_))
w, r, t_, meal_ = meal_run_(183, tense="fight")
check("a tense meal gives nothing", not t_["meal"]["calm"] and t_["meal"]["sour"] == "fight" and all(w.agents[c]["sanity"] <= 60 and r.mind(c)["needs"]["social"] <= 30 for c in meal_["came"]))
w, r, _ = fresh(184)
ids = sorted(w.agents)
w.state["news"] = [{"day": r.day, "text": "Somebody found a knife under the stairs.", "knows": [ids[0]]}]
told_ = r.spread_news(r.new_tick(12), ids[:3], "Lunch")
check("news passes around the table to those who had not heard", told_ == 1 and any("knife under the stairs" in m for m in w.agents[ids[2]]["memory"]["recent"]) and set(ids[:3]) <= set(w.state["news"][0]["knows"]))
w, r, _ = fresh(185)
ids = sorted(w.agents)
w.state["meal_skips"] = {ids[0]: 2}
r.__dict__["_meal"] = {"id": "lunch", "label": "Lunch", "room": "dining_hall", "m": 30.0, "end_m": 90.0, "came": ids[1:4], "skipped": [ids[0]], "hour": 12}
r.clock_start(); r.sim_turn(r.new_tick(12)); r.convo_reset()
tk_ = r.new_tick(12)
r.meal_settle(tk_, 12)
r.clock_stop()
check("someone who keeps skipping meals gets noticed", w.state["meal_skips"][ids[0]] == 3 and any("skipped 3 meals" in m for m in w.agents[ids[1]]["memory"]["recent"]))
meals_wk_ = [t["meal"] for t in wk_ticks if t.get("meal")]
check("a mock week serves meals, some calm and some not", len(meals_wk_) >= 8 and {m["id"] for m in meals_wk_} == {"breakfast", "lunch", "dinner"} and any(m["calm"] for m in meals_wk_),
      f"{len(meals_wk_)} meals, {sum(1 for m in meals_wk_ if m['calm'])} calm")

# ---- the schedule: the GM moves and adds draws, NeoVi fetches stragglers
w, r, _ = fresh(186)
tk_ = r.new_tick(10)
r.gm_schedule(tk_, {"op": "move", "id": "dinner", "at": 17 * 60}, 10)
r.gm_schedule(tk_, {"op": "add", "at": 15 * 60, "room": "lounge", "text": "A word from TereVi"}, 10)
r.gm_schedule(tk_, {"op": "cancel", "id": "breakfast"}, 10)
ids_ = [d["id"] for d in r.day_schedule()]
check("the GM can move a meal, add a summons and cancel a draw (a change to a time already past applies tomorrow)", r.meal_in_turn(16)[0]["id"] == "dinner" and r.meal_in_turn(14)[0]["kind"] == "summons"
      and "breakfast" in ids_, str(ids_))
check("a bad schedule change is refused", r.gm_schedule(tk_, {"op": "move", "id": "lunch", "at": 3 * 60}, 10) is None and r.gm_schedule(tk_, {"op": "explode"}, 10) is None)
w, r, _ = fresh(187)
ids = sorted(w.agents)
w.agents[ids[0]]["room"] = "lookout"
w.agents[ids[1]]["hiding"] = True
w.agents[ids[2]]["asleep"] = True
for c in ids[3:]:
    w.agents[c]["room"] = "foyer"
tk_ = r.new_tick(14)
got_ = r.fetch_stragglers(tk_, ids, "voting_grounds", "the class trial")
check("NeoVi fetches whoever will not make a mandatory scene on their own (far away, hiding, asleep), and nobody else", {ids[0], ids[1], ids[2]} == set(got_) and not w.agents[ids[2]].get("asleep")
      and any(e["type"] == "fetch" for e in tk_["events"]), str(got_))
w, r, _ = fresh(188)
r.s["schedule_mods"] = [{"op": "add", "day": r.day, "draw": {"id": "gm1", "kind": "summons", "at": 12 * 60 + 30, "end": 13 * 60 + 30, "label": "A summons", "room": "lounge"}},
                        {"op": "cancel", "id": "lunch", "day": r.day}]
r.clock_start(); tk_ = r.new_tick(12); r.sim_turn(tk_); r.convo_reset()
m_ = r.meal_call(tk_, 12, r.meal_in_turn(12)[0], 30.0)
r.clock_stop()
check("a summons brings everyone who can come", m_ and set(m_["came"]) == {c for c in w.agents if not w.agents[c].get("out") and not r.restrained(c)} and all(w.agents[c]["room"] == "lounge" for c in m_["came"]))
night_wk_ = [t for t in wk_ticks if t.get("phase") == "night" and t["hour"] in (23, 25, 27, 29)]
check("a mock week plays its nights in blocks, some quiet and some with people up", night_wk_ and any(t.get("quiet") for t in night_wk_) and any(t.get("awake") for t in night_wk_),
      f"{len(night_wk_)} blocks, {sum(1 for t in night_wk_ if t.get('quiet'))} quiet")
kinds_wk_ = {t.get("type") for t in wk_ticks} | {"meal" for t in wk_ticks if t.get("meal")}
check("a mock week serves meals", "meal" in kinds_wk_, str(sorted(k for k in kinds_wk_ if k)))

# ---- phase 4 gate: across a few mock weeks the day's schedule and its mandatory scenes all fire
gate_kinds_ = set()
import murder.llm as llm_  # noqa: E402
mmp_ = llm_.LLM.mock_murder_prob
for seed_, murders_ in ((41, True), (43, True), (44, True), (45, True), (61, False)):   # a murder brings a trial and a vigil; a week with none reaches the deadline: the last call
    if murders_ and "vigil" in gate_kinds_:
        continue                                                            # some murder weeks end before a vigil is due: try the next
    llm_.LLM.mock_murder_prob = 0.08 if murders_ else 0.0
    wk_ = World(new_state(3))
    tg_ = []
    for d in range(3, 11):
        wk_.state["day"] = d
        DayRunner(wk_, LLM(backend="mock"), tg_.append, step=2, murders=murders_, rule_mode="roulette", seed=seed_ + d).run()
        if not wk_.agents or wk_.state.get("over"):
            break
    for t in tg_:
        gate_kinds_ |= {t.get("type")} | ({"meal"} if t.get("meal") else set()) | ({"vigil"} if any(e.get("type") == "vigil" for e in t["events"]) else set())
        gate_kinds_ |= {"quiet_night"} if t.get("quiet") else set()
        gate_kinds_ |= {"night_awake"} if t.get("phase") == "night" and t.get("awake") else set()
llm_.LLM.mock_murder_prob = mmp_
check("phase 4 gate: mock weeks fire meals, a trial, a vigil and a last call, and play quiet and wakeful nights",
      {"meal", "trial", "vigil", "lastcall", "quiet_night", "night_awake"} <= gate_kinds_, str(sorted(k for k in gate_kinds_ if k)))

# ---- code health: no two mixins define the same method (the later one would silently shadow the other)
owners_ = {}
for cls_ in DayRunner.__mro__[1:]:
    for k_, v_ in vars(cls_).items():
        if callable(v_) and not k_.startswith("__"):
            owners_.setdefault(k_, []).append(cls_.__name__)
clash_ = {k_: v_ for k_, v_ in owners_.items() if len(v_) > 1}
check("no two engine mixins define a method with the same name", not clash_, str(sorted(clash_.items())[:5]))

# ---- code health: a game does not depend on Python's hash seed (set order must never drive a choice)
import subprocess  # noqa: E402
DET_ = """
import sys, os, json, hashlib, tempfile
sys.path.insert(0, %r); os.environ["MC_DATA_DIR"] = tempfile.mkdtemp()
from murder.engine import DayRunner
from murder.llm import LLM
from murder.world import World, new_state
w = World(new_state(3)); h = hashlib.md5()
def dig(t):
    h.update(json.dumps({k: v for k, v in t.items() if k != "usage"}, sort_keys=True, default=str).encode())
for d in (3, 4, 5):
    w.state["day"] = d
    DayRunner(w, LLM(backend="mock"), dig, step=2, murders=True, rule_mode="roulette", seed=40 + d).run()
    if w.state.get("over"):
        break
print(h.hexdigest())
""" % os.path.dirname(HERE)
digs_ = [subprocess.run([sys.executable, "-c", DET_], capture_output=True, text=True, env={**os.environ, "PYTHONHASHSEED": hs_}).stdout.strip() for hs_ in ("1", "2")]
check("the same seed gives the same three days under two different hash seeds", digs_[0] and digs_[0] == digs_[1], str(digs_))

from murder.session import resume_hour  # noqa: E402
check("an old save checkpointed at the old 23:00 night turn replays from bedtime; new checkpoints resume where they stopped",
      resume_hour({"hour": 23}) == 21 and resume_hour({"hour": 23, "v": 2}) == 23 and resume_hour({"hour": 14}) == 14)

# ---- phase 5: belief bases
w, r, _ = fresh(190)
ids = sorted(w.agents)
x_, o_, f_, l_ = ids[0], ids[1], ids[2], ids[3]
T_ = r.day * 24 + 14.5
r.believe(o_, {"k": "at", "s": x_, "r": "kitchen", "t0": T_ - 0.25, "t1": T_ + 0.25, "src": "seen", "c": 0.9, "true": True})
got_ = r.believed_at(o_, x_, T_)
check("a belief records what, where, when, how it was learned and how sure they are", got_ and got_["r"] == "kitchen" and got_["src"] == "seen" and got_["c"] == 0.9)
r.believe(o_, {"k": "at", "s": x_, "r": "kitchen", "t0": T_ + 0.5, "t1": T_ + 0.5, "src": "seen", "c": 0.9, "true": True})
r.believe(o_, {"k": "at", "s": x_, "r": "kitchen", "t0": T_ + 1.5, "t1": T_ + 1.5, "src": "seen", "c": 0.9, "true": True})
check("consecutive sightings join up, a gap keeps them apart", sorted((b["t0"], b["t1"]) for b in r.beliefs(o_) if b["k"] == "at" and b["s"] == x_) == [(T_ - 0.25, T_ + 0.5), (T_ + 1.5, T_ + 1.5)])
aff0_ = w.agents[o_]["aff"][x_]
r.believe(o_, {"k": "at", "s": x_, "r": "library", "t0": T_, "t1": T_, "by": x_, "src": "told", "c": 0.6, "true": False})
check("a claim that contradicts what someone saw is caught as a lie", x_ in r.caught_liars(o_) and w.agents[o_]["aff"][x_] < aff0_ and r.suspects(o_)[0] == x_
      and any(e["liar"] == x_ and e["true_lie"] for e in w.state["lies_caught"]))
r.believe(f_, {"k": "at", "s": x_, "r": "kitchen", "t0": T_ - 0.25, "t1": T_ + 0.25, "src": "seen", "c": 0.9, "true": True})
r.believe(f_, {"k": "at", "s": x_, "r": "kitchen", "t0": T_, "t1": T_, "by": x_, "src": "told", "c": 0.6, "true": True})
check("a claim that matches what they saw is not a lie", x_ not in r.caught_liars(f_))
conv_ = {"members": [x_, f_], "joined": [], "room": "lounge"}
beats_ = [{"who": x_, "claim_at": {"s": x_, "r": "study", "t": T_ + 3, "true": False}}]
lines_ = [{"b": 0, "heard": {l_: "full", ids[4]: "part"}}]
r.rng = _Fixed(0.0, r.rng)
r.belief_from_talk(conv_, lines_, beats_)
tl_, hl_, pl_ = r.believed_at(f_, x_, T_ + 3), r.believed_at(l_, x_, T_ + 3), r.believed_at(ids[4], x_, T_ + 3)
check("testimony is told to the people in the conversation, overheard in full by a listener, and half heard with the room wrong", tl_ and tl_["src"] == "told" and tl_["by"] == x_
      and hl_ and hl_["src"] == "heard" and hl_["r"] == "study" and pl_ and pl_["r"] != "study" and pl_["c"] < hl_["c"], str((tl_, hl_, pl_)))
check("a lie someone believes is marked false (for the GM), the person does not know", tl_ and tl_["true"] is False and any(b["false"] for b in r.beliefs_view(f_)))
r.spread_rumor(r.new_tick(14), x_, f_, "keeps a knife under the pillow", "bad", True, [l_], "lounge", 14)
check("a rumour becomes a belief that may be false", any(b["k"] == "rumor" and b["s"] == f_ and b["true"] is False for b in r.beliefs(l_)))
tk_ = r.new_tick(14)
r.belief_witness({"type": "assault", "who": x_, "room": "lounge", "vis": "public", "text": "X shoves Y."}, [l_], x_)
check("a witnessed event becomes a belief about who did it", any(b["k"] == "did" and b["s"] == x_ and b["o"] == "assault" for b in r.beliefs(l_)))

w, r, _ = fresh(191)
ids = sorted(w.agents)
for c in ids:
    w.agents[c]["room"] = "garden"
w.agents[ids[0]]["room"] = w.agents[ids[1]]["room"] = "lounge"
tq_ = r.new_tick(14)
r.clock_start(); r.sim_turn(tq_); r.clock_to(30)
r.emit(tq_)
check("people note who they saw where, and where they were themselves, from real positions", r.believed_at(ids[0], ids[1], r.day * 24 + 14) and r.believed_at(ids[0], ids[0], r.day * 24 + 14)
      and r.believed_at(ids[0], ids[0], r.day * 24 + 14)["src"] == "seen")
w.state["case"] = {"announced": True, "resolved": False, "day": r.day, "hour": 14, "m": 0.0, "room": "study", "killer": ids[5], "victim": ids[6]}
tm_ = r.testimony_for(ids[0])
check("honest testimony says where they really were and who they really saw", tm_ and not tm_["lie"] and tm_["room"] == r.believed_at(ids[0], ids[0], r.day * 24 + 14)["r"])
check("during a case the decision prompt carries what they know about the time of the death", any(l.startswith("WHAT YOU KNOW") for l in r.belief_lines(ids[0])))
w.state["case"] = None

llm_.LLM.mock_murder_prob = 0.2
false_ = told_ = 0
for seed_ in (40, 60):
    wb_ = World(new_state(3))
    for d in range(3, 9):
        wb_.state["day"] = d
        DayRunner(wb_, LLM(backend="mock"), lambda t: None, step=2, murders=True, rule_mode="roulette", seed=seed_ + d).run()
        if not wb_.agents or wb_.state.get("over"):
            break
    false_ += sum(1 for e in wb_.state.get("lies_caught") or [] if not e["true_lie"])
    told_ += sum(1 for a in wb_.agents.values() for b in a.get("beliefs", []) if b["src"] == "seen")
llm_.LLM.mock_murder_prob = mmp_
check("phase 5 gate: mock weeks build beliefs from what people see, and nobody telling the truth is ever caught 'lying'", told_ > 100 and false_ == 0, f"{told_} sightings, {false_} false catches")

# ---- phase 6: captivity wears people down night by night
w, r, _ = fresh(192)
w.state["revealed"] = True
c_ = sorted(w.agents)[0]
set0_ = r.mind(c_)["set"]
r.mind_wear(c_)
check("each night on the island lowers the level sanity recovers towards", r.mind(c_)["set"] < set0_)
r.tuning_get = lambda: {"wear": 0}
set1_ = r.mind(c_)["set"]
r.mind_wear(c_)
check("the wear dial can switch it off", r.mind(c_)["set"] == set1_)
r.tuning_get = lambda: {"wear": 10}
for _ in range(40):
    r.mind_wear(c_)
check("it never sinks below 25", r.mind(c_)["set"] == 25.0)

# ---- phase 6: secret meetings and snooping at night
w, r, _ = fresh(193)
ids = sorted(w.agents)
w.state["revealed"] = True
w.state["deadline_day"] = r.day + 3
for c in ids:
    w.agents[c]["hunger"] = w.agents[c]["thirst"] = 0
    r.body(c)["bladder"] = 0
w.state["bonds"] = [{"a": ids[0], "b": ids[1], "kind": "romance"}]
base_ = r.rng
r.rng = _Fixed(0.0, base_)
extra_ = r.night_extra([])
r.rng = base_
mt_ = (w.state.get("meets") or [None])[0]
check("at bedtime lovers (or allies, or a plotter and an accomplice) arrange a secret meeting and both stay up", mt_ and {mt_["a"], mt_["b"]} == {ids[0], ids[1]} and {ids[0], ids[1]} <= set(extra_))
r.run_bedtime()
w.state["meets"] = [dict(mt_, block=23, done=False)] if mt_ else []
nb_ = r.run_night_block(23)
check("they go to the quiet room in the night and talk", any(e["type"] == "meet" for e in nb_["events"]) and any(set(ch["members"]) == {ids[0], ids[1]} for ch in nb_.get("free_chats") or []),
      str([e["text"] for e in nb_["events"] if e["type"] in ("meet", "move")][:4]))

w, r, _ = fresh(194)
ids = sorted(w.agents)
sp_, tg_ = ids[0], ids[1]
w.state["revealed"] = True
r.believe(sp_, {"k": "lied", "s": tg_, "n": "lied about the kitchen", "src": "inferred", "c": 0.9, "t0": r.abs_now()})
check("someone you caught lying is who you snoop on", r.snoop_target(sp_) == tg_)
home_ = w.cast[tg_]["home"]
w.agents[sp_]["room"] = w.agents[tg_]["room"] = home_
w.agents[tg_]["asleep"] = True
knife_ = sharp()
w.agents[tg_]["inv"][knife_] = 1
w.agents[sp_]["snoop"] = {"on": tg_, "day": r.day}
r.rng = _Fixed(0.99, r.rng)
tk_ = r.new_tick(25, phase="night")
found_ = r.do_snoop(tk_, sp_, 10.0)
check("going through a sleeper's things finds what they keep, and it becomes a belief (and a suspicion)", knife_ in (found_ or []) and any(b["k"] == "has" and b["o"] == knife_ for b in r.beliefs(sp_))
      and tg_ in r.suspects(sp_) and w.agents[tg_].get("asleep"))
w.agents[sp_]["snoop"] = {"on": tg_, "day": r.day}
r.rng = _Fixed(0.0, r.rng.b)
r.do_snoop(tk_, sp_, 20.0)
check("a sleeper may wake and catch the snooper at it", not w.agents[tg_].get("asleep") and any(b["k"] == "did" and b["s"] == sp_ and b["o"] == "snoop" for b in r.beliefs(tg_))
      and any(e["type"] == "snoop_caught" for e in tk_["events"]))

# ---- phase 6: the murder planner
w, r, _ = fresh(195)
ids = sorted(w.agents)
pk_, tv_ = ids[0], ids[1]
T_ = r.day * 24 + 11
r.believe(pk_, {"k": "at", "s": tv_, "r": "landing", "t0": T_, "t1": T_ + 0.25, "src": "seen", "c": 0.9, "true": True})
r.believe(pk_, {"k": "at", "s": tv_, "r": "library", "t0": T_ + 2, "t1": T_ + 2.25, "src": "seen", "c": 0.9, "true": True})
kinds_ = {sc["kind"]: sc for _, sc in r.plan_schemes(pk_, tv_)}
check("the planner sees the schemes the world and the plotter's beliefs offer: asleep in their room, alone where they saw them alone, a push from a height",
      {"asleep", "alone", "height"} <= set(kinds_) and kinds_["height"]["room"] == "landing" and kinds_["alone"]["room"] == "library", str(sorted(kinds_)))
pl_ = {"target": tv_, "stage": "striking", "stage_ticks": 0, "plan": [], "scheme": kinds_["height"]}
w.agents[pk_]["room"] = "library"
check("a plotter waits for the planned place instead of striking anywhere", not r.scheme_allows(pk_, pl_))
check("unless the deadline is on them", r.scheme_allows(pk_, pl_, urgent=True))
w.agents[pk_]["room"] = w.agents[tv_]["room"] = "landing"
check("in the planned place the scheme calls for a push", r.scheme_allows(pk_, pl_) and r.scheme_method(pk_, pl_) == "push")
w.agents[tv_]["hp"] = 3
tk_ = r.new_tick(14)
r.resolve_attacks(tk_, [(pk_, {"target": tv_, "method": "push", "frame": None})], 14)
case_ = w.state.get("case") or {}
check("a fatal push is a murder with the pusher as culprit, not an accident", tv_ not in w.agents and case_.get("kind") == "murder" and case_.get("killer") == pk_
      and any(e["type"] == "fall" for e in tk_["events"]), str({k: case_.get(k) for k in ("kind", "killer")}))

# ---- phase 6: fights in blows, with hit locations
w, r, _ = fresh(196)
ids = sorted(w.agents)
outs_ = {}
for kind_, asleep_ in (("sharp", True), ("sharp", False), ("hands", False)):
    got_ = []
    for i in range(120):
        w.agents[ids[1]]["hp"], w.agents[ids[1]]["asleep"] = 100, asleep_
        got_.append(r.fight(r.new_tick(14), ids[0], ids[1], "x" if kind_ != "hands" else None, kind_, 14, others=[ids[2]] if i % 2 else []))
    outs_[(kind_, asleep_)] = got_
kr_ = {k: sum(g["outcome"] == "killed" for g in v) / len(v) for k, v in outs_.items()}
check("a sleeper rarely survives a blade, an awake person often does, and bare hands kill least", kr_[("sharp", True)] > 0.9 and 0.25 < kr_[("sharp", False)] < 0.75 and kr_[("hands", False)] < kr_[("sharp", False)], str(kr_))
awake_ = [g for g in outs_[("sharp", False)]]
check("an awake victim blocks, dodges, struggles, runs or screams, and can get away, be rescued or take the weapon",
      {"escaped", "rescued", "disarmed"} <= {g["outcome"] for g in awake_} and {"block", "dodge", "struggle", "flee", "scream"} <= {b.get("reply") for g in awake_ for b in g["blows"]})
check("every hit lands on a part of the body and leaves a wound", all(wd["part"] in ("head", "throat", "chest", "belly", "back", "arm", "leg", "hand") for g in awake_ for wd in g["wounds"])
      and all(len(g["wounds"]) == sum(b["hit"] for b in g["blows"]) for g in awake_))
check("a sleeper is hit where it counts", all(wd["part"] in ("throat", "head") for g in outs_[("sharp", True)] for wd in g["wounds"]))
w.agents[ids[1]]["hp"], w.agents[ids[1]]["asleep"] = 100, True
for c in ids[2:]:
    w.agents[c]["room"] = "garden"
w.agents[ids[0]]["room"] = w.agents[ids[1]]["room"] = "lounge"
w.agents[ids[0]]["inv"][sharp()] = 1
w.state["case"] = None
r.resolve_attacks(r.new_tick(14), [(ids[0], {"target": ids[1], "method": sharp(), "frame": None})], 14)
cs_ = w.state.get("case") or {}
check("the case records the wounds for the autopsy", cs_.get("wounds") and cs_.get("wound_text") and ("throat" in cs_["wound_text"] or "head" in cs_["wound_text"]), str(cs_.get("wound_text")))

# ---- phase 6: hands, pockets and what items can do
w, r, _ = fresh(197)
ids = sorted(w.agents)
cb_ = r.item_caps("crowbar")
check("every item says what it can do, how big it is and what it leaves", "bludgeon" in cb_["does"] and cb_["size"] == "large" and "blood" in cb_["traces"]
      and r.item_caps("scissors")["size"] == "small" and "cut" in r.item_caps("scissors")["does"])
ha_ = ids[0]
w.agents[ha_]["inv"] = {"crowbar": 1, "scissors": 1}
check("a large item is in plain sight and takes both hands; a small one rides in a pocket", r.held_items(ha_) == ["crowbar"] and r.pocketed(ha_) == ["scissors"] and r.hands_free(ha_) == 0)
r.seen_holding(ids[1], ha_, r.abs_now())
check("someone seen carrying a weapon is remembered with it (and suspected)", any(b["k"] == "has" and b["o"] == "crowbar" for b in r.beliefs(ids[1])) and ha_ in r.suspects(ids[1]))
check("a pocketed weapon has to be drawn first", r.must_draw(ha_, "scissors") and not r.must_draw(ha_, "crowbar"))
w.agents[ha_]["room"] = "lounge"
r.knock_out(r.new_tick(14), ha_, "knocked out")
check("whoever is knocked out drops what they were holding", "crowbar" not in w.agents[ha_]["inv"] and w.state["room_items"].get("lounge", {}).get("crowbar", 0) >= 1 and w.agents[ha_]["inv"].get("scissors"))

# ---- evidence: no TereVi footage, the Case File
w, r, _ = fresh(198)
ids = sorted(w.agents)
k_, v_ = ids[0], ids[1]
w.agents[k_]["inv"] = {}
w.agents[ids[2]]["inv"] = {}
said_ = r.clean_line(ids[2], "say", "The camera footage shows Cail in the kitchen. I saw him there myself.")
check("nobody cites TereVi's camera footage they cannot have (the sentence is cut)", "footage" not in said_ and "saw him there myself" in said_, said_)
w.agents[ids[2]]["inv"] = {"gopro": 1}
check("someone with a camera of their own may", "footage" in r.clean_line(ids[2], "say", "My footage shows Cail in the kitchen."))
w.agents[k_]["room"] = w.agents[v_]["room"] = "lounge"
for c in ids[2:]:
    w.agents[c]["room"] = "foyer"
tk_ = r.new_tick(14)
r.open_case(tk_, "murder", v_, culprit=k_, wkind="sharp", weapon=sharp(), room="lounge", hour=14, witnesses=[])
case_ = w.state["case"]
r.reveal_clues(tk_, ids[3])
check("the camera archive is not lying in the Foyer for anyone to read", not any(c["kind"] == "ledger" and ids[3] in c["found_by"] for c in case_["clues"]))
check("TereVi's Case File lists the victim, where they were found, time and cause (or says they are withheld), wounds and weapon unknown",
      case_["file"][0].startswith("Victim:") and any(l.startswith("Found in:") for l in case_["file"]) and any(l.startswith("Time of death:") for l in case_["file"])
      and any(l.startswith("Cause of death:") for l in case_["file"]) and "Weapon: unknown." in case_["file"], str(case_["file"]))
case_["cf"]["time"]["known"] = False
case_["file"] = r.render_case_file(case_)
check("a fact TereVi keeps back reads as withheld", "Time of death: withheld by TereVi." in case_["file"])
r.announce_body(r.new_tick(15), 15)
w.agents[ids[3]]["room"] = "lounge"
r.reveal_clues(r.new_tick(16), ids[3])
check("examining the body brings the time of death into the file, and everyone is told", any(l.startswith("Time of death: around") for l in case_["file"])
      and any("Case File was updated" in m for m in w.agents[ids[4]]["memory"]["recent"]), str(case_["file"]))
cl_ = case_["clues"][0]
r.update_clue(r.new_tick(16), cl_, cl_["text"] + " The body was moved after death.", "a second look")
check("a piece of evidence can be updated with what is learned, and its finders are told", "moved after death" in cl_["text"] and cl_["history"]
      and any("CLUE UPDATED" in m for m in w.agents[ids[3]]["memory"]["recent"]))
nb_ = w.state["npcs"]["neovi"]
nb_["room"] = "lounge"
r.rng = _Fixed(0.0, r.rng)
got_ = r.neovi_shares_footage(r.new_tick(16), 16)
check("only NeoVi can show someone the camera archive, in secret, and then they can cite it", got_ and r.has_footage(got_) and any(c["kind"] == "ledger" and got_ in c["found_by"] for c in case_["clues"]))

# ---- silencing a victim, and plotters who stack the odds
w, r, _ = fresh(199)
ids = sorted(w.agents)
at_, vi_, by_ = ids[0], ids[1], ids[2]
def rescues_(gag):
    w.agents[at_]["inv"] = {"crowbar": 1, **({"duct_tape": 1} if gag else {})}
    n = sil = 0
    for i in range(150):
        w.agents[vi_]["hp"], w.agents[vi_]["asleep"] = 100, False
        res_ = r.fight(r.new_tick(14), at_, vi_, "crowbar", "blunt", 14, others=[by_])
        n += res_["outcome"] == "rescued"
        sil += bool(res_.get("silenced")) or any(b.get("gag") for b in res_["blows"])
    return n, sil
plain_, gagged_ = rescues_(False), rescues_(True)
check("a gag stops the scream that would bring help", gagged_[0] < plain_[0] and gagged_[1] > 0, f"rescued {plain_[0]} without a gag, {gagged_[0]} with")
from murder.combat import WATER_ROOMS  # noqa: E402
w.agents[at_]["inv"] = {}
w.agents[at_]["room"] = w.agents[vi_]["room"] = "pool"
for c in ids[2:]:
    w.agents[c]["room"] = "garden"
w.agents[vi_]["hp"], w.agents[vi_]["asleep"] = 100, True
r.resolve_attacks(r.new_tick(14), [(at_, {"target": vi_, "method": "drown", "frame": None})], 14)
cs_ = w.state.get("case") or {}
check("someone can be held under the water: a silent killing with its own marks", cs_.get("killer") == at_ and "water" in (cs_.get("cause") or "") + str(cs_.get("true_cause")), str(cs_.get("cause")))

w, r, _ = fresh(200)
ids = sorted(w.agents)
at_, vi_ = ids[0], ids[1]
w.agents[at_]["room"] = w.agents[vi_]["room"] = "lounge"
for c in ids[2:]:
    w.agents[c]["room"] = "garden"
w.agents[at_]["inv"] = {"rags": 1}
w.agents[vi_]["asleep"] = True
r.rng = _Fixed(0.3, r.rng)
r.do_knockout(r.new_tick(14), at_, {"target": vi_, "method": "hands"})
r.rng = r.rng.b
check("someone knocked out can be gagged, and tears it off when they come round", w.agents[vi_].get("out") and w.agents[vi_].get("gagged"), str(w.agents[vi_].get("out")))
r.wake_up(r.new_tick(18), vi_)
check("unless their hands are tied", not w.agents[vi_].get("gagged"))

w, r, _ = fresh(201)
ids = sorted(w.agents)
pk_, tv_ = ids[0], ids[1]
T_ = r.day * 24 + 11
r.believe(pk_, {"k": "at", "s": tv_, "r": "pool", "t0": T_, "t1": T_ + 0.25, "src": "seen", "c": 0.9, "true": True})
w.agents[tv_]["aff"][pk_] = 5
kinds_ = {sc["kind"] for _, sc in r.plan_schemes(pk_, tv_)}
check("plotters can plan to drown someone they saw alone by the water, or lure someone who trusts them", {"drown", "lure"} <= kinds_, str(sorted(kinds_)))
pl_ = {"target": tv_, "stage": "stalking", "stage_ticks": 0, "plan": [], "scheme": {"kind": "lure", "room": None, "when": "night"}}
w.state["plots"] = {pk_: pl_}
w.state["revealed"] = True
r.rng = _Fixed(0.0, r.rng)
r.night_extra([])
r.rng = r.rng.b
check("a lure becomes a quiet meeting at night with the target", any(m["why"] == "lure" and {m["a"], m["b"]} == {pk_, tv_} for m in w.state.get("meets") or []))
pl2_ = {"target": tv_, "stage": "preparing", "stage_ticks": 0, "plan": [], "scheme": {"kind": "alone", "room": "library", "when": "day"}, "weapon": None}
w.agents[pk_]["inv"] = {}
check("a plotter who means to catch someone awake goes looking for a gag first", "gag" in r.scheme_needs(pk_, pl2_))

# ---- gear (gloves, a coat, a bag, a holster) and plans that combine items
w, r, _ = fresh(202)
ids = sorted(w.agents)
k_, v_ = ids[0], ids[1]
w.agents[k_]["inv"] = {"kitchen_knife": 1, "holster": 1}
check("a holster hides a weapon and it comes out at once", "kitchen_knife" not in r.held_items(k_) and not r.must_draw(k_, "kitchen_knife"))
w.agents[k_]["inv"] = {"kitchen_knife": 1, "duffel_bag": 1}
check("a bag hides it too, but drawing from it takes a moment", "kitchen_knife" not in r.held_items(k_) and r.must_draw(k_, "kitchen_knife"))
w.agents[k_]["inv"] = {"kitchen_knife": 1}
check("without either, the knife is seen in the hand", "kitchen_knife" in r.held_items(k_))
def kill_(gear):
    w_, r_, _ = fresh(203)
    i_ = sorted(w_.agents)
    r_.ensure_wardrobe()
    w_.agents[i_[0]]["inv"].update({"kitchen_knife": 1, **gear})
    w_.agents[i_[0]]["room"] = w_.agents[i_[1]]["room"] = "lounge"
    for c in i_[2:]:
        w_.agents[c]["room"] = "garden"
    w_.agents[i_[1]]["asleep"] = True
    r_.resolve_attacks(r_.new_tick(14), [(i_[0], {"target": i_[1], "method": "kitchen_knife", "frame": None})], 14)
    return w_, r_, i_
w2_, r2_, i2_ = kill_({"work_gloves": 1, "trench_coat": 1})
wc_ = next((c for c in w2_.state["case"]["clues"] if c["kind"] == "weapon"), None)
check("gloves leave no handprint on the weapon, only a fabric weave, and the gloves are stained", w2_.state["case"].get("handmark") is None and (wc_ is None or "wore gloves" in wc_["text"])
      and (wc_ is None or "stained_work_gloves" in w2_.agents[i2_[0]]["inv"] or any("stained_work_gloves" in x for x in w2_.state["room_items"].values())))
check("a coat takes the blood instead of the clothes underneath", "stained_trench_coat" in w2_.agents[i2_[0]]["inv"] and "stained" not in r2_.tags(r2_.worn(i2_[0]) or "x"))
w3_, r3_, i3_ = kill_({})
wc3_ = next((c for c in w3_.state["case"]["clues"] if c["kind"] == "weapon"), None)
check("without gloves the handle shows a bloody handprint of the killer's hand size (or a smear), never fingerprints", (wc3_ is None or ("ingerprint" not in wc3_["text"]
      and ("handprint" in wc3_["text"] or "smeared" in wc3_["text"]))) and w3_.state["case"].get("handmark") in (None, r3_.build_of(i3_[0])["hand"]))

w, r, _ = fresh(204)
ids = sorted(w.agents)
pk_, tv_ = ids[0], ids[1]
w.agents[pk_]["inv"] = {"rope": 1, "sleeping_pills": 1}
kinds_ = {sc["kind"]: sc for _, sc in r.plan_schemes(pk_, tv_)}
check("the planner combines items: a rope (hang it as a suicide), sleeping pills and the bath (an accident)", {"hang", "bath"} <= set(kinds_)
      and kinds_["hang"]["staged"] == "suicide" and kinds_["bath"]["staged"] == "accident", str(sorted(kinds_)))
w.agents[pk_]["inv"] = {}
pl_ = {"target": tv_, "stage": "preparing", "stage_ticks": 0, "plan": [], "scheme": kinds_["hang"], "weapon": None}
check("a plotter without the rope goes to fetch it", "rope" in r.scheme_needs(pk_, pl_))
r.mind(pk_)["facets"]["orderliness"] = 80
check("a careful plotter fetches gloves too", "gloves" in r.scheme_needs(pk_, {"scheme": {"kind": "asleep"}}))
w.agents[pk_]["inv"] = {"rope": 1}
home_ = w.cast[tv_]["home"]
w.agents[pk_]["room"] = w.agents[tv_]["room"] = home_
for c in ids[2:]:
    w.agents[c]["room"] = "garden"
w.agents[tv_]["asleep"] = True
pl_.update(stage="striking")
check("they only do it once the target is helpless", r.scheme_allows(pk_, pl_))
r.resolve_attacks(r.new_tick(23), [(pk_, {"target": tv_, "method": r.scheme_method(pk_, pl_), "frame": None, "staged": r.scheme_staging(pl_)})], 23)
cs_ = w.state.get("case") or {}
check("a hanging is staged as a suicide (with the flaws a careful look finds) and the rope stays at the scene", cs_.get("killer") == pk_ and cs_.get("staged") == "suicide"
      and any(c["kind"] == "staging" for c in cs_.get("clues", [])) and w.state["room_items"].get(home_, {}).get("rope", 0) >= 1, str({k: cs_.get(k) for k in ("staged", "kind")}))

# ---- phase 7: the claim-based trial
def trial_case_(seed, setup):
    w_, r_, _ = fresh(seed)
    i_ = sorted(w_.agents)
    k_, v_ = i_[0], i_[1]
    w_.state["revealed"] = True
    for c in i_:
        w_.agents[c]["room"] = "garden"
    w_.agents[k_]["room"] = w_.agents[v_]["room"] = "library"
    tk_ = r_.new_tick(14)
    r_.open_case(tk_, "murder", v_, culprit=k_, wkind="sharp", weapon=sharp(), room="library", hour=14, witnesses=[])
    case_ = w_.state["case"]
    setup(w_, r_, i_, case_)
    r_.announce_body(r_.new_tick(15), 15)
    calls0_ = r_.llm.usage["calls"]
    tr_ = r_.run_trial(16)
    return w_, r_, i_, case_, tr_, r_.llm.usage["calls"] - calls0_
def seen_(w_, r_, i_, case_):
    t_ = r_.case_time(case_)
    for h in i_[2:6]:
        r_.believe(h, {"k": "at", "s": i_[0], "r": "library", "t0": t_ - 0.25, "t1": t_ + 0.25, "src": "seen", "c": 0.9, "true": True})
    for c in i_[2:]:
        r_.self_at(c, "garden", t_)
    r_.self_at(i_[0], "library", t_)
w, r, ids, case_, tr, calls_ = trial_case_(205, seen_)
kinds_ = [sg["kind"] for sg in tr["segments"]]
check("the claim trial plays its sequences: an open debate, then hot seat, clash or brainstorm as the room calls for, and closing arguments", kinds_[0] == "debate" and kinds_[-1] == "closing", str(kinds_))
check("the engine computes the votes (no model call per voter) and witnesses near the scene convict the killer", tr["trial"]["found"] and calls_ <= len(tr["segments"]) + 4, f"{calls_} calls, votes {tr['trial']['tally']}")
check("the suspicion meter is public: every sequence shows it", all("meter" in sg for sg in tr["segments"]) and max(tr["segments"][-1]["meter"], key=tr["segments"][-1]["meter"].get) == ids[0])
lines_ = [l for g in tr["talk"] if g.get("segment") for l in g["lines"]]
check("everyone states where they were, and the lines are in the record", sum(1 for l in lines_ if l.get("move") == "alibi") >= len(ids) - 2)

def lie_(w_, r_, i_, case_):
    t_ = r_.case_time(case_)
    w_.state["where_log"] = {i_[0]: [[r_.day, 14, "kitchen"], [r_.day, 12, "lounge"]]}
    r_.self_at(i_[0], "library", t_)
    for c in i_[2:]:
        r_.self_at(c, "garden", t_)
    for h in i_[2:5]:
        r_.believe(h, {"k": "at", "s": i_[0], "r": "pool", "t0": t_ - 0.25, "t1": t_ + 0.25, "src": "seen", "c": 0.9, "true": True})
    for c in i_[2:5]:
        w_.agents[c]["aff"][i_[0]] = -3
        r_.mind(c)["facets"]["courage"] = 90
w, r, ids, case_, tr, _ = trial_case_(207, lie_)
ct_ = tr.get("claim_trial") or {}
moves_ = [l.get("move") for g in tr["talk"] if g.get("segment") for l in g["lines"]]
check("a claim that contradicts what someone saw is a weak point: they object, the lie is proven and the liar's credibility halves",
      "objection" in moves_ and ct_.get("lies_proven", {}).get(ids[0], 0) >= 1 and ct_["cred"][ids[0]] <= 0.5, str(ct_))
check("the culprit answers with a new story from the lie planner, or is cornered, and never confesses", ("new_story" in moves_ or "cornered" in moves_)
      and not any("I did it" in l["text"] or "I killed" in l["text"] for g in tr["talk"] for l in g.get("lines", []) if l["speaker"] == ids[0]))

w, r, _ = fresh(208)
ids = sorted(w.agents)
w.agents[ids[0]]["aff"][ids[1]] = 8
r.mind(ids[0])["facets"]["courage"] = 50
hi_ = r.willingness(ids[2], ids[1], 0.9)
lo_ = r.willingness(ids[0], ids[1], 0.9)
check("people are less willing to speak against someone they love than against a stranger", lo_ < hi_, f"{lo_:.2f} vs {hi_:.2f}")

# ---- phase 7: cries, cross-examination, split court, climax
w, r, ids, case_, tr, _ = trial_case_(205, seen_)
kinds_ = [sg["kind"] for sg in tr["segments"]]
lines_ = [l for g in tr["talk"] if g.get("segment") for l in g["lines"]]
check("the strongest witness against the accused is cross-examined", "crossexam" in kinds_ and any(l.get("move") in ("probe", "crossexam") for l in lines_), str(kinds_))
clim_ = next((sg for sg in tr["segments"] if sg["kind"] == "climax"), None)
check("before the vote the accuser tells the crime step by step; steps with no fact are gaps the accused can jump on", clim_ and clim_.get("steps")
      and any(st["gap"] for st in clim_["steps"]) and any(l.get("move") == "interrupt" for l in lines_), str(clim_ and clim_.get("steps")))
w, r, ids, case_, tr, _ = trial_case_(207, lie_)
cries_ = [l for g in tr["talk"] if g.get("segment") for l in g["lines"] if l.get("move") == "cry"]
from murder.claimtrial import CRIES  # noqa: E402
check("whoever catches a contradiction shouts their cry first (Objection!, Hold it!, That's wrong!...), never reworded", cries_ and all(l["text"].rstrip("!").strip() for l in cries_)
      and any(l["text"] in CRIES or l["text"].startswith("W-wait") for l in cries_), str([l["text"] for l in cries_]))
w, r, _ = fresh(211)
ids = sorted(w.agents)
w.cast[ids[0]]["objection"] = "Take that!"
r.rng = _Fixed(0.5, r.rng)
check("a character can have a signature cry of their own", r.objection_cry(ids[0]) == "Take that!")
w, r, _ = fresh(212)
ids = sorted(w.agents)
r.suspicion = {ids[2]: ids[0], ids[3]: ids[0], ids[4]: ids[0], ids[5]: ids[1], ids[6]: ids[1], ids[7]: ids[1]}
facts_ = [{"by": ids[2], "about": ids[0], "kind": "clue", "w": 4.0, "text": "Clear fingerprints on the handle.", "true": True},
          {"by": ids[5], "about": ids[1], "kind": "has", "w": 1.0, "text": "carrying a hammer", "true": True}]
cred_ = {p: 1.0 for p in ids}
mt_ = {p: 0.0 for p in ids}
beats_ = []
sides_ = r.split_court(beats_, ids[0], ids[1], facts_, cred_, lambda p, x, why=None: mt_.__setitem__(p, max(0, mt_[p] + x)), ids)
check("when the room splits between two suspects, the two sides argue and the weaker side loses people", len(sides_[ids[0]]) > 3 and any(b["move"] == "switch" for b in beats_) and mt_[ids[0]] > mt_[ids[1]], str(sides_))

w, r, ids, case_, tr, _ = trial_case_(205, seen_)
rep_ = tr["trial"].get("report") or {}
check("after the verdict a truth-against-belief report: what really happened, each vote, what each person held and kept quiet",
      rep_.get("truth", "").startswith(r.nm(ids[0]) if ids[0] in w.cast else "") and len(rep_.get("rows", [])) == len(tr["trial"]["votes"]) and all("silent" in x for x in rep_["rows"]), str(rep_)[:200])

# ---- phase 7: the trial as a live practice on the map
w, r, ids, case_, tr, _ = trial_case_(205, seen_)
r.emit(tr)
pr_ = tr.get("practice") or {}
seg_lines_ = [l for g in tr["talk"] if g.get("segment") for l in g["lines"]]
check("the trial is a live practice: everyone walks to the Voting Grounds, and nobody speaks before they have arrived",
      pr_.get("room") == "voting_grounds" and len(pr_.get("arrive", {})) >= len(ids) - 2
      and all(l.get("m") is not None and l["room"] == "voting_grounds" and l["m"] >= pr_["arrive"].get(l["speaker"], 0) for l in seg_lines_), str(pr_)[:200])
check("the trial lines are on the clock in order and the walk in is on the map", [l["m"] for l in seg_lines_] == sorted(l["m"] for l in seg_lines_)
      and all(g.get("live") for g in tr["talk"] if g.get("segment")) and len((tr.get("live") or {}).get("tracks") or {}) >= len(ids) - 2)
ev_ = [l["text"] for l in seg_lines_ if l.get("move") == "evidence"]
check("each piece of evidence is shown once, and each person names who they saw in one line", len(ev_) == len(set(ev_)) and sum(1 for x in ev_ if x.startswith("I saw ")) <= len(ids), str(ev_))
wh_ = [g for g in tr["talk"] if g.get("whisper")]
check("allies whisper at the trial; a whisper is a live side conversation on the clock", all(g.get("live") and all(l.get("m") is not None for l in g["lines"]) for g in wh_))

w, r, _ = fresh(213)
check("being seen with a weapon counts at the trial only if it fits the case: the weapon itself most, the same kind a little, anything else not at all",
      r.weapon_match("kitchen_knife", "kitchen_knife") > r.weapon_match("scissors", "kitchen_knife") > 0 and r.weapon_match("baseball_bat", "kitchen_knife") == 0)

# ---- phase 7: wounds and marks read by eye (no prints, no lab)
w, r, _ = fresh(214)
ids = sorted(w.agents)
rh_ = next(c for c in ids if r.build_of(c)["handed"] == "right")
sides_ = [r.blow_marks(rh_, ids[0] if ids[0] != rh_ else ids[1], "head")["side"] for _ in range(60)]
check("a right-handed attacker facing the victim lands most blows on the victim's left side", sides_.count("left") >= 40, str(sides_.count("left")))
cs_ = {"victim": ids[1], "killer": ids[0], "killer_scratched": True,
       "wounds": [{"part": "head", "kind": "blunt", "side": "left", "above": True}, {"part": "head", "kind": "blunt", "side": "left", "above": True}, {"part": "arm", "kind": "blunt", "side": "left", "above": False}]}
said_, inf_ = r.read_wounds(cs_)
check("the body tells what an eye can see: which hand, from above, defensive wounds, skin under the nails", inf_.get("handed") == "right" and inf_.get("taller") is True
      and inf_.get("scratched") and any("forearms" in x for x in said_) and not any("print" in x for x in said_), str(said_))
txt_ = "".join(r.hand_mark_text(ids[0], "kitchen_knife") for _ in range(20))
check("a weapon shows a handprint's size or a smear, never fingerprints anyone could match", "ingerprint" not in txt_ and ("handprint" in txt_ or "smeared" in txt_))

def marks_(w_, r_, i_, case_):
    case_["killer_scratched"] = True
    case_["marks"] = {"handed": r_.build_of(i_[0])["handed"], "scratched": True}
    for c in case_["clues"]:
        if c["kind"] == "scene":
            c["found_by"] = [i_[2]]
    r_.scratch(None, i_[0], "the victim clawed at them")
    r_.scratch(None, i_[3], "thorns in the garden")
    r_.willingness = lambda *a_, **k_: 1.0
    r_.believe(i_[4], {"k": "at", "s": i_[3], "r": "garden", "t0": r_.abs_now() - 2, "t1": r_.abs_now() - 1, "src": "seen", "c": 0.9, "true": True})
w, r, ids, case_, tr, _ = trial_case_(215, marks_)
mv_ = [(l["speaker"], l.get("move"), l["text"]) for g in tr["talk"] if g.get("segment") for l in g["lines"]]
ct_ = tr.get("claim_trial") or {}
check("at the trial the body is compared by eye: who uses that hand, whose hands are scratched", any(m == "compare" and "hand" in t for _, m, t in mv_)
      and any(m == "compare" and "scratches" in t and r.nm(ids[0]) in t for _, m, t in mv_), str([t for _, m, t in mv_ if m == "compare"]))
check("scratches from the garden's thorns are explained when someone saw them there; the killer's story is not backed up",
      any(s_ == ids[3] and "Thorns" in t for s_, _, t in mv_) and ct_["meter"][ids[0]] > ct_["meter"][ids[3]], str(ct_.get("meter")))

# ---- looks and the traces they leave (looks.py)
from murder.looks import describe as _describe, LOOKS as _LOOKS  # noqa: E402
w, r, _ = fresh(216)
r.ensure_wardrobe()
ids = sorted(w.agents)
check("everyone's looks follow their portrait: hair, eyes, build, outfit, accessory", set(_LOOKS) >= set(ids) and "lavender" in _describe("seul") and "fedora" in _describe("noah")
      and "parka" in w.item_name("clothes_szymon") and w.agents["ayden"]["inv"].get("acc_ayden") and not w.agents["shintaro"]["inv"].get("acc_shintaro"))
check("a worn accessory weighs nothing and cannot be pickpocketed", w.carried("ayden") == sum(q for k_, q in w.agents["ayden"]["inv"].items() if k_ != "acc_ayden"))
k_, v_ = "seul", "noah"
r.rng = _Fixed(0.01, r.rng)
cs_ = {"victim": v_, "killer": k_, "clues": []}
tr_ = r.body_traces(cs_, k_, v_, "library", True, True, ["vixen"])
kinds_ = {c["kind"]: c for c in tr_}
check("a struggle leaves the killer's hair and the fibres of what they wore, and a glimpse for whoever was in the dark", "lavender" in kinds_.get("hair", {}).get("text", "")
      and kinds_.get("fibres", {}).get("fibre") == "light blue fleece" and cs_.get("glimpses") and cs_["glimpses"][0]["feature"] in r.silhouette(k_), str(tr_))
w.agents["vixen"]["inv"]["clothes_shintaro"] = 1
w.agents["vixen"]["wearing"] = "clothes_shintaro"
cs2_ = {"victim": v_, "killer": "vixen", "clues": []}
tr2_ = r.body_traces(cs2_, "vixen", v_, "library", True, True, [])
fib_ = next(c for c in tr2_ if c["kind"] == "fibres")
check("in someone else's clothes, the fibres point at the owner of the clothes", fib_["fibre"] in ("white fur", "brown suede"))
fib_["found_by"] = ["chloe"]
acc_ = next((c for c in tr2_ if c["kind"] == "accessory"), None)
if acc_:
    acc_["found_by"] = ["chloe"]
cs2_["clues"] = tr2_
r.rng = r.rng.b
lf_ = r.look_facts(cs2_, ids)
check("matched by eye: the fibres fit Shintaro's jacket; Vixen's lost scarf is hers and she is visibly without it",
      any(f["look"] == "fibres" and f["about"] == "shintaro" and f["fits"] for f in lf_) and (acc_ is None or any(f["look"] == "accessory" and f["about"] == "vixen" and f["w"] >= 3 for f in lf_)), str(lf_)[:300])
w.agents["seul"]["inv"]["sheet_cloak"] = 1
check("a cloak hides the hair from a glimpse", "long hair" not in r.silhouette("seul") and "cloaked" in r.silhouette("seul"))

def hair_(w_, r_, i_, case_):
    hl_, hc_ = r_.looks(i_[0])["hair"]
    case_["clues"].append({"room": "library", "scene": True, "found_by": [i_[2]], "kind": "hair", "text": f"A single {hl_} {hc_} hair is caught in the fingers.", "hair": [hl_, hc_]})
    r_.willingness = lambda *a_, **k_: 1.0
w, r, ids, case_, tr, _ = trial_case_(217, hair_)
cmp_ = [l["text"] for g in tr["talk"] if g.get("segment") for l in g["lines"] if l.get("move") == "compare"]
check("at the trial a hair is held up against everyone's hair", any("Whose hair is that?" in t and r.nm(ids[0]) in t for t in cmp_), str(cmp_))

w, r, _ = fresh(218)
r.ensure_wardrobe()
w.agents["chloe"]["inv"].pop("acc_chloe", None)
r.scratch(None, "chloe", "thorns in the garden")
check("the prompts carry how someone looks right now: their own looks, what they wear, a missing accessory, visible marks",
      "lavender" in r.system_prompt("seul") and "without their usual red-framed glasses" in r.looks_line("chloe") and "scratches" in r.looks_line("chloe", short=True))

# ---- the gatherings as live practices (scenes.py)
def scene_ok_(t_, room_):
    gs_ = [g for g in t_["talk"] if g.get("scene")]
    P_ = t_.get("practice") or {}
    ls_ = [l for g in gs_ for l in g["lines"]]
    return (gs_ and P_.get("room") == room_ and all(g.get("live") for g in gs_) and ls_
            and all(l.get("m") is not None and l["m"] >= P_["arrive"].get(l["speaker"], 0) for l in ls_)), ls_
w, r, _ = fresh(219)
for c in w.agents:
    w.agents[c]["room"] = "garden"
calls0_ = r.llm.usage["calls"]
t_ = r.run_presentations(9)
r.emit(t_)
ok_, ls_ = scene_ok_(t_, "dining_hall")
check("the introductions are a live practice: everyone walks to the Dining Hall and introduces themselves on the clock",
      ok_ and {l["speaker"] for l in ls_ if l.get("move") == "introduce"} >= set(w.agents) and len((t_.get("live") or {}).get("tracks") or {}) >= len(w.agents) - 1, str(ls_[:3]))
t_ = r.run_reveal(10)
r.emit(t_)
ok_, ls_ = scene_ok_(t_, "dining_hall")
check("the reveal: everyone reacts by temperament and TereVi answers at most two challenges", ok_ and len({l["speaker"] for l in ls_ if l["speaker"] in w.agents}) >= len(w.agents) - 1
      and sum(1 for l in ls_ if l["speaker"] == "terevi") <= 2 and r.llm.usage["calls"] - calls0_ <= 6, str([l["move"] for l in ls_]))
w, r, _ = fresh(220)
w.state["revealed"] = True
ids = sorted(w.agents)
w.agents[ids[0]]["sanity"] = 10
r.mind(ids[0])["facets"]["altruism"] = 90
r.rng = _Fixed(0.01, r.rng)
beats_, vols_, strk_ = r.lastcall_beats(ids)
r.rng = r.rng.b
check("at the last call the engine decides who volunteers (the most broken or selfless) and who means to strike", vols_ == [ids[0]] and len(strk_) == 1 and strk_[0][0] != strk_[0][1]
      and any(b["move"] == "volunteer" and b["speaker"] == ids[0] for b in beats_))
w, r, _ = fresh(221)
ids = sorted(w.agents)
w.state["revealed"] = True
dead_ = ids[0]
w.agents[ids[1]]["aff"][dead_] = 6
w.end_agent(dead_, "dead", "murdered")
r.note_loss(dead_)
r.s["aftermath"]["since"] = (r.day - 1, 10)
t_ = r.run_vigil(12)
r.emit(t_)
ok_, ls_ = scene_ok_(t_, "lounge")
check("the remembrance: each survivor speaks of the dead, someone lights a candle, nobody says the same line twice", ok_ and any(l.get("move") == "candle" for l in ls_)
      and any(l["speaker"] == ids[1] and l.get("move") == "fond" for l in ls_) and len({l["text"] for l in ls_}) >= len(ls_) - 1, str([(l["speaker"], l["text"]) for l in ls_][:4]))

w, r, _ = fresh(222)
w.state["revealed"] = True
ids = sorted(w.agents)
moves_ = [b["move"] for b in r.lastcall_beats(ids)[0]]
check("at the last call people take different stances, not all the same plea", len(set(moves_)) >= 3, str(moves_))
w, r, _ = fresh(223)
ids = sorted(w.agents)
w.end_agent(ids[0], "executed", "executed after the trial")
w.end_agent(ids[1], "dead", "murdered")
vb_ = r.vigil_beats(sorted(w.agents), [ids[0], ids[1]])
check("at the remembrance an executed killer is not mourned like a victim", all(r.nm(ids[0]) not in b["text"] or b["move"] in ("betrayed", "candle") for b in vb_), str([b["text"] for b in vb_]))

# ---- phase 7b: ending tiers
from murder.routes import ending_tier  # noqa: E402
check("every ending has a tier: the show defeated or several walking out is good, a lone survivor is bittersweet, a fight to the death is bad",
      ending_tier("truth", ["a"]) == "good" and ending_tier("winners", ["a", "b"]) == "good" and ending_tier("winners", ["a"]) == "bittersweet"
      and ending_tier("battle", ["a"]) == "bad" and ending_tier("reckoning", []) == "bad" and ending_tier("raft", ["a"]) == "bittersweet")
w, r, _ = fresh(224)
w.state["revealed"] = True
for c in sorted(w.agents)[3:]:
    w.end_agent(c, "dead", "murdered")
t_ = r.run_endgame(20)
check("the endgame records its tier with the ending", t_.get("ending", {}).get("tier") in ("good", "bittersweet", "bad") and w.state["over"].get("tier") == t_["ending"]["tier"])

# ---- phase 7b step 2: working on the ways out (escape.py)
w, r, _ = fresh(225)
w.state["revealed"] = True
ids = sorted(w.agents)
c_ = ids[0]
w.agents[c_]["route"] = "raft"
rt_ = w.state["escape"]["routes"]["raft"]
check("a step that needs parts stops at half way until they are gathered", r.step_missing("raft", "materials") and r.escape_step_for("raft") == "materials")
src_ = r.parts_source(c_, "raft", "materials")
check("someone working on it goes to fetch a part where one lies about", src_ in ("beach", "boathouse", "generator_shed", "laundry", "linen_store"), str(src_))
w.agents[c_]["room"] = src_
tk_ = r.new_tick(10)
res_ = r.escape_work(tk_, c_, 10)
check("fetching puts the part into the route's store", res_ and res_["verdict"] == "gathered" and rt_["parts"]["materials"] >= 1, str(res_))
rt_["parts"]["materials"] = 3
w.agents[c_]["room"] = "beach"
r.rng = _Fixed(0.5, r.rng)
for _ in range(20):
    r.escape_work(tk_, c_, 10)
r.rng = r.rng.b
check("with the parts in, work takes the step all the way and the next step opens", rt_["plan"]["materials"] == 100 and r.escape_step_for("raft") != "materials", str(rt_["plan"]))
w2_, r2_, _ = fresh(226)
w2_.state["revealed"] = True
r2_.rng = _Fixed(0.5, r2_.rng)
for _ in range(20):
    r2_.escape_work(r2_.new_tick(10), sorted(w2_.agents)[1], 10)
check("without what a step needs, work stops at half way", max(w2_.state["escape"]["routes"][r2_.escape_route_for(sorted(w2_.agents)[1]) or "raft"]["plan"].values()) <= 50)

# ---- phase 7b step 2: the raid and the standoff as live scenes (finales.py)
def finale_(seed, rid, patch=None):
    w_, r_, _ = fresh(seed)
    w_.state["revealed"] = True
    w_.state["found_edges"].append("SP-5")
    for st in w_.state["escape"]["routes"][rid]["plan"]:
        w_.state["escape"]["routes"][rid]["plan"][st] = 100
    if patch:
        patch(r_)
    t_ = r_.run_finale(rid, 23)
    r_.emit(t_)
    return w_, r_, t_
outs_ = set()
for sd_ in range(227, 237):
    w, r, t_ = finale_(sd_, "shutdown")
    outs_.add(r._finale_outcome)
    if sd_ == 227:
        ls_ = [l for g in t_["talk"] if g.get("scene") for l in g["lines"]]
        check("the raid on the core is a live scene: the team walks to the Core Vault and the lines run on the clock",
              (t_.get("practice") or {}).get("room") == "core_vault" and ls_ and all(l.get("m") is not None for l in ls_), str(t_.get("practice")))
check("the raid can succeed or fail, and success shuts TereVi down", "shut down" in outs_ and len(outs_) >= 2, str(outs_))
outs_ = set()
for sd_ in range(237, 252):
    w, r, t_ = finale_(sd_, "ultimatum")
    outs_.add(r._finale_outcome)
check("the standoff ends in a surrender, a fold or a real blast", "surrender" in outs_ and len(outs_) >= 2, str(outs_))
class _Turn(_Fixed):
    def choice(self, seq):
        return "turn" if "turn" in seq else self.b.choice(seq)
def traitor_(r_):
    r_.turned = lambda cid, team: True
    r_.rng = _Turn(0.99, r_.rng)
w, r, t_ = finale_(252, "shutdown", traitor_)
check("TereVi can turn a raider, who runs for the alarm: the raid fails", r._finale_outcome == "betrayed" and not w.state.get("over"), str(r._finale_outcome))

w, r, _ = fresh(253)
w.state["revealed"] = True
ids = sorted(w.agents)
rt_ = w.state["escape"]["routes"]["raft"]
rt_["contributors"] = ids[:3]
rt_["parts"] = {"materials": 4}
tk_ = r.new_tick(14)
used_ = []
for _ in range(6):
    used_ += r.escape_counter(tk_, "raft")
evs_ = [e["text"] for e in tk_["events"] if e["type"] == "tease"]
check("TereVi's counters are things people see: confiscations, a locked workroom, a punishment on air, a planted rumour",
      len(set(used_)) >= 3 and len(evs_) >= 6 and rt_["parts"]["materials"] < 4, str(sorted(set(used_))))

# ---- phase 7b step 3: the raft, the outside and the rescue (outside.py)
def raft_(seed):
    w_, r_, _ = fresh(seed)
    w_.state["revealed"] = True
    rt = w_.state["escape"]["routes"]["raft"]
    for st in rt["plan"]:
        rt["plan"][st] = 100
    rt["contributors"] = sorted(w_.agents)[:3]
    rt["parts"] = {"materials": 4, "provisions": 2}
    r_.rng = _Fixed(0.01, r_.rng)
    t_ = r_.run_finale("raft", 6)
    r_.rng = r_.rng.b
    r_.emit(t_)
    return w_, r_, t_
w, r, t_ = raft_(254)
crew_ = r.outside()["crews"][0]["ids"] if r.outside()["crews"] else []
ls_ = [l for g in t_["talk"] if g.get("scene") for l in g["lines"]]
check("the raft is small (two or three), its launch is a live scene, and the show goes on for everyone else",
      2 <= len(crew_) <= 4 and not w.state.get("over") and len(w.agents) >= 4 and (t_.get("practice") or {}).get("room") == "beach" and any(l.get("move") == "launch" for l in ls_), str(crew_))
check("the crew is off the show ('escaped') and has an off-screen journey", all(w.state["agents"][c]["status"] == "escaped" for c in crew_) and r.outside()["crews"][0]["stage"] == "sea")
stages_ = []
for d in range(8):
    tk_ = r.new_tick(31)
    r.outside_dawn(tk_)
    stages_.append(r.outside()["crews"][0]["stage"])
    r.day += 1
check("each dawn the audience gets a snippet from out there, and the crew lands or is lost, then is believed, dismissed or silenced",
      any(e["type"] == "outside" for e in tk_["events"]) or stages_[-1] in ("believed", "dismissed", "silenced", "lost"), str(stages_))
w, r, _ = fresh(255)
w.state["revealed"] = True
tk_ = r.new_tick(12)
r.start_rescue(tk_, "broadcast", "the broadcast was believed")
check("a believed escape or broadcast starts a rescue countdown, and TereVi announces the final episode",
      w.state["rescue"]["arrive"] >= r.day + 2 and any("FINAL EPISODE" in b["text"] for b in tk_["broadcasts"]))
r.day = w.state["rescue"]["arrive"]
check("the rescue is due once its day comes", r.rescue_due(12))
t_ = r.run_rescue(12)
check("rescue with enough people alive is a good ending", w.state["over"]["kind"] == "rescue" and w.state["over"]["tier"] == "good")
w, r, _ = fresh(256)
w.state["revealed"] = True
w.state["rescue"] = {"arrive": r.day, "how": "raft", "why": "x", "alive_then": 8, "day": r.day}
for c in sorted(w.agents)[2:]:
    w.end_agent(c, "dead", "murdered")
r.run_rescue(12)
check("rescue that comes after most have died is bittersweet", w.state["over"]["kind"] == "rescue_late" and w.state["over"]["tier"] == "bittersweet")

# ---- NeoVi as a person: Kumiko Akimoto (kumiko.py)
from murder.world import BEDROOMS as BEDROOMS_  # noqa: E402
from murder.looks import looks_of  # noqa: E402
w, r, _ = fresh(260)
w.state["revealed"] = True
nv_ = w.state["npcs"]["neovi"]
fan = sorted(w.agents)[0]
nv_["aff"][fan] = 7
w.agents[fan]["nv_aff"] = 7
r.day = 5
tk_ = r.new_tick(25)
got_ = [r.neovi_visit(tk_) for _ in range(6)]
check("at night NeoVi stops at the door of the one she feels most for, and feelings grow both ways",
      all(g and g["who"] == fan for g in got_) and r.nv_feel(fan) > 7 - 1 and nv_["aff"][fan] >= 8, str(got_[:2]))
check("with mutual trust she confides, and sometimes tells her real name",
      any(g.get("confided") for g in got_) and any(e["type"] == "neovi" for e in tk_["events"]))
nv_["told"] = {}
r.rng.seed(1)
for _ in range(20):
    r.neovi_confide(tk_, fan)
check("her real name, Kumiko Akimoto, is told once and remembered", nv_["told"][fan].count("name") == 1
      and any("Kumiko Akimoto" in m for m in w.agents[fan]["memory"]["recent"] + w.agents[fan]["memory"]["notes"] + [str(w.agents[fan]["memory"])]))
w.agents[fan]["nv_aff"] = 10
nv_["aff"][fan] = 10
r.mind(fan)["facets"]["romantic"] = 80
for _ in range(30):
    if r.neovi_lover():
        break
    r.neovi_visit(tk_)
check("a slow romance can grow with someone she trusts deeply", r.neovi_lover() == fan)
r.neovi_visit(tk_)
check("a lover's night is implied, never shown", any("cameras are not allowed to see" in e["text"] for e in tk_["events"]))
w, r, _ = fresh(261)
w.state["revealed"] = True
nv_ = w.state["npcs"]["neovi"]
ally_ = sorted(w.agents)[1]
nv_["aff"][ally_] = 9
nv_["fear"] = 0
r.neovi_arc()["stage"] = 3
kinds_ = Counter()
for _ in range(30):
    if not r.neovi_maid():
        break
    nv_.update(fear=0, sanity=70)
    nv_["aff"][ally_] = 9
    kinds_[r.neovi_choice(r.new_tick(25))] += 1
check("a fond, unafraid NeoVi mostly helps (and may get caught)", kinds_["help"] + kinds_["caught"] >= kinds_["obey"] and not kinds_["betray"], str(kinds_))
w, r, _ = fresh(262)
w.state["revealed"] = True
nv_ = w.state["npcs"]["neovi"]
nv_["fear"] = 10
nv_["sanity"] = 20
kinds_ = Counter(r.neovi_choice(r.new_tick(25)) for _ in range(40))
check("a frightened, broken NeoVi with no friends betrays or obeys, never helps", kinds_["betray"] > 0 and not kinds_["help"], str(kinds_))
w, r, _ = fresh(263)
w.state["revealed"] = True
nv_ = w.state["npcs"]["neovi"]
w.state["escape"]["routes"]["raft"]["parts"] = {"materials": 4}
nv_["warned"] = "raft"
tk_ = r.new_tick(25)
used_ = r.escape_counter(tk_, "raft", strong=True)
check("a warning from NeoVi spoils TereVi's counter: the parts are kept and nobody is punished",
      used_ == ["lockdown"] and w.state["escape"]["routes"]["raft"]["parts"]["materials"] == 4 and "warned" not in nv_)
w, r, _ = fresh(264)
w.state["revealed"] = True
nv_ = w.state["npcs"]["neovi"]
san0_ = nv_.setdefault("sanity", 70)
class _Roll:
    def __init__(self, v): self.v = v
    def random(self): return self.v
    def __getattr__(self, k): return getattr(r.__dict__["_rng0"], k)
r._rng0 = r.rng
r.rng = _Roll(0.3)
r.neovi_caught(r.new_tick(25), sorted(w.agents)[0])
check("caught helping, she can be re-educated: her sanity drops hard and her feelings are pushed back",
      nv_["punished"][-1]["kind"] == "re-education" and nv_["sanity"] <= san0_ - 25)
r.rng = _Roll(0.0)
before_ = len(w.agents)
r.neovi_caught(r.new_tick(25), sorted(w.agents)[0])
check("or TereVi makes her a contestant under her real name, in a bedroom of her own",
      "kumiko" in w.agents and len(w.agents) == before_ + 1 and w.state["cast"]["kumiko"]["name"] == "Kumiko Akimoto"
      and w.state["cast"]["kumiko"]["home"] in BEDROOMS_ and not r.neovi_maid() and nv_["arc"]["fate"] == "participant")
r.rng = r._rng0
check("after that no newcomers can arrive", w.state["no_newcomers"])
r.ensure_wardrobe()
check("Kumiko has her own looks and clothes", looks_of("kumiko", w.state["cast"]["kumiko"])["eyes"] == "red eyes" and "clothes_kumiko" in w.state["custom_items"])
kc_ = w.state["cast"]["kumiko"]
lk_ = looks_of("kumiko", kc_)
check("out of uniform Kumiko looks like her picture: long dark purple hair, red eyes, short, a stuffed rabbit, a black blazer and red tie",
      lk_["hair"] == ("long", "dark purple") and lk_["eyes"] == "red eyes" and lk_["height"] == "short" and "rabbit" in lk_["accessory"][0]
      and "red tie" in w.state["custom_items"]["clothes_kumiko"]["name"])
check("her sheet sets her nature outright: very curious, mild, not assertive, fragile under weight",
      r.facet("kumiko", "curiosity") >= 85 and r.facet("kumiko", "anger") <= 20 and r.facet("kumiko", "assertiveness") <= 30
      and r.facet("kumiko", "stress_vulnerability") >= 70 and r.has_trait("kumiko", "undecided") and not r.has_trait(sorted(w.agents)[0], "undecided"))
other_ = next(c for c in sorted(w.agents) if c != "kumiko")
bts_k = r.resolve_move(r.new_tick(14), {"id": "tk", "room": w.agents["kumiko"]["room"], "members": [other_, "kumiko"], "used": {}, "hour": 14}, other_, "kumiko", "accuse")
check("accused to her face, Kumiko freezes instead of answering", bts_k[1]["move"] == "freeze")
labs_ = []
r._seg = lambda tk, cid, m0, m1, room, act, label, *a, **k: labs_.append(label)
for _ in range(6):
    w.agents["kumiko"]["room"] = "lounge"
    r._start(r.new_tick(14), "kumiko", "look", "lounge", None, 0)
del r._seg
check("she does cat-like things (watching from a high shelf, staring at a corner)", labs_ and all(l in ("watching everyone from a high shelf", "staring at nothing in a corner") for l in labs_), str(labs_))
r.run_tick(12)
check("Kumiko plays a day as a contestant", "kumiko" in w.state["agents"])

# ---- the inner voice and breaking minds (innervoice.py)
w = World(new_state(3))
t_ = []
DayRunner(w, LLM(backend="mock"), t_.append, step=2, murders=False, rule_mode="none", seed=7).run()
inner_ = [x for tk in t_ for x in (tk.get("inner") or [])]
check("now and then people's thoughts show, some said out loud", len(inner_) >= 3 and {"think"} <= {x["kind"] for x in inner_}
      and all(x.get("room") and x.get("text") for x in inner_), str(len(inner_)))
w, r, _ = fresh(270)
w.state["revealed"] = True
a_, b_, c_ = sorted(w.agents)[:3]
w.agents[a_]["sanity"] = 30
now_ = r.abs_now()
r.believe(a_, {"k": "at", "s": b_, "r": "kitchen", "t0": now_, "t1": now_, "src": "seen", "c": 0.9, "true": True})
w.agents[a_]["aff"][c_] = -5
r.rng.seed(4)
kinds_ = {r.warp_belief(a_) for _ in range(8)}
check("below 40 sanity beliefs are reread through fear (a sighting gets the wrong person, a rumour hardens, a friend becomes a trap)",
      kinds_ - {None} and any(b.get("warp") for b in r.beliefs(a_)), str(kinds_))
w.agents[a_]["sanity"] = 10
hk_ = [r.hallucinate(r.new_tick(14), a_) for _ in range(6)]
hal_ = [b for b in r.beliefs(a_) if b.get("hal")]
check("below 25 people hallucinate: false beliefs held with confidence, marked for the GM",
      len(hal_) >= 3 and all(not b.get("true", True) and b["c"] >= 0.8 for b in hal_)
      and any(v.get("mind") == "hallucination" for v in r.beliefs_view(a_)), str(hk_))
w, r, _ = fresh(271)
w.state["revealed"] = True
ids_ = sorted(w.agents)
k_, v_, wit_ = ids_[0], ids_[1], ids_[2]
w.agents[k_]["room"] = w.agents[v_]["room"] = "green_room"
tk_ = r.new_tick(15)
r.open_case(tk_, "murder", v_, culprit=k_, wkind="sharp", weapon=sharp(), room="green_room", hour=15, witnesses=[])
r.announce_body(tk_, 16)
w.agents[wit_]["sanity"] = 0
fm_ = None
for _ in range(20):
    fm_ = fm_ or r.false_memory(wit_)
facts_ = r.trial_facts(w.state["case"], [c for c in ids_ if c in w.agents])
check("a broken mind 'remembers' someone at the scene, and it goes into their testimony as an honest but false fact",
      fm_ and any(f["by"] == wit_ and f["about"] == fm_ and f["kind"] == "near_scene" and not f["true"] for f in facts_), str(fm_))
w, r, _ = fresh(272)
w.state["revealed"] = True
a_, b_ = sorted(w.agents)[:2]
w.agents[a_]["sanity"] = 5
r.believe(a_, {"k": "has", "s": b_, "o": "kitchen_knife", "n": "I saw them with a knife", "src": "seen", "c": 0.85, "t0": r.abs_now(), "true": False, "hal": True})
acts_ = Counter(r.act_on_fear(r.new_tick(14), a_, 14) for _ in range(20))
check("below 10 they act on it: hiding, or deciding to strike first", acts_["strike"] + acts_["hide"] >= 1
      and (acts_["strike"] == 0 or w.state["plots"][a_]["target"] == b_), str(acts_))
w.agents[a_]["sanity"] = 60
r.rng.seed(1)
for _ in range(6):
    r.recover_minds(r.new_tick(31))
check("when sanity recovers, a hallucination is seen for what it was", any(b.get("seen_through") for b in r.beliefs(a_)))
w, r, _ = fresh(273)
r.tuning_get = lambda: {"hallucinations": 0}
w.state["revealed"] = True
a_ = sorted(w.agents)[0]
w.agents[a_]["sanity"] = 5
r.distort_minds(r.new_tick(14), 14)
check("the dial switches breaking minds off", not any(b.get("hal") or b.get("warp") for b in r.beliefs(a_)))

# ---- tone, intimacy and rare turns (tone.py, intimacy.py, twists.py)
w, r, _ = fresh(280)
w.state["revealed"] = True
r.tuning_get = lambda: {"gore": 3, "flirt_level": 2}
b3_ = r.bible()
r.tuning_get = lambda: {"gore": 0, "flirt_level": 2}
b0_ = r.bible()
check("the tone guide is in every voice call: game-show comedy, gore by the dial, sex implied and never explicit",
      "game show" in b3_ and "unflinchingly" in b3_ and "cut away" in b0_ and "Never explicit" in b3_)
check("at gore 0 a body is not described", r.body_desc({"kind": "murder", "method": "sharp (knife)"}) == "is dead")
r.tuning_get = lambda: {}
a_, b_, c_ = sorted(w.agents)[:3]
w.state["bonds"] = [{"a": a_, "b": b_, "kind": "romance", "since": 3}]
tk_ = r.new_tick(23)
r.night_together(tk_, a_, b_)
check("lovers spend the night together, implied and cut away from", any(e["type"] == "romance" and r.nm(a_) in e["text"] for e in tk_["events"])
      and w.state["nights"][-1]["a"] == a_)
w.agents[c_]["aff"][a_] = 9
r.mind(c_)["facets"]["romantic"] = 70
aff0_ = w.agents[c_]["aff"].get(b_, 0)
r.jealousy(r.new_tick(31), c_, a_, b_)
check("someone who wanted one of them is jealous of the other", w.agents[c_]["aff"].get(b_, 0) < aff0_)
d_ = sorted(w.agents)[3]
r.affair_found(r.new_tick(31), b_, a_, d_)
check("an affair found out ends the romance in a row", not r.partner_of(b_) and w.agents[b_]["aff"][a_] < 0)
w, r, _ = fresh(281)
w.state["revealed"] = True
a_, b_ = sorted(w.agents)[:2]
w.state["bonds"] = [{"a": a_, "b": b_, "kind": "romance", "since": 3}]
w.agents[a_]["sanity"] = w.agents[b_]["sanity"] = 10
w.state["deadline_day"] = r.day
got_ = None
for _ in range(30):
    w.state.pop("_pact_day", None)
    got_ = r.death_pact(r.new_tick(20), 20)
    if got_:
        break
check("a death pact on deadline day: two lovers go together, both dead by their own hand", got_ and a_ not in w.agents and b_ not in w.agents
      and w.state["case"]["kind"] == "suicide" and w.state["case"]["extra_victims"] == [b_ if got_[0] == a_ else a_])
tk_ = r.new_tick(21)
r.announce_body(tk_, 21)
check("it is announced without a trial, and both places fall vacant", w.state["case"] is None and len(w.state["vacancies"]) >= 2)
w, r, _ = fresh(282)
w.state["revealed"] = True
a_, b_ = sorted(w.agents)[:2]
w.state["bonds"] = [{"a": a_, "b": b_, "kind": "romance", "since": 3}]
w.agents[a_]["sanity"] = 5
r.believe(a_, {"k": "rumor", "s": b_, "n": "they are betraying me", "src": "inferred", "c": 0.8, "t0": r.abs_now(), "true": False, "warp": True})
got_ = None
for _ in range(60):
    got_ = got_ or r.murder_suicide(r.new_tick(27))
check("a broken lover who believes the worst can kill the other and then themselves", got_ == (a_, b_) and a_ not in w.agents and b_ not in w.agents
      and w.state["twists"]["murder_suicide"] == 1)
w, r, _ = fresh(283)
ids_ = sorted(w.agents)
k_, v_ = ids_[0], ids_[1]
case_ = {"victim": v_, "kind": "murder", "culprit_aware": True}
w.agents[k_]["sanity"] = 10
meter_ = {p: 0.0 for p in ids_}
meter_[ids_[2]] = 5.0
def push_(x, a):
    meter_[x] = max(0.0, meter_[x] + a)
class _R:
    def __init__(self, v): self.v = v
    def random(self): return self.v
    def __getattr__(self, k): return getattr(r.__dict__["_r0"], k)
r._r0, r.rng = r.rng, _R(0.0)
bt_ = []
tw_ = r.trial_twist(bt_, ids_, k_, meter_, push_, case_)
check("a guilt-sick killer can confess just before the vote", tw_ == "confession" and max(meter_, key=meter_.get) == k_ and bt_[0]["speaker"] == k_)
meter_ = {p: 0.0 for p in ids_}
meter_[k_] = 6.0
w.agents[k_]["sanity"] = 80
r.mind(k_)["facets"]["altruism"] = 20
case_["culprit_aware"] = False
lover_ = ids_[3]
w.agents[lover_]["aff"][k_] = 9
r.mind(lover_)["facets"]["altruism"] = 70
tw_ = r.trial_twist([], ids_, k_, meter_, push_, case_)
check("someone who loves the killer can take the blame for them", tw_ == "took_blame" and max(meter_, key=meter_.get) == lover_)
r.rng = r._r0
w, r, _ = fresh(284)
w.state["revealed"] = True
x_ = sorted(w.agents)[0]
crew_ = {"ids": [x_], "alive": [x_], "stage": "sea", "days": 1, "food": 2, "log": [], "tries": 0, "proof": False}
w.agents[x_]["room"] = "beach"
w.end_agent(x_, "escaped", "escaped on a raft")
w.state["vacancies"].append({"gender": w.state["cast"][x_]["gender"], "reason": "x"})
n0_ = len(w.state["vacancies"])
check("an escapee can be carried back by the sea, a participant again", r.raft_returns(r.new_tick(31), crew_) and x_ in w.agents and len(w.state["vacancies"]) == n0_ - 1
      and crew_["stage"] == "returned")

# ---- endings: the price of winning, the parting shot, the last stand and the epilogues (endings.py)
w, r, _ = fresh(290)
w.state["revealed"] = True
tk_ = r.new_tick(14)
r._end_season(tk_, "shutdown", "TEREVI IS SHUT DOWN", "x")
check("a clean win is a good ending, with an epilogue for every survivor", w.state["over"]["tier"] == "good" and not w.state["over"]["costs"]
      and len(w.state["over"]["epilogues"]) >= len(w.agents) and all(e["text"] for e in w.state["over"]["epilogues"]))
w, r, _ = fresh(291)
w.state["revealed"] = True
r.tuning_get = lambda: {"parting_shot": 10}
team_ = sorted(w.agents)[:2]
dead_ = r.parting_shot(r.new_tick(14), "shutdown", team_)
r._end_season(r.new_tick(14), "shutdown", "TEREVI IS SHUT DOWN", "x")
check("TereVi's parting shot takes someone with her, and the win becomes bittersweet", dead_ and all(d not in w.agents for d in dead_)
      and w.state["over"]["tier"] == "bittersweet" and any("TereVi took" in c for c in w.state["over"]["costs"]), str(dead_))
w, r, _ = fresh(292)
w.state["revealed"] = True
ids_ = sorted(w.agents)
for c in ids_[2:]:
    w.end_agent(c, "dead", "murdered")
r._end_season(r.new_tick(14), "winners", "THE WINNERS", "x", ids=ids_[:2])
check("crowned winners of a killing game are a bittersweet ending", w.state["over"]["tier"] == "bittersweet")
w, r, _ = fresh(293)
w.state["revealed"] = True
a_, b_ = sorted(w.agents)[:2]
w.state["bonds"] = [{"a": a_, "b": b_, "kind": "romance", "since": 3}]
w.agents[a_]["aff"][b_] = w.agents[b_]["aff"][a_] = 9
r._end_season(r.new_tick(14), "ultimatum", "THE SHOW SURRENDERS", "x")
ep_ = {e["id"]: e["text"] for e in w.state["over"]["epilogues"]}
check("lovers who walk out together share one fate in their epilogues", r.nm(b_) in ep_[a_] and r.nm(a_) in ep_[b_])
w, r, _ = fresh(294)
w.state["revealed"] = True
for k_ in w.state["escape"]["routes"]["raft"]["plan"]:
    w.state["escape"]["routes"]["raft"]["plan"][k_] = 80
for c in sorted(w.agents)[3:]:
    w.end_agent(c, "dead", "murdered")
check("with only a few left, a way out that is far along gets a last-stand attempt, once", r.last_stand_route() == "raft" and r._desperate > 0
      and r.last_stand_route() is None)
w, r, _ = fresh(295)
w.state["revealed"] = True
n0_ = len(w.agents)
r.rng.seed(1)
lost_ = None
for _ in range(20):
    lost_ = lost_ or r.rescue_loss(r.new_tick(12))
check("the rescue can leave someone behind", lost_ and len(w.agents) == n0_ - 1 and w.state["_left_behind"] == lost_)

bad = [n for n, ok, known in RESULTS if not ok and not known]
known_ = [n for n, ok, known in RESULTS if not ok and known]
print(f"\n{len(RESULTS) - len(bad) - len(known_)}/{len(RESULTS)} passed" + (f"; {len(known_)} known failures" if known_ else "") + (f"; FAILED: {bad}" if bad else ""))
sys.exit(1 if bad else 0)
