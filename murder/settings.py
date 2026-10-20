"""The tuning panel: the constants that decide how hard, how quarrelsome and how bawdy the show is, in one place.

Each setting has a default (the behaviour before the panel existed), a range and a one-line explanation. Values are saved in state/tuning.json and read live by the running day,
so a change lands on the next turn. TuningMixin is mixed into DayRunner (engine.py).
"""

# key, label, group, min, max, step, default, help
SETTINGS = [
    ("friction_rate", "Quarrels", "Drama", 0, 3, 0.1, 1.0, "How often small slights and snubs happen between people. 0 = never."),
    ("clue_clarity", "How clear the clues are", "Drama", 0, 2, 0.1, 0.8, "How readily evidence names its owner. 0 = labels torn out, nothing points anywhere; 1 = a label is often readable; 2 = almost always. Also scales the red herrings that point at other people (the lower, the more of them) and whether TereVi hands out free clues."),
    ("plot_rate", "Murder plots starting", "Drama", 0, 3, 0.1, 1.0, "How readily hatred, jealousy, blackmail and the deadline turn into a plot."),
    ("alliance_rate", "Alliances forming", "Drama", 0, 3, 0.1, 1.0, "How often trusting people ally."),
    ("betrayal_rate", "Betrayals", "Drama", 0, 3, 0.1, 1.0, "How readily allies break faith under pressure."),
    ("hook_notice", "Noticing something is wrong", "Drama", 0, 2, 0.1, 1.0, "How quickly people notice their room was searched or a lock was picked."),
    ("neovi_inspect", "NeoVi's daily inspection", "Drama", 0, 1, 1, 1, "1 = she inspects a bedroom each day and confiscates contraband; 0 = off."),
    ("experiment_quota", "Escape attempts per day", "Pacing", 0, 2, 0.1, 1.0, "Scales the daily quota of escape experiments (about 3 at 1.0)."),
    ("hallucinations", "Breaking minds", "Drama", 0, 1, 1, 1, "Low sanity bends beliefs (below 40), brings hallucinations (below 25) and acting on them (below 10). 0 = off."),
    ("parting_shot", "TereVi's parting shot", "Pacing", 0, 2, 0.1, 1.0, "How often TereVi takes someone with her when she loses (a last execution, or the floors flooding as the doors open). 0 = never."),
    ("last_stand", "Last-stand attempts", "Pacing", 0, 2, 0.1, 0.9, "When only a few are left, they try an unfinished way out if it is at least 70% (times this) done. Above 1.4 never."),
    ("escapee_help", "Escaped killers helping", "Pacing", 0, 3, 0.1, 1.0, "How often a killer the show let go tries to help the cast from outside (low by default: they risk prison and are rarely believed). 0 = never."),
    ("season_days", "Season length", "Pacing", 7, 56, 1, 28, "The season's run in days: at the end of the last day TereVi ends the show her way."),
    ("goal_push", "GM goals: how hard the director pushes", "Drama", 0, 2, 0.1, 1.0, "How often the director makes a move toward each goal the GM has set (odds and opportunities only). 0 = goals are tracked but not pushed."),
    ("gm_nudge", "GM pause: how much encourage or discourage shifts a roll", "Drama", 0, 0.5, 0.05, 0.25, "When you answer a paused roll, the chance moves by this much (it never becomes certain)."),
    ("decide_ahead", "Decide ahead", "Pacing", 0, 1, 1, 1, "1 = when you are watching live and have caught up with the island, the next block's decisions are asked for near the end of this one, so the next block starts at once (a few extra model calls a day when someone's situation changes in between); 0 = off."),
    ("proposer_calls", "Model proposals per day", "Pacing", 0, 6, 1, 2, "How many times a day the model may propose a murder plan for a stalled plot or a social move for someone in crisis (the engine checks every proposal). 0 = off."),
    ("escape_rate", "Work on the ways out", "Pacing", 0, 6, 0.1, 4.6, "How fast free-time work on a way out makes progress, and how keen people are to do it. 0 = nobody works on them in free time (experiments still count)."),
    ("drain_mult", "Everyday sanity drain", "Sanity", 0, 2, 0.1, 1.0, "How fast each quiet hour wears people down. 0 = no drain."),
    ("dread_mult", "Deadline dread", "Sanity", 0, 2, 0.1, 1.0, "How hard the approaching deadline hits everyone's sanity."),
    ("wear", "Captivity wear", "Sanity", 0, 10, 0.1, 2.8, "How far everyone's resting sanity sinks each night on the island (the level they recover towards). 0 = none; the default brings a week's survivors to around 60."),
    ("claim_trial", "Claim-based trial", "Drama", 0, 1, 1, 1, "1 = the engine runs the trial (claims, contradictions, who dares speak, lies, credibility, computed votes) and the model only voices the lines; 0 = the old trial, where the model writes the debate and casts the votes."),
    ("calm_days", "Calm window after a death", "Sanity", 0, 3, 1, 1, "Days after a closed case with no drain, dread or new quarrels. 0 = none."),
    ("vigil_gain", "Remembrance lift", "Sanity", 0, 12, 1, 6, "Sanity everyone regains at the remembrance after a death (+3 if they loved the dead)."),
    ("lock_fear", "Locking doors at night", "Night", 0, 2, 0.1, 1.0, "How readily frightened people bolt their doors."),
    ("affliction_rate", "Afflictions", "Body", 0, 2, 0.1, 1.0, "How readily sickness, panic, blindness, dizziness and the like take hold. 0 = never."),
    ("injury_severity", "Injuries", "Body", 0, 2, 0.1, 1.0, "How often blows, falls and fire cause broken bones, bleeding, concussion and worse."),
    ("faint_rate", "Fainting and knockouts", "Body", 0, 2, 0.1, 1.0, "How often people black out from injury, fear or a blow. 0 = never."),
    ("hunger_rate", "Hunger and thirst", "Body", 0, 2, 0.1, 1.0, "How fast people get hungry and thirsty. 0 = never."),
    ("perception", "Sight and hearing on the map", "World", 0, 1, 1, 1, "1 = witnesses, plotting windows and conversations in very large rooms depend on who can really see or hear (line of sight, light, walls, distance); 0 = everyone in a room counts."),
    ("environment", "Fire, water, smoke and breakage", "World", 0, 1, 1, 1, "1 = fires spread and burn, pipes burst, smoke chokes, doors and furniture break, blood and marks stay as evidence; 0 = none of it."),
    ("mind", "Needs, thoughts and stress", "World", 0, 1, 1, 1, "1 = sanity is the projection of facets, needs and fading thoughts (it recovers on its own when nothing new hurts and needs are met); 0 = the old scalar sanity."),
    ("stress_scale", "Stress strength", "World", 0.3, 3, 0.1, 1.0, "How hard thoughts, unmet needs and the deadline weigh on the mind (1 = normal). Higher breaks people sooner."),
    ("engine_decisions", "Engine-made routine turns", "World", 0, 1, 1, 1, "1 = quiet turns (nothing at stake) are decided from needs and relationships without asking the model; 0 = the model decides every turn. Needs the mind dial."),
    ("crime_pipeline", "Pursuit, witnesses and interrogation", "World", 0, 1, 1, 1, "1 = attackers follow a target who slipped away, a spree waives the trial only for its own killer, interrogations depend on facets and values and bring out what witnesses saw, and the trial gets a digest of what the cast saw; 0 = the old behaviour."),
    ("brain", "Memory and plans (the model as the mind)", "World", 0, 1, 1, 0, "1 = characters keep a real memory (the most relevant memories go into each prompt, not just the last few lines), the model writes what each person intends over the next few hours and the engine carries it out, and routine blocks stop costing a model call; 0 = the earlier behaviour."),
    ("fire_lethality", "Fire and smoke danger", "World", 0, 3, 0.1, 1.0, "How much damage flames, heat and smoke do each five minutes to people who stay in the room. 0 = harmless, 1 = rough, 3 = deadly. Sleepers, the unconscious, the badly hurt and the panicked are the ones who die."),
    ("free_time", "Free-time blocks", "World", 0, 1, 1, 1, "1 = the day alternates turns (morning, midday, evening) with free-time blocks (10:00, 14:00, 16:00, 20:00) where people eat, wash, play, tinker and chase their plots minute by minute; 0 = every block is a plain turn."),
    ("director_nudge", "Director opportunities", "Drama", 0, 2, 0.1, 1.0, "When a plotter has been waiting for a long time, the Director may steer their target somewhere quiet. It never makes the kill: the plotter still has to strike. 0 = off."),
    ("neovi_risk", "Turning on NeoVi", "Drama", 0, 3, 0.1, 1.0, "How readily people with a grudge against NeoVi, a snapped mind or an eye on her master key attack her. 0 = never."),
    ("snap_rate", "Snapping", "Drama", 0, 3, 0.1, 1.0, "How readily someone with very little sanity left, or pushed past their limit by someone they hate, kills with no plan. 0 = only planned killings."),
    ("modesty", "Embarrassment", "Tone", 0, 2, 0.1, 1.0, "How hard being seen in their underwear hits the modest. 0 = nobody minds."),
    ("gore", "Gore", "Tone", 0, 3, 1, 3, "How graphic deaths, wounds, bodies and executions are. 0 = cut away, 1 = restrained, 2 = vivid and brutal, 3 = graphic and unflinching (the default)."),
    ("flirt_level", "Flirtation", "Tone", 0, 3, 1, 3, "0 off, 1 occasional, 2 frequent, 3 steamy (the default). Adult flirtation and sexual tension between people who are into each other; nights together fade to black, never explicit."),
    ("banter_level", "Banter and crude jokes", "Tone", 0, 3, 1, 2, "0 civil, 1 light teasing, 2 friendly trash talk and the odd nasty joke, 3 relentless."),
]
DEFAULTS = {k: d for k, _, _, _, _, _, d, _ in SETTINGS}
RANGES = {k: (lo, hi) for k, _, _, lo, hi, _, _, _ in SETTINGS}


def meta():
    return [{"key": k, "label": lab, "group": g, "min": lo, "max": hi, "step": st, "default": d, "help": h} for k, lab, g, lo, hi, st, d, h in SETTINGS]


def clean(raw):
    out = {}
    for k, v in (raw or {}).items():
        if k in RANGES:
            try:
                f = float(v)
            except (TypeError, ValueError):
                continue
            lo, hi = RANGES[k]
            f = max(lo, min(hi, f))
            out[k] = int(round(f)) if isinstance(DEFAULTS[k], int) else round(f, 2)
    return out


class TuningMixin:
    def tune(self, key):
        v = (self.tuning_get() or {}).get(key)
        return DEFAULTS[key] if v is None else v
