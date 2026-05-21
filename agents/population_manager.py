from typing import List, Dict, Any, Optional, Tuple
from actors import NonUserActor, Actor
from agents.creator_agent import CreatorAgent
from openrouter_config import create_role_client, OpenRouterConfig, retry_with_backoff, RetryConfig, robust_llm_call
from json_utils import extract_and_parse_json
import json
from json_utils import _fix_json_formatting
from color_utils import Color

try:
    from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
except ImportError:
    WorldbuildingCategory = None

from rag_lock_utils import get_multi_category_context_for_llm

class PopulationManager:
    """
    Manages the logical population of scenes with NPCs based on context.
    Classifies environments into three types:
    1. Mixed: Background NUAs (crowd/ambience) + Foreground NUAs (independent).
    2. Foreground Only: Only independent NUAs (e.g., interrogation).
    3. Empty: No NUAs (e.g., private bathroom).
    """
    
    def __init__(self, creator_agent: CreatorAgent, logger, context_manager=None, rag_system=None):
        self.creator_agent = creator_agent
        self.logger = logger
        self.context_manager = context_manager
        self.rag_system = rag_system  # For worldbuilding context
        self.client = create_role_client("scene_creation")
        self.model = OpenRouterConfig.get_model_for_role("scene_creation")
    
    def _get_worldbuilding_context(self, query: str, max_tokens: int = 300) -> str:
        """Get relevant worldbuilding context from RAG system."""
        if not self.rag_system:
            return ""
        try:
            categories = []
            if WorldbuildingCategory:
                categories = [
                    WorldbuildingCategory.TEMPORAL,
                    WorldbuildingCategory.CIVILIZATION,
                    WorldbuildingCategory.CULTURE,
                    WorldbuildingCategory.PLACES,
                    WorldbuildingCategory.CITIES,
                    WorldbuildingCategory.UA_OCCUPATIONS,
                    WorldbuildingCategory.NUA_OCCUPATIONS,
                    WorldbuildingCategory.NUA_GENERATION,
                ]

            context = get_multi_category_context_for_llm(
                self.rag_system,
                query=query,
                categories=categories,
                max_tokens_per_category=max(60, int(max_tokens / 4)),
                include_related=True,
            )
            return context if context else ""
        except Exception as e:
            self.logger.log_system(f"RAG query failed in PopulationManager: {e}")
            return ""
        
    def get_present_actors(self, location: str, time_context: Dict[str, Any]) -> List[NonUserActor]:
        """
        Retrieves actors that should be present in this location based on:
        1. Persistence (They were here last time we visited)
        2. Schedule (They work/live here at this time)
        """
        present_actors = []
        
        # 1. Check Persistent Context
        if self.context_manager:
            # We need to access the internal context directly
            # Note: This relies on the updated PersistentContext having location_states
            try:
                ctx = self.context_manager.get_context()
                if hasattr(ctx, 'location_states') and location in ctx.location_states:
                    saved_state = ctx.location_states[location]
                    saved_names = saved_state.get('present_nuas', [])
                    
                    if saved_names:
                        print(f"{Color.SYSTEM}[POPULATION] Restoring {len(saved_names)} persistent actors for {location}...{Color.RESET}")
                        for name in saved_names:
                            # Rehydrate actor
                            # Since we only saved names, we re-generate them based on name + location context
                            # Ideal: Save full character sheet. Current: Name-based regeneration.
                            try:
                                context_str = f"Name: {name}. Location: {location}. Role: Returning inhabitant."
                                nua = self.creator_agent.generate_nua(context_str, scene_description=f"Recreating {name} at {location}")
                                nua.sheet.name = name # Ensure exact name match
                                present_actors.append(nua)
                            except Exception as e:
                                self.logger.log_system(f"Failed to rehydrate {name}: {e}")
            except Exception as e:
                 self.logger.log_system(f"Error reading persistent context: {e}")

        return present_actors

    def check_random_spawns(self, location: str, time_context: Dict[str, Any]) -> List[NonUserActor]:
        """
        Determines if random atmospheric NPCs should spawn.
        """
        new_actors = []
        
        # Simple logic: If we have context, check density
        if self.context_manager:
            try:
                ctx = self.context_manager.get_context()
                # If we know this location, check its density
                if hasattr(ctx, 'location_states') and location in ctx.location_states:
                    saved_state = ctx.location_states[location]
                    current_count = len(saved_state.get('present_nuas', []))
                    
                    # If sparse population (arbitrary threshold < 3), chance to spawn one
                    import random
                    if current_count < 3 and random.random() < 0.3:
                         print(f"{Color.SYSTEM}[POPULATION] Spawning random atmospheric NPC...{Color.RESET}")
                         # Use generate_scene_population for a single random
                         pop_data = self.generate_scene_population(f"A generic version of {location}", time_context)
                         generated, _ = self.populate_actors(pop_data)
                         if generated:
                             new_actors.append(generated[0]) # Just take one
            except Exception:
                pass
                
        return new_actors
        
    def generate_scene_population(self, scene_description: str, time_context: Dict[str, Any], world_context: str = "") -> Dict[str, Any]:
        """
        Generates a structured population roster for the scene.
        Returns a dict containing:
        - 'foreground_roster': List of independent NPCs to create.
        - 'background_atmosphere': Description of background crowd (if any).
        """
        time_str = time_context.get('formatted_time', 'Unknown time')
        
        # Get worldbuilding context for setting-appropriate NPCs
        worldbuilding_context = self._get_worldbuilding_context(
            query=f"{scene_description[:150]} population inhabitants occupations culture society era setting",
            max_tokens=300
        )
        worldbuilding_section = ""
        if worldbuilding_context:
            worldbuilding_section = f"""
        **WORLDBUILDING CONTEXT (CRITICAL - NPCs must be setting-appropriate):**
        {worldbuilding_context}
        
        **SETTING ENFORCEMENT:** All NPCs MUST fit this world's setting.
        - If medieval: NO modern occupations (office workers, drivers, etc.)
        - If futuristic: Technology and occupations should match the era
        - If specific time period: Use period-appropriate roles and names
        - Names should fit the cultural context of the world
        """
        
        prompt = f"""
        You are a world simulation logic engine. 
        Determine who is present in the current scene based on the environment, time, and context.
        
        **SCENE:** {scene_description}
        **TIME:** {time_str}
        **CONTEXT:** {world_context}
        {worldbuilding_section}
        **POPULATION LOGIC (Choose One Type):**
        1. **MIXED (Crowd + Individuals):** Public places like classrooms, diners, streets. Contains generic background people AND specific independent characters.
        2. **FOREGROUND ONLY (Specific Individuals):** Private/Specific interactions like interrogation rooms, meetings, ambushes. Only independent characters.
        3. **EMPTY (Solitary):** Private places like bathrooms, empty hallways, abandoned sites. No people.
        
        **DEFINITIONS:**
        - **Foreground NUAs:** Independent characters with names, roles, and goals. Can be visible OR hidden (ambushing).
        - **Background Atmosphere:** The general presence of the crowd (e.g., "students chatting", "diners eating").
        
        Respond with ONLY a valid JSON object:
        {{
            "scene_type": "mixed" | "foreground_only" | "empty",
            "background_atmosphere": "Description of the crowd/ambience (null if empty or foreground_only)",
            "foreground_roster": [
                {{
                    "role": "Role Name",
                    "name": "Character Name",
                    "reasoning": "Why they are here",
                    "description": "Visual description",
                    "is_hidden": true/false, // TRUE if hiding/ambushing/stealthy
                    "initial_goal": "What are they doing right now?"
                }}
            ]
        }}
        """
        
        try:
            # Use centralized robust LLM call
            content = robust_llm_call(
                client=self.client,
                messages=[{'role': 'user', 'content': prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=1000,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="POPULATION ROSTER"
            )
            
            if not content:
                return {"foreground_roster": [], "background_atmosphere": None}
            
            json_data = extract_and_parse_json(content)
            
            # Validation
            if not isinstance(json_data, dict):
                return {"foreground_roster": [], "background_atmosphere": None}
                
            return json_data
            
        except Exception as e:
            self.logger.log_system(f"Error generating population roster: {e}")
            return {"foreground_roster": [], "background_atmosphere": None}

    def populate_actors(self, population_data: Dict[str, Any]) -> Tuple[List[NonUserActor], Optional[str]]:
        """
        Converts population data into actual NonUserActor objects and background context.
        Returns: (List of independent actors, Background atmosphere string)
        """
        roster = population_data.get("foreground_roster", [])
        background_atmosphere = population_data.get("background_atmosphere")
        
        actors = []
        for entry in roster:
            try:
                print(f"{Color.SYSTEM}Generating independent actor: {entry['role']}...{Color.RESET}")
                # Create a context string for the CreatorAgent
                context = f"Role: {entry['role']}. Reasoning: {entry['reasoning']}. Description: {entry['description']}. Goal: {entry.get('initial_goal', 'Exist')}"
                
                # Use CreatorAgent to build full actor
                _existing_names = [a.sheet.name for a in actors if hasattr(a, 'sheet')]
                nua = self.creator_agent.generate_nua(context, scene_description=entry['description'], existing_names=_existing_names)

                # Override name if specific one provided
                if entry.get('name') and entry['name'] != "Unknown":
                     nua.sheet.name = entry['name']
                
                # Set initial hidden state if applicable
                if entry.get('is_hidden', False):
                    nua.is_hidden = True
                    print(f"{Color.SYSTEM}  -> Created hidden actor (will not be initially described){Color.RESET}")
                else:
                    nua.is_hidden = False
                
                # Assign initial goal/task from roster
                if entry.get('initial_goal'):
                    if not hasattr(nua.sheet, 'goals'):
                         nua.sheet.goals = []
                    nua.sheet.goals.append(entry['initial_goal'])

                actors.append(nua)
            except Exception as e:
                self.logger.log_system(f"Error populating actor {entry.get('role')}: {e}")
                
        return actors, background_atmosphere

    def promote_background_actor(self, query: str, background_atmosphere: str, scene_description: str) -> Optional[NonUserActor]:
        """
        Attempts to promote a background entity into a foreground actor based on user interaction.
        Returns the new actor if successful, or None if the query doesn't match the background.
        """
        if not background_atmosphere:
            return None
            
        prompt = f"""
        The user is trying to interact with '{query}'.
        
        **SCENE CONTEXT:**
        Scene: {scene_description}
        Background Atmosphere: {background_atmosphere}
        
        **TASK:**
        Determine if '{query}' plausibly refers to someone present in the background crowd/atmosphere.
        - If YES: Create a specific identity for this person.
        - If NO (or if the query refers to an object/setting detail, not a person): Return null.
        
        Respond with ONLY a valid JSON object (or null):
        {{
            "is_match": true,
            "role": "Student",
            "name": "Generated Name",
            "description": "Visual description consistent with background",
            "reasoning": "Why this matches the background context",
            "initial_goal": "Reacting to user"
        }}
        """
        
        try:
            # Use centralized robust LLM call
            content = robust_llm_call(
                client=self.client,
                messages=[{'role': 'user', 'content': prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=500,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="BACKGROUND PROMOTION"
            )
            
            if not content or ("null" in content.lower() and len(content) < 10):
                return None
                
            data = extract_and_parse_json(content)
            
            if not data or not data.get('is_match'):
                return None
                
            print(f"{Color.SUCCESS}Promoting background actor '{data['role']}' to foreground...{Color.RESET}")
            
            # Create the actor using the standard pipeline
            context = f"Role: {data['role']}. Reasoning: Promoted from background interaction. Description: {data['description']}. Goal: {data.get('initial_goal', 'Exist')}"
            nua = self.creator_agent.generate_nua(context, scene_description=data['description'])
            if data.get('name'):
                nua.sheet.name = data['name']
            
            nua.is_hidden = False # Promoted actors are by definition interacting/visible
            
            return nua
            
        except Exception as e:
            self.logger.log_system(f"Error promoting background actor: {e}")
            return None

    def _extract_json(self, text: str) -> Any:
        try:
            if "```json" in text:
                start = text.find("```json") + 7
                end = text.find("```", start)
                text = text[start:end]
            elif "{" in text:
                 start = text.find("{")
                 end = text.rfind("}") + 1
                 text = text[start:end]
            
            text = _fix_json_formatting(text)
            return json.loads(text)
        except Exception:
            return {}
