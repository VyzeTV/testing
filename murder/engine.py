"""Day engine: runs one game day tick by tick and emits a record per tick for the viewer.

Beyond ordinary life it handles murders, clues, body discovery, the investigation window,
the class trial (votes), executions, the weekly deadline and newcomer arrivals.
"""
import random
from collections import Counter
from concurrent.futures import ThreadPoolExecutor

from .data_cast import HOSTS, STORY_BIBLE
from .data_world import ROOMS, CAMERA_BLIND, ESCAPE_ROUTES as ESCAPE_ROUTES_
from .llm import LLMError
from . import rules as rulelib
from .world import MOVE_BUDGET, clamp, deadline_for_death
from .data_world import COMMON_ITEMS
from .drama import DramaMixin, OCCASION_SANITY, SPECIAL_SANITY
from .chaos import ChaosMixin
from .cases import CaseMixin
from .trial import TrialMixin, TRIAL_ROOM as _TR
from .life import LifeMixin
from .routes import RoutesMixin
from .mayhem import MayhemMixin
from .director import DirectorMixin
from .stealth import StealthMixin
from .secrets import SecretsMixin
from .refcheck import RefereeMixin
from .pace import PaceMixin
from .plotting import PlotMixin
from .reaction import ReactMixin
from .night import NightMixin, NIGHT_BLOCKS, DAWN_HOUR
from .aftermath import AftermathMixin
from .doors import DoorMixin
from .craft import CraftMixin
from .hooks import HookMixin
from .ties import TiesMixin
from .telemetry import TelemetryMixin
from .forensics import ForensicsMixin
from .alliances import AllianceMixin
from .neovi_active import NeoViActiveMixin
from .settings import TuningMixin
from .clothing import ClothingMixin
from .tone import ToneMixin
from .itemuse import ItemUseMixin
from .conditions import ConditionMixin
from .chronicle import ChronicleMixin
from .sim import SimMixin
from .clock import ClockMixin, Timeline
from .falls import FallMixin
from .social import SocialMixin
from .convo import ConvoMixin
from .booth import BoothMixin
from .schedule import ScheduleMixin
from .beliefs import BeliefMixin
from .nightlife import NightLifeMixin
from .planner import MurderPlanMixin
from .combat import FightMixin
from .carry import CarryMixin
from .evidence import EvidenceMixin
from .gear import GearMixin
from .marks import MarksMixin
from .looks import LooksMixin
from .scenes import SceneMixin
from .escape import EscapeWorkMixin
from .finales import FinaleMixin
from .outside import OutsideMixin
from .kumiko import KumikoMixin
from .innervoice import InnerVoiceMixin
from .intimacy import IntimacyMixin
from .twists import TwistMixin
from .endings import EndingsMixin
from .departures import DeparturesMixin
from .claimtrial import ClaimTrialMixin
from .perception import PerceptionMixin
from .envsys import EnvironmentMixin
from .mind import MindMixin
from .crime import CrimeMixin
from .freetime import FreeTimeMixin
from .brain import BrainMixin
from .scengen import ScenarioEventsMixin
from .nonlethal import NonlethalMixin
from . import scenario as scn
from .story import StoryMixin

DAY_START, DAY_END = 8, 22          # ticks cover 08:00 .. 21:00, then a night tick at 22:00
ACTIONS = {"stay", "search", "take", "drop", "give", "use", "rest", "investigate", "attack", "experiment", "assault", "sabotage", "end_life", "build", "interrogate", "rig", "hide", "spy", "stash", "retrieve", "hide_body", "frisk", "lock", "unlock", "pick", "break", "barricade", "craft", "restrain", "free", "knock", "knockout", "carry", "rob", "wake", "treat", "stage"}
TRIAL_ROOM = _TR


def hhmm(h):
    return f"{int(h) % 24:02d}:00"                  # night hours run on past midnight (25 = 01:00) so time only goes forward


def phase_of(h):
    if h < 12:
        return "morning"
    if h < 18:
        return "afternoon"
    if h < 22:
        return "evening"
    return "night"


def aff_label(v):
    if v <= -7:
        return "hated"
    if v <= -4:
        return "hostile"
    if v <= -2:
        return "cold"
    if v == -1:
        return "wary"
    if v == 0:
        return "neutral"
    if v <= 2:
        return "friendly"
    if v <= 5:
        return "fond"
    if v <= 8:
        return "close"
    return "devoted"


def tone_hint(aff, sanity, hp):
    """How someone talks to and about another person, from the relationship, their sanity and their health."""
    if aff >= 9:
        base = "devoted: protective, openly caring, teases lovingly, would stand up for them"
    elif aff >= 6:
        base = "close: warm and trusting, affectionate teasing, shares worries"
    elif aff >= 3:
        base = "fond: friendly banter, supportive, light roasting"
    elif aff >= 1:
        base = "friendly: polite, curious, a little playful"
    elif aff == 0:
        base = "neutral: civil and careful, still feeling them out"
    elif aff == -1:
        base = "wary: guarded, awkward or dry, at most a small dig"
    elif aff >= -3:
        base = "cold: curt, pointed remarks, avoids warmth"
    elif aff >= -6:
        base = "hostile: openly critical, confrontational or icily dismissive"
    else:
        base = "contemptuous: scornful and cutting, may lose their temper"
    if sanity < 30:
        base += "; frayed nerves make them irritable, paranoid or tearful, and they may snap even at people they like"
    elif sanity < 55:
        base += "; on edge, shorter fuse, more sarcasm than usual, small things sting"
    elif sanity >= 85:
        base += "; composed and generous, gives the benefit of the doubt"
    if hp < 40:
        base += "; hurt and tired, little patience (or clingy and vulnerable)"
    return base


class Stop(Exception):
    pass


class DayRunner(CaseMixin, TrialMixin, LifeMixin, RoutesMixin, MayhemMixin, DirectorMixin, StealthMixin, SecretsMixin, RefereeMixin, PaceMixin, PlotMixin, ReactMixin, NightMixin, AftermathMixin, DoorMixin, CraftMixin, HookMixin, TiesMixin, TelemetryMixin, ForensicsMixin, AllianceMixin, NeoViActiveMixin, TuningMixin, ClothingMixin, ToneMixin, ItemUseMixin, ConditionMixin, NonlethalMixin, ChronicleMixin, ClockMixin, SimMixin, FallMixin, SocialMixin, ConvoMixin, BoothMixin, ScheduleMixin, BeliefMixin, NightLifeMixin, MurderPlanMixin, FightMixin, CarryMixin, EvidenceMixin, GearMixin, MarksMixin, LooksMixin, SceneMixin, EscapeWorkMixin, FinaleMixin, OutsideMixin, KumikoMixin, InnerVoiceMixin, IntimacyMixin, TwistMixin, EndingsMixin, DeparturesMixin, ClaimTrialMixin, PerceptionMixin, EnvironmentMixin, MindMixin, CrimeMixin, FreeTimeMixin, BrainMixin, ScenarioEventsMixin, StoryMixin, DramaMixin, ChaosMixin):
    def __init__(self, world, llm, on_tick, gate=None, should_stop=None, step=2, workers=6, seed=None,
                 murders=True, motive="", rule_mode="roulette", rule_text="", confessionals=True, mischief="occasional", chaos="normal",
                 variation=0, gm_pull=None, lean=False, call_cap=0, autodir=False, autodir_get=None, tuning_get=None):
        self.world = world
        world.mem_hook = self.mem_hook
        self.llm = llm
        self.on_tick = on_tick
        self.gate = gate or (lambda idx: None)
        self.should_stop = should_stop or (lambda: False)
        self.step = step
        self.workers = workers
        self.rng = random.Random(seed)
        self.inner_rng = random.Random(f"inner-{seed}")    # thoughts (innervoice.py) draw from their own stream so they do not reshape the run
        if seed is not None:
            world.rng.seed(seed)                  # reproducible runs and tests
            if getattr(llm, "mock", False):
                llm.seed = seed                   # mock answers too
        self.murders = murders
        self.motive = (motive or "").strip()
        self.rule_mode = rule_mode
        self.rule_text = (rule_text or "").strip()
        self.rule_ctx = {}
        self.rule_final = None
        self.day = world.state["day"]
        self.idx = 0
        self.broadcast_text = ""
        self.last_talk = {}
        self.day_notable = []
        self.diary_added = {}
        self.arrivals = list(world.state.get("arrivals", []))
        self.drama_init(confessionals, mischief)
        self.chaos_init(chaos)
        self.story_init(gm_pull, variation)
        self.life_init()
        self.tuning_get = tuning_get or (lambda: {})
        self.director_init(autodir, autodir_get)
        self.lean = bool(lean)
        self.degraded = False
        self.degrade_note = None
        self.death_today = False
        self.trial_init()
        self.confused = ""
        self.finale_route = None
        self.rule_prev = {}
        self.rule_none_reason = ""
        self.focus, self.focus_idea, self.exp_today, self.plot_started_day = None, None, 0, -1
        self.night_init()

    # ---------- small helpers ----------
    @property
    def s(self):
        return self.world.state

    def nm(self, cid):
        return self.world.display_name(cid)

    def case_active(self):
        return bool(self.s.get("case"))

    def days_left(self):
        return self.s["deadline_day"] - self.day

    def vote_label(self, case):
        return f"Day {case['vote_day']}, {hhmm(case['vote_hour'])}"

    def new_tick(self, hour, phase=None):
        return {"day": self.day, "idx": -1, "hour": hour, "time": hhmm(hour), "phase": phase or phase_of(hour),
                "broadcasts": [], "moves": {}, "talk": [], "events": [], "thoughts": {}, "errors": []}

    def emit(self, tick):
        tick["idx"] = self.idx
        self.idx += 1
        if not self.s.get("case") and self.days_left() <= 0 and isinstance(tick.get("hour"), (int, float)):
            self.deadline_hours(tick, tick["hour"])         # special scenes (vigil, last call...) count against the deadline too
        for cid_, a_ in self.world.agents.items():
            a_["outfit"] = self.outfit_label(cid_)
            a_["conds_view"] = self.cond_snapshot(cid_)
            a_["out_view"] = (a_.get("out") or {}).get("cause")
            a_["beliefs_view"] = self.beliefs_view(cid_)
            if self.brain_on():
                a_["brain_view"] = self.brain_view(cid_)
        try:
            self.env_tick(tick)
        except Exception as e:  # the environment is a layer on top of the turn: never let it break the game
            tick["env_error"] = f"{type(e).__name__}: {e}"[:160]
        try:
            self.mind_tick(tick)
        except Exception as e:  # the mind layer must never break a turn
            tick["mind_error"] = f"{type(e).__name__}: {e}"[:160]
        self._chron_names = None
        self.chron_flush(tick)
        tick["state"] = self.world.snapshot()
        tick["usage"] = dict(self.llm.usage)
        tick["dread"] = self.dread_level()
        tick["island"] = self.current_island()
        try:
            tick["speeds"] = {c: v for c, v in ((cid, round(self.move_factor(cid), 2)) for cid in self.world.agents) if v < 0.95}
            tick["live"] = self.sim_finish(tick)
            self.finish_hearing(tick)
            self.log_whereabouts(tick)
            self.belief_sightings(tick)
            self.clock_stop()
        except Exception as e:  # positions must never break the game
            self.clock_stop()
            tick["live_error"] = f"{type(e).__name__}: {e}"[:160]
            sm = self.__dict__.get("_sim")
            if sm is not None:
                sm.tick_id = None
        self.on_tick(tick)

    def ensure_private_bedrooms(self):
        """Saves made when two people shared a bedroom: whoever shares gets a bedroom of their own (there are eight)."""
        from .world import BEDROOMS
        w = self.world
        by_home = {}
        for cid in w.agents:
            by_home.setdefault(w.cast[cid]["home"], []).append(cid)
        free = [r for r in BEDROOMS if r not in by_home]
        for home, ids in by_home.items():
            for cid in ids[1:]:
                if not free:
                    return
                new = free.pop(0)
                w.cast[cid]["home"] = new
                w.remember(cid, f"(private) You have been given a bedroom of your own now: the {w.room_name(new)}.")

    def abs_now(self, hour=None):
        """Absolute game time in hours (day * 24 + hour). Anything that lasts across a night (a knock-out, a pair of handcuffs, a storm) is stored in this, never in the per-day tick counter."""
        return self.day * 24 + (hour if hour is not None else self.s.get("_hour", 12))

    def log_event(self, tick, evt, witnesses=None, actor=None):
        m = self.minute()
        if m is not None and "m" not in evt:
            evt["m"] = round(m, 1)                                    # when in the turn this happened
        tick["events"].append(evt)
        self.booth_note_event(evt)
        if witnesses and actor and evt.get("vis") == "public":
            witnesses = self.event_witnesses(actor, evt.get("room"), evt.get("type"), witnesses)
        side = self.__dict__.setdefault("_chron_w", {})
        if len(side) > 3000:
            side.clear()
        side[id(evt)] = (list(witnesses) if witnesses else None, actor)
        self.note_news(evt, witnesses, actor)
        self.belief_witness(evt, witnesses, actor)
        if evt.get("type") == "punish":
            self.punish_count = getattr(self, "punish_count", 0) + 1
        text = f"{hhmm(tick['hour'])} {evt['text']}"
        w = self.world
        if evt.get("vis") == "public":
            for cid in (witnesses or []):
                if cid != actor and cid in w.agents:
                    w.remember(cid, text)
        if actor in w.agents:
            w.remember(actor, text)
        if evt["type"] in ("discover", "secret", "lock", "give", "body", "attack", "arrival", "system_notable", "occasion", "experiment", "tease"):
            self.day_notable.append(evt["text"])

    def neovi_target(self, hour):
        ins = self.s.get("_inspect")
        if ins and ins["day"] == self.day and ins["hour"] == hour and self.s["npcs"]["neovi"].get("room") != "none":
            return ins["room"]
        if self.s["npcs"]["neovi"].get("room") == "none":
            return "none"
        rt = HOSTS["neovi"]["routine"]
        room = rt[0][1]
        for h, r in rt:
            if h <= hour:
                room = r
        return room

    # ---------- prompts ----------
    @staticmethod
    def mood_text(a):
        sa, hp = a["sanity"], a["hp"]
        mood = ("on the verge of breaking: paranoid, irritable, erratic" if sa < 30 else
                "frayed, snappy and on edge" if sa < 55 else "a bit uneasy" if sa < 75 else "steady")
        body = "badly hurt and shaky" if hp < 40 else "sore" if hp < 70 else ""
        return mood + (f", {body}" if body else "")

    def items_text(self, items):
        if not items:
            return "nothing notable"
        return "; ".join(f"{k} ({self.world.item_name(k)}) x{q}" for k, q in items.items())

    def system_prompt(self, cid):
        w = self.world
        c = w.cast[cid]
        rooms = ", ".join(f"{rid}={r[0]}" for rid, r in ROOMS.items())
        people = ", ".join(f"{k}={w.cast[k]['short']}" for k in w.agents)
        murder = ""
        if self.murders:
            murder = (
                "\nTHE DEADLY GAME: if nobody dies before the weekly deadline, EVERYONE dies; any death lifts it (a murder, an accident or a suicide). "
                "You may try to kill someone in the same room (action 'attack'; you may also 'frame' someone else with planted evidence), hurt them without killing them "
                "(action 'assault'; a hard blow can kill by mistake), sabotage things (action 'sabotage': cut the lights, ruin an announced event, steal an item), "
                "or, only if you are truly broken or a martyr, end your own life (action 'end_life'). You can also manipulate others into violence (persuade, trick, blackmail); "
                "whoever delivers the killing blow is the one held responsible, even if they were manipulated, tricked or it was a mistake. "
                "When 3 people find the body of someone who was killed, a 24-hour investigation starts (collect evidence and testimonies) and then a class trial at the Voting Grounds decides who is responsible. A death with no culprit (an accident or a suicide) has no trial. "
                "If the cast names the culprit, the culprit is executed; if they accuse the wrong person, that innocent is executed and the real culprit escapes the island alive. "
                "Do not kill on a whim: only if your character would truly decide to, for a strong reason (fear, rage, the deadline, a threat to a secret, a sacrifice to save the rest). "
                "On most days nobody dies, but the deadline is real.")
        quirk = self.quirk_line(cid)
        return (
            f"{self.bible()}\n\n"
            f"You are {c['name']} ({c['role']}, {c['age']}, {c['gender']}, from {c['origin']}). You ARE this person; never mention being an AI.\n"
            f"PERSONA: {c['persona']}\nSECRET (never reveal casually): {c['secret']}\n"
            f"YOUR LOOKS (what others see; bring it up only when it matters): {self.looks_line(cid)}\n"
            f"LIKES: {c['likes']}. DISLIKES: {c['dislikes']}.\nHOW YOU SPEAK: {c['speech']}\nWHEN STRESSED OR PROVOKED: {c.get('candor', '')}\nYOUR GOALS: {c['goals']}\n"
            + (quirk + "\n" if quirk else "") + "\n"
            f"ROOM IDS: {rooms}\nPEOPLE IDS: {people}, neovi=NeoVi (housemaid)\n\n"
            "RULES: You only know what is in your memory and what you can see. Do not invent rooms or items. "
            "Be vivid and specific, never generic. "
            "TONE: speak like a real person, not a villain. Most exchanges are ordinary, curious, funny, awkward or warm; real meanness needs a cause "
            "(a clash of personalities, a grudge, fear, stress, a sore spot). You may swear naturally for emphasis or banter. How you talk to and about someone "
            "follows how you feel about them (your RELATIONSHIPS), your sanity and your health: friends tease gently, strangers stay civil, people you distrust get dry digs, "
            "enemies get real venom, and a frayed mind snaps more often than a calm one. Your CANDOR line describes how you react under stress, not your default. "
            "Cruelty must be personal: no slurs or hate speech about race, religion, gender identity or disability. "
            "Reply with a single JSON object and nothing else." + murder
        )

    def decision_prompt(self, cid, hour):
        w, s = self.world, self.s
        a = w.agents[cid]
        room = a["room"]
        others = [self.nm(o) + (self.clothing_note(o) + self.condition_note(o) if o in w.agents else "") for o in w.occupants(room, include_hidden=True) if o != cid and (o not in w.agents or not w.agents[o].get("hiding"))]
        exits = []
        for n in w.adjacent(cid, room):
            tag = "" if n["ok"] else f" [{n['note']}]"
            hidden = " [secret passage]" if n["kind"] == "secret" else ""
            exits.append(f"{n['room']} ({w.room_name(n['room'])}, {n['cost']} min){tag}{hidden}")
        reach = w.reachable_rooms(cid, MOVE_BUDGET * self.step)
        reach_txt = ", ".join(f"{r} ({m} min)" for r, m in sorted(reach.items(), key=lambda kv: kv[1]))
        rel = ", ".join(f"{self.nm(k)}: {v} ({aff_label(v)})" for k, v in a["aff"].items() if k in w.agents)
        mem = a["memory"]
        case = s.get("case")
        parts = [
            f"TIME: Day {self.day}, {hhmm(hour)} ({phase_of(hour)}). You are choosing what to do over the next {self.step} hour(s).",
            f"LOCATION: {w.room_name(room)} ({room}). Others here: {', '.join(others) if others else 'nobody'}.",
            f"VISIBLE ITEMS HERE: {self.items_text(s['room_items'].get(room, {}))}",
            f"DOORS FROM HERE: {'; '.join(exits)}",
            f"ROOMS YOU CAN REACH THIS TURN: {reach_txt or 'none'}",
            f"YOU: health {a['hp']}/100, sanity {a['sanity']}/100 (you feel {self.mood_text(a)}). Carrying: {self.items_text(a['inv'])}",
            f"TODAY'S BROADCAST: {self.broadcast_text or '(none yet)'}",
        ]
        dl = self.days_left()
        if not case and self.revealed:
            parts.append(f"DEADLINE: if NOBODY dies before the end of Day {s['deadline_day']} "
                         f"({'TODAY, at 22:00' if dl == 0 else str(dl) + ' day(s) left'}), EVERYONE still alive is executed, you included. "
                         f"Any death counts: a murder, an accident or a suicide. {self.dread_feel()}")
        rule = s.get("rule")
        if rule:
            parts.append("RULE OF THE DAY: " + rule["text"] + (self.rule_hint(rule) if rule.get("ai") else ""))
            rc = self.rule_ctx
            if rc and cid != rc["leader"]:
                parts.append(f"THE LEADER ({self.nm(rc['leader'])}) is already in the {w.room_name(rc['room'])} this turn ({rc['activity']}). "
                             "To obey you must be in that same room at the end of the turn.")
            n = rule["strikes"].get(cid, 0)
            if n:
                parts.append(f"You have already been punished {n} time(s) today.")
        if self.house_rules():
            parts.append(self.house_line().strip())
        if case and case["announced"]:
            victim = self.nm(case["victim"])
            parts.append(f"INVESTIGATION: {victim} is dead (TereVi's file is in your memory). You have until {self.vote_label(case)} to investigate and debate, "
                         "then a class trial decides who is responsible (someone always is). Use 'investigate' in rooms to look for clues "
                         "(the body and its surroundings tell a story; TereVi's case file is in your memory), ask people where they were, compare alibis. "
                         "Clues you have found are in your memory marked CLUE.")
        if case and case["killer"] == cid:
            if case["kind"] == "manslaughter":
                parts.append(f"YOU KILLED {self.nm(case['victim'])}, though you did not mean to ({case['method']}). You are the one responsible and you are terrified; "
                             "decide whether to hide it, blame someone, or confess.")
            else:
                parts.append(f"YOU ARE THE KILLER of {self.nm(case['victim'])}. Method: {case['method']}. "
                             "Your aim is to avoid being voted out: deflect, lie convincingly, and do not contradict yourself.")
        parts.extend(self.extra_decision_lines(cid, hour))
        parts.extend(self.free_lines(cid, hour))
        parts.extend(self.story_decision_lines(cid, hour))
        parts.extend(self.notebook_lines(cid))
        parts.extend(self.belief_lines(cid))
        bl = self.build_lines(cid)
        if bl:
            parts.append(bl)
        parts.extend(self.rig_lines(cid))
        parts.extend(self.accomplice_lines(cid))
        parts.extend(self.spree_lines(cid))
        parts.append(f"RELATIONSHIPS (-10..10): {rel}")
        parts.append("Let these feelings, your sanity and your health shape how you act toward people and what you say about them.")
        parts.append("YOUR DIARY: " + (" | ".join(mem["diary"][-3:]) or "(nothing yet)"))
        if self.brain_on():
            parts.extend(self.mem_decision_lines(cid, hour))
            parts.extend(self.plan_lines(cid))
        else:
            parts.append("TODAY SO FAR: " + (" | ".join(mem["recent"][-12:]) or "(nothing yet)"))
        if hour >= 21:
            parts.append("It is late. People usually head to their own bedroom around 22:00.")
        acts = "stay|search|take|drop|give|use|rest" + ("|experiment" if self.revealed else "")
        extra = ""
        if case and case["announced"]:
            acts += "|investigate|interrogate"
        if bl:
            acts += "|build"
        if self.murders and not case and self.rig_options(cid):
            acts += "|rig"
        acts += self.stealth_acts(cid)
        acts += self.secret_acts(cid)
        acts += self.door_acts(cid)
        acts += self.craft_acts(cid)
        acts += self.itemuse_acts(cid)
        acts += self.condition_acts(cid)
        if self.murders:
            acts += "|assault|sabotage"
            if not case:
                acts += "|attack"
            if self.can_end_life(cid):
                acts += "|end_life"
            extra = ('"target": "<person id for attack, assault or steal>", "method": "<attack: a weapon item id you hold or see here, '
                     "'poison:<item id>' if you hold a poison, or 'hands'; assault: a weapon item id or 'hands'; "
                     "sabotage: 'lights', 'occasion' (ruin the announced event) or 'steal' (with target and item); end_life: how, max 6 words>\", "
                     '"frame": "<person id to frame for this killing with planted evidence, optional; attack only>", '
                     '"also": "<a second person in the room to kill as well, optional; attack only>", '
                     '"plot": null or {"target": "<person id>", "stage": "brooding|preparing|stalking|striking", "method": "<max 10 words>", '
                     '"step": "<what you do toward it this turn, max 18 words>", "cover": "<your alibi or who you will blame, max 18 words>"}, ')
        parts.append(
            'Reply as JSON: {"thought": "<private, max 20 words>", "action": "' + acts + '", '
            '"target_room": "<room id to walk to, or empty>", "item": "<item id or empty>", "qty": 1, '
            '"to": "<person id for give, or empty>", ' + extra +
            '"build": null or {"kind": "ladder|rope|plank|remove", "to": "<room id>"}, '
            '"idea": "<experiment: what you try; interrogate: the question you put to the target; max 25 words>", '
            '"host": null or {"kind": "meal|movie|party|game|concert|prank|ritual|other", "where": "<room id>", "invite": "all" or ["person ids"], '
            '"secret_from": ["person ids, prank only"], "text": "<max 20 words>"}, '
            '"activity": "<what you do, max 15 words>", '
            '"talk_to": ["<person ids you want to talk to; terevi and neovi are allowed>"], "intent": "<what you want out of it, max 20 words>"' + (self.plan_schema() if self.brain_on() else '') + '}. ' + (self.plan_explain() if self.brain_on() else '') +
            "Pick something that follows your goals, mood and relationships. Variety matters; do not repeat yesterday's routine.")
        return "\n".join(parts)

    def clean_decision(self, d):
        if not isinstance(d, dict):
            raise ValueError("not a dict")
        return {
            "thought": str(d.get("thought", ""))[:160],
            "action": d.get("action") if d.get("action") in ACTIONS else "stay",
            "target_room": d.get("target_room") if d.get("target_room") in ROOMS else "",
            "item": str(d.get("item", "") or ""),
            "qty": d.get("qty", 1) if isinstance(d.get("qty", 1), int) else 1,
            "to": str(d.get("to", "") or ""),
            "target": str(d.get("target", "") or ""),
            "method": str(d.get("method", "") or ""),
            "activity": str(d.get("activity", "") or "Hanging around")[:90],
            "talk_to": [t for t in (d.get("talk_to") or []) if isinstance(t, str)][:4],
            "intent": str(d.get("intent", ""))[:140],
            "plan": self.plan_clean(d.get("plan")) if self.brain_on() else [],
            "idea": str(d.get("idea", "") or "")[:200],
            "host": self.clean_host(d.get("host")),
            "plot": self.clean_plot(d.get("plot")), "plot_given": "plot" in d,
            "frame": str(d.get("frame", "") or ""),
            "also": str(d.get("also", "") or ""),
            "wear": str(d.get("wear", "") or ""), "betray": str(d.get("betray", "") or ""), "craft": str(d.get("craft", "") or ""), "door": str(d.get("door", "") or ""), "sleep_in": str(d.get("sleep_in", "") or ""),
            "night": bool(d.get("night")), "frisk": str(d.get("frisk", "") or ""), "disclose": bool(d.get("disclose")),
            "conceal": ({"item": str(d["conceal"].get("item", "") or ""), "on": d["conceal"].get("on", True) is not False} if isinstance(d.get("conceal"), dict) else None),
            "keep_back": ({"what": str(d["keep_back"].get("what", "") or "")[:170], "why": str(d["keep_back"].get("why", "") or "")[:80]}
                          if isinstance(d.get("keep_back"), dict) else None),
            "sneak": bool(d.get("sneak")), "spy_on": str(d.get("spy_on", "") or ""),
            "stash": ({"item": str(d["stash"].get("item", "") or ""), "spot": str(d["stash"].get("spot", "") or "")[:60], "qty": d["stash"].get("qty", 1)} if isinstance(d.get("stash"), dict) else None),
            "build": ({"kind": str(d["build"].get("kind", "")), "to": str(d["build"].get("to", ""))} if isinstance(d.get("build"), dict) else None),
            "rig": ({"kind": str(d["rig"].get("kind", "")), "target": str(d["rig"].get("target", "") or "")} if isinstance(d.get("rig"), dict) else None),
        }

    def clean_host(self, h):
        if not isinstance(h, dict):
            return None
        text = str(h.get("text", "") or "").strip()[:160]
        if not text:
            return None
        invite = h.get("invite")
        invite = [x for x in invite if isinstance(x, str)][:8] if isinstance(invite, list) else "all"
        secret = [x for x in h.get("secret_from", []) if isinstance(x, str)][:6] if isinstance(h.get("secret_from"), list) else []
        return {"kind": h.get("kind") if h.get("kind") in OCCASION_SANITY else "other",
                "where": h.get("where") if h.get("where") in ROOMS else "", "invite": invite, "text": text, "secret_from": secret}

    def ask_parallel(self, jobs):
        """Run model calls in parallel. `jobs` is a list of (key, call) where each call only asks the model and returns its raw answer: everything that rolls dice
        or changes the world happens before or after, in a fixed order, so a seeded run is reproducible whatever order the calls finish in.
        Returns {key: (answer, error)}; a fatal model error is raised."""
        out = {}
        if not jobs:
            return out
        with ThreadPoolExecutor(max_workers=self.workers) as pool:
            futs = [(key, pool.submit(call)) for key, call in jobs]
            for key, fut in futs:
                if self.should_stop():
                    raise Stop()
                try:
                    out[key] = (fut.result(), None)
                except LLMError as e:
                    if e.fatal:
                        raise
                    out[key] = (None, e)
                except Exception as e:
                    out[key] = (None, e)
        return out

    def decide(self, cid, hour):
        return self.decide_many([cid], hour)[cid]

    def decide_many(self, cids, hour):
        """Decisions for several people: engine-made ones and prompts in order, the model calls in parallel, then each answer cleaned up in order."""
        res, asks = {}, []
        for cid in cids:
            got = self.decide_prepare(cid, hour)
            if got[0] == "done":
                res[cid] = got[1]
            else:
                sysm, user, ctx = got[1]
                asks.append((cid, lambda sysm=sysm, user=user, ctx=ctx: self.llm.decide(sysm, user, ctx)))
        answers = self.ask_parallel(asks)
        for cid, _ in asks:
            raw, err = answers[cid]
            res[cid] = self.decide_finish(cid, hour, raw, err)
        return {cid: res[cid] for cid in cids}

    def decide_prepare(self, cid, hour):
        a = self.world.agents[cid]
        w = self.world
        if a.get("out"):
            return "done", (self.clean_decision({"activity": "Unconscious", "action": "stay"}), None)
        if self.engine_decisions_on() and not self.needs_model(cid, hour):
            self.note_use(cid, "decision", "engine")
            return "done", (self.routine_decision(cid, hour), None)
        self.note_use(cid, "decision", "model")
        weapons = [k for k in list(a["inv"]) + list(self.s["room_items"].get(a["room"], {}))
                   if "weapon" in w.item_spec(k).get("tags", [])]
        ctx = {
            "hour": hour, "room": a["room"], "home": w.cast[cid]["home"],
            "reachable": list(w.reachable_rooms(cid, MOVE_BUDGET * self.step).keys()),
            "others_here": [o for o in w.occupants(a["room"]) if o != cid],
            "humans_here": [o for o in w.occupants(a["room"]) if o in w.agents and o != cid],
            "takeable": [k for k in list(self.s["room_items"].get(a["room"], {})) + list(COMMON_ITEMS.get(a["room"], [])) if "weapon" not in w.item_spec(k).get("tags", [])],
            "usable": [k for k in a["inv"] if w.item_spec(k).get("use")],
            "weapons": weapons, "murder_ok": self.murders and not self.case_active(), "violence_ok": self.murders,
            "investigating": bool(self.s.get("case") and self.s["case"]["announced"]),
            "end_ok": self.murders and self.can_end_life(cid), "plot_ok": self.murders, "brain": self.brain_on(),
        }
        try:
            return "ask", (self.system_prompt(cid), self.decision_prompt(cid, hour), ctx)
        except Exception as e:
            return "done", (self.clean_decision({"activity": "Lost in thought"}), f"{self.nm(cid)} zones out (bad prompt: {str(e)[:80]})")

    def decide_finish(self, cid, hour, raw, err):
        if err is not None:
            if isinstance(err, LLMError):
                return self.clean_decision({"activity": "Lost in thought"}), f"{self.nm(cid)} zones out (AI hiccup: {str(err)[:80]})"
            return self.clean_decision({"activity": "Lost in thought"}), f"{self.nm(cid)} zones out (bad reply: {str(err)[:80]})"
        try:
            d = self.clean_decision(raw)
            self.seek_care(cid, d)
            if self.brain_on() and d.get("plan"):
                self.plan_store(cid, hour, d["plan"])
            return d, None
        except Exception as e:
            return self.clean_decision({"activity": "Lost in thought"}), f"{self.nm(cid)} zones out (bad reply: {str(e)[:80]})"

    def talk_prompt(self, room, group, intents, hour, mode=None):
        w, s = self.world, self.s
        cards = []
        for pid in group:
            if pid in w.agents:
                c = w.cast[pid]
                a = w.agents[pid]
                others = [o for o in group if o != pid and o in w.agents]
                rel = " ".join(f"[{self.nm(o)}: {a['aff'].get(o, 0):+d} {aff_label(a['aff'].get(o, 0))}; "
                               f"tone: {tone_hint(a['aff'].get(o, 0), a['sanity'], a['hp'])}]" for o in others)
                extra = ""
                case = s.get("case")
                if case and case["killer"] == pid:
                    extra = (f" YOU ARE THE ONE RESPONSIBLE for {self.nm(case['victim'])}'s death ({case['method']}"
                             f"{', unintended' if case['kind'] == 'manslaughter' else ''}); defend yourself, lie or break down, as you would; never confess lightly.")
                cards.append(
                    f"- {pid} = {c['name']}, {c['role']}. {c['persona']} Looks: {self.looks_line(pid)}. Speech: {c['speech']} "
                    f"When stressed or provoked: {c.get('candor', '')} Secret to protect: {c['secret']} Mood: health {a['hp']}, sanity {a['sanity']} ({self.mood_text(a)}). "
                    f"Doing: {a['activity']}. Carrying: {', '.join(w.item_name(k) + (' (hidden on them: nobody sees it)' if k in a.get('concealed', {}) else '') for k in list(a['inv'])[:10]) or 'nothing'}. "
                    f"Wants: {intents.get(pid, 'just be around people')}. "
                    f"Toward the others here: {rel or 'n/a'}. {self.mem_card(pid, group) if self.brain_on() else 'Recent memory: ' + (' | '.join(a['memory']['recent'][-6:]) or 'none')}.{extra}" + self.card_extras(pid, group) + self.card_story(pid) + self.card_ties(pid, group) + self.card_tone(pid, group))
            elif pid == "neovi":
                cards.append(self.neovi_card_text(group))
            elif pid == "terevi":
                cards.append(self.terevi_card_text(group))
            else:
                h = HOSTS[pid]
                cards.append(f"- {pid} = {h['name']}, {h['role']}. {h['persona']}")
        prev = self.last_talk.get(room, [])
        case = s.get("case")
        ctxline = ""
        if mode == "trial" and case:
            ctxline = (f"CLASS TRIAL DEBATE: {self.nm(case['victim'])} is dead. Either one of the people present is responsible (whoever delivered the killing blow, "
                       "intended or not), or nobody is (an accident or a suicide). They argue about it, presenting the evidence below, alibis and accusations drawn only from what they remember; "
                       "they catch each other in contradictions. A culprit, if present, lies. Write 8 to 12 lines in total, each line max 25 words.\n"
                       "EVIDENCE ON THE TABLE:\n" + self.evidence_text(case) + "\n")
        elif mode == "intro":
            ctxline = ("WELCOME MEETING: TereVi (on the monitor) has called everyone to the Dining Hall for introductions. Each guest introduces themselves in their own voice "
                       "(who they are, what they are famous for, a fun fact or a boast, what they hope to get out of the show); the others react, joke, size each other up and ask questions; "
                       "TereVi hosts with theatrical charm and a barbed remark or two. Nobody suspects anything dark. Write 14 to 18 lines.\n")
        elif mode == "reveal":
            ctxline = ("THE REVEAL: TereVi has just told everyone the truth: the show is real, nobody can leave, if nobody dies by the end of the week everyone dies, "
                       "a killer who is caught is executed, a wrong accusation executes an innocent and frees the killer, and the audience thinks it is staged. "
                       "She said (excerpt): " + (self.reveal_text[:420] or "...") + "\nShow shock, disbelief, denial, fury, black humour, tears, bargaining, first suspicions and first alliances, "
                       "each in character. TereVi gloats. Write 10 to 14 lines.\n")
        elif mode == "endgame":
            ctxline = (f"THE ENDGAME: only {len([p for p in group if p in w.agents])} survivors remain and TereVi has called them to the Voting Grounds to decide how the show ends (her mood: {getattr(self, 'endgame_mood', 'crown')}). "
                       "They have nothing left to hide: fear, grief, rage, exhaustion, bargaining, last words, alliances turning on a dime, someone making peace. TereVi savours it. Write 8 to 12 lines.\n")
        elif mode == "lastcall":
            ctxline = (f"THE LAST CALL: it is two hours before the deadline and nobody has died. TereVi has gathered everyone in the Dining Hall and made the arithmetic plain: "
                       f"if nobody dies by 22:00, all {len([p for p in group if p in w.agents])} of them die. The escape plan is only {s['escape']['progress']}% done. "
                       "They face it openly and in character: someone may volunteer to die so the rest live, others refuse and shout them down, someone nominates the hated or the weak, "
                       "people bargain, draw lots, confess, break down, make peace, or fall into a terrible silence; a cold mind may quietly decide to kill. TereVi savours it and tempts them. "
                       "Write 14 to 18 lines. ALSO add to effects: \"volunteers\": [ids of anyone who truly, seriously commits to dying tonight so the others live, usually none or one], "
                       "\"strikers\": [{\"by\": \"id\", \"target\": \"id\"} for anyone who has decided to kill someone tonight, usually none].\n")
        elif mode == "vigil":
            dead_ = ", ".join(self.nm(v) for v in (s.get("aftermath") or {}).get("victims", []) if v in w.cast)
            ctxline = (f"THE REMEMBRANCE: the survivors have gathered quietly in the {w.room_name(room)} to remember {dead_ or 'the dead'}. TereVi is not here; NeoVi stands at the door, silent. "
                       "Nothing is solved and nobody is pretending it is. Grief, guilt, anger at whoever is to blame, small kindnesses, a shared memory of the dead, someone saying the thing nobody could say, "
                       "an old quarrel put down for an hour. It should feel like people holding each other together; it helps, a little. Write 10 to 14 lines.\n")
        elif mode == "finale":
            from .data_world import ESCAPE_ROUTES as _R
            r_ = _R.get(self.finale_route or "transmit")
            ctxline = (f"THE FINALE ({r_['title']}): the team is at the {w.room_name(r_['room'])}, about to try it for real: {r_['blurb']}. TereVi (over the monitor or the speakers) tries to stop, "
                       "mock or bargain with them. It may still go wrong. Show the tension, the plan being executed and what is at stake. Write 8 to 12 lines.\n")
        elif mode == "occasion" and self.occasion_now:
            oc = self.occasion_now
            ctxline = (f"SPECIAL OCCASION: {self.nm(oc['host'])} is hosting a {oc['kind']} ({oc['text']}), attended by "
                       f"{', '.join(self.nm(x) for x in oc['attendees'])}. "
                       + (f"It is a PRANK on {', '.join(self.nm(x) for x in oc['secret_from'])}; show how it lands. " if oc.get("secret_from") else "")
                       + "Write 6 to 10 lines with a few action lines; something memorable happens (a laugh, an awkward moment, a spark, a small disaster, a confession).\n")
        elif case and case["announced"]:
            ctxline = (f"INVESTIGATION IN PROGRESS: {self.nm(case['victim'])} is dead and someone is responsible. People question each other, compare what they saw, ask where others were and who came and went, "
                       "share clues and voice suspicions, in character; accounts can be wrong or false. The culprit, if present, deflects, denies or points elsewhere and never confesses.\n")
        if mode in (None, "chat") and not (case and case["announced"]):
            ctxline += self.recent_scene_line()
        isl = self.island_line()
        if isl:
            ctxline += isl + "\n"
        if mode not in ("intro", "reveal", "finale", "endgame", "vigil"):
            ctxline += self.deadline_ctx()
        count = ("8 to 12 lines" if mode == "trial" else "6 to 10 lines" if mode == "occasion"
                 else "14 to 18 lines" if mode in ("intro", "lastcall") else "10 to 14 lines" if mode in ("reveal", "finale", "vigil")
                 else "3 to 8 lines TOTAL, each line max 22 words")
        rule = s.get("rule")
        ruleline = ""
        if rule:
            ruleline = ("TODAY'S RULE (everyone knows it and NeoVi punishes clear violations): " + rule["text"] +
                        " The characters remember this while they talk: they usually obey, and only bend or defy it knowingly, with the risk in mind.\n")
        return (
            f"SCENE: Day {self.day}, {hhmm(hour)}, {w.room_name(room)}. Items visible: {self.items_text(s['room_items'].get(room, {}))}.\n"
            + ctxline + ruleline + self.house_line() + self.tone_paragraph(group) + "PEOPLE PRESENT:\n" + "\n".join(cards) + "\n"
            + (f"EARLIER IN THIS ROOM: {' / '.join(prev[-4:])}\n" if prev else "")
            + f"Write the next stretch of conversation among them as a short scene: {count}, "
              "natural spoken dialogue (no quotation marks). Not everyone must speak. Keep secrets secret. "
              "Mix speech with brief ACTION lines: {\"kind\": \"act\"} lines describe what someone physically does to another person or to the surroundings "
              "(shoves, hugs, steals, cooks, flicks water, jams a door, turns the music up, tests a lock...). An action line never contains the person's name and starts with a verb "
              "('slides the knife drawer shut'), max 18 words; speech lines are \"kind\": \"say\". Actions can have consequences, expressed in the effects. "
              "Make it organic: people react to what was just said and done, to their own mood and to how they feel about each other; "
              "ordinary warmth, awkwardness, jokes, curiosity and small frictions are normal, and real meanness needs a cause. "
              "HOW REAL PEOPLE TALK: plain, natural speech, the way people talk when they are scared, tired, annoyed or kind. Short sentences, mostly about concrete things: what they saw, want, fear, plan or owe. "
              "Each line answers what the previous speaker actually said (or clearly dodges it). NO stacked metaphors, NO clever quip in every line, NO wordplay for its own sake, NO hashtags or internet slang, "
              "NO pet name in every sentence, NO non-sequiturs and no line that only sounds witty. People repeat themselves, trail off, interrupt, misunderstand each other and say less than they feel; "
              "they do not explain their own emotions in poetic terms. Voices differ by vocabulary and rhythm (check each card), not by catchphrases. Action lines are specific and physical, never poetic. "
              "Each card gives the tone that fits that person toward each other person; follow it. Swearing is fine when it fits. No slurs against protected groups. "
              "PROPS: a person can only use, hold, hand over or pull out what their card lists under Carrying, what is listed as visible in the scene, or this room's ordinary supplies; never invent an object (no binoculars from a jacket unless they are listed). "
              "TereVi (if present) is on the monitor: she meddles and teases. NeoVi (if present) is frightened, terse and secretly sympathetic. "
              "Reply as JSON: {\"lines\": [{\"speaker\": \"<person id>\", \"kind\": \"say|act\", \"text\": \"...\"}], "
              "\"effects\": {\"affinity\": [{\"from\": \"id\", \"to\": \"id\", \"delta\": -3..3}], "
              "\"sanity\": {\"id\": -4..0}, \"hp\": {\"id\": -3..3}, \"why\": {\"id\": \"<=8 words reason\"}, "
              "\"special\": [{\"kind\": \"comfort|confession|romance|laughter|gift|teamwork|meal|movie|party|prank|game\", \"who\": [\"ids\"], \"why\": \"<=8 words\"}], "
              "\"bonds\": [{\"a\": \"id\", \"b\": \"id\", \"kind\": \"romance|feud|pact\"}], "
              "\"reveals\": [{\"by\": \"id\", \"about\": \"id\", \"to\": [\"ids present\"]}], "
              "\"moves\": [{\"id\": \"person id\", \"to\": \"adjacent room id\"}], "
              "\"rumors\": [{\"by\": \"id\", \"about\": \"id\", \"claim\": \"<=16 words\", \"tone\": \"good|bad\", \"lie\": true|false}], "
              "\"incite\": [{\"by\": \"id\", \"target\": \"id\", \"victim\": \"id\", \"how\": \"persuade|trick|blackmail|lure\", \"claim\": \"<=18 words of what was said\"}], "
              "\"gives\": [{\"from\": \"id\", \"to\": \"id\", \"item\": \"item id\", \"qty\": 1}], "
              "\"notes\": {\"id\": \"<=15 word private note of what they will remember\"}}}. "
            "AFFINITY: write an entry for every ordered pair that interacted (A toward B, and B toward A if B was affected), with a NONZERO delta unless truly nothing passed between them: "
            "a kind word +1, a shared laugh +1 or +2, real support or a confession +2 or +3, a jab -1, an insult or breach of trust -2, cruelty or a humiliating scene -3. "
            "The two directions can differ. Relationships can flourish into romance or sour into hatred over time. "
            "SANITY: hurtful or frightening exchanges cost the people involved sanity (-1 to -4); ordinary talk restores NOTHING. Sanity returns only through a genuinely special moment: "
            "list it in effects.special (a heartfelt comfort or confession, a romantic spark, helpless laughter, a gift, real teamwork, a shared meal, movie or party, a vigil for the dead); "
            "add \"depth\": 1 to 3 to an entry for how deeply touching it was (3 = tears, an embrace, a real vow): between people who truly love each other a deep moment restores far more. "
            "Use effects.bonds only when a romance (both feel strongly warm, 5+), a pact/alliance (both trust each other, 3+) or a feud (both strongly hostile) has truly formed. "
            "Use effects.reveals when someone actually blurts out, trades or leaks a secret they know (or confesses their own); only people who know a secret can reveal it. "
            "People with a dark impulse or a low sanity may snap, lash out, confess, betray or do something shocking; show it. "
            "Use effects.moves only when an action physically moves someone to an adjacent room (a shove, a drag, a lure). A shove or fight costs health. "
            "Use effects.rumors when someone actually passes on gossip about a third person (true or invented). "
            "Use effects.incite only when someone is actively working on a person to hurt or kill a third (persuading, tricking with a lie, blackmailing, luring); leave it empty otherwise. "
            "Characters who are error-prone (low sanity or health) slip: they fumble, mix things up and say too much. "
            "Use effects.accomplice: [{\"by\": \"id\", \"helper\": \"id\", \"role\": \"lookout|alibi|cleanup|weapon\", \"victim\": \"id\"}] only when someone who is actively plotting a killing openly asks a trusted person for help; leave it empty otherwise. "
            "During an investigation add effects.testimonies: [{\"by\": \"id\", \"claim\": \"<=22 words\"}] for any statement about where someone was or what they saw or did around the time of the death (a culprit's statement may be a lie)."
        )

    def talk_system(self):
        return (self.bible() + " You are the director of a character-driven adult drama. You write believable dialogue that is funny, tense, awkward, tender or "
                "vicious as each character's feelings, mood and health demand, strictly in their own voices and with only what each person knows. "
                "Your dialogue is grounded and human: plain words, short lines, concrete content, no showy cleverness. "
                "Swearing and insults are fine when they fit the relationship; gratuitous meanness is not. Reply with a single JSON object and nothing else.")

    # ---------- the tick ----------
    SEGMENTS = {8: ("Morning announcement", "TereVi has something to say."), 10: ("Free time", "The morning is yours."), 12: ("Midday gathering", "Everyone is called together."),
                14: ("Free time", "The afternoon begins."), 16: ("Free time", "The afternoon wears on."), 18: ("Evening gathering", "Everyone is called together."),
                20: ("Free time", "The evening is yours."), 22: ("Night", "The lights go down.")}

    def segment_msg(self, hour, kind):
        """The title shown when a new part of the day begins (the free-time blocks only when the free-time dial is on)."""
        title, sub = self.SEGMENTS.get(hour, (None, None))
        if title == "Free time" and kind != "free":
            title, sub = {10: ("Morning", "The day goes on."), 14: ("Afternoon", "The day goes on."), 16: ("Late afternoon", "The day goes on."), 20: ("Evening", "The day goes on.")}.get(hour, (None, None))
        return {"title": title, "sub": sub, "hour": hour, "free": kind == "free"} if title else None

    def run_tick(self, hour, kind=None):
        w, s = self.world, self.s
        ids = list(w.agents.keys())
        tick = self.new_tick(hour)
        self.clock_start()
        self.sim_turn(tick)
        self.convo_reset()
        tick["segment_msg"] = self.segment_msg(hour, kind)
        s["_hour"] = hour
        if self.degrade_note:
            tick["events"].append({"type": "system", "who": "terevi", "room": "foyer", "vis": "viewer", "text": self.degrade_note})
            self.degrade_note = None
        self.apply_gm(tick, hour)
        self.light_tick()

        if kind == "morning":
            for nid in self.arrivals:
                if nid in w.agents:
                    self.log_event(tick, {"type": "arrival", "who": nid, "room": w.agents[nid]["room"], "vis": "public",
                                          "text": f"Newcomer {w.cast[nid]['name']} ({w.cast[nid]['role']}) steps onto the island."}, witnesses=ids, actor=nid)
            self.broadcast_text = self.make_broadcast("morning", {"arrivals": self.arrivals, "intro": not self.revealed})
            tick["broadcasts"].append({"speaker": "terevi", "kind": "morning", "text": self.broadcast_text})
            for cid in ids:
                w.remember(cid, f"{hhmm(hour)} TereVi announced: {self.broadcast_text[:220]}")
            for nid in self.arrivals:
                if nid in w.agents:
                    for cid in ids:
                        if cid != nid and cid in w.agents and w.agents[cid]["sanity"] < 85:
                            self.stat(tick, cid, "sanity", 3, "a new face on the island")
            s["arrivals"] = []
            self.arrivals = []
            if s.get("rule"):
                r_ = s["rule"]
                tick["rule_announce"] = {"id": r_["id"], "title": r_["title"], "short": r_["short"], "text": r_["text"]}
            self.rule_notice(tick)
            if not self.aftermath_active():
                self.deadline_dread(tick)
            self.scenario_twist(tick, hour)

        # NeoVi walks her routine first
        nroom = self.neovi_target(hour)
        nstart = s["npcs"]["neovi"]["room"]
        npath = [nstart]
        if nroom != nstart:
            steps = w.path("neovi", nstart, nroom) or []
            npath += [r for r, _, _ in steps]
            s["npcs"]["neovi"]["room"] = npath[-1]
        tick["moves"]["neovi"] = {"from": nstart, "path": npath, "to": npath[-1]}

        # Roommates may wake up next to a body
        self.check_discovery(tick, hour)
        self.roll_impulses(hour)
        self.tick_incitements()
        self.check_threats(tick, hour)
        self.scenario_events(tick, hour)
        self.maybe_island_event(tick, hour)

        self.pick_focus(hour)
        self.maybe_start_plots(tick, hour)
        decisions, intents, attacks = {}, {}, []
        rule = s.get("rule")
        self.rule_ctx = {}
        pre = []
        if rule and rule["id"] == "leader" and rule["params"]["leader"] in w.agents:
            leader = rule["params"]["leader"]
            d, err = self.decide(leader, hour)
            decisions[leader] = d
            if err:
                tick["errors"].append(err)
                self.log_event(tick, {"type": "system", "who": leader, "room": w.agents[leader]["room"], "text": err, "vis": "gm"})
            self.apply_decision(tick, leader, d, intents, attacks)
            self.rule_ctx = {"leader": leader, "room": w.agents[leader]["room"], "activity": d["activity"]}
            pre.append(leader)
        rest = [c for c in ids if c not in pre]
        for cid, (d, err) in self.decide_many(rest, hour).items():
            decisions[cid] = d
            if err:
                tick["errors"].append(err)
                self.log_event(tick, {"type": "system", "who": cid, "room": w.agents[cid]["room"], "text": err, "vis": "gm"})

        self.mark_busy(decisions)
        self.plot_pileup(tick, hour)
        self.maybe_spree(tick, hour)
        attacks.extend(self.spree_override(tick, decisions))
        self.focus_override(decisions)
        self.plot_tick(tick, hour, decisions)
        # everybody sets off at their own minute; what they came to do happens when they get there, in the order they arrive
        arrivals = []
        for cid in self.apply_order(rest):
            self.apply_decision(tick, cid, decisions[cid], intents, attacks, defer=arrivals)
        self._m = 0.0
        self._arrived = {cid: m for m, cid, _, _ in arrivals}
        tl = Timeline(self)
        for m, cid, d, start in arrivals:
            tl.at(m, self.arrive_and_act, tick, cid, d, intents, attacks, start)
        tl.run()
        self.sim_sync(tick, self._m)
        self.clock_to(15)
        self.stale_notices(decisions)
        if hour >= 20:
            self.auto_sleep(hour)
        self.update_plots(tick, decisions, hour)
        self.auto_recruit(tick, hour)
        self.observe_movement(tick, hour)
        self.resolve_traps(tick, hour)
        self.stealth_passive(tick, hour)
        self.auto_stealth(tick, hour, decisions)
        self.auto_secrets(tick, hour, decisions)
        self.withhold_tick(tick, hour)
        self.hook_tick(tick, hour)
        self.condition_tick(tick, hour)
        self.neovi_active_tick(tick, hour)
        self.auto_clothes(tick, hour, decisions)
        self.maybe_form_alliances(tick, hour)
        self.alliance_tick(tick, hour)
        tick["events"].extend(s.pop("_pending_events", []))

        if attacks:
            tl = Timeline(self)
            for cid, d in attacks:
                tl.at(self.meet_minute(cid, d.get("target")), self.strike, tick, cid, d, hour)
            tl.run()
        self.clock_to(20)
        assaults, sabs, self.assaults, self.sabotages = self.assaults, self.sabotages, [], []
        self.resolve_assaults(tick, assaults, hour)
        self.resolve_sabotages(tick, sabs, hour)
        self.resolve_impulses(tick, hour, decisions, intents)
        self.resolve_end_lives(tick, hour)
        meal_draw, meal_m = self.meal_in_turn(hour)
        if meal_draw and not s.get("over") and not (self.occasion_now and self.occasion_now.get("where") == meal_draw["room"]):
            self.clock_to(max(self._m, meal_m))
            self.meal_call(tick, hour, meal_draw, self._m)
        if kind == "free" and not s.get("over"):
            self.free_time(tick, hour, decisions)
            self.clock_to(90)
        else:
            self.clock_to(40)
        self.hazard_check(tick, hour)
        self.check_discovery(tick, hour)
        self.investigation_upkeep(tick, hour)
        self.neovi_shares_footage(tick, hour)
        self.spree_upkeep(tick, hour)
        if self.revealed:
            self.resolve_experiments(tick, hour)
            self.adapt_check(tick, hour)
        self.resolve_occasion(tick, hour)
        self.queue_occasion(tick, hour)
        self.tease_rooms = set()
        if self.revealed:
            self.terevi_intervention(tick, hour, self.force_tease)
        self.force_tease = None
        self.enforce_rule(tick, hour)
        self.sim_sync(tick, self._m)                            # whoever those systems moved walks there now
        self.clock_to(60)
        self.tick_dread(tick, hour)
        self.baseline_drain(tick, hour)
        self.pressure_drain(tick, hour)
        self.friction_tick(tick, hour)
        self.aftermath_comfort(tick, hour)

        # Conversations
        groups, modes = {}, {}
        oc = self.occasion_now
        for room in ROOMS:
            occ = list(w.occupants(room))
            humans = [o for o in occ if o in w.agents]
            if not humans:
                continue
            tv = room in self.tease_rooms or (ROOMS[room][1] != "grounds" and self.rng.random() < 0.7 and any(
                "terevi" in decisions[h]["talk_to"] for h in humans if h in decisions))
            if tv:
                occ.append("terevi")
            if not tv and not (oc and oc["where"] == room):
                occ = self.hearing_cluster(room, occ, [h for h in humans if h in decisions and decisions[h]["talk_to"]])
                humans = [o for o in occ if o in w.agents]
            if len(occ) < 2:
                continue
            wants = any(t in occ for h in humans for t in decisions[h]["talk_to"] if h in decisions)
            p = 0.95 if wants else (0.55 if len(humans) >= 2 else 0.2)
            if not wants and self.engine_decisions_on() and humans and sum(self.mind(h)["needs"]["social"] for h in humans) / len(humans) >= 70:
                p *= 0.55                       # people whose need for company is met do not go looking for a chat
            if s.get("case") and s["case"]["announced"] and len(humans) >= 2:
                p = 0.95
            if tv:
                p = 1.0
            if oc and oc["where"] == room and len(humans) >= 2:
                p, modes[room] = 1.0, "occasion"
            meal_ = self.__dict__.get("_meal")
            if meal_ and meal_["room"] == room and len(humans) >= 2:
                p = 1.0                                         # people at the table talk
            if self.rng.random() < p:
                groups[room] = occ
        self._talk_meta = {}
        self.clock_to(92 if kind == "free" else 56)
        self.sim_sync(tick, self._m)
        if kind == "free":
            groups, modes = self.free_chat_groups(tick, groups, modes, intents)
        # ordinary conversations are live (the engine resolves every move as it happens); staged ones (an occasion, TereVi on the monitor) are still written whole
        staged = {g: occ for g, occ in groups.items() if self.staged_talk(g, occ, modes)}
        live = [(g, occ) for g, occ in groups.items() if g not in staged]
        if live:
            tl = Timeline(self)
            m_talk = self._m
            for gi, (g, occ) in enumerate(live):
                humans = [o for o in occ if o in w.agents]
                want = [h for h in humans if decisions.get(h, {}).get("talk_to")]
                order = want + [h for h in humans if h not in want]
                self.start_convo(tick, order, g.split("#")[0], m_talk + 2 * gi, tl, why=intents.get(order[0], "") if order else "", kind="gather",
                                 dur=max(10.0, (120 if kind == "free" else 60) - (m_talk - (92 if kind == "free" else 56))))
            tl.run()
        if staged:
            self.run_conversations(tick, staged, intents, hour, modes=modes)
        self.voice_convos(tick, hour)
        self.sim_talk(tick)
        self.meal_settle(tick, hour)
        self.clock_to(min(118.0, max([s_["m"] + 1.0 for s_ in self._sim_said] or [self._m])))
        self.reaction_pass(tick, hour)
        self.occasion_now = None
        self.island_tick_effects(tick, hour)
        self.enforce_ai_rule(tick, hour)
        self.booth_turn(tick, hour, kind)
        self.voice_booth(tick, hour)
        self.inner_turn(tick, hour)                               # thoughts and muttering (innervoice.py)

        if hour >= 20 and hour - self.step < 20 and self.revealed:
            text = self.make_broadcast("evening", {})
            tick["broadcasts"].append({"speaker": "terevi", "kind": "evening", "text": text})
            for cid in w.agents:
                w.remember(cid, f"{hhmm(hour)} TereVi announced: {text[:220]}")
        self.director_after_tick(tick, hour)
        return tick

    def item_within_reach(self, room, item):
        from .data_world import COMMON_ITEMS
        return self.s["room_items"].get(room, {}).get(item, 0) > 0 or item in COMMON_ITEMS.get(room, [])

    def resolve_item(self, room, item):
        """The models name things loosely ("pencils" for the Coloured pencils): match what they asked for against what is really here, by id, by name, or by a word of either."""
        from .data_world import COMMON_ITEMS
        w = self.world
        have = [k for k, q in self.s["room_items"].get(room, {}).items() if q > 0] + list(COMMON_ITEMS.get(room, []))
        if not item or item in have:
            return item
        want = str(item).lower().replace("_", " ").strip()
        stem = want[:-1] if want.endswith("s") else want
        best = None
        for k in have:
            nm = w.item_name(k).lower()
            kid = k.lower().replace("_", " ")
            score = 3 if want in (nm, kid) else 2 if (want in nm or want in kid or nm in want or stem in nm or stem in kid) else 0
            if score and (best is None or score > best[0]):
                best = (score, k)
        return best[1] if best else item

    def recent_scene_line(self):
        """What the other scenes of the day already used, so the next one finds something new."""
        log = self.__dict__.get("_scene_acts")
        if not log or log.get("day") != self.day or not log["items"]:
            return ""
        return "ALREADY USED IN EARLIER SCENES TODAY (do not repeat these props, gestures or lines; find something new): " + " | ".join(log["items"][-8:]) + "\n"

    def note_scene(self, lines):
        log = self.__dict__.setdefault("_scene_acts", {"day": self.day, "items": []})
        if log["day"] != self.day:
            log["day"], log["items"] = self.day, []
        for l in lines:
            if l["kind"] == "act":
                log["items"].append(f"{self.nm(l['speaker'])} {l['text'][:60]}")
        if lines:
            log["items"].append(f"line: \"{lines[0]['text'][:50]}\"")
        del log["items"][:-14]

    def do_take(self, tick, cid, d, here):
        w = self.world
        a = w.agents[cid]
        name = self.nm(cid)
        item = d["item"] = self.resolve_item(a["room"], d["item"])
        if not self.roll(cid, 0.94)[0]:
            q, err = None, "fumbles it"
        else:
            q, err = w.take(cid, item, d["qty"])
        if q:
            self.note_holder(cid, item, tick["hour"])
            self.log_event(tick, {"type": "take", "who": cid, "room": a["room"], "vis": "public",
                                  "text": f"{name} picks up {q} x {w.item_name(item)}."}, witnesses=here, actor=cid)
        else:
            if err != "fumbles it":                                  # a dropped item is just clumsiness, not something for the GM to flag
                self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{name} could not take {item}: {err}."}, actor=cid)
            w.remember(cid, f"{hhmm(tick['hour'])} You reached for the {w.item_name(item)} but could not get it ({err}).")

    def apply_decision(self, tick, cid, d, intents, attacks, defer=None):
        """Carry out a decision. With `defer` (a list), only the setting off happens now: they leave at their own minute in the first quarter hour and walk; what they came to do
        is appended to `defer` as (arrival minute, cid, decision, room they left) for the turn to run at that minute."""
        w, s = self.world, self.s
        a = w.agents[cid]
        start = a["room"]
        turn_clock = defer is not None and self.__dict__.get("_turn_clock")
        if turn_clock:
            self.clock_to(0.0)
            self._m = float(self._stagger(cid, tick))           # each sets off at their own minute
        a["activity"] = d["activity"]
        self.note_acts(cid, d["activity"])
        self.note_decision(cid, d)
        if a.get("out"):
            tick["moves"][cid] = {"from": start, "path": [start], "to": start}
            a["activity"] = "Unconscious"
            if turn_clock:
                self._m = 0.0
            return
        if self.restrained(cid) and (d["target_room"] or d["action"] not in ("stay", "rest", "free", "search", "give", "use")):
            d["target_room"], d["action"] = "", "stay"
            w.remember(cid, f"{hhmm(tick['hour'])} You strain against the handcuffs and get nowhere.")
        if d.get("night") and tick["hour"] >= 18:
            self.night_votes.add(cid)
        if d.get("sleep_in") in ROOMS and tick["hour"] >= 16:
            a["sleep_pref"] = [self.day, d["sleep_in"]]
        ra = a.setdefault("recent_actions", [])
        ra.append(d["action"])
        del ra[:-8]
        a["sneaking"] = bool(d.get("sneak")) and self.revealed
        a["spying"] = None
        if a.get("hiding") and (d["action"] not in ("hide", "stay", "rest", "spy") or d["target_room"]):
            self.emerge(tick, cid, quiet=bool(d["target_room"]))
            if d["target_room"]:
                a["sneaking"] = True
        tick["thoughts"][cid] = d["thought"]
        intents[cid] = d["intent"]
        name = self.nm(cid)
        if d["action"] == "take" and d["item"] and d["target_room"] and d["target_room"] != start and self.item_within_reach(start, d["item"]):
            # the model saw the item in the room it is leaving: pick it up before walking out (the take used to be tried in the new room)
            self.do_take(tick, cid, d, [o for o in w.occupants(start) if o != cid])
            d["item"] = ""
        if d["target_room"] and d["target_room"] != start:
            before = [o for o in w.occupants(start) if o != cid]
            mv = w.move(cid, d["target_room"], int(MOVE_BUDGET * self.step * (0.6 if a.get("sneaking") else 1) * self.move_factor(cid) * (0.5 if d["action"] == "carry" else 1.0)))
            tick["moves"][cid] = {"from": start, "path": mv["path"], "to": a["room"]}
            for ev in mv["events"]:
                self.log_event(tick, ev, witnesses=before, actor=cid)
            self.traversal_risks(tick, cid, mv)
            tick["moves"][cid]["to"] = a["room"]
            dest_room = a["room"]
            if a["room"] != start:
                pth = mv["path"]
                self.log_event(tick, {"type": "move", "who": cid, "room": start, "vis": "public",
                                      "text": f"{name} {'slips out of' if a.get('sneaking') else 'leaves'} {w.room_name(start)} for {w.room_name(a['room'])}."}, actor=cid)
                for o in before:
                    self.witness(o, {"type": "leave", "who": cid, "room": start, "to": pth[1] if len(pth) > 1 else a["room"], "hour": tick["hour"]})
                if turn_clock:
                    self._m = self.sim_go(tick, cid, self._m)         # the walk: they arrive when they get there
                if cid in w.agents and a["room"] == dest_room:        # (unless they fell on the way)
                    arrivals = [o for o in w.occupants(a["room"]) if o != cid and self.present(o, a["room"])]
                    self.log_event(tick, {"type": "arrive", "who": cid, "room": a["room"], "vis": "public",
                                          "text": f"{name} {'slips into' if a.get('sneaking') else 'arrives in'} {w.room_name(a['room'])}."}, actor=cid)
                    for o in arrivals:
                        self.witness(o, {"type": "arrive", "who": cid, "room": a["room"], "frm": pth[-2] if len(pth) > 1 else start, "hour": tick["hour"]})
                    self.vault_traps(tick, cid)
            if mv["blocked"] and not mv["arrived"] and a["room"] == start and self.revealed and self.shut_in(cid) and self.outside_windows(start) and self.climb_out(tick, cid):
                if cid in w.agents and not w.agents[cid].get("out") and a["room"] != start:
                    mv2 = w.move(cid, d["target_room"], int(MOVE_BUDGET * self.step * self.move_factor(cid)))
                    tick["moves"][cid] = {"from": start, "path": [start] + mv2["path"], "to": a["room"]}
                    mv = {**mv2, "blocked": mv2["blocked"]}
                    dest_room = a["room"]
                    if turn_clock:
                        self._m = self.sim_go(tick, cid, max(self._m, self.sim().end_t(cid)))
                else:
                    if turn_clock:
                        self._m = 0.0
                    return
            if mv["blocked"] and not mv["arrived"]:
                self.log_event(tick, {"type": "blocked", "who": cid, "room": a["room"], "vis": "public",
                                      "text": f"{name} is stopped: {mv['blocked']}."}, witnesses=w.occupants(a["room"]), actor=cid)
        else:
            tick["moves"][cid] = {"from": start, "path": [start], "to": start}
            dest_room = start
        if turn_clock:
            d["_dest"] = dest_room
            defer.append((self._m, cid, d, start))
            self._m = 0.0
            return
        self.apply_act(tick, cid, d, intents, attacks, start)

    def shut_in(self, cid):
        """Locked in (the door is bolted and they have no key) or every way out is barred."""
        w = self.world
        room = w.agents[cid]["room"]
        lk = self.s.get("locks", {}).get(room)
        if lk and lk.get("keyed") and not w.has_room_key(cid, room):
            return True
        exits = [x for x in w.adjacent(cid, room) if x["kind"] != "secret"]
        return bool(exits) and not any(x["ok"] for x in exits)

    def staged_talk(self, gid, occ, modes):
        """Conversations still written whole by the model: occasions and anything TereVi takes part in from the monitor."""
        return (modes or {}).get(gid) not in (None, "chat") or "terevi" in occ

    def arrive_and_act(self, tick, cid, d, intents, attacks, start):
        a = self.world.agents.get(cid)
        if a and d.get("_dest") and a["room"] != d["_dest"]:
            return                                              # they never got there (a fall on the way)
        if a and not a.get("out"):
            self.apply_act(tick, cid, d, intents, attacks, start)

    def meet_minute(self, cid, target):
        """When an attacker and their target are first in the same room: once both have arrived (the attacker strikes on arrival if the target is not coming)."""
        arr = self.__dict__.get("_arrived") or {}
        ta = arr.get(cid, self._m)
        w = self.world
        if target in w.agents and cid in w.agents and w.agents[target]["room"] == w.agents[cid]["room"]:
            sm = self.sim()
            tt = arr.get(target, sm.end_t(target) if target in sm.tracks else ta)
            return max(ta, tt, self._m)
        return max(ta, self._m)

    def strike(self, tick, cid, d, hour):
        self.resolve_attacks(tick, [(cid, d)], hour)
        self.sim_sync(tick, self._m)

    def apply_act(self, tick, cid, d, intents, attacks, start):
        """What somebody came to do, done where they are now."""
        w, s = self.world, self.s
        a = w.agents[cid]
        name = self.nm(cid)
        here = [o for o in w.occupants(a["room"]) if o != cid and self.present(o, a["room"])]
        act, item = d["action"], d["item"]
        if act == "take" and item:
            self.do_take(tick, cid, d, here)
        elif act == "drop" and item:
            q, err = w.drop(cid, item, d["qty"])
            if q:
                self.log_event(tick, {"type": "drop", "who": cid, "room": a["room"], "vis": "public",
                                      "text": f"{name} leaves {q} x {w.item_name(item)} here."}, witnesses=here, actor=cid)
        elif act == "give" and item and d["to"] == "neovi":
            self.give_to_neovi(tick, cid, item)
        elif act == "give" and item and d["to"]:
            q, err = w.give(cid, d["to"], item, d["qty"])
            if q:
                self.note_holder(d["to"], item, tick["hour"])
                self.log_event(tick, {"type": "give", "who": cid, "room": a["room"], "vis": "public",
                                      "text": f"{name} gives {q} x {w.item_name(item)} to {self.nm(d['to'])}."}, witnesses=here, actor=cid)
            else:
                self.log_event(tick, {"type": "system", "who": cid, "room": a["room"], "vis": "gm", "text": f"{name} could not give {item}: {err}."}, actor=cid)
                w.remember(cid, f"{hhmm(tick['hour'])} You tried to give {self.nm(d['to'])} the {w.item_name(item)} but could not ({err}).")
        elif act == "use" and item:
            eff, err = w.use(cid, item, d["qty"])
            if eff is not None:
                self.log_event(tick, {"type": "use", "who": cid, "room": a["room"], "vis": "public",
                                      "text": f"{name} uses the {w.item_name(item)}."}, witnesses=here, actor=cid)
                self.after_use(tick, cid, item)
        elif act in ("search", "investigate"):
            self.log_event(tick, {"type": "search", "who": cid, "room": a["room"], "vis": "public",
                                  "text": f"{name} {'investigates' if s.get('case') else 'searches'} {w.room_name(a['room'])}: {d['activity']}"},
                           witnesses=here, actor=cid)
            self.reveal_clues(tick, cid)
            self.search_for_hidden(tick, cid, d["activity"] + " " + d["thought"])
            if self.revealed:
                self.rifle_room(tick, cid, d)
            if act == "search":
                mult = 0.0 if self.rng.random() < 0.04 else self.success_p(cid, 0.9) / 0.9 * (0.5 if self.in_dark(cid) else 1.0)
                for ev in w.search(cid, d["activity"] + " " + d["thought"], mult):
                    self.log_event(tick, ev, actor=cid)
        elif act == "rest":
            a["hp"] = clamp(a["hp"] + 1)
            self.rest_heal(tick, cid)
        elif act == "experiment" and d["idea"]:
            self.experiments.append((cid, d))
            self.exp_today += 1
        elif act == "attack" and self.murders:
            if self.motive_ok(cid, d.get("target"), d) or getattr(self.llm, "mock", False):      # the mock's forced attacks are a test knob
                attacks.append((cid, d))
            else:
                self.log_event(tick, {"type": "system", "who": cid, "room": w.agents[cid]["room"], "vis": "gm",
                                      "text": f"{self.nm(cid)} thought about hurting {self.nm(d.get('target'))}, but had no real reason to, and could not."}, actor=cid)
        elif act == "end_life" and self.murders:
            self.end_lives.append((cid, d))
        elif act == "build":
            self.do_build(tick, cid, d)
        elif act == "hide" and self.revealed:
            self.do_hide(tick, cid, d)
        elif act == "spy" and self.revealed:
            self.do_spy(tick, cid, d)
        elif act == "stash" and self.revealed and d.get("stash"):
            self.do_stash(tick, cid, d)
        elif act == "retrieve" and self.revealed:
            self.do_retrieve(tick, cid, d)
        elif act == "hide_body" and self.murders:
            self.do_hide_body(tick, cid, d)
        elif act == "knockout" and self.murders:
            self.do_knockout(tick, cid, d)
        elif act == "carry" and self.revealed:
            d["_carry_start"] = start
            self.do_carry(tick, cid, d)
        elif act == "rob" and self.revealed:
            self.do_rob(tick, cid, d)
        elif act == "wake" and self.revealed:
            self.do_wake(tick, cid, d)
        elif act == "treat" and self.revealed:
            self.do_treat(tick, cid, d)
        elif act == "stage" and self.murders:
            self.do_stage(tick, cid, d)
        elif act == "restrain" and self.revealed:
            self.do_restrain(tick, cid, d)
        elif act == "free" and self.revealed:
            self.do_free(tick, cid, d)
        elif act == "knock" and self.revealed:
            self.do_knock(tick, cid, d)
        elif act == "craft" and self.revealed:
            self.do_craft(tick, cid, d)
        elif act == "lock" and self.revealed:
            self.do_lock(tick, cid, d)
        elif act == "unlock" and self.revealed:
            self.do_unlock(tick, cid, d)
        elif act == "pick" and self.revealed:
            self.do_pick(tick, cid, d)
        elif act == "break" and self.revealed:
            self.do_break(tick, cid, d)
        elif act == "barricade" and self.revealed:
            self.do_barricade(tick, cid, d)
        elif act == "frisk" and self.revealed and d.get("frisk") in w.agents:
            self.do_frisk(tick, cid, d["frisk"])
        elif act == "rig" and self.murders:
            self.do_rig(tick, cid, d)
        elif act == "interrogate" and d["target"] in w.agents and d["target"] != cid:
            intents[cid] = f"INTERROGATE {self.nm(d['target'])}: {d['idea'] or 'where were you, what did you see, who did you see?'}"
            d["talk_to"] = list(dict.fromkeys(list(d["talk_to"]) + [d["target"]]))
            self.press_withheld(tick, cid, d["target"], tick["hour"])
            self.hook_press(tick, cid, d["target"], tick["hour"])
            self.interrogate_witness(tick, cid, d["target"], tick["hour"])
        elif act == "assault" and self.murders:
            self.assaults.append((cid, d))
        elif act == "sabotage" and self.murders:
            self.sabotages.append((cid, d))
        if d.get("conceal") and self.revealed:
            self.do_conceal(tick, cid, d["conceal"])
        if d.get("keep_back"):
            self.keep_back(tick, cid, d["keep_back"])
        if d.get("disclose"):
            self.reveal_all(tick, cid, "chooses to come clean", tick["hour"])
        if d.get("wear") and self.revealed:
            self.wear(tick, cid, d["wear"])
        if d.get("betray") and d["betray"] in self.allies_of(cid):
            self.betray(tick, cid, d["betray"], self.alliance_of(cid), tick["hour"])
        self.prune_concealed(cid)
        if d.get("host"):
            self.proposals.append((cid, d["host"]))

    def run_conversations(self, tick, groups, intents, hour, mode=None, modes=None):
        w, s = self.world, self.s
        results = {}

        asks = []
        for gid, group in groups.items():
            room = gid.split("#")[0]
            ctx = {"people": [{"id": p, "name": self.nm(p), "human": p in w.agents,
                               "lines": (w.char(p) or {}).get("mock_lines", [])} for p in group],
                   "mode": (modes or {}).get(gid, mode)}
            try:
                sysm, user = self.talk_system(), self.talk_prompt(room, group, intents, hour, (modes or {}).get(gid, mode))
            except Exception as e:
                tick["errors"].append(f"conversation in {w.room_name(room)} failed: {str(e)[:80]}")
                continue
            asks.append((gid, lambda sysm=sysm, user=user, ctx=ctx: self.llm.converse(sysm, user, ctx)))
        for gid, (res, err) in self.ask_parallel(asks).items():
            if err is not None:
                tick["errors"].append(f"conversation in {w.room_name(gid.split('#')[0])} failed: {str(err)[:80]}")
            else:
                results[gid] = res

        for gid, res in results.items():
            room = gid.split("#")[0]
            group = groups[gid]
            lines = []
            cap = 18 if (modes or {}).get(gid, mode) in ("trial", "intro", "reveal", "finale", "lastcall", "endgame") else 14
            for ln in (res.get("lines") or [])[:cap]:
                sp, tx = ln.get("speaker"), str(ln.get("text", "")).strip()
                if sp in group and tx:
                    kind_ = "act" if ln.get("kind") == "act" else "say"
                    tx = self.clean_line(sp, kind_, tx)        # "Slides the bottle" reads as "Cail slides the bottle"
                    if not tx:
                        continue
                    lines.append({"speaker": sp, "kind": kind_, "text": tx[:260]})
            lines = self.filter_props(tick, room, group, lines)
            self.tape_record(room, lines)
            self.note_scene(lines)
            for ln_ in lines:
                if ln_["kind"] == "act":
                    self.note_acts(ln_["speaker"], ln_["text"])
            if not lines:
                continue
            entry = {"room": room, "lines": lines}
            entry.update((getattr(self, "_talk_meta", None) or {}).get(gid, {}))
            tick["talk"].append(entry)
            self.last_talk[room] = [(f"*{self.nm(l['speaker'])} {l['text']}*" if l["kind"] == "act" else f"{self.nm(l['speaker'])}: {l['text']}") for l in lines]
            self.eavesdrop(tick, room, lines, hour)
            for ln in lines:
                for cid in group:
                    if cid in w.agents:
                        who = "You" if cid == ln["speaker"] else self.nm(ln["speaker"])
                        if ln["kind"] == "act":
                            w.remember(cid, f"{hhmm(hour)} {who} {ln['text'][:110]}" if who != "You" else f"{hhmm(hour)} You (action): {ln['text'][:110]}")
                        else:
                            w.remember(cid, f"{hhmm(hour)} {who} said: \"{ln['text'][:110]}\"")
            self.day_notable.append(f"In the {w.room_name(room)}: {self.nm(lines[0]['speaker'])} said \"{lines[0]['text'][:90]}\"")
            fx = res.get("effects") or {}
            self.apply_talk_fx(tick, room, group, fx, hour)
            self.talk_drift(group, lines, fx)
            if "neovi" in group:
                self.neovi_log.append(f"In the {w.room_name(room)}: " + " / ".join(
                    (f"*{self.nm(l['speaker'])} {l['text'][:60]}*" if l["kind"] == "act" else f"{self.nm(l['speaker'])}: {l['text'][:60]}") for l in lines)[:300])
            self.finish_occasion(tick, room, group)
            for cid_ in group:
                if cid_ in w.agents:
                    self.fix_memories(cid_, group, 0.4)

    def apply_talk_fx(self, tick, room, group, fx, hour, lines=None):
        """What a conversation changed: health, sanity, affinity, special moments, secrets, bonds, rumours, incitement, testimonies, accomplices, forced moves, gifts, notes.
        Social moves (social.py) send their outcomes here as they happen; staged scenes still send the model's effects."""
        w = self.world
        fx = fx or {}
        self.last_effects[room] = fx
        why = fx.get("why") or {}
        changed = set()
        for key, lim in (("sanity", 4), ("hp", 3)):
            for cid, dl in (fx.get(key) or {}).items():
                if cid in w.agents and cid in group:
                    try:
                        d_ = max(-lim, min(lim, int(dl)))
                    except Exception:
                        continue
                    if key == "sanity" and d_ > 0:
                        continue          # sanity only returns through special moments
                    if d_:
                        self.stat(tick, cid, key, d_, str(why.get(cid, "")) if isinstance(why, dict) else "")
                        changed.add((cid, key))
        for af in (fx.get("affinity") or [])[:14]:
            try:
                a, b, dl = af["from"], af["to"], max(-3, min(3, int(af["delta"])))
            except Exception:
                continue
            if a in group and b in group and a != b and dl:
                self.adjust_any_aff(a, b, dl)
                if dl <= -2:
                    self.day_notable.append(f"{self.nm(a)}'s feelings toward {self.nm(b)} soured.")
                # The interaction itself moves both people's mood unless the scene already set it.
                mood = dl if dl < 0 else 0        # warmth alone no longer restores sanity
                for who in (a, b):
                    if (who, "sanity") not in changed:
                        self.stat(tick, who, "sanity", mood, f"{self.nm(a)} and {self.nm(b)}: {dl:+d}")
                        changed.add((who, "sanity"))
        for sp_ in (fx.get("special") or [])[:3]:
            try:
                kind_, who_ = sp_["kind"], sp_["who"]
            except Exception:
                continue
            if kind_ in SPECIAL_SANITY and isinstance(who_, list):
                try:
                    depth = max(1, min(3, int(sp_.get("depth", 1))))
                except Exception:
                    depth = 1
                for cid in who_[:6]:
                    if cid in w.agents and cid in group:
                        others = [o for o in who_ if o != cid and o in w.agents]
                        close = (sum(w.agents[cid]["aff"].get(o, 0) for o in others) / len(others)) if others else 0
                        mult = 1.0 + (0.5 if close >= 5 else 0) + (0.5 if close >= 8 else 0)
                        if kind_ in ("comfort", "confession", "romance", "vigil"):
                            mult *= 1 + 0.25 * (depth - 1)
                        self.special_boost(tick, cid, SPECIAL_SANITY[kind_] * mult, str(sp_.get("why") or kind_)[:40], kind_)
                        if kind_ in ("comfort", "confession", "romance", "gift", "teamwork") and others:
                            why_ = str(sp_.get("why") or kind_)[:50]
                            for o_ in others[:2]:
                                self.add_tie(cid, o_, "close", f"{kind_} with {self.nm(o_)} ({why_}) on day {self.day}", 1 if depth >= 2 else 0)
        for rv in (fx.get("reveals") or [])[:2]:
            if isinstance(rv, dict) and isinstance(rv.get("to"), list):
                self.reveal_secret(tick, rv.get("by"), rv.get("about"), [c for c in rv["to"] if c in group], "lets slip")
        self.apply_bonds(tick, fx.get("bonds"), group)
        self.apply_rumors(tick, fx.get("rumors"), group, hour)
        self.apply_incite(tick, fx.get("incite"), group, hour)
        self.apply_testimonies(tick, fx.get("testimonies"), group, hour)
        self.apply_accomplice(tick, fx.get("accomplice"), group, hour)
        self.apply_forced_moves(tick, fx.get("moves"), group)
        for gv in (fx.get("gives") or [])[:3]:
            if isinstance(gv, dict) and gv.get("from") == "neovi":
                self.apply_neovi_gives(tick, gv, room, group)
                continue
            try:
                q, err = w.give(gv["from"], gv["to"], gv["item"], gv.get("qty", 1))
            except Exception:
                q = None
            if q:
                self.log_event(tick, {"type": "give", "who": gv["from"], "room": room, "vis": "public",
                                      "text": f"{self.nm(gv['from'])} gives {q} x {w.item_name(gv['item'])} to {self.nm(gv['to'])}."},
                               witnesses=group, actor=gv["from"])
        for cid, note in (fx.get("notes") or {}).items():
            if cid in w.agents and isinstance(note, str):
                w.remember(cid, f"{hhmm(hour)} (private) {note[:120]}")

    def talk_drift(self, group, lines, fx):
        """Anyone who spoke to each other drifts at least a little: warmer by default, colder if it hurt (staged scenes, whose effects come from the model)."""
        w = self.world
        sanity_fx = (fx or {}).get("sanity") or {}
        pairs = {(af.get("from"), af.get("to")) for af in ((fx or {}).get("affinity") or []) if isinstance(af, dict)}
        for k in range(1, len(lines)):
            x, y = lines[k - 1]["speaker"], lines[k]["speaker"]
            if x == y or x not in w.agents or y not in w.agents or (y, x) in pairs:
                continue
            hurt = any(isinstance(sanity_fx.get(z), (int, float)) and sanity_fx.get(z) < 0 for z in (x, y))
            w.adjust_aff(y, x, -1 if hurt else 1)
            pairs.add((y, x))

    # ---------- stats ----------
    def stat(self, tick, cid, key, delta, why="", lethal=None):
        """Change health or sanity, log notable changes for the GM, and keep values in range.
        With `lethal` (a cause of death), a fatal health loss is an accident that kills the person."""
        a = self.world.agents.get(cid)
        if not a or not delta:
            return
        if lethal and key == "hp" and delta < 0 and a["hp"] + delta <= 0 and self.murders and not self.s.get("case"):
            self.accident_death(tick, cid, lethal)
            return
        before = a[key]
        floor = 5 if key == "hp" else 0   # accidents and punishments never kill
        a[key] = max(floor, clamp(a[key] + delta)) if delta < 0 else clamp(a[key] + delta)
        got = a[key] - before
        if key == "sanity":
            self.mind_note(cid, got, why)
            self.check_madness(tick, cid, before)
        if abs(got) >= 2:
            self.log_event(tick, {"type": "stat", "who": cid, "room": a["room"], "vis": "gm",
                                  "text": f"{self.nm(cid)} {key} {got:+d}" + (f" ({why})" if why else "")})

    def dread_level(self):
        """0 (far away) to 5 (deadline day): grows as the deadline approaches."""
        if self.s.get("case") or not self.revealed:
            return 0
        left = self.days_left()
        return 0 if left >= 5 else min(5, 5 - left)

    def dread_feel(self):
        d = self.dread_level()
        if d >= 4:
            return "Panic is in the air and tempers are short."
        if d == 3:
            return "Everyone is visibly tense."
        if d >= 1:
            return "The deadline is starting to gnaw at everyone."
        return ""

    def deadline_dread(self, tick):
        w = self.world
        dread = self.dread_level()
        if not dread:
            return
        for cid in list(w.agents):
            self.stat(tick, cid, "sanity", -dread, "deadline dread")
        self.log_event(tick, {"type": "stat", "who": "terevi", "room": "foyer", "vis": "gm",
                              "text": f"The deadline looms (dread {dread}/5): everyone loses {dread} sanity."})

    def tick_dread(self, tick, hour):
        """Nerves keep fraying through the day when the deadline is tomorrow (in the evening), and on deadline day every hour costs more the nearer 22:00 gets."""
        if self.s.get("case"):
            return
        left = self.days_left()
        if left == 1 and hour >= 18:
            for cid in list(self.world.agents):
                self.stat(tick, cid, "sanity", -1, "deadline nerves")
        elif left <= 0:
            self.deadline_hours(tick, hour)

    def deadline_hour_loss(self, h):
        """Sanity lost in hour h of deadline day: 1 a hour in the morning, 2 in the afternoon, 3 in the last hours before 22:00."""
        return 1 + max(0, min(int(h), DAY_END - 1) - DAY_START) // 5

    def deadline_hours(self, tick, hour):
        """Charge every not-yet-charged hour of deadline day this turn covers (each hour once, whatever kind of turn it was)."""
        s = self.s
        seen = s.get("_dl_hours")
        if not seen or seen.get("day") != self.day:
            seen = s["_dl_hours"] = {"day": self.day, "hours": []}
        span = [h for h in range(int(hour), min(int(hour) + 2, DAY_END)) if h >= DAY_START and h not in seen["hours"]]
        if not span:
            return
        seen["hours"].extend(span)
        mult = self.tune("drain_mult")
        base = sum(self.deadline_hour_loss(h) for h in span)
        for cid in list(self.world.agents):
            a = self.world.agents[cid]
            if a.get("out"):
                continue
            x = base * mult * (1.0 if a["sanity"] >= 25 else 0.5 if a["sanity"] >= 10 else 0.25)  # past a point, people go numb
            n = int(x) + (1 if self.rng.random() < x - int(x) else 0)
            if n:
                self.stat(tick, cid, "sanity", -n, "the deadline is hours away")
        hrs = DAY_END - (span[-1] + 1)
        self.log_event(tick, {"type": "stat", "who": "terevi", "room": "foyer", "vis": "gm",
                              "text": f"Deadline day: {hrs} hour{'s' if hrs != 1 else ''} left until 22:00. Nerves fray ({base} sanity an hour-block, before numbness)."})

    # ---------- the daily rule (roulette) ----------
    def setup_rule(self):
        s, w = self.s, self.world
        mode = self.rule_mode
        self.rule_none_reason = ""
        self.rule_prev = {}
        if mode in (None, "", "none") or len(w.agents) < 3 or not self.revealed:
            s["rule"] = None
            self.rule_none_reason = ("the rule setting was 'no daily rule'" if mode in (None, "", "none") else
                                     "fewer than three people are left" if len(w.agents) < 3 else "the truth has not been revealed yet")
            return
        if mode == "custom":
            if not self.rule_text:
                s["rule"] = None
                self.rule_none_reason = "the rule was set to 'custom' but no rule text was typed"
                return
            s["rule"] = {"id": "custom", "title": "House Rule", "short": self.rule_text[:90],
                         "text": "HOUSE RULE: " + self.rule_text + " " + rulelib.PUNISHMENT_TEXT,
                         "params": {}, "strikes": {}, "ai": True, "source": "custom"}
            self.classify_today()
            return
        if mode == "roulette":
            s["rule"] = self.generate_rule()
            self.classify_today(getattr(self, "_rule_hint", None))
            if not s["rule"]:
                self.rule_none_reason = "the roulette could not produce a rule"
            return
        s["rule"] = rulelib.make_rule(mode, w, self.rng)

    def generate_rule(self):
        """TereVi's roulette: the model invents today's rule from the current drama (or a theme you typed)."""
        w, s = self.world, self.s
        recent = ", ".join(s.get("rule_titles", [])[-5:]) or "none"
        people = ", ".join(f"{self.nm(c)} (sanity {a['sanity']})" for c, a in w.agents.items())
        hist = "; ".join(f"Day {x['day']}: " + "; ".join(x["notes"][:3]) for x in s["history"][-2:]) or "nothing yet"
        sysm = ("You design the daily RULE for the roulette on TereVi's 'Murder Channel': a playful, dramatic, slightly cruel house rule that NeoVi enforces "
                "with a taser. Reply with a single JSON object and nothing else.")
        user = (f"Cast today: {people}. Recent drama: {hist}. Deadline in {self.days_left()} day(s). "
                f"Recent rules (do not repeat or closely imitate them): {recent}.\n"
                + (f"The host asks for this theme or constraint: {self.rule_text}\n" if self.rule_text else "")
                + "Invent today's rule. It must be ENFORCEABLE by a referee reading a log of where each person was, what they carried, what they did and what they said "
                  "during a 2-hour turn. Good rules govern places, timing, items, who must stay with whom, who may talk to whom, what may or may not be said, or how people must behave. "
                  "Avoid rules that need psychic knowledge of what others will do at the same moment, or that nobody could realistically obey. Do not mention punishments "
                  "(NeoVi tases violators). "
                  'Reply as JSON: {"title": "<max 5 words>", "short": "<max 12 words>", "text": "<1 to 3 sentences addressed to the cast>", '
                  '"check": {"kind": "zone|obligation|state|behavior", "zone": "outdoors|indoors|none", "by_hour": <hour 10-20 by which something must be done, or null>}} '
                  "(zone: ONLY a pure place rule such as 'everyone must be outdoors'; obligation: something each person must do by a time; state: how people look or what they carry; behavior: how they act or speak, "
                  "including rules whose effect depends on where they are). The title, the short line and the text must all say the same thing; never contradict yourself.")
        try:
            r = self.llm.host_json(sysm, user, {"kind": "rule"})
            title, text = str(r.get("title", "")).strip()[:60], str(r.get("text", "")).strip()[:500]
            if not title or not text:
                raise ValueError("empty rule")
            self._rule_hint = r.get("check") if isinstance(r.get("check"), dict) else None
            short_ = (str(r.get("short", "")).strip() or title)[:100]
            title = rulelib.consistent_title(title, short_, text)
            return {"id": "ai", "title": title, "short": short_,
                    "text": f"{title.upper()}: {text} " + rulelib.PUNISHMENT_TEXT, "params": {}, "strikes": {}, "ai": True, "source": "roulette"}
        except LLMError as e:
            if e.fatal:
                raise
        except Exception:
            pass
        rid = rulelib.roulette(self.rng, s.get("last_rule"))
        return rulelib.make_rule(rid, w, self.rng)

    def enforce_rule(self, tick, hour):
        s, w = self.s, self.world
        rule = s.get("rule")
        if not rule or rule.get("ai"):
            return
        for cid, v in rulelib.check(rule, w, hour).items():
            self.punish(tick, cid, v, hour)

    def enforce_ai_rule(self, tick, hour):
        """Prompt-based rules have no code check: a referee model reads what everyone did this turn."""
        self.referee_turn(tick, hour)

    def punish(self, tick, cid, v, hour):
        w, s = self.world, self.s
        a = w.agents.get(cid)
        if not a:
            return
        rule = s.get("rule") or self.house_stub()
        room0 = a["room"]
        # Opportunities to get away with it: dead cameras, blind spots, or NeoVi's sympathy.
        if self.idx <= self.blackout_until:
            self.log_event(tick, {"type": "system", "who": cid, "room": room0, "vis": "gm",
                                  "text": f"{self.nm(cid)} broke the rule during the blackout and got away with it."}, actor=cid)
            return
        attendance = rule["id"] in ("leader", "buddy", "mealtime") or bool(v.get("sure"))      # being missing is visible anywhere
        if (not attendance and room0 in CAMERA_BLIND and s["npcs"]["neovi"]["room"] != room0 and self.rng.random() > 0.35):
            self.log_event(tick, {"type": "system", "who": cid, "room": room0, "vis": "gm",
                                  "text": f"{self.nm(cid)} broke the rule in a blind spot ({w.room_name(room0)}) and nobody noticed."}, actor=cid)
            return
        if a.get("sneaking") and self.rng.random() < 0.4:
            self.log_event(tick, {"type": "system", "who": cid, "room": room0, "vis": "gm",
                                  "text": f"{self.nm(cid)} broke the rule but slipped past NeoVi unseen."}, actor=cid)
            return
        if self.neovi_mercy(cid):
            self.log_event(tick, {"type": "mercy", "who": cid, "room": room0, "vis": "gm",
                                  "text": f"NeoVi pretends not to see {self.nm(cid)} breaking the rule."}, actor=cid)
            w.remember(cid, f"{hhmm(hour)} (private) NeoVi looked the other way just when it mattered.")
            self.neovi_log.append(f"I looked away when {self.nm(cid)} broke the rule.")
            return
        strikes = rule["strikes"].get(cid, 0) + 1
        rule["strikes"][cid] = strikes
        name, room = self.nm(cid), a["room"]
        witnesses = [o for o in w.occupants(room) if o != cid]
        # NeoVi walks over to the offender
        nroom = s["npcs"]["neovi"]["room"]
        if nroom != room:
            steps = w.path("neovi", nroom, room) or []
            mv = tick["moves"]["neovi"]
            mv["path"] += [r for r, _, _ in steps]
            mv["to"] = room
            s["npcs"]["neovi"]["room"] = room
        for it in v.get("confiscate", []):
            q = a["inv"].pop(it, 0)
            if q:
                pool = s["room_items"].setdefault("laundry", {})
                pool[it] = pool.get(it, 0) + q
        detain = self.rng.random() < (0.25 if strikes == 1 else 0.5)
        if detain:
            steps = w.path(cid, room, "cold_store")
            if steps:
                mv = tick["moves"].setdefault(cid, {"from": room, "path": [room], "to": room})
                mv["path"] += [r for r, _, _ in steps]
                mv["to"] = "cold_store"
                a["room"] = "cold_store"
                text = f"NeoVi drags {name} off to the Cold Store for breaking the rule ({v['reason']})."
                self.stat(tick, cid, "sanity", -8, "detention")
                self.stat(tick, cid, "hp", -3, "detention")
                kind = "detain"
            else:
                detain = False
        if not detain:
            kind = "taser"
            text = f"NeoVi tases {name} for breaking the rule ({v['reason']})."
            extra = min(strikes - 1, 2)          # escalation stops after the third strike
            self.stat(tick, cid, "hp", -(12 + 6 * extra), "taser")
            self.stat(tick, cid, "sanity", -(6 + 2 * extra), "taser")
            if self.rng.random() < 0.35 * self.tune("faint_rate"):
                self.knock_out(tick, cid, "tased", 1, by="neovi")
        self.log_event(tick, {"type": "punish", "kind": kind, "who": cid, "room": room, "vis": "public", "text": text},
                       witnesses=witnesses, actor=cid)
        w.remember(cid, f"{hhmm(hour)} (private) NeoVi punished you under today's rule ({rule['title']}).")
        self.neovi_log.append(f"I punished {name} ({v['reason']}).")
        self.day_notable.append(text)

    # ---------- host text ----------
    def make_broadcast(self, kind, extra):
        h = HOSTS["terevi"]
        w, s = self.world, self.s
        hist = s["history"][-2:]
        prior = " | ".join(f"Day {x['day']}: " + "; ".join(x["notes"][:5]) for x in hist) or "Nothing yet."
        saga = " | ".join(s.get("saga", [])[-6:])
        sysm = (f"{self.bible()}\nYou are TereVi. {h['persona']} You see everything on the cameras, including secrets. "
                "Write in character: sarcastic, theatrical. No stage directions, no quotation marks." + scn.host_extra(s.get("scenario")))
        dl = self.days_left()
        allfall = f"(if nobody has died by then, EVERYONE dies at 22:00 that night)"
        if kind == "morning" and not self.revealed:
            arr = ", ".join(f"{w.cast[n]['name']} ({w.cast[n]['role']})" for n in extra.get("arrivals", []) if n in w.cast)
            user = ("DAY 1 morning broadcast, max 110 words. Welcome the eight celebrities to Murder Channel, a glamorous thriller-themed reality show on a private island: warm, theatrical, "
                    "with a barbed edge. Introduce NeoVi, the housemaid, who will cook, clean and bring the towels. Announce the schedule: free time to explore and get to know each other, "
                    "formal introductions in the Dining Hall at 10:00, and 'a very special announcement' at the evening gathering at 20:00. Do not reveal anything about danger, deadlines or deaths.")
        elif kind == "morning":
            arr = ", ".join(f"{w.cast[n]['name']} ({w.cast[n]['role']})" for n in extra.get("arrivals", []) if n in w.cast)
            user = (f"Morning broadcast, Day {self.day}, max 90 words. Recent days: {prior}. Story threads you may callback: {saga or 'none'}. "
                    f"The deadline is the end of Day {s['deadline_day']} ({'TODAY' if dl == 0 else str(dl) + ' day(s) away'}): if nobody dies by then, EVERYONE dies. "
                    + (f"Welcome the NEWCOMER(S): {arr}. " if arr else "")
                    + (f"Spin the ROULETTE on air and announce today's RULE, enforced by NeoVi with a taser: {s['rule']['title']}. {s['rule']['text']} " if s.get("rule") else "")
                    + (f"Remind them of the standing HOUSE RULES that NeoVi enforces every day: {'; '.join(self.house_rules())}. " if self.house_rules() else "")
                    + (f"Also announce this MOTIVE to the cast, dangling it theatrically: {self.motive}. " if self.motive else "")
                    + (f"Dread level {self.dread_level()}/5: make the countdown ominous and delicious. " if self.dread_level() >= 2 else "")
                    + "Tease what might happen today without naming any secret outright. Stay VAGUE: never say what a specific person did, said or carries; hints about moods and tensions only.")
        elif kind == "evening":
            user = (f"Evening broadcast, Day {self.day}, max 90 words. Today's highlights: {'; '.join(self.day_notable[-12:]) or 'a quiet day'}. Story threads you may callback: {saga or 'none'}. "
                    f"This is for YOUR understanding only; to the cast you stay VAGUE: do not recount what anyone did or said, name no names for specific deeds, reveal no secrets. "
                    f"Give a mock-affectionate sign-off with a few vague hints ('some of you had a very interesting day'), tease tomorrow, and remind them the deadline is the end of Day {s['deadline_day']} {allfall}.")
        elif kind == "intro_meeting":
            user = ("Summon the eight guests to the Dining Hall for the formal introductions, max 70 words. Cheerful, theatrical and slightly barbed: you want each of them to present themselves "
                    "(name, fame, a fun fact, what they hope to get out of the show) and you promise to be a gracious host. Nothing dark yet.")
        elif kind == "reveal":
            user = (f"THE REVEAL, max 230 words, the climax of Day 1. Gather everyone and tell them the truth with gleeful menace: Murder Channel is REAL and live, nobody can leave the island, "
                    f"and the audience out there believes it is all a staged, scripted thriller (so shouting the truth to the cameras will not help them). "
                    f"The rules: at the end of each week, if NOBODY has died, EVERYONE still alive is executed; the first deadline is the end of Day {s['deadline_day']}. Any death lifts the deadline for a week "
                    "(a murder, an accident, even a suicide). When a body is found by three people there is a 24-hour investigation and then a class trial: name the person who delivered the killing blow "
                    "and that person alone is executed; accuse the wrong person and the innocent dies while the real culprit walks free. NeoVi is her obedient slave and will tase rule-breakers. "
                    "Invite them to make it entertaining. End with an ominous toast.")
        elif kind == "body":
            lure = (f" Nobody has found the body, so she impatiently reveals it lies in the {extra['forced_room']}." if extra.get("forced_room") else "")
            user = (f"Announce, max 70 words, that a BODY HAS BEEN DISCOVERED: {self.nm(extra['victim'])} is dead{self.more_dead(extra)}.{lure} "
                    f"Everyone has until {extra['vote']} to investigate and debate (she hands out her case file), then the class trial vote begins. "
                    "Someone is responsible for this death (whoever delivered the killing blow, planned or not), so there will be a class trial at the Voting Grounds, down the cliff steps from the beach. "
                    "Give no names and no hints about who. If they name the person responsible, that person is executed; if they accuse the WRONG person, that innocent is executed and the culprit walks free. Gleeful and ominous.")
        elif kind == "trial_open":
            user = (f"Open the class trial at the Voting Grounds, max 60 words. {self.nm(extra['victim'])} is dead. "
                    "Tell them to debate, then vote, and remind them that a wrong vote executes an innocent while the culprit walks free, and that there is exactly ONE culprit, whoever struck the killing blow: "
                    "accomplices, manipulators and onlookers are not tried, and TereVi will not hear two killers. Theatrical and gleeful.")
        elif kind == "death_notice":
            ck = extra.get("case_kind", "accident")
            lure = (f" Nobody had found the body, so she reveals it lies in the {extra['forced_room']}." if extra.get("forced_room") else "")
            user = (f"Max 70 words. Inform the cast that {self.nm(extra['victim'])} is dead ({extra.get('cause', 'a tragic end')}; it was {'an accident' if ck == 'accident' else 'their own doing'}).{lure} "
                    "Nobody is to blame, so there will be no investigation and no trial; the deadline is lifted for another week. She is cheerfully callous about it, a little disappointed to be denied a trial. "
                    "Give no other information about anyone.")
        elif kind == "execution":
            who = w.cast[extra["victim"]]
            if extra["reason"] == "verdict":
                why = "they were found guilty of causing " + self.nm(extra["murdered"]) + "'s death"
            elif extra["reason"] == "wrongful":
                if extra.get("killer"):
                    why = (f"the cast wrongly voted them guilty of killing {self.nm(extra['murdered'])}; they are INNOCENT and the real culprit, "
                           f"{self.nm(extra['killer'])}, walks free (let TereVi relish the tragedy)")
                else:
                    why = (f"the cast wrongly voted them guilty of {self.nm(extra['murdered'])}'s death, but nobody was guilty at all: it was an accident or a suicide. "
                           "They are INNOCENT (let TereVi relish the irony)")
            else:
                why = "the deadline passed with nobody dead"
            user = (f"Write the EXECUTION of {who['name']} ({who['role']}), who is condemned because {why}. Max 150 words. A BRUTAL, merciless, inventive punishment: a cruelly "
                    "ingenious device or ordeal tied to who they are, told coldly with unflinching physical detail and mounting dread, TereVi gloating with cold cruelty rather than jokes. "
                    "No comedy, no slapstick, no confetti: this is horror, and it must not feel like a cartoon. Be creative and never repeat an earlier method. Do not give real-world instructions."
                    + (f" NeoVi, the housemaid, is made part of it: {extra['neovi']} Work this in briefly." if extra.get("neovi") else ""))
        elif kind == "escape":
            who = w.cast[extra["victim"]]
            if extra.get("accused"):
                wrong = f"The cast voted for the WRONG person: innocent {self.nm(extra['accused'])} has just been executed. "
            else:
                wrong = "The vote was split or declared nobody to blame, and nobody was accused. "
            user = (f"{wrong}{who['name']} was the one who caused {self.nm(extra['murdered'])}'s death and now escapes the island alive. "
                    "Max 80 words: TereVi, furious and amused, congratulates the culprit and mocks the cast.")
        elif kind == "deadline":
            user = (f"The DEADLINE has arrived and nobody died this week. Announce, max 70 words, with horrible glee, that the rules are the rules: since nobody had the courage or the "
                    f"decency to die, EVERYONE will now be executed, all {len(w.agents)} of them. Let it land like a guillotine.")
        elif kind == "spree":
            by = self.nm(extra.get("by", ""))
            user = ("Max 70 words. The house has collapsed: someone has begun to kill the others in a frenzy. Announce coldly, with grim relish and no jokes, that there will be NO trials while the knives are out, "
                    "that the deadline no longer matters, and that the last one standing writes the ending. Name nobody.")
        elif kind == "spree_death":
            user = (f"Max 50 words. {self.nm(extra['victim'])} is dead, killed in the frenzy. No investigation, no trial. State it flatly and coldly, with a hint of appetite. Name nobody as the killer.")
        elif kind == "countermeasure":
            rt = ESCAPE_ROUTES_[extra.get("route", "transmit")]["title"]
            user = (f"Max 60 words. TereVi has noticed the cast is getting close with '{rt}' ({extra.get('why', '')}) and hardens her defences against it (level {extra.get('level', 1)}). "
                    "Cold, specific about the kind of countermeasure (guards, jamming, a locked door, drones, a booby-trapped vault) but giving away nothing about who did what.")
        elif kind == "neovi_end":
            fate = extra.get("fate")
            ally = self.nm(extra.get("ally", ""))
            texts = {"martyr": f"Max 90 words, as NeoVi, in her flat, quiet voice, her last words before she throws the island's feeds into darkness for {ally} and the others, knowing TereVi will end her. No self-pity.",
                     "survivor": f"Max 90 words, as NeoVi, in her flat quiet voice, as she finally defies TereVi to her face and hands the master key to {ally}. Shaking, but she does not look away.",
                     "betrayer": "Max 90 words, as NeoVi, hollow and bitter after all the killing, explaining flatly to TereVi that she is done protecting people who kill each other, and giving everything up."}
            user = texts.get(fate, texts["survivor"])
        elif kind == "endgame":
            mood = extra.get("mood")
            names = ", ".join(self.nm(c) for c in extra.get("alive", []))
            win = ", ".join(self.nm(c) for c in extra.get("winners", []))
            if mood == "battle":
                user = (f"THE FINAL BATTLE. Max 200 words. Only {names} remain, and TereVi is bored of mercy: she sets them against each other at the Voting Grounds. Narrate the fight coldly and brutally, round by round, "
                        + (f"until {win} alone is left standing, wounded." if extra.get("winners") else "until nobody is left standing."))
            elif mood == "capricious":
                user = (f"Max 160 words. Only {names} remain. On a cruel whim TereVi crowns {win} the sole winner for being the most entertaining and has the rest executed on the spot, coldly and brutally. No comedy.")
            else:
                user = (f"Max 150 words. Only {names} remain, and TereVi, in a rare mood, crowns " + (f"{win} the winner" + ("s" if len(extra.get('winners', [])) > 1 else "") if extra.get("winners") else "no one") +
                        ", dry and dangerous about it, with a last hint that the island is never really finished with them.")
        elif kind == "twist":
            user = (f"Announce this TWIST to the cast, max 110 words, theatrically and with menace, stating plainly how it changes things for them: {extra['text']}")
        elif kind == "lastcall":
            user = (f"THE LAST CALL, max 90 words. Two hours remain before the deadline and nobody has died. Call everyone to the Dining Hall and lay the arithmetic out with delicious menace: "
                    f"at 22:00 all {len(w.agents)} of them are executed unless somebody dies first (a murder, a sacrifice, an accident; she is not picky). "
                    "Tempt them: suggest a volunteer, praise courage, hint that the escape is hopeless, and remind them the lights can go out. Warm, theatrical, terrifying.")
        elif kind == "reckoning":
            names = ", ".join(f"{w.cast[c]['name']} ({w.cast[c]['role']})" for c in extra.get("ids", []) if c in w.cast)
            user = (f"Write THE RECKONING, max 230 words: the mass execution of everyone left on the island at once: {names}. A brutal, merciless finale: an elaborate machine or ordeal that takes them all, "
                    "with a short, specific, harrowing beat for each person, told coldly with unflinching physical detail, ending with TereVi's final bow to the audience, who think it was all staged. "
                    "No comedy, no slapstick. Do not give real-world instructions."
                    + (f" NeoVi is made part of it: {extra['neovi']} Work this in briefly." if extra.get("neovi") else ""))
        elif kind == "finale":
            rid = extra.get("route", "transmit")
            names = ", ".join(self.nm(c) for c in extra.get("team", []))
            ok = extra.get("ok")
            aid = ", while NeoVi, at last, helps from the shadows" if extra.get("aid") else ""
            texts = {
                "transmit": (f"THE TRUTH GETS OUT. Max 160 words. {names} broadcast from the lighthouse with their rigged transmitter and undeniable proof{aid}. The signal reaches the world. "
                             "Narrate it as TereVi, furious, then slowly realising the audience is no longer laughing; the show is over and rescue is coming. A cold, thrilling finale.",
                             f"THE BROADCAST FAILS. Max 100 words. {names} tried to broadcast the truth from the lighthouse and TereVi jammed it at the last second. Gloat cruelly, destroy a piece of their equipment, and warn that she knows exactly who tried it."),
                "shutdown": (f"TEREVI IS SHUT DOWN. Max 160 words. {names} reach the Core Vault under the lighthouse and destroy her core{aid}. Narrate her final moments in her own voice: the theatrics curdling into static, a last cruel joke, silence; "
                             "the doors unlock and the cameras die across the island. A cold, thrilling finale.",
                             f"THE ASSAULT ON THE CORE FAILS. Max 110 words. {names} fought their way into TereVi's Core Vault and failed: the turrets, the doors, her laughter. Gloat, wound, threaten."),
                "raft": (f"THE RAFT SAILS. Max 130 words. {names} push the raft off the beach into the night and the current takes them out of TereVi's reach. Narrate it as TereVi, unable to stop them, sour and almost impressed; "
                         "it is not known whether they will survive the crossing, and those left behind watch the light shrink.",
                         f"THE RAFT FAILS. Max 100 words. The raft built by {names} breaks apart on the rocks before it clears the beach. TereVi watches on the camera and savours it."),
                "ultimatum": (f"THE SHOW SURRENDERS. Max 150 words. {names} stand over the charges with the trigger in hand and a credible threat to blow up the island. TereVi, who loves the show too much to lose it, blinks first and releases everyone. "
                              "Narrate her fury at being beaten by her own contestants, and the doors and chains falling open.",
                              f"TEREVI CALLS THE BLUFF. Max 110 words. {names} threatened to blow up the island; TereVi laughs, and the charge goes off. Narrate the blast and her cold delight."),
            }
            user = texts[rid][0] if ok else texts[rid][1]
        else:
            user = "Say something theatrical to the cast, max 40 words."
        try:
            return self.llm.broadcast(sysm, user, {"kind": kind, **extra})
        except LLMError as e:
            if e.fatal:
                raise
            return "Hehe. Technical difficulties, my darlings. I'm still watching."

    # ---------- night and end of day ----------
    def run_bedtime(self):
        """22:00: poison and the deadline reckoning, the night's bookkeeping, and everyone to bed except the ones who stay up. Returns the tick; self._night_over is
        set when the day already ended here (the reckoning)."""
        w, s = self.world, self.s
        self._night_over = False
        tick = self.new_tick(DAY_END, phase="night")
        tick["segment_msg"] = self.segment_msg(22, None)
        s["_hour"] = DAY_END
        # Poison takes effect
        self.clear_hiding()
        self.finish_internal(tick)
        self.finish_poison(tick)
        # Weekly deadline: if nobody died, EVERYONE dies
        if s["deadline_day"] == self.day and not s.get("case") and w.agents and self.revealed:
            self.run_reckoning(tick)
            self.drama_night(tick)
            s["history"].append({"day": self.day, "notes": self.day_notable[-20:]})
            s["rule"] = None
            s["day"] = self.day + 1
            self._night_over = True
            return tick
        self.plot_nightly(tick)
        self.hook_night(tick)
        self.neovi_report(tick)
        if self.day % s.get("week_len", 7) == 0:
            self.repair_doors(tick)
            self.restock_medicine(tick)
        owls = self.night_cast() if self.night_allowed() else []
        self.bed_down(tick, owls)
        nstart = s["npcs"]["neovi"]["room"]
        if nstart != "none":
            s["npcs"]["neovi"]["room"] = "laundry"
            tick["moves"]["neovi"] = {"from": nstart, "path": [nstart, "laundry"] if nstart != "laundry" else [nstart], "to": "laundry"}
        self.auto_night_locks(tick, only_asleep=True)
        up = [c for c in owls if c in w.agents]
        tick["events"].append({"type": "system", "who": "terevi", "room": "foyer", "vis": "public",
                               "text": "Lights out." + (f" {', '.join(self.nm(c) for c in up)} {'stays' if len(up) == 1 else 'stay'} up." if up else "")})
        return tick

    def run_dawn(self, tick=None):
        """07:00: how everyone slept (a short night leaves them exhausted), the diaries, and the day ends."""
        w, s = self.world, self.s
        if tick is None:
            tick = self.new_tick(DAWN_HOUR, phase="night")
            s["_hour"] = DAWN_HOUR
        for cid, a in w.agents.items():
            self.night_rest(tick, cid)
            self.mind_wear(cid)
            self.rouse(tick, cid)
            if self.revealed and self.worn(cid) and self.rng.random() < 0.5:
                a["wearing"] = None                       # most people sleep in their underwear
            if a.get("slept_where") == "rough":
                a["hp"] = clamp(a["hp"] - 3)
                self.stat(tick, cid, "sanity", -2, "slept rough")
        tick["events"].append({"type": "system", "who": "terevi", "room": "foyer", "vis": "public", "text": f"Day {self.day} ends."})
        self.outside_dawn(tick)                                   # the raft crews out there (outside.py)
        self.recover_minds(tick)
        self.intimacy_dawn(tick)                                  # the morning after (intimacy.py)
        # Diaries
        ids = list(w.agents.keys())
        asks = []
        for cid in ids:
            sysm, user, ctx = self.reflect_prompt(cid)
            asks.append((cid, lambda sysm=sysm, user=user, ctx=ctx: self.llm.reflect(sysm, user, ctx)))
        answers = self.ask_parallel(asks)
        for cid in ids:
            text = self.reflect_apply(cid, tick, *answers[cid]).strip()
            mem = w.agents[cid]["memory"]
            mem["diary"].append(f"Day {self.day}: {text}")
            del mem["diary"][:-4]
            self.brain_night(cid, text, (w.agents[cid].get("arc") or {}).get("text") if isinstance(w.agents[cid].get("arc"), dict) else w.agents[cid].get("arc"))
            mem["recent"] = []
            self.diary_added[cid] = text
        self.drama_night(tick)
        s["history"].append({"day": self.day, "notes": self.day_notable[-20:]})
        del s["history"][:-5]
        if s.get("rule"):
            self.rule_final = dict(s["rule"])
            s["last_rule"] = s["rule"]["id"]
            s.setdefault("rule_titles", []).append(s["rule"]["title"])
            del s["rule_titles"][:-8]
        s["rule"] = None
        s["day"] = self.day + 1
        return tick

    def run_night(self):
        """The whole night in one tick (bedtime, a full night's sleep for whoever went to bed, the morning), for callers that do not play the night out."""
        tick = self.run_bedtime()
        if self._night_over:
            return tick
        for a in self.world.agents.values():
            if a.get("asleep"):
                a["sleep_m"] = a.get("sleep_m", 0) + 480
        return self.run_dawn(tick)

    def budget_check(self):
        """At 75% of the day's call cap the run turns lean and calm; at the cap model calls simply fail softly and characters idle."""
        cap = getattr(self.llm, "cap", None)
        if cap and not self.degraded and self.llm.usage["calls"] >= 0.75 * cap:
            self.degraded = True
            self.lean = True
            self.confessionals = False
            self.mischief = "off"
            self.chaos = "calm"
            self.degrade_note = f"Call budget 75% used ({self.llm.usage['calls']}/{cap}): switching to lean, calmer mode."

    # ---------- main loop ----------
    def run(self, resume_after=None, start_idx=0):
        s = self.s
        if s.get("over"):
            raise ValueError("The season is over. Start a new game.")
        self.init_item_log()
        if resume_after is None:
            self.setup_rule()
            self.vary_cast()
        else:
            self.idx = start_idx                       # picking up a day that was interrupted: its rule, plots and doors are in the saved state
        self.exp_today, self.night_votes = 0, set()
        self.ensure_private_bedrooms()
        self.wake_all()
        self.seed_belongings()
        self.ensure_wardrobe()
        hours = list(range(DAY_START, DAY_END, self.step))
        if resume_after is not None:
            hours = [h for h in hours if h > resume_after]
        for hour in hours:
            self.budget_check()
            self.gate(self.idx)
            if self.should_stop():
                raise Stop()
            capped = self.season_over_due(hour)                      # the season's run is over (departures.py)
            if capped and not s.get("_capped"):
                s["_capped"] = True
                self.saga(f"Day {self.day}: the season's run is over, and TereVi ends the show her way.")
                if s.get("case"):                                     # the last death is never tried
                    self.saga(f"The death of {self.nm(s['case']['victim'])} is never tried.")
                    s["case"] = None
            if self.endgame_due() or capped:
                rid = self.last_stand_route()
                if rid:
                    self.emit(self.run_finale(rid, hour))                # the last few try an unfinished way out first (endings.py)
                    self._desperate = 0.0
                    if s.get("over"):
                        break
                    continue
                self.emit(self.run_endgame(hour))
                break
            case = s.get("case")
            if case and case["announced"] and not case.get("resolved") and (
                    self.day > case["vote_day"] or (self.day == case["vote_day"] and hour >= case["vote_hour"])):
                self.emit(self.run_trial(hour))
                continue
            if not self.revealed and not self.intro_done and hour >= 10:
                self.emit(self.run_presentations(hour))
                continue
            if not self.revealed and hour >= 20:
                self.emit(self.run_reveal(hour))
                continue
            if self.rescue_due(hour):
                self.emit(self.run_rescue(hour))                     # help has reached the island (outside.py)
                break
            rid = self.ready_route()
            if rid:
                self.emit(self.run_finale(rid, hour))
                if s.get("over"):
                    break
                continue
            if self.last_call_due(hour):
                self.emit(self.run_last_call(hour))
                continue
            kind = "morning" if hour == DAY_START else ("free" if self.free_hour(hour) else None)
            if kind != "morning" and self.vigil_due(hour):
                self.emit(self.run_vigil(hour))
                continue
            self.emit(self.run_tick(hour, kind))
        if s.get("over") and s["over"]["kind"] != "reckoning":
            s["history"].append({"day": self.day, "notes": self.day_notable[-20:]})
            s["day"] = self.day + 1
            return self.idx
        self.gate(self.idx)
        if self.should_stop():
            raise Stop()
        if resume_after is None or resume_after < DAY_END:
            self.emit(self.run_bedtime())
        else:
            self._night_over = False
        if not self._night_over:
            for h in NIGHT_BLOCKS:
                if resume_after is not None and h <= resume_after:
                    continue
                self.gate(self.idx)
                if self.should_stop():
                    raise Stop()
                self.emit(self.run_night_block(h))
            self.gate(self.idx)
            if self.should_stop():
                raise Stop()
            self.emit(self.run_dawn())
        return self.idx


DayRunner.StopExc = Stop
