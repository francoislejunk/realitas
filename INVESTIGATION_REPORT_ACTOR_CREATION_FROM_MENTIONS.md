# Investigation Report: Actor Creation from Mentions

## Issue Summary
Need to verify if mentioned actors are properly created/spawned and if narrative context captures all actor appearances.

## Current System Analysis

### ✅ SYSTEM EXISTS: SceneNPCParser
**Location:** `scene_npc_parser.py`

The codebase **already has** a comprehensive system for detecting and spawning NPCs mentioned in scene descriptions:

#### Key Components:

1. **extract_npcs_from_scene()** (lines 20-134)
   - Uses LLM to intelligently parse scene descriptions
   - Detects physically present actors
   - Filters out:
     - Actors mentioned in messages/calls
     - Actors from memories
     - Actors who are elsewhere
     - Background atmosphere

2. **auto_spawn_scene_npcs()** (lines 319-588)
   - Main integration function
   - Called in multiple places in redesigned_main.py
   - Features:
     - Deduplication (name match, role match)
     - Generic description matching
     - Relationship context inference
     - Spatial map integration
     - Auto-memory creation

### ✅ Current Usage Points

The system is called in **redesigned_main.py** at:
- **Line 6526**: Initial location seed
- **Line 6718**: After location generation
- **Line 11985**: Success narration context
- **Line 14145**: Action responses
- **Line 14429**: After action processing

### 🔍 Potential Gaps

#### 1. **Dialogue Mentions**
When an NPC mentions another actor in dialogue:
```
Bartender: "Marcus was just here asking about you."
```

**Current behavior:** May not spawn Marcus because:
- The scene description may not include this dialogue
- The NPC parser only sees the scene_description parameter
- Dialogue happens AFTER scene generation

**Recommendation:** Pass recent dialogue/narrative to auto_spawn when needed.

#### 2. **User Action Mentions**
When the user mentions someone:
```
User: "I go to Marcus's apartment"
User: "I call Linda on the phone"
```

**Current behavior:**
- May not spawn if Marcus/Linda aren't in current scene
- System correctly filters out "mentioned but not present" actors
- **This is likely correct behavior** (don't spawn everyone mentioned)

#### 3. **Narrative Context Integration**
The narrative_context_manager tracks events but may not trigger NPC spawning from its context.

**Recommendation:** Consider periodic NPC extraction from accumulated narrative context.

## Strengths of Current System

1. ✅ **Smart Detection**: Uses LLM to understand physical presence vs mentions
2. ✅ **Deduplication**: Multiple strategies to avoid duplicate spawns
3. ✅ **Role-based matching**: Matches generic descriptions to existing NPCs
4. ✅ **Relationship inference**: Automatically determines NPC relationship to UA
5. ✅ **Spatial integration**: Adds spawned NPCs to map
6. ✅ **Memory creation**: Auto-creates first-meeting memories
7. ✅ **Multiple trigger points**: Called at strategic moments

## Recommended Enhancements

### Enhancement 1: Dialogue-Triggered Spawning
**Priority: Medium**

When NPCs mention other actors in dialogue, consider spawning them if they become relevant:

```python
# After NPC dialogue is generated
if "mentioned_actors" in dialogue_data:
    for mentioned_actor in dialogue_data["mentioned_actors"]:
        # Check if they should be spawned (e.g., "here", "approaching", etc.)
        if should_spawn_mentioned_actor(mentioned_actor, context):
            spawn_from_mention(mentioned_actor)
```

### Enhancement 2: Narrative Context Scanning
**Priority: Low**

Periodically scan accumulated narrative for emerging actors:

```python
# Every N turns or at scene transitions
narrative_text = narrative_context_manager.get_recent_context()
auto_spawn_scene_npcs(narrative_text, ...)
```

### Enhancement 3: Actor Mention Tracking (→ Task #5)
**Priority: High - Links to Missing System: Mention System**

Track all actor mentions with metadata:
- Who mentioned them
- In what context (present, elsewhere, past)
- Last known location
- Relationship to speakers

This feeds into the **Mention System** task.

## Testing Recommendations

Test these scenarios to verify current behavior:

### ✅ Should Work Already:
1. Scene description: "Marcus stands by the bar" → Should spawn Marcus
2. Narrator: "A waitress approaches" → Should spawn generic waitress
3. Multiple mentions of same NPC → Should  deduplicate correctly

### ❓ May Need Enhancement:
1. NPC dialogue: "Marcus just left" → Should this spawn Marcus? (probably not)
2. NPC dialogue: "Here comes Marcus now" → Should spawn Marcus (yes!)
3. User:  "I call Marcus" → Should this pull Marcus into scene? (context-dependent)

## Files Involved
- **scene_npc_parser.py** - Core parsing logic
- **MAIN/redesigned_main.py** - Integration points (multiple locations)
- **narrative_context_manager.py** - Context tracking (potential enhancement)

## Connection to Other Tasks

### Task #5: Mention System
The Mention System should:
- Use SceneNPCParser's detection as a foundation
- Add tracking of ALL mentions (not just spawnable ones)
- Record location context for mentioned actors
- Enable queries like "Where was Marcus last mentioned?"

### Task #6: Continuous Map Population
Should leverage SceneNPCParser for:
- Spawning appropriate NPCs as UA explores
- Populating locations dynamically
- Maintaining NPC presence consistency

## Status
**INVESTIGATION COMPLETE** - System is robust but could be enhanced

## Verdict
The automatic actor creation system is **well-implemented** with strong detection, deduplication, and integration. The main opportunities are:

1. **Dialogue-triggered spawning** (when NPCs mention others who are "arriving")
2. **Better mention tracking** (feeds into Task #5: Mention System)
3. **Narrative context scanning** (optional, lower priority)

### Recommendation:
**NO IMMEDIATE FIXES NEEDED** - Current system is solid. Focus on:
1. Testing edge cases (dialogue mentions)
2. Implementing Task #5 (Mention System) to enhance tracking
3. Documenting expected behavior for different mention types
