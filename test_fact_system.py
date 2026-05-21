"""
Unit tests for Fact System

Tests core functionality including:
- Fact establishment
- Conflict detection and resolution
- Authority hierarchy
- Querying and filtering
- Context generation
- Persistence
"""

import unittest
import shutil
from pathlib import Path
from fact_system import (
    FactSystem, Fact, FactType, FactAuthority, FactStatus
)


class TestFactSystem(unittest.TestCase):
    """Test suite for Fact System"""

    def setUp(self):
        """Set up test environment"""
        self.test_session = "test_fact_system_unit"
        self.test_dir = Path(f"sessions/{self.test_session}")

        # Clean up any previous test data
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        self.fs = FactSystem(self.test_session)

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_establish_basic_fact(self):
        """Test establishing a basic fact"""
        fact_id, conflict = self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer",
            authority=FactAuthority.SYSTEM_CANONICAL
        )

        self.assertIsNotNone(fact_id)
        self.assertIsNone(conflict)

        fact = self.fs.get_fact_by_id(fact_id)
        self.assertIsNotNone(fact)
        self.assertEqual(fact.subject, "Marcus")
        self.assertEqual(fact.predicate, "occupation")
        self.assertEqual(fact.value, "engineer")
        self.assertEqual(fact.status, FactStatus.ACTIVE)

    def test_query_by_subject(self):
        """Test querying facts by subject"""
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer"
        )
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_POSSESSION,
            subject="Marcus",
            predicate="owns",
            value="red car"
        )
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Linda",
            predicate="occupation",
            value="doctor"
        )

        marcus_facts = self.fs.query_facts(subject="Marcus")
        self.assertEqual(len(marcus_facts), 2)

        linda_facts = self.fs.query_facts(subject="Linda")
        self.assertEqual(len(linda_facts), 1)

    def test_query_by_type(self):
        """Test querying facts by type"""
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer"
        )
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_POSSESSION,
            subject="Marcus",
            predicate="owns",
            value="red car"
        )

        identity_facts = self.fs.query_facts(fact_type=FactType.ACTOR_IDENTITY)
        self.assertEqual(len(identity_facts), 1)

        possession_facts = self.fs.query_facts(fact_type=FactType.ACTOR_POSSESSION)
        self.assertEqual(len(possession_facts), 1)

    def test_query_by_tags(self):
        """Test querying facts by tags"""
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer",
            tags=["marcus", "job", "important"]
        )
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_POSSESSION,
            subject="Marcus",
            predicate="owns",
            value="red car",
            tags=["marcus", "vehicle"]
        )

        # Query with single tag
        marcus_facts = self.fs.query_facts(tags=["marcus"])
        self.assertEqual(len(marcus_facts), 2)

        # Query with multiple tags (must have ALL)
        job_facts = self.fs.query_facts(tags=["marcus", "job"])
        self.assertEqual(len(job_facts), 1)
        self.assertEqual(job_facts[0].value, "engineer")

    def test_conflict_detection_lower_authority(self):
        """Test conflict when new fact has lower authority"""
        # Establish high-authority fact
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer",
            authority=FactAuthority.SYSTEM_CANONICAL
        )

        # Try to establish conflicting fact with lower authority
        fact_id, conflict = self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="bartender",
            authority=FactAuthority.INFERRED
        )

        self.assertIsNotNone(conflict)

        new_fact = self.fs.get_fact_by_id(fact_id)
        self.assertEqual(new_fact.status, FactStatus.DISPUTED)

    def test_conflict_supersede_higher_authority(self):
        """Test that higher authority fact supersedes lower authority"""
        # Establish lower-authority fact
        old_fact_id, _ = self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="intern",
            authority=FactAuthority.INFERRED
        )

        # Establish higher-authority conflicting fact
        new_fact_id, conflict = self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer",
            authority=FactAuthority.SYSTEM_CANONICAL
        )

        self.assertIsNotNone(conflict)

        old_fact = self.fs.get_fact_by_id(old_fact_id)
        new_fact = self.fs.get_fact_by_id(new_fact_id)

        self.assertEqual(old_fact.status, FactStatus.SUPERSEDED)
        self.assertEqual(new_fact.status, FactStatus.ACTIVE)
        self.assertEqual(old_fact.superseded_by, new_fact_id)
        self.assertEqual(new_fact.supersedes, old_fact_id)

    def test_authority_hierarchy(self):
        """Test authority level comparison"""
        self.assertTrue(FactAuthority.USER_ESTABLISHED > FactAuthority.SYSTEM_CANONICAL)
        self.assertTrue(FactAuthority.SYSTEM_CANONICAL > FactAuthority.SCENE_DECLARED)
        self.assertTrue(FactAuthority.SCENE_DECLARED > FactAuthority.DIALOGUE_MENTIONED)
        self.assertTrue(FactAuthority.DIALOGUE_MENTIONED > FactAuthority.INFERRED)

    def test_fact_context_generation(self):
        """Test formatted context generation for LLM"""
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer",
            authority=FactAuthority.SYSTEM_CANONICAL
        )
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_POSSESSION,
            subject="Marcus",
            predicate="owns",
            value="red car",
            authority=FactAuthority.USER_ESTABLISHED
        )

        context = self.fs.get_fact_context("Marcus")

        self.assertIn("MARCUS", context)
        self.assertIn("engineer", context)
        self.assertIn("red car", context)
        self.assertIn("user-established", context)

    def test_persistence(self):
        """Test saving and loading facts"""
        # Establish facts
        fact_id_1, _ = self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer"
        )
        fact_id_2, _ = self.fs.establish_fact(
            fact_type=FactType.RELATIONSHIP,
            subject="Linda",
            predicate="sister_of",
            object="Marcus"
        )

        # Create new instance (should load persisted facts)
        fs2 = FactSystem(self.test_session)

        # Verify facts loaded
        self.assertEqual(len(fs2.facts), 2)
        self.assertIsNotNone(fs2.get_fact_by_id(fact_id_1))
        self.assertIsNotNone(fs2.get_fact_by_id(fact_id_2))

        # Verify indexes rebuilt
        marcus_facts = fs2.query_facts(subject="Marcus")
        self.assertEqual(len(marcus_facts), 1)

    def test_invalidate_fact(self):
        """Test invalidating a fact"""
        fact_id, _ = self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer"
        )

        # Invalidate
        success = self.fs.invalidate_fact(fact_id, "Retconned in episode 2")
        self.assertTrue(success)

        fact = self.fs.get_fact_by_id(fact_id)
        self.assertEqual(fact.status, FactStatus.INVALIDATED)
        self.assertIn("INVALIDATED", fact.context)

    def test_relationship_facts(self):
        """Test relationship-type facts"""
        fact_id, conflict = self.fs.establish_fact(
            fact_type=FactType.RELATIONSHIP,
            subject="Linda",
            predicate="is_sister_of",
            object="Marcus",
            authority=FactAuthority.SCENE_DECLARED
        )

        self.assertIsNone(conflict)

        fact = self.fs.get_fact_by_id(fact_id)
        self.assertEqual(fact.subject, "Linda")
        self.assertEqual(fact.object, "Marcus")
        self.assertIn("sister", fact.statement.lower())

    def test_validate_statement(self):
        """Test statement validation against facts"""
        # Establish fact
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer",
            authority=FactAuthority.SYSTEM_CANONICAL
        )

        # Validate conflicting statement
        result = self.fs.validate_statement(
            "Marcus is a bartender",
            {
                'subject': 'Marcus',
                'predicate': 'occupation',
                'value': 'bartender',
                'authority': FactAuthority.INFERRED
            }
        )

        self.assertFalse(result['valid'])
        self.assertTrue(len(result['conflicts']) > 0)
        self.assertTrue(len(result['warnings']) > 0)

    def test_query_with_min_authority(self):
        """Test querying with minimum authority filter"""
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="hobby",
            value="gaming",
            authority=FactAuthority.INFERRED
        )
        self.fs.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="engineer",
            authority=FactAuthority.SYSTEM_CANONICAL
        )

        # Query with high minimum authority
        high_auth_facts = self.fs.query_facts(
            subject="Marcus",
            min_authority=FactAuthority.SYSTEM_CANONICAL
        )
        self.assertEqual(len(high_auth_facts), 1)
        self.assertEqual(high_auth_facts[0].value, "engineer")

        # Query with low minimum authority
        all_facts = self.fs.query_facts(
            subject="Marcus",
            min_authority=FactAuthority.INFERRED
        )
        self.assertEqual(len(all_facts), 2)


if __name__ == "__main__":
    unittest.main()
