"""
Key Memories System for Realitas Neo

Implements a Friends & Fables-style memory highlighting and access system.
Users can mark important moments as "key memories" and access them at will
for reference and narrative continuity.

Key memories are:
- Highlighted during gameplay
- Saved with rich context
- Accessible via simple commands
- Integrated with narrative context
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum
from color_utils import Color


class MemoryImportance(Enum):
    """Importance levels for memories"""
    CRITICAL = "critical"      # Major revelations, life-changing events
    IMPORTANT = "important"    # Significant moments, key decisions
    NOTABLE = "notable"        # Interesting moments worth remembering
    ROUTINE = "routine"        # Standard events (rarely saved as key memory)


class MemoryCategory(Enum):
    """Categories for organizing memories"""
    DISCOVERY = "discovery"              # Learning new information
    RELATIONSHIP = "relationship"        # Interactions with NPCs
    COMBAT = "combat"                    # Fight scenes
    REVELATION = "revelation"            # Plot twists, secrets revealed
    ACHIEVEMENT = "achievement"          # Accomplishments, successes
    LOSS = "loss"                        # Defeats, failures, deaths
    DECISION = "decision"                # Important choices made
    LOCATION = "location"                # New places discovered
    ITEM = "item"                        # Important items acquired
    MISSION = "mission"                  # Mission-related events


@dataclass
class KeyMemory:
    """A single key memory with rich context"""
    memory_id: str
    title: str
    description: str
    full_narrative: str
    category: MemoryCategory
    importance: MemoryImportance
    timestamp: datetime
    
    # Context
    location: str
    actors_involved: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    
    # Metadata
    turn_number: Optional[int] = None
    scene_id: Optional[str] = None
    emotional_tone: Optional[str] = None
    
    # User notes
    user_note: Optional[str] = None
    is_pinned: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON storage"""
        return {
            'memory_id': self.memory_id,
            'title': self.title,
            'description': self.description,
            'full_narrative': self.full_narrative,
            'category': self.category.value,
            'importance': self.importance.value,
            'timestamp': self.timestamp.isoformat(),
            'location': self.location,
            'actors_involved': self.actors_involved,
            'tags': self.tags,
            'turn_number': self.turn_number,
            'scene_id': self.scene_id,
            'emotional_tone': self.emotional_tone,
            'user_note': self.user_note,
            'is_pinned': self.is_pinned
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'KeyMemory':
        """Create from dictionary"""
        return cls(
            memory_id=data['memory_id'],
            title=data['title'],
            description=data['description'],
            full_narrative=data['full_narrative'],
            category=MemoryCategory(data['category']),
            importance=MemoryImportance(data['importance']),
            timestamp=datetime.fromisoformat(data['timestamp']),
            location=data['location'],
            actors_involved=data.get('actors_involved', []),
            tags=data.get('tags', []),
            turn_number=data.get('turn_number'),
            scene_id=data.get('scene_id'),
            emotional_tone=data.get('emotional_tone'),
            user_note=data.get('user_note'),
            is_pinned=data.get('is_pinned', False)
        )


class KeyMemoriesSystem:
    """Manages key memories with highlighting and access"""
    
    def __init__(self, session_id: str, storage_directory: Path, fact_system=None):
        self.session_id = session_id
        self.storage_directory = Path(storage_directory)
        self.memories_dir = self.storage_directory / "key_memories"
        self.memories_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(__name__)
        self.fact_system = fact_system  # For establishing USER_ESTABLISHED facts

        # Memory storage
        self.memories: Dict[str, KeyMemory] = {}
        self.pinned_memories: List[str] = []  # IDs of pinned memories

        # Auto-highlight settings
        self.auto_highlight_importance = MemoryImportance.IMPORTANT

        # Load existing memories
        self._load_memories()
    
    def _load_memories(self):
        """Load memories from storage"""
        memories_file = self.memories_dir / f"{self.session_id}_memories.json"
        
        if memories_file.exists():
            try:
                with open(memories_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                for memory_data in data.get('memories', []):
                    memory = KeyMemory.from_dict(memory_data)
                    self.memories[memory.memory_id] = memory
                    
                    if memory.is_pinned:
                        self.pinned_memories.append(memory.memory_id)
                
                self.logger.info(f"Loaded {len(self.memories)} key memories")
            except Exception as e:
                self.logger.error(f"Error loading memories: {e}")
    
    def _save_memories(self):
        """Save memories to storage"""
        memories_file = self.memories_dir / f"{self.session_id}_memories.json"
        
        try:
            data = {
                'session_id': self.session_id,
                'memories': [memory.to_dict() for memory in self.memories.values()],
                'last_updated': datetime.now().isoformat()
            }
            
            with open(memories_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
            self.logger.info(f"Saved {len(self.memories)} key memories")
        except Exception as e:
            self.logger.error(f"Error saving memories: {e}")

    def _extract_facts_from_memory(self, memory: KeyMemory):
        """
        Extract and establish facts from a key memory with USER_ESTABLISHED authority.
        This gives user-marked memories the highest authority level.
        """
        if not self.fact_system:
            return

        try:
            from fact_system import FactType, FactAuthority

            source = f"key_memory_{memory.memory_id}"
            turn = memory.turn_number or 0
            scene = memory.scene_id or ""

            # Extract facts based on memory category
            if memory.category == MemoryCategory.RELATIONSHIP:
                # Relationship memories often establish connections
                # Example: "Met Marcus at the bar" → Marcus exists, relationship formed
                for actor_name in memory.actors_involved:
                    if actor_name:
                        # Establish that this actor exists and was encountered
                        self.fact_system.establish_fact(
                            fact_type=FactType.ACTOR_IDENTITY,
                            subject=actor_name,
                            predicate="encountered_at",
                            value=memory.location,
                            authority=FactAuthority.USER_ESTABLISHED,
                            source=source,
                            tags=[actor_name.lower(), "encounter", "relationship"],
                            turn_number=turn,
                            scene_id=scene,
                            context=memory.full_narrative
                        )

            elif memory.category == MemoryCategory.ITEM:
                # Item memories establish possessions
                # Extract item from title/description
                item_name = memory.title.replace("Acquired ", "").replace("Found ", "").strip()
                for actor_name in memory.actors_involved:
                    if actor_name:
                        self.fact_system.establish_fact(
                            fact_type=FactType.ACTOR_POSSESSION,
                            subject=actor_name,
                            predicate="acquired",
                            value=item_name,
                            authority=FactAuthority.USER_ESTABLISHED,
                            source=source,
                            tags=[actor_name.lower(), "item", "possession"],
                            turn_number=turn,
                            scene_id=scene,
                            context=memory.full_narrative
                        )

            elif memory.category == MemoryCategory.LOCATION:
                # Location memories establish place discoveries
                self.fact_system.establish_fact(
                    fact_type=FactType.LOCATION_IDENTITY,
                    subject=memory.location,
                    predicate="discovered",
                    value="true",
                    authority=FactAuthority.USER_ESTABLISHED,
                    source=source,
                    tags=[memory.location.lower(), "location", "discovery"],
                    turn_number=turn,
                    scene_id=scene,
                    context=memory.full_narrative
                )

            elif memory.category == MemoryCategory.REVELATION:
                # Revelations often establish critical facts
                # User marked this as important, so it's canon
                if memory.importance in (MemoryImportance.CRITICAL, MemoryImportance.IMPORTANT):
                    # Extract any actor mentions and mark as canon
                    for actor_name in memory.actors_involved:
                        if actor_name:
                            self.fact_system.establish_fact(
                                fact_type=FactType.EVENT_OCCURRED,
                                subject=actor_name,
                                predicate="revelation",
                                value=memory.title,
                                authority=FactAuthority.USER_ESTABLISHED,
                                source=source,
                                tags=[actor_name.lower(), "revelation", "critical"],
                                turn_number=turn,
                                scene_id=scene,
                                context=memory.full_narrative
                            )

            elif memory.category == MemoryCategory.DECISION:
                # Decisions made by UA are canon
                if memory.actors_involved:
                    ua_name = memory.actors_involved[0]  # First actor is usually UA
                    self.fact_system.establish_fact(
                        fact_type=FactType.EVENT_OCCURRED,
                        subject=ua_name,
                        predicate="decided",
                        value=memory.title,
                        authority=FactAuthority.USER_ESTABLISHED,
                        source=source,
                        tags=[ua_name.lower(), "decision", "action"],
                        turn_number=turn,
                        scene_id=scene,
                        context=memory.full_narrative
                    )

            # CRITICAL: If memory has user_note, that's explicit user statement
            if memory.user_note and memory.user_note.strip():
                # Store user note as high-authority fact
                subject = memory.actors_involved[0] if memory.actors_involved else "World"
                self.fact_system.establish_fact(
                    fact_type=FactType.WORLD_RULE,
                    subject=subject,
                    predicate="user_noted",
                    value=memory.user_note,
                    authority=FactAuthority.USER_ESTABLISHED,
                    source=source,
                    tags=["user_note", subject.lower()],
                    turn_number=turn,
                    scene_id=scene,
                    context=memory.full_narrative
                )

            self.logger.info(f"Extracted facts from memory: {memory.title}")

        except Exception as e:
            self.logger.error(f"Error extracting facts from memory {memory.memory_id}: {e}")

    def extract_all_memory_facts(self):
        """
        Extract facts from all existing memories.
        Useful when fact_system is added to an existing session.
        """
        if not self.fact_system:
            self.logger.warning("Cannot extract memory facts: fact_system not available")
            return

        count = 0
        for memory in self.memories.values():
            try:
                self._extract_facts_from_memory(memory)
                count += 1
            except Exception as e:
                self.logger.error(f"Failed to extract facts from memory {memory.memory_id}: {e}")

        self.logger.info(f"Extracted facts from {count} existing memories")
        return count

    def create_memory(
        self,
        title: str,
        description: str,
        full_narrative: str,
        category: MemoryCategory,
        importance: MemoryImportance,
        location: str,
        actors_involved: Optional[List[str]] = None,
        tags: Optional[List[str]] = None,
        turn_number: Optional[int] = None,
        scene_id: Optional[str] = None,
        emotional_tone: Optional[str] = None,
        auto_save: bool = True
    ) -> str:
        """
        Create a new key memory
        
        Returns the memory_id
        """
        memory_id = f"mem_{len(self.memories)}_{datetime.now().timestamp()}"
        
        memory = KeyMemory(
            memory_id=memory_id,
            title=title,
            description=description,
            full_narrative=full_narrative,
            category=category,
            importance=importance,
            timestamp=datetime.now(),
            location=location,
            actors_involved=actors_involved or [],
            tags=tags or [],
            turn_number=turn_number,
            scene_id=scene_id,
            emotional_tone=emotional_tone
        )
        
        self.memories[memory_id] = memory

        # Extract facts from this memory (USER_ESTABLISHED authority)
        self._extract_facts_from_memory(memory)

        if auto_save:
            self._save_memories()

        # Display memory creation notification
        from color_utils import Color
        importance_indicator = {
            MemoryImportance.CRITICAL: "[CRITICAL]",
            MemoryImportance.IMPORTANT: "[IMPORTANT]",
            MemoryImportance.NOTABLE: "[NOTABLE]",
            MemoryImportance.ROUTINE: "[ROUTINE]"
        }
        indicator = importance_indicator.get(importance, "[MEMORY]")
        print(f"{Color.INFO}{indicator} Memory Saved: {title} [{importance.value}]{Color.RESET}")
        
        self.logger.info(f"Created key memory: {title}")
        return memory_id
    
    def highlight_memory_prompt(self, memory_id: str):
        """Display a prompt to highlight a moment as a key memory"""
        memory = self.memories.get(memory_id)
        if not memory:
            return
        
        importance_color = {
            MemoryImportance.CRITICAL: Color.ERROR,
            MemoryImportance.IMPORTANT: Color.WARNING,
            MemoryImportance.NOTABLE: Color.INFO,
            MemoryImportance.ROUTINE: Color.SYSTEM
        }.get(memory.importance, Color.INFO)
        
        print(f"\n{importance_color}{'═' * 70}{Color.RESET}")
        print(f"{importance_color}✨ KEY MEMORY HIGHLIGHTED ✨{Color.RESET}")
        print(f"{importance_color}{'═' * 70}{Color.RESET}\n")
        print(f"{Color.SUCCESS}Title:{Color.RESET} {memory.title}")
        print(f"{Color.INFO}Category:{Color.RESET} {memory.category.value.capitalize()}")
        print(f"{Color.INFO}Importance:{Color.RESET} {memory.importance.value.capitalize()}")
        print(f"\n{Color.WARNING}Description:{Color.RESET}")
        print(f"{memory.description}\n")
        print(f"{importance_color}{'─' * 70}{Color.RESET}")
        print(f"{Color.SYSTEM}💾 This memory has been saved and can be accessed anytime.{Color.RESET}")
        print(f"{importance_color}{'═' * 70}{Color.RESET}\n")
    
    def display_memory(self, memory_id: str):
        """Display a full memory with immersive formatting"""
        memory = self.memories.get(memory_id)
        if not memory:
            print(f"{Color.ERROR}Memory not found: {memory_id}{Color.RESET}")
            return
        
        # Importance-based styling
        importance_colors = {
            MemoryImportance.CRITICAL: Color.ERROR,
            MemoryImportance.IMPORTANT: Color.WARNING,
            MemoryImportance.NOTABLE: Color.INFO,
            MemoryImportance.ROUTINE: Color.SYSTEM
        }
        importance_emojis = {
            MemoryImportance.CRITICAL: "🔴",
            MemoryImportance.IMPORTANT: "🟡",
            MemoryImportance.NOTABLE: "🔵",
            MemoryImportance.ROUTINE: "⚪"
        }
        
        title_color = importance_colors.get(memory.importance, Color.SUCCESS)
        emoji = importance_emojis.get(memory.importance, "💭")
        pin_indicator = "📌 " if memory.is_pinned else ""
        
        # Header
        print(f"\n{Color.HEADER}{'═' * 70}{Color.RESET}")
        print(f"{title_color}{pin_indicator}{emoji} {memory.title.upper()}{Color.RESET}")
        print(f"{Color.HEADER}{'═' * 70}{Color.RESET}\n")
        
        # Metadata in a more narrative style
        print(f"{Color.SYSTEM}📍 {memory.location} • {memory.timestamp.strftime('%B %d, %Y at %H:%M')}{Color.RESET}")
        print(f"{Color.SYSTEM}🏷️  {memory.category.value.capitalize()} • {memory.importance.value.capitalize()} importance{Color.RESET}")
        
        if memory.actors_involved:
            print(f"{Color.SYSTEM}👥 Present: {', '.join(memory.actors_involved)}{Color.RESET}")
        
        if memory.emotional_tone:
            print(f"{Color.SYSTEM}💫 Emotional tone: {memory.emotional_tone}{Color.RESET}")
        
        print(f"\n{Color.HEADER}{'─' * 70}{Color.RESET}\n")
        
        # Description (summary)
        print(f"{Color.WARNING}What Happened:{Color.RESET}")
        print(f"{memory.description}\n")
        
        print(f"{Color.HEADER}{'─' * 70}{Color.RESET}\n")
        
        # Full narrative (the experience)
        print(f"{Color.NARRATIVE}The Memory:{Color.RESET}")
        print(f"{Color.NARRATIVE}{memory.full_narrative}{Color.RESET}\n")
        
        print(f"{Color.HEADER}{'─' * 70}{Color.RESET}\n")
        
        # User note (if any)
        if memory.user_note:
            print(f"{Color.INFO}📝 Your Note:{Color.RESET}")
            print(f"{Color.INFO}{memory.user_note}{Color.RESET}\n")
            print(f"{Color.HEADER}{'─' * 70}{Color.RESET}\n")
        
        # Footer with metadata
        if memory.tags:
            print(f"{Color.SYSTEM}🔖 Tags: {', '.join(memory.tags)}{Color.RESET}")
        
        if memory.turn_number:
            print(f"{Color.SYSTEM}⏱️  Turn #{memory.turn_number}{Color.RESET}")
        
        print(f"\n{Color.HEADER}{'═' * 70}{Color.RESET}\n")
    
    def get_memories_for_llm(
        self,
        limit: int = 10,
        min_importance: Optional[MemoryImportance] = MemoryImportance.NOTABLE
    ) -> str:
        """
        Get formatted memory context for LLM prompts.
        Returns recent important memories as a formatted string.
        """
        # Get memories above importance threshold
        filtered = []
        importance_order = [MemoryImportance.ROUTINE, MemoryImportance.NOTABLE, 
                          MemoryImportance.IMPORTANT, MemoryImportance.CRITICAL]
        
        for memory in self.memories.values():
            try:
                mem_idx = importance_order.index(memory.importance)
                min_idx = importance_order.index(min_importance)
                if mem_idx >= min_idx:
                    filtered.append(memory)
            except (ValueError, AttributeError):
                continue
        
        if not filtered:
            return ""
        
        # Sort by timestamp (newest first) and limit
        filtered.sort(key=lambda m: m.timestamp, reverse=True)
        filtered = filtered[:limit]
        
        # Build context string
        context_parts = ["**RELEVANT MEMORIES:**"]
        for memory in filtered:
            context_parts.append(f"- {memory.title}: {memory.description}")
            if memory.tags:
                context_parts.append(f"  Tags: {', '.join(memory.tags)}")
        
        return "\n".join(context_parts)
    
    def list_memories(
        self,
        category: Optional[MemoryCategory] = None,
        importance: Optional[MemoryImportance] = None,
        pinned_only: bool = False,
        limit: int = 20
    ):
        """List memories with optional filters"""
        # Filter memories
        filtered = list(self.memories.values())
        
        if category:
            filtered = [m for m in filtered if m.category == category]
        
        if importance:
            filtered = [m for m in filtered if m.importance == importance]
        
        if pinned_only:
            filtered = [m for m in filtered if m.is_pinned]
        
        # Sort by timestamp (newest first)
        filtered.sort(key=lambda m: m.timestamp, reverse=True)
        
        # Limit results
        filtered = filtered[:limit]
        
        if not filtered:
            print(f"{Color.WARNING}No memories found matching criteria.{Color.RESET}")
            return
        
        # Header with count
        print(f"\n{Color.HEADER}{'═' * 70}{Color.RESET}")
        if pinned_only:
            print(f"{Color.SUCCESS}📌 PINNED MEMORIES ({len(filtered)}){Color.RESET}")
        else:
            print(f"{Color.SUCCESS}💭 YOUR MEMORIES ({len(filtered)}){Color.RESET}")
        print(f"{Color.HEADER}{'═' * 70}{Color.RESET}\n")
        
        # Group by importance for better visual hierarchy
        critical = [m for m in filtered if m.importance == MemoryImportance.CRITICAL]
        important = [m for m in filtered if m.importance == MemoryImportance.IMPORTANT]
        notable = [m for m in filtered if m.importance == MemoryImportance.NOTABLE]
        routine = [m for m in filtered if m.importance == MemoryImportance.ROUTINE]
        
        idx = 1
        
        # Display critical memories first
        if critical:
            print(f"{Color.ERROR}🔴 CRITICAL MOMENTS:{Color.RESET}")
            for memory in critical:
                pin_indicator = "📌" if memory.is_pinned else "  "
                print(f"  {pin_indicator} [{idx}] {Color.ERROR}{memory.title}{Color.RESET}")
                print(f"       {Color.SYSTEM}{memory.category.value} • {memory.timestamp.strftime('%b %d, %Y')}{Color.RESET}")
                print(f"       {Color.INFO}{memory.description}{Color.RESET}")
                print()
                idx += 1
        
        # Display important memories
        if important:
            print(f"{Color.WARNING}🟡 IMPORTANT EVENTS:{Color.RESET}")
            for memory in important:
                pin_indicator = "📌" if memory.is_pinned else "  "
                print(f"  {pin_indicator} [{idx}] {Color.WARNING}{memory.title}{Color.RESET}")
                print(f"       {Color.SYSTEM}{memory.category.value} • {memory.timestamp.strftime('%b %d, %Y')}{Color.RESET}")
                print(f"       {Color.INFO}{memory.description}{Color.RESET}")
                print()
                idx += 1
        
        # Display notable memories
        if notable:
            print(f"{Color.INFO}🔵 NOTABLE MOMENTS:{Color.RESET}")
            for memory in notable:
                pin_indicator = "📌" if memory.is_pinned else "  "
                print(f"  {pin_indicator} [{idx}] {Color.INFO}{memory.title}{Color.RESET}")
                print(f"       {Color.SYSTEM}{memory.category.value} • {memory.timestamp.strftime('%b %d, %Y')}{Color.RESET}")
                print(f"       {memory.description}")
                print()
                idx += 1
        
        # Display routine memories (if any)
        if routine:
            print(f"{Color.SYSTEM}⚪ ROUTINE EVENTS:{Color.RESET}")
            for memory in routine:
                pin_indicator = "📌" if memory.is_pinned else "  "
                print(f"  {pin_indicator} [{idx}] {memory.title}")
                print(f"       {memory.category.value} • {memory.timestamp.strftime('%b %d, %Y')}")
                print()
                idx += 1
        
        print(f"{Color.HEADER}{'═' * 70}{Color.RESET}")
        print(f"{Color.SYSTEM}💡 Type 'recall [number]' or '/mem [number]' to view full memory{Color.RESET}")
        print(f"{Color.SYSTEM}💡 Type '/mem help' for more commands{Color.RESET}\n")
    
    def pin_memory(self, memory_id: str):
        """Pin a memory for quick access"""
        if memory_id in self.memories:
            self.memories[memory_id].is_pinned = True
            if memory_id not in self.pinned_memories:
                self.pinned_memories.append(memory_id)
            self._save_memories()
            print(f"{Color.SUCCESS}📌 Memory pinned: {self.memories[memory_id].title}{Color.RESET}")
        else:
            print(f"{Color.ERROR}Memory not found{Color.RESET}")
    
    def unpin_memory(self, memory_id: str):
        """Unpin a memory"""
        if memory_id in self.memories:
            self.memories[memory_id].is_pinned = False
            if memory_id in self.pinned_memories:
                self.pinned_memories.remove(memory_id)
            self._save_memories()
            print(f"{Color.INFO}Memory unpinned: {self.memories[memory_id].title}{Color.RESET}")
        else:
            print(f"{Color.ERROR}Memory not found{Color.RESET}")
    
    def add_note_to_memory(self, memory_id: str, note: str):
        """Add a user note to a memory"""
        if memory_id in self.memories:
            self.memories[memory_id].user_note = note
            self._save_memories()
            print(f"{Color.SUCCESS}✓ Note added to memory{Color.RESET}")
        else:
            print(f"{Color.ERROR}Memory not found{Color.RESET}")
    
    def search_memories(self, query: str, limit: int = 10) -> List[KeyMemory]:
        """Search memories by text using keyword matching with semantic expansion"""
        query_lower = query.lower()
        
        # Extract keywords from query (remove common words)
        stop_words = {'what', 'where', 'when', 'how', 'who', 'why', 'can', 'should', 
                      'is', 'are', 'the', 'a', 'an', 'to', 'from', 'in', 'on', 'at',
                      'i', 'you', 'we', 'they', 'do', 'does', 'my', 'your', 'his', 'her'}
        
        query_words = [w.strip('.,!?;:').lower() for w in query.split() 
                       if w.lower() not in stop_words and len(w) > 2]
        
        # Handle compound words and semantic expansion
        expanded_words = []
        for word in query_words:
            expanded_words.append(word)
            # Split common compounds and add synonyms
            if 'friend' in word:
                expanded_words.extend(['friend', 'friends', 'friendship'])
            if 'family' in word or 'mother' in word or 'father' in word:
                expanded_words.extend(['family', 'mother', 'father', 'parent', 'sibling'])
            if 'love' in word or 'partner' in word:
                expanded_words.extend(['love', 'partner', 'relationship', 'romantic'])
            if 'work' in word or 'job' in word:
                expanded_words.extend(['work', 'job', 'career', 'colleague', 'office'])
            if 'fear' in word or 'afraid' in word or 'scared' in word:
                expanded_words.extend(['fear', 'afraid', 'terror', 'dread', 'anxious'])
            if 'dream' in word or 'hope' in word or 'wish' in word:
                expanded_words.extend(['dream', 'hope', 'aspire', 'ambition', 'wish'])
            if 'secret' in word or 'hide' in word or 'hidden' in word:
                expanded_words.extend(['secret', 'hide', 'hidden', 'guilt', 'shame'])
            
            # Skill/ability queries -> search for training, learning, practice memories
            if any(w in word for w in ['skill', 'ability', 'can', 'able', 'good', 'capable', 'trained']):
                expanded_words.extend(['training', 'learned', 'practice', 'education', 'academy', 
                                      'taught', 'mastered', 'experience', 'proficient'])
            if 'hack' in word or 'computer' in word or 'tech' in word:
                expanded_words.extend(['computing', 'terminal', 'system', 'code', 'program', 'digital'])
            if 'fight' in word or 'combat' in word or 'weapon' in word:
                expanded_words.extend(['combat', 'fight', 'weapon', 'training', 'drill', 'sparring'])
            if 'talk' in word or 'persuade' in word or 'convince' in word:
                expanded_words.extend(['negotiation', 'conversation', 'convinced', 'persuaded', 'talked'])
            if 'sneak' in word or 'stealth' in word or 'hide' in word:
                expanded_words.extend(['stealth', 'shadow', 'unnoticed', 'slipped', 'crept', 'quiet'])
            
            # Money/resource queries
            if 'money' in word or 'afford' in word or 'rich' in word or 'poor' in word:
                expanded_words.extend(['credits', 'payment', 'salary', 'bought', 'expensive', 'cheap'])
            
            # Identity queries -> search for self-defining memories
            if 'who' in word and ('am' in query_lower or 'are' in query_lower):
                expanded_words.extend(['identity', 'name', 'became', 'always', 'childhood', 'defining'])
        
        query_words = list(set(expanded_words))  # Deduplicate
        
        # If no keywords, fall back to full query
        if not query_words:
            query_words = [query_lower]
        
        results = []
        
        for memory in self.memories.values():
            score = 0
            title_lower = memory.title.lower()
            desc_lower = memory.description.lower()
            tags_lower = [tag.lower() for tag in memory.tags]
            
            # Score based on keyword matches
            for word in query_words:
                # Title match (highest priority)
                if word in title_lower:
                    score += 3
                # Tag match (high priority)
                if any(word in tag for tag in tags_lower):
                    score += 2
                # Description match (medium priority)
                if word in desc_lower:
                    score += 1
            
            # Boost for category-matching queries
            # Relationship queries
            if any(w in ['friend', 'friends', 'relationship', 'partner', 'love', 'family', 
                        'mother', 'father', 'sibling', 'brother', 'sister', 'childhood'] for w in query_words):
                if 'relationship' in title_lower or memory.category == MemoryCategory.RELATIONSHIP:
                    score += 2
            
            # Achievement/dreams queries
            if any(w in ['achievement', 'proud', 'accomplish', 'success', 'dream', 'dreams',
                        'hope', 'aspire', 'ambition', 'goal', 'win', 'victory'] for w in query_words):
                if 'achievement' in title_lower or 'dreams' in title_lower or memory.category == MemoryCategory.ACHIEVEMENT:
                    score += 2
            
            # Loss/trauma/fear queries
            if any(w in ['loss', 'lost', 'trauma', 'painful', 'grief', 'death', 'died',
                        'fear', 'afraid', 'scared', 'terror', 'dread', 'anxious'] for w in query_words):
                if 'loss' in title_lower or 'trauma' in title_lower or 'fears' in title_lower or memory.category == MemoryCategory.LOSS:
                    score += 2
            
            # Discovery/learning/work queries
            if any(w in ['learn', 'education', 'school', 'training', 'work', 'job', 'career',
                        'discover', 'hobby', 'hobbies', 'belief', 'beliefs', 'secret', 'secrets'] for w in query_words):
                if any(cat in title_lower for cat in ['education', 'hobbies', 'beliefs', 'secrets', 'job']) or memory.category == MemoryCategory.DISCOVERY:
                    score += 2
            
            # Location queries
            if any(w in ['location', 'place', 'where', 'home', 'live', 'city', 'neighborhood'] for w in query_words):
                if 'location' in title_lower or memory.category == MemoryCategory.LOCATION:
                    score += 2
            
            if score > 0:
                results.append((score, memory))
        
        # Sort by score (highest first)
        results.sort(key=lambda x: x[0], reverse=True)
        
        # Return just the memories (without scores)
        return [memory for score, memory in results[:limit]]
    
    def get_context_for_llm(self, max_memories: int = 5) -> str:
        """
        Get formatted memory context for LLM prompts
        
        Prioritizes pinned and recent important memories
        """
        # Get pinned memories first
        context_memories = [
            self.memories[mid] for mid in self.pinned_memories
            if mid in self.memories
        ]
        
        # Add recent important memories
        recent_important = [
            m for m in self.memories.values()
            if m.importance in [MemoryImportance.CRITICAL, MemoryImportance.IMPORTANT]
            and not m.is_pinned
        ]
        recent_important.sort(key=lambda m: m.timestamp, reverse=True)
        
        context_memories.extend(recent_important[:max_memories - len(context_memories)])
        
        if not context_memories:
            return ""
        
        context_parts = ["**KEY MEMORIES:**\n"]
        
        for memory in context_memories:
            context_parts.append(f"\n**{memory.title}** ({memory.category.value}):")
            context_parts.append(f"{memory.description}")
            if memory.user_note:
                context_parts.append(f"Note: {memory.user_note}")
            context_parts.append("")
        
        return "\n".join(context_parts)


# Global instance
_key_memories: Optional[KeyMemoriesSystem] = None


def initialize_key_memories(session_id: str, storage_directory: Path) -> KeyMemoriesSystem:
    """Initialize the global key memories system"""
    global _key_memories
    _key_memories = KeyMemoriesSystem(session_id, storage_directory)
    return _key_memories


def get_key_memories() -> KeyMemoriesSystem:
    """Get the global key memories system instance"""
    if _key_memories is None:
        raise RuntimeError("Key memories system not initialized. Call initialize_key_memories() first.")
    return _key_memories


def handle_memory_command(command: str) -> bool:
    """
    Handle memory-related commands with meta command support
    
    Supports both natural language and quick meta commands:
    - Natural: "memories", "recall 3", "search memories combat"
    - Meta: "/mem", "/mem 3", "/mem search combat"
    
    Returns True if command was handled, False otherwise
    """
    if _key_memories is None:
        return False
    
    command_lower = command.lower().strip()
    original_command = command.strip()
    
    # Check for meta command prefix (/mem or @mem)
    is_meta = False
    if command_lower.startswith('/mem') or command_lower.startswith('@mem'):
        is_meta = True
        # Extract the rest of the command after /mem or @mem
        if command_lower.startswith('/mem'):
            rest = original_command[4:].strip()
        else:  # @mem
            rest = original_command[4:].strip()
        
        # Parse meta command
        if not rest:
            # Just "/mem" - list all memories
            _key_memories.list_memories()
            return True
        elif rest.isdigit():
            # "/mem 3" - recall memory #3
            try:
                idx = int(rest) - 1
                memories_list = list(_key_memories.memories.values())
                memories_list.sort(key=lambda m: m.timestamp, reverse=True)
                if 0 <= idx < len(memories_list):
                    _key_memories.display_memory(memories_list[idx].memory_id)
                else:
                    print(f"{Color.ERROR}Invalid memory number{Color.RESET}")
            except ValueError:
                print(f"{Color.ERROR}Invalid memory number{Color.RESET}")
            return True
        elif rest.lower() == 'pinned' or rest.lower() == 'pin':
            # "/mem pinned" - show pinned memories
            _key_memories.list_memories(pinned_only=True)
            return True
        elif rest.lower().startswith('search ') or rest.lower().startswith('find '):
            # "/mem search combat" or "/mem find combat"
            query = rest[7:].strip() if rest.lower().startswith('search ') else rest[5:].strip()
            results = _key_memories.search_memories(query)
            if results:
                print(f"\n{Color.SUCCESS}Found {len(results)} memories:{Color.RESET}\n")
                for idx, memory in enumerate(results, 1):
                    print(f"[{idx}] {memory.title}")
                    print(f"    {memory.description[:80]}{'...' if len(memory.description) > 80 else ''}\n")
            else:
                print(f"{Color.WARNING}No memories found matching '{query}'{Color.RESET}")
            return True
        elif rest.lower() == 'help' or rest.lower() == '?':
            # "/mem help" - show help
            _display_memory_help()
            return True
    
    # Natural language commands (original behavior)
    
    # List memories
    if command_lower in ['memories', 'list memories', 'show memories']:
        _key_memories.list_memories()
        return True
    
    # List pinned memories
    if command_lower in ['pinned', 'pinned memories', 'show pinned']:
        _key_memories.list_memories(pinned_only=True)
        return True
    
    # Search memories
    if command_lower.startswith('search memories '):
        query = command[16:].strip()
        results = _key_memories.search_memories(query)
        if results:
            print(f"\n{Color.SUCCESS}Found {len(results)} memories:{Color.RESET}\n")
            for idx, memory in enumerate(results, 1):
                print(f"[{idx}] {memory.title}")
                print(f"    {memory.description[:80]}{'...' if len(memory.description) > 80 else ''}\n")
        else:
            print(f"{Color.WARNING}No memories found matching '{query}'{Color.RESET}")
        return True
    
    # Recall specific memory
    if command_lower.startswith('recall '):
        try:
            idx = int(command[7:].strip()) - 1
            memories_list = list(_key_memories.memories.values())
            memories_list.sort(key=lambda m: m.timestamp, reverse=True)
            if 0 <= idx < len(memories_list):
                _key_memories.display_memory(memories_list[idx].memory_id)
            else:
                print(f"{Color.ERROR}Invalid memory number{Color.RESET}")
        except ValueError:
            print(f"{Color.ERROR}Invalid memory number{Color.RESET}")
        return True
    
    return False


def _display_memory_help():
    """Display help for memory commands"""
    print(f"\n{Color.HEADER}{'═' * 70}{Color.RESET}")
    print(f"{Color.HEADER}                    📖 MEMORY COMMANDS{Color.RESET}")
    print(f"{Color.HEADER}{'═' * 70}{Color.RESET}\n")
    
    print(f"{Color.SUCCESS}Quick Meta Commands:{Color.RESET}")
    print(f"  {Color.INFO}/mem{Color.RESET}              - List all memories")
    print(f"  {Color.INFO}/mem [number]{Color.RESET}     - Recall specific memory (e.g., /mem 3)")
    print(f"  {Color.INFO}/mem pinned{Color.RESET}       - Show only pinned memories")
    print(f"  {Color.INFO}/mem search [query]{Color.RESET} - Search memories (e.g., /mem search combat)")
    print(f"  {Color.INFO}/mem help{Color.RESET}         - Show this help\n")
    
    print(f"{Color.SUCCESS}Natural Language Commands:{Color.RESET}")
    print(f"  {Color.INFO}memories{Color.RESET}          - List all memories")
    print(f"  {Color.INFO}recall [number]{Color.RESET}   - Recall specific memory")
    print(f"  {Color.INFO}pinned{Color.RESET}            - Show pinned memories")
    print(f"  {Color.INFO}search memories [query]{Color.RESET} - Search memories\n")
    
    print(f"{Color.WARNING}Examples:{Color.RESET}")
    print(f"  /mem                    → List all memories")
    print(f"  /mem 5                  → View memory #5")
    print(f"  /mem search first fight → Find combat memories")
    print(f"  /mem pinned             → Show important memories\n")
    
    print(f"{Color.HEADER}{'═' * 70}{Color.RESET}\n")
