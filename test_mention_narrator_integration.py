"""
Test suite for Mention System integration with NarratorAgent.

Tests that actor mentions are properly extracted from generated narratives.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent))

from mention_system import MentionSystem, MentionType, MentionSource, PresenceConfidence
from agents.narrator_agent import NarratorAgent


class TestMentionNarratorIntegration(unittest.TestCase):
    """Test NarratorAgent integration with Mention System"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_narrator_session"

        # Create mention system
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # Create narrator agent with mention system
        self.narrator_agent = NarratorAgent(
            rag_system=None,
            key_memories_system=None,
            mention_system=self.mention_system
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_narrator_agent_has_mention_system(self):
        """Test that NarratorAgent properly stores mention_system reference"""
        self.assertIsNotNone(self.narrator_agent.mention_system)
        self.assertEqual(self.narrator_agent.mention_system, self.mention_system)

    def test_get_actor_mention_context_no_mentions(self):
        """Test _get_actor_mention_context returns empty string for unknown actor"""
        context = self.narrator_agent._get_actor_mention_context("UnknownActor")
        self.assertEqual(context, "")

    def test_get_actor_mention_context_with_mention(self):
        """Test _get_actor_mention_context returns formatted context"""
        # Record a mention
        self.mention_system.record_physical_presence(
            "Marcus",
            "Studio",
            "Marcus at his mixing board",
            turn_number=1,
            scene_id="scene_001"
        )

        # Get context
        context = self.narrator_agent._get_actor_mention_context("Marcus")

        self.assertIn("Marcus", context)
        self.assertIn("Studio", context)
        self.assertIn("confirmed", context.lower())

    def test_extract_narrative_mentions_physical_presence(self):
        """Test extraction of physical presence descriptions"""
        narrative = "Marcus stands at the bar, waiting patiently for his drink."
        actors_in_scene = ["Marcus"]

        self.narrator_agent._extract_narrative_mentions(
            narrative=narrative,
            actors_in_scene=actors_in_scene,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.mention_type, MentionType.PHYSICAL_PRESENCE)
        self.assertEqual(mention.source, MentionSource.NARRATIVE)

    def test_extract_narrative_mentions_arrival_pattern(self):
        """Test extraction of arrival patterns"""
        narrative = "Marcus walks into the Studio with a confident stride."

        self.narrator_agent._extract_narrative_mentions(
            narrative=narrative,
            actors_in_scene=[],
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.mention_type, MentionType.ARRIVING)
        self.assertEqual(mention.source, MentionSource.NARRATIVE)
        self.assertEqual(mention.destination, "the")  # Simple heuristic limitation

    def test_extract_narrative_mentions_departure_pattern(self):
        """Test extraction of departure patterns"""
        narrative = "Marcus leaves for Bar after finishing his work."

        self.narrator_agent._extract_narrative_mentions(
            narrative=narrative,
            actors_in_scene=[],
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.mention_type, MentionType.DEPARTING)
        self.assertEqual(mention.source, MentionSource.NARRATIVE)

    def test_extract_narrative_mentions_past_presence(self):
        """Test extraction of past presence patterns"""
        narrative = "Marcus was here earlier, but he left before you arrived."

        self.narrator_agent._extract_narrative_mentions(
            narrative=narrative,
            actors_in_scene=[],
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.mention_type, MentionType.ELSEWHERE_PAST)
        self.assertEqual(mention.source, MentionSource.NARRATIVE)

    def test_extract_narrative_mentions_no_patterns(self):
        """Test that narrative with no mention patterns doesn't create mentions"""
        narrative = "The room is dimly lit. You can hear soft music playing."

        self.narrator_agent._extract_narrative_mentions(
            narrative=narrative,
            actors_in_scene=[],
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify no mentions were recorded
        mentions = self.mention_system.query_mentions()
        self.assertEqual(len(mentions), 0)

    def test_extract_narrative_mentions_multiple_patterns(self):
        """Test extracting multiple mentions from single narrative"""
        narrative = "Marcus stands at the corner. Linda walks into Bar with a smile."
        actors_in_scene = ["Marcus"]

        self.narrator_agent._extract_narrative_mentions(
            narrative=narrative,
            actors_in_scene=actors_in_scene,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mentions were recorded
        all_mentions = self.mention_system.query_mentions()
        self.assertGreater(len(all_mentions), 0)

        # Check for Marcus mention
        marcus_mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(marcus_mentions), 0)

        # Check for Linda mention
        linda_mentions = self.mention_system.query_mentions(actor_name="Linda")
        self.assertGreater(len(linda_mentions), 0)

    def test_graceful_degradation_without_mention_system(self):
        """Test that NarratorAgent works without mention_system"""
        # Create narrator without mention system
        narrator_no_mentions = NarratorAgent(
            rag_system=None,
            key_memories_system=None,
            mention_system=None
        )

        # These should not crash
        context = narrator_no_mentions._get_actor_mention_context("Actor")
        self.assertEqual(context, "")

        # _extract_narrative_mentions should not crash
        try:
            narrator_no_mentions._extract_narrative_mentions(
                narrative="Test narrative",
                actors_in_scene=["TestActor"],
                turn_number=1,
                scene_id="scene_001"
            )
        except Exception as e:
            self.fail(f"_extract_narrative_mentions should not crash without mention_system: {e}")

    def test_extract_narrative_mentions_empty_narrative(self):
        """Test that empty narrative doesn't cause errors"""
        self.narrator_agent._extract_narrative_mentions(
            narrative="",
            actors_in_scene=["Marcus"],
            turn_number=5,
            scene_id="scene_test"
        )

        # Should not crash and should not create mentions
        mentions = self.mention_system.query_mentions()
        self.assertEqual(len(mentions), 0)

    def test_extract_narrative_mentions_sitting_pattern(self):
        """Test extraction of sitting pattern for physical presence"""
        narrative = "You see Marcus sits in the corner booth, nursing his drink."
        actors_in_scene = ["Marcus"]

        self.narrator_agent._extract_narrative_mentions(
            narrative=narrative,
            actors_in_scene=actors_in_scene,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.mention_type, MentionType.PHYSICAL_PRESENCE)


class TestMentionNarratorNarrativeGeneration(unittest.TestCase):
    """Test narrative generation with mention tracking"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_narrative_gen_session"

        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        self.narrator_agent = NarratorAgent(
            rag_system=None,
            key_memories_system=None,
            mention_system=self.mention_system
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch.object(NarratorAgent, '_call_llm')
    def test_build_action_narrative_extracts_mentions(self, mock_llm):
        """Test that _build_action_narrative extracts mentions"""
        # Mock LLM response with mention patterns
        mock_llm.return_value = "Marcus stands at the bar and prepares to strike."

        # Create mock data
        proactor_data = {
            'name': 'Marcus',
            'is_user_actor': False,
            'utas_factors': {
                'skill': {'name': 'Combat'},
                'skill_val': 5,
                's_trait_to_use': 'AGILITY',
                's_trait_val': 4,
                'status_to_shift': 'SPIRIT',
                'stress_level': 3,
                'serendipity': 0,
                'status_modifier': 0
            },
            'narrative_description': 'strikes at the opponent'
        }
        reactor_data = {'name': 'Linda'}
        framing_guidance = {'turn_number': 10, 'scene_id': 'combat_scene'}

        # Call method
        narrative = self.narrator_agent._build_action_narrative(
            proactor_data, reactor_data, framing_guidance=framing_guidance
        )

        # Verify narrative was returned
        self.assertIsNotNone(narrative)
        self.assertIn("Marcus", narrative)

        # Verify mention was extracted
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)

    @patch.object(NarratorAgent, '_call_llm')
    def test_build_reaction_narrative_extracts_mentions(self, mock_llm):
        """Test that _build_reaction_narrative extracts mentions"""
        # Mock LLM response with mention patterns
        mock_llm.return_value = "You see Linda sits quickly, dodging the attack."

        # Create mock data
        proactor_data = {
            'name': 'Marcus',
            'narrative_description': 'strikes'
        }
        reactor_data = {
            'name': 'Linda',
            'is_user_actor': False,
            'utas_factors': {
                'skill': {'name': 'Dodge'},
                'skill_val': 4,
                's_trait_to_use': 'AGILITY',
                's_trait_val': 5,
                'status_to_shift': 'BODY',
                'stress_level': 2,
                'serendipity': 1,
                'status_modifier': 0
            },
            'narrative_description': 'dodges'
        }
        framing_guidance = {'turn_number': 10, 'scene_id': 'combat_scene'}

        # Call method
        narrative = self.narrator_agent._build_reaction_narrative(
            proactor_data, reactor_data, framing_guidance=framing_guidance
        )

        # Verify narrative was returned
        self.assertIsNotNone(narrative)

        # Verify mention was extracted
        mentions = self.mention_system.query_mentions(actor_name="Linda")
        self.assertGreater(len(mentions), 0)


if __name__ == '__main__':
    unittest.main()
