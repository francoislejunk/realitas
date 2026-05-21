# Internal Voice Failure Awareness - Self-Reflection on Repeated Failures

## Current State: NO

**The internal voice does NOT currently track or comment on repeated failures.**

### What It Currently Has:
- ✅ Personality-driven thoughts
- ✅ Observations and intuitions
- ✅ Solution suggestions (can be wrong)
- ✅ Warnings and reminders
- ✅ Current state awareness (stamina, spirit, supply)
- ✅ Recent narrative context (last 3-5 events)

### What It's Missing:
- ❌ **Failure tracking** - No count of how many times action failed
- ❌ **Pattern recognition** - No awareness of "we keep trying this"
- ❌ **Self-criticism** - No thoughts like "Are we really dumb enough to keep doing this?"
- ❌ **Frustration escalation** - No increasing exasperation after multiple failures
- ❌ **Learning from mistakes** - No memory of "this didn't work last time"

---

## Why This Would Be Powerful

**Realistic internal dialogue includes self-awareness about repeated mistakes:**

### **After 1st Failure:**
```
💭 Damn. That didn't work.
```

### **After 2nd Failure (Same Action):**
```
💭 Okay, maybe we need a different approach here.
```

### **After 3rd Failure (Same Action):**
```
💭 Are we really dumb enough to keep trying this? Clearly not working.
```

### **After 4th+ Failure (Same Action):**
```
💭 This is insane. We're doing the same thing over and over expecting different results.
```

**This creates:**
- **Realism** - People DO criticize themselves for repeated failures
- **Personality expression** - Different personalities react differently
- **Gameplay feedback** - Hints that player should try something else
- **Character depth** - Shows character learning (or not learning)

---

## Implementation Design

### **Phase 1: Failure Tracking**

**Track recent action attempts and outcomes:**

```python
class FailureTracker:
    """Tracks repeated action attempts and failures"""
    
    def __init__(self):
        self.recent_attempts = []  # List of (action, success, timestamp)
        self.max_history = 10  # Keep last 10 attempts
    
    def record_attempt(self, action_description: str, success: bool):
        """Record an action attempt"""
        self.recent_attempts.append({
            'action': self._normalize_action(action_description),
            'success': success,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        if len(self.recent_attempts) > self.max_history:
            self.recent_attempts.pop(0)
    
    def _normalize_action(self, action: str) -> str:
        """Normalize action for comparison (remove minor variations)"""
        # Extract core action (e.g., "climb ladder", "pick lock", "convince guard")
        # Simple keyword extraction for now
        keywords = action.lower().split()[:3]  # First 3 words
        return " ".join(keywords)
    
    def get_failure_count(self, action_description: str, window_minutes: int = 30) -> int:
        """Get count of recent failures for similar action"""
        normalized = self._normalize_action(action_description)
        cutoff_time = datetime.now() - timedelta(minutes=window_minutes)
        
        failures = [
            a for a in self.recent_attempts
            if a['action'] == normalized
            and not a['success']
            and a['timestamp'] > cutoff_time
        ]
        
        return len(failures)
    
    def get_consecutive_failures(self, action_description: str) -> int:
        """Get count of consecutive failures for this action"""
        normalized = self._normalize_action(action_description)
        
        # Count from most recent backwards
        consecutive = 0
        for attempt in reversed(self.recent_attempts):
            if attempt['action'] == normalized and not attempt['success']:
                consecutive += 1
            elif attempt['action'] == normalized:
                # Hit a success, stop counting
                break
        
        return consecutive
```

---

### **Phase 2: Enhanced Internal Voice Prompt**

**Add failure awareness to internal voice generation:**

```python
def generate_internal_voice(
    self,
    ua_actor,
    action_description: str,
    scene_description: str,
    narrative_context: str,
    success_level: Optional[int] = None,
    outcome_description: Optional[str] = None,
    failure_tracker: Optional[FailureTracker] = None  # NEW
) -> Optional[str]:
    """Generate internal voice with failure awareness"""
    
    # Get failure history for this action
    failure_context = ""
    if failure_tracker:
        consecutive_failures = failure_tracker.get_consecutive_failures(action_description)
        total_failures = failure_tracker.get_failure_count(action_description)
        
        if consecutive_failures > 0:
            failure_context = f"""
**FAILURE HISTORY:**
- Consecutive failures of this action: {consecutive_failures}
- Total recent failures: {total_failures}
- Pattern: Character keeps trying the same thing despite failures

**CRITICAL: Character should be AWARE of this pattern and react accordingly:**
- 1st failure: Disappointment, determination to try again
- 2nd failure: Frustration, questioning approach
- 3rd+ failure: Self-criticism, exasperation, "Are we really dumb enough to keep doing this?"

**The internal voice MUST reflect this escalating frustration based on failure count.**
"""
    
    # Build prompt with failure awareness
    base_prompt = f"""Generate a brief internal voice narration for {ua_name} during a ROAM mode action.

**ACTOR PERSONALITY:**
- Internal: {internal_personality}
- External: {external_personality}

**CURRENT STATE:**
- Stamina: {current_stamina}/10 | Spirit: {current_spirit}/10 | Supply: {current_supply}/10

**CURRENT ACTION:**
{action_description}

**OUTCOME:**
{outcome_description if outcome_description else "Action in progress"}
{f"Success Level: {self._get_success_descriptor(success_level)}" if success_level else ""}

{failure_context}

**INSTRUCTIONS:**
Generate internal voice that reflects:
1. Character's personality: {internal_personality}
2. Current outcome (success/failure)
3. **CRITICAL: Awareness of repeated failures if applicable**

**FAILURE AWARENESS EXAMPLES:**

**After 1st failure:**
- Cynical: "Of course that didn't work. Nothing ever does."
- Optimistic: "Okay, that didn't work. But we'll get it next time."
- Analytical: "Interesting. That approach failed. Need to recalculate."

**After 2nd consecutive failure:**
- Cynical: "Twice now. Maybe we should try something that actually works."
- Optimistic: "Alright, clearly we need a different strategy here."
- Analytical: "Two failures. The pattern suggests this approach is flawed."

**After 3rd+ consecutive failure:**
- Cynical: "Are we really dumb enough to keep doing this? Clearly not working."
- Optimistic: "Okay, we need to seriously rethink this. This isn't working."
- Analytical: "Three failures. Continuing this approach is irrational. Alternative required."

**After 4th+ consecutive failure:**
- Cynical: "This is insane. Same thing over and over. We're idiots."
- Optimistic: "This... this just isn't going to work. Time to try something completely different."
- Analytical: "Four failures. This approach has a 0% success rate. Must abandon immediately."

**CRITICAL: The frustration/self-criticism MUST escalate with failure count.**

Use "we", "us", "our". 1-2 sentences. Embody the personality while acknowledging failures.

Respond with ONLY the internal voice narration."""
```

---

### **Phase 3: Integration with Main Loop**

**Track failures and pass to internal voice:**

```python
# Initialize failure tracker (once at start of simulation)
failure_tracker = FailureTracker()

# After action resolution
if action_resolved:
    # Determine success/failure
    success = (success_level >= 3)  # 3+ is success
    
    # Record attempt
    failure_tracker.record_attempt(
        action_description=user_input,
        success=success
    )
    
    # Generate internal voice with failure awareness
    if current_mode == SimulationMode.ROAM:
        try:
            recent_narrative = narrative_context_manager.get_context_for_llm(
                lookback_events=3,
                importance_threshold="routine"
            )
            
            internal_voice = narrator.generate_internal_voice(
                ua_actor=actor,
                action_description=user_input,
                scene_description=scene_description,
                narrative_context=recent_narrative,
                success_level=success_level,
                outcome_description=contextual_result,
                failure_tracker=failure_tracker  # Pass tracker
            )
            
            if internal_voice:
                print(f"\n{Color.SYSTEM}{'─' * 70}{Color.RESET}")
                print(f"{Color.INTERNAL_VOICE}💭 {internal_voice}{Color.RESET}")
                print(f"{Color.SYSTEM}{'─' * 70}{Color.RESET}")
        except Exception:
            pass
```

---

## Personality-Based Reactions

### **Cynical Personality**
```
1st: "Of course that didn't work."
2nd: "Twice now. Shocking."
3rd: "Are we really dumb enough to keep doing this?"
4th: "This is insane. We're idiots."
```

### **Optimistic Personality**
```
1st: "Okay, that didn't work. But we'll get it next time."
2nd: "Alright, clearly we need a different strategy."
3rd: "Okay, we need to seriously rethink this."
4th: "This just isn't going to work. Time for something different."
```

### **Analytical Personality**
```
1st: "Interesting. That approach failed. Need to recalculate."
2nd: "Two failures. The pattern suggests this is flawed."
3rd: "Three failures. Continuing is irrational."
4th: "Four failures. 0% success rate. Must abandon."
```

### **Impulsive Personality**
```
1st: "Damn it! Why didn't that work?"
2nd: "Screw this. Let's try something else."
3rd: "This is bullshit. We're wasting time."
4th: "Forget it. This is never going to work."
```

### **Cautious Personality**
```
1st: "That didn't work. We should have been more careful."
2nd: "Two failures. We're missing something important."
3rd: "Three times now. We need to stop and think."
4th: "This approach is clearly wrong. We need to reassess."
```

---

## Benefits

### **Gameplay**
- ✅ **Feedback** - Player knows they're repeating failed actions
- ✅ **Guidance** - Hints to try something different
- ✅ **Challenge** - Encourages creative problem-solving

### **Immersion**
- ✅ **Realism** - People DO criticize themselves for repeated mistakes
- ✅ **Character depth** - Shows character learning (or frustration)
- ✅ **Personality expression** - Different reactions based on personality

### **System**
- ✅ **Simple tracking** - Just count recent failures
- ✅ **No new UI** - Uses existing internal voice system
- ✅ **Personality-driven** - Fits with existing personality system

---

## Example Scenario

**User keeps trying to pick a lock and failing:**

```
Attempt 1 (Failure):
🎲 Roll: 4 vs 7 → FAILURE
💭 Damn. That didn't work. Lock's tougher than it looks.

Attempt 2 (Failure):
🎲 Roll: 5 vs 7 → FAILURE
💭 Twice now. Maybe we need better tools for this.

Attempt 3 (Failure):
🎲 Roll: 3 vs 7 → FAILURE
💭 Are we really dumb enough to keep trying this? Clearly not working.

Attempt 4 (Failure):
🎲 Roll: 4 vs 7 → FAILURE
💭 This is insane. Same thing over and over. We need a different approach entirely.
```

**This naturally guides the player to:**
- Try a different action (kick door, find key, etc.)
- Improve their approach (get better tools, find help)
- Accept they can't do this and move on

---

## Implementation Priority

**MEDIUM-HIGH PRIORITY**

This enhances the existing internal voice system with:
1. Simple failure tracking (easy to implement)
2. Escalating self-awareness (powerful for immersion)
3. Personality-driven reactions (fits existing system)
4. Gameplay guidance (helps players)

**Should be implemented AFTER:**
- Fix #1 (Inquiry system)
- Fix #2 (Personality enforcement)

**Can be implemented as enhancement to existing internal voice system.**

---

## Storage

**Failure tracker should be:**
- Session-based (resets each session)
- In-memory (no persistence needed)
- Attached to main loop
- Passed to narrator when generating internal voice

**No need for complex storage - just track last 10 attempts.**

---

## Testing

### **Test 1: Single Failure**
```
Action: "I try to pick the lock"
Result: Failure
Expected: Disappointment, but not harsh
Example: "Damn. That didn't work."
```

### **Test 2: Second Failure**
```
Action: "I try to pick the lock" (again)
Result: Failure (2nd consecutive)
Expected: Frustration, questioning approach
Example: "Twice now. Maybe we need a different approach."
```

### **Test 3: Third Failure**
```
Action: "I try to pick the lock" (again)
Result: Failure (3rd consecutive)
Expected: Self-criticism, exasperation
Example: "Are we really dumb enough to keep doing this?"
```

### **Test 4: Success After Failures**
```
Action: "I try to pick the lock" (4th time)
Result: SUCCESS
Expected: Relief, vindication
Example: "Finally! Knew we'd get it eventually."
```

### **Test 5: Different Action**
```
Action: "I kick the door down"
Result: Failure
Expected: Fresh disappointment (not escalated)
Example: "That didn't work either. Door's solid."
```

---

## Summary

**Current Answer: NO** - Internal voice does NOT currently track or comment on repeated failures.

**Proposed Enhancement:**
1. Add `FailureTracker` class (simple, in-memory)
2. Track last 10 action attempts with success/failure
3. Pass failure count to internal voice generation
4. Generate personality-based reactions that escalate with failures
5. Self-criticism increases: "Are we really dumb enough to keep doing this?"

**Result:** More realistic, helpful, and personality-driven internal voice that guides players away from repeated failed approaches.
