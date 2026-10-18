"""The gatherings as live practices: the introductions, the reveal, the last call and the remembrance.

Like the trial (claimtrial.py), the engine decides what happens in each gathering and the model only voices it, in one call per scene. People walk
in from wherever they were; the lines run on the clock once the speaker has arrived; allies whisper and can be overheard; the most rattled may
step out for a moment. What each person does comes from who they are and where they stand:

* The introductions: everyone says who they are, most outgoing first; someone who already likes or dislikes them may answer (a small change in
  feeling either way).
* The reveal: each reacts to TereVi's news by temperament (panic, rage at the monitor, demanding a way out, distrust, silence); TereVi answers
  the first two who challenge her; a friend comforts the most shaken (a little sanity back).
* The last call: the engine decides who volunteers to die (the most broken or the most selfless) and who means to strike in the dark (a
  plotter whose target is in the room, or else the cruellest and most desperate, against the one they like least); the rest plead, despair or
  turn on the one they like least.
* The remembrance: each survivor speaks of the dead they were closest to (fondly, with regret, or with the false grief of the one who did it);
  someone lights a candle; the closest pair hold each other.

SceneMixin is mixed into DayRunner (engine.py).
"""
from .data_cast import HOSTS

TITLES = {"intro": "THE INTRODUCTIONS", "reveal": "THE TRUTH", "lastcall": "THE LAST CALL", "vigil": "THE REMEMBRANCE"}
LABELS = {"intro": "the introductions", "reveal": "TereVi's announcement", "lastcall": "the last call", "vigil": "the remembrance"}
CONTEXT = {"intro": "The cast meet each other for the first time in the Dining Hall, believing this is a reality show.",
           "reveal": "TereVi has just told them the show is real: nobody leaves, and if nobody dies by the deadline, everyone dies.",
           "lastcall": "Two hours to the deadline and nobody has died. TereVi has gathered everyone.",
           "vigil": "The survivors gather to remember the dead."}
WHISPERS = {"intro": ("What do you make of them?", "Too early to tell."), "reveal": ("Are you okay?", "Stay close to me."),
            "lastcall": ("If it comes to it... stay away from the lights.", "I know."), "vigil": ("Are you holding up?", "Not really.")}


class SceneMixin:
    def scene_beat(self, beats, speaker, text, move, kind="say"):
        beats.append({"speaker": speaker, "text": text, "move": move, "kind": kind})

    def pick_line(self, beats, options):
        """A template line nobody has said yet in this scene, if there is one."""
        said = {b["text"] for b in beats}
        fresh = [o for o in options if o not in said]
        return self.rng.choice(fresh or options)

    def they(self, cid):
        return {"he": "He", "she": "She"}.get((self.world.cast.get(cid) or {}).get("pron"), "They")

    def first_like(self, cid):
        likes = (self.world.cast.get(cid) or {}).get("likes") or ""
        return likes.split(",")[0].strip()

    # ------------------------------------------------------------------ what happens in each gathering
    def intro_beats(self, ids):
        w = self.world
        beats = []
        for p in sorted(ids, key=lambda c: (-self.facet(c, "gregariousness"), c)):
            c = w.cast[p]
            like = self.first_like(p)
            text = self.rng.choice([f"I'm {c['name']}. {c['role']}, from {c['origin']}." + (f" I'm into {like}." if like else ""),
                                    f"Hi. {c['short']}. {c['role']}." + (f" Talk to me about {like}." if like else ""),
                                    f"{c['name']}, {c['role']}. Nice to meet you all, I guess."])
            self.scene_beat(beats, p, text, "introduce")
            fans = [o for o in ids if o != p and w.agents[o]["aff"].get(p, 0) >= 3]
            foes = [o for o in ids if o != p and w.agents[o]["aff"].get(p, 0) <= -2]
            if fans and self.rng.random() < 0.5:
                o = self.rng.choice(sorted(fans))
                self.scene_beat(beats, o, f"{c['short']}! Good to see a familiar face.", "warm")
                w.adjust_aff(o, p, 1)
                w.adjust_aff(p, o, 1)
            elif foes and self.rng.random() < 0.5:
                o = self.rng.choice(sorted(foes))
                self.scene_beat(beats, o, f"Great. {c['short']} is here too.", "jab")
                w.adjust_aff(p, o, -1)
        return beats

    def reveal_beats(self, tick, ids):
        w = self.world
        beats, answered, shaken = [], 0, []
        for p in sorted(ids, key=lambda c: (-self.facet(c, "assertiveness"), c)):
            f = lambda k: self.facet(p, k)
            if f("stress_vulnerability") >= 60 and f("courage") < 50:
                self.scene_beat(beats, p, self.pick_line(beats, ["No. No, no, no. This is a joke. Tell me this is a joke.", "This isn't happening. This can't be happening.",
                                                                  "I want to go home. I just want to go home."]), "panic")
                shaken.append(p)
            elif f("anger") >= 55:
                self.scene_beat(beats, p, self.pick_line(beats, ["You think we'll kill each other for your ratings? You're sick.", "Come down here and say that to my face!",
                                                                  "This is insane. You're insane."]), "rage")
                if answered < 2:
                    answered += 1
                    self.scene_beat(beats, "terevi", "Sick? Darling, I'm the only one here who isn't going to die.", "answer")
            elif f("courage") >= 55:
                self.scene_beat(beats, p, self.pick_line(beats, ["How do we get out? There has to be a way out of here.", "Who's running this? Who's actually behind you?",
                                                                  "What happens if we just refuse? All of us, together?"]), "demand")
                if answered < 2:
                    answered += 1
                    self.scene_beat(beats, "terevi", "There is one way out, and you all heard it. Hehe.", "answer")
            elif f("trust") < 40:
                self.scene_beat(beats, p, self.pick_line(beats, ["Then nobody trusts anybody. Not from now on.", "Look around. One of us is already thinking about it."]), "distrust")
            else:
                self.scene_beat(beats, p, self.pick_line(beats, ["stares at the monitor and says nothing.", "sits down slowly, hands shaking.", "backs against the wall, very still."]), "silent", "act")
                shaken.append(p)
        for v in shaken:
            friend = max((o for o in ids if o != v), key=lambda o: (w.agents[o]["aff"].get(v, 0), o), default=None)
            if friend and w.agents[friend]["aff"].get(v, 0) >= 4:
                self.scene_beat(beats, friend, f"Hey. {self.nm(v)}, look at me. We'll get through this.", "comfort")
                self.stat(tick, v, "sanity", 2, f"{self.nm(friend)} comforted them")
                w.adjust_aff(v, friend, 1)
                break
        return beats

    def lastcall_beats(self, ids):
        """Returns (beats, volunteers, strikers): who offers to die, who means to strike when the lights go."""
        w, s = self.world, self.s
        beats, vols, strikers = [], [], []
        if ids:
            v = max(ids, key=lambda c: (self.facet(c, "altruism") + 100 - w.agents[c]["sanity"], c))         # the most selfless or the most broken
            p_vol = 0.15 + (0.3 if self.facet(v, "altruism") >= 65 else 0) + (0.3 if w.agents[v]["sanity"] <= 30 else 0)
            if self.rng.random() < min(0.6, p_vol):
                vols.append(v)
        if self.murders and len(ids) >= 2:
            for p in sorted(ids):
                t = ((s.get("plots") or {}).get(p) or {}).get("target")
                if t in ids and t != p and self.rng.random() < 0.6:
                    strikers.append((p, t))
            if not strikers:
                p = max(ids, key=lambda c: (self.facet(c, "cruelty") + (100 - w.agents[c]["sanity"]) / 2 + self.facet(c, "courage") / 3, c))
                if self.rng.random() < 0.3 + (0.2 if self.facet(p, "cruelty") >= 65 else 0):
                    t = min((o for o in ids if o != p), key=lambda o: (w.agents[p]["aff"].get(o, 0), o))
                    strikers.append((p, t))
        lurk = {by for by, _ in strikers}
        for p in sorted(ids, key=lambda c: (-self.facet(c, "assertiveness"), c)):
            if p in vols:
                continue
            if p in lurk:
                t = next(t for by, t in strikers if by == p)
                if self.rng.random() < 0.5:
                    self.scene_beat(beats, p, f"is very quiet, eyes on {self.nm(t)}.", "lurk", "act")
                continue
            worst = min((o for o in ids if o != p), key=lambda o: (w.agents[p]["aff"].get(o, 0), o), default=None)
            if worst and w.agents[p]["aff"].get(worst, 0) <= -3 and self.facet(p, "cruelty") >= 50:
                self.scene_beat(beats, p, f"If anyone deserves it, it's {self.nm(worst)}.", "accuse")
                w.adjust_aff(worst, p, -2)
            elif w.agents[p]["sanity"] < 40:
                self.scene_beat(beats, p, self.pick_line(beats, ["Two hours. Two hours, and then we're all dead.", "I don't want to die. I don't want to die here.",
                                                              "So this is it. This is how it ends."]), "despair")
            else:
                self.scene_beat(beats, p, self.pick_line(beats, ["Somebody think of something. We can't just sit here and wait.", "There has to be another way. There has to be.",
                                                              "Please. Let's just stay calm and stay together."]), "plead")
        for v in vols:
            self.scene_beat(beats, v, "It's me. Let it be me.", "volunteer")
        return beats, vols, strikers[:1]

    def vigil_beats(self, ids, dead):
        w, s = self.world, self.s
        beats = []
        case = s.get("case") or {}
        for p in sorted(ids, key=lambda c: (-self.facet(c, "altruism"), c)):
            if not dead:
                break
            v = max(dead, key=lambda d: (w.agents[p]["aff"].get(d, 0), d))
            vn = self.nm(v)
            aff = w.agents[p]["aff"].get(v, 0)
            if case.get("killer") == p and case.get("victim") == v and case.get("culprit_aware", True):
                self.scene_beat(beats, p, self.pick_line(beats, [f"I can't believe {vn} is gone. I just can't.", f"Who would do this to {vn}? Who?"]), "mask")
            elif aff >= 3:
                like = self.first_like(v)
                self.scene_beat(beats, p, self.pick_line(beats, [f"I keep thinking about {vn}." + (f" {self.they(v)} loved {like}." if like else ""),
                                                              f"{vn} was the first one here who was kind to me.", f"I'd give anything to hear {vn} laugh again.",
                                                              f"{vn} should still be here. {self.they(v)} should still be here."]), "fond")
            elif aff <= -2:
                self.scene_beat(beats, p, self.pick_line(beats, [f"I never got along with {vn}. I'm sorry for that now.", f"I said things to {vn} I can't take back now."]), "regret")
            else:
                self.scene_beat(beats, p, self.pick_line(beats, [f"{vn} didn't deserve this.", f"Nobody deserves to die like {vn} did.", f"I didn't know {vn} well. I wish I had.",
                                                              f"It doesn't feel real that {vn} is gone.", f"I keep seeing {vn}'s face.", f"We should have looked out for {vn}.",
                                                              f"{vn} was one of us. Whatever else, {vn} was one of us."]), "grief")
        if ids and dead:
            kind = max(ids, key=lambda c: (self.facet(c, "altruism"), c))
            self.scene_beat(beats, kind, f"lights a candle for {', '.join(self.nm(d) for d in dead)}.", "candle", "act")
            pairs = [(w.agents[a]["aff"].get(b, 0) + w.agents[b]["aff"].get(a, 0), a, b) for i, a in enumerate(sorted(ids)) for b in sorted(ids)[i + 1:]]
            best = max(pairs, default=None)
            if best and best[0] >= 8:
                self.scene_beat(beats, best[1], f"holds {self.nm(best[2])} close.", "hold", "act")
        return beats

    # ------------------------------------------------------------------ voicing, publishing and staging
    def voice_scene_lines(self, beats, kind):
        """One voicing call per gathering: the model puts each decided beat in the speaker's voice; anything missing keeps the template line."""
        w = self.world
        if not beats:
            return []
        who = sorted({b["speaker"] for b in beats})
        cards = []
        for p in who:
            if p in w.cast:
                cards.append(f"- {p} = {self.nm(p)}, {w.cast[p]['role']}. Looks: {self.looks_line(p, short=True)}. Speech: {w.cast[p]['speech'][:90]}")
            elif p in HOSTS:
                cards.append(f"- {p} = {HOSTS[p]['name']}, {HOSTS[p]['role']}. {HOSTS[p]['persona'][:160]}")
        listing = "\n".join(f"{i}. {b['speaker']}{' (action)' if b.get('kind') == 'act' else ''}: {b['text']}" for i, b in enumerate(beats))
        sysm = f"{self.bible()}\nYou voice the lines of a scene. The engine has decided what each person says or does; you only put it in their own words. Reply with JSON only."
        user = (f"{TITLES[kind]}. {CONTEXT[kind]} Rewrite each numbered line in the speaker's voice: same meaning, same person named, max 25 words, no new facts or events. "
                f"An action stays an action (third person, no name at the start).\nSPEAKERS:\n" + "\n".join(cards) + f"\nLINES:\n{listing}\n"
                'Reply as JSON: {"lines": [{"i": <number>, "text": "..."}]}')
        try:
            res = self.llm.voice(sysm, user, {"beats": len(beats), "scene": kind}) or {}
        except Exception as e:
            if getattr(e, "fatal", False):
                raise
            res = {}
        got = {}
        for ln in res.get("lines") or []:
            if isinstance(ln, dict) and isinstance(ln.get("i"), int) and 0 <= ln["i"] < len(beats) and str(ln.get("text", "")).strip():
                got[ln["i"]] = str(ln["text"]).strip()[:260]
        out = []
        for i, b in enumerate(beats):
            text = self.clean_line(b["speaker"], b.get("kind", "say"), got.get(i, b["text"])) if b["speaker"] in w.agents else got.get(i, b["text"])
            out.append({"speaker": b["speaker"], "kind": b.get("kind", "say"), "text": text or b["text"], "move": b.get("move")})
        return out

    def run_scene_live(self, tick, kind, room, ids, hour, beats):
        """Voice the decided beats, put them in the record and everyone's memory, then walk everyone in and stage the lines on the clock."""
        w = self.world
        lines = self.voice_scene_lines(beats, kind)
        if lines:
            tick["talk"].append({"room": room, "lines": lines, "scene": {"kind": kind, "title": TITLES[kind]}})
            self.tape_record(room, lines)
            self.last_talk[room] = [(f"*{self.nm(l['speaker'])} {l['text']}*" if l["kind"] == "act" else f"{self.nm(l['speaker'])}: {l['text']}") for l in lines]
            for cid in ids:
                for ln in lines[:12]:
                    who = "You" if cid == ln["speaker"] else self.nm(ln["speaker"])
                    w.remember(cid, f"{hour % 24:02d}:00 ({LABELS[kind]}) {who}" + (f" {ln['text'][:100]}" if ln["kind"] == "act" else f": {ln['text'][:100]}"))
            self.day_notable.append(f"At {LABELS[kind]}: {self.nm(lines[0]['speaker'])} said \"{lines[0]['text'][:90]}\"")
        arrivals = self.walk_in(tick, ids)
        self.stage_trial_live(tick, arrivals, room, LABELS[kind], WHISPERS[kind])
        return lines
