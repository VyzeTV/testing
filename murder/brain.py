"""The brain: what the models remember, and what they intend.

The engine is the body and the autopilot (paths, needs, furniture, fire, slices). The chat models are the mind. With the `brain` dial on:

* MEMORY. Everything a character perceives or does is remembered as a timestamped entry with an importance and the people it is about (`agent["mem"]`). A model call does not get the whole log: it
  gets the handful of memories most relevant to the moment (recent, important, about the people involved, in this room), so a feud from day 2 can come back on day 5 and a scene is not
  written cold. Diary lines and the nightly arc are memories too, and the store is trimmed each night (important things last).
* PLANS. In a decision the model also writes what it intends over the next few hours (go somewhere, talk to someone, work at something, look into something, avoid somebody). The engine then
  carries those intentions out through the free-time slices (walking, queueing at furniture, starting the chat), ticks them off, and only asks the model again when the plan is used up,
  stale, or something big happens. Routine blocks stop costing a call.
* CONVERSATIONS. When two people meet with a purpose, the scene card gets what each of them remembers about the other, and their stated intention.

BrainMixin is mixed into DayRunner (engine.py). Everything is skipped when the dial is 0, which keeps the old behaviour.
"""
import re

MEM_CAP = 240
DO_KINDS = ("talk", "go", "work", "search", "avoid", "wait")
KEYS = [  # (regex, importance, kind)
    (r"\(private\)", 4, "private"), (r"CLUE|clue", 6, "clue"), (r"\b(kill|killed|murder|murdered|dead|body|bodies|attack|attacked|stab|stabbed|poison|poisoned|strangle|strangled|blood|bloody)\b", 7, "violence"), (r"trial|vote|verdict|execut", 6, "trial"),
    (r"secret|confess|reveal", 5, "secret"), (r"fire|burn|smoke|flood", 5, "danger"), (r"\(you saw\)|\(saw\)", 3, "saw"), (r"overheard|\(heard\)", 4, "heard"), (r"\(odd\)|\(learned\)", 4, "odd"),
    (r"tased|punish|detention", 4, "punish"), (r"gave|gives|handed", 3, "gift"), (r"lied|lie |betray|blackmail|threat", 5, "betrayal"), (r"love|kiss|flirt|hug", 4, "warm"),
    (r"shove|insult|snub|slap|hates|furious", 3, "friction"), (r"said:", 2, "talk"), (r"announced", 2, "announce"), (r"experiment|raft|radio|transmitter|escape", 3, "escape"),
]
SKIP = re.compile(r"\b(leaves?|arrives? in|arrive|slips? out of|slips? into|pass through|passes through|passing through|walks? (in|out))\b")


def _hh(text):
    m = re.match(r"\s*(\d{1,2}):(\d{2})", text or "")
    return int(m.group(1)) if m else None


class BrainMixin:
    def brain_on(self):
        return bool(self.tune("brain"))

    # ------------------------------------------------------------------ memory
    def mem_hook(self, cid, text):
        """Called by World.remember for everything a character learns. Trivia (people walking about) is not kept."""
        if not self.brain_on() or cid not in self.world.agents or not text:
            return
        if SKIP.search(text) and not re.search(r"\(private\)|CLUE|dead|body", text):
            return
        imp, kind = 1, "event"
        for rx, v, k in KEYS:
            if re.search(rx, text):
                if v > imp:
                    imp, kind = v, k
        if imp < 2:
            return
        self.mem_add(cid, text, kind, imp)

    def mem_people(self, text):
        names = getattr(self, "_chron_names", None)
        if names is None:
            names = self._chron_names = self.chron_names()
        return [c for c, rx in names.items() if rx.search(text or "")]

    def mem_add(self, cid, text, kind="event", imp=3, people=None, hour=None):
        a = self.world.agents.get(cid)
        if a is None:
            return
        store = a.setdefault("mem", [])
        h = hour if hour is not None else (_hh(text) if _hh(text) is not None else self.s.get("_hour", 12))
        text = re.sub(r"^\s*\d{1,2}:\d{2}\s*", "", text.strip())[:240]
        if store and store[-1]["t"] == text:
            return
        people = [p for p in (people if people is not None else self.mem_people(text)) if p != cid]
        store.append({"d": self.day, "h": int(h), "t": text, "p": people, "w": int(imp), "k": kind})
        if len(store) > MEM_CAP + 60:
            self.mem_prune(cid)

    def mem_prune(self, cid, keep=MEM_CAP):
        a = self.world.agents.get(cid)
        if not a:
            return
        store = a.get("mem") or []
        if len(store) <= keep:
            return
        now = self.day * 24 + self.s.get("_hour", 12)
        ranked = sorted(store, key=lambda m: m["w"] * 1.0 + 0.5 ** ((now - (m["d"] * 24 + m["h"])) / 72.0) * 4, reverse=True)[:keep]
        a["mem"] = sorted(ranked, key=lambda m: (m["d"], m["h"]))

    def mem_recall(self, cid, people=(), words=(), room=None, k=8, skip_recent=0):
        """The memories most worth having in mind right now, oldest first: recent ones, important ones, those about the people involved, those that happened in this room."""
        a = self.world.agents.get(cid)
        if not a:
            return []
        store = a.get("mem") or []
        if skip_recent:
            store = store[:-skip_recent]
        now = self.day * 24 + self.s.get("_hour", 12)
        people = set(people)
        words = [x.lower() for x in words if x]
        scored = []
        for i, m in enumerate(store):
            age = max(0, now - (m["d"] * 24 + m["h"]))
            sc = 0.55 * (0.5 ** (age / 36.0)) + 0.07 * m["w"] + 0.9 * len(people & set(m["p"]))
            if words:
                low = m["t"].lower()
                sc += 0.12 * sum(1 for x in words if x in low)
            if room and room in m["t"].lower().replace(" ", "_"):
                sc += 0.15
            scored.append((sc, i))
        top = sorted(scored, reverse=True)[:k]
        return [store[i] for _, i in sorted(top, key=lambda t: t[1])]

    def mem_lines(self, mems, width=120):
        return [f"[D{m['d']} {m['h']:02d}h] {m['t'][:width]}" for m in mems]

    def mem_focus(self, cid):
        """Who and what this person has on their mind: people in the room, strong feelings, a plot target, plan targets."""
        w, s = self.world, self.s
        a = w.agents[cid]
        people = {o for o in w.occupants(a["room"]) if o in w.agents and o != cid}
        people |= {o for o, v in a["aff"].items() if abs(v) >= 5 and o in w.agents}
        p = s.get("plots", {}).get(cid)
        if p:
            people.add(p["target"])
        for it in self.plan_items(cid):
            if it.get("who") in w.agents:
                people.add(it["who"])
        return people

    def mem_decision_lines(self, cid, hour):
        """The memory part of a decision prompt: what is recent, then what is relevant from further back."""
        w = self.world
        a = w.agents[cid]
        rec = a["memory"]["recent"][-5:]
        old = self.mem_recall(cid, self.mem_focus(cid), [w.room_name(a["room"])], a["room"], k=9, skip_recent=3)
        out = []
        if old:
            out.append("WHAT YOU REMEMBER (the most relevant, oldest first): " + " | ".join(self.mem_lines(old)))
        out.append("JUST NOW: " + (" | ".join(rec) or "(nothing yet)"))
        return out

    def mem_card(self, cid, group, k=4):
        """The memory part of a conversation card: the last few things, and what this person remembers about the people they are talking to."""
        a = self.world.agents[cid]
        others = [o for o in group if o != cid and o in self.world.agents]
        rec = a["memory"]["recent"][-3:]
        rel = self.mem_recall(cid, others, [], a["room"], k=k, skip_recent=2)
        parts = []
        if rel:
            parts.append("Remembers about them: " + " | ".join(self.mem_lines(rel, 100)))
        parts.append("Just now: " + (" | ".join(rec) or "none"))
        return " ".join(parts)

    # ------------------------------------------------------------------ plans
    def plan_clean(self, raw):
        w = self.world
        out = []
        if isinstance(raw, list):
            for it in raw[:8]:
                if len(out) >= 3:
                    break
                if not isinstance(it, dict):
                    continue
                do = str(it.get("do") or "").lower().strip()
                if do not in DO_KINDS:
                    continue
                who = str(it.get("who") or "")
                where = str(it.get("where") or "")
                from .data_world import ROOMS
                out.append({"do": do, "who": who if who in w.agents else "", "where": where if where in ROOMS else "", "why": str(it.get("why") or "")[:80], "done": False})
        return out

    def plan_schema(self):
        return ', "plan": [{"do": "talk|go|work|search|avoid|wait", "who": "<person id, for talk or avoid>", "where": "<room id, for go, work or search>", "why": "<max 10 words>"}]'

    def plan_explain(self):
        return ("PLAN: also write up to 3 things you intend to do over the next few hours, beyond this turn (talk to someone about something, go and look into somewhere, work at a way out, "
                "keep away from somebody); the house carries them out for you through the free hours, so make them specific and true to your goals, feelings and what you remember. "
                "Keep your old plan if it still fits. ")

    def plan_account(self, cid):
        """Count what the plan that is being replaced or retired achieved (for telemetry)."""
        a = self.world.agents.get(cid)
        p = (a or {}).get("plan")
        if not p:
            return
        st = self.s.setdefault("brain_stats", {}).setdefault(str(p.get("day")), {"made": 0, "done": 0})
        st["made"] += len(p["items"])
        st["done"] += sum(1 for it in p["items"] if it.get("done"))

    def plan_store(self, cid, hour, items):
        a = self.world.agents[cid]
        self.plan_account(cid)
        a["plan"] = {"day": self.day, "hour": hour, "items": items}

    def plan_items(self, cid):
        a = self.world.agents.get(cid)
        p = (a or {}).get("plan")
        if not p or p.get("day") != self.day:
            return []
        return [it for it in p["items"] if not it.get("done")]

    def plan_needed(self, cid, hour):
        """Whether the model should be asked for a fresh plan: none yet today, all of it done, or it is more than three blocks old."""
        a = self.world.agents[cid]
        p = a.get("plan")
        if not p or p.get("day") != self.day or not [it for it in p["items"] if it["do"] != "wait"]:
            return True
        age = hour - p.get("hour", 0)
        if not self.plan_items(cid):
            return age >= 4                       # everything done: a fresh plan, but not every block
        return age >= 6

    def plan_lines(self, cid):
        """What the character is told about their own plan in a decision prompt."""
        a = self.world.agents[cid]
        p = a.get("plan")
        if not p or p.get("day") != self.day:
            return ["YOUR PLAN: you have none yet today. Decide what you intend over the next few hours."]
        bits = []
        for it in p["items"]:
            tgt = (f" {self.nm(it['who'])}" if it.get("who") else "") + (f" in the {self.world.room_name(it['where'])}" if it.get("where") else "")
            bits.append(f"{'(done) ' if it.get('done') else ''}{it['do']}{tgt}: {it['why']}")
        return ["YOUR PLAN (made at " + f"{p.get('hour', 0):02d}:00" + "; keep it if it still fits, change it if things have moved on): " + " | ".join(bits)]

    def plan_mark(self, cid, do=None, who=None, where=None):
        a = self.world.agents.get(cid)
        if not a or not a.get("plan"):
            return
        for it in a["plan"]["items"]:
            if it.get("done") or (do and it["do"] != do):
                continue
            if who and it.get("who") == who or where and it.get("where") == where:
                it["done"] = True

    def plan_avoid(self, cid):
        return {it["who"] for it in self.plan_items(cid) if it["do"] == "avoid" and it.get("who")}

    def plan_options(self, tick, cid, hour, m, reach, add):
        """Intentions of the plan as options for this slice. Chats are offered by chat_options (it reads the plan too)."""
        a = self.world.agents[cid]
        here = a["room"]
        reach = self.world.reachable_rooms(cid, max(14, int(48 * self.move_factor(cid))))          # a plan is worth a longer walk than a whim
        for it in self.plan_items(cid):
            do, where, why = it["do"], it.get("where"), it.get("why") or ""
            if do in ("go", "search"):
                if where and (where in reach or where == here):
                    add(1.5, "explore", room=where, why=why or "has somewhere to be")
                elif not where:
                    add(1.1, "look", why=why or "looking into something")
            elif do == "work":
                rooms = [where] if where else ["generator_shed", "boathouse", "boiler_room", "study"]
                add(1.5, "tinker", rooms=rooms, kinds=["workbench", "table", "desk", "radio"], why=why or "working on something")

    def plan_talk_targets(self, cid):
        return [it for it in self.plan_items(cid) if it["do"] == "talk" and it.get("who") in self.world.agents]

    def plan_done_by_act(self, cid, act, room):
        """An activity just started: tick off the plan items it satisfies."""
        if not self.brain_on() or not self.world.agents.get(cid, {}).get("plan"):
            return
        if act in ("explore", "look"):
            self.plan_mark(cid, "go", where=room)
            self.plan_mark(cid, "search", where=room)
            if not any(it.get("where") for it in self.plan_items(cid) if it["do"] in ("go", "search")):
                for it in self.plan_items(cid):
                    if it["do"] == "search" and not it.get("where"):
                        it["done"] = True
        elif act == "tinker":
            for it in self.plan_items(cid):
                if it["do"] == "work" and (not it.get("where") or it["where"] == room):
                    it["done"] = True
                    break

    # ------------------------------------------------------------------ reflection and trimming
    def brain_night(self, cid, diary, arc=None):
        """The night: the diary and the arc become memories, the store is trimmed, the day's plan is retired."""
        if not self.brain_on() or cid not in self.world.agents:
            return
        if diary:
            self.mem_add(cid, f"(my diary) {diary}", "diary", 7, hour=22)
        if arc:
            self.mem_add(cid, f"(how I am changing) {arc}", "arc", 6, hour=22)
        self.mem_prune(cid)
        a = self.world.agents[cid]
        self.plan_account(cid)
        a["plan"] = None

    def brain_view(self, cid):
        """For the viewer's cast panel: the plan and the memories that matter most just now."""
        a = self.world.agents.get(cid)
        if not a:
            return None
        plan = [dict(it) for it in ((a.get("plan") or {}).get("items") or [])] if (a.get("plan") or {}).get("day") == self.day else []
        mem = self.mem_recall(cid, self.mem_focus(cid), [], a["room"], k=5)
        return {"plan": plan, "mem": self.mem_lines(mem, 110)}
