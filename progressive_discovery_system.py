"""
Progressive Discovery System for UTAS Simulation

Manages the progression from environmental clues to diegetic NUA introduction.
Tracks player investigation and triggers actor creation when thresholds are reached.
"""

import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from diegetic_clue_tracker import DiegeticClueTracker, get_clue_tracker, ClueType

try:
    from context_store import ContextStore, WorldTime
except Exception:
    ContextStore = None
    WorldTime = None

try:
    from master_time_coordinator import get_master_time_coordinator
except Exception:
    get_master_time_coordinator = None

try:
    from spatial_context_system import get_spatial_manager
except Exception:
    get_spatial_manager = None

from pathlib import Path


@dataclass
class ActiveDiscovery:
    """Represents an ongoing clue investigation."""
    discovery_id: str
    clue_type: str
    implies: str  # What actor type this leads to
    threshold: int
    follow_count: int = 0
    first_detected_turn: int = 0
    first_narrative: str = ""
    last_follow_turn: int = 0
    urgency: str = "medium"
    confidence: str = "medium"
    is_fresh: bool = False
    has_direction: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class ProgressiveDiscoverySystem:
    """
    Manages progressive discovery mechanics where following clues leads to NUA introduction.
    
    Features:
    - Tracks multiple simultaneous clue trails
    - Threshold-based actor introduction
    - Context-aware NUA creation
    - Narrative integration support
    """
    
    def __init__(self):
        """Initialize the progressive discovery system."""
        self.clue_tracker = get_clue_tracker()
        self.active_discoveries: Dict[str, ActiveDiscovery] = {}
        self.current_turn = 0
        self.discovery_counter = 0

        # Best-effort: de-dupe persistence logging
        self._last_logged_clue_key: Optional[str] = None
        self._last_logged_threshold_key: Optional[str] = None
        
        # Configuration
        self.max_active_discoveries = 3  # Limit simultaneous trails
        self.stale_threshold = 5  # Turns before a trail goes stale
    
    def process_turn(self, user_input: str, narrative: str) -> Optional[Dict[str, Any]]:
        """
        Process a turn to check for clue progression and potential actor introduction.
        
        Args:
            user_input: The user's action this turn
            narrative: The narrative result of the action
            
        Returns:
            Introduction context dict if threshold reached, None otherwise
        """
        self.current_turn += 1
        
        # Step 1: Detect new clues in the narrative
        new_clues = self.clue_tracker.analyze_narrative_for_clues(narrative)
        for clue in new_clues:
            self._register_new_clue(clue)
        
        # Step 2: Check if user is following any active clues
        introduction_context = None
        for discovery_id, discovery in list(self.active_discoveries.items()):
            if self._is_following_clue(user_input, discovery):
                discovery.follow_count += 1
                discovery.last_follow_turn = self.current_turn
                
                print(f"[DISCOVERY] Following {discovery.clue_type}: {discovery.follow_count}/{discovery.threshold}")
                
                # Check if threshold reached
                if self._should_introduce_actor(discovery):
                    introduction_context = self._create_introduction_context(discovery)

                    # Best-effort: persist threshold reached as INFO_LEARNED (seed UA memory)
                    try:
                        self._log_threshold_reached(discovery, introduction_context)
                    except Exception:
                        pass

                    # Remove this discovery as it's been resolved
                    del self.active_discoveries[discovery_id]
                    break  # Only introduce one actor per turn
        
        # Step 3: Clean up stale discoveries
        self._cleanup_stale_discoveries()
        
        return introduction_context
    
    def _register_new_clue(self, clue: Dict[str, Any]):
        """Register a newly detected clue as an active discovery."""
        # Check if we already have too many active discoveries
        if len(self.active_discoveries) >= self.max_active_discoveries:
            # Remove oldest stale discovery
            self._remove_oldest_stale()
        
        # Create unique ID
        self.discovery_counter += 1
        discovery_id = f"{clue['type']}_{self.discovery_counter}"
        
        # Create active discovery
        discovery = ActiveDiscovery(
            discovery_id=discovery_id,
            clue_type=clue['type'],
            implies=clue['implies'],
            threshold=clue['threshold'],
            first_detected_turn=self.current_turn,
            first_narrative=clue['full_narrative'],
            urgency=clue['urgency'],
            confidence=clue['confidence'],
            is_fresh=clue['is_fresh'],
            has_direction=clue['has_direction'],
            metadata={
                'keyword': clue['keyword'],
                'context': clue['context']
            }
        )
        
        self.active_discoveries[discovery_id] = discovery
        print(f"[DISCOVERY] New clue registered: {clue['type']} (threshold: {clue['threshold']})")

        # Best-effort: persist clue detection (no memory seeding; noise-filtered)
        try:
            self._log_clue_detected(discovery)
        except Exception:
            pass


    def _get_world_time_safe(self) -> Optional['WorldTime']:
        try:
            if get_master_time_coordinator is None or WorldTime is None:
                return None
            tc = get_master_time_coordinator()
            time_ctx = tc.get_current_time_context() if tc else None
            gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
            if gt is None:
                return None
            return WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
        except Exception:
            return None


    def _try_get_session_location_and_user(self) -> tuple[str, Optional[str], Optional[str], Optional[str]]:
        """Returns (session_id, location_id, ua_id, ua_name) best-effort."""
        session_id = 'default'
        location_id = None
        ua_id = None
        ua_name = None
        try:
            if get_spatial_manager is None:
                return session_id, location_id, ua_id, ua_name
            spatial = get_spatial_manager()
            session_id = getattr(spatial, 'session_id', None) or session_id
            location_id = getattr(spatial, 'current_location', None)
            ctx = spatial.get_current_context() if spatial else None
            if ctx and getattr(ctx, 'actor_positions', None):
                for aid, apos in ctx.actor_positions.items():
                    if getattr(apos, 'is_user_actor', False):
                        ua_id = str(aid)
                        ua_name = getattr(apos, 'actor_name', None)
                        break
        except Exception:
            pass
        return session_id, location_id, ua_id, ua_name


    def _log_clue_detected(self, discovery: ActiveDiscovery) -> None:
        try:
            if ContextStore is None:
                return

            session_id, location_id, ua_id, ua_name = self._try_get_session_location_and_user()
            wt = self._get_world_time_safe()
            store = ContextStore(Path('simulation_data/context/context.db'))

            key = f"{discovery.clue_type}||{discovery.metadata.get('keyword')}||{discovery.metadata.get('context')}||{location_id}"
            if key == getattr(self, '_last_logged_clue_key', None):
                return
            self._last_logged_clue_key = key

            summary = f"Clue detected: {discovery.clue_type} (implies {discovery.implies})"
            store.log_world_event(
                session_id=session_id,
                location_id=location_id,
                event_type='CLUE_DETECTED',
                summary=summary,
                importance=3,
                tags=['discovery', 'clue', str(discovery.clue_type).lower()],
                payload={
                    'actor_ids': [ua_id] if ua_id else [],
                    'actor_names': [ua_name] if ua_name else [],
                    'discovery_id': discovery.discovery_id,
                    'clue_type': discovery.clue_type,
                    'implies': discovery.implies,
                    'threshold': int(discovery.threshold),
                    'urgency': discovery.urgency,
                    'confidence': discovery.confidence,
                    'is_fresh': bool(discovery.is_fresh),
                    'has_direction': bool(discovery.has_direction),
                    'metadata': dict(discovery.metadata or {}),
                    'first_narrative': discovery.first_narrative,
                },
                world_time=wt
            )
        except Exception:
            return


    def _log_threshold_reached(self, discovery: ActiveDiscovery, introduction_context: Optional[Dict[str, Any]]) -> None:
        try:
            if ContextStore is None:
                return

            session_id, location_id, ua_id, ua_name = self._try_get_session_location_and_user()
            wt = self._get_world_time_safe()
            store = ContextStore(Path('simulation_data/context/context.db'))

            key = f"{discovery.clue_type}||THRESHOLD||{discovery.metadata.get('keyword')}||{location_id}"
            if key == getattr(self, '_last_logged_threshold_key', None):
                return
            self._last_logged_threshold_key = key

            observer_id = ua_id or 'ua_001'
            observer_name = ua_name or 'User'
            summary = f"INFO LEARNED: {observer_name} followed clues and uncovered a lead ({discovery.clue_type} -> {discovery.implies})"

            event_id = store.log_world_event(
                session_id=session_id,
                location_id=location_id,
                event_type='INFO_LEARNED',
                summary=summary,
                importance=7,
                tags=['info', 'discovery', 'clue_trail', str(discovery.clue_type).lower()],
                payload={
                    'actor_ids': [observer_id],
                    'actor_names': [observer_name],
                    'discovery_id': discovery.discovery_id,
                    'clue_type': discovery.clue_type,
                    'implies': discovery.implies,
                    'threshold': int(discovery.threshold),
                    'follow_count': int(discovery.follow_count),
                    'urgency': discovery.urgency,
                    'confidence': discovery.confidence,
                    'metadata': dict(discovery.metadata or {}),
                    'first_narrative': discovery.first_narrative,
                    'introduction_context': dict(introduction_context or {}),
                },
                world_time=wt
            )

            try:
                if hasattr(store, 'remember'):
                    store.remember(
                        session_id=session_id,
                        actor_id=str(observer_id),
                        memory_type='info_learned',
                        content=summary,
                        importance=7,
                        pinned=False,
                        decay_rate=0.00016,
                        source_event_id=int(event_id) if event_id is not None else None,
                        world_time=wt
                    )
            except Exception:
                pass
        except Exception:
            return
    
    def _is_following_clue(self, user_input: str, discovery: ActiveDiscovery) -> bool:
        """Check if user input represents following this specific clue."""
        return self.clue_tracker.is_following_action(user_input, discovery.clue_type)
    
    def _should_introduce_actor(self, discovery: ActiveDiscovery) -> bool:
        """Determine if it's time to introduce the NUA."""
        return discovery.follow_count >= discovery.threshold
    
    def _create_introduction_context(self, discovery: ActiveDiscovery) -> Dict[str, Any]:
        """
        Create context for NUA introduction based on discovery progression.
        
        Returns:
            Context dict with all information needed to create and introduce the NUA
        """
        # Determine introduction style based on clue type and urgency
        if discovery.urgency == "high" or discovery.clue_type in ["movement", "shadow", "voices"]:
            introduction_style = "sudden_encounter"
        else:
            introduction_style = "gradual_reveal"
        
        # Infer NUA characteristics from clue type
        nua_characteristics = self._infer_nua_characteristics(discovery)
        
        return {
            'trigger': 'progressive_discovery',
            'discovery_id': discovery.discovery_id,
            'clue_type': discovery.clue_type,
            'follow_count': discovery.follow_count,
            'threshold': discovery.threshold,
            'introduction_style': introduction_style,
            'urgency': discovery.urgency,
            'confidence': discovery.confidence,
            'suggested_nua_type': discovery.implies,
            'nua_characteristics': nua_characteristics,
            'first_narrative': discovery.first_narrative,
            'narrative_hint': self._generate_narrative_hint(discovery)
        }
    
    def _infer_nua_characteristics(self, discovery: ActiveDiscovery) -> Dict[str, Any]:
        """
        Infer NUA characteristics based on the clue type.
        
        Returns:
            Dict with suggested NUA attributes
        """
        characteristics = {
            'occupation': 'Unknown',
            'initial_state': 'unaware',  # or 'aware', 'hostile', 'friendly'
            'suggested_name': None,
            'context_hints': []
        }
        
        clue_type = discovery.clue_type
        
        if clue_type == "footprints" or clue_type == "tracks":
            characteristics['context_hints'] = [
                "recently passed through",
                "on foot",
                "moving with purpose"
            ]
            characteristics['initial_state'] = 'unaware'
        
        elif clue_type == "voices":
            characteristics['context_hints'] = [
                "talking to someone or themselves",
                "unaware of your presence"
            ]
            characteristics['initial_state'] = 'unaware'
        
        elif clue_type == "blood_trail":
            characteristics['context_hints'] = [
                "injured",
                "bleeding",
                "may be weakened"
            ]
            characteristics['initial_state'] = 'distressed'
            characteristics['occupation'] = 'Injured Person'
        
        elif clue_type == "smoke":
            characteristics['context_hints'] = [
                "has made camp",
                "cooking or warming themselves",
                "settled in one spot"
            ]
            characteristics['initial_state'] = 'relaxed'
        
        elif clue_type == "movement" or clue_type == "shadow":
            characteristics['context_hints'] = [
                "nearby",
                "possibly aware of you",
                "moving cautiously"
            ]
            characteristics['initial_state'] = 'alert'
        
        elif clue_type == "light":
            characteristics['context_hints'] = [
                "carrying a light source",
                "searching or navigating",
                "may not have noticed you yet"
            ]
            characteristics['initial_state'] = 'focused'
        
        return characteristics
    
    def _generate_narrative_hint(self, discovery: ActiveDiscovery) -> str:
        """
        Generate a narrative hint for the NUA introduction.
        
        This provides context for the narrator to create a smooth introduction.
        """
        clue_type = discovery.clue_type
        
        hints = {
            "footprints": "The trail leads you to...",
            "tracks": "Following the tracks, you discover...",
            "voices": "The voices grow clearer as you approach, revealing...",
            "sounds": "The sounds lead you to...",
            "blood_trail": "The blood trail ends at...",
            "smoke": "Following the smoke, you find...",
            "light": "The light source belongs to...",
            "movement": "The movement resolves into...",
            "shadow": "The shadow takes form as...",
            "scent": "Following the scent, you discover..."
        }
        
        return hints.get(clue_type, "You discover...")
    
    def _cleanup_stale_discoveries(self):
        """Remove discoveries that haven't been followed recently."""
        stale_ids = []
        
        for discovery_id, discovery in self.active_discoveries.items():
            turns_since_follow = self.current_turn - discovery.last_follow_turn
            
            # If never followed, check turns since first detected
            if discovery.follow_count == 0:
                turns_since_follow = self.current_turn - discovery.first_detected_turn
            
            if turns_since_follow > self.stale_threshold:
                stale_ids.append(discovery_id)
        
        for discovery_id in stale_ids:
            print(f"[DISCOVERY] Clue trail went stale: {self.active_discoveries[discovery_id].clue_type}")
            del self.active_discoveries[discovery_id]
    
    def _remove_oldest_stale(self):
        """Remove the oldest stale discovery to make room for new ones."""
        if not self.active_discoveries:
            return
        
        # Find discovery with longest time since last follow
        oldest_id = None
        oldest_time = -1
        
        for discovery_id, discovery in self.active_discoveries.items():
            time_since_follow = self.current_turn - discovery.last_follow_turn
            if discovery.follow_count == 0:
                time_since_follow = self.current_turn - discovery.first_detected_turn
            
            if time_since_follow > oldest_time:
                oldest_time = time_since_follow
                oldest_id = discovery_id
        
        if oldest_id:
            del self.active_discoveries[oldest_id]
    
    def get_active_discoveries_summary(self) -> List[Dict[str, Any]]:
        """Get a summary of all active discoveries for debugging."""
        return [
            {
                'id': discovery.discovery_id,
                'type': discovery.clue_type,
                'progress': f"{discovery.follow_count}/{discovery.threshold}",
                'turns_active': self.current_turn - discovery.first_detected_turn
            }
            for discovery in self.active_discoveries.values()
        ]


# Global instance for easy access
_progressive_discovery_instance = None

def get_progressive_discovery() -> ProgressiveDiscoverySystem:
    """Get or create the global progressive discovery system instance."""
    global _progressive_discovery_instance
    if _progressive_discovery_instance is None:
        _progressive_discovery_instance = ProgressiveDiscoverySystem()
    return _progressive_discovery_instance
