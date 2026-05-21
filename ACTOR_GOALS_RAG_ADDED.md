# Actor Goals Added to RAG System

## What Was Done

Added **Actor Goals and Motivations** section to the worldbuilding RAG system in `universal_lore_restructured.py`.

## Changes Made

### 1. Added ACTOR_GOALS Content Section
**File:** `WORLD_BUILDER/universal_lore_restructured.py` lines 432-496

New content section defining 8 goal types:
- **SURVIVAL GOALS** - Maintain status, secure needs, avoid trouble
- **INVESTIGATION GOALS** - Uncover truth, understand anomalies
- **ADVANCEMENT GOALS** - Gain promotion, build network, learn skills
- **RELATIONSHIP GOALS** - Reconnect with family, protect loved ones
- **ESCAPE GOALS** - Leave sector, break free from system
- **REVENGE GOALS** - Get back at betrayers, expose corruption
- **PRESERVATION GOALS** - Keep secrets, protect vulnerable
- **UNDERSTANDING GOALS** - Figure out mechanics, decode patterns

Also includes goal complexity levels:
- Short-term (immediate needs)
- Medium-term (scene/session objectives)
- Long-term (character arc goals)
- Hidden (secret agendas)

### 2. Added RAG Entry
**File:** `WORLD_BUILDER/universal_lore_restructured.py` lines 969-975

```python
entries.append({
    "title": "Actor Goals and Motivations",
    "content": ACTOR_GOALS,
    "category": WorldbuildingCategory.BEINGS,
    "tags": ["character_generation", "actor_generation", "goals", "motivations", "objectives", "desires"],
    "importance": 10
})
```

### 3. Updated Header Documentation
**File:** `WORLD_BUILDER/universal_lore_restructured.py` line 31

Updated to reflect new section:
```
- ACTOR_GENERATION: Names, ages, skills, endowments, status, personality traits, goals
```

## How Agents Will Use This

### Internal Voice Generation
When generating internal voice, narrator can query actor goals:

```python
# In narrator_agent.py generate_internal_voice()
if self.rag_system:
    goals_context = self.rag_system.search(
        query=f"{ua_name} goals motivations objectives",
        categories=[WorldbuildingCategory.BEINGS],
        max_results=2
    )
```

Internal voice can then reference goals:
```
💭 We need to figure out those margin notes. That's the key to understanding what's happening to us.
```

### Actor Creation
When creating actors, CreatorAgent can query appropriate goals:

```python
# Get goal examples for actor type
goal_examples = rag_system.search(
    query="investigation goals curious idealistic",
    categories=[WorldbuildingCategory.BEINGS]
)
```

### NUA Decision Making
DeciderAgent can reference actor goals when determining actions:

```python
# Get NUA's goals
nua_goals = rag_system.search(
    query=f"{nua_name} goals objectives",
    categories=[WorldbuildingCategory.BEINGS]
)
```

## Goal Types Explained

### SURVIVAL GOALS (Universal)
Every actor has some survival goals:
- Maintain current status level
- Secure basic needs (food, shelter, safety)
- Avoid dangerous classifications
- Keep job and income stable
- Stay off authority's radar

### INVESTIGATION GOALS (Curious Actors)
For actors driven by curiosity:
- Understand temporal anomalies
- Uncover truth about disappeared persons
- Discover what happened to mentor/family
- Learn real purpose of systems
- Find evidence of conspiracy

### ADVANCEMENT GOALS (Ambitious Actors)
For actors seeking to rise:
- Gain promotion to higher position
- Acquire better living quarters
- Build network of useful contacts
- Learn valuable skills
- Earn favor with superiors

### RELATIONSHIP GOALS (Social Actors)
For actors focused on connections:
- Reconnect with estranged family
- Find romantic partner
- Protect loved ones from system
- Build trust with specific person
- Repair damaged relationship

### ESCAPE GOALS (Desperate Actors)
For actors seeking freedom:
- Leave current sector or district
- Break free from oppressive job
- Escape surveillance or monitoring
- Find way out of the system
- Reach rumored safe zones

### REVENGE GOALS (Wronged Actors)
For actors seeking justice:
- Get back at person who betrayed them
- Expose corrupt official
- Sabotage system that hurt them
- Prove innocence or clear name
- Make someone pay for past injustice

### PRESERVATION GOALS (Protective Actors)
For actors guarding something:
- Keep dangerous secret hidden
- Protect vulnerable person or group
- Maintain cover identity
- Preserve important information
- Prevent specific outcome

### UNDERSTANDING GOALS (Analytical Actors)
For actors seeking knowledge:
- Figure out how temporal mechanics work
- Understand own Echo-Adjacent classification
- Learn why events keep repeating
- Decode mysterious messages
- Map true structure of power

## Integration with Existing Systems

### With Key Memories
Goals inform which memories are important:
- Investigation goal → Memories about mentor's disappearance are critical
- Relationship goal → Memories about estranged family matter
- Understanding goal → Memories about anomalies are key

### With Goal/Task Manager
Two-tier system:
- **RAG Goals** - Deep, long-term motivations
- **Task Manager** - Immediate, actionable objectives

Example:
- RAG: "Understand why handwriting appears before touching files"
- Task: "Examine the margin notes in File #77-K"

### With Internal Voice
Goals provide context for thoughts:
- Actor with investigation goal thinks analytically about clues
- Actor with survival goal worries about consequences
- Actor with revenge goal thinks about opportunities

## Query Examples

### Get All Actor Goals
```python
goals = rag_system.search(
    query="actor goals motivations objectives",
    categories=[WorldbuildingCategory.BEINGS],
    max_results=5
)
```

### Get Specific Goal Type
```python
investigation_goals = rag_system.search(
    query="investigation goals curious uncover truth",
    categories=[WorldbuildingCategory.BEINGS],
    max_results=3
)
```

### Get Goals for Actor Type
```python
ambitious_goals = rag_system.search(
    query="advancement goals ambitious promotion",
    categories=[WorldbuildingCategory.BEINGS],
    max_results=2
)
```

## Next Steps

### To Load Into RAG:
```bash
cd WORLD_BUILDER
python universal_lore_restructured.py
```

This will rebuild the RAG database with the new actor goals section.

### To Verify:
After loading, agents can query:
```python
results = rag_system.search(
    query="actor goals",
    categories=[WorldbuildingCategory.BEINGS]
)
print(f"Found {len(results)} goal-related documents")
```

## Benefits

✅ **Consistent Goals** - All agents reference same goal types
✅ **Actor-Appropriate** - Goals match personality and situation
✅ **Multiple Levels** - Short, medium, long-term goals
✅ **Hidden Agendas** - Support for secret motivations
✅ **Integration Ready** - Works with memories, tasks, internal voice
✅ **Queryable** - Easy to find relevant goals for any actor
✅ **Persistent** - Stored in RAG, available across sessions

## Result

Actors now have:
- ✅ 8 distinct goal types to choose from
- ✅ Examples for each goal type
- ✅ Complexity levels (short/medium/long/hidden)
- ✅ Integration with personality traits
- ✅ RAG storage for agent access
- ✅ Proper terminology (Actor, not NPC/character)
