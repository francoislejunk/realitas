"""
Actor Placement System

Determines where actors should be positioned in a scene based on:
1. Available obstacles and their spatial zones
2. Actor roles/activities from CreatorAgent
3. Narrative context

Each obstacle has 4 spatial zones:
- IN_FRONT: Actor is using/interacting with the obstacle
- BEHIND: Actor is using obstacle as cover/hiding
- LEFT_SIDE: Actor is in the vicinity (left)
- RIGHT_SIDE: Actor is in the vicinity (right)
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Any
from enum import Enum
import math

from spatial_context_system import DEFAULT_MAP_WIDTH, DEFAULT_MAP_HEIGHT


class ObstacleRelation(Enum):
    """Spatial relationship to an obstacle"""
    IN_FRONT = "in_front"      # Using/interacting with the obstacle
    BEHIND = "behind"          # Using as cover, hiding behind
    LEFT_SIDE = "left_side"    # In vicinity, to the left
    RIGHT_SIDE = "right_side"  # In vicinity, to the right
    ON_TOP = "on_top"          # Sitting/standing on (for chairs, beds, etc.)
    INSIDE = "inside"          # Inside the obstacle (for vehicles, booths)


@dataclass
class ObstacleSpatialZones:
    """
    Defines the spatial zones around an obstacle.
    
    Coordinates are in world units, relative to the obstacle's position.
    The obstacle's "front" is determined by its facing direction (default: south/down).
    """
    obstacle_id: str
    obstacle_name: str
    
    # Obstacle bounds
    x: float
    y: float
    width: float
    height: float
    
    # Facing direction (0=north, 90=east, 180=south, 270=west)
    facing: float = 180.0  # Default facing south (toward bottom of map)
    
    # Zone padding (how far from obstacle edge each zone extends)
    zone_padding: float = 5.0  # Reduced for tighter placement near obstacles
    
    @property
    def center(self) -> Tuple[float, float]:
        """Center point of the obstacle"""
        return (self.x + self.width / 2, self.y + self.height / 2)
    
    def get_zone_position(self, relation: ObstacleRelation) -> Tuple[float, float]:
        """
        Get the center position for a specific zone.
        
        Returns (x, y) coordinates where an actor should stand for this relation.
        """
        cx, cy = self.center
        
        # Calculate offset based on facing direction
        facing_rad = math.radians(self.facing)
        
        # Forward vector (direction obstacle faces)
        forward_x = math.sin(facing_rad)
        forward_y = -math.cos(facing_rad)  # Negative because Y increases downward
        
        # Right vector (perpendicular to forward)
        right_x = math.cos(facing_rad)
        right_y = math.sin(facing_rad)
        
        # Distance from center to zone
        front_dist = self.height / 2 + self.zone_padding
        side_dist = self.width / 2 + self.zone_padding
        
        if relation == ObstacleRelation.IN_FRONT:
            return (cx + forward_x * front_dist, cy + forward_y * front_dist)
        elif relation == ObstacleRelation.BEHIND:
            return (cx - forward_x * front_dist, cy - forward_y * front_dist)
        elif relation == ObstacleRelation.LEFT_SIDE:
            return (cx - right_x * side_dist, cy - right_y * side_dist)
        elif relation == ObstacleRelation.RIGHT_SIDE:
            return (cx + right_x * side_dist, cy + right_y * side_dist)
        elif relation == ObstacleRelation.ON_TOP:
            return (cx, cy)  # Center of obstacle
        elif relation == ObstacleRelation.INSIDE:
            return (cx, cy)  # Center of obstacle
        else:
            return (cx, cy)
    
    def get_all_zone_positions(self) -> Dict[ObstacleRelation, Tuple[float, float]]:
        """Get positions for all zones"""
        return {
            relation: self.get_zone_position(relation)
            for relation in ObstacleRelation
        }
    
    def get_zone_bounds(self, relation: ObstacleRelation) -> Tuple[float, float, float, float]:
        """
        Get the bounding box for a zone (x, y, width, height).
        
        Useful for checking if an actor is within a zone.
        """
        pos = self.get_zone_position(relation)
        zone_size = self.zone_padding * 2
        return (pos[0] - zone_size/2, pos[1] - zone_size/2, zone_size, zone_size)
    
    def describe_position(self, relation: ObstacleRelation) -> str:
        """Get a narrative description of this position"""
        descriptions = {
            ObstacleRelation.IN_FRONT: f"in front of the {self.obstacle_name}",
            ObstacleRelation.BEHIND: f"behind the {self.obstacle_name}",
            ObstacleRelation.LEFT_SIDE: f"to the left of the {self.obstacle_name}",
            ObstacleRelation.RIGHT_SIDE: f"to the right of the {self.obstacle_name}",
            ObstacleRelation.ON_TOP: f"on the {self.obstacle_name}",
            ObstacleRelation.INSIDE: f"inside the {self.obstacle_name}",
        }
        return descriptions.get(relation, f"near the {self.obstacle_name}")


@dataclass
class ActorPlacement:
    """Describes where an actor should be placed"""
    actor_id: str
    actor_name: str
    
    # Position
    x: float
    y: float
    
    # Relation to obstacle (if any)
    near_obstacle_id: Optional[str] = None
    near_obstacle_name: Optional[str] = None
    obstacle_relation: Optional[ObstacleRelation] = None
    
    # Activity description
    activity: str = ""  # e.g., "working at", "hiding behind", "standing near"
    
    def get_narrative_description(self) -> str:
        """Get a description suitable for the narrator"""
        if self.near_obstacle_name and self.obstacle_relation:
            relation_verbs = {
                ObstacleRelation.IN_FRONT: "using",
                ObstacleRelation.BEHIND: "behind",
                ObstacleRelation.LEFT_SIDE: "near",
                ObstacleRelation.RIGHT_SIDE: "near",
                ObstacleRelation.ON_TOP: "on",
                ObstacleRelation.INSIDE: "in",
            }
            verb = relation_verbs.get(self.obstacle_relation, "near")
            return f"{self.actor_name} is {verb} the {self.near_obstacle_name}"
        return f"{self.actor_name} is in the area"


class ActorPlacementSystem:
    """
    System for determining actor positions based on obstacles and context.
    
    Usage:
    1. Initialize with obstacle data from the layout
    2. Call determine_placements() with actor info from CreatorAgent
    3. Get positions and narrative descriptions for each actor
    """
    
    def __init__(self):
        self.obstacles: Dict[str, ObstacleSpatialZones] = {}
        self.placements: Dict[str, ActorPlacement] = {}
        self.map_width: float = float(DEFAULT_MAP_WIDTH)
        self.map_height: float = float(DEFAULT_MAP_HEIGHT)
    
    def load_obstacles_from_layout(self, obstacles: List[Dict[str, Any]], map_width: Optional[float] = None, map_height: Optional[float] = None):
        """
        Load obstacles from layout generator output.
        
        Args:
            obstacles: List of obstacle dicts with keys: id/name, x, y, width, height, type
        """
        if map_width is not None:
            try:
                self.map_width = float(map_width)
            except Exception:
                pass
        if map_height is not None:
            try:
                self.map_height = float(map_height)
            except Exception:
                pass

        self.obstacles.clear()
        
        for obs in obstacles:
            obs_id = obs.get('id') or obs.get('obstacle_id') or obs.get('name', 'unknown')
            obs_name = obs.get('name', obs_id)
            
            # Determine facing based on obstacle type/position
            facing = self._determine_obstacle_facing(obs)
            
            zones = ObstacleSpatialZones(
                obstacle_id=obs_id,
                obstacle_name=obs_name,
                x=float(obs.get('x', 0)),
                y=float(obs.get('y', 0)),
                width=float(obs.get('width', 20)),
                height=float(obs.get('height', 20)),
                facing=facing
            )
            self.obstacles[obs_id] = zones
    
    def _determine_obstacle_facing(self, obstacle: Dict) -> float:
        """
        Determine which direction an obstacle faces based on its type and position.
        
        - Desks face away from walls (toward room center)
        - Counters face the customer side
        - Beds face the foot of the bed
        - Default: face south (180 degrees)
        """
        obs_type = obstacle.get('type', '').lower()
        obs_name = obstacle.get('name', '').lower()
        x = obstacle.get('x', 125)
        y = obstacle.get('y', 100)
        
        # Furniture against walls faces toward room center
        # Assume room is 250x200, center is (125, 100)
        try:
            w = float(self.map_width or DEFAULT_MAP_WIDTH)
            h = float(self.map_height or DEFAULT_MAP_HEIGHT)
        except Exception:
            w = float(DEFAULT_MAP_WIDTH)
            h = float(DEFAULT_MAP_HEIGHT)
        room_center_x, room_center_y = (w * 0.5), (h * 0.5)
        
        # Calculate angle from obstacle to room center
        dx = room_center_x - x
        dy = room_center_y - y
        
        if abs(dx) > abs(dy):
            # More horizontal offset - face east or west
            return 90 if dx > 0 else 270
        else:
            # More vertical offset - face north or south
            return 0 if dy > 0 else 180
    
    def determine_placements(self, 
                            actors: List[Dict[str, Any]], 
                            scene_context: str = "") -> List[ActorPlacement]:
        """
        Determine where each actor should be placed.
        
        Args:
            actors: List of actor dicts from CreatorAgent with keys:
                   - name: Actor name
                   - role/occupation: What they do
                   - activity: What they're currently doing (optional)
            scene_context: Scene description for context
        
        Returns:
            List of ActorPlacement objects with positions
        """
        self.placements.clear()
        placements = []
        
        # Track which obstacle zones are occupied
        occupied_zones: Dict[str, List[ObstacleRelation]] = {
            obs_id: [] for obs_id in self.obstacles
        }
        
        for actor in actors:
            actor_name = actor.get('name', 'Unknown')
            actor_id = actor.get('id') or actor_name.lower().replace(' ', '_')
            activity = actor.get('activity', '')
            role = actor.get('role') or actor.get('occupation', '')
            
            # Find best obstacle and relation for this actor
            best_obstacle, best_relation = self._find_best_placement(
                actor_name, role, activity, scene_context, occupied_zones
            )
            
            if best_obstacle and best_relation:
                # Get position from obstacle zone
                pos = best_obstacle.get_zone_position(best_relation)
                
                placement = ActorPlacement(
                    actor_id=actor_id,
                    actor_name=actor_name,
                    x=pos[0],
                    y=pos[1],
                    near_obstacle_id=best_obstacle.obstacle_id,
                    near_obstacle_name=best_obstacle.obstacle_name,
                    obstacle_relation=best_relation,
                    activity=activity or self._infer_activity(best_relation)
                )
                
                # Mark zone as occupied
                occupied_zones[best_obstacle.obstacle_id].append(best_relation)
            else:
                # No suitable obstacle - place in open area
                pos = self._find_open_position(occupied_zones)
                placement = ActorPlacement(
                    actor_id=actor_id,
                    actor_name=actor_name,
                    x=pos[0],
                    y=pos[1],
                    activity=activity or "standing"
                )
            
            placements.append(placement)
            self.placements[actor_id] = placement
        
        return placements
    
    def _find_best_placement(self,
                            actor_name: str,
                            role: str,
                            activity: str,
                            scene_context: str,
                            occupied_zones: Dict[str, List[ObstacleRelation]]
                            ) -> Tuple[Optional[ObstacleSpatialZones], Optional[ObstacleRelation]]:
        """Find the best obstacle and relation for an actor based on their role/activity"""
        
        # Keywords that suggest specific relations
        activity_lower = activity.lower() if activity else ""
        role_lower = role.lower() if role else ""
        combined = f"{activity_lower} {role_lower}"
        
        # Check for activity-based placement
        if any(word in combined for word in ['hiding', 'cover', 'crouching', 'sneaking']):
            preferred_relation = ObstacleRelation.BEHIND
        elif any(word in combined for word in ['working', 'using', 'operating', 'typing', 'cooking']):
            preferred_relation = ObstacleRelation.IN_FRONT
        elif any(word in combined for word in ['sitting', 'resting', 'sleeping']):
            preferred_relation = ObstacleRelation.ON_TOP
        elif any(word in combined for word in ['driving', 'inside']):
            preferred_relation = ObstacleRelation.INSIDE
        else:
            preferred_relation = ObstacleRelation.IN_FRONT  # Default
        
        # Find matching obstacle based on role
        role_obstacle_map = {
            'bartender': ['counter', 'bar'],
            'cashier': ['register', 'counter', 'checkout'],
            'cook': ['stove', 'grill', 'kitchen'],
            'receptionist': ['desk', 'counter', 'reception'],
            'guard': ['door', 'entrance', 'gate'],
            'worker': ['desk', 'workstation', 'terminal'],
            'customer': ['counter', 'table', 'booth'],
            'patron': ['table', 'booth', 'bar', 'stool'],
        }
        
        # Find obstacles that match the role
        matching_obstacles = []
        for obs_id, obs in self.obstacles.items():
            obs_name_lower = obs.obstacle_name.lower()
            
            # Check role-based matching
            for role_key, obstacle_keywords in role_obstacle_map.items():
                if role_key in role_lower:
                    for keyword in obstacle_keywords:
                        if keyword in obs_name_lower:
                            matching_obstacles.append(obs)
                            break
            
            # Also check if activity mentions this obstacle
            if obs_name_lower in activity_lower or obs_name_lower in scene_context.lower():
                if obs not in matching_obstacles:
                    matching_obstacles.append(obs)
        
        # If no specific match, use any available obstacle
        if not matching_obstacles:
            matching_obstacles = list(self.obstacles.values())
        
        # Find first obstacle with available zone
        for obs in matching_obstacles:
            if preferred_relation not in occupied_zones.get(obs.obstacle_id, []):
                return obs, preferred_relation
            
            # Try other relations
            for relation in ObstacleRelation:
                if relation not in occupied_zones.get(obs.obstacle_id, []):
                    return obs, relation
        
        return None, None
    
    def _infer_activity(self, relation: ObstacleRelation) -> str:
        """Infer activity description from relation"""
        activity_map = {
            ObstacleRelation.IN_FRONT: "using",
            ObstacleRelation.BEHIND: "standing behind",
            ObstacleRelation.LEFT_SIDE: "standing near",
            ObstacleRelation.RIGHT_SIDE: "standing near",
            ObstacleRelation.ON_TOP: "sitting on",
            ObstacleRelation.INSIDE: "inside",
        }
        return activity_map.get(relation, "near")
    
    def _find_open_position(self, occupied_zones: Dict) -> Tuple[float, float]:
        """Find an open position not near any obstacle"""
        # Default to center-ish area with some randomization
        import random
        return (
            100 + random.uniform(-30, 30),
            80 + random.uniform(-20, 20)
        )
    
    def get_placement_for_narrator(self, actor_id: str) -> Dict[str, Any]:
        """
        Get placement info formatted for the NarratorAgent.
        
        Returns dict with:
        - position: (x, y)
        - description: Narrative description of position
        - obstacle_context: Info about nearby obstacle
        """
        placement = self.placements.get(actor_id)
        if not placement:
            return {}
        
        result = {
            'position': (placement.x, placement.y),
            'description': placement.get_narrative_description(),
            'activity': placement.activity,
        }
        
        if placement.near_obstacle_id:
            obs = self.obstacles.get(placement.near_obstacle_id)
            if obs:
                result['obstacle_context'] = {
                    'obstacle_name': obs.obstacle_name,
                    'relation': placement.obstacle_relation.value if placement.obstacle_relation else None,
                    'zone_description': obs.describe_position(placement.obstacle_relation) if placement.obstacle_relation else None,
                }
        
        return result
    
    def get_all_placements_summary(self) -> str:
        """Get a summary of all placements for narrative context"""
        lines = []
        for actor_id, placement in self.placements.items():
            lines.append(placement.get_narrative_description())
        return "; ".join(lines)


# ═══════════════════════════════════════════════════════════════════════════════
# SINGLETON ACCESS
# ═══════════════════════════════════════════════════════════════════════════════

_placement_system: Optional[ActorPlacementSystem] = None

def get_actor_placement_system() -> ActorPlacementSystem:
    """Get the global actor placement system instance"""
    global _placement_system
    if _placement_system is None:
        _placement_system = ActorPlacementSystem()
    return _placement_system


def initialize_actor_placement(obstacles: List[Dict[str, Any]]) -> ActorPlacementSystem:
    """Initialize the placement system with obstacles from layout"""
    system = get_actor_placement_system()
    system.load_obstacles_from_layout(obstacles)
    return system


# ═══════════════════════════════════════════════════════════════════════════════
# TESTING
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    # Test the system
    print("=== Actor Placement System Test ===\n")
    
    # Sample obstacles from a diner layout
    obstacles = [
        {"name": "Counter", "x": 140, "y": 130, "width": 80, "height": 15, "type": "furniture"},
        {"name": "Counter Stool", "x": 125, "y": 115, "width": 8, "height": 8, "type": "furniture"},
        {"name": "Booth", "x": 30, "y": 160, "width": 35, "height": 25, "type": "furniture"},
        {"name": "Cash Register", "x": 175, "y": 145, "width": 12, "height": 10, "type": "equipment"},
        {"name": "Jukebox", "x": 25, "y": 100, "width": 15, "height": 20, "type": "equipment"},
    ]
    
    # Initialize system
    system = initialize_actor_placement(obstacles)
    
    # Sample actors
    actors = [
        {"name": "Betty", "role": "waitress", "activity": "working at the counter"},
        {"name": "Joe", "role": "customer", "activity": "sitting at the booth"},
        {"name": "Mike", "role": "cook", "activity": "behind the counter"},
        {"name": "Sarah", "role": "patron", "activity": "standing by the jukebox"},
    ]
    
    # Determine placements
    placements = system.determine_placements(actors, "A classic 1960s diner")
    
    print("Actor Placements:")
    print("-" * 50)
    for p in placements:
        print(f"\n{p.actor_name}:")
        print(f"  Position: ({p.x:.1f}, {p.y:.1f})")
        print(f"  Near: {p.near_obstacle_name or 'N/A'}")
        print(f"  Relation: {p.obstacle_relation.value if p.obstacle_relation else 'N/A'}")
        print(f"  Narrative: {p.get_narrative_description()}")
    
    print("\n" + "=" * 50)
    print("Summary for Narrator:")
    print(system.get_all_placements_summary())
