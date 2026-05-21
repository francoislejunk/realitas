"""
Sympathy Initialization Utility

Simple utility to assign initial sympathies between actors using LLM analysis.
Can be called from main.py or other parts of the system when needed.
"""

import json
from typing import List, Dict, Any
from openrouter_config import OpenRouterConfig
from actors import Actor
from narrative_utils import get_generic_descriptor


def _safe_display_name(actor: Actor) -> str:
    try:
        nm = getattr(getattr(actor, 'sheet', None), 'name', None)
        if not nm:
            return str(actor)
        try:
            if getattr(getattr(actor, 'sheet', None), 'is_user_actor', False):
                return str(nm)
        except Exception:
            pass
        try:
            from stranger_description_system import known_actors_tracker
            if known_actors_tracker is not None and known_actors_tracker.is_name_known(str(nm)):
                return str(nm)
        except Exception:
            pass
        ka = getattr(getattr(actor, 'sheet', None), 'known_as', None)
        if ka:
            return str(ka)
        pd = getattr(getattr(actor, 'sheet', None), 'public_description', None)
        if pd:
            return str(pd)
        return "someone"
    except Exception:
        return "someone"

def assign_initial_sympathies(actors: List[Actor], sympathy_manager=None, context_text: str = "") -> None:
    """
    Use LLM to assign realistic initial sympathies between actors.
    Simple utility function that can be called when needed.
    
    Args:
        actors: List of actors to analyze for initial relationships
        sympathy_manager: Optional sympathy manager to apply results to
        context_text: Optional narrative context (e.g. "Inge is my best friend") to inform analysis
    """
    if len(actors) < 2:
        print("Need at least 2 actors for sympathy analysis")
        return
    
    print(f"\n🧠 Analyzing Initial Relationships with LLM...")
    print(f"Actors: {', '.join(_safe_display_name(actor) for actor in actors)}")
    
    try:
        # Create LLM client
        client = OpenRouterConfig.create_role_client("data_management")
        
        from actor_sheet import SFactorType
        actor_profiles = []
        for actor in actors:
            profile = {
                "name": actor.sheet.name,
                "occupation": actor.sheet.occupation,
                "personality_traits": dict(actor.sheet.personality_traits),
                "goals": actor.sheet.goals[:3],
                "s_factors": {
                    "swiftness": actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS),
                    "sociability": actor.sheet.s_factors.get_factor(SFactorType.SOCIABILITY),
                    "sturdiness": actor.sheet.s_factors.get_factor(SFactorType.STURDINESS),
                    "smarts": actor.sheet.s_factors.get_factor(SFactorType.SMARTS),
                    "shadow": actor.sheet.s_factors.get_factor(SFactorType.SHADOW)
                }
            }
            actor_profiles.append(profile)
        
        # Create prompt
        prompt = _create_sympathy_prompt(actor_profiles, context_text)
        
        # Call LLM with timeout and retry handling
        max_retries = 3
        timeout_seconds = 30
        
        for attempt in range(max_retries):
            try:
                print(f"DEBUG SYMPATHY: Attempting LLM call (attempt {attempt + 1}/{max_retries})")
                response = client.chat.completions.create(
                    model=OpenRouterConfig.get_model_for_role("record_keeping"),
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a relationship dynamics expert analyzing initial impressions between characters. Provide realistic, nuanced assessments based on personality compatibility, goals, and social dynamics."
                        },
                        {
                            "role": "user", 
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                    timeout=timeout_seconds
                )
                break  # Success, exit retry loop
                
            except Exception as e:
                print(f"DEBUG SYMPATHY: LLM call failed on attempt {attempt + 1}: {e}")
                if attempt == max_retries - 1:
                    # Final attempt failed, use fallback
                    print(f"DEBUG SYMPATHY: All attempts failed, using neutral sympathies")
                    _assign_neutral_sympathies(actors)
                    return
                else:
                    print(f"DEBUG SYMPATHY: Retrying in 2 seconds...")
                    import time
                    time.sleep(2)
        
        response_text = response.choices[0].message.content
        _parse_and_apply_sympathies(actors, response_text)
        
    except Exception as e:
        print(f"Warning: LLM sympathy analysis failed: {e}")
        print("Actors will start with neutral (0) sympathies")

def _create_sympathy_prompt(actor_profiles: List[Dict], context_text: str = "") -> str:
    """Create LLM prompt for sympathy analysis"""
    
    sympathy_descriptors = {
        -5: "Superb Reverse (Maximum hostility/hatred)",
        -4: "Extraordinary Reverse (Strong hostility)", 
        -3: "Average Reverse (Significant dislike)",
        -2: "Subpar Reverse (Moderate dislike)",
        -1: "Minimal Reverse (Minor dislike)",
        0: "Null (True neutrality - no feelings either way)",
        1: "Minimal (Minor friendship/liking)",
        2: "Subpar (Moderate friendship)",
        3: "Average (Good friendship)",
        4: "Extraordinary (Strong friendship)",
        5: "Superb (Maximum friendship/love)"
    }
    
    descriptor_list = "\n".join([f"{value}: {desc}" for value, desc in sympathy_descriptors.items()])
    
    context_section = ""
    if context_text:
        context_section = f"""
NARRATIVE CONTEXT (CRITICAL - MAY CONTAIN RELATIONSHIP DETAILS):
{context_text}
"""

    return f"""
Analyze initial sympathy relationships between these characters based on their profiles and context:

ACTOR PROFILES:
{json.dumps(actor_profiles, indent=2)}
{context_section}
SYMPATHY SCALE (-5 to +5):
{descriptor_list}

ANALYSIS GUIDELINES:
- Check NARRATIVE CONTEXT first! If it says "best friend", "enemy", etc., match that intensity.
- Most strangers start near 0 (neutral) unless strong reasons exist
- Strong values (±4/±5) should be rare and well-justified unless context dictates otherwise
- Consider personality compatibility, goal alignment, social dynamics
- Factor in occupational relationships and moral alignment
- Remember this is INITIAL sympathy - can change through interactions

Respond with JSON array of relationships:
[
  {{"from": "Actor A", "to": "Actor B", "value": 0, "reason": "explanation"}},
  {{"from": "Actor B", "to": "Actor A", "value": 1, "reason": "explanation"}}
]

Analyze ALL possible actor pairs (both directions):
"""

def _parse_and_apply_sympathies(actors: List[Actor], response_text: str) -> None:
    """Parse LLM response and apply sympathy values"""
    try:
        start_idx = response_text.find('[')
        end_idx = response_text.rfind(']') + 1
        
        if start_idx == -1 or end_idx == 0:
            raise ValueError("No JSON array found in response")
        
        json_str = response_text[start_idx:end_idx]
        relationships = json.loads(json_str)
        
        actor_lookup = {actor.sheet.name: actor for actor in actors}
        display_lookup = {actor.sheet.name: _safe_display_name(actor) for actor in actors}
        
        print(f"\n🤖 Applying LLM-Generated Initial Sympathies:")
        print("=" * 50)
        
        for rel in relationships:
            from_name = rel.get('from', '')
            to_name = rel.get('to', '')
            value = int(rel.get('value', 0))
            reason = rel.get('reason', 'No reason provided')
            
            value = max(-5, min(5, value))
            
            if from_name in actor_lookup and to_name in actor_lookup:
                actor = actor_lookup[from_name]
                
                if value != 0:
                    actor.sheet.update_sympathy(to_name, value, "Initial LLM Analysis")
                
                descriptor = get_generic_descriptor(value)
                disp_from = display_lookup.get(from_name, from_name)
                disp_to = display_lookup.get(to_name, to_name)
                print(f"  {disp_from} → {disp_to}: {value:+2d} ({descriptor})")
                print(f"    Reasoning: {reason[:80]}{'...' if len(reason) > 80 else ''}")
                print()
        
        print(f"✅ Applied {len(relationships)} initial relationship dynamics!")
        
    except Exception as e:
        print(f"Warning: Failed to parse LLM sympathy response: {e}")
        print("Actors will start with neutral (0) sympathies")

def _assign_neutral_sympathies(actors: List[Actor]) -> None:
    """Fallback function to assign neutral sympathies when LLM fails."""
    print(f"\n🔄 Using Neutral Sympathies (Fallback):")
    print("=" * 50)
    
    for actor in actors:
        for other_actor in actors:
            if actor != other_actor:
                # All actors start with neutral (0) sympathy
                print(f"  {_safe_display_name(actor)} → {_safe_display_name(other_actor)}: +0 (Null - True neutrality)")
    
    print(f"✅ Applied neutral sympathies for {len(actors)} actors!")
