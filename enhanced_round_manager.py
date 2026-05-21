"""
Enhanced Round Manager for Multi-Actor UTAS Simulation

This system replaces the original RoundManager to handle unlimited actors
using the MultiActorManager for scalable turn order and initiative management.
"""

import random
from typing import List, Dict, Any, Optional, Tuple
from actors import UserActor, NonUserActor, InanimateNonUserActor, Actor
from actor_sheet import SFactorType
from color_utils import Color
from enhanced_temporary_recovery_system import EnhancedTemporaryRecoveryIntegrator
from multi_actor_manager import MultiActorManager, ActorRole
from actor_state_filter import actor_state_filter


def _safe_display_name(actor: Actor) -> str:
    try:
        nm = getattr(getattr(actor, 'sheet', None), 'name', None)
        if not nm:
            return str(actor)
        try:
            if getattr(getattr(actor, 'sheet', None), 'is_user_actor', False):
                return str(nm)
        except Exception:
            pass
        try:
            from stranger_description_system import known_actors_tracker
            if known_actors_tracker is not None and known_actors_tracker.is_name_known(str(nm)):
                return str(nm)
        except Exception:
            pass
        ka = getattr(getattr(actor, 'sheet', None), 'known_as', None)
        if ka:
            return str(ka)
        pd = getattr(getattr(actor, 'sheet', None), 'public_description', None)
        if pd:
            return str(pd)
        return str(nm)
    except Exception:
        return "someone"


class EnhancedRoundManager:
    """
    Enhanced Round Manager that can handle unlimited actors through MultiActorManager.
    
    Features:
    - Scalable initiative calculation for any number of actors
    - Dynamic proactor/reactor assignment
    - Intelligent turn rotation to prevent dominance
    - Support for complex multi-actor scenarios
    - Performance optimized for large actor counts
    """
    
    def __init__(self, actor_manager: MultiActorManager, recovery_integrator: EnhancedTemporaryRecoveryIntegrator = None):
        self.actor_manager = actor_manager
        self.round_number = 0
        self.recovery_integrator = recovery_integrator or EnhancedTemporaryRecoveryIntegrator()
        
        # Enhanced proactor rotation tracking
        self.proactor_history = []  # Track recent proactors
        self.MAX_CONSECUTIVE_PROACTOR_TURNS = 2
        self.turn_participation_count = {}  # Track how many turns each actor has participated
        
        # Initiative and turn management
        self.last_initiative_data = None
        self.current_turn_queue = []
        self.turn_queue_position = 0
        
        # UTAS Serendipity Table
        self.UTAS_SERENDIPITY_TABLE = {
            2: -5, 3: -4, 4: -3, 5: -2, 6: -1,
            7: 0, 8: 1, 9: 2, 10: 3, 11: 4, 12: 5
        }
        
        # Performance tracking
        self.initiative_calculation_cache = {}
        self.cache_valid = False
        
        # Forced proactor for Round 1 (overrides UA-first)
        self.forced_round_one_proactor = None
    
    def set_round_one_proactor(self, actor: Actor):
        """Set a specific actor to be the proactor in Round 1 (overriding UA-first)."""
        self.forced_round_one_proactor = actor

    def _roll_serendipity(self) -> Tuple[int, str]:
        """
        Rolls 2d6 and uses UTAS table lookup to get Serendipity score from -5 to +5.
        Returns (result, detailed_roll_string)
        """
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        total = die1 + die2
        
        serendipity = self.UTAS_SERENDIPITY_TABLE[total]
        
        if serendipity < -5 or serendipity > 5:
            raise ValueError(f"Serendipity {serendipity} outside UTAS range [-5, +5]")
        
        detail = f"2D6({die1}+{die2}={total}) → {serendipity:+d}" if serendipity != 0 else f"2D6({die1}+{die2}={total}) → 0"
        return serendipity, detail
    
    def _calculate_actor_initiative(self, actor: Actor) -> Tuple[int, Dict[str, Any]]:
        """
        Calculate initiative for a single actor with detailed breakdown.
        Incorporates base Swiftness, current status values, serendipity, actor role bonuses, and recent action penalties.
        
        Args:
            actor: The actor to calculate initiative for
            
        Returns:
            Tuple of (total_initiative, breakdown_data)
        """
        # Get base stats
        swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
        serendipity, serendipity_detail = self._roll_serendipity()
        
        # Get current status values for initiative modifiers
        from actor_sheet import StatusType
        stamina = actor.sheet.statuses[StatusType.STAMINA].value
        spirit = actor.sheet.statuses[StatusType.SPIRIT].value
        
        # Calculate status modifier (average of Stamina and Spirit only)
        # Supply doesn't affect initiative as it represents resources, not readiness
        status_modifier = (stamina + spirit) // 2
        
        # Get actor role bonus from MultiActorManager
        actor_role = self.actor_manager.get_actor_role_by_actor(actor)
        role_bonus = self.actor_manager._get_role_priority_bonus(actor_role) if actor_role else 0
        
        
        # Check for INUA override (User Actor always goes first against INUAs)
        inua_override = False
        if isinstance(actor, UserActor):
            active_actors = self.actor_manager.get_active_actors()
            has_inua = any(isinstance(a, InanimateNonUserActor) for a in active_actors)
            if has_inua:
                inua_override = True
        
        # Calculate total initiative
        if inua_override:
            total_initiative = 100  # Guaranteed first
        else:
            total_initiative = swiftness + status_modifier + serendipity + role_bonus
        
        # Create breakdown data
        breakdown = {
            'swiftness': swiftness,
            'status_modifier': status_modifier,
            'stamina': stamina,
            'spirit': spirit,
            'serendipity': serendipity,
            'serendipity_roll_detail': serendipity_detail,
            'role_bonus': role_bonus,
            'total': total_initiative,
            'inua_override': inua_override
        }
        
        return total_initiative, breakdown
    
    def create_turn_queue(self) -> Dict[str, Any]:
        """
        Create a turn queue with initiative calculated once per round.
        Max 4 actors: UA + top 3 NUA/INUA by initiative.
        
        Returns:
            Dict containing turn queue data
        """
        active_actors = self.actor_manager.get_active_actors()
        
        if not active_actors:
            return {
                'turn_queue': [],
                'actor_initiatives': {},
                'excluded_actors': [],
                'queue_size': 0,
                'max_queue_size': 4
            }
        
        # Calculate initiative for all actors
        actor_initiatives = {}
        ua_actor = None
        nua_actors = []
        
        for actor in active_actors:
            initiative, breakdown = self._calculate_actor_initiative(actor)
            actor_initiatives[actor.sheet.name] = {
                'initiative_score': initiative,
                **breakdown
            }
            
            # Separate UA from NUA/INUA
            if getattr(actor, 'is_user_actor', False):
                ua_actor = actor
            else:
                nua_actors.append(actor)
        
        # Sort NUA/INUA by initiative ONLY (no tie-breakers for NUAs)
        # Tied NUAs will act together in the same turn
        def nua_sort_key(actor):
            initiative = actor_initiatives[actor.sheet.name]['initiative_score']
            return -initiative  # Only sort by initiative, no tie-breakers
        
        nua_actors.sort(key=nua_sort_key)
        
        # Build turn queue: top 3 NUA/INUA + UA
        turn_queue = []
        excluded_actors = []
        
        # Take top 3 NUA/INUA
        top_3_nua = nua_actors[:3]
        excluded_nua = nua_actors[3:]
        
        # Create combined list for sorting
        queue_candidates = top_3_nua.copy()
        if ua_actor:
            queue_candidates.append(ua_actor)
        
        # Sort final queue with special tie-breaker rules:
        # - UA uses tie-breakers (swiftness, then random)
        # - NUAs do NOT use tie-breakers (tied NUAs act together)
        def queue_sort_key(actor):
            initiative = actor_initiatives[actor.sheet.name]['initiative_score']
            is_ua = getattr(actor, 'is_user_actor', False)
            
            if is_ua:
                # UA gets tie-breakers: initiative, then swiftness, then random
                swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
                return (-initiative, -swiftness, random.random())
            else:
                # NUA sorts by initiative, then swiftness for tie-breaking
                swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
                return (-initiative, -swiftness, random.random())
        
        queue_candidates.sort(key=queue_sort_key)

        # UA-FIRST OVERRIDE: Ensure UserActor acts first ONLY in Round 1 of contested actions
        # After Round 1, initiative determines order normally
        ua_first_applied = False
        
        # Check for forced proactor (NUA initiation)
        forced_actor = self.forced_round_one_proactor
        
        if forced_actor and self.round_number == 1:
            print(f"🔍 DEBUG OVERRIDE: Forced proactor set to {forced_actor.sheet.name}")
            if forced_actor in queue_candidates:
                 try:
                    idx = queue_candidates.index(forced_actor)
                    if idx != 0:
                        queue_candidates.insert(0, queue_candidates.pop(idx))
                    ua_first_applied = True # Re-use this flag to indicate manual ordering
                    # Clear the force so it doesn't apply to round 2
                    self.forced_round_one_proactor = None 
                 except ValueError:
                    pass
        elif ua_actor and ua_actor in queue_candidates and self.round_number == 1:  # Round 1 is when UA goes first
            print(f"🔍 DEBUG UA-FIRST: Applying override! Moving UA to position 0")
            try:
                ua_index = queue_candidates.index(ua_actor)
                print(f"🔍 DEBUG UA-FIRST: UA currently at index {ua_index}")
                if ua_index != 0:
                    queue_candidates.insert(0, queue_candidates.pop(ua_index))
                    print(f"🔍 DEBUG UA-FIRST: Moved UA to position 0")
                    ua_first_applied = True
                    # Mark in initiatives that UA-first override applied (for optional reporting)
                    try:
                        actor_initiatives[ua_actor.sheet.name]['ua_first_override'] = True
                    except Exception:
                        pass
            except ValueError:
                print(f"🔍 DEBUG UA-FIRST: ValueError - UA not in queue_candidates")
                pass
        else:
            print(f"🔍 DEBUG UA-FIRST: Override NOT applied - conditions not met")
        
        # Build turn queue data
        # If UA-FIRST was applied, use the queue_candidates order directly
        # Otherwise, group by initiative score to detect NUA ties
        if ua_first_applied:
            # UA-FIRST: Use queue_candidates order directly (UA is already at position 0)
            position = 1
            for actor in queue_candidates:
                turn_queue.append({
                    'position': position,
                    'actor_name': actor.sheet.name,
                    'actor': actor,
                    'initiative_score': actor_initiatives[actor.sheet.name]['initiative_score'],
                    'is_nua_group': False,
                    'group_size': 1
                })
                position += 1
        else:
            # Normal initiative order: Group actors by initiative score to detect ties
            initiative_groups = {}
            for actor in queue_candidates:
                init_score = actor_initiatives[actor.sheet.name]['initiative_score']
                if init_score not in initiative_groups:
                    initiative_groups[init_score] = []
                initiative_groups[init_score].append(actor)
            
            # Build turn queue with grouped entries
            position = 1
            for init_score in sorted(initiative_groups.keys(), reverse=True):
                actors_at_this_init = initiative_groups[init_score]
                
                # Check if this is a NUA tie (multiple NUAs with same initiative)
                nua_actors_tied = [a for a in actors_at_this_init if not getattr(a, 'is_user_actor', False)]
                ua_actors_tied = [a for a in actors_at_this_init if getattr(a, 'is_user_actor', False)]
                
                # Add UA actors individually (they use tie-breakers)
                for ua in ua_actors_tied:
                    turn_queue.append({
                        'position': position,
                        'actor_name': ua.sheet.name,
                        'actor': ua,
                        'initiative_score': init_score,
                        'is_user_actor': True,
                        'is_grouped': False,
                        'group_members': None
                    })
                    position += 1
                
                # Add NUA actors as a group if tied, individually if not
                if len(nua_actors_tied) > 1:
                    # Multiple NUAs tied - create grouped entry
                    turn_queue.append({
                        'position': position,
                        'actor_name': f"Group of {len(nua_actors_tied)} NPCs",
                        'actor': nua_actors_tied[0],  # Primary actor for compatibility
                        'initiative_score': init_score,
                        'is_user_actor': False,
                        'is_grouped': True,
                        'group_members': nua_actors_tied  # All tied NUAs
                    })
                    position += 1
                elif len(nua_actors_tied) == 1:
                    # Single NUA - add individually
                    nua = nua_actors_tied[0]
                    turn_queue.append({
                        'position': position,
                        'actor_name': _safe_display_name(nua),
                        'actor': nua,
                        'initiative_score': init_score,
                        'is_user_actor': False,
                        'is_grouped': False,
                        'group_members': None
                    })
                    position += 1
        
        # Track excluded actors
        for actor in excluded_nua:
            excluded_actors.append({
                'actor_name': _safe_display_name(actor),
                'initiative_score': actor_initiatives[actor.sheet.name]['initiative_score'],
                'reason': 'Not in top 3 NUA/INUA'
            })
        
        # Filter turn queue for dead/unconscious actors
        filtered_queue = actor_state_filter.filter_turn_queue(turn_queue)
        
        # Update internal turn queue - store full turn queue data (not just actors)
        # This preserves grouped entry information
        self.current_turn_queue_data = filtered_queue  # Full data with is_grouped, group_members
        self.current_turn_queue = [item['actor'] for item in filtered_queue]  # Legacy compatibility
        self.turn_queue_position = 0
        # DEBUG: Print initialized queue order
        try:
            names = []
            for item in filtered_queue:
                if item.get('is_grouped'):
                    group_names = [_safe_display_name(a) for a in item['group_members']]
                    names.append(f"[{', '.join(group_names)}]")
                else:
                    names.append(_safe_display_name(item['actor']))
            print(f"{Color.SYSTEM}TURN QUEUE INIT: {names}{Color.RESET}")
        except Exception:
            pass
        
        # Detect tie-breakers in final queue
        tie_breaker_data = self._detect_queue_tie_breakers(queue_candidates, actor_initiatives)
        
        return {
            'turn_queue': filtered_queue,
            'actor_initiatives': actor_initiatives,
            'excluded_actors': excluded_actors,
            'queue_size': len(filtered_queue),
            'max_queue_size': 4,
            'tie_breakers': tie_breaker_data.get('tie_breakers', []),
            'nua_groups': tie_breaker_data.get('nua_groups', [])
        }
    
    def _detect_queue_tie_breakers(self, queue_candidates: List[Actor], actor_initiatives: Dict[str, Dict]) -> List[Dict[str, Any]]:
        """Detect tie-breakers used in turn queue creation.
        
        NEW SYSTEM:
        - Only UA uses tie-breakers (swiftness, then random)
        - NUAs with tied initiative act together as a group (no tie-breakers)
        """
        tie_breakers = []
        nua_groups = []  # Track NUA groups that act together
        
        for i in range(len(queue_candidates) - 1):
            current_actor = queue_candidates[i]
            next_actor = queue_candidates[i + 1]
            
            current_initiative = actor_initiatives[current_actor.sheet.name]['initiative_score']
            next_initiative = actor_initiatives[next_actor.sheet.name]['initiative_score']
            
            if current_initiative == next_initiative:
                current_is_ua = getattr(current_actor, 'is_user_actor', False)
                next_is_ua = getattr(next_actor, 'is_user_actor', False)
                
                # Only apply tie-breakers if UA is involved
                if current_is_ua or next_is_ua:
                    # UA vs UA or UA vs NUA - use tie-breaker
                    current_swiftness = current_actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
                    next_swiftness = next_actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
                    
                    tie_breaker_info = {
                        'actor_1': current_actor.sheet.name,
                        'actor_2': next_actor.sheet.name,
                        'tied_initiative': current_initiative,
                        'actor_1_swiftness': current_swiftness,
                        'actor_2_swiftness': next_swiftness,
                        'resolution_method': 'swiftness' if current_swiftness != next_swiftness else 'random',
                        'winner': current_actor.sheet.name,
                        'involves_ua': True
                    }
                    tie_breakers.append(tie_breaker_info)
                else:
                    # NUA vs NUA tie - they act together (no tie-breaker)
                    nua_groups.append({
                        'actors': [current_actor.sheet.name, next_actor.sheet.name],
                        'tied_initiative': current_initiative,
                        'resolution': 'grouped_action',
                        'note': 'These NPCs act simultaneously in the same turn'
                    })
        
        return {
            'tie_breakers': tie_breakers,
            'nua_groups': nua_groups
        }
    
    def _detect_tie_breakers(self, initiative_scores: List[Tuple[Actor, int]]) -> List[Dict[str, Any]]:
        """Detect and record tie breakers used in initiative resolution."""
        tie_breakers = []
        
        for i in range(len(initiative_scores) - 1):
            current_actor, current_score = initiative_scores[i]
            next_actor, next_score = initiative_scores[i + 1]
            
            if current_score == next_score:
                current_swiftness = current_actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
                next_swiftness = next_actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
                
                if current_swiftness != next_swiftness:
                    tie_breakers.append({
                        'type': 'swiftness',
                        'actors': [current_actor.sheet.name, next_actor.sheet.name],
                        'winner': current_actor.sheet.name if current_swiftness > next_swiftness else next_actor.sheet.name,
                        'swiftness_values': [current_swiftness, next_swiftness]
                    })
                else:
                    tie_breakers.append({
                        'type': 'random',
                        'actors': [current_actor.sheet.name, next_actor.sheet.name],
                        'winner': current_actor.sheet.name,
                    })
        
        return tie_breakers
    
    def _enforce_proactor_rotation(self):
        """
        Enforce proactor rotation to prevent any actor from dominating.
        Uses intelligent rotation based on participation history.
        """
        if len(self.current_turn_queue) < 2:
            return
        
        current_proactor = self.current_turn_queue[0]
        
        # Check consecutive proactor turns
        if len(self.proactor_history) >= self.MAX_CONSECUTIVE_PROACTOR_TURNS:
            recent_proactors = self.proactor_history[-self.MAX_CONSECUTIVE_PROACTOR_TURNS:]
            
            # If same actor has been proactor too many times, rotate
            if all(p.sheet.name == current_proactor.sheet.name for p in recent_proactors):
                print(f"{Color.WARNING}🔄 PROACTOR ROTATION: {current_proactor.sheet.name} has been proactor for {self.MAX_CONSECUTIVE_PROACTOR_TURNS} consecutive turns{Color.RESET}")
                
                # Find best alternative proactor
                alternative = self._find_best_alternative_proactor()
                if alternative:
                    # Move alternative to front
                    self.current_turn_queue.remove(alternative)
                    self.current_turn_queue.insert(0, alternative)
                    print(f"{Color.INFO}   → Rotating to: {alternative.sheet.name}{Color.RESET}")
    
    def _find_best_alternative_proactor(self) -> Optional[Actor]:
        """
        Find the best alternative proactor based on participation history and initiative.
        
        Returns:
            Actor that should be the next proactor, or None if no alternatives
        """
        if len(self.current_turn_queue) < 2:
            return None

        # Consider all actors except current proactor
        alternatives = self.current_turn_queue[1:]
        
        # Score each alternative
        best_actor = None
        best_score = float('-inf')
        
        for actor in alternatives:
            score = 0
            
            # Prefer actors who haven't been proactor recently
            recent_turns = self.turn_participation_count.get(actor.sheet.name, 0)
            score -= recent_turns * 2
            
            # Prefer actors with higher initiative components
            swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
            score += swiftness
            
            # Prefer User Actor if present (slight bonus)
            if isinstance(actor, UserActor):
                score += 1
            
            # Add role priority bonus
            actor_role = self.actor_manager.get_actor_role_by_actor(actor)
            if actor_role:
                role_priority_bonus = self._get_role_priority_bonus(actor_role)
                score += role_priority_bonus
            
            if score > best_score:
                best_score = score
                best_actor = actor
        
        return best_actor

    def ensure_actor_in_turn_queue(self, actor: Actor) -> bool:
        try:
            if actor is None:
                return False
            if actor in (self.current_turn_queue or []):
                return False

            if not hasattr(self, 'current_turn_queue_data') or not self.current_turn_queue_data:
                self.current_turn_queue = [actor]
                self.current_turn_queue_data = [{
                    'position': 1,
                    'actor_name': actor.sheet.name,
                    'actor': actor,
                    'is_grouped': False,
                    'group_members': None
                }]
                self.turn_queue_position = 0
                return True

            try:
                insert_after = max(0, min(self.turn_queue_position, len(self.current_turn_queue_data) - 1))
            except Exception:
                insert_after = 0

            new_item = {
                'position': -1,
                'actor_name': actor.sheet.name,
                'actor': actor,
                'is_grouped': False,
                'group_members': None
            }
            self.current_turn_queue_data.insert(insert_after + 1, new_item)
            for i, item in enumerate(self.current_turn_queue_data, start=1):
                item['position'] = i
            self.current_turn_queue = [item['actor'] for item in self.current_turn_queue_data]
            return True
        except Exception:
            return False
    
    def _get_role_priority_bonus(self, role: ActorRole) -> int:
        """Get initiative bonus based on actor role."""
        bonuses = {
            ActorRole.USER: 0,           # User and primary have equal priority
            ActorRole.SCENE_PRIMARY: 0,   # Main scene actor has equal priority with user
            ActorRole.SCENE_SECONDARY: -1, # Secondary actors go later
            ActorRole.BACKGROUND: -2,     # Background actors go much later
            ActorRole.INACTIVE: -20       # Inactive actors shouldn't be in turn order
        }
        return bonuses.get(role, 0)   
    def start_round(self) -> Dict[str, Any]:
        """
        Start a new round with recovery processing and turn queue creation.
        
        Returns:
            Dict containing round start data including turn queue and recovery
        """
        self.round_number += 1
        self.actor_manager.advance_turn()
        
        # Get all active actors for recovery
        active_actors = self.actor_manager.get_active_actors()
        
        print(f"DEBUG: Round {self.round_number} - Processing recovery for {len(active_actors)} actors")
        
        # Apply temporary recovery
        recovery_events = self.recovery_integrator.apply_recovery_to_actors(active_actors)
        print(f"DEBUG: Recovery returned {len(recovery_events)} events")
        
        # Create turn queue for this round (initiative calculated once)
        turn_queue_data = self.create_turn_queue()
        turn_queue_data['recovery_events'] = recovery_events
        turn_queue_data['round_number'] = self.round_number
        
        return turn_queue_data
    
    def get_turn_order(self) -> List[Actor]:
        """Get the current turn order queue."""
        return self.current_turn_queue.copy()
    
    def get_current_turn_entry(self) -> Optional[Dict[str, Any]]:
        """
        Get the current turn queue entry (includes grouped NUA information).
        
        Returns:
            Current turn entry dict with 'actor', 'is_grouped', 'group_members', etc.
        """
        if not hasattr(self, 'current_turn_queue_data') or len(self.current_turn_queue_data) == 0:
            return None
        
        return self.current_turn_queue_data[self.turn_queue_position]
    
    def is_current_turn_grouped(self) -> bool:
        """Check if the current turn is a grouped NUA turn."""
        entry = self.get_current_turn_entry()
        return entry.get('is_grouped', False) if entry else False
    
    def get_current_group_members(self) -> List[Actor]:
        """Get all actors in the current grouped turn (empty list if not grouped)."""
        entry = self.get_current_turn_entry()
        if entry and entry.get('is_grouped'):
            return entry.get('group_members', [])
        return []
    
    def get_current_proactor(self) -> Optional[Actor]:
        """
        Get the current proactor based on turn queue position.
        For grouped turns, returns the primary actor (first in group).
        
        Returns:
            Current proactor actor or None if no actors in queue
        """
        if len(self.current_turn_queue) == 0:
            return None
        
        return self.current_turn_queue[self.turn_queue_position]
    
    def get_next_proactor_reactor_pair(self) -> Tuple[Optional[Actor], Optional[Actor]]:
        """
        Get the next proactor and a default reactor pair for the current turn.
        NOTE: This method provides a fallback reactor selection. 
        For dynamic reactor selection based on action targeting, use get_current_proactor() 
        and determine the reactor through NUA/INUA detection systems.
        
        Returns:
            Tuple of (proactor, default_reactor) or (None, None) if insufficient actors
        """
        if len(self.current_turn_queue) < 2:
            return None, None
        
        # Get proactor based on current queue position
        proactor = self.current_turn_queue[self.turn_queue_position]
        
        # Get default reactor (next actor in queue, wrapping around if needed)
        # This is a fallback - actual reactor should be determined by action targeting
        reactor_position = (self.turn_queue_position + 1) % len(self.current_turn_queue)
        default_reactor = self.current_turn_queue[reactor_position]
        
        return proactor, default_reactor
    
    def get_all_potential_reactors(self, exclude_proactor: Actor) -> List[Actor]:
        """
        Get all actors who could potentially be reactors (excluding the proactor).
        
        Args:
            exclude_proactor: The current proactor to exclude
            
        Returns:
            List of potential reactor actors
        """
        return [actor for actor in self.current_turn_queue if actor != exclude_proactor]
    
    def find_reactor_by_target_detection(self, user_input: str, scene_description: str = "") -> Optional[Actor]:
        """
        Find reactor using the existing target detection system.
        Integrates with TargetDetector to identify the target actor from user input.
        
        Args:
            user_input: The user's action input
            scene_description: Current scene context for better detection
            
        Returns:
            Actor if target found in turn queue, None otherwise
        """
        from llm_agents.target_detection_system import TargetDetector
        
        detector = TargetDetector()
        target_info = detector.detect_target_type(user_input, scene_description)
        
        detected_target = target_info.get('detected_target', '').lower()

        # Prefer matching across ALL active actors (not just the trimmed turn queue).
        # This prevents encounters from aborting when the intended target is excluded
        # from the top-initiative slice.
        actors_to_check = []
        try:
            if hasattr(self.actor_manager, 'get_active_actors'):
                actors_to_check = list(self.actor_manager.get_active_actors() or [])
        except Exception:
            actors_to_check = []
        if not actors_to_check:
            actors_to_check = list(self.current_turn_queue or [])

        # Try to match detected target with actors in the candidate list
        for actor in actors_to_check:
            actor_name_lower = actor.sheet.name.lower()
            actor_occ_lower = (getattr(getattr(actor, 'sheet', None), 'occupation', '') or '').lower()
            alias_texts = [actor_name_lower]
            if actor_occ_lower:
                alias_texts.append(actor_occ_lower)
            try:
                from stranger_description_system import get_nua_definite_description
                alias_texts.append((get_nua_definite_description(actor) or '').lower())
            except Exception:
                pass

            # Direct name match
            if detected_target == actor_name_lower:
                return actor

            # Direct occupation/alias match
            try:
                for alias in alias_texts:
                    if alias and detected_target == alias:
                        return actor
            except Exception:
                pass
            
            # Partial name match (e.g., "guard" matches "Security Guard")
            if detected_target in actor_name_lower or actor_name_lower in detected_target:
                return actor

            # Partial occupation/alias match
            try:
                for alias in alias_texts:
                    if not alias:
                        continue
                    if detected_target in alias or alias in detected_target:
                        return actor
            except Exception:
                pass
            
            # Enhanced matching for common aliases and role descriptions
            actor_words = set(actor_name_lower.split())
            target_words = set(detected_target.split())
            try:
                if actor_occ_lower:
                    actor_words |= set(actor_occ_lower.split())
            except Exception:
                pass
            try:
                for alias in alias_texts:
                    if alias:
                        actor_words |= set(alias.split())
            except Exception:
                pass
            
            # Check for word overlap (e.g., "shop owner" matches "Shop Merchant" via "shop")
            if actor_words & target_words:
                return actor
            
            # Dynamic word-based matching for flexible target detection
            # Check if any word from the detected target appears in the actor name
            for target_word in target_words:
                if len(target_word) > 2:  # Skip very short words
                    for actor_word in actor_words:
                        if target_word in actor_word or actor_word in target_word:
                            return actor
        
        return None
    
    def find_reactor_by_name(self, reactor_name: str) -> Optional[Actor]:
        """
        Find a specific actor in the turn queue by name to use as reactor.
        This supports direct reactor selection when the target name is already known.
        
        Args:
            reactor_name: Name of the actor to find
            
        Returns:
            Actor if found in turn queue, None otherwise
        """
        for actor in self.current_turn_queue:
            if actor.sheet.name.lower() == reactor_name.lower():
                return actor
        return None
    
    def validate_reactor_selection(self, proactor: Actor, reactor: Actor) -> bool:
        """
        Validate that both proactor and reactor are in the current turn queue.
        
        Args:
            proactor: The proactor actor
            reactor: The reactor actor
            
        Returns:
            True if both actors are valid for the current turn, False otherwise
        """
        return (proactor in self.current_turn_queue and 
                reactor in self.current_turn_queue and 
                proactor != reactor)
    
    def record_proactor_turn(self, proactor: Actor):
        """Record that an actor took a proactor turn."""
        self.proactor_history.append(proactor)
        
        # Track participation count
        name = proactor.sheet.name
        self.turn_participation_count[name] = self.turn_participation_count.get(name, 0) + 1
        
        # Record in actor manager
        actor_id = self.actor_manager.get_actor_id_by_name(name)
        if actor_id:
            self.actor_manager.record_actor_action(actor_id)
        
        # Keep history manageable
        if len(self.proactor_history) > 10:
            self.proactor_history = self.proactor_history[-10:]
    
    def advance_turn_queue(self) -> bool:
        """
        Advance to the next actor in the turn queue.
        Returns True if the turn queue cycle is complete (everyone has acted as proactor).
        Skips dead/unconscious actors automatically.
        """
        if len(self.current_turn_queue) > 0:
            try:
                old_pos = self.turn_queue_position
                old_actor = self.current_turn_queue[old_pos]
                new_pos = (old_pos + 1) % len(self.current_turn_queue)
                new_actor = self.current_turn_queue[new_pos]
                print(f"{Color.SYSTEM}ADVANCE QUEUE: pos {old_pos+1}->{new_pos+1} | {old_actor.sheet.name} -> {new_actor.sheet.name}{Color.RESET}")
            except Exception:
                pass
            self.turn_queue_position = (self.turn_queue_position + 1) % len(self.current_turn_queue)
            
            # Check if new actor can act
            if len(self.current_turn_queue) > 0:
                current_actor = self.current_turn_queue[self.turn_queue_position]
                if not actor_state_filter.can_actor_take_action(current_actor):
                    state = actor_state_filter.check_actor_state(current_actor)
                    print(f"{Color.WARNING}⏭️  Skipping {current_actor.sheet.name}'s turn ({state}){Color.RESET}")
                    # Recursively advance to next actor
                    return self.advance_turn_queue()
            
            # Return True if we've cycled back to position 0 (everyone has had a turn)
            return self.turn_queue_position == 0
        return False
    
    def is_turn_queue_complete(self) -> bool:
        """
        Check if all actors in the current turn queue have acted as proactor.
        Returns True when we're at position 0, indicating everyone has had a turn.
        """
        return self.turn_queue_position == 0 and len(self.current_turn_queue) > 0
    
    def rotate_turn_queue(self):
        """Legacy method - now just calls advance_turn_queue for compatibility."""
        self.advance_turn_queue()
    
    def is_contest_resolved(self) -> bool:
        """Check if the contest is resolved (any actor is dead or critically damaged)."""
        active_actors = self.actor_manager.get_active_actors()
        return any(actor.sheet.is_dead() for actor in active_actors)
    
    def get_winner_and_loser(self) -> Tuple[Optional[Actor], Optional[Actor]]:
        """Determine winner and loser if contest is resolved."""
        active_actors = self.actor_manager.get_active_actors()
        
        defeated_actor = None
        for actor in active_actors:
            if actor.sheet.is_dead():
                defeated_actor = actor
                break
        
        if defeated_actor:
            winner = next((actor for actor in active_actors if actor != defeated_actor), None)
            return winner, defeated_actor
        
        return None, None
    
    def end_round(self):
        """Handle end-of-round logic like status effect decay and lasting shifts."""
        print(f"{Color.SYSTEM}--- Round {self.round_number} End ---{Color.RESET}")
        
        active_actors = self.actor_manager.get_active_actors()
        
        # Apply accumulated lasting shifts to max capacity
        print(f"{Color.SYSTEM}Applying lasting shifts...{Color.RESET}")
        self.recovery_integrator.recovery_manager.apply_lasting_shifts_to_actors(active_actors)
        
        # Check for deaths after lasting shifts applied
        for actor in active_actors:
            if actor.sheet.is_dead():
                print(f"{Color.ERROR}💀 {actor.sheet.name} has died from accumulated injuries!{Color.RESET}")
        
        # Handle status effect duration decay
        for actor in active_actors:
            expired_effects = []
            active_effects = []
            
            for effect in actor.sheet.effects:
                if effect.duration > 0:
                    effect.duration -= 1
                    if effect.duration == 0:
                        expired_effects.append(effect)
                    else:
                        active_effects.append(effect)
                elif effect.duration == -1:  # Permanent effect
                    active_effects.append(effect)
            
            actor.sheet.effects = active_effects
            
            # Report expired effects
            for effect in expired_effects:
                print(f"{Color.SYSTEM}EFFECT: The '{effect.name}' effect has worn off for {actor.sheet.name}.{Color.RESET}")
    
    def get_round_summary(self) -> Dict[str, Any]:
        """Get a summary of the current round state."""
        active_actors = self.actor_manager.get_active_actors()
        
        return {
            'round_number': self.round_number,
            'active_actor_count': len(active_actors),
            'turn_queue_length': len(self.current_turn_queue),
            'proactor_history_length': len(self.proactor_history),
            'participation_stats': self.turn_participation_count.copy()
        }
    
    def display_round_status(self):
        """Display current round status for debugging."""
        summary = self.get_round_summary()
        
        print(f"\n{Color.SYSTEM}=== ROUND {summary['round_number']} STATUS ==={Color.RESET}")
        print(f"{Color.INFO}Active Actors: {summary['active_actor_count']}{Color.RESET}")
        print(f"{Color.INFO}Turn Queue: {summary['turn_queue_length']} actors{Color.RESET}")
        
        if self.current_turn_queue:
            print(f"\n{Color.SYSTEM}Current Turn Order:{Color.RESET}")
            for i, actor in enumerate(self.current_turn_queue):
                role_indicator = "👤" if isinstance(actor, UserActor) else "🤖" if isinstance(actor, NonUserActor) else "🔧"
                proactor_indicator = " (PROACTOR)" if i == 0 else " (REACTOR)" if i == 1 else ""
                print(f"  {i+1}. {role_indicator} {actor.sheet.name}{proactor_indicator}")
