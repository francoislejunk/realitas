"""
Stranger Description System - Diegetic NUA Descriptions

When the UA encounters NPCs they don't know, we shouldn't use their names.
Instead, we describe them based on:
1. Visual appearance (S-traits like Sturdiness, Shapeliness)
2. Occupation (if visually obvious - uniform, badge, apron, etc.)
3. Distinguishing features (hair color, clothing, age)
4. Behavior/posture

This creates more immersive, realistic descriptions where the UA
perceives strangers the way a real person would.

Usage:
    from stranger_description_system import get_nua_description, StrangerDescriber
    
    # Check if we know them
    desc = get_nua_description(nua, ua_actor, relationship_system)
    # Returns "Doe" if known, or "a dark-haired waitress" if stranger
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# S-TRAIT BASED DESCRIPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Sturdiness descriptions (physical build)
STURDINESS_DESCRIPTIONS = {
    1: ["frail", "gaunt", "skeletal", "emaciated", "skin and bones", "wasted"],
    2: ["thin", "slight", "slender", "lean", "wiry", "scrawny"],
    3: ["average build", "medium build", "ordinary physique", "unremarkable build"],
    4: ["sturdy", "solid", "well-built", "muscular", "athletic", "fit"],
    5: ["massive", "hulking", "powerfully built", "imposing", "giant", "enormous"]
}

# Swiftness descriptions (movement/energy)
SWIFTNESS_DESCRIPTIONS = {
    1: ["sluggish", "lethargic", "slow-moving", "plodding"],
    2: ["unhurried", "deliberate", "measured"],
    3: ["normal pace", "steady"],
    4: ["quick", "nimble", "agile", "energetic"],
    5: ["lightning-fast", "incredibly quick", "darting", "hyperactive"]
}

# Smart descriptions (visible intelligence markers)
SMART_DESCRIPTIONS = {
    1: ["vacant-eyed", "confused-looking", "bewildered"],
    2: ["simple", "unassuming"],
    3: ["attentive", "alert"],
    4: ["sharp-eyed", "keen", "observant", "intelligent-looking"],
    5: ["piercing gaze", "calculating eyes", "intensely focused", "brilliant-looking"]
}

# Sociability descriptions (social presence/demeanor)
SOCIABILITY_DESCRIPTIONS = {
    1: ["withdrawn", "reclusive", "antisocial", "standoffish"],
    2: ["quiet", "reserved", "introverted"],
    3: ["approachable", "neutral demeanor"],
    4: ["friendly-looking", "warm", "personable", "engaging"],
    5: ["charismatic", "magnetic", "commanding presence", "captivating"]
}

# Shadow descriptions (darkness/moral ambiguity visible in demeanor)
SHADOW_DESCRIPTIONS = {
    1: ["innocent-looking", "guileless", "open-faced", "trusting"],
    2: ["earnest", "straightforward"],
    3: ["unreadable", "neutral expression"],
    4: ["guarded", "wary-eyed", "calculating", "secretive"],
    5: ["sinister", "menacing", "dark-eyed", "unsettling", "predatory"]
}


# ═══════════════════════════════════════════════════════════════════════════════
# OCCUPATION VISIBILITY
# ═══════════════════════════════════════════════════════════════════════════════

# Occupations that are visually obvious (uniform, equipment, context)
VISIBLE_OCCUPATIONS = {
    # Service industry
    "waitress": ["waitress", "server", "the waitress"],
    "waiter": ["waiter", "server", "the waiter"],
    "bartender": ["bartender", "the bartender"],
    "cook": ["cook", "chef", "the cook"],
    "barista": ["barista", "the barista"],
    
    # Uniformed professions
    "police": ["cop", "police officer", "officer", "the cop"],
    "security": ["security guard", "guard", "the guard"],
    "soldier": ["soldier", "military", "the soldier"],
    "firefighter": ["firefighter", "fireman", "the firefighter"],
    "paramedic": ["paramedic", "EMT", "the paramedic"],
    "nurse": ["nurse", "the nurse"],
    "doctor": ["doctor", "physician", "the doctor"],
    
    # Service workers
    "mechanic": ["mechanic", "the mechanic"],
    "janitor": ["janitor", "custodian", "the janitor"],
    "delivery": ["delivery person", "courier", "the delivery person"],
    
    # Retail
    "cashier": ["cashier", "clerk", "the cashier"],
    "shopkeeper": ["shopkeeper", "store owner", "the shopkeeper"],
    
    # Context-obvious
    "beggar": ["beggar", "homeless person", "vagrant", "the beggar"],
    "street vendor": ["vendor", "street vendor", "the vendor"],
    "bouncer": ["bouncer", "doorman", "the bouncer"],
    
    # Professional (if in context)
    "receptionist": ["receptionist", "the receptionist"],
    "secretary": ["secretary", "assistant", "the secretary"],
}

# Keywords that indicate visible occupation
OCCUPATION_KEYWORDS = {
    "apron": ["cook", "chef", "barista", "bartender"],
    "uniform": ["police", "security", "soldier", "nurse"],
    "badge": ["police", "security", "detective"],
    "scrubs": ["nurse", "doctor", "medical"],
    "hardhat": ["construction", "worker"],
    "suit": ["businessman", "executive", "professional"],
    "lab coat": ["doctor", "scientist", "researcher"],
}


# ═══════════════════════════════════════════════════════════════════════════════
# AGE DESCRIPTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def get_age_description(age: int) -> str:
    """Get age-appropriate description"""
    if age < 13:
        return "child"
    elif age < 20:
        return "teenager" if age < 18 else "young person"
    elif age < 30:
        return "young"
    elif age < 40:
        return "thirtyish"
    elif age < 50:
        return "middle-aged"
    elif age < 60:
        return "older"
    elif age < 70:
        return "elderly"
    else:
        return "aged"


def get_gender_noun(gender: str, age: int) -> str:
    """Get appropriate gender noun based on age"""
    gender_lower = (gender or "").lower()
    
    if age < 18:
        if gender_lower in ["male", "m", "man", "boy"]:
            return "boy" if age < 13 else "young man"
        elif gender_lower in ["female", "f", "woman", "girl"]:
            return "girl" if age < 13 else "young woman"
        else:
            return "youth"
    else:
        if gender_lower in ["male", "m", "man", "boy"]:
            return "man"
        elif gender_lower in ["female", "f", "woman", "girl"]:
            return "woman"
        else:
            return "person"


# ═══════════════════════════════════════════════════════════════════════════════
# STRANGER DESCRIBER CLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class StrangerDescription:
    """A generated description for a stranger"""
    short_desc: str          # "a hulking man" 
    article_desc: str        # "a hulking man" (with article)
    definite_desc: str       # "the hulking man" (with 'the')
    occupation_desc: str     # "the cook" (if visible)
    trait_highlights: List[str]  # Notable traits
    is_stranger: bool        # Whether they're actually a stranger


class KnownActorsTracker:
    """
    Tracks which NPC names the UA has learned.
    
    An NPC's name becomes known when:
    - They introduce themselves
    - Someone else introduces them
    - The UA asks their name and they respond
    - The UA reads their name (badge, sign, etc.)
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._known_names: set = set()
        return cls._instance
    
    def learn_name(self, npc_name: str) -> None:
        """Mark an NPC's name as known to the UA."""
        self._known_names.add(npc_name.lower())
        print(f"[STRANGER SYSTEM] UA learned name: {npc_name}")
    
    def is_name_known(self, npc_name: str) -> bool:
        """Check if the UA knows this NPC's name."""
        return npc_name.lower() in self._known_names
    
    def forget_name(self, npc_name: str) -> None:
        """Remove an NPC's name from known (for testing/reset)."""
        self._known_names.discard(npc_name.lower())
    
    def get_all_known_names(self) -> set:
        """Get all known NPC names."""
        return self._known_names.copy()
    
    def reset(self) -> None:
        """Clear all known names (for new game)."""
        self._known_names.clear()


# Global singleton instance
known_actors_tracker = KnownActorsTracker()


class StrangerDescriber:
    """
    Generates diegetic descriptions for NPCs based on whether the UA knows them.
    """
    
    def __init__(self, relationship_system=None):
        """
        Initialize with optional relationship system.
        
        Args:
            relationship_system: System that tracks UA-NUA relationships
        """
        self.relationship_system = relationship_system
        self._description_cache: Dict[str, StrangerDescription] = {}
        self.known_tracker = known_actors_tracker  # Use global tracker
    
    def is_stranger(self, ua_actor, nua_actor) -> bool:
        """
        Check if the NUA is a stranger to the UA.
        
        Returns True if the UA doesn't know the NPC's name.
        
        Name becomes known through:
        - Introduction (NPC says their name)
        - Someone else introduces them
        - UA asks and NPC responds
        - UA reads their name (badge, sign, etc.)
        """
        # Get NPC name
        nua_name = nua_actor.sheet.name if hasattr(nua_actor, 'sheet') else str(nua_actor)
        
        # PRIMARY CHECK: Has UA learned this NPC's name?
        if self.known_tracker.is_name_known(nua_name):
            return False  # Not a stranger - UA knows their name
        
        # FALLBACK: Check relationship system if available
        if self.relationship_system:
            try:
                ua_id = getattr(ua_actor, 'actor_id', None) or getattr(ua_actor.sheet, 'name', 'ua')
                nua_id = getattr(nua_actor, 'actor_id', None) or nua_name
                
                relationship = self.relationship_system.get_relationship(ua_id, nua_id)
                
                if relationship:
                    familiarity = relationship.get('familiarity', 0)
                    if familiarity >= 1:  # 1+ = acquaintance or better
                        return False
            except Exception:
                pass
        
        # Default: They're a stranger
        return True
    
    def get_description(self, nua_actor, ua_actor=None, 
                        context: str = "") -> StrangerDescription:
        """
        Get appropriate description for an NUA.
        
        If stranger: Returns trait-based description
        If known: Returns their name
        
        Args:
            nua_actor: The NUA to describe
            ua_actor: The UA (for relationship check)
            context: Scene context (helps determine visible occupation)
        """
        # Check cache first
        nua_id = getattr(nua_actor, 'actor_id', None) or id(nua_actor)
        cache_key = f"{nua_id}_{id(ua_actor)}"
        
        if cache_key in self._description_cache:
            return self._description_cache[cache_key]
        
        # Check if stranger
        is_stranger = self.is_stranger(ua_actor, nua_actor) if ua_actor else True
        
        if not is_stranger:
            # Known person - use their name
            name = nua_actor.sheet.name if hasattr(nua_actor, 'sheet') else str(nua_actor)
            desc = StrangerDescription(
                short_desc=name,
                article_desc=name,
                definite_desc=name,
                occupation_desc=name,
                trait_highlights=[],
                is_stranger=False
            )
            self._description_cache[cache_key] = desc
            return desc

        # Prefer persisted public/known-as description if present (stable across reloads)
        try:
            sheet = nua_actor.sheet if hasattr(nua_actor, 'sheet') else None
            if sheet is not None:
                pd = (getattr(sheet, 'public_description', None) or '').strip()
                if pd:
                    pd_l = pd.lower()
                    definite_desc = pd if pd_l.startswith('the ') else f"the {pd}"
                    # Heuristic articles
                    if pd_l.startswith('the '):
                        noun = pd[4:].strip()
                    elif pd_l.startswith('a '):
                        noun = pd[2:].strip()
                    elif pd_l.startswith('an '):
                        noun = pd[3:].strip()
                    else:
                        noun = pd
                    article = 'an' if noun[:1].lower() in 'aeiou' else 'a'
                    article_desc = pd if pd_l.startswith(('a ', 'an ')) else f"{article} {noun}" if not pd_l.startswith('the ') else f"{article} {noun}"
                    short_desc = noun
                    desc = StrangerDescription(
                        short_desc=short_desc,
                        article_desc=article_desc,
                        definite_desc=definite_desc,
                        occupation_desc=definite_desc,
                        trait_highlights=[],
                        is_stranger=True
                    )
                    self._description_cache[cache_key] = desc
                    return desc

                kas = getattr(sheet, 'known_as', None) or []
                if kas:
                    ka0 = str(kas[0]).strip()
                    if ka0:
                        base = ka0
                        base_l = base.lower()
                        noun = base
                        if base_l.startswith('the '):
                            noun = base[4:].strip()
                        elif base_l.startswith('a '):
                            noun = base[2:].strip()
                        elif base_l.startswith('an '):
                            noun = base[3:].strip()
                        definite_desc = base if base_l.startswith('the ') else f"the {base.lower()}"
                        article = 'an' if noun[:1].lower() in 'aeiou' else 'a'
                        article_desc = base if base_l.startswith(('a ', 'an ')) else f"{article} {noun.lower()}"
                        desc = StrangerDescription(
                            short_desc=noun,
                            article_desc=article_desc,
                            definite_desc=definite_desc,
                            occupation_desc=definite_desc,
                            trait_highlights=[],
                            is_stranger=True
                        )
                        self._description_cache[cache_key] = desc
                        return desc
        except Exception:
            pass
        
        # Generate stranger description
        desc = self._generate_stranger_description(nua_actor, context)
        self._description_cache[cache_key] = desc
        return desc
    
    def _generate_stranger_description(self, nua_actor, context: str) -> StrangerDescription:
        """Generate a description for a stranger based on their traits"""
        sheet = nua_actor.sheet if hasattr(nua_actor, 'sheet') else None
        
        if not sheet:
            return StrangerDescription(
                short_desc="someone",
                article_desc="someone",
                definite_desc="the person",
                occupation_desc="the person",
                trait_highlights=[],
                is_stranger=True
            )
        
        # Get basic info
        age = getattr(sheet, 'age', 30)
        gender = getattr(sheet, 'gender', 'unknown')
        occupation = getattr(sheet, 'occupation', '')
        
        # Get S-traits (Sturdiness, Smarts, Swiftness, Sociability, Shadow)
        s_factors = getattr(sheet, 's_factors', None)
        try:
            from actor_sheet import SFactorType
            sturdiness = s_factors.get_factor(SFactorType.STURDINESS) if s_factors else 3
            smart = s_factors.get_factor(SFactorType.SMARTS) if s_factors else 3
            swiftness = s_factors.get_factor(SFactorType.SWIFTNESS) if s_factors else 3
            sociability = s_factors.get_factor(SFactorType.SOCIABILITY) if s_factors else 3
            shadow = s_factors.get_factor(SFactorType.SHADOW) if s_factors else 3
        except Exception:
            # Fallback to defaults if s_factors access fails
            sturdiness = smart = swiftness = sociability = shadow = 3
        
        # Build description components
        trait_highlights = []
        adjectives = []
        
        # Check for standout traits (1 or 5) - prioritize most visible traits
        # Sturdiness is most visually obvious
        if sturdiness <= 1:
            adj = STURDINESS_DESCRIPTIONS[1][0]
            adjectives.append(adj)
            trait_highlights.append(f"extremely {adj}")
        elif sturdiness >= 5:
            adj = STURDINESS_DESCRIPTIONS[5][0]
            adjectives.append(adj)
            trait_highlights.append(f"extremely {adj}")
        elif sturdiness == 4:
            adjectives.append(STURDINESS_DESCRIPTIONS[4][0])
        elif sturdiness == 2:
            adjectives.append(STURDINESS_DESCRIPTIONS[2][0])
        
        # Sociability affects demeanor/presence (second most visible)
        if sociability <= 1:
            adj = SOCIABILITY_DESCRIPTIONS[1][0]
            adjectives.append(adj)
            trait_highlights.append(f"very {adj}")
        elif sociability >= 5:
            adj = SOCIABILITY_DESCRIPTIONS[5][0]
            adjectives.append(adj)
            trait_highlights.append(adj)
        
        # Shadow can be visible in extreme cases (menacing vs innocent)
        if shadow >= 5:
            adj = SHADOW_DESCRIPTIONS[5][0]
            adjectives.append(adj)
            trait_highlights.append(adj)
        
        # Add age descriptor if notable
        age_desc = get_age_description(age)
        if age_desc not in ["thirtyish"]:  # Skip unremarkable ages
            adjectives.insert(0, age_desc)
        
        # Get gender noun
        gender_noun = get_gender_noun(gender, age)
        
        # Check for visible occupation
        occupation_visible = self._is_occupation_visible(occupation, context)
        occupation_desc = ""
        if occupation_visible:
            occupation_desc = self._get_occupation_description(occupation)
        
        # Build final description
        if adjectives:
            # Limit to 2 adjectives for readability
            adj_str = " ".join(adjectives[:2])
            short_desc = f"{adj_str} {gender_noun}"
        else:
            short_desc = gender_noun
        
        # Add articles
        article = "an" if short_desc[0].lower() in 'aeiou' else "a"
        article_desc = f"{article} {short_desc}"
        definite_desc = f"the {short_desc}"
        
        # Use occupation if visible, otherwise trait description
        if occupation_desc:
            final_occupation_desc = occupation_desc
        else:
            final_occupation_desc = definite_desc
        
        return StrangerDescription(
            short_desc=short_desc,
            article_desc=article_desc,
            definite_desc=definite_desc,
            occupation_desc=final_occupation_desc,
            trait_highlights=trait_highlights,
            is_stranger=True
        )
    
    def _is_occupation_visible(self, occupation: str, context: str) -> bool:
        """Check if occupation would be visually obvious"""
        if not occupation:
            return False
        
        occupation_lower = occupation.lower()
        context_lower = context.lower()
        
        # Check if occupation is in visible list
        for key in VISIBLE_OCCUPATIONS:
            if key in occupation_lower:
                return True
        
        # Check context for occupation keywords
        for keyword, occupations in OCCUPATION_KEYWORDS.items():
            if keyword in context_lower:
                for occ in occupations:
                    if occ in occupation_lower:
                        return True
        
        # Check if in appropriate context (e.g., "cook" in "diner")
        context_occupation_hints = {
            "diner": ["cook", "waitress", "waiter", "server"],
            "restaurant": ["cook", "chef", "waitress", "waiter", "server", "hostess"],
            "bar": ["bartender", "bouncer"],
            "hospital": ["nurse", "doctor", "orderly"],
            "police station": ["police", "officer", "detective"],
            "store": ["clerk", "cashier", "shopkeeper"],
            "office": ["receptionist", "secretary"],
        }
        
        for location, occupations in context_occupation_hints.items():
            if location in context_lower:
                for occ in occupations:
                    if occ in occupation_lower:
                        return True
        
        return False
    
    def _get_occupation_description(self, occupation: str) -> str:
        """Get the appropriate description for a visible occupation"""
        occupation_lower = occupation.lower()
        
        for key, descriptions in VISIBLE_OCCUPATIONS.items():
            if key in occupation_lower:
                # Return the definite article version
                return descriptions[-1]  # e.g., "the waitress"
        
        return f"the {occupation.lower()}"
    
    def clear_cache(self):
        """Clear the description cache (call when relationships change)"""
        self._description_cache.clear()


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

_describer: Optional[StrangerDescriber] = None

def get_stranger_describer(relationship_system=None) -> StrangerDescriber:
    """Get or create global stranger describer"""
    global _describer
    if _describer is None:
        _describer = StrangerDescriber(relationship_system)
    elif relationship_system and _describer.relationship_system != relationship_system:
        _describer = StrangerDescriber(relationship_system)
    return _describer


def get_nua_description(nua_actor, ua_actor=None, context: str = "",
                        relationship_system=None) -> str:
    """
    Get appropriate description for an NUA.
    
    Returns name if known, or trait-based description if stranger.
    
    Args:
        nua_actor: The NUA to describe
        ua_actor: The UA (for relationship check)
        context: Scene context
        relationship_system: Optional relationship tracker
    
    Returns:
        String description (e.g., "Doe" or "a dark-haired waitress")
    """
    describer = get_stranger_describer(relationship_system)
    desc = describer.get_description(nua_actor, ua_actor, context)
    return desc.article_desc if desc.is_stranger else desc.short_desc


def get_nua_definite_description(nua_actor, ua_actor=None, context: str = "",
                                  relationship_system=None) -> str:
    """
    Get definite description for an NUA (with 'the').
    
    Returns name if known, or "the [description]" if stranger.
    """
    describer = get_stranger_describer(relationship_system)
    desc = describer.get_description(nua_actor, ua_actor, context)
    return desc.definite_desc if desc.is_stranger else desc.short_desc


def describe_nuas_in_scene(nuas: List, ua_actor=None, context: str = "",
                           relationship_system=None) -> str:
    """
    Generate a description of multiple NUAs in a scene.
    
    Groups strangers by description type and uses names for known people.
    """
    describer = get_stranger_describer(relationship_system)
    
    descriptions = []
    for nua in nuas:
        desc = describer.get_description(nua, ua_actor, context)
        if desc.is_stranger:
            descriptions.append(desc.occupation_desc)
        else:
            descriptions.append(desc.short_desc)
    
    if not descriptions:
        return ""
    elif len(descriptions) == 1:
        return descriptions[0]
    elif len(descriptions) == 2:
        return f"{descriptions[0]} and {descriptions[1]}"
    else:
        return ", ".join(descriptions[:-1]) + f", and {descriptions[-1]}"


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Stranger Description System Test\n")
    
    # Mock actor sheet
    class MockSFactors:
        def __init__(self, sturdiness=3, smart=3, swiftness=3, sociability=3, shadow=3):
            self._factors = {
                'sturdiness': sturdiness,
                'smart': smart,
                'swiftness': swiftness,
                'sociability': sociability,
                'shadow': shadow
            }
        
        def get_factor_value(self, name):
            return self._factors.get(name.lower(), 3)
    
    class MockSheet:
        def __init__(self, name, age, gender, occupation, s_factors):
            self.name = name
            self.age = age
            self.gender = gender
            self.occupation = occupation
            self.s_factors = s_factors
    
    class MockActor:
        def __init__(self, sheet):
            self.sheet = sheet
    
    # Test cases
    test_cases = [
        ("Hulking bouncer", MockActor(MockSheet("Bruno", 35, "male", "Bouncer", MockSFactors(sturdiness=5)))),
        ("Frail withdrawn beggar", MockActor(MockSheet("Old Tom", 70, "male", "Beggar", MockSFactors(sturdiness=1, sociability=1)))),
        ("Charismatic waitress", MockActor(MockSheet("Doe", 28, "female", "Diner Waitress", MockSFactors(sociability=5)))),
        ("Average cook", MockActor(MockSheet("Mars", 45, "male", "Cook", MockSFactors()))),
        ("Thin sinister man", MockActor(MockSheet("Shade", 40, "male", "Unknown", MockSFactors(sturdiness=2, shadow=5)))),
    ]
    
    describer = StrangerDescriber()
    
    print("=== Stranger Descriptions ===\n")
    for name, actor in test_cases:
        desc = describer.get_description(actor, context="diner")
        print(f"{name}:")
        print(f"  Article: {desc.article_desc}")
        print(f"  Definite: {desc.definite_desc}")
        print(f"  Occupation: {desc.occupation_desc}")
        print(f"  Highlights: {desc.trait_highlights}")
        print()
    
    # Test name learning
    print("\n=== Name Learning Test ===\n")
    print(f"Is Bruno a stranger? {describer.is_stranger(None, test_cases[0][1])}")
    print("Learning Bruno's name...")
    known_actors_tracker.learn_name("Bruno")
    print(f"Is Bruno a stranger now? {describer.is_stranger(None, test_cases[0][1])}")
    
    print("\n✅ Stranger description system ready!")


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTION FOR NAME LEARNING
# ═══════════════════════════════════════════════════════════════════════════════

def learn_npc_name(npc_name: str) -> None:
    """
    Mark an NPC's name as known to the UA.
    
    Call this when:
    - NPC introduces themselves ("I'm Julian")
    - Someone else introduces them ("This is Julian")
    - UA asks and NPC responds
    - UA reads their name (badge, sign, etc.)
    
    Args:
        npc_name: The NPC's name to learn
    """
    known_actors_tracker.learn_name(npc_name)


def is_npc_name_known(npc_name: str) -> bool:
    """Check if the UA knows this NPC's name."""
    return known_actors_tracker.is_name_known(npc_name)


def detect_name_introduction(narrative: str, available_npcs: list = None) -> list:
    """
    Detect if any NPC names are introduced in the narrative.
    
    Looks for patterns like:
    - "I'm Julian" / "I am Julian"
    - "My name is Julian"
    - "Call me Julian"
    - "This is Julian" / "Meet Julian"
    - "Name's Julian"
    
    Args:
        narrative: The narrative text to scan
        available_npcs: List of NPC actors to check names against
        
    Returns:
        List of NPC names that were introduced
    """
    import re
    
    if not narrative or not available_npcs:
        return []
    
    # Get all NPC names
    npc_names = []
    for npc in available_npcs:
        if hasattr(npc, 'sheet'):
            npc_names.append(npc.sheet.name)
    
    if not npc_names:
        return []
    
    learned_names = []
    narrative_lower = narrative.lower()
    
    # Introduction patterns
    patterns = [
        r"i'm\s+(\w+)",
        r"i am\s+(\w+)",
        r"my name is\s+(\w+)",
        r"call me\s+(\w+)",
        r"name's\s+(\w+)",
        r"this is\s+(\w+)",
        r"meet\s+(\w+)",
        r"introducing\s+(\w+)",
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, narrative_lower)
        for match in matches:
            # Check if this matches any NPC name
            for npc_name in npc_names:
                if match.lower() == npc_name.lower().split()[0].lower():
                    # First name match
                    if not is_npc_name_known(npc_name):
                        learn_npc_name(npc_name)
                        learned_names.append(npc_name)
    
    return learned_names
