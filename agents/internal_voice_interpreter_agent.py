"""
Internal Voice Interpreter Agent

Determines what type of internal voice response is most relevant for the current situation.
This agent analyzes the context and decides which of the 5 internal voice functions to use:

1. MEMORY - Recall relevant memories (triggered by associations)
2. COMMENT - Add personality flavor (always personality-driven)
3. SOLUTION - Suggest actions when in predicaments
4. INFORMATION - Answer direct questions about identity/knowledge
5. TASK_REMINDER - Diegetic reminder of current task/goal when drifting

The interpreter ensures the internal voice is ALWAYS present and NEVER repetitive.

Design Philosophy:
- Internal voice should ALWAYS be evident (never disappear)
- Personality (OCEAN, MBTI, Mood) must always be reflected
- The most RELEVANT function should be selected
- Never repeat the same type back-to-back without good reason
- Task reminders should feel natural, like suddenly remembering what you were doing
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

from openrouter_config import create_role_client, OpenRouterConfig, robust_llm_call
from json_utils import extract_and_parse_json
from color_utils import Color


class InternalVoiceFunction(Enum):
    """The five functions of internal voice"""
    MEMORY = "memory"           # Recall relevant memories
    COMMENT = "comment"         # Personality-driven flavor
    SOLUTION = "solution"       # Suggest actions when in predicaments
    INFORMATION = "information" # Answer identity/knowledge questions
    TASK_GOAL_REMINDER = "task_goal_reminder"  # Diegetic reminder of current task/goal
    TASK_REMINDER = "task_reminder"            # Alias used by creator agent


class QuestionType(Enum):
    """Types of questions the internal voice can answer"""
    LOGIC = "logic"             # Factual questions (friend, family, boss, work)
    CONCEPTUAL = "conceptual"   # Abstract questions (should I, meaning of)
    IDENTITY = "identity"       # Who am I, what do I want


@dataclass
class VoiceInterpretation:
    """Result of interpreting what internal voice should do"""
    primary_function: InternalVoiceFunction
    secondary_function: Optional[InternalVoiceFunction] = None
    
    # For INFORMATION function
    question_type: Optional[QuestionType] = None
    question_content: Optional[str] = None
    
    # For MEMORY function
    memory_trigger: Optional[str] = None
    memory_category: Optional[str] = None
    
    # For SOLUTION function
    predicament_description: Optional[str] = None
    goal_relevance: Optional[str] = None
    
    # For TASK_REMINDER function
    task_drift_detected: bool = False
    drift_severity: str = "mild"  # mild, moderate, severe
    
    # Context
    urgency: str = "normal"  # calm, normal, urgent, frantic
    reasoning: str = ""


class InternalVoiceInterpreterAgent:
    """
    Interprets the current situation to determine the most relevant
    internal voice function.
    
    Key Responsibilities:
    1. Analyze current context (scene, action, outcome)
    2. Consider actor's personality (OCEAN, MBTI, Mood)
    3. Check for predicaments that need solutions
    4. Detect questions that need answers
    5. Identify memory triggers
    6. Default to personality-driven comments
    
    The internal voice should NEVER disappear - if nothing else is relevant,
    a personality-driven comment should always be generated.
    """
    
    def __init__(self):
        self.client = create_role_client("coordination")
        self.logger = logging.getLogger(__name__)
        
        # Track recent functions to avoid repetition
        self.recent_functions: List[InternalVoiceFunction] = []
        self.max_recent_history = 5
        
        # Track recent topics to avoid repetition
        self.recent_topics: List[str] = []
        self.max_recent_topics = 10
    
    def interpret_situation(self,
                           scene_description: str,
                           user_action: str,
                           action_outcome: str,
                           actor_state: Dict[str, Any],
                           personality_context: str,
                           current_goal: str = "",
                           current_task: str = "",
                           available_memories: List[str] = None,
                           is_inquiry: bool = False) -> VoiceInterpretation:
        """
        Interpret the current situation to determine internal voice function.
        
        Args:
            scene_description: Current scene
            user_action: What the user just did/said
            action_outcome: Result of the action
            actor_state: Current status (stamina, spirit, mood, etc.)
            personality_context: Personality prompt section
            current_goal: Actor's current goal
            current_task: Actor's current task
            available_memories: List of available memories
            is_inquiry: Whether this is an inquiry (question) from user
            
        Returns:
            VoiceInterpretation with recommended function
        """
        # FAST PATH: Try quick classification first to save LLM calls
        quick_func, confidence = self.quick_classify(user_action)
        
        # High confidence threshold - skip LLM if we're confident
        CONFIDENCE_THRESHOLD = 0.8
        
        if confidence >= CONFIDENCE_THRESHOLD and quick_func is not None:
            # Fast path - use heuristic result
            urgency = self.determine_urgency(
                actor_state.get('mood', {}),
                action_outcome,
                scene_description
            )
            
            # Build interpretation from quick classification
            interpretation = VoiceInterpretation(
                primary_function=quick_func,
                urgency=urgency,
                reasoning=f"Quick classification (confidence: {confidence:.0%})"
            )
            
            # Add function-specific details
            if quick_func == InternalVoiceFunction.INFORMATION:
                # Determine question type from input
                input_lower = user_action.lower()
                if any(w in input_lower for w in ["who", "what", "where", "when"]):
                    interpretation.question_type = QuestionType.LOGIC
                elif any(w in input_lower for w in ["should", "why", "meaning"]):
                    interpretation.question_type = QuestionType.CONCEPTUAL
                else:
                    interpretation.question_type = QuestionType.LOGIC
                interpretation.question_content = user_action
            elif quick_func == InternalVoiceFunction.SOLUTION:
                interpretation.predicament_description = user_action
                interpretation.goal_relevance = current_goal
            elif quick_func == InternalVoiceFunction.MEMORY:
                interpretation.memory_trigger = user_action
            elif quick_func == InternalVoiceFunction.TASK_REMINDER:
                interpretation.task_drift_detected = True
                interpretation.drift_severity = "moderate"
            
            # Track for anti-repetition
            self._track_function(quick_func)
            
            return interpretation
        
        # SLOW PATH: Use LLM for ambiguous cases
        # Build context for analysis
        memories_text = "\n".join(f"- {m}" for m in (available_memories or [])[:5])
        recent_funcs = [f.value for f in self.recent_functions[-3:]]
        
        prompt = f"""Analyze this situation to determine the most relevant internal voice function.

**SCENE:**
{scene_description}

**USER ACTION:**
{user_action}

**ACTION OUTCOME:**
{action_outcome}

**ACTOR STATE:**
- Stamina: {actor_state.get('stamina', 'Unknown')}
- Spirit: {actor_state.get('spirit', 'Unknown')}
- Mood: {actor_state.get('mood', 'Unknown')}
- Stress: {actor_state.get('stress', 'Unknown')}

**CURRENT GOAL:** {current_goal or 'None'}
**CURRENT TASK:** {current_task or 'None'}

**AVAILABLE MEMORIES:**
{memories_text if memories_text else 'None loaded'}

**RECENT INTERNAL VOICE FUNCTIONS (avoid repetition):**
{', '.join(recent_funcs) if recent_funcs else 'None'}

**IS THIS AN INQUIRY (USER ASKING A QUESTION)?** {is_inquiry}

**INTERNAL VOICE FUNCTIONS:**

1. **INFORMATION** - Use when:
   - User is asking a direct question about identity, relationships, or facts
   - Questions like "Who is my best friend?", "What is my goal?", "Is this my office?"
   - Two types:
     * LOGIC: Factual questions with known answers (friend, family, boss, work)
     * CONCEPTUAL: Abstract questions requiring thought (Should I kill him? What's the meaning?)
   - PRIORITY: If user is asking a question, this should usually be selected

2. **SOLUTION** - Use when:
   - Actor is in a predicament or difficult situation
   - There's a problem that needs solving
   - The current situation blocks progress toward goal
   - Examples: trapped, lost, facing danger, stuck on a problem
   - Should suggest an idea to get closer to the goal

3. **MEMORY** - Use when:
   - Something in the scene triggers a memory association
   - A person, place, or object reminds of something
   - An emotional moment connects to past experiences
   - Categories: family, job, friends, trauma, achievement, relationship, location, etc.

4. **COMMENT** - Use when:
   - None of the above are strongly relevant
   - Adding personality flavor to the moment
   - Reacting to the situation with characteristic thoughts
   - This is the DEFAULT - internal voice should never be silent

5. **TASK_REMINDER** - Use when:
   - User is drifting away from their current goal or task
   - The action doesn't relate to what they came here to do
   - They seem distracted or off-track
   - Should feel like suddenly remembering: "Wait, wasn't I supposed to...?"
   - Examples: chatting when they should be searching, exploring when they should be meeting someone
   - PRIORITY: If there's an active goal and user is off-task, this takes precedence over COMMENT

**SELECTION PRIORITY:**
1. If user is asking a question → INFORMATION
2. If in a predicament/danger → SOLUTION
3. If user is drifting from goal/task → TASK_REMINDER
4. If something triggers a memory → MEMORY
5. Otherwise → COMMENT (personality flavor)

**AVOID REPETITION:**
- Don't select the same function 2 times in a row
- If recent functions are [{', '.join(recent_funcs)}], prefer a different one unless strongly warranted

**Response Format:**
Return JSON:

{{
    "primary_function": "memory/comment/solution/information/task_reminder",
    "secondary_function": "optional second function or null",
    "question_type": "logic/conceptual/identity (if INFORMATION)",
    "question_content": "the question being answered (if INFORMATION)",
    "memory_trigger": "what triggered the memory (if MEMORY)",
    "memory_category": "family/job/friends/trauma/etc (if MEMORY)",
    "predicament_description": "the problem to solve (if SOLUTION)",
    "goal_relevance": "how solution relates to goal (if SOLUTION)",
    "task_drift_detected": true/false (if TASK_REMINDER),
    "drift_severity": "mild/moderate/severe (if TASK_REMINDER)",
    "urgency": "calm/normal/urgent/frantic",
    "reasoning": "Brief explanation of why this function was selected"
}}
"""
        
        try:
            response = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=OpenRouterConfig.get_model_for_role("coordination"),
                temperature=0.3,
                max_tokens=500,
                call_name="INTERNAL_VOICE_INTERPRET"
            )
            
            result = extract_and_parse_json(response)
            
            if not result:
                # Default to COMMENT if parsing fails
                return self._create_default_interpretation(user_action, is_inquiry)
            
            # Parse function
            func_str = result.get("primary_function", "comment").lower()
            try:
                primary_func = InternalVoiceFunction(func_str)
            except ValueError:
                primary_func = InternalVoiceFunction.COMMENT
            
            # Parse secondary function
            secondary_func = None
            if result.get("secondary_function"):
                try:
                    secondary_func = InternalVoiceFunction(result["secondary_function"].lower())
                except ValueError:
                    pass
            
            # Parse question type
            question_type = None
            if result.get("question_type"):
                try:
                    question_type = QuestionType(result["question_type"].lower())
                except ValueError:
                    pass
            
            interpretation = VoiceInterpretation(
                primary_function=primary_func,
                secondary_function=secondary_func,
                question_type=question_type,
                question_content=result.get("question_content"),
                memory_trigger=result.get("memory_trigger"),
                memory_category=result.get("memory_category"),
                predicament_description=result.get("predicament_description"),
                goal_relevance=result.get("goal_relevance"),
                task_drift_detected=result.get("task_drift_detected", False),
                drift_severity=result.get("drift_severity", "mild"),
                urgency=result.get("urgency", "normal"),
                reasoning=result.get("reasoning", "")
            )
            
            # Track this function
            self._track_function(primary_func)
            
            return interpretation
            
        except Exception as e:
            self.logger.error(f"Error interpreting situation: {e}")
            return self._create_default_interpretation(user_action, is_inquiry)
    
    def _create_default_interpretation(self, user_action: str, is_inquiry: bool) -> VoiceInterpretation:
        """Create a default interpretation when analysis fails"""
        # If it's an inquiry, default to INFORMATION
        if is_inquiry:
            return VoiceInterpretation(
                primary_function=InternalVoiceFunction.INFORMATION,
                question_type=QuestionType.LOGIC,
                question_content=user_action,
                urgency="normal",
                reasoning="Default to information for inquiry"
            )
        
        # Otherwise default to COMMENT
        return VoiceInterpretation(
            primary_function=InternalVoiceFunction.COMMENT,
            urgency="normal",
            reasoning="Default to personality comment"
        )
    
    def _track_function(self, func: InternalVoiceFunction):
        """Track recent functions to avoid repetition"""
        self.recent_functions.append(func)
        if len(self.recent_functions) > self.max_recent_history:
            self.recent_functions.pop(0)
    
    def _track_topic(self, topic: str):
        """Track recent topics to avoid repetition"""
        self.recent_topics.append(topic.lower())
        if len(self.recent_topics) > self.max_recent_topics:
            self.recent_topics.pop(0)
    
    def is_topic_recent(self, topic: str) -> bool:
        """Check if a topic was recently used"""
        return topic.lower() in self.recent_topics
    
    def get_anti_repetition_guidance(self) -> str:
        """Get guidance for avoiding repetition"""
        recent_funcs = [f.value for f in self.recent_functions[-3:]]
        recent_topics = self.recent_topics[-5:]
        
        guidance = []
        
        if recent_funcs:
            guidance.append(f"Recent functions used: {', '.join(recent_funcs)}")
            
            # Check for repetition
            if len(recent_funcs) >= 2 and len(set(recent_funcs[-2:])) == 1:
                guidance.append(f"WARNING: {recent_funcs[-1]} used twice in a row - strongly prefer different function")
        
        if recent_topics:
            guidance.append(f"Recent topics: {', '.join(recent_topics)}")
            guidance.append("Avoid these topics unless directly relevant")
        
        return "\n".join(guidance) if guidance else "No repetition concerns"
    
    def quick_classify(self, user_input: str, context: str = "") -> Tuple[Optional[InternalVoiceFunction], float]:
        """
        Quick classification without full LLM call.
        
        Uses heuristics for common patterns. Returns (function, confidence).
        If confidence is below threshold, caller should use LLM instead.
        
        Returns:
            Tuple of (InternalVoiceFunction or None, confidence 0.0-1.0)
            - High confidence (0.8+): Strong keyword match, safe to use
            - Medium confidence (0.5-0.8): Possible match, LLM recommended
            - Low confidence (<0.5): No match, must use LLM
        """
        input_lower = user_input.lower()
        
        # Check for questions (INFORMATION) - HIGH confidence if clear question
        question_starters = ["who ", "what ", "where ", "when ", "why ", "how ", "is ", "are ", "do ", "does ", "can ", "should "]
        if any(input_lower.startswith(w) for w in question_starters) and "?" in user_input:
            return (InternalVoiceFunction.INFORMATION, 0.95)  # Very confident - starts with question word AND has ?
        elif "?" in user_input:
            return (InternalVoiceFunction.INFORMATION, 0.85)  # Confident - has question mark
        elif any(input_lower.startswith(w) for w in question_starters):
            return (InternalVoiceFunction.INFORMATION, 0.7)   # Medium - starts with question word but no ?
        
        # Check for predicament keywords (SOLUTION) - confidence based on keyword strength
        strong_predicament = ["stuck", "trapped", "can't escape", "no way out", "impossible to"]
        medium_predicament = ["can't", "cannot", "help me", "how do i", "what should i"]
        
        if any(phrase in input_lower for phrase in strong_predicament):
            return (InternalVoiceFunction.SOLUTION, 0.9)
        elif any(phrase in input_lower for phrase in medium_predicament):
            return (InternalVoiceFunction.SOLUTION, 0.7)
        
        # Check for memory triggers (MEMORY) - confidence based on explicitness
        strong_memory = ["i remember", "reminds me of", "just like when", "back when i", "used to be"]
        medium_memory = ["remember", "remind", "familiar", "like before"]
        
        if any(phrase in input_lower for phrase in strong_memory):
            return (InternalVoiceFunction.MEMORY, 0.9)
        elif any(word in input_lower for word in medium_memory):
            return (InternalVoiceFunction.MEMORY, 0.6)
        
        # No confident match - return None to signal LLM should be used
        return (None, 0.0)
    
    def detect_task_drift(self, user_action: str, current_goal: str) -> Tuple[bool, str]:
        """
        Detect if user action drifts from current goal/task.
        
        Returns (is_drifting, severity)
        - is_drifting: True if action doesn't align with goal
        - severity: "mild", "moderate", or "severe"
        
        Examples:
        - Goal: "find the documents", Action: "chat with guard" → drifting
        - Goal: "meet Sarah at 3pm", Action: "explore the park" → drifting
        """
        if not current_goal or not user_action:
            return False, "none"
        
        action_lower = user_action.lower()
        goal_lower = current_goal.lower()
        
        # Extract key goal keywords (nouns/verbs)
        goal_keywords = self._extract_goal_keywords(goal_lower)
        
        # Check if action relates to any goal keywords
        relevance_score = 0
        for keyword in goal_keywords:
            if keyword in action_lower:
                relevance_score += 1
        
        # Calculate relevance percentage
        if goal_keywords:
            relevance_pct = relevance_score / len(goal_keywords)
        else:
            relevance_pct = 0.5  # Default if no keywords extracted
        
        # Determine drift based on relevance
        if relevance_pct >= 0.6:
            return False, "none"  # Action aligns with goal
        elif relevance_pct >= 0.3:
            return True, "mild"  # Partially aligned
        elif relevance_pct >= 0.1:
            return True, "moderate"  # Weak alignment
        else:
            return True, "severe"  # No alignment, clearly off-task
    
    def _extract_goal_keywords(self, goal: str) -> List[str]:
        """Extract important keywords from a goal string."""
        # Common stop words to filter out
        stop_words = {
            'the', 'a', 'an', 'to', 'for', 'of', 'in', 'at', 'by', 'with', 
            'and', 'or', 'but', 'is', 'are', 'was', 'were', 'be', 'been',
            'my', 'your', 'his', 'her', 'their', 'our', 'this', 'that',
            'i', 'you', 'he', 'she', 'they', 'we', 'it', 'me', 'him', 'them'
        }
        
        # Split goal into words and filter
        words = re.findall(r'\b\w+\b', goal.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]
        
        # Include compound phrases (like "find document" or "meet sarah")
        if len(words) >= 2:
            for i in range(len(words)-1):
                compound = f"{words[i]} {words[i+1]}"
                if words[i] not in stop_words or words[i+1] not in stop_words:
                    keywords.append(compound)
        
        return list(set(keywords))  # Remove duplicates
    
    def determine_urgency(self, 
                         mood_state: Dict[str, Any],
                         action_outcome: str,
                         scene_context: str) -> str:
        """
        Determine the urgency level for internal voice.
        
        Based on mood and situation.
        """
        # Check mood intensity
        mood_intensity = mood_state.get("intensity", "moderate")
        stress_level = mood_state.get("stress_level", 5)
        
        # Check for danger keywords
        danger_words = ["danger", "attack", "hurt", "pain", "blood", "gun", "knife", "death", "dying"]
        is_dangerous = any(word in scene_context.lower() or word in action_outcome.lower() 
                          for word in danger_words)
        
        # Determine urgency
        if is_dangerous or stress_level >= 8 or mood_intensity == "overwhelming":
            return "frantic"
        elif stress_level >= 6 or mood_intensity == "strong":
            return "urgent"
        elif stress_level <= 2 or mood_intensity == "subtle":
            return "calm"
        else:
            return "normal"


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global instance
_interpreter_agent: Optional[InternalVoiceInterpreterAgent] = None


def get_voice_interpreter() -> InternalVoiceInterpreterAgent:
    """Get or create the global interpreter agent"""
    global _interpreter_agent
    if _interpreter_agent is None:
        _interpreter_agent = InternalVoiceInterpreterAgent()
    return _interpreter_agent


def interpret_for_voice(scene_description: str,
                       user_action: str,
                       action_outcome: str,
                       actor_state: Dict[str, Any],
                       personality_context: str = "",
                       current_goal: str = "",
                       is_inquiry: bool = False) -> VoiceInterpretation:
    """Convenience function to interpret situation for internal voice"""
    interpreter = get_voice_interpreter()
    return interpreter.interpret_situation(
        scene_description=scene_description,
        user_action=user_action,
        action_outcome=action_outcome,
        actor_state=actor_state,
        personality_context=personality_context,
        current_goal=current_goal,
        is_inquiry=is_inquiry
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Internal Voice Interpreter Agent Test\n")
    
    interpreter = InternalVoiceInterpreterAgent()
    
    # Test scenarios
    test_cases = [
        {
            "name": "Question about identity",
            "scene": "You're in your apartment",
            "action": "Who is my best friend?",
            "outcome": "",
            "is_inquiry": True
        },
        {
            "name": "Dangerous situation",
            "scene": "You're falling toward a pit of lava",
            "action": "I try to grab something",
            "outcome": "You're still falling",
            "is_inquiry": False
        },
        {
            "name": "Memory trigger",
            "scene": "You see a kind elderly lady at the park",
            "action": "I watch her feed the pigeons",
            "outcome": "She smiles warmly",
            "is_inquiry": False
        },
        {
            "name": "Normal situation",
            "scene": "You're walking down the street",
            "action": "I keep walking",
            "outcome": "You continue on your way",
            "is_inquiry": False
        }
    ]
    
    actor_state = {
        "stamina": 4,
        "spirit": 3,
        "mood": "anxious",
        "stress": 6
    }
    
    print("=== Interpretation Tests ===\n")
    
    for test in test_cases:
        print(f"Test: {test['name']}")
        print(f"  Scene: {test['scene'][:50]}...")
        print(f"  Action: {test['action']}")
        
        result = interpreter.interpret_situation(
            scene_description=test["scene"],
            user_action=test["action"],
            action_outcome=test["outcome"],
            actor_state=actor_state,
            personality_context="",
            is_inquiry=test["is_inquiry"]
        )
        
        print(f"  → Function: {result.primary_function.value}")
        print(f"  → Urgency: {result.urgency}")
        print(f"  → Reasoning: {result.reasoning[:80]}...")
        print()
    
    print("✅ Internal Voice Interpreter Agent ready!")
