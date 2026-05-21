#!/usr/bin/env python3
"""
Survival Needs System for UTAS

Tracks basic human needs: food, water, sleep, and fulfillment.
Implements time-based degradation and status penalties when needs are unmet.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import time

class SurvivalNeed(Enum):
    FOOD = "food"
    WATER = "water" 
    SLEEP = "sleep"
    FULFILLMENT = "fulfillment"

@dataclass
class SurvivalStatus:
    """Tracks a single survival need"""
    need_type: SurvivalNeed
    last_satisfied: float
    degradation_threshold: float
    degradation_rate: float
    status_penalty: int
    
    def __post_init__(self):
        if self.last_satisfied == 0:
            self.last_satisfied = time.time()
    
    def hours_since_satisfied(self) -> float:
        """Calculate hours since need was last satisfied"""
        return (time.time() - self.last_satisfied) / 3600.0
    
    def is_degrading(self) -> bool:
        """Check if this need is causing status degradation"""
        return self.hours_since_satisfied() > self.degradation_threshold
    
    def degradation_cycles(self) -> int:
        """Calculate how many degradation cycles have occurred"""
        if not self.is_degrading():
            return 0
        
        excess_hours = self.hours_since_satisfied() - self.degradation_threshold
        return int(excess_hours / self.degradation_rate)
    
    def satisfy_need(self):
        """Mark this need as satisfied"""
        self.last_satisfied = time.time()

class SurvivalManager:
    """Manages all survival needs for an actor"""
    
    def __init__(self):
        self.needs: Dict[SurvivalNeed, SurvivalStatus] = {
            SurvivalNeed.FOOD: SurvivalStatus(
                need_type=SurvivalNeed.FOOD,
                last_satisfied=time.time(),
                degradation_threshold=72.0,
                degradation_rate=3.0,
                status_penalty=1
            ),
            SurvivalNeed.WATER: SurvivalStatus(
                need_type=SurvivalNeed.WATER,
                last_satisfied=time.time(),
                degradation_threshold=24.0,
                degradation_rate=3.0,
                status_penalty=1
            ),
            SurvivalNeed.SLEEP: SurvivalStatus(
                need_type=SurvivalNeed.SLEEP,
                last_satisfied=time.time(),
                degradation_threshold=24.0,
                degradation_rate=3.0,
                status_penalty=1
            ),
            SurvivalNeed.FULFILLMENT: SurvivalStatus(
                need_type=SurvivalNeed.FULFILLMENT,
                last_satisfied=time.time(),
                degradation_threshold=168.0,
                degradation_rate=24.0,
                status_penalty=1
            )
        }
        
        self.last_degradation_check = time.time()
    
    def satisfy_need(self, need: SurvivalNeed):
        """Satisfy a specific survival need"""
        if need in self.needs:
            self.needs[need].satisfy_need()
    
    def get_unmet_needs(self) -> List[SurvivalNeed]:
        """Get list of needs that are currently causing degradation"""
        return [need for need, status in self.needs.items() if status.is_degrading()]
    
    def has_unmet_needs(self) -> bool:
        """Check if any survival needs are unmet"""
        return len(self.get_unmet_needs()) > 0
    
    def calculate_survival_penalties(self) -> Dict[str, int]:
        """Calculate total status penalties from unmet survival needs"""
        penalties = {"stamina": 0, "spirit": 0}
        
        for need, status in self.needs.items():
            if status.is_degrading():
                cycles = status.degradation_cycles()
                if cycles > 0:
                    # Most survival needs affect stamina, fulfillment affects spirit
                    if need == SurvivalNeed.FULFILLMENT:
                        penalties["spirit"] += cycles * status.status_penalty
                    else:
                        penalties["stamina"] += cycles * status.status_penalty
        
        return penalties
    
    def should_disable_temporary_bonuses(self) -> bool:
        """Check if temporary status bonuses should be disabled"""
        basic_needs = [SurvivalNeed.FOOD, SurvivalNeed.WATER, SurvivalNeed.SLEEP]
        return any(self.needs[need].is_degrading() for need in basic_needs)
    
    def get_survival_summary(self) -> Dict[str, str]:
        """Get human-readable summary of survival status"""
        summary = {}
        
        for need, status in self.needs.items():
            hours = status.hours_since_satisfied()
            
            if hours < status.degradation_threshold:
                remaining = status.degradation_threshold - hours
                summary[need.value] = f"Satisfied ({remaining:.1f}h remaining)"
            else:
                cycles = status.degradation_cycles()
                summary[need.value] = f"CRITICAL (-{cycles} status penalty)"
        
        return summary
    
    def perform_sleep_healing(self, actor_sheet) -> List[str]:
        """
        Perform sleep healing - remove all temporary status shifts
        Returns list of healing messages
        """
        from actor_sheet import StatusType
        
        healing_messages = []
        
        self.satisfy_need(SurvivalNeed.SLEEP)
        
        for status_type in [StatusType.STAMINA, StatusType.SPIRIT]:
            status = actor_sheet.statuses[status_type]
            
            temp_shifts = status.value - status.max_value
            
            if temp_shifts < 0:
                status.value = status.max_value
                healing_messages.append(f"Sleep restored {abs(temp_shifts)} {status_type.value} (temporary penalties removed)")
        
        return healing_messages
    
    def to_dict(self) -> dict:
        """Serialize survival manager to dictionary"""
        return {
            "needs": {
                need.value: {
                    "last_satisfied": status.last_satisfied,
                    "degradation_threshold": status.degradation_threshold,
                    "degradation_rate": status.degradation_rate,
                    "status_penalty": status.status_penalty
                }
                for need, status in self.needs.items()
            },
            "last_degradation_check": self.last_degradation_check
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SurvivalManager':
        """Deserialize survival manager from dictionary"""
        manager = cls()
        
        if "needs" in data:
            for need_name, need_data in data["needs"].items():
                need = SurvivalNeed(need_name)
                if need in manager.needs:
                    manager.needs[need].last_satisfied = need_data.get("last_satisfied", time.time())
        
        manager.last_degradation_check = data.get("last_degradation_check", time.time())
        return manager
