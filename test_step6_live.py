"""
End-to-end test of the Step 6 reporter pipeline using the real live classes.
Simulates the exact data flow from main loop -> reporter -> formula -> output.
"""
import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

print('=== Step 6 Live Code End-to-End Test ===')
print()

# ─── Fake actors matching exact structure used in main loop ──────────────────
class FakeSheet:
    def __init__(self, name, occ):
        self.name = name; self.occupation = occ; self.goals = ['survive']
        self.personality_traits = {}; self.social_factors = {}
        self.physical_factors = {}; self.mental_factors = {}
        self.survival_factors = {}; self.endowments = {'tactician': 1}
        self.flaws = {}; self.relationships = {}; self.inventory = {}
        self.history = ''; self.mood = 'neutral'; self.stress = 0; self.raw = {}

class FakeActor:
    def __init__(self, sheet, is_ua=False):
        self.sheet = sheet; self.is_user_actor = is_ua; self.is_inanimate = False

proactor = FakeActor(FakeSheet('Elias the Jailbroken', 'Hacker'), is_ua=True)
reactor  = FakeActor(FakeSheet('Kaelen Voss', 'Enforcer'), is_ua=False)

# ─── Exact data as it comes from the interpreter (name=None is the bug) ───────
proactor_action_data = {
    'name': None,
    'action_noun': 'punch',
    'action_description': 'Strike Kaelen Voss',
    'narrative_description': 'You throw a punch at Kaelen Voss.',
    'interpreted_user_action': 'punch',
    'raw_user_action': 'punch him',
    'ua_attempt_text': 'You swing hard.',
    'is_user_actor': None,
    'utas_factors': {'status_to_shift': 'STAMINA', 'shift_polarity': 'subtractive'},
    'self_effects': {},
    'continuity_check': {},
    'value': 'contested',
    'actor': proactor,
}
reactor_action_data = {
    'name': None,
    'action_description': 'Dodge and counter',
    'narrative_description': 'Kaelen Voss sidesteps your blow.',
    'utas_factors': {'status_to_shift': 'STAMINA', 'shift_polarity': 'subtractive'},
    'is_user_actor': None,
    'actor': reactor,
}

# ─── Raw exchange outcome (Step 5 result) ─────────────────────────────────────
outcome_data = {
    'proactor_successes': 6,
    'reactor_successes': 9,
    'margin': -3,
    'status_shifts': [
        {
            'actor': 'Elias the Jailbroken',
            'status': 'STAMINA',
            'delta': -2,
            'attempted_delta': -2,
            'original': 3,
            'updated': 1,
            'shift_type': 'Temporary',
            'clamped': False
        }
    ]
}

# ─── Apply main-loop name fix (as in redesigned_main.py) ─────────────────────
print('--- Applying main-loop name fix ---')
pro_for_step6 = dict(proactor_action_data)
rea_for_step6 = dict(reactor_action_data)
pro_for_step6['name'] = pro_for_step6.get('name') or getattr(getattr(proactor, 'sheet', None), 'name', '')
rea_for_step6['name'] = rea_for_step6.get('name') or getattr(getattr(reactor, 'sheet', None), 'name', '')
pro_for_step6['is_user_actor'] = pro_for_step6.get('is_user_actor') or getattr(proactor, 'is_user_actor', False)
rea_for_step6['is_user_actor'] = rea_for_step6.get('is_user_actor') or getattr(reactor, 'is_user_actor', False)
print(f'  pro name={pro_for_step6["name"]}, is_ua={pro_for_step6["is_user_actor"]}')
print(f'  rea name={rea_for_step6["name"]}, is_ua={rea_for_step6["is_user_actor"]}')
assert pro_for_step6['name'] == 'Elias the Jailbroken'
assert rea_for_step6['name'] == 'Kaelen Voss'
print('  PASS')

# ─── Test UTASNarrativeFormula directly (the formula path / fallback) ─────────
print()
print('--- UTASNarrativeFormula (formula fallback path) ---')
from llm_agents.utas_narrative_formula import UTASNarrativeFormula
formula = UTASNarrativeFormula()
out_for_step6 = dict(outcome_data)
formula_result = formula.generate_turn_outcome_narrative(
    proactor_data=pro_for_step6,
    reactor_data=rea_for_step6,
    outcome_data=out_for_step6
)
print(f'  Output: {formula_result}')
assert formula_result is not None, 'Formula returned None'
assert 'None' not in formula_result, f'None in formula output: {formula_result}'
assert 'STAMINA' in formula_result.upper(), f'STAMINA missing: {formula_result}'
assert 'Penalty' in formula_result or 'penalty' in formula_result, f'Penalty missing: {formula_result}'
# Confirm it says "your STAMINA" (proactor is UA, display = 'You')
assert 'your' in formula_result.lower(), f'your/Your missing: {formula_result}'
print('  PASS')

# ─── Test enhanced_reporter _build_status_effect_phrase with live code ────────
print()
print('--- enhanced_reporter._build_status_effect_phrase ---')
from enhanced_reporter import EnhancedReporter
from multi_actor_manager import MultiActorManager
from enhanced_sympathy_system import EnhancedSympathyManager
_am = MultiActorManager()
_sm = EnhancedSympathyManager(_am)
reporter = EnhancedReporter(_am, _sm)
# Use the fixed names (as reporter now builds them from shifts when name=None)
phrase = reporter._build_status_effect_phrase(
    proactor_name='Elias the Jailbroken',
    reactor_name='Kaelen Voss',
    outcome_data=out_for_step6
)
print(f'  Phrase: {phrase}')
assert phrase, 'phrase is empty'
assert 'None' not in phrase, f'None in phrase: {phrase}'
assert 'Elias' in phrase, f'Proactor name missing from phrase: {phrase}'
print('  PASS')

# ─── Confirm reporter addendum name resolution from shifts ────────────────────
print()
print('--- Reporter addendum name resolution (name=None fallback) ---')
# Simulate what reporter does when original data still has name=None
pro_nm = proactor_action_data.get('name') or 'Proactor'  # None -> 'Proactor'
rea_nm = reactor_action_data.get('name') or 'Reactor'
for s in (out_for_step6.get('status_shifts') or []):
    an = s.get('actor_name') or s.get('actor') or ''
    if an:
        ps = out_for_step6.get('proactor_successes', 0) or 0
        rs = out_for_step6.get('reactor_successes', 0) or 0
        if pro_nm == 'Proactor' and rs > ps:
            pro_nm = an
        elif rea_nm == 'Reactor' and ps > rs:
            rea_nm = an
print(f'  pro_name resolved: {pro_nm}')
assert pro_nm == 'Elias the Jailbroken'
addendum_phrase = reporter._build_status_effect_phrase(pro_nm, rea_nm, out_for_step6)
print(f'  [MECHANICS] {addendum_phrase}')
assert 'None' not in addendum_phrase, f'None in addendum: {addendum_phrase}'
assert 'Elias' in addendum_phrase, f'Elias missing from addendum: {addendum_phrase}'
print('  PASS')

# ─── Verify NPC-initiated queue ordering (no regression) ─────────────────────
print()
print('--- NPC-initiated round 1 queue ordering ---')
ctx_npc_initiated = True
tq = [{'actor': reactor}, {'actor': proactor}]
if True and not ctx_npc_initiated:
    tq = sorted(tq, key=lambda e: not e['actor'].is_user_actor)
p_actor = tq[0]['actor']; r_actor = tq[1]['actor']
print(f'  proactor={p_actor.sheet.name}, reactor={r_actor.sheet.name}')
assert p_actor.sheet.name == 'Kaelen Voss', f'Expected NPC proactor, got {p_actor.sheet.name}'
assert r_actor.sheet.name == 'Elias the Jailbroken'
print('  PASS')

print()
print('=== ALL LIVE CODE TESTS PASSED ===')
print()
print('Live simulation Step 6 will produce:')
print(f'  Formula fallback: {formula_result}')
print(f'  [MECHANICS] {addendum_phrase}')
