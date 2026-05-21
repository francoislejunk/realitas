# RAG Integration Audit - All Agents

## Current Status

### ✅ CreatorAgent - GOOD
**Queries RAG for:**
- Setting context (time period, technology, culture)
- Cultural context
- Occupation context
- Actor generation parameters (names, ages, skills, endowments, status, personality)
- Location context
- Scene-specific worldbuilding

**Used in:**
- `_generate_user_actor_profile()` - UA creation
- `_generate_nua_profile()` - NUA creation
- `_generate_scene()` - Scene generation

### ✅ NarratorAgent - GOOD
**Queries RAG for:**
- Time period context (multiple methods)
- Worldbuilding (setting, technology, culture, temporal)
- Scene-specific context for narratives
- Physics/reality checks
- Dialogue style and slang
- Object/setting details for inquiries

**Used in:**
- `generate_narrative()` - Main narrative generation
- `generate_internal_voice()` - Internal thoughts
- `generate_inquiry_factual_answer()` - Answering questions
- `generate_object_inquiry_answer()` - Object details
- `_enhance_prompt_with_rag()` - General RAG enhancement
- Various specialized methods

### ❌ DeciderAgent - MISSING RAG!
**Currently has `rag_system` but NEVER uses it!**

**Should query RAG for:**
- Technology limitations (what's possible in 1970s)
- Cultural norms (how people behave)
- Location-specific details (what's available)
- Occupation-specific knowledge (what NPCs know)
- Social dynamics (how relationships work)
- Conflict escalation patterns

**Methods that need RAG:**
1. `determine_nua_proaction()` - NUA deciding what to do
2. `determine_nua_reaction()` - NUA reacting to UA
3. `determine_inua_reaction()` - INUA passive resistance

## Required Fixes

### DeciderAgent - Add RAG Integration

#### 1. Add helper method for RAG queries
```python
def _get_worldbuilding_context(self, query: str, max_tokens: int = 300) -> str:
    """Get worldbuilding context from RAG system."""
    if not self.rag_system:
        return ""
    
    try:
        context = self.rag_system.get_context_for_llm(
            query=query,
            max_tokens=max_tokens
        )
        return context if context else ""
    except Exception as e:
        self.logger.log_system(f"Error getting RAG context: {e}")
        return ""
```

#### 2. Update `determine_nua_proaction()`
Add RAG query for:
- NUA's occupation knowledge
- Available actions in current location
- Cultural/social norms
- Technology limitations

```python
# Get worldbuilding context for NUA action
worldbuilding_context = self._get_worldbuilding_context(
    query=f"{proactor.sheet.occupation} {self.scene_description[:150]} actions technology culture",
    max_tokens=400
)
```

#### 3. Update `determine_nua_reaction()`
Add RAG query for:
- Reaction patterns
- Social dynamics
- Conflict escalation
- Technology/physics constraints

```python
# Get worldbuilding context for reaction
worldbuilding_context = self._get_worldbuilding_context(
    query=f"{proactor_action_data.get('action_description', '')[:150]} reactions social_dynamics conflict culture",
    max_tokens=300
)
```

#### 4. Update `determine_inua_reaction()`
Add RAG query for:
- Object properties
- Physics/material constraints
- Technology limitations
- Environmental factors

```python
# Get worldbuilding context for INUA properties
worldbuilding_context = self._get_worldbuilding_context(
    query=f"{reactor.sheet.name} {reactor.sheet.occupation} objects technology physics materials",
    max_tokens=300
)
```

## Why This Matters

### Without RAG in DeciderAgent:
- ❌ NPCs might suggest impossible actions (e.g., "use smartphone" in 1970s)
- ❌ NPCs ignore cultural norms (e.g., too casual with authority)
- ❌ NPCs don't know location-specific details
- ❌ NPCs act inconsistently with worldbuilding
- ❌ INUAs have unrealistic properties

### With RAG in DeciderAgent:
- ✅ NPCs suggest period-appropriate actions
- ✅ NPCs follow cultural norms
- ✅ NPCs use location-specific knowledge
- ✅ NPCs act consistently with worldbuilding
- ✅ INUAs have realistic properties

## Implementation Priority

### HIGH PRIORITY:
1. **DeciderAgent RAG integration** - NPCs need worldbuilding context

### MEDIUM PRIORITY:
2. **Verify all CreatorAgent queries are comprehensive**
3. **Verify all NarratorAgent queries are comprehensive**

### LOW PRIORITY:
4. **Add category filters to RAG queries** (optional optimization)
5. **Cache frequently-used RAG contexts** (performance optimization)

## Testing Checklist

After implementing DeciderAgent RAG:

- [ ] NPC suggests action using 1970s technology (not modern)
- [ ] NPC follows cultural norms from RAG
- [ ] NPC uses location-specific knowledge
- [ ] NPC occupation matches RAG occupation descriptions
- [ ] INUA properties match RAG technology/physics
- [ ] NPC dialogue uses period-appropriate slang
- [ ] NPC reactions follow social dynamics from RAG

## Files to Modify

1. **`agents/decider_agent.py`**:
   - Add `_get_worldbuilding_context()` helper method
   - Update `determine_nua_proaction()` to query RAG
   - Update `determine_nua_reaction()` to query RAG
   - Update `determine_inua_reaction()` to query RAG

## Estimated Changes

- **Lines to add**: ~50-80 lines
- **Methods to modify**: 4 methods
- **New helper methods**: 1 method
- **Risk level**: Low (additive changes, no breaking changes)
