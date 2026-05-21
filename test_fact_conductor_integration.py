"""
Integration test for Fact System + ConductorAgent

Tests that facts are extracted from NPC dialogue during exchanges.
"""

import unittest
from unittest.mock import Mock, MagicMock
from pathlib import Path
import shutil

from fact_system import FactSystem, FactType, FactAuthority
from agents.conductor_agent import ConductorAgent
from logbook.utas_logger import UTASLogger


class TestFactConductorIntegration(unittest.TestCase):
    """Test suite for Fact System + ConductorAgent integration"""

    def setUp(self):
        """Set up test environment"""
        self.test_session = "test_fact_conductor"
        self.test_dir = Path(f"sessions/{self.test_session}")

        # Clean up any previous test data
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # Create fact system
        self.fact_system = FactSystem(self.test_session)

        # Create mock logger
        self.logger = Mock(spec=UTASLogger)
        self.logger.log_system = Mock()

        # Create conductor with fact system
        self.conductor = ConductorAgent(
            logger=self.logger,
            scene_description="Test scene",
            fact_system=self.fact_system
        )

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_get_actor_facts(self):
        """Test retrieving formatted fact context"""
        # Establish some facts
        self.fact_system.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="studio engineer",
            authority=FactAuthority.SYSTEM_CANONICAL,
            source="test"
        )

        # Retrieve facts
        context = self.conductor._get_actor_facts("Marcus", max_facts=10)

        # Verify formatting
        self.assertIn("MARCUS", context.upper())
        self.assertIn("OCCUPATION", context.upper())
        self.assertIn("STUDIO ENGINEER", context.upper())

    def test_get_actor_facts_no_fact_system(self):
        """Test fact retrieval when fact_system is None"""
        conductor_no_facts = ConductorAgent(
            logger=self.logger,
            scene_description="Test scene",
            fact_system=None
        )

        context = conductor_no_facts._get_actor_facts("Marcus")
        self.assertEqual(context, "")

    def test_extract_dialogue_facts_occupation(self):
        """Test extracting occupation from dialogue"""
        dialogue = "I'm a studio engineer working on this project."

        self.conductor._extract_dialogue_facts(
            dialogue=dialogue,
            speaker_name="Marcus",
            target_name="Player",
            turn_number=5,
            scene_id="scene_001"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(subject="Marcus", predicate="occupation")
        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].authority, FactAuthority.DIALOGUE_MENTIONED)
        self.assertIn("studio engineer", facts[0].value)

    def test_extract_dialogue_facts_relationship(self):
        """Test extracting relationship from dialogue"""
        dialogue = "I'm Marcus's sister, and I've known him all my life."

        self.conductor._extract_dialogue_facts(
            dialogue=dialogue,
            speaker_name="Linda",
            target_name="Player",
            turn_number=8,
            scene_id="scene_002"
        )

        # Verify relationship fact created
        facts = self.fact_system.query_facts(subject="Linda", fact_type=FactType.RELATIONSHIP)
        self.assertGreater(len(facts), 0)

        sister_facts = [f for f in facts if f.predicate == "sister"]
        self.assertEqual(len(sister_facts), 1)
        self.assertEqual(sister_facts[0].object, "Marcus")
        self.assertEqual(sister_facts[0].authority, FactAuthority.DIALOGUE_MENTIONED)

    def test_extract_dialogue_facts_multiple_patterns(self):
        """Test extracting multiple facts from rich dialogue"""
        dialogue = "I work as a bartender here. I'm Tom's sister, actually."

        self.conductor._extract_dialogue_facts(
            dialogue=dialogue,
            speaker_name="Sarah",
            target_name="Player",
            turn_number=3,
            scene_id="scene_003"
        )

        # Should extract occupation
        occupation_facts = self.fact_system.query_facts(subject="Sarah", predicate="occupation")
        self.assertGreater(len(occupation_facts), 0, "Should extract occupation from dialogue")

        # Should extract relationship
        rel_facts = self.fact_system.query_facts(subject="Sarah", fact_type=FactType.RELATIONSHIP)
        self.assertGreater(len(rel_facts), 0, "Should extract relationship from dialogue")

    def test_extract_dialogue_no_facts(self):
        """Test dialogue extraction with no extractable facts"""
        dialogue = "The weather is nice today."

        initial_count = len(self.fact_system.facts)

        self.conductor._extract_dialogue_facts(
            dialogue=dialogue,
            speaker_name="Stranger",
            target_name="Player"
        )

        # No facts should be added
        self.assertEqual(len(self.fact_system.facts), initial_count)

    def test_validate_action_no_contradiction(self):
        """Test validating action that doesn't contradict facts"""
        # Establish fact
        self.fact_system.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="studio engineer",
            authority=FactAuthority.SYSTEM_CANONICAL,
            source="test"
        )

        # Action that aligns with fact
        action_data = {
            "dialogue": "I've been working on music production all day.",
            "action_description": "Marcus discusses his work"
        }

        warning = self.conductor._validate_action_against_facts(action_data, "Marcus")
        # Should not warn since no contradiction
        self.assertIsNone(warning)

    def test_validate_action_with_contradiction(self):
        """Test validating action that contradicts established facts"""
        # Establish fact
        self.fact_system.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="studio engineer",
            authority=FactAuthority.SYSTEM_CANONICAL,
            source="test"
        )

        # Action that contradicts
        action_data = {
            "dialogue": "I work as a bartender here.",
            "action_description": "Marcus discusses his occupation"
        }

        warning = self.conductor._validate_action_against_facts(action_data, "Marcus")
        # Should warn about contradiction
        self.assertIsNotNone(warning, "Should detect occupation contradiction")
        self.assertIn("studio engineer", warning)

    def test_validate_action_no_fact_system(self):
        """Test action validation when fact_system is None"""
        conductor_no_facts = ConductorAgent(
            logger=self.logger,
            scene_description="Test scene",
            fact_system=None
        )

        action_data = {"dialogue": "Test dialogue"}
        warning = conductor_no_facts._validate_action_against_facts(action_data, "Marcus")
        self.assertIsNone(warning)

    def test_determine_nua_proaction_extracts_facts(self):
        """Test that NUA proaction determination extracts facts from dialogue"""
        # Mock proactor and reactor
        proactor = Mock()
        proactor.sheet = Mock()
        proactor.sheet.name = "Marcus"
        proactor.is_inanimate = False

        reactor = Mock()
        reactor.sheet = Mock()
        reactor.sheet.name = "Player"

        # Mock the decider_agent to return action with dialogue
        self.conductor.decider_agent.determine_nua_proaction = Mock(return_value={
            "dialogue": "I'm a studio engineer working on the new album.",
            "action_description": "Marcus introduces himself"
        })

        # Mock interpreter validation
        self.conductor.interpreter_agent.validate_and_repair_proactor = Mock(side_effect=lambda x, *args: x)

        context_guidance = {"turn_number": 10, "scene_id": "scene_005"}

        # Call proaction determination
        result = self.conductor.determine_nua_proaction(
            proactor=proactor,
            reactor=reactor,
            context_guidance=context_guidance
        )

        # Verify dialogue was processed
        self.assertIsNotNone(result)

        # Verify fact was extracted
        facts = self.fact_system.query_facts(subject="Marcus", predicate="occupation")
        self.assertGreater(len(facts), 0, "Fact should have been extracted from dialogue")

    def test_determine_nua_reaction_extracts_facts(self):
        """Test that NUA reaction determination extracts facts from dialogue"""
        # Mock proactor and reactor
        proactor = Mock()
        proactor.sheet = Mock()
        proactor.sheet.name = "Player"

        reactor = Mock()
        reactor.sheet = Mock()
        reactor.sheet.name = "Linda"
        reactor.is_inanimate = False

        proactor_action = {"dialogue": "Who are you?"}

        # Mock the decider_agent to return reaction with dialogue
        self.conductor.decider_agent.determine_nua_reaction = Mock(return_value={
            "dialogue": "I'm Marcus's sister, Linda.",
            "action_description": "Linda responds"
        })

        # Mock interpreter validation
        self.conductor.interpreter_agent.validate_and_repair_reactor = Mock(side_effect=lambda x, *args: x)

        context_guidance = {"turn_number": 12, "scene_id": "scene_006"}

        # Call reaction determination
        result = self.conductor.determine_nua_reaction(
            proactor=proactor,
            proactor_action_data=proactor_action,
            reactor=reactor,
            context_guidance=context_guidance
        )

        # Verify dialogue was processed
        self.assertIsNotNone(result)

        # Verify relationship fact was extracted
        facts = self.fact_system.query_facts(subject="Linda", fact_type=FactType.RELATIONSHIP)
        self.assertGreater(len(facts), 0, "Relationship fact should have been extracted")


if __name__ == "__main__":
    unittest.main()
