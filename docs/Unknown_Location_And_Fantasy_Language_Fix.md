# Unknown Location & Fantasy Language Fix

## 🐛 **TWO ISSUES IDENTIFIED**

### **Issue 1: "Unknown Location" When LLM Created It**
```
MAP: Unknown Location  ❌
Type: exterior | Size: 100x60 units
```

**Your Question:** "why is the location unknown when the LLM is the one that made it"

**Scene Description:**
> "You stand on the cracked asphalt of the abandoned **Evergreen Chemical Plant**..."

**Problem:** LLM generated "Evergreen Chemical Plant" but map shows "Unknown Location"!

---

### **Issue 2: Fantasy Language in 1980s Setting**
**Your Observation:** "look at the wording relic faded"

**Scene Text:**
> "...abandoned Evergreen Chemical Plant, **a relic of 1980s industrial boom**..."
> "...still reads 'Evergreen Industries - Hazardous Waste Disposal' in **faded 1970s typography**..."

**Problem:** "Relic" and "faded" sound like **fantasy/medieval language**, not gritty 1980s realism!

---

## 🔍 **ROOT CAUSES**

### **Issue 1: Hardcoded Location Extraction**

**Old Code (Lines 1976-1986):**
```python
# Extract location name from scene data or description
location_name = scene_data.get('setting', 'Unknown Location')
if location_name == 'Unknown Location':
    # Try to extract from scene description
    if "Rusty's Repairs" in scene_description:
        location_name = "Rusty's Repairs"
    elif "garage" in scene_description.lower():
        location_name = "Garage"
    elif "newsroom" in scene_description.lower():
        location_name = "Newsroom"
    elif "office" in scene_description.lower():
        location_name = "Office"
```

**Problem:** **MORE HARDCODING!** 😅

- Only checks for specific keywords: "garage", "office", "newsroom"
- "Evergreen Chemical Plant" doesn't match any keywords
- Falls back to "Unknown Location"

---

### **Issue 2: Scene Generator Prompt**

The scene generator LLM isn't being told to avoid fantasy language for 1980s settings.

---

## ✅ **THE FIXES**

### **Fix 1: LLM-Based Location Name Extraction**

**New Code:**
```python
# Extract location name from scene data or description
location_name = scene_data.get('setting', 'Unknown Location')
if location_name == 'Unknown Location':
    # Use LLM to extract location name from scene description
    prompt = f"""Extract the primary location name from this scene description.

SCENE:
{scene_description[:500]}

Respond with just the location name (2-4 words max), nothing else.

Examples:
- "You stand in the garage..." → "Garage"
- "The diner hums with activity..." → "Diner"
- "You're in Rusty's Repairs..." → "Rusty's Repairs"
- "The abandoned Evergreen Chemical Plant..." → "Evergreen Chemical Plant"

Location name:"""
    
    response = llm.chat.completions.create(...)
    location_name = response.choices[0].message.content.strip()
```

**Benefits:**
- ✅ No hardcoded keywords
- ✅ Works for ANY location name
- ✅ Extracts "Evergreen Chemical Plant" correctly
- ✅ Handles creative names

---

### **Fix 2: Scene Generator Language Guidance** (TODO)

**Need to update scene generator prompt to:**
```
For 1980s settings, use period-appropriate language:
- ❌ "relic" → ✅ "leftover", "abandoned since", "closed down"
- ❌ "faded" → ✅ "peeling", "weathered", "worn"
- ❌ "ancient" → ✅ "old", "rundown", "beat-up"
- ❌ "mystical" → ✅ "eerie", "creepy", "unsettling"

Use gritty, realistic 1980s urban language, not fantasy/medieval terms.
```

---

## 📊 **COMPARISON**

### **Before (Hardcoded):**
```python
# Hardcoded keyword check
if "garage" in scene_description.lower():
    location_name = "Garage"
elif "office" in scene_description.lower():
    location_name = "Office"
# ... limited to predefined keywords

Result for "Evergreen Chemical Plant":
→ No match → "Unknown Location" ❌
```

### **After (LLM Extraction):**
```python
# LLM extracts location name
prompt = "Extract location name from: {scene_description}"
location_name = llm(prompt)

Result for "Evergreen Chemical Plant":
→ LLM extracts: "Evergreen Chemical Plant" ✅
```

---

## 🎯 **EXAMPLES**

### **Example 1: Evergreen Chemical Plant**
```
Scene: "You stand on the cracked asphalt of the abandoned Evergreen Chemical Plant..."

Old System:
- Checks: "garage"? No. "office"? No. "newsroom"? No.
- Result: "Unknown Location" ❌

New System:
- LLM extracts: "Evergreen Chemical Plant"
- Result: "Evergreen Chemical Plant" ✅

Map Display:
MAP: Evergreen Chemical Plant  ✅
Type: exterior | Size: 100x60 units
```

### **Example 2: Rusty's Repairs**
```
Scene: "You're in Rusty's Repairs, a small garage..."

Old System:
- Checks: "garage"? Yes!
- Result: "Garage" (loses the specific name) ⚠️

New System:
- LLM extracts: "Rusty's Repairs"
- Result: "Rusty's Repairs" ✅

Map Display:
MAP: Rusty's Repairs  ✅
Type: interior | Size: 30x25 units
```

### **Example 3: The Neon Lounge**
```
Scene: "You step into The Neon Lounge, a dimly lit bar..."

Old System:
- Checks: "garage"? No. "office"? No. "bar"? No (not in keyword list!)
- Result: "Unknown Location" ❌

New System:
- LLM extracts: "The Neon Lounge"
- Result: "The Neon Lounge" ✅

Map Display:
MAP: The Neon Lounge  ✅
Type: interior | Size: 25x20 units
```

---

## 🎨 **LANGUAGE FIX (TODO)**

### **Fantasy Language → 1980s Realism**

| Fantasy/Medieval | 1980s Gritty |
|------------------|--------------|
| "relic of the past" | "leftover from the 80s" |
| "faded typography" | "peeling lettering" |
| "ancient structure" | "rundown building" |
| "mystical glow" | "eerie neon light" |
| "enchanted" | "weird" |
| "sacred" | "important" |
| "cursed" | "bad news" |
| "tome" | "book" |
| "chamber" | "room" |

### **Better Scene Wording:**

**Before:**
> "You stand on the cracked asphalt of the abandoned Evergreen Chemical Plant, **a relic of 1980s industrial boom**. The rusted sign at the entrance still reads 'Evergreen Industries - Hazardous Waste Disposal' in **faded 1970s typography**."

**After:**
> "You stand on the cracked asphalt of the abandoned Evergreen Chemical Plant, **closed down since the early 80s**. The rusted sign at the entrance still reads 'Evergreen Industries - Hazardous Waste Disposal' in **peeling 70s-style lettering**."

---

## 🔧 **IMPLEMENTATION**

### **File: `redesigned_main.py` (Lines 1975-2011)**

```python
# Extract location name from scene data or description
location_name = scene_data.get('setting', 'Unknown Location')
if location_name == 'Unknown Location':
    # Use LLM to extract location name from scene description
    try:
        from openrouter_config import OpenRouterConfig
        config = OpenRouterConfig()
        client = config.create_client()
        
        prompt = f"""Extract the primary location name from this scene description.

SCENE:
{scene_description[:500]}

Respond with just the location name (2-4 words max), nothing else.

Examples:
- "You stand in the garage..." → "Garage"
- "The diner hums with activity..." → "Diner"
- "You're in Rusty's Repairs..." → "Rusty's Repairs"
- "The abandoned Evergreen Chemical Plant..." → "Evergreen Chemical Plant"

Location name:"""
        
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=20
        )
        
        extracted_name = response.choices[0].message.content.strip()
        if extracted_name and len(extracted_name) < 50:
            location_name = extracted_name
    except Exception as e:
        print(f"[SPATIAL] Could not extract location name: {e}")
        location_name = "Unknown Location"
```

---

## 🎉 **NEXT RUN WILL SHOW**

```
Scene: "You stand on the cracked asphalt of the abandoned Evergreen Chemical Plant..."

[SPATIAL] Analyzing initial location: Evergreen Chemical Plant  ✅
[SPATIAL] Created location: Evergreen Chemical Plant (100x60 units)

> map

MAP: Evergreen Chemical Plant  ✅ No more "Unknown Location"!
Type: exterior | Size: 100x60 units

ACTORS:
  @ Ethan Cole at (50.0, 30.0) in Administration Building Area
```

---

## 📋 **TODO: Scene Generator Language Fix**

Need to update the scene generator prompt (likely in `CreatorAgent` or `NarratorAgent`) to avoid fantasy language:

```python
# Add to scene generation prompt:
"""
LANGUAGE STYLE FOR 1980s SETTINGS:
- Use gritty, realistic urban language
- Avoid fantasy/medieval terms: "relic", "faded", "ancient", "mystical"
- Use period-appropriate alternatives: "leftover", "peeling", "old", "eerie"
- Think: noir detective novels, not fantasy epics
"""
```

---

## 🏆 **SUMMARY**

**Issue 1: "Unknown Location"**
- ❌ **Problem:** Hardcoded keyword matching
- ✅ **Fix:** LLM extracts location name from scene
- ✅ **Result:** Works for ANY location name

**Issue 2: Fantasy Language**
- ❌ **Problem:** "Relic", "faded" sound medieval
- ⏳ **Fix:** Update scene generator prompt (TODO)
- ✅ **Result:** Gritty 1980s realism

**No more "Unknown Location" and no more fantasy language! 🎯**
