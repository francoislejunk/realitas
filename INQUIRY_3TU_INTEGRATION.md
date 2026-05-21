# Inquiry 3TU Integration

## The Issue

Inquiries (memory recall, mental actions) were being processed as fallible actions with UTAS rolls, but they were **not advancing time**. At line 4904, inquiries would just `continue` to the next turn without any time passage.

**Problem:**
```python
# After inquiry processing...
continue  # ❌ No time advancement!
```

This made inquiries "free actions" that didn't consume time, which is incorrect.

## The Solution

Integrated inquiries into the 3TU (Three Time Units) system so they advance time like all other fallible actions.

### Time Classification

**3-SECOND (All Inquiries):**
- All questions and mental actions
- Quick mental recall
- Information gathering
- Memory recall
- Examples:
  - "What's my friend's name?"
  - "Who is that person?"
  - "Where did I put my keys?"
  - "How do I get downtown?"
  - "I try to remember my childhood"
  - "I think back to that day"

### Implementation

**File:** `MAIN/redesigned_main.py` (lines 4903-4939)

```python
# ============================================================
# TIME ADVANCEMENT - Inquiries use 3TU system like all fallible actions
# ============================================================
# All inquiries are 3-SECOND (quick mental recall)
from rule_of_3s import RuleOf3Category

# All inquiries = 3-SECOND
inquiry_time_scale = RuleOf3Category.THREE_SECOND
time_description = "a quick thought"

# Advance time using master_time system
if not SUPPRESS_DEBUG:
    print(f"{Color.INFO}[INQUIRY TIME] {inquiry_time_scale.name} - {time_description}{Color.RESET}")

req = master_time.create_user_action_request(
    inquiry_time_scale,
    actor.sheet.name,
    user_input
)
res = master_time.request_time_advancement(req)

# Display time advancement
if not SUPPRESS_DEBUG:
    elapsed = simulation_time_tracker.get_simulation_time_display()
    print(f"{Color.SYSTEM}⏰ Time advanced: +{res.duration_advanced_seconds}s | Clock: {res.new_time.format_full()} | Elapsed: {elapsed}{Color.RESET}")

# Continue to next turn
continue
```

## Time Scale

**All Inquiries = 3-SECOND:**
- All questions and mental actions
- Fast mental access
- ~3 seconds of in-game time
- Simple and consistent

## Examples

### All Inquiries (3-SECOND)
```
User: "What's my best friend's name?"
→ 3-SECOND
→ Time advances: +3s
→ Clock: 9:00:03 AM

User: "How do I get downtown?"
→ 3-SECOND
→ Time advances: +3s
→ Clock: 9:00:06 AM

User: "Who is that person?"
→ 3-SECOND
→ Time advances: +3s
→ Clock: 9:00:09 AM

User: "I try to remember my best friend"
→ 3-SECOND
→ Time advances: +3s
→ Clock: 9:00:12 AM

User: "I think back to that day"
→ 3-SECOND
→ Time advances: +3s
→ Clock: 9:00:15 AM
```

## Flow

```
1. User inputs inquiry
2. Classify as inquiry (fallible_subtype: inquiry) ✓
3. Check intent availability ✓
4. Process inquiry with UTAS roll ✓
5. Generate perceptual description ✓
6. Generate internal voice ✓
7. Create memory (if appropriate) ✓
8. Advance time by 3 seconds ✓ NEW
9. Continue to next turn ✓
```

## Result

✅ **Inquiries advance time** - No longer free actions  
✅ **All inquiries = 3-SECOND** - Simple and consistent  
✅ **Consistent with other actions** - All fallible actions advance time  
✅ **Realistic time passage** - Mental actions are nearly instantaneous  

Inquiries are now fully integrated into the time system!
