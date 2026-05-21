# RAG Integration Implementation Plan

## Overview

This document provides step-by-step instructions to integrate RAG into all necessary agents.

---

## Phase 1: Fix DeciderAgent (CRITICAL)

### **Problem**
DeciderAgent has `self.rag_system` but never uses it!

### **Solution**

**File:** `agents/decider_agent.py`

**Step 1: Add RAG helper method**

Add this method after `__init__`:

```python
def _get_rag_context_for_nua(self, nua_name: str, occupation: str, context_type: str = "behavior") -> str:
    """
    Get RAG context for NUA decision-making.
    
    Args:
        nua_name: Name of the NUA
        occupation: NUA's occupation
        context_type: Type of context needed ("behavior", "reaction", "social")
    
    Returns:
        Formatted RAG context string
    """
    if not self.rag_system:
        return ""
    
    try:
        # Build query based on context type
        if context_type == "behavior":
            query = f"{occupation} behavior actions typical work"
        elif context_type == "reaction":
            query = f"{occupation} reaction response social norms"
        elif context_type == "social":
            query = f"{occupation} social dynamics relationships"
        else:
            query = f"{occupation} {context_type}"
        
        context = self.rag_system.get_context_for_llm(
            query=query,
            max_tokens=400
        )
        
        if context:
            return f"\n**WORLD CONTEXT (use this to inform {nua_name}'s behavior):**\n{context}\n"
        return ""
    
    except Exception as e:
        self.logger.log_system(f"Warning: Could not retrieve RAG context for {nua_name}: {e}")
        return ""
```

**Step 2: Update `determine_nua_proaction()`**

Find this method (around line 100-200) and add RAG context to the prompt:

```python
def determine_nua_proaction(self, proactor, reactor, scene_description, ...):
    # ... existing code ...
    
    # GET RAG CONTEXT - ADD THIS
    rag_context = self._get_rag_context_for_nua(
        nua_name=proactor.sheet.name,
        occupation=proactor.sheet.occupation,
        context_type="behavior"
    )
    
    # ... existing code to build prompt ...
    
    prompt = f"""
    {rag_context}  # ← ADD THIS LINE
    
    You are determining what {proactor.sheet.name} does in this situation.
    
    # ... rest of existing prompt ...
    """
```

**Step 3: Update `determine_nua_reaction()`**

Find this method and add RAG context:

```python
def determine_nua_reaction(self, proactor, reactor, ...):
    # ... existing code ...
    
    # GET RAG CONTEXT - ADD THIS
    rag_context = self._get_rag_context_for_nua(
        nua_name=reactor.sheet.name,
        occupation=reactor.sheet.occupation,
        context_type="reaction"
    )
    
    # ... existing code to build prompt ...
    
    prompt = f"""
    {rag_context}  # ← ADD THIS LINE
    
    You are determining how {reactor.sheet.name} reacts to {proactor.sheet.name}'s action.
    
    # ... rest of existing prompt ...
    """
```

**Step 4: Test**

```bash
cd MAIN
python redesigned_main.py
```

Create a character, interact with NPCs, verify they act according to world lore.

---

## Phase 2: Add RAG to InterpreterAgent (CRITICAL)

### **Problem**
InterpreterAgent has NO RAG integration at all!

### **Solution**

**File:** `agents/interpreter_agent.py`

**Step 1: Add RAG parameter to `__init__`**

Find the `__init__` method (around line 30) and add `rag_system` parameter:

```python
# OLD:
def __init__(self, logger: 'UTASLogger', scene_description: str, tracker_agent=None, actor_manager=None):

# NEW:
def __init__(self, logger: 'UTASLogger', scene_description: str, tracker_agent=None, actor_manager=None, rag_system=None):
    self.logger = UTASLogger()
    self.scene_description = scene_description
    self.tracker_agent = tracker_agent
    self.rag_system = rag_system  # ← ADD THIS LINE
    # ... rest of existing code ...
```

**Step 2: Add RAG helper method**

Add this method after `__init__`:

```python
def _get_rag_context_for_interpretation(self, user_input: str, context_type: str = "action") -> str:
    """
    Get RAG context for action interpretation.
    
    Args:
        user_input: The user's action
        context_type: Type of context ("action", "continuity", "technology")
    
    Returns:
        Formatted RAG context string
    """
    if not self.rag_system:
        return ""
    
    try:
        # Build query based on context type
        if context_type == "action":
            query = f"{user_input} culture period-appropriate actions"
        elif context_type == "continuity":
            query = f"{user_input} technology availability what exists"
        elif context_type == "technology":
            query = f"technology {user_input} communication computing"
        else:
            query = f"{user_input} {context_type}"
        
        context = self.rag_system.get_context_for_llm(
            query=query,
            max_tokens=300
        )
        
        if context:
            return f"\n**WORLD CONTEXT:**\n{context}\n"
        return ""
    
    except Exception as e:
        self.logger.log_system(f"Warning: Could not retrieve RAG context: {e}")
        return ""
```

**Step 3: Update `interpret_action()`**

Find the `interpret_action()` method and add RAG context:

```python
def interpret_action(self, user_input: str, actor, ...):
    # ... existing code ...
    
    # GET RAG CONTEXT - ADD THIS
    rag_context = self._get_rag_context_for_interpretation(
        user_input=user_input,
        context_type="action"
    )
    
    # ... existing code to build prompt ...
    
    prompt = f"""
    {rag_context}  # ← ADD THIS LINE
    
    Interpret the following action: "{user_input}"
    
    # ... rest of existing prompt ...
    """
```

**Step 4: Update `check_continuity()`**

Find the `check_continuity()` method and add RAG context:

```python
def check_continuity(self, user_input: str, actor, ...):
    # ... existing code ...
    
    # GET RAG CONTEXT - ADD THIS
    rag_context = self._get_rag_context_for_interpretation(
        user_input=user_input,
        context_type="continuity"
    )
    
    # ... existing code to build prompt ...
    
    prompt = f"""
    {rag_context}  # ← ADD THIS LINE
    
    Check if this action is possible: "{user_input}"
    
    # ... rest of existing prompt ...
    """
```

**Step 5: Update ConductorAgent**

**File:** `agents/conductor_agent.py`

Find where InterpreterAgent is initialized (around line 39):

```python
# OLD:
self.interpreter_agent = InterpreterAgent(logger, scene_description, tracker_agent)

# NEW:
self.interpreter_agent = InterpreterAgent(
    logger, 
    scene_description, 
    tracker_agent, 
    actor_manager=actor_manager,
    rag_system=rag_system  # ← ADD THIS
)
```

**Step 6: Update main.py**

**File:** `MAIN/redesigned_main.py`

Find where ConductorAgent is created and verify it receives RAG:

```python
# Should already have this (verify):
conductor = ConductorAgent(
    logger=logger,
    scene_description=scene_description,
    recovery_integrator=recovery_integrator,
    tracker_agent=tracker_agent,
    actor_manager=actor_manager,
    rag_system=rag_system  # ← Verify this exists
)
```

**Step 7: Test**

```bash
cd MAIN
python redesigned_main.py
```

Try actions like:
- "I use my smartphone" (should fail in 1990s)
- "I call on my pager" (should work in 1990s)
- "I check social media" (should fail in 1990s)

---

## Phase 3: Enhance with Category Filters (OPTIONAL)

### **NarratorAgent Enhancement**

**File:** `agents/narrator_agent.py`

Add import at top:

```python
from WORLD_BUILDER.enhanced_lore_categories import WorldbuildingCategory
```

Update RAG queries to use category filters:

```python
# In _build_turn_narrative():
rag_context = self.rag_system.get_context_for_llm(
    query=search_query,
    max_tokens=300,
    category_filter=WorldbuildingCategory.NARRATION_STYLE_TONE  # ← ADD THIS
)

# In generate_inquiry_narrative():
rag_context = self.rag_system.get_context_for_llm(
    query=search_query,
    max_tokens=300,
    category_filter=WorldbuildingCategory.CULTURE  # ← ADD THIS
)
```

### **CreatorAgent Enhancement**

**File:** `agents/creator_agent.py`

Add import at top:

```python
from WORLD_BUILDER.enhanced_lore_categories import WorldbuildingCategory
```

Update helper methods to use category filters:

```python
def _get_setting_context(self) -> str:
    """Get time period and setting context from RAG"""
    return self._get_rag_context(
        query="time period setting year era technology culture",
        max_tokens=400,
        category_filter=WorldbuildingCategory.TEMPORAL  # ← ADD THIS
    )

def _get_location_context(self, occupation: str, goals: list) -> str:
    """Get location-appropriate context from RAG"""
    query = f"locations places {occupation} {' '.join(goals[:2])}"
    return self._get_rag_context(
        query=query,
        max_tokens=400,
        category_filter=WorldbuildingCategory.PLACES  # ← ADD THIS
    )

def _get_occupation_context(self, occupation: str) -> str:
    """Get occupation-specific context from RAG"""
    return self._get_rag_context(
        query=f"occupation work job {occupation}",
        max_tokens=300,
        category_filter=WorldbuildingCategory.OCCUPATIONS  # ← ADD THIS
    )

def _get_cultural_context(self) -> str:
    """Get cultural and atmospheric context from RAG"""
    return self._get_rag_context(
        query="culture atmosphere music fashion social issues",
        max_tokens=400,
        category_filter=WorldbuildingCategory.CULTURE  # ← ADD THIS
    )
```

---

## Testing Checklist

### **DeciderAgent RAG Testing**

- [ ] Create NUA with occupation (e.g., "Bartender")
- [ ] Verify NUA actions match occupation (serves drinks, cleans bar)
- [ ] Verify NUA reactions match world lore (1990s behavior)
- [ ] Check console for RAG context retrieval messages

### **InterpreterAgent RAG Testing**

- [ ] Try anachronistic action: "I use my smartphone"
  - Expected: Continuity failure or reinterpretation to pager/landline
- [ ] Try period-appropriate action: "I use the payphone"
  - Expected: Success, mentions quarters, phone booth
- [ ] Try technology check: "I send an email"
  - Expected: Mentions dial-up, AOL, slow connection
- [ ] Check console for RAG context retrieval messages

### **Integration Testing**

- [ ] Generate new scene - verify period details
- [ ] Create NUA - verify occupation-appropriate behavior
- [ ] Interact with NUA - verify reactions match world
- [ ] Try various actions - verify continuity enforcement
- [ ] Change lore (edit universal_lore.py) - verify adaptation

---

## Rollback Plan

If issues occur:

### **Rollback DeciderAgent**

Remove RAG context from prompts:
```python
# Comment out or remove:
# rag_context = self._get_rag_context_for_nua(...)

# Remove from prompt:
prompt = f"""
# {rag_context}  ← Comment this out
...
"""
```

### **Rollback InterpreterAgent**

Remove RAG parameter:
```python
# In __init__:
# self.rag_system = rag_system  ← Comment out

# In ConductorAgent:
self.interpreter_agent = InterpreterAgent(
    logger, 
    scene_description, 
    tracker_agent
    # rag_system=rag_system  ← Comment out
)
```

---

## Success Criteria

✅ **DeciderAgent:**
- NPCs act according to their occupation
- NPC reactions match world lore
- No anachronistic NPC behavior

✅ **InterpreterAgent:**
- Anachronistic actions caught/reinterpreted
- Period-appropriate actions succeed
- Technology availability enforced

✅ **Overall:**
- All agents use unified RAG
- Consistent worldbuilding across simulation
- Easy setting changes (just update lore)

---

## Timeline

**Phase 1 (Critical):**
- DeciderAgent: 30 minutes
- InterpreterAgent: 45 minutes
- Testing: 30 minutes
- **Total: ~2 hours**

**Phase 2 (Enhancement):**
- Category filters: 30 minutes
- Testing: 15 minutes
- **Total: ~45 minutes**

**Grand Total: ~3 hours** for complete RAG integration across all agents.

---

## Summary

**Current State:**
- CreatorAgent: ✅ Has RAG, uses it well
- NarratorAgent: ✅ Has RAG, uses it
- DeciderAgent: ⚠️ Has RAG, doesn't use it
- InterpreterAgent: ❌ No RAG
- ConductorAgent: ✅ Passes RAG to others

**After Implementation:**
- All content-generating agents use RAG
- Consistent worldbuilding
- Period-appropriate behavior
- Easy setting changes

**Next Step:** Start with Phase 1 (DeciderAgent and InterpreterAgent)
