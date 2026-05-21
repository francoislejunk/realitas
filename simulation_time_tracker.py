"""
Simulation Time Tracker for UTAS

Tracks simulation time across all actions and manages automatic SPARK generation
based on turn count in ROAM mode (10 turns minimum, 10% chance per turn).
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time
import random
from rule_of_3s import RuleOf3Category

@dataclass
class TimeAction:
    """Represents an action with its time cost"""
    action_description: str
    rule_of_3_category: RuleOf3Category
    time_cost_seconds: float
    timestamp: float
    actor_name: str

class SimulationTimeTracker:
    """Tracks simulation time and manages SPARK generation timing"""
    
    def __init__(self, starting_simulation_time: float = 0.0):
        self.simulation_time = starting_simulation_time  # Total elapsed simulation time in seconds
        self.action_history: List[TimeAction] = []
        
        # Turn-based SPARK system
        self.turns_since_spark = 0  # Turns since last SPARK
        self.spark_min_turns = 10  # Minimum turns before SPARK can occur
        self.spark_chance_per_turn = 0.10  # 10% chance per turn after threshold
        
        # Rule of 3 time mappings (in seconds)
        self.rule_of_3_times = {
            RuleOf3Category.THREE_SECOND: 3.0,
            RuleOf3Category.THREE_MINUTE: 180.0,  # 3 minutes
            RuleOf3Category.SLEEP: 7200.0,  # 2 hours minimum (sleep exception)
        }
    
    def add_action_time(self, action_description: str, rule_of_3_category: RuleOf3Category, 
                       actor_name: str = "Unknown") -> float:
        """
        Add time for an action and return the new simulation time
        
        Args:
            action_description: Description of the action taken
            rule_of_3_category: Rule of 3 category for time calculation
            actor_name: Name of the actor performing the action
            
        Returns:
            New total simulation time in seconds
        """
        time_cost = self.rule_of_3_times[rule_of_3_category]
        
        # Create action record
        action = TimeAction(
            action_description=action_description,
            rule_of_3_category=rule_of_3_category,
            time_cost_seconds=time_cost,
            timestamp=self.simulation_time,
            actor_name=actor_name
        )
        
        self.action_history.append(action)
        self.simulation_time += time_cost
        self.turns_since_spark += 1  # Increment turn counter
        
        return self.simulation_time
    
    def should_generate_spark(self, current_mode: str) -> bool:
        """
        Check if a SPARK should be generated based on turn count.
        
        NEW SYSTEM: After 10 turns in ROAM, 10% chance per turn.
        
        Args:
            current_mode: Current simulation mode ("roam" or "encounter")
            
        Returns:
            True if a SPARK should be generated
        """
        if current_mode.lower() != "roam":
            return False
        
        # Must be at least 10 turns since last SPARK
        if self.turns_since_spark < self.spark_min_turns:
            return False
        
        # 10% chance per turn after threshold
        roll = random.random()
        return roll < self.spark_chance_per_turn
    
    def mark_spark_generated(self):
        """Mark that a SPARK has been generated"""
        self.turns_since_spark = 0  # Reset turn counter
    
    def get_simulation_time_display(self) -> str:
        """Get human-readable simulation time"""
        total_seconds = int(self.simulation_time)
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
    
    def get_recent_actions(self, count: int = 5) -> List[TimeAction]:
        """Get the most recent actions"""
        return self.action_history[-count:] if self.action_history else []
    
    def get_total_simulation_time(self) -> float:
        """Get total simulation time in seconds"""
        return self.simulation_time
    
    def get_time_breakdown(self) -> Dict[RuleOf3Category, float]:
        """Get breakdown of time spent in each Rule of 3 category"""
        breakdown = {
            RuleOf3Category.THREE_SECOND: 0.0,
            RuleOf3Category.THREE_MINUTE: 0.0,
            RuleOf3Category.SLEEP: 0.0
        }
        
        for action in self.action_history:
            breakdown[action.rule_of_3_category] += action.time_cost_seconds
        
        return breakdown
    
    def reset_spark_timer(self):
        """Reset the SPARK turn counter (useful when entering encounter mode)"""
        self.turns_since_spark = 0
    
    def get_turns_since_spark(self) -> int:
        """Get number of turns since last SPARK"""
        return self.turns_since_spark
    
    def get_action_count_by_category(self) -> Dict[RuleOf3Category, int]:
        """Get count of actions by Rule of 3 category"""
        counts = {
            RuleOf3Category.THREE_SECOND: 0,
            RuleOf3Category.THREE_MINUTE: 0,
            RuleOf3Category.SLEEP: 0
        }
        
        for action in self.action_history:
            counts[action.rule_of_3_category] += 1
        
        return counts
    
    def get_time_summary(self) -> str:
        """Get a summary of simulation time and activity"""
        breakdown = self.get_time_breakdown()
        counts = self.get_action_count_by_category()
        
        # SPARK status
        if self.turns_since_spark < self.spark_min_turns:
            spark_status = f"{self.spark_min_turns - self.turns_since_spark} turns until eligible"
        else:
            spark_status = f"Eligible (10% chance per turn)"
        
        summary_lines = [
            f"Total Simulation Time: {self.get_simulation_time_display()}",
            f"Actions Taken: {len(self.action_history)}",
            "",
            "Time Breakdown:",
            f"  3-Second Actions: {counts[RuleOf3Category.THREE_SECOND]} ({int(breakdown[RuleOf3Category.THREE_SECOND])}s)",
            f"  3-Minute Actions: {counts[RuleOf3Category.THREE_MINUTE]} ({int(breakdown[RuleOf3Category.THREE_MINUTE])}s)",
            f"  Sleep Actions: {counts[RuleOf3Category.SLEEP]} ({int(breakdown[RuleOf3Category.SLEEP])}s)",
            "",
            f"Turns Since Last SPARK: {self.turns_since_spark}",
            f"SPARK Status: {spark_status}"
        ]
        
        return "\n".join(summary_lines)
