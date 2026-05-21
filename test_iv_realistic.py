"""
Realistic & completeness test for the Internal Voice Exchange System.

Checks:
  1. All 6 conflict types produce coherent dialogue
  2. All 4 UA stances (defensive / accepting / defiant / rationalizing) produce
     distinct step-3 AND step-5 responses
  3. Personality trait injects grammatically into every IV line
  4. Spirit progression accumulates correctly across multiple exchanges
  5. Edge-case personalities (very long / one word / punctuation)
  6. AGAINST_EXTERNAL / FOR_EXTERNAL / EXTREME_ALIGNMENT completeness
     (currently falls to a generic fallback — detected and flagged)
"""

import sys
import io
import re
import random

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from actor_sheet import ActorSheet, SFactors
from actors import Actor
from internal_voice_exchange_system import (
    get_internal_voice_exchange_system,
    reset_internal_voice_exchange_system,
    PersonalityConflict,
    PersonalityConflictType,
    SpiritImpactDirection,
)
from internal_voice_exchange_integration import (
    run_6_step_internal_voice_conversation,
    display_spirit_impact,
)

_ANSI = re.compile(r'\x1b\[[0-9;]*m')


# ── helpers ──────────────────────────────────────────────────────────────────

def _make_actor(name="Test", sturdiness=4, shadow=4, internal="", external="", introspection=0):
    s = SFactors(swiftness=3, sociability=3, sturdiness=sturdiness, smarts=3, shadow=shadow)
    skills = {"introspection": introspection} if introspection else {}
    sheet = ActorSheet(name=name, s_factors=s,
        personality_traits={"internal": internal, "external": external},
        goals=["survive"], skills=skills)
    return Actor(sheet=sheet)


def _run_and_capture(actor, conflict, responses, seed=42):
    """Run a full exchange with canned responses; return (printed_lines, outcome, spirit_level)."""
    reset_internal_voice_exchange_system()
    iv = get_internal_voice_exchange_system()

    exchange = iv.generate_6_step_internal_voice_exchange(
        actor=actor, completed_action=conflict.action_description,
        action_result="Done.", conflict=conflict)

    resp_iter = iter(responses)
    def mock_prompt(_): return next(resp_iter, "...")

    buf = io.StringIO()
    real = sys.stdout; sys.stdout = buf
    try:
        completed = run_6_step_internal_voice_conversation(exchange, prompt_func=mock_prompt)
    finally:
        sys.stdout = real

    random.seed(seed)
    narrative, magnitude, outcome = iv.process_completed_exchange(actor.sheet.name, completed)

    buf2 = io.StringIO()
    sys.stdout = buf2
    try:
        display_spirit_impact(completed, iv.get_spirit_status(actor.sheet.name), outcome)
    finally:
        sys.stdout = real

    all_output = buf.getvalue() + buf2.getvalue()
    lines = [_ANSI.sub('', l) for l in all_output.splitlines() if _ANSI.sub('', l).strip()]
    spirit_level = iv.get_spirit_status(actor.sheet.name)['level']
    return lines, outcome, spirit_level, completed


PASS = []; FAIL = []
def chk(name, ok, detail=""):
    if ok:
        PASS.append(name); print(f"  [OK]   {name}")
    else:
        FAIL.append(name); print(f"  [FAIL] {name}" + (f" -- {detail}" if detail else ""))

def section(t):
    print(f"\n{'='*65}\n  {t}\n{'='*65}")


RESPONSES_DEFENSIVE    = ["I had no choice, it was necessary", "I was forced into this", "I stand by it"]
RESPONSES_ACCEPTING    = ["Yes, I know it was wrong", "I accept that I crossed a line", "I own this guilt"]
RESPONSES_DEFIANT      = ["Wrong — I deny any regret and stand firm", "I was right, full stop", "No remorse"]
RESPONSES_RATIONALIZING = ["But the mission required it", "However the context justifies it", "Although it was hard it was correct"]


# ═══════════════════════════════════════════════════════════════
# 1. All 6 conflict types generate a valid opening line
# ═══════════════════════════════════════════════════════════════
section("1 · All 6 Conflict Types — Opening Line")

actor = _make_actor(internal="fear of becoming a monster again")
reset_internal_voice_exchange_system()
iv = get_internal_voice_exchange_system()

for ct in PersonalityConflictType:
    conflict = PersonalityConflict(
        conflict_type=ct,
        internal_trait=actor.sheet.personality_traits["internal"],
        action_description="test action",
        severity=0.8,
        trigger_reason="test")
    ex = iv.generate_6_step_internal_voice_exchange(
        actor=actor, completed_action="test", action_result="done", conflict=conflict)
    opening = ex.turns[0].content
    has_trait = actor.sheet.personality_traits["internal"] in opening
    non_empty = bool(opening) and len(opening) > 15
    chk(f"{ct.name}: opening non-empty", non_empty, repr(opening[:80]))
    chk(f"{ct.name}: personality trait injected into opening", has_trait,
        f"trait not found in: {opening[:80]!r}")


# ═══════════════════════════════════════════════════════════════
# 2. Step 3 and 5 produce distinct responses for all 4 UA stances
# ═══════════════════════════════════════════════════════════════
section("2 · Four UA Stances — Step 3 & Step 5 Distinctness")

reset_internal_voice_exchange_system()
iv = get_internal_voice_exchange_system()
actor = _make_actor(internal="terror of becoming the monster he once fought")
conflict_ag = PersonalityConflict(
    conflict_type=PersonalityConflictType.AGAINST_INTERNAL,
    internal_trait=actor.sheet.personality_traits["internal"],
    action_description="executed the prisoner",
    severity=0.9, trigger_reason="test")

step3s = {}; step5s = {}
for label, ua2, ua4 in [
    ("defensive",     "I had no choice, it was forced",          "I was protecting others"),
    ("accepting",     "Yes I know it was wrong",                  "I accept the weight of this"),
    ("defiant",       "Wrong — I deny any guilt and stand firm",  "No I was right completely"),
    ("rationalizing", "But the mission required it",              "Although painful it was correct"),
]:
    ex = iv.generate_6_step_internal_voice_exchange(
        actor=actor, completed_action="executed", action_result="done", conflict=conflict_ag)
    s3 = iv.generate_step_3_response(ex, ua2)
    ex.turns[3].content = ua4
    s5 = iv.generate_step_5_response(ex, ua4)
    step3s[label] = s3; step5s[label] = s5
    chk(f"Step 3 [{label}]: non-empty", bool(s3) and len(s3) > 10)
    chk(f"Step 3 [{label}]: trait injected", actor.sheet.personality_traits["internal"] in s3,
        s3[:80])
    chk(f"Step 5 [{label}]: non-empty", bool(s5) and len(s5) > 10)
    chk(f"Step 5 [{label}]: trait injected", actor.sheet.personality_traits["internal"] in s5,
        s5[:80])

# All step-3 responses should differ from each other
labels = list(step3s)
for i in range(len(labels)):
    for j in range(i+1, len(labels)):
        chk(f"Step 3 [{labels[i]}] != [{labels[j]}]",
            step3s[labels[i]] != step3s[labels[j]])

# All step-5 responses should differ from each other
for i in range(len(labels)):
    for j in range(i+1, len(labels)):
        chk(f"Step 5 [{labels[i]}] != [{labels[j]}]",
            step5s[labels[i]] != step5s[labels[j]])


# ═══════════════════════════════════════════════════════════════
# 3. FOR_INTERNAL and IDENTITY_CRISIS dialogue is distinct from AGAINST_INTERNAL
# ═══════════════════════════════════════════════════════════════
section("3 · Conflict Type Dialogue Distinctness")

reset_internal_voice_exchange_system()
iv = get_internal_voice_exchange_system()
actor = _make_actor(internal="deep compassion for all living things")

def _get_step3(conflict_type, ua_input="I accept this"):
    conflict = PersonalityConflict(conflict_type=conflict_type,
        internal_trait=actor.sheet.personality_traits["internal"],
        action_description="test", severity=0.8, trigger_reason="test")
    ex = iv.generate_6_step_internal_voice_exchange(
        actor=actor, completed_action="test", action_result="done", conflict=conflict)
    return iv.generate_step_3_response(ex, ua_input)

s3_against = _get_step3(PersonalityConflictType.AGAINST_INTERNAL)
s3_for     = _get_step3(PersonalityConflictType.FOR_INTERNAL)
s3_crisis  = _get_step3(PersonalityConflictType.IDENTITY_CRISIS)

chk("AGAINST_INTERNAL step 3 differs from FOR_INTERNAL step 3",
    s3_against != s3_for, f"\nagainst: {s3_against}\nfor:     {s3_for}")
chk("AGAINST_INTERNAL step 3 differs from IDENTITY_CRISIS step 3",
    s3_against != s3_crisis)
chk("FOR_INTERNAL step 3 differs from IDENTITY_CRISIS step 3",
    s3_for != s3_crisis)

print(f"\n  AGAINST_INTERNAL: {s3_against[:90]}")
print(f"  FOR_INTERNAL:     {s3_for[:90]}")
print(f"  IDENTITY_CRISIS:  {s3_crisis[:90]}")


# ═══════════════════════════════════════════════════════════════
# 4. AGAINST_EXTERNAL / FOR_EXTERNAL / EXTREME_ALIGNMENT completeness check
# ═══════════════════════════════════════════════════════════════
section("4 · AGAINST_EXTERNAL / FOR_EXTERNAL / EXTREME_ALIGNMENT coverage")

reset_internal_voice_exchange_system()
iv = get_internal_voice_exchange_system()
actor = _make_actor(internal="secretly yearns for acceptance despite cold exterior")
FALLBACK = "Listen to what you're truly saying."

for ct in [PersonalityConflictType.AGAINST_EXTERNAL,
           PersonalityConflictType.FOR_EXTERNAL,
           PersonalityConflictType.EXTREME_ALIGNMENT]:
    conflict = PersonalityConflict(conflict_type=ct,
        internal_trait=actor.sheet.personality_traits["internal"],
        action_description="test", severity=0.8, trigger_reason="test")
    ex = iv.generate_6_step_internal_voice_exchange(
        actor=actor, completed_action="test", action_result="done", conflict=conflict)
    s3 = iv.generate_step_3_response(ex, "I accept this")
    s5 = iv.generate_step_5_response(ex, "I stand by it")
    chk(f"{ct.name} step 3: specific dialogue (not generic fallback)", FALLBACK not in s3, s3[:90])
    chk(f"{ct.name} step 5: specific dialogue (not generic fallback)", FALLBACK not in s5, s5[:90])
    print(f"         -> {s3[:90]}")


# ═══════════════════════════════════════════════════════════════
# 5. Personality trait injects grammatically — test varied traits
# ═══════════════════════════════════════════════════════════════
section("5 · Personality Trait Injection — Varied Trait Lengths")

reset_internal_voice_exchange_system()
iv = get_internal_voice_exchange_system()

trait_cases = [
    ("one word",        "guilt"),
    ("short phrase",    "fear of failure"),
    ("full sentence",   "the belief that violence only begets more violence"),
    ("very long",       "a deep-seated terror of repeating the sins of the father "
                        "and becoming the tyrant he swore to destroy, rooted in "
                        "childhood trauma and years of war"),
    ("with punctuation","compassion — the belief that all life deserves mercy, even enemies"),
]

for label, trait in trait_cases:
    actor_t = _make_actor(internal=trait)
    conflict = PersonalityConflict(
        conflict_type=PersonalityConflictType.AGAINST_INTERNAL,
        internal_trait=trait, action_description="killed someone",
        severity=0.9, trigger_reason="test")
    ex = iv.generate_6_step_internal_voice_exchange(
        actor=actor_t, completed_action="killed", action_result="done", conflict=conflict)
    opening = ex.turns[0].content
    s3 = iv.generate_step_3_response(ex, "I had no choice")
    chk(f"[{label}] trait in opening", trait in opening, opening[:100])
    chk(f"[{label}] trait in step 3",  trait in s3, s3[:100])
    print(f"\n  [{label}] opening:")
    print(f"    {opening}")


# ═══════════════════════════════════════════════════════════════
# 6. Spirit level accumulates realistically across a session
# ═══════════════════════════════════════════════════════════════
section("6 · Spirit Progression Across a Session")

reset_internal_voice_exchange_system()
actor = _make_actor(name="Kael", sturdiness=3, shadow=3,
                    internal="fear of becoming the monster he once fought")

session_events = [
    ("killed an unarmed guard",      PersonalityConflictType.AGAINST_INTERNAL, 0.9,
     ["I had no choice", "I protect my mission", "I live with it"]),
    ("executed a prisoner",          PersonalityConflictType.AGAINST_INTERNAL, 0.8,
     ["It was necessary", "War demands hard choices", "I accept it"]),
    ("spared a wounded enemy",       PersonalityConflictType.FOR_INTERNAL, 0.7,
     ["Yes it felt right", "Compassion is not weakness", "Always"]),
    ("tortured someone for intel",   PersonalityConflictType.AGAINST_INTERNAL, 1.0,
     ["The mission required it", "I had no choice", "I move forward"]),
    ("protected a child from harm",  PersonalityConflictType.FOR_INTERNAL, 0.8,
     ["Yes of course", "That is who I am", "Without hesitation"]),
]

print(f"\n  Start: Spirit = 0.0 (Uncertain)")
spirit_trajectory = [0.0]
prev_level = 0.0

for action, ct, severity, responses in session_events:
    lines, outcome, spirit_level, completed = _run_and_capture(
        actor,
        PersonalityConflict(conflict_type=ct, internal_trait=actor.sheet.personality_traits["internal"],
            action_description=action, severity=severity, trigger_reason="session"),
        responses, seed=7)
    delta = spirit_level - prev_level
    direction = "+" if delta >= 0 else ""
    spirit_trajectory.append(spirit_level)
    iv_sys = get_internal_voice_exchange_system()
    desc = iv_sys.get_spirit_status(actor.sheet.name)['description']
    print(f"  After '{action}':")
    print(f"    Outcome: {outcome:15s}  Spirit: {spirit_level:+.1f} ({delta:+.1f})  [{desc}]")
    prev_level = spirit_level

# Verify AGAINST_INTERNAL drives spirit down, FOR_INTERNAL drives it up
against_delta = spirit_trajectory[2] - spirit_trajectory[0]  # after 2 AGAINST events
for_delta     = spirit_trajectory[3] - spirit_trajectory[2]  # after 1 FOR event

chk("Two AGAINST_INTERNAL events lower spirit below start",
    spirit_trajectory[2] < spirit_trajectory[0],
    f"was {spirit_trajectory[0]:.1f}, after two against events: {spirit_trajectory[2]:.1f}")
chk("FOR_INTERNAL event raises spirit vs previous",
    spirit_trajectory[3] > spirit_trajectory[2],
    f"was {spirit_trajectory[2]:.1f}, after for event: {spirit_trajectory[3]:.1f}")
chk("Spirit trajectory spans meaningful range across session",
    max(spirit_trajectory) - min(spirit_trajectory) >= 1.0,
    f"trajectory: {[f'{v:.1f}' for v in spirit_trajectory]}")


# ═══════════════════════════════════════════════════════════════
# 7. Full end-to-end display check — all lines make sense
# ═══════════════════════════════════════════════════════════════
section("7 · End-to-End Display Sanity")

actor = _make_actor(name="Kael", sturdiness=4, shadow=5,
                    internal="terror of becoming the monster he once fought",
                    external="hard-edged mercenary who shows no weakness")
conflict = PersonalityConflict(
    conflict_type=PersonalityConflictType.AGAINST_INTERNAL,
    internal_trait=actor.sheet.personality_traits["internal"],
    action_description="executed the unarmed prisoner",
    severity=0.9, trigger_reason="test")

lines, outcome, spirit_level, completed = _run_and_capture(
    actor, conflict,
    ["I had no choice, it was him or me",
     "I refuse to be defined by one moment",
     "I carry this weight and move forward"],
    seed=12)

print()
for line in lines:
    print(f"  | {line}")

# Sanity checks on displayed content
full_text = "\n".join(lines)
trait = actor.sheet.personality_traits["internal"]

chk("Header appears",        "INTERNAL VOICE" in full_text)
chk("Personality trait in dialogue", trait in full_text,
    "personality trait missing from all displayed text")
chk("Spirit level displayed", "Spirit Level" in full_text)
chk("Outcome displayed",      "Outcome:" in full_text)
chk("No blank double-space gap (trait not empty)",
    "  -" not in full_text,
    "found '  -' pattern indicating blank trait injection")
chk("Master Time message absent", "Master Time Coordinator" not in full_text,
    "startup message leaked into player output")
chk("FOR_INTERNAL language not used for AGAINST_INTERNAL",
    "inner compass" not in full_text and "Your true self" not in full_text)


# ═══════════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════════
total = len(PASS) + len(FAIL)
print(f"\n{'='*65}")
if FAIL:
    print(f"  {len(PASS)}/{total} passed  --  {len(FAIL)} FAILED")
    print("="*65)
    for f in FAIL: print(f"  [FAIL] {f}")
    sys.exit(1)
else:
    print(f"  ALL {total} CHECKS PASSED")
    print("="*65)
    sys.exit(0)
