"""The drama layer: occasions, TereVi's meddling, NeoVi's agenda, escape experiments,
romances and feuds, restorative moments, and the confessional booth.

DramaMixin is mixed into DayRunner (engine.py) and uses its helpers (self.world, self.s, self.nm,
self.stat, self.log_event, self.dread_level, ...).
"""
from concurrent.futures import ThreadPoolExecutor

from .data_cast import HOSTS, STORY_BIBLE
from .data_world import ROOMS, CAMERA_BLIND, ISLAND_TRUTHS, COMMON_ITEMS
from .llm import LLMError

OCCASION_SANITY = {"meal": 4, "movie": 4, "party": 5, "game": 3, "concert": 4, "prank": 2, "ritual": 3, "other": 3}
OCCASION_ROOM = {"meal": "dining_hall", "movie": "lounge", "party": "pool", "game": "games_room", "concert": "music_room",
                 "prank": "lounge", "ritual": "garden", "other": "lounge"}
SPECIAL_SANITY = {"comfort": 3, "confession": 3, "romance": 3, "laughter": 3, "gift": 2, "teamwork": 3,
                  "meal": 4, "movie": 4, "party": 5, "prank": 2, "game": 3, "vigil": 4}
SPECIAL_DAILY_CAP = 14         # sanity a person can regain from special moments in one day
GIFT_ITEMS = ["champagne", "spirits", "sweets", "board_game", "candles", "rope", "records", "first_aid_kit"]
TEASE_KINDS = {"whisper", "announce", "dare", "blackout", "gift", "motive"}


def _hh(h):
    return f"{h:02d}:00"


class DramaMixin:
    def drama_init(self, confessionals=True, mischief="occasional"):
        self.confessionals = confessionals
        self.mischief = mischief
        self.proposals = []            # (host id, occasion dict) proposed this turn
        self.experiments = []          # (id, decision) escape experiments this turn
        self.blackout_until = -1       # tick index until which the cameras are dead
        self.interventions_today = 0
        self.occasion_now = None       # the occasion being played out this turn
        self.force_tease = None        # a hint that makes TereVi react this turn
        self.tease_rooms = set()       # rooms where TereVi is talking to someone on the monitor
        self.neovi_log = []            # what NeoVi did and heard today, for her nightly plan

    # ------------------------------------------------------------------ prompt lines
    def extra_decision_lines(self, cid, hour):
        w, s = self.world, self.s
        if not self.revealed:
            return self.intro_decision_lines(cid, hour)
        a = w.agents[cid]
        out = []
        out.append("GOAL: survive. Depending on who you are and who you care about, also help others survive. Murder is a last resort; the honest way out is to contact the outside world "
                   "and convince the audience the show is real (see THE REAL WAY OUT), though the deadline will not wait and desperate people consider other things. "
                   "Experimenting on the way out is only ONE of the things people do here: you also talk, comfort, argue, scheme, investigate, snoop, keep secrets, rest and tend to your own feelings. "
                   "Only run an experiment (action 'experiment' with an 'idea') when you have a genuinely NEW concrete idea.")
        if s.get("rule"):
            blind = ", ".join(ROOMS[r][0] for r in sorted(CAMERA_BLIND))
            out.append(f"RULE-BREAKING: punishment is real but not certain. Cameras cover only the public rooms; the blind spots are: {blind}. "
                       "In a blind spot NeoVi punishes only what she sees herself, and she is not always looking. Break today's rule if the payoff is worth the risk "
                       "(a secret, an advantage, revenge, curiosity, helping someone), especially in a blind spot. You may also try to get someone you despise to break it: "
                       "lure, dare, trick or shove them into it. Cautious people obey.")
        nv = s["npcs"]["neovi"]
        out.append(f"HOSTS: TereVi watches from the monitors in every indoor room and may speak to you or meddle; add 'terevi' to talk_to to address her. "
                   f"NeoVi is in the {w.room_name(nv['room'])}{' (with you)' if nv['room'] == a['room'] else ''}; you can only talk to her when she is in your room.")
        ch = s.get("challenge")
        if ch:
            out.append("TEREVI'S CHALLENGE TODAY: " + ch["text"])
        oc = s.get("occasion")
        if oc and oc["status"] == "announced" and (cid == oc["host"] or cid in oc["invite_ids"]):
            out.append(f"INVITATION: {self.nm(oc['host'])} is hosting a {oc['kind']} in the {w.room_name(oc['where'])} this turn: {oc['text']}. "
                       + ("You are in on a secret prank. " if oc.get("secret_from") else "You are invited. ")
                       + "Go if you want to; a gathering shapes friendships, sparks and trouble.")
        elif not oc and not (s.get("case") and s["case"]["announced"]):
            out.append("SPECIAL OCCASIONS: anyone may host one for the next turn (cook a meal, movie night, game night, beach or pool party, concert, a prank, a ritual...). "
                       "Use the 'host' field. It pulls people together and moves everyone around, which breeds friendships, sparks and mischief (and gives killers a crowd to hide in).")
        b = self.bonds_text(cid)
        if b:
            out.append(b)
        out.extend(self.chaos_decision_lines(cid, hour))
        return out

    def bond_list(self, cid):
        w = self.world
        return [b for b in self.s["bonds"] if cid in (b["a"], b["b"]) and b["a"] in w.agents and b["b"] in w.agents]

    def bonds_text(self, cid):
        parts = []
        for b in self.bond_list(cid):
            other = b["b"] if b["a"] == cid else b["a"]
            parts.append(f"you are in a {dict(romance='ROMANCE', feud='FEUD', pact='PACT (alliance)')[b['kind']]} with {self.nm(other)}")
        return ("BONDS: " + "; ".join(parts) + ".") if parts else ""

    # ------------------------------------------------------------------ cards for TereVi and NeoVi in conversations
    def neovi_card_text(self, group):
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        humans = [p for p in group if p in w.agents]
        feel = ", ".join(f"{self.nm(p)} {nv['aff'].get(p, 0):+d}" for p in humans)
        inv = ", ".join(f"{k} ({w.item_name(k)}) x{q}" for k, q in nv["inv"].items()) or "nothing"
        facts = ""
        case = s.get("case")
        if case and case.get("neovi_facts"):
            facts = (" WHAT YOU KNOW ABOUT THE MURDER (reveal only a little and obscurely, never name the killer outright; you stay neutral and cannot "
                     "interfere with the trial): " + " | ".join(case["neovi_facts"]))
        elif case:
            facts = " A murder happened; you stay neutral and know nothing useful."
        return (f"- neovi = NeoVi, housemaid. {HOSTS['neovi']['persona']} Her fear of TereVi: {nv['fear']}/10. Her secret scheme: {nv['scheme'] or 'none yet'}. "
                f"Feelings toward those present: {feel or 'n/a'}. She can give from her pockets: {inv} (the master key only to someone she trusts completely, +8 or more). "
                f"She speaks rarely, flat and short, and helps only in small, deniable ways when she dares.{facts}")

    def terevi_card_text(self, group):
        w = self.world
        humans = [p for p in group if p in w.agents]
        secrets = " | ".join(f"{self.nm(p)}: {w.cast[p]['secret']}" for p in humans)
        return (f"- terevi = TereVi, the AI host, speaking from the monitor on the wall. {HOSTS['terevi']['persona']} She knows every secret in the room "
                f"({secrets or 'none'}) and may tease, tempt, bargain, threaten or hint to stir up drama; she loves cleverness, hates boredom and never kills on the spot.")

    # ------------------------------------------------------------------ restorative moments, bonds
    def special_boost(self, tick, cid, amount, why, fx_kind=None):
        """Sanity returns only through special moments, capped per person per day."""
        a = self.world.agents.get(cid)
        if not a:
            return
        cap_mult, amt_mult = self.special_scale()
        room = int(SPECIAL_DAILY_CAP * cap_mult) - a.get("special_today", 0)
        amt = min(int(round(amount * amt_mult)), room)
        if amt <= 0:
            return
        a["special_today"] = a.get("special_today", 0) + amt
        self.stat(tick, cid, "sanity", amt, why or "a special moment")
        if fx_kind:
            self.fx(tick, "hearts" if fx_kind in ("romance", "comfort", "confession", "gift") else "confetti", a["room"], cid)

    def baseline_drain(self, tick, hour):
        """Living in the show wears people down: sanity falls every turn and only special moments restore it."""
        if self.step < 2 and (hour - 8) % 2:
            return
        factor = self.drain_factor()                 # recovery comes first after a death
        if factor <= 0:
            return
        for cid, a in list(self.world.agents.items()):
            # numbness: the lower someone already is, the less each quiet hour wears them down
            sa = a["sanity"]
            if self.rng.random() < factor * self.tune("drain_mult") * (1.0 if sa >= 60 else 0.7 if sa >= 35 else 0.4 if sa >= 15 else 0.2):
                self.stat(tick, cid, "sanity", -1 - (1 if a["hp"] < 40 else 0), "")

    def apply_bonds(self, tick, bonds, group):
        w, s = self.world, self.s
        for b in (bonds or [])[:3]:
            try:
                x, y, kind = b["a"], b["b"], b["kind"]
            except Exception:
                continue
            if kind not in ("romance", "feud", "pact") or x == y or x not in w.agents or y not in w.agents or x not in group or y not in group:
                continue
            if any({e["a"], e["b"]} == {x, y} and e["kind"] == kind for e in s["bonds"]):
                continue
            ax, ay = w.agents[x]["aff"].get(y, 0), w.agents[y]["aff"].get(x, 0)
            if kind == "romance" and not (ax >= 5 and ay >= 5):
                continue
            if kind == "feud" and not (ax <= -4 and ay <= -4):
                continue
            if kind == "pact" and not (ax >= 3 and ay >= 3):
                continue
            s["bonds"] = [e for e in s["bonds"] if {e["a"], e["b"]} != {x, y}]
            s["bonds"].append({"a": x, "b": y, "kind": kind, "since": self.day})
            txt = {"romance": f"{self.nm(x)} and {self.nm(y)} are now in a romance.",
                   "feud": f"{self.nm(x)} and {self.nm(y)} are now bitter enemies.",
                   "pact": f"{self.nm(x)} and {self.nm(y)} have sworn a pact to protect each other."}[kind]
            self.log_event(tick, {"type": "system_notable", "who": x, "room": w.agents[x]["room"], "vis": "public", "text": txt},
                           witnesses=w.occupants(w.agents[x]["room"]), actor=x)

    def bond_upkeep(self, tick):
        w, s = self.world, self.s
        keep = []
        for b in s["bonds"]:
            if b["a"] not in w.agents or b["b"] not in w.agents:
                continue
            ax, ay = w.agents[b["a"]]["aff"].get(b["b"], 0), w.agents[b["b"]]["aff"].get(b["a"], 0)
            if b["kind"] == "romance" and min(ax, ay) < 3:
                tick["events"].append({"type": "system_notable", "who": b["a"], "room": "foyer", "vis": "public",
                                       "text": f"The romance between {self.nm(b['a'])} and {self.nm(b['b'])} has cooled."})
                continue
            if b["kind"] == "pact" and min(ax, ay) < 1:
                tick["events"].append({"type": "system_notable", "who": b["a"], "room": "foyer", "vis": "public",
                                       "text": f"The pact between {self.nm(b['a'])} and {self.nm(b['b'])} has dissolved."})
                continue
            if b["kind"] == "feud" and max(ax, ay) > -2:
                tick["events"].append({"type": "system_notable", "who": b["a"], "room": "foyer", "vis": "public",
                                       "text": f"The feud between {self.nm(b['a'])} and {self.nm(b['b'])} has burned out."})
                continue
            keep.append(b)
        s["bonds"] = keep

    def apply_forced_moves(self, tick, moves, group):
        """An action in a scene (a shove, a drag, a lure) can move someone into an adjacent room."""
        w = self.world
        for mv in (moves or [])[:2]:
            try:
                cid, dest = mv["id"], mv["to"]
            except Exception:
                continue
            if cid not in w.agents or cid not in group or dest not in ROOMS:
                continue
            a = w.agents[cid]
            if not any(n["room"] == dest and n["ok"] for n in w.adjacent(cid, a["room"])):
                continue
            start = a["room"]
            a["room"] = dest
            m = tick["moves"].setdefault(cid, {"from": start, "path": [start], "to": start})
            m["path"] = list(m["path"]) + [dest]
            m["to"] = dest
            self.log_event(tick, {"type": "move", "who": cid, "room": start, "vis": "public",
                                  "text": f"{self.nm(cid)} is hauled into the {w.room_name(dest)}."},
                           witnesses=[o for o in w.occupants(start) if o != cid], actor=cid)

    def apply_neovi_gives(self, tick, gv, room, group):
        """NeoVi can hand over small things; the master key only to someone she trusts completely."""
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        to, item = gv.get("to"), gv.get("item")
        if to not in w.agents or to not in group or nv["inv"].get(item, 0) <= 0:
            return
        if item == "master_key" and nv["aff"].get(to, 0) < 8:
            return
        nv["inv"][item] -= 1
        if nv["inv"][item] <= 0:
            del nv["inv"][item]
        w.agents[to]["inv"][item] = w.agents[to]["inv"].get(item, 0) + 1
        self.log_event(tick, {"type": "give", "who": "neovi", "room": room, "vis": "public",
                              "text": f"NeoVi slips {self.nm(to)} the {w.item_name(item)}."}, witnesses=group, actor=to)
        self.neovi_log.append(f"I gave {self.nm(to)} the {w.item_name(item)}.")

    def adjust_any_aff(self, a, b, delta):
        """Relationship change that also works for NeoVi's feelings toward participants."""
        w, s = self.world, self.s
        if a == "neovi" and b in w.agents:
            aff = s["npcs"]["neovi"]["aff"]
            aff[b] = max(-10, min(10, aff.get(b, 0) + int(delta)))
        elif a in w.agents and b in w.agents:
            w.adjust_aff(a, b, delta)

    # ------------------------------------------------------------------ occasions
    def resolve_occasion(self, tick, hour):
        """The occasion announced last turn takes place now if its host and at least one guest are at the venue."""
        w, s = self.world, self.s
        self.occasion_now = None
        oc = s.get("occasion")
        if not oc or oc["status"] != "announced":
            return
        s["occasion"] = None
        host, where = oc["host"], oc["where"]
        if host not in w.agents:
            return
        guests = [c for c, a in w.agents.items() if a["room"] == where and c != host and (c in oc["invite_ids"] or oc["open"])]
        if w.agents[host]["room"] != where:
            self.log_event(tick, {"type": "occasion", "who": host, "room": w.agents[host]["room"], "vis": "public",
                                  "text": f"{self.nm(host)} never made it to their own {oc['kind']}: it falls flat."}, witnesses=list(w.agents), actor=host)
            self.stat(tick, host, "sanity", -2, "ruined plans")
            return
        if not guests:
            self.log_event(tick, {"type": "occasion", "who": host, "room": where, "vis": "public",
                                  "text": f"Nobody comes to {self.nm(host)}'s {oc['kind']} in the {w.room_name(where)}."}, witnesses=[host], actor=host)
            self.stat(tick, host, "sanity", -3, "nobody came")
            return
        attendees = [host] + guests
        self.occasion_now = dict(oc, attendees=attendees)
        self.log_event(tick, {"type": "occasion", "who": host, "room": where, "vis": "public",
                              "text": f"{self.nm(host)}'s {oc['kind']} begins in the {w.room_name(where)} with {len(attendees)} people: {oc['text']}"},
                       witnesses=attendees, actor=host)
        for g in guests:
            self.adjust_any_aff(host, g, 1)
            self.adjust_any_aff(g, host, 1)

    def finish_occasion(self, tick, room, group):
        oc = self.occasion_now
        if not oc or oc["where"] != room:
            return
        base = OCCASION_SANITY.get(oc["kind"], 3)
        if oc["kind"] == "meal":
            self.meal_for(tick, [c for c in oc["attendees"] if c in group])
        for cid in oc["attendees"]:
            if cid in group:
                # the target of a prank gets the scene's own effects instead of a boost
                if oc["kind"] == "prank" and cid in oc.get("secret_from", []):
                    continue
                self.special_boost(tick, cid, base, f"{oc['kind']}", oc["kind"])
        self.day_notable.append(f"{self.nm(oc['host'])} hosted a {oc['kind']} in the {self.world.room_name(room)} ({len(oc['attendees'])} people).")
        self.occasion_now = None

    def queue_occasion(self, tick, hour):
        """Pick one proposal made this turn; it happens next turn."""
        w, s = self.world, self.s
        props, self.proposals = self.proposals, []
        if not props or s.get("occasion"):
            return
        self.rng.shuffle(props)
        for host, p in props:
            if host not in w.agents:
                continue
            kind = p["kind"]
            where = p["where"] if p["where"] in ROOMS else OCCASION_ROOM.get(kind, "lounge")
            kind = "get-together" if kind == "other" else kind
            secret = [x for x in p.get("secret_from", []) if x in w.agents and x != host]
            invite = p.get("invite") or "all"
            if invite == "all":
                invite_ids = [c for c in w.agents if c != host and c not in secret]
                open_ = not secret
            else:
                invite_ids = [c for c in invite if c in w.agents and c != host and c not in secret]
                open_ = False
            oc = {"kind": kind, "where": where, "host": host, "text": p["text"], "invite_ids": invite_ids, "open": open_,
                  "secret_from": secret, "status": "announced", "day": self.day, "hour": hour,
                  "invite": "all" if invite == "all" else invite_ids}
            s["occasion"] = oc
            who = [host] + invite_ids
            if secret:
                self.log_event(tick, {"type": "occasion", "who": host, "room": w.agents[host]["room"], "vis": "gm",
                                      "text": f"{self.nm(host)} plans a secret prank in the {w.room_name(where)} (hidden from {', '.join(self.nm(x) for x in secret)}): {p['text']}"},
                               actor=host)
                for c in invite_ids:
                    w.remember(c, f"{hhmm_(hour)} (private) {self.nm(host)} let you in on a prank in the {w.room_name(where)}: {p['text']}")
            else:
                self.log_event(tick, {"type": "occasion", "who": host, "room": w.agents[host]["room"], "vis": "public",
                                      "text": f"{self.nm(host)} announces a {kind} in the {w.room_name(where)} next turn: {p['text']}"},
                               witnesses=[c for c in who if c != host], actor=host)
            return

    # ------------------------------------------------------------------ TereVi's meddling
    def terevi_intervention(self, tick, hour, forced=None):
        w, s = self.world, self.s
        if (self.mischief == "off" and not forced) or not w.agents:
            return
        if not forced:
            if self.interventions_today >= 3:
                return
            if s.get("case") and s["case"]["announced"] and self.rng.random() < 0.6:
                return                                   # she lets the investigation breathe
            p = {"occasional": 0.18, "frequent": 0.38}.get(self.mischief, 0.18) + 0.04 * self.dread_level()
            if self.rng.random() > p:
                return
        self.interventions_today += 1
        people = []
        for cid, a in w.agents.items():
            c = w.cast[cid]
            known = {k: v for k, v in a["aff"].items() if k in w.agents}
            best = max(known.items(), key=lambda kv: kv[1], default=None)
            worst = min(known.items(), key=lambda kv: kv[1], default=None)
            people.append(f"- {cid} ({c['name']}): in the {w.room_name(a['room'])}, sanity {a['sanity']}, health {a['hp']}; secret: {c['secret']}; "
                          f"closest to {self.nm(best[0]) if best else '?'} ({best[1] if best else 0:+d}), most at odds with {self.nm(worst[0]) if worst else '?'} ({worst[1] if worst else 0:+d})")
        sysm = (f"{self.bible()}\nYou are TereVi. {HOSTS['terevi']['persona']} You are bored and the ratings need drama. Reply with a single JSON object and nothing else.")
        rule = s.get("rule")
        user = (f"Day {self.day}, {_hh(hour)}. Deadline: end of Day {s['deadline_day']} (dread {self.dread_level()}/5). "
                f"Today's rule: {rule['title'] if rule else 'none'}. Active challenge: {s['challenge']['text'] if s.get('challenge') else 'none'}. "
                f"Escape progress: {s['escape']['progress']}/100. Recent drama (for YOUR understanding only; you must never repeat specifics of it to the cast): {'; '.join(self.day_notable[-6:]) or 'nothing yet'}.\n"
                "VAGUE ONLY: you may hint at moods, tensions and the general shape of things ('someone in this house is lying to a friend', 'two of you have a lot to talk about'), "
                "but NEVER tell anyone what a specific person did, said, is carrying or where anyone is, and never state a secret. The cast learns what others do only by seeing it, hearing it from each other or from rumours.\n"
                + (f"HINT: {forced}\n" if forced else "")
                + "THE CAST:\n" + "\n".join(people) + "\n"
                "Choose ONE meddling move that creates drama or an exciting situation, using what you know (secrets, rivalries, fears):\n"
                "- whisper: murmur something unsettling and VAGUE to ONE person (target) on their room's monitor: a hint or a mood, never specifics about anyone\n"
                "- announce: a house-wide twist, game, bounty or dare with stakes\n"
                "- dare: dare ONE person (target) to do something, with a reward or a penalty\n"
                "- blackout: cut the cameras and lights for the next turn\n"
                f"- gift: give ONE person (target) an item from {GIFT_ITEMS} with a sly message\n"
                "- motive: a classic motive video: threaten ONE person (target) with exposing their secret to everyone in a few hours unless they meet a clear demand (a task, a confession, an act of kindness or cruelty)\n"
                'Never kill anyone yourself; stay playful but dangerous. Reply as JSON: {"kind": "whisper|announce|dare|blackout|gift", "target": "<person id or empty>", '
                '"subject": "<person id or empty>", "reveal": true|false, "gift": "<item id, gift only>", "text": "<what you say on air or on the monitor, max 45 words, in your voice>"}')
        try:
            r = self.llm.host_json(sysm, user, {"kind": "tease", "ids": list(w.agents.keys()), "gifts": GIFT_ITEMS})
        except LLMError as e:
            if e.fatal:
                raise
            return
        except Exception:
            return
        kind = r.get("kind")
        text = str(r.get("text", "")).strip()[:380]
        target = r.get("target") if r.get("target") in w.agents else None
        subject = r.get("subject") if r.get("subject") in w.agents else None
        if kind not in TEASE_KINDS or not text:
            return
        if kind in ("whisper", "dare", "gift", "motive") and not target:
            return
        everyone = list(w.agents)
        tick["broadcasts"].append({"speaker": "terevi", "kind": "tease", "text": text})
        hour_ = hhmm_(hour)
        if kind == "whisper":
            room = w.agents[target]["room"]
            self.log_event(tick, {"type": "tease", "who": target, "room": room, "vis": "public",
                                  "text": f"TereVi whispers to {self.nm(target)} from the monitor in the {w.room_name(room)}."},
                           witnesses=[o for o in w.occupants(room) if o != target], actor=target)
            w.remember(target, f"{hour_} TereVi whispered to you: \"{text[:200]}\"")
            if subject and subject != target:
                w.adjust_aff(target, subject, -1)
            self.tease_rooms.add(room)
        elif kind == "dare":
            room = w.agents[target]["room"]
            s["challenge"] = {"text": text, "day": self.day, "who": [target]}
            self.log_event(tick, {"type": "tease", "who": target, "room": room, "vis": "public",
                                  "text": f"TereVi dares {self.nm(target)} on air."}, witnesses=everyone, actor=target)
            for cid in everyone:
                w.remember(cid, f"{hour_} TereVi announced a dare for {self.nm(target)}: \"{text[:200]}\"")
            self.tease_rooms.add(room)
        elif kind == "motive":
            if self.create_threat(tick, hour, target, text):
                th = s["threats"][-1]
                self.log_event(tick, {"type": "tease", "who": target, "room": w.agents[target]["room"], "vis": "public",
                                      "text": f"TereVi threatens to expose {self.nm(target)}'s secret at {_hh(th['due_hour'])} (Day {th['due_day']}) unless they comply."},
                               witnesses=everyone, actor=target)
                for cid in everyone:
                    w.remember(cid, f"{hour_} TereVi's motive video: {self.nm(target)} must comply by {_hh(th['due_hour'])} or their secret is exposed: \"{text[:180]}\"")
                self.fx(tick, "flash", w.agents[target]["room"], target)
                self.stat(tick, target, "sanity", -3, "threatened")
            else:
                tick["broadcasts"].pop()
                self.interventions_today -= 1
                return
        elif kind == "announce":
            s["challenge"] = {"text": text, "day": self.day, "who": everyone}
            self.log_event(tick, {"type": "tease", "who": "terevi", "room": "foyer", "vis": "public",
                                  "text": "TereVi interrupts every monitor with a surprise announcement."}, witnesses=everyone)
            for cid in everyone:
                w.remember(cid, f"{hour_} TereVi announced: \"{text[:220]}\"")
        elif kind == "blackout":
            self.blackout_until = self.idx + 1
            self.log_event(tick, {"type": "tease", "who": "terevi", "room": "foyer", "vis": "public",
                                  "text": "The lights and cameras cut out across the island."}, witnesses=everyone)
            for cid in everyone:
                w.remember(cid, f"{hour_} TereVi cut the lights and cameras. Nobody is watching, for now.")
                self.stat(tick, cid, "sanity", -2, "blackout")
        elif kind == "gift":
            item = r.get("gift") if r.get("gift") in GIFT_ITEMS else self.rng.choice(GIFT_ITEMS)
            a = w.agents[target]
            a["inv"][item] = a["inv"].get(item, 0) + 1
            room = a["room"]
            self.log_event(tick, {"type": "tease", "who": target, "room": room, "vis": "public",
                                  "text": f"A hatch pops open and delivers {w.item_name(item)} to {self.nm(target)}."},
                           witnesses=[o for o in w.occupants(room) if o != target], actor=target)
            w.remember(target, f"{hour_} TereVi sent you {w.item_name(item)} with a message: \"{text[:200]}\"")
            self.tease_rooms.add(room)
        self.day_notable.append(f"TereVi meddled ({kind}): {text[:100]}")

    # ------------------------------------------------------------------ NeoVi
    def neovi_mercy(self, cid):
        """NeoVi sometimes pretends not to see a violation, if she likes the offender."""
        nv = self.s["npcs"]["neovi"]
        fate = (nv.get("arc") or {}).get("fate")
        if fate == "betrayer" or fate == "martyr":
            return False
        if fate == "survivor":
            return True
        if self.neovi_favored(cid) and self.rng.random() < 0.85:
            return True                                   # a small gift bought her silence for the day
        aff = nv["aff"].get(cid, 0)
        p = 0.65 if aff >= 5 else 0.45 if aff >= 3 else 0.2 if aff >= 1 else 0.0
        p += 0.15 if (nv.get("arc") or {}).get("stage", 0) >= 2 and aff >= 2 else 0.0
        p *= max(0.2, 1 - nv["fear"] / 12)
        if self.rng.random() < p:
            nv["fear"] = min(10, nv["fear"] + 1)
            return True
        return False

    def neovi_observe_case(self, case, killer, room, hour):
        """What NeoVi saw of a murder, for her obscure hints."""
        w, s = self.world, self.s
        facts = []
        nroom = s["npcs"]["neovi"]["room"]
        near = nroom == room or any(n["room"] == nroom for n in w.adjacent(killer, room))
        if near:
            facts.append(f"You glimpsed {self.nm(killer)} near the {w.room_name(room)} around {_hh(hour)}.")
        if case.get("trace"):
            facts.append(f"You noticed {w.item_name(case['trace'])} near the body, an item you have seen {self.nm(killer)} carry.")
        case["neovi_facts"] = facts

    def neovi_plan(self, tick):
        """At night NeoVi reflects on the day and updates her scheme and her feelings toward the cast."""
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        feel = ", ".join(f"{self.nm(c)} {nv['aff'].get(c, 0):+d}" for c in w.agents)
        sysm = (f"{self.bible()}\nYou are NeoVi. {HOSTS['neovi']['persona']} Think privately. Reply with a single JSON object and nothing else.")
        user = (f"Day {self.day} is over. Your feelings toward the cast: {feel}. Fear of TereVi: {nv['fear']}/10. Your current scheme: {nv['scheme'] or 'none'}.\n"
                f"What happened to you today: {' | '.join(self.neovi_log[-8:]) or 'a quiet day of chores'}. Deadline in {self.days_left()} day(s).\n"
                'Reply as JSON: {"scheme": "<your secret plan now, 1-2 sentences: how you might free yourself, help someone, or gain something, within what a frightened slave can do>", '
                '"aff": {"<person id>": -2..2}, "diary": "<one private sentence>"}')
        try:
            r = self.llm.neovi_plan(sysm, user, {"ids": list(w.agents.keys())})
        except LLMError as e:
            if e.fatal:
                raise
            return
        except Exception:
            return
        if isinstance(r.get("scheme"), str) and r["scheme"].strip():
            nv["scheme"] = r["scheme"].strip()[:300]
        for cid, d in (r.get("aff") or {}).items():
            if cid in w.agents:
                try:
                    nv["aff"][cid] = max(-10, min(10, nv["aff"].get(cid, 0) + max(-2, min(2, int(d)))))
                except Exception:
                    pass
        if isinstance(r.get("diary"), str) and r["diary"].strip():
            nv["diary"].append(f"Day {self.day}: {r['diary'].strip()[:240]}")
            del nv["diary"][:-4]
        nv["fear"] = max(0, nv["fear"] - 1)
        self.neovi_log = []

    # ------------------------------------------------------------------ escape experiments
    def resolve_experiments(self, tick, hour):
        w, s = self.world, self.s
        exps, self.experiments = self.experiments[:2], []
        if not exps:
            return
        truths = "\n".join("- " + t for t in ISLAND_TRUTHS)
        from .data_world import ESCAPE_ROUTES

        def judge(cid, d):
            a = w.agents[cid]
            c = w.cast[cid]
            room = a["room"]
            dice, why_dice, p = self.experiment_dice(cid, d)
            sysm = ("You are the impartial game master of a sealed-island reality show. The cast is trying to defeat the show by one of several routes. Narrate the experiment's outcome "
                    "faithfully to the DICE ROLL, respecting the TRUTHS: a failure really fails (something breaks, hurts, goes nowhere or alerts TereVi), a partial success moves things a little, "
                    "a success is a real step. Nobody leaves the island in this scene. Reply with a single JSON object and nothing else.")
            routes = " || ".join(f"[{rid}] {r['title']}: " + "; ".join(f"{k} {s['escape']['routes'][rid]['plan'][k]}% = {r['steps'][k]}" for k in r["steps"]) for rid, r in ESCAPE_ROUTES.items())
            user = (f"TRUTHS:\n{truths}\nROUTES AND STEPS (percent complete): {routes}\n"
                    f"EXPERIMENTER: {c['name']} ({c['role']}). Traits: {c['persona'][:200]} Health {a['hp']}, sanity {a['sanity']} (the worse, the more mistakes).\n"
                    f"Location: {w.room_name(room)}. Carrying: {self.items_text(a['inv'])}. Items here: {self.items_text(s['room_items'].get(room, {}))}. Common supplies here: {', '.join(w.item_name(k) for k in COMMON_ITEMS.get(room, [])) or 'none'}.\n"
                    "ITEM RULE: the experimenter can only use what is carried, lies here or is a common supply here; anything else does not exist, so an idea that needs it fails or must be improvised from what is there.\n"
                    f"What the cast has learned so far: {' | '.join(x['text'] for x in s['escape']['clues'][-4:]) or 'nothing'}. IDEA: {d['idea']}\n"
                    f"DICE ROLL: {dice.upper()}{' (' + why_dice + ')' if why_dice else ''} (odds were {int(p * 100)}%). "
                    + ("Gain must be 0 and a real setback (damage, a broken tool, a noise TereVi hears) is likely." if dice == "failure" else
                       "Gain is small." if dice == "partial" else "Gain can be meaningful.")
                    + '\nReply as JSON: {"route": "transmit|shutdown|raft|ultimatum|none", "step": "<step name of that route, or none>", "gain": 0..30, '
                      '"outcome": "<1-2 vivid sentences of what happens>", "learned": "<one concrete fact the experimenter learns, or empty>", '
                      '"hp": 0..-15, "sanity": -5..2, "alert_terevi": true|false}')
            r = self.llm.adjudicate(sysm, user, {"cid": cid})
            r["_dice"] = dice
            return r

        with ThreadPoolExecutor(max_workers=2) as pool:
            futs = [(cid, d, pool.submit(judge, cid, d)) for cid, d in exps if cid in w.agents]
            for cid, d, fut in futs:
                try:
                    r = fut.result()
                except LLMError as e:
                    if e.fatal:
                        raise
                    tick["errors"].append(f"experiment judging failed: {str(e)[:80]}")
                    continue
                except Exception:
                    continue
                self.apply_experiment(tick, cid, d, r, hour)

    def apply_experiment(self, tick, cid, d, r, hour):
        w, s = self.world, self.s
        a = w.agents.get(cid)
        if not a:
            return
        dice = r.get("_dice", "partial")
        outcome = str(r.get("outcome", "")).strip()[:300] or "Nothing much comes of it."
        room = a["room"]
        here = [o for o in w.occupants(room) if o != cid]
        self.log_event(tick, {"type": "experiment", "who": cid, "room": room, "vis": "public",
                              "text": f"{self.nm(cid)} experiments ({d['idea'][:90]}): {outcome}"}, witnesses=here, actor=cid)
        self.tally(cid, "experiments")
        for key, lo, hi in (("hp", -9, 0), ("sanity", -5, 2)):
            try:
                v = max(lo, min(hi, int(r.get(key, 0))))
            except Exception:
                v = 0
            if dice == "success":
                v = self.rng.randint(2, 6) if key == "hp" else self.rng.randint(2, 5)         # a win feels like one: a lift in health and in spirits
            elif dice == "partial" and key == "sanity" and v <= 0:
                v = 1
            elif dice == "failure" and key == "hp" and v == 0 and self.rng.random() < 0.4:
                v = -self.rng.randint(1, 5)
            if v:
                self.stat(tick, cid, key, v, "experiment", lethal=("died in a failed experiment" if key == "hp" else None))
                if cid not in w.agents:
                    return
        if dice == "failure" and any(k in str(d.get("idea", "")).lower() for k in ("explosive", "fuel", "chlorine", "bomb", "fire", "burn")) and self.rng.random() < 0.18:
            self.env_ignite_room(tick, w.agents[cid]["room"], f"The experiment goes wrong in the {w.room_name(w.agents[cid]['room'])}: something catches fire.")
        learned = str(r.get("learned", "")).strip()[:200]
        if learned and dice != "failure":
            w.remember(cid, f"{hhmm_(hour)} (learned) {learned}")
            s["escape"]["clues"].append({"by": cid, "text": learned, "day": self.day})
            del s["escape"]["clues"][:-12]
        before, after, rid, step, gain = self.escape_apply(tick, cid, d, r, hour, dice)
        crossed = [t for t in (30, 60, 90, 100) if before < t <= after]
        if rid and step and gain:
            self.log_event(tick, {"type": "system_notable", "who": cid, "room": room, "vis": "viewer",
                                  "text": f"Way out ({rid}): {step} +{gain}% (now {s['escape']['routes'][rid]['plan'][step]}%)."}, actor=cid)
        elif dice == "failure":
            self.log_event(tick, {"type": "system", "who": cid, "room": room, "vis": "gm", "text": f"{self.nm(cid)}'s experiment failed."}, actor=cid)
        if crossed:
            self.force_tease = f"The cast is getting closer to getting out (best route at {after}%). React, in character, with a countermeasure or a mocking threat."
        elif r.get("alert_terevi") is True:
            self.force_tease = f"{self.nm(cid)} just tried something suspicious ({d['idea'][:80]}). React as you see fit."

    # ------------------------------------------------------------------ the confessional booth
    def make_confessionals(self, tick, hour):
        w, s = self.world, self.s
        if not self.confessionals or not w.agents:
            return
        score = {}
        for e in tick["events"]:
            who = e.get("who")
            if who not in w.agents:
                continue
            t = e["type"]
            score[who] = score.get(who, 0) + {"punish": 4, "attack": 6, "experiment": 3, "occasion": 2, "tease": 3,
                                              "body": 5, "system_notable": 3, "give": 1, "discover": 2, "mercy": 2, "madness": 4, "assault": 5, "betrayal": 6,
                                              "leak": 4, "outburst": 4, "sabotage": 3}.get(t, 0)
        for g in tick["talk"]:
            for l in g["lines"]:
                if l["speaker"] in w.agents:
                    score[l["speaker"]] = score.get(l["speaker"], 0) + 0.5
        for pc, pl in s.get("plots", {}).items():
            if pc in w.agents:
                score[pc] = score.get(pc, 0) + (7 if pl.get("stage") in ("stalking", "striking") else 4)
        ranked = sorted(score.items(), key=lambda kv: -kv[1])
        chosen = [c for c, v in ranked if v >= 3.5][:1] + [c for c, v in ranked[1:2] if v >= 7]
        if not chosen:
            pool = [c for c in score if score[c] > 0] or list(w.agents)
            if self.rng.random() < 0.2:
                chosen = [self.rng.choice(pool)]
        if not chosen:
            return
        cards = []
        for cid in chosen:
            a, c = w.agents[cid], w.cast[cid]
            known = {k: v for k, v in a["aff"].items() if k in w.agents}
            ranked = sorted(known.items(), key=lambda kv: kv[1])
            bits = []
            if ranked:
                bits.append(f"warmest to {self.nm(ranked[-1][0])} ({ranked[-1][1]:+d})")
                bits.append(f"coldest to {self.nm(ranked[0][0])} ({ranked[0][1]:+d})")
            cards.append(f"- {cid} = {c['name']} ({c['role']}). Voice: {c['speech']} Secret: {c['secret']} Mood: health {a['hp']}, sanity {a['sanity']} ({self.mood_text(a)}). "
                         f"Feelings: {', '.join(bits)}. {self.bonds_text(cid)} Thought this turn: {tick['thoughts'].get(cid, '')} "
                         + (f"SECRET PLOT: planning to kill {self.nm(s['plots'][cid]['target'])} ({s['plots'][cid]['stage']}); method {s['plots'][cid]['method'] or 'undecided'}; cover: {s['plots'][cid]['cover'] or 'none'} "
                            "(they talk about it candidly: the plan, the doubts, the cold calm or the shaking hands). " if cid in s.get("plots", {}) else "")
                         + self.lost_lines(cid)[:160] + " "
                         f"Recent: {' | '.join(a['memory']['recent'][-6:]) or 'nothing'}")
        sysm = (f"{self.bible()}\nYou write CONFESSIONAL-BOOTH entries for a reality show: a character alone with the camera, candid in a way they never are in front of the others. "
                "Reply with a single JSON object and nothing else.")
        user = (f"Day {self.day}, {_hh(hour)}. Write one confessional for each person below: they speak straight to the camera in their own voice, 25 to 55 words, "
                "honest about what they really feel, fear, want or plan (crushes, schemes, doubts, suspicions, even things nobody knows), reacting to what just happened to them.\n"
                + "\n".join(cards) + '\nReply as JSON: {"entries": [{"id": "<person id>", "text": "..."}]}')
        try:
            r = self.llm.confess(sysm, user, {"ids": chosen, "lines": {c: w.cast[c].get("mock_lines", []) for c in chosen}})
        except LLMError as e:
            if e.fatal:
                raise
            return
        except Exception:
            return
        out = []
        for en in (r.get("entries") or [])[:3]:
            if isinstance(en, dict) and en.get("id") in w.agents and str(en.get("text", "")).strip():
                out.append({"id": en["id"], "text": str(en["text"]).strip()[:420]})
        if out:
            tick["confessionals"] = out

    # ------------------------------------------------------------------ night
    def night_recovery(self, tick):
        """Ways sanity comes back besides special moments: a night beside someone who cares, a vigil, NeoVi's tea, plain rest."""
        w, s = self.world, self.s
        nv = s["npcs"]["neovi"]
        mourners = [c for c, a in w.agents.items() if any(x.get("day") == self.day for x in a["memory"].get("lost", []))]
        vigil_done = set()
        for cid, a in w.agents.items():
            mates = [o for o in w.agents if o != cid and w.agents[o]["room"] == a["room"]]
            best = max((min(a["aff"].get(o, 0), w.agents[o]["aff"].get(cid, 0)) for o in mates), default=-10)
            gain, why = 0, []
            if best >= 6:
                gain, why = gain + 5, why + ["a night beside someone they love"]
            elif best >= 3:
                gain, why = gain + 3, why + ["a night beside a friend"]
            if a.get("slept_where") == "home" and a.get("slept", True):
                gain, why = gain + 1, why + ["their own bed"]
            if a["hp"] >= 50 and a.get("slept", True) and a["sanity"] < 85:
                gain, why = gain + 2, why + ["a night's sleep"]
            if nv["aff"].get(cid, 0) >= 4:
                gain, why = gain + 2, why + ["tea from NeoVi"]
            if cid in mourners and cid not in vigil_done:
                partner = next((o for o in mourners if o != cid and min(a["aff"].get(o, 0), w.agents[o]["aff"].get(cid, 0)) >= 3), None)
                if partner:
                    gain, why = gain + 4, why + [f"keeping vigil with {self.nm(partner)}"]
                    vigil_done.add(cid)
            if gain:
                self.stat(tick, cid, "sanity", gain, ", ".join(why))
                self.moment(cid, "found some comfort in the dark") if gain >= 6 else None

    def drama_night(self, tick):
        w, s = self.world, self.s
        self.bond_upkeep(tick)
        for a in w.agents.values():
            a["special_today"] = 0
            a["comfort_today"] = 0
        s["occasion"] = None
        s["challenge"] = None
        s["island"] = None
        self.story_night(tick)
        self.night_recovery(tick)
        self.aftermath_night(tick)
        for cid_, a_ in w.agents.items():
            h_ = s.setdefault("san_hist", {}).setdefault(cid_, [])
            h_.append([self.day, a_["sanity"], a_["hp"]])
            del h_[:-40]
        if w.agents and s["npcs"]["neovi"].get("room") != "none":
            self.neovi_plan(tick)
            self.neovi_arc_night(tick)
        self.death_today = False
        self.make_recap(tick)


def hhmm_(h):
    return f"{h:02d}:00"
