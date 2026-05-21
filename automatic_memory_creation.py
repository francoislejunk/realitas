"""
Automatic Key Memory Creation System

Automatically creates key memories for important simulation events:
- Task completions
- Meeting new NUAs
- Combat victories/defeats
- Major discoveries
- Relationship changes
- Critical moments
"""

from typing import Optional, List
from datetime import datetime
from key_memories_system import (
    get_key_memories, 
    MemoryCategory, 
    MemoryImportance
)
from color_utils import Color
import logging


class AutomaticMemoryCreator:
    """Automatically creates key memories for important events"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.last_task_completed = None
        self.met_nuas = set()  # Track which NUAs we've met
    
    def on_task_completed(
        self,
        task_description: str,
        location: str,
        actors_involved: List[str],
        narrative: str,
        turn_number: int,
        scene_id: str
    ):
        """Create memory when task is completed"""
        try:
            key_memories = get_key_memories()
            
            # Determine importance based on task keywords
            importance = MemoryImportance.NOTABLE
            if any(word in task_description.lower() for word in ['critical', 'urgent', 'life', 'death', 'survive']):
                importance = MemoryImportance.CRITICAL
            elif any(word in task_description.lower() for word in ['important', 'major', 'significant']):
                importance = MemoryImportance.IMPORTANT
            
            memory_id = key_memories.create_memory(
                title=f"Completed: {task_description[:50]}",
                description=f"Successfully completed task: {task_description}",
                full_narrative=narrative,
                category=MemoryCategory.ACHIEVEMENT,
                importance=importance,
                location=location,
                actors_involved=actors_involved,
                tags=['task', 'completion', 'achievement'],
                turn_number=turn_number,
                scene_id=scene_id,
                auto_save=True
            )
            
            self.last_task_completed = task_description
            
            print(f"{Color.SUCCESS}✨ Key memory created: Task completed{Color.RESET}")
            
        except Exception as e:
            self.logger.error(f"Error creating task completion memory: {e}")
    
    def on_nua_first_met(
        self,
        nua_name: str,
        nua_occupation: str,
        location: str,
        first_impression: str,
        narrative: str,
        turn_number: int,
        scene_id: str
    ):
        """Create memory when meeting a new NUA"""
        if nua_name in self.met_nuas:
            return  # Already met this NUA
        
        try:
            key_memories = get_key_memories()
            
            memory_id = key_memories.create_memory(
                title=f"Met {nua_name}",
                description=f"First meeting with {nua_name}, a {nua_occupation}. {first_impression}",
                full_narrative=narrative,
                category=MemoryCategory.RELATIONSHIP,
                importance=MemoryImportance.NOTABLE,
                location=location,
                actors_involved=[nua_name],
                tags=['first_meeting', 'nua', nua_name.lower()],
                turn_number=turn_number,
                scene_id=scene_id,
                emotional_tone="curious",
                auto_save=True
            )
            
            self.met_nuas.add(nua_name)
            
            print(f"{Color.SUCCESS}✨ Key memory created: Met {nua_name}{Color.RESET}")
            
        except Exception as e:
            self.logger.error(f"Error creating first meeting memory: {e}")
    
    def on_combat_ended(
        self,
        victory: bool,
        opponent_name: str,
        location: str,
        narrative: str,
        turn_number: int,
        scene_id: str,
        casualties: Optional[List[str]] = None
    ):
        """Create memory when combat ends"""
        try:
            key_memories = get_key_memories()
            
            if victory:
                title = f"Victory against {opponent_name}"
                description = f"Emerged victorious in combat against {opponent_name}"
                importance = MemoryImportance.IMPORTANT
                emotional_tone = "triumphant"
            else:
                title = f"Defeated by {opponent_name}"
                description = f"Was defeated in combat by {opponent_name}"
                importance = MemoryImportance.CRITICAL
                emotional_tone = "defeated"
            
            actors_involved = [opponent_name]
            if casualties:
                actors_involved.extend(casualties)
                description += f". Casualties: {', '.join(casualties)}"
            
            memory_id = key_memories.create_memory(
                title=title,
                description=description,
                full_narrative=narrative,
                category=MemoryCategory.COMBAT,
                importance=importance,
                location=location,
                actors_involved=actors_involved,
                tags=['combat', 'victory' if victory else 'defeat', opponent_name.lower()],
                turn_number=turn_number,
                scene_id=scene_id,
                emotional_tone=emotional_tone,
                auto_save=True
            )
            
            print(f"{Color.SUCCESS}✨ Key memory created: Combat ended{Color.RESET}")
            
        except Exception as e:
            self.logger.error(f"Error creating combat memory: {e}")
    
    def on_major_discovery(
        self,
        discovery_type: str,
        discovery_description: str,
        location: str,
        narrative: str,
        turn_number: int,
        scene_id: str,
        actors_involved: Optional[List[str]] = None
    ):
        """Create memory for major discoveries"""
        try:
            key_memories = get_key_memories()
            
            # Determine category
            category = MemoryCategory.DISCOVERY
            if 'item' in discovery_type.lower() or 'found' in discovery_type.lower():
                category = MemoryCategory.ITEM
            elif 'location' in discovery_type.lower() or 'place' in discovery_type.lower():
                category = MemoryCategory.LOCATION
            elif 'secret' in discovery_type.lower() or 'revelation' in discovery_type.lower():
                category = MemoryCategory.REVELATION
            
            memory_id = key_memories.create_memory(
                title=f"Discovered: {discovery_description[:50]}",
                description=discovery_description,
                full_narrative=narrative,
                category=category,
                importance=MemoryImportance.IMPORTANT,
                location=location,
                actors_involved=actors_involved or [],
                tags=['discovery', discovery_type.lower()],
                turn_number=turn_number,
                scene_id=scene_id,
                emotional_tone="intrigued",
                auto_save=True
            )
            
            print(f"{Color.SUCCESS}✨ Key memory created: Major discovery{Color.RESET}")
            
        except Exception as e:
            self.logger.error(f"Error creating discovery memory: {e}")
    
    def on_relationship_milestone(
        self,
        nua_name: str,
        milestone_type: str,  # 'became_friends', 'became_enemies', 'betrayal', 'reconciliation'
        description: str,
        location: str,
        narrative: str,
        turn_number: int,
        scene_id: str
    ):
        """Create memory for relationship milestones"""
        try:
            key_memories = get_key_memories()
            
            importance_map = {
                'betrayal': MemoryImportance.CRITICAL,
                'became_enemies': MemoryImportance.IMPORTANT,
                'reconciliation': MemoryImportance.IMPORTANT,
                'became_friends': MemoryImportance.NOTABLE
            }
            
            emotional_map = {
                'betrayal': 'betrayed',
                'became_enemies': 'hostile',
                'reconciliation': 'relieved',
                'became_friends': 'warm'
            }
            
            memory_id = key_memories.create_memory(
                title=f"{milestone_type.replace('_', ' ').title()}: {nua_name}",
                description=description,
                full_narrative=narrative,
                category=MemoryCategory.RELATIONSHIP,
                importance=importance_map.get(milestone_type, MemoryImportance.NOTABLE),
                location=location,
                actors_involved=[nua_name],
                tags=['relationship', milestone_type, nua_name.lower()],
                turn_number=turn_number,
                scene_id=scene_id,
                emotional_tone=emotional_map.get(milestone_type, 'neutral'),
                auto_save=True
            )
            
            print(f"{Color.SUCCESS}✨ Key memory created: Relationship milestone{Color.RESET}")
            
        except Exception as e:
            self.logger.error(f"Error creating relationship memory: {e}")
    
    def on_critical_moment(
        self,
        moment_description: str,
        location: str,
        narrative: str,
        turn_number: int,
        scene_id: str,
        actors_involved: Optional[List[str]] = None,
        category: Optional[MemoryCategory] = None
    ):
        """Create memory for any critical moment"""
        try:
            key_memories = get_key_memories()
            
            memory_id = key_memories.create_memory(
                title=moment_description[:60],
                description=moment_description,
                full_narrative=narrative,
                category=category or MemoryCategory.DECISION,
                importance=MemoryImportance.CRITICAL,
                location=location,
                actors_involved=actors_involved or [],
                tags=['critical', 'important'],
                turn_number=turn_number,
                scene_id=scene_id,
                auto_save=True
            )
            
            print(f"{Color.SUCCESS}✨ Key memory created: Critical moment{Color.RESET}")
            
        except Exception as e:
            self.logger.error(f"Error creating critical moment memory: {e}")
    
    def on_death(
        self,
        deceased_name: str,
        cause: str,
        location: str,
        narrative: str,
        turn_number: int,
        scene_id: str,
        witnesses: Optional[List[str]] = None
    ):
        """Create memory when someone dies"""
        try:
            key_memories = get_key_memories()
            
            actors_involved = [deceased_name]
            if witnesses:
                actors_involved.extend(witnesses)
            
            memory_id = key_memories.create_memory(
                title=f"Death of {deceased_name}",
                description=f"{deceased_name} died. Cause: {cause}",
                full_narrative=narrative,
                category=MemoryCategory.LOSS,
                importance=MemoryImportance.CRITICAL,
                location=location,
                actors_involved=actors_involved,
                tags=['death', 'loss', deceased_name.lower()],
                turn_number=turn_number,
                scene_id=scene_id,
                emotional_tone="grief",
                auto_save=True
            )
            
            print(f"{Color.SUCCESS}✨ Key memory created: Death of {deceased_name}{Color.RESET}")
            
        except Exception as e:
            self.logger.error(f"Error creating death memory: {e}")


# Global instance
_automatic_memory_creator: Optional[AutomaticMemoryCreator] = None


def initialize_automatic_memory_creator() -> AutomaticMemoryCreator:
    """Initialize the global automatic memory creator"""
    global _automatic_memory_creator
    _automatic_memory_creator = AutomaticMemoryCreator()
    return _automatic_memory_creator


def get_automatic_memory_creator() -> AutomaticMemoryCreator:
    """Get the global automatic memory creator instance"""
    if _automatic_memory_creator is None:
        return initialize_automatic_memory_creator()
    return _automatic_memory_creator
