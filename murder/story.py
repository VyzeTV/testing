"""The story layer: Day 1 introductions and the reveal, the Reckoning, murder plots, manipulation, rumours,
defining memories, slip-ups, the concrete escape plan (contact the outside world) and the director's tools.

StoryMixin is mixed into DayRunner (engine.py) next to CaseMixin, DramaMixin and ChaosMixin.
"""
from .data_cast import STORY_BIBLE, STORY_BIBLE_INTRO, HOSTS
from . import scenario as scn
from .data_world import ROOMS
from .llm import LLMError
from .world import clamp, week_of
from .plotting import STAGES

STAGE_RANK = {k: i for i, k in enumerate(STAGES)}

PLOT_STAGES = ("brooding", "preparing", "stalking", "striking")
INCITE_VERB = {"persuade": "talked at you at length", "trick": "told you something (it may be a lie)",
               "blackmail": "leaned on you with something they know", "lure": "baited you into a corner"}


def _hh(h):
    return f"{h:02d}:00"


class StoryMixin:
    def story_init(self, gm_pull=None, variation=0):
        self.end_lives = []
        self.gm_pull = gm_pull or (lambda: [])
        self.variation = max(0, min(100, int(variation or 0)))
        self.intro_done = False
        self.reveal_text = ""
        self.force_island = None
        self.last_effects = {}
        self.last_call_done = False
        self.s.setdefault("_hour", 8)

    # ------------------------------------------------------------------ switches
    @property
    def murders(self):
        return bool(getattr(self, "_murders_cfg", True)) and bool(self.world.state.get("revealed", True))

    @murders.setter
    def murders(self, v):
        self._murders_cfg = v

    @property
    def revealed(self):
        return bool(self.world.state.get("revealed", True))

    def bible(self):
        return ((STORY_BIBLE if self.revealed else STORY_BIBLE_INTRO) + scn.bible_extra(self.s.get("scenario"), self.revealed)
                + ("\nEVIDENCE: the house cameras are TereVi's; nobody in the cast can see their footage. Only cite a recording if you really have one "
                   "(a still NeoVi showed you, a tape or a camera of your own) and say where it came from." if self.revealed else ""))

    def house_rules(self):
        sc = self.s.get("scenario")
        return list(sc.get("rules", [])) if (sc and self.revealed) else []

    def house_line(self):
        hr = self.house_rules()
        return ("STANDING HOUSE RULES (always in force; NeoVi punishes clear violations): " + " | ".join(hr) + "\n") if hr else ""

    def house_stub(self):
        if not hasattr(self, "_house_stub"):
            self._house_stub = {"id": "house", "title": "House Rules", "strikes": {}}
        return self._house_stub

    def scenario_twist(self, tick, hour):
        """The scenario's secret twist: TereVi announces it on its day and from then on it is part of the story."""
        sc = self.s.get("scenario")
        tw = (sc or {}).get("twist")
        if not tw or tw.get("done") or not self.revealed or self.day < int(tw.get("day") or 99):
            return
        w = self.world
        text = self.make_broadcast("twist", {"text": tw["text"]})
        tw["done"] = True
        tick["broadcasts"].append({"speaker": "terevi", "kind": "tease", "text": text})
        for cid in w.agents:
            w.remember(cid, f"{_hh(hour)} TereVi announced a TWIST: {tw['text'][:200]}")
        self.log_event(tick, {"type": "system_notable", "who": "terevi", "room": "foyer", "vis": "public", "text": f"A TWIST: {tw['text']}"})
        self.fx(tick, "flash")
        self.saga(f"Twist: {tw['text'][:100]}")
        self.day_notable.append(f"A twist was announced: {tw['text'][:80]}")

    # ------------------------------------------------------------------ memories
    def tally(self, cid, key, n=1):
        """Season statistics per character."""
        st = self.s.setdefault("stats", {}).setdefault(cid, {})
        st[key] = st.get(key, 0) + n

    def moment(self, cid, text):
        a = self.world.agents.get(cid)
        if not a:
            return
        m = a["memory"].setdefault("moments", [])
        line = f"Day {self.day}: {text}"[:170]
        if line not in m:
            m.append(line)
            del m[:-12]

    def saga(self, text):
        sg = self.s.setdefault("saga", [])
        sg.append(f"Day {self.day}: {text}"[:200])
        del sg[:-24]

    def moments_lines(self, cid):
        m = self.world.agents[cid]["memory"].get("moments", [])[-(3 if self.lean else 5):]
        return ("DEFINING MOMENTS (you never forget these; they colour how you feel and act): " + " | ".join(m)) if m else ""

    # ------------------------------------------------------------------ slip-ups
    def slip_chance(self, cid):
        a = self.world.agents.get(cid) or self.world.all_agents.get(cid)
        if not a:
            return 0.0
        p = max(0, 55 - a["sanity"]) / 55 * 0.40 + max(0, 55 - a["hp"]) / 55 * 0.25
        if a.get("conds"):
            p += self.cond_slip(cid)
        return min(0.55, p)

    def condition_line(self, cid):
        p = self.slip_chance(cid)
        if p < 0.08:
            return ""
        level = "very" if p > 0.3 else "fairly"
        return (f"CONDITION: with your sanity and health you are {level} error-prone. You misjudge, fumble, mix up names and times, say too much, hit the wrong person, "
                "hit harder than you meant, leave traces behind or lose track of your own story. Make believable mistakes now and then, and let them cost you.")

    # ------------------------------------------------------------------ who touched what
    def init_item_log(self):
        log = self.s.setdefault("item_log", {})
        for cid, a in self.world.agents.items():
            for it in a["inv"]:
                if not any(x[0] == cid for x in log.get(it, [])):
                    log.setdefault(it, []).append([cid, self.day, 8])
                    del log[it][:-6]

    def note_holder(self, cid, item, hour):
        log = self.s.setdefault("item_log", {}).setdefault(item, [])
        log.append([cid, self.day, hour])
        del log[:-6]

    # ------------------------------------------------------------------ murder plots
    def clean_plot(self, raw):
        if not isinstance(raw, dict):
            return None
        t = raw.get("target")
        if t not in self.world.agents:
            return None
        stage = raw.get("stage") if raw.get("stage") in PLOT_STAGES else "brooding"
        return {"target": t, "stage": stage, "method": str(raw.get("method") or "")[:70],
                "step": str(raw.get("step") or "")[:130], "cover": str(raw.get("cover") or "")[:130]}

    def update_plots(self, tick, decisions, hour):
        """Record each plotter's declared plot so the audience can watch it unfold."""
        w, s = self.world, self.s
        if not self.murders:
            return
        plots = s.setdefault("plots", {})
        for cid, d in decisions.items():
            if cid not in w.agents or "plot_given" not in d:
                continue
            if not d["plot_given"]:
                continue
            new = d.get("plot")
            old = plots.get(cid)
            name = self.nm(cid)
            if new is None:
                if old:
                    del plots[cid]
                    self.log_event(tick, {"type": "plot", "who": cid, "room": w.agents[cid]["room"], "vis": "viewer",
                                          "text": f"{name} gives up the plan to kill {self.nm(old['target'])}."}, actor=cid)
                continue
            if new["target"] == cid:
                continue
            room = w.agents[cid]["room"]
            if not old or old["target"] != new["target"]:
                plots[cid] = self.plot_defaults(dict(new, log=[], quiet=0, since=f"Day {self.day} {_hh(hour)}", origin="model"))
                self.plan_note(plots[cid], f"began to plan {self.nm(new['target'])}'s death")
                self.log_event(tick, {"type": "plot", "who": cid, "room": room, "vis": "viewer",
                                      "text": f"{name} is plotting to kill {self.nm(new['target'])} ({new['stage']}): {(new['step'] or new['method'] or 'brooding').rstrip('.')}"
                                              + (f". Cover: {new['cover']}" if new["cover"] else "")}, actor=cid)
                self.moment(cid, f"decided {self.nm(new['target'])} must die")
                self.tally(cid, "plots")
            else:
                changed = new["stage"] != old["stage"] or (new["step"] and new["step"] != old["step"])
                old.update({k: new[k] for k in ("method", "cover") if new[k]})
                if STAGE_RANK.get(new["stage"], 0) > STAGE_RANK.get(old["stage"], 0):
                    old["stage"], old["stage_ticks"] = new["stage"], 0
                if new["step"]:
                    old["step"] = new["step"]
                old["quiet"] = 0
                if changed:
                    self.log_event(tick, {"type": "plot", "who": cid, "room": room, "vis": "viewer",
                                          "text": f"{name} ({old['stage']}) against {self.nm(old['target'])}: {old['step'] or old['method']}"}, actor=cid)
            p = plots[cid]
            if p["step"]:
                p["log"].append(f"{_hh(hour)} {p['step']}"[:140])
                del p["log"][:-6]
            # the plotter's tells: someone may notice odd behaviour, and remembers it
            tell = {"brooding": None, "preparing": f"{name} was oddly secretive, fiddling with something and hiding it when you looked",
                    "stalking": f"{name} kept watching {self.nm(p['target'])} with an unsettling stillness",
                    "striking": f"{name} looked dead serious around {self.nm(p['target'])}, as if waiting for something"}[p["stage"]]
            if tell:
                for o in w.occupants(room):
                    if o in w.agents and o != cid and o != p["target"] and self.rng.random() < 0.3:
                        w.remember(o, f"{_hh(hour)} (odd) {tell}.")
                        self.note_odd(cid, o, hour)
        for cid in list(plots):
            t_ = plots[cid]["target"]
            if cid in w.agents and (t_ not in w.agents or w.agents[cid]["aff"].get(t_, 0) >= 5):
                self.log_event(tick, {"type": "plot", "who": cid, "room": w.agents[cid]["room"], "vis": "viewer",
                                      "text": f"{self.nm(cid)} no longer wants {self.nm(t_)} dead." if t_ in w.agents else f"{self.nm(cid)}'s target is gone, and the plan dies with it."}, actor=cid)
                del plots[cid]
        # plots now live on across turns and days (see plotting.py); they end when abandoned, when the target is gone, or in a strike

    def plot_lines(self, cid):
        w, s = self.world, self.s
        if not self.murders:
            return []
        out = []
        p = s.get("plots", {}).get(cid)
        if p and p["target"] in w.agents:
            t = p["target"]
            room = w.agents[cid]["room"]
            humans = [o for o in w.occupants(room) if o in w.agents]
            out.append(f"YOUR PLOT: you are secretly planning to kill {self.nm(t)} (stage: {p['stage']}; method: {p['method'] or 'undecided'}; "
                       f"cover: {p['cover'] or 'none yet'}). Steps so far: {' | '.join(p['log'][-3:]) or 'none'}. Keep your plot consistent turn to turn, or drop it (\"plot\": null).")
            if t in humans:
                alone = len(humans) == 2
                out.append(f"OPPORTUNITY: {self.nm(t)} is in the room with you, {'alone with you' if alone else 'with ' + str(len(humans) - 2) + ' other(s) around'}. "
                           "Strike now only if you are ready: weapon, witnesses, cameras (blind spots), your alibi and what you will say afterwards. "
                           "You may also try to frame someone with planted evidence (attack with 'frame'), but a careful investigator may see through it.")
        out.append("PLOTTING A KILL: if you are seriously planning to kill someone (fear, rage, the deadline, a threat, a plan to save others by sacrificing one), declare it in \"plot\" "
                   "(target, stage brooding|preparing|stalking|striking, method, this turn's step, cover). The audience watches your plot unfold. Most days nobody plots. "
                   "Whoever delivers the killing blow is the culprit, even if they were manipulated or it was a mistake.")
        return out

    # ------------------------------------------------------------------ manipulation
    def apply_incite(self, tick, items, group, hour):
        """Someone works on another person to hurt or kill a third (persuade, trick, blackmail, lure)."""
        w, s = self.world, self.s
        if not self.murders:
            return
        for it in (items or [])[:2]:
            try:
                by, target, victim = it["by"], it["target"], it["victim"]
            except Exception:
                continue
            if not (by in w.agents and target in w.agents and victim in w.agents) or len({by, target, victim}) < 3 or by not in group or target not in group:
                continue
            how = it.get("how") if it.get("how") in INCITE_VERB else "persuade"
            claim = str(it.get("claim") or "")[:140]
            a = w.agents[target]
            p = 0.3 + (0.25 if a["aff"].get(by, 0) >= 3 else 0) + (0.2 if a["sanity"] < 50 else 0) + (0.15 if how in ("trick", "blackmail") else 0)
            if a["aff"].get(victim, 0) >= 5:
                p -= 0.3
            p = max(0.05, min(0.85, p))
            room = a["room"]
            if self.rng.random() >= p:
                self.log_event(tick, {"type": "incite", "who": by, "room": room, "vis": "gm",
                                      "text": f"{self.nm(by)} tries to turn {self.nm(target)} against {self.nm(victim)} ({how}) and fails."}, actor=by)
                w.remember(target, f"{_hh(hour)} (private) {self.nm(by)} tried to push you toward harming {self.nm(victim)}: {claim or 'no reason given'}. You did not bite.")
                self.adjust_any_aff(target, by, -1)
                continue
            s.setdefault("incitements", []).append({"by": by, "target": target, "victim": victim, "how": how, "claim": claim, "day": self.day, "ttl": 3})
            w.remember(target, f"{_hh(hour)} (private) {self.nm(by)} {INCITE_VERB[how]}: {claim or victim + ' deserves it'}. You cannot stop thinking about it.")
            w.remember(by, f"{_hh(hour)} (private) You worked on {self.nm(target)} to act against {self.nm(victim)} ({how}).")
            self.log_event(tick, {"type": "incite", "who": by, "room": room, "vis": "viewer",
                                  "text": f"{self.nm(by)} is working on {self.nm(target)}, turning them against {self.nm(victim)} ({how})."}, actor=by)
            self.moment(target, f"{self.nm(by)} got into your head about {self.nm(victim)}")
            self.tally(by, "manipulations")
            for o in group:
                if o in w.agents and o not in (by, target) and self.rng.random() < 0.35:
                    w.remember(o, f"{_hh(hour)} (overheard) {self.nm(by)} was murmuring to {self.nm(target)} about {self.nm(victim)}.")

    def incite_lines(self, cid):
        out = []
        for inc in self.s.get("incitements", []):
            if inc["ttl"] <= 0 or inc["target"] not in self.world.agents:
                continue
            if inc["target"] == cid and inc["victim"] in self.world.agents:
                out.append(f"{self.nm(inc['by'])} has been working on you ({inc['how']}): {inc['claim'] or 'that ' + self.nm(inc['victim']) + ' deserves it'}. "
                           f"You are tempted to hurt or kill {self.nm(inc['victim'])}; you can act on it (assault or attack) or see through it. If you do it, YOU are the one responsible.")
            elif inc["by"] == cid:
                out.append(f"You have been working on {self.nm(inc['target'])} against {self.nm(inc['victim'])}; you keep your own hands clean and watch.")
        return out

    def tick_incitements(self):
        """Incited people feel a pull toward violence for a few turns."""
        w = self.world
        for inc in self.s.get("incitements", []):
            inc["ttl"] -= 1
            if inc["ttl"] > 0 and inc["target"] in w.agents and inc["victim"] in w.agents and self.rng.random() < 0.6:
                lvl = max(3, self.impulses.get(inc["target"], {}).get("level", 0))
                self.impulses[inc["target"]] = {"kind": "hurt", "target": inc["victim"], "level": lvl, "incited": inc["by"]}
        self.s["incitements"] = [i for i in self.s.get("incitements", []) if i["ttl"] > -6]

    # ------------------------------------------------------------------ rumours
    def spread_rumor(self, tick, by, about, claim, tone, lie, recipients, room, hour):
        w, s = self.world, self.s
        claim = str(claim or "").strip()[:140]
        if about not in w.cast or not claim:
            return False
        heard = []
        for c in recipients:
            if c not in w.agents or c in (about, by):
                continue
            trust = w.agents[c]["aff"].get(by, 0) if by in w.agents else 0
            src = self.nm(by) if by in w.cast else "an unknown source"
            w.remember(c, f"{_hh(hour)} (rumor, from {src}) {self.nm(about)}: {claim}")
            self.belief_rumor(c, by, about, claim, lie)
            if trust >= 0 and about in w.agents[c]["aff"]:
                self.adjust_any_aff(c, about, -1 if tone == "bad" else 1)
            heard.append(c)
        if not heard:
            return False
        s.setdefault("rumors", []).append({"by": by, "about": about, "claim": claim, "tone": tone, "lie": bool(lie), "day": self.day, "heard": heard})
        del s["rumors"][:-20]
        if by in w.agents:
            self.tally(by, "rumors")
        who = self.nm(by) if by in w.cast else "Someone"
        self.log_event(tick, {"type": "rumor", "who": by if by in w.agents else about, "room": room, "vis": "viewer",
                              "text": f"{who} spreads a rumor about {self.nm(about)}: {claim}" + (" (it is a lie)" if lie else "")}, actor=None)
        return True

    def apply_rumors(self, tick, items, group, hour):
        for it in (items or [])[:2]:
            if not isinstance(it, dict):
                continue
            by, about = it.get("by"), it.get("about")
            if by not in group or about not in self.world.cast:
                continue
            self.spread_rumor(tick, by, about, it.get("claim"), "good" if it.get("tone") == "good" else "bad", it.get("lie") is True,
                              [g for g in group if g in self.world.agents], self.world.agents[by]["room"], hour)

    def rumor_lines(self, cid):
        out = []
        for r in self.s.get("rumors", [])[-8:]:
            if cid in r["heard"]:
                out.append(f"{self.nm(r['about'])}: {r['claim']}")
        return ("RUMORS YOU HAVE HEARD (they may be true or false): " + " | ".join(out[-3:]) + ". Believe, test, confront or pass them on as you see fit.") if out else ""

    # ------------------------------------------------------------------ avoiding repetition
    def note_acts(self, cid, text):
        a = self.world.agents.get(cid)
        if not a or not text:
            return
        ra = a.setdefault("recent_acts", [])
        ra.append(str(text)[:60].lower())
        del ra[:-10]

    def repeat_lines(self, cid):
        a = self.world.agents.get(cid)
        ra = (a or {}).get("recent_acts", [])
        if len(ra) < 3:
            return ""
        words = {}
        for t in ra:
            for wd in dict.fromkeys(t.replace(",", " ").split()):          # each word once per act, in order (a set would order them by hash)
                if len(wd) > 4:
                    words[wd] = words.get(wd, 0) + 1
        stale = [wd for wd, n in sorted(words.items(), key=lambda kv: -kv[1]) if n >= 3][:5]
        if not stale:
            return ""
        return f"NOVELTY: you keep doing the same sort of thing lately (words that keep recurring: {', '.join(stale)}). Do something DIFFERENT this time: another place, another person, another idea."

    # ------------------------------------------------------------------ factions
    def update_factions(self):
        w, s = self.world, self.s
        parent = {c: c for c in w.agents}

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x
        kinds = {}
        for b in s["bonds"]:
            if b["kind"] in ("pact", "romance") and b["a"] in parent and b["b"] in parent:
                parent[find(b["a"])] = find(b["b"])
                kinds.setdefault(find(b["a"]), set()).add(b["kind"])
        groups = {}
        for c in parent:
            groups.setdefault(find(c), []).append(c)
        out = []
        for root, mem in groups.items():
            if len(mem) >= 2:
                names = [self.nm(m) for m in mem]
                label = (f"{names[0]} & {names[1]}" + (" (lovers)" if "romance" in set().union(*[kinds.get(find(m), set()) for m in mem]) else " alliance")) if len(mem) == 2 \
                    else f"The {names[0]} circle ({', '.join(names)})"
                out.append({"name": label, "members": mem})
        s["factions"] = out

    def faction_line(self, cid):
        for f in self.s.get("factions", []):
            if cid in f["members"] and len(f["members"]) >= 3:
                return f"FACTION: you belong to {f['name']}. They expect loyalty; rumours spread fast among them."
        return ""

    # ------------------------------------------------------------------ the director's tools
    def apply_gm(self, tick, hour):
        w, s = self.world, self.s
        items = list(s.get("gm_pending", [])) + list(self.gm_pull() or [])
        s["gm_pending"] = []
        for it in items[:6]:
            t = it.get("type")
            try:
                if t == "rumor":
                    to = it.get("to")
                    rec = list(w.agents) if to in (None, "", "all") else [x for x in (to if isinstance(to, list) else [to]) if x in w.agents]
                    self.spread_rumor(tick, "unknown", it["about"], it["claim"], "bad" if it.get("tone", "bad") == "bad" else "good", it.get("lie", False), rec, "foyer", hour)
                elif t == "item":
                    room = it["room"]
                    name = str(it["name"]).strip()[:40]
                    if room in ROOMS and name:
                        iid = f"gm_{len(s['custom_items']) + 1}"
                        s["custom_items"][iid] = {"name": name, "tags": ["gear"]}
                        s["room_items"].setdefault(room, {})[iid] = 1
                        self.log_event(tick, {"type": "system", "who": "terevi", "room": room, "vis": "gm", "text": f"Director: a {name} appears in the {w.room_name(room)}."})
                elif t == "whisper":
                    to, text = it["to"], str(it["text"]).strip()[:240]
                    if to in w.agents and text:
                        w.remember(to, f"{_hh(hour)} You find an unsigned note: \"{text}\"")
                        self.moment(to, f"found a mysterious note: {text[:80]}")
                        self.log_event(tick, {"type": "system", "who": to, "room": w.agents[to]["room"], "vis": "gm", "text": f"Director whispers to {self.nm(to)}: {text}"})
                elif t == "schedule":
                    self.gm_schedule(tick, it, hour)
                elif t == "announce":
                    text = str(it["text"]).strip()[:400]
                    if text:
                        tick["broadcasts"].append({"speaker": "terevi", "kind": "tease", "text": text})
                        for cid in w.agents:
                            w.remember(cid, f"{_hh(hour)} TereVi announced: {text[:220]}")
                elif t == "twist":
                    self.force_tease = str(it.get("text") or "Escalate. Shake things up in a way nobody expects.")[:300]
                elif t == "event":
                    self.force_island = it.get("id")
            except Exception:
                continue

    # ------------------------------------------------------------------ vary the cast
    def vary_cast(self):
        """Slightly vary every character's personality or backstory at the start of the day (one call)."""
        if not self.variation:
            return
        w, s = self.world, self.s
        v = self.variation
        amount = ("a slight tweak (a new habit, a mood, a small opinion)" if v < 34 else
                  "a noticeable shift (a new fear or passion, a changed attitude, a hobby, a petty grudge)" if v < 67 else
                  "a strong twist (an unexpected side of them, a buried piece of backstory, a changed outlook that surprises their friends)")
        rows = []
        for cid in w.agents:
            c = w.cast[cid]
            old = "; ".join(q["text"] for q in c.get("quirks", [])[-2:])
            rows.append(f"- {cid}: {c['name']}, {c['role']}. Persona: {c['persona'][:240]} Earlier changes: {old or 'none'}")
        sysm = ("You are the head writer of a drama. You keep characters fresh by giving each a small change that is consistent with who they are. "
                "Reply with a single JSON object and nothing else.")
        user = (f"Day {self.day}. Give each character {amount}. It must feel like THEM on a different day, never contradict their core, and must not mention the island rules or invent other people. "
                "One or two sentences, max 40 words, written as a fact about them ('Lately she ...').\n" + "\n".join(rows) +
                '\nReply as JSON: {"changes": {"<id>": "..."}}')
        try:
            r = self.llm.host_json(sysm, user, {"kind": "vary", "ids": list(w.agents)})
        except LLMError as e:
            if e.fatal:
                raise
            return
        except Exception:
            return
        ch = r.get("changes") if isinstance(r, dict) else None
        if not isinstance(ch, dict):
            return
        for cid, txt in ch.items():
            if cid in w.agents and isinstance(txt, str) and txt.strip():
                q = w.cast[cid].setdefault("quirks", [])
                q.append({"day": self.day, "text": txt.strip()[:300]})
                del q[:-3]

    def quirk_line(self, cid):
        q = self.world.cast[cid].get("quirks", [])[-2:]
        return ("RECENT CHANGES IN YOU (part of who you are lately): " + " ".join(x["text"] for x in q)) if q else ""

    # ------------------------------------------------------------------ Day 1: introductions and the reveal
    def intro_decision_lines(self, cid, hour):
        w, s = self.world, self.s
        out = ["IT IS YOUR FIRST DAY. You are on a thriller-themed reality show with seven strangers, a cheerful AI host (TereVi) and a silent housemaid (NeoVi). "
               "Meet people you have not met yet: introduce yourself one-on-one, size them up, find allies and rivals, explore the house and grounds. "
               "TereVi has announced introductions in the Dining Hall at 10:00 and a special announcement this evening. Nobody has told you of any danger."]
        oc = s.get("occasion")
        if oc and oc["status"] == "announced" and (cid == oc["host"] or cid in oc["invite_ids"]):
            out.append(f"INVITATION: {self.nm(oc['host'])} is hosting a {oc['kind']} in the {w.room_name(oc['where'])} this turn: {oc['text']}.")
        elif not oc:
            out.append("You may host a small gathering (a meal, a game, a swim...) using the 'host' field, if you like.")
        b = self.bonds_text(cid)
        if b:
            out.append(b)
        out.append("HOSTS: add 'terevi' to talk_to to speak to the monitor. NeoVi is the housemaid; you can only talk to her when she is in your room.")
        return out

    def run_presentations(self, hour):
        w, s = self.world, self.s
        tick = self.new_tick(hour)
        tick["type"] = "meeting"
        self.begin_practice(tick)                                # people walk in on the live map (claimtrial.py)
        ids = [c for c in w.agents if not w.agents[c].get("out")]            # the unconscious are not marched to the meeting
        room = "dining_hall"
        text = self.make_broadcast("intro_meeting", {})
        tick["broadcasts"].append({"speaker": "terevi", "kind": "welcome", "text": text})
        self.fetch_stragglers(tick, ids, room, "the introductions")
        for cid in ids:
            a = w.agents[cid]
            start = a["room"]
            steps = w.path(cid, start, room) if start != room else []
            tick["moves"][cid] = {"from": start, "path": [start] + ([r for r, _, _ in steps] if steps else ([room] if start != room else [])), "to": room}
            a["room"] = room
            a["activity"] = "At the introductions"
            w.remember(cid, f"{_hh(hour)} The introductions began in the Dining Hall. TereVi: {text[:200]}")
        self.neovi_attend(tick, room)
        self.run_scene_live(tick, "intro", room, ids, hour, self.intro_beats(ids))           # the engine decides, the model voices (scenes.py)
        self.intro_done = True
        self.day_notable.append("The cast introduced themselves to each other in the Dining Hall.")
        return tick

    def run_reveal(self, hour):
        w, s = self.world, self.s
        tick = self.new_tick(hour)
        tick["type"] = "reveal"
        self.begin_practice(tick)                                # people walk in on the live map (claimtrial.py)
        ids = [c for c in w.agents if not w.agents[c].get("out")]
        for c_ in w.agents:
            if c_ not in ids:
                w.agents[c_]["missed_reveal"] = True                          # they will be told when they come round
        s["revealed"] = True
        n = s.get("week_len", 7)
        s["deadline_day"] = max(self.day + 1, n * week_of(self.day, n))
        room = "dining_hall"
        text = self.make_broadcast("reveal", {})
        self.reveal_text = text
        tick["broadcasts"].append({"speaker": "terevi", "kind": "reveal", "text": text})
        self.fetch_stragglers(tick, ids, room, "TereVi's announcement")
        for cid in ids:
            a = w.agents[cid]
            start = a["room"]
            steps = w.path(cid, start, room) if start != room else []
            tick["moves"][cid] = {"from": start, "path": [start] + ([r for r, _, _ in steps] if steps else ([room] if start != room else [])), "to": room}
            a["room"] = room
            a["activity"] = "Hearing the truth"
            w.remember(cid, f"{_hh(hour)} TereVi REVEALED THE TRUTH: the show is real, nobody leaves, and if nobody dies before the end of Day {s['deadline_day']} EVERYONE dies. "
                            f"A killer who is caught is executed; a wrong accusation executes an innocent and frees the killer. The audience thinks it is all staged. {text[:200]}")
            self.stat(tick, cid, "sanity", -(14 + self.rng.randint(0, 6)), "the truth")
        self.neovi_attend(tick, room)
        self.fx(tick, "flash", room)
        self.fx(tick, "shake", room)
        self.run_scene_live(tick, "reveal", room, ids, hour, self.reveal_beats(tick, ids))
        self.day_notable.append("TereVi revealed the truth: the show is real, nobody leaves, and the weekly deadline is deadly.")
        self.saga("TereVi revealed the truth on Day 1: the killing game is real.")
        tick["events"].append({"type": "system_notable", "who": "terevi", "room": room, "vis": "public",
                               "text": f"THE TRUTH IS OUT: if nobody dies by the end of Day {s['deadline_day']}, everyone dies."})
        return tick

    # ------------------------------------------------------------------ the last call
    def last_call_due(self, hour):
        s = self.s
        return (self.revealed and not self.last_call_done and not s.get("case") and not s.get("over") and bool(self.world.agents)
                and s["deadline_day"] == self.day and hour >= 20)

    def run_last_call(self, hour):
        """Two hours before the Reckoning TereVi gathers everyone: someone can volunteer, someone can strike in the dark."""
        w, s = self.world, self.s
        self.last_call_done = True
        tick = self.new_tick(hour)
        tick["type"] = "lastcall"
        self.begin_practice(tick)                                # people walk in on the live map (claimtrial.py)
        ids = [c for c in w.agents if not w.agents[c].get("out")]            # the unconscious are not marched to the meeting
        room = "dining_hall"
        text = self.make_broadcast("lastcall", {})
        tick["broadcasts"].append({"speaker": "terevi", "kind": "deadline", "text": text})
        self.fetch_stragglers(tick, ids, room, "the last call")
        for cid in ids:
            a = w.agents[cid]
            start = a["room"]
            steps = w.path(cid, start, room) if start != room else []
            tick["moves"][cid] = {"from": start, "path": [start] + ([r for r, _, _ in steps] if steps else ([room] if start != room else [])), "to": room}
            a["room"] = room
            a["activity"] = "The last call"
            w.remember(cid, f"{_hh(hour)} TereVi gathered everyone for the last call: two hours to the deadline and nobody has died. {text[:200]}")
        self.neovi_attend(tick, room)
        beats, vols, strikers = self.lastcall_beats(ids)                                    # who volunteers, who strikes: the engine decides (scenes.py)
        self.run_scene_live(tick, "lastcall", room, ids, hour, beats)
        if vols:
            v = vols[0]
            a = w.agents[v]
            here = [o for o in w.occupants(room) if o in w.agents and o != v]
            saver = s.pop("_lastcall_saver", None)                                 # decided with the scene (scenes.py), so the line and the outcome agree
            savers = [saver] if saver in here else []
            if savers:
                self.log_event(tick, {"type": "mercy", "who": savers[0], "room": room, "vis": "public",
                                      "text": f"{self.nm(savers[0])} refuses to let {self.nm(v)} sacrifice themselves, and the moment passes."}, witnesses=here, actor=savers[0])
                self.moment(v, f"offered to die for everyone; {self.nm(savers[0])} would not allow it")
            else:
                self.log_event(tick, {"type": "madness", "who": v, "room": room, "vis": "public",
                                      "text": f"{self.nm(v)} steps forward: 'It's me. Let it be me.'"}, witnesses=here, actor=v)
                self.open_case(tick, "suicide", v, room=room, hour=hour, witnesses=here, cause="gave their life so the others could live",
                               note="It has to be someone. Let it be me.")
                s["case"]["sacrifice"] = True
        if not s.get("case") and strikers and self.murders:
            by, t = strikers[0]
            self.blackout_until = self.idx + 1
            self.fx(tick, "dark")
            self.log_event(tick, {"type": "sabotage", "who": "terevi", "room": room, "vis": "public",
                                  "text": "The lights cut out. In the dark, something happens."}, witnesses=list(w.agents))
            a = w.agents[by]
            weap = next((k for k in a["inv"] if "weapon" in w.item_spec(k).get("tags", [])), None) \
                or next((k for k, q in s["room_items"].get(room, {}).items() if q > 0 and "weapon" in w.item_spec(k).get("tags", [])), None)
            self.resolve_attacks(tick, [(by, {"target": t, "method": weap or "hands", "activity": "", "thought": "", "staged": ""})], hour)
        if not s.get("case"):
            self.day_notable.append("Nobody volunteered, nobody struck: the last call ended in silence and dread.")
        return tick

    # ------------------------------------------------------------------ the Reckoning
    def run_reckoning(self, tick):
        w, s = self.world, self.s
        ids = list(w.agents)
        announce = self.make_broadcast("deadline", {})
        tick["broadcasts"].append({"speaker": "terevi", "kind": "deadline", "text": announce})
        scene = self.make_broadcast("reckoning", {"ids": ids, "neovi": self.neovi_enforce(tick, None, 22)})
        for cid in ids:
            w.end_agent(cid, "executed", "died in the Reckoning")
        tick["reckoning"] = {"ids": ids, "scene": scene}
        tick["ending"] = {"kind": "reckoning", "title": "THE RECKONING", "text": scene, "ids": ids}
        s["over"] = {"kind": "reckoning", "day": self.day, "title": "THE RECKONING", "text": scene}
        res = "Nobody died before the deadline, so everyone was executed. The season is over."
        tick["events"].append({"type": "system_notable", "who": "terevi", "room": "foyer", "vis": "public", "text": res})
        self.day_notable.append(res)

    # ------------------------------------------------------------------ prompt assembly
    def can_end_life(self, cid):
        a = self.world.agents.get(cid)
        if not a or not self.murders or self.s.get("case"):
            return False
        drive = a["drive"]["id"]
        desperate = self.days_left() <= 1 and self.s["escape"]["progress"] < 60 and (drive in ("martyr", "protector") or a["sanity"] < 60)
        return a["sanity"] < 35 or (drive == "martyr" and self.dread_level() >= 2) or (drive == "nihilist" and a["sanity"] < 55) or desperate

    def deadline_lines(self, cid, hour):
        """When the deadline is near the stakes are spelled out: somebody has to die or everybody does."""
        s = self.s
        if not self.revealed or s.get("case"):
            return []
        dl = self.days_left()
        if dl > 2:
            return []
        esc = s["escape"]["progress"]
        if dl == 0:
            when = f"tonight at 22:00, in {max(0, 22 - hour)} hour(s)"
        elif dl == 1:
            when = f"tomorrow night at 22:00, in about {24 + 22 - hour} hours"
        else:
            when = f"on the night of Day {s['deadline_day']} (2 days away)"
        close = esc >= 80
        txt = (f"THE MATH: the deadline falls {when}. The escape plan is {esc}% done"
               + (", close enough that you might just make it. " if close else ", so it will not save you in time. ")
               + "If nobody dies before then, EVERYONE dies, you included. The only certain way to save everyone is for ONE person to die first: a murder, a sacrifice "
                 "(someone volunteers or ends their own life) or an accident. This is the moral crisis of the week: people bargain, volunteer, argue over who it should be, turn on the weak "
                 "or the hated, confess, or quietly plan a killing, while others refuse to let anyone die and chase any other way. Decide how YOU act, in character, and act on it: "
                 + ("time is almost gone." if dl <= 1 else "the clock is running."))
        return [txt]

    def deadline_ctx(self):
        s = self.s
        if not self.revealed or s.get("case") or self.days_left() > 2:
            return ""
        dl = self.days_left()
        return (f"THE CLOCK: the deadline is {'TONIGHT at 22:00' if dl == 0 else 'tomorrow night' if dl == 1 else 'in two days'} and escape is only {s['escape']['progress']}% done. "
                "If nobody dies, everyone dies. The room feels it in every line: people propose volunteers or drawing lots, accuse the weak or the hated, bargain, confess, break down, "
                "protect each other, or go very quiet in a way that frightens the others.\n")

    def story_decision_lines(self, cid, hour):
        """Everything the story layer adds to a character's decision prompt."""
        out = list(self.deadline_lines(cid, hour))
        fns = (self.lost_lines, self.moments_lines, self.condition_line) if self.lean else \
            (self.lost_lines, self.moments_lines, self.rumor_lines, self.faction_line, self.condition_line, self.repeat_lines)
        for fn in fns:
            t = fn(cid)
            if t:
                out.append(t)
        out.extend(self.plot_lines(cid))
        self.short_docs = not self.docs_full(cid, hour)
        out.extend(self.plot_lines2(cid))
        out.extend(self.focus_lines(cid))
        out.extend(self.night_lines(cid, hour))
        out.extend(self.door_lines(cid))
        out.extend(self.craft_lines(cid))
        out.extend(self.clothes_lines(cid))
        out.extend(self.cond_lines(cid))
        out.extend(self.env_lines(cid))
        out.extend(self.mind_lines(cid))
        out.extend(self.hook_lines(cid))
        out.extend(self.alliance_lines(cid))
        out.extend(self.tie_lines(cid))
        out.extend(self.options_hint(cid, hour))
        out.extend(self.sleep_lines(cid, hour))
        out.extend(self.stealth_lines(cid))
        out.extend(self.secret_lines(cid))
        out.extend(self.variety_lines(cid))
        out.extend(self.incite_lines(cid))
        if self.can_end_life(cid):
            out.append("DESPAIR: you are broken enough to consider ending your own life (action 'end_life'). It is a real option for someone this far gone, "
                       "and a martyr may see it as the way to save everyone else from the deadline, but friends nearby may talk you down.")
        if self.revealed:
            out.append(self.escape_lines(cid))
        return out

    def card_story(self, pid):
        """Short story-layer lines for a character's card in conversations."""
        w = self.world
        a = w.agents.get(pid)
        if not a:
            return ""
        bits = []
        lost = a["memory"].get("lost", [])[-2:]
        if lost:
            bits.append(" Still grieving: " + ", ".join(f"{x['name']} ({x['how']})" for x in lost) + ".")
        mm = a["memory"].get("moments", [])[-2:]
        if mm:
            bits.append(" Defining moments: " + " | ".join(mm) + ".")
        if self.slip_chance(pid) >= 0.12:
            bits.append(" Error-prone right now: fumbles, misremembers, says too much.")
        bits.append(self.card_secret(pid))
        rp = self.repeat_lines(pid)
        if rp:
            bits.append(" Do not repeat their usual gestures; vary them.")
        for inc in self.s.get("incitements", []):
            if inc["ttl"] > 0 and inc["target"] == pid and inc["victim"] in w.agents:
                bits.append(f" Has been worked on by {self.nm(inc['by'])} to hurt {self.nm(inc['victim'])}.")
        rl = self.rumor_lines(pid)
        if rl:
            bits.append(" " + rl[:200])
        pl = self.s.get("plots", {}).get(pid)
        if pl and pl.get("target") in w.agents and self.murders:
            bits.append(f" SECRETLY PLOTTING to kill {self.nm(pl['target'])} ({pl['stage']}); if a person who trusts them is present they may sound that person out for help "
                        "(a lookout, an alibi, cleaning up or a weapon) via effects.accomplice, or stay silent.")
        return "".join(bits)

    # ------------------------------------------------------------------ nightly upkeep
    def story_night(self, tick):
        w, s = self.world, self.s
        self.update_factions()
        # a rumour about someone usually finds its way back to them
        for r in s.get("rumors", []):
            if r["day"] == self.day and r["about"] in w.agents and r["about"] not in r["heard"] and self.rng.random() < 0.6:
                r["heard"].append(r["about"])
                w.remember(r["about"], f"A rumor about you is going around: {r['claim']}")
                self.moment(r["about"], "learned a rumor was spreading about you")
        s["incitements"] = []
