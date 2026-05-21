"""
Tracker_Agent - Comprehensive UTAS Simulation Data Persistence

This agent captures every aspect of a UTAS simulation session with complete fidelity,
enabling perfect reconstruction of any simulation state and providing comprehensive
historical context that transcends LLM context window limitations.
"""

import json
import os
import re
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from actor_sheet import ActorSheet, SFactorType, StatusType
from actors import Actor, UserActor, NonUserActor
from narrative_utils import get_status_descriptor, get_generic_descriptor
from color_utils import Color
import openrouter_config


def _format_session_actor_display(actor_entry: Dict[str, Any]) -> str:
    try:
        snapshot = actor_entry.get('initial_sheet_snapshot') if isinstance(actor_entry, dict) else None
        if not isinstance(snapshot, dict):
            snapshot = {}

        raw_name = actor_entry.get('name') if isinstance(actor_entry, dict) else None
        actor_type = actor_entry.get('actor_type') if isinstance(actor_entry, dict) else None

        is_user = bool(snapshot.get('is_user_actor')) or (str(actor_type).lower() == 'useractor')

        occupation = snapshot.get('occupation') or ""

        if is_user:
            base = str(raw_name or snapshot.get('name') or 'You')
        else:
            base = snapshot.get('known_as') or snapshot.get('public_description') or 'vessel'

        if occupation:
            return f"{base} ({occupation})"
        return str(base)
    except Exception:
        return "vessel"


class TrackerAgent:
    """
    Comprehensive simulation tracking agent that captures all inputs, outputs,
    and state changes during a UTAS simulation session.
    """
    
    def __init__(self, storage_directory: str = "simulation_data"):
        """
        Initialize the Tracker_Agent with storage configuration.
        
        Args:
            storage_directory: Base directory for storing simulation data
        """
        self.storage_directory = Path(storage_directory)
        self.session_id = str(uuid.uuid4())
        self.session_data = self._initialize_session_structure()
        self.current_scene_id = None
        self.current_exchange_id = None
        self.current_round_id = None
        self.current_turn_id = None
        
        self._create_storage_structure()
        
        self.llm_call_count = 0
        self.total_processing_time = 0.0
    
    def _initialize_session_structure(self) -> Dict[str, Any]:
        """Initialize the complete session data structure."""
        return {
            "simulation_session": {
                "session_id": self.session_id,
                "start_timestamp": datetime.now(timezone.utc).isoformat(),
                "end_timestamp": None,
                "version": "1.0.0",
                "initial_actors": [],
                "scenes": [],
                "session_statistics": {
                    "total_scenes": 0,
                    "total_exchanges": 0,
                    "total_rounds": 0,
                    "total_turns": 0,
                    "total_llm_calls": 0,
                    "total_processing_time": 0.0,
                    "actor_statistics": {}
                },
                "error_log": []
            }
        }
    
    def _create_storage_structure(self):
        """Create the directory structure for data storage."""
        directories = [
            self.storage_directory,
            self.storage_directory / "sessions",
            self.storage_directory / "actors",
            self.storage_directory / "analytics",
            self.storage_directory / "backups"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO 8601 format."""
        return datetime.now(timezone.utc).isoformat()

    @staticmethod
    def _canonicalize_actor_name_for_id(name: str) -> str:
        try:
            if name is None:
                return ""
            t = str(name)
            # Remove parenthetical disambiguators (e.g., "(real name unknown)")
            t = re.sub(r"\s*\([^)]*\)\s*", " ", t)
            # Strip common quote characters (including curly quotes)
            t = t.replace("'", " ").replace('"', " ")
            t = t.replace("‘", " ").replace("’", " ")
            t = t.replace("“", " ").replace("”", " ")
            t = t.strip().lower()
            # Keep only alphanumerics and spaces/underscores
            t = re.sub(r"[^a-z0-9\s_]", " ", t)
            t = re.sub(r"\s+", " ", t).strip()
            t = t.replace(" ", "_")
            t = re.sub(r"_+", "_", t).strip("_")
            return t
        except Exception:
            return ""

    def make_actor_id(self, actor_name: str) -> str:
        slug = self._canonicalize_actor_name_for_id(actor_name)
        return f"actor_{slug}" if slug else "actor_unknown"

    def resolve_actor_id(self, actor_name: str) -> str:
        try:
            target = self._canonicalize_actor_name_for_id(actor_name)
            if not target:
                return self.make_actor_id(actor_name)

            initial_actors = self.session_data.get('simulation_session', {}).get('initial_actors', []) or []
            for a in initial_actors:
                if not isinstance(a, dict):
                    continue
                actor_id = a.get('actor_id') or ''
                snapshot = a.get('initial_sheet_snapshot') if isinstance(a.get('initial_sheet_snapshot'), dict) else {}

                candidates = []
                candidates.append(a.get('name'))
                candidates.append(snapshot.get('name'))
                candidates.append(snapshot.get('canonical_name'))
                candidates.append(snapshot.get('public_description'))
                for aka in (snapshot.get('known_as') or []):
                    candidates.append(aka)

                for c in candidates:
                    if not c:
                        continue
                    if self._canonicalize_actor_name_for_id(c) == target:
                        return actor_id or self.make_actor_id(c)
            return self.make_actor_id(actor_name)
        except Exception:
            return self.make_actor_id(actor_name)

    def _equivalent_actor_ids(self, actor_id: str) -> List[str]:
        """Return candidate actor_id variants for tolerant history lookup."""
        try:
            base = str(actor_id or "").strip()
            if not base:
                return []
            candidates = [base]
            if base.startswith("actor_"):
                raw = base[len("actor_"):]
                norm = self._canonicalize_actor_name_for_id(raw)
                if norm:
                    candidates.append(f"actor_{norm}")
            # Also try normalizing the entire id string (handles curly quotes, etc.)
            norm_full = self._canonicalize_actor_name_for_id(base.replace("actor_", "", 1))
            if norm_full:
                candidates.append(f"actor_{norm_full}")
            # Uniquify while preserving order
            seen = set()
            out = []
            for c in candidates:
                if c not in seen:
                    seen.add(c)
                    out.append(c)
            return out
        except Exception:
            return [actor_id] if actor_id else []
    
    def _serialize_actor_sheet(self, actor: Actor) -> Dict[str, Any]:
        """Serialize an actor sheet to a dictionary for storage."""
        sheet = actor.sheet
        
        # Serialize goal/task manager if available
        goal_task_data = None
        if hasattr(sheet, 'goal_task_manager'):
            try:
                goal_task_data = sheet.goal_task_manager.to_dict()
            except Exception:
                goal_task_data = None
        
        return {
            "name": sheet.name,
            "canonical_name": getattr(sheet, 'canonical_name', None) or sheet.name,
            "known_as": list(getattr(sheet, 'known_as', []) or []),
            "public_description": getattr(sheet, 'public_description', None),
            "occupation": sheet.occupation,
            "affiliation": sheet.affiliation,
            "personality_traits": sheet.personality_traits,
            "goals": sheet.goals,  # Legacy support
            "goal_task_manager": goal_task_data,  # New goal/task system
            "s_factors": {
                "swiftness": sheet.s_factors.get_factor(SFactorType.SWIFTNESS),
                "sociability": sheet.s_factors.get_factor(SFactorType.SOCIABILITY),
                "sturdiness": sheet.s_factors.get_factor(SFactorType.STURDINESS),
                "smarts": sheet.s_factors.get_factor(SFactorType.SMARTS),
                "shadow": sheet.s_factors.get_factor(SFactorType.SHADOW)
            },
            "skills": sheet.skills,
            "endowments": sheet.endowments,
            "statuses": {
                str(status_type.name): {
                    "value": status.value,
                    "max_value": status.max_value,
                    "modifier": status.get_modifier(),
                    "descriptor": get_status_descriptor(status.value)
                } for status_type, status in sheet.statuses.items()
            },
            "sympathy": {
                str(name): {
                    "value": status.value,
                    "max_value": status.max_value,
                    "modifier": status.get_modifier(),
                    "descriptor": get_status_descriptor(status.value)
                } for name, status in sheet.sympathy.items()
            },
            "inventory": [self._serialize_item(item) for item in sheet.inventory],
            "memories": list(sheet.memories) if sheet.memories else [],
            "effects": [
                {
                    "name": str(effect.name),
                    "duration": effect.duration,
                    "effects": {str(status_type.name): value for status_type, value in effect.effects.items()}
                } for effect in sheet.effects
            ],
            "knockout_state": {
                "is_knocked_out": sheet.is_knocked_out(),
                "knockout_turns_remaining": sheet.get_knockout_turns_remaining(),
                "is_dead": sheet.is_dead(),
                "is_defeated": sheet.is_defeated()
            }
        }
    
    def _serialize_item(self, item) -> Dict[str, Any]:
        """Serialize an inventory item to a dictionary for JSON storage."""
        supplement_value = 0
        if hasattr(item, 'supplement_bonus'):
            supplement_value = item.supplement_bonus
        elif hasattr(item, 'supplement'):
            supplement_value = item.supplement
        
        return {
            "name": str(item.name),
            "description": str(item.description),
            "supplement_bonus": supplement_value
        }
    
    
    def start_session(self, initial_actors: List[Actor], session_name: str = None):
        """
        Start a new simulation session with initial actors.
        
        Args:
            initial_actors: List of actors participating in the simulation
            session_name: Optional custom name for the session
        """
        # CRITICAL: Clear actor registry to prevent cross-session sympathy contamination
        from actor_sheet import ActorSheet
        ActorSheet.clear_registry()
        
        if session_name:
            self.session_data["simulation_session"]["session_name"] = session_name.strip()
        for actor in initial_actors:
            actor_data = {
                "actor_id": self.make_actor_id(actor.sheet.name),
                "actor_type": "UserActor" if isinstance(actor, UserActor) else "NonUserActor",
                "name": actor.sheet.name,
                "initial_sheet_snapshot": self._serialize_actor_sheet(actor)
            }
            self.session_data["simulation_session"]["initial_actors"].append(actor_data)
            
            self.session_data["simulation_session"]["session_statistics"]["actor_statistics"][actor_data["actor_id"]] = {
                "turns_as_proactor": 0,
                "turns_as_reactor": 0,
                "successful_actions": 0,
                "failed_actions": 0,
                "status_changes": 0,
                "self_effects_triggered": 0
            }
    
    def end_session(self):
        """End the current simulation session and finalize data."""
        self.session_data["simulation_session"]["end_timestamp"] = self._get_timestamp()
        self.session_data["simulation_session"]["session_statistics"]["total_llm_calls"] = self.llm_call_count
        self.session_data["simulation_session"]["session_statistics"]["total_processing_time"] = self.total_processing_time
        self._save_session_data()
    
    
    def start_scene(self, scene_number: int, scene_data: Dict[str, Any], nua_data: Optional[Dict[str, Any]] = None, scene_description: str = ""):
        """
        Start a new scene in the simulation.
        
        Args:
            scene_number: Sequential scene number
            scene_data: Scene elements from CreatorAgent
            nua_data: Non-User Actor data if present
            scene_description: Narrated scene introduction
        """
        self.current_scene_id = str(uuid.uuid4())
        
        scene_entry = {
            "scene_id": self.current_scene_id,
            "scene_number": scene_number,
            "timestamp": self._get_timestamp(),
            "scene_data": {
                "scene_elements": scene_data,
                "nua_data": nua_data,
                "scene_description": scene_description
            },
            "exchanges": [],
            "scene_conclusion": None
        }
        
        self.session_data["simulation_session"]["scenes"].append(scene_entry)
        self.session_data["simulation_session"]["session_statistics"]["total_scenes"] += 1
    
    def conclude_scene(self, conclusion_type: str, final_narrative: str, next_scene_trigger: Optional[str] = None):
        """
        Conclude the current scene with outcome data.
        
        Args:
            conclusion_type: Type of conclusion (victory, defeat, transition, interrupted)
            final_narrative: Final narrative description
            next_scene_trigger: What triggers the next scene (if any)
        """
        if self.current_scene_id:
            current_scene = self._get_current_scene()
            if current_scene:
                current_scene["scene_conclusion"] = {
                    "conclusion_type": conclusion_type,
                    "final_narrative": final_narrative,
                    "next_scene_trigger": next_scene_trigger
                }
    
    
    def start_exchange(self, exchange_number: int, participants: List[str]):
        """
        Start a new exchange within the current scene.
        
        Args:
            exchange_number: Sequential exchange number within scene
            participants: List of actor IDs participating in the exchange
        """
        self.current_exchange_id = str(uuid.uuid4())
        
        exchange_entry = {
            "exchange_id": self.current_exchange_id,
            "exchange_number": exchange_number,
            "timestamp": self._get_timestamp(),
            "participants": participants,
            "rounds": [],
            "exchange_outcome": None
        }
        
        current_scene = self._get_current_scene()
        if current_scene:
            current_scene["exchanges"].append(exchange_entry)
            self.session_data["simulation_session"]["session_statistics"]["total_exchanges"] += 1
    
    def conclude_exchange(self, winner: Optional[str], final_state: str, scene_transition: bool):
        """
        Conclude the current exchange with outcome data.
        
        Args:
            winner: Actor ID of the winner (if any)
            final_state: Final state (resolved, ongoing, interrupted)
            scene_transition: Whether this triggers a scene transition
        """
        if self.current_exchange_id:
            current_exchange = self._get_current_exchange()
            if current_exchange:
                current_exchange["exchange_outcome"] = {
                    "winner": winner,
                    "final_state": final_state,
                    "scene_transition": scene_transition
                }
    
    
    def start_round(self, round_number: int, initiative_data: Dict[str, Any]):
        """
        Start a new round with initiative data.
        
        Args:
            round_number: Sequential round number
            initiative_data: Complete initiative calculation data
        """
        self.current_round_id = str(uuid.uuid4())
        
        round_entry = {
            "round_id": self.current_round_id,
            "round_number": round_number,
            "timestamp": self._get_timestamp(),
            "initiative_data": initiative_data,
            "turns": []
        }
        
        current_exchange = self._get_current_exchange()
        if current_exchange:
            current_exchange["rounds"].append(round_entry)
            self.session_data["simulation_session"]["session_statistics"]["total_rounds"] += 1
    
    
    def start_turn(self, turn_number: int, proactor: Actor, reactor: Actor):
        """
        Start a new turn and capture pre-turn state snapshots.
        
        Args:
            turn_number: Sequential turn number within round
            proactor: Actor taking the proactive action
            reactor: Actor responding to the action
        """
        self.current_turn_id = str(uuid.uuid4())
        
        turn_entry = {
            "turn_id": self.current_turn_id,
            "turn_number": turn_number,
            "timestamp": self._get_timestamp(),
            "proactor": self.make_actor_id(proactor.sheet.name),
            "reactor": self.make_actor_id(reactor.sheet.name),
            "pre_turn_snapshots": {
                "proactor_sheet": self._serialize_actor_sheet(proactor),
                "reactor_sheet": self._serialize_actor_sheet(reactor)
            },
            "step1_proactor_interpretation": None,
            "step2_proactor_success": None,
            "step3_reactor_interpretation": None,
            "step4_reactor_success": None,
            "step5_exchange_resolution": None,
            "step6_narrative_outcome": None,
            "post_turn_snapshots": None,
            "reporter_output": None
        }
        
        current_round = self._get_current_round()
        if current_round:
            current_round["turns"].append(turn_entry)
            self.session_data["simulation_session"]["session_statistics"]["total_turns"] += 1
    
    def complete_turn(self, proactor: Actor, reactor: Actor, reporter_output: str):
        """
        Complete the current turn with post-turn state snapshots.
        
        Args:
            proactor: Proactor actor for final state capture
            reactor: Reactor actor for final state capture
            reporter_output: Complete formatted turn report
        """
        if self.current_turn_id:
            current_turn = self._get_current_turn()
            if current_turn:
                current_turn["post_turn_snapshots"] = {
                    "proactor_sheet": self._serialize_actor_sheet(proactor),
                    "reactor_sheet": self._serialize_actor_sheet(reactor)
                }
                current_turn["reporter_output"] = {
                    "formatted_output": reporter_output,
                    "display_timestamp": self._get_timestamp()
                }
    
    
    def track_step1_proactor_interpretation(self, agent_type: str, input_data: Dict[str, Any], 
                                          llm_interaction: Dict[str, Any], normalized_output: Dict[str, Any], 
                                          enriched_factors: Dict[str, Any]):
        """Track Step 1: Proactor Action Interpretation."""
        if self.current_turn_id:
            current_turn = self._get_current_turn()
            if current_turn:
                current_turn["step1_proactor_interpretation"] = {
                    "agent_type": agent_type,
                    "input_data": input_data,
                    "llm_interaction": llm_interaction,
                    "normalized_output": normalized_output,
                    "enriched_factors": enriched_factors
                }
                self.llm_call_count += 1
                self.total_processing_time += llm_interaction.get("processing_time", 0.0)
    
    def track_step2_proactor_success(self, calculation_breakdown: Dict[str, Any], attempt_narrative: str):
        """Track Step 2: Proactor Success Calculation."""
        if self.current_turn_id:
            current_turn = self._get_current_turn()
            if current_turn:
                current_turn["step2_proactor_success"] = {
                    "calculation_breakdown": calculation_breakdown,
                    "attempt_narrative": attempt_narrative
                }
    
    def track_step3_reactor_interpretation(self, agent_type: str, input_data: Dict[str, Any], 
                                         llm_interaction: Dict[str, Any], normalized_output: Dict[str, Any], 
                                         enriched_factors: Dict[str, Any]):
        """Track Step 3: Reactor Action Interpretation."""
        if self.current_turn_id:
            current_turn = self._get_current_turn()
            if current_turn:
                current_turn["step3_reactor_interpretation"] = {
                    "agent_type": agent_type,
                    "input_data": input_data,
                    "llm_interaction": llm_interaction,
                    "normalized_output": normalized_output,
                    "enriched_factors": enriched_factors
                }
                self.llm_call_count += 1
                self.total_processing_time += llm_interaction.get("processing_time", 0.0)
    
    def track_step4_reactor_success(self, calculation_breakdown: Dict[str, Any], attempt_narrative: str):
        """Track Step 4: Reactor Success Calculation."""
        if self.current_turn_id:
            current_turn = self._get_current_turn()
            if current_turn:
                current_turn["step4_reactor_success"] = {
                    "calculation_breakdown": calculation_breakdown,
                    "attempt_narrative": attempt_narrative
                }
    
    def track_step5_exchange_resolution(self, exchange_calculation: Dict[str, Any], 
                                      status_shifts: Dict[str, Any], self_effects_applied: List[Dict[str, Any]]):
        """Track Step 5: Exchange Resolution."""
        if self.current_turn_id:
            current_turn = self._get_current_turn()
            if current_turn:
                current_turn["step5_exchange_resolution"] = {
                    "exchange_calculation": exchange_calculation,
                    "status_shifts": status_shifts,
                    "self_effects_applied": self_effects_applied
                }
                
                proactor_id = current_turn["proactor"]
                winner = exchange_calculation.get("winner", "draw")
                
                if winner == "proactor":
                    self.session_data["simulation_session"]["session_statistics"]["actor_statistics"][proactor_id]["successful_actions"] += 1
                elif winner == "reactor":
                    self.session_data["simulation_session"]["session_statistics"]["actor_statistics"][proactor_id]["failed_actions"] += 1
                
                if status_shifts.get("primary_shift"):
                    affected_actor = status_shifts["primary_shift"]["affected_actor"]
                    self.session_data["simulation_session"]["session_statistics"]["actor_statistics"][affected_actor]["status_changes"] += 1
                
                if self_effects_applied:
                    self.session_data["simulation_session"]["session_statistics"]["actor_statistics"][proactor_id]["self_effects_triggered"] += len(self_effects_applied)
    
    def track_step6_narrative_outcome(self, agent_type: str, input_data: Dict[str, Any], 
                                    llm_interaction: Dict[str, Any], final_narrative: str):
        """Track Step 6: Narrative Outcome."""
        if self.current_turn_id:
            current_turn = self._get_current_turn()
            if current_turn:
                current_turn["step6_narrative_outcome"] = {
                    "agent_type": agent_type,
                    "input_data": input_data,
                    "llm_interaction": llm_interaction,
                    "final_narrative": final_narrative
                }
                self.llm_call_count += 1
                self.total_processing_time += llm_interaction.get("processing_time", 0.0)
    
    
    def log_error(self, error_type: str, error_message: str, context: Dict[str, Any], recovery_action: str):
        """
        Log an error that occurred during simulation.
        
        Args:
            error_type: Type/category of the error
            error_message: Detailed error message
            context: Contextual information about when/where the error occurred
            recovery_action: What action was taken to recover from the error
        """
        error_entry = {
            "timestamp": self._get_timestamp(),
            "error_type": error_type,
            "error_message": error_message,
            "context": context,
            "recovery_action": recovery_action
        }
        
        self.session_data["simulation_session"]["error_log"].append(error_entry)
    
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get a summary of the current session."""
        return {
            "session_id": self.session_id,
            "statistics": self.session_data["simulation_session"]["session_statistics"],
            "current_scene": self.current_scene_id,
            "current_exchange": self.current_exchange_id,
            "current_round": self.current_round_id,
            "current_turn": self.current_turn_id
        }
    
    def get_actor_history(self, actor_id: str) -> List[Dict[str, Any]]:
        """Get complete history for a specific actor."""
        history = []

        actor_ids = self._equivalent_actor_ids(actor_id)
        if not actor_ids:
            return history
        
        for scene in self.session_data["simulation_session"]["scenes"]:
            for exchange in scene["exchanges"]:
                for round_data in exchange["rounds"]:
                    for turn in round_data["turns"]:
                        if turn["proactor"] in actor_ids or turn["reactor"] in actor_ids:
                            history.append({
                                "scene_id": scene["scene_id"],
                                "exchange_id": exchange["exchange_id"],
                                "round_id": round_data["round_id"],
                                "turn_id": turn["turn_id"],
                                "role": "proactor" if turn["proactor"] in actor_ids else "reactor",
                                "turn_data": turn
                            })
        
        return history
    
    def record_roam_action(self, actor_id: str, action_data: Dict[str, Any]) -> None:
        """
        Record a standalone ROAM action for an actor (not part of an exchange).
        This allows tracking NUA actions for repetition avoidance.
        
        Args:
            actor_id: The actor identifier (e.g., "actor_john_smith")
            action_data: Dict containing narrative_description, action_type, target, dialogue, time, etc.
        """
        # Initialize roam_actions list if not present
        if "roam_actions" not in self.session_data["simulation_session"]:
            self.session_data["simulation_session"]["roam_actions"] = []
        
        # Add the action with timestamp
        from datetime import datetime
        self.session_data["simulation_session"]["roam_actions"].append({
            "actor_id": actor_id,
            "timestamp": datetime.now().isoformat(),
            "action_data": action_data
        })

        try:
            from context_store import ContextStore, WorldTime
            from spatial_context_system import get_spatial_manager

            spatial = get_spatial_manager(session_id=self.session_id)
            ctx = spatial.get_current_context() if spatial else None
            actor_positions = getattr(ctx, 'actor_positions', None) if ctx else None

            resolved_actor_id = None
            try:
                if actor_positions:
                    actor_name = None
                    try:
                        actor_name = action_data.get('actor_name')
                    except Exception:
                        actor_name = None
                    if actor_name:
                        for aid, apos in actor_positions.items():
                            if getattr(apos, 'actor_name', None) == actor_name:
                                resolved_actor_id = str(aid)
                                break
            except Exception:
                resolved_actor_id = None

            if not resolved_actor_id:
                resolved_actor_id = str(actor_id or '')

            store = ContextStore(Path('simulation_data/context/context.db'))
            location_id = getattr(spatial, 'current_location', None) if spatial else None

            wt = None
            try:
                try:
                    tc = spatial.time_context if spatial else None
                except Exception:
                    tc = None
                gt = None
                if isinstance(tc, dict):
                    gt = tc.get('game_time')
                if gt is not None:
                    wt = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
            except Exception:
                wt = None

            narrative = ''
            try:
                narrative = str(action_data.get('narrative_description') or '').strip()
            except Exception:
                narrative = ''

            if narrative:
                summary = narrative
                if len(summary) > 220:
                    summary = summary[:220] + '…'

                payload = {
                    'actor_id': resolved_actor_id,
                    'actor_ids': [resolved_actor_id],
                    'actor_name': action_data.get('actor_name') or resolved_actor_id,
                    'action_data': action_data,
                }

                event_id = store.log_world_event(
                    session_id=self.session_id,
                    event_type='ROAM_ACTION',
                    summary=summary,
                    location_id=location_id,
                    importance=4,
                    tags=['roam'],
                    payload=payload,
                    world_time=wt,
                )

                store.remember(
                    session_id=self.session_id,
                    actor_id=resolved_actor_id,
                    memory_type='ROAM_ACTION',
                    content=summary,
                    importance=4,
                    source_event_id=event_id,
                    world_time=wt,
                )
        except Exception:
            pass
        
        # Keep only last 50 roam actions to prevent bloat
        if len(self.session_data["simulation_session"]["roam_actions"]) > 50:
            self.session_data["simulation_session"]["roam_actions"] = \
                self.session_data["simulation_session"]["roam_actions"][-50:]
    
    def get_roam_action_history(self, actor_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent ROAM actions for a specific actor.
        
        Args:
            actor_id: The actor identifier
            limit: Maximum number of actions to return
            
        Returns:
            List of action data dicts, most recent first
        """
        if "roam_actions" not in self.session_data["simulation_session"]:
            return []
        
        actor_ids = set(self._equivalent_actor_ids(actor_id))
        actor_actions = [
            action for action in self.session_data["simulation_session"]["roam_actions"]
            if action.get("actor_id") in actor_ids
        ]
        
        # Return most recent first
        return list(reversed(actor_actions[-limit:]))
    
    def get_all_recent_nua_actions(self, exclude_actor_id: str = None, limit: int = 10) -> str:
        """
        Get recent ROAM actions from ALL NUAs for perceptual context.
        These are autonomous actions that happened and can be perceived by the UA.
        
        Args:
            exclude_actor_id: Actor ID to exclude (usually the UA)
            limit: Maximum number of actions to return
            
        Returns:
            Formatted string of recent NUA actions for LLM context
        """
        if "roam_actions" not in self.session_data["simulation_session"]:
            return ""
        
        # Get all NUA actions (excluding the specified actor, usually UA)
        nua_actions = []
        for action in reversed(self.session_data["simulation_session"]["roam_actions"]):
            if exclude_actor_id and action.get("actor_id") == exclude_actor_id:
                continue
            
            action_data = action.get("action_data", {})
            actor_name = action_data.get("actor_name", action.get("actor_id", "Someone"))
            narrative = action_data.get("narrative_description", "")
            
            if narrative:
                # Clean up actor name from ID format
                if actor_name.startswith("actor_"):
                    actor_name = actor_name.replace("actor_", "").replace("_", " ").title()
                
                nua_actions.append(f"- {actor_name}: {narrative[:200]}")
                
                if len(nua_actions) >= limit:
                    break
        
        if not nua_actions:
            return ""
        
        return "**RECENT NUA ACTIONS (what others are doing - include if perceivable):**\n" + "\n".join(nua_actions)
    
    def get_context_for_llm(self, lookback_turns: int = 5) -> str:
        """
        Generate contextual information for LLM prompts based on recent history.
        
        Args:
            lookback_turns: Number of recent turns to include in context
            
        Returns:
            Formatted context string for LLM consumption
        """
        context_parts = []
        
        recent_turns = []
        for scene in reversed(self.session_data["simulation_session"]["scenes"]):
            for exchange in reversed(scene["exchanges"]):
                for round_data in reversed(exchange["rounds"]):
                    for turn in reversed(round_data["turns"]):
                        recent_turns.append(turn)
                        if len(recent_turns) >= lookback_turns:
                            break
                    if len(recent_turns) >= lookback_turns:
                        break
                if len(recent_turns) >= lookback_turns:
                    break
            if len(recent_turns) >= lookback_turns:
                break
        
        if recent_turns:
            context_parts.append("## Recent Simulation History")
            for i, turn in enumerate(reversed(recent_turns)):
                context_parts.append(f"\n### Turn {len(recent_turns) - i}")
                context_parts.append(f"Proactor: {turn['proactor']}")
                context_parts.append(f"Reactor: {turn['reactor']}")
                
                if turn.get("step1_proactor_interpretation"):
                    action_desc = turn["step1_proactor_interpretation"]["normalized_output"].get("action_description", "Unknown action")
                    context_parts.append(f"Action: {action_desc}")
                
                if turn.get("step5_exchange_resolution"):
                    winner = turn["step5_exchange_resolution"]["exchange_calculation"].get("winner", "draw")
                    context_parts.append(f"Outcome: {winner}")
                elif turn.get("step1_proactor_interpretation"):
                    context_parts.append(f"Outcome: [Turn in progress]")
                
                if turn.get("step6_narrative_outcome"):
                    narrative = turn["step6_narrative_outcome"]["final_narrative"]
                    context_parts.append(f"Result: {narrative[:200]}...")
                elif turn.get("step1_proactor_interpretation"):
                    context_parts.append(f"Result: [Action interpreted, awaiting resolution]")
        
        return "\n".join(context_parts)
    
    
    def _make_json_serializable(self, obj, _visited=None, _depth=0):
        """Convert objects to JSON-serializable format with circular reference protection."""
        if _depth > 10:
            return "<max_depth_reached>"
        
        if _visited is None:
            _visited = set()
        
        obj_id = id(obj)
        if obj_id in _visited:
            return "<circular_reference>"
        
        if hasattr(obj, '__dict__'):
            _visited.add(obj_id)
            try:
                result = {key: self._make_json_serializable(value, _visited, _depth + 1) 
                         for key, value in obj.__dict__.items()}
                _visited.remove(obj_id)
                return result
            except:
                _visited.discard(obj_id)
                return "<serialization_error>"
        elif isinstance(obj, dict):
            return {str(key): self._make_json_serializable(value, _visited, _depth + 1) 
                   for key, value in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [self._make_json_serializable(item, _visited, _depth + 1) for item in obj]
        elif hasattr(obj, 'name') and hasattr(obj, 'value'):
            return str(obj.name)
        elif hasattr(obj, 'name'):
            return str(obj.name)
        elif callable(obj):
            return f"<function:{obj.__name__ if hasattr(obj, '__name__') else 'unknown'}>"
        elif isinstance(obj, (str, int, float, bool, type(None))):
            return obj
        else:
            return f"<non_serializable:{type(obj).__name__}>"
    
    def _save_session_data(self):
        """Save the current session data to disk with safe JSON serialization."""
        session_file = self.storage_directory / "sessions" / f"session_{self.session_id}.json"
        
        try:
            # Ensure the sessions directory exists
            session_file.parent.mkdir(parents=True, exist_ok=True)
            
            serializable_data = self._make_json_serializable(self.session_data)
            
            with open(session_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_data, f, indent=2, ensure_ascii=False)
            
            print(f"{Color.SUCCESS}💾 WORLD SAVED: {session_file}{Color.RESET}")
            self._update_session_index()
            
        except Exception as e:
            print(f"ERROR: Failed to save session data: {str(e)}")
            import traceback
            traceback.print_exc()
    
    def auto_save(self):
        """Perform an automatic save of current session data."""
        self._save_session_data()
    
    # === SaveCoordinator integration points ===
    def save_session_state(self, combined_data: Dict[str, Any]) -> None:
        """Persist a generic snapshot of current runtime state.
        The combined_data is stored under simulation_session.runtime_state and the session file is saved.
        """
        # NOTE: runtime_state['available_npcs'] is reserved for serialized NPC sheets
        # (list of dicts with sheet_data). Some callers were sending a list of NPC names
        # under the same key which breaks load_available_npcs() on resume.
        # We defensively sanitize here to avoid clobbering the serialized structure.
        data = dict(combined_data or {})
        try:
            av = data.get('available_npcs')
            if isinstance(av, list):
                is_serialized = bool(av) and all(isinstance(x, dict) and ('sheet_data' in x) for x in av)
                if not is_serialized:
                    # Preserve the informational name list (if that's what it is), but don't overwrite
                    # the serialized NPC payload used for actual resume.
                    if all(isinstance(x, str) for x in av):
                        data['available_npc_names'] = list(av)
                    data.pop('available_npcs', None)
        except Exception:
            pass
        try:
            self.session_data.setdefault('simulation_session', {}).setdefault('runtime_state', {}).update(data)
        except Exception:
            # Ensure we don't break on unexpected structures
            self.session_data.setdefault('simulation_session', {})['runtime_state'] = data
        self._save_session_data()

    def save_scene_transition(self, combined_data: Dict[str, Any]) -> None:
        """Persist information specific to scene transitions and save session."""
        sim = self.session_data.setdefault('simulation_session', {})
        sim['last_scene_transition'] = combined_data or {}
        # If a scene_description was provided, ensure current scene holds it
        desc = (combined_data or {}).get('scene_description')
        if desc and self.current_scene_id:
            current_scene = self._get_current_scene()
            if current_scene:
                current_scene.setdefault('scene_data', {}).setdefault('scene_description', desc)
        self._save_session_data()

    # === Authoritative scene context (single source of truth) ===
    def set_current_scene(self, scene_description: str, location_label: Optional[str] = None) -> None:
        """
        Persist the authoritative current scene description and optional location label
        to runtime_state so all subsystems can read the same value.
        """
        sim = self.session_data.setdefault('simulation_session', {})
        runtime = sim.setdefault('runtime_state', {})
        if scene_description:
            runtime['scene_description'] = scene_description
            try:
                if self.current_scene_id:
                    current_scene = self._get_current_scene()
                    if current_scene:
                        current_scene.setdefault('scene_data', {})['scene_description'] = scene_description
            except Exception:
                pass
        if location_label is not None:
            runtime['current_location'] = location_label
        self._save_session_data()

    def get_current_scene(self) -> Dict[str, Any]:
        """
        Return the latest authoritative scene context with keys:
        - scene_description: str
        - current_location: str (optional)
        """
        sim = self.session_data.get('simulation_session', {})
        runtime = sim.get('runtime_state', {}) or {}
        return {
            'scene_description': runtime.get('scene_description', ''),
            'current_location': runtime.get('current_location')
        }
    
    def save_available_npcs(self, available_npcs: List[Actor]) -> None:
        """
        Persist available NUAs to runtime_state for session continuity.
        
        Args:
            available_npcs: List of NUA actors currently in the scene
        """
        sim = self.session_data.setdefault('simulation_session', {})
        runtime = sim.setdefault('runtime_state', {})
        
        # Serialize each NUA
        serialized_npcs = []
        for npc in available_npcs:
            npc_data = {
                "actor_type": "NonUserActor" if not getattr(npc, 'is_inanimate', False) else "InanimateNonUserActor",
                "sheet_data": self._serialize_actor_sheet(npc)
            }
            serialized_npcs.append(npc_data)
        
        runtime['available_npcs'] = serialized_npcs
        self._save_session_data()
    
    def load_available_npcs(self) -> Optional[List[Actor]]:
        """
        Load available NUAs from runtime_state.
        
        Returns:
            List of restored NUA actors, or None if no NUAs saved
        """
        try:
            sim = self.session_data.get('simulation_session', {})
            runtime = sim.get('runtime_state', {}) or {}
            serialized_npcs = runtime.get('available_npcs', [])
            
            if not serialized_npcs:
                return None
            
            restored_npcs = []
            for npc_data in serialized_npcs:
                actor_type = npc_data.get('actor_type', 'NonUserActor')
                sheet_data = npc_data.get('sheet_data', {})
                
                restored_npc = self._deserialize_actor_sheet(sheet_data, actor_type)
                restored_npcs.append(restored_npc)
            
            return restored_npcs
            
        except Exception as e:
            self.log_error("NUALoadError", f"Failed to load available NUAs: {str(e)}", 
                         {"runtime_state": str(self.session_data.get('simulation_session', {}).get('runtime_state', {}))}, 
                         "Return None, NUAs will need to be regenerated")
            return None
    
    def record_nua_death(self, nua_actor: Actor, cause_of_death: str, killer_name: str = None) -> None:
        """
        Record NUA death for permanent tracking and memory consistency.
        
        Args:
            nua_actor: The NUA actor who died
            cause_of_death: Description of how they died
            killer_name: Optional name of who killed them
        """
        sim = self.session_data.setdefault('simulation_session', {})
        runtime = sim.setdefault('runtime_state', {})
        
        # Initialize deceased NUAs list if not exists
        if 'deceased_nuas' not in runtime:
            runtime['deceased_nuas'] = []
        
        # Record death with full state snapshot
        death_record = {
            "name": nua_actor.sheet.name,
            "occupation": nua_actor.sheet.occupation,
            "cause_of_death": cause_of_death,
            "killer": killer_name,
            "timestamp": self._get_timestamp(),
            "final_state": self._serialize_actor_sheet(nua_actor),
            "location": runtime.get('current_location', 'Unknown'),
            "scene_description": runtime.get('scene_description', '')[:200]  # First 200 chars
        }
        
        runtime['deceased_nuas'].append(death_record)
        
        # Remove from available NPCs if present
        available_npcs = runtime.get('available_npcs', [])
        runtime['available_npcs'] = [
            npc for npc in available_npcs 
            if npc.get('sheet_data', {}).get('name') != nua_actor.sheet.name
        ]
        
        self._save_session_data()
        print(f"[DEATH] Recorded death of {nua_actor.sheet.name}: {cause_of_death}")
    
    def get_deceased_nuas(self) -> List[Dict[str, Any]]:
        """
        Get list of all deceased NUAs in this session.
        
        Returns:
            List of death records with full state snapshots
        """
        sim = self.session_data.get('simulation_session', {})
        runtime = sim.get('runtime_state', {}) or {}
        return runtime.get('deceased_nuas', [])
    
    def is_nua_alive(self, nua_name: str) -> bool:
        """
        Check if a NUA is still alive (not in deceased list).
        
        Args:
            nua_name: Name of the NUA to check
            
        Returns:
            True if alive, False if deceased
        """
        deceased = self.get_deceased_nuas()
        return not any(record['name'] == nua_name for record in deceased)
    
    def get_nua_state_history(self, nua_name: str) -> Optional[Dict[str, Any]]:
        """
        Get the last known state of a NUA (alive or deceased).
        
        Args:
            nua_name: Name of the NUA
            
        Returns:
            State record with full actor sheet, or None if never encountered
        """
        # Check if deceased
        deceased = self.get_deceased_nuas()
        for record in deceased:
            if record['name'] == nua_name:
                return {
                    'status': 'deceased',
                    'state': record['final_state'],
                    'death_info': {
                        'cause': record['cause_of_death'],
                        'killer': record.get('killer'),
                        'timestamp': record['timestamp'],
                        'location': record['location']
                    }
                }
        
        # Check if currently alive
        sim = self.session_data.get('simulation_session', {})
        runtime = sim.get('runtime_state', {}) or {}
        available_npcs = runtime.get('available_npcs', [])
        
        for npc_data in available_npcs:
            sheet_data = npc_data.get('sheet_data', {})
            if sheet_data.get('name') == nua_name:
                return {
                    'status': 'alive',
                    'state': sheet_data,
                    'location': runtime.get('current_location', 'Unknown')
                }
        
        return None  # Never encountered

    def save_round_completion(self, combined_data: Dict[str, Any]) -> None:
        """Persist information when a round completes (encounter mode) and save session."""
        sim = self.session_data.setdefault('simulation_session', {})
        sim['last_round_completion'] = combined_data or {}
        self._save_session_data()

    def save_final_session_state(self, combined_data: Dict[str, Any]) -> None:
        """Persist a final snapshot then close the session."""
        sim = self.session_data.setdefault('simulation_session', {})
        sim['final_snapshot'] = combined_data or {}
        # End session performs the save
        self.end_session()

    def get_runtime_resume_state(self) -> Optional[Dict[str, Any]]:
        """Return the last saved runtime state snapshot if available."""
        try:
            sim = self.session_data.get('simulation_session', {})
            state = sim.get('runtime_state') or sim.get('final_snapshot')
            if isinstance(state, dict) and state:
                return state
            return None
        except Exception:
            return None

    def load_session(self, session_id: str) -> bool:
        """
        Load a previous session from disk.
        
        Args:
            session_id: ID of the session to load
            
        Returns:
            True if successful, False otherwise
        """
        session_file = self.storage_directory / "sessions" / f"session_{session_id}.json"
        
        if session_file.exists():
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    self.session_data = json.load(f)
                    self.session_id = session_id
                    return True
            except Exception as e:
                self.log_error("LoadError", f"Failed to load session {session_id}: {str(e)}", 
                             {"session_file": str(session_file)}, "Continue with current session")
                return False
        return False
    
    def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions with metadata using fast index lookup.
        
        Returns:
            List of session metadata dictionaries
        """
        index_file = self.storage_directory / "session_index.json"
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index = json.load(f)

                # Normalize index structure: prefer dict-of-dicts; accept list as legacy format
                if isinstance(index, dict):
                    raw_entries: List[Any] = list(index.values())
                elif isinstance(index, list):
                    raw_entries = index
                else:
                    raw_entries = []

                def coerce_meta(entry: Any) -> Optional[Dict[str, Any]]:
                    """Coerce a generic JSON entry to a session metadata dict if possible."""
                    if isinstance(entry, dict):
                        return entry
                    if isinstance(entry, list):
                        # Some legacy writers stored a single dict inside a list
                        for item in entry:
                            if isinstance(item, dict):
                                return item
                        return None
                    return None

                sessions: List[Dict[str, Any]] = []
                for entry in raw_entries:
                    meta = coerce_meta(entry)
                    if not meta:
                        continue
                    ts = meta.get('start_timestamp')
                    if not ts:
                        continue
                    sessions.append({
                        'session_id': meta.get('session_id', 'unknown'),
                        'session_name': meta.get('session_name', ''),
                        'start_timestamp': ts,
                        'end_timestamp': meta.get('end_timestamp'),
                        'scene_count': meta.get('scene_count', 0),
                        'actors': meta.get('actors', []),
                        'actors_display': meta.get('actors_display', []),
                        'status': meta.get('status', 'active'),
                        'total_exchanges': meta.get('total_exchanges', 0)
                    })

                # Backfill actors_display for legacy indexes (avoid leaking true names in the menu)
                try:
                    any_backfilled = False
                    for s in sessions:
                        if s.get('actors_display'):
                            continue
                        sid = s.get('session_id')
                        if not sid or sid == 'unknown':
                            continue
                        session_file = self.storage_directory / "sessions" / f"session_{sid}.json"
                        if not session_file.exists():
                            continue
                        try:
                            with open(session_file, 'r', encoding='utf-8') as sf:
                                session_data = json.load(sf)
                            sim_session = session_data.get('simulation_session')
                            if not isinstance(sim_session, dict):
                                continue
                            initial_actors = sim_session.get('initial_actors', [])
                            if not isinstance(initial_actors, list):
                                continue
                            s['actors_display'] = [_format_session_actor_display(a) for a in initial_actors]
                            any_backfilled = True

                            # Persist back into index if possible (dict-of-dicts index format)
                            try:
                                if isinstance(index, dict) and sid in index and isinstance(index[sid], dict):
                                    index[sid]['actors_display'] = s['actors_display']
                            except Exception:
                                pass
                        except Exception:
                            continue

                    if any_backfilled and isinstance(index, dict):
                        try:
                            with open(index_file, 'w', encoding='utf-8') as wf:
                                json.dump(index, wf, indent=2, ensure_ascii=False)
                        except Exception:
                            pass
                except Exception:
                    pass

                # Safe sort by start_timestamp (missing becomes empty string)
                sessions.sort(key=lambda x: x.get('start_timestamp', ''), reverse=True)
                return sessions
            except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                self.log_error("IndexLoadError", f"Failed to load session index: {str(e)}", 
                             {"index_file": str(index_file)}, "Falling back to file scanning")
        
        sessions = []
        sessions_dir = self.storage_directory / "sessions"
        
        if not sessions_dir.exists():
            return sessions
        
        for session_file in sessions_dir.glob("session_*.json"):
            try:
                with open(session_file, 'r', encoding='utf-8') as f:
                    session_data = json.load(f)
                
                # Extract session metadata - fail if critical data is missing
                sim_session = session_data.get('simulation_session')
                if not sim_session:
                    raise ValueError(f"Session file {session_file} missing 'simulation_session' data")
                
                session_id = sim_session.get('session_id')
                start_timestamp = sim_session.get('start_timestamp')
                if not session_id or not start_timestamp:
                    raise ValueError(f"Session file {session_file} missing critical metadata (session_id or start_timestamp)")
                
                metadata = {
                    'session_id': session_id,
                    'start_timestamp': start_timestamp,
                    'end_timestamp': sim_session.get('end_timestamp'),
                    'scene_count': len(sim_session.get('scenes', [])),
                    'actors': [actor['name'] for actor in sim_session.get('initial_actors', []) if 'name' in actor],
                    'actors_display': [_format_session_actor_display(a) for a in sim_session.get('initial_actors', [])],
                    'status': 'completed' if sim_session.get('end_timestamp') else 'active',
                    'total_exchanges': sim_session.get('session_statistics', {}).get('total_exchanges', 0)
                }
                sessions.append(metadata)
                
            except (json.JSONDecodeError, KeyError, FileNotFoundError, ValueError) as e:
                self.log_error("SessionFileCorruption", f"Corrupted session file {session_file}: {str(e)}", 
                             {"session_file": str(session_file)}, "Session excluded from listing")
                continue
        
        sessions.sort(key=lambda x: x.get('start_timestamp', ''), reverse=True)
        
        self._rebuild_session_index(sessions)
        
        return sessions
    
    def _update_session_index(self):
        """Update the session index with current session metadata and clean orphaned entries."""
        index_file = self.storage_directory / "session_index.json"
        sessions_dir = self.storage_directory / "sessions"
        
        index = {}
        
        if sessions_dir.exists():
            for session_file in sessions_dir.glob("session_*.json"):
                try:
                    with open(session_file, 'r', encoding='utf-8') as f:
                        session_data = json.load(f)
                    
                    sim_session = session_data.get('simulation_session')
                    if not sim_session:
                        continue
                    
                    session_id = sim_session.get('session_id')
                    start_timestamp = sim_session.get('start_timestamp')
                    if not session_id or not start_timestamp:
                        continue  # Skip files with missing critical data
                    
                    index[session_id] = {
                        'session_id': session_id,
                        'session_name': sim_session.get('session_name', ''),
                        'start_timestamp': start_timestamp,
                        'end_timestamp': sim_session.get('end_timestamp'),
                        'scene_count': len(sim_session.get('scenes', [])),
                        'actors': [actor['name'] for actor in sim_session.get('initial_actors', []) if 'name' in actor],
                        'actors_display': [_format_session_actor_display(a) for a in sim_session.get('initial_actors', [])],
                        'status': 'completed' if sim_session.get('end_timestamp') else 'active',
                        'total_exchanges': sim_session.get('session_statistics', {}).get('total_exchanges', 0),
                        'last_updated': self._get_timestamp()
                    }
                except (json.JSONDecodeError, FileNotFoundError, PermissionError) as e:
                    self.log_error("IndexRebuildError", f"Failed to read session file {session_file}: {str(e)}", 
                                 {"session_file": str(session_file)}, "Skipping file")
                    continue
        
        if hasattr(self, 'session_id') and self.session_id and hasattr(self, 'session_data'):
            sim_session = self.session_data.get('simulation_session')
            if sim_session and sim_session.get('start_timestamp'):
                index[self.session_id] = {
                    'session_id': self.session_id,
                    'session_name': sim_session.get('session_name', ''),
                    'start_timestamp': sim_session.get('start_timestamp'),
                    'end_timestamp': sim_session.get('end_timestamp'),
                    'scene_count': len(sim_session.get('scenes', [])),
                    'actors': [actor['name'] for actor in sim_session.get('initial_actors', []) if 'name' in actor],
                    'actors_display': [_format_session_actor_display(a) for a in sim_session.get('initial_actors', [])],
                    'status': 'completed' if sim_session.get('end_timestamp') else 'active',
                    'total_exchanges': sim_session.get('session_statistics', {}).get('total_exchanges', 0),
                    'last_updated': self._get_timestamp()
                }
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    
    def _rebuild_session_index(self, sessions: List[Dict[str, Any]]):
        """Rebuild the entire session index from session list."""
        index_file = self.storage_directory / "session_index.json"
        
        index = {}
        for session in sessions:
            session_id = session.get('session_id')
            if session_id and session_id != 'unknown':
                index[session_id] = session
        
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)
    
    def display_session_menu(self) -> Optional[str]:
        """
        Display an interactive session selection menu.
        
        Returns:
            Selected session ID, None for new session, or 'quit' to exit
        """
        from color_utils import Color
        
        sessions = self.list_sessions()
        
        print(f"\n{Color.HEADER}=== UTAS Session Manager ==={Color.RESET}")
        print(f"{Color.SYSTEM}Available Sessions:{Color.RESET}")
        
        if not sessions:
            print(f"{Color.WARNING}No existing sessions found.{Color.RESET}")
            print(f"{Color.SYSTEM}Starting new session...{Color.RESET}")
            return None
        
        for i, session in enumerate(sessions, 1):
            status_color = Color.SUCCESS if session['status'] == 'active' else Color.SYSTEM
            session_name = session.get('session_name', '')
            
            if session_name:
                print(f"{Color.SYSTEM}{i:2d}.{Color.RESET} {Color.HEADER}{session_name}{Color.RESET} {status_color}({session['session_id'][:8]}...){Color.RESET}")
            else:
                print(f"{Color.SYSTEM}{i:2d}.{Color.RESET} {status_color}{session['session_id'][:8]}...{Color.RESET}")
            
            print(f"     Created: {session['start_timestamp'][:19].replace('T', ' ')}")
            actor_line = session.get('actors_display') or session.get('actors') or []
            print(f"     Actors: {', '.join([a for a in actor_line if a])}")
            print(f"     Progress: {session['scene_count']} scenes, {session['total_exchanges']} exchanges")
            print(f"     Status: {status_color}{session['status']}{Color.RESET}")
            print()
        
        print(f"{Color.SYSTEM}Options:{Color.RESET}")
        print(f"{Color.SYSTEM}  1-{len(sessions)}: Load existing session{Color.RESET}")
        print(f"{Color.SYSTEM}  n: Create new session{Color.RESET}")
        print(f"{Color.SYSTEM}  d: Delete a session{Color.RESET}")
        print(f"{Color.SYSTEM}  q: Quit{Color.RESET}")
        
        while True:
            choice = input(f"\n{Color.INPUT}Enter your choice: {Color.RESET}").strip().lower()
            
            if choice == 'q':
                return 'quit'
            elif choice == 'n':
                return None
            elif choice == 'd':
                self._handle_session_deletion(sessions)
                return self.display_session_menu()
            elif choice.isdigit():
                session_index = int(choice) - 1
                if 0 <= session_index < len(sessions):
                    return sessions[session_index]['session_id']
                else:
                    print(f"{Color.ERROR}Invalid session number. Please try again.{Color.RESET}")
            else:
                print(f"{Color.ERROR}Invalid choice. Please try again.{Color.RESET}")
    
    def _handle_session_deletion(self, sessions: List[Dict[str, Any]]):
        """Handle session deletion workflow."""
        from color_utils import Color
        
        print(f"\n{Color.WARNING}=== Delete Session ==={Color.RESET}")
        
        for i, session in enumerate(sessions, 1):
            print(f"{Color.SYSTEM}{i:2d}.{Color.RESET} {session['session_id'][:8]}... "
                  f"({session['start_timestamp'][:19].replace('T', ' ')})")
        
        choice = input(f"\n{Color.INPUT}Enter session number to delete (or 'c' to cancel): {Color.RESET}").strip()
        
        if choice.lower() == 'c':
            return
        
        if choice.isdigit():
            session_index = int(choice) - 1
            if 0 <= session_index < len(sessions):
                session_id = sessions[session_index]['session_id']
                confirm = input(f"{Color.WARNING}Are you sure you want to delete session {session_id[:8]}...? (y/N): {Color.RESET}").strip().lower()
                if confirm == 'y':
                    self.delete_session(session_id)
                else:
                    print(f"{Color.SYSTEM}Deletion cancelled.{Color.RESET}")
            else:
                print(f"{Color.ERROR}Invalid session number.{Color.RESET}")
        else:
            print(f"{Color.ERROR}Invalid input.{Color.RESET}")
    
    def delete_session(self, session_id: str) -> bool:
        """
        Delete a session permanently.
        
        Args:
            session_id: The session ID to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        from color_utils import Color
        
        session_file = self.storage_directory / "sessions" / f"session_{session_id}.json"
        
        if not session_file.exists():
            print(f"{Color.WARNING}Session file {session_id} not found on disk{Color.RESET}")
            print(f"{Color.SYSTEM}Cleaning up session index...{Color.RESET}")
            self._update_session_index()
            print(f"{Color.SUCCESS}✓ Session index cleaned up{Color.RESET}")
            return True
        
        try:
            session_file.unlink()
            self._update_session_index()
            print(f"{Color.SUCCESS}✓ Session {session_id} deleted successfully{Color.RESET}")
            return True
        except OSError as e:
            print(f"{Color.ERROR}✗ Error deleting session {session_id}: {e}{Color.RESET}")
            return False
    
    def restore_actors_from_session(self) -> Optional[List[Actor]]:
        """
        Restore actors from the current loaded session data.
        
        Returns:
            List of restored actors or None if failed
        """
        try:
            initial_actors = self.session_data.get('simulation_session', {}).get('initial_actors', [])
            
            if not initial_actors:
                return None
            
            restored_actors = []
            for actor_data in initial_actors:
                actor_sheet_data = actor_data.get('initial_sheet_snapshot', {})
                actor_type = actor_data.get('actor_type', 'UserActor')
                
                restored_actor = self._deserialize_actor_sheet(actor_sheet_data, actor_type)
                restored_actors.append(restored_actor)
            
            return restored_actors
            
        except Exception as e:
            self.log_error("ActorRestoreError", f"Failed to restore actors: {str(e)}", 
                         {"session_data": str(self.session_data)}, "Use default actors")
            return None
    
    def _deserialize_actor_sheet(self, sheet_data: Dict[str, Any], actor_type: str) -> Actor:
        """Deserialize actor sheet data back to an Actor object."""
        from actor_sheet import ActorSheet, SFactors, Item, StatusType, SFactorType
        from actors import UserActor, NonUserActor
        
        s_factors_data = sheet_data.get('s_factors', {})
        s_factors = SFactors(
            swiftness=s_factors_data.get('swiftness', 1),
            sociability=s_factors_data.get('sociability', 1),
            sturdiness=s_factors_data.get('sturdiness', 1),
            smarts=s_factors_data.get('smarts', 1),
            shadow=s_factors_data.get('shadow', 1)
        )
        
        inventory = []
        for item_data in sheet_data.get('inventory', []):
            item = Item(
                name=item_data.get('name', ''),
                description=item_data.get('description', ''),
                supplement_bonus=item_data.get('supplement_bonus', 0)
            )
            inventory.append(item)
        
        actor_sheet = ActorSheet(
            name=sheet_data.get('name', 'Unknown'),
            canonical_name=sheet_data.get('canonical_name') or sheet_data.get('name', 'Unknown'),
            known_as=sheet_data.get('known_as') or [],
            public_description=sheet_data.get('public_description'),
            s_factors=s_factors,
            skills=sheet_data.get('skills', {}),
            personality_traits=sheet_data.get('personality_traits', {}),
            goals=sheet_data.get('goals', []),
            inventory=inventory,
            occupation=sheet_data.get('occupation', ''),
            affiliation=sheet_data.get('affiliation', ''),
            endowments=sheet_data.get('endowments', {}),
            memories=list(sheet_data.get('memories', []))
        )
        
        for status_name, status_data in sheet_data.get('statuses', {}).items():
            try:
                status_type = StatusType[status_name]
                if status_type in actor_sheet.statuses:
                    actor_sheet.statuses[status_type].value = status_data.get('value', 0)
                    actor_sheet.statuses[status_type].max_value = status_data.get('max_value', 10)
            except KeyError:
                continue
        
        if actor_type == 'UserActor':
            return UserActor(actor_sheet)
        else:
            return NonUserActor(actor_sheet)
    
    
    def _get_current_scene(self) -> Optional[Dict[str, Any]]:
        """Get the current scene data."""
        if self.current_scene_id:
            for scene in self.session_data["simulation_session"]["scenes"]:
                if scene["scene_id"] == self.current_scene_id:
                    return scene
        return None
    
    def _get_current_exchange(self) -> Optional[Dict[str, Any]]:
        """Get the current exchange data."""
        if self.current_exchange_id:
            current_scene = self._get_current_scene()
            if current_scene:
                for exchange in current_scene["exchanges"]:
                    if exchange["exchange_id"] == self.current_exchange_id:
                        return exchange
        return None
    
    def _get_current_round(self) -> Optional[Dict[str, Any]]:
        """Get the current round data."""
        if self.current_round_id:
            current_exchange = self._get_current_exchange()
            if current_exchange:
                for round_data in current_exchange["rounds"]:
                    if round_data["round_id"] == self.current_round_id:
                        return round_data
        return None
    
    def _get_current_turn(self) -> Optional[Dict[str, Any]]:
        """Get the current turn data."""
        if self.current_turn_id:
            current_round = self._get_current_round()
            if current_round:
                for turn in current_round["turns"]:
                    if turn["turn_id"] == self.current_turn_id:
                        return turn
        return None
