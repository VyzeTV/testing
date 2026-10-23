"""Checked model requests and persistent stated motives, separate from outcomes.

Reasons are a character's account of their intention, never evidence or an alibi.
The manager builds read-only offers and records answers on the engine thread.
"""
import copy

from .commitments import active, concrete_reason
from .data_world import COMMON_ITEMS
from .emotions import active as feelings

LIMIT = 48
KEYS = ('action', 'target_room', 'target', 'to', 'item', 'talk_to', 'method')


def upgrade(state):
    state.setdefault('decision_history', {})
    state.setdefault('decision_seq', 0)


def text(value, limit=200):
    return ' '.join(value.split()[:25])[:limit] if isinstance(value, str) else ''


def choice(decision):
    return {k: copy.deepcopy(decision.get(k) or ([] if k == 'talk_to' else '')) for k in KEYS}


def describe(decision):
    parts = [decision.get('action') or 'stay']
    for key in ('target_room', 'target', 'to', 'item'):
        if decision.get(key):
            parts.append(key + '=' + decision[key])
    if decision.get('talk_to'):
        parts.append('talk_to=' + ','.join(decision['talk_to']))
    return ' '.join(parts)


def remember(state, owner, day, hour, decision, reason, source, **fields):
    upgrade(state)
    state['decision_seq'] += 1
    record = dict(id=f"d{state['decision_seq']}", owner=owner, day=day, hour=hour,
                  selected=choice(decision), reason=text(reason), source=source,
                  status='selected', known_by=[owner], **fields)
    records = state['decision_history'].setdefault(owner, [])
    records.append(record)
    records[:] = [r for r in records if day - r['day'] <= 30][-LIMIT:]
    return record


def rename_person(state, old, new):
    histories = state.get('decision_history', {})
    if old in histories:
        histories.setdefault(new, []).extend(histories.pop(old))
        histories[new] = sorted(histories[new], key=lambda r: (r['day'], r['hour'], int(r['id'][1:])))[-LIMIT:]
    for records in histories.values():
        for rec in records:
            if rec['owner'] == old:
                rec['owner'] = new
            rec['known_by'] = [new if p == old else p for p in rec['known_by']]
            for field in ('selected', 'applied', 'fallback'):
                request = rec.get(field, {})
                for key in ('target', 'to'):
                    if request.get(key) == old:
                        request[key] = new
                request['talk_to'] = [new if p == old else p for p in request.get('talk_to', [])]


class DecisionManager:
    def __init__(self, engine):
        self.e = engine
        upgrade(self.s)

    @property
    def s(self):
        return self.e.s

    def actions(self, cid, build=None):
        """Available request verbs; each mechanic still checks its own parameters."""
        e = self.e
        case = e.s.get('case')
        acts = 'stay|search|take|drop|give|use|rest' + ('|experiment' if e.revealed else '')
        if case and case.get('announced'):
            acts += '|investigate|interrogate'
        has_build = bool(e.build_lines(cid)) if build is None else build
        if has_build:
            acts += '|build'
        if e.murders and not case and e.rig_options(cid):
            acts += '|rig'
        for method in (e.stealth_acts, e.secret_acts, e.door_acts, e.craft_acts, e.itemuse_acts, e.condition_acts):
            acts += method(cid)
        if e.murders:
            acts += '|assault|sabotage'
            if not case:
                acts += '|attack'
            if e.can_end_life(cid):
                acts += '|end_life'
        return list(dict.fromkeys(acts.split('|')))

    def offers(self, cid, hour):
        """Stable IDs with checked verbs, reachable rooms and available objects."""
        e, w = self.e, self.e.world
        a = w.agents[cid]
        from .world import MOVE_BUDGET
        reach = sorted(w.reachable_rooms(cid, MOVE_BUDGET * e.step))
        actions = self.actions(cid)
        out = []

        def add(key, label, **fields):
            out.append(dict(id=key, label=label, decision=fields))

        for act in actions:
            if act not in ('take', 'use'):
                add('act:' + act, act.replace('_', ' '), action=act)
        for room in reach:
            if room != a['room']:
                add('go:' + room, 'go to ' + w.room_name(room), action='stay', target_room=room)
        # Blind people can request a conversation by identity without acquiring
        # visual knowledge of a person's location, clothes or health.
        for other in sorted(w.agents):
            if other != cid:
                add('talk:' + other, 'seek a conversation with ' + e.nm(other), action='stay', talk_to=[other])
        if not e.in_dark(cid):
            items = set(k for k, q in self.s['room_items'].get(a['room'], {}).items() if q > 0)
            items.update(COMMON_ITEMS.get(a['room'], []))
            for item in sorted(items):
                if e.item_within_reach(a['room'], item):
                    add('take:' + item, 'take ' + w.item_name(item), action='take', item=item)
        for item, qty in sorted(a['inv'].items()):
            if qty > 0 and w.item_spec(item).get('use'):
                add('use:' + item, 'use ' + w.item_name(item), action='use', item=item)
        return out

    def prompt(self, cid, hour, offers=None):
        offers = self.offers(cid, hour) if offers is None else offers
        listing = '; '.join(f"{o['id']}={o['label']}" for o in offers)
        anchors = ', '.join(f"{f['id']}={f['kind']}" for f in feelings(self.s, cid, self.e.day * 24 + hour)[:4])
        return ('CHECKED REQUESTS (availability, not guaranteed success): ' + listing + '.\n'
                + ('Your strongest emotion ids: ' + anchors + '.\n' if anchors else '') +
                'Return "option": one offered id, and "reason": a short first-person motive (max 25 words) matching that exact request. '
                'ID contracts: act:X fixes action=X; go:R fixes action=stay,target_room=R; talk:P fixes action=stay,talk_to=[P]; '
                'take:I and use:I fix action and item. To search after walking, select act:search and add a reachable target_room. '
                'The selected option fixes its listed action, destination, item or conversation target; supply other mechanic parameters in the normal fields. '
                'Do not contradict it. You may name "reason_refs": {"commitments": [your ids], "emotions": [your emotion ids]} if relevant. '
                'Your reason stays private unless you set "say_reason": true, which actually says it aloud where you act. '
                'An intention is not proof of an action, a location or innocence. Do not turn an old reason into a new fact.')

    def resolve(self, cid, hour, raw, offers=None):
        if not isinstance(raw, dict):
            raise ValueError('not a decision object')
        offers = self.offers(cid, hour) if offers is None else offers
        by_id = {o['id']: o for o in offers}
        current_ids = {o['id'] for o in self.offers(cid, hour)}
        option = raw.get('option')
        result = dict(raw)
        if option:
            if not isinstance(option, str) or option not in by_id or option not in current_ids:
                return None, 'the selected option is no longer available'
            fixed = by_id[option]['decision']
            if any(k in raw and raw[k] not in ('', None, []) and raw[k] != v for k, v in fixed.items()):
                return None, 'the supplied fields contradict the selected option'
            result.update(fixed)
        # Older responses remain usable, but do not gain invented reasons.
        action = result.get('action') or 'stay'
        if action not in self.actions(cid):
            return None, 'that action is not available now'
        from .world import MOVE_BUDGET
        w, a = self.e.world, self.e.world.agents[cid]
        room = result.get('target_room')
        if room and room != a['room'] and room not in w.reachable_rooms(cid, MOVE_BUDGET * self.e.step):
            return None, 'the requested destination cannot be reached this turn'
        for key in ('target', 'to'):
            target = result.get(key)
            if target and target not in w.agents and target not in ('neovi', 'terevi'):
                return None, 'the requested person is no longer present in the cast'
        talk = result.get('talk_to') or []
        if not isinstance(talk, list) or any(p not in w.agents and p not in ('neovi', 'terevi') for p in talk):
            return None, 'a conversation target is no longer available'
        if action in ('take', 'use'):
            key = action + ':' + str(result.get('item') or '')
            if key not in by_id or key not in current_ids:
                return None, 'the requested item is not available for that action'
        return result, ''

    def record(self, cid, hour, raw, decision, rejected=''):
        reason = text(raw.get('reason')) if isinstance(raw, dict) else ''
        refs = raw.get('reason_refs') if isinstance(raw, dict) else None
        refs = refs if isinstance(refs, dict) else {}
        owned = {c['id'] for c in active(self.s, cid)}
        now = self.e.day * 24 + hour
        felt = {f['id'] for f in feelings(self.s, cid, now)}
        valid = lambda key, ids: [r for r in refs.get(key, []) if isinstance(r, str) and r in ids][:4] if isinstance(refs.get(key), list) else []
        rec = remember(self.s, cid, self.e.day, hour, decision, reason,
                       'mock' if self.e.llm.mock else 'model', option=text(raw.get('option'), 100) if isinstance(raw, dict) else '',
                       refs=dict(commitments=valid('commitments', owned), emotions=valid('emotions', felt)))
        rec['label'] = (decision.get('action') or 'stay').replace('_', ' ')
        if decision.get('target_room'):
            rec['label'] += ' in the ' + self.e.world.room_name(decision['target_room'])
        if decision.get('talk_to'):
            rec['label'] = 'seek a conversation with ' + ', '.join(self.e.nm(p) for p in decision['talk_to'])
        if rejected:
            requested = {k: text(raw.get(k), 100) for k in KEYS if k != 'talk_to'}
            requested['talk_to'] = [text(p, 60) for p in raw.get('talk_to', [])[:4] if isinstance(p, str)] if isinstance(raw.get('talk_to'), list) else []
            rec.update(status='rejected', change=rejected, selected=requested, fallback=choice(decision))
        decision['decision_id'] = rec['id']
        return rec

    def current(self, cid, decision=None, hour=None):
        if (decision or {}).get('_src') == 'engine':
            return None
        records = self.s['decision_history'].get(cid, [])
        key = (decision or {}).get('decision_id')
        return next((r for r in reversed(records) if r['id'] == key or (not key and r['day'] == self.e.day and r['hour'] == hour)), None)

    def applied(self, tick, cid, decision, status='attempted', why=''):
        rec = self.current(cid, decision, tick['hour'])
        if not rec or rec['status'] == 'rejected':
            return
        changed = choice(decision) != rec['selected']
        rec.update(status='changed' if changed else status, applied=choice(decision))
        if changed or why:
            rec['change'] = why or rec.get('change') or ('engine direction changed the request: ' + text(decision.get('activity'), 100))
        # This records attempting a request, never that a kill, gift or chat succeeded.

    def say(self, tick, cid, decision):
        rec = self.current(cid, decision, tick['hour'])
        if not rec or rec.get('said') or not decision.get('say_reason') or not rec['reason'] or rec['status'] in ('changed', 'rejected', 'blocked'):
            return
        e, w = self.e, self.e.world
        a = w.agents.get(cid)
        if not a or a.get('asleep') or a.get('out'):
            return
        candidates = [p for p in w.occupants(a['room']) if p in w.agents and p != cid and not w.agents[p].get('asleep') and not w.agents[p].get('out')]
        heard = e.event_witnesses(cid, a['room'], 'talk', candidates)
        rec.update(said=True, known_by=sorted(set(heard + [cid])))
        e.log_event(tick, dict(type='decision', who=cid, room=a['room'], vis='public', decision=rec['id'],
                              text=f"{e.nm(cid)} explains their intention: \"{rec['reason']}\""), witnesses=heard, actor=cid)

    def context(self, cid, group=None):
        rows = [r for r in self.s['decision_history'].get(cid, []) if r['reason'] and 0 <= self.e.day - r['day'] <= 7]
        if group is not None:
            rows = [r for r in rows if r.get('said') and set(group) <= set(r['known_by'])]
        parts = [f"{r['id']} Day {r['day']} {r['hour']}: {describe(r['selected'])}; stated '{r['reason']}'"
                 + f"; {r['status']}" + (f" ({r['change']})" if r.get('change') else '') for r in rows[-3:]]
        return ('STATED MOTIVES (intentions only, not evidence or alibis): ' + ' | '.join(parts)) if parts else ''

    def signature(self, cid):
        records = self.s['decision_history'].get(cid, [])
        return (records[-1]['id'], records[-1]['status']) if records else None

    def view(self, cid):
        return copy.deepcopy(self.s['decision_history'].get(cid, [])[-8:])

    def reflect(self, tick, cid, reply):
        """Dawn applies explicit requests once through I2's ownership/cooldown rules."""
        if not isinstance(reply, dict):
            return []
        updates = reply.get('commitment_updates')
        if not isinstance(updates, list):
            return []
        done = []
        for update in updates[:3]:
            if not isinstance(update, dict):
                continue
            verb = update.get('op')
            if verb == 'keep':
                # Keeping a promise must not reset its due time.
                if any(c['id'] == update.get('id') for c in active(self.s, cid)):
                    done.append(update['id'])
            elif verb == 'drop' and concrete_reason(update.get('reason')):
                if self.e.commitments.drop(tick, cid, update.get('id'), update['reason']):
                    done.append(update.get('id'))
            elif verb == 'request':
                request = update.get('request')
                # A diary cannot speak a public promise to an absent recipient.
                if not isinstance(request, dict) or request.get('kind') == 'promise':
                    continue
                rec = self.e.commitments.request(tick, cid, request)
                if rec:
                    if rec['kind'] == 'resolve':
                        rec.setdefault('not_before', (self.e.day + 1) * 24 + 8)
                    done.append(rec['id'])
        return done
