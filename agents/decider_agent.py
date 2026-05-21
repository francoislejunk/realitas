import json
import hashlib
from typing import TYPE_CHECKING, Dict, Any, Optional
from openrouter_config import create_role_client, OpenRouterConfig, retry_with_backoff, RetryConfig, robust_llm_call
from logbook.utas_logger import UTASLogger
from color_utils import Color
from json_utils import extract_and_parse_json
from numeric_utils import extract_numeric_value
from schemas.utas_action import validate_action_data
from dialogue_context_system import dialogue_context_system
from sympathy_behavior_modifier import sympathy_behavior_modifier
from tactical_awareness_system import tactical_awareness_system
from ally_coordination_system import ally_coordinator
from npc_memory_system import get_nua_memory_system

try:
    from context_store import ContextStore
except Exception:
    ContextStore = None

try:
    from spatial_context_system import get_spatial_manager
except Exception:
    get_spatial_manager = None

try:
    from master_time_coordinator import get_master_time_coordinator
except Exception:
    get_master_time_coordinator = None

try:
    from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
except Exception:
    WorldbuildingCategory = None

if TYPE_CHECKING:
    from actors import Actor

class DeciderAgent:
    """
    The Decider Agent, responsible for determining Non-User Actor (NUA)
    and Inanimate Non-User Actor (INUA) actions and reactions in the simulation.
    """

    def __init__(self, logger: 'UTASLogger', scene_description: str, tracker_agent=None, rag_system=None, narrative_context_manager=None):
        self.logger = logger
        self.scene_description = scene_description
        self.tracker_agent = tracker_agent
        self.rag_system = rag_system  # RAG system for worldbuilding context
        self.narrative_context_manager = narrative_context_manager  # For concrete details
        self.response_cache = {}  # Cache for LLM responses
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Initialize OpenRouter client
        self.client = create_role_client("decision")
        self.model = OpenRouterConfig.get_model_for_role("decision")
        
        if not tracker_agent:
            self.logger.log_system("WARNING: DeciderAgent initialized without TrackerAgent. Historical context will be unavailable.")

    def _get_actor_category_label(self, actor: 'Actor') -> str:
        """Best-effort actor category label for prompts (UA/NUA/MNUA/INUA)."""
        try:
            if getattr(actor, 'is_user_actor', False):
                return "UA"
            # NonUserActor exposes .category property in actors.py
            cat = getattr(actor, 'category', None)
            if cat is not None:
                return str(getattr(cat, 'name', cat)).upper()
            if getattr(actor, 'is_mnua', False):
                return "MNUA"
        except Exception:
            pass
        return "NUA"
    
    def _get_worldbuilding_context(self, query: str, max_tokens: int = 300, category_filter: Optional[Any] = None) -> str:
        """Get worldbuilding context from RAG system for NPC decision-making."""
        if not self.rag_system:
            return ""
        
        try:
            context = self.rag_system.get_context_for_llm(
                query=query,
                max_tokens=max_tokens,
                category_filter=category_filter
            )
            return context if context else ""
        except Exception as e:
            self.logger.log_system(f"Error getting RAG context for DeciderAgent: {e}")
            return ""

    def _get_context_store(self) -> Optional['ContextStore']:
        if ContextStore is None:
            return None
        try:
            from pathlib import Path
            return ContextStore(Path("simulation_data/context/context.db"))
        except Exception:
            return None

    def _get_current_location_id(self) -> Optional[str]:
        try:
            if get_spatial_manager is None:
                return None
            spatial = get_spatial_manager()
            return getattr(spatial, 'current_location', None)
        except Exception:
            return None

    def _get_current_session_id(self) -> str:
        try:
            if get_spatial_manager is None:
                return "default"
            spatial = get_spatial_manager()
            sid = getattr(spatial, 'session_id', None)
            return sid or "default"
        except Exception:
            return "default"

    def _try_resolve_spatial_actor_id(self, actor: 'Actor') -> Optional[str]:
        """Best-effort mapping from Actor to spatial_context_system actor_id."""
        try:
            if get_spatial_manager is None:
                return None
            spatial = get_spatial_manager()
            ctx = spatial.get_current_context() if spatial else None
            if not ctx or not getattr(ctx, 'actor_positions', None):
                return None
            actor_name = getattr(getattr(actor, 'sheet', None), 'name', None) or getattr(actor, 'name', None)
            if not actor_name:
                return None
            for aid, apos in ctx.actor_positions.items():
                if getattr(apos, 'actor_name', None) == actor_name:
                    return aid
            return None
        except Exception:
            return None

    def _format_recent_events_for_prompt(self, events: list, max_lines: int = 10) -> str:
        if not events:
            return ""
        lines = []
        for e in events[:max_lines]:
            wt = ""
            try:
                if e.get('world_day') is not None and e.get('world_hour') is not None and e.get('world_minute') is not None:
                    wt = f"[Day {e['world_day']} {int(e['world_hour']):02d}:{int(e['world_minute']):02d}] "
            except Exception:
                wt = ""
            summary = e.get('summary') or e.get('event_type')
            lines.append(f"- {wt}{summary}")
        return "\n".join(lines)

    def _get_current_world_time(self) -> Optional[Any]:
        try:
            if get_master_time_coordinator is None:
                return None
            tc = get_master_time_coordinator()
            time_ctx = tc.get_current_time_context() if tc else None
            return time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
        except Exception:
            return None

    def _get_actor_long_term_memory_section(self, actor: 'Actor', limit: int = 8) -> str:
        store = self._get_context_store()
        if store is None:
            return ""

        session_id = self._get_current_session_id()
        actor_id = self._try_resolve_spatial_actor_id(actor)
        if not actor_id:
            return ""

        gt = self._get_current_world_time()
        world_time = None
        try:
            if gt is not None:
                # WorldTime type lives in context_store; avoid hard dependency here
                from context_store import WorldTime
                world_time = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
        except Exception:
            world_time = None

        try:
            memories = store.recall(
                session_id=session_id,
                actor_id=actor_id,
                query=None,
                limit=limit,
                world_time=world_time
            )
        except Exception:
            memories = []

        if not memories:
            return ""

        lines = ["**LONG-TERM MEMORY (decayed, actor-subjective):**"]
        for m in memories:
            mtype = m.get('memory_type') or "memory"
            content = m.get('content') or ""
            lines.append(f"- [{mtype}] {content}")
        return "\n".join(lines) + "\n"

    def _format_position_snapshot_for_prompt(self, snapshot: list, max_lines: int = 20) -> str:
        if not snapshot:
            return ""

        actors = [s for s in snapshot if s.get('entity_type') == 'actor']
        obstacles = [s for s in snapshot if s.get('entity_type') == 'obstacle']

        lines = []
        if actors:
            lines.append("**Actors (latest known positions):**")
            for s in actors[:max_lines]:
                name = s.get('entity_name') or s.get('entity_id')
                x = s.get('x')
                y = s.get('y')
                active = s.get('is_active')
                if x is None or y is None:
                    continue
                act_str = "active" if active else "inactive"
                lines.append(f"- {name}: ({float(x):.0f}, {float(y):.0f}) [{act_str}]")

        if obstacles:
            lines.append("**Key obstacles (centroid):**")
            for s in obstacles[:10]:
                name = s.get('entity_name') or s.get('entity_id')
                x = s.get('x')
                y = s.get('y')
                if x is None or y is None:
                    continue
                lines.append(f"- {name}: ({float(x):.0f}, {float(y):.0f})")

        return "\n".join(lines)

    def _get_persistent_context_section(self, actor: 'Actor', max_event_lines: int = 10) -> str:
        store = self._get_context_store()
        if store is None:
            return ""

        session_id = self._get_current_session_id()
        location_id = self._get_current_location_id()
        if not location_id:
            return ""

        try:
            recent = store.get_recent_world_events(
                session_id=session_id,
                location_id=location_id,
                limit=25
            )
        except Exception:
            recent = []

        # Actor-relevant slice (best-effort): prefer stable actor_id from spatial context
        actor_id = self._try_resolve_spatial_actor_id(actor)
        actor_name = getattr(getattr(actor, 'sheet', None), 'name', None) or getattr(actor, 'name', None)
        relevant = []
        if (actor_id or actor_name) and recent:
            try:
                for e in recent:
                    payload = e.get('payload') or {}
                    actor_ids = payload.get('actor_ids') if isinstance(payload.get('actor_ids'), list) else []
                    if actor_id and actor_ids and actor_id in actor_ids:
                        relevant.append(e)
                        continue
                    if actor_id and payload.get('actor_id') == actor_id:
                        relevant.append(e)
                        continue
                    if actor_name and payload.get('actor_name') == actor_name:
                        relevant.append(e)
            except Exception:
                relevant = []

        try:
            snapshot = store.get_latest_position_snapshot(
                session_id=session_id,
                location_id=location_id,
                limit_entities=250
            )
        except Exception:
            snapshot = []

        recent_txt = self._format_recent_events_for_prompt(recent, max_lines=max_event_lines)
        relevant_txt = self._format_recent_events_for_prompt(relevant, max_lines=min(5, max_event_lines))
        pos_txt = self._format_position_snapshot_for_prompt(snapshot, max_lines=20)

        if not (recent_txt or relevant_txt or pos_txt):
            return ""

        parts = ["**PERSISTENT CONTEXT (from simulation history DB):**"]
        if recent_txt:
            parts.append("**Recent events in this location:**")
            parts.append(recent_txt)
        if relevant_txt:
            parts.append("**Events directly involving this actor (best-effort):**")
            parts.append(relevant_txt)
        if pos_txt:
            parts.append("**Current location snapshot (best-effort):**")
            parts.append(pos_txt)
        return "\n".join(parts) + "\n"
        
    def _get_actor_occupation_category(self, actor: 'Actor') -> Optional[Any]:
        if not WorldbuildingCategory:
            return None
        label = self._get_actor_category_label(actor)
        if label == "UA":
            return WorldbuildingCategory.UA_OCCUPATIONS
        if label == "MNUA":
            return WorldbuildingCategory.MNUA_OCCUPATIONS
        return WorldbuildingCategory.NUA_OCCUPATIONS

    def _get_actor_goals_category(self, actor: 'Actor') -> Optional[Any]:
        if not WorldbuildingCategory:
            return None
        label = self._get_actor_category_label(actor)
        if label == "UA":
            return WorldbuildingCategory.UA_GOALS
        if label == "MNUA":
            return WorldbuildingCategory.MNUA_GOALS
        return WorldbuildingCategory.NUA_GOALS

    def _get_actor_relationship_matrices_category(self, actor: 'Actor') -> Optional[Any]:
        if not WorldbuildingCategory:
            return None
        label = self._get_actor_category_label(actor)
        if label == "MNUA":
            return getattr(WorldbuildingCategory, 'MNUA_RELATIONSHIP_MATRICES', None)
        return getattr(WorldbuildingCategory, 'NUA_RELATIONSHIP_MATRICES', None)

    def _get_relationship_dynamics_context(self, actor: 'Actor', query: str, max_tokens: int = 250) -> str:
        if not self.rag_system or not WorldbuildingCategory:
            return ""
        parts = []
        try:
            rel = ""
            rel_cat = self._get_actor_relationship_matrices_category(actor)
            if rel_cat is not None:
                rel = self._get_worldbuilding_context(
                    query=query,
                    max_tokens=max_tokens,
                    category_filter=rel_cat
                )
            if not rel:
                rel = self._get_worldbuilding_context(
                    query=query,
                    max_tokens=max_tokens,
                    category_filter=WorldbuildingCategory.RELATIONSHIP_MATRICES
                )
            if rel:
                parts.append(rel)
        except Exception:
            pass

        try:
            factions = self._get_worldbuilding_context(
                query=query,
                max_tokens=max_tokens,
                category_filter=WorldbuildingCategory.FACTIONS_ORGANIZATIONS
            )
            if factions:
                parts.append(factions)
        except Exception:
            pass

        if not parts:
            return ""
        return f"""**FACTION & RELATIONSHIP DYNAMICS (use to interpret alliances/hostility):**
{chr(10).join(parts)}
"""

    def _get_narrative_format_instruction(self, context_guidance: Optional[Dict], reactor: 'Actor') -> str:
        """Generate narrative format instruction based on encounter type."""
        is_remote = context_guidance and context_guidance.get('is_remote_encounter', False)
        
        if is_remote:
            # PHONE CALL - ONLY dialogue allowed
            return """MANDATORY FORMAT FOR PHONE CALLS - NO EXCEPTIONS:
            'says "[exact quoted dialogue]" in a [tone] voice'
            
            YOU MUST USE THIS EXACT FORMAT. Examples:
            - 'says "Hey, I was thinking about that project we discussed" in a thoughtful voice'
            - 'says "I'd love to help you with that!" in an enthusiastic voice'
            - 'says "Can we meet up later to talk?" in a casual voice'
            
            FORBIDDEN: Do NOT include ANY physical actions, gestures, or movements. They cannot see you."""
        else:
            # IN-PERSON - dialogue with physical actions allowed
            reactor_name = reactor.sheet.name if reactor else "the target"
            return f"""Format for narrative_description:
            
            FOR SOCIAL/CONVERSATIONAL ACTIONS (talking, persuading, greeting, etc.):
            - MUST include quoted dialogue: 'says "[exact words]" while [physical action/expression]'
            - Example: 'says "Hey, you got a minute?" while approaching {reactor_name} with a friendly smile'
            - Example: 'says "Back off!" while stepping forward aggressively'
            
            FOR NON-DIALOGUE ACTIONS (combat, movement, etc.):
            - 'attempts to lunge at {reactor_name} with a dagger'
            - 'tries to dodge {reactor_name}'s incoming strike'
            
            NEVER describe outcomes, results, or consequences - only the attempt."""
    
    def _refresh_scene_from_tracker(self) -> None:
        """Update self.scene_description from TrackerAgent if available."""
        try:
            if getattr(self, 'tracker_agent', None):
                latest = self.tracker_agent.get_current_scene() or {}
                latest_desc = latest.get('scene_description')
                if latest_desc:
                    self.scene_description = latest_desc
        except Exception:
            # Non-fatal: keep current scene_description
            pass

    def _get_historical_context(self, lookback_turns: int = 10) -> str:
        """Get recent turn history for NUA decision context."""
        if not self.tracker_agent:
            return "\n**No historical context available**\n"
        
        try:
            context = self.tracker_agent.get_context_for_llm(lookback_turns)
            if context.strip():
                return f"\n**Recent Turn History:**\n{context}\n"
            else:
                return "\n**No previous turns recorded**\n"
        except Exception as e:
            self.logger.log_system(f"Error getting historical context: {e}")
            return "\n**Historical context unavailable**\n"
    
    def _get_concrete_details_context(self, actor_names: list = None) -> str:
        """Get concrete details for NPCs to maintain consistency."""
        if not self.narrative_context_manager:
            return ""
        
        try:
            # Get concrete details from the detail tracker
            if hasattr(self.narrative_context_manager, 'detail_tracker'):
                detail_tracker = self.narrative_context_manager.detail_tracker
                context_parts = []
                
                # Get details for specified actors
                if actor_names:
                    for actor_name in actor_names:
                        details = detail_tracker.get_details_for_owner(actor_name)
                        if details:
                            context_parts.append(f"\n**ESTABLISHED DETAILS FOR {actor_name.upper()}:**")
                            context_parts.append("(NPCs must reference these consistently)")
                            for detail in details[:5]:  # Limit to top 5
                                context_parts.append(f"- {detail.category.value}: {detail.detail_text}")
                
                if context_parts:
                    return "\n".join(context_parts) + "\n"
            
            return ""
        except Exception as e:
            self.logger.log_system(f"Error getting concrete details: {e}")
            return ""
    
    def _get_recent_nua_actions(self, actor_name: str, lookback_turns: int = 10) -> str:
        """Get ALL historical actions by this specific NUA to prevent repetition."""
        if not self.tracker_agent:
            return "No action history available - be creative and varied!"
        
        try:
            try:
                if hasattr(self.tracker_agent, 'resolve_actor_id'):
                    actor_id = self.tracker_agent.resolve_actor_id(actor_name)
                elif hasattr(self.tracker_agent, 'make_actor_id'):
                    actor_id = self.tracker_agent.make_actor_id(actor_name)
                else:
                    actor_id = f"actor_{actor_name.lower().replace(' ', '_')}"
            except Exception:
                actor_id = f"actor_{actor_name.lower().replace(' ', '_')}"
            historical_actions = []
            
            # First, check ROAM action history (standalone actions)
            if hasattr(self.tracker_agent, 'get_roam_action_history'):
                roam_actions = self.tracker_agent.get_roam_action_history(actor_id, limit=lookback_turns)
                for action in roam_actions:
                    action_data = action.get('action_data', {})
                    narrative = action_data.get('narrative_description', '')
                    if narrative:
                        # Truncate long narratives
                        if len(narrative) > 150:
                            narrative = narrative[:150] + "..."
                        historical_actions.append(f"- [ROAM] {narrative}")
            
            # Also check exchange-based history
            all_actions = self.tracker_agent.get_actor_history(actor_id)
            
            # Debug logging
            self.logger.log_system(f"DEBUG: Looking for actor_id: {actor_id}")
            self.logger.log_system(f"DEBUG: Found {len(all_actions)} exchange actions, {len(historical_actions)} roam actions for {actor_name}")
            
            for i, turn_data in enumerate(all_actions[-lookback_turns:]):  # Limit to recent
                role = turn_data.get("role", "unknown")
                turn_info = turn_data.get("turn_data", {})
                
                # Check multiple possible data structures
                action_desc = None
                if role == "proactor":
                    # Try different possible data locations
                    if turn_info.get("step1_proactor_interpretation"):
                        step1_data = turn_info["step1_proactor_interpretation"]
                        if "normalized_output" in step1_data:
                            action_desc = step1_data["normalized_output"].get("action_description", "Unknown action")
                        elif "input_data" in step1_data:
                            action_desc = step1_data["input_data"].get("narrative_description", "Unknown action")
                    
                    # Fallback: look for any action description in the turn data
                    if not action_desc:
                        for key, value in turn_info.items():
                            if isinstance(value, dict):
                                if "action_description" in value:
                                    action_desc = value["action_description"]
                                    break
                                elif "narrative_description" in value:
                                    action_desc = value["narrative_description"]
                                    break
                    
                    if action_desc:
                        # Truncate long narratives
                        if len(action_desc) > 150:
                            action_desc = action_desc[:150] + "..."
                        historical_actions.append(f"- [EXCHANGE] {action_desc}")
            
            if historical_actions:
                return f"**RECENT ACTIONS BY {actor_name.upper()} (AVOID REPEATING):**\n" + "\n".join(historical_actions[-10:]) + "\n\n**Create something NEW and DIFFERENT from the above!**"
            else:
                return f"No historical actions found for {actor_name} - be creative and authentic!"
                
        except Exception as e:
            self.logger.log_system(f"Error getting recent NUA actions: {e}")
            return "Action history unavailable - focus on character authenticity!"

    def _build_last_exchange_context_section(self, last_exchange_context: Dict[str, Any], proactor_name: str, reactor_name: str) -> str:
        """Build a rich context section from the last exchange to inform the next action."""
        if not last_exchange_context:
            return ""
        
        try:
            # Extract key information from last exchange
            last_proactor = last_exchange_context.get('proactor_name', 'Unknown')
            last_reactor = last_exchange_context.get('reactor_name', 'Unknown')
            proactor_action = last_exchange_context.get('proactor_action', 'acted')
            reactor_action = last_exchange_context.get('reactor_action', 'reacted')
            outcome_narrative = last_exchange_context.get('outcome_narrative', '')
            winner = last_exchange_context.get('winner', 'unknown')
            status_shifts = last_exchange_context.get('status_shifts', [])
            
            # Extract dialogue if available
            proactor_dialogue = ""
            reactor_dialogue = ""
            try:
                # Try to extract quoted dialogue from actions
                import re
                proactor_quotes = re.findall(r'"([^"]*)"', str(proactor_action))
                reactor_quotes = re.findall(r'"([^"]*)"', str(reactor_action))
                if proactor_quotes:
                    proactor_dialogue = f'\n    - **What {last_proactor} said:** "{proactor_quotes[-1]}"'
                if reactor_quotes:
                    reactor_dialogue = f'\n    - **What {last_reactor} said:** "{reactor_quotes[-1]}"'
            except Exception:
                pass
            
            # Build a narrative summary with Step 6 outcome as primary context
            context_text = f"""**🔄 LAST EXCHANGE CONTEXT (CRITICAL FOR CONTINUITY):**
    
    **📖 WHAT THE PLAYER JUST EXPERIENCED (Step 6 Narrative):**
    {outcome_narrative if outcome_narrative else 'No narrative available'}
    
    **📋 Exchange Details:**
    - **{last_proactor}'s Action:** {proactor_action}{proactor_dialogue}
    - **{last_reactor}'s Response:** {reactor_action}{reactor_dialogue}
    - **Winner:** {winner}
    """
            
            # Add status shift information if available
            if status_shifts:
                context_text += "\n    **Status Changes:**\n"
                for shift in status_shifts:
                    actor = shift.get('actor_name', 'Unknown')
                    status = shift.get('status_name', 'STATUS')
                    magnitude = shift.get('magnitude_descriptor', 'UNKNOWN')
                    polarity = shift.get('polarity', 'UNKNOWN')
                    context_text += f"    - {actor} experienced a {magnitude} {polarity} to {status}\n"
            
            # Add guidance for continuity
            context_text += f"""
    **⚠️ CONTINUITY REQUIREMENTS:**
    - Your action MUST acknowledge and build upon what just happened
    - If dialogue was exchanged, CONTINUE THAT CONVERSATION TOPIC
    - DO NOT change the subject or ignore what was just said
    - If a question was asked, address it (answer, deflect, or ask for clarification)
    - If a statement was made, respond to that specific topic
    - React to the emotional/physical state changes from the last exchange
    - If you were involved in the last exchange, your action should feel like a natural continuation
    - If {proactor_name} was the winner, they may feel confident; if they lost, they may feel frustrated/hurt
    - Consider the immediate aftermath: Are they catching their breath? Regaining composure? Pressing advantage?

    **🚨 ADVANCE THE SCENE (NO REPETITION):**
    - Your next action MUST move the exchange FORWARD by one beat (a new line, new ask, new boundary, new offer, new consequence)
    - DO NOT restate the Step 6 narrative
    - DO NOT repeat the last line of dialogue verbatim
    - If you already answered/deflected a question, you must now build on that answer (e.g., ask a follow-up, set a boundary, offer terms, change posture, or end the exchange)
    - If the other person asked a question and it was NOT yet answered, answer/deflect FIRST, then continue
    
    🚨 **CRITICAL: DO NOT IGNORE OR CHANGE THE TOPIC OF THE CONVERSATION** 🚨
    """
            
            return context_text
            
        except Exception as e:
            self.logger.log_system(f"Error building last exchange context: {e}")
            return ""

    def _call_llm_for_json(self, prompt: str, max_retries: int = 5) -> Optional[Dict[str, Any]]:
        """Calls the OpenRouter LLM and attempts to parse the response as JSON with retries."""
        try:
            from persistent_context_manager import get_context_manager
            cm = get_context_manager()
            if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                facts_block = cm.get_continuity_facts_for_llm(max_facts=8) or ""
                if facts_block and isinstance(prompt, str) and prompt.strip():
                    prompt = f"{facts_block}\n\n{prompt}"
        except Exception:
            pass
        # Check if the prompt is in the cache
        prompt_hash = hashlib.sha256(prompt.encode()).hexdigest()
        if prompt_hash in self.response_cache:
            self.cache_hits += 1
            return self.response_cache[prompt_hash]
        
        self.cache_misses += 1
        
        last_response = None
        
        for attempt in range(max_retries):
            try:
                response = retry_with_backoff(
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7 + (attempt * 0.05)  # Slightly increase temp on retries
                    )
                )
                response_text = response.choices[0].message.content
                last_response = response_text
                result = extract_and_parse_json(response_text)
                
                if result is not None:
                    self.response_cache[prompt_hash] = result
                    return result
                
                # JSON parsing failed, retry
                if attempt < max_retries - 1:
                    print(f"{Color.WARNING}⚠️ JSON parse failed (attempt {attempt + 1}/{max_retries}), retrying...{Color.RESET}")
                    import time
                    time.sleep(0.5 * (attempt + 1))
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"{Color.WARNING}⚠️ LLM call failed (attempt {attempt + 1}/{max_retries}): {e}, retrying...{Color.RESET}")
                    import time
                    time.sleep(1.0 * (attempt + 1))
        
        # All retries exhausted
        raw_response = last_response if last_response else 'No response data'
        error_message = f"JSONDecodeError after {max_retries} attempts\nRaw Response:\n{raw_response}"
        self.logger.log_system(f"ERROR: {error_message}")
        return None

    def determine_roam_action(self, proactor: 'Actor', visible_actors: list, scene_description: str, time_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Determines an autonomous action for an NUA in ROAM mode.
        The NUA can interact, move, wait, or perform tasks.
        """
        self._refresh_scene_from_tracker()
        self.time_context = time_context
        
        # Build actor summary with relationship context
        visible_actors_info = []
        relationship_context = ""
        for a in visible_actors:
            if a != proactor:
                actor_info = f"{a.sheet.name} ({a.sheet.occupation})"
                visible_actors_info.append(actor_info)
                
                # Get sympathy/relationship toward this actor
                try:
                    sympathy_value = proactor.sheet.get_sympathy(a.sheet.name)
                    if sympathy_value != 0:
                        relationship_context += f"- Feelings toward {a.sheet.name}: {sympathy_value} "
                        if sympathy_value >= 3:
                            relationship_context += "(friendly, trusting)\n"
                        elif sympathy_value >= 1:
                            relationship_context += "(positive, approachable)\n"
                        elif sympathy_value <= -3:
                            relationship_context += "(hostile, distrustful)\n"
                        elif sympathy_value <= -1:
                            relationship_context += "(wary, cautious)\n"
                        else:
                            relationship_context += "(neutral)\n"
                except Exception:
                    pass
                    
                # Get dialogue history with this actor
                if dialogue_context_system.has_conversation_history(proactor.sheet.name, a.sheet.name):
                    recent_dialogue = dialogue_context_system.get_dialogue_context(proactor.sheet.name, a.sheet.name)
                    if recent_dialogue:
                        relationship_context += f"- Recent conversation with {a.sheet.name}: {recent_dialogue[:200]}...\n"
        
        visible_actors_str = ", ".join(visible_actors_info) if visible_actors_info else "None"
            
        # Get recent history
        recent_actions = self._get_recent_nua_actions(proactor.sheet.name)
        
        # Get memory context
        from npc_memory_system import get_nua_memory_system
        nua_memory_system = get_nua_memory_system()
        memory_context = ""
        if nua_memory_system:
             memory_context = nua_memory_system.get_memory_context_for_decision(proactor.sheet.name, "general")

        # Get worldbuilding context from RAG for occupation-appropriate behavior
        # CRITICAL: Include technology and era keywords to ensure period-appropriate actions
        worldbuilding_context = ""
        if self.rag_system:
            goals_hint = ""
            try:
                if hasattr(proactor.sheet, 'goals') and proactor.sheet.goals:
                    goals_hint = " ".join([str(g) for g in proactor.sheet.goals[:3] if g])
            except Exception:
                goals_hint = ""
            occupation_guidance = self._get_worldbuilding_context(
                query=f"{proactor.sheet.occupation} occupations social role",
                max_tokens=250,
                category_filter=self._get_actor_occupation_category(proactor)
            )
            goals_guidance = self._get_worldbuilding_context(
                query=f"{goals_hint} goals motivation",
                max_tokens=250,
                category_filter=self._get_actor_goals_category(proactor)
            )
            worldbuilding_context = self._get_worldbuilding_context(
                query=f"{self._get_actor_category_label(proactor)} {proactor.sheet.occupation} {goals_hint} daily routine behavior technology era communication devices setting {scene_description[:100]}",
                max_tokens=400
            )
            if occupation_guidance or goals_guidance:
                worldbuilding_context = "\n\n".join([x for x in [occupation_guidance, goals_guidance, worldbuilding_context] if x])
            if worldbuilding_context:
                worldbuilding_context = f"""**WORLDBUILDING CONTEXT (act according to this world's rules):**
{worldbuilding_context}

**CRITICAL: Follow the technology and setting constraints from the worldbuilding context above.**

Use ONLY technology, objects, and vocabulary that appear in the WORLD SETTING CONTEXT provided above. Never invent technology based on assumed time periods - ground every action and object in the established worldbuilding.
"""

        # Get concrete details for consistency
        concrete_details = self._get_concrete_details_context([proactor.sheet.name])

        # Get spatial context for position awareness
        try:
            from agents.spatial_context_helper import get_spatial_context_for_prompt
            spatial_context = get_spatial_context_for_prompt(proactor_name=proactor.sheet.name)
        except Exception:
            spatial_context = ""

        # Get status string safely
        status_str = "Unknown"
        if hasattr(proactor.sheet, 'get_statuses_string'):
            status_str = proactor.sheet.get_statuses_string()
        elif hasattr(proactor.sheet, 'statuses'):
            status_str = str(proactor.sheet.statuses)
        
        # Build relationship section
        relationship_section = ""
        if relationship_context:
            relationship_section = f"""**RELATIONSHIPS WITH VISIBLE ACTORS:**
{relationship_context}
Consider these relationships when deciding how to act!
"""

        relationship_dynamics_section = ""
        try:
            relationship_dynamics_section = self._get_relationship_dynamics_context(
                proactor,
                query=f"relationships factions sympathy {proactor.sheet.occupation} {' '.join([str(g) for g in (proactor.sheet.goals or [])[:2] if g])}",
                max_tokens=250
            )
        except Exception:
            relationship_dynamics_section = ""

        persistent_context = ""
        try:
            persistent_context = self._get_persistent_context_section(proactor, max_event_lines=10)
        except Exception:
            persistent_context = ""

        long_term_memory = ""
        try:
            long_term_memory = self._get_actor_long_term_memory_section(proactor, limit=8)
        except Exception:
            long_term_memory = ""
            
        actor_category = self._get_actor_category_label(proactor)
        prompt = f"""
        You are the NUA Decision Agent for {proactor.sheet.name} in a living simulation.
        Current Mode: ROAM (Exploration/Routine)
        
        {worldbuilding_context}
        
        **CHARACTER CONTEXT:**
        Name: {proactor.sheet.name}
        Category: {actor_category}
        Occupation: {proactor.sheet.occupation}
        Personality: {proactor.sheet.personality_traits}
        Goals: {proactor.sheet.goals}
        Current Status: {status_str}
        
        {concrete_details}
        
        **ENVIRONMENT CONTEXT:**
        Scene: {scene_description}
        Time: {time_context.get('formatted_time') if time_context else 'Unknown'}
        Visible Actors: {visible_actors_str}
        {spatial_context}
        {relationship_section}
        {relationship_dynamics_section}
        {persistent_context}
        
        **MEMORY CONTEXT:**
        {memory_context}
        {long_term_memory}
        
        {recent_actions}
        
        **DECISION GUIDELINES:**
        - Act autonomously based on personality, goals, AND your relationships with visible actors.
        - If you have positive feelings toward someone, you might greet them, help them, or engage in friendly conversation.
        - If you have negative feelings, you might avoid them, be curt, or watch them suspiciously.
        - You can interact with other actors (User or NPCs), interact with the environment, or do nothing/wait.
        - If you speak, include the dialogue in quotes.
        - If you start a significant interaction with the User or an NPC that requires a response, this may trigger an EXCHANGE.
        - BE NATURAL. If you are a guard, you might patrol. If a merchant, you might organize goods.
        - AVOID repeating actions you've already taken recently.
        - **YOU HAVE AGENCY TO LEAVE:** If your goals are elsewhere, you're done here, or you simply want to go, you can LEAVE THE LOCATION. This is a valid choice - you are not obligated to stay.
        
        **REQUIRED OUTPUT FORMAT (JSON):**
        {{
            "narrative_description": "Full description of the action, including dialogue if any. Write in THIRD PERSON.",
            "action_type": "interaction" | "movement" | "wait" | "task" | "exchange_start" | "depart_location",
            "target": "Name of target actor if interaction/exchange, else null",
            "dialogue": "Exact dialogue string if spoken, else null"
        }}
        
        Respond ONLY with the JSON object.
        """

        prompt_text = prompt.strip()
        data = self._call_llm_for_json(prompt_text) or {}

        # Guardrail: if ROAM narrative is empty or punctuation-only (common failure mode ':'),
        # evict it from cache so the caller's retry loop can get a fresh LLM response.
        try:
            narrative = data.get('narrative_description')
            if not isinstance(narrative, str):
                return data

            stripped = narrative.strip()
            # Consider invalid if nothing but punctuation/whitespace
            has_alpha = any(ch.isalpha() for ch in stripped)
            if (not stripped) or (not has_alpha) or stripped in {":", "-", "--", "..."}:
                try:
                    prompt_hash = hashlib.sha256(prompt_text.encode()).hexdigest()
                    if prompt_hash in self.response_cache:
                        del self.response_cache[prompt_hash]
                except Exception:
                    pass
                # Return empty so upstream can retry or fallback cleanly
                return {}
        except Exception:
            pass

        return data

    def determine_nua_proaction(self, proactor: 'Actor', reactor: 'Actor', context_guidance: Dict = None, group_members: list = None, time_context: Optional[Dict[str, Any]] = None, last_exchange_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Determines the Non-User-Actor's (NUA) proactive action when it wins initiative.
        INUAs don't take proactive actions - they only react.
        
        Args:
            proactor: The actor taking the action
            reactor: The target of the action
            context_guidance: Context and escalation guidance
            group_members: List of NPCs acting together (if this is a grouped turn)
            time_context: Optional time-of-day context for narrative consistency
            last_exchange_context: Recent exchange data (actions, outcomes, narratives) for continuity
        """
        # Ensure we have the authoritative scene before building prompts
        self._refresh_scene_from_tracker()
        
        # Store time context for prompt enhancement
        self.time_context = time_context
        
        if hasattr(proactor, 'is_inanimate') and proactor.is_inanimate:
            return None
        
        # Check for ally assistance needs FIRST (highest priority)
        all_actors = context_guidance.get('all_actors', [proactor, reactor]) if context_guidance else [proactor, reactor]
        assistance_needed = ally_coordinator.check_ally_assistance_needed(
            actor=proactor,
            all_actors=all_actors,
            current_situation=self.scene_description
        )
        if assistance_needed:
            ally_coordinator.display_coordination_action(assistance_needed)
            # Convert assistance action to proper format
            return {
                'action_description': assistance_needed['narrative'],
                'targeted_status': 'STAMINA',
                'shift_polarity': 'Additive',
                'shift_type': 'Temporary',
                'stress_level': 2,
                'self_effects': [{
                    'condition': 'Helping ally',
                    'target_status': 'STAMINA',
                    'polarity': 'Subtractive',
                    'shift_type': 'Temporary',
                    'severity': 1,
                    'description': f'{proactor.sheet.name} exerts effort to help their wounded ally'
                }]
            }
        
        # Get dialogue context if this is a conversation
        dialogue_context = ""
        if dialogue_context_system.has_conversation_history(proactor.sheet.name, reactor.sheet.name):
            dialogue_context = dialogue_context_system.get_dialogue_context(proactor.sheet.name, reactor.sheet.name)
        
        # Get sympathy-based behavior guidance
        sympathy_value = proactor.sheet.get_sympathy(reactor.sheet.name)
        behavior_guidance = sympathy_behavior_modifier.get_behavior_guidance(
            proactor.sheet.name,
            reactor.sheet.name,
            sympathy_value,
            "general"
        )
        
        # Get memory context
        nua_memory_system = get_nua_memory_system()
        memory_context = nua_memory_system.get_memory_context_for_decision(
            proactor.sheet.name,
            reactor.sheet.name
        )
        
        # CRITICAL: Validate NUA state with memories for consistency
        nua_state_context = ""
        
        # Force-feed the immediate last turn narrative if available to ensure emotional continuity
        if last_exchange_context and last_exchange_context.get('outcome_narrative'):
            last_narrative = last_exchange_context.get('outcome_narrative')
            nua_state_context += f"""
**🚨 IMMEDIATE PREVIOUS OUTCOME (MUST MAINTAIN CONTINUITY):**
{last_narrative}

CRITICAL: Your action MUST reflect the emotional and physical state described above. 
If you were in pain, you are STILL in pain. If you were angry, you are STILL angry. 
DO NOT RESET TO NEUTRAL.
"""

        if hasattr(self, 'tracker_agent') and self.tracker_agent:
            try:
                nua_state = self.tracker_agent.get_nua_state_history(proactor.sheet.name)
                if nua_state and nua_state['status'] == 'alive':
                    # Cross-check sympathy values
                    tracked_sympathy = nua_state['state'].get('sympathy', {}).get(reactor.sheet.name, {})
                    if tracked_sympathy:
                        tracked_value = tracked_sympathy.get('value', 0)
                        current_sympathy_obj = proactor.sheet.sympathy.get(reactor.sheet.name)
                        if current_sympathy_obj:
                            current_value = current_sympathy_obj.value
                            if abs(tracked_value - current_value) > 2:
                                print(f"[WARNING] Sympathy mismatch for {proactor.sheet.name} → {reactor.sheet.name}: tracked={tracked_value}, current={current_value}")
                                # Use tracked value as source of truth
                                current_sympathy_obj.value = tracked_value
                    
                    # Add state context to prompt
                    nua_state_context = f"""
**NUA STATE HISTORY:**
Last known location: {nua_state.get('location', 'Unknown')}
Current sympathy toward {reactor.sheet.name}: {tracked_sympathy.get('value', 0) if tracked_sympathy else 'Unknown'}
Status: {nua_state['status']}

Your behavior MUST be consistent with this history and your memories.
"""
            except Exception as e:
                print(f"[WARNING] Could not validate NUA state: {e}")
        
        # Get worldbuilding context for NPC decision-making
        worldbuilding_context = ""
        if self.rag_system:
            proactor_goals_hint = ""
            try:
                if hasattr(proactor.sheet, 'goals') and proactor.sheet.goals:
                    proactor_goals_hint = " ".join([str(g) for g in proactor.sheet.goals[:3] if g])
            except Exception:
                proactor_goals_hint = ""
            occupation_guidance = self._get_worldbuilding_context(
                query=f"{proactor.sheet.occupation} occupations social role",
                max_tokens=250,
                category_filter=self._get_actor_occupation_category(proactor)
            )
            goals_guidance = self._get_worldbuilding_context(
                query=f"{proactor_goals_hint} goals motivation",
                max_tokens=250,
                category_filter=self._get_actor_goals_category(proactor)
            )
            worldbuilding_context = self._get_worldbuilding_context(
                query=f"{self._get_actor_category_label(proactor)} {proactor.sheet.occupation} {proactor_goals_hint} {self.scene_description[:150]} civilization culture supernatural mechanics conflict_generators temporal",
                max_tokens=400
            )
            if occupation_guidance or goals_guidance:
                worldbuilding_context = "\n\n".join([x for x in [occupation_guidance, goals_guidance, worldbuilding_context] if x])
        
        # Get spatial context for position awareness
        try:
            from agents.spatial_context_helper import get_spatial_context_for_prompt
            spatial_context = get_spatial_context_for_prompt(proactor_name=proactor.sheet.name)
        except Exception:
            spatial_context = ""
        
        # Get tactical assessment if in combat
        enemies = [reactor] if context_guidance and context_guidance.get('escalation_level', 0) >= 3 else []
        allies = [a for a in all_actors if a != proactor and a != reactor]
        tactical_assessment = tactical_awareness_system.assess_tactical_situation(
            proactor, enemies, allies, self.scene_description
        )
        
        # Override with tactical recommendation if urgent
        if tactical_assessment['urgency'] == 'critical':
            tactical_awareness_system.display_tactical_assessment(proactor, enemies, allies, self.scene_description)
            return {
                'action_description': tactical_assessment['reasoning'],
                'targeted_status': 'STAMINA',
                'shift_polarity': 'Subtractive' if 'flee' in tactical_assessment['recommended_action'] else 'Additive',
                'shift_type': 'Temporary',
                'stress_level': 3,
                'self_effects': [{
                    'condition': 'Tactical necessity',
                    'target_status': 'SPIRIT',
                    'polarity': 'Subtractive',
                    'shift_type': 'Temporary',
                    'severity': 1,
                    'description': f'{proactor.sheet.name} acts under tactical pressure'
                }]
            }
            
        # Only show NUA character sheets - never expose UA (User Actor) sheets to prevent meta-gaming
        show_reactor_sheet = not getattr(reactor, 'is_user_actor', False)
        reactor_sheet_dict = reactor.sheet.to_dict() if show_reactor_sheet else None
        
        # Check if proactor is a User Actor - if so, don't expose their sheet
        show_proactor_sheet = not getattr(proactor, 'is_user_actor', False)
        proactor_sheet_dict = proactor.sheet.to_dict() if show_proactor_sheet else None
        
        # Ensure sympathy is passed for NUA behavior logic
        sympathy_context_str = ""
        try:
            current_sympathy = proactor.sheet.get_sympathy(reactor.sheet.name)
            sympathy_context_str = f"Current sympathy toward {reactor.sheet.name}: {current_sympathy}"
            # Append to nua_state_context if not already there
            if nua_state_context and f"Current sympathy toward {reactor.sheet.name}" not in nua_state_context:
                nua_state_context += f"\n{sympathy_context_str}"
            elif not nua_state_context:
                nua_state_context = f"\n**RELATIONSHIP STATE:**\n{sympathy_context_str}\n"
        except Exception:
            pass
        
        recent_actions = self._get_recent_nua_actions(proactor.sheet.name)
        
        # Debug: Log action history status for production troubleshooting
        self.logger.log_system(f"DEBUG: Action history for {proactor.sheet.name}: {recent_actions[:100]}...")

        # Use context guidance for escalation analysis if available
        from llm_agents.nua_context_system import NUAContextTracker, EscalationLevel, ActionType
        temp_context = NUAContextTracker("temp_analysis")
        
        # Get escalation level from context guidance or default to TENSE
        if context_guidance and 'escalation_level' in context_guidance:
            escalation_value = context_guidance['escalation_level']
            escalation_names = ['PEACEFUL', 'TENSE', 'HOSTILE', 'VIOLENT', 'LETHAL']
            escalation_name = escalation_names[min(escalation_value - 1, 4)] if escalation_value > 0 else 'TENSE'
            
            # Create mock escalation object
            class MockEscalation:
                def __init__(self, name, value):
                    self.name = name
                    self.value = value
            
            immediate_escalation = MockEscalation(escalation_name, escalation_value)
            immediate_action_type = ActionType.PHYSICAL if escalation_value >= 4 else ActionType.SOCIAL
        else:
            # Fallback for when no context is available - assume moderate threat
            immediate_escalation = EscalationLevel.TENSE
            immediate_action_type = ActionType.SOCIAL
        
        # Use immediate escalation analysis if no context guidance provided
        if not context_guidance:
            context_guidance = {
                'escalation_level': immediate_escalation.value,
                'recommended_action_type': 'cooperative_response' if immediate_escalation.value <= 2 else ('defensive_response' if immediate_escalation.value <= 4 else 'lethal_response'),
                'context_summary': f"Escalation: {immediate_escalation.name}, Trust: Unknown"
            }
        # DEBUG - Summarize initial inputs
        try:
            print(f"{Color.SYSTEM}NUA PROACTOR DEBUG: proactor={proactor.sheet.name}, reactor={reactor.sheet.name}{Color.RESET}")
            print(f"{Color.SYSTEM}NUA PROACTOR DEBUG: context_guidance={{'escalation_level': {context_guidance.get('escalation_level')}, 'recommended_action_type': '{context_guidance.get('recommended_action_type')}', 'has_mode': {bool(context_guidance.get('narrative_mode'))}}}{Color.RESET}")
            latest_scene = getattr(self, 'scene_description', '')
            print(f"{Color.SYSTEM}NUA PROACTOR DEBUG: scene_description_preview='{str(latest_scene)[:120]}'{Color.RESET}")
        except Exception:
            pass
        
        # Enhance context guidance with Four-Mode Narrative Loop guidance if available
        narrative_guidance_section = ""
        if context_guidance.get('narrative_mode'):
            narrative_mode = context_guidance.get('narrative_mode', 'unknown')
            narrative_intent = context_guidance.get('narrative_intent', 'Natural progression')
            narrative_tone = context_guidance.get('narrative_tone', 'Balanced')
            
            narrative_guidance_section = f"""
    **ðŸ“– FOUR-MODE NARRATIVE GUIDANCE:**
    Current Mode: {narrative_mode.title()}
    Intent: {narrative_intent}
    Tone: {narrative_tone}
    
    **MODE-SPECIFIC NPC BEHAVIOR:**"""
            
            if narrative_mode.lower() == 'roam':
                narrative_guidance_section += """
    - ROAM MODE: Be curious, exploratory, and social
    - Engage in drift-friendly interactions and conversations
    - Show interest in discovering new things or people
    - Avoid aggressive or high-stakes confrontations"""
            elif narrative_mode.lower() == 'spark':
                narrative_guidance_section += """
    - SPARK MODE: Present opportunities or gentle challenges
    - Create hooks that invite engagement without forcing conflict
    - Be purposeful but not overwhelming in your approach
    - Guide toward meaningful interactions or discoveries"""
            elif narrative_mode.lower() == 'pressure':
                # Check for active mission context
                active_mission = guidance_data.get('active_mission')
                mission_progress = guidance_data.get('mission_progress', 0.0)
                
                if active_mission:
                    narrative_guidance_section += f"""
    - PRESSURE MODE: Advance Mission '{active_mission}'
    - Mission Progress: {int(mission_progress * 100)}%
    - Create obstacles that directly challenge progress toward this mission
    - Mix hard challenges (require planning/resources) with easier wins (build momentum)
    - Each interaction should feel like it advances or complicates the mission
    - Be assertive and create meaningful obstacles related to the mission goal"""
                else:
                    narrative_guidance_section += """
    - PRESSURE MODE: Escalate stakes and create complications
    - Challenge the protagonist's assumptions or plans
    - Introduce time pressure or difficult moral choices
    - Be more assertive and create meaningful obstacles"""
            elif narrative_mode.lower() == 'outcome':
                # Check for completed mission
                active_mission = guidance_data.get('active_mission')
                mission_progress = guidance_data.get('mission_progress', 0.0)
                
                if active_mission and mission_progress >= 1.0:
                    narrative_guidance_section += f"""
    - OUTCOME MODE: Resolve Mission '{active_mission}'
    - Mission Complete! Deliver consequences and rewards
    - Tie up loose ends related to this mission
    - Show how the world/relationships changed from this mission
    - Provide closure while hinting at new possibilities
    - Be measured and thoughtful in delivering resolution"""
                else:
                    narrative_guidance_section += """
    - OUTCOME MODE: Focus on resolution and consequences
    - Allow for natural conclusions to conflicts
    - Provide space for reflection and character growth
    - Be more measured and thoughtful in responses"""
        
        # Build escalation context section with immediate threat emphasis
        escalation_context = f"""
    **ðŸš¨ IMMEDIATE THREAT ASSESSMENT (CRITICAL):**
    Proactor's Action Escalation Level: {immediate_escalation.name} ({immediate_escalation.value}/5)
    Proactor's Action Type: {immediate_action_type.value}
    
    **ðŸ”¥ ESCALATION CONTEXT (CRITICAL):**
    Current Escalation Level: {context_guidance.get('escalation_level', immediate_escalation.value)}
    Recommended Action Type: {context_guidance.get('recommended_action_type', 'defensive_response')}
    Context Summary: {context_guidance.get('context_summary', 'No previous context')}
    {narrative_guidance_section}
    
    âš ï¸ **ESCALATION RESPONSE RULES (MANDATORY):**
    - If escalation is PEACEFUL (1): Casual response, social interaction
    - If escalation is TENSE (2): Cautious, alert, ready to defend
    - If escalation is HOSTILE (3): MUST use aggressive actions (attack, threaten, intimidate, physical confrontation)
    - If escalation is VIOLENT (4): MUST use physical combat, serious defensive measures
    - If escalation is LETHAL (5): MUST use direct violence or overwhelming force - LIFE OR DEATH SITUATION
    - HOSTILE+ escalation PROHIBITS passive actions like pure conversation or social manipulation
    - At HOSTILE+ level, character has moved beyond talking - action must involve threat or force
    - Deception/cunning can SUPPLEMENT aggressive actions but cannot REPLACE them at HOSTILE+ escalation
    
    ðŸš¨ **LETHAL SITUATION OVERRIDE:** If proactor action is LETHAL (5), reactor MUST respond with maximum force for survival!
    """

        # Build remote encounter context if applicable
        remote_context = ""
        if context_guidance and context_guidance.get('is_remote_encounter'):
            remote_type = context_guidance.get('remote_encounter_type', 'phone_call').replace('_', ' ').upper()
            remote_constraint = context_guidance.get('remote_constraint', '')
            remote_context = f"""

    🚨🚨🚨 **ABSOLUTE REQUIREMENT: {remote_type} - HEARING ONLY** 🚨🚨🚨
    {remote_constraint}
    
    **YOU ARE ON A PHONE CALL. ONLY YOUR HEARING WORKS.**
    - You can HEAR: voice, tone, words, background sounds
    - You CANNOT see, touch, smell, or taste anything
    - The other person CANNOT see you, so physical actions are meaningless
    
    **MANDATORY FORMAT FOR narrative_description:**
    - MUST start with: "says '[exact dialogue in quotes]'"
    - MUST end with: "in a [tone] voice"
    - NOTHING ELSE IS ALLOWED
    
    **CORRECT EXAMPLES:**
    ✅ "says 'Hey, I was thinking about that project we discussed' in a thoughtful voice"
    ✅ "says 'I'd love to help you with that!' in an enthusiastic voice"
    ✅ "says 'Can we meet up later to talk about this?' in a casual voice"
    
    **ABSOLUTELY FORBIDDEN - DO NOT USE:**
    ❌ ANY "while [action]" - FORBIDDEN! (e.g., "while pulling out", "while moving", "while picking up")
    ❌ "walks towards..." (YOU CANNOT WALK ON A PHONE CALL)
    ❌ "approaches..." (YOU CANNOT APPROACH ON A PHONE CALL)
    ❌ "pulling out..." (THEY CANNOT SEE YOU PULLING ANYTHING)
    ❌ "picks up..." (THEY CANNOT SEE YOU PICKING UP ANYTHING)
    ❌ "gestures..." (THEY CANNOT SEE YOU)
    ❌ "smiles..." (THEY CANNOT SEE YOU)
    ❌ "eyes sparkling..." (THEY CANNOT SEE YOUR EYES)
    ❌ ANY physical movement or visible expression (THEY CANNOT SEE YOU)
    
    **IF YOU GENERATE ANYTHING OTHER THAN DIALOGUE, THE SYSTEM WILL FAIL.**
    **ONLY DIALOGUE. ONLY VOICE TONE. NOTHING ELSE.**
    """

        # Build grouped NUA context if applicable
        grouped_context = ""
        if group_members and len(group_members) > 1:
            group_names = [npc.sheet.name for npc in group_members]
            grouped_context = f"""

    **GROUPED NPC TURN - COORDINATED ACTION:**
    This NPC is acting as part of a coordinated group with tied initiative.
    **Group Members:** {', '.join(group_names)}

    **COORDINATION GUIDELINES:**
    - This NPC's action should complement the group's overall strategy
    - Consider how this action works with what other group members might do
    - Coordinated attacks (flanking, distraction, combined assault)
    - Coordinated defense (covering allies, forming defensive line)
    - Tactical positioning (surrounding target, blocking escape routes)
    - Support actions (one attacks while others provide cover/distraction)

    **IMPORTANT:** You are deciding THIS NPC's action only, but be aware they are part of a coordinated effort.
    The group acts together because they have the same initiative - make the action feel like part of a team strategy.
    """

        # Build last exchange context section FIRST for maximum prominence
        last_exchange_section = self._build_last_exchange_context_section(last_exchange_context, proactor.sheet.name, reactor.sheet.name) if last_exchange_context else ""
        
        prompt = f"""{nua_state_context}
    You are the NUA Decision Agent. Your PRIMARY goal is to create an authentic, dynamic character experience that prioritizes NARRATIVE IMMERSION over mechanical optimization.
    {remote_context}
    {last_exchange_section}
    
    **WORLDBUILDING CONTEXT (Reality & Setting Constraints):**
    {worldbuilding_context if worldbuilding_context else "Use period-appropriate actions and technology."}
    
    **CHARACTER-FIRST DECISION MAKING:**
    **PERSONALITY DRIVES ACTION:** {proactor.sheet.name}'s personality traits ({proactor.sheet.personality_traits}) should be the PRIMARY factor in decision-making
    **GOALS ARE PARAMOUNT:** Every action must serve {proactor.sheet.name}'s goals: {proactor.sheet.goals}
        → Ask yourself: "How does this action move me closer to achieving my goals?"
        → Be strategic: Use every interaction as an opportunity for goal advancement
        → Stay focused: Don't get distracted from what you're trying to accomplish
    **AVOID REPETITION:** Do NOT repeat recent actions. Be creative and dynamic!
    **EMBRACE VARIETY:** Mix different approaches - physical, social, psychological, environmental, strategic
    {grouped_context}
    {escalation_context}

    **RECENT ACTION HISTORY (AVOID REPEATING):**
    {recent_actions}

    **CHARACTER AUTHENTICITY RULES:**
    1. **Personality First:** What would THIS specific character realistically do based on their traits and background?
    2. **Goal-Oriented:** How does this action serve their personal objectives?
    3. **Relationship Context:** Consider existing sympathy/hostility and the nature of the interaction
    4. **Prioritize Authentic Responses:** Consider cooperation, assistance, or neutral responses before defaulting to opposition
    5. **Dynamic Behavior:** Vary tactics, approaches, and intensity based on situation evolution
    6. **Emotional State:** Consider their current status levels as emotional/physical state indicators
    
    **ACTION VARIETY GUIDELINES:**
    - **Cooperative:** Assistance, information sharing, alliance building
    - **Neutral:** Professional responses, transactional interactions, boundary setting
    - **Social:** Persuasion, negotiation, conversation, relationship building
    - **Aggressive:** Direct attacks, intimidation, escalation (when escalation warrants it)
    - **Defensive:** Blocks, dodges, protective stances when threatened
    - **Strategic:** Positioning, preparation, resource management, seeking advantage
    - **Environmental:** Using surroundings, tools, terrain advantages
    - **Psychological:** Mind games, misdirection, emotional manipulation
    - **Opportunistic:** Exploiting weaknesses, capitalizing on moments
    - **Passive/Waiting:** Doing nothing, observing, waiting for opponent's move, defensive stance
      * Valid when: Assessing situation, waiting for better opportunity, conserving energy
      * Tactical value: Lets opponent act first, gathers information, avoids commitment
      * Use sparingly: Should feel like a deliberate tactical choice, not indecision
    - **Flee/Escape (CRITICAL):** Attempting to leave the exchange or area
      * Valid when: Overwhelmed, injured (low STAMINA/SPIRIT), mission failure imminent, or tactically prudent
      * Tactical value: Preserves life/resources, resets engagement
      * Criteria: High stress, low health, outmatched by opponent, or goal achieved

    **ESCALATION-DEPENDENT CONSTRAINTS:**
    - **HOSTILE/VIOLENT ESCALATION:** Aggressive actions OR Flee/Escape may be required for authenticity
    - **LOWER ESCALATION:** Full variety allowed - prioritize cooperative/neutral/social approaches
    
    **S-TRAIT ACTION SELECTION GUIDE (Consistency Required):**
    - Verbal persuasion, command, boundary-setting, de-escalation -> choose SOCIABILITY
    - Physical exertion, lifting, shoving, grappling, breaking -> choose STURDINESS
    - Evasive footwork, quick approach/retreat, acrobatics, FLEEING -> choose SWIFTNESS
    - Misdirection, feint, stealthy manipulation, concealment -> choose SHADOW
    - Logical analysis, rule/policy citation, precise planning -> choose SMARTS
    
    You MUST align the S-trait with the action's described narrative style. If your initial choice does not match, re-evaluate and select the more appropriate trait, and justify briefly.

    **Scenario Context:**
    *   **Scene:** {self.scene_description}
    *   **Proactor (The one acting):** {proactor.sheet.name}
    *   **Reactor (The one being acted upon):** {reactor.sheet.name}
    {spatial_context}
    {self._get_persistent_context_section(proactor, max_event_lines=10)}
    
    {f'''**RELATIONSHIP CONTEXT:**
    {proactor.sheet.relationship_context}
    ''' if hasattr(proactor.sheet, 'relationship_context') and proactor.sheet.relationship_context else ''}
    
    **🎯 GOALS & MOTIVATIONS (CRITICAL - DRIVE YOUR ACTION):**
    {proactor.sheet.name}'s Primary Goals: {proactor.sheet.goals}
    
    **⚠️ GOAL-DRIVEN ACTION REQUIREMENTS:**
    - Every action should advance at least one of {proactor.sheet.name}'s goals
    - Consider: How does this interaction with {reactor.sheet.name} help or hinder your objectives?
    - Be opportunistic: Can you use this moment to make progress toward your goals?
    - Stay authentic: Goals should guide but not override personality and relationships
    {f"- Context from last exchange: Use what just happened to further your goals" if last_exchange_context else ""}
    
    **CONVERSATION HISTORY:**
    {dialogue_context if dialogue_context else "No previous conversation between these actors."}
    
    **RELATIONSHIP GUIDANCE (SYMPATHY: {sympathy_value}):**
    {behavior_guidance['guidance_text']}
    **Behavioral Constraints:**
    {chr(10).join('    - ' + c for c in behavior_guidance['constraints'])}
    **Dialogue Tone:** {behavior_guidance['dialogue_tone']}
    
    **TACTICAL SITUATION:**
    Threat Level: {tactical_assessment['threat_level']}/5
    NPC Condition: {tactical_assessment['npc_condition']}
    Recommended Action: {tactical_assessment['recommended_action']}
    Reasoning: {tactical_assessment['reasoning']}
    
    **NPC MEMORIES:**
    {memory_context}

    {self._get_actor_long_term_memory_section(proactor, limit=8)}

    **Character Sheets:**
    {f'''*   **Proactor Sheet ({proactor.sheet.name}):**
        ```json
        {json.dumps(proactor_sheet_dict, indent=2)}
        ```''' if show_proactor_sheet else f'''*   **Proactor ({proactor.sheet.name}):** [User Actor - sheet hidden for immersion]'''}
    {f'''*   **Reactor Sheet ({reactor.sheet.name}):**
        ```json
        {json.dumps(reactor_sheet_dict, indent=2)}
        ```''' if show_reactor_sheet else f'''*   **Reactor ({reactor.sheet.name}):** [User Actor - sheet hidden for immersion]'''}

    {f'''**CHARACTER ANALYSIS FOR {proactor.sheet.name}:**
    - **Personality:** {proactor.sheet.personality_traits}
    - **Primary Goals:** {proactor.sheet.goals}
    - **Occupation/Background:** {proactor.sheet.occupation}
    - **Current Emotional State:** Consider their Spirit level as confidence/morale
    - **Physical Condition:** Consider their Stamina level as energy/health
    - **Resource Status:** Consider their Supply level as preparedness/wealth''' if show_proactor_sheet else f'''**PROACTOR ANALYSIS FOR {proactor.sheet.name}:**
    - [User Actor - detailed analysis hidden for immersion]
    - You can observe their general actions and behavior, but not their internal stats or motivations'''}
    
    **DECISION PROCESS:**
    1. **Character Motivation:** What would drive {proactor.sheet.name} to act right now?
    2. **Goal Advancement (CRITICAL):** Which of their goals can this action advance? How?
    3. **Relationship Assessment:** What is their relationship with the target? (ally, neutral, rival, enemy)
    4. **Personality Expression:** How would their traits manifest in this situation?
    5. **Tactical Variety:** What haven't they tried recently that fits their character?
    6. **Situational Adaptation:** How do current circumstances shape their choice?
    
    **Your Task:**
    Create an action that feels AUTHENTIC to {proactor.sheet.name} as a living character with motivations and relationships. NPCs can be allies, neutrals, or opponents based on context and personality. Prioritize narrative immersion and character consistency over mechanical optimization.

    Return a JSON object with the following structure:
    
    {{
        "action_noun": "A single, simple noun for the action (e.g., 'attack', 'intimidate', 'deceive', 'retreat').",
        "narrative_description": "{self._get_narrative_format_instruction(context_guidance, reactor)}",
        "character_motivation": "Explain WHY this character would choose this specific action based on their personality and goals.",
        "justification": "Your reasoning for selecting the specific skill and supplement based on character authenticity and narrative variety.",
        "utas_factors": {{
            "exchange_type": "The type of exchange taking place - MUST be one of: SPIRIT, STAMINA, or SUPPLY (based on the primary status being affected).",
            "s_trait_to_use": "The most relevant S-Trait for the action (SWIFTNESS, SOCIABILITY, STURDINESS, SMARTS, SHADOW).",
            "s_trait_value": "The value of the S-Trait being used.",
            "skill": {{"name": "skill_name", "value": skill_value}},
            "endowment": {{"name": "endowment_name", "value": endowment_value}},
            "supplement": {{"name": "supplement_name", "value": supplement_value}},
            "stress_level": "An integer from 1 (very low stress) to 5 (very high stress), representing the action's inherent difficulty.",
            "status_to_shift": "The primary status of the target you intend to affect (SPIRIT, STAMINA, SUPPLY).",
            "shift_type": "DURATION - MUST be either 'Temporary' (effect lasts only this scene) or 'Lasting' (effect persists). Examples: encouraging words = Temporary, teaching a skill = Lasting. **DO NOT confuse with shift_polarity!**",
            "shift_polarity": "DIRECTION - MUST be either 'Additive' (increasing/helping) or 'Subtractive' (decreasing/harming). Examples: healing = Additive, attacking = Subtractive. **DO NOT confuse with shift_type!** In combat/hostile situations, use 'Subtractive' when attacking, defending, or counterattacking. Use 'Additive' ONLY when genuinely helping/healing the target.",
            "self_effects": [ // **CRITICAL**: This field MUST be present and CANNOT be empty for proactor actions! Must contain at least one self-effect.
                {{
                    "trigger": "The condition for the effect (Inherent Cost, On Action Success, On Action Failure).",
                    "status_shifted": "The status on the proactor to be shifted (e.g., 'STAMINA').",
                    "shift_magnitude": "The size of the shift (e.g., -1).",
                    "prefix": "A short phrase describing the cause (e.g., 'As a result of the exertion,').",
                    "description": "A brief description of the effect on the proactor (e.g., 'feels a drain on their energy')."
                }}
            ]
        }}
    }}

        **CRITICAL FORMATTING REQUIREMENTS:**
        - ALL nested objects (skill, supplement) MUST be JSON objects with "name" and "value" keys
        - ALL numeric values MUST be integers, never strings or text
        - If no skill/supplement applies, use: {{"name": "None", "value": 0}}
        - NEVER return strings where objects are expected

        **CORRECT EXAMPLES:**
        "skill": {{"name": "Combat", "value": 3}}
        "supplement": {{"name": "Sword", "value": 2}}
        "stress_level": 4

        **SELF-EFFECTS EXAMPLES:**
        ðŸš¨ **CRITICAL: Only ONE self-effect condition applies per NUA proactor per action!** ðŸš¨
        Choose the most appropriate trigger based on the action's nature:

        **Example 1 - Inherent Cost (Most Common):**
        "self_effects": [
            {{
                "trigger": "Inherent Cost",
                "status_shifted": "STAMINA",
                "shift_magnitude": -1,
                "severity": 2,
                "severity_justification": "Moderate physical exertion from combat action",
                "prefix": "From the physical exertion,"
                "description": "feels their energy drain from the intense effort"
            }}
        ]

        **Example 2 - On Action Success:**
        "self_effects": [
            {{
                "trigger": "On Action Success",
                "status_shifted": "SPIRIT",
                "shift_magnitude": +1,
                "severity": 1,
                "severity_justification": "Minor positive boost from successful action",
                "prefix": "After successfully completing the action,",
                "description": "feels a surge of confidence and emotional empowerment"
            }}
        ]

        **Example 3 - On Action Failure:**
        "self_effects": [
            {{
                "trigger": "On Action Failure",
                "status_shifted": "SPIRIT",
                "shift_magnitude": -2,
                "severity": 3,
                "severity_justification": "Significant psychological impact from failed action",
                "prefix": "From the humiliating failure,",
                "description": "feels their confidence shatter as their attack is easily deflected"
            }}
        ]

        **TRIGGER SELECTION GUIDE:**
        - **Inherent Cost**: Effect happens only if success and failure are not applicable (physical exertion, resource consumption)
        - **On Action Success**: Effect only occurs if the action succeeds (confidence boost, overconfidence, empowerment from success)
        - **On Action Failure**: Effect only occurs if the action fails (embarrassment, injury from failure, wasted resources)

        ðŸš¨ **SEVERITY FIELD IS MANDATORY FOR ALL SELF-EFFECTS** ðŸš¨
        âœ… CORRECT: "severity": 2
        âœ… CORRECT: "severity": 1  
        âœ… CORRECT: "severity": 4
        âŒ WRONG: "severity": null
        âŒ WRONG: "severity": None
        âŒ WRONG: Missing severity field entirely
        
        **SEVERITY MUST ALWAYS BE AN INTEGER FROM 1 TO 4**
        If unsure, use 2 as a safe default rather than leaving it empty!

        **INCORRECT EXAMPLES TO AVOID:**
        "skill": "Combat"  âŒ (should be object)
        "skill": {{"name": "Combat", "value": "3"}}  âŒ (value should be number)
        "stress_level": "High"  âŒ (should be number)
        "self_effects": []  âŒ (NEVER empty for proactor actions!)

        **IF UNCERTAIN:**
        - For skills: Use {{"name": "None", "value": 0}}
        - For supplements: Use {{"name": "None", "value": 0}}
        - For numeric values: Use appropriate integer (1-5)

        **COMPLETE EXAMPLE - SOCIAL ACTION WITH DIALOGUE:**
        {{
            "action_noun": "Approach",
            "narrative_description": "says \"Hey, you got a minute? I wanted to talk about that mixtape project\" while approaching {reactor.sheet.name} with a friendly smile",
            "character_motivation": "{proactor.sheet.name} wants to collaborate on the mixtape and sees this as an opportunity to advance their music goals while building a connection.",
            "justification": "Using SOCIABILITY and Conversation skill since this is a friendly social approach. No supplement needed for casual conversation.",
            "utas_factors": {{
                "exchange_type": "SPIRIT",
                "s_trait_to_use": "SOCIABILITY",
                "s_trait_value": 3,
                "skill": {{"name": "Conversation", "value": 2}},
                "endowment": {{"name": "None", "value": 0}},
                "supplement": {{"name": "None", "value": 0}},
                "stress_level": 1,
                "status_to_shift": "SPIRIT",
                "shift_type": "Temporary",
                "shift_polarity": "Additive",
                "self_effects": [
                    {{
                        "trigger": "Inherent Cost",
                        "status_shifted": "SPIRIT",
                        "shift_magnitude": -1,
                        "severity": 1,
                        "severity_justification": "Minor social effort to initiate conversation",
                        "prefix": "From putting themselves out there,",
                        "description": "feels a slight vulnerability from initiating the conversation"
                    }}
                ]
            }}
        }}

        **CHARACTER-FIRST CHECKLIST BEFORE RESPONDING:**
        1. **Character Authenticity:** Does this action feel true to {proactor.sheet.name}'s personality and background?
        2. **Goal Alignment:** How does this action advance their personal objectives?
        3. **Dialogue Requirement:** If this is a social action, did you include actual quoted dialogue?
        4. **Action Variety:** Is this different from their recent actions? Does it show tactical/emotional evolution?
        5. **Narrative Impact:** Will this create interesting story moments rather than just mechanical exchanges?
        6. **Technical Validation:** Verify all nested objects have both "name" and "value" keys
        7. **Field Completeness:** Confirm all required fields are present and properly formatted
        8. **JSON Structure:** Ensure JSON is properly formatted and parseable

        **RESPONSE FORMAT:**
        - Respond ONLY with valid JSON
        - No explanatory text before or after the JSON
        - No markdown code blocks or formatting
        - Raw JSON object only
        """
        # Enhance prompt with time context if available
        if hasattr(self, 'time_context') and self.time_context:
            prompt = self._enhance_prompt_with_time_context(prompt, self.time_context)
        
        # DEBUG - Prompt length
        try:
            print(f"{Color.SYSTEM}NUA PROACTOR DEBUG: prompt_chars={len(prompt)}{Color.RESET}")
        except Exception:
            pass
        data = self._call_llm_for_json(prompt.strip())

        # SELF-EFFECTS DEBUGGING - Capture raw AI output (decider stays minimal; no normalization here)
        print(f"{Color.SYSTEM}=== SELF-EFFECTS DEBUG START ==={Color.RESET}")
        print(f"{Color.SYSTEM}Raw AI Response Type: {type(data)}{Color.RESET}")
        print(f"{Color.SYSTEM}Raw AI Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}{Color.RESET}")
        if data:
            print(f"{Color.SYSTEM}Raw AI Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}{Color.RESET}")
            if isinstance(data, dict):
                utas_factors = data.get('utas_factors', {})
                print(f"{Color.SYSTEM}UTAS Factors Keys: {list(utas_factors.keys()) if isinstance(utas_factors, dict) else 'Not a dict'}{Color.RESET}")
                
                self_effects_raw = utas_factors.get('self_effects') if isinstance(utas_factors, dict) else None
                print(f"{Color.SYSTEM}Raw self_effects found: {self_effects_raw is not None}{Color.RESET}")
                print(f"{Color.SYSTEM}Raw self_effects type: {type(self_effects_raw)}{Color.RESET}")
                print(f"{Color.SYSTEM}Raw self_effects content: {self_effects_raw}{Color.RESET}")
        else:
            print(f"{Color.SYSTEM}Raw AI Response is None or empty!{Color.RESET}")
        print(f"{Color.SYSTEM}=== SELF-EFFECTS DEBUG END ==={Color.RESET}")
        # Return raw LLM JSON; Interpreter will validate/repair
        return data or {}

    def _enrich_utas_factors_with_actor_data(self, normalized_data: Dict[str, Any], actor: 'Actor') -> None:
        """Enriches UTAS factors with actual values from the actor's sheet."""
        from actor_sheet import SFactorType
        
        if "utas_factors" not in normalized_data:
            return
            
        factors = normalized_data["utas_factors"]
        
        s_trait_name = factors.get("s_trait_to_use")
        if s_trait_name and s_trait_name != "None":
            try:
                # Handle common LLM mistake: SOCIALITY -> SOCIABILITY
                s_trait_upper = s_trait_name.upper()
                if s_trait_upper == "SOCIALITY":
                    s_trait_upper = "SOCIABILITY"
                    factors["s_trait_to_use"] = "SOCIABILITY"  # Fix the data
                    
                s_factor_type = SFactorType[s_trait_upper]
                actual_value = actor.sheet.s_factors.get_factor(s_factor_type)
                factors["s_trait_value"] = actual_value
            except (KeyError, AttributeError) as e:
                # Fallback to STURDINESS if invalid S-trait provided
                print(f"Warning: Invalid S-trait '{s_trait_name}': {e}. Defaulting to STURDINESS.")
                factors["s_trait_to_use"] = "STURDINESS"
                factors["s_trait_value"] = actor.sheet.s_factors.get_factor(SFactorType.STURDINESS)
        else:
            # Fallback to STURDINESS if no S-trait provided
            print(f"Warning: Missing s_trait_to_use in LLM response. Defaulting to STURDINESS.")
            factors["s_trait_to_use"] = "STURDINESS"
            factors["s_trait_value"] = actor.sheet.s_factors.get_factor(SFactorType.STURDINESS)
            
        # Handle reactor-specific fields if present
        if "reactor_reaction_skill" in factors:
            skill_data = factors.get("reactor_reaction_skill", {})
            if isinstance(skill_data, dict) and skill_data.get("name") and skill_data.get("name") != "None":
                skill_name = skill_data["name"]
                actual_skill_value = actor.sheet.skills.get(skill_name, 0)
                skill_data["value"] = actual_skill_value
                factors["skill"] = skill_data
            else:
                factors["skill"] = {"name": "None", "value": 0}
                
            endowment_data = factors.get("reactor_reaction_endowment", {})
            if isinstance(endowment_data, dict) and endowment_data.get("name") and endowment_data.get("name") != "None":
                endowment_name = endowment_data["name"]
                actual_endowment_value = actor.sheet.endowments.get(endowment_name, 0) if actor.sheet.endowments else 0
                endowment_data["value"] = actual_endowment_value
                factors["endowment"] = endowment_data
            else:
                factors["endowment"] = {"name": "None", "value": 0}
                
            supplement_data = factors.get("reactor_reaction_supplement", {})
            if isinstance(supplement_data, dict) and supplement_data.get("name") and supplement_data.get("name") != "None":
                supplement_name = supplement_data["name"]
                actual_supplement_value = 0
                supplement_found = False
                for item in actor.sheet.inventory:
                    if item.name.lower() == supplement_name.lower():
                        actual_supplement_value = item.supplement_bonus
                        supplement_found = True
                        break
                
                if not supplement_found:
                    factors["supplement"] = {"name": "None", "value": 0}
                else:
                    supplement_data["value"] = actual_supplement_value
                    factors["supplement"] = supplement_data
            else:
                factors["supplement"] = {"name": "None", "value": 0}
                
            factors["exchange_type"] = factors.get("reactor_primary_defensive_status_type", "N/A")
            factors["status_to_shift"] = factors.get("reactor_primary_defensive_status_type", "N/A")
            
        else:
            # Handle standard proactor fields
            skill_data = factors.get("skill", {})
            if isinstance(skill_data, dict) and skill_data.get("name") and skill_data.get("name") != "None":
                skill_name = skill_data["name"]
                actual_skill_value = actor.sheet.skills.get(skill_name, 0)
                skill_data["value"] = actual_skill_value
            elif not isinstance(skill_data, dict):
                factors["skill"] = {"name": "None", "value": 0}
                
            endowment_data = factors.get("endowment", {})
            if isinstance(endowment_data, dict) and endowment_data.get("name") and endowment_data.get("name") != "None":
                endowment_name = endowment_data["name"]
                actual_endowment_value = actor.sheet.endowments.get(endowment_name, 0) if actor.sheet.endowments else 0
                endowment_data["value"] = actual_endowment_value
            elif not isinstance(endowment_data, dict):
                factors["endowment"] = {"name": "None", "value": 0}
                
            supplement_data = factors.get("supplement", {})
            if isinstance(supplement_data, dict) and supplement_data.get("name") and supplement_data.get("name") != "None":
                supplement_name = supplement_data["name"]
                actual_supplement_value = 0
                supplement_found = False
                for item in actor.sheet.inventory:
                    if item.name.lower() == supplement_name.lower():
                        actual_supplement_value = item.supplement_bonus
                        supplement_found = True
                        break
                
                if not supplement_found:
                    factors["supplement"] = {"name": "None", "value": 0}
                else:
                    supplement_data["value"] = actual_supplement_value
            elif not isinstance(supplement_data, dict):
                factors["supplement"] = {"name": "None", "value": 0}

    def determine_nua_reaction(self, proactor: 'Actor', proactor_action_data: Dict[str, Any], reactor: 'Actor', context_guidance: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Determines the Non-User-Actor's (NUA) reaction to the proactor's action.
        """
        # Ensure we have the authoritative scene before building prompts
        self._refresh_scene_from_tracker()
        # Analyze proactor's action for immediate escalation assessment
        from llm_agents.nua_context_system import NUAContextTracker
        temp_context = NUAContextTracker("temp_analysis")
        immediate_escalation = temp_context._determine_escalation_from_action(proactor_action_data)
        immediate_action_type = temp_context._classify_action_type(proactor_action_data.get('narrative_description', ''))
        
        print(f"DEBUG REACTOR: Immediate escalation analysis of proactor action: {immediate_escalation.name}")
        print(f"DEBUG REACTOR: Immediate action type: {immediate_action_type.value}")
        
        # Only show NUA character sheets - never expose UA (User Actor) sheets to prevent meta-gaming
        show_reactor_sheet = not getattr(reactor, 'is_user_actor', False)
        reactor_sheet_dict = reactor.sheet.to_dict() if show_reactor_sheet else None
        
        # Check if proactor is a User Actor - if so, don't expose their sheet details
        show_proactor_details = not getattr(proactor, 'is_user_actor', False)

        # Get spatial context for position awareness
        try:
            from agents.spatial_context_helper import get_spatial_context_for_prompt
            spatial_context = get_spatial_context_for_prompt(proactor_name=reactor.sheet.name)
        except Exception:
            spatial_context = ""

        # Enhance context guidance with Four-Mode Narrative Loop guidance if available
        narrative_guidance_section = ""
        if context_guidance and context_guidance.get('narrative_mode'):
            narrative_mode = context_guidance.get('narrative_mode', 'unknown')
            narrative_intent = context_guidance.get('narrative_intent', 'Natural progression')
            narrative_tone = context_guidance.get('narrative_tone', 'Balanced')
            
            narrative_guidance_section = f"""
        **ðŸ“– FOUR-MODE NARRATIVE GUIDANCE:**
        Current Mode: {narrative_mode.title()}
        Intent: {narrative_intent}
        Tone: {narrative_tone}
        
        **MODE-SPECIFIC REACTION BEHAVIOR:**"""
            
            if narrative_mode.lower() == 'roam':
                narrative_guidance_section += """
        - ROAM MODE: React with curiosity and openness
        - Engage in exploratory dialogue or cooperative responses
        - Avoid escalating conflicts unnecessarily
        - Show interest in understanding rather than dominating"""
            elif narrative_mode.lower() == 'spark':
                narrative_guidance_section += """
        - SPARK MODE: React in ways that create opportunities
        - Present counter-offers or alternative approaches
        - Create hooks for further engagement
        - Be purposeful but not overly aggressive"""
            elif narrative_mode.lower() == 'pressure':
                # Check for active mission context
                active_mission = context_guidance.get('active_mission')
                mission_progress = context_guidance.get('mission_progress', 0.0)
                
                if active_mission:
                    narrative_guidance_section += f"""
        - PRESSURE MODE: React to Mission '{active_mission}' (Progress: {int(mission_progress * 100)}%)
        - Your reaction should complicate or advance the mission
        - Create obstacles that test the proactor's commitment to the mission
        - Escalate stakes related to the mission goal
        - Challenge their approach to achieving the mission"""
                else:
                    narrative_guidance_section += """
        - PRESSURE MODE: React with increased stakes
        - Escalate appropriately to create meaningful tension
        - Challenge the proactor's approach or assumptions
        - Create complications that drive the story forward"""
            elif narrative_mode.lower() == 'outcome':
                # Check for completed mission
                active_mission = context_guidance.get('active_mission')
                mission_progress = context_guidance.get('mission_progress', 0.0)
                
                if active_mission and mission_progress >= 1.0:
                    narrative_guidance_section += f"""
        - OUTCOME MODE: React to Mission '{active_mission}' Completion
        - Acknowledge the mission's resolution
        - Deliver rewards, consequences, or both based on how it concluded
        - Show how this mission changed your relationship or situation
        - Be measured and provide closure"""
                else:
                    narrative_guidance_section += """
        - OUTCOME MODE: React with resolution in mind
        - Allow for natural conclusions to emerge
        - Focus on consequences and character growth
        - Be more measured and thoughtful in responses"""

        # Extract UA dialogue weight for matching (tennis ball analogy)
        proactor_dialogue = proactor_action_data.get("dialogue_metadata", {})
        ua_dialogue_weight = proactor_dialogue.get("dialogue_weight", 0)
        ua_can_affect_status = proactor_dialogue.get("can_affect_status", True)
        
        dialogue_guidance = ""
        if ua_dialogue_weight > 0:
            # Get current sympathy level for conversational cooperation
            current_sympathy = reactor.sheet.get_sympathy(proactor.sheet.name) if hasattr(reactor.sheet, 'get_sympathy') else 3
            
            dialogue_guidance = f"""
**💬 CONVERSATIONAL AGENCY & NATURAL FLOW:**
- UA sent {ua_dialogue_weight} dialogue units (~{ua_dialogue_weight * 3} seconds of speech)
- Current Sympathy Level: {current_sympathy}/5 (affects conversational cooperation and engagement)

**YOUR CONVERSATIONAL GOALS AS {reactor.sheet.name}:**
- You have your own interests, topics, and conversational objectives
- You may steer the conversation toward YOUR goals: {reactor.sheet.goals}
- You can ask questions, share information, or deflect based on your personality
- High sympathy ({current_sympathy} >= 4) → More helpful, engaged, willing to share
- Low sympathy ({current_sympathy} <= 2) → Guarded, brief, may redirect or end conversation
- Neutral sympathy (3) → Professional, transactional, measured responses

**NATURAL CONVERSATION PRINCIPLES:**
- Match conversational energy: brief reply to brief input, detailed to detailed
- Build on previous exchanges - reference earlier topics if relevant
- Show personality through speech patterns, word choice, and topics of interest
- You can introduce new topics that interest {reactor.sheet.name}
- You can ask counter-questions or seek clarification
- Conversations should feel organic, not mechanical question-answer loops

**🗣️ ABSOLUTE REQUIREMENT - DIALOGUE MUST CONTAIN SPOKEN WORDS:**
- If UA spoke to you, YOU MUST SPEAK BACK with actual words in quotation marks
- This is NOT optional - your narrative_description MUST include quoted dialogue
- WRONG: "she speaks in a measured tone" ❌ (no actual words!)
- WRONG: "she attempts to brush off the insult with a joke" ❌ (no actual words!)
- WRONG: "Marcus smiles and reciprocates the high five" ❌ (no actual words!)
- RIGHT: "'Hey, Jet! What's up?' Marcus says with a grin, returning the high five" ✅
- RIGHT: "'Oh this old thing? Yeah, management's fashion sense is questionable!' she jokes" ✅
- RIGHT: "'Not bad! Busy morning. How about you?' he asks with a smile" ✅

**FORMAT REQUIREMENT:**
- Start with the quoted dialogue: "'[Exact words]' [name] [action/expression]"
- Include the EXACT WORDS you say in quotation marks FIRST
- Then add any accompanying actions or expressions
- Example: "'Hey there!' she waves enthusiastically" NOT "She waves and greets them"

**DIALOGUE TYPE IN YOUR RESPONSE:**
- **Pure Dialogue Response:** If you're ONLY speaking (no physical action), set dialogue_only=true
  - Example: "'Good! How about you?' he asks" → dialogue_only=true
- **Action + Dialogue Response:** If you're speaking WHILE doing something, set dialogue_only=false
  - Example: "'Get out!' he shouts while pushing them toward the door" → dialogue_only=false
- Include dialogue_only field in your dialogue_metadata

**DIALOGUE AS UTAS ACTION:**
- If UA is trying to persuade/negotiate/deceive → This is a contested SPIRIT/SYMPATHY exchange
- If UA is being casual/phatic → Brief response, no status shift needed
- Your response can ALSO attempt to achieve conversational goals (persuade them, extract info, build rapport)
- Include dialogue_weight estimate in your response (match UA's energy ±1-2 units)

"""
        
        # ═══════════════════════════════════════════════════════════
        # NUA MEMORY RETRIEVAL - Get past interactions with proactor
        # ═══════════════════════════════════════════════════════════
        memory_context = ""
        try:
            from npc_memory_system import get_nua_memory_system
            nua_memory_system = get_nua_memory_system()
            
            if nua_memory_system:
                # Get memories about the proactor
                memory_context_text = nua_memory_system.get_memory_context_for_decision(
                    nua_name=reactor.sheet.name,
                    target_actor=proactor.sheet.name
                )
                
                if memory_context_text and memory_context_text != "No significant memories.":
                    memory_context = f"""
        **🧠 MEMORY CONTEXT - What {reactor.sheet.name} Remembers About {proactor.sheet.name}:**
        {memory_context_text}
        
        **CRITICAL: Use these memories to inform your reaction:**
        - If they threatened you before → Be cautious, defensive, or fearful
        - If they helped you before → Be grateful, cooperative, or friendly
        - If you witnessed them commit violence → Be wary or traumatized
        - If you had significant conversations → Reference past topics or build on them
        - Memories should DIRECTLY influence your emotional state and reaction choice
        
"""
        except Exception as e:
            # Silently fail - memory retrieval shouldn't break decision-making
            pass
        
        # Build remote encounter context for reactions too
        remote_context_reaction = ""
        if context_guidance and context_guidance.get('is_remote_encounter'):
            remote_type = context_guidance.get('remote_encounter_type', 'phone_call').replace('_', ' ').upper()
            remote_context_reaction = f"""

🚨🚨🚨 **ABSOLUTE REQUIREMENT: {remote_type} - HEARING ONLY** 🚨🚨🚨

**YOU ARE ON A PHONE CALL. ONLY YOUR HEARING WORKS.**
- You can HEAR: voice, tone, words, background sounds
- You CANNOT see, touch, smell, or taste anything
- The other person CANNOT see you, so physical actions are meaningless

**MANDATORY FORMAT FOR narrative_description:**
- MUST be: "says '[exact dialogue in quotes]' in a [tone] voice"
- NOTHING ELSE IS ALLOWED

**CORRECT EXAMPLES:**
✅ "says 'I've been worried about you, honey' in a concerned voice"
✅ "says 'Of course! What's going on?' in a warm voice"
✅ "says 'I'm here for you' in a comforting voice"

**ABSOLUTELY FORBIDDEN:**
❌ ANY "while [action]" - FORBIDDEN! (e.g., "while pulling out", "while moving", "while picking up")
❌ "answers the phone" (NO - must have dialogue)
❌ "speaks over the phone" (NO - must have actual quoted words)
❌ "pulling out..." (THEY CANNOT SEE YOU PULLING ANYTHING)
❌ "picks up..." (THEY CANNOT SEE YOU PICKING UP ANYTHING)
❌ "smiles" (THEY CANNOT SEE YOU)
❌ "nods" (THEY CANNOT SEE YOU)
❌ "eyes sparkling..." (THEY CANNOT SEE YOUR EYES)
❌ ANY physical movement or visible expression (THEY CANNOT SEE YOU)

**IF YOU GENERATE ANYTHING OTHER THAN DIALOGUE, THE SYSTEM WILL FAIL.**
"""
        
        # Get worldbuilding context for NPC reaction decision-making
        worldbuilding_context = ""
        if self.rag_system:
            reactor_goals_hint = ""
            try:
                if hasattr(reactor.sheet, 'goals') and reactor.sheet.goals:
                    reactor_goals_hint = " ".join([str(g) for g in reactor.sheet.goals[:3] if g])
            except Exception:
                reactor_goals_hint = ""
            occupation_guidance = self._get_worldbuilding_context(
                query=f"{reactor.sheet.occupation} occupations social role",
                max_tokens=200,
                category_filter=self._get_actor_occupation_category(reactor)
            )
            goals_guidance = self._get_worldbuilding_context(
                query=f"{reactor_goals_hint} goals motivation",
                max_tokens=200,
                category_filter=self._get_actor_goals_category(reactor)
            )
            worldbuilding_context = self._get_worldbuilding_context(
                query=f"{self._get_actor_category_label(reactor)} {reactor.sheet.occupation} {reactor_goals_hint} {self.scene_description[:150]} reaction defense technology era setting",
                max_tokens=300
            )
            if occupation_guidance or goals_guidance:
                worldbuilding_context = "\n\n".join([x for x in [occupation_guidance, goals_guidance, worldbuilding_context] if x])
            if worldbuilding_context:
                worldbuilding_context = f"""
        **WORLDBUILDING CONTEXT (CRITICAL - ACT ACCORDING TO THIS WORLD'S RULES):**
        {worldbuilding_context}
        
        **SETTING ENFORCEMENT:** Your reaction MUST be appropriate for this setting's technology and culture.
        - If medieval: NO modern technology, NO guns, NO phones
        - If futuristic: Technology should match the era
        - If specific time period: Use period-appropriate actions and references
        """
        
        proactor_is_ua = bool(getattr(proactor, 'is_user_actor', False))
        ua_pov_rule = ""
        if proactor_is_ua:
            ua_pov_rule = f"""

🚨 **UA POV RULE (MANDATORY):**
- The PROACTOR is the User Actor.
- In your narrative_description, you MUST refer to the proactor as **you/your** (never she/her/he/him/his).
- Example: "says 'Busy so far—what can I get you?'" or "leans closer and says 'Keep your voice down.'"
"""

        prompt = f"""
        You are the NUA Decision Agent.
{remote_context_reaction}{dialogue_guidance}{memory_context}{worldbuilding_context}
        Your task is to determine a realistic, character-driven reaction for {reactor.sheet.name} to {proactor.sheet.name}'s action. This NUA is a living character with personality, goals, and motivations who can respond with cooperation, neutrality, or opposition based on context and relationships.

        {self._get_actor_long_term_memory_section(reactor, limit=8)}

        **🚨 IMMEDIATE THREAT ASSESSMENT:**
        Proactor's Action Escalation Level: {immediate_escalation.name} ({immediate_escalation.value}/5)
        Proactor's Action Type: {immediate_action_type.value}
        {narrative_guidance_section}
        
        **ESCALATION RESPONSE GUIDELINES:**
        - PEACEFUL (1): Casual response, social interaction
        - TENSE (2): Cautious, alert, ready to defend
        - HOSTILE (3): Aggressive response, intimidation, threats
        - VIOLENT (4): Physical combat, serious defensive measures
        - LETHAL (5): Life-or-death response, maximum force, survival mode
        
        **CHARACTER-DRIVEN REACTION PRINCIPLES:**
        1. **Match Relationship Context:** Consider existing sympathy/hostility and the nature of the interaction
        2. **Embody the Character:** React based on {reactor.sheet.name}'s personality traits, goals, and current emotional state
        3. **Prioritize Authentic Responses:** Consider cooperation, assistance, or neutral responses before defaulting to opposition
        4. **Use Character Goals:** How does this situation help or hinder {reactor.sheet.name}'s objectives?
        5. **Match Escalation Appropriately:** Only escalate to aggression when the situation truly warrants it
        6. **Embrace Relationship Diversity:** NPCs can be helpful, neutral, or challenging based on context and personality

        **REACTION VARIETY GUIDELINES:**
        - **Cooperative:** Assistance, information sharing, alliance building
        - **Neutral:** Professional responses, transactional interactions, boundary setting
        - **Social:** Persuasion, negotiation, conversation, relationship building
        - **Aggressive:** Direct attacks, intimidation, escalation (when escalation warrants it)
        - **Defensive:** Blocks, dodges, protective stances when threatened
        - **Strategic:** Repositioning, creating distance, seeking advantage
        - **Environmental:** Using surroundings, tools, terrain
        - **Psychological:** Mind games, misdirection, emotional manipulation
        - **Opportunistic:** Exploiting weaknesses, turning situations to advantage
        - **Passive/Waiting:** Doing nothing, observing, waiting to see what happens next
          * Valid when: Assessing opponent's action, waiting for them to commit, conserving energy
          * Tactical value: Lets situation develop, gathers more information, avoids premature response
          * Use sparingly: Should feel like a deliberate tactical choice, not indecision
        - **Flee/Escape (CRITICAL):** Attempting to leave the exchange or area
          * Valid when: Overwhelmed, injured (low STAMINA/SPIRIT), outmatched, or mission complete
          * Tactical value: Preserves life/resources, prevents defeat
          * Criteria: High stress, low health, or goal achievement

        **Scenario Context:**
        *   **Scene:** {self.scene_description}
        *   **Proactor (The NUA taking action):** {proactor.sheet.name}
        *   **Reactor (The target of the action):** {reactor.sheet.name}
        {spatial_context}
        {self._get_persistent_context_section(reactor, max_event_lines=10)}
        
        {f'''**RELATIONSHIP CONTEXT:**
        {reactor.sheet.relationship_context}
        ''' if hasattr(reactor.sheet, 'relationship_context') and reactor.sheet.relationship_context else ''}

        {self._get_relationship_dynamics_context(reactor, query=f"relationships factions {reactor.sheet.occupation} {' '.join([str(g) for g in (reactor.sheet.goals or [])[:2] if g])}", max_tokens=250)}
        
        {self._get_historical_context()}

        {f'''**Context Summary (Updated):**
        {context_guidance.get('context_summary')}''' if (context_guidance and context_guidance.get('context_summary')) else ''}

        {f'''**REPAIR NOTE (Fill ONLY missing fields exactly as instructed):**
        {context_guidance.get('repair_note')}''' if (context_guidance and context_guidance.get('repair_note')) else ''}

        **Proactor's Action Details:**
        ```json
        {json.dumps(proactor_action_data, indent=2)}
{{ ... }}
        ```
        
        🚨 **CRITICAL: YOUR REACTION MUST DIRECTLY RESPOND TO WHAT {proactor.sheet.name} JUST SAID/DID** 🚨
        - If they asked a question → Answer it or acknowledge it
        - If they made a statement → Respond to that specific topic
        - If they took an action → React to that specific action
        - DO NOT change the subject or ignore what they said
        - DO NOT generate generic filler dialogue unrelated to their action
        - If the proactor action is primarily DIALOGUE/QUESTIONING, your reaction MUST remain dialogue-focused.
          - Romance/physical intimacy is NOT banned, but it MUST NOT be a non-sequitur.
          - If the proactor asked a normal question (e.g., "How's business?") you MUST answer or acknowledge it first.
          - Only introduce escalation into physical intimacy (kissing, grabbing, pulling close, etc.) if the proactor explicitly initiated that kind of contact in proactor_action_data or the immediately preceding exchange context clearly supports it.

        {f'''**Reactor's Character Sheet:**
        ```json
        {json.dumps(reactor_sheet_dict, indent=2)}
        ```''' if show_reactor_sheet else f'''**Reactor ({reactor.sheet.name}):** [User Actor - sheet hidden for immersion]'''}

        {f'''**PROACTOR INFORMATION ({proactor.sheet.name}):**
        - **Personality Traits:** {proactor.sheet.personality_traits}
        - **Goals:** {proactor.sheet.goals}
        - **Occupation:** {proactor.sheet.occupation}
        - **Observable Behavior:** Based on their recent actions and demeanor''' if show_proactor_details else f'''**PROACTOR INFORMATION ({proactor.sheet.name}):**
        - [User Actor - detailed information hidden for immersion]
        - You can observe their actions and general behavior, but not their internal motivations or stats'''}

        {f'''**CHARACTER ANALYSIS FOR {reactor.sheet.name}:**
        - **Personality Traits:** {reactor.sheet.personality_traits}
        - **Goals:** {reactor.sheet.goals}
        - **Occupation:** {reactor.sheet.occupation}
        - **Strongest Skills:** {sorted(reactor.sheet.skills.items(), key=lambda x: x[1], reverse=True)[:3]}
        - **Current Status:** Consider their current stamina, spirit, and supply levels''' if show_reactor_sheet else f'''**REACTOR ANALYSIS FOR {reactor.sheet.name}:**
        - [User Actor - detailed analysis hidden for immersion]
        - You can observe their general actions and behavior, but not their internal stats or motivations'''}

        **REACTION DECISION PROCESS:**
        1. **Assess Threat Level:** How dangerous/beneficial is the proactor's action to {reactor.sheet.name}?
        2. **Character Response:** What would {reactor.sheet.name} realistically do based on their personality and goals?
        3. **Tactical Choice:** Which approach (aggressive/defensive/social/strategic) fits their skills and situation?
        4. **Resource Management:** What can they afford to spend (stamina/spirit/supply)?

        **Your Task - REACTOR INTERPRETATION (UTAS OBJECTIVE Step 4):**
        Create a character-driven reaction that feels authentic to {reactor.sheet.name}. Consider both immediate tactical response and any secondary effects that align with their personality and objectives.

        **ðŸš¨ CRITICAL: ATTEMPT ONLY - NO OUTCOMES**
        - Describe what {reactor.sheet.name} is TRYING to do, not what happens
        - Do NOT include results, success, failure, or consequences in the narrative
        - Do NOT describe bullets hitting, missing, grazing, or any impact results
        - Do NOT describe whether attacks connect, defenses work, or any outcomes
        - The math will determine if the attempt succeeds or fails
        - Focus ONLY on the character's intention, movement, and effort

        **REACTION COMPONENTS:**
        - **Primary Action:** The main thing {reactor.sheet.name} is attempting (attack, defend, manipulate, etc.)
        - **Skill Selection:** Choose from their actual skills based on the reaction type
        - **Secondary Effects:** Additional consequences that make sense for this character's approach

        **MANDATORY UTAS OUTPUT (REACTOR KEYS ONLY):**
        - Under "utas_factors" include EXACTLY these keys with explicit values (no defaults):
          - "reactor_reaction_description": concise description of the attempted reaction
          - "reactor_reaction_skill": {{"name": "...", "value": 2}}
          - "reactor_reaction_s_trait": one of SWIFTNESS, SOCIABILITY, STURDINESS, SMARTS, SHADOW
          - "reactor_reaction_endowment": {{"name": "None", "value": 0}},
          - "reactor_reaction_supplement": {{"name": "None", "value": 0}}
          - "reactor_primary_defensive_status_type": one of SPIRIT, STAMINA, SUPPLY
          - "status_to_shift": one of SPIRIT, STAMINA, SUPPLY, SYMPATHY
          - "shift_polarity": "Additive" or "Subtractive"
          - "has_secondary_effect": true/false (if true, include all secondary effect justification/target/type fields)
        - Reactors do NOT include "self_effects"; that field is for proactor actions only.

EXACT MINIMAL JSON SHAPE (example values shown; adapt appropriately):
        {{
          "action_noun": "Reciprocate",
          "narrative_description": "{self._get_narrative_format_instruction(context_guidance, proactor)}",
          "utas_factors": {{
            "s_trait_to_use": "SOCIABILITY",
            "skill": {{"name": "Customer Service", "value": 2}},
            "endowment": {{"name": "None", "value": 0}},
            "supplement": {{"name": "None", "value": 0}},
{{ ... }}
            "reactor_reaction_endowment": {{"name": "None", "value": 0}},
            "reactor_reaction_supplement": {{"name": "None", "value": 0}},
            "reactor_primary_defensive_status_type": "SPIRIT"
          }}
        }}
        **POV REQUIREMENT:**
        - If the proactor is the UA: refer to them as "you/your" (never she/her/he/him).
        - Otherwise: write in third person using actor names; NEVER use first person (I, me, my).

        **📖 IMMERSIVE WRITING STYLE - CRITICAL:**
        - Write as if the USER is EXPERIENCING this moment through their senses
        - Use FIRST NAME ONLY after initial introduction (not "Marcus 'DJ Phreak' Holloway" repeatedly)
        - Focus on what the USER sees, hears, and feels
        - WRONG: "Marcus 'DJ Phreak' Holloway smiles and reciprocates Jasper 'Jet' Monroe's high five, his eyes lighting up with a mix of curiosity and interest." ❌ (Narrator voice, full names, distant)
        - RIGHT: "'Hey, Jet! What's up?' Marcus says with a grin, returning the high five with a bit more energy, his eyes lighting up at the unexpected social interaction." ✅ (Immersive, dialogue-first, sensory)
        - Think: What does the USER hear? What do they see? How does it feel?
        - Avoid formal, report-like narration. Make it feel LIVED, not DESCRIBED.

        **CRITICAL FORMATTING REQUIREMENTS:**
        - ALL nested objects (skill, supplement) MUST be JSON objects with "name" and "value" keys
        - ALL numeric values MUST be integers, never strings or text
        - If no skill/supplement applies, use: {{"name": "None", "value": 0}}
        - NEVER return strings where objects are expected

        **CORRECT EXAMPLES:**
        "skill": {{"name": "Defense", "value": 3}}
        "supplement": {{"name": "Shield", "value": 2}}
        "stress_level": 3

        **INCORRECT EXAMPLES TO AVOID:**
        "skill": "Defense"  âŒ (should be object)
        "skill": {{"name": "Defense", "value": "3"}}  âŒ (value should be number)
        "stress_level": "Medium"  âŒ (should be number)

        **IF UNCERTAIN:**
        - For skills: Use {{"name": "None", "value": 0}}
        - For supplements: Use {{"name": "None", "value": 0}}
        - For numeric values: Use appropriate integer (1-5)

        **BEFORE RESPONDING:**
        1. Verify all nested objects have both "name" and "value" keys
        2. Confirm all numeric fields contain integers, not strings
        3. Check that no required field is missing or null
        4. **Confirm `self_effects` is present and contains at least one effect (NEVER empty for proactor actions)**
        5. **Include ALL justification fields:** s_trait_justification, skill_justification, stress_justification, shift_type_justification, shift_polarity_justification, self_effects_justification
        6. **CRITICAL: shift_type MUST be 'Temporary' or 'Lasting' (NOT 'Additive' or 'Subtractive'!)**
        7. **CRITICAL: shift_polarity MUST be 'Additive' or 'Subtractive' (NOT 'Temporary' or 'Lasting'!)**
        8. Ensure JSON is properly formatted and parseable

        {ua_pov_rule}

        **RESPONSE FORMAT:**
        - Respond ONLY with valid JSON
        - No explanatory text before or after the JSON
        - No markdown code blocks or formatting
        - Raw JSON object only
        """
        data = self._call_llm_for_json(prompt.strip())
        # Return raw LLM JSON; Interpreter/Normalizer will validate/repair downstream
        return data or {}

    def determine_inua_reaction(self, proactor: 'Actor', proactor_action_data: Dict[str, Any], reactor: 'Actor') -> Optional[Dict[str, Any]]:
        """
        Determines how an Inanimate Non-User Actor (INUA) reacts to a proactor's action.
        INUAs don't take independent actions - they provide passive resistance based on their properties.
        """
        # Ensure we have the authoritative scene before building prompts
        self._refresh_scene_from_tracker()
        self.logger.log_system(f"Determining INUA reaction for {reactor.sheet.name}...")
        
        import random
        serendipity = random.randint(1, 6) + random.randint(1, 6) - 7
        
        # Build the INUA reaction prompt
        prompt = self._build_inua_reaction_prompt(proactor, proactor_action_data, reactor, serendipity)
        
        # Get LLM response
        response_data = self._call_llm_for_json(prompt)
        if not response_data:
            self.logger.log_system(f"ERROR: Could not get INUA reaction for {reactor.sheet.name}")
            return None
        # Return raw LLM JSON; Interpreter/Normalizer will validate/repair downstream
        self.logger.log_system(f"Successfully determined INUA reaction (raw) for {reactor.sheet.name}")
        return response_data
    
    def _build_inua_reaction_prompt(self, proactor: 'Actor', proactor_action_data: Dict[str, Any], reactor: 'Actor', serendipity: int) -> str:
        """
        Builds the prompt for determining how an INUA reacts to a proactor's action.
        """
        proactor_action = proactor_action_data.get('narrative_description', 'acts')
        
        return f"""
You are determining how an Inanimate Non-User Actor (INUA) responds to a character's action in a simulation.

**Scene Context:**
{self.scene_description}

**Proactor Action:**
{proactor.sheet.name} {proactor_action}

**INUA Being Acted Upon:**
- Name: {reactor.sheet.name}
- Type: {reactor.sheet.occupation}
- Nature: {reactor.sheet.personality_traits.get('internal', 'inanimate')}
- Appearance: {reactor.sheet.personality_traits.get('external', 'static')}
- Skills: {reactor.sheet.skills}
- Components: {[item.name for item in reactor.sheet.inventory]}

**INUA Reaction Guidelines:**
INUAs don't take independent actions - they provide passive resistance or response based on:
1. **Physical Properties**: How sturdy/fragile is it? Does it break, bend, or resist?
2. **Complexity**: Does it have mechanisms, locks, or systems that activate?
3. **Environmental Response**: Does it create hazards, obstacles, or opportunities?
4. **Interaction Skills**: Which of the INUA's skills are relevant to the proactor's approach?

**Examples:**
- Door with lock â†’ Tests lockpicking skill, may jam or open
- Boulder â†’ Tests strength/climbing, may shift or hold firm
- Security system â†’ Tests hacking/stealth, may trigger alarms
- Bridge â†’ Tests balance/engineering, may collapse or hold
**Required Response Format:**
Provide a JSON response with the INUA's passive reaction:

{{
          "action_noun": "Answer",
    "narrative_description": "Maria sees the call incoming from Evelyn 'Eva' Martinez. She picks up the smart tablet and swipes to accept the call. 'Hi Eva, how can I help you today?' Maria says with a friendly tone, ensuring the camera on the tablet is properly aligned to face her.",
    "utas_factors": {{
        "exchange_type": "STAMINA",
        "s_trait_to_use": "{reactor.sheet.get_highest_s_factor_name()}",
        "s_trait_value": "Actual S-Factor value from INUA sheet",
        "skill": {{
{{ ... }}
```
            "value": "Skill difficulty value (1-3)"
        }},
        "endowment": {{
            "name": "None",
            "value": 0
        }},
        "supplement": {{
            "name": "Most relevant component/part from INUA's inventory",
            "value": "Component effectiveness (1-3)"
        }},
        "serendipity": {serendipity},
        "stress_level": 3,
        "status_to_shift": "STAMINA",
        "shift_type": "Temporary",
        "shift_polarity": "Subtractive",
        "self_effects": [
            {{
                "trigger": "Inherent Cost",
                "status_shifted": "STAMINA",
                "shift_magnitude": -1,
                "severity": 1,
                "severity_justification": "Minor wear from interaction",
                "prefix": "From the strain of resisting,",
                "description": "shows signs of wear from the interaction"
            }}
        ]
    }}
}}

**CRITICAL Requirements:**
- INUAs provide RESISTANCE, not active attacks
- Use the INUA's actual skills and components from their sheet
- Self-effects represent wear/damage to the INUA itself
- Shift magnitude reflects how difficult the INUA is to overcome
- Narrative should be passive/reactive, not active
- action_noun should always be "Resist" for INUAs
- exchange_type and status_to_shift should typically be "STAMINA"

Respond with ONLY the JSON object.
        """.strip()
    
    def _enhance_prompt_with_time_context(self, prompt: str, time_context: Dict[str, Any]) -> str:
        """
        Enhance prompt with time-of-day context for narrative consistency.
        
        Args:
            prompt: The base prompt
            time_context: Time context from MasterTimeCoordinator
            
        Returns:
            Enhanced prompt with time information
        """
        if not time_context:
            return prompt
        
        time_of_day = time_context.get('time_of_day')
        atmospheric_desc = time_context.get('atmospheric_description', '')
        lighting = time_context.get('lighting_condition', '')
        current_time = time_context.get('formatted_time', '')
        
        if not time_of_day:
            return prompt
        
        # Convert TimeOfDay enum to readable string
        time_of_day_str = time_of_day.value.replace('_', ' ').title() if hasattr(time_of_day, 'value') else str(time_of_day)
        
        time_enhancement = f"""

**CURRENT TIME CONTEXT:**
- Time: {current_time}
- Time of Day: {time_of_day_str}
- Atmosphere: {atmospheric_desc}
- Lighting: {lighting}

**NARRATIVE TIME CONSISTENCY REQUIRED:**
Ensure the narrative_description field reflects the current time of day. Use appropriate lighting, atmospheric details, and time-appropriate language. Do NOT describe nighttime scenes during daytime or vice versa. The narrative should naturally incorporate the current lighting and atmospheric conditions.
"""
        
        return prompt + time_enhancement
