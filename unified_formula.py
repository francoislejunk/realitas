"""
Unified Formula System for UTAS Simulation

This module implements the single unified formula used throughout the simulation:
(s-trait + skill + endowment + supplement + serendipity) - (stress modifier + status modifier + sympathy modifier)
"""

import random
from typing import Dict, Any, Optional, TYPE_CHECKING
from actor_sheet import SFactorType, StatusType
from sympathy_utils import calculate_sympathy_modifier

if TYPE_CHECKING:
    from actors import Actor

def calculate_status_modifier(status_value):
    """
    Calculates the status modifier for UTAS calculations based on UTAS OBJECTIVE.md specification:
    Status value 0 → modifier +3
    Status value 1 → modifier +2
    Status value 2 → modifier +1
    Status value 3 → modifier 0
    Status value 4 → modifier -1
    Status value 5 → modifier -2
    """
    status_modifier_map = {
        0: 3,
        1: 2,
        2: 1,
        3: 0,
        4: -1,
        5: -2
    }
    
    clamped_value = max(0, min(5, status_value))
    return status_modifier_map[clamped_value]

def calculate_unified_result(
    actor: 'Actor',
    s_trait: SFactorType,
    skill_name: Optional[str] = None,
    target_actor: Optional['Actor'] = None,
    shift_polarity: str = 'Subtractive',
    targeted_status: Optional[StatusType] = None,
    supplement_val: int = 0,
    serendipity_override: Optional[int] = None,
    stress_level_override: Optional[int] = None,
    endowment_name: Optional[str] = None,
    super_name: Optional[str] = None
) -> Dict[str, Any]:
    """
    Calculate result using the unified UTAS formula:
    (s-trait + skill + endowment + supplement + serendipity) - (stress modifier + status modifier + sympathy modifier)
    
    Args:
        actor: The actor performing the action
        s_trait: The S-Factor trait to use
        skill_name: Name of the skill to use (optional for some contexts like inquiries)
        target_actor: Target actor (for sympathy calculations, None for inquiries/INUA)
        shift_polarity: 'Additive' or 'Subtractive' for sympathy
        targeted_status: Status type being targeted (None for inquiries)
        supplement_val: Override supplement value (0 for inquiries)
        serendipity_override: Use specific serendipity value instead of rolling
        stress_level_override: Use specific stress level instead of actor's current
        
    Returns:
        Dictionary containing detailed calculation breakdown
    """
    
    
    s_trait_value = actor.sheet.s_factors.get_factor(s_trait)
    
    skill_value = actor.sheet.skills.get(skill_name, 0) if skill_name else 0
    
    # Backward-compatibility: older call sites may still pass `super_name`.
    # The simulation no longer models Supers as a separate mechanic; treat it as an endowment alias.
    if not endowment_name and super_name:
        endowment_name = super_name

    endowment_value = actor.sheet.endowments.get(endowment_name, 0) if endowment_name else 0
    
    supplement_value = supplement_val if supplement_val > 0 else (actor.sheet.get_supplement_bonus() if hasattr(actor.sheet, 'get_supplement_bonus') else 0)
    
    serendipity_value = serendipity_override if serendipity_override is not None else (random.randint(1, 6) + random.randint(1, 6) - 7)
    
    positive_total = s_trait_value + skill_value + endowment_value + supplement_value + serendipity_value
    
    
    if stress_level_override is not None:
        stress_modifier = max(1, min(5, stress_level_override)) - 3
    else:
        # Default stress level is 3 (neutral) since STRESS is not a valid StatusType
        # Stress is determined by action difficulty, not actor status
        stress_value = 3
        stress_modifier = stress_value - 3
    
    if targeted_status:
        if targeted_status == StatusType.SYMPATHY and target_actor:
            sympathy_obj = actor.sheet.sympathy.get(target_actor.sheet.name)
            if sympathy_obj and hasattr(sympathy_obj, 'value'):
                status_value = sympathy_obj.value
            else:
                status_value = 0
        else:
            status_obj = actor.sheet.statuses.get(targeted_status)
            if status_obj and hasattr(status_obj, 'value'):
                status_value = status_obj.value
            else:
                status_value = 3
        status_modifier = calculate_status_modifier(status_value)
    else:
        status_modifier = 0
    
    sympathy_modifier = calculate_sympathy_modifier(actor, target_actor, shift_polarity) if target_actor else 0 
    negative_total = stress_modifier + status_modifier + sympathy_modifier
    
    final_result = positive_total - negative_total
    
    return {
        'final_result': final_result,
        'positive_components': {
            's_trait': s_trait_value,
            'skill': skill_value,
            'endowment': endowment_value,
            'supplement': supplement_value,
            'serendipity': serendipity_value,
            'total': positive_total
        },
        'negative_components': {
            'stress_modifier': stress_modifier,
            'status_modifier': status_modifier,
            'sympathy_modifier': sympathy_modifier,
            'total': negative_total
        },
        'breakdown': {
            's_trait_name': s_trait.name if hasattr(s_trait, 'name') else str(s_trait),
            'skill_name': skill_name,
            'targeted_status': targeted_status.value if hasattr(targeted_status, 'value') else targeted_status if targeted_status else None,
            'shift_polarity': shift_polarity,
            'target_name': target_actor.sheet.name if target_actor else None
        }
    }

def format_calculation_display(result: Dict[str, Any]) -> str:
    """Format the calculation result for display."""
    pos = result['positive_components']
    neg = result['negative_components']
    
    display = f"({pos['s_trait']} + {pos['skill']} + {pos['endowment']} + {pos['supplement']} + {pos['serendipity']}) - ({neg['stress_modifier']} + {neg['status_modifier']} + {neg['sympathy_modifier']}) = {result['final_result']}"
    
    return display
