# DOES_NOT_EXIST Narrative Fix

## Problem Identified

When the Intent Availability system returned `DOES_NOT_EXIST`, the perceptual description was describing the **current scene** instead of explaining **why the target doesn't exist**.

### Example of the Bug:
```
User: "I head to the nearest diner"
System: "You see a payphone in the corner. The ringing is constant. You see YOUR notebook..."
```

This is WRONG because it's describing the apartment (current location) instead of explaining why there's no diner nearby.

## Root Cause

**File:** `MAIN/redesigned_main.py` line 3764

The system was calling `narrator.generate_inquiry_response()` for DOES_NOT_EXIST cases. This method is designed for answering questions about the current scene, NOT for explaining absences.

```python
# OLD (WRONG):
perceptual_description = narrator.generate_inquiry_response(
    user_question=user_input,
    ua_actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    current_time=time_context,
    availability_context=availability_result
)
```

## Solution Implemented

Created a new specialized method: `generate_does_not_exist_narrative()` in `NarratorAgent`.

### Changes Made:

**1. MAIN/redesigned_main.py (line 3764)**
```python
# NEW (CORRECT):
perceptual_description = narrator.generate_does_not_exist_narrative(
    user_intent=user_input,
    ua_actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    current_time=time_context,
    reasoning=availability_result.get("reasoning", "No reasoning provided")
)
```

**2. agents/narrator_agent.py (new method at line 4180)**

Created `generate_does_not_exist_narrative()` with:
- Specialized prompt that focuses on **explaining absence**
- Clear examples of correct vs incorrect narratives
- Diegetic, observational tone
- Specific, contextual explanations

### Key Prompt Instructions:

**CRITICAL REQUIREMENTS:**
1. **Explain the ABSENCE** - Don't describe the current scene, explain why the target doesn't exist
2. **Be DIEGETIC** - Make it feel natural, not like a system message
3. **Be SPECIFIC** - Don't just say "you don't see it", explain WHY it's not there
4. **Use OBSERVATION** - Describe what you DO see that confirms the absence

### Examples in Prompt:

❌ **WRONG** (describes current scene):
```
"You see a payphone in the corner. The ringing is constant."
```

✅ **CORRECT** (explains absence):
```
"You scan the industrial area around you. There are no diners in sight—just warehouses, 
auto shops, and empty lots. This part of town is all business, no food."
```

✅ **CORRECT** (specific and contextual):
```
"You step outside and look around. The neighborhood is residential—houses, apartments, 
a corner store. No restaurants or diners on this block. You'd have to head downtown for that."
```

✅ **CORRECT** (diegetic world knowledge):
```
"You check your mental map of the area. There used to be a diner on 5th Street, but it 
closed down months ago. The nearest one now is probably downtown, at least a 15-minute drive."
```

## Expected Behavior Now

**User Input:** "I head to the nearest diner"

**System Output:**
```
You step outside and scan the street. This neighborhood is all residential—apartment 
buildings, a corner bodega, a laundromat. No diners or restaurants in sight. You'd 
need to head downtown or to the commercial district for that.

💭 INTERNAL VOICE
We're in the wrong part of town for food. Should've thought of that before we left.
```

## Benefits

✅ **Diegetic** - Feels like natural observation, not system rejection  
✅ **Informative** - Explains WHY it doesn't exist  
✅ **Immersive** - Maintains narrative flow  
✅ **Contextual** - References the actual environment  
✅ **Actionable** - Often suggests alternatives or next steps

## Files Modified

1. `MAIN/redesigned_main.py` - Line 3764 (changed method call)
2. `agents/narrator_agent.py` - Lines 4180-4283 (new method)

## Testing

Test with various DOES_NOT_EXIST scenarios:
- "I head to the nearest diner"
- "I go to the gun shop"
- "I drive to the airport"
- "I call my lawyer"
- "I check my private jet"

Each should now explain WHY it doesn't exist rather than describing the current scene.
