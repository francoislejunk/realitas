"""
Fact System for Realitas Neo

Centralized "source of truth" for canonical facts about actors, locations,
relationships, events, and world rules. Prevents narrative contradictions by
tracking facts with authority levels and conflict detection.

Key Features:
- Authority hierarchy (USER_ESTABLISHED > SYSTEM_CANONICAL > SCENE_DECLARED > DIALOGUE_MENTIONED > INFERRED)
- Conflict detection and resolution
- Fact querying and filtering
- Context injection for LLM prompts
- Version history tracking
- Integration with Key Memories, ConcreteDetailTracker, and all agents
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set
from dataclasses import dataclass, field, asdict
from enum import Enum
from uuid import uuid4

logger = logging.getLogger(__name__)


class FactType(Enum):
    """Types of facts that can be tracked"""
    ACTOR_IDENTITY = "actor_identity"          # Who/what actors are (Marcus is a studio engineer)
    ACTOR_TRAIT = "actor_trait"                # Personality/characteristics (Marcus is cautious)
    ACTOR_POSSESSION = "actor_possession"      # What actors own (Marcus owns red Lamborghini)
    LOCATION_IDENTITY = "location_identity"    # Location names/identity
    LOCATION_PROPERTY = "location_property"    # Location attributes (on Main Street)
    RELATIONSHIP = "relationship"              # Actor-to-actor connections (Linda is Marcus's sister)
    EVENT_OCCURRED = "event_occurred"          # What happened (power went out)
    WORLD_RULE = "world_rule"                  # Setting rules (cyberpunk 2026)


class FactAuthority(Enum):
    """Authority levels for facts (highest to lowest)"""
    USER_ESTABLISHED = "user_established"      # User explicitly stated (can override anything)
    SYSTEM_CANONICAL = "system_canonical"      # System-generated canon
    SCENE_DECLARED = "scene_declared"          # Declared in scene generation
    DIALOGUE_MENTIONED = "dialogue_mentioned"  # Mentioned in NPC dialogue
    INFERRED = "inferred"                      # Inferred from context

    def __lt__(self, other):
        """Enable comparison for authority hierarchy"""
        if not isinstance(other, FactAuthority):
            return NotImplemented
        authority_order = [
            FactAuthority.INFERRED,
            FactAuthority.DIALOGUE_MENTIONED,
            FactAuthority.SCENE_DECLARED,
            FactAuthority.SYSTEM_CANONICAL,
            FactAuthority.USER_ESTABLISHED
        ]
        return authority_order.index(self) < authority_order.index(other)

    def __le__(self, other):
        return self == other or self < other

    def __gt__(self, other):
        if not isinstance(other, FactAuthority):
            return NotImplemented
        return not self <= other

    def __ge__(self, other):
        return self == other or self > other


class FactStatus(Enum):
    """Status of a fact"""
    ACTIVE = "active"              # Currently true
    SUPERSEDED = "superseded"      # Replaced by newer fact
    DISPUTED = "disputed"          # Contradictory information exists
    INVALIDATED = "invalidated"    # Proven false/retconned


@dataclass
class Fact:
    """A single canonical fact about the world/actors/events"""
    fact_id: str
    fact_type: FactType
    authority: FactAuthority
    status: FactStatus

    # Core fact data
    subject: str                    # Who/what this fact is about
    predicate: str                  # Relationship/property
    object: Optional[str] = None    # Target (for relationships)
    value: Optional[Any] = None     # Value (for properties)
    statement: str = ""             # Human-readable statement

    # Metadata
    source: str = ""                # Where this fact came from
    created_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    # Versioning
    version: int = 1
    supersedes: Optional[str] = None       # Previous fact ID
    superseded_by: Optional[str] = None    # Next fact ID

    # Context
    turn_number: int = 0
    scene_id: str = ""
    context: str = ""               # Full context where fact was established

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['fact_type'] = self.fact_type.value
        data['authority'] = self.authority.value
        data['status'] = self.status.value
        data['created_at'] = self.created_at.isoformat()
        return data

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'Fact':
        """Create Fact from dictionary"""
        data['fact_type'] = FactType(data['fact_type'])
        data['authority'] = FactAuthority(data['authority'])
        data['status'] = FactStatus(data['status'])
        data['created_at'] = datetime.fromisoformat(data['created_at'])
        return Fact(**data)


class FactSystem:
    """Central system for managing canonical facts"""

    def __init__(self, session_id: str, save_dir: Optional[Path] = None):
        """
        Initialize Fact System

        Args:
            session_id: Unique session identifier
            save_dir: Directory to save facts (defaults to sessions/{session_id}/facts/)
        """
        self.session_id = session_id
        self.save_dir = save_dir or Path(f"sessions/{session_id}/facts")
        self.save_dir.mkdir(parents=True, exist_ok=True)

        self.facts: Dict[str, Fact] = {}  # fact_id -> Fact

        # Indexes for fast lookup
        self.subject_index: Dict[str, Set[str]] = {}      # subject -> {fact_ids}
        self.type_index: Dict[FactType, Set[str]] = {}    # type -> {fact_ids}
        self.tag_index: Dict[str, Set[str]] = {}          # tag -> {fact_ids}
        self.predicate_index: Dict[str, Set[str]] = {}    # predicate -> {fact_ids}

        self.save_path = self.save_dir / f"facts_{session_id}.json"
        self._load_facts()

        logger.info(f"Fact System initialized for session {session_id}")

    def establish_fact(
        self,
        fact_type: FactType,
        subject: str,
        predicate: str,
        object: Optional[str] = None,
        value: Optional[Any] = None,
        authority: FactAuthority = FactAuthority.SYSTEM_CANONICAL,
        source: str = "",
        tags: Optional[List[str]] = None,
        turn_number: int = 0,
        scene_id: str = "",
        context: str = ""
    ) -> Tuple[str, Optional[str]]:
        """
        Establish a new fact

        Args:
            fact_type: Type of fact
            subject: Who/what the fact is about
            predicate: Relationship/property
            object: Target (for relationships)
            value: Value (for properties)
            authority: Authority level
            source: Where the fact came from
            tags: Tags for categorization
            turn_number: Turn when fact was established
            scene_id: Scene identifier
            context: Full context

        Returns:
            Tuple of (fact_id, conflict_message)
            conflict_message is None if no conflict, otherwise describes the conflict
        """
        # Generate fact ID
        fact_id = f"fact_{uuid4().hex[:12]}"

        # Generate human-readable statement
        statement = self._generate_statement(fact_type, subject, predicate, object, value)

        # Check for conflicts
        conflict_msg = self._check_conflict(subject, predicate, object, value, authority)

        # Create fact
        fact = Fact(
            fact_id=fact_id,
            fact_type=fact_type,
            authority=authority,
            status=FactStatus.ACTIVE,
            subject=subject,
            predicate=predicate,
            object=object,
            value=value,
            statement=statement,
            source=source,
            tags=tags or [],
            turn_number=turn_number,
            scene_id=scene_id,
            context=context
        )

        # Handle conflicts if any
        if conflict_msg:
            conflicting_facts = self._find_conflicting_facts(subject, predicate, object, value)
            for cf in conflicting_facts:
                if authority > cf.authority:
                    # New fact supersedes old one
                    cf.status = FactStatus.SUPERSEDED
                    cf.superseded_by = fact_id
                    fact.supersedes = cf.fact_id
                    fact.version = cf.version + 1
                elif authority == cf.authority:
                    # Same authority - mark both as disputed
                    cf.status = FactStatus.DISPUTED
                    fact.status = FactStatus.DISPUTED
                else:
                    # Old fact has higher authority - new fact is disputed
                    fact.status = FactStatus.DISPUTED

        # Store fact
        self.facts[fact_id] = fact

        # Update indexes
        self._index_fact(fact)

        # Save to disk
        self._save_facts()

        logger.info(f"Established fact: {statement} (authority: {authority.value}, status: {fact.status.value})")
        if conflict_msg:
            logger.warning(f"Conflict detected: {conflict_msg}")

        return fact_id, conflict_msg

    def query_facts(
        self,
        subject: Optional[str] = None,
        fact_type: Optional[FactType] = None,
        predicate: Optional[str] = None,
        tags: Optional[List[str]] = None,
        status: FactStatus = FactStatus.ACTIVE,
        min_authority: Optional[FactAuthority] = None
    ) -> List[Fact]:
        """
        Query facts with filters

        Args:
            subject: Filter by subject
            fact_type: Filter by type
            predicate: Filter by predicate
            tags: Filter by tags (fact must have ALL tags)
            status: Filter by status (default: ACTIVE only)
            min_authority: Minimum authority level

        Returns:
            List of matching facts, sorted by authority (highest first)
        """
        # Start with all fact IDs
        candidate_ids = set(self.facts.keys())

        # Apply filters
        if subject:
            subject_lower = subject.lower()
            candidate_ids &= self.subject_index.get(subject_lower, set())

        if fact_type:
            candidate_ids &= self.type_index.get(fact_type, set())

        if predicate:
            predicate_lower = predicate.lower()
            candidate_ids &= self.predicate_index.get(predicate_lower, set())

        if tags:
            for tag in tags:
                tag_lower = tag.lower()
                candidate_ids &= self.tag_index.get(tag_lower, set())

        # Get facts and apply remaining filters
        results = []
        for fact_id in candidate_ids:
            fact = self.facts[fact_id]

            # Status filter
            if fact.status != status:
                continue

            # Authority filter
            if min_authority and fact.authority < min_authority:
                continue

            results.append(fact)

        # Sort by authority (highest first), then by created_at (newest first)
        results.sort(key=lambda f: (
            -list(FactAuthority).index(f.authority),
            -f.created_at.timestamp()
        ))

        return results

    def get_fact_context(
        self,
        subject: str,
        max_facts: int = 10,
        fact_types: Optional[List[FactType]] = None
    ) -> str:
        """
        Generate formatted fact context for LLM prompts

        Args:
            subject: Subject to get facts about
            max_facts: Maximum number of facts to include
            fact_types: Filter by fact types (None = all types)

        Returns:
            Formatted string with facts about subject
        """
        # Query facts (query_facts already returns unique, sorted results)
        if fact_types:
            all_facts = []
            seen_ids = set()
            for ft in fact_types:
                facts = self.query_facts(subject=subject, fact_type=ft)
                for fact in facts:
                    if fact.fact_id not in seen_ids:
                        seen_ids.add(fact.fact_id)
                        all_facts.append(fact)
        else:
            all_facts = self.query_facts(subject=subject)

        # Limit to max_facts
        unique_facts = all_facts[:max_facts]

        if not unique_facts:
            return ""

        # Format output
        lines = [f"**ESTABLISHED FACTS ABOUT {subject.upper()}:**"]

        for fact in unique_facts:
            # Authority indicator
            if fact.authority == FactAuthority.USER_ESTABLISHED:
                prefix = "[USER]"
            elif fact.authority == FactAuthority.SYSTEM_CANONICAL:
                prefix = "[CANON]"
            else:
                prefix = "  -"

            # Statement
            statement = fact.statement

            # Add authority note for user-established facts
            if fact.authority == FactAuthority.USER_ESTABLISHED:
                statement += " (user-established)"

            lines.append(f"{prefix} {statement}")

        return "\n".join(lines)

    def validate_statement(
        self,
        statement: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a statement against established facts

        Args:
            statement: Statement to validate
            context: Context including subject, predicate, etc.

        Returns:
            Dict with validation results:
            {
                'valid': bool,
                'conflicts': List[str],  # Conflicting fact statements
                'warnings': List[str]     # Warnings about potential issues
            }
        """
        subject = context.get('subject', '')
        predicate = context.get('predicate', '')
        value = context.get('value')

        conflicts = []
        warnings = []

        # Get existing facts about subject
        existing_facts = self.query_facts(subject=subject, predicate=predicate)

        for fact in existing_facts:
            # Check if values conflict
            if fact.value and value and fact.value != value:
                conflicts.append(
                    f"Conflicts with: {fact.statement} (authority: {fact.authority.value})"
                )

            # Warn if lower authority
            proposed_authority = context.get('authority', FactAuthority.INFERRED)
            if fact.authority > proposed_authority:
                warnings.append(
                    f"Lower authority than existing fact: {fact.statement}"
                )

        return {
            'valid': len(conflicts) == 0,
            'conflicts': conflicts,
            'warnings': warnings
        }

    def get_fact_by_id(self, fact_id: str) -> Optional[Fact]:
        """Get fact by ID"""
        return self.facts.get(fact_id)

    def invalidate_fact(self, fact_id: str, reason: str = "") -> bool:
        """
        Invalidate a fact (mark as false/retconned)

        Args:
            fact_id: Fact to invalidate
            reason: Reason for invalidation

        Returns:
            True if invalidated, False if fact not found
        """
        fact = self.facts.get(fact_id)
        if not fact:
            return False

        fact.status = FactStatus.INVALIDATED
        if reason:
            fact.context = f"{fact.context}\n[INVALIDATED: {reason}]"

        self._save_facts()
        logger.info(f"Invalidated fact {fact_id}: {fact.statement}")
        return True

    def _generate_statement(
        self,
        fact_type: FactType,
        subject: str,
        predicate: str,
        object: Optional[str],
        value: Optional[Any]
    ) -> str:
        """Generate human-readable statement from fact components"""
        if fact_type == FactType.RELATIONSHIP:
            return f"{subject} {predicate} {object}"
        elif fact_type == FactType.ACTOR_POSSESSION:
            return f"{subject} owns {value}"
        else:
            return f"{subject} {predicate} {value}"

    def _check_conflict(
        self,
        subject: str,
        predicate: str,
        object: Optional[str],
        value: Optional[Any],
        authority: FactAuthority
    ) -> Optional[str]:
        """Check if establishing this fact would conflict with existing facts"""
        # Get existing facts with same subject and predicate
        existing = self.query_facts(subject=subject, predicate=predicate)

        for fact in existing:
            # Check if values/objects differ
            if object and fact.object and object != fact.object:
                return f"Conflicts with existing fact: {fact.statement}"
            if value and fact.value and value != fact.value:
                return f"Conflicts with existing fact: {fact.statement}"

        return None

    def _find_conflicting_facts(
        self,
        subject: str,
        predicate: str,
        object: Optional[str],
        value: Optional[Any]
    ) -> List[Fact]:
        """Find facts that conflict with given parameters"""
        existing = self.query_facts(subject=subject, predicate=predicate)
        conflicts = []

        for fact in existing:
            if object and fact.object and object != fact.object:
                conflicts.append(fact)
            elif value and fact.value and value != fact.value:
                conflicts.append(fact)

        return conflicts

    def _index_fact(self, fact: Fact):
        """Add fact to indexes"""
        fact_id = fact.fact_id

        # Subject index
        subject_lower = fact.subject.lower()
        if subject_lower not in self.subject_index:
            self.subject_index[subject_lower] = set()
        self.subject_index[subject_lower].add(fact_id)

        # Type index
        if fact.fact_type not in self.type_index:
            self.type_index[fact.fact_type] = set()
        self.type_index[fact.fact_type].add(fact_id)

        # Tag index
        for tag in fact.tags:
            tag_lower = tag.lower()
            if tag_lower not in self.tag_index:
                self.tag_index[tag_lower] = set()
            self.tag_index[tag_lower].add(fact_id)

        # Predicate index
        predicate_lower = fact.predicate.lower()
        if predicate_lower not in self.predicate_index:
            self.predicate_index[predicate_lower] = set()
        self.predicate_index[predicate_lower].add(fact_id)

    def _rebuild_indexes(self):
        """Rebuild all indexes from facts"""
        self.subject_index.clear()
        self.type_index.clear()
        self.tag_index.clear()
        self.predicate_index.clear()

        for fact in self.facts.values():
            self._index_fact(fact)

    def _save_facts(self):
        """Save facts to disk"""
        try:
            data = {
                'session_id': self.session_id,
                'saved_at': datetime.now().isoformat(),
                'facts': [fact.to_dict() for fact in self.facts.values()]
            }

            with open(self.save_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            logger.debug(f"Saved {len(self.facts)} facts to {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to save facts: {e}")

    def _load_facts(self):
        """Load facts from disk"""
        if not self.save_path.exists():
            logger.info("No existing facts file found, starting fresh")
            return

        try:
            with open(self.save_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            for fact_data in data.get('facts', []):
                fact = Fact.from_dict(fact_data)
                self.facts[fact.fact_id] = fact

            # Rebuild indexes
            self._rebuild_indexes()

            logger.info(f"Loaded {len(self.facts)} facts from {self.save_path}")
        except Exception as e:
            logger.error(f"Failed to load facts: {e}")


# Example usage and testing
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Create fact system
    fs = FactSystem("test_session")

    # Establish some facts
    print("\n=== Establishing Facts ===")

    # Fact 1: Marcus is a studio engineer
    fact_id_1, conflict = fs.establish_fact(
        fact_type=FactType.ACTOR_IDENTITY,
        subject="Marcus",
        predicate="occupation",
        value="studio engineer",
        authority=FactAuthority.SCENE_DECLARED,
        source="initial_scene",
        tags=["marcus", "occupation"]
    )
    print(f"Fact 1: {fs.get_fact_by_id(fact_id_1).statement}")
    if conflict:
        print(f"  Conflict: {conflict}")

    # Fact 2: Marcus owns a red Lamborghini
    fact_id_2, conflict = fs.establish_fact(
        fact_type=FactType.ACTOR_POSSESSION,
        subject="Marcus",
        predicate="owns",
        value="red 1987 Lamborghini Countach",
        authority=FactAuthority.SYSTEM_CANONICAL,
        source="vehicle_creation",
        tags=["marcus", "vehicle"]
    )
    print(f"Fact 2: {fs.get_fact_by_id(fact_id_2).statement}")

    # Fact 3: Linda is Marcus's sister (relationship)
    fact_id_3, conflict = fs.establish_fact(
        fact_type=FactType.RELATIONSHIP,
        subject="Linda",
        predicate="is_sister_of",
        object="Marcus",
        authority=FactAuthority.DIALOGUE_MENTIONED,
        source="npc_dialogue",
        tags=["linda", "marcus", "relationship", "family"]
    )
    print(f"Fact 3: {fs.get_fact_by_id(fact_id_3).statement}")

    # Query facts about Marcus
    print("\n=== Querying Facts About Marcus ===")
    marcus_facts = fs.query_facts(subject="Marcus")
    for fact in marcus_facts:
        print(f"  - {fact.statement} (authority: {fact.authority.value})")

    # Get formatted context
    print("\n=== Formatted Context for LLM ===")
    context = fs.get_fact_context("Marcus")
    print(context)

    # Try to establish conflicting fact
    print("\n=== Establishing Conflicting Fact ===")
    fact_id_4, conflict = fs.establish_fact(
        fact_type=FactType.ACTOR_IDENTITY,
        subject="Marcus",
        predicate="occupation",
        value="bartender",
        authority=FactAuthority.INFERRED,
        source="test_conflict"
    )
    print(f"Fact 4: {fs.get_fact_by_id(fact_id_4).statement}")
    print(f"  Status: {fs.get_fact_by_id(fact_id_4).status.value}")
    if conflict:
        print(f"  Conflict: {conflict}")

    # Query again
    print("\n=== Querying After Conflict ===")
    marcus_facts = fs.query_facts(subject="Marcus", predicate="occupation")
    for fact in marcus_facts:
        print(f"  - {fact.statement} (authority: {fact.authority.value}, status: {fact.status.value})")
