from actor_sheet import ActorSheet
from enum import Enum
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field

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


# ═══════════════════════════════════════════════════════════════════════════════
# ACTOR CATEGORY SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class ActorCategory(Enum):
    """
    Actor categories for the simulation system.
    
    UA   - User Actor (player-controlled)
    NUA  - Non-User Actor (standard NPCs - people and animals)
    MNUA - Major Non-User Actor (important recurring characters)
    INUA - Inanimate Non-User Actor (objects, environments)
    """
    UA = "ua"
    NUA = "nua"
    MNUA = "mnua"
    INUA = "inua"


@dataclass
class MNUAStatus:
    """
    Tracks MNUA-specific data for major characters.
    
    MNUAs can be created via TWO PATHS:
    
    PATH 1 - ORGANIC PROMOTION:
        NUA earns significance through gameplay → graduates to MNUA
        Use: Characters who become important through player interaction
        
    PATH 2 - DIRECT CREATION:
        MNUA created directly with predefined role/significance
        Use: Story-critical characters (antagonists, mentors, pre-established relationships)
        Method: CreatorAgent.generate_mnua()
    
    MNUAs can:
    - Draw from Vessel/UA data pools
    - Have enhanced point allocation
    - Graduate from NUA status (Path 1)
    - Be created directly for narrative purposes (Path 2)
    - Play recurring narrative roles
    - Affect difficulty scaling via tension_modifier
    """
    is_mnua: bool = False
    graduation_date: Optional[str] = None  # When they became MNUA
    graduation_reason: Optional[str] = None  # Why they graduated
    relationship_significance: int = 0  # 0-10 scale of importance to UA
    recurring_role: Optional[str] = None  # Their narrative role
    ua_pool_access: bool = False  # Can draw from UA/Vessel data
    enhanced_points: int = 0  # Extra creation points used
    tension_modifier: float = 1.0  # How they affect difficulty scaling
    
    # Tracking for graduation criteria (Path 1: Organic Promotion)
    interaction_count: int = 0
    scenes_appeared: int = 0
    significant_events: List[str] = field(default_factory=list)
    
    # Tracking for tension-spawned MNUAs (Path 2: Direct Creation)
    spawn_tension_level: int = 0  # Tension level when spawned (0 = not tension-spawned)
    was_tension_spawned: bool = False  # True if created via tension trigger


# ═══════════════════════════════════════════════════════════════════════════════
# GRADUATION CRITERIA
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class GraduationCriteria:
    """Criteria for NUA → MNUA graduation"""
    min_interactions: int = 5  # Minimum direct interactions with UA
    min_scenes: int = 3  # Minimum scenes appeared in
    min_relationship_change: int = 2  # Sympathy change threshold (absolute)
    significant_event_required: bool = True  # Must have at least one significant event
    
    def check_graduation(self, mnua_status: MNUAStatus, sympathy_change: int = 0) -> tuple[bool, str]:
        """
        Check if an NUA qualifies for MNUA graduation.
        
        Returns:
            (qualifies: bool, reason: str)
        """
        reasons = []
        
        if mnua_status.interaction_count >= self.min_interactions:
            reasons.append(f"sufficient interactions ({mnua_status.interaction_count})")
        
        if mnua_status.scenes_appeared >= self.min_scenes:
            reasons.append(f"recurring presence ({mnua_status.scenes_appeared} scenes)")
        
        if abs(sympathy_change) >= self.min_relationship_change:
            direction = "positive" if sympathy_change > 0 else "negative"
            reasons.append(f"significant {direction} relationship ({sympathy_change:+d})")
        
        if mnua_status.significant_events:
            reasons.append(f"significant events: {', '.join(mnua_status.significant_events[:2])}")
        
        # Graduation requires at least 2 criteria met
        qualifies = len(reasons) >= 2
        
        if self.significant_event_required and not mnua_status.significant_events:
            qualifies = False
            reasons.append("(needs significant event)")
        
        return qualifies, "; ".join(reasons)


# Default graduation criteria
DEFAULT_GRADUATION_CRITERIA = GraduationCriteria()


class Actor:
    """Base class for all entities, linking a name to a detailed sheet."""
    def __init__(self, sheet: ActorSheet):
        self.sheet = sheet
        self.name = sheet.name

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}')"

    def is_user_controlled(self) -> bool:
        """Returns True if the actor is controlled by the user."""
        return False

class UserActor(Actor):
    """Represents the User's avatar in the Realita."""
    is_user_actor = True

    def __init__(self, sheet: ActorSheet):
        super().__init__(sheet)
        # User Actor skills are always revealed (you know your own abilities)
        self.sheet.revealed_skills = set(self.sheet.skills.keys())
        self.sheet.revealed_endowments = set(self.sheet.endowments.keys())

    def is_user_controlled(self) -> bool:
        """Returns True if the actor is controlled by the user."""
        return True

class NonUserActor(Actor):
    """
    Represents any sentient actor that is not controlled by the User.
    
    Can be either:
    - NUA (standard NPC)
    - MNUA (Major NPC - important recurring character)
    
    MNUAs can graduate from NUA status based on interaction history.
    """
    is_user_actor = False
    
    def __init__(self, sheet: ActorSheet, is_mnua: bool = False):
        super().__init__(sheet)
        self.identity_discovered = False  # Track if true identity is known
        self.original_name = sheet.name   # Store original name for reference
        self.discovered_details = {}      # Store newly learned information
        
        # MNUA status tracking
        self.mnua_status = MNUAStatus(is_mnua=is_mnua)
        if is_mnua:
            self.mnua_status.ua_pool_access = True
    
    @property
    def category(self) -> ActorCategory:
        """Get the actor's category"""
        return ActorCategory.MNUA if self.mnua_status.is_mnua else ActorCategory.NUA
    
    @property
    def is_mnua(self) -> bool:
        """Check if this is a Major NUA"""
        return self.mnua_status.is_mnua
    
    def record_interaction(self):
        """Record an interaction with the UA"""
        self.mnua_status.interaction_count += 1
    
    def record_scene_appearance(self):
        """Record appearing in a scene"""
        self.mnua_status.scenes_appeared += 1
    
    def record_significant_event(self, event_description: str):
        """Record a significant event involving this NUA"""
        self.mnua_status.significant_events.append(event_description)
    
    def check_graduation(self, sympathy_change: int = 0, 
                         criteria: GraduationCriteria = None) -> tuple[bool, str]:
        """
        Check if this NUA qualifies for MNUA graduation.
        
        Args:
            sympathy_change: Net change in sympathy since first meeting
            criteria: Custom graduation criteria (uses default if None)
        
        Returns:
            (qualifies: bool, reason: str)
        """
        if self.mnua_status.is_mnua:
            return False, "Already an MNUA"
        
        criteria = criteria or DEFAULT_GRADUATION_CRITERIA
        return criteria.check_graduation(self.mnua_status, sympathy_change)
    
    def graduate_to_mnua(self, reason: str, recurring_role: str = None,
                         tension_modifier: float = 1.0) -> bool:
        """
        Graduate this NUA to MNUA status.
        
        Args:
            reason: Why they're being graduated
            recurring_role: Their narrative role (e.g., "ally", "rival", "mentor")
            tension_modifier: How they affect difficulty (>1 = harder, <1 = easier)
        
        Returns:
            True if graduation successful
        """
        if self.mnua_status.is_mnua:
            return False
        
        import datetime
        self.mnua_status.is_mnua = True
        self.mnua_status.graduation_date = datetime.datetime.now().isoformat()
        self.mnua_status.graduation_reason = reason
        self.mnua_status.recurring_role = recurring_role
        self.mnua_status.ua_pool_access = True
        self.mnua_status.tension_modifier = tension_modifier
        
        return True
    
    def update_identity(self, new_name: str = None, new_occupation: str = None, 
                       new_details: dict = None, mark_discovered: bool = True):
        """Update NUA identity as information is discovered through narrative"""
        old_name = getattr(self.sheet, 'name', None)
        old_occupation = getattr(self.sheet, 'occupation', None)
        old_faction = getattr(self.sheet, 'faction', None)
        old_affiliation = getattr(self.sheet, 'affiliation', None)
        old_details = dict(getattr(self, 'discovered_details', {}) or {})
        old_discovered = bool(getattr(self, 'identity_discovered', False))

        if new_name and new_name != self.sheet.name:
            self.sheet.name = new_name
            self.name = new_name
            
        if new_occupation and new_occupation != self.sheet.occupation:
            self.sheet.occupation = new_occupation
            
        if new_details:
            try:
                if 'faction' in new_details and new_details.get('faction') is not None:
                    self.sheet.faction = new_details.get('faction')
                if 'affiliation' in new_details and new_details.get('affiliation') is not None:
                    self.sheet.affiliation = new_details.get('affiliation')
            except Exception:
                pass
            self.discovered_details.update(new_details)
            
        if mark_discovered:
            self.identity_discovered = True

        # Best-effort: persist identity discovery into everlasting context DB + seed decaying memory
        try:
            if ContextStore is None:
                return

            spatial = None
            session_id = "default"
            location_id = None
            try:
                if get_spatial_manager is not None:
                    spatial = get_spatial_manager()
                    session_id = getattr(spatial, 'session_id', None) or session_id
                    location_id = getattr(spatial, 'current_location', None)
            except Exception:
                spatial = None

            changed = False
            changes: Dict[str, Any] = {}
            if new_name and new_name != old_name:
                changed = True
                changes['name'] = {'old': old_name, 'new': new_name}
            if new_occupation and new_occupation != old_occupation:
                changed = True
                changes['occupation'] = {'old': old_occupation, 'new': new_occupation}
            if new_details:
                # Only record truly new/changed details (noise-filter)
                detail_changes: Dict[str, Any] = {}
                try:
                    for k, v in dict(new_details).items():
                        if k in ('faction', 'affiliation'):
                            continue
                        if old_details.get(k) != v:
                            detail_changes[k] = v
                except Exception:
                    detail_changes = dict(new_details)

                if detail_changes:
                    changed = True
                    changes['details'] = detail_changes

                # Faction/affiliation are first-class fields on ActorSheet
                try:
                    new_faction = getattr(self.sheet, 'faction', None)
                    if ('faction' in new_details) and (new_faction != old_faction):
                        changed = True
                        changes['faction'] = {'old': old_faction, 'new': new_faction}
                except Exception:
                    pass

                try:
                    new_affiliation = getattr(self.sheet, 'affiliation', None)
                    if ('affiliation' in new_details) and (new_affiliation != old_affiliation):
                        changed = True
                        changes['affiliation'] = {'old': old_affiliation, 'new': new_affiliation}
                except Exception:
                    pass
            if mark_discovered and not old_discovered:
                changed = True
                changes['identity_discovered'] = True

            if not changed:
                return

            # Resolve stable spatial actor_id if possible
            actor_id = self.sheet.name
            try:
                if get_spatial_manager is not None:
                    ctx = spatial.get_current_context() if spatial else None
                    if ctx and getattr(ctx, 'actor_positions', None):
                        for aid, apos in ctx.actor_positions.items():
                            if getattr(apos, 'actor_name', None) == self.sheet.name or getattr(apos, 'actor_name', None) == old_name:
                                actor_id = aid
                                break
            except Exception:
                actor_id = self.sheet.name

            # Time
            wt = None
            try:
                if get_master_time_coordinator is not None and WorldTime is not None:
                    tc = get_master_time_coordinator()
                    time_ctx = tc.get_current_time_context() if tc else None
                    gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
                    if gt is not None:
                        wt = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
            except Exception:
                wt = None

            from pathlib import Path
            store = ContextStore(Path('simulation_data/context/context.db'))
            summary = f"INFO LEARNED: {old_name or self.sheet.name} identity updated"
            event_id = store.log_world_event(
                session_id=session_id,
                location_id=location_id,
                event_type='INFO_LEARNED',
                summary=summary,
                importance=7,
                tags=['info', 'identity', 'discovery'],
                payload={
                    'actor_id': actor_id,
                    'actor_ids': [actor_id],
                    'actor_name': self.sheet.name,
                    'actor_names': [self.sheet.name],
                    'changes': changes,
                },
                world_time=wt
            )

            try:
                if hasattr(store, 'remember'):
                    store.remember(
                        session_id=session_id,
                        actor_id=str(actor_id),
                        memory_type='info_learned',
                        content=summary,
                        importance=7,
                        pinned=False,
                        decay_rate=0.00015,
                        source_event_id=int(event_id) if event_id is not None else None,
                        world_time=wt
                    )
            except Exception:
                pass
        except Exception:
            # Never break identity updates
            return
    
    def is_identity_known(self) -> bool:
        """Check if this NUA's true identity has been discovered"""
        return self.identity_discovered
    
    def get_display_name(self) -> str:
        """Get the name to display based on discovery status"""
        try:
            # Always mask true identity until it has been explicitly discovered.
            if not self.identity_discovered:
                return self.original_name or self.sheet.name
        except Exception:
            return getattr(self.sheet, 'name', None) or self.original_name or "Unknown"
        return self.sheet.name
    
    def get_tension_modifier(self) -> float:
        """Get this actor's tension/difficulty modifier"""
        return self.mnua_status.tension_modifier if self.mnua_status.is_mnua else 1.0

class InanimateNonUserActor(Actor):
    """Represents an inanimate object that can participate in the simulation.
    
    INUAs are objects, environments, or abstract concepts that can be interacted with
    but don't take independent actions. Examples include:
    - Doors, locks, traps
    - Environmental hazards (fire, water, cliffs)
    - Vehicles, machines, tools
    - Abstract concepts (reputation, weather, time pressure)
    """
    is_user_actor = False
    is_inanimate = True
    
    def __init__(self, sheet: ActorSheet):
        super().__init__(sheet)
    
    @property
    def category(self) -> ActorCategory:
        """Get the actor's category"""
        return ActorCategory.INUA


# ═══════════════════════════════════════════════════════════════════════════════
# MAJOR NUA (MNUA) CLASS - For direct creation as MNUA
# ═══════════════════════════════════════════════════════════════════════════════

class MajorNonUserActor(NonUserActor):
    """
    Major Non-User Actor - Important recurring characters.
    
    MNUAs are created directly as major characters or graduated from NUA status.
    They can:
    - Draw from Vessel/UA data pools for richer characterization
    - Have enhanced point allocation (same or more than UAs)
    - Affect tension/difficulty scaling
    - Play significant recurring narrative roles
    """
    
    # Enhanced creation points (same as UA or more)
    BASE_CREATION_POINTS = 30  # Standard UA points
    ENHANCED_POINTS_BONUS = 5  # Extra points for MNUAs
    
    def __init__(self, sheet: ActorSheet, recurring_role: str = None,
                 tension_modifier: float = 1.0, enhanced_points: int = 0):
        super().__init__(sheet, is_mnua=True)
        
        self.mnua_status.recurring_role = recurring_role
        self.mnua_status.tension_modifier = tension_modifier
        self.mnua_status.enhanced_points = enhanced_points or self.ENHANCED_POINTS_BONUS
        self.mnua_status.relationship_significance = 5  # Start at medium significance


# ═══════════════════════════════════════════════════════════════════════════════
# S-TRAIT OUTLIER SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

# N2N (Natural-to-Natural) descriptors for S-trait outliers
S_TRAIT_N2N_DESCRIPTORS = {
    'sturdiness': {
        1: ["frail", "gaunt", "skeletal", "wasted"],
        2: ["thin", "slight", "lean"],
        4: ["sturdy", "solid", "well-built"],
        5: ["massive", "hulking", "powerfully built", "imposing"]
    },
    'smart': {
        1: ["vacant-eyed", "confused", "slow-witted"],
        2: ["simple", "unassuming"],
        4: ["sharp-eyed", "keen", "observant"],
        5: ["piercing gaze", "calculating", "brilliant-looking"]
    },
    'swiftness': {
        1: ["sluggish", "lethargic", "plodding"],
        2: ["unhurried", "deliberate"],
        4: ["quick", "nimble", "agile"],
        5: ["lightning-fast", "darting", "hyperactive"]
    },
    'sociability': {
        1: ["withdrawn", "reclusive", "antisocial"],
        2: ["quiet", "reserved", "introverted"],
        4: ["friendly", "warm", "personable"],
        5: ["charismatic", "magnetic", "captivating"]
    },
    'shadow': {
        1: ["innocent-looking", "guileless", "open-faced"],
        2: ["earnest", "straightforward"],
        4: ["guarded", "wary-eyed", "secretive"],
        5: ["sinister", "menacing", "unsettling"]
    }
}


def get_s_trait_outliers(actor: Actor) -> List[Dict[str, Any]]:
    """
    Extract S-trait outliers (values of 1, 2, 4, or 5) from an actor.
    
    Returns list of outlier info with N2N descriptors.
    """
    outliers = []
    
    if not hasattr(actor, 'sheet') or not hasattr(actor.sheet, 's_factors'):
        return outliers
    
    s_factors = actor.sheet.s_factors
    if not s_factors:
        return outliers
    
    # Check each S-trait using proper SFactorType enum
    from actor_sheet import SFactorType
    trait_map = {
        'sturdiness': SFactorType.STURDINESS,
        'smarts': SFactorType.SMARTS,
        'swiftness': SFactorType.SWIFTNESS,
        'sociability': SFactorType.SOCIABILITY,
        'shadow': SFactorType.SHADOW
    }
    
    for trait_name, factor_type in trait_map.items():
        try:
            value = s_factors.get_factor(factor_type)
            
            # Only outliers (not 3 - average)
            if value in [1, 2, 4, 5]:
                descriptors = S_TRAIT_N2N_DESCRIPTORS.get(trait_name, {}).get(value, [])
                descriptor = descriptors[0] if descriptors else f"{trait_name}:{value}"
                
                outliers.append({
                    'trait': trait_name,
                    'value': value,
                    'descriptor': descriptor,
                    'all_descriptors': descriptors,
                    'is_extreme': value in [1, 5],
                    'direction': 'high' if value > 3 else 'low'
                })
        except Exception:
            continue
    
    # Sort by extremity (1 and 5 first)
    outliers.sort(key=lambda x: (not x['is_extreme'], x['trait']))
    
    return outliers


def format_outliers_for_introduction(actor: Actor, max_outliers: int = 2) -> str:
    """
    Format S-trait outliers for actor introduction.
    
    Returns a natural language description of the most notable traits.
    """
    outliers = get_s_trait_outliers(actor)
    
    if not outliers:
        return ""
    
    # Take most extreme outliers first
    extreme = [o for o in outliers if o['is_extreme']]
    moderate = [o for o in outliers if not o['is_extreme']]
    
    selected = (extreme + moderate)[:max_outliers]
    
    if not selected:
        return ""
    
    if len(selected) == 1:
        return selected[0]['descriptor']
    
    # Combine descriptors naturally
    descriptors = [o['descriptor'] for o in selected]
    return f"{descriptors[0]} and {descriptors[1]}"


# Alias for import compatibility
format_outliers_for_narrative = format_outliers_for_introduction


def get_actor_category(actor: Actor) -> ActorCategory:
    """Get the category of an actor (INUA, NUA, MNUA, or UA)"""
    if hasattr(actor, 'category'):
        return actor.category
    if isinstance(actor, UserActor):
        return ActorCategory.UA
    if isinstance(actor, NonUserActor):
        return ActorCategory.NUA
    return ActorCategory.INUA


def can_graduate_to_mnua(actor: Actor, interaction_count: int = 0, 
                          narrative_importance: float = 0.0) -> bool:
    """
    Check if an NUA can graduate to MNUA status.
    
    Criteria:
    - Must be NUA (not INUA or already MNUA)
    - High interaction count (5+) OR
    - High narrative importance (0.7+) OR
    - Explicitly marked for graduation
    """
    if not isinstance(actor, NonUserActor):
        return False
    
    current_cat = get_actor_category(actor)
    if current_cat != ActorCategory.NUA:
        return False
    
    # Check graduation criteria
    if interaction_count >= 5:
        return True
    if narrative_importance >= 0.7:
        return True
    if hasattr(actor, 'marked_for_mnua') and actor.marked_for_mnua:
        return True
    
    return False


def graduate_to_mnua(actor: Actor) -> bool:
    """Graduate an NUA to MNUA status"""
    if not can_graduate_to_mnua(actor):
        return False
    
    actor.category = ActorCategory.MNUA
    return True


def get_actor_introduction_description(actor: Actor, include_occupation: bool = True) -> str:
    """
    Generate a full introduction description for an actor.
    
    Includes:
    - S-trait outliers (N2N descriptors)
    - Occupation (if visible/known)
    - Age/gender indicators
    """
    parts = []
    
    # Get outlier descriptors
    outlier_desc = format_outliers_for_introduction(actor)
    if outlier_desc:
        parts.append(outlier_desc)
    
    # Get age descriptor
    if hasattr(actor, 'sheet'):
        age = getattr(actor.sheet, 'age', None)
        if age:
            if age < 20:
                parts.append("young")
            elif age > 60:
                parts.append("elderly")
            elif age > 45:
                parts.append("middle-aged")
    
    # Get gender noun
    gender = getattr(actor.sheet, 'gender', '').lower() if hasattr(actor, 'sheet') else ''
    if gender == 'male':
        noun = "man"
    elif gender == 'female':
        noun = "woman"
    else:
        noun = "person"
    
    # Combine
    if parts:
        return f"a {' '.join(parts)} {noun}"
    return f"a {noun}"
