#!/usr/bin/env python3
"""
Survival Action Analyzer for UTAS

Automatically detects when user actions fulfill survival needs without requiring
explicit survival action selection.
"""

from survival_system import SurvivalNeed
from typing import List, Dict, Any, Optional
import re

class SurvivalActionAnalyzer:
    """Analyzes user actions to automatically detect survival need fulfillment"""
    
    def __init__(self):
        """Precompile regex patterns with word boundaries to avoid substring matches.
        Also distinguish explicit action verbs from context nouns to prevent intention-only triggers.
        """
        # Cooldown configuration (minutes) to avoid repeated fulfillment spam
        self.COOLDOWN_MINUTES = 15
        # Track last fulfillment per (actor_name, need) for cooldown suppression
        self._last_fulfillment: dict[tuple[str, str], float] = {}
        # FOOD detection
        # Explicit consumption verbs (as standalone words or standard inflections)
        self._food_verbs = re.compile(r"\b(eat|eats|ate|eating|consume|consumes|consumed|consuming|devour|devours|devoured|devouring|chew|chews|chewed|chewing|swallow|swallows|swallowed|swallowing|munch|munches|munched|munching|dine|dined|dining)\b", re.IGNORECASE)
        # Meal phrases that imply consumption (e.g., have breakfast, grab a snack, order lunch)
        self._have_meal = re.compile(r"\bhave\s+(a\s+|some\s+)?(breakfast|lunch|dinner|meal|snack)\b", re.IGNORECASE)
        self._grab_meal = re.compile(r"\bgrab\s+(a\s+|some\s+)?(bite|breakfast|lunch|dinner|snack|meal)\b", re.IGNORECASE)
        self._order_meal = re.compile(r"\border\s+(a\s+|some\s+)?(breakfast|lunch|dinner|sandwich|burger|pizza|meal|snack|soup|pasta)\b", re.IGNORECASE)
        # Food nouns (do NOT trigger alone; used with verbs above)
        self._food_nouns = re.compile(r"\b(sandwich|burger|pizza|meal|food|snack|bread|apple|banana|cookie|cake|pasta|rice|soup|breakfast|lunch|dinner|feast)\b", re.IGNORECASE)

        # WATER detection (explicit drinking verbs OR beverage nouns with drink verbs)
        self._drink_verbs = re.compile(r"\b(drink|drinks|drank|drinking|sip|sips|sipped|sipping|gulp|gulps|gulped|gulping|hydrate|hydrating|hydrated|quench|quenching|quenched)\b", re.IGNORECASE)
        self._beverage_nouns = re.compile(r"\b(water|soda|juice|coffee|tea|beer|wine|beverage|liquid|fluid)\b", re.IGNORECASE)

        # SLEEP detection (whole-word verbs and states; 'rest' won't match 'restaurant')
        self._sleep_verbs = re.compile(r"\b(sleep|sleeps|slept|sleeping|nap|naps|napped|napping|doze|dozes|dozed|dozing|slumber|slumbering|lie\s+down|lying\s+down|retire)\b", re.IGNORECASE)
        self._sleep_states = re.compile(r"\b(rest|tired|exhausted|weary|close\s+eyes|drift\s+off|fall\s+asleep|pillow|blanket|bed)\b", re.IGNORECASE)

        # FULFILLMENT detection (social/hobby verbs)
        self._fulfill_verbs = re.compile(r"\b(relax|socialize|chat|talk|converse|play|read|create|build|laugh|smile|celebrate|meditate)\b", re.IGNORECASE)
        self._fulfill_nouns = re.compile(r"\b(hobby|fun|music|book|art|friend|companion|conversation|party|leisure|entertainment|peace|spiritual|zen)\b", re.IGNORECASE)
    
    def analyze_action(self, action_text: str) -> List[SurvivalNeed]:
        """
        Analyze a user action to determine which survival needs it fulfills
        
        Args:
            action_text: The user's action description
            
        Returns:
            List of SurvivalNeed enums that this action fulfills
        """
        text = action_text or ""
        fulfilled_needs: List[SurvivalNeed] = []

        # FOOD: require explicit consumption intent
        food_intent = bool(self._food_verbs.search(text) or self._have_meal.search(text) or self._grab_meal.search(text) or self._order_meal.search(text))
        if food_intent:
            fulfilled_needs.append(SurvivalNeed.FOOD)

        # WATER: require explicit drink verbs OR hydrate intent
        if self._drink_verbs.search(text):
            fulfilled_needs.append(SurvivalNeed.WATER)

        # SLEEP: require explicit sleep verbs or strong sleep state phrases (whole-word)
        # Avoid matching 'rest' inside 'restaurant' via word boundaries
        if self._sleep_verbs.search(text) or self._sleep_states.search(text):
            fulfilled_needs.append(SurvivalNeed.SLEEP)

        # FULFILLMENT: light-touch; verbs or nouns indicating recreation/socializing
        if self._fulfill_verbs.search(text) or self._fulfill_nouns.search(text):
            fulfilled_needs.append(SurvivalNeed.FULFILLMENT)

        return fulfilled_needs
    
    def get_action_costs(self, action_text: str, fulfilled_needs: List[SurvivalNeed]) -> Dict[str, Any]:
        """
        Determine time and supply costs for actions that fulfill survival needs
        
        Args:
            action_text: The user's action description
            fulfilled_needs: List of needs this action fulfills
            
        Returns:
            Dictionary with 'time_cost' and 'supply_cost' keys
        """
        action_lower = action_text.lower()
        
        # Base costs (survival needs are free - no supply costs)
        time_cost = 0.0
        supply_cost = 0  # Always 0 for survival needs
        
        # Calculate costs based on fulfilled needs (no supply costs - survival needs are free)
        for need in fulfilled_needs:
            if need == SurvivalNeed.FOOD:
                # Food time costs vary by type
                if any(word in action_lower for word in ["sandwich", "snack", "apple", "banana"]):
                    time_cost += 0.25  # Light meal
                elif any(word in action_lower for word in ["meal", "dinner", "lunch", "feast"]):
                    time_cost += 0.5  # Full meal
                else:
                    time_cost += 0.3  # Default food time
            
            elif need == SurvivalNeed.WATER:
                # Drink time costs vary by type
                if any(word in action_lower for word in ["water", "sip"]):
                    time_cost += 0.1  # Basic water
                elif any(word in action_lower for word in ["soda", "juice", "coffee", "tea"]):
                    time_cost += 0.2  # More complex beverage
                elif any(word in action_lower for word in ["beer", "wine"]):
                    time_cost += 0.3  # Alcoholic beverage
                else:
                    time_cost += 0.15  # Default drink time
            
            elif need == SurvivalNeed.SLEEP:
                # Sleep time varies by type
                if any(word in action_lower for word in ["nap", "doze", "rest"]):
                    time_cost += 2.0  # Short rest
                else:
                    time_cost += 8.0  # Full sleep
            
            elif need == SurvivalNeed.FULFILLMENT:
                # Fulfillment activities (no supply costs)
                if any(word in action_lower for word in ["socialize", "chat", "talk", "friend"]):
                    time_cost += 1.0  # Social activity
                elif any(word in action_lower for word in ["hobby", "play", "music", "art"]):
                    time_cost += 2.0  # Hobby activity
                else:
                    time_cost += 0.5  # Default fulfillment time
        
        return {
            'time_cost': time_cost,
            'supply_cost': supply_cost
        }
    
    def process_survival_fulfillment(self, actor_sheet, action_text: str, fulfilled_needs: List[SurvivalNeed], costs: Dict[str, Any], narrative_context_manager=None) -> List[str]:
        """
        Process the fulfillment of survival needs and apply costs
        
        Args:
            actor_sheet: The actor's character sheet
            action_text: The user's action description
            fulfilled_needs: List of needs this action fulfills
            costs: Dictionary with time and supply costs
            narrative_context_manager: Optional context manager for logging
            
        Returns:
            List of messages describing what happened
        """
        messages = []
        import time as _time
        actor_name = getattr(actor_sheet, 'name', getattr(getattr(actor_sheet, 'owner', None), 'name', 'Actor'))
        now = _time.time()
        cooldown_seconds = self.COOLDOWN_MINUTES * 60
        # Filter out needs that are within cooldown window
        filtered_needs: List[SurvivalNeed] = []
        for need in fulfilled_needs:
            key = (actor_name, need.value)
            last_ts = self._last_fulfillment.get(key, 0)
            if last_ts and (now - last_ts) < cooldown_seconds:
                # Suppress duplicate within cooldown
                continue
            filtered_needs.append(need)
        # If all suppressed, return empty messages
        if not filtered_needs:
            return messages
        # Update fulfilled_needs to filtered set for downstream processing
        fulfilled_needs = filtered_needs
        
        # No supply costs for survival needs - they are free
        
        # Fulfill the needs
        for need in fulfilled_needs:
            actor_sheet.survival.satisfy_need(need)
            messages.append(f"✓ {need.value.capitalize()} need satisfied")
            # Record cooldown timestamp
            self._last_fulfillment[(actor_name, need.value)] = now
        
        # Special handling for sleep (healing)
        if SurvivalNeed.SLEEP in fulfilled_needs:
            healing_messages = actor_sheet.survival.perform_sleep_healing(actor_sheet)
            messages.extend(healing_messages)
        
        # Optional narrative logging into context
        if narrative_context_manager is not None:
            try:
                from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
                needs_list = ", ".join([n.value for n in fulfilled_needs])
                narrative_context_manager.add_narrative_event(
                    event_type=NarrativeEventType.ACTION_OUTCOME,
                    narrative_text=f"Survival needs fulfilled: {needs_list} via '{action_text}'",
                    actors_involved=[actor_name],
                    importance=NarrativeImportance.ROUTINE,
                    emotional_tone="restorative"
                )
            except Exception:
                # Logging should not break core flow
                pass
        
        return messages
    
    def get_survival_summary(self, fulfilled_needs: List[SurvivalNeed], costs: Dict[str, Any]) -> str:
        """
        Generate a summary message for survival needs fulfilled
        
        Args:
            fulfilled_needs: List of needs this action fulfills
            costs: Dictionary with time and supply costs
            
        Returns:
            Formatted summary string
        """
        if not fulfilled_needs:
            return ""
        
        need_names = [need.value.capitalize() for need in fulfilled_needs]
        needs_text = ", ".join(need_names)
        
        cost_parts = []
        # No supply costs for survival needs
        if costs['time_cost'] > 0:
            cost_parts.append(f"{costs['time_cost']}h")
        
        cost_text = f" ({', '.join(cost_parts)})" if cost_parts else ""
        
        return f"🍽️ Survival needs fulfilled: {needs_text}{cost_text}"

# Global instance for easy access
survival_analyzer = SurvivalActionAnalyzer()
