"""
Master Time Coordinator - Single Source of Truth for All Time Management

This system eliminates race conditions by centralizing all time advancement
through a single coordinator that manages multiple time tracking systems.
"""

from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from enum import Enum
import time

from rule_of_3s import RuleOf3Category
from time_cycle_system import TimeCycleTracker, GameTime
from simulation_time_tracker import SimulationTimeTracker
from reactor_time_system import ReactorTimeManager


class TimeEventType(Enum):
    """Types of events that can advance time"""
    USER_ACTION = "user_action"
    SURVIVAL_ACTION = "survival_action"
    RECOVERY_PROCESS = "recovery_process"
    SCENE_TRANSITION = "scene_transition"
    ENCOUNTER_TURN = "encounter_turn"
    SYSTEM_PROCESS = "system_process"


@dataclass
class TimeAdvancementRequest:
    """Request to advance time with full context"""
    event_type: TimeEventType
    rule_of_3_category: RuleOf3Category
    requester_system: str
    actor_name: Optional[str] = None
    description: str = ""
    custom_duration_hours: Optional[float] = None
    
    def __post_init__(self):
        if not self.description:
            self.description = f"{self.event_type.value} by {self.requester_system}"


@dataclass
class TimeAdvancementResult:
    """Result of time advancement with all system updates"""
    previous_time: GameTime
    new_time: GameTime
    time_of_day_changed: bool
    duration_advanced_hours: float
    duration_advanced_seconds: int
    affected_systems: List[str]
    atmospheric_changes: Dict[str, Any]


class MasterTimeCoordinator:
    """
    Centralized time coordinator that manages all time advancement.
    
    CRITICAL: This is the ONLY system allowed to advance time.
    All other systems must request time advancement through this coordinator.
    """
    
    def __init__(self, starting_hour: int = 9, starting_minute: int = 0, starting_day: int = 1):
        # Initialize all time tracking systems
        self.time_tracker = TimeCycleTracker(starting_hour, starting_minute, starting_day)
        self.simulation_tracker = SimulationTimeTracker()
        self.reactor_time_manager = ReactorTimeManager()
        
        # Track advancement history for debugging
        self.advancement_history: List[Tuple[float, TimeAdvancementRequest, TimeAdvancementResult]] = []
        self.last_advancement_timestamp = time.time()
        
        # System synchronization tracking
        self.synchronized_systems = {
            'time_tracker': True,
            'simulation_tracker': True, 
            'reactor_time_manager': True
        }
        
        pass  # initialization complete
    
    def request_time_advancement(self, request: TimeAdvancementRequest) -> TimeAdvancementResult:
        """
        SINGLE POINT OF TIME ADVANCEMENT
        
        All systems must use this method to advance time.
        This prevents race conditions and ensures synchronization.
        """
        # Capture current state
        previous_time = self.time_tracker.get_current_time()
        previous_atmospheric = self.time_tracker.get_atmospheric_description()
        
        # Determine advancement duration
        if request.custom_duration_hours is not None:
            duration_hours = request.custom_duration_hours
        else:
            # Use Rule of 3's category for standard advancement
            duration_hours = self._get_duration_from_rule_of_3s(request.rule_of_3_category)
        
        duration_seconds = int(duration_hours * 3600)
        
        # CRITICAL: Advance all systems synchronously
        new_time, time_of_day_changed = self.time_tracker.advance_time(request.rule_of_3_category)
        self.simulation_tracker.add_action_time(
            action_description=f"{request.event_type.value}: {getattr(request, 'action_description', 'Unknown action')}",
            rule_of_3_category=request.rule_of_3_category,
            actor_name=getattr(request, 'actor_name', 'Unknown')
        )
        
        # Update reactor time manager if needed
        if request.event_type == TimeEventType.ENCOUNTER_TURN:
            self.reactor_time_manager.advance_reactor_time(duration_seconds)
        
        # Capture new atmospheric state
        new_atmospheric = self.time_tracker.get_atmospheric_description()
        atmospheric_changes = {
            'previous': previous_atmospheric,
            'new': new_atmospheric,
            'changed': previous_atmospheric != new_atmospheric
        }
        
        # Create result
        result = TimeAdvancementResult(
            previous_time=previous_time,
            new_time=new_time,
            time_of_day_changed=time_of_day_changed,
            duration_advanced_hours=duration_hours,
            duration_advanced_seconds=duration_seconds,
            affected_systems=['time_tracker', 'simulation_tracker', 'reactor_time_manager'],
            atmospheric_changes=atmospheric_changes
        )
        
        # Record advancement for debugging
        self.advancement_history.append((time.time(), request, result))
        self.last_advancement_timestamp = time.time()
        
        # Verify synchronization
        self._verify_system_synchronization()
        
        return result
    
    def _get_duration_from_rule_of_3s(self, category: RuleOf3Category) -> float:
        """Convert Rule of 3's category to hours"""
        duration_mapping = {
            RuleOf3Category.THREE_SECOND: 0.0167,  # 1 minute = 0.0167 hours (minimum time cost)
            RuleOf3Category.THREE_MINUTE: 0.05,    # 3 minutes = 0.05 hours
            RuleOf3Category.SLEEP: 2.0,            # 2 hours minimum (sleep exception)
        }
        return duration_mapping.get(category, 0.05)  # Default to 3 minutes
    
    def _verify_system_synchronization(self) -> bool:
        """Verify all time systems are synchronized"""
        try:
            # Check if simulation time roughly matches narrative time
            current_time = self.time_tracker.get_current_time()
            # Calculate hours since start (assuming Day 1, 9:00 AM is start time)
            narrative_hours = (current_time.day - 1) * 24 + current_time.hour + (current_time.minute / 60.0) - 9.0
            sim_hours = self.simulation_tracker.get_total_simulation_time() / 3600
            
            # Allow small discrepancy (within 1 minute)
            discrepancy = abs(narrative_hours - sim_hours)
            if discrepancy > 0.017:  # 0.017 hours = ~1 minute
                print(f"⚠️ Time synchronization warning: {discrepancy:.3f} hour discrepancy")
                return False
            
            return True
        except Exception as e:
            print(f"❌ Time synchronization check failed: {e}")
            return False
    
    def get_current_time_context(self) -> Dict[str, Any]:
        """Get comprehensive time context for all systems"""
        current_time = self.time_tracker.get_current_time()
        
        return {
            'game_time': current_time,
            'formatted_time': current_time.format_full(),
            'time_of_day': current_time.get_time_of_day(),
            'atmospheric_description': self.time_tracker.get_atmospheric_description(),
            'lighting_condition': self.time_tracker.get_lighting_condition(),
            'simulation_time_seconds': self.simulation_tracker.get_total_simulation_time(),
            'simulation_time_display': self.simulation_tracker.get_simulation_time_display(),
            'reactor_time_active': hasattr(self.reactor_time_manager, 'is_active') and self.reactor_time_manager.is_active,
            'systems_synchronized': self._verify_system_synchronization()
        }
    
    def create_survival_action_request(self, action_name: str, time_cost_hours: float, actor_name: str) -> TimeAdvancementRequest:
        """Helper to create survival action time requests"""
        return TimeAdvancementRequest(
            event_type=TimeEventType.SURVIVAL_ACTION,
            rule_of_3_category=RuleOf3Category.THREE_MINUTE,  # Survival actions in real-time
            requester_system="survival_system",
            actor_name=actor_name,
            description=f"{actor_name} performs {action_name}",
            custom_duration_hours=time_cost_hours
        )
    
    def create_user_action_request(self, rule_of_3_category: RuleOf3Category, actor_name: str, action_description: str) -> TimeAdvancementRequest:
        """Helper to create user action time requests"""
        return TimeAdvancementRequest(
            event_type=TimeEventType.USER_ACTION,
            rule_of_3_category=rule_of_3_category,
            requester_system="main_simulation",
            actor_name=actor_name,
            description=action_description
        )
    
    def create_recovery_request(self, actor_name: str, recovery_minutes: int) -> TimeAdvancementRequest:
        """Helper to create recovery process time requests"""
        return TimeAdvancementRequest(
            event_type=TimeEventType.RECOVERY_PROCESS,
            rule_of_3_category=RuleOf3Category.THREE_MINUTE,
            requester_system="recovery_system",
            actor_name=actor_name,
            description=f"{actor_name} recovery process",
            custom_duration_hours=recovery_minutes / 60.0
        )
    
    def get_advancement_history(self, last_n: int = 5) -> List[Tuple[str, str, str]]:
        """Get recent time advancement history for debugging"""
        recent = self.advancement_history[-last_n:] if self.advancement_history else []
        
        formatted_history = []
        for timestamp, request, result in recent:
            time_str = time.strftime("%H:%M:%S", time.localtime(timestamp))
            duration_str = f"+{result.duration_advanced_hours:.2f}h"
            description = f"{request.requester_system}: {request.description}"
            formatted_history.append((time_str, duration_str, description))
        
        return formatted_history
    
    def reset_systems(self, starting_hour: int = 9, starting_minute: int = 0, starting_day: int = 1):
        """Reset all time systems to synchronized state"""
        self.time_tracker = TimeCycleTracker(starting_hour, starting_minute, starting_day)
        self.simulation_tracker = SimulationTimeTracker()
        self.reactor_time_manager = ReactorTimeManager()
        self.advancement_history.clear()
        print("🔄 All time systems reset and synchronized")


# Global instance - SINGLE SOURCE OF TRUTH
_master_coordinator: Optional[MasterTimeCoordinator] = None

def get_master_time_coordinator() -> MasterTimeCoordinator:
    """Get the global master time coordinator instance"""
    global _master_coordinator
    if _master_coordinator is None:
        _master_coordinator = MasterTimeCoordinator()
    return _master_coordinator

def initialize_master_time_coordinator(starting_hour: int = 9, starting_minute: int = 0, starting_day: int = 1) -> MasterTimeCoordinator:
    """Initialize the global master time coordinator"""
    global _master_coordinator
    _master_coordinator = MasterTimeCoordinator(starting_hour, starting_minute, starting_day)
    return _master_coordinator
