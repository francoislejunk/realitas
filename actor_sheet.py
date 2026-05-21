from __future__ import annotations
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import json
from survival_system import SurvivalManager, SurvivalNeed
from narrative_utils import get_narrative_descriptor, get_status_descriptor
from color_utils import Color
from goal_task_system import GoalTaskManager, Goal, Task, GoalImportance, TaskPriority, TaskCategory

# Import personality and reputation systems
try:
    from personality_mood_system import (
        CompletePersonalityProfile, OceanProfile, MBTIProfile, MoodState,
        MBTIType, MoodCategory, MoodIntensity, PersonalityGenerator,
        display_personality_section
    )
    PERSONALITY_SYSTEM_AVAILABLE = True
except ImportError:
    PERSONALITY_SYSTEM_AVAILABLE = False

try:
    from reputation_system import (
        ReputationSystem, ActorReputation, Title, TitleCategory, TitleRarity,
        get_reputation_system
    )
    REPUTATION_SYSTEM_AVAILABLE = True
except ImportError:
    REPUTATION_SYSTEM_AVAILABLE = False

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

    _LAST_STATUS_LOG_WMS: dict[tuple[str, str], int] = {}

    from spatial_context_system import get_spatial_manager
except Exception:
    get_spatial_manager = None


def _as_get_session_and_location_safe() -> tuple[str, Optional[str]]:
    session_id = 'default'
    location_id = None
    try:
        if get_spatial_manager is not None:
            spatial = get_spatial_manager()
            session_id = getattr(spatial, 'session_id', None) or session_id
            location_id = getattr(spatial, 'current_location', None)
    except Exception:
        pass
    return session_id, location_id


def _as_get_world_time_safe() -> Optional['WorldTime']:
    try:
        if get_master_time_coordinator is None or WorldTime is None:
            return None
        tc = get_master_time_coordinator()
        time_ctx = tc.get_current_time_context() if tc else None
        gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
        if gt is None:
            return None
        return WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
    except Exception:
        return None


def _as_safe_display_name(actor_name: str) -> str:
    try:
        if not actor_name:
            return "someone"

        try:
            from stranger_description_system import known_actors_tracker
            if known_actors_tracker is not None and known_actors_tracker.is_name_known(str(actor_name)):
                return str(actor_name)
        except Exception:
            pass

        try:
            _AS = globals().get('ActorSheet')
            reg = getattr(_AS, '_actor_registry', None) if _AS is not None else None
            sheet = reg.get(actor_name) if isinstance(reg, dict) else None
            if sheet is not None:
                try:
                    if getattr(sheet, 'is_user_actor', False):
                        return str(actor_name)
                except Exception:
                    pass
                ka = getattr(sheet, 'known_as', None)
                if ka:
                    return str(ka)
                pd = getattr(sheet, 'public_description', None)
                if pd:
                    return str(pd)
        except Exception:
            pass

        return "someone"
    except Exception:
        return "someone"


def _as_try_resolve_spatial_actor_id_by_name(actor_name: str) -> Optional[str]:
    try:
        if not actor_name or get_spatial_manager is None:
            return None
        spatial = get_spatial_manager()
        ctx = spatial.get_current_context() if spatial else None
        if not ctx or not getattr(ctx, 'actor_positions', None):
            return None
        for aid, apos in ctx.actor_positions.items():
            if getattr(apos, 'actor_name', None) == actor_name:
                return aid
        return None
    except Exception:
        return None


def _as_log_status_event(*, actor_name: str, status_type: str, old_value: Any, new_value: Any,
                         change: int, reason: str = "", importance: int = 5,
                         tags: Optional[List[str]] = None, payload_extra: Optional[Dict[str, Any]] = None,
                         memory_type: str = "status_changed", decay_rate: float = 0.00025) -> None:
    try:
        if ContextStore is None:
            return
        session_id, location_id = _as_get_session_and_location_safe()
        wt = _as_get_world_time_safe()
        actor_id = _as_try_resolve_spatial_actor_id_by_name(actor_name) or actor_name
        from pathlib import Path
        store = ContextStore(Path('simulation_data/context/context.db'))
        summary = f"{actor_name}'s {status_type} changed from {old_value} to {new_value} ({change:+d})"
        if reason:
            summary += f". Reason: {reason}"
        event_id = store.log_world_event(
            session_id=session_id,
            location_id=location_id,
            event_type='STATUS_CHANGED',
            summary=summary,
            importance=int(importance),
            tags=(tags or ['status']),
            payload={
                'actor_id': actor_id,
                'actor_ids': [actor_id],
                'actor_name': actor_name,
                'actor_names': [actor_name],
                'status_type': status_type,
                'old_value': old_value,
                'new_value': new_value,
                'change': int(change),
                'reason': reason,
                **(payload_extra or {}),
            },
            world_time=wt
        )

        try:
            if hasattr(store, 'remember'):
                store.remember(
                    session_id=session_id,
                    actor_id=str(actor_id),
                    memory_type=memory_type,
                    content=summary,
                    importance=int(importance),
                    pinned=False,
                    decay_rate=float(decay_rate),
                    source_event_id=int(event_id) if event_id is not None else None,
                    world_time=wt
                )
        except Exception:
            pass
    except Exception:
        return


class SFactorType(Enum):
    """Enumeration of the five core S-Factors."""
    SWIFTNESS = "Swiftness"
    SOCIABILITY = "Sociability"
    STURDINESS = "Sturdiness"
    SMARTS = "Smarts"
    SHADOW = "Shadow"

class StatusType(Enum):
    """Enumeration of the four core Status types."""
    STAMINA = "Stamina"
    SPIRIT = "Spirit"
    SUPPLY = "Supply"
    SYMPATHY = "Sympathy"

class SFactors:
    """A container for an Actor's S-Factor values (0-5)."""
    def __init__(self, swiftness: int = 3, sociability: int = 3, sturdiness: int = 3, smarts: int = 3, shadow: int = 3):
        self.factors = {
            SFactorType.SWIFTNESS: swiftness,
            SFactorType.SOCIABILITY: sociability,
            SFactorType.STURDINESS: sturdiness,
            SFactorType.SMARTS: smarts,
            SFactorType.SHADOW: shadow,
        }
        for factor_type, value in self.factors.items():
            if value is None:
                value = 0
                self.factors[factor_type] = value
            if not 0 <= value <= 5:
                raise ValueError(f"{factor_type.value} S-Factor must be between 0 and 5.")
        

    def get_factor(self, factor_type: SFactorType) -> int:
        return self.factors[factor_type]

    def __repr__(self):
        return ", ".join(f"{ft.name[:3]}={val}" for ft, val in self.factors.items())

    def to_dict(self) -> dict[str, int]:
        """Serializes S-Factors to a dictionary."""
        return {k.value: v for k, v in self.factors.items()}

class Status:
    """Represents a single dynamic status of an Actor with enhanced temporary/lasting shift support."""
    def __init__(self, status_type: StatusType, value: int = 3, max_value: int = 5, base_max_value: int = 5, min_value: int = None, money_amount: int = None):
        self.type = status_type
        self.base_max_value = base_max_value
        self.max_value = max_value
        self.min_value = -5 if status_type == StatusType.SYMPATHY else min_value
        
        if status_type == StatusType.SUPPLY:
            from supply_utils import get_supply_status_from_money, get_typical_money_for_status
            if money_amount is not None:
                self.money_amount = money_amount
                self.value = get_supply_status_from_money(money_amount)
            else:
                self.money_amount = get_typical_money_for_status(value)
                self.value = value
        else:
            self.value = self._clamp(value)
            self.money_amount = None
            
        self.lasting_shift_total = 0

    def _clamp(self, value: int) -> int:
        """Ensures status values remain within the valid range [min_value, max_value]."""
        if self.min_value is not None:
            value = max(value, self.min_value)
        return min(value, self.max_value)

    def modify(self, amount: int):
        """Modifies the status value by a given amount, clamping the result."""
        old_value = getattr(self, 'value', None)
        if self.type == StatusType.SUPPLY:
            from supply_utils import get_supply_status_from_money
            self.money_amount = max(0, self.money_amount + amount)
            self.value = get_supply_status_from_money(self.money_amount)
        else:
            self.value = self._clamp(self.value + amount)

        # Best-effort: persist significant status shifts into everlasting context DB
        try:
            # Noise filter: ignore tiny shifts unless they cause a critical threshold transition
            new_value = getattr(self, 'value', None)
            if old_value is None or new_value is None:
                return

            actual_change = int(new_value) - int(old_value) if isinstance(new_value, (int, float)) and isinstance(old_value, (int, float)) else amount

            significant = abs(int(amount)) >= 2
            critical_threshold = False
            band_crossing = False
            cadence_ok = False
            try:
                if self.type in (StatusType.STAMINA, StatusType.SPIRIT):
                    critical_threshold = (int(old_value) > 0 and int(new_value) == 0)
                if self.type == StatusType.SUPPLY:
                    # log larger money moves even if value bucket doesn't change
                    significant = significant or abs(int(amount)) >= 25

                # Band crossing: allow +/-1 logs when it changes the perceived band
                # Generic 0..max statuses use low/mid/high bands; sympathy handled elsewhere.
                if self.type not in (StatusType.SUPPLY, StatusType.SYMPATHY):
                    try:
                        ov = int(old_value)
                        nv = int(new_value)
                        mx = int(getattr(self, 'max_value', 5) or 5)
                        if mx <= 0:
                            mx = 5

                        def _band(v: int) -> str:
                            if v <= 1:
                                return 'low'
                            if v >= max(4, mx - 1):
                                return 'high'
                            return 'mid'

                        band_crossing = _band(ov) != _band(nv)
                    except Exception:
                        band_crossing = False

                # Cadence: for small deltas, only log occasionally to avoid spam
                try:
                    wms = None
                    if get_master_time_coordinator is not None and WorldTime is not None:
                        tc = get_master_time_coordinator()
                        time_ctx = tc.get_current_time_context() if tc else None
                        gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
                        if gt is not None:
                            wt = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
                            wms = wt.minutes_since_start
                    actor_name_for_key = getattr(getattr(self, '_owner_sheet', None), 'name', None)
                    st_key = getattr(self.type, 'value', str(self.type))
                    if actor_name_for_key and wms is not None:
                        last = _LAST_STATUS_LOG_WMS.get((str(actor_name_for_key), str(st_key)))
                        if last is None or int(wms) - int(last) >= 10:
                            cadence_ok = True
                except Exception:
                    cadence_ok = False
            except Exception:
                critical_threshold = False

            if not significant and not critical_threshold and not band_crossing and not cadence_ok:
                return

            actor_name = getattr(getattr(self, '_owner_sheet', None), 'name', None)
            if not actor_name:
                # Fallback: status object doesn't know owner; skip
                return

            try:
                if get_master_time_coordinator is not None and WorldTime is not None:
                    tc = get_master_time_coordinator()
                    time_ctx = tc.get_current_time_context() if tc else None
                    gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
                    if gt is not None:
                        wt = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
                        _LAST_STATUS_LOG_WMS[(str(actor_name), str(getattr(self.type, 'value', str(self.type))))] = int(wt.minutes_since_start)
            except Exception:
                pass

            importance = 6 if critical_threshold else (6 if abs(int(amount)) >= 3 else 5)
            _as_log_status_event(
                actor_name=actor_name,
                status_type=getattr(self.type, 'value', str(self.type)),
                old_value=old_value,
                new_value=new_value,
                change=int(amount),
                reason='',
                importance=importance,
                tags=['status', getattr(self.type, 'name', str(self.type)).lower()],
                payload_extra={'critical_threshold': bool(critical_threshold), 'band_crossing': bool(band_crossing), 'cadence_ok': bool(cadence_ok)},
                memory_type='status_changed',
                decay_rate=0.00025
            )
        except Exception:
            return
    
    def apply_lasting_shift(self, amount: int):
        """Applies a lasting shift that affects both current value and max capacity."""
        if self.type == StatusType.SUPPLY:
            from supply_utils import get_supply_status_from_money
            self.lasting_shift_total += amount
            self.max_value = max(0, self.base_max_value + self.lasting_shift_total)
            self.money_amount = max(0, self.money_amount + amount)
            self.value = get_supply_status_from_money(self.money_amount)
        else:
            self.lasting_shift_total += amount
            self.max_value = max(0, self.base_max_value + self.lasting_shift_total)
            self.value = self._clamp(self.value + amount)
    
    def is_dead(self) -> bool:
        """Check if this status indicates death (max capacity <= 0)."""
        return self.max_value <= 0

    def get_modifier(self) -> int:
        """Calculates the modifier based on the current status value."""
        if self.value == 0:
            return 3
        if self.value == 1:
            return 2
        if self.value == 2:
            return 1
        if self.value == 3:
            return 0
        if self.value == 4:
            return -1
        if self.value == 5:
            return -2
        return 0

    def __str__(self) -> str:
        """Returns a user-friendly string representation for display."""
        if self.type == StatusType.SUPPLY:
            from supply_utils import format_money_display, get_supply_descriptor
            money_display = format_money_display(self.money_amount)
            descriptor = get_supply_descriptor(self.value)
            return f"{self.type.name}: {money_display} ({descriptor})"
        else:
            return f"{self.type.name}: {self.value}/{self.max_value}"

    def to_dict(self) -> dict[str, int]:
        """Serializes the status to a dictionary."""
        return {"value": self.value, "max_value": self.max_value, "modifier": self.get_modifier()}

class Effect:
    """Represents a temporary or lasting effect on an actor."""
    def __init__(self, name: str, description: str, duration: int, effects: dict[StatusType, int]):
        self.name = name
        self.description = description
        self.duration = duration
        self.effects = effects

    def __repr__(self):
        return f"{self.name} ({self.duration} rounds left)"

class Item:
    """Represents an item in an Actor's inventory."""
    def __init__(self, name: str, description: str = "", supplement_bonus: int = 0):
        self.name = name
        self.description = description
        self.supplement_bonus = supplement_bonus

    def __repr__(self):
        return f"{self.name} (+{self.supplement_bonus})" if self.supplement_bonus else self.name

    def to_dict(self) -> dict[str, Any]:
        """Serializes the item to a dictionary."""
        return {"name": self.name, "description": self.description, "supplement_bonus": self.supplement_bonus}

class ActorSheet:
    """A comprehensive character sheet for an Actor in the UTAS system."""
    
    _actor_registry: dict[str, 'ActorSheet'] = {}
    _simulation_year: int = None  # Canonical simulation year - set by UA, used by all systems
    
    def __init__(self, name: str, s_factors: SFactors, personality_traits: dict[str, str], goals: list[str],
                 occupation: str = "Unemployed", affiliation: str = "None", faction: str = "None",
                 skills: Optional[dict[str, int]] = None, endowments: Optional[dict[str, int]] = None,
                 inventory: Optional[list[Item]] = None, memories: Optional[list[str]] = None,
                 effects: Optional[list[Effect]] = None, initial_money: Optional[int] = None,
                 age: int = 30, location: str = "Unknown", is_user_actor: bool = False,
                 simulation_year: Optional[int] = None, canonical_name: Optional[str] = None,
                 known_as: Optional[list[str]] = None, public_description: Optional[str] = None,
                 pronouns: Optional[str] = None):
        
        self.name = name
        self.canonical_name = canonical_name if canonical_name is not None else name
        self.known_as: list[str] = list(known_as) if known_as else []
        self.public_description = public_description
        if not self.public_description:
            try:
                if self.known_as:
                    ka0 = str(self.known_as[0]).strip()
                    if ka0:
                        if ka0.lower().startswith(('the ', 'a ', 'an ')):
                            self.public_description = ka0
                        else:
                            self.public_description = f"the {ka0}"
            except Exception:
                self.public_description = public_description
        self.occupation = occupation
        self.affiliation = affiliation
        self.faction = faction  # Primary faction/clan affiliation from RAG
        self.age = age if age is not None else 30  # Default age if not specified
        self.location = location if location is not None else "Unknown"  # Default location
        self.personality_traits = personality_traits
        self.goals = goals  # Legacy support - kept for backward compatibility
        
        # Simulation year - if provided, this actor's year becomes the canonical year
        self.simulation_year = simulation_year
        
        # Pronouns for pronoun resolution (he/him, she/her, they/them)
        self.pronouns = pronouns if pronouns is not None else "they/them"  # Default to they/them
        
        # Relationship context with user (for NPCs spawned from scenes)
        self.relationship_context = None  # Will be set for auto-spawned NPCs
        
        # Initialize new goal/task system
        self.goal_task_manager = GoalTaskManager()
        
        # Convert legacy goals to new system if provided
        if goals:
            for goal_desc in goals:
                self.goal_task_manager.add_goal(
                    description=goal_desc,
                    importance=GoalImportance.MAJOR  # Default to MAJOR for legacy goals
                )

        self.s_factors = s_factors
        self.skills = skills or {}
        self.endowments = endowments or {}
        
        stamina_max = max(s_factors.get_factor(SFactorType.SWIFTNESS), s_factors.get_factor(SFactorType.STURDINESS))
        spirit_max = max(s_factors.get_factor(SFactorType.SOCIABILITY), s_factors.get_factor(SFactorType.SMARTS))
        supply_max = 5
        
        if initial_money is not None:
            supply_money = initial_money
        else:
            supply_money = self._get_default_money_for_occupation(occupation)
        
        self.statuses = {
            StatusType.STAMINA: Status(StatusType.STAMINA, stamina_max, stamina_max, stamina_max),
            StatusType.SPIRIT: Status(StatusType.SPIRIT, spirit_max, spirit_max, spirit_max),
            StatusType.SUPPLY: Status(StatusType.SUPPLY, supply_max, supply_max, supply_max, money_amount=supply_money),
        }

        # Attach back-reference so Status.modify can attribute events to an actor
        try:
            for _st in self.statuses.values():
                setattr(_st, '_owner_sheet', self)
        except Exception:
            pass
        self.sympathy: dict[str, Status] = {}
        
        self.survival = SurvivalManager()
        
        self._initialize_sympathy_system()

        self.inventory = inventory if inventory is not None else []
        self.memories = memories if memories is not None else []
        self.effects = effects if effects is not None else []
        
        # Register built-in memories to Key Memories System
        if self.memories:
            self._register_builtin_memories()
        
        # Progressive revelation system - track what skills/endowments have been revealed
        # FIX BUG #13: Auto-reveal all skills/endowments for NPCs (only hide for UA)
        if not is_user_actor:
            self.revealed_skills: set[str] = set(self.skills.keys()) if self.skills else set()
            self.revealed_endowments: set[str] = set(k for k, v in (self.endowments.items() if self.endowments else []) if v > 0)
        else:
            self.revealed_skills: set[str] = set()
            self.revealed_endowments: set[str] = set()
        
        # Initialize personality profile (OCEAN, MBTI, Mood)
        # OCEAN is now derived from MBTI to ensure consistency
        self.personality_profile: Optional['CompletePersonalityProfile'] = None
        if PERSONALITY_SYSTEM_AVAILABLE:
            self.personality_profile = CompletePersonalityProfile.create_random()
        
        # Initialize reputation/titles list
        self.titles: list[str] = []  # List of title names for quick access
    
    @classmethod
    def set_simulation_year(cls, year: int):
        """
        Set the canonical simulation year globally for all systems.
        This should be called when the UA is created - the UA's year becomes
        the single source of truth for the entire simulation.
        
        Args:
            year: The simulation year (e.g., 1968, 1972)
        
        Example:
            ActorSheet.set_simulation_year(1968)  # All systems now use 1968
        """
        cls._simulation_year = year
    
    @classmethod
    def get_simulation_year(cls) -> Optional[int]:
        """
        Get the canonical simulation year.
        This is the single source of truth for all systems.
        
        Returns:
            The simulation year, or None if not set (RAG should provide the year)
        """
        return cls._simulation_year
    
    def _register_builtin_memories(self):
        """Register built-in memories to the Key Memories System for persistence"""
        try:
            from key_memories_system import get_key_memories, MemoryCategory, MemoryImportance
            
            key_memories = get_key_memories()
            
            for idx, memory_text in enumerate(self.memories, 1):
                # Create a memory for each built-in memory
                memory_id = key_memories.create_memory(
                    title=f"{self.name} - Background #{idx}",
                    description=memory_text,
                    full_narrative=f"Background memory about {self.name}: {memory_text}",
                    category=MemoryCategory.CHARACTER,
                    importance=MemoryImportance.NOTABLE,
                    location=self.location or "Unknown",
                    actors_involved=[self.name],
                    tags=["background", "builtin", self.name.lower().replace(" ", "_")],
                    turn_number=0,  # Created at character creation
                    scene_id="character_creation",
                    auto_save=False  # Batch save at the end
                )
            
            # Save all memories at once
            if self.memories:
                key_memories._save_memories()
                
        except Exception as e:
            # If Key Memories System isn't initialized yet, that's okay
            # Memories will still be in ActorSheet.memories
            pass
    
    def _get_default_money_for_occupation(self, occupation: str) -> int:
        """
        Get default money amount based on occupation/character type.
        Creators can override this with initial_money parameter.
        """
        occupation_lower = occupation.lower()
        
        if any(term in occupation_lower for term in ['ceo', 'executive', 'businessman', 'business', 'banker', 'lawyer', 'doctor', 'surgeon']):
            return 2_000_000
        
        elif any(term in occupation_lower for term in ['manager', 'engineer', 'consultant', 'architect', 'pilot']):
            return 200_000
        
        elif any(term in occupation_lower for term in ['teacher', 'nurse', 'technician', 'clerk', 'officer', 'soldier', 'warden', 'guard', 'sheriff', 'deputy']):
            return 30_000
        
        elif any(term in occupation_lower for term in ['thief', 'criminal', 'smuggler', 'mercenary', 'assassin', 'bounty', 'hunter', 'infiltrator', 'ops']):
            return 15_000
        
        elif any(term in occupation_lower for term in ['beggar', 'homeless', 'vagrant', 'prisoner', 'slave']):
            return 0
        
        elif any(term in occupation_lower for term in ['student', 'unemployed', 'intern']):
            return 2_000
        
        elif any(term in occupation_lower for term in ['cartographer', 'explorer', 'scout', 'tracker', 'ranger']):
            return 8_000
        
        else:
            return 5_000

    def _initialize_sympathy_system(self):
        """Register this actor in the registry. Sympathy created on first meeting."""
        # FIX BUG #12: Do NOT pre-populate sympathies for all actors
        # Sympathies should only be created when actors actually meet
        # This prevents showing relationships with NPCs the player hasn't encountered
        
        # Just register this actor - sympathies will be created dynamically when needed
        self._actor_registry[self.name] = self
    
    def ensure_sympathy_exists(self, other_actor_name: str, other_actor: 'ActorSheet' = None):
        """Ensure sympathy exists between this actor and another. Create if missing."""
        # FIX BUG #12: Create sympathy on first meeting, not at initialization
        if other_actor_name not in self.sympathy:
            sociability = self.s_factors.get_factor(SFactorType.SOCIABILITY)
            self.sympathy[other_actor_name] = Status(StatusType.SYMPATHY, 0, sociability, sociability)
            try:
                setattr(self.sympathy[other_actor_name], '_owner_sheet', self)
            except Exception:
                pass
            
            # Also create reverse sympathy if we have the other actor
            if other_actor and self.name not in other_actor.sympathy:
                other_sociability = other_actor.s_factors.get_factor(SFactorType.SOCIABILITY)
                other_actor.sympathy[self.name] = Status(StatusType.SYMPATHY, 0, other_sociability, other_sociability)
                try:
                    setattr(other_actor.sympathy[self.name], '_owner_sheet', other_actor)
                except Exception:
                    pass

    @classmethod
    def clear_registry(cls):
        """Clear the actor registry. Useful for testing or resetting scenarios."""
        cls._actor_registry.clear()

    def update_status(self, status_type: StatusType, amount: int, reason: str = None):
        """Updates a specific status, ensuring it stays within bounds, and optionally prints a reason."""
        if status_type in self.statuses:
            original_value = self.statuses[status_type].value
            self.statuses[status_type].value += amount
            self.statuses[status_type].value = max(0, min(self.statuses[status_type].value, self.statuses[status_type].max_value))
            new_value = self.statuses[status_type].value
            if original_value != new_value:
                actual_change = new_value - original_value
                reason_str = f"{reason.upper()}: " if reason else ""
                print(f"{Color.SYSTEM}* System: {reason_str}{_as_safe_display_name(self.name)}'s {status_type.name} changed from {original_value} to {new_value} ({actual_change:+}).{Color.RESET}")
                # If this update caused unconsciousness (first drop to 0), set a 1-turn knockout
                if status_type in (StatusType.STAMINA, StatusType.SPIRIT) and original_value > 0 and new_value == 0 and not self.is_dead():
                    current_ko = self.get_knockout_turns_remaining()
                    if current_ko <= 0:
                        self.set_knockout_duration(1)
                        print(f"{Color.WARNING}   • {_as_safe_display_name(self.name)} is knocked out and will miss at least 1 turn{Color.RESET}")

    def update_sympathy(self, target_actor_name: str, change: int, reason: str = ""):
        """Updates sympathy toward another actor, creating the relationship if it doesn't exist."""
        if target_actor_name not in self.sympathy:
            self.sympathy[target_actor_name] = Status(StatusType.SYMPATHY, 0)
            try:
                setattr(self.sympathy[target_actor_name], '_owner_sheet', self)
            except Exception:
                pass
        
        current_value = self.sympathy[target_actor_name].value
        new_value = max(-5, min(5, current_value + change))
        self.sympathy[target_actor_name].value = new_value

        # Best-effort: persist meaningful sympathy shifts into everlasting context DB
        try:
            # Noise filter: ignore +/-1 unless it crosses a relationship band boundary
            band_before = None
            band_after = None
            try:
                # simple bands: [-5,-3]=hostile, [-2,-1]=cold, [0]=neutral, [1,2]=warm, [3,5]=friendly
                def _band(v: int) -> str:
                    if v <= -3:
                        return 'hostile'
                    if v <= -1:
                        return 'cold'
                    if v == 0:
                        return 'neutral'
                    if v <= 2:
                        return 'warm'
                    return 'friendly'
                band_before = _band(int(current_value))
                band_after = _band(int(new_value))
            except Exception:
                band_before = None
                band_after = None

            should_log = abs(int(change)) >= 2 or (band_before is not None and band_after is not None and band_before != band_after)
            if should_log:
                _as_log_status_event(
                    actor_name=self.name,
                    status_type='Sympathy',
                    old_value=int(current_value),
                    new_value=int(new_value),
                    change=int(change),
                    reason=reason,
                    importance=6 if abs(int(change)) >= 2 else 5,
                    tags=['sympathy', 'relationship'],
                    payload_extra={
                        'target_actor_name': target_actor_name,
                        'band_before': band_before,
                        'band_after': band_after,
                    },
                    memory_type='sympathy_shift',
                    decay_rate=0.0002
                )
        except Exception:
            pass
        print(f"      * System: {_as_safe_display_name(self.name)}'s Sympathy for {_as_safe_display_name(target_actor_name)} changed by {change} -> {new_value}")

    def get_sympathy(self, target_actor_name: str) -> int:
        """Retrieves sympathy for a target, defaulting to neutral (0)."""
        return self.sympathy.get(target_actor_name, Status(StatusType.SYMPATHY, 0)).value

    def get_status_modifier(self, targeted_status: StatusType) -> int:
        """
        Calculates the status modifier based on the targeted status.
        Currently applies to Stamina, Spirit, and Supply.
        Includes survival penalties and temporary bonus restrictions.
        """
        if targeted_status in [StatusType.STAMINA, StatusType.SPIRIT, StatusType.SUPPLY]:
            base_modifier = self.statuses[targeted_status].get_modifier()
            
            survival_penalties = self.survival.calculate_survival_penalties()
            if targeted_status == StatusType.STAMINA:
                base_modifier -= survival_penalties.get("stamina", 0)
            elif targeted_status == StatusType.SPIRIT:
                base_modifier -= survival_penalties.get("spirit", 0)
            
            if self.survival.should_disable_temporary_bonuses() and base_modifier > 0:
                base_modifier = 0
            
            return base_modifier
        return 0

    def add_memory(self, memory: str):
        """Adds a new memory to the actor's sheet."""
        self.memories.append(memory)
        print(f"      * System: {self.name} now remembers: '{memory}'")
    
    def is_dead(self) -> bool:
        """Check if actor is dead due to any status max capacity reaching 0.
        Supply does not cause death - only Stamina and Spirit can kill an actor."""
        critical_statuses = [StatusType.STAMINA, StatusType.SPIRIT]
        return any(self.statuses[status_type].is_dead() for status_type in critical_statuses)
    
    def apply_lasting_status_shift(self, status_type: StatusType, amount: int):
        """Apply a lasting shift that affects both current value and max capacity."""
        if status_type in self.statuses:
            self.statuses[status_type].apply_lasting_shift(amount)
            print(f"      * System: {self.name}'s {status_type.name} lasting shift: {amount:+d} (Max capacity now: {self.statuses[status_type].max_value})")
            
            if self.is_dead():
                print(f"      * {Color.ERROR}CRITICAL: {self.name} has died due to status max capacity reaching 0!{Color.RESET}")
    
    def get_death_status(self) -> str:
        """Get description of which status caused death, if any."""
        dead_statuses = [status.type.name for status in self.statuses.values() if status.is_dead()]
        if dead_statuses:
            return f"Death due to {', '.join(dead_statuses)} max capacity reaching 0"
        return "Alive"
    
    def get_highest_s_factor_name(self) -> str:
        """Returns the name of the highest S-Factor for this actor."""
        highest_factor = max(self.s_factors.factors.items(), key=lambda x: x[1])
        return highest_factor[0].value

    def get_skills_string(self) -> str:
        """Returns a formatted string of the actor's skills and their narrative ranks."""
        if not self.skills:
            return "None"
        return ", ".join([f"{skill}: {get_narrative_descriptor(rank)}" for skill, rank in self.skills.items()])

    def get_statuses_string(self) -> str:
        """Returns a formatted string of the actor's statuses and their narrative descriptors."""
        if not self.statuses:
            return "None"
        return ", ".join([f"{status.type.name}: {get_status_descriptor(status.value)}" for status in self.statuses.values()])

    def to_dict(self) -> dict[str, Any]:
        """Serializes the entire actor sheet to a dictionary."""
        return {
            "name": self.name,
            "occupation": self.occupation,
            "affiliation": self.affiliation,
            "personality_traits": self.personality_traits,
            "goals": self.goals,
            "s_factors": self.s_factors.to_dict(),
            "statuses": {k.value: v.to_dict() for k, v in self.statuses.items()},
            "skills": self.skills,
            "endowments": self.endowments,
            "inventory": [item.to_dict() for item in self.inventory],
            "memories": self.memories,
            "effects": [effect.__dict__ for effect in self.effects],
            "sympathy": {name: status.to_dict() for name, status in self.sympathy.items()},
        }

    def get_statuses_string(self) -> str:
        """Returns a formatted string of the actor's statuses and their narrative descriptors."""
        if not self.statuses:
            return "None"
        return ", ".join([f"{status.type.name}: {get_status_descriptor(status.value)}" for status in self.statuses.values()])

    def get_skills_string(self) -> str:
        """Returns a formatted string of the actor's skills and their narrative descriptors."""
        if not self.skills:
            return "None"
        return ", ".join([f"{skill}: {get_narrative_descriptor(rank)}" for skill, rank in self.skills.items()])

    def is_defeated(self) -> bool:
        """Checks if the actor's stamina OR spirit has reached zero."""
        return (self.statuses[StatusType.STAMINA].value <= 0 or 
                self.statuses[StatusType.SPIRIT].value <= 0)
    
    def is_knocked_out(self) -> bool:
        """Checks if the actor is knocked out (defeated but not dead)."""
        return self.is_defeated() and not self.is_dead()
    
    def get_knockout_turns_remaining(self) -> int:
        """Get remaining knockout turns. Returns 0 if not knocked out."""
        return getattr(self, '_knockout_turns_remaining', 0)
    
    def set_knockout_duration(self, turns: int):
        """Set the number of turns this actor remains knocked out."""
        self._knockout_turns_remaining = max(turns, 0)
    
    def decrement_knockout_turns(self):
        """Decrement knockout turns remaining. Returns True if actor can wake up."""
        if hasattr(self, '_knockout_turns_remaining') and self._knockout_turns_remaining > 0:
            self._knockout_turns_remaining -= 1
            return self._knockout_turns_remaining == 0
        return False

    def display_summary(self):
        """Prints a concise, one-line summary of the actor's current statuses."""
        stamina = self.statuses[StatusType.STAMINA]
        spirit = self.statuses[StatusType.SPIRIT]
        supply = self.statuses[StatusType.SUPPLY]
        
        from supply_utils import format_money_display
        supply_money = format_money_display(supply.money_amount)
        
        summary = (
            f"    {Color.ACTOR_NAME}{self.name}{Color.RESET}: "
            f"{Color.STATUS}Stamina:{Color.RESET} {stamina.value}/{stamina.max_value} | "
            f"{Color.STATUS}Spirit:{Color.RESET} {spirit.value}/{spirit.max_value} | "
            f"{Color.STATUS}Supply:{Color.RESET} {supply.value}/{supply.max_value} ({supply_money})"
        )
        
        if self.sympathy:
            relationship_count = len(self.sympathy)
            summary += f" | {Color.STATUS}Relationships:{Color.RESET} {relationship_count}"
        
        print(summary)
    

    def _create_status_bar(self, value: int, max_value: int = 5) -> str:
        """Creates a visual status bar representation."""
        filled = "█" * value
        empty = "░" * (max_value - value)
        return f"{filled}{empty}"
    
    def _format_goal(self, goal: str, max_length: int = None) -> str:
        """Formats a goal string - no truncation, show full goal."""
        # Return full goal without truncation
        return goal
    
    def _create_sympathy_bar(self, value: int) -> str:
        """Creates a visual sympathy bar representation (-5 to +5 range)."""
        display_value = value + 5
        
        if value < 0:
            filled = "▓" * abs(value)
            empty = "░" * (5 - abs(value))
            neutral = "│"
            positive_empty = "░" * 5
            return f"{filled}{empty}{neutral}{positive_empty}"
        elif value > 0:
            negative_empty = "░" * 5
            neutral = "│"
            empty = "░" * (5 - value)
            filled = "█" * value
            return f"{negative_empty}{neutral}{empty}{filled}"
        else:
            negative_empty = "░" * 5
            neutral = "│"
            positive_empty = "░" * 5
            return f"{negative_empty}{neutral}{positive_empty}"
    
    def _get_sympathy_descriptor(self, value: int) -> str:
        """Returns a descriptive string for sympathy values using the same system as serendipity."""
        from narrative_utils import get_generic_descriptor
        return get_generic_descriptor(value)
    
    def reveal_skill(self, skill_name: str) -> bool:
        """
        Reveals a skill, making it visible in the actor sheet.
        Returns True if this is the first time the skill was revealed.
        """
        if skill_name not in self.revealed_skills:
            self.revealed_skills.add(skill_name)
            return True  # First revelation
        return False  # Already revealed
    
    def reveal_endowment(self, endowment_name: str) -> bool:
        """
        Reveals an endowment, making it visible in the actor sheet.
        Returns True if this is the first time the endowment was revealed.
        """
        if endowment_name not in self.revealed_endowments:
            self.revealed_endowments.add(endowment_name)
            return True  # First revelation
        return False  # Already revealed
    
    def is_skill_revealed(self, skill_name: str) -> bool:
        """Check if a skill has been revealed."""
        return skill_name in self.revealed_skills
    
    def is_endowment_revealed(self, endowment_name: str) -> bool:
        """Check if an endowment has been revealed."""
        return endowment_name in self.revealed_endowments

    def display_detailed(self):
        """Prints a beautifully formatted actor sheet with card-based layout."""
        stamina = self.statuses[StatusType.STAMINA]
        spirit = self.statuses[StatusType.SPIRIT]
        supply = self.statuses[StatusType.SUPPLY]
        
        internal_trait = self.personality_traits.get('internal', 'N/A')
        external_trait = self.personality_traits.get('external', 'N/A')
        
        # Use new goal system if available, fallback to legacy
        if self.goal_task_manager.goals:
            primary_goal = self.goal_task_manager.goals[0].description
            goal_progress = int(self.goal_task_manager.goals[0].progress * 100)
            goal_importance = self.goal_task_manager.goals[0].importance.value
        else:
            primary_goal = self.goals[0] if self.goals else "No specific goal"
            goal_progress = 0
            goal_importance = "unknown"
        
        formatted_goal = self._format_goal(primary_goal)
        current_task = self.get_current_task_description()
        
        print(f"{Color.INFO}┌─────────────────────────────────────────────────────────┐{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 🎭 {Color.ACTOR_NAME}{self.name:<20}{Color.RESET} {Color.INFO}│{Color.RESET} 💼 {Color.STATUS}{self.occupation:<25}{Color.RESET} {Color.INFO}│{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 🎂 Age: {Color.STATUS}{self.age}{Color.RESET} • 📍 Location: {Color.STATUS}{self.location} {ActorSheet.get_simulation_year()}{Color.RESET} {Color.INFO}│{Color.RESET}")
        if getattr(self, 'faction', 'None') != "None":
            print(f"{Color.INFO}│{Color.RESET} 🏛️ Faction: {Color.STATUS}{self.faction}{Color.RESET} {Color.INFO}│{Color.RESET}")
        print(f"{Color.INFO}│ ═══════════════════════════════════════════════════════ │{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 🧠 {Color.STATUS}{internal_trait}{Color.RESET} (Internal) • 🎯 {Color.STATUS}{external_trait}{Color.RESET} (External) {Color.INFO}│{Color.RESET}")
        
        # Display OCEAN, MBTI, Mood if personality profile exists
        if self.personality_profile and PERSONALITY_SYSTEM_AVAILABLE:
            ocean = self.personality_profile.ocean
            mbti = self.personality_profile.mbti
            mood = self.personality_profile.mood
            
            # OCEAN summary (dominant traits)
            ocean_traits = []
            if ocean.openness >= 4: ocean_traits.append("Open")
            elif ocean.openness <= 2: ocean_traits.append("Traditional")
            if ocean.conscientiousness >= 4: ocean_traits.append("Organized")
            elif ocean.conscientiousness <= 2: ocean_traits.append("Spontaneous")
            if ocean.extraversion >= 4: ocean_traits.append("Extraverted")
            elif ocean.extraversion <= 2: ocean_traits.append("Introverted")
            if ocean.agreeableness >= 4: ocean_traits.append("Agreeable")
            elif ocean.agreeableness <= 2: ocean_traits.append("Competitive")
            if ocean.neuroticism >= 4: ocean_traits.append("Sensitive")
            elif ocean.neuroticism <= 2: ocean_traits.append("Stable")
            ocean_summary = ", ".join(ocean_traits[:3]) if ocean_traits else "Balanced"
            
            # MBTI type
            mbti_type = mbti.mbti_type.value if hasattr(mbti.mbti_type, 'value') else str(mbti.mbti_type)
            
            # Mood display
            mood_cat = mood.primary_mood.value if hasattr(mood.primary_mood, 'value') else str(mood.primary_mood)
            mood_intensity = mood.intensity.value if hasattr(mood.intensity, 'value') else str(mood.intensity)
            
            print(f"{Color.INFO}│{Color.RESET} 🎭 MBTI: {Color.STATUS}{mbti_type}{Color.RESET} • OCEAN: {Color.STATUS}{ocean_summary}{Color.RESET} {Color.INFO}│{Color.RESET}")
            print(f"{Color.INFO}│{Color.RESET} 😊 Mood: {Color.STATUS}{mood_cat} ({mood_intensity}){Color.RESET} {Color.INFO}│{Color.RESET}")
        
        # Display titles/reputation summary
        if self.titles:
            titles_display = ", ".join(self.titles[:2])
            if len(self.titles) > 2:
                titles_display += f" (+{len(self.titles) - 2} more)"
            print(f"{Color.INFO}│{Color.RESET} 🏆 Titles: {Color.STATUS}{titles_display}{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        print(f"{Color.INFO}│{Color.RESET} 🎯 Goal: {Color.STATUS}{formatted_goal}{Color.RESET}")
        if self.goal_task_manager.goals:
            print(f"{Color.INFO}│{Color.RESET}    Progress: {goal_progress}% [{goal_importance}]")
        print(f"{Color.INFO}│{Color.RESET} 📋 Current Task: {Color.STATUS}{current_task}{Color.RESET}")
        print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} ⚡ {Color.INFO}CORE ATTRIBUTES{Color.RESET} {Color.INFO}│{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} Swiftness: {Color.STATUS}{get_narrative_descriptor(self.s_factors.get_factor(SFactorType.SWIFTNESS))}({self.s_factors.get_factor(SFactorType.SWIFTNESS)}){Color.RESET} │ Sociability: {Color.STATUS}{get_narrative_descriptor(self.s_factors.get_factor(SFactorType.SOCIABILITY))}({self.s_factors.get_factor(SFactorType.SOCIABILITY)}){Color.RESET} │ Sturdiness: {Color.STATUS}{get_narrative_descriptor(self.s_factors.get_factor(SFactorType.STURDINESS))}({self.s_factors.get_factor(SFactorType.STURDINESS)}){Color.RESET} {Color.INFO}│{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} Smarts: {Color.STATUS}{get_narrative_descriptor(self.s_factors.get_factor(SFactorType.SMARTS))}({self.s_factors.get_factor(SFactorType.SMARTS)}){Color.RESET} │ Shadow: {Color.STATUS}{get_narrative_descriptor(self.s_factors.get_factor(SFactorType.SHADOW))}({self.s_factors.get_factor(SFactorType.SHADOW)}){Color.RESET} {Color.INFO}│{Color.RESET}")
        print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 💪 {Color.INFO}STATUS & CONDITION{Color.RESET} {Color.INFO}│{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} Stamina: {Color.STATUS}{self._create_status_bar(stamina.value)}{Color.RESET} {stamina.value}/{stamina.max_value} {Color.STATUS}{get_status_descriptor(stamina.value)}{Color.RESET} ({stamina.get_modifier():+d}) {Color.INFO}│{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} Spirit:  {Color.STATUS}{self._create_status_bar(spirit.value)}{Color.RESET} {spirit.value}/{spirit.max_value} {Color.STATUS}{get_status_descriptor(spirit.value)}{Color.RESET} ({spirit.get_modifier():+d}) {Color.INFO}│{Color.RESET}")
        
        from supply_utils import get_supply_descriptor
        
        # print(f"DEBUG: {self.name} supply.money_amount = {supply.money_amount}")
        if supply.money_amount is None:
            migrated_money = self._get_default_money_for_occupation(self.occupation)
            supply.money_amount = migrated_money
            from supply_utils import get_supply_status_from_money
            supply.value = get_supply_status_from_money(migrated_money)
            # print(f"MIGRATED: {self.name} money set to ${migrated_money:,} based on occupation")
        # else:
            # print(f"DEBUG: {self.name} already has money: ${supply.money_amount:,}")
            
        exact_money = f"${supply.money_amount:,}"
        supply_desc = get_supply_descriptor(supply.value)
        print(f"{Color.INFO}│{Color.RESET} Supply:  {Color.STATUS}{self._create_status_bar(supply.value)}{Color.RESET} {supply.value}/{supply.max_value} {Color.STATUS}{supply_desc}{Color.RESET} ({exact_money}) ({supply.get_modifier():+d}) {Color.INFO}│{Color.RESET}")
        
        print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 🍽️  {Color.INFO}SURVIVAL NEEDS{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        survival_summary = self.survival.get_survival_summary()
        unmet_needs = self.survival.get_unmet_needs()
        
        for need_name, status_text in survival_summary.items():
            need_emoji = {"food": "🍞", "water": "💧", "sleep": "😴", "fulfillment": "💝"}
            emoji = need_emoji.get(need_name, "📋")
            
            if "CRITICAL" in status_text:
                color = Color.ERROR
            elif any(need.value == need_name for need in unmet_needs):
                color = Color.WARNING
            else:
                color = Color.STATUS
            
            print(f"{Color.INFO}│{Color.RESET} {emoji} {need_name.capitalize()}: {color}{status_text}{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        if unmet_needs:
            penalties = self.survival.calculate_survival_penalties()
            effects = []
            if penalties["stamina"] > 0:
                effects.append(f"Stamina -{penalties['stamina']}")
            if penalties["spirit"] > 0:
                effects.append(f"Spirit -{penalties['spirit']}")
            if self.survival.should_disable_temporary_bonuses():
                effects.append("Temp bonuses disabled")
            
            if effects:
                effects_text = ", ".join(effects)
                print(f"{Color.INFO}│{Color.RESET} {Color.ERROR}⚠️  Effects: {effects_text}{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 💝 {Color.INFO}RELATIONSHIPS & SYMPATHY{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        if self.sympathy:
            for actor_name, sympathy_status in self.sympathy.items():
                sympathy_value = sympathy_status.value
                sympathy_desc = self._get_sympathy_descriptor(sympathy_value)
                sympathy_bar = self._create_sympathy_bar(sympathy_value)
                print(f"{Color.INFO}│{Color.RESET} • {Color.STATUS}{actor_name:<20}{Color.RESET} {sympathy_bar} {sympathy_value:+2d} {Color.STATUS}{sympathy_desc}{Color.RESET} {Color.INFO}│{Color.RESET}")
        else:
            print(f"{Color.INFO}│{Color.RESET} • {Color.STATUS}No established relationships{Color.RESET} {Color.INFO}│{Color.RESET}")
    
        print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 🛠️  {Color.INFO}SKILLS & ABILITIES{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        if self.skills:
            for skill, rank in self.skills.items():
                # Show ??? for unrevealed skills
                if self.is_skill_revealed(skill):
                    print(f"{Color.INFO}│{Color.RESET} • {Color.STATUS}{skill}: {get_narrative_descriptor(rank)} ({rank}){Color.RESET} {Color.INFO}│{Color.RESET}")
                else:
                    print(f"{Color.INFO}│{Color.RESET} • {Color.SYSTEM}??? : ??? (???){Color.RESET} {Color.INFO}│{Color.RESET}")
        else:
            print(f"{Color.INFO}│{Color.RESET} • {Color.STATUS}None{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        print(f"{Color.INFO}│{Color.RESET} {Color.INFO}ENDOWMENT ABILITIES:{Color.RESET} {Color.INFO}│{Color.RESET}")
        if self.endowments and any(rank > 0 for rank in self.endowments.values()):
            for endowment_name, rank in self.endowments.items():
                if rank > 0:
                    # Show ??? for unrevealed endowments
                    if self.is_endowment_revealed(endowment_name):
                        print(f"{Color.INFO}│{Color.RESET} • {Color.STATUS}{endowment_name}: {get_narrative_descriptor(rank)} ({rank}){Color.RESET} {Color.INFO}│{Color.RESET}")
                    else:
                        print(f"{Color.INFO}│{Color.RESET} • {Color.SYSTEM}??? : ??? (???){Color.RESET} {Color.INFO}│{Color.RESET}")
        else:
            print(f"{Color.INFO}│{Color.RESET} • {Color.STATUS}None{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 🎒 {Color.INFO}SUPPLEMENTS{Color.RESET} {Color.INFO}│{Color.RESET}")
        supplement_items = [item for item in self.inventory if item.supplement_bonus > 0]
        if supplement_items:
            for item in supplement_items:
                bonus_desc = get_narrative_descriptor(item.supplement_bonus)
                print(f"{Color.INFO}│{Color.RESET} • {Color.STATUS}{item.name}: {bonus_desc} (+{item.supplement_bonus}){Color.RESET} {Color.INFO}│{Color.RESET}")
        else:
            print(f"{Color.INFO}│{Color.RESET} • {Color.STATUS}No equipment bonuses{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 💝 {Color.INFO}SYMPATHIES{Color.RESET} {Color.INFO}│{Color.RESET}")
        if self.sympathy:
            for actor_name, sympathy_status in self.sympathy.items():
                sympathy_desc = get_status_descriptor(sympathy_status.value)
                print(f"{Color.INFO}│{Color.RESET} • {Color.STATUS}{actor_name}: {sympathy_desc} ({sympathy_status.value}){Color.RESET} {Color.INFO}│{Color.RESET}")
        else:
            print(f"{Color.INFO}│{Color.RESET} • {Color.STATUS}No special relationships{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        has_additional_info = bool(self.inventory or self.memories or self.effects or self.affiliation != "None" or self.faction != "None")
        
        if has_additional_info:
            print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
            print(f"{Color.INFO}│{Color.RESET} 📋 {Color.INFO}ADDITIONAL INFO{Color.RESET} {Color.INFO}│{Color.RESET}")
            
            if self.affiliation != "None":
                print(f"{Color.INFO}│{Color.RESET} Affiliation: {Color.STATUS}{self.affiliation}{Color.RESET} {Color.INFO}│{Color.RESET}")

            if self.faction != "None":
                print(f"{Color.INFO}│{Color.RESET} Faction: {Color.STATUS}{self.faction}{Color.RESET} {Color.INFO}│{Color.RESET}")
            
            if self.memories:
                print(f"{Color.INFO}│{Color.RESET} 📚 {Color.INFO}BACKGROUND MEMORIES:{Color.RESET} {Color.INFO}│{Color.RESET}")
                for idx, memory in enumerate(self.memories, 1):
                    print(f"{Color.INFO}│{Color.RESET}   {idx}. {Color.STATUS}{memory}{Color.RESET}")
            
            if self.inventory:
                items_str = ", ".join([item.name for item in self.inventory])
                print(f"{Color.INFO}│{Color.RESET} Inventory: {Color.STATUS}{items_str}{Color.RESET} {Color.INFO}│{Color.RESET}")
            
            if self.effects:
                effects_str = ", ".join([effect.name for effect in self.effects])
                print(f"{Color.INFO}│{Color.RESET} Active Effects: {Color.STATUS}{effects_str}{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        # Display KEY MEMORIES section - fetch from KeyMemoriesSystem
        print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 🔑 {Color.INFO}KEY MEMORIES (Character-Defining){Color.RESET} {Color.INFO}│{Color.RESET}")
        
        # Fetch all important memories from KeyMemoriesSystem
        try:
            from key_memories_system import get_key_memories, MemoryCategory
            key_memories_system = get_key_memories()
            
            # Get ONLY character-defining background memories (created at character creation)
            # Filter by actor name tag AND character_background tag
            actor_tag = self.name.lower().replace(" ", "_")
            background_memories = [
                m for m in key_memories_system.memories.values()
                if "character_background" in m.tags and actor_tag in m.tags
            ]
            
            # Sort by importance (critical > important > notable > routine) then by timestamp
            importance_order = {"critical": 0, "important": 1, "notable": 2, "routine": 3}
            background_memories.sort(key=lambda m: (
                importance_order.get(m.importance.value if hasattr(m.importance, 'value') else m.importance, 4),
                -m.timestamp.timestamp() if hasattr(m.timestamp, 'timestamp') else -m.timestamp  # Most recent first within same importance
            ))
            
            if background_memories:
                for i, memory in enumerate(background_memories[:3], 1):  # Show max 3 background memories
                    # Get importance icon
                    importance_value = memory.importance.value if hasattr(memory.importance, 'value') else memory.importance
                    importance_icon = {"critical": "🔴", "important": "🟡", "notable": "🔵", "routine": "⚪"}.get(importance_value, "📝")
                    
                    memory_text = memory.description
                    # Word wrap long memories to fit within the box (account for icon)
                    max_width = 52  # Reduced to account for icon
                    if len(memory_text) <= max_width:
                        print(f"{Color.INFO}│{Color.RESET} {importance_icon} {Color.STATUS}{memory_text}{Color.RESET}")
                    else:
                        # Split into multiple lines
                        words = memory_text.split()
                        lines = []
                        current_line = ""
                        for word in words:
                            if len(current_line) + len(word) + 1 <= max_width:
                                current_line += (word + " ")
                            else:
                                lines.append(current_line.strip())
                                current_line = word + " "
                        if current_line:
                            lines.append(current_line.strip())
                        
                        # Print first line with icon
                        print(f"{Color.INFO}│{Color.RESET} {importance_icon} {Color.STATUS}{lines[0]}{Color.RESET}")
                        # Print continuation lines
                        for line in lines[1:]:
                            print(f"{Color.INFO}│{Color.RESET}    {Color.STATUS}{line}{Color.RESET}")
            else:
                print(f"{Color.INFO}│{Color.RESET} • {Color.SYSTEM}No key memories yet{Color.RESET} {Color.INFO}│{Color.RESET}")
        except Exception:
            print(f"{Color.INFO}│{Color.RESET} • {Color.SYSTEM}Key memories unavailable{Color.RESET} {Color.INFO}│{Color.RESET}")
        
        print(f"{Color.INFO}└─────────────────────────────────────────────────────────┘{Color.RESET}")

    def get_total_supplement_bonus(self) -> int:
        """Return 0 since supplements are selected contextually by LLM (ALWAYS ONLY ONE rule)."""
        # The InterpreterAgent/LLM selects the single most appropriate supplement
        # for each action context. This method exists only to prevent AttributeError.
        return 0
    
    # Goal/Task System Methods
    
    def add_goal(self, description: str, importance: GoalImportance = GoalImportance.MAJOR, 
                sub_goals: list[str] = None) -> Goal:
        """Add a new long-term goal"""
        goal = self.goal_task_manager.add_goal(description, importance, sub_goals)
        print(f"{Color.INFO}* {self.name} has a new goal: {description} [{importance.value}]{Color.RESET}")
        return goal
    
    def update_goal_progress(self, goal_index: int, progress: float):
        """Update progress on a goal"""
        if self.goal_task_manager.update_goal(goal_index, new_progress=progress):
            goal = self.goal_task_manager.goals[goal_index]
            print(f"{Color.INFO}* {self.name}'s goal progress updated: {goal.description} -> {int(progress * 100)}%{Color.RESET}")
    
    def add_task(self, description: str, priority: TaskPriority, 
                category: TaskCategory, related_goal: str = None) -> Task:
        """Add a new task"""
        task = self.goal_task_manager.add_task(description, priority, category, related_goal)
        print(f"{Color.SYSTEM}* New task for {self.name}: [{priority.value}] {description}{Color.RESET}")
        return task
    
    def set_current_task(self, task: Task):
        """Set the current active task"""
        self.goal_task_manager.set_current_task(task)
        print(f"{Color.INFO}→ {self.name} is now focused on: {task.description}{Color.RESET}")
    
    def complete_task(self, task: Task):
        """Mark a task as completed"""
        self.goal_task_manager.complete_task(task)
        print(f"{Color.SUCCESS}✓ {self.name} completed task: {task.description}{Color.RESET}")
    
    def get_current_task_description(self) -> str:
        """Get description of current task, or 'None' if no current task"""
        if self.goal_task_manager.current_task:
            return self.goal_task_manager.current_task.description
        return "None"
    
    def get_goals_summary(self) -> str:
        """Get a formatted summary of all goals"""
        if not self.goal_task_manager.goals:
            return "No defined goals"
        
        lines = []
        for i, goal in enumerate(self.goal_task_manager.goals):
            progress_pct = int(goal.progress * 100)
            lines.append(f"{i+1}. {goal.description} ({progress_pct}%)")
        return "\n".join(lines)
    
    def get_tasks_summary(self) -> str:
        """Get a formatted summary of active tasks"""
        active_tasks = self.goal_task_manager.get_active_tasks()
        if not active_tasks:
            return "No active tasks"
        
        lines = []
        for task in active_tasks:
            marker = "→" if task == self.goal_task_manager.current_task else " "
            lines.append(f"{marker} [{task.priority.value}] {task.description}")
        return "\n".join(lines)
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PERSONALITY SYSTEM METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def set_personality_profile(self, profile: 'CompletePersonalityProfile'):
        """Set the complete personality profile for this actor"""
        self.personality_profile = profile
    
    def get_personality_prompt_section(self) -> str:
        """Get the personality section for internal voice prompts"""
        if self.personality_profile and PERSONALITY_SYSTEM_AVAILABLE:
            return self.personality_profile.get_voice_prompt_section()
        
        # Fallback to basic personality traits
        internal = self.personality_traits.get('internal', 'Unknown')
        external = self.personality_traits.get('external', 'Unknown')
        return f"""**CHARACTER PERSONALITY**
Internal Trait: {internal}
External Trait: {external}
"""
    
    def update_mood(self, scene_description: str, recent_events: List[str] = None):
        """Update the actor's mood based on current context"""
        if not self.personality_profile or not PERSONALITY_SYSTEM_AVAILABLE:
            return
        
        try:
            from personality_mood_system import MoodAnalyzer
            analyzer = MoodAnalyzer()
            
            actor_state = {
                'stamina': self.statuses[StatusType.STAMINA].value,
                'spirit': self.statuses[StatusType.SPIRIT].value,
                'injuries': 'None'  # Could be enhanced
            }
            
            new_mood = analyzer.analyze_mood_from_context(
                current_mood=self.personality_profile.mood,
                scene_description=scene_description,
                recent_events=recent_events or [],
                actor_state=actor_state,
                ocean_profile=self.personality_profile.ocean
            )
            
            self.personality_profile.mood = new_mood
            
        except Exception as e:
            pass  # Silently fail if mood update fails
    
    def get_current_mood(self) -> Dict[str, Any]:
        """Get current mood state as dictionary"""
        if self.personality_profile and PERSONALITY_SYSTEM_AVAILABLE:
            mood = self.personality_profile.mood
            return {
                'primary_mood': mood.primary_mood.value,
                'intensity': mood.intensity.value,
                'stress_level': mood.stress_level,
                'energy_level': mood.energy_level,
                'confidence_level': mood.confidence_level,
                'voice_urgency': mood.get_voice_urgency(),
                'voice_tone': mood.get_voice_tone()
            }
        return {
            'primary_mood': 'calm',
            'intensity': 'moderate',
            'stress_level': 3,
            'energy_level': 5,
            'confidence_level': 5,
            'voice_urgency': 'normal',
            'voice_tone': 'neutral'
        }
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # REPUTATION/TITLE SYSTEM METHODS
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def add_title(self, title_name: str):
        """Add a title to this actor"""
        if title_name not in self.titles:
            self.titles.append(title_name)
            print(f"{Color.SUCCESS}🏆 {self.name} earned the title: \"{title_name}\"{Color.RESET}")
    
    def has_title(self, title_name: str) -> bool:
        """Check if actor has a specific title"""
        return title_name in self.titles
    
    def get_titles_display(self) -> str:
        """Get formatted titles for display"""
        if not self.titles:
            return "No titles"
        return ", ".join(f'"{t}"' for t in self.titles)
    
    def get_primary_title(self) -> Optional[str]:
        """Get the actor's primary (most recent) title"""
        return self.titles[-1] if self.titles else None
    
    def get_reputation_context(self) -> str:
        """Get reputation context for NUA interactions"""
        if not REPUTATION_SYSTEM_AVAILABLE:
            if self.titles:
                return f"{self.name} is known as {self.get_titles_display()}"
            return f"{self.name} has no notable reputation"
        
        try:
            rep_system = get_reputation_system()
            return rep_system.get_reputation_context_for_nua("observer", self.name)
        except Exception:
            return f"{self.name} has no notable reputation"
    
    def display_personality_and_titles(self):
        """Display personality profile and titles section"""
        # Display personality if available
        if self.personality_profile and PERSONALITY_SYSTEM_AVAILABLE:
            display_personality_section(self.personality_profile)
        
        # Display titles
        print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
        print(f"{Color.INFO}│{Color.RESET} 🏆 {Color.INFO}TITLES & REPUTATION{Color.RESET}")
        
        if self.titles:
            for title in self.titles[:5]:
                print(f"{Color.INFO}│{Color.RESET} • {Color.ACTOR_NAME}\"{title}\"{Color.RESET}")
            if len(self.titles) > 5:
                print(f"{Color.INFO}│{Color.RESET}   {Color.SYSTEM}... and {len(self.titles) - 5} more{Color.RESET}")
        else:
            print(f"{Color.INFO}│{Color.RESET} • {Color.SYSTEM}No titles earned yet{Color.RESET}")
