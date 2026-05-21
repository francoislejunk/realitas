"""
NUA Memory Enhancement System for UTAS Simulation

Ensures NUAs remember past interactions, events, and important moments.
Prevents fake signals where NUAs forget being threatened, helped, or witnessing events.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
import json
import re
import logging
from color_utils import Color


class NUAMemory:
    """Stores memories for a single NUA."""
    
    def __init__(self, nua_name: str):
        self.nua_name = nua_name
        self.memories = []
        self.important_events = []
        self.relationships_history = {}
        self.threats_received = []
        self.help_received = []
        self.witnessed_events = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {
            'nua_name': self.nua_name,
            'memories': [
                {
                    **mem,
                    'timestamp': mem['timestamp'].isoformat()
                } for mem in self.memories
            ],
            'important_events': [
                {
                    **event,
                    'timestamp': event['timestamp'].isoformat()
                } for event in self.important_events
            ],
            'relationships_history': self.relationships_history,
            'threats_received': [
                {
                    **threat,
                    'timestamp': threat['timestamp'].isoformat()
                } for threat in self.threats_received
            ],
            'help_received': [
                {
                    **help_mem,
                    'timestamp': help_mem['timestamp'].isoformat()
                } for help_mem in self.help_received
            ],
            'witnessed_events': [
                {
                    **event,
                    'timestamp': event['timestamp'].isoformat()
                } for event in self.witnessed_events
            ]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NUAMemory':
        """Create from dictionary"""
        memory = cls(data['nua_name'])
        
        # Restore memories with datetime objects
        memory.memories = [
            {
                **mem,
                'timestamp': datetime.fromisoformat(mem['timestamp'])
            } for mem in data.get('memories', [])
        ]
        
        memory.important_events = [
            {
                **event,
                'timestamp': datetime.fromisoformat(event['timestamp'])
            } for event in data.get('important_events', [])
        ]
        
        memory.relationships_history = data.get('relationships_history', {})
        
        memory.threats_received = [
            {
                **threat,
                'timestamp': datetime.fromisoformat(threat['timestamp'])
            } for threat in data.get('threats_received', [])
        ]
        
        memory.help_received = [
            {
                **help_mem,
                'timestamp': datetime.fromisoformat(help_mem['timestamp'])
            } for help_mem in data.get('help_received', [])
        ]
        
        memory.witnessed_events = [
            {
                **event,
                'timestamp': datetime.fromisoformat(event['timestamp'])
            } for event in data.get('witnessed_events', [])
        ]
        
        return memory
    
    def add_memory(
        self,
        memory_type: str,
        description: str,
        actors_involved: List[str],
        importance: int = 3,
        emotional_impact: str = "neutral"
    ):
        """Add a memory to this NUA's memory bank."""
        memory = {
            'type': memory_type,
            'description': description,
            'actors_involved': actors_involved,
            'importance': importance,  # 1-5
            'emotional_impact': emotional_impact,
            'timestamp': datetime.now(),
            'turn_number': len(self.memories) + 1
        }
        
        self.memories.append(memory)
        
        # Track important events separately
        if importance >= 4:
            self.important_events.append(memory)
        
        # Track specific memory types
        if memory_type == "threat":
            self.threats_received.append(memory)
        elif memory_type == "help":
            self.help_received.append(memory)
        elif memory_type == "witnessed":
            self.witnessed_events.append(memory)
    
    def get_memories_about(self, actor_name: str, limit: int = 5) -> List[Dict]:
        """Get memories involving a specific actor."""
        relevant_memories = [
            m for m in self.memories
            if actor_name in m['actors_involved']
        ]
        return relevant_memories[-limit:]
    
    def get_recent_memories(self, limit: int = 5) -> List[Dict]:
        """Get most recent memories."""
        return self.memories[-limit:]
    
    def has_been_threatened_by(self, actor_name: str) -> bool:
        """Check if NPC has been threatened by specific actor."""
        return any(
            actor_name in threat['actors_involved']
            for threat in self.threats_received
        )
    
    def has_been_helped_by(self, actor_name: str) -> bool:
        """Check if NPC has been helped by specific actor."""
        return any(
            actor_name in help_mem['actors_involved']
            for help_mem in self.help_received
        )
    
    def has_witnessed_violence_by(self, actor_name: str) -> bool:
        """Check if NPC has witnessed violence by specific actor."""
        return any(
            actor_name in event['actors_involved'] and 'violence' in event['description'].lower()
            for event in self.witnessed_events
        )
    
    def get_memory_summary(self, actor_name: str = None) -> str:
        """Get summary of memories for LLM context."""
        if actor_name:
            memories = self.get_memories_about(actor_name, 3)
            if not memories:
                return f"{self.nua_name} has no specific memories about {actor_name}."
        else:
            memories = self.get_recent_memories(3)
            if not memories:
                return f"{self.nua_name} has no significant memories."
        
        summary_parts = [f"{self.nua_name}'s MEMORIES:"]
        for mem in memories:
            summary_parts.append(f"  - {mem['description']} (Turn {mem['turn_number']}, {mem['emotional_impact']})")
        
        return "\n".join(summary_parts)


class NUAMemorySystem:
    """
    Manages memories for all NUAs in the simulation.
    
    Features:
    - Tracks important events per NUA
    - Remembers threats, help, violence
    - Provides memory context for decisions
    - Prevents NUAs from forgetting key moments
    - Persists memories to disk across sessions
    """
    
    def __init__(self, storage_directory: Optional[Path] = None):
        self.nua_memories: Dict[str, NUAMemory] = {}
        self.storage_directory = Path(storage_directory) if storage_directory else Path("./simulation_data/nua_memories")
        self.storage_directory.mkdir(parents=True, exist_ok=True)
        self.logger = logging.getLogger(__name__)
        
        # Load existing memories
        self._load_memories()
    
    def get_or_create_memory(self, nua_name: str) -> NUAMemory:
        """Get existing memory or create new one for NUA."""
        if nua_name not in self.nua_memories:
            self.nua_memories[nua_name] = NUAMemory(nua_name)
        return self.nua_memories[nua_name]
    
    def _load_memories(self):
        """Load all NUA memories from disk"""
        memories_file = self.storage_directory / "nua_memories.json"
        
        if memories_file.exists():
            try:
                with open(memories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for nua_name, memory_data in data.get('nua_memories', {}).items():
                    self.nua_memories[nua_name] = NUAMemory.from_dict(memory_data)
                
                self.logger.info(f"Loaded memories for {len(self.nua_memories)} NUAs")
            except Exception as e:
                self.logger.error(f"Error loading NUA memories: {e}")
    
    def _save_memories(self):
        """Save all NUA memories to disk"""
        memories_file = self.storage_directory / "nua_memories.json"
        
        try:
            data = {
                'nua_memories': {
                    nua_name: memory.to_dict()
                    for nua_name, memory in self.nua_memories.items()
                },
                'last_updated': datetime.now().isoformat()
            }
            
            with open(memories_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved memories for {len(self.nua_memories)} NUAs")
        except Exception as e:
            self.logger.error(f"Error saving NUA memories: {e}")
    
    def record_event(
        self,
        nua_name: str,
        event_type: str,
        description: str,
        actors_involved: List[str],
        importance: int = 3,
        emotional_impact: str = "neutral",
        auto_save: bool = True
    ):
        """Record an event in NUA's memory."""
        memory = self.get_or_create_memory(nua_name)
        memory.add_memory(event_type, description, actors_involved, importance, emotional_impact)
        
        # Display memory recording with importance indicator
        importance_emoji = {
            5: "🔴",  # Critical
            4: "🟡",  # Important
            3: "🔵",  # Notable
            2: "⚪",  # Minor
            1: "⚫"   # Trivial
        }
        emoji = importance_emoji.get(importance, "🧠")
        
        # Show all memories with importance >= 3, or high importance ones always
        if importance >= 3:
            print(f"{Color.INFO}{emoji} {nua_name} remembers: {description[:60]}...{Color.RESET}")
        
        # Auto-save to disk
        if auto_save:
            self._save_memories()
            if importance >= 4:  # Confirm save for important memories
                print(f"{Color.SYSTEM}   💾 NUA memory saved to disk{Color.RESET}")
    
    def record_threat(self, nua_name: str, threatener_name: str, threat_description: str, auto_save: bool = True):
        """Record a threat received by NUA."""
        self.record_event(
            nua_name=nua_name,
            event_type="threat",
            description=f"{threatener_name} threatened: {threat_description}",
            actors_involved=[threatener_name],
            importance=4,
            emotional_impact="fearful",
            auto_save=auto_save
        )
    
    def record_help(self, nua_name: str, helper_name: str, help_description: str, auto_save: bool = True):
        """Record help received by NUA."""
        self.record_event(
            nua_name=nua_name,
            event_type="help",
            description=f"{helper_name} helped: {help_description}",
            actors_involved=[helper_name],
            importance=3,
            emotional_impact="grateful",
            auto_save=auto_save
        )
    
    def record_witnessed_violence(
        self,
        nua_name: str,
        perpetrator_name: str,
        victim_name: str,
        violence_description: str,
        auto_save: bool = True
    ):
        """Record violence witnessed by NUA."""
        self.record_event(
            nua_name=nua_name,
            event_type="witnessed",
            description=f"Witnessed {perpetrator_name} commit violence against {victim_name}: {violence_description}",
            actors_involved=[perpetrator_name, victim_name],
            importance=5,
            emotional_impact="traumatized",
            auto_save=auto_save
        )
    
    def record_conversation(
        self,
        nua_name: str,
        other_actor: str,
        topic: str,
        key_points: str,
        auto_save: bool = True
    ):
        """Record a significant conversation."""
        self.record_event(
            nua_name=nua_name,
            event_type="conversation",
            description=f"Discussed {topic} with {other_actor}: {key_points}",
            actors_involved=[other_actor],
            importance=2,
            emotional_impact="neutral",
            auto_save=auto_save
        )
    
    def get_memory_context_for_decision(
        self,
        nua_name: str,
        target_actor: str = None
    ) -> str:
        """Get memory context for NUA decision-making."""
        memory = self.get_or_create_memory(nua_name)

        def _age_seconds(ts: Any) -> Optional[float]:
            try:
                if isinstance(ts, datetime):
                    return (datetime.now() - ts).total_seconds()
            except Exception:
                pass
            return None

        def _decay_text(text: str, age_s: Optional[float]) -> str:
            """Apply deterministic "forgetting" to older memories.

            Recent memories remain detailed; older memories progressively lose precision.
            """
            t = (text or '').strip()
            if not t:
                return ''

            # If we can't compute age, be conservative: return as-is.
            if age_s is None:
                return t

            # Fresh (<= 15 minutes): keep verbatim.
            if age_s <= 15 * 60:
                return t

            # Recent (<= 1 day): keep content but cap length.
            if age_s <= 24 * 60 * 60:
                return t[:220]

            # Medium (<= 2 weeks): remove some precision (numbers/prices) and cap length.
            if age_s <= 14 * 24 * 60 * 60:
                t2 = re.sub(r"\b\d+(?:[\.,]\d+)?\b", "some", t)
                return t2[:170]

            # Old (> 2 weeks): keep gist only.
            t3 = re.sub(r"\b\d+(?:[\.,]\d+)?\b", "some", t)
            # Drop quoted text (often exact wording) to simulate fading.
            t3 = re.sub(r"(['\"]).*?\1", "…", t3)
            return t3[:120]
        
        if not memory.memories:
            return "No significant memories."
        
        context_parts = []
        
        # Get memories about target actor if specified
        if target_actor:
            # Memory decay policy:
            # - very recent memories: include more entries, verbatim
            # - older memories: fewer entries, progressively "faded" details
            relevant_memories = memory.get_memories_about(target_actor, 12)
            if relevant_memories:
                now = datetime.now()

                fresh = []
                recent = []
                faded = []

                # Sort newest->oldest
                for mem in reversed(relevant_memories):
                    age_s = _age_seconds(mem.get('timestamp'))
                    desc = _decay_text(mem.get('description', ''), age_s)
                    if not desc:
                        continue

                    if age_s is not None and age_s <= 15 * 60:
                        minutes = int(max(0, (now - mem['timestamp']).total_seconds()) // 60) if isinstance(mem.get('timestamp'), datetime) else 0
                        fresh.append(f"  - {desc} ({minutes}m ago)")
                    elif age_s is not None and age_s <= 24 * 60 * 60:
                        hours = int(max(0, age_s) // 3600) if age_s is not None else 0
                        recent.append(f"  - {desc} ({hours}h ago)")
                    else:
                        # Keep no relative time here to avoid token bloat.
                        faded.append(f"  - {desc}")

                # Cap output to keep prompts stable.
                if fresh or recent or faded:
                    context_parts.append(f"MEMORIES ABOUT {target_actor}:")
                    if fresh:
                        context_parts.append("RECENT (clear):")
                        context_parts.extend(fresh[:6])
                    if recent:
                        context_parts.append("RECENT (somewhat clear):")
                        context_parts.extend(recent[:4])
                    if faded:
                        context_parts.append("OLDER (faded):")
                        context_parts.extend(faded[:3])
            
            # Check for specific relationship history
            if memory.has_been_threatened_by(target_actor):
                context_parts.append(f"⚠️  {nua_name} remembers being THREATENED by {target_actor}")
            
            if memory.has_been_helped_by(target_actor):
                context_parts.append(f"✓ {nua_name} remembers being HELPED by {target_actor}")
            
            if memory.has_witnessed_violence_by(target_actor):
                context_parts.append(f"👁️  {nua_name} witnessed {target_actor} commit VIOLENCE")
        
        # Add important events
        if memory.important_events:
            context_parts.append("\nIMPORTANT MEMORIES:")
            # Important events also decay, but retain more detail than general memories.
            for event in memory.important_events[-4:]:
                age_s = _age_seconds(event.get('timestamp'))
                desc = _decay_text(event.get('description', ''), age_s)
                if desc:
                    context_parts.append(f"  - {desc}")
        
        return "\n".join(context_parts) if context_parts else "No significant memories."
    
    def should_remember_event(self, event_type: str, severity: int) -> bool:
        """Determine if an event should be remembered."""
        # Always remember high severity events
        if severity >= 4:
            return True
        
        # Always remember threats and violence
        if event_type in ["threat", "violence", "death", "betrayal"]:
            return True
        
        # Remember moderate events
        if severity >= 3 and event_type in ["help", "gift", "promise"]:
            return True
        
        return False
    
    def get_nua_memory_stats(self, nua_name: str) -> Dict[str, Any]:
        """Get statistics about NUA's memories."""
        if nua_name not in self.nua_memories:
            return {
                'total_memories': 0,
                'important_events': 0,
                'threats_received': 0,
                'help_received': 0,
                'witnessed_events': 0
            }
        
        memory = self.nua_memories[nua_name]
        return {
            'total_memories': len(memory.memories),
            'important_events': len(memory.important_events),
            'threats_received': len(memory.threats_received),
            'help_received': len(memory.help_received),
            'witnessed_events': len(memory.witnessed_events)
        }
    
    def display_npc_memories(self, nua_name: str):
        """Display all memories for a NUA."""
        if nua_name not in self.nua_memories:
            print(f"{Color.INFO}{nua_name} has no memories.{Color.RESET}")
            return
        
        memory = self.nua_memories[nua_name]
        stats = self.get_nua_memory_stats(nua_name)
        
        print(f"\n{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.INFO}🧠 {nua_name}'S MEMORIES{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.SYSTEM}Total Memories: {stats['total_memories']}{Color.RESET}")
        print(f"{Color.SYSTEM}Important Events: {stats['important_events']}{Color.RESET}")
        print(f"{Color.SYSTEM}Threats Received: {stats['threats_received']}{Color.RESET}")
        print(f"{Color.SYSTEM}Help Received: {stats['help_received']}{Color.RESET}")
        print(f"{Color.SYSTEM}Witnessed Events: {stats['witnessed_events']}{Color.RESET}")
        
        if memory.important_events:
            print(f"\n{Color.WARNING}Important Memories:{Color.RESET}")
            for event in memory.important_events[-3:]:
                print(f"{Color.NARRATIVE}  - {event['description']}{Color.RESET}")
        
        print(f"{Color.INFO}{'='*80}{Color.RESET}\n")
    
    def clear_nua_memories(self, nua_name: str):
        """Clear all memories for a NUA (use sparingly)."""
        if nua_name in self.nua_memories:
            del self.nua_memories[nua_name]
            print(f"{Color.WARNING}Cleared all memories for {nua_name}{Color.RESET}")


# Global instance (initialized with storage path in main)
_nua_memory_system: Optional[NUAMemorySystem] = None


def _get_session_id_safe() -> str:
    try:
        import persistent_context_manager as _pcm
        gcm = getattr(_pcm, '_global_context_manager', None)
        if gcm is not None:
            sid = getattr(gcm, 'session_id', None)
            if sid:
                return str(sid)
            try:
                ctx = getattr(gcm, 'context', None)
                sid2 = getattr(ctx, 'session_id', None) if ctx is not None else None
                if sid2:
                    return str(sid2)
            except Exception:
                pass
    except Exception:
        pass

    try:
        import spatial_context_system as _scs
        sm = getattr(_scs, '_spatial_manager', None)
        if sm is not None:
            sid = getattr(sm, 'session_id', None)
            if sid:
                return str(sid)
    except Exception:
        pass

    return 'default'


def initialize_nua_memory_system(storage_directory: Optional[Path] = None) -> NUAMemorySystem:
    """Initialize the global NUA memory system"""
    global _nua_memory_system
    _nua_memory_system = NUAMemorySystem(storage_directory)
    return _nua_memory_system


def get_nua_memory_system() -> NUAMemorySystem:
    """Get the global NUA memory system instance"""
    if _nua_memory_system is None:
        try:
            sid = _get_session_id_safe()
        except Exception:
            sid = 'default'
        try:
            storage = Path("./simulation_data/nua_memories") / str(sid)
        except Exception:
            storage = None
        return initialize_nua_memory_system(storage)
    return _nua_memory_system
