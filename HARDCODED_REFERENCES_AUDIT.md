# Hardcoded Setting References Audit

## Overview

This document identifies all hardcoded worldbuilding references in agents that should be replaced with RAG queries to make the system truly setting-agnostic.

---

## Critical Hardcoded References (MUST FIX)

### **1. NarratorAgent - Multiple 1990s/1980s References** 🔴

**File:** `agents/narrator_agent.py`

**Line 2052-2054:**
```python
prompt = f"""{concrete_context}You are a master storyteller crafting an exploration action RESULT. The year is 1990s. You exist IN this time period.

**CRITICAL: You are IN the 1990s, not looking back at it. A 1990 Honda is just "a Honda" or "a car", NOT "vintage" or "classic". Current technology and culture are NORMAL, not "retro" or "old-fashioned".**
```

**Problem:** Hardcodes 1990s setting
**Solution:** Replace with RAG query for time period

**Recommended Fix:**
```python
# Get time period from RAG
time_period_context = ""
if self.rag_system:
    time_period_context = self.rag_system.get_context_for_llm(
        query="time period year era current setting",
        max_tokens=200,
        category_filter=WorldbuildingCategory.TEMPORAL
    )

prompt = f"""{concrete_context}You are a master storyteller crafting an exploration action RESULT.

**WORLD CONTEXT:**
{time_period_context}

**CRITICAL: You exist IN this time period, not looking back at it. Describe things as CURRENT and NORMAL, not nostalgic or dated.**
```

---

**Line 2074:**
```python
- Keep it grounded in 1980s details when relevant (equipment, environment, mood).
```

**Problem:** Hardcodes 1980s
**Solution:** Remove or make generic

**Recommended Fix:**
```python
- Keep it grounded in period-appropriate details when relevant (equipment, environment, mood).
```

---

**Line 2135:**
```python
- Keep it grounded in 1980s details when relevant (equipment, environment, mood).
```

**Same issue, same fix.**

---

**Line 2193:**
```python
- Keep it grounded in 1980s details when relevant (equipment, environment, mood).
```

**Same issue, same fix.**

---

**Line 2253:**
```python
- Keep it grounded in 1980s details when relevant (equipment, environment, mood).
```

**Same issue, same fix.**

---

**Line 2477:**
```python
- Keep it grounded and realistic (1990s setting)
```

**Problem:** Hardcodes 1990s
**Solution:** Make generic

**Recommended Fix:**
```python
- Keep it grounded and realistic (period-appropriate setting)
```

---

### **2. CreatorAgent - 1980s Reference** 🔴

**File:** `agents/creator_agent.py`

**Line 1071:**
```python
- Focus on rich environmental details that suggest the 1980s setting (varied elements like neon signs, analog technology, vintage cars, cassette players, arcade machines, VHS stores, etc. - avoid repetitive use of payphones)
```

**Problem:** Hardcodes 1980s with specific examples
**Solution:** Replace with RAG-driven context

**Recommended Fix:**
```python
- Focus on rich environmental details that match the world setting (use period-appropriate technology, culture, and atmosphere from the world context above - vary the details to avoid repetition)
```

**Note:** This prompt should already have RAG context from `_get_initial_scene_prompt()`, so just reference it generically.

---

## Medium Priority (SHOULD FIX)

### **3. Test Files - 1980s/1990s References** 🟡

**File:** `test_character_generation.py`

**Lines 3, 26, 56:**
```python
"""
Test script to verify character generation with modern 1980s names
"""

user_profile = creator._generate_user_actor_profile("Test context for 1980s character")

nua_profile = creator._generate_nua_profile("Test context for 1980s NPC", "A busy street in downtown")
```

**Problem:** Test files assume 1980s setting
**Solution:** Update test descriptions or make setting-agnostic

**Recommended Fix:**
```python
"""
Test script to verify character generation with period-appropriate names
"""

user_profile = creator._generate_user_actor_profile("Test context for character")

nua_profile = creator._generate_nua_profile("Test context for NPC", "A busy street in downtown")
```

---

**File:** `test_complete_simulation.py`

**Lines 3-4, 40, 136-142, 202-207:**

Multiple references to "1980s" in test descriptions and validation.

**Recommended Fix:**
Update test to be setting-agnostic or parameterized by setting.

---

### **4. Vessel Selection System** 🟡

**File:** `vessel_selection_system.py`

**Line 5:**
```python
which character they want to play. All are normal 1990s humans with different
```

**Problem:** Hardcodes 1990s
**Solution:** Make generic or query RAG

**Recommended Fix:**
```python
which character they want to play. All are period-appropriate characters with different
```

---

## Low Priority (OPTIONAL)

### **5. Comments and Docstrings** 🟢

**File:** `WORLD_BUILDER/lore_rag_system.py`

**Lines 5, 324-336:**
```python
- 1990s cultural context and history

def initialize_default_lore(rag_system: LoreRAGSystem):
    """Initialize the RAG system with basic 1990s lore"""
    
    # 1990s Culture
    rag_system.add_lore_document(
        title="1990s Music Scene",
        ...
```

**Problem:** Comments reference 1990s
**Solution:** These are in the OLD basic RAG system which should be deprecated

**Recommended Action:**
- Mark `lore_rag_system.py` as DEPRECATED
- Use `worldbuilding_rag_system.py` and `universal_lore.py` instead

---

### **6. Universal Lore File** 🟢

**File:** `WORLD_BUILDER/universal_lore.py`

**Multiple lines:** Contains 1990s content

**Problem:** This is EXPECTED - it's the lore data file
**Solution:** No fix needed - this is where setting content belongs!

**Note:** To change settings, users edit this file. This is correct behavior.

---

## Summary of Required Changes

### **Critical Fixes (Must Do):**

| File | Lines | Issue | Fix Complexity |
|------|-------|-------|----------------|
| narrator_agent.py | 2052-2054 | Hardcoded "1990s" in prompt | Medium - Add RAG query |
| narrator_agent.py | 2074, 2135, 2193, 2253 | "1980s details" references | Easy - Replace text |
| narrator_agent.py | 2477 | "1990s setting" reference | Easy - Replace text |
| creator_agent.py | 1071 | "1980s setting" with examples | Easy - Replace text |

### **Medium Priority:**

| File | Lines | Issue | Fix Complexity |
|------|-------|-------|----------------|
| test_character_generation.py | 3, 26, 56 | Test assumes 1980s | Easy - Update text |
| test_complete_simulation.py | Multiple | Test validates 1980s | Medium - Update tests |
| vessel_selection_system.py | 5 | "1990s humans" reference | Easy - Replace text |

### **No Fix Needed:**

| File | Reason |
|------|--------|
| universal_lore.py | This is the lore DATA file - 1990s content is correct here |
| lore_rag_system.py | Should be deprecated in favor of worldbuilding_rag_system.py |

---

## Implementation Plan

### **Phase 1: NarratorAgent (Critical)** 🔴

**Step 1: Add RAG query for time period**

In `generate_exploration_action_result()` method (around line 2052):

```python
# Before building prompt, get time period context
time_period_context = ""
if self.rag_system:
    try:
        time_period_context = self.rag_system.get_context_for_llm(
            query="time period year era current setting",
            max_tokens=200
        )
        if time_period_context:
            time_period_context = f"\n**WORLD CONTEXT:**\n{time_period_context}\n"
    except Exception as e:
        # Silently fail, continue without context
        pass

# Then in prompt:
prompt = f"""{concrete_context}You are a master storyteller crafting an exploration action RESULT.

{time_period_context}

**CRITICAL: You exist IN this time period, not looking back at it. Describe things as CURRENT and NORMAL, not nostalgic or dated.**
```

**Step 2: Replace all "1980s"/"1990s" text references**

Find and replace:
- "1980s details" → "period-appropriate details"
- "1990s setting" → "period-appropriate setting"
- "grounded in 1980s" → "grounded in the world setting"

**Locations:**
- Line 2074
- Line 2135
- Line 2193
- Line 2253
- Line 2477

**Step 3: Test**

```bash
cd MAIN
python redesigned_main.py
```

Generate scenes and verify they still reference appropriate period details.

---

### **Phase 2: CreatorAgent (Critical)** 🔴

**File:** `agents/creator_agent.py`

**Line 1071:**

Replace:
```python
- Focus on rich environmental details that suggest the 1980s setting (varied elements like neon signs, analog technology, vintage cars, cassette players, arcade machines, VHS stores, etc. - avoid repetitive use of payphones)
```

With:
```python
- Focus on rich environmental details that match the world setting from the context above (use period-appropriate technology, culture, and atmosphere - vary the details to avoid repetition)
```

**Step 2: Test**

Generate new scenes and verify they use appropriate details from RAG context.

---

### **Phase 3: Test Files (Medium Priority)** 🟡

**Update test descriptions to be setting-agnostic:**

1. `test_character_generation.py` - Remove "1980s" from descriptions
2. `test_complete_simulation.py` - Make setting validation generic
3. `vessel_selection_system.py` - Change "1990s humans" to "period-appropriate characters"

---

## Verification Checklist

After implementing fixes:

- [ ] Search codebase for "1980" - should only appear in lore files
- [ ] Search codebase for "1990" - should only appear in lore files
- [ ] Search for "grunge", "hip-hop", "pager" - should only be in lore files
- [ ] Generate scene - verify period details come from RAG
- [ ] Change lore to different setting - verify scenes adapt
- [ ] All agents use generic language, not hardcoded periods

---

## Testing Different Settings

After fixes, test setting-agnosticism:

**Test 1: Change to Cyberpunk**

Edit `universal_lore.py`:
```python
SETTING_TIME_PERIOD = """
Cyberpunk 2077 - Megacorporations rule...
"""
```

Run simulation, verify:
- Scenes mention cyberware, not cassettes
- NPCs act according to cyberpunk lore
- No 1990s references appear

**Test 2: Change to Medieval Fantasy**

Edit `universal_lore.py`:
```python
SETTING_TIME_PERIOD = """
Medieval Kingdom - Age of knights and magic...
"""
```

Run simulation, verify:
- Scenes mention castles, not cars
- NPCs act according to medieval lore
- No modern technology references

---

## Expected Benefits

### **After Removing Hardcoded References:**

✅ **True Setting-Agnosticism**
- Change setting by editing one file (universal_lore.py)
- No code changes needed
- All agents adapt automatically

✅ **Consistent Worldbuilding**
- All period details come from RAG
- No conflicting references
- Single source of truth

✅ **Easy Maintenance**
- Update lore, not code
- No scattered references to fix
- Clear separation of data and logic

✅ **Multiple Settings Support**
- Switch between settings easily
- Support parallel campaigns
- Community-created settings work

---

## Summary

**Total Hardcoded References Found:** 11

**Critical (Must Fix):** 7
- NarratorAgent: 6 references
- CreatorAgent: 1 reference

**Medium (Should Fix):** 4
- Test files: 3 references
- Vessel system: 1 reference

**No Fix Needed:** 2
- universal_lore.py (correct - it's the data file)
- lore_rag_system.py (deprecated)

**Estimated Time:** 1-2 hours to fix all critical references

**Priority Order:**
1. Fix NarratorAgent (most critical, most references)
2. Fix CreatorAgent (one line, easy fix)
3. Update test files (optional, for completeness)
4. Verify with different settings

Once complete, the system will be **100% setting-agnostic** with all worldbuilding coming from the RAG system!
