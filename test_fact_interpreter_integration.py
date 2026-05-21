"""
Integration test for Fact System + InterpreterAgent

Tests that user declarations are extracted and validated against established facts.
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path
import shutil

from fact_system import FactSystem, FactType, FactAuthority
from agents.interpreter_agent import InterpreterAgent


class TestFactInterpreterIntegration(unittest.TestCase):
    """Test suite for Fact System + InterpreterAgent integration"""

    def setUp(self):
        """Set up test environment"""
        # Use unique session ID per test for isolation
        import uuid
        self.test_session = f"test_fact_interpreter_{uuid.uuid4().hex[:8]}"
        self.test_dir = Path(f"sessions/{self.test_session}")

        # Clean up any previous test data
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # Create fact system
        self.fact_system = FactSystem(self.test_session)

        # Create mock logger
        self.mock_logger = Mock()

        # Create interpreter agent with fact system
        self.interpreter = InterpreterAgent(
            logger=self.mock_logger,
            scene_description="Test scene",
            fact_system=self.fact_system
        )

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_extract_occupation_declaration_im_a(self):
        """Test extraction of occupation from 'I'm a doctor' pattern"""
        self.interpreter._extract_user_declarations(
            user_input="I'm a doctor and I need to examine the patient",
            actor_name="Marcus",
            turn_number=1,
            scene_id="scene_001"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(
            subject="Marcus",
            fact_type=FactType.ACTOR_IDENTITY,
            predicate="occupation"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("doctor", facts[0].value.lower())
        self.assertEqual(facts[0].authority, FactAuthority.USER_ESTABLISHED)

    def test_extract_occupation_declaration_i_am_an(self):
        """Test extraction of occupation from 'I am an engineer' pattern"""
        self.interpreter._extract_user_declarations(
            user_input="I am an engineer working on this project",
            actor_name="Sarah",
            turn_number=2,
            scene_id="scene_002"
        )

        facts = self.fact_system.query_facts(
            subject="Sarah",
            predicate="occupation"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("engineer", facts[0].value.lower())

    def test_extract_occupation_declaration_i_work_as(self):
        """Test extraction of occupation from 'I work as' pattern"""
        self.interpreter._extract_user_declarations(
            user_input="I work as a bartender here",
            actor_name="Jake",
            turn_number=3,
            scene_id="scene_003"
        )

        facts = self.fact_system.query_facts(
            subject="Jake",
            predicate="occupation"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("bartender", facts[0].value.lower())

    def test_extract_possession_declaration_i_own(self):
        """Test extraction of possession from 'I own' pattern"""
        self.interpreter._extract_user_declarations(
            user_input="I own a red Lamborghini Countach",
            actor_name="Marcus",
            turn_number=4,
            scene_id="scene_004"
        )

        facts = self.fact_system.query_facts(
            subject="Marcus",
            fact_type=FactType.ACTOR_POSSESSION,
            predicate="owns"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("Lamborghini", facts[0].value)
        self.assertEqual(facts[0].authority, FactAuthority.USER_ESTABLISHED)

    def test_extract_possession_declaration_i_have(self):
        """Test extraction of possession from 'I have' pattern"""
        self.interpreter._extract_user_declarations(
            user_input="I have a Glock 19 in my holster",
            actor_name="Detective Miller",
            turn_number=5,
            scene_id="scene_005"
        )

        facts = self.fact_system.query_facts(
            subject="Detective Miller",
            predicate="owns"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("Glock", facts[0].value)

    def test_extract_origin_declaration_im_from(self):
        """Test extraction of origin from 'I'm from' pattern"""
        self.interpreter._extract_user_declarations(
            user_input="I'm from Chicago originally",
            actor_name="Marcus",
            turn_number=6,
            scene_id="scene_006"
        )

        facts = self.fact_system.query_facts(
            subject="Marcus",
            fact_type=FactType.ACTOR_TRAIT,
            predicate="origin"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("Chicago", facts[0].value)
        self.assertEqual(facts[0].authority, FactAuthority.USER_ESTABLISHED)

    def test_extract_origin_declaration_i_grew_up_in(self):
        """Test extraction of origin from 'I grew up in' pattern"""
        self.interpreter._extract_user_declarations(
            user_input="I grew up in Los Angeles",
            actor_name="Sarah",
            turn_number=7,
            scene_id="scene_007"
        )

        facts = self.fact_system.query_facts(
            subject="Sarah",
            predicate="origin"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("Los Angeles", facts[0].value)

    def test_validate_no_contradiction(self):
        """Test that validation passes when no contradiction exists"""
        # Establish a fact
        self.fact_system.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="doctor",
            authority=FactAuthority.SCENE_DECLARED,
            source="test_setup"
        )

        # Validate input that doesn't contradict
        warning = self.interpreter._validate_action_against_facts(
            user_input="I need to treat this patient",
            actor_name="Marcus"
        )

        self.assertIsNone(warning)

    def test_validate_occupation_contradiction(self):
        """Test that validation detects occupation contradictions"""
        # Establish occupation
        self.fact_system.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="doctor",
            authority=FactAuthority.SCENE_DECLARED,
            source="test_setup"
        )

        # Try to state different occupation
        warning = self.interpreter._validate_action_against_facts(
            user_input="I'm a lawyer and I object to this!",
            actor_name="Marcus"
        )

        self.assertIsNotNone(warning)
        self.assertIn("doctor", warning.lower())
        self.assertIn("WARNING", warning)

    def test_validate_possession_contradiction_dont_have(self):
        """Test that validation detects possession contradictions"""
        # Establish possession
        self.fact_system.establish_fact(
            fact_type=FactType.ACTOR_POSSESSION,
            subject="Marcus",
            predicate="owns",
            value="red Lamborghini Countach",
            authority=FactAuthority.SCENE_DECLARED,
            source="test_setup"
        )

        # Try to deny possession
        warning = self.interpreter._validate_action_against_facts(
            user_input="I don't have a Lamborghini anymore",
            actor_name="Marcus"
        )

        self.assertIsNotNone(warning)
        self.assertIn("Lamborghini", warning)
        self.assertIn("WARNING", warning)

    def test_extract_multiple_declarations_in_one_input(self):
        """Test extraction of multiple declarations from single input"""
        self.interpreter._extract_user_declarations(
            user_input="I'm a doctor from Chicago and I own a red Ferrari",
            actor_name="Marcus",
            turn_number=8,
            scene_id="scene_008"
        )

        # Should extract occupation (first pattern matched)
        occupation_facts = self.fact_system.query_facts(
            subject="Marcus",
            predicate="occupation"
        )
        self.assertEqual(len(occupation_facts), 1)
        self.assertIn("doctor", occupation_facts[0].value.lower())

        # Note: Current implementation extracts one fact per category per call
        # This is acceptable behavior, prioritizing first mention

    def test_no_fact_system_graceful_degradation(self):
        """Test that interpreter works without fact system"""
        interpreter_no_facts = InterpreterAgent(
            logger=self.mock_logger,
            scene_description="Test scene",
            fact_system=None
        )

        # Should not raise error
        interpreter_no_facts._extract_user_declarations(
            user_input="I'm a doctor",
            actor_name="Test",
            turn_number=0,
            scene_id=""
        )

        warning = interpreter_no_facts._validate_action_against_facts(
            user_input="I'm a doctor",
            actor_name="Test"
        )

        self.assertIsNone(warning)

    def test_user_established_authority_overrides_scene_declared(self):
        """Test that USER_ESTABLISHED facts can override SCENE_DECLARED facts"""
        # Establish SCENE_DECLARED fact
        self.fact_system.establish_fact(
            fact_type=FactType.ACTOR_IDENTITY,
            subject="Marcus",
            predicate="occupation",
            value="bartender",
            authority=FactAuthority.SCENE_DECLARED,
            source="scene_generation"
        )

        # User declares different occupation (should supersede)
        self.interpreter._extract_user_declarations(
            user_input="I'm a doctor, not a bartender",
            actor_name="Marcus",
            turn_number=10,
            scene_id="scene_010"
        )

        # Should have USER_ESTABLISHED fact
        facts = self.fact_system.query_facts(
            subject="Marcus",
            predicate="occupation"
        )

        # Should find the USER_ESTABLISHED fact (it supersedes the SCENE_DECLARED one)
        user_facts = [f for f in facts if f.authority == FactAuthority.USER_ESTABLISHED]
        self.assertEqual(len(user_facts), 1)
        self.assertIn("doctor", user_facts[0].value.lower())

    def test_fact_tags_include_user_declared(self):
        """Test that extracted facts include 'user_declared' tag"""
        self.interpreter._extract_user_declarations(
            user_input="I'm a software engineer",
            actor_name="Alex",
            turn_number=11,
            scene_id="scene_011"
        )

        facts = self.fact_system.query_facts(
            subject="Alex",
            predicate="occupation"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("user_declared", facts[0].tags)
        self.assertIn("alex", facts[0].tags)
        self.assertIn("occupation", facts[0].tags)

    def test_extract_with_context_stored(self):
        """Test that full user input is stored as context"""
        full_input = "I'm a doctor and I've been practicing for 20 years"

        self.interpreter._extract_user_declarations(
            user_input=full_input,
            actor_name="Marcus",
            turn_number=12,
            scene_id="scene_012"
        )

        facts = self.fact_system.query_facts(
            subject="Marcus",
            predicate="occupation"
        )

        self.assertEqual(len(facts), 1)
        self.assertEqual(facts[0].context, full_input)

    def test_empty_input_graceful_handling(self):
        """Test that empty input is handled gracefully"""
        # Should not raise error
        self.interpreter._extract_user_declarations(
            user_input="",
            actor_name="Marcus",
            turn_number=13,
            scene_id="scene_013"
        )

        warning = self.interpreter._validate_action_against_facts(
            user_input="",
            actor_name="Marcus"
        )

        self.assertIsNone(warning)

    def test_extract_preserves_case_in_value(self):
        """Test that extraction preserves case in occupation/possession values"""
        self.interpreter._extract_user_declarations(
            user_input="I work as a Senior Software Engineer",
            actor_name="Alex",
            turn_number=14,
            scene_id="scene_014"
        )

        facts = self.fact_system.query_facts(
            subject="Alex",
            predicate="occupation"
        )

        self.assertEqual(len(facts), 1)
        # Check that case is preserved
        self.assertIn("Senior", facts[0].value)
        self.assertIn("Software", facts[0].value)
        self.assertIn("Engineer", facts[0].value)


if __name__ == "__main__":
    unittest.main()
