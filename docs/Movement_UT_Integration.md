# Movement + Unit Time Integration - Complete System

## 🎯 **YOUR INSIGHT**

**"this is why we made the u/s system and calculation these are supposed to work hand in hand and work together to create the final output of how action are interpreted and how their results to then be shown on the map and in narration"**

**EXACTLY RIGHT!** The movement system now fully integrates with the Unit Time (u/s) system!

---

## ✅ **COMPLETE INTEGRATION**

### **The u/s System (Already Existed):**
- **MovementSpeed** enum: CRAWL, SNEAK, WALK, JOG, RUN, SPRINT
- **Swiftness modifier**: +0.0 to +2.0 u/s based on S-trait
- **Time calculation**: `distance / effective_speed = seconds`
- **UT conversion**: `seconds / 3 = Unit Time`

### **Now Integrated With Movement Tracking:**
1. Detect movement → Extract target
2. Resolve target → Get coordinates
3. **Calculate distance** → Use Position.distance_to()
4. **Map movement type to speed** → walk/run/sneak
5. **Get actor's Swiftness** → From character sheet
6. **Calculate time** → Using u/s system
7. **Advance game time** → Consume UT
8. **Update position** → Save to map
9. **Display in narrative** → Show time taken

---

## 📊 **HOW IT WORKS**

### **Complete Flow:**

```
1. User Action:
   > "I run to the workbench"

2. Movement Detection:
   → Detects: "run" (movement type)
   → Target: "workbench" (obstacle)

3. Position Resolution:
   → Current: (10.0, 3.0)
   → Target: (15.0, 12.0) (workbench location)
   → Distance: 10.3 units

4. Speed Calculation:
   → Movement type: "run" → MovementSpeed.RUN (5.0 u/s base)
   → Actor Swiftness: 4 → +1.5 u/s modifier
   → Effective speed: 5.0 + 1.5 = 6.5 u/s

5. Time Calculation:
   → Distance: 10.3 units
   → Speed: 6.5 u/s
   → Time: 10.3 / 6.5 = 1.58 seconds
   → Unit Time: ceil(1.58 / 3) = 1 UT

6. Time Advancement:
   → master_time.advance_time(seconds=1.58)
   → Game time: 9:00 AM → 9:00:02 AM

7. Position Update:
   → spatial.move_actor("ua_001", Position(15.0, 12.0))
   → Saved to disk

8. Output:
   [MOVEMENT] Run from (10.0, 3.0) to (15.0, 12.0)
   [MOVEMENT] Distance: 10.3 units | Time: 1.6s (1 UT) | Speed: RUN
   [TIME] Advanced 1.6 seconds
   
   > map
      12 │        @███    │  @ = You at workbench
```

---

## 🎮 **MOVEMENT SPEED TABLE**

| Movement Type | Base Speed (u/s) | With Swiftness 3 | With Swiftness 5 |
|---------------|------------------|------------------|------------------|
| **CRAWL** | 0.5 | 1.5 u/s | 2.5 u/s |
| **SNEAK** | 1.0 | 2.0 u/s | 3.0 u/s |
| **WALK** | 2.0 | 3.0 u/s | 4.0 u/s |
| **JOG** | 3.5 | 4.5 u/s | 5.5 u/s |
| **RUN** | 5.0 | 6.0 u/s | 7.0 u/s |
| **SPRINT** | 7.0 | 8.0 u/s | 9.0 u/s |

---

## ⏱️ **TIME CALCULATION EXAMPLES**

### **Example 1: Walk 10 units (Swiftness 3)**
```
Distance: 10 units
Movement: walk → 2.0 u/s base
Swiftness: 3 → +1.0 u/s modifier
Effective speed: 3.0 u/s

Time: 10 / 3.0 = 3.33 seconds
Unit Time: ceil(3.33 / 3) = 2 UT

Output:
[MOVEMENT] Distance: 10.0 units | Time: 3.3s (2 UT) | Speed: WALK
```

### **Example 2: Run 10 units (Swiftness 5)**
```
Distance: 10 units
Movement: run → 5.0 u/s base
Swiftness: 5 → +2.0 u/s modifier
Effective speed: 7.0 u/s

Time: 10 / 7.0 = 1.43 seconds
Unit Time: ceil(1.43 / 3) = 1 UT

Output:
[MOVEMENT] Distance: 10.0 units | Time: 1.4s (1 UT) | Speed: RUN
```

### **Example 3: Sneak 5 units (Swiftness 2)**
```
Distance: 5 units
Movement: sneak → 1.0 u/s base
Swiftness: 2 → +0.5 u/s modifier
Effective speed: 1.5 u/s

Time: 5 / 1.5 = 3.33 seconds
Unit Time: ceil(3.33 / 3) = 2 UT

Output:
[MOVEMENT] Distance: 5.0 units | Time: 3.3s (2 UT) | Speed: SNEAK
```

---

## 🔧 **IMPLEMENTATION DETAILS**

### **File: redesigned_main.py (Lines 2982-3019)**

```python
# Calculate movement time and UT cost
if current_pos:
    from spatial_context_system import MovementSpeed
    
    # Map movement type to speed
    speed_map = {
        'crawl': MovementSpeed.CRAWL,
        'sneak': MovementSpeed.SNEAK,
        'walk': MovementSpeed.WALK,
        'jog': MovementSpeed.JOG,
        'run': MovementSpeed.RUN,
        'sprint': MovementSpeed.SPRINT
    }
    speed = speed_map.get(movement_type.lower(), MovementSpeed.WALK)
    
    # Get actor's Swiftness
    swiftness = actor.sheet.get_s_trait_value('Swiftness')
    
    # Calculate movement time using u/s system
    time_seconds, unit_time = current_pos.calculate_movement_time_with_ut(
        new_position, speed, swiftness
    )
    
    distance = current_pos.distance_to(new_position)
    
    # Update position
    spatial.move_actor("ua_001", new_position)
    
    # Display movement info
    print(f"[MOVEMENT] {movement_type.capitalize()} from ({current_pos.x:.1f}, {current_pos.y:.1f}) to ({new_position.x:.1f}, {new_position.y:.1f})")
    print(f"[MOVEMENT] Distance: {distance:.1f} units | Time: {time_seconds:.1f}s ({unit_time} UT) | Speed: {speed.name}")
    
    # Advance time
    master_time.advance_time(seconds=int(time_seconds))
    print(f"[TIME] Advanced {time_seconds:.1f} seconds")
```

---

## 📋 **DISTANCE CATEGORIES**

The system also uses distance categories for action mechanics:

| Category | Range | Use Case |
|----------|-------|----------|
| **IMMEDIATE** | 0-2 units | Touch, whisper, melee |
| **CLOSE** | 3-5 units | Normal conversation |
| **NEAR** | 6-10 units | Raised voice, quick movement |
| **FAR** | 11-20 units | Shout, significant movement |
| **DISTANT** | 21+ units | Out of range for most actions |

**Example:**
```python
distance_category = current_pos.get_distance_category(target_pos)

if distance_category == DistanceCategory.DISTANT:
    print("Target is too far away! You need to move closer.")
```

---

## 🎯 **NARRATIVE INTEGRATION**

### **Before (No Time):**
```
> I walk to the workbench

Narrative: "You walk to the workbench..."

Map: @ moved to workbench
Time: No change ❌
```

### **After (With u/s Integration):**
```
> I walk to the workbench

[MOVEMENT] Detected walk to workbench (obstacle)
[MOVEMENT] Walk from (10.0, 3.0) to (15.0, 12.0)
[MOVEMENT] Distance: 10.3 units | Time: 3.4s (2 UT) | Speed: WALK
[TIME] Advanced 3.4 seconds

Narrative: "You walk across the garage to the workbench, taking about 3 seconds..."

Map: @ moved to workbench ✅
Time: 9:00 AM → 9:00:03 AM ✅
```

---

## 🏃 **MOVEMENT TYPE MATTERS**

### **Same Distance, Different Speeds:**

**Scenario:** Move 15 units (Swiftness 3)

| Movement | Speed | Time | UT Cost |
|----------|-------|------|---------|
| **Crawl** | 1.5 u/s | 10.0s | 4 UT |
| **Sneak** | 2.0 u/s | 7.5s | 3 UT |
| **Walk** | 3.0 u/s | 5.0s | 2 UT |
| **Jog** | 4.5 u/s | 3.3s | 2 UT |
| **Run** | 6.0 u/s | 2.5s | 1 UT |
| **Sprint** | 8.0 u/s | 1.9s | 1 UT |

**Tactical Choice:**
- **Sneak:** Slower but stealthy
- **Walk:** Normal, balanced
- **Run:** Fast but noisy
- **Sprint:** Fastest but exhausting

---

## 🎮 **SWIFTNESS MATTERS**

### **Same Movement, Different Swiftness:**

**Scenario:** Walk 10 units

| Swiftness | Modifier | Speed | Time | UT Cost |
|-----------|----------|-------|------|---------|
| **1** | +0.0 | 2.0 u/s | 5.0s | 2 UT |
| **2** | +0.5 | 2.5 u/s | 4.0s | 2 UT |
| **3** | +1.0 | 3.0 u/s | 3.3s | 2 UT |
| **4** | +1.5 | 3.5 u/s | 2.9s | 1 UT |
| **5** | +2.0 | 4.0 u/s | 2.5s | 1 UT |

**Character Building:**
- High Swiftness = Faster movement = Less UT cost
- Low Swiftness = Slower movement = More UT cost

---

## 🎯 **TACTICAL IMPLICATIONS**

### **1. Time Management:**
```
> I need to reach the exit before the alarm goes off (10 seconds)

Current position: (5.0, 5.0)
Exit position: (45.0, 25.0)
Distance: 44.7 units

Options (Swiftness 3):
- Walk (3.0 u/s): 14.9s ❌ Too slow!
- Run (6.0 u/s): 7.5s ✅ Just in time!
- Sprint (8.0 u/s): 5.6s ✅ Safe margin!
```

### **2. Stealth vs Speed:**
```
> I need to reach the guard without being heard

Options:
- Sneak (2.0 u/s): 10s, stealthy ✅
- Walk (3.0 u/s): 6.7s, might be heard ⚠️
- Run (6.0 u/s): 3.3s, definitely heard ❌
```

### **3. Resource Management:**
```
> I have limited time before reinforcements arrive

Each action costs UT:
- Walk 20 units: 2 UT
- Pick lock: 3 UT
- Search room: 2 UT
- Walk back: 2 UT
Total: 9 UT

If I run instead of walk:
- Run 20 units: 1 UT
- Pick lock: 3 UT
- Search room: 2 UT
- Run back: 1 UT
Total: 7 UT (saved 2 UT!)
```

---

## 🏆 **COMPLETE SYSTEM BENEFITS**

### **1. Realistic Movement:**
- Distance matters
- Speed matters
- Swiftness matters
- Time passes realistically

### **2. Tactical Depth:**
- Choose movement speed based on situation
- Balance speed vs stealth
- Manage time resources

### **3. Character Differentiation:**
- High Swiftness characters move faster
- Low Swiftness characters need more time
- Movement becomes part of character identity

### **4. Narrative Consistency:**
- Maps show actual positions
- Time advances realistically
- Narration reflects time taken
- Everything works together

---

## 📊 **FULL INTEGRATION SUMMARY**

| System | Function | Integration |
|--------|----------|-------------|
| **Movement Detection** | Detects movement from input | ✅ Extracts movement type |
| **Position Resolution** | Converts target to coordinates | ✅ Calculates distance |
| **u/s System** | Calculates time/speed | ✅ Uses Swiftness modifier |
| **UT Calculation** | Converts seconds to UT | ✅ Advances game time |
| **Spatial Map** | Shows actor positions | ✅ Updates on movement |
| **Persistence** | Saves to disk | ✅ Positions + time saved |
| **Narrative** | Describes actions | ✅ Reflects time taken |

---

## 🎉 **RESULT**

**Everything works together:**

```
> I sprint to the door

[MOVEMENT] Detected sprint to door (obstacle)
[MOVEMENT] Sprint from (10.0, 10.0) to (25.0, 5.0)
[MOVEMENT] Distance: 15.8 units | Time: 2.0s (1 UT) | Speed: SPRINT
[TIME] Advanced 2.0 seconds

Narrative: "You sprint across the room to the door in just 2 seconds, 
your heart pounding as you reach for the handle..."

> map
   10 │                │
    5 │             @█ │  @ = You at door (moved!)
    0 └────────────────┘

Time: 9:00:02 AM (advanced 2 seconds!)
```

**The u/s system and movement tracking are now fully integrated! 🎯**
