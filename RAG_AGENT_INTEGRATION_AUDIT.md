# RAG Agent Integration Audit

## Current State

### **Agents WITH RAG Integration ✅**

| Agent | Has RAG | Uses RAG | Categories Needed | Status |
|-------|---------|----------|-------------------|--------|
| **CreatorAgent** | ✅ Yes | ✅ Yes | ALL (scene/NUA/UA generation) | ✅ Complete |
| **NarratorAgent** | ✅ Yes | ✅ Yes | CULTURE, NARRATION_STYLE_TONE | ✅ Complete |
| **DeciderAgent** | ✅ Yes | ⚠️ Minimal | BEINGS, CULTURE, OCCUPATIONS | ⚠️ Needs Enhancement |
| **ConductorAgent** | ✅ Yes | ✅ Yes | Passes to other agents | ✅ Complete |

### **Agents WITHOUT RAG Integration ❌**

| Agent | Has RAG | Should Have | Categories Needed | Priority |
|-------|---------|-------------|-------------------|----------|
| **InterpreterAgent** | ❌ No | ✅ Yes | CULTURE, NARRATION_STYLE_TONE, PLACES | 🔴 High |
| **TrackerAgent** | ❌ No | ⚠️ Maybe | NARRATION_STYLE_TONE | 🟡 Low |

---

## Detailed Analysis

### **1. CreatorAgent** ✅ COMPLETE

**Current Integration:**
- Has `self.rag_system` parameter
- Uses RAG in:
  - `_get_initial_scene_prompt()` - Scene generation
  - `_generate_nua_profile()` - NUA generation
  - `_generate_user_actor_profile()` - UA generation
  - `_get_next_scene_prompt()` - Scene transitions

**Categories Used:**
- Setting context (TEMPORAL, WORLD_STRUCTURE)
- Location context (PLACES)
- Occupation context (OCCUPATIONS)
- Cultural context (CULTURE)

**Helper Methods:**
```python
_get_rag_context(query, max_tokens, category_filter)
_get_setting_context()
_get_location_context(occupation, goals)
_get_occupation_context(occupation)
_get_cultural_context()
```

**Status:** ✅ Fully integrated, working well

---

### **2. NarratorAgent** ✅ COMPLETE

**Current Integration:**
- Has `self.rag_system` parameter
- Uses RAG in:
  - `_build_turn_narrative()` - Turn narration
  - `generate_inquiry_narrative()` - Inquiry responses

**Categories Used:**
- Cultural context (CULTURE)
- Narrative style (NARRATION_STYLE_TONE)

**Query Strategy:**
```python
# Uses action/scene context to find relevant lore
search_query = f"{proactor_narrative[:100]} {reactor_narrative[:100]}"
rag_context = self.rag_system.get_context_for_llm(query=search_query, max_tokens=300)
```

**Status:** ✅ Integrated, could be enhanced with category filters

---

### **3. DeciderAgent** ⚠️ NEEDS ENHANCEMENT

**Current Integration:**
- Has `self.rag_system` parameter
- **BUT DOESN'T USE IT!** ⚠️

**Where It Should Use RAG:**

**a) NUA Proaction (`determine_nua_proaction`)**
```python
# Should query:
# - BEINGS (character types, behavior patterns)
# - CULTURE (customs, social norms)
# - OCCUPATIONS (job-appropriate actions)
# - CONFLICT_GENERATORS (sources of tension)

# Current: No RAG usage
# Needed: Context about NUA's occupation, personality, world norms
```

**b) NUA Reaction (`determine_nua_reaction`)**
```python
# Should query:
# - BEINGS (reaction patterns)
# - CULTURE (social responses)
# - RELATIONSHIP_MATRICES (how groups interact)

# Current: No RAG usage
# Needed: Context about social dynamics, appropriate responses
```

**Recommended Categories:**
- `BEINGS` - Character behavior patterns
- `CULTURE` - Social norms, customs
- `OCCUPATIONS` - Job-appropriate actions
- `CONFLICT_GENERATORS` - Tension sources
- `RELATIONSHIP_MATRICES` - Social dynamics

**Status:** ⚠️ Has RAG but doesn't use it - HIGH PRIORITY FIX

---

### **4. InterpreterAgent** ❌ MISSING RAG

**Current State:**
- NO `rag_system` parameter
- NO RAG usage

**Where It Should Use RAG:**

**a) Action Interpretation (`interpret_action`)**
```python
# Should query:
# - CULTURE (period-appropriate actions)
# - PLACES (location-specific possibilities)
# - NARRATION_STYLE_TONE (how to describe actions)

# Example: "I use my phone"
# RAG should provide: "In 1990s, phones are landlines or pagers"
```

**b) Continuity Checking (`check_continuity`)**
```python
# Should query:
# - CIVILIZATION (technology availability)
# - CULTURE (what exists in this world)
# - PLACES (location details)

# Example: Checking if "smartphone" exists in 1990s
# RAG should provide: "No smartphones in 1990s"
```

**c) Dynamic Actor Detection**
```python
# Should query:
# - BEINGS (character types)
# - OCCUPATIONS (job types)
# - PLACES (who would be in this location)

# Example: "I talk to the bartender"
# RAG should provide: "Bartenders are service industry workers..."
```

**Recommended Categories:**
- `CULTURE` - Period-appropriate actions
- `CIVILIZATION` - Technology availability
- `PLACES` - Location details
- `NARRATION_STYLE_TONE` - Description style
- `BEINGS` - Character types
- `OCCUPATIONS` - Job types

**Status:** ❌ Missing RAG - HIGH PRIORITY ADD

---

### **5. ConductorAgent** ✅ COMPLETE

**Current Integration:**
- Has `self.rag_system` parameter
- Passes RAG to child agents:
  - `NarratorAgent(rag_system=rag_system)`
  - `DeciderAgent(..., rag_system=rag_system)`

**Status:** ✅ Correctly orchestrates RAG distribution

---

### **6. TrackerAgent** 🟡 LOW PRIORITY

**Current State:**
- NO RAG integration
- Primarily tracks state, doesn't generate content

**Potential Use:**
- Could use NARRATION_STYLE_TONE for formatting output
- Low priority - not essential

**Status:** 🟡 Optional enhancement

---

## Recommended Actions

### **Priority 1: Fix DeciderAgent** 🔴 HIGH

DeciderAgent has RAG but doesn't use it. This is the biggest gap.

**Add RAG queries to:**

1. **`determine_nua_proaction()`**
```python
def determine_nua_proaction(self, proactor, reactor, scene_description, ...):
    # Get RAG context for NUA behavior
    rag_context = ""
    if self.rag_system:
        query = f"{proactor.sheet.occupation} behavior {scene_description[:100]}"
        rag_context = self.rag_system.get_context_for_llm(
            query=query,
            max_tokens=400
        )
    
    # Include in prompt
    prompt = f"""
    {rag_context}
    
    Given the world context above, determine what {proactor.sheet.name} does...
    """
```

2. **`determine_nua_reaction()`**
```python
def determine_nua_reaction(self, proactor, reactor, ...):
    # Get RAG context for social dynamics
    rag_context = ""
    if self.rag_system:
        query = f"{reactor.sheet.occupation} reaction social norms"
        rag_context = self.rag_system.get_context_for_llm(
            query=query,
            max_tokens=300
        )
    
    # Include in prompt
```

### **Priority 2: Add RAG to InterpreterAgent** 🔴 HIGH

InterpreterAgent needs RAG for period-appropriate interpretation.

**Steps:**

1. **Add RAG parameter to `__init__`:**
```python
def __init__(self, logger, scene_description, tracker_agent=None, actor_manager=None, rag_system=None):
    # ... existing code ...
    self.rag_system = rag_system
```

2. **Update ConductorAgent to pass RAG:**
```python
self.interpreter_agent = InterpreterAgent(
    logger, 
    scene_description, 
    tracker_agent,
    rag_system=rag_system  # ← ADD THIS
)
```

3. **Add RAG queries to key methods:**

**In `interpret_action()`:**
```python
# Get period-appropriate context
rag_context = ""
if self.rag_system:
    query = f"{user_input} {scene_description[:100]} technology culture"
    rag_context = self.rag_system.get_context_for_llm(
        query=query,
        max_tokens=300
    )
```

**In `check_continuity()`:**
```python
# Get world rules context
rag_context = ""
if self.rag_system:
    query = f"technology availability {user_input}"
    rag_context = self.rag_system.get_context_for_llm(
        query=query,
        max_tokens=200
    )
```

### **Priority 3: Enhance NarratorAgent** 🟡 MEDIUM

NarratorAgent uses RAG but could use category filters for better results.

**Enhancement:**
```python
# Instead of generic query
rag_context = self.rag_system.get_context_for_llm(
    query=search_query,
    max_tokens=300
)

# Use category filter
from WORLD_BUILDER.enhanced_lore_categories import WorldbuildingCategory

rag_context = self.rag_system.get_context_for_llm(
    query=search_query,
    max_tokens=300,
    category_filter=WorldbuildingCategory.NARRATION_STYLE_TONE
)
```

---

## Category Usage Matrix

| Agent | WORLD_STRUCTURE | TEMPORAL | BEINGS | SUPERNATURAL | CIVILIZATION | FACTIONS | RELATIONSHIPS | CONFLICTS | CULTURE | NARRATION | PLACES | OCCUPATIONS |
|-------|----------------|----------|--------|--------------|--------------|----------|---------------|-----------|---------|-----------|--------|-------------|
| **CreatorAgent** | ✅ | ✅ | ✅ | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ✅ | ✅ |
| **NarratorAgent** | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | ✅ | ✅ | ⚠️ | ⚠️ |
| **DeciderAgent** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |
| **InterpreterAgent** | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ |

**Legend:**
- ✅ = Currently uses
- ⚠️ = Could use (not category-filtered)
- ❌ = Doesn't use (should use)

---

## Implementation Checklist

### **Phase 1: Critical Fixes** 🔴

- [ ] Add RAG usage to DeciderAgent.determine_nua_proaction()
- [ ] Add RAG usage to DeciderAgent.determine_nua_reaction()
- [ ] Add RAG parameter to InterpreterAgent.__init__()
- [ ] Update ConductorAgent to pass RAG to InterpreterAgent
- [ ] Add RAG usage to InterpreterAgent.interpret_action()
- [ ] Add RAG usage to InterpreterAgent.check_continuity()

### **Phase 2: Enhancements** 🟡

- [ ] Add category filters to NarratorAgent queries
- [ ] Add category filters to CreatorAgent queries
- [ ] Add RAG helper methods to DeciderAgent
- [ ] Add RAG helper methods to InterpreterAgent

### **Phase 3: Testing** ✅

- [ ] Test DeciderAgent with RAG context
- [ ] Test InterpreterAgent with RAG context
- [ ] Verify period-appropriate actions
- [ ] Verify NUA behavior matches world lore
- [ ] Test with different settings (change lore, verify adaptation)

---

## Expected Benefits

### **With DeciderAgent RAG:**
- NPCs act according to world lore
- Occupation-appropriate actions
- Period-appropriate behavior
- Social dynamics match world rules

### **With InterpreterAgent RAG:**
- Actions interpreted with period context
- Continuity checks against world lore
- Technology availability enforced
- Cultural norms respected

### **Overall:**
- Consistent worldbuilding across all agents
- Easy setting changes (just update lore)
- No anachronisms
- Authentic period feel

---

## Summary

**Current Status:**
- 2/6 agents fully integrated ✅
- 1/6 agents has RAG but doesn't use it ⚠️
- 1/6 agents missing RAG ❌
- 2/6 agents don't need RAG 🟡

**Critical Gaps:**
1. **DeciderAgent** - Has RAG, doesn't use it
2. **InterpreterAgent** - Missing RAG entirely

**Next Steps:**
1. Fix DeciderAgent RAG usage
2. Add RAG to InterpreterAgent
3. Enhance with category filters
4. Test thoroughly

Once complete, all content-generating agents will use the unified RAG system for consistent, setting-appropriate worldbuilding!
