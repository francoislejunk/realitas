"""
Skill & Sympathy Progression System

Tracks substantial growth in skills and sympathy relationships through actual use.
No XP points - just organic progression based on performance and interactions.

Skill Progression:
- Tracks extraordinary successes (success level 4+)
- After 10 extraordinary uses, 10% chance to increase skill by 1
- Realistic growth through practice

Sympathy Progression:
- Three ways sympathy can shift:
  1. Direct targeting (sympathy is the target status)
  2. Indirect effect (action affects sympathy as side effect)
  3. Interaction tracking (10 interactions, majority determines 50/50 roll)
- Makes relationships feel dynamic and realistic
"""

import json
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

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

from enum import Enum


class InteractionType(Enum):
    """Type of interaction between actors"""
    FRIENDLY = "friendly"
    HOSTILE = "hostile"
    NEUTRAL = "neutral"


class SkillProgressionTracker:
    """Tracks skill usage and progression for an actor"""
    
    def __init__(self, actor_name: str, storage_dir: Path):
        self.actor_name = actor_name
        self.storage_dir = storage_dir / "progression" / "skills"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Track extraordinary successes per skill
        # Format: {skill_name: [list of timestamps of extraordinary uses]}
        self.skill_usage: Dict[str, List[str]] = {}
        
        # Track progression history
        # Format: {skill_name: [list of progression events]}
        self.progression_history: Dict[str, List[Dict[str, Any]]] = {}
        
        self._load_data()
    
    def record_skill_use(self, skill_name: str, success_level: int, 
                        action_description: str) -> Optional[Dict[str, Any]]:
        """
        Record a skill use and check for progression.
        
        Args:
            skill_name: Name of the skill used
            success_level: Success level achieved (1-5)
            action_description: What the actor did
            
        Returns:
            Progression result if skill increased, None otherwise
        """
        # Only track extraordinary successes (level 4+)
        if success_level < 4:
            return None
        
        # Initialize tracking for this skill if needed
        if skill_name not in self.skill_usage:
            self.skill_usage[skill_name] = []
            self.progression_history[skill_name] = []
        
        # Record this extraordinary use
        timestamp = datetime.now().isoformat()
        self.skill_usage[skill_name].append(timestamp)
        
        # Check if we've hit 10 extraordinary uses
        if len(self.skill_usage[skill_name]) >= 10:
            # Roll for progression (10% chance)
            if random.random() < 0.10:
                # Skill increases!
                progression_event = {
                    "timestamp": timestamp,
                    "action": action_description,
                    "success_level": success_level,
                    "uses_before_increase": len(self.skill_usage[skill_name]),
                    "increase_amount": 1
                }
                
                self.progression_history[skill_name].append(progression_event)
                
                # Reset usage counter
                self.skill_usage[skill_name] = []
                
                self._save_data()
                
                return {
                    "skill_name": skill_name,
                    "increased": True,
                    "increase_amount": 1,
                    "reason": f"After {progression_event['uses_before_increase']} extraordinary uses"
                }
            else:
                # No progression this time, reset counter
                self.skill_usage[skill_name] = []
                self._save_data()
                
                return {
                    "skill_name": skill_name,
                    "increased": False,
                    "reason": "Progression roll failed (10% chance)"
                }
        
        # Not enough uses yet
        self._save_data()
        return None
    
    def get_skill_progress(self, skill_name: str) -> Dict[str, Any]:
        """Get current progress toward next skill increase"""
        uses = len(self.skill_usage.get(skill_name, []))
        history = self.progression_history.get(skill_name, [])
        
        return {
            "skill_name": skill_name,
            "extraordinary_uses": uses,
            "uses_needed": 10,
            "progress_percentage": (uses / 10) * 100,
            "total_increases": len(history),
            "last_increase": history[-1] if history else None
        }
    
    def _save_data(self):
        """Save progression data to disk"""
        try:
            file_path = self.storage_dir / f"{self.actor_name}_skills.json"
            data = {
                "actor_name": self.actor_name,
                "skill_usage": self.skill_usage,
                "progression_history": self.progression_history,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save skill progression: {e}")
    
    def _load_data(self):
        """Load progression data from disk"""
        try:
            file_path = self.storage_dir / f"{self.actor_name}_skills.json"
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.skill_usage = data.get("skill_usage", {})
                    self.progression_history = data.get("progression_history", {})
        except Exception as e:
            print(f"Warning: Could not load skill progression: {e}")


class SympathyProgressionTracker:
    """Tracks sympathy changes and progression between actors"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir / "progression" / "sympathy"
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        # Track interactions between actor pairs
        # Format: {(actor1, actor2): [list of interaction types]}
        self.interaction_history: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        
        # Track sympathy change history
        # Format: {(actor1, actor2): [list of change events]}
        self.sympathy_history: Dict[Tuple[str, str], List[Dict[str, Any]]] = {}
        
        self._load_data()

    def _get_current_world_time(self) -> Optional['WorldTime']:
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

    def _try_resolve_actor_id(self, actor_name: str) -> str:
        try:
            if get_spatial_manager is None:
                return actor_name
            spatial = get_spatial_manager()
            ctx = spatial.get_current_context() if spatial else None
            if not ctx or not getattr(ctx, 'actor_positions', None):
                return actor_name
            for aid, apos in ctx.actor_positions.items():
                if getattr(apos, 'actor_name', None) == actor_name:
                    return str(aid)
            return actor_name
        except Exception:
            return actor_name

    def _log_sympathy_shift(self, actor1: str, actor2: str, change_amount: int, reason: str, method: str) -> None:
        try:
            if ContextStore is None or change_amount == 0:
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

            a1_id = self._try_resolve_actor_id(actor1)
            a2_id = self._try_resolve_actor_id(actor2)

            store = ContextStore(Path('simulation_data/context/context.db'))
            world_time = self._get_current_world_time()
            direction = 'increased' if change_amount > 0 else 'decreased'
            summary = f"Sympathy {direction}: {actor1} -> {actor2} ({change_amount:+d}). Reason: {reason}"

            event_id = store.log_world_event(
                session_id=session_id,
                location_id=location_id,
                event_type='SYMPATHY_SHIFT',
                summary=summary,
                importance=7,
                tags=['sympathy', 'relationship'],
                payload={
                    'actor_ids': [a1_id, a2_id],
                    'actor_names': [actor1, actor2],
                    'proactor_name': actor1,
                    'reactor_name': actor2,
                    'proactor_id': a1_id,
                    'reactor_id': a2_id,
                    'change_amount': int(change_amount),
                    'reason': reason,
                    'method': method,
                },
                world_time=world_time
            )

            try:
                if hasattr(store, 'remember'):
                    content = f"{actor1} {direction} sympathy toward {actor2} ({change_amount:+d}): {reason}"
                    for aid in [str(a1_id), str(a2_id)]:
                        store.remember(
                            session_id=session_id,
                            actor_id=aid,
                            memory_type='sympathy_shift',
                            content=content,
                            importance=7,
                            pinned=False,
                            decay_rate=0.0002,
                            source_event_id=int(event_id) if event_id is not None else None,
                            world_time=world_time
                        )
            except Exception:
                pass
        except Exception:
            return
    
    def record_direct_sympathy_change(self, actor1: str, actor2: str, 
                                     change_amount: int, reason: str) -> Dict[str, Any]:
        """
        Record a direct sympathy change (Method 1: sympathy is target status).
        
        Args:
            actor1: First actor
            actor2: Second actor
            change_amount: How much sympathy changed
            reason: Why it changed
            
        Returns:
            Change event details
        """
        pair = self._normalize_pair(actor1, actor2)
        
        if pair not in self.sympathy_history:
            self.sympathy_history[pair] = []
        
        event = {
            "timestamp": datetime.now().isoformat(),
            "method": "direct_targeting",
            "change_amount": change_amount,
            "reason": reason,
            "actor1": actor1,
            "actor2": actor2
        }
        
        self.sympathy_history[pair].append(event)
        self._save_data()

        self._log_sympathy_shift(actor1=actor1, actor2=actor2, change_amount=change_amount, reason=reason, method='direct_targeting')
        
        return event
    
    def record_indirect_sympathy_effect(self, proactor: str, reactor: str,
                                       action_description: str, 
                                       action_polarity: str,
                                       success: bool) -> Optional[Dict[str, Any]]:
        """
        Record an indirect sympathy effect (Method 2: side effect of action).
        
        Args:
            proactor: Actor performing the action
            reactor: Actor being affected
            action_description: What happened
            action_polarity: "Additive" (helping) or "Subtractive" (harming)
            success: Whether the action succeeded
            
        Returns:
            Sympathy change event if applicable
        """
        # Determine sympathy change based on action type and success
        change_amount = 0
        
        if action_polarity == "Subtractive":
            # Harmful action
            if success:
                change_amount = -1  # Successful harm decreases sympathy
            else:
                change_amount = 0  # Failed harm might not change sympathy
        elif action_polarity == "Additive":
            # Helpful action
            if success:
                change_amount = 1  # Successful help increases sympathy
            else:
                change_amount = 0  # Failed help might not change sympathy
        
        if change_amount != 0:
            pair = self._normalize_pair(proactor, reactor)
            
            if pair not in self.sympathy_history:
                self.sympathy_history[pair] = []
            
            event = {
                "timestamp": datetime.now().isoformat(),
                "method": "indirect_effect",
                "change_amount": change_amount,
                "reason": f"{action_polarity} action: {action_description}",
                "proactor": proactor,
                "reactor": reactor,
                "success": success
            }
            
            self.sympathy_history[pair].append(event)
            self._save_data()

            self._log_sympathy_shift(actor1=proactor, actor2=reactor, change_amount=change_amount, reason=event.get('reason', ''), method='indirect_effect')
            
            return event
        
        return None
    
    def record_interaction(self, actor1: str, actor2: str, 
                          interaction_type: InteractionType,
                          action_description: str) -> Optional[Dict[str, Any]]:
        """
        Record an interaction and check for progression (Method 3: interaction tracking).
        
        Args:
            actor1: First actor
            actor2: Second actor
            interaction_type: FRIENDLY, HOSTILE, or NEUTRAL
            action_description: What happened
            
        Returns:
            Progression result if sympathy changed, None otherwise
        """
        pair = self._normalize_pair(actor1, actor2)
        
        if pair not in self.interaction_history:
            self.interaction_history[pair] = []
        
        # Record this interaction
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "type": interaction_type.value,
            "action": action_description,
            "actor1": actor1,
            "actor2": actor2
        }
        
        self.interaction_history[pair].append(interaction)
        
        # Check if we've hit 10 interactions
        if len(self.interaction_history[pair]) >= 10:
            # Count friendly vs hostile
            recent_10 = self.interaction_history[pair][-10:]
            friendly_count = sum(1 for i in recent_10 if i["type"] == "friendly")
            hostile_count = sum(1 for i in recent_10 if i["type"] == "hostile")
            
            # Determine majority
            majority_type = None
            if friendly_count > hostile_count:
                majority_type = "friendly"
            elif hostile_count > friendly_count:
                majority_type = "hostile"
            
            # Roll for progression (50/50 chance)
            if majority_type and random.random() < 0.50:
                # Sympathy shifts!
                change_amount = 1 if majority_type == "friendly" else -1
                
                if pair not in self.sympathy_history:
                    self.sympathy_history[pair] = []
                
                event = {
                    "timestamp": datetime.now().isoformat(),
                    "method": "interaction_tracking",
                    "change_amount": change_amount,
                    "reason": f"Majority {majority_type} interactions ({friendly_count} friendly, {hostile_count} hostile)",
                    "actor1": actor1,
                    "actor2": actor2,
                    "interactions_counted": 10
                }
                
                self.sympathy_history[pair].append(event)
                
                # Reset interaction counter
                self.interaction_history[pair] = []
                
                self._save_data()

                self._log_sympathy_shift(actor1=actor1, actor2=actor2, change_amount=change_amount, reason=event.get('reason', ''), method='interaction_tracking')
                
                return {
                    "actors": pair,
                    "changed": True,
                    "change_amount": change_amount,
                    "reason": event["reason"]
                }
            else:
                # No progression this time, reset counter
                self.interaction_history[pair] = []
                self._save_data()
                
                return {
                    "actors": pair,
                    "changed": False,
                    "reason": "Progression roll failed (50% chance)" if majority_type else "No clear majority"
                }
        
        # Not enough interactions yet
        self._save_data()
        return None
    
    def classify_interaction_type(self, action_description: str, 
                                  action_polarity: str,
                                  success: bool) -> InteractionType:
        """
        Classify an interaction as friendly, hostile, or neutral.
        
        Args:
            action_description: What happened
            action_polarity: "Additive" or "Subtractive"
            success: Whether action succeeded
            
        Returns:
            InteractionType classification
        """
        # Hostile keywords
        hostile_keywords = [
            'attack', 'hit', 'punch', 'kick', 'stab', 'shoot', 'harm', 'hurt',
            'threaten', 'intimidate', 'insult', 'mock', 'steal', 'rob',
            'fight', 'combat', 'strike', 'wound', 'injure'
        ]
        
        # Friendly keywords
        friendly_keywords = [
            'help', 'assist', 'heal', 'give', 'share', 'support', 'protect',
            'compliment', 'praise', 'thank', 'gift', 'donate', 'save',
            'comfort', 'encourage', 'befriend', 'ally', 'cooperate'
        ]
        
        action_lower = action_description.lower()
        
        # Check keywords
        is_hostile = any(kw in action_lower for kw in hostile_keywords)
        is_friendly = any(kw in action_lower for kw in friendly_keywords)
        
        # Use polarity as tiebreaker
        if is_hostile and not is_friendly:
            return InteractionType.HOSTILE
        elif is_friendly and not is_hostile:
            return InteractionType.FRIENDLY
        elif action_polarity == "Subtractive":
            return InteractionType.HOSTILE
        elif action_polarity == "Additive":
            return InteractionType.FRIENDLY
        else:
            return InteractionType.NEUTRAL
    
    def get_sympathy_progress(self, actor1: str, actor2: str) -> Dict[str, Any]:
        """Get current progress toward next sympathy change"""
        pair = self._normalize_pair(actor1, actor2)
        interactions = self.interaction_history.get(pair, [])
        history = self.sympathy_history.get(pair, [])
        
        # Count friendly vs hostile in current batch
        friendly_count = sum(1 for i in interactions if i["type"] == "friendly")
        hostile_count = sum(1 for i in interactions if i["type"] == "hostile")
        
        return {
            "actors": pair,
            "interactions_recorded": len(interactions),
            "interactions_needed": 10,
            "progress_percentage": (len(interactions) / 10) * 100,
            "friendly_count": friendly_count,
            "hostile_count": hostile_count,
            "current_lean": "friendly" if friendly_count > hostile_count else "hostile" if hostile_count > friendly_count else "neutral",
            "total_changes": len(history),
            "last_change": history[-1] if history else None
        }
    
    def _normalize_pair(self, actor1: str, actor2: str) -> Tuple[str, str]:
        """Normalize actor pair to consistent order"""
        return tuple(sorted([actor1, actor2]))
    
    def _save_data(self):
        """Save progression data to disk"""
        try:
            file_path = self.storage_dir / "sympathy_progression.json"
            
            # Convert tuple keys to strings for JSON
            interaction_history_serializable = {
                f"{k[0]}|{k[1]}": v for k, v in self.interaction_history.items()
            }
            sympathy_history_serializable = {
                f"{k[0]}|{k[1]}": v for k, v in self.sympathy_history.items()
            }
            
            data = {
                "interaction_history": interaction_history_serializable,
                "sympathy_history": sympathy_history_serializable,
                "last_updated": datetime.now().isoformat()
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Could not save sympathy progression: {e}")
    
    def _load_data(self):
        """Load progression data from disk"""
        try:
            file_path = self.storage_dir / "sympathy_progression.json"
            
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Convert string keys back to tuples
                    interaction_history_loaded = data.get("interaction_history", {})
                    self.interaction_history = {
                        tuple(k.split("|")): v for k, v in interaction_history_loaded.items()
                    }
                    
                    sympathy_history_loaded = data.get("sympathy_history", {})
                    self.sympathy_history = {
                        tuple(k.split("|")): v for k, v in sympathy_history_loaded.items()
                    }
        except Exception as e:
            print(f"Warning: Could not load sympathy progression: {e}")


class ProgressionManager:
    """Unified manager for skill and sympathy progression"""
    
    def __init__(self, storage_dir: Path):
        self.storage_dir = storage_dir
        self.skill_trackers: Dict[str, SkillProgressionTracker] = {}
        self.sympathy_tracker = SympathyProgressionTracker(storage_dir)
    
    def get_skill_tracker(self, actor_name: str) -> SkillProgressionTracker:
        """Get or create skill tracker for an actor"""
        if actor_name not in self.skill_trackers:
            self.skill_trackers[actor_name] = SkillProgressionTracker(
                actor_name, self.storage_dir
            )
        return self.skill_trackers[actor_name]
    
    def process_action_result(self, proactor_name: str, reactor_name: Optional[str],
                             skill_used: str, success_level: int,
                             action_description: str, action_polarity: str,
                             success: bool) -> Dict[str, Any]:
        """
        Process an action result for both skill and sympathy progression.
        
        Returns:
            Dictionary with skill and sympathy progression results
        """
        results = {
            "skill_progression": None,
            "sympathy_progression": None,
            "sympathy_indirect_effect": None
        }
        
        # Track skill progression
        skill_tracker = self.get_skill_tracker(proactor_name)
        skill_result = skill_tracker.record_skill_use(
            skill_used, success_level, action_description
        )
        results["skill_progression"] = skill_result
        
        # Track sympathy if there's a reactor
        if reactor_name:
            # Record indirect sympathy effect
            indirect_effect = self.sympathy_tracker.record_indirect_sympathy_effect(
                proactor_name, reactor_name, action_description, 
                action_polarity, success
            )
            results["sympathy_indirect_effect"] = indirect_effect
            
            # Record interaction for tracking
            interaction_type = self.sympathy_tracker.classify_interaction_type(
                action_description, action_polarity, success
            )
            interaction_result = self.sympathy_tracker.record_interaction(
                proactor_name, reactor_name, interaction_type, action_description
            )
            results["sympathy_progression"] = interaction_result
        
        return results
