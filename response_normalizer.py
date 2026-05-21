"""
Response Normalizer Module

This module provides utilities to normalize LLM responses from different models
into a consistent format expected by the UTAS Exchange system.
"""

from typing import Dict, Any, List, Optional
from color_utils import Color
from severity_validation import SeverityValidator, validate_severity_list

class ResponseNormalizer:
    """
    Normalizes LLM responses to consistent format for Exchange system.
    
    IMPORTANT: This class handles TWO DISTINCT types of responses:
    1. PROACTOR responses (user/NUA actions) - handled by normalize_action_response()
    2. REACTOR responses (defensive reactions) - handled by normalize_reactor_response()
    
    These have different field structures and must be kept separate!
    """
    
    @staticmethod
    def _ensure_narrative_sensory_perspective(narrative: str, actor_name: str, is_user_actor: bool = False) -> str:
        """
        Ensure the narrative follows UA sensory perspective rules.
        
        UNIVERSAL RULE: All narrative outputs must be from the UA's 5 senses perspective.
        - UA actions: "You say...", "You punch..."
        - NUA actions: "You hear [Name] say...", "You see [Name] punch..."
        
        Args:
            narrative: The raw narrative text
            actor_name: The actor's name
            is_user_actor: Whether this actor is the UA (user actor)
            
        Returns:
            Narrative in proper sensory perspective
        """
        if not narrative:
            return narrative
        
        narrative = narrative.strip()
        narrative_lower = narrative.lower()
        actor_first_name = actor_name.split()[0] if actor_name else ""
        
        # Dialogue verbs
        dialogue_verbs = ['says ', 'say ', 'asks ', 'ask ', 'replies ', 'reply ', 'responds ', 
                         'respond ', 'answers ', 'answer ', 'speaks ', 'speak ', 
                         'whispers ', 'whisper ', 'shouts ', 'shout ', 'mutters ', 'mutter ',
                         'growls ', 'growl ', 'yells ', 'yell ', 'calls ', 'call ',
                         'exclaims ', 'exclaim ', 'declares ', 'declare ', 'announces ', 
                         'announce ', 'mentions ', 'mention ', 'states ', 'state ']
        
        # Action verbs
        action_verbs = ['steps ', 'step ', 'moves ', 'move ', 'walks ', 'walk ', 'turns ', 'turn ',
                       'looks ', 'look ', 'glances ', 'glance ', 'nods ', 'nod ', 
                       'shakes ', 'shake ', 'leans ', 'lean ', 'stands ', 'stand ', 
                       'sits ', 'sit ', 'reaches ', 'reach ', 'grabs ', 'grab ', 
                       'takes ', 'take ', 'puts ', 'put ', 'pulls ', 'pull ', 
                       'pushes ', 'push ', 'opens ', 'open ', 'closes ', 'close ', 
                       'sighs ', 'sigh ', 'laughs ', 'laugh ', 'smiles ', 'smile ', 
                       'frowns ', 'frown ', 'punches ', 'punch ', 'kicks ', 'kick ', 
                       'throws ', 'throw ', 'catches ', 'catch ', 'runs ', 'run ', 
                       'jumps ', 'jump ', 'ducks ', 'duck ', 'dodges ', 'dodge ', 
                       'blocks ', 'block ', 'swings ', 'swing ', 'strikes ', 'strike ',
                       'backflips ', 'backflip ', 'flips ', 'flip ', 'spins ', 'spin ', 
                       'rolls ', 'roll ', 'crouches ', 'crouch ', 'kneels ', 'kneel ']
        
        # If already starts with "You " - it's correct
        if narrative_lower.startswith('you '):
            return narrative
        
        # If already starts with "You hear" or "You see" - it's correct  
        if narrative_lower.startswith('you hear ') or narrative_lower.startswith('you see '):
            return narrative
        
        # ===== UA (User Actor) HANDLING =====
        # UA actions should be "You say...", "You punch...", etc.
        if is_user_actor:
            # Check if it starts with the UA's name (e.g., "Marcus says...")
            starts_with_name = (narrative_lower.startswith(actor_name.lower() + ' ') or 
                               narrative_lower.startswith(actor_first_name.lower() + ' '))
            
            if starts_with_name:
                # Extract the rest after the name and replace with "You"
                if narrative_lower.startswith(actor_name.lower() + ' '):
                    rest = narrative[len(actor_name) + 1:]
                else:
                    rest = narrative[len(actor_first_name) + 1:]
                return f"You {rest}"
            
            # Check if it starts with a pronoun - replace with "You"
            for pronoun in ['he ', 'she ', 'they ', 'i ']:
                if narrative_lower.startswith(pronoun):
                    rest = narrative[len(pronoun):]
                    return f"You {rest}"
            
            # Check if it starts directly with a verb - prepend "You"
            for verb in dialogue_verbs + action_verbs:
                if narrative_lower.startswith(verb):
                    return f"You {narrative}"
            
            # Check if it starts with a quote - prepend "You say,"
            if narrative.startswith('"') or narrative.startswith("'") or narrative.startswith('"') or narrative.startswith("'"):
                return f"You say, {narrative}"
            
            # Default for UA: prepend "You"
            return f"You {narrative}"
        
        # ===== NUA (Non-User Actor) HANDLING =====
        # NUA actions should be "You hear [Name] say...", "You see [Name] punch...", etc.
        
        # Check if it starts with the actor's name (e.g., "Diana says...")
        starts_with_name = (narrative_lower.startswith(actor_name.lower() + ' ') or 
                           narrative_lower.startswith(actor_first_name.lower() + ' '))
        
        if starts_with_name:
            # Extract the rest after the name
            if narrative_lower.startswith(actor_name.lower() + ' '):
                rest = narrative[len(actor_name) + 1:]
            else:
                rest = narrative[len(actor_first_name) + 1:]
            
            rest_lower = rest.lower()
            
            # Check if it's a dialogue verb
            for verb in dialogue_verbs:
                if rest_lower.startswith(verb):
                    return f"You hear {actor_name} {rest}"
            
            # Otherwise it's an action verb - use "You see"
            return f"You see {actor_name} {rest}"
        
        # Check if it starts with a pronoun (he/she/they)
        pronoun_map = {'he ': actor_name, 'she ': actor_name, 'they ': actor_name,
                      'his ': actor_name + "'s", 'her ': actor_name + "'s", 'their ': actor_name + "'s"}
        for pronoun, replacement in pronoun_map.items():
            if narrative_lower.startswith(pronoun):
                rest = narrative[len(pronoun):]
                rest_lower = rest.lower()
                # Check if dialogue or action
                for verb in dialogue_verbs:
                    if rest_lower.startswith(verb):
                        return f"You hear {replacement} {rest}"
                return f"You see {replacement} {rest}"
        
        # Check if it starts directly with a verb (missing subject entirely)
        for verb in dialogue_verbs:
            if narrative_lower.startswith(verb):
                return f"You hear {actor_name} {narrative}"
        
        for verb in action_verbs:
            if narrative_lower.startswith(verb):
                return f"You see {actor_name} {narrative}"
        
        # Check if it starts with a quote (dialogue first)
        if narrative.startswith('"') or narrative.startswith("'") or narrative.startswith('"') or narrative.startswith("'"):
            return f"You hear {actor_name} say, {narrative}"
        
        # Default: prepend "You see [Name]" for unknown patterns
        return f"You see {actor_name} {narrative}"
    
    @staticmethod
    def normalize_reactor_response(data: Any, actor_name: str, fallback_description: str = "reacts defensively", is_user_actor: bool = False) -> Dict[str, Any]:
        """
        Normalizes REACTOR interpretation responses with reactor-specific fields.
        
        REACTOR-SPECIFIC FIELDS:
        - reaction_type: Description of reaction type (e.g., "Spirit-based reaction against Supply action")
        - primary_defensive_status: Status being defended (SPIRIT, STAMINA, STANDING, SANITY, STEALTH)
        - stress_level: Reaction difficulty (1-5)
        - secondary_effect: Counter-attack/self-buff indicator ("None" or description)
        - skill, supplement, s_trait_to_use: Standard UTAS factors
        
        Args:
            data: The raw LLM response from reactor interpretation (dict, string, or None)
            actor_name: Name of the reactor for fallback descriptions
            fallback_description: Fallback action description
            is_user_actor: Whether this actor is the UA (for sensory perspective)
            
        Returns:
            Standardized dictionary with REACTOR-SPECIFIC fields for defensive reactions
        """
        if data is None or not isinstance(data, dict):
            error_msg = f"CRITICAL ERROR: Invalid reactor response data type: {type(data)}. Expected dict, got {data}"
            print(f"{Color.SYSTEM}{error_msg}{Color.RESET}")
            raise ValueError(error_msg)
        
        normalized = {
            "action_description": "",
            "narrative_description": "",
            "utas_factors": {}
        }
        
        if "reaction" in data and isinstance(data["reaction"], dict):
            print(f"{Color.SYSTEM}DEBUG: Normalizing nested 'reaction' structure{Color.RESET}")
            source_data = data["reaction"]
        elif "action" in data and isinstance(data["action"], dict):
            print(f"{Color.SYSTEM}DEBUG: Normalizing nested 'action' structure{Color.RESET}")
            source_data = data["action"]
        else:
            source_data = data
        
        normalized["action_description"] = (
            source_data.get("action_description") or 
            source_data.get("action_noun") or 
            f"{actor_name} {fallback_description}"
        )
        
        raw_narrative = (
            source_data.get("narrative_description") or 
            source_data.get("justification") or 
            source_data.get("description") or
            normalized["action_description"]
        )
        
        # Ensure reactor narrative follows UA sensory perspective (UNIVERSAL RULE)
        normalized["narrative_description"] = ResponseNormalizer._ensure_narrative_sensory_perspective(
            raw_narrative, actor_name, is_user_actor
        )
        
        if "utas_factors" in source_data and isinstance(source_data["utas_factors"], dict):
            normalized["utas_factors"] = source_data["utas_factors"]
        else:
            normalized["utas_factors"] = {
                "reactor_reaction_description": source_data.get("reactor_reaction_description"),
                "reactor_reaction_skill": source_data.get("reactor_reaction_skill"),
                "reactor_reaction_s_trait": source_data.get("reactor_reaction_s_trait"),
                "reactor_reaction_super": source_data.get("reactor_reaction_super"),
                "reactor_reaction_supplement": source_data.get("reactor_reaction_supplement"),
                "reactor_primary_defensive_status_type": source_data.get("reactor_primary_defensive_status_type"),
                "has_secondary_effect": source_data.get("has_secondary_effect"),
                "secondary_effect_justification": source_data.get("secondary_effect_justification"),
                "secondary_effect_target": source_data.get("secondary_effect_target"),
                "secondary_effect_target_justification": source_data.get("secondary_effect_target_justification"),
                "secondary_effect_target_status_type": source_data.get("secondary_effect_target_status_type"),
                "secondary_effect_target_status_justification": source_data.get("secondary_effect_target_status_justification"),
                "secondary_effect_shift_polarity_numeric": source_data.get("secondary_effect_shift_polarity_numeric"),
                "secondary_effect_shift_polarity_justification": source_data.get("secondary_effect_shift_polarity_justification"),
                "secondary_effect_shift_type_multiplier": source_data.get("secondary_effect_shift_type_multiplier"),
                "secondary_effect_shift_type_justification": source_data.get("secondary_effect_shift_type_justification"),
                "stress_level": source_data.get("stress_level")
            }

        # Map legacy reactor_* fields to canonical UTAS keys when needed
        uf = normalized.get("utas_factors", {})
        # self_effects is optional; default to [] when missing/None
        try:
            if uf.get('self_effects') is None:
                uf['self_effects'] = []
                normalized['utas_factors']['self_effects'] = []
        except Exception:
            pass
        try:
            legacy_to_canonical = {
                "reactor_reaction_s_trait": "s_trait_to_use",
                "reactor_reaction_skill": "skill",
                "reactor_reaction_endowment": "endowment",
                "reactor_reaction_supplement": "supplement",
            }
            for old_key, new_key in legacy_to_canonical.items():
                if old_key in uf and new_key not in uf:
                    uf[new_key] = uf.get(old_key)
            # Map defensive status type to status_to_shift if missing
            if "status_to_shift" not in uf and uf.get("reactor_primary_defensive_status_type"):
                uf["status_to_shift"] = str(uf.get("reactor_primary_defensive_status_type")).strip().upper()
            normalized["utas_factors"] = uf
        except Exception:
            pass
        
        # Validate critical reactor UTAS fields.
        # IMPORTANT: For gameplay continuity we do NOT hard-fail when the LLM omits fields.
        # Instead we backfill safe defaults so downstream steps (calc + narration) don't
        # collapse into N/A/0 or empty narratives.
        uf = normalized.get("utas_factors", {})
        missing_fields = []
        missing_justifications = []

        # Core required canonical fields
        core_required = [
            "s_trait_to_use",
            "skill",
            "stress_level",
        ]
        for field in core_required:
            if uf.get(field) is None:
                # Allow zero/False; only None indicates missing
                if field not in uf:
                    missing_fields.append(field)

        # Primary intent (validated strictly below but ensure presence)
        if "status_to_shift" not in uf:
            missing_fields.append("status_to_shift")
        if "shift_polarity" not in uf:
            missing_fields.append("shift_polarity")

        # Secondary effects conditional validation
        has_secondary = uf.get("has_secondary_effect")
        if has_secondary is True:
            # When declared, require minimal target info and justification.
            # If incomplete, downgrade to no-secondary-effect instead of throwing.
            if not uf.get("secondary_effect_target"):
                missing_fields.append("secondary_effect_target")
            if not uf.get("secondary_effect_target_status_type"):
                missing_fields.append("secondary_effect_target_status_type")
            if not uf.get("secondary_effect_justification"):
                missing_justifications.append("secondary_effect_justification")
        
        # Normalize mandatory primary resolution intent if present
        uf = normalized.get("utas_factors", {})
        try:
            sts = uf.get("status_to_shift")
            if isinstance(sts, str):
                sts_up = sts.strip().upper()
                if sts_up in ["SPIRIT", "STAMINA", "SUPPLY", "SYMPATHY"]:
                    normalized["utas_factors"]["status_to_shift"] = sts_up
                else:
                    missing_fields.append("status_to_shift")
            else:
                missing_fields.append("status_to_shift")
        except Exception:
            missing_fields.append("status_to_shift")

        try:
            pol = uf.get("shift_polarity")
            if isinstance(pol, str):
                pol_norm = pol.strip().capitalize()
                if pol_norm in ["Additive", "Subtractive"]:
                    normalized["utas_factors"]["shift_polarity"] = pol_norm
                else:
                    missing_fields.append("shift_polarity")
            else:
                missing_fields.append("shift_polarity")
        except Exception:
            missing_fields.append("shift_polarity")

        # Populate display-friendly reactor_* keys for EnhancedReporter from canonical values
        try:
            uf = normalized.get("utas_factors", {})
            # Description fallback
            if "reactor_reaction_description" not in uf:
                desc = normalized.get("action_description") or normalized.get("narrative_description")
                if isinstance(desc, str) and desc.strip():
                    uf["reactor_reaction_description"] = desc.strip()
            # Skill passthrough
            if "reactor_reaction_skill" not in uf and isinstance(uf.get("skill"), dict):
                uf["reactor_reaction_skill"] = uf.get("skill")
            # S-trait label from canonical
            if "reactor_reaction_s_trait" not in uf and uf.get("s_trait_to_use"):
                trait = str(uf.get("s_trait_to_use")).strip().upper()
                trait_map = {"SWIFTNESS":"SWIFTNESS","SOCIABILITY":"SOCIABILITY","STURDINESS":"STURDINESS","SMARTS":"SMARTS","SHADOW":"SHADOW"}
                if trait in trait_map:
                    uf["reactor_reaction_s_trait"] = trait_map[trait]
            # Endowment/supplement passthrough
            if "reactor_reaction_endowment" not in uf and isinstance(uf.get("endowment"), dict):
                uf["reactor_reaction_endowment"] = uf.get("endowment")
            if "reactor_reaction_supplement" not in uf and isinstance(uf.get("supplement"), dict):
                uf["reactor_reaction_supplement"] = uf.get("supplement")
            # Defensive status type from status_to_shift
            if "reactor_primary_defensive_status_type" not in uf and uf.get("status_to_shift"):
                uf["reactor_primary_defensive_status_type"] = uf.get("status_to_shift")
            # Derive has_secondary_effect if absent
            if "has_secondary_effect" not in uf:
                has_secondary = any(uf.get(k) for k in [
                    "secondary_effect_target",
                    "secondary_effect_target_status_type",
                    "secondary_effect_justification",
                    "secondary_effect_shift_polarity_numeric",
                    "secondary_effect_shift_type_multiplier",
                ])
                uf["has_secondary_effect"] = bool(has_secondary)
            normalized["utas_factors"] = uf
        except Exception:
            pass

        if missing_fields:
            # Backfill safe defaults instead of raising.
            try:
                print(
                    f"{Color.SYSTEM}WARNING: Reactor interpretation missing fields {missing_fields}; applying safe defaults to continue.{Color.RESET}"
                )
            except Exception:
                pass

            uf = normalized.get('utas_factors', {})

            # Ensure core canonical fields exist
            try:
                if not uf.get('s_trait_to_use'):
                    uf['s_trait_to_use'] = 'STURDINESS'
            except Exception:
                uf['s_trait_to_use'] = 'STURDINESS'

            try:
                skill = uf.get('skill')
                if not isinstance(skill, dict):
                    uf['skill'] = {'name': 'None', 'value': 0}
                else:
                    skill.setdefault('name', 'None')
                    try:
                        skill['value'] = int(skill.get('value', 0) or 0)
                    except Exception:
                        skill['value'] = 0
                    uf['skill'] = skill
            except Exception:
                uf['skill'] = {'name': 'None', 'value': 0}

            try:
                if uf.get('stress_level') is None:
                    uf['stress_level'] = 3
            except Exception:
                uf['stress_level'] = 3

            # Primary intent defaults
            try:
                if not uf.get('status_to_shift'):
                    uf['status_to_shift'] = 'SPIRIT'
            except Exception:
                uf['status_to_shift'] = 'SPIRIT'

            try:
                if not uf.get('shift_polarity'):
                    # Defensive default
                    uf['shift_polarity'] = 'Subtractive'
            except Exception:
                uf['shift_polarity'] = 'Subtractive'

            # If secondary effects were declared but incomplete, downgrade
            try:
                if uf.get('has_secondary_effect') is True and (
                    (not uf.get('secondary_effect_target')) or (not uf.get('secondary_effect_target_status_type'))
                ):
                    uf['has_secondary_effect'] = False
                    for k in [
                        'secondary_effect_target',
                        'secondary_effect_target_justification',
                        'secondary_effect_target_status_type',
                        'secondary_effect_target_status_justification',
                        'secondary_effect_shift_polarity_numeric',
                        'secondary_effect_shift_polarity_justification',
                        'secondary_effect_shift_type_multiplier',
                        'secondary_effect_shift_type_justification',
                        'secondary_effect_justification',
                    ]:
                        uf.pop(k, None)
            except Exception:
                pass

            normalized['utas_factors'] = uf

        if missing_justifications:
            print(f"{Color.SYSTEM}WARNING: Missing REACTOR UTAS justifications: {missing_justifications}. Consider enhancing prompts for better analysis.{Color.RESET}")

        # Ensure we always have a narrative_description for Step 4 display.
        try:
            nd = normalized.get('narrative_description')
            if not isinstance(nd, str) or not nd.strip():
                ad = normalized.get('action_description')
                normalized['narrative_description'] = (ad if isinstance(ad, str) and ad.strip() else f"You see {actor_name} react.")
        except Exception:
            normalized['narrative_description'] = f"You see {actor_name} react."
        
        print(f"{Color.SYSTEM}DEBUG: Normalized reactor response structure: {list(normalized.keys())}{Color.RESET}")
        return normalized
    
    
    @staticmethod
    def normalize_proactor_action_response(data: Any, actor_name: str, fallback_description: str = "takes action", is_user_actor: bool = False) -> Dict[str, Any]:
        """
        Normalizes any LLM response into the standard action format expected by Exchange system.
        
        Args:
            data: The raw LLM response (dict, string, or None)
            actor_name: Name of the actor for fallback descriptions
            fallback_description: Fallback action description
            is_user_actor: Whether this actor is the UA (for sensory perspective)
            
        Returns:
            Standardized dictionary with action_description, narrative_description, character_motivation, and utas_factors
        """
        if data is None or not isinstance(data, dict):
            print(f"{Color.SYSTEM}DEBUG: Normalizing non-dict response: {type(data)}{Color.RESET}")
            raise ValueError(f"LLM returned invalid response for {actor_name}: {type(data)}. This indicates a real issue that needs to be fixed.")
        
        normalized = {
            "action_description": "",
            "narrative_description": "",
            "character_motivation": "",
            "utas_factors": {}
        }
        
        if "reaction" in data and isinstance(data["reaction"], dict):
            print(f"{Color.SYSTEM}DEBUG: Normalizing nested 'reaction' structure{Color.RESET}")
            source_data = data["reaction"]
        elif "action" in data and isinstance(data["action"], dict):
            print(f"{Color.SYSTEM}DEBUG: Normalizing nested 'action' structure{Color.RESET}")
            source_data = data["action"]
        else:
            source_data = data
        
        normalized["action_description"] = (
            source_data.get("action_description") or 
            source_data.get("action_noun") or 
            f"{actor_name} {fallback_description}"
        )
        
        raw_narrative = (
            source_data.get("narrative_description") or 
            source_data.get("justification") or 
            source_data.get("description") or
            normalized["action_description"]
        )
        
        # Ensure proactor narrative follows UA sensory perspective (UNIVERSAL RULE)
        normalized["narrative_description"] = ResponseNormalizer._ensure_narrative_sensory_perspective(
            raw_narrative, actor_name, is_user_actor
        )
        
        if "utas_factors" in source_data and isinstance(source_data["utas_factors"], dict):
            normalized["utas_factors"] = source_data["utas_factors"]
            if "self_effects" not in normalized["utas_factors"] and "self_effects" in source_data:
                normalized["utas_factors"]["self_effects"] = source_data["self_effects"]
        else:
            # Build utas_factors from flat structure - no defaults, all must be provided by LLM
            normalized["utas_factors"] = {
                "exchange_type": source_data.get("exchange_type"),
                "skill": source_data.get("skill"),
                "s_trait_to_use": source_data.get("s_trait_to_use"),
                "endowment": source_data.get("endowment"),
                "supplement": source_data.get("supplement"),
                "supplement_val": source_data.get("supplement_val"),
                "shift_type": source_data.get("shift_type"),
                "shift_polarity": source_data.get("shift_polarity"),
                "stress_level": source_data.get("stress_level"),
                "status_to_shift": source_data.get("status_to_shift"),
                "self_effects": source_data.get("self_effects")
            }
        
         # Extract optional dialogue metadata (non-blocking)
        if "dialogue_metadata" in source_data:
            normalized["dialogue_metadata"] = source_data["dialogue_metadata"]

        # Validate that critical UTAS fields are present - no defaults allowed
        # The LLM must provide all interpretation fields based on actual analysis
        # FIX BUG #6: skill, endowment, supplement are optional (can be None/0)
        required_fields = [
            "exchange_type",
            "status_to_shift",
            "s_trait_to_use",
            "s_trait_value",
            "stress_level",
            "shift_type",
            "shift_polarity",
        ]
        
        # Optional fields that should exist but can be None/0
        optional_fields = ["skill", "endowment", "supplement"]
        
        justification_fields = [
            "s_trait_justification",
            "skill_justification",
            "stress_justification",
            "shift_type_justification",
            "shift_polarity_justification",
            "self_effects_justification"    
        ]
        
        missing_fields = []
        missing_justifications = []
        
        # Don't check for missing fields yet - normalize first, then validate
        # This prevents duplicate entries in missing_fields
        
        for field in justification_fields:
            if field not in normalized["utas_factors"] or not normalized["utas_factors"][field]:
                missing_justifications.append(field)
        
        def _infer_status_to_shift(exchange_type_val: Any) -> Optional[str]:
            try:
                if isinstance(exchange_type_val, str):
                    et = exchange_type_val.strip().upper()
                    if et in ["SPIRIT", "STAMINA", "SUPPLY", "SYMPATHY"]:
                        return et
                return None
            except Exception:
                return None

        def _infer_shift_type(text: str) -> str:
            tl = (text or '').lower()
            lasting_markers = [
                'permanent', 'permanently', 'forever', 'break', 'ruin', 'destroy', 'shatter',
                'cripple', 'maim', 'scar', 'kill', 'murder'
            ]
            for w in lasting_markers:
                if w in tl:
                    return "Lasting"
            return "Temporary"

        def _infer_shift_polarity(text: str, status_to_shift: str) -> str:
            tl = (text or '').lower()
            additive_markers = [
                'help', 'heal', 'comfort', 'reassure', 'encourage', 'support', 'protect',
                'save', 'give', 'share', 'apologize', 'thank', 'compliment', 'praise'
            ]
            subtractive_markers = [
                'attack', 'hit', 'punch', 'kick', 'stab', 'shoot', 'hurt', 'harm', 'threaten',
                'intimidate', 'insult', 'mock', 'steal', 'break', 'destroy', 'kill'
            ]
            if status_to_shift == "SYMPATHY":
                if any(w in tl for w in subtractive_markers):
                    return "Subtractive"
                if any(w in tl for w in additive_markers):
                    return "Additive"
                return "Additive"
            if any(w in tl for w in subtractive_markers):
                return "Subtractive"
            if any(w in tl for w in additive_markers):
                return "Additive"
            return "Subtractive"

        # Normalize and validate key intent fields
        uf = normalized.get("utas_factors", {})

        # Fill missing status_to_shift from exchange_type when possible
        try:
            if not uf.get("status_to_shift"):
                inferred_sts = _infer_status_to_shift(uf.get("exchange_type"))
                if inferred_sts:
                    normalized["utas_factors"]["status_to_shift"] = inferred_sts
                    uf["status_to_shift"] = inferred_sts
        except Exception:
            pass

        # Fill missing/invalid shift_type and shift_polarity from text when possible
        try:
            combined_text = " ".join([
                str(normalized.get("action_description") or ""),
                str(normalized.get("narrative_description") or ""),
            ]).strip()
        except Exception:
            combined_text = ""

        try:
            st_val = uf.get("shift_type")
            if not isinstance(st_val, str) or st_val not in ("Lasting", "Temporary"):
                inferred = _infer_shift_type(combined_text)
                normalized["utas_factors"]["shift_type"] = inferred
                uf["shift_type"] = inferred
        except Exception:
            pass

        try:
            pol_val = uf.get("shift_polarity")
            if not isinstance(pol_val, str) or pol_val.strip().capitalize() not in ("Additive", "Subtractive"):
                sts_for_pol = str(uf.get("status_to_shift") or "SPIRIT").strip().upper()
                inferred_pol = _infer_shift_polarity(combined_text, sts_for_pol)
                normalized["utas_factors"]["shift_polarity"] = inferred_pol
                uf["shift_polarity"] = inferred_pol
        except Exception:
            pass

        # status_to_shift must be canonical STATUS
        try:
            sts = uf.get("status_to_shift")
            if isinstance(sts, str):
                sts_up = sts.strip().upper()
                if sts_up in ["SPIRIT", "STAMINA", "SUPPLY", "SYMPATHY"]:
                    normalized["utas_factors"]["status_to_shift"] = sts_up
                else:
                    missing_fields.append("status_to_shift")
            else:
                missing_fields.append("status_to_shift")
        except Exception:
            missing_fields.append("status_to_shift")
        
        # shift_polarity must be Additive/Subtractive
        try:
            pol = uf.get("shift_polarity")
            if isinstance(pol, str):
                pol_norm = pol.strip().capitalize()
                if pol_norm in ["Additive", "Subtractive"]:
                    normalized["utas_factors"]["shift_polarity"] = pol_norm
                else:
                    missing_fields.append("shift_polarity")
            else:
                missing_fields.append("shift_polarity")
        except Exception:
            missing_fields.append("shift_polarity")
        
        # s_trait_to_use must be canonical SFactorType
        try:
            trait = uf.get("s_trait_to_use")
            trait_map = {
                "swiftness": "SWIFTNESS",
                "sociability": "SOCIABILITY",
                "sturdiness": "STURDINESS",
                "smarts": "SMARTS",
                "shadow": "SHADOW"
            }
            if isinstance(trait, str):
                key = trait.strip().lower()
                if key in trait_map:
                    normalized["utas_factors"]["s_trait_to_use"] = trait_map[key]
                elif trait.strip().upper() in trait_map.values():
                    normalized["utas_factors"]["s_trait_to_use"] = trait.strip().upper()
                else:
                    missing_fields.append("s_trait_to_use")
            else:
                missing_fields.append("s_trait_to_use")
        except Exception:
            missing_fields.append("s_trait_to_use")
        
        # Numeric validations
        try:
            sv = uf.get("s_trait_value")
            if not isinstance(sv, int) or sv < 0 or sv > 5:
                missing_fields.append("s_trait_value")
        except Exception:
            missing_fields.append("s_trait_value")
        try:
            sl = uf.get("stress_level")
            if not isinstance(sl, int) or sl < 1 or sl > 5:
                missing_fields.append("stress_level")
        except Exception:
            missing_fields.append("stress_level")
        
        # shift_type validation
        try:
            st = uf.get("shift_type")
            if not isinstance(st, str) or st not in ("Lasting", "Temporary"):
                missing_fields.append("shift_type")
        except Exception:
            missing_fields.append("shift_type")
        
        # skill/endowment/supplement must be dicts with name/value ints
        # BUT: endowment, skill, supplement are OPTIONAL - if missing, add default and skip validation
        for fld in ("skill", "endowment", "supplement"):
            val = uf.get(fld)
            if val is None:
                # Missing nested object - default safely.
                normalized["utas_factors"][fld] = {"name": "None", "value": 0}
                continue
            elif not isinstance(val, dict) or "name" not in val or "value" not in val:
                # Malformed nested object - coerce rather than abort.
                normalized["utas_factors"][fld] = {"name": "None", "value": 0}
                continue
            else:
                try:
                    _ = int(val["value"])
                except Exception:
                    # Invalid numeric value - coerce rather than abort.
                    normalized["utas_factors"][fld] = {"name": "None", "value": 0}
                    continue
        
        # self_effects shape normalization and validation (optional)
        se_list = uf.get("self_effects")
        if isinstance(se_list, list) and len(se_list) > 0:
            # Map common legacy keys to canonical ones without introducing defaults
            normalized_effects = []
            for idx, se in enumerate(se_list):
                if not isinstance(se, dict):
                    normalized_effects.append(se)
                    continue
                se_norm = dict(se)
                # Map 'trigger' -> 'condition'
                if 'condition' not in se_norm and 'trigger' in se_norm:
                    se_norm['condition'] = se_norm.get('trigger')
                # Map 'status_shifted' -> 'target_status'
                if 'target_status' not in se_norm and 'status_shifted' in se_norm:
                    se_norm['target_status'] = se_norm.get('status_shifted')
                # Derive 'polarity' from 'shift_magnitude' sign if polarity absent and magnitude provided
                if 'polarity' not in se_norm and 'shift_magnitude' in se_norm:
                    try:
                        mag = int(se_norm.get('shift_magnitude'))
                        if mag > 0:
                            se_norm['polarity'] = 'Additive'
                        elif mag < 0:
                            se_norm['polarity'] = 'Subtractive'
                    except Exception:
                        pass
                normalized_effects.append(se_norm)
            uf['self_effects'] = normalized_effects

            # Validate minimal required fields for each self-effect without defaults
            required_se_min_fields = {"condition", "target_status", "severity"}
            for idx, se in enumerate(uf['self_effects']):
                if not isinstance(se, dict) or not required_se_min_fields.issubset(set(se.keys())):
                    break
                # severity must be int 1-4
                try:
                    sev = int(se.get("severity"))
                    if sev < 1 or sev > 4:
                        break
                except Exception:
                    break
                # Warn (do not abort) if optional fields missing
                if not se.get('polarity'):
                    print(f"{Color.SYSTEM}WARNING: Self-effect missing 'polarity' (effect #{idx+1}); proceeding without default.{Color.RESET}")
                if not se.get('shift_type'):
                    print(f"{Color.SYSTEM}WARNING: Self-effect missing 'shift_type' (effect #{idx+1}); proceeding without default.{Color.RESET}")
        
        # FIX BUG #6: Ensure optional fields exist BEFORE validation (set to None if missing)
        for field in optional_fields:
            if field not in normalized["utas_factors"]:
                normalized["utas_factors"][field] = None
                print(f"{Color.SYSTEM}INFO: Optional field '{field}' not provided by LLM, set to None{Color.RESET}")
        
        # Final validation: Check if required fields are still missing after normalization
        for field in required_fields:
            if field not in normalized["utas_factors"] or normalized["utas_factors"].get(field) is None:
                if field not in missing_fields:  # Avoid duplicates
                    missing_fields.append(field)
        
        if missing_fields:
            error_msg = f"CRITICAL ERROR: Missing/invalid required PROACTOR UTAS fields: {missing_fields}. LLM interpretation incomplete."
            print(f"{Color.SYSTEM}{error_msg}{Color.RESET}")
            raise ValueError(error_msg)
        
        if missing_justifications:
            print(f"{Color.SYSTEM}WARNING: Missing UTAS justifications: {missing_justifications}. Consider enhancing prompts for better analysis.{Color.RESET}")
        
        
        stress_level = normalized["utas_factors"].get("stress_level")
        self_effects = normalized["utas_factors"].get("self_effects")
        
        if isinstance(self_effects, list) and len(self_effects) > 0:
            print(f"{Color.SYSTEM}Applying severity validation to {len(self_effects)} self-effects...{Color.RESET}")
            
            validated_effects = []
            for i, effect in enumerate(self_effects):
                if isinstance(effect, dict):
                    validated_effect = SeverityValidator.validate_self_effect_severity(effect, stress_level)
                    validated_effects.append(validated_effect)
                    
                    original_severity = effect.get("severity")
                    new_severity = validated_effect.get("severity")
                    if original_severity != new_severity:
                        print(f"{Color.YELLOW}Self-effect {i+1}: Severity corrected from {original_severity} to {new_severity}{Color.RESET}")
                else:
                    validated_effects.append(effect)
            
            normalized["utas_factors"]["self_effects"] = validated_effects
            print(f"{Color.SYSTEM}Severity validation complete.{Color.RESET}")
        
        print(f"{Color.SYSTEM}DEBUG: Normalized response structure: {list(normalized.keys())}{Color.RESET}")
        return normalized
    
    # debugging of LLM response issues rather than masking them with defaults
    

