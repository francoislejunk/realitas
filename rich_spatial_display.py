"""
Rich Live Spatial Display System - Real-Time Entity Tracking

Provides real-time visual tracking of all actors (UA, NUA, INUA) with:
- Live-updating map display
- Precise coordinate tracking
- Distance-based sensory information (from sensory_constants.py)
- Time unit calculations for movement
- Dynamic zone/obstacle editing

Dependencies: pip install rich
"""

import math
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.style import Style
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    print("[WARNING] Rich library not installed. Run: pip install rich")

from spatial_context_system import (
    get_spatial_manager, 
    Position, 
    DistanceCategory, 
    MovementSpeed,
    get_effective_speed,
    SpatialContextManager,
    SpatialContext
)

# Import canonical sensory constants
from sensory_constants import (
    SensoryCapabilities,
    get_distance_category,
    get_sensory_context_for_narrator,
    get_sensory_rules_for_distance,
    SENSORY_THRESHOLDS,
)


# ═══════════════════════════════════════════════════════════════════════════════
# SENSORY INFO WRAPPER - Uses canonical sensory_constants
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SensoryInfo:
    """
    Wrapper around SensoryCapabilities for backward compatibility.
    Uses canonical thresholds from sensory_constants.py.
    """
    distance: float
    can_touch: bool
    can_smell: bool
    can_whisper: bool
    can_talk: bool
    can_see_detail: bool
    can_hear_raised: bool
    can_see_general: bool
    can_hear_shout: bool
    can_see_distant: bool
    
    @classmethod
    def from_distance(cls, distance: float) -> 'SensoryInfo':
        """Create sensory info based on distance using canonical thresholds"""
        caps = SensoryCapabilities.at_distance(distance)
        return cls(
            distance=distance,
            can_touch=caps.can_touch,
            can_smell=caps.can_smell_strong,
            can_whisper=caps.can_hear_whisper,
            can_talk=caps.can_hear_speech,
            can_see_detail=caps.can_see_facial_detail,
            can_hear_raised=caps.can_hear_raised,
            can_see_general=caps.can_identify_person,
            can_hear_shout=caps.can_hear_shout,
            can_see_distant=caps.can_see_movement
        )
    
    def get_available_senses(self) -> List[str]:
        """Get list of available senses at this distance"""
        caps = SensoryCapabilities.at_distance(self.distance)
        return caps.get_available_senses_list()
    
    def get_communication_options(self) -> str:
        """Get description of communication options"""
        caps = SensoryCapabilities.at_distance(self.distance)
        return caps.get_communication_mode()


# ═══════════════════════════════════════════════════════════════════════════════
# TIME UNIT CALCULATIONS - 3-Second and 3-Minute units
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MovementTimeInfo:
    """Detailed movement time breakdown"""
    distance: float
    speed: MovementSpeed
    swiftness: int
    effective_speed: float
    time_seconds: float
    time_3sec_units: int      # 3-SECOND units (combat/action time)
    time_3min_units: int      # 3-MINUTE units (travel time)
    
    @classmethod
    def calculate(cls, start: Position, end: Position, 
                  speed: MovementSpeed = MovementSpeed.WALK,
                  swiftness: int = 3) -> 'MovementTimeInfo':
        """Calculate movement time with all unit breakdowns"""
        distance = start.distance_to(end)
        eff_speed = get_effective_speed(speed, swiftness)
        time_sec = distance / eff_speed if eff_speed > 0 else float('inf')
        
        return cls(
            distance=distance,
            speed=speed,
            swiftness=swiftness,
            effective_speed=eff_speed,
            time_seconds=time_sec,
            time_3sec_units=max(1, math.ceil(time_sec / 3.0)),
            time_3min_units=max(1, math.ceil(time_sec / 180.0))
        )
    
    def format_time(self) -> str:
        """Format time in human-readable form"""
        if self.time_seconds < 60:
            return f"{self.time_seconds:.1f}s ({self.time_3sec_units} action units)"
        elif self.time_seconds < 3600:
            mins = self.time_seconds / 60
            return f"{mins:.1f}m ({self.time_3min_units} travel units)"
        else:
            hours = self.time_seconds / 3600
            return f"{hours:.1f}h"


# ═══════════════════════════════════════════════════════════════════════════════
# RICH LIVE SPATIAL DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

class RichSpatialDisplay:
    """
    Real-time spatial display using Rich library.
    
    Features:
    - Live-updating map with actor positions
    - Distance and sensory information
    - Time unit calculations
    - Dynamic editing support
    """
    
    # Actor type symbols
    SYMBOLS = {
        'ua': '🧍',      # User Actor
        'nua': '👤',     # Non-User Actor
        'inua': '📦',    # Inanimate Non-User Actor
        'obstacle': '▪',
        'zone': '░',
        'empty': '·',
        'door': '🚪',
        'window': '🪟',
    }
    
    # Distance category colors
    DISTANCE_COLORS = {
        DistanceCategory.IMMEDIATE: "bold green",
        DistanceCategory.CLOSE: "green",
        DistanceCategory.NEAR: "yellow",
        DistanceCategory.FAR: "orange1",
        DistanceCategory.DISTANT: "red",
    }
    
    def __init__(self, session_id: Optional[str] = None):
        """Initialize the Rich spatial display"""
        if not RICH_AVAILABLE:
            raise ImportError("Rich library required. Install with: pip install rich")
        
        self.console = Console()
        self.session_id = session_id
        self._live: Optional[Live] = None
        self._update_callbacks: List[Callable] = []
    
    @property
    def spatial(self):
        """Always get fresh spatial manager to reflect current location"""
        return get_spatial_manager(session_id=self.session_id)
    
    def refresh(self):
        """Force refresh spatial data from disk"""
        # Re-get spatial manager which will reload from disk if needed
        spatial = self.spatial
        if spatial:
            spatial._load()  # Force reload from disk
        
    # ═══════════════════════════════════════════════════════════════════════════
    # CORE DISPLAY METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def generate_display(self, show_sensory: bool = True, 
                         show_time: bool = True,
                         focus_actor_id: str = "ua_001") -> Layout:
        """
        Generate the complete display layout.
        
        Args:
            show_sensory: Show sensory range information
            show_time: Show time unit calculations
            focus_actor_id: Actor to calculate distances from (usually UA)
        """
        layout = Layout()
        
        # Get current context
        context = self.spatial.get_current_context()
        if not context:
            return Panel("No spatial context available", title="Spatial Display")
        
        # Build layout sections
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        # Header
        dims = context.location_dimensions
        header_text = f"📍 {dims.location_name} | {dims.location_type} | {dims.width}×{dims.height} units"
        layout["header"].update(Panel(header_text, style="bold cyan"))
        
        # Main content split
        layout["main"].split_row(
            Layout(name="map", ratio=2),
            Layout(name="info", ratio=1)
        )
        
        # Map panel
        map_table = self._generate_map_grid(context, focus_actor_id)
        layout["main"]["map"].update(Panel(map_table, title="🗺️ Map", border_style="blue"))
        
        # Info panel (actors, distances, senses)
        info_content = self._generate_info_panel(context, focus_actor_id, show_sensory, show_time)
        layout["main"]["info"].update(info_content)
        
        # Footer with legend
        legend = "🧍 You  👤 NUA  📦 INUA/Object  🚪 Door  · Empty"
        layout["footer"].update(Panel(legend, style="dim"))
        
        return layout
    
    def _generate_map_grid(self, context: SpatialContext, 
                           focus_actor_id: str = "ua_001") -> Table:
        """Generate the map grid as a Rich Table"""
        dims = context.location_dimensions
        
        # Calculate grid size (max 40x25 for terminal display)
        scale_x = max(1, dims.width / 40)
        scale_y = max(1, dims.height / 25)
        grid_width = min(40, int(dims.width / scale_x) + 1)
        grid_height = min(25, int(dims.height / scale_y) + 1)
        
        # Initialize grid
        grid = [[self.SYMBOLS['empty'] for _ in range(grid_width)] for _ in range(grid_height)]
        
        # Draw obstacles
        for obs in dims.obstacles.values():
            if obs.boundary_points:
                cx = sum(p.x for p in obs.boundary_points) / len(obs.boundary_points)
                cy = sum(p.y for p in obs.boundary_points) / len(obs.boundary_points)
                gx = int(cx / scale_x)
                gy = grid_height - 1 - int(cy / scale_y)
                if 0 <= gx < grid_width and 0 <= gy < grid_height:
                    obs_name = obs.obstacle_name.lower()
                    if 'door' in obs_name:
                        grid[gy][gx] = self.SYMBOLS['door']
                    elif 'window' in obs_name:
                        grid[gy][gx] = self.SYMBOLS['window']
                    else:
                        grid[gy][gx] = self.SYMBOLS['inua']
        
        # Draw actors
        for actor_id, actor_pos in context.actor_positions.items():
            gx = int(actor_pos.position.x / scale_x)
            gy = grid_height - 1 - int(actor_pos.position.y / scale_y)
            if 0 <= gx < grid_width and 0 <= gy < grid_height:
                if actor_pos.is_user_actor:
                    grid[gy][gx] = self.SYMBOLS['ua']
                else:
                    grid[gy][gx] = self.SYMBOLS['nua']
        
        # Create table
        table = Table(show_header=False, box=box.SIMPLE, padding=0)
        
        # Add Y-axis labels column
        table.add_column("Y", style="dim", width=4)
        
        # Add grid columns
        for x in range(grid_width):
            table.add_column(str(x), width=2)
        
        # Add rows (top to bottom)
        for y in range(grid_height):
            y_coord = int(dims.height * (grid_height - y - 1) / grid_height)
            row = [f"{y_coord:3d}"] + list(grid[y])
            table.add_row(*row)
        
        # Add X-axis labels
        x_labels = [""] + [str(int(dims.width * x / grid_width)) if x % 5 == 0 else "" 
                          for x in range(grid_width)]
        table.add_row(*x_labels, style="dim")
        
        return table
    
    def _generate_info_panel(self, context: SpatialContext,
                             focus_actor_id: str,
                             show_sensory: bool,
                             show_time: bool) -> Panel:
        """Generate the information panel with actors, distances, and senses"""
        dims = context.location_dimensions
        focus_pos = context.actor_positions.get(focus_actor_id)
        
        # Build info sections
        sections = []
        
        # === ACTORS SECTION ===
        actors_table = Table(title="👥 Actors", box=box.ROUNDED, show_header=True)
        actors_table.add_column("Actor", style="cyan")
        actors_table.add_column("Position", style="green")
        actors_table.add_column("Zone", style="yellow")
        
        for actor_id, actor_pos in context.actor_positions.items():
            pos_str = f"({actor_pos.position.x:.1f}, {actor_pos.position.y:.1f})"
            zone = dims.get_zone_at_position(actor_pos.position)
            zone_name = zone.zone_name if zone else "-"
            
            if actor_pos.is_user_actor:
                name = f"🧍 {actor_pos.actor_name}"
            else:
                name = f"👤 {actor_pos.actor_name}"
            
            actors_table.add_row(name, pos_str, zone_name)
        
        sections.append(actors_table)
        
        # === OBJECTS/OBSTACLES SECTION ===
        if dims.obstacles:
            objects_table = Table(title="📦 Objects", box=box.ROUNDED, show_header=True)
            objects_table.add_column("Object", style="cyan")
            objects_table.add_column("Position", style="green")
            objects_table.add_column("Type", style="yellow")
            
            for obs_id, obstacle in dims.obstacles.items():
                # Get center position of obstacle
                if obstacle.boundary_points:
                    center_x = sum(p.x for p in obstacle.boundary_points) / len(obstacle.boundary_points)
                    center_y = sum(p.y for p in obstacle.boundary_points) / len(obstacle.boundary_points)
                    pos_str = f"({center_x:.1f}, {center_y:.1f})"
                else:
                    pos_str = "-"
                
                # Choose emoji based on obstacle type
                obs_type = (obstacle.obstacle_type or "").lower()
                if obs_type == "door":
                    emoji = "🚪"
                elif obs_type == "window":
                    emoji = "🪟"
                else:
                    emoji = "📦"
                
                objects_table.add_row(
                    f"{emoji} {obstacle.obstacle_name}",
                    pos_str,
                    obstacle.obstacle_type or "-"
                )
            
            sections.append(objects_table)
        
        # === DISTANCES SECTION ===
        if focus_pos and len(context.actor_positions) > 1:
            dist_table = Table(title="📏 Distances from You", box=box.ROUNDED, show_header=True)
            dist_table.add_column("Target", style="cyan")
            dist_table.add_column("Distance", style="green")
            dist_table.add_column("Category", style="yellow")
            
            for actor_id, actor_pos in context.actor_positions.items():
                if actor_id == focus_actor_id:
                    continue
                
                distance = focus_pos.position.distance_to(actor_pos.position)
                category = focus_pos.position.get_distance_category(actor_pos.position)
                color = self.DISTANCE_COLORS.get(category, "white")
                
                dist_table.add_row(
                    actor_pos.actor_name,
                    f"{distance:.1f} units",
                    Text(category.value.upper(), style=color)
                )
            
            sections.append(dist_table)
        
        # === SENSORY SECTION ===
        if show_sensory and focus_pos and len(context.actor_positions) > 1:
            sense_table = Table(title="👁️ Sensory Range", box=box.ROUNDED, show_header=True)
            sense_table.add_column("Target", style="cyan")
            sense_table.add_column("Available Senses", style="green")
            
            for actor_id, actor_pos in context.actor_positions.items():
                if actor_id == focus_actor_id:
                    continue
                
                distance = focus_pos.position.distance_to(actor_pos.position)
                sensory = SensoryInfo.from_distance(distance)
                senses = sensory.get_available_senses()
                
                sense_table.add_row(
                    actor_pos.actor_name,
                    ", ".join(senses[:4]) + ("..." if len(senses) > 4 else "")
                )
            
            sections.append(sense_table)
        
        # === TIME SECTION ===
        if show_time and focus_pos and len(context.actor_positions) > 1:
            time_table = Table(title="⏱️ Movement Time (Walking)", box=box.ROUNDED, show_header=True)
            time_table.add_column("Target", style="cyan")
            time_table.add_column("Time", style="green")
            time_table.add_column("3-Sec Units", style="yellow")
            
            for actor_id, actor_pos in context.actor_positions.items():
                if actor_id == focus_actor_id:
                    continue
                
                time_info = MovementTimeInfo.calculate(
                    focus_pos.position, 
                    actor_pos.position,
                    MovementSpeed.WALK,
                    swiftness=3
                )
                
                time_table.add_row(
                    actor_pos.actor_name,
                    f"{time_info.time_seconds:.1f}s",
                    str(time_info.time_3sec_units)
                )
            
            sections.append(time_table)
        
        # Combine sections
        from rich.console import Group
        return Panel(Group(*sections), title="📊 Information", border_style="green")
    
    # ═══════════════════════════════════════════════════════════════════════════
    # DISPLAY METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def show(self, show_sensory: bool = True, show_time: bool = True):
        """Display the spatial map once (static)"""
        display = self.generate_display(show_sensory, show_time)
        self.console.print(display)
    
    def show_live(self, refresh_per_second: float = 4.0) -> Live:
        """
        Start live display that updates automatically.
        
        Returns the Live object so caller can update it.
        
        Usage:
            display = RichSpatialDisplay()
            with display.show_live() as live:
                # Move actors, live display updates automatically
                spatial.move_actor("nua_001", Position(5, 5))
                live.refresh()  # Force immediate refresh
        """
        self._live = Live(
            self.generate_display(),
            console=self.console,
            refresh_per_second=refresh_per_second,
            screen=False
        )
        return self._live
    
    def refresh(self):
        """Refresh the live display if active"""
        if self._live:
            self._live.update(self.generate_display())
    
    # ═══════════════════════════════════════════════════════════════════════════
    # QUICK INFO METHODS
    # ═══════════════════════════════════════════════════════════════════════════
    
    def show_actor_info(self, actor_id: str):
        """Show detailed info for a specific actor"""
        context = self.spatial.get_current_context()
        if not context:
            self.console.print("[red]No spatial context available[/red]")
            return
        
        actor_pos = context.actor_positions.get(actor_id)
        if not actor_pos:
            self.console.print(f"[red]Actor {actor_id} not found[/red]")
            return
        
        dims = context.location_dimensions
        zone = dims.get_zone_at_position(actor_pos.position)
        
        table = Table(title=f"Actor: {actor_pos.actor_name}", box=box.DOUBLE)
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("ID", actor_id)
        table.add_row("Position", f"({actor_pos.position.x:.2f}, {actor_pos.position.y:.2f})")
        table.add_row("Zone", zone.zone_name if zone else "None")
        table.add_row("Type", "User Actor" if actor_pos.is_user_actor else "Non-User Actor")
        table.add_row("Active", "Yes" if actor_pos.is_active else "No")
        
        self.console.print(table)
    
    def show_distance_info(self, actor1_id: str, actor2_id: str):
        """Show detailed distance and sensory info between two actors"""
        context = self.spatial.get_current_context()
        if not context:
            self.console.print("[red]No spatial context available[/red]")
            return
        
        pos1 = context.actor_positions.get(actor1_id)
        pos2 = context.actor_positions.get(actor2_id)
        
        if not pos1 or not pos2:
            self.console.print("[red]One or both actors not found[/red]")
            return
        
        distance = pos1.position.distance_to(pos2.position)
        category = pos1.position.get_distance_category(pos2.position)
        sensory = SensoryInfo.from_distance(distance)
        time_walk = MovementTimeInfo.calculate(pos1.position, pos2.position, MovementSpeed.WALK, 3)
        time_run = MovementTimeInfo.calculate(pos1.position, pos2.position, MovementSpeed.RUN, 3)
        
        # Has line of sight?
        dims = context.location_dimensions
        has_los = dims.has_line_of_sight(pos1.position, pos2.position)
        
        table = Table(title=f"📏 {pos1.actor_name} → {pos2.actor_name}", box=box.DOUBLE)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Distance", f"{distance:.2f} units")
        table.add_row("Category", Text(category.value.upper(), style=self.DISTANCE_COLORS.get(category, "white")))
        table.add_row("Line of Sight", "✅ Clear" if has_los else "❌ Blocked")
        table.add_row("", "")
        table.add_row("[bold]Movement Time[/bold]", "")
        table.add_row("  Walking", f"{time_walk.time_seconds:.1f}s ({time_walk.time_3sec_units} action units)")
        table.add_row("  Running", f"{time_run.time_seconds:.1f}s ({time_run.time_3sec_units} action units)")
        table.add_row("", "")
        table.add_row("[bold]Available Senses[/bold]", "")
        for sense in sensory.get_available_senses():
            table.add_row("", sense)
        table.add_row("", "")
        table.add_row("Communication", sensory.get_communication_options())
        
        self.console.print(table)
    
    def show_all_distances(self, from_actor_id: str = "ua_001"):
        """Show distances from one actor to all others"""
        context = self.spatial.get_current_context()
        if not context:
            self.console.print("[red]No spatial context available[/red]")
            return
        
        from_pos = context.actor_positions.get(from_actor_id)
        if not from_pos:
            self.console.print(f"[red]Actor {from_actor_id} not found[/red]")
            return
        
        table = Table(title=f"📏 Distances from {from_pos.actor_name}", box=box.DOUBLE)
        table.add_column("Actor", style="cyan")
        table.add_column("Distance", style="green")
        table.add_column("Category", style="yellow")
        table.add_column("Walk Time", style="blue")
        table.add_column("Action Units", style="magenta")
        table.add_column("Senses", style="white")
        
        for actor_id, actor_pos in context.actor_positions.items():
            if actor_id == from_actor_id:
                continue
            
            distance = from_pos.position.distance_to(actor_pos.position)
            category = from_pos.position.get_distance_category(actor_pos.position)
            sensory = SensoryInfo.from_distance(distance)
            time_info = MovementTimeInfo.calculate(from_pos.position, actor_pos.position)
            
            senses = sensory.get_available_senses()
            sense_str = ", ".join([s.split()[0] for s in senses[:3]])  # Just emojis
            
            table.add_row(
                actor_pos.actor_name,
                f"{distance:.1f}",
                Text(category.value, style=self.DISTANCE_COLORS.get(category, "white")),
                f"{time_info.time_seconds:.1f}s",
                str(time_info.time_3sec_units),
                sense_str
            )
        
        self.console.print(table)


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL ACCESSOR AND CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

_rich_display: Optional[RichSpatialDisplay] = None

def get_rich_display(session_id: Optional[str] = None) -> RichSpatialDisplay:
    """Get or create global Rich spatial display"""
    global _rich_display
    if _rich_display is None or _rich_display.session_id != session_id:
        _rich_display = RichSpatialDisplay(session_id=session_id)
    return _rich_display


def show_spatial_map(session_id: Optional[str] = None):
    """Quick function to show spatial map"""
    display = get_rich_display(session_id)
    display.show()


def show_distances(from_actor: str = "ua_001", session_id: Optional[str] = None):
    """Quick function to show all distances from an actor"""
    display = get_rich_display(session_id)
    display.show_all_distances(from_actor)


def show_distance_between(actor1: str, actor2: str, session_id: Optional[str] = None):
    """Quick function to show distance between two actors"""
    display = get_rich_display(session_id)
    display.show_distance_info(actor1, actor2)


def get_sensory_info(distance: float) -> SensoryInfo:
    """Get sensory capabilities at a given distance"""
    return SensoryInfo.from_distance(distance)


def get_movement_time(start: Position, end: Position, 
                      speed: MovementSpeed = MovementSpeed.WALK,
                      swiftness: int = 3) -> MovementTimeInfo:
    """Calculate movement time between two positions"""
    return MovementTimeInfo.calculate(start, end, speed, swiftness)


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION HELPER - For use in main simulation loop
# ═══════════════════════════════════════════════════════════════════════════════

def get_sensory_context_for_narrator(
    observer_id: str = "ua_001",
    target_id: Optional[str] = None,
    session_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Get sensory context for narrator/LLM prompts.
    
    Returns dict with:
    - observer_position: (x, y)
    - targets: list of {name, distance, category, senses, communication}
    - can_see_all: bool
    - can_hear_all: bool
    
    This helps the narrator describe what the observer can perceive.
    """
    spatial = get_spatial_manager(session_id=session_id)
    context = spatial.get_current_context()
    
    if not context:
        return {"error": "No spatial context"}
    
    observer = context.actor_positions.get(observer_id)
    if not observer:
        return {"error": f"Observer {observer_id} not found"}
    
    dims = context.location_dimensions
    result = {
        "observer_position": (observer.position.x, observer.position.y),
        "observer_zone": None,
        "targets": [],
        "can_see_all": True,
        "can_hear_all": True,
    }
    
    # Get observer's zone
    zone = dims.get_zone_at_position(observer.position)
    if zone:
        result["observer_zone"] = zone.zone_name
    
    # Process targets
    for actor_id, actor_pos in context.actor_positions.items():
        if actor_id == observer_id:
            continue
        
        if target_id and actor_id != target_id:
            continue
        
        distance = observer.position.distance_to(actor_pos.position)
        category = observer.position.get_distance_category(actor_pos.position)
        sensory = SensoryInfo.from_distance(distance)
        has_los = dims.has_line_of_sight(observer.position, actor_pos.position)
        time_info = MovementTimeInfo.calculate(observer.position, actor_pos.position)
        
        target_info = {
            "id": actor_id,
            "name": actor_pos.actor_name,
            "position": (actor_pos.position.x, actor_pos.position.y),
            "distance": distance,
            "distance_category": category.value,
            "has_line_of_sight": has_los,
            "senses": sensory.get_available_senses(),
            "communication": sensory.get_communication_options(),
            "can_touch": sensory.can_touch,
            "can_talk": sensory.can_talk,
            "can_see_detail": sensory.can_see_detail,
            "can_see_general": sensory.can_see_general,
            "movement_time_seconds": time_info.time_seconds,
            "movement_action_units": time_info.time_3sec_units,
        }
        
        result["targets"].append(target_info)
        
        # Update global flags
        if not sensory.can_see_general:
            result["can_see_all"] = False
        if not sensory.can_hear_shout:
            result["can_hear_all"] = False
    
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# TEST / DEMO
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    if not RICH_AVAILABLE:
        print("Rich library not available. Install with: pip install rich")
        exit(1)
    
    console = Console()
    console.print("\n[bold cyan]Rich Spatial Display Demo[/bold cyan]\n")
    
    # Create test spatial context
    spatial = get_spatial_manager(session_id="demo")
    
    # Create a test location
    if not spatial.location_exists("Demo Room"):
        spatial.create_location(
            location_name="Demo Room",
            width=20,
            height=15,
            location_type="interior",
            description="A test room for the spatial display"
        )
    
    spatial.set_current_location("Demo Room")
    
    # Add test actors
    if not spatial.get_actor_position("ua_001"):
        spatial.add_actor("ua_001", "Player", Position(10, 7), is_user_actor=True)
    if not spatial.get_actor_position("nua_001"):
        spatial.add_actor("nua_001", "Guard", Position(5, 3), is_user_actor=False)
    if not spatial.get_actor_position("nua_002"):
        spatial.add_actor("nua_002", "Shopkeeper", Position(15, 12), is_user_actor=False)
    
    # Show the display
    display = RichSpatialDisplay(session_id="demo")
    display.show()
    
    console.print("\n[bold]Distance Details:[/bold]")
    display.show_all_distances("ua_001")
    
    console.print("\n[bold]Detailed Distance Info:[/bold]")
    display.show_distance_info("ua_001", "nua_001")
    
    # Show sensory context for narrator
    console.print("\n[bold]Sensory Context for Narrator:[/bold]")
    sensory_ctx = get_sensory_context_for_narrator("ua_001", session_id="demo")
    from rich.pretty import pprint
    pprint(sensory_ctx)
