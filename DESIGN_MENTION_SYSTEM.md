# Mention System Design Document
**Date:** 2026-02-11
**Version:** 1.0
**Status:** Design Phase

---

## Executive Summary

The **Mention System** tracks all actor mentions throughout the simulation to maintain narrative consistency, enable intelligent NPC spawning, and support continuity queries. It acts as the "memory of who was where and when" for the Realitas Neo simulation.

### Problem Statement
Currently, the simulation lacks continuity tracking for actor mentions:
- **"Where was Marcus last seen?"** - No way to query
- **Spawning inconsistency** - Marcus might spawn in the bar when dialogue just said he left
- **Contradictory locations** - NPCs simultaneously in multiple places
- **Lost narrative threads** - "I need to find Marcus" but system doesn't know where to look

### Solution
A centralized Mention System that:
1. **Tracks** all actor mentions with context (present, elsewhere, arriving, departing, etc.)
2. **Records** location and time data for each mention
3. **Queries** mention history ("Where was Marcus last mentioned?")
4. **Validates** spawning decisions (don't spawn NPCs who just left)
5. **Integrates** with SceneNPCParser for intelligent NPC placement

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    MENTION SYSTEM                           │
│                                                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐    │
│  │ Mention      │  │ Query Engine │  │ Spawning     │    │
│  │ Tracker      │  │              │  │ Validator    │    │
│  │              │  │ - Location   │  │              │    │
│  │ - Record     │  │ - Timeline   │  │ - Presence   │    │
│  │ - Index      │  │ - Context    │  │ - Validation │    │
│  │ - Update     │  │ - Proximity  │  │ - Smart      │    │
│  └──────────────┘  └──────────────┘  └──────────────┘    │
└─────────────────────────────────────────────────────────────┘
           │                  │                  │
           ▼                  ▼                  ▼
    ┌─────────────┐    ┌─────────────┐   ┌─────────────┐
    │ Scene NPC   │    │  Spatial    │   │   Fact      │
    │  Parser     │    │  System     │   │   System    │
    └─────────────┘    └─────────────┘   └─────────────┘
           │                  │                  │
           └──────────────────┴──────────────────┘
                           │
                           ▼
                 ┌──────────────────┐
                 │ Narrative Context│
                 │     Manager      │
                 └──────────────────┘
```

---

## Core Components

### 1. Mention Types

```python
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from datetime import datetime

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
```

### 2. Mention Data Model

```python
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
    spatial_position: Optional[tuple]  # (x, y, z) if known

    # Temporal context
    timestamp: datetime              # When mentioned
    turn_number: int                 # Turn number in simulation
    scene_id: Optional[str]          # Scene ID
    world_time: Optional[str]        # In-world time (if tracked)

    # Context details
    mentioned_by: Optional[str]      # Who mentioned them
    context: str                     # Full context text
    intent: Optional[str]            # Intent (if applicable)

    # Metadata
    tags: List[str]                  # Semantic tags
    related_actors: List[str]        # Other actors in context

    # Travel/Movement tracking
    origin: Optional[str] = None     # Where from (if departing/arriving)
    destination: Optional[str] = None  # Where to (if departing/arriving)
    travel_method: Optional[str] = None  # How (car, walking, etc.)

    # Validation
    is_spawnable: bool = True        # Can actor be spawned here?
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

@dataclass
class ActorPresenceState:
    """Current best-known state for an actor's presence"""
    actor_name: str
    last_known_location: Optional[str]
    location_confidence: PresenceConfidence
    last_seen: datetime
    last_mention: ActorMention
    current_activity: Optional[str]  # What they're doing
    is_present: bool                 # In current scene?
    is_spawned: bool                 # Currently spawned in simulation?
    mention_count: int               # Total mentions
    recent_mentions: List[str]       # Recent mention IDs (last 5)
```

### 3. Mention System Class

```python
from pathlib import Path
import json
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

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
        self.storage_directory = storage_directory
        self.mentions_file = storage_directory / f"mentions_{session_id}.json"

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

    def mark_actor_despawned(self, actor_name: str):
        """Mark an actor as no longer spawned."""
        if actor_name in self.actor_states:
            self.actor_states[actor_name].is_spawned = False
            self.actor_states[actor_name].is_present = False

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
                mention = ActorMention(
                    mention_id=mention_data['mention_id'],
                    actor_name=mention_data['actor_name'],
                    mention_type=MentionType(mention_data['mention_type']),
                    source=MentionSource(mention_data['source']),
                    location=mention_data.get('location'),
                    location_confidence=PresenceConfidence(mention_data['location_confidence']),
                    spatial_position=tuple(mention_data['spatial_position']) if mention_data.get('spatial_position') else None,
                    timestamp=datetime.fromisoformat(mention_data['timestamp']),
                    turn_number=mention_data['turn_number'],
                    scene_id=mention_data.get('scene_id'),
                    world_time=mention_data.get('world_time'),
                    mentioned_by=mention_data.get('mentioned_by'),
                    context=mention_data['context'],
                    intent=mention_data.get('intent'),
                    tags=mention_data.get('tags', []),
                    related_actors=mention_data.get('related_actors', []),
                    origin=mention_data.get('origin'),
                    destination=mention_data.get('destination'),
                    travel_method=mention_data.get('travel_method'),
                    is_spawnable=mention_data.get('is_spawnable', True),
                    spawn_blocked_reason=mention_data.get('spawn_blocked_reason')
                )
                self.mentions[mention.mention_id] = mention
                self._index_mention(mention)
                self._update_actor_state(mention)
        except Exception as e:
            print(f"Error loading mentions: {e}")

    def _save_mentions(self):
        """Save mentions to storage."""
        try:
            self.storage_directory.mkdir(parents=True, exist_ok=True)

            data = {
                'session_id': self.session_id,
                'last_updated': datetime.now().isoformat(),
                'mentions': [mention.to_dict() for mention in self.mentions.values()]
            }

            with open(self.mentions_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving mentions: {e}")

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
```

---

## Integration Points

### 1. Scene Generation (CreatorAgent)

**Integration:** Record physical presence from scene descriptions

```python
# In creator_agent.py - after generating scene

# Extract NPCs from scene (existing SceneNPCParser)
npcs_found = scene_npc_parser.extract_npcs_from_scene(scene_description)

# Record physical presence for each
for npc in npcs_found:
    mention_system.record_physical_presence(
        actor_name=npc['name'],
        location=current_location,
        context=scene_description,
        source=MentionSource.SCENE_DESCRIPTION,
        turn_number=turn_number,
        scene_id=scene_id,
        tags=['scene_generation', 'present']
    )
```

### 2. Dialogue Processing (ConductorAgent)

**Integration:** Extract mentions from NPC dialogue

```python
# In conductor_agent.py - after generating NPC dialogue

# Parse dialogue for actor mentions
mentioned_actors = _extract_actor_mentions_from_dialogue(dialogue_text, npc_name)

for mention in mentioned_actors:
    if mention['type'] == 'departing':
        mention_system.record_departure(
            actor_name=mention['actor'],
            origin=current_location,
            destination=mention.get('destination'),
            context=dialogue_text,
            source=MentionSource.NPC_DIALOGUE,
            mentioned_by=npc_name,
            turn_number=turn_number
        )
    elif mention['type'] == 'arriving':
        mention_system.record_arrival(
            actor_name=mention['actor'],
            destination=current_location,
            origin=None,
            context=dialogue_text,
            source=MentionSource.NPC_DIALOGUE,
            mentioned_by=npc_name,
            turn_number=turn_number
        )
    elif mention['type'] == 'elsewhere':
        mention_system.record_mention(
            actor_name=mention['actor'],
            mention_type=MentionType.ELSEWHERE_CURRENT,
            source=MentionSource.NPC_DIALOGUE,
            context=dialogue_text,
            location=mention.get('location'),
            location_confidence=PresenceConfidence.MEDIUM,
            mentioned_by=npc_name,
            turn_number=turn_number
        )
```

### 3. User Input (InterpreterAgent)

**Integration:** Track intentions and inquiries from user input

```python
# In interpreter_agent.py - after detecting action

if action_data['input_type'] == 'inquiry':
    # Check if asking about an actor
    if 'Where is Marcus?' in user_input:
        mention_system.record_mention(
            actor_name='Marcus',
            mention_type=MentionType.INQUIRY,
            source=MentionSource.USER_INPUT,
            context=user_input,
            turn_number=turn_number,
            intent='locate_actor'
        )

        # Query last known location
        location, confidence = mention_system.get_last_known_location('Marcus')
        # Use in response generation

elif 'I go to find' in user_input:
    # User intends to find someone
    target_actor = _extract_target_actor(user_input)
    mention_system.record_mention(
        actor_name=target_actor,
        mention_type=MentionType.INTENTION,
        source=MentionSource.USER_INPUT,
        context=user_input,
        turn_number=turn_number,
        intent='find_actor'
    )
```

### 4. NPC Spawning (SceneNPCParser)

**Integration:** Validate spawning against mention history

```python
# In scene_npc_parser.py - auto_spawn_scene_npcs()

def auto_spawn_scene_npcs(scene_description, current_location, ...):
    """Enhanced with mention system validation"""

    # Extract NPCs (existing logic)
    npcs_found = extract_npcs_from_scene(scene_description)

    for npc_data in npcs_found:
        actor_name = npc_data['name']

        # CHECK MENTION SYSTEM FIRST
        can_spawn, reason = mention_system.can_spawn_at_location(actor_name, current_location)

        if not can_spawn:
            print(f"⚠️ Skipping spawn: {actor_name} - {reason}")
            continue

        # Proceed with spawning (existing logic)
        spawned_npc = spawn_npc(npc_data, ...)

        # Mark as spawned in mention system
        if spawned_npc:
            mention_system.mark_actor_spawned(actor_name)
            mention_system.record_physical_presence(
                actor_name=actor_name,
                location=current_location,
                context=scene_description,
                source=MentionSource.SYSTEM_INFERENCE,
                turn_number=turn_number
            )
```

### 5. Spatial System

**Integration:** Sync spatial positions with mentions

```python
# In spatial_context_system.py

# When actor moves on spatial map
def on_actor_move(actor_name, from_location, to_location):
    """Hook called when actor moves"""

    if from_location:
        mention_system.record_departure(
            actor_name=actor_name,
            origin=from_location,
            destination=to_location,
            context=f"{actor_name} moved from {from_location} to {to_location}",
            source=MentionSource.SYSTEM_INFERENCE
        )

    mention_system.record_arrival(
        actor_name=actor_name,
        destination=to_location,
        origin=from_location,
        context=f"{actor_name} arrived at {to_location}",
        source=MentionSource.SYSTEM_INFERENCE
    )
```

### 6. Fact System

**Integration:** Convert significant mentions to facts

```python
# Bidirectional integration

# Mention → Fact
mention = mention_system.get_recent_mentions('Marcus', count=1)[0]
if mention.mention_type == MentionType.PHYSICAL_PRESENCE:
    fact_system.establish_fact(
        fact_type=FactType.LOCATION_PROPERTY,
        subject='Marcus',
        predicate='last_seen_at',
        value=mention.location,
        authority=FactAuthority.SCENE_DECLARED,
        source=f"mention_{mention.mention_id}",
        tags=['location', 'actor_position']
    )

# Fact → Mention query
# When generating scene, check facts for actor locations
marcus_facts = fact_system.query_facts(subject='Marcus', predicate='last_seen_at')
if marcus_facts:
    # Cross-reference with mention system
    location, confidence = mention_system.get_last_known_location('Marcus')
```

---

## Usage Examples

### Example 1: Physical Presence in Scene

```python
# Scene description mentions Marcus
scene_text = "You enter the studio. Marcus is at the mixing desk, headphones on."

# Record physical presence
mention_system.record_physical_presence(
    actor_name="Marcus",
    location="Studio",
    context=scene_text,
    source=MentionSource.SCENE_DESCRIPTION,
    turn_number=42,
    scene_id="scene_015",
    tags=["marcus", "studio", "present"]
)

# Later: Check if Marcus can spawn at the bar
can_spawn, reason = mention_system.can_spawn_at_location("Marcus", "Bar")
# Returns: (False, "Marcus is currently at Studio")
```

### Example 2: Dialogue Mentions Departure

```python
# NPC says Marcus just left
dialogue = 'Bartender says: "Marcus? He just left, headed to the studio I think."'

# Record departure
mention_system.record_departure(
    actor_name="Marcus",
    origin="Bar",
    destination="Studio",
    context=dialogue,
    source=MentionSource.NPC_DIALOGUE,
    mentioned_by="Bartender",
    turn_number=43
)

# Immediately after: Try to spawn Marcus at bar
can_spawn, reason = mention_system.can_spawn_at_location("Marcus", "Bar")
# Returns: (False, "Marcus just left Bar")
```

### Example 3: User Asks About Location

```python
# User: "Where is Marcus?"
user_input = "Where is Marcus?"

# Record inquiry
mention_system.record_mention(
    actor_name="Marcus",
    mention_type=MentionType.INQUIRY,
    source=MentionSource.USER_INPUT,
    context=user_input,
    turn_number=44,
    intent="locate_actor"
)

# Query last known location
location, confidence = mention_system.get_last_known_location("Marcus")
# Returns: ("Studio", PresenceConfidence.HIGH)

# Generate response
response = f"Last you heard, Marcus was at the {location}."
```

### Example 4: Smart NPC Spawning

```python
# User goes to studio
user_action = "I head to the studio"

# Get spawn candidates
candidates = mention_system.get_spawn_candidates("Studio", max_candidates=5)
# Returns: ["Marcus"] (because he was mentioned as going there)

# Spawn Marcus at studio
for actor_name in candidates:
    spawn_npc(actor_name, "Studio")
    mention_system.mark_actor_spawned(actor_name)
```

### Example 5: Timeline Query

```python
# Get Marcus's movement history
marcus_mentions = mention_system.query_mentions(
    actor_name="Marcus",
    mention_type=MentionType.PHYSICAL_PRESENCE,
    limit=10
)

# Display timeline
for mention in marcus_mentions:
    print(f"Turn {mention.turn_number}: {mention.location} - {mention.context[:50]}...")

# Output:
# Turn 45: Studio - Marcus at mixing desk...
# Turn 40: Bar - Marcus sits at the bar...
# Turn 35: Street - Marcus leans against his car...
```

---

## Implementation Phases

### Phase 1: Core Infrastructure (Priority: HIGH)
**Estimated Effort:** 4-6 hours

1. ✅ Create `mention_system.py` with core classes
2. ✅ Implement mention recording and indexing
3. ✅ Implement basic querying
4. ✅ Add persistence (JSON storage)
5. ✅ Write unit tests

**Deliverables:**
- `mention_system.py` - Core system
- `test_mention_system.py` - Unit tests
- Storage directory: `sessions/{session_id}/mentions/`

### Phase 2: Integration (Priority: HIGH)
**Estimated Effort:** 6-8 hours

1. ✅ Integrate with SceneNPCParser (spawning validation)
2. ✅ Integrate with CreatorAgent (scene generation)
3. ✅ Integrate with ConductorAgent (dialogue parsing)
4. ✅ Integrate with InterpreterAgent (user input tracking)
5. ✅ Create mention_system singleton in redesigned_main.py

**Deliverables:**
- Modified scene_npc_parser.py with validation
- Dialogue mention extraction
- User input tracking

### Phase 3: LLM-Based Extraction (Priority: MEDIUM)
**Estimated Effort:** 4-6 hours

1. ✅ Create `_extract_actor_mentions_from_dialogue()` LLM function
2. ✅ Implement mention type classification (departing/arriving/elsewhere)
3. ✅ Add destination/origin extraction
4. ✅ Integrate with narrative generation

**Deliverables:**
- Automatic mention extraction from text
- Smart mention type classification

### Phase 4: Advanced Features (Priority: LOW)
**Estimated Effort:** 3-4 hours

1. ✅ Timeline visualization commands
2. ✅ Actor tracking dashboard
3. ✅ Mention-based fact establishment
4. ✅ Spatial system integration

**Deliverables:**
- User commands for querying mentions
- Enhanced continuity tracking

---

## LLM Helper: Dialogue Mention Extraction

```python
def _extract_actor_mentions_from_dialogue(dialogue_text: str,
                                         speaker_name: str,
                                         current_location: str) -> List[Dict[str, Any]]:
    """
    Use LLM to extract actor mentions from dialogue.

    Returns list of mention dictionaries with:
    - actor: actor name
    - type: 'present', 'departing', 'arriving', 'elsewhere', 'rumor'
    - location: mentioned location
    - destination: where they're going (if departing/arriving)
    - confidence: how certain (high/medium/low)
    """

    prompt = f"""
Analyze this dialogue for actor mentions:

**Speaker:** {speaker_name}
**Current Location:** {current_location}
**Dialogue:** "{dialogue_text}"

**Task:** Extract all mentioned actors and their presence context.

**Mention Types:**
- **present**: Actor is here now (e.g., "Marcus is right over there")
- **departing**: Actor is leaving/just left (e.g., "Marcus just left", "He's heading out")
- **arriving**: Actor is coming/about to arrive (e.g., "Here comes Marcus", "Marcus is on his way")
- **elsewhere**: Actor is at a different location (e.g., "Marcus is at the studio")
- **rumor**: Heard about actor indirectly (e.g., "I heard Marcus was around")

**Response Format (JSON):**
[
  {{
    "actor": "actor name",
    "type": "present|departing|arriving|elsewhere|rumor",
    "location": "location name (if mentioned)",
    "destination": "where going (if departing/arriving)",
    "confidence": "high|medium|low"
  }}
]

If no actor mentions, return: []
"""

    response = llm.generate(prompt, response_format='json')
    return json.loads(response)
```

---

## Testing Strategy

### Unit Tests

```python
def test_record_physical_presence():
    """Test basic physical presence recording"""
    ms = MentionSystem("test_session", Path("test_data"))

    mention_id = ms.record_physical_presence(
        actor_name="Marcus",
        location="Studio",
        context="Marcus is at the mixing desk",
        turn_number=1
    )

    assert mention_id is not None
    assert len(ms.mentions) == 1

    # Check state
    state = ms.get_actor_state("Marcus")
    assert state.last_known_location == "Studio"
    assert state.is_present == True

def test_departure_blocks_spawning():
    """Test that departure blocks immediate spawning"""
    ms = MentionSystem("test_session", Path("test_data"))

    # Marcus present at bar
    ms.record_physical_presence("Marcus", "Bar", "Marcus at bar", turn_number=1)

    # Marcus leaves
    ms.record_departure("Marcus", "Bar", "Studio", "Marcus leaves", turn_number=2)

    # Try to spawn at bar
    can_spawn, reason = ms.can_spawn_at_location("Marcus", "Bar")
    assert can_spawn == False
    assert "just left" in reason.lower()

def test_last_known_location():
    """Test location tracking"""
    ms = MentionSystem("test_session", Path("test_data"))

    ms.record_physical_presence("Marcus", "Bar", "At bar", turn_number=1)
    ms.record_departure("Marcus", "Bar", "Studio", "Leaves", turn_number=2)
    ms.record_arrival("Marcus", "Studio", "Bar", "Arrives", turn_number=3)

    location, confidence = ms.get_last_known_location("Marcus")
    assert location == "Studio"
    assert confidence == PresenceConfidence.HIGH

def test_spawn_candidates():
    """Test spawn candidate retrieval"""
    ms = MentionSystem("test_session", Path("test_data"))

    # Marcus arriving at studio
    ms.record_arrival("Marcus", "Studio", "Bar", "Arrives", turn_number=1)

    # Linda present at studio
    ms.record_physical_presence("Linda", "Studio", "Linda here", turn_number=1)

    candidates = ms.get_spawn_candidates("Studio")
    assert "Marcus" in candidates
    assert "Linda" in candidates
```

### Integration Tests
- Test mention extraction from scene descriptions
- Test dialogue parsing for actor mentions
- Test spawning validation in SceneNPCParser
- Test cross-system consistency (Mention + Fact)

### Scenario Tests
- **Scenario 1:** Actor movement tracking across multiple locations
- **Scenario 2:** Dialogue-driven presence updates
- **Scenario 3:** User inquiry about actor location
- **Scenario 4:** Smart spawning based on mention history

---

## Performance Considerations

### Indexing Strategy
- **Actor index**: Fast lookup by actor name
- **Location index**: Fast lookup by location
- **Turn index**: Timeline queries
- **Type index**: Filter by mention type

### Query Optimization
- Cache actor states (updated on new mentions)
- Limit query results by default (50 mentions)
- Use indexes for all queries

### Storage Optimization
- JSON for simplicity
- Archive old mentions (>100 turns old)
- Compress mention context for long-running sessions

---

## Open Questions & Future Enhancements

### Q1: How long should departure blocks last?
**Current:** Indefinitely until new mention
**Consideration:** Add time decay? After 5 turns, allow spawning again?

### Q2: Should mentions affect NPC behavior?
**Example:** If someone mentions Marcus is at studio, should NPCs know?
**Proposed:** Create "knowledge graph" - who knows what

### Q3: How to handle contradictory mentions?
**Example:** NPC A says "Marcus is at bar", NPC B says "Marcus is at studio"
**Proposed:** Track confidence, source reliability

### Q4: Integration with travel time?
**Example:** Marcus leaves bar for studio - how long until arrival?
**Proposed:** Calculate travel time based on spatial distance

---

## Success Metrics

After implementation:
1. **Zero contradictory spawns** - No actor in two places at once
2. **Continuity queries work** - "Where is Marcus?" answered correctly
3. **Smart spawning** - NPCs appear where they should be
4. **Departure tracking** - NPCs don't spawn immediately after leaving
5. **Timeline coherence** - Actor movements make narrative sense
6. **Query performance** - <10ms for location queries

---

## File Structure

```
mention_system.py              # Core system
test_mention_system.py        # Unit tests
sessions/
  {session_id}/
    mentions/
      mentions_{session_id}.json  # Mention database
      actor_states.json           # Current actor states
      mention_archive.json        # Old mentions (optional)
```

---

## Status: READY FOR IMPLEMENTATION

This design document is complete and ready for Phase 1 implementation.

**Next Steps:**
1. Review and approve design
2. Create `mention_system.py` skeleton
3. Implement Phase 1 (Core Infrastructure)
4. Write unit tests
5. Begin Phase 2 (Integration with SceneNPCParser)

**Estimated Total Time:** 17-24 hours across all phases

---

## Appendix: Mention Type Decision Matrix

| User/NPC Says | Mention Type | Spawnable? | Location Update? |
|---------------|-------------|------------|------------------|
| "Marcus is right here" | PHYSICAL_PRESENCE | ✅ Yes | ✅ Confirmed |
| "Marcus just left" | DEPARTING | ❌ No | ✅ Origin marked |
| "Here comes Marcus" | ARRIVING | ✅ Yes | ✅ Destination |
| "Marcus is at the bar" | ELSEWHERE_CURRENT | ❌ No | ✅ At bar |
| "Marcus was here yesterday" | ELSEWHERE_PAST | ❌ No | ⚠️ Old info |
| "I got a call from Marcus" | MESSAGE | ❌ No | ❌ No location |
| "I heard Marcus is in town" | RUMOR | ❌ No | ⚠️ Low confidence |
| "Where is Marcus?" | INQUIRY | ❌ No | ❌ No info |
| "I'm going to find Marcus" | INTENTION | ❌ No | ❌ No info |
| "I remember when Marcus..." | MEMORY | ❌ No | ❌ Past event |
