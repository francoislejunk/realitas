"""
Progression Integration Helper

Helper functions to integrate skill and sympathy progression into the main simulation.
Provides easy-to-use functions for tracking progression after actions.
"""

from typing import Dict, Any, Optional
from color_utils import Color
from narrative_utils import get_success_level_numeric


def process_and_display_progression(
    progression_manager,
    proactor_name: str,
    reactor_name: Optional[str],
    skill_used: str,
    success_value: int,
    action_description: str,
    action_polarity: str,
    proactor_actor,
    reactor_actor=None
) -> Dict[str, Any]:
    """
    Process progression tracking and display results.
    
    Args:
        progression_manager: ProgressionManager instance
        proactor_name: Name of actor performing action
        reactor_name: Name of reactor (if any)
        skill_used: Skill that was used
        success_value: Success value from calculation
        action_description: Description of the action
        action_polarity: "Additive" or "Subtractive"
        proactor_actor: Proactor Actor object
        reactor_actor: Reactor Actor object (if any)
        
    Returns:
        Dictionary with progression results
    """
    # Convert success value to level (1-5)
    success_level = get_success_level_numeric(success_value)
    
    # Determine if action succeeded (3+)
    success = success_value >= 3
    
    # Process progression
    results = progression_manager.process_action_result(
        proactor_name=proactor_name,
        reactor_name=reactor_name,
        skill_used=skill_used,
        success_level=success_level,
        action_description=action_description,
        action_polarity=action_polarity,
        success=success
    )
    
    # Display skill progression
    if results.get("skill_progression"):
        skill_result = results["skill_progression"]
        if skill_result.get("increased"):
            print(f"\n{Color.SUCCESS}📈 SKILL PROGRESSION!{Color.RESET}")
            print(f"{Color.INFO}Your {skill_result['skill_name']} skill has increased by {skill_result['increase_amount']}!{Color.RESET}")
            print(f"{Color.SYSTEM}Reason: {skill_result['reason']}{Color.RESET}")
            
            # Actually increase the skill on the actor sheet
            if hasattr(proactor_actor.sheet, 'skills') and skill_used in proactor_actor.sheet.skills:
                current_value = proactor_actor.sheet.skills[skill_used]
                proactor_actor.sheet.skills[skill_used] = current_value + 1
                print(f"{Color.SUCCESS}✓ {skill_used}: {current_value} → {current_value + 1}{Color.RESET}\n")
        elif skill_result.get("increased") is False:
            # Close to progression but didn't make it
            print(f"{Color.INFO}💪 You're getting better at {skill_result['skill_name']}... (progression roll: {skill_result['reason']}){Color.RESET}")
    
    # Display sympathy indirect effect
    if results.get("sympathy_indirect_effect"):
        symp_effect = results["sympathy_indirect_effect"]
        change = symp_effect["change_amount"]
        if change != 0:
            direction = "increased" if change > 0 else "decreased"
            emoji = "💚" if change > 0 else "💔"
            print(f"\n{Color.INFO}{emoji} Sympathy {direction} with {reactor_name}{Color.RESET}")
            print(f"{Color.SYSTEM}Reason: {symp_effect['reason']}{Color.RESET}")
            
            # Actually change sympathy on the actor sheet
            if reactor_actor and hasattr(proactor_actor.sheet, 'sympathies'):
                if reactor_name in proactor_actor.sheet.sympathies:
                    current_symp = proactor_actor.sheet.sympathies[reactor_name]
                    new_symp = max(-5, min(5, current_symp + change))
                    proactor_actor.sheet.sympathies[reactor_name] = new_symp
                    print(f"{Color.SYSTEM}Sympathy: {current_symp} → {new_symp}{Color.RESET}")
            
            # REPUTATION PROPAGATION: Word spreads through social network
            if abs(change) >= 1 and reactor_name:
                try:
                    from world_persistence_system import get_world_state_manager
                    world_state = get_world_state_manager()
                    
                    # Determine action type for propagation
                    if change > 0:
                        action_type = "helped" if action_polarity == "Additive" else "impressed"
                    else:
                        action_type = "harmed" if action_polarity == "Subtractive" else "insulted"
                    
                    # Define updater function for propagated sympathy changes
                    def update_npc_sympathy(npc_name, user_name, change_amount):
                        # This would need access to NPC actor sheets
                        # For now, just track the propagation
                        pass
                    
                    # Propagate reputation through social network
                    world_state.process_reputation_change(
                        user_name=proactor_name,
                        npc_name=reactor_name,
                        action_type=action_type,
                        magnitude=abs(change),
                        actor_sheet_updater=update_npc_sympathy
                    )
                    
                    # NPC MEMORY: Record this interaction
                    try:
                        from world_persistence_system import get_extended_world_state_manager
                        ext_world = get_extended_world_state_manager()
                        
                        emotional_impact = "grateful" if change > 0 else "angry"
                        ext_world.npc_memory.record_interaction(
                            npc_name=reactor_name,
                            interaction_type=action_type,
                            description=symp_effect.get('reason', 'interacted'),
                            emotional_impact=emotional_impact,
                            importance=min(5, abs(change) + 2)
                        )
                        
                        # FACTION REPUTATION: Update faction standing
                        faction_changes = ext_world.faction_system.modify_reputation_via_member(
                            npc_name=reactor_name,
                            change=change * 5  # Scale for faction rep (-100 to +100)
                        )
                        for fc in faction_changes:
                            print(f"{Color.SYSTEM}📊 {fc['faction']} reputation: {fc['new_reputation']}{Color.RESET}")
                        
                        # RUMOR: Create rumor about significant interactions
                        if abs(change) >= 2:
                            ext_world.rumor_system.create_rumor(
                                fact=f"{proactor_name} {action_type} {reactor_name}",
                                subject=proactor_name,
                                origin_npc=reactor_name
                            )
                    except Exception:
                        pass
                except Exception:
                    pass  # Reputation propagation is optional enhancement
    
    # Display sympathy progression (interaction tracking)
    if results.get("sympathy_progression"):
        symp_prog = results["sympathy_progression"]
        if symp_prog.get("changed"):
            change = symp_prog["change_amount"]
            direction = "increased" if change > 0 else "decreased"
            emoji = "💚" if change > 0 else "💔"
            print(f"\n{Color.SUCCESS}{emoji} SYMPATHY PROGRESSION!{Color.RESET}")
            print(f"{Color.INFO}Your relationship with {reactor_name} has {direction}!{Color.RESET}")
            print(f"{Color.SYSTEM}Reason: {symp_prog['reason']}{Color.RESET}")
            
            # Actually change sympathy on the actor sheet
            if reactor_actor and hasattr(proactor_actor.sheet, 'sympathies'):
                if reactor_name in proactor_actor.sheet.sympathies:
                    current_symp = proactor_actor.sheet.sympathies[reactor_name]
                    new_symp = max(-5, min(5, current_symp + change))
                    proactor_actor.sheet.sympathies[reactor_name] = new_symp
                    print(f"{Color.SUCCESS}✓ Sympathy: {current_symp} → {new_symp}{Color.RESET}\n")
        elif symp_prog.get("changed") is False:
            # Close to progression but didn't make it
            print(f"{Color.INFO}🤝 Your relationship with {reactor_name} is evolving... ({symp_prog['reason']}){Color.RESET}")
    
    return results


def display_progression_status(progression_manager, actor_name: str, skill_name: str = None):
    """
    Display current progression status for skills.
    
    Args:
        progression_manager: ProgressionManager instance
        actor_name: Name of the actor
        skill_name: Specific skill to check (optional)
    """
    skill_tracker = progression_manager.get_skill_tracker(actor_name)
    
    if skill_name:
        progress = skill_tracker.get_skill_progress(skill_name)
        print(f"\n{Color.INFO}📊 {skill_name} Progression:{Color.RESET}")
        print(f"{Color.SYSTEM}Extraordinary uses: {progress['extraordinary_uses']}/{progress['uses_needed']}{Color.RESET}")
        print(f"{Color.SYSTEM}Progress: {progress['progress_percentage']:.0f}%{Color.RESET}")
        if progress['last_increase']:
            print(f"{Color.SYSTEM}Last increase: {progress['last_increase']['timestamp']}{Color.RESET}")


def display_sympathy_progression_status(progression_manager, actor1: str, actor2: str):
    """
    Display current sympathy progression status between two actors.
    
    Args:
        progression_manager: ProgressionManager instance
        actor1: First actor name
        actor2: Second actor name
    """
    progress = progression_manager.sympathy_tracker.get_sympathy_progress(actor1, actor2)
    
    print(f"\n{Color.INFO}🤝 Relationship Progress ({actor1} ↔ {actor2}):{Color.RESET}")
    print(f"{Color.SYSTEM}Interactions: {progress['interactions_recorded']}/{progress['interactions_needed']}{Color.RESET}")
    print(f"{Color.SYSTEM}Progress: {progress['progress_percentage']:.0f}%{Color.RESET}")
    print(f"{Color.SYSTEM}Current lean: {progress['current_lean']} ({progress['friendly_count']} friendly, {progress['hostile_count']} hostile){Color.RESET}")
    if progress['last_change']:
        print(f"{Color.SYSTEM}Last change: {progress['last_change']['reason']}{Color.RESET}")
