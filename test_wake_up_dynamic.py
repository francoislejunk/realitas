"""
Test suite for Dynamic Wake-Up Narration System.

Tests that wake-up openings vary based on personality, S-factors, and occupation.
"""

import unittest
import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "agents"))

from agents.creator_agent import CreatorAgent
from logbook.utas_logger import UTASLogger
from actor_sheet import ActorSheet, SFactorType, SFactors


class TestDynamicWakeUpNarration(unittest.TestCase):
    """Test Dynamic Wake-Up Narration helper methods"""

    def setUp(self):
        """Set up test fixtures"""
        self.logger = UTASLogger()
        self.creator = CreatorAgent(self.logger, rag_system=None)

    def test_classify_wake_up_style_alert(self):
        """Test classification of determined/confident personality as 'alert'"""
        result = self.creator._classify_wake_up_style("Determined and focused")
        self.assertEqual(result, "alert")

        result = self.creator._classify_wake_up_style("Confident and bold")
        self.assertEqual(result, "alert")

    def test_classify_wake_up_style_gradual(self):
        """Test classification of anxious personality as 'gradual'"""
        result = self.creator._classify_wake_up_style("Anxious and worried")
        self.assertEqual(result, "gradual")

        result = self.creator._classify_wake_up_style("Nervous and uncertain")
        self.assertEqual(result, "gradual")

    def test_classify_wake_up_style_aggressive(self):
        """Test classification of aggressive personality as 'aggressive'"""
        result = self.creator._classify_wake_up_style("Aggressive and hostile")
        self.assertEqual(result, "aggressive")

        result = self.creator._classify_wake_up_style("Angry and violent")
        self.assertEqual(result, "aggressive")

    def test_classify_wake_up_style_cautious(self):
        """Test classification of paranoid personality as 'cautious'"""
        result = self.creator._classify_wake_up_style("Paranoid and suspicious")
        self.assertEqual(result, "cautious")

        result = self.creator._classify_wake_up_style("Cautious and vigilant")
        self.assertEqual(result, "cautious")

    def test_classify_wake_up_style_peaceful(self):
        """Test classification of calm personality as 'peaceful'"""
        result = self.creator._classify_wake_up_style("Calm and peaceful")
        self.assertEqual(result, "peaceful")

        # Default case
        result = self.creator._classify_wake_up_style("Neutral and balanced")
        self.assertEqual(result, "peaceful")

    def test_get_eye_opening_verb_returns_appropriate_verbs(self):
        """Test that eye-opening verbs match wake-up style"""
        alert_verbs = ["snap open", "flash open", "shoot open"]
        result = self.creator._get_eye_opening_verb("alert")
        self.assertIn(result, alert_verbs)

        gradual_verbs = ["flutter open", "slowly open", "hesitantly open"]
        result = self.creator._get_eye_opening_verb("gradual")
        self.assertIn(result, gradual_verbs)

        aggressive_verbs = ["burst open", "jolt open", "slam open"]
        result = self.creator._get_eye_opening_verb("aggressive")
        self.assertIn(result, aggressive_verbs)

    def test_get_immediate_reaction_high_perception(self):
        """Test immediate reaction with high perception"""
        result = self.creator._get_immediate_reaction("alert", perception=5, shadow=2)
        # Should mention clarity or awareness
        self.assertTrue(any(word in result.lower() for word in ["clarity", "detail", "aware", "focus"]))

    def test_get_immediate_reaction_high_shadow(self):
        """Test immediate reaction with high shadow (vigilance)"""
        result = self.creator._get_immediate_reaction("alert", perception=3, shadow=5)
        # Should mention threats or danger
        self.assertTrue(any(word in result.lower() for word in ["threat", "danger", "alert", "checking"]))

    def test_get_immediate_reaction_low_perception(self):
        """Test immediate reaction with low perception"""
        result = self.creator._get_immediate_reaction("peaceful", perception=1, shadow=2)
        # Should mention blurry or adjusting vision
        self.assertTrue(any(word in result.lower() for word in ["adjust", "blurry", "focus", "slowly"]))

    def test_get_perceptual_action_observant(self):
        """Test perceptual action for observant personality"""
        result = self.creator._get_perceptual_action("Observant and perceptive", perception=4)
        # Should use strong perception verbs
        self.assertTrue(any(word in result for word in ["notice", "observe", "pick up"]))

    def test_get_perceptual_action_cautious(self):
        """Test perceptual action for cautious personality"""
        result = self.creator._get_perceptual_action("Cautious and careful", perception=3)
        # Should use careful verbs
        self.assertTrue(any(word in result.lower() for word in ["scan", "check", "assess"]))

    def test_get_perceptual_action_impulsive(self):
        """Test perceptual action for impulsive personality"""
        result = self.creator._get_perceptual_action("Impulsive and reckless", perception=3)
        # Should use quick/hasty verbs
        self.assertTrue(any(word in result.lower() for word in ["already", "quickly", "glance"]))


class TestDynamicWakeUpIntegration(unittest.TestCase):
    """Test integration of dynamic wake-up with scene generation"""

    def setUp(self):
        """Set up test fixtures"""
        self.logger = UTASLogger()
        self.creator = CreatorAgent(self.logger, rag_system=None)

    def _create_mock_actor(self, personality_internal, personality_external,
                          perception=3, strength=3, shadow=3, occupation="Test Occupation"):
        """Helper to create mock UserActor"""
        mock_actor = Mock()
        mock_actor.name = "TestActor"

        # Mock actor sheet
        mock_sheet = Mock()
        mock_sheet.occupation = occupation
        mock_sheet.personality_traits = {
            'internal': personality_internal,
            'external': personality_external
        }

        # Mock S-factors (use correct SFactorType attribute names)
        mock_s_factors = Mock()
        mock_s_factors.get_factor = Mock(side_effect=lambda sf_type: {
            SFactorType.SMARTS: perception,  # Using Smarts as proxy for perceptual awareness
            SFactorType.STURDINESS: strength,  # Sturdiness = physical strength
            SFactorType.SHADOW: shadow,
            SFactorType.SOCIABILITY: 3,
            SFactorType.SWIFTNESS: 3
        }.get(sf_type, 3))
        mock_sheet.s_factors = mock_s_factors

        mock_actor.sheet = mock_sheet
        return mock_actor

    def test_generate_dynamic_wake_up_opening_confident_military(self):
        """Test dynamic opening for confident military character"""
        mock_actor = self._create_mock_actor(
            "Determined and confident",
            "Observant and cautious",
            perception=4,
            shadow=3,
            occupation="Former soldier"
        )

        result = self.creator._generate_dynamic_wake_up_opening(
            mock_actor,
            world_context="Cyberpunk dystopia",
            personality_internal="Determined and confident",
            personality_external="Observant and cautious",
            s_factors_note="Perception: Exceptional (4)"
        )

        # Should contain alert wake-up style
        self.assertTrue(any(verb in result for verb in ["snap open", "flash open", "shoot open"]))
        # Should mention multiple sensory details (high perception)
        self.assertIn("3 specific sensory details", result)
        # Should mention tactical/military context
        self.assertIn("tactical", result.lower())

    def test_generate_dynamic_wake_up_opening_anxious_artist(self):
        """Test dynamic opening for anxious artist character"""
        mock_actor = self._create_mock_actor(
            "Anxious and worried",
            "Withdrawn and introspective",
            perception=2,
            occupation="Struggling painter"
        )

        result = self.creator._generate_dynamic_wake_up_opening(
            mock_actor,
            world_context="Modern urban setting",
            personality_internal="Anxious and worried",
            personality_external="Withdrawn and introspective",
            s_factors_note="Perception: Minimal (2)"
        )

        # Should contain gradual wake-up style
        self.assertTrue(any(verb in result for verb in ["flutter open", "slowly open", "hesitantly open"]))
        # Should mention limited sensory details (low perception)
        self.assertIn("1 obvious sensory", result)
        # Should mention sensory/aesthetic context for artist
        self.assertIn("sensory", result.lower())

    def test_generate_dynamic_wake_up_opening_paranoid_criminal(self):
        """Test dynamic opening for paranoid criminal character"""
        mock_actor = self._create_mock_actor(
            "Paranoid and suspicious",
            "Cautious and defensive",
            perception=5,
            shadow=5,
            occupation="Black market dealer"
        )

        result = self.creator._generate_dynamic_wake_up_opening(
            mock_actor,
            world_context="Noir detective world",
            personality_internal="Paranoid and suspicious",
            personality_external="Cautious and defensive",
            s_factors_note="Perception: Exceptional (5), Shadow: Exceptional (5)"
        )

        # Should contain cautious wake-up style
        self.assertTrue(any(verb in result for verb in ["crack open", "carefully open", "slit open"]))
        # Should mention maximum sensory details (very high perception)
        self.assertIn("3 specific sensory details", result)
        # Should mention security/vigilance/check/threats context (criminal context)
        self.assertTrue(any(word in result.lower() for word in ["security", "exits", "check", "disturbance", "threats", "scan"]),
                       f"Expected security-related context in: {result}")

    def test_generate_dynamic_wake_up_opening_peaceful_scholar(self):
        """Test dynamic opening for peaceful scholar character"""
        mock_actor = self._create_mock_actor(
            "Calm and thoughtful",
            "Friendly and helpful",
            perception=3,
            occupation="Librarian"
        )

        result = self.creator._generate_dynamic_wake_up_opening(
            mock_actor,
            world_context="Fantasy medieval setting",
            personality_internal="Calm and thoughtful",
            personality_external="Friendly and helpful",
            s_factors_note="Average across all attributes"
        )

        # Should contain peaceful wake-up style
        self.assertTrue(any(verb in result for verb in ["gently open", "drift open", "softly open"]))
        # Should mention moderate sensory details (medium perception)
        self.assertIn("2 clear sensory", result)
        # Should mention analytical context for scholar
        self.assertIn("analytical", result.lower())

    def test_dynamic_opening_no_explanation_of_why(self):
        """Test that dynamic opening never explains WHY character acts"""
        mock_actor = self._create_mock_actor(
            "Determined and confident",
            "Observant and cautious",
            occupation="Any occupation"
        )

        result = self.creator._generate_dynamic_wake_up_opening(
            mock_actor,
            world_context="Any world",
            personality_internal="Determined and confident",
            personality_external="Observant and cautious",
            s_factors_note="Average"
        )

        # Should NOT contain explanatory phrases (Bug #14 protection)
        forbidden_phrases = [
            "because", "due to", "reflecting", "showing",
            "born from", "habit", "personality", "trait"
        ]
        for phrase in forbidden_phrases:
            self.assertNotIn(phrase, result.lower())

        # Should contain instruction to show action only
        self.assertIn("NEVER explain why", result)


class TestWakeUpVariety(unittest.TestCase):
    """Test that wake-up openings produce variety"""

    def setUp(self):
        """Set up test fixtures"""
        self.logger = UTASLogger()
        self.creator = CreatorAgent(self.logger, rag_system=None)

    def test_different_personalities_produce_different_styles(self):
        """Test that different personalities produce different wake-up styles"""
        personalities = [
            "Determined and confident",
            "Anxious and worried",
            "Aggressive and hostile",
            "Paranoid and suspicious",
            "Calm and peaceful"
        ]

        styles = set()
        for personality in personalities:
            style = self.creator._classify_wake_up_style(personality)
            styles.add(style)

        # Should have at least 4 different styles
        self.assertGreaterEqual(len(styles), 4)

    def test_eye_opening_verbs_vary_within_style(self):
        """Test that multiple calls produce different verbs (randomization)"""
        verbs = set()
        for _ in range(10):
            verb = self.creator._get_eye_opening_verb("alert")
            verbs.add(verb)

        # Should have at least 2 different verbs (randomization working)
        self.assertGreaterEqual(len(verbs), 2)


if __name__ == '__main__':
    unittest.main()
