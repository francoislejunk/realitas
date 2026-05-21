"""
Concrete Detail Tracker for UTAS Simulation

This system tracks EVERY specific detail mentioned in the narrative to maintain
perfect consistency across scenes. Details like car models, brand names, clothing,
locations, and other concrete specifics are stored and enforced.

CRITICAL: If a character drives a Lamborghini in scene 1, they MUST drive the same
Lamborghini in scene 2. No exceptions. This is essential for immersion.
"""

import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Set
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum


class DetailCategory(Enum):
    """Categories of concrete details to track"""
    VEHICLE = "vehicle"              # Car models, motorcycles, etc.
    CLOTHING = "clothing"            # What characters are wearing
    WEAPON = "weapon"                # Specific weapons/tools
    LOCATION = "location"            # Specific places with names
    BRAND = "brand"                  # Brand names (watches, phones, etc.)
    PHYSICAL_TRAIT = "physical_trait"  # Scars, tattoos, distinctive features
    POSSESSION = "possession"        # Items characters own/carry
    BUILDING = "building"            # Specific buildings/establishments
    RELATIONSHIP = "relationship"    # Specific relationship details
    BACKSTORY = "backstory"          # Established backstory facts


@dataclass
class ConcreteDetail:
    """A single concrete detail that must remain consistent"""
    detail_id: str
    category: DetailCategory
    owner: str  # Character or location this detail belongs to
    detail_text: str  # The exact detail (e.g., "1987 Lamborghini Countach, red with black interior")
    keywords: List[str]  # Keywords for matching (e.g., ["car", "vehicle", "lamborghini", "countach"])
    first_mentioned: datetime
    last_referenced: datetime
    mention_count: int = 0
    scene_ids: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            "detail_id": self.detail_id,
            "category": self.category.value,
            "owner": self.owner,
            "detail_text": self.detail_text,
            "keywords": self.keywords,
            "first_mentioned": self.first_mentioned.isoformat(),
            "last_referenced": self.last_referenced.isoformat(),
            "mention_count": self.mention_count,
            "scene_ids": self.scene_ids
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'ConcreteDetail':
        """Create from dictionary"""
        return ConcreteDetail(
            detail_id=data["detail_id"],
            category=DetailCategory(data["category"]),
            owner=data["owner"],
            detail_text=data["detail_text"],
            keywords=data["keywords"],
            first_mentioned=datetime.fromisoformat(data["first_mentioned"]),
            last_referenced=datetime.fromisoformat(data["last_referenced"]),
            mention_count=data.get("mention_count", 0),
            scene_ids=data.get("scene_ids", [])
        )


class ConcreteDetailTracker:
    """
    Tracks all concrete details mentioned in the simulation to ensure consistency.
    
    This is CRITICAL for immersion - if a character drives a specific car model,
    wears specific clothing, or has specific possessions, these MUST remain
    consistent across all scenes.
    """
    
    def __init__(self, session_id: str, storage_directory: Path, fact_system=None):
        self.session_id = session_id
        self.storage_directory = storage_directory
        self.logger = logging.getLogger(__name__)
        self.fact_system = fact_system  # For canonical facts

        # Core storage: detail_id -> ConcreteDetail
        self.details: Dict[str, ConcreteDetail] = {}

        # Index by owner for quick lookup
        self.details_by_owner: Dict[str, List[str]] = {}

        # Index by category for quick lookup
        self.details_by_category: Dict[DetailCategory, List[str]] = {
            category: [] for category in DetailCategory
        }

        # Keyword index for semantic matching
        self.keyword_index: Dict[str, Set[str]] = {}

        # Load existing details
        self._load_details()
    
    def add_detail(self, 
                   category: DetailCategory,
                   owner: str,
                   detail_text: str,
                   keywords: List[str],
                   scene_id: str) -> str:
        """
        Add a new concrete detail to track.
        
        Args:
            category: Category of detail (vehicle, clothing, etc.)
            owner: Who/what this detail belongs to
            detail_text: The exact detail description
            keywords: Keywords for matching
            scene_id: Current scene ID
            
        Returns:
            detail_id of the added detail
        """
        # Check if this detail already exists
        existing_id = self._find_existing_detail(owner, category, keywords)
        if existing_id:
            # Update existing detail
            detail = self.details[existing_id]
            detail.last_referenced = datetime.now()
            detail.mention_count += 1
            if scene_id not in detail.scene_ids:
                detail.scene_ids.append(scene_id)
            self._save_details()
            return existing_id
        
        # Create new detail
        detail_id = f"{category.value}_{owner}_{len(self.details)}"
        detail = ConcreteDetail(
            detail_id=detail_id,
            category=category,
            owner=owner,
            detail_text=detail_text,
            keywords=[kw.lower() for kw in keywords],
            first_mentioned=datetime.now(),
            last_referenced=datetime.now(),
            mention_count=1,
            scene_ids=[scene_id]
        )
        
        # Store detail
        self.details[detail_id] = detail
        
        # Update indices
        if owner not in self.details_by_owner:
            self.details_by_owner[owner] = []
        self.details_by_owner[owner].append(detail_id)
        
        self.details_by_category[category].append(detail_id)
        
        for keyword in detail.keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = set()
            self.keyword_index[keyword].add(detail_id)
        
        self._save_details()
        self.logger.info(f"Added detail: {category.value} for {owner}: {detail_text}")

        # Establish fact for this detail
        self._establish_detail_fact(detail)

        return detail_id
    
    def get_details_for_owner(self, owner: str, category: Optional[DetailCategory] = None) -> List[ConcreteDetail]:
        """
        Get all details for a specific owner (character, location, etc.)
        
        Args:
            owner: The owner name
            category: Optional category filter
            
        Returns:
            List of ConcreteDetail objects
        """
        detail_ids = self.details_by_owner.get(owner, [])
        details = [self.details[did] for did in detail_ids if did in self.details]
        
        if category:
            details = [d for d in details if d.category == category]
        
        return details
    
    def get_detail_by_keywords(self, keywords: List[str], owner: Optional[str] = None) -> Optional[ConcreteDetail]:
        """
        Find a detail by keywords
        
        Args:
            keywords: Keywords to search for
            owner: Optional owner filter
            
        Returns:
            Matching ConcreteDetail or None
        """
        matching_ids = set()
        
        for keyword in keywords:
            keyword_lower = keyword.lower()
            if keyword_lower in self.keyword_index:
                if not matching_ids:
                    matching_ids = self.keyword_index[keyword_lower].copy()
                else:
                    matching_ids &= self.keyword_index[keyword_lower]
        
        if not matching_ids:
            return None
        
        # Filter by owner if specified
        if owner:
            matching_ids = {did for did in matching_ids if self.details[did].owner == owner}
        
        if not matching_ids:
            return None
        
        # Return most recently referenced
        details = [self.details[did] for did in matching_ids]
        return max(details, key=lambda d: d.last_referenced)
    
    def get_context_for_llm(self, owner: str, scene_id: str) -> str:
        """
        Generate context string for LLM prompts with all concrete details for an owner.
        
        This ensures the LLM maintains consistency with established details.
        
        Args:
            owner: Character or location name
            scene_id: Current scene ID
            
        Returns:
            Formatted context string
        """
        details = self.get_details_for_owner(owner)
        
        if not details:
            return ""
        
        context_parts = [f"**ESTABLISHED CONCRETE DETAILS FOR {owner.upper()}:**"]
        context_parts.append("(These details MUST remain consistent in all narration)")
        context_parts.append("")
        
        # Group by category
        by_category = {}
        for detail in details:
            if detail.category not in by_category:
                by_category[detail.category] = []
            by_category[detail.category].append(detail)
        
        for category, category_details in sorted(by_category.items(), key=lambda x: x[0].value):
            context_parts.append(f"**{category.value.upper().replace('_', ' ')}:**")
            for detail in category_details:
                context_parts.append(f"- {detail.detail_text}")
                # Mark if recently referenced
                if scene_id in detail.scene_ids:
                    context_parts.append(f"  (Mentioned in current scene)")
            context_parts.append("")
        
        return "\n".join(context_parts)
    
    def get_all_active_details_context(self, scene_id: str, recent_owners: List[str]) -> str:
        """
        Get context for all recently active owners in the scene.
        
        Args:
            scene_id: Current scene ID
            recent_owners: List of character/location names recently active
            
        Returns:
            Combined context string
        """
        all_contexts = []
        
        for owner in recent_owners:
            owner_context = self.get_context_for_llm(owner, scene_id)
            if owner_context:
                all_contexts.append(owner_context)
        
        if not all_contexts:
            return ""
        
        return "\n\n".join(all_contexts)
    
    def _establish_detail_fact(self, detail: ConcreteDetail):
        """
        Establish a fact in the fact system for this concrete detail.

        This creates bidirectional sync between concrete details and canonical facts.

        Args:
            detail: The ConcreteDetail to convert to a fact
        """
        if not self.fact_system:
            return

        try:
            from fact_system import FactType, FactAuthority

            # Map DetailCategory to FactType and predicate
            category_mapping = {
                DetailCategory.VEHICLE: (FactType.ACTOR_POSSESSION, "has_vehicle"),
                DetailCategory.CLOTHING: (FactType.ACTOR_POSSESSION, "wears"),
                DetailCategory.WEAPON: (FactType.ACTOR_POSSESSION, "has_weapon"),
                DetailCategory.BRAND: (FactType.ACTOR_POSSESSION, "owns_brand"),
                DetailCategory.PHYSICAL_TRAIT: (FactType.ACTOR_TRAIT, "physical_trait"),
                DetailCategory.POSSESSION: (FactType.ACTOR_POSSESSION, "owns"),
                DetailCategory.LOCATION: (FactType.LOCATION_PROPERTY, "known_location"),
                DetailCategory.BUILDING: (FactType.LOCATION_IDENTITY, "building"),
                DetailCategory.RELATIONSHIP: (FactType.RELATIONSHIP, "relationship_detail"),
                DetailCategory.BACKSTORY: (FactType.ACTOR_TRAIT, "backstory"),
            }

            if detail.category not in category_mapping:
                self.logger.warning(f"No fact mapping for detail category: {detail.category}")
                return

            fact_type, predicate = category_mapping[detail.category]

            # Establish the fact
            fact_id, conflict = self.fact_system.establish_fact(
                fact_type=fact_type,
                subject=detail.owner,
                predicate=predicate,
                value=detail.detail_text,
                authority=FactAuthority.SCENE_DECLARED,
                source=f"concrete_detail_{detail.detail_id}",
                tags=detail.keywords + [detail.category.value],
                scene_id=detail.scene_ids[0] if detail.scene_ids else ""
            )

            if conflict:
                self.logger.warning(f"Fact conflict when establishing detail: {conflict}")
            else:
                self.logger.info(f"Established fact {fact_id} for detail {detail.detail_id}")

        except Exception as e:
            self.logger.error(f"Error establishing fact for detail: {e}")

    def _find_existing_detail(self, owner: str, category: DetailCategory, keywords: List[str]) -> Optional[str]:
        """Check if a detail with similar keywords already exists for this owner"""
        owner_details = self.get_details_for_owner(owner, category)
        
        keywords_lower = set(kw.lower() for kw in keywords)
        
        for detail in owner_details:
            detail_keywords = set(detail.keywords)
            # If there's significant keyword overlap, consider it the same detail
            overlap = keywords_lower & detail_keywords
            if len(overlap) >= min(2, len(keywords_lower)):
                return detail.detail_id
        
        return None
    
    def _save_details(self):
        """Save all details to disk"""
        try:
            details_file = self.storage_directory / "concrete_details" / f"details_{self.session_id}.json"
            details_file.parent.mkdir(parents=True, exist_ok=True)
            
            data = {
                "session_id": self.session_id,
                "details": {did: detail.to_dict() for did, detail in self.details.items()},
                "saved_at": datetime.now().isoformat()
            }
            
            with open(details_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved {len(self.details)} concrete details")
            
        except Exception as e:
            self.logger.error(f"Failed to save concrete details: {e}")
    
    def _load_details(self):
        """Load existing details from disk"""
        try:
            details_file = self.storage_directory / "concrete_details" / f"details_{self.session_id}.json"
            
            if details_file.exists():
                with open(details_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Restore details
                for detail_id, detail_data in data.get("details", {}).items():
                    detail = ConcreteDetail.from_dict(detail_data)
                    self.details[detail_id] = detail
                    
                    # Rebuild indices
                    if detail.owner not in self.details_by_owner:
                        self.details_by_owner[detail.owner] = []
                    self.details_by_owner[detail.owner].append(detail_id)
                    
                    self.details_by_category[detail.category].append(detail_id)
                    
                    for keyword in detail.keywords:
                        if keyword not in self.keyword_index:
                            self.keyword_index[keyword] = set()
                        self.keyword_index[keyword].add(detail_id)
                
                self.logger.info(f"Loaded {len(self.details)} concrete details")
                
        except Exception as e:
            self.logger.warning(f"Could not load concrete details: {e}")
    
    def extract_and_store_details_from_narrative(self, narrative: str, actors: List[str], scene_id: str):
        """
        Extract concrete details from narrative text and store them.
        
        This uses pattern matching to identify specific details that should be tracked.
        
        Args:
            narrative: The narrative text to analyze
            actors: List of actor names involved
            scene_id: Current scene ID
        """
        # Vehicle patterns
        vehicle_patterns = [
            r"(\d{4}\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(car|sedan|coupe|convertible|truck|motorcycle|bike)",
            r"(Lamborghini|Ferrari|Porsche|Mercedes|BMW|Audi|Toyota|Honda|Ford|Chevrolet|Dodge)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)",
        ]
        
        # Brand patterns
        brand_patterns = [
            r"(Rolex|Omega|Seiko|Casio|Tag Heuer)\s+watch",
            r"(iPhone|Samsung|Motorola|Nokia)\s+phone",
            r"(Ray-Ban|Oakley|Aviator)\s+sunglasses",
        ]
        
        # Clothing patterns
        clothing_patterns = [
            r"(leather|denim|silk|cotton)\s+(jacket|coat|shirt|pants|dress)",
            r"(black|white|red|blue|green)\s+(suit|jacket|shirt|dress|pants)",
        ]
        
        # For now, we'll use simple keyword extraction
        # This can be enhanced with regex patterns or LLM extraction
        
        narrative_lower = narrative.lower()
        
        # Check for vehicle mentions
        vehicle_keywords = ["car", "vehicle", "sedan", "coupe", "truck", "motorcycle", "bike", 
                          "lamborghini", "ferrari", "porsche", "mercedes", "bmw", "toyota", "honda"]
        
        for actor in actors:
            # Check if this actor has vehicle mentions
            for keyword in vehicle_keywords:
                if keyword in narrative_lower and actor.lower() in narrative_lower:
                    # Extract the sentence containing the vehicle mention
                    sentences = narrative.split('.')
                    for sentence in sentences:
                        if keyword in sentence.lower() and actor.lower() in sentence.lower():
                            # Store this as a detail
                            self.add_detail(
                                category=DetailCategory.VEHICLE,
                                owner=actor,
                                detail_text=sentence.strip(),
                                keywords=[keyword, "vehicle", actor.lower()],
                                scene_id=scene_id
                            )
                            break
