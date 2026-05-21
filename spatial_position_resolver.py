"""
Spatial Position Resolver - Converts targets to coordinates

Resolves movement targets (obstacles, zones, directions) into actual
map coordinates.
"""

from typing import Optional, Tuple
from spatial_context_system import Position, SpatialContext


class SpatialPositionResolver:
    """
    Resolves movement targets to actual coordinates.
    """
    
    def resolve_target_position(self, target: str, target_type: str, 
                                spatial_context: SpatialContext,
                                current_position: Optional[Position] = None) -> Optional[Position]:
        """
        Convert target name/direction to actual coordinates.
        
        Args:
            target: Name of destination ("workbench", "back", "left", etc.)
            target_type: Type of target ("obstacle", "zone", "direction")
            spatial_context: Current spatial context
            current_position: Actor's current position (for relative movement)
        
        Returns:
            Position object with coordinates, or None if can't resolve
        """
        if not spatial_context or not spatial_context.location_dimensions:
            return None
        
        dims = spatial_context.location_dimensions
        
        if target_type == "obstacle":
            return self._resolve_obstacle_position(target, spatial_context)
        
        elif target_type == "zone":
            return self._resolve_zone_position(target, spatial_context)
        
        elif target_type == "direction":
            return self._resolve_direction_position(target, dims, current_position)
        
        elif target_type == "actor":
            return self._resolve_actor_position(target, spatial_context, current_position)
        
        return None
    
    def _resolve_actor_position(self, target: str, context: SpatialContext, 
                                 current_pos: Optional[Position] = None) -> Optional[Position]:
        """Find actor and return position near them (for approaching)"""
        target_lower = target.lower()
        
        # Search actors by name
        for actor_id, actor_pos in context.actor_positions.items():
            if target_lower in actor_pos.actor_name.lower() or actor_pos.actor_name.lower() in target_lower:
                # Return position 1.5 units away from actor (conversation distance)
                actor_x = actor_pos.position.x
                actor_y = actor_pos.position.y
                
                # If we have current position, approach from that direction
                if current_pos:
                    # Calculate direction vector
                    dx = actor_x - current_pos.x
                    dy = actor_y - current_pos.y
                    dist = (dx**2 + dy**2)**0.5
                    
                    if dist > 1.5:
                        # Normalize and position 1.5 units away
                        scale = (dist - 1.5) / dist
                        return Position(current_pos.x + dx * scale, current_pos.y + dy * scale)
                    else:
                        # Already close enough
                        return current_pos
                else:
                    # No current position, just get close to actor
                    return Position(actor_x, max(0, actor_y - 1.5))
        
        return None
    
    def _resolve_obstacle_position(self, target: str, context: SpatialContext) -> Optional[Position]:
        """Find obstacle and return position adjacent to it"""
        target_lower = target.lower().replace(" ", "").replace("-", "").replace("_", "")
        
        # Search obstacles by name (check both key and obstacle_name)
        for obs_key, obstacle in context.location_dimensions.obstacles.items():
            # Normalize names for comparison
            key_normalized = obs_key.lower().replace(" ", "").replace("-", "").replace("_", "")
            name_normalized = obstacle.obstacle_name.lower().replace(" ", "").replace("-", "").replace("_", "") if obstacle.obstacle_name else ""
            
            # Check if target matches key or name (fuzzy match)
            if (target_lower in key_normalized or key_normalized in target_lower or
                target_lower in name_normalized or name_normalized in target_lower):
                
                # Get position - prefer boundary points, fallback to center of room
                if obstacle.boundary_points and len(obstacle.boundary_points) > 0:
                    # Get center of obstacle
                    center_x = sum(p.x for p in obstacle.boundary_points) / len(obstacle.boundary_points)
                    center_y = sum(p.y for p in obstacle.boundary_points) / len(obstacle.boundary_points)
                else:
                    # No boundary points - use a default position based on obstacle key
                    # This happens when obstacles are added without explicit coordinates
                    dims = context.location_dimensions
                    # Place at a reasonable position in the room
                    center_x = dims.width / 2
                    center_y = dims.height / 2
                
                # Position 1 unit in front (lower Y)
                return Position(center_x, max(0, center_y - 1))
        
        return None
    
    def _resolve_zone_position(self, target: str, context: SpatialContext) -> Optional[Position]:
        """Find zone and return center position"""
        target_lower = target.lower()
        
        # Search zones by name
        for zone_name, zone in context.location_dimensions.zones.items():
            if target_lower in zone_name.lower() or zone_name.lower() in target_lower:
                # Return center of zone
                if zone.boundary_points and len(zone.boundary_points) >= 3:
                    center_x = sum(p.x for p in zone.boundary_points) / len(zone.boundary_points)
                    center_y = sum(p.y for p in zone.boundary_points) / len(zone.boundary_points)
                    return Position(center_x, center_y)
        
        return None
    
    def _resolve_direction_position(self, direction: str, dims, current_pos: Optional[Position]) -> Optional[Position]:
        """Convert direction to coordinates"""
        direction_lower = direction.lower()
        
        width = dims.width
        height = dims.height
        
        # Absolute directions (relative to room)
        if direction_lower in ['front', 'entrance']:
            return Position(width / 2, height * 0.15)  # Front/entrance
        
        elif direction_lower in ['back', 'rear']:
            return Position(width / 2, height * 0.85)  # Back
        
        elif direction_lower in ['left']:
            return Position(width * 0.15, height / 2)  # Left side
        
        elif direction_lower in ['right']:
            return Position(width * 0.85, height / 2)  # Right side
        
        elif direction_lower in ['center', 'middle']:
            return Position(width / 2, height / 2)  # Center
        
        # Corner positions
        elif 'corner' in direction_lower:
            if 'left' in direction_lower or 'west' in direction_lower:
                if 'back' in direction_lower or 'north' in direction_lower:
                    return Position(width * 0.1, height * 0.9)  # Back-left
                else:
                    return Position(width * 0.1, height * 0.1)  # Front-left
            else:  # right
                if 'back' in direction_lower or 'north' in direction_lower:
                    return Position(width * 0.9, height * 0.9)  # Back-right
                else:
                    return Position(width * 0.9, height * 0.1)  # Front-right
        
        # Relative directions (if current position known)
        if current_pos:
            if direction_lower in ['forward', 'ahead']:
                return Position(current_pos.x, min(height, current_pos.y + 5))
            
            elif direction_lower in ['backward', 'backwards', 'back']:
                return Position(current_pos.x, max(0, current_pos.y - 5))
        
        # Cardinal directions
        if direction_lower in ['north']:
            return Position(width / 2, height * 0.85)
        elif direction_lower in ['south']:
            return Position(width / 2, height * 0.15)
        elif direction_lower in ['east']:
            return Position(width * 0.85, height / 2)
        elif direction_lower in ['west']:
            return Position(width * 0.15, height / 2)
        
        return None


# Global accessor
_position_resolver: Optional[SpatialPositionResolver] = None

def get_position_resolver() -> SpatialPositionResolver:
    """Get or create global position resolver"""
    global _position_resolver
    if _position_resolver is None:
        _position_resolver = SpatialPositionResolver()
    return _position_resolver
