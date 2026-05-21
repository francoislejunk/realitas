"""
Automatic Inventory Management System

Detects when players acquire items through actions and automatically
adds them to their actor sheet inventory.
"""

import logging
from typing import Dict, Any, Optional, List
from actor_sheet import Item, ActorSheet
from openrouter_config import OpenRouterConfig
import json

try:
    from context_store import ContextStore, WorldTime
except Exception:
    ContextStore = None
    WorldTime = None

try:
    from master_time_coordinator import get_master_time_coordinator
except Exception:
    get_master_time_coordinator = None

try:
    from spatial_context_system import get_spatial_manager
except Exception:
    get_spatial_manager = None


class InventoryManager:
    """Manages automatic item acquisition detection and inventory updates."""
    
    # Action verbs that indicate item acquisition
    ACQUISITION_VERBS = [
        'pick up', 'pick', 'take', 'grab', 'acquire', 'obtain', 'get',
        'collect', 'gather', 'retrieve', 'find', 'discover', 'loot',
        'steal', 'pocket', 'snatch', 'seize', 'claim', 'secure'
    ]
    
    def __init__(self, llm_client):
        """
        Initialize the inventory manager.
        
        Args:
            llm_client: OpenAI-compatible client for LLM analysis
        """
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
    
    def detect_item_acquisition(self, user_input: str, action_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Detect if the user action involves acquiring an item.
        
        Args:
            user_input: The user's action input
            action_result: The result from action interpretation/execution
            
        Returns:
            Dictionary with item details if acquisition detected, None otherwise
        """
        # Quick heuristic check first with typo tolerance
        input_lower = user_input.lower()
        has_acquisition_verb = any(verb in input_lower for verb in self.ACQUISITION_VERBS)
        
        # Add fuzzy matching for common typos
        if not has_acquisition_verb:
            has_acquisition_verb = self._check_fuzzy_acquisition_verbs(input_lower)
        
        if not has_acquisition_verb:
            return None
        
        # Check if action was successful (don't add items for failed actions)
        success_total = action_result.get('success_calculation', {}).get('total_successes', 0)
        if success_total <= 0:
            self.logger.info("Item acquisition attempted but action failed - not adding to inventory")
            return None
        
        # Use LLM to extract item details
        return self._extract_item_details_llm(user_input, action_result)
    
    def _check_fuzzy_acquisition_verbs(self, input_lower: str) -> bool:
        """
        Check for common typos of acquisition verbs using fuzzy matching.
        
        Args:
            input_lower: Lowercase user input
            
        Returns:
            True if a fuzzy match is found, False otherwise
        """
        # Common typos for acquisition verbs
        typo_patterns = {
            'take': ['teak', 'taek', 'tkae', 'tke', 'tak'],
            'grab': ['garb', 'grap', 'grba', 'grb'],
            'pick': ['pikc', 'pcik', 'pik', 'pic'],
            'get': ['gte', 'gett', 'gt'],
            'steal': ['stael', 'seteal', 'stea', 'stel'],
            'collect': ['colect', 'collct', 'collet'],
            'gather': ['gahter', 'gathe', 'gtaher'],
            'retrieve': ['retreive', 'retrive', 'retreve']
        }
        
        # Check for typo patterns
        for correct_verb, typos in typo_patterns.items():
            for typo in typos:
                if typo in input_lower:
                    self.logger.info(f"Fuzzy match: '{typo}' matched to '{correct_verb}'")
                    return True
        
        return False
    
    def _extract_item_details_llm(self, user_input: str, action_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Use LLM to extract detailed item information from the action.
        
        Args:
            user_input: The user's action input
            action_result: The result from action interpretation/execution
            
        Returns:
            Dictionary with item details or None
        """
        narrative = action_result.get('narrative', '')
        
        prompt = f"""
Analyze this successful action to determine if an item was acquired and extract its details.

User Action: "{user_input}"
Action Narrative: "{narrative}"

Determine:
1. Was an item actually acquired/picked up/taken?
2. If yes, what is the item's name?
3. What is a brief description of the item?
4. Does this item provide any mechanical bonus? (supplement_bonus: 0-3)
   - 0: No mechanical benefit (most items)
   - 1: Minor benefit (flashlight, basic tools)
   - 2: Moderate benefit (quality equipment, weapons)
   - 3: Significant benefit (rare/powerful items)

Respond with JSON:
{{
    "item_acquired": true/false,
    "item_name": "Name of the item" or null,
    "item_description": "Brief description" or null,
    "supplement_bonus": 0-3 or 0,
    "reasoning": "Brief explanation of your analysis"
}}

Examples:
- "I pick up the phone" → {{"item_acquired": true, "item_name": "Phone", "item_description": "A mobile phone found on the ground", "supplement_bonus": 1}}
- "I take the revolver" → {{"item_acquired": true, "item_name": "Revolver", "item_description": "A .38 caliber revolver", "supplement_bonus": 2}}
- "I grab the keys" → {{"item_acquired": true, "item_name": "Keys", "item_description": "A set of keys", "supplement_bonus": 0}}
- "I look at the phone" → {{"item_acquired": false, "item_name": null, "item_description": null, "supplement_bonus": 0}}
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            response_content = response.choices[0].message.content.strip()
            if not response_content:
                return None
            
            # Extract JSON from response
            from json_utils import extract_and_parse_json
            result = extract_and_parse_json(response_content)
            
            if result and result.get('item_acquired', False):
                self.logger.info(f"Item acquisition detected: {result.get('item_name')} - {result.get('reasoning')}")
                return result
            
        except Exception as e:
            self.logger.warning(f"Failed to extract item details via LLM: {e}")
        
        return None
    
    def add_item_to_inventory(self, actor_sheet: ActorSheet, item_details: Dict[str, Any]) -> bool:
        """
        Add an item to the actor's inventory.
        
        Args:
            actor_sheet: The actor's character sheet
            item_details: Dictionary with item_name, item_description, supplement_bonus
            
        Returns:
            True if item was added, False otherwise
        """
        try:
            item_name = item_details.get('item_name')
            item_description = item_details.get('item_description', '')
            supplement_bonus = item_details.get('supplement_bonus', 0)
            
            if not item_name:
                self.logger.warning("Cannot add item without a name")
                return False
            
            # Check if item already exists in inventory
            existing_item = next((item for item in actor_sheet.inventory if item.name.lower() == item_name.lower()), None)
            if existing_item:
                self.logger.info(f"Item '{item_name}' already in inventory - not adding duplicate")
                return False
            
            # Create and add the new item
            new_item = Item(
                name=item_name,
                description=item_description,
                supplement_bonus=supplement_bonus
            )
            
            actor_sheet.inventory.append(new_item)
            self.logger.info(f"Added '{item_name}' to {actor_sheet.name}'s inventory (bonus: {supplement_bonus})")

            self._log_inventory_event(
                actor_name=actor_sheet.name,
                event_type="ITEM_GAINED",
                summary=f"{actor_sheet.name} gained item: {item_name}",
                payload={
                    "item_name": item_name,
                    "item_description": item_description,
                    "supplement_bonus": supplement_bonus,
                },
                importance=6 if supplement_bonus and supplement_bonus > 0 else 4,
                tags=["inventory", "item", "gain"],
                memory_type="item_gained",
                pinned=False
            )

            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add item to inventory: {e}")
            return False
    
    def process_action_for_inventory(self, user_input: str, action_result: Dict[str, Any], 
                                    actor_sheet: ActorSheet) -> Optional[str]:
        """
        Complete workflow: detect item acquisition and add to inventory if applicable.
        
        Args:
            user_input: The user's action input
            action_result: The result from action interpretation/execution
            actor_sheet: The actor's character sheet
            
        Returns:
            Success message if item was added, None otherwise
        """
        # Detect if item was acquired
        item_details = self.detect_item_acquisition(user_input, action_result)
        
        if not item_details:
            return None
        
        # Add to inventory
        if self.add_item_to_inventory(actor_sheet, item_details):
            item_name = item_details.get('item_name')
            bonus = item_details.get('supplement_bonus', 0)
            
            if bonus > 0:
                return f"📦 {item_name} added to inventory (provides +{bonus} supplement bonus)"
            else:
                return f"📦 {item_name} added to inventory"
        
        return None
    
    def remove_item_from_inventory(self, actor_sheet: ActorSheet, item_name: str) -> bool:
        """
        Remove an item from the actor's inventory.
        
        Args:
            actor_sheet: The actor's character sheet
            item_name: Name of the item to remove
            
        Returns:
            True if item was removed, False if not found
        """
        try:
            # Find the item (case-insensitive)
            item_to_remove = next((item for item in actor_sheet.inventory 
                                  if item.name.lower() == item_name.lower()), None)
            
            if item_to_remove:
                actor_sheet.inventory.remove(item_to_remove)
                self.logger.info(f"Removed '{item_name}' from {actor_sheet.name}'s inventory")

                try:
                    item_desc = getattr(item_to_remove, 'description', '')
                    bonus = getattr(item_to_remove, 'supplement_bonus', 0)
                except Exception:
                    item_desc = ''
                    bonus = 0

                self._log_inventory_event(
                    actor_name=actor_sheet.name,
                    event_type="ITEM_LOST",
                    summary=f"{actor_sheet.name} lost item: {item_name}",
                    payload={
                        "item_name": item_name,
                        "item_description": item_desc,
                        "supplement_bonus": bonus,
                    },
                    importance=5,
                    tags=["inventory", "item", "loss"],
                    memory_type="item_lost",
                    pinned=False
                )

                return True
            else:
                self.logger.warning(f"Item '{item_name}' not found in inventory")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to remove item from inventory: {e}")
            return False

    def _get_context_store_safe(self) -> Optional['ContextStore']:
        if ContextStore is None:
            return None
        try:
            from pathlib import Path
            return ContextStore(Path("simulation_data/context/context.db"))
        except Exception:
            return None

    def _get_world_time_safe(self) -> Optional['WorldTime']:
        try:
            if get_master_time_coordinator is None or WorldTime is None:
                return None
            tc = get_master_time_coordinator()
            time_ctx = tc.get_current_time_context() if tc else None
            gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
            if gt is None:
                return None
            return WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
        except Exception:
            return None

    def _try_resolve_spatial_actor_id_by_name(self, actor_name: str) -> Optional[str]:
        try:
            if not actor_name or get_spatial_manager is None:
                return None
            spatial = get_spatial_manager()
            ctx = spatial.get_current_context() if spatial else None
            if not ctx or not getattr(ctx, 'actor_positions', None):
                return None
            for aid, apos in ctx.actor_positions.items():
                if getattr(apos, 'actor_name', None) == actor_name:
                    return aid
            return None
        except Exception:
            return None

    def _get_session_and_location_safe(self) -> tuple[str, Optional[str]]:
        session_id = "default"
        location_id = None
        try:
            if get_spatial_manager is not None:
                spatial = get_spatial_manager()
                session_id = getattr(spatial, 'session_id', None) or "default"
                location_id = getattr(spatial, 'current_location', None)
        except Exception:
            pass
        return session_id, location_id

    def _log_inventory_event(self, *, actor_name: str, event_type: str, summary: str,
                             payload: Dict[str, Any], importance: int, tags: List[str],
                             memory_type: str, pinned: bool) -> None:
        store = self._get_context_store_safe()
        if store is None:
            return
        try:
            session_id, location_id = self._get_session_and_location_safe()
            wt = self._get_world_time_safe()
            actor_id = self._try_resolve_spatial_actor_id_by_name(actor_name) or actor_name
            full_payload = dict(payload or {})
            full_payload.update({
                "actor_id": actor_id,
                "actor_ids": [actor_id],
                "actor_name": actor_name,
                "actor_names": [actor_name],
            })
            event_id = store.log_world_event(
                session_id=session_id,
                location_id=location_id,
                event_type=event_type,
                summary=summary,
                importance=int(importance),
                tags=tags,
                payload=full_payload,
                world_time=wt
            )

            try:
                if hasattr(store, 'remember'):
                    store.remember(
                        session_id=session_id,
                        actor_id=str(actor_id),
                        memory_type=memory_type,
                        content=summary,
                        importance=int(importance),
                        pinned=bool(pinned),
                        source_event_id=int(event_id) if event_id is not None else None,
                        world_time=wt
                    )
            except Exception:
                pass
        except Exception:
            return
    
    def detect_item_removal(self, user_input: str) -> Optional[str]:
        """
        Detect if the user wants to drop/discard an item.
        
        Args:
            user_input: The user's action input
            
        Returns:
            Item name if removal detected, None otherwise
        """
        input_lower = user_input.lower()
        
        removal_verbs = ['drop', 'discard', 'throw away', 'get rid of', 'leave behind', 'abandon']
        
        if not any(verb in input_lower for verb in removal_verbs):
            return None
        
        # Use LLM to extract item name
        prompt = f"""
Analyze this action to determine if the user wants to remove an item from their inventory.

User Action: "{user_input}"

If they want to drop/discard/remove an item, respond with JSON:
{{
    "remove_item": true,
    "item_name": "Name of the item to remove"
}}

If not, respond with:
{{
    "remove_item": false,
    "item_name": null
}}
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=150
            )
            
            response_content = response.choices[0].message.content.strip()
            from json_utils import extract_and_parse_json
            result = extract_and_parse_json(response_content)
            
            if result and result.get('remove_item', False):
                return result.get('item_name')
                
        except Exception as e:
            self.logger.warning(f"Failed to detect item removal: {e}")
        
        return None
