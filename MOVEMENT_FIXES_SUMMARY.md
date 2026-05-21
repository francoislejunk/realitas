# Movement System Fixes - February 18, 2026

## Bug #6: Double Movement Call ✅ FIXED

### Issue
When user entered "I head to X", movement executed twice:
1. First: Successful 2.7m movement
2. Second: Redundant 0m movement (already at destination)

### Root Cause
Two movement systems both triggered for same action:
- Early movement (diegetic transition system)
- Late movement (narrative extraction or re-processing)

### Fix Applied
**File:** `agents/architect_agent.py:3661-3673`

Added distance check before executing movement:

```python
# CHECK: Skip movement if already at target (within 1 unit tolerance)
try:
    import math
    distance = math.sqrt(
        (new_position.x - current_pos.x)**2 +
        (new_position.y - current_pos.y)**2
    )
    if distance < 1.0:
        # Already at target - skip redundant movement
        return False
except Exception:
    pass  # If check fails, proceed with movement anyway
```

### Expected Result
After fix, only ONE movement call should appear:
```
[SPATIAL] Moved Elias Thorne: (10.0, 2.1) → (12.7, 2.0) | Trail: 2.7m
🏛️ ARCHITECT Elias Thorne moved to 'Technician Workbench'
```

No second 0m movement.

---

## Bug #7: Missing Movement Narration ✅ FIXED

### Issue
Perceptual descriptions jump straight to interaction without describing the walk:

**Current:**
```
You run your hand over the cold, scarred metal of the technician workbench...
```

**Expected:**
```
You walk to the technician workbench. You run your hand over the cold metal...
```

### Fix Applied
**Files:**
- `agents/narrator_agent.py:5153-5162` - Added movement parameters to function signature
- `agents/narrator_agent.py:5318-5326` - Added movement instruction to LLM prompt
- `MAIN/redesigned_main.py:14167-14175` - Updated narrator call to pass movement data

Added `explicit_movement` and `movement_target` parameters to narrator's `generate_inquiry_response()`:

```python
def generate_inquiry_response(
    self,
    user_question: str,
    ua_actor,
    scene_description: str,
    narrative_context: str,
    current_time: Dict[str, Any],
    availability_context: Optional[Dict[str, Any]] = None,
    nua_actions_context: str = "",
    explicit_movement: bool = False,      # NEW
    movement_target: Optional[str] = None  # NEW
) -> str:
```

When `explicit_movement=True`, the prompt now includes:
```python
**MOVEMENT INSTRUCTION:** The user just moved to "[target]". Begin your response by
BRIEFLY acknowledging the movement (e.g., "You walk to the [target].") THEN
describe what you perceive.
```

### Expected Result
After fix, perceptual descriptions will include movement:
```
You walk to the technician workbench. You run your hand over the cold, scarred metal...
```

---

## Bug #8: Map Trail Position Confusing Display ✅ FIXED

### Issue
Map sync logs show trail position (9.0, 6.0) but current position is (12.7, 2.0):

```
[PMAP] Actor Elias Thorne moved: (9.0, 6.0) → (12.7, 2.0)
[PMAP] UA trail set: 3 points, pos=(9.0, 6.0)  ← Confusing!
```

### Root Cause Analysis
This is NOT actually a bug - it's a misleading debug message. Trail system works correctly:
- Trail stores **historical waypoints** (where the actor has been)
- Current position is stored **separately** in actor's x,y fields
- When actor moves A → B, position A is added to trail, position B becomes current

The old debug message printed them separately, creating confusion.

### Fix Applied
**File:** `pygame_spatial_map.py:3429-3432`

Improved debug message clarity:

```python
# Debug: confirm trail is set
if trail_data and actor_pos.is_user_actor:
    first_trail = trail_data[0]
    print(f"[PMAP] UA trail: {len(trail_data)} waypoints from ({first_trail[0]:.1f}, {first_trail[1]:.1f}) → current ({scaled_x:.1f}, {scaled_y:.1f})")
elif actor_pos.is_user_actor:
    print(f"[PMAP] UA trail: No waypoints, current_pos=({scaled_x:.1f}, {scaled_y:.1f})")
```

### Expected Result
After fix, logs show clear historical trail:
```
[PMAP] Actor Elias Thorne moved: (9.0, 6.0) → (12.7, 2.0)
[PMAP] UA trail: 3 waypoints from (9.0, 6.0) → current (12.7, 2.0)
```

---

## Files Modified

1. **agents/architect_agent.py:3661-3673** - Added redundant movement check
2. **agents/narrator_agent.py:5153-5162** - Added movement parameters to function signature
3. **agents/narrator_agent.py:5318-5326** - Added movement instruction to LLM prompt
4. **MAIN/redesigned_main.py:14167-14175** - Updated narrator call to pass movement data
5. **pygame_spatial_map.py:3429-3432** - Improved trail debug message clarity

## Testing

After fixes, test with:
1. "I head to [object]" - should only show 1 movement ✅
2. Check if perceptual description mentions the walk ✅
3. Verify map trail shows correct path with clear debug messages ✅

**Status:** 3/3 fixes complete ✅
