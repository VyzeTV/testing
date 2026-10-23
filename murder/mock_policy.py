"""Seeded character choices for the offline model, independent of model transport.

The adapter copies only an actor's own information. Policy functions consume that
snapshot and a supplied random source; they never mutate the world or use global
randomness. Engine checks and commitment/relationship gates still own outcomes.
"""
import copy

from .commitments import active as obligations
from .emotions import active as feelings, strength


def actor_context(engine, cid, hour=None, group=None):
    w, s = engine.world, engine.s
    a = w.agents[cid]
    now = engine.day * 24 + (s.get('_hour', 8) if hour is None else hour)
    m = engine.mind(cid)
    shared = set(group or [])
    emotions = [dict(id=e['id'], kind=e['kind'], strength=round(strength(e, now), 3),
                     target=e.get('target'), room=e.get('room'), cause=e['cause'])
                for e in feelings(s, cid, now)
                if group is None or shared <= set(e.get('known_by', [cid]))]
    commitments = [copy.deepcopy(c) for c in obligations(s, cid)
                   if (c.get('due') is None or c['due'] > now)
                   and c.get('not_before', 0) <= now
                   and (group is None or shared <= set(c.get('known_by', [cid])))]
    # No other person's private emotions, inventory, plots, or remote position.
    visible = {}
    if not engine.blind(cid) and not engine.in_dark(cid):
        for other in sorted(w.occupants(a['room'])):
            b = w.agents.get(other)
            if not b or other == cid or b.get('hiding') or b.get('asleep') or b.get('out'):
                continue
            # Avoid resolving randomized disguise recognition during prompt building.
            if engine.worn(other) and (set(engine.tags(engine.worn(other))) & {'mask', 'disguise'}
                                       or engine.owner_of(engine.worn(other)) not in (None, other)):
                continue
            visible[other] = dict(hp=b['hp'], sanity=b['sanity'])
    out = dict(cid=cid, facets=dict(m['facets']), values=dict(m['values']), needs=dict(m['needs']),
               hp=a['hp'], sanity=a['sanity'], aff=dict(a['aff']), drive=copy.deepcopy(a['drive']) if group is None else {},
               emotions=emotions, commitments=commitments, visible=visible,
               private_rooms=sorted({c['home'] for c in w.cast.values() if c.get('home') and c['home'] != w.cast[cid]['home']}),
               plan=copy.deepcopy(engine.plan_items(cid)) if group is None and engine.brain_on() else [])
    if group is None:
        # A work destination is offered only if an actual route and step exist.
        rid = engine.escape_route_for(cid) if engine.revealed and engine.tune('escape_rate') > 0 else None
        step = engine.escape_step_for(rid) if rid else None
        if step:
            out['work'] = dict(route=rid, step=step, room=engine.escape_work_room(cid, rid, step))
    return out


def pick(rng, options):
    """Stable weighted sampling; zero weight means unavailable, not a tiny chance."""
    options = [(max(0, weight), value) for weight, value in options if weight > 0]
    if not options:
        return None
    roll = rng.random() * sum(weight for weight, _ in options)
    for weight, value in options:
        roll -= weight
        if roll < 0:
            return value
    return options[-1][1]


def facet(actor, name):
    return actor.get('facets', {}).get(name, 50) / 100


def emotion(actor, kind, target=None):
    return max((e['strength'] for e in actor.get('emotions', [])
                if e['kind'] == kind and (target is None or e.get('target') == target)), default=0) / 10


def chance(rng, base, factor):
    # Existing stress-test knobs retain exact off/force semantics.
    return base >= 1 or (base > 0 and rng.random() < min(.85, base * max(.05, factor)))


def company_score(actor, other):
    aff = actor.get('aff', {}).get(other, 0)
    fear = emotion(actor, 'fear', other)
    anger = emotion(actor, 'anger', other)
    return max(.02, .5 + aff / 8 + emotion(actor, 'attraction', other) * 2
               + emotion(actor, 'loneliness') + emotion(actor, 'grief') * .5 - fear * 3 - anger)


def hostile_score(actor, other):
    return max(.02, .2 - actor.get('aff', {}).get(other, 0) / 6
               + emotion(actor, 'anger', other) * 3 + emotion(actor, 'fear', other))


def decide(ctx, rng, knobs):
    a = ctx.get('actor', {})
    f = lambda k: facet(a, k)
    humans = sorted(set(ctx.get('humans_here', [])) & set(a.get('visible', {}))) if 'actor' in ctx else sorted(ctx.get('humans_here', []))
    reach = sorted(set(ctx.get('reachable', [])))
    room, home = ctx['room'], ctx['home']
    act = dict(action='stay', activity='Taking a moment', talk_to=[], intent='', thought='I need to choose carefully.')
    if ctx.get('end_ok') and chance(rng, knobs.mock_suicide_prob, 1):
        return dict(act, action='end_life', method='the cellar steps', activity='Slipping away', thought="I can't do this any more.")
    commitments = a.get('commitments', [])
    plotting = next((c for c in commitments if c['kind'] == 'plot'), None)
    anger = emotion(a, 'anger')
    aggression = (.1 + f('anger') + f('cruelty') + f('impulsiveness') + anger
                  - f('altruism') * .7) * (1.4 if a.get('sanity', 70) < 30 else .7)
    target = pick(rng, [(hostile_score(a, p), p) for p in humans])
    if target:
        aggression *= min(2, .15 + hostile_score(a, target))
    # Existing plans belong to the planner: do not overwrite stage or switch victims.
    if not plotting and ctx.get('plot_ok') and target and chance(rng, knobs.mock_plot_prob, aggression):
        act['plot'] = dict(target=target, stage='brooding', method='something sharp',
                           step='Watching for a moment alone together.', cover='')
    if not plotting and ctx.get('murder_ok') and target and chance(rng, knobs.mock_murder_prob, aggression):
        return dict(act, action='attack', target=target, method=pick(rng, [(1, w) for w in sorted(ctx.get('weapons') or ['hands'])]), activity='Losing control')
    if not plotting and ctx.get('violence_ok') and target and chance(rng, knobs.mock_assault_prob, aggression * .6):
        return dict(act, action='assault', target=target, method='hands', activity='Lashing out')
    if not plotting and ctx.get('violence_ok') and chance(rng, knobs.mock_sabotage_prob, f('cruelty') * f('impulsiveness')):
        return dict(act, action='sabotage', method='lights', activity='Tampering with the lights')
    # Health and sleep take priority over ordinary social plans and experiments.
    if a.get('hp', 100) < 40 or a.get('needs', {}).get('rest', 70) < 20 or ctx['hour'] >= 21:
        return dict(act, action='rest', target_room=home if home in reach or home == room else room,
                    activity='Resting somewhere safe', thought='I need to recover first.')
    due = sorted((c for c in commitments if c['kind'] != 'plot'), key=lambda c: (c.get('due') or float('inf'), c['id']))
    for c in due:
        if c['kind'] == 'host' and c.get('due') and c['due'] - (ctx.get('now', 0)) > 4:
            continue
        if c.get('room') and (c['room'] in reach or c['room'] == room):
            return finish(dict(act, target_room=c['room'], activity=c['title'], thought='I said I would be there.'), ctx, a)
        if c.get('target') in humans:
            return finish(dict(act, talk_to=[c['target']], intent=c['title'], activity='Following through',
                               thought='I still owe them this.'), ctx, a)
    work = a.get('work')
    if work and not plotting and chance(rng, knobs.mock_experiment_prob, .3 + f('curiosity') * 1.4 + f('courage') * .4):
        return finish(dict(act, action='experiment', idea=f"Test the {work['step']} step of the {work['route']} way out.",
                           activity='Testing a way out'), ctx, a)
    if not commitments and humans and not ctx.get('investigating') and chance(rng, knobs.mock_host_prob, f('gregariousness') * 1.5 + f('humour') * .4):
        act['host'] = dict(kind='meal' if f('altruism') > .6 else 'game', where=room, invite='all',
                           text='A little company might help us through this.', secret_from=[])
    options = [(1, dict(activity='Keeping my own company')),
               (.1 + (1 - a.get('needs', {}).get('rest', 70) / 100) * 2, dict(action='rest', activity='Resting for a bit'))]
    for other in humans:
        options.append(((.2 + f('gregariousness') * 1.6) * company_score(a, other),
                        dict(talk_to=[other], intent='See how they are holding up.', activity='Making time for company')))
    if ctx.get('investigating'):
        options.append((1 + f('curiosity') * 3 + a.get('values', {}).get('truth', 50) / 50,
                        dict(action='investigate', activity='Looking for clues')))
    else:
        options.append((.2 + f('curiosity'), dict(action='search', activity='Looking into the room')))
    if work and work['room'] in reach and not plotting:
        options.append((.3 + f('curiosity') + f('altruism') + emotion(a, 'guilt'),
                        dict(target_room=work['room'], intent='Work on a way out together.', activity='Getting back to work on a way out')))
    for dest in reach:
        if dest == room or dest in a.get('private_rooms', []) or (dest.startswith('bedroom') and dest != home):
            continue
        unpleasant = max((e['strength'] / 10 for e in a.get('emotions', [])
                          if e.get('room') == dest and e['kind'] in ('fear', 'grief')), default=0)
        options.append(((.15 + f('curiosity') * .4) * max(.02, 1 - unpleasant), dict(target_room=dest, activity='Taking a walk')))
    act.update(pick(rng, options))
    return finish(act, ctx, a)


def finish(act, ctx, actor):
    """Plans stay coherent with this choice; preserve unfinished plans when possible."""
    if not ctx.get('brain'):
        return act
    plan = copy.deepcopy(actor.get('plan', []))[:3]
    if not plan:
        for other in act.get('talk_to', []):
            plan.append(dict(do='talk', who=other, where='', why=act.get('intent') or 'keep them company'))
        work = actor.get('work')
        if work and act.get('target_room') == work['room']:
            plan.append(dict(do='work', who='', where=work['room'], why='help with the way out'))
        elif act.get('target_room'):
            plan.append(dict(do='go', who='', where=act['target_room'], why=act['activity']))
    act['plan'] = plan[:3]
    return act


def react(ctx, rng):
    a = ctx.get('actor', {})
    f = lambda k: facet(a, k)
    humans = sorted(set(ctx.get('humans', [])) & set(a.get('visible', {})))
    hurt = [p for p in humans if a['visible'][p]['hp'] < 75]
    scared = [p for p in humans if a['visible'][p]['sanity'] < 45]
    options = [(1, ('stay', '', 'Give me a second.')),
               (.3 + emotion(a, 'fear') + (1 - f('courage')), ('alert', '', 'Can somebody help here?'))]
    if ctx.get('reachable'):
        options.append(((1 - f('courage')) * 2 + emotion(a, 'fear') * 3 + (1 if a.get('hp', 100) < 40 else 0),
                        ('flee', '', 'I need to get clear.')))
    for p in hurt:
        loyal = any(c.get('target') == p and c['kind'] in ('protect', 'pact') for c in a.get('commitments', []))
        options.append((f('altruism') ** 2 * 8 + (8 if loyal else 0), ('help', p, 'Hold still. Let me help.')))
    for p in scared:
        options.append((f('altruism') * company_score(a, p) * 3, ('comfort', p, 'Stay with me. Breathe.')))
    for p in humans:
        hostility = emotion(a, 'anger', p) + max(0, -a.get('aff', {}).get(p, 0)) / 10
        options.append((hostility * f('courage') * f('anger') * 3, ('confront', p, 'Enough. Back off.')))
    kind, target, line = pick(rng, options)
    destinations = sorted(ctx.get('reachable', []))
    home = ctx.get('home')
    reasons = {'stay': 'I need a moment to understand what is happening.', 'alert': 'We need other people to help.',
               'flee': 'I want to get clear of this danger.', 'help': 'Someone is hurt and I want to help.',
               'comfort': 'I want to steady someone who is distressed.', 'confront': 'I want them to stop what they are doing.'}
    return dict(reaction=kind, target=target, to_room=(home if home in destinations else destinations[0]) if destinations else '',
                line=line, act='', thought='I have to deal with what is happening here.', reason=reasons[kind])


def reflect(ctx, rng, shift_probability):
    a = ctx.get('actor', {})
    emotions = a.get('emotions', [])
    strongest = max(emotions, key=lambda e: e['strength'], default=None)
    diary = (f"I still feel {strongest['kind']}: {strongest['cause']}." if strongest else
             (' '.join(ctx.get('events', [])[-3:]) or 'A quiet day.'))[:240]
    motives = [m for m in ctx.get('stated_motives', []) if m['reason'] and m['status'] != 'rejected']
    if motives:
        last = motives[-1]
        diary = diary[:140] + f" Earlier I meant to {last.get('label') or last['selected']['action'].replace('_', ' ')} because {last['reason']}"
    out = dict(diary=diary, drive='keep', target='', arc='')
    # A persistent goal does not spin to a random new drive every night.
    if a.get('commitments') or not strongest or strongest['strength'] < 4 or not chance(rng, shift_probability, 1):
        return out
    kind, target = strongest['kind'], strongest.get('target')
    drive = None
    if kind == 'anger' and target in ctx.get('ids', []) and facet(a, 'vengefulness') >= .65:
        drive = 'avenger'
    elif kind == 'guilt' and facet(a, 'altruism') >= .6:
        drive, target = 'protector', ''
    elif kind == 'fear':
        drive, target = 'survivor', ''
    elif kind == 'attraction' and target in ctx.get('ids', []) and facet(a, 'romantic') >= .6:
        drive = 'romantic'
    if drive and drive != a.get('drive', {}).get('id'):
        out.update(drive=drive, target=target or '', arc=f"The lingering {kind} is changing what I want.")
    return out


def social_proposal(ctx, rng):
    a = ctx.get('actor', {})
    ids = sorted(p for p in ctx.get('ids', []) if p != ctx.get('cid'))
    options = []
    for p in ids:
        warmth = company_score(a, p)
        options.extend([(warmth * facet(a, 'altruism'), ('comfort', p)),
                        (warmth * facet(a, 'trust'), ('confide', p)),
                        (emotion(a, 'anger', p) * facet(a, 'courage'), ('confront', p))])
        if a.get('aff', {}).get(p, 0) >= 4 and not emotion(a, 'fear', p):
            options.append((facet(a, 'romantic') * warmth, ('flirt', p)))
    chosen = pick(rng, options)
    return dict(move=chosen[0], to=chosen[1], about='', reason='I want to ' + chosen[0] + ' them because of how I feel toward them.') if chosen else {}


def conversation_effects(people, rng):
    """Small changes follow the participants' dispositions and existing feelings."""
    affinity, special, bonds = [], [], []
    humans = sorted((p for p in people if p.get('human', True)), key=lambda p: p['id'])
    pairs = [(a, b) for a in humans for b in humans if a['id'] < b['id']]
    if not pairs:
        return affinity, special, bonds
    a, b = pick(rng, [(company_score(a.get('actor', {}), b['id']) + company_score(b.get('actor', {}), a['id']), (a, b))
                     for a, b in pairs])
    aa, bb = a.get('actor', {}), b.get('actor', {})
    warmth = min(aa.get('aff', {}).get(b['id'], 0), bb.get('aff', {}).get(a['id'], 0))
    hostile = warmth <= -3 or emotion(aa, 'anger', b['id']) >= .5 or emotion(bb, 'anger', a['id']) >= .5
    if rng.random() < .6:
        # Conversation cannot randomly flip a friendly pair into abuse.
        delta = -1 if hostile else 1
        affinity = [dict(**{'from': a['id'], 'to': b['id']}, delta=delta),
                    dict(**{'from': b['id'], 'to': a['id']}, delta=delta)]
    if not hostile and rng.random() < .25:
        grief = max(emotion(aa, 'grief'), emotion(bb, 'grief'), emotion(aa, 'fear'), emotion(bb, 'fear'))
        kind = 'comfort' if grief > .3 and max(facet(aa, 'altruism'), facet(bb, 'altruism')) >= .5 else 'laughter'
        special = [dict(kind=kind, who=[a['id'], b['id']], why='offering support' if kind == 'comfort' else 'sharing a lighter moment')]
    if warmth >= 7 and rng.random() < .1:
        kind = 'romance' if min(facet(aa, 'romantic'), facet(bb, 'romantic')) >= .6 else 'pact'
        bonds = [dict(a=a['id'], b=b['id'], kind=kind)]
    return affinity, special, bonds


def explain(ctx, decision):
    """Give the mock's existing choice a matching stated motive, without new dice."""
    options = ctx.get('options', [])
    matches = [o for o in options if all(decision.get(k) == v for k, v in o['decision'].items())]
    chosen = max(matches, key=lambda o: (len(o['decision']), o['id']), default=None)
    if chosen:
        decision['option'] = chosen['id']
    a = ctx.get('actor', {})
    commitments, emotions = [], []
    label = chosen['label'] if chosen else decision.get('activity', 'take a moment')
    reason = 'I want to ' + label + '.'
    for c in a.get('commitments', []):
        if c.get('target') in decision.get('talk_to', []) or c.get('room') and c['room'] == decision.get('target_room'):
            reason = 'I intend to keep my commitment to ' + c['title'] + '.'
            commitments = [c['id']]
            break
    if not commitments:
        for f in a.get('emotions', []):
            kind, target = f['kind'], f.get('target')
            talking = bool(decision.get('talk_to'))
            if talking and kind in ('loneliness', 'grief'):
                reason = f"I want company because I still feel {kind}."
            elif talking and kind == 'attraction' and target in decision['talk_to']:
                reason = 'I want to spend time with someone I feel attracted to.'
            elif decision.get('action') in ('attack', 'assault') and kind == 'anger' and target == decision.get('target'):
                reason = 'I am still angry at them and want to lash out.'
            elif decision.get('target_room') and kind == 'fear' and target in ctx.get('humans_here', []):
                reason = 'I want some distance from someone who scares me.'
            else:
                continue
            emotions = [f['id']] if f.get('id') else []
            break
    if decision.get('action') == 'rest':
        reason, commitments, emotions = 'I need to rest and recover before doing anything else.', [], []
    decision['reason'] = reason[:200]
    decision['reason_refs'] = dict(commitments=commitments, emotions=emotions)
    return decision
