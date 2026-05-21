"""
Enhanced Narrative Context System for UTAS

Provides intelligent narrative memory that tracks story continuity, character relationships,
and plot threads with semantic importance weighting. Integrates with the Four-Mode 
Narrative Loop to maintain invisible story scaffolding.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

class NarrativeImportance(Enum):
    """Semantic importance levels for narrative events"""
    CRITICAL = "critical"      # Major plot points, character revelations
    IMPORTANT = "important"    # Significant actions, relationship changes
    NOTABLE = "notable"        # Interesting moments, minor developments
    ROUTINE = "routine"        # Standard actions, filler content

class NarrativeEventType(Enum):
    """Types of narrative events to track"""
    PLOT_ADVANCEMENT = "plot_advancement"
    CHARACTER_DEVELOPMENT = "character_development"
    CHARACTER_INTRODUCTION = "character_introduction"
    CHARACTER_IDENTITY_DISCOVERY = "character_identity_discovery"
    RELATIONSHIP_CHANGE = "relationship_change"
    TENSION_ESCALATION = "tension_escalation"
    TENSION_RESOLUTION = "tension_resolution"
    SCENE_TRANSITION = "scene_transition"
    SCENE_INTRODUCTION = "scene_introduction"
    DIALOGUE_EXCHANGE = "dialogue_exchange"
    ACTION_SEQUENCE = "action_sequence"
    ACTION_OUTCOME = "action_outcome"
    GIVEN_ACTION = "given_action"
    EXPLORATION = "exploration"
    TIME_PASSAGE = "time_passage"
    ATMOSPHERIC_DESCRIPTION = "atmospheric_description"
    INTERNAL_VOICE = "internal_voice"  # Vessel's internal thoughts/memories
    MEMORY_CREATION = "memory_creation"  # Background memory created
    MEMORY_RESURFACING = "memory_resurfacing"  # Existing memory resurfaced

@dataclass
class NarrativeEvent:
    """A single narrative event with context and importance"""
    timestamp: datetime
    event_type: NarrativeEventType
    importance: NarrativeImportance
    summary: str
    full_narrative: str
    actors_involved: List[str]
    emotional_tone: str
    plot_threads: List[str] = field(default_factory=list)
    relationship_changes: Dict[str, int] = field(default_factory=dict)
    narrative_mode: Optional[str] = None
    scene_context: Optional[str] = None

@dataclass
class PlotThread:
    """Ongoing story thread with current status"""
    thread_id: str
    title: str
    description: str
    status: str  # "active", "resolved", "dormant"
    importance: NarrativeImportance
    related_actors: List[str]
    key_events: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    last_updated: datetime = field(default_factory=datetime.now)

@dataclass
class CharacterArc:
    """Character development tracking"""
    character_name: str
    current_emotional_state: str
    goals: List[str]
    conflicts: List[str]
    relationships: Dict[str, str] = field(default_factory=dict)
    key_moments: List[str] = field(default_factory=list)
    development_trajectory: str = ""

class NarrativeContextManager:
    """Manages intelligent narrative context with semantic understanding"""
    
    def __init__(self, session_id: str, storage_directory: Path):
        self.session_id = session_id
        self.storage_directory = storage_directory
        self.logger = logging.getLogger(__name__)
        
        # Core narrative state
        self.events: List[NarrativeEvent] = []
        self.plot_threads: Dict[str, PlotThread] = {}
        self.character_arcs: Dict[str, CharacterArc] = {}
        
        # Context caches for performance
        self._recent_context_cache: Optional[str] = None
        self._cache_timestamp: Optional[datetime] = None
        self._cache_duration_minutes = 5
        
        # Load existing context if available
        self._load_context()
    
    def add_narrative_event(self, 
                          event_type: NarrativeEventType,
                          narrative_text: str,
                          actors_involved: List[str],
                          importance: NarrativeImportance = NarrativeImportance.NOTABLE,
                          emotional_tone: str = "neutral",
                          narrative_mode: Optional[str] = None,
                          scene_context: Optional[str] = None,
                          identity_discoveries: Dict[str, Dict[str, str]] = None) -> str:
        """Add a new narrative event with intelligent categorization"""
        
        # Generate summary from full narrative
        summary = self._generate_event_summary(narrative_text, event_type)
        
        # Detect plot threads and relationship changes
        plot_threads = self._detect_plot_threads(narrative_text, actors_involved)
        relationship_changes = self._detect_relationship_changes(narrative_text, actors_involved)
        
        event = NarrativeEvent(
            timestamp=datetime.now(),
            event_type=event_type,
            importance=importance,
            summary=summary,
            full_narrative=narrative_text,
            actors_involved=actors_involved,
            emotional_tone=emotional_tone,
            plot_threads=plot_threads,
            relationship_changes=relationship_changes,
            narrative_mode=narrative_mode,
            scene_context=scene_context
        )
        
        self.events.append(event)
        
        # Update plot threads and character arcs
        self._update_plot_threads(event)
        self._update_character_arcs(event)
        
        # Process identity discoveries if provided
        if identity_discoveries:
            self._process_identity_discoveries(identity_discoveries)
        
        # Invalidate cache
        self._recent_context_cache = None
        
        # Auto-save periodically
        if len(self.events) % 10 == 0:
            self._save_context()
        
        return f"event_{len(self.events)}"
    
    def detect_identity_revelations(self, narrative_text: str, actors_involved: List[str]) -> Dict[str, Dict[str, str]]:
        """Detect if any character identities are revealed in the narrative"""
        identity_discoveries = {}
        
        # Common patterns for identity revelation
        import re
        
        # Pattern: "My name is [Name]" or "I'm [Name]"
        name_patterns = [
            r"(?:my name is|i'm|i am|call me)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s*(?:is my name|here)",
            r"(?:this is|meet)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)"
        ]
        
        # Pattern: "I work as [occupation]" or "I'm a [occupation]"
        occupation_patterns = [
            r"(?:i work as|i'm a|i am a)\s+([a-z\s]+)",
            r"(?:work as|job is)\s+([a-z\s]+)"
        ]
        
        text_lower = narrative_text.lower()
        
        for pattern in name_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                # Find which actor this might refer to
                for actor_name in actors_involved:
                    if actor_name in ["Unknown Person", "Stranger", "Figure"]:
                        if actor_name not in identity_discoveries:
                            identity_discoveries[actor_name] = {}
                        identity_discoveries[actor_name]['name'] = match.title()
        
        for pattern in occupation_patterns:
            matches = re.findall(pattern, text_lower, re.IGNORECASE)
            for match in matches:
                for actor_name in actors_involved:
                    if actor_name in ["Unknown Person", "Stranger", "Figure"]:
                        if actor_name not in identity_discoveries:
                            identity_discoveries[actor_name] = {}
                        identity_discoveries[actor_name]['occupation'] = match.strip().title()
        
        return identity_discoveries
    
    def _process_identity_discoveries(self, identity_discoveries: Dict[str, Dict[str, str]]):
        """Process discovered identities and track them"""
        for old_name, new_info in identity_discoveries.items():
            # Add identity discovery event
            discovery_text = f"Identity revealed: {old_name} is actually "
            if 'name' in new_info:
                discovery_text += f"{new_info['name']}"
            if 'occupation' in new_info:
                discovery_text += f", a {new_info['occupation']}"
            
            # Create identity discovery event
            self.add_narrative_event(
                event_type=NarrativeEventType.CHARACTER_IDENTITY_DISCOVERY,
                narrative_text=discovery_text,
                actors_involved=[old_name, new_info.get('name', old_name)],
                importance=NarrativeImportance.IMPORTANT,
                emotional_tone="revelatory"
            )
    
    def get_narrative_context_for_llm(self, 
                                    lookback_events: int = 15,
                                    importance_threshold: NarrativeImportance = NarrativeImportance.ROUTINE,
                                    include_character_state: bool = True,
                                    include_plot_threads: bool = True) -> str:
        """Generate intelligent narrative context for LLM prompts"""
        
        # Check cache first
        if (self._recent_context_cache and self._cache_timestamp and 
            (datetime.now() - self._cache_timestamp).total_seconds() < self._cache_duration_minutes * 60):
            return self._recent_context_cache
        
        context_parts = []
        
        # Recent narrative events (importance-weighted)
        recent_events = self._get_recent_important_events(lookback_events, importance_threshold)
        if recent_events:
            context_parts.append("## Recent Story Events")
            for event in recent_events:
                context_parts.append(f"**{event.event_type.value.title()}** ({event.importance.value})")
                context_parts.append(f"- {event.summary}")
                if event.emotional_tone != "neutral":
                    context_parts.append(f"- Tone: {event.emotional_tone}")
                if event.narrative_mode:
                    context_parts.append(f"- Mode: {event.narrative_mode}")
                context_parts.append("")
        
        # Active plot threads
        if include_plot_threads:
            active_threads = [t for t in self.plot_threads.values() if t.status == "active"]
            if active_threads:
                context_parts.append("## Active Plot Threads")
                for thread in sorted(active_threads, key=lambda x: x.importance.value, reverse=True):
                    context_parts.append(f"**{thread.title}** ({thread.importance.value})")
                    context_parts.append(f"- {thread.description}")
                    context_parts.append(f"- Actors: {', '.join(thread.related_actors)}")
                    context_parts.append("")
        
        # Character emotional states and relationships
        if include_character_state:
            if self.character_arcs:
                context_parts.append("## Character States")
                for char_name, arc in self.character_arcs.items():
                    context_parts.append(f"**{char_name}**")
                    context_parts.append(f"- Emotional state: {arc.current_emotional_state}")
                    if arc.goals:
                        context_parts.append(f"- Goals: {', '.join(arc.goals[:2])}")
                    if arc.conflicts:
                        context_parts.append(f"- Conflicts: {', '.join(arc.conflicts[:2])}")
                    context_parts.append("")
        
        context = "\n".join(context_parts)
        
        # Cache the result
        self._recent_context_cache = context
        self._cache_timestamp = datetime.now()
        
        return context
    
    def get_relationship_context(self, actor1: str, actor2: str) -> str:
        """Get specific relationship context between two actors"""
        relationship_events = []
        
        for event in reversed(self.events[-20:]):  # Last 20 events
            if actor1 in event.actors_involved and actor2 in event.actors_involved:
                if event.event_type in [NarrativeEventType.RELATIONSHIP_CHANGE, 
                                      NarrativeEventType.DIALOGUE_EXCHANGE]:
                    relationship_events.append(event)
        
        if not relationship_events:
            return f"No significant recent interactions between {actor1} and {actor2}."
        
        context_parts = [f"## Recent {actor1} ↔ {actor2} Interactions"]
        for event in relationship_events[-3:]:  # Last 3 interactions
            context_parts.append(f"- {event.summary} ({event.emotional_tone})")
        
        return "\n".join(context_parts)
    
    def _get_recent_important_events(self, 
                                   count: int, 
                                   min_importance: NarrativeImportance) -> List[NarrativeEvent]:
        """Get recent events filtered by importance"""
        importance_order = {
            NarrativeImportance.CRITICAL: 4,
            NarrativeImportance.IMPORTANT: 3,
            NarrativeImportance.NOTABLE: 2,
            NarrativeImportance.ROUTINE: 1
        }
        
        min_level = importance_order[min_importance]
        
        # Filter by importance and get recent events
        important_events = [
            event for event in self.events
            if importance_order[event.importance] >= min_level
        ]
        
        return important_events[-count:] if important_events else []
    
    def _generate_event_summary(self, narrative_text: str, event_type: NarrativeEventType) -> str:
        """Generate a concise summary of the narrative event"""
        # Simple extraction - could be enhanced with LLM summarization
        sentences = narrative_text.split('.')
        if sentences:
            # Take first meaningful sentence
            for sentence in sentences:
                if len(sentence.strip()) > 20:
                    return sentence.strip()[:100] + "..."
        
        return narrative_text[:100] + "..." if len(narrative_text) > 100 else narrative_text
    
    def _detect_plot_threads(self, narrative_text: str, actors: List[str]) -> List[str]:
        """Detect which plot threads this event relates to"""
        # Simple keyword matching - could be enhanced with semantic analysis
        related_threads = []
        
        for thread_id, thread in self.plot_threads.items():
            # Check if any thread actors are involved
            if any(actor in thread.related_actors for actor in actors):
                related_threads.append(thread_id)
            
            # Check for thread keywords in narrative
            thread_keywords = thread.description.lower().split()[:5]  # First 5 words as keywords
            if any(keyword in narrative_text.lower() for keyword in thread_keywords):
                related_threads.append(thread_id)
        
        return list(set(related_threads))
    
    def _detect_relationship_changes(self, narrative_text: str, actors: List[str]) -> Dict[str, int]:
        """Detect relationship changes from narrative text"""
        # Simple sentiment analysis - could be enhanced
        changes = {}
        
        positive_indicators = ["smile", "laugh", "agree", "help", "trust", "friend"]
        negative_indicators = ["frown", "anger", "disagree", "betray", "enemy", "hate"]
        
        text_lower = narrative_text.lower()
        
        positive_score = sum(1 for word in positive_indicators if word in text_lower)
        negative_score = sum(1 for word in negative_indicators if word in text_lower)
        
        if positive_score > negative_score:
            for i, actor1 in enumerate(actors):
                for actor2 in actors[i+1:]:
                    changes[f"{actor1}→{actor2}"] = 1
        elif negative_score > positive_score:
            for i, actor1 in enumerate(actors):
                for actor2 in actors[i+1:]:
                    changes[f"{actor1}→{actor2}"] = -1
        
        return changes
    
    def _update_plot_threads(self, event: NarrativeEvent):
        """Update plot threads based on new event"""
        for thread_id in event.plot_threads:
            if thread_id in self.plot_threads:
                thread = self.plot_threads[thread_id]
                thread.key_events.append(f"event_{len(self.events)}")
                thread.last_updated = datetime.now()
    
    def _update_character_arcs(self, event: NarrativeEvent):
        """Update character arcs based on new event"""
        for actor in event.actors_involved:
            if actor not in self.character_arcs:
                self.character_arcs[actor] = CharacterArc(
                    character_name=actor,
                    current_emotional_state=event.emotional_tone,
                    goals=[],
                    conflicts=[]
                )
            
            arc = self.character_arcs[actor]
            arc.current_emotional_state = event.emotional_tone
            arc.key_moments.append(f"event_{len(self.events)}")
            
            # Update relationships
            for other_actor in event.actors_involved:
                if other_actor != actor:
                    relationship_key = f"{actor}→{other_actor}"
                    if relationship_key in event.relationship_changes:
                        change = event.relationship_changes[relationship_key]
                        current = arc.relationships.get(other_actor, "neutral")
                        # Simple relationship state update
                        if change > 0:
                            arc.relationships[other_actor] = "positive"
                        elif change < 0:
                            arc.relationships[other_actor] = "negative"
    
    def _save_context(self):
        """Save narrative context to disk"""
        try:
            context_file = self.storage_directory / "narrative_contexts" / f"context_{self.session_id}.json"
            context_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to serializable format
            data = {
                "session_id": self.session_id,
                "events": [self._event_to_dict(event) for event in self.events],
                "plot_threads": {k: self._thread_to_dict(v) for k, v in self.plot_threads.items()},
                "character_arcs": {k: self._arc_to_dict(v) for k, v in self.character_arcs.items()},
                "saved_at": datetime.now().isoformat()
            }
            
            with open(context_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Saved narrative context with {len(self.events)} events")
            
        except Exception as e:
            self.logger.error(f"Failed to save narrative context: {e}")
    
    def _load_context(self):
        """Load existing narrative context from disk"""
        try:
            context_file = self.storage_directory / "narrative_contexts" / f"context_{self.session_id}.json"
            
            if context_file.exists():
                with open(context_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Restore events
                self.events = [self._dict_to_event(event_data) for event_data in data.get("events", [])]
                
                # Restore plot threads
                self.plot_threads = {
                    k: self._dict_to_thread(v) for k, v in data.get("plot_threads", {}).items()
                }
                
                # Restore character arcs
                self.character_arcs = {
                    k: self._dict_to_arc(v) for k, v in data.get("character_arcs", {}).items()
                }
                
                self.logger.info(f"Loaded narrative context with {len(self.events)} events")
                
        except Exception as e:
            self.logger.warning(f"Could not load narrative context: {e}")
    
    def _event_to_dict(self, event: NarrativeEvent) -> Dict[str, Any]:
        """Convert NarrativeEvent to dictionary"""
        return {
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type.value,
            "importance": event.importance.value,
            "summary": event.summary,
            "full_narrative": event.full_narrative,
            "actors_involved": event.actors_involved,
            "emotional_tone": event.emotional_tone,
            "plot_threads": event.plot_threads,
            "relationship_changes": event.relationship_changes,
            "narrative_mode": event.narrative_mode,
            "scene_context": event.scene_context
        }
    
    def _dict_to_event(self, data: Dict[str, Any]) -> NarrativeEvent:
        """Convert dictionary to NarrativeEvent"""
        return NarrativeEvent(
            timestamp=datetime.fromisoformat(data["timestamp"]),
            event_type=NarrativeEventType(data["event_type"]),
            importance=NarrativeImportance(data["importance"]),
            summary=data["summary"],
            full_narrative=data["full_narrative"],
            actors_involved=data["actors_involved"],
            emotional_tone=data["emotional_tone"],
            plot_threads=data.get("plot_threads", []),
            relationship_changes=data.get("relationship_changes", {}),
            narrative_mode=data.get("narrative_mode"),
            scene_context=data.get("scene_context")
        )
    
    def _thread_to_dict(self, thread: PlotThread) -> Dict[str, Any]:
        """Convert PlotThread to dictionary"""
        return {
            "thread_id": thread.thread_id,
            "title": thread.title,
            "description": thread.description,
            "status": thread.status,
            "importance": thread.importance.value,
            "related_actors": thread.related_actors,
            "key_events": thread.key_events,
            "created_at": thread.created_at.isoformat(),
            "last_updated": thread.last_updated.isoformat()
        }
    
    def _dict_to_thread(self, data: Dict[str, Any]) -> PlotThread:
        """Convert dictionary to PlotThread"""
        return PlotThread(
            thread_id=data["thread_id"],
            title=data["title"],
            description=data["description"],
            status=data["status"],
            importance=NarrativeImportance(data["importance"]),
            related_actors=data["related_actors"],
            key_events=data.get("key_events", []),
            created_at=datetime.fromisoformat(data["created_at"]),
            last_updated=datetime.fromisoformat(data["last_updated"])
        )
    
    def _arc_to_dict(self, arc: CharacterArc) -> Dict[str, Any]:
        """Convert CharacterArc to dictionary"""
        return {
            "character_name": arc.character_name,
            "current_emotional_state": arc.current_emotional_state,
            "goals": arc.goals,
            "conflicts": arc.conflicts,
            "relationships": arc.relationships,
            "key_moments": arc.key_moments,
            "development_trajectory": arc.development_trajectory
        }
    
    def _dict_to_arc(self, data: Dict[str, Any]) -> CharacterArc:
        """Convert dictionary to CharacterArc"""
        return CharacterArc(
            character_name=data["character_name"],
            current_emotional_state=data["current_emotional_state"],
            goals=data.get("goals", []),
            conflicts=data.get("conflicts", []),
            relationships=data.get("relationships", {}),
            key_moments=data.get("key_moments", []),
            development_trajectory=data.get("development_trajectory", "")
        )
    
    def get_context_for_llm(self, lookback_events: int = 5, importance_threshold: str = "notable", key_memories_system=None) -> str:
        """Generate intelligent narrative context for LLM prompts, including memories"""
        try:
            # Convert importance threshold to enum
            threshold_map = {
                "critical": NarrativeImportance.CRITICAL,
                "important": NarrativeImportance.IMPORTANT,
                "notable": NarrativeImportance.NOTABLE,
                "routine": NarrativeImportance.ROUTINE
            }
            min_importance = threshold_map.get(importance_threshold.lower(), NarrativeImportance.NOTABLE)
            
            # Build context string
            context_parts = []
            
            # FIRST: Include memories (most important for consistency)
            if key_memories_system:
                try:
                    from key_memories_system import MemoryImportance as MemImp
                    # Map narrative importance to memory importance
                    mem_importance_map = {
                        NarrativeImportance.ROUTINE: MemImp.ROUTINE,
                        NarrativeImportance.NOTABLE: MemImp.NOTABLE,
                        NarrativeImportance.IMPORTANT: MemImp.IMPORTANT,
                        NarrativeImportance.CRITICAL: MemImp.CRITICAL
                    }
                    mem_importance = mem_importance_map.get(min_importance, MemImp.NOTABLE)
                    
                    memories_context = key_memories_system.get_memories_for_llm(
                        limit=10,
                        min_importance=mem_importance
                    )
                    if memories_context:
                        context_parts.append(memories_context)
                        context_parts.append("")
                except Exception as e:
                    self.logger.error(f"Error getting memories for LLM context: {e}")
            
            # Get recent events above threshold
            recent_events = []
            importance_order = [NarrativeImportance.ROUTINE, NarrativeImportance.NOTABLE, 
                             NarrativeImportance.IMPORTANT, NarrativeImportance.CRITICAL]
            for event in reversed(self.events[-lookback_events:]):
                try:
                    event_idx = importance_order.index(event.importance)
                    min_idx = importance_order.index(min_importance)
                    if event_idx >= min_idx:
                        recent_events.append(event)
                except (ValueError, AttributeError):
                    # If importance is not in list or invalid, skip this event
                    continue
            
            if not recent_events and not context_parts:
                return ""
            
            # Add recent narrative events
            if recent_events:
                context_parts.append("**RECENT NARRATIVE CONTEXT:**")
            
            for i, event in enumerate(recent_events, 1):
                actors_str = ", ".join(event.actors_involved)
                context_parts.append(f"Event {i}: {event.summary}")
                context_parts.append(f"  Actors: {actors_str}")
                context_parts.append(f"  Tone: {event.emotional_tone}")
                if event.narrative_mode:
                    context_parts.append(f"  Mode: {event.narrative_mode}")
                context_parts.append("")
            
            # Add active plot threads
            active_threads = self.get_active_plot_threads()
            if active_threads:
                context_parts.append("**ACTIVE PLOT THREADS:**")
                for thread in active_threads[:3]:  # Limit to top 3
                    context_parts.append(f"- {thread.title}: {thread.description}")
                context_parts.append("")
            
            # Add character development notes
            if self.character_arcs:
                context_parts.append("**CHARACTER DEVELOPMENT:**")
                for name, arc in self.character_arcs.items():
                    if arc.current_emotional_state:
                        context_parts.append(f"- {name}: {arc.current_emotional_state}")
                context_parts.append("")
            
            return "\n".join(context_parts)
            
        except Exception as e:
            self.logger.error(f"Error generating LLM context: {e}")
            return ""
    
    def get_active_plot_threads(self) -> List[PlotThread]:
        """Get currently active plot threads"""
        return [thread for thread in self.plot_threads.values() if thread.status == "active"]
    
    def get_character_arcs(self) -> Dict[str, CharacterArc]:
        """Get all character arcs"""
        return self.character_arcs.copy()
