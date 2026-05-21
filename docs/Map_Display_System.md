# Map Display System - Visual Spatial Context

## 🗺️ **OVERVIEW**

The Map Display System provides **ASCII art visualization** of spatial context, similar to how you can view actor sheets.

**Command:** `map` or `show map`

---

## 📊 **MAP DISPLAY FEATURES**

### **Shows:**
- ✅ Actor positions (@ for UA, ● for NUA)
- ✅ Obstacles (█ blocks)
- ✅ Grid coordinates (X/Y axis)
- ✅ Zone information
- ✅ Distance categories
- ✅ Line of sight status

---

## 🎮 **USAGE**

### **Basic Command:**
```python
# In main simulation loop
if user_input.lower() in ["map", "show map", "view map"]:
    from spatial_map_display import show_map
    show_map()
```

### **User Types:**
```
> map
```

### **Output Example:**
```
============================================================
MAP: Joe's Garage
Type: interior | Size: 20x15 units
============================================================

Y-axis
  ^
  15 ┌────────────┐
     │            │
     │    ●       │  ● = Vince (mechanic)
  10 │            │
     │  @         │  @ = You
     │            │
   5 │  ████      │  ████ = Counter
     │  ████      │
   0 └────────────┘
      0    5   10  → X-axis

ACTORS:
  @ Detective Morgan at (3.0, 8.0) in Front Area
  ● Vince at (8.0, 12.0) in Bay 1

ZONES:
  • Front Area (room)
  • Bay 1 (area)
  • Bay 2 (area)

OBSTACLES:
  █ Reception Desk (furniture)
  █ 1973 Pontiac (vehicle)

LEGEND:
  @ = User Actor (you)
  ● = Non-User Actor
  █ = Obstacle (blocks movement/sight)
  Scale: 1 character = 2 grid units

============================================================
```

---

## 🎯 **DIFFERENT LOCATION SIZES**

### **Small Office (12x10):**
```
Y-axis
  ^
  10 ┌──────┐
     │      │
   5 │  @   │
     │      │
   0 └──────┘
      0   5  10 → X-axis
```

### **Large Warehouse (50x40):**
```
Y-axis
  ^
  40 ┌─────────────────────────┐
     │                         │
  30 │  ███  ███       ███     │
     │  ███  ███       ███     │
  20 │                         │
     │        @                │
  10 │  ███           ███  ●   │
     │  ███           ███      │
   0 └─────────────────────────┘
      0    10   20   30   40   50 → X-axis
```

### **Narrow Alley (15x40):**
```
Y-axis
  ^
  40 ┌───────┐
     │       │
  30 │   ●   │
     │       │
  20 │       │
     │       │
  10 │   @   │
     │       │
   0 └───────┘
      0   5  10  15 → X-axis
```

---

## 🌳 **OUTDOOR LOCATIONS**

### **Park (80x60):**
```
Y-axis
  ^
  60 ┌────────────────────────────────────────┐
     │                                        │
  50 │    ██                                  │  ██ = Trees
     │         ██      ██                     │
  40 │                                        │
     │                    @                   │
  30 │  ██         ██              ██         │
     │                                        │
  20 │         ██              ██             │
     │                                        │
  10 │    ██                      ██          │
     │                                        │
   0 └────────────────────────────────────────┘
      0    10   20   30   40   50   60   70   80 → X-axis
```

### **Junkyard (70x50):**
```
Y-axis
  ^
  50 ┌───────────────────────────────────┐
     │                                   │
  40 │  ████████                         │  ████ = Scrap piles
     │  ████████        ████████         │
  30 │                  ████████         │
     │        @                          │
  20 │              ████████████         │
     │              ████████████         │
  10 │  ████████                         │
     │  ████████    ●                    │
   0 └───────────────────────────────────┘
      0    10   20   30   40   50   60   70 → X-axis
```

### **Main Street (100x20):**
```
Y-axis
  ^
  20 ┌──────────────────────────────────────────────────┐
     │ SIDEWALK                                         │
  15 ├──────────────────────────────────────────────────┤
     │ ████  ████  ████  ████  ████  ████  ████  ████  │  ████ = Parked cars
  10 │                                                  │
     │ ROAD                    @                        │
   5 ├──────────────────────────────────────────────────┤
     │ SIDEWALK                           ●             │
   0 └──────────────────────────────────────────────────┘
      0    10   20   30   40   50   60   70   80   90  100 → X-axis
```

---

## 🔧 **ADDITIONAL COMMANDS**

### **Compact Map:**
```python
> compact map

# Shows smaller, more condensed view
# Scale: 1 character = 4 grid units
```

### **Distance Check:**
```python
> distance to [actor_name]

# Shows:
# - Distance in units
# - Distance category (immediate/close/near/far/distant)
# - Line of sight status (clear/blocked)
```

**Example:**
```
> distance to Vince

DISTANCE:
  Detective Morgan → Vince
  8.5 units (near)
  Line of sight: Clear
```

---

## 📋 **INTEGRATION INTO MAIN LOOP**

```python
# In redesigned_main.py

from spatial_map_display import show_map, show_compact_map, show_distance

# Main loop
while True:
    user_input = input("What do you want to do? ").strip()
    
    # Map commands
    if user_input.lower() in ["map", "show map", "view map"]:
        show_map()
        continue
    
    if user_input.lower() in ["compact map", "small map"]:
        show_compact_map()
        continue
    
    if user_input.lower().startswith("distance to "):
        target_name = user_input[12:].strip()
        # Find actor by name
        target_id = find_actor_by_name(target_name)
        if target_id:
            show_distance("ua_001", target_id)
        else:
            print(f"Actor '{target_name}' not found")
        continue
    
    # ... rest of action processing
```

---

## 🎨 **CUSTOMIZATION**

### **Scale Adjustment:**
```python
from spatial_map_display import get_map_display

# Larger scale = more compact map
display = get_map_display(scale=4)
display.show_map()

# Smaller scale = more detailed map
display = get_map_display(scale=1)
display.show_map()
```

### **Scale Guide:**
- **Scale 1:** 1 character = 1 unit (very detailed, large maps)
- **Scale 2:** 1 character = 2 units (default, balanced)
- **Scale 4:** 1 character = 4 units (compact, overview)
- **Scale 8:** 1 character = 8 units (very compact, huge locations)

---

## 📊 **MAP SYMBOLS**

| Symbol | Meaning |
|--------|---------|
| `@` | User Actor (you) |
| `●` | Non-User Actor |
| `█` | Obstacle (blocks movement/sight) |
| `│` | Vertical border |
| `─` | Horizontal border |
| `┌┐└┘` | Corners |

---

## 🎯 **USE CASES**

### **1. Tactical Planning**
```
> map
# See where enemies are
# Plan movement path
# Check for cover (obstacles)
```

### **2. Navigation**
```
> map
# See where zones are
# Find exits
# Locate objectives
```

### **3. Distance Assessment**
```
> distance to guard
# Check if in range for action
# Determine movement time needed
```

### **4. Situational Awareness**
```
> map
# See all actors in location
# Check line of sight
# Identify obstacles
```

---

## 🎉 **SUMMARY**

**Map Display System provides:**
- 🗺️ **Visual representation** of spatial context
- 📍 **Actor positions** with clear symbols
- 🚧 **Obstacle locations** and types
- 📏 **Grid coordinates** for reference
- 🎯 **Distance calculations** between actors
- 👁️ **Line of sight** status
- 🏢 **Different sizes** for different locations
- 🌳 **Outdoor support** (parks, streets, junkyards)

**Commands:**
- `map` - Show full map
- `compact map` - Show condensed map
- `distance to [name]` - Check distance to actor

**Result: Visual spatial awareness just like actor sheets! 🗺️**
