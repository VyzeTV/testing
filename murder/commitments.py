"""Persistent intentions and obligations, with checked outcomes and a bounded history.

The store functions are independent of DayRunner. CommitmentManager adapts the
store to existing plots, pacts, occasions, dares, reflection and social moves.
"""
import copy
import math

PERSONAL = ("protect", "confront", "apologise", "ask", "thank", "promise")
TALK_MOVES = {"confront": "confront", "apologise": "apologise", "ask": "ask", "thank": "thank"}
TERMINAL = ("fulfilled", "abandoned", "failed", "cancelled", "broken")


def upgrade(state):
    state.setdefault("commitments", [])
    state.setdefault("commitment_history", [])
    state.setdefault("commitment_seq", 0)
    state.setdefault("commitment_revision", 0)


def active(state, owner=None, kind=None):
    return [c for c in state.get("commitments", []) if c["status"] == "active"
            and (owner is None or c["owner"] == owner) and (kind is None or c["kind"] == kind)]


def history(state, c, now, status, reason):
    state["commitment_revision"] += 1
    state["commitment_history"].append({"id": c["id"], "owner": c["owner"], "kind": c["kind"],
                                        "target": c.get("target"), "at": now, "status": status, "reason": reason})
    del state["commitment_history"][:-200]


def start(state, owner, kind, title, now, due=None, **fields):
    upgrade(state)
    state["commitment_seq"] += 1
    c = dict(fields, id=f"c{state['commitment_seq']}", owner=owner, kind=kind, title=title[:180],
             started=now, due=due, status="active")
    state["commitments"].append(c)
    history(state, c, now, "active", "accepted")
    return c


def end(state, c, now, status, reason):
    """One terminal transition only. Unexplained abandonment is never accepted."""
    if status not in TERMINAL or c["status"] != "active" or not str(reason or "").strip():
        return False
    c.update(status=status, ended=now, reason=str(reason).strip()[:180])
    history(state, c, now, status, c["reason"])
    # Retain every active obligation and the last 100 completed ones.
    closed = [x for x in state["commitments"] if x["status"] != "active"]
    keep = {x["id"] for x in closed[-100:]}
    state["commitments"][:] = [x for x in state["commitments"] if x["status"] == "active" or x["id"] in keep]
    return True


def concrete_reason(raw):
    reason = str(raw or "").strip()[:180]
    if len(reason) < 8 or reason.lower().rstrip(".! ") in ("changed my mind", "never mind", "no reason", "i am bored", "something changed"):
        return ""
    return reason


def clean_request(raw):
    if not isinstance(raw, dict) or raw.get("kind") not in PERSONAL:
        return None
    try:
        hours = float(raw.get("hours", 24))
        if not math.isfinite(hours):
            return None
    except (ValueError, TypeError):
        return None
    return {"kind": raw["kind"], "target": str(raw.get("target") or ""),
            "action": str(raw.get("action") or "talk"), "item": str(raw.get("item") or "")[:80],
            "room": str(raw.get("room") or ""), "hours": max(4, min(72, hours)),
            "reason": concrete_reason(raw.get("reason"))}


class CommitmentManager:
    def __init__(self, engine):
        self.e = engine
        upgrade(self.s)
        self.sync(None)  # Also adopts obligations in old saves, without events or costs.

    @property
    def s(self):
        return self.e.world.state

    def now(self, tick=None):
        e = self.e
        return e.day * 24 + (tick["hour"] if tick else self.s.get("_hour", 8)) + (e.minute() or 0) / 60

    def active(self, owner=None, kind=None):
        return active(self.s, owner, kind)

    def finish(self, tick, c, status, reason, cost=False):
        if not end(self.s, c, self.now(tick), status, reason):
            return False
        e, w = self.e, self.e.world
        owner = c["owner"]
        if tick is not None:
            text = f"{e.nm(owner)}: {c['title']} — {status}: {c['reason']}."
            tick["events"].append({"type": "commitment", "who": owner, "room": w.all_agents.get(owner, {}).get("room", "foyer"),
                                   "vis": "gm", "commitment": c["id"], "status": status, "reason": c["reason"], "text": text,
                                   "m": e.minute() or 0.0})
            for p in c.get("known_by", [owner]):
                if p in w.agents:
                    w.remember(p, text)
            if cost and owner in w.agents:
                e.stat(tick, owner, "sanity", -1, "a commitment not kept")
                target = c.get("target")
                if target in w.agents and target in c.get("known_by", []):
                    w.adjust_aff(target, owner, -2)
        if c["kind"] == "protect":
            old = w.all_agents.get(owner, {}).get("commit") or {}
            if old.get("commitment_id") == c["id"]:
                w.all_agents[owner].pop("commit", None)
        return True

    def adopt(self, owner, kind, title, source, due=None, target=None, known_by=None, **fields):
        """Attach an existing engine obligation once; refreshing it never extends its life."""
        ref = source.get("commitment_id")
        if ref:
            return next((c for c in self.s["commitments"] if c["id"] == ref), None)
        c = next((c for c in self.active(owner, kind) if c.get("target") == target), None)
        if c is None:
            c = start(self.s, owner, kind, title, getattr(self, "_sync_at", self.now()), due, target=target,
                      known_by=sorted(set(known_by or [owner])), **fields)
        source["commitment_id"] = c["id"]
        return c

    def sync(self, tick):
        """Track checked source outcomes, impossibility, and deadlines, without random rolls."""
        e, w, s = self.e, self.e.world, self.s
        self._sync_at = self.now(tick)
        for owner, p in sorted(s.get("plots", {}).items()):
            if owner in w.agents:
                self.adopt(owner, "plot", f"carry through the plan against {e.nm(p['target'])}", p, target=p["target"])
        for b in s.get("bonds", []):
            if b["kind"] != "pact":
                continue
            # Each partner has their own obligation and private outcome.
            refs = b.setdefault("commitment_refs", {})
            for owner, target in ((b["a"], b["b"]), (b["b"], b["a"])):
                if owner in w.agents and target in w.agents:
                    ref = refs.setdefault(owner, {})
                    self.adopt(owner, "pact", f"honour the pact with {e.nm(target)}", ref, target=target, known_by=[owner, target])
        oc = s.get("occasion")
        if oc and oc.get("status") == "announced" and oc["host"] in w.agents:
            due = oc["day"] * 24 + oc["hour"] + e.step + 2
            self.adopt(oc["host"], "host", f"host the {oc['kind']} in the {w.room_name(oc['where'])}", oc,
                       due=due, room=oc["where"], known_by=[oc["host"]] + oc.get("invite_ids", []))
        for d in s.get("dares", []):
            if d.get("willing") and (d.get("status") == "open" or d.get("commitment_id")) and d["who"] in w.agents:
                self.adopt(d["who"], "dare", d["task"], d, due=d["due"], target=d.get("with"))
        for owner, a in sorted(w.agents.items()):
            old = a.get("commit") or {}
            if old.get("protect") in w.agents and e.day <= old.get("until", 0):
                self.adopt(owner, "protect", f"protect {e.nm(old['protect'])}", old,
                           due=(old["until"] + 1) * 24, target=old["protect"])
            if a.get("commitments_adopted"):
                continue
            a["commitments_adopted"] = True
            want = a.get("want_talk") or {}
            if want.get("day", 0) >= e.day and not want.get("commitment_id"):
                # Only import structured reflection intentions, never arbitrary prose.
                for action in TALK_MOVES:
                    if str(want.get("why", "")).startswith(action) and len(want.get("who", [])) == 1:
                        target = want["who"][0]
                        if target in w.agents:
                            self.adopt(owner, "resolve", f"{action} {e.nm(target)}", want,
                                       due=(want["day"] + 1) * 24, target=target, action=action,
                                       not_before=want["day"] * 24 + 8)
                        break
        if tick is None:
            return
        now = self.now(tick)
        for c in list(self.active()):
            owner, target = c["owner"], c.get("target")
            case = s.get("case") or {}
            if c["kind"] == "plot" and case.get("killer") == owner and case.get("victim") == target:
                self.finish(tick, c, "fulfilled", "the planned target was killed by the plotter")
                continue
            if owner not in w.agents or target and target not in w.agents:
                p = owner if owner not in w.agents else target
                status = w.all_agents.get(p, {}).get("status", "unavailable")
                self.finish(tick, c, "cancelled", f"{e.nm(p)} is {status}")
                continue
            if c["kind"] == "plot":
                p = s.get("plots", {}).get(owner)
                if not p or p.get("commitment_id") != c["id"]:
                    change = next((x for x in reversed(s.get("plot_history", [])) if x["who"] == owner and x.get("target") == target), {})
                    self.finish(tick, c, "abandoned", change.get("reason") or "the recorded plot has ended",
                                cost=change.get("action") == "abandoned")
            elif c["kind"] == "pact":
                if not any(b["kind"] == "pact" and {b["a"], b["b"]} == {owner, target} for b in s["bonds"]):
                    change = next((b for b in reversed(s.get("bond_history", [])) if b["kind"] == "pact" and {b["a"], b["b"]} == {owner, target} and b["action"] == "ended"), {})
                    self.finish(tick, c, "abandoned", change.get("reason") or "the pact was dissolved")
            elif c["kind"] == "dare":
                d = next((d for d in s.get("dares", []) if d.get("commitment_id") == c["id"]), {})
                if d.get("status") in ("done", "failed"):
                    self.finish(tick, c, "fulfilled" if d["status"] == "done" else "failed", "the dare's task was completed" if d["status"] == "done" else "the accepted dare's deadline passed")
            elif c["due"] is not None and now >= c["due"]:
                if c["kind"] == "protect":
                    self.finish(tick, c, "fulfilled", "the protection period ended with the person alive")
                else:
                    a = w.agents[owner]
                    blocked = a.get("out") or a.get("restrained") or a["hp"] < 35 or target and w.agents[target].get("out")
                    investigating = bool(s.get("case") and s["case"].get("announced"))
                    reason = ("injury or restraint prevented following through" if blocked else
                              "a body investigation took precedence" if investigating else "the deadline passed without the promised action")
                    self.finish(tick, c, "cancelled" if blocked or investigating else "failed", reason, cost=not (blocked or investigating))

    def request(self, tick, owner, raw):
        q = clean_request(raw)
        w, e = self.e.world, self.e
        if not q or owner not in w.agents or q["target"] not in w.agents or q["target"] == owner:
            return None
        if w.agents[owner].get("out") or w.agents[owner].get("asleep"):
            return None
        target, kind = q["target"], q["kind"]
        stored_kind = "resolve" if kind in TALK_MOVES else kind
        fields = {"target": target, "action": kind if stored_kind == "resolve" else q["action"] if kind == "promise" else "protect",
                  "item": q["item"] if kind == "promise" and q["action"] == "give" else "",
                  "room": q["room"] if kind == "promise" and q["action"] == "visit" else ""}
        if kind == "promise":
            if q["action"] not in ("talk", "give", "visit") or w.agents[target]["room"] != w.agents[owner]["room"] or not e.present(target, w.agents[owner]["room"]) or w.agents[target].get("asleep") or w.agents[target].get("out"):
                return None
            if q["action"] == "give" and w.agents[owner]["inv"].get(q["item"], 0) <= 0:
                return None
            if q["action"] == "visit" and (q["room"] not in w.reachable_rooms(owner, 80) or q["room"] == w.agents[owner]["room"]):
                return None
        now = self.now(tick)
        recent = [c for c in self.s["commitments"] if c["owner"] == owner and c["kind"] == stored_kind and c.get("target") == target and c["status"] != "active" and now - c.get("ended", 0) < 24]
        if recent:
            return None
        for old in self.active(owner, stored_kind):
            if old.get("target") == target and (stored_kind == "protect" or all(old.get(k, "") == v for k, v in fields.items())):
                return old
            if stored_kind in ("protect", "resolve"):
                if not self.drop(tick, owner, old["id"], q["reason"]):
                    if old.get("wavered_on") != e.day:
                        old["wavered_on"] = e.day
                        text = f"{e.nm(owner)} considers changing {old['title']}, but keeps the commitment without a concrete new reason."
                        history(self.s, old, now, "considered", "kept the existing obligation")
                        w.remember(owner, text)
                        tick["events"].append({"type": "commitment", "commitment": old["id"], "status": "considered",
                                               "who": owner, "room": w.agents[owner]["room"], "vis": "gm", "text": text,
                                               "m": e.minute() or 0.0})
                    return None
        if len(self.active(owner)) >= 12:
            return None
        title = f"{kind} {e.nm(target)}"
        known = [owner]
        if kind == "promise":
            task = {"talk": f"talk with {e.nm(target)}", "give": f"give {e.nm(target)} the {w.item_name(q['item'])}",
                    "visit": f"visit the {w.room_name(fields['room'])}" if fields["room"] else "visit a room"}[q["action"]]
            title = f"promised {e.nm(target)} to {task}"
            known += [target]
        c = start(self.s, owner, stored_kind, title, now, now + q["hours"], known_by=known, **fields)
        w.remember(owner, f"Commitment {c['id']}: {title}; due Day {int(c['due'] // 24)}, {int(c['due'] % 24):02d}:00.")
        if kind == "protect":
            w.agents[owner]["commit"] = {"protect": target, "day": e.day, "until": int(c["due"] // 24), "commitment_id": c["id"]}
        if kind == "promise":
            e.log_event(tick, {"type": "commitment", "who": owner, "room": w.agents[owner]["room"], "vis": "public",
                               "commitment": c["id"], "status": "active", "text": f"{e.nm(owner)} {title}.", "m": e.minute() or 0.0}, witnesses=known, actor=owner)
        else:
            tick["events"].append({"type": "commitment", "who": owner, "room": w.agents[owner]["room"], "vis": "gm", "commitment": c["id"],
                                   "status": "active", "text": f"{e.nm(owner)} commits to {title}.", "m": e.minute() or 0.0})
        return c

    def drop(self, tick, owner, cid, raw_reason):
        c = next((c for c in self.active(owner) if c["id"] == cid), None)
        reason = concrete_reason(raw_reason)
        if not c or not reason:
            return False
        # A new explanation is required even in the diary; casual same-block reversals wait.
        emergency = self.e.world.agents[owner]["hp"] < 50 or self.e.world.agents[owner]["sanity"] < 40
        if self.now(tick) - c["started"] < 2 and not emergency:
            return False
        if c["kind"] == "plot":
            self.e.abandon_plot(tick, owner, reason)
        elif c["kind"] == "pact":
            from .relationships import record_bond
            for b in list(self.s["bonds"]):
                if b["kind"] == "pact" and {b["a"], b["b"]} == {owner, c["target"]}:
                    record_bond(self.s, b, self.now(tick), "ended", reason)
                    self.s["bonds"].remove(b)
        elif c["kind"] == "host":
            oc = self.s.get("occasion")
            if oc and oc.get("commitment_id") == cid:
                self.s["occasion"] = None
        elif c["kind"] == "dare":
            for d in self.s.get("dares", []):
                if d.get("commitment_id") == cid:
                    d["willing"] = False
        return self.finish(tick, c, "abandoned", reason, cost=True)

    def planned_move(self, owner, target, conv):
        for c in self.active(owner, "resolve"):
            if c.get("not_before", 0) <= self.now() and c.get("target") == target and c["action"] in TALK_MOVES:
                if c["action"] in ("apologise", "thank") and target in conv.get("against", {}).get(owner, []):
                    continue
                return c["action"]
        return None

    def spoken(self, tick, owner, target, move):
        for c in list(self.active(owner)):
            if c.get("target") != target:
                continue
            if c["kind"] == "resolve" and c.get("action") == move or c["kind"] == "promise" and c.get("action") == "talk":
                self.finish(tick, c, "fulfilled", f"actually spoke to {self.e.nm(target)} ({move}); acceptance is up to them")

    def gave(self, tick, owner, target, item):
        for c in self.active(owner, "promise"):
            if c.get("target") == target and c.get("action") == "give" and c.get("item") == item:
                self.finish(tick, c, "fulfilled", "the promised item was handed over")

    def harmed(self, tick, actor, victim):
        for c in list(self.active()):
            if c["kind"] == "plot" and c["owner"] == actor and c.get("target") == victim:
                c["progress"] = "acted on the plan by attacking the target"
            if c["kind"] in ("protect", "pact") and c.get("target") == victim and c["owner"] == actor:
                self.finish(tick, c, "broken", "harmed the person they undertook to protect", cost=c["kind"] != "pact")
            elif c["kind"] == "protect" and c["owner"] == victim and c.get("target") == actor:
                self.finish(tick, c, "abandoned", "the protected person attacked them")

    def hosted(self, tick, occasion, attended, reason):
        c = next((c for c in self.active(occasion["host"], "host") if c["id"] == occasion.get("commitment_id")), None)
        if c:
            self.finish(tick, c, "fulfilled" if attended else "failed", reason)

    def direct(self, tick, owner, decision):
        """Hosting is a real appointment. Danger and urgent care can interrupt it with a reason."""
        e, w = self.e, self.e.world
        c = next(iter(self.active(owner, "host")), None)
        oc = self.s.get("occasion")
        if not c or not oc:
            self.pursue(tick, owner, decision)
            return
        if self.now(tick) < oc["day"] * 24 + oc["hour"] + e.step:
            return
        a = w.agents[owner]
        reason = ""
        if a.get("out") or a.get("asleep") or a["hp"] < 35 or e.restrained(owner):
            reason = "injury, sleep or restraint prevents hosting"
        elif self.s.get("case") and self.s["case"].get("announced"):
            reason = "a body announcement requires an investigation"
        elif decision.get("action") in ("attack", "assault", "end_life"):
            reason = "an immediate dangerous decision displaced the gathering"
        elif e._unsafe(c["room"]):
            reason = "the venue has become unsafe"
        elif a["room"] != c["room"] and not w.path(owner, a["room"], c["room"]):
            reason = "the venue is no longer reachable"
        if reason:
            self.finish(tick, c, "cancelled", reason)
            self.s["occasion"] = None
            return
        decision.update(action="stay", target_room=c["room"], activity=c["title"], intent=c["title"])

    def pursue(self, tick, owner, decision):
        """A kept intention gets an attempt; medical needs, danger and privacy take precedence."""
        e, w = self.e, self.e.world
        a = w.agents[owner]
        if a.get("out") or a.get("asleep") or a["hp"] < 50 or e.restrained(owner) or decision.get("action") not in ("stay", "search"):
            return
        for c in self.active(owner):
            if c["kind"] not in ("resolve", "promise") or c.get("not_before", 0) > self.now(tick):
                continue
            target = c.get("target")
            if target not in w.agents or c.get("action") != "visit" and (w.agents[target].get("out") or w.agents[target].get("asleep")):
                continue
            room = c["room"] if c.get("action") == "visit" else w.agents[target]["room"]
            from .freetime import PRIVATE_ROOMS
            if room == "bathroom" or room in PRIVATE_ROOMS and room != w.cast[owner]["home"]:
                continue
            if e._unsafe(room) or room != a["room"] and not w.path(owner, a["room"], room):
                continue
            if c.get("action") == "give":
                if a["inv"].get(c["item"], 0) <= 0:
                    continue
                decision.update(action="give", to=target, item=c["item"], qty=1)
            elif c.get("action") != "visit":
                decision["talk_to"] = [target]
            decision.update(target_room=room, activity=c["title"], intent=c["title"])
            return

    def options(self, tick, owner, add):
        """Bias free time toward unfinished intentions, using normal reachability checks."""
        w = self.e.world
        for c in self.active(owner):
            if c.get("not_before", 0) > self.now(tick):
                continue
            target = c.get("target")
            if c["kind"] in ("resolve", "protect") and target in w.agents:
                if not w.agents[target].get("asleep") and not w.agents[target].get("out"):
                    add(2.4 if c["kind"] == "resolve" else 1.0, "chat", room=w.agents[target]["room"], partner=target, why=c["title"])
            elif c["kind"] == "promise" and c.get("action") == "visit":
                add(2.4, "look", room=c["room"], why=c["title"])

    def arrived(self, tick, owner, room):
        for c in list(self.active(owner, "promise")):
            if c.get("action") == "visit" and c.get("room") == room and self.now(tick) > c["started"]:
                self.finish(tick, c, "fulfilled", "actually reached the promised room")

    def context(self, owner, group=None, beats=None):
        """Private decision/diary context; shared voicing includes only known or enacted facts."""
        out = []
        records = self.active(owner)
        if group is not None:
            records += [c for c in self.s["commitments"] if c["owner"] == owner and c["status"] == "fulfilled" and c["kind"] == "resolve"
                        and any(b.get("who") == owner and b.get("to") == c.get("target") and b.get("move") == c.get("action") for b in beats or [])]
        for c in records:
            if group is not None and not set(group) <= set(c.get("known_by", [])):
                if not (c["kind"] == "resolve" and any(b.get("who") == owner and b.get("to") == c.get("target") and b.get("move") == c.get("action") for b in beats or [])):
                    continue
            due = f"; due Day {int(c['due'] // 24)} {int(c['due'] % 24):02d}:00" if c.get("due") is not None else "; remains in force until resolved"
            out.append(f"{c['id']}: {c['title']}{due}; {c['status']}")
        if group is None:
            closed = [c for c in self.s["commitments"] if c["owner"] == owner and c["status"] != "active"][-2:]
            out.extend(f"{c['id']}: {c['title']} — {c['status']}: {c['reason']}" for c in closed)
        return "COMMITMENTS: " + " | ".join(out) if out else ""

    def view(self, owner):
        pending = self.active(owner)
        closed = [c for c in self.s["commitments"] if c["owner"] == owner and c["status"] != "active"]
        return copy.deepcopy(pending + closed[-max(1, 12 - len(pending)):])

    def signature(self, owner):
        """Only this person's changed obligations invalidate a prefetched decision."""
        return tuple((c["id"], c["status"], c.get("due"), c.get("not_before")) for c in self.s["commitments"] if c["owner"] == owner)
