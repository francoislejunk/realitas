"""
World Map Visualizer - ASCII/Unicode Visual World Map

Creates a visual representation of discovered locations and their connections.
Displays:
- Location nodes with types and NUAs
- Connections with travel times
- Current location highlighted
"""

from typing import Dict, List, Optional, Tuple, Set
from location_distance_tracker import get_location_tracker, LocationNode, LocationType


# Location type icons
LOCATION_ICONS = {
    LocationType.RESIDENCE: "🏠",
    LocationType.COMMERCIAL: "🏪",
    LocationType.FOOD: "🍽️",
    LocationType.ENTERTAINMENT: "🎵",
    LocationType.INDUSTRIAL: "🏭",
    LocationType.OFFICE: "🏢",
    LocationType.PUBLIC: "🌳",
    LocationType.TRANSIT: "🚉",
    LocationType.INSTITUTIONAL: "🏛️",
    LocationType.OUTDOOR: "🛤️",
    LocationType.UNKNOWN: "📍",
}


def get_location_icon(loc_type: LocationType) -> str:
    """Get icon for location type"""
    return LOCATION_ICONS.get(loc_type, "📍")


def create_location_box(loc: LocationNode, is_current: bool = False, max_width: int = 20) -> List[str]:
    """Create a box representation of a location"""
    icon = get_location_icon(loc.location_type)
    name = loc.name[:max_width-2] if len(loc.name) > max_width-2 else loc.name
    
    # Box characters
    if is_current:
        tl, tr, bl, br = "╔", "╗", "╚", "╝"
        h, v = "═", "║"
        marker = " ★ YOU"
    else:
        tl, tr, bl, br = "┌", "┐", "└", "┘"
        h, v = "─", "│"
        marker = ""
    
    # Calculate box width
    box_width = max(len(name) + 4, 16)
    
    lines = []
    
    # Top border
    lines.append(f"{tl}{h * box_width}{tr}")
    
    # Name line with icon
    name_line = f"{icon} {name}{marker}"
    padding = box_width - len(name_line)
    lines.append(f"{v}{name_line}{' ' * padding}{v}")
    
    # Type line
    type_str = f"[{loc.location_type.value}]"
    padding = box_width - len(type_str)
    lines.append(f"{v}{type_str}{' ' * padding}{v}")
    
    # NUAs (if any, show first 2)
    if loc.known_nuas:
        for nua in loc.known_nuas[:2]:
            nua_str = f"👤 {nua[:max_width-4]}"
            padding = box_width - len(nua_str)
            lines.append(f"{v}{nua_str}{' ' * padding}{v}")
        if len(loc.known_nuas) > 2:
            more_str = f"   +{len(loc.known_nuas)-2} more"
            padding = box_width - len(more_str)
            lines.append(f"{v}{more_str}{' ' * padding}{v}")
    
    # Bottom border
    lines.append(f"{bl}{h * box_width}{br}")
    
    return lines


def create_connection_line(travel_time: float, direction: str = "horizontal") -> str:
    """Create a connection line with travel time"""
    time_str = f"{travel_time:.0f}m"
    
    if direction == "horizontal":
        return f"──{time_str}──→"
    else:
        return f"│{time_str}"


def render_simple_map(storage_dir: str = "simulation_data/world_map") -> str:
    """
    Render a simple visual world map.
    Shows locations in a list format with connections.
    """
    tracker = get_location_tracker(storage_dir)
    
    if not tracker.locations:
        return "No locations discovered yet."
    
    lines = []
    lines.append("╔══════════════════════════════════════════════════════════╗")
    lines.append("║                    🗺️  WORLD MAP                         ║")
    lines.append("╠══════════════════════════════════════════════════════════╣")
    
    # Current location
    if tracker.current_location:
        lines.append(f"║  📍 Current: {tracker.current_location.title():<44} ║")
    lines.append("╠══════════════════════════════════════════════════════════╣")
    
    # Locations
    for loc_key, loc in tracker.locations.items():
        icon = get_location_icon(loc.location_type)
        is_current = loc_key == tracker.current_location
        marker = " ★" if is_current else ""
        
        # Location line
        loc_line = f"{icon} {loc.name}{marker}"
        lines.append(f"║  {loc_line:<56} ║")
        
        # Type and visits
        type_line = f"   [{loc.location_type.value}] visited {loc.visit_count}x"
        lines.append(f"║  {type_line:<56} ║")
        
        # NUAs
        if loc.known_nuas:
            nua_line = f"   👤 {', '.join(loc.known_nuas[:3])}"
            if len(loc.known_nuas) > 3:
                nua_line += f" +{len(loc.known_nuas)-3}"
            lines.append(f"║  {nua_line:<56} ║")
        
        # Connections from this location
        connections = []
        for edge_key, edge in tracker.edges.items():
            if loc_key in edge_key.split("|"):
                other = edge.to_location if edge.from_location.lower() == loc_key else edge.from_location
                connections.append((other, edge.travel_time_walking))
        
        if connections:
            conn_strs = [f"→{name}({time:.0f}m)" for name, time in connections[:3]]
            conn_line = f"   {' '.join(conn_strs)}"
            lines.append(f"║  {conn_line:<56} ║")
        
        lines.append("║  ──────────────────────────────────────────────────────  ║")
    
    lines.append("╚══════════════════════════════════════════════════════════╝")
    
    return "\n".join(lines)


def render_graph_map(storage_dir: str = "simulation_data/world_map") -> str:
    """
    Render a graph-style visual map showing nodes and connections.
    """
    tracker = get_location_tracker(storage_dir)
    
    if not tracker.locations:
        return "No locations discovered yet."
    
    lines = []
    lines.append("")
    lines.append("  ╔═══════════════════════════════════════════════════════════════╗")
    lines.append("  ║                      🗺️  WORLD MAP                            ║")
    lines.append("  ╚═══════════════════════════════════════════════════════════════╝")
    lines.append("")
    
    # Build adjacency info
    adjacency: Dict[str, List[Tuple[str, float]]] = {}
    for loc_key in tracker.locations:
        adjacency[loc_key] = []
    
    for edge_key, edge in tracker.edges.items():
        parts = edge_key.split("|")
        if len(parts) == 2:
            loc1, loc2 = parts
            if loc1 in adjacency:
                adjacency[loc1].append((loc2, edge.travel_time_walking))
            if loc2 in adjacency:
                adjacency[loc2].append((loc1, edge.travel_time_walking))
    
    # Render each location as a node
    rendered: Set[str] = set()
    
    for loc_key, loc in tracker.locations.items():
        if loc_key in rendered:
            continue
        
        is_current = loc_key == tracker.current_location
        icon = get_location_icon(loc.location_type)
        
        # Node box
        if is_current:
            box_top = "  ╔════════════════════════════╗"
            box_mid = f"  ║ {icon} {loc.name[:22]:<22} ║ ★ YOU ARE HERE"
            box_bot = "  ╚════════════════════════════╝"
        else:
            box_top = "  ┌────────────────────────────┐"
            box_mid = f"  │ {icon} {loc.name[:24]:<24} │"
            box_bot = "  └────────────────────────────┘"
        
        lines.append(box_top)
        lines.append(box_mid)
        
        # Show type
        type_line = f"  │   [{loc.location_type.value}]"
        type_line = f"{type_line:<31}│"
        lines.append(type_line)
        
        # Show NUAs
        if loc.known_nuas:
            for nua in loc.known_nuas[:2]:
                nua_line = f"  │   👤 {nua[:21]:<21}│"
                lines.append(nua_line)
        
        lines.append(box_bot)
        
        # Show connections
        connections = adjacency.get(loc_key, [])
        if connections:
            for other_key, time in connections:
                other_loc = tracker.locations.get(other_key)
                if other_loc:
                    other_icon = get_location_icon(other_loc.location_type)
                    conn_line = f"        │"
                    lines.append(conn_line)
                    conn_line = f"        ├──── {time:.0f} min ────→ {other_icon} {other_loc.name}"
                    lines.append(conn_line)
        
        lines.append("")
        rendered.add(loc_key)
    
    return "\n".join(lines)


def render_compact_map(storage_dir: str = "simulation_data/world_map") -> str:
    """
    Render a compact single-line-per-location map.
    """
    tracker = get_location_tracker(storage_dir)
    
    if not tracker.locations:
        return "No locations discovered yet."
    
    lines = []
    lines.append("┌─────────────────────────────────────────────────────────────────┐")
    lines.append("│                        🗺️  WORLD MAP                            │")
    lines.append("├─────────────────────────────────────────────────────────────────┤")
    
    for loc_key, loc in tracker.locations.items():
        is_current = loc_key == tracker.current_location
        icon = get_location_icon(loc.location_type)
        marker = "★" if is_current else " "
        
        # Get connections
        connections = []
        for edge_key, edge in tracker.edges.items():
            if loc_key in edge_key.split("|"):
                other = edge.to_location if edge.from_location.lower() == loc_key else edge.from_location
                connections.append(f"{other}({edge.travel_time_walking:.0f}m)")
        
        conn_str = " → " + ", ".join(connections[:2]) if connections else ""
        nua_count = f" [{len(loc.known_nuas)}👤]" if loc.known_nuas else ""
        
        line = f"│ {marker} {icon} {loc.name[:18]:<18}{nua_count:<8}{conn_str[:25]:<25} │"
        lines.append(line)
    
    lines.append("└─────────────────────────────────────────────────────────────────┘")
    
    if tracker.current_location:
        lines.append(f"  📍 You are at: {tracker.current_location.title()}")
    
    return "\n".join(lines)


def show_visual_world_map(style: str = "graph", storage_dir: str = "simulation_data/world_map"):
    """
    Display the visual world map.
    
    Args:
        style: "simple", "graph", or "compact"
        storage_dir: Path to world map data
    """
    if style == "simple":
        print(render_simple_map(storage_dir))
    elif style == "compact":
        print(render_compact_map(storage_dir))
    else:
        print(render_graph_map(storage_dir))


# Demo
if __name__ == "__main__":
    from location_distance_tracker import TravelMethod
    
    # Create demo data
    tracker = get_location_tracker("simulation_data/demo_world_map")
    
    tracker.set_current_location("Riverside Apartment", LocationType.RESIDENCE)
    tracker.record_travel("Riverside Apartment", "Moe's Diner", 8.0, TravelMethod.WALKING)
    tracker.set_current_location("Moe's Diner", LocationType.FOOD)
    tracker.add_nua_to_location("Dolores", "Moe's Diner")
    tracker.add_nua_to_location("Frank", "Moe's Diner")
    
    tracker.record_travel("Moe's Diner", "The Blue Note", 12.0, TravelMethod.WALKING)
    tracker.set_current_location("The Blue Note", LocationType.ENTERTAINMENT)
    tracker.add_nua_to_location("Marcus", "The Blue Note")
    
    tracker.record_travel("The Blue Note", "Central Station", 5.0, TravelMethod.WALKING)
    tracker.set_current_location("Central Station", LocationType.TRANSIT)
    
    print("\n=== GRAPH STYLE ===")
    show_visual_world_map("graph", "simulation_data/demo_world_map")
    
    print("\n=== COMPACT STYLE ===")
    show_visual_world_map("compact", "simulation_data/demo_world_map")
