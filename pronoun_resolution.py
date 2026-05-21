"""
Pronoun Resolution System

Resolves pronoun references (he/him, she/her, they/them) to NPCs in the scene.
"""

from typing import List, Optional, Tuple


def get_pronoun_forms(pronouns: str) -> Tuple[str, str, str, str, str]:
    """
    Get all pronoun forms from the base pronouns.
    
    Args:
        pronouns: Base pronouns (e.g., "he/him", "she/her", "they/them")
        
    Returns:
        Tuple of (subject, object, possessive, possessive_pronoun, reflexive)
        e.g., ("he", "him", "his", "his", "himself")
    """
    pronouns_lower = pronouns.lower().strip()
    
    if pronouns_lower in ["he/him", "he", "him"]:
        return ("he", "him", "his", "his", "himself")
    elif pronouns_lower in ["she/her", "she", "her"]:
        return ("she", "her", "her", "hers", "herself")
    elif pronouns_lower in ["they/them", "they", "them"]:
        return ("they", "them", "their", "theirs", "themselves")
    else:
        # Default to they/them
        return ("they", "them", "their", "theirs", "themselves")


def resolve_pronoun_to_npc(
    pronoun: str,
    available_npcs: List,
    recent_npc_name: Optional[str] = None
) -> Optional[str]:
    """
    Resolve a pronoun reference to an NPC name.
    
    Args:
        pronoun: The pronoun to resolve (e.g., "him", "her", "them")
        available_npcs: List of available NPCs
        recent_npc_name: Name of the most recently mentioned NPC (for context)
        
    Returns:
        NPC name if resolved, None otherwise
    """
    pronoun_lower = pronoun.lower().strip()
    
    # Map pronouns to their base forms
    pronoun_mapping = {
        "he": "he/him",
        "him": "he/him",
        "his": "he/him",
        "himself": "he/him",
        "she": "she/her",
        "her": "she/her",
        "hers": "she/her",
        "herself": "she/her",
        "they": "they/them",
        "them": "they/them",
        "their": "they/them",
        "theirs": "they/them",
        "themselves": "they/them",
    }
    
    target_pronouns = pronoun_mapping.get(pronoun_lower)
    if not target_pronouns:
        return None
    
    # Find NPCs with matching pronouns
    matching_npcs = []
    for npc in available_npcs:
        if hasattr(npc, 'sheet') and hasattr(npc.sheet, 'pronouns'):
            npc_pronouns = npc.sheet.pronouns.lower().strip()
            if npc_pronouns == target_pronouns:
                matching_npcs.append(npc)
    
    if not matching_npcs:
        return None
    
    # If only one match, return it
    if len(matching_npcs) == 1:
        return matching_npcs[0].sheet.name
    
    # If multiple matches, prefer the most recently mentioned NPC
    if recent_npc_name:
        for npc in matching_npcs:
            if npc.sheet.name == recent_npc_name:
                return npc.sheet.name
    
    # Otherwise, return the first match (ambiguous)
    return matching_npcs[0].sheet.name


def extract_pronoun_from_action(action: str) -> Optional[str]:
    """
    Extract pronoun reference from user action.
    
    Args:
        action: User action string
        
    Returns:
        Pronoun if found, None otherwise
    """
    action_lower = action.lower()
    
    pronouns = [
        "him", "her", "them",
        "he", "she", "they",
        "his", "hers", "their", "theirs",
        "himself", "herself", "themselves"
    ]
    
    for pronoun in pronouns:
        # Look for pronoun as a whole word
        if f" {pronoun} " in f" {action_lower} ":
            return pronoun
        if action_lower.startswith(f"{pronoun} "):
            return pronoun
        if action_lower.endswith(f" {pronoun}"):
            return pronoun
    
    return None


def replace_pronoun_with_name(action: str, pronoun: str, npc_name: str) -> str:
    """
    Replace pronoun in action with NPC name.
    
    Args:
        action: Original action string
        pronoun: Pronoun to replace
        npc_name: NPC name to use
        
    Returns:
        Action with pronoun replaced
    """
    import re
    
    # Case-insensitive replacement, preserving original case
    pattern = re.compile(re.escape(pronoun), re.IGNORECASE)
    
    def replace_func(match):
        # If original was capitalized, capitalize the replacement
        if match.group(0)[0].isupper():
            return npc_name
        return npc_name.lower()
    
    return pattern.sub(replace_func, action, count=1)
