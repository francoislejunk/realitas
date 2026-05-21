"""
Diegetic Momentum Tracker for Enhanced Four Mode Narrative Loop

Tracks story momentum through in-world logical factors rather than arbitrary timers.
Provides immersion-first activation triggers based on fiction state.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum

# Configurable keyword sets for fallback analysis
MOMENTUM_KEYWORDS = {
    'high_energy': ['attack', 'charge', 'rush', 'sprint', 'leap', 'dive', 'strike', 'slam', 'burst', 'explode'],
    'medium_energy': ['walk', 'move', 'approach', 'examine', 'search', 'investigate', 'talk', 'speak'],
    'low_energy': ['wait', 'pause', 'hesitate', 'consider', 'think', 'ponder', 'observe', 'watch'],
    
    'high_motivation': ['determined', 'focused', 'urgent', 'desperate', 'driven', 'committed', 'resolved'],
    'medium_motivation': ['interested', 'curious', 'willing', 'ready', 'prepared', 'motivated'],
    'low_motivation': ['reluctant', 'hesitant', 'uncertain', 'doubtful', 'confused', 'lost'],
    
    'high_social': ['confront', 'challenge', 'argue', 'debate', 'negotiate', 'persuade', 'demand'],
    'medium_social': ['ask', 'tell', 'talk', 'speak', 'say', 'respond', 'discuss'],
    'low_social': ['ignore', 'avoid', 'leave', 'walk away', 'withdraw', 'retreat'],
    
    'high_npc_pressure': ['attack', 'threaten', 'hostile', 'angry', 'furious', 'enemy', 'fight', 'combat', 
                         'battle', 'confrontation', 'aggressive', 'demands', 'insists', 'forces', 'compels', 
                         'urgent', 'desperate'],
    'medium_npc_pressure': ['suspicious', 'wary', 'cautious', 'tense', 'nervous', 'concerned', 'worried', 
                           'questioning', 'challenging', 'disagreement', 'argument', 'debate', 'negotiation'],
    'low_npc_pressure': ['friendly', 'helpful', 'kind', 'supportive', 'calm', 'peaceful', 'agreeable', 
                        'cooperative', 'understanding'],
    
    'high_env_pressure': ['storm', 'fire', 'flood', 'earthquake', 'avalanche', 'blizzard', 'darkness', 'fog', 
                         'mist', 'shadows', 'ruins', 'abandoned', 'crumbling', 'unstable', 'dangerous', 
                         'treacherous', 'hostile', 'deadline', 'urgent', 'running out', 'limited time', 'quickly'],
    'medium_env_pressure': ['rain', 'wind', 'cold', 'hot', 'crowded', 'noisy', 'busy', 'unfamiliar', 'strange', 
                           'eerie', 'quiet', 'isolated', 'remote', 'narrow', 'steep', 'high', 'deep'],
    'low_env_pressure': ['sunny', 'calm', 'peaceful', 'safe', 'comfortable', 'familiar', 'warm', 'bright', 
                        'open', 'spacious', 'plenty of time', 'relaxed']
}

class MomentumFactor(Enum):
    """Types of diegetic factors that influence narrative momentum"""
    SCENE_ENERGY = "scene_energy"          # How static/dynamic is the current situation
    CHARACTER_MOTIVATION = "character_motivation"  # Goal pursuit vs abandonment
    ENVIRONMENTAL_PRESSURE = "environmental_pressure"  # Time-sensitive factors
    SOCIAL_DYNAMICS = "social_dynamics"    # NPC patience and reactions
    LOCATION_CONTEXT = "location_context"  # Busy vs quiet, safe vs dangerous

@dataclass
class MomentumState:
    """Current momentum state of the narrative"""
    scene_stagnation_turns: int = 0
    active_goals: List[str] = field(default_factory=list)
    environmental_factors: Dict[str, Any] = field(default_factory=dict)
    npc_patience_levels: Dict[str, float] = field(default_factory=dict)  # 0.0-1.0
    location_pressure: float = 0.0  # 0.0 (calm) to 1.0 (urgent)
    last_significant_event: Optional[datetime] = None

class DiegeticMomentumTracker:
    """Tracks narrative momentum through story logic rather than arbitrary timing"""
    
    def __init__(self, client=None):
        self.momentum_state = MomentumState()
        self.momentum_history: List[Dict[str, Any]] = []
        self.client = client
    
    def analyze_turn_momentum(self, turn_data: Dict[str, Any], scene_context: str, 
                            time_context: Dict[str, Any] = None, available_npcs: List[Any] = None) -> Dict[str, float]:
        """Analyze momentum factors for a given turn using diegetic elements."""
        momentum_scores = {}
        
        # Analyze scene energy
        momentum_scores['scene_energy'] = self._analyze_scene_energy(turn_data)
        
        # Analyze character motivation
        momentum_scores['character_motivation'] = self._analyze_character_motivation(turn_data)
        
        # Enhanced environmental pressure analysis
        momentum_scores['environmental_pressure'] = self.analyze_environmental_pressure(scene_context, time_context)
        
        # Analyze social dynamics
        momentum_scores['social_dynamics'] = self._analyze_social_dynamics(turn_data)
        
        # Analyze location context
        momentum_scores['location_context'] = self._analyze_location_context(scene_context)
        
        # Add NPC-driven pressure as additional factor
        if available_npcs:
            npc_pressure = self.analyze_npc_driven_pressure(turn_data, available_npcs)
            # Weight NPC pressure into social dynamics and environmental pressure
            momentum_scores['social_dynamics'] = min(1.0, 
                momentum_scores['social_dynamics'] + (npc_pressure * 0.3))
            momentum_scores['environmental_pressure'] = min(1.0,
                momentum_scores['environmental_pressure'] + (npc_pressure * 0.2))
        
        return momentum_scores
    
    def _analyze_scene_energy(self, turn_data: Dict[str, Any]) -> float:
        """Use LLM to analyze scene energy and momentum"""
        user_input = turn_data.get('user_input', '')
        
        # Use LLM for nuanced analysis instead of keyword matching
        prompt = f"""
        Analyze the energy level of this player action in a narrative context.
        
        Player Action: "{user_input}"
        
        Rate the energy level from 0.0 to 1.0 where:
        - 0.9-1.0: High energy (combat, chase, urgent action, decisive movement)
        - 0.6-0.8: Medium energy (social interaction, purposeful investigation, active engagement)
        - 0.3-0.5: Low energy (passive observation, hesitation, contemplation)
        - 0.0-0.2: Very low energy (aimless wandering, indecision, stalling)
        
        Consider:
        - Action vs observation
        - Decisiveness vs hesitation
        - Engagement vs withdrawal
        - Purpose vs aimlessness
        
        Respond with only a number between 0.0 and 1.0.
        """
        
        try:
            if self.client:
                response = self.client.chat.completions.create(
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0.3
                )
            else:
                from openrouter_config import create_role_client, OpenRouterConfig
                client = create_role_client("analysis")
                model = OpenRouterConfig.get_model_for_role("analysis")
                response = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=10,
                    temperature=0.3
                )
            
            energy_score = float(response.choices[0].message.content.strip())
            
            # Update stagnation tracking based on energy
            if energy_score > 0.5:
                self.momentum_state.scene_stagnation_turns = 0
            else:
                self.momentum_state.scene_stagnation_turns += 1
            
            # Apply stagnation penalty
            stagnation_penalty = self.momentum_state.scene_stagnation_turns * 0.1
            return max(0.0, energy_score - stagnation_penalty)
            
        except Exception as e:
            # Fallback to simple keyword analysis if LLM fails
            return self._fallback_energy_analysis(user_input)
    
    def _analyze_character_motivation(self, turn_data: Dict[str, Any]) -> float:
        """Use LLM to analyze character motivation and goal clarity"""
        user_input = turn_data.get('user_input', '')
        
        prompt = f"""
        Analyze the motivation level in this player action.
        
        Player Action: "{user_input}"
        
        Rate motivation from 0.0 to 1.0 where:
        - 0.8-1.0: Clear goals ("I need to find...", "I'm going to...", decisive action)
        - 0.6-0.7: Seeking direction (questions, exploration with purpose)
        - 0.4-0.5: Neutral engagement (general interaction, mild interest)
        - 0.2-0.3: Low motivation (hesitation, uncertainty, "I don't know")
        - 0.0-0.1: Aimless (wandering, complete indecision, disengagement)
        
        Consider:
        - Clarity of intent
        - Decisiveness vs hesitation
        - Goal-oriented vs exploratory language
        - Engagement vs withdrawal
        
        Respond with only a number between 0.0 and 1.0.
        """
        
        try:
            from openrouter_config import create_role_client, OpenRouterConfig
            client = create_role_client("analysis")
            model = OpenRouterConfig.get_model_for_role("analysis")
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.3
            )
            
            return float(response.choices[0].message.content.strip())
            
        except Exception as e:
            return self._fallback_motivation_analysis(user_input)
    
    def _analyze_environmental_pressure(self, scene_context: str) -> float:
        """Detect environmental factors that create natural urgency"""
        scene_lower = scene_context.lower()
        
        # High pressure environments
        high_pressure = ['alarm', 'fire', 'police', 'emergency', 'closing', 'deadline', 'storm']
        if any(word in scene_lower for word in high_pressure):
            return 0.9
        
        # Medium pressure environments
        medium_pressure = ['crowd', 'busy', 'rush', 'hurried', 'impatient', 'waiting']
        if any(word in scene_lower for word in medium_pressure):
            return 0.6
        
        # Low pressure environments
        low_pressure = ['quiet', 'peaceful', 'empty', 'calm', 'relaxed']
        if any(word in scene_lower for word in low_pressure):
            return 0.2
        
        return 0.4  # Default moderate pressure
    
    def _analyze_social_dynamics(self, turn_data: Dict[str, Any]) -> float:
        """Use LLM to analyze social pressure and interaction dynamics"""
        user_input = turn_data.get('user_input', '')
        
        prompt = f"""
        Analyze the social dynamics and pressure in this player action.
        
        Player Action: "{user_input}"
        
        Rate social pressure from 0.0 to 1.0 where:
        - 0.8-1.0: High social engagement (direct conversation, confrontation, urgent social needs)
        - 0.6-0.7: Active social interaction (asking questions, responding, social investigation)
        - 0.4-0.5: Neutral social presence (observing others, mild social awareness)
        - 0.2-0.3: Social withdrawal (avoiding interaction, leaving social situations)
        - 0.0-0.1: Social isolation (ignoring others, complete social disengagement)
        
        Consider:
        - Direct vs indirect social engagement
        - Urgency of social needs
        - Relationship building vs avoidance
        - Communication vs withdrawal
        
        Respond with only a number between 0.0 and 1.0.
        """
        
        try:
            from openrouter_config import create_role_client, OpenRouterConfig
            client = create_role_client("analysis")
            model = OpenRouterConfig.get_model_for_role("analysis")
            
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.3
            )
            
            return float(response.choices[0].message.content.strip())
            
        except Exception as e:
            return self._fallback_social_analysis(user_input)
    
    def _analyze_location_context(self, scene_context: str) -> float:
        """Analyze location-based momentum factors"""
        scene_lower = scene_context.lower()
        
        # High-momentum locations
        high_momentum = ['street', 'market', 'bar', 'club', 'station', 'airport']
        if any(word in scene_lower for word in high_momentum):
            return 0.7
        
        # Low-momentum locations
        low_momentum = ['home', 'bedroom', 'library', 'park', 'garden']
        if any(word in scene_lower for word in low_momentum):
            return 0.3
        
        return 0.5  # Default momentum
    
    def should_trigger_mode_transition(self, momentum_scores: Dict[MomentumFactor, float], 
                                     current_mode: str) -> Optional[str]:
        """
        Determine if momentum factors suggest a mode transition
        
        Returns:
            Suggested new mode or None if no transition needed
        """
        # Calculate weighted momentum score
        weights = {
            MomentumFactor.SCENE_ENERGY: 0.3,
            MomentumFactor.CHARACTER_MOTIVATION: 0.25,
            MomentumFactor.ENVIRONMENTAL_PRESSURE: 0.2,
            MomentumFactor.SOCIAL_DYNAMICS: 0.15,
            MomentumFactor.LOCATION_CONTEXT: 0.1
        }
        
        total_momentum = sum(
            momentum_scores.get(factor, 0.5) * weight 
            for factor, weight in weights.items()
        )
        
        # Mode transition logic based on momentum
        if current_mode == 'roam':
            # Low energy + low motivation = need spark
            if (momentum_scores.get(MomentumFactor.SCENE_ENERGY, 0.5) < 0.3 and 
                momentum_scores.get(MomentumFactor.CHARACTER_MOTIVATION, 0.5) < 0.4):
                return 'spark'
        
        elif current_mode == 'spark':
            # High environmental pressure = move to pressure
            if momentum_scores.get(MomentumFactor.ENVIRONMENTAL_PRESSURE, 0.5) > 0.7:
                return 'pressure'
        
        elif current_mode == 'pressure':
            # Very low momentum = resolution needed
            if total_momentum < 0.3:
                return 'outcome'
        
        elif current_mode == 'outcome':
            # Return to roam after resolution
            if total_momentum > 0.4:
                return 'roam'
        
        return None
    
    def get_diegetic_cues(self, momentum_scores: Dict[MomentumFactor, float], 
                         suggested_mode: Optional[str]) -> List[str]:
        """Generate diegetic cues based on momentum analysis"""
        cues = []
        
        if suggested_mode == 'spark':
            if momentum_scores.get(MomentumFactor.SCENE_ENERGY, 0.5) < 0.3:
                cues.append("The scene feels static - something needs to change")
            if momentum_scores.get(MomentumFactor.CHARACTER_MOTIVATION, 0.5) < 0.4:
                cues.append("Character seems to lack clear direction")
        
        elif suggested_mode == 'pressure':
            if momentum_scores.get(MomentumFactor.ENVIRONMENTAL_PRESSURE, 0.5) > 0.7:
                cues.append("Environmental factors create urgency")
            if momentum_scores.get(MomentumFactor.SOCIAL_DYNAMICS, 0.5) > 0.6:
                cues.append("Social pressure is building")
        
        elif suggested_mode == 'outcome':
            cues.append("Situation needs resolution")
        
        return cues
    
    def _fallback_energy_analysis(self, user_input: str) -> float:
        """Fallback energy analysis using keywords when LLM fails"""
        user_input = user_input.lower()
        
        if any(word in user_input for word in MOMENTUM_KEYWORDS['high_energy']):
            return 0.9
        elif any(word in user_input for word in MOMENTUM_KEYWORDS['medium_energy']):
            return 0.6
        elif any(word in user_input for word in MOMENTUM_KEYWORDS['low_energy']):
            return 0.3
        
        return 0.5  # Default medium energy

    def _fallback_motivation_analysis(self, user_input: str) -> float:
        """Fallback keyword-based analysis if LLM fails"""
        user_input = user_input.lower()
        
        if any(word in user_input for word in MOMENTUM_KEYWORDS['high_motivation']):
            return 0.8
        elif any(word in user_input for word in MOMENTUM_KEYWORDS['medium_motivation']):
            return 0.6
        elif any(word in user_input for word in MOMENTUM_KEYWORDS['low_motivation']):
            return 0.3
        
        # Additional goal indicators
        goal_indicators = ['need to', 'want to', 'should', 'must', 'have to', 'going to']
        if any(phrase in user_input for phrase in goal_indicators):
            return 0.8
        
        if '?' in user_input:
            return 0.6
        
        return 0.5
    
    def _fallback_social_analysis(self, user_input: str) -> float:
        """Fallback keyword-based analysis if LLM fails"""
        user_input = user_input.lower()
        
        if any(word in user_input for word in MOMENTUM_KEYWORDS['high_social']):
            return 0.8
        elif any(word in user_input for word in MOMENTUM_KEYWORDS['medium_social']):
            return 0.6
        elif any(word in user_input for word in MOMENTUM_KEYWORDS['low_social']):
            return 0.3
        
        return 0.5

    def analyze_environmental_pressure(self, scene_context: str, time_context: Dict[str, Any] = None) -> float:
        """Analyze environmental factors that create narrative pressure."""
        try:
            prompt = f"""
            Analyze the environmental narrative pressure in this scene context.
            
            Scene Context: {scene_context}
            Time Context: {time_context if time_context else 'Not specified'}
            
            Rate the environmental pressure from 0.0 to 1.0 based on:
            - Weather conditions and their impact on tension
            - Location danger level and atmosphere
            - Time pressure (deadlines, urgency)
            - Resource scarcity or abundance
            - Ambient threats or safety
            - Atmospheric mood and tension
            
            Respond with only a number between 0.0 and 1.0.
            """
            
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10
            )
            
            score_text = response.choices[0].message.content.strip()
            score = float(score_text)
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            # Fallback: keyword-based environmental pressure analysis
            return self._fallback_environmental_pressure(scene_context, time_context)
    
    def _fallback_environmental_pressure(self, scene_context: str, time_context: Dict[str, Any] = None) -> float:
        """Fallback environmental pressure analysis using keywords."""
        context_lower = scene_context.lower()
        
        if any(phrase in context_lower for phrase in MOMENTUM_KEYWORDS['high_env_pressure']):
            return 0.8
        elif any(phrase in context_lower for phrase in MOMENTUM_KEYWORDS['medium_env_pressure']):
            return 0.6
        elif any(phrase in context_lower for phrase in MOMENTUM_KEYWORDS['low_env_pressure']):
            return 0.2
        
        return 0.4

    def analyze_npc_driven_pressure(self, turn_data: Dict[str, Any], available_npcs: List[Any] = None) -> float:
        """Analyze narrative pressure created by NPC behavior and presence."""
        try:
            npc_context = ""
            if available_npcs:
                npc_names = []
                for npc in available_npcs:
                    if hasattr(npc, 'sheet') and hasattr(npc.sheet, 'name'):
                        npc_names.append(npc.sheet.name)
                    else:
                        npc_names.append('Unknown NUA')
                npc_context = f"Available NUAs: {', '.join(npc_names)}"
            
            user_input = turn_data.get('user_input', '')
            narrative_response = turn_data.get('narrative_response', '')
            
            prompt = f"""
            Analyze the NPC-driven narrative pressure in this situation.
            
            User Action: {user_input}
            Narrative Response: {narrative_response}
            {npc_context}
            
            Rate the NPC-driven pressure from 0.0 to 1.0 based on:
            - NPC hostility or friendliness toward the player
            - NPC urgency or demands on the player
            - Social tension or conflict with NPCs
            - NPC-created obstacles or complications
            - Number and intensity of NPC interactions
            - NPC emotional states affecting the scene
            
            Respond with only a number between 0.0 and 1.0.
            """
            
            response = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=10
            )
            
            score_text = response.choices[0].message.content.strip()
            score = float(score_text)
            return max(0.0, min(1.0, score))
            
        except Exception as e:
            # Fallback: keyword-based NPC pressure analysis
            return self._fallback_npc_pressure(turn_data, available_npcs)
    
    def _fallback_npc_pressure(self, turn_data: Dict[str, Any], available_npcs: List[Any] = None) -> float:
        """Fallback NUA pressure analysis using keywords."""
        user_input = turn_data.get('user_input', '') or ''
        narrative_response = turn_data.get('narrative_response', '') or ''
        combined_text = f"{user_input.lower()} {narrative_response.lower()}"
        
        # Bonus pressure for multiple NPCs
        npc_count_bonus = 0.0
        if available_npcs and len(available_npcs) > 1:
            npc_count_bonus = min(0.2, len(available_npcs) * 0.1)
        
        base_pressure = 0.3
        if any(phrase in combined_text for phrase in MOMENTUM_KEYWORDS['high_npc_pressure']):
            base_pressure = 0.8
        elif any(phrase in combined_text for phrase in MOMENTUM_KEYWORDS['medium_npc_pressure']):
            base_pressure = 0.6
        elif any(phrase in combined_text for phrase in MOMENTUM_KEYWORDS['low_npc_pressure']):
            base_pressure = 0.2
        
        return min(1.0, base_pressure + npc_count_bonus)
