"""
Intent-Based Memory Creation System

Creates vessel background memories based on user intent and Intent Availability System.
Builds character history diegetically through actions and internal voice narration.

Example Flow:
1. User mentions "family" in action
2. Intent Availability determines: AVAILABLE_NOW, AVAILABLE_LATER, or AVAILABLE_NEVER
3. System creates appropriate memory based on availability
4. Internal voice relays memory diegetically to user

Examples:
- AVAILABLE_NOW: "You have a loving family" → Internal voice: "I should call mom soon"
- AVAILABLE_LATER: "Your family is distant" → Internal voice: "Maybe I'll reconnect someday"
- AVAILABLE_NEVER: "You have no family" → Internal voice: "I've been alone for so long"
"""

import json
import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from enum import Enum

from intent_availability_system import IntentAvailability
from key_memories_system import get_key_memories, MemoryCategory, MemoryImportance
from openrouter_config import create_role_client, OpenRouterConfig
from json_utils import extract_and_parse_json
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


class MemoryTriggerType(Enum):
    """Types of triggers that can create memories"""
    FAMILY = "family"
    RELATIONSHIP = "relationship"
    LOCATION = "location"
    POSSESSION = "possession"
    SKILL = "skill"
    OCCUPATION = "occupation"
    BACKSTORY = "backstory"
    TRAUMA = "trauma"
    ACHIEVEMENT = "achievement"
    HABIT = "habit"


class IntentBasedMemoryCreator:
    """
    Creates vessel background memories based on user intent and availability.
    Integrates with Intent Availability System to build character history organically.
    Also triggers memories from narration/perception (memory resurfacing).
    """
    
    def __init__(self, storage_directory: Path):
        self.client = create_role_client("coordination")
        self.logger = logging.getLogger(__name__)
        # Ensure storage_directory is a Path object
        self.storage_directory = Path(storage_directory) if isinstance(storage_directory, str) else storage_directory
        
        # Track what memories have been created to avoid duplicates
        self.created_memory_topics = set()
        
        # Track last turn when memory was created (to enforce minimum interval)
        self.last_memory_turn = -999  # Start far in past
        self.min_turn_interval = 5  # Minimum 5 turns between memory creations
        
        # Probability thresholds for memory creation
        self.intent_memory_probability = 0.25  # 25% chance for intent-based
        self.narration_memory_probability = 0.15  # 15% chance for narration-based
        
        # Load existing topics
        self._load_memory_topics()
    
    def detect_memory_triggers(self, user_intent: str) -> List[Dict[str, Any]]:
        """
        Detect if user intent contains triggers for memory creation.
        
        Args:
            user_intent: The user's stated intent/action
            
        Returns:
            List of detected triggers with type and context
        """
        
        prompt = f"""Analyze this user intent for memory creation triggers.

**User Intent:**
{user_intent}

**Memory Trigger Detection:**

Detect if the user mentions or implies any of these categories:

1. **FAMILY** - mother, father, sister, brother, parents, siblings, family, relatives
2. **RELATIONSHIP** - friend, girlfriend, boyfriend, partner, spouse, ex, lover
3. **LOCATION** - childhood home, favorite place, hometown, old neighborhood, familiar spot
4. **POSSESSION** - car, house, apartment, belongings, cherished item, heirloom
5. **SKILL** - learned ability, training, expertise, practiced skill
6. **OCCUPATION** - job, career, former work, profession
7. **BACKSTORY** - past event, history, origin, where they came from
8. **TRAUMA** - painful memory, loss, regret, difficult past
9. **ACHIEVEMENT** - accomplishment, success, proud moment
10. **HABIT** - routine, regular activity, usual behavior

**IMPORTANT:**
- Only detect triggers that are EXPLICITLY mentioned or strongly implied
- Don't over-interpret - "I go to the store" doesn't trigger LOCATION memories
- Multiple triggers can exist in one intent
- Return empty list if no clear triggers

**Response Format:**
Return JSON array:

[
    {{
        "trigger_type": "family/relationship/location/etc",
        "trigger_context": "What specifically was mentioned (e.g., 'mother', 'childhood home')",
        "confidence": 0.0-1.0,
        "reasoning": "Why this is a memory trigger"
    }}
]

If no triggers detected, return: []
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            if result and isinstance(result, list):
                return result
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error detecting memory triggers: {e}")
            return []
    
    def create_memory_from_intent(self,
                                  trigger: Dict[str, Any],
                                  availability: IntentAvailability,
                                  user_intent: str,
                                  current_location: str,
                                  turn_number: int,
                                  scene_id: str) -> Optional[Dict[str, Any]]:
        """
        Create a memory based on trigger and availability classification.
        
        MEMORY CREATION LOGIC:
        - EXIST → Create memory about the thing (it exists and is accessible)
        - EXIST_NOT_HERE → Create memory about why it's not here (exists but unavailable)
        - DOES_NOT_EXIST → NO memory created (we don't know anything about it)
        
        Args:
            trigger: The detected memory trigger
            availability: EXIST, EXIST_NOT_HERE, or DOES_NOT_EXIST
            user_intent: Original user intent
            current_location: Where the vessel is
            turn_number: Current turn number
            scene_id: Current scene ID
            
        Returns:
            Dictionary with memory details and internal voice narration, or None
        """
        
        # DOES_NOT_EXIST → No memory created
        if availability == IntentAvailability.DOES_NOT_EXIST:
            self.logger.info(f"Intent does not exist - no memory created")
            return None
        
        trigger_type = trigger.get("trigger_type", "backstory")
        trigger_context = trigger.get("trigger_context", "")
        
        # Check if we've already created a memory for this topic
        topic_key = f"{trigger_type}:{trigger_context.lower()}"
        if topic_key in self.created_memory_topics:
            self.logger.info(f"Memory already exists for: {topic_key}")
            return None
        
        prompt = f"""Create a vessel background memory based on intent availability.

**User Intent:**
{user_intent}

**Memory Trigger:**
Type: {trigger_type}
Context: {trigger_context}

**Availability Classification:**
{availability.value}

**Memory Creation Guidelines:**

**If EXIST:**
- Create memory about the thing (it exists and is accessible)
- This thing exists and can be interacted with
- Examples:
  - Family: "You have a loving mother, Margaret, who lives nearby in the suburbs"
  - Location: "You know Joe's Diner on 5th Street - great coffee, open 24/7"
  - Possession: "You own a reliable '98 Honda Civic, parked outside"
  - Relationship: "You have a close friend named Jake who works at the garage"

**If EXIST_NOT_HERE:**
- Create memory about why it's not here (exists but unavailable)
- Explain the constraint or distance
- Examples:
  - Family: "You have a sister, Sarah, but she moved to California years ago after the argument and you lost contact"
  - Location: "You used to go to Murphy's Bar downtown, but it closed last year after the fire"
  - Possession: "You had a motorcycle but sold it last year to pay rent"
  - Relationship: "You had a best friend, Marcus, but lost touch after he moved to Seattle"

**NOTE:** DOES_NOT_EXIST should never reach this function - no memory is created in that case.

**Internal Voice Guidelines:**

Create a brief internal thought (1-2 sentences) that:
- Reflects the memory naturally
- Uses first person PLURAL ("we", "our", "us") - NEVER use "I" or "my"
- Feels like genuine inner monologue
- Matches the emotional tone of the memory

**Examples:**

EXIST (Family):
- Memory: "You have a loving mother, Margaret, who lives in the suburbs. She calls every Sunday."
- Internal Voice: "We should call mom soon. She worries when we don't check in."

EXIST_NOT_HERE (Family):
- Memory: "You have a sister, Sarah, who moved to California years ago after the argument. You haven't spoken since."
- Internal Voice: "We wonder how Sarah's doing. Maybe we'll reach out someday."

EXIST (Location):
- Memory: "You know Joe's Diner on 5th Street. Best coffee in town, open 24/7."
- Internal Voice: "Joe's is just a few blocks away. We could grab a coffee there."

EXIST_NOT_HERE (Location):
- Memory: "You used to go to Murphy's Bar downtown, but it closed last year after the fire."
- Internal Voice: "We miss Murphy's. That place had character. Nothing like it now."

**Response Format:**
Return JSON:

{{
    "memory_title": "Brief title (e.g., 'Loving Mother', 'Estranged Sister')",
    "memory_description": "Full memory description (2-3 sentences)",
    "memory_category": "relationship/location/possession/backstory/etc",
    "memory_importance": "notable/important/critical",
    "emotional_tone": "warm/neutral/melancholic/resigned/etc",
    "internal_voice": "First-person internal thought (1-2 sentences)",
    "tags": ["relevant", "tags", "for", "memory"]
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            if not result:
                self.logger.error("Failed to parse memory creation response")
                return None
            
            # Create the memory in the key memories system
            key_memories = get_key_memories()
            
            # Map category string to enum
            # Note: BACKSTORY doesn't exist in MemoryCategory, use DISCOVERY as fallback
            category_map = {
                "relationship": MemoryCategory.RELATIONSHIP,
                "location": MemoryCategory.LOCATION,
                "possession": MemoryCategory.ITEM,
                "backstory": MemoryCategory.DISCOVERY,  # No BACKSTORY enum, use DISCOVERY
                "achievement": MemoryCategory.ACHIEVEMENT,
                "trauma": MemoryCategory.LOSS,
                "skill": MemoryCategory.DISCOVERY,
                "occupation": MemoryCategory.DISCOVERY,  # No BACKSTORY enum, use DISCOVERY
                "habit": MemoryCategory.DISCOVERY,  # No BACKSTORY enum, use DISCOVERY
                "family": MemoryCategory.RELATIONSHIP
            }
            
            # Map importance string to enum
            importance_map = {
                "notable": MemoryImportance.NOTABLE,
                "important": MemoryImportance.IMPORTANT,
                "critical": MemoryImportance.CRITICAL
            }
            
            category = category_map.get(
                result.get("memory_category", "discovery").lower(),
                MemoryCategory.DISCOVERY  # Default to DISCOVERY instead of non-existent BACKSTORY
            )
            
            importance = importance_map.get(
                result.get("memory_importance", "notable").lower(),
                MemoryImportance.NOTABLE
            )
            
            memory_id = key_memories.create_memory(
                title=result.get("memory_title", "Background Memory"),
                description=result.get("memory_description", ""),
                full_narrative=f"Created from intent: {user_intent}",
                category=category,
                importance=importance,
                location=current_location,
                actors_involved=[],
                tags=result.get("tags", [trigger_type, "intent_based"]),
                turn_number=turn_number,
                scene_id=scene_id,
                emotional_tone=result.get("emotional_tone", "neutral"),
                auto_save=True
            )
            
            # Track this topic
            self.created_memory_topics.add(topic_key)
            self._save_memory_topics()
            
            # Return full result with internal voice
            result["memory_id"] = memory_id
            result["trigger_type"] = trigger_type
            result["trigger_context"] = trigger_context
            result["availability"] = availability.value
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating memory from intent: {e}")
            return None
    
    def _extract_memory_keywords(self, text: str) -> List[str]:
        """
        Extract key nouns/concepts from text for memory tagging.
        
        Args:
            text: Text to extract keywords from
            
        Returns:
            List of lowercase keywords
        """
        # Common words to ignore
        stopwords = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'to', 'from', 'in', 'on', 'at',
                    'what', 'where', 'when', 'how', 'why', 'who', 'which', 'best', 'way', 'get'}
        
        # Split and clean
        words = text.lower().replace('?', '').replace(',', '').split()
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        return keywords[:5]  # Limit to 5 most relevant
    
    def _check_existing_memory(self, keywords: List[str]) -> Optional[Dict[str, Any]]:
        """
        Check if we already have a memory with similar keywords.
        
        Args:
            keywords: Keywords to search for
            
        Returns:
            Existing memory dict if found, None otherwise
        """
        try:
            from key_memories_system import get_key_memories
            key_memories = get_key_memories()
            
            # Search memories for matching keywords
            # Access the memories dict directly
            for memory_id, memory_obj in key_memories.memories.items():
                # Convert KeyMemory object to dict for compatibility
                memory_tags = memory_obj.tags if hasattr(memory_obj, 'tags') else []
                
                # Check if any keyword matches any tag
                if any(keyword in ' '.join(memory_tags).lower() for keyword in keywords):
                    # Return as dict for compatibility
                    return {
                        'id': memory_id,
                        'title': memory_obj.title,
                        'description': memory_obj.description,
                        'tags': memory_tags
                    }
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error checking existing memories: {e}")
            return None
    
    def create_memory_from_inquiry_answer(self,
                                         question: str,
                                         answer: str,
                                         current_location: str,
                                         turn_number: int,
                                         scene_id: str,
                                         internal_voice: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Create a memory from an inquiry answer that contains knowledge.
        
        CRITICAL: This should ONLY be called if the answer contains actual factual knowledge.
        The answer parameter should be a FACT ("The #7 bus runs every 20 minutes"),
        NOT a thought ("We should take the bus").
        
        Args:
            question: The question that was asked
            answer: The FACTUAL knowledge (not a suggestion)
            current_location: Current location
            turn_number: Current turn
            scene_id: Current scene
            internal_voice: Optional internal voice to accompany memory
            
        Returns:
            Memory result dict if created, None otherwise
        """
        try:
            # Check if answer contains actual knowledge (not admission of ignorance)
            ignorance_phrases = [
                "don't know", "not sure", "never been", "no idea", 
                "can't remember", "haven't", "maybe we should ask",
                "we could", "we should", "let's", "maybe"
            ]
            
            answer_lower = answer.lower()
            if any(phrase in answer_lower for phrase in ignorance_phrases):
                # Answer admits lack of knowledge or is a suggestion, don't create memory
                return None
            
            # Extract keywords from question and answer for tagging
            question_keywords = self._extract_memory_keywords(question)
            answer_keywords = self._extract_memory_keywords(answer)
            all_keywords = list(set(question_keywords + answer_keywords))  # Unique keywords
            
            # Check if we already have a memory about this topic
            existing_memory = self._check_existing_memory(all_keywords)
            if existing_memory:
                # Return existing memory instead of creating duplicate
                self.logger.info(f"Found existing memory, not creating duplicate: {existing_memory.get('title')}")
                return {
                    "memory_id": existing_memory.get('id'),
                    "memory_title": existing_memory.get('title'),
                    "memory_description": existing_memory.get('description'),
                    "internal_voice": internal_voice,  # Still provide internal voice
                    "location": current_location,
                    "turn_number": turn_number,
                    "scene_id": scene_id,
                    "trigger_type": "INQUIRY_RETRIEVAL",  # Mark as retrieval, not creation
                    "trigger_context": question,
                    "timestamp": datetime.now().isoformat(),
                    "is_existing": True  # Flag to indicate this is existing
                }
            
            # Extract the knowledge from the answer and create a NEW memory
            memory_title = f"Knowledge: {' '.join(all_keywords[:3]).title()}"  # Use keywords for title
            memory_description = answer  # Should be a FACT, not a suggestion
            
            # Get key memories instance
            key_memories = get_key_memories()
            
            # Create memory using key_memories module with proper tags
            memory_tags = ["inquiry_knowledge", "automatic"] + all_keywords
            memory_id = key_memories.create_memory(
                title=memory_title,
                description=memory_description,
                full_narrative=f"Inquiry: {question}\nAnswer: {answer}",
                category=MemoryCategory.DISCOVERY,  # DISCOVERY = Learning new information
                importance=MemoryImportance.NOTABLE,
                location=current_location,
                actors_involved=[],
                tags=memory_tags,  # Include keywords for future retrieval
                turn_number=turn_number,
                scene_id=scene_id,
                emotional_tone="informative",
                auto_save=True
            )
            
            # Track topic to prevent duplicates
            topic_key = f"inquiry:{question[:30].lower()}"
            self.created_memory_topics.add(topic_key)
            self._save_memory_topics()
            
            # Update last memory turn
            self.last_memory_turn = turn_number
            
            # Return memory data for display
            # Memory = FACT, Internal Voice = THOUGHT to acknowledge the memory
            memory_data = {
                "memory_id": memory_id,
                "memory_title": memory_title,
                "memory_description": memory_description,
                "internal_voice": internal_voice,  # Include internal voice to acknowledge memory
                "location": current_location,
                "turn_number": turn_number,
                "scene_id": scene_id,
                "trigger_type": "INQUIRY_KNOWLEDGE",
                "trigger_context": question,
                "timestamp": datetime.now().isoformat(),
                "is_existing": False,  # Flag to indicate this is new
                "keywords": all_keywords  # Store keywords for reference
            }
            
            return memory_data
            
        except Exception as e:
            self.logger.error(f"Error creating memory from inquiry answer: {e}")
            return None
    
    def process_intent_for_memories(self,
                                   user_intent: str,
                                   availability_result: Dict[str, Any],
                                   current_location: str,
                                   turn_number: int,
                                   scene_id: str) -> List[Dict[str, Any]]:
        """
        Complete pipeline: detect triggers and create memories.
        
        Args:
            user_intent: User's stated intent
            availability_result: Result from IntentAvailabilitySystem
            current_location: Current location
            turn_number: Current turn
            scene_id: Current scene
            
        Returns:
            List of created memories with internal voice narration
        """
        
        # CRITERIA 1: Probability check (25% chance)
        if random.random() > self.intent_memory_probability:
            return []
        
        # CRITERIA 2: Minimum turn interval (at least 5 turns since last memory)
        if turn_number - self.last_memory_turn < self.min_turn_interval:
            return []
        
        # Detect memory triggers
        triggers = self.detect_memory_triggers(user_intent)
        
        if not triggers:
            return []
        
        # Get availability classification
        availability = availability_result.get("availability")
        if not isinstance(availability, IntentAvailability):
            # Try to convert from string
            try:
                availability = IntentAvailability(availability)
            except:
                self.logger.warning(f"Invalid availability type: {availability}")
                return []
        
        # Create memories for each trigger
        created_memories = []
        for trigger in triggers:
            memory_result = self.create_memory_from_intent(
                trigger=trigger,
                availability=availability,
                user_intent=user_intent,
                current_location=current_location,
                turn_number=turn_number,
                scene_id=scene_id
            )
            
            if memory_result:
                created_memories.append(memory_result)
        
        # Update last memory turn if any memories were created
        if created_memories:
            self.last_memory_turn = turn_number
        
        return created_memories
    
    def _save_memory_topics(self):
        """Save created memory topics to disk"""
        try:
            topics_file = self.storage_directory / "intent_memories" / "topics.json"
            topics_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(topics_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "created_topics": list(self.created_memory_topics),
                    "saved_at": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save memory topics: {e}")
    
    def _load_memory_topics(self):
        """Load created memory topics from disk"""
        try:
            topics_file = self.storage_directory / "intent_memories" / "topics.json"
            
            if topics_file.exists():
                with open(topics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.created_memory_topics = set(data.get("created_topics", []))
                    self.logger.info(f"Loaded {len(self.created_memory_topics)} memory topics")
                    
        except Exception as e:
            self.logger.warning(f"Could not load memory topics: {e}")
    
    def detect_memory_triggers_from_narration(self, narration: str) -> List[Dict[str, Any]]:
        """
        Detect if narration/scene description contains triggers for memory resurfacing.
        
        This is for PERCEPTION-BASED memory triggers - when the vessel sees/hears/experiences
        something that reminds them of their past.
        
        Args:
            narration: The narrative text (scene description, action outcome, etc.)
            
        Returns:
            List of detected triggers with type and context
        """
        
        prompt = f"""Analyze this narration for memory resurfacing triggers.

**Narration:**
{narration}

**Memory Resurfacing Detection:**

Detect if the narration contains elements that would trigger a memory for the vessel:

1. **FAMILY** - Seeing families, parents with children, family gatherings
2. **RELATIONSHIP** - Seeing couples, friends together, romantic moments
3. **LOCATION** - Familiar-looking places, nostalgic settings, childhood-like environments
4. **POSSESSION** - Seeing items that remind of cherished possessions
5. **SKILL** - Seeing someone perform a skill the vessel knows/learned
6. **OCCUPATION** - Seeing work environments, professional settings
7. **BACKSTORY** - Situations that echo past experiences
8. **TRAUMA** - Triggering situations that remind of painful past
9. **ACHIEVEMENT** - Seeing success that reminds of own accomplishments
10. **HABIT** - Seeing routines that remind of own habits

**IMPORTANT:**
- Only detect STRONG triggers that would genuinely resurface a memory
- The narration must contain something SPECIFIC and evocative
- Generic descriptions don't trigger memories
- Multiple triggers can exist in one narration

**Examples:**

STRONG TRIGGER:
- "You see a happy family having a picnic together" → FAMILY trigger
- "A couple walks by, holding hands and laughing" → RELATIONSHIP trigger
- "The old diner reminds you of somewhere familiar" → LOCATION trigger
- "You hear someone playing guitar beautifully" → SKILL trigger

WEAK/NO TRIGGER:
- "You walk down the street" → No trigger
- "The guard stands there" → No trigger
- "It's a sunny day" → No trigger

**Response Format:**
Return JSON array:

[
    {{
        "trigger_type": "family/relationship/location/etc",
        "trigger_context": "What specifically triggered the memory (e.g., 'seeing happy family', 'hearing guitar')",
        "confidence": 0.0-1.0,
        "reasoning": "Why this would trigger a memory",
        "narration_excerpt": "The specific part of narration that triggered it"
    }}
]

If no strong triggers detected, return: []
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            if result and isinstance(result, list):
                # Filter for high confidence triggers only
                return [t for t in result if t.get("confidence", 0) >= 0.7]
            else:
                return []
                
        except Exception as e:
            self.logger.error(f"Error detecting narration memory triggers: {e}")
            return []
    
    def process_narration_for_memories(self,
                                      narration: str,
                                      current_location: str,
                                      turn_number: int,
                                      scene_id: str) -> List[Dict[str, Any]]:
        """
        Complete pipeline for narration-triggered memories (memory resurfacing).
        
        IMPORTANT: Perception-based memories can resurface multiple times.
        Unlike intent-based memories, seeing a happy family can remind you
        of your mother every time, not just once.
        
        Args:
            narration: The narrative text
            current_location: Current location
            turn_number: Current turn
            scene_id: Current scene
            
        Returns:
            List of created/resurfaced memories with internal voice narration
        """
        
        # CRITERIA 1: Probability check (15% chance)
        if random.random() > self.narration_memory_probability:
            return []
        
        # CRITERIA 2: Minimum turn interval (at least 5 turns since last memory)
        if turn_number - self.last_memory_turn < self.min_turn_interval:
            return []
        
        # Detect memory triggers from narration
        triggers = self.detect_memory_triggers_from_narration(narration)
        
        if not triggers:
            return []
        
        # For narration-triggered memories:
        # - If memory exists → Resurface it with new internal voice
        # - If no memory exists → Create one
        # - Availability is determined by the emotional tone of the trigger
        
        resurfaced_memories = []
        for trigger in triggers:
            trigger_type = trigger.get("trigger_type", "backstory")
            trigger_context = trigger.get("trigger_context", "")
            topic_key = f"{trigger_type}:{trigger_context.lower()}"
            
            # Check if memory already exists for this topic
            memory_exists = topic_key in self.created_memory_topics
            
            if memory_exists:
                # RESURFACE existing memory with new internal voice
                # Don't create duplicate, just remind the vessel
                availability = self._determine_narration_availability(trigger, narration)
                
                memory_result = self._resurface_existing_memory(
                    trigger=trigger,
                    availability=availability,
                    narration_excerpt=trigger.get('narration_excerpt', ''),
                    current_location=current_location,
                    turn_number=turn_number,
                    scene_id=scene_id
                )
                
                if memory_result:
                    memory_result["triggered_by"] = "perception"
                    memory_result["narration_excerpt"] = trigger.get("narration_excerpt", "")
                    memory_result["is_resurfacing"] = True
                    resurfaced_memories.append(memory_result)
            else:
                # CREATE new memory (first time encountering this trigger)
                availability = self._determine_narration_availability(trigger, narration)
                
                memory_result = self.create_memory_from_intent(
                    trigger=trigger,
                    availability=availability,
                    user_intent=f"Triggered by perception: {trigger.get('narration_excerpt', '')}",
                    current_location=current_location,
                    turn_number=turn_number,
                    scene_id=scene_id
                )
                
                if memory_result:
                    memory_result["triggered_by"] = "perception"
                    memory_result["narration_excerpt"] = trigger.get("narration_excerpt", "")
                    memory_result["is_resurfacing"] = False
                    resurfaced_memories.append(memory_result)
        
        # Update last memory turn if any memories were created/resurfaced
        if resurfaced_memories:
            self.last_memory_turn = turn_number
        
        return resurfaced_memories
    
    def _resurface_existing_memory(self,
                                   trigger: Dict[str, Any],
                                   availability: IntentAvailability,
                                   narration_excerpt: str,
                                   current_location: str,
                                   turn_number: int,
                                   scene_id: str) -> Optional[Dict[str, Any]]:
        """
        Resurface an existing memory with a new internal voice.
        
        This is for when the vessel sees something that reminds them of
        a memory they already have. We don't create a duplicate memory,
        but we do generate a fresh internal voice reaction.
        
        Args:
            trigger: The detected trigger
            availability: Availability classification
            narration_excerpt: What triggered the memory
            current_location: Current location
            turn_number: Current turn
            scene_id: Current scene
            
        Returns:
            Dictionary with memory details and NEW internal voice
        """
        
        trigger_type = trigger.get("trigger_type", "backstory")
        trigger_context = trigger.get("trigger_context", "")
        
        prompt = f"""Generate a NEW internal voice for an EXISTING memory that has resurfaced.

**What Triggered the Memory:**
{narration_excerpt}

**Memory Trigger:**
Type: {trigger_type}
Context: {trigger_context}

**Availability Classification:**
{availability.value}

**IMPORTANT:**
This memory ALREADY EXISTS. The vessel already knows this about themselves.
We just need a NEW internal voice reaction to seeing something that reminded them.

**Guidelines:**

1. Generate a BRIEF internal thought (1-2 sentences)
2. Use first person PLURAL ("we", "our", "us") - NEVER use "I" or "my"
3. Should feel like a spontaneous reaction to what they just saw
4. Match the emotional tone of the availability:
   - AVAILABLE_NOW: Warm, nostalgic, longing
   - AVAILABLE_LATER: Wistful, bittersweet, distant
   - AVAILABLE_NEVER: Resigned, melancholic, accepting

**Examples:**

AVAILABLE_NOW (seeing happy family → remembering loving mother):
- "Man, we really miss our mom. We should go see her soon."
- "Seeing them together makes us think of mom. We need to call her."
- "We wonder what mom's doing right now. Probably worrying about us."

AVAILABLE_LATER (seeing couple → remembering ex):
- "That could've been us. If things had been different."
- "We hope Alex is happy now. We had something good once."
- "Seeing them hurts a little. Maybe we'll reach out to Alex someday."

AVAILABLE_NEVER (seeing father-daughter → never knowing father):
- "We'll never know what that feels like. It's just how it is."
- "Some people have that. We never did. Never will."
- "We've learned to be okay without it. Mostly."

**Response Format:**
Return JSON:

{{
    "internal_voice": "First-person internal thought (1-2 sentences)",
    "emotional_tone": "warm/wistful/resigned/melancholic/etc"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            if not result:
                self.logger.error("Failed to parse memory resurfacing response")
                return None
            
            # Get the existing memory from key memories system
            key_memories = get_key_memories()
            
            # Find the existing memory by searching for matching tags/category
            # For now, we'll create a simple result with the new internal voice
            # The actual memory already exists in the system
            
            return {
                "memory_title": f"{trigger_context.title()} Memory",
                "memory_description": f"(Existing memory about {trigger_context})",
                "internal_voice": result.get("internal_voice", ""),
                "emotional_tone": result.get("emotional_tone", "neutral"),
                "trigger_type": trigger_type,
                "trigger_context": trigger_context,
                "availability": availability.value
            }
            
        except Exception as e:
            self.logger.error(f"Error resurfacing memory: {e}")
            return None
    
    def _determine_narration_availability(self, trigger: Dict[str, Any], narration: str) -> IntentAvailability:
        """
        Determine availability for narration-triggered memories based on emotional tone.
        
        Args:
            trigger: The detected trigger
            narration: The full narration text
            
        Returns:
            IntentAvailability classification
        """
        
        prompt = f"""Determine the emotional tone of this memory trigger.

**Narration:**
{narration}

**Trigger:**
{trigger.get('trigger_context', '')}

**Emotional Tone Analysis:**

Classify the emotional tone of this trigger:

1. **POSITIVE/NOSTALGIC** - Warm, happy, comforting scenes
   - Example: Happy family picnic, couple in love, beautiful music
   - Result: AVAILABLE_NOW (vessel has positive memory)

2. **MELANCHOLIC/WISTFUL** - Bittersweet, distant, longing scenes
   - Example: Seeing what they once had, reminder of distance
   - Result: AVAILABLE_LATER (vessel has distant/strained memory)

3. **PAINFUL/TRIGGERING** - Sad, traumatic, loss-related scenes
   - Example: Seeing what they never had, reminder of loss
   - Result: AVAILABLE_NEVER (vessel has absence/loss memory)

**Response Format:**
Return JSON:

{{
    "emotional_tone": "positive/melancholic/painful",
    "availability": "exist/exist_not_here/does_not_exist",
    "reasoning": "Why this tone was chosen"
}}

Note: Use "exist" for positive/available now, "exist_not_here" for melancholic/available later, "does_not_exist" for painful/never available.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            if result and "availability" in result:
                # Map old-style values to new enum values
                availability_map = {
                    "available_now": "exist",
                    "available_later": "exist_not_here", 
                    "available_never": "does_not_exist",
                    "exist": "exist",
                    "exist_not_here": "exist_not_here",
                    "does_not_exist": "does_not_exist"
                }
                mapped_value = availability_map.get(result["availability"], "exist")
                return IntentAvailability(mapped_value)
            else:
                # Default to EXIST for positive triggers
                return IntentAvailability.EXIST
                
        except Exception as e:
            self.logger.error(f"Error determining narration availability: {e}")
            return IntentAvailability.EXIST


def display_memory_creation(memory_result: dict, narrative_context_manager=None, actor_name: str = "User Actor", show_internal_voice: bool = False):
    """
    Display formatted memory creation to user.
    Also records the internal voice in narrative context for future LLM calls.
    
    Args:
        memory_result: Result from create_memory_from_intent or _resurface_existing_memory
        narrative_context_manager: Optional narrative context manager to record event
        actor_name: Name of the actor (for context recording)
        show_internal_voice: Whether to show internal voice (False for inquiries since it's shown separately)
    """
    print(f"\n{Color.SUCCESS}{'═' * 60}{Color.RESET}")
    
    # Check if this is a resurfacing of existing memory
    is_resurfacing = memory_result.get("is_resurfacing", False)
    is_existing = memory_result.get("is_existing", False)
    
    # Check if this was triggered by perception
    if memory_result.get("triggered_by") == "perception":
        if is_resurfacing:
            print(f"{Color.SUCCESS}✨ MEMORY RESURFACED{Color.RESET}")
        else:
            print(f"{Color.SUCCESS}🔍 MEMORY UNCOVERED (from perception){Color.RESET}")
        print(f"{Color.SUCCESS}{'═' * 60}{Color.RESET}")
        
        # Show what triggered it
        if memory_result.get("narration_excerpt"):
            print(f"\n{Color.SYSTEM}Triggered by: {memory_result.get('narration_excerpt')}{Color.RESET}")
    else:
        # For inquiries, distinguish between new and recalled memories
        if is_existing:
            print(f"{Color.SUCCESS}💡 MEMORY RECALLED{Color.RESET}")
        else:
            print(f"{Color.SUCCESS}🔍 MEMORY UNCOVERED{Color.RESET}")
        print(f"{Color.SUCCESS}{'═' * 60}{Color.RESET}")
    
    # Show title and description
    print(f"\n{Color.INFO}📝 {memory_result.get('memory_title', 'Memory')}{Color.RESET}")
    print(f"{Color.NARRATIVE}{memory_result.get('memory_description', '')}{Color.RESET}")
    
    # Optionally show internal voice (only for perception-based memories, not inquiries)
    if show_internal_voice and memory_result.get('internal_voice'):
        print(f"\n{Color.WARNING}💭 Internal Voice:{Color.RESET}")
        print(f"{Color.NARRATIVE_ITALIC}{memory_result.get('internal_voice', '')}{Color.RESET}")
    
    print(f"\n{Color.SUCCESS}{'═' * 60}{Color.RESET}\n")
    
    # Record in narrative context if manager provided
    if narrative_context_manager:
        try:
            from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
            
            internal_voice = memory_result.get('internal_voice', '')
            
            if is_resurfacing:
                # Record memory resurfacing
                event_text = f"💭 {memory_result.get('trigger_context', 'Memory').title()}: {internal_voice}"
                narrative_context_manager.add_narrative_event(
                    event_type=NarrativeEventType.MEMORY_RESURFACING,
                    narrative_text=event_text,
                    actors_involved=[actor_name],
                    importance=NarrativeImportance.NOTABLE,
                    emotional_tone=memory_result.get('emotional_tone', 'reflective')
                )
            else:
                # Record new memory creation
                memory_title = memory_result.get('memory_title', 'Memory')
                memory_desc = memory_result.get('memory_description', '')
                event_text = f"📝 {memory_title}: {memory_desc}\n💭 {internal_voice}"
                
                narrative_context_manager.add_narrative_event(
                    event_type=NarrativeEventType.MEMORY_CREATION,
                    narrative_text=event_text,
                    actors_involved=[actor_name],
                    importance=NarrativeImportance.IMPORTANT,
                    emotional_tone=memory_result.get('emotional_tone', 'reflective')
                )
        except Exception as e:
            # Silently fail - context recording is optional enhancement
            pass

    # Best-effort: persist memory discovery/resurfacing into everlasting ContextStore
    try:
        if ContextStore is None:
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

        wt = None
        try:
            if get_master_time_coordinator is not None and WorldTime is not None:
                tc = get_master_time_coordinator()
                time_ctx = tc.get_current_time_context() if tc else None
                gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
                if gt is not None:
                    wt = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
        except Exception:
            wt = None

        actor_id = actor_name
        try:
            if get_spatial_manager is not None:
                spatial = get_spatial_manager()
                ctx = spatial.get_current_context() if spatial else None
                if ctx and getattr(ctx, 'actor_positions', None):
                    for aid, apos in ctx.actor_positions.items():
                        if getattr(apos, 'actor_name', None) == actor_name:
                            actor_id = str(aid)
                            break
        except Exception:
            actor_id = actor_name

        is_resurfacing = bool(memory_result.get('is_resurfacing', False))
        is_existing = bool(memory_result.get('is_existing', False))
        triggered_by = memory_result.get('triggered_by')

        event_type = 'MEMORY_RESURFACED' if is_resurfacing else 'MEMORY_UNCOVERED'
        # If this is an inquiry recall (existing), it's not "learned", just recalled.
        if not is_resurfacing and not is_existing and memory_result.get('trigger_type') in ['INQUIRY_KNOWLEDGE', 'INQUIRY_RETRIEVAL']:
            event_type = 'INFO_LEARNED'

        title = memory_result.get('memory_title', 'Memory')
        desc = memory_result.get('memory_description', '')
        internal_voice = memory_result.get('internal_voice', '')
        summary = f"{event_type}: {actor_name} - {title}"

        from pathlib import Path
        store = ContextStore(Path('simulation_data/context/context.db'))
        event_id = store.log_world_event(
            session_id=session_id,
            location_id=location_id,
            event_type=event_type,
            summary=summary,
            importance=6 if not is_resurfacing else 5,
            tags=['memory', 'vessel', 'discovery'] + ([str(triggered_by)] if triggered_by else []),
            payload={
                'actor_id': actor_id,
                'actor_ids': [actor_id],
                'actor_name': actor_name,
                'actor_names': [actor_name],
                'memory_id': memory_result.get('memory_id'),
                'memory_title': title,
                'memory_description': desc,
                'internal_voice': internal_voice,
                'trigger_type': memory_result.get('trigger_type'),
                'trigger_context': memory_result.get('trigger_context'),
                'availability': memory_result.get('availability'),
                'triggered_by': triggered_by,
                'narration_excerpt': memory_result.get('narration_excerpt'),
            },
            world_time=wt
        )

        try:
            if hasattr(store, 'remember'):
                memory_type = 'memory_resurfaced' if is_resurfacing else 'memory_uncovered'
                content = f"{title}: {desc}".strip()
                if internal_voice:
                    content = f"{content} | Internal voice: {internal_voice}"
                store.remember(
                    session_id=session_id,
                    actor_id=str(actor_id),
                    memory_type=memory_type,
                    content=content,
                    importance=6 if not is_resurfacing else 5,
                    pinned=False,
                    decay_rate=0.00018,
                    source_event_id=int(event_id) if event_id is not None else None,
                    world_time=wt
                )
        except Exception:
            pass
    except Exception:
        return
