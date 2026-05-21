"""
Test suite for Mention System integration with SceneNPCParser.

Tests that mention validation works correctly during NPC spawning.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent))

from mention_system import MentionSystem, MentionType, MentionSource, PresenceConfidence
from scene_npc_parser import SceneNPCParser


class TestMentionParserIntegration(unittest.TestCase):
    """Test SceneNPCParser integration with Mention System"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_parser_session"

        # Create mention system
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # Create parser with mention system
        self.parser = SceneNPCParser(mention_system=self.mention_system)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_parser_has_mention_system(self):
        """Test that SceneNPCParser properly stores mention_system reference"""
        self.assertIsNotNone(self.parser.mention_system)
        self.assertEqual(self.parser.mention_system, self.mention_system)

    def test_validate_spawn_no_mention_history(self):
        """Test validation passes when actor has no mention history"""
        should_spawn, reason = self.parser._validate_spawn_against_mentions("Marcus", "Bar")

        self.assertTrue(should_spawn)
        self.assertIn("No mention history", reason)

    def test_validate_spawn_consistent_location(self):
        """Test validation passes when spawn location matches last mention"""
        # Record mention at Bar
        self.mention_system.record_physical_presence(
            "Marcus",
            "Bar",
            "Marcus at the bar",
            turn_number=5,
            scene_id="scene_001"
        )

        # Validate spawning at same location
        should_spawn, reason = self.parser._validate_spawn_against_mentions("Marcus", "Bar")

        self.assertTrue(should_spawn)
        self.assertIn("consistent", reason.lower())

    def test_validate_spawn_conflicting_location_high_confidence(self):
        """Test validation fails when spawn location conflicts with high-confidence mention"""
        # Record CONFIRMED mention at Studio
        self.mention_system.record_physical_presence(
            "Marcus",
            "Studio",
            "Marcus working at his studio",
            turn_number=5,
            scene_id="scene_001"
        )

        # Try to spawn at different location
        should_spawn, reason = self.parser._validate_spawn_against_mentions("Marcus", "Bar")

        self.assertFalse(should_spawn)
        self.assertIn("conflict", reason.lower())
        self.assertIn("Studio", reason)

    def test_validate_spawn_after_departure(self):
        """Test validation passes when actor was mentioned departing"""
        # Record departure from Studio
        self.mention_system.record_departure(
            "Marcus",
            origin="Studio",
            destination="Unknown",
            context="Marcus leaves the studio",
            turn_number=5,
            scene_id="scene_001"
        )

        # Spawning elsewhere should be allowed
        should_spawn, reason = self.parser._validate_spawn_against_mentions("Marcus", "Bar")

        self.assertTrue(should_spawn)
        self.assertIn("departing", reason.lower())

    def test_validate_spawn_after_arrival(self):
        """Test validation passes when actor was mentioned arriving at spawn location"""
        # Record arrival at Bar
        self.mention_system.record_arrival(
            "Marcus",
            destination="Bar",
            origin="Studio",
            context="Marcus walks into the bar",
            turn_number=5,
            scene_id="scene_001"
        )

        # Spawning at Bar should be allowed
        should_spawn, reason = self.parser._validate_spawn_against_mentions("Marcus", "Bar")

        self.assertTrue(should_spawn)
        # Arrival at Bar creates location consistency, so either "arriving" or "consistent" is valid
        self.assertTrue("arriving" in reason.lower() or "consistent" in reason.lower())

    def test_validate_spawn_low_confidence_allows_spawn(self):
        """Test validation passes with warning for low-confidence mentions"""
        # Record low-confidence mention
        self.mention_system.record_mention(
            actor_name="Marcus",
            mention_type=MentionType.INQUIRY,
            location="Studio",
            location_confidence=PresenceConfidence.LOW,
            source=MentionSource.NPC_DIALOGUE,
            turn_number=5,
            scene_id="scene_001",
            context="Someone asks about Marcus"
        )

        # Should allow spawn but log warning
        should_spawn, reason = self.parser._validate_spawn_against_mentions("Marcus", "Bar")

        self.assertTrue(should_spawn)
        self.assertIn("low-confidence", reason.lower())

    def test_check_actor_recently_mentioned_true(self):
        """Test detection of recently mentioned actors"""
        # Record recent mention
        self.mention_system.record_physical_presence(
            "Marcus",
            "Bar",
            "Marcus at the bar",
            turn_number=5,
            scene_id="scene_001"
        )

        recently_mentioned = self.parser._check_actor_recently_mentioned("Marcus", max_turns=10)

        self.assertTrue(recently_mentioned)

    def test_check_actor_recently_mentioned_false(self):
        """Test that actors with no recent mentions return False"""
        recently_mentioned = self.parser._check_actor_recently_mentioned("UnknownActor", max_turns=10)

        self.assertFalse(recently_mentioned)

    def test_graceful_degradation_without_mention_system(self):
        """Test that SceneNPCParser works without mention_system"""
        # Create parser without mention system
        parser_no_mentions = SceneNPCParser(mention_system=None)

        self.assertIsNone(parser_no_mentions.mention_system)

        # Validation should always pass
        should_spawn, reason = parser_no_mentions._validate_spawn_against_mentions("Marcus", "Bar")
        self.assertTrue(should_spawn)
        self.assertIn("No mention system", reason)

        # Check recent mentions should return False
        recently_mentioned = parser_no_mentions._check_actor_recently_mentioned("Marcus")
        self.assertFalse(recently_mentioned)


class TestMentionParserValidationScenarios(unittest.TestCase):
    """Test complex validation scenarios"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_validation_session"

        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        self.parser = SceneNPCParser(mention_system=self.mention_system)

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_scenario_actor_travels_studio_to_bar(self):
        """Test scenario: Actor departs Studio, then arrives at Bar"""
        # Turn 1: Marcus at Studio
        self.mention_system.record_physical_presence(
            "Marcus", "Studio", "Marcus at studio", turn_number=1, scene_id="scene_001"
        )

        # Turn 2: Marcus leaves Studio
        self.mention_system.record_departure(
            "Marcus", origin="Studio", destination="Bar",
            context="Marcus leaves for Bar", turn_number=2, scene_id="scene_001"
        )

        # Turn 3: Try to spawn at Bar (should succeed)
        should_spawn, reason = self.parser._validate_spawn_against_mentions("Marcus", "Bar")
        self.assertTrue(should_spawn)

    def test_scenario_actor_mentioned_in_dialogue_elsewhere(self):
        """Test scenario: Actor mentioned in dialogue at different location"""
        # Someone mentions Marcus being at Studio (low confidence)
        self.mention_system.record_mention(
            actor_name="Marcus",
            mention_type=MentionType.MESSAGE,
            location="Studio",
            location_confidence=PresenceConfidence.LOW,
            source=MentionSource.NPC_DIALOGUE,
            turn_number=5,
            scene_id="scene_001",
            context="Someone says 'Marcus is at the studio'"
        )

        # Try to spawn at Bar (should succeed with warning)
        should_spawn, reason = self.parser._validate_spawn_against_mentions("Marcus", "Bar")
        self.assertTrue(should_spawn)
        self.assertIn("low-confidence", reason.lower())

    def test_scenario_actor_confirmed_present_elsewhere(self):
        """Test scenario: Actor confirmed present at different location"""
        # Marcus confirmed at Studio (turn 10)
        self.mention_system.record_physical_presence(
            "Marcus", "Studio", "Marcus working at studio",
            turn_number=10, scene_id="scene_005"
        )

        # Try to spawn at Bar (should fail)
        should_spawn, reason = self.parser._validate_spawn_against_mentions("Marcus", "Bar")
        self.assertFalse(should_spawn)
        self.assertIn("conflict", reason.lower())


if __name__ == '__main__':
    unittest.main()
