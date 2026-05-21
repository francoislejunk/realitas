from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from actor_sheet import StatusType


def get_generic_descriptor(value: Optional[int]) -> str:
    """Converts a generic integer value into a narrative descriptor based on the specified scale."""
    descriptors = {
        -5: "Superb Reverse",
        -4: "Extraordinary Reverse",
        -3: "Average Reverse",
        -2: "Subpar Reverse",
        -1: "Minimal Reverse",
        0: "Null",
        1: "Minimal",
        2: "Subpar",
        3: "Average",
        4: "Extraordinary",
        5: "Superb"
    }
    return descriptors.get(value, "Unknown")

def get_serendipity_descriptor(value: Optional[int]) -> str:
    """
    Describes the influence of luck on the action using the standard serendipity mapping.
    DEPRECATED: Use N2N_Serendipity_Level() for UTAS compliance.
    """
    if value is None:
        return "null"
    
    return N2N_Serendipity_Level(value)


def N2N_Skill_Level(value: int) -> str:
    """Convert skill value to UTAS-compliant skill level descriptor."""
    skill_descriptors = {
        0: "Untrained",
        1: "Novice", 
        2: "Competent",
        3: "Proficient",
        4: "Expert",
        5: "Master"
    }
    return skill_descriptors.get(value, "Unknown")

def N2N_S_Trait_Level(value: int) -> str:
    """Convert S-trait value to narrative descriptor (Minimal→Superb)."""
    # Per design: only skills use Competent/Proficient/etc.
    # All other axes (including S-traits) use Minimal/Subpar/Average/Extraordinary/Superb
    return get_narrative_descriptor(value)

def N2N_Endowment_Level(value: int) -> str:
    """Convert endowment power value to UTAS-compliant power level descriptor."""
    endowment_descriptors = {
        0: "None",
        1: "Weak",
        2: "Moderate", 
        3: "Strong",
        4: "Powerful",
        5: "Legendary"
    }
    return super_descriptors.get(value, "Unknown")

def N2N_Status_Level(value: int) -> str:
    """Convert status value to UTAS-compliant status level descriptor."""
    status_descriptors = {
        0: "Depleted",
        1: "Critical",
        2: "Impaired", 
        3: "Average",
        4: "Strong",
        5: "Peak"
    }
    return status_descriptors.get(value, "Unknown")

def N2N_Shift_Magnitude(abs_value: int) -> str:
    """Convert absolute shift value to UTAS-compliant magnitude descriptor."""
    # Use the same core narrative magnitude ladder used elsewhere in the system
    # so reporting and narrator synthesis match.
    shift_descriptors = {
        0: "Null",
        1: "Minimal",
        2: "Subpar",
        3: "Average",
        4: "Extraordinary",
        5: "Superb",
    }
    if abs_value >= 6:
        return "Critical"
    return shift_descriptors.get(abs_value, "Unknown")

def N2N_Difficulty(stress_level: int) -> str:
    """Convert stress level to UTAS-compliant difficulty descriptor."""
    if stress_level <= 2:
        return "Routine"
    elif stress_level == 3:
        return "Challenging"
    elif stress_level == 4:
        return "Difficult"
    elif stress_level >= 5:
        return "Formidable"
    else:
        return "Unknown"

def N2N_Serendipity_Level(value: int) -> str:
    """Convert serendipity value to UTAS-compliant serendipity level descriptor."""
    serendipity_descriptors = {
        -5: "Superb Reverse",
        -4: "Extraordinary Reverse", 
        -3: "Average Reverse",
        -2: "Subpar Reverse",
        -1: "Minimal Reverse",
        0: "Null",
        1: "Minimal",
        2: "Subpar", 
        3: "Average",
        4: "Extraordinary",
        5: "Superb"
    }
    return serendipity_descriptors.get(value, "Unknown")

def N2N_Status_Modifier_Impact(modifier_value: int, status_type: str = "") -> str:
    """Convert status modifier value to UTAS-compliant impact descriptor."""
    if modifier_value > 0:
        return "Boost"
    elif modifier_value < 0:
        return "Penalty"
    else:
        return "No Modifier"

NARRATIVE_DESCRIPTORS = {
    -5: "Superb Reverse",
    -4: "Extraordinary Reverse",
    -3: "Average Reverse",
    -2: "Subpar Reverse",
    -1: "Minimal Reverse",
    0: "null",
    1: "Minimal",
    2: "Subpar",
    3: "Average",
    4: "Extraordinary",
    5: "Superb",
}

def get_narrative_descriptor(value: int) -> str:
    """
    Returns a narrative descriptor for a given numerical value.
    
    DEPRECATED: Use specific N2N functions for UTAS compliance:
    - N2N_Skill_Level() for skills
    - N2N_S_Trait_Level() for S-traits  
    - N2N_Status_Level() for status values
    - N2N_Shift_Magnitude() for shift magnitudes
    - N2N_Difficulty() for stress levels
    - N2N_Serendipity_Level() for serendipity values
    - etc.
    """
    return NARRATIVE_DESCRIPTORS.get(value, str(value))

def get_status_descriptor(status_value: int) -> str:
    """
    Returns a narrative descriptor for a given status value.
    DEPRECATED: Use get_narrative_descriptor instead for consistency.
    """
    if status_value <= 0:
        return "Depleted"
    return get_narrative_descriptor(status_value)

def _get_success_level_from_diff(success_diff: int) -> int:
    """Converts a raw success difference into a 0-5 level."""
    abs_diff = abs(success_diff)
    if abs_diff == 0: return 0
    elif abs_diff <= 2: return 1
    elif abs_diff <= 4: return 2
    elif abs_diff <= 6: return 3
    elif abs_diff <= 8: return 4
    else: return 5

def generate_template_narrative(
    proactor_name: str,
    reactor_name: str,
    proaction_skill: str,
    reaction_skill: str,
    success_diff: int,
    status_shifted: 'StatusType',
    shift_amount: int
) -> str:
    """Generates a narrative using customizable templates."""
    success_level = _get_success_level_from_diff(success_diff)
    success_desc = SUCCESS_LEVELS[success_level].lower()

    action_template = f"{proactor_name} attempts a {success_desc} strike with their {proaction_skill or 'innate talent'}."

    if success_diff > 0:
        outcome_template = f"{reactor_name}'s reaction fails, and their {status_shifted.name} is reduced by {shift_amount}."
    elif success_diff < 0:
        outcome_template = f"{reactor_name}'s {reaction_skill or 'quick thinking'} turns the tables, reducing {proactor_name}'s {status_shifted.name} by {shift_amount}."
    else:
        outcome_template = f"{reactor_name}'s reaction nullifies the attack, resulting in no change."

    return f"  - {action_template}\n  - {outcome_template}"

def get_success_level_narration(success_value: int) -> str:
    """
    Converts success value to narrative description for steps 2 and 4.
    1-5 = n2n descriptors, 6 = critical, 7+ = critical + extra
    """
    if success_value <= 0:
        return "with a FAILED attempt"
    elif success_value == 1:
        return "with a MINIMAL success attempt"
    elif success_value == 2:
        return "with a SUBPAR success attempt"
    elif success_value == 3:
        return "with an AVERAGE success attempt"
    elif success_value == 4:
        return "with an EXTRAORDINARY success attempt"
    elif success_value == 5:
        return "with a SUPERB success attempt"
    elif success_value == 6:
        return "with a CRITICAL success attempt"
    else:  # 7+
        extra_successes = success_value - 6
        return f"with a CRITICAL + ({extra_successes}) success attempt"


def get_success_level_numeric(success_value: int) -> int:
    """
    Converts success value to numeric level (1-5) for progression tracking.
    4+ is considered extraordinary for skill progression.
    
    Returns:
        1 = Minimal/Failed
        2 = Subpar
        3 = Average
        4 = Extraordinary
        5 = Superb/Critical
    """
    if success_value <= 1:
        return 1
    elif success_value == 2:
        return 2
    elif success_value == 3:
        return 3
    elif success_value == 4:
        return 4
    else:  # 5+
        return 5
