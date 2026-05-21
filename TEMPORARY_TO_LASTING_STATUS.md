# Temporary-to-Lasting Status Shift System - Implementation Analysis

## ⚠️ **PARTIAL IMPLEMENTATION - Missing Critical Integration**

### What's Implemented ✅

**1. Conversion Logic** ✅
**File:** `enhanced_temporary_recovery_system.py` (lines 84-107)

When a temporary shift causes status to go below 0:
```python
if new_value < 0:
    temporary_portion = -original_value  # Above 0 = temporary
    lasting_portion = abs(new_value)      # Below 0 = lasting
    
    # Store lasting shift for later application
    self.lasting_shifts[actor_name][status_type] -= lasting_portion
    
    # Track only temporary portion for recovery
    effect = EnhancedTemporaryStatusEffect(
        temporary_shift_amount=temporary_portion,
        current_value=0,
        ...
    )
```

**Example:**
- Actor has Stamina = 3
- Takes -5 damage
- Result: 3 + (-5) = -2
- **Temporary portion:** -3 (from 3 → 0, recoverable)
- **Lasting portion:** -2 (from 0 → -2, permanent damage to max capacity)

**2. Lasting Shift Storage** ✅
**File:** `enhanced_temporary_recovery_system.py` (lines 54-56, 79-90)
```python
self.lasting_shifts: Dict[str, Dict[StatusType, int]] = {}
```
- Tracks accumulated lasting shifts per actor
- Stored separately from temporary effects

**3. Application Method** ✅
**File:** `enhanced_temporary_recovery_system.py` (lines 223-232)
```python
def apply_lasting_shifts_to_actors(self, actors: List[Actor]):
    """Apply all accumulated lasting shifts to actors"""
    for actor in actors:
        actor_name = actor.sheet.name
        if actor_name in self.lasting_shifts:
            for status_type, lasting_amount in self.lasting_shifts[actor_name].items():
                if lasting_amount != 0:
                    actor.sheet.apply_lasting_status_shift(status_type, lasting_amount)
            
            self.lasting_shifts[actor_name] = {}  # Clear after applying
```

**4. Actor Sheet Support** ✅
**File:** `actor_sheet.py` (lines 94-106, 339-346)

**Status.apply_lasting_shift():**
```python
def apply_lasting_shift(self, amount: int):
    """Applies a lasting shift that affects both current value and max capacity."""
    self.lasting_shift_total += amount
    self.max_value = max(0, self.base_max_value + self.lasting_shift_total)
    self.value = self._clamp(self.value + amount)
```

**ActorSheet.apply_lasting_status_shift():**
```python
def apply_lasting_status_shift(self, status_type: StatusType, amount: int):
    """Apply a lasting shift that affects both current value and max capacity."""
    if status_type in self.statuses:
        self.statuses[status_type].apply_lasting_shift(amount)
        print(f"System: {self.name}'s {status_type.name} lasting shift: {amount:+d} (Max capacity now: {self.statuses[status_type].max_value})")
        
        if self.is_dead():
            print(f"CRITICAL: {self.name} has died due to status max capacity reaching 0!")
```

**5. Death Detection** ✅
**File:** `actor_sheet.py` (lines 107-110, 336-337)
```python
def is_dead(self) -> bool:
    """Check if max capacity has reached 0 (permanent death)."""
    return self.max_value <= 0

# ActorSheet level
def is_dead(self) -> bool:
    critical_statuses = [StatusType.STAMINA, StatusType.SPIRIT]
    return any(self.statuses[status_type].is_dead() for status_type in critical_statuses)
```

**6. Exchange System Integration** ✅
**File:** `exchange_system.py` (lines 327-331, 363-365, 706-707, 833-834, 924-925)

Exchange system properly calls `apply_lasting_status_shift()` for lasting shifts:
```python
if proactor_factors.get("shift_type") == "Lasting":
    self.reactor.sheet.apply_lasting_status_shift(proactor_targeted_status, final_shift_amount)
elif proactor_factors.get("shift_type") == "Temporary":
    # ... temporary handling with conversion logic
```

### ❌ **What's MISSING - Critical Gap**

**Lasting Shifts Are NOT Applied at End of Round/Turn**

**Problem:**
The `apply_lasting_shifts_to_actors()` method exists but is **NEVER CALLED** in the main simulation loop.

**Where It Should Be Called:**
- **Option 1:** End of each turn (after exchange completes)
- **Option 2:** End of each round (when turn queue cycles)
- **Option 3:** Start of next round (before initiative)

**Current State:**
```python
# enhanced_round_manager.py - end_round() method
def end_round(self):
    """Handle end-of-round logic like status effect decay."""
    # ... handles effect duration decay
    # ❌ MISSING: self.recovery_integrator.apply_lasting_shifts_to_actors(active_actors)
```

**Impact:**
- Temporary-to-lasting conversion is tracked internally
- But lasting shifts are **never actually applied** to max capacity
- Actors won't die from accumulated lasting damage
- Max capacity remains unchanged despite conversion

### What Happens Currently

**Turn 1:**
```
Guard takes -7 Stamina damage (has 5 max)
→ Conversion: -5 temporary, -2 lasting
→ lasting_shifts["Guard"][STAMINA] = -2  ← Stored but not applied
→ Guard's max capacity: Still 5 (should be 3)
```

**Turn 2:**
```
Guard takes another -7 Stamina damage
→ Conversion: -5 temporary, -2 lasting  
→ lasting_shifts["Guard"][STAMINA] = -4  ← Accumulated but not applied
→ Guard's max capacity: Still 5 (should be 1)
```

**Turn 3:**
```
Guard takes another -7 Stamina damage
→ Conversion: -5 temporary, -2 lasting
→ lasting_shifts["Guard"][STAMINA] = -6  ← Should kill but doesn't
→ Guard's max capacity: Still 5 (should be -1, which means DEAD)
→ Guard.is_dead() = False (WRONG - should be True)
```

### Required Fix

**Add to `enhanced_round_manager.py`:**

```python
def end_round(self):
    """Handle end-of-round logic like status effect decay and lasting shifts."""
    print(f"{Color.SYSTEM}--- Round {self.round_number} End ---{Color.RESET}")
    
    active_actors = self.actor_manager.get_active_actors()
    
    # Apply accumulated lasting shifts to max capacity
    self.recovery_integrator.recovery_manager.apply_lasting_shifts_to_actors(active_actors)
    
    # Handle status effect duration decay
    for actor in active_actors:
        expired_effects = []
        active_effects = []
        
        for effect in actor.sheet.effects:
            if effect.duration > 0:
                effect.duration -= 1
                if effect.duration == 0:
                    expired_effects.append(effect)
                else:
                    active_effects.append(effect)
            elif effect.duration == -1:  # Permanent effect
                active_effects.append(effect)
        
        actor.sheet.effects = active_effects
        
        # Report expired effects
        for effect in expired_effects:
            print(f"{Color.SYSTEM}EFFECT: The '{effect.name}' effect has worn off for {actor.sheet.name}.{Color.RESET}")
```

**OR Add to main loop after each exchange:**

```python
# After exchange completes
result = exch.execute()

# Apply any accumulated lasting shifts immediately
encounter_checker.current_context.enhanced_recovery.recovery_manager.apply_lasting_shifts_to_actors([proactor, reactor])

# Check for death
if proactor.sheet.is_dead():
    print(f"{proactor.sheet.name} has died!")
if reactor.sheet.is_dead():
    print(f"{reactor.sheet.name} has died!")
```

### Verification Checklist

✅ **Conversion logic** - Splits damage into temporary/lasting  
✅ **Lasting shift storage** - Tracks accumulated lasting damage  
✅ **Application method** - Can apply lasting shifts to max capacity  
✅ **Actor sheet support** - Handles lasting shifts correctly  
✅ **Death detection** - Detects when max capacity reaches 0  
✅ **Exchange integration** - Properly categorizes shift types  
❌ **Main loop integration** - **NOT CALLED ANYWHERE**  
❌ **End of round/turn** - **MISSING INTEGRATION**  

### Current Status

**System State:** PARTIALLY IMPLEMENTED

**What Works:**
- Temporary damage recovery (+1 per round to lowest status)
- Conversion calculation (temporary vs lasting portions)
- Death detection logic
- Actor sheet lasting shift support

**What Doesn't Work:**
- Lasting shifts never applied to max capacity
- Actors can't die from accumulated lasting damage
- Max capacity never decreases despite conversion
- System tracks lasting shifts but doesn't use them

**Priority:** **HIGH** - Core feature is non-functional without this integration

### Recommended Solution

**Add to `enhanced_round_manager.py` end_round() method:**
```python
# Apply accumulated lasting shifts before checking death
self.recovery_integrator.recovery_manager.apply_lasting_shifts_to_actors(active_actors)

# Check for deaths after lasting shifts applied
for actor in active_actors:
    if actor.sheet.is_dead():
        print(f"{Color.ERROR}💀 {actor.sheet.name} has died from accumulated injuries!{Color.RESET}")
```

This ensures:
1. Lasting shifts applied at predictable time (end of round)
2. Death checks happen after lasting shifts
3. Consistent with other end-of-round processing (effect decay)
4. Visible to players when it happens

## Summary

The temporary-to-lasting conversion system is **85% complete** but **non-functional** due to missing integration. All the logic exists, but `apply_lasting_shifts_to_actors()` is never called, so lasting shifts accumulate internally but never affect max capacity or cause death.

**Fix Required:** Add one method call to `end_round()` in `enhanced_round_manager.py`

**Status:** NEEDS INTEGRATION ⚠️
