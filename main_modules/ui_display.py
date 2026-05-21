"""Auto-extracted from redesigned_main.py"""

import sys
import os
import time
import re
import json
import random
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

# These imports will need to be adjusted based on what's actually used in each module

def _ua_display_name(actor_obj, ua_actor=None) -> str:
    try:
        nm = getattr(getattr(actor_obj, 'sheet', None), 'name', None)
        if not nm:
            return str(actor_obj)

        try:
            if getattr(getattr(actor_obj, 'sheet', None), 'is_user_actor', False):
                return str(nm)
        except Exception:
            pass

        if ua_actor is not None and actor_obj is ua_actor:
            return str(nm)

        try:
            from stranger_description_system import known_actors_tracker
            if known_actors_tracker is not None and known_actors_tracker.is_name_known(str(nm)):
                return str(nm)
        except Exception:
            pass

        try:
            return str(get_stranger_description(actor_obj, ua_actor=ua_actor))
        except Exception:
            return str(nm)
    except Exception:
        return "someone"




def _transform_agent_data_for_display(action_data, success_data=None, actor_sheet=None):
    """Transform agent/LLM data into format expected by display functions
    
    CRITICAL: Uses actor sheet as authoritative source for all values.
    LLM outputs are only used for selection/identification, not values.
    """
    # Handle case where success_data is embedded in action_data
    if success_data is None and 'success_calculation' in action_data:
        success_data = action_data['success_calculation']
    elif success_data is None:
        success_data = {}
    
    # Extract UTAS factors if available
    utas_factors = action_data.get('utas_factors', {})
    
    # Initialize with LLM selections but actor sheet values
    transformed = {
        # S-Trait data - LLM selects which trait, actor sheet provides value
        's_trait_used': utas_factors.get('s_trait_to_use', success_data.get('s_trait_used', 'Unknown')),
        's_trait_value': 0,  # Will be set from actor sheet or success_data
        # Skill data - LLM selects skill, actor sheet provides value
        'skill_used': 'Unknown',
        'skill_value': 0,  # Will be filled from actor sheet
        
        # Endowment data - LLM selects endowment, actor sheet provides value
        'endowment_used': 'None',
        'endowment_value': 0,  # Will be filled from actor sheet
        
        # Supplement data - calculated from actor sheet equipment
        'supplement_bonus': 0,  # Will be calculated from actor sheet
        
        # Other factors
        'serendipity': success_data.get('serendipity', 0),  # Random, not from sheet
        'stress_level': utas_factors.get('stress_level', success_data.get('stress_level', 1)),
        'stress_penalty': 0,  # Will be calculated
        'status_penalties': 0,  # Will be calculated from actor sheet
        'sympathy_modifier': success_data.get('sympathy_modifier', 0),  # Calculated elsewhere
        'total': success_data.get('total', 0)
    }
    
    # Normalize display labels early to avoid 'N/A' surfacing in output
    # Determine if fallible info-gathering to default S-Trait sensibly
    action_type_lower = str(action_data.get('action_type', '')).lower()
    input_type_lower = str(action_data.get('input_type', '')).lower()
    fallible_subtype = str(action_data.get('fallible_subtype', utas_factors.get('fallible_subtype', ''))).lower()
    # Treat both "mental" (legacy) and "inquiry" (new) as inquiry
    is_info_gathering = fallible_subtype in ['mental', 'inquiry']
    is_fallible_any = action_type_lower == 'fallible_action' or input_type_lower == 'fallible_action' or bool(fallible_subtype)

    # Coerce s_trait_used to a readable, valid name even without actor_sheet
    raw_trait_label = (transformed['s_trait_used'] or '').strip()
    invalid_labels = {'', 'n/a', 'na', 'none', 'unknown', 'null'}
    if raw_trait_label.lower() in invalid_labels:
        # Default to Shadow for info-gathering fallible actions, else keep a safe default
        transformed['s_trait_used'] = 'Shadow' if is_info_gathering or is_fallible_any else 'Shadow'
    else:
        # Title-case for display if not one of canonical caps
        canon = {'shadow': 'Shadow', 'swiftness': 'Swiftness', 'sociability': 'Sociability', 'sturdiness': 'Sturdiness', 'smarts': 'Smarts'}
        transformed['s_trait_used'] = canon.get(raw_trait_label.lower(), raw_trait_label)

    # Coerce skill label for display when missing
    raw_skill_label = (transformed['skill_used'] or '').strip()
    if raw_skill_label.lower() in invalid_labels:
        transformed['skill_used'] = 'none'
    
    # ACTOR SHEET AUTHORITATIVE VALUES
    if actor_sheet:
        from actor_sheet import SFactorType
        
        # Normalize and resolve S-Trait name
        raw_s_trait = (transformed['s_trait_used'] or '').strip()
        s_trait_name = raw_s_trait.lower()
        
        # Provide a sensible default when missing/unknown
        if not s_trait_name or s_trait_name in ('unknown', 'n/a', 'none'):
            s_trait_name = 'shadow'
            transformed['s_trait_used'] = 'Shadow'
        
        # Map to correct SFactorType
        if s_trait_name == 'shadow':
            transformed['s_trait_value'] = actor_sheet.s_factors.get_factor(SFactorType.SHADOW)
            transformed['s_trait_used'] = 'Shadow'
        elif s_trait_name == 'swiftness':
            transformed['s_trait_value'] = actor_sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
            transformed['s_trait_used'] = 'Swiftness'
        elif s_trait_name == 'sociability':
            transformed['s_trait_value'] = actor_sheet.s_factors.get_factor(SFactorType.SOCIABILITY)
            transformed['s_trait_used'] = 'Sociability'
        elif s_trait_name == 'sturdiness':
            transformed['s_trait_value'] = actor_sheet.s_factors.get_factor(SFactorType.STURDINESS)
            transformed['s_trait_used'] = 'Sturdiness'
        elif s_trait_name == 'smarts':
            transformed['s_trait_value'] = actor_sheet.s_factors.get_factor(SFactorType.SMARTS)
            transformed['s_trait_used'] = 'Smarts'
        else:
            # Fallback to provided numeric value if name is unrecognized
            transformed['s_trait_value'] = utas_factors.get('s_trait_value', success_data.get('s_trait_value', 0))
        
        # Get skill value from actor sheet (LLM only selects which skill)
        skill_data = utas_factors.get('skill', success_data.get('skill', {}))
        if isinstance(skill_data, dict):
            skill_name = skill_data.get('name', 'none')
            transformed['skill_used'] = skill_name
            if skill_name.lower() != 'none' and hasattr(actor_sheet, 'skills'):
                transformed['skill_value'] = actor_sheet.skills.get(skill_name, 0)
        
        # Get endowment value from actor sheet (LLM only selects which endowment)
        endowment_data = utas_factors.get('endowment', success_data.get('endowment', {}))
        if isinstance(endowment_data, dict):
            endowment_name = endowment_data.get('name', 'none')
            transformed['endowment_used'] = endowment_name
            if endowment_name.lower() != 'none' and hasattr(actor_sheet, 'endowments'):
                transformed['endowment_value'] = actor_sheet.endowments.get(endowment_name, 0)
        
        # Calculate supplement bonus from actor sheet equipment
        if hasattr(actor_sheet, 'get_total_supplement_bonus'):
            transformed['supplement_bonus'] = actor_sheet.get_total_supplement_bonus()
        elif hasattr(actor_sheet, 'supplements'):
            transformed['supplement_bonus'] = sum(item.supplement_bonus for item in actor_sheet.supplements if hasattr(item, 'supplement_bonus'))
        
        # Calculate status penalties from actor sheet current status
        status_penalty_total = 0
        if hasattr(actor_sheet, 'statuses'):
            for status_type in [StatusType.STAMINA, StatusType.SPIRIT, StatusType.SUPPLY]:
                status = actor_sheet.statuses.get(status_type)
                if status and status.value < status.max_value:
                    # Calculate penalty based on how depleted the status is
                    depletion_ratio = (status.max_value - status.value) / status.max_value
                    if depletion_ratio > 0.5:  # More than 50% depleted
                        status_penalty_total += int(depletion_ratio * 3)  # Up to 3 penalty
        transformed['status_penalties'] = status_penalty_total
    
    else:
        # Fallback to LLM values if no actor sheet provided
        transformed['s_trait_value'] = utas_factors.get('s_trait_value', success_data.get('s_trait_value', 0))
        
        skill_data = utas_factors.get('skill', success_data.get('skill', {}))
        if isinstance(skill_data, dict):
            transformed['skill_used'] = skill_data.get('name', 'None')
            transformed['skill_value'] = skill_data.get('value', 0)
        
        endowment_data = utas_factors.get('endowment', success_data.get('endowment', {}))
        if isinstance(endowment_data, dict):
            transformed['endowment_used'] = endowment_data.get('name', 'None')
            transformed['endowment_value'] = endowment_data.get('value', 0)
        
        supplement_data = utas_factors.get('supplement', success_data.get('supplement', {}))
        if isinstance(supplement_data, dict):
            transformed['supplement_bonus'] = supplement_data.get('value', 0)
    
    # Calculate stress penalty from stress level
    if transformed['stress_penalty'] == 0 and transformed['stress_level'] > 0:
        transformed['stress_penalty'] = max(0, transformed['stress_level'] - 1)

    # Simplified penalty model for FALLIBLE actions:
    # - Stress penalty = 2 * stress_level
    # - Ignore status penalties and sympathy modifier entirely
    # Detection heuristics: action_type/input_type == 'fallible_action' OR presence of fallible_subtype
    is_fallible = False
    try:
        action_type = str(action_data.get('action_type', '')).lower()
        input_type = str(action_data.get('input_type', '')).lower()
        fallible_sub_present = ('fallible_subtype' in action_data) or ('fallible_subtype' in utas_factors)
        if action_type == 'fallible_action' or input_type == 'fallible_action' or fallible_sub_present:
            is_fallible = True
    except Exception:
        is_fallible = False

    if is_fallible:
        transformed['stress_penalty'] = transformed['stress_level'] * 2
        transformed['status_penalties'] = 0
        transformed['sympathy_modifier'] = 0
    
    return transformed



def _display_detailed_calculation_breakdown(raw_data, actor_name, calculation_type="Action", success_data=None, actor_sheet=None):
    """Display detailed step-by-step calculation breakdown with full transparency"""
    # Transform data to expected format using actor sheet as authoritative source
    display_data = _transform_agent_data_for_display(raw_data, success_data, actor_sheet)
    
    print(f"\n{Color.INFO}📊 {calculation_type.upper()} CALCULATION BREAKDOWN - {actor_name}{Color.RESET}")
    print(f"{Color.SYSTEM}{'='*60}{Color.RESET}")
    
    # S-Trait breakdown
    s_trait_name = normalize_sfactor_label(display_data['s_trait_used'])
    s_trait_value = display_data['s_trait_value']
    print(f"{Color.SYSTEM}S-Trait: {s_trait_name} = {s_trait_value}{Color.RESET}")
    
    # Skill breakdown
    skill_name = display_data['skill_used']
    skill_value = display_data['skill_value']
    print(f"{Color.SYSTEM}Skill: {skill_name} = {skill_value}{Color.RESET}")
    
    # Endowment breakdown
    endowment_name = display_data['endowment_used']
    endowment_value = display_data['endowment_value']
    if endowment_value > 0:
        print(f"{Color.SYSTEM}Endowment: {endowment_name} = +{endowment_value}{Color.RESET}")
    else:
        print(f"{Color.SYSTEM}Endowment: None = 0{Color.RESET}")
    
    # Supplement breakdown
    supplement_value = display_data['supplement_bonus']
    if supplement_value > 0:
        print(f"{Color.SYSTEM}Supplements: Equipment Bonus = +{supplement_value}{Color.RESET}")
    else:
        print(f"{Color.SYSTEM}Supplements: No Equipment Bonus = 0{Color.RESET}")
    
    # Serendipity breakdown
    serendipity = display_data['serendipity']
    print(f"{Color.SYSTEM}Serendipity: Random Factor = {serendipity:+d}{Color.RESET}")
    
    # Positive subtotal
    positive_total = s_trait_value + skill_value + endowment_value + supplement_value + serendipity
    print(f"{Color.SUCCESS}Positive Subtotal: {positive_total}{Color.RESET}")
    
    print(f"{Color.SYSTEM}{'-'*30}{Color.RESET}")
    
    # Stress penalty
    stress_level = display_data['stress_level']
    stress_penalty = display_data['stress_penalty']
    print(f"{Color.WARNING}Stress Level: {stress_level} = -{stress_penalty}{Color.RESET}")
    
    # Status penalties
    status_penalties = display_data['status_penalties']
    if status_penalties > 0:
        print(f"{Color.WARNING}Status Penalties: -{status_penalties}{Color.RESET}")
    else:
        print(f"{Color.SYSTEM}Status Penalties: None = 0{Color.RESET}")
    
    # Sympathy modifier
    sympathy_modifier = display_data['sympathy_modifier']
    if sympathy_modifier != 0:
        print(f"{Color.WARNING}Sympathy Modifier: {sympathy_modifier:+d}{Color.RESET}")
    else:
        print(f"{Color.SYSTEM}Sympathy Modifier: None = 0{Color.RESET}")
    
    # Negative subtotal
    negative_total = stress_penalty + status_penalties + abs(min(0, sympathy_modifier))
    print(f"{Color.WARNING}Negative Subtotal: -{negative_total}{Color.RESET}")
    
    print(f"{Color.SYSTEM}{'='*30}{Color.RESET}")
    
    # Final calculation
    final_total = display_data['total']
    calculated_total = positive_total - negative_total
    
    # Show both calculated and reported totals for verification
    print(f"{Color.SUCCESS}CALCULATED TOTAL: {positive_total} - {negative_total} = {calculated_total}{Color.RESET}")
    if final_total != calculated_total:
        print(f"{Color.WARNING}REPORTED TOTAL: {final_total} (differs from calculation){Color.RESET}")
    
    # Success level narration
    from narrative_utils import get_success_level_narration
    success_narration = get_success_level_narration(final_total or calculated_total)
    print(f"{Color.SUCCESS}🎯 Success Level: {success_narration}{Color.RESET}")
    print(f"{Color.SYSTEM}{'='*60}{Color.RESET}")



def _display_exchange_outcome_breakdown(proactor_data, reactor_data, exchange_outcome):
    """Display detailed exchange outcome with comparative analysis"""
    print(f"\n{Color.INFO}⚖️ EXCHANGE OUTCOME ANALYSIS{Color.RESET}")
    print(f"{Color.SYSTEM}{'='*60}{Color.RESET}")
    
    proactor_total = proactor_data.get('total', 0)
    reactor_total = reactor_data.get('total', 0)
    difference = proactor_total - reactor_total
    
    print(f"{Color.INFO}Proactor Total: {proactor_total}{Color.RESET}")
    print(f"{Color.INFO}Reactor Total: {reactor_total}{Color.RESET}")
    print(f"{Color.SYSTEM}Difference: {difference:+d}{Color.RESET}")
    
    if difference > 0:
        print(f"{Color.SUCCESS}🏆 PROACTOR WINS by {difference} points{Color.RESET}")
        outcome_desc = "Proactor Success"
    elif difference < 0:
        print(f"{Color.WARNING}🛡️ REACTOR WINS by {abs(difference)} points{Color.RESET}")
        outcome_desc = "Reactor Success"
    else:
        print(f"{Color.INFO}🤝 TIE - No clear winner{Color.RESET}")
        outcome_desc = "Tied Result"
    
    print(f"{Color.SYSTEM}Outcome Classification: {outcome_desc}{Color.RESET}")
    print(f"{Color.SYSTEM}{'='*60}{Color.RESET}")



def _display_action_processing_steps(action_data, actor_name):
    """Display step-by-step action processing transparency"""
    print(f"\n{Color.INFO}🔍 ACTION PROCESSING STEPS - {actor_name}{Color.RESET}")
    print(f"{Color.SYSTEM}{'='*50}{Color.RESET}")
    
    # Step 1: Action Interpretation
    raw_action = action_data.get('raw_action', 'Unknown')
    print(f"{Color.SYSTEM}Step 1 - Raw Input: '{raw_action}'{Color.RESET}")
    
    # Step 2: Continuity Check
    continuity_result = action_data.get('continuity_check', 'Unknown')
    print(f"{Color.SYSTEM}Step 2 - Continuity: {continuity_result}{Color.RESET}")
    
    # Step 3: Action Classification
    action_type = action_data.get('action_type', 'Unknown')
    print(f"{Color.SYSTEM}Step 3 - Classification: {action_type}{Color.RESET}")
    
    # Step 4: Success Calculation
    print(f"{Color.SYSTEM}Step 4 - Success Calculation: [See breakdown above]{Color.RESET}")
    
    # Step 5: Self-Effects
    self_effects = action_data.get('self_effects', [])
    if self_effects:
        print(f"{Color.SYSTEM}Step 5 - Self-Effects: {len(self_effects)} effect(s) applied{Color.RESET}")
        for i, effect in enumerate(self_effects, 1):
            effect_desc = effect.get('description', 'Unknown effect')
            print(f"{Color.SYSTEM}   {i}. {effect_desc}{Color.RESET}")
    else:
        print(f"{Color.SYSTEM}Step 5 - Self-Effects: None{Color.RESET}")
    
    # Step 6: Narrative Generation
    narrative = action_data.get('narrative_description', 'No narrative generated')
    narrative_preview = narrative[:100] + "..." if len(narrative) > 100 else narrative
    print(f"{Color.SYSTEM}Step 6 - Narrative: {narrative_preview}{Color.RESET}")
    
    print(f"{Color.SYSTEM}{'='*50}{Color.RESET}")




def _display_actor_sheet_simple(actor_sheet, show_outliers: bool = True):
    """
    Display actor sheet with S-trait outliers prominently shown.
    
    S-trait outliers are displayed FIRST as they are the most immediately
    perceivable characteristics of a person.
    """
    ua_actor = None
    actor_obj = None
    try:
        if hasattr(actor_sheet, 'sheet'):
            actor_obj = actor_sheet
            actor_sheet = actor_sheet.sheet
    except Exception:
        actor_obj = None
    try:
        if isinstance(show_outliers, dict):
            ua_actor = show_outliers.get('ua_actor')
            show_outliers = bool(show_outliers.get('show_outliers', True))
    except Exception:
        ua_actor = None
    safe_name = None
    try:
        if actor_obj is not None and ua_actor is not None:
            safe_name = _ua_display_name(actor_obj, ua_actor=ua_actor)
        elif actor_sheet is not None and hasattr(actor_sheet, 'name'):
            nm = getattr(actor_sheet, 'name', None)
            try:
                from stranger_description_system import known_actors_tracker
                if nm and known_actors_tracker is not None and known_actors_tracker.is_name_known(str(nm)):
                    safe_name = str(nm)
            except Exception:
                safe_name = None
            if not safe_name:
                ka = getattr(actor_sheet, 'known_as', None)
                pd = getattr(actor_sheet, 'public_description', None)
                if ka:
                    safe_name = str(ka)
                elif pd:
                    safe_name = str(pd)
    except Exception:
        safe_name = None

    original_name = None
    try:
        if safe_name and actor_sheet is not None and hasattr(actor_sheet, 'name'):
            original_name = actor_sheet.name
            actor_sheet.name = safe_name
    except Exception:
        original_name = None

    # Show S-trait outliers first (most noticeable traits)
    if show_outliers:
        try:
            # Create a temporary actor wrapper for the outlier function
            class ActorWrapper:
                def __init__(self, sheet):
                    self.sheet = sheet
            
            wrapper = ActorWrapper(actor_sheet)
            intro = get_actor_introduction_with_outliers(wrapper)
            
            # Get category
            category = get_actor_category(wrapper)
            category_icon = "⭐" if category == ActorCategory.MNUA else "👤"
            
            print(f"\n{Color.INFO}{category_icon} {intro}{Color.RESET}")
        except Exception:
            pass
    
    # Then show full sheet
    try:
        actor_sheet.display_detailed()
    finally:
        try:
            if original_name is not None:
                actor_sheet.name = original_name
        except Exception:
            pass




def _display_actor_sheet(actor, sheet_data):
    """Display formatted actor sheet information."""
    from narrative_utils import get_narrative_descriptor, get_status_descriptor
    
    print(f"\n{Color.INFO}📋 {_ua_display_name(actor, ua_actor=actor if getattr(getattr(actor, 'sheet', None), 'is_user_actor', False) else None)} - Character Sheet{Color.RESET}")
    print(f"{Color.SYSTEM}Occupation: {sheet_data['occupation']}{Color.RESET}")
    print(f"{Color.SYSTEM}Affiliation: {sheet_data['affiliation']}{Color.RESET}")
    print(f"{Color.SYSTEM}Life Goal: {sheet_data['life_goal']}{Color.RESET}")
    
    print(f"\n{Color.INFO}🎭 Personality{Color.RESET}")
    print(f"{Color.SYSTEM}Internal: {sheet_data['personality_internal']}{Color.RESET}")
    print(f"{Color.SYSTEM}External: {sheet_data['personality_external']}{Color.RESET}")
    
    print(f"\n{Color.INFO}⚡ S-Factors{Color.RESET}")
    for factor_name, value in sheet_data['s_factors'].items():
        descriptor = get_narrative_descriptor(value)
        print(f"{Color.SYSTEM}{factor_name.title()}: {value} ({descriptor}){Color.RESET}")
    
    print(f"\n{Color.INFO}🎯 Skills{Color.RESET}")
    if sheet_data['skills']:
        for skill_name, value in sheet_data['skills'].items():
            descriptor = get_narrative_descriptor(value)
            print(f"{Color.SYSTEM}{skill_name}: {value} ({descriptor}){Color.RESET}")
    else:
        print(f"{Color.SYSTEM}No skills{Color.RESET}")
    
    if sheet_data['endowments']:
        print(f"\n{Color.INFO}✨ Endowment Abilities{Color.RESET}")
        for endowment_name, value in sheet_data['endowments'].items():
            descriptor = get_narrative_descriptor(value)
            print(f"{Color.SYSTEM}{endowment_name}: {value} ({descriptor}){Color.RESET}")
    
    if sheet_data['supplements']:
        print(f"\n{Color.INFO}🎒 Equipment Bonuses{Color.RESET}")
        for item_name, bonus in sheet_data['supplements'].items():
            print(f"{Color.SYSTEM}{item_name}: +{bonus}{Color.RESET}")
    
    print(f"\n{Color.INFO}💪 Status{Color.RESET}")
    for status_name, status_info in sheet_data['statuses'].items():
        value = status_info['value']
        modifier = status_info['modifier']
        descriptor = get_status_descriptor(value)
        modifier_text = f" (modifier: {modifier:+d})" if modifier != 0 else ""
        print(f"{Color.SYSTEM}{status_name.title()}: {value} ({descriptor}){modifier_text}{Color.RESET}")
        
        if status_name == 'supply' and 'money_amount' in status_info:
            print(f"{Color.SYSTEM}  Money: ${status_info['money_amount']}{Color.RESET}")



