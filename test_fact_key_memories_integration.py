"""
Integration test for Fact System + Key Memories System

Tests that facts are correctly extracted from key memories with USER_ESTABLISHED authority.
"""

import unittest
import shutil
from pathlib import Path
from datetime import datetime

from fact_system import FactSystem, FactType, FactAuthority, FactStatus
from key_memories_system import KeyMemoriesSystem, MemoryCategory, MemoryImportance


class TestFactKeyMemoriesIntegration(unittest.TestCase):
    """Test suite for Fact System + Key Memories integration"""

    def setUp(self):
        """Set up test environment"""
        self.test_session = "test_fact_key_memories"
        self.test_dir = Path(f"sessions/{self.test_session}")
        self.storage_dir = Path(f"sessions/{self.test_session}")

        # Clean up any previous test data
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # Create systems
        self.fact_system = FactSystem(self.test_session)
        self.key_memories = KeyMemoriesSystem(
            self.test_session,
            self.storage_dir,
            fact_system=self.fact_system
        )

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_relationship_memory_creates_fact(self):
        """Test that relationship memory creates encounter fact"""
        memory_id = self.key_memories.create_memory(
            title="Met Marcus at the bar",
            description="First encounter with Marcus",
            full_narrative="You met Marcus at the dimly lit bar. He introduced himself.",
            category=MemoryCategory.RELATIONSHIP,
            importance=MemoryImportance.IMPORTANT,
            location="The Rusty Nail Bar",
            actors_involved=["Marcus"],
            tags=["marcus", "meeting"],
            turn_number=5,
            scene_id="scene_001"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(subject="Marcus")
        self.assertGreater(len(facts), 0)

        # Verify fact has USER_ESTABLISHED authority
        encounter_facts = [f for f in facts if f.predicate == "encountered_at"]
        self.assertEqual(len(encounter_facts), 1)
        self.assertEqual(encounter_facts[0].authority, FactAuthority.USER_ESTABLISHED)
        self.assertEqual(encounter_facts[0].value, "The Rusty Nail Bar")

    def test_item_memory_creates_possession_fact(self):
        """Test that item memory creates possession fact"""
        memory_id = self.key_memories.create_memory(
            title="Acquired Ancient Key",
            description="Found the ancient key in the vault",
            full_narrative="You discovered an ancient brass key hidden in the vault.",
            category=MemoryCategory.ITEM,
            importance=MemoryImportance.IMPORTANT,
            location="Underground Vault",
            actors_involved=["Player"],
            tags=["key", "item"],
            turn_number=10
        )

        # Verify possession fact created
        facts = self.fact_system.query_facts(subject="Player", fact_type=FactType.ACTOR_POSSESSION)
        self.assertGreater(len(facts), 0)
        self.assertEqual(facts[0].authority, FactAuthority.USER_ESTABLISHED)
        self.assertIn("Ancient Key", facts[0].value)

    def test_location_memory_creates_discovery_fact(self):
        """Test that location memory creates discovery fact"""
        memory_id = self.key_memories.create_memory(
            title="Discovered Hidden Temple",
            description="Found the legendary hidden temple",
            full_narrative="You pushed through the jungle and discovered the hidden temple.",
            category=MemoryCategory.LOCATION,
            importance=MemoryImportance.CRITICAL,
            location="Hidden Temple",
            actors_involved=["Player"],
            tags=["temple", "discovery"]
        )

        # Verify location fact created
        facts = self.fact_system.query_facts(subject="Hidden Temple")
        self.assertGreater(len(facts), 0)
        self.assertEqual(facts[0].authority, FactAuthority.USER_ESTABLISHED)
        self.assertEqual(facts[0].predicate, "discovered")

    def test_revelation_memory_creates_event_fact(self):
        """Test that revelation memory creates event fact"""
        memory_id = self.key_memories.create_memory(
            title="Marcus revealed his secret",
            description="Marcus admitted he's been lying about his identity",
            full_narrative="Marcus finally broke down and revealed everything.",
            category=MemoryCategory.REVELATION,
            importance=MemoryImportance.CRITICAL,
            location="Safe House",
            actors_involved=["Marcus"],
            tags=["revelation", "secret"]
        )

        # Verify event fact created
        facts = self.fact_system.query_facts(subject="Marcus", fact_type=FactType.EVENT_OCCURRED)
        self.assertGreater(len(facts), 0)
        self.assertEqual(facts[0].authority, FactAuthority.USER_ESTABLISHED)
        self.assertEqual(facts[0].predicate, "revelation")

    def test_decision_memory_creates_decision_fact(self):
        """Test that decision memory creates decision fact"""
        memory_id = self.key_memories.create_memory(
            title="Chose to spare his life",
            description="Made the difficult choice to let him live",
            full_narrative="You lowered your weapon and decided to spare his life.",
            category=MemoryCategory.DECISION,
            importance=MemoryImportance.IMPORTANT,
            location="Warehouse",
            actors_involved=["Player", "Victor"],
            tags=["decision", "mercy"]
        )

        # Verify decision fact created
        facts = self.fact_system.query_facts(subject="Player", fact_type=FactType.EVENT_OCCURRED)
        decision_facts = [f for f in facts if f.predicate == "decided"]
        self.assertGreater(len(decision_facts), 0)
        self.assertEqual(decision_facts[0].authority, FactAuthority.USER_ESTABLISHED)

    def test_user_note_creates_user_established_fact(self):
        """Test that user notes create highest authority facts"""
        memory_id = self.key_memories.create_memory(
            title="Important conversation",
            description="Discussed the plan",
            full_narrative="You and Linda discussed the plan in detail.",
            category=MemoryCategory.RELATIONSHIP,
            importance=MemoryImportance.IMPORTANT,
            location="Coffee Shop",
            actors_involved=["Player", "Linda"]
        )

        # Add user note
        memory = self.key_memories.memories[memory_id]
        memory.user_note = "Linda is definitely trustworthy"
        self.key_memories._extract_facts_from_memory(memory)

        # Verify user note fact created with USER_ESTABLISHED authority
        facts = self.fact_system.query_facts(predicate="user_noted")
        self.assertGreater(len(facts), 0)
        self.assertEqual(facts[0].authority, FactAuthority.USER_ESTABLISHED)
        self.assertIn("trustworthy", facts[0].value)

    def test_user_established_overrides_system_facts(self):
        """Test that USER_ESTABLISHED facts from memories override system facts"""
        # Create system fact
        self.fact_system.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="bartender",
            authority=FactAuthority.SYSTEM_CANONICAL,
            source="scene_generation"
        )

        # Create a user note that explicitly contradicts
        memory_id = self.key_memories.create_memory(
            title="Conversation with Marcus",
            description="Important conversation",
            full_narrative="Marcus told you about his past.",
            category=MemoryCategory.RELATIONSHIP,
            importance=MemoryImportance.CRITICAL,
            location="Bar",
            actors_involved=["Marcus"]
        )

        # Add user note (highest authority)
        memory = self.key_memories.memories[memory_id]
        memory.user_note = "Marcus is actually a studio engineer, not a bartender"
        self.key_memories._extract_facts_from_memory(memory)

        # User note fact should be created with USER_ESTABLISHED authority
        user_note_facts = self.fact_system.query_facts(predicate="user_noted")
        self.assertGreater(len(user_note_facts), 0)
        self.assertEqual(user_note_facts[0].authority, FactAuthority.USER_ESTABLISHED)
        self.assertIn("engineer", user_note_facts[0].value)

    def test_extract_all_memory_facts(self):
        """Test extracting facts from all existing memories"""
        # Create memories without fact extraction
        self.key_memories.fact_system = None  # Temporarily disable

        self.key_memories.create_memory(
            title="Memory 1",
            description="First memory",
            full_narrative="Content 1",
            category=MemoryCategory.LOCATION,
            importance=MemoryImportance.IMPORTANT,
            location="Location1",
            actors_involved=["Player"]
        )

        self.key_memories.create_memory(
            title="Memory 2",
            description="Second memory",
            full_narrative="Content 2",
            category=MemoryCategory.RELATIONSHIP,
            importance=MemoryImportance.IMPORTANT,
            location="Location2",
            actors_involved=["Marcus"]
        )

        # Re-enable fact system
        self.key_memories.fact_system = self.fact_system

        # Extract all facts
        count = self.key_memories.extract_all_memory_facts()

        self.assertEqual(count, 2)

        # Verify facts were created
        location_facts = self.fact_system.query_facts(subject="Location1")
        self.assertGreater(len(location_facts), 0)

        marcus_facts = self.fact_system.query_facts(subject="Marcus")
        self.assertGreater(len(marcus_facts), 0)


if __name__ == "__main__":
    unittest.main()
