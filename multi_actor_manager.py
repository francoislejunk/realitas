"""
Multi-Actor Management System for UTAS Simulation

This system enables the simulation to handle an infinite number of actors
by providing scalable storage, retrieval, and management capabilities.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import uuid
from actors import UserActor, NonUserActor, InanimateNonUserActor, Actor
from actor_sheet import ActorSheet, StatusType
from color_utils import Color


class ActorRole(Enum):
    """Defines the different roles actors can have in the simulation."""
    USER = "user"           # The player character
    SCENE_PRIMARY = "scene_primary"    # Main NUA/INUA for current scene
    SCENE_SECONDARY = "scene_secondary"  # Additional actors in scene
    BACKGROUND = "background"          # Actors mentioned but not active
    INACTIVE = "inactive"             # Actors not currently in scene


def _safe_display_name(actor: Actor) -> str:
    try:
        nm = getattr(getattr(actor, 'sheet', None), 'name', None)
        if not nm:
            return str(actor)
        try:
            if getattr(getattr(actor, 'sheet', None), 'is_user_actor', False):
                return str(nm)
        except Exception:
            pass

        name_is_known = False
        try:
            from stranger_description_system import known_actors_tracker
            if known_actors_tracker is not None and known_actors_tracker.is_name_known(str(nm)):
                name_is_known = True
        except Exception:
            name_is_known = False

        try:
            if name_is_known:
                base = str(nm)
                occ = str(getattr(getattr(actor, 'sheet', None), 'occupation', '') or '').strip()
                if occ and occ.lower() not in base.lower():
                    return f"{base} ({occ})"
                return base
        except Exception:
            pass
        ka = getattr(getattr(actor, 'sheet', None), 'known_as', None)
        if ka:
            try:
                if isinstance(ka, (list, tuple, set)):
                    for item in ka:
                        s = str(item or '').strip()
                        if s:
                            if not name_is_known:
                                return s
                            base = str(nm)
                            if base and s.lower() not in base.lower():
                                return f"{base} ({s})"
                            return base or s
                    joined = ", ".join([str(x).strip() for x in ka if str(x or '').strip()])
                    if joined:
                        if not name_is_known:
                            return joined
                        base = str(nm)
                        if base and joined.lower() not in base.lower():
                            return f"{base} ({joined})"
                        return base or joined
                else:
                    s = str(ka).strip()
                    if s:
                        if not name_is_known:
                            return s
                        base = str(nm)
                        if base and s.lower() not in base.lower():
                            return f"{base} ({s})"
                        return base or s
            except Exception:
                return str(ka)
        pd = getattr(getattr(actor, 'sheet', None), 'public_description', None)
        if pd:
            pd_s = str(pd).strip()
            if not name_is_known:
                return pd_s or "someone"
            base = str(nm)
            if base and pd_s and pd_s.lower() not in base.lower():
                return f"{base} ({pd_s})"
            return base or pd_s

        occ = str(getattr(getattr(actor, 'sheet', None), 'occupation', '') or '').strip()
        if not name_is_known:
            if occ:
                return occ
            return "someone"

        base = str(nm)
        if occ and occ.lower() not in base.lower():
            return f"{base} ({occ})"
        return base
    except Exception:
        return "someone"


@dataclass
class ActorContext:
    """Stores contextual information about an actor's current state."""
    actor: Actor
    role: ActorRole
    scene_id: str
    last_interaction_turn: int
    is_active: bool
    location_context: str
    relationship_notes: Dict[str, str]  # Notes about relationships with other actors


class MultiActorManager:
    """
    Manages an unlimited number of actors in the UTAS simulation.
    
    Features:
    - Scalable actor storage and retrieval
    - Dynamic role assignment and management
    - Efficient turn order calculation for any number of actors
    - Context-aware actor activation/deactivation
    - Relationship tracking between all actors
    """
    
    def __init__(self):
        # Core storage
        self.actors: Dict[str, ActorContext] = {}  # actor_id -> ActorContext
        self.actor_name_index: Dict[str, str] = {}  # name -> actor_id (for fast lookup)
        
        # Scene management
        self.current_scene_id: str = str(uuid.uuid4())
        self.active_actors: Set[str] = set()  # actor_ids currently in scene
        
        # Turn management
        self.turn_history: List[Tuple[str, int]] = []  # (actor_id, turn_number)
        self.current_turn: int = 0
        
        # User actor tracking
        self.user_actor_id: Optional[str] = None
        
        # Performance optimization
        self._cached_turn_order: Optional[List[str]] = None
        self._turn_order_dirty: bool = True
    
    def add_actor(self, actor: Actor, role: ActorRole = ActorRole.SCENE_SECONDARY, 
                  location_context: str = "") -> str:
        """
        Add a new actor to the simulation.
        
        Args:
            actor: The actor instance to add
            role: The role this actor should have
            location_context: Description of where this actor is
            
        Returns:
            str: The unique actor_id assigned to this actor
        """
        actor_id = str(uuid.uuid4())
        
        # Handle duplicate names by appending numbers
        base_name = actor.sheet.name
        name = base_name
        counter = 1
        while name in self.actor_name_index:
            name = f"{base_name} ({counter})"
            counter += 1
        
        # Update actor name if it was changed
        if name != base_name:
            actor.sheet.name = name
            actor.name = name
        
        # Create actor context
        context = ActorContext(
            actor=actor,
            role=role,
            scene_id=self.current_scene_id,
            last_interaction_turn=self.current_turn,
            is_active=True,
            location_context=location_context,
            relationship_notes={}
        )
        
        # Store actor
        self.actors[actor_id] = context
        self.actor_name_index[name] = actor_id
        self.active_actors.add(actor_id)
        
        # Track user actor
        if isinstance(actor, UserActor):
            self.user_actor_id = actor_id
            context.role = ActorRole.USER
        
        # Invalidate cached turn order
        self._turn_order_dirty = True
        
        print(f"{Color.SUCCESS}✓ Added {_safe_display_name(actor)} as {role.value} (ID: {actor_id[:8]}...){Color.RESET}")
        return actor_id
    
    def remove_actor(self, actor_id: str) -> bool:
        """
        Remove an actor from the simulation.
        
        Args:
            actor_id: The ID of the actor to remove
            
        Returns:
            bool: True if actor was removed, False if not found
        """
        if actor_id not in self.actors:
            return False
        
        context = self.actors[actor_id]
        actor_name = context.actor.sheet.name
        
        # Clean up references
        del self.actors[actor_id]
        if actor_name in self.actor_name_index:
            del self.actor_name_index[actor_name]
        self.active_actors.discard(actor_id)
        
        # Clear user actor reference if needed
        if self.user_actor_id == actor_id:
            self.user_actor_id = None
        
        # Invalidate cached turn order
        self._turn_order_dirty = True
        
        try:
            disp = _safe_display_name(context.actor)
        except Exception:
            disp = actor_name
        print(f"{Color.WARNING}⚠ Removed {disp} from simulation{Color.RESET}")
        return True
    
    def get_actor_by_id(self, actor_id: str) -> Optional[Actor]:
        """Get an actor by their ID."""
        context = self.actors.get(actor_id)
        return context.actor if context else None
    
    def get_actor_by_name(self, name: str) -> Optional[Actor]:
        """Get an actor by their name."""
        actor_id = self.actor_name_index.get(name)
        return self.get_actor_by_id(actor_id) if actor_id else None
    
    def get_actor_id_by_name(self, name: str) -> Optional[str]:
        """Get an actor's ID by their name."""
        return self.actor_name_index.get(name)
    
    def get_all_actors(self) -> List[Actor]:
        """Get all actors in the simulation."""
        return [context.actor for context in self.actors.values()]
    
    def get_active_actors(self) -> List[Actor]:
        """Get all currently active actors."""
        return [self.actors[actor_id].actor for actor_id in self.active_actors 
                if actor_id in self.actors]
    
    def get_actors_by_role(self, role: ActorRole) -> List[Actor]:
        """Get all actors with a specific role."""
        return [context.actor for context in self.actors.values() 
                if context.role == role]
    
    def get_actor_role_by_actor(self, actor: Actor) -> Optional[ActorRole]:
        """Get the role of an actor by the actor object."""
        for context in self.actors.values():
            if context.actor == actor:
                return context.role
        return None
    
    def set_actor_role(self, actor_id: str, new_role: ActorRole) -> bool:
        """
        Change an actor's role.
        
        Args:
            actor_id: The ID of the actor
            new_role: The new role to assign
            
        Returns:
            bool: True if role was changed, False if actor not found
        """
        if actor_id not in self.actors:
            return False
        
        old_role = self.actors[actor_id].role
        self.actors[actor_id].role = new_role
        
        actor_name = self.actors[actor_id].actor.sheet.name
        print(f"{Color.INFO}🔄 {actor_name}: {old_role.value} → {new_role.value}{Color.RESET}")
        
        # Invalidate cached turn order if role affects turn priority
        self._turn_order_dirty = True
        return True
    
    def activate_actor(self, actor_id: str) -> bool:
        """Activate an actor (bring them into the current scene)."""
        if actor_id not in self.actors:
            return False
        
        self.actors[actor_id].is_active = True
        self.actors[actor_id].scene_id = self.current_scene_id
        self.active_actors.add(actor_id)
        self._turn_order_dirty = True
        
        actor_name = self.actors[actor_id].actor.sheet.name
        print(f"{Color.SUCCESS}✓ Activated {actor_name}{Color.RESET}")
        return True
    
    def deactivate_actor(self, actor_id: str) -> bool:
        """Deactivate an actor (remove them from current scene)."""
        if actor_id not in self.actors:
            return False
        
        self.actors[actor_id].is_active = False
        self.active_actors.discard(actor_id)
        self._turn_order_dirty = True
        
        actor_name = self.actors[actor_id].actor.sheet.name
        print(f"{Color.WARNING}⚠ Deactivated {actor_name}{Color.RESET}")
        return True
    
    def get_turn_order(self) -> List[Actor]:
        """
        Calculate turn order for all active actors based on initiative.
        Uses caching for performance with large actor counts.
        
        Returns:
            List[Actor]: Actors in turn order (highest initiative first)
        """
        if not self._turn_order_dirty and self._cached_turn_order:
            return [self.actors[actor_id].actor for actor_id in self._cached_turn_order 
                    if actor_id in self.active_actors]
        
        # Get all active actors
        active_contexts = [self.actors[actor_id] for actor_id in self.active_actors 
                          if actor_id in self.actors]
        
        if not active_contexts:
            return []
        
        # Calculate initiative for each actor
        actor_initiatives = []
        for context in active_contexts:
            actor = context.actor
            
            # Base initiative from Swiftness
            from actor_sheet import SFactorType
            swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
            
            # Add role-based priority bonuses
            role_bonus = self._get_role_priority_bonus(context.role)
            
            total_initiative = swiftness + role_bonus
            
            actor_initiatives.append((context, total_initiative))
        
        # Sort by initiative (highest first), with tiebreakers
        def sort_key(item):
            context, initiative = item
            actor = context.actor
            swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
            
            # Tiebreaker order: initiative, swiftness, role priority, random
            import random
            return (-initiative, -swiftness, -self._get_role_priority_bonus(context.role), random.random())
        
        actor_initiatives.sort(key=sort_key)
        
        # Cache the result
        self._cached_turn_order = [context.actor.sheet.name for context, _ in actor_initiatives]
        self._turn_order_dirty = False
        
        return [context.actor for context, _ in actor_initiatives]
    
    def _get_role_priority_bonus(self, role: ActorRole) -> int:
        """Get initiative bonus based on actor role."""
        bonuses = {
            ActorRole.USER: 2,           # User gets slight priority
            ActorRole.SCENE_PRIMARY: 1,   # Main scene actor gets priority
            ActorRole.SCENE_SECONDARY: 0, # Normal priority
            ActorRole.BACKGROUND: -1,     # Background actors go later
            ActorRole.INACTIVE: -10       # Inactive actors shouldn't be in turn order
        }
        return bonuses.get(role, 0)
    
    
    def record_actor_action(self, actor_id: str):
        """Record that an actor took an action this turn."""
        if actor_id in self.actors:
            self.actors[actor_id].last_interaction_turn = self.current_turn
            self._turn_order_dirty = True
    
    def advance_turn(self):
        """Advance to the next turn."""
        self.current_turn += 1
        self._turn_order_dirty = True
    
    def start_new_scene(self, scene_context: str = "") -> str:
        """
        Start a new scene, potentially changing which actors are active.
        
        Args:
            scene_context: Description of the new scene
            
        Returns:
            str: The new scene ID
        """
        old_scene_id = self.current_scene_id
        self.current_scene_id = str(uuid.uuid4())
        
        print(f"{Color.SYSTEM}🎬 Starting new scene (ID: {self.current_scene_id[:8]}...){Color.RESET}")
        if scene_context:
            print(f"{Color.INFO}   Context: {scene_context}{Color.RESET}")
        
        # Optionally deactivate all non-user actors for scene transition
        # This can be customized based on scene transition logic
        
        return self.current_scene_id
    
    def get_actor_relationships(self, actor_id: str) -> Dict[str, int]:
        """
        Get sympathy relationships for a specific actor.
        
        Args:
            actor_id: The actor to get relationships for
            
        Returns:
            Dict[str, int]: Mapping of other actor names to sympathy values
        """
        if actor_id not in self.actors:
            return {}
        
        actor = self.actors[actor_id].actor
        relationships = {}
        
        for other_id, other_context in self.actors.items():
            if other_id != actor_id:
                other_name = other_context.actor.sheet.name
                sympathy = actor.sheet.get_sympathy(other_name)
                relationships[other_name] = sympathy
        
        return relationships
    
    def update_actor_relationship(self, actor1_id: str, actor2_id: str, sympathy_change: int):
        """Update sympathy between two actors."""
        if actor1_id in self.actors and actor2_id in self.actors:
            actor1 = self.actors[actor1_id].actor
            actor2 = self.actors[actor2_id].actor
            
            # Update both directions
            actor1.sheet.update_sympathy(actor2.sheet.name, sympathy_change)
            actor2.sheet.update_sympathy(actor1.sheet.name, sympathy_change)
    
    def get_simulation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current simulation state."""
        return {
            'total_actors': len(self.actors),
            'active_actors': len(self.active_actors),
            'current_scene_id': self.current_scene_id,
            'current_turn': self.current_turn,
            'user_actor_id': self.user_actor_id,
            'actors_by_role': {
                role.value: len([c for c in self.actors.values() if c.role == role])
                for role in ActorRole
            }
        }
    
    def display_actor_summary(self):
        """Display a summary of all actors in the simulation."""
        summary = self.get_simulation_summary()
        
        print(f"\n{Color.SYSTEM}=== ACTOR SIMULATION SUMMARY ==={Color.RESET}")
        print(f"{Color.INFO}Total Actors: {summary['total_actors']}{Color.RESET}")
        print(f"{Color.INFO}Active Actors: {summary['active_actors']}{Color.RESET}")
        print(f"{Color.INFO}Current Turn: {summary['current_turn']}{Color.RESET}")
        
        print(f"\n{Color.SYSTEM}Actors by Role:{Color.RESET}")
        for role, count in summary['actors_by_role'].items():
            if count > 0:
                print(f"  {role.title()}: {count}")
        
        if self.active_actors:
            print(f"\n{Color.SYSTEM}Active Actors:{Color.RESET}")
            for actor_id in self.active_actors:
                if actor_id in self.actors:
                    context = self.actors[actor_id]
                    actor = context.actor
                    role_indicator = "👤" if isinstance(actor, UserActor) else "🤖" if isinstance(actor, NonUserActor) else "🔧"
                    print(f"  {role_indicator} {actor.sheet.name} ({context.role.value})")
