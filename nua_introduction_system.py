"""
NUA Introduction System - First Impression Narratives

Generates immersive "outlier" descriptions when NUAs are first encountered,
showing only what's immediately observable: S-traits (physical) and External Personality (demeanor).
"""

from color_utils import Color
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from actors import Actor

def generate_first_impression(actor: 'Actor', context: str = "") -> str:
    """
    Generates a narrative first impression of a NUA based on their S-traits and external personality.
    This is the "outlier" - what you notice immediately upon meeting someone.
    
    Args:
        actor: The NUA being introduced
        context: Optional context about how they were discovered
        
    Returns:
        Formatted narrative description
    """
    from actor_sheet import SFactorType
    
    # Get S-traits (physical appearance indicators)
    s_factors = actor.sheet.s_factors
    swiftness = s_factors.get_factor(SFactorType.SWIFTNESS)
    sociability = s_factors.get_factor(SFactorType.SOCIABILITY)
    sturdiness = s_factors.get_factor(SFactorType.STURDINESS)
    smarts = s_factors.get_factor(SFactorType.SMARTS)
    shadow = s_factors.get_factor(SFactorType.SHADOW)
    
    # Get external personality (demeanor)
    external_trait = actor.sheet.personality_traits.get('external', 'composed')
    
    # Get occupation for context
    occupation = actor.sheet.occupation
    
    # Build physical description from S-traits
    physical_descriptors = []
    
    # Swiftness (movement, agility)
    if swiftness >= 4:
        physical_descriptors.append("moves with quick, precise movements")
    elif swiftness >= 3:
        physical_descriptors.append("has a steady, capable bearing")
    elif swiftness >= 2:
        physical_descriptors.append("moves at a measured pace")
    else:
        physical_descriptors.append("moves slowly and deliberately")
    
    # Sturdiness (build, physical presence)
    if sturdiness >= 4:
        physical_descriptors.append("has a strong, imposing build")
    elif sturdiness >= 3:
        physical_descriptors.append("appears physically capable")
    elif sturdiness >= 2:
        physical_descriptors.append("has an average build")
    else:
        physical_descriptors.append("appears slight and fragile")
    
    # Shadow (presence, noticeability)
    if shadow >= 4:
        physical_descriptors.append("blends into the background effortlessly")
    elif shadow >= 3:
        physical_descriptors.append("has an understated presence")
    elif shadow >= 2:
        physical_descriptors.append("draws moderate attention")
    else:
        physical_descriptors.append("commands immediate attention")
    
    # Combine physical descriptors
    if len(physical_descriptors) >= 3:
        physical_desc = f"{physical_descriptors[0]}, {physical_descriptors[1]}, and {physical_descriptors[2]}"
    elif len(physical_descriptors) == 2:
        physical_desc = f"{physical_descriptors[0]} and {physical_descriptors[1]}"
    else:
        physical_desc = physical_descriptors[0] if physical_descriptors else "has a distinctive presence"
    
    # Build demeanor description from external personality
    demeanor_desc = f"Their demeanor is {external_trait.lower()}"
    
    # Add occupation hint if relevant
    occupation_hint = ""
    if occupation and occupation.lower() not in ['unknown', 'unemployed', 'none']:
        occupation_hint = f", suggesting they might be {_get_occupation_article(occupation)} {occupation.lower()}"
    
    # Construct the full first impression
    name = actor.sheet.name
    
    first_impression = f"""
{Color.NARRATIVE}You notice {name}. They {physical_desc}. {demeanor_desc}{occupation_hint}.{Color.RESET}
"""
    
    return first_impression.strip()


def _get_occupation_article(occupation: str) -> str:
    """Returns 'a' or 'an' based on occupation."""
    vowels = ['a', 'e', 'i', 'o', 'u']
    return 'an' if occupation[0].lower() in vowels else 'a'


def display_nua_introduction(actor: 'Actor', context: str = "") -> None:
    """
    Displays a formatted NUA introduction with first impression.
    
    Args:
        actor: The NUA being introduced
        context: Optional context about how they were discovered (e.g., "through investigation")
    """
    # Header
    if context:
        print(f"\n{Color.SUCCESS}✓ Discovered {context}: {actor.sheet.name}{Color.RESET}")
    else:
        print(f"\n{Color.SUCCESS}✓ {actor.sheet.name} appears{Color.RESET}")
    
    # First impression (outlier)
    first_impression = generate_first_impression(actor, context)
    print(first_impression)
    
    # Subtle hint about hidden abilities
    print(f"{Color.SYSTEM}(Their skills and abilities remain unknown until demonstrated){Color.RESET}\n")


def generate_llm_first_impression(actor: 'Actor', context: str = "", narrator_agent=None) -> str:
    """
    Uses the NarratorAgent to generate a more sophisticated first impression via LLM.
    Falls back to template-based generation if LLM fails.
    
    Args:
        actor: The NUA being introduced
        context: Optional context about discovery
        narrator_agent: Optional NarratorAgent for LLM generation
        
    Returns:
        Narrative first impression
    """
    if not narrator_agent:
        # Fallback to template-based
        return generate_first_impression(actor, context)
    
    try:
        from actor_sheet import SFactorType
        
        # Get S-traits
        s_factors = actor.sheet.s_factors
        swiftness = s_factors.get_factor(SFactorType.SWIFTNESS)
        sociability = s_factors.get_factor(SFactorType.SOCIABILITY)
        sturdiness = s_factors.get_factor(SFactorType.STURDINESS)
        smarts = s_factors.get_factor(SFactorType.SMARTS)
        shadow = s_factors.get_factor(SFactorType.SHADOW)
        
        # Get external personality
        external_trait = actor.sheet.personality_traits.get('external', 'composed')
        occupation = actor.sheet.occupation
        
        # Build LLM prompt
        prompt = f"""Generate a brief, naturally-embedded first impression description of a character you just encountered.

**Character Information:**
- Name: {actor.sheet.name}
- Occupation: {occupation}

**Observable Traits (S-Factors):**
- Swiftness: {swiftness}/5 (movement, agility)
- Sturdiness: {sturdiness}/5 (build, physical presence)
- Shadow: {shadow}/5 (noticeability - high = stealthy, low = attention-grabbing)

**Demeanor:**
- External Personality: {external_trait}

**Context:** {context if context else "You encounter them"}

**Instructions:**
- Write in SECOND PERSON ("You notice...", "A wiry man...", etc.)
- EMBED the physical traits and demeanor NATURALLY in the description
- DO NOT use formulaic structure like "They move X, have Y build, and Z demeanor"
- Focus ONLY on what you can see/sense immediately (appearance, movement, presence, demeanor)
- DO NOT mention skills, abilities, or internal thoughts
- Keep it brief (2-3 sentences maximum)
- Use present tense and vivid, atmospheric language
- Make it feel like natural narrative, not a character sheet

**Good Example (Natural):**
"A wiry man with a cigarette dangling from his lips pokes his head from the back room, squinting at you through a haze of smoke. His movements are cautious and deliberate, and there's something guarded in the way he sizes you up."

**Bad Example (Too Formulaic):**
"You notice Marcus Chen. He moves with quick, precise movements and has a strong, imposing build. His demeanor is confident and charismatic."

Generate the natural first impression:"""

        # Call LLM
        response = narrator_agent.client.chat.completions.create(
            model=narrator_agent.model,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
            max_tokens=150
        )
        
        llm_impression = response.choices[0].message.content.strip()
        
        # Validate response
        if llm_impression and len(llm_impression) > 20:
            return f"{Color.NARRATIVE}{llm_impression}{Color.RESET}"
        else:
            # Fallback to template
            return generate_first_impression(actor, context)
            
    except Exception as e:
        # Fallback to template on any error
        return generate_first_impression(actor, context)


def display_llm_nua_introduction(actor: 'Actor', context: str = "", narrator_agent=None) -> None:
    """
    Displays a formatted NUA introduction with LLM-generated first impression.
    
    Args:
        actor: The NUA being introduced
        context: Optional context about how they were discovered
        narrator_agent: Optional NarratorAgent for LLM generation
    """
    # Header
    if context:
        print(f"\n{Color.SUCCESS}✓ Discovered {context}: {actor.sheet.name}{Color.RESET}")
    else:
        print(f"\n{Color.SUCCESS}✓ {actor.sheet.name} appears{Color.RESET}")
    
    # First impression (outlier) - LLM or template
    first_impression = generate_llm_first_impression(actor, context, narrator_agent)
    print(f"\n{first_impression}")
    
    # Subtle hint about hidden abilities
    print(f"{Color.SYSTEM}(Their skills and abilities remain unknown until demonstrated){Color.RESET}\n")


# Configuration
USE_LLM_FOR_INTRODUCTIONS = True  # Set to False to use template-based only

def set_llm_introductions(enabled: bool) -> None:
    """Enable or disable LLM-based introductions."""
    global USE_LLM_FOR_INTRODUCTIONS
    USE_LLM_FOR_INTRODUCTIONS = enabled
