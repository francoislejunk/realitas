"""
Sympathy Modifier Utilities

This module handles the nuanced sympathy modifier logic for the UTAS system.
The sympathy modifier affects action difficulty based on relationship dynamics and action intent.
"""

from actor_sheet import StatusType
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from actors import Actor

def calculate_sympathy_modifier(proactor: 'Actor', reactor: 'Actor', shift_polarity: str) -> int:
    """
    Calculate the sympathy modifier based on relationship and action intent.
    
    Args:
        proactor: The actor performing the action
        reactor: The target of the action
        shift_polarity: "Additive" or "Subtractive" - the intent of the action
    
    Returns:
        int: The sympathy modifier to be added to the difficulty calculation
        
    Logic:
        For Negative Sympathy (Enemies, -5 to -1):
        - Additive actions (helping): Harder to help enemies → sympathy becomes positive penalty
        - Subtractive actions (harming): Easier to harm enemies → sympathy stays negative (bonus)
        
        For Positive Sympathy (Friends, +1 to +5):
        - Additive actions (helping): Easier to help friends → sympathy becomes negative (bonus)
        - Subtractive actions (harming): Harder to harm friends → sympathy stays positive penalty
        
        For Neutral Sympathy (0):
        - No modifier applied
    """
    sympathy_value = proactor.sheet.get_sympathy(reactor.sheet.name)
    
    if sympathy_value == 0:
        return 0
    
    # Guard: if missing or not a string, no modifier applies
    if not isinstance(shift_polarity, str) or not shift_polarity.strip():
        print("Warning: Missing or invalid shift polarity (None/empty). No sympathy modifier applied.")
        return 0
    shift_polarity = shift_polarity.strip().title()
    
    if shift_polarity == "Additive":
        return -sympathy_value
    
    elif shift_polarity == "Subtractive":
        return sympathy_value
    
    else:
        print(f"Warning: Unknown shift polarity '{shift_polarity}'. No sympathy modifier applied.")
        return 0

def get_sympathy_modifier_description(proactor_name: str, reactor_name: str, 
                                    sympathy_value: int, shift_polarity: str, 
                                    modifier: int) -> str:
    """
    Generate a human-readable description of the sympathy modifier.
    
    Args:
        proactor_name: Name of the actor performing the action
        reactor_name: Name of the target actor
        sympathy_value: The raw sympathy value
        shift_polarity: "Additive" or "Subtractive"
        modifier: The calculated modifier
    
    Returns:
        str: Description of the sympathy modifier effect
    """
    if modifier == 0:
        if sympathy_value == 0:
            return f"{proactor_name} feels neutral toward {reactor_name} (no sympathy modifier)"
        else:
            return f"No sympathy modifier applied (unknown polarity: {shift_polarity})"
    
    if sympathy_value > 0:
        relationship = "friendly" if sympathy_value <= 2 else "close" if sympathy_value <= 4 else "beloved"
    else:
        relationship = "unfriendly" if sympathy_value >= -2 else "hostile" if sympathy_value >= -4 else "hated"
    
    action_type = "help" if shift_polarity == "Additive" else "harm"
    
    if modifier > 0:
        difficulty = "harder" if modifier <= 2 else "much harder"
    else:
        difficulty = "easier" if modifier >= -2 else "much easier"
    
    return (f"{proactor_name}'s {relationship} relationship with {reactor_name} "
            f"makes it {difficulty} to {action_type} them "
            f"(sympathy {sympathy_value:+d} → modifier {modifier:+d})")

if __name__ == "__main__":
    print("Sympathy Modifier Examples:")
    print("=" * 50)
    
    scenarios = [
        (3, "Additive", -3, "Helping a friend (easier)"),
        (3, "Subtractive", 3, "Harming a friend (harder)"),
        (-3, "Additive", 3, "Helping an enemy (harder)"),
        (-3, "Subtractive", -3, "Harming an enemy (easier)"),
        (0, "Additive", 0, "Neutral relationship"),
        (0, "Subtractive", 0, "Neutral relationship"),
    ]
    
    for sympathy, polarity, expected, desc in scenarios:
        if sympathy == 0:
            modifier = 0
        elif polarity == "Additive":
            modifier = -sympathy
        else:
            modifier = sympathy
            
        status = "✓" if modifier == expected else "✗"
        print(f"{status} {desc}: sympathy {sympathy:+d}, polarity {polarity} → modifier {modifier:+d}")
