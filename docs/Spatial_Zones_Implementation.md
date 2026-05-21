# Spatial Zones - Area Separation System

## 🎯 **THE NEED**

Maps currently show obstacles but **no area separation**:

```
Current Map (No Zones):
   20 ┌───────────────┐
   10 │    ████       │  Just obstacles, no areas
    0 └───────────────┘
```

**What's Missing:**
- **Diner**: Eating area vs counter vs kitchen
- **Garage**: Work area vs office vs storage
- **Street**: Road vs sidewalk vs storefronts
- **Any location**: Functional area separation

---

## ✅ **SOLUTION: VISUAL ZONES**

### **With Zones:**
```
Diner Map (With Zones):
   20 ┌───────────────┐
   18 │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│  ▒ = Kitchen
   15 │───────────────│
   14 │  ████         │  ░ = Eating Area
   10 │░░░░░░░░░░░░░░░│  █ = Counter
    5 │░░░@░░░░░░░░░░░│  @ = You
    0 └───────────────┘

Street Map (With Zones):
   20 ┌───────────────┐
   15 │░░░░░░░░░░░░░░░│  ░ = Sidewalk
   12 │───────────────│
   10 │  ██    ██     │  ▓ = Road
    5 │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  █ = Parked Cars
    3 │───────────────│
    0 │░░@░░░░░░░░░░░░│  @ = You (on sidewalk)
    0 └───────────────┘
```

---

## 🔧 **IMPLEMENTATION PLAN**

### **Step 1: Zone Creation (Already Started)**

The LLM already suggests zones in `spatial_location_analyzer.py`:

```python
"suggested_zones": [
    {
        "name": "Road",
        "description": "Main traffic area",
        "position": "center"
    },
    {
        "name": "Sidewalk",
        "description": "Pedestrian walkway",
        "position": "front"
    }
]
```

### **Step 2: Add Zone Creation to Location Move**

In `redesigned_main.py` after creating location, add zones:

```python
# Add zones from LLM suggestions
from spatial_context_system import Zone
context = spatial.get_current_context()

for zone_data in analysis.get("suggested_zones", [])[:4]:
    zone_name = zone_data.get("name", "Area")
    position_hint = zone_data.get("position", "center")
    
    # Convert position to boundary coordinates
    if position_hint == "front":
        zone = Zone(
            zone_name=zone_name,
            zone_type=zone_data.get("description", "area"),
            boundary_points=[
                Position(0, 0),
                Position(width, 0),
                Position(width, height*0.3),
                Position(0, height*0.3)
            ]
        )
    # ... other positions
    
    context.location_dimensions.zones[zone_name.lower()] = zone
```

### **Step 3: Visualize Zones on Map**

In `spatial_map_display.py`, enhance `_create_grid()`:

```python
def _create_grid(self, dims) -> List[List[str]]:
    # Create base grid
    grid = [[' ' for _ in range(map_width)] for _ in range(map_height)]
    
    # Draw zones FIRST (background)
    for zone in dims.zones.values():
        self._draw_zone(grid, zone, map_width, map_height)
    
    # Draw obstacles (middle layer)
    for obstacle in dims.obstacles.values():
        self._draw_obstacle(grid, obstacle, map_width, map_height)
    
    # Draw actors (top layer)
    for actor_pos in context.actor_positions.values():
        self._draw_actor(grid, actor_pos, map_width, map_height)
    
    return grid

def _draw_zone(self, grid, zone, map_width, map_height):
    """Draw zone with distinctive pattern"""
    # Get zone boundaries
    min_x, max_x, min_y, max_y = zone.get_bounds()
    
    # Choose pattern based on zone type
    patterns = {
        'road': '▓',
        'sidewalk': '░',
        'eating area': '░',
        'kitchen': '▒',
        'office': '▒',
        'work area': '.',
        'storage': '▒'
    }
    
    pattern = patterns.get(zone.zone_type.lower(), '·')
    
    # Fill zone area with pattern
    for y in range(grid_min_y, grid_max_y):
        for x in range(grid_min_x, grid_max_x):
            display_y = map_height - 1 - y
            if 0 <= display_y < map_height and 0 <= x < map_width:
                if grid[display_y][x] == ' ':  # Don't overwrite obstacles/actors
                    grid[display_y][x] = pattern
```

---

## 🎨 **ZONE PATTERNS**

Different patterns for different zone types:

| Zone Type | Pattern | Symbol | Example |
|-----------|---------|--------|---------|
| Road | Dense | `▓` | Street traffic area |
| Sidewalk | Light | `░` | Pedestrian walkway |
| Eating Area | Light | `░` | Diner seating |
| Kitchen | Medium | `▒` | Food prep area |
| Office | Medium | `▒` | Administrative space |
| Work Area | Dots | `.` | Garage work bay |
| Storage | Medium | `▒` | Storage/back room |
| Entrance | Light | `░` | Entry area |

---

## 📊 **EXAMPLE OUTPUTS**

### **Diner with Zones:**
```
MAP: Diner
Type: interior | Size: 25x20 units

   20 ┌─────────────────────────┐
   18 │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│  ▒ = Kitchen
   16 │▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒│
   14 │─────────────────────────│
   12 │░░░░░░░░░░█████░░░░░░░░░│  ░ = Eating Area
   10 │░░░░░░░░░░█████░░░░░░░░░│  █ = Counter
    8 │░░░░░░░░░░█████░░░░░░░░░│
    6 │░░░░░░░░░░░░░░░░░░░░░░░░│
    4 │░░@░░░░░░░░░░░░░░░░░░░░░│  @ = You
    2 │░░░░░░░░░░░░░░░░░░░░░░░░│
    0 └─────────────────────────┘

ZONES:
  ▒ Kitchen (back) - Food preparation area
  ░ Eating Area (center) - Customer seating
  █ Counter (center) - Service counter

ACTORS:
  @ You at (5.0, 4.0) in Eating Area
```

### **Street with Zones:**
```
MAP: Main Street
Type: exterior | Size: 100x20 units

   20 ┌──────────────────────────────────────┐
   18 │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  ░ = Sidewalk
   16 │░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│
   14 │──────────────────────────────────────│
   12 │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  ▓ = Road
   10 │▓▓██▓▓▓▓▓▓▓▓▓▓▓▓▓▓██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│  █ = Parked Cars
    8 │▓▓██▓▓▓▓▓▓▓▓▓▓▓▓▓▓██▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
    6 │▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓│
    4 │──────────────────────────────────────│
    2 │░░@░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  @ = You (on sidewalk)
    0 └──────────────────────────────────────┘

ZONES:
  ░ Sidewalk (front/back) - Pedestrian walkway
  ▓ Road (center) - Vehicle traffic area

ACTORS:
  @ You at (3.0, 2.0) in Sidewalk
```

### **Garage with Zones:**
```
MAP: Garage
Type: interior | Size: 30x25 units

   25 ┌────────────────────────────┐
   23 │▒▒▒▒▒▒▒│.....................│  ▒ = Office
   21 │▒▒▒▒▒▒▒│.....................│  . = Work Area
   19 │▒▒▒▒▒▒▒│.....................│  █ = Equipment
   17 │───────│.....................│
   15 │.......│.....................│
   13 │.......│.....████............│
   11 │.......│.....████............│
    9 │.......│.....................│
    7 │.......│.........@...........│  @ = You
    5 │.......│.....................│
    3 │░░░░░░░░░░░░░░░░░░░░░░░░░░░░│  ░ = Entrance
    0 └────────────────────────────┘

ZONES:
  ▒ Office (left-back) - Administrative area
  . Work Area (center) - Main repair bay
  ░ Entrance (front) - Entry/exit area

ACTORS:
  @ You at (15.0, 7.0) in Work Area
```

---

## 🎯 **BENEFITS**

### **1. Clear Area Identification**
- Know which functional area you're in
- Understand location layout at a glance

### **2. Better Positioning Context**
- "You're in the eating area" vs "You're in the kitchen"
- "You're on the sidewalk" vs "You're in the road"

### **3. Movement Clarity**
- See boundaries between areas
- Understand spatial relationships

### **4. Narrative Consistency**
- Map matches narrative descriptions
- Visual confirmation of location structure

---

## 📋 **IMPLEMENTATION CHECKLIST**

- [x] Enhanced LLM prompt to request zones (spatial_location_analyzer.py)
- [ ] Add zone creation in location move (redesigned_main.py)
- [ ] Add zone creation in initial scene (redesigned_main.py)
- [ ] Implement `_draw_zone()` method (spatial_map_display.py)
- [ ] Add zone patterns dictionary (spatial_map_display.py)
- [ ] Update map legend to show zone patterns
- [ ] Test with various location types

---

## 🚀 **NEXT STEPS**

1. **Add zone creation code** to `redesigned_main.py` (both location move and initial scene)
2. **Implement zone visualization** in `spatial_map_display.py`
3. **Test with different locations**:
   - Diner (eating area, counter, kitchen)
   - Street (road, sidewalk)
   - Garage (work area, office, storage)
   - Bar (seating, bar counter, back room)

**This will make maps much more informative and match the narrative! 🗺️✨**
