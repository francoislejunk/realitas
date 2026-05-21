#!/usr/bin/env python3
"""
Dynamic Actor Creation System
Handles on-the-fly creation of NUAs and INUAs based on user input mentions.
"""

import re
from typing import Optional, Dict, Any, Tuple
from actors import NonUserActor, InanimateNonUserActor
from agents.creator_agent import CreatorAgent

class DynamicActorDetector:
    """Detects mentions of new actors in user input and classifies them."""
    
    def __init__(self):
        self.inua_patterns = [
            r'\b(?:pick|hack|break|open|disable|bypass|unlock)\s+(?:the\s+)?(\w+(?:\s+\w+)*)',
            r'\b(?:interact|examine|use|manipulate)\s+(?:with\s+)?(?:the\s+)?(\w+(?:\s+\w+)*)',
            r'\b(?:door|lock|terminal|computer|machine|device|system|barrier|gate|wall)\b',
            r'\b(?:try|attempt)\s+to\s+\w+\s+(?:the\s+)?(\w+(?:\s+\w+)*)'
        ]
        
        self.nua_patterns = [
            r'\b(?:talk|speak|converse|approach|ask|tell)\s+(?:to\s+)?(?:the\s+)?(\w+(?:\s+\w+)*)',
            r'\b(?:person|people|guard|merchant|stranger|individual|character)\b',
            r'\b(?:he|she|they|them|him|her)\b',
            r'\b(?:someone|anyone|everybody|nobody)\b'
        ]
        
        self.inua_keywords = {
            'lock', 'door', 'gate', 'terminal', 'computer', 'machine', 'device',
            'system', 'barrier', 'wall', 'chest', 'safe', 'panel', 'console',
            'mechanism', 'trap', 'puzzle', 'keypad', 'scanner', 'sensor',
            'stool', 'chair', 'table', 'desk', 'counter', 'bar', 'shelf',
            'cabinet', 'drawer', 'box', 'container', 'barrel', 'crate'
        }
        
        self.nua_keywords = {
            'guard', 'merchant', 'stranger', 'person', 'people', 'individual',
            'character', 'someone', 'anyone', 'everybody', 'nobody', 'citizen',
            'soldier', 'officer', 'clerk', 'assistant', 'worker', 'employee'
        }

    def detect_existing_actor_reference(self, user_input: str, existing_actors: list) -> Optional[Dict[str, Any]]:
        """
        Detects if user input refers to an existing actor instead of creating a new one.
        Returns existing actor info if found, None otherwise.
        
        Args:
            user_input: The user's input text
            existing_actors: List of currently existing actors
        """
        user_input_lower = user_input.lower()
        
        for actor in existing_actors:
            actor_name = actor.sheet.name.lower()
            actor_words = set(actor_name.split())
            
            if actor_name in user_input_lower:
                return {
                    'existing_actor': actor,
                    'name': actor.sheet.name,
                    'type': 'INUA' if hasattr(actor, 'is_inanimate') and actor.is_inanimate else 'NUA',
                    'reference_type': 'direct_name'
                }
            
            for word in actor_words:
                if len(word) > 2 and word in user_input_lower:
                    word_patterns = [
                        rf'\bthe\s+{re.escape(word)}\b',
                        rf'\b{re.escape(word)}\b',
                        rf'\bto\s+{re.escape(word)}\b',
                        rf'\bat\s+{re.escape(word)}\b',
                        rf'\bwith\s+{re.escape(word)}\b'
                    ]
                    
                    for pattern in word_patterns:
                        if re.search(pattern, user_input_lower):
                            if len(actor_words) > 1:
                                matched_words = []
                                for actor_word in actor_words:
                                    if actor_word in user_input_lower:
                                        matched_words.append(actor_word)
                                
                                # Threshold is based on whether the MATCHED words are distinctive.
                                # If a long/unique word was matched (e.g. "Bartholomew"), 1 match is enough.
                                # If only short/generic words matched (e.g. "guard", "man"), require 2 matches
                                # to avoid falsely claiming "I talk to the guard" references "Security Guard".
                                distinctive_threshold = 1 if any(len(w) > 5 for w in matched_words) else 2
                                if len(matched_words) >= distinctive_threshold:
                                    return {
                                        'existing_actor': actor,
                                        'name': actor.sheet.name,
                                    'type': 'INUA' if hasattr(actor, 'is_inanimate') and actor.is_inanimate else 'NUA',
                                    'reference_type': 'partial_name'
                                }
                            else:
                                return {
                                    'existing_actor': actor,
                                    'name': actor.sheet.name,
                                    'type': 'INUA' if hasattr(actor, 'is_inanimate') and actor.is_inanimate else 'NUA',
                                    'reference_type': 'partial_name'
                                }
                            break
            
            # TODO: Implement context-aware pronoun resolution in the future.
            
        
        return None

    def detect_new_actor_mention(self, user_input: str, existing_actors: list, target_info: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Detects if user input mentions a new actor not in existing_actors list.
        Returns actor info if found, None otherwise.
        
        Args:
            user_input: The user's input text
            existing_actors: List of currently existing actors
            target_info: Optional target detection results to inform actor type
        """
        existing_reference = self.detect_existing_actor_reference(user_input, existing_actors)
        if existing_reference:
            return None
        
        user_input_lower = user_input.lower()
        existing_names = [actor.sheet.name.lower() for actor in existing_actors]
        
        existing_inventory = []
        for actor in existing_actors:
            if hasattr(actor, 'sheet') and hasattr(actor.sheet, 'inventory'):
                existing_inventory.extend([item.name.lower() for item in actor.sheet.inventory])
        
        inua_mention = self._detect_inua_mention(user_input_lower, existing_names, existing_inventory)
        if inua_mention:
            return {
                'type': 'INUA',
                'name': inua_mention,
                'context': user_input,
                'action_type': self._classify_inua_action(user_input_lower)
            }
        
        nua_mention = self._detect_nua_mention(user_input_lower, existing_names, existing_inventory)
        if nua_mention:
            return {
                'type': 'NUA',
                'name': nua_mention,
                'context': user_input,
                'action_type': self._classify_nua_action(user_input_lower)
            }
        
        return None

    def _detect_inua_mention(self, user_input: str, existing_names: list, existing_inventory: list = None) -> Optional[str]:
        """Detect mentions of objects/INUAs in user input."""
        if existing_inventory is None:
            existing_inventory = []
            
        for keyword in self.inua_keywords:
            if keyword in user_input and keyword not in existing_names and keyword not in existing_inventory:
                if not self._matches_existing_actor(keyword, existing_names):
                    return keyword.title()
        
        for pattern in self.inua_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                match_clean = match.strip().lower()
                
                if (match_clean and 
                    match_clean not in existing_names and 
                    match_clean not in existing_inventory and
                    not self._is_problematic_phrase(match_clean)):
                    
                    contains_existing = self._matches_existing_actor(match_clean, existing_names)
                    if not contains_existing:
                        return match.strip().title()
        
        return None

    def _detect_nua_mention(self, user_input: str, existing_names: list, existing_inventory: list = None) -> Optional[str]:
        """Detect mentions of people/NUAs in user input."""
        if existing_inventory is None:
            existing_inventory = []
            
        for keyword in self.nua_keywords:
            if keyword in user_input and keyword not in existing_names and keyword not in existing_inventory:
                if not self._matches_existing_actor(keyword, existing_names):
                    return keyword.title()
        
        for pattern in self.nua_patterns:
            matches = re.findall(pattern, user_input, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match else ""
                match_clean = match.strip().lower()
                
                if (match_clean and 
                    match_clean not in existing_names and 
                    match_clean not in existing_inventory and
                    not self._is_problematic_phrase(match_clean)):
                    
                    contains_existing = self._matches_existing_actor(match_clean, existing_names)
                    if not contains_existing:
                        return match.strip().title()
        
        return None

    def _classify_inua_action(self, user_input: str) -> str:
        """Classify the type of action being attempted on an INUA."""
        if any(word in user_input for word in ['hack', 'bypass', 'disable']):
            return 'electronic_interaction'
        elif any(word in user_input for word in ['pick', 'unlock', 'open']):
            return 'mechanical_interaction'
        elif any(word in user_input for word in ['break', 'smash', 'destroy']):
            return 'force_interaction'
        else:
            return 'general_interaction'

    def _classify_nua_action(self, user_input: str) -> str:
        """Classify the type of action being attempted with an NUA."""
        if any(word in user_input for word in ['talk', 'speak', 'converse', 'ask']):
            return 'social_interaction'
        elif any(word in user_input for word in ['approach', 'follow', 'pursue']):
            return 'movement_interaction'
        elif any(word in user_input for word in ['attack', 'fight', 'combat']):
            return 'combat_interaction'
        else:
            return 'general_interaction'
    
    def _is_problematic_phrase(self, phrase: str) -> bool:
        """Check if a phrase should be ignored (too vague, possessive, etc.)."""
        problematic_patterns = [
            r'^my\s+',
            r'^the\s+area\s+for\s+',
            r'^area\s+for\s+',
            r'\s+for\s+\w+$',
            r'^\w+\s+\w+\s+\w+\s+\w+',
        ]
        
        for pattern in problematic_patterns:
            if re.search(pattern, phrase, re.IGNORECASE):
                return True
        
        return False
    
    def _matches_existing_actor(self, detected_name: str, existing_names: list) -> bool:
        """Check if detected name matches any existing actor (including partial matches)."""
        detected_words = set(detected_name.lower().split())
        
        for existing_name in existing_names:
            existing_words = set(existing_name.lower().split())
            
            if detected_name.lower() == existing_name.lower():
                return True
            
            if detected_words.issubset(existing_words):
                return True
            
            if existing_words.issubset(detected_words):
                return True
        
        return False


class DynamicActorCreator:
    """Creates new actors dynamically based on detection results."""
    
    def __init__(self, creator_agent: CreatorAgent):
        self.creator = creator_agent

    def create_dynamic_actor(self, actor_info: Dict[str, Any], scene_context: str) -> Optional[Any]:
        """
        Creates a new NUA or INUA based on the detection info.
        """
        if actor_info['type'] == 'INUA':
            return self._create_dynamic_inua(actor_info, scene_context)
        elif actor_info['type'] == 'NUA':
            return self._create_dynamic_nua(actor_info, scene_context)
        return None

    def _create_dynamic_inua(self, actor_info: Dict[str, Any], scene_context: str) -> Optional[InanimateNonUserActor]:
        """Create an INUA based on user mention."""
        try:
            inua_context = f"User is trying to interact with: {actor_info['name']}"
            action_context = f"Action type: {actor_info['action_type']}"
            full_context = f"{scene_context}\n{inua_context}\n{action_context}"
            
            inua = self.creator.generate_inua(
                context=full_context,
                scene_description=f"A {actor_info['name']} that the user wants to interact with"
            )
            
            if actor_info['name'].lower() not in inua.sheet.name.lower():
                inua.sheet.name = actor_info['name']
            
            return inua
            
        except Exception as e:
            print(f"Failed to create dynamic INUA: {e}")
            return None

    def _create_dynamic_nua(self, actor_info: Dict[str, Any], scene_context: str) -> Optional[NonUserActor]:
        """Create an NUA based on user mention."""
        try:
            nua_context = f"User wants to interact with: {actor_info['name']}"
            action_context = f"Interaction type: {actor_info['action_type']}"
            full_context = f"{scene_context}\n{nua_context}\n{action_context}"
            
            nua = self.creator.generate_nua(
                context=full_context,
                scene_description=f"A {actor_info['name']} that the user encounters"
            )
            
            if actor_info['name'].lower() not in nua.sheet.name.lower():
                nua.sheet.name = actor_info['name']
            
            return nua
            
        except Exception as e:
            print(f"Failed to create dynamic NUA: {e}")
            return None


class DynamicActorSystem:
    """Main system that coordinates dynamic actor detection and creation."""
    
    def __init__(self, creator_agent: CreatorAgent):
        self.detector = DynamicActorDetector()
        self.creator = DynamicActorCreator(creator_agent)

    def process_user_input(self, user_input: str, existing_actors: list, scene_context: str) -> Tuple[Optional[Any], Optional[Dict[str, Any]]]:
        """
        Process user input for dynamic actor creation.
        Returns (new_actor, actor_info) if created, (None, None) otherwise.
        """
        actor_info = self.detector.detect_new_actor_mention(user_input, existing_actors)
        
        if not actor_info:
            return None, None
        
        print(f"🔍 Attempting to create {actor_info['type']}: {actor_info['name']}")
        # Note: This system doesn't have access to actor_manager, so it can't auto-register
        new_actor = self.creator.create_dynamic_actor(actor_info, scene_context)
        
        if new_actor:
            print(f"🎭 Dynamically created {actor_info['type']}: {new_actor.sheet.name}")
            return new_actor, actor_info
        else:
            print(f"❌ Failed to create {actor_info['type']}: {actor_info['name']} (likely API key issue)")
        
        return None, None

    def should_switch_reactor(self, user_input: str, current_reactor: Any, existing_actors: list) -> bool:
        """
        Determine if the user input suggests switching to a different reactor.
        """
        actor_info = self.detector.detect_new_actor_mention(user_input, existing_actors)
        
        if not actor_info:
            return False
        
        current_name = current_reactor.sheet.name.lower() if current_reactor else ""
        mentioned_name = actor_info['name'].lower()
        
        return mentioned_name != current_name
