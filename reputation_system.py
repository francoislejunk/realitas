"""
Reputation System - Title-Based Recognition for All Actors

Every actor (UA, NUA, MNUA, INUA) has titles that can be earned through notable actions.
Titles are visible to all actors and affect how others perceive and interact with them.

Example:
- "Hero of the Supermarket" - Earned by saving someone at a supermarket
- "The Rat" - Earned by betraying allies
- "Kingpin of 5th Street" - Earned by dominating local territory

Design Philosophy:
- Titles are earned through ACTIONS, not stats
- All actors can see all titles (public reputation)
- Titles affect NUA behavior toward the actor
- Multiple titles can be held simultaneously
- Titles have categories (heroic, villainous, professional, social)

Title Levels (determines how much a title defines the character):
- MINOR: Small good/bad deed (helped carry groceries, was rude) - quickly forgotten
- NOTABLE: Significant action (saved a life, committed a crime) - remembered for months
- DEFINING: Major character trait (serial killer, war hero) - remembered for years
- CHARACTER_DEFINING: Core identity ("The Butcher of Berlin") - never forgotten

Recency Decay:
- Titles fade over time (recency multiplier: 1.0 → 0.05 over 2+ years)
- Recent titles overshadow old ones in perception
- Reinforcement (repeating similar actions) slows decay
- A CHARACTER_DEFINING title from last week (impact: 15.0) will completely
  overshadow a NOTABLE title from 2 years ago (impact: 0.15)

Example Scenario:
- Actor was "Hero of the Supermarket" (NOTABLE) 2 years ago → impact: 3 * 0.05 = 0.15
- Actor just earned "The Manslayer" (CHARACTER_DEFINING) last week → impact: 15 * 1.0 = 15.0
- Others will primarily see "The Manslayer" - the old heroism is a distant memory
"""

import json
import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field

from openrouter_config import create_role_client, OpenRouterConfig
from json_utils import extract_and_parse_json
from color_utils import Color


class TitleCategory(Enum):
    """Categories of reputation titles"""
    HEROIC = "heroic"           # Saving lives, protecting others
    VILLAINOUS = "villainous"   # Causing harm, betrayal, crime
    PROFESSIONAL = "professional"  # Work-related achievements
    SOCIAL = "social"           # Relationship-based titles
    NOTORIOUS = "notorious"     # Infamy, fear-based reputation
    RESPECTED = "respected"     # Earned respect, authority
    MYSTERIOUS = "mysterious"   # Unknown, enigmatic reputation
    LOCAL = "local"             # Location-specific recognition


class TitleLevel(Enum):
    """
    Title significance level - determines how much it defines the character.
    
    Higher levels overshadow lower levels in perception.
    A CHARACTER_DEFINING title will eclipse MINOR titles in how others see you.
    """
    MINOR = "minor"                     # Small good/bad deed (helped carry groceries, was rude)
    NOTABLE = "notable"                 # Significant action (saved a life, committed a crime)
    DEFINING = "defining"               # Major character trait (serial killer, war hero)
    CHARACTER_DEFINING = "character_defining"  # Core identity ("The Butcher of Berlin")


class TitleRarity(Enum):
    """How rare/significant the title is"""
    COMMON = "common"           # Easy to earn, many have it
    UNCOMMON = "uncommon"       # Requires some effort
    RARE = "rare"               # Significant achievement
    LEGENDARY = "legendary"     # Exceptional, story-defining


@dataclass
class Title:
    """
    A single reputation title with level-based significance and recency decay.
    
    Title Impact Formula:
    - Base impact from level (MINOR=1, NOTABLE=3, DEFINING=7, CHARACTER_DEFINING=15)
    - Recency multiplier (1.0 for recent, decays over time)
    - Final perceived impact = base_impact * recency_multiplier
    
    Example:
    - "Hero of the Supermarket" (NOTABLE, 2 years ago) = 3 * 0.3 = 0.9 impact
    - "The Manslayer" (CHARACTER_DEFINING, 1 week ago) = 15 * 1.0 = 15.0 impact
    - The Manslayer title completely overshadows the old hero title
    """
    name: str                           # "Hero of the Supermarket"
    description: str                    # How it was earned
    category: TitleCategory
    level: TitleLevel                   # How defining is this title?
    rarity: TitleRarity
    earned_at: datetime
    earned_location: str                # Where the title was earned
    earned_action: str                  # What action earned it
    witnesses: List[str] = field(default_factory=list)  # Who saw it happen
    is_public: bool = True              # Can others see this title?
    reputation_modifier: int = 0        # -5 to +5, affects initial sympathy
    reinforcement_count: int = 0        # How many times this title has been reinforced by similar actions
    
    # Base impact values for each level
    LEVEL_BASE_IMPACT = {
        TitleLevel.MINOR: 1,
        TitleLevel.NOTABLE: 3,
        TitleLevel.DEFINING: 7,
        TitleLevel.CHARACTER_DEFINING: 15
    }
    
    def get_base_impact(self) -> int:
        """Get the base impact value for this title's level"""
        return self.LEVEL_BASE_IMPACT.get(self.level, 1)
    
    def get_recency_multiplier(self, current_time: datetime = None) -> float:
        """
        Calculate recency decay multiplier.
        
        Decay formula:
        - 0-7 days: 1.0 (full impact)
        - 7-30 days: 0.9 (slight decay)
        - 1-3 months: 0.7 (noticeable decay)
        - 3-6 months: 0.5 (significant decay)
        - 6-12 months: 0.3 (fading memory)
        - 1-2 years: 0.15 (distant memory)
        - 2+ years: 0.05 (almost forgotten)
        
        Reinforcement slows decay:
        - Each reinforcement adds 0.1 to the multiplier (capped at 1.0)
        """
        if current_time is None:
            current_time = datetime.now()
        
        days_since = (current_time - self.earned_at).days
        
        # Base decay
        if days_since <= 7:
            base_multiplier = 1.0
        elif days_since <= 30:
            base_multiplier = 0.9
        elif days_since <= 90:
            base_multiplier = 0.7
        elif days_since <= 180:
            base_multiplier = 0.5
        elif days_since <= 365:
            base_multiplier = 0.3
        elif days_since <= 730:
            base_multiplier = 0.15
        else:
            base_multiplier = 0.05
        
        # Reinforcement bonus (each reinforcement adds 0.1, capped)
        reinforcement_bonus = min(self.reinforcement_count * 0.1, 0.5)
        
        return min(base_multiplier + reinforcement_bonus, 1.0)
    
    def get_perceived_impact(self, current_time: datetime = None) -> float:
        """
        Calculate the current perceived impact of this title.
        
        perceived_impact = base_impact * recency_multiplier
        
        This determines how much this title affects others' perception.
        """
        return self.get_base_impact() * self.get_recency_multiplier(current_time)
    
    def reinforce(self):
        """Reinforce this title with a similar action, slowing decay"""
        self.reinforcement_count += 1
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize title to dictionary"""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category.value,
            "level": self.level.value,
            "rarity": self.rarity.value,
            "earned_at": self.earned_at.isoformat(),
            "earned_location": self.earned_location,
            "earned_action": self.earned_action,
            "witnesses": self.witnesses,
            "is_public": self.is_public,
            "reputation_modifier": self.reputation_modifier,
            "reinforcement_count": self.reinforcement_count
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Title':
        """Deserialize title from dictionary"""
        # Handle legacy data without level field
        level_str = data.get("level", "notable")
        try:
            level = TitleLevel(level_str)
        except ValueError:
            level = TitleLevel.NOTABLE
        
        return cls(
            name=data["name"],
            description=data["description"],
            category=TitleCategory(data["category"]),
            level=level,
            rarity=TitleRarity(data["rarity"]),
            earned_at=datetime.fromisoformat(data["earned_at"]),
            earned_location=data["earned_location"],
            earned_action=data["earned_action"],
            witnesses=data.get("witnesses", []),
            is_public=data.get("is_public", True),
            reputation_modifier=data.get("reputation_modifier", 0),
            reinforcement_count=data.get("reinforcement_count", 0)
        )


@dataclass
class ActorReputation:
    """
    Complete reputation profile for an actor.
    
    Perception System:
    - Titles are ranked by perceived impact (level * recency)
    - The dominant title is what others primarily see
    - Old titles fade but can be reinforced
    - Character-defining titles overshadow minor ones
    """
    actor_name: str
    titles: List[Title] = field(default_factory=list)
    primary_title: Optional[str] = None  # The title they're most known for (dynamic)
    total_reputation_score: int = 0      # Sum of all title modifiers
    
    def add_title(self, title: Title):
        """Add a new title"""
        self.titles.append(title)
        self.total_reputation_score += title.reputation_modifier
        
        # Recalculate primary title based on perceived impact
        self._update_primary_title()
    
    def _update_primary_title(self):
        """Update primary title based on current perceived impact"""
        if not self.titles:
            self.primary_title = None
            return
        
        # Get title with highest perceived impact
        dominant = self.get_dominant_title()
        if dominant:
            self.primary_title = dominant.name
    
    def get_dominant_title(self, current_time: datetime = None) -> Optional[Title]:
        """
        Get the title with highest perceived impact right now.
        
        This is what others will primarily recognize this actor for.
        """
        if not self.titles:
            return None
        
        public_titles = self.get_public_titles()
        if not public_titles:
            return None
        
        return max(public_titles, key=lambda t: t.get_perceived_impact(current_time))
    
    def get_titles_by_perceived_impact(self, current_time: datetime = None) -> List[Title]:
        """Get all titles sorted by current perceived impact (highest first)"""
        return sorted(
            self.titles,
            key=lambda t: t.get_perceived_impact(current_time),
            reverse=True
        )
    
    def get_perception_for_other_actor(self, 
                                       perceiver_name: str,
                                       current_time: datetime = None) -> Dict[str, Any]:
        """
        Get how another actor would perceive this actor's reputation.
        
        Returns a perception dict with:
        - dominant_title: The title they'll primarily recognize
        - dominant_impact: How strongly they perceive it
        - secondary_titles: Other notable titles they might remember
        - overall_impression: positive/negative/neutral/mixed
        - sympathy_modifier: How this affects initial sympathy (-5 to +5)
        """
        if not self.titles:
            return {
                "dominant_title": None,
                "dominant_impact": 0,
                "secondary_titles": [],
                "overall_impression": "unknown",
                "sympathy_modifier": 0,
                "perception_summary": f"{self.actor_name} is unknown to {perceiver_name}."
            }
        
        # Get titles sorted by impact
        ranked_titles = self.get_titles_by_perceived_impact(current_time)
        public_titles = [t for t in ranked_titles if t.is_public]
        
        if not public_titles:
            return {
                "dominant_title": None,
                "dominant_impact": 0,
                "secondary_titles": [],
                "overall_impression": "mysterious",
                "sympathy_modifier": 0,
                "perception_summary": f"{self.actor_name} keeps their reputation hidden."
            }
        
        dominant = public_titles[0]
        dominant_impact = dominant.get_perceived_impact(current_time)
        
        # Secondary titles are those with at least 30% of dominant's impact
        threshold = dominant_impact * 0.3
        secondary = [t for t in public_titles[1:] if t.get_perceived_impact(current_time) >= threshold]
        
        # Calculate overall impression
        positive_impact = sum(t.get_perceived_impact(current_time) 
                             for t in public_titles 
                             if t.category in [TitleCategory.HEROIC, TitleCategory.RESPECTED])
        negative_impact = sum(t.get_perceived_impact(current_time) 
                             for t in public_titles 
                             if t.category in [TitleCategory.VILLAINOUS, TitleCategory.NOTORIOUS])
        
        if positive_impact > negative_impact * 1.5:
            overall = "positive"
        elif negative_impact > positive_impact * 1.5:
            overall = "negative"
        elif positive_impact > 0 and negative_impact > 0:
            overall = "mixed"
        else:
            overall = "neutral"
        
        # Calculate sympathy modifier based on dominant title
        sympathy_mod = dominant.reputation_modifier
        # Decay sympathy modifier based on recency
        sympathy_mod = int(sympathy_mod * dominant.get_recency_multiplier(current_time))
        
        # Build perception summary
        summary = self._build_perception_summary(dominant, secondary, overall, current_time)
        
        return {
            "dominant_title": dominant.name,
            "dominant_impact": dominant_impact,
            "dominant_level": dominant.level.value,
            "secondary_titles": [t.name for t in secondary[:3]],
            "overall_impression": overall,
            "sympathy_modifier": sympathy_mod,
            "perception_summary": summary
        }
    
    def _build_perception_summary(self, 
                                  dominant: Title, 
                                  secondary: List[Title],
                                  overall: str,
                                  current_time: datetime = None) -> str:
        """Build a natural language summary of how this actor is perceived"""
        recency = dominant.get_recency_multiplier(current_time)
        
        # Describe recency
        if recency >= 0.9:
            time_desc = "is known as"
        elif recency >= 0.5:
            time_desc = "was recently known as"
        elif recency >= 0.2:
            time_desc = "was once known as"
        else:
            time_desc = "was long ago known as"
        
        summary = f'{self.actor_name} {time_desc} "{dominant.name}"'
        
        # Add secondary titles if significant
        if secondary:
            if len(secondary) == 1:
                summary += f', though some also remember them as "{secondary[0].name}"'
            else:
                summary += f', with a history including "{secondary[0].name}"'
        
        # Add overall impression
        if overall == "mixed":
            summary += ". Their reputation is complicated."
        elif overall == "negative" and dominant.category in [TitleCategory.HEROIC, TitleCategory.RESPECTED]:
            summary += ". But darker deeds shadow their past heroism."
        elif overall == "positive" and dominant.category in [TitleCategory.VILLAINOUS, TitleCategory.NOTORIOUS]:
            summary += ". Though they've shown capacity for good."
        
        return summary
    
    def reinforce_similar_title(self, category: TitleCategory, level: TitleLevel) -> Optional[Title]:
        """
        Find and reinforce a similar existing title.
        
        Returns the reinforced title if found, None otherwise.
        """
        for title in self.titles:
            if title.category == category and title.level == level:
                title.reinforce()
                self._update_primary_title()
                return title
        return None
    
    def has_title(self, title_name: str) -> bool:
        """Check if actor has a specific title"""
        return any(t.name.lower() == title_name.lower() for t in self.titles)
    
    def get_titles_by_category(self, category: TitleCategory) -> List[Title]:
        """Get all titles in a category"""
        return [t for t in self.titles if t.category == category]
    
    def get_titles_by_level(self, level: TitleLevel) -> List[Title]:
        """Get all titles at a specific level"""
        return [t for t in self.titles if t.level == level]
    
    def get_public_titles(self) -> List[Title]:
        """Get all publicly visible titles"""
        return [t for t in self.titles if t.is_public]
    
    def get_reputation_summary(self) -> str:
        """Get a brief summary of reputation"""
        if not self.titles:
            return "Unknown"
        
        dominant = self.get_dominant_title()
        if dominant:
            impact = dominant.get_perceived_impact()
            level_desc = dominant.level.value.replace("_", " ").title()
            return f'"{dominant.name}" ({level_desc}, impact: {impact:.1f})'
        
        return f"{len(self.titles)} titles earned"
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize reputation to dictionary"""
        return {
            "actor_name": self.actor_name,
            "titles": [t.to_dict() for t in self.titles],
            "primary_title": self.primary_title,
            "total_reputation_score": self.total_reputation_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ActorReputation':
        """Deserialize reputation from dictionary"""
        rep = cls(
            actor_name=data["actor_name"],
            primary_title=data.get("primary_title"),
            total_reputation_score=data.get("total_reputation_score", 0)
        )
        rep.titles = [Title.from_dict(t) for t in data.get("titles", [])]
        return rep


class ReputationSystem:
    """
    Central system for managing actor reputations and titles.
    
    Key Features:
    - Detects notable actions that should earn titles
    - Creates contextually appropriate titles
    - Tracks reputation across all actors
    - Provides reputation info to other systems
    """
    
    def __init__(self, storage_directory: Path, rag_system=None):
        self.client = create_role_client("coordination")
        self.logger = logging.getLogger(__name__)
        self.storage_directory = Path(storage_directory) if isinstance(storage_directory, str) else storage_directory
        self.rag_system = rag_system  # For worldbuilding context
        
        # Actor reputations indexed by name
        self.reputations: Dict[str, ActorReputation] = {}
        
        # Track recent actions to avoid duplicate title awards
        self.recent_title_actions: Set[str] = set()
        
        # Load existing reputations
        self._load_reputations()
    
    def _get_worldbuilding_context(self, query: str, max_tokens: int = 300) -> str:
        """Get relevant worldbuilding context from RAG system."""
        if not self.rag_system:
            return ""
        try:
            results = self.rag_system.query(query, top_k=3)
            if results:
                context_parts = []
                for doc in results[:3]:
                    content = doc.get('content', doc.get('text', ''))[:max_tokens]
                    if content:
                        context_parts.append(content)
                return "\n".join(context_parts)
        except Exception as e:
            self.logger.warning(f"RAG query failed: {e}")
        return ""
    
    def get_or_create_reputation(self, actor_name: str) -> ActorReputation:
        """Get an actor's reputation, creating if needed"""
        if actor_name not in self.reputations:
            self.reputations[actor_name] = ActorReputation(actor_name=actor_name)
        return self.reputations[actor_name]
    
    def detect_title_worthy_action(self,
                                   actor_name: str,
                                   action_description: str,
                                   action_outcome: str,
                                   location: str,
                                   witnesses: List[str] = None,
                                   context: str = "") -> Optional[Title]:
        """
        Detect if an action is worthy of earning a title.
        
        Args:
            actor_name: Who performed the action
            action_description: What they did
            action_outcome: How it turned out
            location: Where it happened
            witnesses: Who saw it
            context: Additional context
            
        Returns:
            Title if earned, None otherwise
        """
        # Create action signature to prevent duplicates
        action_sig = f"{actor_name}:{action_description[:50]}:{location}"
        if action_sig in self.recent_title_actions:
            return None
        
        # Get worldbuilding context for setting-appropriate titles
        worldbuilding_context = self._get_worldbuilding_context(
            f"reputation titles culture society {location}",
            max_tokens=300
        )
        
        worldbuilding_section = ""
        if worldbuilding_context:
            worldbuilding_section = f"""
**WORLDBUILDING CONTEXT (titles must fit this setting):**
{worldbuilding_context}

"""
        
        prompt = f"""Analyze this action to determine if it deserves a reputation title.

**Actor:** {actor_name}
**Action:** {action_description}
**Outcome:** {action_outcome}
**Location:** {location}
**Witnesses:** {', '.join(witnesses) if witnesses else 'None'}
**Context:** {context}
{worldbuilding_section}

**Title-Worthy Actions Include:**
- Saving someone's life or protecting others from harm
- Major acts of betrayal or cruelty
- Significant professional achievements
- Building or destroying important relationships
- Acts that would be talked about by witnesses
- Establishing dominance or authority in an area
- Mysterious or unexplained impressive feats

**NOT Title-Worthy:**
- Routine actions (buying groceries, walking around)
- Minor successes or failures
- Actions with no witnesses and no lasting impact
- Things that wouldn't be remembered or discussed

**TITLE LEVELS (Critical):**
- MINOR: Small good/bad deed (helped someone, was rude) - quickly forgotten
- NOTABLE: Significant action (saved a life, committed a crime) - remembered for months
- DEFINING: Major character trait (serial killer, war hero) - remembered for years
- CHARACTER_DEFINING: Core identity ("The Butcher of Berlin") - never forgotten

Choose level based on how much this action DEFINES who the person is.
Killing 100 men = CHARACTER_DEFINING
Saving one person = NOTABLE
Being rude to a shopkeeper = MINOR

**Response Format:**
Return JSON:

{{
    "is_title_worthy": true/false,
    "reasoning": "Why this does or doesn't deserve a title",
    "title_name": "The Title Name (if worthy)",
    "title_description": "Brief description of how it was earned",
    "category": "heroic/villainous/professional/social/notorious/respected/mysterious/local",
    "level": "minor/notable/defining/character_defining",
    "rarity": "common/uncommon/rare/legendary",
    "reputation_modifier": -5 to +5 (negative for villainous, positive for heroic)
}}

If not title-worthy, set is_title_worthy to false and leave other fields empty.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            
            if not result or not result.get("is_title_worthy", False):
                return None
            
            # Parse level
            level_str = result.get("level", "notable")
            try:
                level = TitleLevel(level_str)
            except ValueError:
                level = TitleLevel.NOTABLE
            
            # Check if we should reinforce an existing similar title instead
            reputation = self.get_or_create_reputation(actor_name)
            category = TitleCategory(result.get("category", "local"))
            
            # If actor already has a similar title, reinforce it instead of creating new
            reinforced = reputation.reinforce_similar_title(category, level)
            if reinforced:
                self.logger.info(f"Title reinforced: {actor_name}'s '{reinforced.name}' (count: {reinforced.reinforcement_count})")
                self._save_reputations()
                return reinforced
            
            # Create the title
            title = Title(
                name=result.get("title_name", "Unknown Title"),
                description=result.get("title_description", action_description),
                category=category,
                level=level,
                rarity=TitleRarity(result.get("rarity", "common")),
                earned_at=datetime.now(),
                earned_location=location,
                earned_action=action_description,
                witnesses=witnesses or [],
                is_public=True,
                reputation_modifier=result.get("reputation_modifier", 0)
            )
            
            # Add to actor's reputation (reputation already fetched above)
            reputation.add_title(title)
            
            # Track to prevent duplicates
            self.recent_title_actions.add(action_sig)
            
            # Save
            self._save_reputations()
            
            self.logger.info(f"Title earned: {actor_name} earned '{title.name}'")
            
            return title
            
        except Exception as e:
            self.logger.error(f"Error detecting title-worthy action: {e}")
            return None
    
    def create_initial_titles(self, 
                             actor_name: str,
                             occupation: str,
                             backstory: str = "",
                             personality: Dict[str, str] = None) -> List[Title]:
        """
        Create initial titles for a new actor based on their background.
        
        Args:
            actor_name: Actor's name
            occupation: Their occupation
            backstory: Background information
            personality: Personality traits
            
        Returns:
            List of initial titles
        """
        prompt = f"""Create 0-2 initial reputation titles for this character based on their background.

**Character:** {actor_name}
**Occupation:** {occupation}
**Backstory:** {backstory}
**Personality:** {personality}

**Guidelines:**
- Only create titles if the background suggests notable past achievements
- A regular person with no special history should have 0 titles
- Titles should reflect things that happened BEFORE the story starts
- Consider their occupation - a veteran cop might have earned recognition
- Consider their personality - a notorious troublemaker might have infamy

**TITLE LEVELS:**
- MINOR: Small deed from their past - almost forgotten now
- NOTABLE: Significant past action - still remembered
- DEFINING: Major past achievement - defines part of who they are
- CHARACTER_DEFINING: Core identity from their past - everyone knows this about them

**Response Format:**
Return JSON array (can be empty):

[
    {{
        "title_name": "The Title",
        "title_description": "How they earned it in their past",
        "category": "heroic/villainous/professional/social/notorious/respected/mysterious/local",
        "level": "minor/notable/defining/character_defining",
        "rarity": "common/uncommon/rare/legendary",
        "reputation_modifier": -5 to +5,
        "earned_location": "Where they earned it",
        "years_ago": 0-10 (how many years ago they earned this)
    }}
]

Return [] if no titles are warranted.
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.5
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            
            if not result or not isinstance(result, list):
                return []
            
            titles = []
            reputation = self.get_or_create_reputation(actor_name)
            
            for title_data in result:
                # Parse level
                level_str = title_data.get("level", "notable")
                try:
                    level = TitleLevel(level_str)
                except ValueError:
                    level = TitleLevel.NOTABLE
                
                # Calculate earned_at based on years_ago
                years_ago = title_data.get("years_ago", 1)
                earned_at = datetime.now() - timedelta(days=years_ago * 365)
                
                title = Title(
                    name=title_data.get("title_name", "Unknown"),
                    description=title_data.get("title_description", ""),
                    category=TitleCategory(title_data.get("category", "local")),
                    level=level,
                    rarity=TitleRarity(title_data.get("rarity", "common")),
                    earned_at=earned_at,
                    earned_location=title_data.get("earned_location", "Unknown"),
                    earned_action="Background history",
                    witnesses=[],
                    is_public=True,
                    reputation_modifier=title_data.get("reputation_modifier", 0)
                )
                
                reputation.add_title(title)
                titles.append(title)
            
            if titles:
                self._save_reputations()
            
            return titles
            
        except Exception as e:
            self.logger.error(f"Error creating initial titles: {e}")
            return []
    
    def get_actor_titles_for_display(self, actor_name: str) -> List[Dict[str, Any]]:
        """Get formatted titles for actor sheet display, sorted by perceived impact"""
        reputation = self.reputations.get(actor_name)
        if not reputation:
            return []
        
        # Sort by perceived impact (highest first)
        sorted_titles = reputation.get_titles_by_perceived_impact()
        
        return [
            {
                "name": t.name,
                "category": t.category.value,
                "level": t.level.value,
                "rarity": t.rarity.value,
                "modifier": t.reputation_modifier,
                "perceived_impact": round(t.get_perceived_impact(), 1),
                "recency": round(t.get_recency_multiplier(), 2),
                "reinforcements": t.reinforcement_count
            }
            for t in sorted_titles if t.is_public
        ]
    
    def get_reputation_context_for_nua(self, 
                                       observer_name: str,
                                       target_name: str) -> str:
        """
        Get reputation context that an NUA would know about a target.
        
        Uses the perception system to determine what the observer would recognize.
        This affects how NPCs perceive and interact with the target.
        """
        reputation = self.reputations.get(target_name)
        if not reputation or not reputation.titles:
            return f"{target_name} has no notable reputation."
        
        # Use the perception system
        perception = reputation.get_perception_for_other_actor(observer_name)
        
        if perception["dominant_title"] is None:
            return f"{target_name} has no publicly known reputation."
        
        # Build context string with perception-aware information
        context_parts = [perception["perception_summary"]]
        
        # Add level context
        level = perception.get("dominant_level", "notable")
        if level == "character_defining":
            context_parts.append(f"This is the DEFINING trait of {target_name} - it overshadows everything else.")
        elif level == "defining":
            context_parts.append(f"This is a major part of who {target_name} is.")
        
        # Add secondary titles if any
        if perception["secondary_titles"]:
            secondary_str = ", ".join(f'"{t}"' for t in perception["secondary_titles"])
            context_parts.append(f"Also known for: {secondary_str}")
        
        # Add overall impression
        impression = perception["overall_impression"]
        if impression == "positive":
            context_parts.append(f"Overall impression: Trustworthy, respected")
        elif impression == "negative":
            context_parts.append(f"Overall impression: Dangerous, distrusted")
        elif impression == "mixed":
            context_parts.append(f"Overall impression: Complicated - both good and bad deeds")
        
        # Add sympathy modifier hint
        sympathy_mod = perception["sympathy_modifier"]
        if sympathy_mod >= 2:
            context_parts.append(f"Initial reaction: Favorable (+{sympathy_mod} sympathy)")
        elif sympathy_mod <= -2:
            context_parts.append(f"Initial reaction: Wary ({sympathy_mod} sympathy)")
        
        return "\n".join(context_parts)
    
    def get_initial_sympathy_modifier(self, 
                                      observer_name: str,
                                      target_name: str) -> int:
        """
        Get sympathy modifier based on reputation.
        
        Uses the perception system - recency and level affect the modifier.
        This affects initial sympathy when actors first meet.
        """
        reputation = self.reputations.get(target_name)
        if not reputation:
            return 0
        
        # Use perception system for accurate modifier
        perception = reputation.get_perception_for_other_actor(observer_name)
        
        # Clamp to reasonable range
        return max(-3, min(3, perception["sympathy_modifier"]))
    
    def display_actor_titles(self, actor_name: str):
        """Display an actor's titles in formatted output, sorted by perceived impact"""
        reputation = self.reputations.get(actor_name)
        
        if not reputation or not reputation.titles:
            print(f"{Color.INFO}│{Color.RESET} 🏆 {Color.INFO}TITLES & REPUTATION{Color.RESET}")
            print(f"{Color.INFO}│{Color.RESET} • {Color.SYSTEM}No titles earned yet{Color.RESET}")
            return
        
        print(f"{Color.INFO}│{Color.RESET} 🏆 {Color.INFO}TITLES & REPUTATION{Color.RESET}")
        
        # Get dominant title (what others primarily see)
        dominant = reputation.get_dominant_title()
        if dominant:
            impact = dominant.get_perceived_impact()
            recency = dominant.get_recency_multiplier()
            recency_desc = "current" if recency >= 0.9 else "recent" if recency >= 0.5 else "fading" if recency >= 0.2 else "distant"
            print(f"{Color.INFO}│{Color.RESET} 👁️ Dominant: {Color.ACTOR_NAME}\"{dominant.name}\"{Color.RESET} ({recency_desc}, impact: {impact:.1f})")
        
        # Display titles sorted by perceived impact
        sorted_titles = reputation.get_titles_by_perceived_impact()
        
        for title in sorted_titles[:5]:  # Max 5 displayed
            # Level icon
            level_icon = {
                TitleLevel.MINOR: "·",
                TitleLevel.NOTABLE: "○",
                TitleLevel.DEFINING: "◉",
                TitleLevel.CHARACTER_DEFINING: "★"
            }.get(title.level, "○")
            
            # Rarity color
            rarity_color = {
                TitleRarity.COMMON: Color.SYSTEM,
                TitleRarity.UNCOMMON: Color.SUCCESS,
                TitleRarity.RARE: Color.INFO,
                TitleRarity.LEGENDARY: Color.WARNING
            }.get(title.rarity, Color.SYSTEM)
            
            # Impact and recency
            impact = title.get_perceived_impact()
            recency = title.get_recency_multiplier()
            
            # Modifier text
            modifier_text = ""
            if title.reputation_modifier > 0:
                modifier_text = f" {Color.SUCCESS}(+{title.reputation_modifier}){Color.RESET}"
            elif title.reputation_modifier < 0:
                modifier_text = f" {Color.ERROR}({title.reputation_modifier}){Color.RESET}"
            
            # Reinforcement indicator
            reinforce_text = f" ×{title.reinforcement_count}" if title.reinforcement_count > 0 else ""
            
            # Recency indicator
            recency_bar = "█" * int(recency * 5) + "░" * (5 - int(recency * 5))
            
            print(f"{Color.INFO}│{Color.RESET} {level_icon} {rarity_color}\"{title.name}\"{Color.RESET}{modifier_text}{reinforce_text}")
            print(f"{Color.INFO}│{Color.RESET}    Impact: {impact:.1f} | Recency: [{recency_bar}] {recency:.0%}")
        
        if len(reputation.titles) > 5:
            print(f"{Color.INFO}│{Color.RESET} {Color.SYSTEM}... and {len(reputation.titles) - 5} more titles{Color.RESET}")
        
        # Overall reputation score
        score = reputation.total_reputation_score
        if score > 0:
            print(f"{Color.INFO}│{Color.RESET} Overall: {Color.SUCCESS}+{score} (Respected){Color.RESET}")
        elif score < 0:
            print(f"{Color.INFO}│{Color.RESET} Overall: {Color.ERROR}{score} (Notorious){Color.RESET}")
        else:
            print(f"{Color.INFO}│{Color.RESET} Overall: {Color.STATUS}Neutral{Color.RESET}")
    
    def _save_reputations(self):
        """Save all reputations to disk"""
        try:
            rep_file = self.storage_directory / "reputation" / "reputations.json"
            rep_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                name: rep.to_dict() 
                for name, rep in self.reputations.items()
            }
            
            with open(rep_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save reputations: {e}")
    
    def _load_reputations(self):
        """Load reputations from disk"""
        try:
            rep_file = self.storage_directory / "reputation" / "reputations.json"
            
            if rep_file.exists():
                with open(rep_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                self.reputations = {
                    name: ActorReputation.from_dict(rep_data)
                    for name, rep_data in data.items()
                }
                
                self.logger.info(f"Loaded {len(self.reputations)} actor reputations")
                
        except Exception as e:
            self.logger.warning(f"Could not load reputations: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global instance
_reputation_system: Optional[ReputationSystem] = None


def get_reputation_system(storage_directory: Path = None) -> ReputationSystem:
    """Get or create the global reputation system instance"""
    global _reputation_system
    
    if _reputation_system is None:
        if storage_directory is None:
            storage_directory = Path("./simulation_data")
        _reputation_system = ReputationSystem(storage_directory)
    
    return _reputation_system


def check_for_title(actor_name: str,
                   action_description: str,
                   action_outcome: str,
                   location: str,
                   witnesses: List[str] = None,
                   context: str = "") -> Optional[Title]:
    """Convenience function to check if an action earns a title"""
    system = get_reputation_system()
    return system.detect_title_worthy_action(
        actor_name=actor_name,
        action_description=action_description,
        action_outcome=action_outcome,
        location=location,
        witnesses=witnesses,
        context=context
    )


def display_title_earned(title: Title, actor_name: str):
    """Display a newly earned title"""
    print(f"\n{Color.SUCCESS}{'═' * 60}{Color.RESET}")
    print(f"{Color.SUCCESS}🏆 TITLE EARNED!{Color.RESET}")
    print(f"{Color.SUCCESS}{'═' * 60}{Color.RESET}")
    print(f"\n{Color.ACTOR_NAME}{actor_name}{Color.RESET} has earned the title:")
    print(f"\n    {Color.INFO}\"{title.name}\"{Color.RESET}")
    print(f"\n{Color.STATUS}{title.description}{Color.RESET}")
    
    if title.reputation_modifier > 0:
        print(f"\n{Color.SUCCESS}Reputation: +{title.reputation_modifier}{Color.RESET}")
    elif title.reputation_modifier < 0:
        print(f"\n{Color.ERROR}Reputation: {title.reputation_modifier}{Color.RESET}")
    
    print(f"\n{Color.SUCCESS}{'═' * 60}{Color.RESET}\n")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Reputation System Test\n")
    
    # Create test system
    system = ReputationSystem(Path("./test_data"))
    
    # Test title detection
    print("Testing title detection...")
    
    title = system.detect_title_worthy_action(
        actor_name="Marcus",
        action_description="Tackled a gunman who was threatening shoppers, disarming him and saving multiple lives",
        action_outcome="The gunman was subdued and no one was hurt",
        location="Downtown Supermarket",
        witnesses=["Store Manager", "Security Guard", "Several Shoppers"],
        context="A robbery gone wrong"
    )
    
    if title:
        display_title_earned(title, "Marcus")
    else:
        print("No title earned (this shouldn't happen for this action)")
    
    # Test initial titles
    print("\nTesting initial title creation...")
    
    initial_titles = system.create_initial_titles(
        actor_name="Detective Sarah Chen",
        occupation="Homicide Detective",
        backstory="15-year veteran who solved the infamous Riverside Killer case",
        personality={"internal": "Determined", "external": "Professional"}
    )
    
    print(f"Created {len(initial_titles)} initial titles")
    for t in initial_titles:
        print(f"  - {t.name}: {t.description}")
    
    # Display reputation
    print("\nDisplaying reputation...")
    system.display_actor_titles("Marcus")
    system.display_actor_titles("Detective Sarah Chen")
    
    print("\n✅ Reputation system ready!")
