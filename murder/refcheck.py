"""Enforcing the daily rule and the house rules.

A rule is classified when it is set up, and each kind is judged in the way that can actually work:
  zone        a place rule ("only outdoors"): checked by the engine from where everyone is, no AI call
  obligation  "do X before 20:00": the referee notes who has done it each turn; at the deadline everyone who has not is punished
  state       "wear X", "carry Y": the burden of proof is on the character (the record must show compliance); silence counts against them
  behavior    what people do or say: the referee reads the record, with the last turns' verdicts as memory
RefereeMixin is mixed into DayRunner (engine.py).
"""
import json
import os
import re

from .data_world import ROOMS
from . import rules as rulelib

STATE_WORDS = r"\b(wear|wearing|dressed|undress|underwear|naked|barefoot|blindfold|mask|costume|hat|carry|carrying|holding|hold|wrapped|disguise)\b"
LAST_TURN = 20


def _hh(h):
    return f"{int(h):02d}:00"


SPEECH = r"\b(whisper|whispers|speak|speaking|say|says|talk|talking|shout|shouting|scream|loud|loudly|voice|voices|sing|singing|hum|humming|silent|silence|quiet|mention|words?|swear|compliments?|insult|names?)\b"
CONDITIONAL = r"\b(if you|when you|while you|whenever|as long as|for as long as|unless|carry|carrying|wear|wearing|holding|hold|bring|light)\b"


def zone_of(t):
    """A pure place rule ("only outdoors", "nobody indoors after 18:00"), or None. Anything that mixes places with speech, conditions or objects is NOT a zone rule."""
    B = r"\b"
    out = re.search(B + r"(outdoors|outside|out of doors)" + B, t)
    ins = re.search(B + r"(indoors|inside)" + B, t)
    if bool(out) == bool(ins) or re.search(SPEECH, t) or re.search(CONDITIONAL, t):
        return None
    place = "outdoors" if out else "indoors"
    word = r"(?:outdoors|outside|out of doors)" if out else r"(?:indoors|inside)"
    negated = (re.search(B + r"(not|never|nobody|no one|no-one|none of you|forbidden|banned)" + B + r"[^.;]{0,40}" + B + word + B, t)
               or re.search(B + word + B + r"[^.;]{0,20}" + B + r"(forbidden|banned|off.?limits)" + B, t))
    positive = re.search(B + r"(only|must|have to|stay|remain|spend|keep)" + B + r"[^.;]{0,40}" + B + word + B, t)
    if negated:
        return ("indoors" if place == "outdoors" else "outdoors",)
    if positive:
        return (place,)
    return None


def classify_text(text, hint=None):
    """Work out how a free-text rule can be judged. `hint` is the AI's own classification when it gave one."""
    t = (text or "").lower()
    chk = {"kind": "behavior", "zone": None, "by_hour": None, "until": None, "proof": False}
    hint = hint if isinstance(hint, dict) else {}
    m = re.search(r"\b(?:before|by|no later than)\s+(\d{1,2})(?::\d{2})?\s*(am|pm)?", t)
    by = None
    if m:
        by = int(m.group(1)) + (12 if m.group(2) == "pm" and int(m.group(1)) < 12 else 0)
        if not 8 <= by <= 23:
            by = None
    m2 = re.search(r"\buntil\s+(\d{1,2})(?::\d{2})?\s*(am|pm)?", t)
    if m2:
        u = int(m2.group(1)) + (12 if m2.group(2) == "pm" and int(m2.group(1)) < 12 else 0)
        if 8 <= u <= 23:
            chk["until"] = u
    zone = zone_of(t)
    if zone:
        chk.update(kind="zone", zone=zone[0])
        m3 = re.search(r"after\s+(\d{1,2})(?::\d{2})?\s*(am|pm)?", t)
        if m3:
            f = int(m3.group(1)) + (12 if m3.group(2) == "pm" and int(m3.group(1)) < 12 else 0)
            if 8 <= f <= 23:
                chk["from"] = f
        return chk
    if hint.get("by_hour") not in (None, "", 0):
        try:
            by = int(hint["by_hour"])
        except (TypeError, ValueError):
            pass
    wants = re.search(r"\b(must|have to|has to|need to|needs to|required to|each of you|everyone (?:will|shall))\b", t)
    once = re.search(r"\b(at least once|once today|before (?:the day|tonight|the day is)|sometime today)\b", t)
    if hint.get("kind") == "obligation" or (wants and (by or once)):
        chk.update(kind="obligation", by_hour=min(by or LAST_TURN, 23), proof=True)
        return chk
    if re.search(SPEECH, t):
        return chk                                   # anything about what people say is judged by the referee, whatever else it mentions
    if hint.get("kind") == "state" or re.search(STATE_WORDS, t):
        chk.update(kind="state", proof=True)
        if re.search(r"underwear|undies|naked|nude|stripped|in your pants", t):
            chk["state_check"] = "underwear"
        return chk
    return chk


class RefereeMixin:
    # ------------------------------------------------------------------ set-up
    def rule_describe(self, rule):
        chk = rule.get("chk") or {}
        k = chk.get("kind", "behavior")
        if k == "zone":
            return f"checked by the engine from where everyone is: everybody must be {chk['zone']}, from {_hh(max(10, chk.get('from') or 10))}; anyone who is not is punished"
        if k == "obligation":
            return f"an obligation: the referee notes who has done it, and everyone who has not by {_hh(min(chk['by_hour'], LAST_TURN))} is punished"
        if k == "state" and chk.get("state_check") == "underwear":
            return "checked by the engine from what each person is wearing: anyone in clothes at the end of a turn (from 10:00) is punished"
        if k == "state":
            return "a condition on how people look or what they carry: the referee only counts what each person's record shows, so silence counts against them"
        return "a behaviour rule: the referee reads what people did and said each turn"

    def rule_hint(self, rule):
        chk = (rule or {}).get("chk") or {}
        k = chk.get("kind")
        if k == "zone":
            return f" HOW IT IS CHECKED: your position at the end of every turn from {_hh(max(10, chk.get('from') or 10))} (not before): you must be {chk['zone']} then."
        if k == "obligation":
            return (f" HOW IT IS CHECKED: it has to be DONE by {_hh(min(chk['by_hour'], LAST_TURN))}. The referee notes who has done it from your activity, "
                    "so do it and say plainly in your activity that you did. Everyone who has not is punished at the deadline.")
        if k == "state" and chk.get("state_check") == "underwear":
            return " HOW IT IS CHECKED: what you are wearing at the end of every turn from 10:00. Take your clothes off (\"wear\": \"none\") to obey."
        if k == "state":
            return " HOW IT IS CHECKED: the referee only counts what it is told you do. Say how you comply in your activity (what you wear or hold). Silence counts as breaking it."
        return " HOW IT IS CHECKED: the referee reads your activity and your words each turn."

    def classify_today(self, hint=None):
        rule = self.s.get("rule")
        if not rule or not rule.get("ai"):
            return
        rule["chk"] = classify_text(rule.get("text", "") + " " + rule.get("short", ""), hint)
        rule["done"], rule["log"], rule["last_pun"] = [], [], {}
        self.second_opinion(rule)
        self.log_rule_seen(rule)

    def second_opinion(self, rule):
        """A rule the engine will enforce by itself (a place or a deadline) gets a second, independent reading first. If the two disagree it is left to the referee."""
        chk = rule["chk"]
        rule["reading"] = None
        if chk["kind"] not in ("zone", "obligation"):
            return
        sysm = "You read a house rule from a reality show and say how a referee should enforce it. Reply with a single JSON object and nothing else."
        user = (f"RULE: {rule['text']}\nPick ONE kind: 'zone' (everyone simply has to be indoors or outdoors and nothing else is asked), 'obligation' (each person must do something by a time), "
                "'state' (how people look or what they carry), 'behavior' (how they act or speak; anything conditional, anything about speech, anything that depends on where they are but is not just a place to be). "
                'Reply as JSON: {"kind": "zone|obligation|state|behavior", "zone": "outdoors|indoors|none", "by_hour": null or an hour, "reading": "<one plain sentence: exactly what is required or forbidden>"}')
        try:
            r = self.llm.host_json(sysm, user, {"kind": "ruleclass", "guess": {"kind": chk["kind"], "zone": chk.get("zone")}})
        except Exception as e:
            if getattr(e, "fatal", False):
                raise
            chk["confirmed"] = False
            return
        rule["reading"] = str(r.get("reading") or "")[:200] or None
        agree = r.get("kind") == chk["kind"] and (chk["kind"] != "zone" or r.get("zone") == chk.get("zone"))
        if agree:
            chk["confirmed"] = True
            return
        rule["chk"] = {"kind": "behavior", "zone": None, "by_hour": None, "until": None, "proof": False, "disagreed": True, "was": chk["kind"]}

    def log_rule_seen(self, rule):
        """Every rule that is set up is appended to a file, so the classifier can be tested on real ones."""
        try:
            base = os.environ.get("MC_DATA_DIR") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            os.makedirs(os.path.join(base, "state"), exist_ok=True)
            with open(os.path.join(base, "state", "rules_seen.jsonl"), "a", encoding="utf-8") as f:
                f.write(json.dumps({"day": self.day, "title": rule.get("title"), "short": rule.get("short"), "text": rule.get("text", "")[:600],
                                    "kind": rule["chk"]["kind"], "zone": rule["chk"].get("zone"), "disagreed": bool(rule["chk"].get("disagreed")),
                                    "reading": rule.get("reading")}, ensure_ascii=False) + "\n")
        except OSError:
            pass

    def rule_notice(self, tick):
        """Tell the viewer how today's rule will be judged, or why there is no rule."""
        rule = self.s.get("rule")
        if rule:
            if rule.get("ai"):
                chk = rule.get("chk") or {}
                extra = (f" Plain reading: {rule['reading']}" if rule.get("reading") else "") \
                    + (" A second reading disagreed with the first, so the referee judges it instead of the engine." if chk.get("disagreed") else "") \
                    + (" (Volume and tone are judged from the dialogue.)" if re.search(SPEECH, rule.get("text", "").lower()) else "")
                self.log_event(tick, {"type": "system", "who": "terevi", "room": "foyer", "vis": "viewer",
                                      "text": f"RULE CHECK: \"{rule['title']}\" is {self.rule_describe(rule)}.{extra}"})
            return
        why = getattr(self, "rule_none_reason", "") or "no rule was set"
        if self.revealed:
            self.log_event(tick, {"type": "system", "who": "terevi", "room": "foyer", "vis": "viewer", "text": f"NO RULE TODAY: {why}."})

    # ------------------------------------------------------------------ the checks
    def zone_ok(self, chk, room):
        outdoors = ROOMS[room][1] == "grounds"
        return outdoors if chk["zone"] == "outdoors" else not outdoors

    def recently_punished(self, rule, cid):
        lp = rule.setdefault("last_pun", {}).get(cid)
        return lp is not None and self.idx - lp <= 1

    def referee_punish(self, tick, rule, cid, reason, hour, sure=False):
        if rule is not None and self.recently_punished(rule, cid):
            return
        if rule is not None:
            rule.setdefault("last_pun", {})[cid] = self.idx
            rule.setdefault("log", []).append(f"{_hh(hour)} {self.nm(cid)} punished: {reason[:70]}")
            del rule["log"][:-5]
        self.punish(tick, cid, {"reason": str(reason)[:120], "confiscate": [], "sure": sure}, hour)

    def referee_turn(self, tick, hour):
        w, s = self.world, self.s
        rule = s.get("rule") if (s.get("rule") or {}).get("ai") else None
        house = self.house_rules()
        if not w.agents or (not rule and not house):
            return
        chk = (rule or {}).get("chk") or {"kind": "behavior"}
        first = hour < 8 + self.step                                       # the announcement turn: nobody can have obeyed yet
        kind = chk.get("kind", "behavior")
        until = chk.get("until") or 24
        if rule and kind == "zone" and not first and chk.get("from", 0) <= hour <= min(until, LAST_TURN):
            for cid, a in list(w.agents.items()):
                if a["room"] in ("cold_store", "voting_grounds") or self.zone_ok(chk, a["room"]):
                    continue
                self.referee_punish(tick, rule, cid, f"was {w.room_name(a['room'])}, not {chk['zone']}", hour)
        if rule and kind == "state" and chk.get("state_check") == "underwear" and not first:
            for cid in list(w.agents):
                if self.worn(cid) is not None:
                    self.referee_punish(tick, rule, cid, f"was wearing {self.outfit_label(cid)} instead of being in their underwear", hour)
            if not house:
                return
        judge_rule = rule is not None and kind != "zone" and not (kind == "state" and chk.get("state_check"))
        if not judge_rule and not house:
            return
        if first and not house:
            for cid, a in w.agents.items():
                self.rule_prev[cid] = a["activity"]
            return
        said = {}
        for g in tick["talk"]:
            for l in g["lines"]:
                said.setdefault(l["speaker"], []).append(l["text"])
        rows = []
        for cid, a in w.agents.items():
            items = ", ".join(w.item_name(k) for k in a["inv"]) or "nothing"
            talk = " / ".join(said.get(cid, [])) or "(said nothing aloud)"
            prev = self.rule_prev.get(cid)
            rows.append(f"- {cid} ({self.nm(cid)}): in the {w.room_name(a['room'])} ({'OUTDOORS' if ROOMS[a['room']][1] == 'grounds' else 'indoors'}); doing: {a['activity']}"
                        + (f" (the turn before: {prev[:70]})" if prev else "") + f"; wearing: {self.wearing_desc(cid)}; carrying: {items}; said: {talk[:300]}")
        texts = ([rule["text"]] if judge_rule else []) + [f"HOUSE RULE (always in force): {h} " + rulelib.PUNISHMENT_TEXT for h in house]
        extra = ""
        sysm = ("You are the impartial referee of a house rule on a reality show. Punish only CLEAR violations supported by the record below. "
                "If the record is ambiguous or silent, do not punish. Reply with a single JSON object and nothing else.")
        if judge_rule and kind == "obligation":
            extra = (f"Rule 1 is an OBLIGATION to be done by {_hh(min(chk['by_hour'], LAST_TURN))}. Do not list violators for it; list in \"fulfilled\" the ids of everyone whose record "
                     f"clearly shows they have done it (this turn or earlier). Already recorded as done: {', '.join(rule.get('done', [])) or 'nobody'}. ")
        elif judge_rule and kind == "state":
            sysm = ("You are the impartial referee of a house rule on a reality show. The rule is a condition on how people look or what they carry, and the burden of proof is on them: "
                    "a person whose record does not show they comply is a violator. Reply with a single JSON object and nothing else.")
            extra = "Rule 1 is a CONDITION: list as violators everyone whose record does not show they comply. "
        if judge_rule and kind == "behavior":
            extra += "If the rule depends on where a person is (indoors or outdoors) use the location given for each person, and judge speech by what they said. "
        log = (" Recent verdicts: " + " | ".join(rule.get("log", [])[-3:]) + ".") if rule and rule.get("log") else ""
        user = ("RULES:\n" + "\n".join(f"{i + 1}. {t}" for i, t in enumerate(texts)) + f"\nTime: Day {self.day}, {hhmm_(hour)} (the end of a {self.step}-hour turn).{log}\n"
                + extra + "WHAT EACH PERSON DID THIS TURN:\n" + "\n".join(rows) + "\n"
                'List the violators as JSON: {"violations": [{"id": "<person id>", "reason": "<max 12 words>"}], "fulfilled": ["<person id>"]}. Use empty lists if there are none.')
        try:
            r = self.llm.judge(sysm, user, {"ids": list(w.agents.keys())})
        except Exception as e:
            if getattr(e, "fatal", False):
                raise
            tick["errors"].append(f"the referee failed: {str(e)[:80]}")
            r = {}
        for cid, a in w.agents.items():
            self.rule_prev[cid] = a["activity"]
        if rule is not None and kind == "obligation":
            for cid in (r.get("fulfilled") or []):
                if cid in w.agents and cid not in rule["done"]:
                    rule["done"].append(cid)
        seen = set()
        for v in (r.get("violations") or [])[:8]:
            cid = v.get("id") if isinstance(v, dict) else None
            if cid in w.agents and cid not in seen and not (kind == "obligation" and judge_rule):
                seen.add(cid)
                self.referee_punish(tick, rule, cid, str(v.get("reason", "broke the rule")), hour)
        if rule is not None and kind == "obligation" and not rule.get("deadline_done") and (hour >= min(chk["by_hour"], LAST_TURN)):
            rule["deadline_done"] = True
            for cid in list(w.agents):
                if cid not in rule["done"]:
                    self.referee_punish(tick, rule, cid, f"had not done it by {_hh(min(chk['by_hour'], LAST_TURN))}", hour, sure=True)


def hhmm_(h):
    return f"{int(h):02d}:00"
