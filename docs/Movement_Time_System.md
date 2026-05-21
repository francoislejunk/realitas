# Movement Time System - Distance & Duration

## 🏃 **MOVEMENT SPEED CATEGORIES**

### **Speed Definitions**

| Speed | Units/Second | Description | Use Cases |
|-------|--------------|-------------|-----------|
| **CRAWL** | 0.5 u/s | Crawling, sneaking very slowly | Injured, stealth in tight space |
| **SNEAK** | 1.0 u/s | Sneaking, careful movement | Stealth approach, avoiding detection |
| **WALK** | 2.0 u/s | Normal walking pace | Default movement, casual approach |
| **JOG** | 3.5 u/s | Light jog, hurried movement | Urgent but not panicked |
| **RUN** | 5.0 u/s | Running, urgent movement | Chase, escape, emergency |
| **SPRINT** | 7.0 u/s | Full sprint, maximum speed | Life or death, all-out effort |

---

## ⏱️ **TIME CONVERSION**

### **Seconds to Unit Time (UT)**

**Rule:** 3 seconds = 1 UT (rounded up)

| Seconds | Unit Time (UT) |
|---------|----------------|
| 0-3 | 1 UT |
| 4-6 | 2 UT |
| 7-9 | 3 UT |
| 10-12 | 4 UT |
| 13-15 | 5 UT |

---

## 📏 **MOVEMENT TIME TABLES**

### **Table 1: WALK Speed (2 units/second)**

| Distance | Seconds | Unit Time (UT) | Example |
|----------|---------|----------------|---------|
| 1 unit | 0.5 s | 1 UT | Step forward |
| 2 units | 1.0 s | 1 UT | Across a desk |
| 3 units | 1.5 s | 1 UT | To nearby person |
| 4 units | 2.0 s | 1 UT | Across small room |
| 5 units | 2.5 s | 1 UT | To far side of room |
| 6 units | 3.0 s | 1 UT | Across medium room |
| 8 units | 4.0 s | 2 UT | Across large room |
| 10 units | 5.0 s | 2 UT | Down a hallway |
| 15 units | 7.5 s | 3 UT | Across warehouse |
| 20 units | 10.0 s | 4 UT | Across parking lot |

---

### **Table 2: RUN Speed (5 units/second)**

| Distance | Seconds | Unit Time (UT) | Example |
|----------|---------|----------------|---------|
| 2 units | 0.4 s | 1 UT | Quick dash |
| 5 units | 1.0 s | 1 UT | Sprint to cover |
| 10 units | 2.0 s | 1 UT | Run across room |
| 15 units | 3.0 s | 1 UT | Run down hallway |
| 20 units | 4.0 s | 2 UT | Run across lot |
| 30 units | 6.0 s | 2 UT | Long sprint |

---

### **Table 3: SNEAK Speed (1 unit/second)**

| Distance | Seconds | Unit Time (UT) | Example |
|----------|---------|----------------|---------|
| 1 unit | 1.0 s | 1 UT | Careful step |
| 2 units | 2.0 s | 1 UT | Sneak forward |
| 3 units | 3.0 s | 1 UT | Approach quietly |
| 5 units | 5.0 s | 2 UT | Sneak across room |
| 10 units | 10.0 s | 4 UT | Long stealth approach |

---

## 🎮 **USAGE EXAMPLES**

### **Example 1: Simple Movement**

```python
from spatial_context_system import get_spatial_manager, Position, MovementSpeed

spatial = get_spatial_manager()

# UA wants to move from (5, 5) to (15, 10)
ua_pos = Position(5, 5)
target_pos = Position(15, 10)

# Calculate at WALK speed
seconds, ut = ua_pos.calculate_movement_time_with_ut(target_pos, MovementSpeed.WALK)
print(f"Walking: {seconds:.1f} seconds = {ut} UT")
# Output: "Walking: 5.6 seconds = 2 UT"

# Calculate at RUN speed
seconds, ut = ua_pos.calculate_movement_time_with_ut(target_pos, MovementSpeed.RUN)
print(f"Running: {seconds:.1f} seconds = {ut} UT")
# Output: "Running: 2.2 seconds = 1 UT"
```

---

### **Example 2: Action Feasibility with Movement**

```python
# User wants to whisper to NUA who is 8 units away
ua_pos = spatial.get_actor_position("ua_001")
nua_pos = spatial.get_actor_position("nua_001")

distance = ua_pos.distance_to(nua_pos)  # 8 units
print(f"Distance: {distance:.1f} units")

# Check if whisper is feasible
feasible, reason = spatial.is_action_feasible("ua_001", "nua_001", "whisper")
print(f"Can whisper? {feasible} - {reason}")
# Output: "Can whisper? False - Target too far for whisper"

# Calculate movement time to get in range
# Whisper requires IMMEDIATE (0-2 units), so move to 1 unit away
target_pos = Position(nua_pos.x - 1, nua_pos.y)
seconds, ut = ua_pos.calculate_movement_time_with_ut(target_pos, MovementSpeed.WALK)
print(f"Move to whisper range: {seconds:.1f}s = {ut} UT")
# Output: "Move to whisper range: 3.5s = 2 UT"

# System response:
# "You need to move closer first. It will take 2 UT to get in whisper range."
```

---

### **Example 3: Partial Actions (Time Constraints)**

```python
# User has 3 UT available this turn
available_ut = 3

# User wants to run to NUA (20 units away) and attack
ua_pos = Position(5, 5)
nua_pos = Position(25, 5)

# Calculate movement time at RUN speed
seconds, move_ut = ua_pos.calculate_movement_time_with_ut(nua_pos, MovementSpeed.RUN)
print(f"Movement: {move_ut} UT")
# Output: "Movement: 4 UT"

# Attack takes 1 UT
attack_ut = 1
total_ut = move_ut + attack_ut  # 5 UT

if total_ut > available_ut:
    # Partial action - can only move partway
    ut_for_movement = available_ut  # Use all 3 UT for movement
    
    # Calculate how far they can move in 3 UT at RUN speed
    seconds_available = ut_for_movement * 3  # 9 seconds
    distance_possible = MovementSpeed.RUN.value * seconds_available  # 5 u/s * 9s = 45 units
    
    # But they only need to go 20 units, so they reach target in 4 UT
    # System response:
    print("You don't have enough time to reach and attack this turn.")
    print(f"You can move {move_ut} UT toward the target, but won't reach them.")
```

---

### **Example 4: Speed Selection Based on Context**

```python
# Stealth scenario - sneaking past guard
if user_wants_stealth:
    speed = MovementSpeed.SNEAK
    print("Moving carefully to avoid detection...")
    
# Combat scenario - closing distance quickly
elif in_combat:
    speed = MovementSpeed.RUN
    print("Sprinting toward the enemy...")
    
# Injured actor - moving slowly
elif actor.is_injured:
    speed = MovementSpeed.CRAWL
    print("Dragging yourself forward painfully...")
    
# Default - normal movement
else:
    speed = MovementSpeed.WALK
    print("Walking toward your destination...")

# Calculate time with selected speed
seconds, ut = ua_pos.calculate_movement_time_with_ut(target_pos, speed)
```

---

## 📊 **DISTANCE CATEGORIES WITH MOVEMENT TIME**

### **At WALK Speed (2 u/s):**

| Category | Range | Movement Time | Example |
|----------|-------|---------------|---------|
| **IMMEDIATE** | 0-2 units | 0-1 seconds (1 UT) | Already there, quick step |
| **CLOSE** | 3-5 units | 1.5-2.5 seconds (1 UT) | Across desk, small room |
| **NEAR** | 6-10 units | 3-5 seconds (1-2 UT) | Across room, hallway |
| **FAR** | 11-20 units | 5.5-10 seconds (2-4 UT) | Large room, parking lot |
| **DISTANT** | 21+ units | 10.5+ seconds (4+ UT) | Different areas, far away |

### **At RUN Speed (5 u/s):**

| Category | Range | Movement Time | Example |
|----------|-------|---------------|---------|
| **IMMEDIATE** | 0-2 units | 0-0.4 seconds (1 UT) | Instant |
| **CLOSE** | 3-5 units | 0.6-1.0 seconds (1 UT) | Quick dash |
| **NEAR** | 6-10 units | 1.2-2.0 seconds (1 UT) | Sprint across room |
| **FAR** | 11-20 units | 2.2-4.0 seconds (1-2 UT) | Run across lot |
| **DISTANT** | 21+ units | 4.2+ seconds (2+ UT) | Long sprint |

---

## 🎯 **GAMEPLAY IMPLICATIONS**

### **1. Action Planning**
```
User: "I whisper to the guard"
System: "The guard is 8 units away. You need to move closer first."
System: "Walking will take 2 UT. Do you want to move closer?"
```

### **2. Time Management**
```
User: "I run to the exit"
System: "The exit is 25 units away. Running will take 5 UT."
System: "You have 3 UT this turn. You'll get partway there."
```

### **3. Speed Choices**
```
User: "I sneak to the door"
System: "Sneaking 10 units will take 4 UT (slower but stealthy)."
User: "I run to the door"
System: "Running 10 units will take 1 UT (faster but noisy)."
```

### **4. Tactical Decisions**
```
User: "I move to cover and shoot"
System: "Cover is 6 units away (1 UT to run). Shooting takes 1 UT."
System: "Total: 2 UT. You have 3 UT available. Proceed?"
```

---

## 🔧 **INTEGRATION WITH UTAS**

### **Movement as Action Component:**

```python
# In main simulation loop

# 1. User declares action
user_input = "I run to the mechanic and whisper about the case"

# 2. Calculate movement time
ua_pos = spatial.get_actor_position("ua_001")
nua_pos = spatial.get_actor_position("nua_001")
move_ut = spatial.get_movement_time("ua_001", nua_pos, speed=MovementSpeed.RUN)

# 3. Calculate action time
whisper_ut = 1  # Whisper takes 1 UT

# 4. Total time
total_ut = move_ut + whisper_ut

# 5. Check if actor has enough time
if total_ut <= actor_available_ut:
    # Execute full action
    spatial.move_actor("ua_001", nua_pos)
    # Process whisper action
else:
    # Partial action or deny
    print(f"Not enough time. Need {total_ut} UT, have {actor_available_ut} UT")
```

---

## 📝 **QUICK REFERENCE**

### **Common Distances:**

| Description | Distance | WALK Time | RUN Time |
|-------------|----------|-----------|----------|
| Touch range | 0-2 units | 0-1 s (1 UT) | 0-0.4 s (1 UT) |
| Across desk | 3-4 units | 1.5-2 s (1 UT) | 0.6-0.8 s (1 UT) |
| Small room | 5-8 units | 2.5-4 s (1-2 UT) | 1-1.6 s (1 UT) |
| Large room | 10-15 units | 5-7.5 s (2-3 UT) | 2-3 s (1 UT) |
| Hallway | 15-20 units | 7.5-10 s (3-4 UT) | 3-4 s (1-2 UT) |
| Parking lot | 20-30 units | 10-15 s (4-5 UT) | 4-6 s (2 UT) |

### **Speed Selection Guide:**

- **CRAWL (0.5 u/s):** Injured, prone, extreme stealth
- **SNEAK (1.0 u/s):** Stealth approach, avoiding detection
- **WALK (2.0 u/s):** Default, casual, normal pace
- **JOG (3.5 u/s):** Hurried, urgent but controlled
- **RUN (5.0 u/s):** Combat, chase, emergency
- **SPRINT (7.0 u/s):** All-out, life or death, maximum effort

---

## 🎉 **SUMMARY**

**Movement time system provides:**
- ⏱️ **Realistic timing** based on distance and speed
- 🏃 **6 speed categories** from crawl to sprint
- 📏 **Distance-based** calculations (units/second)
- 🎯 **UT conversion** (3 seconds = 1 UT)
- 🎮 **Tactical choices** (speed vs stealth)
- ⚖️ **Time management** (partial actions when time runs out)

**Result: Movement has meaningful cost and tactical implications! 🎯**
