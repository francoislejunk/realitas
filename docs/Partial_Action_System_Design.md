# Partial Action System - Never Deny, Always Interpret

## 🎯 **CORE PHILOSOPHY**

### **NEVER DENY USER ACTIONS**

**Traditional Approach (BAD):**
```
User: "I run to the guard and hug them"
System: "You can't do that. The guard is too far away."
❌ Action denied
❌ User frustrated
❌ Breaks immersion
```

**Partial Action Approach (GOOD):**
```
User: "I run to the guard and hug them"
System: "You sprint toward the guard but trip over scattered debris halfway, sprawling on the ground before you can reach them."
✅ Action attempted
✅ Diegetic explanation
✅ Immersion maintained
```

---

## 🔑 **KEY PRINCIPLES**

### **1. Always Allow Attempt**
- User ALWAYS acts, even if conditions aren't perfect
- No "you can't do that" messages
- Every action has an outcome, even if partial

### **2. Diegetic Explanations**
- Fiction-based reasons for partial completion
- "You trip over debris" NOT "insufficient time"
- World explains failure, not game mechanics

### **3. Dynamic Reinterpretation**
- Original intent: "Run to guard and hug them"
- Reinterpreted: "Run partway and fall"
- Mechanics process the NEW action, not the original

### **4. Narrative Consistency**
- Explanations fit the world and situation
- Use environmental elements (debris, wet floor, obstacles)
- Maintain 1980s immersion

---

## 📊 **PARTIAL ACTION CATEGORIES**

### **Reason Categories:**

| Reason | Description | Example |
|--------|-------------|---------|
| **INSUFFICIENT_TIME** | Ran out of UT | "You run out of time before completing" |
| **OUT_OF_RANGE** | Target too far/close | "They're too far away to whisper" |
| **OBSTACLE_INTERFERENCE** | Physical obstacle | "You collide with a chair" |
| **INTERRUPTED** | Another actor interfered | "Someone grabs your arm" |
| **EXHAUSTION** | Too tired/injured | "Fatigue catches up with you" |
| **ENVIRONMENTAL** | Weather, terrain | "You slip on the wet floor" |

---

## 🎮 **USAGE EXAMPLES**

### **Example 1: Movement + Action (Insufficient Time)**

**Scenario:**
- User: "I run to the mechanic and hug them"
- Mechanic is 20 units away
- Running takes 4 UT, hug takes 1 UT = 5 UT total
- User only has 3 UT available

**Traditional System:**
```
System: "You don't have enough time. You need 5 UT but only have 3 UT."
❌ Denied
```

**Partial Action System:**
```python
from partial_action_system import get_partial_action_interpreter
from spatial_context_system import Position, MovementSpeed

interpreter = get_partial_action_interpreter()

result = interpreter.interpret_movement_action(
    original_action="run to mechanic and hug them",
    start_pos=Position(5, 5),
    target_pos=Position(25, 5),  # 20 units away
    available_ut=3,
    speed=MovementSpeed.RUN
)

print(result.actual_outcome)
# "You make it about halfway before you trip over scattered tools and sprawl on the ground"

print(result.reinterpreted_action)
# "move partway toward target"

print(f"Completion: {result.partial_completion_percent * 100:.0f}%")
# "Completion: 60%"
```

**Narrative Output:**
```
You sprint toward the mechanic, arms outstretched, but trip over scattered 
tools halfway across the garage. You sprawl on the concrete, the hug never 
happening. The mechanic looks up, startled by the commotion.
```

✅ **Action attempted**
✅ **Diegetic explanation** (tools on floor)
✅ **Reinterpreted** (now it's a "fall" action, not a "hug")

---

### **Example 2: Out of Range (Whisper)**

**Scenario:**
- User: "I whisper to the guard about the case"
- Guard is 8 units away
- Whisper requires IMMEDIATE range (0-2 units)

**Traditional System:**
```
System: "You can't whisper. The guard is too far away."
❌ Denied
```

**Partial Action System:**
```python
result = interpreter.interpret_ranged_action(
    original_action="whisper to guard about the case",
    action_type="whisper",
    current_distance=8.0,
    required_distance_category=DistanceCategory.IMMEDIATE,
    actual_distance_category=DistanceCategory.NEAR
)

print(result.actual_outcome)
# "You lean in to whisper but they're too far - your words come out as a hushed call"

print(result.reinterpreted_action)
# "speak quietly from a distance"
```

**Narrative Output:**
```
You lean in conspiratorially, dropping your voice to a whisper, but the guard 
is across the room. Your words come out as a hushed call instead - not quite 
the secret you intended. The guard tilts their head, straining to hear.
```

✅ **Action attempted**
✅ **Diegetic explanation** (distance makes whisper impossible)
✅ **Reinterpreted** (becomes "quiet speaking" instead of "whisper")

---

### **Example 3: Combined Action (Movement Succeeds, Action Fails)**

**Scenario:**
- User: "I run to the door and lock it"
- Door is 10 units away
- Running takes 2 UT, locking takes 1 UT = 3 UT total
- User has 2 UT available

**Partial Action System:**
```python
# First, interpret movement
movement_result = interpreter.interpret_movement_action(
    original_action="run to door",
    start_pos=Position(5, 5),
    target_pos=Position(15, 5),
    available_ut=2,
    speed=MovementSpeed.RUN
)

# Then, interpret combined action
result = interpreter.interpret_combined_action(
    original_action="run to door and lock it",
    movement_component=movement_result,
    action_component="lock the door",
    action_ut_cost=1,
    total_ut_available=2
)

print(result.actual_outcome)
# "You reach the door but run out of time before you can lock it"
```

**Narrative Output:**
```
You sprint to the door, reaching it just as you hear footsteps behind you. 
Your hand grasps the lock, but before you can turn it, the door bursts open 
from the other side. You were too slow.
```

✅ **Movement succeeded**
✅ **Action failed** (no time)
✅ **Diegetic explanation** (door opened before lock turned)

---

### **Example 4: Melee Attack Out of Range**

**Scenario:**
- User: "I punch the thug"
- Thug is 4 units away
- Melee requires IMMEDIATE range (0-2 units)

**Partial Action System:**
```python
result = interpreter.interpret_ranged_action(
    original_action="punch the thug",
    action_type="melee",
    current_distance=4.0,
    required_distance_category=DistanceCategory.IMMEDIATE,
    actual_distance_category=DistanceCategory.CLOSE
)

print(result.actual_outcome)
# "You swing but the distance is too great - your attack falls short"

print(result.reinterpreted_action)
# "swing at empty air"
```

**Narrative Output:**
```
You lunge forward, fist cocked back, and throw a wild haymaker. But the thug 
is just out of reach - your knuckles slice through empty air as they step 
back, grinning. You're off-balance now, exposed.
```

✅ **Attack attempted**
✅ **Diegetic explanation** (target out of reach)
✅ **Reinterpreted** (becomes "miss" instead of "punch")
✅ **Consequences** (now off-balance, vulnerable)

---

## 🔧 **INTEGRATION WITH UTAS**

### **Step-by-Step Integration:**

```python
# In main simulation loop (redesigned_main.py)

from partial_action_system import get_partial_action_interpreter
from spatial_context_system import get_spatial_manager

interpreter = get_partial_action_interpreter()
spatial = get_spatial_manager()

# 1. User declares action
user_input = "I run to the guard and tackle them"

# 2. Parse action components
# (Use existing interpreter agent)
action_components = parse_action(user_input)
# Returns: {
#   "movement": {"target": "guard", "speed": "run"},
#   "action": {"type": "tackle", "target": "guard"}
# }

# 3. Get positions
ua_pos = spatial.get_actor_position("ua_001")
guard_pos = spatial.get_actor_position("guard_001")

# 4. Calculate movement time
from spatial_context_system import MovementSpeed
move_ut = spatial.get_movement_time("ua_001", guard_pos, MovementSpeed.RUN)
action_ut = 1  # Tackle takes 1 UT
total_ut = move_ut + action_ut

# 5. Check available UT
available_ut = get_actor_available_ut("ua_001")  # e.g., 3 UT

# 6. Interpret as partial if needed
if total_ut > available_ut:
    # Partial action!
    result = interpreter.interpret_combined_action(
        original_action=user_input,
        movement_component=interpreter.interpret_movement_action(
            original_action="run to guard",
            start_pos=ua_pos,
            target_pos=guard_pos,
            available_ut=available_ut - action_ut,  # Reserve UT for action
            speed=MovementSpeed.RUN
        ),
        action_component="tackle them",
        action_ut_cost=action_ut,
        total_ut_available=available_ut
    )
    
    # Use reinterpreted action for mechanics
    actual_action = result.reinterpreted_action
    # e.g., "move partway toward target" instead of "tackle"
    
    # Generate narrative
    narrative = interpreter.generate_narrative_description(result, actor_name="You")
    print(narrative)
    
    # Process reinterpreted action through UTAS
    process_action(actual_action, result.partial_completion_percent)
else:
    # Full action possible
    process_action(user_input, 1.0)
```

---

## 📝 **DIEGETIC FAILURE TEMPLATES**

### **Movement Failures:**

| Template | Example |
|----------|---------|
| Trip over obstacle | "You trip over scattered debris and sprawl on the ground" |
| Slip on surface | "You slip on a wet patch and lose your footing" |
| Collide with obstacle | "You collide with a chair and stagger back" |
| Lose balance | "You lose your balance on the uneven ground" |
| Get tangled | "You get tangled in cables and have to stop" |
| Misjudge distance | "You misjudge the distance and have to slow down" |

### **Range Failures:**

| Action Type | Too Far Explanation |
|-------------|---------------------|
| **Whisper** | "Your words come out as a hushed call" |
| **Touch** | "Your hand grasps at empty air" |
| **Grab** | "They're just out of reach" |
| **Melee** | "Your attack falls short" |
| **Throw** | "The object falls short of the target" |
| **Talk** | "You have to raise your voice to be heard" |

---

## 🎭 **NARRATIVE EXAMPLES**

### **Example 1: Heroic Failure**

**Input:** "I dive across the room to push the civilian out of the way"
**Distance:** 15 units, 3 UT available, need 4 UT

**Output:**
```
You launch yourself forward in a desperate dive, arms outstretched toward 
the civilian. But the distance is too great - you sprawl on the floor halfway 
across the room, watching helplessly as events unfold without you. Your heroic 
attempt falls short.
```

---

### **Example 2: Stealth Failure**

**Input:** "I sneak up behind the guard and grab them"
**Distance:** 8 units, 2 UT available, need 8 UT (sneaking is slow)

**Output:**
```
You move carefully, trying to stay silent, but you're forced to rush. Your 
foot catches on a loose floorboard with a loud CREAK. The guard spins around, 
hand going to their weapon. So much for the element of surprise.
```

---

### **Example 3: Combat Failure**

**Input:** "I charge the thug and punch them in the face"
**Distance:** 12 units, 2 UT available, need 3 UT

**Output:**
```
You break into a run, closing the distance fast, but trip over a discarded 
bottle at the last moment. You stumble forward, your punch going wild as you 
fight to keep your balance. The thug sees you coming and braces for impact.
```

---

## ✅ **BENEFITS**

### **1. Player Agency**
- ✅ User always acts
- ✅ No "you can't" messages
- ✅ Feels responsive and dynamic

### **2. Immersion**
- ✅ Diegetic explanations
- ✅ World-based failures
- ✅ No mechanical language

### **3. Narrative Richness**
- ✅ Failures create drama
- ✅ Partial success adds tension
- ✅ Consequences feel earned

### **4. Mechanical Integration**
- ✅ Reinterpreted actions processed by UTAS
- ✅ Partial completion affects outcomes
- ✅ Time/distance constraints matter

---

## 🎯 **DESIGN GUIDELINES**

### **DO:**
- ✅ Always allow the attempt
- ✅ Use environmental elements for failures
- ✅ Reinterpret action based on what actually happened
- ✅ Make failures interesting and dramatic
- ✅ Maintain 1980s setting in explanations

### **DON'T:**
- ❌ Use mechanical language ("insufficient UT")
- ❌ Deny actions outright
- ❌ Make failures feel arbitrary
- ❌ Break immersion with game terms
- ❌ Ignore partial completion in mechanics

---

## 🎉 **SUMMARY**

**Partial Action System provides:**
- 🎯 **Never deny** - always interpret
- 📖 **Diegetic explanations** - world-based failures
- 🔄 **Dynamic reinterpretation** - adjust action based on outcome
- 🎭 **Narrative richness** - failures create drama
- ⚙️ **Mechanical integration** - reinterpreted actions processed by UTAS

**Result: User always acts, failures feel natural, immersion maintained! 🎯**
