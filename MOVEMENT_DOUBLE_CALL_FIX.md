# Movement Double Call Fix

## Problem

When user enters "I head to X", movement executes **twice**:
1. First call: Successful movement (2.7m)
2. Second call: Redundant 0m movement (already at destination)

## Root Cause

Two movement systems trigger for the same action:

1. **Early Movement (Line ~11230)**: Diegetic transition system
   - Detects local scene feature (obstacle/zone)
   - Executes movement immediately

2. **Late Movement (somewhere in given_action processing)**:
   - Movement extraction from generated narrative or user input re-processing
   - Tries to move again but actor is already there

## Simple Fix

Add spatial position check in `move_actor_on_map()` function in `agents/architect_agent.py`:

**Before moving, check if actor is already at target position. If yes, skip movement and return False.**

This prevents redundant 0m moves without needing to track flags across complex code paths.

### Implementation:

**File:** `agents/architect_agent.py`

In `move_actor_on_map()` function, add check:

```python
def move_actor_on_map(actor_name, movement_target, narrative, session_id=None):
    try:
        from spatial_context_system import get_spatial_manager
        spatial = get_spatial_manager(session_id)
        context = spatial.get_current_context()

        # Get current position
        actor_id = f"actor_{actor_name.lower().replace(' ', '_')}"
        current_pos = context.actor_positions.get(actor_id)

        if not current_pos:
            return False

        # Find target position by checking obstacles/zones
        target_pos = _find_target_position(movement_target, context)

        if not target_pos:
            return False

        # CHECK: If already at target (within 1 unit), skip movement
        distance = math.sqrt(
            (target_pos.x - current_pos.position.x)**2 +
            (target_pos.y - current_pos.position.y)**2
        )

        if distance < 1.0:  # Already at target
            return False  # Skip redundant movement

        # Proceed with movement...
        spatial.move_actor(actor_id, target_pos)
        return True
    except Exception:
        return False
```

## Alternative: Flag-Based Fix

If simple position check doesn't work, use flag approach:

1. After first movement at line 11237, set flag:
   ```python
   if 'explicit_movement_data' not in locals():
       explicit_movement_data = {}
   explicit_movement_data['movement_completed'] = True
   ```

2. Before second movement attempt, check flag:
   ```python
   if explicit_movement_data.get('movement_completed'):
       continue  # Skip - already moved
   ```

But this requires finding ALL secondary movement call sites.

## Testing

After fix, logs should show:
```
[SPATIAL] Moved Elias Thorne: (10.0, 2.1) → (12.7, 2.0) | Trail: 2.7m  ← ONLY ONE CALL
🏛️ ARCHITECT Elias Thorne moved to 'Technician Workbench'
```

No second 0m movement should appear.
