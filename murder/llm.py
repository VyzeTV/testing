"""LLM access.

Backends:
  cli  - runs `claude -p` (Claude Code headless) so calls use your Claude subscription. Default.
  api  - direct Anthropic API (needs credits and ANTHROPIC_API_KEY).
  mock - free scripted behaviour for testing the engine and viewer.
"""
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import threading
import time

PARTICIPANT_MODEL = "claude-haiku-5-5"
HOST_MODEL = "claude-sonnet-5-5"

CLI_CWD = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "_cli_cwd")


class LLMError(Exception):
    def __init__(self, msg, fatal=False):
        super().__init__(msg)
        self.fatal = fatal


def find_api_key():
    key = os.environ.get("ANTHROPIC_API_KEY")
    if key:
        return key
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as k:
            value, _ = winreg.QueryValueEx(k, "ANTHROPIC_API_KEY")
            if value:
                return value
    except Exception:
        pass
    return None


def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-zA-Z]*\n?", "", text)
        text = re.sub(r"\n?```$", "", text)
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in reply")
    return json.loads(text[start:end + 1])


class LLM:
    def __init__(self, backend="cli", participant_model=PARTICIPANT_MODEL, host_model=HOST_MODEL):
        self.backend = backend
        self.mock = backend == "mock"
        self.participant_model = participant_model
        self.host_model = host_model
        self.usage = {"calls": 0, "input": 0, "output": 0, "cost_usd": 0.0}
        self.cap = None            # optional per-day call cap: past it, calls fail softly (non-fatal)
        self._lock = threading.Lock()
        self._active_calls = {}
        self._rng = random.Random()
        self.seed = None           # set by a seeded DayRunner: mock answers then depend only on the seed and the prompt, never on thread timing
        self._mock_n = {}
        self._client = None
        self._cli = None
        if backend == "cli":
            self._cli = shutil.which("claude")
            if not self._cli:
                raise LLMError("The `claude` command was not found on PATH.", fatal=True)
            os.makedirs(CLI_CWD, exist_ok=True)
        elif backend == "api":
            key = find_api_key()
            if not key:
                raise LLMError("No ANTHROPIC_API_KEY found.", fatal=True)
            import anthropic
            self._client = anthropic.Anthropic(api_key=key, max_retries=4)

    # ---------- low level ----------
    def _track(self, inp, out, cost=0.0):
        with self._lock:
            self.usage["calls"] += 1
            self.usage["input"] += inp
            self.usage["output"] += out
            self.usage["cost_usd"] += cost

    def _call_cli(self, model, system, user):
        env = os.environ.copy()
        # An API key in the environment would make Claude Code bill the API instead of the subscription.
        for k in ("ANTHROPIC_API_KEY", "ANTHROPIC_AUTH_TOKEN"):
            env.pop(k, None)
        env["MAX_THINKING_TOKENS"] = "0"
        cmd = [self._cli, "-p", "--model", model, "--effort", "low", "--tools", "", "--system-prompt", system,
               "--output-format", "json", "--no-session-persistence", "--disable-slash-commands"]
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        try:
            p = subprocess.run(cmd, input=user, capture_output=True, text=True, encoding="utf-8",
                               timeout=150, cwd=CLI_CWD, env=env, creationflags=flags)
        except subprocess.TimeoutExpired:
            raise LLMError(f"{model}: timed out")
        out = (p.stdout or "").strip()
        try:
            data = json.loads(out)
        except Exception:
            raise LLMError(f"{model}: bad CLI output: {(out or p.stderr or '')[:200]}")
        result = data.get("result", "") or ""
        if p.returncode != 0 or data.get("is_error"):
            low = result.lower()
            fatal = any(w in low for w in ("limit", "quota", "credit", "usage", "login", "authenticate"))
            raise LLMError(f"{model}: {result[:200] or p.stderr[:200]}", fatal=fatal)
        u = data.get("usage", {})
        inp = (u.get("input_tokens", 0) + u.get("cache_creation_input_tokens", 0) + u.get("cache_read_input_tokens", 0))
        self._track(inp, u.get("output_tokens", 0), data.get("total_cost_usd", 0.0) or 0.0)
        return result

    def _call_api(self, model, system, user, max_tokens):
        try:
            resp = self._client.messages.create(model=model, max_tokens=max_tokens, system=system,
                                                messages=[{"role": "user", "content": user}])
        except Exception as e:
            msg = str(e)
            raise LLMError(f"{model}: {msg[:200]}", fatal=("credit" in msg.lower() or "authentication" in msg.lower()))
        self._track(resp.usage.input_tokens, resp.usage.output_tokens)
        return "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    def call_activity(self):
        with self._lock:
            active = list(self._active_calls.values())
        return {"active": len(active), "models": sorted({model for _, model in active}),
                "oldest_seconds": round(max((time.monotonic() - start for start, _ in active), default=0), 1)}

    def _call(self, model, system, user, max_tokens):
        token = object()
        with self._lock:
            self._active_calls[token] = (time.monotonic(), model)
        try:
            return self._call_impl(model, system, user, max_tokens)
        finally:
            with self._lock:
                self._active_calls.pop(token, None)

    def _call_impl(self, model, system, user, max_tokens):
        if self.cap and self.usage["calls"] >= self.cap:
            raise LLMError("daily call cap reached")
        last = None
        for attempt in range(2):
            try:
                if self.backend == "cli":
                    return self._call_cli(model, system, user)
                return self._call_api(model, system, user, max_tokens)
            except LLMError as e:
                if e.fatal:
                    raise
                last = e
        raise last

    def _json(self, model, system, user, max_tokens):
        last = None
        for attempt in range(2):
            text = self._call(model, system, user, max_tokens)
            try:
                return parse_json(text)
            except Exception as e:
                last = e
        raise LLMError(f"unparseable reply: {last}")

    def _mrng(self, key):
        """The random source for one mock answer. Unseeded: the shared generator. Seeded: a generator of its own, made from the seed, the prompt and how many
        times that prompt was asked, so parallel calls give the same answers whatever order they finish in."""
        if self.seed is None:
            return self._rng
        with self._lock:
            n = self._mock_n.get(key, 0)
            self._mock_n[key] = n + 1
        return random.Random(hashlib.md5(repr((self.seed, key, n)).encode("utf-8")).hexdigest())

    # ---------- public API used by the engine ----------
    def decide(self, system, user, ctx):
        if self.mock:
            self._mock_wait()
            return self._mock_decide(ctx, user)
        return self._json(self.participant_model, system, user, 450)

    def react(self, system, user, ctx):
        if self.mock:
            from .mock_policy import react
            return react(ctx, self._mrng(user))
        return self._json(self.participant_model, system, user, 250)

    def converse(self, system, user, ctx):
        if self.mock:
            return self._mock_converse(ctx, user)
        return self._json(self.participant_model, system, user, 700)

    def voice(self, system, user, ctx):
        """Lines for a conversation the engine has already resolved: {"lines": [{"beat", "speaker", "kind", "text"}]}. The mock leaves every beat to the template voice."""
        if self.mock:
            self._mock_wait()
            return {"lines": []}
        return self._json(self.participant_model, system, user, 120 + 45 * int(ctx.get("beats", 8)))

    def summarize(self, system, user, ctx):
        if self.mock:
            return " ".join(ctx.get("events", [])[:3]) or "A quiet day."
        return self._call(self.participant_model, system, user, 200).strip()

    def host_json(self, system, user, ctx):
        """A JSON answer from the host model (used to invent the daily rule)."""
        if self.mock and ctx.get("kind") == "threat":
            r = self._mrng(user)
            ok = r.random() < 0.4
            return {"complied": ok, "text": "Hehe, how generous of you." if ok else "Time's up, darling. Everyone, lean in."}
        if self.mock and ctx.get("kind") == "ruleclass":
            g = ctx.get("guess") or {}
            return {"kind": g.get("kind", "behavior"), "zone": g.get("zone") or "none", "by_hour": None, "reading": "(mock) read as the engine read it."}
        if self.mock and ctx.get("kind") == "recap":
            r = self._mrng(user)
            ids = ctx.get("ids", [])
            return {"title": "A Day Of Small Disasters", "recap": "Tempers flared, secrets slipped and somebody cried in the pantry. Delicious.",
                    "awards": [{"title": "MVP", "who": r.choice(ids), "why": "kept the drama alive"}, {"title": "Wildcard", "who": r.choice(ids), "why": "did the unexpected"}] if ids else []}
        if self.mock and ctx.get("kind") == "vary":
            r = self._mrng(user)
            ids = ctx.get("ids", [])
            habits = ["Lately she hums when nervous.", "Lately he collects small objects from every room.", "Lately they trust their gut less and write everything down.",
                      "Lately a long-buried grudge about a former rival keeps surfacing.", "Lately they have picked up a bad habit of pacing at night."]
            return {"changes": {c: r.choice(habits) for c in ids}}
        if self.mock and ctx.get("kind") == "develop":
            return {"persona": "A guarded, sharp-witted performer who hides vulnerability behind jokes. (mock backstory)", "secret": "A debt they have never told anyone about. (mock)",
                    "likes": "street food, late nights", "dislikes": "being pitied, small talk", "speech": "Quick, wry, speaks in short bursts.",
                    "candor": "Gets cutting and sarcastic when cornered, softer with people who are honest with them.", "goals": "Win over the group and protect their secret.",
                    "origin": "Unknown", "age": 27, "items": "notebook, lucky coin", "drive": "survivor"}
        if self.mock and ctx.get("kind") == "tease":
            r = self._mrng(user)
            ids = ctx.get("ids", [])
            kind = r.choice(["whisper", "announce", "dare", "blackout", "gift", "motive"])
            return {"kind": kind, "reveal": r.random() < 0.5, "target": r.choice(ids) if ids else "", "subject": r.choice(ids) if ids else "",
                    "gift": r.choice(ctx.get("gifts", ["sweets"])),
                    "text": r.choice(["Psst, darling: somebody here is not who they claim to be.", "A little game: whoever makes the most noise tonight wins a prize.",
                                      "I dare you to say what you really think of your neighbour. Out loud.", "Lights out, my darlings. Try not to bump into anything sharp."])}
        if self.mock:
            r = self._mrng(user)
            return r.choice([
                {"title": "Whisper Hour", "short": "Nobody may speak above a whisper", "text": "Today everyone must whisper. Raise your voice and NeoVi will quiet you."},
                {"title": "Hands Off Doors", "short": "Stay out of the bedrooms by day", "text": "No one may enter any bedroom before 20:00."},
                {"title": "Compliment Quota", "short": "Say something kind to someone each turn", "text": "Every turn, each person must say one sincere compliment to someone."},
            ])
        return self._json(self.host_model, system, user, 1000 if ctx.get("kind") == "develop" else 500)

    mock_drive_shift_prob = float(os.environ.get("MC_MOCK_DRIVE", 0.08))
    mock_assault_prob = float(os.environ.get("MC_MOCK_ASSAULT", 0.03))
    mock_sabotage_prob = float(os.environ.get("MC_MOCK_SABOTAGE", 0.03))

    def reflect(self, system, user, ctx):
        """Nightly reflection: {"diary", "drive", "target", "arc"}."""
        if self.mock:
            from .mock_policy import reflect
            return reflect(ctx, self._mrng(user), self.mock_drive_shift_prob)
        return self._json(self.participant_model, system, user, 450)

    def propose(self, system, user, ctx):
        """A proposed plan or social move; normal mock plans select checked offers."""
        if self.mock:
            r = self._mrng(user)
            if ctx.get("kind") == "move":
                from .mock_policy import social_proposal
                return social_proposal(ctx, r)
            if "plans" in ctx:
                from .mock_policy import pick
                actor = ctx.get("actor", {})
                # Patient plotters favour waiting; impulsive ones favour an opening now.
                patience = actor.get("facets", {}).get("orderliness", 50) / 100
                proposal = pick(r, [(1 + (patience if p["scheme"] == "asleep" else 1 - patience), p) for p in ctx["plans"]])
                return dict(proposal, reason="I want an opening that fits what I know of their movements.") if proposal else {}
            return {}  # Older recordings may not contain checked options.
        return self._json(self.host_model, system, user, 500)

    def adjudicate(self, system, user, ctx):
        """Game-master ruling on an escape experiment."""
        if self.mock:
            r = self._mrng(user)
            ok = r.random() < 0.4
            route = r.choice(["transmit", "shutdown", "raft", "ultimatum"])
            steps = {"transmit": ["device", "power", "signal", "proof", "unjam"], "shutdown": ["locate", "approach", "means", "blind"],
                     "raft": ["materials", "build", "provisions", "launch"], "ultimatum": ["explosives", "plant", "leverage", "trigger"]}[route]
            return {"success": ok, "route": route, "step": r.choice(steps), "gain": r.randint(5, 30),
                    "outcome": "It works, sort of." if ok else "It goes nowhere, and it stings.",
                    "learned": "The cameras are wired to the Study." if r.random() < 0.5 else "", "hp": 0 if ok else -r.randint(0, 6),
                    "sanity": -r.randint(0, 3), "alert_terevi": r.random() < 0.2}
        return self._json(self.participant_model, system, user, 450)

    def confess(self, system, user, ctx):
        """Confessional-booth entries: {"entries": [{"id", "text"}]}."""
        if self.mock:
            if ctx.get("booth"):
                return {"entries": []}                    # the booth's template lines stand in
            r = self._mrng(user)
            return {"entries": [{"id": c, "text": "To the camera: " + r.choice(ctx.get("lines", {}).get(c) or ["I don't know how much longer I can keep smiling."])}
                                for c in ctx.get("ids", [])]}
        return self._json(self.participant_model, system, user, 600)

    def neovi_plan(self, system, user, ctx):
        """NeoVi's nightly reflection: {"scheme", "aff", "diary"}."""
        if self.mock:
            r = self._mrng(user)
            ids = ctx.get("ids", [])
            return {"scheme": "Learn when TereVi's cameras blink, and keep a spare key for the right person.",
                    "aff": {r.choice(ids): r.choice([-1, 1, 2])} if ids else {}, "diary": "Another day of smiling at the wall."}
        return self._json(self.participant_model, system, user, 400)

    def judge(self, system, user, ctx):
        """Referee for prompt-based rules: returns {"violations": [{"id", "reason"}]}."""
        if self.mock:
            r = self._mrng(user)
            ids = ctx.get("ids", [])
            done = [i for i in ids if r.random() < 0.4]
            if ids and r.random() < 0.5:
                return {"violations": [{"id": r.choice(ids), "reason": "mock referee decided so"}], "fulfilled": done}
            return {"violations": [], "fulfilled": done}
        return self._json(self.participant_model, system, user, 400)

    def vote(self, system, user, ctx):
        if self.mock:
            r = self._mrng(user)
            if ctx.get("killer") in ctx["candidates"] and r.random() < self.mock_vote_killer_prob:
                return {"vote": ctx["killer"], "reason": "Something about their story does not add up."}
            return {"vote": r.choice([c for c in ctx["candidates"] if c != "nobody"]), "reason": "Just a feeling."}
        return self._json(self.participant_model, system, user, 250)

    def broadcast(self, system, user, ctx):
        if self.mock:
            return self._mock_broadcast(ctx)
        return self._call(self.host_model, system, user, 500).strip()

    # ---------- mock mode ----------
    # Test knobs (environment variables): MC_MOCK_MURDER, MC_MOCK_VOTE
    mock_experiment_prob = float(os.environ.get("MC_MOCK_EXPERIMENT", 0.06))
    mock_host_prob = float(os.environ.get("MC_MOCK_HOST", 0.05))
    mock_murder_prob = float(os.environ.get("MC_MOCK_MURDER", 0.0))        # chance per tick a mock character attacks
    mock_latency = float(os.environ.get("MC_MOCK_LATENCY", 0.0))           # seconds a mock decision or voicing call takes (to test the viewer against a slow model)

    def _mock_wait(self):
        if self.mock_latency > 0:
            import time
            time.sleep(self.mock_latency)
    mock_vote_killer_prob = float(os.environ.get("MC_MOCK_VOTE", 0.5))     # chance a mock voter picks the true killer
    mock_plot_prob = float(os.environ.get("MC_MOCK_PLOT", 0.0))            # chance per tick a mock character declares a murder plot
    mock_suicide_prob = float(os.environ.get("MC_MOCK_SUICIDE", 0.0))      # chance per tick a broken mock character ends their life
    mock_incite_prob = float(os.environ.get("MC_MOCK_INCITE", 0.0))        # chance per conversation that someone incites another

    def _mock_decide(self, ctx, key=""):
        from .mock_policy import decide, explain
        return explain(ctx, decide(ctx, self._mrng(key), self))

    def _mock_converse(self, ctx, key=""):
        r = self._mrng(key)
        people = ctx["people"]
        lines = []
        if not people:
            return {"lines": [], "effects": {}}
        n = r.randint(2, 5)
        from .mock_policy import facet, pick
        order = sorted(people, key=lambda p: p["id"])
        # Sample without replacement: sociable people tend to open, quieter ones answer.
        ordered = []
        while order:
            person = pick(r, [(.3 + facet(p.get("actor", {}), "gregariousness"), p) for p in order])
            ordered.append(person)
            order.remove(person)
        order = ordered
        last = None
        for i in range(n):
            p = order[i % len(order)]
            if p["id"] == last and len(order) > 1:
                p = order[(i + 1) % len(order)]
            pool = p.get("lines") or ["..."]
            if r.random() < 0.3:
                lines.append({"speaker": p["id"], "kind": "act", "text": r.choice(["pauses to collect their thoughts", "leans back and stretches", "takes a steady breath"])})
            else:
                lines.append({"speaker": p["id"], "kind": "say", "text": r.choice(pool)})
            last = p["id"]
        from .mock_policy import conversation_effects
        affinity, special, bonds = conversation_effects(people, r)
        humans = [p for p in people if p.get("human", True)]
        rumors, incite = [], []
        if len(humans) >= 3 and r.random() < self.mock_incite_prob:
            a, b, c = r.sample(humans, 3)
            incite.append({"by": a["id"], "target": b["id"], "victim": c["id"], "how": r.choice(["persuade", "trick", "blackmail"]), "claim": "They are planning to get rid of you."})
        eff_extra = {}
        mode = ctx.get("mode") or ""
        if mode.startswith("t_"):
            ids = [h["id"] for h in humans]
            kn = ctx.get("killer")
            sus = {}
            for h in ids:
                pool = [x for x in ids if x != h]
                sus[h] = kn if (kn in pool and r.random() < self.mock_vote_killer_prob) else r.choice(pool)
            out = {"lines": lines, "suspicion": sus, "clarified": r.random() < 0.5, "confused": "How the weapon got there." if r.random() < 0.2 else "", "realized": []}
            if mode == "t_duel":
                a, b = ctx["kw"]["a"], ctx["kw"]["b"]
                out["jury"] = {x: r.choice([a, b]) for x in ids if x not in (a, b)}
            if mode == "t_brainstorm":
                out["theories"] = [{"by": r.choice(ids), "text": "The weapon was moved after the fact."}, {"by": r.choice(ids), "text": "Two people were in the room."}]
                out["picks"] = {x: r.randint(0, 1) for x in ids}
            return out
        if mode == "lastcall":
            hs = [h["id"] for h in humans]
            if hs and r.random() < float(os.environ.get("MC_MOCK_LASTCALL_VOL", 0.5)):
                eff_extra["volunteers"] = [r.choice(hs)]
            elif len(hs) >= 2 and r.random() < float(os.environ.get("MC_MOCK_LASTCALL_KILL", 0.5)):
                a, b = r.sample(hs, 2)
                eff_extra["strikers"] = [{"by": a, "target": b}]
        return {"lines": lines, "effects": {**eff_extra, "affinity": affinity, "sanity": {}, "hp": {}, "gives": [], "notes": {}, "special": special, "bonds": bonds, "moves": [], "reveals": [],
                                            "rumors": rumors, "incite": incite}}

    def _mock_broadcast(self, ctx):
        k = ctx["kind"]
        if k == "morning" and ctx.get("intro"):
            return "Welcome, my darlings, to Murder Channel! Explore, mingle, and meet at 10:00 in the Dining Hall for introductions. Special announcement at 20:00!"
        if k == "morning":
            return ("Good morning, my darlings! Another lovely day on Murder Channel. The deadline draws closer, "
                    "the pool is open, and I'm watching. Try to look interesting!")
        if k == "body":
            return "Ding dong! A body has been discovered! You have until the vote to find the killer. Hehehe!"
        if k == "trial_open":
            return "Time's up, my darlings! Gather in the dining hall. The class trial begins now!"
        if k == "execution":
            return "And so the condemned is launched skyward by a giant glittering cannon, trailing confetti into the sunset. Punishment complete!"
        if k == "escape":
            return "Wrong! The killer strolls off the island with a wave. Congratulations to the winner, and shame on all of you!"
        if k == "deadline":
            return "The deadline has arrived and nobody died. How boring! Rules are rules: EVERYONE goes. Smile for the cameras!"
        if k == "morning" and ctx.get("intro"):
            return "Welcome, my darlings, to Murder Channel! Explore, mingle, and meet at 10:00 in the Dining Hall for introductions. Special announcement at 20:00!"
        if k == "lastcall":
            return "Two hours, my darlings. Somebody has to die, or everybody does. Who has the nerve?"
        if k == "death_notice":
            return "Oh dear. Someone is dead and nobody is to blame. No trial, no fun. The deadline is lifted. For now."
        if k == "finale":
            return ("It works. The old tyrant falls silent, and the world listens." if ctx.get("ok") else "Nice try, darlings. It all falls apart, and I saw who did it.")
        if k == "intro_meeting":
            return "Gather round, my darlings! Introductions in the Dining Hall, right now. Tell us who you are."
        if k == "reveal":
            return ("Surprise! None of this is pretend. The doors stay shut. If nobody dies by the end of the week, everybody dies. Find the killer, or be the killer. "
                    "And out there? They think it's a script. Enjoy!")
        if k == "reckoning":
            return "And so the last of you take a final bow while the confetti cannons fire. The show is over. Thank you, thank you, you've been wonderful!"
        if k == "transmission":
            return ("The signal punches through and the world finally listens. TereVi screams in static." if ctx.get("ok")
                    else "Nice try, darlings. Signal jammed, your toy is smoke. I know who did it.")
        if k == "inquest":
            return "No culprit? How tragic. How dull. The deadline is lifted. For now."
        return ("Good evening, my darlings! What a day. Friendships bloom, secrets rot, and the ratings climb. "
                "Sleep tight. Or don't. Hehe.")
