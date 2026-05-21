"""
UTAS Narrative Formula Engine

Implements the exact deterministic formula from UTAS OBJECTIVE.md for turn outcome narratives.
This provides predictable, consistent narrative output based on mechanical calculations.
"""

from typing import Dict, Any, Optional
from narrative_utils import (
    get_status_descriptor,
    N2N_Shift_Magnitude,
    N2N_Status_Modifier_Impact
)


class UTASNarrativeFormula:
    """
    Deterministic narrative formula engine that implements the exact UTAS OBJECTIVE.md specification:
    
    "With PROACTOR ACTION GERUND, [IF Proactor Successes > Reactor Successes THEN 'PROACTOR NAME overcomes 
    REACTOR NAME's REACTOR ACTION GERUND with a' ELSE IF Proactor Successes < Reactor Successes THEN 
    'REACTOR NAME overcomes PROACTOR NAME's PROACTOR ACTION GERUND with a' ELSE 'PROACTOR NAME is neutralized 
    by REACTOR NAME's REACTOR ACTION GERUND with a'] [IF Proactor Successes < Reactor Successes & Shift Polarity = -1 
    THEN "Reverse"] "Numerical-to-Narrative Descriptor Shift" "Affected REACTOR Status Type" Shift causing 
    REACTOR NAME's "Numerical-to-Narrative Descriptor Status Type" to go from "Current Numerical-to-Narrative 
    Descriptor Status Type" to "Updated Numerical-to-Narrative Descriptor Status Type" with a 
    "Numerical-to-Narrative Descriptor Status Type Modifier" "Status Type" "[IF reverse THEN "Boost", OTHERWISE "Penalty"]"."
    """
    
    def __init__(self):
        self.gerund_conversions = {
            'punch': 'punching',
            'hit': 'hitting',
            'strike': 'striking',
            'kick': 'kicking',
            'brandish': 'brandishing',
            'stab': 'stabbing',
            'shoot': 'shooting',
            'fire': 'firing',
            'throw': 'throwing',
            'cast': 'casting',
            
            'dodge': 'dodging',
            'jump': 'jumping',
            'run': 'running',
            'walk': 'walking',
            'leap': 'leaping',
            'roll': 'rolling',
            'dive': 'diving',
            'backflip': 'backflipping',
            'sidestep': 'sidestepping',
            'retreat': 'retreating',
            'advance': 'advancing',
            
            'block': 'blocking',
            'parry': 'parrying',
            'deflect': 'deflecting',
            'guard': 'guarding',
            'shield': 'shielding',
            'evade': 'evading',
            'counter': 'countering',
            
            'shout': 'shouting',
            'yell': 'yelling',
            'intimidate': 'intimidating',
            'persuade': 'persuading',
            'deceive': 'deceiving',
            'charm': 'charming',
            'taunt': 'taunting',
            
            'focus': 'focusing',
            'concentrate': 'concentrating',
            'analyze': 'analyzing',
            'study': 'studying',
            'observe': 'observing',
            'search': 'searching',
            'investigate': 'investigating',
            
            'try': 'trying',
            'attempt': 'attempting',
            'use': 'using',
            'grab': 'grabbing',
            'take': 'taking',
            'give': 'giving',
            'drop': 'dropping',
            'pick up': 'picking up',
            'put down': 'putting down',
            'channel': 'channeling',
        }
    
    def _convert_to_gerund(self, action: str) -> str:
        """
        Convert an action to its gerund form (verb + -ing).
        Only converts the main verb, preserves proper nouns and object phrases.
        
        Args:
            action: The action string to convert
            
        Returns:
            The gerund form of the action
        """
        if not action:
            return "acting"
            
        original_action = action.strip()
        action_lower = action.lower().strip()
        
        if action_lower.endswith('ing'):
            return original_action
        
        if action_lower in self.gerund_conversions:
            return self.gerund_conversions[action_lower]
        
        words = original_action.split()
        if len(words) > 1:
            first_word_lower = words[0].lower()
            
            if first_word_lower.endswith('ing'):
                return original_action
            
            if self._is_safe_to_convert(words[0]):
                if first_word_lower in self.gerund_conversions:
                    return self.gerund_conversions[first_word_lower] + " " + " ".join(words[1:])
                else:
                    first_gerund = self._apply_gerund_rules(first_word_lower)
                    return first_gerund + " " + " ".join(words[1:])
            else:
                return original_action
        
        return self._apply_gerund_rules(action_lower)
    
    def _is_safe_to_convert(self, word: str) -> bool:
        """
        Check if a word is safe to convert to gerund form.
        Prevents conversion of proper nouns, prepositions, and non-verbs.
        
        Args:
            word: The word to check
            
        Returns:
            True if safe to convert, False otherwise
        """
        # Don't convert proper nouns (capitalized words)
        if word[0].isupper():
            return False
        
        non_verbs = {
            'amid', 'among', 'between', 'through', 'across', 'around',
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'by',
            'for', 'with', 'without', 'to', 'from', 'of', 'about', 'over',
            'under', 'above', 'below', 'near', 'far', 'here', 'there',
            'this', 'that', 'these', 'those', 'my', 'your', 'his', 'her',
            'its', 'our', 'their', 'some', 'any', 'all', 'each', 'every'
        }
        
        if word.lower() in non_verbs:
            return False
        
        if word.lower() in self.gerund_conversions:
            return True
        
        word_lower = word.lower()
        if len(word_lower) < 3 or len(word_lower) > 12:
            return False
        
        non_verb_suffixes = ['tion', 'sion', 'ness', 'ment', 'able', 'ible', 'ful', 'less', 'ous', 'ive', 'ly']
        for suffix in non_verb_suffixes:
            if word_lower.endswith(suffix):
                return False
        
        return True
    
    def _apply_gerund_rules(self, word: str) -> str:
        """
        Apply standard English gerund rules to a single word.
        
        Args:
            word: Single word to convert (should be lowercase)
            
        Returns:
            Gerund form of the word
        """
        # Handle common third-person present to gerund conversions first
        # e.g., tries -> trying, approaches -> approaching, attempts -> attempting
        if len(word) >= 4 and word.endswith('ies'):
            # e.g., 'tries' -> 'trying'
            return word[:-3] + 'ying'
        if len(word) >= 4 and word.endswith('es'):
            base = word[:-2]
            # Words ending with ch/sh/x/s/z/o typically drop 'es' before adding 'ing'
            if base.endswith(('ch', 'sh', 'x', 's', 'z', 'o')):
                return base + 'ing'
        if len(word) >= 4 and word.endswith('s') and not word.endswith('ss'):
            # Drop singular 's' (attempts -> attempt) before applying normal rules
            word = word[:-1]
        if word.endswith('e') and not word.endswith('ee'):
            return word[:-1] + 'ing'
        elif word.endswith('ie'):
            return word[:-2] + 'ying'
        elif len(word) >= 3 and word[-1] in 'bdfgklmnprstv' and word[-2] in 'aeiou' and word[-3] not in 'aeiou':
            return word + word[-1] + 'ing'
        else:
            return word + 'ing'
    
    def _get_shift_magnitude_descriptor(self, shift_value: int) -> str:
        """Get the N2N descriptor for a shift magnitude."""
        abs_shift = abs(shift_value)
        
        descriptors = {
            0: "Null",
            1: "Minimal", 
            2: "Subpar",
            3: "Average",
            4: "Extraordinary",
            5: "Superb"
        }
        
        return descriptors.get(abs_shift, "Extraordinary")
    
    def _get_status_modifier_descriptor(self, modifier_value: int) -> str:
        """Get the N2N descriptor for status modifier impact."""
        if modifier_value == 0:
            return "Null"
        elif modifier_value > 0:
            return self._get_shift_magnitude_descriptor(modifier_value)
        else:
            return self._get_shift_magnitude_descriptor(abs(modifier_value)) + " Reverse"

    def _article_for(self, phrase: str) -> str:
        """Return the correct indefinite article (a/an) for a phrase by its leading sound.
        Very lightweight heuristic: checks the first alpha character.
        """
        if not phrase:
            return "a"
        for ch in phrase.strip():
            if ch.isalpha():
                return "an" if ch.lower() in "aeiou" else "a"
        return "a"
    
    def _determine_outcome_phrase(self, proactor_successes: int, reactor_successes: int, 
                                proactor_name: str, reactor_name: str, 
                                proactor_gerund: str, reactor_gerund: str,
                                shift_polarity: int = -1) -> str:
        """
        Determine the exact outcome phrase based on success comparison and shift polarity.
        
        Returns the middle portion of the formula:
        - Subtractive: "PROACTOR overcomes REACTOR's REACTION with a"
        - Additive: "PROACTOR supports REACTOR's REACTION with a"
        - Neutral: "PROACTOR is neutralized by REACTOR's REACTION with a"
        """
        # Choose verb based on shift polarity
        if shift_polarity > 0:  # Additive
            win_verb = "supports"
            lose_verb = "supporting"
        else:  # Subtractive (default)
            win_verb = "overcomes"
            lose_verb = "overcoming"
        
        if proactor_successes > reactor_successes:
            return f"{proactor_name} {win_verb} {reactor_name}'s {reactor_gerund} with a"
        elif proactor_successes < reactor_successes:
            return f"{reactor_name} {reactor_gerund}, {lose_verb} {proactor_name}'s attempt with a"
        else:
            return f"{proactor_name} is neutralized by {reactor_name}'s {reactor_gerund} with a"
    
    def _should_add_reverse(self, proactor_successes: int, reactor_successes: int, shift_polarity: int) -> bool:
        """
        Determine if "Reverse" should be added to the shift description.
        
        Condition: Proactor Successes < Reactor Successes & Shift Polarity = -1
        """
        return proactor_successes < reactor_successes and shift_polarity == -1
    
    def _determine_penalty_or_boost(self, is_reverse: bool) -> str:
        """
        Determine whether to use "Penalty" or "Boost" in the final phrase.
        
        Rule: IF reverse THEN "Boost", OTHERWISE "Penalty"
        """
        return "Boost" if is_reverse else "Penalty"
    
    def _generate_outcome_resolution_llm(self, proactor_successes: int, reactor_successes: int, 
                                        proactor_name: str, reactor_name: str, 
                                        proactor_action: str, reactor_action: str,
                                        affected_status: str = "STAMINA",
                                        proactor_attempt: str = None, reactor_attempt: str = None) -> str:
        """
        Generate dynamic narrative resolution using LLM with formula constraints.
        
        Args:
            proactor_successes: Number of proactor successes
            reactor_successes: Number of reactor successes
            proactor_name: Name of the proactor
            reactor_name: Name of the reactor
            proactor_action: The proactor's action description
            reactor_action: The reactor's action description
            affected_status: The status being affected (STAMINA, SPIRIT, SUPPLY)
            
        Returns:
            LLM-generated outcome resolution with formula guidance
        """
        from openrouter_config import create_role_client, OpenRouterConfig
        
        success_difference = abs(proactor_successes - reactor_successes)
        
        # Determine outcome type for LLM guidance
        if proactor_successes > reactor_successes:
            outcome_type = "proactor_wins"
            winner = proactor_name
            loser = reactor_name
            winning_action = proactor_action
            losing_action = reactor_action
        elif reactor_successes > proactor_successes:
            outcome_type = "reactor_wins"
            winner = reactor_name
            loser = proactor_name
            winning_action = reactor_action
            losing_action = proactor_action
        else:
            outcome_type = "tie"
            winner = None
            loser = None
            winning_action = proactor_action
            losing_action = reactor_action
        
        # Determine victory margin
        if success_difference == 1:
            margin = "narrow"
        elif success_difference <= 3:
            margin = "clear"
        else:
            margin = "overwhelming"
        
        # Build context from attempt narratives if available
        context_section = ""
        if proactor_attempt and reactor_attempt:
            context_section = f"""
**ATTEMPT CONTEXT (USE THESE EXACT DETAILS):**
- {proactor_name}'s Attempt: {proactor_attempt}
- {reactor_name}'s Attempt: {reactor_attempt}

**CRITICAL: Reference the specific actions, tactics, and execution quality from the attempts above.**
"""

        prompt = f"""
Generate a narrative resolution that explains HOW the outcome occurred in this UTAS exchange.
{context_section}
**CRITICAL: WINNER AND LOSER IDENTIFICATION:**
- WINNER: {winner} ({proactor_successes if outcome_type == "proactor_wins" else reactor_successes} successes)
- LOSER: {loser} ({reactor_successes if outcome_type == "proactor_wins" else proactor_successes} successes)
- THE WINNER'S ACTION SUCCEEDS, THE LOSER'S ACTION FAILS OR IS OVERCOME

**FORMULA REQUIREMENTS:**
- ALWAYS put the loser's action first to create logical flow
- Use the specific attempt details from the context above
- Reference the execution quality (struggles/flawless/competent) from attempts
- Include specific tactical elements (weapons, techniques, positioning) from attempts
- Connect the losing action to the winning action causally
- The WINNER ({winner}) must succeed and the LOSER ({loser}) must fail
- Show how {winner}'s superior execution overcomes {loser}'s attempt
- The LOSER ({loser}) takes the status damage, NOT the winner
- Use status-appropriate consequence language
- Match the victory margin intensity

**EXCHANGE DATA:**
- Outcome: {outcome_type}
- Victory Margin: {margin} (difference of {success_difference})
- Affected Status: {affected_status}

**STATUS CONSEQUENCE GUIDELINES:**
- STAMINA: Physical effects (endurance, strength, body)
- SPIRIT: Mental effects (wits, composure, psychological state)
- SUPPLY: Resource effects (provisions, equipment, materials)

**MARGIN INTENSITY:**
- Narrow (1): Close contest, subtle consequences
- Clear (2-3): Decisive victory, noticeable impact
- Overwhelming (4+): Dominant victory, severe consequences

**STRUCTURE:** [Loser's action] + [how it fails against winner's action] + [status-appropriate consequence]

Generate ONLY the resolution sentence (1-2 sentences max). Reference the specific attempt details and execution quality.
"""

        try:
            client = create_role_client("narration")
            model = OpenRouterConfig.get_model_for_role("narration")
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback to deterministic version if LLM fails
            return self._generate_outcome_resolution_fallback(
                proactor_successes, reactor_successes, proactor_name, reactor_name,
                proactor_action, reactor_action, affected_status
            )
    
    def _generate_outcome_resolution_fallback(self, proactor_successes: int, reactor_successes: int, 
                                            proactor_name: str, reactor_name: str, 
                                            proactor_action: str, reactor_action: str,
                                            affected_status: str = "STAMINA") -> str:
        """
        Fallback deterministic resolution for when LLM fails.
        """
        success_difference = abs(proactor_successes - reactor_successes)
        
        # Status-specific consequence phrases
        status_consequences = {
            "STAMINA": {
                "close": "physical endurance wavers",
                "clear": "body weakens under the strain", 
                "overwhelming": "physical strength is severely compromised"
            },
            "SPIRIT": {
                "close": "grasp of their wits loosens",
                "clear": "mental composure crumbles",
                "overwhelming": "psychological state is shattered"
            },
            "SUPPLY": {
                "close": "resources become strained",
                "clear": "provisions are diminished",
                "overwhelming": "supplies are severely depleted"
            }
        }
        
        consequences = status_consequences.get(affected_status, status_consequences["STAMINA"])
        
        if proactor_successes > reactor_successes:
            # Proactor wins - put reactor's (losing) action first
            if success_difference == 1:
                return f"{reactor_name}'s attempts at {reactor_action} are not enough to overcome {proactor_name}'s {proactor_action} as their {consequences['close']}."
            elif success_difference <= 3:
                return f"{reactor_name}'s {reactor_action} proves insufficient against {proactor_name}'s {proactor_action} as their {consequences['clear']}."
            else:
                return f"{reactor_name}'s {reactor_action} completely fails to counter {proactor_name}'s overwhelming {proactor_action} as their {consequences['overwhelming']}."
        elif proactor_successes < reactor_successes:
            # Reactor wins - put proactor's (losing) action first
            if success_difference == 1:
                return f"{proactor_name}'s {proactor_action} falls just short as {reactor_name}'s {reactor_action} narrowly prevails, causing {proactor_name}'s {consequences['close']}."
            elif success_difference <= 3:
                return f"{proactor_name}'s {proactor_action} is effectively countered by {reactor_name}'s {reactor_action}, causing {proactor_name}'s {consequences['clear']}."
            else:
                return f"{proactor_name}'s {proactor_action} is completely overwhelmed by {reactor_name}'s superior {reactor_action}, causing {proactor_name}'s {consequences['overwhelming']}."
        else:
            # Tie - both actions clash equally
            return f"{proactor_name}'s {proactor_action} clashes evenly with {reactor_name}'s {reactor_action}, resulting in a stalemate where neither gains clear advantage."
    
    def generate_turn_outcome_narrative(self, 
                                      proactor_data: Dict[str, Any],
                                      reactor_data: Dict[str, Any], 
                                      outcome_data: Dict[str, Any]) -> str:
        """
        Generate the exact UTAS formula-based turn outcome narrative.
        
        Args:
            proactor_data: Proactor action and success data
            reactor_data: Reactor reaction and success data  
            outcome_data: Turn outcome calculations and status shifts
            
        Returns:
            The exact formula-based narrative string
        """
        # Get original names for shift matching
        proactor_original_name = proactor_data.get('name', 'Proactor')
        reactor_original_name = reactor_data.get('name', 'Reactor')
        
        # Check if actors are UA and convert to "you" for display
        proactor_is_ua = proactor_data.get('is_user_actor', False)
        reactor_is_ua = reactor_data.get('is_user_actor', False)
        
        proactor_name = 'You' if proactor_is_ua else proactor_original_name
        reactor_name = 'you' if reactor_is_ua else reactor_original_name
        
        # Use action_noun for brief gerund, not full narrative_description
        # Fallback chain: action_noun → first 50 chars of action_description → 'acts'/'reacts'
        proactor_action = proactor_data.get('action_noun')
        if not proactor_action:
            action_desc = proactor_data.get('action_description', '')
            proactor_action = action_desc[:50] + '...' if len(action_desc) > 50 else (action_desc or 'acts')
        
        reactor_action = reactor_data.get('action_noun')
        if not reactor_action:
            action_desc = reactor_data.get('action_description', '')
            reactor_action = action_desc[:50] + '...' if len(action_desc) > 50 else (action_desc or 'reacts')
        
        proactor_action = proactor_action.replace('[REACTOR_NAME]', reactor_name)
        reactor_action = reactor_action.replace('[PROACTOR_NAME]', proactor_name)
        
        proactor_successes = outcome_data.get('proactor_successes', 0)
        reactor_successes = outcome_data.get('reactor_successes', 0)
        
        proactor_gerund = self._convert_to_gerund(proactor_action)
        reactor_gerund = self._convert_to_gerund(reactor_action)
        
        if proactor_gerund.startswith("With "):
            proactor_gerund = proactor_gerund[5:]
        if reactor_gerund.startswith("With "):
            reactor_gerund = reactor_gerund[5:]
        
        status_shifts = outcome_data.get('status_shifts', [])
        # Normalize shift schema to support both legacy and new keys
        normalized_shifts = []
        try:
            for s in (status_shifts or []):
                actor_nm = s.get('actor_name') or s.get('actor')
                status_nm = s.get('status_type') or s.get('status') or s.get('status_name')
                shift_val = s.get('shift_value') if s.get('shift_value') is not None else s.get('delta')
                orig_desc = s.get('original_descriptor')
                new_desc = s.get('new_descriptor')
                # Derive descriptors from numeric values if needed
                try:
                    if orig_desc is None:
                        orig_val = s.get('original_value') if s.get('original_value') is not None else s.get('original')
                        if orig_val is not None:
                            orig_desc = get_status_descriptor(int(orig_val))
                    if new_desc is None:
                        new_val = s.get('new_value') if s.get('new_value') is not None else s.get('updated')
                        if new_val is not None:
                            new_desc = get_status_descriptor(int(new_val))
                except Exception:
                    pass
                normalized_shifts.append({
                    'actor_name': actor_nm,
                    'status_type': str(status_nm).upper() if status_nm else None,
                    'shift_value': shift_val if shift_val is not None else 0,
                    'original_descriptor': orig_desc,
                    'new_descriptor': new_desc,
                    'shift_type': s.get('shift_type') or s.get('type') or 'Temporary',
                })
        except Exception:
            normalized_shifts = []
        
        if proactor_successes > reactor_successes:
            affected_actor_name = reactor_name
            # Match using original name, not display name
            damage_shift = next((shift for shift in normalized_shifts 
                               if shift.get('actor_name') == reactor_original_name or shift.get('actor') == reactor_original_name), {})
        elif reactor_successes > proactor_successes:
            affected_actor_name = proactor_name
            # Match using original name, not display name
            damage_shift = next((shift for shift in normalized_shifts 
                               if shift.get('actor_name') == proactor_original_name or shift.get('actor') == proactor_original_name), {})
        else:
            damage_shift = {}
            affected_actor_name = reactor_name
        
        # DEBUG: Print what we found
        print(f"DEBUG FORMULA: proactor_name = '{proactor_name}'")
        print(f"DEBUG FORMULA: reactor_name = '{reactor_name}'")
        print(f"DEBUG FORMULA: damage_shift = {damage_shift}")
        print(f"DEBUG FORMULA: normalized_shifts = {normalized_shifts}")
        
        # Check if we have a valid shift with a non-zero value
        shift_value = damage_shift.get('delta') or damage_shift.get('shift_value', 0) if damage_shift else 0
        print(f"DEBUG FORMULA: shift_value = {shift_value}")
        
        if not damage_shift or shift_value == 0:
            # Produce explicit 'Null Impact' phrasing even when no shift entry exists.
            if proactor_successes == reactor_successes:
                return "Neither side overcomes the other; stalemate with no status change."
            # Determine winner/loser and infer targeted status from UTAS factors
            if proactor_successes > reactor_successes:
                winner_name = proactor_name
                loser_name = reactor_name
                loser_gerund = reactor_gerund
                # Proactor targeted the reactor
                status_to_shift = (
                    (proactor_data.get('utas_factors', {}) or {}).get('status_to_shift')
                ) or 'STATUS'
            else:
                winner_name = reactor_name
                loser_name = proactor_name
                loser_gerund = proactor_gerund
                # Reactor targeted the proactor
                status_to_shift = (
                    (reactor_data.get('utas_factors', {}) or {}).get('status_to_shift')
                ) or 'STATUS'
            status_to_shift = str(status_to_shift).upper()
            # Convert possessive forms for "You"
            loser_possessive = "your" if loser_name.lower() == "you" else f"{loser_name}'s"
            
            # Determine verb based on shift polarity from factors
            try:
                if proactor_successes > reactor_successes:
                    polarity_str = (proactor_data.get('utas_factors', {}) or {}).get('shift_polarity', '')
                else:
                    polarity_str = (reactor_data.get('utas_factors', {}) or {}).get('shift_polarity', '')
                win_verb = "supports" if str(polarity_str).lower() == "additive" else "overcomes"
            except:
                win_verb = "overcomes"
            
            return (
                f"{winner_name} {win_verb} {loser_gerund}, "
                f"with {loser_possessive} {status_to_shift} experiencing a Null Impact."
            )
        
        shift_value = damage_shift.get('shift_value') or damage_shift.get('delta', 0)
        shift_polarity = -1 if shift_value < 0 else 1
        base_formula_polarity = -1
        affected_status = damage_shift.get('status_type', 'STAMINA')
        original_descriptor = damage_shift.get('original_descriptor', 'Average')
        new_descriptor = damage_shift.get('new_descriptor', 'Average')
        status_modifier = damage_shift.get('status_modifier', 0)
        shift_type = damage_shift.get('shift_type', 'Lasting')
        
        outcome_phrase = self._determine_outcome_phrase(
            proactor_successes, reactor_successes, proactor_name, reactor_name,
            proactor_gerund, reactor_gerund, shift_polarity
        )
        
        is_reverse = self._should_add_reverse(proactor_successes, reactor_successes, base_formula_polarity)
        
        shift_magnitude_desc = self._get_shift_magnitude_descriptor(shift_value)
        if is_reverse:
            shift_desc_with_reverse = f"Reverse {shift_magnitude_desc}"
        else:
            shift_desc_with_reverse = shift_magnitude_desc
        
        status_modifier_desc = self._get_shift_magnitude_descriptor(abs(shift_value))
        # Determine penalty/boost based on actual status change direction; handle zero as Null Impact
        if shift_value < 0:
            penalty_or_boost = "Penalty"
        elif shift_value > 0:
            penalty_or_boost = "Boost"
        else:
            penalty_or_boost = "Impact"
        
        # Add temporary/lasting distinction for status changes
        duration_modifier = "temporarily " if shift_type == "Temporary" else ""
        
        # Minimal deterministic phrasing: winner overcomes loser + N2N magnitude and penalty/boost
        if proactor_successes > reactor_successes:
            winner_name = proactor_name
            loser_name = reactor_name
            loser_gerund = reactor_gerund
            try:
                polarity_str = (proactor_data.get('utas_factors', {}) or {}).get('shift_polarity', '')
                win_verb = "supports" if str(polarity_str).lower() == "additive" else "overcomes"
            except Exception:
                win_verb = "overcomes"
        elif reactor_successes > proactor_successes:
            winner_name = reactor_name
            loser_name = proactor_name
            loser_gerund = proactor_gerund
            try:
                polarity_str = (reactor_data.get('utas_factors', {}) or {}).get('shift_polarity', '')
                win_verb = "supports" if str(polarity_str).lower() == "additive" else "overcomes"
            except Exception:
                win_verb = "overcomes"
        else:
            return "Neither side overcomes the other; stalemate with no status change."

        # Compose concise outcome with explicit loser status + magnitude + penalty/boost
        # Convert possessive forms for "You"
        loser_possessive = "your" if loser_name.lower() == "you" else f"{loser_name}'s"
        
        article = self._article_for(shift_magnitude_desc)
        outcome_min = (
            f"{winner_name} {win_verb} {loser_gerund}, "
            f"with {loser_possessive} {affected_status} experiencing {article} {shift_magnitude_desc} {penalty_or_boost}."
        )

        # Append explicit status change line: goes from pre to post with magnitude + penalty/boost
        try:
            # Preserve explicit from→to clause for transparency
            status_change_line = (
                f" This causes {loser_possessive} {affected_status} to go from {original_descriptor} "
                f"to {new_descriptor} with {article} {shift_magnitude_desc} {affected_status} {penalty_or_boost}."
            )
        except Exception:
            status_change_line = ""

        return outcome_min + status_change_line
    
    def test_formula_examples(self):
        """
        Test the formula with the exact examples from UTAS OBJECTIVE.md.
        """
        print("Testing UTAS Formula Examples:")
        print("=" * 50)
        
        proactor_data_1 = {
            'name': 'John',
            'narrative_description': 'punching Mara in the face'
        }
        reactor_data_1 = {
            'name': 'Mara', 
            'narrative_description': 'backflipping away from the punch'
        }
        outcome_data_1 = {
            'proactor_successes': 9,
            'reactor_successes': 7,
            'status_shifts': [{
                'actor_name': 'Mara',
                'shift_value': -1,
                'status_type': 'STAMINA',
                'original_descriptor': 'Average',
                'new_descriptor': 'Subpar',
                'status_modifier': 1
            }]
        }
        
        result_1 = self.generate_turn_outcome_narrative(proactor_data_1, reactor_data_1, outcome_data_1)
        expected_1 = "With punching Mara in the face, John overcomes Mara's backflipping away from the punch with a Reverse Minimal STAMINA Shift. John succeeds while Mara fails to counter effectively. This causes Mara's STAMINA to go from Average to Subpar with a Minimal STAMINA Penalty."
        
        print("Example 1 (Proactor Wins):")
        print(f"Generated: {result_1}")
        print(f"Expected:  {expected_1}")
        print(f"Match: {result_1 == expected_1}")
        print()
        
        outcome_data_2 = {
            'proactor_successes': 7,
            'reactor_successes': 9,
            'status_shifts': [{
                'actor_name': 'Mara',
                'shift_value': 1,
                'status_type': 'STAMINA', 
                'original_descriptor': 'Average',
                'new_descriptor': 'Extraordinary',
                'status_modifier': -1
            }]
        }
        
        result_2 = self.generate_turn_outcome_narrative(proactor_data_1, reactor_data_1, outcome_data_2)
        expected_2 = "With punching Mara in the face, Mara overcomes John's punching Mara in the face with a Reverse Minimal STAMINA Shift causing Mara's STAMINA to go from Average to Extraordinary with a Minimal Reverse STAMINA Boost."
        
        print("Example 2 (Reactor Wins):")
        print(f"Generated: {result_2}")
        print(f"Expected:  {expected_2}")
        print(f"Match: {result_2 == expected_2}")
        print()
        
        outcome_data_3 = {
            'proactor_successes': 8,
            'reactor_successes': 8,
            'status_shifts': [{
                'actor_name': 'Mara',
                'shift_value': 0,
                'status_type': 'STAMINA',
                'original_descriptor': 'Average', 
                'new_descriptor': 'Average',
                'status_modifier': 0
            }]
        }
        
        result_3 = self.generate_turn_outcome_narrative(proactor_data_1, reactor_data_1, outcome_data_3)
        expected_3 = "With punching Mara in the face, John is neutralized by Mara's backflipping away from the punch with a Null STAMINA Shift causing Mara's STAMINA to go from Average to Average with a Null STAMINA Penalty."
        
        print("Example 3 (Tie):")
        print(f"Generated: {result_3}")
        print(f"Expected:  {expected_3}")
        print(f"Match: {result_3 == expected_3}")


if __name__ == "__main__":
    formula = UTASNarrativeFormula()
    formula.test_formula_examples()
