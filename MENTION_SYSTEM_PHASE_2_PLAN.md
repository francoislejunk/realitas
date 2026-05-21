# Mention System Phase 2: Integration Plan

**Status:** PLANNING
**Phase 1 Complete:** ✅ 28 tests passing
**Phase 2 Goal:** Integrate mention tracking throughout simulation

---

## Overview

Phase 1 built the core infrastructure (mention_system.py with 28 tests). Phase 2 will integrate the Mention System with all major simulation agents to automatically track actor mentions throughout gameplay.

## Integration Strategy

Similar to Fact System Phase 2, we'll integrate in phases with each agent:
1. **CreatorAgent** - Scene generation and NPC creation
2. **ConductorAgent** - NPC dialogue
3. **NarratorAgent** - Narrative descriptions
4. **InterpreterAgent** - User actions/input
5. **SceneNPCParser** - Auto-spawn integration

Each integration will:
- Record mentions automatically during normal operation
- Query mention history to inform decisions
- Validate actions against mention state
- Have comprehensive test coverage

---

## Phase 2.1: CreatorAgent Integration

**Goal:** Track actor mentions during scene generation and NPC creation

### Recording Mentions
- When `generate_nua()` creates NPC → record PHYSICAL_PRESENCE mention
- When initial scene describes actors → record mentions from scene text
- When NPC has location specified → record with appropriate confidence

### Querying History
- Before generating scene → query existing actor mentions
- Inject mention context into prompts (similar to fact context)
- Prevent contradictions: "Marcus was last seen at Studio, don't spawn at Bar"

### Integration Points
- `agents/creator_agent.py` line 2465: `generate_nua()`
- `agents/creator_agent.py` line 3091: `_get_initial_scene_prompt()`
- After NPC creation → record mention
- Scene generation → extract and record mentions

### Tests
- Test NPC creation records mention
- Test scene generation considers mention history
- Test mention context injection
- Test spawn validation prevents contradictions

---

## Phase 2.2: ConductorAgent Integration

**Goal:** Extract and record mentions from NPC dialogue

### Recording Mentions
- Parse NPC dialogue for actor mentions
- Heuristic extraction patterns:
  - "I saw [Actor] at [Location]" → ELSEWHERE_CURRENT or ELSEWHERE_PAST
  - "[Actor] is at [Location]" → ELSEWHERE_CURRENT
  - "[Actor] was at [Location]" → ELSEWHERE_PAST
  - "I heard [Actor] is..." → RUMOR
  - "[Actor] left for [Location]" → DEPARTING mention

### Querying History
- Before generating dialogue → query mention history
- NPCs should reference known mentions ("As I said, Marcus is at the bar")
- Prevent contradictions in dialogue

### Integration Points
- `agents/conductor_agent.py` - dialogue generation
- After NPC speaks → extract mentions from dialogue
- Validate dialogue doesn't contradict high-confidence mentions

### Tests
- Test dialogue mention extraction
- Test various mention patterns
- Test validation prevents contradictions
- Test multiple mentions from single dialogue

---

## Phase 2.3: NarratorAgent Integration

**Goal:** Track mentions from narrative descriptions

### Recording Mentions
- When narrator describes actor location → PHYSICAL_PRESENCE mention
- When narrator describes movement → ARRIVING/DEPARTING mentions
- When narrator references past events → MEMORY mentions
- Internal thoughts about actors → INTERNAL_THOUGHT source

### Querying History
- Check mention history for context
- Enrich narration with mention-based details
- Maintain consistency with known locations

### Integration Points
- `agents/narrator_agent.py` - narrative generation
- After narration → extract location mentions
- Record movement mentions (arriving/departing)

### Tests
- Test narration records appropriate mentions
- Test mention source tracking (NARRATIVE)
- Test movement descriptions create proper mention types

---

## Phase 2.4: InterpreterAgent Integration

**Goal:** Track mentions from user input

### Recording Mentions
- User says "I go to Marcus" → query Marcus location
- User asks "Where is Linda?" → query mention system
- User actions reference actors → record as USER_INPUT source
- User describes seeing actors → high-confidence mention

### Querying History
- Answer location queries from mention system
- Validate user actions against mention state
- Warn if user tries to interact with actor elsewhere

### Integration Points
- `agents/interpreter_agent.py` line 2887: `detect_inquiry_or_action()`
- Extract mentions from user input
- Query system for location inquiries
- Record user mentions with USER_INPUT source

### Tests
- Test user input mention extraction
- Test location queries
- Test validation warnings
- Test USER_INPUT source tracking

---

## Phase 2.5: SceneNPCParser Integration

**Goal:** Use mention system for intelligent auto-spawning

### Recording Mentions
- When auto-spawn extracts NPCs → record mentions
- Scene descriptions become SCENE_DESCRIPTION source
- Track all mentioned actors from scene text

### Querying for Spawning
- **KEY CHANGE:** Before spawning NPC, check `can_spawn_actor()`
- Use `get_spawn_candidates(location)` for smart spawning
- Respect mention history (don't spawn if elsewhere)
- Query last known location for returning NPCs

### Integration Points
- `scene_npc_parser.py` line 20: `extract_npcs_from_scene()`
- `scene_npc_parser.py` line 319: `auto_spawn_scene_npcs()`
- Before spawn → validate with mention system
- After extraction → record all mentions

### Tests
- Test spawn validation respects mention history
- Test spawn candidates filtering
- Test mention recording from scene text
- Test prevents spawning actors elsewhere

---

## Phase 2.6: Main Loop Integration

**Goal:** Connect mention system to main simulation loop

### Recording Mentions
- When UA enters location → update presence
- When NPCs spawn → record PHYSICAL_PRESENCE
- When NPCs despawn → record DEPARTING
- Scene transitions → track movement

### Querying for UI/Debug
- Display last known locations in debug UI
- Show mention history for actors
- Validate encounter participants

### Integration Points
- `MAIN/redesigned_main.py` line 6518: NPC spawn
- `MAIN/redesigned_main.py` line 12356: Encounter mode
- After spawn → `mark_actor_spawned()`
- After despawn → `mark_actor_despawned()`
- Scene change → record UA movement

### Tests
- Test spawn tracking
- Test movement tracking
- Test encounter validation
- Test state consistency

---

## Implementation Order

**Recommended sequence (easiest → most complex):**

1. **Phase 2.1: CreatorAgent** (EASIEST)
   - Single, clear integration point (`generate_nua`)
   - Similar to Fact System integration
   - Good "hello world" test

2. **Phase 2.5: SceneNPCParser** (MEDIUM)
   - Already well-structured code
   - Clear integration points
   - High-value (prevents spawn contradictions)

3. **Phase 2.2: ConductorAgent** (MEDIUM)
   - Heuristic extraction (similar to Fact System)
   - Dialogue parsing already familiar
   - Moderate complexity

4. **Phase 2.4: InterpreterAgent** (MEDIUM)
   - User input parsing
   - Query integration for "where is X?"
   - Already integrated with Fact System

5. **Phase 2.3: NarratorAgent** (MEDIUM-HARD)
   - Narrative text extraction
   - Movement detection needed

6. **Phase 2.6: Main Loop** (HARDEST)
   - Large, complex file
   - Multiple integration points
   - Requires understanding full simulation flow

---

## Testing Strategy

Each phase gets its own test file:
- `test_mention_creator_integration.py`
- `test_mention_conductor_integration.py`
- `test_mention_narrator_integration.py`
- `test_mention_interpreter_integration.py`
- `test_mention_parser_integration.py`
- `test_mention_main_loop_integration.py`

Target: 10-15 tests per integration (60-90 tests total for Phase 2)

---

## Success Criteria

✅ All agents automatically record mentions
✅ Spawn validation prevents contradictions
✅ Location queries work in real-time
✅ User can ask "Where is X?" and get answer
✅ No performance degradation
✅ All tests passing (Phase 1: 28 + Phase 2: ~70 = ~98 total)
✅ Graceful degradation if mention system unavailable

---

## Expected Benefits

### 1. Intelligent NPC Spawning
- Auto-spawn respects mention history
- No more "Marcus at bar AND studio" contradictions
- NPCs can "return" to locations realistically

### 2. Location Tracking
- "Where is Marcus?" → instant answer from mention system
- Last seen information available to all agents
- Movement history tracked automatically

### 3. Narrative Consistency
- Agents reference mention history in generation
- NPCs remember who they saw where
- User questions answered from mention data

### 4. Foundation for Advanced Features
- Enables "search for X" functionality
- Supports "summon X" with location validation
- Powers continuous map population (Task #6)

---

## Comparison with Fact System Phase 2

| Aspect | Fact System | Mention System |
|--------|-------------|----------------|
| Integrations | 5 (Creator, KeyMem, Conductor, DetailTracker, Interpreter) | 6 (Creator, Conductor, Narrator, Interpreter, Parser, MainLoop) |
| Extraction | Heuristic (occupation, relationship) | Heuristic + LLM (location mentions) |
| Validation | Contradiction warnings | Spawn blocking |
| Primary Use | What is true | Where actors are |
| Tests (Phase 2) | 50 additional | Est. 60-70 additional |

---

## Next Steps

1. ✅ Create this plan
2. ⏳ Start with Phase 2.1: CreatorAgent integration
3. ⏳ Create test file and implement integration
4. ⏳ Continue through phases 2.2-2.6
5. ⏳ Create Phase 2 completion summary

---

## Notes

- Similar to Fact System, use heuristic extraction for performance
- Consider LLM extraction only if heuristics insufficient
- Maintain backward compatibility (mention system optional)
- Focus on "happy path" first, edge cases later
- Each integration should be independently valuable

**Let's begin with Phase 2.1: CreatorAgent Integration!**
