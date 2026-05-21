"""
Intent Availability System - Diegetic Constraint Checking

Prevents "manifestation" where user intents are automatically granted without
realistic world constraints. Classifies intents into three categories:

1. EXIST: Intent can be performed here and now (continues normally)
2. EXIST (NOT HERE): Intent is valid but not at current location (Internal Voice explains why)
   - Example: "I want to call my friend" → Internal Voice: "Oh we left our phone at the diner last night"
3. DOES NOT EXIST: Intent references something that doesn't exist in the world (Internal Voice explains)
   - Example: "I want to call my best friend" → Internal Voice: "It's been years since we last got in contact with John we dont even have his number anymore"

All explanations use INTERNAL VOICE for diegetic, character-driven reasoning.
The system uses LLM intelligence to determine availability and generate appropriate Internal Voice responses.
"""

import random
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from datetime import datetime
from pathlib import Path
from openrouter_config import create_role_client, OpenRouterConfig
from json_utils import extract_and_parse_json


class IntentAvailability(Enum):
    """Classification of intent availability - Diegetic naming"""
    EXIST = "exist"  # Action can be performed here and now
    EXIST_NOT_HERE = "exist_not_here"  # Action is valid but not at current location
    DOES_NOT_EXIST = "does_not_exist"  # Action references something that doesn't exist


class IntentAvailabilitySystem:
    """
    Determines whether a user intent can be pursued now, later, or never.
    
    Prevents manifestation by enforcing realistic world constraints.
    """
    
    def __init__(self, storage_directory: Path):
        self.client = create_role_client("coordination")
        self.logger = logging.getLogger(__name__)
        self.storage_directory = storage_directory
        
        # Track deferred intents (Available Later)
        self.deferred_intents: List[Dict[str, Any]] = []
        
        # Load existing deferred intents
        self._load_deferred_intents()
    
    def evaluate_intent_availability(self,
                                    user_intent: str,
                                    narrative_context: str,
                                    scene_context: str,
                                    established_facts: List[str],
                                    current_time_of_day: Optional[str] = None) -> Dict[str, Any]:
        """
        Evaluate whether a user intent is available now, later, or never.
        
        Args:
            user_intent: The user's stated intent/action
            narrative_context: Recent narrative history
            scene_context: Current scene description
            established_facts: List of established facts about the world/characters
            current_time_of_day: Optional time context (morning, afternoon, evening, night)
            
        Returns:
            Dictionary with availability classification and diegetic explanation
        """
        
        # Step 0: Check for universal actions that are ALWAYS available
        universal_keywords = [
            'check time', 'what time', 'check the time', 'look at time',
            'check watch', 'look at watch', 'check clock', 'look at clock'
        ]
        user_intent_lower = user_intent.lower()
        if any(keyword in user_intent_lower for keyword in universal_keywords):
            return {
                "availability": IntentAvailability.EXIST,
                "reasoning": "Checking the time is a universal action that's always available"
            }
        
        # Step 1: Check if intent is supported by previous narration/context
        support_check = self._check_contextual_support(
            user_intent, narrative_context, scene_context, established_facts
        )
        
        # Step 2: Determine availability based on support
        if support_check["has_support"]:
            # Context supports this intent - choose between NOW or LATER (50/50)
            availability = self._determine_supported_availability(
                user_intent, narrative_context, scene_context, 
                current_time_of_day, support_check
            )
        else:
            # No contextual support - 1/3 chance for NOW, LATER, or NEVER
            availability = self._determine_unsupported_availability(
                user_intent, narrative_context, scene_context,
                established_facts, current_time_of_day
            )
        
        # Step 3: Generate diegetic explanation
        result = self._generate_diegetic_explanation(
            user_intent, availability, support_check, 
            current_time_of_day, scene_context
        )
        
        # Step 4: If Exist Not Here, save the intent for future opportunities
        if result["availability"] == IntentAvailability.EXIST_NOT_HERE:
            self._save_deferred_intent(user_intent, result)
        
        return result
    
    def _check_contextual_support(self,
                                  user_intent: str,
                                  narrative_context: str,
                                  scene_context: str,
                                  established_facts: List[str]) -> Dict[str, Any]:
        """
        Check if the intent is supported by previous narration, scene description, or established facts.
        
        Returns:
            Dictionary with has_support (bool) and supporting_evidence (list)
        """
        prompt = f"""Analyze whether the following user intent is supported by established context.

**User Intent:**
{user_intent}

**CRITICAL: CHECK SCENE DESCRIPTION FIRST (PRIMARY SOURCE):**
{scene_context}

**SCENE ANALYSIS PRIORITY:**
- The SCENE DESCRIPTION is the MOST IMPORTANT source of truth
- If something is mentioned in the scene, it EXISTS and IS AVAILABLE
- Examples: door mentioned → can go through door, alleyway mentioned → can go to alleyway, phone mentioned → can use phone
- DO NOT ignore scene details - they are the current reality

**Secondary Context (Recent Events):**
{narrative_context}

**Established Facts (Background Knowledge):**
{chr(10).join(f"- {fact}" for fact in established_facts)}

**Analysis Task:**
Determine if this intent references something that has been previously established or mentioned.
**PRIORITY ORDER:** Scene Description > Narrative Context > Established Facts

Examples of SUPPORTED intents:
- "I head out to the alleyway" (if the scene description mentions an alleyway) ← SCENE SUPPORTS IT
- "I walk outside" (if the scene mentions doors, exits, or outdoor areas) ← SCENE SUPPORTS IT
- "I use the phone" (if the scene mentions a phone/payphone) ← SCENE SUPPORTS IT
- "I want to visit my childhood friend" (if childhood friend was previously mentioned in narrative/facts)
- "I want to go to the diner" (if a diner was previously mentioned or established)
- "I want to check on my car" (if the character owns a car that was mentioned)
- "I try to hack the computer" (ALWAYS supported - anyone can TRY, even without skills)
- "I attempt to pick the lock" (ALWAYS supported - anyone can TRY, even without skills)

Examples of UNSUPPORTED intents:
- "I talk to the guard" (if NO guard is present in the scene AND no guard mentioned in context)
- "I want to visit my childhood friend" (if NO childhood friend was ever mentioned anywhere)
- "I want to use my magic powers" (if NO magic was established in this world)
- "I want to call my sister" (if NO sister was ever mentioned anywhere)

CRITICAL RULES:
1. **CHECK THE SCENE DESCRIPTION FIRST** - if something is mentioned there, it IS supported! This is the current reality.
2. Scene mentions take ABSOLUTE PRIORITY over everything else
3. LACK OF SKILL does NOT make an intent unsupported - anyone can TRY anything
4. Only mark UNSUPPORTED if the target/object/person doesn't exist in the world
5. Skills affect SUCCESS CHANCE, not AVAILABILITY
6. If the scene says "you see a door" → "I go through the door" IS SUPPORTED
7. If the scene says "narrow alleyway" → "I go to the alleyway" IS SUPPORTED

**Response Format:**
Return a JSON object:

{{
    "has_support": true/false,
    "supporting_evidence": ["list of specific context/facts that support this intent"],
    "confidence": 0.0-1.0,
    "reasoning": "Explanation of why this is/isn't supported"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            if result:
                return result
            else:
                # Default to no support if parsing fails
                return {
                    "has_support": False,
                    "supporting_evidence": [],
                    "confidence": 0.5,
                    "reasoning": "Unable to determine support"
                }
                
        except Exception as e:
            self.logger.error(f"Error checking contextual support: {e}")
            return {
                "has_support": False,
                "supporting_evidence": [],
                "confidence": 0.5,
                "reasoning": "Error in analysis"
            }
    
    def _determine_supported_availability(self,
                                         user_intent: str,
                                         narrative_context: str,
                                         scene_context: str,
                                         current_time_of_day: Optional[str],
                                         support_check: Dict[str, Any]) -> IntentAvailability:
        """
        Determine availability when intent IS supported by context.
        50/50 chance between EXIST and EXIST_NOT_HERE.
        """
        
        # Use LLM to make intelligent decision with 50/50 guidance
        prompt = f"""Determine if this supported intent can be performed HERE or exists but NOT HERE.

**User Intent:**
{user_intent}

**Current Scene:**
{scene_context}

**Time of Day:** {current_time_of_day or "Unknown"}

**Supporting Evidence:**
{chr(10).join(f"- {evidence}" for evidence in support_check.get("supporting_evidence", []))}

**Decision Criteria:**
The intent IS supported by established context, so it EXISTS. The question is WHERE.

Choose EXIST if:
- The action can be performed at the current location
- Required items/people are present in the scene
- No location-based obstacles prevent this

Choose EXIST_NOT_HERE if:
- The action requires a different location (e.g., "call friend" but phone is elsewhere)
- Required items are at a different place (e.g., "use my laptop" but it's at home)
- The target person/object exists but isn't here (e.g., "talk to John" but John is downtown)

**IMPORTANT:** This should be roughly 50/50. Use realistic logic but don't be overly restrictive.

**Response Format:**
Return JSON:

{{
    "availability": "exist" or "exist_not_here",
    "reasoning": "Diegetic explanation for location constraint",
    "location_constraint": "What location constraint prevents this (if exist_not_here)"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7  # Higher temp for more variety
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            if result and "availability" in result:
                return IntentAvailability(result["availability"])
            else:
                # Fallback: true 50/50 random
                return random.choice([IntentAvailability.EXIST, IntentAvailability.EXIST_NOT_HERE])
                
        except Exception as e:
            self.logger.error(f"Error determining supported availability: {e}")
            # Fallback: 50/50 random
            return random.choice([IntentAvailability.EXIST, IntentAvailability.EXIST_NOT_HERE])
    
    def _determine_unsupported_availability(self,
                                           user_intent: str,
                                           narrative_context: str,
                                           scene_context: str,
                                           established_facts: List[str],
                                           current_time_of_day: Optional[str]) -> IntentAvailability:
        """
        Determine availability when intent is NOT supported by context.
        1/3 chance each for EXIST, EXIST_NOT_HERE, DOES_NOT_EXIST.
        """
        
        # Pure 1/3 random selection
        return random.choice([
            IntentAvailability.EXIST,
            IntentAvailability.EXIST_NOT_HERE,
            IntentAvailability.DOES_NOT_EXIST
        ])
    
    def _generate_diegetic_explanation(self,
                                          user_intent: str,
                                          availability: IntentAvailability,
                                          support_check: Dict[str, Any],
                                          current_time_of_day: Optional[str],
                                          scene_context: str) -> Dict[str, Any]:
        """
        Generate INTERNAL VOICE explanation for the availability classification.
        Uses character's internal thoughts, not narrator descriptions.
        """
        
        prompt = f"""Generate an INTERNAL VOICE explanation (character's thoughts) for why this intent has the given availability.

**User Intent:**
{user_intent}

**Availability Classification:**
{availability.value}

**Context Support:**
Has Support: {support_check.get("has_support", False)}
Supporting Evidence: {", ".join(support_check.get("supporting_evidence", []))}

**Current Scene:**
{scene_context}

**Time of Day:** {current_time_of_day or "Unknown"}

**CRITICAL: Use INTERNAL VOICE (first-person thoughts), NOT narrator descriptions**

If EXIST:
- Action continues normally, no internal voice needed
- Return null for internal_voice
- Example: null (action proceeds)

If EXIST_NOT_HERE:
- Use INTERNAL VOICE to explain why action can't be done at current location
- Character realizes what's missing or where something is
- Use "we" voice (character thinking to themselves)
- Example: "Oh we left our phone at the diner last night, we should hurry and get it back before someone takes it."
- Example: "Right, the laptop is back at the apartment. We'll need to head home first."
- Example: "John's probably at his usual spot downtown. We'd need to go there to talk to him."

If DOES_NOT_EXIST:
- Use INTERNAL VOICE to explain why this doesn't exist
- Character recalls memories or realizes the truth
- Use "we" voice and past tense for memories
- Example: "It's been years since we last got in contact with John... he changed his number a few years back."
- Example: "We never had a car. That's just wishful thinking."
- Example: "There's no magic in this world. What am I even thinking?"

**Response Format:**
Return JSON:

{{
    "availability": "{availability.value}",
    "internal_voice": "The character's internal thought (1-2 sentences, 'we' voice) or null if EXIST",
    "action_path": "How to proceed if exist, or null",
    "location_hint": "Where to go if exist_not_here, or null",
    "emotional_tone": "The emotional tone of this thought"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            if result:
                result["availability"] = availability
                result["user_intent"] = user_intent
                result["timestamp"] = datetime.now().isoformat()
                return result
            else:
                # Fallback explanation
                return self._create_fallback_explanation(user_intent, availability)
                
        except Exception as e:
            self.logger.error(f"Error generating diegetic explanation: {e}")
            return self._create_fallback_explanation(user_intent, availability)
    
    def _create_fallback_explanation(self, user_intent: str, availability: IntentAvailability) -> Dict[str, Any]:
        """Create a basic fallback explanation if LLM fails"""
        explanations = {
            IntentAvailability.EXIST: {
                "internal_voice": None,
                "action_path": "Proceed with the action",
                "location_hint": None,
                "emotional_tone": "neutral"
            },
            IntentAvailability.EXIST_NOT_HERE: {
                "internal_voice": "We can't do that here. We'll need to find the right place first.",
                "action_path": None,
                "location_hint": "Find the appropriate location",
                "emotional_tone": "thoughtful"
            },
            IntentAvailability.DOES_NOT_EXIST: {
                "internal_voice": "That's not something we have access to. We'll need to think of something else.",
                "action_path": None,
                "location_hint": None,
                "emotional_tone": "resigned"
            }
        }
        
        result = explanations[availability].copy()
        result["availability"] = availability
        result["user_intent"] = user_intent
        result["timestamp"] = datetime.now().isoformat()
        return result
    
    def _save_deferred_intent(self, user_intent: str, result: Dict[str, Any]):
        """Save an intent that exists but not here for future opportunity narration"""
        deferred = {
            "intent": user_intent,
            "internal_voice": result.get("internal_voice"),
            "location_hint": result.get("location_hint"),
            "deferred_at": datetime.now().isoformat(),
            "triggered": False
        }
        
        self.deferred_intents.append(deferred)
        self._persist_deferred_intents()
        
        self.logger.info(f"Deferred intent saved (exists not here): {user_intent}")
    
    def get_deferred_intents(self, triggered_only: bool = False) -> List[Dict[str, Any]]:
        """
        Get list of deferred intents.
        
        Args:
            triggered_only: If True, only return intents that haven't been triggered yet
            
        Returns:
            List of deferred intent dictionaries
        """
        if triggered_only:
            return [intent for intent in self.deferred_intents if not intent.get("triggered", False)]
        return self.deferred_intents.copy()
    
    def mark_intent_triggered(self, intent_index: int):
        """Mark a deferred intent as triggered (brought up in opportunity narration)"""
        if 0 <= intent_index < len(self.deferred_intents):
            self.deferred_intents[intent_index]["triggered"] = True
            self.deferred_intents[intent_index]["triggered_at"] = datetime.now().isoformat()
            self._persist_deferred_intents()
    
    def get_opportunity_narration_hints(self) -> str:
        """
        Get hints for opportunity narration based on deferred intents.
        
        Returns:
            Formatted string with deferred intents for opportunity narration
        """
        untriggered = self.get_deferred_intents(triggered_only=True)
        
        if not untriggered:
            return ""
        
        hints = ["**DEFERRED INTENTS (Exist Not Here):**"]
        hints.append("These are intents the user wanted to pursue but couldn't at current location.")
        hints.append("Consider weaving these into opportunity narration when user reaches the right location:")
        hints.append("")
        
        for i, intent in enumerate(untriggered):
            hints.append(f"{i+1}. Intent: {intent['intent']}")
            hints.append(f"   Location Hint: {intent.get('location_hint', 'Unknown location')}")
            hints.append(f"   Internal Voice: {intent.get('internal_voice', 'N/A')}")
            hints.append("")
        
        return "\n".join(hints)
    
    def _persist_deferred_intents(self):
        """Save deferred intents to disk"""
        try:
            intents_file = self.storage_directory / "deferred_intents" / "intents.json"
            intents_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(intents_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "deferred_intents": self.deferred_intents,
                    "saved_at": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to persist deferred intents: {e}")
    
    def _load_deferred_intents(self):
        """Load deferred intents from disk"""
        try:
            intents_file = self.storage_directory / "deferred_intents" / "intents.json"
            
            if intents_file.exists():
                with open(intents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.deferred_intents = data.get("deferred_intents", [])
                    self.logger.info(f"Loaded {len(self.deferred_intents)} deferred intents")
                    
        except Exception as e:
            self.logger.warning(f"Could not load deferred intents: {e}")
