"""
Comprehensive tests for Mention System Phase 1: Core Infrastructure

Tests cover:
- Recording mentions (physical presence, departures, arrivals, elsewhere)
- Querying mentions (by actor, location, turn, type)
- Spawning validation logic
- Actor state tracking
- Last known location tracking
- Persistence (save/load)
- Confidence levels
- Indexing and performance
"""

import unittest
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime

from mention_system import (
    MentionSystem,
    MentionType,
    MentionSource,
    PresenceConfidence,
    ActorMention,
    ActorPresenceState
)


class TestMentionSystemCore(unittest.TestCase):
    """Test core mention recording and retrieval"""

    def setUp(self):
        """Create temporary directory for test sessions"""
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_session_001"
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

    def tearDown(self):
        """Clean up temporary directory"""
        shutil.rmtree(self.test_dir)

    def test_record_physical_presence(self):
        """Test recording a basic physical presence mention"""
        mention_id = self.mention_system.record_physical_presence(
            actor_name="Marcus",
            location="Studio",
            context="Marcus is working at his mixing board",
            source=MentionSource.SCENE_DESCRIPTION,
            turn_number=1,
            scene_id="scene_001"
        )

        self.assertIsNotNone(mention_id)

        # Query mentions
        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertEqual(len(mentions), 1)

        mention = mentions[0]
        self.assertEqual(mention.actor_name, "Marcus")
        self.assertEqual(mention.location, "Studio")
        self.assertEqual(mention.mention_type, MentionType.PHYSICAL_PRESENCE)
        self.assertEqual(mention.location_confidence, PresenceConfidence.CONFIRMED)

    def test_record_departure(self):
        """Test recording departure mention"""
        # First establish presence
        self.mention_system.record_physical_presence(
            actor_name="Linda",
            location="Bar",
            context="Linda is at the bar",
            turn_number=1,
            scene_id="scene_001"
        )

        # Then record departure
        self.mention_system.record_departure(
            actor_name="Linda",
            origin="Bar",
            destination="Home",
            context="Linda waves goodbye and heads for the exit",
            turn_number=5,
            scene_id="scene_001"
        )

        mentions = self.mention_system.query_mentions(actor_name="Linda")
        self.assertEqual(len(mentions), 2)

        departure = [m for m in mentions if m.mention_type == MentionType.DEPARTING][0]
        self.assertEqual(departure.location, "Bar")
        self.assertEqual(departure.turn_number, 5)
        self.assertEqual(departure.origin, "Bar")
        self.assertEqual(departure.destination, "Home")

    def test_record_arrival(self):
        """Test recording arrival mention"""
        mention_id = self.mention_system.record_arrival(
            actor_name="Carlos",
            destination="Restaurant",
            origin="Street",
            context="Carlos walks through the restaurant entrance",
            turn_number=10,
            scene_id="scene_002"
        )

        self.assertIsNotNone(mention_id)

        mentions = self.mention_system.query_mentions(actor_name="Carlos")
        arrival = mentions[0]

        self.assertEqual(arrival.mention_type, MentionType.ARRIVING)
        self.assertEqual(arrival.location, "Restaurant")
        self.assertEqual(arrival.destination, "Restaurant")
        self.assertEqual(arrival.origin, "Street")


class TestSpawningValidation(unittest.TestCase):
    """Test spawning validation logic"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_session_002"
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_can_spawn_never_mentioned(self):
        """Test that never-mentioned actors can be spawned"""
        can_spawn, reason = self.mention_system.can_spawn_at_location(
            actor_name="NewCharacter",
            location="Bar"
        )

        self.assertTrue(can_spawn)
        self.assertIsNone(reason)

    def test_departure_blocks_spawning(self):
        """Test that recent departure blocks spawning at same location"""
        # Record departure
        self.mention_system.record_departure(
            actor_name="Marcus",
            origin="Studio",
            destination="Home",
            context="Marcus locks up and leaves the studio",
            turn_number=10,
            scene_id="scene_001"
        )

        # Try to spawn at same location
        can_spawn, reason = self.mention_system.can_spawn_at_location(
            actor_name="Marcus",
            location="Studio"
        )

        self.assertFalse(can_spawn)
        self.assertIn("just left", reason)

    def test_elsewhere_current_blocks_spawning(self):
        """Test that ELSEWHERE_CURRENT blocks spawning at different location"""
        # Record actor elsewhere
        self.mention_system.record_mention(
            actor_name="Linda",
            mention_type=MentionType.ELSEWHERE_CURRENT,
            source=MentionSource.NPC_DIALOGUE,
            context="Marcus mentions Linda is at home sick",
            location="Home",
            turn_number=5,
            scene_id="scene_001"
        )

        # Try to spawn at different location
        can_spawn, reason = self.mention_system.can_spawn_at_location(
            actor_name="Linda",
            location="Bar"
        )

        self.assertFalse(can_spawn)
        self.assertIn("currently at Home", reason)

    def test_already_spawned_blocks_spawning(self):
        """Test that already-spawned actors can't be spawned again"""
        # Record presence and mark spawned
        self.mention_system.record_physical_presence(
            actor_name="Carlos",
            location="Restaurant",
            context="Carlos is dining at a table",
            turn_number=1,
            scene_id="scene_001"
        )
        self.mention_system.mark_actor_spawned("Carlos")

        # Try to spawn again
        can_spawn, reason = self.mention_system.can_spawn_at_location(
            actor_name="Carlos",
            location="Restaurant"
        )

        self.assertFalse(can_spawn)
        self.assertIn("already spawned", reason)

    def test_arrival_enables_spawning(self):
        """Test that arrival mention enables spawning at that location"""
        # Record arrival
        self.mention_system.record_arrival(
            actor_name="Elena",
            destination="Club",
            origin="Street",
            context="Elena enters the club",
            turn_number=8,
            scene_id="scene_001"
        )

        # Should be able to spawn at arrival location
        can_spawn, reason = self.mention_system.can_spawn_at_location(
            actor_name="Elena",
            location="Club"
        )

        self.assertTrue(can_spawn)


class TestQueryingMentions(unittest.TestCase):
    """Test querying and filtering mentions"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_session_003"
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # Create test data
        self.mention_system.record_physical_presence(
            "Marcus", "Studio", "Marcus at studio", turn_number=1, scene_id="scene_001"
        )
        self.mention_system.record_physical_presence(
            "Linda", "Bar", "Linda at bar", turn_number=2, scene_id="scene_001"
        )
        self.mention_system.record_physical_presence(
            "Marcus", "Bar", "Marcus at bar", turn_number=5, scene_id="scene_002"
        )
        self.mention_system.record_departure(
            "Linda", "Bar", "Home", "Linda leaves bar", turn_number=8, scene_id="scene_002"
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_query_mentions_by_actor(self):
        """Test querying mentions by actor name"""
        marcus_mentions = self.mention_system.query_mentions(actor_name="Marcus")

        self.assertEqual(len(marcus_mentions), 2)
        self.assertTrue(all(m.actor_name == "Marcus" for m in marcus_mentions))

    def test_query_mentions_by_location(self):
        """Test querying mentions by location"""
        bar_mentions = self.mention_system.query_mentions(location="Bar")

        self.assertEqual(len(bar_mentions), 3)  # Linda arrival, Marcus arrival, Linda departure
        self.assertTrue(all(m.location == "Bar" for m in bar_mentions))

    def test_query_mentions_by_type(self):
        """Test querying mentions by type"""
        presence_mentions = self.mention_system.query_mentions(
            mention_type=MentionType.PHYSICAL_PRESENCE
        )

        self.assertEqual(len(presence_mentions), 3)

        departure_mentions = self.mention_system.query_mentions(
            mention_type=MentionType.DEPARTING
        )

        self.assertEqual(len(departure_mentions), 1)
        self.assertEqual(departure_mentions[0].actor_name, "Linda")

    def test_query_mentions_by_turn_range(self):
        """Test querying mentions within turn range"""
        recent_mentions = self.mention_system.query_mentions(
            turn_range=(5, 10)
        )

        self.assertEqual(len(recent_mentions), 2)  # Marcus at bar (turn 5), Linda departure (turn 8)
        self.assertTrue(all(5 <= m.turn_number <= 10 for m in recent_mentions))

    def test_get_recent_mentions(self):
        """Test getting recent mentions for an actor"""
        recent = self.mention_system.get_recent_mentions("Marcus", count=1)

        self.assertEqual(len(recent), 1)
        self.assertEqual(recent[0].location, "Bar")  # Most recent mention


class TestActorState(unittest.TestCase):
    """Test actor state tracking"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_session_004"
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_state_tracking(self):
        """Test that actor state is updated with mentions"""
        # Record initial presence
        self.mention_system.record_physical_presence(
            "Marcus", "Studio", "Marcus at studio",
            turn_number=1, scene_id="scene_001"
        )

        state = self.mention_system.get_actor_state("Marcus")

        self.assertIsNotNone(state)
        self.assertEqual(state.actor_name, "Marcus")
        self.assertEqual(state.last_known_location, "Studio")
        self.assertEqual(state.location_confidence, PresenceConfidence.CONFIRMED)
        self.assertFalse(state.is_spawned)

    def test_state_updates_with_movement(self):
        """Test that state updates when actor moves with higher confidence"""
        # Initial arrival (HIGH confidence)
        self.mention_system.record_arrival(
            "Linda", "Bar", "Street", "Linda arrives at bar", turn_number=1, scene_id="scene_001"
        )

        state = self.mention_system.get_actor_state("Linda")
        self.assertEqual(state.last_known_location, "Bar")
        self.assertEqual(state.location_confidence, PresenceConfidence.HIGH)

        # Departure (HIGH confidence - won't override HIGH, but updates last_mention)
        self.mention_system.record_departure(
            "Linda", "Bar", "Restaurant", "Linda leaves", turn_number=5, scene_id="scene_001"
        )

        state = self.mention_system.get_actor_state("Linda")
        self.assertEqual(state.last_mention.turn_number, 5)

        # Physical presence at Restaurant (CONFIRMED confidence - overrides HIGH)
        self.mention_system.record_physical_presence(
            "Linda", "Restaurant", "Linda at restaurant", turn_number=10, scene_id="scene_002"
        )

        state = self.mention_system.get_actor_state("Linda")
        self.assertEqual(state.last_known_location, "Restaurant")
        self.assertEqual(state.location_confidence, PresenceConfidence.CONFIRMED)
        self.assertEqual(state.last_mention.turn_number, 10)

    def test_last_known_location(self):
        """Test getting last known location for actor"""
        self.mention_system.record_physical_presence(
            "Carlos", "Club", "Carlos at club", turn_number=10, scene_id="scene_003"
        )

        location, confidence = self.mention_system.get_last_known_location("Carlos")

        self.assertEqual(location, "Club")
        self.assertEqual(confidence, PresenceConfidence.CONFIRMED)

    def test_last_known_location_none_for_unknown(self):
        """Test that unknown actors return None for last location"""
        location, confidence = self.mention_system.get_last_known_location("UnknownPerson")

        self.assertIsNone(location)
        self.assertEqual(confidence, PresenceConfidence.UNKNOWN)

    def test_mark_actor_spawned(self):
        """Test marking actor as spawned"""
        self.mention_system.record_physical_presence(
            "Elena", "Park", "Elena at park", turn_number=1, scene_id="scene_001"
        )

        self.mention_system.mark_actor_spawned("Elena")

        state = self.mention_system.get_actor_state("Elena")
        self.assertTrue(state.is_spawned)

    def test_mark_actor_despawned(self):
        """Test marking actor as despawned"""
        self.mention_system.record_physical_presence(
            "Marcus", "Studio", "Marcus at studio", turn_number=1, scene_id="scene_001"
        )
        self.mention_system.mark_actor_spawned("Marcus")
        self.mention_system.mark_actor_despawned("Marcus")

        state = self.mention_system.get_actor_state("Marcus")
        self.assertFalse(state.is_spawned)


class TestConfidenceLevels(unittest.TestCase):
    """Test confidence level handling"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_session_005"
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_confidence_levels(self):
        """Test different confidence levels are recorded correctly"""
        # CONFIRMED (via physical presence)
        self.mention_system.record_physical_presence(
            "Marcus", "Studio", "Marcus at studio",
            turn_number=1, scene_id="scene_001"
        )

        # HIGH (via elsewhere dialogue)
        self.mention_system.record_mention(
            "Linda", MentionType.ELSEWHERE_CURRENT,
            MentionSource.NPC_DIALOGUE,
            "Marcus thinks Linda is at home",
            location="Home",
            location_confidence=PresenceConfidence.HIGH,
            turn_number=2, scene_id="scene_001"
        )

        # MEDIUM (via inference)
        self.mention_system.record_mention(
            "Carlos", MentionType.ELSEWHERE_CURRENT,
            MentionSource.SYSTEM_INFERENCE,
            "Inferred from work schedule",
            location="Office",
            location_confidence=PresenceConfidence.MEDIUM,
            turn_number=3, scene_id="scene_001"
        )

        marcus_state = self.mention_system.get_actor_state("Marcus")
        linda_state = self.mention_system.get_actor_state("Linda")
        carlos_state = self.mention_system.get_actor_state("Carlos")

        self.assertEqual(marcus_state.location_confidence, PresenceConfidence.CONFIRMED)
        self.assertEqual(linda_state.location_confidence, PresenceConfidence.HIGH)
        self.assertEqual(carlos_state.location_confidence, PresenceConfidence.MEDIUM)

    def test_higher_confidence_overrides_lower(self):
        """Test that higher confidence mentions update state"""
        # Start with MEDIUM
        self.mention_system.record_mention(
            "Marcus", MentionType.ELSEWHERE_CURRENT,
            MentionSource.SYSTEM_INFERENCE,
            "Inferred location",
            location="Studio",
            location_confidence=PresenceConfidence.MEDIUM,
            turn_number=1, scene_id="scene_001"
        )

        state = self.mention_system.get_actor_state("Marcus")
        self.assertEqual(state.location_confidence, PresenceConfidence.MEDIUM)

        # Update with CONFIRMED
        self.mention_system.record_physical_presence(
            "Marcus", "Studio", "Marcus at studio",
            turn_number=5, scene_id="scene_001"
        )

        state = self.mention_system.get_actor_state("Marcus")
        self.assertEqual(state.location_confidence, PresenceConfidence.CONFIRMED)


class TestPersistence(unittest.TestCase):
    """Test persistence (save/load) functionality"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_session_006"

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_persistence(self):
        """Test that mentions are saved and can be loaded"""
        # Create system and add mentions
        system1 = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        system1.record_physical_presence(
            "Marcus", "Studio", "Marcus at studio", turn_number=1, scene_id="scene_001"
        )
        system1.record_physical_presence(
            "Linda", "Bar", "Linda at bar", turn_number=2, scene_id="scene_001"
        )

        # Create new system instance (should load from file)
        system2 = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # Verify mentions loaded
        marcus_mentions = system2.query_mentions(actor_name="Marcus")
        linda_mentions = system2.query_mentions(actor_name="Linda")

        self.assertEqual(len(marcus_mentions), 1)
        self.assertEqual(len(linda_mentions), 1)

        # Verify state reconstructed from mentions
        marcus_state = system2.get_actor_state("Marcus")
        self.assertIsNotNone(marcus_state)
        self.assertEqual(marcus_state.last_known_location, "Studio")

    def test_persistence_file_format(self):
        """Test that persistence file has correct JSON format"""
        system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        system.record_physical_presence(
            "Marcus", "Studio", "Marcus at studio", turn_number=1, scene_id="scene_001"
        )

        # Check file exists and has valid JSON
        mentions_file = Path(self.test_dir) / "mentions" / f"mentions_{self.session_id}.json"
        self.assertTrue(mentions_file.exists())

        with open(mentions_file, 'r') as f:
            data = json.load(f)

        self.assertIn("mentions", data)
        self.assertEqual(data["session_id"], self.session_id)
        self.assertEqual(len(data["mentions"]), 1)
        self.assertEqual(data["mentions"][0]["actor_name"], "Marcus")


class TestSpawnCandidates(unittest.TestCase):
    """Test spawn candidate retrieval"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_session_007"
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

        # Set up test scenario
        self.mention_system.record_physical_presence(
            "Marcus", "Studio", "Marcus at studio", turn_number=1, scene_id="scene_001"
        )
        self.mention_system.record_physical_presence(
            "Linda", "Bar", "Linda at bar", turn_number=1, scene_id="scene_001"
        )
        self.mention_system.record_mention(
            "Carlos", MentionType.ELSEWHERE_CURRENT,
            MentionSource.NPC_DIALOGUE,
            "Carlos is at home",
            location="Home",
            turn_number=1, scene_id="scene_001"
        )

        # Mark Marcus as spawned
        self.mention_system.mark_actor_spawned("Marcus")

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_get_spawn_candidates(self):
        """Test getting spawn candidates for a location"""
        candidates = self.mention_system.get_spawn_candidates("Bar", max_candidates=10)

        # Linda should be a candidate (mentioned at Bar, not spawned)
        self.assertIn("Linda", candidates)

        # Marcus should NOT be a candidate (already spawned)
        self.assertNotIn("Marcus", candidates)

        # Carlos should NOT be a candidate (currently elsewhere)
        self.assertNotIn("Carlos", candidates)

    def test_spawn_candidates_limited_by_max(self):
        """Test that spawn candidates respect max_candidates parameter"""
        # Add many actors at same location
        for i in range(10):
            self.mention_system.record_physical_presence(
                f"Actor{i}", "Club", f"Actor{i} at club", turn_number=1, scene_id="scene_001"
            )

        candidates = self.mention_system.get_spawn_candidates("Club", max_candidates=3)

        self.assertEqual(len(candidates), 3)


class TestMentionDetails(unittest.TestCase):
    """Test mention details and metadata"""

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.session_id = "test_session_008"
        self.mention_system = MentionSystem(
            session_id=self.session_id,
            storage_directory=Path(self.test_dir)
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_mention_context(self):
        """Test that context is stored in mentions"""
        context = "Marcus adjusts the mixing board levels carefully"

        self.mention_system.record_physical_presence(
            "Marcus", "Studio", context,
            turn_number=1, scene_id="scene_001"
        )

        mentions = self.mention_system.query_mentions(actor_name="Marcus")
        self.assertEqual(mentions[0].context, context)

    def test_arrival_from_location(self):
        """Test that arrival stores origin in details"""
        self.mention_system.record_arrival(
            "Linda", "Bar", "Street", "Linda enters the bar",
            turn_number=5, scene_id="scene_001"
        )

        mentions = self.mention_system.query_mentions(actor_name="Linda")
        arrival = mentions[0]

        self.assertEqual(arrival.origin, "Street")
        self.assertEqual(arrival.destination, "Bar")

    def test_mention_source_tracking(self):
        """Test that mention sources are tracked correctly"""
        self.mention_system.record_physical_presence(
            "Marcus", "Studio", "Marcus at studio",
            source=MentionSource.SCENE_DESCRIPTION,
            turn_number=1, scene_id="scene_001"
        )

        self.mention_system.record_mention(
            "Linda", MentionType.ELSEWHERE_CURRENT,
            MentionSource.NPC_DIALOGUE,
            "Linda is at home",
            location="Home",
            turn_number=2, scene_id="scene_001"
        )

        marcus_mentions = self.mention_system.query_mentions(actor_name="Marcus")
        linda_mentions = self.mention_system.query_mentions(actor_name="Linda")

        self.assertEqual(marcus_mentions[0].source, MentionSource.SCENE_DESCRIPTION)
        self.assertEqual(linda_mentions[0].source, MentionSource.NPC_DIALOGUE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
