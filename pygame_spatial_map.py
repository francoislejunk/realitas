"""
Pygame Spatial Map - Dungeon/Building Style Map

A persistent, interactive map window with:
- Grid-based layout with clear squares
- Thick black walls defining rooms
- Doorways shown as gaps in walls
- Numbered rooms/zones
- Actor tokens (UA, NUA, MNUA, INUA)
- Clean, readable tabletop RPG aesthetic

Runs in a separate thread so it doesn't block the main game loop.
"""

import threading
import queue
import time
import math
import random
import os
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
import json

# Pygame import with fallback
try:
    import pygame
    import pygame.gfxdraw
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    print("[WARNING] Pygame not installed. Run: pip install pygame")


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS & CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

class ActorType(Enum):
    """Actor categories for the map"""
    UA = "ua"           # User Actor (player)
    NUA = "nua"         # Non-User Actor (standard NPC)
    MNUA = "mnua"       # Major Non-User Actor (important recurring NPC)
    INUA = "inua"       # Inanimate Non-User Actor (objects)


class MapMode(Enum):
    """Map display mode"""
    LOCAL = "local"     # Current location/room layout
    WORLD = "world"     # Global location graph


# Sensory range constants (in map units)
# These are MAX ranges - walls/obstacles block line of sight
class SensoryRange:
    """Fixed sensory parameters based on distance"""
    # For a 250x200 building, vision should be ~100-150 (half the building)
    # This represents clear line of sight in open areas
    VISION = 100.0      # Can see up to 100 units (limited by walls indoors)
    HEARING = 80.0      # Can hear up to 80 units (sound travels through walls)
    SMELL = 30.0        # Can smell up to 30 units
    TOUCH = 2.0         # Must be within 2 units for touch
    TASTE = 1.0         # Must be within 1 unit (essentially touching)
    
    # Conversation distances
    WHISPER = 3.0       # Whisper range
    TALK = 15.0         # Normal conversation
    SHOUT = 60.0        # Shouting range


class LocationScale:
    """
    Dynamic map scaling based on location type.
    
    Determines appropriate map dimensions based on context.
    """
    # Scale presets: (width, height) in meters
    SCALES = {
        # Interiors - small focus
        "interior": (50, 40),
        "room": (30, 25),
        "office": (40, 30),
        "apartment": (60, 50),
        "building": (100, 80),
        
        # Urban - medium focus
        "urban": (500, 400),
        "street": (300, 100),
        "block": (400, 400),
        "plaza": (200, 200),
        
        # Rural - large focus
        "rural": (2000, 2000),
        "farm": (1000, 800),
        "village": (1500, 1200),
        
        # Wilderness - very large
        "wilderness": (10000, 10000),
        "forest": (5000, 5000),
        "mountain": (8000, 8000),
        
        # Vehicles - dynamic based on speed
        "vehicle": (500, 400),  # Base, scales with speed
    }
    
    # Context-based zoom adjustments
    CONTEXT_ZOOM = {
        "combat": 1.5,      # Zoom in for combat (50m buffer)
        "stealth": 1.2,     # Moderate zoom for stealth (250m sensing)
        "social": 2.0,      # Tight zoom for conversation (10m)
        "exploration": 0.8, # Zoom out for exploration
        "travel": 0.5,      # Wide view for travel
    }
    
    @classmethod
    def get_scale(cls, location_type: str) -> tuple:
        """Get appropriate scale for location type"""
        location_type = location_type.lower()
        
        # Check for exact match
        if location_type in cls.SCALES:
            return cls.SCALES[location_type]
        
        # Check for partial match
        for key, scale in cls.SCALES.items():
            if key in location_type or location_type in key:
                return scale
        
        # Default to interior
        return cls.SCALES["interior"]
    
    @classmethod
    def get_context_zoom(cls, context: str) -> float:
        """Get zoom multiplier for context"""
        return cls.CONTEXT_ZOOM.get(context.lower(), 1.0)


# Colors (RGB) - Dungeon Map Style
class Colors:
    # Map background - parchment/paper style
    BACKGROUND = (245, 240, 230)      # Light parchment
    EXTERIOR = (180, 175, 165)        # Hatched exterior area
    
    # Grid
    GRID = (200, 195, 185)            # Subtle grid lines
    GRID_MAJOR = (180, 175, 165)      # Slightly darker major lines
    
    # Walls and structure
    WALL = (30, 30, 30)               # Thick black walls
    WALL_OUTLINE = (50, 50, 50)       # Wall outline
    DOOR = (245, 240, 230)            # Door gaps (same as floor)
    DOOR_FRAME = (100, 80, 60)        # Door frame color
    
    # Floor
    FLOOR = (250, 245, 235)           # Interior floor (slightly lighter)
    
    # Actors - Token style
    UA = (50, 150, 80)                # Green - player token
    UA_BORDER = (30, 100, 50)         # Darker green border
    NUA = (70, 130, 200)              # Blue - standard NPC
    NUA_BORDER = (40, 90, 150)        # Darker blue border
    MNUA = (220, 180, 50)             # Gold - major NPC
    MNUA_BORDER = (180, 140, 30)      # Darker gold border
    INUA = (140, 100, 70)             # Brown - objects
    INUA_BORDER = (100, 70, 50)       # Darker brown border
    
    # Zone labels
    ZONE_NUMBER_BG = (30, 30, 30)     # Black circle for zone numbers
    ZONE_NUMBER_TEXT = (255, 255, 255) # White text
    ZONE_LABEL = (80, 80, 80)         # Zone name text
    
    # Sensory ranges (semi-transparent)
    VISION_RANGE = (100, 150, 200, 40)
    HEARING_RANGE = (200, 150, 100, 30)
    SMELL_RANGE = (150, 200, 100, 50)
    TOUCH_RANGE = (150, 150, 150, 80)
    
    # UI
    TEXT = (50, 50, 50)
    TEXT_HIGHLIGHT = (30, 30, 30)
    PANEL_BG = (255, 250, 240, 230)
    SELECTED = (255, 200, 50)
    SELECTED_GLOW = (255, 220, 100, 100)
    
    # Movement trails - more visible/darker
    TRAIL_UA = (40, 160, 80, 220)         # Darker green trail for UA
    TRAIL_NUA = (60, 120, 200, 220)       # Darker blue trail for NUA
    TRAIL_DOT = (50, 50, 50, 180)         # Trail waypoint dots
    
    # Door/Exit markers
    DOOR_MARKER = (180, 100, 50)          # Orange-brown door marker
    DOOR_MARKER_GLOW = (255, 200, 100, 80) # Glow around doors

    # World map
    WORLD_EDGE = (90, 90, 90)
    WORLD_EDGE_UNKNOWN = (140, 140, 140)
    WORLD_NODE = (230, 230, 230)
    WORLD_NODE_BORDER = (60, 60, 60)
    WORLD_NODE_CURRENT = (80, 160, 110)
    WORLD_NODE_UNKNOWN = (210, 210, 210)
    WORLD_NODE_SELECTED = (255, 200, 50)


# ═══════════════════════════════════════════════════════════════════════════════
# NARRATIVE PANEL CONSTANTS  (embedded in pmap window, below the map)
# ═══════════════════════════════════════════════════════════════════════════════

_NAR_H      = 350   # narrative section height (pixels, below map)
_NAR_DIV    = 4     # divider line thickness
_NAR_HDR    = 34    # header bar height
_NAR_INP    = 56    # input bar height
_NAR_SCR_W  = 6     # scrollbar width
_NAR_PAD    = 16    # horizontal padding
_NAR_MAX    = 600   # max messages to keep

# Dark narrative theme ─────────────────────────────────────────────────────────
_NAR_BG     = (13,  13,  20)
_NAR_HDBG   = (8,   8,  14)
_NAR_INPBG  = (18,  18,  30)
_NAR_CHR    = (32,  28,  50)
_NAR_TITLE  = (155, 148, 200)
_NAR_BAR_BG = (20,  18,  30)
_NAR_BAR_FG = (58,  52,  84)
_NAR_BORDA  = (115,  85, 175)
_NAR_BORDI  = (42,   38,  62)

_NAR_TYPE_COLORS = {
    "scene":      (200, 180, 255),
    "narrator":   (218, 212, 202),
    "perceptual": (145, 138, 158),
    "iv":         (140, 218, 232),
    "iv_voice":   (210, 168, 252),
    "iv_ua":      (160, 238, 185),
    "system":     (100, 158, 208),
    "separator":  (40,   38,  60),
    "prompt":     (240, 214, 128),
    "user_input": (240, 214, 128),
}
_NAR_ACCENT = {
    "scene":      (130, 100, 210),
    "narrator":   None,
    "perceptual": (80,  72, 100),
    "iv":         (75, 185, 210),
    "iv_voice":   (165, 110, 220),
    "iv_ua":      (90, 195, 130),
    "system":     None,
    "separator":  None,
    "prompt":     (195, 165, 70),
    "user_input": (195, 165, 70),
}
_NAR_TINTS = {
    "scene":      (20, 16, 32),
    "narrator":   None,
    "perceptual": None,
    "iv":         (13, 20, 30),
    "iv_voice":   (20, 14, 30),
    "iv_ua":      (12, 22, 18),
    "system":     None,
    "separator":  None,
    "prompt":     (22, 20, 12),
    "user_input": (22, 20, 12),
}


# ═══════════════════════════════════════════════════════════════════════════════
# DATA STRUCTURES
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class MapActor:
    """Actor data for map display"""
    actor_id: str
    name: str
    actor_type: ActorType
    x: float
    y: float
    # S-trait outliers for display
    s_trait_outliers: List[str] = field(default_factory=list)
    # Additional info
    occupation: str = ""
    is_selected: bool = False
    facing_direction: float = 0.0  # Degrees, 0=North, 90=East
    
    # Movement trail - list of (x, y, timestamp) tuples
    trail: List[Tuple[float, float, float]] = field(default_factory=list)
    max_trail_length: int = 2   # Max waypoints to keep (2 = last 2 turns)
    trail_duration: float = 300.0  # 5 minutes in seconds
    
    # Calculated trail info (updated on sync)
    trail_distance: float = 0.0  # Total distance along trail
    straight_distance: float = 0.0  # Straight-line from start
    average_speed: float = 0.0  # Units per second


@dataclass
class MapObstacle:
    """Obstacle data for map display"""
    obstacle_id: str
    name: str
    x: float
    y: float
    width: float = 2.0
    height: float = 2.0
    blocks_los: bool = False
    obstacle_type: str = ""  # "door", "window", "furniture", etc.


@dataclass
class MapWall:
    """Wall segment for dungeon-style map"""
    wall_id: str
    start: Tuple[float, float]  # (x, y) start point
    end: Tuple[float, float]    # (x, y) end point
    thickness: float = 0.5      # Wall thickness in units
    has_door: bool = False
    door_position: float = 0.5  # 0-1, position along wall


@dataclass
class MapRoom:
    """Room/zone with walls for dungeon-style map"""
    room_id: str
    name: str
    number: int = 0             # Room number for display
    bounds: Tuple[float, float, float, float] = (0, 0, 10, 10)  # x, y, width, height
    walls: List[str] = field(default_factory=list)  # Wall IDs
    description: str = ""
    is_exterior: bool = False   # If True, draw hatched pattern


@dataclass
class MapZone:
    """Zone data for map display (legacy support)"""
    zone_id: str
    name: str
    points: List[Tuple[float, float]]  # Boundary polygon
    description: str = ""
    number: int = 0  # Zone number for display


@dataclass
class MapState:
    """Complete map state with dynamic scaling support"""
    location_name: str = "Unknown"
    location_type: str = "interior"
    width: float = 20.0
    height: float = 20.0
    grid_size: float = 1.0      # Size of each grid square in units
    wall_thickness: int = 4     # Wall thickness in pixels
    
    actors: Dict[str, MapActor] = field(default_factory=dict)
    obstacles: Dict[str, MapObstacle] = field(default_factory=dict)
    zones: Dict[str, MapZone] = field(default_factory=dict)
    walls: Dict[str, MapWall] = field(default_factory=dict)
    rooms: Dict[str, MapRoom] = field(default_factory=dict)
    
    # View settings
    show_vision_range: bool = False
    show_hearing_range: bool = False
    
    # Context-based zoom
    current_context: str = "exploration"  # combat, stealth, social, exploration, travel
    auto_zoom_enabled: bool = True
    follow_ua: bool = True  # Auto-center on UA
    
    # Geographic mode support
    is_geographic: bool = False
    origin_lat: float = 0.0
    origin_lon: float = 0.0
    show_smell_range: bool = False
    show_touch_range: bool = False
    show_grid: bool = True
    show_zones: bool = True
    show_zone_numbers: bool = True

    # Universal map mode
    map_mode: MapMode = MapMode.LOCAL

    local_location_name: str = "Unknown"
    local_location_type: str = "interior"
    local_width: float = 20.0
    local_height: float = 20.0

    world_canvas_name: str = "World Map"
    world_canvas_width: float = 1000.0
    world_canvas_height: float = 1000.0

    # World graph state (only used when map_mode == WORLD)
    world_nodes: Dict[str, Dict[str, Any]] = field(default_factory=dict)  # key -> {name,x,y,is_unknown,is_current}
    world_edges: List[Dict[str, Any]] = field(default_factory=list)       # {a,b,is_unknown,minutes}
    world_current_location: str = ""
    selected_world_node: Optional[str] = None


# ═══════════════════════════════════════════════════════════════════════════════
# PYGAME MAP WINDOW
# ═══════════════════════════════════════════════════════════════════════════════

class PygameSpatialMap:
    """
    Pygame-based spatial map window.
    
    Runs in a separate thread and receives updates via a queue.
    """
    
    # Window settings
    DEFAULT_WIDTH = 800
    DEFAULT_HEIGHT = 600
    MIN_ZOOM = 0.5
    WORLD_MIN_ZOOM = 0.15
    MAX_ZOOM = 50.0
    
    def __init__(self):
        self.state = MapState()
        self.update_queue: queue.Queue = queue.Queue()
        self.outbox_queue: queue.Queue = queue.Queue()
        self.running = False
        self.thread: Optional[threading.Thread] = None

        # When True: run headless (no own window) — legacy, kept for compat
        self.suppress_own_window: bool = False

        # ── Narrative panel state ─────────────────────────────────────────────
        self._nar_port: int = 0          # TCP port (set once server is ready)
        self._nar_msgs: list = []        # [(text, type_str), ...]
        self._nar_vessel: str = ""
        self._nar_input: str = ""
        self._nar_cursor: int = 0
        self._nar_waiting: bool = False
        self._nar_wait_conn = None
        self._nar_scroll: int = 0
        self._nar_conns: list = []
        self._nar_bufs: dict = {}
        self._nar_font_body = None
        self._nar_font_label = None
        self._nar_font_input = None
        self._nar_font_title = None

        # View state
        self.zoom = 1.0
        self.pan_x = 0.0
        self.pan_y = 0.0
        self.selected_actor: Optional[str] = None
        self.selected_obstacle: Optional[str] = None

        # Pygame surfaces (initialized in thread)
        self.screen = None
        self.clock = None
        self.font = None
        self.font_small = None

    def pop_action(self) -> Optional[Tuple[str, Any]]:
        """Pop one pending UI action from the map thread (thread-safe)."""
        try:
            return self.outbox_queue.get_nowait()
        except Exception:
            return None

    def set_mode(self, mode: MapMode):
        """Set current map mode (thread-safe)."""
        try:
            self.update_queue.put(('mode', mode))
        except Exception:
            pass

    def toggle_mode(self):
        """Toggle map mode (thread-safe)."""
        try:
            self.update_queue.put(('toggle_mode', None))
        except Exception:
            pass

    def sync_world_graph(self, session_id: Optional[str] = None):
        """Sync the world graph state from LocationDistanceTracker (thread-safe)."""
        try:
            from location_distance_tracker import get_location_tracker
            tracker = get_location_tracker(session_id or "simulation_data/world_map")

            nodes, edges, current_loc = _build_world_graph_layout(tracker)
            payload = {
                'nodes': nodes,
                'edges': edges,
                'current_location': current_loc,
            }
            self.update_queue.put(('world_graph', payload))
        except Exception:
            pass
        
    def start(self):
        """Start the map window in a separate thread"""
        if not PYGAME_AVAILABLE:
            print("[PMAP] Pygame not available")
            return False
        
        if self.running:
            print("[PMAP] Already running")
            return True
        
        try:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()
            # Give the thread a moment to initialize
            import time
            time.sleep(0.2)
            print(f"[PMAP] Thread started, running={self.running}")
            return True
        except Exception as e:
            print(f"[PMAP] Failed to start thread: {e}")
            self.running = False
            return False
    
    def stop(self):
        """Stop the map window"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1.0)
            self.thread = None
    
    def update_state(self, new_state: MapState):
        """Queue a state update (thread-safe)"""
        self.update_queue.put(('state', new_state))
    
    def update_actor(self, actor: MapActor):
        """Queue an actor update (thread-safe)"""
        self.update_queue.put(('actor', actor))
    
    def remove_actor(self, actor_id: str):
        """Queue an actor removal (thread-safe)"""
        self.update_queue.put(('remove_actor', actor_id))
    
    def update_location(self, name: str, width: float, height: float, loc_type: str = "interior"):
        """Queue a location change (thread-safe)"""
        self.update_queue.put(('location', (name, width, height, loc_type)))
    
    def get_display_state(self) -> dict:
        """Return serializable map state for external rendering (e.g. narrative display)."""
        # In headless mode the background thread is sleeping; flush the queue here
        # so the state reflects any updates queued by the main thread.
        if self.suppress_own_window:
            self._process_updates()
        state = self.state
        actors = {}
        for aid, a in state.actors.items():
            actors[aid] = {
                "name": a.name,
                "type": a.actor_type.value,
                "x": a.x,
                "y": a.y,
            }
        obstacles = {}
        for oid, o in state.obstacles.items():
            obstacles[oid] = {
                "name": o.name,
                "x": o.x,
                "y": o.y,
                "width": o.width,
                "height": o.height,
            }
        return {
            "location_name": state.location_name,
            "width": state.width,
            "height": state.height,
            "actors": actors,
            "obstacles": obstacles,
        }

    def _run_loop(self):
        """Main pygame loop (runs in thread)"""
        # Legacy headless mode (suppress_own_window) — just process queue
        if self.suppress_own_window:
            while self.running:
                self._process_updates()
                time.sleep(0.033)
            return

        import os
        import socket as _sock

        os.environ['SDL_VIDEO_WINDOW_POS'] = '50,50'

        pygame.init()
        pygame.font.init()
        pygame.key.set_repeat(350, 45)

        # Load narrative fonts before opening window so _nar_port is set quickly
        self._nar_font_body, self._nar_font_label, self._nar_font_input, self._nar_font_title = \
            self._nar_load_fonts()

        # Start embedded narrative TCP server
        _ns = _sock.socket(_sock.AF_INET, _sock.SOCK_STREAM)
        _ns.setsockopt(_sock.SOL_SOCKET, _sock.SO_REUSEADDR, 1)
        _ns.bind(('127.0.0.1', 0))
        self._nar_port = _ns.getsockname()[1]
        _ns.listen(5)
        _ns.setblocking(False)
        print(f"[PMAP] Narrative server listening on port {self._nar_port}")

        # Combined window: map (top) + narrative panel (bottom)
        _comb_h = self.DEFAULT_HEIGHT + _NAR_DIV + _NAR_H
        self.screen = pygame.display.set_mode(
            (920, _comb_h),
            pygame.RESIZABLE | pygame.SHOWN
        )
        pygame.display.set_caption("Realitas Neo")

        # Force window to front on Windows
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info()['window']
            ctypes.windll.user32.SetForegroundWindow(hwnd)
            ctypes.windll.user32.BringWindowToTop(hwnd)
        except Exception:
            pass  # Non-critical

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.font_small = pygame.font.Font(None, 18)
        
        # For panning
        dragging = False
        last_mouse_pos = (0, 0)
        
        while self.running:
            # Poll narrative TCP connections
            self._nar_poll(_ns)

            # Process pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                    break

                elif event.type == pygame.MOUSEWHEEL:
                    _mx, _my = pygame.mouse.get_pos()
                    _sw, _sh = self.screen.get_size()
                    # Scroll narrative panel when mouse is over it; zoom map otherwise
                    if _my >= _sh - _NAR_H:
                        self._nar_scroll = max(0, self._nar_scroll - event.y * 45)
                    else:
                        self.zoom *= 1.1 if event.y > 0 else 0.9
                        self.zoom = max(self.MIN_ZOOM, min(self.MAX_ZOOM, self.zoom))

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    _mx, _my = event.pos
                    _sw, _sh = self.screen.get_size()
                    if _my < _sh - _NAR_H:
                        # Event is inside the map area
                        if event.button == 1:
                            self._handle_click(event.pos)
                        elif event.button == 2:
                            dragging = True
                            last_mouse_pos = event.pos
                        elif event.button == 3:
                            self.zoom = 1.0
                            self.pan_x = 0.0
                            self.pan_y = 0.0

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 2:
                        dragging = False

                elif event.type == pygame.MOUSEMOTION:
                    if dragging:
                        dx = event.pos[0] - last_mouse_pos[0]
                        dy = event.pos[1] - last_mouse_pos[1]
                        self.pan_x += dx
                        self.pan_y += dy
                        last_mouse_pos = event.pos

                elif event.type == pygame.KEYDOWN:
                    # Route keyboard to narrative input or map controls
                    if self._nar_waiting:
                        self._nar_handle_key(event)
                    else:
                        self._handle_key(event.key)

                elif event.type == pygame.VIDEORESIZE:
                    self.screen = pygame.display.set_mode(
                        (event.w, event.h),
                        pygame.RESIZABLE
                    )

            # Process update queue
            self._process_updates()

            # Render
            self._render()

            # Cap framerate
            self.clock.tick(30)

        pygame.quit()
    
    def _process_updates(self):
        """Process queued updates"""
        while not self.update_queue.empty():
            try:
                update_type, data = self.update_queue.get_nowait()
                
                if update_type == 'state':
                    self.state = data
                    self._auto_fit_view()
                
                elif update_type == 'actor':
                    # Track movement trail
                    if data.actor_id in self.state.actors:
                        old_actor = self.state.actors[data.actor_id]
                        # Check if position changed significantly (> 1 unit)
                        dx = abs(data.x - old_actor.x)
                        dy = abs(data.y - old_actor.y)
                        if dx > 1 or dy > 1:
                            # Add old position to trail
                            data.trail = old_actor.trail.copy()
                            data.trail.append((old_actor.x, old_actor.y, time.time()))
                            # Trim trail to max length
                            if len(data.trail) > data.max_trail_length:
                                data.trail = data.trail[-data.max_trail_length:]
                        else:
                            # Keep existing trail
                            data.trail = old_actor.trail
                    self.state.actors[data.actor_id] = data
                
                elif update_type == 'remove_actor':
                    if data in self.state.actors:
                        del self.state.actors[data]
                
                elif update_type == 'location':
                    name, width, height, loc_type = data
                    self.state.location_name = name
                    self.state.width = width
                    self.state.height = height
                    self.state.location_type = loc_type

                    self.state.local_location_name = name
                    self.state.local_width = width
                    self.state.local_height = height
                    self.state.local_location_type = loc_type

                    self.state.actors.clear()
                    self.state.obstacles.clear()
                    self.state.zones.clear()
                    self._auto_fit_view()

                elif update_type == 'mode':
                    if isinstance(data, MapMode):
                        self.state.map_mode = data
                        self._apply_canvas_for_mode(data)
                        self._auto_fit_view()

                elif update_type == 'toggle_mode':
                    self.state.map_mode = MapMode.WORLD if self.state.map_mode == MapMode.LOCAL else MapMode.LOCAL
                    self._apply_canvas_for_mode(self.state.map_mode)
                    self._auto_fit_view()

                elif update_type == 'world_graph':
                    try:
                        if not self.state.local_location_name:
                            self.state.local_location_name = self.state.location_name
                        if not self.state.local_width or not self.state.local_height:
                            self.state.local_width = self.state.width
                            self.state.local_height = self.state.height
                        if not self.state.local_location_type:
                            self.state.local_location_type = self.state.location_type

                        self.state.map_mode = MapMode.WORLD
                        self.state.world_nodes = dict((data or {}).get('nodes') or {})
                        self.state.world_edges = list((data or {}).get('edges') or [])
                        self.state.world_current_location = str((data or {}).get('current_location') or '')
                        self.state.selected_world_node = None

                        self.state.world_canvas_name = "World Map"
                        self.state.world_canvas_width = 1000.0
                        self.state.world_canvas_height = 1000.0

                        self._apply_canvas_for_mode(MapMode.WORLD)
                        self._auto_fit_view()
                    except Exception:
                        pass
                    
            except queue.Empty:
                break

    # ══════════════════════════════════════════════════════════════════════════
    # NARRATIVE PANEL  — embedded below the map in the same pygame window
    # ══════════════════════════════════════════════════════════════════════════

    def _nar_load_fonts(self):
        """Load monospace fonts for the narrative panel."""
        for name in ["Consolas", "Courier New", "Lucida Console",
                     "DejaVu Sans Mono", "Liberation Mono"]:
            try:
                return (
                    pygame.font.SysFont(name, 15),
                    pygame.font.SysFont(name, 11, bold=True),
                    pygame.font.SysFont(name, 15),
                    pygame.font.SysFont(name, 13, bold=True),
                )
            except Exception:
                continue
        fb = pygame.font.Font(None, 19)
        return fb, fb, fb, fb

    def _nar_poll(self, server_sock):
        """Accept and read narrative TCP connections (non-blocking)."""
        import socket as _sk
        try:
            nc, _ = server_sock.accept()
            nc.setblocking(False)
            self._nar_conns.append(nc)
            self._nar_bufs[id(nc)] = b""
        except BlockingIOError:
            pass
        dead = []
        for nc in list(self._nar_conns):
            try:
                data = nc.recv(4096)
                if not data:
                    dead.append(nc); continue
                self._nar_bufs[id(nc)] += data
                while b"\n" in self._nar_bufs[id(nc)]:
                    line, self._nar_bufs[id(nc)] = self._nar_bufs[id(nc)].split(b"\n", 1)
                    try:
                        self._nar_handle_msg(json.loads(line.decode()), nc)
                    except Exception:
                        pass
            except BlockingIOError:
                pass
            except Exception:
                dead.append(nc)
        for nc in dead:
            try: self._nar_conns.remove(nc)
            except: pass
            self._nar_bufs.pop(id(nc), None)

    def _nar_handle_msg(self, msg: dict, conn):
        mtype = msg.get("type", "narrator")
        if mtype == "vessel_name":
            self._nar_vessel = msg.get("name", "")
        elif mtype == "input_request":
            self._nar_waiting = True
            self._nar_wait_conn = conn
        elif mtype == "separator":
            self._nar_msgs.append(("", "separator"))
            if len(self._nar_msgs) > _NAR_MAX:
                self._nar_msgs = self._nar_msgs[-_NAR_MAX:]
        elif mtype in ("stop", "map_state"):
            pass  # ignored (we are the window)
        else:
            text = msg.get("text", "")
            if text:
                self._nar_msgs.append((text, mtype))
                if len(self._nar_msgs) > _NAR_MAX:
                    self._nar_msgs = self._nar_msgs[-_NAR_MAX:]

    def _nar_handle_key(self, event):
        """Handle keyboard when narrative panel is waiting for user input."""
        k = event.key
        # Let map control keys pass through even while narrative panel is waiting
        if k in (pygame.K_TAB, pygame.K_ESCAPE, pygame.K_PLUS, pygame.K_MINUS,
                 pygame.K_EQUALS, pygame.K_KP_PLUS, pygame.K_KP_MINUS,
                 pygame.K_LEFT, pygame.K_RIGHT, pygame.K_UP, pygame.K_DOWN):
            self._handle_key(k)
            return
        if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
            text = self._nar_input.strip()
            self._nar_input = ""
            self._nar_cursor = 0
            if text:
                self._nar_msgs.append((text, "user_input"))
                self._nar_scroll = 0
            if self._nar_waiting and self._nar_wait_conn:
                try:
                    reply = json.dumps({"type": "input", "text": text}) + "\n"
                    self._nar_wait_conn.sendall(reply.encode())
                except Exception:
                    pass
            self._nar_waiting = False
            self._nar_wait_conn = None
        elif k == pygame.K_BACKSPACE:
            if self._nar_cursor > 0:
                self._nar_input = (self._nar_input[:self._nar_cursor - 1]
                                   + self._nar_input[self._nar_cursor:])
                self._nar_cursor -= 1
        elif k == pygame.K_DELETE:
            if self._nar_cursor < len(self._nar_input):
                self._nar_input = (self._nar_input[:self._nar_cursor]
                                   + self._nar_input[self._nar_cursor + 1:])
        elif k == pygame.K_LEFT:
            self._nar_cursor = max(0, self._nar_cursor - 1)
        elif k == pygame.K_RIGHT:
            self._nar_cursor = min(len(self._nar_input), self._nar_cursor + 1)
        elif k == pygame.K_HOME:
            self._nar_cursor = 0
        elif k == pygame.K_END:
            self._nar_cursor = len(self._nar_input)
        elif k == pygame.K_PAGEUP:
            self._nar_scroll = min(self._nar_scroll + 200, 99999)
        elif k == pygame.K_PAGEDOWN:
            self._nar_scroll = max(0, self._nar_scroll - 200)
        elif event.unicode and ord(event.unicode) >= 32:
            self._nar_input = (self._nar_input[:self._nar_cursor]
                               + event.unicode
                               + self._nar_input[self._nar_cursor:])
            self._nar_cursor += 1

    def _nar_wrap(self, text: str, font, max_w: int) -> list:
        if not text:
            return []
        lines = []
        for para in text.split('\n'):
            if not para.strip():
                lines.append(""); continue
            words, cur = para.split(' '), ""
            for word in words:
                cand = (cur + " " + word).strip() if cur else word
                if font.size(cand)[0] <= max_w:
                    cur = cand
                else:
                    if cur: lines.append(cur)
                    if font.size(word)[0] > max_w:
                        part = ""
                        for ch in word:
                            if font.size(part + ch)[0] <= max_w:
                                part += ch
                            else:
                                if part: lines.append(part)
                                part = ch
                        cur = part
                    else:
                        cur = word
            if cur: lines.append(cur)
        return lines or [""]

    def _nar_render(self):
        """Render the narrative text panel at the bottom of the combined window."""
        if not self.screen or not self._nar_font_body:
            return
        sw, sh = self.screen.get_size()
        map_h = sh - _NAR_H   # Y where narrative panel starts

        # Background fill
        pygame.draw.rect(self.screen, _NAR_BG, (0, map_h, sw, _NAR_H))
        # Divider
        pygame.draw.rect(self.screen, _NAR_CHR, (0, map_h, sw, _NAR_DIV))

        # Header bar
        hdr_top = map_h + _NAR_DIV
        pygame.draw.rect(self.screen, _NAR_HDBG, (0, hdr_top, sw, _NAR_HDR))
        pygame.draw.line(self.screen, _NAR_CHR,
                         (0, hdr_top + _NAR_HDR), (sw, hdr_top + _NAR_HDR), 1)
        ts = self._nar_font_title.render("REALITAS  NEO", True, _NAR_TITLE)
        self.screen.blit(ts, (_NAR_PAD, hdr_top + (_NAR_HDR - ts.get_height()) // 2))
        dot_col = (85, 195, 115) if self._nar_waiting else (55, 50, 80)
        dx = sw - _NAR_PAD - 6
        dy = hdr_top + _NAR_HDR // 2
        pygame.draw.circle(self.screen, dot_col, (dx, dy), 5)
        if self._nar_waiting and self._nar_vessel:
            lbl = self._nar_font_label.render(
                f"Your turn, {self._nar_vessel}.", True, (85, 195, 115))
            self.screen.blit(lbl, (dx - lbl.get_width() - 10,
                                   hdr_top + (_NAR_HDR - lbl.get_height()) // 2))

        # Messages area
        msg_top = hdr_top + _NAR_HDR + 1
        msg_h   = _NAR_H - _NAR_DIV - _NAR_HDR - _NAR_INP - 1
        msg_w   = sw - _NAR_SCR_W - 1
        line_h  = self._nar_font_body.get_linesize() + 3
        lbl_lh  = self._nar_font_label.get_linesize() + 4
        tx0     = _NAR_PAD + 6 + 3 + 10  # ACCENT_MARG + ACCENT_W + ACCENT_PAD
        text_w  = msg_w - tx0 - _NAR_PAD

        # Build display blocks
        blocks = []
        for text, mtype in self._nar_msgs:
            if mtype == "separator":
                blocks.append(("sep", [], None, None, None, 14, None))
                continue
            vessel = self._nar_vessel or "You"
            label_map = {
                "scene": "Perception", "narrator": "Perception",
                "perceptual": "Perception",
                "iv": "Inner Voice", "iv_voice": "Inner Voice",
                "iv_ua": vessel, "prompt": vessel, "user_input": vessel,
                "system": None,
            }
            label = label_map.get(mtype)
            eff_w = text_w - (12 if mtype == "perceptual" else 0)
            lines = self._nar_wrap(text, self._nar_font_body, eff_w)
            lh = lbl_lh if label else 0
            total_h = lh + len(lines) * line_h + 7 * 2 + 2
            blocks.append((
                mtype, lines,
                _NAR_TYPE_COLORS.get(mtype, (218, 212, 202)),
                _NAR_ACCENT.get(mtype),
                _NAR_TINTS.get(mtype),
                total_h, label,
            ))

        total_h = sum(b[5] for b in blocks)
        max_scroll = max(0, total_h - msg_h)
        self._nar_scroll = min(self._nar_scroll, max_scroll)
        vp_start = max(0, total_h - msg_h - self._nar_scroll)

        self.screen.set_clip(pygame.Rect(0, msg_top, msg_w, msg_h))
        cy = 0
        for btype, lines, color, accent, bg, bh, label in blocks:
            if cy + bh <= vp_start:
                cy += bh; continue
            if cy >= vp_start + msg_h:
                break
            dy = msg_top + (cy - vp_start)

            if btype == "sep":
                sy = dy + bh // 2
                pygame.draw.line(self.screen, (40, 38, 60),
                                 (_NAR_PAD, sy), (msg_w - _NAR_PAD, sy), 1)
                cy += bh; continue

            if bg:
                pygame.draw.rect(self.screen, bg, (0, dy, msg_w, bh))
            if accent:
                pygame.draw.rect(self.screen, accent,
                                 pygame.Rect(6, dy + 4, 3, bh - 8), border_radius=2)
            ty = dy + 7
            if label:
                badge = self._nar_font_label.render(label, True, accent or color)
                self.screen.blit(badge, (tx0, ty))
                ty += lbl_lh
            extra_x = 8 if btype == "perceptual" else 0
            for line in lines:
                if line:
                    self.screen.blit(
                        self._nar_font_body.render(line, True, color),
                        (tx0 + extra_x, ty))
                ty += line_h
            cy += bh
        self.screen.set_clip(None)

        # Scrollbar
        pygame.draw.line(self.screen, _NAR_CHR, (msg_w, msg_top), (msg_w, msg_top + msg_h), 1)
        pygame.draw.rect(self.screen, _NAR_BAR_BG, (msg_w + 1, msg_top, _NAR_SCR_W, msg_h))
        if total_h > msg_h:
            ratio   = msg_h / total_h
            thumb_h = max(20, int(msg_h * ratio))
            frac    = self._nar_scroll / max(1, max_scroll)
            thumb_y = msg_top + int((msg_h - thumb_h) * (1.0 - frac))
            pygame.draw.rect(self.screen, _NAR_BAR_FG,
                             (msg_w + 2, thumb_y, _NAR_SCR_W - 2, thumb_h), border_radius=3)

        # Input box
        inp_top = map_h + _NAR_H - _NAR_INP
        pygame.draw.rect(self.screen, _NAR_HDBG, (0, inp_top, sw, _NAR_INP))
        pygame.draw.line(self.screen, _NAR_CHR, (0, inp_top), (sw, inp_top), 1)
        bx_l, bx_r = _NAR_PAD, sw - _NAR_PAD
        bx_t = inp_top + 10
        bx_h = _NAR_INP - 20
        border = _NAR_BORDA if self._nar_waiting else _NAR_BORDI
        pygame.draw.rect(self.screen, _NAR_INPBG, (bx_l, bx_t, bx_r - bx_l, bx_h), border_radius=4)
        pygame.draw.rect(self.screen, border,    (bx_l, bx_t, bx_r - bx_l, bx_h), 1, border_radius=4)
        pc = (240, 214, 128) if self._nar_waiting else (60, 56, 88)
        ps = self._nar_font_input.render(">", True, pc)
        baseline = bx_t + (bx_h - ps.get_height()) // 2
        self.screen.blit(ps, (bx_l + 10, baseline))
        inp_x  = bx_l + 28
        avail_w = bx_r - inp_x - 12
        self.screen.set_clip(pygame.Rect(inp_x, bx_t, avail_w, bx_h))
        full = self._nar_font_input.render(self._nar_input, True, (240, 214, 128))
        cur_px = self._nar_font_input.size(self._nar_input[:self._nar_cursor])[0]
        txt_scroll = max(0, cur_px - avail_w + 20)
        self.screen.blit(full, (inp_x - txt_scroll, baseline))
        if int(time.time() * 2) % 2 == 0:
            cx = inp_x + cur_px - txt_scroll
            pygame.draw.rect(self.screen, (240, 214, 128),
                             (cx, baseline, 2, self._nar_font_input.get_height()))
        self.screen.set_clip(None)

    def _apply_canvas_for_mode(self, mode: MapMode):
        try:
            if mode == MapMode.WORLD:
                self.state.location_name = self.state.world_canvas_name or "World Map"
                self.state.width = float(self.state.world_canvas_width or 1000.0)
                self.state.height = float(self.state.world_canvas_height or 1000.0)
                self.state.location_type = "world"
            else:
                self.state.location_name = self.state.local_location_name or self.state.location_name
                self.state.width = float(self.state.local_width or self.state.width)
                self.state.height = float(self.state.local_height or self.state.height)
                self.state.location_type = self.state.local_location_type or self.state.location_type
        except Exception:
            pass
    
    def _auto_fit_view(self):
        """Auto-fit zoom and pan to show entire location"""
        if self.screen is None:
            return

        screen_w, screen_h = self.screen.get_size()
        # Only consider the map area (above the narrative panel)
        screen_h = screen_h - _NAR_H - _NAR_DIV
        margin = 50

        # Calculate zoom to fit
        zoom_x = (screen_w - margin * 2) / max(1, self.state.width)
        zoom_y = (screen_h - margin * 2) / max(1, self.state.height)
        self.zoom = min(zoom_x, zoom_y, self.MAX_ZOOM)
        min_zoom = self.WORLD_MIN_ZOOM if self.state.map_mode == MapMode.WORLD else self.MIN_ZOOM
        self.zoom = max(self.zoom, min_zoom)
        
        # Center the view
        self.pan_x = (screen_w - self.state.width * self.zoom) / 2
        self.pan_y = (screen_h - self.state.height * self.zoom) / 2
    
    def _world_to_screen(self, x: float, y: float) -> Tuple[int, int]:
        """Convert world coordinates to screen coordinates"""
        # Flip Y axis (world Y increases up, screen Y increases down)
        screen_x = int(x * self.zoom + self.pan_x)
        screen_y = int((self.state.height - y) * self.zoom + self.pan_y)
        return screen_x, screen_y
    
    def _screen_to_world(self, sx: int, sy: int) -> Tuple[float, float]:
        """Convert screen coordinates to world coordinates"""
        x = (sx - self.pan_x) / self.zoom
        y = self.state.height - (sy - self.pan_y) / self.zoom
        return x, y
    
    def _is_exterior_location(self) -> bool:
        """Check if the current location is an exterior/outdoor space."""
        # Use the shared utility function from llm_layout_generator
        try:
            from llm_layout_generator import is_exterior_location
            if is_exterior_location(self.state.location_name, self.state.location_type):
                return True
        except ImportError:
            pass
        
        # Fallback: Check if any room is marked as exterior
        for room in self.state.rooms.values():
            if room.is_exterior:
                return True
        
        return False
    
    def _handle_click(self, pos: Tuple[int, int]):
        """Handle mouse click - select actors or obstacles"""
        if self.state.map_mode == MapMode.WORLD:
            self._handle_world_click(pos)
            return

        world_x, world_y = self._screen_to_world(pos[0], pos[1])
        
        # Find closest actor within click radius
        click_radius = 15 / self.zoom  # Adjust for zoom
        closest_actor = None
        closest_actor_dist = float('inf')
        
        for actor_id, actor in self.state.actors.items():
            dist = ((actor.x - world_x)**2 + (actor.y - world_y)**2)**0.5
            if dist < click_radius and dist < closest_actor_dist:
                closest_actor_dist = dist
                closest_actor = actor_id
        
        # Find closest obstacle within click radius
        closest_obstacle = None
        closest_obs_dist = float('inf')
        
        for obs_id, obs in self.state.obstacles.items():
            # Check if click is within obstacle bounds
            half_w = obs.width / 2
            half_h = obs.height / 2
            if (obs.x - half_w <= world_x <= obs.x + half_w and
                obs.y - half_h <= world_y <= obs.y + half_h):
                # Click is inside obstacle - calculate distance to center
                dist = ((obs.x - world_x)**2 + (obs.y - world_y)**2)**0.5
                if dist < closest_obs_dist:
                    closest_obs_dist = dist
                    closest_obstacle = obs_id
        
        # Prioritize actors over obstacles if both are clicked
        if closest_actor:
            self.selected_actor = closest_actor
            self.selected_obstacle = None
            for actor in self.state.actors.values():
                actor.is_selected = (actor.actor_id == closest_actor)
        elif closest_obstacle:
            self.selected_actor = None
            self.selected_obstacle = closest_obstacle
            for actor in self.state.actors.values():
                actor.is_selected = False

    def _handle_world_click(self, pos: Tuple[int, int]):
        """Handle click selection on world graph nodes."""
        world_x, world_y = self._screen_to_world(pos[0], pos[1])
        click_radius = 18 / max(self.zoom, 0.1)

        closest = None
        closest_dist = float('inf')
        for k, n in (self.state.world_nodes or {}).items():
            try:
                dx = float(n.get('x', 0.0)) - world_x
                dy = float(n.get('y', 0.0)) - world_y
                dist = (dx * dx + dy * dy) ** 0.5
                if dist < click_radius and dist < closest_dist:
                    closest = k
                    closest_dist = dist
            except Exception:
                continue

        self.state.selected_world_node = closest
    
    def _handle_key(self, key: int):
        """Handle keyboard input"""
        if key == pygame.K_TAB:
            self.state.map_mode = MapMode.WORLD if self.state.map_mode == MapMode.LOCAL else MapMode.LOCAL
            self.selected_actor = None
            self.selected_obstacle = None
            try:
                self._apply_canvas_for_mode(self.state.map_mode)
            except Exception:
                pass
            self._auto_fit_view()
            return

        if self.state.map_mode == MapMode.WORLD:
            if key == pygame.K_ESCAPE:
                self.state.selected_world_node = None
                return

            if key == pygame.K_RETURN or key == pygame.K_KP_ENTER:
                sel = self.state.selected_world_node
                if sel and sel in (self.state.world_nodes or {}):
                    node = self.state.world_nodes.get(sel) or {}
                    if not bool(node.get('is_unknown')):
                        try:
                            self.outbox_queue.put(('travel_request', str(node.get('name') or sel)))
                        except Exception:
                            pass
                return

        if key == pygame.K_v:
            self.state.show_vision_range = not self.state.show_vision_range
        elif key == pygame.K_h:
            self.state.show_hearing_range = not self.state.show_hearing_range
        elif key == pygame.K_s:
            self.state.show_smell_range = not self.state.show_smell_range
        elif key == pygame.K_t:
            self.state.show_touch_range = not self.state.show_touch_range
        elif key == pygame.K_g:
            self.state.show_grid = not self.state.show_grid
        elif key == pygame.K_z:
            self.state.show_zones = not self.state.show_zones
        elif key == pygame.K_r:
            self._auto_fit_view()
        elif key == pygame.K_ESCAPE:
            self.selected_actor = None
            self.selected_obstacle = None
            for actor in self.state.actors.values():
                actor.is_selected = False
    
    def _render(self):
        """Render the dungeon-style map"""
        if self.screen is None:
            return

        if self.state.map_mode == MapMode.WORLD:
            self._render_world()
            return
        
        # Clear screen with parchment background
        self.screen.fill(Colors.BACKGROUND)
        
        # Draw exterior hatching first (outside the building)
        self._draw_exterior_hatching()
        
        # Draw floor areas (interior)
        self._draw_floor()
        
        # Draw grid on floor
        if self.state.show_grid:
            self._draw_grid()
        
        # Draw walls (thick black lines)
        self._draw_walls()
        
        # Draw doors
        self._draw_doors()
        
        # Draw obstacles/furniture (INUA)
        self._draw_obstacles()
        
        # Draw zone numbers
        if self.state.show_zones and self.state.show_zone_numbers:
            self._draw_zone_numbers()
        
        # Draw sensory ranges for UA (subtle)
        self._draw_sensory_ranges()
        
        # Draw actors as tokens
        self._draw_actors()
        
        # Draw UI panels
        self._draw_ui()

        # Draw narrative panel below the map
        self._nar_render()

        # Update display
        pygame.display.flip()

    def _render_world(self):
        """Render the world location graph."""
        if self.screen is None:
            return

        self.screen.fill(Colors.BACKGROUND)

        # Draw edges first
        for e in list(self.state.world_edges or []):
            try:
                a = e.get('a')
                b = e.get('b')
                if not a or not b:
                    continue
                na = (self.state.world_nodes or {}).get(a)
                nb = (self.state.world_nodes or {}).get(b)
                if not na or not nb:
                    continue
                ax, ay = float(na.get('x', 0.0)), float(na.get('y', 0.0))
                bx, by = float(nb.get('x', 0.0)), float(nb.get('y', 0.0))
                a_s = self._world_to_screen(ax, ay)
                b_s = self._world_to_screen(bx, by)
                is_unknown = bool(e.get('is_unknown'))
                color = Colors.WORLD_EDGE_UNKNOWN if is_unknown else Colors.WORLD_EDGE
                pygame.draw.line(self.screen, color, a_s, b_s, max(1, int(2 * self.zoom / 2)))

                # Label minutes near midpoint
                minutes = e.get('minutes')
                if minutes is not None and self.font_small is not None:
                    mx = int((a_s[0] + b_s[0]) / 2)
                    my = int((a_s[1] + b_s[1]) / 2)
                    label = f"{int(minutes)}m" if not is_unknown else f"~{int(minutes)}m"
                    txt = self.font_small.render(label, True, Colors.TEXT)
                    self.screen.blit(txt, (mx + 4, my + 4))
            except Exception:
                continue

        # Draw nodes
        node_radius = max(7, int(9 * self.zoom / 2))
        for k, n in (self.state.world_nodes or {}).items():
            try:
                x, y = float(n.get('x', 0.0)), float(n.get('y', 0.0))
                is_unknown = bool(n.get('is_unknown'))
                is_current = bool(n.get('is_current'))
                is_selected = (k == self.state.selected_world_node)
                pos = self._world_to_screen(x, y)

                if is_selected:
                    fill = Colors.WORLD_NODE_SELECTED
                elif is_current:
                    fill = Colors.WORLD_NODE_CURRENT
                elif is_unknown:
                    fill = Colors.WORLD_NODE_UNKNOWN
                else:
                    fill = Colors.WORLD_NODE
                pygame.draw.circle(self.screen, fill, pos, node_radius)
                pygame.draw.circle(self.screen, Colors.WORLD_NODE_BORDER, pos, node_radius, 2)

                # Name
                if self.font_small is not None:
                    name = str(n.get('name') or k)
                    label = self.font_small.render(name[:24], True, Colors.TEXT)
                    self.screen.blit(label, (pos[0] + node_radius + 4, pos[1] - 8))
            except Exception:
                continue

        # UI panel
        try:
            if self.font is not None:
                header = self.font.render("WORLD MAP (TAB toggles LOCAL/WORLD)", True, Colors.TEXT_HIGHLIGHT)
                self.screen.blit(header, (10, 10))

            sel = self.state.selected_world_node
            if sel and self.font_small is not None:
                node = (self.state.world_nodes or {}).get(sel) or {}
                name = str(node.get('name') or sel)
                is_unknown = bool(node.get('is_unknown'))
                hint = "ENTER to confirm travel" if not is_unknown else "Unknown location (placeholder)"
                line1 = self.font_small.render(f"Selected: {name}", True, Colors.TEXT)
                line2 = self.font_small.render(hint, True, Colors.TEXT)
                self.screen.blit(line1, (10, 36))
                self.screen.blit(line2, (10, 54))
        except Exception:
            pass

        self._nar_render()
        pygame.display.flip()

    def _draw_exterior_hatching(self):
        """Draw hatched pattern for exterior/outside areas"""
        screen_w, screen_h = self.screen.get_size()
        
        # Get map bounds in screen coords
        map_left, map_top = self._world_to_screen(0, self.state.height)
        map_right, map_bottom = self._world_to_screen(self.state.width, 0)
        
        # Draw hatching outside the map bounds
        hatch_color = Colors.EXTERIOR
        hatch_spacing = 8
        
        # Create hatching pattern surface
        for i in range(-screen_h, screen_w + screen_h, hatch_spacing):
            # Diagonal lines going one way
            pygame.draw.line(self.screen, hatch_color, 
                           (i, 0), (i + screen_h, screen_h), 1)
            # Diagonal lines going the other way
            pygame.draw.line(self.screen, hatch_color,
                           (i + screen_h, 0), (i, screen_h), 1)
        
        # Clear the interior (draw floor color over hatching)
        # This will be done in _draw_floor
    
    def _draw_floor(self):
        """Draw interior floor areas"""
        # Draw main floor rectangle
        left, top = self._world_to_screen(0, self.state.height)
        right, bottom = self._world_to_screen(self.state.width, 0)
        
        floor_rect = pygame.Rect(left, top, right - left, bottom - top)
        pygame.draw.rect(self.screen, Colors.FLOOR, floor_rect)
        
        # Draw individual room floors if defined
        for room in self.state.rooms.values():
            if not room.is_exterior:
                rx, ry, rw, rh = room.bounds
                r_left, r_top = self._world_to_screen(rx, ry + rh)
                r_right, r_bottom = self._world_to_screen(rx + rw, ry)
                room_rect = pygame.Rect(r_left, r_top, r_right - r_left, r_bottom - r_top)
                pygame.draw.rect(self.screen, Colors.FLOOR, room_rect)
    
    def _draw_grid(self):
        """Draw subtle grid lines on floor"""
        screen_w, screen_h = self.screen.get_size()
        grid_size = self.state.grid_size
        
        # Get map bounds
        map_left, map_top = self._world_to_screen(0, self.state.height)
        map_right, map_bottom = self._world_to_screen(self.state.width, 0)
        
        # Vertical lines
        x = 0
        while x <= self.state.width:
            sx, _ = self._world_to_screen(x, 0)
            if map_left <= sx <= map_right:
                pygame.draw.line(self.screen, Colors.GRID, 
                               (sx, map_top), (sx, map_bottom), 1)
            x += grid_size
        
        # Horizontal lines
        y = 0
        while y <= self.state.height:
            _, sy = self._world_to_screen(0, y)
            if map_top <= sy <= map_bottom:
                pygame.draw.line(self.screen, Colors.GRID,
                               (map_left, sy), (map_right, sy), 1)
            y += grid_size
    
    def _draw_walls(self):
        """Draw thick black walls"""
        wall_thickness = max(3, int(self.state.wall_thickness * self.zoom / 20))
        
        # Check if this is an exterior location - don't draw full boundary for outdoor spaces
        is_exterior = self._is_exterior_location()
        
        if not is_exterior:
            # Avoid double outlines: if the layout already provided boundary walls,
            # don't also draw a full outer rectangle.
            has_boundary = False
            try:
                w = float(getattr(self.state, 'width', 0.0) or 0.0)
                h = float(getattr(self.state, 'height', 0.0) or 0.0)
                eps = max(0.75, min(w, h) * 0.05)
                for wall in (self.state.walls or {}).values():
                    x0, y0 = float(wall.start[0]), float(wall.start[1])
                    x1, y1 = float(wall.end[0]), float(wall.end[1])
                    if (
                        abs(x0 - 0.0) <= eps or abs(x1 - 0.0) <= eps
                        or abs(x0 - w) <= eps or abs(x1 - w) <= eps
                        or abs(y0 - 0.0) <= eps or abs(y1 - 0.0) <= eps
                        or abs(y0 - h) <= eps or abs(y1 - h) <= eps
                    ):
                        has_boundary = True
                        break
            except Exception:
                has_boundary = False

            if not has_boundary:
                # Draw outer boundary walls only when boundary isn't already defined
                left, top = self._world_to_screen(0, self.state.height)
                right, bottom = self._world_to_screen(self.state.width, 0)
                pygame.draw.rect(self.screen, Colors.WALL, 
                                (left, top, right - left, bottom - top), wall_thickness)
        
        # Draw defined walls
        for wall in self.state.walls.values():
            start_screen = self._world_to_screen(wall.start[0], wall.start[1])
            end_screen = self._world_to_screen(wall.end[0], wall.end[1])
            
            if not wall.has_door:
                pygame.draw.line(self.screen, Colors.WALL,
                               start_screen, end_screen, wall_thickness)
            else:
                # Draw wall with door gap
                self._draw_wall_with_door(start_screen, end_screen, 
                                         wall.door_position, wall_thickness)
        
        # NOTE: Zone walls are now handled by the explicit walls with door gaps
        # Don't draw zone polygons as walls - they would overwrite door gaps
    
    def _draw_wall_with_door(self, start: Tuple[int, int], end: Tuple[int, int],
                             door_pos: float, thickness: int):
        """Draw a wall segment with a door gap"""
        # Calculate door gap
        door_width = 20  # pixels
        
        dx = end[0] - start[0]
        dy = end[1] - start[1]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length < door_width * 2:
            return  # Wall too short for door
        
        # Door center position
        door_center_x = start[0] + dx * door_pos
        door_center_y = start[1] + dy * door_pos
        
        # Normalized direction
        if length > 0:
            nx, ny = dx / length, dy / length
        else:
            return
        
        # Draw wall before door
        door_start_x = door_center_x - nx * door_width / 2
        door_start_y = door_center_y - ny * door_width / 2
        pygame.draw.line(self.screen, Colors.WALL,
                        start, (int(door_start_x), int(door_start_y)), thickness)
        
        # Draw wall after door
        door_end_x = door_center_x + nx * door_width / 2
        door_end_y = door_center_y + ny * door_width / 2
        pygame.draw.line(self.screen, Colors.WALL,
                        (int(door_end_x), int(door_end_y)), end, thickness)
    
    def _draw_doors(self):
        """Draw door indicators - highly visible"""
        door_count = 0
        
        for obs in self.state.obstacles.values():
            # Check for door-like obstacles
            name_lower = obs.name.lower() if obs.name else ""
            type_lower = obs.obstacle_type.lower() if obs.obstacle_type else ""
            is_door = (type_lower == "door" or 
                      "door" in name_lower or 
                      "entrance" in name_lower or 
                      "exit" in name_lower or
                      "gate" in name_lower or
                      "hatch" in name_lower or
                      "trapdoor" in name_lower or
                      "grate" in name_lower or
                      "sewer" in name_lower or
                      "manhole" in name_lower or
                      "ladder" in name_lower)
            
            if is_door:
                door_count += 1
                sx, sy = self._world_to_screen(obs.x, obs.y)
                
                # Draw glow effect behind door
                glow_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, Colors.DOOR_MARKER_GLOW, (30, 30), 25)
                self.screen.blit(glow_surf, (sx - 30, sy - 30))
                
                # Draw door marker - prominent arch shape
                door_w = max(16, int(20 * self.zoom / 50))
                door_h = max(20, int(25 * self.zoom / 50))
                
                # Draw door frame (arch)
                door_rect = pygame.Rect(sx - door_w//2, sy - door_h//2, door_w, door_h)
                pygame.draw.rect(self.screen, Colors.DOOR_MARKER, door_rect, border_radius=door_w//3)
                pygame.draw.rect(self.screen, Colors.WALL, door_rect, 2, border_radius=door_w//3)
                
                # Draw door icon (small lines to indicate door)
                pygame.draw.line(self.screen, Colors.WALL, 
                               (sx - door_w//4, sy - door_h//3), 
                               (sx - door_w//4, sy + door_h//3), 2)
                
                # Label if it's an exit
                if "exit" in name_lower or "entrance" in name_lower:
                    label = self.font_small.render("EXIT", True, Colors.DOOR_MARKER)
                    label_rect = label.get_rect(center=(sx, sy + door_h//2 + 10))
                    self.screen.blit(label, label_rect)
        
        # If no doors found, draw default exit marker at bottom center
        if door_count == 0:
            self._draw_default_exit_marker()
    
    def _draw_default_exit_marker(self):
        """Draw a default exit marker at bottom center when no doors are defined"""
        # Exit is at bottom center of map (where journeys head toward)
        map_w = float(getattr(self.state, 'width', 0.0) or 0.0)
        map_h = float(getattr(self.state, 'height', 0.0) or 0.0)
        if map_w <= 0 or map_h <= 0:
            loc_type = (getattr(self.state, 'location_type', None) or 'interior')
            map_w, map_h = LocationScale.get_scale(loc_type)
        exit_x, exit_y = map_w / 2, map_h * 0.05  # Bottom center
        
        sx, sy = self._world_to_screen(exit_x, exit_y)
        
        # Draw glow
        glow_surf = pygame.Surface((80, 80), pygame.SRCALPHA)
        pygame.draw.circle(glow_surf, Colors.DOOR_MARKER_GLOW, (40, 40), 35)
        self.screen.blit(glow_surf, (sx - 40, sy - 40))
        
        # Draw exit arrow pointing down (out of the room)
        arrow_size = 20
        # Triangle pointing down
        points = [
            (sx, sy + arrow_size),      # Bottom point
            (sx - arrow_size//2, sy - arrow_size//3),  # Top left
            (sx + arrow_size//2, sy - arrow_size//3),  # Top right
        ]
        pygame.draw.polygon(self.screen, Colors.DOOR_MARKER, points)
        pygame.draw.polygon(self.screen, Colors.WALL, points, 2)
        
        # Draw "EXIT" label
        label = self.font_small.render("EXIT", True, Colors.DOOR_MARKER)
        label_rect = label.get_rect(center=(sx, sy - arrow_size))
        self.screen.blit(label, label_rect)
    
    def _draw_zone_numbers(self):
        """Draw numbered circles for zones like in the reference image"""
        zone_number = 1
        
        for zone in self.state.zones.values():
            if len(zone.points) < 3:
                continue
            
            # Calculate center
            center_x = sum(p[0] for p in zone.points) / len(zone.points)
            center_y = sum(p[1] for p in zone.points) / len(zone.points)
            sx, sy = self._world_to_screen(center_x, center_y)
            
            # Use zone's number if set, otherwise auto-increment
            num = zone.number if zone.number > 0 else zone_number
            
            # Draw black circle with white number - smaller size
            radius = 10
            pygame.draw.circle(self.screen, Colors.ZONE_NUMBER_BG, (sx, sy), radius)
            pygame.draw.circle(self.screen, Colors.WALL, (sx, sy), radius, 1)
            
            # Draw number with smaller font
            text = self.font_small.render(str(num), True, Colors.ZONE_NUMBER_TEXT)
            text_rect = text.get_rect(center=(sx, sy))
            self.screen.blit(text, text_rect)
            
            zone_number += 1
    
    def _classify_obstacle(self, name: str, obs_type: str) -> str:
        """Classify obstacle by name keywords for better visualization"""
        name_lower = name.lower()
        
        # Tech/Electronics
        if any(w in name_lower for w in ["computer", "terminal", "console", "monitor", "screen", "display", "server", "node", "reader", "scanner", "printer"]):
            return "tech"
        # Seating
        if any(w in name_lower for w in ["chair", "seat", "stool", "bench", "sofa", "couch"]):
            return "seating"
        # Beds/Sleep
        if any(w in name_lower for w in ["bed", "cot", "bunk", "mattress", "sleep", "cradle", "pod"]):
            return "bed"
        # Desks/Tables
        if any(w in name_lower for w in ["desk", "table", "counter", "workstation", "workspace"]):
            return "desk"
        # Storage/Filing
        if any(w in name_lower for w in ["cabinet", "locker", "shelf", "shelves", "storage", "drawer", "filing", "rack", "container", "crate", "box", "catalog", "archive", "supply", "cart", "trolley"]):
            return "storage"
        # Lighting
        if any(w in name_lower for w in ["lamp", "light", "lantern", "fixture"]):
            return "lighting"
        # Wall-mounted/Decor
        if any(w in name_lower for w in ["clock", "calendar", "poster", "painting", "art", "decoration", "frame"]):
            return "wall_decor"
        # Plants
        if any(w in name_lower for w in ["plant", "potted", "flower", "vase", "fern", "succulent"]):
            return "plant"
        # Appliances/Equipment
        if any(w in name_lower for w in ["fridge", "refrigerator", "microwave", "coffee", "cooler", "heater", "fan", "shredder", "copier", "machine"]):
            return "appliance"
        # HVAC/Infrastructure
        if any(w in name_lower for w in ["vent", "ventilation", "hvac", "air", "filtration", "duct", "pipe", "conduit"]):
            return "infrastructure"
        # Safety Equipment
        if any(w in name_lower for w in ["fire", "extinguisher", "alarm", "emergency", "first aid", "safety"]):
            return "safety"
        # Maintenance
        if any(w in name_lower for w in ["maintenance", "panel", "electrical", "utility", "control"]):
            return "maintenance"
        # Bathroom
        if any(w in name_lower for w in ["toilet", "sink", "shower", "bath", "mirror"]):
            return "bathroom"
        # Doors/Windows
        if any(w in name_lower for w in ["door", "entrance", "exit", "gate"]):
            return "door"
        if any(w in name_lower for w in ["window", "glass"]):
            return "window"
        # Boards/Displays
        if any(w in name_lower for w in ["board", "whiteboard", "bulletin", "sign", "notice", "microfiche"]):
            return "board"
        # Waste
        if any(w in name_lower for w in ["trash", "waste", "garbage", "recycl"]):
            return "waste"
        # Bins (not waste)
        if "bin" in name_lower:
            return "storage"
        
        return obs_type.lower() if obs_type else "object"
    
    def _draw_obstacles(self):
        """Draw obstacles (furniture, objects) with type-specific colors and shapes"""
        if not self.screen:
            return
        
        screen_w, screen_h = self.screen.get_size()
        
        # Calculate visible world bounds for culling
        margin = 30
        world_min_x, world_max_y = self._screen_to_world(-margin, -margin)
        world_max_x, world_min_y = self._screen_to_world(screen_w + margin, screen_h + margin)
        
        # Enhanced color mapping with distinct colors per category
        obstacle_colors = {
            # Tech - Blue tones
            "tech": ((70, 130, 200), (40, 90, 160)),
            "terminal": ((70, 130, 200), (40, 90, 160)),
            # Seating - Orange/Tan
            "seating": ((200, 150, 100), (160, 110, 60)),
            # Beds - Purple
            "bed": ((150, 120, 180), (110, 80, 140)),
            # Desks - Wood brown
            "desk": ((160, 120, 80), (120, 80, 40)),
            "furniture": ((160, 120, 80), (120, 80, 40)),
            # Storage - Green
            "storage": ((100, 160, 100), (60, 120, 60)),
            # Lighting - Yellow
            "lighting": ((240, 220, 120), (200, 180, 80)),
            # Wall decor - Light tan
            "wall_decor": ((210, 200, 180), (170, 160, 140)),
            # Plants - Bright green
            "plant": ((80, 180, 80), (50, 140, 50)),
            # Appliances - Gray metallic
            "appliance": ((160, 170, 180), (120, 130, 140)),
            # Infrastructure - Steel gray
            "infrastructure": ((140, 150, 160), (100, 110, 120)),
            # Safety - Red
            "safety": ((200, 80, 80), (160, 50, 50)),
            # Maintenance - Orange
            "maintenance": ((200, 140, 80), (160, 100, 50)),
            # Bathroom - Light blue
            "bathroom": ((180, 210, 230), (140, 170, 190)),
            # Boards - White
            "board": ((240, 240, 240), (180, 180, 180)),
            # Windows - Cyan
            "window": ((180, 220, 240), (140, 180, 200)),
            # Waste - Dark gray
            "waste": ((80, 80, 80), (50, 50, 50)),
            # Infrastructure - Dark gray
            "vent": ((90, 90, 100), (50, 50, 60)),
            # Generic
            "object": ((170, 150, 130), (130, 110, 90)),
        }
        default_colors = ((170, 150, 130), (130, 110, 90))
        
        for obs in self.state.obstacles.values():
            # Classify by name for better colors
            obs_category = self._classify_obstacle(obs.name, obs.obstacle_type or "object")
            
            if obs_category == "door":
                continue  # Doors handled separately
            
            # Viewport culling
            if not (world_min_x <= obs.x <= world_max_x and world_min_y <= obs.y <= world_max_y):
                continue
            
            sx, sy = self._world_to_screen(obs.x, obs.y)
            
            # Size based on obstacle dimensions
            w = max(10, int(obs.width * self.zoom))
            h = max(8, int(obs.height * self.zoom))
            
            # Get colors
            fill_color, border_color = obstacle_colors.get(obs_category, default_colors)
            
            rect = pygame.Rect(sx - w//2, sy - h//2, w, h)
            
            # Different shapes based on category
            if obs_category == "seating":
                # Chairs - rounded rectangle
                pygame.draw.rect(self.screen, fill_color, rect, border_radius=5)
                pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=5)
            elif obs_category == "bed":
                # Beds - rounded with pillow indicator
                pygame.draw.rect(self.screen, fill_color, rect, border_radius=4)
                pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=4)
                # Pillow
                pillow_rect = pygame.Rect(sx - w//2 + 2, sy - h//2 + 2, w//3, h - 4)
                pygame.draw.rect(self.screen, (220, 220, 230), pillow_rect, border_radius=2)
            elif obs_category == "tech":
                # Tech - rectangle with screen glow
                pygame.draw.rect(self.screen, fill_color, rect, border_radius=2)
                pygame.draw.rect(self.screen, border_color, rect, 2, border_radius=2)
                # Screen glow
                inner = rect.inflate(-6, -6)
                pygame.draw.rect(self.screen, (150, 200, 255), inner)
            elif obs_category == "lighting":
                # Lamps - circle
                radius = min(w, h) // 2
                pygame.draw.circle(self.screen, fill_color, (sx, sy), radius)
                pygame.draw.circle(self.screen, border_color, (sx, sy), radius, 2)
                # Glow effect
                pygame.draw.circle(self.screen, (255, 255, 200), (sx, sy), radius - 3)
            elif obs_category == "waste":
                # Trash bins - small rectangle
                pygame.draw.rect(self.screen, fill_color, rect)
                pygame.draw.rect(self.screen, border_color, rect, 2)
            elif obs_category == "board":
                # Whiteboards - flat rectangle with border
                pygame.draw.rect(self.screen, fill_color, rect)
                pygame.draw.rect(self.screen, (80, 80, 80), rect, 3)
            elif obs_category == "storage":
                # Storage - rectangle with lines (shelves)
                pygame.draw.rect(self.screen, fill_color, rect)
                pygame.draw.rect(self.screen, border_color, rect, 2)
                # Shelf lines
                for i in range(1, 3):
                    y_line = sy - h//2 + (h * i // 3)
                    pygame.draw.line(self.screen, border_color, (sx - w//2 + 2, y_line), (sx + w//2 - 2, y_line), 1)
            elif obs_category == "plant":
                # Plants - green ellipse
                pygame.draw.ellipse(self.screen, fill_color, rect)
                pygame.draw.ellipse(self.screen, border_color, rect, 2)
            elif obs_category == "safety":
                # Safety equipment - red rectangle with cross
                pygame.draw.rect(self.screen, fill_color, rect)
                pygame.draw.rect(self.screen, border_color, rect, 2)
                # Cross symbol
                cx, cy = sx, sy
                pygame.draw.line(self.screen, (255, 255, 255), (cx - 4, cy), (cx + 4, cy), 2)
                pygame.draw.line(self.screen, (255, 255, 255), (cx, cy - 4), (cx, cy + 4), 2)
            elif obs_category == "infrastructure":
                # HVAC/vents - gray with vent lines
                pygame.draw.rect(self.screen, fill_color, rect)
                pygame.draw.rect(self.screen, border_color, rect, 2)
                # Vent lines
                for i in range(1, 4):
                    x_line = sx - w//2 + (w * i // 4)
                    pygame.draw.line(self.screen, border_color, (x_line, sy - h//2 + 2), (x_line, sy + h//2 - 2), 1)
            elif obs_category == "maintenance":
                # Maintenance panels - orange with bolt pattern
                pygame.draw.rect(self.screen, fill_color, rect)
                pygame.draw.rect(self.screen, border_color, rect, 2)
            elif obs_category == "wall_decor":
                # Wall-mounted items - thin rectangle
                pygame.draw.rect(self.screen, fill_color, rect)
                pygame.draw.rect(self.screen, border_color, rect, 2)
            else:
                # Default rectangle
                pygame.draw.rect(self.screen, fill_color, rect)
                pygame.draw.rect(self.screen, border_color, rect, 2)
            
            # Draw selection highlight if this obstacle is selected
            if self.selected_obstacle == obs.obstacle_id:
                # Draw glowing selection border
                select_rect = rect.inflate(6, 6)
                pygame.draw.rect(self.screen, (255, 200, 0), select_rect, 3)  # Gold border
                pygame.draw.rect(self.screen, (255, 255, 100), select_rect, 1)  # Inner glow
            
            # Draw name label
            if self.font_small:
                display_name = obs.name
                if len(display_name) > 15:
                    display_name = display_name[:13] + ".."
                
                text = self.font_small.render(display_name, True, Colors.TEXT)
                text_rect = text.get_rect(center=(sx, sy + h//2 + 10))
                
                # Background for readability
                bg_rect = text_rect.inflate(4, 2)
                pygame.draw.rect(self.screen, (255, 255, 255, 200), bg_rect)
                self.screen.blit(text, text_rect)
    
    def _draw_sensory_ranges(self):
        """Draw sensory range circles for UA"""
        # Find UA
        ua = None
        for actor in self.state.actors.values():
            if actor.actor_type == ActorType.UA:
                ua = actor
                break
        
        if not ua:
            return
        
        sx, sy = self._world_to_screen(ua.x, ua.y)
        
        # Draw ranges as circles (largest first for layering)
        ranges = []
        if self.state.show_vision_range:
            ranges.append((SensoryRange.VISION, Colors.VISION_RANGE, "Vision"))
        if self.state.show_hearing_range:
            ranges.append((SensoryRange.HEARING, Colors.HEARING_RANGE, "Hearing"))
        if self.state.show_smell_range:
            ranges.append((SensoryRange.SMELL, Colors.SMELL_RANGE, "Smell"))
        if self.state.show_touch_range:
            ranges.append((SensoryRange.TOUCH, Colors.TOUCH_RANGE, "Touch"))
        
        # Sort by range (largest first)
        ranges.sort(key=lambda x: x[0], reverse=True)
        
        for range_dist, color, name in ranges:
            radius = int(range_dist * self.zoom)
            if radius > 2:
                # Create surface with alpha for transparency
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, color, (radius, radius), radius)
                self.screen.blit(surf, (sx - radius, sy - radius))
                
                # Draw border
                border_color = (color[0], color[1], color[2])
                pygame.draw.circle(self.screen, border_color, (sx, sy), radius, 1)
    
    def _draw_actors(self):
        """Draw all actors with viewport culling for performance"""
        if not self.screen:
            return
        
        screen_w, screen_h = self.screen.get_size()
        
        # Calculate visible world bounds (with margin for actors near edge)
        margin = 50  # pixels
        world_min_x, world_max_y = self._screen_to_world(-margin, -margin)
        world_max_x, world_min_y = self._screen_to_world(screen_w + margin, screen_h + margin)
        
        # Filter to only visible actors (viewport culling)
        visible_actors = []
        for actor in self.state.actors.values():
            if world_min_x <= actor.x <= world_max_x and world_min_y <= actor.y <= world_max_y:
                visible_actors.append(actor)
        
        # Sort so UA is drawn last (on top)
        sorted_actors = sorted(
            visible_actors,
            key=lambda a: (a.actor_type == ActorType.UA, a.is_selected)
        )
        
        # Draw trails first (behind actors)
        for actor in sorted_actors:
            self._draw_actor_trail(actor)
        
        # Then draw actors on top
        for actor in sorted_actors:
            self._draw_actor(actor)
    
    def _draw_actor_trail(self, actor: MapActor):
        """Draw movement trail for an actor"""
        if not actor.trail or len(actor.trail) < 1:
            return
        
        # Choose trail color based on actor type
        if actor.actor_type == ActorType.UA:
            trail_color = Colors.TRAIL_UA
        else:
            trail_color = Colors.TRAIL_NUA
        
        # Create semi-transparent surface for trail
        trail_surf = pygame.Surface(self.screen.get_size(), pygame.SRCALPHA)
        
        # Build path: trail points + current position
        path_points = [(p[0], p[1]) for p in actor.trail]
        path_points.append((actor.x, actor.y))
        
        # Convert to screen coordinates
        screen_points = [self._world_to_screen(p[0], p[1]) for p in path_points]
        
        # Draw trail line with fading opacity - more visible now
        if len(screen_points) >= 2:
            for i in range(len(screen_points) - 1):
                # Fade from old (more transparent) to new (fully opaque)
                # Start at 120 alpha, end at 255 (fully visible)
                alpha = int(120 + (135 * i / max(1, len(screen_points) - 1)))
                color = (trail_color[0], trail_color[1], trail_color[2], alpha)
                
                # Line thickness increases toward current position (thicker lines)
                thickness = max(3, int(3 + i * 0.7))
                
                pygame.draw.line(trail_surf, color, 
                               screen_points[i], screen_points[i + 1], thickness)
        
        # Draw waypoint dots - more visible
        for i, sp in enumerate(screen_points[:-1]):  # Exclude current position
            alpha = int(150 + (105 * i / max(1, len(screen_points))))
            dot_color = (Colors.TRAIL_DOT[0], Colors.TRAIL_DOT[1], Colors.TRAIL_DOT[2], alpha)
            pygame.draw.circle(trail_surf, dot_color, sp, 4)  # Larger dots
        
        self.screen.blit(trail_surf, (0, 0))
    
    def _draw_actor(self, actor: MapActor):
        """Draw a single actor as a token"""
        # Clip actor position to room boundaries with small margin
        margin = 0.3  # 30cm margin from walls
        max_x = max(margin, float(getattr(self.state, 'width', 10.0) or 10.0) - margin)
        max_y = max(margin, float(getattr(self.state, 'height', 10.0) or 10.0) - margin)
        clipped_x = max(margin, min(max_x, float(actor.x)))
        clipped_y = max(margin, min(max_y, float(actor.y)))
        
        sx, sy = self._world_to_screen(clipped_x, clipped_y)
        
        # Determine color, border color, and base size based on type
        if actor.actor_type == ActorType.UA:
            fill_color = Colors.UA
            border_color = Colors.UA_BORDER
            base_m = 0.70
        elif actor.actor_type == ActorType.MNUA:
            fill_color = Colors.MNUA
            border_color = Colors.MNUA_BORDER
            base_m = 0.62
        elif actor.actor_type == ActorType.NUA:
            fill_color = Colors.NUA
            border_color = Colors.NUA_BORDER
            base_m = 0.55
        else:  # INUA
            fill_color = Colors.INUA
            border_color = Colors.INUA_BORDER
            base_m = 0.45
        
        # Scale radius using pixels-per-meter (zoom). Clamp so small maps don't get huge tokens.
        # zoom ~ pixels per world unit (meter)
        try:
            min_dim = max(1.0, min(float(getattr(self.state, 'width', 0.0) or 0.0), float(getattr(self.state, 'height', 0.0) or 0.0)))
        except Exception:
            min_dim = 25.0
        max_px = max(10, int(22 - min(12.0, min_dim * 0.25)))
        radius = max(4, min(max_px, int(base_m * max(6.0, float(self.zoom)))))
        
        # Draw selection glow
        if actor.is_selected:
            glow_radius = radius + 6
            glow_surf = pygame.Surface((glow_radius * 2 + 4, glow_radius * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, Colors.SELECTED_GLOW, 
                             (glow_radius + 2, glow_radius + 2), glow_radius)
            self.screen.blit(glow_surf, (sx - glow_radius - 2, sy - glow_radius - 2))
            pygame.draw.circle(self.screen, Colors.SELECTED, (sx, sy), radius + 3, 2)
        
        # Draw token - filled circle with scaled border thickness
        border_thickness = max(2, min(4, int(max(1, radius) * 0.22)))
        pygame.draw.circle(self.screen, fill_color, (sx, sy), radius)
        pygame.draw.circle(self.screen, border_color, (sx, sy), radius, border_thickness)
        
        # Draw facing direction indicator (small triangle pointing in facing direction)
        if actor.facing_direction != 0 or actor.trail:
            angle_rad = math.radians(90 - actor.facing_direction)  # Convert to screen coords
            indicator_dist = radius + 4
            tip_x = sx + int(indicator_dist * math.cos(angle_rad))
            tip_y = sy - int(indicator_dist * math.sin(angle_rad))
            
            # Draw small direction indicator
            pygame.draw.circle(self.screen, border_color, (tip_x, tip_y), 3)
        
        # Draw initial letter inside token for all actors (when token is large enough)
        inner_font = self.font if (actor.actor_type == ActorType.UA) else self.font_small
        if inner_font and radius >= 7:
            initial = actor.name[0].upper() if actor.name else "?"
            text = inner_font.render(initial, True, (255, 255, 255))
            text_rect = text.get_rect(center=(sx, sy))
            self.screen.blit(text, text_rect)
        
        # Draw name label below token
        if self.font_small:
            name_text = actor.name
            if len(name_text) > 12:
                name_text = name_text[:10] + ".."
            
            text = self.font_small.render(name_text, True, Colors.TEXT)
            text_rect = text.get_rect(center=(sx, sy + radius + max(8, int(10 * min(self.zoom / 20, 1.0)))))
            
            # Background for readability
            bg_rect = text_rect.inflate(6, 2)
            pygame.draw.rect(self.screen, Colors.FLOOR, bg_rect)
            pygame.draw.rect(self.screen, Colors.GRID, bg_rect, 1)
            self.screen.blit(text, text_rect)
        
        # Draw S-trait outliers if any and zoomed in
        if actor.s_trait_outliers and self.zoom > 20 and self.font_small:
            outlier_text = ", ".join(actor.s_trait_outliers[:2])
            text = self.font_small.render(outlier_text, True, Colors.MNUA_BORDER)
            text_rect = text.get_rect(center=(sx, sy + radius + 26))
            self.screen.blit(text, text_rect)
        
        # Draw trail info when selected
        if actor.is_selected and self.font_small:
            info_y = sy + radius + 40
            
            # Trail distance
            if actor.trail_distance > 0:
                dist_text = f"Trail: {actor.trail_distance:.1f}m"
                text = self.font_small.render(dist_text, True, Colors.TEXT)
                text_rect = text.get_rect(center=(sx, info_y))
                bg_rect = text_rect.inflate(6, 2)
                pygame.draw.rect(self.screen, Colors.FLOOR, bg_rect)
                self.screen.blit(text, text_rect)
                info_y += 14
            
            # Speed
            if actor.average_speed > 0:
                speed_text = f"Speed: {actor.average_speed:.1f}m/s"
                text = self.font_small.render(speed_text, True, Colors.TEXT)
                text_rect = text.get_rect(center=(sx, info_y))
                bg_rect = text_rect.inflate(6, 2)
                pygame.draw.rect(self.screen, Colors.FLOOR, bg_rect)
                self.screen.blit(text, text_rect)
    
    def _draw_ui(self):
        """Draw UI panels"""
        screen_w, screen_h = self.screen.get_size()
        
        # Location info (top-left)
        loc_text = f"{self.state.location_name} ({self.state.width:.0f}x{self.state.height:.0f})"
        text = self.font.render(loc_text, True, Colors.TEXT_HIGHLIGHT)
        self.screen.blit(text, (10, 10))
        
        # Actor count
        ua_count = sum(1 for a in self.state.actors.values() if a.actor_type == ActorType.UA)
        nua_count = sum(1 for a in self.state.actors.values() if a.actor_type == ActorType.NUA)
        mnua_count = sum(1 for a in self.state.actors.values() if a.actor_type == ActorType.MNUA)
        
        count_text = f"UA: {ua_count} | NUA: {nua_count} | MNUA: {mnua_count}"
        text = self.font_small.render(count_text, True, Colors.TEXT)
        self.screen.blit(text, (10, 35))
        
        # Controls help (bottom-left)
        controls = [
            "V: Vision | H: Hearing | S: Smell | T: Touch",
            "G: Grid | Z: Zones | R: Reset View",
            "Scroll: Zoom | Middle-drag: Pan | Right-click: Reset"
        ]
        map_area_h = screen_h - _NAR_H - _NAR_DIV
        y = map_area_h - 60
        for line in controls:
            text = self.font_small.render(line, True, Colors.TEXT)
            self.screen.blit(text, (10, y))
            y += 18
        
        # Selected actor info (right panel)
        if self.selected_actor and self.selected_actor in self.state.actors:
            self._draw_actor_panel(self.state.actors[self.selected_actor])
        # Selected obstacle info (right panel)
        elif self.selected_obstacle and self.selected_obstacle in self.state.obstacles:
            self._draw_obstacle_panel(self.state.obstacles[self.selected_obstacle])
    
    def _draw_actor_panel(self, actor: MapActor):
        """Draw info panel for selected actor"""
        screen_w, screen_h = self.screen.get_size()
        
        panel_w = 200
        panel_h = 150
        panel_x = screen_w - panel_w - 10
        panel_y = 10
        
        # Panel background
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(Colors.PANEL_BG)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, Colors.TEXT, (panel_x, panel_y, panel_w, panel_h), 1)
        
        # Actor info
        y = panel_y + 10
        
        # Name
        text = self.font.render(actor.name, True, Colors.TEXT_HIGHLIGHT)
        self.screen.blit(text, (panel_x + 10, y))
        y += 25
        
        # Type
        type_colors = {
            ActorType.UA: Colors.UA,
            ActorType.NUA: Colors.NUA,
            ActorType.MNUA: Colors.MNUA,
            ActorType.INUA: Colors.INUA
        }
        type_text = f"Type: {actor.actor_type.value.upper()}"
        text = self.font_small.render(type_text, True, type_colors.get(actor.actor_type, Colors.TEXT))
        self.screen.blit(text, (panel_x + 10, y))
        y += 20
        
        # Position
        pos_text = f"Position: ({actor.x:.1f}, {actor.y:.1f})"
        text = self.font_small.render(pos_text, True, Colors.TEXT)
        self.screen.blit(text, (panel_x + 10, y))
        y += 20
        
        # Occupation
        if actor.occupation:
            occ_text = f"Role: {actor.occupation}"
            text = self.font_small.render(occ_text, True, Colors.TEXT)
            self.screen.blit(text, (panel_x + 10, y))
            y += 20
        
        # S-trait outliers
        if actor.s_trait_outliers:
            traits_text = f"Traits: {', '.join(actor.s_trait_outliers)}"
            text = self.font_small.render(traits_text, True, Colors.MNUA)
            self.screen.blit(text, (panel_x + 10, y))
    
    def _draw_obstacle_panel(self, obstacle: MapObstacle):
        """Draw info panel for selected obstacle"""
        screen_w, screen_h = self.screen.get_size()
        
        panel_w = 220
        panel_h = 180
        panel_x = screen_w - panel_w - 10
        panel_y = 10
        
        # Panel background
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill(Colors.PANEL_BG)
        self.screen.blit(panel_surf, (panel_x, panel_y))
        pygame.draw.rect(self.screen, Colors.TEXT, (panel_x, panel_y, panel_w, panel_h), 1)
        
        # Obstacle info
        y = panel_y + 10
        
        # Name (with word wrap for long names)
        name = obstacle.name
        if len(name) > 22:
            # Split into two lines
            words = name.split()
            line1 = ""
            line2 = ""
            for word in words:
                if len(line1) + len(word) < 22:
                    line1 += word + " "
                else:
                    line2 += word + " "
            text = self.font.render(line1.strip(), True, Colors.TEXT_HIGHLIGHT)
            self.screen.blit(text, (panel_x + 10, y))
            y += 22
            if line2:
                text = self.font.render(line2.strip(), True, Colors.TEXT_HIGHLIGHT)
                self.screen.blit(text, (panel_x + 10, y))
                y += 22
        else:
            text = self.font.render(name, True, Colors.TEXT_HIGHLIGHT)
            self.screen.blit(text, (panel_x + 10, y))
            y += 25
        
        # Category (classified type)
        category = self._classify_obstacle(obstacle.name, obstacle.obstacle_type or "object")
        category_display = category.replace("_", " ").title()
        cat_text = f"Category: {category_display}"
        text = self.font_small.render(cat_text, True, Colors.TEXT)
        self.screen.blit(text, (panel_x + 10, y))
        y += 20
        
        # Type
        type_text = f"Type: {obstacle.obstacle_type or 'Unknown'}"
        text = self.font_small.render(type_text, True, Colors.TEXT)
        self.screen.blit(text, (panel_x + 10, y))
        y += 20
        
        # Position
        pos_text = f"Position: ({obstacle.x:.1f}, {obstacle.y:.1f})"
        text = self.font_small.render(pos_text, True, Colors.TEXT)
        self.screen.blit(text, (panel_x + 10, y))
        y += 20
        
        # Size
        size_text = f"Size: {obstacle.width:.1f} x {obstacle.height:.1f}"
        text = self.font_small.render(size_text, True, Colors.TEXT)
        self.screen.blit(text, (panel_x + 10, y))
        y += 20
        
        # Properties
        props = []
        if obstacle.blocks_los:
            props.append("Blocks LOS")
        if props:
            props_text = f"Properties: {', '.join(props)}"
            text = self.font_small.render(props_text, True, (150, 100, 100))
            self.screen.blit(text, (panel_x + 10, y))


# ═══════════════════════════════════════════════════════════════════════════════
# GLOBAL INSTANCE & INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

def _build_world_graph_layout(tracker) -> Tuple[Dict[str, Dict[str, Any]], List[Dict[str, Any]], str]:
    """Build a force-directed layout for the world graph plus unknown placeholders."""
    try:
        current_key = getattr(tracker, 'current_location', None) or ''
        current_key = str(current_key)
    except Exception:
        current_key = ''

    # Determine a usable current node key
    if not current_key and getattr(tracker, 'locations', None):
        try:
            current_key = next(iter(tracker.locations.keys()))
        except Exception:
            current_key = ''

    center_x, center_y = 500.0, 500.0
    nodes: Dict[str, Dict[str, Any]] = {}

    # Collect known nodes
    try:
        for k, loc in (getattr(tracker, 'locations', {}) or {}).items():
            nodes[str(k)] = {
                'key': str(k),
                'name': getattr(loc, 'name', str(k)),
                'is_unknown': False,
                'is_current': (str(k) == str(current_key)),
                'x': center_x,
                'y': center_y,
            }
    except Exception:
        nodes = {}

    # Adjacency from known edges
    adjacency: Dict[str, List[Tuple[str, float]]] = {}
    for k in list(nodes.keys()):
        adjacency[k] = []

    edges_out: List[Dict[str, Any]] = []
    try:
        for edge_key, edge in (getattr(tracker, 'edges', {}) or {}).items():
            parts = str(edge_key).split('|')
            if len(parts) != 2:
                continue
            a, b = parts[0], parts[1]
            minutes = getattr(edge, 'travel_time_walking', None)
            try:
                minutes = float(minutes) if minutes is not None else None
            except Exception:
                minutes = None

            if a in adjacency:
                adjacency[a].append((b, minutes or 0.0))
            if b in adjacency:
                adjacency[b].append((a, minutes or 0.0))

            edges_out.append({'a': a, 'b': b, 'is_unknown': False, 'minutes': minutes})
    except Exception:
        pass

    # Determine a usable current node key
    keys = list(nodes.keys())
    if current_key not in nodes and keys:
        current_key = keys[0]
        nodes[current_key]['is_current'] = True

    # Force-directed layout for known nodes (deterministic)
    known_keys = [k for k in nodes.keys() if not bool(nodes[k].get('is_unknown'))]
    if len(known_keys) == 1:
        only = known_keys[0]
        nodes[only]['x'] = center_x
        nodes[only]['y'] = center_y
    elif len(known_keys) > 1:
        # Deterministic seed per graph
        seed_str = "|".join(sorted(known_keys))
        rng = random.Random(abs(hash(seed_str)) % (2**32))

        # Initial positions in a box around center
        pos: Dict[str, List[float]] = {}
        for k in known_keys:
            if k == current_key:
                pos[k] = [center_x, center_y]
            else:
                pos[k] = [center_x + rng.uniform(-180.0, 180.0), center_y + rng.uniform(-180.0, 180.0)]

        width, height = 800.0, 800.0
        area = width * height
        k_spring = math.sqrt(area / max(1, len(known_keys)))
        iterations = 60
        temperature = 80.0

        # Build undirected edge set for layout
        edge_pairs: Set[Tuple[str, str]] = set()
        for e in edges_out:
            a = str(e.get('a'))
            b = str(e.get('b'))
            if a in pos and b in pos and a != b:
                edge_pairs.add((a, b) if a < b else (b, a))

        for _ in range(iterations):
            disp: Dict[str, List[float]] = {k: [0.0, 0.0] for k in known_keys}

            # Repulsion
            for i in range(len(known_keys)):
                v = known_keys[i]
                for j in range(i + 1, len(known_keys)):
                    u = known_keys[j]
                    dx = pos[v][0] - pos[u][0]
                    dy = pos[v][1] - pos[u][1]
                    dist = math.hypot(dx, dy) or 0.001
                    force = (k_spring * k_spring) / dist
                    rx = (dx / dist) * force
                    ry = (dy / dist) * force
                    disp[v][0] += rx
                    disp[v][1] += ry
                    disp[u][0] -= rx
                    disp[u][1] -= ry

            # Attraction
            for a, b in edge_pairs:
                dx = pos[a][0] - pos[b][0]
                dy = pos[a][1] - pos[b][1]
                dist = math.hypot(dx, dy) or 0.001
                force = (dist * dist) / k_spring
                ax = (dx / dist) * force
                ay = (dy / dist) * force
                disp[a][0] -= ax
                disp[a][1] -= ay
                disp[b][0] += ax
                disp[b][1] += ay

            # Update positions (keep current pinned to center)
            for v in known_keys:
                if v == current_key:
                    pos[v][0] = center_x
                    pos[v][1] = center_y
                    continue
                dx, dy = disp[v]
                dist = math.hypot(dx, dy) or 0.001
                step = min(dist, temperature)
                pos[v][0] += (dx / dist) * step
                pos[v][1] += (dy / dist) * step

            temperature *= 0.95

        # Normalize into the canvas with margins
        xs = [pos[k][0] for k in known_keys]
        ys = [pos[k][1] for k in known_keys]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        span_x = max(1.0, max_x - min_x)
        span_y = max(1.0, max_y - min_y)
        margin = 110.0
        target_min_x, target_max_x = margin, 1000.0 - margin
        target_min_y, target_max_y = margin, 1000.0 - margin
        scale = min((target_max_x - target_min_x) / span_x, (target_max_y - target_min_y) / span_y)

        for k in known_keys:
            nx = (pos[k][0] - min_x) * scale + target_min_x
            ny = (pos[k][1] - min_y) * scale + target_min_y
            nodes[k]['x'] = float(nx)
            nodes[k]['y'] = float(ny)

        # Ensure current stays visually centered-ish even after normalization
        if current_key in nodes:
            nodes[current_key]['x'] = center_x
            nodes[current_key]['y'] = center_y

    # Unknown placeholders: ensure at least 8 nodes for navigation scaffolding
    try:
        target_count = 8
        missing = max(0, target_count - len(nodes))
        for i in range(missing):
            uk = f"unknown_{i+1}"
            # Spread unknowns around the perimeter to avoid a cross/line artifact
            ang = (2 * math.pi) * ((i + 0.3) / max(1, missing))
            px = center_x + math.cos(ang) * 430.0
            py = center_y + math.sin(ang) * 430.0
            nodes[uk] = {
                'key': uk,
                'name': f"Unknown {i+1}",
                'is_unknown': True,
                'is_current': False,
                'x': px,
                'y': py,
            }
            edges_out.append({'a': str(current_key), 'b': uk, 'is_unknown': True, 'minutes': 10})
    except Exception:
        pass

    return nodes, edges_out, str(current_key)


def sync_world_graph(storage_dir: Optional[str] = None):
    """Sync the pygame map with the current world graph (safe no-op if map isn't running)."""
    map_inst = get_pygame_map()
    if map_inst and map_inst.running:
        map_inst.sync_world_graph(session_id=storage_dir)
    return None


_map_instance: Optional[PygameSpatialMap] = None


def get_pygame_map() -> Optional[PygameSpatialMap]:
    """Get or create the global pygame map instance"""
    global _map_instance, PYGAME_AVAILABLE
    
    # Try runtime import if needed
    if not PYGAME_AVAILABLE:
        try:
            import pygame
            PYGAME_AVAILABLE = True
        except ImportError:
            return None
    
    if _map_instance is None:
        _map_instance = PygameSpatialMap()
    return _map_instance


def start_pygame_map(suppress_own_window: bool = False) -> bool:
    """Start the pygame map window.

    Args:
        suppress_own_window: When True, pmap runs headless (no SDL window) and
            its state can be streamed to the narrative display instead.
    """
    global PYGAME_AVAILABLE

    # Try to import pygame at runtime if not available
    if not PYGAME_AVAILABLE:
        try:
            import pygame
            import pygame.gfxdraw
            PYGAME_AVAILABLE = True
            print("[PMAP] Pygame loaded at runtime")
        except ImportError as e:
            print(f"[PMAP] Pygame not available: {e}")
            print("[PMAP] Install with: pip install pygame")
            return False

    map_inst = get_pygame_map()
    if not map_inst:
        print("[PMAP] Could not create map instance")
        return False

    if suppress_own_window:
        map_inst.suppress_own_window = True

    result = map_inst.start()
    if not result:
        print("[PMAP] map_inst.start() returned False")
    return result


def stop_pygame_map():
    """Stop the pygame map window"""
    global _map_instance
    if _map_instance:
        _map_instance.stop()
        _map_instance = None


def update_map_location(name: str, width: float, height: float, loc_type: str = "interior"):
    """Update the map with a new location"""
    map_inst = get_pygame_map()
    if map_inst and map_inst.running:
        map_inst.update_location(name, width, height, loc_type)


def update_map_actor(actor_id: str, name: str, x: float, y: float, 
                     actor_type: str = "nua", s_trait_outliers: List[str] = None,
                     occupation: str = ""):
    """Update an actor on the map"""
    map_inst = get_pygame_map()
    if map_inst and map_inst.running:
        # Convert string type to enum
        type_map = {
            "ua": ActorType.UA,
            "nua": ActorType.NUA,
            "mnua": ActorType.MNUA,
            "inua": ActorType.INUA
        }
        actor_type_enum = type_map.get(actor_type.lower(), ActorType.NUA)
        
        actor = MapActor(
            actor_id=actor_id,
            name=name,
            actor_type=actor_type_enum,
            x=x,
            y=y,
            s_trait_outliers=s_trait_outliers or [],
            occupation=occupation
        )
        map_inst.update_actor(actor)


def remove_map_actor(actor_id: str):
    """Remove an actor from the map"""
    map_inst = get_pygame_map()
    if map_inst and map_inst.running:
        map_inst.remove_actor(actor_id)


# Cache for generated layouts - persists across syncs
_layout_cache: Dict[str, Any] = {}  # location_name -> (layout, scale_x, scale_y, width, height)


def _layout_cache_disabled() -> bool:
    v = (os.environ.get('PMAP_DISABLE_LAYOUT_CACHE') or os.environ.get('PMAP_DISABLE_SNAPSHOTS') or '').strip().lower()
    return v in ('1', 'true', 'yes', 'on')


def _layout_cache_path(session_id: Optional[str]) -> Path:
    sid = (session_id or 'default').strip() or 'default'
    p = Path(f"sessions/{sid}/pmap_layout_cache.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _layout_to_dict(layout: Any) -> Optional[dict]:
    try:
        if layout is None:
            return None
        # GeneratedLayout is a dataclass (llm_layout_generator.py)
        from dataclasses import asdict
        return asdict(layout)
    except Exception:
        return None


def _layout_from_dict(d: dict) -> Optional[Any]:
    try:
        if not isinstance(d, dict):
            return None
        # Rehydrate to GeneratedLayout objects expected by apply_generated_layout()
        from llm_layout_generator import GeneratedLayout, GeneratedRoom, GeneratedWall, GeneratedObstacle
        rooms: Dict[str, GeneratedRoom] = {}
        for rid, r in (d.get('rooms') or {}).items():
            if isinstance(r, dict):
                rooms[rid] = GeneratedRoom(
                    room_id=str(r.get('room_id') or rid),
                    name=str(r.get('name') or rid),
                    x=float(r.get('x', 0.0)),
                    y=float(r.get('y', 0.0)),
                    width=float(r.get('width', 0.0)),
                    height=float(r.get('height', 0.0)),
                    connections=list(r.get('connections') or []),
                    door_positions=[tuple(p) for p in (r.get('door_positions') or []) if isinstance(p, (list, tuple)) and len(p) == 2],
                )
        walls: List[GeneratedWall] = []
        for w in (d.get('walls') or []):
            if not isinstance(w, dict):
                continue
            walls.append(
                GeneratedWall(
                    wall_id=str(w.get('wall_id') or ''),
                    start=tuple(w.get('start') or (0.0, 0.0)),
                    end=tuple(w.get('end') or (0.0, 0.0)),
                    room_a=str(w.get('room_a') or ''),
                    room_b=(str(w.get('room_b')) if w.get('room_b') is not None else None),
                    has_door=bool(w.get('has_door', False)),
                    door_position=float(w.get('door_position', 0.5)),
                )
            )
        obstacles: List[GeneratedObstacle] = []
        for o in (d.get('obstacles') or []):
            if not isinstance(o, dict):
                continue
            obstacles.append(
                GeneratedObstacle(
                    obstacle_id=str(o.get('obstacle_id') or ''),
                    name=str(o.get('name') or ''),
                    x=float(o.get('x', 0.0)),
                    y=float(o.get('y', 0.0)),
                    width=float(o.get('width', 0.0)),
                    height=float(o.get('height', 0.0)),
                    obstacle_type=str(o.get('obstacle_type') or 'furniture'),
                )
            )
        w = float(d.get('width', 0.0) or 0.0)
        h = float(d.get('height', 0.0) or 0.0)
        if w <= 0 or h <= 0:
            w, h = LocationScale.get_scale('interior')
        return GeneratedLayout(
            width=float(w),
            height=float(h),
            rooms=rooms,
            walls=walls,
            obstacles=obstacles,
        )
    except Exception:
        return None


def _load_layout_cache_from_disk(session_id: Optional[str]) -> None:
    global _layout_cache
    try:
        if _layout_cache_disabled():
            return
        p = _layout_cache_path(session_id)
        if not p.exists():
            return
        raw = json.loads(p.read_text(encoding='utf-8') or '{}')
        layouts = raw.get('layouts') if isinstance(raw, dict) else None
        if not isinstance(layouts, dict):
            return
        loaded: Dict[str, Any] = {}
        for loc, payload in layouts.items():
            if not isinstance(payload, dict):
                continue
            lay = _layout_from_dict(payload.get('layout') or {})
            if lay is None:
                continue
            sx = float(payload.get('scale_x', 1.0))
            sy = float(payload.get('scale_y', 1.0))
            cw = float(payload.get('width', 0.0) or 0.0)
            ch = float(payload.get('height', 0.0) or 0.0)
            loaded[str(loc)] = (lay, sx, sy, cw, ch)
        if loaded:
            _layout_cache.update(loaded)
            print(f"[PMAP] 📥 Loaded persisted layout cache ({len(loaded)} locations) from {p}")
    except Exception:
        return


def _save_layout_cache_to_disk(session_id: Optional[str]) -> None:
    try:
        if _layout_cache_disabled():
            return
        p = _layout_cache_path(session_id)
        out: dict[str, Any] = {
            'version': 2,
            'saved_at': time.time(),
            'layouts': {},
        }
        for loc, tup in (_layout_cache or {}).items():
            try:
                layout, sx, sy, cw, ch = tup
            except Exception:
                continue
            ld = _layout_to_dict(layout)
            if not ld:
                continue
            out['layouts'][str(loc)] = {
                'layout': ld,
                'scale_x': float(sx),
                'scale_y': float(sy),
                'width': float(cw),
                'height': float(ch),
            }
        p.write_text(json.dumps(out, indent=2), encoding='utf-8')
    except Exception:
        return


def _determine_zone_count(location_name: str, dims, suggested_count: int) -> int:
    """
    Intelligently determine how many zones/rooms a location should have.
    
    Small personal spaces = 1 zone
    Medium spaces = 2 zones  
    Large complexes = 3+ zones
    """
    name_lower = location_name.lower()
    
    # Single room indicators - always 1 zone
    single_room_keywords = [
        "room", "pod", "cell", "booth", "cubicle", "closet", "bathroom",
        "office", "safe-house", "safehouse", "safe-cube", "safecube", "cube",
        "hideout", "bunk", "quarters", "chamber", "cabin", "tent", "shack", 
        "shed", "alcove", "nook", "dormitory", "dorm", "bedroom", "kitchen", 
        "lounge", "den", "vault", "capsule", "compartment", "berth", "bay",
        "level", "sub-level", "sublevel", "corridor", "hallway", "passage",
        "maintenance", "storage", "closet", "pantry", "restroom", "lavatory"
    ]
    
    if any(kw in name_lower for kw in single_room_keywords):
        print(f"[PMAP] Zone count: 1 (matched single-room keyword in '{location_name}')")
        return 1

    # Small building indicators - 1-2 zones
    small_building_keywords = [
        "apartment", "flat", "shop", "store", "cafe", "bar", "diner",
        "clinic", "pharmacy", "studio", "garage", "workshop"
    ]
    
    if any(kw in name_lower for kw in small_building_keywords):
        count = min(2, suggested_count)
        print(f"[PMAP] Zone count: {count} (small building)")
        return count
    
    # Large building indicators - 3+ zones
    large_building_keywords = [
        "warehouse", "station", "complex", "facility", "hospital",
        "mall", "market", "factory", "plant", "terminal", "hub",
        "headquarters", "compound", "base", "bunker", "hangar"
    ]
    
    if any(kw in name_lower for kw in large_building_keywords):
        count = max(3, min(suggested_count, 6))
        print(f"[PMAP] Zone count: {count} (large building)")
        return count
    
    # Check location size from dims
    area = dims.width * dims.height
    if area <= 100:  # Small (10x10 or less)
        print(f"[PMAP] Zone count: 1 (small area {area})")
        return 1
    elif area <= 400:  # Medium (20x20 or less)
        count = min(2, suggested_count)
        print(f"[PMAP] Zone count: {count} (medium area {area})")
        return count
    else:  # Large
        count = min(suggested_count, 4)
        print(f"[PMAP] Zone count: {count} (large area {area})")
        return count


def _clamp_1d(value: float, lo: float, hi: float) -> float:
    if hi < lo:
        return lo
    return max(lo, min(hi, value))


def _score_obstacle_for_occupation(occupation: str, obstacle_name: str, obstacle_type: str) -> int:
    occ = (occupation or "").lower()
    name_l = (obstacle_name or "").lower()
    typ_l = (obstacle_type or "").lower()

    if not occ:
        return 0

    rules = [
        ({"waitress", "server", "barkeep", "bartender", "innkeeper"}, {"counter", "bar", "table", "kitchen", "stall"}),
        ({"cook", "chef", "baker"}, {"kitchen", "oven", "hearth", "stove", "counter", "table"}),
        ({"guard", "watchman", "soldier", "cop", "police", "constable"}, {"door", "gate", "entrance", "exit", "wall", "barricade"}),
        ({"blacksmith", "smith"}, {"anvil", "forge", "workbench", "hammer", "furnace"}),
        ({"merchant", "trader", "shopkeeper", "vendor"}, {"counter", "stall", "shelf", "cabinet", "crate", "table"}),
        ({"scribe", "accountant", "clerk"}, {"desk", "table", "counter", "shelf", "cabinet"}),
        ({"alchemist", "physician", "healer", "apothecary"}, {"table", "bench", "cabinet", "shelf", "workbench", "chest"}),
    ]

    score = 0
    for occ_keys, obs_keys in rules:
        if any(k in occ for k in occ_keys):
            for ok in obs_keys:
                if ok in name_l:
                    score = max(score, 100)
            if typ_l and any(k in typ_l for k in ["door", "furniture", "storage", "structure"]):
                score = max(score, 30)

    if score == 0:
        tokens = [t for t in occ.replace("-", " ").replace("_", " ").split() if len(t) >= 4]
        for t in tokens:
            if t in name_l:
                score = max(score, 60)

    return score


def _llm_pick_obstacle_for_npc(occupation: str, obstacle_names: List[str], scene_description: str, location_name: str) -> str:
    try:
        from openrouter_config import create_role_client, OpenRouterConfig
        client = create_role_client("coordination")
        model = OpenRouterConfig.get_model_for_role("coordination")

        obs_list = "\n".join(f"- {n}" for n in obstacle_names[:40])
        prompt = f"""Pick the single best obstacle for an NPC to stand near.

NPC OCCUPATION:
{occupation}

LOCATION:
{location_name}

SCENE (optional context):
{scene_description[:800]}

OBSTACLES:
{obs_list}

Return JSON only:
{{"best_obstacle": "<exact obstacle name from the list>"}}
"""

        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
            max_tokens=80,
        )
        txt = (resp.choices[0].message.content or "").strip()
        import json
        if "```" in txt:
            start = txt.find("{")
            end = txt.rfind("}")
            if start != -1 and end != -1 and end > start:
                txt = txt[start:end+1]
        data = json.loads(txt)
        chosen = (data.get("best_obstacle") or "").strip()
        return chosen
    except Exception:
        return ""


def _add_obstacles_from_spatial_context(map_inst, dims, scale_x: float, scale_y: float, 
                                         map_width: float, map_height: float):
    """
    Add obstacles from spatial context to the map.
    
    SPATIAL CONTEXT IS THE SOURCE OF TRUTH.
    This function just scales and visualizes what's in the spatial context.
    
    If obstacles don't have positions, we assign them logical positions
    AND UPDATE THE SPATIAL CONTEXT so movement resolution works.
    """
    if not dims.obstacles:
        print(f"[PMAP] No obstacles in spatial context")
        return
    
    print(f"[PMAP] Adding {len(dims.obstacles)} obstacles from spatial context")
    
    # Find the actual room boundaries from the map's rooms
    # This ensures obstacles are placed INSIDE the rooms, not on walls
    room_bounds = None
    if map_inst.state.rooms:
        # Get the first/main room's bounds
        for room in map_inst.state.rooms.values():
            rx, ry, rw, rh = room.bounds
            room_bounds = {
                'left': rx + 1.0,
                'right': (rx + rw) - 1.0,
                'top': ry + 1.0,
                'bottom': (ry + rh) - 1.0,
            }
            break
    
    # Fallback if no rooms defined
    if not room_bounds:
        margin = max(1.0, min(map_width, map_height) * 0.10)
        room_bounds = {
            'left': margin,
            'right': map_width - margin,
            'top': margin,
            'bottom': map_height - margin,
        }

    # Guard against pathological bounds (can happen on very small maps)
    if room_bounds['right'] <= room_bounds['left'] + 1.0:
        room_bounds['left'] = 1.0
        room_bounds['right'] = max(2.0, map_width - 1.0)
    if room_bounds['bottom'] <= room_bounds['top'] + 1.0:
        room_bounds['top'] = 1.0
        room_bounds['bottom'] = max(2.0, map_height - 1.0)
    
    # Calculate usable area
    usable_width = room_bounds['right'] - room_bounds['left']
    usable_height = room_bounds['bottom'] - room_bounds['top']
    center_x = room_bounds['left'] + usable_width / 2
    center_y = room_bounds['top'] + usable_height / 2
    
    # Placement positions INSIDE the room
    step_x = max(1.5, usable_width * 0.22)
    step_y = max(1.5, usable_height * 0.22)
    placement_slots = {
        # Beds go against left wall (inside room)
        'bed': {'x': room_bounds['left'] + (usable_width * 0.20), 'y': room_bounds['top'] + (usable_height * 0.20), 'dx': 0, 'dy': step_y},
        # Terminals/computers against top wall (back of room)
        'terminal': {'x': center_x, 'y': room_bounds['top'] + (usable_height * 0.15), 'dx': step_x, 'dy': 0},
        # Furniture in center area
        'furniture': {'x': center_x, 'y': center_y, 'dx': step_x, 'dy': 0},
        # Storage against right wall (inside room)
        'storage': {'x': room_bounds['right'] - (usable_width * 0.20), 'y': room_bounds['top'] + (usable_height * 0.25), 'dx': 0, 'dy': step_y},
        # Doors at bottom (inside room)
        'door': {'x': center_x, 'y': room_bounds['bottom'] - (usable_height * 0.15), 'dx': step_x, 'dy': 0},
        # Vents/pipes on right side
        'vent': {'x': room_bounds['right'] - (usable_width * 0.15), 'y': center_y, 'dx': 0, 'dy': step_y},
        # Other objects in center-right
        'object': {'x': center_x + (usable_width * 0.15), 'y': center_y + (usable_height * 0.10), 'dx': step_x, 'dy': step_y},
    }
    slot_counters = {k: 0 for k in placement_slots}
    
    # Size presets by type
    size_presets = {
        'bed': (12.0, 8.0),
        'terminal': (8.0, 5.0),
        'furniture': (10.0, 6.0),
        'storage': (6.0, 8.0),
        'door': (8.0, 4.0),
        'vent': (4.0, 4.0),
        'object': (6.0, 5.0),
    }

    base_scale = min(1.0, max(0.35, min(map_width, map_height) / 40.0))
    
    for obs_id, obstacle in dims.obstacles.items():
        name_lower = obstacle.obstacle_name.lower()
        
        # Determine type
        if any(w in name_lower for w in ["bunk", "bed", "pod", "sleep", "cot"]):
            obs_type = "bed"
        elif any(w in name_lower for w in ["terminal", "console", "computer", "node", "screen"]):
            obs_type = "terminal"
        elif any(w in name_lower for w in ["desk", "table", "counter", "workstation"]):
            obs_type = "furniture"
        elif any(w in name_lower for w in ["locker", "cabinet", "shelf", "storage"]):
            obs_type = "storage"
        elif "door" in name_lower or "entrance" in name_lower or "exit" in name_lower:
            obs_type = "door"
        elif any(w in name_lower for w in ["vent", "grate", "conduit", "pipe", "panel", "piping"]):
            obs_type = "vent"
        else:
            obs_type = "object"
        
        # Get position from spatial context OR assign one
        if obstacle.boundary_points and len(obstacle.boundary_points) > 0:
            # Has position - scale it, but also clamp oversize polygons.
            cx = sum(p.x for p in obstacle.boundary_points) / len(obstacle.boundary_points)
            cy = sum(p.y for p in obstacle.boundary_points) / len(obstacle.boundary_points)
            scaled_x = cx * scale_x
            scaled_y = cy * scale_y

            try:
                xs = [p.x for p in obstacle.boundary_points]
                ys = [p.y for p in obstacle.boundary_points]
                bb_w = (max(xs) - min(xs)) * scale_x
                bb_h = (max(ys) - min(ys)) * scale_y

                # If the obstacle is nearly the size of the whole map, shrink it.
                # This prevents "everything is massive" cases like debris spanning the full room.
                max_bb_w = max(2.0, map_width * 0.40)
                max_bb_h = max(2.0, map_height * 0.40)

                if bb_w > max_bb_w or bb_h > max_bb_h:
                    clamped_w = max(1.25, min(max_bb_w, bb_w))
                    clamped_h = max(1.25, min(max_bb_h, bb_h))

                    # Update spatial context polygon in ORIGINAL scale so movement/LoS match visuals.
                    from spatial_context_system import Position
                    orig_w = clamped_w / max(0.0001, scale_x)
                    orig_h = clamped_h / max(0.0001, scale_y)
                    obstacle.boundary_points = [
                        Position(cx - orig_w/2, cy - orig_h/2),
                        Position(cx + orig_w/2, cy - orig_h/2),
                        Position(cx + orig_w/2, cy + orig_h/2),
                        Position(cx - orig_w/2, cy + orig_h/2),
                    ]
            except Exception:
                pass
        else:
            # No position - assign one based on type and UPDATE spatial context
            slot = placement_slots[obs_type]
            count = slot_counters[obs_type]
            scaled_x = slot['x'] + (slot['dx'] * count)
            scaled_y = slot['y'] + (slot['dy'] * count)
            slot_counters[obs_type] += 1
            
            # IMPORTANT: Update spatial context with the position (in original scale)
            # So movement resolution can find this obstacle
            from spatial_context_system import Position
            original_x = scaled_x / scale_x
            original_y = scaled_y / scale_y
            obstacle.boundary_points = [
                Position(original_x - 1, original_y - 1),
                Position(original_x + 1, original_y - 1),
                Position(original_x + 1, original_y + 1),
                Position(original_x - 1, original_y + 1),
            ]
        
        # Get size
        if obstacle.boundary_points and len(obstacle.boundary_points) > 0:
            try:
                xs = [p.x for p in obstacle.boundary_points]
                ys = [p.y for p in obstacle.boundary_points]
                w = max(1.25, (max(xs) - min(xs)) * scale_x)
                h = max(1.25, (max(ys) - min(ys)) * scale_y)
            except Exception:
                w, h = size_presets.get(obs_type, (6.0, 5.0))
                w *= base_scale
                h *= base_scale
        else:
            w, h = size_presets.get(obs_type, (6.0, 5.0))
            w *= base_scale
            h *= base_scale

        max_w = max(2.0, map_width * 0.30)
        max_h = max(2.0, map_height * 0.30)
        w = max(1.25, min(max_w, w))
        h = max(1.25, min(max_h, h))

        # Clamp to map bounds (account for obstacle extents)
        half_w = w / 2
        half_h = h / 2
        scaled_x = max(half_w, min(map_width - half_w, scaled_x))
        scaled_y = max(half_h, min(map_height - half_h, scaled_y))
        
        # Add to map
        map_obs = MapObstacle(
            obstacle_id=obs_id,
            name=obstacle.obstacle_name,
            x=scaled_x,
            y=scaled_y,
            width=w,
            height=h,
            blocks_los=obstacle.blocks_line_of_sight,
            obstacle_type=obs_type
        )
        map_inst.state.obstacles[obs_id] = map_obs


def _sync_llm_obstacles_to_spatial_context(layout, dims, scale_x: float, scale_y: float,
                                            session_id: str = None):
    """
    Sync LLM-generated obstacles BACK to the spatial context system.
    
    This is CRITICAL - it ensures the simulation is aware of ALL furniture
    so actors can interact with them (sit on chairs, use terminals, etc.)
    
    IMPORTANT: We use MAP COORDINATES (250x200) directly in spatial context
    so that movement resolution works correctly with the visual map.
    
    Args:
        layout: The GeneratedLayout from LLM
        dims: Location dimensions from spatial context
        scale_x, scale_y: Scale factors (NOT USED - we keep map scale)
        session_id: Session ID for spatial manager
    """
    from spatial_context_system import get_spatial_manager, Obstacle, Position
    
    spatial = get_spatial_manager(session_id=session_id)
    context = spatial.get_current_context()
    
    if not context:
        print(f"[PMAP] Cannot sync obstacles - no spatial context")
        return
    
    # Authoritative dimensions come from spatial context.
    # Never overwrite dims.width/height from a layout object (which may be stale or undersized).
    try:
        MAP_WIDTH = float(getattr(dims, 'width', 0.0) or 0.0)
        MAP_HEIGHT = float(getattr(dims, 'height', 0.0) or 0.0)
    except Exception:
        MAP_WIDTH, MAP_HEIGHT = 0.0, 0.0

    if MAP_WIDTH <= 0 or MAP_HEIGHT <= 0:
        MAP_WIDTH = float(getattr(layout, 'width', 0.0) or 0.0)
        MAP_HEIGHT = float(getattr(layout, 'height', 0.0) or 0.0)

    if MAP_WIDTH <= 0 or MAP_HEIGHT <= 0:
        MAP_WIDTH, MAP_HEIGHT = LocationScale.get_scale(getattr(dims, 'location_type', None) or 'interior')

    # Ensure dims carries the authoritative sizes for downstream validity checks.
    dims.width = MAP_WIDTH
    dims.height = MAP_HEIGHT
    
    # Clear existing obstacles and replace with LLM-generated ones
    dims.obstacles.clear()

    # Detect the true coordinate extents of the incoming layout. Some generators/models
    # will emit furniture in a legacy 250x200-ish coordinate space even when layout.width
    # is small. We scale everything into the authoritative MAP_WIDTH/MAP_HEIGHT.
    src_w = float(getattr(layout, 'width', 0.0) or 0.0)
    src_h = float(getattr(layout, 'height', 0.0) or 0.0)
    try:
        max_x = src_w
        max_y = src_h
        for r in (getattr(layout, 'rooms', {}) or {}).values():
            rx = float(getattr(r, 'x', 0.0) or 0.0)
            ry = float(getattr(r, 'y', 0.0) or 0.0)
            rw = float(getattr(r, 'width', 0.0) or 0.0)
            rh = float(getattr(r, 'height', 0.0) or 0.0)
            max_x = max(max_x, rx + rw)
            max_y = max(max_y, ry + rh)
        for o in getattr(layout, 'obstacles', []) or []:
            ox = float(getattr(o, 'x', 0.0) or 0.0)
            oy = float(getattr(o, 'y', 0.0) or 0.0)
            ow = float(getattr(o, 'width', 0.0) or 0.0)
            oh = float(getattr(o, 'height', 0.0) or 0.0)
            max_x = max(max_x, ox + (ow / 2.0))
            max_y = max(max_y, oy + (oh / 2.0))
        src_w = max(src_w, max_x)
        src_h = max(src_h, max_y)
    except Exception:
        pass

    layout_to_map_sx = (MAP_WIDTH / src_w) if (MAP_WIDTH > 0 and src_w > 0) else 1.0
    layout_to_map_sy = (MAP_HEIGHT / src_h) if (MAP_HEIGHT > 0 and src_h > 0) else 1.0
    
    synced_count = 0
    door_synced_count = 0
    for obs in layout.obstacles:
        # Scale from layout-space into authoritative map-space.
        ox = float(getattr(obs, 'x', 0.0) or 0.0) * layout_to_map_sx
        oy = float(getattr(obs, 'y', 0.0) or 0.0) * layout_to_map_sy
        original_w = float(getattr(obs, 'width', 0.0) or 0.0) * layout_to_map_sx
        original_h = float(getattr(obs, 'height', 0.0) or 0.0) * layout_to_map_sy

        # Layout obstacles are treated as top-left coordinates. Spatial context uses obstacle centers.
        original_x = ox + (original_w / 2.0)
        original_y = oy + (original_h / 2.0)

        obs_type = (obs.obstacle_type.lower() if getattr(obs, 'obstacle_type', None) else "furniture")
        name_lower = (getattr(obs, 'name', '') or '').lower()

        # Hard cap to a fraction of the map so LLM can't create room-filling debris.
        # Debris-like objects should be much smaller than furniture by default.
        frac_w = 0.30
        frac_h = 0.30
        if obs_type in ["debris", "rubble"] or any(k in name_lower for k in ["bone", "bones", "rubble", "debris", "wreckage", "blocks", "collapsed"]):
            frac_w = 0.22
            frac_h = 0.22

        max_w = max(0.5, MAP_WIDTH * frac_w)
        max_h = max(0.5, MAP_HEIGHT * frac_h)
        original_w = min(float(original_w) if original_w else 0.0, max_w)
        original_h = min(float(original_h) if original_h else 0.0, max_h)

        half_w = float(original_w) / 2.0 if original_w else 0.0
        half_h = float(original_h) / 2.0 if original_h else 0.0
        original_x = _clamp_1d(float(original_x), half_w, MAP_WIDTH - half_w)
        original_y = _clamp_1d(float(original_y), half_h, MAP_HEIGHT - half_h)
        
        # Create boundary points for the obstacle
        boundary = [
            Position(original_x - original_w/2, original_y - original_h/2),
            Position(original_x + original_w/2, original_y - original_h/2),
            Position(original_x + original_w/2, original_y + original_h/2),
            Position(original_x - original_w/2, original_y + original_h/2),
        ]
        
        # Determine if it blocks movement/LOS based on type

        is_portal = (
            obs_type in ["door", "portal", "exit", "entrance", "hatch", "trapdoor", "grate", "ladder", "manhole"]
            or any(w in name_lower for w in [
                "door", "exit", "entrance", "gate", "hatch", "trapdoor", "grate", "sewer", "manhole", "ladder"
            ])
        )

        if is_portal:
            blocks_movement = False
            blocks_los = False
        else:
            blocks_movement = obs_type not in ["rug", "mat", "decor", "art", "painting"]
            blocks_los = obs_type in ["cabinet", "shelf", "storage", "wall", "partition"]
        
        portal_kind = ""
        is_external = False
        connects_to = ""
        if is_portal:
            # Rule: any portal implies transitioning to a new location by default
            is_external = True
            connects_to = "outside"

            if any(w in name_lower for w in ["exit", "entrance", "gate"]):
                portal_kind = "exit"
            elif any(w in name_lower for w in ["hatch", "trapdoor", "attic"]):
                portal_kind = "hatch"
            elif any(w in name_lower for w in ["grate", "sewer", "manhole"]):
                portal_kind = "grate"
            elif "ladder" in name_lower:
                portal_kind = "ladder"
            else:
                portal_kind = "door"

        # Create spatial context obstacle
        spatial_obs = Obstacle(
            obstacle_name=obs.name,
            obstacle_type="door" if is_portal else (obs.obstacle_type or "furniture"),
            boundary_points=boundary,
            blocks_movement=blocks_movement,
            blocks_line_of_sight=blocks_los,
            height=2.0 if blocks_los else 1.0,
            portal_kind=portal_kind,
            connects_from="",
            connects_to=connects_to,
            is_external=is_external
        )
        
        # Add to spatial context using obstacle name as ID
        obs_id = obs.name.lower().replace(" ", "_").replace("'", "")[:20]
        # Ensure unique ID
        base_id = obs_id
        counter = 1
        while obs_id in dims.obstacles:
            obs_id = f"{base_id}_{counter}"
            counter += 1
        
        dims.obstacles[obs_id] = spatial_obs
        synced_count += 1

    try:
        for wall in getattr(layout, 'walls', []) or []:
            if not getattr(wall, 'has_door', False):
                continue

            start = getattr(wall, 'start', None)
            end = getattr(wall, 'end', None)
            door_pos = float(getattr(wall, 'door_position', 0.5))
            if not start or not end:
                continue

            sx0 = float(start[0]) * layout_to_map_sx
            sy0 = float(start[1]) * layout_to_map_sy
            sx1 = float(end[0]) * layout_to_map_sx
            sy1 = float(end[1]) * layout_to_map_sy

            x0 = sx0
            y0 = sy0
            x1 = sx1
            y1 = sy1

            door_x = x0 + (x1 - x0) * door_pos
            door_y = y0 + (y1 - y0) * door_pos

            door_w = 6.0
            door_h = 4.0
            door_x = _clamp_1d(door_x, door_w / 2, MAP_WIDTH - door_w / 2)
            door_y = _clamp_1d(door_y, door_h / 2, MAP_HEIGHT - door_h / 2)

            # De-dup: if a portal/door obstacle already exists near this wall door, don't add another.
            try:
                near = False
                thresh = max(1.5, min(MAP_WIDTH, MAP_HEIGHT) * 0.08)
                for existing in (dims.obstacles or {}).values():
                    et = str(getattr(existing, 'obstacle_type', '') or '').lower()
                    en = str(getattr(existing, 'obstacle_name', '') or '').lower()
                    if et != 'door' and not any(k in en for k in ["door", "exit", "entrance", "gate", "hatch", "trapdoor", "portal"]):
                        continue
                    pts = getattr(existing, 'boundary_points', None) or []
                    if not pts:
                        continue
                    ex = sum(float(p.x) for p in pts) / len(pts)
                    ey = sum(float(p.y) for p in pts) / len(pts)
                    if ((ex - door_x) ** 2 + (ey - door_y) ** 2) ** 0.5 <= thresh:
                        near = True
                        break
                if near:
                    continue
            except Exception:
                pass

            # Treat all portals as leading to a new location (not an intra-location connector)
            raw_to = str(getattr(wall, 'room_b', '') or '').strip()
            dest_key = raw_to if raw_to else "outside"
            is_exit = True
            door_name = "Exit" if dest_key == "outside" else "Door"

            spatial_door = Obstacle(
                obstacle_name=door_name,
                obstacle_type="door",
                boundary_points=[
                    Position(door_x - door_w / 2, door_y - door_h / 2),
                    Position(door_x + door_w / 2, door_y - door_h / 2),
                    Position(door_x + door_w / 2, door_y + door_h / 2),
                    Position(door_x - door_w / 2, door_y + door_h / 2),
                ],
                blocks_movement=False,
                blocks_line_of_sight=False,
                height=2.0,
                portal_kind="exit",
                connects_from=str(getattr(wall, 'room_a', '') or ''),
                connects_to=dest_key,
                is_external=True
            )

            wall_id = str(getattr(wall, 'wall_id', '') or '')
            door_id = f"door_{wall_id}" if wall_id else f"door_{door_synced_count}"
            door_id = door_id.lower().replace(" ", "_").replace("'", "")[:30]

            base_id = door_id
            counter = 1
            while door_id in dims.obstacles:
                door_id = f"{base_id}_{counter}"
                counter += 1

            dims.obstacles[door_id] = spatial_door
            door_synced_count += 1
    except Exception as e:
        print(f"[PMAP] Failed to sync wall doors to spatial context: {e}")
    
    print(f"[PMAP] Synced {synced_count} LLM obstacles to spatial context (using {MAP_WIDTH}x{MAP_HEIGHT} coords)")
    if door_synced_count:
        print(f"[PMAP] Synced {door_synced_count} wall doors to spatial context")
    
    # CRITICAL: Save spatial context to disk so obstacles persist across manager reloads
    spatial._save()
    
    # Save again after syncing
    spatial._save()


def _add_actors_only_from_spatial_context(map_inst, dims, scale_x: float, scale_y: float,
                                           map_width: float, map_height: float):
    """
    Add only NPC actors from spatial context, NOT furniture.
    
    Used when LLM layout generator has already provided furniture.
    This ensures we don't duplicate or override the well-positioned LLM furniture.
    """
    # This function intentionally does NOT add obstacles
    # The LLM-generated furniture is already in place
    # Actors are handled separately in the main sync function
    print(f"[PMAP] Skipping spatial context obstacles (using LLM furniture)")
    pass


def sync_from_spatial_context(session_id: str = None):
    """
    Sync the pygame map with the current spatial context.
    
    Uses the layout generator to create proper dungeon-style maps
    with scaled dimensions (250x200 units).
    
    IMPORTANT: Layout is cached per location - only regenerates when
    location changes, not on every action within the same location.
    """
    global _layout_cache
    
    map_inst = get_pygame_map()
    if not map_inst or not map_inst.running:
        return
    
    try:
        from spatial_context_system import get_spatial_manager
        
        print(f"[PMAP] sync_from_spatial_context called with session_id={session_id}")

        if _layout_cache_disabled():
            try:
                if _layout_cache:
                    _layout_cache.clear()
            except Exception:
                pass

        # Reload persisted layout cache on demand (so map layout is identical after resume)
        try:
            if (not _layout_cache) and session_id and (not _layout_cache_disabled()):
                _load_layout_cache_from_disk(session_id)
        except Exception:
            pass
        
        # Try LLM-based layout generator first (better spatial understanding)
        try:
            from llm_layout_generator import generate_layout_for_location_llm
            use_llm_layout = True
            print(f"[PMAP] LLM layout generator available")
        except ImportError as e:
            from layout_generator import generate_layout_for_location
            use_llm_layout = False
            print(f"[PMAP] Using fallback layout generator: {e}")
        
        spatial = get_spatial_manager(session_id=session_id)
        print(f"[PMAP] Spatial manager: {spatial}, current_location: {getattr(spatial, 'current_location', 'N/A')}")
        
        context = spatial.get_current_context()
        
        if not context:
            print(f"[PMAP] No spatial context available - is a location loaded?")
            print(f"[PMAP] Available contexts: {list(spatial.contexts.keys()) if hasattr(spatial, 'contexts') else 'N/A'}")
            return
        
        dims = context.location_dimensions
        scene_description = getattr(dims, 'scene_description', '') or getattr(dims, 'description', '') or ""
        # Prefer display name, but never overwrite a known label with "Unknown"
        location_name = (getattr(dims, 'location_name', None) or '').strip()
        if not location_name:
            try:
                location_name = (getattr(spatial, 'current_location', None) or '').strip()
            except Exception:
                location_name = ''
        if not location_name:
            location_name = (getattr(map_inst.state, 'location_name', None) or '').strip() or "Unknown"
        
        # Dynamic map sizing: use spatial context dimensions when available,
        # otherwise fall back to type-based scale presets.
        try:
            base_w = float(getattr(dims, 'width', 0.0) or 0.0)
            base_h = float(getattr(dims, 'height', 0.0) or 0.0)
        except Exception:
            base_w, base_h = 0.0, 0.0

        if base_w <= 0 or base_h <= 0:
            base_w, base_h = LocationScale.get_scale(dims.location_type or "interior")

        MAP_WIDTH = float(base_w)
        MAP_HEIGHT = float(base_h)

        # No scaling between backend and map: backend coords are authoritative.
        scale_x = 1.0
        scale_y = 1.0
        
        # Check if we need to generate a new layout or use cached
        current_location = map_inst.state.location_name or ""
        
        # Debug: Show cache state and location info
        print(f"[PMAP] ═══════════════════════════════════════════════════")
        print(f"[PMAP] Spatial current_location: '{spatial.current_location}'")
        print(f"[PMAP] dims.location_name: '{location_name}'")
        print(f"[PMAP] Map state location: '{current_location}'")
        print(f"[PMAP] Cache keys: {list(_layout_cache.keys())}")
        print(f"[PMAP] Is '{location_name}' in cache? {location_name in _layout_cache}")
        print(f"[PMAP] ═══════════════════════════════════════════════════")
        
        # PERSISTENCE: Check if we have a cached layout for this location
        # Also check if we need to force regeneration due to location mismatch
        force_regenerate = False
        if _layout_cache_disabled():
            force_regenerate = True
        if current_location and location_name != current_location and location_name not in _layout_cache:
            # Moving to a genuinely new location - ensure we generate a new layout
            print(f"[PMAP] 🆕 Detected NEW location: '{location_name}' (was '{current_location}')")
            force_regenerate = True
            # Clear stale actor positions from prior location so they don't render out-of-bounds
            try:
                map_inst.state.actors.clear()
                print(f"[PMAP] Cleared stale actor positions from previous location")
            except Exception:
                pass

        use_cached_layout = (location_name in _layout_cache) and (not force_regenerate)

        if use_cached_layout:
            # RETURNING TO CACHED LOCATION - use cached layout
            cached_layout = None
            cached_scale_x = 1.0
            cached_scale_y = 1.0
            cached_w = 0.0
            cached_h = 0.0
            try:
                tup = _layout_cache[location_name]
                if isinstance(tup, (list, tuple)):
                    if len(tup) >= 5:
                        cached_layout, cached_scale_x, cached_scale_y, cached_w, cached_h = tup[:5]
                    elif len(tup) >= 3:
                        cached_layout, cached_scale_x, cached_scale_y = tup[:3]
                    else:
                        cached_layout = tup[0] if len(tup) >= 1 else None
            except Exception:
                cached_layout = None

            scale_x, scale_y = float(cached_scale_x or 1.0), float(cached_scale_y or 1.0)
            try:
                cached_w = float(cached_w or 0.0)
                cached_h = float(cached_h or 0.0)
            except Exception:
                cached_w, cached_h = 0.0, 0.0

            # Backward compatibility: older cache entries may not store width/height.
            # Infer from the cached layout object when possible.
            if (cached_w <= 0.0 or cached_h <= 0.0) and cached_layout is not None:
                try:
                    lw = float(getattr(cached_layout, 'width', 0.0) or 0.0)
                    lh = float(getattr(cached_layout, 'height', 0.0) or 0.0)
                    if lw > 0.0 and lh > 0.0:
                        cached_w, cached_h = lw, lh
                except Exception:
                    pass

            # If cached layout was generated under a different coordinate space, regenerate.
            if cached_w > 0.0 and cached_h > 0.0:
                if abs(float(cached_w) - float(MAP_WIDTH)) > 0.01 or abs(float(cached_h) - float(MAP_HEIGHT)) > 0.01:
                    print(f"[PMAP] ♻️ Cached layout dims mismatch for '{location_name}': cached {cached_w}x{cached_h} vs current {MAP_WIDTH}x{MAP_HEIGHT} - regenerating")
                    try:
                        _layout_cache.pop(location_name, None)
                        _save_layout_cache_to_disk(session_id)
                    except Exception:
                        pass
                    use_cached_layout = False
                    force_regenerate = True

            if not cached_layout:
                use_cached_layout = False

            if use_cached_layout and location_name != current_location:
                # Different location - apply the cached layout
                print(f"[PMAP] ♻️ Restoring cached layout for: {location_name}")
                # IMPORTANT: set authoritative dimensions BEFORE applying layout so apply_generated_layout
                # scales rooms/walls/obstacles into the correct coordinate space (prevents legacy 250x200 artifacts).
                map_inst.state.width = float(MAP_WIDTH)
                map_inst.state.height = float(MAP_HEIGHT)
                map_inst.state.location_name = location_name
                map_inst.state.local_location_name = location_name
                map_inst.state.local_width = float(MAP_WIDTH)
                map_inst.state.local_height = float(MAP_HEIGHT)
                map_inst.state.local_location_type = getattr(dims, 'location_type', None) or map_inst.state.location_type
                apply_generated_layout(cached_layout, map_inst)
                # Keep pygame map dimensions authoritative to spatial dims
                map_inst.state.width = float(MAP_WIDTH)
                map_inst.state.height = float(MAP_HEIGHT)
                map_inst.state.location_name = location_name
                map_inst.state.local_location_name = location_name
                map_inst.state.local_width = float(MAP_WIDTH)
                map_inst.state.local_height = float(MAP_HEIGHT)
                map_inst.state.local_location_type = getattr(dims, 'location_type', None) or map_inst.state.location_type
                # CRITICAL: Also sync obstacles to spatial context so movement resolution works
                _sync_llm_obstacles_to_spatial_context(cached_layout, dims, scale_x, scale_y, session_id)
            elif use_cached_layout:
                # Same location - just update actors, DON'T regenerate layout or move obstacles
                print(f"[PMAP] ✓ Same location '{location_name}', updating actors only (obstacles remain stationary)")
                # Never re-sync obstacles when using cached layout for same location
                # This ensures obstacles only move when explicitly acted upon by player/NPC
                # Only sync obstacles if spatial context is completely empty (first load only)
                if not dims.obstacles and location_name != current_location:
                    print(f"[PMAP] First load: Syncing obstacles from cached layout to spatial context")
                    _sync_llm_obstacles_to_spatial_context(cached_layout, dims, scale_x, scale_y, session_id)
            # Skip the layout generation - we're using cache
            # Fall through to actor update section

        if (not use_cached_layout) or force_regenerate:
            # NEW LOCATION - generate fresh layout
            print(f"[PMAP] 🆕 Generating NEW layout for: {location_name}")
            
            # Clear all actor trails when entering a new location
            map_inst.state.actors.clear()  # Clear old actors (they'll be re-added below)
            try:
                spatial.clear_all_trails()
                print(f"[PMAP] Cleared trails for new location")
            except Exception:
                pass
            
            # Get zone names for layout generation
            zone_names = [zone.zone_name for zone in dims.zones.values()] if dims.zones else ["Main Area"]
            
            # INTELLIGENT ZONE COUNT: Determine if we need multiple rooms or just one
            actual_zone_count = _determine_zone_count(location_name, dims, len(zone_names))
            
            # If we need fewer zones than provided, use just "Main Area"
            if actual_zone_count == 1:
                zone_names = [location_name]  # Single room with location name
            elif actual_zone_count < len(zone_names):
                zone_names = zone_names[:actual_zone_count]
            
            try:
                # Use LLM layout generator if available (better spatial understanding)
                if use_llm_layout:
                    # Get scene description if available from spatial context
                    # Try both 'scene_description' and 'description' attributes
                    scene_desc = getattr(dims, 'scene_description', '') or getattr(dims, 'description', '') or ""
                    if scene_desc:
                        print(f"[PMAP] Scene description for layout ({len(scene_desc)} chars): {scene_desc[:100]}...")
                    else:
                        print(f"[PMAP] ⚠️ No scene description available for layout generation")
                    
                    layout = generate_layout_for_location_llm(
                        zone_names=zone_names,
                        width=MAP_WIDTH,
                        height=MAP_HEIGHT,
                        location_type=dims.location_type or "interior",
                        location_name=location_name,
                        scene_description=scene_desc
                    )
                    print(f"[PMAP] Using LLM layout generator for '{location_name}'")
                else:
                    layout = generate_layout_for_location(
                        zone_names=zone_names,
                        width=MAP_WIDTH,
                        height=MAP_HEIGHT,
                        location_type=dims.location_type or "interior"
                    )
                
                # Cache the layout for persistence (memory + disk)
                if not _layout_cache_disabled():
                    _layout_cache[location_name] = (layout, scale_x, scale_y, float(MAP_WIDTH), float(MAP_HEIGHT))
                    print(f"[PMAP] 💾 Cached layout for: {location_name} (total cached: {len(_layout_cache)})")
                    try:
                        _save_layout_cache_to_disk(session_id)
                    except Exception:
                        pass
                
                # Apply the generated layout (rooms/walls structure)
                # IMPORTANT: set authoritative dimensions BEFORE applying layout so apply_generated_layout
                # scales rooms/walls/obstacles into the correct coordinate space.
                map_inst.state.width = float(MAP_WIDTH)
                map_inst.state.height = float(MAP_HEIGHT)
                map_inst.state.location_name = location_name
                map_inst.state.local_location_name = location_name
                map_inst.state.local_width = float(MAP_WIDTH)
                map_inst.state.local_height = float(MAP_HEIGHT)
                map_inst.state.local_location_type = getattr(dims, 'location_type', None) or map_inst.state.location_type

                apply_generated_layout(layout, map_inst)
                # Keep pygame map dimensions authoritative to spatial dims
                map_inst.state.width = float(MAP_WIDTH)
                map_inst.state.height = float(MAP_HEIGHT)
                map_inst.state.location_name = location_name
                map_inst.state.local_location_name = location_name
                map_inst.state.local_width = float(MAP_WIDTH)
                map_inst.state.local_height = float(MAP_HEIGHT)
                map_inst.state.local_location_type = getattr(dims, 'location_type', None) or map_inst.state.location_type
                
                # KEEP LLM-generated furniture if using LLM layout generator
                if use_llm_layout and layout.obstacles:
                    print(f"[PMAP] Using {len(layout.obstacles)} LLM-generated furniture pieces")
                    # CRITICAL: Sync LLM obstacles back to spatial context so simulation knows about them
                    _sync_llm_obstacles_to_spatial_context(layout, dims, scale_x, scale_y, session_id)
                    # Only add NPCs/actors from spatial context, not furniture
                    _add_actors_only_from_spatial_context(map_inst, dims, scale_x, scale_y, MAP_WIDTH, MAP_HEIGHT)
                else:
                    # Fallback: use spatial context obstacles (old behavior)
                    map_inst.state.obstacles.clear()
                    _add_obstacles_from_spatial_context(map_inst, dims, scale_x, scale_y, MAP_WIDTH, MAP_HEIGHT)
                
            except Exception as e:
                print(f"[PMAP] Layout generation failed: {e}, using fallback")
                map_inst.state.width = MAP_WIDTH
                map_inst.state.height = MAP_HEIGHT
                map_inst.state.location_name = location_name
                map_inst.state.local_location_name = location_name
                map_inst.state.local_width = float(MAP_WIDTH)
                map_inst.state.local_height = float(MAP_HEIGHT)
                map_inst.state.local_location_type = getattr(dims, 'location_type', None) or map_inst.state.location_type
                _add_obstacles_from_spatial_context(map_inst, dims, scale_x, scale_y, MAP_WIDTH, MAP_HEIGHT)
        
        # Update actors - use spatial context positions directly
        for actor_id, actor_pos in context.actor_positions.items():
            scaled_x = actor_pos.position.x
            scaled_y = actor_pos.position.y
            
            # Only do intelligent placement for NEW actors (not in map yet)
            # This prevents overriding movement positions
            is_new_actor = actor_id not in map_inst.state.actors
            
            if is_new_actor and map_inst.state.obstacles:
                if not actor_pos.is_user_actor:
                    occ = getattr(actor_pos, 'occupation', '') or ""
                    if occ:
                        best = None
                        best_score = -1
                        for obs in map_inst.state.obstacles.values():
                            sc = _score_obstacle_for_occupation(occ, obs.name, obs.obstacle_type)
                            if sc > best_score:
                                best_score = sc
                                best = obs

                        if (best is None or best_score <= 0) and scene_description:
                            names = [o.name for o in map_inst.state.obstacles.values() if getattr(o, 'name', None)]
                            picked = _llm_pick_obstacle_for_npc(occ, names, scene_description, location_name)
                            if picked:
                                picked_l = picked.strip().lower()
                                for obs in map_inst.state.obstacles.values():
                                    if (obs.name or "").strip().lower() == picked_l:
                                        best = obs
                                        best_score = 1
                                        break

                        if best is not None:
                            try:
                                from spatial_context_system import Position
                                context_now = spatial.get_current_context()
                                dims_now = context_now.location_dimensions if context_now else None

                                if dims_now is not None:
                                    half_w = float(best.width) / 2.0
                                    half_h = float(best.height) / 2.0
                                    left = float(best.x) - half_w
                                    right = float(best.x) + half_w
                                    top = float(best.y) - half_h
                                    bottom = float(best.y) + half_h
                                    cx = float(best.x)
                                    cy = float(best.y)

                                    min_dim = max(1.0, min(float(MAP_WIDTH), float(MAP_HEIGHT)))
                                    offset = max(1.5, min_dim * 0.06)

                                    candidates = [
                                        Position(right + offset, cy),
                                        Position(left - offset, cy),
                                        Position(cx, bottom + offset),
                                        Position(cx, top - offset),
                                        Position(cx + offset, cy + offset),
                                        Position(cx - offset, cy + offset),
                                        Position(cx + offset, cy - offset),
                                        Position(cx - offset, cy - offset),
                                    ]

                                    chosen = None
                                    for cand in candidates:
                                        if dims_now.is_position_valid(cand):
                                            chosen = cand
                                            break

                                    if chosen is not None:
                                        spatial.move_actor(actor_id, chosen)
                                        scaled_x = chosen.x
                                        scaled_y = chosen.y
                            except Exception:
                                pass
            
            # Debug: Show position updates
            if actor_id in map_inst.state.actors:
                old_actor = map_inst.state.actors[actor_id]
                if abs(old_actor.x - scaled_x) > 1 or abs(old_actor.y - scaled_y) > 1:
                    print(f"[PMAP] Actor {actor_pos.actor_name} moved: ({old_actor.x:.1f}, {old_actor.y:.1f}) → ({scaled_x:.1f}, {scaled_y:.1f})")
            
            # Clamp to map bounds
            min_dim = max(1.0, min(float(MAP_WIDTH), float(MAP_HEIGHT)))
            margin = max(6.0, min(18.0, min_dim * 0.04))
            scaled_x = _clamp_1d(float(scaled_x), margin, float(MAP_WIDTH) - margin)
            scaled_y = _clamp_1d(float(scaled_y), margin, float(MAP_HEIGHT) - margin)
            
            # Get trail data from spatial context
            trail_data = []
            facing = 0.0
            trail_dist = 0.0
            straight_dist = 0.0
            avg_speed = 0.0
            
            if hasattr(actor_pos, 'trail') and actor_pos.trail:
                for tp in actor_pos.trail:
                    tx, ty = tp.position.x, tp.position.y
                    trail_data.append((tx, ty, tp.timestamp))
                
                # Get calculated values - trail distance is already in correct units
                facing = actor_pos.facing_direction
                trail_dist = actor_pos.get_trail_distance()
                straight_dist = actor_pos.get_straight_line_distance()
                avg_speed = actor_pos.get_average_speed()
            
            # Preserve and merge trail data from map state
            # This ensures trail persists across syncs even if spatial context resets
            if actor_id in map_inst.state.actors:
                old_actor = map_inst.state.actors[actor_id]
                
                # ALWAYS merge with existing trail - spatial context may not have full history
                if old_actor.trail:
                    # Merge: use existing trail as base, add any new points from spatial context
                    existing_coords = set((round(t[0], 1), round(t[1], 1)) for t in old_actor.trail)
                    merged_trail = old_actor.trail.copy()
                    
                    # Add new points from spatial context that aren't already in trail
                    for tp in trail_data:
                        coord = (round(tp[0], 1), round(tp[1], 1))
                        if coord not in existing_coords:
                            merged_trail.append(tp)
                            existing_coords.add(coord)
                    
                    trail_data = merged_trail
                    # Recalculate distances if we merged
                    if len(trail_data) >= 1:
                        trail_dist = sum(
                            ((trail_data[i][0] - trail_data[i-1][0])**2 + 
                             (trail_data[i][1] - trail_data[i-1][1])**2)**0.5
                            for i in range(1, len(trail_data))
                        )
                
                # If actor moved, add old position to trail
                dx = abs(old_actor.x - scaled_x)
                dy = abs(old_actor.y - scaled_y)
                if dx > 1 or dy > 1:
                    import time
                    # Check if this point is already in trail
                    old_coord = (round(old_actor.x, 1), round(old_actor.y, 1))
                    existing_coords = set((round(t[0], 1), round(t[1], 1)) for t in trail_data)
                    if old_coord not in existing_coords:
                        trail_data.append((old_actor.x, old_actor.y, time.time()))
                        print(f"[PMAP] 🚶 Trail point added: ({old_actor.x:.1f}, {old_actor.y:.1f}) → ({scaled_x:.1f}, {scaled_y:.1f}) | Trail length: {len(trail_data)}")
                    else:
                        print(f"[PMAP] 🚶 Actor moved: ({old_actor.x:.1f}, {old_actor.y:.1f}) → ({scaled_x:.1f}, {scaled_y:.1f}) | Trail length: {len(trail_data)}")
                    
                    # Trim trail to max length (20 points)
                    if len(trail_data) > 20:
                        trail_data = trail_data[-20:]
                    # Recalculate trail distance
                    if len(trail_data) >= 1:
                        trail_dist = sum(
                            ((trail_data[i][0] - trail_data[i-1][0])**2 + 
                             (trail_data[i][1] - trail_data[i-1][1])**2)**0.5
                            for i in range(1, len(trail_data))
                        )
                        # Add distance to current position
                        trail_dist += ((scaled_x - trail_data[-1][0])**2 + 
                                      (scaled_y - trail_data[-1][1])**2)**0.5
            
            # Update actor with full trail info
            map_actor = MapActor(
                actor_id=actor_id,
                name=actor_pos.actor_name,
                actor_type=ActorType.UA if actor_pos.is_user_actor else ActorType.NUA,
                x=scaled_x,
                y=scaled_y,
                occupation=getattr(actor_pos, 'occupation', '') or "",
                facing_direction=facing,
                trail=trail_data,
                trail_distance=trail_dist,
                straight_distance=straight_dist,
                average_speed=avg_speed
            )
            
            # Preserve selection state
            if actor_id in map_inst.state.actors:
                map_actor.is_selected = map_inst.state.actors[actor_id].is_selected
            
            # Debug: confirm trail is set
            if trail_data and actor_pos.is_user_actor:
                first_trail = trail_data[0]
                print(f"[PMAP] UA trail: {len(trail_data)} waypoints from ({first_trail[0]:.1f}, {first_trail[1]:.1f}) → current ({scaled_x:.1f}, {scaled_y:.1f})")
            elif actor_pos.is_user_actor:
                print(f"[PMAP] UA trail: No waypoints, current_pos=({scaled_x:.1f}, {scaled_y:.1f})")
            
            map_inst.state.actors[actor_id] = map_actor
        
    except ImportError as e:
        print(f"[PMAP] Import error during sync: {e}")
    except Exception as e:
        import traceback
        print(f"[PMAP] Sync error: {e}")
        traceback.print_exc()


def clear_layout_cache(location_name: str = None, session_id: str = None):
    """
    Clear cached layout(s).
    
    Args:
        location_name: Specific location to clear, or None to clear all
        session_id: Session ID for persisted cache file (defaults to 'default')
    """
    global _layout_cache
    if location_name:
        if location_name in _layout_cache:
            _layout_cache.pop(location_name, None)
            print(f"[PMAP] Cleared cache for location: {location_name}")
        else:
            print(f"[PMAP] No cache to clear for: {location_name}")
    else:
        count = len(_layout_cache)
        _layout_cache.clear()
        print(f"[PMAP] Cleared all layout cache ({count} entries)")

    # Best-effort: also update persisted cache on disk
    try:
        sid = (session_id or 'default').strip() or 'default'
        p = _layout_cache_path(sid)
        if not p.exists():
            return
        if location_name is None:
            p.unlink(missing_ok=True)
            return
        raw = json.loads(p.read_text(encoding='utf-8') or '{}')
        if not isinstance(raw, dict):
            return
        layouts = raw.get('layouts')
        if not isinstance(layouts, dict):
            return
        # Try to remove by exact key, then case-insensitive fallback.
        if location_name in layouts:
            layouts.pop(location_name, None)
        else:
            key_l = str(location_name).strip().lower()
            for k in list(layouts.keys()):
                if str(k).strip().lower() == key_l:
                    layouts.pop(k, None)
                    break
        raw['layouts'] = layouts
        p.write_text(json.dumps(raw, indent=2), encoding='utf-8')
    except Exception:
        pass


def auto_sync_map(session_id: str = None):
    """
    Auto-sync map if it's running.

    Call this after any action that might change actor positions.
    Does nothing if map isn't running - safe to call anywhere.
    """
    try:
        map_inst = get_pygame_map()
        if map_inst and map_inst.running:
            print(f"[PMAP] 🔄 auto_sync_map - updating actor positions...")
            sync_from_spatial_context(session_id=session_id)
            print(f"[PMAP] ✓ Map synced")
            # If running headless, push state to the narrative display map panel
            if map_inst.suppress_own_window:
                try:
                    from pygame_narrative_display import send_map_state
                    send_map_state(map_inst.get_display_state())
                except Exception:
                    pass
        else:
            # Silent - don't spam if map not open
            pass
    except Exception as e:
        print(f"[PMAP] auto_sync_map error: {e}")


def sync_from_spatial_context_legacy(session_id: str = None):
    """
    Legacy sync - kept for reference but not used.
    Uses raw spatial context dimensions without scaling.
    """
    map_inst = get_pygame_map()
    if not map_inst or not map_inst.running:
        return
    
    try:
        from spatial_context_system import get_spatial_manager
        spatial = get_spatial_manager(session_id=session_id)
        context = spatial.get_current_context()
        if not context:
            return
        dims = context.location_dimensions
        
        # Update obstacles and detect doors
        door_positions = []
        for obs_id, obstacle in dims.obstacles.items():
            if obstacle.boundary_points:
                cx = sum(p.x for p in obstacle.boundary_points) / len(obstacle.boundary_points)
                cy = sum(p.y for p in obstacle.boundary_points) / len(obstacle.boundary_points)
                
                # Detect obstacle type
                obs_type = obstacle.obstacle_type or ""
                name_lower = obstacle.obstacle_name.lower()
                
                if "door" in name_lower or "entrance" in name_lower or "exit" in name_lower:
                    obs_type = "door"
                    door_positions.append((cx, cy))
                elif "window" in name_lower:
                    obs_type = "window"
                elif any(w in name_lower for w in ["desk", "table", "chair", "bed", "couch", "shelf"]):
                    obs_type = "furniture"
                
                # Calculate size from boundary
                if len(obstacle.boundary_points) >= 2:
                    xs = [p.x for p in obstacle.boundary_points]
                    ys = [p.y for p in obstacle.boundary_points]
                    width = max(xs) - min(xs)
                    height = max(ys) - min(ys)
                else:
                    width, height = 2.0, 2.0
                
                obs = MapObstacle(
                    obstacle_id=obs_id,
                    name=obstacle.obstacle_name,
                    x=cx,
                    y=cy,
                    width=max(1.0, width),
                    height=max(1.0, height),
                    blocks_los=obstacle.blocks_line_of_sight,
                    obstacle_type=obs_type
                )
                map_inst.state.obstacles[obs_id] = obs
        
        # Update zones and auto-number them
        zone_number = 1
        for zone_id, zone in dims.zones.items():
            if zone.boundary_points:
                points = [(p.x, p.y) for p in zone.boundary_points]
                map_zone = MapZone(
                    zone_id=zone_id,
                    name=zone.zone_name,
                    points=points,
                    description=zone.description or "",
                    number=zone_number
                )
                map_inst.state.zones[zone_id] = map_zone
                zone_number += 1
        
        # Generate interior walls from zones
        _generate_walls_from_zones(map_inst, door_positions)
                
    except ImportError:
        print("[WARNING] spatial_context_system not available for sync")
    except Exception as e:
        import traceback
        print(f"[WARNING] Failed to sync pygame map: {e}")
        traceback.print_exc()


def _generate_walls_from_zones(map_inst, door_positions: List[Tuple[float, float]] = None):
    """
    Generate interior walls based on zone boundaries.
    
    Creates walls where zones share edges, with door gaps where doors are detected.
    """
    door_positions = door_positions or []
    zones = list(map_inst.state.zones.values())
    
    if not zones:
        return
    
    # Track all wall segments
    wall_segments = []
    
    for zone in zones:
        if len(zone.points) < 3:
            continue
        
        # Create wall segments for each edge of the zone
        points = zone.points
        for i in range(len(points)):
            p1 = points[i]
            p2 = points[(i + 1) % len(points)]
            
            # Check if this edge is on the outer boundary
            is_outer = _is_outer_edge(p1, p2, map_inst.state.width, map_inst.state.height)
            
            if not is_outer:
                # This is an interior wall
                wall_segments.append((p1, p2, zone.zone_id))
    
    # Deduplicate walls (shared edges between zones)
    unique_walls = {}
    for p1, p2, zone_id in wall_segments:
        # Normalize edge direction for comparison
        edge_key = _normalize_edge(p1, p2)
        
        if edge_key not in unique_walls:
            unique_walls[edge_key] = (p1, p2)
    
    # Create wall objects with door detection
    wall_id = 0
    for edge_key, (p1, p2) in unique_walls.items():
        # Check if there's a door on this wall
        has_door, door_pos = _check_door_on_wall(p1, p2, door_positions)
        
        wall = MapWall(
            wall_id=f"wall_{wall_id}",
            start=p1,
            end=p2,
            has_door=has_door,
            door_position=door_pos
        )
        map_inst.state.walls[f"wall_{wall_id}"] = wall
        wall_id += 1


def _is_outer_edge(p1: Tuple[float, float], p2: Tuple[float, float], 
                   width: float, height: float, tolerance: float = 0.5) -> bool:
    """Check if an edge is on the outer boundary of the map"""
    # Check if both points are on the same outer edge
    on_left = abs(p1[0]) < tolerance and abs(p2[0]) < tolerance
    on_right = abs(p1[0] - width) < tolerance and abs(p2[0] - width) < tolerance
    on_bottom = abs(p1[1]) < tolerance and abs(p2[1]) < tolerance
    on_top = abs(p1[1] - height) < tolerance and abs(p2[1] - height) < tolerance
    
    return on_left or on_right or on_bottom or on_top


def _normalize_edge(p1: Tuple[float, float], p2: Tuple[float, float]) -> tuple:
    """Normalize edge for comparison (smaller point first)"""
    if p1 < p2:
        return (p1, p2)
    return (p2, p1)


def _check_door_on_wall(p1: Tuple[float, float], p2: Tuple[float, float],
                        door_positions: List[Tuple[float, float]],
                        threshold: float = 3.0) -> Tuple[bool, float]:
    """
    Check if any door position is near this wall segment.
    
    Returns (has_door, door_position_ratio)
    """
    if not door_positions:
        return False, 0.5
    
    # Wall vector
    wx = p2[0] - p1[0]
    wy = p2[1] - p1[1]
    wall_len = math.sqrt(wx*wx + wy*wy)
    
    if wall_len < 0.1:
        return False, 0.5
    
    for dx, dy in door_positions:
        # Vector from p1 to door
        vx = dx - p1[0]
        vy = dy - p1[1]
        
        # Project door onto wall line
        t = (vx * wx + vy * wy) / (wall_len * wall_len)
        
        if 0 <= t <= 1:
            # Closest point on wall
            closest_x = p1[0] + t * wx
            closest_y = p1[1] + t * wy
            
            # Distance from door to wall
            dist = math.sqrt((dx - closest_x)**2 + (dy - closest_y)**2)
            
            if dist < threshold:
                return True, t
    
    return False, 0.5


def get_sensing_data_from_map() -> Optional[Dict[str, Any]]:
    """
    Get current sensing bubble data from the map for use in other systems.
    
    Returns dict with:
        - ua_position: (x, y) of the User Actor
        - actors: {actor_id: {"name", "position", "type", "distance_to_ua"}}
        - obstacles: {obs_id: {"name", "position", "type"}}
        - actors_in_vision: list of actor_ids within vision range
        - actors_in_hearing: list of actor_ids within hearing range
        - actors_in_smell: list of actor_ids within smell range
        - actors_in_touch: list of actor_ids within touch range
    
    Example:
        from pygame_spatial_map import get_sensing_data_from_map
        
        sensing = get_sensing_data_from_map()
        if sensing:
            for actor_id in sensing['actors_in_vision']:
                actor = sensing['actors'][actor_id]
                print(f"Can see {actor['name']} at distance {actor['distance_to_ua']:.1f}")
    """
    map_inst = get_pygame_map()
    if not map_inst or not map_inst.running:
        return None
    
    # Find UA
    ua = None
    for actor in map_inst.state.actors.values():
        if actor.actor_type == ActorType.UA:
            ua = actor
            break
    
    if not ua:
        return None
    
    ua_pos = (ua.x, ua.y)
    
    # Calculate distances and categorize by sense range
    actors_data = {}
    in_vision = []
    in_hearing = []
    in_smell = []
    in_touch = []
    
    for actor_id, actor in map_inst.state.actors.items():
        if actor.actor_type == ActorType.UA:
            continue
        
        # Calculate distance
        dx = actor.x - ua.x
        dy = actor.y - ua.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        actors_data[actor_id] = {
            "name": actor.name,
            "position": (actor.x, actor.y),
            "type": actor.actor_type.value,
            "distance_to_ua": distance,
            "occupation": actor.occupation,
            "s_traits": actor.s_trait_outliers
        }
        
        # Categorize by sense range
        if distance <= SensoryRange.VISION:
            in_vision.append(actor_id)
        if distance <= SensoryRange.HEARING:
            in_hearing.append(actor_id)
        if distance <= SensoryRange.SMELL:
            in_smell.append(actor_id)
        if distance <= SensoryRange.TOUCH:
            in_touch.append(actor_id)
    
    # Get obstacles
    obstacles_data = {}
    for obs_id, obs in map_inst.state.obstacles.items():
        dx = obs.x - ua.x
        dy = obs.y - ua.y
        distance = math.sqrt(dx*dx + dy*dy)
        
        obstacles_data[obs_id] = {
            "name": obs.name,
            "position": (obs.x, obs.y),
            "type": obs.obstacle_type,
            "distance_to_ua": distance
        }
    
    return {
        "ua_id": ua.actor_id,
        "ua_position": ua_pos,
        "ua_name": ua.name,
        "actors": actors_data,
        "obstacles": obstacles_data,
        "actors_in_vision": in_vision,
        "actors_in_hearing": in_hearing,
        "actors_in_smell": in_smell,
        "actors_in_touch": in_touch,
        "location_name": map_inst.state.location_name,
        "location_size": (map_inst.state.width, map_inst.state.height)
    }


def get_perceivable_actors_for_narrative() -> str:
    """
    Get a formatted string of what the UA can perceive for LLM prompts.
    
    Returns a narrative-ready description of sensory perceptions.
    """
    sensing = get_sensing_data_from_map()
    if not sensing:
        return ""
    
    parts = []
    
    # Vision
    if sensing['actors_in_vision']:
        visible = []
        for aid in sensing['actors_in_vision']:
            a = sensing['actors'][aid]
            dist = a['distance_to_ua']
            if dist <= 20:
                visible.append(f"{a['name']} (clearly visible, {dist:.0f} units)")
            elif dist <= 50:
                visible.append(f"{a['name']} (visible, {dist:.0f} units)")
            else:
                visible.append(f"{a['name']} (distant, {dist:.0f} units)")
        parts.append(f"VISIBLE: {', '.join(visible)}")
    
    # Hearing (only those NOT in vision, or very close)
    heard_only = [aid for aid in sensing['actors_in_hearing'] 
                  if aid not in sensing['actors_in_vision']]
    if heard_only:
        audible = [f"{sensing['actors'][aid]['name']}" for aid in heard_only]
        parts.append(f"HEARD (not seen): {', '.join(audible)}")
    
    # Touch range
    if sensing['actors_in_touch']:
        touching = [sensing['actors'][aid]['name'] for aid in sensing['actors_in_touch']]
        parts.append(f"WITHIN REACH: {', '.join(touching)}")
    
    return "\n".join(parts) if parts else "No one nearby."


def init_pygame_map_for_simulation(zone_names: List[str], width: float = 0.0, 
                                    height: float = 0.0, location_name: str = "Location",
                                    location_type: str = "interior") -> bool:
    """
    Initialize the pygame map for a simulation location.
    
    Call this when entering a new location. The map runs in a background thread.
    
    Args:
        zone_names: List of zone/room names (e.g., ["Entrance", "Kitchen", "Office"])
        width: Location width in units (default 250)
        height: Location height in units (default 200)
        location_name: Display name for the location
        location_type: Type of location ("interior", "exterior", "warehouse", etc.)
    
    Returns:
        True if map started successfully
    
    Example:
        from pygame_spatial_map import (
            init_pygame_map_for_simulation,
            update_map_actor,
            stop_pygame_map
        )
        
        # Start map when entering location
        init_pygame_map_for_simulation(
            zone_names=["Lobby", "Kitchen", "Dining Area"],
            width=DEFAULT_MAP_WIDTH, height=DEFAULT_MAP_HEIGHT,
            location_name="Joe's Diner"
        )
        
        # Update actor positions during simulation
        update_map_actor("ua_001", "Petra", 100, 50, "ua")
        update_map_actor("nua_001", "Waitress", 150, 80, "nua")
        
        # Stop when exiting
        stop_pygame_map()
    """
    try:
        if float(width or 0.0) <= 0.0 or float(height or 0.0) <= 0.0:
            width, height = LocationScale.get_scale(location_type or "interior")

        # Try LLM-based layout generator first (better spatial understanding)
        try:
            from llm_layout_generator import generate_layout_for_location_llm
            use_llm = True
        except ImportError:
            from layout_generator import generate_layout_for_location
            use_llm = False
        
        # Start the map window (runs in background thread)
        if not start_pygame_map():
            return False
        
        # Generate layout from zone names
        if use_llm:
            layout = generate_layout_for_location_llm(
                zone_names=zone_names,
                width=width,
                height=height,
                location_type=location_type,
                location_name=location_name,
                scene_description=""  # Will be built from zone names
            )
            print(f"[PMAP] Using LLM layout generator for '{location_name}'")
        else:
            layout = generate_layout_for_location(
                zone_names=zone_names,
                width=width,
                height=height,
                location_type=location_type
            )
        
        # Apply layout
        apply_generated_layout(layout)
        # Ensure the visible map uses the requested authoritative dimensions
        map_inst = get_pygame_map()
        if map_inst:
            map_inst.state.width = float(width)
            map_inst.state.height = float(height)
        
        # Set location name
        if map_inst:
            map_inst.state.location_name = location_name
            map_inst.state.location_type = location_type
        
        return True
        
    except Exception as e:
        print(f"[WARNING] Failed to init pygame map: {e}")
        return False


def apply_generated_layout(layout, map_inst=None):
    """
    Apply a GeneratedLayout to the pygame map.
    
    Args:
        layout: GeneratedLayout from layout_generator
        map_inst: PygameSpatialMap instance (uses global if None)
    """
    if map_inst is None:
        map_inst = get_pygame_map()
    
    if not map_inst:
        return
    
    # Clear existing
    map_inst.state.zones.clear()
    map_inst.state.walls.clear()
    map_inst.state.obstacles.clear()
    map_inst.state.rooms.clear()
    
    # Set dimensions and grid size
    try:
        cur_w = float(getattr(map_inst.state, 'width', 0.0) or 0.0)
        cur_h = float(getattr(map_inst.state, 'height', 0.0) or 0.0)
    except Exception:
        cur_w, cur_h = 0.0, 0.0
    if cur_w <= 0 or cur_h <= 0:
        map_inst.state.width = layout.width
        map_inst.state.height = layout.height
    map_inst.state.grid_size = 10.0  # 10 unit grid (talk distance)

    # If the generated layout coordinate space differs from the authoritative map size,
    # scale layout geometry into the authoritative space so rooms/walls don't become a tiny
    # inset box (common on wagons/small interiors).
    try:
        target_w = float(getattr(map_inst.state, 'width', 0.0) or 0.0)
        target_h = float(getattr(map_inst.state, 'height', 0.0) or 0.0)
        src_w = float(getattr(layout, 'width', 0.0) or 0.0)
        src_h = float(getattr(layout, 'height', 0.0) or 0.0)
    except Exception:
        target_w, target_h, src_w, src_h = 0.0, 0.0, 0.0, 0.0

    scale_x = 1.0
    scale_y = 1.0
    # Detect true extents of geometry (rooms/walls/obstacles) since some generators
    # can emit objects outside layout.width/layout.height.
    try:
        max_x = src_w
        max_y = src_h
        for r in (getattr(layout, 'rooms', {}) or {}).values():
            rx = float(getattr(r, 'x', 0.0) or 0.0)
            ry = float(getattr(r, 'y', 0.0) or 0.0)
            rw = float(getattr(r, 'width', 0.0) or 0.0)
            rh = float(getattr(r, 'height', 0.0) or 0.0)
            max_x = max(max_x, rx + rw)
            max_y = max(max_y, ry + rh)
        for w in getattr(layout, 'walls', []) or []:
            try:
                max_x = max(max_x, float(w.start[0]), float(w.end[0]))
                max_y = max(max_y, float(w.start[1]), float(w.end[1]))
            except Exception:
                pass
        for o in getattr(layout, 'obstacles', []) or []:
            ox = float(getattr(o, 'x', 0.0) or 0.0)
            oy = float(getattr(o, 'y', 0.0) or 0.0)
            ow = float(getattr(o, 'width', 0.0) or 0.0)
            oh = float(getattr(o, 'height', 0.0) or 0.0)
            max_x = max(max_x, ox + (ow / 2.0))
            max_y = max(max_y, oy + (oh / 2.0))
        src_w = max(src_w, max_x)
        src_h = max(src_h, max_y)
    except Exception:
        pass

    if target_w > 0.0 and target_h > 0.0 and src_w > 0.0 and src_h > 0.0:
        sx = target_w / src_w
        sy = target_h / src_h
        if abs(sx - 1.0) > 0.05 or abs(sy - 1.0) > 0.05:
            scale_x = sx
            scale_y = sy

    try:
        lname = str(getattr(map_inst.state, 'location_name', '') or '').lower()
        ltype = str(getattr(map_inst.state, 'location_type', '') or '').lower()
    except Exception:
        lname, ltype = '', ''

    # Only treat PUBLIC TRANSPORT (or large transport) as eligible to be a location interior.
    # Land vehicles like cars/wagons/carts are not locations; they can exist within locations.
    vehicle_name_keys = [
        "boat", "ship", "ferry", "barge", "skiff", "canoe",
        "train", "rail", "railcar", "bus",
        "plane", "aircraft",
    ]
    vehicle_type_keys = [
        "boat", "ship", "ferry", "barge",
        "train", "rail", "railcar", "bus",
        "plane", "aircraft",
    ]

    # Only treat the CURRENT LOCATION as a vehicle interior when it's clearly the inside of a vehicle.
    # Avoid triggering when a vehicle is merely present in a normal location (garage, depot, dock, station, etc.).
    exclusion_place_keys = [
        "garage", "parking", "lot", "depot", "station", "platform", "yard",
        "dock", "port", "harbor", "terminal", "hangar", "warehouse",
    ]
    interior_hint_keys = [
        "interior", "inside", "cabin", "cockpit", "hold", "berth", "compartment",
        "railcar",
    ]

    name_has_vehicle = any(k in lname for k in vehicle_name_keys)
    type_is_vehicle = any(k in ltype for k in vehicle_type_keys)
    name_has_exclusion_place = any(k in lname for k in exclusion_place_keys)
    name_has_interior_hint = any(k in lname for k in interior_hint_keys)

    # Strong public transport types: if the location_type is one of these, it's intended to be the interior.
    type_is_strong_vehicle = any(k in ltype for k in [
        "railcar", "train", "bus",
        "boat", "ship", "ferry", "barge",
        "plane", "aircraft",
    ])

    # Name-based matching requires an explicit interior hint ("cabin", "inside", etc.)
    # so a vehicle mentioned as a prop doesn't become a location.
    is_vehicle_like = (
        type_is_strong_vehicle
        or ((name_has_vehicle and not name_has_exclusion_place) and name_has_interior_hint)
    )
    vehicle_single_room = is_vehicle_like and (len(getattr(layout, 'rooms', {}) or {}) <= 1)
    
    # Add rooms as zones
    zone_num = 1
    for room_id, room in layout.rooms.items():
        # Layout generators are treated as using the same world coordinate orientation as the map.
        # Only obstacle center conversion is applied elsewhere.
        try:
            room_poly = list(getattr(room, 'polygon', None) or [])
        except Exception:
            room_poly = []

        if room_poly:
            try:
                room_poly = [(float(px) * scale_x, float(py) * scale_y) for (px, py) in room_poly]
            except Exception:
                pass

        zone = MapZone(
            zone_id=room_id,
            name=room.name,
            points=room_poly if room_poly else room.polygon,
            number=zone_num
        )
        map_inst.state.zones[room_id] = zone

        # Keep a room record as authoritative bounds for obstacle/actor placement.
        # Use whatever geometry the layout provides.
        try:
            rx = float(getattr(room, 'x', 0.0) or 0.0)
            ry = float(getattr(room, 'y', 0.0) or 0.0)
            rw = float(getattr(room, 'width', 0.0) or 0.0)
            rh = float(getattr(room, 'height', 0.0) or 0.0)
        except Exception:
            rx, ry, rw, rh = 0.0, 0.0, 0.0, 0.0

        if rw > 0.0 and rh > 0.0:
            rx *= scale_x
            ry *= scale_y
            rw *= scale_x
            rh *= scale_y

            if vehicle_single_room:
                margin = max(0.75, min(target_w, target_h) * 0.06)
                rx = margin
                ry = margin
                rw = max(1.0, target_w - (2 * margin))
                rh = max(1.0, target_h - (2 * margin))

            map_inst.state.rooms[room_id] = MapRoom(
                room_id=room_id,
                name=room.name,
                number=zone_num,
                bounds=(rx, ry, rw, rh),
            )
        zone_num += 1
    
    # Add walls
    if not vehicle_single_room:
        for wall in layout.walls:
            try:
                start = (float(wall.start[0]) * scale_x, float(wall.start[1]) * scale_y)
                end = (float(wall.end[0]) * scale_x, float(wall.end[1]) * scale_y)
            except Exception:
                start = wall.start
                end = wall.end
            map_wall = MapWall(
                wall_id=wall.wall_id,
                start=start,
                end=end,
                has_door=wall.has_door,
                door_position=wall.door_position
            )
            map_inst.state.walls[wall.wall_id] = map_wall

    # If the LLM already emitted a door/exit as an obstacle, don't also create a wall-derived door.
    # Otherwise the map shows duplicated exits.
    has_llm_door_obstacle = False
    try:
        for o in getattr(layout, 'obstacles', []) or []:
            otyp = str(getattr(o, 'obstacle_type', '') or '').lower()
            oname = str(getattr(o, 'name', '') or '').lower()
            if otyp in ["door", "exit", "entrance", "portal"] or any(k in oname for k in ["door", "exit", "entrance", "gate", "hatch", "trapdoor"]):
                has_llm_door_obstacle = True
                break
    except Exception:
        has_llm_door_obstacle = False

    if not vehicle_single_room and not has_llm_door_obstacle:
        for wall in layout.walls:
            if not getattr(wall, 'has_door', False):
                continue

            start = getattr(wall, 'start', None)
            end = getattr(wall, 'end', None)
            door_pos = float(getattr(wall, 'door_position', 0.5))
            if not start or not end:
                continue

            dx = (float(end[0]) - float(start[0])) * scale_x
            dy = (float(end[1]) - float(start[1])) * scale_y
            door_x = (float(start[0]) * scale_x) + dx * door_pos
            door_y = (float(start[1]) * scale_y) + dy * door_pos

            raw_to = str(getattr(wall, 'room_b', '') or '').strip()
            dest_key = raw_to if raw_to else "outside"
            door_name = "Exit" if dest_key == "outside" else "Door"

            door_id = f"door_{str(getattr(wall, 'wall_id', '') or '')}"
            door_id = door_id.lower().replace(" ", "_").replace("'", "")[:30]
            if not door_id or door_id in map_inst.state.obstacles:
                continue

            door_w = 6.0
            door_h = 4.0
            door_x = max(door_w / 2, min(target_w - door_w / 2, door_x))
            door_y = max(door_h / 2, min(target_h - door_h / 2, door_y))

            map_inst.state.obstacles[door_id] = MapObstacle(
                obstacle_id=door_id,
                name=door_name,
                x=door_x,
                y=door_y,
                width=door_w,
                height=door_h,
                blocks_los=False,
                obstacle_type="door"
            )

    # Wagon-like single-room locations: rely on the outer boundary walls and ensure a default exit.
    if vehicle_single_room:
        has_any_door = any((o.obstacle_type == "door" or (o.name or "").lower() in ["door", "exit"]) for o in map_inst.state.obstacles.values())
        if not has_any_door:
            door_id = "door_vehicle"
            door_w = 2.2
            door_h = 1.2
            door_x = float(target_w) * 0.50
            door_y = max(door_h / 2, min(float(target_h) - door_h / 2, float(target_h) - 1.0))
            map_inst.state.obstacles[door_id] = MapObstacle(
                obstacle_id=door_id,
                name="Exit",
                x=door_x,
                y=door_y,
                width=door_w,
                height=door_h,
                blocks_los=False,
                obstacle_type="door",
            )
    
    # Add obstacles/furniture
    if hasattr(layout, 'obstacles'):
        for obs in layout.obstacles:
            # Clamp obstacle sizes/positions to current layout bounds.
            # This avoids huge furniture in tiny maps collapsing into a corner.
            obs_type = str(getattr(obs, 'obstacle_type', '') or 'furniture').lower()
            name_lower = str(getattr(obs, 'name', '') or '').lower()

            frac_w = 0.30
            frac_h = 0.30
            if obs_type in ["debris", "rubble"] or any(k in name_lower for k in ["bone", "bones", "rubble", "debris", "wreckage", "blocks", "collapsed"]):
                frac_w = 0.22
                frac_h = 0.22

            # Scale obstacle geometry to the authoritative target size (same approach as rooms/walls).
            try:
                sx = float(scale_x)
                sy = float(scale_y)
            except Exception:
                sx, sy = 1.0, 1.0

            raw_w = float(getattr(obs, 'width', 0.0) or 0.0) * sx
            raw_h = float(getattr(obs, 'height', 0.0) or 0.0) * sy
            raw_x = float(getattr(obs, 'x', 0.0) or 0.0) * sx
            raw_y = float(getattr(obs, 'y', 0.0) or 0.0) * sy

            max_w = max(0.5, float(target_w) * frac_w)
            max_h = max(0.5, float(target_h) * frac_h)
            w = min(raw_w, max_w)
            h = min(raw_h, max_h)

            # Layout obstacles use top-left coords; map obstacles use centers.
            cx = raw_x + (w / 2.0)
            cy = raw_y + (h / 2.0)
            x = _clamp_1d(cx, w / 2.0, float(target_w) - (w / 2.0))
            y = _clamp_1d(cy, h / 2.0, float(target_h) - (h / 2.0))
            map_obs = MapObstacle(
                obstacle_id=obs.obstacle_id,
                name=obs.name,
                x=x,
                y=y,
                width=w,
                height=h,
                obstacle_type=obs.obstacle_type
            )
            map_inst.state.obstacles[obs.obstacle_id] = map_obs


# ═══════════════════════════════════════════════════════════════════════════════
# CONTEXT-BASED ZOOM AND ACTOR DETAILS
# ═══════════════════════════════════════════════════════════════════════════════

def set_map_context(context: str):
    """
    Set the current context mode for auto-zoom.
    
    Args:
        context: One of "combat", "stealth", "social", "exploration", "travel"
    """
    map_inst = get_pygame_map()
    if not map_inst:
        return
    
    map_inst.state.current_context = context.lower()
    
    # Apply context-based zoom if enabled
    if map_inst.state.auto_zoom_enabled:
        zoom_mult = LocationScale.get_context_zoom(context)
        map_inst.zoom = zoom_mult
        map_inst._auto_fit_view()
        print(f"[PMAP] Context set to '{context}' (zoom: {zoom_mult}x)")


def get_actor_details(actor_id: str) -> Optional[Dict[str, Any]]:
    """
    Get detailed information about an actor for display.
    
    Returns dict with position, trail info, distances, etc.
    """
    map_inst = get_pygame_map()
    if not map_inst or actor_id not in map_inst.state.actors:
        return None
    
    actor = map_inst.state.actors[actor_id]
    
    # Calculate trail info
    trail_points = [(p[0], p[1]) for p in actor.trail]
    trail_distance = 0.0
    if len(trail_points) >= 1:
        points = trail_points + [(actor.x, actor.y)]
        for i in range(len(points) - 1):
            dx = points[i+1][0] - points[i][0]
            dy = points[i+1][1] - points[i][1]
            trail_distance += math.sqrt(dx*dx + dy*dy)
    
    straight_distance = 0.0
    if trail_points:
        dx = actor.x - trail_points[0][0]
        dy = actor.y - trail_points[0][1]
        straight_distance = math.sqrt(dx*dx + dy*dy)
    
    return {
        "actor_id": actor.actor_id,
        "name": actor.name,
        "type": actor.actor_type.value,
        "position": {"x": actor.x, "y": actor.y},
        "facing": actor.facing_direction,
        "trail_distance": trail_distance,
        "straight_distance": straight_distance,
        "average_speed": actor.average_speed,
        "occupation": actor.occupation,
        "s_trait_outliers": actor.s_trait_outliers,
        "trail_points": len(actor.trail)
    }


def get_map_data_for_rag() -> Dict[str, Any]:
    """
    Get map data formatted for RAG/narrative system integration.
    
    Returns comprehensive map state for context injection.
    """
    map_inst = get_pygame_map()
    if not map_inst:
        return {}
    
    state = map_inst.state
    
    # Collect actor data
    actors_data = {}
    for actor_id, actor in state.actors.items():
        actors_data[actor_id] = {
            "name": actor.name,
            "type": actor.actor_type.value,
            "x": actor.x,
            "y": actor.y,
            "facing": actor.facing_direction,
            "trail_distance": actor.trail_distance,
            "speed": actor.average_speed
        }
    
    # Collect obstacle data
    obstacles_data = {}
    for obs_id, obs in state.obstacles.items():
        obstacles_data[obs_id] = {
            "name": obs.name,
            "type": obs.obstacle_type,
            "x": obs.x,
            "y": obs.y,
            "width": obs.width,
            "height": obs.height
        }
    
    # Calculate distances between actors
    distances = {}
    actor_ids = list(state.actors.keys())
    for i, id1 in enumerate(actor_ids):
        for id2 in actor_ids[i+1:]:
            a1, a2 = state.actors[id1], state.actors[id2]
            dist = math.sqrt((a1.x - a2.x)**2 + (a1.y - a2.y)**2)
            distances[f"{id1}_{id2}"] = {
                "actor1": a1.name,
                "actor2": a2.name,
                "distance": dist
            }
    
    return {
        "location_name": state.location_name,
        "location_type": state.location_type,
        "dimensions": {"width": state.width, "height": state.height},
        "context": state.current_context,
        "actors": actors_data,
        "obstacles": obstacles_data,
        "actor_distances": distances,
        "zone_count": len(state.zones),
        "is_geographic": state.is_geographic
    }


def get_obstacle_names_for_narrative() -> str:
    """
    Get a formatted list of obstacle names for narrative context.
    
    This allows the narrator/LLM to know what objects exist in the scene
    so it can reference them appropriately.
    
    Returns:
        A string like "Objects in this location: Potted Plant, Desk Lamp, Filing Cabinet, ..."
    """
    map_inst = get_pygame_map()
    if not map_inst or not map_inst.state.obstacles:
        return ""
    
    # Get unique obstacle names
    obstacle_names = []
    for obs in map_inst.state.obstacles.values():
        if obs.name and obs.name not in obstacle_names:
            obstacle_names.append(obs.name)
    
    if not obstacle_names:
        return ""
    
    # Format as a readable list
    return f"Objects/furniture in this location: {', '.join(obstacle_names)}"


def get_nearby_obstacles(actor_id: str = "ua_001", radius: float = 30.0) -> List[str]:
    """
    Get names of obstacles near a specific actor.
    
    Args:
        actor_id: The actor to check proximity for
        radius: Distance threshold in map units
        
    Returns:
        List of obstacle names within radius
    """
    map_inst = get_pygame_map()
    if not map_inst:
        return []
    
    # Find actor position
    actor = map_inst.state.actors.get(actor_id)
    if not actor:
        return []
    
    nearby = []
    for obs in map_inst.state.obstacles.values():
        # Calculate distance from actor to obstacle center
        dist = ((actor.x - obs.x)**2 + (actor.y - obs.y)**2)**0.5
        if dist <= radius:
            nearby.append(obs.name)
    
    return nearby


def toggle_auto_zoom(enabled: bool = None):
    """Toggle or set auto-zoom behavior"""
    map_inst = get_pygame_map()
    if not map_inst:
        return
    
    if enabled is None:
        map_inst.state.auto_zoom_enabled = not map_inst.state.auto_zoom_enabled
    else:
        map_inst.state.auto_zoom_enabled = enabled
    
    print(f"[PMAP] Auto-zoom: {'enabled' if map_inst.state.auto_zoom_enabled else 'disabled'}")


def toggle_follow_ua(enabled: bool = None):
    """Toggle or set UA following behavior"""
    map_inst = get_pygame_map()
    if not map_inst:
        return
    
    if enabled is None:
        map_inst.state.follow_ua = not map_inst.state.follow_ua
    else:
        map_inst.state.follow_ua = enabled
    
    print(f"[PMAP] Follow UA: {'enabled' if map_inst.state.follow_ua else 'disabled'}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST - Dynamic Dungeon Style Map
# ═══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    if not PYGAME_AVAILABLE:
        print("Pygame not installed. Run: pip install pygame")
        exit(1)
    
    print("Starting Pygame Dungeon-Style Map test...")
    print("Using dynamic layout generator...")
    
    # Import layout generator
    try:
        from layout_generator import generate_layout_for_location
        HAS_LAYOUT_GEN = True
    except ImportError:
        HAS_LAYOUT_GEN = False
        print("[WARNING] layout_generator not found, using static layout")
    
    # Start map
    if start_pygame_map():
        print("Map window started!")
        
        map_inst = get_pygame_map()
        
        if HAS_LAYOUT_GEN:
            # DYNAMIC LAYOUT - Generated from zone names
            # Scale based on sensory units:
            # - Vision = 250 units, so building should be ~200-300 units
            # - Room = ~40-60 units (can shout across at 50 units)
            # - Talk = 10 units, Touch = 2 units
            zone_names = ["Entrance Hall", "Main Corridor", "Storage Room", 
                         "Office", "Break Room"]
            
            layout = generate_layout_for_location(
                zone_names=zone_names,
                width=int(LocationScale.get_scale("warehouse")[0]),
                height=int(LocationScale.get_scale("warehouse")[1]),
                location_type="warehouse",
                seed=42  # For reproducibility in test
            )
            
            apply_generated_layout(layout, map_inst)
            map_inst.state.location_name = "Abandoned Warehouse (Dynamic)"
            
            print(f"Generated {len(layout.rooms)} rooms with {len(layout.walls)} walls")
        else:
            # STATIC FALLBACK - Hardcoded layout (250x200 scale)
            map_inst.state.location_name = "Abandoned Warehouse (Static)"
            w, h = LocationScale.get_scale("warehouse")
            map_inst.state.width = w
            map_inst.state.height = h
            map_inst.state.grid_size = 10.0  # 10 unit grid squares
            map_inst.state.wall_thickness = 4
            
            # Static fallback rooms (~50-80 units each)
            map_inst.state.zones["room_1"] = MapZone(
                zone_id="room_1", name="Entrance Hall",
                points=[(150, 0), (250, 0), (250, 100), (150, 100)], number=1
            )
            map_inst.state.zones["room_2"] = MapZone(
                zone_id="room_2", name="Corridor",
                points=[(70, 30), (150, 30), (150, 120), (70, 120)], number=2
            )
            map_inst.state.zones["room_3"] = MapZone(
                zone_id="room_3", name="Storage",
                points=[(90, 120), (180, 120), (180, 200), (90, 200)], number=3
            )
            map_inst.state.zones["room_4"] = MapZone(
                zone_id="room_4", name="Office",
                points=[(0, 100), (70, 100), (70, 180), (0, 180)], number=4
            )
            map_inst.state.zones["room_5"] = MapZone(
                zone_id="room_5", name="Break Room",
                points=[(0, 0), (70, 0), (70, 80), (0, 80)], number=5
            )
            
            # Static walls
            map_inst.state.walls["wall_1"] = MapWall(
                wall_id="wall_1", start=(70, 0), end=(70, 80), has_door=True
            )
            map_inst.state.walls["wall_2"] = MapWall(
                wall_id="wall_2", start=(70, 100), end=(70, 180), has_door=True
            )
        
        # Add test actors (positions for 250x200 map)
        # Entrance Hall area
        w = float(getattr(map_inst.state, 'width', 0.0) or 0.0)
        h = float(getattr(map_inst.state, 'height', 0.0) or 0.0)
        update_map_actor("ua_001", "Petra Weber", w * 0.8, h * 0.25, "ua", ["Sturdy", "Quick"])
        # Corridor
        update_map_actor("nua_001", "Guard", w * 0.44, h * 0.38, "nua", ["Intimidating"], "Security")
        # Storage
        update_map_actor("nua_002", "Worker", w * 0.54, h * 0.8, "nua", [], "Laborer")
        # Office
        update_map_actor("mnua_001", "Foreman Krause", w * 0.14, h * 0.7, "mnua", ["Sharp-eyed", "Gruff"], "Foreman")
        
        print("Dungeon-style map created!")
        print("Controls:")
        print("  Scroll: Zoom | Middle-drag: Pan | Right-click: Reset")
        print("  G: Toggle Grid | Z: Toggle Zones | R: Reset View")
        print("  Click: Select actor | ESC: Deselect")
        print("\nClose the window to exit.")
        
        # Keep running until window is closed
        try:
            while get_pygame_map() and get_pygame_map().running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            pass
        
        stop_pygame_map()
        print("Map closed.")
    else:
        print("Failed to start map window.")
