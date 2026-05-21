# Quick Test - Exit Transition System

## How to Test the New Feature

### Setup
1. Run the simulation: `python MAIN/redesigned_main.py`
2. Load any existing session (like Elias Thorne)
3. You should be in an interior location (apartment, van, building, etc.)

### Test Commands

#### Test 1: Basic Leave
```
Input: I leave
Expected: Automatic transition to hallway/street with new scene description
```

#### Test 2: Walk to Door
```
Input: I walk to the door
Expected: Movement to door, then automatic transition
```

#### Test 3: Go Outside
```
Input: I go outside
Expected: Automatic transition to exterior location
```

#### Test 4: Exit Building
```
Input: I exit the building
Expected: Transition to street with new scene
```

#### Test 5: In-Room Movement (Should NOT Trigger)
```
Input: I approach the workbench
Expected: Normal movement, NO transition, just perceptual description
```

### What to Look For

✅ **Success Indicators:**
```
[EXIT SYSTEM] Automatic transition to 'Hallway' detected
[EXIT SYSTEM] Distance to exit: 18.5 units
[SYSTEM] Cleared NPCs from previous location
[EXIT] Transitioned to 'Hallway'

🎬 SCENE DESCRIPTION:
You step through the doorway into a narrow hallway...
```

✅ **No Separate Door Action Required:**
- User types "I leave" → Door opens automatically
- No need to type "I open the door" first
- System doesn't prompt for additional action

✅ **New Location Immediately Described:**
- Scene description shows new location
- NPCs may be present in new location
- Can immediately act in new location

❌ **What Should NOT Happen:**
- System asking "do you want to open the door?"
- Generic "you approach the door" with no transition
- Error messages about missing destination
- Transition triggering for in-room objects (workbench, terminal, etc.)

### Debug Output

When feature works correctly, you'll see:
```
[EXIT SYSTEM] Automatic transition to '[destination]' detected
[EXIT SYSTEM] Distance to exit: [distance] units
[SYSTEM] Cleared NPCs from previous location
[EXIT] Transitioned to '[destination]'
```

### Common Issues

**Issue:** No transition occurs when saying "I leave"
- **Check:** Are you in an interior location with an exit/door?
- **Check:** Is there a door obstacle in the spatial system?
- **Fix:** Try "I walk to the door" first to get closer

**Issue:** Transition happens for in-room objects
- **Check:** Is the object marked as "door" or "exit" in obstacles?
- **Fix:** This is a false positive - report if occurs

**Issue:** Error messages during transition
- **Check:** Error logs for details
- **Fix:** May indicate missing conductor/architect components

### Expected Flow

```
1. User: "I leave"
   ↓
2. System detects exit proximity
   ↓
3. System pre-creates destination
   ↓
4. System displays new location
   ↓
5. User can immediately act in new location
```

**Total Time:** < 5 seconds (depending on LLM speed)

### Verification Checklist

After each test:
- [ ] Transition occurred automatically?
- [ ] New location was described?
- [ ] No "open door" prompt?
- [ ] NPCs cleared from previous location?
- [ ] Can interact with new location immediately?
- [ ] Spatial map updated (if using /pmap)?

### Files to Check

If issues occur, check logs in:
- Console output (look for [EXIT SYSTEM] tags)
- `simulation_data/sessions/[session_id]/` (spatial state)
- Error tracebacks (if any exceptions)

### Quick Regression Test

Test that existing functionality still works:
```
1. "I walk to the workbench" → Should work (in-room movement)
2. "look" → Should work (scene observation)
3. "I examine the terminal" → Should work (object interaction)
4. "I leave" → Should work (exit transition)
5. Return to previous location → Should work (reverse travel)
```

All commands should work without errors.

---

## Implementation Status

**Status:** ✅ COMPLETE (2026-02-18)
**Files Modified:** MAIN/redesigned_main.py
**Documentation:** EXIT_TRANSITION_IMPLEMENTATION_SUMMARY.md
**Test Plan:** TEST_EXIT_TRANSITION_SYSTEM.md

Ready for testing!
