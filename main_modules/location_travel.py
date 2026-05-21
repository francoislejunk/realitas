"""Auto-extracted from redesigned_main.py"""

import sys
import os
import time
import re
import json
import random
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

# These imports will need to be adjusted based on what's actually used in each module

def _promote_world_destinations_from_text(text: str, *, source: str = 'narrative') -> None:
    try:
        t = (text or '').strip()
        if not t:
            return
        tl = t.lower()
    except Exception:
        return

    try:
        from location_distance_tracker import get_location_tracker
        from location_distance_tracker import LocationType, TravelMethod
    except Exception:
        return

    try:
        origin_loc = None
        try:
            from persistent_context_manager import get_context_manager
            cm = get_context_manager()
            origin_loc = getattr(getattr(cm, 'context', None), 'current_location', None) if cm else None
        except Exception:
            origin_loc = None
        if not origin_loc:
            origin_loc = 'Current Area'
    except Exception:
        origin_loc = 'Current Area'

    try:
        # Use default session if a specific session id isn't available in this scope.
        world_tracker = get_location_tracker(None)
    except Exception:
        return

    blocks = 3.0
    try:
        if any(k in tl for k in ('next door', 'next-door', 'adjacent')):
            blocks = 1.0
        elif any(k in tl for k in ('down the road', 'nearby', 'a short walk', 'short walk', 'close by', 'down the street', 'around the corner')):
            blocks = 3.0
        elif any(k in tl for k in ('across town', 'across the city', 'far', 'distant')):
            blocks = 12.0
    except Exception:
        blocks = 3.0

    candidates: list[tuple[str, LocationType]] = []
    try:
        patterns = [
            (r"\b(tavern|inn|pub|bar)\b", LocationType.ENTERTAINMENT),
            (r"\b(market|bazaar|shop|store)\b", LocationType.COMMERCIAL),
            (r"\b(temple|abbey|church|cathedral|ward|hospital)\b", LocationType.INSTITUTIONAL),
            (r"\b(plaza|square|street|road|alley|bridge|gate)\b", LocationType.OUTDOOR),
        ]
        import re
        for pat, ltype in patterns:
            for m in re.finditer(pat, tl):
                nm = (m.group(1) or '').strip()
                if nm:
                    candidates.append((nm.title(), ltype))
    except Exception:
        candidates = []

    if not candidates:
        return

    for loc_name, loc_type in candidates[:5]:
        try:
            world_tracker.add_location(loc_name, location_type=loc_type, description=f"Mentioned in {source}")
        except Exception:
            pass
        try:
            minutes = blocks * 3.0
            world_tracker.record_travel(origin_loc, loc_name, travel_time_minutes=minutes, method=TravelMethod.WALKING, route_description=f"Mentioned in {source}")
        except Exception:
            pass




def _print_arrival_opening(vehicle: str, label: str):
    """Narrative arrival opening based on vehicle."""
    label_text = label or "the next stop"
    if vehicle == "train":
        print(f"{Color.NARRATIVE}With a slowing hiss, the train eases into {label_text}. Doors slide open and a cool draft carries platform announcements inside.{Color.RESET}")
    elif vehicle == "bus":
        print(f"{Color.NARRATIVE}The bus brakes with a soft chuff at {label_text}. Doors fold open to the murmur of curbside traffic.{Color.RESET}")
    elif vehicle == "cab":
        print(f"{Color.NARRATIVE}The cab noses up to the curb at {label_text}. The driver glances back, tapping the meter impatiently.{Color.RESET}")
    elif vehicle == "plane":
        print(f"{Color.NARRATIVE}The aircraft rolls to a halt at the gate. The seatbelt sign dings off; the cabin door opens to the jet bridge.{Color.RESET}")
    else:
        print(f"{Color.NARRATIVE}You arrive at {label_text}. A brief pause settles over the moment.{Color.RESET}")



def _print_arrival_followup(vehicle: str, choice: str):
    """Narrative follow-up after the user's choice: 'exit' or 'stay'."""
    # Central rule: planes and cabs cannot be stayed in at arrival; force exit
    if choice != "exit" and vehicle in ("plane", "cab"):
        _print_forced_exit(vehicle)
        return
    if choice == "exit":
        if vehicle == "train":
            print(f"{Color.NARRATIVE}You step onto the platform as the doors chime behind you, the train idling for a beat before it pulls away.{Color.RESET}")
        elif vehicle == "bus":
            print(f"{Color.NARRATIVE}You step down to the curb; the bus exhales and merges back into traffic.{Color.RESET}")
        elif vehicle == "cab":
            print(f"{Color.NARRATIVE}You slide out of the cab; the door thunks shut and the driver pulls off with a short nod.{Color.RESET}")
        elif vehicle == "plane":
            print(f"{Color.NARRATIVE}You file into the jet bridge, air cooler and brighter than the cabin behind you.{Color.RESET}")
        else:
            print(f"{Color.NARRATIVE}You step out into your surroundings, the moment shifting to the world outside.{Color.RESET}")
    else:  # stay aboard
        if vehicle == "train":
            print(f"{Color.NARRATIVE}You remain aboard. The doors close; the platform slides away and you miss the stop.{Color.RESET}")
        elif vehicle == "bus":
            print(f"{Color.NARRATIVE}You stay in your seat. The doors fold shut and the bus pulls onward.{Color.RESET}")
        else:
            print(f"{Color.NARRATIVE}You stay put, letting the moment pass as the journey continues.{Color.RESET}")



class TravelChunkingState:
    """Tracks progress through multi-segment journeys with PERSISTENCE"""
    def __init__(self, context_manager):
        self.context_manager = context_manager
        
    @property
    def active_journey(self):
        if self.context_manager and self.context_manager.context:
            val = self.context_manager.context.active_journey
            print(f"[TRAVEL DEBUG] Getter: {val} (Context ID: {id(self.context_manager.context)})")
            return val
        print(f"[TRAVEL DEBUG] Getter Failed: Context Manager is None")
        return None
            
    @active_journey.setter
    def active_journey(self, value):
        if self.context_manager and self.context_manager.context:
            print(f"[TRAVEL DEBUG] Setter: {value} (Context ID: {id(self.context_manager.context)})")
            self.context_manager.context.active_journey = value
            self.context_manager._save() # Force save to disk immediately
        else:
            print(f"[TRAVEL DEBUG] Setter Failed: Context Manager is None")
    
    def start_journey(self, destination: str, total_minutes: int, origin: str = None):
        """Start a new chunked journey with intermediate locations and directional data"""
        print(f"{Color.SYSTEM}DEBUG: JOURNEY STARTING to {destination} ({total_minutes}m){Color.RESET}")
        segment_duration = 3  # Each segment is 3 minutes
        total_segments = max(1, total_minutes // segment_duration)
        
        # Calculate world-relative direction and distance
        direction_data = self._calculate_travel_direction(origin, destination, total_minutes)
        
        # Generate intermediate transitional locations for the route
        intermediate_locations = self._generate_route_locations(origin, destination, total_segments, direction_data)
        
        # Use setter to save to persistence
        self.active_journey = {
            "destination": destination,
            "origin": origin,
            "total_segments": total_segments,
            "current_segment": 0,
            "segment_duration": segment_duration,
            "total_minutes": total_minutes,
            "intermediate_locations": intermediate_locations,
            "current_location": origin,  # Track where we are now
            "direction": direction_data.get("cardinal_direction", ""),
            "world_distance": direction_data.get("world_distance", 0),
            "is_outdoor": direction_data.get("is_outdoor", False)
        }
        
        # Log directional info for world map building
        print(f"{Color.INFO}[WORLD] {destination} is {direction_data.get('cardinal_direction', 'nearby')} of {origin} (~{direction_data.get('world_distance', 0)} units){Color.RESET}")
        
        return total_segments
    
    def _calculate_travel_direction(self, origin: str, destination: str, travel_minutes: int) -> Dict[str, Any]:
        """
        Calculate the cardinal direction and world-relative distance between locations.
        This builds spatial understanding for the world map.
        
        Returns:
            dict with: cardinal_direction (N/S/E/W/NE/NW/SE/SW), world_distance, is_outdoor
        """
        origin_lower = (origin or "").lower()
        dest_lower = (destination or "").lower()
        
        # Detect outdoor vs indoor
        outdoor_indicators = ["street", "plaza", "park", "market", "square", "district", "alley", "road", "avenue", "boulevard", "lane", "way"]
        indoor_indicators = ["room", "office", "building", "floor", "apartment", "shop", "store", "bar", "club", "station", "terminal", "lobby"]
        
        is_outdoor = any(ind in origin_lower or ind in dest_lower for ind in outdoor_indicators)
        is_indoor = any(ind in origin_lower or ind in dest_lower for ind in indoor_indicators)
        
        # Estimate world distance based on travel time (1 minute ≈ 50 world units at walking pace)
        world_distance = travel_minutes * 50
        
        # Try to get actual coordinates from spatial system if available
        cardinal_direction = self._infer_cardinal_direction(origin, destination)
        
        return {
            "cardinal_direction": cardinal_direction,
            "world_distance": world_distance,
            "is_outdoor": is_outdoor and not is_indoor,
            "is_indoor": is_indoor and not is_outdoor
        }
    
    def _infer_cardinal_direction(self, origin: str, destination: str) -> str:
        """
        Infer cardinal direction from origin to destination.
        Uses location registry if available, otherwise infers from naming patterns.
        """
        # Try to get from location registry/spatial system
        try:
            from spatial_context_system import get_spatial_manager
            spatial = get_spatial_manager()
            
            # Check if we have world coordinates for these locations
            origin_ctx = spatial.contexts.get(origin) if origin else None
            dest_ctx = spatial.contexts.get(destination) if destination else None
            
            if origin_ctx and dest_ctx:
                # Get world coordinates if stored
                origin_world = getattr(origin_ctx, 'world_coordinates', None)
                dest_world = getattr(dest_ctx, 'world_coordinates', None)
                
                if origin_world and dest_world:
                    dx = dest_world[0] - origin_world[0]
                    dy = dest_world[1] - origin_world[1]
                    return self._coords_to_cardinal(dx, dy)
        except Exception:
            pass
        
        # Fallback: infer from location name patterns
        dest_lower = (destination or "").lower()
        
        # Common directional hints in location names
        if any(w in dest_lower for w in ["north", "upper", "uptown"]):
            return "N"
        elif any(w in dest_lower for w in ["south", "lower", "downtown"]):
            return "S"
        elif any(w in dest_lower for w in ["east", "right"]):
            return "E"
        elif any(w in dest_lower for w in ["west", "left"]):
            return "W"
        
        # Default: assign based on hash for consistency (same destination always same direction)
        import hashlib
        hash_val = int(hashlib.md5((destination or "").encode()).hexdigest()[:8], 16)
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        return directions[hash_val % 8]
    
    def _coords_to_cardinal(self, dx: float, dy: float) -> str:
        """Convert coordinate delta to cardinal direction"""
        import math
        if dx == 0 and dy == 0:
            return ""
        
        angle = math.degrees(math.atan2(dy, dx))
        # Convert to compass (0=E, 90=N, etc.)
        # Adjust so 0=N
        compass = (90 - angle) % 360
        
        if compass < 22.5 or compass >= 337.5:
            return "N"
        elif compass < 67.5:
            return "NE"
        elif compass < 112.5:
            return "E"
        elif compass < 157.5:
            return "SE"
        elif compass < 202.5:
            return "S"
        elif compass < 247.5:
            return "SW"
        elif compass < 292.5:
            return "W"
        else:
            return "NW"
    
    def _generate_route_locations(self, origin: str, destination: str, total_segments: int, direction_data: Dict[str, Any] = None) -> List[str]:
        """
        Generate intermediate transitional locations for a journey.
        Uses cardinal directions for outdoor travel, corridors/hallways for indoor.
        
        Args:
            origin: Starting location name
            destination: Target location name  
            total_segments: Number of travel segments
            direction_data: Dict with cardinal_direction, is_outdoor, is_indoor
        """
        if total_segments <= 1:
            return [destination]
        
        direction_data = direction_data or {}
        is_outdoor = direction_data.get("is_outdoor", False)
        is_indoor = direction_data.get("is_indoor", False)
        cardinal = direction_data.get("cardinal_direction", "")
        
        # Expand cardinal to full name for readability
        cardinal_names = {
            "N": "North", "S": "South", "E": "East", "W": "West",
            "NE": "Northeast", "NW": "Northwest", "SE": "Southeast", "SW": "Southwest"
        }
        direction_name = cardinal_names.get(cardinal, cardinal)
        
        # Select appropriate transitional types based on indoor/outdoor
        if is_outdoor:
            # Outdoor: use directional street names
            transitional_types = [
                f"{direction_name} Side Street",
                f"{direction_name} Alley", 
                f"{direction_name} Walkway",
                f"{direction_name} Path",
                f"Heading {direction_name}",
                f"{direction_name} Lane",
                f"{direction_name} Passage"
            ]
        elif is_indoor:
            # Indoor: use corridor/hallway names
            transitional_types = [
                "Corridor", "Hallway", "Passage", "Service Corridor", "Stairwell",
                "Connecting Walkway", "Interior Passage", "Access Corridor"
            ]
        else:
            # Mixed: use variety with direction hints
            transitional_types = [
                f"Passage ({direction_name})" if direction_name else "Passage",
                "Corridor", "Walkway", "Transit Area",
                f"Heading {direction_name}" if direction_name else "Connecting Path"
            ]
        
        # Generate route: origin -> [transitional spaces] -> destination
        route = []
        for i in range(total_segments - 1):
            # Pick transitional type based on segment (vary the types)
            trans_type = transitional_types[i % len(transitional_types)]
            route.append(trans_type)
        
        # Final segment is the destination
        route.append(destination)
        
        return route
    
    def advance_segment(self):
        """Move to next segment of journey, returning current transitional location"""
        journey = self.active_journey # Getter
        if journey:
            journey["current_segment"] += 1
            current_seg = journey["current_segment"]
            total_segs = journey["total_segments"]
            
            # Get the location for this segment
            intermediate_locs = journey.get("intermediate_locations", [])
            if current_seg <= len(intermediate_locs):
                current_loc = intermediate_locs[current_seg - 1]
                journey["current_location"] = current_loc
            
            if current_seg >= total_segs:
                # Journey complete
                dest = journey["destination"]
                self.active_journey = None # Setter (Clears and saves)
                return True, dest  # (completed, destination)
            
            # Save progress (Critical update)
            self.active_journey = journey # Setter (Saves updated count)
            
            # Return the current transitional location
            return False, journey.get("current_location")
        return False, None
    
    def get_current_transitional_location(self) -> Optional[str]:
        """Get the current intermediate location during travel"""
        journey = self.active_journey
        if journey:
            return journey.get("current_location")
        return None
    
    def cancel_journey(self):
        """User strayed from path - cancel journey"""
        self.active_journey = None # Setter (Clears and saves)
    
    def get_progress(self) -> Optional[Dict[str, Any]]:
        """Get current journey progress"""
        # print(f"{Color.SYSTEM}DEBUG: CHECKING PROGRESS{Color.RESET}")
        return self.active_journey
    
    def is_traveling(self) -> bool:
        """Check if a journey is active"""
        return self.active_journey is not None
    
    def create_transitional_context(self, spatial_manager, transitional_location: str, destination: str, session_id=None):
        """
        Create a spatial context for a transitional location during travel.
        Uses cardinal directions for outdoor locations instead of generic exits.
        
        Args:
            spatial_manager: The spatial context manager
            transitional_location: Name of the transitional space
            destination: Final destination name
            session_id: Optional session ID for spatial manager
        """
        from spatial_context_system import Position
        
        journey = self.active_journey
        if not journey:
            return
        
        is_outdoor = journey.get("is_outdoor", False)
        cardinal = journey.get("direction", "")
        
        # Check if context already exists
        if spatial_manager.location_exists(transitional_location):
            return
        
        # Create the transitional location
        # Use 'exterior' for outdoor, 'corridor' for indoor (avoids auto-door)
        location_type = "exterior" if is_outdoor else "corridor"

        # IMPORTANT: Transitional map dimensions should follow the current map's dimensions
        # (dynamic per location), not a hardcoded 250x200.
        from spatial_context_system import DEFAULT_MAP_WIDTH as _DMW, DEFAULT_MAP_HEIGHT as _DMH
        base_w = float(_DMW)
        base_h = float(_DMH)
        try:
            cur_ctx = spatial_manager.get_current_context()
            cur_dims = getattr(cur_ctx, 'location_dimensions', None) if cur_ctx else None
            if cur_dims:
                base_w = float(getattr(cur_dims, 'width', base_w) or base_w)
                base_h = float(getattr(cur_dims, 'height', base_h) or base_h)
        except Exception:
            base_w = float(_DMW)
            base_h = float(_DMH)

        # Fallback safety
        if base_w <= 0:
            base_w = float(_DMW)
        if base_h <= 0:
            base_h = float(_DMH)

        mid_x = base_w * 0.5
        mid_y = base_h * 0.5
        pad_x = max(1.0, base_w * 0.04)
        pad_y = max(1.0, base_h * 0.05)

        spatial_manager.create_location(
            location_name=transitional_location,
            width=base_w,
            height=base_h,
            location_type=location_type,
            description=f"A transitional space heading {cardinal} toward {destination}",
            auto_add_door=False  # Transitional spaces don't need doors
        )
        
        if is_outdoor:
            # Outdoor: use cardinal direction zones instead of walls/exits
            # Map cardinal to zone positions (N=top, S=bottom, E=right, W=left)
            direction_zones = {
                "N": (Position(mid_x, pad_y), (base_w * 0.80, base_h * 0.10), "north_passage"),
                "S": (Position(mid_x, base_h - pad_y), (base_w * 0.80, base_h * 0.10), "south_passage"),
                "E": (Position(base_w - pad_x, mid_y), (base_w * 0.08, base_h * 0.85), "east_passage"),
                "W": (Position(pad_x, mid_y), (base_w * 0.08, base_h * 0.85), "west_passage"),
                "NE": (Position(base_w * 0.88, base_h * 0.15), (base_w * 0.24, base_h * 0.24), "northeast_passage"),
                "NW": (Position(base_w * 0.12, base_h * 0.15), (base_w * 0.24, base_h * 0.24), "northwest_passage"),
                "SE": (Position(base_w * 0.88, base_h * 0.85), (base_w * 0.24, base_h * 0.24), "southeast_passage"),
                "SW": (Position(base_w * 0.12, base_h * 0.85), (base_w * 0.24, base_h * 0.24), "southwest_passage")
            }
            
            # Add the directional zone toward destination
            if cardinal in direction_zones:
                pos, size, zone_name = direction_zones[cardinal]
                spatial_manager.add_zone(
                    transitional_location, 
                    f"{zone_name}_to_{destination.lower().replace(' ', '_')}", 
                    pos, size, "passage"
                )
            
            # Add some street furniture for outdoor feel
            spatial_manager.add_obstacle(transitional_location, "street_lamp", Position(base_w * 0.20, base_h * 0.25), (max(2.0, base_w * 0.02), max(2.0, base_h * 0.02)), "prop")
            spatial_manager.add_obstacle(transitional_location, "street_lamp_2", Position(base_w * 0.80, base_h * 0.75), (max(2.0, base_w * 0.02), max(2.0, base_h * 0.02)), "prop")
        else:
            # Indoor: use corridor walls
            spatial_manager.add_obstacle(transitional_location, "left_wall", Position(pad_x, mid_y), (max(2.0, base_w * 0.04), base_h * 0.90), "wall", blocks_movement=True)
            spatial_manager.add_obstacle(transitional_location, "right_wall", Position(base_w - pad_x, mid_y), (max(2.0, base_w * 0.04), base_h * 0.90), "wall", blocks_movement=True)
            # Add passage zone at the end
            spatial_manager.add_zone(
                transitional_location, 
                f"passage_to_{destination.lower().replace(' ', '_')}", 
                Position(mid_x, pad_y), (base_w * 0.40, base_h * 0.10), "passage"
            )



def calculate_travel_time(origin: str, destination: str, spatial_manager=None) -> int:
    """
    Calculate realistic travel time in minutes between two locations.
    
    Priority:
    1. Check if returning to previous location (instant - 0 minutes)
    2. Check location_distance_tracker for known routes
    3. Fall back to LLM estimation for unknown routes
    
    Returns: minutes (integer)
    """
    # Normalize location names for comparison
    origin_lower = origin.lower().strip() if origin else ""
    dest_lower = destination.lower().strip() if destination else ""
    
    # PRIORITY 1: Check if returning to previous location (instant return)
    try:
        from persistent_context_manager import get_context_manager
        context_mgr = get_context_manager()
        if context_mgr and hasattr(context_mgr.context, 'previous_location'):
            prev_loc = (context_mgr.context.previous_location or "").lower().strip()
            if prev_loc and dest_lower and (prev_loc in dest_lower or dest_lower in prev_loc):
                print(f"{Color.SYSTEM}[TRAVEL TIME] {origin} → {destination}: 0 minutes (returning to previous location){Color.RESET}")
                return 0
    except Exception:
        pass
    
    # PRIORITY 2: Check location_distance_tracker for known routes
    try:
        tracker = get_location_tracker()
        travel_time, is_known = tracker.get_travel_time(origin_lower, dest_lower)
        if is_known:
            print(f"{Color.SYSTEM}[TRAVEL TIME] {origin} → {destination}: {int(travel_time)} minutes (from location tracker){Color.RESET}")
            return int(travel_time)
    except Exception as e:
        if not SUPPRESS_DEBUG:
            print(f"{Color.WARNING}[TRAVEL TIME] Location tracker lookup failed: {e}{Color.RESET}")
    
    # PRIORITY 3: Fall back to LLM estimation
    from openrouter_config import OpenRouterConfig, RetryConfig, robust_llm_call
    from json_utils import extract_and_parse_json
    
    client = OpenRouterConfig.create_client()
    
    # Get current location context if available
    origin_type = "unknown"
    if spatial_manager:
        try:
            context = spatial_manager.get_current_context()
            if context and context.location_dimensions:
                origin_type = context.location_dimensions.location_type or "unknown"
        except:
            pass
    
    prompt = f"""Calculate realistic walking travel time between two locations in an urban environment.

**ORIGIN:** {origin} (type: {origin_type})
**DESTINATION:** {destination}

**REALISTIC TRAVEL TIME GUIDELINES:**
- Same building (room to room): 0-1 minutes (instant, no chunking)
- Same building (floor to floor): 1-2 minutes (instant, no chunking)
- Adjacent buildings: 2-5 minutes (instant, no chunking)
- Same neighborhood: 5-15 minutes (needs chunking)
- Across town: 15-45 minutes (needs chunking)
- Across city: 45-90 minutes (needs chunking)

**EXAMPLES:**
- Apartment → Hallway: 0 minutes (same building)
- Hallway → Street: 1 minute (exiting building)
- Street → Nearby Diner: 5 minutes (same block)
- Home → Office across town: 30 minutes (different neighborhoods)
- Downtown → Suburbs: 60 minutes (cross-city)

**YOUR TASK:**
Estimate realistic walking time in minutes. Be conservative - walking takes time.

Respond ONLY with a JSON object (no markdown):
{{"minutes": <integer>, "reasoning": "<brief explanation>"}}"""

    response_text = robust_llm_call(
        client=client,
        messages=[{"role": "user", "content": prompt}],
        model=OpenRouterConfig.get_model_for_role("coordination"),
        temperature=0.1,
        max_tokens=150,
        max_retries=RetryConfig.MAX_RETRIES,
        call_name="TRAVEL TIME"
    )
    
    if response_text:
        result = extract_and_parse_json(response_text)
        if result:
            minutes = result.get("minutes", 3)
            reasoning = result.get("reasoning", "")
            print(f"{Color.SYSTEM}[TRAVEL TIME] {origin} → {destination}: {minutes} minutes ({reasoning}){Color.RESET}")
            return max(0, minutes)
    
    # Fallback
    print(f"{Color.WARNING}[TRAVEL TIME] Could not calculate, defaulting to 3 minutes{Color.RESET}")
    return 3



def _detect_location_move(user_text: str, action_result: str = None, spatial_manager=None) -> Optional[str]:
    """
    Detect if user input or action result indicates a location move.
    Uses LLM to intelligently detect location changes from context.
    Returns a location name if detected, else None.
    
    CRITICAL: Checks if target is an obstacle on current map first to avoid
    treating within-map movement as location changes.
    
    ENHANCED: Intelligently infers destination when user says "I leave", "I exit"
    without specifying where (e.g., infers "hallway" from apartment, "street" from building).
    """
    # Get current location context for intelligent inference
    current_location_name = "Unknown Location"
    current_location_type = "unknown"
    if spatial_manager:
        try:
            context = spatial_manager.get_current_context()
            if context and context.location_dimensions:
                current_location_name = context.location_dimensions.location_name or "Unknown Location"
                current_location_type = context.location_dimensions.location_type or "unknown"
                
                # Check if target is an obstacle on the current map
                user_lower = user_text.lower() if user_text else ""
                
                # Common in-room object keywords that should NEVER be location changes
                in_room_objects = [
                    'terminal', 'desk', 'chair', 'bed', 'table', 'shelf', 'cabinet', 
                    'fridge', 'refrigerator', 'door', 'window', 'screen', 'monitor',
                    'computer', 'console', 'workstation', 'locker', 'drawer', 'couch',
                    'sofa', 'lamp', 'light', 'vent', 'panel', 'cube', 'stack', 'pile',
                    'corner', 'wall', 'floor', 'ceiling', 'counter', 'sink', 'toilet',
                    'shower', 'mirror', 'closet', 'wardrobe', 'bookshelf', 'plant'
                ]
                
                # Check if user is moving to a common in-room object
                for obj in in_room_objects:
                    if obj in user_lower:
                        print(f"{Color.SYSTEM}[LOCATION] Target contains '{obj}' - treating as within-room movement{Color.RESET}")
                        return None  # Not a location change
                
                # Check if any obstacle name matches the target
                for obstacle_id, obstacle in context.location_dimensions.obstacles.items():
                    obstacle_name_lower = obstacle.obstacle_name.lower() if hasattr(obstacle, 'obstacle_name') else str(obstacle).lower()
                    # Check if obstacle name is in user input - require meaningful word match (3+ chars)
                    # Avoid false positives from short words like "a", "to", "the"
                    meaningful_words = [w for w in obstacle_name_lower.split() if len(w) >= 3]
                    if obstacle_name_lower in user_lower or any(f" {word} " in f" {user_lower} " for word in meaningful_words):
                        print(f"{Color.SYSTEM}[LOCATION] Target matches obstacle '{obstacle_name_lower}' - treating as within-map movement{Color.RESET}")
                        return None  # Not a location change, just movement to obstacle
        except Exception as e:
            print(f"{Color.WARNING}[LOCATION] Could not check obstacles: {e}{Color.RESET}")
    
    # Use LLM to analyze both user input and action result
    if user_text or action_result:
        try:
            from openrouter_config import OpenRouterConfig, RetryConfig, robust_llm_call
            from json_utils import extract_and_parse_json
            client = OpenRouterConfig.create_client()
            
            prompt = f"""Analyze the user's input to determine if the character moved to a NEW distinct location.

**CURRENT LOCATION:** {current_location_name} (type: {current_location_type})
**USER INPUT:** {user_text or "N/A"}
**ACTION RESULT:** {action_result or "N/A (action not yet processed)"}

**CRITICAL RULES:**
1. If ACTION RESULT is "N/A" or missing, analyze ONLY the user input
2. Questions/inquiries ("What do I see?", "Where am I?") are NOT location changes
3. Only detect location changes when there's clear intent to MOVE to a new place

**INTELLIGENT DESTINATION INFERENCE:**
When user says "I leave", "I exit", "I go outside" WITHOUT specifying destination:
- From apartment/room → infer "Hallway" or "Corridor"
- From building/house → infer "Street" or "Outside"
- From shop/store → infer "Street" or "Outside"
- From hallway → infer "Street" or "Building Entrance"
- From street → infer "Nearby Area" or "Another Street"

**Examples with Inference:**
- Current: "My Apartment" + "I leave" → NEW location: "Hallway"
- Current: "Office Building" + "I exit" → NEW location: "Street"
- Current: "Shop" + "I go outside" → NEW location: "Street"
- Current: "Hallway" + "I leave the building" → NEW location: "Street"
- Current: "My Apartment" + "I exit the door" → NEW location: "Hallway"

**Explicit Destination Examples:**
- "I go to the diner" → NEW location: "Diner"
- "I enter the bar" → NEW location: "Bar"
- "I head to the office" → NEW location: "Office"

**NOT Location Changes:**
- "What do I see?" → NO location change (question/inquiry)
- "I look around" → NO location change (observation, no movement)
- "I walk across the room" → NO location change (movement within same location)
- "I approach the workbench" → NO location change (movement within same location)

**YOUR TASK:**
1. Determine if this is a location change
2. If YES and destination is explicit → use that destination name
3. If YES but destination is NOT explicit (just "leave", "exit", etc.) → INFER the most logical destination based on current location type
4. If NO → return location_change: false

Respond ONLY with valid JSON (no markdown, no explanations):
{{"location_change": true, "location_name": "specific location name", "inferred": true/false}}
OR
{{"location_change": false}}"""

            # Use centralized robust LLM call
            response_text = robust_llm_call(
                client=client,
                messages=[{"role": "user", "content": prompt}],
                model=OpenRouterConfig.get_model_for_role("coordination"),
                temperature=0.2,
                max_tokens=150,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="LOCATION"
            )
            
            if not response_text:
                return None
            
            # Use centralized JSON extraction
            result = extract_and_parse_json(response_text)
            
            if not result:
                # Fallback: if simple "true"/"false" text, convert to JSON structure
                if response_text.lower().strip() == "true":
                    result = {"location_change": True}
                elif response_text.lower().strip() == "false":
                    result = {"location_change": False}
                else:
                    return None
            
            if result.get("location_change"):
                location_name = result.get("location_name", "Unknown Location")
                was_inferred = result.get("inferred", False)
                if was_inferred:
                    print(f"{Color.SYSTEM}[LOCATION] Intelligently inferred destination: {location_name}{Color.RESET}")
                return location_name
        except Exception as e:
            print(f"{Color.WARNING}[LOCATION] Could not detect location change: {e}{Color.RESET}")
    
    return None



def _apply_location_move(conductor, label: str, time_context, actor, previous_scene_desc: str, narrative_context_manager=None, tracker=None, available_npcs=None, population_manager=None, scene_creator=None, actor_registry=None) -> str:
    """Use the Conductor to generate a refreshed scene description for a new location.
    Does not increment scene_number; treated as an intra-scene location shift.
    Returns the new scene description. If NPCs are detected and created, adds them to available_npcs list.
    
    Args:
        scene_creator: Optional CreatorAgent with RAG system for NPC generation
        actor_registry: Optional dict to store/retrieve Actor objects by name for persistence
    """
    # Access global continuity_validator
    from scene_continuity_validator import continuity_validator
    
    try:
        # ============================================================
        # STEP 0: ARCHITECT FIRST - Establish spatial constraints
        # ============================================================
        # The Architect analyzes the location BEFORE population, ensuring:
        # - Valid space type and dimensions
        # - Maximum NPC capacity
        # - Pre-calculated spawn positions
        # - Forbidden/required objects from world memory
        spatial_constraints = None
        try:
            from agents.architect_agent import generate_spatial_constraints, get_valid_spawn_position, SpatialConstraints
            
            # Get RAG system from scene_creator if available
            rag_system = scene_creator.rag_system if scene_creator and hasattr(scene_creator, 'rag_system') else None

            # Centralized sizing: single source of truth for location scale hints.
            try:
                from location_sizer import LocationSizer
                sizing = LocationSizer.decide(label)
                expected_npc_count = int(getattr(sizing, 'expected_npc_count', 8) or 8)
                max_capacity_override = int(getattr(sizing, 'max_capacity', 0) or 0)
                override_dimensions = (
                    float(getattr(sizing, 'width', 0.0) or 0.0),
                    float(getattr(sizing, 'height', 0.0) or 0.0),
                )
                if max_capacity_override > 0:
                    expected_npc_count = min(expected_npc_count, max_capacity_override)
            except Exception:
                expected_npc_count = 8
                max_capacity_override = None
                override_dimensions = None
            
            spatial_constraints = generate_spatial_constraints(
                location_name=label,
                location_hint="",  # Could extract from previous context
                expected_npc_count=expected_npc_count,  # Initial estimate, will be refined
                rag_system=rag_system,
                override_dimensions=override_dimensions,
                max_capacity_override=max_capacity_override if (max_capacity_override and max_capacity_override > 0) else None
            )
            
            print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} Space: {spatial_constraints.space_type.value} | "
                  f"Size: {spatial_constraints.dimensions[0]:.0f}m × {spatial_constraints.dimensions[1]:.0f}m | "
                  f"Capacity: {spatial_constraints.max_capacity}")
            
            if spatial_constraints.required_elements:
                print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} Required elements: {', '.join(spatial_constraints.required_elements[:5])}")
            
            if spatial_constraints.architectural_style:
                print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} Style: {spatial_constraints.architectural_style}")
                
        except ImportError:
            print(f"{Color.WARNING}[ARCHITECT] Architect agent not available - using default spatial logic{Color.RESET}")
        except Exception as arch_e:
            print(f"{Color.WARNING}[ARCHITECT] Could not generate spatial constraints: {arch_e}{Color.RESET}")

        # ============================================================
        # SAFETY RETURN: ensure location shifts always return a usable scene string
        # ============================================================
        # The deeper population/location-state logic below has historically been fragile.
        # Never allow a successful Architect pass to result in returning None.
        try:
            scene_seed = f"A {spatial_constraints.space_type.value} called {label}" if spatial_constraints else f"A {label}"
        except Exception:
            scene_seed = f"A {label}"

        scene_data = {
            'setting': scene_seed,
            'transition_bridge': f"Moved to the {label}",
            'ua_goal': 'Explore and assess the situation',
            'conflict': 'Unknown; opportunities may arise'
        }
        try:
            if spatial_constraints:
                scene_data['spatial_constraints'] = spatial_constraints
        except Exception:
            pass

        new_desc = None
        try:
            new_desc = conductor.generate_scene_description(scene_data, scene_type='location_shift', time_context=time_context)
        except Exception:
            new_desc = None
        if not new_desc or len(str(new_desc).strip()) < 10:
            new_desc = f"You arrive at the {label}."

        try:
            if population_manager is not None and available_npcs is not None:
                try:
                    from persistent_context_manager import get_context_manager
                    _cm = get_context_manager()
                except Exception:
                    _cm = None

                try:
                    if isinstance(available_npcs, list):
                        available_npcs.clear()
                except Exception:
                    pass

                present_actors = []
                random_actors = []
                try:
                    present_actors = population_manager.get_present_actors(label, time_context) or []
                except Exception:
                    present_actors = []
                try:
                    random_actors = population_manager.check_random_spawns(label, time_context) or []
                except Exception:
                    random_actors = []

                all_population = []
                try:
                    all_population.extend(list(present_actors or []))
                    all_population.extend([a for a in (random_actors or []) if a not in all_population])
                except Exception:
                    all_population = list(present_actors or [])

                if not all_population:
                    try:
                        population_data = population_manager.generate_scene_population(
                            scene_description=f"{label} - {str(new_desc)[:200] if new_desc else 'A location'}",
                            time_context=time_context,
                            world_context=""
                        )
                        generated_actors, _background_atmosphere = population_manager.populate_actors(population_data)
                        if generated_actors:
                            all_population = list(generated_actors)
                    except Exception:
                        pass

                try:
                    max_to_add = int(spatial_constraints.max_capacity) if spatial_constraints else 20
                except Exception:
                    max_to_add = 20

                try:
                    for actor_obj in (all_population or []):
                        if len(available_npcs) >= max_to_add:
                            break
                        try:
                            available_npcs.append(actor_obj)
                        except Exception:
                            continue
                except Exception:
                    pass

                try:
                    if _cm is not None and hasattr(_cm, 'set_nuas'):
                        names = []
                        for a in (available_npcs or []):
                            try:
                                names.append(a.sheet.name)
                            except Exception:
                                continue
                        _cm.set_nuas(names)
                except Exception:
                    pass
        except Exception:
            pass

        try:
            from persistent_context_manager import get_context_manager
            cm = get_context_manager()
            if cm is not None and hasattr(cm, 'update_location'):
                cm.update_location(location=label, scene_description=str(new_desc), location_label=label, skip_npc_restore=True)
        except Exception:
            pass

        try:
            if conductor is not None:
                conductor.scene_description = str(new_desc)
        except Exception:
            pass
        try:
            if tracker is not None and hasattr(tracker, 'set_current_scene'):
                tracker.set_current_scene(str(new_desc))
        except Exception:
            pass

        # Ensure spatial/PMAP state is consistent with the narrative location.
        # Without this, the narrative can move to Tavern while PMAP remains on the previous location.
        try:
            from spatial_context_system import get_spatial_manager
            spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
        except Exception:
            spatial = None
        if spatial is not None:
            try:
                location_title = str(label or '').title()
            except Exception:
                location_title = str(label or '')

            try:
                if location_title:
                    if spatial.location_exists(location_title):
                        spatial.set_current_location(location_title)
                    else:
                        # Use Architect dimensions when available; otherwise let spatial defaults apply.
                        try:
                            w = float(spatial_constraints.dimensions[0]) if spatial_constraints else 24.0
                            h = float(spatial_constraints.dimensions[1]) if spatial_constraints else 18.0
                        except Exception:
                            w, h = 24.0, 18.0
                        try:
                            loc_type = spatial_constraints.space_type.value if spatial_constraints and getattr(spatial_constraints, 'space_type', None) else "unknown"
                        except Exception:
                            loc_type = "unknown"
                        spatial.create_location(
                            location_name=location_title,
                            width=w,
                            height=h,
                            location_type=loc_type,
                            description=str(new_desc)[:200] if new_desc else f"A {label}",
                            scene_description=str(new_desc or "")
                        )
                        spatial.set_current_location(location_title)
            except Exception:
                pass

            try:
                from spatial_context_system import Position
                ctx = spatial.get_current_context()
                dims = getattr(ctx, 'location_dimensions', None) if ctx else None
                map_w = float(getattr(dims, 'width', 0.0) or 0.0) if dims else 0.0
                map_h = float(getattr(dims, 'height', 0.0) or 0.0) if dims else 0.0
                if map_w > 0.0 and map_h > 0.0:
                    entrance_x = map_w / 2.0
                    entrance_y = map_h * 0.15
                    try:
                        if spatial.get_actor_position("ua_001"):
                            spatial.move_actor("ua_001", Position(entrance_x, entrance_y))
                        else:
                            spatial.add_actor(
                                actor_id="ua_001",
                                actor_name=actor.sheet.name,
                                position=Position(entrance_x, entrance_y),
                                is_user_actor=True,
                                occupation=getattr(actor.sheet, 'occupation', '') or ""
                            )
                    except Exception:
                        pass

                    if available_npcs:
                        import random
                        for npc in list(available_npcs or []):
                            base_id = None
                            try:
                                au = str(getattr(npc, 'actor_uuid', None) or '').strip()
                                if au:
                                    base_id = f"nua_{au}"
                            except Exception:
                                base_id = None
                            if not base_id:
                                try:
                                    base_id = f"nua_{npc.sheet.name.lower().replace(' ', '_')}"
                                except Exception:
                                    base_id = f"nua_{str(npc).lower().replace(' ', '_')}"

                            npc_id = base_id
                            try:
                                suffix = 2
                                while spatial.get_actor_position(npc_id):
                                    try:
                                        existing = spatial.get_actor_position(npc_id)
                                        if existing and str(getattr(existing, 'actor_name', '') or '') == str(getattr(npc.sheet, 'name', '') or ''):
                                            break
                                    except Exception:
                                        pass
                                    npc_id = f"{base_id}_{suffix}"
                                    suffix += 1
                            except Exception:
                                npc_id = base_id

                            try:
                                if spatial.get_actor_position(npc_id):
                                    continue
                            except Exception:
                                pass

                            if hasattr(npc, 'spatial_data') and isinstance(npc.spatial_data, dict) and 'spawn_position' in npc.spatial_data:
                                try:
                                    sp = npc.spatial_data['spawn_position']
                                    npc_x = float(sp[0]) * map_w
                                    npc_y = float(sp[1]) * map_h
                                except Exception:
                                    npc_x = map_w * (0.2 + 0.6 * random.random())
                                    npc_y = map_h * (0.3 + 0.5 * random.random())
                            else:
                                npc_x = map_w * (0.2 + 0.6 * random.random())
                                npc_y = map_h * (0.3 + 0.5 * random.random())

                            try:
                                spatial.add_actor(
                                    actor_id=npc_id,
                                    actor_name=npc.sheet.name,
                                    position=Position(npc_x, npc_y),
                                    is_user_actor=False,
                                    occupation=getattr(npc.sheet, 'occupation', '') or ""
                                )
                            except Exception:
                                pass
            except Exception:
                pass

            try:
                from pygame_spatial_map import sync_from_spatial_context, clear_layout_cache
                clear_layout_cache()
                sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
            except Exception:
                pass

        return str(new_desc)
    except Exception as e:
        print(f"{Color.ERROR}Critical error in _apply_location_move logic: {e}{Color.RESET}")
        import traceback
        traceback.print_exc()
        
        # ============================================================
        # STEP 1: GENERATE INITIAL SCENE SEED FOR NPC DETECTION
        # ============================================================
        # Generate a basic scene seed that describes what MIGHT be at this location
        # Now informed by Architect's spatial analysis
        if spatial_constraints:
            scene_seed = f"A {spatial_constraints.space_type.value} called {label}"
        else:
            scene_seed = f"A {label}"
            
        scene_data = {
            'setting': scene_seed,
            'transition_bridge': f"Moved to the {label}",
            'ua_goal': 'Explore and assess the situation',
            'conflict': 'Unknown; opportunities may arise'
        }
        
        # Add spatial constraints to scene_data for downstream use
        if spatial_constraints:
            scene_data['spatial_constraints'] = spatial_constraints
        
        # Generate initial scene seed for NPC detection (not the final description)
        initial_seed = conductor.generate_scene_description(scene_data, scene_type='location_shift', time_context=time_context)
        if not initial_seed or len(initial_seed.strip()) < 10:
            initial_seed = f"You arrive at the {label}. The area stretches before you."
        
        # ============================================================
        # STEP 2: POPULATE ENVIRONMENT (PERSISTENCE + SCHEDULE + RANDOM + NARRATIVE)
        # ============================================================
        # Reality principle: NPCs exist in locations whether you're there or not
        # When you arrive, you perceive the people who are ALREADY there
        context_manager = get_context_manager()

        # CRITICAL: Ensure we don't carry over NPC objects from the previous location.
        # The caller isn't guaranteed to clear `available_npcs` on every travel path.
        try:
            if available_npcs is not None:
                available_npcs.clear()
        except Exception:
            pass
        
        spawned_npc_names = []
        existing_names = set()
        
        # ============================================================
        # CHECK FOR SAVED LOCATION STATE (RETURNING TO PREVIOUSLY VISITED LOCATION)
        # ============================================================
        saved_nua_names = []
        if label in context_manager.context.location_states:
            saved_state = context_manager.context.location_states[label]
            saved_nua_names = saved_state.get('present_nuas', [])
            if saved_nua_names:
                print(f"{Color.INFO}[POPULATION] Returning to {label} - restoring {len(saved_nua_names)} saved NPC(s)...{Color.RESET}")
        
        context_manager.set_nuas([])  # Clear NPCs from previous location
        
        # IMPORTANT: Update location NOW before adding new NPCs
        # This ensures the OLD location's state is saved before we start adding new NPCs
        # Use skip_npc_restore=True to prevent restoring stale NPCs from cache
        # (We'll either restore them explicitly from saved_nua_names or generate fresh ones)
        context_manager.update_location(
            location=label,
            scene_description="",  # Will be updated later with final description
            location_label=label,
            skip_npc_restore=True  # Don't restore old NPCs - we handle this explicitly
        )
        
        # Track location in world map for distance/travel context
        try:
            location_tracker = get_location_tracker()
            old_location = location_tracker.current_location
            location_tracker.set_current_location(label)
            
            # If we have a previous location, record the travel (estimate 10 min walk if unknown)
            if old_location and old_location != label.lower():
                travel_time, is_known = location_tracker.get_travel_time(old_location, label)
                if not is_known:
                    # Record this as a new route (default 10 min walk)
                    location_tracker.record_travel(old_location, label, 10.0, TravelMethod.WALKING)
                print(f"{Color.INFO}[WORLD MAP] Traveled from {old_location} to {label}{Color.RESET}")
        except Exception as e:
            print(f"{Color.WARNING}[WORLD MAP] Could not update location tracker: {e}{Color.RESET}")
        
        # Update spatial context system location (for pygame map sync)
        # NOTE: Use title case for consistency
        # CRITICAL: Always ensure the spatial context is set to the new location
        try:
            from spatial_context_system import get_spatial_manager
            spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
            # Use title case to match what will be used later
            location_title = label.title()
            
            if spatial.location_exists(location_title):
                # Location exists - just switch to it
                spatial.set_current_location(location_title)
                spatial.clear_all_trails()
                print(f"{Color.SYSTEM}[SPATIAL] Switched to existing location: {location_title}{Color.RESET}")
            else:
                # Do NOT create placeholder locations with hardcoded dimensions here.
                # Defer location creation to the dynamic spatial analyzer/Architect path later in this flow.
                print(f"{Color.SYSTEM}[SPATIAL] Deferring location creation for: {location_title}{Color.RESET}")
        except Exception as e:
            print(f"{Color.WARNING}[SPATIAL] Could not update spatial location: {e}{Color.RESET}")
            import traceback
            traceback.print_exc()
        
        # 2a. Population Manager (Persistence + Schedule + Random + NEW LOCATION GENERATION)
        if population_manager:
            print(f"{Color.SYSTEM}[POPULATION] Checking for inhabitants at {label}...{Color.RESET}")
            try:
                # Aggregate population for this location. Start empty, then restore persistent cast,
                # then add schedule/random spawns, then only generate brand new actors if still empty.
                all_population = []

                # ============================================================
                # SQLITE ACTOR REGISTRY (RE-ENCOUNTER FIRST): restore persistent cast by stable UUID
                # ============================================================
                try:
                    from pathlib import Path as _Path
                    from context_store import ContextStore
                    from agents.tracker_agent import TrackerAgent

                    session_id = getattr(tracker, 'session_id', None) or 'default'
                    location_id = str(label)
                    store = ContextStore(_Path('simulation_data/context/context.db'))

                    cast = []
                    try:
                        cast = store.get_location_cast(session_id=session_id, location_id=location_id)
                    except Exception:
                        cast = []

                    if cast:
                        print(f"{Color.INFO}[POPULATION] Restoring {len(cast)} persistent cast member(s) from SQLite for {label}...{Color.RESET}")

                    # Use TrackerAgent's proven (de)serialization code path
                    _ser = TrackerAgent()

                    for c in cast:
                        try:
                            actor_uuid = str((c or {}).get('actor_uuid') or '')
                            if not actor_uuid:
                                continue
                            row = store.get_actor(session_id=session_id, actor_uuid=actor_uuid)
                            if not row:
                                continue

                            sheet_data = row.get('serialized_sheet') or {}
                            actor_type = str(row.get('actor_type') or 'NonUserActor')
                            restored_actor = _ser._deserialize_actor_sheet(sheet_data, actor_type)
                            # Stable identity on runtime object (Option A)
                            try:
                                setattr(restored_actor, 'actor_uuid', actor_uuid)
                            except Exception:
                                pass

                            # Mark present in this location
                            try:
                                wt = None
                                try:
                                    from context_store import WorldTime
                                    if get_master_time_coordinator is not None and WorldTime is not None:
                                        tc = get_master_time_coordinator()
                                        tctx = tc.get_current_time_context() if tc else None
                                        gt = tctx.get('game_time') if isinstance(tctx, dict) else None
                                        if gt is not None:
                                            wt = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
                                except Exception:
                                    wt = None
                                now_wms = wt.minutes_since_start if wt is not None else None
                                store.set_actor_location_state(
                                    session_id=session_id,
                                    actor_uuid=actor_uuid,
                                    current_location_id=location_id,
                                    presence_state='present',
                                    last_seen_world_minutes=int(now_wms) if now_wms is not None else None,
                                )
                            except Exception:
                                pass

                            all_population.append(restored_actor)
                            try:
                                existing_names.add(restored_actor.sheet.name)
                            except Exception:
                                pass
                        except Exception:
                            continue
                except Exception:
                    pass

                # Get present actors (Persistence + Schedule)
                present_actors = population_manager.get_present_actors(label, time_context)

                # Check random spawns (Atmosphere)
                random_actors = population_manager.check_random_spawns(label, time_context)

                # Merge schedule + random into restored population (avoid name duplicates)
                try:
                    for a in list(present_actors or []) + list(random_actors or []):
                        try:
                            nm = a.sheet.name
                        except Exception:
                            nm = None
                        if nm and nm in existing_names:
                            continue
                        all_population.append(a)
                        if nm:
                            existing_names.add(nm)
                except Exception:
                    pass
                
                # ============================================================
                # RESTORE SAVED NPCs: If returning to a previously visited location
                # ============================================================
                if saved_nua_names and not all_population:
                    print(f"{Color.INFO}[POPULATION] Restoring saved NPCs: {', '.join(saved_nua_names)}{Color.RESET}")
                    try:
                        # Try to get actors by name from the global actor registry
                        for nua_name in saved_nua_names:
                            restored_actor = None
                            # First try the global actor registry
                            if actor_registry and nua_name in actor_registry:
                                restored_actor = actor_registry[nua_name]
                            
                            if restored_actor:
                                all_population.append(restored_actor)
                                try:
                                    existing_names.add(restored_actor.sheet.name)
                                except Exception:
                                    pass
                                print(f"{Color.SUCCESS}[POPULATION] ✓ Restored: {nua_name}{Color.RESET}")

                                # One-time migration: ensure restored actors are in SQLite with stable UUID
                                try:
                                    from pathlib import Path as _Path
                                    from context_store import ContextStore
                                    import uuid as _uuid
                                    from agents.tracker_agent import TrackerAgent

                                    session_id = getattr(tracker, 'session_id', None) or 'default'
                                    location_id = str(label)
                                    store = ContextStore(_Path('simulation_data/context/context.db'))

                                    if not getattr(restored_actor, 'actor_uuid', None):
                                        setattr(restored_actor, 'actor_uuid', str(_uuid.uuid4()))
                                    au = str(getattr(restored_actor, 'actor_uuid', None) or '')
                                    if au:
                                        _ser = TrackerAgent()
                                        sheet_data = _ser._serialize_actor_sheet(restored_actor)
                                        store.upsert_actor(
                                            session_id=session_id,
                                            actor_uuid=au,
                                            display_name=getattr(restored_actor.sheet, 'name', ''),
                                            actor_type='NonUserActor' if not getattr(restored_actor, 'is_inanimate', False) else 'InanimateNonUserActor',
                                            serialized_sheet=sheet_data,
                                            tags=['location_cast']
                                        )
                                        store.add_actor_to_location_cast(
                                            session_id=session_id,
                                            location_id=location_id,
                                            actor_uuid=au,
                                            role='',
                                            schedule=None
                                        )
                                        store.set_actor_location_state(
                                            session_id=session_id,
                                            actor_uuid=au,
                                            current_location_id=location_id,
                                            presence_state='present'
                                        )
                                except Exception:
                                    pass
                            else:
                                # Legacy fallback: regenerate ONCE, then migrate to SQLite so it never re-generates again.
                                print(f"{Color.WARNING}[POPULATION] Regenerating (legacy): {nua_name} (not in registry){Color.RESET}")
                                try:
                                    context_str = f"Name: {nua_name}. Location: {label}. Role: Returning inhabitant."
                                    if scene_creator:
                                        nua = scene_creator.generate_nua(context_str, scene_description=f"Recreating {nua_name} at {label}")
                                        nua.sheet.name = nua_name  # Ensure exact name match

                                        # Assign stable UUID immediately (Option A)
                                        try:
                                            import uuid as _uuid
                                            if not getattr(nua, 'actor_uuid', None):
                                                setattr(nua, 'actor_uuid', str(_uuid.uuid4()))
                                        except Exception:
                                            pass

                                        all_population.append(nua)
                                        try:
                                            existing_names.add(nua.sheet.name)
                                        except Exception:
                                            pass

                                        # Register for future use
                                        if actor_registry is not None:
                                            actor_registry[nua_name] = nua

                                        # Persist to SQLite now so next visit restores by UUID
                                        try:
                                            from pathlib import Path as _Path
                                            from context_store import ContextStore
                                            from agents.tracker_agent import TrackerAgent

                                            session_id = getattr(tracker, 'session_id', None) or 'default'
                                            location_id = str(label)
                                            store = ContextStore(_Path('simulation_data/context/context.db'))
                                            au = str(getattr(nua, 'actor_uuid', None) or '')
                                            if au:
                                                _ser = TrackerAgent()
                                                sheet_data = _ser._serialize_actor_sheet(nua)
                                                store.upsert_actor(
                                                    session_id=session_id,
                                                    actor_uuid=au,
                                                    display_name=getattr(nua.sheet, 'name', ''),
                                                    actor_type='NonUserActor' if not getattr(nua, 'is_inanimate', False) else 'InanimateNonUserActor',
                                                    serialized_sheet=sheet_data,
                                                    tags=['location_cast']
                                                )
                                                store.add_actor_to_location_cast(
                                                    session_id=session_id,
                                                    location_id=location_id,
                                                    actor_uuid=au,
                                                    role='',
                                                    schedule=None
                                                )
                                                store.set_actor_location_state(
                                                    session_id=session_id,
                                                    actor_uuid=au,
                                                    current_location_id=location_id,
                                                    presence_state='present'
                                                )
                                        except Exception:
                                            pass

                                        print(f"{Color.SUCCESS}[POPULATION] ✓ Regenerated + migrated: {nua_name}{Color.RESET}")
                                except Exception as regen_e:
                                    print(f"{Color.WARNING}[POPULATION] Failed to regenerate {nua_name}: {regen_e}{Color.RESET}")
                    except Exception as restore_e:
                        print(f"{Color.WARNING}[POPULATION] Failed to restore saved NPCs: {restore_e}{Color.RESET}")
                
                # ============================================================
                # NEW LOCATION GENERATION: If no persistent/random/saved actors found,
                # generate appropriate population for this type of location
                # ============================================================
                if not all_population:
                    print(f"{Color.INFO}[POPULATION] First visit to {label} - generating appropriate population...{Color.RESET}")
                    # CRITICAL: Clear any stale NPC names from context before generating new ones
                    # This prevents old cached names from mixing with newly generated NPCs
                    context_manager.set_nuas([])
                    try:
                        # Generate population roster based on location type and time
                        population_data = population_manager.generate_scene_population(
                            scene_description=f"{label} - {initial_seed[:200] if initial_seed else 'A location'}",
                            time_context=time_context,
                            world_context=""
                        )
                        
                        # Convert roster to actual actors
                        generated_actors, background_atmosphere = population_manager.populate_actors(population_data)
                        
                        if generated_actors:
                            all_population = generated_actors
                            print(f"{Color.SUCCESS}[POPULATION] Generated {len(generated_actors)} inhabitant(s) for {label}{Color.RESET}")
                        
                        # Store background atmosphere for later use (e.g., promoting background actors)
                        if background_atmosphere:
                            print(f"{Color.INFO}[POPULATION] Background atmosphere: {background_atmosphere[:100]}...{Color.RESET}")
                            # Could store this in context_manager for future reference
                            
                    except Exception as gen_e:
                        print(f"{Color.WARNING}[POPULATION] Failed to generate population: {gen_e}{Color.RESET}")
                
                if available_npcs is not None:
                    # Respect Architect's capacity limit
                    max_to_add = spatial_constraints.max_capacity if spatial_constraints else 20
                    npc_index = 0
                    
                    for actor_obj in all_population:
                        if actor_obj.sheet.name not in existing_names:
                            # Check capacity
                            if len(available_npcs) >= max_to_add:
                                print(f"{Color.WARNING}[ARCHITECT] Capacity limit ({max_to_add}) reached - skipping {_ua_display_name(actor_obj)}{Color.RESET}")
                                continue
                            
                            available_npcs.append(actor_obj)
                            spawned_npc_names.append(actor_obj.sheet.name)
                            existing_names.add(actor_obj.sheet.name)
                            context_manager.add_nua(actor_obj.sheet.name)
                            
                            # ARCHITECT: Assign valid spawn position and add to spatial context
                            spawn_pos = None
                            if spatial_constraints:
                                try:
                                    from agents.architect_agent import get_valid_spawn_position
                                    spawn_pos = get_valid_spawn_position(spatial_constraints, npc_index)
                                    # Store position on actor for map system
                                    if not hasattr(actor_obj, 'spatial_data'):
                                        actor_obj.spatial_data = {}
                                    actor_obj.spatial_data['spawn_position'] = spawn_pos
                                    actor_obj.spatial_data['zone'] = spatial_constraints.valid_npc_zones[npc_index % len(spatial_constraints.valid_npc_zones)]['zone_type'] if spatial_constraints.valid_npc_zones else 'general'
                                    npc_index += 1
                                except Exception as pos_e:
                                    pass  # Silently continue if position assignment fails
                            
                            # Store spawn position for later spatial context registration
                            # (actual registration happens in _apply_location_move to avoid duplicates)
                            
                            # Register in global actor registry for future restoration
                            if actor_registry is not None:
                                actor_registry[actor_obj.sheet.name] = actor_obj

                            # SQLite actor registry: assign stable UUID, upsert full sheet, bind to location
                            try:
                                from pathlib import Path as _Path
                                from context_store import ContextStore
                                import uuid as _uuid
                                from agents.tracker_agent import TrackerAgent

                                session_id = getattr(tracker, 'session_id', None) or 'default'
                                location_id = str(label)
                                store = ContextStore(_Path('simulation_data/context/context.db'))

                                if not getattr(actor_obj, 'actor_uuid', None):
                                    setattr(actor_obj, 'actor_uuid', str(_uuid.uuid4()))
                                au = str(getattr(actor_obj, 'actor_uuid', None) or '')
                                if au:
                                    _ser = TrackerAgent()
                                    sheet_data = _ser._serialize_actor_sheet(actor_obj)
                                    store.upsert_actor(
                                        session_id=session_id,
                                        actor_uuid=au,
                                        display_name=getattr(actor_obj.sheet, 'name', ''),
                                        actor_type='NonUserActor' if not getattr(actor_obj, 'is_inanimate', False) else 'InanimateNonUserActor',
                                        serialized_sheet=sheet_data,
                                        tags=['location_cast']
                                    )
                                    store.add_actor_to_location_cast(
                                        session_id=session_id,
                                        location_id=location_id,
                                        actor_uuid=au,
                                        role='',
                                        schedule=None
                                    )
                                    store.set_actor_location_state(
                                        session_id=session_id,
                                        actor_uuid=au,
                                        current_location_id=location_id,
                                        presence_state='present'
                                    )
                            except Exception:
                                pass
                
                if spawned_npc_names:
                    print(f"{Color.SUCCESS}[POPULATION] Found/generated inhabitants: {', '.join(spawned_npc_names)}{Color.RESET}")

                # Persist the authoritative present-NUA list for this location.
                # Use actual runtime actor names (not roster roles / old cached names).
                try:
                    if context_manager and available_npcs is not None:
                        context_manager.set_nuas([npc.sheet.name for npc in available_npcs if hasattr(npc, 'sheet')])
                except Exception:
                    pass
            except Exception as e:
                print(f"{Color.WARNING}[POPULATION] Failed to retrieve population: {e}{Color.RESET}")

        # 2b. Narrative Spawning (Fallback/Flavor from RAG Seed)
        # Only spawn if name not already present
        try:
            from scene_npc_parser import auto_spawn_scene_npcs
            from agents.creator_agent import CreatorAgent
            
            # Use passed scene_creator (with RAG) or fall back to creating one without RAG
            local_scene_creator = scene_creator if scene_creator else CreatorAgent(conductor.logger)
            auto_memory_creator = None  # AutoMemoryCreator not yet implemented
            
            # Auto-spawn NPCs mentioned in the initial seed
            spawned_count = auto_spawn_scene_npcs(
                scene_description=initial_seed,
                creator_agent=local_scene_creator,
                available_npcs=available_npcs if available_npcs is not None else [],
                continuity_validator=continuity_validator,
                auto_memory_creator=auto_memory_creator,
                actor_name=actor.sheet.name,
                scene_id=f"location_{label}",
                mention_system=mention_system
            )
            
            # Update tracking lists for any NEWLY spawned NPCs
            # Also assign Architect spawn positions
            if available_npcs:
                max_to_add = spatial_constraints.max_capacity if spatial_constraints else 20
                npc_index = len(spawned_npc_names)  # Continue from where population manager left off
                
                for npc in available_npcs:
                    if npc.sheet.name not in existing_names:
                        # Check capacity
                        if len(spawned_npc_names) >= max_to_add:
                            print(f"{Color.WARNING}[ARCHITECT] Capacity limit ({max_to_add}) reached{Color.RESET}")
                            break
                            
                        spawned_npc_names.append(npc.sheet.name)
                        existing_names.add(npc.sheet.name)
                        context_manager.add_nua(npc.sheet.name)
                        
                        # ARCHITECT: Assign valid spawn position
                        spawn_pos = None
                        if spatial_constraints:
                            try:
                                from agents.architect_agent import get_valid_spawn_position
                                spawn_pos = get_valid_spawn_position(spatial_constraints, npc_index)
                                if not hasattr(npc, 'spatial_data'):
                                    npc.spatial_data = {}
                                npc.spatial_data['spawn_position'] = spawn_pos
                                npc.spatial_data['zone'] = spatial_constraints.valid_npc_zones[npc_index % len(spatial_constraints.valid_npc_zones)]['zone_type'] if spatial_constraints.valid_npc_zones else 'general'
                                npc_index += 1
                            except Exception:
                                pass
                        
                        # Store spawn position for later spatial context registration
                        # (actual registration happens in _apply_location_move to avoid duplicates)
                        
                        # Register in global actor registry for future restoration
                        if actor_registry is not None:
                            actor_registry[npc.sheet.name] = npc
            
            if spawned_count > 0:
                print(f"{Color.SUCCESS}[LOCATION] {spawned_count} narrative NPC(s) spawned at {label}{Color.RESET}")
            
        except Exception as e:
            print(f"{Color.WARNING}[LOCATION] Could not spawn NPCs: {e}{Color.RESET}")
            import traceback
            traceback.print_exc()

        # ============================================================
        # STEP 2c: MENTIONED ACTORS (LOCATION-BASED REINTRODUCTION)
        # ============================================================
        try:
            if available_npcs is not None:
                max_cap = spatial_constraints.max_capacity if spatial_constraints else 20
                remaining = max(0, int(max_cap) - int(len(available_npcs) if available_npcs else 0))
                if remaining > 0:
                    # Keep this conservative even if capacity is high.
                    # Mentioned actors should feel like meaningful re-encounters, not bulk population.
                    max_mention_spawns = min(2, remaining)
                    _ = _apply_mentioned_actor_reintroduction_policy(
                        available_npcs=available_npcs,
                        scene_description=f"Destination: {label}.\n\n{initial_seed}\n\n{scene_seed}",
                        scene_creator=scene_creator,
                        actor_registry=actor_registry,
                        max_spawns=max_mention_spawns,
                        allow_generation=True,
                    )
        except Exception:
            pass

        if not spawned_npc_names:
            print(f"{Color.SYSTEM}[LOCATION] No NPCs present at {label}{Color.RESET}")

        # ============================================================
        # STEP 2d: MENTION SYSTEM - SCAN UA CONTEXT (GOALS & MEMORIES)
        # ============================================================
        sync_mentions_from_ua_context(actor)

        # ============================================================
        # STEP 2e: ROLL INITIATIVE FOR ALL PRESENT ACTORS
        # ============================================================
        # This initiative persists until leaving the location
        if available_npcs:
            try:
                from initiative_system import get_location_initiative_tracker
                
                # Get the global initiative tracker and set initiative for this location
                init_tracker = get_location_initiative_tracker()
                turn_order = init_tracker.set_location_initiative(label, actor, available_npcs)
                
                if turn_order:
                    ua_pos = init_tracker.ua_position
                    print(f"{Color.INFO}[INITIATIVE] Turn order established for {label}:{Color.RESET}")
                    for i, entry in enumerate(turn_order):
                        marker = "→" if entry['is_user'] else " "
                        position_note = ""
                        if i < ua_pos:
                            position_note = " (acts before you)"
                        elif i > ua_pos:
                            position_note = " (acts after you)"
                        print(f"{Color.SYSTEM}  {marker} {i+1}. {entry['name']} (Initiative: {entry['score']}){position_note}{Color.RESET}")
            except ImportError:
                # Initiative system not available - use simple ordering
                print(f"{Color.SYSTEM}[INITIATIVE] Using default turn order (UA first){Color.RESET}")
            except Exception as e:
                print(f"{Color.WARNING}[INITIATIVE] Could not roll initiative: {e}{Color.RESET}")

        # ============================================================
        # STEP 3: GENERATE FINAL SCENE DESCRIPTION WITH NPC INFO
        # ============================================================
        # Now generate the FINAL scene description with knowledge of which NPCs are present
        # This ensures narrative consistency between description and game state
        
        # Frame the setting ACTIVE to force perceptual description
        # Use concrete action verbs for entry
        active_framing = f"You step into the {label}."
        
        if spawned_npc_names:
            # Pass actual NPC actor objects for stranger description system
            scene_data['npcs_present'] = available_npcs if available_npcs else []
            scene_data['ua_actor'] = actor  # For relationship checking
            scene_data['setting'] = f"{active_framing} You see {len(spawned_npc_names)} people scattered inside."
        else:
            scene_data['npcs_present'] = []
            scene_data['ua_actor'] = actor
            # Clearer prompt for empty room to avoid "It appears to be..." meta-talk
            scene_data['setting'] = f"{active_framing} The space is quiet and currently empty."

        try:
            from spatial_context_system import get_spatial_manager
            spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
            ctx = spatial.get_current_context() if spatial else None
            dims = getattr(ctx, 'location_dimensions', None) if ctx else None
            if dims:
                w = float(getattr(dims, 'width', 0.0) or 0.0)
                h = float(getattr(dims, 'height', 0.0) or 0.0)
                lines = []
                lines.append(f"Location: {getattr(dims, 'location_name', '') or label} | type={getattr(dims, 'location_type', '') or ''} | size={w:.1f}x{h:.1f}")

                def _zone_for_pos(p):
                    try:
                        for zn, zone in (getattr(dims, 'zones', {}) or {}).items():
                            if zone and hasattr(zone, 'contains_point') and zone.contains_point(p):
                                return str(getattr(zone, 'zone_name', None) or zn)
                    except Exception:
                        return ""
                    return ""

                for aid, apos in (getattr(ctx, 'actor_positions', {}) or {}).items():
                    try:
                        p = getattr(apos, 'position', None)
                        if not p:
                            continue
                        ax = float(getattr(p, 'x', 0.0) or 0.0)
                        ay = float(getattr(p, 'y', 0.0) or 0.0)
                        zn = _zone_for_pos(p)
                        zn_txt = f" zone={zn}" if zn else ""
                        name = str(getattr(apos, 'actor_name', '') or aid)
                        is_ua = bool(getattr(apos, 'is_user_actor', False))
                        tag = "UA" if is_ua else "NPC"
                        lines.append(f"- {tag} {name}: ({ax:.1f}, {ay:.1f}){zn_txt}")
                    except Exception:
                        continue

                scene_data['spatial_facts'] = "\n".join(lines)
        except Exception:
            pass
        
        new_desc = conductor.generate_scene_description(scene_data, scene_type='location_shift', time_context=time_context)
        if not new_desc or len(new_desc.strip()) < 10:
            # Fallback: Use the initial_seed if it was good, otherwise use generic
            if initial_seed and len(initial_seed.strip()) > 50:
                new_desc = initial_seed
                print(f"{Color.INFO}[LOCATION] Using initial scene description (second generation failed){Color.RESET}")
            else:
                new_desc = f"You arrive at the {label}. The area stretches before you, waiting to be explored."

        try:
            from scene_npc_parser import auto_spawn_scene_npcs
            from agents.creator_agent import CreatorAgent

            local_scene_creator = scene_creator if scene_creator else CreatorAgent(conductor.logger)
            auto_memory_creator = None

            auto_spawn_scene_npcs(
                scene_description=new_desc,
                creator_agent=local_scene_creator,
                available_npcs=available_npcs if available_npcs is not None else [],
                continuity_validator=continuity_validator,
                auto_memory_creator=auto_memory_creator,
                actor_name=actor.sheet.name,
                scene_id=f"location_{label}",
                mention_system=mention_system
            )

            if available_npcs:
                max_to_add = spatial_constraints.max_capacity if spatial_constraints else 20
                npc_index = len(spawned_npc_names)

                for npc in available_npcs:
                    if npc.sheet.name not in existing_names:
                        if len(spawned_npc_names) >= max_to_add:
                            break

                        spawned_npc_names.append(npc.sheet.name)
                        existing_names.add(npc.sheet.name)
                        context_manager.add_nua(npc.sheet.name)

                        spawn_pos = None
                        if spatial_constraints:
                            try:
                                from agents.architect_agent import get_valid_spawn_position
                                spawn_pos = get_valid_spawn_position(spatial_constraints, npc_index)
                                if not hasattr(npc, 'spatial_data'):
                                    npc.spatial_data = {}
                                npc.spatial_data['spawn_position'] = spawn_pos
                            except Exception:
                                pass
                        npc_index += 1
        except Exception:
            pass
        
        # Update conductor's internal scene text
        try:
            conductor.scene_description = new_desc
        except Exception:
            pass
        
        # Persist authoritative scene context to tracker
        try:
            if tracker is not None:
                tracker.set_current_scene(new_desc, location_label=label)
        except Exception:
            pass
        
        # SAVE FINAL SCENE DESCRIPTION TO PERSISTENT CONTEXT
        # (Location was already updated earlier, before adding NPCs)
        context_manager.update_scene_description(new_desc)

        # Continuity facts: location shift description anchors (high-ish confidence)
        _trace_continuity_fact_capture(new_desc, source="location_shift", base_confidence=0.85)

        try:
            _capture_mentioned_actors_from_text(new_desc, source="location_shift")
        except Exception:
            pass

        # ============================================================
        # AUTO-SAVEPOINT (AFTER LOCATION POPULATION)
        # ============================================================
        # Critical rule: only save AFTER the location is fully populated (NPCs restored/generated)
        # and the final scene description has been produced.
        try:
            if tracker is not None:
                try:
                    tracker.set_current_scene(new_desc, location_label=label)
                except Exception:
                    pass
                try:
                    tracker.save_available_npcs(list(available_npcs or []))
                except Exception:
                    pass
        except Exception:
            pass
        
        # ============================================================
        # OLD NPC DETECTION CODE (PRESERVED FOR ROLLBACK IF NEEDED)
        # ============================================================
        # try:
        #     from enhanced_dynamic_actor_system import EnhancedDynamicActorDetector
        #     from multi_actor_manager import MultiActorManager, ActorRole
        #     
        #     # Create temporary actor manager for detection
        #     temp_manager = MultiActorManager()
        #     detector = EnhancedDynamicActorDetector(temp_manager)
        #     
        #     # Check scene description for NUA mentions
        #     nua_detection = detector.detect_new_actor_mention(new_desc)
        #     
        #     if nua_detection and nua_detection.get('type') == 'NUA':
        #         nua_name = nua_detection.get('name', 'Unknown')
        #         print(f"{Color.SYSTEM}[LOCATION] Detected NUA in new location: {nua_name}{Color.RESET}")
        #         
        #         # Create the NUA
        #         from dynamic_actor_system import DynamicActorSystem
        #         dynamic_system = DynamicActorSystem(conductor.scene_creator)
        #         new_nua = dynamic_system.creator.create_dynamic_actor(
        #             {'name': nua_name, 'type': 'NUA', 'context': f"Located at {label}"},
        #             new_desc
        #         )
        #         
        #         if new_nua:
        #             print(f"{Color.SUCCESS}✓ Created location NUA: {new_nua.sheet.name}{Color.RESET}")
        #             # Add to available NUAs list if provided
        #             if available_npcs is not None:
        #                 available_npcs.append(new_nua)
        #             # Store in context manager
        #             context_manager.add_nua(new_nua.sheet.name)
        # except Exception as e:
        #     print(f"{Color.WARNING}[LOCATION] Could not detect/create location NPCs: {e}{Color.RESET}")
        # ============================================================
        
        # UPDATE SPATIAL CONTEXT (new location) - DYNAMIC ANALYSIS
        try:
            from spatial_context_system import get_spatial_manager, Position, Obstacle
            from spatial_location_analyzer import analyze_scene_for_spatial
            
            spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
            
            # Check if location already exists
            location_title = label.title()
            analysis = None  # Initialize to None for existing locations
            loc_type = "unknown"  # Default value
            reasoning = ""  # Default value

            land_vehicle_keys = [
                "wagon", "cart", "carriage", "coach", "stagecoach",
                "car", "automobile", "truck", "van", "motorcycle", "bike",
            ]

            is_land_vehicle_label = any(k in str(label or "").lower() for k in land_vehicle_keys)
            original_vehicle_label = None

            if is_land_vehicle_label and new_desc:
                original_vehicle_label = str(label)
                try:
                    from openrouter_config import OpenRouterConfig
                    client = OpenRouterConfig.create_client()
                    model = OpenRouterConfig.get_model_for_role("coordination")
                    prompt = f"""You are choosing the CURRENT LOCATION NAME for a scene.

The user-facing label that was proposed is a LAND VEHICLE: {original_vehicle_label}
Land vehicles are NOT locations. The location should be the surrounding place where that vehicle is located.

Scene description:
{new_desc}

Return JSON only:
{{"surrounding_location": "<short place name>", "location_type": "interior"|"exterior"}}"""

                    resp = client.chat.completions.create(
                        model=model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2,
                        max_tokens=120,
                    )
                    txt = (resp.choices[0].message.content or "").strip()
                    if "```" in txt:
                        j0 = txt.find("{")
                        j1 = txt.rfind("}")
                        if j0 != -1 and j1 != -1 and j1 > j0:
                            txt = txt[j0:j1+1]
                    import json
                    data = json.loads(txt)
                    chosen = str((data.get("surrounding_location") or "")).strip()
                    chosen_type = str((data.get("location_type") or "")).strip().lower()
                    if chosen:
                        location_title = chosen.title()
                        if chosen_type in ["interior", "exterior", "street", "building", "room"]:
                            loc_type = chosen_type
                except Exception:
                    pass
            
            if spatial.location_exists(location_title):
                print(f"{Color.SYSTEM}[SPATIAL] Location '{location_title}' already exists, reusing existing map{Color.RESET}")
                spatial.set_current_location(location_title)
                # Get dimensions from existing location
                context = spatial.get_current_context()
                width = context.location_dimensions.width
                height = context.location_dimensions.height
                # Update scene_description if we have a new one (for LLM layout generator)
                if new_desc and (not context.location_dimensions.scene_description or len(context.location_dimensions.scene_description) < len(new_desc)):
                    context.location_dimensions.scene_description = new_desc
                    print(f"{Color.SYSTEM}[SPATIAL] Updated scene description ({len(new_desc)} chars){Color.RESET}")
            else:
                # Prefer the same sizing path as the intro scene: analyze the FULL scene description.
                analysis = None
                try:
                    print(f"{Color.SYSTEM}[SPATIAL] Analyzing location dimensions (scene-driven)...{Color.RESET}")
                    analysis = analyze_scene_for_spatial(new_desc, label)
                except Exception:
                    analysis = None

                if isinstance(analysis, dict) and analysis.get("width") and analysis.get("height"):
                    width = analysis.get("width")
                    height = analysis.get("height")
                    loc_type = analysis.get("location_type") or loc_type
                    reasoning = analysis.get("reasoning", "")
                    print(f"{Color.SYSTEM}[SPATIAL] Sizing source: scene_analyzer ({float(width):.0f}x{float(height):.0f} {loc_type}){Color.RESET}")
                elif spatial_constraints:
                    width = spatial_constraints.dimensions[0]
                    height = spatial_constraints.dimensions[1]
                    loc_type = spatial_constraints.space_type.value
                    reasoning = f"Architect determined (fallback): {loc_type}"
                    print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} Sizing source: architect_fallback ({float(width):.0f}x{float(height):.0f} {loc_type})")
                else:
                    width = 12.0
                    height = 9.0
                    loc_type = "interior"
                    reasoning = "Default fallback dimensions"
                    print(f"{Color.WARNING}[SPATIAL] Sizing source: default_fallback ({float(width):.0f}x{float(height):.0f} {loc_type}){Color.RESET}")

                # Create new location with analyzed/architected dimensions
                spatial.create_location(
                    location_name=location_title,
                    width=float(width),
                    height=float(height),
                    location_type=loc_type,
                    description=new_desc[:200] if new_desc else f"A {label}",
                    scene_description=new_desc or ""  # Full scene description for LLM layout generator
                )
                spatial.set_current_location(location_title)
                print(f"{Color.SYSTEM}[SPATIAL] Created location: {location_title} ({float(width):.1f}x{float(height):.1f}){Color.RESET}")

            if original_vehicle_label:
                try:
                    context = spatial.get_current_context()
                    dims = context.location_dimensions if context else None
                    if dims is not None:
                        veh_id = "land_vehicle_prop"
                        if veh_id not in dims.obstacles:
                            w = max(2.0, min(float(dims.width) * 0.25, 8.0))
                            h = max(1.8, min(float(dims.height) * 0.18, 6.0))
                            cx = float(dims.width) * 0.50
                            cy = float(dims.height) * 0.55
                            dims.obstacles[veh_id] = Obstacle(
                                obstacle_name=original_vehicle_label.title(),
                                obstacle_type="vehicle",
                                boundary_points=[
                                    Position(cx - w/2, cy - h/2),
                                    Position(cx + w/2, cy - h/2),
                                    Position(cx + w/2, cy + h/2),
                                    Position(cx - w/2, cy + h/2),
                                ],
                                blocks_movement=True,
                                blocks_line_of_sight=True,
                                height=2.0,
                            )
                            try:
                                spatial._save()
                            except Exception:
                                pass
                except Exception:
                    pass
            
            # Move UA to entrance (front of location)
            MAP_WIDTH = float(width)
            MAP_HEIGHT = float(height)
            entrance_x = MAP_WIDTH / 2  # Center horizontally
            entrance_y = MAP_HEIGHT * 0.15  # Near front (15% from bottom)
            
            # Check if actor exists, add if not
            existing_pos = spatial.get_actor_position("ua_001")
            if existing_pos:
                spatial.move_actor("ua_001", Position(entrance_x, entrance_y))
                print(f"{Color.SYSTEM}[SPATIAL] Moved UA to entrance ({entrance_x:.1f}, {entrance_y:.1f}){Color.RESET}")
            else:
                # Actor doesn't exist, add it
                spatial.add_actor(
                    actor_id="ua_001",
                    actor_name=actor.sheet.name,
                    position=Position(entrance_x, entrance_y),
                    is_user_actor=True,
                    occupation=getattr(actor.sheet, 'occupation', '') or ""
                )
                print(f"{Color.SYSTEM}[SPATIAL] Added UA at entrance ({entrance_x:.1f}, {entrance_y:.1f}){Color.RESET}")
            
            # Add NPCs to spatial system - use Architect's spawn positions if available
            if available_npcs:
                import random
                num_npcs = len(available_npcs)
                for i, npc in enumerate(available_npcs):
                    base_id = None
                    try:
                        au = str(getattr(npc, 'actor_uuid', None) or '').strip()
                        if au:
                            base_id = f"nua_{au}"
                    except Exception:
                        base_id = None
                    if not base_id:
                        try:
                            npc_name_lower = npc.sheet.name.lower().replace(' ', '_')
                        except Exception:
                            npc_name_lower = str(npc).lower().replace(' ', '_')
                        base_id = f"nua_{npc_name_lower}"

                    npc_id = base_id
                    try:
                        suffix = 2
                        while spatial.get_actor_position(npc_id):
                            try:
                                existing = spatial.get_actor_position(npc_id)
                                if existing and str(getattr(existing, 'actor_name', '') or '') == str(getattr(npc.sheet, 'name', '') or ''):
                                    break
                            except Exception:
                                pass
                            npc_id = f"{base_id}_{suffix}"
                            suffix += 1
                    except Exception:
                        npc_id = base_id
                    
                    # Check if NPC already exists in spatial
                    existing_npc_pos = spatial.get_actor_position(npc_id)
                    if existing_npc_pos:
                        continue  # Already positioned
                    
                    # ARCHITECT: Use pre-calculated spawn position if available
                    if hasattr(npc, 'spatial_data') and 'spawn_position' in npc.spatial_data:
                        spawn_pos = npc.spatial_data['spawn_position']
                        npc_x = float(spawn_pos[0]) * MAP_WIDTH  # Convert normalized to map coords
                        npc_y = float(spawn_pos[1]) * MAP_HEIGHT
                        zone_info = npc.spatial_data.get('zone', 'general')
                        print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} Placed '{_ua_display_name(npc, ua_actor=actor)}' in {zone_info} zone")
                    else:
                        # Fallback: Distribute NPCs throughout the space (not at entrance)
                        npc_x = MAP_WIDTH * (0.2 + 0.6 * random.random())  # 20-80% of width
                        npc_y = MAP_HEIGHT * (0.3 + 0.5 * random.random())  # 30-80% of height
                    
                    spatial.add_actor(
                        actor_id=npc_id,
                        actor_name=npc.sheet.name,
                        position=Position(npc_x, npc_y),
                        is_user_actor=False,
                        occupation=getattr(npc.sheet, 'occupation', '') or ""
                    )
                    print(f"{Color.SYSTEM}[SPATIAL] Added NPC '{_ua_display_name(npc, ua_actor=actor)}' at ({npc_x:.1f}, {npc_y:.1f}){Color.RESET}")
            
            # Add zones from LLM suggestions (only for new locations)
            if analysis is not None:
                from spatial_context_system import Obstacle, Zone
                context = spatial.get_current_context()
                
                # For streets, create horizontal bands; for buildings, use position hints
                is_street = loc_type == "exterior" and any(word in label.lower() for word in ['street', 'road', 'alley'])
                
                if is_street and len(analysis.get("suggested_zones", [])) >= 2:
                    # Street layout: divide into horizontal bands
                    zones_list = analysis.get("suggested_zones", [])
                    num_zones = min(len(zones_list), 4)
                    band_height = MAP_HEIGHT / num_zones
                    
                    for i, zone_data in enumerate(zones_list[:num_zones]):
                        try:
                            zone_name = zone_data.get("name", f"Zone {i+1}")
                            zone_desc = zone_data.get("description", "")
                            
                            # Create horizontal band
                            y_start = i * band_height
                            y_end = (i + 1) * band_height
                            
                            zone_bounds = [
                                Position(0, y_start),
                                Position(MAP_WIDTH, y_start),
                                Position(MAP_WIDTH, y_end),
                                Position(0, y_end)
                            ]
                            
                            zone = Zone(
                                zone_name=zone_name,
                                zone_type=zone_desc[:50] if zone_desc else "area",
                                boundary_points=zone_bounds
                            )
                            context.location_dimensions.zones[zone_name.lower().replace(" ", "_")] = zone
                            print(f"{Color.SYSTEM}[SPATIAL] Added zone: {zone_name} (band {i+1}/{num_zones}){Color.RESET}")
                        except Exception as e:
                            print(f"{Color.WARNING}[SPATIAL] Could not add zone {zone_data.get('name', 'unknown')}: {e}{Color.RESET}")
                else:
                    # Building layout: use position hints with standardized coords
                    for zone_data in analysis.get("suggested_zones", [])[:4]:
                        try:
                            zone_name = zone_data.get("name", "Area")
                            zone_desc = zone_data.get("description", "")
                            position_hint = zone_data.get("position", "center")
                            
                            # Convert position hint to zone boundaries
                            if position_hint == "front":
                                zone_bounds = [
                                    Position(0, 0),
                                    Position(MAP_WIDTH, 0),
                                    Position(MAP_WIDTH, MAP_HEIGHT*0.3),
                                    Position(0, MAP_HEIGHT*0.3)
                                ]
                            elif position_hint == "back":
                                zone_bounds = [
                                    Position(0, MAP_HEIGHT*0.7),
                                    Position(MAP_WIDTH, MAP_HEIGHT*0.7),
                                    Position(MAP_WIDTH, MAP_HEIGHT),
                                    Position(0, MAP_HEIGHT)
                                ]
                            elif position_hint == "left":
                                zone_bounds = [
                                    Position(0, 0),
                                    Position(MAP_WIDTH*0.3, 0),
                                    Position(MAP_WIDTH*0.3, MAP_HEIGHT),
                                    Position(0, MAP_HEIGHT)
                                ]
                            elif position_hint == "right":
                                zone_bounds = [
                                    Position(MAP_WIDTH*0.7, 0),
                                    Position(MAP_WIDTH, 0),
                                    Position(MAP_WIDTH, MAP_HEIGHT),
                                    Position(MAP_WIDTH*0.7, MAP_HEIGHT)
                                ]
                            else:  # center
                                zone_bounds = [
                                    Position(MAP_WIDTH*0.2, MAP_HEIGHT*0.2),
                                    Position(MAP_WIDTH*0.8, MAP_HEIGHT*0.2),
                                    Position(MAP_WIDTH*0.8, MAP_HEIGHT*0.8),
                                    Position(MAP_WIDTH*0.2, MAP_HEIGHT*0.8)
                                ]
                            
                            zone = Zone(
                                zone_name=zone_name,
                                zone_type=zone_desc[:50] if zone_desc else "area",
                                boundary_points=zone_bounds
                            )
                            context.location_dimensions.zones[zone_name.lower().replace(" ", "_")] = zone
                            print(f"{Color.SYSTEM}[SPATIAL] Added zone: {zone_name}{Color.RESET}")
                        except Exception as e:
                            print(f"{Color.WARNING}[SPATIAL] Could not add zone {zone_data.get('name', 'unknown')}: {e}{Color.RESET}")
                
                # Add obstacles - ARCHITECT INTERIOR DESIGN SYSTEM
                # Generate realistic room layout based on room type and design principles
                context = spatial.get_current_context()
                
                print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} Generating realistic interior layout...")
                
                try:
                    from agents.architect_agent import generate_realistic_layout, extract_objects_from_description
                    
                    # First, extract any objects mentioned in the narrative
                    extracted_objects = extract_objects_from_description(new_desc)
                    
                    # Generate realistic layout using interior design principles
                    layout_obstacles = generate_realistic_layout(
                        scene_description=new_desc,
                        location_name=label.title(),
                        width=width,
                        height=height,
                        extracted_objects=extracted_objects if extracted_objects else None
                    )
                    
                    if layout_obstacles:
                        print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} Generated {len(layout_obstacles)} furniture pieces with realistic placement")
                        
                        for obs_data in layout_obstacles:
                            try:
                                obs_x = obs_data['x']
                                obs_y = obs_data['y']
                                obs_w = obs_data.get('width', 2.0)
                                obs_h = obs_data.get('height', 2.0)
                                
                                obstacle = Obstacle(
                                    obstacle_name=obs_data['name'],
                                    obstacle_type=obs_data['type'],
                                    boundary_points=[
                                        Position(obs_x - obs_w/2, obs_y - obs_h/2),
                                        Position(obs_x + obs_w/2, obs_y - obs_h/2),
                                        Position(obs_x + obs_w/2, obs_y + obs_h/2),
                                        Position(obs_x - obs_w/2, obs_y + obs_h/2)
                                    ],
                                    blocks_movement=obs_data.get('blocks_movement', True),
                                    blocks_line_of_sight=obs_data.get('blocks_los', False)
                                )
                                context.location_dimensions.obstacles[obs_data['name'].lower().replace(" ", "_")] = obstacle
                                
                                # Show placement with wall info
                                wall_info = obs_data.get('position_hint', 'placed')
                                print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} '{obs_data['name']}' → {wall_info} wall ({obs_x:.1f}, {obs_y:.1f})")
                            except Exception as obs_e:
                                print(f"{Color.WARNING}[ARCHITECT] Could not place {obs_data.get('name', 'unknown')}: {obs_e}{Color.RESET}")
                    else:
                        print(f"{Color.WARNING}[ARCHITECT] No layout generated - room may be empty{Color.RESET}")
                        
                except Exception as ie:
                    print(f"{Color.WARNING}[ARCHITECT] Interior design system error: {ie}{Color.RESET}")
            
            print(f"{Color.SUCCESS}[SPATIAL] ✓ Moved to '{label.title()}' ({width}x{height} {loc_type}){Color.RESET}")
            if reasoning:
                print(f"{Color.SYSTEM}[SPATIAL] Reasoning: {reasoning}{Color.RESET}")
            
            # Sync pygame map if running
            # The sync function will use cached layout if returning to a visited location,
            # or generate a new one if this is a new location
            try:
                from pygame_spatial_map import sync_from_spatial_context, get_pygame_map, _layout_cache
                map_inst = get_pygame_map()
                if map_inst and map_inst.running:
                    # Get the location name as it will appear in spatial context
                    location_title = label.title()
                    current_map_location = map_inst.state.location_name or ""
                    
                    # Debug: Show what's happening
                    print(f"{Color.SYSTEM}[PMAP] Location change: '{current_map_location}' → '{location_title}'{Color.RESET}")
                    print(f"{Color.SYSTEM}[PMAP] Cache contains: {list(_layout_cache.keys())}{Color.RESET}")
                    
                    # Force sync - the sync function will handle cache logic
                    sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                    print(f"{Color.SYSTEM}[PMAP] Map synced to location: {location_title}{Color.RESET}")
            except ImportError:
                pass
            except Exception as map_err:
                print(f"{Color.WARNING}[PMAP] Map sync error: {map_err}{Color.RESET}")
                import traceback
                traceback.print_exc()
        except Exception as e:
            print(f"{Color.WARNING}[SPATIAL] Could not update location: {e}{Color.RESET}")
        # Minimal debug confirmation only when the scene actually changes
        try:
            if (new_desc or "").strip() and (new_desc.strip() != (previous_scene_desc or "").strip()):
                print(f"{Color.SYSTEM}Location set → {label}{Color.RESET}")
        except Exception:
            pass
        # Record in narrative context as a minor transition (if manager provided)
        if narrative_context_manager is not None:
            try:
                # Local import to avoid early top-level dependency
                from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
                narrative_context_manager.add_narrative_event(
                    event_type=NarrativeEventType.SCENE_TRANSITION,
                    narrative_text=f"Shifted location to the {label} interior.",
                    actors_involved=[actor.sheet.name],
                    importance=NarrativeImportance.NOTABLE,
                    emotional_tone='transitional',
                    scene_context=f"from: {previous_scene_desc[:60]}..."
                )
            except Exception:
                pass
        return new_desc
    except Exception as e:
        # CRITICAL: Log the error - don't silently fail and return old scene
        print(f"{Color.ERROR}[LOCATION MOVE] Critical error generating new scene: {e}{Color.RESET}")
        import traceback
        traceback.print_exc()
        # Generate a minimal fallback scene for the new location instead of returning old scene
        fallback_desc = f"You arrive at the {label}. The space opens before you, its details slowly coming into focus."
        return fallback_desc


