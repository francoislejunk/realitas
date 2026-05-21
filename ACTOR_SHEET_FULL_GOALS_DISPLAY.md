# Actor Sheet Now Displays Full Goals (No Truncation)

## The Problem

Goals were being truncated to 50 characters with "..." added:

```
🎯 Goal: Find my missing sister and bring her ho...
```

This cut off important information and made goals hard to read.

## The Solution

Removed goal truncation - goals now display in full length.

## Changes Made

### File: `actor_sheet.py`

**1. Removed Truncation Logic** (lines 475-478)

**Before:**
```python
def _format_goal(self, goal: str, max_length: int = 50) -> str:
    """Formats a goal string, truncating if too long."""
    if len(goal) <= max_length:
        return goal
    return goal[:max_length-3] + "..."  # Truncated!
```

**After:**
```python
def _format_goal(self, goal: str, max_length: int = None) -> str:
    """Formats a goal string - no truncation, show full goal."""
    # Return full goal without truncation
    return goal
```

**2. Removed Fixed-Width Padding** (lines 562-565)

**Before:**
```python
print(f"│ 🎯 Goal: {formatted_goal:<43} │")  # Fixed 43 char width
print(f"│    Progress: {goal_progress}% [{goal_importance}] │")
print(f"│ 📋 Current Task: {current_task:<38} │")  # Fixed 38 char width
```

**After:**
```python
print(f"│ 🎯 Goal: {formatted_goal}")  # No padding, full length
print(f"│    Progress: {goal_progress}% [{goal_importance}]")
print(f"│ 📋 Current Task: {current_task}")  # No padding, full length
```

## Example Output

### Before (Truncated)

```
┌─────────────────────────────────────────────────────────┐
│ 🎭 Lena Kovač            │ 💼 Underground Music Promoter    │
│ 🎂 Age: 28 • 📍 Location: Downtown                      │
│ ═══════════════════════════════════════════════════════ │
│ 🧠 Cynical and analytical (Internal) • 🎯 Charismatic and passionate (External) │
│ 🎯 Goal: Find my missing sister and bring her ho...     │
│    Progress: 35% [life_defining]                        │
│ 📋 Current Task: Investigate the last known lo...       │
├─────────────────────────────────────────────────────────┤
```

### After (Full Display)

```
┌─────────────────────────────────────────────────────────┐
│ 🎭 Lena Kovač            │ 💼 Underground Music Promoter    │
│ 🎂 Age: 28 • 📍 Location: Downtown                      │
│ ═══════════════════════════════════════════════════════ │
│ 🧠 Cynical and analytical (Internal) • 🎯 Charismatic and passionate (External) │
│ 🎯 Goal: Find my missing sister and bring her home safely before it's too late
│    Progress: 35% [life_defining]
│ 📋 Current Task: Investigate the last known location where she was seen and talk to witnesses
├─────────────────────────────────────────────────────────┤
```

## Benefits

✅ **Full Information** - No important details cut off  
✅ **Better Readability** - Can read complete goals  
✅ **No Confusion** - Don't have to guess what "..." hides  
✅ **Natural Display** - Goals display as written  
✅ **Works for All Lengths** - Short or long goals both work  

## Impact on Display

### Short Goals
```
│ 🎯 Goal: Survive in the city
│    Progress: 60% [major]
```
Works perfectly - no change from before.

### Medium Goals
```
│ 🎯 Goal: Save enough money to open a proper restaurant
│    Progress: 45% [major]
```
Now fully visible instead of "Save enough money to open a proper restaur..."

### Long Goals
```
│ 🎯 Goal: Find my missing sister and bring her home safely before it's too late
│    Progress: 35% [life_defining]
```
Fully visible instead of "Find my missing sister and bring her ho..."

## Technical Details

- Removed `max_length` parameter enforcement
- Removed string slicing `goal[:max_length-3]`
- Removed padding format specifiers `:<43` and `:<38`
- Goals and tasks now display at natural length
- Box borders removed from goal/task lines to allow overflow

## Files Modified

**`actor_sheet.py`** (lines 475-478, 562-565)
- `_format_goal()` method - removed truncation
- `display_detailed()` method - removed fixed-width padding

## Result

✅ **Goals display in full** - No truncation  
✅ **Tasks display in full** - No truncation  
✅ **Better UX** - Users can read complete information  
✅ **No information loss** - Everything is visible  

Users can now see their complete goals and tasks without having to guess what was cut off!
