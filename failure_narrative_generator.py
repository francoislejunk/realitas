"""
Failure Narrative Generator for UTAS
Generates logical narrative explanations for action failures and status shifts.
"""

from typing import Dict, Any, Optional
from action_type_detector import ActionCategory

class FailureNarrativeGenerator:
    """Generates narrative explanations for action failures and their consequences."""
    
    def __init__(self):
        # Narrative templates for different failure scenarios
        self.zero_success_narratives = {
            ActionCategory.MENTAL: {
                "SPIRIT": [
                    "fails to notice crucial details, leaving them feeling confused and uncertain",
                    "misses important information, causing doubt and mental frustration",
                    "cannot make sense of what they're observing, leading to cognitive strain",
                    "struggles to process the information, resulting in mental fatigue",
                    "finds their perception clouded, causing psychological stress"
                ]
            },
            ActionCategory.PHYSICAL: {
                "STAMINA": [
                    "exerts themselves but achieves nothing, wasting precious energy",
                    "strains against the obstacle unsuccessfully, depleting their physical reserves",
                    "pushes their body to the limit with no progress, leaving them drained",
                    "attempts the physical challenge but fails, exhausting themselves in the process",
                    "overexerts without success, feeling the toll on their body"
                ]
            }
        }
        
        self.negative_success_narratives = {
            ActionCategory.MENTAL: {
                "SPIRIT": [
                    "not only fails to gather information but becomes overwhelmed by confusion",
                    "misinterprets what they see, leading to dangerous misconceptions",
                    "becomes disoriented by conflicting sensory input, shaking their confidence",
                    "suffers from information overload, causing mental distress",
                    "finds their perception actively working against them, damaging their psyche"
                ]
            },
            ActionCategory.PHYSICAL: {
                "STAMINA": [
                    "not only fails but injures themselves in the attempt",
                    "overexerts so badly that they strain muscles and joints",
                    "pushes too hard and suffers physical consequences from the failed effort",
                    "attempts the challenge recklessly, resulting in bodily harm",
                    "exhausts themselves completely while making the situation worse"
                ]
            }
        }
        
        self.contested_failure_narratives = {
            "proactor_wins": [
                "overwhelms their opponent through superior skill and determination",
                "outmaneuvers their adversary with tactical precision",
                "dominates the exchange through sheer force of will",
                "proves their superiority in this contest of abilities",
                "succeeds where their opponent falters"
            ],
            "reactor_wins": [
                "successfully counters their opponent's attempt",
                "turns the tables with a skillful defensive maneuver",
                "proves more capable in this crucial moment",
                "outmatches their adversary's efforts",
                "demonstrates superior ability under pressure"
            ],
            "stalemate": [
                "matches their opponent's efforts exactly, neither gaining advantage",
                "finds themselves evenly matched with their adversary",
                "engages in a perfectly balanced contest with no clear victor",
                "demonstrates equal skill to their opponent in this exchange",
                "neither succeeds nor fails, locked in perfect opposition"
            ]
        }

    def generate_failure_narrative(self, actor_name: str, action_category: ActionCategory, 
                                 success_value: int, penalty_status: str) -> str:
        """
        Generate a narrative explanation for action failure and status penalty.
        
        Args:
            actor_name: Name of the actor who failed
            action_category: Category of the failed action
            success_value: The success value (0 or negative)
            penalty_status: The status being penalized
            
        Returns:
            Narrative string explaining the failure and its consequences
        """
        import random
        
        if success_value == 0:
            # Zero success - simple failure
            if action_category in self.zero_success_narratives:
                templates = self.zero_success_narratives[action_category].get(penalty_status, [])
                if templates:
                    template = random.choice(templates)
                    return f"{actor_name} {template}."
            
            # Fallback for zero success
            return f"{actor_name} fails to accomplish their goal, suffering the consequences of the failed attempt."
            
        elif success_value < 0:
            # Negative success - catastrophic failure
            if action_category in self.negative_success_narratives:
                templates = self.negative_success_narratives[action_category].get(penalty_status, [])
                if templates:
                    template = random.choice(templates)
                    return f"{actor_name} {template}."
            
            # Fallback for negative success
            return f"{actor_name} not only fails but makes their situation worse, suffering additional consequences."
        
        return f"{actor_name} experiences an unexpected setback."

    def generate_contested_outcome_narrative(self, proactor_name: str, reactor_name: str, 
                                           outcome_type: str, success_diff: int) -> str:
        """
        Generate narrative for contested action outcomes.
        
        Args:
            proactor_name: Name of the proactor
            reactor_name: Name of the reactor  
            outcome_type: "proactor_wins", "reactor_wins", or "stalemate"
            success_diff: Difference in success values
            
        Returns:
            Narrative string explaining the contested outcome
        """
        import random
        
        templates = self.contested_failure_narratives.get(outcome_type, [])
        if templates:
            base_narrative = random.choice(templates)
            
            if outcome_type == "proactor_wins":
                return f"{proactor_name} {base_narrative}, overcoming {reactor_name}'s resistance."
            elif outcome_type == "reactor_wins":
                return f"{reactor_name} {base_narrative}, thwarting {proactor_name}'s attempt."
            else:  # stalemate
                return f"{proactor_name} and {reactor_name} are evenly matched - {base_narrative}."
        
        # Fallback narratives
        if outcome_type == "proactor_wins":
            return f"{proactor_name} succeeds against {reactor_name}."
        elif outcome_type == "reactor_wins":
            return f"{reactor_name} successfully counters {proactor_name}."
        else:
            return f"{proactor_name} and {reactor_name} are perfectly matched."

    def generate_status_shift_explanation(self, actor_name: str, status_type: str, 
                                        original_value: int, new_value: int, 
                                        shift_reason: str) -> str:
        """
        Generate explanation for why a status shifted.
        
        Args:
            actor_name: Name of the affected actor
            status_type: Type of status (SPIRIT, STAMINA, SUPPLY)
            original_value: Original status value
            new_value: New status value
            shift_reason: Reason for the shift
            
        Returns:
            Narrative explanation of the status change
        """
        shift_amount = new_value - original_value
        
        status_descriptions = {
            "SPIRIT": {
                "positive": ["confidence", "morale", "mental fortitude", "psychological strength"],
                "negative": ["doubt", "demoralization", "mental strain", "psychological stress"]
            },
            "STAMINA": {
                "positive": ["energy", "physical strength", "vitality", "endurance"],
                "negative": ["exhaustion", "physical strain", "bodily fatigue", "weakness"]
            },
            "SUPPLY": {
                "positive": ["resources", "preparedness", "material advantage", "wealth"],
                "negative": ["resource depletion", "material loss", "financial strain", "scarcity"]
            }
        }
        
        import random
        
        if shift_amount > 0:
            # Positive shift
            desc_list = status_descriptions.get(status_type, {}).get("positive", ["strength"])
            description = random.choice(desc_list)
            return f"The successful outcome bolsters {actor_name}'s {description}."
        elif shift_amount < 0:
            # Negative shift
            desc_list = status_descriptions.get(status_type, {}).get("negative", ["condition"])
            description = random.choice(desc_list)
            
            if "failure" in shift_reason.lower():
                return f"The failure inflicts {description} upon {actor_name}."
            elif "penalty" in shift_reason.lower():
                return f"The poor performance causes {description} for {actor_name}."
            else:
                return f"The outcome results in {description} for {actor_name}."
        else:
            return f"{actor_name}'s {status_type.lower()} remains unchanged."
