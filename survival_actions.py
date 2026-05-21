#!/usr/bin/env python3
"""
Survival Actions for UTAS

Defines actions that characters can take to satisfy survival needs.
"""

from survival_system import SurvivalNeed
from typing import List, Dict, Any

class SurvivalAction:
    """Base class for survival-related actions"""
    
    def __init__(self, name: str, description: str, needs_satisfied: List[SurvivalNeed], 
                 time_cost: float = 1.0, supply_cost: int = 0):
        self.name = name
        self.description = description
        self.needs_satisfied = needs_satisfied
        self.time_cost = time_cost
        self.supply_cost = supply_cost
    
    def can_perform(self, actor_sheet) -> bool:
        """Check if actor can perform this action"""
        if self.supply_cost > 0:
            supply_status = actor_sheet.statuses.get("SUPPLY")
            if supply_status and supply_status.money_amount < self.supply_cost:
                return False
        return True
    
    def perform(self, actor_sheet) -> List[str]:
        """Perform the survival action"""
        messages = []
        
        if self.supply_cost > 0:
            supply_status = actor_sheet.statuses.get("SUPPLY")
            if supply_status:
                supply_status.modify(-self.supply_cost)
                messages.append(f"Spent ${self.supply_cost} on {self.name}")
        
        for need in self.needs_satisfied:
            actor_sheet.survival.satisfy_need(need)
            messages.append(f"{need.value.capitalize()} need satisfied")
        
        if SurvivalNeed.SLEEP in self.needs_satisfied:
            healing_messages = actor_sheet.survival.perform_sleep_healing(actor_sheet)
            messages.extend(healing_messages)
        
        return messages

SURVIVAL_ACTIONS = {
    "eat_meal": SurvivalAction(
        name="Eat a Meal",
        description="Consume food to satisfy hunger",
        needs_satisfied=[SurvivalNeed.FOOD],
        time_cost=0.5,
        supply_cost=10
    ),
    
    "drink_water": SurvivalAction(
        name="Drink Water",
        description="Drink water to stay hydrated",
        needs_satisfied=[SurvivalNeed.WATER],
        time_cost=0.1,
        supply_cost=2
    ),
    
    "sleep": SurvivalAction(
        name="Sleep",
        description="Get rest and heal temporary injuries",
        needs_satisfied=[SurvivalNeed.SLEEP],
        time_cost=8.0,
        supply_cost=0
    ),
    
    "rest_at_inn": SurvivalAction(
        name="Rest at Inn",
        description="Sleep comfortably at an inn with meals included",
        needs_satisfied=[SurvivalNeed.SLEEP, SurvivalNeed.FOOD, SurvivalNeed.WATER],
        time_cost=8.0,
        supply_cost=50
    ),
    
    "pursue_hobby": SurvivalAction(
        name="Pursue Hobby",
        description="Engage in fulfilling activities",
        needs_satisfied=[SurvivalNeed.FULFILLMENT],
        time_cost=2.0,
        supply_cost=20
    ),
    
    "socialize": SurvivalAction(
        name="Socialize",
        description="Spend time with others for fulfillment",
        needs_satisfied=[SurvivalNeed.FULFILLMENT],
        time_cost=1.0,
        supply_cost=15
    )
}

def get_available_survival_actions(actor_sheet) -> Dict[str, SurvivalAction]:
    """Get survival actions that the actor can currently perform"""
    available = {}
    
    for action_id, action in SURVIVAL_ACTIONS.items():
        if action.can_perform(actor_sheet):
            available[action_id] = action
    
    return available

def get_critical_survival_actions(actor_sheet) -> Dict[str, SurvivalAction]:
    """Get survival actions for currently unmet needs"""
    critical = {}
    unmet_needs = actor_sheet.survival.get_unmet_needs()
    
    for action_id, action in SURVIVAL_ACTIONS.items():
        if any(need in action.needs_satisfied for need in unmet_needs):
            if action.can_perform(actor_sheet):
                critical[action_id] = action
    
    return critical
