"""
Location Distance Tracker - World Geography System

Tracks distances and travel times between named locations in the simulation world.
This enables:
- Realistic travel time calculations when moving between locations
- Context about "how far" places are from each other
- Persistence of discovered location relationships
- NUA location tracking (where are they relative to the player?)

Design Philosophy:
- Locations are nodes in a graph
- Edges represent known travel times/distances
- Unknown routes are estimated based on location types
- Travel times are stored in MINUTES (simulation time)
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum


class LocationType(Enum):
    """Types of locations for distance estimation"""
    RESIDENCE = "residence"          # Apartments, houses
    COMMERCIAL = "commercial"        # Shops, stores, businesses
    FOOD = "food"                    # Restaurants, diners, cafes
    ENTERTAINMENT = "entertainment"  # Bars, clubs, theaters
    INDUSTRIAL = "industrial"        # Factories, warehouses
    OFFICE = "office"                # Office buildings
    PUBLIC = "public"                # Parks, plazas, streets
    TRANSIT = "transit"              # Bus stops, train stations
    INSTITUTIONAL = "institutional"  # Schools, hospitals, government
    OUTDOOR = "outdoor"              # Streets, alleys, parking lots
    UNKNOWN = "unknown"


class TravelMethod(Enum):
    """Methods of travel between locations"""
    WALKING = "walking"
    DRIVING = "driving"
    PUBLIC_TRANSIT = "public_transit"
    RUNNING = "running"
    CYCLING = "cycling"


# Default travel speeds (minutes per "block" - abstract distance unit)
TRAVEL_SPEEDS = {
    TravelMethod.WALKING: 3.0,       # 3 minutes per block walking
    TravelMethod.RUNNING: 1.5,       # 1.5 minutes per block running
    TravelMethod.CYCLING: 1.0,       # 1 minute per block cycling
    TravelMethod.DRIVING: 0.5,       # 0.5 minutes per block driving
    TravelMethod.PUBLIC_TRANSIT: 2.0 # 2 minutes per block (includes waiting)
}


@dataclass
class LocationNode:
    """A named location in the world"""
    name: str
    location_type: LocationType = LocationType.UNKNOWN
    description: str = ""
    first_visited: Optional[str] = None
    last_visited: Optional[str] = None
    visit_count: int = 0
    known_nuas: List[str] = field(default_factory=list)  # NUAs known to be at this location
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "location_type": self.location_type.value,
            "description": self.description,
            "first_visited": self.first_visited,
            "last_visited": self.last_visited,
            "visit_count": self.visit_count,
            "known_nuas": self.known_nuas
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationNode':
        return cls(
            name=data["name"],
            location_type=LocationType(data.get("location_type", "unknown")),
            description=data.get("description", ""),
            first_visited=data.get("first_visited"),
            last_visited=data.get("last_visited"),
            visit_count=data.get("visit_count", 0),
            known_nuas=data.get("known_nuas", [])
        )


@dataclass
class LocationEdge:
    """A known route between two locations"""
    from_location: str
    to_location: str
    distance_blocks: float  # Abstract distance in "blocks"
    travel_time_walking: float  # Minutes to walk
    travel_time_driving: Optional[float] = None  # Minutes to drive (if applicable)
    route_description: str = ""  # "through the park", "down Main Street"
    discovered_at: Optional[str] = None
    
    def get_travel_time(self, method: TravelMethod) -> float:
        """Get travel time for a specific method"""
        if method == TravelMethod.WALKING:
            return self.travel_time_walking
        elif method == TravelMethod.DRIVING and self.travel_time_driving:
            return self.travel_time_driving
        else:
            # Estimate based on walking time and speed ratios
            walking_speed = TRAVEL_SPEEDS[TravelMethod.WALKING]
            target_speed = TRAVEL_SPEEDS[method]
            return self.travel_time_walking * (target_speed / walking_speed)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "from_location": self.from_location,
            "to_location": self.to_location,
            "distance_blocks": self.distance_blocks,
            "travel_time_walking": self.travel_time_walking,
            "travel_time_driving": self.travel_time_driving,
            "route_description": self.route_description,
            "discovered_at": self.discovered_at
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LocationEdge':
        return cls(
            from_location=data["from_location"],
            to_location=data["to_location"],
            distance_blocks=data["distance_blocks"],
            travel_time_walking=data["travel_time_walking"],
            travel_time_driving=data.get("travel_time_driving"),
            route_description=data.get("route_description", ""),
            discovered_at=data.get("discovered_at")
        )


class LocationDistanceTracker:
    """
    Tracks the world geography - locations and distances between them.
    
    Features:
    - Add/update locations as they're discovered
    - Record travel times between locations
    - Estimate travel times for unknown routes
    - Track which NUAs are at which locations
    - Persist to JSON for session continuity
    """
    
    def __init__(self, storage_dir: str = "simulation_data/world_map"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.locations: Dict[str, LocationNode] = {}
        self.edges: Dict[str, LocationEdge] = {}  # Key: "from|to"
        self.current_location: Optional[str] = None
        
        self._load()
    
    def _get_edge_key(self, from_loc: str, to_loc: str) -> str:
        """Generate consistent edge key (alphabetically ordered for bidirectional)"""
        # Sort to make edges bidirectional
        locs = sorted([from_loc.lower(), to_loc.lower()])
        return f"{locs[0]}|{locs[1]}"
    
    def _save(self):
        """Save world map to disk"""
        data = {
            "locations": {k: v.to_dict() for k, v in self.locations.items()},
            "edges": {k: v.to_dict() for k, v in self.edges.items()},
            "current_location": self.current_location,
            "last_updated": datetime.now().isoformat()
        }
        
        save_path = self.storage_dir / "world_map.json"
        with open(save_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load(self):
        """Load world map from disk"""
        load_path = self.storage_dir / "world_map.json"
        if load_path.exists():
            try:
                with open(load_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                self.locations = {k: LocationNode.from_dict(v) for k, v in data.get("locations", {}).items()}
                self.edges = {k: LocationEdge.from_dict(v) for k, v in data.get("edges", {}).items()}
                self.current_location = data.get("current_location")
                
                print(f"[WORLD MAP] Loaded {len(self.locations)} locations, {len(self.edges)} routes")
            except Exception as e:
                print(f"[WORLD MAP] Failed to load: {e}")
    
    def add_location(self, name: str, location_type: LocationType = LocationType.UNKNOWN,
                    description: str = "") -> LocationNode:
        """Add or update a location"""
        key = name.lower()
        now = datetime.now().isoformat()
        
        if key in self.locations:
            # Update existing
            loc = self.locations[key]
            loc.last_visited = now
            loc.visit_count += 1
            if description:
                loc.description = description
            if location_type != LocationType.UNKNOWN:
                loc.location_type = location_type
        else:
            # Create new
            loc = LocationNode(
                name=name,
                location_type=location_type,
                description=description,
                first_visited=now,
                last_visited=now,
                visit_count=1
            )
            self.locations[key] = loc
            print(f"[WORLD MAP] Discovered new location: {name}")
        
        self._save()
        return loc
    
    def set_current_location(self, name: str, location_type: LocationType = LocationType.UNKNOWN,
                            description: str = ""):
        """Set the player's current location"""
        self.add_location(name, location_type, description)
        self.current_location = name.lower()
        self._save()
    
    def record_travel(self, from_location: str, to_location: str, 
                     travel_time_minutes: float, method: TravelMethod = TravelMethod.WALKING,
                     route_description: str = ""):
        """Record a travel between two locations"""
        # Ensure both locations exist
        self.add_location(from_location)
        self.add_location(to_location)
        
        # Calculate distance in blocks based on travel time and method
        speed = TRAVEL_SPEEDS[method]
        distance_blocks = travel_time_minutes / speed
        
        # Calculate walking time if not walking
        if method == TravelMethod.WALKING:
            walking_time = travel_time_minutes
            driving_time = distance_blocks * TRAVEL_SPEEDS[TravelMethod.DRIVING]
        else:
            walking_time = distance_blocks * TRAVEL_SPEEDS[TravelMethod.WALKING]
            driving_time = travel_time_minutes if method == TravelMethod.DRIVING else None
        
        edge_key = self._get_edge_key(from_location, to_location)
        
        edge = LocationEdge(
            from_location=from_location,
            to_location=to_location,
            distance_blocks=distance_blocks,
            travel_time_walking=walking_time,
            travel_time_driving=driving_time,
            route_description=route_description,
            discovered_at=datetime.now().isoformat()
        )
        
        self.edges[edge_key] = edge
        print(f"[WORLD MAP] Recorded route: {from_location} → {to_location} ({travel_time_minutes:.1f} min {method.value})")
        self._save()
        
        return edge
    
    def get_travel_time(self, from_location: str, to_location: str,
                       method: TravelMethod = TravelMethod.WALKING) -> Tuple[float, bool]:
        """
        Get travel time between two locations.
        
        Returns:
            Tuple of (travel_time_minutes, is_known_route)
            - is_known_route: True if we have recorded data, False if estimated
        """
        edge_key = self._get_edge_key(from_location, to_location)
        
        if edge_key in self.edges:
            edge = self.edges[edge_key]
            return edge.get_travel_time(method), True
        
        # Estimate based on location types
        from_loc = self.locations.get(from_location.lower())
        to_loc = self.locations.get(to_location.lower())
        
        # Default estimate: 10 minutes walking (about 3 blocks)
        estimated_blocks = 3.0
        
        # Adjust based on location types if known
        if from_loc and to_loc:
            # Same type locations might be clustered
            if from_loc.location_type == to_loc.location_type:
                estimated_blocks = 2.0  # Closer together
            # Transit stations are usually far from residences
            elif LocationType.TRANSIT in [from_loc.location_type, to_loc.location_type]:
                estimated_blocks = 5.0
        
        estimated_time = estimated_blocks * TRAVEL_SPEEDS[method]
        return estimated_time, False
    
    def get_distance_description(self, from_location: str, to_location: str) -> str:
        """Get a narrative description of distance between locations"""
        travel_time, is_known = self.get_travel_time(from_location, to_location)
        
        if travel_time <= 2:
            distance_desc = "just around the corner"
        elif travel_time <= 5:
            distance_desc = "a short walk away"
        elif travel_time <= 10:
            distance_desc = "a few blocks away"
        elif travel_time <= 20:
            distance_desc = "across the neighborhood"
        elif travel_time <= 30:
            distance_desc = "across town"
        else:
            distance_desc = "quite far away"
        
        if is_known:
            return f"{distance_desc} (about {travel_time:.0f} minutes)"
        else:
            return f"{distance_desc} (estimated {travel_time:.0f} minutes)"
    
    def add_nua_to_location(self, nua_name: str, location_name: str):
        """Record that an NUA is at a specific location"""
        key = location_name.lower()
        if key in self.locations:
            if nua_name not in self.locations[key].known_nuas:
                self.locations[key].known_nuas.append(nua_name)
                self._save()
    
    def remove_nua_from_location(self, nua_name: str, location_name: str):
        """Remove NUA from a location (they left)"""
        key = location_name.lower()
        if key in self.locations:
            if nua_name in self.locations[key].known_nuas:
                self.locations[key].known_nuas.remove(nua_name)
                self._save()
    
    def get_nuas_at_location(self, location_name: str) -> List[str]:
        """Get list of NUAs known to be at a location"""
        key = location_name.lower()
        if key in self.locations:
            return self.locations[key].known_nuas.copy()
        return []
    
    def get_all_known_locations(self) -> List[str]:
        """Get list of all discovered locations"""
        return [loc.name for loc in self.locations.values()]
    
    def get_nearby_locations(self, from_location: str, max_minutes: float = 15,
                            method: TravelMethod = TravelMethod.WALKING) -> List[Tuple[str, float]]:
        """Get locations within a certain travel time"""
        nearby = []
        for loc_key, loc in self.locations.items():
            if loc_key == from_location.lower():
                continue
            
            travel_time, _ = self.get_travel_time(from_location, loc.name, method)
            if travel_time <= max_minutes:
                nearby.append((loc.name, travel_time))
        
        # Sort by travel time
        nearby.sort(key=lambda x: x[1])
        return nearby
    
    def get_context_for_llm(self) -> str:
        """Get world map context for LLM prompts"""
        if not self.locations:
            return ""
        
        lines = ["**KNOWN LOCATIONS:**"]
        
        for loc in self.locations.values():
            type_str = f" ({loc.location_type.value})" if loc.location_type != LocationType.UNKNOWN else ""
            nua_str = f" - NUAs: {', '.join(loc.known_nuas)}" if loc.known_nuas else ""
            lines.append(f"- {loc.name}{type_str}{nua_str}")
        
        if self.current_location:
            lines.append(f"\n**CURRENT LOCATION:** {self.current_location}")
            
            # Add nearby locations
            nearby = self.get_nearby_locations(self.current_location, max_minutes=15)
            if nearby:
                lines.append("**NEARBY (within 15 min walk):**")
                for name, time in nearby[:5]:  # Top 5
                    lines.append(f"- {name}: ~{time:.0f} min")
        
        return "\n".join(lines)


# Singleton instance
_tracker_instance: Optional[LocationDistanceTracker] = None

def get_location_tracker(storage_dir: str = "simulation_data/world_map") -> LocationDistanceTracker:
    """Get or create the singleton LocationDistanceTracker"""
    global _tracker_instance
    if _tracker_instance is None:
        _tracker_instance = LocationDistanceTracker(storage_dir)
    return _tracker_instance
