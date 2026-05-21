"""
Demo: what the player actually sees when the Internal Voice Exchange fires.

Runs three scenarios:
  A) AGAINST_INTERNAL, UA loses  (iv_dominated)
  B) AGAINST_INTERNAL, UA wins   (ua_dominated)
  C) FOR_INTERNAL,     UA wins   (spirit affirmed)

No mocks — real Actor objects, real formula.
ANSI colour codes are stripped so the text is readable in any terminal.
"""

import sys
import re
import io
import random

# Force UTF-8 so emoji / box-drawing chars don't crash Windows cp1252
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from actor_sheet import ActorSheet, SFactors
from actors import Actor
from internal_voice_exchange_system import (
    get_internal_voice_exchange_system,
    reset_internal_voice_exchange_system,
    PersonalityConflict,
    PersonalityConflictType,
)
from internal_voice_exchange_integration import (
    run_6_step_internal_voice_conversation,
    display_spirit_impact,
)


_ANSI = re.compile(r'\x1b\[[0-9;]*m')

def _strip(text):
    return _ANSI.sub('', text)


class _CapturingStream(io.StringIO):
    """Capture everything printed, then replay stripped."""
    pass


def run_scenario(label, actor, conflict, responses, seed):
    """
    Fully run one IV exchange scenario and print the player-visible output.
    `responses` is a list of 3 strings the player would type at the prompts.
    """
    print(f"\n{'#'*70}")
    print(f"  SCENARIO: {label}")
    print(f"{'#'*70}")

    reset_internal_voice_exchange_system()
    iv_system = get_internal_voice_exchange_system()

    exchange = iv_system.generate_6_step_internal_voice_exchange(
        actor=actor,
        completed_action=conflict.action_description,
        action_result="The deed is done.",
        conflict=conflict,
    )

    resp_iter = iter(responses)
    def mock_prompt(_prompt):
        response = next(resp_iter, "...")
        # Show what the player typed
        print(f"  [Player types]: {response}")
        return response

    # Capture display output so we can strip ANSI
    buf = _CapturingStream()
    real_stdout = sys.stdout
    sys.stdout = buf
    try:
        completed = run_6_step_internal_voice_conversation(
            exchange, prompt_func=mock_prompt
        )
    finally:
        sys.stdout = real_stdout

    # Replay stripped
    for line in buf.getvalue().splitlines():
        cleaned = _strip(line)
        if cleaned.strip():
            print(cleaned)

    # Process and show spirit impact
    random.seed(seed)
    narrative, magnitude, outcome = iv_system.process_completed_exchange(
        actor.sheet.name, completed
    )

    spirit_status = iv_system.get_spirit_status(actor.sheet.name)

    buf2 = _CapturingStream()
    sys.stdout = buf2
    try:
        display_spirit_impact(completed, spirit_status, outcome)
    finally:
        sys.stdout = real_stdout

    for line in buf2.getvalue().splitlines():
        cleaned = _strip(line)
        if cleaned.strip():
            print(cleaned)

    print(f"\n  [Roll result] {narrative}")
    print(f"  [Spirit level now] {spirit_status['level']:.1f}  ({spirit_status['description']})")


def _make_actor(name, sturdiness, shadow, internal, external, introspection=0):
    s = SFactors(swiftness=3, sociability=3, sturdiness=sturdiness,
                 smarts=3, shadow=shadow)
    skills = {"introspection": introspection} if introspection else {}
    sheet = ActorSheet(
        name=name, s_factors=s,
        personality_traits={"internal": internal, "external": external},
        goals=["survive"], skills=skills,
    )
    return Actor(sheet=sheet)


# ─── Scenario A ─────────────────────────────────────────────────────────────
# Soldier who fears becoming a monster executes a prisoner.
# Low STURDINESS/SHADOW — UA gets crushed.

actor_A = _make_actor(
    name="Kael",
    sturdiness=2, shadow=5,
    internal="terror of becoming the monster he once fought",
    external="hard-edged mercenary who shows no weakness",
)
conflict_A = PersonalityConflict(
    conflict_type=PersonalityConflictType.AGAINST_INTERNAL,
    internal_trait=actor_A.sheet.personality_traits["internal"],
    action_description="executed the unarmed prisoner without mercy",
    severity=0.9,
    trigger_reason="Violence against helpless targets awakens the beast within",
)

run_scenario(
    label="AGAINST_INTERNAL — UA loses (iv_dominated)  [SHADOW=5, STURDINESS=2]",
    actor=actor_A,
    conflict=conflict_A,
    responses=[
        "He was a threat. I had no choice.",
        "No — I'm not a monster. I'm a soldier.",
        "I'll carry this. But I'd do it again.",
    ],
    seed=12,   # seed chosen to produce iv_dominated
)


# ─── Scenario B ─────────────────────────────────────────────────────────────
# Same soldier type but with high STURDINESS and introspection skill — UA holds firm.

actor_B = _make_actor(
    name="Kael",
    sturdiness=5, shadow=3,
    internal="terror of becoming the monster he once fought",
    external="hard-edged mercenary who shows no weakness",
    introspection=3,
)
conflict_B = PersonalityConflict(
    conflict_type=PersonalityConflictType.AGAINST_INTERNAL,
    internal_trait=actor_B.sheet.personality_traits["internal"],
    action_description="executed the unarmed prisoner without mercy",
    severity=0.7,
    trigger_reason="Violence against helpless targets awakens the beast within",
)

run_scenario(
    label="AGAINST_INTERNAL — UA wins (ua_dominated)  [SHADOW=3, STURDINESS=5, introspection=3]",
    actor=actor_B,
    conflict=conflict_B,
    responses=[
        "I had no choice — it was survival, not cruelty.",
        "I refuse to let one act define me. I know who I am.",
        "I am not the monster. I draw the line here.",
    ],
    seed=3,    # seed chosen to produce ua_dominated
)


# ─── Scenario C ─────────────────────────────────────────────────────────────
# Pacifist healer spares a wounded enemy. FOR_INTERNAL — spirit affirmed.

actor_C = _make_actor(
    name="Sera",
    sturdiness=3, shadow=4,
    internal="deep compassion — the belief that all life deserves a chance to heal",
    external="quiet herbalist who avoids conflict",
)
conflict_C = PersonalityConflict(
    conflict_type=PersonalityConflictType.FOR_INTERNAL,
    internal_trait=actor_C.sheet.personality_traits["internal"],
    action_description="tended the enemy soldier's wounds and let him go free",
    severity=0.7,
    trigger_reason="Act of mercy deeply aligns with core compassion",
)

run_scenario(
    label="FOR_INTERNAL — spirit affirmed  [SHADOW=4, compassionate healer]",
    actor=actor_C,
    conflict=conflict_C,
    responses=[
        "Yes. He was suffering. What else could I do?",
        "I know some will call it weakness. I call it who I am.",
        "I would do it again without hesitation.",
    ],
    seed=1,
)
