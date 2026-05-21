# Map Desync Investigation Report

## Issue Description

**Reported Problem:**
- **Map shows:** 1 NPC labeled "meticulous scribe"
- **Terminal shows:** 2 NPCs labeled "auditorial clerk"

This is a **display bug**, not a duplication bug. The same NPC is being displayed differently in the two systems.

---

## Root Cause

### Primary Issue: Names Not Registered in known_actors_tracker

**File:** `stranger_description_system.py:189-230`

The `KnownActorsTracker` system tracks which NPC names the UA (player) has learned. When a name is NOT in this tracker:
- **Terminal display:** Shows only the occupation (`"auditorial clerk"`)
- **Map display:** Shows the actual name (`"meticulous scribe"`)

**The Problem:** When NPCs are spawned, their names are **NEVER** automatically added to `known_actors_tracker.learn_name()`.

### Display Logic Chain:

1. **NPC Created:**
   - Name: "Meticulous Scribe"
   - Occupation: "auditorial clerk"

2. **Terminal Display** (`multi_actor_manager.py:96-100`):
   ```python
   if not name_is_known:  # ← Name not in tracker!
       if occ:
           return occ  # Returns "auditorial clerk"
       return "someone"
   ```

3. **Map Display** (`pygame_spatial_map.py:3413`):
   ```python
   name=actor_pos.actor_name,  # Uses actual name directly
   ```

4. **Result:**
   - Terminal: "auditorial clerk" (occupation)
   - Map: "Meticulous Scribe" (name)

---

## Secondary Issue: Why "2" NPCs?

The number "2" appears because:

1. In the NPC selection menu (`MAIN/redesigned_main.py:4847`):
   ```python
   print(f"  {i}. {_display_npc_name(nua)}{tag} - {occupation} ({affiliation})")
   ```

2. If there's a numbered list like:
   ```
   1. auditorial clerk - auditorial clerk (Neutral)
   2. someone else - ...
   ```

The user might be seeing position "2" in the list, OR there might actually be duplicate NPC objects.

---

## Fix Strategy

### Option 1: Auto-Register Names on Spawn (RECOMMENDED)

When NPCs are spawned, automatically register their names as "known":

**Location:** `MAIN/redesigned_main.py` - Multiple spawn points

**Implementation:**
```python
# After creating NPC
try:
    from stranger_description_system import known_actors_tracker
    if known_actors_tracker and hasattr(actor_obj, 'sheet'):
        known_actors_tracker.learn_name(actor_obj.sheet.name)
except Exception:
    pass
```

**Spawn locations to fix:**
1. Line ~6442: Population Manager spawns
2. Line ~6557: Auto-spawn from scene
3. Line ~2718: Mention system restoration
4. Line ~9155: Spatial restoration
5. Line ~10340: Test NPC creation

---

### Option 2: Sync Map Display to Use Occupation (NOT RECOMMENDED)

Change map to show occupation instead of name when unknown. **Don't do this** - it makes the map inconsistent with the simulation's physical reality.

---

### Option 3: Change Display Logic to ALWAYSShow Names (PARTIAL FIX)

Modify `multi_actor_manager.py:96-100` to always show names in certain contexts:

```python
# Option 3: Always show name in present actor lists
if not name_is_known and context == "present_list":
    return f"{nm} (occupation: {occ})"  # Show both
elif not name_is_known:
    if occ:
        return occ
    return "someone"
```

**Problem:** This breaks the intended stranger system design where you don't know names until NPCs introduce themselves.

---

## Recommended Solution

**Implement Option 1 with a configuration flag:**

### 1. Add Setting to Control Auto-Name-Learning

**File:** New or existing settings file

```python
# Gameplay Settings
AUTO_LEARN_NPC_NAMES_ON_SPAWN = True  # False for immersive "learn names" gameplay
```

### 2. Create Helper Function

**File:** `MAIN/redesigned_main.py` (or `multi_actor_manager.py`)

```python
def _register_npc_name_if_enabled(actor):
    """
    Register NPC name in known_actors_tracker if auto-learning is enabled.

    This ensures NPCs display consistently between map and terminal.
    Set AUTO_LEARN_NPC_NAMES_ON_SPAWN=False for immersive gameplay
    where you must learn NPCs names through interaction.
    """
    try:
        AUTO_LEARN = globals().get('AUTO_LEARN_NPC_NAMES_ON_SPAWN', True)
        if not AUTO_LEARN:
            return

        from stranger_description_system import known_actors_tracker
        if known_actors_tracker and hasattr(actor, 'sheet') and hasattr(actor.sheet, 'name'):
            name = str(actor.sheet.name or '').strip()
            if name:
                known_actors_tracker.learn_name(name)
    except Exception:
        pass
```

### 3. Call After Every NPC Spawn

Add `_register_npc_name_if_enabled(actor_obj)` after:
- Population Manager spawns (line ~6442)
- Auto-spawn from scene (line ~6557)
- Mention restoration (line ~2718)
- Spatial restoration (line ~9155)
- Test NPC creation (line ~10340)

---

## Expected Behavior After Fix

### With AUTO_LEARN_NPC_NAMES_ON_SPAWN = True (default):
- **Terminal:** "Meticulous Scribe - auditorial clerk (Neutral)"
- **Map:** "Meticulous Scribe"
- **Consistent display across all systems**

### With AUTO_LEARN_NPC_NAMES_ON_SPAWN = False (immersive):
- **Terminal:** "auditorial clerk" (until you learn their name)
- **Map:** "Meticulous Scribe" (map shows physical reality)
- **Immersive "learn names" gameplay**

---

## Additional Investigation Needed

To confirm there's no actual duplication, check:

1. **Count NPCs in available_npcs:**
   ```python
   print(f"[DEBUG] available_npcs count: {len(available_npcs)}")
   for i, npc in enumerate(available_npcs):
       print(f"  {i+1}. {npc.sheet.name} ({id(npc)})")
   ```

2. **Count actors in spatial context:**
   ```python
   print(f"[DEBUG] Spatial actors: {len(context.actor_positions)}")
   for actor_id in context.actor_positions:
       print(f"  - {actor_id}")
   ```

3. **Compare the two lists:**
   - If counts match → Display bug only
   - If counts differ → True duplication bug

---

## Files Involved

| File | Lines | Purpose |
|------|-------|---------|
| `stranger_description_system.py` | 189-230 | KnownActorsTracker implementation |
| `multi_actor_manager.py` | 96-100 | Display logic (shows occupation if name unknown)|
| `pygame_spatial_map.py` | 3413 | Map display (always shows name) |
| `MAIN/redesigned_main.py` | 6442, 6557, 2718, 9155 | NPC spawn locations |

---

## Status

**Issue Type:** Display inconsistency
**Severity:** Medium (confusing but not breaking)
**Fix Complexity:** Low (add registration calls)
**Estimated Time:** 30 minutes

**Next Step:** Implement Option 1 with configuration flag for maximum flexibility.
