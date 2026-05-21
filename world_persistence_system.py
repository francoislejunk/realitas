"""
World Persistence System - Makes the simulation feel like reality

Three core systems:
1. Event Aftermath Tracker - Events persist and affect the world
2. In-Progress Situations - Scenes have ongoing activity when you arrive
3. Reputation Propagation - Actions ripple through social networks

Philosophy: The world doesn't wait for you. It was happening before you arrived,
continues while you're there, and keeps going after you leave.
"""

import json
import os
import random
import time
import re
from typing import List, Dict, Any, Optional, Set, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from pathlib import Path
from color_utils import Color

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

try:
    from spatial_context_system import _spatial_manager as _global_spatial_manager
except Exception:
    _global_spatial_manager = None


def _wps_get_current_world_time() -> Optional['WorldTime']:
    try:
        if get_master_time_coordinator is None or WorldTime is None:
            return None
        tc = get_master_time_coordinator()
        time_ctx = tc.get_current_time_context() if tc else None
        gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
        if gt is None:
            return None
        return WorldTime(
            day=getattr(gt, 'day', 1),
            hour=getattr(gt, 'hour', 0),
            minute=getattr(gt, 'minute', 0)
        )
    except Exception:
        return None


def _wps_try_resolve_actor_id(actor_name: str) -> str:
    try:
        if get_spatial_manager is None:
            return actor_name
        sid = None
        try:
            sid = getattr(_global_spatial_manager, 'session_id', None)
        except Exception:
            sid = None
        spatial = get_spatial_manager(session_id=sid or 'default')
        ctx = spatial.get_current_context() if spatial else None
        if not ctx or not getattr(ctx, 'actor_positions', None):
            return actor_name
        for aid, apos in ctx.actor_positions.items():
            if getattr(apos, 'actor_name', None) == actor_name:
                return str(aid)
        return actor_name
    except Exception:
        return actor_name


def _wps_log_world_event(event_type: str, summary: str, payload: Optional[Dict[str, Any]] = None,
                         importance: int = 5, tags: Optional[List[str]] = None,
                         actor_names: Optional[List[str]] = None) -> None:
    try:
        if ContextStore is None:
            return
        session_id = 'default'
        location_id = None
        try:
            if get_spatial_manager is not None:
                sid = None
                try:
                    sid = getattr(_global_spatial_manager, 'session_id', None)
                except Exception:
                    sid = None
                spatial = get_spatial_manager(session_id=sid or session_id)
                session_id = getattr(spatial, 'session_id', None) or session_id
                location_id = getattr(spatial, 'current_location', None)
        except Exception:
            pass

        actor_ids: List[str] = []
        for n in (actor_names or []):
            if n:
                actor_ids.append(_wps_try_resolve_actor_id(n))
        # De-dupe
        seen = set()
        actor_ids = [x for x in actor_ids if not (x in seen or seen.add(x))]

        wt = _wps_get_current_world_time()
        store = ContextStore(Path('simulation_data/context/context.db'))
        event_id = store.log_world_event(
            session_id=session_id,
            location_id=location_id,
            event_type=event_type,
            summary=summary,
            importance=int(importance),
            tags=tags,
            payload={
                **(payload or {}),
                'actor_ids': actor_ids,
                'actor_names': [x for x in (actor_names or []) if x],
            },
            world_time=wt
        )

        try:
            if hasattr(store, 'remember'):
                for aid in actor_ids:
                    store.remember(
                        session_id=session_id,
                        actor_id=str(aid),
                        memory_type=str(event_type).lower(),
                        content=str(summary),
                        importance=int(importance),
                        pinned=False,
                        decay_rate=0.00022,
                        source_event_id=int(event_id) if event_id is not None else None,
                        world_time=wt
                    )
        except Exception:
            pass
    except Exception:
        return


# ============================================================================
# EVENT AFTERMATH TRACKER
# ============================================================================

class AftermathType(Enum):
    """Types of aftermath that persist in the world."""
    INJURY = "injury"           # Someone was hurt - they're still hurt
    DAMAGE = "damage"           # Something broke - it's still broken
    DEATH = "death"             # Someone died - they're gone
    CONFLICT = "conflict"       # Fight happened - tension remains
    DISCOVERY = "discovery"     # Something was found/revealed
    RELATIONSHIP = "relationship"  # Relationship changed publicly
    ENVIRONMENTAL = "environmental"  # Weather, fire, flood aftermath


@dataclass
class WorldEvent:
    """A persistent event that affects the world."""
    event_id: str
    event_type: AftermathType
    description: str
    location: str
    actors_involved: List[str]
    timestamp: str
    severity: int  # 1-4
    
    # Aftermath details
    aftermath_description: str = ""
    duration_hours: float = 24.0  # How long aftermath persists
    resolved: bool = False
    resolution_description: str = ""
    
    # For injuries/damage
    affected_entity: str = ""  # Who/what is affected
    effect_description: str = ""  # "limping", "broken arm", "out of service"
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['event_type'] = self.event_type.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorldEvent':
        data['event_type'] = AftermathType(data['event_type'])
        return cls(**data)


class EventAftermathTracker:
    """
    Tracks world events and their persistent aftermath.
    
    When a crane falls on Martinez:
    - The event is recorded
    - Martinez has "injured shoulder" status
    - The crane is "out of service"
    - Scene descriptions mention the aftermath
    - Other NPCs reference it in conversation
    """
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.events_file = self.storage_dir / "world_events.json"
        
        self.events: List[WorldEvent] = []
        self._load_events()
    
    def _load_events(self):
        """Load events from disk."""
        if self.events_file.exists():
            try:
                with open(self.events_file, 'r') as f:
                    data = json.load(f)
                    self.events = [WorldEvent.from_dict(e) for e in data]
            except Exception as e:
                print(f"{Color.WARNING}[AFTERMATH] Failed to load events: {e}{Color.RESET}")
                self.events = []
    
    def _save_events(self):
        """Save events to disk."""
        try:
            with open(self.events_file, 'w') as f:
                json.dump([e.to_dict() for e in self.events], f, indent=2)
        except Exception as e:
            print(f"{Color.WARNING}[AFTERMATH] Failed to save events: {e}{Color.RESET}")
    
    def record_event(self, 
                     event_type: AftermathType,
                     description: str,
                     location: str,
                     actors_involved: List[str],
                     severity: int = 2,
                     affected_entity: str = "",
                     effect_description: str = "",
                     duration_hours: float = 24.0) -> WorldEvent:
        """Record a world event with its aftermath."""
        
        event = WorldEvent(
            event_id=f"evt_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}",
            event_type=event_type,
            description=description,
            location=location,
            actors_involved=actors_involved,
            timestamp=datetime.now().isoformat(),
            severity=severity,
            affected_entity=affected_entity,
            effect_description=effect_description,
            duration_hours=duration_hours,
            aftermath_description=self._generate_aftermath_description(
                event_type, description, affected_entity, effect_description
            )
        )
        
        self.events.append(event)
        self._save_events()

        # Best-effort: persist aftermath creation into everlasting ContextStore
        try:
            actor_names: List[str] = []
            try:
                actor_names.extend([x for x in (actors_involved or []) if x])
            except Exception:
                pass
            if affected_entity:
                actor_names.append(affected_entity)

            _wps_log_world_event(
                event_type='AFTERMATH_CREATED',
                summary=f"Aftermath created: {event_type.value} at {location} - {description}",
                payload={
                    'aftermath_event_id': event.event_id,
                    'aftermath_type': event_type.value,
                    'location': location,
                    'description': description,
                    'severity': int(severity),
                    'affected_entity': affected_entity,
                    'effect_description': effect_description,
                    'duration_hours': float(duration_hours),
                    'aftermath_description': event.aftermath_description,
                },
                importance=max(5, min(9, int(severity) + 4)),
                tags=['aftermath', event_type.value],
                actor_names=actor_names
            )
        except Exception:
            pass
        
        return event
    
    def _generate_aftermath_description(self, event_type: AftermathType, 
                                         description: str, 
                                         affected_entity: str,
                                         effect: str) -> str:
        """Generate a description of the aftermath for scene injection."""
        
        if event_type == AftermathType.INJURY:
            return f"{affected_entity} is still recovering - {effect}."
        elif event_type == AftermathType.DAMAGE:
            return f"The {affected_entity} remains {effect}. Yellow caution tape marks the area."
        elif event_type == AftermathType.DEATH:
            return f"A somber atmosphere lingers where {affected_entity} fell. People speak in hushed tones."
        elif event_type == AftermathType.CONFLICT:
            return f"Tension hangs in the air after the confrontation. People are on edge."
        elif event_type == AftermathType.ENVIRONMENTAL:
            return f"Signs of the {effect} are still visible - cleanup is ongoing."
        else:
            return f"The aftermath of recent events is still evident."
    
    def get_active_aftermath(self, location: str = None, 
                             actor_name: str = None,
                             max_age_hours: float = 48.0) -> List[WorldEvent]:
        """Get events with active aftermath, optionally filtered."""
        
        active = []
        now = datetime.now()
        
        for event in self.events:
            if event.resolved:
                continue
            
            # Check age
            try:
                event_time = datetime.fromisoformat(event.timestamp)
                age_hours = (now - event_time).total_seconds() / 3600
                if age_hours > event.duration_hours or age_hours > max_age_hours:
                    continue
            except:
                continue
            
            # Filter by location
            if location and event.location.lower() not in location.lower():
                if location.lower() not in event.location.lower():
                    continue
            
            # Filter by actor
            if actor_name:
                if actor_name not in event.actors_involved and actor_name != event.affected_entity:
                    continue
            
            active.append(event)
        
        return active
    
    def get_aftermath_for_scene(self, scene_description: str, 
                                 present_actors: List[str] = None) -> str:
        """Get aftermath text to inject into scene descriptions."""
        
        aftermath_lines = []
        
        # Get location-relevant aftermath
        location_events = self.get_active_aftermath(location=scene_description[:100])
        
        for event in location_events[:3]:  # Limit to 3 most relevant
            aftermath_lines.append(event.aftermath_description)
        
        # Get actor-relevant aftermath
        if present_actors:
            for actor in present_actors:
                actor_events = self.get_active_aftermath(actor_name=actor)
                for event in actor_events[:1]:  # 1 per actor
                    if event not in location_events:
                        aftermath_lines.append(event.aftermath_description)
        
        if aftermath_lines:
            return "\n".join(aftermath_lines)
        return ""
    
    def get_npc_injury_status(self, npc_name: str) -> Optional[str]:
        """Check if an NPC has an active injury."""
        events = self.get_active_aftermath(actor_name=npc_name)
        
        for event in events:
            if event.event_type == AftermathType.INJURY:
                if event.affected_entity == npc_name:
                    return event.effect_description
        
        return None
    
    def resolve_event(self, event_id: str, resolution: str = ""):
        """Mark an event as resolved."""
        for event in self.events:
            if event.event_id == event_id:
                event.resolved = True
                event.resolution_description = resolution
                self._save_events()

                # Best-effort: persist aftermath resolution
                try:
                    actor_names: List[str] = []
                    try:
                        actor_names.extend([x for x in (event.actors_involved or []) if x])
                    except Exception:
                        pass
                    if getattr(event, 'affected_entity', None):
                        actor_names.append(getattr(event, 'affected_entity'))

                    _wps_log_world_event(
                        event_type='AFTERMATH_RESOLVED',
                        summary=f"Aftermath resolved: {event.event_type.value} at {event.location} - {event.description}. Resolution: {resolution}",
                        payload={
                            'aftermath_event_id': event.event_id,
                            'aftermath_type': event.event_type.value,
                            'location': event.location,
                            'description': event.description,
                            'resolution': resolution,
                        },
                        importance=6,
                        tags=['aftermath', 'resolved', event.event_type.value],
                        actor_names=actor_names
                    )
                except Exception:
                    pass
                return


# ============================================================================
# IN-PROGRESS SITUATIONS
# ============================================================================

class SituationType(Enum):
    """Types of ongoing situations."""
    CONVERSATION = "conversation"
    ARGUMENT = "argument"
    WORK_TASK = "work_task"
    WAITING = "waiting"
    TRANSACTION = "transaction"
    EMERGENCY = "emergency"
    LEISURE = "leisure"
    TENSION = "tension"


@dataclass
class OngoingSituation:
    """A situation already in progress when the user arrives."""
    situation_type: SituationType
    participants: List[str]
    description: str
    tension_level: int  # 0-5
    can_involve_user: bool = True
    resolution_hint: str = ""  # What might happen next


class InProgressSituationGenerator:
    """
    Generates ongoing situations for scenes.
    
    Philosophy: You're not the protagonist who triggers everything.
    You walk into a world already in motion.
    """
    
    def __init__(self, rag_system=None):
        self.rag_system = rag_system
        
        # Situation templates by type
        self.templates = {
            SituationType.CONVERSATION: [
                "{npc1} and {npc2} are deep in conversation, heads close together",
                "{npc1} is explaining something to {npc2}, gesturing emphatically",
                "{npc1} and {npc2} share a laugh over something you didn't catch",
            ],
            SituationType.ARGUMENT: [
                "{npc1} and {npc2} are having a heated exchange, voices rising",
                "{npc1} jabs a finger at {npc2}, face flushed with anger",
                "Tension crackles between {npc1} and {npc2} - something's wrong",
            ],
            SituationType.WORK_TASK: [
                "{npc1} is focused on their work, barely noticing your arrival",
                "{npc1} struggles with a stubborn piece of equipment",
                "{npc1} and {npc2} coordinate on a task, calling out to each other",
            ],
            SituationType.WAITING: [
                "{npc1} checks their watch impatiently, waiting for something",
                "{npc1} paces near the entrance, clearly expecting someone",
                "A small group has gathered, waiting for something to begin",
            ],
            SituationType.TRANSACTION: [
                "{npc1} counts out money while {npc2} watches carefully",
                "{npc1} hands something to {npc2} with a meaningful look",
                "Papers are being signed - some kind of deal in progress",
            ],
            SituationType.EMERGENCY: [
                "People are gathered around something - there's been an incident",
                "{npc1} is shouting orders, trying to manage a situation",
                "The atmosphere is tense - something just happened",
            ],
            SituationType.LEISURE: [
                "{npc1} nurses a drink, lost in thought",
                "A card game is in progress, money on the table",
                "{npc1} and {npc2} share a meal, conversation easy",
            ],
            SituationType.TENSION: [
                "The room goes quiet as you enter - conversations pause",
                "Eyes follow you - you've interrupted something",
                "There's an undercurrent of unease you can't quite place",
            ],
        }
    
    def generate_situation(self, 
                           available_npcs: List[str],
                           scene_description: str,
                           time_of_day: str = "day",
                           recent_events: List[WorldEvent] = None) -> Optional[OngoingSituation]:
        """Generate an in-progress situation for the scene."""
        
        if not available_npcs:
            return None
        
        # Determine situation type based on context
        situation_type = self._determine_situation_type(
            scene_description, time_of_day, recent_events
        )
        
        # Select participants
        num_participants = min(len(available_npcs), random.choice([1, 1, 2, 2, 2, 3]))
        participants = random.sample(available_npcs, num_participants)
        
        # Generate description
        description = self._generate_description(situation_type, participants)
        
        # Determine tension level
        tension = self._calculate_tension(situation_type, recent_events)
        
        return OngoingSituation(
            situation_type=situation_type,
            participants=participants,
            description=description,
            tension_level=tension,
            can_involve_user=situation_type not in [SituationType.TENSION],
            resolution_hint=self._get_resolution_hint(situation_type)
        )
    
    def _determine_situation_type(self, scene: str, time: str, 
                                   events: List[WorldEvent] = None) -> SituationType:
        """Determine appropriate situation type for context."""
        
        # If recent emergency events, higher chance of emergency/tension
        if events:
            recent_severe = [e for e in events if e.severity >= 3]
            if recent_severe:
                if random.random() < 0.4:
                    return random.choice([SituationType.EMERGENCY, SituationType.TENSION])
        
        # Time-based weighting
        if time in ['night', 'evening']:
            weights = {
                SituationType.CONVERSATION: 3,
                SituationType.ARGUMENT: 2,
                SituationType.LEISURE: 4,
                SituationType.TENSION: 2,
                SituationType.WAITING: 1,
            }
        else:
            weights = {
                SituationType.CONVERSATION: 2,
                SituationType.WORK_TASK: 4,
                SituationType.TRANSACTION: 2,
                SituationType.WAITING: 2,
                SituationType.ARGUMENT: 1,
            }
        
        # Scene-based adjustments
        scene_lower = scene.lower()
        if 'bar' in scene_lower or 'restaurant' in scene_lower:
            weights[SituationType.LEISURE] = weights.get(SituationType.LEISURE, 0) + 3
        if 'office' in scene_lower or 'work' in scene_lower:
            weights[SituationType.WORK_TASK] = weights.get(SituationType.WORK_TASK, 0) + 3
        
        # Weighted random selection
        types = list(weights.keys())
        probs = [weights[t] for t in types]
        total = sum(probs)
        probs = [p/total for p in probs]
        
        return random.choices(types, weights=probs)[0]
    
    def _generate_description(self, situation_type: SituationType, 
                               participants: List[str]) -> str:
        """Generate situation description from template."""
        
        templates = self.templates.get(situation_type, ["{npc1} is here"])
        template = random.choice(templates)
        
        # Fill in participants
        replacements = {
            '{npc1}': participants[0] if len(participants) > 0 else 'Someone',
            '{npc2}': participants[1] if len(participants) > 1 else 'another person',
            '{npc3}': participants[2] if len(participants) > 2 else 'a third person',
        }
        
        description = template
        for key, value in replacements.items():
            description = description.replace(key, value)
        
        return description
    
    def _calculate_tension(self, situation_type: SituationType,
                           events: List[WorldEvent] = None) -> int:
        """Calculate tension level 0-5."""
        
        base_tension = {
            SituationType.CONVERSATION: 1,
            SituationType.ARGUMENT: 4,
            SituationType.WORK_TASK: 1,
            SituationType.WAITING: 2,
            SituationType.TRANSACTION: 2,
            SituationType.EMERGENCY: 5,
            SituationType.LEISURE: 0,
            SituationType.TENSION: 4,
        }.get(situation_type, 2)
        
        # Increase if recent severe events
        if events:
            severe_count = sum(1 for e in events if e.severity >= 3)
            base_tension = min(5, base_tension + severe_count)
        
        return base_tension
    
    def _get_resolution_hint(self, situation_type: SituationType) -> str:
        """Get a hint about what might happen next."""
        
        hints = {
            SituationType.ARGUMENT: "This could escalate or someone might back down",
            SituationType.EMERGENCY: "Help is needed or the situation will worsen",
            SituationType.TRANSACTION: "The deal is almost done",
            SituationType.WAITING: "Whatever they're waiting for is coming soon",
            SituationType.TENSION: "Something is about to break",
        }
        
        return hints.get(situation_type, "")


# ============================================================================
# REPUTATION PROPAGATION
# ============================================================================

@dataclass
class SocialConnection:
    """A connection between two NPCs."""
    npc1: str
    npc2: str
    relationship: str  # "coworker", "friend", "family", "rival", "acquaintance"
    strength: int  # 1-5, how close they are
    
    def involves(self, npc_name: str) -> bool:
        return npc_name in [self.npc1, self.npc2]
    
    def get_other(self, npc_name: str) -> Optional[str]:
        if npc_name == self.npc1:
            return self.npc2
        elif npc_name == self.npc2:
            return self.npc1
        return None


class ReputationPropagator:
    """
    Propagates reputation changes through NPC social networks.
    
    When you help Martinez:
    - Martinez's sympathy toward you increases (direct)
    - Martinez tells his friend Chen about it
    - Chen's sympathy toward you increases slightly (propagated)
    - The foreman hears about it from Chen
    - Your reputation as "helpful" spreads
    """
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.connections_file = self.storage_dir / "social_connections.json"
        self.reputation_file = self.storage_dir / "reputation_events.json"
        
        self.connections: List[SocialConnection] = []
        self.reputation_events: List[Dict] = []
        
        self._load_data()
    
    def _load_data(self):
        """Load social network data."""
        if self.connections_file.exists():
            try:
                with open(self.connections_file, 'r') as f:
                    data = json.load(f)
                    self.connections = [SocialConnection(**c) for c in data]
            except Exception:
                self.connections = []
        
        if self.reputation_file.exists():
            try:
                with open(self.reputation_file, 'r') as f:
                    self.reputation_events = json.load(f)
            except Exception:
                self.reputation_events = []
    
    def _save_data(self):
        """Save social network data."""
        try:
            with open(self.connections_file, 'w') as f:
                json.dump([asdict(c) for c in self.connections], f, indent=2)
            with open(self.reputation_file, 'w') as f:
                json.dump(self.reputation_events, f, indent=2)
        except Exception as e:
            print(f"{Color.WARNING}[REPUTATION] Failed to save: {e}{Color.RESET}")
    
    def add_connection(self, npc1: str, npc2: str, 
                       relationship: str = "acquaintance",
                       strength: int = 2):
        """Add a social connection between NPCs."""
        
        # Check if connection exists
        for conn in self.connections:
            if conn.involves(npc1) and conn.involves(npc2):
                conn.relationship = relationship
                conn.strength = strength
                self._save_data()
                return
        
        self.connections.append(SocialConnection(
            npc1=npc1, npc2=npc2, relationship=relationship, strength=strength
        ))
        self._save_data()
    
    def auto_generate_connections(self, npcs: List[str], location: str = ""):
        """Auto-generate plausible connections between NPCs at a location."""
        
        if len(npcs) < 2:
            return
        
        # NPCs at the same location likely know each other
        for i, npc1 in enumerate(npcs):
            for npc2 in npcs[i+1:]:
                # Check if connection exists
                exists = any(c.involves(npc1) and c.involves(npc2) for c in self.connections)
                if not exists:
                    # Generate connection based on context
                    if random.random() < 0.7:  # 70% chance they know each other
                        relationship = random.choice([
                            "coworker", "coworker", "coworker",
                            "acquaintance", "acquaintance",
                            "friend"
                        ])
                        strength = random.randint(1, 3)
                        self.add_connection(npc1, npc2, relationship, strength)
    
    def get_connected_npcs(self, npc_name: str, min_strength: int = 1) -> List[Tuple[str, SocialConnection]]:
        """Get all NPCs connected to this one."""
        
        connected = []
        for conn in self.connections:
            if conn.involves(npc_name) and conn.strength >= min_strength:
                other = conn.get_other(npc_name)
                if other:
                    connected.append((other, conn))
        
        return connected
    
    def propagate_reputation_change(self,
                                     user_name: str,
                                     affected_npc: str,
                                     action_type: str,  # "helped", "harmed", "impressed", "insulted"
                                     magnitude: int,  # 1-3
                                     actor_sheet_updater=None) -> List[Dict]:
        """
        Propagate a reputation change through the social network.
        
        Returns list of propagation effects for display.
        """
        
        propagation_effects = []
        
        # Record the original event
        event = {
            "timestamp": datetime.now().isoformat(),
            "user": user_name,
            "target_npc": affected_npc,
            "action_type": action_type,
            "magnitude": magnitude
        }
        self.reputation_events.append(event)
        
        # Get connected NPCs
        connected = self.get_connected_npcs(affected_npc)
        
        for other_npc, connection in connected:
            # Calculate propagation chance based on connection strength and action magnitude
            propagation_chance = (connection.strength / 5) * (magnitude / 3) * 0.6
            
            if random.random() < propagation_chance:
                # Determine propagated effect
                if action_type in ["helped", "impressed"]:
                    propagated_change = 1 if magnitude >= 2 else 0
                    effect_type = "positive"
                elif action_type in ["harmed", "insulted"]:
                    propagated_change = -1 if magnitude >= 2 else 0
                    effect_type = "negative"
                else:
                    propagated_change = 0
                    effect_type = "neutral"
                
                if propagated_change != 0:
                    # Apply the change if we have an updater
                    if actor_sheet_updater:
                        try:
                            actor_sheet_updater(other_npc, user_name, propagated_change)
                        except Exception:
                            pass
                    
                    # Record the propagation
                    propagation = {
                        "from_npc": affected_npc,
                        "to_npc": other_npc,
                        "relationship": connection.relationship,
                        "effect_type": effect_type,
                        "change": propagated_change,
                        "reason": f"{affected_npc} told {other_npc} about what happened"
                    }
                    propagation_effects.append(propagation)
        
        self._save_data()
        return propagation_effects
    
    def get_reputation_summary(self, user_name: str) -> Dict[str, int]:
        """Get a summary of user's reputation based on recent events."""
        
        summary = {"positive": 0, "negative": 0, "neutral": 0}
        
        # Count recent events (last 20)
        recent = self.reputation_events[-20:]
        
        for event in recent:
            if event.get("user") == user_name:
                action = event.get("action_type", "")
                if action in ["helped", "impressed"]:
                    summary["positive"] += 1
                elif action in ["harmed", "insulted"]:
                    summary["negative"] += 1
                else:
                    summary["neutral"] += 1
        
        return summary
    
    def display_propagation_effects(self, effects: List[Dict]):
        """Display reputation propagation to the user."""
        
        if not effects:
            return
        
        print(f"\n{Color.INFO}━━━ 📢 WORD SPREADS ━━━{Color.RESET}")
        
        for effect in effects:
            if effect["effect_type"] == "positive":
                emoji = "👍"
                color = Color.SUCCESS
            else:
                emoji = "👎"
                color = Color.WARNING
            
            print(f"{color}{emoji} {effect['reason']}{Color.RESET}")
            print(f"{color}   {effect['to_npc']}'s opinion of you shifts.{Color.RESET}")


# ============================================================================
# UNIFIED WORLD STATE MANAGER
# ============================================================================

class WorldStateManager:
    """
    Unified manager for all world persistence systems.
    
    Provides a single interface for:
    - Event aftermath tracking
    - In-progress situation generation
    - Reputation propagation
    """
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state", rag_system=None):
        self.storage_dir = storage_dir
        
        # Initialize subsystems
        self.aftermath_tracker = EventAftermathTracker(storage_dir)
        self.situation_generator = InProgressSituationGenerator(rag_system)
        self.reputation_propagator = ReputationPropagator(storage_dir)

        # Best-effort: avoid spamming situation logs for identical generated situations
        self._last_logged_situation_key: Optional[str] = None
    
    def record_hazard_event(self, 
                            hazard_name: str,
                            victim_name: str,
                            location: str,
                            severity: int,
                            effect: str) -> WorldEvent:
        """Record a hazard event with aftermath."""
        
        return self.aftermath_tracker.record_event(
            event_type=AftermathType.INJURY if victim_name else AftermathType.DAMAGE,
            description=f"{hazard_name} incident",
            location=location,
            actors_involved=[victim_name] if victim_name else [],
            severity=severity,
            affected_entity=victim_name or hazard_name,
            effect_description=effect,
            duration_hours=24.0 * severity  # More severe = longer aftermath
        )
    
    def record_conflict_event(self,
                              participants: List[str],
                              location: str,
                              severity: int) -> WorldEvent:
        """Record a conflict between NPCs."""
        
        return self.aftermath_tracker.record_event(
            event_type=AftermathType.CONFLICT,
            description=f"Confrontation between {' and '.join(participants)}",
            location=location,
            actors_involved=participants,
            severity=severity,
            duration_hours=12.0 * severity
        )
    
    def get_scene_context(self, 
                          scene_description: str,
                          present_npcs: List[str],
                          time_of_day: str = "day") -> Dict[str, Any]:
        """
        Get full world context for a scene.
        
        Returns:
        - aftermath: Text describing persistent aftermath
        - situation: An ongoing situation (if any)
        - npc_injuries: Dict of NPC injuries
        """
        
        # Get aftermath
        aftermath = self.aftermath_tracker.get_aftermath_for_scene(
            scene_description, present_npcs
        )
        
        # Get recent events for situation generation
        recent_events = self.aftermath_tracker.get_active_aftermath(max_age_hours=24)
        
        # Generate in-progress situation
        situation = self.situation_generator.generate_situation(
            available_npcs=present_npcs,
            scene_description=scene_description,
            time_of_day=time_of_day,
            recent_events=recent_events
        )

        # Best-effort: persist high-signal in-progress situations (noise-filtered)
        try:
            if situation is not None:
                high_signal_types = {
                    SituationType.EMERGENCY,
                    SituationType.ARGUMENT,
                    SituationType.TRANSACTION,
                    SituationType.TENSION,
                }

                should_log = (getattr(situation, 'tension_level', 0) >= 4) or (situation.situation_type in high_signal_types)
                if should_log:
                    key = f"{scene_description[:80]}||{situation.situation_type.value}||{','.join(situation.participants)}||{situation.description}"
                    if key != getattr(self, '_last_logged_situation_key', None):
                        self._last_logged_situation_key = key
                        _wps_log_world_event(
                            event_type='SITUATION_ACTIVE',
                            summary=f"Ongoing situation ({situation.situation_type.value}) in scene: {situation.description}",
                            payload={
                                'situation_type': situation.situation_type.value,
                                'participants': list(situation.participants or []),
                                'description': situation.description,
                                'tension_level': int(getattr(situation, 'tension_level', 0)),
                                'can_involve_user': bool(getattr(situation, 'can_involve_user', True)),
                                'resolution_hint': getattr(situation, 'resolution_hint', ''),
                                'scene_excerpt': scene_description[:200],
                            },
                            importance=6,
                            tags=['situation', 'ongoing', situation.situation_type.value],
                            actor_names=list(situation.participants or [])
                        )
        except Exception:
            pass
        
        # Check NPC injuries
        npc_injuries = {}
        for npc in present_npcs:
            injury = self.aftermath_tracker.get_npc_injury_status(npc)
            if injury:
                npc_injuries[npc] = injury
        
        # Auto-generate social connections
        self.reputation_propagator.auto_generate_connections(present_npcs, scene_description[:50])
        
        return {
            "aftermath": aftermath,
            "situation": situation,
            "npc_injuries": npc_injuries,
            "recent_events": recent_events
        }
    
    def process_reputation_change(self,
                                   user_name: str,
                                   npc_name: str,
                                   action_type: str,
                                   magnitude: int,
                                   actor_sheet_updater=None) -> List[Dict]:
        """Process a reputation change and propagate through network."""
        
        effects = self.reputation_propagator.propagate_reputation_change(
            user_name=user_name,
            affected_npc=npc_name,
            action_type=action_type,
            magnitude=magnitude,
            actor_sheet_updater=actor_sheet_updater
        )
        
        # Display effects
        self.reputation_propagator.display_propagation_effects(effects)
        
        return effects


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

_world_state_manager: Optional[WorldStateManager] = None

def get_world_state_manager(storage_dir: str = "./simulation_data/world_state",
                            rag_system=None) -> WorldStateManager:
    """Get or create the global world state manager."""
    global _world_state_manager
    
    if _world_state_manager is None:
        _world_state_manager = WorldStateManager(storage_dir, rag_system)
    
    return _world_state_manager


def format_situation_for_display(situation: OngoingSituation) -> str:
    """Format an in-progress situation for display."""
    
    if not situation:
        return ""
    
    tension_indicator = "⚡" * situation.tension_level if situation.tension_level > 2 else ""
    
    return f"{tension_indicator}{situation.description}"


# ============================================================================
# NPC SCHEDULES & ROUTINES
# ============================================================================

class ActivityType(Enum):
    """Types of activities NPCs can be doing."""
    SLEEPING = "sleeping"
    WORKING = "working"
    COMMUTING = "commuting"
    EATING = "eating"
    LEISURE = "leisure"
    SOCIALIZING = "socializing"
    ERRANDS = "errands"
    UNAVAILABLE = "unavailable"  # Generic "not here"


@dataclass
class ScheduleBlock:
    """A block of time in an NPC's schedule."""
    start_hour: int  # 0-23
    end_hour: int    # 0-23 (can wrap around midnight)
    activity: ActivityType
    location: str    # Where they are during this block
    flexibility: float = 0.5  # 0-1, how likely to deviate from schedule
    
    def contains_hour(self, hour: int) -> bool:
        """Check if this block contains the given hour."""
        if self.start_hour <= self.end_hour:
            return self.start_hour <= hour < self.end_hour
        else:
            # Wraps around midnight (e.g., 22-6)
            return hour >= self.start_hour or hour < self.end_hour


@dataclass 
class NPCSchedule:
    """Complete schedule for an NPC."""
    npc_name: str
    occupation: str
    home_location: str
    work_location: str
    schedule_blocks: List[ScheduleBlock] = field(default_factory=list)
    
    # Schedule modifiers
    days_off: List[int] = field(default_factory=list)  # 0=Monday, 6=Sunday
    is_night_shift: bool = False
    
    def get_current_activity(self, hour: int, day_of_week: int = 0) -> Tuple[ActivityType, str]:
        """Get what the NPC is doing at this hour."""
        
        # Check if it's a day off
        if day_of_week in self.days_off:
            # Day off schedule - simplified
            if 0 <= hour < 9:
                return ActivityType.SLEEPING, self.home_location
            elif 9 <= hour < 12:
                return ActivityType.LEISURE, self.home_location
            elif 12 <= hour < 14:
                return ActivityType.EATING, "restaurant"
            elif 14 <= hour < 18:
                return ActivityType.ERRANDS, "various"
            elif 18 <= hour < 22:
                return ActivityType.SOCIALIZING, "bar"
            else:
                return ActivityType.SLEEPING, self.home_location
        
        # Check schedule blocks
        for block in self.schedule_blocks:
            if block.contains_hour(hour):
                return block.activity, block.location
        
        # Default fallback
        if 0 <= hour < 7:
            return ActivityType.SLEEPING, self.home_location
        elif 7 <= hour < 8:
            return ActivityType.COMMUTING, "transit"
        elif 8 <= hour < 17:
            return ActivityType.WORKING, self.work_location
        elif 17 <= hour < 18:
            return ActivityType.COMMUTING, "transit"
        elif 18 <= hour < 22:
            return ActivityType.LEISURE, self.home_location
        else:
            return ActivityType.SLEEPING, self.home_location


class NPCScheduleManager:
    """
    Manages NPC schedules and availability.
    
    NPCs aren't always available - they have lives, routines, and places to be.
    """
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.schedules_file = self.storage_dir / "npc_schedules.json"
        
        self.schedules: Dict[str, NPCSchedule] = {}
        self._load_schedules()
        
        # Occupation-based schedule templates
        self.occupation_templates = self._create_occupation_templates()
    
    def _load_schedules(self):
        """Load schedules from disk."""
        if self.schedules_file.exists():
            try:
                with open(self.schedules_file, 'r') as f:
                    data = json.load(f)
                    for name, sched_data in data.items():
                        blocks = [
                            ScheduleBlock(
                                start_hour=b['start_hour'],
                                end_hour=b['end_hour'],
                                activity=ActivityType(b['activity']),
                                location=b['location'],
                                flexibility=b.get('flexibility', 0.5)
                            )
                            for b in sched_data.get('schedule_blocks', [])
                        ]
                        self.schedules[name] = NPCSchedule(
                            npc_name=name,
                            occupation=sched_data.get('occupation', 'unknown'),
                            home_location=sched_data.get('home_location', 'home'),
                            work_location=sched_data.get('work_location', 'workplace'),
                            schedule_blocks=blocks,
                            days_off=sched_data.get('days_off', [6]),
                            is_night_shift=sched_data.get('is_night_shift', False)
                        )
            except Exception as e:
                print(f"{Color.WARNING}[SCHEDULES] Failed to load: {e}{Color.RESET}")
    
    def _save_schedules(self):
        """Save schedules to disk."""
        try:
            data = {}
            for name, sched in self.schedules.items():
                data[name] = {
                    'occupation': sched.occupation,
                    'home_location': sched.home_location,
                    'work_location': sched.work_location,
                    'schedule_blocks': [
                        {
                            'start_hour': b.start_hour,
                            'end_hour': b.end_hour,
                            'activity': b.activity.value,
                            'location': b.location,
                            'flexibility': b.flexibility
                        }
                        for b in sched.schedule_blocks
                    ],
                    'days_off': sched.days_off,
                    'is_night_shift': sched.is_night_shift
                }
            with open(self.schedules_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"{Color.WARNING}[SCHEDULES] Failed to save: {e}{Color.RESET}")
    
    def _create_occupation_templates(self) -> Dict[str, List[ScheduleBlock]]:
        """Create schedule templates based on occupation."""
        return {
            # Day shift workers (9-5)
            "office_worker": [
                ScheduleBlock(0, 7, ActivityType.SLEEPING, "home"),
                ScheduleBlock(7, 8, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(8, 12, ActivityType.WORKING, "office"),
                ScheduleBlock(12, 13, ActivityType.EATING, "cafeteria"),
                ScheduleBlock(13, 17, ActivityType.WORKING, "office"),
                ScheduleBlock(17, 18, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(18, 22, ActivityType.LEISURE, "home"),
                ScheduleBlock(22, 24, ActivityType.SLEEPING, "home"),
            ],
            
            # Industrial workers (early shift)
            "factory_worker": [
                ScheduleBlock(0, 5, ActivityType.SLEEPING, "home"),
                ScheduleBlock(5, 6, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(6, 14, ActivityType.WORKING, "factory"),
                ScheduleBlock(14, 15, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(15, 18, ActivityType.LEISURE, "home"),
                ScheduleBlock(18, 20, ActivityType.SOCIALIZING, "bar"),
                ScheduleBlock(20, 24, ActivityType.SLEEPING, "home"),
            ],
            
            # Night shift workers
            "night_guard": [
                ScheduleBlock(0, 8, ActivityType.WORKING, "workplace"),
                ScheduleBlock(8, 9, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(9, 17, ActivityType.SLEEPING, "home"),
                ScheduleBlock(17, 19, ActivityType.LEISURE, "home"),
                ScheduleBlock(19, 20, ActivityType.EATING, "diner"),
                ScheduleBlock(20, 22, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(22, 24, ActivityType.WORKING, "workplace"),
            ],
            
            # Service workers (variable)
            "bartender": [
                ScheduleBlock(0, 3, ActivityType.WORKING, "bar"),
                ScheduleBlock(3, 4, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(4, 12, ActivityType.SLEEPING, "home"),
                ScheduleBlock(12, 14, ActivityType.LEISURE, "home"),
                ScheduleBlock(14, 16, ActivityType.ERRANDS, "various"),
                ScheduleBlock(16, 17, ActivityType.EATING, "home"),
                ScheduleBlock(17, 18, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(18, 24, ActivityType.WORKING, "bar"),
            ],
            
            # Healthcare (rotating shifts)
            "nurse": [
                ScheduleBlock(0, 7, ActivityType.SLEEPING, "home"),
                ScheduleBlock(7, 8, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(8, 20, ActivityType.WORKING, "hospital"),
                ScheduleBlock(20, 21, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(21, 24, ActivityType.SLEEPING, "home"),
            ],
            
            # Default/generic
            "default": [
                ScheduleBlock(0, 7, ActivityType.SLEEPING, "home"),
                ScheduleBlock(7, 8, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(8, 17, ActivityType.WORKING, "workplace"),
                ScheduleBlock(17, 18, ActivityType.COMMUTING, "transit"),
                ScheduleBlock(18, 22, ActivityType.LEISURE, "home"),
                ScheduleBlock(22, 24, ActivityType.SLEEPING, "home"),
            ],
        }
    
    def create_schedule_for_npc(self, npc_name: str, occupation: str, 
                                 work_location: str = "workplace",
                                 home_location: str = "home") -> NPCSchedule:
        """Create a schedule for an NPC based on their occupation."""
        
        # Find matching template
        occupation_lower = occupation.lower()
        template_key = "default"
        
        for key in self.occupation_templates:
            if key in occupation_lower or occupation_lower in key:
                template_key = key
                break
        
        # Check for night-shift indicators
        is_night = any(word in occupation_lower for word in 
                      ['night', 'guard', 'security', 'bartender', 'bouncer'])
        
        # Create schedule from template
        template_blocks = self.occupation_templates[template_key]
        
        # Customize locations
        blocks = []
        for b in template_blocks:
            location = b.location
            if location == "workplace":
                location = work_location
            elif location == "home":
                location = home_location
            
            blocks.append(ScheduleBlock(
                start_hour=b.start_hour,
                end_hour=b.end_hour,
                activity=b.activity,
                location=location,
                flexibility=b.flexibility
            ))
        
        schedule = NPCSchedule(
            npc_name=npc_name,
            occupation=occupation,
            home_location=home_location,
            work_location=work_location,
            schedule_blocks=blocks,
            days_off=[5, 6] if not is_night else [0, 1],  # Weekend off, or Mon-Tue for night shift
            is_night_shift=is_night
        )
        
        self.schedules[npc_name] = schedule
        self._save_schedules()
        
        return schedule
    
    def get_npc_status(self, npc_name: str, hour: int, 
                       day_of_week: int = 0,
                       current_location: str = "") -> Dict[str, Any]:
        """
        Get NPC's current status and availability.
        
        Returns:
            dict with keys: available, activity, location, reason
        """
        
        # Get or create schedule
        if npc_name not in self.schedules:
            return {
                "available": True,
                "activity": ActivityType.UNAVAILABLE,
                "location": "unknown",
                "reason": "No schedule defined"
            }
        
        schedule = self.schedules[npc_name]
        activity, expected_location = schedule.get_current_activity(hour, day_of_week)
        
        # Check if NPC is at the current location
        available = False
        reason = ""
        
        if current_location:
            # Check if expected location matches current scene
            location_match = (
                expected_location.lower() in current_location.lower() or
                current_location.lower() in expected_location.lower() or
                expected_location == "various"
            )
            
            if location_match:
                available = True
                reason = f"Currently {activity.value} here"
            else:
                available = False
                if activity == ActivityType.SLEEPING:
                    reason = f"Sleeping at home"
                elif activity == ActivityType.WORKING:
                    reason = f"At work ({expected_location})"
                elif activity == ActivityType.COMMUTING:
                    reason = f"In transit"
                else:
                    reason = f"{activity.value.title()} at {expected_location}"
        else:
            available = True
            reason = f"Currently {activity.value}"
        
        return {
            "available": available,
            "activity": activity,
            "location": expected_location,
            "reason": reason
        }
    
    def get_available_npcs(self, all_npcs: List[str], hour: int,
                           current_location: str,
                           day_of_week: int = 0) -> Tuple[List[str], List[Tuple[str, str]]]:
        """
        Filter NPCs by availability at current time/location.
        
        Returns:
            (available_npcs, unavailable_with_reasons)
        """
        available = []
        unavailable = []
        
        for npc_name in all_npcs:
            status = self.get_npc_status(npc_name, hour, day_of_week, current_location)
            
            if status["available"]:
                available.append(npc_name)
            else:
                unavailable.append((npc_name, status["reason"]))
        
        return available, unavailable
    
    def get_npcs_at_location(self, location: str, hour: int,
                             day_of_week: int = 0) -> List[Tuple[str, ActivityType]]:
        """Get all NPCs who should be at a specific location right now."""
        
        npcs_here = []
        
        for npc_name, schedule in self.schedules.items():
            activity, expected_loc = schedule.get_current_activity(hour, day_of_week)
            
            if (expected_loc.lower() in location.lower() or 
                location.lower() in expected_loc.lower()):
                npcs_here.append((npc_name, activity))
        
        return npcs_here


# ============================================================================
# OBJECT & ENVIRONMENTAL PERSISTENCE
# ============================================================================

@dataclass
class PersistentObject:
    """An object that persists in the world."""
    object_id: str
    name: str
    description: str
    location: str
    position: str  # "on the table", "by the door", "in the corner"
    
    # State
    state: str = "normal"  # normal, damaged, destroyed, moved, hidden
    owner: str = ""  # Who it belongs to (if anyone)
    
    # Timestamps
    placed_at: str = ""
    last_interacted: str = ""
    
    # Flags
    is_portable: bool = True
    is_valuable: bool = False
    is_evidence: bool = False  # Important for investigations
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'PersistentObject':
        return cls(**data)


@dataclass
class EnvironmentalState:
    """State of environmental elements at a location."""
    location: str
    
    # Lighting
    lights_on: bool = True
    natural_light: str = "normal"  # dark, dim, normal, bright
    
    # Doors/Windows
    doors: Dict[str, str] = field(default_factory=dict)  # door_name: open/closed/locked
    windows: Dict[str, str] = field(default_factory=dict)  # window_name: open/closed/broken
    
    # Atmosphere
    temperature: str = "normal"  # cold, cool, normal, warm, hot
    air_quality: str = "normal"  # fresh, stale, smoky, dusty
    noise_level: str = "normal"  # quiet, normal, noisy, loud
    
    # Cleanliness
    cleanliness: str = "normal"  # pristine, clean, normal, messy, filthy
    
    # Timestamps
    last_updated: str = ""
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EnvironmentalState':
        return cls(**data)


class ObjectPersistenceManager:
    """
    Manages persistent objects and environmental state.
    
    Things stay where you put them. Doors stay open. Lights stay off.
    """
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.objects_file = self.storage_dir / "persistent_objects.json"
        self.environments_file = self.storage_dir / "environmental_states.json"
        
        self.objects: Dict[str, PersistentObject] = {}
        self.environments: Dict[str, EnvironmentalState] = {}
        
        self._load_data()
    
    def _load_data(self):
        """Load persistent data from disk."""
        if self.objects_file.exists():
            try:
                with open(self.objects_file, 'r') as f:
                    data = json.load(f)
                    self.objects = {k: PersistentObject.from_dict(v) for k, v in data.items()}
            except Exception as e:
                print(f"{Color.WARNING}[OBJECTS] Failed to load: {e}{Color.RESET}")
        
        if self.environments_file.exists():
            try:
                with open(self.environments_file, 'r') as f:
                    data = json.load(f)
                    self.environments = {k: EnvironmentalState.from_dict(v) for k, v in data.items()}
            except Exception as e:
                print(f"{Color.WARNING}[ENVIRONMENTS] Failed to load: {e}{Color.RESET}")
    
    def _save_data(self):
        """Save persistent data to disk."""
        try:
            with open(self.objects_file, 'w') as f:
                json.dump({k: v.to_dict() for k, v in self.objects.items()}, f, indent=2)
            with open(self.environments_file, 'w') as f:
                json.dump({k: v.to_dict() for k, v in self.environments.items()}, f, indent=2)
        except Exception as e:
            print(f"{Color.WARNING}[PERSISTENCE] Failed to save: {e}{Color.RESET}")
    
    # ==================== OBJECT MANAGEMENT ====================
    
    def place_object(self, name: str, description: str, location: str,
                     position: str, owner: str = "",
                     is_portable: bool = True,
                     is_valuable: bool = False) -> PersistentObject:
        """Place an object in the world."""
        
        obj_id = f"obj_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{random.randint(1000,9999)}"
        
        obj = PersistentObject(
            object_id=obj_id,
            name=name,
            description=description,
            location=location,
            position=position,
            owner=owner,
            is_portable=is_portable,
            is_valuable=is_valuable,
            placed_at=datetime.now().isoformat(),
            last_interacted=datetime.now().isoformat()
        )
        
        self.objects[obj_id] = obj
        self._save_data()
        
        return obj
    
    def move_object(self, obj_id: str, new_location: str, new_position: str):
        """Move an object to a new location."""
        if obj_id in self.objects:
            obj = self.objects[obj_id]
            obj.location = new_location
            obj.position = new_position
            obj.state = "moved"
            obj.last_interacted = datetime.now().isoformat()
            self._save_data()
    
    def update_object_state(self, obj_id: str, new_state: str):
        """Update an object's state (damaged, destroyed, hidden, etc.)."""
        if obj_id in self.objects:
            self.objects[obj_id].state = new_state
            self.objects[obj_id].last_interacted = datetime.now().isoformat()
            self._save_data()
    
    def get_objects_at_location(self, location: str) -> List[PersistentObject]:
        """Get all objects at a location."""
        return [
            obj for obj in self.objects.values()
            if location.lower() in obj.location.lower() or obj.location.lower() in location.lower()
        ]
    
    def find_object_by_name(self, name: str, location: str = None) -> Optional[PersistentObject]:
        """Find an object by name, optionally at a specific location."""
        for obj in self.objects.values():
            if name.lower() in obj.name.lower():
                if location is None or location.lower() in obj.location.lower():
                    return obj
        return None
    
    def remove_object(self, obj_id: str):
        """Remove an object from the world (picked up, destroyed, etc.)."""
        if obj_id in self.objects:
            del self.objects[obj_id]
            self._save_data()
    
    # ==================== ENVIRONMENT MANAGEMENT ====================
    
    def get_environment(self, location: str) -> EnvironmentalState:
        """Get or create environmental state for a location."""
        
        # Normalize location key
        loc_key = location.lower().strip()[:50]
        
        if loc_key not in self.environments:
            self.environments[loc_key] = EnvironmentalState(
                location=location,
                last_updated=datetime.now().isoformat()
            )
            self._save_data()
        
        return self.environments[loc_key]
    
    def set_lights(self, location: str, on: bool):
        """Turn lights on or off at a location."""
        env = self.get_environment(location)
        env.lights_on = on
        env.last_updated = datetime.now().isoformat()
        self._save_data()
    
    def set_door_state(self, location: str, door_name: str, state: str):
        """Set door state (open/closed/locked)."""
        env = self.get_environment(location)
        env.doors[door_name] = state
        env.last_updated = datetime.now().isoformat()
        self._save_data()
    
    def set_window_state(self, location: str, window_name: str, state: str):
        """Set window state (open/closed/broken)."""
        env = self.get_environment(location)
        env.windows[window_name] = state
        env.last_updated = datetime.now().isoformat()
        self._save_data()
    
    def update_atmosphere(self, location: str, 
                          temperature: str = None,
                          air_quality: str = None,
                          noise_level: str = None,
                          cleanliness: str = None):
        """Update atmospheric conditions at a location."""
        env = self.get_environment(location)
        
        if temperature:
            env.temperature = temperature
        if air_quality:
            env.air_quality = air_quality
        if noise_level:
            env.noise_level = noise_level
        if cleanliness:
            env.cleanliness = cleanliness
        
        env.last_updated = datetime.now().isoformat()
        self._save_data()
    
    # ==================== SCENE INTEGRATION ====================
    
    def get_location_description_additions(self, location: str) -> str:
        """Get additional description text for objects and environment at location."""
        
        additions = []
        
        # Get objects
        objects = self.get_objects_at_location(location)
        if objects:
            for obj in objects[:5]:  # Limit to 5 most relevant
                if obj.state == "normal":
                    additions.append(f"{obj.name} is {obj.position}.")
                elif obj.state == "damaged":
                    additions.append(f"A damaged {obj.name} lies {obj.position}.")
                elif obj.state == "moved":
                    additions.append(f"{obj.name} has been moved to {obj.position}.")
        
        # Get environment
        loc_key = location.lower().strip()[:50]
        if loc_key in self.environments:
            env = self.environments[loc_key]
            
            # Lighting
            if not env.lights_on:
                additions.append("The lights are off.")
            
            # Doors
            for door, state in env.doors.items():
                if state == "open":
                    additions.append(f"The {door} stands open.")
                elif state == "locked":
                    additions.append(f"The {door} is locked.")
            
            # Windows
            for window, state in env.windows.items():
                if state == "open":
                    additions.append(f"The {window} is open.")
                elif state == "broken":
                    additions.append(f"The {window} is broken.")
            
            # Atmosphere
            if env.temperature != "normal":
                temp_desc = {"cold": "It's cold in here.", "cool": "There's a chill in the air.",
                            "warm": "It's warm.", "hot": "It's uncomfortably hot."}
                additions.append(temp_desc.get(env.temperature, ""))
            
            if env.air_quality != "normal":
                air_desc = {"stale": "The air is stale.", "smoky": "Smoke hangs in the air.",
                           "dusty": "Dust motes float in the air.", "fresh": "The air is fresh."}
                additions.append(air_desc.get(env.air_quality, ""))
            
            if env.cleanliness not in ["normal", "clean"]:
                clean_desc = {"messy": "The place is a mess.", "filthy": "Filth covers every surface.",
                             "pristine": "Everything is immaculately clean."}
                additions.append(clean_desc.get(env.cleanliness, ""))
        
        return " ".join([a for a in additions if a])


# ============================================================================
# EXTENDED WORLD STATE MANAGER
# ============================================================================

# Update WorldStateManager to include new systems
class ExtendedWorldStateManager(WorldStateManager):
    """
    Extended world state manager with NPC schedules, object persistence,
    action linking, off-screen simulation, and weather.
    """
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state", rag_system=None):
        super().__init__(storage_dir, rag_system)
        
        # Add new subsystems
        self.schedule_manager = NPCScheduleManager(storage_dir)
        self.object_manager = ObjectPersistenceManager(storage_dir)
        self.offscreen_simulator = OffScreenSimulator(storage_dir)
        self.weather_system = WeatherSystem(storage_dir)
        self.action_linker = None  # Initialized lazily to avoid circular ref
        
        # Additional reality systems
        self.spatial_memory = SpatialMemorySystem(storage_dir)
        self.sound_system = SoundPropagationSystem(storage_dir)
        self.npc_memory = NPCMemoryOfUser(storage_dir)
        self.rumor_system = RumorSystem(storage_dir)
        self.faction_system = FactionSystem(storage_dir)
        self.obligation_system = SocialObligationSystem(storage_dir)
        self.calendar_system = CalendarSystem(storage_dir)
    
    def get_full_scene_context(self,
                                scene_description: str,
                                present_npcs: List[str],
                                hour: int,
                                day_of_week: int = 0,
                                current_location: str = "") -> Dict[str, Any]:
        """
        Get complete world context for a scene including schedules and objects.
        """
        
        # Get base context
        context = self.get_scene_context(
            scene_description=scene_description,
            present_npcs=present_npcs,
            time_of_day="night" if (hour < 6 or hour >= 22) else "day"
        )
        
        # Add NPC availability
        available, unavailable = self.schedule_manager.get_available_npcs(
            all_npcs=present_npcs,
            hour=hour,
            current_location=current_location or scene_description[:50],
            day_of_week=day_of_week
        )
        context["available_npcs"] = available
        context["unavailable_npcs"] = unavailable
        
        # Add object/environment info
        location = current_location or scene_description[:50]
        context["persistent_objects"] = self.object_manager.get_objects_at_location(location)
        context["environment_additions"] = self.object_manager.get_location_description_additions(location)

        # Best-effort: inject everlasting context (recent world events + recalled long-term memories)
        try:
            ev = self.get_everlasting_context(
                present_npcs=list(present_npcs or []),
                current_location=location,
                max_age_minutes=180,
                events_limit=20,
                memories_limit=6
            )
            if ev:
                context.update(ev)
        except Exception:
            pass
        
        return context

    def get_everlasting_context(self,
                               *,
                               present_npcs: List[str],
                               current_location: str = "",
                               max_age_minutes: int = 180,
                               events_limit: int = 20,
                               memories_limit: int = 6) -> Dict[str, Any]:
        """Side-effect-free: fetch only ContextStore-backed everlasting context."""
        out: Dict[str, Any] = {}
        try:
            if ContextStore is None:
                return out

            session_id = 'default'
            location_id = current_location or None
            try:
                spatial = None
                try:
                    import spatial_context_system as _scs
                    spatial = getattr(_scs, '_spatial_manager', None)
                except Exception:
                    spatial = None

                if spatial is None and get_spatial_manager is not None:
                    spatial = get_spatial_manager(session_id=session_id)

                session_id = getattr(spatial, 'session_id', None) or session_id
                location_id = getattr(spatial, 'current_location', None) or location_id
            except Exception:
                pass

            wt = _wps_get_current_world_time()
            from pathlib import Path
            store = ContextStore(Path('simulation_data/context/context.db'))

            min_wms = None
            try:
                if wt is not None:
                    min_wms = max(0, int(wt.minutes_since_start) - int(max(0, int(max_age_minutes))))
            except Exception:
                min_wms = None

            recent_events = []
            try:
                recent_events = store.get_recent_world_events(
                    session_id=session_id,
                    location_id=location_id,
                    limit=int(events_limit),
                    min_world_minutes_since_start=min_wms
                )
            except Exception:
                recent_events = []

            actor_ids: List[str] = []
            actor_names: List[str] = [n for n in (present_npcs or []) if n]

            try:
                spatial = None
                try:
                    import spatial_context_system as _scs
                    spatial = getattr(_scs, '_spatial_manager', None)
                except Exception:
                    spatial = None

                if spatial is None and get_spatial_manager is not None:
                    spatial = get_spatial_manager(session_id=session_id)

                ctx = spatial.get_current_context() if spatial else None
                if ctx and getattr(ctx, 'actor_positions', None):
                    for aid, apos in ctx.actor_positions.items():
                        if getattr(apos, 'is_user_actor', False):
                            ua_name = getattr(apos, 'actor_name', None)
                            if ua_name:
                                actor_names.insert(0, ua_name)
                            actor_ids.insert(0, str(aid))
                            break
            except Exception:
                pass

            try:
                for n in actor_names:
                    if n and str(n) not in [str(x) for x in actor_ids]:
                        actor_ids.append(_wps_try_resolve_actor_id(n))
            except Exception:
                actor_ids = [str(n) for n in actor_names]

            seen = set()
            actor_ids = [x for x in actor_ids if not (x in seen or seen.add(x))]

            recalled_by_actor: Dict[str, List[Dict[str, Any]]] = {}
            try:
                for aid in actor_ids:
                    try:
                        recalled_by_actor[str(aid)] = store.recall(
                            session_id=session_id,
                            actor_id=str(aid),
                            query=None,
                            limit=int(memories_limit),
                            world_time=wt,
                            min_strength=0.08
                        )
                    except Exception:
                        recalled_by_actor[str(aid)] = []
            except Exception:
                recalled_by_actor = {}

            lines: List[str] = []
            if recent_events:
                lines.append("## Everlasting Context: Recent World Events")
                for e in list(recent_events)[:12]:
                    try:
                        et = e.get('event_type')
                        summ = e.get('summary')
                        if summ:
                            lines.append(f"- [{et}] {summ}")
                    except Exception:
                        continue

            memories_lines: List[str] = []
            for aid, mems in (recalled_by_actor or {}).items():
                if not mems:
                    continue
                try:
                    name_guess = None
                    try:
                        idx = actor_ids.index(aid)
                        if idx >= 0 and idx < len(actor_names):
                            name_guess = actor_names[idx]
                    except Exception:
                        name_guess = None
                    header = name_guess or aid
                    memories_lines.append(f"- {header}:")
                    for m in mems[:6]:
                        c = m.get('content')
                        if not c:
                            continue
                        mt = m.get('memory_type')
                        imp = m.get('importance')
                        pinned = bool(m.get('pinned'))
                        eff = m.get('effective_strength')
                        meta = []
                        try:
                            if mt:
                                meta.append(str(mt))
                        except Exception:
                            pass
                        try:
                            if pinned:
                                meta.append('pinned')
                        except Exception:
                            pass
                        try:
                            if imp is not None:
                                meta.append(f"i{int(imp)}")
                        except Exception:
                            pass
                        try:
                            if eff is not None:
                                meta.append(f"s{float(eff):.2f}")
                        except Exception:
                            pass
                        meta_txt = f" [{'|'.join(meta)}]" if meta else ""
                        memories_lines.append(f"  - {c}{meta_txt}")
                except Exception:
                    continue

            if memories_lines:
                lines.append("## Everlasting Context: Recalled Memories")
                lines.extend(memories_lines)

            out['everlasting_recent_world_events'] = recent_events
            out['everlasting_recalled_memories'] = recalled_by_actor
            out['everlasting_context_text'] = "\n".join(lines).strip()
            return out
        except Exception:
            return out
    
    def ensure_npc_has_schedule(self, npc_name: str, occupation: str,
                                 work_location: str = "workplace"):
        """Ensure an NPC has a schedule, creating one if needed."""
        if npc_name not in self.schedule_manager.schedules:
            self.schedule_manager.create_schedule_for_npc(
                npc_name=npc_name,
                occupation=occupation,
                work_location=work_location
            )
    
    def get_action_linker(self) -> 'ActionWorldLinker':
        """Get or create the action linker."""
        if self.action_linker is None:
            self.action_linker = ActionWorldLinker(self)
        return self.action_linker
    
    def process_user_action(self, action_text: str, location: str, 
                            actor_name: str = "") -> List[Dict[str, Any]]:
        """
        Process a user action and persist any world changes.
        
        Returns list of world changes for display.
        """
        linker = self.get_action_linker()
        return linker.process_action(action_text, location, actor_name)
    
    def simulate_time_passage(self, hours_passed: float, 
                               known_npcs: List[str] = None) -> Dict[str, Any]:
        """
        Simulate world changes during time passage.
        
        Returns dict with weather changes and NPC events.
        """
        results = {
            "weather_change": None,
            "npc_events": [],
            "weather_description": ""
        }
        
        # Update weather
        weather_change = self.weather_system.update_weather(hours_passed)
        if weather_change:
            results["weather_change"] = weather_change
        results["weather_description"] = self.weather_system.get_weather_description()
        
        # Simulate NPCs
        if known_npcs:
            for npc_name in known_npcs:
                events = self.offscreen_simulator.simulate_time_passage(
                    npc_name=npc_name,
                    hours_passed=hours_passed,
                    schedule_manager=self.schedule_manager,
                    reputation_propagator=self.reputation_propagator
                )
                results["npc_events"].extend(events)
        
        return results
    
    def get_npc_reunion_info(self, npc_name: str) -> Dict[str, Any]:
        """Get info about what an NPC has been up to since last seen."""
        return self.offscreen_simulator.get_reunion_context(npc_name)
    
    def get_weather_for_scene(self) -> Dict[str, Any]:
        """Get current weather info for scene description."""
        return {
            "description": self.weather_system.get_weather_description(),
            "effects": self.weather_system.get_weather_effects(),
            "type": self.weather_system.get_current_weather().weather_type.value
        }


# Replace the global getter
_extended_world_state_manager: Optional[ExtendedWorldStateManager] = None

def get_extended_world_state_manager(storage_dir: str = "./simulation_data/world_state",
                                      rag_system=None) -> ExtendedWorldStateManager:
    """Get or create the extended world state manager."""
    global _extended_world_state_manager
    
    if _extended_world_state_manager is None:
        _extended_world_state_manager = ExtendedWorldStateManager(storage_dir, rag_system)
    
    return _extended_world_state_manager


# ============================================================================
# ACTION-TO-WORLD LINKING
# ============================================================================

class ActionWorldLinker:
    """
    Automatically detects world-affecting actions and persists their effects.
    
    When user "drops the cigarette" -> creates persistent object
    When user "turns off the lights" -> updates environment state
    When user "breaks the window" -> updates window state + creates debris
    """
    
    def __init__(self, world_state: ExtendedWorldStateManager):
        self.world_state = world_state
        
        # Action patterns that affect objects
        self.object_creation_verbs = [
            'drop', 'leave', 'place', 'put', 'set', 'throw', 'toss',
            'discard', 'abandon', 'deposit', 'lay'
        ]
        
        self.object_destruction_verbs = [
            'break', 'smash', 'destroy', 'shatter', 'crush', 'tear',
            'rip', 'burn', 'demolish'
        ]
        
        self.object_movement_verbs = [
            'move', 'push', 'pull', 'drag', 'carry', 'shift', 'slide',
            'roll', 'kick', 'shove'
        ]
        
        # Action patterns that affect environment
        self.light_verbs = ['turn on', 'turn off', 'switch on', 'switch off', 'flip']
        self.door_verbs = ['open', 'close', 'shut', 'lock', 'unlock', 'slam']
        self.window_verbs = ['open', 'close', 'break', 'shatter', 'smash']
    
    def process_action(self, action_text: str, location: str, 
                       actor_name: str = "") -> List[Dict[str, Any]]:
        """
        Process an action and detect world-affecting changes.
        
        Returns list of changes made to the world.
        """
        changes = []
        action_lower = action_text.lower()
        
        # Check for object creation (dropping/leaving things)
        obj_change = self._check_object_creation(action_lower, location, actor_name)
        if obj_change:
            changes.append(obj_change)
        
        # Check for object destruction
        dest_change = self._check_object_destruction(action_lower, location)
        if dest_change:
            changes.append(dest_change)
        
        # Check for environment changes
        env_changes = self._check_environment_changes(action_lower, location)
        changes.extend(env_changes)
        
        # SOUND PROPAGATION: Emit sounds for loud actions
        self._emit_action_sounds(action_lower, location, actor_name)
        
        return changes
    
    def _emit_action_sounds(self, action: str, location: str, actor_name: str):
        """Emit sounds based on action type."""
        try:
            sound_sys = self.world_state.sound_system
            
            # Gunshots
            if any(w in action for w in ['shoot', 'fire', 'gun', 'shot']):
                sound_sys.emit_sound(
                    SoundType.GUNSHOT, location,
                    f"a gunshot from {location}", intensity=1.0, duration=5.0
                )
            # Explosions
            elif any(w in action for w in ['explode', 'explosion', 'blast', 'bomb']):
                sound_sys.emit_sound(
                    SoundType.EXPLOSION, location,
                    f"an explosion from {location}", intensity=1.0, duration=10.0
                )
            # Fighting
            elif any(w in action for w in ['punch', 'kick', 'fight', 'attack', 'hit', 'strike']):
                sound_sys.emit_sound(
                    SoundType.FIGHT, location,
                    f"sounds of a fight from {location}", intensity=0.8, duration=30.0
                )
            # Screaming
            elif any(w in action for w in ['scream', 'yell', 'shout', 'cry out']):
                sound_sys.emit_sound(
                    SoundType.SCREAM, location,
                    f"someone screaming from {location}", intensity=0.9, duration=5.0
                )
            # Doors
            elif any(w in action for w in ['slam', 'bang', 'crash']):
                sound_sys.emit_sound(
                    SoundType.DOOR, location,
                    f"a loud bang from {location}", intensity=0.7, duration=2.0
                )
        except Exception:
            pass  # Sound is optional
    
    def _check_object_creation(self, action: str, location: str, 
                                actor_name: str) -> Optional[Dict]:
        """Check if action creates a persistent object."""
        
        for verb in self.object_creation_verbs:
            if verb in action:
                # Try to extract what was dropped/placed
                obj_name = self._extract_object_name(action, verb)
                if obj_name:
                    # Create the persistent object
                    position = self._extract_position(action) or "on the ground"
                    
                    obj = self.world_state.object_manager.place_object(
                        name=obj_name,
                        description=f"Left here by {actor_name}" if actor_name else "Left here",
                        location=location,
                        position=position,
                        owner=actor_name
                    )
                    
                    return {
                        "type": "object_created",
                        "object": obj_name,
                        "position": position,
                        "message": f"📦 {obj_name} is now {position}."
                    }
        
        return None
    
    def _check_object_destruction(self, action: str, location: str) -> Optional[Dict]:
        """Check if action destroys/damages an object."""
        
        for verb in self.object_destruction_verbs:
            if verb in action:
                obj_name = self._extract_object_name(action, verb)
                if obj_name:
                    # Check if object exists
                    existing = self.world_state.object_manager.find_object_by_name(
                        obj_name, location
                    )
                    
                    if existing:
                        self.world_state.object_manager.update_object_state(
                            existing.object_id, "damaged"
                        )
                        return {
                            "type": "object_damaged",
                            "object": obj_name,
                            "message": f"💥 The {obj_name} is now damaged."
                        }
                    else:
                        # Create debris
                        self.world_state.object_manager.place_object(
                            name=f"Broken {obj_name}",
                            description=f"Remnants of a destroyed {obj_name}",
                            location=location,
                            position="scattered on the ground",
                            is_portable=False
                        )
                        return {
                            "type": "object_destroyed",
                            "object": obj_name,
                            "message": f"💥 The {obj_name} is destroyed. Debris litters the area."
                        }
        
        return None
    
    def _check_environment_changes(self, action: str, location: str) -> List[Dict]:
        """Check if action changes environment state."""
        
        changes = []
        
        # Light changes
        if any(v in action for v in ['turn off', 'switch off']):
            if 'light' in action or 'lamp' in action:
                self.world_state.object_manager.set_lights(location, on=False)
                changes.append({
                    "type": "lights_off",
                    "message": "🔦 The lights go off. Darkness settles in."
                })
        
        elif any(v in action for v in ['turn on', 'switch on']):
            if 'light' in action or 'lamp' in action:
                self.world_state.object_manager.set_lights(location, on=True)
                changes.append({
                    "type": "lights_on",
                    "message": "💡 Light floods the space."
                })
        
        # Door changes
        for door_word in ['door', 'gate', 'hatch', 'entrance']:
            if door_word in action:
                door_name = self._extract_door_name(action, door_word)
                
                if 'open' in action or 'unlock' in action:
                    state = 'open' if 'open' in action else 'unlocked'
                    self.world_state.object_manager.set_door_state(location, door_name, state)
                    changes.append({
                        "type": f"door_{state}",
                        "door": door_name,
                        "message": f"🚪 The {door_name} is now {state}."
                    })
                elif 'close' in action or 'shut' in action:
                    self.world_state.object_manager.set_door_state(location, door_name, 'closed')
                    changes.append({
                        "type": "door_closed",
                        "door": door_name,
                        "message": f"🚪 The {door_name} closes."
                    })
                elif 'lock' in action:
                    self.world_state.object_manager.set_door_state(location, door_name, 'locked')
                    changes.append({
                        "type": "door_locked",
                        "door": door_name,
                        "message": f"🔒 The {door_name} is now locked."
                    })
                break
        
        # Window changes
        for window_word in ['window', 'pane', 'glass']:
            if window_word in action:
                window_name = self._extract_door_name(action, window_word)  # Reuse logic
                
                if 'break' in action or 'smash' in action or 'shatter' in action:
                    self.world_state.object_manager.set_window_state(location, window_name, 'broken')
                    # Also create glass debris
                    self.world_state.object_manager.place_object(
                        name="Broken glass",
                        description="Shards of broken glass",
                        location=location,
                        position="scattered beneath the window",
                        is_portable=False
                    )
                    changes.append({
                        "type": "window_broken",
                        "window": window_name,
                        "message": f"💥 Glass shatters. The {window_name} is broken."
                    })
                elif 'open' in action:
                    self.world_state.object_manager.set_window_state(location, window_name, 'open')
                    changes.append({
                        "type": "window_open",
                        "window": window_name,
                        "message": f"🪟 The {window_name} is now open. Fresh air flows in."
                    })
                elif 'close' in action:
                    self.world_state.object_manager.set_window_state(location, window_name, 'closed')
                    changes.append({
                        "type": "window_closed",
                        "window": window_name,
                        "message": f"🪟 The {window_name} closes."
                    })
                break
        
        return changes
    
    def _extract_object_name(self, action: str, verb: str) -> Optional[str]:
        """Extract the object name from an action string."""
        
        # Common patterns: "drop the cigarette", "leave my bag", "put the gun down"
        import re
        
        # Pattern: verb + (the/a/my/his/her) + object
        patterns = [
            rf'{verb}\s+(?:the|a|an|my|his|her|their)?\s*(\w+(?:\s+\w+)?)',
            rf'{verb}s?\s+(?:the|a|an|my|his|her|their)?\s*(\w+(?:\s+\w+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, action)
            if match:
                obj = match.group(1).strip()
                # Filter out common non-objects
                if obj not in ['it', 'them', 'down', 'up', 'here', 'there', 'away']:
                    return obj.title()
        
        return None
    
    def _extract_position(self, action: str) -> Optional[str]:
        """Extract position/location from action string."""
        
        import re
        
        # Patterns: "on the table", "by the door", "in the corner"
        patterns = [
            r'(on|by|near|beside|next to|in|under|behind|against)\s+(?:the\s+)?(\w+(?:\s+\w+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, action)
            if match:
                prep = match.group(1)
                location = match.group(2)
                return f"{prep} the {location}"
        
        return None
    
    def _extract_door_name(self, action: str, door_word: str) -> str:
        """Extract door/window name from action."""
        
        import re
        
        # Pattern: "the back door", "front door", "main entrance"
        pattern = rf'(?:the\s+)?(\w+\s+)?{door_word}'
        match = re.search(pattern, action)
        
        if match and match.group(1):
            return f"{match.group(1).strip()} {door_word}"
        
        return door_word


# ============================================================================
# NPC OFF-SCREEN SIMULATION
# ============================================================================

class NPCGoalType(Enum):
    """Types of goals NPCs can pursue."""
    WORK = "work"           # Do their job
    SOCIALIZE = "socialize" # Talk to people, build relationships
    REST = "rest"           # Recover energy
    ERRAND = "errand"       # Personal tasks
    CONFLICT = "conflict"   # Pursue grudge/rivalry
    HELP = "help"           # Assist someone they like
    AVOID = "avoid"         # Stay away from someone they dislike


@dataclass
class NPCGoal:
    """A goal an NPC is pursuing."""
    goal_type: NPCGoalType
    target: str = ""        # Target person/place/thing
    priority: int = 5       # 1-10, higher = more important
    progress: float = 0.0   # 0-1, how close to completion
    started_at: str = ""
    
    def to_dict(self) -> Dict:
        d = asdict(self)
        d['goal_type'] = self.goal_type.value
        return d
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NPCGoal':
        data['goal_type'] = NPCGoalType(data['goal_type'])
        return cls(**data)


@dataclass
class NPCOffScreenState:
    """State of an NPC when off-screen."""
    npc_name: str
    current_goals: List[NPCGoal] = field(default_factory=list)
    recent_actions: List[str] = field(default_factory=list)  # What they did while away
    mood: str = "neutral"  # happy, neutral, stressed, angry, tired
    energy: float = 1.0    # 0-1
    last_simulated: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'npc_name': self.npc_name,
            'current_goals': [g.to_dict() for g in self.current_goals],
            'recent_actions': self.recent_actions,
            'mood': self.mood,
            'energy': self.energy,
            'last_simulated': self.last_simulated
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'NPCOffScreenState':
        goals = [NPCGoal.from_dict(g) for g in data.get('current_goals', [])]
        return cls(
            npc_name=data['npc_name'],
            current_goals=goals,
            recent_actions=data.get('recent_actions', []),
            mood=data.get('mood', 'neutral'),
            energy=data.get('energy', 1.0),
            last_simulated=data.get('last_simulated', '')
        )


class OffScreenSimulator:
    """
    Simulates what NPCs do when the user isn't around.
    
    When you leave and come back:
    - NPCs have progressed their goals
    - Relationships may have shifted
    - Events may have occurred
    - The world moved forward
    """
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.states_file = self.storage_dir / "npc_offscreen_states.json"
        
        self.npc_states: Dict[str, NPCOffScreenState] = {}
        self._load_states()
    
    def _load_states(self):
        """Load NPC states from disk."""
        if self.states_file.exists():
            try:
                with open(self.states_file, 'r') as f:
                    data = json.load(f)
                    self.npc_states = {
                        k: NPCOffScreenState.from_dict(v) 
                        for k, v in data.items()
                    }
            except Exception as e:
                print(f"{Color.WARNING}[OFFSCREEN] Failed to load: {e}{Color.RESET}")
    
    def _save_states(self):
        """Save NPC states to disk."""
        try:
            with open(self.states_file, 'w') as f:
                json.dump(
                    {k: v.to_dict() for k, v in self.npc_states.items()},
                    f, indent=2
                )
        except Exception as e:
            print(f"{Color.WARNING}[OFFSCREEN] Failed to save: {e}{Color.RESET}")
    
    def get_or_create_state(self, npc_name: str) -> NPCOffScreenState:
        """Get or create off-screen state for an NPC."""
        if npc_name not in self.npc_states:
            self.npc_states[npc_name] = NPCOffScreenState(
                npc_name=npc_name,
                last_simulated=datetime.now().isoformat()
            )
            self._save_states()
        return self.npc_states[npc_name]
    
    def assign_goal(self, npc_name: str, goal_type: NPCGoalType, 
                    target: str = "", priority: int = 5):
        """Assign a goal to an NPC."""
        state = self.get_or_create_state(npc_name)
        
        goal = NPCGoal(
            goal_type=goal_type,
            target=target,
            priority=priority,
            started_at=datetime.now().isoformat()
        )
        
        state.current_goals.append(goal)
        # Keep only top 5 goals by priority
        state.current_goals.sort(key=lambda g: g.priority, reverse=True)
        state.current_goals = state.current_goals[:5]
        
        self._save_states()
    
    def simulate_time_passage(self, npc_name: str, hours_passed: float,
                               schedule_manager: NPCScheduleManager = None,
                               reputation_propagator: ReputationPropagator = None) -> List[str]:
        """
        Simulate what an NPC did during time passage.
        
        Returns list of notable events/actions.
        """
        state = self.get_or_create_state(npc_name)
        events = []
        
        # Determine what they were doing based on schedule
        activity = "unknown"
        if schedule_manager and npc_name in schedule_manager.schedules:
            current_hour = datetime.now().hour
            schedule = schedule_manager.schedules[npc_name]
            activity_type, location = schedule.get_current_activity(current_hour)
            activity = activity_type.value
        
        # Simulate based on activity and goals
        for goal in state.current_goals:
            progress_rate = 0.1 * hours_passed  # Base progress
            
            # Adjust based on activity alignment
            if goal.goal_type == NPCGoalType.WORK and activity == "working":
                progress_rate *= 2.0
            elif goal.goal_type == NPCGoalType.REST and activity == "sleeping":
                progress_rate *= 2.0
            elif goal.goal_type == NPCGoalType.SOCIALIZE and activity in ["socializing", "leisure"]:
                progress_rate *= 1.5
            
            # Apply progress
            old_progress = goal.progress
            goal.progress = min(1.0, goal.progress + progress_rate)
            
            # Check for goal completion
            if goal.progress >= 1.0 and old_progress < 1.0:
                event = self._generate_goal_completion_event(npc_name, goal)
                if event:
                    events.append(event)
                    state.recent_actions.append(event)
        
        # Update energy based on activity
        if activity == "sleeping":
            state.energy = min(1.0, state.energy + 0.1 * hours_passed)
        elif activity == "working":
            state.energy = max(0.0, state.energy - 0.05 * hours_passed)
        
        # Update mood based on energy and goal progress
        if state.energy < 0.3:
            state.mood = "tired"
        elif any(g.progress > 0.8 for g in state.current_goals):
            state.mood = "happy"
        else:
            state.mood = "neutral"
        
        # Random chance of social interaction
        if random.random() < 0.1 * hours_passed:
            if reputation_propagator:
                connections = reputation_propagator.get_connected_npcs(npc_name)
                if connections:
                    other_npc, conn = random.choice(connections)
                    interaction = self._generate_social_interaction(npc_name, other_npc, conn)
                    if interaction:
                        events.append(interaction)
                        state.recent_actions.append(interaction)
        
        # Keep only last 10 actions
        state.recent_actions = state.recent_actions[-10:]
        state.last_simulated = datetime.now().isoformat()
        
        self._save_states()
        return events
    
    def _generate_goal_completion_event(self, npc_name: str, goal: NPCGoal) -> Optional[str]:
        """Generate an event description for goal completion."""
        
        templates = {
            NPCGoalType.WORK: [
                f"{npc_name} finished their work tasks",
                f"{npc_name} completed a project at work",
            ],
            NPCGoalType.SOCIALIZE: [
                f"{npc_name} spent time with {goal.target}" if goal.target else f"{npc_name} caught up with friends",
                f"{npc_name} had a good conversation with {goal.target}" if goal.target else f"{npc_name} was socializing",
            ],
            NPCGoalType.REST: [
                f"{npc_name} got some much-needed rest",
                f"{npc_name} recovered their energy",
            ],
            NPCGoalType.CONFLICT: [
                f"{npc_name} had a confrontation with {goal.target}" if goal.target else f"{npc_name} dealt with a conflict",
            ],
            NPCGoalType.HELP: [
                f"{npc_name} helped {goal.target} with something" if goal.target else f"{npc_name} helped someone out",
            ],
        }
        
        options = templates.get(goal.goal_type, [f"{npc_name} accomplished something"])
        return random.choice(options)
    
    def _generate_social_interaction(self, npc1: str, npc2: str, 
                                      connection: SocialConnection) -> Optional[str]:
        """Generate a social interaction event."""
        
        if connection.strength >= 3:
            templates = [
                f"{npc1} and {npc2} shared a meal together",
                f"{npc1} helped {npc2} with a task",
                f"{npc1} and {npc2} had a long conversation",
            ]
        elif connection.strength <= 1:
            templates = [
                f"{npc1} and {npc2} exchanged tense words",
                f"{npc1} avoided {npc2}",
                f"There was friction between {npc1} and {npc2}",
            ]
        else:
            templates = [
                f"{npc1} and {npc2} crossed paths briefly",
                f"{npc1} nodded to {npc2} in passing",
            ]
        
        return random.choice(templates)
    
    def get_npc_summary(self, npc_name: str) -> str:
        """Get a summary of what an NPC has been up to."""
        
        if npc_name not in self.npc_states:
            return ""
        
        state = self.npc_states[npc_name]
        
        if not state.recent_actions:
            return ""
        
        # Return most recent notable action
        return state.recent_actions[-1] if state.recent_actions else ""
    
    def get_reunion_context(self, npc_name: str) -> Dict[str, Any]:
        """Get context for when user reunites with an NPC."""
        
        state = self.get_or_create_state(npc_name)
        
        return {
            "mood": state.mood,
            "energy": state.energy,
            "recent_actions": state.recent_actions[-3:],  # Last 3 actions
            "active_goals": [g.goal_type.value for g in state.current_goals if g.progress < 1.0],
            "summary": self.get_npc_summary(npc_name)
        }


# ============================================================================
# WEATHER CONTINUITY SYSTEM
# ============================================================================

class WeatherType(Enum):
    """Types of weather."""
    CLEAR = "clear"
    CLOUDY = "cloudy"
    OVERCAST = "overcast"
    LIGHT_RAIN = "light_rain"
    RAIN = "rain"
    HEAVY_RAIN = "heavy_rain"
    STORM = "storm"
    FOG = "fog"
    SNOW = "snow"
    WIND = "wind"


@dataclass
class WeatherState:
    """Current weather state."""
    weather_type: WeatherType
    intensity: float = 0.5      # 0-1
    wind_speed: float = 0.0     # 0-1 (calm to gale)
    temperature: str = "mild"   # cold, cool, mild, warm, hot
    visibility: str = "normal"  # poor, reduced, normal, good
    
    started_at: str = ""
    expected_duration_hours: float = 4.0
    
    def to_dict(self) -> Dict:
        return {
            'weather_type': self.weather_type.value,
            'intensity': self.intensity,
            'wind_speed': self.wind_speed,
            'temperature': self.temperature,
            'visibility': self.visibility,
            'started_at': self.started_at,
            'expected_duration_hours': self.expected_duration_hours
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WeatherState':
        return cls(
            weather_type=WeatherType(data['weather_type']),
            intensity=data.get('intensity', 0.5),
            wind_speed=data.get('wind_speed', 0.0),
            temperature=data.get('temperature', 'mild'),
            visibility=data.get('visibility', 'normal'),
            started_at=data.get('started_at', ''),
            expected_duration_hours=data.get('expected_duration_hours', 4.0)
        )


class WeatherSystem:
    """
    Manages weather continuity.
    
    Weather persists and evolves naturally:
    - Rain that started 2 hours ago is still raining (or has stopped)
    - Weather transitions smoothly (cloudy -> rain -> clearing)
    - Time of day affects temperature
    """
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.weather_file = self.storage_dir / "weather_state.json"
        
        self.current_weather: Optional[WeatherState] = None
        self.weather_history: List[Dict] = []
        
        self._load_weather()
        
        # Weather transition probabilities
        self.transitions = {
            WeatherType.CLEAR: {
                WeatherType.CLEAR: 0.7,
                WeatherType.CLOUDY: 0.2,
                WeatherType.FOG: 0.05,
                WeatherType.WIND: 0.05,
            },
            WeatherType.CLOUDY: {
                WeatherType.CLOUDY: 0.4,
                WeatherType.CLEAR: 0.2,
                WeatherType.OVERCAST: 0.25,
                WeatherType.LIGHT_RAIN: 0.1,
                WeatherType.FOG: 0.05,
            },
            WeatherType.OVERCAST: {
                WeatherType.OVERCAST: 0.3,
                WeatherType.CLOUDY: 0.2,
                WeatherType.LIGHT_RAIN: 0.3,
                WeatherType.RAIN: 0.15,
                WeatherType.FOG: 0.05,
            },
            WeatherType.LIGHT_RAIN: {
                WeatherType.LIGHT_RAIN: 0.4,
                WeatherType.RAIN: 0.25,
                WeatherType.OVERCAST: 0.2,
                WeatherType.CLOUDY: 0.15,
            },
            WeatherType.RAIN: {
                WeatherType.RAIN: 0.4,
                WeatherType.LIGHT_RAIN: 0.2,
                WeatherType.HEAVY_RAIN: 0.15,
                WeatherType.STORM: 0.1,
                WeatherType.OVERCAST: 0.15,
            },
            WeatherType.HEAVY_RAIN: {
                WeatherType.HEAVY_RAIN: 0.3,
                WeatherType.RAIN: 0.3,
                WeatherType.STORM: 0.2,
                WeatherType.OVERCAST: 0.2,
            },
            WeatherType.STORM: {
                WeatherType.STORM: 0.3,
                WeatherType.HEAVY_RAIN: 0.3,
                WeatherType.RAIN: 0.2,
                WeatherType.OVERCAST: 0.2,
            },
            WeatherType.FOG: {
                WeatherType.FOG: 0.5,
                WeatherType.CLOUDY: 0.3,
                WeatherType.CLEAR: 0.2,
            },
            WeatherType.SNOW: {
                WeatherType.SNOW: 0.6,
                WeatherType.OVERCAST: 0.2,
                WeatherType.CLOUDY: 0.2,
            },
            WeatherType.WIND: {
                WeatherType.WIND: 0.4,
                WeatherType.CLEAR: 0.3,
                WeatherType.CLOUDY: 0.2,
                WeatherType.STORM: 0.1,
            },
        }
    
    def _load_weather(self):
        """Load weather state from disk."""
        if self.weather_file.exists():
            try:
                with open(self.weather_file, 'r') as f:
                    data = json.load(f)
                    if data.get('current'):
                        self.current_weather = WeatherState.from_dict(data['current'])
                    self.weather_history = data.get('history', [])
            except Exception as e:
                print(f"{Color.WARNING}[WEATHER] Failed to load: {e}{Color.RESET}")
    
    def _save_weather(self):
        """Save weather state to disk."""
        try:
            data = {
                'current': self.current_weather.to_dict() if self.current_weather else None,
                'history': self.weather_history[-20:]  # Keep last 20
            }
            with open(self.weather_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"{Color.WARNING}[WEATHER] Failed to save: {e}{Color.RESET}")
    
    def get_current_weather(self) -> WeatherState:
        """Get current weather, initializing if needed."""
        
        if self.current_weather is None:
            self.current_weather = WeatherState(
                weather_type=WeatherType.CLEAR,
                started_at=datetime.now().isoformat(),
                expected_duration_hours=random.uniform(2, 8)
            )
            self._save_weather()
        
        return self.current_weather
    
    def update_weather(self, hours_passed: float = 0) -> Optional[str]:
        """
        Update weather based on time passage.
        
        Returns description of weather change if any.
        """
        weather = self.get_current_weather()
        
        # Check if weather should change
        try:
            started = datetime.fromisoformat(weather.started_at)
            elapsed = (datetime.now() - started).total_seconds() / 3600
            elapsed += hours_passed
            
            if elapsed >= weather.expected_duration_hours:
                # Time for weather to potentially change
                return self._transition_weather()
        except Exception:
            pass
        
        return None
    
    def _transition_weather(self) -> Optional[str]:
        """Transition to new weather state."""
        
        old_weather = self.current_weather.weather_type
        
        # Get transition probabilities
        probs = self.transitions.get(old_weather, {WeatherType.CLEAR: 1.0})
        
        # Weighted random selection
        types = list(probs.keys())
        weights = [probs[t] for t in types]
        new_type = random.choices(types, weights=weights)[0]
        
        if new_type != old_weather:
            # Record history
            self.weather_history.append({
                'type': old_weather.value,
                'ended_at': datetime.now().isoformat()
            })
            
            # Create new weather
            self.current_weather = WeatherState(
                weather_type=new_type,
                intensity=random.uniform(0.3, 0.8),
                wind_speed=random.uniform(0.1, 0.6) if new_type in [WeatherType.STORM, WeatherType.WIND] else random.uniform(0, 0.3),
                started_at=datetime.now().isoformat(),
                expected_duration_hours=random.uniform(1, 6)
            )
            
            self._save_weather()
            
            return self._describe_transition(old_weather, new_type)
        
        # Same weather continues, extend duration
        self.current_weather.expected_duration_hours += random.uniform(1, 3)
        self._save_weather()
        
        return None
    
    def _describe_transition(self, old: WeatherType, new: WeatherType) -> str:
        """Describe a weather transition."""
        
        descriptions = {
            (WeatherType.CLEAR, WeatherType.CLOUDY): "Clouds are rolling in.",
            (WeatherType.CLOUDY, WeatherType.CLEAR): "The clouds are breaking up. Blue sky appears.",
            (WeatherType.CLOUDY, WeatherType.OVERCAST): "The sky darkens as clouds thicken overhead.",
            (WeatherType.OVERCAST, WeatherType.LIGHT_RAIN): "It's starting to rain. Light drops patter down.",
            (WeatherType.LIGHT_RAIN, WeatherType.RAIN): "The rain is picking up.",
            (WeatherType.RAIN, WeatherType.HEAVY_RAIN): "The rain intensifies to a downpour.",
            (WeatherType.HEAVY_RAIN, WeatherType.STORM): "Thunder rumbles. A storm is breaking.",
            (WeatherType.STORM, WeatherType.RAIN): "The storm is passing. Rain continues.",
            (WeatherType.RAIN, WeatherType.LIGHT_RAIN): "The rain is easing off.",
            (WeatherType.LIGHT_RAIN, WeatherType.OVERCAST): "The rain has stopped, but clouds remain.",
            (WeatherType.OVERCAST, WeatherType.CLOUDY): "The sky is lightening.",
            (WeatherType.CLEAR, WeatherType.FOG): "Fog is rolling in, visibility dropping.",
            (WeatherType.FOG, WeatherType.CLEAR): "The fog is lifting.",
        }
        
        return descriptions.get((old, new), f"The weather is changing from {old.value} to {new.value}.")
    
    def get_weather_description(self) -> str:
        """Get a narrative description of current weather."""
        
        weather = self.get_current_weather()
        
        descriptions = {
            WeatherType.CLEAR: "The sky is clear.",
            WeatherType.CLOUDY: "Clouds drift across the sky.",
            WeatherType.OVERCAST: "The sky is a uniform gray.",
            WeatherType.LIGHT_RAIN: "A light rain falls.",
            WeatherType.RAIN: "Rain drums steadily down.",
            WeatherType.HEAVY_RAIN: "Heavy rain sheets down, visibility poor.",
            WeatherType.STORM: "Thunder rumbles. Lightning flashes. Rain lashes down.",
            WeatherType.FOG: "Fog blankets everything, muffling sound.",
            WeatherType.SNOW: "Snow falls silently.",
            WeatherType.WIND: "Wind gusts strongly.",
        }
        
        base = descriptions.get(weather.weather_type, "")
        
        # Add intensity modifier
        if weather.intensity > 0.7:
            if weather.weather_type in [WeatherType.RAIN, WeatherType.HEAVY_RAIN]:
                base += " It's coming down hard."
        
        # Add wind
        if weather.wind_speed > 0.5:
            base += " Strong winds make it worse."
        
        return base
    
    def get_weather_effects(self) -> Dict[str, Any]:
        """Get mechanical effects of current weather."""
        
        weather = self.get_current_weather()
        
        effects = {
            "visibility_modifier": 0,
            "movement_modifier": 0,
            "perception_modifier": 0,
            "comfort": "normal",
            "hazards": []
        }
        
        if weather.weather_type in [WeatherType.FOG, WeatherType.HEAVY_RAIN, WeatherType.STORM]:
            effects["visibility_modifier"] = -2
            effects["perception_modifier"] = -1
        elif weather.weather_type in [WeatherType.RAIN, WeatherType.SNOW]:
            effects["visibility_modifier"] = -1
        
        if weather.weather_type in [WeatherType.STORM, WeatherType.HEAVY_RAIN]:
            effects["movement_modifier"] = -1
            effects["comfort"] = "miserable"
            effects["hazards"].append("slippery surfaces")
        elif weather.weather_type == WeatherType.SNOW:
            effects["movement_modifier"] = -1
            effects["comfort"] = "cold"
        
        if weather.wind_speed > 0.6:
            effects["hazards"].append("flying debris")
        
        return effects


# ============================================================================
# SPATIAL MEMORY SYSTEM
# ============================================================================

@dataclass
class LocationMemory:
    """Memory of a visited location."""
    location_id: str
    location_name: str
    first_visited: float
    last_visited: float
    visit_count: int = 1
    exits: List[str] = field(default_factory=list)
    features: List[str] = field(default_factory=list)
    npcs_seen: List[str] = field(default_factory=list)
    events_witnessed: List[str] = field(default_factory=list)
    connected_to: Dict[str, str] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)


class SpatialMemorySystem:
    """Tracks locations the user has visited and what they learned about them."""
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = storage_dir
        self.memories: Dict[str, LocationMemory] = {}
        self._load()
    
    def _get_location_id(self, location_name: str) -> str:
        return location_name.lower().strip().replace(" ", "_")[:50]
    
    def record_visit(self, location_name: str, scene_description: str = "",
                     npcs_present: List[str] = None) -> LocationMemory:
        loc_id = self._get_location_id(location_name)
        now = time.time()
        
        if loc_id in self.memories:
            memory = self.memories[loc_id]
            memory.last_visited = now
            memory.visit_count += 1
        else:
            memory = LocationMemory(
                location_id=loc_id, location_name=location_name,
                first_visited=now, last_visited=now
            )
            self.memories[loc_id] = memory
        
        if scene_description:
            self._extract_features(memory, scene_description)
        if npcs_present:
            for npc in npcs_present:
                if npc not in memory.npcs_seen:
                    memory.npcs_seen.append(npc)
        
        self._save()
        return memory
    
    def _extract_features(self, memory: LocationMemory, scene_description: str):
        scene_lower = scene_description.lower()
        
        exit_words = ['door', 'entrance', 'exit', 'gate', 'stairs', 'ladder']
        for word in exit_words:
            if word in scene_lower and word not in memory.exits:
                memory.exits.append(word)
        
        feature_words = ['desk', 'table', 'safe', 'computer', 'window', 'bar', 'counter']
        for word in feature_words:
            if word in scene_lower and word not in memory.features:
                memory.features.append(word)
    
    def record_connection(self, from_location: str, exit_used: str, to_location: str):
        from_id = self._get_location_id(from_location)
        if from_id in self.memories:
            self.memories[from_id].connected_to[exit_used] = to_location
            self._save()
    
    def get_location_memory(self, location_name: str) -> Optional[LocationMemory]:
        return self.memories.get(self._get_location_id(location_name))
    
    def get_known_locations(self) -> List[str]:
        return [m.location_name for m in self.memories.values()]
    
    def find_location_with_npc(self, npc_name: str) -> List[str]:
        return [m.location_name for m in self.memories.values()
                if any(npc_name.lower() in n.lower() for n in m.npcs_seen)]
    
    def get_location_summary(self, location_name: str) -> str:
        memory = self.get_location_memory(location_name)
        if not memory:
            return "You haven't been there before."
        
        parts = [f"Visited {memory.visit_count} time(s)."]
        if memory.features:
            parts.append(f"Features: {', '.join(memory.features[:5])}")
        if memory.exits:
            parts.append(f"Exits: {', '.join(memory.exits[:5])}")
        if memory.npcs_seen:
            parts.append(f"Seen: {', '.join(memory.npcs_seen[:5])}")
        return " ".join(parts)
    
    def _save(self):
        os.makedirs(self.storage_dir, exist_ok=True)
        filepath = os.path.join(self.storage_dir, "spatial_memory.json")
        data = {loc_id: {"location_id": m.location_id, "location_name": m.location_name,
                        "first_visited": m.first_visited, "last_visited": m.last_visited,
                        "visit_count": m.visit_count, "exits": m.exits, "features": m.features,
                        "npcs_seen": m.npcs_seen, "connected_to": m.connected_to}
                for loc_id, m in self.memories.items()}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        filepath = os.path.join(self.storage_dir, "spatial_memory.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for loc_id, d in data.items():
                    self.memories[loc_id] = LocationMemory(
                        location_id=d.get("location_id", loc_id),
                        location_name=d.get("location_name", loc_id),
                        first_visited=d.get("first_visited", 0),
                        last_visited=d.get("last_visited", 0),
                        visit_count=d.get("visit_count", 1),
                        exits=d.get("exits", []), features=d.get("features", []),
                        npcs_seen=d.get("npcs_seen", []),
                        connected_to=d.get("connected_to", {}))
            except Exception:
                pass


# ============================================================================
# SOUND PROPAGATION SYSTEM
# ============================================================================

class SoundType(Enum):
    WHISPER = "whisper"
    CONVERSATION = "conversation"
    SHOUT = "shout"
    FOOTSTEPS = "footsteps"
    DOOR = "door"
    GUNSHOT = "gunshot"
    EXPLOSION = "explosion"
    ALARM = "alarm"
    FIGHT = "fight"
    SCREAM = "scream"


@dataclass
class ActiveSound:
    sound_id: str
    sound_type: SoundType
    source_location: str
    source_description: str
    timestamp: float
    intensity: float = 1.0
    duration_seconds: float = 1.0


class SoundPropagationSystem:
    """Tracks sounds and determines what can be heard from other locations."""
    
    SOUND_RANGES = {
        SoundType.WHISPER: 0, SoundType.CONVERSATION: 1, SoundType.SHOUT: 2,
        SoundType.FOOTSTEPS: 1, SoundType.DOOR: 2, SoundType.GUNSHOT: 5,
        SoundType.EXPLOSION: 8, SoundType.ALARM: 6, SoundType.FIGHT: 3,
        SoundType.SCREAM: 4,
    }
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = storage_dir
        self.active_sounds: List[ActiveSound] = []
        self.location_adjacency: Dict[str, List[str]] = {}
        self._load()
    
    def emit_sound(self, sound_type: SoundType, source_location: str,
                   description: str, intensity: float = 1.0, duration: float = 1.0) -> str:
        sound = ActiveSound(
            sound_id=f"sound_{int(time.time() * 1000)}_{random.randint(0, 999)}",
            sound_type=sound_type, source_location=source_location,
            source_description=description, timestamp=time.time(),
            intensity=intensity, duration_seconds=duration
        )
        self.active_sounds.append(sound)
        self._cleanup_old_sounds()
        self._save()
        return sound.sound_id
    
    def set_location_adjacency(self, location: str, adjacent_locations: List[str]):
        self.location_adjacency[location.lower()] = [l.lower() for l in adjacent_locations]
        self._save()
    
    def get_distance(self, from_location: str, to_location: str) -> int:
        from_lower, to_lower = from_location.lower(), to_location.lower()
        if from_lower == to_lower:
            return 0
        if from_lower in self.location_adjacency:
            if to_lower in self.location_adjacency[from_lower]:
                return 1
        return 10  # Unknown = far
    
    def get_audible_sounds(self, listener_location: str) -> List[Dict[str, Any]]:
        self._cleanup_old_sounds()
        audible = []
        for sound in self.active_sounds:
            distance = self.get_distance(listener_location, sound.source_location)
            max_range = self.SOUND_RANGES.get(sound.sound_type, 2)
            if distance <= int(max_range * sound.intensity):
                clarity = "clear" if distance == 0 else "muffled" if distance == 1 else "distant"
                prefix = "" if distance == 0 else "From nearby, " if distance == 1 else "In the distance, "
                audible.append({
                    "sound_type": sound.sound_type.value,
                    "description": f"{prefix}{sound.source_description}",
                    "clarity": clarity, "distance": distance
                })
        return audible
    
    def get_sounds_description(self, listener_location: str) -> str:
        sounds = self.get_audible_sounds(listener_location)
        if not sounds:
            return ""
        return " ".join([f"You hear {s['description']}." for s in sounds])
    
    def _cleanup_old_sounds(self):
        now = time.time()
        self.active_sounds = [s for s in self.active_sounds
                              if now - s.timestamp < s.duration_seconds + 30]
    
    def _save(self):
        os.makedirs(self.storage_dir, exist_ok=True)
        filepath = os.path.join(self.storage_dir, "sound_system.json")
        data = {"adjacency": self.location_adjacency,
                "active_sounds": [{"sound_id": s.sound_id, "sound_type": s.sound_type.value,
                                   "source_location": s.source_location,
                                   "source_description": s.source_description,
                                   "timestamp": s.timestamp, "intensity": s.intensity,
                                   "duration_seconds": s.duration_seconds}
                                  for s in self.active_sounds]}

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        filepath = os.path.join(self.storage_dir, "sound_system.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                self.location_adjacency = data.get("adjacency", {})
                for s in data.get("active_sounds", []):
                    try:
                        self.active_sounds.append(ActiveSound(
                            sound_id=s["sound_id"], sound_type=SoundType(s["sound_type"]),
                            source_location=s["source_location"],
                            source_description=s["source_description"],
                            timestamp=s["timestamp"], intensity=s.get("intensity", 1.0),
                            duration_seconds=s.get("duration_seconds", 1.0)))
                    except Exception:
                        pass
            except Exception:
                pass


# ============================================================================
# NPC MEMORY OF USER SYSTEM
# ============================================================================

@dataclass
class InteractionMemory:
    """Memory of a specific interaction with the user."""
    interaction_id: str
    timestamp: float
    interaction_type: str  # "helped", "threatened", "talked", "fought", "traded"
    description: str
    emotional_impact: str  # "grateful", "angry", "neutral", "fearful"
    importance: int  # 1-5
    location: str = ""


class NPCMemoryOfUser:
    """Tracks what NPCs remember about their interactions with the user."""
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = storage_dir
        self.memories: Dict[str, List[InteractionMemory]] = {}
        self._load()
    
    def record_interaction(self, npc_name: str, interaction_type: str,
                          description: str, emotional_impact: str = "neutral",
                          importance: int = 2, location: str = "") -> InteractionMemory:
        memory = InteractionMemory(
            interaction_id=f"int_{int(time.time() * 1000)}",
            timestamp=time.time(), interaction_type=interaction_type,
            description=description, emotional_impact=emotional_impact,
            importance=importance, location=location
        )
        if npc_name not in self.memories:
            self.memories[npc_name] = []
        self.memories[npc_name].append(memory)
        # Keep top 20 by importance/recency
        if len(self.memories[npc_name]) > 20:
            self.memories[npc_name].sort(key=lambda m: (m.importance, m.timestamp), reverse=True)
            self.memories[npc_name] = self.memories[npc_name][:20]
        self._save()
        return memory
    
    def get_npc_memories(self, npc_name: str) -> List[InteractionMemory]:
        return self.memories.get(npc_name, [])
    
    def get_recent_memories(self, npc_name: str, count: int = 3) -> List[InteractionMemory]:
        return sorted(self.get_npc_memories(npc_name), key=lambda m: m.timestamp, reverse=True)[:count]
    
    def get_emotional_history(self, npc_name: str) -> Dict[str, int]:
        history = {}
        for m in self.get_npc_memories(npc_name):
            history[m.emotional_impact] = history.get(m.emotional_impact, 0) + 1
        return history
    
    def get_greeting_context(self, npc_name: str) -> str:
        memories = self.get_npc_memories(npc_name)
        if not memories:
            return "first_meeting"
        history = self.get_emotional_history(npc_name)
        if history.get("grateful", 0) > history.get("angry", 0):
            return "friendly"
        elif history.get("angry", 0) > history.get("grateful", 0):
            return "hostile"
        elif history.get("fearful", 0) > 2:
            return "nervous"
        return "neutral"
    
    def generate_memory_reference(self, npc_name: str) -> Optional[str]:
        significant = [m for m in self.get_npc_memories(npc_name) if m.importance >= 3]
        if not significant:
            return None
        memory = random.choice(significant)
        templates = {
            "grateful": f"I still remember when you {memory.description}.",
            "angry": f"I haven't forgotten what you did - {memory.description}.",
            "fearful": f"Please... last time you {memory.description}...",
            "neutral": f"We met before, when you {memory.description}.",
        }
        return templates.get(memory.emotional_impact, templates["neutral"])
    
    def _save(self):
        os.makedirs(self.storage_dir, exist_ok=True)
        filepath = os.path.join(self.storage_dir, "npc_user_memories.json")
        data = {npc: [{"interaction_id": m.interaction_id, "timestamp": m.timestamp,
                       "interaction_type": m.interaction_type, "description": m.description,
                       "emotional_impact": m.emotional_impact, "importance": m.importance,
                       "location": m.location} for m in mems]
                for npc, mems in self.memories.items()}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        filepath = os.path.join(self.storage_dir, "npc_user_memories.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for npc, mems in data.items():
                    self.memories[npc] = [InteractionMemory(
                        interaction_id=m.get("interaction_id", ""),
                        timestamp=m.get("timestamp", 0),
                        interaction_type=m.get("interaction_type", ""),
                        description=m.get("description", ""),
                        emotional_impact=m.get("emotional_impact", "neutral"),
                        importance=m.get("importance", 2),
                        location=m.get("location", "")) for m in mems]
            except Exception:
                pass


# ============================================================================
# RUMOR SYSTEM
# ============================================================================

@dataclass
class Rumor:
    """A piece of information spreading through the world."""
    rumor_id: str
    original_fact: str
    current_version: str
    subject: str
    origin_npc: str
    timestamp: float
    spread_count: int = 0
    distortion_level: float = 0.0
    believers: List[str] = field(default_factory=list)


class RumorSystem:
    """Tracks information spreading through NPC networks, with distortion."""
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = storage_dir
        self.rumors: Dict[str, Rumor] = {}
        self._load()
    
    def create_rumor(self, fact: str, subject: str, origin_npc: str) -> Rumor:
        rumor = Rumor(
            rumor_id=f"rumor_{int(time.time() * 1000)}",
            original_fact=fact, current_version=fact, subject=subject,
            origin_npc=origin_npc, timestamp=time.time(), believers=[origin_npc]
        )
        self.rumors[rumor.rumor_id] = rumor
        self._save()

        # Best-effort: persist rumor creation as everlasting context
        try:
            _wps_log_world_event(
                event_type='RUMOR_CREATED',
                summary=f"Rumor started by {origin_npc} about {subject}: {fact}",
                payload={
                    'rumor_id': rumor.rumor_id,
                    'original_fact': rumor.original_fact,
                    'current_version': rumor.current_version,
                    'subject': subject,
                    'origin_npc': origin_npc,
                },
                importance=6,
                tags=['rumor', 'info'],
                actor_names=[origin_npc, subject]
            )
        except Exception:
            pass

        return rumor
    
    def spread_rumor(self, rumor_id: str, from_npc: str, to_npc: str,
                     distort: bool = True) -> Optional[str]:
        if rumor_id not in self.rumors:
            return None
        rumor = self.rumors[rumor_id]
        if to_npc in rumor.believers:
            return rumor.current_version
        rumor.spread_count += 1
        rumor.believers.append(to_npc)
        if distort and random.random() < 0.3:
            rumor.current_version = self._distort(rumor.current_version)
            rumor.distortion_level = min(1.0, rumor.distortion_level + 0.2)
        self._save()

        # Best-effort: persist rumor spread as info learned by recipient
        try:
            _wps_log_world_event(
                event_type='INFO_LEARNED',
                summary=f"{to_npc} learned a rumor from {from_npc}: {rumor.current_version}",
                payload={
                    'rumor_id': rumor.rumor_id,
                    'from_npc': from_npc,
                    'to_npc': to_npc,
                    'subject': rumor.subject,
                    'distorted': bool(distort),
                    'distortion_level': float(rumor.distortion_level),
                    'rumor_text': rumor.current_version,
                },
                importance=5,
                tags=['rumor', 'info_learned'],
                actor_names=[to_npc, from_npc, rumor.subject]
            )
        except Exception:
            pass

        return rumor.current_version
    
    def _distort(self, text: str) -> str:
        distortions = [("helped", "saved their life"), ("hurt", "nearly killed"),
                       ("stole", "robbed everything"), ("attacked", "had a disagreement with")]
        for orig, repl in distortions:
            if orig in text.lower():
                return text.lower().replace(orig, repl)
        prefixes = ["I heard that ", "They say ", "Word is "]
        return random.choice(prefixes) + text
    
    def get_rumors_about(self, subject: str) -> List[Rumor]:
        return [r for r in self.rumors.values() if subject.lower() in r.subject.lower()]
    
    def get_rumors_known_by(self, npc_name: str) -> List[Rumor]:
        return [r for r in self.rumors.values() if npc_name in r.believers]
    
    def npc_shares_rumor(self, npc_name: str, about_subject: str = None) -> Optional[str]:
        known = self.get_rumors_known_by(npc_name)
        if about_subject:
            known = [r for r in known if about_subject.lower() in r.subject.lower()]
        if not known:
            return None
        rumor = random.choice(known)
        intros = ["I heard that ", "Word on the street is ", "People are saying "]
        return f"{random.choice(intros)}{rumor.current_version}"
    
    def _save(self):
        os.makedirs(self.storage_dir, exist_ok=True)
        filepath = os.path.join(self.storage_dir, "rumors.json")
        data = {rid: {"rumor_id": r.rumor_id, "original_fact": r.original_fact,
                      "current_version": r.current_version, "subject": r.subject,
                      "origin_npc": r.origin_npc, "timestamp": r.timestamp,
                      "spread_count": r.spread_count, "distortion_level": r.distortion_level,
                      "believers": r.believers} for rid, r in self.rumors.items()}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        filepath = os.path.join(self.storage_dir, "rumors.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for rid, d in data.items():
                    self.rumors[rid] = Rumor(
                        rumor_id=d.get("rumor_id", rid), original_fact=d.get("original_fact", ""),
                        current_version=d.get("current_version", ""), subject=d.get("subject", ""),
                        origin_npc=d.get("origin_npc", ""), timestamp=d.get("timestamp", 0),
                        spread_count=d.get("spread_count", 0),
                        distortion_level=d.get("distortion_level", 0),
                        believers=d.get("believers", []))
            except Exception:
                pass


# ============================================================================
# FACTION/GROUP DYNAMICS SYSTEM
# ============================================================================

@dataclass
class Faction:
    """A group or organization with collective opinions."""
    faction_id: str
    name: str
    description: str
    members: List[str] = field(default_factory=list)
    leader: str = ""
    reputation: int = 0  # -100 to +100
    allies: List[str] = field(default_factory=list)
    enemies: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)


class FactionSystem:
    """Manages group dynamics and collective opinions."""
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = storage_dir
        self.factions: Dict[str, Faction] = {}
        self._load()
    
    def create_faction(self, name: str, description: str = "", members: List[str] = None,
                       leader: str = "", values: List[str] = None) -> Faction:
        faction = Faction(
            faction_id=f"faction_{name.lower().replace(' ', '_')}",
            name=name, description=description, members=members or [],
            leader=leader, values=values or []
        )
        self.factions[faction.faction_id] = faction
        self._save()
        return faction
    
    def add_member(self, faction_id: str, npc_name: str):
        if faction_id in self.factions and npc_name not in self.factions[faction_id].members:
            self.factions[faction_id].members.append(npc_name)
            self._save()
    
    def get_npc_factions(self, npc_name: str) -> List[Faction]:
        return [f for f in self.factions.values() if npc_name in f.members]
    
    def modify_faction_reputation(self, faction_id: str, change: int) -> int:
        if faction_id not in self.factions:
            return 0
        faction = self.factions[faction_id]
        faction.reputation = max(-100, min(100, faction.reputation + change))
        # Propagate to allies/enemies
        for ally_id in faction.allies:
            if ally_id in self.factions:
                self.factions[ally_id].reputation = max(-100, min(100,
                    self.factions[ally_id].reputation + change // 2))
        for enemy_id in faction.enemies:
            if enemy_id in self.factions:
                self.factions[enemy_id].reputation = max(-100, min(100,
                    self.factions[enemy_id].reputation - change // 2))
        self._save()
        return faction.reputation
    
    def modify_reputation_via_member(self, npc_name: str, change: int) -> List[Dict[str, Any]]:
        changes = []
        for faction in self.get_npc_factions(npc_name):
            scaled = change * 2 if npc_name == faction.leader else change
            new_rep = self.modify_faction_reputation(faction.faction_id, scaled)
            changes.append({"faction": faction.name, "change": scaled, "new_reputation": new_rep})

            # Best-effort: persist faction reputation changes
            try:
                _wps_log_world_event(
                    event_type='FACTION_REPUTATION_CHANGED',
                    summary=f"Faction reputation changed via {npc_name}: {faction.name} ({scaled:+d}) -> {new_rep}",
                    payload={
                        'npc_name': npc_name,
                        'faction_id': faction.faction_id,
                        'faction_name': faction.name,
                        'change': int(scaled),
                        'new_reputation': int(new_rep),
                    },
                    importance=5,
                    tags=['faction', 'reputation'],
                    actor_names=[npc_name]
                )
            except Exception:
                pass
        return changes
    
    def get_faction_standing(self, faction_id: str) -> str:
        if faction_id not in self.factions:
            return "unknown"
        rep = self.factions[faction_id].reputation
        if rep >= 75: return "revered"
        elif rep >= 50: return "respected"
        elif rep >= 25: return "friendly"
        elif rep >= -25: return "neutral"
        elif rep >= -50: return "disliked"
        elif rep >= -75: return "hostile"
        return "hated"
    
    def get_member_attitude_modifier(self, npc_name: str) -> int:
        factions = self.get_npc_factions(npc_name)
        if not factions:
            return 0
        avg_rep = sum(f.reputation for f in factions) // len(factions)
        return avg_rep // 33  # -3 to +3
    
    def _save(self):
        os.makedirs(self.storage_dir, exist_ok=True)
        filepath = os.path.join(self.storage_dir, "factions.json")
        data = {fid: {"faction_id": f.faction_id, "name": f.name, "description": f.description,
                      "members": f.members, "leader": f.leader, "reputation": f.reputation,
                      "allies": f.allies, "enemies": f.enemies, "values": f.values}
                for fid, f in self.factions.items()}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        filepath = os.path.join(self.storage_dir, "factions.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for fid, d in data.items():
                    self.factions[fid] = Faction(
                        faction_id=d.get("faction_id", fid), name=d.get("name", ""),
                        description=d.get("description", ""), members=d.get("members", []),
                        leader=d.get("leader", ""), reputation=d.get("reputation", 0),
                        allies=d.get("allies", []), enemies=d.get("enemies", []),
                        values=d.get("values", []))
            except Exception:
                pass


# ============================================================================
# SOCIAL OBLIGATIONS SYSTEM
# ============================================================================

@dataclass
class SocialObligation:
    """A promise, debt, or favor owed."""
    obligation_id: str
    obligation_type: str  # "promise", "debt", "favor_owed"
    from_party: str
    to_party: str
    description: str
    created_timestamp: float
    deadline: Optional[float] = None
    status: str = "active"  # "active", "fulfilled", "broken", "expired"
    reputation_if_fulfilled: int = 5
    reputation_if_broken: int = -10


class SocialObligationSystem:
    """Tracks promises, debts, and favors between user and NPCs."""
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = storage_dir
        self.obligations: Dict[str, SocialObligation] = {}
        self._load()
    
    def create_promise(self, from_party: str, to_party: str, description: str,
                       deadline: float = None) -> SocialObligation:
        ob = SocialObligation(
            obligation_id=f"promise_{int(time.time() * 1000)}",
            obligation_type="promise", from_party=from_party, to_party=to_party,
            description=description, created_timestamp=time.time(), deadline=deadline,
            reputation_if_fulfilled=5, reputation_if_broken=-15
        )
        self.obligations[ob.obligation_id] = ob
        self._save()

        # Best-effort: persist promise creation
        try:
            _wps_log_world_event(
                event_type='OBLIGATION_CREATED',
                summary=f"Promise created: {from_party} -> {to_party}: {description}",
                payload={
                    'obligation_id': ob.obligation_id,
                    'obligation_type': ob.obligation_type,
                    'from_party': from_party,
                    'to_party': to_party,
                    'description': description,
                    'deadline': deadline,
                },
                importance=7,
                tags=['obligation', 'promise'],
                actor_names=[from_party, to_party]
            )
        except Exception:
            pass

        return ob
    
    def create_favor(self, owed_by: str, owed_to: str, description: str) -> SocialObligation:
        ob = SocialObligation(
            obligation_id=f"favor_{int(time.time() * 1000)}",
            obligation_type="favor_owed", from_party=owed_by, to_party=owed_to,
            description=description, created_timestamp=time.time(),
            reputation_if_fulfilled=3, reputation_if_broken=-5
        )
        self.obligations[ob.obligation_id] = ob
        self._save()

        # Best-effort: persist favor creation
        try:
            _wps_log_world_event(
                event_type='OBLIGATION_CREATED',
                summary=f"Favor owed: {owed_by} -> {owed_to}: {description}",
                payload={
                    'obligation_id': ob.obligation_id,
                    'obligation_type': ob.obligation_type,
                    'from_party': owed_by,
                    'to_party': owed_to,
                    'description': description,
                },
                importance=6,
                tags=['obligation', 'favor'],
                actor_names=[owed_by, owed_to]
            )
        except Exception:
            pass

        return ob
    
    def fulfill_obligation(self, obligation_id: str) -> Dict[str, Any]:
        if obligation_id not in self.obligations:
            return {"error": "Not found"}
        ob = self.obligations[obligation_id]
        ob.status = "fulfilled"
        self._save()

        # Best-effort: persist fulfillment
        try:
            _wps_log_world_event(
                event_type='OBLIGATION_FULFILLED',
                summary=f"Obligation fulfilled: {ob.from_party} -> {ob.to_party}: {ob.description}",
                payload={
                    'obligation_id': ob.obligation_id,
                    'obligation_type': ob.obligation_type,
                    'from_party': ob.from_party,
                    'to_party': ob.to_party,
                    'description': ob.description,
                    'reputation_change': ob.reputation_if_fulfilled,
                },
                importance=7,
                tags=['obligation'],
                actor_names=[ob.from_party, ob.to_party]
            )
        except Exception:
            pass

        return {"description": ob.description, "reputation_change": ob.reputation_if_fulfilled}
    
    def break_obligation(self, obligation_id: str) -> Dict[str, Any]:
        if obligation_id not in self.obligations:
            return {"error": "Not found"}
        ob = self.obligations[obligation_id]
        ob.status = "broken"
        self._save()

        # Best-effort: persist broken promise
        try:
            _wps_log_world_event(
                event_type='OBLIGATION_BROKEN',
                summary=f"Obligation broken: {ob.from_party} -> {ob.to_party}: {ob.description}",
                payload={
                    'obligation_id': ob.obligation_id,
                    'obligation_type': ob.obligation_type,
                    'from_party': ob.from_party,
                    'to_party': ob.to_party,
                    'description': ob.description,
                    'reputation_change': ob.reputation_if_broken,
                },
                importance=8,
                tags=['obligation'],
                actor_names=[ob.from_party, ob.to_party]
            )
        except Exception:
            pass

        return {"description": ob.description, "reputation_change": ob.reputation_if_broken}
    
    def get_obligations_from(self, party: str) -> List[SocialObligation]:
        return [o for o in self.obligations.values()
                if o.from_party.lower() == party.lower() and o.status == "active"]
    
    def get_obligations_to(self, party: str) -> List[SocialObligation]:
        return [o for o in self.obligations.values()
                if o.to_party.lower() == party.lower() and o.status == "active"]
    
    def npc_reminds_of_obligation(self, npc_name: str) -> Optional[str]:
        obligations = [o for o in self.obligations.values()
                      if o.to_party.lower() == npc_name.lower() and
                      o.from_party.lower() == "user" and o.status == "active"]
        if not obligations:
            return None
        ob = random.choice(obligations)
        templates = [f"You promised you'd {ob.description}. Remember?",
                     f"I'm still waiting for you to {ob.description}."]
        return random.choice(templates)
    
    def _save(self):
        os.makedirs(self.storage_dir, exist_ok=True)
        filepath = os.path.join(self.storage_dir, "obligations.json")
        data = {oid: {"obligation_id": o.obligation_id, "obligation_type": o.obligation_type,
                      "from_party": o.from_party, "to_party": o.to_party,
                      "description": o.description, "created_timestamp": o.created_timestamp,
                      "deadline": o.deadline, "status": o.status,
                      "reputation_if_fulfilled": o.reputation_if_fulfilled,
                      "reputation_if_broken": o.reputation_if_broken}
                for oid, o in self.obligations.items()}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        filepath = os.path.join(self.storage_dir, "obligations.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for oid, d in data.items():
                    self.obligations[oid] = SocialObligation(
                        obligation_id=d.get("obligation_id", oid),
                        obligation_type=d.get("obligation_type", "promise"),
                        from_party=d.get("from_party", ""),
                        to_party=d.get("to_party", ""),
                        description=d.get("description", ""),
                        created_timestamp=d.get("created_timestamp", 0),
                        deadline=d.get("deadline"),
                        status=d.get("status", "active"),
                        reputation_if_fulfilled=d.get("reputation_if_fulfilled", 5),
                        reputation_if_broken=d.get("reputation_if_broken", -10))
            except Exception:
                pass


# ============================================================================
# CALENDAR/SEASONAL EVENTS SYSTEM
# ============================================================================

@dataclass
class CalendarEvent:
    """A scheduled event in the world."""
    event_id: str
    name: str
    description: str
    event_type: str  # "weekly", "monthly", "yearly", "one_time"
    day_of_week: Optional[int] = None  # 0=Monday
    day_of_month: Optional[int] = None
    month: Optional[int] = None
    hour: int = 12
    duration_hours: float = 1.0
    affected_locations: List[str] = field(default_factory=list)
    world_effects: Dict[str, Any] = field(default_factory=dict)
    narrative_additions: List[str] = field(default_factory=list)


class CalendarSystem:
    """Manages scheduled world events - holidays, paydays, regular occurrences."""
    
    DEFAULT_EVENTS = [
        {"event_id": "sunday_rest", "name": "Sunday Rest", "event_type": "weekly",
         "day_of_week": 6, "hour": 0, "duration_hours": 24,
         "world_effects": {"shops_closed": True}, 
         "narrative_additions": ["It's Sunday - the streets are quieter than usual."]},
        {"event_id": "friday_payday", "name": "Payday", "event_type": "weekly",
         "day_of_week": 4, "hour": 17, "duration_hours": 6,
         "world_effects": {"bars_busy": True},
         "narrative_additions": ["It's Friday evening - people are out spending their paychecks."]},
        {"event_id": "market_day", "name": "Market Day", "event_type": "weekly",
         "day_of_week": 2, "hour": 8, "duration_hours": 10,
         "affected_locations": ["market", "square"],
         "world_effects": {"crowds": True},
         "narrative_additions": ["The weekly market is in full swing."]},
    ]
    
    def __init__(self, storage_dir: str = "./simulation_data/world_state"):
        self.storage_dir = storage_dir
        self.events: Dict[str, CalendarEvent] = {}
        self._load()
        self._ensure_defaults()
    
    def _ensure_defaults(self):
        for evt in self.DEFAULT_EVENTS:
            if evt["event_id"] not in self.events:
                self.events[evt["event_id"]] = CalendarEvent(
                    event_id=evt["event_id"], name=evt["name"], description=evt.get("description", ""),
                    event_type=evt["event_type"], day_of_week=evt.get("day_of_week"),
                    day_of_month=evt.get("day_of_month"), month=evt.get("month"),
                    hour=evt.get("hour", 12), duration_hours=evt.get("duration_hours", 1),
                    affected_locations=evt.get("affected_locations", []),
                    world_effects=evt.get("world_effects", {}),
                    narrative_additions=evt.get("narrative_additions", [])
                )
        self._save()
    
    def add_event(self, name: str, event_type: str, description: str = "",
                  day_of_week: int = None, hour: int = 12, duration: float = 1,
                  effects: Dict = None, narratives: List[str] = None) -> CalendarEvent:
        evt = CalendarEvent(
            event_id=f"event_{name.lower().replace(' ', '_')}",
            name=name, description=description, event_type=event_type,
            day_of_week=day_of_week, hour=hour, duration_hours=duration,
            world_effects=effects or {}, narrative_additions=narratives or []
        )
        self.events[evt.event_id] = evt
        self._save()
        return evt
    
    def get_active_events(self, day_of_week: int, hour: int, month: int = 1,
                          day_of_month: int = 1) -> List[CalendarEvent]:
        active = []
        for evt in self.events.values():
            if evt.event_type == "weekly" and evt.day_of_week == day_of_week:
                if evt.hour <= hour < evt.hour + evt.duration_hours:
                    active.append(evt)
            elif evt.event_type == "monthly" and evt.day_of_month == day_of_month:
                if evt.hour <= hour < evt.hour + evt.duration_hours:
                    active.append(evt)
        return active
    
    def get_world_effects(self, day_of_week: int, hour: int) -> Dict[str, Any]:
        effects = {}
        for evt in self.get_active_events(day_of_week, hour):
            effects.update(evt.world_effects)
        return effects
    
    def get_narrative_additions(self, day_of_week: int, hour: int) -> List[str]:
        additions = []
        for evt in self.get_active_events(day_of_week, hour):
            additions.extend(evt.narrative_additions)
        return additions
    
    def _save(self):
        os.makedirs(self.storage_dir, exist_ok=True)
        filepath = os.path.join(self.storage_dir, "calendar.json")
        data = {eid: {"event_id": e.event_id, "name": e.name, "description": e.description,
                      "event_type": e.event_type, "day_of_week": e.day_of_week,
                      "day_of_month": e.day_of_month, "month": e.month, "hour": e.hour,
                      "duration_hours": e.duration_hours, "affected_locations": e.affected_locations,
                      "world_effects": e.world_effects, "narrative_additions": e.narrative_additions}
                for eid, e in self.events.items()}
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _load(self):
        filepath = os.path.join(self.storage_dir, "calendar.json")
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                for eid, d in data.items():
                    self.events[eid] = CalendarEvent(
                        event_id=d.get("event_id", eid), name=d.get("name", ""),
                        description=d.get("description", ""), event_type=d.get("event_type", "weekly"),
                        day_of_week=d.get("day_of_week"), day_of_month=d.get("day_of_month"),
                        month=d.get("month"), hour=d.get("hour", 12),
                        duration_hours=d.get("duration_hours", 1),
                        affected_locations=d.get("affected_locations", []),
                        world_effects=d.get("world_effects", {}),
                        narrative_additions=d.get("narrative_additions", []))
            except Exception:
                pass
