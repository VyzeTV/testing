"""Event-based feelings with analytic decay and an adapter to the existing runner.

Queries never age or refresh a record. Choices, diaries and voice cards read the
same state at the same game time; revisiting a memory cannot make it immortal.
"""
import copy
import math

# Half-life and maximum duration, in game hours.
LIFE = {'grief': (72, 336), 'guilt': (96, 336), 'fear': (48, 240), 'anger': (48, 240),
        'shame': (36, 168), 'relief': (36, 120), 'attraction': (72, 240), 'loneliness': (48, 168)}


def upgrade(state):
    for key, value in (('emotions', {}), ('emotion_sources', {}), ('emotion_seq', 0), ('emotion_company', {}), ('emotion_rooms', {}), ('emotion_adopted', [])):
        state.setdefault(key, value)


def strength(record, now):
    if now < record['started'] or now >= record['expires']:
        return 0.0
    value = record['strength'] * 2 ** (-max(0, now - record['updated']) / LIFE[record['kind']][0])
    return min(10, value * (1.15 if record.get('reminded_until', 0) > now else 1))


def active(state, who, now):
    return sorted((e for e in state.get('emotions', {}).get(who, []) if strength(e, now) >= .5),
                  key=lambda e: (-strength(e, now), e['id']))


def add(state, who, kind, amount, now, cause, source, target=None, room=None, known_by=None):
    """Appraise a new known event once, including after save/load."""
    if kind not in LIFE or not math.isfinite(amount) or amount <= 0 or not cause or not source:
        return None
    upgrade(state)
    key = f'{who}:{kind}:{target}:{source}'
    seen = state['emotion_sources']
    if key in seen:
        for e in state['emotions'].get(who, []):
            if e['kind'] == kind and e.get('target') == target and e.get('source') == source:
                e['known_by'] = sorted(set(e['known_by']) | set(known_by or [who]))
        return None
    seen[key] = now
    if len(seen) > 2048:
        for old in list(seen)[:1024]:
            del seen[old]
    records = state['emotions'].setdefault(who, [])
    records[:] = active(state, who, now)
    record = next((e for e in records if e['kind'] == kind and e.get('target') == target), None)
    if record:
        value = min(10, strength(record, now) + min(10, amount) * .3)
        record.update(strength=value, updated=now, expires=now + LIFE[kind][1], cause=cause[:180],
                      room=room, known_by=sorted(set(known_by or [who])), source=source)
    else:
        state['emotion_seq'] += 1
        record = dict(id=f"e{state['emotion_seq']}", who=who, kind=kind, strength=min(10, amount),
                      started=now, updated=now, expires=now + LIFE[kind][1], cause=cause[:180],
                      source=source, target=target, room=room, known_by=sorted(set(known_by or [who])))
        records.append(record)
    records.sort(key=lambda e: (-strength(e, now), e['id']))
    del records[16:]
    return record


def soothe(state, who, kinds, now, factor=.7):
    for e in active(state, who, now):
        if e['kind'] in kinds and e.get('soothed_day') != int(now // 24):
            e.update(strength=strength(e, now) * factor, updated=now, soothed_day=int(now // 24))


def context(state, who, now, names, group=None):
    out = []
    for e in active(state, who, now):
        if group is not None and not set(group) <= set(e.get('known_by', [])):
            continue
        toward = f" toward/about {names(e['target'])}" if e.get('target') else ''
        reminder = '; brought back by a recent reminder' if e.get('reminded_until', 0) > now else ''
        out.append(f"{e['kind']}{toward} {strength(e, now):.1f}/10: {e['cause']}{reminder}")
        if len(out) == 4:
            break
    return 'LASTING EMOTIONS: ' + ' | '.join(out) if out else ''


class EmotionManager:
    def __init__(self, engine):
        self.e = engine
        upgrade(self.s)
        # Legacy memories describe things this person already knows. Do not infer
        # knowledge of a hidden death or killer from the global graveyard/case.
        for who, a in self.e.world.agents.items():
            self.s['emotion_rooms'].setdefault(who, a['room'])
            if who in self.s['emotion_adopted']:
                continue
            self.s['emotion_adopted'].append(who)
            if self.s['emotions'].get(who):
                continue
            for loss in a.get('memory', {}).get('lost', []):
                if a.get('aff', {}).get(loss.get('id'), 0) >= 3 and 'escaped' not in loss.get('how', '') and 'raft' not in loss.get('how', ''):
                    when = min(self.now(), loss.get('day', self.e.day) * 24 + 12)
                    if when <= self.now() < when + LIFE['grief'][1]:
                        self.put(who, 'grief', 6, f"lost {loss.get('name', loss.get('id'))}", f"loss:{loss.get('id')}",
                                 target=loss.get('id'), at=when)

    @property
    def s(self):
        return self.e.world.state

    def now(self, tick=None):
        return self.e.day * 24 + (tick['hour'] if tick else self.s.get('_hour', 8)) + (self.e.minute() or 0) / 60

    def put(self, who, kind, amount, cause, source, tick=None, target=None, room=None, known_by=None, at=None):
        a = self.e.world.all_agents.get(who) or self.s.get('npcs', {}).get(who)
        if not a or a.get('status', 'alive') != 'alive' or a.get('dead'):
            return None
        return add(self.s, who, kind, amount, self.now(tick) if at is None else at, cause, source, target, room, known_by)

    def level(self, who, kind, target=None):
        return max((strength(e, self.now()) for e in active(self.s, who, self.now())
                    if e['kind'] == kind and (target is None or e.get('target') == target)), default=0)

    def loss(self, tick, victim, room, informed):
        w = self.e.world
        known = sorted(set(informed))
        for who in known:
            if who == victim or who not in w.agents:
                continue
            a = w.agents[who]
            aff = a['aff'].get(victim, 0)
            bonded = any(b['kind'] in ('romance', 'pact') and {b['a'], b['b']} == {who, victim} for b in self.s.get('bonds', []))
            if aff >= 3 or bonded:
                amount = min(10, 4 + max(0, aff) * .5 + (2 if bonded else 0))
                self.put(who, 'grief', amount, f"learned that {self.e.nm(victim)} died", f'loss:{victim}', tick, victim, room, known)
            else:
                self.put(who, 'fear', 3, 'another known death made the house feel unsafe', f'loss:{victim}', tick, room=room, known_by=known)

    def guilt(self, tick, case):
        who = case.get('killer')
        if who not in self.e.world.agents or not case.get('culprit_aware', True):
            return
        a = self.e.world.agents[who]
        values = self.e.mind(who)['values']
        amount = max(1, min(9, 3 + self.e.facet(who, 'altruism') / 25 + values.get('loyalty', 50) / 50 - self.e.facet(who, 'cruelty') / 25))
        if a['drive']['id'] == 'protector':
            amount = min(10, amount + 2)
        self.put(who, 'guilt', amount, f"knows they caused {self.e.nm(case['victim'])}'s death", f"guilt:{case['victim']}", tick,
                 case['victim'], case.get('room'))

    def event(self, tick, event, witnesses, actor):
        kind, who = event.get('type'), event.get('who')
        if kind not in ('attack', 'assault', 'body', 'embarrassed', 'punish', 'mercy'):
            return
        if kind in ('attack', 'assault') and event.get('vis') != 'public':
            return
        if event.get('emotion_source'):
            return
        self.s['emotion_seq'] += 1
        source = f"event:{self.s['emotion_seq']}"
        event['emotion_source'] = source
        known = sorted(set(witnesses or []) | ({actor} if actor else set()))
        target, room = event.get('target'), event.get('room')
        if kind == 'body' and event.get('victim'):
            self.loss(tick, event['victim'], room, known)
        elif kind in ('attack', 'assault') and target:
            w = self.e.world
            observers = set(witnesses or []) | {target}
            for observer in sorted(observers):
                a = w.agents.get(observer)
                if not a or observer == actor or a.get('asleep') or a.get('out'):
                    continue
                ident = None if self.e.blind(observer) or self.e.in_dark(observer) else self.e.perceived_identity(observer, actor)
                cause = f"witnessed violence by {self.e.nm(ident)}" if ident else 'heard or suffered violence without identifying the attacker'
                self.put(observer, 'fear', 7 if observer == target else 4, cause, source, tick, ident, room,
                         known if ident else [observer])
                if observer == target:
                    self.put(observer, 'anger', 5, cause, source, tick, ident, room, known if ident else [observer])
        elif kind in ('embarrassed', 'punish'):
            self.put(who, 'shame', 4 + self.e.facet(who, 'vanity') / 30, 'was exposed or humiliated in front of others', source, tick,
                     room=room, known_by=known or [who])
        elif kind == 'mercy' and event.get('saved'):
            self.put(event['saved'], 'relief', 7, f"was saved by {self.e.nm(who)}", source, tick, who, room, known)

    def betrayed(self, tick, actor, victim, why, close=False):
        if why in ('attacked', 'murdered', 'tried to kill', 'killed'):
            return  # Observed violence is appraised through checked witnesses instead.
        source = f"betrayal:{actor}:{victim}:{self.e.day}:{tick['hour']}:{why}"
        known = [actor, victim]
        self.put(victim, 'anger', 7 if close else 4, f"{self.e.nm(actor)} {why}", source, tick, actor, known_by=known)
        if 'secret' in why or 'affair' in why:
            self.put(victim, 'shame', 5, f"was hurt by {self.e.nm(actor)} ({why})", source, tick, actor, known_by=known)

    def social(self, tick, a, b, move, outcome):
        now = self.now(tick)
        source = f"social:{a}:{b}:{self.e.day}:{tick['hour']}:{move}"
        known = [a, b]
        if outcome == 'ok' and move in ('chat', 'joke', 'comfort', 'confide', 'thank', 'apologise', 'gift', 'teamwork', 'flirt'):
            soothe(self.s, a, ('loneliness',), now)
            soothe(self.s, b, ('loneliness',), now)
            if move in ('comfort', 'apologise', 'thank', 'gift', 'teamwork'):
                self.put(b, 'relief', 4, f"received {move} from {self.e.nm(a)}", source, tick, a, known_by=known)
                soothe(self.s, b, ('fear', 'grief'), now, .9)
            if move == 'flirt':
                for who, other in ((a, b), (b, a)):
                    self.put(who, 'attraction', 2 + self.e.facet(who, 'romantic') / 30,
                             f"a welcomed flirtation with {self.e.nm(other)}", source, tick, other, known_by=known)
        elif outcome != 'ok' and move == 'flirt' and self.e.facet(a, 'vanity') >= 60:
            self.put(a, 'shame', 4, f"an advance toward {self.e.nm(b)} was declined", source, tick, b, known_by=known)
        if move in ('putdown', 'mock', 'threaten'):
            self.put(b, 'anger', 4, f"{self.e.nm(a)} directed {move} at them", source, tick, a, known_by=known)

    def remind(self, tick, who, room):
        old = self.s['emotion_rooms'].get(who)
        self.s['emotion_rooms'][who] = room
        if old is None or old == room:
            return
        for emotion in active(self.s, who, self.now(tick)):
            target = emotion.get('target')
            near = (target in self.e.world.agents and target in self.e.world.occupants(room)
                    and not self.e.blind(who) and not self.e.in_dark(who))
            if (emotion.get('room') == room or near) and emotion.get('reminded_day') != self.e.day:
                emotion.update(reminded_day=self.e.day, reminded_until=self.now(tick) + 2)
                tick['events'].append({'type': 'emotion', 'who': who, 'room': room, 'vis': 'gm', 'emotion': emotion['id'],
                                       'kind': emotion['kind'], 'm': self.e.minute() or 0,
                                       'text': f"{self.e.nm(who)} is reminded of {emotion['cause']} ({emotion['kind']})."})

    def sync(self, tick):
        now = self.now(tick)
        w = self.e.world
        for who in list(self.s['emotions']):
            self.s['emotions'][who] = active(self.s, who, now)
        for who, a in sorted(w.agents.items()):
            self.remind(tick, who, a['room'])
            others = [o for o in w.occupants(a['room']) if o in w.agents and o != who]
            alone = not others and not a.get('asleep') and not a.get('out')
            company = self.s['emotion_company'].setdefault(who, {'since': now, 'alone': alone})
            if alone != company['alone']:
                company.update(since=now, alone=alone)
            if alone and now - company['since'] >= 12:
                self.put(who, 'loneliness', 3 + self.e.facet(who, 'gregariousness') / 40,
                         'has spent a long waking stretch without company', f'isolation:{self.e.day}', tick)

    def context(self, who, group=None):
        return context(self.s, who, self.now(), self.e.nm, group)

    def view(self, who):
        return [dict(copy.deepcopy(e), intensity=round(strength(e, self.now()), 2)) for e in active(self.s, who, self.now())]

    def signature(self, who):
        """Major new shocks invalidate an early choice; ordinary fading does not."""
        return tuple(sorted((e['id'], e['updated']) for e in active(self.s, who, self.now())
                            if e['kind'] in ('grief', 'guilt', 'fear', 'anger', 'shame') and e['strength'] >= 4))

    def score(self, who, act, room, partner=None):
        adjustment = 0.0
        a = self.e.world.agents[who]
        if a['hp'] < 35 or act in ('rest', 'nap') and a['hp'] < 50:
            return adjustment
        if act in ('rescue', 'fight', 'flee', 'warn', 'eat', 'drink', 'bathroom', 'treat'):
            return adjustment
        for emotion in active(self.s, who, self.now()):
            level = strength(emotion, self.now())
            target = emotion.get('target')
            if emotion['kind'] in ('fear', 'grief'):
                if room == emotion.get('room'):
                    adjustment -= min(1, level * .12)
                if emotion['kind'] == 'fear' and target in self.e.world.agents and room == self.e.world.agents[who]['room'] and target in self.e.world.occupants(room) and not self.e.blind(who) and not self.e.in_dark(who):
                    adjustment -= min(2, level * .25)
            if act in ('chat', 'company', 'talk', 'visit'):
                if emotion['kind'] in ('grief', 'loneliness'):
                    adjustment += min(1.5, level * .2)
                if partner == target and emotion['kind'] in ('anger', 'attraction'):
                    adjustment += min(1.2, level * .18)
            if emotion['kind'] == 'guilt' and act in ('confess', 'cook'):
                adjustment += min(1.2, level * .16)
        return adjustment

    def options(self, tick, who, add_option):
        w = self.e.world
        a = w.agents[who]
        if a['hp'] < 35 or a.get('out') or a.get('asleep'):
            return
        for emotion in active(self.s, who, self.now(tick))[:4]:
            level, kind, target = strength(emotion, self.now(tick)), emotion['kind'], emotion.get('target')
            if kind in ('grief', 'loneliness'):
                from .freetime import PRIVATE_ROOMS
                friends = [p for p in sorted(w.agents) if p != who and w.agents[who]['aff'].get(p, 0) >= 2
                           and not w.agents[p].get('asleep') and not w.agents[p].get('out')
                           and w.agents[p]['room'] != 'bathroom'
                           and (w.agents[p]['room'] not in PRIVATE_ROOMS or w.agents[p]['room'] == w.cast[who]['home'])]
                if friends:
                    friend = max(friends, key=lambda p: (w.agents[who]['aff'].get(p, 0), p))
                    add_option(.5 + level / 6, 'chat', room=w.agents[friend]['room'], partner=friend, why=f"seeking company while feeling {kind}")
            elif kind == 'guilt' and self.e.confessionals:
                add_option(level / 8, 'confess', why='guilt and the need to say something')

    def move_options(self, who, target, options):
        fear = self.level(who, 'fear', target)
        anger = self.level(who, 'anger', target)
        attraction = self.level(who, 'attraction', target)
        result = []
        for weight, move, about in options:
            if move in ('flirt', 'confide'):
                weight *= max(.15, 1 - fear / 10)
            if move == 'flirt':
                weight *= 1 + attraction / 8
            if move in ('confront', 'putdown'):
                weight *= 1 + anger / 8
            result.append((weight, move, about))
        if anger >= 5 and not any(m == 'confront' for _, m, _ in result):
            result.append((min(1.2, anger / 6), 'confront', None))
        return result

    def trial_bias(self, who, target, supported):
        # Emotion affects judgement, never manufactures a fact or an identity.
        anger = self.level(who, 'anger', target)
        fear = self.level(who, 'fear', target)
        attraction = self.level(who, 'attraction', target)
        return max(-.4, min(.6, (anger + fear) * .035 - attraction * .035)) if supported else 0.0
