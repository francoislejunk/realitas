"""
Scene Population System - Pre-generates all potential NUAs before scene narration

Philosophy:
- ALL NUAs that could exist in a scene are generated BEFORE the scene is narrated
- Full actor sheets are created upfront, not on-demand
- This prevents random NUA creation and ensures narrative consistency
- NUAs are stored in available_npcs and ready for immediate interaction

Architecture:
1. Scene type detected (diner, street, office, etc.)
2. Population template defines who SHOULD be there
3. Full actor sheets generated for all potential NUAs
4. Sympathy initialized between UA and all NUAs
5. Scene narrated with knowledge of who exists
6. Player can interact with any pre-generated NUA instantly
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from actors import NonUserActor
from actor_sheet import ActorSheet
from agents.creator_agent import CreatorAgent


@dataclass
class PopulationRole:
    """Defines a role that should exist in a scene"""
    role_type: str  # "waitress", "patron", "guard", etc.
    is_guaranteed: bool  # True = always present, False = might be present
    count_range: tuple  # (min, max) number of this role
    description_hint: str  # Brief description for LLM generation


class ScenePopulationTemplates:
    """Templates defining typical populations for different scene types"""
    
    TEMPLATES = {
        "diner": [
            PopulationRole("waitress", True, (1, 2), "Friendly or tired waitress working the shift"),
            PopulationRole("cook", True, (1, 1), "Cook working in the kitchen, visible through serving window"),
            PopulationRole("patron", False, (2, 5), "Various diner patrons - truckers, locals, travelers"),
            PopulationRole("manager", False, (0, 1), "Diner owner or manager, might be present")
        ],
        "bar": [
            PopulationRole("bartender", True, (1, 1), "Bartender serving drinks and chatting with customers"),
            PopulationRole("bouncer", False, (0, 1), "Security guard or bouncer at entrance"),
            PopulationRole("patron", False, (3, 8), "Bar patrons - regulars, tourists, troublemakers"),
            PopulationRole("musician", False, (0, 3), "Live band or solo performer")
        ],
        "office": [
            PopulationRole("receptionist", True, (1, 1), "Front desk receptionist managing visitors"),
            PopulationRole("security", False, (1, 2), "Security guard monitoring the lobby"),
            PopulationRole("employee", False, (2, 6), "Office workers, managers, or executives"),
            PopulationRole("janitor", False, (0, 1), "Cleaning staff working after hours")
        ],
        "street": [
            PopulationRole("vendor", False, (0, 2), "Street vendor selling goods or food"),
            PopulationRole("pedestrian", False, (3, 8), "Random pedestrians walking by"),
            PopulationRole("homeless", False, (0, 2), "Homeless person asking for change"),
            PopulationRole("cop", False, (0, 2), "Police officer on patrol")
        ],
        "store": [
            PopulationRole("clerk", True, (1, 2), "Store clerk at register or stocking shelves"),
            PopulationRole("manager", False, (0, 1), "Store manager handling operations"),
            PopulationRole("customer", False, (1, 4), "Other customers shopping"),
            PopulationRole("security", False, (0, 1), "Security guard watching for shoplifters")
        ],
        "warehouse": [
            PopulationRole("worker", False, (2, 5), "Warehouse workers loading/unloading"),
            PopulationRole("foreman", False, (0, 1), "Warehouse supervisor overseeing operations"),
            PopulationRole("driver", False, (0, 2), "Truck driver making deliveries"),
            PopulationRole("guard", False, (0, 2), "Security guard patrolling the area")
        ],
        "club": [
            PopulationRole("bouncer", True, (1, 2), "Bouncer checking IDs at entrance"),
            PopulationRole("dj", False, (0, 1), "DJ playing music"),
            PopulationRole("bartender", True, (1, 2), "Bartender serving drinks"),
            PopulationRole("patron", False, (5, 15), "Club-goers dancing and socializing"),
            PopulationRole("dealer", False, (0, 2), "Drug dealer or black market contact")
        ],
        "default": [
            PopulationRole("person", False, (1, 3), "Generic person appropriate to the scene")
        ]
    }
    
    @classmethod
    def get_template(cls, scene_type: str) -> List[PopulationRole]:
        """Get population template for a scene type"""
        return cls.TEMPLATES.get(scene_type.lower(), cls.TEMPLATES["default"])


class ScenePopulator:
    """Generates full NUA populations before scene narration"""
    
    def __init__(self, creator_agent: CreatorAgent):
        self.creator = creator_agent
    
    def detect_scene_type(self, scene_description: str) -> str:
        """
        Detect scene type from description using keywords
        
        Returns: scene_type string (diner, bar, office, etc.)
        """
        scene_lower = scene_description.lower()
        
        # Check for specific scene types
        if any(word in scene_lower for word in ["diner", "restaurant", "cafe", "eatery"]):
            return "diner"
        elif any(word in scene_lower for word in ["bar", "pub", "tavern", "saloon"]):
            return "bar"
        elif any(word in scene_lower for word in ["office", "corporate", "headquarters", "cubicle"]):
            return "office"
        elif any(word in scene_lower for word in ["street", "sidewalk", "avenue", "boulevard"]):
            return "street"
        elif any(word in scene_lower for word in ["store", "shop", "market", "retail"]):
            return "store"
        elif any(word in scene_lower for word in ["warehouse", "storage", "depot"]):
            return "warehouse"
        elif any(word in scene_lower for word in ["club", "nightclub", "disco", "venue"]):
            return "club"
        else:
            return "default"
    
    def populate_scene(self, scene_description: str, time_of_day: str = "day", tracker=None) -> List[NonUserActor]:
        """
        Generate all potential NUAs for a scene BEFORE narration
        
        Args:
            scene_description: The scene setting/description
            time_of_day: Time context (affects population density)
            tracker: Optional TrackerAgent to check for deceased NUAs
            
        Returns:
            List of fully-generated NonUserActor instances ready for interaction
        """
        import random
        
        # Detect scene type
        scene_type = self.detect_scene_type(scene_description)
        print(f"[POPULATION] Scene type detected: {scene_type}")
        
        # Get population template
        template = ScenePopulationTemplates.get_template(scene_type)
        
        # Generate NUAs based on template
        generated_nuas = []
        
        for role in template:
            # Determine how many of this role to generate
            if role.is_guaranteed:
                count = random.randint(role.count_range[0], role.count_range[1])
            else:
                # 60% chance to include non-guaranteed roles
                if random.random() < 0.6:
                    count = random.randint(role.count_range[0], role.count_range[1])
                else:
                    count = 0
            
            # Generate each NUA for this role
            for i in range(count):
                nua_prompt = f"""Create a {role.role_type} for this scene:

Scene: {scene_description[:300]}
Time: {time_of_day}
Role: {role.role_type}
Description: {role.description_hint}

Generate a unique character with:
- Appropriate name for the setting
- Occupation matching the role
- Personality traits fitting the role
- Skills and S-factors appropriate to their job
- Brief backstory hints in goals

Make them feel like a real person, not a stereotype."""
                
                try:
                    nua = self.creator.generate_nua(nua_prompt, scene_description)
                    if nua:
                        generated_nuas.append(nua)
                        print(f"[POPULATION] Generated {role.role_type}: {nua.sheet.name}")
                except Exception as e:
                    print(f"[POPULATION] Failed to generate {role.role_type}: {e}")
        
        # CRITICAL: Filter out deceased NUAs to prevent resurrection
        if tracker:
            original_count = len(generated_nuas)
            generated_nuas = [
                nua for nua in generated_nuas 
                if tracker.is_nua_alive(nua.sheet.name)
            ]
            removed_count = original_count - len(generated_nuas)
            if removed_count > 0:
                print(f"[POPULATION] ⚰️  Filtered out {removed_count} deceased NUA(s) - they stay dead")
        
        print(f"[POPULATION] Total NUAs generated: {len(generated_nuas)}")
        return generated_nuas
    
    def populate_scene_minimal(self, scene_description: str, max_nuas: int = 3) -> List[NonUserActor]:
        """
        Generate minimal population for quick scenes
        
        Args:
            scene_description: The scene setting
            max_nuas: Maximum number of NUAs to generate
            
        Returns:
            List of 1-3 key NUAs for the scene
        """
        scene_type = self.detect_scene_type(scene_description)
        template = ScenePopulationTemplates.get_template(scene_type)
        
        # Only generate guaranteed roles
        generated_nuas = []
        for role in template:
            if role.is_guaranteed and len(generated_nuas) < max_nuas:
                nua_prompt = f"""Create a {role.role_type} for this scene:

Scene: {scene_description[:300]}
Role: {role.role_type}
Description: {role.description_hint}

Brief character appropriate to the setting."""
                
                try:
                    nua = self.creator.generate_nua(nua_prompt, scene_description)
                    if nua:
                        generated_nuas.append(nua)
                        print(f"[POPULATION] Generated {role.role_type}: {nua.sheet.name}")
                except Exception as e:
                    print(f"[POPULATION] Failed to generate {role.role_type}: {e}")
        
        return generated_nuas


# Integration helper
def populate_scene_with_nuas(creator_agent: CreatorAgent, scene_description: str, 
                             time_context: Dict[str, Any], full_population: bool = True,
                             tracker=None) -> List[NonUserActor]:
    """
    Convenience function to populate a scene with NUAs
    
    Args:
        creator_agent: CreatorAgent instance for NUA generation
        scene_description: Scene description text
        time_context: Time context dict with 'time_of_day' key
        full_population: If True, generate full population; if False, minimal
        tracker: Optional TrackerAgent to check for deceased NUAs
        
    Returns:
        List of generated NUAs ready for interaction
    """
    populator = ScenePopulator(creator_agent)
    time_of_day = time_context.get('time_of_day', 'day')
    
    if full_population:
        return populator.populate_scene(scene_description, time_of_day, tracker=tracker)
    else:
        return populator.populate_scene_minimal(scene_description)


def replace_scene_npcs(available_npcs: List, new_npcs: List[NonUserActor], 
                       tracker=None, location_name: str = "new location") -> None:
    """
    Safely replace NUAs when changing locations (prevents overlap bug)
    
    Args:
        available_npcs: The list to update (will be cleared and refilled)
        new_npcs: New NUAs for the location
        tracker: Optional TrackerAgent to save NUAs to disk
        location_name: Name of new location for logging
    """
    # Clear old NUAs
    old_count = len(available_npcs)
    available_npcs.clear()
    
    # Add new NUAs
    available_npcs.extend(new_npcs)
    
    # Save to disk if tracker provided
    if tracker is not None:
        tracker.save_available_npcs(available_npcs)
    
    print(f"[LOCATION] Replaced {old_count} NUAs with {len(new_npcs)} NUAs at {location_name}")
