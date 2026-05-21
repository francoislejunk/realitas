# Spatial System Integration Guide

## 🎯 **COMPLETE SPATIAL SYSTEM OVERVIEW**

This guide covers integration of all three spatial systems:
1. **Spatial Context System** - Positions, zones, obstacles
2. **Movement Time System** - Speed, distance, time calculations
3. **Partial Action System** - Never deny, always interpret

---

## 📦 **SYSTEM COMPONENTS**

### **1. Spatial Context (`spatial_context_system.py`)**
- Position tracking (X/Y grid)
- Location dimensions with zones
- Obstacles (walls, furniture, vehicles)
- Line of sight calculations
- Pre-seeded possible actors
- JSON persistence

### **2. Movement Time (`spatial_context_system.py`)**
- Movement speed categories (CRAWL to SPRINT)
- Time calculations (seconds and UT)
- Distance-based timing
- Speed selection logic

### **3. Partial Actions (`partial_action_system.py`)**
- Never deny user actions
- Diegetic failure explanations
- Action reinterpretation
- Narrative generation

---

## 🔗 **INTEGRATION POINTS**

### **Main Simulation Loop (`redesigned_main.py`)**

```python
from spatial_context_system import get_spatial_manager, Position, MovementSpeed
from partial_action_system import get_partial_action_interpreter

# Initialize systems
spatial = get_spatial_manager(session_id=tracker.session_id)
partial_interpreter = get_partial_action_interpreter()

# === LOCATION SETUP ===

def setup_location(location_name: str, layout_data: dict):
    """Setup location with dimensions, zones, obstacles, and possible actors"""
    
    # Create location
    spatial.create_location(
        location_name=location_name,
        width=layout_data["width"],
        height=layout_data["height"],
        location_type=layout_data["type"],
        description=layout_data["description"]
    )
    
    spatial.set_current_location(location_name)
    context = spatial.get_current_context()
    dims = context.location_dimensions
    
    # Add zones
    for zone_data in layout_data.get("zones", []):
        from spatial_context_system import Zone
        zone = Zone(
            zone_name=zone_data["name"],
            zone_type=zone_data["type"],
            boundary_points=[Position(p[0], p[1]) for p in zone_data["points"]],
            description=zone_data["description"]
        )
        dims.zones[zone_data["id"]] = zone
    
    # Add obstacles
    for obs_data in layout_data.get("obstacles", []):
        from spatial_context_system import Obstacle
        obstacle = Obstacle(
            obstacle_name=obs_data["name"],
            obstacle_type=obs_data["type"],
            boundary_points=[Position(p[0], p[1]) for p in obs_data["points"]],
            blocks_movement=obs_data.get("blocks_movement", True),
            blocks_line_of_sight=obs_data.get("blocks_los", True),
            height=obs_data.get("height", 2.0)
        )
        dims.obstacles[obs_data["id"]] = obstacle
    
    # Add possible actors
    for actor_data in layout_data.get("possible_actors", []):
        spatial.add_possible_actor(
            actor_id=actor_data["id"],
            actor_name=actor_data["name"],
            actor_type=actor_data["type"],
            brief_description=actor_data["description"],
            narrative_role=actor_data["role"],
            introduction_triggers=actor_data["triggers"]
        )
    
    print(f"[SPATIAL] Setup complete: {location_name}")

# === ACTION PROCESSING ===

def process_user_action(user_input: str, ua_actor, available_ut: int):
    """Process user action with spatial awareness and partial action support"""
    
    # 1. Parse action (use existing interpreter)
    action_data = interpreter_agent.interpret_action(user_input, ua_actor)
    
    # 2. Check for actor introduction triggers
    possible_actors = spatial.get_possible_actors(only_unintroduced=True)
    for possible in possible_actors:
        if spatial.can_introduce_actor(possible.actor_id, user_input):
            # Introduce actor
            introduce_actor(possible)
    
    # 3. Get spatial information
    ua_pos = spatial.get_actor_position(ua_actor.id)
    
    # 4. Determine if action involves movement
    if action_data.get("target_actor"):
        target_id = action_data["target_actor"]
        target_pos = spatial.get_actor_position(target_id)
        
        if target_pos:
            # Calculate distance and time
            distance = ua_pos.distance_to(target_pos)
            distance_cat = ua_pos.get_distance_category(target_pos)
            
            # Determine movement speed
            speed = determine_movement_speed(action_data)
            
            # Calculate movement time
            move_seconds, move_ut = ua_pos.calculate_movement_time_with_ut(
                target_pos, speed
            )
            
            # Check action range requirements
            action_type = action_data.get("action_type", "talk")
            feasible, reason = spatial.is_action_feasible(
                ua_actor.id, target_id, action_type
            )
            
            # 5. Determine if partial action needed
            action_ut = action_data.get("ut_cost", 1)
            total_ut = move_ut + action_ut
            
            if not feasible or total_ut > available_ut:
                # PARTIAL ACTION
                if not feasible:
                    # Out of range
                    result = partial_interpreter.interpret_ranged_action(
                        original_action=user_input,
                        action_type=action_type,
                        current_distance=distance,
                        required_distance_category=get_required_range(action_type),
                        actual_distance_category=distance_cat
                    )
                else:
                    # Insufficient time
                    movement_result = partial_interpreter.interpret_movement_action(
                        original_action=user_input,
                        start_pos=ua_pos,
                        target_pos=target_pos,
                        available_ut=available_ut - action_ut,
                        speed=speed
                    )
                    
                    result = partial_interpreter.interpret_combined_action(
                        original_action=user_input,
                        movement_component=movement_result,
                        action_component=action_data.get("action_description"),
                        action_ut_cost=action_ut,
                        total_ut_available=available_ut
                    )
                
                # Generate narrative
                narrative = partial_interpreter.generate_narrative_description(
                    result, actor_name=ua_actor.name
                )
                
                # Process reinterpreted action
                return process_reinterpreted_action(
                    result.reinterpreted_action,
                    result.partial_completion_percent,
                    narrative
                )
            else:
                # FULL ACTION POSSIBLE
                # Move actor
                spatial.move_actor(ua_actor.id, target_pos)
                
                # Process action normally
                return process_full_action(action_data, ua_actor)
    
    # No spatial constraints
    return process_full_action(action_data, ua_actor)

def determine_movement_speed(action_data: dict) -> MovementSpeed:
    """Determine movement speed based on action context"""
    
    # Check for explicit speed keywords
    action_lower = action_data.get("raw_input", "").lower()
    
    if any(word in action_lower for word in ["sprint", "dash", "bolt"]):
        return MovementSpeed.SPRINT
    elif any(word in action_lower for word in ["run", "rush", "hurry"]):
        return MovementSpeed.RUN
    elif any(word in action_lower for word in ["jog", "quick"]):
        return MovementSpeed.JOG
    elif any(word in action_lower for word in ["sneak", "creep", "quietly"]):
        return MovementSpeed.SNEAK
    elif any(word in action_lower for word in ["crawl", "drag"]):
        return MovementSpeed.CRAWL
    else:
        # Default to walk
        return MovementSpeed.WALK

def get_required_range(action_type: str) -> DistanceCategory:
    """Get required distance category for action type"""
    from spatial_context_system import DistanceCategory
    
    range_requirements = {
        "touch": DistanceCategory.IMMEDIATE,
        "grab": DistanceCategory.IMMEDIATE,
        "melee": DistanceCategory.IMMEDIATE,
        "whisper": DistanceCategory.IMMEDIATE,
        "talk": DistanceCategory.NEAR,
        "shout": DistanceCategory.FAR,
        "throw": DistanceCategory.NEAR,
        "ranged": DistanceCategory.DISTANT
    }
    
    return range_requirements.get(action_type.lower(), DistanceCategory.CLOSE)

def introduce_actor(possible_actor):
    """Introduce a possible actor into the scene"""
    
    # Create actor using existing creator agent
    new_actor = creator_agent.create_actor(
        actor_type=possible_actor.actor_type,
        name=possible_actor.actor_name,
        description=possible_actor.brief_description
    )
    
    # Add to spatial context at appropriate position
    context = spatial.get_current_context()
    
    # Choose position based on zone or random
    if context.location_dimensions.zones:
        # Place in a random zone
        zone = random.choice(list(context.location_dimensions.zones.values()))
        position = zone.center
    else:
        # Place at random valid position
        position = Position(
            random.uniform(0, context.location_dimensions.width),
            random.uniform(0, context.location_dimensions.height)
        )
    
    spatial.add_actor(new_actor.id, new_actor.name, position)
    spatial.mark_actor_introduced(possible_actor.actor_id)
    
    # Add to active actors
    active_actors[new_actor.id] = new_actor
    
    print(f"[SPATIAL] Introduced {new_actor.name} at {position.x:.1f}, {position.y:.1f}")
```

---

### **Narrator Agent Integration (`narrator_agent.py`)**

```python
def generate_scene_description(self, location_name: str, ...):
    """Generate scene description with spatial context"""
    
    from spatial_context_system import get_spatial_manager
    spatial = get_spatial_manager()
    
    context = spatial.get_current_context()
    if not context:
        # No spatial context, use default
        return self._generate_default_scene(location_name, ...)
    
    dims = context.location_dimensions
    
    # Build spatial context for LLM
    spatial_info = f"""
Location: {dims.location_name} ({dims.width}x{dims.height} units)
Type: {dims.location_type}
Description: {dims.description}

Zones:
"""
    
    for zone in dims.zones.values():
        spatial_info += f"- {zone.zone_name} ({zone.zone_type}): {zone.description}\n"
    
    spatial_info += "\nNotable Features:\n"
    for obstacle in dims.obstacles.values():
        spatial_info += f"- {obstacle.obstacle_name} ({obstacle.obstacle_type})\n"
    
    # Hint at possible actors
    possible_actors = spatial.get_possible_actors(only_unintroduced=True)
    if possible_actors:
        spatial_info += "\nPotential Presence (hint subtly):\n"
        for actor in possible_actors[:3]:  # Limit to 3 hints
            spatial_info += f"- {actor.brief_description}\n"
    
    # Generate scene with spatial context
    prompt = f"""
Generate a scene description for {location_name}.

{spatial_info}

Current actors present:
{self._format_actor_positions(context)}

Create an immersive description that:
1. Describes the space and its layout
2. Mentions zones naturally
3. Hints at possible actors without being explicit
4. Maintains 1980s setting
"""
    
    # Call LLM...
    return scene_description

def _format_actor_positions(self, context):
    """Format actor positions for narrator"""
    output = ""
    
    for actor_pos in context.actor_positions.values():
        zone = context.location_dimensions.get_zone_at_position(actor_pos.position)
        zone_name = zone.zone_name if zone else "the area"
        
        output += f"- {actor_pos.actor_name} in {zone_name}\n"
    
    return output
```

---

### **Conductor Agent Integration (`conductor_agent.py`)**

```python
def determine_reactor(self, proactor_id: str, action_data: dict):
    """Determine reactor with spatial awareness"""
    
    from spatial_context_system import get_spatial_manager
    spatial = get_spatial_manager()
    
    proactor_pos = spatial.get_actor_position(proactor_id)
    if not proactor_pos:
        # No spatial context, use default logic
        return self._default_reactor_selection(proactor_id, action_data)
    
    # Get actors within reasonable range
    max_range = 15  # units
    nearby_actors = spatial.get_actors_within_range(proactor_id, max_range)
    
    # Filter to valid reactors
    valid_reactors = []
    for actor_pos in nearby_actors:
        if actor_pos.actor_id != proactor_id:
            valid_reactors.append(actor_pos)
    
    if not valid_reactors:
        # No one in range
        return None
    
    # Prioritize by distance and line of sight
    context = spatial.get_current_context()
    scored_reactors = []
    
    for actor_pos in valid_reactors:
        distance = proactor_pos.distance_to(actor_pos.position)
        has_los = context.location_dimensions.has_line_of_sight(
            proactor_pos, actor_pos.position
        )
        
        # Score: closer is better, line of sight is better
        score = 100 - distance
        if has_los:
            score += 20
        
        scored_reactors.append((actor_pos.actor_id, score))
    
    # Sort by score
    scored_reactors.sort(key=lambda x: x[1], reverse=True)
    
    return scored_reactors[0][0]  # Return highest scored reactor
```

---

## 📋 **LOCATION TEMPLATE**

### **JSON Format for Location Data:**

```json
{
  "location_name": "Joe's Garage",
  "width": 20,
  "height": 15,
  "type": "interior",
  "description": "Small auto repair shop with two bays",
  
  "zones": [
    {
      "id": "front_area",
      "name": "Front Area",
      "type": "room",
      "points": [[0, 0], [20, 0], [20, 8], [0, 8]],
      "description": "Reception area with desk and waiting chairs"
    },
    {
      "id": "bay_1",
      "name": "Bay 1",
      "type": "area",
      "points": [[0, 8], [10, 8], [10, 15], [0, 15]],
      "description": "Left repair bay with lift"
    },
    {
      "id": "bay_2",
      "name": "Bay 2",
      "type": "area",
      "points": [[10, 8], [20, 8], [20, 15], [10, 15]],
      "description": "Right repair bay with workbench"
    }
  ],
  
  "obstacles": [
    {
      "id": "desk",
      "name": "Reception Desk",
      "type": "furniture",
      "points": [[8, 3], [12, 3], [12, 5], [8, 5]],
      "blocks_movement": true,
      "blocks_los": false,
      "height": 1.0
    },
    {
      "id": "car_1",
      "name": "1973 Pontiac",
      "type": "vehicle",
      "points": [[2, 9], [7, 9], [7, 13], [2, 13]],
      "blocks_movement": true,
      "blocks_los": true,
      "height": 1.5
    }
  ],
  
  "possible_actors": [
    {
      "id": "mech_001",
      "name": "Vince",
      "type": "NUA",
      "description": "Gruff mechanic in his 50s, knows cars inside out",
      "role": "ally",
      "triggers": ["mechanic", "repair", "help", "car", "engine"]
    },
    {
      "id": "cust_001",
      "name": "Nervous Customer",
      "type": "NUA",
      "description": "Anxious man waiting for his car",
      "role": "neutral",
      "triggers": ["customer", "waiting", "reception", "front"]
    }
  ]
}
```

---

## 🎯 **COMPLETE WORKFLOW**

### **1. Session Start**
```python
# Initialize spatial manager
spatial = get_spatial_manager(session_id)

# Load location data
location_data = load_location_json("joes_garage.json")

# Setup location
setup_location("Joe's Garage", location_data)

# Add UA
spatial.add_actor("ua_001", "Detective Morgan", Position(3, 3), is_user_actor=True)
```

### **2. User Action**
```python
user_input = "I run to the mechanic and ask about the car"

# Process with spatial awareness
result = process_user_action(user_input, ua_actor, available_ut=3)
```

### **3. Spatial Checks**
- Calculate distance to target
- Determine movement time
- Check action range feasibility
- Check line of sight

### **4. Partial Action (if needed)**
- Interpret as partial completion
- Generate diegetic explanation
- Reinterpret action for mechanics
- Create narrative description

### **5. Execute Action**
- Update actor positions
- Process through UTAS
- Generate outcome narrative
- Update spatial state

---

## 🎉 **SUMMARY**

**Complete spatial system provides:**
- 📐 **Position tracking** with zones and obstacles
- ⏱️ **Movement timing** based on distance and speed
- 🚫 **Never deny** - partial actions with diegetic explanations
- 🎭 **Narrative integration** - spatial context in descriptions
- 💾 **Persistence** - all spatial data saved to JSON
- 🎯 **Pre-seeded actors** - controlled introduction with payoff

**Result: Fully spatial, time-aware simulation with natural failure handling! 🎯**
