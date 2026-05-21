"""
Witness Reaction System for UTAS Simulation

Ensures NPCs react realistically to violence, murder, and other dramatic events.
Prevents fake signals where witnesses ignore shocking events.
"""

from typing import List, Dict, Any, Tuple
from actor_sheet import StatusType
from color_utils import Color
import random

try:
    from stranger_description_system import known_actors_tracker, get_nua_definite_description
except Exception:
    known_actors_tracker = None
    get_nua_definite_description = None


class WitnessReactionSystem:
    """
    Handles realistic NPC reactions to witnessed events.
    
    Event Types:
    - Violence (attack, injury)
    - Murder (killing)
    - Theft (stealing)
    - Threats (intimidation)
    - Supernatural (impossible events)
    """
    
    def __init__(self):
        self.witnessed_events = []
    
    def process_witness_reactions(
        self,
        event_type: str,
        perpetrator,
        victim,
        witnesses: List,
        severity: int,
        scene_description: str
    ) -> List[Dict[str, Any]]:
        """
        Process reactions from all witnesses to an event.
        
        Args:
            event_type: Type of event (violence, murder, theft, threat)
            perpetrator: Actor who performed the action
            victim: Actor who was targeted
            witnesses: List of NPCs who can see the event
            severity: How severe the event is (1-5)
            scene_description: Current scene context
            
        Returns:
            List of reaction dictionaries for each witness
        """
        reactions = []
        
        for witness in witnesses:
            # Skip if witness is the perpetrator or victim
            if witness == perpetrator or witness == victim:
                continue
            
            reaction = self._determine_witness_reaction(
                event_type, perpetrator, victim, witness, severity, scene_description
            )
            
            if reaction:
                reactions.append(reaction)
                self._apply_reaction_effects(witness, reaction)
        
        return reactions
    
    def _determine_witness_reaction(
        self,
        event_type: str,
        perpetrator,
        victim,
        witness,
        severity: int,
        scene_description: str
    ) -> Dict[str, Any]:
        """Determine how a specific witness reacts to an event."""
        
        # Get witness's relationship with perpetrator and victim
        perp_sympathy = witness.sheet.get_sympathy(perpetrator.sheet.name)
        victim_sympathy = witness.sheet.get_sympathy(victim.sheet.name) if victim else 0
        
        # Get witness's personality traits
        personality = getattr(witness.sheet, 'personality_traits', {})
        is_brave = self._check_trait(personality, ['brave', 'courageous', 'fearless'])
        is_timid = self._check_trait(personality, ['timid', 'cowardly', 'fearful'])
        is_aggressive = self._check_trait(personality, ['aggressive', 'violent', 'hostile'])
        
        # Determine base reaction type
        reaction_type = self._get_reaction_type(
            event_type, severity, perp_sympathy, victim_sympathy,
            is_brave, is_timid, is_aggressive
        )
        
        # Build reaction dictionary
        witness_display = self._get_display_name_for_player(witness)
        reaction = {
            'witness': witness.sheet.name,
            'witness_display': witness_display,
            'event_type': event_type,
            'reaction_type': reaction_type,
            'severity': severity,
            'narrative': self._generate_reaction_narrative(
                witness, reaction_type, event_type, perpetrator, victim
            ),
            'sympathy_shifts': self._calculate_sympathy_shifts(
                reaction_type, perp_sympathy, victim_sympathy
            ),
            'status_effects': self._calculate_status_effects(
                reaction_type, severity
            ),
            'behavioral_change': self._determine_behavioral_change(
                reaction_type, event_type
            )
        }
        
        return reaction

    def _get_display_name_for_player(self, actor) -> str:
        """Return a stranger-safe name for UA-facing text without changing internal identity."""
        try:
            name = getattr(getattr(actor, 'sheet', None), 'name', None)
            if not name:
                return str(actor)

            if known_actors_tracker is None or get_nua_definite_description is None:
                return str(name)

            try:
                if known_actors_tracker.is_name_known(str(name)):
                    return str(name)
            except Exception:
                return str(name)

            ua_actor = None
            try:
                # Best-effort access to UA for definite descriptions.
                if 'runtime_state' in globals() and getattr(runtime_state, 'current_actor', None) is not None:
                    ua_actor = getattr(runtime_state, 'current_actor')
            except Exception:
                ua_actor = None

            try:
                replacement = get_nua_definite_description(actor, ua_actor=ua_actor)
                if replacement:
                    return str(replacement)
            except Exception:
                pass

            return str(name)
        except Exception:
            return "someone"
    
    def _get_reaction_type(
        self,
        event_type: str,
        severity: int,
        perp_sympathy: int,
        victim_sympathy: int,
        is_brave: bool,
        is_timid: bool,
        is_aggressive: bool
    ) -> str:
        """Determine the type of reaction based on context."""
        
        # Murder always triggers strong reactions
        if event_type == "murder":
            if perp_sympathy > 3:  # Close friend
                return "shocked_denial"
            elif victim_sympathy > 3:  # Close to victim
                return "enraged_intervention"
            elif is_timid or severity >= 4:
                return "flee_terror"
            elif is_brave and victim_sympathy > 0:
                return "heroic_intervention"
            else:
                return "scream_flee"
        
        # Violence reactions
        elif event_type == "violence":
            if severity >= 4:  # Severe violence
                if is_brave and victim_sympathy > 2:
                    return "intervene"
                elif is_aggressive and perp_sympathy < -2:
                    return "counter_attack"
                else:
                    return "flee_panic"
            elif severity >= 2:  # Moderate violence
                if victim_sympathy > 3:
                    return "call_for_help"
                elif is_timid:
                    return "flee_quietly"
                else:
                    return "shocked_watching"
            else:  # Minor violence
                return "concerned_watching"
        
        # Theft reactions
        elif event_type == "theft":
            if victim_sympathy > 2:
                return "alert_victim"
            elif perp_sympathy < -1:
                return "call_authorities"
            else:
                return "pretend_not_notice"
        
        # Threat reactions
        elif event_type == "threat":
            if severity >= 3:
                if is_brave:
                    return "stand_ground"
                else:
                    return "flee_quietly"
            else:
                return "nervous_watching"
        
        # Default: shocked watching
        return "shocked_watching"
    
    def _generate_reaction_narrative(
        self,
        witness,
        reaction_type: str,
        event_type: str,
        perpetrator,
        victim
    ) -> str:
        """Generate narrative description of witness reaction."""

        witness_name = self._get_display_name_for_player(witness)
        perp_name = self._get_display_name_for_player(perpetrator)
        victim_name = self._get_display_name_for_player(victim) if victim else "the target"
        
        narratives = {
            "scream_flee": f"{witness_name} screams in terror and flees from the scene, desperate to escape the violence...",
            "flee_terror": f"{witness_name}'s face goes pale with horror as they turn and run, stumbling in their panic...",
            "flee_panic": f"{witness_name} backs away in fear, then breaks into a run, seeking safety...",
            "flee_quietly": f"{witness_name} quietly slips away, not wanting to draw attention...",
            "shocked_watching": f"{witness_name} freezes in shock, unable to look away from the unfolding scene...",
            "concerned_watching": f"{witness_name} watches with growing concern, unsure whether to intervene...",
            "nervous_watching": f"{witness_name} shifts nervously, keeping a wary eye on the situation...",
            "shocked_denial": f"{witness_name} stares in disbelief, unable to process what {perp_name} just did...",
            "heroic_intervention": f"{witness_name} rushes forward to stop {perp_name}, shouting for them to stand down...",
            "enraged_intervention": f"{witness_name} roars in fury and charges at {perp_name}, seeking vengeance for {victim_name}...",
            "intervene": f"{witness_name} steps between {perp_name} and {victim_name}, trying to stop the violence...",
            "counter_attack": f"{witness_name} sees an opportunity and attacks {perp_name} while they're distracted...",
            "call_for_help": f"{witness_name} shouts for help, trying to draw attention to the situation...",
            "alert_victim": f"{witness_name} urgently warns {victim_name} about what's happening...",
            "call_authorities": f"{witness_name} looks around for security or police, ready to report the crime...",
            "pretend_not_notice": f"{witness_name} deliberately looks away, pretending not to see anything...",
            "stand_ground": f"{witness_name} stands firm, refusing to be intimidated by {perp_name}..."
        }
        
        return narratives.get(reaction_type, f"{witness_name} reacts to the situation...")
    
    def _calculate_sympathy_shifts(
        self,
        reaction_type: str,
        perp_sympathy: int,
        victim_sympathy: int
    ) -> Dict[str, int]:
        """Calculate sympathy changes based on reaction."""
        
        shifts = {
            'perpetrator': 0,
            'victim': 0
        }
        
        # Reactions that drastically reduce sympathy with perpetrator
        if reaction_type in ["scream_flee", "flee_terror", "flee_panic", "enraged_intervention", "counter_attack"]:
            shifts['perpetrator'] = -3
            shifts['victim'] = 2
        
        # Reactions that moderately reduce sympathy
        elif reaction_type in ["shocked_denial", "heroic_intervention", "intervene", "call_for_help"]:
            shifts['perpetrator'] = -2
            shifts['victim'] = 1
        
        # Reactions that slightly reduce sympathy
        elif reaction_type in ["shocked_watching", "concerned_watching", "alert_victim", "call_authorities"]:
            shifts['perpetrator'] = -1
            shifts['victim'] = 1
        
        # Neutral/self-preservation reactions
        elif reaction_type in ["flee_quietly", "pretend_not_notice"]:
            shifts['perpetrator'] = 0
            shifts['victim'] = 0
        
        return shifts
    
    def _calculate_status_effects(
        self,
        reaction_type: str,
        severity: int
    ) -> Dict[str, int]:
        """Calculate status effects on witness from witnessing event."""
        
        effects = {
            'spirit': 0,
            'stamina': 0
        }
        
        # Traumatic reactions cause Spirit damage
        if reaction_type in ["scream_flee", "flee_terror", "shocked_denial"]:
            effects['spirit'] = -min(severity, 3)  # Cap at -3
        
        # Panic reactions cause moderate Spirit damage
        elif reaction_type in ["flee_panic", "shocked_watching"]:
            effects['spirit'] = -min(severity - 1, 2)  # Cap at -2
        
        # Active reactions cause Stamina cost
        if reaction_type in ["heroic_intervention", "enraged_intervention", "intervene", "counter_attack"]:
            effects['stamina'] = -1
        
        return effects
    
    def _determine_behavioral_change(
        self,
        reaction_type: str,
        event_type: str
    ) -> str:
        """Determine how witness's behavior should change going forward."""
        
        # Witnesses who flee should leave the scene
        if reaction_type in ["scream_flee", "flee_terror", "flee_panic", "flee_quietly"]:
            return "leave_scene"
        
        # Witnesses who intervene should join combat
        elif reaction_type in ["heroic_intervention", "enraged_intervention", "intervene", "counter_attack"]:
            return "join_combat_against_perpetrator"
        
        # Witnesses who call for help should alert others
        elif reaction_type in ["call_for_help", "call_authorities"]:
            return "alert_others"
        
        # Witnesses who are shocked should be distracted
        elif reaction_type in ["shocked_watching", "shocked_denial", "concerned_watching"]:
            return "distracted_watching"
        
        # Default: cautious behavior
        return "cautious"
    
    def _apply_reaction_effects(
        self,
        witness,
        reaction: Dict[str, Any]
    ):
        """Apply the effects of a reaction to the witness."""
        
        # Apply status effects
        status_effects = reaction['status_effects']
        if status_effects['spirit'] != 0:
            spirit_status = witness.sheet.statuses[StatusType.SPIRIT]
            spirit_status.modify(status_effects['spirit'])
        
        if status_effects['stamina'] != 0:
            stamina_status = witness.sheet.statuses[StatusType.STAMINA]
            stamina_status.modify(status_effects['stamina'])
        
        # Sympathy shifts will be applied by the caller who has access to perpetrator/victim
    
    def _check_trait(self, personality: Dict, trait_keywords: List[str]) -> bool:
        """Check if personality contains any of the given trait keywords."""
        if not personality:
            return False
        
        personality_str = str(personality).lower()
        return any(keyword in personality_str for keyword in trait_keywords)
    
    def display_witness_reactions(self, reactions: List[Dict[str, Any]]):
        """Display all witness reactions in a formatted way."""
        
        if not reactions:
            return
        
        print(f"\n{Color.WARNING}{'='*80}{Color.RESET}")
        print(f"{Color.WARNING}👁️  WITNESS REACTIONS{Color.RESET}")
        print(f"{Color.WARNING}{'='*80}{Color.RESET}")
        
        for reaction in reactions:
            witness_disp = reaction.get('witness_display') or reaction.get('witness')
            print(f"\n{Color.INFO}Witness: {witness_disp}{Color.RESET}")
            print(f"{Color.NARRATIVE}{reaction['narrative']}{Color.RESET}")
            
            # Show sympathy shifts
            if reaction['sympathy_shifts']['perpetrator'] != 0:
                shift = reaction['sympathy_shifts']['perpetrator']
                print(f"{Color.WARNING}   Sympathy with perpetrator: {shift:+d}{Color.RESET}")
            
            if reaction['sympathy_shifts']['victim'] != 0:
                shift = reaction['sympathy_shifts']['victim']
                print(f"{Color.SUCCESS}   Sympathy with victim: {shift:+d}{Color.RESET}")
            
            # Show status effects
            if reaction['status_effects']['spirit'] != 0:
                print(f"{Color.WARNING}   Spirit: {reaction['status_effects']['spirit']:+d} (trauma/shock){Color.RESET}")
            
            if reaction['status_effects']['stamina'] != 0:
                print(f"{Color.WARNING}   Stamina: {reaction['status_effects']['stamina']:+d} (physical exertion){Color.RESET}")
            
            # Show behavioral change
            behavior = reaction['behavioral_change']
            if behavior == "leave_scene":
                print(f"{Color.WARNING}   → {witness_disp} flees the scene!{Color.RESET}")
            elif behavior == "join_combat_against_perpetrator":
                print(f"{Color.ERROR}   → {witness_disp} joins the fight!{Color.RESET}")
            elif behavior == "alert_others":
                print(f"{Color.INFO}   → {witness_disp} calls for help!{Color.RESET}")
        
        print(f"{Color.WARNING}{'='*80}{Color.RESET}\n")


# Global instance
witness_system = WitnessReactionSystem()
