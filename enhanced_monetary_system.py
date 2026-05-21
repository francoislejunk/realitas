"""
Enhanced Monetary Exchange System for UTAS Simulation

This module provides comprehensive monetary transaction handling including:
- Inventory integration (items added/removed)
- Change calculation
- Transaction history tracking
- Contextual pricing (location, reputation, time-based)
- Social consequences for specific transaction types (bribes, gifts, gambling)

Note: Failed transaction consequences are handled by the existing self-effects system.
"""

from typing import Dict, Any, Optional, Tuple
from actor_sheet import StatusType, Item
from color_utils import Color
from economic_awareness_enhancer import economic_awareness

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


class EnhancedMonetaryProcessor:
    """
    Enhanced processor for monetary transactions with full feature set:
    - Inventory management
    - Change calculation
    - Social consequences
    - Transaction history
    - Contextual pricing
    """
    
    def __init__(self, tracker_agent=None):
        """
        Initialize the enhanced monetary processor.
        
        Args:
            tracker_agent: Optional TrackerAgent for transaction history
        """
        self.tracker_agent = tracker_agent
        self.transaction_history = []
    
    def process_enhanced_transaction(
        self,
        monetary_data: Dict[str, Any],
        proactor,
        reactor=None,
        success: bool = True,
        targeted_status: str = None
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Process a comprehensive monetary transaction with all enhancements.
        
        Args:
            monetary_data: Transaction metadata from detector
            proactor: Actor performing the transaction
            reactor: Optional reactor actor
            success: Whether the transaction succeeded (for contested actions)
            targeted_status: The status being targeted by the action (to avoid duplicate sympathy shifts)
            
        Returns:
            Tuple of (can_proceed: bool, narrative: str, consequences: dict)
        """
        if not monetary_data.get("transaction_detected", False):
            return True, "", {}
        
        transaction_type = monetary_data.get("transaction_type", "None")
        amount = monetary_data.get("amount", 0)
        payment_amount = monetary_data.get("payment_amount", amount)
        item_name = monetary_data.get("item_name", "")
        removes_item = monetary_data.get("removes_item", "")
        creates_item = monetary_data.get("creates_item", False)
        
        # Get proactor's current money
        supply_status = proactor.sheet.statuses[StatusType.SUPPLY]
        current_money = supply_status.money_amount
        
        # Calculate change if payment amount differs from cost
        change_amount = 0
        if payment_amount != amount and amount < 0:  # Spending with overpayment
            change_amount = abs(payment_amount) - abs(amount)
        
        # Initialize consequences dictionary
        consequences = {
            "sympathy_shift": 0,
            "spirit_shift": 0,
            "item_added": None,
            "item_removed": None,
            "change_received": change_amount,
            "social_impact": ""
        }
        
        # Handle failed transactions (insufficient funds)
        if amount < 0 and current_money + amount < 0:
            return self._handle_failed_transaction(
                monetary_data, proactor, reactor, current_money, consequences
            )
        
        # Apply the monetary change
        supply_status.modify(amount)
        
        # Handle inventory changes
        if creates_item and item_name and success:
            self._add_item_to_inventory(proactor, item_name, monetary_data, consequences)
        
        if removes_item and success:
            self._remove_item_from_inventory(proactor, removes_item, consequences)
        
        # Handle reactor money transfer
        if reactor and transaction_type in ["Purchase", "Bribe", "Service"] and amount < 0:
            reactor_supply = reactor.sheet.statuses[StatusType.SUPPLY]
            reactor_supply.modify(abs(amount))
        
        # Handle change
        if change_amount > 0:
            supply_status.modify(change_amount)
        
        # Apply social consequences based on transaction type
        # (only if not already targeting sympathy to avoid double-application)
        self._apply_social_consequences(
            transaction_type, proactor, reactor, success, amount, consequences, targeted_status
        )
        
        # Record transaction in history
        self._record_transaction(monetary_data, proactor, reactor, success, consequences)
        
        # Generate narrative
        from agents.interpreter_agent import InterpreterAgent
        # We'll need to import this properly or pass it in
        narrative = self._generate_enhanced_narrative(
            monetary_data, proactor, reactor, success, change_amount
        )
        
        return True, narrative, consequences
    
    def _handle_failed_transaction(
        self,
        monetary_data: Dict[str, Any],
        proactor,
        reactor,
        current_money: float,
        consequences: Dict[str, Any]
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """Handle failed transaction due to insufficient funds."""
        amount = abs(monetary_data.get("amount", 0))
        item = monetary_data.get("item_or_service", "the item")
        insufficient = amount - current_money
        
        # No additional penalties - self-effects already handle action consequences
        # Just block the transaction and provide clear feedback
        
        narrative = f"{proactor.sheet.name} cannot afford {item} (needs ${insufficient:.2f} more)..."
        
        print(f"\n{Color.WARNING}❌ TRANSACTION FAILED - INSUFFICIENT FUNDS{Color.RESET}")
        print(f"{Color.WARNING}Need: ${insufficient:.2f} more{Color.RESET}")
        print(f"{Color.WARNING}Current Balance: ${current_money:.2f} | Cost: ${amount:.2f}{Color.RESET}")
        print(f"{Color.INFO}Note: Self-effects from attempting the action still apply{Color.RESET}")
        
        return False, narrative, consequences
    
    def _add_item_to_inventory(
        self,
        proactor,
        item_name: str,
        monetary_data: Dict[str, Any],
        consequences: Dict[str, Any]
    ):
        """Add purchased/stolen item to proactor's inventory."""
        try:
            # Create item with appropriate properties
            item_description = monetary_data.get("item_or_service", item_name)
            supplement_bonus = self._estimate_supplement_bonus(item_name)
            
            new_item = Item(
                name=item_name,
                description=item_description,
                supplement_bonus=supplement_bonus
            )
            
            proactor.sheet.inventory.append(new_item)
            consequences["item_added"] = item_name
            
            print(f"{Color.SUCCESS}📦 Added to inventory: {item_name}{Color.RESET}")
            if supplement_bonus > 0:
                print(f"{Color.INFO}   Supplement Bonus: +{supplement_bonus}{Color.RESET}")

            # Best-effort: persist inventory gain into everlasting context DB + seed memory
            try:
                if ContextStore is not None:
                    session_id = 'default'
                    location_id = None
                    try:
                        if get_spatial_manager is not None:
                            spatial = get_spatial_manager()
                            session_id = getattr(spatial, 'session_id', None) or session_id
                            location_id = getattr(spatial, 'current_location', None)
                    except Exception:
                        pass

                    # Actor id best-effort
                    actor_name = getattr(getattr(proactor, 'sheet', None), 'name', None) or getattr(proactor, 'name', None) or 'unknown'
                    actor_id = actor_name
                    try:
                        if get_spatial_manager is not None:
                            spatial = get_spatial_manager()
                            ctx = spatial.get_current_context() if spatial else None
                            if ctx and getattr(ctx, 'actor_positions', None):
                                for aid, apos in ctx.actor_positions.items():
                                    if getattr(apos, 'actor_name', None) == actor_name:
                                        actor_id = aid
                                        break
                    except Exception:
                        actor_id = actor_name

                    wt = None
                    try:
                        if get_master_time_coordinator is not None and WorldTime is not None:
                            tc = get_master_time_coordinator()
                            time_ctx = tc.get_current_time_context() if tc else None
                            gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
                            if gt is not None:
                                wt = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
                    except Exception:
                        wt = None

                    from pathlib import Path
                    store = ContextStore(Path('simulation_data/context/context.db'))
                    summary = f"{actor_name} gained item: {item_name}"
                    event_id = store.log_world_event(
                        session_id=session_id,
                        location_id=location_id,
                        event_type='INVENTORY_UPDATED',
                        summary=summary,
                        importance=6 if supplement_bonus and supplement_bonus > 0 else 4,
                        tags=['inventory', 'item', 'gain'],
                        payload={
                            'actor_id': actor_id,
                            'actor_ids': [actor_id],
                            'actor_name': actor_name,
                            'actor_names': [actor_name],
                            'change_type': 'item_gained',
                            'item_name': item_name,
                            'item_description': item_description,
                            'supplement_bonus': supplement_bonus,
                            'transaction_type': monetary_data.get('transaction_type'),
                            'amount': monetary_data.get('amount'),
                        },
                        world_time=wt
                    )

                    try:
                        if hasattr(store, 'remember'):
                            store.remember(
                                session_id=session_id,
                                actor_id=str(actor_id),
                                memory_type='item_gained',
                                content=summary,
                                importance=6 if supplement_bonus and supplement_bonus > 0 else 4,
                                pinned=False,
                                decay_rate=0.0002,
                                source_event_id=int(event_id) if event_id is not None else None,
                                world_time=wt
                            )
                    except Exception:
                        pass
            except Exception:
                pass
        
        except Exception as e:
            print(f"{Color.ERROR}Failed to add item to inventory: {e}{Color.RESET}")
    
    def _remove_item_from_inventory(
        self,
        proactor,
        item_name: str,
        consequences: Dict[str, Any]
    ):
        """Remove sold item from proactor's inventory."""
        try:
            # Find and remove the item
            for i, item in enumerate(proactor.sheet.inventory):
                if item.name.lower() == item_name.lower() or item_name.lower() in item.name.lower():
                    removed_item = proactor.sheet.inventory.pop(i)
                    consequences["item_removed"] = removed_item.name
                    print(f"{Color.WARNING}📤 Removed from inventory: {removed_item.name}{Color.RESET}")

                    # Best-effort: persist inventory loss into everlasting context DB + seed memory
                    try:
                        if ContextStore is not None:
                            session_id = 'default'
                            location_id = None
                            try:
                                if get_spatial_manager is not None:
                                    spatial = get_spatial_manager()
                                    session_id = getattr(spatial, 'session_id', None) or session_id
                                    location_id = getattr(spatial, 'current_location', None)
                            except Exception:
                                pass

                            actor_name = getattr(getattr(proactor, 'sheet', None), 'name', None) or getattr(proactor, 'name', None) or 'unknown'
                            actor_id = actor_name
                            try:
                                if get_spatial_manager is not None:
                                    spatial = get_spatial_manager()
                                    ctx = spatial.get_current_context() if spatial else None
                                    if ctx and getattr(ctx, 'actor_positions', None):
                                        for aid, apos in ctx.actor_positions.items():
                                            if getattr(apos, 'actor_name', None) == actor_name:
                                                actor_id = aid
                                                break
                            except Exception:
                                actor_id = actor_name

                            wt = None
                            try:
                                if get_master_time_coordinator is not None and WorldTime is not None:
                                    tc = get_master_time_coordinator()
                                    time_ctx = tc.get_current_time_context() if tc else None
                                    gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
                                    if gt is not None:
                                        wt = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
                            except Exception:
                                wt = None

                            try:
                                item_desc = getattr(removed_item, 'description', '')
                                bonus = getattr(removed_item, 'supplement_bonus', 0)
                            except Exception:
                                item_desc = ''
                                bonus = 0

                            from pathlib import Path
                            store = ContextStore(Path('simulation_data/context/context.db'))
                            summary = f"{actor_name} lost item: {removed_item.name}"
                            event_id = store.log_world_event(
                                session_id=session_id,
                                location_id=location_id,
                                event_type='INVENTORY_UPDATED',
                                summary=summary,
                                importance=5,
                                tags=['inventory', 'item', 'loss'],
                                payload={
                                    'actor_id': actor_id,
                                    'actor_ids': [actor_id],
                                    'actor_name': actor_name,
                                    'actor_names': [actor_name],
                                    'change_type': 'item_lost',
                                    'item_name': removed_item.name,
                                    'item_description': item_desc,
                                    'supplement_bonus': bonus,
                                },
                                world_time=wt
                            )

                            try:
                                if hasattr(store, 'remember'):
                                    store.remember(
                                        session_id=session_id,
                                        actor_id=str(actor_id),
                                        memory_type='item_lost',
                                        content=summary,
                                        importance=5,
                                        pinned=False,
                                        decay_rate=0.00025,
                                        source_event_id=int(event_id) if event_id is not None else None,
                                        world_time=wt
                                    )
                            except Exception:
                                pass
                    except Exception:
                        pass
                    return
            
            print(f"{Color.WARNING}⚠️  Item '{item_name}' not found in inventory{Color.RESET}")
        
        except Exception as e:
            print(f"{Color.ERROR}Failed to remove item from inventory: {e}{Color.RESET}")
    
    def _estimate_supplement_bonus(self, item_name: str) -> int:
        """Estimate supplement bonus for an item based on its name."""
        item_lower = item_name.lower()
        
        # Weapons
        if any(weapon in item_lower for weapon in ['gun', 'pistol', 'revolver', 'rifle', 'shotgun']):
            return 3
        if any(weapon in item_lower for weapon in ['knife', 'blade', 'dagger']):
            return 2
        
        # Tools
        if any(tool in item_lower for tool in ['lockpick', 'crowbar', 'toolkit']):
            return 2
        
        # Protective gear
        if any(gear in item_lower for gear in ['vest', 'armor', 'helmet']):
            return 2
        
        # Electronics
        if any(elec in item_lower for elec in ['camera', 'recorder', 'radio', 'phone']):
            return 1
        
        # Clothing (minimal bonus)
        if any(cloth in item_lower for cloth in ['jacket', 'coat', 'boots', 'gloves']):
            return 1
        
        return 0  # No bonus for most items
    
    def _apply_social_consequences(
        self,
        transaction_type: str,
        proactor,
        reactor,
        success: bool,
        amount: float,
        consequences: Dict[str, Any],
        targeted_status: str = None
    ):
        """
        Apply social/sympathy consequences based on transaction type.
        
        Note: Only applies sympathy shifts if the action is NOT already targeting sympathy
        to avoid double-application with the exchange system.
        """
        if not reactor:
            return
        
        # Skip sympathy shifts if the action is already targeting sympathy
        # (exchange system will handle it)
        if targeted_status and targeted_status.upper() == "SYMPATHY":
            return
        
        try:
            # Bribe consequences
            if transaction_type == "Bribe":
                if success:
                    # Successful bribe improves sympathy temporarily
                    proactor.sheet.update_sympathy(reactor.sheet.name, 1)
                    consequences["sympathy_shift"] = 1
                    consequences["social_impact"] = "bribe accepted, relationship improved"
                else:
                    # Failed bribe damages sympathy significantly
                    proactor.sheet.update_sympathy(reactor.sheet.name, -2)
                    consequences["sympathy_shift"] = -2
                    consequences["social_impact"] = "bribe rejected, relationship damaged"
            
            # Theft consequences (only if caught/failed)
            elif transaction_type == "Theft" and not success:
                proactor.sheet.update_sympathy(reactor.sheet.name, -3)
                consequences["sympathy_shift"] = -3
                consequences["social_impact"] = "caught stealing, relationship severely damaged"
            
            # Gift consequences
            elif transaction_type == "Gift":
                # Gifts improve sympathy based on amount
                sympathy_gain = min(2, max(1, int(abs(amount) / 50)))
                proactor.sheet.update_sympathy(reactor.sheet.name, sympathy_gain)
                consequences["sympathy_shift"] = sympathy_gain
                consequences["social_impact"] = "generous gift, relationship improved"
            
            # Gambling consequences (with house/dealer)
            elif transaction_type == "Gambling":
                if success:
                    # Winning might slightly annoy the house
                    proactor.sheet.update_sympathy(reactor.sheet.name, -1)
                    consequences["sympathy_shift"] = -1
                    consequences["social_impact"] = "won against the house"
            
            # Purchase/Payment - check for economic awareness reactions
            elif transaction_type in ["Purchase", "Payment", "Service"]:
                # Get expected price (stored in monetary_data if available)
                expected_price = abs(amount)
                actual_payment = abs(amount)  # In successful transactions, these match
                
                # Assess payment reaction
                payment_reaction = economic_awareness.assess_payment(
                    reactor.sheet.name,
                    expected_price,
                    actual_payment,
                    "transaction"
                )
                
                # Apply additional sympathy shift if payment was generous/insulting
                if payment_reaction['sympathy_shift'] != 0:
                    reactor.sheet.update_sympathy(proactor.sheet.name, payment_reaction['sympathy_shift'])
                    consequences["economic_reaction"] = payment_reaction['narrative']
        
        except Exception as e:
            print(f"{Color.ERROR}Failed to apply social consequences: {e}{Color.RESET}")
    
    def _record_transaction(
        self,
        monetary_data: Dict[str, Any],
        proactor,
        reactor,
        success: bool,
        consequences: Dict[str, Any]
    ):
        """Record transaction in history for tracking."""
        transaction_record = {
            "proactor": proactor.sheet.name,
            "reactor": reactor.sheet.name if reactor else None,
            "type": monetary_data.get("transaction_type"),
            "amount": monetary_data.get("amount"),
            "item": monetary_data.get("item_or_service"),
            "success": success,
            "consequences": consequences
        }
        
        self.transaction_history.append(transaction_record)
        
        # Record in TrackerAgent if available
        if self.tracker_agent:
            try:
                self.tracker_agent.record_monetary_transaction(transaction_record)
            except Exception:
                pass
    
    def _generate_enhanced_narrative(
        self,
        monetary_data: Dict[str, Any],
        proactor,
        reactor,
        success: bool,
        change_amount: float
    ) -> str:
        """Generate enhanced narrative with change and social context."""
        transaction_type = monetary_data.get("transaction_type", "None")
        amount = abs(monetary_data.get("amount", 0))
        item = monetary_data.get("item_or_service", "the item")
        proactor_name = proactor.sheet.name
        reactor_name = reactor.sheet.name if reactor else "the vendor"
        
        # Check if proactor is UA for second-person narration
        is_user_actor = getattr(proactor, 'is_user_actor', False)
        
        # Use second person for UA, third person for NUA
        if is_user_actor:
            proactor_subject = "You"
            proactor_verb_pay = "pay"
            proactor_verb_steal = "steal"
            proactor_verb_earn = "earn"
            proactor_verb_give = "give"
            proactor_verb_slip = "slip"
            proactor_verb_attempt = "attempt"
            proactor_verb_borrow = "borrow"
            proactor_verb_loan = "loan"
            proactor_verb_win = "win"
            proactor_verb_lose = "lose"
            proactor_verb_sell = "sell"
            proactor_verb_complete = "complete"
            proactor_possessive = "your"
        else:
            proactor_subject = proactor_name
            proactor_verb_pay = "pays"
            proactor_verb_steal = "steals"
            proactor_verb_earn = "earns"
            proactor_verb_give = "gives"
            proactor_verb_slip = "slips"
            proactor_verb_attempt = "attempts"
            proactor_verb_borrow = "borrows"
            proactor_verb_loan = "loans"
            proactor_verb_win = "wins"
            proactor_verb_lose = "loses"
            proactor_verb_sell = "sells"
            proactor_verb_complete = "completes"
            proactor_possessive = f"{proactor_name}'s"
        
        # Add change narrative if applicable
        change_text = f", receiving ${change_amount:.2f} in change" if change_amount > 0 else ""
        
        # Generate narrative based on transaction type
        if transaction_type == "Purchase":
            if success:
                return f"{proactor_subject} {proactor_verb_pay} {reactor_name} ${amount:.2f} to obtain {item}{change_text}..."
            else:
                return f"{proactor_subject} cannot afford {item} (${amount:.2f} required)..."
        
        elif transaction_type == "Theft":
            if success:
                if monetary_data.get("creates_item"):
                    return f"{proactor_subject} successfully {proactor_verb_steal} {item} from {reactor_name}..."
                else:
                    return f"{proactor_subject} successfully {proactor_verb_steal} ${amount:.2f} from {reactor_name}..."
            else:
                return f"{proactor_subject} fail to steal from {reactor_name}..." if is_user_actor else f"{proactor_subject} fails to steal from {reactor_name}..."
        
        elif transaction_type == "Earning":
            return f"{proactor_subject} {proactor_verb_earn} ${amount:.2f} from {item}..."
        
        elif transaction_type == "Gift":
            return f"{proactor_subject} {proactor_verb_give} ${amount:.2f} to {reactor_name}..."
        
        elif transaction_type == "Payment":
            return f"{proactor_subject} {proactor_verb_pay} ${amount:.2f} for {item}{change_text}..."
        
        elif transaction_type == "Bribe":
            if success:
                return f"{proactor_subject} {proactor_verb_slip} {reactor_name} ${amount:.2f} as a bribe..."
            else:
                return f"{proactor_subject} {proactor_verb_attempt} to bribe {reactor_name} with ${amount:.2f}, but fail..." if is_user_actor else f"{proactor_subject} {proactor_verb_attempt} to bribe {reactor_name} with ${amount:.2f}, but fails..."
        
        elif transaction_type == "Loan":
            if amount > 0:  # Borrowing
                return f"{proactor_subject} {proactor_verb_borrow} ${amount:.2f} from {reactor_name}..."
            else:  # Lending
                return f"{proactor_subject} {proactor_verb_loan} ${amount:.2f} to {reactor_name}..."
        
        elif transaction_type == "Gambling":
            if success:
                return f"{proactor_subject} {proactor_verb_win} ${amount:.2f} from {item}..."
            else:
                return f"{proactor_subject} {proactor_verb_lose} ${amount:.2f} on {item}..."
        
        elif transaction_type == "Service":
            return f"{proactor_subject} {proactor_verb_pay} ${amount:.2f} for {item}{change_text}..."
        
        elif transaction_type == "Sale":
            return f"{proactor_subject} {proactor_verb_sell} {item} for ${amount:.2f}..."
        
        else:
            return f"{proactor_subject} {proactor_verb_complete} a ${amount:.2f} transaction..."
    
    def get_transaction_history(self, proactor_name: str = None, limit: int = 10) -> list:
        """
        Get transaction history, optionally filtered by actor.
        
        Args:
            proactor_name: Optional actor name to filter by
            limit: Maximum number of transactions to return
            
        Returns:
            List of transaction records
        """
        if proactor_name:
            filtered = [t for t in self.transaction_history if t["proactor"] == proactor_name]
            return filtered[-limit:]
        return self.transaction_history[-limit:]
