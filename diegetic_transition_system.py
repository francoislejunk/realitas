"""
Diegetic Transition System - Handles vague/sweeping user intents by breaking them into confirmable steps.

PHILOSOPHY:
- System is NOT a narrator (God-view of everything)
- System is an EXPERIENCE DESCRIBER (only what user can perceive)
- When intent is vague/sweeping, pause at natural boundaries
- Use inner voice for memory/suggestion/commentary
- NEVER steal agency - always wait for user confirmation

EXAMPLES:

BAD (Time Skip):
User: "I finish breakfast and get to the garage"
System: "You finish your cereal, get dressed, get on the elevator, and walk to your car."
Problem: Narrated through 10 floors, stole multiple actions

GOOD (Diegetic Pause):
User: "I finish breakfast and get to the garage"
Inner Voice: "Last time you left without brushing your teeth you scared people. 
              Imagine leaving without even getting dressed."
Experience: "You finish your breakfast, feel satiated after all that cereal, milk 
            and sugar like a happy kid before going to school. On your way to getting 
            ready to leave your place to get to the garage, now you're wondering what 
            to do next to get prepared before leaving."
System: "What do you do?"

WHEN TO USE:
- Vague intent that spans multiple 3TU windows
- Sweeping goals without specific steps
- Intent that requires multiple distinct actions

WHEN NOT TO USE:
- Specific intent that fits in one 3TU window
- User: "I open the door in front of me" → Just describe the experience
- Clear, atomic actions
"""

from typing import Dict, List, Optional, Tuple
from enum import Enum


class IntentScope(Enum):
    """Classification of user intent scope."""
    ATOMIC = "atomic"  # Fits in one 3TU window, just describe it
    SWEEPING = "sweeping"  # Spans multiple 3TU windows, needs breakdown
    VAGUE = "vague"  # Unclear steps, needs clarification


class DiegeticTransitionSystem:
    """Handles vague/sweeping intents by breaking them into confirmable steps."""
    
    def __init__(self, llm_client, model: str, logger):
        self.client = llm_client
        self.model = model
        self.logger = logger
    
    def analyze_intent_scope(self, user_input: str, scene_context: str, 
                            actor_personality: Dict[str, str]) -> Dict:
        """
        Analyze if user intent is atomic (fits in 3TU) or sweeping (needs breakdown).
        
        Returns:
            {
                "scope": IntentScope,
                "reasoning": str,
                "estimated_steps": int,
                "needs_breakdown": bool
            }
        """
        # Check if this is a question/inquiry first - bypass diegetic analysis
        question_patterns = [
            "what", "where", "when", "why", "how", "who", "which",
            "can you", "could you", "would you", "do you know",
            "tell me", "explain", "describe", "is there", "are there"
        ]
        
        # Memory recall/inquiry patterns (mental actions, not physical)
        inquiry_patterns = [
            "try to remember", "try to recall", "trying to remember", "trying to recall",
            "think about", "think back", "reminisce", "recall", "remember",
            "search my memory", "dig through"
        ]
        
        user_input_lower = user_input.lower().strip()
        
        # Check if input starts with question word or contains question patterns
        is_question = (
            user_input_lower.endswith("?") or
            any(user_input_lower.startswith(pattern) for pattern in question_patterns) or
            any(f" {pattern} " in f" {user_input_lower} " for pattern in ["can you", "could you", "would you", "tell me"])
        )
        
        # Check if this is a memory recall/inquiry action
        is_inquiry_action = any(pattern in user_input_lower for pattern in inquiry_patterns)
        
        if is_question or is_inquiry_action:
            # This is an inquiry/mental action - return atomic to bypass diegetic pause
            return {
                "scope": IntentScope.ATOMIC,
                "reasoning": "This is a question/inquiry/mental action, not a physical action",
                "estimated_steps": 0,
                "needs_breakdown": False
            }
        
        # Check if this is a combat/violent action - treat as atomic (single exchange)
        combat_keywords = [
            "punch", "hit", "strike", "attack", "kick", "stab", "shoot", "fire",
            "slash", "swing", "throw", "shove", "push", "grab", "tackle", "headbutt",
            "bite", "choke", "strangle", "beat", "smash", "slam", "elbow", "knee"
        ]
        
        is_combat = any(keyword in user_input_lower for keyword in combat_keywords)
        
        if is_combat:
            # Combat actions are single exchanges, even with preparation steps
            return {
                "scope": IntentScope.ATOMIC,
                "reasoning": "Combat action - treated as single exchange",
                "estimated_steps": 1,
                "needs_breakdown": False
            }
        
        # FIX BUG #5: Add heuristic for common simple actions to avoid over-classification
        simple_action_keywords = [
            "open", "close", "pick up", "grab", "take", "put", "place",
            "sit", "stand", "wait", "observe", "look", "watch", "listen",
            "step", "walk through", "go through", "enter", "exit", "leave",
            "say", "speak", "tell", "ask", "call out", "shout",
            "press", "push", "pull", "turn", "flip", "switch"
        ]
        
        # Check if this is a simple single-word action or contains simple action keywords
        word_count = len(user_input.split())
        is_simple_action = (
            word_count <= 6 and  # Short actions are usually simple
            any(keyword in user_input_lower for keyword in simple_action_keywords)
        )
        
        # Special case: movement to nearby locations (street, outside, door, room)
        nearby_movement_keywords = ["street", "outside", "door", "doorway", "room", "hallway", "stairs"]
        is_nearby_movement = (
            any(move_word in user_input_lower for move_word in ["go", "head", "walk", "move", "step"]) and
            any(loc_word in user_input_lower for loc_word in nearby_movement_keywords) and
            word_count <= 10  # Keep it reasonable
        )
        
        if is_simple_action or is_nearby_movement:
            return {
                "scope": IntentScope.ATOMIC,
                "reasoning": "Simple action or nearby movement - execute immediately",
                "estimated_steps": 1,
                "needs_breakdown": False
            }
        
        prompt = f"""
You are analyzing user intent to determine if it fits within a single 3-second or 3-minute time unit.

**User Input:** "{user_input}"
**Scene Context:** {scene_context}

**3-Second Actions (ATOMIC - Execute Immediately):**
- Opening/closing a door
- Picking up an object
- Speaking a sentence
- Taking a step or walking through a doorway
- Looking/observing something
- Pressing a button
- Sitting/standing
- Waiting/pausing

**3-Minute Actions (ATOMIC - Execute Immediately):**
- Having a brief conversation
- Walking to a nearby location (same room, same floor, adjacent street)
- Moving from inside to outside (e.g., "I step outside", "I head to the street")
- Examining something carefully
- Waiting and observing
- Eating a quick snack
- Making a phone call
- Cleaning/sweeping a single room
- Searching a specific area
- Reading a document

**Sweeping Actions (Need Breakdown - Multiple Distinct Steps):**
- "Get ready to leave" (multiple steps: dress, brush teeth, gather items)
- "Go to the garage" from 10th floor (multiple steps: prepare, elevator, walk)
- "Investigate the entire area" (multiple locations/actions)
- "Get some food" (multiple steps: find place, order, eat)
- "Clean the entire house" (multiple rooms/tasks)

**CRITICAL RULES:**
1. Simple movement = ATOMIC ("I go outside", "I walk to the street", "I head to the door")
2. Single observation = ATOMIC ("I wait and observe", "I look around")
3. Opening/closing things = ATOMIC ("I open the door", "I step through the doorway")
4. Only classify as SWEEPING if it EXPLICITLY involves multiple distinct locations or complex multi-step processes
5. When in doubt → ATOMIC (let the action execute)

**Analysis Guidelines:**
1. If action is a single movement, observation, or interaction → ATOMIC
2. If action explicitly requires multiple distinct steps across different locations → SWEEPING
3. Default to ATOMIC unless clearly sweeping

Respond with ONLY a JSON object:
{{
    "scope": "atomic" or "sweeping",
    "reasoning": "Brief explanation",
    "estimated_steps": 1,
    "needs_breakdown": false
}}
        """.strip()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            from json_utils import extract_and_parse_json
            analysis = extract_and_parse_json(response_text)
            
            if analysis:
                analysis['scope'] = IntentScope(analysis['scope'])
                return analysis
            else:
                # Fallback: assume atomic
                return {
                    "scope": IntentScope.ATOMIC,
                    "reasoning": "Could not analyze, defaulting to atomic",
                    "estimated_steps": 1,
                    "needs_breakdown": False
                }
                
        except Exception as e:
            self.logger.log_system(f"Error analyzing intent scope: {e}")
            return {
                "scope": IntentScope.ATOMIC,
                "reasoning": f"Error: {e}",
                "estimated_steps": 1,
                "needs_breakdown": False
            }
    
    def generate_diegetic_pause(self, user_input: str, scene_context: str,
                               actor_name: str, actor_personality: Dict[str, str],
                               current_location: str, previous_inner_voice: str = None) -> Dict[str, str]:
        """
        Generate a diegetic pause with inner voice and experience description.
        
        Returns:
            {
                "inner_voice": str,  # First-person commentary/suggestion
                "experience_description": str,  # What user perceives/feels
                "next_prompt": str  # "What do you do?"
            }
        """
        internal_trait = actor_personality.get('internal', 'thoughtful')
        external_trait = actor_personality.get('external', 'observant')
        
        # Add previous inner voice context if available
        inner_voice_context = ""
        if previous_inner_voice:
            inner_voice_context = f"\n**Previous Inner Voice:** {previous_inner_voice}\n(Your new inner voice should be consistent with this thought pattern)"
        
        prompt = f"""
You are generating a DIEGETIC PAUSE for a sweeping user intent that needs to be broken into steps.

**User Intent:** "{user_input}"
**Recent Context:** {scene_context}
**Current Location:** {current_location}
**Actor:** {actor_name}
**Personality:** Internal: {internal_trait}, External: {external_trait}{inner_voice_context}

**CRITICAL: PROGRESSION, NOT REPETITION**
- The Recent Context shows what JUST happened
- DO NOT repeat descriptions from the context
- CONTINUE FORWARD from where the context left off
- If context mentions "standing up", don't describe standing up again
- If context mentions "at the door", describe what happens NEXT at the door

**YOUR ROLE:**
You are an EXPERIENCE DESCRIBER, NOT a narrator. You only describe what the user can:
- SEE (visual details in their immediate view)
- HEAR (sounds around them)
- FEEL (physical sensations, emotions)
- SMELL (scents in the air)
- TASTE (if relevant)

You do NOT:
- Narrate actions the user hasn't confirmed
- Describe what's happening elsewhere
- Take a God-view of the world
- Complete the user's goal for them
- REPEAT what already happened in the context

**INNER VOICE GUIDELINES:**
- First person PLURAL ("we", "our", "us") - feels like shared consciousness
- MUST reflect internal personality trait: {internal_trait}
- Can comment, remember, or suggest based on personality
- 1-2 sentences maximum
- Should feel like the user's ACTUAL thoughts, not generic narration
- Examples based on personality:
  * (anxious) "We should check the toolkit twice—last time we forgot the multimeter and looked like an idiot."
  * (confident) "We've got this. Ten floors down, grab the keys, and we're golden."
  * (paranoid) "We need to make sure nobody's watching before we head out with all this gear."

**EXPERIENCE DESCRIPTION GUIDELINES:**
- Present tense, second person ("you")
- CONCRETE sensory details - be SPECIFIC, not vague
- Show ONLY the FIRST STEP being completed (ONE 3TU window = 3 seconds OR 3 minutes MAX)
- STOP IMMEDIATELY at the natural boundary before the next step
- Include physical sensations, sounds, smells, textures
- 3-5 sentences with rich detail

**CRITICAL (FIX BUG #9): ONLY USE ESTABLISHED SCENE ELEMENTS**
- Reference ONLY objects/details mentioned in "Recent Context" or "Current Location"
- Do NOT invent new furniture, objects, or environmental details
- If scene mentions "garage bay" → use garage elements (tools, vehicles, concrete)
- If scene mentions "apartment" → use apartment elements from the description
- Do NOT add: chairs, desks, lamps, windows, etc. unless they're in the scene context
- When in doubt, describe body sensations and sounds instead of inventing objects

**⚠️ CRITICAL 3TU BOUNDARY RULE ⚠️**
User: "I get up, grab my gear and flyers, and head out"
FIRST STEP = "get up" (3 seconds)
SECOND STEP = "grab gear and flyers" (3 seconds) ← DO NOT DESCRIBE THIS
THIRD STEP = "head out" (3 minutes) ← DO NOT DESCRIBE THIS

YOU MUST ONLY DESCRIBE THE FIRST STEP!

**WHAT COUNTS AS ONE STEP (3TU):**
- "Get up" = Standing up from sitting/lying position (3 seconds) ← ONLY THIS
- "Grab gear" = Picking up items (3 seconds) ← SEPARATE STEP, DON'T DESCRIBE
- "Head out" = Walking to door and leaving (3 minutes) ← SEPARATE STEP, DON'T DESCRIBE

**CORRECT EXAMPLE:**
User: "I get up, grab my tools, and head out"
Experience: "You push yourself up from the futon, the springs groaning beneath you. Your legs feel stiff from sleep. The tools are on the floor by the door, still out of reach. You're standing now, barefoot on the cold floor."
✓ ONLY describes "get up"
✓ Tools are mentioned but NOT grabbed
✓ Door is NOT approached
✓ User is standing, waiting for next command

**WRONG EXAMPLE (WHAT YOU DID BEFORE):**
User: "I get up, grab my gear and flyers, and head out"
Experience: "You push up from the mattress. The duffel bag's canvas straps dig into your fingertips as you lean over to grip them. You're standing now, the floorboards creaking."
❌ Step 1: Push up ← CORRECT
❌ Step 2: Lean over to grip straps ← WRONG! This is grabbing!
❌ Step 3: Standing with floor creaking ← WRONG! This continues the action!

**ABSOLUTE RULE:**
If the user says "I get up, grab X, and do Y":
- ONLY describe getting up
- DO NOT describe grabbing X
- DO NOT describe doing Y
- DO NOT describe moving toward X
- DO NOT describe touching X
- STOP after standing up

**VERIFICATION:**
After writing the experience, ask yourself:
1. Did I describe ONLY the first action?
2. Did I avoid describing any subsequent actions?
3. Is the user still at the starting point?
If ANY answer is "no", REWRITE IT!

Generate the diegetic pause:

{{
    "inner_voice": "First-person PLURAL ('we') commentary reflecting {internal_trait} personality (1-2 sentences)",
    "experience_description": "CONCRETE sensory details of what user perceives right now - be SPECIFIC (3-5 sentences)",
    "next_prompt": "What do you do?"
}}
        """.strip()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content.strip()
            
            from json_utils import extract_and_parse_json
            pause_data = extract_and_parse_json(response_text)
            
            if pause_data:
                return pause_data
            else:
                # Fallback
                return {
                    "inner_voice": f"We need to think this through step by step.",
                    "experience_description": f"You pause, considering the best way to approach this. The goal is clear, but the path requires careful thought.",
                    "next_prompt": "What do you do?"
                }
                
        except Exception as e:
            self.logger.log_system(f"Error generating diegetic pause: {e}")
            return {
                "inner_voice": f"We need to figure this out.",
                "experience_description": f"You pause to consider your approach, weighing your options.",
                "next_prompt": "What do you do?"
            }
    
    def generate_atomic_experience(self, user_input: str, scene_context: str,
                                   actor_name: str, actor_personality: Dict[str, str],
                                   current_location: str) -> Dict[str, str]:
        """
        Generate inner voice + experience description for atomic (single 3TU) actions.
        
        This is for actions that fit in one 3-second or 3-minute window.
        Returns both internal commentary and sensory experience, mirroring sweeping format.
        
        Returns:
            {
                "inner_voice": str,  # First-person commentary
                "experience_description": str  # What user perceives
            }
        """
        internal_trait = actor_personality.get('internal', 'thoughtful')
        external_trait = actor_personality.get('external', 'observant')
        
        prompt = f"""
You are generating a DIEGETIC EXPERIENCE for an atomic action (fits in one 3-second or 3-minute window).

**User Action:** "{user_input}"
**Recent Context:** {scene_context}
**Current Location:** {current_location}
**Character:** {actor_name}
**Personality:** Internal: {internal_trait}, External: {external_trait}

**CRITICAL: PROGRESSION, NOT REPETITION**
- The Recent Context shows what JUST happened
- DO NOT repeat descriptions from the context
- CONTINUE FORWARD from where the context left off
- If context mentions something, don't describe it again

**YOUR ROLE:**
You are an EXPERIENCE DESCRIBER, NOT a narrator. You only describe what the user can:
- SEE (visual details in their immediate view)
- HEAR (sounds around them)
- FEEL (physical sensations, emotions)
- SMELL (scents in the air)
- TASTE (if relevant)

You do NOT:
- Narrate actions the user hasn't confirmed
- Describe what's happening elsewhere
- Take a God-view of the world
- REPEAT what already happened in the context

**INNER VOICE GUIDELINES:**
- First person PLURAL ("we", "our", "us") - feels like shared consciousness
- MUST reflect internal personality trait: {internal_trait}
- Can comment, remember, or suggest based on personality
- 1-2 sentences maximum
- Should feel like the user's ACTUAL thoughts, not generic narration
- Examples based on personality:
  * (anxious) "We should check the toolkit twice—last time we forgot the multimeter and looked like an idiot."
  * (confident) "We've got this. Ten floors down, grab the keys, and we're golden."
  * (paranoid) "We need to make sure nobody's watching before we head out with all this gear."

**EXPERIENCE DESCRIPTION GUIDELINES:**
- Present tense, second person ("you")
- CONCRETE sensory details - be SPECIFIC, not vague
- Show the action being completed (ONE 3TU window = 3 seconds OR 3 minutes MAX)
- Include physical sensations, sounds, smells, textures
- 3-5 sentences with rich detail

**CRITICAL (FIX BUG #9): ONLY USE ESTABLISHED SCENE ELEMENTS**
- Reference ONLY objects/details mentioned in "Recent Context" or "Current Location"
- Do NOT invent new furniture, objects, or environmental details
- If scene mentions "garage bay" → use garage elements (tools, vehicles, concrete)
- If scene mentions "apartment" → use apartment elements from the description
- Do NOT add: chairs, desks, lamps, windows, etc. unless they're in the scene context
- When in doubt, describe body sensations and sounds instead of inventing objects

**EXAMPLE:**
User: "I open the door in front of me"
Response:
{{
    "inner_voice": "We need to see what's on the other side. Time to find out.",
    "experience_description": "You extend your arm and feel as your hand grasps the coldness of the metal doorknob. As it turns, the door gives way to the light of the room ahead, slowly presenting the silhouette of an older man you've never seen before. A man with a scar across his face, reeking of beer, staring at you."
}}

Generate the atomic experience:

{{
    "inner_voice": "First-person PLURAL ('we') commentary reflecting {internal_trait} personality (1-2 sentences)",
    "experience_description": "CONCRETE sensory details of what user perceives right now - be SPECIFIC (3-5 sentences)"
}}
        """.strip()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.7
            )
            
            import json
            from json_utils import extract_and_parse_json
            
            response_text = response.choices[0].message.content.strip()
            parsed = extract_and_parse_json(response_text)
            
            if parsed and 'inner_voice' in parsed and 'experience_description' in parsed:
                return parsed
            else:
                # Fallback
                return {
                    "inner_voice": f"We're doing this. Let's see what happens.",
                    "experience_description": f"You {user_input.lower()}."
                }
            
        except Exception as e:
            self.logger.log_system(f"Error generating atomic experience: {e}")
            return {
                "inner_voice": f"We're taking action.",
                "experience_description": f"You {user_input.lower()}."
            }


def display_diegetic_pause(pause_data: Dict[str, str], actor_name: str):
    """Display a diegetic pause with formatting."""
    from color_utils import Color
    
    print(f"\n{Color.SYSTEM}{'═' * 70}{Color.RESET}")
    print(f"{Color.SYSTEM}💭 INTERNAL VOICE{Color.RESET}")
    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}")
    print(f"{Color.INTERNAL_VOICE}{pause_data['inner_voice']}{Color.RESET}")
    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
    
    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}")
    print(f"{Color.SYSTEM}👁️  EXPERIENCE{Color.RESET}")
    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}")
    print(f"{Color.NARRATIVE}{pause_data['experience_description']}{Color.RESET}")
    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
    
    print(f"{Color.WARNING}{pause_data['next_prompt']}{Color.RESET}")


def display_atomic_experience(experience_data: Dict[str, str], actor_name: str):
    """Display an atomic experience with inner voice + experience (mirrors sweeping format)."""
    from color_utils import Color
    
    print(f"\n{Color.SYSTEM}{'═' * 70}{Color.RESET}")
    print(f"{Color.SYSTEM}💭 INTERNAL VOICE{Color.RESET}")
    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}")
    print(f"{Color.INTERNAL_VOICE}{experience_data['inner_voice']}{Color.RESET}")
    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
    
    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}")
    print(f"{Color.SYSTEM}👁️  EXPERIENCE{Color.RESET}")
    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}")
    print(f"{Color.NARRATIVE}{experience_data['experience_description']}{Color.RESET}")
    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
