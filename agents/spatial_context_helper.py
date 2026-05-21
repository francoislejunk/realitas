"""
Spatial Context Helper for Agents

Provides a reusable function to generate spatial context text for LLM prompts.
All agents can use this to be aware of actor and obstacle positions.
"""

def get_spatial_context_for_prompt(proactor_name: str = "YOU", max_obstacles: int = 15, include_sensory: bool = True) -> str:
    """
    Generate spatial context text for LLM prompts.
    
    Returns a formatted string with positions of:
    - The user actor (UA)
    - All other actors (NUAs) with distances and sensory info
    - Key obstacles in the location
    - Sensory perception ranges
    
    Args:
        proactor_name: Name to display for the UA (default "YOU")
        max_obstacles: Maximum number of obstacles to include
        include_sensory: Whether to include sensory range information
        
    Returns:
        Formatted string for inclusion in LLM prompts, or empty string if unavailable
    """
    try:
        from spatial_context_system import get_spatial_manager, Position
        spatial = get_spatial_manager()
        context = spatial.get_current_context()
        
        if not context:
            return ""
        
        # Get UA position
        ua_pos = spatial.get_actor_position("ua_001")
        if not ua_pos:
            return ""
        
        spatial_lines = [f"- {proactor_name}: ({ua_pos.x:.0f}, {ua_pos.y:.0f})"]
        
        # Get other actor positions WITH DISTANCES
        for actor_id, actor_pos in context.actor_positions.items():
            if actor_id != "ua_001":
                # Calculate distance from UA
                dx = actor_pos.position.x - ua_pos.x
                dy = actor_pos.position.y - ua_pos.y
                distance = (dx**2 + dy**2)**0.5
                
                # Determine cardinal direction
                direction = _get_cardinal_direction(ua_pos.x, ua_pos.y, actor_pos.position.x, actor_pos.position.y)
                
                # Determine sensory perception quality
                perception = _get_perception_quality(distance)
                
                spatial_lines.append(
                    f"- {actor_pos.actor_name}: {distance:.0f} units {direction} ({perception})"
                )
        
        # Get obstacle positions WITH DISTANCES
        if context.location_dimensions and context.location_dimensions.obstacles:
            obs_list = list(context.location_dimensions.obstacles.items())[:max_obstacles]
            for obs_id, obs in obs_list:
                obs_name = getattr(obs, 'obstacle_name', obs_id)
                if hasattr(obs, 'boundary_points') and obs.boundary_points:
                    cx = sum(p.x for p in obs.boundary_points) / len(obs.boundary_points)
                    cy = sum(p.y for p in obs.boundary_points) / len(obs.boundary_points)
                    
                    # Calculate distance from UA
                    dx = cx - ua_pos.x
                    dy = cy - ua_pos.y
                    distance = (dx**2 + dy**2)**0.5
                    direction = _get_cardinal_direction(ua_pos.x, ua_pos.y, cx, cy)
                    
                    spatial_lines.append(f"- {obs_name}: {distance:.0f} units {direction}")
        
        # Format output
        header = "**SPATIAL AWARENESS** (1 unit ≈ 0.5m):"
        
        # Add sensory ranges if requested
        sensory_info = ""
        if include_sensory:
            sensory_info = """
**SENSORY RANGES:**
- Vision: Clear <20 units, Detailed <50 units, Max ~100 units
- Hearing: Whisper <3 units, Speech <15 units, Max ~80 units
- Touch: <2 units (arm's reach)
"""
        
        footer = "(Use these distances for accurate spatial descriptions)"
        
        return f"\n{header}\n" + "\n".join(spatial_lines) + sensory_info + f"\n{footer}\n"
        
    except Exception:
        return ""  # Spatial context is optional enhancement


def _get_cardinal_direction(from_x: float, from_y: float, to_x: float, to_y: float) -> str:
    """Get cardinal direction from one point to another."""
    import math
    dx = to_x - from_x
    dy = to_y - from_y
    
    if abs(dx) < 5 and abs(dy) < 5:
        return "nearby"
    
    angle = math.atan2(dy, dx) * 180 / math.pi
    
    # Convert angle to cardinal direction (0 = east, 90 = south in screen coords)
    if -22.5 <= angle < 22.5:
        return "east"
    elif 22.5 <= angle < 67.5:
        return "southeast"
    elif 67.5 <= angle < 112.5:
        return "south"
    elif 112.5 <= angle < 157.5:
        return "southwest"
    elif angle >= 157.5 or angle < -157.5:
        return "west"
    elif -157.5 <= angle < -112.5:
        return "northwest"
    elif -112.5 <= angle < -67.5:
        return "north"
    else:  # -67.5 <= angle < -22.5
        return "northeast"


def _get_perception_quality(distance: float) -> str:
    """Get perception quality description based on distance."""
    if distance <= 3:
        return "within arm's reach"
    elif distance <= 15:
        return "conversational distance"
    elif distance <= 50:
        return "clearly visible"
    elif distance <= 100:
        return "visible but distant"
    else:
        return "at the edge of perception"


def get_distance_to_target(target_name: str) -> float:
    """
    Get distance from UA to a named target (actor or obstacle).
    
    Args:
        target_name: Name of the target to find
        
    Returns:
        Distance in map units, or -1 if not found
    """
    try:
        from spatial_context_system import get_spatial_manager
        spatial = get_spatial_manager()
        context = spatial.get_current_context()
        
        if not context:
            return -1
        
        ua_pos = spatial.get_actor_position("ua_001")
        if not ua_pos:
            return -1
        
        target_lower = target_name.lower()
        
        # Check actors
        for actor_id, actor_pos in context.actor_positions.items():
            if actor_id != "ua_001":
                if target_lower in actor_pos.actor_name.lower():
                    dx = actor_pos.position.x - ua_pos.x
                    dy = actor_pos.position.y - ua_pos.y
                    return (dx**2 + dy**2)**0.5
        
        # Check obstacles
        if context.location_dimensions and context.location_dimensions.obstacles:
            for obs_id, obs in context.location_dimensions.obstacles.items():
                obs_name = getattr(obs, 'obstacle_name', obs_id)
                if target_lower in obs_name.lower() or target_lower in obs_id.lower():
                    if hasattr(obs, 'boundary_points') and obs.boundary_points:
                        cx = sum(p.x for p in obs.boundary_points) / len(obs.boundary_points)
                        cy = sum(p.y for p in obs.boundary_points) / len(obs.boundary_points)
                        dx = cx - ua_pos.x
                        dy = cy - ua_pos.y
                        return (dx**2 + dy**2)**0.5
        
        return -1
        
    except Exception:
        return -1
