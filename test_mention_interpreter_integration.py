"""
Test suite for Mention System integration with InterpreterAgent.

Tests that actor mentions are properly extracted from user input.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import sys
sys.path.insert(0, str(Path(__file__).parent))

from mention_system import MentionSystem, MentionType, MentionSource, PresenceConfidence
from agents.interpreter_agent import InterpreterAgent
from logbook.utas_logger import UTASLogger


class TestMentionInterpreterIntegration(unittest.TestCase):
    """Test InterpreterAgent integration with Mention System"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_interpreter_session"

        # Create mention system
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # Create logger
        self.logger = UTASLogger()

        # Create interpreter agent with mention system
        self.interpreter_agent = InterpreterAgent(
            logger=self.logger,
            scene_description="Test scene",
            tracker_agent=None,
            actor_manager=None,
            key_memories_system=None,
            rag_system=None,
            fact_system=None,
            mention_system=self.mention_system
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_interpreter_agent_has_mention_system(self):
        """Test that InterpreterAgent properly stores mention_system reference"""
        self.assertIsNotNone(self.interpreter_agent.mention_system)
        self.assertEqual(self.interpreter_agent.mention_system, self.mention_system)

    def test_get_actor_mention_context_no_mentions(self):
        """Test _get_actor_mention_context returns empty string for unknown actor"""
        context = self.interpreter_agent._get_actor_mention_context("UnknownActor")
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
        context = self.interpreter_agent._get_actor_mention_context("Marcus")

        self.assertIn("Marcus", context)
        self.assertIn("Studio", context)
        self.assertIn("confirmed", context.lower())

    def test_extract_user_input_mentions_ask_pattern(self):
        """Test extraction of 'ask [Actor] about...' pattern"""
        user_input = "I want to ask Marcus about his music."
        actor_name = "Player"

        self.interpreter_agent._extract_user_input_mentions(
            user_input=user_input,
            actor_name=actor_name,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.mention_type, MentionType.INQUIRY)
        self.assertEqual(mention.source, MentionSource.USER_INPUT)

    def test_extract_user_input_mentions_movement_pattern(self):
        """Test extraction of 'go to [Location]' pattern"""
        user_input = "I go to Bar to meet my friend."
        actor_name = "Player"

        self.interpreter_agent._extract_user_input_mentions(
            user_input=user_input,
            actor_name=actor_name,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Player")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Player")
        self.assertEqual(mention.mention_type, MentionType.INTENTION)
        self.assertEqual(mention.source, MentionSource.USER_INPUT)
        self.assertIn("Bar", mention.location or "")

    def test_extract_user_input_mentions_where_is_pattern(self):
        """Test extraction of 'where is [Actor]?' pattern"""
        user_input = "Where is Linda? I need to find her."
        actor_name = "Player"

        self.interpreter_agent._extract_user_input_mentions(
            user_input=user_input,
            actor_name=actor_name,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Linda")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Linda")
        self.assertEqual(mention.mention_type, MentionType.INQUIRY)
        self.assertEqual(mention.source, MentionSource.USER_INPUT)
        self.assertEqual(mention.location_confidence, PresenceConfidence.LOW)

    def test_extract_user_input_mentions_dialogue_pattern(self):
        """Test extraction of actor mentions in quoted dialogue"""
        user_input = 'I tell the guard "Marcus sent me, he can vouch for me."'
        actor_name = "Player"

        self.interpreter_agent._extract_user_input_mentions(
            user_input=user_input,
            actor_name=actor_name,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.mention_type, MentionType.MESSAGE)
        self.assertEqual(mention.source, MentionSource.USER_INPUT)

    def test_extract_user_input_mentions_no_patterns(self):
        """Test that input with no mention patterns doesn't create mentions"""
        user_input = "I look around the room carefully."
        actor_name = "Player"

        self.interpreter_agent._extract_user_input_mentions(
            user_input=user_input,
            actor_name=actor_name,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify no mentions were recorded
        mentions = self.mention_system.query_mentions()
        self.assertEqual(len(mentions), 0)

    def test_extract_user_input_mentions_multiple_patterns(self):
        """Test extracting multiple mentions from single input"""
        user_input = "I talk to Marcus, then I head to Bar."
        actor_name = "Player"

        self.interpreter_agent._extract_user_input_mentions(
            user_input=user_input,
            actor_name=actor_name,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mentions were recorded
        all_mentions = self.mention_system.query_mentions()
        self.assertGreater(len(all_mentions), 0)

        # Check for Marcus mention (INQUIRY - from "talk to Marcus")
        marcus_mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(marcus_mentions), 0)
        self.assertEqual(marcus_mentions[0].mention_type, MentionType.INQUIRY)

        # Check for Player's INTENTION to go to Bar
        player_mentions = self.mention_system.query_mentions(actor_name="Player")
        self.assertGreater(len(player_mentions), 0)
        self.assertEqual(player_mentions[0].mention_type, MentionType.INTENTION)

    def test_extract_user_input_mentions_empty_input(self):
        """Test that empty input doesn't cause errors"""
        self.interpreter_agent._extract_user_input_mentions(
            user_input="",
            actor_name="Player",
            turn_number=5,
            scene_id="scene_test"
        )

        # Should not crash and should not create mentions
        mentions = self.mention_system.query_mentions()
        self.assertEqual(len(mentions), 0)

    def test_graceful_degradation_without_mention_system(self):
        """Test that InterpreterAgent works without mention_system"""
        # Create interpreter without mention system
        interpreter_no_mentions = InterpreterAgent(
            logger=self.logger,
            scene_description="Test scene",
            tracker_agent=None,
            actor_manager=None,
            key_memories_system=None,
            rag_system=None,
            fact_system=None,
            mention_system=None
        )

        # These should not crash
        context = interpreter_no_mentions._get_actor_mention_context("Actor")
        self.assertEqual(context, "")

        # _extract_user_input_mentions should not crash
        try:
            interpreter_no_mentions._extract_user_input_mentions(
                user_input="Test input",
                actor_name="Player",
                turn_number=1,
                scene_id="scene_001"
            )
        except Exception as e:
            self.fail(f"_extract_user_input_mentions should not crash without mention_system: {e}")

    def test_extract_user_input_mentions_talk_to_pattern(self):
        """Test extraction of 'talk to [Actor]' pattern"""
        user_input = "I want to talk to Linda about the situation."
        actor_name = "Player"

        self.interpreter_agent._extract_user_input_mentions(
            user_input=user_input,
            actor_name=actor_name,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Linda")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Linda")
        self.assertEqual(mention.mention_type, MentionType.INQUIRY)

    def test_extract_user_input_mentions_head_to_pattern(self):
        """Test extraction of 'head to [Location]' pattern"""
        user_input = "I head to Studio to work on my music."
        actor_name = "Player"

        self.interpreter_agent._extract_user_input_mentions(
            user_input=user_input,
            actor_name=actor_name,
            turn_number=5,
            scene_id="scene_test"
        )

        # Verify mention was recorded
        mentions = self.mention_system.query_mentions(actor_name="Player")
        self.assertGreater(len(mentions), 0)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Player")
        self.assertEqual(mention.mention_type, MentionType.INTENTION)
        self.assertIn("Studio", mention.location or "")


class TestMentionInterpreterActionProcessing(unittest.TestCase):
    """Test mention extraction during action processing"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_action_session"

        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        self.logger = UTASLogger()

        self.interpreter_agent = InterpreterAgent(
            logger=self.logger,
            scene_description="Test scene",
            tracker_agent=None,
            actor_manager=None,
            key_memories_system=None,
            rag_system=None,
            fact_system=None,
            mention_system=self.mention_system
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    @patch.object(InterpreterAgent, '_call_llm_for_json')
    @patch.object(InterpreterAgent, '_build_interpretation_prompt')
    def test_interpret_user_action_extracts_mentions(self, mock_build_prompt, mock_llm):
        """Test that interpret_user_action extracts mentions"""
        # Mock LLM response
        mock_llm.return_value = {
            'narrative_description': 'Player asks Marcus about music',
            'utas_factors': {
                'skill': {'name': 'Social'},
                'skill_val': 3,
                's_trait_to_use': 'CHARM',
                's_trait_val': 4,
                'status_to_shift': 'SPIRIT',
                'stress_level': 2,
                'serendipity': 0
            }
        }
        mock_build_prompt.return_value = "test prompt"

        # Create mock actor
        mock_actor = Mock()
        mock_actor.sheet = Mock()
        mock_actor.sheet.name = "Player"
        mock_actor.sheet.skills = {'Social': 3}
        mock_actor.sheet.inventory = []
        mock_actor.sheet.effects = []
        mock_actor.sheet.s_factors = Mock()
        mock_actor.sheet.s_factors.get_factor = Mock(return_value=4)
        mock_actor.is_user_actor = True

        user_input = "I ask Marcus about his music career."

        # Call method
        try:
            result = self.interpreter_agent.interpret_user_action(
                user_input=user_input,
                proactor=mock_actor
            )
        except Exception as e:
            # Expected to fail during validation, but mentions should be extracted
            pass

        # Verify mention was extracted
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)

    @patch.object(InterpreterAgent, '_call_llm_for_json')
    def test_detect_inquiry_or_action_extracts_mentions(self, mock_llm):
        """Test that detect_inquiry_or_action extracts mentions"""
        # Mock LLM response
        mock_llm.return_value = {
            'input_type': 'inquiry',
            'reasoning': 'User is asking a question'
        }

        # Create mock actors
        mock_proactor = Mock()
        mock_proactor.sheet = Mock()
        mock_proactor.sheet.name = "Player"

        mock_reactor = Mock()
        mock_reactor.sheet = Mock()
        mock_reactor.sheet.name = "NPC"

        user_input = "Where is Marcus? Have you seen him?"

        # Call method
        try:
            result = self.interpreter_agent.detect_inquiry_or_action(
                user_input=user_input,
                proactor=mock_proactor,
                reactor=mock_reactor
            )
        except Exception as e:
            # May fail during processing, but mentions should be extracted
            pass

        # Verify mention was extracted
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)


if __name__ == '__main__':
    unittest.main()
