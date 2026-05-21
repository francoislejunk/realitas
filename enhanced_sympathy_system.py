"""
Enhanced Sympathy System for Multi-Actor UTAS Simulation

This system manages sympathy relationships between unlimited actors efficiently,
providing scalable N-to-N relationship tracking and management.
"""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass
from enum import Enum
import json
from actors import Actor, UserActor, NonUserActor, InanimateNonUserActor
from actor_sheet import Status, StatusType
from multi_actor_manager import MultiActorManager
from color_utils import Color


def _safe_display_name_for_player(actor_manager: MultiActorManager, name: str) -> str:
    try:
        if not name:
            return "someone"

        try:
            from stranger_description_system import known_actors_tracker
            if known_actors_tracker is not None and known_actors_tracker.is_name_known(str(name)):
                return str(name)
        except Exception:
            pass

        actor_obj = None
        try:
            actor_obj = actor_manager.get_actor_by_name(name) if actor_manager is not None else None
        except Exception:
            actor_obj = None

        if actor_obj is not None:
            try:
                if getattr(getattr(actor_obj, 'sheet', None), 'is_user_actor', False):
                    return str(name)
            except Exception:
                pass
            ka = getattr(getattr(actor_obj, 'sheet', None), 'known_as', None)
            if ka:
                return str(ka)
            pd = getattr(getattr(actor_obj, 'sheet', None), 'public_description', None)
            if pd:
                return str(pd)

        return "someone"
    except Exception:
        return "someone"

try:
    from context_store import ContextStore, WorldTime
except Exception:
    ContextStore = None
    WorldTime = None

try:
    from master_time_coordinator import get_master_time_coordinator
except Exception:
    get_master_time_coordinator = None

try:
    from spatial_context_system import get_spatial_manager
except Exception:
    get_spatial_manager = None


class RelationshipType(Enum):
    """Types of relationships between actors."""
    HOSTILE = "hostile"          # -5 to -3
    UNFRIENDLY = "unfriendly"    # -2 to -1
    NEUTRAL = "neutral"          # 0
    FRIENDLY = "friendly"        # 1 to 2
    ALLIED = "allied"           # 3 to 5


@dataclass
class RelationshipHistory:
    """Tracks the history of a relationship between two actors."""
    actor1_name: str
    actor2_name: str
    current_sympathy: int
    history: List[Tuple[int, str, int]]  # (turn, reason, change)
    relationship_type: RelationshipType
    first_meeting_turn: int
    last_interaction_turn: int
    interaction_count: int


class EnhancedSympathyManager:
    """
    Manages sympathy relationships between unlimited actors.
    
    Features:
    - Efficient N-to-N relationship storage
    - Relationship history tracking
    - Batch sympathy updates
    - Performance optimized for large actor counts
    - Relationship analytics and insights
    """
    
    def __init__(self, actor_manager: MultiActorManager):
        self.actor_manager = actor_manager
        
        # Core relationship storage - uses actor names as keys for persistence
        self.relationships: Dict[str, Dict[str, RelationshipHistory]] = {}
        
        # Performance optimization
        self._relationship_cache: Dict[Tuple[str, str], int] = {}
        self._cache_valid = False
        
        # Statistics tracking
        self.relationship_stats = {
            'total_relationships': 0,
            'hostile_relationships': 0,
            'friendly_relationships': 0,
            'neutral_relationships': 0,
            'relationship_changes': 0
        }
        
        # Current turn for history tracking
        self.current_turn = 0
    
    def initialize_actor_relationships(self, actor: Actor, baseline_sympathy: int = 1):
        """
        Initialize sympathy relationships for a new actor with all existing actors.
        
        Args:
            actor: The new actor to initialize relationships for
            baseline_sympathy: Starting sympathy value for strangers
        """
        actor_name = actor.sheet.name
        
        if actor_name not in self.relationships:
            self.relationships[actor_name] = {}
        
        # Get all existing actors
        existing_actors = self.actor_manager.get_all_actors()
        
        for existing_actor in existing_actors:
            if existing_actor.sheet.name != actor_name:
                # Initialize bidirectional relationship if it doesn't exist
                self._create_relationship(actor_name, existing_actor.sheet.name, baseline_sympathy)
        
        self._invalidate_cache()
        disp = _safe_display_name_for_player(self.actor_manager, actor_name)
        print(f"{Color.INFO}✓ Initialized relationships for {disp} with {len(existing_actors)-1} actors{Color.RESET}")
    
    def _create_relationship(self, actor1_name: str, actor2_name: str, initial_sympathy: int):
        """Create a bidirectional relationship between two actors."""
        relationship_type = self._classify_relationship(initial_sympathy)
        
        # Create relationship from actor1 to actor2
        if actor1_name not in self.relationships:
            self.relationships[actor1_name] = {}
        
        if actor2_name not in self.relationships[actor1_name]:
            self.relationships[actor1_name][actor2_name] = RelationshipHistory(
                actor1_name=actor1_name,
                actor2_name=actor2_name,
                current_sympathy=initial_sympathy,
                history=[(self.current_turn, "Initial meeting", initial_sympathy)],
                relationship_type=relationship_type,
                first_meeting_turn=self.current_turn,
                last_interaction_turn=self.current_turn,
                interaction_count=0
            )
        
        # Create reverse relationship from actor2 to actor1
        if actor2_name not in self.relationships:
            self.relationships[actor2_name] = {}
        
        if actor1_name not in self.relationships[actor2_name]:
            self.relationships[actor2_name][actor1_name] = RelationshipHistory(
                actor1_name=actor2_name,
                actor2_name=actor1_name,
                current_sympathy=initial_sympathy,
                history=[(self.current_turn, "Initial meeting", initial_sympathy)],
                relationship_type=relationship_type,
                first_meeting_turn=self.current_turn,
                last_interaction_turn=self.current_turn,
                interaction_count=0
            )
        
        # Update statistics
        self.relationship_stats['total_relationships'] += 1
        self._update_relationship_type_stats(relationship_type, 1)
    
    def get_sympathy(self, actor1_name: str, actor2_name: str) -> int:
        """
        Get sympathy value from actor1 toward actor2.
        
        Args:
            actor1_name: Name of the actor whose sympathy we're checking
            actor2_name: Name of the target actor
            
        Returns:
            int: Sympathy value (-5 to 5), defaults to 1 for strangers
        """
        # Check cache first
        cache_key = (actor1_name, actor2_name)
        if self._cache_valid and cache_key in self._relationship_cache:
            return self._relationship_cache[cache_key]
        
        # Get from relationships
        if (actor1_name in self.relationships and 
            actor2_name in self.relationships[actor1_name]):
            sympathy = self.relationships[actor1_name][actor2_name].current_sympathy
        else:
            # Default for strangers
            sympathy = 1
            # Create the relationship if actors exist
            actor1 = self.actor_manager.get_actor_by_name(actor1_name)
            actor2 = self.actor_manager.get_actor_by_name(actor2_name)
            if actor1 and actor2:
                self._create_relationship(actor1_name, actor2_name, sympathy)
        
        # Cache the result
        self._relationship_cache[cache_key] = sympathy
        return sympathy
    
    def update_sympathy(self, actor1_name: str, actor2_name: str, change: int, reason: str = ""):
        """
        Update sympathy between two actors.
        
        Args:
            actor1_name: Name of the actor whose sympathy is changing
            actor2_name: Name of the target actor
            change: Change in sympathy (-5 to +5)
            reason: Reason for the change (for history tracking)
        """
        # Ensure relationship exists
        if (actor1_name not in self.relationships or 
            actor2_name not in self.relationships[actor1_name]):
            self._create_relationship(actor1_name, actor2_name, 1)
        
        # Get current relationship
        relationship = self.relationships[actor1_name][actor2_name]
        old_sympathy = relationship.current_sympathy
        old_type = relationship.relationship_type
        
        # Apply change with clamping to valid range
        new_sympathy = max(-5, min(5, old_sympathy + change))
        new_type = self._classify_relationship(new_sympathy)
        
        # Update relationship
        relationship.current_sympathy = new_sympathy
        relationship.relationship_type = new_type
        relationship.last_interaction_turn = self.current_turn
        relationship.interaction_count += 1
        relationship.history.append((self.current_turn, reason or "Interaction", change))
        
        # Update statistics
        if old_type != new_type:
            self._update_relationship_type_stats(old_type, -1)
            self._update_relationship_type_stats(new_type, 1)
        
        if change != 0:
            self.relationship_stats['relationship_changes'] += 1
        
        # Invalidate cache
        self._invalidate_cache()
        
        # Also update the actor's internal sympathy system for compatibility
        actor1 = self.actor_manager.get_actor_by_name(actor1_name)
        if actor1:
            actor1.sheet.update_sympathy(actor2_name, change)
        
        # Log significant changes
        if abs(change) >= 2 or old_type != new_type:
            change_indicator = "📈" if change > 0 else "📉" if change < 0 else "➡️"
            print(f"{Color.INFO}{change_indicator} {actor1_name} → {actor2_name}: {old_sympathy:+d} → {new_sympathy:+d} ({new_type.value}){Color.RESET}")

        # Best-effort: persist sympathy shifts into everlasting context DB + seed memory
        try:
            if ContextStore is None or change == 0:
                return

            session_id = 'default'
            location_id = None
            try:
                if get_spatial_manager is not None:
                    spatial = get_spatial_manager()
                    session_id = getattr(spatial, 'session_id', None) or session_id
                    location_id = getattr(spatial, 'current_location', None)
            except Exception:
                pass

            def _world_time() -> Optional['WorldTime']:
                try:
                    if get_master_time_coordinator is None or WorldTime is None:
                        return None
                    tc = get_master_time_coordinator()
                    time_ctx = tc.get_current_time_context() if tc else None
                    gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
                    if gt is None:
                        return None
                    return WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
                except Exception:
                    return None

            def _resolve_id(name: str) -> str:
                try:
                    if get_spatial_manager is None:
                        return name
                    spatial = get_spatial_manager()
                    ctx = spatial.get_current_context() if spatial else None
                    if not ctx or not getattr(ctx, 'actor_positions', None):
                        return name
                    for aid, apos in ctx.actor_positions.items():
                        if getattr(apos, 'actor_name', None) == name:
                            return str(aid)
                    return name
                except Exception:
                    return name

            a1_id = _resolve_id(actor1_name)
            a2_id = _resolve_id(actor2_name)
            wt = _world_time()
            direction = 'increased' if change > 0 else 'decreased'
            summary = f"Sympathy {direction}: {actor1_name} -> {actor2_name} ({change:+d}). Reason: {reason}"

            from pathlib import Path
            store = ContextStore(Path('simulation_data/context/context.db'))
            event_id = store.log_world_event(
                session_id=session_id,
                location_id=location_id,
                event_type='SYMPATHY_SHIFT',
                summary=summary,
                importance=7 if abs(change) >= 2 or old_type != new_type else 5,
                tags=['sympathy', 'relationship'],
                payload={
                    'actor_ids': [a1_id, a2_id],
                    'actor_names': [actor1_name, actor2_name],
                    'proactor_name': actor1_name,
                    'reactor_name': actor2_name,
                    'proactor_id': a1_id,
                    'reactor_id': a2_id,
                    'change_amount': int(change),
                    'old_sympathy': int(old_sympathy),
                    'new_sympathy': int(new_sympathy),
                    'old_relationship_type': getattr(old_type, 'value', str(old_type)),
                    'new_relationship_type': getattr(new_type, 'value', str(new_type)),
                    'reason': reason,
                    'method': 'enhanced_sympathy_system',
                },
                world_time=wt
            )

            try:
                if hasattr(store, 'remember'):
                    content = f"{actor1_name} {direction} sympathy toward {actor2_name} ({change:+d}): {reason}"
                    for aid in [str(a1_id), str(a2_id)]:
                        store.remember(
                            session_id=session_id,
                            actor_id=aid,
                            memory_type='sympathy_shift',
                            content=content,
                            importance=7 if abs(change) >= 2 or old_type != new_type else 5,
                            pinned=False,
                            decay_rate=0.0002,
                            source_event_id=int(event_id) if event_id is not None else None,
                            world_time=wt
                        )
            except Exception:
                pass
        except Exception:
            return
    
    def batch_update_sympathy(self, updates: List[Tuple[str, str, int, str]]):
        """
        Apply multiple sympathy updates efficiently.
        
        Args:
            updates: List of (actor1_name, actor2_name, change, reason) tuples
        """
        print(f"{Color.INFO}📊 Processing {len(updates)} sympathy updates...{Color.RESET}")
        
        for actor1_name, actor2_name, change, reason in updates:
            self.update_sympathy(actor1_name, actor2_name, change, reason)
        
        print(f"{Color.SUCCESS}✓ Completed batch sympathy updates{Color.RESET}")
    
    def get_actor_relationships(self, actor_name: str) -> Dict[str, RelationshipHistory]:
        """Get all relationships for a specific actor."""
        return self.relationships.get(actor_name, {}).copy()
    
    def get_relationship_summary(self, actor1_name: str, actor2_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed summary of relationship between two actors."""
        if (actor1_name not in self.relationships or 
            actor2_name not in self.relationships[actor1_name]):
            return None
        
        relationship = self.relationships[actor1_name][actor2_name]
        
        return {
            'current_sympathy': relationship.current_sympathy,
            'relationship_type': relationship.relationship_type.value,
            'first_meeting_turn': relationship.first_meeting_turn,
            'last_interaction_turn': relationship.last_interaction_turn,
            'interaction_count': relationship.interaction_count,
            'history_length': len(relationship.history),
            'recent_changes': relationship.history[-3:] if len(relationship.history) > 3 else relationship.history
        }
    
    def find_relationships_by_type(self, relationship_type: RelationshipType) -> List[Tuple[str, str, int]]:
        """Find all relationships of a specific type."""
        results = []
        
        for actor1_name, actor1_relationships in self.relationships.items():
            for actor2_name, relationship in actor1_relationships.items():
                if relationship.relationship_type == relationship_type:
                    results.append((actor1_name, actor2_name, relationship.current_sympathy))
        
        return results
    
    def get_most_liked_actors(self, actor_name: str, limit: int = 5) -> List[Tuple[str, int]]:
        """Get the actors most liked by the specified actor."""
        if actor_name not in self.relationships:
            return []
        
        relationships = [(name, rel.current_sympathy) 
                        for name, rel in self.relationships[actor_name].items()]
        relationships.sort(key=lambda x: x[1], reverse=True)
        
        return relationships[:limit]
    
    def get_most_disliked_actors(self, actor_name: str, limit: int = 5) -> List[Tuple[str, int]]:
        """Get the actors most disliked by the specified actor."""
        if actor_name not in self.relationships:
            return []
        
        relationships = [(name, rel.current_sympathy) 
                        for name, rel in self.relationships[actor_name].items()]
        relationships.sort(key=lambda x: x[1])
        
        return relationships[:limit]
    
    def analyze_relationship_network(self) -> Dict[str, Any]:
        """Analyze the overall relationship network."""
        if not self.relationships:
            return {'error': 'No relationships to analyze'}
        
        all_sympathies = []
        actor_popularity = {}  # How much others like each actor
        actor_friendliness = {}  # How much each actor likes others
        
        for actor1_name, actor1_relationships in self.relationships.items():
            actor_friendliness[actor1_name] = []
            
            for actor2_name, relationship in actor1_relationships.items():
                sympathy = relationship.current_sympathy
                all_sympathies.append(sympathy)
                actor_friendliness[actor1_name].append(sympathy)
                
                # Track popularity (how much others like this actor)
                if actor2_name not in actor_popularity:
                    actor_popularity[actor2_name] = []
                actor_popularity[actor2_name].append(sympathy)
        
        # Calculate statistics
        avg_sympathy = sum(all_sympathies) / len(all_sympathies) if all_sympathies else 0
        
        # Most popular actor (most liked by others)
        most_popular = max(actor_popularity.items(), 
                          key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0) if actor_popularity else None
        
        # Most friendly actor (likes others most)
        most_friendly = max(actor_friendliness.items(), 
                           key=lambda x: sum(x[1]) / len(x[1]) if x[1] else 0) if actor_friendliness else None
        
        return {
            'total_relationships': len(all_sympathies),
            'average_sympathy': round(avg_sympathy, 2),
            'sympathy_range': (min(all_sympathies), max(all_sympathies)) if all_sympathies else (0, 0),
            'most_popular_actor': most_popular[0] if most_popular else None,
            'most_popular_score': round(sum(most_popular[1]) / len(most_popular[1]), 2) if most_popular and most_popular[1] else 0,
            'most_friendly_actor': most_friendly[0] if most_friendly else None,
            'most_friendly_score': round(sum(most_friendly[1]) / len(most_friendly[1]), 2) if most_friendly and most_friendly[1] else 0,
            'relationship_distribution': dict(self.relationship_stats)
        }
    
    def _classify_relationship(self, sympathy: int) -> RelationshipType:
        """Classify relationship type based on sympathy value."""
        if sympathy <= -3:
            return RelationshipType.HOSTILE
        elif sympathy <= -1:
            return RelationshipType.UNFRIENDLY
        elif sympathy == 0:
            return RelationshipType.NEUTRAL
        elif sympathy <= 2:
            return RelationshipType.FRIENDLY
        else:
            return RelationshipType.ALLIED
    
    def _update_relationship_type_stats(self, relationship_type: RelationshipType, change: int):
        """Update statistics for relationship type changes."""
        if relationship_type == RelationshipType.HOSTILE:
            self.relationship_stats['hostile_relationships'] += change
        elif relationship_type == RelationshipType.UNFRIENDLY:
            self.relationship_stats['hostile_relationships'] += change
        elif relationship_type == RelationshipType.NEUTRAL:
            self.relationship_stats['neutral_relationships'] += change
        elif relationship_type == RelationshipType.FRIENDLY:
            self.relationship_stats['friendly_relationships'] += change
        elif relationship_type == RelationshipType.ALLIED:
            self.relationship_stats['friendly_relationships'] += change
    
    def _invalidate_cache(self):
        """Invalidate the relationship cache."""
        self._cache_valid = False
        self._relationship_cache.clear()
    
    def advance_turn(self):
        """Advance to the next turn for history tracking."""
        self.current_turn += 1
    
    def export_relationships(self) -> Dict[str, Any]:
        """Export all relationships for saving/loading."""
        export_data = {
            'relationships': {},
            'stats': self.relationship_stats.copy(),
            'current_turn': self.current_turn
        }
        
        # Convert relationships to serializable format
        for actor1_name, actor1_relationships in self.relationships.items():
            export_data['relationships'][actor1_name] = {}
            for actor2_name, relationship in actor1_relationships.items():
                export_data['relationships'][actor1_name][actor2_name] = {
                    'current_sympathy': relationship.current_sympathy,
                    'history': relationship.history,
                    'relationship_type': relationship.relationship_type.value,
                    'first_meeting_turn': relationship.first_meeting_turn,
                    'last_interaction_turn': relationship.last_interaction_turn,
                    'interaction_count': relationship.interaction_count
                }
        
        return export_data
    
    def import_relationships(self, data: Dict[str, Any]):
        """Import relationships from saved data."""
        self.relationship_stats = data.get('stats', {})
        self.current_turn = data.get('current_turn', 0)
        
        # Import relationships
        relationships_data = data.get('relationships', {})
        for actor1_name, actor1_relationships in relationships_data.items():
            self.relationships[actor1_name] = {}
            for actor2_name, rel_data in actor1_relationships.items():
                self.relationships[actor1_name][actor2_name] = RelationshipHistory(
                    actor1_name=actor1_name,
                    actor2_name=actor2_name,
                    current_sympathy=rel_data['current_sympathy'],
                    history=rel_data['history'],
                    relationship_type=RelationshipType(rel_data['relationship_type']),
                    first_meeting_turn=rel_data['first_meeting_turn'],
                    last_interaction_turn=rel_data['last_interaction_turn'],
                    interaction_count=rel_data['interaction_count']
                )
        
        self._invalidate_cache()
        print(f"{Color.SUCCESS}✓ Imported {len(relationships_data)} actor relationships{Color.RESET}")
    
    def display_relationship_summary(self):
        """Display a summary of all relationships."""
        analysis = self.analyze_relationship_network()
        
        print(f"\n{Color.SYSTEM}=== RELATIONSHIP NETWORK SUMMARY ==={Color.RESET}")
        print(f"{Color.INFO}Total Relationships: {analysis.get('total_relationships', 0)}{Color.RESET}")
        print(f"{Color.INFO}Average Sympathy: {analysis.get('average_sympathy', 0):.2f}{Color.RESET}")
        
        if analysis.get('most_popular_actor'):
            print(f"{Color.INFO}Most Popular: {analysis['most_popular_actor']} (avg: {analysis['most_popular_score']:.2f}){Color.RESET}")
        
        if analysis.get('most_friendly_actor'):
            print(f"{Color.INFO}Most Friendly: {analysis['most_friendly_actor']} (avg: {analysis['most_friendly_score']:.2f}){Color.RESET}")
        
        print(f"\n{Color.SYSTEM}Relationship Distribution:{Color.RESET}")
        for rel_type, count in analysis.get('relationship_distribution', {}).items():
            if count > 0:
                print(f"  {rel_type.replace('_', ' ').title()}: {count}")
    
    def display_actor_relationships(self, actor_name: str):
        """Display detailed relationships for a specific actor."""
        if actor_name not in self.relationships:
            print(f"{Color.WARNING}No relationships found for {actor_name}{Color.RESET}")
            return
        
        relationships = self.relationships[actor_name]
        
        print(f"\n{Color.SYSTEM}=== RELATIONSHIPS FOR {actor_name.upper()} ==={Color.RESET}")
        
        # Group by relationship type
        by_type = {}
        for name, rel in relationships.items():
            rel_type = rel.relationship_type
            if rel_type not in by_type:
                by_type[rel_type] = []
            by_type[rel_type].append((name, rel.current_sympathy))
        
        # Display each type
        for rel_type in RelationshipType:
            if rel_type in by_type:
                print(f"\n{Color.INFO}{rel_type.value.title()} ({len(by_type[rel_type])}):{Color.RESET}")
                for name, sympathy in sorted(by_type[rel_type], key=lambda x: x[1], reverse=True):
                    print(f"  {name}: {sympathy:+d}")
