"""
Actor State Filter for UTAS Simulation

Prevents dead or unconscious actors from taking actions.
Ensures proper state management and turn queue filtering.
"""

from typing import List, Optional, Dict, Any
from actor_sheet import StatusType
from color_utils import Color


class ActorStateFilter:
    """
    Filters and validates actor states to prevent fake signals.
    
    Tracks:
    - Dead actors (cannot act, removed from turn queue)
    - Unconscious actors (cannot act, skip turns)
    - Incapacitated actors (severely limited actions)
    """
    
    def __init__(self):
        self.dead_actors = set()
        self.unconscious_actors = set()
        self.incapacitated_actors = set()
        self.death_events = []
    
    def check_actor_state(self, actor) -> str:
        """
        Check current state of an actor.
        
        Returns:
            'dead', 'unconscious', 'incapacitated', or 'active'
        """
        actor_name = actor.sheet.name
        
        # Check if already marked as dead
        if actor_name in self.dead_actors:
            return 'dead'
        
        # Check if already marked as unconscious
        if actor_name in self.unconscious_actors:
            return 'unconscious'
        
        # Check status values for death conditions
        try:
            stamina = actor.sheet.statuses[StatusType.STAMINA]
            spirit = actor.sheet.statuses[StatusType.SPIRIT]
            supply = actor.sheet.statuses[StatusType.SUPPLY]
            
            # Death condition: Any status max capacity reaches 0 (from lasting shifts)
            if hasattr(stamina, 'max_value') and stamina.max_value <= 0:
                self.mark_actor_dead(actor, "stamina exhaustion")
                return 'dead'
            
            if hasattr(spirit, 'max_value') and spirit.max_value <= 0:
                self.mark_actor_dead(actor, "spirit broken")
                return 'dead'
            
            if hasattr(supply, 'max_value') and supply.max_value <= 0:
                self.mark_actor_dead(actor, "resource depletion")
                return 'dead'
            
            # Unconscious condition: Stamina or Spirit at 0
            if stamina.value <= 0 or spirit.value <= 0:
                if actor_name not in self.unconscious_actors:
                    self.mark_actor_unconscious(actor)
                return 'unconscious'
            
            # Incapacitated condition: Multiple statuses critically low
            critical_count = sum([
                1 for status in [stamina, spirit, supply]
                if status.value <= 1
            ])
            
            if critical_count >= 2:
                if actor_name not in self.incapacitated_actors:
                    self.incapacitated_actors.add(actor_name)
                return 'incapacitated'
            
            # Remove from incapacitated if recovered
            if actor_name in self.incapacitated_actors and critical_count < 2:
                self.incapacitated_actors.remove(actor_name)
            
            # Check for recovery from unconsciousness
            if actor_name in self.unconscious_actors:
                if stamina.value > 0 and spirit.value > 0:
                    self.mark_actor_conscious(actor)
                    return 'active'
                else:
                    return 'unconscious'
            
            return 'active'
            
        except Exception as e:
            print(f"{Color.ERROR}Error checking actor state: {e}{Color.RESET}")
            return 'active'  # Default to active on error
    
    def mark_actor_dead(self, actor, cause: str = "unknown"):
        """Mark an actor as dead and record the event."""
        actor_name = actor.sheet.name
        
        if actor_name not in self.dead_actors:
            self.dead_actors.add(actor_name)
            
            # Remove from other states
            self.unconscious_actors.discard(actor_name)
            self.incapacitated_actors.discard(actor_name)
            
            # Record death event
            death_event = {
                'actor': actor_name,
                'cause': cause,
                'turn': len(self.death_events) + 1
            }
            self.death_events.append(death_event)
            
            print(f"\n{Color.ERROR}{'='*80}{Color.RESET}")
            print(f"{Color.ERROR}💀 DEATH{Color.RESET}")
            print(f"{Color.ERROR}{'='*80}{Color.RESET}")
            print(f"{Color.ERROR}{actor_name} has died from {cause}!{Color.RESET}")
            print(f"{Color.ERROR}They are removed from the turn queue and cannot act.{Color.RESET}")
            print(f"{Color.ERROR}{'='*80}{Color.RESET}\n")
    
    def mark_actor_unconscious(self, actor):
        """Mark an actor as unconscious."""
        actor_name = actor.sheet.name
        
        if actor_name not in self.unconscious_actors:
            self.unconscious_actors.add(actor_name)
            
            print(f"\n{Color.WARNING}{'='*80}{Color.RESET}")
            print(f"{Color.WARNING}😵 UNCONSCIOUS{Color.RESET}")
            print(f"{Color.WARNING}{'='*80}{Color.RESET}")
            print(f"{Color.WARNING}{actor_name} has fallen unconscious!{Color.RESET}")
            print(f"{Color.WARNING}They cannot act until they recover.{Color.RESET}")
            print(f"{Color.WARNING}{'='*80}{Color.RESET}\n")
    
    def mark_actor_conscious(self, actor):
        """Mark an actor as regaining consciousness."""
        actor_name = actor.sheet.name
        
        if actor_name in self.unconscious_actors:
            self.unconscious_actors.remove(actor_name)
            
            print(f"\n{Color.SUCCESS}{'='*80}{Color.RESET}")
            print(f"{Color.SUCCESS}✓ CONSCIOUSNESS REGAINED{Color.RESET}")
            print(f"{Color.SUCCESS}{'='*80}{Color.RESET}")
            print(f"{Color.SUCCESS}{actor_name} regains consciousness!{Color.RESET}")
            print(f"{Color.SUCCESS}They can now act again.{Color.RESET}")
            print(f"{Color.SUCCESS}{'='*80}{Color.RESET}\n")
    
    def can_actor_take_action(self, actor) -> bool:
        """Check if an actor can take an action."""
        state = self.check_actor_state(actor)
        return state == 'active' or state == 'incapacitated'
    
    def can_actor_take_full_action(self, actor) -> bool:
        """Check if an actor can take a full action (not incapacitated)."""
        state = self.check_actor_state(actor)
        return state == 'active'
    
    def filter_turn_queue(self, turn_queue: List) -> List:
        """
        Filter turn queue to remove dead actors and mark unconscious actors.
        
        Args:
            turn_queue: List of turn data dicts with 'actor' key
            
        Returns:
            Filtered turn queue
        """
        filtered_queue = []
        
        for turn_data in turn_queue:
            actor = turn_data.get('actor')
            if not actor:
                continue
            
            state = self.check_actor_state(actor)
            
            if state == 'dead':
                # Skip dead actors entirely
                print(f"{Color.ERROR}⏭️  Skipping {actor.sheet.name}'s turn (dead){Color.RESET}")
                continue
            elif state == 'unconscious':
                # Mark but keep in queue for potential recovery
                turn_data['state'] = 'unconscious'
                turn_data['can_act'] = False
                filtered_queue.append(turn_data)
            elif state == 'incapacitated':
                # Mark as limited
                turn_data['state'] = 'incapacitated'
                turn_data['can_act'] = True
                turn_data['limited'] = True
                filtered_queue.append(turn_data)
            else:
                # Active actor
                turn_data['state'] = 'active'
                turn_data['can_act'] = True
                filtered_queue.append(turn_data)
        
        return filtered_queue
    
    def get_available_actions_for_state(self, state: str) -> List[str]:
        """Get list of available actions based on actor state."""
        if state == 'dead':
            return []
        elif state == 'unconscious':
            return []
        elif state == 'incapacitated':
            return [
                'crawl',
                'call_for_help',
                'surrender',
                'use_item',
                'speak'
            ]
        else:  # active
            return [
                'attack',
                'defend',
                'move',
                'use_item',
                'speak',
                'help_ally',
                'flee',
                'any_action'
            ]
    
    def display_actor_state_warning(self, actor, attempted_action: str):
        """Display warning when actor in wrong state attempts action."""
        state = self.check_actor_state(actor)
        actor_name = actor.sheet.name
        
        if state == 'dead':
            print(f"\n{Color.ERROR}❌ INVALID ACTION{Color.RESET}")
            print(f"{Color.ERROR}{actor_name} is dead and cannot {attempted_action}!{Color.RESET}\n")
        elif state == 'unconscious':
            print(f"\n{Color.WARNING}❌ INVALID ACTION{Color.RESET}")
            print(f"{Color.WARNING}{actor_name} is unconscious and cannot {attempted_action}!{Color.RESET}\n")
        elif state == 'incapacitated':
            print(f"\n{Color.WARNING}⚠️  LIMITED ACTIONS{Color.RESET}")
            print(f"{Color.WARNING}{actor_name} is incapacitated and has limited options.{Color.RESET}")
            available = self.get_available_actions_for_state(state)
            print(f"{Color.INFO}Available: {', '.join(available)}{Color.RESET}\n")
    
    def get_state_narrative_context(self, actor) -> str:
        """Get narrative context about actor's current state."""
        state = self.check_actor_state(actor)
        actor_name = actor.sheet.name
        
        if state == 'dead':
            return f"{actor_name} lies motionless, their life extinguished."
        elif state == 'unconscious':
            return f"{actor_name} is unconscious and unresponsive."
        elif state == 'incapacitated':
            return f"{actor_name} is severely wounded and barely able to move."
        else:
            return ""
    
    def check_for_death_triggers(self, actor) -> bool:
        """
        Check if actor should die based on current conditions.
        
        Returns:
            True if actor died, False otherwise
        """
        try:
            stamina = actor.sheet.statuses[StatusType.STAMINA]
            spirit = actor.sheet.statuses[StatusType.SPIRIT]
            supply = actor.sheet.statuses[StatusType.SUPPLY]
            
            # Check for death from lasting shifts
            if hasattr(stamina, 'max_value') and stamina.max_value <= 0:
                self.mark_actor_dead(actor, "stamina capacity exhausted")
                return True
            
            if hasattr(spirit, 'max_value') and spirit.max_value <= 0:
                self.mark_actor_dead(actor, "spirit capacity exhausted")
                return True
            
            if hasattr(supply, 'max_value') and supply.max_value <= 0:
                self.mark_actor_dead(actor, "supply capacity exhausted")
                return True
            
            # Check for death from extreme negative values
            if stamina.value <= -5:
                self.mark_actor_dead(actor, "catastrophic stamina loss")
                return True
            
            if spirit.value <= -5:
                self.mark_actor_dead(actor, "catastrophic spirit loss")
                return True
            
            return False
            
        except Exception as e:
            print(f"{Color.ERROR}Error checking death triggers: {e}{Color.RESET}")
            return False
    
    def get_death_summary(self) -> str:
        """Get summary of all deaths that occurred."""
        if not self.death_events:
            return "No deaths have occurred."
        
        summary = f"Deaths: {len(self.death_events)}\n"
        for event in self.death_events:
            summary += f"  - {event['actor']} (Turn {event['turn']}, {event['cause']})\n"
        
        return summary


# Global instance
actor_state_filter = ActorStateFilter()
