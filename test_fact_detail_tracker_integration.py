"""
Integration test for Fact System + ConcreteDetailTracker

Tests that concrete details are automatically converted to canonical facts.
"""

import unittest
from unittest.mock import Mock
from pathlib import Path
import shutil

from fact_system import FactSystem, FactType, FactAuthority
from concrete_detail_tracker import ConcreteDetailTracker, DetailCategory


class TestFactDetailTrackerIntegration(unittest.TestCase):
    """Test suite for Fact System + ConcreteDetailTracker integration"""

    def setUp(self):
        """Set up test environment"""
        # Use unique session ID per test for isolation
        import uuid
        self.test_session = f"test_fact_detail_tracker_{uuid.uuid4().hex[:8]}"
        self.test_dir = Path(f"sessions/{self.test_session}")

        # Clean up any previous test data
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

        # Create fact system
        self.fact_system = FactSystem(self.test_session)

        # Create detail tracker with fact system
        self.tracker = ConcreteDetailTracker(
            session_id=self.test_session,
            storage_directory=Path("sessions"),
            fact_system=self.fact_system
        )

    def tearDown(self):
        """Clean up test environment"""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_vehicle_detail_creates_possession_fact(self):
        """Test that adding a vehicle detail creates an ACTOR_POSSESSION fact"""
        # Add vehicle detail
        detail_id = self.tracker.add_detail(
            category=DetailCategory.VEHICLE,
            owner="Marcus",
            detail_text="1987 Lamborghini Countach, red with black interior",
            keywords=["lamborghini", "countach", "car", "vehicle"],
            scene_id="scene_001"
        )

        # Verify detail was created
        self.assertIsNotNone(detail_id)

        # Verify fact was created
        facts = self.fact_system.query_facts(
            subject="Marcus",
            fact_type=FactType.ACTOR_POSSESSION,
            predicate="has_vehicle"
        )

        self.assertEqual(len(facts), 1, "Should create one possession fact for vehicle")
        self.assertEqual(facts[0].subject, "Marcus")
        self.assertEqual(facts[0].predicate, "has_vehicle")
        self.assertIn("Lamborghini", facts[0].value)
        self.assertEqual(facts[0].authority, FactAuthority.SCENE_DECLARED)

    def test_physical_trait_detail_creates_trait_fact(self):
        """Test that physical trait details create ACTOR_TRAIT facts"""
        detail_id = self.tracker.add_detail(
            category=DetailCategory.PHYSICAL_TRAIT,
            owner="Sarah",
            detail_text="Scar across left eyebrow from childhood accident",
            keywords=["scar", "eyebrow", "physical"],
            scene_id="scene_002"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(
            subject="Sarah",
            fact_type=FactType.ACTOR_TRAIT,
            predicate="physical_trait"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("scar", facts[0].value.lower())

    def test_clothing_detail_creates_possession_fact(self):
        """Test that clothing details create possession facts"""
        detail_id = self.tracker.add_detail(
            category=DetailCategory.CLOTHING,
            owner="Marcus",
            detail_text="Black leather jacket with silver zipper",
            keywords=["jacket", "leather", "black", "clothing"],
            scene_id="scene_003"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(
            subject="Marcus",
            fact_type=FactType.ACTOR_POSSESSION,
            predicate="wears"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("leather jacket", facts[0].value)

    def test_location_detail_creates_location_property_fact(self):
        """Test that location details create LOCATION_PROPERTY facts"""
        detail_id = self.tracker.add_detail(
            category=DetailCategory.LOCATION,
            owner="Downtown Bar",
            detail_text="Corner of 5th and Main Street",
            keywords=["location", "downtown", "corner"],
            scene_id="scene_004"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(
            subject="Downtown Bar",
            fact_type=FactType.LOCATION_PROPERTY,
            predicate="known_location"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("5th and Main", facts[0].value)

    def test_weapon_detail_creates_possession_fact(self):
        """Test that weapon details create possession facts"""
        detail_id = self.tracker.add_detail(
            category=DetailCategory.WEAPON,
            owner="Detective Miller",
            detail_text="Glock 19 service pistol",
            keywords=["glock", "pistol", "weapon", "gun"],
            scene_id="scene_005"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(
            subject="Detective Miller",
            fact_type=FactType.ACTOR_POSSESSION,
            predicate="has_weapon"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("Glock", facts[0].value)

    def test_brand_detail_creates_possession_fact(self):
        """Test that brand details create possession facts"""
        detail_id = self.tracker.add_detail(
            category=DetailCategory.BRAND,
            owner="Marcus",
            detail_text="Rolex Submariner watch",
            keywords=["rolex", "watch", "brand"],
            scene_id="scene_006"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(
            subject="Marcus",
            fact_type=FactType.ACTOR_POSSESSION,
            predicate="owns_brand"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("Rolex", facts[0].value)

    def test_building_detail_creates_location_identity_fact(self):
        """Test that building details create LOCATION_IDENTITY facts"""
        detail_id = self.tracker.add_detail(
            category=DetailCategory.BUILDING,
            owner="City",
            detail_text="The Grand Hotel, a 20-story Art Deco building",
            keywords=["hotel", "building", "grand"],
            scene_id="scene_007"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(
            subject="City",
            fact_type=FactType.LOCATION_IDENTITY,
            predicate="building"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("Grand Hotel", facts[0].value)

    def test_relationship_detail_creates_relationship_fact(self):
        """Test that relationship details create RELATIONSHIP facts"""
        detail_id = self.tracker.add_detail(
            category=DetailCategory.RELATIONSHIP,
            owner="Linda",
            detail_text="Marcus's younger sister, protective and loyal",
            keywords=["sister", "relationship", "marcus"],
            scene_id="scene_008"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(
            subject="Linda",
            fact_type=FactType.RELATIONSHIP,
            predicate="relationship_detail"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("sister", facts[0].value.lower())

    def test_backstory_detail_creates_trait_fact(self):
        """Test that backstory details create ACTOR_TRAIT facts"""
        detail_id = self.tracker.add_detail(
            category=DetailCategory.BACKSTORY,
            owner="Marcus",
            detail_text="Grew up in Chicago, moved to LA after college",
            keywords=["backstory", "chicago", "history"],
            scene_id="scene_009"
        )

        # Verify fact was created
        facts = self.fact_system.query_facts(
            subject="Marcus",
            fact_type=FactType.ACTOR_TRAIT,
            predicate="backstory"
        )

        self.assertEqual(len(facts), 1)
        self.assertIn("Chicago", facts[0].value)

    def test_no_fact_system_graceful_degradation(self):
        """Test that tracker works without fact system"""
        tracker_no_facts = ConcreteDetailTracker(
            session_id="test_no_facts",
            storage_directory=Path("sessions"),
            fact_system=None
        )

        # Should not raise error
        detail_id = tracker_no_facts.add_detail(
            category=DetailCategory.VEHICLE,
            owner="TestActor",
            detail_text="Test vehicle",
            keywords=["test"],
            scene_id="scene_test"
        )

        self.assertIsNotNone(detail_id)

    def test_fact_tags_include_keywords(self):
        """Test that fact tags include detail keywords"""
        detail_id = self.tracker.add_detail(
            category=DetailCategory.VEHICLE,
            owner="Marcus",
            detail_text="Red Ferrari 458 Spider",
            keywords=["ferrari", "car", "sports", "red"],
            scene_id="scene_010"
        )

        # Query fact and check tags
        facts = self.fact_system.query_facts(subject="Marcus", predicate="has_vehicle")
        self.assertEqual(len(facts), 1)

        # Tags should include keywords
        fact_tags = facts[0].tags
        self.assertIn("ferrari", fact_tags)
        self.assertIn("car", fact_tags)
        self.assertIn("sports", fact_tags)
        self.assertIn("red", fact_tags)
        self.assertIn("vehicle", fact_tags)  # Category also included

    def test_fact_source_references_detail_id(self):
        """Test that fact source references the originating detail ID"""
        detail_id = self.tracker.add_detail(
            category=DetailCategory.WEAPON,
            owner="Agent Smith",
            detail_text="Walther PPK",
            keywords=["walther", "ppk", "pistol"],
            scene_id="scene_011"
        )

        # Query fact and check source
        facts = self.fact_system.query_facts(subject="Agent Smith", predicate="has_weapon")
        self.assertEqual(len(facts), 1)

        # Source should reference detail ID
        self.assertIn("concrete_detail", facts[0].source)
        self.assertIn(detail_id, facts[0].source)

    def test_multiple_details_create_multiple_facts(self):
        """Test that multiple details for same actor create multiple facts"""
        # Add vehicle
        self.tracker.add_detail(
            category=DetailCategory.VEHICLE,
            owner="Marcus",
            detail_text="Red Lamborghini Countach",
            keywords=["lamborghini", "car"],
            scene_id="scene_012"
        )

        # Add clothing
        self.tracker.add_detail(
            category=DetailCategory.CLOTHING,
            owner="Marcus",
            detail_text="Black leather jacket",
            keywords=["jacket", "leather"],
            scene_id="scene_012"
        )

        # Add weapon
        self.tracker.add_detail(
            category=DetailCategory.WEAPON,
            owner="Marcus",
            detail_text="Beretta 92FS",
            keywords=["beretta", "pistol"],
            scene_id="scene_012"
        )

        # Should create 3 different facts
        all_facts = self.fact_system.query_facts(subject="Marcus")
        self.assertEqual(len(all_facts), 3)

        # Each with different predicate
        predicates = {fact.predicate for fact in all_facts}
        self.assertEqual(len(predicates), 3)
        self.assertIn("has_vehicle", predicates)
        self.assertIn("wears", predicates)
        self.assertIn("has_weapon", predicates)

    def test_duplicate_detail_doesnt_create_duplicate_fact(self):
        """Test that re-adding same detail doesn't create duplicate fact"""
        keywords = ["lamborghini", "car", "countach"]

        # Add detail first time
        detail_id_1 = self.tracker.add_detail(
            category=DetailCategory.VEHICLE,
            owner="Marcus",
            detail_text="1987 Lamborghini Countach",
            keywords=keywords,
            scene_id="scene_013"
        )

        # Add similar detail (should be deduplicated)
        detail_id_2 = self.tracker.add_detail(
            category=DetailCategory.VEHICLE,
            owner="Marcus",
            detail_text="1987 Lamborghini Countach (same car)",
            keywords=keywords,
            scene_id="scene_014"
        )

        # Should return same detail ID (deduplication)
        self.assertEqual(detail_id_1, detail_id_2)

        # Should only create one fact
        facts = self.fact_system.query_facts(subject="Marcus", predicate="has_vehicle")
        self.assertEqual(len(facts), 1, "Should not create duplicate facts")


if __name__ == "__main__":
    unittest.main()
