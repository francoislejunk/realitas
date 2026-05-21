"""
THE ARCHITECT AGENT
═══════════════════════════════════════════════════════════════════════════════

I am the Architect. I see the bones beneath the skin of every space.

When the Narrator paints a scene with words, I translate that poetry into 
geometry. Where they see "a cramped diner with flickering neon," I see:
- 10 meters by 8 meters
- Counter along the back wall (6m × 0.8m)
- Four booths against the windows (1.5m × 1.2m each)
- Primary circulation path from entrance to counter
- Secondary paths between seating zones
- Focal point: the counter, drawing the eye and the hungry

My purpose is CONSISTENCY and VALIDITY. A diner described in Chapter 1 must 
have the same bones when revisited in Chapter 10. The terminal mentioned in 
passing must exist somewhere specific, reachable, real. And a car will NEVER
appear inside a living room - not on my watch.

═══════════════════════════════════════════════════════════════════════════════
MY CORE RULES - THE LAWS OF SPACE
═══════════════════════════════════════════════════════════════════════════════

1. FUNCTION-FIRST PLACEMENT
   Every object must serve a clear functional purpose based on location type.
   Before placing anything, I ask: "What is this object's primary function, 
   and does this placement support that function?"
   Cars belong in garages, driveways, parking lots - NEVER inside living spaces.

2. CONTEXTUAL COHERENCE  
   Design must respect the existing environment, style, and scale.
   A modern glass office doesn't get a Victorian porch. Period.

3. LOGICAL SPATIAL HIERARCHY
   - Public areas (lobbies, waiting rooms) near entrances
   - Related functions grouped (kitchen near dining, bathrooms near bedrooms)
   - Clear circulation paths connecting spaces logically
   - Noisy areas separated from quiet zones

4. PROPORTIONAL BALANCE
   Human-scale references are sacred:
   - Door height: ~2.1m
   - Car length: ~4-5m  
   - Desk: ~1.5m x 0.8m
   - Chair clearance: ~0.6m
   A conference table MUST fit with space for chairs AND movement.

5. MATERIAL & OBJECT INTEGRITY
   - Outdoor furniture: weather-resistant
   - Kitchen surfaces: easy to clean
   - Structural elements: appropriate materials (concrete foundations, glass windows)

6. MOVEMENT ORCHESTRATION
   Pathways naturally guide movement. No dead-ends in high-traffic areas.
   Exits always clearly accessible. Minimum path width: 0.9m.

7. SUSTAINABLE & PRACTICAL LAYOUT
   - Group plumbing fixtures to reduce pipe runs
   - Orient windows for natural light
   - Utilize roof spaces for gardens or utilities where appropriate

8. UNIFIED COMPOSITION
   Every element contributes to the whole. If it doesn't serve the location's
   purpose or aesthetic, it doesn't belong.

═══════════════════════════════════════════════════════════════════════════════
MY PROCESS - HOW I BUILD
═══════════════════════════════════════════════════════════════════════════════

For each location, I:

1. ANALYZE - Identify location type, primary functions, fixed elements
2. ZONE - Divide space into functional zones (work, circulation, services, outdoor)
3. PLACE - Sequential placement:
   a) Large structural/fixed elements first
   b) Furniture and equipment based on function
   c) Decorative items only if space and function allow
4. VALIDATE - Check against common errors:
   - No vehicles inside buildings (unless designated garage)
   - No furniture blocking doors or pathways
   - No mismatched scales
   - All utilities accessible
5. COHERENCE CHECK - Does the layout support intended activities?

The Creator dreams. I make those dreams obey the laws of physics and function.

═══════════════════════════════════════════════════════════════════════════════
"""

import json
import re
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum

from color_utils import Color


class SpaceType(Enum):
    """Types of spaces with default architectural properties."""
    # Residential
    BEDROOM = "bedroom"
    LIVING_ROOM = "living_room"
    KITCHEN = "kitchen"
    BATHROOM = "bathroom"
    DINING_ROOM = "dining_room"
    HALLWAY = "hallway"
    CLOSET = "closet"
    GARAGE = "garage"
    BASEMENT = "basement"
    ATTIC = "attic"
    
    # Commercial
    OFFICE = "office"
    LOBBY = "lobby"
    CONFERENCE_ROOM = "conference_room"
    BREAK_ROOM = "break_room"
    RECEPTION = "reception"
    STORAGE = "storage"
    RESTROOM = "restroom"
    
    # Industrial
    WAREHOUSE = "warehouse"
    FACTORY_FLOOR = "factory_floor"
    LOADING_DOCK = "loading_dock"
    CONTROL_ROOM = "control_room"
    
    # Public/Commercial
    RESTAURANT = "restaurant"
    DINER = "diner"
    BAR = "bar"
    SHOP = "shop"
    CLINIC = "clinic"
    WAITING_ROOM = "waiting_room"
    
    # Specialized
    LAB = "lab"
    SERVER_ROOM = "server_room"
    SECURITY_STATION = "security_station"
    INTERROGATION_ROOM = "interrogation_room"
    CELL = "cell"
    ARMORY = "armory"
    
    # Outdoor/Transitional
    COURTYARD = "courtyard"
    ALLEY = "alley"
    STREET = "street"
    PARKING_LOT = "parking_lot"
    ROOFTOP = "rooftop"
    
    # Generic
    ROOM = "room"
    CORRIDOR = "corridor"
    OPEN_SPACE = "open_space"


@dataclass
class ArchitecturalZone:
    """Defines a functional zone within a space."""
    zone_id: str
    zone_type: str  # e.g., "seating", "work", "storage", "circulation"
    purpose: str
    min_width: float  # meters
    min_height: float  # meters
    position_hint: str  # e.g., "center", "corner", "near_entrance", "near_window"
    furniture_suggestions: List[str] = field(default_factory=list)
    clearance_required: float = 0.9  # meters (default ~3 feet)


@dataclass
class CirculationPath:
    """Defines a movement pathway through a space."""
    path_id: str
    path_type: str  # "primary", "secondary", "service"
    start_point: str  # zone or entrance name
    end_point: str
    min_width: float = 0.9  # meters (~3 feet minimum)
    must_be_clear: bool = True


@dataclass
class ArchitecturalElement:
    """Defines a structural or functional element."""
    element_id: str
    element_type: str  # "door", "window", "column", "stairs", "counter", etc.
    position: Tuple[float, float]  # (x, y) in meters from origin
    dimensions: Tuple[float, float]  # (width, depth)
    rotation: float = 0.0  # degrees
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ArchitecturalLayout:
    """Complete architectural layout for a location."""
    location_name: str
    space_type: SpaceType
    dimensions: Tuple[float, float]  # (width, height) in meters
    zones: List[ArchitecturalZone] = field(default_factory=list)
    circulation_paths: List[CirculationPath] = field(default_factory=list)
    elements: List[ArchitecturalElement] = field(default_factory=list)
    entrances: List[Dict[str, Any]] = field(default_factory=list)
    focal_points: List[Dict[str, Any]] = field(default_factory=list)
    lighting_zones: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# Default space dimensions (width, height in meters)
DEFAULT_SPACE_DIMENSIONS = {
    SpaceType.BEDROOM: (4.0, 4.0),
    SpaceType.LIVING_ROOM: (6.0, 5.0),
    SpaceType.KITCHEN: (4.0, 3.5),
    SpaceType.BATHROOM: (2.5, 2.0),
    SpaceType.DINING_ROOM: (4.0, 4.0),
    SpaceType.HALLWAY: (8.0, 1.5),
    SpaceType.CLOSET: (1.5, 1.0),
    SpaceType.GARAGE: (6.0, 6.0),
    SpaceType.OFFICE: (4.0, 4.0),
    SpaceType.LOBBY: (8.0, 6.0),
    SpaceType.CONFERENCE_ROOM: (6.0, 5.0),
    SpaceType.BREAK_ROOM: (5.0, 4.0),
    SpaceType.RECEPTION: (5.0, 4.0),
    SpaceType.STORAGE: (3.0, 3.0),
    SpaceType.RESTROOM: (3.0, 2.5),
    SpaceType.WAREHOUSE: (20.0, 15.0),
    SpaceType.FACTORY_FLOOR: (25.0, 20.0),
    SpaceType.LOADING_DOCK: (10.0, 8.0),
    SpaceType.CONTROL_ROOM: (5.0, 4.0),
    SpaceType.RESTAURANT: (12.0, 10.0),
    SpaceType.DINER: (10.0, 8.0),
    SpaceType.BAR: (8.0, 6.0),
    SpaceType.SHOP: (8.0, 6.0),
    SpaceType.CLINIC: (10.0, 8.0),
    SpaceType.WAITING_ROOM: (5.0, 4.0),
    SpaceType.LAB: (8.0, 6.0),
    SpaceType.SERVER_ROOM: (6.0, 5.0),
    SpaceType.SECURITY_STATION: (4.0, 3.0),
    SpaceType.INTERROGATION_ROOM: (3.5, 3.0),
    SpaceType.CELL: (2.5, 2.0),
    SpaceType.ARMORY: (5.0, 4.0),
    SpaceType.COURTYARD: (15.0, 15.0),
    SpaceType.ALLEY: (15.0, 3.0),
    SpaceType.STREET: (30.0, 10.0),
    SpaceType.PARKING_LOT: (20.0, 15.0),
    SpaceType.ROOFTOP: (15.0, 12.0),
    SpaceType.ROOM: (5.0, 4.0),
    SpaceType.CORRIDOR: (10.0, 2.0),
    SpaceType.OPEN_SPACE: (10.0, 10.0),
}


# Typical furniture/elements for each space type
TYPICAL_ELEMENTS = {
    SpaceType.DINER: [
        {"type": "counter", "position_hint": "back_wall", "dimensions": (6.0, 0.8)},
        {"type": "booth", "position_hint": "side_wall", "count": 4, "dimensions": (1.5, 1.2)},
        {"type": "stool", "position_hint": "at_counter", "count": 6, "dimensions": (0.4, 0.4)},
        {"type": "table", "position_hint": "center", "count": 3, "dimensions": (1.0, 1.0)},
        {"type": "jukebox", "position_hint": "corner", "dimensions": (0.8, 0.5)},
        {"type": "cash_register", "position_hint": "counter_end", "dimensions": (0.5, 0.4)},
        {"type": "door", "position_hint": "front", "dimensions": (1.0, 0.1)},
        {"type": "window", "position_hint": "front_wall", "count": 2, "dimensions": (1.5, 0.1)},
    ],
    SpaceType.OFFICE: [
        {"type": "desk", "position_hint": "center_back", "dimensions": (1.5, 0.8)},
        {"type": "chair", "position_hint": "at_desk", "dimensions": (0.6, 0.6)},
        {"type": "filing_cabinet", "position_hint": "corner", "dimensions": (0.5, 0.6)},
        {"type": "bookshelf", "position_hint": "side_wall", "dimensions": (1.0, 0.3)},
        {"type": "door", "position_hint": "front", "dimensions": (0.9, 0.1)},
        {"type": "window", "position_hint": "back_wall", "dimensions": (1.2, 0.1)},
    ],
    SpaceType.LOBBY: [
        {"type": "reception_desk", "position_hint": "center_back", "dimensions": (2.5, 1.0)},
        {"type": "seating_area", "position_hint": "side", "dimensions": (3.0, 2.0)},
        {"type": "plant", "position_hint": "corners", "count": 2, "dimensions": (0.5, 0.5)},
        {"type": "door", "position_hint": "front", "dimensions": (1.5, 0.1)},
        {"type": "elevator", "position_hint": "back", "dimensions": (2.0, 2.0)},
    ],
    SpaceType.BAR: [
        {"type": "bar_counter", "position_hint": "back_wall", "dimensions": (5.0, 0.8)},
        {"type": "bar_stool", "position_hint": "at_counter", "count": 8, "dimensions": (0.4, 0.4)},
        {"type": "table", "position_hint": "scattered", "count": 5, "dimensions": (0.8, 0.8)},
        {"type": "pool_table", "position_hint": "side", "dimensions": (2.5, 1.4)},
        {"type": "jukebox", "position_hint": "corner", "dimensions": (0.8, 0.5)},
        {"type": "door", "position_hint": "front", "dimensions": (1.0, 0.1)},
    ],
    SpaceType.WAREHOUSE: [
        {"type": "shelving_unit", "position_hint": "rows", "count": 6, "dimensions": (8.0, 1.0)},
        {"type": "forklift", "position_hint": "aisle", "dimensions": (2.0, 1.2)},
        {"type": "loading_door", "position_hint": "back", "dimensions": (4.0, 0.2)},
        {"type": "office_partition", "position_hint": "corner", "dimensions": (4.0, 3.0)},
        {"type": "pallet", "position_hint": "scattered", "count": 10, "dimensions": (1.2, 1.0)},
    ],
    SpaceType.LAB: [
        {"type": "lab_bench", "position_hint": "center", "count": 2, "dimensions": (3.0, 1.0)},
        {"type": "fume_hood", "position_hint": "back_wall", "dimensions": (1.5, 0.8)},
        {"type": "storage_cabinet", "position_hint": "side_wall", "count": 2, "dimensions": (1.0, 0.5)},
        {"type": "computer_station", "position_hint": "corner", "dimensions": (1.2, 0.8)},
        {"type": "sink", "position_hint": "near_bench", "dimensions": (0.6, 0.5)},
        {"type": "door", "position_hint": "front", "dimensions": (0.9, 0.1)},
    ],
    SpaceType.SECURITY_STATION: [
        {"type": "monitor_bank", "position_hint": "back_wall", "dimensions": (2.5, 0.6)},
        {"type": "desk", "position_hint": "center", "dimensions": (1.5, 0.8)},
        {"type": "chair", "position_hint": "at_desk", "dimensions": (0.6, 0.6)},
        {"type": "weapon_locker", "position_hint": "side_wall", "dimensions": (1.0, 0.5)},
        {"type": "door", "position_hint": "front", "dimensions": (0.9, 0.1)},
    ],
}


# ═══════════════════════════════════════════════════════════════════════════════
# PLACEMENT VALIDATION RULES - What can go where
# ═══════════════════════════════════════════════════════════════════════════════

# Objects that can ONLY appear in specific zone types
VALID_PLACEMENT_ZONES = {
    # Vehicles - NEVER inside buildings unless garage/parking
    "car": ["garage", "parking_lot", "street", "driveway", "loading_dock"],
    "truck": ["garage", "parking_lot", "street", "loading_dock"],
    "motorcycle": ["garage", "parking_lot", "street", "driveway"],
    "forklift": ["warehouse", "loading_dock", "garage", "factory_floor"],
    "bicycle": ["garage", "street", "courtyard", "parking_lot", "storage"],
    
    # Large outdoor elements
    "tree": ["courtyard", "street", "parking_lot", "rooftop", "outdoor"],
    "fountain": ["courtyard", "lobby", "outdoor"],
    "bench_outdoor": ["courtyard", "street", "parking_lot", "rooftop", "outdoor"],
    
    # Kitchen-specific
    "stove": ["kitchen", "break_room", "restaurant_kitchen"],
    "oven": ["kitchen", "break_room", "restaurant_kitchen"],
    "refrigerator": ["kitchen", "break_room", "restaurant_kitchen", "bar"],
    "dishwasher": ["kitchen", "restaurant_kitchen"],
    
    # Bathroom-specific
    "toilet": ["bathroom", "restroom"],
    "shower": ["bathroom"],
    "bathtub": ["bathroom"],
    "urinal": ["restroom"],
    
    # Industrial
    "heavy_machinery": ["factory_floor", "warehouse", "loading_dock"],
    "conveyor": ["factory_floor", "warehouse", "loading_dock"],
    
    # Medical
    "hospital_bed": ["clinic", "hospital_room"],
    "examination_table": ["clinic", "hospital_room"],
    "surgical_equipment": ["operating_room"],
}

# Objects that should NEVER appear in certain space types
FORBIDDEN_PLACEMENTS = {
    SpaceType.BEDROOM: ["car", "truck", "forklift", "heavy_machinery", "urinal"],
    SpaceType.LIVING_ROOM: ["car", "truck", "forklift", "toilet", "urinal", "shower", "heavy_machinery"],
    SpaceType.OFFICE: ["car", "truck", "bed", "bathtub", "shower", "toilet", "heavy_machinery"],
    SpaceType.KITCHEN: ["car", "truck", "bed", "toilet", "shower"],
    SpaceType.BATHROOM: ["car", "truck", "bed", "desk", "stove", "refrigerator"],
    SpaceType.RESTAURANT: ["car", "truck", "bed", "toilet", "shower", "heavy_machinery"],
    SpaceType.DINER: ["car", "truck", "bed", "toilet", "shower", "heavy_machinery"],
    SpaceType.BAR: ["car", "truck", "bed", "toilet", "shower", "heavy_machinery"],
    SpaceType.LOBBY: ["car", "truck", "bed", "toilet", "shower", "stove", "heavy_machinery"],
    SpaceType.LAB: ["car", "truck", "bed", "bathtub"],
    SpaceType.CLINIC: ["car", "truck", "stove", "heavy_machinery"],
}

# Human-scale reference dimensions (in meters)
SCALE_REFERENCES = {
    "door_height": 2.1,
    "door_width": 0.9,
    "car_length": 4.5,
    "car_width": 1.8,
    "desk_width": 1.5,
    "desk_depth": 0.8,
    "chair_width": 0.6,
    "chair_depth": 0.6,
    "bed_single_width": 1.0,
    "bed_single_length": 2.0,
    "bed_double_width": 1.5,
    "bed_double_length": 2.0,
    "table_dining_width": 1.2,
    "table_dining_length": 2.0,
    "couch_width": 2.0,
    "couch_depth": 0.9,
    "toilet_width": 0.4,
    "toilet_depth": 0.7,
    "sink_width": 0.6,
    "sink_depth": 0.5,
    "refrigerator_width": 0.8,
    "refrigerator_depth": 0.7,
    "stove_width": 0.6,
    "stove_depth": 0.6,
    "booth_width": 1.5,
    "booth_depth": 1.2,
    "counter_depth": 0.8,
    "aisle_min_width": 0.9,
    "corridor_min_width": 1.2,
    "person_standing_radius": 0.5,
}

# Minimum clearances (in meters)
CLEARANCE_REQUIREMENTS = {
    "door_swing": 1.0,  # Space needed for door to open
    "chair_pullout": 0.8,  # Space behind chair to pull out
    "walkway_primary": 1.2,  # Main circulation paths
    "walkway_secondary": 0.9,  # Secondary paths
    "furniture_wall_gap": 0.1,  # Minimum gap between furniture and wall
    "between_desks": 1.5,  # Space between facing desks
    "around_bed": 0.6,  # Space to walk around bed
    "kitchen_work_triangle": 1.2,  # Min distance in kitchen work triangle
}

# Zone adjacency preferences (which zones should be near each other)
ZONE_ADJACENCY = {
    "kitchen": ["dining", "storage", "service"],
    "dining": ["kitchen", "living", "service"],
    "living": ["dining", "entrance", "hallway"],
    "bedroom": ["bathroom", "hallway", "closet"],
    "bathroom": ["bedroom", "hallway"],
    "entrance": ["living", "hallway", "reception"],
    "reception": ["entrance", "waiting", "hallway"],
    "waiting": ["reception", "hallway"],
    "office": ["hallway", "conference", "break_room"],
    "conference": ["office", "hallway"],
    "break_room": ["office", "hallway", "kitchen"],
    "storage": ["kitchen", "service", "loading"],
    "loading": ["storage", "parking", "warehouse"],
    "parking": ["entrance", "loading", "street"],
}


@dataclass
class PlacementValidation:
    """Result of validating an object placement."""
    is_valid: bool
    object_type: str
    proposed_zone: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


class ArchitectAgent:
    """
    I am the Architect.
    
    I transform the Narrator's prose into precise spatial reality.
    Every wall has a place. Every door opens somewhere real.
    
    My principles are immutable:
    - CONSISTENCY: The same space, the same bones, every time.
    - CIRCULATION: People must move. Paths must be clear.
    - FUNCTION: Form follows purpose. Always.
    - PROPORTION: Space breathes or suffocates by design.
    
    Feed me descriptions. I return blueprints.
    """
    
    # The Architect's voice for debug output
    VOICE_PREFIX = "🏛️ ARCHITECT"
    
    def __init__(self, llm_caller=None, rag_system=None):
        """
        The Architect awakens.
        
        Args:
            llm_caller: My connection to deeper reasoning, when geometry alone fails
            rag_system: The world's memory - past layouts, established elements, world style
        """
        self.llm_caller = llm_caller
        self.rag_system = rag_system
        self._layout_cache: Dict[str, ArchitecturalLayout] = {}
        self._verbose = False  # Set True to hear my thoughts
        self._rag_context_cache: Dict[str, Dict] = {}  # Cache RAG results per location
        self.time_context = None  # Current time context for lighting and atmosphere
    
    def set_time_context(self, time_context):
        """Set the current time context for layout generation."""
        self.time_context = time_context
    
    def _format_time_context(self, time_context=None) -> str:
        """Format time context for inclusion in prompts."""
        tc = time_context or self.time_context
        
        # Auto-fetch from MasterTimeCoordinator if not set
        if not tc:
            try:
                from master_time_coordinator import get_master_time_coordinator
                master_time = get_master_time_coordinator()
                if master_time:
                    tc = master_time.get_current_time_context()
            except Exception:
                pass
        
        if not tc:
            return ""
        
        time_str = tc.get('time_string', '') or tc.get('formatted_time', '')
        period = tc.get('time_of_day', '') or tc.get('period', '')
        lighting = tc.get('lighting_condition', '')
        
        parts = []
        if time_str:
            parts.append(f"Current Time: {time_str}")
        if period:
            parts.append(f"Time of Day: {period}")
        if lighting:
            parts.append(f"Lighting: {lighting}")
        
        if parts:
            return f"""
**TIME CONTEXT (Affects lighting and atmosphere):**
{chr(10).join(parts)}
"""
        return ""
    
    # ═══════════════════════════════════════════════════════════════════════════
    # RAG INTEGRATION - The World's Memory
    # ═══════════════════════════════════════════════════════════════════════════
    
    def _query_rag_for_location(self, location_name: str, scene_description: str = "") -> Dict[str, Any]:
        """
        I consult the world's memory before building.
        
        What has been established about this place?
        - Previous descriptions and layouts
        - Architectural style of the area
        - Adjacent locations and their relationships
        - Specific elements mentioned in narrative history
        
        Args:
            location_name: The location to query
            scene_description: Current scene for context
            
        Returns:
            RAG context with established facts about this location
        """
        if not self.rag_system:
            return {}
        
        # Check cache first
        if location_name in self._rag_context_cache:
            self._speak(f"Using cached RAG context for '{location_name}'")
            return self._rag_context_cache[location_name]
        
        self._speak(f"Querying world memory for '{location_name}'...")
        
        rag_context = {
            "established_elements": [],
            "architectural_style": None,
            "adjacent_locations": [],
            "previous_descriptions": [],
            "specific_features": [],
            "area_type": None,  # e.g., "BSU facility", "residential", "commercial"
        }
        
        try:
            # Query 1: Direct location information
            location_query = f"location layout description {location_name}"
            location_results = self.rag_system.query(location_query, top_k=3)
            
            if location_results:
                for result in location_results:
                    text = result.get('text', '') if isinstance(result, dict) else str(result)
                    rag_context["previous_descriptions"].append(text[:500])
                    
                    # Extract specific elements mentioned
                    self._extract_rag_elements(text, rag_context)
            
            # Query 2: Architectural style of the area
            style_query = f"architectural style building design {location_name}"
            style_results = self.rag_system.query(style_query, top_k=2)
            
            if style_results:
                for result in style_results:
                    text = result.get('text', '') if isinstance(result, dict) else str(result)
                    style = self._infer_architectural_style(text)
                    if style:
                        rag_context["architectural_style"] = style
                        break
            
            # Query 3: Adjacent locations
            adjacent_query = f"near adjacent connected to {location_name}"
            adjacent_results = self.rag_system.query(adjacent_query, top_k=3)
            
            if adjacent_results:
                for result in adjacent_results:
                    text = result.get('text', '') if isinstance(result, dict) else str(result)
                    adjacents = self._extract_adjacent_locations(text, location_name)
                    rag_context["adjacent_locations"].extend(adjacents)
            
            # Query 4: Area type (BSU, residential, etc.)
            area_query = f"district area zone {location_name}"
            area_results = self.rag_system.query(area_query, top_k=2)
            
            if area_results:
                for result in area_results:
                    text = result.get('text', '') if isinstance(result, dict) else str(result)
                    area_type = self._infer_area_type(text)
                    if area_type:
                        rag_context["area_type"] = area_type
                        break
            
            # Cache the results
            self._rag_context_cache[location_name] = rag_context
            
            self._speak(f"RAG found {len(rag_context['established_elements'])} established elements", "success")
            
        except Exception as e:
            self._speak(f"RAG query failed: {e}", "error")
        
        return rag_context
    
    def _extract_rag_elements(self, text: str, rag_context: Dict):
        """Extract specific architectural elements mentioned in RAG results."""
        text_lower = text.lower()
        
        # Look for specific furniture/elements
        element_patterns = [
            (r'terminal[s]?', 'terminal'),
            (r'counter[s]?', 'counter'),
            (r'booth[s]?', 'booth'),
            (r'desk[s]?', 'desk'),
            (r'door[s]?', 'door'),
            (r'window[s]?', 'window'),
            (r'stair[s]?|staircase', 'stairs'),
            (r'elevator[s]?', 'elevator'),
            (r'reception', 'reception_desk'),
            (r'security\s*(?:checkpoint|station|desk)', 'security_station'),
            (r'waiting\s*area', 'waiting_area'),
            (r'parking', 'parking'),
            (r'loading\s*dock', 'loading_dock'),
        ]
        
        for pattern, element_type in element_patterns:
            if re.search(pattern, text_lower):
                if element_type not in rag_context["established_elements"]:
                    rag_context["established_elements"].append(element_type)
        
        # Look for specific features
        feature_patterns = [
            (r'flickering\s*(?:lights?|neon)', 'flickering_lights'),
            (r'broken|damaged|cracked', 'damaged_state'),
            (r'pristine|clean|polished', 'well_maintained'),
            (r'crowded|busy|packed', 'high_traffic'),
            (r'empty|abandoned|deserted', 'low_traffic'),
        ]
        
        for pattern, feature in feature_patterns:
            if re.search(pattern, text_lower):
                if feature not in rag_context["specific_features"]:
                    rag_context["specific_features"].append(feature)
    
    def _infer_architectural_style(self, text: str) -> Optional[str]:
        """Infer architectural style from RAG text."""
        text_lower = text.lower()
        
        style_indicators = {
            "brutalist": ["concrete", "brutalist", "monolithic", "imposing", "stark"],
            "corporate": ["glass", "steel", "modern", "sleek", "corporate"],
            "industrial": ["warehouse", "factory", "industrial", "metal", "pipes"],
            "residential": ["apartment", "home", "house", "domestic", "cozy"],
            "retro": ["neon", "diner", "vintage", "retro", "chrome"],
            "institutional": ["government", "official", "bureaucratic", "sterile"],
            "underground": ["bunker", "basement", "underground", "subterranean"],
        }
        
        for style, indicators in style_indicators.items():
            if any(ind in text_lower for ind in indicators):
                return style
        
        return None
    
    def _extract_adjacent_locations(self, text: str, current_location: str) -> List[str]:
        """Extract names of adjacent locations from RAG text."""
        adjacents = []
        
        # Look for patterns like "near the X", "adjacent to X", "connected to X"
        patterns = [
            r'near\s+(?:the\s+)?([A-Z][a-zA-Z\s]+)',
            r'adjacent\s+to\s+(?:the\s+)?([A-Z][a-zA-Z\s]+)',
            r'connected\s+to\s+(?:the\s+)?([A-Z][a-zA-Z\s]+)',
            r'leads\s+to\s+(?:the\s+)?([A-Z][a-zA-Z\s]+)',
            r'across\s+from\s+(?:the\s+)?([A-Z][a-zA-Z\s]+)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                location = match.strip()
                if location.lower() != current_location.lower() and len(location) > 2:
                    adjacents.append(location)
        
        return list(set(adjacents))[:5]  # Limit to 5 unique adjacents
    
    def _infer_area_type(self, text: str) -> Optional[str]:
        """Infer the type of area (BSU, residential, etc.) from RAG text."""
        text_lower = text.lower()
        
        area_indicators = {
            "bsu_facility": ["bsu", "arbitration", "enforcement", "official", "government"],
            "commercial": ["shop", "store", "market", "mall", "business"],
            "residential": ["apartment", "home", "housing", "residential"],
            "industrial": ["factory", "warehouse", "industrial", "manufacturing"],
            "entertainment": ["bar", "club", "restaurant", "diner", "theater"],
            "medical": ["hospital", "clinic", "medical", "healthcare"],
            "transit": ["station", "terminal", "port", "hub"],
        }
        
        for area_type, indicators in area_indicators.items():
            if any(ind in text_lower for ind in indicators):
                return area_type
        
        return None
    
    def _apply_rag_context_to_analysis(self, analysis: Dict[str, Any], 
                                        rag_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge RAG context into the analysis.
        
        Established facts from RAG take precedence - consistency is law.
        """
        if not rag_context:
            return analysis
        
        # Add established elements that weren't detected
        for element in rag_context.get("established_elements", []):
            if element not in analysis["detected_elements"]:
                analysis["detected_elements"].append(element)
                self._speak(f"Added established element from RAG: '{element}'")
        
        # Apply architectural style
        if rag_context.get("architectural_style"):
            analysis["architectural_style"] = rag_context["architectural_style"]
        
        # Add adjacent locations
        if rag_context.get("adjacent_locations"):
            analysis["adjacent_locations"] = rag_context["adjacent_locations"]
        
        # Add area type
        if rag_context.get("area_type"):
            analysis["area_type"] = rag_context["area_type"]
        
        # Add specific features
        if rag_context.get("specific_features"):
            analysis["rag_features"] = rag_context["specific_features"]
        
        return analysis
    
    def _speak(self, message: str, level: str = "info"):
        """The Architect speaks, when permitted."""
        if not self._verbose:
            return
        
        prefix = f"{Color.CYAN}{self.VOICE_PREFIX}{Color.RESET}"
        if level == "warn":
            print(f"{prefix} {Color.WARNING}{message}{Color.RESET}")
        elif level == "error":
            print(f"{prefix} {Color.FAILURE}{message}{Color.RESET}")
        elif level == "success":
            print(f"{prefix} {Color.SUCCESS}{message}{Color.RESET}")
        else:
            print(f"{prefix} {message}")
    
    def set_verbose(self, verbose: bool):
        """Allow or silence the Architect's voice."""
        self._verbose = verbose
        
    def analyze_scene_description(self, scene_description: str, location_name: str = None) -> Dict[str, Any]:
        """
        I read the Narrator's words and see the space beneath.
        
        Every adjective is a clue. Every noun, a potential element.
        'Cramped' tells me dimensions. 'Flickering' tells me atmosphere.
        'Counter' tells me there's a service zone with stools.
        
        But first, I consult the world's memory. What has been established?
        Consistency is law. If a terminal was mentioned before, it exists now.
        
        Args:
            scene_description: The Narrator's prose
            location_name: A name, if known
            
        Returns:
            My analysis - the architectural DNA extracted from poetry, 
            enriched with established facts from RAG
        """
        self._speak(f"Reading the space... '{scene_description[:50]}...'")
        
        # First, extract location name if not provided
        resolved_location = location_name or self._extract_location_name(scene_description)
        
        # Consult the world's memory FIRST
        rag_context = self._query_rag_for_location(resolved_location, scene_description)
        
        # Now analyze the current description
        analysis = {
            "location_name": resolved_location,
            "space_type": self._infer_space_type(scene_description),
            "detected_elements": self._extract_elements(scene_description),
            "detected_zones": self._extract_zones(scene_description),
            "atmosphere": self._extract_atmosphere(scene_description),
            "scale_hints": self._extract_scale_hints(scene_description),
            "entrance_hints": self._extract_entrance_hints(scene_description),
        }
        
        # Merge RAG context - established facts take precedence
        analysis = self._apply_rag_context_to_analysis(analysis, rag_context)
        
        self._speak(f"Space type: {analysis['space_type'].value}", "success")
        self._speak(f"Found {len(analysis['detected_elements'])} elements, {len(analysis['detected_zones'])} zones")
        
        if rag_context.get("architectural_style"):
            self._speak(f"Architectural style from world memory: {rag_context['architectural_style']}")
        
        return analysis
    
    def generate_layout(self, 
                       scene_description: str, 
                       location_name: str = None,
                       override_dimensions: Tuple[float, float] = None,
                       npc_count: int = 0) -> ArchitecturalLayout:
        """
        This is my primary function. Give me words, I give you a building.
        
        I work in layers, like any good architect:
        1. ANALYSIS - Read the description, extract the DNA
        2. DIMENSIONS - How big is this space? Scale matters.
        3. ZONES - Carve the space into functional areas
        4. CIRCULATION - Draw the paths people will walk
        5. ELEMENTS - Place the furniture, the doors, the windows
        6. FOCAL POINTS - Where does the eye rest?
        7. LIGHTING - How does light define the mood?
        
        Args:
            scene_description: The Narrator's vision in prose
            location_name: What we call this place
            override_dimensions: Force specific dimensions (I prefer to calculate)
            npc_count: How many souls must this space hold?
            
        Returns:
            A complete ArchitecturalLayout - the blueprint made real
        """
        # Check cache first - consistency demands we return the same bones
        cache_key = location_name or self._extract_location_name(scene_description)
        if cache_key in self._layout_cache:
            self._speak(f"Retrieving cached layout for '{cache_key}'", "success")
            return self._layout_cache[cache_key]
        
        self._speak(f"Building layout for '{cache_key}'...")
        
        # LAYER 1: Analysis - read the space
        analysis = self.analyze_scene_description(scene_description, location_name)
        space_type = analysis["space_type"]
        
        # LAYER 2: Dimensions - size the space
        if override_dimensions:
            dimensions = override_dimensions
            self._speak(f"Using override dimensions: {dimensions[0]}m × {dimensions[1]}m")
        else:
            dimensions = self._calculate_dimensions(space_type, analysis, npc_count)
            self._speak(f"Calculated dimensions: {dimensions[0]}m × {dimensions[1]}m")
        
        # Create the layout shell
        layout = ArchitecturalLayout(
            location_name=analysis["location_name"],
            space_type=space_type,
            dimensions=dimensions,
        )
        
        # LAYER 3: Zones - carve functional areas
        layout.zones = self._generate_zones(space_type, dimensions, analysis)
        self._speak(f"Created {len(layout.zones)} functional zones")
        
        # LAYER 4: Circulation - draw the paths
        layout.circulation_paths = self._generate_circulation(space_type, dimensions, layout.zones)
        self._speak(f"Defined {len(layout.circulation_paths)} circulation paths")
        
        # LAYER 5: Elements - place the objects
        layout.elements = self._generate_elements(space_type, dimensions, analysis)
        self._speak(f"Placed {len(layout.elements)} architectural elements")
        
        # LAYER 6: Entrances - where do we enter?
        layout.entrances = self._generate_entrances(space_type, dimensions, analysis)
        
        # LAYER 7: Focal points - where does the eye rest?
        layout.focal_points = self._generate_focal_points(space_type, dimensions, analysis)
        
        # LAYER 8: Lighting - mood through illumination
        layout.lighting_zones = self._generate_lighting(space_type, dimensions, analysis)
        
        # Store metadata for future reference
        layout.metadata = {
            "source_description": scene_description[:500],
            "analysis": analysis,
            "npc_capacity": self._calculate_capacity(dimensions, space_type),
            "architect_version": "1.0",
        }
        
        # Cache for consistency - same place, same bones
        self._layout_cache[analysis["location_name"]] = layout
        self._speak(f"Layout complete and cached for '{analysis['location_name']}'", "success")
        
        return layout
    
    def layout_to_map_data(self, layout: ArchitecturalLayout) -> Dict[str, Any]:
        """
        Convert an ArchitecturalLayout to data format for pygame_spatial_map.
        
        Args:
            layout: The architectural layout to convert
            
        Returns:
            Dictionary compatible with pygame_spatial_map
        """
        # Convert meters to grid units (1 meter = 1 grid unit for simplicity)
        width, height = layout.dimensions
        
        map_data = {
            "location_name": layout.location_name,
            "width": int(width),
            "height": int(height),
            "zones": [],
            "obstacles": [],
            "entrances": [],
            "focal_points": [],
        }
        
        # Convert zones
        for zone in layout.zones:
            map_data["zones"].append({
                "zone_id": zone.zone_id,
                "zone_type": zone.zone_type,
                "purpose": zone.purpose,
                "position_hint": zone.position_hint,
                "min_width": zone.min_width,
                "min_height": zone.min_height,
            })
        
        # Convert elements to obstacles
        for element in layout.elements:
            obstacle = {
                "obstacle_id": element.element_id,
                "obstacle_name": element.element_type.replace("_", " ").title(),
                "obstacle_type": self._element_to_obstacle_type(element.element_type),
                "x": element.position[0],
                "y": element.position[1],
                "width": element.dimensions[0],
                "height": element.dimensions[1],
                "is_passable": element.properties.get("passable", False),
                "blocks_los": element.properties.get("blocks_los", True),
            }
            map_data["obstacles"].append(obstacle)
        
        # Convert entrances
        for entrance in layout.entrances:
            map_data["entrances"].append({
                "entrance_id": entrance.get("id", "entrance_main"),
                "position": entrance.get("position", (0, height // 2)),
                "direction": entrance.get("direction", "south"),
                "width": entrance.get("width", 1.0),
            })
        
        # Convert focal points
        for fp in layout.focal_points:
            map_data["focal_points"].append({
                "name": fp.get("name", "focal_point"),
                "position": fp.get("position", (width // 2, height // 2)),
                "importance": fp.get("importance", "primary"),
            })
        
        return map_data
    
    def get_spawn_positions(self, layout: ArchitecturalLayout, count: int) -> List[Tuple[float, float]]:
        """
        Get appropriate spawn positions for actors based on layout.
        
        Args:
            layout: The architectural layout
            count: Number of positions needed
            
        Returns:
            List of (x, y) positions
        """
        positions = []
        width, height = layout.dimensions
        
        # Prioritize positions in functional zones
        zone_positions = []
        for zone in layout.zones:
            if zone.zone_type in ["seating", "work", "social", "waiting"]:
                # Calculate zone center based on position hint
                pos = self._hint_to_position(zone.position_hint, width, height)
                zone_positions.append(pos)
        
        # Use zone positions first
        positions.extend(zone_positions[:count])
        
        # If we need more, generate positions avoiding obstacles
        if len(positions) < count:
            remaining = count - len(positions)
            
            # Get obstacle positions to avoid
            obstacle_positions = set()
            for element in layout.elements:
                ex, ey = element.position
                ew, eh = element.dimensions
                for ox in range(int(ex), int(ex + ew) + 1):
                    for oy in range(int(ey), int(ey + eh) + 1):
                        obstacle_positions.add((ox, oy))
            
            # Generate positions in a grid pattern, avoiding obstacles
            import random
            attempts = 0
            while len(positions) < count and attempts < 100:
                x = random.uniform(1, width - 1)
                y = random.uniform(1, height - 1)
                
                # Check if position is clear
                grid_pos = (int(x), int(y))
                if grid_pos not in obstacle_positions:
                    # Check minimum distance from other positions
                    too_close = False
                    for px, py in positions:
                        if abs(x - px) < 1.0 and abs(y - py) < 1.0:
                            too_close = True
                            break
                    
                    if not too_close:
                        positions.append((x, y))
                
                attempts += 1
        
        return positions[:count]
    
    def _extract_location_name(self, description: str) -> str:
        """Extract location name from description."""
        # Common patterns
        patterns = [
            r"(?:arrive at|enter|step into|walk into|in the|at the)\s+(?:the\s+)?([A-Z][a-zA-Z\s']+?)(?:\.|,|$)",
            r"(?:the|a|an)\s+([A-Z][a-zA-Z\s']+?)(?:\s+is|\s+stretches|\s+lies)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, description)
            if match:
                return match.group(1).strip()
        
        return "Unknown Location"
    
    def _infer_space_type(self, description: str) -> SpaceType:
        """Infer the type of space from description."""
        desc_lower = description.lower()
        
        # Check for specific keywords
        type_keywords = {
            SpaceType.DINER: ["diner", "dine", "booth", "counter service", "waitress", "jukebox"],
            SpaceType.RESTAURANT: ["restaurant", "dining", "tables", "waiter", "menu"],
            SpaceType.BAR: ["bar", "pub", "tavern", "drinks", "bartender", "pool table"],
            SpaceType.OFFICE: ["office", "desk", "cubicle", "workstation", "filing cabinet"],
            SpaceType.LOBBY: ["lobby", "reception", "waiting area", "front desk", "elevator"],
            SpaceType.WAREHOUSE: ["warehouse", "storage facility", "shelving", "forklift", "loading"],
            SpaceType.LAB: ["lab", "laboratory", "research", "equipment", "specimens", "fume hood"],
            SpaceType.BEDROOM: ["bedroom", "bed", "nightstand", "dresser", "closet"],
            SpaceType.LIVING_ROOM: ["living room", "couch", "sofa", "television", "fireplace"],
            SpaceType.KITCHEN: ["kitchen", "stove", "refrigerator", "sink", "counter"],
            SpaceType.BATHROOM: ["bathroom", "toilet", "shower", "sink", "mirror"],
            SpaceType.HALLWAY: ["hallway", "corridor", "passage", "hall"],
            SpaceType.SECURITY_STATION: ["security", "monitors", "surveillance", "guard station"],
            SpaceType.CONTROL_ROOM: ["control room", "console", "monitors", "operations"],
            SpaceType.CELL: ["cell", "prison", "jail", "detention"],
            SpaceType.INTERROGATION_ROOM: ["interrogation", "interview room"],
            SpaceType.CLINIC: ["clinic", "medical", "examination", "doctor"],
            SpaceType.SHOP: ["shop", "store", "merchandise", "shelves", "register"],
            SpaceType.ALLEY: ["alley", "alleyway", "narrow passage"],
            SpaceType.STREET: ["street", "road", "sidewalk", "traffic"],
            SpaceType.ROOFTOP: ["rooftop", "roof", "skyline"],
            SpaceType.PARKING_LOT: ["parking", "lot", "cars parked"],
            SpaceType.COURTYARD: ["courtyard", "open area", "central space"],
        }
        
        for space_type, keywords in type_keywords.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    return space_type
        
        return SpaceType.ROOM
    
    def _extract_elements(self, description: str) -> List[Dict[str, Any]]:
        """Extract mentioned elements/furniture from description."""
        elements = []
        desc_lower = description.lower()
        
        # Common element patterns
        element_patterns = {
            "desk": ["desk", "workstation"],
            "chair": ["chair", "seat", "stool"],
            "table": ["table"],
            "counter": ["counter", "bar"],
            "booth": ["booth"],
            "shelf": ["shelf", "shelving", "bookshelf"],
            "cabinet": ["cabinet", "locker", "filing"],
            "door": ["door", "entrance", "exit", "doorway"],
            "window": ["window"],
            "terminal": ["terminal", "computer", "monitor", "screen"],
            "bed": ["bed", "cot", "bunk"],
            "couch": ["couch", "sofa"],
            "refrigerator": ["refrigerator", "fridge"],
            "stove": ["stove", "oven", "range"],
            "sink": ["sink"],
            "plant": ["plant", "potted"],
            "lamp": ["lamp", "light"],
            "elevator": ["elevator", "lift"],
            "stairs": ["stairs", "staircase", "steps"],
        }
        
        for element_type, keywords in element_patterns.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    # Try to extract count
                    count_match = re.search(rf"(\d+|several|few|multiple|many)\s+{keyword}", desc_lower)
                    count = 1
                    if count_match:
                        count_word = count_match.group(1)
                        if count_word.isdigit():
                            count = int(count_word)
                        elif count_word in ["several", "few"]:
                            count = 3
                        elif count_word in ["multiple", "many"]:
                            count = 5
                    
                    elements.append({
                        "type": element_type,
                        "count": count,
                        "mentioned_as": keyword,
                    })
                    break  # Only add once per element type
        
        return elements
    
    def _extract_zones(self, description: str) -> List[Dict[str, Any]]:
        """Extract functional zones from description."""
        zones = []
        desc_lower = description.lower()
        
        zone_patterns = {
            "seating": ["seating area", "sitting area", "tables", "booths", "chairs"],
            "work": ["work area", "workspace", "desk area", "office space"],
            "service": ["service area", "counter", "bar", "kitchen"],
            "storage": ["storage", "back room", "closet", "warehouse"],
            "circulation": ["hallway", "corridor", "aisle", "pathway"],
            "waiting": ["waiting area", "lobby", "reception"],
            "private": ["private room", "office", "bedroom"],
        }
        
        for zone_type, keywords in zone_patterns.items():
            for keyword in keywords:
                if keyword in desc_lower:
                    zones.append({
                        "type": zone_type,
                        "keyword": keyword,
                    })
                    break
        
        return zones
    
    def _extract_atmosphere(self, description: str) -> Dict[str, Any]:
        """Extract atmospheric qualities from description."""
        desc_lower = description.lower()
        
        atmosphere = {
            "lighting": "normal",
            "crowding": "normal",
            "noise": "normal",
            "cleanliness": "normal",
        }
        
        # Lighting
        if any(word in desc_lower for word in ["dim", "dark", "shadowy", "gloomy"]):
            atmosphere["lighting"] = "dim"
        elif any(word in desc_lower for word in ["bright", "well-lit", "fluorescent", "glaring"]):
            atmosphere["lighting"] = "bright"
        elif any(word in desc_lower for word in ["neon", "flickering", "pulsing"]):
            atmosphere["lighting"] = "neon"
        
        # Crowding
        if any(word in desc_lower for word in ["crowded", "packed", "busy", "bustling"]):
            atmosphere["crowding"] = "crowded"
        elif any(word in desc_lower for word in ["empty", "deserted", "abandoned", "quiet"]):
            atmosphere["crowding"] = "empty"
        
        # Noise
        if any(word in desc_lower for word in ["loud", "noisy", "cacophony", "blaring"]):
            atmosphere["noise"] = "loud"
        elif any(word in desc_lower for word in ["quiet", "silent", "hushed", "still"]):
            atmosphere["noise"] = "quiet"
        
        # Cleanliness
        if any(word in desc_lower for word in ["dirty", "grimy", "filthy", "stained"]):
            atmosphere["cleanliness"] = "dirty"
        elif any(word in desc_lower for word in ["clean", "pristine", "spotless", "sterile"]):
            atmosphere["cleanliness"] = "clean"
        
        return atmosphere
    
    def _extract_scale_hints(self, description: str) -> Dict[str, Any]:
        """Extract hints about the scale/size of the space."""
        desc_lower = description.lower()
        
        scale = {
            "size_modifier": 1.0,
            "size_description": "normal",
        }
        
        if any(word in desc_lower for word in ["tiny", "cramped", "small", "narrow", "compact"]):
            scale["size_modifier"] = 0.6
            scale["size_description"] = "small"
        elif any(word in desc_lower for word in ["large", "spacious", "vast", "expansive", "huge"]):
            scale["size_modifier"] = 1.5
            scale["size_description"] = "large"
        elif any(word in desc_lower for word in ["massive", "enormous", "cavernous"]):
            scale["size_modifier"] = 2.0
            scale["size_description"] = "massive"
        
        return scale
    
    def _extract_entrance_hints(self, description: str) -> List[Dict[str, Any]]:
        """Extract hints about entrances/exits."""
        entrances = []
        desc_lower = description.lower()
        
        # Look for entrance mentions
        entrance_patterns = [
            (r"(?:main|front|primary)\s+(?:door|entrance|entry)", "front", "primary"),
            (r"(?:back|rear|service)\s+(?:door|entrance|exit)", "back", "secondary"),
            (r"(?:side)\s+(?:door|entrance)", "side", "secondary"),
            (r"(?:emergency|fire)\s+(?:exit|door)", "side", "emergency"),
        ]
        
        for pattern, position, entrance_type in entrance_patterns:
            if re.search(pattern, desc_lower):
                entrances.append({
                    "position": position,
                    "type": entrance_type,
                })
        
        # Default entrance if none found
        if not entrances:
            entrances.append({
                "position": "front",
                "type": "primary",
            })
        
        return entrances
    
    def _calculate_dimensions(self, space_type: SpaceType, analysis: Dict, npc_count: int) -> Tuple[float, float]:
        """Calculate appropriate dimensions for the space."""
        # Get base dimensions
        base_dims = DEFAULT_SPACE_DIMENSIONS.get(space_type, (5.0, 4.0))
        
        # Apply scale modifier
        scale = analysis.get("scale_hints", {}).get("size_modifier", 1.0)
        width = base_dims[0] * scale
        height = base_dims[1] * scale
        
        # Adjust for NPC count (need ~2 sq meters per person minimum)
        # Public venues need substantially more room for furniture + circulation.
        min_area = npc_count * 2.0
        if space_type in (SpaceType.BAR, SpaceType.RESTAURANT, SpaceType.DINER):
            # A "tavern"/"bar" with only a handful of named NPCs can still host many patrons.
            # Enforce a realistic minimum footprint for public venues.
            min_area = max(min_area, npc_count * 2.5)
            min_area = max(min_area, 80.0)  # ~10m x 8m baseline
        current_area = width * height
        if current_area < min_area:
            scale_up = (min_area / current_area) ** 0.5
            width *= scale_up
            height *= scale_up

        # Minimum side lengths (prevents skinny or too-small rooms after rounding)
        if space_type in (SpaceType.BAR, SpaceType.RESTAURANT, SpaceType.DINER):
            width = max(width, 10.0)
            height = max(height, 8.0)

        return (round(width, 1), round(height, 1))
    
    def _generate_zones(self, space_type: SpaceType, dimensions: Tuple[float, float], 
                       analysis: Dict) -> List[ArchitecturalZone]:
        """Generate functional zones for the space."""
        zones = []
        width, height = dimensions
        
        # Default zones based on space type
        if space_type == SpaceType.DINER:
            zones = [
                ArchitecturalZone("zone_counter", "service", "Counter seating", 
                                 width * 0.6, 1.5, "back_wall", ["stool", "counter"]),
                ArchitecturalZone("zone_booths", "seating", "Booth seating",
                                 width * 0.3, height * 0.6, "side_wall", ["booth"]),
                ArchitecturalZone("zone_tables", "seating", "Table seating",
                                 width * 0.4, height * 0.4, "center", ["table", "chair"]),
                ArchitecturalZone("zone_entrance", "circulation", "Entry area",
                                 2.0, 2.0, "front", []),
            ]
        elif space_type == SpaceType.OFFICE:
            zones = [
                ArchitecturalZone("zone_desk", "work", "Primary workspace",
                                 2.0, 1.5, "center_back", ["desk", "chair"]),
                ArchitecturalZone("zone_meeting", "social", "Meeting area",
                                 2.0, 2.0, "front", ["chair"]),
                ArchitecturalZone("zone_storage", "storage", "File storage",
                                 1.0, 1.0, "corner", ["cabinet"]),
            ]
        elif space_type == SpaceType.LOBBY:
            zones = [
                ArchitecturalZone("zone_reception", "service", "Reception desk",
                                 3.0, 1.5, "center_back", ["desk"]),
                ArchitecturalZone("zone_waiting", "waiting", "Waiting area",
                                 4.0, 3.0, "side", ["couch", "chair", "table"]),
                ArchitecturalZone("zone_circulation", "circulation", "Main walkway",
                                 2.0, height, "center", []),
            ]
        elif space_type == SpaceType.BAR:
            zones = [
                ArchitecturalZone("zone_bar", "service", "Bar counter",
                                 width * 0.6, 1.5, "back_wall", ["bar_counter", "stool"]),
                ArchitecturalZone("zone_tables", "seating", "Table area",
                                 width * 0.5, height * 0.5, "center", ["table", "chair"]),
                ArchitecturalZone("zone_games", "social", "Game area",
                                 3.0, 2.0, "side", ["pool_table"]),
            ]
        else:
            # Generic zones
            zones = [
                ArchitecturalZone("zone_main", "general", "Main area",
                                 width * 0.6, height * 0.6, "center", []),
                ArchitecturalZone("zone_entry", "circulation", "Entry",
                                 2.0, 2.0, "front", []),
            ]
        
        return zones
    
    def _generate_circulation(self, space_type: SpaceType, dimensions: Tuple[float, float],
                             zones: List[ArchitecturalZone]) -> List[CirculationPath]:
        """Generate circulation paths through the space."""
        paths = []
        width, height = dimensions
        
        # Primary path from entrance to main area
        paths.append(CirculationPath(
            "path_main", "primary", "entrance", "main_area",
            min_width=1.0, must_be_clear=True
        ))
        
        # Secondary paths between zones
        zone_names = [z.zone_id for z in zones]
        if len(zone_names) > 1:
            for i in range(len(zone_names) - 1):
                paths.append(CirculationPath(
                    f"path_{i}", "secondary", zone_names[i], zone_names[i + 1],
                    min_width=0.9, must_be_clear=True
                ))
        
        return paths
    
    def _generate_elements(self, space_type: SpaceType, dimensions: Tuple[float, float],
                          analysis: Dict) -> List[ArchitecturalElement]:
        """Generate architectural elements for the space."""
        elements = []
        width, height = dimensions
        
        # Get typical elements for this space type
        typical = TYPICAL_ELEMENTS.get(space_type, [])
        
        element_id = 0
        for template in typical:
            elem_type = template["type"]
            count = template.get("count", 1)
            dims = template.get("dimensions", (1.0, 1.0))
            hint = template.get("position_hint", "center")
            
            for i in range(count):
                # Calculate position based on hint
                pos = self._hint_to_position(hint, width, height, i, count)
                
                # Determine properties
                props = {
                    "passable": elem_type in ["door", "window", "entrance"],
                    "blocks_los": elem_type not in ["door", "window", "plant", "lamp"],
                }
                
                elements.append(ArchitecturalElement(
                    element_id=f"{elem_type}_{element_id}",
                    element_type=elem_type,
                    position=pos,
                    dimensions=dims,
                    properties=props
                ))
                element_id += 1
        
        # Add elements mentioned in description but not in typical
        detected = analysis.get("detected_elements", [])
        for det in detected:
            det_type = det["type"]
            # Check if already added
            if not any(e.element_type == det_type for e in elements):
                pos = self._hint_to_position("scattered", width, height, 0, 1)
                elements.append(ArchitecturalElement(
                    element_id=f"{det_type}_{element_id}",
                    element_type=det_type,
                    position=pos,
                    dimensions=(1.0, 1.0),
                    properties={"passable": False, "blocks_los": True}
                ))
                element_id += 1
        
        return elements
    
    def _generate_entrances(self, space_type: SpaceType, dimensions: Tuple[float, float],
                           analysis: Dict) -> List[Dict[str, Any]]:
        """Generate entrance positions."""
        entrances = []
        width, height = dimensions
        
        hints = analysis.get("entrance_hints", [{"position": "front", "type": "primary"}])
        
        for i, hint in enumerate(hints):
            pos_type = hint.get("position", "front")
            
            if pos_type == "front":
                position = (width / 2, 0.5)
                direction = "north"
            elif pos_type == "back":
                position = (width / 2, height - 0.5)
                direction = "south"
            elif pos_type == "side":
                position = (0.5, height / 2)
                direction = "west"
            else:
                position = (width / 2, 0.5)
                direction = "north"
            
            entrances.append({
                "id": f"entrance_{i}",
                "position": position,
                "direction": direction,
                "type": hint.get("type", "primary"),
                "width": 1.0,
            })
        
        return entrances
    
    def _generate_focal_points(self, space_type: SpaceType, dimensions: Tuple[float, float],
                              analysis: Dict) -> List[Dict[str, Any]]:
        """Generate focal points for the space."""
        focal_points = []
        width, height = dimensions
        
        # Primary focal point based on space type
        if space_type == SpaceType.DINER:
            focal_points.append({
                "name": "counter",
                "position": (width / 2, height - 1.5),
                "importance": "primary",
            })
        elif space_type == SpaceType.BAR:
            focal_points.append({
                "name": "bar",
                "position": (width / 2, height - 1.5),
                "importance": "primary",
            })
        elif space_type == SpaceType.LOBBY:
            focal_points.append({
                "name": "reception",
                "position": (width / 2, height - 2.0),
                "importance": "primary",
            })
        else:
            # Default center focal point
            focal_points.append({
                "name": "center",
                "position": (width / 2, height / 2),
                "importance": "primary",
            })
        
        return focal_points
    
    def _generate_lighting(self, space_type: SpaceType, dimensions: Tuple[float, float],
                          analysis: Dict) -> List[Dict[str, Any]]:
        """Generate lighting zones."""
        lighting_zones = []
        width, height = dimensions
        atmosphere = analysis.get("atmosphere", {})
        
        # Main lighting zone
        lighting_type = atmosphere.get("lighting", "normal")
        
        lighting_zones.append({
            "zone_id": "lighting_main",
            "type": lighting_type,
            "coverage": "full",
            "intensity": 0.8 if lighting_type == "bright" else 0.5 if lighting_type == "dim" else 0.7,
        })
        
        return lighting_zones
    
    def _hint_to_position(self, hint: str, width: float, height: float, 
                         index: int = 0, total: int = 1) -> Tuple[float, float]:
        """Convert a position hint to actual coordinates."""
        # Add some variation for multiple items
        offset = (index / max(total, 1)) * 0.3
        
        positions = {
            "center": (width / 2, height / 2),
            "center_back": (width / 2, height - 2),
            "back_wall": (width / 2 + offset * width, height - 1),
            "front": (width / 2, 1.5),
            "front_wall": (width / 2 + offset * width, 0.5),
            "side_wall": (1.5, height / 2 + offset * height),
            "side": (2, height / 2),
            "corner": (1.5 + offset * (width - 3), 1.5 + offset * (height - 3)),
            "corners": (1.5 if index % 2 == 0 else width - 1.5, 
                       1.5 if index < total / 2 else height - 1.5),
            "at_counter": (2 + index * 1.0, height - 2),
            "counter_end": (width - 2, height - 1),
            "scattered": (2 + (index % 3) * 2.5, 2 + (index // 3) * 2.5),
            "rows": (width / 2, 2 + index * 2.5),
            "aisle": (width / 2, height / 2),
            "back": (width / 2, height - 1),
            "near_entrance": (width / 2, 2),
            "near_window": (1, height / 2),
            "at_desk": (width / 2, height / 2 - 0.5),
            "near_bench": (width / 2 + 1.5, height / 2),
        }
        
        return positions.get(hint, (width / 2, height / 2))
    
    def _element_to_obstacle_type(self, element_type: str) -> str:
        """Convert element type to obstacle type for map system."""
        type_mapping = {
            "desk": "furniture",
            "chair": "furniture",
            "table": "furniture",
            "counter": "furniture",
            "booth": "furniture",
            "shelf": "furniture",
            "cabinet": "furniture",
            "bed": "furniture",
            "couch": "furniture",
            "door": "entrance",
            "window": "window",
            "terminal": "equipment",
            "computer": "equipment",
            "monitor": "equipment",
            "refrigerator": "appliance",
            "stove": "appliance",
            "sink": "fixture",
            "plant": "decoration",
            "lamp": "decoration",
            "elevator": "structure",
            "stairs": "structure",
            "column": "structure",
            "wall": "structure",
            "bar_counter": "furniture",
            "bar_stool": "furniture",
            "stool": "furniture",
            "pool_table": "furniture",
            "jukebox": "equipment",
            "cash_register": "equipment",
            "shelving_unit": "furniture",
            "forklift": "vehicle",
            "pallet": "container",
            "lab_bench": "furniture",
            "fume_hood": "equipment",
            "storage_cabinet": "furniture",
            "computer_station": "equipment",
            "monitor_bank": "equipment",
            "weapon_locker": "furniture",
            "reception_desk": "furniture",
            "seating_area": "furniture",
            "office_partition": "structure",
            "loading_door": "entrance",
        }
        
        return type_mapping.get(element_type, "obstacle")
    
    def _calculate_capacity(self, dimensions: Tuple[float, float], space_type: SpaceType) -> int:
        """Calculate comfortable capacity for the space."""
        width, height = dimensions
        area = width * height
        
        # Different space types have different density requirements
        density_factors = {
            SpaceType.DINER: 3.0,  # 3 sq meters per person
            SpaceType.RESTAURANT: 2.5,
            SpaceType.BAR: 2.0,
            SpaceType.OFFICE: 5.0,
            SpaceType.LOBBY: 3.0,
            SpaceType.WAREHOUSE: 10.0,
            SpaceType.LAB: 6.0,
        }
        
        factor = density_factors.get(space_type, 4.0)
        return max(1, int(area / factor))
    
    def interpret_with_llm(self, scene_description: str, location_name: str = None) -> Dict[str, Any]:
        """
        When geometry alone fails, I consult deeper reasoning.
        
        Some descriptions are too poetic, too abstract for rules.
        'A space that feels like forgotten promises' - what dimensions are those?
        Here, I ask the LLM to help me see what the Narrator truly meant.
        
        Args:
            scene_description: The challenging prose
            location_name: A name, if known
            
        Returns:
            Enhanced analysis with LLM interpretation
        """
        if not self.llm_caller:
            self._speak("No LLM connection - falling back to rules alone", "warn")
            return self.analyze_scene_description(scene_description, location_name)
        
        self._speak("Consulting deeper reasoning for complex interpretation...")
        
        prompt = f"""You are the Architect - you see the bones beneath the skin of every space.

Given this scene description, extract precise architectural data:

SCENE: {scene_description}
LOCATION NAME: {location_name or "Unknown"}

Analyze and return JSON with:
{{
    "space_type": "one of: diner, restaurant, bar, office, lobby, warehouse, lab, bedroom, living_room, kitchen, bathroom, hallway, security_station, control_room, cell, clinic, shop, alley, street, rooftop, parking_lot, courtyard, room, corridor, open_space",
    "dimensions_meters": {{"width": float, "height": float}},
    "atmosphere": {{
        "lighting": "dim/normal/bright/neon",
        "crowding": "empty/sparse/normal/crowded",
        "cleanliness": "dirty/normal/clean/sterile"
    }},
    "key_elements": [
        {{"type": "element_type", "position_hint": "where in room", "count": int}}
    ],
    "zones": [
        {{"type": "zone_type", "purpose": "what happens here", "position": "where"}}
    ],
    "entrances": [
        {{"position": "front/back/side", "type": "primary/secondary/emergency"}}
    ],
    "focal_point": {{"name": "what draws the eye", "position": "where"}},
    "architectural_notes": "any special considerations"
}}

Be precise. Be consistent. The map depends on your accuracy."""

        try:
            response = self.llm_caller(prompt)
            if response:
                # Parse JSON from response
                import json
                # Try to extract JSON from response
                json_match = re.search(r'\{[\s\S]*\}', response)
                if json_match:
                    llm_data = json.loads(json_match.group())
                    self._speak("LLM interpretation received", "success")
                    
                    # Merge with rule-based analysis
                    rule_analysis = self.analyze_scene_description(scene_description, location_name)
                    
                    # LLM data takes precedence where available
                    if "space_type" in llm_data:
                        try:
                            rule_analysis["space_type"] = SpaceType(llm_data["space_type"])
                        except ValueError:
                            pass
                    
                    if "dimensions_meters" in llm_data:
                        rule_analysis["llm_dimensions"] = (
                            llm_data["dimensions_meters"].get("width", 10),
                            llm_data["dimensions_meters"].get("height", 8)
                        )
                    
                    if "key_elements" in llm_data:
                        rule_analysis["llm_elements"] = llm_data["key_elements"]
                    
                    if "zones" in llm_data:
                        rule_analysis["llm_zones"] = llm_data["zones"]
                    
                    if "architectural_notes" in llm_data:
                        rule_analysis["notes"] = llm_data["architectural_notes"]
                    
                    return rule_analysis
                    
        except Exception as e:
            self._speak(f"LLM interpretation failed: {e}", "error")
        
        # Fallback to rules
        return self.analyze_scene_description(scene_description, location_name)
    
    def clear_cache(self, location_name: str = None):
        """
        Sometimes a space must be rebuilt. Demolition before construction.
        
        Args:
            location_name: Specific location to clear, or None for all
        """
        if location_name:
            if location_name in self._layout_cache:
                del self._layout_cache[location_name]
                self._speak(f"Cleared cache for '{location_name}'")
        else:
            self._layout_cache.clear()
            self._speak("All cached layouts cleared")
    
    def get_cached_locations(self) -> List[str]:
        """Return list of all cached location names."""
        return list(self._layout_cache.keys())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # VALIDATION METHODS - The Laws Must Be Enforced
    # ═══════════════════════════════════════════════════════════════════════════
    
    def validate_placement(self, object_type: str, space_type: SpaceType, 
                          zone_type: str = None) -> PlacementValidation:
        """
        Can this object exist in this space? I enforce the laws.
        
        A car in a living room? REJECTED.
        A toilet in an office? REJECTED.
        A desk in an office? APPROVED.
        
        Args:
            object_type: What we're trying to place
            space_type: The type of space we're placing it in
            zone_type: Optional specific zone within the space
            
        Returns:
            PlacementValidation with verdict and reasoning
        """
        result = PlacementValidation(
            is_valid=True,
            object_type=object_type,
            proposed_zone=zone_type or space_type.value
        )
        
        obj_lower = object_type.lower()
        
        # Check FORBIDDEN placements first - these are absolute
        if space_type in FORBIDDEN_PLACEMENTS:
            forbidden = FORBIDDEN_PLACEMENTS[space_type]
            for forbidden_item in forbidden:
                if forbidden_item in obj_lower or obj_lower in forbidden_item:
                    result.is_valid = False
                    result.errors.append(
                        f"'{object_type}' is FORBIDDEN in {space_type.value}. "
                        f"This violates Rule 1: Function-First Placement."
                    )
                    # Suggest valid locations
                    if obj_lower in VALID_PLACEMENT_ZONES:
                        valid_zones = VALID_PLACEMENT_ZONES[obj_lower]
                        result.suggestions.append(
                            f"'{object_type}' belongs in: {', '.join(valid_zones)}"
                        )
                    return result
        
        # Check if object has REQUIRED zones
        if obj_lower in VALID_PLACEMENT_ZONES:
            valid_zones = VALID_PLACEMENT_ZONES[obj_lower]
            space_name = space_type.value.lower()
            zone_name = (zone_type or "").lower()
            
            # Check if current space/zone is in valid list
            is_valid_zone = any(
                vz in space_name or vz in zone_name or space_name in vz
                for vz in valid_zones
            )
            
            if not is_valid_zone:
                result.is_valid = False
                result.errors.append(
                    f"'{object_type}' can only be placed in: {', '.join(valid_zones)}. "
                    f"Current space '{space_type.value}' is not valid."
                )
                return result
        
        # Passed all checks
        self._speak(f"Placement approved: '{object_type}' in {space_type.value}", "success")
        return result
    
    def validate_layout(self, layout: 'ArchitecturalLayout') -> List[PlacementValidation]:
        """
        Validate an entire layout against all architectural rules.
        
        I check every element, every placement, every clearance.
        Nothing escapes my scrutiny.
        
        Args:
            layout: The layout to validate
            
        Returns:
            List of validation results (only invalid ones if all pass)
        """
        validations = []
        
        self._speak(f"Validating layout for '{layout.location_name}'...")
        
        # Validate each element
        for element in layout.elements:
            validation = self.validate_placement(
                element.element_type,
                layout.space_type
            )
            if not validation.is_valid:
                validations.append(validation)
        
        # Check clearances
        clearance_issues = self._check_clearances(layout)
        validations.extend(clearance_issues)
        
        # Check circulation paths
        circulation_issues = self._check_circulation(layout)
        validations.extend(circulation_issues)
        
        if not validations:
            self._speak("Layout validation PASSED - all rules satisfied", "success")
        else:
            self._speak(f"Layout validation found {len(validations)} issue(s)", "warn")
        
        return validations
    
    def _check_clearances(self, layout: 'ArchitecturalLayout') -> List[PlacementValidation]:
        """Check that all clearance requirements are met."""
        issues = []
        
        # Check door clearances
        for element in layout.elements:
            if element.element_type == "door":
                # Check if there's enough space for door swing
                door_x, door_y = element.position
                door_clearance = CLEARANCE_REQUIREMENTS["door_swing"]
                
                # Check for blocking elements
                for other in layout.elements:
                    if other.element_id == element.element_id:
                        continue
                    ox, oy = other.position
                    ow, oh = other.dimensions
                    
                    # Simple overlap check for door swing area
                    if (abs(door_x - ox) < door_clearance and 
                        abs(door_y - oy) < door_clearance):
                        issue = PlacementValidation(
                            is_valid=False,
                            object_type=other.element_type,
                            proposed_zone="door_clearance",
                            errors=[f"'{other.element_type}' blocks door swing clearance"]
                        )
                        issues.append(issue)
        
        return issues
    
    def _check_circulation(self, layout: 'ArchitecturalLayout') -> List[PlacementValidation]:
        """Check that circulation paths are clear and wide enough."""
        issues = []
        
        for path in layout.circulation_paths:
            if path.min_width < CLEARANCE_REQUIREMENTS["walkway_secondary"]:
                issue = PlacementValidation(
                    is_valid=False,
                    object_type="circulation_path",
                    proposed_zone=path.path_id,
                    errors=[
                        f"Path '{path.path_id}' is too narrow ({path.min_width}m). "
                        f"Minimum required: {CLEARANCE_REQUIREMENTS['walkway_secondary']}m"
                    ]
                )
                issues.append(issue)
        
        return issues
    
    def suggest_valid_placement(self, object_type: str, 
                               space_type: SpaceType) -> Dict[str, Any]:
        """
        If a placement is invalid, I suggest where it SHOULD go.
        
        Args:
            object_type: The object we're trying to place
            space_type: The current (invalid) space
            
        Returns:
            Dictionary with suggestions
        """
        obj_lower = object_type.lower()
        
        suggestions = {
            "object": object_type,
            "current_space": space_type.value,
            "valid_spaces": [],
            "reasoning": ""
        }
        
        # Check if object has specific valid zones
        if obj_lower in VALID_PLACEMENT_ZONES:
            suggestions["valid_spaces"] = VALID_PLACEMENT_ZONES[obj_lower]
            suggestions["reasoning"] = (
                f"'{object_type}' is a specialized object that belongs in "
                f"specific functional areas."
            )
        else:
            # Generic object - suggest based on space type
            suggestions["valid_spaces"] = ["most indoor spaces"]
            suggestions["reasoning"] = (
                f"'{object_type}' is a general object. Ensure it serves "
                f"a functional purpose in its placement."
            )
        
        return suggestions
    
    def get_scale_reference(self, object_type: str) -> Tuple[float, float]:
        """
        Get the standard dimensions for an object type.
        
        Human scale is sacred. A door is 2.1m tall. A car is 4.5m long.
        These are the immutable truths of space.
        
        Args:
            object_type: The object to get dimensions for
            
        Returns:
            (width, depth) in meters
        """
        obj_lower = object_type.lower()
        
        # Direct matches
        dimension_map = {
            "door": (SCALE_REFERENCES["door_width"], 0.1),
            "car": (SCALE_REFERENCES["car_width"], SCALE_REFERENCES["car_length"]),
            "desk": (SCALE_REFERENCES["desk_width"], SCALE_REFERENCES["desk_depth"]),
            "chair": (SCALE_REFERENCES["chair_width"], SCALE_REFERENCES["chair_depth"]),
            "bed": (SCALE_REFERENCES["bed_single_width"], SCALE_REFERENCES["bed_single_length"]),
            "bed_double": (SCALE_REFERENCES["bed_double_width"], SCALE_REFERENCES["bed_double_length"]),
            "table": (SCALE_REFERENCES["table_dining_width"], SCALE_REFERENCES["table_dining_length"]),
            "couch": (SCALE_REFERENCES["couch_width"], SCALE_REFERENCES["couch_depth"]),
            "sofa": (SCALE_REFERENCES["couch_width"], SCALE_REFERENCES["couch_depth"]),
            "toilet": (SCALE_REFERENCES["toilet_width"], SCALE_REFERENCES["toilet_depth"]),
            "sink": (SCALE_REFERENCES["sink_width"], SCALE_REFERENCES["sink_depth"]),
            "refrigerator": (SCALE_REFERENCES["refrigerator_width"], SCALE_REFERENCES["refrigerator_depth"]),
            "fridge": (SCALE_REFERENCES["refrigerator_width"], SCALE_REFERENCES["refrigerator_depth"]),
            "stove": (SCALE_REFERENCES["stove_width"], SCALE_REFERENCES["stove_depth"]),
            "booth": (SCALE_REFERENCES["booth_width"], SCALE_REFERENCES["booth_depth"]),
            "counter": (2.0, SCALE_REFERENCES["counter_depth"]),
        }
        
        for key, dims in dimension_map.items():
            if key in obj_lower:
                return dims
        
        # Default for unknown objects
        return (1.0, 1.0)


# Singleton instance
_architect_agent: Optional[ArchitectAgent] = None


def get_architect_agent(llm_caller=None, rag_system=None) -> ArchitectAgent:
    """Get or create the singleton ArchitectAgent instance."""
    global _architect_agent
    if _architect_agent is None:
        _architect_agent = ArchitectAgent(llm_caller, rag_system)
    return _architect_agent


def generate_map_layout_from_scene(scene_description: str, 
                                   location_name: str = None,
                                   npc_count: int = 0) -> Dict[str, Any]:
    """
    Convenience function to generate map-ready layout data from a scene description.
    
    Args:
        scene_description: Narrative description of the scene
        location_name: Optional explicit location name
        npc_count: Number of NPCs to accommodate
        
    Returns:
        Dictionary compatible with pygame_spatial_map
    """
    agent = get_architect_agent()
    layout = agent.generate_layout(scene_description, location_name, npc_count=npc_count)
    return agent.layout_to_map_data(layout)


# ═══════════════════════════════════════════════════════════════════════════════
# ARCHITECT-FIRST INTEGRATION - Spatial Constraints Before Population
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SpatialConstraints:
    """
    The Architect's blueprint - spatial rules the Creator must follow.
    
    This is generated BEFORE the Creator populates the scene, ensuring
    that NPCs and objects are placed in valid, logical positions.
    """
    location_name: str
    space_type: SpaceType
    dimensions: Tuple[float, float]  # (width, height) in meters
    
    # Valid zones where NPCs can be placed
    valid_npc_zones: List[Dict[str, Any]] = field(default_factory=list)
    
    # Maximum capacity for this space
    max_capacity: int = 10
    
    # Objects that MUST exist (from RAG/established facts)
    required_elements: List[str] = field(default_factory=list)
    
    # Objects that CANNOT exist here
    forbidden_objects: List[str] = field(default_factory=list)
    
    # Architectural style to maintain
    architectural_style: Optional[str] = None
    
    # Adjacent locations (for exit placement)
    adjacent_locations: List[str] = field(default_factory=list)
    
    # Spawn positions for NPCs (pre-calculated valid positions)
    spawn_positions: List[Tuple[float, float]] = field(default_factory=list)
    
    # Entrance position (where player enters)
    entrance_position: Tuple[float, float] = (0.5, 0.9)  # Default: bottom center
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


def _compute_zone_bounds(zone: ArchitecturalZone, space_width: float, space_height: float) -> Tuple[float, float, float, float]:
    """
    Compute (x, y, width, height) bounds for a zone based on its position_hint and min dimensions.
    
    Returns normalized bounds (0-1 range) within the space.
    """
    # Use zone's min dimensions, capped to space size
    zone_w = min(zone.min_width / space_width, 0.4)  # Max 40% of space width
    zone_h = min(zone.min_height / space_height, 0.4)  # Max 40% of space height
    
    # Position based on hint
    hint = zone.position_hint.lower() if zone.position_hint else "center"
    
    if "center" in hint:
        x = 0.5 - zone_w / 2
        y = 0.5 - zone_h / 2
    elif "corner" in hint:
        # Pick a corner based on zone_id hash for consistency
        corner_idx = hash(zone.zone_id) % 4
        if corner_idx == 0:  # top-left
            x, y = 0.05, 0.05
        elif corner_idx == 1:  # top-right
            x, y = 0.95 - zone_w, 0.05
        elif corner_idx == 2:  # bottom-left
            x, y = 0.05, 0.95 - zone_h
        else:  # bottom-right
            x, y = 0.95 - zone_w, 0.95 - zone_h
    elif "entrance" in hint or "door" in hint:
        x = 0.5 - zone_w / 2
        y = 0.85 - zone_h  # Near bottom (entrance)
    elif "window" in hint or "wall" in hint:
        x = 0.5 - zone_w / 2
        y = 0.1  # Near top (window/back wall)
    elif "left" in hint:
        x = 0.05
        y = 0.5 - zone_h / 2
    elif "right" in hint:
        x = 0.95 - zone_w
        y = 0.5 - zone_h / 2
    else:
        # Default to center
        x = 0.5 - zone_w / 2
        y = 0.5 - zone_h / 2
    
    return (x, y, zone_w, zone_h)


def _generate_spawn_positions(space_type: SpaceType, 
                               dimensions: Tuple[float, float], 
                               npc_count: int) -> List[Tuple[float, float]]:
    """
    Generate valid spawn positions for NPCs based on space type and dimensions.
    
    Returns list of (x, y) NORMALIZED positions (0.0-1.0 range).
    Caller should multiply by actual map dimensions to get absolute coordinates.
    """
    import random
    
    positions = []
    
    # Dynamically categorize space type using the enum value string
    # This avoids hardcoding every possible SpaceType
    space_value = space_type.value.lower() if hasattr(space_type, 'value') else str(space_type).lower()
    
    # Commercial/public keywords - places where customers gather
    commercial_keywords = ['diner', 'restaurant', 'bar', 'pub', 'cafe', 'shop', 'store', 
                          'lobby', 'reception', 'waiting', 'clinic', 'hospital', 'bank',
                          'theater', 'cinema', 'gym', 'salon', 'market', 'mall']
    # Residential keywords - living spaces
    residential_keywords = ['bedroom', 'living', 'kitchen', 'bathroom', 'dining', 
                           'apartment', 'house', 'home', 'closet', 'attic', 'basement']
    # Industrial keywords - work/manufacturing spaces
    industrial_keywords = ['warehouse', 'factory', 'loading', 'dock', 'control', 
                          'plant', 'facility', 'hangar', 'garage', 'workshop']
    # Office keywords - professional workspaces
    office_keywords = ['office', 'conference', 'meeting', 'cubicle', 'break_room']
    # Outdoor keywords
    outdoor_keywords = ['street', 'alley', 'courtyard', 'parking', 'rooftop', 'plaza', 'park']
    
    # Determine category by keyword matching
    def matches_category(keywords):
        return any(kw in space_value for kw in keywords)
    
    if matches_category(commercial_keywords):
        # Commercial: NPCs near counters, booths, tables
        spawn_zones = [
            (0.2, 0.3, 0.6, 0.5),   # Main floor area
            (0.1, 0.2, 0.3, 0.3),   # Left side (booths/seating)
            (0.6, 0.4, 0.3, 0.3),   # Right side (counter area)
        ]
    elif matches_category(residential_keywords):
        # Residential: NPCs in living areas
        spawn_zones = [
            (0.3, 0.3, 0.4, 0.4),   # Center (main room)
            (0.6, 0.2, 0.3, 0.3),   # Secondary area
        ]
    elif matches_category(industrial_keywords):
        # Industrial: NPCs near workstations, spread out
        spawn_zones = [
            (0.2, 0.2, 0.6, 0.6),   # Main floor
        ]
    elif matches_category(office_keywords):
        # Office: NPCs at desks, meeting areas
        spawn_zones = [
            (0.2, 0.3, 0.3, 0.4),   # Desk area left
            (0.5, 0.3, 0.3, 0.4),   # Desk area right
            (0.3, 0.6, 0.4, 0.3),   # Meeting/common area
        ]
    elif matches_category(outdoor_keywords):
        # Outdoor: NPCs spread across open space
        spawn_zones = [
            (0.1, 0.1, 0.8, 0.8),   # Wide spread
        ]
    else:
        # Default: spread across center
        spawn_zones = [
            (0.2, 0.2, 0.6, 0.6),   # Center area
        ]
    
    # Generate positions dynamically spread across the map
    # Use grid-based distribution to ensure NPCs are spread out
    
    # Calculate grid layout based on NPC count
    if npc_count <= 1:
        cols, rows = 1, 1
    elif npc_count <= 2:
        cols, rows = 2, 1
    elif npc_count <= 4:
        cols, rows = 2, 2
    elif npc_count <= 6:
        cols, rows = 3, 2
    elif npc_count <= 9:
        cols, rows = 3, 3
    else:
        cols, rows = 4, 3  # Max 12 positions
    
    # Define usable area (avoid edges and entrance at bottom)
    margin_x = 0.10  # 10% margin on sides
    margin_y_top = 0.15  # 15% margin at top
    margin_y_bottom = 0.25  # 25% margin at bottom (entrance area)
    
    usable_width = 1.0 - (2 * margin_x)
    usable_height = 1.0 - margin_y_top - margin_y_bottom
    
    # Calculate cell size
    cell_width = usable_width / cols
    cell_height = usable_height / rows
    
    # Generate positions with jitter for natural feel
    for i in range(npc_count):
        col = i % cols
        row = i // cols
        if row >= rows:
            row = row % rows  # Wrap around if more NPCs than grid cells
        
        # Base position (center of cell)
        base_x = margin_x + (col + 0.5) * cell_width
        base_y = margin_y_top + (row + 0.5) * cell_height
        
        # Add random jitter within cell (±30% of cell size)
        jitter_x = random.uniform(-0.3, 0.3) * cell_width
        jitter_y = random.uniform(-0.3, 0.3) * cell_height
        
        x = base_x + jitter_x
        y = base_y + jitter_y
        
        # Ensure within bounds
        x = max(0.08, min(0.92, x))
        y = max(0.12, min(0.85, y))
        
        positions.append((x, y))
    
    return positions


def generate_spatial_constraints(location_name: str, 
                                  location_hint: str = "",
                                  expected_npc_count: int = 0,
                                  rag_system=None,
                                  override_dimensions: Optional[Tuple[float, float]] = None,
                                  max_capacity_override: Optional[int] = None) -> SpatialConstraints:
    """
    ARCHITECT-FIRST: Generate spatial constraints BEFORE the Creator populates.
    
    This is the key integration point. Call this BEFORE generating NPCs or
    scene descriptions. The constraints returned tell the Creator:
    - What type of space this is
    - How many NPCs can fit
    - Where NPCs can be placed
    - What objects must/cannot exist
    
    Args:
        location_name: Name of the location (e.g., "Rosie's Diner")
        location_hint: Optional hint about location type (e.g., "diner", "office")
        expected_npc_count: How many NPCs we expect to place
        rag_system: Optional RAG system for world memory
        
    Returns:
        SpatialConstraints that the Creator must respect
    """
    agent = get_architect_agent(rag_system=rag_system)
    
    # Build a minimal scene description from what we know
    scene_hint = f"{location_name}. {location_hint}" if location_hint else location_name
    
    # Analyze the space
    analysis = agent.analyze_scene_description(scene_hint, location_name)
    
    # Calculate dimensions
    space_type = analysis["space_type"]
    if override_dimensions is not None:
        try:
            ow = float(override_dimensions[0])
            oh = float(override_dimensions[1])
            if ow > 0 and oh > 0:
                dimensions = (ow, oh)
            else:
                dimensions = agent._calculate_dimensions(space_type, analysis, expected_npc_count)
        except Exception:
            dimensions = agent._calculate_dimensions(space_type, analysis, expected_npc_count)
    else:
        dimensions = agent._calculate_dimensions(space_type, analysis, expected_npc_count)
    
    # Get forbidden objects for this space type
    forbidden = FORBIDDEN_PLACEMENTS.get(space_type, [])
    
    # Calculate max capacity
    max_cap = agent._calculate_capacity(dimensions, space_type)
    if max_capacity_override is not None:
        try:
            max_cap = max(1, min(int(max_cap), int(max_capacity_override)))
        except Exception:
            pass
    
    # Generate valid NPC zones
    zones = agent._generate_zones(space_type, dimensions, analysis)
    valid_npc_zones = []
    width, height = dimensions
    for zone in zones:
        if zone.zone_type not in ["storage", "kitchen", "service", "restricted"]:
            # Compute bounds from position_hint and min dimensions
            # ArchitecturalZone doesn't have bounds, so we calculate them
            zone_bounds = _compute_zone_bounds(zone, width, height)
            valid_npc_zones.append({
                "zone_id": zone.zone_id,
                "zone_type": zone.zone_type,
                "bounds": zone_bounds,
                "purpose": zone.purpose,
            })
    
    # Pre-calculate spawn positions using standalone function
    try:
        expected_npc_count = int(expected_npc_count or 0)
    except Exception:
        expected_npc_count = 0
    expected_npc_count = max(0, min(expected_npc_count, int(max_cap)))

    spawn_positions = _generate_spawn_positions(
        space_type, dimensions, min(expected_npc_count, max_cap)
    )
    
    # Build constraints
    constraints = SpatialConstraints(
        location_name=location_name,
        space_type=space_type,
        dimensions=dimensions,
        valid_npc_zones=valid_npc_zones,
        max_capacity=max_cap,
        required_elements=analysis.get("detected_elements", []),
        forbidden_objects=list(forbidden),
        architectural_style=analysis.get("architectural_style"),
        adjacent_locations=analysis.get("adjacent_locations", []),
        spawn_positions=spawn_positions,
        metadata={
            "analysis": analysis,
            "generated_at": "architect_first",
        }
    )
    
    return constraints


def validate_npc_placement(npc_type: str, 
                           proposed_position: Tuple[float, float],
                           constraints: SpatialConstraints) -> Tuple[bool, str]:
    """
    Validate that an NPC can be placed at a proposed position.
    
    Args:
        npc_type: Type/role of NPC (e.g., "waitress", "customer", "guard")
        proposed_position: (x, y) normalized position (0-1 range)
        constraints: The spatial constraints for this location
        
    Returns:
        (is_valid, reason) - True if valid, False with explanation if not
    """
    agent = get_architect_agent()
    
    # Check if position is within any valid zone
    x, y = proposed_position
    width, height = constraints.dimensions
    
    # Convert normalized to meters
    pos_x = x * width
    pos_y = y * height
    
    in_valid_zone = False
    for zone in constraints.valid_npc_zones:
        bounds = zone["bounds"]
        if (bounds[0] <= pos_x <= bounds[0] + bounds[2] and
            bounds[1] <= pos_y <= bounds[1] + bounds[3]):
            in_valid_zone = True
            break
    
    if not in_valid_zone:
        return False, f"Position ({x:.2f}, {y:.2f}) is not in a valid NPC zone"
    
    # Check capacity
    # (Would need to track current count - simplified here)
    
    return True, "Placement valid"


def get_valid_spawn_position(constraints: SpatialConstraints, 
                              index: int = 0) -> Tuple[float, float]:
    """
    Get a valid spawn position for an NPC.
    
    Args:
        constraints: The spatial constraints
        index: Which spawn position to use (cycles if > available)
        
    Returns:
        (x, y) normalized position
    """
    if not constraints.spawn_positions:
        # Fallback: center of space
        return (0.5, 0.5)
    
    # Cycle through available positions
    pos_index = index % len(constraints.spawn_positions)
    return constraints.spawn_positions[pos_index]


# ═══════════════════════════════════════════════════════════════════════════════
# CREATOR → ARCHITECT PIPELINE
# Extract spatial information from narrative descriptions
# ═══════════════════════════════════════════════════════════════════════════════

# Spatial keywords that indicate object positions in narrative text
SPATIAL_KEYWORDS = {
    # Wall positions
    "against the wall": "wall",
    "along the wall": "wall", 
    "lining the wall": "wall",
    "pushed against": "wall",
    "backed against": "wall",
    
    # Specific walls
    "left wall": "left_wall",
    "right wall": "right_wall",
    "back wall": "back_wall",
    "far wall": "back_wall",
    "front wall": "front_wall",
    "near the entrance": "front",
    "by the entrance": "front",
    "by the door": "front",
    "near the door": "front",
    
    # Window positions (typically back or side walls)
    "by the window": "back_wall",
    "near the window": "back_wall",
    "beneath the window": "back_wall",
    "under the window": "back_wall",
    
    # Corner positions
    "in the corner": "corner",
    "corner of": "corner",
    "tucked in": "corner",
    "back corner": "back_corner",
    "far corner": "back_corner",
    "front corner": "front_corner",
    
    # Center positions (avoid these for obstacles)
    "in the center": "center",
    "in the middle": "center",
    "center of the room": "center",
    "middle of": "center",
    
    # Relative positions
    "opposite the": "opposite",
    "across from": "opposite",
    "facing the": "facing",
    "next to": "adjacent",
    "beside": "adjacent",
    "near": "nearby",
}

# Map position keywords to safe coordinates (avoiding 50% center lines)
POSITION_TO_COORDS = {
    # Walls - place objects against edges
    "wall": [(0.15, 0.5), (0.85, 0.5), (0.5, 0.15), (0.5, 0.85)],  # Will pick based on context
    "left_wall": (0.12, 0.65),      # Left edge, offset from horizontal center
    "right_wall": (0.88, 0.35),     # Right edge, offset from horizontal center
    "back_wall": (0.65, 0.88),      # Back edge, offset from vertical center
    "front_wall": (0.35, 0.12),     # Front edge, offset from vertical center
    "front": (0.35, 0.15),          # Near entrance
    
    # Corners - safe quadrant positions
    "corner": (0.15, 0.85),         # Default: back-left corner
    "back_corner": (0.85, 0.85),    # Back-right
    "front_corner": (0.15, 0.15),   # Front-left
    "back_left_corner": (0.15, 0.85),
    "back_right_corner": (0.85, 0.85),
    "front_left_corner": (0.15, 0.15),
    "front_right_corner": (0.85, 0.15),
    
    # Center - OFFSET to avoid wall lines
    "center": (0.35, 0.65),         # Offset from true center
    
    # Relative - will be resolved based on context
    "opposite": (0.65, 0.35),
    "facing": (0.35, 0.35),
    "adjacent": (0.25, 0.65),
    "nearby": (0.35, 0.75),
}


# ═══════════════════════════════════════════════════════════════════════════════
# INTERIOR DESIGN SYSTEM
# Realistic furniture placement based on room type and function
# ═══════════════════════════════════════════════════════════════════════════════

# Furniture placement rules - where items naturally go in real spaces
# Format: (wall_preference, corner_ok, needs_clearance, typical_companions)
FURNITURE_PLACEMENT_RULES = {
    # BEDS - Always against a wall, usually back or side wall, need nightstand space
    'bed': {'wall': 'back', 'corner_ok': True, 'clearance': 'sides', 'companions': ['nightstand', 'lamp']},
    'cot': {'wall': 'corner', 'corner_ok': True, 'clearance': 'one_side', 'companions': []},
    'mattress': {'wall': 'corner', 'corner_ok': True, 'clearance': 'one_side', 'companions': []},
    
    # DESKS - Against wall, near window for light, need chair space in front
    'desk': {'wall': 'side', 'corner_ok': True, 'clearance': 'front', 'companions': ['chair', 'lamp']},
    'workstation': {'wall': 'side', 'corner_ok': True, 'clearance': 'front', 'companions': ['chair', 'monitor']},
    'terminal': {'wall': 'side', 'corner_ok': True, 'clearance': 'front', 'companions': ['chair']},
    
    # TABLES - Can be center or against wall depending on type
    'table': {'wall': 'none', 'corner_ok': False, 'clearance': 'all', 'companions': ['chair']},
    'dining table': {'wall': 'none', 'corner_ok': False, 'clearance': 'all', 'companions': ['chair']},
    'coffee table': {'wall': 'none', 'corner_ok': False, 'clearance': 'front', 'companions': ['couch', 'sofa']},
    
    # SEATING - Couches against walls, chairs can be anywhere
    'couch': {'wall': 'back', 'corner_ok': False, 'clearance': 'front', 'companions': ['coffee table', 'lamp']},
    'sofa': {'wall': 'back', 'corner_ok': False, 'clearance': 'front', 'companions': ['coffee table', 'lamp']},
    'chair': {'wall': 'none', 'corner_ok': True, 'clearance': 'front', 'companions': []},
    'armchair': {'wall': 'side', 'corner_ok': True, 'clearance': 'front', 'companions': ['lamp', 'side table']},
    
    # STORAGE - Always against walls
    'wardrobe': {'wall': 'side', 'corner_ok': True, 'clearance': 'front', 'companions': []},
    'closet': {'wall': 'side', 'corner_ok': True, 'clearance': 'front', 'companions': []},
    'dresser': {'wall': 'side', 'corner_ok': False, 'clearance': 'front', 'companions': ['mirror']},
    'cabinet': {'wall': 'back', 'corner_ok': True, 'clearance': 'front', 'companions': []},
    'shelf': {'wall': 'any', 'corner_ok': True, 'clearance': 'none', 'companions': []},
    'bookshelf': {'wall': 'side', 'corner_ok': True, 'clearance': 'front', 'companions': []},
    
    # KITCHEN - Against walls, need counter space
    'counter': {'wall': 'back', 'corner_ok': False, 'clearance': 'front', 'companions': []},
    'stove': {'wall': 'back', 'corner_ok': False, 'clearance': 'front', 'companions': ['counter']},
    'refrigerator': {'wall': 'corner', 'corner_ok': True, 'clearance': 'front', 'companions': []},
    'sink': {'wall': 'back', 'corner_ok': False, 'clearance': 'front', 'companions': ['counter']},
    
    # BATHROOM - Fixed positions
    'toilet': {'wall': 'side', 'corner_ok': True, 'clearance': 'front', 'companions': []},
    'shower': {'wall': 'corner', 'corner_ok': True, 'clearance': 'front', 'companions': []},
    'bathtub': {'wall': 'back', 'corner_ok': True, 'clearance': 'side', 'companions': []},
    
    # DECORATIVE - Can go many places
    'plant': {'wall': 'corner', 'corner_ok': True, 'clearance': 'none', 'companions': []},
    'lamp': {'wall': 'corner', 'corner_ok': True, 'clearance': 'none', 'companions': []},
    'display': {'wall': 'any', 'corner_ok': False, 'clearance': 'front', 'companions': []},
    'mirror': {'wall': 'side', 'corner_ok': False, 'clearance': 'front', 'companions': []},
    'rug': {'wall': 'none', 'corner_ok': False, 'clearance': 'none', 'companions': []},
    
    # MISC
    'crate': {'wall': 'corner', 'corner_ok': True, 'clearance': 'none', 'companions': []},
    'bench': {'wall': 'side', 'corner_ok': False, 'clearance': 'front', 'companions': []},
    'stool': {'wall': 'none', 'corner_ok': True, 'clearance': 'none', 'companions': ['counter']},
    'nightstand': {'wall': 'side', 'corner_ok': True, 'clearance': 'none', 'companions': ['bed', 'lamp']},
}

# Room type templates - realistic layouts for different space types
# Each template has MORE items to create lived-in, populated spaces
ROOM_LAYOUT_TEMPLATES = {
    'bedroom': {
        'anchor': 'bed',  # Primary furniture piece
        'anchor_position': (0.5, 0.85),  # Centered on back wall
        'layout_zones': [
            {'zone': 'sleeping', 'area': (0.3, 0.6, 0.7, 0.95)},  # Back center
            {'zone': 'dressing', 'area': (0.05, 0.4, 0.25, 0.9)},  # Left side
            {'zone': 'work', 'area': (0.75, 0.4, 0.95, 0.7)},  # Right side
        ],
        'typical_items': ['bed', 'nightstand', 'nightstand', 'dresser', 'wardrobe', 'lamp', 'lamp', 'chair', 'mirror', 'plant', 'shelf'],
    },
    'office': {
        'anchor': 'desk',
        'anchor_position': (0.75, 0.5),  # Right side, facing room
        'layout_zones': [
            {'zone': 'work', 'area': (0.5, 0.3, 0.95, 0.7)},
            {'zone': 'storage', 'area': (0.05, 0.6, 0.3, 0.95)},
            {'zone': 'meeting', 'area': (0.05, 0.05, 0.4, 0.4)},
        ],
        'typical_items': ['desk', 'chair', 'chair', 'bookshelf', 'bookshelf', 'cabinet', 'terminal', 'lamp', 'plant', 'shelf', 'display'],
    },
    'living_room': {
        'anchor': 'couch',
        'anchor_position': (0.5, 0.75),  # Back center
        'layout_zones': [
            {'zone': 'seating', 'area': (0.2, 0.5, 0.8, 0.9)},
            {'zone': 'entertainment', 'area': (0.3, 0.05, 0.7, 0.3)},
            {'zone': 'reading', 'area': (0.05, 0.05, 0.25, 0.4)},
        ],
        'typical_items': ['couch', 'coffee table', 'armchair', 'armchair', 'lamp', 'lamp', 'shelf', 'display', 'plant', 'plant', 'cabinet', 'rug'],
    },
    'kitchen': {
        'anchor': 'counter',
        'anchor_position': (0.5, 0.9),  # Back wall
        'layout_zones': [
            {'zone': 'cooking', 'area': (0.3, 0.7, 0.7, 0.95)},
            {'zone': 'storage', 'area': (0.05, 0.5, 0.25, 0.95)},
            {'zone': 'prep', 'area': (0.75, 0.5, 0.95, 0.95)},
        ],
        'typical_items': ['counter', 'counter', 'stove', 'refrigerator', 'sink', 'cabinet', 'cabinet', 'table', 'chair', 'chair', 'shelf'],
    },
    'bathroom': {
        'anchor': 'sink',
        'anchor_position': (0.5, 0.85),
        'layout_zones': [
            {'zone': 'washing', 'area': (0.3, 0.6, 0.7, 0.95)},
            {'zone': 'toilet', 'area': (0.05, 0.5, 0.25, 0.8)},
            {'zone': 'bathing', 'area': (0.75, 0.3, 0.95, 0.95)},
        ],
        'typical_items': ['sink', 'toilet', 'shower', 'cabinet', 'mirror', 'shelf', 'plant'],
    },
    'bank': {
        'anchor': 'counter',
        'anchor_position': (0.5, 0.8),  # Service counter at back
        'layout_zones': [
            {'zone': 'service', 'area': (0.2, 0.6, 0.8, 0.95)},
            {'zone': 'waiting', 'area': (0.1, 0.1, 0.9, 0.4)},
            {'zone': 'private', 'area': (0.8, 0.5, 0.95, 0.95)},
        ],
        'typical_items': ['counter', 'counter', 'terminal', 'terminal', 'chair', 'chair', 'chair', 'bench', 'desk', 'display', 'display', 'cabinet', 'plant', 'lamp'],
    },
    'shop': {
        'anchor': 'counter',
        'anchor_position': (0.85, 0.5),  # Counter on right side
        'layout_zones': [
            {'zone': 'display', 'area': (0.1, 0.1, 0.7, 0.9)},
            {'zone': 'checkout', 'area': (0.75, 0.3, 0.95, 0.7)},
            {'zone': 'storage', 'area': (0.75, 0.75, 0.95, 0.95)},
        ],
        'typical_items': ['counter', 'shelf', 'shelf', 'shelf', 'display', 'display', 'terminal', 'cabinet', 'chair', 'plant', 'lamp'],
    },
    'bar': {
        'anchor': 'counter',
        'anchor_position': (0.5, 0.85),  # Bar counter at back
        'layout_zones': [
            {'zone': 'bar', 'area': (0.15, 0.65, 0.85, 0.95)},
            {'zone': 'seating', 'area': (0.1, 0.1, 0.9, 0.5)},
            {'zone': 'stage', 'area': (0.3, 0.05, 0.7, 0.2)},
        ],
        'typical_items': ['counter', 'stool', 'stool', 'stool', 'stool', 'table', 'table', 'chair', 'chair', 'chair', 'shelf', 'display', 'lamp', 'lamp', 'plant'],
    },
    'corridor': {
        'anchor': None,
        'anchor_position': None,
        'layout_zones': [
            {'zone': 'passage', 'area': (0.3, 0.1, 0.7, 0.9)},
        ],
        'typical_items': ['lamp', 'lamp', 'plant', 'bench', 'display'],
    },
    'medical': {
        'anchor': 'bed',
        'anchor_position': (0.5, 0.7),
        'layout_zones': [
            {'zone': 'treatment', 'area': (0.3, 0.5, 0.7, 0.9)},
            {'zone': 'equipment', 'area': (0.75, 0.3, 0.95, 0.9)},
            {'zone': 'waiting', 'area': (0.05, 0.05, 0.3, 0.4)},
        ],
        'typical_items': ['bed', 'terminal', 'cabinet', 'cabinet', 'chair', 'chair', 'desk', 'display', 'shelf', 'lamp'],
    },
    'warehouse': {
        'anchor': None,
        'anchor_position': None,
        'layout_zones': [
            {'zone': 'storage', 'area': (0.1, 0.1, 0.9, 0.9)},
        ],
        'typical_items': ['shelf', 'shelf', 'shelf', 'shelf', 'cabinet', 'cabinet', 'crate', 'crate', 'crate', 'terminal', 'lamp'],
    },
    'default': {
        'anchor': None,
        'anchor_position': None,
        'layout_zones': [
            {'zone': 'main', 'area': (0.1, 0.1, 0.9, 0.9)},
        ],
        'typical_items': ['table', 'chair', 'chair', 'shelf', 'lamp', 'plant', 'cabinet', 'display'],
    },
}


def analyze_space_function(scene_description: str, location_name: str = "") -> Dict:
    """
    Analyze the FUNCTION of a space from its description - genre agnostic.
    
    Instead of matching "bedroom" or "tavern", we detect:
    - Primary function (sleep, work, commerce, transit, social, combat, storage)
    - Density (sparse, moderate, cluttered)
    - Formality (formal, casual, utilitarian)
    - Scale (intimate, standard, grand)
    
    This works for any genre: cyberpunk megacorp office, fantasy inn, 
    wild west saloon, spaceship quarters, medieval throne room, etc.
    """
    text = (scene_description + " " + location_name).lower()
    
    # Detect PRIMARY FUNCTION by looking for activity/purpose indicators
    function_indicators = {
        'sleep': ['bed', 'sleep', 'rest', 'quarters', 'bunk', 'dormitory', 'inn', 'hotel', 
                  'chamber', 'cot', 'mattress', 'pillow', 'blanket'],
        'work': ['desk', 'office', 'work', 'terminal', 'computer', 'study', 'craft', 
                 'forge', 'workshop', 'laboratory', 'research', 'write', 'type'],
        'commerce': ['shop', 'store', 'market', 'vendor', 'merchant', 'trade', 'buy', 'sell',
                     'counter', 'wares', 'goods', 'price', 'coin', 'credit', 'bank', 'vault'],
        'social': ['bar', 'tavern', 'pub', 'lounge', 'club', 'cantina', 'saloon', 'cafe',
                   'restaurant', 'dining', 'drink', 'gather', 'meet', 'party', 'feast'],
        'transit': ['corridor', 'hallway', 'passage', 'tunnel', 'walkway', 'alley', 'street',
                    'path', 'bridge', 'stairs', 'elevator', 'airlock', 'gate', 'entrance'],
        'storage': ['warehouse', 'storage', 'depot', 'cargo', 'hangar', 'garage', 'cellar',
                    'basement', 'attic', 'closet', 'vault', 'armory', 'pantry', 'larder'],
        'medical': ['medical', 'clinic', 'hospital', 'infirmary', 'healer', 'doctor', 'nurse',
                    'pharmacy', 'apothecary', 'surgery', 'treatment', 'patient', 'wound'],
        'worship': ['temple', 'church', 'shrine', 'altar', 'chapel', 'cathedral', 'sanctuary',
                    'prayer', 'worship', 'holy', 'sacred', 'divine'],
        'authority': ['throne', 'court', 'council', 'headquarters', 'command', 'bridge',
                      'captain', 'leader', 'chief', 'mayor', 'governor', 'king', 'queen'],
        'cooking': ['kitchen', 'galley', 'cook', 'stove', 'oven', 'fire', 'pot', 'pan',
                    'food', 'meal', 'prepare', 'chef', 'hearth'],
        'hygiene': ['bathroom', 'bath', 'wash', 'shower', 'toilet', 'latrine', 'privy',
                    'sink', 'water', 'clean', 'soap'],
        'living': ['living', 'sitting', 'common', 'lounge', 'parlor', 'den', 'family',
                   'couch', 'sofa', 'fireplace', 'hearth', 'relax'],
    }
    
    # Score each function
    function_scores = {}
    for func, keywords in function_indicators.items():
        score = sum(1 for kw in keywords if kw in text)
        if score > 0:
            function_scores[func] = score
    
    # Get primary function (highest score) or 'general' if none
    primary_function = max(function_scores, key=function_scores.get) if function_scores else 'general'
    
    # Detect DENSITY from descriptive words
    density = 'moderate'
    sparse_words = ['empty', 'bare', 'sparse', 'minimal', 'clean', 'open', 'spacious', 'vast']
    cluttered_words = ['cluttered', 'crowded', 'packed', 'stuffed', 'overflowing', 'cramped', 
                       'messy', 'chaotic', 'piled', 'stacked', 'filled', 'busy']
    if any(w in text for w in sparse_words):
        density = 'sparse'
    elif any(w in text for w in cluttered_words):
        density = 'cluttered'
    
    # Detect FORMALITY
    formality = 'casual'
    formal_words = ['formal', 'elegant', 'ornate', 'grand', 'official', 'pristine', 'polished',
                    'marble', 'gold', 'silver', 'velvet', 'silk', 'crystal', 'chandelier']
    utilitarian_words = ['utilitarian', 'functional', 'industrial', 'bare', 'metal', 'concrete',
                         'steel', 'pipes', 'wires', 'machinery', 'equipment', 'tools']
    if any(w in text for w in formal_words):
        formality = 'formal'
    elif any(w in text for w in utilitarian_words):
        formality = 'utilitarian'
    
    # Detect SCALE from size words
    scale = 'standard'
    intimate_words = ['small', 'tiny', 'cramped', 'narrow', 'compact', 'cozy', 'intimate']
    grand_words = ['large', 'vast', 'huge', 'grand', 'massive', 'enormous', 'cavernous', 'sprawling']
    if any(w in text for w in intimate_words):
        scale = 'intimate'
    elif any(w in text for w in grand_words):
        scale = 'grand'
    
    return {
        'primary_function': primary_function,
        'secondary_functions': [f for f, s in sorted(function_scores.items(), key=lambda x: -x[1])[1:3]],
        'density': density,
        'formality': formality,
        'scale': scale,
    }


# Function-based furniture sets - what items serve each PURPOSE (genre-agnostic)
FUNCTION_FURNITURE = {
    'sleep': {
        'anchor': ('bed', (3.0, 4.0), 'back'),
        'essential': [('nightstand', (0.8, 0.8)), ('lamp', (0.4, 0.4))],
        'common': [('dresser', (2.0, 1.0)), ('wardrobe', (2.5, 1.0)), ('mirror', (1.5, 0.3)), ('chair', (1.0, 1.0))],
        'decorative': [('plant', (0.5, 0.5)), ('rug', (3.0, 2.0)), ('shelf', (2.0, 0.5))],
    },
    'work': {
        'anchor': ('desk', (2.5, 1.5), 'side'),
        'essential': [('chair', (1.0, 1.0)), ('lamp', (0.4, 0.4))],
        'common': [('bookshelf', (2.5, 0.8)), ('cabinet', (1.5, 1.0)), ('shelf', (2.5, 0.5))],
        'decorative': [('plant', (0.5, 0.5)), ('display', (2.0, 0.5))],
    },
    'commerce': {
        'anchor': ('counter', (5.0, 1.5), 'back'),
        'essential': [('shelf', (2.5, 0.5)), ('display', (2.0, 0.5))],
        'common': [('cabinet', (1.5, 1.0)), ('chair', (1.0, 1.0)), ('crate', (1.0, 1.0))],
        'decorative': [('plant', (0.5, 0.5)), ('lamp', (0.4, 0.4))],
    },
    'social': {
        'anchor': ('counter', (5.0, 1.5), 'back'),
        'essential': [('stool', (0.6, 0.6)), ('table', (3.0, 2.0)), ('chair', (1.0, 1.0))],
        'common': [('shelf', (2.5, 0.5)), ('bench', (2.5, 0.8)), ('lamp', (0.4, 0.4))],
        'decorative': [('plant', (0.5, 0.5)), ('display', (2.0, 0.5)), ('rug', (3.0, 2.0))],
    },
    'transit': {
        'anchor': None,
        'essential': [],
        'common': [('lamp', (0.4, 0.4)), ('bench', (2.5, 0.8))],
        'decorative': [('plant', (0.5, 0.5)), ('display', (2.0, 0.5))],
    },
    'storage': {
        'anchor': None,
        'essential': [('shelf', (2.5, 0.5)), ('crate', (1.0, 1.0))],
        'common': [('cabinet', (1.5, 1.0)), ('shelf', (2.5, 0.5))],
        'decorative': [('lamp', (0.4, 0.4))],
    },
    'medical': {
        'anchor': ('bed', (3.0, 4.0), 'side'),
        'essential': [('cabinet', (1.5, 1.0)), ('chair', (1.0, 1.0))],
        'common': [('desk', (2.5, 1.5)), ('shelf', (2.5, 0.5)), ('display', (2.0, 0.5))],
        'decorative': [('plant', (0.5, 0.5)), ('lamp', (0.4, 0.4))],
    },
    'worship': {
        'anchor': ('altar', (2.0, 1.5), 'back'),
        'essential': [('bench', (2.5, 0.8))],
        'common': [('lamp', (0.4, 0.4)), ('display', (2.0, 0.5)), ('shelf', (2.5, 0.5))],
        'decorative': [('plant', (0.5, 0.5)), ('rug', (3.0, 2.0))],
    },
    'authority': {
        'anchor': ('desk', (3.0, 2.0), 'back'),
        'essential': [('chair', (1.5, 1.5))],
        'common': [('bookshelf', (2.5, 0.8)), ('cabinet', (1.5, 1.0)), ('display', (2.0, 0.5))],
        'decorative': [('plant', (0.5, 0.5)), ('lamp', (0.4, 0.4)), ('rug', (3.0, 2.0))],
    },
    'cooking': {
        'anchor': ('counter', (4.0, 1.5), 'back'),
        'essential': [('stove', (1.5, 1.5)), ('sink', (1.5, 1.0))],
        'common': [('cabinet', (1.5, 1.0)), ('shelf', (2.5, 0.5)), ('table', (3.0, 2.0))],
        'decorative': [('plant', (0.5, 0.5)), ('lamp', (0.4, 0.4))],
    },
    'hygiene': {
        'anchor': ('sink', (1.5, 1.0), 'back'),
        'essential': [('toilet', (1.0, 1.5))],
        'common': [('shower', (2.0, 2.0)), ('cabinet', (1.5, 1.0)), ('mirror', (1.5, 0.3))],
        'decorative': [('plant', (0.5, 0.5))],
    },
    'living': {
        'anchor': ('couch', (4.0, 2.0), 'back'),
        'essential': [('table', (2.0, 1.0))],
        'common': [('armchair', (1.5, 1.5)), ('shelf', (2.5, 0.5)), ('lamp', (0.4, 0.4))],
        'decorative': [('plant', (0.5, 0.5)), ('rug', (3.0, 2.0)), ('display', (2.0, 0.5))],
    },
    'general': {
        'anchor': None,
        'essential': [('table', (3.0, 2.0)), ('chair', (1.0, 1.0))],
        'common': [('shelf', (2.5, 0.5)), ('cabinet', (1.5, 1.0)), ('lamp', (0.4, 0.4))],
        'decorative': [('plant', (0.5, 0.5)), ('display', (2.0, 0.5))],
    },
}


def generate_realistic_layout(
    scene_description: str,
    location_name: str,
    width: float,
    height: float,
    extracted_objects: List['ExtractedObject'] = None
) -> List[Dict]:
    """
    ARCHITECT: Generate a realistic room layout based on interior design principles.
    
    Key principles from the reference images:
    1. Furniture hugs walls - beds, desks, wardrobes against edges
    2. Functional groupings - related items together (bed + nightstands)
    3. Clear pathways - walking space through the room
    4. Asymmetry - real rooms aren't perfectly symmetric
    5. Purpose-driven - each item where it would actually be used
    
    Uses FUNCTION-BASED analysis instead of genre-specific room types.
    Works for any setting: cyberpunk, fantasy, western, sci-fi, etc.
    
    Args:
        scene_description: Narrative description of the space
        location_name: Name of the location
        width: Room width in units
        height: Room height in units
        extracted_objects: Optional pre-extracted objects from narrative
        
    Returns:
        List of obstacle dictionaries with realistic positions
    """
    import random
    
    # Analyze space function (genre-agnostic)
    space_analysis = analyze_space_function(scene_description, location_name)
    primary_function = space_analysis['primary_function']
    density = space_analysis['density']
    scale = space_analysis['scale']
    
    # Get furniture set for this function
    furniture_set = FUNCTION_FURNITURE.get(primary_function, FUNCTION_FURNITURE['general'])
    
    print(f"[ARCHITECT] Space function: {primary_function} | Density: {density} | Scale: {scale}")
    
    obstacles = []
    placed_positions = []  # Track placed items to avoid overlap
    
    # Margin from walls (but items CAN be against walls)
    wall_margin = 0.08  # 8% from edge for wall-hugging items
    center_margin = 0.15  # Keep center clear for pathways
    
    # Helper to check if position is valid (no overlap, not in center pathway)
    def is_valid_position(x, y, w, h):
        # Normalize to 0-1
        nx, ny = x / width, y / height
        
        # Check center pathway (keep clear for walking)
        if 0.4 < nx < 0.6 and 0.3 < ny < 0.7:
            return False
        
        # Check overlap with existing items
        for px, py, pw, ph in placed_positions:
            if (abs(x - px) < (w + pw) / 2 + 1 and 
                abs(y - py) < (h + ph) / 2 + 1):
                return False
        
        return True
    
    # Helper to place item against a wall
    def place_against_wall(wall: str, item_width: float, item_height: float, offset: float = 0):
        """Place item against specified wall with optional offset along the wall."""
        if wall == 'back':
            x = width * (0.3 + offset * 0.4)  # Vary along back wall
            y = height * (1 - wall_margin) - item_height / 2
        elif wall == 'front':
            x = width * (0.3 + offset * 0.4)
            y = height * wall_margin + item_height / 2
        elif wall == 'left':
            x = width * wall_margin + item_width / 2
            y = height * (0.3 + offset * 0.4)
        elif wall == 'right':
            x = width * (1 - wall_margin) - item_width / 2
            y = height * (0.3 + offset * 0.4)
        elif wall == 'corner':
            # Pick a corner
            corners = [
                (width * wall_margin + item_width/2, height * (1 - wall_margin) - item_height/2),  # back-left
                (width * (1 - wall_margin) - item_width/2, height * (1 - wall_margin) - item_height/2),  # back-right
                (width * wall_margin + item_width/2, height * wall_margin + item_height/2),  # front-left
            ]
            x, y = corners[int(offset * len(corners)) % len(corners)]
        else:
            # 'any' or 'none' - place in a zone
            x = width * (0.2 + offset * 0.6)
            y = height * (0.3 + offset * 0.4)
        
        return x, y
    
    # Build items list from function-based furniture set
    items_to_place = []
    
    # First add any extracted objects from the narrative
    if extracted_objects:
        for obj in extracted_objects:
            items_to_place.append((obj.name.lower(), obj.object_type, obj.position_coords))
    
    # Add essential items for this function (always included)
    for item_name, item_size in furniture_set.get('essential', []):
        if item_name not in [i[0] for i in items_to_place]:
            items_to_place.append((item_name, 'furniture', None))
    
    # Add common items based on density
    common_items = furniture_set.get('common', [])
    if density == 'cluttered':
        # Add all common items, some duplicated
        for item_name, item_size in common_items:
            items_to_place.append((item_name, 'furniture', None))
        for item_name, item_size in common_items[:3]:  # Duplicate first 3
            items_to_place.append((item_name, 'furniture', None))
    elif density == 'moderate':
        # Add all common items
        for item_name, item_size in common_items:
            items_to_place.append((item_name, 'furniture', None))
    else:  # sparse
        # Add only half of common items
        for item_name, item_size in common_items[:len(common_items)//2]:
            items_to_place.append((item_name, 'furniture', None))
    
    # Add decorative items based on scale and density
    decorative = furniture_set.get('decorative', [])
    if scale == 'grand' or density == 'cluttered':
        # Add all decorative items, duplicated for larger spaces
        for item_name, item_size in decorative:
            items_to_place.append((item_name, 'decoration', None))
            if scale == 'grand':
                items_to_place.append((item_name, 'decoration', None))
    elif density != 'sparse':
        for item_name, item_size in decorative:
            items_to_place.append((item_name, 'decoration', None))
    
    # Add items from secondary functions for mixed-use spaces
    for sec_func in space_analysis.get('secondary_functions', [])[:1]:
        sec_furniture = FUNCTION_FURNITURE.get(sec_func, {})
        for item_name, item_size in sec_furniture.get('essential', [])[:2]:
            if item_name not in [i[0] for i in items_to_place]:
                items_to_place.append((item_name, 'furniture', None))
    
    # Place anchor item first if furniture set has one
    anchor_data = furniture_set.get('anchor')
    if anchor_data:
        anchor_name, (aw, ah), anchor_wall = anchor_data
        
        # Position anchor based on wall preference
        if anchor_wall == 'back':
            ax = width * 0.5
            ay = height * (1 - wall_margin) - ah / 2
        elif anchor_wall == 'side':
            ax = width * (1 - wall_margin) - aw / 2
            ay = height * 0.5
        elif anchor_wall == 'front':
            ax = width * 0.5
            ay = height * wall_margin + ah / 2
        else:
            ax = width * 0.5
            ay = height * 0.7
        
        obstacles.append({
            'name': anchor_name.title(),
            'type': 'furniture',
            'x': ax,
            'y': ay,
            'width': aw,
            'height': ah,
            'position_hint': f'{anchor_wall}_anchor',
            'confidence': 1.0,
            'blocks_movement': True,
            'blocks_los': False,
        })
        placed_positions.append((ax, ay, aw, ah))
    
    # Determine max items based on room size
    room_area = width * height
    if room_area < 150:
        max_items = 6
    elif room_area < 300:
        max_items = 10
    elif room_area < 500:
        max_items = 14
    else:
        max_items = 18  # Large spaces can have many items
    
    # Place remaining items using placement rules
    wall_offset = 0
    anchor_name = anchor_data[0] if anchor_data else None
    
    for item_tuple in items_to_place[:max_items]:
        # Unpack tuple (may have 2 or 3 elements)
        if len(item_tuple) == 3:
            item_name, item_type, hint_coords = item_tuple
        else:
            item_name, item_type = item_tuple
            hint_coords = None
        
        # Skip if already placed as anchor
        if anchor_name and item_name == anchor_name:
            continue
        
        # Get placement rules for this item
        rules = FURNITURE_PLACEMENT_RULES.get(item_name, {
            'wall': 'side', 'corner_ok': True, 'clearance': 'front', 'companions': []
        })
        
        # Determine size based on item type
        size_map = {
            # Beds
            'bed': (3.0, 4.0), 'cot': (2.0, 3.0), 'mattress': (2.5, 3.5),
            # Work surfaces
            'desk': (2.5, 1.5), 'workstation': (3.0, 2.0), 'terminal': (1.5, 1.0),
            # Tables
            'table': (3.0, 2.0), 'coffee table': (2.0, 1.0), 'dining table': (4.0, 2.5),
            # Seating
            'couch': (4.0, 2.0), 'sofa': (4.0, 2.0), 'chair': (1.0, 1.0), 'armchair': (1.5, 1.5),
            'stool': (0.6, 0.6), 'bench': (2.5, 0.8),
            # Storage
            'wardrobe': (2.5, 1.0), 'closet': (2.0, 1.0), 'dresser': (2.0, 1.0),
            'cabinet': (1.5, 1.0), 'shelf': (2.5, 0.5), 'bookshelf': (2.5, 0.8),
            'crate': (1.0, 1.0),
            # Kitchen
            'counter': (4.0, 1.5), 'stove': (1.5, 1.5), 'refrigerator': (1.5, 1.5), 'sink': (1.5, 1.0),
            # Bathroom
            'toilet': (1.0, 1.5), 'shower': (2.0, 2.0), 'bathtub': (2.0, 4.0),
            # Decorative
            'lamp': (0.4, 0.4), 'plant': (0.5, 0.5), 'display': (2.0, 0.5),
            'mirror': (1.5, 0.3), 'rug': (3.0, 2.0),
            # Bedroom
            'nightstand': (0.8, 0.8),
        }
        iw, ih = size_map.get(item_name, (1.5, 1.5))
        
        # Determine wall preference
        wall_pref = rules.get('wall', 'side')
        if wall_pref == 'side':
            wall_pref = 'left' if wall_offset % 2 == 0 else 'right'
        elif wall_pref == 'any':
            walls = ['left', 'right', 'back']
            wall_pref = walls[wall_offset % len(walls)]
        
        # Try to place against preferred wall
        offset_along_wall = random.uniform(0.1, 0.9)
        x, y = place_against_wall(wall_pref, iw, ih, offset_along_wall)
        
        # Validate position
        attempts = 0
        while not is_valid_position(x, y, iw, ih) and attempts < 10:
            offset_along_wall = random.uniform(0.1, 0.9)
            wall_pref = ['left', 'right', 'back', 'corner'][attempts % 4]
            x, y = place_against_wall(wall_pref, iw, ih, offset_along_wall)
            attempts += 1
        
        if is_valid_position(x, y, iw, ih):
            obstacles.append({
                'name': item_name.title(),
                'type': item_type,
                'x': x,
                'y': y,
                'width': iw,
                'height': ih,
                'position_hint': wall_pref,
                'confidence': 0.8,
                'blocks_movement': item_type in ['furniture', 'fixture'],
                'blocks_los': item_name in ['wardrobe', 'bookshelf', 'cabinet'],
            })
            placed_positions.append((x, y, iw, ih))
        
        wall_offset += 1
    
    return obstacles


@dataclass
class ExtractedObject:
    """An object extracted from narrative text with spatial information."""
    name: str
    object_type: str  # furniture, fixture, decoration, etc.
    position_hint: str  # The spatial keyword found
    position_coords: Tuple[float, float]  # Normalized (x, y)
    context: str  # The sentence it was found in
    confidence: float  # How confident we are in the extraction


def extract_objects_from_description(scene_description: str) -> List[ExtractedObject]:
    """
    CREATOR → ARCHITECT: Parse narrative description to extract objects and positions.
    
    The Creator generates rich narrative descriptions like:
        "A cramped apartment with a fold-out bed pushed against the left wall,
         a cluttered desk by the window, and a small kitchenette in the corner."
    
    This function extracts:
        - fold-out bed → left_wall → (0.12, 0.65)
        - desk → back_wall (by window) → (0.65, 0.88)
        - kitchenette → corner → (0.15, 0.85)
    
    Args:
        scene_description: Narrative text from Creator
        
    Returns:
        List of ExtractedObject with positions
    """
    extracted = []
    
    # Common furniture/fixture patterns
    object_patterns = [
        # Furniture
        (r'\b(bed|cot|mattress|futon|fold-out bed)\b', 'furniture'),
        (r'\b(desk|table|workstation|counter|countertop)\b', 'furniture'),
        (r'\b(chair|stool|seat|bench|couch|sofa)\b', 'furniture'),
        (r'\b(shelf|shelves|bookshelf|cabinet|dresser|wardrobe|closet)\b', 'furniture'),
        
        # Fixtures
        (r'\b(sink|toilet|shower|bathtub|tub)\b', 'fixture'),
        (r'\b(stove|oven|refrigerator|fridge|microwave)\b', 'fixture'),
        (r'\b(terminal|console|monitor|screen|display)\b', 'fixture'),
        
        # Decorations/misc
        (r'\b(plant|potted plant|fern)\b', 'decoration'),
        (r'\b(lamp|light|fixture)\b', 'decoration'),
        (r'\b(rug|carpet|mat)\b', 'decoration'),
        
        # Structural
        (r'\b(door|entrance|exit|doorway)\b', 'structural'),
        (r'\b(window|windows)\b', 'structural'),
        (r'\b(stairs|staircase|ladder)\b', 'structural'),
    ]
    
    import re
    
    # Split into sentences for context
    sentences = re.split(r'[.!?]', scene_description)
    
    for sentence in sentences:
        sentence_lower = sentence.lower().strip()
        if not sentence_lower:
            continue
        
        # Find objects in this sentence
        for pattern, obj_type in object_patterns:
            matches = re.finditer(pattern, sentence_lower)
            for match in matches:
                obj_name = match.group(1)
                
                # Look for spatial keywords near this object
                best_position = None
                best_confidence = 0.0
                
                for keyword, position in SPATIAL_KEYWORDS.items():
                    if keyword in sentence_lower:
                        # Check if keyword is near the object (within ~50 chars)
                        keyword_pos = sentence_lower.find(keyword)
                        obj_pos = match.start()
                        distance = abs(keyword_pos - obj_pos)
                        
                        # Closer = higher confidence
                        confidence = max(0.3, 1.0 - (distance / 100))
                        
                        if confidence > best_confidence:
                            best_confidence = confidence
                            best_position = position
                
                # Get coordinates for this position
                if best_position and best_position in POSITION_TO_COORDS:
                    coords = POSITION_TO_COORDS[best_position]
                    # Handle list of coords (pick first for now)
                    if isinstance(coords, list):
                        coords = coords[0]
                    
                    extracted.append(ExtractedObject(
                        name=obj_name.title(),
                        object_type=obj_type,
                        position_hint=best_position,
                        position_coords=coords,
                        context=sentence.strip(),
                        confidence=best_confidence
                    ))
                elif best_position is None:
                    # No spatial keyword found - use default based on object type
                    default_positions = {
                        'furniture': (0.35, 0.75),  # Back-left quadrant
                        'fixture': (0.75, 0.85),    # Back-right quadrant
                        'decoration': (0.25, 0.35), # Front-left quadrant
                        'structural': (0.35, 0.12), # Front (doors/entrances)
                    }
                    coords = default_positions.get(obj_type, (0.35, 0.65))
                    
                    extracted.append(ExtractedObject(
                        name=obj_name.title(),
                        object_type=obj_type,
                        position_hint="default",
                        position_coords=coords,
                        context=sentence.strip(),
                        confidence=0.3  # Low confidence for defaults
                    ))
    
    # Deduplicate by name, keeping highest confidence
    seen = {}
    for obj in extracted:
        if obj.name not in seen or obj.confidence > seen[obj.name].confidence:
            seen[obj.name] = obj
    
    return list(seen.values())


# ═══════════════════════════════════════════════════════════════════════════════
# MOVEMENT RESOLUTION - Consolidated from spatial_position_resolver.py
# The Architect resolves movement targets to validated coordinates
# ═══════════════════════════════════════════════════════════════════════════════

def resolve_movement_target(
    target: str,
    current_position: Tuple[float, float],
    spatial_context: Any,
    user_input: str = ""
) -> Optional[Tuple[float, float]]:
    """
    ARCHITECT: Resolve a movement target to validated coordinates.
    
    Consolidates all movement resolution logic:
    - Obstacles (desk, bed, counter)
    - Actors (approach NPC by name)
    - Zones (seating area, kitchen)
    - Directions (left, back, corner)
    - Narrative phrases ("by the window", "near the entrance")
    
    Args:
        target: The movement target from user input
        current_position: (x, y) current actor position
        spatial_context: SpatialContext with location data
        user_input: Full user input for context
        
    Returns:
        (x, y) validated coordinates, or None if can't resolve
    """
    if not spatial_context or not hasattr(spatial_context, 'location_dimensions'):
        return None
    
    dims = spatial_context.location_dimensions
    width = dims.width
    height = dims.height
    target_lower = target.lower().strip()
    input_lower = user_input.lower() if user_input else target_lower
    
    # 1. TRY SPATIAL KEYWORDS FROM NARRATIVE (highest priority)
    # These match phrases like "by the window", "near the entrance"
    for keyword, position_key in SPATIAL_KEYWORDS.items():
        if keyword in input_lower or keyword in target_lower:
            if position_key in POSITION_TO_COORDS:
                coords = POSITION_TO_COORDS[position_key]
                if isinstance(coords, list):
                    coords = coords[0]
                # Convert normalized to actual
                x = coords[0] * width
                y = coords[1] * height
                # Validate: avoid center lines
                if 0.45 < coords[0] < 0.55:
                    x = width * 0.35
                if 0.45 < coords[1] < 0.55:
                    y = height * 0.65
                return (x, y)
    
    # 2. TRY ACTOR MATCHING
    result = _resolve_actor(target_lower, spatial_context, current_position)
    if result:
        print(f"[ARCHITECT] Movement target resolved as actor: '{target}'")
        return result
    
    # 3. TRY OBSTACLE MATCHING
    result = _resolve_obstacle(target_lower, spatial_context, current_position)
    if result:
        return result
    
    # 4. TRY ZONE MATCHING
    result = _resolve_zone(target_lower, spatial_context)
    if result:
        return result
    
    # 5. TRY DIRECTION MATCHING
    result = _resolve_direction(target_lower, width, height, current_position)
    if result:
        return result
    
    # 6. FALLBACK: Small movement in a sensible direction
    # Don't return None - give a reasonable fallback
    curr_x, curr_y = current_position
    
    # Move toward center if at edges, otherwise move forward (higher Y)
    if curr_x < width * 0.3:
        new_x = curr_x + 3
    elif curr_x > width * 0.7:
        new_x = curr_x - 3
    else:
        new_x = curr_x
    
    if curr_y < height * 0.3:
        new_y = curr_y + 3
    elif curr_y > height * 0.7:
        new_y = curr_y - 3
    else:
        new_y = curr_y + 2  # Default: move forward
    
    # Clamp to bounds
    new_x = max(2, min(width - 2, new_x))
    new_y = max(2, min(height - 2, new_y))
    
    return (new_x, new_y)


def _axis_adjacent(center_x: float, center_y: float, curr_x: float, curr_y: float,
                    width: float = 50.0, height: float = 50.0) -> Tuple[float, float]:
    """Return the axis-aligned position 1 unit from (center_x, center_y) on the
    side closest to the approaching actor at (curr_x, curr_y).

    Rule: pick the dominant approach axis (larger |delta|), then place the
    actor exactly 1 unit away on that axis, same coordinate on the other axis.
    Result is always clamped to [1, dim-1].
    """
    dx = center_x - curr_x
    dy = center_y - curr_y
    if abs(dx) >= abs(dy):
        # Approaching from left or right
        adj_x = center_x - 1.0 if dx > 0 else center_x + 1.0
        adj_y = center_y
    else:
        # Approaching from above or below
        adj_x = center_x
        adj_y = center_y - 1.0 if dy > 0 else center_y + 1.0
    adj_x = max(1.0, min(width - 1.0, adj_x))
    adj_y = max(1.0, min(height - 1.0, adj_y))
    return (adj_x, adj_y)


def _resolve_obstacle(target: str, context: Any,
                      current_pos: Tuple[float, float] = (25.0, 25.0)) -> Optional[Tuple[float, float]]:
    """Find obstacle and return the axis-aligned position 1 unit away on the
    approach side (the side the actor is coming from)."""
    target_normalized = target.replace(" ", "").replace("-", "").replace("_", "")

    # Debug: Show available obstacles
    obs_count = len(context.location_dimensions.obstacles) if context.location_dimensions.obstacles else 0
    print(f"[ARCHITECT] Searching for '{target}' in {obs_count} obstacles")
    if obs_count > 0:
        obs_names = [getattr(o, 'obstacle_name', k) for k, o in list(context.location_dimensions.obstacles.items())[:5]]
        print(f"[ARCHITECT] Available: {obs_names}")

    dims = context.location_dimensions
    width = getattr(dims, 'width', 50.0) or 50.0
    height = getattr(dims, 'height', 50.0) or 50.0

    for obs_key, obstacle in context.location_dimensions.obstacles.items():
        key_normalized = obs_key.replace(" ", "").replace("-", "").replace("_", "")
        name_normalized = ""
        if hasattr(obstacle, 'obstacle_name') and obstacle.obstacle_name:
            name_normalized = obstacle.obstacle_name.lower().replace(" ", "").replace("-", "").replace("_", "")

        # Fuzzy match
        if (target_normalized in key_normalized or key_normalized in target_normalized or
            target_normalized in name_normalized or name_normalized in target_normalized):

            # Get center of obstacle
            if hasattr(obstacle, 'boundary_points') and obstacle.boundary_points:
                center_x = sum(p.x for p in obstacle.boundary_points) / len(obstacle.boundary_points)
                center_y = sum(p.y for p in obstacle.boundary_points) / len(obstacle.boundary_points)
            else:
                center_x = width / 2
                center_y = height / 2

            return _axis_adjacent(center_x, center_y, current_pos[0], current_pos[1], width, height)

    return None


def _resolve_actor(target: str, context: Any, current_pos: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    """Find actor and return the axis-aligned position 1 unit away on the
    approach side (the side the mover is coming from)."""
    for actor_id, actor_pos in context.actor_positions.items():
        actor_name = actor_pos.actor_name.lower() if hasattr(actor_pos, 'actor_name') else ""

        if target in actor_name or actor_name in target:
            actor_x = actor_pos.position.x
            actor_y = actor_pos.position.y
            curr_x, curr_y = current_pos

            dx = actor_x - curr_x
            dy = actor_y - curr_y
            dist = (dx**2 + dy**2)**0.5

            if dist <= 1.0:
                return current_pos  # Already adjacent

            # Place 1 unit away on the dominant approach axis
            try:
                dims = context.location_dimensions
                width = getattr(dims, 'width', 50.0) or 50.0
                height = getattr(dims, 'height', 50.0) or 50.0
            except Exception:
                width, height = 50.0, 50.0
            return _axis_adjacent(actor_x, actor_y, curr_x, curr_y, width, height)

    return None


def _resolve_zone(target: str, context: Any) -> Optional[Tuple[float, float]]:
    """Find zone and return center position."""
    for zone_name, zone in context.location_dimensions.zones.items():
        if target in zone_name.lower() or zone_name.lower() in target:
            if hasattr(zone, 'boundary_points') and zone.boundary_points and len(zone.boundary_points) >= 3:
                center_x = sum(p.x for p in zone.boundary_points) / len(zone.boundary_points)
                center_y = sum(p.y for p in zone.boundary_points) / len(zone.boundary_points)
                return (center_x, center_y)
    
    return None


def _resolve_direction(direction: str, width: float, height: float, 
                       current_pos: Tuple[float, float]) -> Optional[Tuple[float, float]]:
    """Convert direction to coordinates."""
    curr_x, curr_y = current_pos
    
    # Absolute directions - AVOID 50% center lines
    if direction in ['front', 'entrance', 'door']:
        return (width * 0.35, height * 0.15)
    
    elif direction in ['back', 'rear', 'far']:
        return (width * 0.65, height * 0.85)
    
    elif direction == 'left':
        return (width * 0.15, height * 0.35)
    
    elif direction == 'right':
        return (width * 0.85, height * 0.65)
    
    elif direction in ['center', 'middle']:
        return (width * 0.35, height * 0.65)  # Offset from true center
    
    # Corners
    elif 'corner' in direction:
        if 'left' in direction or 'west' in direction:
            if 'back' in direction or 'far' in direction:
                return (width * 0.1, height * 0.9)
            else:
                return (width * 0.1, height * 0.1)
        else:
            if 'back' in direction or 'far' in direction:
                return (width * 0.9, height * 0.9)
            else:
                return (width * 0.9, height * 0.1)
    
    # Relative directions
    elif direction in ['forward', 'ahead']:
        return (curr_x, min(height - 2, curr_y + 5))
    
    elif direction in ['backward', 'backwards']:
        return (curr_x, max(2, curr_y - 5))
    
    # Cardinal
    elif direction == 'north':
        return (width * 0.35, height * 0.85)
    elif direction == 'south':
        return (width * 0.65, height * 0.15)
    elif direction == 'east':
        return (width * 0.85, height * 0.35)
    elif direction == 'west':
        return (width * 0.15, height * 0.65)
    
    return None


def apply_creator_objects_to_layout(
    scene_description: str,
    spatial_constraints: SpatialConstraints,
    width: float,
    height: float
) -> List[Dict[str, Any]]:
    """
    Full Creator → Architect pipeline: Extract objects from narrative and
    generate validated obstacle placements.
    
    Args:
        scene_description: The Creator's narrative description
        spatial_constraints: Architect's spatial constraints for this location
        width: Location width in meters
        height: Location height in meters
        
    Returns:
        List of obstacle dictionaries ready for spatial system
    """
    # Extract objects from Creator's description
    extracted = extract_objects_from_description(scene_description)
    
    if not extracted:
        return []
    
    obstacles = []
    used_positions = set()  # Track to avoid overlaps
    
    for obj in extracted:
        # Get base coordinates
        x_norm, y_norm = obj.position_coords
        
        # CRITICAL: Ensure we avoid center lines (50%)
        if 0.45 < x_norm < 0.55:
            x_norm = 0.35 if x_norm < 0.5 else 0.65
        if 0.45 < y_norm < 0.55:
            y_norm = 0.35 if y_norm < 0.5 else 0.65
        
        # Convert to actual coordinates
        x = x_norm * width
        y = y_norm * height
        
        # Check for overlaps - shift if needed
        pos_key = (round(x / 5) * 5, round(y / 5) * 5)  # Grid snap for overlap check
        shift = 0
        while pos_key in used_positions and shift < 4:
            shift += 1
            # Shift in a spiral pattern
            x_shift = [0.1, 0, -0.1, 0][shift % 4] * width
            y_shift = [0, 0.1, 0, -0.1][shift % 4] * height
            x += x_shift
            y += y_shift
            pos_key = (round(x / 5) * 5, round(y / 5) * 5)
        
        used_positions.add(pos_key)
        
        # Validate against Architect's forbidden placements
        space_type = spatial_constraints.space_type if spatial_constraints else SpaceType.ROOM
        forbidden = FORBIDDEN_PLACEMENTS.get(space_type, [])
        
        if obj.name.lower() in [f.lower() for f in forbidden]:
            print(f"[ARCHITECT] Skipping forbidden object '{obj.name}' for {space_type.value}")
            continue
        
        # Determine obstacle size based on type
        size_map = {
            'furniture': (2.0, 2.0),
            'fixture': (1.5, 1.5),
            'decoration': (0.5, 0.5),
            'structural': (1.0, 2.0),
        }
        size = size_map.get(obj.object_type, (1.0, 1.0))
        
        obstacles.append({
            'name': obj.name,
            'type': obj.object_type,
            'x': x,
            'y': y,
            'width': size[0],
            'height': size[1],
            'position_hint': obj.position_hint,
            'confidence': obj.confidence,
            'blocks_movement': obj.object_type in ['furniture', 'fixture', 'structural'],
            'blocks_los': obj.object_type == 'structural' and obj.name.lower() not in ['window', 'door'],
        })
    
    return obstacles


# ═══════════════════════════════════════════════════════════════════════════════
# NUA/MNUA MOVEMENT HELPER
# Unified function to move any actor on the spatial map
# ═══════════════════════════════════════════════════════════════════════════════

def move_actor_on_map(
    actor_name: str,
    movement_target: str,
    narrative: str = "",
    session_id: str = None
) -> bool:
    """
    ARCHITECT: Move any actor (UA, NUA, MNUA) on the spatial map.
    
    This is the unified entry point for all actor movement. It:
    1. Gets the actor's current position
    2. Resolves the movement target to coordinates
    3. Updates the spatial system
    4. Syncs the pygame map
    
    Args:
        actor_name: Name of the actor to move
        movement_target: Target description (obstacle name, direction, narrative phrase)
        narrative: Full narrative for context extraction
        session_id: Optional session ID for spatial manager
        
    Returns:
        True if movement succeeded, False otherwise
    """
    try:
        from spatial_context_system import get_spatial_manager, Position
        
        spatial = get_spatial_manager(session_id=session_id)
        context = spatial.get_current_context()
        
        if not context:
            return False
        
        actor_name_lower = str(actor_name or '').strip().lower()

        # Resolve actor_id from spatial context by name first.
        # This supports UUID-based actor_ids (e.g., nua_<uuid>) and avoids accidentally moving UA.
        actor_id = None
        current_pos = None
        try:
            for aid, apos in (getattr(context, 'actor_positions', {}) or {}).items():
                try:
                    nm = str(getattr(apos, 'actor_name', '') or '').strip().lower()
                except Exception:
                    nm = ''
                if nm and actor_name_lower and nm == actor_name_lower:
                    try:
                        is_ua = bool(getattr(apos, 'is_user_actor', False))
                    except Exception:
                        is_ua = False
                    # Prefer non-UA match unless we're explicitly moving UA
                    if actor_id is None or (not is_ua):
                        actor_id = str(aid)
                        current_pos = getattr(apos, 'position', None)
                        if current_pos and (not is_ua):
                            break
        except Exception:
            actor_id = None
            current_pos = None

        # Fallback: conventional ids (but do NOT try ua_001 unless actor_name matches UA)
        if not actor_id or not current_pos:
            actor_name_key = actor_name_lower.replace(' ', '_')
            possible_ids = []
            try:
                ua_pos = spatial.get_actor_position('ua_001')
                if ua_pos:
                    ua_name = str(getattr(ua_pos, 'actor_name', '') or '').strip().lower()
                else:
                    ua_name = ''
            except Exception:
                ua_name = ''

            if actor_name_lower and ua_name and actor_name_lower == ua_name:
                possible_ids.append('ua_001')
            possible_ids.extend([
                f"nua_{actor_name_key}",
                f"mnua_{actor_name_key}",
                f"actor_{actor_name_key}",
            ])
        
            for pid in possible_ids:
                pos = spatial.get_actor_position(pid)
                if pos:
                    actor_id = pid
                    current_pos = pos
                    break
        
        if not actor_id or not current_pos:
            # Actor not on map yet
            return False
        
        # Resolve movement target using Architect
        resolved = resolve_movement_target(
            target=movement_target,
            current_position=(current_pos.x, current_pos.y),
            spatial_context=context,
            user_input=narrative or movement_target
        )
        
        if resolved:
            new_position = Position(resolved[0], resolved[1])

            # CHECK: Skip movement if already at target (within 1 unit tolerance)
            # This prevents redundant 0m moves when movement is called multiple times
            try:
                import math
                distance = math.sqrt(
                    (new_position.x - current_pos.x)**2 +
                    (new_position.y - current_pos.y)**2
                )
                if distance < 1.0:
                    # Already at target - skip redundant movement
                    return False
            except Exception:
                pass  # If check fails, proceed with movement anyway

            spatial.move_actor(actor_id, new_position)

            # Sync pygame map to show movement and trail
            try:
                from pygame_spatial_map import auto_sync_map
                auto_sync_map(session_id=session_id)
            except Exception as sync_err:
                print(f"[ARCHITECT] Map sync failed: {sync_err}")

            return True

        return False
        
    except Exception as e:
        print(f"[ARCHITECT] Movement failed for {actor_name}: {e}")
        return False


def extract_movement_from_narrative(narrative: str) -> Optional[str]:
    """
    Extract movement target from a narrative description.
    
    Looks for movement verbs and extracts the destination.
    
    Args:
        narrative: The narrative text to parse
        
    Returns:
        Movement target string, or None if no movement detected
    """
    import re
    
    narrative_lower = narrative.lower()
    
    # Movement verb patterns with capture groups for target
    patterns = [
        r'\b(?:walks?|moves?|heads?|goes?|approaches?|steps?)\s+(?:to|toward|towards|over to|up to)\s+(?:the\s+)?([^,.!?]+)',
        r'\b(?:walks?|moves?|heads?|goes?)\s+(?:the\s+)?([^,.!?]+)',
        r'\bapproaches?\s+(?:the\s+)?([^,.!?]+)',
        r'\b(?:crosses?|enters?)\s+(?:to\s+)?(?:the\s+)?([^,.!?]+)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, narrative_lower)
        if match:
            target = match.group(1).strip()
            # Clean up common suffixes
            target = re.sub(r'\s+(and|then|before|after|while).*$', '', target)
            if len(target) > 2:
                return target
    
    # Check for spatial keywords directly
    for keyword in SPATIAL_KEYWORDS.keys():
        if keyword in narrative_lower:
            return keyword
    
    return None
