"""
Identity Manager for Dynamic NUA Profile Updates

Handles the discovery and updating of NUA identities as information is revealed
through narrative interactions. Integrates with the narrative context system
to track identity revelations and update actor profiles accordingly.
"""

from typing import Dict, List, Any, Optional
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from actors import NonUserActor
from llm_agents.narrative_context_system import NarrativeContextManager, NarrativeEventType, NarrativeImportance

class IdentityManager:
    """Manages dynamic identity updates for NPCs as information is discovered"""
    
    def __init__(self, narrative_context_manager: NarrativeContextManager):
        self.narrative_context_manager = narrative_context_manager
        self.identity_mappings: Dict[str, str] = {}  # old_name -> new_name
        self.discovered_actors: Dict[str, NonUserActor] = {}  # Track actors by current name
    
    def register_actor(self, actor: NonUserActor):
        """Register an actor for identity tracking"""
        self.discovered_actors[actor.get_display_name()] = actor
    
    def process_narrative_for_identity_discovery(self, narrative_text: str, 
                                               actors_involved: List[str],
                                               actor_manager=None) -> Dict[str, Dict[str, str]]:
        """
        Process narrative text to detect identity revelations and update actors accordingly
        
        Returns:
            Dictionary of discovered identities {old_name: {new_info}}
        """
        # Use narrative context manager to detect identity revelations
        identity_discoveries = self.narrative_context_manager.detect_identity_revelations(
            narrative_text, actors_involved
        )
        
        if identity_discoveries and actor_manager:
            self._update_actors_from_discoveries(identity_discoveries, actor_manager)
        
        return identity_discoveries
    
    def _update_actors_from_discoveries(self, identity_discoveries: Dict[str, Dict[str, str]], 
                                      actor_manager):
        """Update actor profiles based on discovered identities"""
        for old_name, new_info in identity_discoveries.items():
            # Find the actor in the manager
            actor = None
            if hasattr(actor_manager, 'get_actor_by_name'):
                actor = actor_manager.get_actor_by_name(old_name)
            elif hasattr(actor_manager, 'actors'):
                # Try to find in actors dict/list
                for actor_id, potential_actor in actor_manager.actors.items():
                    if hasattr(potential_actor, 'sheet') and potential_actor.sheet.name == old_name:
                        actor = potential_actor
                        break
            
            if actor and isinstance(actor, NonUserActor):
                # Update the actor's identity
                new_name = new_info.get('name')
                new_occupation = new_info.get('occupation')
                
                actor.update_identity(
                    new_name=new_name,
                    new_occupation=new_occupation,
                    new_details=new_info,
                    mark_discovered=True
                )
                
                # Update our tracking
                if new_name and new_name != old_name:
                    self.identity_mappings[old_name] = new_name
                    self.discovered_actors[new_name] = actor
                    if old_name in self.discovered_actors:
                        del self.discovered_actors[old_name]
                
                print(f"🎭 Identity Updated: {old_name} → {new_name or 'details updated'}")
    
    def get_current_name(self, original_name: str) -> str:
        """Get the current name for an actor, accounting for identity changes"""
        return self.identity_mappings.get(original_name, original_name)
    
    def is_identity_known(self, actor_name: str) -> bool:
        """Check if an actor's identity has been discovered"""
        current_name = self.get_current_name(actor_name)
        actor = self.discovered_actors.get(current_name)
        if actor and isinstance(actor, NonUserActor):
            return actor.is_identity_known()
        return False
    
    def get_display_name_for_actor(self, actor_name: str) -> str:
        """Get the appropriate display name for an actor based on discovery status"""
        current_name = self.get_current_name(actor_name)
        actor = self.discovered_actors.get(current_name)
        if actor and isinstance(actor, NonUserActor):
            return actor.get_display_name()
        return current_name

def integrate_identity_discovery_with_narrative(narrator_agent, identity_manager: IdentityManager):
    """
    Enhance narrator agent to automatically detect and process identity discoveries
    """
    original_generate_outcome = getattr(narrator_agent, 'generate_outcome_narrative', None)
    
    if original_generate_outcome:
        def enhanced_generate_outcome(outcome_data, rule_of_3s_context=None, 
                                    time_context=None, framing_guidance=None, 
                                    actor_manager=None):
            # Generate the narrative normally
            narrative = original_generate_outcome(
                outcome_data, rule_of_3s_context, time_context, framing_guidance, actor_manager
            )
            
            # Extract actors involved from outcome data
            actors_involved = []
            if 'proactor' in outcome_data:
                actors_involved.append(outcome_data['proactor'].get('name', 'Unknown'))
            if 'reactor' in outcome_data:
                actors_involved.append(outcome_data['reactor'].get('name', 'Unknown'))
            
            # Process for identity discoveries
            if narrative and actors_involved:
                identity_manager.process_narrative_for_identity_discovery(
                    narrative, actors_involved, actor_manager
                )
            
            return narrative
        
        # Replace the method
        narrator_agent.generate_outcome_narrative = enhanced_generate_outcome
    
    return narrator_agent
