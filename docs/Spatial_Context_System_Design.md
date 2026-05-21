# Spatial Context System - Design Document

## 🎯 **CORE PURPOSE**

The Spatial Context System solves **two critical problems**:

### **1. Distance-Based Action Mechanics**
**Problem:** Actions happen in a void without spatial awareness.
- Whisper vs shout - no difference
- Touch vs throw - same mechanics
- Movement time - not calculated
- Partial actions - can't determine if actor has time to complete

**Solution:** Track actor positions on X/Y grid, calculate distances, determine action feasibility.

### **2. Narrative Consistency & Actor Control**
**Problem:** Actors appear/disappear arbitrarily based on user intent.
- User chases hints about an actor → actor never shows up (no payoff)
- User creates actors spontaneously through intent → breaks narrative control
- No pre-planning of who CAN appear in a location

**Solution:** Pre-seed "possible actors" pool, only introduce from this pool, track introduction status.

---

## 📐 **SPATIAL POSITIONING SYSTEM**

### **Top-Down Grid View**

```
Y-axis (height)
^
|  20 ┌─────────────────────────┐
|     │                         │
|     │    NUA2 (8,15)          │
|  15 │         ●               │
|     │                         │
|     │              UA (12,10) │
|  10 │                ●        │
|     │                         │
|     │  NUA1 (3,5)             │
|   5 │    ●                    │
|     │                         │
|   0 └─────────────────────────┘
     0    5    10   15   20  → X-axis (width)
```

### **Position Tracking**
- **X-axis:** Horizontal position (0 to width)
- **Y-axis:** Vertical position (0 to height)
- **Units:** Abstract grid units (not meters/feet)
- **Precision:** Float values for smooth movement

---

## 📏 **DISTANCE CATEGORIES**

### **Distance Ranges & Action Implications**

| Category | Range | Actions Possible | Examples |
|----------|-------|------------------|----------|
| **IMMEDIATE** | 0-2 units | Touch, whisper, melee, grab | Hand on shoulder, quiet talk |
| **CLOSE** | 3-5 units | Normal conversation, throw | Across a desk, small room |
| **NEAR** | 6-10 units | Raised voice, quick movement | Across a room, hallway |
| **FAR** | 11-20 units | Shout, significant movement | Large room, parking lot |
| **DISTANT** | 21+ units | Out of range for most actions | Different areas, far away |

### **Action Feasibility Matrix**

```python
Action Type    | IMMEDIATE | CLOSE | NEAR | FAR | DISTANT
---------------|-----------|-------|------|-----|--------
Touch/Melee    |     ✓     |   ✗   |  ✗   |  ✗  |   ✗
Whisper        |     ✓     |   ✓   |  ✗   |  ✗  |   ✗
Talk           |     ✓     |   ✓   |  ✓   |  ✗  |   ✗
Shout          |     ✓     |   ✓   |  ✓   |  ✓  |   ✗
Throw          |     ✓     |   ✓   |  ✓   |  ✗  |   ✗
Ranged         |     ✓     |   ✓   |  ✓   |  ✓  |   ✓
```

---

## 🎭 **POSSIBLE ACTORS SYSTEM**

### **Pre-Seeded Actor Pool**

**Concept:** Every location has a **pre-defined list** of actors that CAN appear.

**Why This Matters:**
1. **Narrative Payoff:** If hints mention "a mechanic", the mechanic EXISTS and CAN be found
2. **Controlled Introduction:** Actors only appear when narratively appropriate
3. **No Spontaneous Creation:** User can't arbitrarily create actors through intent alone
4. **Consistency:** Same actors available across sessions

### **Possible Actor Structure**

```python
PossibleActor:
    actor_id: "mech_001"
    actor_name: "Vince the Mechanic"
    actor_type: "NUA"  # or "INUA"
    brief_description: "Gruff but fair mechanic, knows cars inside out"
    narrative_role: "ally"  # ally, antagonist, neutral, obstacle, resource
    introduction_triggers: ["mechanic", "car repair", "engine", "garage"]
    has_been_introduced: False
```

### **Introduction Flow**

```
1. Location created → Possible actors seeded
2. User action mentions trigger → System checks pool
3. Trigger matches → Actor CAN be introduced
4. Narrator introduces actor → Mark as introduced
5. Actor added to active positions → Now interactable
```

### **Narrative Roles**

| Role | Purpose | Example |
|------|---------|---------|
| **ally** | Helps UA achieve goals | Friendly mechanic, helpful clerk |
| **antagonist** | Opposes UA | Rival, enemy, obstacle |
| **neutral** | No strong alignment | Bystander, shopkeeper |
| **obstacle** | Blocks progress (not hostile) | Bureaucrat, locked door (INUA) |
| **resource** | Provides tools/info | Library (INUA), informant |

---

## 🔧 **CORE COMPONENTS**

### **1. Position (x, y coordinates)**
```python
Position(x=10.5, y=8.3)
- distance_to(other_position) → float
- get_distance_category(other_position) → DistanceCategory
```

### **2. LocationDimensions**
```python
LocationDimensions(
    width=20,
    height=15,
    location_name="Joe's Garage",
    location_type="interior",
    description="Small auto repair shop with two bays"
)
```

### **3. ActorPosition**
```python
ActorPosition(
    actor_id="ua_001",
    actor_name="Detective Morgan",
    position=Position(12, 10),
    is_user_actor=True,
    is_active=True
)
```

### **4. PossibleActor**
```python
PossibleActor(
    actor_id="mech_001",
    actor_name="Vince",
    actor_type="NUA",
    brief_description="Mechanic who knows the neighborhood",
    narrative_role="ally",
    introduction_triggers=["mechanic", "repair", "garage"],
    has_been_introduced=False
)
```

### **5. SpatialContext**
```python
SpatialContext(
    location_dimensions=LocationDimensions(...),
    actor_positions={...},  # Active actors
    possible_actors={...},  # Pre-seeded pool
    last_updated="2024-10-14T14:30:00"
)
```

---

## 💾 **JSON PERSISTENCE**

### **File Structure**
```
sessions/
  └── {session_id}/
      └── spatial_context.json
```

### **JSON Format**
```json
{
  "session_id": "session_001",
  "current_location": "joes_garage",
  "contexts": {
    "joes_garage": {
      "location_dimensions": {
        "width": 20,
        "height": 15,
        "location_name": "Joe's Garage",
        "location_type": "interior",
        "description": "Small auto repair shop"
      },
      "actor_positions": {
        "ua_001": {
          "actor_id": "ua_001",
          "actor_name": "Detective Morgan",
          "position": {"x": 12.0, "y": 10.0},
          "is_user_actor": true,
          "is_active": true
        },
        "nua_001": {
          "actor_id": "nua_001",
          "actor_name": "Vince",
          "position": {"x": 5.0, "y": 8.0},
          "is_user_actor": false,
          "is_active": true
        }
      },
      "possible_actors": {
        "nua_002": {
          "actor_id": "nua_002",
          "actor_name": "Suspicious Customer",
          "actor_type": "NUA",
          "brief_description": "Nervous man asking about a specific car",
          "narrative_role": "antagonist",
          "introduction_triggers": ["customer", "waiting area", "front desk"],
          "has_been_introduced": false
        }
      },
      "last_updated": "2024-10-14T14:30:00"
    }
  }
}
```

---

## 🎮 **USAGE EXAMPLES**

### **Example 1: Setup Location**
```python
from spatial_context_system import get_spatial_manager, Position

spatial = get_spatial_manager(session_id="session_001")

# Create location
spatial.create_location(
    location_name="Joe's Garage",
    width=20,
    height=15,
    location_type="interior",
    description="Small auto repair shop with two bays"
)

# Set as current
spatial.set_current_location("Joe's Garage")

# Add UA
spatial.add_actor(
    actor_id="ua_001",
    actor_name="Detective Morgan",
    position=Position(12, 10),
    is_user_actor=True
)

# Add possible actors (pre-seed)
spatial.add_possible_actor(
    actor_id="nua_001",
    actor_name="Vince the Mechanic",
    actor_type="NUA",
    brief_description="Gruff but fair mechanic",
    narrative_role="ally",
    introduction_triggers=["mechanic", "repair", "help", "car"]
)

spatial.add_possible_actor(
    actor_id="nua_002",
    actor_name="Suspicious Customer",
    actor_type="NUA",
    brief_description="Nervous man asking about a car",
    narrative_role="antagonist",
    introduction_triggers=["customer", "waiting", "front"]
)
```

### **Example 2: Check Action Feasibility**
```python
# User wants to whisper to Vince
user_input = "I whisper to the mechanic about the case"

# Check if mechanic can be introduced
if spatial.can_introduce_actor("nua_001", user_input):
    # Introduce Vince
    spatial.add_actor("nua_001", "Vince", Position(5, 8))
    spatial.mark_actor_introduced("nua_001")

# Check distance
distance_cat = spatial.get_distance_category("ua_001", "nua_001")
# Returns: DistanceCategory.FAR (distance ~8.5 units)

# Check if whisper is feasible
feasible, reason = spatial.is_action_feasible("ua_001", "nua_001", "whisper")
# Returns: (False, "Target too far for whisper")

# Calculate movement time to get closer
target_pos = Position(6, 9)  # Next to Vince
time_units = spatial.get_movement_time("ua_001", target_pos)
# Returns: 4 UT (distance ~7.2 units / 2 = 3.6 → ceil = 4)

# Move UA closer
spatial.move_actor("ua_001", target_pos)

# Now check again
feasible, reason = spatial.is_action_feasible("ua_001", "nua_001", "whisper")
# Returns: (True, "Action feasible at immediate range")
```

### **Example 3: Prevent Arbitrary Actor Creation**
```python
# User tries to create actor through intent
user_input = "I talk to the police officer"

# Check if "police officer" is in possible actors
possible = spatial.get_possible_actors(only_unintroduced=True)
# Returns: [Vince, Suspicious Customer] - NO police officer

# System response: "There's no police officer here"
# User cannot spontaneously create actors
```

### **Example 4: Narrative Payoff**
```python
# Scene hints at suspicious customer
narrator_text = "You notice someone waiting nervously near the front desk..."

# User follows up
user_input = "I approach the waiting area"

# Check for introduction
if spatial.can_introduce_actor("nua_002", user_input):
    # PAYOFF: Actor exists and can be introduced
    spatial.add_actor("nua_002", "Suspicious Customer", Position(18, 3))
    spatial.mark_actor_introduced("nua_002")
    # Narrator: "A nervous man looks up as you approach..."
```

---

## 🔗 **INTEGRATION POINTS**

### **1. Main Simulation Loop**
```python
# In redesigned_main.py

# Initialize spatial manager
spatial = get_spatial_manager(session_id=tracker.session_id)

# On location change
spatial.set_current_location(new_location)

# On actor creation
spatial.add_actor(actor.id, actor.name, initial_position)

# Before action resolution
feasible, reason = spatial.is_action_feasible(proactor_id, reactor_id, action_type)
if not feasible:
    # Modify action or add movement requirement
    pass
```

### **2. Narrator Agent**
```python
# In narrator_agent.py

def generate_scene_description(self, ...):
    # Include spatial context
    spatial = get_spatial_manager()
    context = spatial.get_current_context()
    
    # Mention possible actors as hints
    possible = spatial.get_possible_actors(only_unintroduced=True)
    # Weave into narration: "You hear someone working in the back..."
```

### **3. Interpreter Agent**
```python
# In interpreter_agent.py

def interpret_action(self, user_input, ...):
    spatial = get_spatial_manager()
    
    # Check for actor introduction triggers
    for possible in spatial.get_possible_actors(only_unintroduced=True):
        if spatial.can_introduce_actor(possible.actor_id, user_input):
            # Flag for introduction
            pass
    
    # Check action feasibility
    feasible, reason = spatial.is_action_feasible(...)
    # Adjust interpretation based on feasibility
```

### **4. Conductor Agent**
```python
# In conductor_agent.py

def determine_reactor(self, user_input, available_actors):
    spatial = get_spatial_manager()
    
    # Only consider actors within reasonable range
    nearby = spatial.get_actors_within_range(ua_id, max_distance=10)
    # Filter available_actors to nearby only
```

---

## 📊 **BENEFITS**

### **1. Realistic Action Mechanics**
- ✅ Whisper only works up close
- ✅ Shout works across room
- ✅ Movement takes time based on distance
- ✅ Partial actions when time runs out

### **2. Narrative Consistency**
- ✅ Hints have payoff (actors exist)
- ✅ No arbitrary actor creation
- ✅ Controlled introduction timing
- ✅ Pre-planned actor pool

### **3. Spatial Awareness**
- ✅ Universal context (X/Y grid)
- ✅ Distance calculations
- ✅ Range-based feasibility
- ✅ Movement tracking

### **4. Persistence**
- ✅ Positions saved to JSON
- ✅ Possible actors tracked
- ✅ Introduction status preserved
- ✅ Context continuity across sessions

---

## 🚀 **NEXT STEPS**

### **Phase 1: Core Integration** (Immediate)
1. ✅ Create `spatial_context_system.py`
2. ⏳ Integrate into `redesigned_main.py`
3. ⏳ Update narrator to use spatial context
4. ⏳ Update interpreter for feasibility checks

### **Phase 2: Action Mechanics** (High Priority)
1. ⏳ Implement distance-based action modifiers
2. ⏳ Add movement time calculations
3. ⏳ Handle partial actions (time constraints)
4. ⏳ Integrate with UTAS formula

### **Phase 3: Actor Management** (High Priority)
1. ⏳ Implement actor introduction system
2. ⏳ Create location templates with pre-seeded actors
3. ⏳ Add trigger detection in user input
4. ⏳ Prevent arbitrary actor creation

### **Phase 4: Enhancement** (Medium Priority)
1. ⏳ Add line-of-sight calculations
2. ⏳ Implement cover/obstacles
3. ⏳ Add area effects (radius)
4. ⏳ Create visual grid display (optional)

---

## 🎉 **SUMMARY**

**The Spatial Context System provides:**
- 📐 **X/Y grid positioning** for universal spatial awareness
- 📏 **Distance-based mechanics** (whisper vs shout, movement time)
- 🎭 **Pre-seeded actor pools** for narrative consistency
- 🚫 **Controlled actor introduction** (no arbitrary creation)
- 💾 **JSON persistence** for context continuity
- ✅ **Action feasibility checks** based on range

**This solves:**
- ❌ Actions happening in a spatial void
- ❌ Actors appearing/disappearing arbitrarily
- ❌ Narrative hints with no payoff
- ❌ User creating actors through intent alone

**Result: Realistic, consistent, spatially-aware simulation! 🎯**
