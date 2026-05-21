"""
Initiative System for Location-Based Turn Order

Provides simple initiative rolling for when the UA enters a new location
with NPCs present. Establishes turn order for potential interactions.

Initiative is rolled ONCE when entering a location and persists until:
- Leaving the location
- An encounter starts (encounter has its own initiative)
- A significant event resets initiative
"""

import random
from typing import List, Tuple, Optional, Dict, Any
from actors import Actor, UserActor, NonUserActor
from actor_sheet import SFactorType, StatusType
from color_utils import Color


# UTAS Serendipity Table (2d6 -> modifier)
UTAS_SERENDIPITY_TABLE = {
    2: -5, 3: -4, 4: -3, 5: -2, 6: -1,
    7: 0, 8: 1, 9: 2, 10: 3, 11: 4, 12: 5
}


class LocationInitiativeTracker:
    """
    Tracks initiative order for the current location.
    Initiative is rolled once when entering and persists until leaving.
    """
    
    def __init__(self):
        self.current_location: Optional[str] = None
        self.turn_order: List[Dict[str, Any]] = []  # [{'actor': Actor, 'score': int, 'is_user': bool}]
        self.ua_position: int = 0  # Index of UA in turn order
        
    def set_location_initiative(self, location: str, ua: UserActor, npcs: List[NonUserActor]) -> List[Dict[str, Any]]:
        """
        Roll and store initiative for a new location.
        
        Args:
            location: Name of the location
            ua: The User Actor
            npcs: List of NPCs at this location
            
        Returns:
            The turn order list
        """
        self.current_location = location
        self.turn_order = []
        
        if not npcs:
            # Just UA
            self.turn_order = [{'actor': ua, 'score': 100, 'is_user': True, 'name': ua.sheet.name}]
            self.ua_position = 0
            return self.turn_order
        
        # Roll for all actors
        all_actors = [ua] + list(npcs)
        results = []
        
        for actor in all_actors:
            score, breakdown = calculate_actor_initiative(actor)
            results.append({
                'actor': actor,
                'score': score,
                'is_user': isinstance(actor, UserActor),
                'name': actor.sheet.name,
                'breakdown': breakdown
            })
        
        # Sort by score (highest first)
        self.turn_order = sorted(results, key=lambda x: x['score'], reverse=True)
        
        # Find UA position
        for i, entry in enumerate(self.turn_order):
            if entry['is_user']:
                self.ua_position = i
                break
        
        return self.turn_order
    
    def get_turn_order(self) -> List[Dict[str, Any]]:
        """Get the current turn order."""
        return self.turn_order
    
    def get_pre_ua_actors(self) -> List[Dict[str, Any]]:
        """Get actors who act BEFORE the UA (higher initiative)."""
        return self.turn_order[:self.ua_position]
    
    def get_post_ua_actors(self) -> List[Dict[str, Any]]:
        """Get actors who act AFTER the UA (lower initiative)."""
        return self.turn_order[self.ua_position + 1:]
    
    def clear(self):
        """Clear the current initiative (e.g., when leaving location)."""
        self.current_location = None
        self.turn_order = []
        self.ua_position = 0
    
    def has_initiative(self) -> bool:
        """Check if initiative has been rolled for current location."""
        return len(self.turn_order) > 0
    
    def add_actor(self, actor: NonUserActor):
        """Add a new actor to the turn order (e.g., someone arrives)."""
        if not self.turn_order:
            return
            
        score, breakdown = calculate_actor_initiative(actor)
        new_entry = {
            'actor': actor,
            'score': score,
            'is_user': False,
            'name': actor.sheet.name,
            'breakdown': breakdown
        }
        
        # Insert in correct position
        inserted = False
        for i, entry in enumerate(self.turn_order):
            if score > entry['score']:
                self.turn_order.insert(i, new_entry)
                inserted = True
                # Update UA position if needed
                if i <= self.ua_position:
                    self.ua_position += 1
                break
        
        if not inserted:
            self.turn_order.append(new_entry)
        
        print(f"{Color.SYSTEM}[INITIATIVE] {actor.sheet.name} joins the scene (Initiative: {score}){Color.RESET}")
    
    def remove_actor(self, actor_name: str):
        """Remove an actor from the turn order (e.g., someone leaves)."""
        for i, entry in enumerate(self.turn_order):
            if entry['name'] == actor_name:
                self.turn_order.pop(i)
                # Update UA position if needed
                if i < self.ua_position:
                    self.ua_position -= 1
                print(f"{Color.SYSTEM}[INITIATIVE] {actor_name} leaves the scene{Color.RESET}")
                break


# Global instance for location initiative tracking
_location_initiative_tracker: Optional[LocationInitiativeTracker] = None


def get_location_initiative_tracker() -> LocationInitiativeTracker:
    """Get or create the global location initiative tracker."""
    global _location_initiative_tracker
    if _location_initiative_tracker is None:
        _location_initiative_tracker = LocationInitiativeTracker()
    return _location_initiative_tracker


def roll_serendipity() -> Tuple[int, str]:
    """
    Rolls 2d6 and uses UTAS table lookup to get Serendipity score from -5 to +5.
    Returns (result, detailed_roll_string)
    """
    die1 = random.randint(1, 6)
    die2 = random.randint(1, 6)
    total = die1 + die2
    
    serendipity = UTAS_SERENDIPITY_TABLE[total]
    detail = f"2d6({die1}+{die2}={total})→{serendipity:+d}"
    return serendipity, detail


def calculate_actor_initiative(actor: Actor) -> Tuple[int, dict]:
    """
    Calculate initiative for a single actor.
    
    Initiative = Swiftness + Status Modifier + Serendipity
    
    Status Modifier = (Stamina + Spirit) // 2
    
    Returns:
        Tuple of (total_initiative, breakdown_dict)
    """
    # Get base Swiftness
    swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
    
    # Get current status values
    stamina = actor.sheet.statuses[StatusType.STAMINA].value
    spirit = actor.sheet.statuses[StatusType.SPIRIT].value
    
    # Calculate status modifier (average of Stamina and Spirit)
    status_modifier = (stamina + spirit) // 2
    
    # Roll serendipity
    serendipity, serendipity_detail = roll_serendipity()
    
    # Calculate total
    total = swiftness + status_modifier + serendipity
    
    breakdown = {
        'swiftness': swiftness,
        'status_modifier': status_modifier,
        'stamina': stamina,
        'spirit': spirit,
        'serendipity': serendipity,
        'serendipity_detail': serendipity_detail,
        'total': total
    }
    
    return total, breakdown


def roll_location_initiative(ua: UserActor, npcs: List[NonUserActor]) -> List[Tuple[str, int]]:
    """
    Roll initiative for the UA and all NPCs at a location.
    
    Args:
        ua: The User Actor
        npcs: List of Non-User Actors present at the location
        
    Returns:
        List of (actor_name, initiative_roll) tuples, sorted by initiative (highest first)
    """
    if not npcs:
        return []
    
    initiative_results = []
    
    # Roll for UA
    ua_init, ua_breakdown = calculate_actor_initiative(ua)
    initiative_results.append((ua.sheet.name, ua_init, ua_breakdown))
    
    # Roll for each NPC
    for npc in npcs:
        try:
            npc_init, npc_breakdown = calculate_actor_initiative(npc)
            initiative_results.append((npc.sheet.name, npc_init, npc_breakdown))
        except Exception as e:
            # If we can't calculate initiative for an NPC, give them a default
            print(f"{Color.WARNING}[INITIATIVE] Could not calculate for {npc.sheet.name}: {e}{Color.RESET}")
            initiative_results.append((npc.sheet.name, 5, {'error': str(e)}))
    
    # Sort by initiative (highest first)
    initiative_results.sort(key=lambda x: x[1], reverse=True)
    
    # Return simplified list (name, roll) for display
    return [(name, roll) for name, roll, _ in initiative_results]


def get_initiative_order_display(initiative_order: List[Tuple[str, int]], ua_name: str) -> str:
    """
    Format initiative order for display.
    
    Args:
        initiative_order: List of (actor_name, initiative_roll) tuples
        ua_name: Name of the User Actor (to mark with arrow)
        
    Returns:
        Formatted string for display
    """
    lines = ["Turn Order:"]
    for i, (name, roll) in enumerate(initiative_order, 1):
        marker = "→" if name == ua_name else " "
        lines.append(f"  {marker} {i}. {name} (Initiative: {roll})")
    return "\n".join(lines)
