# Dynamic Spatial Analysis - LLM-Powered Location Dimensions

## 🤖 **NO MORE HARDCODING!**

The spatial system now uses **LLM analysis** to automatically determine appropriate dimensions for any location based on the scene description!

---

## 🎯 **HOW IT WORKS**

### **Before (Hardcoded):**
```python
if label == 'diner':
    width, height = 25, 20  # ❌ Fixed for all diners
elif label == 'street':
    width, height = 100, 20  # ❌ All streets same size
else:
    width, height = 20, 15  # ❌ Generic default
```

### **After (Dynamic):**
```python
# LLM analyzes the scene description
analysis = analyze_scene_for_spatial(scene_description, location_name)

width = analysis["width"]    # ✅ Determined by LLM
height = analysis["height"]  # ✅ Based on scene details
loc_type = analysis["location_type"]  # ✅ interior/exterior
```

---

## 📊 **WHAT THE LLM ANALYZES**

### **Input:**
- **Scene Description:** Full narrative text
- **Location Name:** Label/name of the location

### **Output:**
```json
{
    "width": 30,
    "height": 25,
    "location_type": "interior",
    "reasoning": "Large diner with multiple booth sections and a long counter",
    "suggested_zones": [
        {"name": "Dining Area", "description": "Booths and tables", "position": "front"},
        {"name": "Counter", "description": "Bar seating", "position": "center"},
        {"name": "Kitchen Door", "description": "Staff area", "position": "back"}
    ],
    "suggested_obstacles": [
        {"name": "Counter", "type": "furniture", "position": "center", "blocks_movement": true},
        {"name": "Booth Seating", "type": "furniture", "position": "left", "blocks_movement": true}
    ]
}
```

---

## 🎮 **EXAMPLE SCENARIOS**

### **Scenario 1: Small Cramped Office**

**Scene Description:**
```
You stand in a cramped detective office barely larger than a closet. 
A single desk is wedged against the wall, covered in case files. 
A filing cabinet blocks the narrow path to the window.
```

**LLM Analysis:**
```json
{
    "width": 12,
    "height": 8,
    "location_type": "interior",
    "reasoning": "Cramped office described as 'barely larger than a closet' with limited space"
}
```

**Result:**
```
MAP: Detective Office
Type: interior | Size: 12x8 units (SMALL!)

   8 ┌──────┐
     │      │
   4 │  @   │
     │      │
   0 └──────┘
```

---

### **Scenario 2: Spacious Warehouse**

**Scene Description:**
```
You enter a massive abandoned warehouse. The ceiling stretches 
high above, supported by rusted metal beams. Rows of empty 
shelving units extend into the darkness. The space echoes with 
every footstep.
```

**LLM Analysis:**
```json
{
    "width": 60,
    "height": 45,
    "location_type": "interior",
    "reasoning": "Massive warehouse with high ceilings and rows of shelving extending into distance"
}
```

**Result:**
```
MAP: Warehouse
Type: interior | Size: 60x45 units (HUGE!)

  45 ┌──────────────────────────────┐
     │                              │
  30 │                              │
     │                              │
  15 │              @               │
     │                              │
   0 └──────────────────────────────┘
```

---

### **Scenario 3: Narrow Alley**

**Scene Description:**
```
You slip into a narrow alley between two buildings. Barely wide 
enough for two people to pass, it stretches deep into the block. 
Dumpsters line one wall, and a fire escape dangles overhead.
```

**LLM Analysis:**
```json
{
    "width": 15,
    "height": 40,
    "location_type": "exterior",
    "reasoning": "Narrow alley (barely wide enough for two people) but stretches deep into the block"
}
```

**Result:**
```
MAP: Alley
Type: exterior | Size: 15x40 units (NARROW & LONG!)

  40 ┌───────┐
     │       │
  30 │       │
     │       │
  20 │   @   │
     │       │
  10 │       │
     │       │
   0 └───────┘
```

---

## 🎨 **LLM DECISION FACTORS**

### **Width Determination:**
- **Keywords:** "cramped", "narrow", "wide", "spacious", "massive"
- **Objects:** Number and size of furniture/obstacles
- **Function:** Office vs warehouse vs street

### **Height Determination:**
- **Keywords:** "deep", "long", "extends", "stretches"
- **Layout:** Corridor vs open room
- **Description:** "barely larger than closet" vs "rows extending into darkness"

### **Location Type:**
- **Interior:** Rooms, buildings, enclosed spaces
- **Exterior:** Streets, alleys, parks, outdoor areas

---

## 📋 **DIMENSION GUIDELINES**

The LLM follows these guidelines:

| Space Type | Width Range | Height Range |
|------------|-------------|--------------|
| **Small Room/Office** | 10-20 units | 10-15 units |
| **Medium Room/Shop** | 20-30 units | 15-25 units |
| **Large Room/Warehouse** | 40-60 units | 30-50 units |
| **Narrow Corridor** | 10-15 units | 20-40 units |
| **Street/Outdoor** | 80-120 units | 20-30 units |

**Safety Limits:**
- Minimum: 10x10 units
- Maximum: 150x100 units

---

## 🔧 **IMPLEMENTATION**

### **New File:** `spatial_location_analyzer.py`

**Key Components:**

1. **SpatialLocationAnalyzer Class:**
   - Uses LLM to analyze scenes
   - Returns dimensions, type, zones, obstacles
   - Includes safety validation

2. **analyze_scene_for_spatial() Function:**
   - Quick convenience function
   - Takes scene description and location name
   - Returns full analysis dict

3. **LLM Prompt:**
   - Detailed examples for different location types
   - Clear dimension guidelines
   - JSON response format

---

## 🎯 **INTEGRATION**

### **Initial Scene Creation:**
```python
# Line 1772-1822 in redesigned_main.py
analysis = analyze_scene_for_spatial(scene_description, location_name)
width = analysis["width"]
height = analysis["height"]
loc_type = analysis["location_type"]

spatial.create_location(location_name, width, height, loc_type)
```

### **Location Changes:**
```python
# Line 848-881 in redesigned_main.py
analysis = analyze_scene_for_spatial(new_desc, label)
width = analysis["width"]
height = analysis["height"]
loc_type = analysis["location_type"]

spatial.create_location(label.title(), width, height, loc_type)
```

---

## 💡 **BENEFITS**

### **1. Contextual Accuracy**
- Small cramped office → 12x8
- Massive warehouse → 60x45
- Narrow alley → 15x40
- **Each location sized appropriately!**

### **2. Narrative Consistency**
- Scene says "cramped" → Map is small
- Scene says "massive" → Map is huge
- **Visual matches description!**

### **3. No Maintenance**
- No hardcoded rules to update
- Works for ANY location type
- **LLM adapts automatically!**

### **4. Future-Proof**
- New location types? No problem!
- Unusual spaces? LLM handles it!
- **Infinitely flexible!**

---

## 🎉 **EXAMPLE OUTPUT**

### **When Scene Starts:**
```
[SPATIAL] Analyzing initial location: Newsroom
[SPATIAL] Setting current location: Newsroom
[SPATIAL] Adding UA: Marcus Holloway
✓ Location 'Newsroom' created (35x25 interior) with UA at center
[SPATIAL] Reasoning: Medium-sized newsroom with multiple desks and a bulletin board area
```

### **When Location Changes:**
```
> I go to the diner

[SPATIAL] Analyzing location dimensions...
✓ Moved to 'Diner' (28x22 interior)
[SPATIAL] Reasoning: Cozy diner with booth seating and counter area
```

---

## 🎯 **SUMMARY**

**Dynamic Spatial Analysis:**

✅ **LLM-powered** - Analyzes scene descriptions
✅ **Context-aware** - Sizes based on narrative details
✅ **No hardcoding** - Works for any location
✅ **Narrative consistency** - Visual matches description
✅ **Automatic** - No manual configuration needed
✅ **Flexible** - Handles unusual spaces
✅ **Future-proof** - Adapts to new location types

**Result: Every location gets appropriate dimensions based on its actual description! 🗺️🤖**
