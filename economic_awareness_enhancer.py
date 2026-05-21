"""
Economic Awareness Enhancer for UTAS Simulation

Enhances NPC reactions to payment amounts and economic situations.
Prevents fake signals where NPCs don't react to being overpaid, underpaid, or robbed.
"""

from typing import Dict, Any, Optional
from color_utils import Color


class EconomicAwarenessEnhancer:
    """
    Enhances NPC awareness and reactions to economic situations.
    
    Features:
    - NPCs react to overpayment/underpayment
    - NPCs notice wealth disparities
    - NPCs adjust prices based on desperation
    - NPCs remember economic interactions
    """
    
    def __init__(self):
        self.price_expectations = {}
        self.economic_interactions = []
    
    def assess_payment(
        self,
        npc_name: str,
        expected_price: float,
        actual_payment: float,
        item_or_service: str
    ) -> Dict[str, Any]:
        """
        Assess NPC's reaction to payment amount.
        
        Returns:
            Dict with reaction_type, emotional_response, and narrative
        """
        difference = actual_payment - expected_price
        percentage_diff = (difference / expected_price * 100) if expected_price > 0 else 0
        
        # Determine reaction type
        if percentage_diff >= 50:
            reaction_type = "very_generous"
            emotional_response = "grateful_surprised"
            sympathy_shift = 2
            narrative = f"{npc_name} is pleasantly surprised by the generous payment of ${actual_payment:.2f} for {item_or_service}"
        elif percentage_diff >= 20:
            reaction_type = "generous"
            emotional_response = "grateful"
            sympathy_shift = 1
            narrative = f"{npc_name} appreciates the ${actual_payment:.2f} payment, more than the ${expected_price:.2f} asking price"
        elif percentage_diff >= -10:
            reaction_type = "fair"
            emotional_response = "satisfied"
            sympathy_shift = 0
            narrative = f"{npc_name} accepts the ${actual_payment:.2f} payment for {item_or_service}"
        elif percentage_diff >= -30:
            reaction_type = "underpaid"
            emotional_response = "disappointed"
            sympathy_shift = -1
            narrative = f"{npc_name} frowns at the ${actual_payment:.2f} payment, less than the ${expected_price:.2f} asking price"
        else:
            reaction_type = "severely_underpaid"
            emotional_response = "angry"
            sympathy_shift = -2
            narrative = f"{npc_name} is insulted by the ${actual_payment:.2f} payment, far below the ${expected_price:.2f} asking price"
        
        return {
            'reaction_type': reaction_type,
            'emotional_response': emotional_response,
            'sympathy_shift': sympathy_shift,
            'narrative': narrative,
            'difference': difference,
            'percentage_diff': percentage_diff
        }
    
    def assess_wealth_disparity(
        self,
        npc_money: float,
        target_money: float,
        npc_name: str,
        target_name: str
    ) -> Dict[str, Any]:
        """Assess NPC's awareness of wealth disparity."""
        
        if npc_money <= 0:
            npc_money = 1  # Avoid division by zero
        
        wealth_ratio = target_money / npc_money
        
        if wealth_ratio >= 10:
            awareness = "extremely_wealthy"
            reaction = f"{npc_name} notices {target_name} is extremely wealthy"
            behavior_change = "deferential"
        elif wealth_ratio >= 5:
            awareness = "very_wealthy"
            reaction = f"{npc_name} notices {target_name} has significant wealth"
            behavior_change = "respectful"
        elif wealth_ratio >= 2:
            awareness = "wealthier"
            reaction = f"{npc_name} notices {target_name} has more money"
            behavior_change = "neutral"
        elif wealth_ratio >= 0.5:
            awareness = "similar_wealth"
            reaction = f"{npc_name} and {target_name} have similar wealth"
            behavior_change = "neutral"
        elif wealth_ratio >= 0.2:
            awareness = "poorer"
            reaction = f"{npc_name} notices {target_name} has less money"
            behavior_change = "sympathetic"
        else:
            awareness = "much_poorer"
            reaction = f"{npc_name} notices {target_name} is struggling financially"
            behavior_change = "sympathetic"
        
        return {
            'awareness': awareness,
            'reaction': reaction,
            'behavior_change': behavior_change,
            'wealth_ratio': wealth_ratio
        }
    
    def get_desperation_pricing(
        self,
        base_price: float,
        npc_money: float,
        npc_needs: Dict[str, Any]
    ) -> float:
        """Calculate price adjustment based on NPC's desperation."""
        
        # Check if NPC is desperate (low money)
        if npc_money <= 10:
            # Very desperate - willing to sell cheap
            return base_price * 0.5
        elif npc_money <= 50:
            # Somewhat desperate
            return base_price * 0.75
        elif npc_money >= 500:
            # Wealthy - can charge more
            return base_price * 1.25
        
        return base_price
    
    def get_haggling_response(
        self,
        npc_name: str,
        original_price: float,
        offered_price: float,
        npc_personality: Dict,
        npc_money: float
    ) -> Dict[str, Any]:
        """Get NPC's response to haggling attempt."""
        
        difference_percent = ((original_price - offered_price) / original_price * 100)
        
        # Check personality traits
        is_greedy = 'greedy' in str(npc_personality).lower()
        is_generous = 'generous' in str(npc_personality).lower()
        is_desperate = npc_money < 20
        
        # Determine acceptance
        if is_desperate:
            # Desperate NPCs accept lower offers
            accept_threshold = 30
        elif is_greedy:
            # Greedy NPCs want full price
            accept_threshold = 5
        elif is_generous:
            # Generous NPCs more flexible
            accept_threshold = 25
        else:
            # Normal NPCs
            accept_threshold = 15
        
        will_accept = difference_percent <= accept_threshold
        
        if will_accept:
            counter_offer = offered_price
            response = "accept"
            narrative = f"{npc_name} accepts the ${offered_price:.2f} offer"
        elif difference_percent <= accept_threshold + 10:
            # Counter-offer
            counter_offer = (original_price + offered_price) / 2
            response = "counter"
            narrative = f"{npc_name} counters with ${counter_offer:.2f}"
        else:
            # Reject
            counter_offer = original_price
            response = "reject"
            narrative = f"{npc_name} refuses the low offer of ${offered_price:.2f}"
        
        return {
            'response': response,
            'will_accept': will_accept,
            'counter_offer': counter_offer,
            'narrative': narrative,
            'difference_percent': difference_percent
        }
    
    def get_robbery_reaction(
        self,
        npc_name: str,
        amount_stolen: float,
        npc_total_money: float
    ) -> Dict[str, Any]:
        """Get NPC's reaction to being robbed."""
        
        percentage_stolen = (amount_stolen / npc_total_money * 100) if npc_total_money > 0 else 100
        
        if percentage_stolen >= 75:
            severity = "devastating"
            emotional_impact = "traumatized"
            sympathy_shift = -5
            narrative = f"{npc_name} is devastated by losing ${amount_stolen:.2f}, nearly everything they had"
        elif percentage_stolen >= 50:
            severity = "severe"
            emotional_impact = "enraged"
            sympathy_shift = -4
            narrative = f"{npc_name} is furious about losing ${amount_stolen:.2f}, over half their money"
        elif percentage_stolen >= 25:
            severity = "significant"
            emotional_impact = "angry"
            sympathy_shift = -3
            narrative = f"{npc_name} is angry about losing ${amount_stolen:.2f}"
        else:
            severity = "minor"
            emotional_impact = "annoyed"
            sympathy_shift = -2
            narrative = f"{npc_name} is annoyed about losing ${amount_stolen:.2f}"
        
        return {
            'severity': severity,
            'emotional_impact': emotional_impact,
            'sympathy_shift': sympathy_shift,
            'narrative': narrative,
            'percentage_stolen': percentage_stolen
        }
    
    def display_economic_reaction(self, reaction: Dict[str, Any]):
        """Display economic reaction."""
        print(f"\n{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.INFO}💰 ECONOMIC REACTION{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.NARRATIVE}{reaction['narrative']}{Color.RESET}")
        
        if 'sympathy_shift' in reaction and reaction['sympathy_shift'] != 0:
            shift = reaction['sympathy_shift']
            print(f"{Color.WARNING}Sympathy Impact: {'+' if shift > 0 else ''}{shift}{Color.RESET}")
        
        print(f"{Color.INFO}{'='*80}{Color.RESET}\n")


# Global instance
economic_awareness = EconomicAwarenessEnhancer()
