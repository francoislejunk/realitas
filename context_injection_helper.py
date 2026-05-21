"""
Context Injection Helper

Provides utility functions to inject persistent context into LLM prompts.
This ensures LLMs NEVER forget where we are or what's happening.
"""

from persistent_context_manager import get_context_manager
from typing import Optional


def inject_context_into_prompt(prompt: str, priority: str = "high") -> str:
    """
    Inject persistent context into an LLM prompt.
    
    Args:
        prompt: The original prompt
        priority: "critical" (location, NPCs), "high" (events, opportunities), 
                 "medium" (atmosphere), "low" (ambient details)
    
    Returns:
        Enhanced prompt with context
    """
    context_manager = get_context_manager()
    context = context_manager.get_context()
    
    # Build context section based on priority
    context_section = _build_context_section(context, priority)
    
    # Inject at the beginning of the prompt
    enhanced_prompt = f"""
{context_section}

{prompt}

**CRITICAL REMINDER:**
- Current location: {context.current_location}
- Present NPCs: {', '.join(context.present_npcs) if context.present_npcs else 'None'}
- DO NOT revert to initial scene
- DO NOT forget where we are
- DO NOT mention NPCs who aren't present
"""
    
    return enhanced_prompt


def _build_context_section(context, priority: str) -> str:
    """Build context section based on priority level"""
    
    # CRITICAL: Always include location and NPCs
    critical_context = f"""
**CURRENT CONTEXT (NEVER FORGET THIS):**

**Location:** {context.current_location}
**Present NPCs:** {', '.join(context.present_npcs) if context.present_npcs else 'None'}
"""
    
    if priority == "critical":
        return critical_context
    
    # HIGH: Add scene, events, opportunities
    high_context = critical_context + f"""
**Scene:** {context.current_scene_description[:300]}...

**Recent Events:**
{chr(10).join(f'  - {e}' for e in context.recent_events[-3:]) if context.recent_events else '  - None'}

**Available Opportunities:**
{chr(10).join(f'  - {o}' for o in context.opportunities) if context.opportunities else '  - None'}

**Visible Objects:**
{chr(10).join(f'  - {obj}' for obj in context.visible_objects) if context.visible_objects else '  - None'}
"""
    
    if priority == "high":
        return high_context
    
    # MEDIUM: Add atmosphere and time
    medium_context = high_context + f"""
**Atmosphere:** {context.location_atmosphere}
**Time:** {context.time_of_day}, {context.weather}
**Narrative Mode:** {context.narrative_mode} ({context.narrative_tone})
"""
    
    if priority == "medium":
        return medium_context
    
    # LOW: Add all details
    low_context = medium_context + f"""
**User's Last Action:** {context.user_last_action}
**User's Intent:** {context.user_last_intent}
**User's Goal:** {context.user_current_goal}
**User's Task:** {context.user_current_task}

**Ambient Details:**
  - Sounds: {', '.join(context.ambient_sounds) if context.ambient_sounds else 'None'}
  - Smells: {', '.join(context.ambient_smells) if context.ambient_smells else 'None'}
  - Lighting: {context.lighting_conditions}
"""
    
    return low_context


def get_context_for_narrator() -> str:
    """Get context specifically formatted for narrator prompts"""
    context_manager = get_context_manager()
    context = context_manager.get_context()
    
    return f"""
**NARRATIVE CONTEXT:**

You are narrating events in: {context.current_location}

**Scene Description:**
{context.current_scene_description}

**Who's Present:**
{', '.join(context.present_npcs) if context.present_npcs else 'No one else is here'}

**Recent Events (for continuity):**
{chr(10).join(f'  {i+1}. {e}' for i, e in enumerate(context.recent_events[-3:])) if context.recent_events else '  None'}

**Atmosphere:** {context.location_atmosphere}
**Time:** {context.time_of_day}, {context.weather}

**CRITICAL CONSTRAINTS:**
- Only describe what's in {context.current_location}
- Only mention NPCs who are present: {', '.join(context.present_npcs) if context.present_npcs else 'none'}
- Reference recent events to maintain continuity
- DO NOT describe the initial scene if we've moved
- DO NOT mention NPCs who have left
"""


def get_context_for_interpreter() -> str:
    """Get context specifically formatted for interpreter prompts"""
    context_manager = get_context_manager()
    context = context_manager.get_context()
    
    return f"""
**CURRENT SITUATION:**

**Location:** {context.current_location}
**Available NPCs:** {', '.join(context.present_npcs) if context.present_npcs else 'None'}
**Visible Objects:** {', '.join(context.visible_objects) if context.visible_objects else 'None'}
**Opportunities:** {', '.join(context.opportunities) if context.opportunities else 'None'}

**Recent Context:**
{chr(10).join(f'  - {e}' for e in context.recent_events[-2:]) if context.recent_events else '  - None'}

**INTERPRETATION CONSTRAINTS:**
- User can only interact with NPCs who are present
- User can only use objects that are visible
- User can only access opportunities that are available
- Consider the current location when interpreting actions
"""


def get_context_for_conductor() -> str:
    """Get context specifically formatted for conductor/scene generation prompts"""
    context_manager = get_context_manager()
    context = context_manager.get_context()
    
    return f"""
**SCENE GENERATION CONTEXT:**

**Current Location:** {context.current_location}
**Previous Scene:** {context.current_scene_description[:200]}...

**Continuity Requirements:**
- Maintain consistency with current location
- Reference recent events if relevant
- Keep NPCs who are present: {', '.join(context.present_npcs) if context.present_npcs else 'none'}
- Time: {context.time_of_day}, {context.weather}
- Atmosphere: {context.location_atmosphere}

**Recent Events (for continuity):**
{chr(10).join(f'  - {e}' for e in context.recent_events[-2:]) if context.recent_events else '  - None'}

**CRITICAL:**
- Generate scene for {context.current_location}, not the initial location
- Maintain continuity with what just happened
- Don't reset to the beginning
"""


def update_context_after_action(user_input: str, narrative: str, 
                                intent: Optional[str] = None,
                                confidence: float = 0.5):
    """
    Update context after a user action and narrative response.
    Call this after every turn.
    """
    context_manager = get_context_manager()
    
    # Save user action
    context_manager.update_user_action(
        action=user_input,
        intent=intent or "Unknown",
        confidence=confidence
    )
    
    # Save narrative
    context_manager.add_narrative(narrative)
    
    # Save event
    context_manager.add_event(f"User: {user_input}")


def update_context_after_scene_change(new_scene: str, location: str, location_label: str = ""):
    """
    Update context after scene changes (location move, scene refresh, etc.)
    Call this whenever scene_description changes.
    """
    context_manager = get_context_manager()
    
    # If location changed, clear NPCs
    if location != context_manager.context.current_location:
        context_manager.update_location(
            location=location,
            scene_description=new_scene,
            location_label=location_label
        )
    else:
        # Just update scene description
        context_manager.update_scene_description(new_scene)


def update_context_npcs(npc_names: list, npc_ids: list = None):
    """
    Update the list of present NPCs.
    Call this when NPCs are added/removed.
    """
    context_manager = get_context_manager()
    context_manager.set_npcs(npc_names, npc_ids or [])


def get_context_summary() -> str:
    """Get a human-readable summary of current context"""
    context_manager = get_context_manager()
    return context_manager.get_context_summary()


# === EXAMPLE USAGE ===

def example_narrator_usage():
    """Example: How to use context in narrator"""
    
    # Original prompt
    original_prompt = """
    Narrate the result of the user's action: "I look around"
    
    Generate a vivid, immersive description.
    """
    
    # Inject context
    enhanced_prompt = inject_context_into_prompt(original_prompt, priority="high")
    
    # Or use specialized function
    context_section = get_context_for_narrator()
    enhanced_prompt = f"{context_section}\n\n{original_prompt}"
    
    return enhanced_prompt


def example_interpreter_usage():
    """Example: How to use context in interpreter"""
    
    # Original prompt
    original_prompt = """
    Analyze this user input: "I talk to the man"
    
    Determine if this is a contested action or fallible action.
    """
    
    # Inject context
    context_section = get_context_for_interpreter()
    enhanced_prompt = f"{context_section}\n\n{original_prompt}"
    
    return enhanced_prompt


def example_update_after_turn():
    """Example: How to update context after a turn"""
    
    user_input = "I enter the diner"
    narrative = "You push through the door into the warm, coffee-scented interior..."
    intent = "Move to new location"
    
    # Update context
    update_context_after_action(
        user_input=user_input,
        narrative=narrative,
        intent=intent,
        confidence=0.9
    )
    
    # If scene changed
    new_scene = "The diner hums with activity..."
    update_context_after_scene_change(
        new_scene=new_scene,
        location="Rusty's Diner",
        location_label="diner"
    )


if __name__ == "__main__":
    print("Context Injection Helper - Example Usage")
    print("="*60)
    
    print("\n1. Narrator Prompt:")
    print(example_narrator_usage())
    
    print("\n2. Interpreter Prompt:")
    print(example_interpreter_usage())
    
    print("\n3. Context Summary:")
    print(get_context_summary())
