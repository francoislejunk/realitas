"""
World Spatial Integration - Bridge between local spatial system and world map

This module provides:
1. World-level distance tracking (between locations)
2. Travel time calculations using the same time unit system
3. NUA location awareness (where are they in the world?)
4. Sensory context for world-level perception

The key difference from local spatial:
- Local: Positions within a room/area (units = ~1 meter)
- World: Positions between locations (blocks = ~100 meters / city block)

Time Units:
- 3-second unit (action time) - for local movement
- 3-minute unit (travel time) - for world movement
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from location_distance_tracker import (
    get_location_tracker,
    LocationNode,
    LocationType,
    LocationEdge,
    TravelMethod,
    TRAVEL_SPEEDS,
)

# Import sensory constants for consistency
try:
    from sensory_constants import DistanceCategory
    SENSORY_AVAILABLE = True
except ImportError:
    SENSORY_AVAILABLE = False


# ═══════════════════════════════════════════════════════════════════════════════
# WORLD DISTANCE CATEGORIES
# ═══════════════════════════════════════════════════════════════════════════════

class WorldDistanceCategory(Enum):
    """Distance categories for world-level travel"""
    SAME_LOCATION = "same_location"      # 0 blocks: Same building/area
    ADJACENT = "adjacent"                 # 1-2 blocks: Next door, across street
    NEARBY = "nearby"                     # 3-5 blocks: Short walk
    MODERATE = "moderate"                 # 6-10 blocks: Decent walk
    FAR = "far"                           # 11-20 blocks: Long walk, consider transit
    DISTANT = "distant"                   # 21+ blocks: Need vehicle/transit


def get_world_distance_category(blocks: float) -> WorldDistanceCategory:
    """Get world distance category from blocks"""
    if blocks <= 0:
        return WorldDistanceCategory.SAME_LOCATION
    elif blocks <= 2:
        return WorldDistanceCategory.ADJACENT
    elif blocks <= 5:
        return WorldDistanceCategory.NEARBY
    elif blocks <= 10:
        return WorldDistanceCategory.MODERATE
    elif blocks <= 20:
        return WorldDistanceCategory.FAR
    else:
        return WorldDistanceCategory.DISTANT


# ═══════════════════════════════════════════════════════════════════════════════
# WORLD TRAVEL TIME INFO
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WorldTravelInfo:
    """Travel information between world locations"""
    from_location: str
    to_location: str
    distance_blocks: float
    category: WorldDistanceCategory
    
    # Travel times by method (in minutes)
    walk_minutes: float
    run_minutes: float
    drive_minutes: float
    transit_minutes: float
    
    # Time units (3-minute units for travel)
    walk_travel_units: int
    run_travel_units: int
    drive_travel_units: int
    transit_travel_units: int
    
    @classmethod
    def calculate(cls, from_loc: str, to_loc: str, 
                  distance_blocks: float) -> 'WorldTravelInfo':
        """Calculate travel info between locations"""
        import math
        
        category = get_world_distance_category(distance_blocks)
        
        # Calculate travel times
        walk_min = distance_blocks * TRAVEL_SPEEDS[TravelMethod.WALKING]
        run_min = distance_blocks * TRAVEL_SPEEDS[TravelMethod.RUNNING]
        drive_min = distance_blocks * TRAVEL_SPEEDS[TravelMethod.DRIVING]
        transit_min = distance_blocks * TRAVEL_SPEEDS[TravelMethod.PUBLIC_TRANSIT]
        
        # Convert to 3-minute travel units
        walk_units = max(1, math.ceil(walk_min / 3.0)) if distance_blocks > 0 else 0
        run_units = max(1, math.ceil(run_min / 3.0)) if distance_blocks > 0 else 0
        drive_units = max(1, math.ceil(drive_min / 3.0)) if distance_blocks > 0 else 0
        transit_units = max(1, math.ceil(transit_min / 3.0)) if distance_blocks > 0 else 0
        
        return cls(
            from_location=from_loc,
            to_location=to_loc,
            distance_blocks=distance_blocks,
            category=category,
            walk_minutes=walk_min,
            run_minutes=run_min,
            drive_minutes=drive_min,
            transit_minutes=transit_min,
            walk_travel_units=walk_units,
            run_travel_units=run_units,
            drive_travel_units=drive_units,
            transit_travel_units=transit_units,
        )
    
    def format_travel_options(self) -> str:
        """Format travel options for display"""
        lines = []
        lines.append(f"Distance: {self.distance_blocks:.1f} blocks ({self.category.value.upper()})")
        lines.append("")
        lines.append("Travel Options:")
        lines.append(f"  🚶 Walk:    {self.walk_minutes:.0f} min ({self.walk_travel_units} travel units)")
        lines.append(f"  🏃 Run:     {self.run_minutes:.0f} min ({self.run_travel_units} travel units)")
        lines.append(f"  🚗 Drive:   {self.drive_minutes:.0f} min ({self.drive_travel_units} travel units)")
        lines.append(f"  🚌 Transit: {self.transit_minutes:.0f} min ({self.transit_travel_units} travel units)")
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# WORLD SENSORY CONTEXT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class WorldSensoryInfo:
    """What can be perceived about a location from current position"""
    distance_blocks: float
    category: WorldDistanceCategory
    
    # What can be perceived
    can_see_building: bool          # Can see the building/location
    can_see_activity: bool          # Can see people moving around
    can_hear_sounds: bool           # Can hear sounds from location
    can_smell_location: bool        # Can smell (food, smoke, etc.)
    can_identify_people: bool       # Can identify specific people
    
    @classmethod
    def from_distance(cls, blocks: float) -> 'WorldSensoryInfo':
        """Create sensory info based on world distance"""
        category = get_world_distance_category(blocks)
        
        return cls(
            distance_blocks=blocks,
            category=category,
            can_see_building=blocks <= 10,      # Can see buildings up to 10 blocks
            can_see_activity=blocks <= 3,       # Can see people moving up to 3 blocks
            can_hear_sounds=blocks <= 2,        # Can hear sounds up to 2 blocks
            can_smell_location=blocks <= 1,     # Can smell up to 1 block (food, smoke)
            can_identify_people=blocks <= 1,    # Can identify people up to 1 block
        )
    
    def get_perception_description(self) -> str:
        """Get description of what can be perceived"""
        if self.category == WorldDistanceCategory.SAME_LOCATION:
            return "You are here - full sensory access"
        elif self.category == WorldDistanceCategory.ADJACENT:
            return "Very close - can see activity, hear sounds, possibly smell"
        elif self.category == WorldDistanceCategory.NEARBY:
            return "Short distance - can see the building and general activity"
        elif self.category == WorldDistanceCategory.MODERATE:
            return "Moderate distance - can see the building in the distance"
        elif self.category == WorldDistanceCategory.FAR:
            return "Far away - might see tall buildings, no details"
        else:
            return "Too distant - no direct perception possible"


# ═══════════════════════════════════════════════════════════════════════════════
# WORLD CONTEXT FOR NARRATOR
# ═══════════════════════════════════════════════════════════════════════════════

def get_world_context_for_narrator(
    current_location: str,
    target_location: Optional[str] = None,
    session_id: Optional[str] = None
) -> str:
    """
    Generate world-level context for narrator prompts.
    
    This tells the narrator what the UA knows about world locations
    and what they can perceive from their current position.
    """
    tracker = get_location_tracker(session_id)
    
    lines = ["**WORLD LOCATION CONTEXT:**"]
    lines.append(f"Current Location: {current_location}")
    
    # Get current location info
    current_node = tracker.get_location(current_location)
    if current_node:
        lines.append(f"Type: {current_node.location_type.value}")
        if current_node.known_nuas:
            lines.append(f"Known NPCs here: {', '.join(current_node.known_nuas)}")
    
    # If targeting a specific location
    if target_location and target_location != current_location:
        distance = tracker.get_distance(current_location, target_location)
        if distance is not None:
            travel_info = WorldTravelInfo.calculate(current_location, target_location, distance)
            sensory = WorldSensoryInfo.from_distance(distance)
            
            lines.append(f"\n**Target: {target_location}**")
            lines.append(f"Distance: {distance:.1f} blocks ({travel_info.category.value.upper()})")
            lines.append(f"Walk time: ~{travel_info.walk_minutes:.0f} minutes")
            lines.append(f"Perception: {sensory.get_perception_description()}")
            
            target_node = tracker.get_location(target_location)
            if target_node and target_node.known_nuas:
                lines.append(f"Known NPCs there: {', '.join(target_node.known_nuas)}")
    else:
        # Show nearby locations
        nearby = []
        for loc_name in tracker.locations.keys():
            if loc_name != current_location:
                dist = tracker.get_distance(current_location, loc_name)
                if dist is not None and dist <= 5:  # Within 5 blocks
                    nearby.append((loc_name, dist))
        
        if nearby:
            nearby.sort(key=lambda x: x[1])
            lines.append("\n**Nearby Locations:**")
            for loc_name, dist in nearby[:5]:
                category = get_world_distance_category(dist)
                lines.append(f"  - {loc_name}: {dist:.1f} blocks ({category.value})")
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# WORLD MAP COMMANDS
# ═══════════════════════════════════════════════════════════════════════════════

def handle_world_spatial_command(command: str, current_location: str, 
                                  session_id: Optional[str] = None) -> bool:
    """
    Handle world-level spatial commands.
    
    Commands:
        /world - Show world map with distances
        /travel <location> - Show travel options to location
        /nearby - Show nearby locations
        /nuas - Show where known NUAs are located
    
    Returns:
        True if command was handled, False otherwise
    """
    cmd = command.strip().lower()
    tracker = get_location_tracker(session_id)
    
    if cmd == "/world" or cmd == "/worldmap":
        _show_world_map(current_location, tracker)
        return True
    
    elif cmd.startswith("/travel "):
        target = command[8:].strip()
        _show_travel_info(current_location, target, tracker)
        return True
    
    elif cmd == "/nearby":
        _show_nearby_locations(current_location, tracker)
        return True
    
    elif cmd == "/nuas" or cmd == "/npcs":
        _show_nua_locations(tracker)
        return True
    
    return False


def _show_world_map(current_location: str, tracker) -> None:
    """Display world map with current location highlighted"""
    from world_map_visualizer import render_graph_map
    print(render_graph_map())


def _show_travel_info(from_loc: str, to_loc: str, tracker) -> None:
    """Show detailed travel information between locations"""
    # Try to find the location (partial match)
    target = None
    for loc_name in tracker.locations.keys():
        if to_loc.lower() in loc_name.lower():
            target = loc_name
            break
    
    if not target:
        print(f"Location '{to_loc}' not found in known locations.")
        print("Known locations:")
        for loc_name in tracker.locations.keys():
            print(f"  - {loc_name}")
        return
    
    distance = tracker.get_distance(from_loc, target)
    if distance is None:
        # Estimate distance
        distance = tracker.estimate_distance(from_loc, target)
        print(f"(Estimated distance - route not yet traveled)")
    
    travel_info = WorldTravelInfo.calculate(from_loc, target, distance)
    sensory = WorldSensoryInfo.from_distance(distance)
    
    print(f"\n{'='*50}")
    print(f"  TRAVEL: {from_loc} → {target}")
    print(f"{'='*50}")
    print(travel_info.format_travel_options())
    print(f"\nPerception: {sensory.get_perception_description()}")
    print(f"{'='*50}\n")


def _show_nearby_locations(current_location: str, tracker) -> None:
    """Show locations near current position"""
    print(f"\n{'='*40}")
    print(f"  NEARBY LOCATIONS (from {current_location})")
    print(f"{'='*40}")
    
    locations_with_dist = []
    for loc_name in tracker.locations.keys():
        if loc_name != current_location:
            dist = tracker.get_distance(current_location, loc_name)
            if dist is None:
                dist = tracker.estimate_distance(current_location, loc_name)
            locations_with_dist.append((loc_name, dist))
    
    locations_with_dist.sort(key=lambda x: x[1])
    
    for loc_name, dist in locations_with_dist[:10]:
        category = get_world_distance_category(dist)
        walk_min = dist * TRAVEL_SPEEDS[TravelMethod.WALKING]
        loc_node = tracker.get_location(loc_name)
        icon = "📍"
        if loc_node:
            from world_map_visualizer import get_location_icon
            icon = get_location_icon(loc_node.location_type)
        
        print(f"  {icon} {loc_name}")
        print(f"      {dist:.1f} blocks ({category.value}) - ~{walk_min:.0f} min walk")
    
    print(f"{'='*40}\n")


def _show_nua_locations(tracker) -> None:
    """Show where known NUAs are located"""
    print(f"\n{'='*40}")
    print(f"  NUA LOCATIONS")
    print(f"{'='*40}")
    
    nua_locations = {}
    for loc_name, loc_node in tracker.locations.items():
        for nua in loc_node.known_nuas:
            nua_locations[nua] = loc_name
    
    if not nua_locations:
        print("  No NUA locations known yet.")
    else:
        for nua, loc in sorted(nua_locations.items()):
            print(f"  👤 {nua}: {loc}")
    
    print(f"{'='*40}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# CONTINUITY INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_world_continuity_context(
    current_location: str,
    target_location: str,
    session_id: Optional[str] = None
) -> str:
    """
    Get world-level context for continuity checking.
    
    This tells the continuity checker if travel between locations is feasible.
    """
    tracker = get_location_tracker(session_id)
    
    distance = tracker.get_distance(current_location, target_location)
    if distance is None:
        distance = tracker.estimate_distance(current_location, target_location)
    
    travel_info = WorldTravelInfo.calculate(current_location, target_location, distance)
    
    lines = ["\n**WORLD TRAVEL CONTEXT:**"]
    lines.append(f"- Current Location: {current_location}")
    lines.append(f"- Target Location: {target_location}")
    lines.append(f"- Distance: {distance:.1f} blocks ({travel_info.category.value.upper()})")
    lines.append(f"- Walk Time: ~{travel_info.walk_minutes:.0f} minutes")
    lines.append("")
    lines.append("**TRAVEL FEASIBILITY:**")
    
    if travel_info.category == WorldDistanceCategory.SAME_LOCATION:
        lines.append("- ✅ Already at this location")
    elif travel_info.category == WorldDistanceCategory.ADJACENT:
        lines.append("- ✅ Very close - can walk there quickly")
    elif travel_info.category == WorldDistanceCategory.NEARBY:
        lines.append("- ✅ Short walk - feasible on foot")
    elif travel_info.category == WorldDistanceCategory.MODERATE:
        lines.append("- ⚠️ Moderate distance - will take some time")
    elif travel_info.category == WorldDistanceCategory.FAR:
        lines.append("- ⚠️ Far - consider vehicle or transit")
    else:
        lines.append("- ⚠️ Very far - will require significant travel time")
    
    return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("World Spatial Integration Test\n")
    
    # Test travel info
    print("=== Travel Info Test ===")
    travel = WorldTravelInfo.calculate("Apartment", "Diner", 5.0)
    print(travel.format_travel_options())
    
    print("\n=== Sensory Info Test ===")
    for blocks in [0, 1, 3, 5, 10, 25]:
        sensory = WorldSensoryInfo.from_distance(blocks)
        print(f"{blocks} blocks: {sensory.get_perception_description()}")
    
    print("\n=== World Distance Categories ===")
    for blocks in [0, 1, 3, 7, 15, 30]:
        cat = get_world_distance_category(blocks)
        print(f"{blocks} blocks: {cat.value}")
    
    print("\n✅ World spatial integration ready!")
