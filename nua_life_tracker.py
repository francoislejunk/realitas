"""
NUA Life Tracker - Living World System

NUAs (Non-User Actors) continue living their lives when not present. When you meet them again,
observable changes reflect the time that has passed.

Uses Rule of 3s time tracking to determine what happened during absence:
- 3 SECONDS: No observable change
- 3 MINUTES: Minor changes (mood, activity)
- Hours/Days/Weeks: Major changes (appearance, possessions, relationships, life events)

Philosophy: Every NUA has a life they're living, not just waiting for the player.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import random


class TimeScale(Enum):
    """Time scales for determining observable changes"""
    SECONDS = "seconds"
    MINUTES = "minutes"
    HOURS = "hours"
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"


class ObservableChangeType(Enum):
    """Types of observable changes in NUAs"""
    APPEARANCE = "appearance"  # Clothing, grooming, injuries
    POSSESSIONS = "possessions"  # New items, lost items
    MOOD = "mood"  # Emotional state
    LOCATION_CONTEXT = "location_context"  # What they're doing here
    RELATIONSHIP = "relationship"  # How they treat you
    LIFE_EVENT = "life_event"  # Major life changes
    ROUTINE = "routine"  # Expected vs unexpected presence


class NUALifeState:
    """Represents a NUA's life state at a point in time"""
    
    def __init__(self, nua_name: str):
        self.nua_name = nua_name
        self.last_seen_timestamp: Optional[str] = None
        self.last_seen_location: Optional[str] = None
        self.last_seen_activity: Optional[str] = None
        self.last_seen_appearance: Dict[str, str] = {}
        self.last_seen_possessions: List[str] = []
        self.last_seen_mood: Optional[str] = None
        self.ongoing_activities: List[Dict[str, Any]] = []  # Long-term activities
        self.life_events: List[Dict[str, Any]] = []  # Major events
        self.routine: Dict[str, Any] = {}  # Expected patterns
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "nua_name": self.nua_name,
            "last_seen_timestamp": self.last_seen_timestamp,
            "last_seen_location": self.last_seen_location,
            "last_seen_activity": self.last_seen_activity,
            "last_seen_appearance": self.last_seen_appearance,
            "last_seen_possessions": self.last_seen_possessions,
            "last_seen_mood": self.last_seen_mood,
            "ongoing_activities": self.ongoing_activities,
            "life_events": self.life_events,
            "routine": self.routine
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'NUALifeState':
        """Deserialize from dictionary"""
        state = cls(data["nua_name"])
        state.last_seen_timestamp = data.get("last_seen_timestamp")
        state.last_seen_location = data.get("last_seen_location")
        state.last_seen_activity = data.get("last_seen_activity")
        state.last_seen_appearance = data.get("last_seen_appearance", {})
        state.last_seen_possessions = data.get("last_seen_possessions", [])
        state.last_seen_mood = data.get("last_seen_mood")
        state.ongoing_activities = data.get("ongoing_activities", [])
        state.life_events = data.get("life_events", [])
        state.routine = data.get("routine", {})
        return state


class NUALifeTracker:
    """Tracks NUA lives when they're not present"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir / "nua_lives"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Track all NUAs
        self.nua_states: Dict[str, NUALifeState] = {}
        
        self._load_data()
    
    def record_nua_encounter(self, nua_name: str, location: str, 
                            activity: str, appearance: Dict[str, str],
                            possessions: List[str], mood: str,
                            current_time: str) -> None:
        """
        Record an encounter with a NUA to track their state.
        
        Args:
            nua_name: Name of the NUA
            location: Where they were encountered
            activity: What they were doing
            appearance: Observable appearance details
            possessions: Visible items they have
            mood: Their emotional state
            current_time: Current simulation time
        """
        if nua_name not in self.nua_states:
            self.nua_states[nua_name] = NUALifeState(nua_name)
        
        state = self.nua_states[nua_name]
        state.last_seen_timestamp = current_time
        state.last_seen_location = location
        state.last_seen_activity = activity
        state.last_seen_appearance = appearance.copy()
        state.last_seen_possessions = possessions.copy()
        state.last_seen_mood = mood
        
        self._save_data()
    
    def generate_reunion_narrative(self, nua_name: str, current_location: str,
                                   current_time: str, nua_occupation: str = None,
                                   nua_personality: str = None) -> Dict[str, Any]:
        """
        Generate narrative for reuniting with a NUA after time has passed.
        
        Args:
            nua_name: Name of the NUA
            current_location: Where you're meeting them now
            current_time: Current simulation time
            nua_occupation: NUA's occupation (for context)
            nua_personality: NUA's personality (for context)
            
        Returns:
            Dictionary with observable changes and narrative
        """
        if nua_name not in self.nua_states:
            # First encounter - no previous state
            return {
                "first_encounter": True,
                "narrative": f"You encounter {nua_name} for the first time.",
                "observable_changes": []
            }
        
        state = self.nua_states[nua_name]
        
        # Calculate time elapsed
        time_elapsed = self._calculate_time_elapsed(
            state.last_seen_timestamp, current_time
        )
        
        # Determine time scale
        time_scale = self._determine_time_scale(time_elapsed)
        
        # Generate observable changes based on time scale
        observable_changes = self._generate_observable_changes(
            state, time_scale, current_location, nua_occupation, nua_personality
        )
        
        # Generate narrative
        narrative = self._generate_reunion_narrative_text(
            nua_name, state, time_scale, observable_changes, current_location
        )
        
        return {
            "first_encounter": False,
            "time_elapsed": time_elapsed,
            "time_scale": time_scale.value,
            "last_seen_location": state.last_seen_location,
            "current_location": current_location,
            "observable_changes": observable_changes,
            "narrative": narrative
        }
    
    def _calculate_time_elapsed(self, last_seen: str, current: str) -> Dict[str, int]:
        """Calculate time elapsed between two timestamps"""
        try:
            # Import here to avoid circular dependency
            from npc_life_integration import calculate_time_difference
            return calculate_time_difference(last_seen, current)
        except Exception:
            return {
                "seconds": 0,
                "minutes": 0,
                "hours": 0,
                "days": 0,
                "weeks": 0
            }
    
    def _determine_time_scale(self, time_elapsed: Dict[str, int]) -> TimeScale:
        """Determine the primary time scale from elapsed time"""
        if time_elapsed["weeks"] > 0:
            return TimeScale.WEEKS
        elif time_elapsed["days"] > 0:
            return TimeScale.DAYS
        elif time_elapsed["hours"] > 0:
            return TimeScale.HOURS
        elif time_elapsed["minutes"] > 0:
            return TimeScale.MINUTES
        else:
            return TimeScale.SECONDS
    
    def _generate_observable_changes(self, state: NUALifeState, 
                                     time_scale: TimeScale,
                                     current_location: str,
                                     occupation: str = None,
                                     personality: str = None) -> List[Dict[str, Any]]:
        """
        Generate observable changes based on time scale.
        
        Returns list of changes with type, description, and diegetic observation.
        """
        changes = []
        
        if time_scale == TimeScale.SECONDS:
            # No observable changes in seconds
            return changes
        
        elif time_scale == TimeScale.MINUTES:
            # Minor changes: mood, immediate activity
            changes.extend(self._generate_minute_scale_changes(state, current_location))
        
        elif time_scale == TimeScale.HOURS:
            # Moderate changes: appearance, possessions, activity
            changes.extend(self._generate_hour_scale_changes(state, current_location, occupation))
        
        elif time_scale == TimeScale.DAYS:
            # Significant changes: appearance, possessions, mood, minor life events
            changes.extend(self._generate_day_scale_changes(state, current_location, occupation))
        
        elif time_scale == TimeScale.WEEKS:
            # Major changes: appearance, possessions, life events, relationships
            changes.extend(self._generate_week_scale_changes(state, current_location, occupation, personality))
        
        return changes
    
    def _generate_minute_scale_changes(self, state: NUALifeState, 
                                       location: str) -> List[Dict[str, Any]]:
        """Generate changes observable after minutes"""
        changes = []
        
        # Mood might have shifted
        if random.random() < 0.3:  # 30% chance
            new_moods = ["more relaxed", "slightly agitated", "focused", "distracted"]
            changes.append({
                "type": ObservableChangeType.MOOD.value,
                "description": f"Seems {random.choice(new_moods)}",
                "observation": f"Their demeanor has shifted slightly."
            })
        
        # Activity might have changed
        if state.last_seen_location == location:
            activities = ["reading a menu", "checking their phone", "talking to someone", 
                         "waiting", "finishing a drink"]
            changes.append({
                "type": ObservableChangeType.LOCATION_CONTEXT.value,
                "description": f"Now {random.choice(activities)}",
                "observation": f"They're engaged in a different activity than before."
            })
        
        return changes
    
    def _generate_hour_scale_changes(self, state: NUALifeState,
                                     location: str, occupation: str) -> List[Dict[str, Any]]:
        """Generate changes observable after hours"""
        changes = []
        
        # Appearance changes (minor)
        appearance_changes = [
            ("clothing", "changed clothes", "They're wearing different clothes than before."),
            ("grooming", "hair slightly disheveled", "Their appearance is less put-together."),
            ("grooming", "freshly groomed", "They look more put-together than before."),
            ("fatigue", "looks tired", "They appear more fatigued."),
            ("energy", "looks refreshed", "They seem more energized.")
        ]
        
        if random.random() < 0.5:  # 50% chance
            category, desc, obs = random.choice(appearance_changes)
            changes.append({
                "type": ObservableChangeType.APPEARANCE.value,
                "category": category,
                "description": desc,
                "observation": obs
            })
        
        # Possessions (minor changes)
        possession_changes = [
            ("carrying a bag", "They're now carrying a bag they didn't have before."),
            ("has a coffee cup", "They're holding a fresh coffee."),
            ("wearing a jacket", "They've put on a jacket."),
            ("no longer has bag", "The bag they had is gone.")
        ]
        
        if random.random() < 0.4:  # 40% chance
            desc, obs = random.choice(possession_changes)
            changes.append({
                "type": ObservableChangeType.POSSESSIONS.value,
                "description": desc,
                "observation": obs
            })
        
        # Location context
        if state.last_seen_location != location:
            changes.append({
                "type": ObservableChangeType.LOCATION_CONTEXT.value,
                "description": f"Moved from {state.last_seen_location} to {location}",
                "observation": f"You last saw them at {state.last_seen_location}, now they're here."
            })
        else:
            # Still here - why?
            reasons = [
                "still working their shift",
                "seems to be a regular here",
                "waiting for someone",
                "enjoying the atmosphere"
            ]
            changes.append({
                "type": ObservableChangeType.ROUTINE.value,
                "description": f"Still at {location}",
                "observation": f"They're still here - {random.choice(reasons)}."
            })
        
        return changes
    
    def _generate_day_scale_changes(self, state: NUALifeState,
                                    location: str, occupation: str) -> List[Dict[str, Any]]:
        """Generate changes observable after days"""
        changes = []
        
        # Appearance changes (moderate)
        appearance_changes = [
            ("clothing", "wearing completely different outfit", "They're dressed quite differently."),
            ("grooming", "new haircut", "They've gotten a haircut."),
            ("grooming", "facial hair grown out", "Their facial hair has grown."),
            ("injury", "has a bandage on their hand", "They have a bandaged hand."),
            ("injury", "has a bruise", "You notice a bruise on their face."),
            ("health", "looks healthier", "They look healthier than before."),
            ("health", "looks under the weather", "They seem a bit under the weather.")
        ]
        
        # Multiple appearance changes possible
        for _ in range(random.randint(1, 2)):
            if random.random() < 0.6:  # 60% chance each
                category, desc, obs = random.choice(appearance_changes)
                changes.append({
                    "type": ObservableChangeType.APPEARANCE.value,
                    "category": category,
                    "description": desc,
                    "observation": obs
                })
        
        # Possessions (moderate changes)
        possession_changes = [
            ("new phone", "They have a new phone."),
            ("new watch", "They're wearing a new watch."),
            ("new bag", "They have a different bag."),
            ("new accessory", "They're wearing new jewelry/accessory.")
        ]
        
        if random.random() < 0.5:  # 50% chance
            desc, obs = random.choice(possession_changes)
            changes.append({
                "type": ObservableChangeType.POSSESSIONS.value,
                "description": desc,
                "observation": obs
            })
        
        # Minor life events
        life_events = [
            ("Started a new hobby", "They mention starting a new hobby."),
            ("Had a birthday", "They mention it was their birthday recently."),
            ("Visited family", "They mention visiting family."),
            ("Took a short trip", "They mention taking a trip."),
            ("Had a rough week", "They mention having a rough week."),
            ("Got good news", "They seem to have received good news.")
        ]
        
        if random.random() < 0.4:  # 40% chance
            desc, obs = random.choice(life_events)
            changes.append({
                "type": ObservableChangeType.LIFE_EVENT.value,
                "description": desc,
                "observation": obs
            })
        
        return changes
    
    def _generate_week_scale_changes(self, state: NUALifeState,
                                     location: str, occupation: str,
                                     personality: str) -> List[Dict[str, Any]]:
        """Generate changes observable after weeks"""
        changes = []
        
        # Major appearance changes
        appearance_changes = [
            ("style", "completely different style", "Their entire style has changed dramatically."),
            ("grooming", "significant hair change", "They've made a major change to their hair."),
            ("weight", "lost weight", "They appear to have lost weight."),
            ("weight", "gained weight", "They appear to have gained weight."),
            ("fitness", "looks more fit", "They look more physically fit."),
            ("injury", "recovering from injury", "They're recovering from an injury."),
            ("health", "looks much healthier", "They look significantly healthier."),
            ("health", "looks worn down", "They look worn down.")
        ]
        
        # Multiple major changes
        for _ in range(random.randint(1, 3)):
            if random.random() < 0.7:  # 70% chance each
                category, desc, obs = random.choice(appearance_changes)
                changes.append({
                    "type": ObservableChangeType.APPEARANCE.value,
                    "category": category,
                    "description": desc,
                    "observation": obs
                })
        
        # Major possession changes
        possession_changes = [
            ("new expensive item", "They have an expensive new item."),
            ("lost valuable", "They no longer have their valuable item."),
            ("upgraded gear", "They've upgraded their equipment."),
            ("different accessories", "They have completely different accessories.")
        ]
        
        if random.random() < 0.6:  # 60% chance
            desc, obs = random.choice(possession_changes)
            changes.append({
                "type": ObservableChangeType.POSSESSIONS.value,
                "description": desc,
                "observation": obs
            })
        
        # Major life events
        life_events = [
            ("Changed jobs", "They mention changing jobs."),
            ("Got promoted", "They mention getting promoted."),
            ("Started relationship", "They mention starting a relationship."),
            ("Ended relationship", "They mention a breakup."),
            ("Moved apartments", "They mention moving."),
            ("Major purchase", "They mention making a major purchase."),
            ("Family event", "They mention a major family event."),
            ("Health scare", "They mention a health scare."),
            ("Achievement", "They mention a significant achievement.")
        ]
        
        # Multiple life events possible
        for _ in range(random.randint(1, 2)):
            if random.random() < 0.6:  # 60% chance each
                desc, obs = random.choice(life_events)
                changes.append({
                    "type": ObservableChangeType.LIFE_EVENT.value,
                    "description": desc,
                    "observation": obs
                })
        
        # Relationship change (based on sympathy progression)
        relationship_changes = [
            ("warmer", "They seem warmer toward you."),
            ("cooler", "They seem more distant."),
            ("friendlier", "They're noticeably friendlier."),
            ("more reserved", "They're more reserved than before.")
        ]
        
        if random.random() < 0.5:  # 50% chance
            desc, obs = random.choice(relationship_changes)
            changes.append({
                "type": ObservableChangeType.RELATIONSHIP.value,
                "description": desc,
                "observation": obs
            })
        
        return changes
    
    def _generate_reunion_narrative_text(self, nua_name: str, state: NUALifeState,
                                         time_scale: TimeScale, 
                                         observable_changes: List[Dict[str, Any]],
                                         current_location: str) -> str:
        """Generate narrative text for the reunion"""
        
        if time_scale == TimeScale.SECONDS:
            return f"You see {nua_name} again, just moments after you last saw them."
        
        elif time_scale == TimeScale.MINUTES:
            base = f"You encounter {nua_name} again after a few minutes."
            if observable_changes:
                change_desc = " ".join([c["observation"] for c in observable_changes])
                return f"{base} {change_desc}"
            return base
        
        elif time_scale == TimeScale.HOURS:
            base = f"You run into {nua_name} again after several hours."
            if observable_changes:
                observations = []
                for change in observable_changes:
                    observations.append(change["observation"])
                change_desc = " ".join(observations)
                return f"{base} {change_desc}"
            return base
        
        elif time_scale == TimeScale.DAYS:
            base = f"You encounter {nua_name} again after days have passed."
            if observable_changes:
                observations = []
                for change in observable_changes:
                    observations.append(change["observation"])
                change_desc = " ".join(observations)
                return f"{base} {change_desc}"
            return base
        
        elif time_scale == TimeScale.WEEKS:
            base = f"You see {nua_name} again after weeks apart."
            if observable_changes:
                observations = []
                for change in observable_changes:
                    observations.append(change["observation"])
                change_desc = " ".join(observations)
                return f"{base} {change_desc} It's clear that life has continued for them in your absence."
            return base
        
        return f"You encounter {nua_name} again."
    
    def _save_data(self):
        """Save NUA life states to disk"""
        try:
            file_path = self.storage_dir / "nua_life_states.json"
            data = {
                "nua_states": {
                    name: state.to_dict() 
                    for name, state in self.nua_states.items()
                },
                "last_updated": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save NUA life states: {e}")
    
    def _load_data(self):
        """Load NUA life states from disk"""
        try:
            file_path = self.storage_dir / "nua_life_states.json"
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    nua_states_data = data.get("nua_states", {})
                    self.nua_states = {
                        name: NUALifeState.from_dict(state_data)
                        for name, state_data in nua_states_data.items()
                    }
        except Exception as e:
            print(f"Warning: Could not load NUA life states: {e}")
