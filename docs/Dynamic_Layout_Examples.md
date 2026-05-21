# Dynamic Layout System - Examples & Templates

## 🎯 **DYNAMIC LAYOUTS - NOT JUST SQUARES!**

The spatial system now supports **irregular shapes**, **zones**, and **obstacles** for realistic location layouts.

---

## 📐 **LAYOUT COMPONENTS**

### **1. Zones (Named Areas)**
- Define irregular polygons for different areas
- "Bar area", "back room", "parking lot", "alley", etc.
- Actors can be in specific zones

### **2. Obstacles (Physical Barriers)**
- Walls, furniture, vehicles, counters
- Block movement and/or line of sight
- Enable cover mechanics

### **3. Bounding Box**
- Overall width × height (for reference)
- Zones and obstacles exist within this space

---

## 🏪 **EXAMPLE 1: L-SHAPED CONVENIENCE STORE**

```
Y-axis
^
|  20 ┌─────────────────────────────┐
|     │ BACK ROOM    │              │
|     │   (storage)  │              │
|  15 │              │   AISLES     │
|     │──────────────┤              │
|     │                             │
|  10 │         ████████            │  ████ = Counter (obstacle)
|     │         ████████            │
|     │                             │
|   5 │    FRONT AREA               │
|     │    (checkout)               │
|   0 └─────────────────────────────┘
     0    5    10   15   20   25  → X-axis
```

### **Code:**
```python
from spatial_context_system import get_spatial_manager, Position, Zone, Obstacle

spatial = get_spatial_manager()

# Create location with bounding box
spatial.create_location(
    location_name="24-Hour Mart",
    width=25,
    height=20,
    location_type="interior",
    description="L-shaped convenience store with back storage room"
)

spatial.set_current_location("24-Hour Mart")
context = spatial.get_current_context()
dims = context.location_dimensions

# Define FRONT AREA zone (irregular polygon)
front_zone = Zone(
    zone_name="Front Area",
    zone_type="room",
    boundary_points=[
        Position(0, 0),    # Bottom-left
        Position(25, 0),   # Bottom-right
        Position(25, 10),  # Right side up to counter
        Position(0, 10)    # Left side up to counter
    ],
    description="Checkout area with front entrance"
)
dims.zones["front_area"] = front_zone

# Define AISLES zone
aisles_zone = Zone(
    zone_name="Aisles",
    zone_type="area",
    boundary_points=[
        Position(12, 10),  # Start after counter
        Position(25, 10),  # Right wall
        Position(25, 20),  # Top-right
        Position(12, 20),  # Top-left
        Position(12, 15)   # Back to counter level
    ],
    description="Shopping aisles with shelves"
)
dims.zones["aisles"] = aisles_zone

# Define BACK ROOM zone
back_room_zone = Zone(
    zone_name="Back Room",
    zone_type="room",
    boundary_points=[
        Position(0, 15),   # Bottom-left
        Position(12, 15),  # Bottom-right (door to aisles)
        Position(12, 20),  # Top-right
        Position(0, 20)    # Top-left
    ],
    description="Storage room with employee entrance"
)
dims.zones["back_room"] = back_room_zone

# Add COUNTER obstacle (blocks movement, partial line of sight)
counter = Obstacle(
    obstacle_name="Checkout Counter",
    obstacle_type="counter",
    boundary_points=[
        Position(8, 9),
        Position(16, 9),
        Position(16, 11),
        Position(8, 11)
    ],
    blocks_movement=True,
    blocks_line_of_sight=False,  # Can see over counter
    height=1.0  # Low obstacle
)
dims.obstacles["counter"] = counter

# Add SHELVES obstacles
shelf_1 = Obstacle(
    obstacle_name="Shelf Unit 1",
    obstacle_type="furniture",
    boundary_points=[
        Position(14, 12),
        Position(16, 12),
        Position(16, 18),
        Position(14, 18)
    ],
    blocks_movement=True,
    blocks_line_of_sight=True,
    height=2.0
)
dims.obstacles["shelf_1"] = shelf_1

shelf_2 = Obstacle(
    obstacle_name="Shelf Unit 2",
    obstacle_type="furniture",
    boundary_points=[
        Position(18, 12),
        Position(20, 12),
        Position(20, 18),
        Position(18, 18)
    ],
    blocks_movement=True,
    blocks_line_of_sight=True,
    height=2.0
)
dims.obstacles["shelf_2"] = shelf_2

# Add possible actors
spatial.add_possible_actor(
    actor_id="clerk_001",
    actor_name="Night Clerk",
    actor_type="NUA",
    brief_description="Tired clerk working the graveyard shift",
    narrative_role="neutral",
    introduction_triggers=["clerk", "cashier", "counter", "checkout"]
)

spatial.add_possible_actor(
    actor_id="customer_001",
    actor_name="Suspicious Customer",
    actor_type="NUA",
    brief_description="Nervous person browsing the aisles",
    narrative_role="antagonist",
    introduction_triggers=["customer", "aisles", "shopping", "browsing"]
)

# Add UA
spatial.add_actor("ua_001", "Detective Morgan", Position(3, 3), is_user_actor=True)

# Check what zone UA is in
zone = dims.get_zone_at_position(Position(3, 3))
print(f"UA is in: {zone.zone_name}")  # "Front Area"
```

---

## 🏢 **EXAMPLE 2: OFFICE WITH CUBICLES**

```
Y-axis
^
|  20 ┌───────────────────────────────┐
|     │  MANAGER    │                 │
|     │   OFFICE    │   CONFERENCE    │
|  15 │             │     ROOM        │
|     ├─────────────┼─────────────────┤
|     │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │  ▓▓▓ = Cubicles
|  10 │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │ ▓▓▓ │
|     │     │     │     │     │     │
|   5 │  OPEN CUBICLE AREA           │
|     │                               │
|   0 └───────────────────────────────┘
     0    5    10   15   20   25   30 → X-axis
```

### **Code:**
```python
spatial.create_location(
    location_name="Corporate Office",
    width=30,
    height=20,
    location_type="interior",
    description="Modern office with cubicles and private offices"
)

spatial.set_current_location("Corporate Office")
context = spatial.get_current_context()
dims = context.location_dimensions

# Define zones
cubicle_area = Zone(
    zone_name="Cubicle Area",
    zone_type="area",
    boundary_points=[
        Position(0, 0),
        Position(30, 0),
        Position(30, 15),
        Position(0, 15)
    ],
    description="Open area with cubicle workstations"
)
dims.zones["cubicle_area"] = cubicle_area

manager_office = Zone(
    zone_name="Manager Office",
    zone_type="room",
    boundary_points=[
        Position(0, 15),
        Position(12, 15),
        Position(12, 20),
        Position(0, 20)
    ],
    description="Private office with door"
)
dims.zones["manager_office"] = manager_office

conference_room = Zone(
    zone_name="Conference Room",
    zone_type="room",
    boundary_points=[
        Position(12, 15),
        Position(30, 15),
        Position(30, 20),
        Position(12, 20)
    ],
    description="Glass-walled conference room"
)
dims.zones["conference_room"] = conference_room

# Add cubicle obstacles (5 cubicles)
for i in range(5):
    x_start = 2 + (i * 6)
    cubicle = Obstacle(
        obstacle_name=f"Cubicle {i+1}",
        obstacle_type="furniture",
        boundary_points=[
            Position(x_start, 8),
            Position(x_start + 4, 8),
            Position(x_start + 4, 13),
            Position(x_start, 13)
        ],
        blocks_movement=True,
        blocks_line_of_sight=False,  # Low cubicle walls
        height=1.5
    )
    dims.obstacles[f"cubicle_{i+1}"] = cubicle

# Add conference table
table = Obstacle(
    obstacle_name="Conference Table",
    obstacle_type="furniture",
    boundary_points=[
        Position(14, 16),
        Position(28, 16),
        Position(28, 19),
        Position(14, 19)
    ],
    blocks_movement=True,
    blocks_line_of_sight=False,
    height=0.8
)
dims.obstacles["conference_table"] = table
```

---

## 🚗 **EXAMPLE 3: PARKING LOT WITH VEHICLES**

```
Y-axis
^
|  30 ┌─────────────────────────────────┐
|     │  [CAR] [CAR]     [CAR] [CAR]    │
|  25 │                                 │
|     │  [VAN]           [TRUCK]        │
|  20 │                                 │
|     │         [CAR] [CAR]             │
|  15 │                                 │
|     │  [CAR]           [CAR] [CAR]    │
|  10 │                                 │
|     │         ENTRANCE                │
|   5 │            ↓                    │
|     │                                 │
|   0 └─────────────────────────────────┘
     0    5    10   15   20   25   30  → X-axis
```

### **Code:**
```python
spatial.create_location(
    location_name="Parking Lot",
    width=35,
    height=30,
    location_type="exterior",
    description="Dimly lit parking lot behind the building"
)

spatial.set_current_location("Parking Lot")
context = spatial.get_current_context()
dims = context.location_dimensions

# Single zone for entire lot
parking_zone = Zone(
    zone_name="Parking Lot",
    zone_type="outdoor",
    boundary_points=[
        Position(0, 0),
        Position(35, 0),
        Position(35, 30),
        Position(0, 30)
    ],
    description="Open parking lot"
)
dims.zones["parking_lot"] = parking_zone

# Add vehicle obstacles (various sizes)
vehicles = [
    # (name, x, y, width, height, type)
    ("Sedan 1", 3, 26, 4, 2, "vehicle"),
    ("Sedan 2", 9, 26, 4, 2, "vehicle"),
    ("Sedan 3", 21, 26, 4, 2, "vehicle"),
    ("Sedan 4", 27, 26, 4, 2, "vehicle"),
    ("Van", 3, 20, 5, 3, "vehicle"),
    ("Pickup Truck", 21, 20, 5, 3, "vehicle"),
    ("Sedan 5", 12, 15, 4, 2, "vehicle"),
    ("Sedan 6", 18, 15, 4, 2, "vehicle"),
    ("Sedan 7", 3, 10, 4, 2, "vehicle"),
    ("Sedan 8", 21, 10, 4, 2, "vehicle"),
    ("Sedan 9", 27, 10, 4, 2, "vehicle"),
]

for name, x, y, w, h, vtype in vehicles:
    vehicle = Obstacle(
        obstacle_name=name,
        obstacle_type=vtype,
        boundary_points=[
            Position(x, y),
            Position(x + w, y),
            Position(x + w, y + h),
            Position(x, y + h)
        ],
        blocks_movement=True,
        blocks_line_of_sight=True,  # Can't see through cars
        height=1.5
    )
    dims.obstacles[name.lower().replace(" ", "_")] = vehicle

# Add possible actors
spatial.add_possible_actor(
    actor_id="lookout_001",
    actor_name="Lookout",
    actor_type="NUA",
    brief_description="Person keeping watch near the vehicles",
    narrative_role="antagonist",
    introduction_triggers=["lookout", "watching", "guard", "suspicious"]
)
```

---

## 🏚️ **EXAMPLE 4: WAREHOUSE WITH CRATES**

```
Y-axis
^
|  25 ┌─────────────────────────────────┐
|     │ ▓▓▓▓  ▓▓▓▓         ▓▓▓▓  ▓▓▓▓  │  ▓▓▓▓ = Crate stacks
|  20 │ ▓▓▓▓  ▓▓▓▓         ▓▓▓▓  ▓▓▓▓  │
|     │                                 │
|  15 │        ▓▓▓▓  ▓▓▓▓               │
|     │        ▓▓▓▓  ▓▓▓▓               │
|  10 │                                 │
|     │ ▓▓▓▓                    ▓▓▓▓   │
|   5 │ ▓▓▓▓         OPEN       ▓▓▓▓   │
|     │              SPACE              │
|   0 └─────────────────────────────────┘
     0    5    10   15   20   25   30  → X-axis
```

### **Code:**
```python
spatial.create_location(
    location_name="Abandoned Warehouse",
    width=35,
    height=25,
    location_type="interior",
    description="Large warehouse with scattered crate stacks"
)

spatial.set_current_location("Abandoned Warehouse")
context = spatial.get_current_context()
dims = context.location_dimensions

# Define zones based on crate placement
open_area = Zone(
    zone_name="Open Area",
    zone_type="area",
    boundary_points=[
        Position(10, 5),
        Position(25, 5),
        Position(25, 12),
        Position(10, 12)
    ],
    description="Clear space in the center"
)
dims.zones["open_area"] = open_area

# Add crate stacks as obstacles
crate_stacks = [
    ("Crates NW1", 2, 20, 3, 3),
    ("Crates NW2", 7, 20, 3, 3),
    ("Crates NE1", 25, 20, 3, 3),
    ("Crates NE2", 30, 20, 3, 3),
    ("Crates C1", 10, 13, 3, 3),
    ("Crates C2", 15, 13, 3, 3),
    ("Crates SW", 2, 5, 3, 3),
    ("Crates SE", 28, 5, 3, 3),
]

for name, x, y, w, h in crate_stacks:
    crates = Obstacle(
        obstacle_name=name,
        obstacle_type="furniture",
        boundary_points=[
            Position(x, y),
            Position(x + w, y),
            Position(x + w, y + h),
            Position(x, y + h)
        ],
        blocks_movement=True,
        blocks_line_of_sight=True,
        height=2.5  # Tall stacks
    )
    dims.obstacles[name.lower().replace(" ", "_")] = crates
```

---

## 🎮 **USAGE IN GAMEPLAY**

### **Check Actor's Zone:**
```python
ua_pos = spatial.get_actor_position("ua_001")
zone = dims.get_zone_at_position(ua_pos)
print(f"You are in the {zone.zone_name}")
# "You are in the Front Area"
```

### **Check Line of Sight:**
```python
ua_pos = spatial.get_actor_position("ua_001")
nua_pos = spatial.get_actor_position("nua_001")

has_los = dims.has_line_of_sight(ua_pos, nua_pos)
if not has_los:
    print("Your view is blocked by obstacles")
```

### **Validate Movement:**
```python
target_pos = Position(15, 10)

if not dims.is_position_valid(target_pos):
    print("You can't move there - obstacle in the way")
else:
    spatial.move_actor("ua_001", target_pos)
```

### **Zone-Based Narration:**
```python
zone = dims.get_zone_at_position(actor_pos)
if zone.zone_name == "Back Room":
    # Narrator: "You're in the storage area, away from customers..."
    pass
elif zone.zone_name == "Aisles":
    # Narrator: "You're among the shelves, partially concealed..."
    pass
```

---

## 📊 **BENEFITS OF DYNAMIC LAYOUTS**

### **✅ Realistic Spaces**
- L-shaped rooms
- Irregular areas
- Natural obstacles
- Zone-based positioning

### **✅ Tactical Gameplay**
- Cover mechanics (behind obstacles)
- Line of sight blocking
- Zone control
- Flanking opportunities

### **✅ Narrative Richness**
- "You're behind the counter"
- "They can't see you from the aisles"
- "You duck behind a car"
- "The conference room has glass walls"

### **✅ Flexible Design**
- Any shape location
- Custom obstacles
- Named zones
- Persistent layouts

---

## 🎉 **SUMMARY**

**Dynamic layouts support:**
- 📐 **Irregular polygons** (not just rectangles)
- 🏢 **Named zones** (bar area, back room, etc.)
- 🚧 **Physical obstacles** (walls, furniture, vehicles)
- 👁️ **Line of sight** calculations
- 🎯 **Zone-based** positioning
- 💾 **JSON persistence** for all layout data

**No more boring squares - create realistic, tactical spaces! 🎯**
