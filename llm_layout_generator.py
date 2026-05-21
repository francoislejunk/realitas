"""
LLM-Based Layout Generator

Uses a vision-capable LLM to generate realistic room layouts based on:
1. Scene description and context
2. Concrete examples of good layouts
3. Interior design principles

This replaces the purely algorithmic layout_generator.py with intelligent
spatial understanding.
"""

import json
import random
import base64
import os
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from openrouter_config import OpenRouterConfig, RetryConfig, robust_llm_call

from spatial_context_system import DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT


# ═══════════════════════════════════════════════════════════════════════════════
# EXTERIOR LOCATION DETECTION (shared utility function)
# ═══════════════════════════════════════════════════════════════════════════════

EXTERIOR_KEYWORDS = [
    'street', 'alley', 'road', 'avenue', 'boulevard', 'lane',
    'rooftop', 'roof', 'terrace', 'balcony',
    'park', 'plaza', 'square', 'courtyard', 'garden',
    'parking', 'lot', 'garage',  # outdoor parking
    'dock', 'pier', 'wharf', 'harbor',
    'market', 'bazaar',  # outdoor markets
    'exterior', 'outside', 'outdoor'
]

def is_exterior_location(location_name: str, location_type: str = "") -> bool:
    """
    Detect if a location is an exterior/outdoor space.
    
    This is the canonical function for exterior detection - use this everywhere.
    
    Args:
        location_name: Name of the location (e.g., "Main Street", "Back Alley")
        location_type: Optional type hint (e.g., "exterior", "interior")
    
    Returns:
        True if the location is outdoors, False if indoors
    """
    name_lower = location_name.lower() if location_name else ""
    type_lower = location_type.lower() if location_type else ""
    
    # Check location type first
    if type_lower in ['exterior', 'outdoor', 'street', 'alley']:
        return True
    
    # Check location name for keywords
    for keyword in EXTERIOR_KEYWORDS:
        if keyword in name_lower:
            return True
    
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# REFERENCE IMAGES FOR VISION-BASED LAYOUT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

# Directory for reference layout images
REFERENCE_IMAGES_DIR = Path(__file__).parent / "layout_references"

def get_reference_images() -> List[Dict]:
    """
    Load reference layout images for vision-based generation.
    
    Returns list of dicts with 'type', 'image_url' for OpenAI vision format.
    Images should be in the layout_references/ directory.
    """
    images = []
    
    if not REFERENCE_IMAGES_DIR.exists():
        # Create directory and return empty (will use text examples)
        REFERENCE_IMAGES_DIR.mkdir(exist_ok=True)
        return images
    
    # Supported image formats
    supported_formats = {'.png', '.jpg', '.jpeg', '.gif', '.webp'}
    
    for img_path in REFERENCE_IMAGES_DIR.iterdir():
        if img_path.suffix.lower() in supported_formats:
            try:
                with open(img_path, 'rb') as f:
                    img_data = base64.b64encode(f.read()).decode('utf-8')
                
                # Determine media type
                media_type = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif',
                    '.webp': 'image/webp'
                }.get(img_path.suffix.lower(), 'image/png')
                
                images.append({
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:{media_type};base64,{img_data}",
                        "detail": "low"  # Use low detail to save tokens
                    }
                })
                print(f"[LLM_LAYOUT] Loaded reference image: {img_path.name}")
                
            except Exception as e:
                print(f"[LLM_LAYOUT] Failed to load {img_path.name}: {e}")
    
    return images


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES (compatible with existing layout_generator.py)
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GeneratedRoom:
    """A generated room with position and connections"""
    room_id: str
    name: str
    x: float
    y: float
    width: float
    height: float
    connections: List[str] = field(default_factory=list)
    door_positions: List[Tuple[float, float]] = field(default_factory=list)
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def polygon(self) -> List[Tuple[float, float]]:
        return [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height)
        ]


@dataclass
class GeneratedWall:
    """A wall segment"""
    wall_id: str
    start: Tuple[float, float]
    end: Tuple[float, float]
    room_a: str
    room_b: Optional[str]
    has_door: bool = False
    door_position: float = 0.5


@dataclass
class GeneratedObstacle:
    """A furniture/obstacle piece"""
    obstacle_id: str
    name: str
    x: float
    y: float
    width: float
    height: float
    obstacle_type: str = "furniture"


@dataclass
class GeneratedLayout:
    """Complete generated layout"""
    width: float
    height: float
    rooms: Dict[str, GeneratedRoom] = field(default_factory=dict)
    walls: List[GeneratedWall] = field(default_factory=list)
    obstacles: List[GeneratedObstacle] = field(default_factory=list)
    
    def get_zone_polygons(self) -> Dict[str, List[Tuple[float, float]]]:
        return {room_id: room.polygon for room_id, room in self.rooms.items()}
    
    def get_door_positions(self) -> List[Tuple[float, float]]:
        positions = []
        for wall in self.walls:
            if wall.has_door:
                dx = wall.end[0] - wall.start[0]
                dy = wall.end[1] - wall.start[1]
                door_x = wall.start[0] + dx * wall.door_position
                door_y = wall.start[1] + dy * wall.door_position
                positions.append((door_x, door_y))
        return positions


# ═══════════════════════════════════════════════════════════════════════════════
# LAYOUT EXAMPLES - Concrete examples for the LLM to learn from
# ═══════════════════════════════════════════════════════════════════════════════

LAYOUT_EXAMPLES = """
## EXAMPLE 1: Small Office (250x200 units)
Scene: "A cramped audit cubicle with fluorescent lighting"

```json
{
  "rooms": [
    {
      "id": "main_area",
      "name": "Audit Cubicle",
      "x": 10, "y": 10,
      "width": 230, "height": 180
    }
  ],
  "walls": [
    {"id": "north_wall", "start": [10, 190], "end": [240, 190], "has_door": false},
    {"id": "south_wall", "start": [10, 10], "end": [240, 10], "has_door": true, "door_position": 0.5},
    {"id": "east_wall", "start": [240, 10], "end": [240, 190], "has_door": false},
    {"id": "west_wall", "start": [10, 10], "end": [10, 190], "has_door": false}
  ],
  "furniture": [
    {"name": "L-Shaped Desk", "x": 180, "y": 150, "width": 50, "height": 35, "type": "furniture"},
    {"name": "Office Chair", "x": 160, "y": 140, "width": 12, "height": 12, "type": "furniture"},
    {"name": "Filing Cabinet", "x": 30, "y": 160, "width": 20, "height": 15, "type": "furniture"},
    {"name": "Filing Cabinet", "x": 55, "y": 160, "width": 20, "height": 15, "type": "furniture"},
    {"name": "Visitor Chair", "x": 140, "y": 100, "width": 12, "height": 12, "type": "furniture"},
    {"name": "Bookshelf", "x": 30, "y": 80, "width": 25, "height": 60, "type": "furniture"},
    {"name": "Coat Rack", "x": 220, "y": 30, "width": 8, "height": 8, "type": "decoration"},
    {"name": "Potted Plant", "x": 220, "y": 170, "width": 10, "height": 10, "type": "decoration"},
    {"name": "Waste Bin", "x": 200, "y": 130, "width": 8, "height": 8, "type": "decoration"}
  ]
}
```

Key principles applied:
- Desk against back-right corner (typical office layout)
- Filing cabinets along back wall
- Clear pathway from door to desk
- Visitor chair facing desk
- Decorations in corners

## EXAMPLE 2: Diner Interior (250x200 units)
Scene: "A classic 1960s diner with a long counter and booths"

```json
{
  "rooms": [
    {
      "id": "main_floor",
      "name": "Dining Area",
      "x": 10, "y": 10,
      "width": 180, "height": 180
    },
    {
      "id": "kitchen",
      "name": "Kitchen",
      "x": 190, "y": 80,
      "width": 50, "height": 110
    }
  ],
  "walls": [
    {"id": "exterior_south", "start": [10, 10], "end": [240, 10], "has_door": true, "door_position": 0.3},
    {"id": "exterior_west", "start": [10, 10], "end": [10, 190], "has_door": false},
    {"id": "exterior_north", "start": [10, 190], "end": [240, 190], "has_door": false},
    {"id": "exterior_east", "start": [240, 10], "end": [240, 190], "has_door": false},
    {"id": "kitchen_wall", "start": [190, 80], "end": [190, 190], "has_door": true, "door_position": 0.2}
  ],
  "furniture": [
    {"name": "Counter", "x": 140, "y": 130, "width": 80, "height": 15, "type": "furniture"},
    {"name": "Counter Stool", "x": 110, "y": 115, "width": 8, "height": 8, "type": "furniture"},
    {"name": "Counter Stool", "x": 125, "y": 115, "width": 8, "height": 8, "type": "furniture"},
    {"name": "Counter Stool", "x": 140, "y": 115, "width": 8, "height": 8, "type": "furniture"},
    {"name": "Counter Stool", "x": 155, "y": 115, "width": 8, "height": 8, "type": "furniture"},
    {"name": "Counter Stool", "x": 170, "y": 115, "width": 8, "height": 8, "type": "furniture"},
    {"name": "Booth", "x": 30, "y": 160, "width": 35, "height": 25, "type": "furniture"},
    {"name": "Booth", "x": 75, "y": 160, "width": 35, "height": 25, "type": "furniture"},
    {"name": "Booth", "x": 30, "y": 50, "width": 35, "height": 25, "type": "furniture"},
    {"name": "Booth", "x": 75, "y": 50, "width": 35, "height": 25, "type": "furniture"},
    {"name": "Jukebox", "x": 25, "y": 100, "width": 15, "height": 20, "type": "equipment"},
    {"name": "Cash Register", "x": 175, "y": 145, "width": 12, "height": 10, "type": "equipment"},
    {"name": "Pie Display", "x": 160, "y": 145, "width": 15, "height": 10, "type": "decoration"}
  ]
}
```

Key principles applied:
- Counter runs horizontally, stools in front
- Booths along walls (left side)
- Clear aisle down the center
- Kitchen separated by wall with service door
- Jukebox against wall, not blocking traffic

## EXAMPLE 3: Warehouse (250x200 units)
Scene: "An industrial warehouse with loading docks"

```json
{
  "rooms": [
    {
      "id": "main_floor",
      "name": "Warehouse Floor",
      "x": 10, "y": 10,
      "width": 200, "height": 180
    },
    {
      "id": "office",
      "name": "Foreman Office",
      "x": 210, "y": 130,
      "width": 30, "height": 60
    }
  ],
  "walls": [
    {"id": "loading_dock", "start": [10, 10], "end": [210, 10], "has_door": true, "door_position": 0.5},
    {"id": "office_wall", "start": [210, 130], "end": [210, 190], "has_door": true, "door_position": 0.5}
  ],
  "furniture": [
    {"name": "Pallet Rack", "x": 40, "y": 160, "width": 50, "height": 20, "type": "furniture"},
    {"name": "Pallet Rack", "x": 100, "y": 160, "width": 50, "height": 20, "type": "furniture"},
    {"name": "Pallet Rack", "x": 160, "y": 160, "width": 40, "height": 20, "type": "furniture"},
    {"name": "Pallet Rack", "x": 40, "y": 100, "width": 50, "height": 20, "type": "furniture"},
    {"name": "Pallet Rack", "x": 100, "y": 100, "width": 50, "height": 20, "type": "furniture"},
    {"name": "Forklift", "x": 180, "y": 50, "width": 20, "height": 30, "type": "vehicle"},
    {"name": "Shipping Crates", "x": 50, "y": 40, "width": 30, "height": 25, "type": "container"},
    {"name": "Shipping Crates", "x": 90, "y": 40, "width": 25, "height": 20, "type": "container"},
    {"name": "Work Bench", "x": 220, "y": 50, "width": 20, "height": 15, "type": "furniture"},
    {"name": "Desk", "x": 220, "y": 160, "width": 15, "height": 12, "type": "furniture"},
    {"name": "Chair", "x": 218, "y": 148, "width": 8, "height": 8, "type": "furniture"}
  ]
}
```

Key principles applied:
- Pallet racks in rows with aisles between
- Loading area near entrance (south)
- Forklift parked near loading area
- Office in corner with own door
- Work bench near office for quick tasks

## EXAMPLE 4: Bedroom (250x200 units)
Scene: "A modest bedroom in a 1960s apartment"

```json
{
  "rooms": [
    {
      "id": "bedroom",
      "name": "Bedroom",
      "x": 10, "y": 10,
      "width": 230, "height": 180
    }
  ],
  "walls": [
    {"id": "north_wall", "start": [10, 190], "end": [240, 190], "has_door": false},
    {"id": "south_wall", "start": [10, 10], "end": [240, 10], "has_door": true, "door_position": 0.8},
    {"id": "east_wall", "start": [240, 10], "end": [240, 190], "has_door": false},
    {"id": "west_wall", "start": [10, 10], "end": [10, 190], "has_door": false}
  ],
  "furniture": [
    {"name": "Double Bed", "x": 70, "y": 160, "width": 50, "height": 60, "type": "furniture"},
    {"name": "Nightstand", "x": 30, "y": 155, "width": 15, "height": 15, "type": "furniture"},
    {"name": "Nightstand", "x": 130, "y": 155, "width": 15, "height": 15, "type": "furniture"},
    {"name": "Wardrobe", "x": 210, "y": 150, "width": 25, "height": 35, "type": "furniture"},
    {"name": "Dresser", "x": 210, "y": 80, "width": 25, "height": 20, "type": "furniture"},
    {"name": "Mirror", "x": 215, "y": 105, "width": 15, "height": 3, "type": "decoration"},
    {"name": "Desk", "x": 30, "y": 60, "width": 30, "height": 18, "type": "furniture"},
    {"name": "Chair", "x": 35, "y": 40, "width": 10, "height": 10, "type": "furniture"},
    {"name": "Lamp", "x": 32, "y": 168, "width": 6, "height": 6, "type": "decoration"},
    {"name": "Rug", "x": 70, "y": 90, "width": 40, "height": 30, "type": "decoration"}
  ]
}
```

Key principles applied:
- Bed against back wall, centered or offset
- Nightstands flanking bed
- Wardrobe against side wall
- Desk in corner for work area
- Clear path from door to bed
"""

# ═══════════════════════════════════════════════════════════════════════════════
# EXTERIOR LAYOUT EXAMPLES (Streets, Alleys, Outdoor Areas)
# ═══════════════════════════════════════════════════════════════════════════════

EXTERIOR_LAYOUT_EXAMPLES = """
## EXAMPLE 1: Back Alley (250x200 units)
Scene: "A narrow back alley between two buildings, dimly lit with scattered debris"

```json
{
  "rooms": [
    {
      "id": "alley",
      "name": "Back Alley",
      "x": 10, "y": 10,
      "width": 230, "height": 180
    }
  ],
  "walls": [
    {"id": "building_west", "start": [10, 10], "end": [10, 190], "has_door": true, "door_position": 0.3},
    {"id": "building_east", "start": [240, 10], "end": [240, 190], "has_door": true, "door_position": 0.7}
  ],
  "furniture": [
    {"name": "Dumpster", "x": 30, "y": 160, "width": 35, "height": 25, "type": "container"},
    {"name": "Trash Bags", "x": 70, "y": 165, "width": 15, "height": 12, "type": "debris"},
    {"name": "Wooden Crates", "x": 200, "y": 50, "width": 25, "height": 20, "type": "container"},
    {"name": "Cardboard Boxes", "x": 210, "y": 80, "width": 18, "height": 15, "type": "debris"},
    {"name": "Fire Escape Ladder", "x": 25, "y": 80, "width": 10, "height": 40, "type": "structure"},
    {"name": "Puddle", "x": 120, "y": 100, "width": 30, "height": 20, "type": "terrain"},
    {"name": "Broken Pipe", "x": 35, "y": 120, "width": 8, "height": 25, "type": "debris"},
    {"name": "Streetlight", "x": 125, "y": 25, "width": 8, "height": 8, "type": "lighting"},
    {"name": "Manhole Cover", "x": 125, "y": 150, "width": 15, "height": 15, "type": "structure"}
  ]
}
```

Key principles applied:
- Walls represent building facades on sides (not enclosed)
- Dumpsters and debris along walls
- Clear path down center for movement
- Streetlight for atmosphere
- Urban debris scattered realistically

## EXAMPLE 2: City Street (250x200 units)
Scene: "A busy city street with storefronts and pedestrian traffic"

```json
{
  "rooms": [
    {
      "id": "street",
      "name": "City Street",
      "x": 10, "y": 10,
      "width": 230, "height": 180
    }
  ],
  "walls": [
    {"id": "storefronts_north", "start": [10, 190], "end": [240, 190], "has_door": true, "door_position": 0.3},
    {"id": "storefronts_south", "start": [10, 10], "end": [240, 10], "has_door": true, "door_position": 0.6}
  ],
  "furniture": [
    {"name": "Street Lamp", "x": 50, "y": 30, "width": 8, "height": 8, "type": "lighting"},
    {"name": "Street Lamp", "x": 150, "y": 30, "width": 8, "height": 8, "type": "lighting"},
    {"name": "Street Lamp", "x": 50, "y": 170, "width": 8, "height": 8, "type": "lighting"},
    {"name": "Street Lamp", "x": 150, "y": 170, "width": 8, "height": 8, "type": "lighting"},
    {"name": "Bench", "x": 80, "y": 165, "width": 25, "height": 10, "type": "furniture"},
    {"name": "Trash Can", "x": 110, "y": 168, "width": 10, "height": 10, "type": "container"},
    {"name": "Newsstand", "x": 200, "y": 25, "width": 20, "height": 15, "type": "structure"},
    {"name": "Phone Booth", "x": 30, "y": 165, "width": 12, "height": 12, "type": "structure"},
    {"name": "Fire Hydrant", "x": 180, "y": 170, "width": 8, "height": 8, "type": "structure"},
    {"name": "Parked Car", "x": 125, "y": 80, "width": 40, "height": 20, "type": "vehicle"},
    {"name": "Parked Car", "x": 125, "y": 120, "width": 40, "height": 20, "type": "vehicle"}
  ]
}
```

Key principles applied:
- Walls represent building facades (storefronts)
- Street furniture along sidewalks (benches, lamps, hydrants)
- Parked cars in road area (center)
- Clear pedestrian paths along edges
- Urban amenities (newsstand, phone booth)

## EXAMPLE 3: Rooftop (250x200 units)
Scene: "A flat rooftop with HVAC units and a water tower"

```json
{
  "rooms": [
    {
      "id": "rooftop",
      "name": "Rooftop",
      "x": 10, "y": 10,
      "width": 230, "height": 180
    }
  ],
  "walls": [
    {"id": "parapet_north", "start": [10, 190], "end": [240, 190], "has_door": false},
    {"id": "parapet_south", "start": [10, 10], "end": [240, 10], "has_door": false},
    {"id": "parapet_east", "start": [240, 10], "end": [240, 190], "has_door": false},
    {"id": "parapet_west", "start": [10, 10], "end": [10, 190], "has_door": false}
  ],
  "furniture": [
    {"name": "HVAC Unit", "x": 180, "y": 150, "width": 40, "height": 30, "type": "equipment"},
    {"name": "HVAC Unit", "x": 180, "y": 50, "width": 35, "height": 25, "type": "equipment"},
    {"name": "Water Tower", "x": 50, "y": 140, "width": 35, "height": 35, "type": "structure"},
    {"name": "Roof Access Door", "x": 30, "y": 30, "width": 20, "height": 25, "type": "structure"},
    {"name": "Ventilation Shaft", "x": 100, "y": 160, "width": 15, "height": 15, "type": "equipment"},
    {"name": "Antenna Array", "x": 210, "y": 100, "width": 12, "height": 12, "type": "equipment"},
    {"name": "Pigeon Coop", "x": 120, "y": 40, "width": 20, "height": 15, "type": "structure"},
    {"name": "Tarp-Covered Crates", "x": 60, "y": 80, "width": 25, "height": 20, "type": "container"}
  ]
}
```

Key principles applied:
- Parapet walls on all sides (low walls, no doors)
- HVAC equipment in corners
- Water tower as major landmark
- Roof access structure
- Open center area for movement
"""

# ═══════════════════════════════════════════════════════════════════════════════
# EXTERIOR DESIGN PRINCIPLES
# ═══════════════════════════════════════════════════════════════════════════════

EXTERIOR_DESIGN_PRINCIPLES = """
## EXTERIOR LAYOUT PRINCIPLES FOR REALISTIC OUTDOOR SPACES

### 1. OUTDOOR ELEMENT PLACEMENT
- **Along Edges**: Street furniture (lamps, benches, hydrants) along building facades
- **Scattered Debris**: Trash, crates, puddles placed organically, not in rows
- **Clear Pathways**: Main walking/driving areas in center
- **Landmarks**: Large items (dumpsters, vehicles, structures) as reference points

### 2. STREET/ALLEY FLOW
- **Sidewalks**: 30-50 units along building edges
- **Road/Path**: Center area for vehicles or main foot traffic
- **Obstacles**: Debris and objects should NOT block the main path entirely

### 3. SCALE GUIDELINES (for 250x200 unit outdoor areas)
- **Small items** (trash cans, hydrants, lamps): 8-15 units
- **Medium items** (benches, crates, phone booths): 15-30 units
- **Large items** (dumpsters, vehicles, structures): 30-50 units
- **Edge margin**: Keep 10-20 units from map edges

### 4. EXTERIOR-SPECIFIC ELEMENTS
- **Lighting**: Streetlights, neon signs, building lights
- **Urban debris**: Trash bags, cardboard, puddles, broken items
- **Structures**: Fire escapes, phone booths, newsstands, bus stops
- **Vehicles**: Parked cars, motorcycles, delivery trucks
- **Terrain**: Puddles, grates, manhole covers, curbs

### 5. WALLS IN EXTERIOR SPACES
- Walls represent BUILDING FACADES, not enclosed rooms
- Alleys: walls on 2 sides (buildings on left and right)
- Streets: walls on 2 sides (storefronts on north and south)
- Rooftops: low parapet walls on all 4 sides
- Parks: may have NO walls (open space)

### 6. COORDINATE SYSTEM
- Origin (0,0) is TOP-LEFT of the map
- X increases going RIGHT
- Y increases going DOWN
"""


# ═══════════════════════════════════════════════════════════════════════════════
# INTERIOR DESIGN PRINCIPLES
# ═══════════════════════════════════════════════════════════════════════════════

DESIGN_PRINCIPLES = """
## INTERIOR DESIGN PRINCIPLES FOR REALISTIC LAYOUTS

### 1. FURNITURE PLACEMENT RULES
- **Against Walls**: Large furniture (beds, desks, wardrobes, counters) should be against walls
- **Clear Pathways**: Always leave walking space (at least 30 units) from door to key areas
- **Functional Groupings**: Related items together (bed + nightstands, desk + chair)
- **Corner Usage**: Corners are good for storage, plants, lamps, waste bins

### 2. ROOM FLOW
- **Entry Zone**: Keep area near door clear (30-50 units)
- **Activity Zones**: Group furniture by function
- **Traffic Lanes**: Main paths should be 30-50 units wide
- **Dead Zones**: Corners and edges for storage/decoration

### 3. SCALE GUIDELINES (for 250x200 unit rooms)
- **Small furniture** (chairs, stools, lamps): 8-15 units
- **Medium furniture** (desks, nightstands): 15-30 units
- **Large furniture** (beds, counters, wardrobes): 30-60 units
- **Wall margin**: Keep furniture 10-20 units from walls (not flush)

### 4. COMMON MISTAKES TO AVOID
- ❌ Furniture floating in center of room
- ❌ Blocking the entrance/door
- ❌ Items overlapping each other
- ❌ No clear walking paths
- ❌ Everything in a straight line
- ❌ Ignoring corners (they should have something)

### 5. COORDINATE SYSTEM
- Origin (0,0) is TOP-LEFT of the map
- X increases going RIGHT
- Y increases going DOWN
"""


# ═══════════════════════════════════════════════════════════════════════════════
# LLM LAYOUT GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class LLMLayoutGenerator:
    """
    Uses an LLM to generate realistic room layouts.
    
    The LLM receives:
    1. Scene description and context
    2. Concrete examples of good layouts
    3. Interior design principles
    4. Output format specification
    
    And returns a structured JSON layout.
    """
    
    def __init__(self, width: float = DEFAULT_MAP_WIDTH, height: float = DEFAULT_MAP_HEIGHT, use_vision: bool = True):
        self.width = width
        self.height = height
        self.client = OpenRouterConfig.create_client()
        self.use_vision = use_vision
        
        # Use role-based model selection for layout generation
        # This allows easy configuration changes in openrouter_config.py
        self.model = OpenRouterConfig.get_model_for_role("layout_generation")
        
        # Load reference images for vision-based generation
        self.reference_images = []
        if use_vision:
            self.reference_images = get_reference_images()
            if self.reference_images:
                print(f"[LLM_LAYOUT] Loaded {len(self.reference_images)} reference images for vision")
        
        print(f"[LLM_LAYOUT] Initialized with model: {self.model} (vision: {use_vision and len(self.reference_images) > 0})")
    
    def generate(self, 
                 scene_description: str,
                 location_name: str,
                 location_type: str = "interior",
                 zone_names: List[str] = None) -> GeneratedLayout:
        """
        Generate a layout using LLM.
        
        Args:
            scene_description: Narrative description of the space
            location_name: Name of the location
            location_type: Type (interior, exterior, etc.)
            zone_names: Optional list of zone/room names
            
        Returns:
            GeneratedLayout with rooms, walls, and furniture
        """
        # Detect exterior vs interior
        is_exterior = self._is_exterior_location(location_name, location_type)
        if is_exterior:
            print(f"[LLM_LAYOUT] 🌆 EXTERIOR location detected: {location_name}")
        else:
            print(f"[LLM_LAYOUT] 🏠 INTERIOR location: {location_name}")
        
        prompt = self._build_prompt(scene_description, location_name, location_type, zone_names)
        
        try:
            # Build message content - with or without images
            if self.use_vision and self.reference_images:
                # Vision-based: include reference images
                content = self._build_vision_content(prompt)
                messages = [{"role": "user", "content": content}]
            else:
                # Text-only
                messages = [{"role": "user", "content": prompt}]
            
            response = robust_llm_call(
                client=self.client,
                messages=messages,
                model=self.model,
                temperature=0.3,  # Lower for more consistent layouts
                max_tokens=4000,
                max_retries=3,
                call_name="LAYOUT_GENERATION"
            )
            
            # Parse the JSON response
            layout_data = self._parse_response(response)
            
            # Convert to GeneratedLayout
            return self._build_layout(layout_data)
            
        except Exception as e:
            print(f"[LLM_LAYOUT] Error generating layout: {e}")
            # Fall back to simple layout
            return self._fallback_layout(location_name)
    
    def _is_exterior_location(self, location_name: str, location_type: str) -> bool:
        """Detect if this is an exterior/outdoor location. Uses shared utility function."""
        return is_exterior_location(location_name, location_type)
    
    def _build_prompt(self, 
                      scene_description: str,
                      location_name: str,
                      location_type: str,
                      zone_names: List[str]) -> str:
        """Build the prompt for layout generation."""
        
        zones_str = ""
        if zone_names:
            zones_str = f"\nZones/Areas to include: {', '.join(zone_names)}"
        
        # Detect if this is an exterior location
        is_exterior = self._is_exterior_location(location_name, location_type)
        
        if is_exterior:
            return self._build_exterior_prompt(scene_description, location_name, location_type, zones_str)
        else:
            return self._build_interior_prompt(scene_description, location_name, location_type, zones_str)
    
    def _build_interior_prompt(self, scene_description: str, location_name: str, 
                                location_type: str, zones_str: str) -> str:
        """Build prompt for interior locations."""
        min_dim = max(1.0, min(float(self.width), float(self.height)))
        edge_margin = max(0.8, min(4.0, min_dim * 0.10))
        near_wall_band = max(1.2, min(6.0, min_dim * 0.18))
        entry_clearance = max(1.5, min(6.0, min_dim * 0.22))
        return f"""You are an interior designer and spatial layout expert. Generate a realistic room layout for a simulation.

## LOCATION DETAILS
- **Name**: {location_name}
- **Type**: {location_type}
- **Dimensions**: {self.width} x {self.height} units
- **Description**: {scene_description}
{zones_str}

IMPORTANT: 1 unit = 1 meter. All width/height values must be physically plausible.

{DESIGN_PRINCIPLES}

## EXAMPLE LAYOUTS
{LAYOUT_EXAMPLES}

## YOUR TASK
Generate a realistic layout for "{location_name}" based on the description. 

**CRITICAL: EXTRACT OBJECTS FROM SCENE DESCRIPTION**
The scene description mentions specific objects, furniture, and environmental details. You MUST:
1. **IDENTIFY** all concrete objects mentioned in the description (terminals, desks, storage, equipment, etc.)
2. **INCLUDE** these specific objects in your furniture list - don't just use generic furniture
3. **MATCH** the scene's atmosphere - if it mentions "cramped back office", make it feel cramped with appropriate furniture density

For example, if the description mentions:
- "audit terminal" → Include "Audit Terminal" as furniture
- "refrigerated storage drawer" → Include "Refrigerated Storage Unit" as furniture  
- "HEM canisters" → Include "HEM Canister Rack" or "Discarded HEM Canisters" as furniture
- "biometric lock" → The storage unit should exist for the lock to be on

**CRITICAL REQUIREMENTS:**
1. **WALL MARGIN (dynamic)**: All furniture must be FULLY inside the room.
   - Minimum X is {edge_margin:.1f} and maximum is {max(edge_margin, float(self.width) - edge_margin):.1f}
   - Minimum Y is {edge_margin:.1f} and maximum is {max(edge_margin, float(self.height) - edge_margin):.1f}
   Interpret furniture `x,y` as the TOP-LEFT corner of the item rectangle.
2. **SIZE LIMITS (meters)**: Keep object sizes physically plausible.
   - Debris (bones, rubble, broken stone): usually 1-3m, rarely up to 4m (never room-filling)
   - Small items (chairs, crates, bins, stools): 0.6-1.5m
   - Medium items (tables, desks, terminals, cabinets): 1.2-3.0m
   - Large items (beds, counters, shelves, racks): 2.0-4.5m
   - Doors/portals: ~1.0m wide, 0.2-0.6m deep
   - No single object should exceed ~25% of the room width/height.
3. Furniture must NOT overlap (check positions AND sizes - item at x=50 with width=30 extends to x=80)
4. Leave clear pathways from entrance to key areas
5. **INCLUDE ALL OBJECTS MENTIONED IN THE SCENE DESCRIPTION** - this is the most important rule!
6. **FURNITURE PLACEMENT:**
   - Wall furniture (desks, beds, shelves): Place with X in [{edge_margin:.1f}..{(edge_margin + near_wall_band):.1f}] OR X in [{max(edge_margin, float(self.width) - edge_margin - near_wall_band):.1f}..{max(edge_margin, float(self.width) - edge_margin):.1f}] for wall-adjacent placement
   - Keep the entrance/exit approach clear: reserve at least {entry_clearance:.1f}m of open space around the main door/exit area
   - DISTRIBUTE furniture across the ENTIRE room (use multiple corners/edges)
   - Leave walking paths between furniture groups
7. Include 6-10 furniture pieces for a lived-in feel
8. Use the coordinate system: (0,0) is TOP-LEFT, Y increases DOWNWARD

**OUTPUT FORMAT:**
Return ONLY valid JSON in this exact format:
```json
{{
  "rooms": [
    {{"id": "room_id", "name": "Room Name", "x": 10, "y": 10, "width": 230, "height": 180}}
  ],
  "walls": [
    {{"id": "wall_id", "start": [x1, y1], "end": [x2, y2], "has_door": true, "door_position": 0.5}}
  ],
  "furniture": [
    {{"name": "Item Name", "x": 100, "y": 150, "width": 30, "height": 20, "type": "furniture"}}
  ]
}}
```

Generate the layout now:"""

    def _build_exterior_prompt(self, scene_description: str, location_name: str,
                                location_type: str, zones_str: str) -> str:
        """Build prompt for exterior/outdoor locations."""
        min_dim = max(1.0, min(float(self.width), float(self.height)))
        edge_margin = max(0.8, min(6.0, min_dim * 0.10))
        return f"""You are an urban planner and outdoor space designer. Generate a realistic EXTERIOR layout for a simulation.

## LOCATION DETAILS
- **Name**: {location_name}
- **Type**: {location_type} (OUTDOOR/EXTERIOR)
- **Dimensions**: {self.width} x {self.height} units
- **Description**: {scene_description}
{zones_str}

{EXTERIOR_DESIGN_PRINCIPLES}

## EXAMPLE EXTERIOR LAYOUTS
{EXTERIOR_LAYOUT_EXAMPLES}

## YOUR TASK
Generate a realistic OUTDOOR layout for "{location_name}" based on the description.

**CRITICAL REQUIREMENTS FOR EXTERIOR SPACES:**
1. All coordinates must be within bounds ({edge_margin:.1f} to {max(edge_margin, float(self.width) - edge_margin):.1f} for X, {edge_margin:.1f} to {max(edge_margin, float(self.height) - edge_margin):.1f} for Y)
2. Objects must NOT overlap (check positions and sizes)
3. **THIS IS AN OUTDOOR SPACE - NOT AN ENCLOSED ROOM:**
   - Walls represent BUILDING FACADES or boundaries, NOT enclosed rooms
   - For streets/alleys: walls on 2 sides only (buildings on left/right OR north/south)
   - For rooftops: low parapet walls on all 4 sides
   - For parks/plazas: minimal or NO walls
4. **OUTDOOR ELEMENT PLACEMENT:**
   - DUMPSTERS, CRATES, DEBRIS → Along building walls/edges
   - STREETLIGHTS, BENCHES, HYDRANTS → Along sidewalk areas (near edges)
   - VEHICLES → In road/parking areas (center for streets)
   - PUDDLES, MANHOLES, GRATES → Scattered in walkable areas
   - Keep CENTER relatively clear for main foot/vehicle traffic
5. Include 6-12 outdoor elements for a realistic urban feel
6. Use the coordinate system: (0,0) is TOP-LEFT, Y increases DOWNWARD

**OUTPUT FORMAT:**
Return ONLY valid JSON in this exact format:
```json
{{
  "rooms": [
    {{"id": "area_id", "name": "Area Name", "x": 10, "y": 10, "width": 230, "height": 180}}
  ],
  "walls": [
    {{"id": "wall_id", "start": [x1, y1], "end": [x2, y2], "has_door": true, "door_position": 0.5}}
  ],
  "furniture": [
    {{"name": "Dumpster", "x": 30, "y": 160, "width": 35, "height": 25, "type": "container"}},
    {{"name": "Streetlight", "x": 125, "y": 25, "width": 8, "height": 8, "type": "lighting"}}
  ]
}}
```

Generate the EXTERIOR layout now:"""
    
    def _build_vision_content(self, text_prompt: str) -> List[Dict]:
        """
        Build vision-enabled content with reference images.
        
        Returns a list of content items for the OpenAI vision API format:
        [
            {"type": "text", "text": "..."},
            {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}},
            ...
        ]
        """
        content = []
        
        # Add instruction about the reference images
        intro = """I'm providing reference images of GOOD room layouts. Study these examples:
- Notice how furniture is placed AGAINST WALLS, not floating in the center
- Notice clear PATHWAYS from doors to key areas
- Notice FUNCTIONAL GROUPINGS (desk+chair, bed+nightstand)
- Notice how CORNERS are used for storage/decoration

After studying these examples, generate a layout following the same principles.

"""
        
        # Add reference images first
        for img in self.reference_images:
            content.append(img)
        
        # Add the main prompt with intro
        content.append({
            "type": "text",
            "text": intro + text_prompt
        })
        
        return content
    
    def _parse_response(self, response: str) -> Dict:
        """Parse the LLM response to extract JSON."""
        import re
        
        # Try to find JSON in the response
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Try to find raw JSON
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                raise ValueError("No JSON found in response")
        
        return json.loads(json_str)
    
    def _build_layout(self, data: Dict) -> GeneratedLayout:
        """Convert parsed JSON to GeneratedLayout."""
        layout = GeneratedLayout(width=self.width, height=self.height)
        
        # Add rooms
        for room_data in data.get("rooms", []):
            room = GeneratedRoom(
                room_id=room_data.get("id", f"room_{len(layout.rooms)+1}"),
                name=room_data.get("name", "Room"),
                x=float(room_data.get("x", 10)),
                y=float(room_data.get("y", 10)),
                width=float(room_data.get("width", self.width - 20)),
                height=float(room_data.get("height", self.height - 20))
            )
            layout.rooms[room.room_id] = room
        
        # If no rooms, create a default one
        if not layout.rooms:
            layout.rooms["main"] = GeneratedRoom(
                room_id="main",
                name="Main Area",
                x=10, y=10,
                width=self.width - 20,
                height=self.height - 20
            )
        
        # Add walls
        for wall_data in data.get("walls", []):
            start = wall_data.get("start", [10, 10])
            end = wall_data.get("end", [self.width - 10, 10])
            
            wall = GeneratedWall(
                wall_id=wall_data.get("id", f"wall_{len(layout.walls)+1}"),
                start=(float(start[0]), float(start[1])),
                end=(float(end[0]), float(end[1])),
                room_a=list(layout.rooms.keys())[0] if layout.rooms else "main",
                room_b=None,
                has_door=wall_data.get("has_door", False),
                door_position=float(wall_data.get("door_position", 0.5))
            )
            layout.walls.append(wall)
        
        # Add default walls if none provided
        if not layout.walls:
            layout.walls = self._create_default_walls(layout)
        
        # Add furniture/obstacles with validation
        for i, furn_data in enumerate(data.get("furniture", [])):
            # Get raw values
            x = float(furn_data.get("x", 50))
            y = float(furn_data.get("y", 50))
            width = float(furn_data.get("width", 15))
            height = float(furn_data.get("height", 15))

            ftype = str(furn_data.get("type", "") or "").lower()
            fname = str(furn_data.get("name", "") or "").lower()

            min_dim = max(1.0, min(float(self.width), float(self.height)))
            frac_cap = max(1.0, min_dim * 0.25)

            min_w = 0.6
            min_h = 0.6
            max_w = frac_cap
            max_h = frac_cap

            if ftype in ["door", "portal", "exit", "entrance"] or any(k in fname for k in ["door", "gate", "exit", "entrance", "hatch", "trapdoor"]):
                min_w, min_h = 0.8, 0.2
                max_w, max_h = min(frac_cap, 1.6), min(frac_cap, 0.8)
            elif ftype in ["debris", "rubble"] or any(k in fname for k in ["bone", "bones", "rubble", "debris", "wreckage", "blocks", "collapsed"]):
                min_w, min_h = 0.8, 0.8
                max_w, max_h = min(frac_cap, 4.0), min(frac_cap, 4.0)
            elif any(k in fname for k in ["chair", "stool", "crate", "barrel", "bin", "box"]):
                min_w, min_h = 0.6, 0.6
                max_w, max_h = min(frac_cap, 1.8), min(frac_cap, 1.8)
            elif any(k in fname for k in ["bed", "bunk", "cot"]):
                min_w, min_h = 1.8, 0.8
                max_w, max_h = min(frac_cap, 3.2), min(frac_cap, 2.2)
            elif any(k in fname for k in ["table", "desk", "terminal", "console", "cabinet", "shelf", "counter", "workbench"]):
                min_w, min_h = 1.2, 0.8
                max_w, max_h = min(frac_cap, 4.5), min(frac_cap, 3.0)

            width = max(min_w, min(width, max_w))
            height = max(min_h, min(height, max_h))
            
            # Clamp positions to stay within walls (with margin for the furniture size)
            margin = max(0.8, min(4.0, min_dim * 0.10))
            max_x = max(margin, float(self.width) - margin - width)
            max_y = max(margin, float(self.height) - margin - height)
            x = max(margin, min(x, max_x))
            y = max(margin, min(y, max_y))
            
            obs = GeneratedObstacle(
                obstacle_id=f"obs_{i+1}",
                name=furn_data.get("name", "Furniture"),
                x=x,
                y=y,
                width=width,
                height=height,
                obstacle_type=furn_data.get("type", "furniture")
            )
            layout.obstacles.append(obs)
        
        return layout
    
    def _create_default_walls(self, layout: GeneratedLayout) -> List[GeneratedWall]:
        """Create default walls around the room."""
        room = list(layout.rooms.values())[0] if layout.rooms else None
        if not room:
            return []
        
        walls = []
        # North wall (top)
        walls.append(GeneratedWall(
            wall_id="wall_north",
            start=(room.x, room.y + room.height),
            end=(room.x + room.width, room.y + room.height),
            room_a=room.room_id,
            room_b=None,
            has_door=False
        ))
        # South wall (bottom) with door
        walls.append(GeneratedWall(
            wall_id="wall_south",
            start=(room.x, room.y),
            end=(room.x + room.width, room.y),
            room_a=room.room_id,
            room_b=None,
            has_door=True,
            door_position=0.5
        ))
        # East wall (right)
        walls.append(GeneratedWall(
            wall_id="wall_east",
            start=(room.x + room.width, room.y),
            end=(room.x + room.width, room.y + room.height),
            room_a=room.room_id,
            room_b=None,
            has_door=False
        ))
        # West wall (left)
        walls.append(GeneratedWall(
            wall_id="wall_west",
            start=(room.x, room.y),
            end=(room.x, room.y + room.height),
            room_a=room.room_id,
            room_b=None,
            has_door=False
        ))
        
        return walls
    
    def _fallback_layout(self, location_name: str) -> GeneratedLayout:
        """Create a simple fallback layout if LLM fails."""
        layout = GeneratedLayout(width=self.width, height=self.height)
        
        # Single room
        room = GeneratedRoom(
            room_id="main",
            name=location_name,
            x=10, y=10,
            width=self.width - 20,
            height=self.height - 20
        )
        layout.rooms["main"] = room
        
        # Default walls
        layout.walls = self._create_default_walls(layout)
        
        # Basic furniture based on common patterns
        furniture = [
            ("Desk", 180, 150, 40, 25),
            ("Chair", 165, 135, 12, 12),
            ("Filing Cabinet", 30, 160, 20, 15),
            ("Bookshelf", 30, 80, 20, 50),
            ("Visitor Chair", 140, 100, 12, 12),
            ("Plant", 220, 170, 10, 10),
            ("Waste Bin", 200, 130, 8, 8),
        ]
        
        for i, (name, x, y, w, h) in enumerate(furniture):
            layout.obstacles.append(GeneratedObstacle(
                obstacle_id=f"obs_{i+1}",
                name=name,
                x=x, y=y,
                width=w, height=h,
                obstacle_type="furniture"
            ))
        
        return layout


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION (drop-in replacement for layout_generator.py)
# ═══════════════════════════════════════════════════════════════════════════════

def generate_layout_for_location_llm(
    zone_names: List[str],
    width: float,
    height: float,
    location_type: str = "interior",
    location_name: str = "Location",
    scene_description: str = ""
) -> GeneratedLayout:
    """
    Generate a layout using LLM (drop-in replacement for generate_layout_for_location).
    
    Args:
        zone_names: List of zone/room names
        width: Location width
        height: Location height
        location_type: Type of location
        location_name: Display name
        scene_description: Narrative description
        
    Returns:
        GeneratedLayout with rooms, walls, and furniture
    """
    generator = LLMLayoutGenerator(width=width, height=height)
    
    # Build description from zone names if not provided
    if not scene_description:
        scene_description = f"A {location_type} space called '{location_name}' containing: {', '.join(zone_names)}"
    
    return generator.generate(
        scene_description=scene_description,
        location_name=location_name,
        location_type=location_type,
        zone_names=zone_names
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Testing LLM Layout Generator...")
    
    # Test with an audit cubicle
    layout = generate_layout_for_location_llm(
        zone_names=["Audit Cubicle"],
        width=DEFAULT_MAP_WIDTH,
        height=DEFAULT_MAP_HEIGHT,
        location_type="office",
        location_name="Audit Cubicle",
        scene_description="A cramped audit cubicle with fluorescent lighting, stacks of paperwork, and a single frosted-glass partition separating it from the hallway."
    )
    
    print(f"\nGenerated layout: {layout.width}x{layout.height}")
    print(f"Rooms: {len(layout.rooms)}")
    for room_id, room in layout.rooms.items():
        print(f"  {room_id}: {room.name} at ({room.x:.1f}, {room.y:.1f}) size {room.width:.1f}x{room.height:.1f}")
    
    print(f"\nWalls: {len(layout.walls)}")
    for wall in layout.walls:
        door_str = " [DOOR]" if wall.has_door else ""
        print(f"  {wall.wall_id}: ({wall.start[0]:.0f},{wall.start[1]:.0f}) -> ({wall.end[0]:.0f},{wall.end[1]:.0f}){door_str}")
    
    print(f"\nFurniture: {len(layout.obstacles)}")
    for obs in layout.obstacles:
        print(f"  {obs.name}: ({obs.x:.0f}, {obs.y:.0f}) size {obs.width:.0f}x{obs.height:.0f}")
    
    print("\n✅ LLM Layout generator test complete!")
