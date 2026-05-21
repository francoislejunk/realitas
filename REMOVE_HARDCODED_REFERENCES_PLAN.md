# Quick Fix Plan: Remove Hardcoded Setting References

## Summary

Found **11 hardcoded references** to 1980s/1990s that should be removed for true setting-agnosticism.

---

## Quick Fixes (Copy-Paste Ready)

### **Fix 1: NarratorAgent Line 2074**

**Find:**
```python
- Keep it grounded in 1980s details when relevant (equipment, environment, mood).
```

**Replace with:**
```python
- Keep it grounded in period-appropriate details when relevant (equipment, environment, mood).
```

---

### **Fix 2: NarratorAgent Line 2135**

**Find:**
```python
- Keep it grounded in 1980s details when relevant (equipment, environment, mood).
```

**Replace with:**
```python
- Keep it grounded in period-appropriate details when relevant (equipment, environment, mood).
```

---

### **Fix 3: NarratorAgent Line 2193**

**Find:**
```python
- Keep it grounded in 1980s details when relevant (equipment, environment, mood).
```

**Replace with:**
```python
- Keep it grounded in period-appropriate details when relevant (equipment, environment, mood).
```

---

### **Fix 4: NarratorAgent Line 2253**

**Find:**
```python
- Keep it grounded in 1980s details when relevant (equipment, environment, mood).
```

**Replace with:**
```python
- Keep it grounded in period-appropriate details when relevant (equipment, environment, mood).
```

---

### **Fix 5: NarratorAgent Line 2477**

**Find:**
```python
- Keep it grounded and realistic (1990s setting)
```

**Replace with:**
```python
- Keep it grounded and realistic (period-appropriate setting)
```

---

### **Fix 6: NarratorAgent Lines 2052-2054 (REQUIRES CODE CHANGE)**

**Find:**
```python
prompt = f"""{concrete_context}You are a master storyteller crafting an exploration action RESULT. The year is 1990s. You exist IN this time period.

**CRITICAL: You are IN the 1990s, not looking back at it. A 1990 Honda is just "a Honda" or "a car", NOT "vintage" or "classic". Current technology and culture are NORMAL, not "retro" or "old-fashioned".**
```

**Replace with:**
```python
# Get time period context from RAG
time_period_context = ""
if self.rag_system:
    try:
        time_period_context = self.rag_system.get_context_for_llm(
            query="time period year era current setting",
            max_tokens=200
        )
        if time_period_context:
            time_period_context = f"\n**WORLD CONTEXT:**\n{time_period_context}\n"
    except Exception:
        pass

prompt = f"""{concrete_context}You are a master storyteller crafting an exploration action RESULT.

{time_period_context}

**CRITICAL: You exist IN this time period, not looking back at it. Describe current technology and culture as NORMAL, not nostalgic, vintage, or dated.**
```

---

### **Fix 7: CreatorAgent Line 1071**

**Find:**
```python
- Focus on rich environmental details that suggest the 1980s setting (varied elements like neon signs, analog technology, vintage cars, cassette players, arcade machines, VHS stores, etc. - avoid repetitive use of payphones)
```

**Replace with:**
```python
- Focus on rich environmental details that match the world setting from the context above (use period-appropriate technology, culture, and atmosphere - vary the details to avoid repetition)
```

---

## Optional Fixes (Test Files)

### **Fix 8: test_character_generation.py Line 3**

**Find:**
```python
Test script to verify character generation with modern 1980s names
```

**Replace with:**
```python
Test script to verify character generation with period-appropriate names
```

---

### **Fix 9: test_character_generation.py Line 26**

**Find:**
```python
user_profile = creator._generate_user_actor_profile("Test context for 1980s character")
```

**Replace with:**
```python
user_profile = creator._generate_user_actor_profile("Test context for character")
```

---

### **Fix 10: test_character_generation.py Line 56**

**Find:**
```python
nua_profile = creator._generate_nua_profile("Test context for 1980s NPC", "A busy street in downtown")
```

**Replace with:**
```python
nua_profile = creator._generate_nua_profile("Test context for NPC", "A busy street in downtown")
```

---

### **Fix 11: vessel_selection_system.py Line 5**

**Find:**
```python
which character they want to play. All are normal 1990s humans with different
```

**Replace with:**
```python
which character they want to play. All are period-appropriate characters with different
```

---

## Implementation Order

1. ✅ **NarratorAgent** (6 fixes) - Most critical
2. ✅ **CreatorAgent** (1 fix) - Easy
3. 🟡 **Test files** (4 fixes) - Optional

---

## Verification Commands

After making changes:

```bash
# Search for remaining hardcoded references
cd "c:\Users\darre\OneDrive\Desktop\Realitas Neo"

# Should only find references in lore files
grep -r "1980s" --include="*.py" --exclude-dir="WORLD_BUILDER"
grep -r "1990s" --include="*.py" --exclude-dir="WORLD_BUILDER"

# Test the simulation
cd MAIN
python redesigned_main.py
```

---

## Testing Different Settings

After fixes, test setting-agnosticism:

```bash
# 1. Edit WORLD_BUILDER/universal_lore.py
# 2. Change SETTING_TIME_PERIOD to different era
# 3. Run: python universal_lore.py
# 4. Run: python MAIN/redesigned_main.py
# 5. Verify scenes match new setting
```

---

## Checklist

- [ ] Fix NarratorAgent line 2074
- [ ] Fix NarratorAgent line 2135
- [ ] Fix NarratorAgent line 2193
- [ ] Fix NarratorAgent line 2253
- [ ] Fix NarratorAgent line 2477
- [ ] Fix NarratorAgent lines 2052-2054 (code change)
- [ ] Fix CreatorAgent line 1071
- [ ] (Optional) Fix test files
- [ ] Run verification grep commands
- [ ] Test with current 1990s setting
- [ ] Test with different setting (cyberpunk/fantasy)
- [ ] Verify no hardcoded references remain

---

## Expected Result

✅ **100% Setting-Agnostic System**
- All worldbuilding from RAG
- No hardcoded time periods
- Easy setting changes
- Consistent across all agents
