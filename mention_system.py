"""
Mention System for UTAS Simulation

Tracks all actor mentions throughout the simulation to maintain narrative consistency,
enable intelligent NPC spawning, and support continuity queries.

This system acts as the "memory of who was where and when" for the Realitas Neo simulation.

Author: Claude Sonnet 4.5
Date: 2026-02-12
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
from collections import defaultdict


class MentionType(Enum):
    """Types of actor mentions"""
    PHYSICAL_PRESENCE = "physical_presence"      # Actor is physically present
    ARRIVING = "arriving"                        # Actor is arriving/approaching
    DEPARTING = "departing"                      # Actor is leaving/has left
    ELSEWHERE_CURRENT = "elsewhere_current"      # Actor is somewhere else (now)
    ELSEWHERE_PAST = "elsewhere_past"            # Actor was somewhere (past)
    MEMORY = "memory"                            # Actor mentioned in memory/flashback
    MESSAGE = "message"                          # Actor mentioned in message/call
    RUMOR = "rumor"                              # Actor mentioned in gossip/hearsay
    INQUIRY = "inquiry"                          # Someone asking about actor
    INTENTION = "intention"                      # Intent to meet/find actor


class MentionSource(Enum):
    """Source of the mention"""
    SCENE_DESCRIPTION = "scene_description"      # Scene narration
    NPC_DIALOGUE = "npc_dialogue"                # NPC speech
    USER_INPUT = "user_input"                    # User action/speech
    NARRATIVE = "narrative"                      # System narration
    INTERNAL_THOUGHT = "internal_thought"        # UA's thoughts
    SYSTEM_INFERENCE = "system_inference"        # Inferred by system


class PresenceConfidence(Enum):
    """Confidence level for location presence"""
    CONFIRMED = "confirmed"          # Definitely present (seen in scene)
    HIGH = "high"                    # Very likely (reliable source)
    MEDIUM = "medium"                # Probably (indirect evidence)
    LOW = "low"                      # Uncertain (rumor, old info)
    UNKNOWN = "unknown"              # No location data


@dataclass
class ActorMention:
    """A single mention of an actor in the simulation"""
    mention_id: str                  # Unique identifier
    actor_name: str                  # Who is mentioned
    mention_type: MentionType        # Type of mention
    source: MentionSource            # Where it came from

    # Location context
    location: Optional[str]          # Where mentioned (if applicable)
    location_confidence: PresenceConfidence  # How sure are we?
    spatial_position: Optional[tuple] = None  # (x, y, z) if known

    # Temporal context
    timestamp: datetime = field(default_factory=datetime.now)
    turn_number: int = 0
    scene_id: Optional[str] = None
    world_time: Optional[str] = None

    # Context details
    mentioned_by: Optional[str] = None  # Who mentioned them
    context: str = ""                   # Full context text
    intent: Optional[str] = None        # Intent (if applicable)

    # Metadata
    tags: List[str] = field(default_factory=list)
    related_actors: List[str] = field(default_factory=list)

    # Travel/Movement tracking
    origin: Optional[str] = None            # Where from (if departing/arriving)
    destination: Optional[str] = None       # Where to (if departing/arriving)
    travel_method: Optional[str] = None     # How (car, walking, etc.)

    # Validation
    is_spawnable: bool = True               # Can actor be spawned here?
    spawn_blocked_reason: Optional[str] = None  # Why not spawnable?

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'mention_id': self.mention_id,
            'actor_name': self.actor_name,
            'mention_type': self.mention_type.value,
            'source': self.source.value,
            'location': self.location,
            'location_confidence': self.location_confidence.value,
            'spatial_position': self.spatial_position,
            'timestamp': self.timestamp.isoformat(),
            'turn_number': self.turn_number,
            'scene_id': self.scene_id,
            'world_time': self.world_time,
            'mentioned_by': self.mentioned_by,
            'context': self.context,
            'intent': self.intent,
            'tags': self.tags,
            'related_actors': self.related_actors,
            'origin': self.origin,
            'destination': self.destination,
            'travel_method': self.travel_method,
            'is_spawnable': self.is_spawnable,
            'spawn_blocked_reason': self.spawn_blocked_reason
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ActorMention':
        """Create from dictionary"""
        return ActorMention(
            mention_id=data['mention_id'],
            actor_name=data['actor_name'],
            mention_type=MentionType(data['mention_type']),
            source=MentionSource(data['source']),
            location=data.get('location'),
            location_confidence=PresenceConfidence(data['location_confidence']),
            spatial_position=tuple(data['spatial_position']) if data.get('spatial_position') else None,
            timestamp=datetime.fromisoformat(data['timestamp']),
            turn_number=data.get('turn_number', 0),
            scene_id=data.get('scene_id'),
            world_time=data.get('world_time'),
            mentioned_by=data.get('mentioned_by'),
            context=data.get('context', ''),
            intent=data.get('intent'),
            tags=data.get('tags', []),
            related_actors=data.get('related_actors', []),
            origin=data.get('origin'),
            destination=data.get('destination'),
            travel_method=data.get('travel_method'),
            is_spawnable=data.get('is_spawnable', True),
            spawn_blocked_reason=data.get('spawn_blocked_reason')
        )


@dataclass
class ActorPresenceState:
    """Current best-known state for an actor's presence"""
    actor_name: str
    last_known_location: Optional[str]
    location_confidence: PresenceConfidence
    last_seen: datetime
    last_mention: ActorMention
    current_activity: Optional[str] = None  # What they're doing
    is_present: bool = False                # In current scene?
    is_spawned: bool = False                # Currently spawned in simulation?
    mention_count: int = 0                  # Total mentions
    recent_mentions: List[str] = field(default_factory=list)  # Recent mention IDs (last 5)


class MentionSystem:
    """
    Central mention tracking system for Realitas Neo.

    Responsibilities:
    - Track all actor mentions with context
    - Query mention history (where, when, by whom)
    - Determine current actor presence state
    - Validate spawning decisions
    - Support continuity queries
    """

    def __init__(self, session_id: str, storage_directory: Path):
        self.session_id = session_id
        self.storage_directory = Path(storage_directory)
        self.mentions_dir = self.storage_directory / "mentions"
        self.mentions_file = self.mentions_dir / f"mentions_{session_id}.json"
        self.logger = logging.getLogger(__name__)

        # Core storage
        self.mentions: Dict[str, ActorMention] = {}  # mention_id -> ActorMention

        # Indexes for fast lookup
        self.mentions_by_actor: Dict[str, List[str]] = defaultdict(list)  # actor -> mention_ids
        self.mentions_by_location: Dict[str, List[str]] = defaultdict(list)  # location -> mention_ids
        self.mentions_by_turn: Dict[int, List[str]] = defaultdict(list)  # turn -> mention_ids
        self.mentions_by_type: Dict[MentionType, List[str]] = defaultdict(list)  # type -> mention_ids

        # Current state tracking
        self.actor_states: Dict[str, ActorPresenceState] = {}  # actor -> state

        # Load existing mentions
        self._load_mentions()

    # ═════════════════════════════════════════════════════════════════
    # MENTION RECORDING
    # ═════════════════════════════════════════════════════════════════

    def record_mention(self,
                      actor_name: str,
                      mention_type: MentionType,
                      source: MentionSource,
                      context: str,
                      location: Optional[str] = None,
                      location_confidence: PresenceConfidence = PresenceConfidence.MEDIUM,
                      mentioned_by: Optional[str] = None,
                      turn_number: int = 0,
                      scene_id: Optional[str] = None,
                      tags: List[str] = None,
                      **kwargs) -> str:
        """
        Record a new mention of an actor.

        Args:
            actor_name: Name of actor mentioned
            mention_type: Type of mention
            source: Source of mention
            context: Full context text
            location: Location where mentioned
            location_confidence: How confident are we?
            mentioned_by: Who mentioned them
            turn_number: Current turn number
            scene_id: Current scene ID
            tags: Semantic tags
            **kwargs: Additional fields (origin, destination, intent, etc.)

        Returns:
            mention_id of recorded mention
        """
        mention_id = self._generate_mention_id()

        # Determine spawnability
        is_spawnable, spawn_blocked_reason = self._determine_spawnability(
            actor_name, mention_type, location, source
        )

        mention = ActorMention(
            mention_id=mention_id,
            actor_name=actor_name,
            mention_type=mention_type,
            source=source,
            location=location,
            location_confidence=location_confidence,
            spatial_position=kwargs.get('spatial_position'),
            timestamp=datetime.now(),
            turn_number=turn_number,
            scene_id=scene_id,
            world_time=kwargs.get('world_time'),
            mentioned_by=mentioned_by,
            context=context,
            intent=kwargs.get('intent'),
            tags=tags or [],
            related_actors=kwargs.get('related_actors', []),
            origin=kwargs.get('origin'),
            destination=kwargs.get('destination'),
            travel_method=kwargs.get('travel_method'),
            is_spawnable=is_spawnable,
            spawn_blocked_reason=spawn_blocked_reason
        )

        # Store mention
        self.mentions[mention_id] = mention
        self._index_mention(mention)

        # Update actor state
        self._update_actor_state(mention)

        # Save to disk
        self._save_mentions()

        self.logger.info(f"Recorded mention: {actor_name} ({mention_type.value}) at {location}")

        return mention_id

    def record_physical_presence(self,
                                actor_name: str,
                                location: str,
                                context: str,
                                source: MentionSource = MentionSource.SCENE_DESCRIPTION,
                                **kwargs) -> str:
        """
        Convenience method for recording physical presence.

        This is the highest confidence mention type.
        """
        return self.record_mention(
            actor_name=actor_name,
            mention_type=MentionType.PHYSICAL_PRESENCE,
            source=source,
            context=context,
            location=location,
            location_confidence=PresenceConfidence.CONFIRMED,
            **kwargs
        )

    def record_departure(self,
                        actor_name: str,
                        origin: str,
                        destination: Optional[str],
                        context: str,
                        source: MentionSource = MentionSource.NARRATIVE,
                        **kwargs) -> str:
        """
        Record an actor leaving a location.

        This blocks spawning at origin location temporarily.
        """
        return self.record_mention(
            actor_name=actor_name,
            mention_type=MentionType.DEPARTING,
            source=source,
            context=context,
            location=origin,
            origin=origin,
            destination=destination,
            location_confidence=PresenceConfidence.HIGH,
            **kwargs
        )

    def record_arrival(self,
                      actor_name: str,
                      destination: str,
                      origin: Optional[str],
                      context: str,
                      source: MentionSource = MentionSource.NARRATIVE,
                      **kwargs) -> str:
        """
        Record an actor arriving at a location.

        This enables spawning at destination.
        """
        return self.record_mention(
            actor_name=actor_name,
            mention_type=MentionType.ARRIVING,
            source=source,
            context=context,
            location=destination,
            origin=origin,
            destination=destination,
            location_confidence=PresenceConfidence.HIGH,
            **kwargs
        )

    # ═════════════════════════════════════════════════════════════════
    # QUERYING
    # ═════════════════════════════════════════════════════════════════

    def get_actor_state(self, actor_name: str) -> Optional[ActorPresenceState]:
        """
        Get current best-known state for an actor.

        Returns:
            ActorPresenceState or None if never mentioned
        """
        return self.actor_states.get(actor_name)

    def get_last_known_location(self, actor_name: str) -> Tuple[Optional[str], PresenceConfidence]:
        """
        Get last known location for an actor.

        Returns:
            (location, confidence) tuple
        """
        state = self.get_actor_state(actor_name)
        if state:
            return state.last_known_location, state.location_confidence
        return None, PresenceConfidence.UNKNOWN

    def query_mentions(self,
                      actor_name: Optional[str] = None,
                      location: Optional[str] = None,
                      mention_type: Optional[MentionType] = None,
                      source: Optional[MentionSource] = None,
                      turn_range: Optional[Tuple[int, int]] = None,
                      limit: int = 50) -> List[ActorMention]:
        """
        Query mentions by various criteria.

        Args:
            actor_name: Filter by actor
            location: Filter by location
            mention_type: Filter by type
            source: Filter by source
            turn_range: Filter by turn range (min, max)
            limit: Maximum results

        Returns:
            List of matching mentions (most recent first)
        """
        results = set()

        # Start with relevant index
        if actor_name:
            results = set(self.mentions_by_actor.get(actor_name, []))
        elif location:
            results = set(self.mentions_by_location.get(location, []))
        elif mention_type:
            results = set(self.mentions_by_type.get(mention_type, []))
        else:
            results = set(self.mentions.keys())

        # Filter by additional criteria
        filtered = []
        for mention_id in results:
            mention = self.mentions[mention_id]

            if actor_name and mention.actor_name != actor_name:
                continue
            if location and mention.location != location:
                continue
            if mention_type and mention.mention_type != mention_type:
                continue
            if source and mention.source != source:
                continue
            if turn_range:
                if mention.turn_number < turn_range[0] or mention.turn_number > turn_range[1]:
                    continue

            filtered.append(mention)

        # Sort by timestamp (most recent first)
        filtered.sort(key=lambda m: m.timestamp, reverse=True)

        return filtered[:limit]

    def get_recent_mentions(self, actor_name: str, count: int = 5) -> List[ActorMention]:
        """Get N most recent mentions of an actor."""
        return self.query_mentions(actor_name=actor_name, limit=count)

    def get_mentions_by_location(self, location: str, limit: int = 20) -> List[ActorMention]:
        """Get all mentions associated with a location."""
        return self.query_mentions(location=location, limit=limit)

    def get_actors_in_location(self, location: str,
                               only_present: bool = True) -> List[Tuple[str, PresenceConfidence]]:
        """
        Get list of actors mentioned in a location.

        Args:
            location: Location to query
            only_present: If True, only return PHYSICAL_PRESENCE mentions

        Returns:
            List of (actor_name, confidence) tuples
        """
        if only_present:
            mentions = self.query_mentions(
                location=location,
                mention_type=MentionType.PHYSICAL_PRESENCE,
                limit=100
            )
        else:
            mentions = self.query_mentions(location=location, limit=100)

        # Group by actor, keep highest confidence
        actor_confidences = {}
        for mention in mentions:
            if mention.actor_name not in actor_confidences:
                actor_confidences[mention.actor_name] = mention.location_confidence
            else:
                # Keep higher confidence
                current = actor_confidences[mention.actor_name]
                if self._confidence_value(mention.location_confidence) > self._confidence_value(current):
                    actor_confidences[mention.actor_name] = mention.location_confidence

        return list(actor_confidences.items())

    # ═════════════════════════════════════════════════════════════════
    # SPAWNING VALIDATION
    # ═════════════════════════════════════════════════════════════════

    def can_spawn_at_location(self, actor_name: str, location: str) -> Tuple[bool, Optional[str]]:
        """
        Check if an actor can be spawned at a location.

        Returns:
            (can_spawn, reason_if_blocked) tuple
        """
        state = self.get_actor_state(actor_name)

        if not state:
            # Never mentioned - default to allowing spawn
            return True, None

        # Check if already spawned
        if state.is_spawned:
            return False, f"{actor_name} is already spawned in the simulation"

        # Get recent mentions
        recent = self.get_recent_mentions(actor_name, count=3)

        if not recent:
            return True, None

        latest = recent[0]

        # Check mention type
        if latest.mention_type == MentionType.DEPARTING:
            # Just left - check if enough time passed
            if latest.location == location:
                return False, f"{actor_name} just left {location}"

        elif latest.mention_type == MentionType.ELSEWHERE_CURRENT:
            # Currently elsewhere
            if latest.location != location:
                return False, f"{actor_name} is currently at {latest.location}"

        elif latest.mention_type == MentionType.PHYSICAL_PRESENCE:
            # Already present at different location
            if latest.location and latest.location != location:
                return False, f"{actor_name} is currently at {latest.location}"

        return True, None

    def get_spawn_candidates(self, location: str, max_candidates: int = 5) -> List[str]:
        """
        Get list of actors that SHOULD be spawned at a location.

        This looks for ARRIVING mentions or recent presence.

        Returns:
            List of actor names
        """
        candidates = []

        # Get actors with ARRIVING or PHYSICAL_PRESENCE mentions
        mentions = self.query_mentions(location=location, limit=50)

        seen_actors = set()
        for mention in mentions:
            if mention.actor_name in seen_actors:
                continue

            if mention.mention_type in [MentionType.ARRIVING, MentionType.PHYSICAL_PRESENCE]:
                # Check if spawnable
                can_spawn, _ = self.can_spawn_at_location(mention.actor_name, location)
                if can_spawn:
                    candidates.append(mention.actor_name)
                    seen_actors.add(mention.actor_name)

                    if len(candidates) >= max_candidates:
                        break

        return candidates

    def _determine_spawnability(self,
                               actor_name: str,
                               mention_type: MentionType,
                               location: Optional[str],
                               source: MentionSource) -> Tuple[bool, Optional[str]]:
        """
        Determine if this mention makes actor spawnable.

        Returns:
            (is_spawnable, reason_if_not) tuple
        """
        # Physical presence is always spawnable
        if mention_type == MentionType.PHYSICAL_PRESENCE:
            return True, None

        # Arriving is spawnable
        if mention_type == MentionType.ARRIVING:
            return True, None

        # Departing blocks spawning
        if mention_type == MentionType.DEPARTING:
            return False, "Actor is leaving/has left"

        # Elsewhere blocks spawning at current location
        if mention_type in [MentionType.ELSEWHERE_CURRENT, MentionType.ELSEWHERE_PAST]:
            return False, "Actor is elsewhere"

        # Memory/message/rumor don't enable spawning
        if mention_type in [MentionType.MEMORY, MentionType.MESSAGE, MentionType.RUMOR]:
            return False, "Indirect mention only"

        # Inquiry/intention suggest future presence, not current
        if mention_type in [MentionType.INQUIRY, MentionType.INTENTION]:
            return False, "Intent to find, not current presence"

        return False, "Unknown mention type"

    # ═════════════════════════════════════════════════════════════════
    # STATE MANAGEMENT
    # ═════════════════════════════════════════════════════════════════

    def mark_actor_spawned(self, actor_name: str):
        """Mark an actor as currently spawned in simulation."""
        if actor_name in self.actor_states:
            self.actor_states[actor_name].is_spawned = True
            self.actor_states[actor_name].is_present = True
            self.logger.info(f"Marked {actor_name} as spawned")

    def mark_actor_despawned(self, actor_name: str):
        """Mark an actor as no longer spawned."""
        if actor_name in self.actor_states:
            self.actor_states[actor_name].is_spawned = False
            self.actor_states[actor_name].is_present = False
            self.logger.info(f"Marked {actor_name} as despawned")

    def _update_actor_state(self, mention: ActorMention):
        """Update actor state based on new mention."""
        actor_name = mention.actor_name

        if actor_name not in self.actor_states:
            # Create new state
            self.actor_states[actor_name] = ActorPresenceState(
                actor_name=actor_name,
                last_known_location=mention.location,
                location_confidence=mention.location_confidence,
                last_seen=mention.timestamp,
                last_mention=mention,
                current_activity=None,
                is_present=mention.mention_type == MentionType.PHYSICAL_PRESENCE,
                is_spawned=False,
                mention_count=1,
                recent_mentions=[mention.mention_id]
            )
        else:
            # Update existing state
            state = self.actor_states[actor_name]
            state.mention_count += 1
            state.recent_mentions.insert(0, mention.mention_id)
            state.recent_mentions = state.recent_mentions[:5]  # Keep last 5

            # Update location if higher confidence
            if self._confidence_value(mention.location_confidence) > self._confidence_value(state.location_confidence):
                state.last_known_location = mention.location
                state.location_confidence = mention.location_confidence

            # Update last seen
            if mention.timestamp > state.last_seen:
                state.last_seen = mention.timestamp
                state.last_mention = mention

            # Update presence
            if mention.mention_type == MentionType.PHYSICAL_PRESENCE:
                state.is_present = True
            elif mention.mention_type in [MentionType.DEPARTING, MentionType.ELSEWHERE_CURRENT]:
                state.is_present = False

    def _confidence_value(self, confidence: PresenceConfidence) -> int:
        """Convert confidence to numeric value for comparison."""
        values = {
            PresenceConfidence.CONFIRMED: 5,
            PresenceConfidence.HIGH: 4,
            PresenceConfidence.MEDIUM: 3,
            PresenceConfidence.LOW: 2,
            PresenceConfidence.UNKNOWN: 1
        }
        return values.get(confidence, 0)

    # ═════════════════════════════════════════════════════════════════
    # PERSISTENCE
    # ═════════════════════════════════════════════════════════════════

    def _load_mentions(self):
        """Load mentions from storage."""
        if not self.mentions_file.exists():
            return

        try:
            with open(self.mentions_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for mention_data in data.get('mentions', []):
                mention = ActorMention.from_dict(mention_data)
                self.mentions[mention.mention_id] = mention
                self._index_mention(mention)
                self._update_actor_state(mention)

            self.logger.info(f"Loaded {len(self.mentions)} mentions for session {self.session_id}")

        except Exception as e:
            self.logger.error(f"Error loading mentions: {e}")

    def _save_mentions(self):
        """Save mentions to storage."""
        try:
            self.mentions_dir.mkdir(parents=True, exist_ok=True)

            data = {
                'session_id': self.session_id,
                'last_updated': datetime.now().isoformat(),
                'mentions': [mention.to_dict() for mention in self.mentions.values()]
            }

            with open(self.mentions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

        except Exception as e:
            self.logger.error(f"Error saving mentions: {e}")

    def _index_mention(self, mention: ActorMention):
        """Add mention to indexes."""
        self.mentions_by_actor[mention.actor_name].append(mention.mention_id)
        if mention.location:
            self.mentions_by_location[mention.location].append(mention.mention_id)
        self.mentions_by_turn[mention.turn_number].append(mention.mention_id)
        self.mentions_by_type[mention.mention_type].append(mention.mention_id)

    def _generate_mention_id(self) -> str:
        """Generate unique mention ID."""
        return f"mention_{len(self.mentions)}_{datetime.now().timestamp()}"
