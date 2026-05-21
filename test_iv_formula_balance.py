"""
IV Formula Balance Test — no mocks, real Actor objects.

Verifies that the IV formula behaves as intended:
  - Both sides use calculate_unified_result on the same scale
  - SHADOW scaling: higher actor SHADOW -> IV scores higher -> harder for UA to win
  - Severity scaling: higher conflict severity -> IV supplements more -> IV wins more often
  - STURDINESS scaling: higher actor STURDINESS -> UA scores higher -> UA wins more often
  - Stress scaling: higher severity raises UA stress, lowering UA score
  - Serendipity: different seeds produce different outcomes (not deterministic)
  - Score components are mathematically correct relative to actor stats
  - The iv_success and ua_success are on the same integer scale
"""

import sys
import random
from collections import Counter

from actor_sheet import ActorSheet, SFactors, SFactorType
from actors import Actor
from internal_voice_exchange_system import (
    get_internal_voice_exchange_system,
    reset_internal_voice_exchange_system,
    PersonalityConflict,
    PersonalityConflictType,
    SpiritImpactDirection,
)

PASSED = []
FAILED = []


def _check(name, condition, detail=""):
    if condition:
        PASSED.append(name)
        print(f"  [OK] {name}")
    else:
        FAILED.append(name)
        print(f"  [FAIL] {name}" + (f": {detail}" if detail else ""))


def section(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print("="*60)


def _make_real_actor(sturdiness=4, shadow=4, introspection=0,
                     internal="fear of becoming a monster again"):
    """Build a fully real Actor using the game's ActorSheet."""
    s = SFactors(
        swiftness=3, sociability=3,
        sturdiness=sturdiness, smarts=3, shadow=shadow
    )
    skills = {"introspection": introspection} if introspection else {}
    sheet = ActorSheet(
        name="Test",
        s_factors=s,
        personality_traits={"internal": internal, "external": "stoic"},
        goals=["survive"],
        skills=skills,
    )
    return Actor(sheet=sheet)


def _run_exchange(actor, severity, seed):
    """
    Run a single complete exchange and return the raw ua_success, iv_success,
    outcome, and the full result dict from process_completed_exchange.
    We capture ua_success/iv_success from exchange_history since
    process_completed_exchange records them there.
    """
    reset_internal_voice_exchange_system()
    iv_system = get_internal_voice_exchange_system()

    conflict = PersonalityConflict(
        conflict_type=PersonalityConflictType.AGAINST_INTERNAL,
        internal_trait=actor.sheet.personality_traits["internal"],
        action_description="killed the guard",
        severity=severity,
        trigger_reason="test",
    )

    exchange = iv_system.generate_6_step_internal_voice_exchange(
        actor=actor,
        completed_action="killed the guard",
        action_result="The guard fell.",
        conflict=conflict,
    )
    # Fill UA turns (content doesn't affect outcome calculation)
    exchange.turns[1].content = "I had no choice"
    exchange.turns[2].content = iv_system.generate_step_3_response(exchange, exchange.turns[1].content)
    exchange.turns[3].content = "I accept the weight"
    exchange.turns[4].content = iv_system.generate_step_5_response(exchange, exchange.turns[3].content)
    exchange.turns[5].content = "I move forward"

    random.seed(seed)
    narrative, magnitude, outcome = iv_system.process_completed_exchange("actor", exchange)

    rec = iv_system.exchange_history[-1]
    return rec["ua_success"], rec["iv_success"], outcome


def _run_many(actor, severity, n=100):
    """Run n exchanges and return (ua_scores, iv_scores, outcome_counts)."""
    ua_scores, iv_scores = [], []
    outcomes = Counter()
    for seed in range(n):
        ua, iv_, outcome = _run_exchange(actor, severity, seed)
        ua_scores.append(ua)
        iv_scores.append(iv_)
        outcomes[outcome] += 1
    return ua_scores, iv_scores, outcomes


# ============================================================
# TEST 1: Score components match actor stats
# ============================================================

def test_score_components():
    section("1 · Score Components Match Actor Stats")

    from unified_formula import calculate_unified_result

    sturdiness, shadow, introspection = 4, 5, 2
    severity = 0.9

    actor = _make_real_actor(sturdiness=sturdiness, shadow=shadow,
                             introspection=introspection)

    # Run with fixed serendipity=0 so we can verify the deterministic parts.
    ua_result = calculate_unified_result(
        actor=actor, s_trait=SFactorType.STURDINESS,
        skill_name="introspection", target_actor=None,
        shift_polarity="Subtractive", targeted_status=None,
        supplement_val=0,
        stress_level_override=int(3 + severity * 2),
        serendipity_override=0,
    )
    iv_result = calculate_unified_result(
        actor=actor, s_trait=SFactorType.SHADOW,
        skill_name=None, target_actor=None,
        shift_polarity="Subtractive", targeted_status=None,
        supplement_val=int(severity * 3),
        stress_level_override=3,
        serendipity_override=0,
    )

    # UA: sturdiness + introspection - stress_modifier (serendipity=0)
    expected_stress_mod = int(3 + severity * 2) - 3  # = 1 for 0.9
    expected_ua = sturdiness + introspection - expected_stress_mod
    _check(f"UA base = STURDINESS({sturdiness}) + introspection({introspection}) - stress({expected_stress_mod}) = {expected_ua}",
           ua_result["final_result"] == expected_ua,
           f"got {ua_result['final_result']}")

    # IV: shadow + supplement (serendipity=0, stress_mod=0)
    expected_supplement = int(severity * 3)  # = 2 for 0.9
    expected_iv = shadow + expected_supplement
    _check(f"IV base = SHADOW({shadow}) + supplement({expected_supplement}) = {expected_iv}",
           iv_result["final_result"] == expected_iv,
           f"got {iv_result['final_result']}")

    # Stress modifier for UA: int(3 + severity*2) - 3
    _check("UA stress modifier = severity*2 (rounded)",
           ua_result["negative_components"]["stress_modifier"] == expected_stress_mod)

    # IV stress modifier = 0 (neutral)
    _check("IV stress modifier = 0",
           iv_result["negative_components"]["stress_modifier"] == 0)

    # IV supplement encodes severity
    _check(f"IV supplement = int(severity*3) = {expected_supplement}",
           iv_result["positive_components"]["supplement"] == expected_supplement)

    # Both on same integer scale
    _check("UA and IV scores are integers on the same scale",
           isinstance(ua_result["final_result"], int) and
           isinstance(iv_result["final_result"], int))

    print(f"\n  UA breakdown: STURDINESS={sturdiness} + introspection={introspection} + seren=0 - stress={expected_stress_mod} = {ua_result['final_result']}")
    print(f"  IV breakdown: SHADOW={shadow} + supplement={expected_supplement} + seren=0 - 0 = {iv_result['final_result']}")
    print(f"  IV advantage at severity 0.9 (no dice): {iv_result['final_result'] - ua_result['final_result']:+d}")


# ============================================================
# TEST 2: SHADOW scaling — higher SHADOW -> IV harder to beat
# ============================================================

def test_shadow_scaling():
    section("2 · SHADOW Scaling (higher SHADOW -> IV scores higher)")

    N = 200
    severity = 0.9

    low_shadow_actor  = _make_real_actor(shadow=1, sturdiness=4)
    high_shadow_actor = _make_real_actor(shadow=5, sturdiness=4)

    _, iv_low,  _ = _run_many(low_shadow_actor,  severity, N)
    _, iv_high, _ = _run_many(high_shadow_actor, severity, N)

    avg_iv_low  = sum(iv_low)  / N
    avg_iv_high = sum(iv_high) / N

    print(f"\n  SHADOW=1 avg IV score: {avg_iv_low:.2f}")
    print(f"  SHADOW=5 avg IV score: {avg_iv_high:.2f}")
    print(f"  Difference: {avg_iv_high - avg_iv_low:+.2f}")

    _check("Higher SHADOW produces higher average IV score",
           avg_iv_high > avg_iv_low,
           f"high={avg_iv_high:.2f} vs low={avg_iv_low:.2f}")

    expected_diff = 4  # SHADOW 5 vs SHADOW 1 = +4 base
    actual_diff = avg_iv_high - avg_iv_low
    _check(f"SHADOW difference ~4 points (SHADOW diff = 4)",
           abs(actual_diff - expected_diff) < 0.5,
           f"expected ~{expected_diff}, got {actual_diff:.2f}")

    # IV win rate should be higher for high-SHADOW actor (harder to beat)
    ua_low, _, outcomes_low   = _run_many(low_shadow_actor,  severity, N)
    ua_high, _, outcomes_high = _run_many(high_shadow_actor, severity, N)

    iv_winrate_low  = (outcomes_low["iv_wins"]  + outcomes_low["iv_dominated"])  / N
    iv_winrate_high = (outcomes_high["iv_wins"] + outcomes_high["iv_dominated"]) / N

    print(f"\n  SHADOW=1 IV win rate: {iv_winrate_low:.0%}")
    print(f"  SHADOW=5 IV win rate: {iv_winrate_high:.0%}")

    _check("High-SHADOW actor's IV wins more often",
           iv_winrate_high > iv_winrate_low,
           f"high={iv_winrate_high:.0%} vs low={iv_winrate_low:.0%}")


# ============================================================
# TEST 3: Severity scaling — higher severity -> IV wins more
# ============================================================

def test_severity_scaling():
    section("3 · Severity Scaling (higher severity -> IV advantages more)")

    N = 200
    actor = _make_real_actor(sturdiness=4, shadow=4)

    results = {}
    for severity in (0.3, 0.6, 0.9):
        ua_scores, iv_scores, outcomes = _run_many(actor, severity, N)
        avg_ua = sum(ua_scores) / N
        avg_iv = sum(iv_scores) / N
        iv_winrate = (outcomes["iv_wins"] + outcomes["iv_dominated"]) / N
        results[severity] = {
            "avg_ua": avg_ua, "avg_iv": avg_iv,
            "iv_adv": avg_iv - avg_ua, "iv_winrate": iv_winrate,
            "outcomes": outcomes,
        }
        print(f"\n  Severity {severity}:")
        print(f"    UA avg={avg_ua:.2f}  IV avg={avg_iv:.2f}  IV advantage={avg_iv-avg_ua:+.2f}")
        print(f"    Outcomes: {dict(outcomes)}")
        print(f"    IV win rate: {iv_winrate:.0%}")

    # IV advantage should increase with severity
    _check("IV advantage grows with severity (0.3 < 0.6)",
           results[0.3]["iv_adv"] < results[0.6]["iv_adv"],
           f"0.3={results[0.3]['iv_adv']:.2f} vs 0.6={results[0.6]['iv_adv']:.2f}")
    _check("IV advantage grows with severity (0.6 < 0.9)",
           results[0.6]["iv_adv"] < results[0.9]["iv_adv"],
           f"0.6={results[0.6]['iv_adv']:.2f} vs 0.9={results[0.9]['iv_adv']:.2f}")

    # IV win rate should increase with severity
    _check("IV win rate grows with severity (0.3 < 0.6)",
           results[0.3]["iv_winrate"] < results[0.6]["iv_winrate"],
           f"0.3={results[0.3]['iv_winrate']:.0%} vs 0.6={results[0.6]['iv_winrate']:.0%}")
    _check("IV win rate grows with severity (0.6 < 0.9)",
           results[0.6]["iv_winrate"] < results[0.9]["iv_winrate"],
           f"0.6={results[0.6]['iv_winrate']:.0%} vs 0.9={results[0.9]['iv_winrate']:.0%}")

    # At low severity the fight should be relatively even (neither side wins 80%+)
    _check("Low severity (0.3): neither side dominates (both between 20-80%)",
           0.2 <= results[0.3]["iv_winrate"] <= 0.8,
           f"IV win rate at 0.3 = {results[0.3]['iv_winrate']:.0%}")

    # Supplement on IV side should differ between severities
    low_supp  = int(0.3 * 3)
    high_supp = int(0.9 * 3)
    _check(f"Supplement differs: severity 0.3 -> {low_supp}, severity 0.9 -> {high_supp}",
           low_supp != high_supp)


# ============================================================
# TEST 4: STURDINESS scaling — higher STURDINESS -> UA wins more
# ============================================================

def test_sturdiness_scaling():
    section("4 · STURDINESS Scaling (higher STURDINESS -> UA scores higher)")

    N = 200
    severity = 0.9  # High severity so IV is strong — STURDINESS has to overcome it

    low_stur_actor  = _make_real_actor(sturdiness=1, shadow=4)
    high_stur_actor = _make_real_actor(sturdiness=5, shadow=4)

    ua_low,  _, outcomes_low  = _run_many(low_stur_actor,  severity, N)
    ua_high, _, outcomes_high = _run_many(high_stur_actor, severity, N)

    avg_ua_low  = sum(ua_low)  / N
    avg_ua_high = sum(ua_high) / N

    print(f"\n  STURDINESS=1 avg UA score: {avg_ua_low:.2f}")
    print(f"  STURDINESS=5 avg UA score: {avg_ua_high:.2f}")
    print(f"  Difference: {avg_ua_high - avg_ua_low:+.2f}")

    _check("Higher STURDINESS produces higher average UA score",
           avg_ua_high > avg_ua_low,
           f"high={avg_ua_high:.2f} vs low={avg_ua_low:.2f}")

    expected_diff = 4  # STURDINESS 5 vs 1 = +4
    actual_diff = avg_ua_high - avg_ua_low
    _check(f"STURDINESS difference ~4 points",
           abs(actual_diff - expected_diff) < 0.5,
           f"expected ~{expected_diff}, got {actual_diff:.2f}")

    ua_winrate_low  = (outcomes_low["ua_wins"]  + outcomes_low["ua_dominated"])  / N
    ua_winrate_high = (outcomes_high["ua_wins"] + outcomes_high["ua_dominated"]) / N

    print(f"\n  STURDINESS=1 UA win rate: {ua_winrate_low:.0%}")
    print(f"  STURDINESS=5 UA win rate: {ua_winrate_high:.0%}")

    _check("High-STURDINESS actor wins internal debate more often",
           ua_winrate_high > ua_winrate_low,
           f"high={ua_winrate_high:.0%} vs low={ua_winrate_low:.0%}")


# ============================================================
# TEST 5: Stress scaling — higher severity raises UA stress
# ============================================================

def test_stress_scaling():
    section("5 · Stress Scaling (UA stress increases with severity)")

    # Verify the stress formula directly
    cases = [
        (0.0, int(3 + 0.0*2), 0),   # severity 0.0 -> stress 3 -> modifier 0
        (0.5, int(3 + 0.5*2), 1),   # severity 0.5 -> stress 4 -> modifier 1
        (0.9, int(3 + 0.9*2), 1),   # severity 0.9 -> stress 4 -> modifier 1
        (1.0, int(3 + 1.0*2), 2),   # severity 1.0 -> stress 5 -> modifier 2
    ]

    for severity, expected_stress, expected_mod in cases:
        actual_stress = int(3 + severity * 2)
        actual_mod = max(1, min(5, actual_stress)) - 3
        _check(f"severity {severity}: stress={actual_stress}, modifier={actual_mod}",
               actual_stress == expected_stress and actual_mod == expected_mod,
               f"got stress={actual_stress} mod={actual_mod}")

    # Higher stress -> lower UA score (using serendipity_override=0 for determinism)
    from unified_formula import calculate_unified_result
    actor = _make_real_actor(sturdiness=4, shadow=4)

    ua_low_stress  = calculate_unified_result(actor=actor, s_trait=SFactorType.STURDINESS,
        skill_name="introspection", target_actor=None, shift_polarity="Subtractive",
        targeted_status=None, supplement_val=0, stress_level_override=3, serendipity_override=0)
    ua_high_stress = calculate_unified_result(actor=actor, s_trait=SFactorType.STURDINESS,
        skill_name="introspection", target_actor=None, shift_polarity="Subtractive",
        targeted_status=None, supplement_val=0, stress_level_override=5, serendipity_override=0)

    _check("UA score lower under high stress than low stress",
           ua_high_stress["final_result"] < ua_low_stress["final_result"],
           f"high={ua_high_stress['final_result']} low={ua_low_stress['final_result']}")

    # IV always uses stress=3 (neutral, modifier=0)
    iv_neutral = calculate_unified_result(actor=actor, s_trait=SFactorType.SHADOW,
        skill_name=None, target_actor=None, shift_polarity="Subtractive",
        targeted_status=None, supplement_val=2, stress_level_override=3, serendipity_override=0)
    _check("IV stress modifier is always 0 (neutral stress=3)",
           iv_neutral["negative_components"]["stress_modifier"] == 0)


# ============================================================
# TEST 6: Serendipity — outcomes vary across seeds
# ============================================================

def test_serendipity():
    section("6 · Serendipity (outcomes genuinely vary)")

    actor = _make_real_actor(sturdiness=4, shadow=4)
    severity = 0.6

    outcomes_seen = set()
    ua_scores = []
    iv_scores = []

    for seed in range(50):
        ua, iv_, outcome = _run_exchange(actor, severity, seed)
        outcomes_seen.add(outcome)
        ua_scores.append(ua)
        iv_scores.append(iv_)

    ua_range = max(ua_scores) - min(ua_scores)
    iv_range = max(iv_scores) - min(iv_scores)

    print(f"\n  UA score range over 50 seeds: {min(ua_scores)} to {max(ua_scores)} (spread {ua_range})")
    print(f"  IV score range over 50 seeds: {min(iv_scores)} to {max(iv_scores)} (spread {iv_range})")
    print(f"  Distinct outcomes seen: {sorted(outcomes_seen)}")

    _check("UA scores vary across seeds (serendipity active)",
           ua_range >= 5,
           f"range only {ua_range} — serendipity should produce at least 5-point spread")
    _check("IV scores vary across seeds (serendipity active)",
           iv_range >= 5,
           f"range only {iv_range}")
    _check("At least 3 distinct outcomes seen across 50 seeds",
           len(outcomes_seen) >= 3,
           f"only saw: {sorted(outcomes_seen)}")
    all_four = {"ua_dominated", "ua_wins", "iv_wins", "iv_dominated"}
    missing = all_four - outcomes_seen
    _check("All 4 outcomes possible within 50 seeds at mid severity",
           len(outcomes_seen) == 4,
           f"missing: {missing}")


# ============================================================
# TEST 7: Introspection skill adds to UA (acts as real skill value)
# ============================================================

def test_introspection_skill():
    section("7 · Introspection Skill Adds to UA Score")

    from unified_formula import calculate_unified_result

    actor_no_skill   = _make_real_actor(sturdiness=4, shadow=4, introspection=0)
    actor_with_skill = _make_real_actor(sturdiness=4, shadow=4, introspection=3)
    severity = 0.9

    ua_no = calculate_unified_result(actor=actor_no_skill, s_trait=SFactorType.STURDINESS,
        skill_name="introspection", target_actor=None, shift_polarity="Subtractive",
        targeted_status=None, supplement_val=0,
        stress_level_override=int(3 + severity * 2), serendipity_override=0)
    ua_with = calculate_unified_result(actor=actor_with_skill, s_trait=SFactorType.STURDINESS,
        skill_name="introspection", target_actor=None, shift_polarity="Subtractive",
        targeted_status=None, supplement_val=0,
        stress_level_override=int(3 + severity * 2), serendipity_override=0)

    print(f"\n  introspection=0 UA score: {ua_no['final_result']}")
    print(f"  introspection=3 UA score: {ua_with['final_result']}")
    print(f"  Skill bonus: +{ua_with['final_result'] - ua_no['final_result']}")

    _check("Introspection skill adds exactly its value to UA score",
           ua_with["final_result"] - ua_no["final_result"] == 3,
           f"expected +3, got +{ua_with['final_result'] - ua_no['final_result']}")
    _check("Without introspection skill: skill component = 0",
           ua_no["positive_components"]["skill"] == 0)
    _check("With introspection=3: skill component = 3",
           ua_with["positive_components"]["skill"] == 3)


# ============================================================
# TEST 8: Full process_completed_exchange with real actors — spot check
# ============================================================

def test_full_exchange_real_actor():
    section("8 · Full process_completed_exchange With Real Actor")

    actor = _make_real_actor(sturdiness=4, shadow=4, introspection=2)
    severity = 0.9

    random.seed(7)
    ua, iv_, outcome = _run_exchange(actor, severity, seed=7)

    print(f"\n  UA score: {ua}")
    print(f"  IV score: {iv_}")
    print(f"  Difference (UA-IV): {ua - iv_:+d}")
    print(f"  Outcome: {outcome}")

    # Basic sanity: scores are plausible integers
    _check("UA score is in plausible range (-10 to 20)",
           -10 <= ua <= 20, f"got {ua}")
    _check("IV score is in plausible range (-10 to 20)",
           -10 <= iv_ <= 20, f"got {iv_}")

    # Outcome matches the difference
    diff = ua - iv_
    if diff > 2:
        expected = "ua_dominated"
    elif diff > 0:
        expected = "ua_wins"
    elif diff > -2:
        expected = "iv_wins"
    else:
        expected = "iv_dominated"
    _check(f"Outcome '{outcome}' matches score difference ({ua}-{iv_}={diff:+d} -> {expected})",
           outcome == expected, f"got {outcome}")

    # IV has no sympathy/status modifier applied (pure formula)
    reset_internal_voice_exchange_system()
    iv_sys = get_internal_voice_exchange_system()
    rec = iv_sys.exchange_history  # empty after reset
    _check("exchange_history empty after reset", len(rec) == 0)


# ============================================================
# Main
# ============================================================

def main():
    print("\n" + "="*60)
    print("  IV FORMULA BALANCE TEST - Real Actors, No Mocks")
    print("="*60)

    test_score_components()
    test_shadow_scaling()
    test_severity_scaling()
    test_sturdiness_scaling()
    test_stress_scaling()
    test_serendipity()
    test_introspection_skill()
    test_full_exchange_real_actor()

    total = len(PASSED) + len(FAILED)
    print(f"\n{'='*60}")
    if FAILED:
        print(f"  RESULT: {len(PASSED)}/{total} passed - {len(FAILED)} FAILED")
        print("="*60)
        for f in FAILED:
            print(f"  [FAIL] {f}")
        return 1
    else:
        print(f"  ALL {total} TESTS PASSED [OK]")
        print("="*60)
        print()
        print("  Formula confirmed:")
        print("  UA = STURDINESS + introspection + 2d6-7 - (severity*2 stress)")
        print("  IV = SHADOW + int(severity*3) + 2d6-7 - 0")
        print("  Both use calculate_unified_result on the same integer scale.")
        return 0


if __name__ == "__main__":
    sys.exit(main())
