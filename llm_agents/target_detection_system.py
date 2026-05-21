#!/usr/bin/env python3
"""
Target Detection System
Determines whether user actions are directed at NUA (Non-User Actor) or INUA (Inanimate Non-User Actor) targets.
Similar to inquiry/action detection but focused on target classification.
"""

import re
from typing import Dict, Any, Optional
from openrouter_config import OpenRouterConfig

class TargetDetector:
    """
    Detects and classifies action targets as NUA (animate) or INUA (inanimate).
    Uses LLM analysis with fallback heuristics similar to inquiry detection.
    """
    
    def __init__(self):
        self.client = OpenRouterConfig.create_role_client('action_interpretation')
        self.config = OpenRouterConfig  # Fix: Initialize config for model lookup
        
        self.inua_keywords = {
            'terminal', 'console', 'screen', 'monitor', 'keyboard',
            'device', 'machine', 'drone', 'camera', 'sensor',
            'system', 'network', 'server', 'database', 'program', 'software',
            'scanner', 'detector', 'alarm', 'lock', 'keypad',
            
            'door', 'gate', 'wall', 'barrier', 'fence', 'window', 'hatch',
            'entrance', 'exit', 'passage', 'corridor', 'hallway',
            
            'lock', 'safe', 'vault', 'chest', 'strongbox', 'security',
            'alarm', 'trap', 'puzzle', 'riddle',
            
            'table', 'desk', 'chair', 'stool', 'counter', 'bar', 'shelf',
            'cabinet', 'drawer', 'box', 'container', 'barrel', 'crate',
            'bag', 'backpack', 'suitcase', 'briefcase',
            
            'weapon', 'gun', 'rifle', 'pistol', 'sword', 'knife', 'blade',
            'tool', 'hammer', 'wrench', 'screwdriver', 'crowbar',
            
            'car', 'vehicle', 'truck', 'van', 'motorcycle', 'bike', 'boat',
            'ship', 'aircraft', 'helicopter', 'plane'
        }
        
        self.nua_keywords = {
            'guard', 'soldier', 'officer', 'captain', 'commander', 'leader',
            'merchant', 'trader', 'shopkeeper', 'vendor', 'clerk', 'cashier',
            'doctor', 'nurse', 'medic', 'scientist', 'researcher', 'engineer',
            'pilot', 'driver', 'operator', 'technician', 'mechanic',
            'thief', 'bandit', 'criminal', 'assassin', 'spy', 'agent',
            'wizard', 'mage', 'priest', 'cleric', 'paladin', 'warrior',
            'citizen', 'civilian', 'person', 'human', 'man', 'woman',
            'child', 'kid', 'boy', 'girl', 'elder', 'old man', 'old woman',
            
            'ai', 'artificial intelligence', 'computer',
            'bot', 'android', 'cyborg', 'robot',
            'stranger', 'someone', 'anyone', 'everybody', 'nobody', 'whoever',
            'he', 'she', 'they', 'them', 'him', 'her', 'his', 'hers', 'their',
            
            'creature', 'beast', 'animal', 'dog', 'cat', 'bird', 'horse',
            'monster', 'alien'
        }
        
        self.inua_verbs = {
            'hack', 'access', 'login', 'connect', 'interface', 'operate',
            'use', 'activate', 'deactivate', 'turn on', 'turn off', 'switch',
            'press', 'push', 'pull', 'lift', 'move', 'shift', 'drag',
            'open', 'close', 'lock', 'unlock', 'break', 'smash', 'destroy',
            'repair', 'fix', 'build', 'construct', 'create', 'make',
            'examine', 'inspect', 'look at', 'search', 'find', 'locate',
            'take', 'grab', 'pick up', 'carry', 'hold', 'drop', 'place',
            'climb', 'jump', 'leap', 'crawl', 'slide', 'swing',
            
            'bypass', 'override', 'disable', 'shutdown', 'reset', 'reboot',
            'program', 'configure', 'install', 'uninstall', 'delete'
        }
        
        self.nua_verbs = {
            'talk', 'speak', 'say', 'tell', 'ask', 'question', 'interview',
            'negotiate', 'bargain', 'persuade', 'convince', 'argue', 'debate',
            'threaten', 'intimidate', 'bribe', 'seduce', 'charm', 'flirt',
            'greet', 'meet', 'introduce', 'befriend', 'trust', 'betray',
            'fight', 'attack', 'hit', 'punch', 'kick', 'stab', 'shoot',
            'kill', 'murder', 'assassinate', 'execute', 'torture',
            'help', 'assist', 'aid', 'support', 'protect', 'defend',
            'follow', 'chase', 'pursue', 'track', 'hunt', 'stalk', 'watch',
            
            'reason', 'convince', 'persuade', 'negotiate', 'discuss',
            'collaborate', 'cooperate', 'ally', 'partner',
            
            'call', 'phone', 'dial', 'ring', 'contact', 'message', 'text'
        }

    def detect_target_type(self, user_input: str, scene_description: str = "") -> Dict[str, Any]:
        """
        Determine if the user's action is targeting an NUA (animate) or INUA (inanimate).
        
        Args:
            user_input: The user's action input
            scene_description: Current scene context for better analysis
            
        Returns:
            Dict with target_type, confidence, reasoning, and detected_target
        """
        print(f"\n🎯 DEBUG: Analyzing target type for: '{user_input}'")
        
        prompt = f"""
You are analyzing user input in a UTAS simulation to determine if the action is targeting an NUA (Non-User Actor - animate being) or INUA (Inanimate Non-User Actor - object/device).

**CRITICAL DISTINCTION - CONVERSATIONAL AUTONOMY TEST:**
The key question: "Can you have a meaningful conversation with this target that might change its mind or behavior through reasoning?"

**NUA (Animate) Criteria:**
- Living beings with consciousness and personality
- Sentient AIs that can reason, negotiate, and change their minds
- Autonomous entities that make independent decisions
- Can engage in dialogue, be persuaded, convinced, or reasoned with
- Examples: humans, animals, autonomous AI assistants, sentient robots

**INUA (Inanimate) Criteria:**
- Objects, devices, and systems that follow programming
- Non-autonomous technology that processes inputs predictably
- Cannot be reasoned with or change behavior through conversation
- Responds only to commands, inputs, or physical manipulation
- Examples: doors, computers, terminals, cameras, most security systems

**AI/Computer Entity Guidelines:**
- "Talk to the computer" → Usually INUA (command interface)
- "Negotiate with the AI" → Usually NUA (conversational autonomy)
- "Hack the system" → INUA (overriding programming)
- "Convince the AI" → NUA (reasoning/persuasion possible)

**Security System Guidelines:**
- Basic security cameras/alarms → INUA
- Autonomous security AI that can be reasoned with → NUA
- Smart systems that just follow protocols → INUA

**CURRENT SCENE CONTEXT:**
{scene_description}

**USER INPUT:** "{user_input}"

Analyze the target and respond with JSON:
{{
    "target_type": "NUA" or "INUA",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation focusing on conversational autonomy",
    "detected_target": "name of the target entity"
}}

Examples:
- "I open the door" → {{"target_type": "INUA", "confidence": 0.9, "reasoning": "Mechanical action on structure", "detected_target": "door"}}
- "I negotiate with the AI" → {{"target_type": "NUA", "confidence": 0.8, "reasoning": "Conversational interaction suggesting autonomy", "detected_target": "AI"}}
- "I bypass the security system" → {{"target_type": "INUA", "confidence": 0.9, "reasoning": "Technical override of automated system", "detected_target": "security system"}}
- "I convince the computer to help me" → {{"target_type": "NUA", "confidence": 0.6, "reasoning": "Persuasion implies conversational autonomy", "detected_target": "computer"}}
"""
        
        try:
            print("🎯 DEBUG: Calling LLM for target detection...")
            response = self.client.chat.completions.create(
                model=self.config.get_model_for_role('interpretation'),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content.strip()
            print(f"🎯 DEBUG: LLM response: {response_text}")
            
            # Clean up markdown formatting if present
            if response_text.startswith('```json'):
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            elif response_text.startswith('```'):
                response_text = response_text.replace('```', '').strip()
            
            import json
            response_data = json.loads(response_text)
            
            if response_data and 'target_type' in response_data:
                print(f"🎯 DEBUG: Parsed LLM response: {response_data}")
                return response_data
            else:
                print("🎯 DEBUG: Invalid LLM response format, falling back to heuristic")
                pass
        except Exception as e:
            print(f"🎯 DEBUG: LLM error: {e}")
            pass
        
        # Fallback: Heuristic analysis if LLM fails
        return self._heuristic_target_detection(user_input, scene_description)
    
    def _heuristic_target_detection(self, user_input: str, scene_description: str = "") -> Dict[str, Any]:
        """
        Fallback heuristic method for target detection when LLM fails.
        
        Args:
            user_input: The user's action input
            
        Returns:
            Dict with target classification results
        """
        print(f"🎯 DEBUG: Using fallback heuristic for: '{user_input}'")
        
        user_lower = user_input.lower()
        
        nua_score = 0
        inua_score = 0
        detected_target = None
        
        # First, check for proper names in the scene description
        if scene_description:
            # Extract capitalized words from scene description as potential proper names
            import re
            proper_names = re.findall(r'\b[A-Z][a-z]+\b', scene_description)
            for name in proper_names:
                if name.lower() in user_lower:
                    nua_score += 5  # Strong indicator of NUA target
                    detected_target = name
                    print(f"🎯 DEBUG: Found proper name from scene: '{name}' (+5 NUA)")
                    break
        
        # Check for proper names in the user input itself (for remote targets or unintroduced NPCs)
        # Exclude the first word if it's just the start of the sentence
        input_words = user_input.split()
        if len(input_words) > 1:
            # Check words other than the first one for capitalization
            potential_names = []
            for i, word in enumerate(input_words):
                if i > 0 and word[0].isupper() and word.lower() not in ['the', 'a', 'an', 'in', 'on', 'at', 'to', 'for', 'of']:
                    clean_word = ''.join(c for c in word if c.isalnum())
                    if clean_word:
                        potential_names.append(clean_word)
            
            if potential_names:
                for name in potential_names:
                    # Verify it's not a common keyword
                    if name.lower() not in self.inua_keywords and name.lower() not in self.nua_keywords:
                        nua_score += 3
                        detected_target = name
                        print(f"🎯 DEBUG: Found potential proper name in input: '{name}' (+3 NUA)")
                        
        words = re.findall(r'\b\w+\b', user_lower)
        
        for word in words:
            if word in self.nua_keywords:
                nua_score += 2
                detected_target = word
                print(f"🎯 DEBUG: Found NUA keyword: '{word}' (+2 NUA)")
            elif word in self.inua_keywords:
                inua_score += 2
                detected_target = word
                print(f"🎯 DEBUG: Found INUA keyword: '{word}' (+2 INUA)")
            elif word in self.nua_verbs:
                nua_score += 1
                print(f"🎯 DEBUG: Found NUA verb: '{word}' (+1 NUA)")
            elif word in self.inua_verbs:
                inua_score += 1
                print(f"🎯 DEBUG: Found INUA verb: '{word}' (+1 INUA)")
        
        pronouns = ['he', 'she', 'they', 'them', 'him', 'her', 'his', 'hers', 'their']
        for pronoun in pronouns:
            if pronoun in user_lower:
                nua_score += 3
                detected_target = pronoun
                print(f"🎯 DEBUG: Found pronoun: '{pronoun}' (+3 NUA)")
        
        the_pattern = r'\bthe\s+(\w+(?:\s+\w+)*)'
        matches = re.findall(the_pattern, user_lower)
        for match in matches:
            if any(keyword in match for keyword in self.inua_keywords):
                inua_score += 1
                detected_target = match
                print(f"🎯 DEBUG: Found 'the {match}' pattern (+1 INUA)")
            elif any(keyword in match for keyword in self.nua_keywords):
                nua_score += 1
                detected_target = match
                print(f"🎯 DEBUG: Found 'the {match}' pattern (+1 NUA)")
        
        print(f"🎯 DEBUG: Final scores - NUA: {nua_score}, INUA: {inua_score}")
        
        if nua_score > inua_score:
            target_type = "nua"
            confidence = "high" if nua_score >= 3 else "medium"
            reasoning = f"NUA indicators detected (score: {nua_score} vs {inua_score})"
        elif inua_score > nua_score:
            target_type = "inua"
            confidence = "high" if inua_score >= 3 else "medium"
            reasoning = f"INUA indicators detected (score: {inua_score} vs {nua_score})"
        else:
            target_type = "inua"
            confidence = "low"
            reasoning = "Ambiguous target, defaulting to INUA"
        
        result = {
            "target_type": target_type,
            "confidence": confidence,
            "reasoning": reasoning,
            "detected_target": detected_target or "unknown"
        }
        
        print(f"🎯 DEBUG: Heuristic result: {result}")
        return result

    def is_targeting_nua(self, user_input: str, scene_description: str = "") -> bool:
        """
        Simple boolean check if action targets an NUA.
        
        Args:
            user_input: The user's action input
            scene_description: Current scene context
            
        Returns:
            True if targeting NUA, False if targeting INUA
        """
        result = self.detect_target_type(user_input, scene_description)
        return result.get('target_type') == 'nua'
    
    def is_targeting_inua(self, user_input: str, scene_description: str = "") -> bool:
        """
        Simple boolean check if action targets an INUA.
        
        Args:
            user_input: The user's action input
            scene_description: Current scene context
            
        Returns:
            True if targeting INUA, False if targeting NUA
        """
        result = self.detect_target_type(user_input, scene_description)
        return result.get('target_type') == 'inua'


def test_target_detector():
    """Test the target detection system with various inputs."""
    detector = TargetDetector()
    
    test_cases = [
        "I talk to the guard",
        "I attack the bandit", 
        "I ask him about the mission",
        "I approach the stranger",
        "I fight the soldier",
        "I negotiate with the merchant",
        
        "I hack the terminal",
        "I open the door",
        "I examine the chest",
        "I break the lock",
        "I use the computer",
        "I search the desk",
        
        "I shoot",
        "I look around",
        "I move forward",
        "I wait"
    ]
    
    print("=== TARGET DETECTION TESTS ===")
    for test_input in test_cases:
        result = detector.detect_target_type(test_input)
        print(f"Input: '{test_input}'")
        print(f"Result: {result}")
        print()

if __name__ == "__main__":
    test_target_detector()
