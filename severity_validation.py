"""
Severity Validation and Table-Based Calculation Module

This module implements the UTAS OBJECTIVE.md table for calculating proper severity
values for self-effects based on condition, stress level, and provides validation
to ensure severity stays within the 1-4 range with special restrictions for magnitude 4.
"""

from typing import Dict, Any, Tuple, Optional
from color_utils import Color


class SeverityValidator:
    """
    Handles severity validation and table-based calculations for self-effects
    based on the UTAS OBJECTIVE.md specification.
    """
    
    SEVERITY_TABLE = {
        ("Inherent Cost", 1): 1,
        ("Inherent Cost", 2): 1,
        ("Inherent Cost", 3): 1,
        ("Inherent Cost", 4): 1,
        ("Inherent Cost", 5): 1,
        
        ("On Success", 1): 1,
        ("On Success", 2): 1,
        ("On Success", 3): 1,
        ("On Success", 4): 2,
        ("On Success", 5): 2,
        
        ("On Failure", 1): 1,
        ("On Failure", 2): 1,
        ("On Failure", 3): 1,
        ("On Failure", 4): 2,
        ("On Failure", 5): 3,
    }
    
    @classmethod
    def get_table_based_severity(cls, condition: str, stress_level: int) -> int:
        """
        Get the base severity from the UTAS OBJECTIVE.md table.
        
        Args:
            condition: "Inherent Cost", "On Success", or "On Failure"
            stress_level: 1-5 integer representing action difficulty
            
        Returns:
            Base severity value (1-4) from the table
        """
        condition_normalized = condition.strip()
        if condition_normalized in ["On Action Success", "Success"]:
            condition_normalized = "On Success"
        elif condition_normalized in ["On Action Failure", "Failure"]:
            condition_normalized = "On Failure"
        
        stress_level = max(1, min(5, stress_level))
        
        table_key = (condition_normalized, stress_level)
        if table_key in cls.SEVERITY_TABLE:
            return cls.SEVERITY_TABLE[table_key]
        
        print(f"{Color.YELLOW}Unknown condition '{condition}', using Inherent Cost fallback{Color.RESET}")
        return cls.SEVERITY_TABLE[("Inherent Cost", stress_level)]
    
    @classmethod
    def validate_severity(cls, severity: Any, condition: str = None, stress_level: int = None, 
                         is_exceptional_case: bool = False) -> Tuple[int, bool]:
        """
        Validate and potentially correct severity values.
        
        Args:
            severity: The severity value to validate
            condition: The self-effect condition (for table lookup if needed)
            stress_level: The action stress level (for table lookup if needed)
            is_exceptional_case: Whether this is an exceptional narrative case
            
        Returns:
            Tuple of (validated_severity, was_corrected)
        """
        was_corrected = False
        
        try:
            severity_int = int(severity)
        except (ValueError, TypeError):
            print(f"{Color.YELLOW}Invalid severity '{severity}', using table-based fallback{Color.RESET}")
            if condition and stress_level:
                severity_int = cls.get_table_based_severity(condition, stress_level)
                was_corrected = True
            else:
                severity_int = 1
                was_corrected = True
        
        if severity_int < 1:
            print(f"{Color.YELLOW}Severity {severity_int} below minimum, correcting to 1{Color.RESET}")
            severity_int = 1
            was_corrected = True
        elif severity_int > 4:
            print(f"{Color.YELLOW}Severity {severity_int} above maximum, correcting to 4{Color.RESET}")
            severity_int = 4
            was_corrected = True
        
        if severity_int == 4 and not is_exceptional_case:
            if condition == "On Failure" and stress_level == 5:
                print(f"{Color.SYSTEM}Magnitude 4 approved: Stress Level 5 failure is inherently exceptional{Color.RESET}")
            else:
                print(f"{Color.YELLOW}Magnitude 4 requires exceptional justification. Consider reducing to 3 unless narratively significant.{Color.RESET}")
        
        return severity_int, was_corrected
    
    @classmethod
    def validate_self_effect_severity(cls, self_effect: Dict[str, Any], stress_level: int = None) -> Dict[str, Any]:
        """
        Validate and potentially correct a single self-effect's severity.
        
        Args:
            self_effect: Dictionary containing self-effect data
            stress_level: The action's stress level for table lookup
            
        Returns:
            Corrected self-effect dictionary
        """
        if not isinstance(self_effect, dict):
            return self_effect
        
        condition = self_effect.get("condition", "Inherent Cost")
        current_severity = self_effect.get("severity")
        
        description = self_effect.get("description", "").lower()
        severity_justification = self_effect.get("severity_justification", "").lower()
        is_exceptional = any(keyword in description + severity_justification for keyword in [
            "exceptional", "extraordinary", "devastating", "life-changing", "permanent", 
            "traumatic", "overwhelming", "catastrophic", "critical"
        ])
        
        validated_severity, was_corrected = cls.validate_severity(
            current_severity, condition, stress_level, is_exceptional
        )
        
        corrected_effect = self_effect.copy()
        corrected_effect["severity"] = validated_severity
        
        if was_corrected:
            original_justification = corrected_effect.get("severity_justification", "")
            corrected_effect["severity_justification"] = (
                f"{original_justification} [System corrected from {current_severity} to {validated_severity}]"
            ).strip()
        
        return corrected_effect
    
    @classmethod
    def create_default_self_effect(cls, condition: str, stress_level: int, 
                                 target_status: str = "STAMINA") -> Dict[str, Any]:
        """
        Create a default self-effect using table-based severity calculation.
        
        Args:
            condition: "Inherent Cost", "On Success", or "On Failure"
            stress_level: 1-5 integer representing action difficulty
            target_status: Status to affect (default: STAMINA)
            
        Returns:
            Complete self-effect dictionary with table-based severity
        """
        base_severity = cls.get_table_based_severity(condition, stress_level)
        
        return {
            "condition": condition,
            "target_status": target_status,
            "polarity": "Subtractive",
            "shift_type": "Temporary",
            "severity": base_severity,
            "severity_justification": f"Table-based calculation: {condition} at Stress Level {stress_level} = {base_severity}",
            "description": f"Taking initiative requires effort, causing {target_status.lower()} depletion"
        }


def validate_severity_list(self_effects: list, stress_level: int = None) -> list:
    """
    Validate severity for a list of self-effects.
    
    Args:
        self_effects: List of self-effect dictionaries
        stress_level: The action's stress level for validation
        
    Returns:
        List of validated self-effect dictionaries
    """
    if not isinstance(self_effects, list):
        return self_effects
    
    validated_effects = []
    for effect in self_effects:
        validated_effect = SeverityValidator.validate_self_effect_severity(effect, stress_level)
        validated_effects.append(validated_effect)
    
    return validated_effects
