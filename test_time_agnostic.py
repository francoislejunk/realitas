"""
Test: Time-agnostic fixes - all hardcoded era references removed from prompts
"""
import sys, os, re, codecs
if sys.platform == 'win32':
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("TIME-AGNOSTIC PROMPTS VERIFICATION")
print("=" * 70)

checks = [
    # (filepath, pattern, should_exist, label)
    ('agents/narrator_agent.py',
     r'default to a generic contemporary setting',
     False, 'narrator: contemporary fallback removed'),

    ('agents/narrator_agent.py',
     r'never assume or invent a period',
     True,  'narrator: time-agnostic replacement present'),

    ('agents/narrator_agent.py',
     r'1993',
     False, 'narrator: hardcoded year 1993 removed'),

    ('agents/narrator_agent.py',
     r'Honda Civic',
     False, 'narrator: Honda Civic removed'),

    ('agents/narrator_agent.py',
     r'Motorola pager',
     False, 'narrator: Motorola pager removed'),

    ('agents/narrator_agent.py',
     r're\.sub.*19\\\\d\{2\}.*20\\\\d\{2\}',
     False, 'narrator: year-strip regex removed'),

    ('agents/creator_agent.py',
     r'default to a generic contemporary setting',
     False, 'creator: contemporary fallback removed'),

    ('agents/storyteller_agent.py',
     r'use generic contemporary setting',
     False, 'storyteller: contemporary fallback removed'),

    ('agents/storyteller_agent.py',
     r'use only details already established',
     True,  'storyteller: neutral fallback present'),

    ('agents/decider_agent.py',
     r'If setting is 1960s',
     False, 'decider: 1960s timeline block removed'),

    ('agents/decider_agent.py',
     r'If setting is 1980s',
     False, 'decider: 1980s timeline block removed'),

    ('agents/decider_agent.py',
     r'WORLD SETTING CONTEXT provided above',
     True,  'decider: RAG-based instruction present'),

    ('agents/internal_voice_creator_agent.py',
     r'NEVER use modern metaphors \(algorithms',
     False, 'internal_voice: modern metaphors ban removed'),

    ('agents/internal_voice_creator_agent.py',
     r'contradict the worldbuilding context',
     True,  'internal_voice: worldbuilding-relative rule present'),

    ('MAIN/redesigned_main.py',
     r"'television': 'notice board'",
     False, 'main: TV->notice board removed'),

    ('MAIN/redesigned_main.py',
     r"'broadcast': 'announcement'",
     False, 'main: broadcast->announcement removed'),
]

passed = 0
failed = 0
for filepath, pattern, should_exist, label in checks:
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        found = bool(re.search(pattern, content))
        ok = found == should_exist
        state = 'found' if found else 'absent'
        mark = 'PASS' if ok else 'FAIL'
        print(f"  [{mark}] {label} ({state})")
        if ok:
            passed += 1
        else:
            failed += 1
    except Exception as e:
        print(f"  [ERR ] {label} - {e}")
        failed += 1

print()
print("=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed")
if failed == 0:
    print("All time-agnostic fixes verified")
else:
    print("Some checks failed - review output above")
print("=" * 70)
