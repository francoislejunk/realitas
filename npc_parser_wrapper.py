"""
NPC Parser Wrapper - Automatically parse narrative for NPCs

This module provides a wrapper function that automatically runs the NPC parser
on any narrative output to detect and spawn mentioned NPCs.
"""

from typing import Optional, List
from color_utils import Color


def parse_narrative_for_npcs(
    narrative_text: str,
    available_npcs: List,
    actor_generator,
    scene_id: str,
    suppress_debug: bool = False
) -> int:
    """
    Parse narrative text for NPCs and auto-spawn them.
    
    This should be called after ANY narrative output to ensure NPCs mentioned
    in generated text are automatically detected and made available for interaction.
    
    Args:
        narrative_text: The narrative text to parse
        available_npcs: List of currently available NPCs
        actor_generator: Actor generator instance
        scene_id: Current scene ID
        suppress_debug: Whether to suppress debug output
        
    Returns:
        Number of NPCs spawned
    """
    if not narrative_text or len(narrative_text.strip()) < 20:
        return 0
    
    try:
        from scene_npc_parser import auto_spawn_scene_npcs
        
        spawned_count = auto_spawn_scene_npcs(
            scene_description=narrative_text,
            creator_agent=actor_generator,
            available_npcs=available_npcs,
            continuity_validator=None,  # Not available in wrapper context
            auto_memory_creator=None,  # Not available in wrapper context
            actor_name="Unknown",  # Not available in wrapper context
            scene_id=scene_id
        )
        
        if spawned_count > 0 and not suppress_debug:
            print(f"{Color.SUCCESS}[NPC PARSER] Auto-spawned {spawned_count} NPC(s) from narrative{Color.RESET}")
        
        return spawned_count
        
    except Exception as e:
        if not suppress_debug:
            print(f"{Color.WARNING}[NPC PARSER] Auto-spawn failed: {e}{Color.RESET}")
        return 0


def display_narrative_with_npc_parsing(
    narrative_text: str,
    available_npcs: List,
    actor_generator,
    scene_id: str,
    color=None,
    suppress_debug: bool = False
) -> int:
    """
    Display narrative and automatically parse for NPCs.
    
    This is a convenience function that combines display and parsing.
    
    Args:
        narrative_text: The narrative text to display and parse
        available_npcs: List of currently available NPCs
        actor_generator: Actor generator instance
        scene_id: Current scene ID
        color: Color to use for display (defaults to Color.NARRATIVE)
        suppress_debug: Whether to suppress debug output
        
    Returns:
        Number of NPCs spawned
    """
    if color is None:
        color = Color.NARRATIVE
    
    # Display the narrative
    print(f"{color}{narrative_text}{Color.RESET}")
    
    # Parse for NPCs
    return parse_narrative_for_npcs(
        narrative_text=narrative_text,
        available_npcs=available_npcs,
        actor_generator=actor_generator,
        scene_id=scene_id,
        suppress_debug=suppress_debug
    )
