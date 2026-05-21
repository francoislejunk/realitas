"""
Test suite for Mention System integration with ConductorAgent.

Tests that actor mentions are properly extracted from NPC dialogue.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent))

from mention_system import MentionSystem, MentionType, MentionSource, PresenceConfidence
from agents.conductor_agent import ConductorAgent


class TestMentionConductorIntegration(unittest.TestCase):
    """Test ConductorAgent integration with Mention System"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_conductor_session"

        # Create mention system
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # Create mock logger
        self.mock_logger = Mock()
        self.mock_logger.log_system = Mock()

        # Create conductor agent with mention system
        self.conductor_agent = ConductorAgent(
            logger=self.mock_logger,
            scene_description="Test scene",
            mention_system=self.mention_system
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_conductor_agent_has_mention_system(self):
        """Test that ConductorAgent properly stores mention_system reference"""
        self.assertIsNotNone(self.conductor_agent.mention_system)
        self.assertEqual(self.conductor_agent.mention_system, self.mention_system)

    def test_get_actor_mention_context_no_mentions(self):
        """Test _get_actor_mention_context returns empty string for unknown actor"""
        context = self.conductor_agent._get_actor_mention_context("UnknownActor")
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
        context = self.conductor_agent._get_actor_mention_context("Marcus")

        self.assertIn("Marcus", context)
        self.assertIn("Studio", context)
        self.assertIn("confirmed", context.lower())

    def test_extract_dialogue_mentions_i_saw_pattern(self):
        """Test extraction of 'I saw [Actor] at [Location]' pattern"""
        dialogue = "I saw Marcus at the Studio yesterday."

        self.conductor_agent._extract_dialogue_mentions(
            dialogue=dialogue,
            speaker_name="Linda",
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertEqual(len(mentions), 1)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.location, "the")  # Simple heuristic limitation
        self.assertEqual(mention.mention_type, MentionType.ELSEWHERE_CURRENT)
        self.assertEqual(mention.source, MentionSource.NPC_DIALOGUE)

    def test_extract_dialogue_mentions_is_at_pattern(self):
        """Test extraction of '[Actor] is at [Location]' pattern"""
        dialogue = "Marcus is at Studio working on his music."

        self.conductor_agent._extract_dialogue_mentions(
            dialogue=dialogue,
            speaker_name="Linda",
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertEqual(len(mentions), 1)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.location, "Studio")
        self.assertEqual(mention.mention_type, MentionType.ELSEWHERE_CURRENT)
        self.assertEqual(mention.source, MentionSource.NPC_DIALOGUE)

    def test_extract_dialogue_mentions_was_at_pattern(self):
        """Test extraction of '[Actor] was at [Location]' pattern"""
        dialogue = "Marcus was at Bar last night."

        self.conductor_agent._extract_dialogue_mentions(
            dialogue=dialogue,
            speaker_name="Linda",
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertEqual(len(mentions), 1)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.location, "Bar")
        self.assertEqual(mention.mention_type, MentionType.ELSEWHERE_PAST)
        self.assertEqual(mention.source, MentionSource.NPC_DIALOGUE)

    def test_extract_dialogue_mentions_rumor_pattern(self):
        """Test extraction of 'I heard [Actor]...' pattern as rumor"""
        dialogue = "I heard Marcus got a new recording contract."

        self.conductor_agent._extract_dialogue_mentions(
            dialogue=dialogue,
            speaker_name="Linda",
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertEqual(len(mentions), 1)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.mention_type, MentionType.RUMOR)
        self.assertEqual(mention.source, MentionSource.NPC_DIALOGUE)

    def test_extract_dialogue_mentions_departing_pattern(self):
        """Test extraction of '[Actor] left for [Location]' pattern"""
        dialogue = "Marcus left for Studio this morning."

        self.conductor_agent._extract_dialogue_mentions(
            dialogue=dialogue,
            speaker_name="Linda",
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertEqual(len(mentions), 1)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.destination, "Studio")
        self.assertEqual(mention.mention_type, MentionType.DEPARTING)
        self.assertEqual(mention.source, MentionSource.NPC_DIALOGUE)

    def test_extract_dialogue_mentions_no_patterns(self):
        """Test that dialogue with no mention patterns doesn't create mentions"""
        dialogue = "The weather is nice today."

        self.conductor_agent._extract_dialogue_mentions(
            dialogue=dialogue,
            speaker_name="Linda",
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify no mentions were recorded
        mentions = self.mention_system.query_mentions()
        self.assertEqual(len(mentions), 0)

    def test_extract_dialogue_mentions_multiple_patterns(self):
        """Test extracting multiple mentions from single dialogue"""
        dialogue = "I saw Marcus at Studio, and I heard Linda went to Bar."

        self.conductor_agent._extract_dialogue_mentions(
            dialogue=dialogue,
            speaker_name="Sam",
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
        """Test that ConductorAgent works without mention_system"""
        # Create conductor without mention system
        conductor_no_mentions = ConductorAgent(
            logger=self.mock_logger,
            scene_description="Test scene",
            mention_system=None
        )

        # These should not crash
        context = conductor_no_mentions._get_actor_mention_context("Actor")
        self.assertEqual(context, "")

        # _extract_dialogue_mentions should not crash
        try:
            conductor_no_mentions._extract_dialogue_mentions(
                dialogue="Test dialogue",
                speaker_name="TestNPC",
                turn_number=1,
                scene_id="scene_001"
            )
        except Exception as e:
            self.fail(f"_extract_dialogue_mentions should not crash without mention_system: {e}")

    def test_extract_dialogue_mentions_empty_dialogue(self):
        """Test that empty dialogue doesn't cause errors"""
        self.conductor_agent._extract_dialogue_mentions(
            dialogue="",
            speaker_name="Linda",
            turn_number=5,
            scene_id="scene_test"
        )

        # Should not crash and should not create mentions
        mentions = self.mention_system.query_mentions()
        self.assertEqual(len(mentions), 0)


class TestMentionConductorDialogueGeneration(unittest.TestCase):
    """Test dialogue generation with mention tracking"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_dialogue_gen_session"

        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        self.mock_logger = Mock()
        self.mock_logger.log_system = Mock()

        self.conductor_agent = ConductorAgent(
            logger=self.mock_logger,
            scene_description="Test scene",
            mention_system=self.mention_system
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch('agents.decider_agent.DeciderAgent.determine_nua_proaction')
    @patch('agents.interpreter_agent.InterpreterAgent.validate_and_repair_proactor')
    def test_determine_nua_proaction_extracts_mentions(self, mock_validate, mock_determine):
        """Test that determine_nua_proaction extracts mentions from dialogue"""
        # Mock the proaction determination
        mock_determine.return_value = {
            'action_description': 'Speaking',
            'dialogue': 'I saw Marcus at Studio yesterday.'
        }
        mock_validate.return_value = {
            'action_description': 'Speaking',
            'dialogue': 'I saw Marcus at Studio yesterday.'
        }

        # Create mock actors
        mock_proactor = Mock()
        mock_proactor.sheet = Mock()
        mock_proactor.sheet.name = "Linda"
        mock_proactor.is_inanimate = False

        mock_reactor = Mock()
        mock_reactor.sheet = Mock()
        mock_reactor.sheet.name = "Sam"

        # Call determine_nua_proaction
        result = self.conductor_agent.determine_nua_proaction(
            proactor=mock_proactor,
            reactor=mock_reactor,
            context_guidance={'turn_number': 5, 'scene_id': 'scene_test'}
        )

        # Verify action was returned
        self.assertIsNotNone(result)
        self.assertEqual(result['dialogue'], 'I saw Marcus at Studio yesterday.')

        # Verify mention was extracted
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)

    @patch('agents.decider_agent.DeciderAgent.determine_nua_reaction')
    @patch('agents.interpreter_agent.InterpreterAgent.validate_and_repair_reactor')
    def test_determine_nua_reaction_extracts_mentions(self, mock_validate, mock_determine):
        """Test that determine_nua_reaction extracts mentions from dialogue"""
        # Mock the reaction determination
        mock_determine.return_value = {
            'action_description': 'Responding',
            'dialogue': 'Marcus is at Bar right now.'
        }
        mock_validate.return_value = {
            'action_description': 'Responding',
            'dialogue': 'Marcus is at Bar right now.'
        }

        # Create mock actors
        mock_proactor = Mock()
        mock_proactor.sheet = Mock()
        mock_proactor.sheet.name = "Sam"

        mock_reactor = Mock()
        mock_reactor.sheet = Mock()
        mock_reactor.sheet.name = "Linda"
        mock_reactor.is_inanimate = False

        # Call determine_nua_reaction
        result = self.conductor_agent.determine_nua_reaction(
            proactor=mock_proactor,
            proactor_action_data={'dialogue': 'Where is Marcus?'},
            reactor=mock_reactor,
            context_guidance={'turn_number': 5, 'scene_id': 'scene_test'}
        )

        # Verify action was returned
        self.assertIsNotNone(result)
        self.assertEqual(result['dialogue'], 'Marcus is at Bar right now.')

        # Verify mention was extracted
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)


if __name__ == '__main__':
    unittest.main()
