# Swiftness Movement Modifier System

## 🎯 **CORE CONCEPT**

**Swiftness S-trait affects movement speed!**

Actors with higher Swiftness move faster, completing the same distance in less time.

---

## 📊 **SWIFTNESS MODIFIER TABLE**

| Swiftness | Speed Bonus | Description |
|-----------|-------------|-------------|
| **1** | +0.0 u/s | No bonus (slow/clumsy) |
| **2** | +0.5 u/s | Slightly faster |
| **3** | +1.0 u/s | Average speed boost |
| **4** | +1.5 u/s | Noticeably faster |
| **5** | +2.0 u/s | Exceptional speed |

**Formula:** `bonus = (swiftness - 1) × 0.5`

---

## 🏃 **EFFECTIVE SPEED CALCULATION**

### **Base Speed + Swiftness Modifier = Effective Speed**

```
Effective Speed = Base Speed + Swiftness Bonus
```

### **Examples:**

#### **Walking (Base: 2.0 u/s)**

| Swiftness | Calculation | Effective Speed | Time for 10 units |
|-----------|-------------|-----------------|-------------------|
| 1 | 2.0 + 0.0 | 2.0 u/s | 5.0 seconds (2 UT) |
| 2 | 2.0 + 0.5 | 2.5 u/s | 4.0 seconds (2 UT) |
| 3 | 2.0 + 1.0 | 3.0 u/s | 3.3 seconds (2 UT) |
| 4 | 2.0 + 1.5 | 3.5 u/s | 2.9 seconds (1 UT) |
| 5 | 2.0 + 2.0 | 4.0 u/s | 2.5 seconds (1 UT) |

#### **Running (Base: 5.0 u/s)**

| Swiftness | Calculation | Effective Speed | Time for 20 units |
|-----------|-------------|-----------------|-------------------|
| 1 | 5.0 + 0.0 | 5.0 u/s | 4.0 seconds (2 UT) |
| 2 | 5.0 + 0.5 | 5.5 u/s | 3.6 seconds (2 UT) |
| 3 | 5.0 + 1.0 | 6.0 u/s | 3.3 seconds (2 UT) |
| 4 | 5.0 + 1.5 | 6.5 u/s | 3.1 seconds (2 UT) |
| 5 | 5.0 + 2.0 | 7.0 u/s | 2.9 seconds (1 UT) |

#### **Sprinting (Base: 7.0 u/s)**

| Swiftness | Calculation | Effective Speed | Time for 20 units |
|-----------|-------------|-----------------|-------------------|
| 1 | 7.0 + 0.0 | 7.0 u/s | 2.9 seconds (1 UT) |
| 2 | 7.0 + 0.5 | 7.5 u/s | 2.7 seconds (1 UT) |
| 3 | 7.0 + 1.0 | 8.0 u/s | 2.5 seconds (1 UT) |
| 4 | 7.0 + 1.5 | 8.5 u/s | 2.4 seconds (1 UT) |
| 5 | 7.0 + 2.0 | 9.0 u/s | 2.2 seconds (1 UT) |

---

## 🎮 **USAGE EXAMPLES**

### **Example 1: Comparing Two Actors**

**Scenario:** Both actors walk 10 units

**Actor A (Swiftness 1 - Clumsy):**
```python
from spatial_context_system import Position, MovementSpeed

start = Position(0, 0)
target = Position(10, 0)

seconds, ut = start.calculate_movement_time_with_ut(
    target, 
    MovementSpeed.WALK, 
    swiftness=1
)

print(f"Actor A: {seconds:.1f}s = {ut} UT")
# Output: "Actor A: 5.0s = 2 UT"
```

**Actor B (Swiftness 5 - Swift):**
```python
seconds, ut = start.calculate_movement_time_with_ut(
    target, 
    MovementSpeed.WALK, 
    swiftness=5
)

print(f"Actor B: {seconds:.1f}s = {ut} UT")
# Output: "Actor B: 2.5s = 1 UT"
```

**Result:** Actor B reaches the target **1 UT faster!**

---

### **Example 2: Chase Scenario**

**Scenario:** Detective (Swiftness 4) chasing Thug (Swiftness 2)

**Thug runs 15 units away:**
```python
# Thug (Swiftness 2) running
thug_speed = get_effective_speed(MovementSpeed.RUN, swiftness=2)
# 5.0 + 0.5 = 5.5 u/s

thug_time = 15 / 5.5  # 2.73 seconds = 1 UT
```

**Detective chases:**
```python
# Detective (Swiftness 4) running
detective_speed = get_effective_speed(MovementSpeed.RUN, swiftness=4)
# 5.0 + 1.5 = 6.5 u/s

detective_time = 15 / 6.5  # 2.31 seconds = 1 UT
```

**Result:** Both take 1 UT, but detective is **0.42 seconds faster** (might matter for close calls!)

---

### **Example 3: Tactical Movement**

**Scenario:** Need to reach cover 12 units away in 1 UT (3 seconds)

**Actor with Swiftness 3:**
```python
# Can they make it walking?
walk_speed = get_effective_speed(MovementSpeed.WALK, swiftness=3)
# 2.0 + 1.0 = 3.0 u/s

distance_in_3s = 3.0 * 3  # 9 units
# NO - only covers 9 units, needs 12
```

```python
# Can they make it running?
run_speed = get_effective_speed(MovementSpeed.RUN, swiftness=3)
# 5.0 + 1.0 = 6.0 u/s

distance_in_3s = 6.0 * 3  # 18 units
# YES - covers 18 units, more than enough!
```

**Result:** Must RUN to reach cover in time.

---

### **Example 4: Swiftness Makes the Difference**

**Scenario:** 8 units to cover, 1 UT available

**Low Swiftness Actor (Swiftness 2):**
```python
walk_speed = get_effective_speed(MovementSpeed.WALK, swiftness=2)
# 2.0 + 0.5 = 2.5 u/s

distance_in_3s = 2.5 * 3  # 7.5 units
# FAILS - only 7.5 units, needs 8
```

**High Swiftness Actor (Swiftness 4):**
```python
walk_speed = get_effective_speed(MovementSpeed.WALK, swiftness=4)
# 2.0 + 1.5 = 3.5 u/s

distance_in_3s = 3.5 * 3  # 10.5 units
# SUCCESS - covers 10.5 units, reaches target!
```

**Result:** Swiftness 4 actor makes it, Swiftness 2 actor doesn't!

---

## 📊 **COMPLETE SPEED TABLE**

### **All Base Speeds with Swiftness Modifiers**

| Base Speed | Swift 1 | Swift 2 | Swift 3 | Swift 4 | Swift 5 |
|------------|---------|---------|---------|---------|---------|
| **CRAWL** (0.5) | 0.5 | 1.0 | 1.5 | 2.0 | 2.5 |
| **SNEAK** (1.0) | 1.0 | 1.5 | 2.0 | 2.5 | 3.0 |
| **WALK** (2.0) | 2.0 | 2.5 | 3.0 | 3.5 | 4.0 |
| **JOG** (3.5) | 3.5 | 4.0 | 4.5 | 5.0 | 5.5 |
| **RUN** (5.0) | 5.0 | 5.5 | 6.0 | 6.5 | 7.0 |
| **SPRINT** (7.0) | 7.0 | 7.5 | 8.0 | 8.5 | 9.0 |

---

## 🔧 **IMPLEMENTATION**

### **Core Functions:**

```python
def calculate_swiftness_modifier(swiftness: int) -> float:
    """
    Calculate speed bonus from Swiftness.
    
    Args:
        swiftness: 1-5
    
    Returns:
        Bonus in u/s
    """
    swiftness = max(1, min(5, swiftness))
    bonus = (swiftness - 1) * 0.5
    return bonus


def get_effective_speed(base_speed: MovementSpeed, swiftness: int) -> float:
    """
    Get effective speed with Swiftness modifier.
    
    Args:
        base_speed: Base movement speed
        swiftness: Actor's Swiftness (1-5)
    
    Returns:
        Effective speed in u/s
    """
    base = base_speed.value
    modifier = calculate_swiftness_modifier(swiftness)
    return base + modifier
```

### **Usage in Movement Calculations:**

```python
# In Position.calculate_movement_time()
distance = self.distance_to(target)
effective_speed = get_effective_speed(speed, swiftness)
time_seconds = distance / effective_speed
```

---

## 🎯 **GAMEPLAY IMPLICATIONS**

### **1. Character Differentiation**

**Swiftness 1 (Slow):**
- Elderly characters
- Injured/exhausted
- Heavy armor/equipment
- Poor physical condition

**Swiftness 3 (Average):**
- Most characters
- Standard fitness level
- Normal conditions

**Swiftness 5 (Swift):**
- Athletes
- Trained runners
- Light/agile characters
- Peak physical condition

### **2. Tactical Decisions**

**High Swiftness Advantages:**
- ✅ Reach cover faster
- ✅ Close distance to enemies quicker
- ✅ Escape more effectively
- ✅ Complete movement + action in same turn

**Low Swiftness Disadvantages:**
- ❌ Takes longer to reach objectives
- ❌ May need to RUN instead of WALK
- ❌ More vulnerable during movement
- ❌ May only partially complete actions

### **3. Chase Mechanics**

```
Pursuer Swiftness > Target Swiftness = Gains ground
Pursuer Swiftness < Target Swiftness = Loses ground
Pursuer Swiftness = Target Swiftness = Maintains distance
```

### **4. Time Pressure**

**Example:** Bomb will explode in 2 UT, exit is 15 units away

- **Swiftness 1 + WALK:** 15 / 2.0 = 7.5s = 3 UT ❌ **TOO SLOW**
- **Swiftness 1 + RUN:** 15 / 5.0 = 3.0s = 1 UT ✅ **MAKES IT**
- **Swiftness 5 + WALK:** 15 / 4.0 = 3.75s = 2 UT ✅ **MAKES IT**

High Swiftness can WALK where low Swiftness must RUN!

---

## 📝 **INTEGRATION CHECKLIST**

### **Systems Updated:**

- ✅ `spatial_context_system.py` - Core functions added
- ✅ `Position.calculate_movement_time()` - Accepts swiftness parameter
- ✅ `Position.calculate_movement_time_with_ut()` - Accepts swiftness parameter
- ✅ `SpatialContextManager.get_movement_time()` - Accepts swiftness parameter
- ✅ `partial_action_system.py` - Uses swiftness in calculations

### **Usage Pattern:**

```python
# Get actor's Swiftness from actor sheet
swiftness = actor.s_factors.swiftness

# Calculate movement time with Swiftness
seconds, ut = position.calculate_movement_time_with_ut(
    target, 
    speed=MovementSpeed.WALK,
    swiftness=swiftness  # ← Use actor's Swiftness
)
```

---

## 🎉 **SUMMARY**

**Swiftness modifier provides:**
- 📊 **Meaningful differentiation** between characters
- ⚡ **Speed advantage** for high Swiftness actors
- 🎯 **Tactical depth** in movement decisions
- ⏱️ **Time management** implications
- 🏃 **Realistic chase** mechanics
- 🎭 **Character flavor** (swift vs clumsy)

**Formula:**
```
Effective Speed = Base Speed + (Swiftness - 1) × 0.5
```

**Result: Swiftness S-trait now meaningfully affects movement! 🎯**
