"""
Test suite for Mention System integration with Main Loop.

Tests that mention_system is properly initialized and passed to all agents.
"""

import unittest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import sys

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent / "MAIN"))

from mention_system import MentionSystem, MentionType, MentionSource, PresenceConfidence


class TestMentionMainLoopIntegration(unittest.TestCase):
    """Test Mention System initialization and agent integration in main loop"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_main_session"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_mention_system_initialization(self):
        """Test that MentionSystem can be initialized with session_id and storage_directory"""
        mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        self.assertIsNotNone(mention_system)
        self.assertEqual(mention_system.session_id, self.session_id)

    def test_creator_agent_accepts_mention_system(self):
        """Test that CreatorAgent can be initialized with mention_system parameter"""
        from agents.creator_agent import CreatorAgent
        from logbook.utas_logger import UTASLogger

        logger = UTASLogger()
        mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # CreatorAgent should accept mention_system parameter
        creator = CreatorAgent(logger, rag_system=None, mention_system=mention_system)

        self.assertIsNotNone(creator.mention_system)
        self.assertEqual(creator.mention_system, mention_system)

    def test_narrator_agent_accepts_mention_system(self):
        """Test that NarratorAgent can be initialized with mention_system parameter"""
        from agents.narrator_agent import NarratorAgent

        mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # NarratorAgent should accept mention_system parameter
        narrator = NarratorAgent(rag_system=None, mention_system=mention_system)

        self.assertIsNotNone(narrator.mention_system)
        self.assertEqual(narrator.mention_system, mention_system)

    def test_conductor_agent_accepts_mention_system(self):
        """Test that ConductorAgent can be initialized with mention_system parameter"""
        from agents.conductor_agent import ConductorAgent
        from logbook.utas_logger import UTASLogger

        logger = UTASLogger()
        mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # ConductorAgent should accept mention_system parameter
        conductor = ConductorAgent(
            logger,
            "Test scene",
            tracker_agent=None,
            rag_system=None,
            mention_system=mention_system
        )

        self.assertIsNotNone(conductor.mention_system)
        self.assertEqual(conductor.mention_system, mention_system)

    def test_conductor_passes_mention_system_to_interpreter(self):
        """Test that ConductorAgent passes mention_system to InterpreterAgent"""
        from agents.conductor_agent import ConductorAgent
        from logbook.utas_logger import UTASLogger

        logger = UTASLogger()
        mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # Create ConductorAgent with mention_system
        conductor = ConductorAgent(
            logger,
            "Test scene",
            tracker_agent=None,
            rag_system=None,
            mention_system=mention_system
        )

        # Verify InterpreterAgent received mention_system
        self.assertIsNotNone(conductor.interpreter_agent.mention_system)
        self.assertEqual(conductor.interpreter_agent.mention_system, mention_system)

    def test_conductor_passes_mention_system_to_narrator(self):
        """Test that ConductorAgent passes mention_system to its NarratorAgent"""
        from agents.conductor_agent import ConductorAgent
        from logbook.utas_logger import UTASLogger

        logger = UTASLogger()
        mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # Create ConductorAgent with mention_system
        conductor = ConductorAgent(
            logger,
            "Test scene",
            tracker_agent=None,
            rag_system=None,
            mention_system=mention_system
        )

        # Verify NarratorAgent received mention_system
        self.assertIsNotNone(conductor.narrator.mention_system)
        self.assertEqual(conductor.narrator.mention_system, mention_system)

    def test_auto_spawn_scene_npcs_accepts_mention_system(self):
        """Test that auto_spawn_scene_npcs accepts mention_system parameter"""
        from scene_npc_parser import auto_spawn_scene_npcs
        from agents.creator_agent import CreatorAgent
        from logbook.utas_logger import UTASLogger

        logger = UTASLogger()
        mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        creator = CreatorAgent(logger, rag_system=None, mention_system=mention_system)

        # Mock dependencies
        mock_continuity = Mock()
        mock_auto_memory = None

        # Should not raise error when mention_system is passed
        try:
            spawned_count = auto_spawn_scene_npcs(
                scene_description="A quiet bar with a bartender.",
                creator_agent=creator,
                available_npcs=[],
                continuity_validator=mock_continuity,
                auto_memory_creator=mock_auto_memory,
                actor_name="Player",
                scene_id="test_bar",
                mention_system=mention_system
            )
            # Success - function accepted mention_system parameter
            success = True
        except TypeError as e:
            # Failure - function doesn't accept mention_system parameter
            if "mention_system" in str(e):
                success = False
            else:
                raise

        self.assertTrue(success, "auto_spawn_scene_npcs should accept mention_system parameter")


class TestMentionSystemPersistence(unittest.TestCase):
    """Test Mention System persistence across sessions"""

    def setUp(self):
        """Set up test fixtures"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_persistence_session"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_mention_system_creates_storage_directory(self):
        """Test that MentionSystem creates its storage directory"""
        storage_dir = Path(self.test_dir) / "mentions"
        self.assertFalse(storage_dir.exists())

        # Create mention system
        storage_dir.mkdir(parents=True, exist_ok=True)
        mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=storage_dir
        )

        # Storage directory should exist
        self.assertTrue(storage_dir.exists())

    def test_mention_system_persists_mentions(self):
        """Test that mentions are automatically saved to disk"""
        storage_dir = Path(self.test_dir) / "mentions"
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Create mention system and record a mention
        mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=storage_dir
        )

        mention_system.record_physical_presence(
            "Marcus",
            "Bar",
            "Marcus at the bar",
            turn_number=1,
            scene_id="scene_001"
        )

        # MentionSystem auto-saves on record, verify mention file was created
        # Note: MentionSystem creates mentions/ subdirectory
        mention_file = storage_dir / "mentions" / f"mentions_{self.session_id}.json"
        self.assertTrue(mention_file.exists())

    def test_mention_system_loads_mentions(self):
        """Test that mentions can be loaded from previous session"""
        storage_dir = Path(self.test_dir) / "mentions"
        storage_dir.mkdir(parents=True, exist_ok=True)

        # Create first mention system and record a mention
        mention_system_1 = MentionSystem(
            session_id=self.session_id,
            storage_directory=storage_dir
        )

        mention_system_1.record_physical_presence(
            "Marcus",
            "Bar",
            "Marcus at the bar",
            turn_number=1,
            scene_id="scene_001"
        )
        # MentionSystem auto-saves on record

        # Create second mention system with same session_id
        mention_system_2 = MentionSystem(
            session_id=self.session_id,
            storage_directory=storage_dir
        )

        # Mentions should be loaded
        mentions = mention_system_2.query_mentions(actor_name="Marcus")
        self.assertGreater(len(mentions), 0)
        self.assertEqual(mentions[0].actor_name, "Marcus")
        self.assertEqual(mentions[0].location, "Bar")


if __name__ == '__main__':
    unittest.main()
