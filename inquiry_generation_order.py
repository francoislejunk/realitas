"""
Inquiry Generation Order System

Determines whether to generate perceptual description or internal voice first
based on whether the action is physical or mental.

PHILOSOPHY:
- Physical actions: Perception → Thought (you see/do something, then think about it)
- Mental actions: Thought → Perception (you think about something, then notice your body reacting)
"""

from typing import Literal

GenerationOrder = Literal["perception_first", "thought_first"]


def determine_generation_order(
    user_input: str,
    fallible_subtype: str,
    input_analysis: dict = None
) -> GenerationOrder:
    """
    Determine whether to generate perceptual description or internal voice first.
    
    Args:
        user_input: The user's input text
        fallible_subtype: The subtype from input analysis ('mental', 'inquiry', 'physical', 'social')
        input_analysis: Optional full input analysis dict for additional context
    
    Returns:
        "perception_first" for physical actions
        "thought_first" for mental actions
    
    Examples:
        Physical actions (perception first):
        - "Where am I?" → Look around, then recognize location
        - "What's that sound?" → Listen, then identify it
        - "Who is that person?" → Look at them, then recall/deduce
        - "Check the time" → Look at clock, then process the time
        - "Read the note" → See the text, then understand it
        
        Mental actions (thought first):
        - "I try to remember my best friend" → Think/recall, then notice yourself thinking
        - "What did I do last week?" → Search memory, then notice concentration
        - "Think about the plan" → Internal deliberation, then notice furrowed brow
        - "Recall the password" → Mental effort, then physical reaction
    """
    
    # Mental/inquiry actions are primarily internal
    if fallible_subtype in ['mental', 'inquiry']:
        # Check for explicit memory/recall keywords
        memory_keywords = [
            'remember', 'recall', 'think about', 'think of',
            'try to remember', 'what did i', 'what was',
            'my memory', 'i forgot', 'trying to recall'
        ]
        
        user_lower = user_input.lower()
        
        # If it's explicitly about recalling/remembering something → thought first
        if any(keyword in user_lower for keyword in memory_keywords):
            return "thought_first"
        
        # Questions about the external world → perception first (look around, then think)
        perception_questions = [
            'where am i', 'where are we', 'what is this place',
            'what\'s that', 'who is that', 'who\'s that',
            'what time', 'check time', 'look at',
            'what does', 'read', 'listen', 'hear',
            'see', 'smell', 'feel', 'taste'
        ]
        
        if any(q in user_lower for q in perception_questions):
            return "perception_first"
        
        # Default for mental/inquiry: thought first (internal processing)
        return "thought_first"
    
    # Physical and social actions: perception first (do something, then react)
    return "perception_first"


def generate_inquiry_outputs(
    narrator,
    user_input: str,
    actor,
    scene_description: str,
    narrative_context: str,
    time_context: dict,
    availability_context: dict,
    factual_knowledge: str = None,
    fallible_subtype: str = 'inquiry'
) -> tuple[str, str]:
    """
    Generate perceptual description and internal voice in the correct order.
    
    Returns:
        (perceptual_description, internal_voice) tuple
        
    The order of generation is determined by determine_generation_order(),
    but the return order is always the same for consistent unpacking.
    """
    
    order = determine_generation_order(user_input, fallible_subtype)
    
    if order == "thought_first":
        # Mental action: Generate internal voice first, then perceptual description
        internal_voice = narrator.generate_inquiry_internal_voice(
            ua_actor=actor,
            question=user_input,
            scene_description=scene_description,
            narrative_context=narrative_context,
            factual_knowledge=factual_knowledge,
            time_context=time_context,
            availability_context=availability_context
        )
        
        # Update scene with internal voice context for perceptual generation
        enhanced_scene = f"{scene_description}\n\nInternal thought: {internal_voice}"
        
        perceptual_description = narrator.generate_inquiry_response(
            user_question=user_input,
            ua_actor=actor,
            scene_description=enhanced_scene,
            narrative_context=narrative_context,
            current_time=time_context,
            availability_context=availability_context
        )
        
    else:
        # Physical action: Generate perceptual description first, then internal voice
        perceptual_description = narrator.generate_inquiry_response(
            user_question=user_input,
            ua_actor=actor,
            scene_description=scene_description,
            narrative_context=narrative_context,
            current_time=time_context,
            availability_context=availability_context
        )
        
        # Update scene with perceptual context for internal voice generation
        enhanced_scene = f"{scene_description}\n\n{perceptual_description}"
        
        internal_voice = narrator.generate_inquiry_internal_voice(
            ua_actor=actor,
            question=user_input,
            scene_description=enhanced_scene,
            narrative_context=narrative_context,
            factual_knowledge=factual_knowledge,
            time_context=time_context,
            availability_context=availability_context
        )
    
    return perceptual_description, internal_voice
