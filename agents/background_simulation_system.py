import random
import re
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from actors import UserActor, NonUserActor, Actor
from color_utils import Color

# Import stranger description system for diegetic NPC descriptions
try:
    from stranger_description_system import (
        StrangerDescriber,
        get_nua_description,
        get_nua_definite_description,
    )
    STRANGER_SYSTEM_AVAILABLE = True
except ImportError:
    STRANGER_SYSTEM_AVAILABLE = False


class WorldEventType(Enum):
    """Types of observable world events."""
    NUA_ROAM = "nua_roam"           # NUA doing routine action
    NUA_TO_NUA = "nua_to_nua"       # NUA interacting with another NUA
    INUA_HAZARD = "inua_hazard"     # Environmental hazard affecting someone
    NUA_TO_USER = "nua_to_user"     # NUA initiating with user (triggers encounter)
    AMBIENT = "ambient"              # Environmental changes (weather, sounds)


class ObservableEvent:
    """An event the user can witness in the world."""
    def __init__(self, 
                 event_type: WorldEventType,
                 actors_involved: List[str],
                 narrative: str,
                 requires_user_response: bool = False,
                 mechanical_effects: Dict[str, Any] = None):
        self.event_type = event_type
        self.actors_involved = actors_involved
        self.narrative = narrative
        self.requires_user_response = requires_user_response
        self.mechanical_effects = mechanical_effects or {}


class BackgroundSimulationSystem:
    """
    Manages background simulation for a LIVING WORLD.
    
    Key Philosophy: The world doesn't wait for the user. NUAs act independently,
    INUAs create hazards, and events unfold that the user witnesses.
    
    Features:
    - NUA autonomous actions (roaming, tasks, conversations)
    - NUA-to-NUA interactions (observable by user)
    - INUA hazard events (machinery failing, objects falling, environmental dangers)
    - Observable event generation with perceptual narratives
    - Internal voice reactions to witnessed events
    """
    
    def __init__(self, 
                 decider_agent, 
                 narrator_agent=None, 
                 tracker_agent=None,
                 narrative_context_manager=None,
                 exchange_system=None):
        self.decider = decider_agent
        self.narrator = narrator_agent
        self.tracker = tracker_agent
        self.narrative_context_manager = narrative_context_manager
        self.exchange_system = exchange_system
        
        # Track recent events to avoid repetition
        self.recent_events: List[ObservableEvent] = []
        self.max_recent_events = 10
        
        # INUA hazard configuration
        self.inua_hazard_chance = 0.15  # 15% chance per turn of environmental hazard
        self.nua_interaction_chance = 0.25  # 25% chance NUAs interact with each other

    def _spatial_facts_block(self) -> str:
        try:
            from spatial_context_system import build_spatial_facts
            sf = build_spatial_facts(session_id=getattr(self.tracker, 'session_id', None) if self.tracker else None)
            if isinstance(sf, str) and sf.strip():
                return f"""

AUTHORITATIVE SPATIAL FACTS (MUST NOT CONTRADICT):
{sf.strip()}
""".rstrip()
        except Exception:
            return ""

    def _is_valid_roam_narrative(self, narrative: Optional[str]) -> bool:
        try:
            if not narrative:
                return False
            t = str(narrative).strip()
            if not t:
                return False

            t = t.strip().strip('.,!?;:\'"')
            t = t.strip()
            if not t:
                return False

            if len(t) < 6:
                return False

            words = re.findall(r"[A-Za-z]{2,}", t)
            if len(words) < 2:
                return False

            alpha_chars = sum(len(w) for w in words)
            if alpha_chars < 8:
                return False

            return True
        except Exception:
            return False

    def _roam_narrative_signal_metrics(self, narrative: Optional[str]) -> Dict[str, Any]:
        try:
            raw = "" if narrative is None else str(narrative)
            t = raw.strip()
            t2 = t.strip().strip('.,!?;:\'"')
            words = re.findall(r"[A-Za-z]{2,}", t2)
            alpha_chars = sum(len(w) for w in words)
            return {
                'raw_len': len(raw),
                'stripped_len': len(t2),
                'word_count': len(words),
                'alpha_chars': alpha_chars,
            }
        except Exception:
            return {}
        
    def prepare_turn_order(self, user_actor: Actor, available_nuas: List[Actor]) -> List[Dict[str, Any]]:
        """
        Rolls initiatives and returns a sorted list of turn entries.
        Each entry: {'actor': Actor, 'score': int, 'is_user': bool}
        """
        if not available_nuas:
             # Just user
             return [{'actor': user_actor, 'score': 100, 'is_user': True}]
             
        initiatives = self._roll_initiatives(user_actor, available_nuas)
        turn_order = sorted(initiatives, key=lambda x: x['score'], reverse=True)
        
        # Display turn order debug
        names = [f"{e['actor'].sheet.name}({e['score']})" for e in turn_order]
        # print(f"{Color.SYSTEM}[BG SIM] Turn Order: {', '.join(names)}{Color.RESET}")
        
        return turn_order

    def execute_pre_user_turns(self, 
                               turn_order: List[Dict[str, Any]], 
                               user_actor: Actor,
                               available_nuas: List[Actor],
                               scene_description: str,
                               time_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes turns for NUAs that appear BEFORE the user in the turn order.
        Returns a status dict: {'count': int, 'interrupt': bool, 'event': dict}
        """
        count = 0
        dynamic_context = ""
        
        for entry in turn_order:
            if entry['is_user']:
                break
            
            # Execute NUA turn
            actor = entry['actor']
            # If the actor has departed (removed from available_nuas), skip them even if they remain in turn_order
            try:
                if actor not in (available_nuas or []):
                    continue
            except Exception:
                pass
            if isinstance(actor, NonUserActor):
                result = self._execute_nua_turn(
                    actor, 
                    available_nuas + [user_actor], 
                    scene_description, 
                    time_context,
                    dynamic_context
                )
                count += 1
                
                # Update dynamic context with this action
                if result.get('narrative_description'):
                    dynamic_context += f"\n- {actor.sheet.name}: {result.get('narrative_description')}"
                
                # Check for exchange start
                if result.get('action_type') == 'exchange_start':
                     return {
                         'count': count,
                         'interrupt': True,
                         'event': {
                             'type': 'exchange_start',
                             'initiator': actor,
                             'target_name': result.get('target'),
                             'narrative': result.get('narrative_description')
                         }
                     }
                
                # Check for NUA departure - remove them from available_nuas
                if result.get('action_type') == 'depart_location':
                    try:
                        if actor in available_nuas:
                            available_nuas.remove(actor)
                            print(f"{Color.INFO}👋 {actor.sheet.name} has left the location.{Color.RESET}")
                    except Exception:
                        pass
                
        return {'count': count, 'interrupt': False, 'event': None}

    def execute_post_user_turns(self, 
                                turn_order: List[Dict[str, Any]], 
                                user_actor: Actor,
                                available_nuas: List[Actor],
                                scene_description: str,
                                time_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes turns for NUAs that appear AFTER the user in the turn order.
        Returns a status dict.
        """
        user_found = False
        count = 0
        dynamic_context = "" # Reset for post-user block, or could pass in if we wanted continuity from pre-user
        
        for entry in turn_order:
            if entry['is_user']:
                user_found = True
                continue
            
            if user_found:
                # Execute NUA turn
                actor = entry['actor']
                # If the actor has departed (removed from available_nuas), skip them even if they remain in turn_order
                try:
                    if actor not in (available_nuas or []):
                        continue
                except Exception:
                    pass
                if isinstance(actor, NonUserActor):
                    result = self._execute_nua_turn(
                        actor, 
                        available_nuas + [user_actor], 
                        scene_description, 
                        time_context,
                        dynamic_context
                    )
                    count += 1
                    
                    if result.get('narrative_description'):
                        dynamic_context += f"\n- {actor.sheet.name}: {result.get('narrative_description')}"

                    if result.get('action_type') == 'exchange_start':
                         return {
                             'count': count,
                             'interrupt': True,
                             'event': {
                                 'type': 'exchange_start',
                                 'initiator': actor,
                                 'target_name': result.get('target'),
                                 'narrative': result.get('narrative_description')
                             }
                         }
                    
                    # Check for NUA departure - remove them from available_nuas
                    if result.get('action_type') == 'depart_location':
                        try:
                            if actor in available_nuas:
                                available_nuas.remove(actor)
                                print(f"{Color.INFO}👋 {actor.sheet.name} has left the location.{Color.RESET}")
                        except Exception:
                            pass
                    
        return {'count': count, 'interrupt': False, 'event': None}

    def simulate_excluded_actors_during_encounter(self,
                                                   excluded_actors: List[Actor],
                                                   encounter_participants: List[Actor],
                                                   scene_description: str,
                                                   time_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Simulates background actions for NPCs NOT in the current encounter.
        
        These actors continue their lives while the encounter unfolds - they might:
        - Watch the encounter (witness behavior)
        - Continue their own tasks
        - Leave the area
        - React to the commotion
        
        Returns list of observable actions (brief, non-interrupting).
        """
        background_actions = []
        
        for actor in excluded_actors:
            if not isinstance(actor, NonUserActor):
                continue
            
            # 50% chance to do something observable
            if random.random() < 0.5:
                continue
            
            # Determine background action type
            action_type = random.choice([
                'watching',      # Observing the encounter
                'continuing',    # Continuing their own task
                'nervous',       # Showing nervousness
                'leaving'        # Departing the area
            ])
            
            actor_name = actor.sheet.name
            
            # Generate brief narrative based on action type
            narratives = {
                'watching': f"You notice {actor_name} watching the situation unfold from a distance.",
                'continuing': f"In your peripheral vision, {actor_name} continues about their business.",
                'nervous': f"You catch {actor_name} shifting nervously, keeping their distance.",
                'leaving': f"You see {actor_name} quietly slip away from the area."
            }
            
            background_actions.append({
                'actor': actor,
                'actor_name': actor_name,
                'action_type': action_type,
                'narrative': narratives.get(action_type, f"{actor_name} remains in the area."),
                'should_depart': action_type == 'leaving'
            })

            # Update NPC goal/task system for background actions during encounters
            try:
                if hasattr(actor, 'goal_task_manager') and actor.goal_task_manager:
                    action_description = narratives.get(action_type, f"{actor_name} remains in the area.")
                    actor.goal_task_manager.update_goal(
                        action_taken=action_description,
                        outcome="success",
                        context=f"Background action during encounter: {action_type}"
                    )
                    print(f"{Color.CYAN}[GOAL/TASK] Updated {actor_name}'s goals/tasks from encounter background action{Color.RESET}")
            except Exception:
                pass  # Non-critical

        return background_actions

    def simulate_world_events(self,
                              user_actor: Actor,
                              available_nuas: List[Actor],
                              available_inuas: List[Actor],
                              scene_description: str,
                              time_context: Dict[str, Any]) -> List[ObservableEvent]:
        """
        Simulates world events that occur independently of user action.
        Returns a list of observable events the user witnesses.
        
        This is the CORE of the living world - things happen whether or not
        the user interacts with them.
        """
        observable_events = []
        
        # 1. Check for INUA hazard events (machinery, environment, objects)
        if available_inuas and random.random() < self.inua_hazard_chance:
            hazard_event = self._generate_inua_hazard(
                available_inuas, 
                available_nuas + [user_actor],
                scene_description,
                time_context
            )
            if hazard_event:
                observable_events.append(hazard_event)
        
        # 2. Check for NUA-to-NUA interactions
        if len(available_nuas) >= 2 and random.random() < self.nua_interaction_chance:
            nua_event = self._generate_nua_interaction(
                available_nuas,
                user_actor,
                scene_description,
                time_context
            )
            if nua_event:
                observable_events.append(nua_event)
        
        # 3. Store events for context
        for event in observable_events:
            self._record_event(event)
        
        return observable_events

    def _generate_inua_hazard(self,
                              inuas: List,  # Can be Actor objects or virtual INUA dicts
                              potential_victims: List[Actor],
                              scene_description: str,
                              time_context: Dict[str, Any]) -> Optional[ObservableEvent]:
        """
        Generates an environmental hazard event from an INUA.
        Examples: crane falling, machinery malfunctioning, structure collapsing.
        
        INUAs can be:
        - Full Actor objects (InanimateNonUserActor)
        - Virtual INUA dicts extracted from scene description {'name': str, 'context': str, 'is_virtual': bool}
        """
        # If no explicit INUAs, try to extract virtual ones from scene
        if not inuas:
            inuas = self.create_virtual_inuas_from_scene(scene_description)
        
        if not inuas:
            return None
        
        # Select a random INUA as the hazard source
        hazard_source = random.choice(inuas)
        
        # Handle both Actor objects and virtual INUA dicts
        if isinstance(hazard_source, dict):
            hazard_name = hazard_source.get('name', 'Environmental Hazard')
        elif hasattr(hazard_source, 'sheet'):
            hazard_name = hazard_source.sheet.name
        else:
            hazard_name = str(hazard_source)
        
        # Determine if it affects someone or is just environmental
        affects_someone = random.random() < 0.6 and potential_victims
        
        if affects_someone:
            # Pick a victim (prefer NUAs over user for drama without forcing user response)
            nua_victims = [v for v in potential_victims if isinstance(v, NonUserActor)]
            if nua_victims:
                victim = random.choice(nua_victims)
                victim_name = victim.sheet.name
            else:
                # Could affect user - this would require response
                victim = potential_victims[0]
                victim_name = victim.sheet.name
                
            # Generate hazard narrative via LLM
            narrative = self._generate_hazard_narrative(
                hazard_name, victim_name, scene_description, time_context
            )
            
            # Determine mechanical effects
            effects = {
                'victim': victim_name,
                'hazard_source': hazard_name,
                'status_shift': {
                    'target': 'STAMINA',
                    'polarity': 'Subtractive',
                    'severity': random.randint(1, 3),
                    'shift_type': 'Temporary'
                }
            }
            
            requires_response = isinstance(victim, UserActor)
            
            return ObservableEvent(
                event_type=WorldEventType.INUA_HAZARD,
                actors_involved=[hazard_name, victim_name],
                narrative=narrative,
                requires_user_response=requires_response,
                mechanical_effects=effects
            )
        else:
            # Environmental event without victim
            narrative = self._generate_ambient_hazard_narrative(
                hazard_name, scene_description, time_context
            )
            
            return ObservableEvent(
                event_type=WorldEventType.AMBIENT,
                actors_involved=[hazard_name],
                narrative=narrative,
                requires_user_response=False
            )

    def _generate_nua_interaction(self,
                                   nuas: List[Actor],
                                   user_actor: Actor,
                                   scene_description: str,
                                   time_context: Dict[str, Any]) -> Optional[ObservableEvent]:
        """
        Generates an interaction between two NUAs that the user observes.
        This could be conversation, conflict, cooperation, etc.
        """
        if len(nuas) < 2:
            return None
        
        # Select two NUAs to interact
        nua1, nua2 = random.sample(nuas, 2)
        
        # Get their relationship context
        sympathy_1_to_2 = 0
        sympathy_2_to_1 = 0
        try:
            sympathy_1_to_2 = nua1.sheet.get_sympathy(nua2.sheet.name)
            sympathy_2_to_1 = nua2.sheet.get_sympathy(nua1.sheet.name)
        except Exception:
            pass
        
        # Determine interaction type based on relationship
        avg_sympathy = (sympathy_1_to_2 + sympathy_2_to_1) / 2
        
        if avg_sympathy >= 2:
            interaction_type = "friendly"
        elif avg_sympathy <= -2:
            interaction_type = "hostile"
        else:
            interaction_type = "neutral"
        
        # Get stranger-appropriate descriptions for NUAs
        if STRANGER_SYSTEM_AVAILABLE:
            nua1_desc = get_nua_definite_description(nua1, user_actor, scene_description)
            nua2_desc = get_nua_definite_description(nua2, user_actor, scene_description)
        else:
            nua1_desc = nua1.sheet.name
            nua2_desc = nua2.sheet.name
        
        # Generate interaction narrative using stranger descriptions
        narrative = self._generate_nua_interaction_narrative(
            nua1_desc, nua1.sheet.occupation,
            nua2_desc, nua2.sheet.occupation,
            interaction_type,
            scene_description,
            time_context
        )
        
        # Determine if this escalates to an exchange
        escalates = interaction_type == "hostile" and random.random() < 0.4
        
        effects = {
            'initiator': nua1.sheet.name,
            'target': nua2.sheet.name,
            'interaction_type': interaction_type,
            'escalates_to_exchange': escalates
        }
        
        return ObservableEvent(
            event_type=WorldEventType.NUA_TO_NUA,
            actors_involved=[nua1.sheet.name, nua2.sheet.name],
            narrative=narrative,
            requires_user_response=False,
            mechanical_effects=effects
        )

    def _generate_hazard_narrative(self, hazard_name: str, victim_name: str, 
                                    scene_description: str, time_context: Dict) -> str:
        """Generate a perceptual narrative for a hazard affecting someone."""
        if not self.narrator:
            return f"You see {hazard_name} suddenly give way, striking {victim_name}!"
        
        try:
            # Get RAG context for narrative style
            rag_context = self.get_hazard_narrative_context()
            rag_section = f"\n\nNARRATIVE STYLE REFERENCE:\n{rag_context}" if rag_context else ""

            spatial_facts_section = self._spatial_facts_block()
            if spatial_facts_section:
                spatial_facts_section = f"\n\n{spatial_facts_section}"
            
            prompt = f"""Generate a brief, visceral PERCEPTUAL description (2-3 sentences) of what the observer SEES and HEARS.

Scene: {scene_description[:300]}
Time: {time_context.get('formatted_time', 'Unknown') if time_context else 'Unknown'}

Event: {hazard_name} (an environmental hazard/object) suddenly affects {victim_name}.
{spatial_facts_section}
{rag_section}

Rules:
- Write what the observer PERCEIVES through their senses (sight, sound, smell)
- Use present tense, immediate and visceral
- Do NOT describe internal thoughts or motivations
- Make it dramatic but realistic
- Include sensory details (crash, groan, dust, sparks, etc.)

Generate the perceptual description:"""
            
            response = self.narrator._call_llm(prompt)
            if response and len(response.strip()) > 20:
                return response.strip()
        except Exception as e:
            print(f"{Color.WARNING}[BG SIM] Hazard narrative generation failed: {e}{Color.RESET}")
        
        return f"You see {hazard_name} suddenly give way, striking {victim_name}!"

    def _generate_ambient_hazard_narrative(self, hazard_name: str,
                                            scene_description: str, time_context: Dict) -> str:
        """Generate a perceptual narrative for an environmental event without victim."""
        if not self.narrator:
            return f"You hear a loud noise from {hazard_name}—something shifts dangerously."
        
        try:
            spatial_facts_section = self._spatial_facts_block()
            if spatial_facts_section:
                spatial_facts_section = f"\n\n{spatial_facts_section}"

            prompt = f"""Generate a brief PERCEPTUAL description (1-2 sentences) of an environmental event.

Scene: {scene_description[:300]}
Time: {time_context.get('formatted_time', 'Unknown') if time_context else 'Unknown'}
{spatial_facts_section}

Event: {hazard_name} makes a concerning noise or movement—a near-miss or warning sign.

Rules:
- Write what the observer PERCEIVES (sight, sound, smell)
- Present tense, immediate
- Create tension without actual harm
- Sensory details only

Generate the perceptual description:"""
            
            response = self.narrator._call_llm(prompt)
            if response and len(response.strip()) > 15:
                return response.strip()
        except Exception as e:
            print(f"{Color.WARNING}[BG SIM] Ambient narrative generation failed: {e}{Color.RESET}")
        
        return f"You hear a loud noise from {hazard_name}—something shifts dangerously."

    def _generate_nua_interaction_narrative(self, nua1_name: str, nua1_occupation: str,
                                             nua2_name: str, nua2_occupation: str,
                                             interaction_type: str,
                                             scene_description: str,
                                             time_context: Dict) -> str:
        """Generate a perceptual narrative for NUA-to-NUA interaction."""
        if not self.narrator:
            if interaction_type == "hostile":
                return f"You see {nua1_name} and {nua2_name} squaring off, tension crackling between them."
            elif interaction_type == "friendly":
                return f"You notice {nua1_name} and {nua2_name} talking, their body language relaxed."
            else:
                return f"You observe {nua1_name} and {nua2_name} exchanging words."
        
        try:
            # Get RAG context for NUA interactions
            rag_context = self.get_nua_interaction_context()
            rag_section = f"\n\nINTERACTION STYLE REFERENCE:\n{rag_context}" if rag_context else ""

            spatial_facts_section = self._spatial_facts_block()
            if spatial_facts_section:
                spatial_facts_section = f"\n\n{spatial_facts_section}"
            
            tone_guidance = {
                "hostile": "tense, aggressive body language, raised voices, threatening postures",
                "friendly": "relaxed, warm, perhaps laughing or sharing something",
                "neutral": "professional, transactional, neither warm nor cold"
            }
            
            prompt = f"""Generate a brief PERCEPTUAL description (2-3 sentences) of what the observer SEES and HEARS.

Scene: {scene_description[:300]}
Time: {time_context.get('formatted_time', 'Unknown') if time_context else 'Unknown'}
{spatial_facts_section}

Event: {nua1_name} ({nua1_occupation}) interacts with {nua2_name} ({nua2_occupation}).
Tone: {interaction_type} - {tone_guidance.get(interaction_type, 'neutral')}
{rag_section}

CRITICAL RULES:
- START with "You see..." or "You notice..." or "You observe..." or similar perceptual opener
- Write what the observer PERCEIVES from a distance (sight, sound)
- Use the EXACT descriptions provided above for the people (e.g., "the waitress", "a hulking man")
- Do NOT invent names for strangers - use only the descriptions given
- They may catch snippets of dialogue but not full conversations
- Describe body language, gestures, tone of voice
- Present tense, immediate
- Do NOT describe internal thoughts
- Make it feel like a living world moment

Generate the perceptual description:"""
            
            response = self.narrator._call_llm(prompt)
            if response and len(response.strip()) > 20:
                return response.strip()
        except Exception as e:
            print(f"{Color.WARNING}[BG SIM] NUA interaction narrative failed: {e}{Color.RESET}")
        
        # Fallback
        if interaction_type == "hostile":
            return f"You see {nua1_name} and {nua2_name} squaring off, tension crackling between them."
        elif interaction_type == "friendly":
            return f"You notice {nua1_name} and {nua2_name} talking, their body language relaxed."
        else:
            return f"You observe {nua1_name} and {nua2_name} exchanging words."

    def generate_internal_voice_reaction(self, event: ObservableEvent, 
                                          user_actor: Actor) -> Optional[str]:
        """Generate the user's internal voice reaction to a witnessed event."""
        if not self.narrator:
            return None
        
        try:
            # Get user's personality for voice consistency
            personality = ""
            if hasattr(user_actor, 'sheet') and hasattr(user_actor.sheet, 'personality_traits'):
                traits = user_actor.sheet.personality_traits
                if isinstance(traits, dict):
                    personality = f"Internal: {traits.get('internal', 'thoughtful')}"
            
            # STRANGER SYSTEM: Only use names the UA actually knows
            # The narrative already uses stranger descriptions, but actors_involved has raw names
            # For internal voice, we should only think about people by name if we KNOW their name
            actors_description = []
            if STRANGER_SYSTEM_AVAILABLE:
                from stranger_description_system import is_npc_name_known
                for actor_name in event.actors_involved:
                    if is_npc_name_known(actor_name):
                        actors_description.append(actor_name)  # Known - use name
                    else:
                        actors_description.append("that person")  # Unknown - generic reference
            else:
                actors_description = event.actors_involved

            spatial_facts_section = self._spatial_facts_block()
            if spatial_facts_section:
                spatial_facts_section = f"\n\n{spatial_facts_section}"
            
            prompt = f"""Generate a brief INTERNAL VOICE reaction (1-2 sentences) to what was just witnessed.

Event witnessed: {event.narrative}
Event type: {event.event_type.value}
People involved: {', '.join(actors_description)}
{spatial_facts_section}

Character personality: {personality}

Rules:
- First person internal monologue ("I", "my", "me")
- React to the SPECIFIC details witnessed
- Can be concern, curiosity, self-preservation instinct, empathy, etc.
- Keep it brief and natural
- NO explicit sensory verbs ("I see", "I hear") - state thoughts directly
- IMPORTANT: Only refer to people by NAME if you know them. Otherwise use descriptions like "that guy", "the waitress", etc.

Examples:
- "Christ. That could've been me."
- "That guy... is he okay? Should I—no, others are closer."
- "Those two have been at each other's throats all week. This won't end well."

Generate the internal voice:"""
            
            response = self.narrator._call_llm(prompt)
            if response and len(response.strip()) > 5:
                return response.strip().strip('"')
        except Exception as e:
            print(f"{Color.WARNING}[BG SIM] Internal voice generation failed: {e}{Color.RESET}")
        
        return None

    def display_observable_event(self, event: ObservableEvent, 
                                  user_actor: Actor = None,
                                  show_internal_voice: bool = True) -> None:
        """Display an observable event with appropriate formatting."""
        # Header based on event type
        headers = {
            WorldEventType.INUA_HAZARD: f"{Color.ERROR}━━━ ⚠️ ENVIRONMENTAL HAZARD ━━━{Color.RESET}",
            WorldEventType.NUA_TO_NUA: f"{Color.INFO}━━━ 👥 NEARBY ACTIVITY ━━━{Color.RESET}",
            WorldEventType.AMBIENT: f"{Color.SYSTEM}━━━ 🌍 ENVIRONMENT ━━━{Color.RESET}",
            WorldEventType.NUA_TO_USER: f"{Color.WARNING}━━━ ⚡ SOMEONE APPROACHES ━━━{Color.RESET}",
            WorldEventType.NUA_ROAM: f"{Color.SUCCESS}━━━ NUA ACTION ━━━{Color.RESET}"
        }
        
        header = headers.get(event.event_type, f"{Color.SYSTEM}━━━ WORLD EVENT ━━━{Color.RESET}")
        
        print(f"\n{header}")
        print(f"{Color.NARRATIVE}*{event.narrative}*{Color.RESET}")
        # Route nearby activity / hazard events to the narrative display
        try:
            from pygame_narrative_display import send_narrator
            send_narrator(event.narrative)
        except Exception:
            pass

        # Generate and show internal voice if requested
        if show_internal_voice and user_actor and event.event_type != WorldEventType.AMBIENT:
            internal_voice = self.generate_internal_voice_reaction(event, user_actor)
            if internal_voice:
                print(f"\n{Color.INTERNAL_VOICE}━━━ 💭 INTERNAL VOICE ━━━{Color.RESET}")
                print(f"{Color.INTERNAL_VOICE}{internal_voice}{Color.RESET}")
                try:
                    from pygame_narrative_display import send_internal_voice
                    send_internal_voice(internal_voice)
                except Exception:
                    pass

        # Show mechanical effects hint if significant
        if event.mechanical_effects.get('escalates_to_exchange'):
            print(f"\n{Color.WARNING}The situation looks like it might escalate...{Color.RESET}")

    def _record_event(self, event: ObservableEvent) -> None:
        """Record event for context and repetition prevention."""
        self.recent_events.append(event)
        if len(self.recent_events) > self.max_recent_events:
            self.recent_events.pop(0)
        
        # Also save to narrative context if available
        if self.narrative_context_manager:
            try:
                from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
                
                importance = NarrativeImportance.ROUTINE
                if event.event_type == WorldEventType.INUA_HAZARD:
                    importance = NarrativeImportance.SIGNIFICANT
                elif event.event_type == WorldEventType.NUA_TO_NUA:
                    if event.mechanical_effects.get('escalates_to_exchange'):
                        importance = NarrativeImportance.SIGNIFICANT
                
                self.narrative_context_manager.add_narrative_event(
                    event_type=NarrativeEventType.ACTION_SEQUENCE,
                    narrative_text=event.narrative,
                    actors_involved=event.actors_involved,
                    importance=importance,
                    emotional_tone="tense" if event.event_type == WorldEventType.INUA_HAZARD else "neutral",
                    scene_context=f"World event: {event.event_type.value}"
                )
            except Exception:
                pass

    def apply_event_effects(self, event: ObservableEvent, 
                            actors_by_name: Dict[str, Actor]) -> List[str]:
        """
        Apply mechanical effects from an event to actors.
        Returns list of effect descriptions.
        """
        applied_effects = []
        effects = event.mechanical_effects
        
        if not effects:
            return applied_effects
        
        # Handle status shifts (e.g., from hazards)
        if 'status_shift' in effects and 'victim' in effects:
            victim_name = effects['victim']
            victim = actors_by_name.get(victim_name)
            
            if victim and hasattr(victim, 'sheet'):
                shift = effects['status_shift']
                try:
                    from actor_sheet import StatusType
                    status_type = StatusType[shift['target']]
                    severity = shift['severity']
                    
                    if shift['polarity'] == 'Subtractive':
                        severity = -severity
                    
                    # Apply the shift
                    if hasattr(victim.sheet, 'apply_status_shift'):
                        victim.sheet.apply_status_shift(
                            status_type=status_type,
                            magnitude=severity,
                            is_temporary=(shift.get('shift_type') == 'Temporary')
                        )
                        applied_effects.append(
                            f"{victim_name}: {shift['target']} {'+' if severity > 0 else ''}{severity}"
                        )
                except Exception as e:
                    print(f"{Color.WARNING}[BG SIM] Failed to apply effect: {e}{Color.RESET}")
        
        return applied_effects

    def _roll_initiatives(self, user_actor: Actor, nuas: List[Actor]) -> List[Dict]:
        actors = [user_actor] + nuas
        results = []
        from actor_sheet import SFactorType, StatusType
        
        for actor in actors:
            # Calculate Initiative: Swiftness + (Stamina+Spirit)/2 + Serendipity
            swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
            
            stamina = 0
            spirit = 0
            if hasattr(actor.sheet, 'statuses'):
                if StatusType.STAMINA in actor.sheet.statuses:
                    stamina = actor.sheet.statuses[StatusType.STAMINA].value
                if StatusType.SPIRIT in actor.sheet.statuses:
                    spirit = actor.sheet.statuses[StatusType.SPIRIT].value
            
            status_mod = (stamina + spirit) // 2
            
            # Serendipity Roll (2d6 mapped to -5 to +5)
            die1 = random.randint(1, 6)
            die2 = random.randint(1, 6)
            total = die1 + die2
            table = {2: -5, 3: -4, 4: -3, 5: -2, 6: -1, 7: 0, 8: 1, 9: 2, 10: 3, 11: 4, 12: 5}
            serendipity = table.get(total, 0)
            
            score = swiftness + status_mod + serendipity
            
            results.append({
                'actor': actor,
                'score': score,
                'is_user': isinstance(actor, UserActor)
            })
            
        return results

    def _generate_fallback_narrative(self, actor: Actor) -> str:
        """
        Generate a simple fallback narrative when LLM fails to produce valid output.
        Uses occupation and personality to create believable idle behavior.
        """
        import random
        
        actor_name = actor.sheet.name
        occupation = getattr(actor.sheet, 'occupation', 'person').lower()
        
        # Occupation-based idle behaviors
        occupation_actions = {
            'guard': [
                "shifts weight from one foot to the other, scanning the area",
                "adjusts their belt and checks their surroundings",
                "stands alert, eyes moving methodically across the scene"
            ],
            'merchant': [
                "straightens items on display, brushing off dust",
                "counts something under their breath, lips moving silently",
                "glances at passersby, assessing potential customers"
            ],
            'worker': [
                "wipes their hands on their clothes, taking a brief pause",
                "stretches their back, looking tired but determined",
                "checks their tools, preparing for the next task"
            ],
            'official': [
                "consults a small notebook, frowning slightly",
                "adjusts their collar and surveys the area with practiced authority",
                "makes a note of something, pen scratching quietly"
            ],
            'default': [
                "pauses, lost in thought for a moment",
                "glances around, taking in the surroundings",
                "shifts position, settling into a more comfortable stance",
                "watches the activity nearby with quiet interest",
                "takes a slow breath, seeming to gather their thoughts"
            ]
        }
        
        # Find matching occupation category or use default
        actions = occupation_actions['default']
        for key in occupation_actions:
            if key in occupation:
                actions = occupation_actions[key]
                break
        
        action = random.choice(actions)
        return action

    def _execute_nua_turn(self, actor: Actor, visible_actors: List[Actor], scene_description: str, time_context: Dict, dynamic_context: str = "") -> Dict:
        try:
            # Determine action via Decider, passing dynamic context
            # Append dynamic context to scene description for the decider's view
            effective_scene = scene_description
            if dynamic_context:
                effective_scene += f"\n\n[RECENT EVENTS IN THIS MOMENT]:{dynamic_context}"
                
            # Retry logic for invalid/empty narratives - KEEP TRYING until success
            max_retries = 10  # High limit but not infinite to prevent hangs
            action_data = {}
            narrative = None
            actor_name = actor.sheet.name
            force_fallback = False
            
            for attempt in range(max_retries):
                action_data = self.decider.determine_roam_action(actor, visible_actors, effective_scene, time_context)
                narrative = action_data.get('narrative_description')
                
                # Validate narrative - retry if empty/punctuation-only or too low-signal
                if self._is_valid_roam_narrative(narrative):
                    if attempt > 0:
                        print(f"{Color.SUCCESS}[BG SIM] {actor_name}: Valid narrative on attempt {attempt + 1}{Color.RESET}")
                    break  # Valid narrative, exit retry loop

                # Hard failure case: models sometimes emit ":" (or other punctuation-only tokens).
                # Retrying usually returns the same junk and just spams output, so fall back immediately.
                try:
                    if isinstance(narrative, str):
                        stripped_raw = narrative.strip()
                        if stripped_raw in {":", "-", "--", "..."}:
                            force_fallback = True
                            break
                except Exception:
                    pass

                if narrative:
                    try:
                        metrics = self._roam_narrative_signal_metrics(narrative)
                        preview = str(narrative).replace("\n", " ")
                        if len(preview) > 160:
                            preview = preview[:160] + "..."
                        print(
                            f"{Color.WARNING}[BG SIM] {actor_name}: Invalid narrative on attempt {attempt + 1}, retrying... "
                            f"(len={metrics.get('stripped_len')}, words={metrics.get('word_count')}, alpha={metrics.get('alpha_chars')}) "
                            f"preview='{preview}'{Color.RESET}"
                        )
                    except Exception:
                        print(f"{Color.WARNING}[BG SIM] {actor_name}: Invalid narrative on attempt {attempt + 1}, retrying...{Color.RESET}")
                else:
                    print(f"{Color.WARNING}[BG SIM] {actor_name}: Empty narrative on attempt {attempt + 1}, retrying...{Color.RESET}")
                
                # Small delay between retries to avoid hammering the API
                import time
                time.sleep(0.3)
            else:
                # Only use fallback if we exhausted ALL retries (very rare)
                print(f"{Color.ERROR}[BG SIM] {actor_name}: Failed after {max_retries} attempts, using fallback{Color.RESET}")
                narrative = self._generate_fallback_narrative(actor)
                action_data['narrative_description'] = narrative
                action_data['action_type'] = 'wait'

            if force_fallback:
                print(f"{Color.ERROR}[BG SIM] {actor_name}: Invalid narrative output, using fallback{Color.RESET}")
                narrative = self._generate_fallback_narrative(actor)
                action_data['narrative_description'] = narrative
                action_data['action_type'] = action_data.get('action_type') or 'wait'
            
            # Process result
            action_type = action_data.get('action_type')
            
            # Format output - check if narrative already starts with actor name to avoid duplication
            # NUA ROAM ACTION header in green
            roam_header = f"{Color.SUCCESS}━━━ NUA ROAM ACTION ━━━{Color.RESET}"
            
            if narrative.lower().startswith(actor_name.lower()) or narrative.lower().startswith(actor_name.split()[0].lower()):
                formatted_output = f"{Color.SUCCESS}*{narrative}*{Color.RESET}"
            else:
                formatted_output = f"{Color.SUCCESS}*{actor_name} {narrative}*{Color.RESET}"
            
            if action_type == 'exchange_start':
                # Highlight aggression/initiation
                formatted_output = f"\n{Color.WARNING}⚡ {actor_name.upper()} INITIATES ACTION!{Color.RESET}\n{formatted_output}"
                roam_header = f"{Color.WARNING}━━━ NUA ROAM ACTION (INITIATING) ━━━{Color.RESET}"
            elif action_type == 'movement':
                # NUA explicitly chose movement action
                roam_header = f"{Color.SUCCESS}━━━ NUA MOVEMENT ━━━{Color.RESET}"
            elif action_type == 'depart_location':
                # NUA is leaving the location - use green for departure
                roam_header = f"{Color.SUCCESS}━━━ NUA DEPARTURE ━━━{Color.RESET}"
                formatted_output = f"{Color.SUCCESS}*{actor_name} {narrative}*{Color.RESET}"
            
            # ALWAYS check for movement in narrative (NUAs often move as part of other actions)
            # e.g., "walks to the counter and examines the goods" should update position
            try:
                from agents.architect_agent import move_actor_on_map, extract_movement_from_narrative
                
                # Extract movement target from narrative
                movement_target = extract_movement_from_narrative(narrative)
                
                if movement_target or action_type == 'movement':
                    target = movement_target or action_data.get('target')

                    # Never use the full narrative as a movement target. This causes bogus moves like
                    # "moved to 'throb slightly as she focuses...'".
                    if not target:
                        target = None

                    # Basic sanity filter: discard obviously non-target text
                    if isinstance(target, str):
                        t = target.strip()
                        if (not t) or (len(t) > 80) or ("\n" in t):
                            target = None
                        else:
                            target = t

                if target:
                    
                    # Use unified movement helper
                    moved = move_actor_on_map(
                        actor_name=actor_name,
                        movement_target=target,
                        narrative=narrative
                    )
                    
                    if moved:
                        print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} NUA '{actor_name}' moved to '{target}'")
            except Exception as move_e:
                pass  # Movement is enhancement, not critical
            
            print(f"\n{roam_header}")
            print(f"{formatted_output}")
            
            # Save to context
            if self.narrative_context_manager:
                from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
                
                # Construct context string
                context_info = f"Roam action at {time_context.get('formatted_time', 'unknown')}"
                
                self.narrative_context_manager.add_narrative_event(
                    event_type=NarrativeEventType.ACTION_SEQUENCE,
                    narrative_text=f"{actor.sheet.name}: {narrative}",
                    actors_involved=[actor.sheet.name],
                    importance=NarrativeImportance.ROUTINE,
                    emotional_tone="neutral",
                    scene_context=context_info
                )
            
            # CRITICAL: Update scene description with NUA action for consistency
            # This ensures ALL outputs (perceptual, internal voice, etc.) see what NUAs are doing
            if self.tracker:
                try:
                    current_scene = self.tracker.get_current_scene() or {}
                    scene_desc = current_scene.get('scene_description') if isinstance(current_scene, dict) else str(current_scene)
                    scene_desc = scene_desc or ""

                    # Format NUA action as observable behavior — one sentence only
                    _narr_raw = narrative.lower() if not narrative.lower().startswith(actor_name.lower()) else narrative
                    # Trim to first sentence so the Perception block stays concise
                    _first_sentence = _narr_raw.split('.')[0].strip()
                    if _first_sentence:
                        _narr_raw = _first_sentence + '.'
                    nua_action_line = f"\n[Nearby: {actor_name} {_narr_raw}]"

                    # Append to scene if not already present (avoid duplicates)
                    if nua_action_line.strip() and (nua_action_line.strip() not in scene_desc):
                        updated_scene = scene_desc + nua_action_line
                        self.tracker.set_current_scene(updated_scene)
                except Exception as scene_e:
                    pass  # Silently fail - scene update is enhancement, not critical
            
            # Also save to tracker for action history (prevents repetition)
            if self.tracker:
                try:
                    actor_id = f"actor_{actor.sheet.name.lower().replace(' ', '_')}"
                    self.tracker.record_roam_action(
                        actor_id=actor_id,
                        action_data={
                            "narrative_description": narrative,
                            "action_type": action_type,
                            "target": action_data.get('target'),
                            "dialogue": action_data.get('dialogue'),
                            "time": time_context.get('formatted_time', 'unknown') if time_context else 'unknown'
                        }
                    )
                except Exception as track_e:
                    print(f"{Color.WARNING}[BG SIM] Could not record action to tracker: {track_e}{Color.RESET}")

            # CRITICAL: Update NPC goal/task system (mirror UA action processing)
            # This ensures NPC background actions properly update their goals and tasks
            try:
                if hasattr(actor, 'goal_task_manager') and actor.goal_task_manager:
                    # Update tasks based on the action performed
                    actor.goal_task_manager.update_goal(
                        action_taken=narrative,
                        outcome="success",  # Background actions are assumed successful
                        context=f"Roam action: {action_type}"
                    )
                    print(f"{Color.CYAN}[GOAL/TASK] Updated {actor.sheet.name}'s goals/tasks from roam action{Color.RESET}")
                elif hasattr(self, 'interpreter') and self.interpreter and hasattr(self.interpreter, 'update_actor_tasks'):
                    # Fallback: use interpreter's task update system if available
                    self.interpreter.update_actor_tasks(
                        user_action=narrative,
                        actor=actor,
                        action_interpretation=action_data
                    )
                    print(f"{Color.CYAN}[GOAL/TASK] Updated {actor.sheet.name}'s tasks via interpreter{Color.RESET}")
            except Exception as goal_e:
                # Non-critical: goal/task updates are enhancement, don't break simulation
                pass

            return action_data
        except Exception as e:
            print(f"{Color.WARNING}[BG SIM] Error executing turn for {actor.sheet.name}: {e}{Color.RESET}")
            return {}

    def get_recent_world_events_context(self, max_events: int = 5) -> str:
        """Get recent world events as context string for LLM prompts."""
        if not self.recent_events:
            return ""
        
        events_text = []
        for event in self.recent_events[-max_events:]:
            events_text.append(f"- [{event.event_type.value}] {event.narrative[:150]}")
        
        return "\n".join(events_text)

    def extract_potential_inuas_from_scene(self, scene_description: str) -> List[Dict[str, str]]:
        """
        Extract potential INUA hazards from a scene description using RAG.
        Returns list of dicts with 'name', 'context', and 'hazard_potential' keys.
        
        Uses the worldbuilding RAG system to get location-appropriate hazards
        instead of hardcoded keywords.
        """
        potential_inuas = []
        
        # Try to use RAG for context-aware hazard identification
        if self.decider and hasattr(self.decider, 'rag_system') and self.decider.rag_system:
            try:
                from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
                
                # Query RAG for hazards relevant to this scene
                rag_results = self.decider.rag_system.search(
                    query=f"environmental hazards dangers {scene_description[:200]}",
                    category_filter=WorldbuildingCategory.ENVIRONMENTAL_HAZARDS,
                    top_k=2
                )
                
                if rag_results:
                    # Use LLM to extract specific hazards from scene based on RAG context
                    hazard_context = "\n".join([doc.content[:500] for doc, _ in rag_results])
                    potential_inuas = self._extract_hazards_with_llm(scene_description, hazard_context)
                    
            except Exception as e:
                print(f"{Color.WARNING}[BG SIM] RAG hazard extraction failed: {e}{Color.RESET}")
        
        # Fallback to basic keyword extraction if RAG fails
        if not potential_inuas:
            potential_inuas = self._extract_hazards_basic(scene_description)
        
        return potential_inuas

    def _extract_hazards_with_llm(self, scene_description: str, hazard_context: str) -> List[Dict[str, str]]:
        """Use LLM to identify specific hazards in scene based on RAG context."""
        if not self.narrator:
            return self._extract_hazards_basic(scene_description)
        
        try:
            prompt = f"""Identify 1-3 potential environmental hazards in this scene.

SCENE:
{scene_description[:500]}

HAZARD REFERENCE (from worldbuilding):
{hazard_context[:800]}

For each hazard found, provide:
- name: The specific hazard (e.g., "Crane", "Storm Waves", "Exposed Wiring")
- context: Brief description of how it appears in the scene
- hazard_potential: low/medium/high

Respond in JSON format:
[{{"name": "...", "context": "...", "hazard_potential": "..."}}]

If no hazards are present, respond with: []"""

            response = self.narrator._call_llm(prompt)
            if response:
                import json
                # Try to parse JSON from response
                response = response.strip()
                if response.startswith('['):
                    hazards = json.loads(response)
                    return hazards[:3]  # Limit to 3
        except Exception as e:
            print(f"{Color.WARNING}[BG SIM] LLM hazard extraction failed: {e}{Color.RESET}")
        
        return []

    def _extract_hazards_basic(self, scene_description: str) -> List[Dict[str, str]]:
        """Basic keyword-based hazard extraction as fallback."""
        # Minimal keyword set - RAG should be primary source
        basic_keywords = [
            'crane', 'machinery', 'generator', 'scaffolding', 'ladder',
            'cable', 'pipe', 'wave', 'storm', 'fire', 'vehicle'
        ]
        
        potential_inuas = []
        scene_lower = scene_description.lower()
        
        for keyword in basic_keywords:
            if keyword in scene_lower:
                idx = scene_lower.find(keyword)
                start = max(0, idx - 30)
                end = min(len(scene_description), idx + len(keyword) + 30)
                context = scene_description[start:end].strip()
                
                potential_inuas.append({
                    'name': keyword.title(),
                    'context': context,
                    'hazard_potential': 'medium'
                })
        
        return potential_inuas[:5]

    def create_virtual_inuas_from_scene(self, scene_description: str) -> List[Dict[str, Any]]:
        """
        Create virtual INUA representations from scene description for hazard events.
        These don't need full Actor objects - just enough info for hazard generation.
        """
        potential = self.extract_potential_inuas_from_scene(scene_description)
        
        virtual_inuas = []
        for p in potential[:5]:  # Limit to 5 potential hazards
            virtual_inuas.append({
                'name': p['name'],
                'context': p.get('context', ''),
                'hazard_potential': p.get('hazard_potential', 'medium'),
                'is_virtual': True  # Flag to indicate this isn't a full Actor
            })
        
        return virtual_inuas
    
    def get_hazard_narrative_context(self) -> str:
        """Get RAG context for hazard narrative generation."""
        if not self.decider or not hasattr(self.decider, 'rag_system') or not self.decider.rag_system:
            return ""
        
        try:
            from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
            
            results = self.decider.rag_system.search(
                query="hazard event narrative style perceptual description",
                category_filter=WorldbuildingCategory.ENVIRONMENTAL_HAZARDS,
                top_k=1
            )
            
            if results:
                return results[0][0].content[:600]
        except Exception:
            pass
        
        return ""
    
    def get_nua_interaction_context(self) -> str:
        """Get RAG context for NUA interaction narrative generation."""
        if not self.decider or not hasattr(self.decider, 'rag_system') or not self.decider.rag_system:
            return ""
        
        try:
            from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
            
            results = self.decider.rag_system.search(
                query="NUA interaction patterns friendly hostile neutral observation",
                category_filter=WorldbuildingCategory.WORLD_EVENTS,
                top_k=1
            )
            
            if results:
                return results[0][0].content[:600]
        except Exception:
            pass
        
        return ""
