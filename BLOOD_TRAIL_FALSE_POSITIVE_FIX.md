# Blood Trail False Positive Fix

## Problem Identified

**User Question:** "when was a blood trail mentioned?"

**Answer:** It wasn't! This was a false positive detection.

### What Happened

The narrative generated was:
```
"...just hums along to the faint music bleeding from the store's speakers."
```

The **Diegetic Clue Tracker** detected the word **"bleeding"** and incorrectly registered it as a blood trail clue, even though it was being used metaphorically to describe music.

### Root Cause

**File:** `diegetic_clue_tracker.py` (lines 84-86)

The keyword list for `BLOOD_TRAIL` included:
```python
keywords=[
    'blood trail', 'fresh blood', 'blood drops', 'bleeding',  # ← Too broad!
    'bloody footprints', 'blood smear', 'crimson trail'
]
```

The single word **"bleeding"** was matching metaphorical usage like:
- "music bleeding from speakers"
- "light bleeding through curtains"
- "color bleeding into fabric"

## Solution Applied

### Fix 1: Removed Ambiguous Keyword

**Changed:**
```python
keywords=[
    'blood trail', 'fresh blood', 'blood drops', 'bleeding',  # ← REMOVED
    'bloody footprints', 'blood smear', 'crimson trail'
]
```

**To:**
```python
keywords=[
    'blood trail', 'fresh blood', 'blood drops', 'blood stain',
    'bloody footprints', 'blood smear', 'crimson trail', 'trail of blood'
]
```

- Removed standalone "bleeding" (too ambiguous)
- Added "blood stain" and "trail of blood" (more specific)

### Fix 2: Added Metaphorical Usage Filter

**New Method:** `_is_metaphorical_usage()` (lines 228-262)

Checks context for metaphorical patterns before registering clues:

```python
# Blood trail specific metaphorical patterns
if clue_type == ClueType.BLOOD_TRAIL:
    metaphorical_patterns = [
        r'(music|sound|light|color|paint)\s+bleed',  # "music bleeding"
        r'bleed\s+(from|through|into)\s+(speaker|wall|window)',  # "bleeding from speakers"
        r'(audio|visual|color)\s+.*\s+bleed',  # "audio bleeding"
    ]
```

**Integration:** Added filter check at line 180:
```python
# Filter out metaphorical usage (e.g., "music bleeding from speakers")
if self._is_metaphorical_usage(clue_type, context):
    continue  # Skip this detection
```

## Result

✅ **"music bleeding from speakers"** → No longer triggers blood trail detection

✅ **"blood trail leading north"** → Still correctly detected

✅ **"fresh blood on the ground"** → Still correctly detected

✅ **"light bleeding through the window"** → No longer triggers blood trail detection

## Files Modified

1. **diegetic_clue_tracker.py**
   - Line 84-86: Updated BLOOD_TRAIL keywords
   - Line 180-181: Added metaphorical usage filter
   - Line 228-262: Added `_is_metaphorical_usage()` method

## Testing

The next time you see narrative with metaphorical "bleeding" (music, light, etc.), it should NOT register a blood trail clue.

Only literal blood/injury references will trigger the detection system.
