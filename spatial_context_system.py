"""
Spatial Context System - Location Dimensions & Actor Positioning

Core Purpose:
- Track WHERE actors exist in physical space (X/Y grid coordinates)
- Define location dimensions to understand distance relationships
- Enable distance-based action mechanics (whisper vs shout, partial actions)
- Maintain list of POSSIBLE actors that can be introduced narratively
- Prevent arbitrary actor creation - only pre-seeded actors can appear
- Persist spatial state to JSON for context continuity

Design Philosophy:
- Top-down grid view for universal spatial context
- Distance affects action feasibility and success
- Narrative consistency through pre-defined actor pool
- No spontaneous actor generation from user intent alone
"""

import json
import math
import os
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from pathlib import Path
from enum import Enum
import re


DEFAULT_MAP_WIDTH = 250.0
DEFAULT_MAP_HEIGHT = 200.0

try:
    from context_store import ContextStore, WorldTime
except Exception:
    ContextStore = None
    WorldTime = None

try:
    from master_time_coordinator import get_master_time_coordinator
except Exception:
    get_master_time_coordinator = None


class MovementSpeed(Enum):
    """
    Movement speed categories (units per second).
    
    Scaled for 250x200 map coordinates where:
    - 250 units ≈ 10 meters (a typical room width)
    - 1 unit ≈ 0.04 meters
    - Walking speed ~1.4 m/s = ~35 units/second
    """
    CRAWL = 12.5     # Crawling, sneaking very slowly (~0.5 m/s)
    SNEAK = 25.0     # Sneaking, careful movement (~1.0 m/s)
    WALK = 35.0      # Normal walking pace (~1.4 m/s)
    JOG = 62.5       # Light jog, hurried movement (~2.5 m/s)
    RUN = 100.0      # Running, urgent movement (~4.0 m/s)
    SPRINT = 150.0   # Full sprint, maximum speed (~6.0 m/s)


class DistanceCategory(Enum):
    """
    Distance categories for action mechanics.
    Scaled for 250x200 coordinate system (1 unit ≈ 0.04m).
    """
    IMMEDIATE = "immediate"      # 0-25 units (~1m): Touch range, whisper
    CLOSE = "close"              # 26-50 units (~2m): Normal conversation
    NEAR = "near"                # 51-100 units (~4m): Raised voice, quick movement
    FAR = "far"                  # 101-200 units (~8m): Shout, significant movement
    DISTANT = "distant"          # 201+ units: Out of range for most actions


def build_spatial_facts(
    session_id: Optional[str] = None,
    *,
    max_actors: int = 14,
    max_obstacles: int = 10,
) -> str:
    """Build a compact, authoritative spatial facts block for LLM grounding.

    This is intended to be injected into prompts so narration stays consistent
    with the spatial/map truth.
    """
    try:
        spatial = get_spatial_manager(session_id=session_id)
        ctx = spatial.get_current_context() if spatial else None
        dims = getattr(ctx, 'location_dimensions', None) if ctx else None
        if not ctx or not dims:
            return ""

        lines: list[str] = []
        try:
            loc_name = str(getattr(dims, 'location_name', '') or getattr(spatial, 'current_location', '') or '').strip()
        except Exception:
            loc_name = ''
        loc_type = str(getattr(dims, 'location_type', '') or '').strip()
        w = float(getattr(dims, 'width', 0.0) or 0.0)
        h = float(getattr(dims, 'height', 0.0) or 0.0)

        hdr = f"Location: {loc_name or 'Unknown'}"
        if loc_type:
            hdr += f" | type={loc_type}"
        if w > 0 and h > 0:
            hdr += f" | size={w:.1f}x{h:.1f}"
        lines.append(hdr)

        def _zone_label_for_pos(p: 'Position') -> str:
            try:
                z = dims.get_zone_at_position(p) if hasattr(dims, 'get_zone_at_position') else None
                if z and getattr(z, 'zone_name', None):
                    return str(getattr(z, 'zone_name'))
            except Exception:
                pass
            try:
                for zn, zone in (getattr(dims, 'zones', {}) or {}).items():
                    if zone and hasattr(zone, 'contains_point') and zone.contains_point(p):
                        return str(getattr(zone, 'zone_name', None) or zn)
            except Exception:
                pass
            return ""

        # Actors (sorted so UA tends to appear first)
        actors = list((getattr(ctx, 'actor_positions', {}) or {}).items())
        try:
            def _sort_key(item):
                _aid, apos = item
                try:
                    is_ua = bool(getattr(apos, 'is_user_actor', False))
                except Exception:
                    is_ua = False
                nm = str(getattr(apos, 'actor_name', '') or _aid)
                return (0 if is_ua else 1, nm.lower())
            actors.sort(key=_sort_key)
        except Exception:
            pass

        if actors:
            lines.append("Actors:")
            for i, (aid, apos) in enumerate(actors[: max(1, int(max_actors))]):
                try:
                    p = getattr(apos, 'position', None)
                    if not p:
                        continue
                    ax = float(getattr(p, 'x', 0.0) or 0.0)
                    ay = float(getattr(p, 'y', 0.0) or 0.0)
                    name = str(getattr(apos, 'actor_name', '') or aid)
                    zn = _zone_label_for_pos(p)
                    zn_txt = f" zone={zn}" if zn else ""
                    lines.append(f"- {name}: ({ax:.1f}, {ay:.1f}){zn_txt}")
                except Exception:
                    continue

        # Landmarks/obstacles: keep short; just list names and centers.
        try:
            obs_items = list((getattr(dims, 'obstacles', {}) or {}).items())
        except Exception:
            obs_items = []

        if obs_items:
            lines.append("Landmarks:")
            for oid, o in obs_items[: max(1, int(max_obstacles))]:
                try:
                    oname = str(getattr(o, 'obstacle_name', '') or oid)
                    bps = getattr(o, 'boundary_points', None) or []
                    if bps:
                        cx = sum(float(getattr(pp, 'x', 0.0) or 0.0) for pp in bps) / len(bps)
                        cy = sum(float(getattr(pp, 'y', 0.0) or 0.0) for pp in bps) / len(bps)
                        lines.append(f"- {oname}: ({cx:.1f}, {cy:.1f})")
                    else:
                        lines.append(f"- {oname}")
                except Exception:
                    continue

        return "\n".join(lines).strip()
    except Exception:
        return ""


def calculate_swiftness_modifier(swiftness: int) -> float:
    """
    Calculate movement speed modifier based on Swiftness S-trait.
    
    Swiftness affects how fast an actor moves (units per second bonus).
    Scaled for 250x200 coordinate system.
    
    Args:
        swiftness: Swiftness S-trait value (1-5)
    
    Returns:
        Speed bonus in units/second
    
    Modifier Table (scaled for 250x200 coords):
        1 Swiftness = +0.0 u/s (no bonus)
        2 Swiftness = +5.0 u/s
        3 Swiftness = +10.0 u/s
        4 Swiftness = +15.0 u/s
        5 Swiftness = +20.0 u/s
    
    Examples:
        - Actor with 3 Swiftness walking (35 base): 35 + 10 = 45 u/s
        - Actor with 5 Swiftness running (100 base): 100 + 20 = 120 u/s
    """
    # Clamp swiftness to valid range
    swiftness = max(1, min(5, swiftness))
    
    # Calculate bonus: (swiftness - 1) * 5.0 (scaled for 250x200 coords)
    bonus = (swiftness - 1) * 5.0
    
    return bonus


def get_effective_speed(base_speed: MovementSpeed, swiftness: int) -> float:
    """
    Get effective movement speed including Swiftness modifier.
    
    Args:
        base_speed: Base movement speed category
        swiftness: Actor's Swiftness S-trait (1-5)
    
    Returns:
        Effective speed in units/second
    
    Examples:
        - WALK (2.0) + 3 Swiftness = 3.0 u/s
        - RUN (5.0) + 5 Swiftness = 7.0 u/s
        - SNEAK (1.0) + 2 Swiftness = 1.5 u/s
    """
    base = base_speed.value
    modifier = calculate_swiftness_modifier(swiftness)
    return base + modifier


@dataclass
class Position:
    """
    2D position supporting both Grid (X,Y) and Geographic (Lat/Lon) modes.
    
    Grid Mode: x/y in meters, origin at map center
    Geographic Mode: latitude/longitude in WGS84 degrees
    """
    x: float  # Grid X or Longitude
    y: float  # Grid Y or Latitude
    elevation: float = 0.0  # Meters above sea level
    is_geographic: bool = False  # True = lat/lon, False = grid x/y
    
    # Constants for geographic calculations
    EARTH_RADIUS_M = 6371000  # Earth radius in meters
    
    def distance_to(self, other: 'Position') -> float:
        """
        Calculate distance to another position.
        Uses Haversine formula for geographic, Euclidean for grid.
        Returns distance in meters.
        """
        if self.is_geographic and other.is_geographic:
            return self._haversine_distance(other)
        else:
            return math.sqrt((self.x - other.x)**2 + (self.y - other.y)**2)
    
    def _haversine_distance(self, other: 'Position') -> float:
        """Calculate great-circle distance using Haversine formula"""
        lat1, lon1 = math.radians(self.y), math.radians(self.x)
        lat2, lon2 = math.radians(other.y), math.radians(other.x)
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        
        return self.EARTH_RADIUS_M * c
    
    def to_grid(self, origin_lat: float = 0.0, origin_lon: float = 0.0) -> 'Position':
        """Convert geographic position to grid coordinates (meters from origin)"""
        if not self.is_geographic:
            return self
        
        # Calculate meters from origin
        origin = Position(origin_lon, origin_lat, is_geographic=True)
        
        # X distance (longitude difference)
        x_pos = Position(self.x, origin_lat, is_geographic=True)
        x_dist = origin._haversine_distance(x_pos)
        if self.x < origin_lon:
            x_dist = -x_dist
        
        # Y distance (latitude difference)
        y_pos = Position(origin_lon, self.y, is_geographic=True)
        y_dist = origin._haversine_distance(y_pos)
        if self.y < origin_lat:
            y_dist = -y_dist
        
        return Position(x_dist, y_dist, self.elevation, is_geographic=False)
    
    def to_geographic(self, origin_lat: float, origin_lon: float) -> 'Position':
        """Convert grid position to geographic coordinates"""
        if self.is_geographic:
            return self
        
        # Convert meters to degrees (approximate)
        lat_per_meter = 1 / 111320  # degrees per meter at equator
        lon_per_meter = 1 / (111320 * math.cos(math.radians(origin_lat)))
        
        new_lat = origin_lat + (self.y * lat_per_meter)
        new_lon = origin_lon + (self.x * lon_per_meter)
        
        return Position(new_lon, new_lat, self.elevation, is_geographic=True)
    
    def bearing_to(self, other: 'Position') -> float:
        """Calculate bearing (direction) to another position in degrees (0=North, 90=East)"""
        dx = other.x - self.x
        dy = other.y - self.y
        angle = math.degrees(math.atan2(dx, dy))  # atan2(x,y) for compass bearing
        return (angle + 360) % 360  # Normalize to 0-360
    
    def get_cardinal_direction(self, other: 'Position') -> str:
        """Get cardinal direction to another position as a string."""
        bearing = self.bearing_to(other)
        
        # Convert bearing to cardinal direction
        # Note: bearing 0 = North, 90 = East, 180 = South, 270 = West
        if bearing >= 337.5 or bearing < 22.5:
            return "north"
        elif bearing >= 22.5 and bearing < 67.5:
            return "northeast"
        elif bearing >= 67.5 and bearing < 112.5:
            return "east"
        elif bearing >= 112.5 and bearing < 157.5:
            return "southeast"
        elif bearing >= 157.5 and bearing < 202.5:
            return "south"
        elif bearing >= 202.5 and bearing < 247.5:
            return "southwest"
        elif bearing >= 247.5 and bearing < 292.5:
            return "west"
        else:  # 292.5 to 337.5
            return "northwest"
    
    def get_distance_category(self, other: 'Position') -> DistanceCategory:
        """Get distance category for action mechanics (scaled for 250x200 coords)"""
        distance = self.distance_to(other)
        
        if distance <= 25:      # ~1m
            return DistanceCategory.IMMEDIATE
        elif distance <= 50:    # ~2m
            return DistanceCategory.CLOSE
        elif distance <= 100:   # ~4m
            return DistanceCategory.NEAR
        elif distance <= 200:   # ~8m
            return DistanceCategory.FAR
        else:
            return DistanceCategory.DISTANT
    
    def calculate_movement_time(self, target: 'Position', speed: MovementSpeed = MovementSpeed.WALK,
                               swiftness: int = 3) -> float:
        """
        Calculate time in seconds to move from this position to target.
        
        Args:
            target: Destination position
            speed: Movement speed (default: WALK = 2 units/second)
            swiftness: Actor's Swiftness S-trait (1-5, default: 3)
        
        Returns:
            Time in seconds (float)
        
        Examples (with Swiftness 3 = +1.0 u/s):
            - 2 units at WALK (2.0 + 1.0 = 3.0 u/s) = 0.67 seconds
            - 5 units at WALK (2.0 + 1.0 = 3.0 u/s) = 1.67 seconds
            - 10 units at RUN (5.0 + 1.0 = 6.0 u/s) = 1.67 seconds
        
        Examples (with Swiftness 1 = +0.0 u/s):
            - 2 units at WALK (2.0 + 0.0 = 2.0 u/s) = 1.0 seconds
            - 10 units at RUN (5.0 + 0.0 = 5.0 u/s) = 2.0 seconds
        """
        distance = self.distance_to(target)
        effective_speed = get_effective_speed(speed, swiftness)
        time_seconds = distance / effective_speed
        return time_seconds
    
    def calculate_movement_time_with_ut(self, target: 'Position', speed: MovementSpeed = MovementSpeed.WALK,
                                       swiftness: int = 3, seconds_per_ut: float = 3.0) -> Tuple[float, int]:
        """
        Calculate movement time in both seconds and Unit Time (UT).
        
        Args:
            target: Destination position
            speed: Movement speed
            swiftness: Actor's Swiftness S-trait (1-5, default: 3)
            seconds_per_ut: How many seconds equal 1 UT (default: 3 seconds = 1 UT)
        
        Returns:
            Tuple of (seconds, unit_time)
        
        Examples (with Swiftness 3 = +1.0 u/s):
            - 2 units at WALK (3.0 u/s): 0.67 seconds = 1 UT
            - 6 units at WALK (3.0 u/s): 2.0 seconds = 1 UT
            - 10 units at WALK (3.0 u/s): 3.33 seconds = 2 UT
        
        Examples (with Swiftness 5 = +2.0 u/s):
            - 10 units at WALK (4.0 u/s): 2.5 seconds = 1 UT
            - 10 units at RUN (7.0 u/s): 1.43 seconds = 1 UT
        """
        time_seconds = self.calculate_movement_time(target, speed, swiftness)
        unit_time = math.ceil(time_seconds / seconds_per_ut)
        return time_seconds, unit_time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "x": self.x, 
            "y": self.y,
            "elevation": self.elevation,
            "is_geographic": self.is_geographic
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Position':
        """Create from dictionary"""
        return cls(
            x=data["x"], 
            y=data["y"],
            elevation=data.get("elevation", 0.0),
            is_geographic=data.get("is_geographic", False)
        )


@dataclass
class Zone:
    """Named area within a location (e.g., 'bar area', 'back room', 'parking lot')"""
    zone_name: str
    zone_type: str  # "room", "area", "corridor", "outdoor", etc.
    boundary_points: List[Position] = field(default_factory=list)  # Polygon vertices
    center: Optional[Position] = None
    description: str = ""
    
    def __post_init__(self):
        """Calculate center if not provided"""
        if not self.center and self.boundary_points:
            avg_x = sum(p.x for p in self.boundary_points) / len(self.boundary_points)
            avg_y = sum(p.y for p in self.boundary_points) / len(self.boundary_points)
            self.center = Position(avg_x, avg_y)
    
    def contains_point(self, pos: Position) -> bool:
        """Check if position is inside zone using ray casting algorithm"""
        if not self.boundary_points or len(self.boundary_points) < 3:
            return False
        
        # Ray casting algorithm for point-in-polygon
        inside = False
        j = len(self.boundary_points) - 1
        
        for i in range(len(self.boundary_points)):
            xi, yi = self.boundary_points[i].x, self.boundary_points[i].y
            xj, yj = self.boundary_points[j].x, self.boundary_points[j].y
            
            if ((yi > pos.y) != (yj > pos.y)) and \
               (pos.x < (xj - xi) * (pos.y - yi) / (yj - yi) + xi):
                inside = not inside
            
            j = i
        
        return inside
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "zone_name": self.zone_name,
            "zone_type": self.zone_type,
            "boundary_points": [p.to_dict() for p in self.boundary_points],
            "center": self.center.to_dict() if self.center else None,
            "description": self.description
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Zone':
        """Create from dictionary"""
        return cls(
            zone_name=data["zone_name"],
            zone_type=data["zone_type"],
            boundary_points=[Position.from_dict(p) for p in data.get("boundary_points", [])],
            center=Position.from_dict(data["center"]) if data.get("center") else None,
            description=data.get("description", "")
        )


@dataclass
class Obstacle:
    """Physical obstacle that blocks movement/line of sight"""
    obstacle_name: str
    obstacle_type: str  # "wall", "furniture", "vehicle", "counter", etc.
    boundary_points: List[Position] = field(default_factory=list)  # Polygon vertices
    blocks_movement: bool = True
    blocks_line_of_sight: bool = True
    height: float = 2.0  # Height in abstract units (for cover mechanics)
    portal_kind: str = ""  # e.g. "door", "exit", "hatch", "grate", "ladder"
    connects_from: str = ""  # zone/room id/name the portal starts from (if applicable)
    connects_to: str = ""  # zone/room id/name or "outside" (if applicable)
    is_external: bool = False  # True if this leads outside the current location
    
    def contains_point(self, pos: Position) -> bool:
        """Check if position is inside obstacle"""
        if not self.boundary_points or len(self.boundary_points) < 3:
            return False
        
        # Ray casting algorithm
        inside = False
        j = len(self.boundary_points) - 1
        
        for i in range(len(self.boundary_points)):
            xi, yi = self.boundary_points[i].x, self.boundary_points[i].y
            xj, yj = self.boundary_points[j].x, self.boundary_points[j].y
            
            if ((yi > pos.y) != (yj > pos.y)) and \
               (pos.x < (xj - xi) * (pos.y - yi) / (yj - yi) + xi):
                inside = not inside
            
            j = i
        
        return inside
    
    def intersects_line(self, start: Position, end: Position) -> bool:
        """Check if line segment intersects obstacle (for line of sight)"""
        if not self.boundary_points or len(self.boundary_points) < 2:
            return False
        
        # Check each edge of the obstacle polygon
        for i in range(len(self.boundary_points)):
            j = (i + 1) % len(self.boundary_points)
            if self._segments_intersect(start, end, 
                                       self.boundary_points[i], 
                                       self.boundary_points[j]):
                return True
        
        return False
    
    def _segments_intersect(self, p1: Position, p2: Position, 
                           p3: Position, p4: Position) -> bool:
        """Check if two line segments intersect"""
        def ccw(A: Position, B: Position, C: Position) -> bool:
            return (C.y - A.y) * (B.x - A.x) > (B.y - A.y) * (C.x - A.x)
        
        return ccw(p1, p3, p4) != ccw(p2, p3, p4) and ccw(p1, p2, p3) != ccw(p1, p2, p4)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "obstacle_name": self.obstacle_name,
            "obstacle_type": self.obstacle_type,
            "boundary_points": [p.to_dict() for p in self.boundary_points],
            "blocks_movement": self.blocks_movement,
            "blocks_line_of_sight": self.blocks_line_of_sight,
            "height": self.height,
            "portal_kind": self.portal_kind,
            "connects_from": self.connects_from,
            "connects_to": self.connects_to,
            "is_external": self.is_external,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Obstacle':
        """Create from dictionary"""
        return cls(
            obstacle_name=data["obstacle_name"],
            obstacle_type=data["obstacle_type"],
            boundary_points=[Position.from_dict(p) for p in data.get("boundary_points", [])],
            blocks_movement=data.get("blocks_movement", True),
            blocks_line_of_sight=data.get("blocks_line_of_sight", True),
            height=data.get("height", 2.0),
            portal_kind=data.get("portal_kind", ""),
            connects_from=data.get("connects_from", ""),
            connects_to=data.get("connects_to", ""),
            is_external=bool(data.get("is_external", False)),
        )


@dataclass
class LocationDimensions:
    """Physical dimensions of a location with dynamic layout support"""
    width: float  # X-axis extent (units) - bounding box
    height: float  # Y-axis extent (units) - bounding box
    location_name: str
    location_type: str  # "interior", "exterior", "street", "building", etc.
    description: str = ""
    scene_description: str = ""  # Full scene description for LLM layout generation
    zones: Dict[str, Zone] = field(default_factory=dict)  # Named areas
    obstacles: Dict[str, Obstacle] = field(default_factory=dict)  # Physical obstacles
    
    def is_position_valid(self, pos: Position) -> bool:
        """Check if position is within location bounds and not in obstacle"""
        # Check bounding box
        if not (0 <= pos.x <= self.width and 0 <= pos.y <= self.height):
            return False
        
        # Check if position is inside any obstacle
        for obstacle in self.obstacles.values():
            if obstacle.blocks_movement and obstacle.contains_point(pos):
                return False
        
        return True
    
    def get_zone_at_position(self, pos: Position) -> Optional[Zone]:
        """Get zone that contains this position"""
        for zone in self.zones.values():
            if zone.contains_point(pos):
                return zone
        return None
    
    def has_line_of_sight(self, start: Position, end: Position) -> bool:
        """Check if there's clear line of sight between two positions"""
        for obstacle in self.obstacles.values():
            if obstacle.blocks_line_of_sight and obstacle.intersects_line(start, end):
                return False
        return True
    
    def get_center(self) -> Position:
        """Get center position of location"""
        return Position(x=self.width / 2, y=self.height / 2)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "width": self.width,
            "height": self.height,
            "location_name": self.location_name,
            "location_type": self.location_type,
            "description": self.description,
            "scene_description": self.scene_description,
            "zones": {k: v.to_dict() for k, v in self.zones.items()},
            "obstacles": {k: v.to_dict() for k, v in self.obstacles.items()}
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationDimensions':
        """Create from dictionary"""
        return cls(
            width=data["width"],
            height=data["height"],
            location_name=data["location_name"],
            location_type=data["location_type"],
            description=data.get("description", ""),
            scene_description=data.get("scene_description", ""),
            zones={k: Zone.from_dict(v) for k, v in data.get("zones", {}).items()},
            obstacles={k: Obstacle.from_dict(v) for k, v in data.get("obstacles", {}).items()}
        )


@dataclass
class TrailPoint:
    """A single point in an actor's movement trail"""
    position: Position
    timestamp: float  # Unix timestamp
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "position": self.position.to_dict(),
            "timestamp": self.timestamp
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TrailPoint':
        return cls(
            position=Position.from_dict(data["position"]),
            timestamp=data["timestamp"]
        )


@dataclass
class ActorPosition:
    """
    Actor's position in space with movement trail tracking.
    
    Trail System:
    - Stores last N positions with timestamps
    - Calculates distance traveled, speed, direction
    - Auto-cleans old trail points (>5 min real-time)
    """
    actor_id: str
    actor_name: str
    position: Position
    is_user_actor: bool = False
    is_active: bool = True  # Currently present in scene
    facing_direction: float = 0.0  # Degrees, 0=North, 90=East
    actor_type: str = "nua"  # "ua", "nua", "mnua", "inua"
    occupation: str = ""
    
    # Movement trail
    trail: List[TrailPoint] = field(default_factory=list)
    max_trail_length: int = 10
    trail_duration_seconds: float = 300.0  # 5 minutes
    
    def add_trail_point(self, old_position: Position, timestamp: float = None):
        """Add a point to the movement trail"""
        import time as time_module
        if timestamp is None:
            timestamp = time_module.time()
        
        # Add old position to trail
        self.trail.append(TrailPoint(old_position, timestamp))
        
        # Trim to max length
        if len(self.trail) > self.max_trail_length:
            self.trail = self.trail[-self.max_trail_length:]
        
        # Update facing direction
        self.facing_direction = old_position.bearing_to(self.position)
    
    def clean_old_trail_points(self):
        """Remove trail points older than trail_duration_seconds"""
        import time as time_module
        cutoff = time_module.time() - self.trail_duration_seconds
        self.trail = [p for p in self.trail if p.timestamp > cutoff]
    
    def get_trail_distance(self) -> float:
        """Calculate total distance traveled along trail"""
        if len(self.trail) < 1:
            return 0.0
        
        total = 0.0
        points = [p.position for p in self.trail] + [self.position]
        for i in range(len(points) - 1):
            total += points[i].distance_to(points[i + 1])
        return total
    
    def get_straight_line_distance(self) -> float:
        """Calculate straight-line distance from trail start to current position"""
        if len(self.trail) < 1:
            return 0.0
        return self.trail[0].position.distance_to(self.position)
    
    def get_average_speed(self) -> float:
        """Calculate average speed from last 3 trail points (units/second)"""
        if len(self.trail) < 2:
            return 0.0
        
        # Use last 3 points
        recent = self.trail[-3:] if len(self.trail) >= 3 else self.trail
        
        total_dist = 0.0
        points = [p.position for p in recent] + [self.position]
        for i in range(len(points) - 1):
            total_dist += points[i].distance_to(points[i + 1])
        
        time_span = recent[-1].timestamp - recent[0].timestamp if len(recent) > 1 else 1.0
        if time_span <= 0:
            return 0.0
        
        return total_dist / time_span
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "position": self.position.to_dict(),
            "is_user_actor": self.is_user_actor,
            "is_active": self.is_active,
            "facing_direction": self.facing_direction,
            "actor_type": self.actor_type,
            "occupation": self.occupation,
            "trail": [p.to_dict() for p in self.trail],
            "max_trail_length": self.max_trail_length,
            "trail_duration_seconds": self.trail_duration_seconds
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActorPosition':
        """Create from dictionary"""
        actor = cls(
            actor_id=data["actor_id"],
            actor_name=data["actor_name"],
            position=Position.from_dict(data["position"]),
            is_user_actor=data.get("is_user_actor", False),
            is_active=data.get("is_active", True),
            facing_direction=data.get("facing_direction", 0.0),
            actor_type=data.get("actor_type", "nua"),
            occupation=data.get("occupation", ""),
            max_trail_length=data.get("max_trail_length", 10),
            trail_duration_seconds=data.get("trail_duration_seconds", 300.0)
        )
        actor.trail = [TrailPoint.from_dict(p) for p in data.get("trail", [])]
        return actor


@dataclass
class PossibleActor:
    """Pre-seeded actor that can be introduced narratively"""
    actor_id: str
    actor_name: str
    actor_type: str  # "NUA" or "INUA"
    brief_description: str
    narrative_role: str  # "ally", "antagonist", "neutral", "obstacle", "resource"
    introduction_triggers: List[str] = field(default_factory=list)  # Keywords/conditions
    has_been_introduced: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "actor_id": self.actor_id,
            "actor_name": self.actor_name,
            "actor_type": self.actor_type,
            "brief_description": self.brief_description,
            "narrative_role": self.narrative_role,
            "introduction_triggers": self.introduction_triggers,
            "has_been_introduced": self.has_been_introduced
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PossibleActor':
        """Create from dictionary"""
        return cls(
            actor_id=data["actor_id"],
            actor_name=data["actor_name"],
            actor_type=data["actor_type"],
            brief_description=data["brief_description"],
            narrative_role=data["narrative_role"],
            introduction_triggers=data.get("introduction_triggers", []),
            has_been_introduced=data.get("has_been_introduced", False)
        )


@dataclass
class SpatialContext:
    """Complete spatial context for a location"""
    location_dimensions: LocationDimensions
    actor_positions: Dict[str, ActorPosition] = field(default_factory=dict)
    possible_actors: Dict[str, PossibleActor] = field(default_factory=dict)
    last_updated: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {
            "location_dimensions": self.location_dimensions.to_dict(),
            "actor_positions": {k: v.to_dict() for k, v in self.actor_positions.items()},
            "possible_actors": {k: v.to_dict() for k, v in self.possible_actors.items()},
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SpatialContext':
        """Create from dictionary"""
        return cls(
            location_dimensions=LocationDimensions.from_dict(data["location_dimensions"]),
            actor_positions={k: ActorPosition.from_dict(v) for k, v in data.get("actor_positions", {}).items()},
            possible_actors={k: PossibleActor.from_dict(v) for k, v in data.get("possible_actors", {}).items()},
            last_updated=data.get("last_updated", "")
        )


class SpatialContextManager:
    """
    Manages spatial context for locations.
    
    Responsibilities:
    1. Track actor positions on X/Y grid
    2. Calculate distances between actors
    3. Determine action feasibility based on distance
    4. Maintain pool of possible actors for narrative consistency
    5. Prevent arbitrary actor creation
    6. Persist spatial state to JSON
    """
    
    def __init__(self, session_id: str = "default"):
        self.session_id = session_id
        self.contexts: Dict[str, SpatialContext] = {}
        self.current_location: Optional[str] = None
        self.save_path = Path(f"sessions/{session_id}/spatial_context.json")
        self.save_path.parent.mkdir(parents=True, exist_ok=True)
        self._context_store = None
        self._last_position_snapshot_signature: Dict[str, tuple] = {}
        self._last_position_snapshot_world_minutes: Dict[str, int] = {}

        self._last_actor_move_world_minutes: Dict[str, int] = {}
        self._last_actor_move_cell: Dict[str, tuple] = {}
        self._last_actor_zone: Dict[str, str] = {}

        # Keep a best-effort record of the last known map dimensions for this manager/session.
        self._last_known_dimensions: Tuple[float, float, str] = (DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT, "interior")
        self._load()

    def _normalize_loaded_context(self, ctx: SpatialContext) -> bool:
        try:
            dims = getattr(ctx, 'location_dimensions', None)
            if dims is None:
                return False
            w = float(getattr(dims, 'width', 0.0) or 0.0)
            h = float(getattr(dims, 'height', 0.0) or 0.0)
            if w <= 0 or h <= 0:
                return False
            if w >= 20.0 and h >= 20.0:
                return False

            sx = float(DEFAULT_MAP_WIDTH) / max(1.0, w)
            sy = float(DEFAULT_MAP_HEIGHT) / max(1.0, h)

            try:
                dims.width = float(DEFAULT_MAP_WIDTH)
                dims.height = float(DEFAULT_MAP_HEIGHT)
            except Exception:
                pass

            try:
                for apos in (getattr(ctx, 'actor_positions', {}) or {}).values():
                    p = getattr(apos, 'position', None)
                    if p is None:
                        continue
                    try:
                        p.x = float(getattr(p, 'x', 0.0) or 0.0) * sx
                        p.y = float(getattr(p, 'y', 0.0) or 0.0) * sy
                    except Exception:
                        pass
                    try:
                        for tp in getattr(apos, 'trail', []) or []:
                            pp = getattr(tp, 'position', None)
                            if pp is None:
                                continue
                            pp.x = float(getattr(pp, 'x', 0.0) or 0.0) * sx
                            pp.y = float(getattr(pp, 'y', 0.0) or 0.0) * sy
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                for z in (getattr(dims, 'zones', {}) or {}).values():
                    try:
                        c = getattr(z, 'center', None)
                        if c is not None:
                            c.x = float(getattr(c, 'x', 0.0) or 0.0) * sx
                            c.y = float(getattr(c, 'y', 0.0) or 0.0) * sy
                    except Exception:
                        pass
                    try:
                        for bp in getattr(z, 'boundary_points', []) or []:
                            bp.x = float(getattr(bp, 'x', 0.0) or 0.0) * sx
                            bp.y = float(getattr(bp, 'y', 0.0) or 0.0) * sy
                    except Exception:
                        pass
            except Exception:
                pass

            try:
                for o in (getattr(dims, 'obstacles', {}) or {}).values():
                    try:
                        for bp in getattr(o, 'boundary_points', []) or []:
                            bp.x = float(getattr(bp, 'x', 0.0) or 0.0) * sx
                            bp.y = float(getattr(bp, 'y', 0.0) or 0.0) * sy
                    except Exception:
                        pass
            except Exception:
                pass

            return True
        except Exception:
            return False
    
    # === LOCATION MANAGEMENT ===
    
    def location_exists(self, location_name: str) -> bool:
        """Check if a location already exists"""
        return location_name in self.contexts

    def _parse_floor_from_location_name(self, location_name: str) -> Tuple[str, Optional[int]]:
        try:
            nm = str(location_name or '').strip()
        except Exception:
            return (str(location_name or ''), None)

        if not nm:
            return (nm, None)

        m = re.match(r"^(.*)\s*\(\s*floor\s*(\d+)\s*\)\s*$", nm, flags=re.IGNORECASE)
        if m:
            base = (m.group(1) or '').strip()
            try:
                return (base, int(m.group(2)))
            except Exception:
                return (base, None)

        m2 = re.match(r"^(.*)\s*\(\s*basement\s*\)\s*$", nm, flags=re.IGNORECASE)
        if m2:
            base = (m2.group(1) or '').strip()
            return (base, -1)

        return (nm, None)

    def _format_location_name_for_floor(self, base_location: str, floor: int) -> str:
        base = str(base_location or '').strip() or 'Location'
        if int(floor) < 0:
            return f"{base} (Basement)"
        return f"{base} (Floor {int(floor)})"

    def get_current_base_location_and_floor(self) -> Tuple[str, int]:
        base, fl = self._parse_floor_from_location_name(self.current_location or '')
        if fl is None:
            fl = 1
        if not base:
            base = str(self.current_location or '').strip() or 'Location'
        return (base, int(fl))

    def change_floor(self, *, delta: int = 0, floor: Optional[int] = None, base_location: Optional[str] = None) -> Optional[str]:
        try:
            base, cur_floor = self.get_current_base_location_and_floor()
        except Exception:
            base, cur_floor = (str(self.current_location or '').strip() or 'Location', 1)

        if base_location is not None:
            base = str(base_location or '').strip() or base

        target_floor = int(floor) if floor is not None else int(cur_floor + int(delta))
        if target_floor == 0:
            target_floor = 1

        target_name = self._format_location_name_for_floor(base, target_floor)

        # Snapshot UA position from current context (if present)
        ua_snapshot = None
        try:
            ctx = self.get_current_context()
            if ctx and isinstance(getattr(ctx, 'actor_positions', None), dict):
                ua_snapshot = ctx.actor_positions.get('ua_001')
        except Exception:
            ua_snapshot = None

        if target_name not in self.contexts:
            # Create new floor context with same footprint as current (preferred), else last-known,
            # else a centralized safe default.
            w, h, loc_type = DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT, 'interior'
            try:
                cur_ctx = self.get_current_context()
                dims = getattr(cur_ctx, 'location_dimensions', None) if cur_ctx else None
                if dims:
                    w = float(getattr(dims, 'width', w) or w)
                    h = float(getattr(dims, 'height', h) or h)
                    loc_type = str(getattr(dims, 'location_type', loc_type) or loc_type)
                else:
                    lw, lh, lt = getattr(self, '_last_known_dimensions', (w, h, loc_type))
                    w = float(lw or w)
                    h = float(lh or h)
                    loc_type = str(lt or loc_type)
            except Exception:
                try:
                    lw, lh, lt = getattr(self, '_last_known_dimensions', (w, h, loc_type))
                    w = float(lw or w)
                    h = float(lh or h)
                    loc_type = str(lt or loc_type)
                except Exception:
                    pass

            self.create_location(target_name, width=w, height=h, location_type=loc_type)

        self.set_current_location(target_name)

        # Carry UA to the new floor so map shows continuity
        try:
            new_ctx = self.get_current_context()
            if new_ctx and ua_snapshot is not None:
                new_ctx.actor_positions['ua_001'] = ua_snapshot
                try:
                    new_ctx.actor_positions['ua_001'].is_active = True
                except Exception:
                    pass
            elif new_ctx:
                try:
                    center = new_ctx.location_dimensions.get_center()
                    self.add_actor('ua_001', 'UA', center, is_user_actor=True)
                except Exception:
                    pass
            self._save()
        except Exception:
            pass

        return target_name
    
    def create_location(self, location_name: str, width: float, height: float, 
                       location_type: str, description: str = "",
                       scene_description: str = "",
                       auto_add_door: bool = True) -> SpatialContext:
        """Create a new location with dimensions"""
        dimensions = LocationDimensions(
            width=width,
            height=height,
            location_name=location_name,
            location_type=location_type,
            description=description,
            scene_description=scene_description  # Full scene description for LLM layout
        )

        try:
            use_graph = False
            try:
                use_graph = str(os.getenv("SPATIAL_USE_GRAPH_LAYOUT") or "").strip().lower() in ("1", "true", "yes", "on")
            except Exception:
                use_graph = False

            if use_graph:
                try:
                    from spatial_layout_graph import build_layout_graph_for_location, embed_graph_as_rect_zones
                    g = build_layout_graph_for_location(
                        location_name=location_name,
                        location_type=location_type,
                        scene_description=scene_description or description or "",
                    )
                    polys = embed_graph_as_rect_zones(graph=g, width=float(width), height=float(height))
                    if polys:
                        for zid, poly in polys.items():
                            try:
                                bps = [Position(float(x), float(y)) for (x, y) in (poly or [])]
                                if len(bps) >= 3:
                                    try:
                                        zname = str(getattr(g.nodes.get(zid), 'name', None) or zid)
                                        ztype = str(getattr(g.nodes.get(zid), 'kind', None) or 'room')
                                    except Exception:
                                        zname = str(zid)
                                        ztype = 'room'

                                    dimensions.zones[str(zid)] = Zone(
                                        zone_name=zname,
                                        zone_type=ztype,
                                        boundary_points=bps,
                                        center=None,
                                        description="",
                                    )
                            except Exception:
                                continue

                    try:
                        use_portals = False
                        try:
                            use_portals = str(os.getenv("SPATIAL_GRAPH_MATERIALIZE_PORTALS") or "").strip().lower() in (
                                "1", "true", "yes", "on"
                            )
                        except Exception:
                            use_portals = False

                        if use_portals and polys and getattr(g, 'edges', None):
                            def _rect_bounds_from_poly(poly_pts: List[Tuple[float, float]]) -> Optional[Tuple[float, float, float, float]]:
                                try:
                                    xs = [float(p[0]) for p in (poly_pts or [])]
                                    ys = [float(p[1]) for p in (poly_pts or [])]
                                    if not xs or not ys:
                                        return None
                                    return (min(xs), min(ys), max(xs), max(ys))
                                except Exception:
                                    return None

                            rects: Dict[str, Tuple[float, float, float, float]] = {}
                            for zid, poly in (polys or {}).items():
                                rb = _rect_bounds_from_poly(poly or [])
                                if rb is not None:
                                    rects[str(zid)] = rb

                            def _units_from_meters(m: float) -> float:
                                try:
                                    return float(m) * 25.0
                                except Exception:
                                    return 25.0

                            for e in list(getattr(g, 'edges', []) or []):
                                try:
                                    a = str(getattr(e, 'a', '') or '')
                                    b = str(getattr(e, 'b', '') or '')
                                    if not a or not b:
                                        continue
                                    if a not in rects or b not in rects:
                                        continue

                                    ax0, ay0, ax1, ay1 = rects[a]
                                    bx0, by0, bx1, by1 = rects[b]
                                    acx, acy = (ax0 + ax1) / 2.0, (ay0 + ay1) / 2.0
                                    bcx, bcy = (bx0 + bx1) / 2.0, (by0 + by1) / 2.0
                                    dx = bcx - acx
                                    dy = bcy - acy

                                    door_w = _units_from_meters(float(getattr(e, 'width', 1.0) or 1.0))
                                    door_w = max(6.0, min(40.0, door_w))
                                    thick = 5.0

                                    if abs(dx) >= abs(dy):
                                        if dx >= 0:
                                            x = min(ax1, bx0)
                                        else:
                                            x = max(ax0, bx1)

                                        ov0 = max(ay0, by0)
                                        ov1 = min(ay1, by1)
                                        if ov1 > ov0:
                                            cy = (ov0 + ov1) / 2.0
                                        else:
                                            cy = (acy + bcy) / 2.0

                                        y0 = cy - (door_w / 2.0)
                                        y1 = cy + (door_w / 2.0)
                                        x0 = x - (thick / 2.0)
                                        x1 = x + (thick / 2.0)
                                    else:
                                        if dy >= 0:
                                            y = min(ay1, by0)
                                        else:
                                            y = max(ay0, by1)

                                        ov0 = max(ax0, bx0)
                                        ov1 = min(ax1, bx1)
                                        if ov1 > ov0:
                                            cx = (ov0 + ov1) / 2.0
                                        else:
                                            cx = (acx + bcx) / 2.0

                                        x0 = cx - (door_w / 2.0)
                                        x1 = cx + (door_w / 2.0)
                                        y0 = y - (thick / 2.0)
                                        y1 = y + (thick / 2.0)

                                    x0 = max(0.0, min(float(width), x0))
                                    x1 = max(0.0, min(float(width), x1))
                                    y0 = max(0.0, min(float(height), y0))
                                    y1 = max(0.0, min(float(height), y1))
                                    if (x1 - x0) < 1.0 or (y1 - y0) < 1.0:
                                        continue

                                    kind = str(getattr(e, 'kind', 'door') or 'door')
                                    obs_key = f"portal_{a}_{b}"[:64]
                                    dimensions.obstacles[obs_key] = Obstacle(
                                        obstacle_name=obs_key,
                                        obstacle_type="door" if kind in ("door", "archway") else "portal",
                                        boundary_points=[
                                            Position(x0, y0),
                                            Position(x1, y0),
                                            Position(x1, y1),
                                            Position(x0, y1),
                                        ],
                                        blocks_movement=False,
                                        blocks_line_of_sight=False,
                                        height=2.0,
                                        portal_kind=kind,
                                        connects_from=a,
                                        connects_to=b,
                                        is_external=False,
                                    )
                                except Exception:
                                    continue
                    except Exception:
                        pass

                    try:
                        use_walls = False
                        try:
                            use_walls = str(os.getenv("SPATIAL_GRAPH_MATERIALIZE_WALLS") or "").strip().lower() in (
                                "1", "true", "yes", "on"
                            )
                        except Exception:
                            use_walls = False

                        if use_walls and polys:
                            def _rect_bounds_from_poly(poly_pts: List[Tuple[float, float]]) -> Optional[Tuple[float, float, float, float]]:
                                try:
                                    xs = [float(p[0]) for p in (poly_pts or [])]
                                    ys = [float(p[1]) for p in (poly_pts or [])]
                                    if not xs or not ys:
                                        return None
                                    return (min(xs), min(ys), max(xs), max(ys))
                                except Exception:
                                    return None

                            rects2: Dict[str, Tuple[float, float, float, float]] = {}
                            for zid, poly in (polys or {}).items():
                                rb = _rect_bounds_from_poly(poly or [])
                                if rb is not None:
                                    rects2[str(zid)] = rb

                            portals = []
                            try:
                                for ok, o in (getattr(dimensions, 'obstacles', {}) or {}).items():
                                    if not o:
                                        continue
                                    ot_l = str(getattr(o, 'obstacle_type', '') or '').lower()
                                    pk = str(getattr(o, 'portal_kind', '') or '')
                                    cf = str(getattr(o, 'connects_from', '') or '')
                                    ct = str(getattr(o, 'connects_to', '') or '')
                                    is_ext = bool(getattr(o, 'is_external', False))

                                    is_portalish = bool(pk and cf and ct)
                                    is_exitish = ot_l == 'exit' or is_ext
                                    if not (is_portalish or is_exitish):
                                        continue

                                    bps = getattr(o, 'boundary_points', None) or []
                                    xs = [float(getattr(p, 'x', 0.0) or 0.0) for p in bps]
                                    ys = [float(getattr(p, 'y', 0.0) or 0.0) for p in bps]
                                    if not xs or not ys:
                                        continue

                                    if is_ext and not cf:
                                        cf = "__all__"
                                    if is_ext and not ct:
                                        ct = "outside"

                                    portals.append((cf, ct, min(xs), min(ys), max(xs), max(ys)))
                            except Exception:
                                portals = []

                            wall_thick = 5.0
                            gap_pad = 2.0

                            def _add_wall_rect(key: str, x0: float, y0: float, x1: float, y1: float):
                                try:
                                    x0 = max(0.0, min(float(width), float(x0)))
                                    x1 = max(0.0, min(float(width), float(x1)))
                                    y0 = max(0.0, min(float(height), float(y0)))
                                    y1 = max(0.0, min(float(height), float(y1)))
                                    if (x1 - x0) < 1.0 or (y1 - y0) < 1.0:
                                        return
                                    k = str(key)[:64]
                                    if k in dimensions.obstacles:
                                        return
                                    dimensions.obstacles[k] = Obstacle(
                                        obstacle_name=k,
                                        obstacle_type="wall",
                                        boundary_points=[
                                            Position(x0, y0),
                                            Position(x1, y0),
                                            Position(x1, y1),
                                            Position(x0, y1),
                                        ],
                                        blocks_movement=True,
                                        blocks_line_of_sight=True,
                                        height=2.0,
                                    )
                                except Exception:
                                    return

                            for zid, (zx0, zy0, zx1, zy1) in rects2.items():
                                try:
                                    zpw = [p for p in portals if (p[0] == zid or p[1] == zid or p[0] == "__all__")]
                                except Exception:
                                    zpw = []

                                left_band = (zx0, zy0, zx0 + wall_thick, zy1)
                                right_band = (zx1 - wall_thick, zy0, zx1, zy1)
                                bottom_band = (zx0, zy0, zx1, zy0 + wall_thick)
                                top_band = (zx0, zy1 - wall_thick, zx1, zy1)

                                def _carve_vertical(band, side_key):
                                    bx0, by0, bx1, by1 = band
                                    gaps = []
                                    for (_cf, _ct, px0, py0, px1, py1) in zpw:
                                        if not (px1 >= bx0 and px0 <= bx1):
                                            continue
                                        gy0 = max(by0, py0 - gap_pad)
                                        gy1 = min(by1, py1 + gap_pad)
                                        if gy1 > gy0:
                                            gaps.append((gy0, gy1))
                                    if not gaps:
                                        _add_wall_rect(f"wall_{zid}_{side_key}", bx0, by0, bx1, by1)
                                        return
                                    gaps.sort(key=lambda t: t[0])
                                    cur = by0
                                    idx = 0
                                    for (g0, g1) in gaps:
                                        if g0 > cur + 0.5:
                                            _add_wall_rect(f"wall_{zid}_{side_key}_{idx}", bx0, cur, bx1, g0)
                                            idx += 1
                                        cur = max(cur, g1)
                                    if by1 > cur + 0.5:
                                        _add_wall_rect(f"wall_{zid}_{side_key}_{idx}", bx0, cur, bx1, by1)

                                def _carve_horizontal(band, side_key):
                                    bx0, by0, bx1, by1 = band
                                    gaps = []
                                    for (_cf, _ct, px0, py0, px1, py1) in zpw:
                                        if not (py1 >= by0 and py0 <= by1):
                                            continue
                                        gx0 = max(bx0, px0 - gap_pad)
                                        gx1 = min(bx1, px1 + gap_pad)
                                        if gx1 > gx0:
                                            gaps.append((gx0, gx1))
                                    if not gaps:
                                        _add_wall_rect(f"wall_{zid}_{side_key}", bx0, by0, bx1, by1)
                                        return
                                    gaps.sort(key=lambda t: t[0])
                                    cur = bx0
                                    idx = 0
                                    for (g0, g1) in gaps:
                                        if g0 > cur + 0.5:
                                            _add_wall_rect(f"wall_{zid}_{side_key}_{idx}", cur, by0, g0, by1)
                                            idx += 1
                                        cur = max(cur, g1)
                                    if bx1 > cur + 0.5:
                                        _add_wall_rect(f"wall_{zid}_{side_key}_{idx}", cur, by0, bx1, by1)

                                _carve_vertical(left_band, "left")
                                _carve_vertical(right_band, "right")
                                _carve_horizontal(bottom_band, "bottom")
                                _carve_horizontal(top_band, "top")
                    except Exception:
                        pass

                except Exception:
                    pass

        except Exception:
            pass

        try:
            def _has_external_exit() -> bool:
                try:
                    for _ok, _o in (getattr(dimensions, 'obstacles', {}) or {}).items():
                        if not _o:
                            continue
                        ot_l = str(getattr(_o, 'obstacle_type', '') or '').lower()
                        pk_l = str(getattr(_o, 'portal_kind', '') or '').lower()
                        nm_l = str(getattr(_o, 'obstacle_name', '') or '').lower()
                        cto_l = str(getattr(_o, 'connects_to', '') or '').lower()
                        is_ext = bool(getattr(_o, 'is_external', False))
                        if ot_l == 'exit' or pk_l == 'exit' or is_ext or cto_l in ('outside', 'outdoors', 'street', 'exterior'):
                            return True
                        if 'exit' in nm_l or 'entrance' in nm_l:
                            return True
                except Exception:
                    return False
                return False

            def _add_exit_obstacle(key: str, *, cx: float, cy: float, w: float = 12.0, h: float = 6.0):
                k = str(key)[:64]
                if k in dimensions.obstacles:
                    return
                x0 = float(cx) - (float(w) / 2.0)
                x1 = float(cx) + (float(w) / 2.0)
                y0 = float(cy) - (float(h) / 2.0)
                y1 = float(cy) + (float(h) / 2.0)
                x0 = max(0.0, min(float(width), x0))
                x1 = max(0.0, min(float(width), x1))
                y0 = max(0.0, min(float(height), y0))
                y1 = max(0.0, min(float(height), y1))
                if (x1 - x0) < 1.0 or (y1 - y0) < 1.0:
                    return
                dimensions.obstacles[k] = Obstacle(
                    obstacle_name="Exit" if k == 'exit_main' else "Exit",
                    obstacle_type="exit",
                    boundary_points=[
                        Position(x0, y0),
                        Position(x1, y0),
                        Position(x1, y1),
                        Position(x0, y1),
                    ],
                    blocks_movement=False,
                    blocks_line_of_sight=False,
                    height=2.0,
                    portal_kind="exit",
                    connects_to="outside",
                    is_external=True,
                )

            if auto_add_door and not _has_external_exit():
                lt = str(location_type or '').lower()
                area = float(width) * float(height)

                placements = []
                placements.append(('exit_main', float(width) / 2.0, max(5.0, float(height) * 0.08)))

                if lt in ['interior', 'room', 'building', 'office', 'dorm', 'tavern', 'shop', 'inn', 'temple'] and area >= 26000.0:
                    placements.append(('exit_secondary', float(width) / 2.0, float(height) * 0.92))

                if lt in ['exterior', 'outdoor', 'street', 'district', 'plaza', 'square']:
                    placements.append(('exit_west', max(5.0, float(width) * 0.08), float(height) / 2.0))
                    placements.append(('exit_east', float(width) * 0.92, float(height) / 2.0))

                placements = placements[:3]

                for k, cx, cy in placements:
                    _add_exit_obstacle(k, cx=float(cx), cy=float(cy))
        except Exception:
            pass

        try:
            use_spawns = False
            try:
                use_spawns = str(os.getenv("SPATIAL_GRAPH_ADD_SPAWNS") or "").strip().lower() in (
                    "1", "true", "yes", "on"
                )
            except Exception:
                use_spawns = False

            if use_spawns:
                def _rect_center_from_zone(z: Zone) -> Optional[Tuple[float, float]]:
                    try:
                        c = getattr(z, 'center', None)
                        if c is not None:
                            return (float(getattr(c, 'x', 0.0) or 0.0), float(getattr(c, 'y', 0.0) or 0.0))
                    except Exception:
                        pass
                    try:
                        bps = getattr(z, 'boundary_points', None) or []
                        xs = [float(getattr(p, 'x', 0.0) or 0.0) for p in bps]
                        ys = [float(getattr(p, 'y', 0.0) or 0.0) for p in bps]
                        if xs and ys:
                            return ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
                    except Exception:
                        pass
                    return None

                def _pick_zone_id(pred) -> Optional[str]:
                    try:
                        for zid, z in (getattr(dimensions, 'zones', {}) or {}).items():
                            try:
                                if pred(str(zid), z):
                                    return str(zid)
                            except Exception:
                                continue
                    except Exception:
                        pass
                    return None

                def _add_spawn(key: str, center_xy: Tuple[float, float]):
                    try:
                        cx, cy = float(center_xy[0]), float(center_xy[1])
                        sz = 10.0
                        x0 = max(0.0, min(float(width), cx - (sz / 2.0)))
                        x1 = max(0.0, min(float(width), cx + (sz / 2.0)))
                        y0 = max(0.0, min(float(height), cy - (sz / 2.0)))
                        y1 = max(0.0, min(float(height), cy + (sz / 2.0)))
                        k = str(key)[:64]
                        if k in dimensions.obstacles:
                            return
                        dimensions.obstacles[k] = Obstacle(
                            obstacle_name=k,
                            obstacle_type="spawn",
                            boundary_points=[
                                Position(x0, y0),
                                Position(x1, y0),
                                Position(x1, y1),
                                Position(x0, y1),
                            ],
                            blocks_movement=False,
                            blocks_line_of_sight=False,
                            height=0.1,
                        )
                    except Exception:
                        return

                staff_zone = _pick_zone_id(lambda _id, z: any(k in str(getattr(z, 'zone_name', '') or '').lower() for k in ['back', 'bar']))
                public_zone = _pick_zone_id(lambda _id, z: any(k in str(getattr(z, 'zone_name', '') or '').lower() for k in ['public', 'seating', 'main']))
                entrance_xy = None
                try:
                    md = (getattr(dimensions, 'obstacles', {}) or {}).get('exit_main')
                    if md is None:
                        md = (getattr(dimensions, 'obstacles', {}) or {}).get('main_door')
                    if md:
                        bps = getattr(md, 'boundary_points', None) or []
                        xs = [float(getattr(p, 'x', 0.0) or 0.0) for p in bps]
                        ys = [float(getattr(p, 'y', 0.0) or 0.0) for p in bps]
                        if xs and ys:
                            entrance_xy = ((min(xs) + max(xs)) / 2.0, (min(ys) + max(ys)) / 2.0)
                except Exception:
                    entrance_xy = None

                if entrance_xy is None:
                    entrance_xy = (float(width) / 2.0, max(5.0, float(height) * 0.08))

                _add_spawn('spawn_entrance', entrance_xy)

                if public_zone:
                    z = (getattr(dimensions, 'zones', {}) or {}).get(public_zone)
                    cxy = _rect_center_from_zone(z) if z else None
                    if cxy:
                        _add_spawn('spawn_public', cxy)

                if staff_zone:
                    z = (getattr(dimensions, 'zones', {}) or {}).get(staff_zone)
                    cxy = _rect_center_from_zone(z) if z else None
                    if cxy:
                        _add_spawn('spawn_staff', cxy)
        except Exception:
            pass

        except Exception:
            pass
        
        context = SpatialContext(location_dimensions=dimensions)
        self.contexts[location_name] = context
        self._save()
        
        print(f"[SPATIAL] Created location: {location_name} ({width}x{height} units)")
        return context
    
    def set_current_location(self, location_name: str):
        """Set the current active location"""
        previous_location = self.current_location
        if location_name not in self.contexts:
            # Mixed policy: retry load first, then safe dynamic fallback.
            # 1) Retry: reload from disk in case another system created the location.
            try:
                self._load()
            except Exception:
                pass

        if location_name not in self.contexts:
            # 2) Dynamic fallback: prefer current context dimensions, else last-known dims, else centralized default.
            w, h, loc_type = DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT, 'interior'
            try:
                cur_ctx = self.get_current_context()
                dims = getattr(cur_ctx, 'location_dimensions', None) if cur_ctx else None
                if dims:
                    w = float(getattr(dims, 'width', w) or w)
                    h = float(getattr(dims, 'height', h) or h)
                    loc_type = str(getattr(dims, 'location_type', loc_type) or loc_type)
                else:
                    lw, lh, lt = getattr(self, '_last_known_dimensions', (w, h, loc_type))
                    w = float(lw or w)
                    h = float(lh or h)
                    loc_type = str(lt or loc_type)
            except Exception:
                try:
                    lw, lh, lt = getattr(self, '_last_known_dimensions', (w, h, loc_type))
                    w = float(lw or w)
                    h = float(lh or h)
                    loc_type = str(lt or loc_type)
                except Exception:
                    pass

            print(f"[SPATIAL] Location '{location_name}' not found. Creating with fallback dimensions ({w}x{h}).")
            self.create_location(location_name, width=w, height=h, location_type=str(loc_type or 'interior'))
        
        # Ensure interior locations have at least one door
        self._ensure_door_exists(location_name)
        
        self.current_location = location_name
        print(f"[SPATIAL] Current location: {location_name}")

        # Update last-known dimensions for safe future fallbacks.
        try:
            ctx = self.get_current_context()
            dims = getattr(ctx, 'location_dimensions', None) if ctx else None
            if dims:
                self._last_known_dimensions = (
                    float(getattr(dims, 'width', DEFAULT_MAP_WIDTH) or DEFAULT_MAP_WIDTH),
                    float(getattr(dims, 'height', DEFAULT_MAP_HEIGHT) or DEFAULT_MAP_HEIGHT),
                    str(getattr(dims, 'location_type', 'interior') or 'interior'),
                )
        except Exception:
            pass

        try:
            if previous_location != location_name:
                use_spawn_ua = False
                try:
                    use_spawn_ua = str(os.getenv("SPATIAL_SPAWN_UA_ON_ENTER") or "").strip().lower() in (
                        "1", "true", "yes", "on"
                    )
                except Exception:
                    use_spawn_ua = False

                if use_spawn_ua:
                    ctx = self.get_current_context()
                    dims = getattr(ctx, 'location_dimensions', None) if ctx else None
                    if ctx and dims:
                        spawn_obs = None
                        try:
                            spawn_obs = (getattr(dims, 'obstacles', {}) or {}).get('spawn_entrance')
                        except Exception:
                            spawn_obs = None

                        target = None
                        try:
                            if spawn_obs:
                                bps = getattr(spawn_obs, 'boundary_points', None) or []
                                xs = [float(getattr(p, 'x', 0.0) or 0.0) for p in bps]
                                ys = [float(getattr(p, 'y', 0.0) or 0.0) for p in bps]
                                if xs and ys:
                                    cx = (min(xs) + max(xs)) / 2.0
                                    cy = (min(ys) + max(ys)) / 2.0
                                    target = Position(cx, cy)
                        except Exception:
                            target = None

                        if target is None:
                            try:
                                target = Position(float(getattr(dims, 'width', DEFAULT_MAP_WIDTH) or DEFAULT_MAP_WIDTH) / 2.0, 12.0)
                            except Exception:
                                target = Position(DEFAULT_MAP_WIDTH / 2.0, 12.0)

                        try:
                            target = Position(float(getattr(target, 'x', 0.0) or 0.0), float(getattr(target, 'y', 0.0) or 0.0) + 12.0)
                        except Exception:
                            pass

                        try:
                            for _ in range(6):
                                if dims.is_position_valid(target):
                                    break
                                target = Position(float(getattr(target, 'x', 0.0) or 0.0), float(getattr(target, 'y', 0.0) or 0.0) + 8.0)
                        except Exception:
                            pass

                        try:
                            if not dims.is_position_valid(target):
                                target = dims.get_center()
                        except Exception:
                            try:
                                target = dims.get_center()
                            except Exception:
                                target = Position(DEFAULT_MAP_WIDTH / 2.0, DEFAULT_MAP_HEIGHT / 2.0)

                        try:
                            if isinstance(getattr(ctx, 'actor_positions', None), dict) and 'ua_001' in ctx.actor_positions:
                                self.move_actor('ua_001', target)
                            else:
                                self.add_actor('ua_001', 'UA', target, is_user_actor=True)
                        except Exception:
                            pass
                        try:
                            self._save()
                        except Exception:
                            pass
        except Exception:
            pass

        if previous_location != location_name:
            self._log_world_event(
                event_type="SCENE_TRANSITION",
                summary=f"Location changed: {previous_location or 'None'} -> {location_name}",
                payload={
                    "from_location": previous_location,
                    "to_location": location_name
                },
                importance=6,
                tags=["location", "transition"],
                location_id=location_name
            )
    
    def _ensure_door_exists(self, location_name: str):
        """Ensure an interior location has at least one exit"""
        if location_name not in self.contexts:
            return
        
        context = self.contexts[location_name]
        dims = context.location_dimensions
        
        # Check if it's an interior location
        if dims.location_type.lower() not in ['interior', 'room', 'building', 'office', 'dorm']:
            return
        
        # Check if any exit/door already exists
        has_exit = any('exit' in obs.obstacle_name.lower() or 'door' in obs.obstacle_name.lower() 
                       or obs.obstacle_type.lower() in ['door', 'exit']
                       for obs in dims.obstacles.values())
        
        if not has_exit:
            # Add door at bottom center - matches pygame map EXIT marker position
            door_x = dims.width / 2
            door_y = dims.height * 0.05  # Near bottom edge (y=10 for 200 height)
            door_width = 10.0
            door_height = 5.0
            
            door = Obstacle(
                obstacle_name="Entrance Exit Door",
                obstacle_type="door",
                boundary_points=[
                    Position(door_x - door_width/2, door_y - door_height/2),
                    Position(door_x + door_width/2, door_y - door_height/2),
                    Position(door_x + door_width/2, door_y + door_height/2),
                    Position(door_x - door_width/2, door_y + door_height/2)
                ],
                blocks_movement=False,
                blocks_line_of_sight=False,
                height=2.0
            )
            dims.obstacles["main_door"] = door
            self._save()
            print(f"[SPATIAL] Added main door to {location_name}")
    
    def get_current_context(self) -> Optional[SpatialContext]:
        """Get spatial context for current location"""
        if not self.current_location:
            return None
        return self.contexts.get(self.current_location)
    
    # === ZONE AND OBSTACLE MANAGEMENT ===
    
    def add_zone(self, location_name: str, zone_name: str, center: Position,
                size: tuple, zone_type: str = "area", description: str = ""):
        """
        Add a zone to a location.
        
        Args:
            location_name: Name of the location to add zone to
            zone_name: Unique identifier for the zone
            center: Center position of the zone
            size: (width, height) tuple for zone dimensions
            zone_type: Type of zone (area, passage, room, etc.)
            description: Optional description
        """
        if location_name not in self.contexts:
            print(f"[SPATIAL] Error: Location '{location_name}' not found")
            return
        
        context = self.contexts[location_name]
        dims = context.location_dimensions
        
        # Create boundary points from center and size
        half_w, half_h = size[0] / 2, size[1] / 2
        boundary_points = [
            Position(center.x - half_w, center.y - half_h),
            Position(center.x + half_w, center.y - half_h),
            Position(center.x + half_w, center.y + half_h),
            Position(center.x - half_w, center.y + half_h)
        ]
        
        zone = Zone(
            zone_name=zone_name,
            zone_type=zone_type,
            boundary_points=boundary_points,
            center=center,
            description=description
        )
        
        dims.zones[zone_name] = zone
        self._save()
        print(f"[SPATIAL] Added zone '{zone_name}' to {location_name}")

        self._log_world_event(
            event_type="ZONE_ADDED",
            summary=f"Zone added: {zone_name}",
            payload={
                "zone_name": zone_name,
                "zone_type": zone_type,
                "description": description,
                "location": location_name,
            },
            importance=4,
            tags=["zone", "layout"],
            location_id=location_name
        )
    
    def add_obstacle(self, location_name: str, obstacle_name: str, center: Position,
                     size: tuple, obstacle_type: str = "prop", 
                     blocks_movement: bool = False, blocks_los: bool = False):
        """
        Add an obstacle to a location.
        
        Args:
            location_name: Name of the location to add obstacle to
            obstacle_name: Unique identifier for the obstacle
            center: Center position of the obstacle
            size: (width, height) tuple for obstacle dimensions
            obstacle_type: Type (wall, furniture, prop, etc.)
            blocks_movement: Whether it blocks actor movement
            blocks_los: Whether it blocks line of sight
        """
        if location_name not in self.contexts:
            print(f"[SPATIAL] Error: Location '{location_name}' not found")
            return
        
        context = self.contexts[location_name]
        dims = context.location_dimensions
        
        # Create boundary points from center and size
        half_w, half_h = size[0] / 2, size[1] / 2
        boundary_points = [
            Position(center.x - half_w, center.y - half_h),
            Position(center.x + half_w, center.y - half_h),
            Position(center.x + half_w, center.y + half_h),
            Position(center.x - half_w, center.y + half_h)
        ]
        
        obstacle = Obstacle(
            obstacle_name=obstacle_name,
            obstacle_type=obstacle_type,
            boundary_points=boundary_points,
            blocks_movement=blocks_movement,
            blocks_line_of_sight=blocks_los
        )
        
        dims.obstacles[obstacle_name] = obstacle
        self._save()
        print(f"[SPATIAL] Added obstacle '{obstacle_name}' to {location_name}")

        self._log_world_event(
            event_type="OBSTACLE_ADDED",
            summary=f"Obstacle added: {obstacle_name}",
            payload={
                "obstacle_name": obstacle_name,
                "obstacle_type": obstacle_type,
                "center": {"x": center.x, "y": center.y},
                "size": {"width": float(size[0]), "height": float(size[1])},
                "blocks_movement": bool(blocks_movement),
                "blocks_line_of_sight": bool(blocks_los),
                "location": location_name,
            },
            importance=4,
            tags=["obstacle", "layout"],
            location_id=location_name
        )
    
    # === ACTOR POSITIONING ===
    
    def add_actor(self, actor_id: str, actor_name: str, position: Position, 
                  is_user_actor: bool = False, location: Optional[str] = None, occupation: str = ""):
        """Add actor to spatial context at specific position"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            print(f"[SPATIAL] Error: Cannot add actor, no valid location")
            return
        
        context = self.contexts[loc]
        
        # Validate position
        if not context.location_dimensions.is_position_valid(position):
            print(f"[SPATIAL] Warning: Position ({position.x}, {position.y}) out of bounds, clamping")
            position.x = max(0, min(position.x, context.location_dimensions.width))
            position.y = max(0, min(position.y, context.location_dimensions.height))
        
        actor_pos = ActorPosition(
            actor_id=actor_id,
            actor_name=actor_name,
            position=position,
            is_user_actor=is_user_actor,
            is_active=True,
            occupation=occupation or ""
        )
        
        context.actor_positions[actor_id] = actor_pos
        self._save()

        try:
            z = None
            try:
                dims = context.location_dimensions
                for zn, zone in getattr(dims, 'zones', {}).items():
                    try:
                        if zone and hasattr(zone, 'contains_point') and zone.contains_point(position):
                            z = str(zn)
                            break
                    except Exception:
                        continue
            except Exception:
                z = None
            if z is not None:
                self._last_actor_zone[str(actor_id)] = f"{loc}||{z}"
            else:
                self._last_actor_zone[str(actor_id)] = f"{loc}||"
        except Exception:
            pass
        
        print(f"[SPATIAL] Added {actor_name} at ({position.x:.1f}, {position.y:.1f})")

        self._log_world_event(
            event_type="ACTOR_ADDED",
            summary=f"Actor added: {actor_name}",
            payload={
                "actor_id": actor_id,
                "actor_name": actor_name,
                "is_user_actor": bool(is_user_actor),
                "location": loc,
                "position": {"x": position.x, "y": position.y},
            },
            importance=6,
            tags=["actor", "spawn"],
            location_id=loc
        )
    
    def move_actor(self, actor_id: str, new_position: Position, location: Optional[str] = None):
        """
        Move actor to new position with trail tracking.
        
        Updates position, adds old position to trail, calculates facing direction.
        """
        import time as time_module
        
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return
        
        context = self.contexts[loc]
        if actor_id not in context.actor_positions:
            print(f"[SPATIAL] Warning: Actor {actor_id} not found in location")
            return
        
        # Validate position
        dims = context.location_dimensions
        if not dims.is_position_valid(new_position):
            new_position.x = max(0, min(new_position.x, dims.width))
            new_position.y = max(0, min(new_position.y, dims.height))
        
        actor = context.actor_positions[actor_id]
        old_pos = actor.position

        old_zone = None
        new_zone = None
        try:
            dims = context.location_dimensions
            for zn, zone in getattr(dims, 'zones', {}).items():
                try:
                    if zone and hasattr(zone, 'contains_point') and zone.contains_point(old_pos):
                        old_zone = str(zn)
                        break
                except Exception:
                    continue
        except Exception:
            old_zone = None

        # Calculate distance moved
        distance = old_pos.distance_to(new_position)
        
        # Only track trail if moved more than 0.5 units
        if distance > 0.5:
            actor.add_trail_point(old_pos, time_module.time())
            actor.clean_old_trail_points()  # Remove old trail points
        
        # Update position
        actor.position = new_position
        self._save()

        try:
            dims = context.location_dimensions
            for zn, zone in getattr(dims, 'zones', {}).items():
                try:
                    if zone and hasattr(zone, 'contains_point') and zone.contains_point(new_position):
                        new_zone = str(zn)
                        break
                except Exception:
                    continue
        except Exception:
            new_zone = None

        try:
            key = str(actor_id)
            last_key = self._last_actor_zone.get(key)
            expected = f"{loc}||{new_zone or ''}"
            if last_key is None:
                last_key = f"{loc}||{old_zone or ''}"
            if expected != last_key:
                prev_zone = None
                try:
                    parts = str(last_key).split('||', 1)
                    if len(parts) == 2 and parts[0] == str(loc):
                        prev_zone = parts[1] or None
                except Exception:
                    prev_zone = old_zone

                if prev_zone and prev_zone != new_zone:
                    self._log_world_event(
                        event_type="ZONE_EXITED",
                        summary=f"Actor left zone: {actor.actor_name} left {prev_zone}",
                        payload={
                            "actor_id": actor_id,
                            "actor_ids": [actor_id],
                            "disable_auto_memory_seed": True,
                            "actor_name": actor.actor_name,
                            "location": loc,
                            "zone": prev_zone,
                            "to_zone": new_zone,
                            "from": {"x": old_pos.x, "y": old_pos.y},
                            "to": {"x": new_position.x, "y": new_position.y},
                        },
                        importance=4,
                        tags=["zone", "movement"],
                        location_id=loc
                    )

                if new_zone and new_zone != prev_zone:
                    self._log_world_event(
                        event_type="ZONE_ENTERED",
                        summary=f"Actor entered zone: {actor.actor_name} entered {new_zone}",
                        payload={
                            "actor_id": actor_id,
                            "actor_ids": [actor_id],
                            "disable_auto_memory_seed": True,
                            "actor_name": actor.actor_name,
                            "location": loc,
                            "zone": new_zone,
                            "from_zone": prev_zone,
                            "from": {"x": old_pos.x, "y": old_pos.y},
                            "to": {"x": new_position.x, "y": new_position.y},
                        },
                        importance=4,
                        tags=["zone", "movement"],
                        location_id=loc
                    )

                self._last_actor_zone[key] = expected
        except Exception:
            pass

        should_log_movement = True
        try:
            # Meaningful distance threshold
            meaningful_distance = 25.0
            if float(distance) < meaningful_distance:
                should_log_movement = False

            # Coarse cell-change gating (reduces jitter logs): 5-unit buckets
            try:
                cell_size = 5.0
                cx = int(float(new_position.x) // cell_size)
                cy = int(float(new_position.y) // cell_size)
                cell = (str(loc), cx, cy)
                last_cell = self._last_actor_move_cell.get(str(actor_id))
                if last_cell is not None and cell == last_cell:
                    should_log_movement = False
            except Exception:
                pass

            # Time cadence fallback (if world time available)
            world_time = self._get_current_world_time()
            wms = world_time.minutes_since_start if world_time else None
            if wms is not None:
                last_wms = self._last_actor_move_world_minutes.get(str(actor_id))
                # Log at least once every 10 minutes even for small jitters
                if last_wms is None or (int(wms) - int(last_wms) >= 10):
                    should_log_movement = True
        except Exception:
            should_log_movement = True

        if should_log_movement:
            self._log_world_event(
                event_type="ACTOR_MOVED",
                summary=f"Actor moved: {actor.actor_name}",
                payload={
                    "actor_id": actor_id,
                    "actor_name": actor.actor_name,
                    "location": loc,
                    "from": {"x": old_pos.x, "y": old_pos.y},
                    "to": {"x": new_position.x, "y": new_position.y},
                    "distance": float(distance),
                    "facing_direction": float(getattr(actor, 'facing_direction', 0.0)),
                },
                importance=3,
                tags=["actor", "movement"],
                location_id=loc
            )

            try:
                world_time = self._get_current_world_time()
                wms = world_time.minutes_since_start if world_time else None
                if wms is not None:
                    self._last_actor_move_world_minutes[str(actor_id)] = int(wms)
                try:
                    cell_size = 5.0
                    cx = int(float(new_position.x) // cell_size)
                    cy = int(float(new_position.y) // cell_size)
                    self._last_actor_move_cell[str(actor_id)] = (str(loc), cx, cy)
                except Exception:
                    pass
            except Exception:
                pass
        
        # Log with trail info
        trail_dist = actor.get_trail_distance()
        speed = actor.get_average_speed()
        print(f"[SPATIAL] Moved {actor.actor_name}: ({old_pos.x:.1f}, {old_pos.y:.1f}) → "
              f"({new_position.x:.1f}, {new_position.y:.1f}) | "
              f"Trail: {trail_dist:.1f}m | Speed: {speed:.1f}m/s")
    
    def clear_actor_trail(self, actor_id: str, location: Optional[str] = None):
        """Clear an actor's movement trail"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return
        
        context = self.contexts[loc]
        if actor_id in context.actor_positions:
            actor = context.actor_positions[actor_id]
            actor.trail.clear()
            self._save()
            print(f"[SPATIAL] Cleared trail for {actor.actor_name}")
    
    def clear_all_trails(self, location: Optional[str] = None):
        """Clear all actor trails in a location"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return
        
        context = self.contexts[loc]
        for actor in context.actor_positions.values():
            actor.trail.clear()
        self._save()
        print(f"[SPATIAL] Cleared all trails in {loc}")
    
    def remove_actor(self, actor_id: str, location: Optional[str] = None):
        """Remove actor from spatial context"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return
        
        context = self.contexts[loc]
        if actor_id in context.actor_positions:
            actor_name = context.actor_positions[actor_id].actor_name
            del context.actor_positions[actor_id]
            self._save()
            print(f"[SPATIAL] Removed {actor_name} from location")
    
    def get_actor_position(self, actor_id: str, location: Optional[str] = None) -> Optional[Position]:
        """Get actor's current position"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return None
        
        context = self.contexts[loc]
        actor_pos = context.actor_positions.get(actor_id)
        return actor_pos.position if actor_pos else None
    
    # === DISTANCE CALCULATIONS ===
    
    def get_distance(self, actor_id_1: str, actor_id_2: str, location: Optional[str] = None) -> Optional[float]:
        """Calculate distance between two actors"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return None
        
        context = self.contexts[loc]
        pos1 = context.actor_positions.get(actor_id_1)
        pos2 = context.actor_positions.get(actor_id_2)
        
        if not pos1 or not pos2:
            return None
        
        return pos1.position.distance_to(pos2.position)
    
    def get_distance_category(self, actor_id_1: str, actor_id_2: str, 
                             location: Optional[str] = None) -> Optional[DistanceCategory]:
        """Get distance category between two actors"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return None
        
        context = self.contexts[loc]
        pos1 = context.actor_positions.get(actor_id_1)
        pos2 = context.actor_positions.get(actor_id_2)
        
        if not pos1 or not pos2:
            return None
        
        return pos1.position.get_distance_category(pos2.position)
    
    def get_actors_within_range(self, actor_id: str, max_distance: float, 
                                location: Optional[str] = None) -> List[ActorPosition]:
        """Get all actors within specified distance"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return []
        
        context = self.contexts[loc]
        source_pos = context.actor_positions.get(actor_id)
        if not source_pos:
            return []
        
        nearby_actors = []
        for other_id, other_pos in context.actor_positions.items():
            if other_id == actor_id:
                continue
            
            distance = source_pos.position.distance_to(other_pos.position)
            if distance <= max_distance:
                nearby_actors.append(other_pos)
        
        return nearby_actors
    
    # === POSSIBLE ACTORS (PRE-SEEDED POOL) ===
    
    def add_possible_actor(self, actor_id: str, actor_name: str, actor_type: str,
                          brief_description: str, narrative_role: str,
                          introduction_triggers: List[str] = None,
                          location: Optional[str] = None):
        """Add a possible actor to the pre-seeded pool"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            print(f"[SPATIAL] Error: Cannot add possible actor, no valid location")
            return
        
        context = self.contexts[loc]
        possible_actor = PossibleActor(
            actor_id=actor_id,
            actor_name=actor_name,
            actor_type=actor_type,
            brief_description=brief_description,
            narrative_role=narrative_role,
            introduction_triggers=introduction_triggers or [],
            has_been_introduced=False
        )
        
        context.possible_actors[actor_id] = possible_actor
        self._save()
        
        print(f"[SPATIAL] Added possible {actor_type}: {actor_name} ({narrative_role})")
    
    def get_possible_actors(self, location: Optional[str] = None, 
                           only_unintroduced: bool = False) -> List[PossibleActor]:
        """Get list of possible actors for location"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return []
        
        context = self.contexts[loc]
        actors = list(context.possible_actors.values())
        
        if only_unintroduced:
            actors = [a for a in actors if not a.has_been_introduced]
        
        return actors
    
    def mark_actor_introduced(self, actor_id: str, location: Optional[str] = None):
        """Mark a possible actor as having been introduced"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return
        
        context = self.contexts[loc]
        if actor_id in context.possible_actors:
            context.possible_actors[actor_id].has_been_introduced = True
            self._save()
            print(f"[SPATIAL] Marked {context.possible_actors[actor_id].actor_name} as introduced")
    
    def can_introduce_actor(self, actor_id: str, user_input: str, 
                           location: Optional[str] = None) -> bool:
        """Check if actor can be introduced based on triggers"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return False
        
        context = self.contexts[loc]
        possible_actor = context.possible_actors.get(actor_id)
        
        if not possible_actor or possible_actor.has_been_introduced:
            return False
        
        # Check if any trigger keywords match user input
        user_lower = user_input.lower()
        for trigger in possible_actor.introduction_triggers:
            if trigger.lower() in user_lower:
                return True
        
        return False
    
    # === ACTION FEASIBILITY ===
    
    def is_action_feasible(self, actor_id: str, target_id: str, action_type: str,
                          location: Optional[str] = None) -> Tuple[bool, str]:
        """
        Check if action is feasible based on distance.
        
        Returns: (is_feasible, reason)
        """
        distance_cat = self.get_distance_category(actor_id, target_id, location)
        
        if not distance_cat:
            return False, "Actors not in same location"
        
        # Define action range requirements
        action_ranges = {
            "touch": [DistanceCategory.IMMEDIATE],
            "whisper": [DistanceCategory.IMMEDIATE, DistanceCategory.CLOSE],
            "talk": [DistanceCategory.IMMEDIATE, DistanceCategory.CLOSE, DistanceCategory.NEAR],
            "shout": [DistanceCategory.IMMEDIATE, DistanceCategory.CLOSE, DistanceCategory.NEAR, 
                     DistanceCategory.FAR],
            "melee": [DistanceCategory.IMMEDIATE],
            "throw": [DistanceCategory.IMMEDIATE, DistanceCategory.CLOSE, DistanceCategory.NEAR],
            "ranged": [DistanceCategory.IMMEDIATE, DistanceCategory.CLOSE, DistanceCategory.NEAR, 
                      DistanceCategory.FAR, DistanceCategory.DISTANT]
        }
        
        required_range = action_ranges.get(action_type.lower())
        if not required_range:
            # Unknown action type, assume close range
            required_range = [DistanceCategory.IMMEDIATE, DistanceCategory.CLOSE]
        
        if distance_cat in required_range:
            return True, f"Action feasible at {distance_cat.value} range"
        else:
            return False, f"Target too {distance_cat.value} for {action_type}"
    
    def get_movement_time(self, actor_id: str, target_position: Position,
                         speed: MovementSpeed = MovementSpeed.WALK,
                         swiftness: int = 3,
                         location: Optional[str] = None,
                         return_details: bool = False) -> Optional[int | Tuple[float, int]]:
        """
        Calculate time required to move to target position.
        
        Args:
            actor_id: ID of actor moving
            target_position: Destination position
            speed: Movement speed (default: WALK = 2 units/second)
            swiftness: Actor's Swiftness S-trait (1-5, default: 3)
            location: Location name (uses current if None)
            return_details: If True, returns (seconds, UT) tuple; if False, returns UT only
        
        Returns:
            If return_details=False: Unit Time (int)
            If return_details=True: Tuple of (seconds, unit_time)
        
        Examples (Swiftness 3 = +1.0 u/s):
            - 2 units at WALK (3.0 u/s): 0.67 seconds = 1 UT
            - 6 units at WALK (3.0 u/s): 2.0 seconds = 1 UT
            - 10 units at WALK (3.0 u/s): 3.33 seconds = 2 UT
            - 10 units at RUN (6.0 u/s): 1.67 seconds = 1 UT
        """
        current_pos = self.get_actor_position(actor_id, location)
        if not current_pos:
            return None
        
        if return_details:
            return current_pos.calculate_movement_time_with_ut(target_position, speed, swiftness)
        else:
            _, unit_time = current_pos.calculate_movement_time_with_ut(target_position, speed, swiftness)
            return unit_time
    
    def get_movement_time_between_positions(self, start: Position, end: Position,
                                           speed: MovementSpeed = MovementSpeed.WALK,
                                           swiftness: int = 3,
                                           return_details: bool = False) -> int | Tuple[float, int]:
        """
        Calculate movement time between two positions.
        
        Args:
            start: Starting position
            end: Ending position
            speed: Movement speed
            swiftness: Actor's Swiftness S-trait (1-5, default: 3)
            return_details: If True, returns (seconds, UT); if False, returns UT only
        
        Returns:
            If return_details=False: Unit Time (int)
            If return_details=True: Tuple of (seconds, unit_time)
        """
        if return_details:
            return start.calculate_movement_time_with_ut(end, speed, swiftness)
        else:
            _, unit_time = start.calculate_movement_time_with_ut(end, speed, swiftness)
            return unit_time
    
    # === LLM CONTEXT GENERATION ===
    
    def get_spatial_context_for_llm(self, ua_actor_id: str = "ua_001", 
                                    location: Optional[str] = None) -> str:
        """
        Generate spatial context string for LLM prompts.
        
        This provides the narrator/LLM with accurate spatial information about:
        - Current location type and size
        - UA's position and current zone
        - Other actors and their distances from UA
        - Nearby obstacles and features
        
        Args:
            ua_actor_id: User Actor's ID (default: "ua_001")
            location: Location name (uses current if None)
            
        Returns:
            Formatted string with spatial context for LLM
        """
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return ""
        
        context = self.contexts[loc]
        dims = context.location_dimensions
        
        # Get UA position - try ID first, then name, then any UA
        ua_pos = context.actor_positions.get(ua_actor_id)
        if not ua_pos:
            # Try by name (case-insensitive)
            ua_id_lower = ua_actor_id.lower()
            for aid, apos in context.actor_positions.items():
                if apos.actor_name.lower() == ua_id_lower:
                    ua_pos = apos
                    break
        if not ua_pos:
            # Fallback to any user actor
            for aid, apos in context.actor_positions.items():
                if apos.is_user_actor:
                    ua_pos = apos
                    break
        if not ua_pos:
            return ""
        
        lines = []
        
        # Location info
        is_exterior = dims.location_type.lower() in ['exterior', 'outdoor', 'outside', 'street', 'plaza', 'park', 'yard']
        loc_type = "outdoor" if is_exterior else "indoor"
        lines.append(f"**SPATIAL CONTEXT:**")
        lines.append(f"- Location: {dims.location_name} ({loc_type}, {dims.width}×{dims.height} units)")
        
        # UA's current zone
        ua_zone = dims.get_zone_at_position(ua_pos.position)
        if ua_zone:
            lines.append(f"- You are in: {ua_zone.zone_name}")
        lines.append(f"- Your position: ({ua_pos.position.x:.0f}, {ua_pos.position.y:.0f})")
        
        # Other actors with distances
        other_actors = []
        for actor_id, actor_pos in context.actor_positions.items():
            if actor_id == ua_actor_id:
                continue
            
            distance = ua_pos.position.distance_to(actor_pos.position)
            distance_cat = ua_pos.position.get_distance_category(actor_pos.position)
            actor_zone = dims.get_zone_at_position(actor_pos.position)
            zone_name = actor_zone.zone_name if actor_zone else "unknown area"
            
            other_actors.append(f"  - {actor_pos.actor_name}: {distance:.1f} units away ({distance_cat.value}), in {zone_name}")
        
        if other_actors:
            lines.append(f"- Other people present:")
            lines.extend(other_actors)
        else:
            lines.append(f"- No other people in this location")
        
        # Nearby obstacles (within 10 units)
        nearby_obstacles = []
        for obs_id, obstacle in dims.obstacles.items():
            if obstacle.boundary_points:
                # Get center of obstacle
                center_x = sum(p.x for p in obstacle.boundary_points) / len(obstacle.boundary_points)
                center_y = sum(p.y for p in obstacle.boundary_points) / len(obstacle.boundary_points)
                obs_pos = Position(center_x, center_y)
                distance = ua_pos.position.distance_to(obs_pos)
                
                if distance <= 10:
                    nearby_obstacles.append(f"  - {obstacle.obstacle_name}: {distance:.1f} units away")
        
        if nearby_obstacles:
            lines.append(f"- Nearby objects/features:")
            lines.extend(nearby_obstacles[:5])  # Limit to 5
        
        # Available zones
        if dims.zones:
            zone_names = [z.zone_name for z in list(dims.zones.values())[:5]]
            lines.append(f"- Areas in location: {', '.join(zone_names)}")
        
        return "\n".join(lines)
    
    # === PERSISTENCE ===
    
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

            self._persist_position_snapshot()
        except Exception as e:
            print(f"[SPATIAL] Error saving: {e}")

    def _get_context_store(self) -> Optional['ContextStore']:
        if ContextStore is None:
            return None
        if self._context_store is None:
            try:
                db_path = Path("simulation_data/context/context.db")
                self._context_store = ContextStore(db_path)
            except Exception:
                self._context_store = None
        return self._context_store

    def _get_current_world_time(self) -> Optional['WorldTime']:
        try:
            if get_master_time_coordinator is None or WorldTime is None:
                return None
            tc = get_master_time_coordinator()
            time_ctx = tc.get_current_time_context() if tc else None
            gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
            if gt is None:
                return None
            return WorldTime(
                day=getattr(gt, 'day', 1),
                hour=getattr(gt, 'hour', 0),
                minute=getattr(gt, 'minute', 0)
            )
        except Exception:
            return None

    def _log_world_event(self, event_type: str, summary: str, payload: Optional[Dict[str, Any]] = None,
                         importance: int = 5, tags: Optional[List[str]] = None,
                         location_id: Optional[str] = None) -> None:
        store = self._get_context_store()
        if store is None:
            return
        try:
            world_time = self._get_current_world_time()
            event_id = store.log_world_event(
                session_id=self.session_id,
                location_id=location_id if location_id is not None else self.current_location,
                event_type=event_type,
                summary=summary,
                importance=importance,
                tags=tags,
                payload=payload,
                world_time=world_time
            )

            # Best-effort: seed per-actor long-term memory from authoritative events
            try:
                if hasattr(store, 'remember'):
                    p = payload or {}

                    # Memory noise reduction: skip seeding for high-frequency low-signal movement.
                    # We still store the world_event row; we just avoid spamming long-term memory.
                    if str(event_type) == 'ACTOR_MOVED':
                        try:
                            dist = float(p.get('distance', 0.0) or 0.0)
                            if int(importance) <= 3 and dist < 25.0:
                                return
                        except Exception:
                            if int(importance) <= 3:
                                return

                    actor_ids = []
                    if isinstance(p.get('actor_ids'), list):
                        actor_ids.extend([str(x) for x in p.get('actor_ids') if x])
                    if p.get('actor_id'):
                        actor_ids.append(str(p.get('actor_id')))
                    # De-dupe, preserve order
                    seen = set()
                    actor_ids = [x for x in actor_ids if not (x in seen or seen.add(x))]

                    for aid in actor_ids:
                        store.remember(
                            session_id=self.session_id,
                            actor_id=aid,
                            memory_type=str(event_type).lower(),
                            content=str(summary),
                            importance=int(importance),
                            pinned=False,
                            source_event_id=int(event_id) if event_id is not None else None,
                            world_time=world_time
                        )
            except Exception:
                pass
        except Exception:
            return

    def _persist_position_snapshot(self) -> None:
        """Best-effort: persist spatial state into long-term context DB."""
        store = self._get_context_store()
        if store is None:
            return

        loc = self.current_location
        if not loc or loc not in self.contexts:
            return

        context = self.contexts[loc]
        dims = context.location_dimensions

        entities: List[Dict[str, Any]] = []

        # Actors
        for actor_id, apos in context.actor_positions.items():
            entities.append({
                "entity_id": actor_id,
                "entity_name": apos.actor_name,
                "entity_type": "actor",
                "x": getattr(apos.position, 'x', None),
                "y": getattr(apos.position, 'y', None),
                "facing_direction": getattr(apos, 'facing_direction', None),
                "is_active": getattr(apos, 'is_active', True),
                "zone_id": None,
            })

        # Obstacles (store centroid so we can reconstruct spatial layout later)
        for obs_id, obs in dims.obstacles.items():
            cx = None
            cy = None
            try:
                if getattr(obs, 'boundary_points', None):
                    pts = obs.boundary_points
                    cx = sum(p.x for p in pts) / len(pts)
                    cy = sum(p.y for p in pts) / len(pts)
            except Exception:
                cx = None
                cy = None

            entities.append({
                "entity_id": obs_id,
                "entity_name": getattr(obs, 'obstacle_name', obs_id),
                "entity_type": "obstacle",
                "x": cx,
                "y": cy,
                "facing_direction": None,
                "is_active": True,
                "zone_id": None,
            })

        if not entities:
            return

        world_time = self._get_current_world_time()

        try:
            sig_parts = []
            for e in entities:
                eid = str(e.get('entity_id'))
                etype = str(e.get('entity_type'))
                x = e.get('x')
                y = e.get('y')
                fd = e.get('facing_direction')
                ia = 1 if e.get('is_active', True) else 0
                zid = e.get('zone_id')
                try:
                    xq = None if x is None else round(float(x), 1)
                except Exception:
                    xq = None
                try:
                    yq = None if y is None else round(float(y), 1)
                except Exception:
                    yq = None
                try:
                    fdq = None if fd is None else round(float(fd), 1)
                except Exception:
                    fdq = None
                sig_parts.append((eid, etype, xq, yq, fdq, int(ia), str(zid) if zid is not None else None))
            sig_parts.sort(key=lambda t: (t[1], t[0]))
            signature = tuple(sig_parts)

            last_sig = self._last_position_snapshot_signature.get(loc)
            wms = world_time.minutes_since_start if (world_time is not None) else None
            last_wms = self._last_position_snapshot_world_minutes.get(loc)

            if last_sig is not None and signature == last_sig:
                if wms is None:
                    return
                if last_wms is not None and int(wms) - int(last_wms) < 3:
                    return
        except Exception:
            signature = None
            wms = world_time.minutes_since_start if (world_time is not None) else None

        try:
            store.record_position_snapshot(
                session_id=self.session_id,
                location_id=loc,
                entities=entities,
                world_time=world_time
            )

            try:
                if signature is not None:
                    self._last_position_snapshot_signature[loc] = signature
                if wms is not None:
                    self._last_position_snapshot_world_minutes[loc] = int(wms)
            except Exception:
                pass
        except Exception:
            # Never block simulation saves
            return
    
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

                try:
                    mutated = False
                    for _k, _ctx in (self.contexts or {}).items():
                        if _ctx is None:
                            continue
                        if self._normalize_loaded_context(_ctx):
                            mutated = True
                    if mutated:
                        try:
                            self._save()
                        except Exception:
                            pass
                except Exception:
                    pass
                
                print(f"[SPATIAL] Loaded {len(self.contexts)} location(s)")
        except Exception as e:
            print(f"[SPATIAL] Error loading: {e}")
    
    def get_spatial_info_for_query(self, actor_id: str, query: str, location: Optional[str] = None) -> str:
        """
        Get spatial information relevant to a user query for internal voice.
        
        Dynamically matches query terms against actual spatial objects/zones.
        
        Args:
            actor_id: Can be actor ID (e.g., "ua_001") OR actor name (e.g., "Marcus")
            query: The user's question
            location: Optional location override
        """
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return ""
        
        context = self.contexts[loc]
        
        # Try direct ID lookup first
        actor_pos = context.actor_positions.get(actor_id)
        
        # If not found, search by name (case-insensitive)
        if not actor_pos:
            actor_id_lower = actor_id.lower()
            for aid, apos in context.actor_positions.items():
                if apos.actor_name.lower() == actor_id_lower:
                    actor_pos = apos
                    break
        
        # If still not found, try to use the UA (user actor)
        if not actor_pos:
            for aid, apos in context.actor_positions.items():
                if apos.is_user_actor:
                    actor_pos = apos
                    break
        
        if not actor_pos:
            return ""
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        info_parts = []
        
        # === DYNAMIC OBJECT/ZONE MATCHING ===
        # Search for any query word that matches obstacle or zone names
        matched_objects = []
        
        dims = context.location_dimensions
        for obs_name, obs in dims.obstacles.items():
            obs_words = set(obs_name.lower().replace('_', ' ').replace('-', ' ').split())
            # Check if any query word matches any word in obstacle name
            if query_words & obs_words:  # Set intersection
                # Calculate obstacle center from boundary points
                if obs.boundary_points:
                    cx = sum(p.x for p in obs.boundary_points) / len(obs.boundary_points)
                    cy = sum(p.y for p in obs.boundary_points) / len(obs.boundary_points)
                    obs_center = Position(cx, cy)
                    dist = actor_pos.position.distance_to(obs_center)
                    direction = actor_pos.position.get_cardinal_direction(obs_center)
                    matched_objects.append((obs_name, dist, direction, 'object'))
        
        for zone_name, zone in dims.zones.items():
            zone_words = set(zone_name.lower().replace('_', ' ').replace('-', ' ').split())
            if query_words & zone_words:
                # Use zone center (calculated in __post_init__) or calculate from boundary
                if zone.center:
                    zone_center = zone.center
                elif zone.boundary_points:
                    cx = sum(p.x for p in zone.boundary_points) / len(zone.boundary_points)
                    cy = sum(p.y for p in zone.boundary_points) / len(zone.boundary_points)
                    zone_center = Position(cx, cy)
                else:
                    continue
                dist = actor_pos.position.distance_to(zone_center)
                direction = actor_pos.position.get_cardinal_direction(zone_center)
                matched_objects.append((zone_name, dist, direction, 'zone'))
        
        # === DYNAMIC ACTOR MATCHING ===
        # Check if query mentions any actor names
        for other_id, other_pos in context.actor_positions.items():
            if other_id == actor_id:
                continue
            name_words = set(other_pos.actor_name.lower().split())
            if query_words & name_words:
                dist = actor_pos.position.distance_to(other_pos.position)
                direction = actor_pos.position.get_cardinal_direction(other_pos.position)
                matched_objects.append((other_pos.actor_name, dist, direction, 'person'))
        
        # === CONTEXTUAL QUERIES (distance, nearby, where, etc.) ===
        # These provide general spatial context even without specific matches
        is_distance_query = any(w in query_lower for w in ['far', 'distance', 'close', 'near', 'how long', 'reach'])
        is_location_query = any(w in query_lower for w in ['where', 'location', 'position', 'am i'])
        is_nearby_query = any(w in query_lower for w in ['around', 'nearby', 'surroundings', 'see', 'visible'])
        is_people_query = any(w in query_lower for w in ['who', 'anyone', 'someone', 'people', 'person'])
        is_exit_query = any(w in query_lower for w in ['exit', 'door', 'way out', 'leave', 'entrance', 'gateway'])
        
        # === EXIT/DOOR QUERIES ===
        # Look for exits, doors, entrances in obstacles or at map edges
        if is_exit_query and not matched_objects:
            exit_candidates = []
            
            # Check for exit-related obstacles
            exit_keywords = ['exit', 'door', 'entrance', 'gateway', 'portal', 'hatch', 'passage', 'corridor']
            for obs_name, obs in dims.obstacles.items():
                obs_lower = obs_name.lower()
                if any(kw in obs_lower for kw in exit_keywords):
                    # Calculate obstacle center from boundary points
                    if obs.boundary_points:
                        cx = sum(p.x for p in obs.boundary_points) / len(obs.boundary_points)
                        cy = sum(p.y for p in obs.boundary_points) / len(obs.boundary_points)
                        obs_center = Position(cx, cy)
                        dist = actor_pos.position.distance_to(obs_center)
                        direction = actor_pos.position.get_cardinal_direction(obs_center)
                        exit_candidates.append((obs_name, dist, direction))
            
            # Check for exit-related zones
            for zone_name, zone in dims.zones.items():
                zone_lower = zone_name.lower()
                if any(kw in zone_lower for kw in exit_keywords):
                    # Use zone center or calculate from boundary
                    if zone.center:
                        zone_center = zone.center
                    elif zone.boundary_points:
                        cx = sum(p.x for p in zone.boundary_points) / len(zone.boundary_points)
                        cy = sum(p.y for p in zone.boundary_points) / len(zone.boundary_points)
                        zone_center = Position(cx, cy)
                    else:
                        continue
                    dist = actor_pos.position.distance_to(zone_center)
                    direction = actor_pos.position.get_cardinal_direction(zone_center)
                    exit_candidates.append((zone_name, dist, direction))
            
            # If no explicit exits found, calculate distance to map edges as potential exits
            if not exit_candidates:
                edges = [
                    ("North edge", Position(actor_pos.position.x, 0)),
                    ("South edge", Position(actor_pos.position.x, dims.height)),
                    ("West edge", Position(0, actor_pos.position.y)),
                    ("East edge", Position(dims.width, actor_pos.position.y))
                ]
                for edge_name, edge_pos in edges:
                    dist = actor_pos.position.distance_to(edge_pos)
                    direction = actor_pos.position.get_cardinal_direction(edge_pos)
                    exit_candidates.append((edge_name, dist, direction))
            
            if exit_candidates:
                exit_candidates.sort(key=lambda x: x[1])
                nearest = exit_candidates[0]
                info_parts.append(f"NEAREST EXIT: {nearest[0]} - approximately {nearest[1]:.0f} meters to the {nearest[2]}")
                if len(exit_candidates) > 1:
                    info_parts.append("Other exits:")
                    for name, dist, direction in exit_candidates[1:4]:
                        info_parts.append(f"  - {name}: ~{dist:.0f} meters {direction}")
        
        # Add matched objects to results
        if matched_objects:
            matched_objects.sort(key=lambda x: x[1])  # Sort by distance
            for name, dist, direction, obj_type in matched_objects[:5]:
                info_parts.append(f"- {name}: ~{dist:.0f} meters to the {direction}")
        
        # If distance/nearby query but no specific matches, list closest objects
        if (is_distance_query or is_nearby_query) and not matched_objects:
            all_objects = []
            for obs_name, obs in dims.obstacles.items():
                # Calculate obstacle center from boundary points
                if obs.boundary_points:
                    cx = sum(p.x for p in obs.boundary_points) / len(obs.boundary_points)
                    cy = sum(p.y for p in obs.boundary_points) / len(obs.boundary_points)
                    obs_center = Position(cx, cy)
                    dist = actor_pos.position.distance_to(obs_center)
                    direction = actor_pos.position.get_cardinal_direction(obs_center)
                    all_objects.append((obs_name, dist, direction))
            
            if all_objects:
                all_objects.sort(key=lambda x: x[1])
                info_parts.append("Nearby objects:")
                for name, dist, direction in all_objects[:5]:
                    info_parts.append(f"  - {name}: ~{dist:.0f} meters {direction}")
        
        # Location context
        if is_location_query:
            info_parts.append(f"- Current location: {context.location_dimensions.location_name}")
            for zone_name, zone in dims.zones.items():
                if zone.contains_point(actor_pos.position):
                    info_parts.append(f"- Currently in: {zone_name}")
                    break
        
        # People nearby
        if is_people_query and not any(obj[3] == 'person' for obj in matched_objects if len(obj) > 3):
            nearby_actors = []
            for other_id, other_pos in context.actor_positions.items():
                if other_id == actor_id:
                    continue
                dist = actor_pos.position.distance_to(other_pos.position)
                direction = actor_pos.position.get_cardinal_direction(other_pos.position)
                nearby_actors.append((other_pos.actor_name, dist, direction))
            
            if nearby_actors:
                nearby_actors.sort(key=lambda x: x[1])
                for name, dist, direction in nearby_actors[:5]:
                    info_parts.append(f"- {name}: ~{dist:.0f} meters {direction}")
            else:
                info_parts.append("- No one else visible in immediate area")
        
        if info_parts:
            return "SPATIAL INFORMATION:\n" + "\n".join(info_parts)
        return ""
    
    def get_summary(self, location: Optional[str] = None) -> str:
        """Get human-readable summary of spatial context"""
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return "No spatial context available"
        
        context = self.contexts[loc]
        dims = context.location_dimensions
        
        summary = f"""
=== SPATIAL CONTEXT: {dims.location_name} ===
Dimensions: {dims.width}x{dims.height} units ({dims.location_type})
Description: {dims.description}

Active Actors ({len(context.actor_positions)}):
"""
        for actor_pos in context.actor_positions.values():
            summary += f"  - {actor_pos.actor_name} at ({actor_pos.position.x:.1f}, {actor_pos.position.y:.1f})\n"
        
        summary += f"\nPossible Actors ({len(context.possible_actors)}):\n"
        for possible in context.possible_actors.values():
            status = "✓ Introduced" if possible.has_been_introduced else "○ Not yet introduced"
            summary += f"  - {possible.actor_name} ({possible.actor_type}, {possible.narrative_role}) [{status}]\n"
        
        return summary
    
    def get_proximity_context_for_llm(self, actor_id: str, location: Optional[str] = None) -> str:
        """
        Get spatial proximity context formatted for LLM prompts.
        
        Returns a human-readable description of who/what is near the actor,
        useful for the interpreter to understand spatial relationships.
        
        Args:
            actor_id: The actor to get proximity context for
            location: Optional location override
            
        Returns:
            Formatted string describing nearby actors and distances
        """
        loc = location or self.current_location
        if not loc or loc not in self.contexts:
            return ""
        
        context = self.contexts[loc]
        source_pos = context.actor_positions.get(actor_id)
        if not source_pos:
            return ""
        
        proximity_lines = []
        proximity_lines.append(f"**SPATIAL PROXIMITY (from {source_pos.actor_name}'s position):**")
        
        # Group actors by distance category
        immediate = []  # 0-25 units (~1m)
        close = []      # 26-50 units (~2m)
        near = []       # 51-100 units (~4m)
        far = []        # 101-200 units (~8m)
        distant = []    # 201+ units
        
        for other_id, other_pos in context.actor_positions.items():
            if other_id == actor_id:
                continue
            
            distance = source_pos.position.distance_to(other_pos.position)
            category = source_pos.position.get_distance_category(other_pos.position)
            direction = source_pos.position.direction_to(other_pos.position)
            
            # Convert direction to compass
            compass = self._direction_to_compass(direction)
            
            entry = f"{other_pos.actor_name} ({compass}, ~{distance:.0f} units)"
            
            if category == DistanceCategory.IMMEDIATE:
                immediate.append(entry)
            elif category == DistanceCategory.CLOSE:
                close.append(entry)
            elif category == DistanceCategory.NEAR:
                near.append(entry)
            elif category == DistanceCategory.FAR:
                far.append(entry)
            else:
                distant.append(entry)
        
        if immediate:
            proximity_lines.append(f"- **IMMEDIATE (touch range):** {', '.join(immediate)}")
        if close:
            proximity_lines.append(f"- **CLOSE (conversation range):** {', '.join(close)}")
        if near:
            proximity_lines.append(f"- **NEAR (raised voice range):** {', '.join(near)}")
        if far:
            proximity_lines.append(f"- **FAR (shout range):** {', '.join(far)}")
        if distant:
            proximity_lines.append(f"- **DISTANT (out of range):** {', '.join(distant)}")
        
        if len(proximity_lines) == 1:
            proximity_lines.append("- No other actors nearby")
        
        return "\n".join(proximity_lines)
    
    def _direction_to_compass(self, degrees: float) -> str:
        """Convert degrees to compass direction."""
        directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
        index = round(degrees / 45) % 8
        return directions[index]


# === GLOBAL ACCESSOR ===

_spatial_manager: Optional[SpatialContextManager] = None

def get_spatial_manager(session_id: str = "default") -> SpatialContextManager:
    """Get or create global spatial context manager"""
    global _spatial_manager
    # If a session-specific manager already exists, avoid accidentally switching to
    # the 'default' session when callers omit session_id.
    try:
        sid = session_id
        if sid is None:
            sid = ""
        sid = str(sid).strip()
    except Exception:
        sid = ""

    if _spatial_manager is not None and (sid == "" or sid.lower() == "default"):
        return _spatial_manager

    if _spatial_manager is None or _spatial_manager.session_id != sid:
        _spatial_manager = SpatialContextManager(sid or "default")
    return _spatial_manager
