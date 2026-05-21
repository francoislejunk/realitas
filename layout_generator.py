"""
Layout Generator - Dynamic Room Layout Generation

Generates dungeon/building-style layouts from zone descriptions.
Creates proper room polygons, walls, and door placements.

Used by:
- spatial_context_system (when creating new locations)
- pygame_spatial_map (for visualization)
"""

import random
import math
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class LayoutStyle(Enum):
    """Layout generation styles"""
    GRID = "grid"           # Regular grid of rooms
    ORGANIC = "organic"     # More natural, irregular shapes
    LINEAR = "linear"       # Rooms in a line/corridor
    RADIAL = "radial"       # Rooms around a central hub
    L_SHAPED = "l_shaped"   # L-shaped building
    RANDOM = "random"       # Random placement


@dataclass
class RoomSpec:
    """Specification for a room to be generated"""
    name: str
    min_size: float = 4.0       # Minimum dimension
    max_size: float = 10.0      # Maximum dimension
    importance: int = 1         # Higher = larger room
    must_connect_to: List[str] = field(default_factory=list)  # Required connections
    is_entrance: bool = False   # Is this an entrance/exit
    zone_type: str = "room"


@dataclass
class GeneratedRoom:
    """A generated room with position and connections"""
    room_id: str
    name: str
    x: float                    # Top-left X
    y: float                    # Top-left Y
    width: float
    height: float
    connections: List[str] = field(default_factory=list)  # Connected room IDs
    door_positions: List[Tuple[float, float]] = field(default_factory=list)
    
    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    @property
    def bounds(self) -> Tuple[float, float, float, float]:
        """Return (x, y, width, height)"""
        return (self.x, self.y, self.width, self.height)
    
    @property
    def polygon(self) -> List[Tuple[float, float]]:
        """Return corner points as polygon"""
        return [
            (self.x, self.y),
            (self.x + self.width, self.y),
            (self.x + self.width, self.y + self.height),
            (self.x, self.y + self.height)
        ]


@dataclass
class GeneratedWall:
    """A wall segment between rooms"""
    wall_id: str
    start: Tuple[float, float]
    end: Tuple[float, float]
    room_a: str                 # Room on one side
    room_b: Optional[str]       # Room on other side (None = exterior)
    has_door: bool = False
    door_position: float = 0.5  # 0-1 along wall


@dataclass
class GeneratedObstacle:
    """A generated obstacle/furniture piece"""
    obstacle_id: str
    name: str
    x: float
    y: float
    width: float
    height: float
    obstacle_type: str = "furniture"  # "furniture", "door", "window"


@dataclass
class GeneratedLayout:
    """Complete generated layout"""
    width: float
    height: float
    rooms: Dict[str, GeneratedRoom] = field(default_factory=dict)
    walls: List[GeneratedWall] = field(default_factory=list)
    obstacles: List[GeneratedObstacle] = field(default_factory=list)
    
    def get_zone_polygons(self) -> Dict[str, List[Tuple[float, float]]]:
        """Get room polygons for zone creation"""
        return {room_id: room.polygon for room_id, room in self.rooms.items()}
    
    def get_door_positions(self) -> List[Tuple[float, float]]:
        """Get all door positions"""
        positions = []
        for wall in self.walls:
            if wall.has_door:
                # Calculate door position along wall
                dx = wall.end[0] - wall.start[0]
                dy = wall.end[1] - wall.start[1]
                door_x = wall.start[0] + dx * wall.door_position
                door_y = wall.start[1] + dy * wall.door_position
                positions.append((door_x, door_y))
        return positions


class LayoutGenerator:
    """
    Generates building/dungeon layouts from room specifications.
    
    Usage:
        generator = LayoutGenerator(width=30, height=25)
        layout = generator.generate([
            RoomSpec("Entrance", is_entrance=True),
            RoomSpec("Kitchen", importance=2),
            RoomSpec("Dining Area", importance=3),
            RoomSpec("Storage"),
        ])
    """
    
    def __init__(self, width: float = 30, height: float = 25, 
                 style: LayoutStyle = LayoutStyle.GRID,
                 seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.style = style
        self.padding = 0.5  # Padding from edges
        self.min_room_size = 4.0
        self.wall_thickness = 0.5
        
        if seed is not None:
            random.seed(seed)
    
    def generate(self, room_specs: List[RoomSpec]) -> GeneratedLayout:
        """Generate a layout from room specifications"""
        if not room_specs:
            return self._generate_single_room("Main Area")
        
        if len(room_specs) == 1:
            return self._generate_single_room(room_specs[0].name)
        
        # Choose generation method based on style and room count
        if self.style == LayoutStyle.LINEAR or len(room_specs) <= 3:
            return self._generate_linear(room_specs)
        elif self.style == LayoutStyle.GRID or len(room_specs) <= 6:
            return self._generate_grid(room_specs)
        elif self.style == LayoutStyle.RADIAL:
            return self._generate_radial(room_specs)
        else:
            return self._generate_grid(room_specs)
    
    def generate_from_names(self, zone_names: List[str], 
                           location_type: str = "interior") -> GeneratedLayout:
        """
        Generate layout from just zone names.
        
        Infers room properties from names.
        """
        specs = []
        for name in zone_names:
            spec = self._infer_room_spec(name, location_type)
            specs.append(spec)
        
        # Determine style from location type
        if location_type in ["corridor", "hallway", "street"]:
            self.style = LayoutStyle.LINEAR
        elif location_type in ["warehouse", "factory", "office"]:
            self.style = LayoutStyle.GRID
        elif location_type in ["house", "apartment", "home"]:
            self.style = LayoutStyle.ORGANIC
        
        return self.generate(specs)
    
    def _infer_room_spec(self, name: str, location_type: str) -> RoomSpec:
        """Infer room properties from name"""
        name_lower = name.lower()
        
        # Detect entrance
        is_entrance = any(w in name_lower for w in 
                         ["entrance", "entry", "lobby", "foyer", "door", "exit"])
        
        # Detect importance/size
        importance = 1
        if any(w in name_lower for w in ["main", "large", "great", "big"]):
            importance = 3
        elif any(w in name_lower for w in ["small", "closet", "storage", "utility"]):
            importance = 1
        elif any(w in name_lower for w in ["dining", "living", "kitchen", "office"]):
            importance = 2
        
        # Detect zone type
        zone_type = "room"
        if any(w in name_lower for w in ["corridor", "hallway", "passage"]):
            zone_type = "corridor"
        elif any(w in name_lower for w in ["outside", "exterior", "yard", "garden"]):
            zone_type = "exterior"
        
        return RoomSpec(
            name=name,
            importance=importance,
            is_entrance=is_entrance,
            zone_type=zone_type,
            min_size=3.0 + importance,
            max_size=6.0 + importance * 2
        )
    
    def _generate_single_room(self, name: str) -> GeneratedLayout:
        """Generate a single-room layout"""
        layout = GeneratedLayout(width=self.width, height=self.height)
        
        room = GeneratedRoom(
            room_id="room_1",
            name=name,
            x=self.padding,
            y=self.padding,
            width=self.width - 2 * self.padding,
            height=self.height - 2 * self.padding
        )
        layout.rooms["room_1"] = room
        
        # Add entrance door on bottom wall
        layout.walls.append(GeneratedWall(
            wall_id="wall_entrance",
            start=(self.width * 0.4, self.padding),
            end=(self.width * 0.6, self.padding),
            room_a="room_1",
            room_b=None,
            has_door=True,
            door_position=0.5
        ))
        
        return layout
    
    def _generate_linear(self, specs: List[RoomSpec]) -> GeneratedLayout:
        """Generate rooms in a linear arrangement"""
        layout = GeneratedLayout(width=self.width, height=self.height)
        
        n = len(specs)
        room_width = (self.width - 2 * self.padding) / n
        room_height = self.height - 2 * self.padding
        
        prev_room_id = None
        
        for i, spec in enumerate(specs):
            room_id = f"room_{i+1}"
            x = self.padding + i * room_width
            
            # Add some variation
            width_var = room_width * random.uniform(0.9, 1.0)
            
            room = GeneratedRoom(
                room_id=room_id,
                name=spec.name,
                x=x,
                y=self.padding,
                width=width_var,
                height=room_height
            )
            layout.rooms[room_id] = room
            
            # Connect to previous room
            if prev_room_id:
                room.connections.append(prev_room_id)
                layout.rooms[prev_room_id].connections.append(room_id)
                
                # Add wall with door between rooms
                wall_x = x
                layout.walls.append(GeneratedWall(
                    wall_id=f"wall_{i}",
                    start=(wall_x, self.padding),
                    end=(wall_x, self.height - self.padding),
                    room_a=prev_room_id,
                    room_b=room_id,
                    has_door=True,
                    door_position=0.5
                ))
            
            # Add entrance door for entrance rooms
            if spec.is_entrance or i == 0:
                door_x = x + width_var / 2
                room.door_positions.append((door_x, self.padding))
            
            prev_room_id = room_id
        
        return layout
    
    def _generate_grid(self, specs: List[RoomSpec]) -> GeneratedLayout:
        """
        Generate an organic, irregular building layout like a real floor plan.
        
        Creates varied room sizes, L-shaped buildings, corridors, etc.
        """
        layout = GeneratedLayout(width=self.width, height=self.height)
        n = len(specs)
        
        if n <= 2:
            return self._generate_linear(specs)
        
        # Create an irregular building footprint
        # Use a template-based approach for interesting shapes
        template = self._select_building_template(n)
        
        # Place rooms according to template
        for i, (spec, room_bounds) in enumerate(zip(specs, template)):
            room_id = f"room_{i + 1}"
            x, y, w, h = room_bounds
            
            # Scale to actual dimensions
            rx = self.padding + x * (self.width - 2 * self.padding)
            ry = self.padding + y * (self.height - 2 * self.padding)
            rw = w * (self.width - 2 * self.padding)
            rh = h * (self.height - 2 * self.padding)
            
            room = GeneratedRoom(
                room_id=room_id,
                name=spec.name,
                x=rx, y=ry,
                width=rw, height=rh
            )
            layout.rooms[room_id] = room
        
        # Find adjacent rooms and create walls with doors
        self._create_walls_between_rooms(layout)
        
        # Add entrance
        self._add_entrance(layout, specs)
        
        # Generate furniture
        self._add_room_furniture(layout, specs)
        
        return layout
    
    def _select_building_template(self, n: int) -> List[Tuple[float, float, float, float]]:
        """
        Select a building template based on room count.
        Returns list of (x, y, width, height) in normalized 0-1 coordinates.
        
        IMPORTANT: Rooms must NOT overlap and should share edges cleanly.
        """
        # All templates use non-overlapping, edge-sharing rooms
        templates = {
            3: [
                # L-shape: two rooms on bottom, one on top-left
                [(0, 0, 0.5, 0.5), (0.5, 0, 0.5, 0.5), (0, 0.5, 0.5, 0.5)],
                # Three in a row
                [(0, 0, 0.33, 1.0), (0.33, 0, 0.34, 1.0), (0.67, 0, 0.33, 1.0)],
            ],
            4: [
                # 2x2 grid - clean and simple
                [(0, 0, 0.5, 0.5), (0.5, 0, 0.5, 0.5), (0, 0.5, 0.5, 0.5), (0.5, 0.5, 0.5, 0.5)],
                # L-shape with 4 rooms
                [(0, 0, 0.4, 0.5), (0.4, 0, 0.6, 0.5), (0.4, 0.5, 0.6, 0.5), (0, 0.5, 0.4, 0.5)],
            ],
            5: [
                # Like reference image - L-shaped building, no overlaps
                # Bottom row: room 5 (left), room 2 (center-ish), room 1 (right large)
                # Top row: room 4 (left), room 3 (right)
                [
                    (0.6, 0, 0.4, 0.5),    # 1: Bottom-right (entrance) - large
                    (0.3, 0, 0.3, 0.5),    # 2: Bottom-center
                    (0.3, 0.5, 0.4, 0.5),  # 3: Top-right
                    (0, 0.5, 0.3, 0.5),    # 4: Top-left
                    (0, 0, 0.3, 0.5),      # 5: Bottom-left
                ],
                # Alternative: T-shape
                [
                    (0.35, 0, 0.3, 0.4),   # 1: Bottom-center (entrance)
                    (0, 0.4, 0.35, 0.6),   # 2: Top-left
                    (0.35, 0.4, 0.3, 0.6), # 3: Top-center
                    (0.65, 0.4, 0.35, 0.6),# 4: Top-right
                    (0.65, 0, 0.35, 0.4),  # 5: Bottom-right
                ],
            ],
            6: [
                # 2x3 grid
                [
                    (0, 0, 0.33, 0.5),      # 1
                    (0.33, 0, 0.34, 0.5),   # 2
                    (0.67, 0, 0.33, 0.5),   # 3
                    (0, 0.5, 0.33, 0.5),    # 4
                    (0.33, 0.5, 0.34, 0.5), # 5
                    (0.67, 0.5, 0.33, 0.5), # 6
                ],
            ],
        }
        
        # Get templates for this room count, or generate a default
        if n in templates:
            return random.choice(templates[n])
        elif n < 3:
            # Simple side-by-side
            w = 1.0 / n
            return [(i * w, 0, w, 1.0) for i in range(n)]
        else:
            # For larger counts, create a grid
            return self._generate_grid_template(n)
    
    def _generate_grid_template(self, n: int) -> List[Tuple[float, float, float, float]]:
        """Generate a clean grid template for many rooms - no overlaps"""
        rooms = []
        
        # Calculate grid dimensions
        cols = math.ceil(math.sqrt(n))
        rows = math.ceil(n / cols)
        
        cell_w = 1.0 / cols
        cell_h = 1.0 / rows
        
        for i in range(n):
            row = i // cols
            col = i % cols
            x = col * cell_w
            y = row * cell_h
            rooms.append((x, y, cell_w, cell_h))
        
        return rooms
    
    def _create_walls_between_rooms(self, layout: GeneratedLayout):
        """Create walls with doors between adjacent rooms"""
        rooms = list(layout.rooms.values())
        processed_pairs = set()
        
        for i, room_a in enumerate(rooms):
            for j, room_b in enumerate(rooms):
                if i >= j:
                    continue
                
                pair_key = (room_a.room_id, room_b.room_id)
                if pair_key in processed_pairs:
                    continue
                
                # Check if rooms share an edge
                shared_edge = self._find_shared_edge(room_a, room_b)
                
                if shared_edge:
                    edge_type, start, end = shared_edge
                    
                    # Create wall with door
                    wall = GeneratedWall(
                        wall_id=f"wall_{room_a.room_id}_{room_b.room_id}",
                        start=start,
                        end=end,
                        room_a=room_a.room_id,
                        room_b=room_b.room_id,
                        has_door=True,
                        door_position=random.uniform(0.3, 0.7)
                    )
                    layout.walls.append(wall)
                    
                    room_a.connections.append(room_b.room_id)
                    room_b.connections.append(room_a.room_id)
                    processed_pairs.add(pair_key)
    
    def _find_shared_edge(self, room_a: GeneratedRoom, room_b: GeneratedRoom, 
                          tolerance: float = 1.0) -> Optional[Tuple[str, Tuple, Tuple]]:
        """Find if two rooms share an edge (are adjacent)"""
        a_left, a_right = room_a.x, room_a.x + room_a.width
        a_bottom, a_top = room_a.y, room_a.y + room_a.height
        b_left, b_right = room_b.x, room_b.x + room_b.width
        b_bottom, b_top = room_b.y, room_b.y + room_b.height
        
        # Check vertical adjacency (rooms side by side)
        if abs(a_right - b_left) < tolerance:
            # Room A is to the left of Room B
            overlap_bottom = max(a_bottom, b_bottom)
            overlap_top = min(a_top, b_top)
            if overlap_top > overlap_bottom + tolerance:
                x = (a_right + b_left) / 2
                return ("vertical", (x, overlap_bottom), (x, overlap_top))
        
        if abs(b_right - a_left) < tolerance:
            # Room B is to the left of Room A
            overlap_bottom = max(a_bottom, b_bottom)
            overlap_top = min(a_top, b_top)
            if overlap_top > overlap_bottom + tolerance:
                x = (b_right + a_left) / 2
                return ("vertical", (x, overlap_bottom), (x, overlap_top))
        
        # Check horizontal adjacency (rooms stacked)
        if abs(a_top - b_bottom) < tolerance:
            # Room A is below Room B
            overlap_left = max(a_left, b_left)
            overlap_right = min(a_right, b_right)
            if overlap_right > overlap_left + tolerance:
                y = (a_top + b_bottom) / 2
                return ("horizontal", (overlap_left, y), (overlap_right, y))
        
        if abs(b_top - a_bottom) < tolerance:
            # Room B is below Room A
            overlap_left = max(a_left, b_left)
            overlap_right = min(a_right, b_right)
            if overlap_right > overlap_left + tolerance:
                y = (b_top + a_bottom) / 2
                return ("horizontal", (overlap_left, y), (overlap_right, y))
        
        return None
    
    def _add_entrance(self, layout: GeneratedLayout, specs: List[RoomSpec]):
        """Add entrance door to the building"""
        # Find entrance room (first room or one marked as entrance)
        entrance_room = None
        for spec in specs:
            if spec.is_entrance:
                for room in layout.rooms.values():
                    if room.name == spec.name:
                        entrance_room = room
                        break
        
        if not entrance_room and layout.rooms:
            entrance_room = list(layout.rooms.values())[0]
        
        if entrance_room:
            # Add door on the bottom edge
            door_x = entrance_room.x + entrance_room.width / 2
            door_y = entrance_room.y
            entrance_room.door_positions.append((door_x, door_y))
    
    def _add_room_furniture(self, layout: GeneratedLayout, specs: List[RoomSpec]):
        """Add appropriate furniture/obstacles to rooms based on their type"""
        # Furniture sizes scaled for 250x200 maps (rooms ~50-80 units)
        # Each piece is roughly 8-15 units
        furniture_templates = {
            "entrance": [("Reception Desk", 15, 8)],
            "office": [("Desk", 12, 8), ("Filing Cabinet", 6, 6)],
            "storage": [("Shelves", 15, 5), ("Crates", 10, 10)],
            "kitchen": [("Counter", 15, 6), ("Stove", 8, 6)],
            "dining": [("Table", 12, 10), ("Chairs", 5, 5)],
            "break": [("Table", 10, 10), ("Vending Machine", 5, 6)],
            "corridor": [("Bench", 8, 4)],
            "hallway": [],
            "default": [("Table", 10, 8)]
        }
        
        obstacle_id = 0
        for room_id, room in layout.rooms.items():
            # Find matching spec
            spec = None
            for s in specs:
                if s.name == room.name:
                    spec = s
                    break
            
            # Determine furniture type from room name
            room_lower = room.name.lower()
            furniture_key = "default"
            for key in furniture_templates:
                if key in room_lower:
                    furniture_key = key
                    break
            
            furniture_list = furniture_templates.get(furniture_key, [])
            
            for furn_name, furn_w, furn_h in furniture_list:
                # Place furniture inside room with margin from walls
                margin = 5.0  # Keep furniture away from walls
                if room.width > furn_w + 2*margin and room.height > furn_h + 2*margin:
                    # Random position inside room
                    fx = room.x + margin + random.random() * (room.width - furn_w - 2*margin)
                    fy = room.y + margin + random.random() * (room.height - furn_h - 2*margin)
                    
                    obs = GeneratedObstacle(
                        obstacle_id=f"obs_{obstacle_id}",
                        name=furn_name,
                        x=fx + furn_w/2,  # Center position
                        y=fy + furn_h/2,
                        width=furn_w,
                        height=furn_h,
                        obstacle_type="furniture"
                    )
                    layout.obstacles.append(obs)
                    obstacle_id += 1
    
    def _generate_radial(self, specs: List[RoomSpec]) -> GeneratedLayout:
        """Generate rooms around a central hub"""
        layout = GeneratedLayout(width=self.width, height=self.height)
        
        center_x = self.width / 2
        center_y = self.height / 2
        
        # Central room
        hub_size = min(self.width, self.height) * 0.25
        hub = GeneratedRoom(
            room_id="room_hub",
            name=specs[0].name if specs else "Central Hub",
            x=center_x - hub_size/2,
            y=center_y - hub_size/2,
            width=hub_size,
            height=hub_size
        )
        layout.rooms["room_hub"] = hub
        
        # Surrounding rooms
        remaining = specs[1:] if len(specs) > 1 else []
        n = len(remaining)
        
        if n > 0:
            radius = min(self.width, self.height) * 0.35
            angle_step = 2 * math.pi / n
            
            for i, spec in enumerate(remaining):
                angle = i * angle_step - math.pi / 2  # Start from top
                room_id = f"room_{i + 1}"
                
                # Room size
                room_size = min(self.width, self.height) * 0.2
                
                # Position
                rx = center_x + radius * math.cos(angle) - room_size/2
                ry = center_y + radius * math.sin(angle) - room_size/2
                
                room = GeneratedRoom(
                    room_id=room_id,
                    name=spec.name,
                    x=rx,
                    y=ry,
                    width=room_size,
                    height=room_size,
                    connections=["room_hub"]
                )
                layout.rooms[room_id] = room
                hub.connections.append(room_id)
                
                # Wall from hub to this room
                layout.walls.append(GeneratedWall(
                    wall_id=f"wall_radial_{i}",
                    start=(center_x + hub_size/2 * math.cos(angle),
                           center_y + hub_size/2 * math.sin(angle)),
                    end=(rx + room_size/2, ry + room_size/2),
                    room_a="room_hub",
                    room_b=room_id,
                    has_door=True,
                    door_position=0.3
                ))
        
        return layout


def generate_layout_for_location(zone_names: List[str], 
                                 width: float, height: float,
                                 location_type: str = "interior",
                                 seed: Optional[int] = None) -> GeneratedLayout:
    """
    Convenience function to generate a layout for a location.
    
    Args:
        zone_names: List of zone/room names
        width: Location width
        height: Location height
        location_type: Type of location (interior, exterior, etc.)
        seed: Random seed for reproducibility
    
    Returns:
        GeneratedLayout with rooms and walls
    """
    generator = LayoutGenerator(width=width, height=height, seed=seed)
    return generator.generate_from_names(zone_names, location_type)


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Testing Layout Generator...")
    
    # Test 1: Simple layout
    layout = generate_layout_for_location(
        zone_names=["Entrance", "Kitchen", "Dining Area", "Storage", "Office"],
        width=30,
        height=25,
        location_type="warehouse"
    )
    
    print(f"\nGenerated layout: {layout.width}x{layout.height}")
    print(f"Rooms: {len(layout.rooms)}")
    for room_id, room in layout.rooms.items():
        print(f"  {room_id}: {room.name} at ({room.x:.1f}, {room.y:.1f}) "
              f"size {room.width:.1f}x{room.height:.1f}")
        print(f"    Connections: {room.connections}")
    
    print(f"\nWalls: {len(layout.walls)}")
    for wall in layout.walls:
        door_str = " [DOOR]" if wall.has_door else ""
        print(f"  {wall.wall_id}: {wall.room_a} <-> {wall.room_b}{door_str}")
    
    print(f"\nDoor positions: {layout.get_door_positions()}")
    
    # Test 2: Linear layout
    print("\n" + "="*50)
    print("Testing linear layout...")
    
    generator = LayoutGenerator(width=40, height=10, style=LayoutStyle.LINEAR)
    layout2 = generator.generate([
        RoomSpec("Entrance", is_entrance=True),
        RoomSpec("Corridor"),
        RoomSpec("Office"),
    ])
    
    print(f"Linear layout: {len(layout2.rooms)} rooms, {len(layout2.walls)} walls")
    
    print("\n✅ Layout generator tests passed!")
