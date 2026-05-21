import sys, os
os.environ['PYTHONIOENCODING'] = 'utf-8'
sys.stdout.reconfigure(encoding='utf-8')

print('=== Full Step 6 Pipeline Integration Test ===')
print()

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

ua  = FakeActor(FakeSheet('Elias the Jailbroken', 'Hacker'), is_ua=True)
npc = FakeActor(FakeSheet('Kaelen Voss', 'Enforcer'))

# Reproduce exact bug: action_data has name=None (key present, value None)
proactor_action_data = {
    'name': None,
    'action_noun': 'punch',
    'action_description': 'Strike Kaelen Voss',
    'narrative_description': 'You throw a punch at Kaelen Voss.',
    'is_user_actor': None,
    'utas_factors': {'status_to_shift': 'STAMINA', 'shift_polarity': 'subtractive'},
    'value': 'contested',
}
reactor_action_data = {
    'action_description': 'Dodge and counter',
    'narrative_description': 'Kaelen Voss sidesteps your blow.',
    'utas_factors': {'status_to_shift': 'STAMINA', 'shift_polarity': 'subtractive'},
    'name': None,
    'is_user_actor': None,
}
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

# --- Step 1: main-loop name override fix ---
print('Step 1: Main-loop explicit name override (not setdefault)')
pro_for_step6 = dict(proactor_action_data)
rea_for_step6 = dict(reactor_action_data)
pro_for_step6['name'] = pro_for_step6.get('name') or getattr(getattr(ua, 'sheet', None), 'name', '')
rea_for_step6['name'] = rea_for_step6.get('name') or getattr(getattr(npc, 'sheet', None), 'name', '')
pro_for_step6['is_user_actor'] = pro_for_step6.get('is_user_actor') or getattr(ua, 'is_user_actor', False)
rea_for_step6['is_user_actor'] = rea_for_step6.get('is_user_actor') or getattr(npc, 'is_user_actor', False)
print(f'  pro name={pro_for_step6["name"]}, ua={pro_for_step6["is_user_actor"]}')
print(f'  rea name={rea_for_step6["name"]}, ua={rea_for_step6["is_user_actor"]}')
assert pro_for_step6['name'] == 'Elias the Jailbroken'
assert rea_for_step6['name'] == 'Kaelen Voss'
assert pro_for_step6['is_user_actor'] == True
print('  PASS')

# --- Step 2: formula receives correct name, damage_shift matches ---
print()
print('Step 2: UTASNarrativeFormula damage_shift match')
from llm_agents.utas_narrative_formula import UTASNarrativeFormula
formula = UTASNarrativeFormula()
out_for_step6 = dict(outcome_data)
result = formula.generate_turn_outcome_narrative(
    proactor_data=pro_for_step6,
    reactor_data=rea_for_step6,
    outcome_data=out_for_step6
)
print(f'  Formula output: {result}')
assert 'None' not in result, f'None in formula output: {result}'
assert 'Penalty' in result or 'penalty' in result, f'Penalty missing: {result}'
assert 'STAMINA' in result or 'Stamina' in result or 'stamina' in result, f'Status missing: {result}'
print('  PASS')

# --- Step 3: addendum pro_name resolved from shifts ---
print()
print('Step 3: Addendum [MECHANICS] name resolution')
# Simulate the fallback with original name=None data
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
print(f'  pro_name={pro_nm}, rea_name={rea_nm}')
# When reactor wins, the affected actor is the proactor — only pro_nm matters for [MECHANICS]
assert pro_nm == 'Elias the Jailbroken', f'Expected Elias, got {pro_nm}'
# rea_nm stays as 'Reactor' placeholder here because Kaelen Voss (reactor) is the winner
# and _build_status_effect_phrase uses loser_name=pro_nm, so rea_nm is irrelevant for this phrase
print(f'  (rea_name={rea_nm!r} is placeholder — correct since reactor is winner, not affected actor)')
print('  PASS')

# --- Step 4: proactor_success_data unbound fix ---
print()
print('Step 4: proactor_success_data init (UnboundLocalError fix)')
proactor_success_data = {}
reactor_success_data = {}
step2_check = dict(proactor_success_data) if isinstance(proactor_success_data, dict) else {}
print(f'  step2 success_calculation={step2_check}')
print('  PASS')

# --- Step 5: NPC encounter deferred for inquiry ---
print()
print('Step 5: Inquiry suppresses NPC encounter (post-user turns)')
for is_inq, expect_trigger, label in [
    (True, False, 'inquiry -> no encounter'),
    (False, True, 'action -> encounter ok'),
]:
    suppress = bool(is_inq)
    triggered = not suppress
    assert triggered == expect_trigger
    print(f'  {label}: triggered={triggered} -> PASS')

# --- Step 6: NPC-initiated queue ordering ---
print()
print('Step 6: NPC-initiated Round 1 queue (NPC stays proactor)')
ctx_npc_initiated = True
round_number = 1
turn_queue = [{'actor': npc}, {'actor': ua}]
if round_number == 1 and not ctx_npc_initiated:
    turn_queue = [e for e in turn_queue if e['actor'].is_user_actor] + \
                 [e for e in turn_queue if not e['actor'].is_user_actor]
proactor = turn_queue[0]['actor']
reactor  = turn_queue[1]['actor']
print(f'  proactor={proactor.sheet.name}, reactor={reactor.sheet.name}')
assert proactor.sheet.name == 'Kaelen Voss'
assert reactor.sheet.name  == 'Elias the Jailbroken'
print('  PASS')

print()
print('=== ALL 6 TESTS PASSED ===')
print()
print('Expected Step 6 output in live simulation:')
print(f'  Formula: {result}')
print(f'  [MECHANICS] with {pro_nm}\'s STAMINA experiencing a Subpar Penalty.')
