"""
Enhanced Reporter for Multi-Actor UTAS Simulation

This system provides comprehensive reporting capabilities for unlimited actors,
including scalable display formats and performance-optimized output.
"""

from typing import Dict, List, Any, Optional, Tuple
from actors import Actor, UserActor, NonUserActor, InanimateNonUserActor
from multi_actor_manager import MultiActorManager, ActorRole
from enhanced_sympathy_system import EnhancedSympathyManager, RelationshipType
from color_utils import Color
from label_utils import (
    normalize_sfactor_label,
    n2n_s_trait,
    n2n_serendipity,
    n2n_shift_magnitude,
    descriptor as get_narrative_descriptor,
)
from llm_agents.utas_narrative_formula import UTASNarrativeFormula
import math


class EnhancedReporter:
    """
    Enhanced reporter that can handle unlimited actors with scalable output formats.
    
    Features:
    - Scalable actor display (summary vs detailed modes)
    - Multi-actor initiative reporting
    - Relationship network visualization
    - Performance optimized for large actor counts
    - Configurable output verbosity
    """
    
    def __init__(self, actor_manager: MultiActorManager, sympathy_manager: EnhancedSympathyManager):
        self.actor_manager = actor_manager
        self.sympathy_manager = sympathy_manager
        
        # Display configuration
        self.max_actors_detailed = 10  # Switch to summary mode above this
        self.max_relationships_shown = 5  # Max relationships to show per actor
        self.verbosity_level = "normal"  # "minimal", "normal", "detailed", "verbose"

    def _scrub_unknown_names(self, text: str, actors: list) -> str:
        try:
            if not isinstance(text, str) or not text.strip():
                return text
            if not actors:
                return text
            try:
                from stranger_description_system import known_actors_tracker
            except Exception:
                known_actors_tracker = None
            try:
                from multi_actor_manager import _safe_display_name
            except Exception:
                _safe_display_name = None

            scrubbed = text
            for a in actors:
                if a is None:
                    continue
                try:
                    if getattr(a, 'is_user_actor', False):
                        continue
                except Exception:
                    pass
                try:
                    true_name = getattr(getattr(a, 'sheet', None), 'name', None)
                except Exception:
                    true_name = None
                if not true_name:
                    continue
                try:
                    if known_actors_tracker is not None and known_actors_tracker.is_name_known(str(true_name)):
                        continue
                except Exception:
                    pass
                try:
                    if _safe_display_name is not None:
                        masked = _safe_display_name(a)
                    else:
                        masked = None
                except Exception:
                    masked = None
                if not masked:
                    continue
                if str(masked).strip() == str(true_name).strip():
                    continue
                try:
                    scrubbed = scrubbed.replace(str(true_name), str(masked))
                except Exception:
                    pass
            return scrubbed
        except Exception:
            return text
    
    def _sanitize_step6_no_invented_loot(self, text: str) -> str:
        try:
            if not isinstance(text, str) or not text.strip():
                return text

            # Preserve the deterministic ending formula (usually contains "you experience" / "experiences")
            lower = text.lower()
            idx = lower.rfind(' you experience')
            if idx < 0:
                idx = lower.rfind(' you experiences')
            if idx < 0:
                idx = lower.rfind(' experiences a ')

            if idx > 0:
                body = text[:idx]
                ending = text[idx:]
            else:
                body = text
                ending = ""

            # Remove/neutralize concrete money handoff/coin pouch prose.
            # Transactions are handled separately by the monetary system and should not be invented here.
            banned_markers = [
                'pouch of coins', 'bag of coins', 'coins', 'coin', 'clink', 'payment', 'pays you',
                'hands you money', 'hands you a pouch', 'gives you money', 'gives you a pouch',
                'presses coins', 'drops coins', 'sets a pouch', 'leather pouch',
            ]

            scrubbed_body = body
            try:
                import re
                # Remove sentences containing these markers.
                for marker in banned_markers:
                    pat = rf"[^.!?]*\b{re.escape(marker)}\b[^.!?]*[.!?]?"
                    scrubbed_body = re.sub(pat, ' ', scrubbed_body, flags=re.IGNORECASE)
                scrubbed_body = re.sub(r"\s+", " ", scrubbed_body).strip()
            except Exception:
                pass

            # If we stripped everything, keep a minimal neutral lead-in.
            if not scrubbed_body:
                scrubbed_body = "The moment leaves a tangible shift in your resources." if ending else ""

            if ending:
                # Ensure spacing between body and ending
                if scrubbed_body and not scrubbed_body.endswith(('.', '!', '?', ',')):
                    scrubbed_body = scrubbed_body.rstrip() + ","
                return (scrubbed_body + " " + ending.lstrip()).strip()
            return scrubbed_body
        except Exception:
            return text

    def report_turn_queue_results(self, turn_queue_data: Dict[str, Any]):
        """
        Report turn queue creation results with the new per-round system.
        Shows queue composition, excluded actors, tie-breaker information,
        and any recovery that occurred at round start.
        """
        turn_queue = turn_queue_data.get('turn_queue', [])
        excluded_actors = turn_queue_data.get('excluded_actors', [])
        tie_breakers = turn_queue_data.get('tie_breakers', [])
        queue_size = turn_queue_data.get('queue_size', len(turn_queue))
        max_queue_size = turn_queue_data.get('max_queue_size', 4)
        recovery_events = turn_queue_data.get('recovery_events', [])
        actor_initiatives = turn_queue_data.get('actor_initiatives', {})
        use_primary_reactor_label = bool(turn_queue_data.get('use_primary_reactor_label', False))

        if not turn_queue:
            print(f"{Color.WARNING}No actors in turn queue{Color.RESET}")
            return

        # Recovery at round start (before rolls)
        if recovery_events:
            self._report_recovery_events(recovery_events)

        # Always show Initiative Rolls first
        print(f"\n{Color.INFO}🎲 INITIATIVE ROLLS:{Color.RESET}")
        for actor_entry in turn_queue:
            actor_obj = actor_entry.get('actor')
            # Display name should be masked; internal lookup key remains the true sheet.name
            try:
                display_name = actor_entry.get('actor_name')
                if not display_name and actor_obj is not None:
                    from multi_actor_manager import _safe_display_name
                    display_name = _safe_display_name(actor_obj)
            except Exception:
                display_name = actor_entry.get('actor_name')
            if not display_name:
                display_name = getattr(getattr(actor_obj, 'sheet', None), 'name', None)

            try:
                lookup_name = getattr(getattr(actor_obj, 'sheet', None), 'name', None) or display_name
            except Exception:
                lookup_name = display_name
            ind = self._get_actor_type_indicator(actor_obj)
            breakdown = actor_initiatives.get(lookup_name, {})
            swiftness = breakdown.get('swiftness', 0)
            status_mod = breakdown.get('status_modifier', 0)
            stamina = breakdown.get('stamina', 0)
            spirit = breakdown.get('spirit', 0)
            ser_detail = breakdown.get('serendipity_roll_detail', '')
            ser_val = breakdown.get('serendipity', 0)
            total = breakdown.get('total', actor_entry.get('initiative_score', 0))
            ua_first = breakdown.get('ua_first_override') or breakdown.get('inua_override') or False
            ua_tag = " [UA-FIRST OVERRIDE]" if ua_first else ""

            # Math line
            print(f"  {ind} {display_name}{ua_tag}: {swiftness} + {status_mod} + ({ser_detail}) = {total}")
            # N2N line
            try:
                s_desc = n2n_s_trait(int(swiftness))
                ser_desc = n2n_serendipity(int(ser_val))
            except Exception:
                s_desc, ser_desc = str(swiftness), str(ser_val)
            print(f"    └─ {s_desc} Swiftness + Status Avg({stamina}+{spirit})/2 + {ser_desc} Serendipity")

        # Then show Turn Order with roles
        print(f"\n{Color.SYSTEM}📋 TURN ORDER:{Color.RESET}")
        for i, actor_data in enumerate(turn_queue, 1):
            actor = actor_data['actor']
            indicator = self._get_actor_type_indicator(actor)
            role_tag = " (PROACTOR)" if i == 1 else (" (PRIMARY REACTOR)" if (i == 2 and use_primary_reactor_label) else (" (REACTOR)" if i == 2 else ""))
            try:
                from multi_actor_manager import _safe_display_name
                _nm = _safe_display_name(actor)
            except Exception:
                _nm = getattr(getattr(actor, 'sheet', None), 'name', None) or str(actor)
            print(f"  {i}. {indicator} {_nm}{role_tag}")

        # Display excluded actors if any
        if excluded_actors:
            print(f"\n{Color.WARNING}⚠️ EXCLUDED ACTORS:{Color.RESET}")
            for excluded in excluded_actors:
                print(f"  • {excluded['actor_name']} (Initiative: {excluded['initiative_score']}, Reason: {excluded['reason']})")

        # Display tie-breakers if any
        if tie_breakers:
            # DEBUG: Check what's actually in tie_breakers
            print(f"\nDEBUG: tie_breakers type: {type(tie_breakers)}, length: {len(tie_breakers) if isinstance(tie_breakers, (list, tuple)) else 'N/A'}")
            if isinstance(tie_breakers, (list, tuple)) and len(tie_breakers) > 0:
                print(f"DEBUG: First item type: {type(tie_breakers[0])}, value: {tie_breakers[0]}")
            
            print(f"\n{Color.INFO}🎲 TIE-BREAKERS RESOLVED:{Color.RESET}")
            for tie in tie_breakers:
                # Skip non-dict entries (defensive coding)
                if not isinstance(tie, dict):
                    print(f"  • Warning: Invalid tie-breaker data (type: {type(tie)}): {tie}")
                    continue
                
                # Support multiple schemas
                if 'actors' in tie:
                    actors = tie.get('actors')
                    initiative = tie.get('initiative')
                    resolution = tie.get('resolution')
                    winner = tie.get('winner')
                else:
                    a1 = tie.get('actor_1')
                    a2 = tie.get('actor_2')
                    actors = f"{a1} vs {a2}"
                    initiative = tie.get('tied_initiative')
                    resolution = tie.get('resolution_method')
                    winner = tie.get('winner')
                actors = actors if actors is not None else 'N/A'
                initiative = initiative if initiative is not None else 'N/A'
                resolution = resolution if resolution is not None else 'N/A'
                winner = winner if winner is not None else 'N/A'
                print(f"  • {actors} tied at Initiative {initiative}")
                print(f"    Resolution: {resolution} → Winner: {winner}")

    def report_initiative_and_turn_order(self, initiative_data: Dict[str, Any]):
        """
        Report initiative rolls and turn order for all active actors.
        Scales automatically based on number of actors.
        LEGACY METHOD - Use report_turn_queue_results for new turn queue system.
        """
        actor_initiatives = initiative_data.get('actor_initiatives', {})
        turn_order = initiative_data.get('turn_order', [])
        tie_breakers = initiative_data.get('tie_breakers', [])
        recovery_events = initiative_data.get('recovery_events', [])
        
        if not actor_initiatives:
            print(f"{Color.WARNING}No actors available for initiative{Color.RESET}")
            return
        
        print(f"\n{Color.SYSTEM}{'='*60}")
        print(f"  ROUND {initiative_data.get('round_number', '?')} - INITIATIVE & TURN ORDER")
        print(f"{'='*60}{Color.RESET}")
        
        # Report recovery events first if any
        if recovery_events:
            self._report_recovery_events(recovery_events)
        
        # Determine display mode based on actor count
        actor_count = len(actor_initiatives)
        use_compact_mode = actor_count > self.max_actors_detailed
        
        if use_compact_mode:
            self._report_initiative_compact(actor_initiatives, turn_order)
        else:
            self._report_initiative_detailed(actor_initiatives, turn_order)
        
        # Report tie breakers if any
        if tie_breakers:
            self._report_tie_breakers(tie_breakers)
        
        # Show turn order summary
        self._report_turn_order_summary(turn_order, use_compact_mode)
    
    def _report_recovery_events(self, recovery_events: List[Dict[str, Any]]):
        """Report temporary status recovery events."""
        if not recovery_events:
            return
        
        print(f"\n{Color.INFO}🔄 TEMPORARY RECOVERY:{Color.RESET}")
        for event in recovery_events:
            actor_name = event.get('actor_name', 'Unknown')
            status_type = event.get('status_type', 'Unknown')
            recovery_amount = event.get('recovery_amount', 0)
            new_value = event.get('new_value', 0)
            # Prefer explicit old_value if provided; otherwise derive from new_value - amount
            old_value = event.get('old_value', new_value - recovery_amount)
            fully_recovered = event.get('fully_recovered', False)
            source_desc = event.get('source_description')

            # Primary recovery line mirroring legacy Reporter
            recovery_msg = f"{actor_name}'s {status_type} recovers +{recovery_amount} ({old_value} → {new_value})"
            if fully_recovered:
                recovery_msg += f" {Color.SUCCESS}[FULLY RECOVERED]{Color.RESET}"
            print(f"  {Color.SUCCESS}{recovery_msg}{Color.RESET}")
            if source_desc:
                print(f"    Source: {source_desc}")

            # Narrative flourish, especially for knockout wake-ups
            recovery_narrative = self._generate_recovery_narrative(actor_name, status_type, old_value, new_value, recovery_amount)
            if recovery_narrative:
                print(f"  {Color.NARRATIVE}{recovery_narrative}{Color.RESET}")
    
    def _generate_recovery_narrative(self, actor_name: str, status_type: str, old_value: int, new_value: int, recovery_amount: int) -> str:
        """Generate narrative description for recovery events, especially knockout recovery."""
        # Special case for knockout recovery (0 -> 1+ for STAMINA)
        if status_type == "STAMINA" and old_value == 0 and new_value >= 1:
            knockout_narratives = [
                f"{actor_name} stirs, consciousness slowly returning as their eyes flutter open.",
                f"{actor_name} groans softly and begins to regain awareness, pushing themselves up slightly.",
                f"{actor_name}'s breathing steadies as they gradually come back to consciousness.",
                f"{actor_name} blinks slowly, the fog of unconsciousness lifting as they return to awareness.",
                f"{actor_name} takes a shuddering breath and begins to recover from their knockout state."
            ]
            import random
            return random.choice(knockout_narratives)
        
        # General recovery narratives for other status types
        recovery_descriptions = {
            "STAMINA": [
                f"{actor_name} catches their breath, feeling some energy return.",
                f"{actor_name} steadies themselves, recovering some physical strength.",
                f"{actor_name} takes a moment to recover, feeling slightly refreshed."
            ],
            "FOCUS": [
                f"{actor_name} shakes their head clear, regaining some mental clarity.",
                f"{actor_name} blinks and refocuses, their concentration improving.",
                f"{actor_name} takes a deep breath, their mind becoming sharper."
            ],
            "SPIRIT": [
                f"{actor_name} feels a spark of determination return to their eyes.",
                f"{actor_name} straightens up, their resolve strengthening slightly.",
                f"{actor_name} draws upon inner reserves, feeling more resilient."
            ]
        }
        
        if status_type in recovery_descriptions:
            import random
            return random.choice(recovery_descriptions[status_type])
        
        # Fallback for unknown status types
        return f"{actor_name} recovers slightly, feeling somewhat better."
    
    def _report_initiative_detailed(self, actor_initiatives: Dict[str, Any], turn_order: List[Dict[str, Any]]):
        """Report initiative with full details for each actor."""
        print(f"\n{Color.INFO}🎲 INITIATIVE ROLLS:{Color.RESET}")
        
        for actor_data in turn_order:
            actor_name = actor_data['name']
            initiative_info = actor_initiatives.get(actor_name, {})
            
            swiftness = initiative_info.get('swiftness', 0)
            serendipity = initiative_info.get('serendipity', 0)
            total = initiative_info.get('total', 0)
            serendipity_detail = initiative_info.get('serendipity_roll_detail', '')
            inua_override = initiative_info.get('inua_override', False)
            
            # Get actor for type indicator
            actor = actor_data.get('actor')
            actor_indicator = self._get_actor_type_indicator(actor)
            
            if inua_override:
                print(f"  {actor_indicator} {actor_name}: {total} (INUA Override - User Actor goes first)")
            else:
                swiftness_desc = n2n_s_trait(swiftness)
                serendipity_desc = n2n_serendipity(serendipity)
                
                # Check if status information is available
                stamina = initiative_info.get('stamina')
                spirit = initiative_info.get('spirit')
                status_modifier = initiative_info.get('status_modifier')
                
                if stamina is not None and spirit is not None and status_modifier is not None:
                    # Display full formula with status modifier
                    print(f"  {actor_indicator} {actor_name}: {swiftness} + {status_modifier} + ({serendipity_detail}) = {total}")
                    print(f"    └─ {swiftness_desc} Swiftness + Status Avg({stamina}+{spirit})/2 + {serendipity_desc} Serendipity")
                else:
                    # Fallback to original display if status info missing
                    print(f"  {actor_indicator} {actor_name}: {swiftness} + ({serendipity_detail}) = {total}")
                    print(f"    └─ {swiftness_desc} Swiftness + {serendipity_desc} Serendipity")
    
    def _report_initiative_compact(self, actor_initiatives: Dict[str, Any], turn_order: List[Dict[str, Any]]):
        """Report initiative in compact format for many actors."""
        print(f"\n{Color.INFO}🎲 INITIATIVE SUMMARY ({len(actor_initiatives)} actors):{Color.RESET}")
        
        # Group actors by initiative score for compact display
        initiative_groups = {}
        for actor_data in turn_order:
            score = actor_data['initiative_score']
            if score not in initiative_groups:
                initiative_groups[score] = []
            initiative_groups[score].append(actor_data)
        
        # Display groups in descending order
        for score in sorted(initiative_groups.keys(), reverse=True):
            actors_at_score = initiative_groups[score]
            actor_names = [f"{self._get_actor_type_indicator(a.get('actor'))}{a['name']}" 
                          for a in actors_at_score]
            
            if len(actors_at_score) == 1:
                print(f"  {score:2d}: {actor_names[0]}")
            else:
                print(f"  {score:2d}: {', '.join(actor_names)} (tied)")
    
    def _report_tie_breakers(self, tie_breakers: List[Dict[str, Any]]):
        """Report tie breaker resolutions."""
        if not tie_breakers:
            return
        
        print(f"\n{Color.WARNING}⚖️ TIE BREAKERS:{Color.RESET}")
        for tie_breaker in tie_breakers:
            tie_type = tie_breaker['type']
            actors = tie_breaker['actors']
            winner = tie_breaker['winner']
            
            if tie_type == 'swiftness':
                swiftness_values = tie_breaker['swiftness_values']
                print(f"  {actors[0]} vs {actors[1]}: {winner} wins on Swiftness ({swiftness_values[0]} vs {swiftness_values[1]})")
            elif tie_type == 'random':
                print(f"  {actors[0]} vs {actors[1]}: {winner} wins on random tiebreaker")
    
    def _report_turn_order_summary(self, turn_order: List[Dict[str, Any]], compact_mode: bool):
        """Report the final turn order."""
        if not turn_order:
            return
        
        print(f"\n{Color.SYSTEM}📋 TURN ORDER:{Color.RESET}")
        
        if compact_mode and len(turn_order) > 8:
            # Show first few, middle indicator, last few
            if len(turn_order) <= 6:
                # Show all actors
                for i, actor in enumerate(turn_order):
                    indicator = self._get_actor_type_indicator(actor.get('actor'))
                    role_text = " (PROACTOR)" if i == 0 else " (REACTOR)" if i == 1 else ""
                    try:
                        _ao = actor.get('actor')
                        from multi_actor_manager import _safe_display_name
                        _nm = actor.get('actor_name') or (_safe_display_name(_ao) if _ao is not None else actor.get('name'))
                    except Exception:
                        _nm = actor.get('actor_name') or actor.get('name')
                    print(f"  {i+1}. {indicator} {_nm}{role_text}")
            
            if len(turn_order) > 6:
                print(f"  ... ({len(turn_order) - 6} more actors)")
            else:
                # Show first 6 actors only
                for i in range(6):
                    if i < len(turn_order):
                        actor = turn_order[i]
                        indicator = self._get_actor_type_indicator(actor.get('actor'))
                        try:
                            _ao = actor.get('actor')
                            from multi_actor_manager import _safe_display_name
                            _nm = actor.get('actor_name') or (_safe_display_name(_ao) if _ao is not None else actor.get('name'))
                        except Exception:
                            _nm = actor.get('actor_name') or actor.get('name')
                        print(f"  {i+1}. {indicator} {_nm}")
        else:
            # Show all actors
            for i, actor_data in enumerate(turn_order):
                indicator = self._get_actor_type_indicator(actor_data.get('actor'))
                role_text = " (PROACTOR)" if i == 0 else " (REACTOR)" if i == 1 else ""
                try:
                    _ao = actor_data.get('actor')
                    from multi_actor_manager import _safe_display_name
                    _nm = actor_data.get('actor_name') or (_safe_display_name(_ao) if _ao is not None else actor_data.get('name'))
                except Exception:
                    _nm = actor_data.get('actor_name') or actor_data.get('name')
                print(f"  {i+1}. {indicator} {_nm}{role_text}")
    
    def display_multi_actor_status(self, focus_actors: Optional[List[Actor]] = None):
        """
        Display status for multiple actors with intelligent formatting.
        
        Args:
            focus_actors: Specific actors to focus on, or None for all active actors
        """
        actors_to_display = focus_actors or self.actor_manager.get_active_actors()
        
        if not actors_to_display:
            print(f"{Color.WARNING}No actors to display{Color.RESET}")
            return
        
        actor_count = len(actors_to_display)
        use_compact_mode = actor_count > self.max_actors_detailed
        
        print(f"\n{Color.SYSTEM}{'='*60}")
        print(f"  ACTOR STATUS ({actor_count} actors)")
        print(f"{'='*60}{Color.RESET}")
        
        if use_compact_mode:
            self._display_actor_status_compact(actors_to_display)
        else:
            self._display_actor_status_detailed(actors_to_display)
    
    def _display_actor_status_detailed(self, actors: List[Actor]):
        """Display detailed status for each actor."""
        for i, actor in enumerate(actors):
            if i > 0:
                print()  # Spacing between actors
            
            self._display_single_actor_detailed(actor)
    
    def _display_actor_status_compact(self, actors: List[Actor]):
        """Display compact status summary for many actors."""
        # Group actors by health status for quick overview
        healthy_actors = []
        injured_actors = []
        critical_actors = []
        
        for actor in actors:
            if actor.sheet.is_dead():
                critical_actors.append(actor)
            elif any(status.value < status.max_value * 0.5 for status in actor.sheet.statuses.values()):
                injured_actors.append(actor)
            else:
                healthy_actors.append(actor)
        
        # Display summary by health status
        if healthy_actors:
            print(f"\n{Color.SUCCESS}✓ HEALTHY ({len(healthy_actors)}):{Color.RESET}")
            self._display_actor_list_compact(healthy_actors)
        
        if injured_actors:
            print(f"\n{Color.WARNING}⚠ INJURED ({len(injured_actors)}):{Color.RESET}")
            self._display_actor_list_compact(injured_actors)
        
        if critical_actors:
            print(f"\n{Color.ERROR}💀 CRITICAL ({len(critical_actors)}):{Color.RESET}")
            self._display_actor_list_compact(critical_actors)
    
    def _display_actor_list_compact(self, actors: List[Actor]):
        """Display a compact list of actors with key status info."""
        for actor in actors:
            indicator = self._get_actor_type_indicator(actor)
            
            # Get most critical status
            critical_status = self._get_most_critical_status(actor)
            status_text = f"{critical_status['name']}: {critical_status['current']}/{critical_status['max']}"
            try:
                _nm = actor.get_display_name() if hasattr(actor, 'get_display_name') else actor.sheet.name
            except Exception:
                _nm = getattr(getattr(actor, 'sheet', None), 'name', None) or str(actor)
            print(f"  {indicator} {_nm} ({status_text})")
    
    def _display_single_actor_detailed(self, actor: Actor):
        """Display detailed information for a single actor."""
        indicator = self._get_actor_type_indicator(actor)

        try:
            _nm = actor.get_display_name() if hasattr(actor, 'get_display_name') else actor.sheet.name
        except Exception:
            _nm = getattr(getattr(actor, 'sheet', None), 'name', None) or str(actor)
        print(f"{Color.INFO}{indicator} {_nm} ({actor.sheet.occupation}){Color.RESET}")
        
        # Status display
        print(f"{Color.SYSTEM}Status:{Color.RESET}")
        for status_type, status in actor.sheet.statuses.items():
            status_name = status_type.name.title()
            current = status.value
            maximum = status.max_value
            percentage = (current / maximum * 100) if maximum > 0 else 0
            
            # Color code based on percentage
            if percentage >= 75:
                color = Color.SUCCESS
            elif percentage >= 50:
                color = Color.WARNING
            elif percentage >= 25:
                color = Color.ERROR
            else:
                color = Color.ERROR
            
            print(f"  {color}{status_name}: {current}/{maximum} ({percentage:.0f}%){Color.RESET}")
        
        # Show key relationships if not too many actors
        if self.verbosity_level in ["detailed", "verbose"]:
            self._display_actor_relationships_summary(actor)
    
    def _display_actor_relationships_summary(self, actor: Actor):
        """Display a summary of an actor's key relationships."""
        try:
            _nm = actor.get_display_name() if hasattr(actor, 'get_display_name') else actor.sheet.name
        except Exception:
            _nm = getattr(getattr(actor, 'sheet', None), 'name', None) or str(actor)
        relationships = self.sympathy_manager.get_actor_relationships(_nm)
        
        if not relationships:
            return
        
        # Get most significant relationships
        significant_relationships = []
        for other_name, relationship in relationships.items():
            if abs(relationship.current_sympathy) >= 2:  # Only show strong relationships
                significant_relationships.append((other_name, relationship.current_sympathy, relationship.relationship_type))
        
        if significant_relationships:
            print(f"{Color.SYSTEM}Key Relationships:{Color.RESET}")
            
            # Sort by sympathy strength
            significant_relationships.sort(key=lambda x: abs(x[1]), reverse=True)
            
            for other_name, sympathy, rel_type in significant_relationships[:self.max_relationships_shown]:
                rel_color = Color.SUCCESS if sympathy > 0 else Color.ERROR if sympathy < 0 else Color.WARNING
                print(f"  {rel_color}{other_name}: {sympathy:+d} ({rel_type.value}){Color.RESET}")
    
    def display_relationship_network_overview(self):
        """Display an overview of the entire relationship network."""
        analysis = self.sympathy_manager.analyze_relationship_network()
        
        if 'error' in analysis:
            print(f"{Color.WARNING}No relationship data available{Color.RESET}")
            return
        
        print(f"\n{Color.SYSTEM}{'='*60}")
        print(f"  RELATIONSHIP NETWORK OVERVIEW")
        print(f"{'='*60}{Color.RESET}")
        
        print(f"{Color.INFO}Network Statistics:{Color.RESET}")
        print(f"  Total Relationships: {analysis['total_relationships']}")
        print(f"  Average Sympathy: {analysis['average_sympathy']:.2f}")
        print(f"  Sympathy Range: {analysis['sympathy_range'][0]} to {analysis['sympathy_range'][1]}")
        
        if analysis.get('most_popular_actor'):
            print(f"  Most Popular: {analysis['most_popular_actor']} (avg: {analysis['most_popular_score']:.2f})")
        
        if analysis.get('most_friendly_actor'):
            print(f"  Most Friendly: {analysis['most_friendly_actor']} (avg: {analysis['most_friendly_score']:.2f})")
        
        # Show relationship type distribution
        distribution = analysis.get('relationship_distribution', {})
        if any(count > 0 for count in distribution.values()):
            print(f"\n{Color.INFO}Relationship Distribution:{Color.RESET}")
            for rel_type, count in distribution.items():
                if count > 0:
                    print(f"  {rel_type.replace('_', ' ').title()}: {count}")
    
    def _get_actor_type_indicator(self, actor: Optional[Actor]) -> str:
        """Get a visual indicator for actor type."""
        if not actor:
            return "❓"
        elif isinstance(actor, UserActor):
            return "👤"
        elif isinstance(actor, InanimateNonUserActor):
            return "🔧"
        elif isinstance(actor, NonUserActor):
            return "🤖"
        else:
            return "❓"
    
    def _get_most_critical_status(self, actor: Actor) -> Dict[str, Any]:
        """Get the most critical (lowest percentage) status for an actor."""
        most_critical = None
        lowest_percentage = 100
        
        for status_type, status in actor.sheet.statuses.items():
            if status.max_value > 0:
                percentage = (status.value / status.max_value) * 100
                if percentage < lowest_percentage:
                    lowest_percentage = percentage
                    most_critical = {
                        'name': status_type.name.title(),
                        'current': status.value,
                        'max': status.max_value,
                        'percentage': percentage
                    }
        
        return most_critical or {'name': 'Unknown', 'current': 0, 'max': 0, 'percentage': 0}
    
    def set_verbosity_level(self, level: str):
        """Set the verbosity level for reports."""
        valid_levels = ["minimal", "normal", "detailed", "verbose"]
        if level in valid_levels:
            self.verbosity_level = level
            print(f"{Color.INFO}Reporter verbosity set to: {level}{Color.RESET}")
        else:
            print(f"{Color.ERROR}Invalid verbosity level. Valid options: {', '.join(valid_levels)}{Color.RESET}")
    
    def get_simulation_overview(self) -> Dict[str, Any]:
        """Get comprehensive simulation overview."""
        all_actors = self.actor_manager.get_all_actors()
        active_actors = self.actor_manager.get_active_actors()
        
        # Get relationship statistics
        relationship_stats = self.sympathy_manager.get_network_analysis()
        
        return {
            'total_actors': len(all_actors),
            'active_actors': len(active_actors),
            'current_turn': self.actor_manager.get_current_turn(),
            'relationship_stats': relationship_stats,
            'reporter_settings': {
                'verbosity': self.verbosity_level,
                'detailed_display_limit': self.max_actors_detailed
            }
        }
    
    # ========== CRITICAL 6-STEP REPORTING METHODS ==========
    # These methods are essential for UTAS simulation output formatting
    
    @staticmethod
    def _safe_int(value):
        """Safely convert a value to integer, handling potential dictionary values."""
        if isinstance(value, dict):
            return value.get('value', 0) if 'value' in value else 0
        return int(value) if value is not None else 0
    
    def report_step1_proactor_interpretation(self, proactor_data: Dict[str, Any]):
        """Reports Step 1: Proactor Action Interpretation with full UTAS factors."""
        from narrative_utils import get_narrative_descriptor

        _pn = proactor_data.get('name')
        print(f"{Color.BOLD + Color.CYAN}STEP 1 - Proactor Action Interpretation (In this case, the Proactor is {_pn}){Color.RESET}")
        print()
        
        # Show if this was LLM or user action
        if proactor_data.get('is_user_actor', False):
            raw_input = proactor_data.get('raw_input', 'N/A')
            # Clean up raw input formatting
            if raw_input != 'N/A':
                raw_input = raw_input.strip().capitalize()
                if not raw_input.endswith(('.', '!', '?')):
                    raw_input += '.'
            print(f"User Action: {raw_input}")
        else:
            raw_action = proactor_data.get('raw_action', 'N/A')
            # Clean up raw action formatting
            if raw_action != 'N/A':
                raw_action = raw_action.strip().capitalize()
                if not raw_action.endswith(('.', '!', '?')):
                    raw_action += '.'
            print(f"LLM Action: {raw_action}")
        
        target_info = proactor_data.get('target_info')
        if target_info:
            target_type = target_info.get('target_type', 'unknown').upper()
            confidence = target_info.get('confidence', 'unknown')
            detected_target = target_info.get('detected_target', 'unknown')
            print(f"Target Type: {target_type} ({confidence} confidence) - {detected_target}")
        
        continuity = proactor_data.get('continuity_check', {})
        print("Continuity Check: (Repeat until the action is valid)")
        print(f"Judgement: {continuity.get('judgment', '[]')}")
        print(f"Continuity Narrative Justification: {continuity.get('justification', '[]')}")

        _pn = proactor_data.get('name')
        print(f"Proactor: {_pn}")
        print(f"Interpreted Action: {proactor_data.get('narrative_description', '[]')}")
        
        factors = proactor_data.get('utas_factors', {})
        print("UTAS Factors:")
        print(f"Exchange Type: {factors.get('exchange_type', '[]')}.")
        print(f"Targeted Reactor Status: {factors.get('status_to_shift', '[]')}.")
        
        s_trait_name = normalize_sfactor_label(factors.get('s_trait_to_use', '[]'))
        s_trait_value = factors.get('s_trait_value', 0)
        s_trait_desc = get_narrative_descriptor(s_trait_value)
        print(f"S-Trait: {s_trait_name} ({s_trait_value}). {factors.get('s_trait_justification', '[]')}")
        
        skill_data = factors.get('skill', {})
        if isinstance(skill_data, dict) and skill_data:
            skill_name = skill_data.get('name', 'None')
            skill_value = skill_data.get('value', 0)
        else:
            skill_name = 'None'
            skill_value = 0
        skill_desc = get_narrative_descriptor(skill_value)
        print(f"Skill: {skill_name} ({skill_value}).")
        print(f"Justification: {factors.get('skill_justification', '[]')}")
        
        endowment_data = factors.get('endowment', {})
        if isinstance(endowment_data, dict) and endowment_data:
            endowment_name = endowment_data.get('name', 'None')
            endowment_value = endowment_data.get('value', 0)
        else:
            endowment_name = 'None'
            endowment_value = 0
        endowment_desc = get_narrative_descriptor(endowment_value)
        print(f"Endowment: {endowment_name} ({endowment_value}).")
        
        supplement_data = factors.get('supplement', {})
        if isinstance(supplement_data, dict) and supplement_data:
            supplement_name = supplement_data.get('name', 'None')
            supplement_value = supplement_data.get('value', 0)
        else:
            supplement_name = 'None'
            supplement_value = 0
        print(f"Supplement: {supplement_name} ({supplement_value}).")
        
        # Stress level
        stress_level = factors.get('stress_level', 0)
        print(f"Stress Level: {stress_level}. {factors.get('stress_justification', '[]')}")
        
        self_effects = proactor_data.get('self_effects') or factors.get('self_effects')
        
        if self_effects:
            print(f"💰 Self-Inflicted Action Effects (Proactor Costs):")
            for i, effect in enumerate(self_effects, 1):
                print(f"Effect {i}:")
                print(f"Possible Self-Effect Condition: {effect.get('trigger', '[]')}.")
                print(f"Possible Self-Inflicted Target Status: {effect.get('status_shifted', '[]')}.")
                
                shift_magnitude = effect.get('shift_magnitude', 0)
                if shift_magnitude > 0:
                    polarity = "Additive"
                    polarity_desc = f"+{shift_magnitude}"
                elif shift_magnitude < 0:
                    polarity = "Subtractive" 
                    polarity_desc = f"{shift_magnitude}"
                else:
                    polarity = "[]"
                    polarity_desc = "[]"
                
                print(f"Possible Proactor Polarity Shift: {polarity} ({polarity_desc}).")
                print(f"Possible Proactor Type Shift: Temporary.")
                print(f"Self-Effect Severity: {effect.get('severity', '[]')}. {effect.get('severity_justification', '[]')}")
        else:
            print(f"💰 Self-Inflicted Action Effects (Proactor Costs):")
            print(f"Effect 1:")
            print(f"Possible Self-Effect Condition: [].")
            print(f"Possible Self-Inflicted Target Status: [].")
            print(f"Possible Proactor Polarity Shift: [] ([]).")
            print(f"Possible Proactor Type Shift: [].")
            print(f"Self-Effect Severity: []. []")
        print()

    def report_step2_proactor_success(self, proactor_data: Dict[str, Any]):
        """Reports Step 2: Proactor Success Calculation and Narrative."""
        print(f"{Color.BOLD + Color.CYAN}STEP 2 - Calculate Proactor's Success & Narrate{Color.RESET}")
        print()
        
        success_data = proactor_data.get('success_calculation', {})
        print("Success Calculation:")
        
        # Use the actual calculation string if available, otherwise build from components
        calc_str = success_data.get('calc_str')
        if calc_str:
            print(f"{calc_str}")
        elif isinstance(success_data.get('positive_components'), dict) and isinstance(success_data.get('negative_components'), dict):
            # Support unified_formula result directly
            pos = success_data['positive_components']
            neg = success_data['negative_components']
            try:
                s_trait = self._safe_int(pos.get('s_trait'))
                skill = self._safe_int(pos.get('skill'))
                endowment_val = self._safe_int(pos.get('endowment'))
                supplement = self._safe_int(pos.get('supplement'))
                serendipity = self._safe_int(pos.get('serendipity'))
                stress_mod = self._safe_int(neg.get('stress_modifier'))
                status_mod = self._safe_int(neg.get('status_modifier'))
                sympathy_mod = self._safe_int(neg.get('sympathy_modifier'))
                total = self._safe_int(success_data.get('final_result', pos.get('total', 0) - neg.get('total', 0)))
                print(
                    f"(S-Trait: {s_trait} + Skill: {skill} + Endowment: {endowment_val} + "
                    f"Supplement: {supplement} + Serendipity: {serendipity:+d}) - ("
                    f"Stress Modifier: {stress_mod:+d} + Status Modifier: {status_mod:+d} + "
                    f"Sympathy Modifier: {sympathy_mod:+d}) = {total}"
                )
            except Exception:
                print("Calculation incomplete due to missing factors.")
                print(f"  • S-Trait: {pos.get('s_trait', 'N/A')}")
                print(f"  • Skill: {pos.get('skill', 'N/A')}")
                print(f"  • Endowment: {pos.get('endowment', 'N/A')}")
                print(f"  • Supplement: {pos.get('supplement', 'N/A')}")
                print(f"  • Serendipity: {pos.get('serendipity', 'N/A')}")
                print(f"  • Stress Modifier: {neg.get('stress_modifier', 'N/A')}")
                print(f"  • Status Modifier: {neg.get('status_modifier', 'N/A')}")
                print(f"  • Sympathy Modifier: {neg.get('sympathy_modifier', 'N/A')}")
                print(f"  • Total: {success_data.get('final_result', 'N/A')}")
        else:
            # Fallback to component display with no defaults; show N/A/incomplete when missing
            s_trait = success_data.get('s_trait_value')
            skill = success_data.get('skill_value')
            endowment_val = success_data.get('endowment_value')
            supplement = success_data.get('supplement_value')
            serendipity = success_data.get('serendipity')
            stress_mod = success_data.get('stress_modifier')
            status_mod = success_data.get('status_modifier')
            sympathy_mod = success_data.get('sympathy_modifier')
            total = success_data.get('total')

            components = [s_trait, skill, endowment_val, supplement, serendipity, stress_mod, status_mod, sympathy_mod, total]
            if all(v is not None for v in components):
                print(
                    f"(S-Trait: {self._safe_int(s_trait)} + Skill: {self._safe_int(skill)} + Endowment: {self._safe_int(endowment_val)} + "
                    f"Supplement: {self._safe_int(supplement)} + Serendipity: {self._safe_int(serendipity):+d}) - ("
                    f"Stress Modifier: {self._safe_int(stress_mod):+d} + Status Modifier: {self._safe_int(status_mod):+d} + "
                    f"Sympathy Modifier: {self._safe_int(sympathy_mod):+d}) = {self._safe_int(total)}"
                )
            else:
                print("Calculation incomplete due to missing factors.")
                print(f"  • S-Trait: {s_trait if s_trait is not None else 'N/A'}")
                print(f"  • Skill: {skill if skill is not None else 'N/A'}")
                print(f"  • Endowment: {endowment_val if endowment_val is not None else 'N/A'}")
                print(f"  • Supplement: {supplement if supplement is not None else 'N/A'}")
                print(f"  • Serendipity: {serendipity if serendipity is not None else 'N/A'}")
                print(f"  • Stress Modifier: {stress_mod if stress_mod is not None else 'N/A'}")
                print(f"  • Status Modifier: {status_mod if status_mod is not None else 'N/A'}")
                print(f"  • Sympathy Modifier: {sympathy_mod if sympathy_mod is not None else 'N/A'}")
                print(f"  • Total: {total if total is not None else 'N/A'}")
        
        # Success determination
        success_threshold = success_data.get('success_threshold')
        total = success_data.get('total')
        if isinstance(total, int) and isinstance(success_threshold, int):
            is_success = total >= success_threshold
            success_text = "SUCCESS" if is_success else "FAILURE"
            print(f"Success Threshold: {success_threshold}")
            print(f"Result: {success_text} ({total} {'≥' if is_success else '<'} {success_threshold})")
        else:
            print("Success Threshold: N/A")
            print("Result: N/A (incomplete calculation)")
        
        # Narrative of attempt (collected for combined paragraph)
        actor_name = proactor_data.get('name', 'Unknown Actor')
        try:
            from stranger_description_system import get_nua_definite_description
            ua_actor = proactor_data.get('ua_actor')
            a_obj = proactor_data.get('actor')
            if ua_actor is not None:
                if a_obj is not None and not getattr(a_obj, 'is_user_actor', False):
                    actor_name = get_nua_definite_description(a_obj, ua_actor=ua_actor) or actor_name
                if proactor_data.get('reactor') is not None and not getattr(proactor_data.get('reactor'), 'is_user_actor', False):
                    reactor_name = get_nua_definite_description(proactor_data.get('reactor'), ua_actor=ua_actor) or proactor_data.get('reactor_name')
            else:
                reactor_name = proactor_data.get('reactor_name')
        except Exception:
            reactor_name = proactor_data.get('reactor_name')

        full_narrative = proactor_data.get('attempt_narrative') or proactor_data.get('narrative_description') or ""
        try:
            _actors_for_scrub = []
            if proactor_data.get('actor') is not None:
                _actors_for_scrub.append(proactor_data.get('actor'))
            if proactor_data.get('reactor') is not None:
                _actors_for_scrub.append(proactor_data.get('reactor'))
            full_narrative = self._scrub_unknown_names(full_narrative, _actors_for_scrub)
        except Exception:
            pass
        
        # Note: LLM now generates narratives in correct perspective from the start
        # No regex conversion needed - narratives should already be in second person for UA

        # Factors narrative: which traits/skills/tools influenced the attempt
        try:
            factors = proactor_data.get('utas_factors', {})
            s_name = normalize_sfactor_label(factors.get('s_trait_to_use', 'S-Trait'))
            s_val = self._safe_int(success_data.get('s_trait_value', factors.get('s_trait_value', 0)))
            s_desc = n2n_s_trait(s_val)

            skill = factors.get('skill', {}) if isinstance(factors.get('skill', {}), dict) else {}
            sk_name = skill.get('name', 'None')
            sk_val = self._safe_int(success_data.get('skill_value', skill.get('value', 0)))
            # Skills use competent/proficient/etc.; traits use minimal/subpar/etc.
            sk_desc = n2n_skill(sk_val)

            sup = factors.get('supplement', {}) if isinstance(factors.get('supplement', {}), dict) else {}
            sup_name = sup.get('name', 'None')
            sup_val = self._safe_int(success_data.get('supplement_value', sup.get('value', 0)))

            end = factors.get('endowment', {}) if isinstance(factors.get('endowment', {}), dict) else {}
            end_name = end.get('name', 'None')
            end_val = self._safe_int(success_data.get('endowment_value', end.get('value', 0)))

            ser = self._safe_int(success_data.get('serendipity', 0))
            ser_desc = n2n_serendipity(ser)

            stress_mod = self._safe_int(success_data.get('stress_modifier', 0))
            status_mod = self._safe_int(success_data.get('status_modifier', 0))
            sympathy_mod = self._safe_int(success_data.get('sympathy_modifier', 0))

            print("Factors Used:")
            print(f"  • S-Trait: {s_name} ({s_val}, {s_desc})")
            print(f"  • Skill: {sk_name} ({sk_val}, {sk_desc})")
            print(f"  • Endowment: {end_name} ({end_val})")
            print(f"  • Supplement: {sup_name} ({sup_val})")
            print(f"  • Serendipity: {ser:+d} ({ser_desc})")
            print("Modifiers:")
            print(f"  • Stress: {stress_mod:+d}")
            print(f"  • Status: {status_mod:+d}")
            print(f"  • Sympathy: {sympathy_mod:+d}")
            # Shift controls transparency
            print("Shift Controls:")
            stype_r = (factors.get('shift_type') or 'N/A')
            spol_r = (factors.get('shift_polarity') or 'N/A')
            print(f"  • Shift Type: {stype_r}")
            print(f"  • Shift Polarity: {spol_r}")
            
            # Build connected N2N attempt summary (defer printing; will be combined with narrative and success)
            attempt_summary_text = ""
            try:
                difficulty = get_narrative_descriptor(self._safe_int(factors.get('stress_level', 3)))
                exchange_type = (factors.get('exchange_type') or '').strip().title() or 'Action'
                status_to_shift = (factors.get('status_to_shift') or '').strip().upper() or 'STATUS'
                # Do not narrate "Sympathy" as a status target; it's a modifier. Prefer SPIRIT for social attempts.
                if status_to_shift == 'SYMPATHY':
                    status_to_shift = 'SPIRIT'
                # Polarity label (Additive/Subtractive) appended after difficulty if available
                pol_raw = (factors.get('shift_polarity') or '').strip().title()
                polarity_label = pol_raw if pol_raw in ('Additive', 'Subtractive') else ''
                polarity_segment = f" ({polarity_label})" if polarity_label else ''
                # Avoid duplicating the targeted status if the attempt narrative already states it
                status_clause = f"focusing on the opponent's {status_to_shift}."
                try:
                    if isinstance(full_narrative, str) and status_to_shift and status_to_shift.lower() in full_narrative.lower():
                        status_clause = ""
                except Exception:
                    pass
                # Use "You" for UA, actor name for NUA
                is_user_actor = proactor_data.get('is_user_actor', False)
                subject = "You" if is_user_actor else proactor_data.get('name', 'Unknown Actor')
                subject_verb = "initiate" if is_user_actor else "initiates"
                subject_employ = "employ" if is_user_actor else "employs"
                
                attempt_summary_text = (
                    f"{subject} {subject_verb} a {difficulty}{polarity_segment} attempt at {exchange_type}, "
                    f"{status_clause + ' ' if status_clause else ''}To achieve this, {subject} {subject_employ} the {sk_desc} {sk_name} "
                    f"and the {s_desc} {s_name}. This action is undertaken with {ser_desc} Serendipity."
                )
            except Exception:
                attempt_summary_text = ""
        except Exception:
            # Absolute fallback attempt summary with minimal fields
            try:
                difficulty = get_narrative_descriptor(3)
            except Exception:
                difficulty = 'Average'
            is_user_actor = proactor_data.get('is_user_actor', False)
            subject = "You" if is_user_actor else (actor_name if actor_name else 'Unknown Actor')
            subject_verb = "initiate" if is_user_actor else "initiates"
            attempt_summary_text = f"{subject} {subject_verb} a {difficulty} attempt."

        # Build success narration (defer printing)
        success_line_text = ""
        try:
            # Fallback to 'final_result' or 'success' if 'total' is missing
            tot = self._safe_int(success_data.get('total', success_data.get('final_result', success_data.get('success', 0))))
            if tot <= 0:
                label = "FAILED"
            elif tot == 1:
                label = "MINIMAL"
            elif tot == 2:
                label = "SUBPAR"
            elif tot == 3:
                label = "AVERAGE"
            elif tot == 4:
                label = "EXTRAORDINARY"
            elif tot == 5:
                label = "SUPERB"
            elif tot == 6:
                label = "CRITICAL SUCCESS"
            else:
                label = f"CRITICAL SUCCESS +{tot - 6}"
            is_user_actor = proactor_data.get('is_user_actor', False)
            actor_name = proactor_data.get('name', 'Unknown Actor')
            if is_user_actor:
                success_line_text = f"Your attempt registers as {label} ({tot} successes)."
            else:
                success_line_text = f"{actor_name}'s attempt registers as {label} ({tot} successes)."
        except Exception:
            # Fallback success line without numeric detail
            is_user_actor = proactor_data.get('is_user_actor', False)
            if is_user_actor:
                success_line_text = f"Your attempt registers as {success_text}."
            else:
                success_line_text = f"{actor_name}'s attempt registers as {success_text}."

        # Print perceptual narrative with success info
        if full_narrative and full_narrative.strip():
            is_ua = bool(proactor_data.get('is_user_actor', False))
            _step2_display_text = None
            if is_ua:
                ua_line = (proactor_data.get('ua_attempt_text') or '').strip()
                if ua_line:
                    print(f"{Color.NARRATIVE}{ua_line}{Color.RESET}")
                    _step2_display_text = ua_line
                else:
                    # Fallback: CRITICAL USER AGENCY: keep minimal and do not add dialogue.
                    raw = (
                        proactor_data.get('interpreted_user_action')
                        or proactor_data.get('raw_user_action')
                        or proactor_data.get('action_description')
                        or proactor_data.get('narrative_description')
                        or full_narrative
                    )
                    raw = (raw or '').strip()
                    try:
                        if (len(raw) >= 2) and ((raw[0] == raw[-1]) and raw[0] in ('"', "'")):
                            raw = f"say {raw}"
                    except Exception:
                        pass
                    print(f"{Color.NARRATIVE}You attempt to ({raw}){Color.RESET}")
                    _step2_display_text = f"You attempt to ({raw})"
            else:
                print(f"Narrative of {actor_name}'s Attempt:")
                print(f"{Color.NARRATIVE}{full_narrative.strip()}{Color.RESET}")
                _step2_display_text = full_narrative.strip()

                # Add success level and targeted status on separate lines
                if success_line_text:
                    print(f"{Color.SYSTEM}{success_line_text}{Color.RESET}")

                # Show targeted status if available
                try:
                    factors = proactor_data.get('utas_factors', {})
                    status_to_shift = (factors.get('status_to_shift') or '').strip().upper()
                    shift_polarity = (factors.get('shift_polarity') or '').strip().title()
                    if status_to_shift and shift_polarity:
                        print(f"{Color.SYSTEM}Targeted Status: {status_to_shift} ({shift_polarity}){Color.RESET}")
                except Exception:
                    pass
            # Route step 2 narrative to the narrative display
            if _step2_display_text:
                try:
                    from pygame_narrative_display import send_narrator, send_separator
                    send_separator()
                    send_narrator(_step2_display_text)
                except Exception:
                    pass
        print()

    def report_step3_reactor_interpretation(self, reactor_data: Dict[str, Any], proactor_summary: str):
        """Reports Step 3: Reactor Action Interpretation."""
        from narrative_utils import get_narrative_descriptor

        _rn = reactor_data.get('name')
        print(f"{Color.BOLD + Color.CYAN}STEP 3 - Reactor Action Interpretation (In this case, the Reactor is {_rn}){Color.RESET}")
        print()
        
        print(f"Proactor Summary: {proactor_summary}")
        
        # Show reactor sheet data
        sheet_data = reactor_data.get('sheet_data', {})
        if sheet_data:
            print(f"\n{Color.INFO}📋 {_rn}'s Current Status:{Color.RESET}")
            
            # S-Factors
            s_factors = sheet_data.get('s_factors', {})
            if s_factors:
                print(f"{Color.SYSTEM}S-Factors:{Color.RESET}")
                for factor_name, factor_value in s_factors.items():
                    desc = get_narrative_descriptor(factor_value)
                    print(f"  {factor_name}: {factor_value} ({desc})")
            
            # Statuses
            statuses = sheet_data.get('statuses', {})
            if statuses:
                print(f"{Color.SYSTEM}Statuses:{Color.RESET}")
                for status_name, status_info in statuses.items():
                    current = status_info.get('current', 0)
                    max_val = status_info.get('max', 0)
                    print(f"  {status_name}: {current}/{max_val}")
        
        # Reactor action interpretation
        raw_action = reactor_data.get('raw_action', 'N/A')
        if raw_action != 'N/A':
            raw_action = raw_action.strip().capitalize()
            if not raw_action.endswith(('.', '!', '?')):
                raw_action += '.'
        print(f"\nLLM Action: {raw_action}")
        
        is_ua = bool(reactor_data.get('is_user_actor', False))
        _rn = reactor_data.get('name')
        print(f"Reactor: {_rn} {'(UA)' if is_ua else '(NUA)'}")
        if is_ua:
            ua_line = (reactor_data.get('ua_attempt_text') or '').strip()
            if ua_line:
                print(f"{ua_line}")
            else:
                raw = (
                    reactor_data.get('interpreted_user_action')
                    or reactor_data.get('raw_user_action')
                    or reactor_data.get('action_description')
                    or reactor_data.get('narrative_description')
                    or 'N/A'
                )
                raw = (raw or '').strip()
                try:
                    if (len(raw) >= 2) and ((raw[0] == raw[-1]) and raw[0] in ('"', "'")):
                        raw = f"say {raw}"
                except Exception:
                    pass
                print(f"You attempt to ({raw})")
        else:
            print(f"Intended Reaction: {reactor_data.get('narrative_description', 'N/A')}")
        
        factors = reactor_data.get('utas_factors', {})
        print("UTAS Factors (UTAS OBJECTIVE Step 4):")
        
        print("1. Core Defensive Factors:")
        
        # Use standard UTAS field names that the LLM actually provides
        action_desc = reactor_data.get('action_description', 'N/A')
        print(f"   Action Description: {action_desc}")
        
        s_trait = factors.get('s_trait_to_use', 'N/A')
        s_trait_value = factors.get('s_trait_value', 0)
        print(f"   S-Trait: {s_trait} ({s_trait_value})")
        print(f"   S-Trait Justification: {factors.get('s_trait_justification', 'N/A')}")
        
        skill_data = factors.get('skill', {})
        if isinstance(skill_data, dict) and skill_data:
            skill_name = skill_data.get('name', 'None')
            skill_value = skill_data.get('value', 0)
        else:
            skill_name = 'None'
            skill_value = 0
        print(f"   Skill: {skill_name} ({skill_value})")
        print(f"   Skill Justification: {factors.get('skill_justification', 'N/A')}")
        
        endowment_data = factors.get('endowment', {})
        if isinstance(endowment_data, dict) and endowment_data:
            endowment_name = endowment_data.get('name', 'None')
            endowment_value = endowment_data.get('value', 0)
        else:
            endowment_name = 'None'
            endowment_value = 0
        print(f"   Endowment: {endowment_name} ({endowment_value})")
        
        supplement_data = factors.get('supplement', {})
        if isinstance(supplement_data, dict) and supplement_data:
            supplement_name = supplement_data.get('name', 'None')
            supplement_value = supplement_data.get('value', 0)
        else:
            supplement_name = 'None'
            supplement_value = 0
        print(f"   Supplement: {supplement_name} ({supplement_value})")
        
        exchange_type = factors.get('exchange_type', 'N/A')
        status_to_shift = factors.get('status_to_shift', 'N/A')
        print(f"   Exchange Type: {exchange_type}")
        print(f"   Status to Shift: {status_to_shift}")
        
        stress_level = factors.get('stress_level', 'N/A')
        stress_justification = factors.get('stress_justification', 'N/A')
        print(f"   Stress Level: {stress_level}")
        print(f"   Stress Justification: {stress_justification}")
        
        shift_type = factors.get('shift_type', 'N/A')
        shift_polarity = factors.get('shift_polarity', 'N/A')
        print(f"   Shift Type: {shift_type}")
        print(f"   Shift Polarity: {shift_polarity}")
        
        print("\n2. Secondary Effects (Reactive Opportunities):")
        has_secondary = factors.get('has_secondary_effect', 'FALSE')
        print(f"   Has Secondary Effect: {has_secondary}")
        secondary_justification = factors.get('secondary_effect_justification', 'N/A')
        print(f"   Secondary Effect Justification: {secondary_justification}")
        
        print("\n3. Self-Effects (Reactor Costs):")
        self_effects = reactor_data.get('self_effects', [])
        if self_effects and len(self_effects) > 0:
            for i, effect in enumerate(self_effects, 1):
                print(f"   Effect {i}:")
                print(f"     Condition: {effect.get('trigger', 'N/A')}")
                print(f"     Target Status: {effect.get('status_shifted', 'N/A')}")
                print(f"     Magnitude: {effect.get('shift_magnitude', 0)}")
                print(f"     Severity: {effect.get('severity', 0)}")
        else:
            print(f"   No self-effects specified")
        
        print()

    def report_step4_reactor_success(self, reactor_data: Dict[str, Any]):
        """Reports Step 4: Reactor Success Calculation and Narrative."""
        print(f"{Color.BOLD + Color.CYAN}STEP 4 - Calculate Reactor's Success & Narrate{Color.RESET}")
        
        # Check if reactor is UA
        is_user_actor = reactor_data.get('is_user_actor', False)
        
        success_data = reactor_data.get('success_calculation', {})
        print("Success Calculation:")
        
        # Use the actual calculation string if available, otherwise build from components
        calc_str = success_data.get('calc_str')
        if calc_str:
            print(f"{calc_str}")
        elif isinstance(success_data.get('positive_components'), dict) and isinstance(success_data.get('negative_components'), dict):
            # Support unified_formula result directly
            pos = success_data['positive_components']
            neg = success_data['negative_components']
            try:
                s_trait = self._safe_int(pos.get('s_trait'))
                skill = self._safe_int(pos.get('skill'))
                endowment_val = self._safe_int(pos.get('endowment'))
                supplement = self._safe_int(pos.get('supplement'))
                serendipity = self._safe_int(pos.get('serendipity'))
                stress_mod = self._safe_int(neg.get('stress_modifier'))
                status_mod = self._safe_int(neg.get('status_modifier'))
                sympathy_mod = self._safe_int(neg.get('sympathy_modifier'))
                total = self._safe_int(success_data.get('final_result', pos.get('total', 0) - neg.get('total', 0)))
                print(
                    f"(S-Trait: {s_trait} + Skill: {skill} + Endowment: {endowment_val} + "
                    f"Supplement: {supplement} + Serendipity: {serendipity:+d}) - ("
                    f"Stress Modifier: {stress_mod:+d} + Status Modifier: {status_mod:+d} + "
                    f"Sympathy Modifier: {sympathy_mod:+d}) = {total}"
                )
            except Exception:
                print("Calculation incomplete due to missing factors.")
                print(f"  • S-Trait: {pos.get('s_trait', 'N/A')}")
                print(f"  • Skill: {pos.get('skill', 'N/A')}")
                print(f"  • Endowment: {pos.get('endowment', 'N/A')}")
                print(f"  • Supplement: {pos.get('supplement', 'N/A')}")
                print(f"  • Serendipity: {pos.get('serendipity', 'N/A')}")
                print(f"  • Stress Modifier: {neg.get('stress_modifier', 'N/A')}")
                print(f"  • Status Modifier: {neg.get('status_modifier', 'N/A')}")
                print(f"  • Sympathy Modifier: {neg.get('sympathy_modifier', 'N/A')}")
                print(f"  • Total: {success_data.get('final_result', 'N/A')}")
        else:
            # Fallback to component display - use same field names as working reporter.py
            s_trait = self._safe_int(success_data.get('s_trait_value', 0))
            skill = self._safe_int(success_data.get('skill_value', 0))
            endowment_val = self._safe_int(success_data.get('endowment_value', 0))
            supplement = self._safe_int(success_data.get('supplement_value', 0))
            serendipity = self._safe_int(success_data.get('serendipity', 0))
            stress_mod = self._safe_int(success_data.get('stress_modifier', 0))
            status_mod = self._safe_int(success_data.get('status_modifier', 0))
            sympathy_mod = self._safe_int(success_data.get('sympathy_modifier', 0))
            total = self._safe_int(success_data.get('total', 0))
            
            print(
                f"(S-Trait: {s_trait} + Skill: {skill} + Endowment: {endowment_val} + "
                f"Supplement: {supplement} + Serendipity: {serendipity:+d}) - ("
                f"Stress Modifier: {stress_mod:+d} + Status Modifier: {status_mod:+d} + "
                f"Sympathy Modifier: {sympathy_mod:+d}) = {total}"
            )
        
        # Success determination
        success_threshold = success_data.get('success_threshold', 0)
        total = success_data.get('total', 0)
        is_success = total >= success_threshold
        success_text = "SUCCESS" if is_success else "FAILURE"
        
        print(f"Success Threshold: {success_threshold}")
        print(f"Result: {success_text} ({total} {'≥' if is_success else '<'} {success_threshold})")
        
        # Narrative of reaction (collected for combined paragraph)
        actor_name = reactor_data.get('name', 'Unknown Actor')
        try:
            from stranger_description_system import get_nua_definite_description
            ua_actor = reactor_data.get('ua_actor')
            a_obj = reactor_data.get('actor')
            if ua_actor is not None and a_obj is not None and not getattr(a_obj, 'is_user_actor', False):
                actor_name = get_nua_definite_description(a_obj, ua_actor=ua_actor) or actor_name
        except Exception:
            pass

        full_narrative = reactor_data.get('attempt_narrative') or reactor_data.get('narrative_description') or ""
        try:
            _actors_for_scrub = []
            if reactor_data.get('actor') is not None:
                _actors_for_scrub.append(reactor_data.get('actor'))
            if reactor_data.get('ua_actor') is not None:
                _actors_for_scrub.append(reactor_data.get('ua_actor'))
            full_narrative = self._scrub_unknown_names(full_narrative, _actors_for_scrub)
        except Exception:
            pass

        # For UA, prefer the perceptual attempt narration if provided.
        if reactor_data.get('is_user_actor', False):
            try:
                _ua_line = (reactor_data.get('ua_attempt_text') or '').strip()
                if _ua_line:
                    full_narrative = _ua_line
            except Exception:
                pass
        
        # Note: LLM now generates narratives in correct perspective from the start
        # No regex conversion needed - narratives should already be in second person for UA

        # Factors narrative for reactor
        try:
            factors = reactor_data.get('utas_factors', {})
            s_name = factors.get('s_trait_to_use', 'S-Trait')
            s_val = self._safe_int(success_data.get('s_trait_value', factors.get('s_trait_value', 0)))
            s_desc = n2n_s_trait(s_val)

            skill = factors.get('skill', {}) if isinstance(factors.get('skill', {}), dict) else {}
            sk_name = skill.get('name', 'None')
            sk_val = self._safe_int(success_data.get('skill_value', skill.get('value', 0)))
            sk_desc = get_narrative_descriptor(sk_val)

            sup = factors.get('supplement', {}) if isinstance(factors.get('supplement', {}), dict) else {}
            sup_name = sup.get('name', 'None')
            sup_val = self._safe_int(success_data.get('supplement_value', sup.get('value', 0)))

            spr = factors.get('super', {}) if isinstance(factors.get('super', {}), dict) else {}
            spr_name = spr.get('name', 'None')
            spr_val = self._safe_int(success_data.get('super_value', spr.get('value', 0)))

            ser = self._safe_int(success_data.get('serendipity', 0))
            ser_desc = n2n_serendipity(ser)

            stress_mod = self._safe_int(success_data.get('stress_modifier', 0))
            status_mod = self._safe_int(success_data.get('status_modifier', 0))
            sympathy_mod = self._safe_int(success_data.get('sympathy_modifier', 0))

            print("Factors Used:")
            print(f"  • S-Trait: {s_name} ({s_val}, {s_desc})")
            print(f"  • Skill: {sk_name} ({sk_val}, {sk_desc})")
            print(f"  • Super: {spr_name} ({spr_val})")
            print(f"  • Supplement: {sup_name} ({sup_val})")
            print(f"  • Serendipity: {ser:+d} ({ser_desc})")
            print("Modifiers:")
            print(f"  • Stress: {stress_mod:+d}")
            print(f"  • Status: {status_mod:+d}")
            print(f"  • Sympathy: {sympathy_mod:+d}")
        except Exception:
            # Fallback success line without numeric detail
            is_user_actor = reactor_data.get('is_user_actor', False)
            if is_user_actor:
                success_line_text = f"Your reaction registers as {success_text}."
            else:
                success_line_text = f"{actor_name}'s reaction registers as {success_text}."

        # Build attempt summary for reactor and success narration; then print combined paragraph
        # Attempt summary mirrors Step 2 wording
        attempt_summary_text = ""
        try:
            s_name = factors.get('s_trait_to_use', 'S-Trait')
            s_val = self._safe_int(success_data.get('s_trait_value', factors.get('s_trait_value', 0)))
            s_desc = n2n_s_trait(s_val)
            ser = self._safe_int(success_data.get('serendipity', 0))
            ser_desc = n2n_serendipity(ser)
            difficulty = get_narrative_descriptor(self._safe_int(factors.get('stress_level', 3)))
            exchange_type = (factors.get('exchange_type') or '').strip().title() or 'Action'
            status_to_shift = (factors.get('status_to_shift') or '').strip().upper() or 'STATUS'
            if status_to_shift == 'SYMPATHY':
                status_to_shift = 'SPIRIT'
            # Polarity label (Additive/Subtractive) appended after difficulty if available
            pol_raw = (factors.get('shift_polarity') or '').strip().title()
            polarity_label = pol_raw if pol_raw in ('Additive', 'Subtractive') else ''
            polarity_segment = f" ({polarity_label})" if polarity_label else ''
            status_clause = f"focusing on the opponent's {status_to_shift}."
            try:
                if isinstance(full_narrative, str) and status_to_shift and status_to_shift.lower() in full_narrative.lower():
                    status_clause = ""
            except Exception:
                pass
            # Use "You" for UA, actor name for NUA
            is_user_actor = reactor_data.get('is_user_actor', False)
            subject = "You" if is_user_actor else reactor_data.get('name', 'Unknown Actor')
            subject_verb = "initiate" if is_user_actor else "initiates"
            subject_employ = "employ" if is_user_actor else "employs"
            
            attempt_summary_text = (
                f"{subject} {subject_verb} a {difficulty}{polarity_segment} attempt at {exchange_type}, "
                f"{status_clause + ' ' if status_clause else ''}To achieve this, {subject} {subject_employ} the {sk_desc} {sk_name} "
                f"and the {s_desc} {s_name}. This action is undertaken with {ser_desc} Serendipity."
            )
        except Exception:
            # Absolute fallback attempt summary with minimal fields
            try:
                difficulty = get_narrative_descriptor(3)
            except Exception:
                difficulty = 'Average'
            is_user_actor = reactor_data.get('is_user_actor', False)
            subject = "You" if is_user_actor else (actor_name if actor_name else 'Unknown Actor')
            subject_verb = "initiate" if is_user_actor else "initiates"
            attempt_summary_text = f"{subject} {subject_verb} a {difficulty} attempt."

        success_line_text = ""
        try:
            # Fallback to 'final_result' or 'success' if 'total' is missing
            tot = self._safe_int(success_data.get('total', success_data.get('final_result', success_data.get('success', 0))))
            if tot <= 0:
                label = "FAILED"
            elif tot == 1:
                label = "MINIMAL"
            elif tot == 2:
                label = "SUBPAR"
            elif tot == 3:
                label = "AVERAGE"
            elif tot == 4:
                label = "EXTRAORDINARY"
            elif tot == 5:
                label = "SUPERB"
            elif tot == 6:
                label = "CRITICAL SUCCESS"
            else:
                label = f"CRITICAL SUCCESS +{tot - 6}"
            is_user_actor = reactor_data.get('is_user_actor', False)
            actor_name = reactor_data.get('name', 'Unknown Actor')
            if is_user_actor:
                success_line_text = f"Your reaction registers as {label} ({tot} successes)."
            else:
                success_line_text = f"{actor_name}'s reaction registers as {label} ({tot} successes)."
        except Exception:
            pass

        # Print perceptual narrative with success info
        if full_narrative and full_narrative.strip():
            is_user_actor = reactor_data.get('is_user_actor', False)
            actor_name = reactor_data.get('name', 'Unknown Actor')
            header = "Narrative of Your Reaction:" if is_user_actor else f"Narrative of {actor_name}'s Reaction:"
            print(f"{header}")
            print(f"{Color.NARRATIVE}{full_narrative.strip()}{Color.RESET}")

            # Add success level and targeted status on separate lines
            if success_line_text:
                print(f"{Color.SYSTEM}{success_line_text}{Color.RESET}")

            # Show targeted status if available
            try:
                factors = reactor_data.get('utas_factors', {})
                status_to_shift = (factors.get('status_to_shift') or '').strip().upper()
                shift_polarity = (factors.get('shift_polarity') or '').strip().title()
                if status_to_shift and shift_polarity:
                    print(f"{Color.SYSTEM}Targeted Status: {status_to_shift} ({shift_polarity}){Color.RESET}")
            except Exception:
                pass
            # Route step 4 narrative to the narrative display
            try:
                from pygame_narrative_display import send_narrator
                send_narrator(full_narrative.strip())
            except Exception:
                pass
        print()

    def report_step5_final_outcome(self, outcome_data: Dict[str, Any]):
        """Reports Step 5: Final Outcome Calculation and Status Updates."""
        print(f"{Color.BOLD + Color.CYAN}STEP 5 - Calculate Final Outcome & Update Statuses{Color.RESET}")
        print()
        
        # Proactor and Reactor success results
        proactor_successes = self._safe_int(outcome_data.get('proactor_successes', 0))
        reactor_successes = self._safe_int(outcome_data.get('reactor_successes', 0))
        margin = self._safe_int(outcome_data.get('margin', 0))
        proactor_name = outcome_data.get('proactor_name', 'Proactor')
        reactor_name = outcome_data.get('reactor_name', 'Reactor')
        
        stress_context = outcome_data.get('stress_context', '')
        if stress_context:
            print(stress_context)
        
        print("Final Outcome Calculation:")
        print(f"Proactor Successes ({proactor_name}): {proactor_successes}")
        print(f"Reactor Successes ({reactor_name}): {reactor_successes}")
        print(f"Raw Success Difference: {proactor_successes} - {reactor_successes} = {margin:+d} ({'Proactor Wins' if margin > 0 else 'Reactor Wins' if margin < 0 else 'Tie'}).")
        
        # Always display the shift calculation; prefer explicit 'shift_calc_formula',
        # otherwise fall back to 'shift_calc' if provided by the exchange system.
        shift_calc_formula = outcome_data.get('shift_calc_formula') or outcome_data.get('shift_calc')
        if shift_calc_formula:
            print(f"Status Shift Calculation: {shift_calc_formula}")
        
        status_shifts = outcome_data.get('status_shifts') or []
        for shift in status_shifts:
            # Accept both legacy and new schemas
            actor_name = shift.get('actor_name') or shift.get('actor') or 'N/A'
            status_name = shift.get('status_name') or shift.get('status_type') or shift.get('status') or 'Status'
            shift_value = shift.get('shift_value') if shift.get('shift_value') is not None else shift.get('delta', 0)
            original_value = shift.get('original_value') if shift.get('original_value') is not None else shift.get('original', 0)
            new_value = shift.get('new_value') if shift.get('new_value') is not None else shift.get('updated', 0)
            original_desc = shift.get('original_descriptor')
            new_desc = shift.get('new_descriptor')
            # Derive descriptors if missing
            try:
                if original_desc is None and original_value is not None:
                    original_desc = get_narrative_descriptor(int(original_value))
                if new_desc is None and new_value is not None:
                    new_desc = get_narrative_descriptor(int(new_value))
            except Exception:
                original_desc = original_desc or 'N/A'
                new_desc = new_desc or 'N/A'
            # Build a concise description if none provided
            shift_description = shift.get('description')
            if not shift_description:
                try:
                    mag_desc = n2n_shift_magnitude(abs(int(shift_value))) if shift_value is not None else 'Null'
                except Exception:
                    mag_desc = 'Null'
                pol = 'Penalty' if (isinstance(shift_value, (int,float)) and shift_value < 0) else 'Boost'
                shift_description = f"{status_name} {mag_desc} {pol}."

            # Perspective: only use "Your" if the affected actor is the UA.
            pro_is_ua = bool(outcome_data.get('proactor_is_user_actor', False))
            rea_is_ua = bool(outcome_data.get('reactor_is_user_actor', False))
            pro_name = outcome_data.get('proactor_name')
            rea_name = outcome_data.get('reactor_name')
            actor_is_ua = (pro_is_ua and actor_name == pro_name) or (rea_is_ua and actor_name == rea_name)
            possessive = "Your" if actor_is_ua else f"{actor_name}'s"
            print(f"Status Shift Calculation ({actor_name}):")
            print(shift_description)
            print(f"Shift Value: {int(shift_value) if isinstance(shift_value, (int, float)) else shift_value}. {possessive} {status_name} of {int(original_value) if isinstance(original_value, (int,float)) else original_value} is {'reduced' if (isinstance(shift_value,(int,float)) and shift_value < 0) else 'increased'} by {abs(int(shift_value)) if isinstance(shift_value,(int,float)) else shift_value}, {'which is floored at 0' if (isinstance(new_value,(int,float)) and int(new_value) == 0 and isinstance(shift_value,(int,float)) and shift_value < 0) else ''}.")
            print(f"{possessive} new {status_name} is {int(new_value) if isinstance(new_value,(int,float)) else new_value} ({new_desc}).")
        
        applied_effects = outcome_data.get('applied_self_effects')
        for effect in applied_effects:
            actor_name = effect.get('actor_name', 'N/A')
            trigger = effect.get('trigger', 'N/A')
            status_name = effect.get('status_name', 'N/A')
            shift_type = effect.get('shift_type', 'N/A')
            shift_polarity = effect.get('shift_polarity', 'N/A')
            shift_value = effect.get('shift_value', 0)
            new_value = effect.get('new_value', 0)
            new_desc = effect.get('new_descriptor', 'N/A')
            
            print(f"Status Shift Calculation ({actor_name}):")
            print(f"Due to {trigger.lower()}, the {actor_name}'s \"On Action {'Success' if 'success' in trigger.lower() else 'Failure'}\" self-effect is triggered.")
            print(f"{'She' if 'Lady' in actor_name else 'He'} gains a {shift_type}, {shift_polarity} shift of {shift_value} to {'her' if 'Lady' in actor_name else 'his'} {status_name}.")
            print(f"{'Her' if 'Lady' in actor_name else 'His'} new {status_name} is {new_value} ({new_desc}).")
        
        # INUA environmental effects (if any)
        env_effects = outcome_data.get('environmental_effects_applied') or []
        if env_effects:
            print(f"\n{Color.SYSTEM}Environmental Effects (INUA):{Color.RESET}")
            for e in env_effects:
                actor_name = e.get('actor_name') or e.get('actor') or 'N/A'
                status_name = e.get('status_name') or e.get('status_type') or e.get('status') or 'Status'
                shift_value = e.get('shift_value') if e.get('shift_value') is not None else e.get('delta', 0)
                original_value = e.get('original_value') if e.get('original_value') is not None else e.get('original', 0)
                new_value = e.get('new_value') if e.get('new_value') is not None else e.get('updated', 0)
                original_desc = e.get('original_descriptor')
                new_desc = e.get('new_descriptor')
                try:
                    if original_desc is None and original_value is not None:
                        original_desc = get_narrative_descriptor(int(original_value))
                    if new_desc is None and new_value is not None:
                        new_desc = get_narrative_descriptor(int(new_value))
                except Exception:
                    original_desc = original_desc or 'N/A'
                    new_desc = new_desc or 'N/A'
                description = e.get('description') or "Environmental consequence applied."
                print(f"Status Shift Calculation ({actor_name}):")
                print(description)
                print(f"Shift Value: {int(shift_value) if isinstance(shift_value,(int,float)) else shift_value}. Your {status_name} of {int(original_value) if isinstance(original_value,(int,float)) else original_value} is {'reduced' if (isinstance(shift_value,(int,float)) and shift_value < 0) else 'increased'} by {abs(int(shift_value)) if isinstance(shift_value,(int,float)) else shift_value}.")
                print(f"Your new {status_name} is {int(new_value) if isinstance(new_value,(int,float)) else new_value} ({new_desc}).")

        print()

    def _build_status_effect_phrase(self, proactor_name: str, reactor_name: str, outcome_data: Dict[str, Any]) -> str:
        """Build explicit phrase: "with [loser]'s [STATUS] experiencing a/an [Magnitude] [Penalty|Boost]."
        Returns empty string if insufficient data.
        """
        try:
            pro_succ = self._safe_int(outcome_data.get('proactor_successes', 0))
            rea_succ = self._safe_int(outcome_data.get('reactor_successes', 0))
            if pro_succ == rea_succ:
                return ""  # stalemate; handled elsewhere
            loser_name = reactor_name if pro_succ > rea_succ else proactor_name
            shifts = outcome_data.get('status_shifts') or []
            # Prefer shift entry that matches the loser
            loser_shift = next((s for s in shifts if (s.get('actor_name') or s.get('actor')) == loser_name), None)
            if not loser_shift:
                loser_shift = shifts[0] if shifts else None
            if not loser_shift:
                return ""
            status_name = str(
                loser_shift.get('status_type')
                or loser_shift.get('status_name')
                or loser_shift.get('status')   # raw Step 5 key
                or 'STATUS'
            ).upper()
            raw_shift = loser_shift.get('shift_value') if loser_shift.get('shift_value') is not None else loser_shift.get('delta', 0)
            try:
                mag = abs(int(raw_shift))
            except Exception:
                mag = 0
            # Use N2N magnitude descriptor already imported
            try:
                magnitude_desc = n2n_shift_magnitude(mag)
            except Exception:
                magnitude_desc = 'Null'
            if isinstance(raw_shift, (int, float)) and raw_shift < 0:
                pol = 'Penalty'
            elif isinstance(raw_shift, (int, float)) and raw_shift > 0:
                pol = 'Boost'
            else:
                pol = 'Impact'
            # Simple article heuristic
            article = 'an' if magnitude_desc and magnitude_desc[:1].lower() in 'aeiou' else 'a'
            return f"with {loser_name}'s {status_name} experiencing {article} {magnitude_desc} {pol}."
        except Exception:
            return ""

    def report_step6_narrative_outcome(self, proactor_data: Dict[str, Any], reactor_data: Dict[str, Any], outcome_data: Dict[str, Any], narrator_agent, scene_context: str = None, is_remote_encounter: bool = False, remote_encounter_type: str = None, ua_actor=None) -> str:
        """Reports Step 6: Comprehensive Narrative Synthesis per UTAS OBJECTIVE.md specification.
        
        Args:
            scene_context: Current location/scene description (FIX BUG #9)
        """
        print(f"{Color.BOLD + Color.CYAN}STEP 6 - NARRATIVE TURN OUTCOME{Color.RESET}")
        print()
        # DEBUG: show status_shifts received for Step 6 synthesis
        try:
            print(f"{Color.SYSTEM}DEBUG: Step6 status_shifts: {outcome_data.get('status_shifts')}{Color.RESET}")
        except Exception:
            pass
        # Visibility: warn loudly if Exchange detected a missing polarity and suppressed shifts
        try:
            scalc = outcome_data.get('shift_calc') or ''
            if isinstance(scalc, str) and 'missing_polarity' in scalc:
                print(f"{Color.WARNING}⚠️ Missing polarity detected in interpretation (Step 1/4). No status shift was applied this turn. Ensure both sides provide 'status_to_shift' and 'shift_polarity'.{Color.RESET}")
                print()
        except Exception:
            pass

        # Bridge Step 5 → Step 6: if Step 5 computed a shift but status_shifts is missing/empty,
        # synthesize a minimal shift entry so Step 6 narrative can stay mechanically grounded.
        out_for_step6 = outcome_data
        try:
            out_for_step6 = dict(outcome_data or {})
            shifts_existing = out_for_step6.get('status_shifts') or []

            pro_succ = self._safe_int(out_for_step6.get('proactor_successes', 0))
            rea_succ = self._safe_int(out_for_step6.get('reactor_successes', 0))
            margin = self._safe_int(out_for_step6.get('margin', pro_succ - rea_succ))
            # Some exchange code uses these keys
            shift_amt = out_for_step6.get('final_shift_amount', None)
            if shift_amt is None:
                shift_amt = out_for_step6.get('shift_value', None)
            if shift_amt is None:
                shift_amt = out_for_step6.get('applied_shift_amount', None)
            try:
                shift_amt = self._safe_int(shift_amt)
            except Exception:
                shift_amt = 0

            # Determine targeted status name
            status_name = (
                out_for_step6.get('status_shifted')
                or out_for_step6.get('status_to_shift')
                or (proactor_data.get('status_to_shift') if isinstance(proactor_data, dict) else None)
                or (reactor_data.get('status_to_shift') if isinstance(reactor_data, dict) else None)
            )
            status_name = str(status_name or 'Status')

            def _extract_numeric(v):
                if isinstance(v, (int, float)):
                    return int(v)
                if isinstance(v, dict):
                    vv = v.get('value')
                    if isinstance(vv, (int, float)):
                        return int(vv)
                return None

            if (not shifts_existing) and margin != 0 and shift_amt != 0:
                # Winner determines who gets shifted in most contested exchanges
                affected_actor = reactor_data.get('name') if margin > 0 else proactor_data.get('name')

                updated_val = None
                if margin > 0:
                    updated_val = _extract_numeric(out_for_step6.get('updated_reactor_status'))
                else:
                    updated_val = _extract_numeric(out_for_step6.get('updated_proactor_status'))

                original_val = None
                if updated_val is not None:
                    original_val = int(updated_val) - int(shift_amt)

                out_for_step6['status_shifts'] = [
                    {
                        'actor_name': affected_actor,
                        'status_name': status_name,
                        'shift_value': int(shift_amt),
                        'original_value': original_val,
                        'new_value': updated_val,
                    }
                ]
        except Exception:
            out_for_step6 = outcome_data
        # Always generate a formula-based deterministic outcome with N2N descriptors
        try:
            # Extract actual actor names from status_shifts if not in proactor/reactor data
            pro_name = proactor_data.get('name')
            rea_name = reactor_data.get('name')
            
            # If names are missing, try to extract from status_shifts
            if not pro_name or not rea_name:
                status_shifts = outcome_data.get('status_shifts', [])
                if status_shifts:
                    for shift in status_shifts:
                        actor_name = shift.get('actor') or shift.get('actor_name')
                        if actor_name:
                            # Determine which actor this is based on success comparison
                            pro_succ = outcome_data.get('proactor_successes', 0)
                            rea_succ = outcome_data.get('reactor_successes', 0)
                            if pro_succ > rea_succ:
                                # Reactor was affected
                                rea_name = actor_name
                            elif rea_succ > pro_succ:
                                # Proactor was affected
                                pro_name = actor_name
            
            # Ensure names are present in the data dicts
            pro_data_with_name = dict(proactor_data)
            rea_data_with_name = dict(reactor_data)
            pro_data_with_name['name'] = pro_name or ''
            rea_data_with_name['name'] = rea_name or ''
            
            formula_engine = UTASNarrativeFormula()
            formula_outcome = formula_engine.generate_turn_outcome_narrative(
                proactor_data=pro_data_with_name,
                reactor_data=rea_data_with_name,
                outcome_data=out_for_step6
            )
        except Exception:
            formula_outcome = None
        # Guard: if interpretation was missing polarity (no shift applied), do not append formula line
        try:
            scalc_guard = (outcome_data.get('shift_calc') or '')
            if isinstance(scalc_guard, str) and 'missing_polarity' in scalc_guard:
                formula_outcome = None
        except Exception:
            pass
        
        comprehensive_narrative = None
        
        # Check if narrator_agent exists
        if narrator_agent is None:
            print(f"⚠️ ERROR: narrator_agent is None - cannot generate Step 6 narrative")
            comprehensive_narrative = None
        else:
            try:
                # Build name-fixed dicts so narrator never sees name=None
                # (action_data may carry name=None when name key exists but was never populated)
                _pro_named = dict(proactor_data)
                _rea_named = dict(reactor_data)
                if not _pro_named.get('name'):
                    # Try status_shifts first, then ua_actor
                    for _s in (out_for_step6.get('status_shifts') or []):
                        _an = _s.get('actor_name') or _s.get('actor')
                        if _an:
                            _pro_succ = out_for_step6.get('proactor_successes', 0) or 0
                            _rea_succ = out_for_step6.get('reactor_successes', 0) or 0
                            if _rea_succ > _pro_succ:
                                _pro_named['name'] = _an
                                break
                    if not _pro_named.get('name') and ua_actor is not None and getattr(_pro_named.get('actor') or ua_actor, 'is_user_actor', False):
                        _pro_named['name'] = getattr(getattr(ua_actor, 'sheet', None), 'name', '')
                if not _rea_named.get('name'):
                    for _s in (out_for_step6.get('status_shifts') or []):
                        _an = _s.get('actor_name') or _s.get('actor')
                        if _an:
                            _pro_succ = out_for_step6.get('proactor_successes', 0) or 0
                            _rea_succ = out_for_step6.get('reactor_successes', 0) or 0
                            if _pro_succ > _rea_succ:
                                _rea_named['name'] = _an
                                break

                # FIX BUG #9: Pass scene_context to narrator
                # Pass remote encounter flags to prevent physical presence narratives during phone calls
                comprehensive_narrative = narrator_agent.generate_step6_turn_narrative(
                    proactor_data=_pro_named,
                    reactor_data=_rea_named,
                    outcome_data=out_for_step6,
                    scene_context=scene_context,
                    is_remote_encounter=is_remote_encounter,
                    remote_encounter_type=remote_encounter_type,
                    ua_actor=ua_actor
                )
            except Exception as e:
                print(f"⚠️ ERROR: Failed to generate Step 6 narrative in reporter: {e}")
                import traceback
                traceback.print_exc()
                comprehensive_narrative = None

        # If shifts exist, replace vague phrases with explicit penalty/boost phrasing
        try:
            pro_name = proactor_data.get('name') or ''
            rea_name = reactor_data.get('name') or ''
            # Fall back to shift actor names when proactor/reactor data has name=None
            if not pro_name or not rea_name:
                for _s in (out_for_step6.get('status_shifts') or []):
                    _an = _s.get('actor_name') or _s.get('actor') or ''
                    if _an:
                        _ps = out_for_step6.get('proactor_successes', 0) or 0
                        _rs = out_for_step6.get('reactor_successes', 0) or 0
                        if not pro_name and _rs > _ps:
                            pro_name = _an
                        elif not rea_name and _ps > _rs:
                            rea_name = _an
            phrase = self._build_status_effect_phrase(pro_name, rea_name, outcome_data)
            if phrase and isinstance(comprehensive_narrative, str):
                # Replace common vague markers
                replacements = [
                    'no status change',
                    'STATUS change applied',
                    'status change applied'
                ]
                for marker in replacements:
                    if marker.lower() in comprehensive_narrative.lower():
                        comprehensive_narrative = comprehensive_narrative.replace(marker, phrase, 1)
                        break
        except Exception:
            pass

        # Append authoritative mechanics addendum derived from Step 5 (never remove narrative).
        try:
            pro_name = proactor_data.get('name') or 'Proactor'
            rea_name = reactor_data.get('name') or 'Reactor'
            # Fall back to shift actor names when data has name=None
            for _s in (out_for_step6.get('status_shifts') or []):
                _an = _s.get('actor_name') or _s.get('actor') or ''
                if _an:
                    _ps = out_for_step6.get('proactor_successes', 0) or 0
                    _rs = out_for_step6.get('reactor_successes', 0) or 0
                    if pro_name == 'Proactor' and _rs > _ps:
                        pro_name = _an
                    elif rea_name == 'Reactor' and _ps > _rs:
                        rea_name = _an
            pro_succ = self._safe_int(out_for_step6.get('proactor_successes', 0))
            rea_succ = self._safe_int(out_for_step6.get('reactor_successes', 0))
            shifts = out_for_step6.get('status_shifts') or []

            addendum = ""
            if pro_succ == rea_succ or not shifts:
                addendum = "[MECHANICS] No status change was applied this turn."
            else:
                effect_phrase = self._build_status_effect_phrase(pro_name, rea_name, out_for_step6)
                if effect_phrase:
                    addendum = f"[MECHANICS] {effect_phrase}"

            if addendum:
                base = comprehensive_narrative if isinstance(comprehensive_narrative, str) else ""
                if isinstance(base, str) and base.strip():
                    if addendum.lower() not in base.lower():
                        comprehensive_narrative = base.rstrip() + "\n\n" + addendum
                else:
                    comprehensive_narrative = addendum
        except Exception:
            pass
        
        # Prefer comprehensive LLM narrative for immersion, fallback to formula for accuracy
        # LLM narrative includes the N2N formula at the end, so it's complete
        if comprehensive_narrative:
            final_line = comprehensive_narrative
        elif formula_outcome:
            final_line = formula_outcome
        else:
            final_line = "[No narrative available]"
        try:
            _actors_for_scrub = []
            if proactor_data.get('actor') is not None:
                _actors_for_scrub.append(proactor_data.get('actor'))
            if reactor_data.get('actor') is not None:
                _actors_for_scrub.append(reactor_data.get('actor'))
            final_line = self._scrub_unknown_names(final_line, _actors_for_scrub)
        except Exception:
            pass

        try:
            final_line = self._sanitize_step6_no_invented_loot(final_line)
        except Exception:
            pass
        print(f"{Color.NARRATIVE}{final_line}{Color.RESET}")
        print()
        # Route step 6 narrative outcome to the narrative display
        try:
            from pygame_narrative_display import send_narrator
            send_narrator(final_line)
        except Exception:
            pass

        return final_line

    def report_scene_resolution(self, resolution_data: Dict[str, Any]):
        """Reports scene resolution and transitions."""
        print(f"{Color.BOLD + Color.CYAN}SCENE RESOLUTION{Color.RESET}")
        print()
        
        resolution_type = resolution_data.get('resolution_type', 'unknown')
        final_narrative = resolution_data.get('final_narrative', '[]')
        
        print(f"Resolution Type: {resolution_type}")
        print(f"Final Narrative: {final_narrative}")
        
        next_scene_trigger = resolution_data.get('next_scene_trigger')
        if next_scene_trigger:
            print(f"Next Scene Trigger: {next_scene_trigger}")
        
        print()

    def report_full_turn(self, turn_data: Dict[str, Any], narrator_agent: Optional[Any] = None) -> str:
        """Consolidated end-of-turn summary, aligned with Output.md structure.

        Expected turn_data keys:
        - turn_queue_data (optional): {'turn_queue': [...]} used to label Proactor/Reactor
        - proactor_data: dict used in Step 1/2
        - reactor_data: dict used in Step 3/4
        - outcome_data: dict used in Step 5/6 (should include successes and status_shifts)
        - final_narrative (optional): precomputed Step 6 narrative

        Returns the final narrative string used.
        """
        pro = turn_data.get('proactor_data', {})
        rea = turn_data.get('reactor_data', {})
        out = turn_data.get('outcome_data', {})
        final_narr = turn_data.get('final_narrative')

        # Derive names safely
        pro_name = pro.get('name', 'Proactor')
        rea_name = rea.get('name', 'Reactor')

        # TURN SUMMARY DISABLED - Return early to skip all printing
        # Data is still processed by the method but not displayed
        return ""  # Skip all turn summary printing

        # Turn Queue Snapshot (supports 3+ actors) and roles this turn
        tq_data = (turn_data.get('turn_queue_data') or {})
        tq = tq_data.get('turn_queue') or []
        use_primary_reactor_label = bool(tq_data.get('use_primary_reactor_label', False) or turn_data.get('use_primary_reactor_label', False))
        # if tq:
        #     print(f"{Color.INFO}Turn Queue Snapshot:{Color.RESET}")
        #     try:
        #         for i, entry in enumerate(tq[:8], start=1):
        #             actor_obj = entry.get('actor')
        #             name = getattr(getattr(actor_obj, 'sheet', None), 'name', None) or entry.get('name') or f"Actor {i}"
        #             init_score = entry.get('initiative_score')
        #             # Tag actual participants for this turn regardless of position
        #             role_tag = ""
        #             if name == pro_name:
        #                 role_tag = " (PROACTOR)"
        #             elif name == rea_name:
        #                 role_tag = " (PRIMARY REACTOR)" if use_primary_reactor_label else " (REACTOR)"
        #             if init_score is not None:
        #                 print(f"  {i}. {name}{role_tag} (Init: {init_score})")
        #             else:
        #                 print(f"  {i}. {name}{role_tag}")
        #         if len(tq) > 8:
        #             print(f"  ... ({len(tq) - 8} more actors)")
        #     except Exception:
        #         # Fallback to basic roles only
        #         print(f"  1. {pro_name} (PROACTOR)")
        #         print(f"  2. {rea_name} ({'PRIMARY REACTOR' if use_primary_reactor_label else 'REACTOR'})")
        # else:
        #     reactor_role_label = "Primary Reactor" if use_primary_reactor_label else "Reactor"
        #     print(f"{Color.INFO}Turn Roles:{Color.RESET} {pro_name} (PROACTOR), {rea_name} ({reactor_role_label.upper()})")

        # # Always clarify roles this turn explicitly
        # print(f"{Color.SYSTEM}Roles this turn:{Color.RESET} Proactor: {pro_name}  •  {'Primary Reactor' if use_primary_reactor_label else 'Reactor'}: {rea_name}")

        # # Symmetric UTAS mandatory field checks (visibility only; no defaults applied)
        # def _warn_missing_utas(label: str, uf: Dict[str, Any], required: List[str]) -> None:
        #     try:
        #         missing = [k for k in required if uf.get(k) in (None, "", [])]
        #     except Exception:
        #         missing = required
        #     if missing:
        #         print(f"{Color.WARNING}⚠️ Missing {label} UTAS fields: {', '.join(missing)}. Interpretation must provide these explicitly; no defaults will be applied.{Color.RESET}")

        # # Proactor required factors (Step 1/2)
        # p_uf = (pro.get('utas_factors') or {}) if isinstance(pro.get('utas_factors'), dict) else {}
        # p_required = [
        #     'exchange_type', 'status_to_shift', 's_trait_to_use', 's_trait_value',
        #     'skill', 'super', 'supplement', 'stress_level', 'shift_type', 'shift_polarity'
        # ]
        # _warn_missing_utas('PROACTOR', p_uf, p_required)

        # # Reactor required factors (Step 4)
        # r_uf = (rea.get('utas_factors') or {}) if isinstance(rea.get('utas_factors'), dict) else {}
        # r_required = [
        #     'reactor_reaction_description', 'reactor_reaction_skill', 'reactor_reaction_s_trait',
        #     'reactor_reaction_super', 'reactor_reaction_supplement', 'reactor_primary_defensive_status_type',
        #     'status_to_shift', 'shift_polarity', 'has_secondary_effect', 'stress_level'
        # ]
        # _warn_missing_utas('REACTOR', r_uf, r_required)

        # # Continuity Check (from Step 1)
        # cont = pro.get('continuity_check') or {}
        # if cont:
        #     print(f"\n{Color.SYSTEM}Continuity Check:{Color.RESET}")
        #     print(f"  Judgment: {cont.get('judgment', 'N/A')}")
        #     just = cont.get('justification') or cont.get('narrative')
        #     if just:
        #         print(f"  Justification: {just}")

        # # Action Interpretations
        # print(f"\n{Color.SYSTEM}Action Interpretations:{Color.RESET}")
        # print(f"  {pro_name}: {pro.get('narrative_description', 'N/A')}")
        # print(f"  {rea_name}: {rea.get('narrative_description', 'N/A')}")

        # # Symmetric UTAS Factors display (Proactor and Reactor), independent of UA/NUA origin
        # pro_uf = (pro.get('utas_factors') or {}) if isinstance(pro.get('utas_factors'), dict) else {}
        # rea_uf = (rea.get('utas_factors') or {}) if isinstance(rea.get('utas_factors'), dict) else {}

        # Proactor UTAS (standardized labels)
        print(f"\n{Color.SYSTEM}UTAS Factors (Proactor):{Color.RESET}")
        try:
            def _print_named_val(prefix: str, obj):
                if isinstance(obj, dict):
                    name = obj.get('name', 'None')
                    val = obj.get('value', 0)
                    print(f"  {prefix}: {name} ({val})")
                else:
                    print(f"  {prefix}: {obj}")

            print(f"  Exchange Type: {pro_uf.get('exchange_type', 'N/A')}")
            print(f"  Target Status: {pro_uf.get('status_to_shift', 'N/A')}")
            print(f"  S-Trait: {pro_uf.get('s_trait_to_use', 'N/A')} ({pro_uf.get('s_trait_value', 'N/A')})")
            _print_named_val('Skill', pro_uf.get('skill', {"name": "None", "value": 0}))
            _print_named_val('Super', pro_uf.get('super', {"name": "None", "value": 0}))
            _print_named_val('Supplement', pro_uf.get('supplement', {"name": "None", "value": 0}))
            print(f"  Stress Level: {pro_uf.get('stress_level', 'N/A')}")
            print(f"  Shift Type: {pro_uf.get('shift_type', 'N/A')}")
            print(f"  Shift Polarity: {pro_uf.get('shift_polarity', 'N/A')}")
        except Exception:
            print("  [Proactor UTAS unavailable]")

        # Reactor UTAS (standardized labels mirroring proactor)
        print(f"\n{Color.SYSTEM}UTAS Factors (Reactor):{Color.RESET}")
        try:
            # Map reactor fields to symmetric labels
            print(f"  Reaction: {rea_uf.get('reactor_reaction_description', 'N/A')}")
            # S-trait is typically a string for reactor
            print(f"  S-Trait: {rea_uf.get('reactor_reaction_s_trait', 'N/A')}")
            _print_named_val('Skill', rea_uf.get('reactor_reaction_skill', {"name": "None", "value": 0}))
            _print_named_val('Super', rea_uf.get('reactor_reaction_super', {"name": "None", "value": 0}))
            _print_named_val('Supplement', rea_uf.get('reactor_reaction_supplement', {"name": "None", "value": 0}))
            print(f"  Defensive Status: {rea_uf.get('reactor_primary_defensive_status_type', 'N/A')}")
            print(f"  Target Status: {rea_uf.get('status_to_shift', 'N/A')}")
            print(f"  Shift Polarity: {rea_uf.get('shift_polarity', 'N/A')}")
            print(f"  Stress Level: {rea_uf.get('stress_level', 'N/A')}")
        except Exception:
            print("  [Reactor UTAS unavailable]")

        # Proactor Self-Effects (Proactor-only; Reactor uses Secondary Effects)
        try:
            se_list = pro_uf.get('self_effects') or []
            if isinstance(se_list, list) and se_list:
                print(f"\n{Color.SYSTEM}Self-Effects (Proactor):{Color.RESET}")
                for i, eff in enumerate(se_list, start=1):
                    if isinstance(eff, dict):
                        cond = eff.get('condition') or eff.get('trigger_condition') or 'N/A'
                        tgt = eff.get('target_status') or eff.get('status_to_shift') or eff.get('status_shifted') or 'N/A'
                        pol = eff.get('polarity') or eff.get('shift_polarity') or 'N/A'
                        stt = eff.get('shift_type') or 'N/A'
                        sev = eff.get('severity') or eff.get('shift_magnitude') or 'N/A'
                        print(f"  {i}. [{cond}] {tgt} {pol}, {stt}, severity/magnitude: {sev}")
        except Exception:
            pass

        # Reactor Secondary Effects (Reactor-only; Proactor uses Self-Effects)
        try:
            if rea_uf:
                hse = rea_uf.get('has_secondary_effect')
                if hse is not None:
                    print(f"\n{Color.SYSTEM}Secondary Effect (Reactor):{Color.RESET}")
                    print(f"  Present: {hse}")
                    if str(hse).upper() in ("TRUE", "YES", "1"):
                        print(f"  Target: {rea_uf.get('secondary_effect_target', 'N/A')}")
                        print(f"  Target Status: {rea_uf.get('secondary_effect_target_status_type', 'N/A')}")
                        print(f"  Shift Polarity (+1/-1): {rea_uf.get('secondary_effect_shift_polarity_numeric', 'N/A')}")
                        print(f"  Shift Type Multiplier (1.0/0.5): {rea_uf.get('secondary_effect_shift_type_multiplier', 'N/A')}")
        except Exception:
            pass

        # Interpretation Justifications (Proactor)
        try:
            pj = []
            if pro_uf.get('s_trait_justification'): pj.append(("S-Trait", pro_uf.get('s_trait_justification')))
            if pro_uf.get('skill_justification'): pj.append(("Skill", pro_uf.get('skill_justification')))
            if pro_uf.get('stress_justification'): pj.append(("Stress", pro_uf.get('stress_justification')))
            if pro_uf.get('shift_type_justification'): pj.append(("Shift Type", pro_uf.get('shift_type_justification')))
            if pro_uf.get('shift_polarity_justification'): pj.append(("Shift Polarity", pro_uf.get('shift_polarity_justification')))
            if pro_uf.get('self_effects_justification'): pj.append(("Self-Effects", pro_uf.get('self_effects_justification')))
            if pj:
                print(f"\n{Color.SYSTEM}Interpretation Justifications (Proactor):{Color.RESET}")
                for label, text in pj:
                    print(f"  {label}: {text}")
        except Exception:
            pass

        # Interpretation Justifications (Reactor)
        try:
            rj = []
            if rea_uf.get('secondary_effect_justification'): rj.append(("Secondary Effect", rea_uf.get('secondary_effect_justification')))
            if rea_uf.get('secondary_effect_target_justification'): rj.append(("SE Target", rea_uf.get('secondary_effect_target_justification')))
            if rea_uf.get('secondary_effect_target_status_justification'): rj.append(("SE Target Status", rea_uf.get('secondary_effect_target_status_justification')))
            if rea_uf.get('secondary_effect_shift_polarity_justification'): rj.append(("SE Shift Polarity", rea_uf.get('secondary_effect_shift_polarity_justification')))
            if rea_uf.get('secondary_effect_shift_type_justification'): rj.append(("SE Shift Type", rea_uf.get('secondary_effect_shift_type_justification')))
            if rj:
                print(f"\n{Color.SYSTEM}Interpretation Justifications (Reactor):{Color.RESET}")
                for label, text in rj:
                    print(f"  {label}: {text}")
        except Exception:
            pass

        # Success Overview (Step 2/4 results)
        pro_s = int(out.get('proactor_successes', out.get('proactor_success', 0)) or 0)
        rea_s = int(out.get('reactor_successes', out.get('reactor_success', 0)) or 0)
        print(f"\n{Color.SYSTEM}Success Overview:{Color.RESET}")
        print(f"  {pro_name}: {pro_s} successes")
        print(f"  {rea_name}: {rea_s} successes")
        # Optional: show calculation strings if available (symmetrically)
        try:
            calc_p = out.get('proactor_calculation')
            calc_r = out.get('reactor_calculation')
            if calc_p or calc_r:
                print(f"  {pro_name} Calc: {calc_p or 'N/A'}")
                print(f"  {rea_name} Calc: {calc_r or 'N/A'}")
        except Exception:
            pass

        # Abort visibility: if Conductor halted the exchange, report and exit early
        try:
            if out.get('exchange_aborted'):
                print(f"\n{Color.WARNING}⚠️ Exchange Aborted{Color.RESET}")
                reason = out.get('abort_reason') or 'Missing mandatory UTAS fields.'
                print(f"  Reason: {reason}")
                attempts = out.get('re_prompt_attempts') or {}
                if attempts:
                    try:
                        print(f"  Re-prompt Attempts → Proactor: {attempts.get('proactor', 0)}, Reactor: {attempts.get('reactor', 0)}")
                    except Exception:
                        pass
                print()
                # Do not attempt status shifts or Step 6; return empty narrative
                return ""
        except Exception:
            pass

        # Status Shifts (Step 5 concise recap)
        shifts = out.get('status_shifts') or []
        if shifts:
            print(f"\n{Color.SYSTEM}Status Shifts:{Color.RESET}")
            for s in shifts:
                # Support both legacy and new schemas
                actor_name = s.get('actor_name') or s.get('actor') or 'N/A'
                status_name = s.get('status_name') or s.get('status_type') or s.get('status') or 'Status'
                shift_value = s.get('shift_value') if s.get('shift_value') is not None else s.get('delta', 0)
                original_value = s.get('original_value') if s.get('original_value') is not None else s.get('original')
                new_value = s.get('new_value') if s.get('new_value') is not None else s.get('updated')
                original_desc = s.get('original_descriptor')
                new_desc = s.get('new_descriptor')
                # Derive descriptors if missing and values available
                if (original_desc is None or new_desc is None) and (original_value is not None and new_value is not None):
                    try:
                        original_desc = original_desc or get_narrative_descriptor(int(original_value))
                        new_desc = new_desc or get_narrative_descriptor(int(new_value))
                    except Exception:
                        original_desc = original_desc or 'N/A'
                        new_desc = new_desc or 'N/A'
                if original_value is not None and new_value is not None:
                    print(f"  {actor_name}: {status_name} {int(shift_value):+d} → {int(original_value)} ({original_desc}) → {int(new_value)} ({new_desc})")
                else:
                    print(f"  {actor_name}: {status_name} {int(shift_value):+d} ({original_desc or 'N/A'} → {new_desc or 'N/A'})")

        # Final Narrative (Step 6)
        generated_here = False
        if not final_narr and narrator_agent is not None:
            try:
                final_narr = narrator_agent.generate_step6_turn_narrative(pro, rea, out)
                generated_here = True
            except Exception:
                final_narr = None
        # To avoid duplicates, only print if we generated it here; otherwise assume it was already printed by report_step6
        if generated_here:
            if final_narr:
                print(f"\n{Color.NARRATIVE}{final_narr}{Color.RESET}")
            else:
                print(f"\n{Color.WARNING}[No final narrative available]{Color.RESET}")

        print()
        return final_narr or ""

    def display_simulation_overview(self):
        """Display a comprehensive overview of the simulation."""
        overview = self.get_simulation_overview()
        
        print(f"\n{Color.SYSTEM}{'='*60}")
        print(f"  SIMULATION OVERVIEW")
        print(f"{'='*60}{Color.RESET}")
        
        # Actor summary
        actors = overview['actors']
        print(f"{Color.INFO}Actors:{Color.RESET}")
        print(f"  Total: {actors['total_actors']}")
        print(f"  Active: {actors['active_actors']}")
        print(f"  Current Turn: {actors['current_turn']}")
        
        # Relationship summary
        relationships = overview['relationships']
        if 'error' not in relationships:
            print(f"\n{Color.INFO}Relationships:{Color.RESET}")
            print(f"  Total: {relationships['total_relationships']}")
            print(f"  Average Sympathy: {relationships['average_sympathy']:.2f}")
        
        # Reporter configuration
        config = overview['reporter_config']
        print(f"\n{Color.INFO}Reporter Settings:{Color.RESET}")
        print(f"  Verbosity: {config['verbosity_level']}")
        print(f"  Detailed Display Limit: {config['max_actors_detailed']} actors")
