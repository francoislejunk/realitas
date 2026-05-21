# Spatial Persistence & Movement Tracking Status

## 📊 **YOUR QUESTIONS**

1. **"are we properly saving the maps in disks?"**
2. **"does the map actively change when the actor mentions moving from one side of the room to the other?"**

---

## ✅ **QUESTION 1: MAP PERSISTENCE - YES!**

### **Maps ARE saved to disk properly!**

**File: `spatial_context_system.py`**

#### **Save Implementation (Lines 858-870):**
```python
def _save(self):
    """Save spatial context to JSON"""
    try:
        data = {
            "session_id": self.session_id,
            "current_location": self.current_location,
            "contexts": {k: v.to_dict() for k, v in self.contexts.items()}
        }
        
        with open(self.save_path, 'w') as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[SPATIAL] Error saving: {e}")
```

#### **Load Implementation (Lines 872-887):**
```python
def _load(self):
    """Load spatial context from JSON"""
    try:
        if self.save_path.exists():
            with open(self.save_path, 'r') as f:
                data = json.load(f)
            
            self.current_location = data.get("current_location")
            self.contexts = {
                k: SpatialContext.from_dict(v) 
                for k, v in data.get("contexts", {}).items()
            }
            
            print(f"[SPATIAL] Loaded {len(self.contexts)} location(s)")
    except Exception as e:
        print(f"[SPATIAL] Error loading: {e}")
```

#### **Save Path (Line 507):**
```python
self.save_path = Path(f"sessions/{session_id}/spatial_context.json")
```

---

### **When Are Maps Saved?**

#### **1. After Creating Location (Line 530):**
```python
def create_location(self, ...):
    context = SpatialContext(location_dimensions=dimensions)
    self.contexts[location_name] = context
    self._save()  # ✅ Saved immediately!
```

#### **2. After Moving Actor (Line 599):**
```python
def move_actor(self, actor_id: str, new_position: Position, ...):
    context.actor_positions[actor_id].position = new_position
    self._save()  # ✅ Saved immediately!
```

#### **3. After Adding Actor (Line 577):**
```python
def add_actor(self, ...):
    context.actor_positions[actor_id] = actor_pos
    self._save()  # ✅ Saved immediately!
```

#### **4. After Removing Actor (Line 614):**
```python
def remove_actor(self, actor_id: str, ...):
    del context.actor_positions[actor_id]
    self._save()  # ✅ Saved immediately!
```

---

### **What Gets Saved?**

```json
{
  "session_id": "abc123",
  "current_location": "Callahan Customs",
  "contexts": {
    "Callahan Customs": {
      "location_dimensions": {
        "width": 25,
        "height": 20,
        "location_name": "Callahan Customs",
        "location_type": "interior",
        "description": "...",
        "zones": {
          "main_work_area": {...},
          "tool_storage": {...},
          "coffee_station": {...}
        },
        "obstacles": {
          "workbench": {...},
          "tool_chest": {...}
        }
      },
      "actor_positions": {
        "ua_001": {
          "actor_id": "ua_001",
          "actor_name": "Derek Callahan",
          "position": {"x": 12.5, "y": 3.0},
          "is_user_actor": true
        }
      }
    },
    "Main Street": {
      "location_dimensions": {...},
      "actor_positions": {...}
    }
  }
}
```

---

### **Persistence Lifecycle:**

```
1. Session Start:
   → SpatialContextManager.__init__()
   → self._load()  # Loads from disk
   → Restores all locations, zones, obstacles, actor positions

2. Create Location:
   → spatial.create_location(...)
   → self._save()  # Saves to disk immediately

3. Move Actor:
   → spatial.move_actor(...)
   → self._save()  # Saves to disk immediately

4. Session End:
   → All data already saved (incremental saves)
   → No data loss!

5. Next Session:
   → self._load()  # Loads everything back
   → All locations, layouts, positions restored!
```

---

## ❌ **QUESTION 2: MOVEMENT TRACKING - NO!**

### **Maps DO NOT update when actor moves within a location!**

**The Problem:**
- User says: "I walk to the workbench"
- System generates narrative: "You walk to the workbench..."
- **BUT:** Actor position on map doesn't change! ❌
- Map still shows actor at entrance

---

### **What's Missing?**

#### **1. Movement Detection:**
```python
# MISSING: No code to detect movement within location
# Need to detect phrases like:
# - "I walk to the workbench"
# - "I move to the corner"
# - "I go to the back of the room"
# - "I approach the door"
```

#### **2. Target Location Extraction:**
```python
# MISSING: No code to extract WHERE the actor is moving to
# Need to identify:
# - Target obstacle: "workbench", "door", "counter"
# - Target zone: "back of room", "corner", "entrance"
# - Target coordinates: "left side", "center", "near the window"
```

#### **3. Position Calculation:**
```python
# MISSING: No code to calculate new position
# Need to:
# - Find obstacle/zone coordinates
# - Calculate position near target
# - Update actor position on map
```

#### **4. Integration:**
```python
# MISSING: No integration in main simulation loop
# Need to:
# - Detect movement in user input
# - Extract target location
# - Calculate new position
# - Call spatial.move_actor(...)
# - Update map display
```

---

### **Current Movement Tracking:**

**Only tracks movements BETWEEN locations:**

```python
# redesigned_main.py (Lines 940-944)
# When moving to NEW location:
if existing_pos:
    spatial.move_actor("ua_001", Position(entrance_x, entrance_y))
    print(f"[SPATIAL] Moved UA to entrance")
```

**Does NOT track movements WITHIN same location!**

---

### **Example of What's Missing:**

```
Current Behavior:
> I walk to the workbench

Narrative: "You walk across the garage to the workbench..."
Map: @ still at entrance (12.5, 3.0) ❌

---

Desired Behavior:
> I walk to the workbench

[SPATIAL] Detected movement to: workbench
[SPATIAL] Workbench located at (15.0, 12.0)
[SPATIAL] Moving UA from (12.5, 3.0) to (14.0, 11.0)
[SPATIAL] Moved Derek Callahan to near workbench

Narrative: "You walk across the garage to the workbench..."
Map: @ now near workbench (14.0, 11.0) ✅
```

---

## 📋 **SUMMARY**

| Feature | Status | Details |
|---------|--------|---------|
| **Map Persistence** | ✅ **YES** | Saved to disk after every change |
| **Location Persistence** | ✅ **YES** | All locations saved and restored |
| **Zone Persistence** | ✅ **YES** | Zones saved with locations |
| **Obstacle Persistence** | ✅ **YES** | Obstacles saved with locations |
| **Actor Position Persistence** | ✅ **YES** | Positions saved after movement |
| **Cross-Session Persistence** | ✅ **YES** | Loads on session start |
| **Movement Detection** | ❌ **NO** | Not detecting within-location movement |
| **Position Updates** | ❌ **NO** | Map doesn't update when actor moves |
| **Target Extraction** | ❌ **NO** | Can't identify movement targets |

---

## 🔧 **WHAT NEEDS TO BE IMPLEMENTED**

### **1. Movement Detection System:**
```python
def detect_movement_within_location(user_input: str) -> Optional[Dict]:
    """
    Detect if user input indicates movement within current location.
    
    Returns:
        {
            "is_movement": True,
            "target": "workbench",  # What they're moving to
            "target_type": "obstacle",  # obstacle/zone/direction
            "movement_type": "walk"  # walk/run/sneak
        }
    """
    # Use LLM or keywords to detect:
    # - "walk to", "move to", "go to", "approach"
    # - "head to", "run to", "sneak to"
    # Extract target: "workbench", "corner", "door", etc.
```

### **2. Target Position Resolver:**
```python
def resolve_target_position(target: str, target_type: str, 
                           spatial_context: SpatialContext) -> Position:
    """
    Convert target name to actual coordinates.
    
    Examples:
        - "workbench" → Find obstacle, return position near it
        - "back of room" → Find zone, return center of zone
        - "left side" → Calculate position on left side
    """
    if target_type == "obstacle":
        # Find obstacle by name
        obstacle = spatial_context.find_obstacle(target)
        # Return position adjacent to obstacle
        return Position(obstacle.x - 1, obstacle.y)
    
    elif target_type == "zone":
        # Find zone by name
        zone = spatial_context.find_zone(target)
        # Return center of zone
        return zone.get_center()
    
    # ... etc
```

### **3. Integration in Main Loop:**
```python
# In main simulation loop, after generating narrative:

# Check if action involves movement within location
movement_data = detect_movement_within_location(user_input)

if movement_data and movement_data["is_movement"]:
    # Resolve target position
    target_pos = resolve_target_position(
        movement_data["target"],
        movement_data["target_type"],
        spatial.get_current_context()
    )
    
    # Update actor position
    spatial.move_actor("ua_001", target_pos)
    
    # Map now reflects new position!
    print(f"[SPATIAL] Moved to {movement_data['target']}")
```

---

## 🎯 **BENEFITS OF IMPLEMENTING MOVEMENT TRACKING**

### **1. Spatial Awareness:**
```
> I walk to the workbench
> map

MAP: Callahan Customs
   20 ┌────────────────┐
   15 │                │
   12 │    @███        │  @ = You (at workbench!)
    8 │                │  █ = Workbench
    3 │                │
    0 └────────────────┘
```

### **2. Distance-Based Interactions:**
```
> I examine the tool chest

[SPATIAL] Tool chest is 8.5 units away
[SPATIAL] You need to move closer (within 2 units)

Narrative: "The tool chest is across the room. You'll need to walk over to examine it."
```

### **3. Line of Sight:**
```
> I look at the door

[SPATIAL] Checking line of sight...
[SPATIAL] Workbench blocks view of door!

Narrative: "The workbench blocks your view of the door from here."
```

### **4. Tactical Positioning:**
```
> I hide behind the car

[SPATIAL] Moving to cover position behind Rusted Chevy Nova
[SPATIAL] You have cover from entrance

Narrative: "You duck behind the rusted Chevy, using it as cover."
```

---

## 🏆 **CURRENT STATUS**

### **✅ What Works:**
- Maps saved to disk
- Locations persist across sessions
- Zones and obstacles saved
- Actor positions saved
- Movement between locations tracked

### **❌ What's Missing:**
- Movement detection within locations
- Position updates when moving around room
- Target location extraction
- Distance-based interactions
- Line of sight calculations

---

## 💡 **RECOMMENDATION**

**Priority: MEDIUM**

The spatial system has solid persistence, but lacks dynamic position tracking within locations. This would add:
- Better spatial awareness
- More realistic interactions
- Distance-based mechanics
- Tactical positioning

**Implementation Effort:** Medium (2-3 days)
- Movement detection: 1 day
- Target resolution: 1 day
- Integration & testing: 1 day

**Value:** High for immersion and tactical gameplay
