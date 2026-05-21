import math
import random
from typing import Dict, Any, List, Tuple, Optional

from actors import Actor
from actor_sheet import StatusType, SFactorType
from numeric_utils import extract_numeric_value
from enhanced_temporary_recovery_system import EnhancedTemporaryRecoveryIntegrator
from sympathy_utils import calculate_sympathy_modifier, get_sympathy_modifier_description
from rule_of_3s import RuleOf3Category, RuleOf3Context
from witness_reaction_system import witness_system
from actor_state_filter import actor_state_filter

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

def _get_context_store_safe():
    if ContextStore is None:
        return None
    try:
        from pathlib import Path
        return ContextStore(Path("simulation_data/context/context.db"))
    except Exception:
        return None

def _get_world_time_safe():
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

def _get_session_and_location_safe():
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

def _try_resolve_spatial_actor_id_by_name(actor_name: str) -> Optional[str]:
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

from object_registry import get_object_state, get_status as get_obj_status, set_status as set_obj_status, merge_object_state
try:
    from object_registry import save_registry_for_session
except Exception:
    save_registry_for_session = None
def round_half_away_from_zero(value):
    """
    Rounds using the "Round Half Away From Zero" method as specified in UTAS OBJECTIVE.md.
    This ensures perfect compliance with the UTAS specification.
    
    Examples:
    - round_half_away_from_zero(2.5) = 3
    - round_half_away_from_zero(-2.5) = -3
    - round_half_away_from_zero(2.3) = 2
    - round_half_away_from_zero(-2.3) = -2
    """
    if value == 0:
        return 0
    elif value > 0:
        return math.floor(value + 0.5)
    else:
        return math.ceil(value - 0.5)

def calculate_status_modifier(status_value):
    """
    Calculates the status modifier for UTAS calculations based on UTAS OBJECTIVE.md specification:
    Status value 0 → modifier +3
    Status value 1 → modifier +2
    Status value 2 → modifier +1
    Status value 3 → modifier 0
    Status value 4 → modifier -1
    Status value 5 → modifier -2
    
    This mapping is used ONLY for calculation purposes in the Exchange system.
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

class ExchangeSystem:
    """
    Manages the mechanical resolution of a single turn between a proactor and a reactor,
    based on structured action data provided by the Arbiter.
    """

    def __init__(self, proactor: 'Actor', reactor: 'Actor', proactor_action_data: Dict[str, Any], reactor_action_data: Dict[str, Any], recovery_integrator: EnhancedTemporaryRecoveryIntegrator = None, rule_of_3s_context: Optional[RuleOf3Context] = None):
        """
        Initializes the exchange with the participants and their interpreted actions.
        """
        self.proactor = proactor
        self.reactor = reactor
        self.proactor_action = proactor_action_data
        self.reactor_action = reactor_action_data
        self.recovery_integrator = recovery_integrator or EnhancedTemporaryRecoveryIntegrator()
        self.rule_of_3s_context = rule_of_3s_context
        
        # FIX BUG #12: Ensure sympathy exists between actors on first meeting
        self.proactor.sheet.ensure_sympathy_exists(self.reactor.sheet.name, self.reactor.sheet)
        self.reactor.sheet.ensure_sympathy_exists(self.proactor.sheet.name, self.proactor.sheet)

    def execute(self, is_inua_exchange=False) -> Dict[str, Any]:
        """
        Executes the exchange using the detailed success formula,
        calculates success, applies outcomes, and returns a dictionary of the results.
        """
        try:
            proactor_success = 0
            reactor_success = 0
            # Track new status values for accurate reporting
            new_proactor_status = None
            new_reactor_status = None

            if is_inua_exchange:
                return self._execute_inua_exchange()

            proactor_factors = self.proactor_action.get("utas_factors", {})
            reactor_factors = self.reactor_action.get("utas_factors", {})
            
            # Get proactor's targeted status
            try:
                p_status_name = proactor_factors.get("status_to_shift", "SPIRIT").upper()
                proactor_targeted_status = StatusType[p_status_name]
            except KeyError:
                proactor_targeted_status = StatusType.SPIRIT
            
            # Get reactor's targeted status (may be different from proactor's)
            try:
                r_status_name = reactor_factors.get("status_to_shift", "SPIRIT").upper()
                reactor_targeted_status = StatusType[r_status_name]
            except KeyError:
                reactor_targeted_status = StatusType.SPIRIT
            
            print(f"DEBUG: Proactor targeting {proactor_targeted_status.name}, Reactor targeting {reactor_targeted_status.name}")

            p_sheet = self.proactor.sheet
            p_skill_name_raw = proactor_factors.get("skill")
            if isinstance(p_skill_name_raw, dict) and p_skill_name_raw:
                p_skill_name = p_skill_name_raw.get("name")
            else:
                p_skill_name = p_skill_name_raw
            p_skill_val = p_sheet.skills.get(p_skill_name, 0) if p_skill_name else 0
            p_s_trait_name = proactor_factors.get("s_trait_to_use", "STURDINESS").upper()
            try:
                p_s_trait_val = p_sheet.s_factors.get_factor(SFactorType[p_s_trait_name])
            except KeyError:
                print(f"Warning: Invalid S-Trait '{p_s_trait_name}' provided for proactor. Defaulting to STURDINESS.")
                p_s_trait_name = "STURDINESS"
                p_s_trait_val = p_sheet.s_factors.get_factor(SFactorType[p_s_trait_name])
            p_supplement_val = proactor_factors.get("supplement_val") or 0
            p_super_name = proactor_factors.get("super")
            p_super_val = p_sheet.supers.get(p_super_name, 0) if p_super_name else 0
            p_serendipity = self.proactor_action.get('success_calculation', {}).get('serendipity', 0)
            p_stress_level = extract_numeric_value(proactor_factors.get("stress_level", 3), default=3, min_val=1, max_val=5)
            p_stress_modifier = p_stress_level - 3
            if proactor_targeted_status == StatusType.SYMPATHY:
                p_status_value = p_sheet.sympathy[self.reactor.sheet.name].value
            else:
                p_status_value = p_sheet.statuses[proactor_targeted_status].value
            p_status_modifier = calculate_status_modifier(p_status_value)
            
            # DEBUG: Status modifier calculation
            print(f"DEBUG: Proactor status value for {proactor_targeted_status}: {p_status_value}")
            print(f"DEBUG: Proactor status modifier calculated: {p_status_modifier}")

            p_shift_polarity = proactor_factors.get('shift_polarity')
            if p_shift_polarity in (None, "", []):
                p_sympathy_modifier = 0
                print("Warning: Missing proactor shift_polarity; skipping sympathy modifier this turn.")
            else:
                p_sympathy_modifier = calculate_sympathy_modifier(self.proactor, self.reactor, p_shift_polarity)
                if p_sympathy_modifier != 0:
                    p_sympathy_description = get_sympathy_modifier_description(
                        self.proactor.sheet.name, self.reactor.sheet.name,
                        self.proactor.sheet.get_sympathy(self.reactor.sheet.name),
                        p_shift_polarity, p_sympathy_modifier
                    )
                    print(f"      * Proactor Sympathy Modifier: {p_sympathy_description}")

            from unified_formula import calculate_unified_result, format_calculation_display
            try:
                p_s_trait_enum = SFactorType[p_s_trait_name]
            except KeyError:
                p_s_trait_enum = SFactorType.STURDINESS
            
            # Use pre-calculated success from step 2 if available
            if 'success_calculation' in self.proactor_action and 'total' in self.proactor_action['success_calculation']:
                proactor_success = self.proactor_action['success_calculation']['total']
                proactor_calc_str = self.proactor_action['success_calculation'].get('calc_str', 'Pre-calculated')
                print(f"DEBUG: Using pre-calculated proactor success: {proactor_success}")
            else:
                proactor_unified_result = calculate_unified_result(
                    actor=self.proactor,
                    s_trait=p_s_trait_enum,
                    skill_name=p_skill_name,
                    target_actor=self.reactor,
                    shift_polarity=p_shift_polarity,
                    targeted_status=proactor_targeted_status,
                    supplement_val=p_supplement_val,
                    serendipity_override=p_serendipity,
                    stress_level_override=p_stress_level
                )
                proactor_success = proactor_unified_result['final_result']
                proactor_calc_str = format_calculation_display(proactor_unified_result)
                print(f"DEBUG: Calculated new proactor success: {proactor_success}")

            r_sheet = self.reactor.sheet
            r_skill_name_raw = reactor_factors.get("skill")
            if isinstance(r_skill_name_raw, dict) and r_skill_name_raw:
                r_skill_name = r_skill_name_raw.get("name")
            else:
                r_skill_name = r_skill_name_raw
            r_skill_val = r_sheet.skills.get(r_skill_name, 0) if r_skill_name else 0
            r_s_trait_name = reactor_factors.get("s_trait_to_use", "STURDINESS").upper()
            try:
                r_s_trait_val = r_sheet.s_factors.get_factor(SFactorType[r_s_trait_name])
            except KeyError:
                print(f"Warning: Invalid S-Trait '{r_s_trait_name}' provided for reactor. Defaulting to STURDINESS.")
                r_s_trait_name = "STURDINESS"
                r_s_trait_val = r_sheet.s_factors.get_factor(SFactorType[r_s_trait_name])
            r_supplement_val = reactor_factors.get("supplement_val") or 0
            r_super_name = reactor_factors.get("super")
            r_super_val = r_sheet.supers.get(r_super_name, 0) if r_super_name else 0
            r_serendipity = self.reactor_action.get('success_calculation', {}).get('serendipity', 0)
            r_stress_level = extract_numeric_value(reactor_factors.get("stress_level", 3), default=3, min_val=1, max_val=5)
            print(f"DEBUG: Reactor stress_level extracted: {r_stress_level} (from raw: {reactor_factors.get('stress_level', 'NOT_FOUND')})")
            r_stress_modifier = r_stress_level - 3
            print(f"DEBUG: Reactor stress_modifier calculated: {r_stress_modifier} (formula: {r_stress_level} - 3)")
            if reactor_targeted_status == StatusType.SYMPATHY:
                r_status_value = r_sheet.sympathy[self.proactor.sheet.name].value
            else:
                r_status_value = r_sheet.statuses[reactor_targeted_status].value
            r_status_modifier = calculate_status_modifier(r_status_value)
            
            # DEBUG: Reactor status modifier calculation
            print(f"DEBUG: Reactor status value for {reactor_targeted_status.value}: {r_status_value}")
            print(f"DEBUG: Reactor status modifier calculated: {r_status_modifier}")

            r_shift_polarity = reactor_factors.get('shift_polarity')
            if r_shift_polarity in (None, "", []):
                r_sympathy_modifier = 0
                print("Warning: Missing reactor shift_polarity; skipping sympathy modifier this turn.")
            else:
                r_sympathy_modifier = calculate_sympathy_modifier(self.reactor, self.proactor, r_shift_polarity)
                if r_sympathy_modifier != 0:
                    r_sympathy_description = get_sympathy_modifier_description(
                        self.reactor.sheet.name, self.proactor.sheet.name,
                        self.reactor.sheet.get_sympathy(self.proactor.sheet.name),
                        r_shift_polarity, r_sympathy_modifier
                    )
                    print(f"      * Reactor Sympathy Modifier: {r_sympathy_description}")

            try:
                r_s_trait_enum = SFactorType[r_s_trait_name]
            except KeyError:
                r_s_trait_enum = SFactorType.STURDINESS
            
            # Use pre-calculated success from step 4 if available
            if 'success_calculation' in self.reactor_action and 'total' in self.reactor_action['success_calculation']:
                reactor_success = self.reactor_action['success_calculation']['total']
                reactor_calc_str = self.reactor_action['success_calculation'].get('calc_str', 'Pre-calculated')
                print(f"DEBUG: Using pre-calculated reactor success: {reactor_success}")
            else:
                reactor_unified_result = calculate_unified_result(
                    actor=self.reactor,
                    s_trait=r_s_trait_enum,
                    skill_name=r_skill_name,
                    target_actor=self.proactor,
                    shift_polarity=r_shift_polarity,
                    targeted_status=reactor_targeted_status,
                    supplement_val=r_supplement_val,
                    serendipity_override=r_serendipity,
                    stress_level_override=r_stress_level
                )
                reactor_success = reactor_unified_result['final_result']
                reactor_calc_str = format_calculation_display(reactor_unified_result)
                print(f"DEBUG: Calculated new reactor success: {reactor_success}")

            success_diff = proactor_success - reactor_success

            # Store original status values for both actors based on their respective targeted statuses
            if proactor_targeted_status == StatusType.SYMPATHY:
                original_proactor_status = self.proactor.sheet.sympathy[self.reactor.sheet.name].value
            else:
                original_proactor_status = self.proactor.sheet.statuses[proactor_targeted_status].value
                
            if reactor_targeted_status == StatusType.SYMPATHY:
                original_reactor_status = self.reactor.sheet.sympathy[self.proactor.sheet.name].value
            else:
                original_reactor_status = self.reactor.sheet.statuses[reactor_targeted_status].value

            base_shift = abs(success_diff)
            def _to_numeric_polarity(val):
                if isinstance(val, str):
                    v = val.strip().lower()
                    if v == 'additive':
                        return 1
                    if v == 'subtractive':
                        return -1
                try:
                    n = int(val)
                    return 1 if n > 0 else (-1 if n < 0 else 0)
                except Exception:
                    return 0

            def _infer_winner_polarity_from_text(text: str, status_to_shift: str) -> int:
                tl = (text or '').lower()
                additive_markers = [
                    'help', 'heal', 'comfort', 'reassure', 'encourage', 'support', 'protect',
                    'save', 'give', 'share', 'apologize', 'thank', 'compliment', 'praise'
                ]
                subtractive_markers = [
                    'attack', 'hit', 'punch', 'kick', 'stab', 'shoot', 'hurt', 'harm', 'threaten',
                    'intimidate', 'insult', 'mock', 'steal', 'break', 'destroy', 'kill', 'yank',
                    'grab', 'clamp', 'slam', 'choke'
                ]
                sts = str(status_to_shift or '').strip().upper()
                if sts == "SYMPATHY":
                    if any(w in tl for w in subtractive_markers):
                        return -1
                    if any(w in tl for w in additive_markers):
                        return 1
                    return 1
                if any(w in tl for w in subtractive_markers):
                    return -1
                if any(w in tl for w in additive_markers):
                    return 1
                return -1

            shift_multiplier = 0.5 if proactor_factors.get("shift_type") == "Temporary" else 1.0
            shift_magnitude = round_half_away_from_zero(base_shift * shift_multiplier)

            p_intended = _to_numeric_polarity(proactor_factors.get('shift_polarity'))
            r_intended = _to_numeric_polarity(reactor_factors.get('shift_polarity'))

            # If the winner's polarity is missing, infer it from the winner's action text so Step 5 remains authoritative.
            inferred_winner_polarity = 0
            coerced_winner_polarity = False
            try:
                winner_is_proactor = success_diff > 0
                if shift_magnitude != 0:
                    if winner_is_proactor:
                        winner_text = " ".join([
                            str(self.proactor_action.get('action_description') or ''),
                            str(self.proactor_action.get('narrative_description') or ''),
                        ]).strip()
                        inferred_winner_polarity = _infer_winner_polarity_from_text(winner_text, proactor_targeted_status.name)
                        if inferred_winner_polarity != 0 and p_intended == 0:
                            p_intended = inferred_winner_polarity
                        elif inferred_winner_polarity != 0 and p_intended != 0 and inferred_winner_polarity != p_intended:
                            # Coerce clearly contradictory polarity (e.g., hostile action marked Additive)
                            p_intended = inferred_winner_polarity
                            coerced_winner_polarity = True
                    else:
                        winner_text = " ".join([
                            str(self.reactor_action.get('action_description') or ''),
                            str(self.reactor_action.get('narrative_description') or ''),
                        ]).strip()
                        inferred_winner_polarity = _infer_winner_polarity_from_text(winner_text, reactor_targeted_status.name)
                        if inferred_winner_polarity != 0 and r_intended == 0:
                            r_intended = inferred_winner_polarity
                        elif inferred_winner_polarity != 0 and r_intended != 0 and inferred_winner_polarity != r_intended:
                            # Coerce clearly contradictory polarity (e.g., hostile action marked Additive)
                            r_intended = inferred_winner_polarity
                            coerced_winner_polarity = True
            except Exception:
                inferred_winner_polarity = 0
                coerced_winner_polarity = False

            # Apply the WINNER's intended polarity only.
            # If the winner's polarity is missing → no shift and a visible calc marker.
            # Check if dialogue metadata indicates no shift should be applied
            dialogue_meta = proactor_factors.get("dialogue_metadata", {})
            should_apply_shift = dialogue_meta.get("apply_shift", True)  # Default True for backward compatibility
            
            action_succeeded = success_diff > 0
            if should_apply_shift and action_succeeded and p_intended != 0:
                final_shift_amount = shift_magnitude * p_intended
                if coerced_winner_polarity is True:
                    shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * coerced_proactor_polarity = {final_shift_amount}"
                elif inferred_winner_polarity != 0 and _to_numeric_polarity(proactor_factors.get('shift_polarity')) == 0:
                    shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * inferred_proactor_polarity = {final_shift_amount}"
                else:
                    shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * proactor_intended_polarity = {final_shift_amount}"
            elif should_apply_shift and (not action_succeeded) and r_intended != 0:
                final_shift_amount = shift_magnitude * r_intended
                if coerced_winner_polarity is True:
                    shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * coerced_reactor_polarity = {final_shift_amount}"
                elif inferred_winner_polarity != 0 and _to_numeric_polarity(reactor_factors.get('shift_polarity')) == 0:
                    shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * inferred_reactor_polarity = {final_shift_amount}"
                else:
                    shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * reactor_intended_polarity = {final_shift_amount}"
            else:
                final_shift_amount = 0
                shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * missing_polarity = 0"

            # Initialize narrator for all outcome scenarios
            from failure_narrative_generator import FailureNarrativeGenerator
            narrator = FailureNarrativeGenerator()
            
            if action_succeeded:
                # Generate narrative for successful contested action
                contest_narrative = narrator.generate_contested_outcome_narrative(
                    self.proactor.sheet.name, self.reactor.sheet.name, "proactor_wins", success_diff
                )
                outcome = contest_narrative
                # Apply shift to reactor using proactor's targeted status (what proactor is trying to affect)
                if proactor_targeted_status == StatusType.SYMPATHY:
                    original_reactor_status = self.reactor.sheet.sympathy[self.proactor.sheet.name].value
                    self.reactor.sheet.update_sympathy(self.proactor.sheet.name, final_shift_amount)
                    new_reactor_status = self.reactor.sheet.sympathy[self.proactor.sheet.name].value
                else:
                    original_reactor_status = self.reactor.sheet.statuses[proactor_targeted_status].value
                    
                    if proactor_factors.get("shift_type") == "Lasting":
                        self.reactor.sheet.apply_lasting_status_shift(proactor_targeted_status, final_shift_amount)
                        new_reactor_status = self.reactor.sheet.statuses[proactor_targeted_status].value
                    elif proactor_factors.get("shift_type") == "Temporary":
                        unclamped_new_value = original_reactor_status + final_shift_amount
                        self.reactor.sheet.update_status(proactor_targeted_status, final_shift_amount)
                        new_reactor_status = self.reactor.sheet.statuses[proactor_targeted_status].value
                        
                        if proactor_targeted_status != StatusType.SYMPATHY:
                            self.recovery_integrator.recovery_manager.add_temporary_effect(
                                actor_name=self.reactor.sheet.name,
                                status_type=proactor_targeted_status,
                                original_value=original_reactor_status,
                                new_value=unclamped_new_value,
                                source_description=f"Temporary effect from {self.proactor.sheet.name}'s action"
                            )
                    else:
                        self.reactor.sheet.update_status(proactor_targeted_status, final_shift_amount)
                        new_reactor_status = self.reactor.sheet.statuses[proactor_targeted_status].value
            elif success_diff < 0:
                # Generate narrative for reactor winning contested action
                contest_narrative = narrator.generate_contested_outcome_narrative(
                    self.proactor.sheet.name, self.reactor.sheet.name, "reactor_wins", success_diff
                )
                outcome = contest_narrative
                # Apply shift to proactor using reactor's targeted status (what reactor is trying to affect)
                if reactor_targeted_status == StatusType.SYMPATHY:
                    original_proactor_status = self.proactor.sheet.sympathy[self.reactor.sheet.name].value
                    self.proactor.sheet.update_sympathy(self.reactor.sheet.name, final_shift_amount)
                    new_proactor_status = self.proactor.sheet.sympathy[self.reactor.sheet.name].value
                else:
                    original_proactor_status = self.proactor.sheet.statuses[reactor_targeted_status].value
                    
                    if reactor_factors.get("shift_type") == "Lasting":
                        self.proactor.sheet.apply_lasting_status_shift(reactor_targeted_status, final_shift_amount)
                        new_proactor_status = self.proactor.sheet.statuses[reactor_targeted_status].value
                    elif reactor_factors.get("shift_type") == "Temporary":
                        unclamped_new_value = original_proactor_status + final_shift_amount
                        self.proactor.sheet.update_status(reactor_targeted_status, final_shift_amount)
                        new_proactor_status = self.proactor.sheet.statuses[reactor_targeted_status].value
                        
                        if reactor_targeted_status != StatusType.SYMPATHY:
                            self.recovery_integrator.recovery_manager.add_temporary_effect(
                                actor_name=self.proactor.sheet.name,
                                status_type=reactor_targeted_status,
                                original_value=original_proactor_status,
                                new_value=unclamped_new_value,
                                source_description=f"Temporary effect from {self.reactor.sheet.name}'s counter-action"
                            )
                    else:
                        self.proactor.sheet.update_status(reactor_targeted_status, final_shift_amount)
                        new_proactor_status = self.proactor.sheet.statuses[reactor_targeted_status].value
            else:
                # Handle stalemate (success_diff == 0)
                contest_narrative = narrator.generate_contested_outcome_narrative(
                    self.proactor.sheet.name, self.reactor.sheet.name, "stalemate", success_diff
                )
                outcome = contest_narrative
                final_shift_amount = 0
                
            # Build a concrete list of status shifts for reporters and Step 6
            status_shifts: List[Dict[str, Any]] = []
            applied_shift_amount = 0
            try:
                if final_shift_amount != 0:
                    if action_succeeded:
                        # Reactor took the shift on proactor's targeted status
                        shifted_status = proactor_targeted_status.name
                        actual_delta = None
                        try:
                            actual_delta = int(new_reactor_status) - int(original_reactor_status)
                        except Exception:
                            actual_delta = None
                        applied_shift_amount = int(actual_delta) if actual_delta is not None else 0
                        # Always report attempted shifts (even if clamped to no net change) so Step 5/6 stay consistent.
                        status_shifts.append({
                            'actor': self.reactor.sheet.name,
                            'status': shifted_status,
                            'delta': applied_shift_amount,
                            'attempted_delta': final_shift_amount,
                            'original': original_reactor_status,
                            'updated': new_reactor_status,
                            'shift_type': proactor_factors.get('shift_type', 'Temporary'),
                            'clamped': (applied_shift_amount == 0 and int(final_shift_amount) != 0)
                        })
                    else:
                        # Proactor took the shift on reactor's targeted status
                        shifted_status = reactor_targeted_status.name
                        actual_delta = None
                        try:
                            actual_delta = int(new_proactor_status) - int(original_proactor_status)
                        except Exception:
                            actual_delta = None
                        applied_shift_amount = int(actual_delta) if actual_delta is not None else 0
                        # Always report attempted shifts (even if clamped to no net change) so Step 5/6 stay consistent.
                        status_shifts.append({
                            'actor': self.proactor.sheet.name,
                            'status': shifted_status,
                            'delta': applied_shift_amount,
                            'attempted_delta': final_shift_amount,
                            'original': original_proactor_status,
                            'updated': new_proactor_status,
                            'shift_type': reactor_factors.get('shift_type', 'Temporary'),
                            'clamped': (applied_shift_amount == 0 and int(final_shift_amount) != 0)
                        })
            except Exception:
                # Keep running even if a reporting field is missing
                pass

            # Persistent context logging: status/sympathy shifts (best-effort)
            try:
                if status_shifts:
                    store = _get_context_store_safe()
                    if store is not None:
                        session_id, location_id = _get_session_and_location_safe()
                        wt = _get_world_time_safe()
                        pro_name = self.proactor.sheet.name
                        re_name = self.reactor.sheet.name
                        pro_id = _try_resolve_spatial_actor_id_by_name(pro_name) or pro_name
                        re_id = _try_resolve_spatial_actor_id_by_name(re_name) or re_name
                        actor_ids = [pro_id, re_id]
                        event_id = store.log_world_event(
                            session_id=session_id,
                            location_id=location_id,
                            event_type="STATUS_SHIFT",
                            summary=f"Status shifts from exchange: {self.proactor.sheet.name} vs {self.reactor.sheet.name}",
                            importance=8,
                            tags=["status", "shift", "exchange"],
                            payload={
                                "actor_ids": actor_ids,
                                "actor_names": [pro_name, re_name],
                                "proactor": pro_name,
                                "reactor": re_name,
                                "proactor_id": pro_id,
                                "reactor_id": re_id,
                                "status_shifts": status_shifts,
                                "winner": "proactor" if proactor_success > reactor_success else "reactor" if reactor_success > proactor_success else "draw",
                            },
                            world_time=wt
                        )

                        try:
                            if hasattr(store, 'remember'):
                                for aid in actor_ids:
                                    store.remember(
                                        session_id=session_id,
                                        actor_id=str(aid),
                                        memory_type="status_shift",
                                        content=f"Status shifts from exchange: {pro_name} vs {re_name}",
                                        importance=8,
                                        pinned=False,
                                        source_event_id=int(event_id) if event_id is not None else None,
                                        world_time=wt
                                    )
                        except Exception:
                            pass
            except Exception:
                pass

            applied_effects = self._apply_self_inflicted_effects(action_succeeded)

            proactor_results = {
                "action_description": self.proactor_action.get("narrative_description", "No description provided."),
                "success": proactor_success,
                "total": proactor_success,  # Add 'total' field for reporter compatibility
                "calc_str": proactor_calc_str,
                "serendipity": p_serendipity,
                "skill_name": p_skill_name,
                "skill_val": p_skill_val,
                "s_trait_name": p_s_trait_name,
                "s_trait_val": p_s_trait_val,
                "super_name": p_super_name,
                "super_val": p_super_val,
                "supplement_name": proactor_factors.get("supplement"),
                "stress_level": p_stress_level,
                "stress_modifier": p_stress_modifier,
                "status_modifier": p_status_modifier,
                "sympathy_modifier": p_sympathy_modifier,
                "targeted_status": proactor_targeted_status.name,
                "action_description": self.proactor_action.get("action_description", "takes action")
            }

            reactor_results = {
                "action_description": self.reactor_action.get("narrative_description", "No description provided."),
                "success": reactor_success,
                "total": reactor_success,  # Add 'total' field for reporter compatibility
                "calc_str": reactor_calc_str,
                "serendipity": r_serendipity,
                "skill_name": r_skill_name,
                "skill_val": r_skill_val,
                "s_trait_name": r_s_trait_name,
                "s_trait_val": r_s_trait_val,
                "super_name": r_super_name,
                "super_val": r_super_val,
                "supplement_name": reactor_factors.get("supplement"),
                "stress_level": r_stress_level,
                "stress_modifier": r_stress_modifier,
                "status_modifier": r_status_modifier,
                "sympathy_modifier": r_sympathy_modifier,
                "targeted_status": reactor_targeted_status.name,
                "action_description": self.reactor_action.get("action_description", "takes action")
            }

            # Determine winner's original shift polarity for narrative context
            winner_shift_polarity = proactor_factors.get('shift_polarity') if action_succeeded else reactor_factors.get('shift_polarity')
            
            outcome_results = {
                "text": outcome,
                "shift_calc": shift_calc_str,
                "final_shift_amount": final_shift_amount,
                "applied_shift_amount": applied_shift_amount,
                "applied_effects": applied_effects,
                "status_shifts": status_shifts,
                "winner": "proactor" if proactor_success > reactor_success else "reactor" if reactor_success > proactor_success else "draw",
                "original_proactor_status": original_proactor_status,
                "updated_proactor_status": self.proactor.sheet.sympathy[self.reactor.sheet.name].value if (action_succeeded and proactor_targeted_status == StatusType.SYMPATHY) or (not action_succeeded and reactor_targeted_status == StatusType.SYMPATHY) else self.proactor.sheet.statuses[reactor_targeted_status if not action_succeeded else proactor_targeted_status].value,
                "original_reactor_status": original_reactor_status,
                "updated_reactor_status": self.reactor.sheet.sympathy[self.proactor.sheet.name].value if (action_succeeded and proactor_targeted_status == StatusType.SYMPATHY) or (not action_succeeded and reactor_targeted_status == StatusType.SYMPATHY) else self.reactor.sheet.statuses[proactor_targeted_status if action_succeeded else reactor_targeted_status].value,
                "status_shifted": proactor_targeted_status.name if action_succeeded else reactor_targeted_status.name,
                "shift_type": proactor_factors.get("shift_type"),  # Should be determined by LLM interpretation
                "shift_polarity": winner_shift_polarity  # Use winner's original intent, not derived from sign
            }
            
            # Check for death triggers after status changes
            proactor_died = actor_state_filter.check_for_death_triggers(self.proactor)
            reactor_died = actor_state_filter.check_for_death_triggers(self.reactor)

            # Persistent context logging: death (best-effort)
            try:
                if proactor_died or reactor_died:
                    store = _get_context_store_safe()
                    if store is not None:
                        session_id, location_id = _get_session_and_location_safe()
                        wt = _get_world_time_safe()
                        pro_name = self.proactor.sheet.name
                        re_name = self.reactor.sheet.name
                        pro_id = _try_resolve_spatial_actor_id_by_name(pro_name) or pro_name
                        re_id = _try_resolve_spatial_actor_id_by_name(re_name) or re_name
                        dead = []
                        if proactor_died:
                            dead.append(pro_name)
                        if reactor_died:
                            dead.append(re_name)
                        event_id = store.log_world_event(
                            session_id=session_id,
                            location_id=location_id,
                            event_type="DEATH",
                            summary=f"Death occurred: {', '.join(dead)}",
                            importance=10,
                            tags=["death", "combat", "exchange"],
                            payload={
                                "actor_ids": [pro_id, re_id],
                                "actor_names": [pro_name, re_name],
                                "dead": dead,
                                "proactor": pro_name,
                                "reactor": re_name,
                                "proactor_id": pro_id,
                                "reactor_id": re_id,
                            },
                            world_time=wt
                        )

                        try:
                            if hasattr(store, 'remember'):
                                for aid in [pro_id, re_id]:
                                    store.remember(
                                        session_id=session_id,
                                        actor_id=str(aid),
                                        memory_type="death",
                                        content=f"Death occurred: {', '.join(dead)}",
                                        importance=10,
                                        pinned=True,
                                        source_event_id=int(event_id) if event_id is not None else None,
                                        world_time=wt
                                    )
                        except Exception:
                            pass
            except Exception:
                pass
            
            return {
                "proactor_success": proactor_success,
                "reactor_success": reactor_success,
                "winner": "proactor" if proactor_success > reactor_success else "reactor" if reactor_success > proactor_success else "draw",
                "success_difference": proactor_success - reactor_success,
                "proactor_results": proactor_results,
                "reactor_results": reactor_results,
                "outcome_results": outcome_results,
                "outcome_type": "proactor_success" if proactor_success > reactor_success else "reactor_success" if reactor_success > proactor_success else "draw",
                "self_effects_applied": applied_effects,
                "text": outcome,
                "shift_calc": shift_calc_str,
                "final_shift_amount": final_shift_amount,
                "applied_effects": applied_effects,
                "status_shifts": status_shifts,
                "original_proactor_status": original_proactor_status,
                "updated_proactor_status": self.proactor.sheet.sympathy[self.reactor.sheet.name].value if (action_succeeded and proactor_targeted_status == StatusType.SYMPATHY) or (not action_succeeded and reactor_targeted_status == StatusType.SYMPATHY) else self.proactor.sheet.statuses[reactor_targeted_status if not action_succeeded else proactor_targeted_status].value,
                "original_reactor_status": original_reactor_status,
                "updated_reactor_status": self.reactor.sheet.sympathy[self.proactor.sheet.name].value if (action_succeeded and proactor_targeted_status == StatusType.SYMPATHY) or (not action_succeeded and reactor_targeted_status == StatusType.SYMPATHY) else self.reactor.sheet.statuses[proactor_targeted_status if action_succeeded else reactor_targeted_status].value,
                "status_shifted": proactor_targeted_status.name if action_succeeded else reactor_targeted_status.name,
                "shift_type": proactor_factors.get("shift_type"),
                "shift_polarity": winner_shift_polarity  # Use winner's original intent, not derived from sign
            }
        except Exception as e:
            print(f"Error in exchange execution: {e}")
            return {"error": str(e)}

    def _execute_inua_exchange(self) -> Dict[str, Any]:
        """
        Execute exchange against INUA (Inanimate Non-User Actor) with proper S-traits.
        INUA now mirrors contested resolution: success difference, rounding, polarity,
        and status shifts are applied similarly to actor-vs-actor exchanges.
        On success, the object's status (via object_state) is shifted; on failure,
        a damage-polarity shift applies to the proactor.
        """
        print(f"\n🏗️ EXECUTING INUA EXCHANGE")
        
        proactor_factors = self.proactor_action.get("utas_factors", {})
        reactor_factors = self.reactor_action.get("utas_factors", {})
        inua_s_traits = self.reactor_action.get("inua_s_traits", {})
        object_name = self.reactor_action.get('name', 'Object')
        
        p_sheet = self.proactor.sheet
        p_skill_name = proactor_factors.get("skill")
        p_skill_val = p_sheet.skills.get(p_skill_name, 0) if p_skill_name else 0
        
        p_s_trait_name = proactor_factors.get("s_trait_to_use", "STURDINESS")
        try:
            p_s_trait_val = p_sheet.s_factors.get_factor(SFactorType[p_s_trait_name])
        except KeyError:
            p_s_trait_name = "STURDINESS"
            p_s_trait_val = p_sheet.s_factors.get_factor(SFactorType.STURDINESS)
        
        p_super_name = proactor_factors.get("super")
        p_super_val = p_sheet.supers.get(p_super_name, 0) if p_super_name else 0
        p_supplement_val = proactor_factors.get("supplement_val", 0)
        p_serendipity = self.proactor_action.get('success_calculation', {}).get('serendipity', 0)
        p_stress_level = extract_numeric_value(proactor_factors.get("stress_level", 3), default=3, min_val=1, max_val=5)
        p_stress_modifier = p_stress_level - 3
        
        try:
            status_name = proactor_factors.get("status_to_shift", "SPIRIT").upper()
            targeted_status = StatusType[status_name]
        except KeyError:
            targeted_status = StatusType.SPIRIT
        
        p_status_value = p_sheet.statuses[targeted_status].value
        p_status_modifier = calculate_status_modifier(p_status_value)
        
        p_sympathy_modifier = 0
        
        from unified_formula import calculate_unified_result, format_calculation_display
        try:
            p_s_trait_enum = SFactorType[p_s_trait_name]
        except KeyError:
            p_s_trait_enum = SFactorType.STURDINESS
        
        proactor_unified_result = calculate_unified_result(
            actor=self.proactor,
            s_trait=p_s_trait_enum,
            skill_name=p_skill_name,
            target_actor=None,
            shift_polarity=proactor_factors.get('shift_polarity'),
            targeted_status=targeted_status,
            supplement_val=p_supplement_val,
            serendipity_override=p_serendipity,
            stress_level_override=p_stress_level,
            super_name=p_super_name
        )
        proactor_success = proactor_unified_result['final_result']
        proactor_calc_str = format_calculation_display(proactor_unified_result)
        
        inua_primary_trait = inua_s_traits.get('primary_trait', 'STURDINESS')
        inua_primary_value = inua_s_traits.get('primary_value', 3)
        inua_serendipity = inua_s_traits.get('serendipity', 2)
        
        inua_resistance = inua_primary_value + inua_serendipity
        inua_calc_str = f"{inua_primary_value} [{inua_primary_trait}] + {inua_serendipity} [Serendipity]"
        
        print(f"Proactor Success: {proactor_success} = {proactor_calc_str}")
        print(f"INUA Resistance: {inua_resistance} = {inua_calc_str}")
        
        # Compute contested-like outcome against INUA
        success_diff = proactor_success - inua_resistance
        proactor_wins = success_diff > 0

        # Track environmental effects applied (optional feature) and status shifts
        environmental_effects_applied: List[Dict[str, Any]] = []
        status_shifts: List[Dict[str, Any]] = []
        shift_calc_str = None
        # Merge any legacy object_state into the global registry, then load the registry state
        legacy_object_state = self.reactor_action.get('object_state')
        if legacy_object_state:
            merge_object_state(legacy_object_state)
        object_state = get_object_state(object_name)
        # Track commonly reported fields
        shift_type_used = None
        final_shift_amount_used = 0
        status_shifted_used = None
        applied_self_effects = []

        if proactor_wins:
            print(f"✅ SUCCESS: Proactor overcomes INUA resistance ({proactor_success} > {inua_resistance})")
            outcome_description = f"Successfully interacts with the {self.reactor_action.get('name', 'object')}"
            
            # Apply main shift to the OBJECT (INUA), mirroring contested logic with explicit winner intent only
            shift_type = proactor_factors.get('shift_type', 'Temporary')
            def _to_numeric_polarity(val):
                if isinstance(val, str):
                    v = val.strip().lower()
                    if v == 'additive':
                        return 1
                    if v == 'subtractive':
                        return -1
                try:
                    n = int(val)
                    return 1 if n > 0 else (-1 if n < 0 else 0)
                except Exception:
                    return 0
            shift_multiplier = 0.5 if shift_type == 'Temporary' else 1.0
            shift_magnitude = round_half_away_from_zero(abs(success_diff) * shift_multiplier)
            p_intended = _to_numeric_polarity(proactor_factors.get('shift_polarity'))
            if p_intended != 0:
                final_shift_amount = shift_magnitude * p_intended
                shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * proactor_intended_polarity = {final_shift_amount}"
            else:
                final_shift_amount = 0
                shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * missing_polarity = 0"

            # Determine targeted status for object (INUA) and update object_state
            try:
                tgt_status_name = proactor_factors.get('status_to_shift', 'STAMINA').upper()
            except Exception:
                tgt_status_name = 'STAMINA'
            original_val = int(get_obj_status(object_name, tgt_status_name, 3))
            unclamped_new_val = original_val + final_shift_amount
            updated_val = max(0, min(5, unclamped_new_val))
            set_obj_status(object_name, tgt_status_name, updated_val)

            # Persist object state (session-scoped) so reload restores it.
            try:
                if save_registry_for_session is not None:
                    sid, _ = _get_session_and_location_safe()
                    save_registry_for_session(sid)
            except Exception:
                pass

            status_shifts.append({
                'actor': object_name,
                'status': tgt_status_name,
                'delta': final_shift_amount,
                'original': original_val,
                'updated': updated_val,
                'shift_type': shift_type
            })

            # Apply proactor self-effects based on success
            applied_self_effects = self._apply_self_inflicted_effects(action_succeeded=True)
            # Track used fields for standardized reporting
            shift_type_used = shift_type
            final_shift_amount_used = final_shift_amount
            status_shifted_used = tgt_status_name
            # Apply optional environmental consequences on success (to proactor only)
            env = self.reactor_action.get('environmental_consequences') or {}
            on_success_effects = env.get('on_success') or []
            if on_success_effects:
                environmental_effects_applied.extend(
                    self._apply_environmental_effects_to_proactor(on_success_effects, source_prefix="Environmental consequence on success")
                )
            
        else:
            print(f"❌ FAILURE: INUA resistance prevails ({proactor_success} <= {inua_resistance})")
            outcome_description = f"Unable to overcome the {self.reactor_action.get('name', 'object')}'s resistance"
            
            # Apply reactor/object intended polarity only; if missing → no shift
            shift_type = proactor_factors.get('shift_type', 'Temporary')
            def _to_numeric_polarity(val):
                if isinstance(val, str):
                    v = val.strip().lower()
                    if v == 'additive':
                        return 1
                    if v == 'subtractive':
                        return -1
                try:
                    n = int(val)
                    return 1 if n > 0 else (-1 if n < 0 else 0)
                except Exception:
                    return 0
            shift_multiplier = 0.5 if shift_type == 'Temporary' else 1.0
            shift_magnitude = round_half_away_from_zero(abs(success_diff) * shift_multiplier)
            r_intended = _to_numeric_polarity(reactor_factors.get('shift_polarity'))
            if r_intended != 0:
                final_shift_amount = shift_magnitude * r_intended
                shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * reactor_intended_polarity = {final_shift_amount}"
            else:
                final_shift_amount = 0
                shift_calc_str = f"round_half_away_from_zero(abs({success_diff}) * {shift_multiplier}) * missing_polarity = 0"

            # Determine targeted status for proactor and apply
            try:
                tgt_status_name = proactor_factors.get('status_to_shift', 'STAMINA').upper()
                targeted_status = StatusType[tgt_status_name]
            except Exception:
                tgt_status_name = 'STAMINA'
                targeted_status = StatusType.STAMINA

            original_val = self.proactor.sheet.statuses[targeted_status].value
            if shift_type == 'Lasting':
                self.proactor.sheet.apply_lasting_status_shift(targeted_status, final_shift_amount)
                updated_val = self.proactor.sheet.statuses[targeted_status].value
            else:
                unclamped_new_val = original_val + final_shift_amount
                self.proactor.sheet.update_status(targeted_status, final_shift_amount)
                updated_val = self.proactor.sheet.statuses[targeted_status].value
                self.recovery_integrator.recovery_manager.add_temporary_effect(
                    actor_name=self.proactor.sheet.name,
                    status_type=targeted_status,
                    original_value=original_val,
                    new_value=unclamped_new_val,
                    source_description=f"Temporary effect from failed interaction with {object_name}"
                )

            status_shifts.append({
                'actor': self.proactor.sheet.name,
                'status': targeted_status.name,
                'delta': final_shift_amount,
                'original': original_val,
                'updated': updated_val,
                'shift_type': shift_type
            })

            # Persist object state even on failure (other object fields may have changed in earlier steps).
            try:
                if save_registry_for_session is not None:
                    sid, _ = _get_session_and_location_safe()
                    save_registry_for_session(sid)
            except Exception:
                pass

            # Apply proactor self-effects based on failure
            applied_self_effects = self._apply_self_inflicted_effects(action_succeeded=False)
            # Track used fields for standardized reporting
            shift_type_used = shift_type
            final_shift_amount_used = final_shift_amount
            status_shifted_used = tgt_status_name
            
            # Optional: apply environmental consequences on failure (to proactor only)
            # Optional: apply environmental consequences on failure (to proactor only)
            env = self.reactor_action.get('environmental_consequences') or {}
            on_failure_effects = env.get('on_failure') or []
            if on_failure_effects:
                environmental_effects_applied.extend(
                    self._apply_environmental_effects_to_proactor(on_failure_effects, source_prefix="Environmental consequence on failure")
                )
        
        return {
            "proactor_success": proactor_wins,
            "proactor_success_value": proactor_success,
            "inua_resistance": inua_resistance,
            "outcome_description": outcome_description,
            "proactor_calculation": proactor_calc_str,
            "inua_calculation": inua_calc_str,
            "no_repercussions": False,
            "is_inua_exchange": True,
            "environmental_effects_applied": environmental_effects_applied,
            "status_shifts": status_shifts,
            "shift_calc": shift_calc_str,
            "self_effects_applied": applied_self_effects,
            "object_state": get_object_state(object_name),
            # Standardized contested-like fields
            "proactor_successes": proactor_success,
            "reactor_successes": inua_resistance,
            "margin": success_diff,
            "proactor_name": self.proactor.sheet.name,
            "reactor_name": object_name,
            "status_shifted": status_shifted_used,
            "shift_type": shift_type_used,
            "shift_polarity": "Additive" if (final_shift_amount_used or 0) > 0 else "Subtractive"
        }


    def _apply_self_inflicted_effects(self, action_succeeded):
        """Apply self-inflicted effects and return the list of applied effects."""
        self_effects = self.proactor_action.get("self_effects")
        applied_effects = []

        if self_effects:
            effects_to_apply = []
            
            for effect in self_effects:
                condition = effect.get("condition") or effect.get("trigger_condition")
                
                if condition:
                    condition = condition.lower().replace("_", " ")
                
                should_apply = False
                if condition in ["always", "inherent cost"]:
                    should_apply = True
                elif action_succeeded and condition in ["on success", "on action success"]:
                    should_apply = True
                elif not action_succeeded and condition in ["on failure", "on action failure"]:
                    should_apply = True
                
                if should_apply:
                    effects_to_apply.append(effect)
            
            for effect_to_apply in effects_to_apply:
                try:
                    effect = effect_to_apply
                    
                    condition = effect.get("condition") or effect.get("trigger_condition")
                    
                    shift_polarity = effect.get("shift_polarity")
                    if shift_polarity == "Additive":
                        effect_shift_pol = 1
                    elif shift_polarity == "Subtractive":
                        effect_shift_pol = -1
                    else:
                        effect_shift_pol = int(shift_polarity) if shift_polarity else -1
                    
                    # Validate magnitude to avoid NoneType errors
                    # Try multiple field names (LLM might use any of these)
                    raw_mag = effect.get("shift_amount")
                    if raw_mag is None:
                        raw_mag = effect.get("base_magnitude")
                    if raw_mag is None:
                        raw_mag = effect.get("shift_magnitude")
                    
                    if raw_mag is None:
                        # Skip invalid self-effect gracefully
                        print("Warning: Skipping self-effect due to missing shift_amount/base_magnitude/shift_magnitude")
                        continue
                    effect_base_mag = int(raw_mag)
                    
                    effect_shift_type = effect.get("shift_type")
                    effect_multiplier = 0.5 if effect_shift_type == "Temporary" else 1.0
                    
                    status_name = effect.get("target_status") or effect.get("status_to_shift")
                    effect_status_name = status_name.upper() if status_name else "STAMINA"
                    effect_targeted_status = StatusType[effect_status_name]

                    original_status = self.proactor.sheet.statuses[effect_targeted_status].value
                    from narrative_utils import get_status_descriptor
                    original_status_desc = get_status_descriptor(original_status)

                    raw_effect_shift = effect_base_mag * effect_shift_pol * effect_multiplier
                    final_effect_shift = round_half_away_from_zero(raw_effect_shift)
                    
                    if effect_shift_type == "Lasting":
                        self.proactor.sheet.apply_lasting_status_shift(effect_targeted_status, final_effect_shift)
                        updated_status = self.proactor.sheet.statuses[effect_targeted_status].value
                    else:
                        unclamped_self_effect_value = original_status + final_effect_shift
                        self.proactor.sheet.update_status(effect_targeted_status, final_effect_shift, reason=condition)
                        updated_status = self.proactor.sheet.statuses[effect_targeted_status].value
                
                    updated_status_desc = get_status_descriptor(updated_status)
                    
                    if effect_shift_type == "Temporary":
                        self.recovery_integrator.recovery_manager.add_temporary_effect(
                            actor_name=self.proactor.sheet.name,
                            status_type=effect_targeted_status,
                            original_value=original_status,
                            new_value=unclamped_self_effect_value,
                            source_description=f"Self-inflicted temporary effect from action ({condition})"
                        )

                    condition_lower = condition.lower() if condition else ""
                    if condition_lower in ["inherent cost", "always"]:
                        prefix = f"As an inherent cost of the action,"
                    else:
                        prefix = f"Because their action {('succeeded' if action_succeeded else 'failed')},"

                    applied_effects.append({
                        "description": effect.get("description", ""),
                        "status_shifted": effect_targeted_status.name,
                        "original_status": original_status,
                        "original_status_desc": original_status_desc,
                        "updated_status": updated_status,
                        "updated_status_desc": updated_status_desc,
                        "shift_type": effect_shift_type,
                        "shift_polarity": "Additive" if effect_shift_pol > 0 else "Subtractive",
                        "shift_magnitude": abs(final_effect_shift),
                        "trigger_condition": condition,
                        "target_status": effect_targeted_status.name,
                        "polarity": "Additive" if effect_shift_pol > 0 else "Subtractive",
                        "prefix": prefix
                    })
                except Exception as e:
                    print(f"Warning: Could not apply self-inflicted effect due to invalid data: {e}")

        return applied_effects

    def _apply_environmental_effects_to_proactor(self, effects: List[Dict[str, Any]], source_prefix: str = "Environmental consequence") -> List[Dict[str, Any]]:
        """
        Apply a list of environmental effects to the proactor (INUA context). Each effect uses:
        - status: STAMINA/SPIRIT/SUPPLY
        - polarity: Additive/Subtractive or +/-1
        - magnitude or base_magnitude: integer magnitude before temporary/lasting multiplier
        - shift_type: Temporary/Lasting (Temporary uses 0.5 multiplier, rounded half away from zero)
        - description: optional narrative description
        Returns a list of applied effect records for reporting.
        """
        applied: List[Dict[str, Any]] = []
        if not effects:
            return applied

        from narrative_utils import get_status_descriptor

        for eff in effects:
            try:
                status_name = (eff.get('status') or eff.get('status_to_shift') or 'STAMINA').upper()
                targeted_status = StatusType[status_name]

                polarity = eff.get('polarity')
                if polarity == 'Additive':
                    pol = 1
                elif polarity == 'Subtractive':
                    pol = -1
                else:
                    try:
                        pol = int(polarity)
                        if pol == 0:
                            pol = -1
                    except Exception:
                        pol = -1

                raw_mag = eff.get('magnitude')
                if raw_mag is None:
                    raw_mag = eff.get('base_magnitude', 1)
                base_mag = max(0, int(raw_mag))

                shift_type = eff.get('shift_type', 'Temporary')
                mult = 0.5 if shift_type == 'Temporary' else 1.0

                original_val = self.proactor.sheet.statuses[targeted_status].value
                raw_shift = base_mag * pol * mult
                final_shift = round_half_away_from_zero(raw_shift)

                if shift_type == 'Lasting':
                    self.proactor.sheet.apply_lasting_status_shift(targeted_status, final_shift)
                    updated_val = self.proactor.sheet.statuses[targeted_status].value
                else:
                    unclamped_new_val = original_val + final_shift
                    self.proactor.sheet.update_status(targeted_status, final_shift, reason=source_prefix)
                    updated_val = self.proactor.sheet.statuses[targeted_status].value
                    self.recovery_integrator.recovery_manager.add_temporary_effect(
                        actor_name=self.proactor.sheet.name,
                        status_type=targeted_status,
                        original_value=original_val,
                        new_value=unclamped_new_val,
                        source_description=f"{source_prefix}"
                    )

                original_desc = get_status_descriptor(original_val)
                updated_desc = get_status_descriptor(updated_val)
                applied.append({
                    'actor_name': self.proactor.sheet.name,
                    'status_name': targeted_status.name,
                    'shift_type': shift_type,
                    'shift_polarity': 'Additive' if final_shift > 0 else 'Subtractive',
                    'shift_value': final_shift,
                    'original_value': original_val,
                    'new_value': updated_val,
                    'original_descriptor': original_desc,
                    'new_descriptor': updated_desc,
                    'description': eff.get('description') or f"{source_prefix}: {targeted_status.name} {'+' if final_shift>0 else ''}{final_shift}"
                })
            except Exception as e:
                print(f"Warning: Could not apply environmental effect due to invalid data: {e}")
                continue

        return applied
    
    def process_witness_reactions(self, witnesses: List[Actor], scene_description: str, exchange_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Process witness reactions to the exchange outcome.
        
        Args:
            witnesses: List of NPCs who witnessed the exchange
            scene_description: Current scene description
            exchange_result: The result dictionary from execute()
            
        Returns:
            List of reaction dictionaries
        """
        if not witnesses:
            return []
        
        # Determine event type and severity
        winner = exchange_result.get('winner')
        final_shift = abs(exchange_result.get('final_shift_amount', 0))
        status_shifted = exchange_result.get('status_shifted', '')
        
        # Determine event type
        event_type = "violence"
        if status_shifted == 'STAMINA' and final_shift >= 3:
            event_type = "murder"
        elif status_shifted == 'SUPPLY':
            event_type = "theft"
        elif status_shifted == 'SPIRIT' and final_shift >= 2:
            event_type = "threat"
        
        # Process reactions
        reactions = witness_system.process_witness_reactions(
            event_type=event_type,
            perpetrator=self.proactor if winner == 'proactor' else self.reactor,
            victim=self.reactor if winner == 'proactor' else self.proactor,
            witnesses=witnesses,
            severity=final_shift,
            scene_description=scene_description
        )
        
        # Apply sympathy shifts from reactions
        for reaction in reactions:
            witness = next((w for w in witnesses if w.sheet.name == reaction['witness']), None)
            if witness:
                # Add masked display label for output (do not change internal keys)
                try:
                    from multi_actor_manager import _safe_display_name
                    reaction['witness_display'] = _safe_display_name(witness)
                except Exception:
                    pass
                witness.sheet.update_sympathy(self.proactor.sheet.name, reaction['sympathy_shifts']['perpetrator'])
                witness.sheet.update_sympathy(self.reactor.sheet.name, reaction['sympathy_shifts']['victim'])
        
        # Display reactions
        if reactions:
            witness_system.display_witness_reactions(reactions)
        
        return reactions


# Backwards compatibility: older modules import `Exchange` from `exchange_system`.
Exchange = ExchangeSystem
