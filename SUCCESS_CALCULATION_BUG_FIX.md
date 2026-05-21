# Success Calculation Bug Fix - Missing 'total' Field

## Problem

**User Question:** "why did they not register the 7 success"

The proactor's success calculation showed **7 successes** initially, but then showed **0 successes** in the final outcome, resulting in a tie instead of a proactor victory.

## Root Cause

The Exchange system was returning success data with a field called `"success"`, but the reporter and main loop were looking for a field called `"total"`.

### Evidence from Output:

**First Step 2 (Correct):**
```
Success Calculation:
(2 + 3 + 0 + 0 + 0) - (-1 + -2 + 1) = 7
Narrative: Dex's attempt registers as CRITICAL SUCCESS +1 (7 successes).
```

**Second Step 2 (Wrong):**
```
Success Calculation:
Calculation incomplete due to missing factors.
  • Total: 0  ← WRONG!
Narrative: Dex's attempt registers as FAILED (0 successes).
```

### Code Analysis:

**exchange_system.py (line 421-439):**
```python
proactor_results = {
    "action_description": self.proactor_action.get("narrative_description", "..."),
    "success": proactor_success,  # ← Uses 'success'
    "calc_str": proactor_calc_str,
    ...
}
```

**reporter.py (line 210):**
```python
total = self._safe_int(calc.get('total', 0))  # ← Expects 'total'
```

**redesigned_main.py (line 5932):**
```python
proactor_total = proactor_success_data.get('total', 0)  # ← Expects 'total'
```

### Why It Happened:

1. **First Step 2 Report** (line 4504): Uses the initial calculation before Exchange execution
2. **Reactor times out**: User doesn't respond in time
3. **Exchange executes**: Returns results with `"success"` field
4. **Second Step 2 Report** (line 5968): Uses Exchange results, looks for `"total"`, gets 0 (default)
5. **Final Outcome**: Uses 0 vs 0, declares tie instead of 7 vs 0 victory

## Solution Applied

Added `"total"` field to both `proactor_results` and `reactor_results` in `exchange_system.py`:

```python
proactor_results = {
    "action_description": self.proactor_action.get("narrative_description", "..."),
    "success": proactor_success,
    "total": proactor_success,  # ← Added for reporter compatibility
    "calc_str": proactor_calc_str,
    ...
}

reactor_results = {
    "action_description": self.reactor_action.get("narrative_description", "..."),
    "success": reactor_success,
    "total": reactor_success,  # ← Added for reporter compatibility
    "calc_str": reactor_calc_str,
    ...
}
```

## Result

✅ **Both `"success"` and `"total"` fields now present** in Exchange results

✅ **Reporter can find `calc.get('total', 0)`** and display correct value

✅ **Main loop can find `proactor_success_data.get('total', 0)`** for outcome calculation

✅ **Second Step 2 report will now show 7 successes** instead of 0

✅ **Final outcome will correctly show proactor victory** (7 vs 0) instead of tie

## Files Modified

- **exchange_system.py** (lines 424, 445): Added `"total"` field to both proactor_results and reactor_results

## Testing

The next time you run a contested action where the reactor times out, the proactor's success value should be preserved correctly through both Step 2 reports and into the final outcome calculation.
