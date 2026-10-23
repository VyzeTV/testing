"""Read-only checks of structured story facts, shared by season and recording checks.

The checker never calls a model or changes simulation state. End-of-tick deaths do
not invalidate earlier actions in that tick. Historical mentions and deliberately
false claims are allowed; this is not a natural-language truth detector.
"""
from collections import Counter


ACTIVE_EVENTS = {"attack", "assault", "give", "take", "craft", "experiment", "intrude", "body", "snap"}
PRESENT_TOPICS = {"gossip", "warn", "incite"}


class StoryLinter:
    def __init__(self, state=None):
        self.issues = []
        self.checks = Counter()
        self.agents = {}
        self.names = {}
        self.announced = {}
        self.found = {}
        self.madness = {}
        self.claims = {}
        self.commitments = {}
        self.bond_seen = set()
        self.romances = set()
        if state:
            self.begin_day(state)

    def begin_day(self, state):
        """Register the day's cast, including newcomers, without clearing history."""
        self.names.update({c: s.get("short", s.get("name", c)) for c, s in state.get("cast", {}).items()})
        self.agents = self.statuses(state)
        self.bond_seen.update(e["seq"] for e in state.get("bond_history", []) if "seq" in e)
        self.romances = {tuple(sorted((b["a"], b["b"]))) for b in state.get("bonds", []) if b["kind"] == "romance"}
        lover = state.get("npcs", {}).get("neovi", {}).get("lover")
        if lover:
            self.romances.add(tuple(sorted(("neovi", lover))))
        for c in self.commitment_records(state):
            self.commitments.setdefault(c["id"], (c["status"], {"day": state.get("day"), "source": "starting state"}))
        case = state.get("case") or {}
        if case.get("announced"):
            self.announced.setdefault(case.get("victim"), {"day": state.get("day"), "source": "starting state"})
        for body in state.get("bodies", []):
            self.announced.setdefault(body["victim"], {"day": body.get("day"), "source": "spree body"})

    @staticmethod
    def commitment_records(state):
        records = state.get("commitments") or [c for a in state.get("agents", {}).values()
                                               for c in a.get("commitments", a.get("commitments_view", []))]
        return [c for c in records if isinstance(c, dict) and c.get("id") and c.get("status")]

    @staticmethod
    def statuses(state):
        statuses = {c: a.get("status", "alive") for c, a in state.get("agents", {}).items()}
        for cid, npc in state.get("npcs", {}).items():
            statuses[cid] = "dead" if npc.get("dead") else "departed" if npc.get("room") == "none" else "alive"
        return statuses

    @staticmethod
    def location(tick, source, item=None):
        item = item or {}
        return {"day": tick.get("day"), "hour": tick.get("hour"), "minute": item.get("m"),
                "tick": tick.get("idx"), "source": source, "text": item.get("text", "")}

    def report(self, code, tick, source, item, message, related=None):
        issue = {"code": code, **self.location(tick, source, item), "message": message}
        if related:
            issue["related"] = related
        self.issues.append(issue)

    def inactive(self, cid):
        return cid in self.agents and self.agents[cid] != "alive"

    def actor(self, cid, tick, source, item):
        if not cid:
            return
        self.checks["active_actor"] += 1
        if self.inactive(cid):
            self.report("inactive_actor", tick, source, item,
                        f"{self.names.get(cid, cid)} acts or is addressed after leaving the active cast ({self.agents[cid]}).")

    def feed(self, tick):
        """Consume one completed tick in playback order; return its new issues."""
        before = len(self.issues)
        day, hour = tick.get("day", 0), tick.get("hour", 0)
        events = tick.get("events") or []
        state = tick.get("state") or {}
        for e in events:
            if e.get("story_kind") == "raft_return":
                for cid in e.get("returned", []):
                    if self.agents.get(cid) == "escaped":
                        self.checks["legitimate_return"] += 1
                        self.agents[cid] = "alive"
        for i, e in enumerate(events):
            source = f"events[{i}]"
            kind = e.get("type")
            if kind == "commitment" and e.get("commitment") and e.get("status"):
                key, status = e["commitment"], e["status"]
                if status != "considered":
                    self.checks["commitment_transition"] += 1
                    previous = self.commitments.get(key)
                    if previous and previous[0] != "active":
                        self.report("commitment_reopened" if status == "active" else "duplicate_commitment_end", tick, source, e,
                                    "An ended commitment is reopened or ended again instead of recording a new obligation.", previous[1])
                    if status != "active" and not str(e.get("reason") or "").strip():
                        self.report("unexplained_commitment_end", tick, source, e, "A commitment ended without a recorded reason.")
                    self.commitments[key] = (status, self.location(tick, source, e))
            actor = e.get("actor") or (e.get("who") if kind in ACTIVE_EVENTS else None)
            self.actor(actor, tick, source, e)
            if e.get("actor_status") not in (None, "alive") and not self.inactive(actor):
                self.report("inactive_actor", tick, source, e, "The actor was already inactive when this event was generated.")
            if kind == "body":
                victim = e.get("victim")
                # Legacy recordings did not label the victim on discovery events.
                if not victim:
                    text = e.get("text", "")
                    victim = next((c for c, name in self.names.items() if f"finds {name}" in text), None)
                if victim:
                    self.checks["body_discovery"] += 1
                    key = (victim, e.get("who"))
                    if victim in self.announced:
                        self.report("body_rediscovered", tick, source, e, "An already announced body is discovered as new.", self.announced[victim])
                    elif key in self.found:
                        self.report("duplicate_finder", tick, source, e, "The same person discovers the same body twice.", self.found[key])
                    self.found[key] = self.location(tick, source, e)
            if kind == "madness":
                self.checks["madness_announcement"] += 1
                key = (e.get("who"), e.get("episode", e.get("text", "").strip()))
                now = day * 24 + hour + e.get("m", 0) / 60
                previous = self.madness.get(key)
                if previous and 0 <= now - previous[0] < 72:
                    self.report("repeated_madness", tick, source, e, "The same madness announcement repeats within three days.", previous[1])
                self.madness[key] = (now, self.location(tick, source, e))
            if kind == "occasion" and e.get("stage") == "begin":
                self.checks["host_attendance"] += 1
                if e.get("who") not in e.get("attendees", []) and not e.get("absence_reason"):
                    self.report("absent_host", tick, source, e, "An event begins without its host or a stated reason.")

        for i, b in enumerate(tick.get("broadcasts") or []):
            victim = b.get("victim")
            if victim and b.get("story_kind", b.get("kind")) in ("body", "death_notice", "spree_death"):
                self.checks["body_announcement"] += 1
                source = f"broadcasts[{i}]"
                if victim in self.announced:
                    self.report("duplicate_body_announcement", tick, source, b, "A body's death is announced twice.", self.announced[victim])
                self.announced[victim] = self.location(tick, source, b)

        for gi, group in enumerate(tick.get("talk") or []):
            for li, line in enumerate(group.get("lines") or []):
                source = f"talk[{gi}].lines[{li}]"
                self.actor(line.get("speaker"), tick, source, line)
                self.actor(line.get("to"), tick, source, line)
                if line.get("move") in PRESENT_TOPICS:
                    self.checks["living_topic"] += 1
                    if self.inactive(line.get("about")):
                        self.report("inactive_topic", tick, source, line, "Present-tense gossip or a warning treats a departed person as active.")
                evidence = line.get("evidence")
                if evidence:
                    self.checks["evidence_presenter"] += 1
                    if (line.get("speaker") in evidence.get("named", []) and evidence.get("weight", 0) > 0
                            and line.get("move") != "defence"):
                        self.report("self_incriminating_evidence", tick, source, line, "A presenter offers incriminating evidence naming themselves without defending against it.")
                claim = line.get("claim_at")
                if claim and claim.get("t") is not None:
                    self.checks["consistent_alibi"] += 1
                    key = (line.get("speaker"), claim["t"])
                    previous = self.claims.get(key)
                    room = claim.get("r")
                    lie = bool(claim.get("lie") or claim.get("true") is False)
                    if previous and room and previous[0] != room and not (lie or previous[1]):
                        self.report("contradictory_alibi", tick, source, line, "Two truthful alibis place one person in different rooms at the same time.", previous[2])
                    self.claims[key] = (room, lie, self.location(tick, source, line))

        for c in self.commitment_records(state):
            previous = self.commitments.get(c["id"])
            if previous and previous[0] != "active" and c["status"] == "active":
                self.report("commitment_reopened", tick, "state.commitments", c, "An ended commitment silently became active again.", previous[1])
            if c["status"] != "active" and not c.get("reason"):
                self.report("unexplained_commitment_end", tick, "state.commitments", c, "An ended commitment has no reason.")
            self.commitments[c["id"]] = (c["status"], self.location(tick, "state.commitments", c))

        for event in state.get("bond_changes", state.get("bond_history", [])):
            seq = event.get("seq")
            if seq is None or seq in self.bond_seen:
                continue
            self.bond_seen.add(seq)
            if event["kind"] != "romance":
                continue
            self.checks["romance_transition"] += 1
            pair = tuple(sorted((event["a"], event["b"])))
            if event["action"] == "formed":
                if pair in self.romances:
                    self.report("duplicate_romance", tick, "state.bond_changes", event, "A romance was announced again without ending first.")
                self.romances.add(pair)
            elif event["action"] == "ended":
                self.romances.discard(pair)

        # Compare only against the preceding tick; a person can speak and die in one block.
        for cid, move in (tick.get("moves") or {}).items():
            if move.get("from") != move.get("to") or move.get("from") != "none":
                self.actor(cid, tick, f"moves.{cid}", {})
        for cid, status in self.statuses(state).items():
            self.checks["status_transition"] += 1
            if self.inactive(cid) and status == "alive":
                self.report("resurrection", tick, f"state.agents.{cid}", {}, "A departed participant becomes alive again.")
        if state.get("agents"):
            self.agents = self.statuses(state)
        return self.issues[before:]
