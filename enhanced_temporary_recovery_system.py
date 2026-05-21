"""
Enhanced Temporary Status Recovery System for UTAS Simulation

This module handles the new comprehensive temporary/lasting status shift system:
1. Enhanced temporary recovery: +1 to lowest affected status each turn
2. Temporary-to-lasting conversion when status goes below 0
3. Lasting shifts affect both current value and max capacity
4. Death condition when max capacity reaches 0
"""

from typing import Dict, Any, List, Optional, Tuple
import random
from dataclasses import dataclass
from enum import Enum
from actor_sheet import StatusType, Status
from actors import Actor


@dataclass
class EnhancedTemporaryStatusEffect:
    """Tracks a temporary status effect with enhanced conversion capabilities"""
    actor_name: str
    status_type: StatusType
    original_value: int
    current_value: int
    temporary_shift_amount: int
    rounds_since_applied: int
    source_description: str
    application_order: int
    
    def can_recover(self) -> bool:
        """Check if this effect can still recover (has temporary shift remaining)"""
        return self.temporary_shift_amount < 0
    
    def get_recovery_amount(self) -> int:
        """Calculate how much this effect should recover this round"""
        if not self.can_recover():
            return 0
        
        return min(1, abs(self.temporary_shift_amount))
    
    def apply_recovery(self, recovery_amount: int):
        """Apply recovery to this temporary effect"""
        if recovery_amount > 0 and self.temporary_shift_amount < 0:
            self.temporary_shift_amount += recovery_amount
            self.current_value += recovery_amount
            self.rounds_since_applied += 1


class EnhancedTemporaryRecoveryManager:
    """Manages enhanced temporary status effects with lasting conversion"""
    
    def __init__(self):
        self.active_effects: Dict[str, List[EnhancedTemporaryStatusEffect]] = {}
        self.lasting_shifts: Dict[str, Dict[StatusType, int]] = {}
        self._effect_counter: int = 0
    
    def add_temporary_effect(self, actor_name: str, status_type: StatusType, original_value: int, new_value: int, source_description: str):
        """
        Add a temporary status effect with enhanced conversion logic
        
        Args:
            actor_name: Name of the actor affected
            status_type: Type of status affected
            original_value: Original status value before the shift
            new_value: New status value after the shift (may be clamped)
            source_description: Description of what caused this effect
        """
        if actor_name not in self.active_effects:
            self.active_effects[actor_name] = []
        
        shift_amount = new_value - original_value
        
        # Debug: Print when adding temporary effects
        print(f"DEBUG: Adding temporary effect for {actor_name}")
        print(f"  Status: {status_type.name}, Original: {original_value}, New: {new_value}, Shift: {shift_amount}")
        print(f"  Source: {source_description}")
        
        if actor_name not in self.lasting_shifts:
            self.lasting_shifts[actor_name] = {}
        
        shift_amount = new_value - original_value
        
        if new_value < 0:
            temporary_portion = -original_value
            lasting_portion = abs(new_value)
            
            if status_type not in self.lasting_shifts[actor_name]:
                self.lasting_shifts[actor_name][status_type] = 0
            self.lasting_shifts[actor_name][status_type] -= lasting_portion
            
            self._effect_counter += 1
            effect = EnhancedTemporaryStatusEffect(
                actor_name=actor_name,
                status_type=status_type,
                original_value=original_value,
                current_value=0,
                temporary_shift_amount=temporary_portion,
                rounds_since_applied=0,
                source_description=f"{source_description} (converted: {lasting_portion} lasting, {abs(temporary_portion)} temporary)",
                application_order=self._effect_counter
            )
            
            print(f"      * System: Temporary-to-lasting conversion for {actor_name}'s {status_type.name}")
            print(f"        - Temporary portion: {temporary_portion}")
            print(f"        - Lasting portion: -{lasting_portion}")
            
        else:
            self._effect_counter += 1
            effect = EnhancedTemporaryStatusEffect(
                actor_name=actor_name,
                status_type=status_type,
                original_value=original_value,
                current_value=new_value,
                temporary_shift_amount=shift_amount,
                rounds_since_applied=0,
                source_description=source_description,
                application_order=self._effect_counter
            )
        
        self.active_effects[actor_name].append(effect)
    
    def process_turn_start_recovery(self, actors: List[Actor]) -> List[Dict[str, Any]]:
        """
        Process enhanced recovery at the start of each turn
        
        Args:
            actors: List of all actors in the scene
            
        Returns:
            List of recovery events that occurred
        """
        recovery_events = []
        
        # Debug: Print current active effects
        print(f"DEBUG: Processing recovery for {len(actors)} actors")
        for actor_name, effects in self.active_effects.items():
            print(f"DEBUG: {actor_name} has {len(effects)} active effects")
            for i, effect in enumerate(effects):
                print(f"  Effect {i}: {effect.status_type.name} from {effect.original_value} to {effect.current_value}")
        
        for actor in actors:
            if actor.sheet.name not in self.active_effects:
                print(f"DEBUG: No active effects for {actor.sheet.name}")
                continue
            
            # Check if NUA is in knockout duration - prevent recovery during knockout
            if not actor.is_user_actor and actor.sheet.get_knockout_turns_remaining() > 0:
                print(f"DEBUG: {actor.sheet.name} is in knockout duration - skipping recovery")
                continue
            
            eligible_effects = [
                effect for effect in self.active_effects[actor.sheet.name]
                if effect.can_recover()
            ]
            
            if not eligible_effects:
                continue
            
            status_candidates = {}
            for effect in eligible_effects:
                if effect.status_type == StatusType.SYMPATHY:
                    current_status_value = 1
                else:
                    current_status_value = actor.sheet.statuses[effect.status_type].value
                if effect.status_type not in status_candidates:
                    status_candidates[effect.status_type] = {
                        'value': current_status_value,
                        'earliest_effect': effect
                    }
                elif current_status_value < status_candidates[effect.status_type]['value']:
                    status_candidates[effect.status_type] = {
                        'value': current_status_value,
                        'earliest_effect': effect
                    }
                elif current_status_value == status_candidates[effect.status_type]['value']:
                    if effect.application_order < status_candidates[effect.status_type]['earliest_effect'].application_order:
                        status_candidates[effect.status_type]['earliest_effect'] = effect
            
            if status_candidates:
                lowest_status_type = min(
                    status_candidates.keys(),
                    key=lambda st: (
                        status_candidates[st]['value'],
                        status_candidates[st]['earliest_effect'].application_order
                    )
                )
                lowest_value = status_candidates[lowest_status_type]['value']
                earliest_effect = status_candidates[lowest_status_type]['earliest_effect']
                
                if lowest_status_type == StatusType.SYMPATHY:
                    print(f"      * Sympathy recovery not yet implemented for {actor.sheet.name}")
                    continue
                else:
                    actor.sheet.update_status(lowest_status_type, 1, "Temporary Recovery")
                
                earliest_effect.apply_recovery(1)
                
                if lowest_status_type == StatusType.SYMPATHY:
                    new_value = 1
                else:
                    new_value = actor.sheet.statuses[lowest_status_type].value
                
                recovery_events.append({
                    'actor_name': actor.sheet.name,
                    'status_name': lowest_status_type.name,
                    'status_type': lowest_status_type.name,
                    'old_value': lowest_value,
                    'new_value': new_value,
                    'recovery_amount': 1,
                    'source_description': f"Temporary recovery at initiative roll",
                    'fully_recovered': earliest_effect.is_fully_recovered() if hasattr(earliest_effect, 'is_fully_recovered') else False,
                    'description': f"Recovered +1 {lowest_status_type.name} (was lowest at {lowest_value})"
                })
            
            self.active_effects[actor.sheet.name] = [
                effect for effect in self.active_effects[actor.sheet.name]
                if effect.can_recover()
            ]
        
        return recovery_events
    
    def apply_lasting_shifts_to_actors(self, actors: List[Actor]):
        """Apply all accumulated lasting shifts to actors"""
        for actor in actors:
            actor_name = actor.sheet.name
            if actor_name in self.lasting_shifts:
                for status_type, lasting_amount in self.lasting_shifts[actor_name].items():
                    if lasting_amount != 0:
                        actor.sheet.apply_lasting_status_shift(status_type, lasting_amount)
                
                self.lasting_shifts[actor_name] = {}
    
    def get_recovery_status_for_actor(self, actor_name: str) -> Dict[str, Any]:
        """
        Get enhanced recovery status information for an actor
        
        Args:
            actor_name: Name of the actor
            
        Returns:
            Dictionary with recovery status information
        """
        if actor_name not in self.active_effects:
            return {
                'actor_name': actor_name,
                'active_temporary_effects': 0,
                'effects': [],
                'lasting_shifts': {}
            }
        
        effects_info = []
        for effect in self.active_effects[actor_name]:
            effects_info.append({
                'status_type': effect.status_type.name,
                'current_value': effect.current_value,
                'temporary_shift_remaining': effect.temporary_shift_amount,
                'rounds_active': effect.rounds_since_applied,
                'source': effect.source_description,
                'can_recover': effect.can_recover()
            })
        
        lasting_info = {}
        if actor_name in self.lasting_shifts:
            lasting_info = {
                status_type.name: amount 
                for status_type, amount in self.lasting_shifts[actor_name].items()
                if amount != 0
            }
        
        return {
            'actor_name': actor_name,
            'active_temporary_effects': len(self.active_effects[actor_name]),
            'effects': effects_info,
            'lasting_shifts': lasting_info
        }


class EnhancedTemporaryRecoveryIntegrator:
    """Integrates the enhanced temporary recovery system with existing UTAS components"""
    
    def __init__(self):
        self.recovery_manager = EnhancedTemporaryRecoveryManager()
    
    def track_exchange_effects(self, exchange_results: Dict[str, Any], proactor_name: str, reactor_name: str):
        """
        Track temporary effects from an exchange with enhanced conversion logic
        
        Args:
            exchange_results: Results from an exchange
            proactor_name: Name of the proactor
            reactor_name: Name of the reactor
        """
        if exchange_results.get('winner') == 'proactor':
            shift_type = exchange_results.get('shift_type')
            if shift_type == 'Temporary':
                original_reactor_status = exchange_results.get('original_reactor_status', 0)
                updated_reactor_status = exchange_results.get('updated_reactor_status', 0)
                status_shifted = exchange_results.get('status_shifted', 'SPIRIT')
                
                try:
                    status_type = StatusType[status_shifted.upper()]
                    self.recovery_manager.add_temporary_effect(
                        actor_name=reactor_name,
                        status_type=status_type,
                        original_value=original_reactor_status,
                        new_value=updated_reactor_status,
                        source_description=f"Temporary effect from {proactor_name}'s action"
                    )
                except KeyError:
                    print(f"Warning: Unknown status type '{status_shifted}' in exchange results")
        
        elif exchange_results.get('winner') == 'reactor':
            shift_type = exchange_results.get('shift_type')
            if shift_type == 'Temporary':
                original_proactor_status = exchange_results.get('original_proactor_status', 0)
                updated_proactor_status = exchange_results.get('updated_proactor_status', 0)
                status_shifted = exchange_results.get('status_shifted', 'SPIRIT')
                
                try:
                    status_type = StatusType[status_shifted.upper()]
                    self.recovery_manager.add_temporary_effect(
                        actor_name=proactor_name,
                        status_type=status_type,
                        original_value=original_proactor_status,
                        new_value=updated_proactor_status,
                        source_description=f"Temporary effect from {reactor_name}'s counter-action"
                    )
                except KeyError:
                    print(f"Warning: Unknown status type '{status_shifted}' in exchange results")
        
        applied_effects = exchange_results.get('applied_effects', [])
        for effect in applied_effects:
            if effect.get('shift_type') == 'Temporary':
                status_name = effect.get('status_shifted')
                if status_name:
                    try:
                        status_type = StatusType[status_name.upper()]
                        original_value = effect.get('original_value', 3)
                        new_value = effect.get('new_value', original_value + effect.get('shift_magnitude', 0))
                        
                        self.recovery_manager.add_temporary_effect(
                            actor_name=proactor_name,
                            status_type=status_type,
                            original_value=original_value,
                            new_value=new_value,
                            source_description=f"Self-inflicted temporary effect"
                        )
                    except KeyError:
                        print(f"Warning: Unknown status type '{status_name}' in self-effect")
    
    def apply_recovery_to_actors(self, actors: List[Actor]) -> List[Dict[str, Any]]:
        """Apply enhanced recovery to all actors (called by round manager)
        
        Args:
            actors: List of all actors in the scene
            
        Returns:
            List of recovery events that occurred
        """
        self.recovery_manager.apply_lasting_shifts_to_actors(actors)
        
        # Knockout handling: guarantee miss 1 turn, then 20% chance per turn to regain consciousness
        actors_for_recovery: List[Actor] = []
        ko_events: List[Dict[str, Any]] = []
        from actor_sheet import StatusType
        import random
        for actor in actors:
            try:
                stamina = actor.sheet.statuses[StatusType.STAMINA].value
                spirit = actor.sheet.statuses[StatusType.SPIRIT].value
                is_knocked_out = (stamina <= 0 or spirit <= 0) and not actor.sheet.is_dead()
                if is_knocked_out:
                    ko_remaining = actor.sheet.get_knockout_turns_remaining()
                    if ko_remaining > 0:
                        actor.sheet.decrement_knockout_turns()
                        ko_events.append({
                            'actor_name': actor.sheet.name,
                            'event': 'ko_tick',
                            'turns_remaining': actor.sheet.get_knockout_turns_remaining()
                        })
                        # Skip recovery this round while guaranteed KO is active
                        continue
                    else:
                        # 20% chance to recover above 0 on statuses at 0
                        if random.random() < 0.20:
                            if stamina <= 0:
                                actor.sheet.update_status(StatusType.STAMINA, 1, "KO recovery chance")
                            if spirit <= 0:
                                actor.sheet.update_status(StatusType.SPIRIT, 1, "KO recovery chance")
                            ko_events.append({
                                'actor_name': actor.sheet.name,
                                'event': 'ko_recovery_success'
                            })
                        else:
                            ko_events.append({
                                'actor_name': actor.sheet.name,
                                'event': 'ko_recovery_failed'
                            })
                            # Remain unconscious this round; skip temp recovery
                            continue
                # Actor is not knocked out or handled this round; allow normal temp recovery
                actors_for_recovery.append(actor)
            except Exception:
                actors_for_recovery.append(actor)
        
        recovery_events = self.recovery_manager.process_turn_start_recovery(actors_for_recovery)
        recovery_events.extend(ko_events)
        
        return recovery_events
    
    def process_round_start(self, actors: List[Actor]) -> List[Dict[str, Any]]:
        """
        Process enhanced round start recovery for all actors (legacy method)
        
        Args:
            actors: List of all actors in the scene
            
        Returns:
            List of recovery events that occurred
        """
        return self.apply_recovery_to_actors(actors)
    
    def get_recovery_status_for_actor(self, actor_name: str) -> Dict[str, Any]:
        """
        Get enhanced recovery status information for an actor
        
        Args:
            actor_name: Name of the actor
            
        Returns:
            Dictionary with recovery status information
        """
        return self.recovery_manager.get_recovery_status_for_actor(actor_name)
