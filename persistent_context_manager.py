"""
Persistent Context Manager - NEVER LOSE CONTEXT AGAIN

This system saves EVERY piece of context to disk immediately and loads it on demand.
No more forgetting where we are, who's present, or what just happened.

Design Philosophy:
- Save EVERYTHING, IMMEDIATELY
- Load EVERYTHING, ALWAYS
- Context is SACRED - never lose it
- Disk is cheap, immersion is priceless
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field, asdict
from enum import Enum


class ContextPriority(Enum):
    """Priority levels for context persistence"""
    CRITICAL = "critical"  # Must never be lost (location, NUAs, scene)
    HIGH = "high"          # Very important (recent events, opportunities)
    MEDIUM = "medium"      # Important (atmosphere, objects)
    LOW = "low"            # Nice to have (ambient details)


@dataclass
class PersistentContext:
    """
    Complete context state that gets saved to disk after EVERY change.
    This is the single source of truth for where we are and what's happening.
    """
    # === CRITICAL CONTEXT (Never lose this) ===
    session_id: str = ""
    current_location: str = "unknown"
    previous_location: str = ""  # Where we just came from (for instant return)
    current_scene_description: str = ""
    location_label: str = ""  # e.g., "diner", "garage"
    present_nuas: List[str] = field(default_factory=list)  # Non-User Actors present
    available_nua_ids: List[str] = field(default_factory=list)  # Actor IDs for reconstruction
    
    # === HIGH PRIORITY CONTEXT ===
    recent_events: List[str] = field(default_factory=list)  # Last 10 events
    recent_narratives: List[str] = field(default_factory=list)  # Last 5 narrations
    unresolved_threads: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    visible_objects: List[str] = field(default_factory=list)
    accessible_paths: List[str] = field(default_factory=list)
    
    # === MEDIUM PRIORITY CONTEXT ===
    location_atmosphere: str = "neutral"
    social_atmosphere: str = "neutral"
    time_of_day: str = "unknown"
    weather: str = "unknown"
    season: str = "unknown"
    
    # === LOW PRIORITY CONTEXT ===
    ambient_sounds: List[str] = field(default_factory=list)
    ambient_smells: List[str] = field(default_factory=list)
    lighting_conditions: str = "normal"
    temperature: str = "comfortable"
    
    # === NARRATIVE STATE ===
    narrative_mode: str = "roam"
    narrative_tone: str = "calm"
    turns_in_current_mode: int = 0
    last_mode_change: str = ""
    
    # === USER STATE ===
    user_last_action: str = ""
    user_last_intent: str = ""
    user_intent_confidence: float = 0.0
    user_current_goal: str = ""
    user_current_task: str = ""
    
    # === METADATA ===
    last_updated: str = ""
    update_count: int = 0
    context_version: str = "1.1"
    
    # === WORLD STATE ===
    # Map of location_label -> { 'present_nuas': [], 'scene_description': '', 'atmosphere': '' }
    location_states: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    
    # === TRAVEL STATE ===
    # { "destination": str, "total_segments": int, "current_segment": int, "segment_duration": int, "total_minutes": int }
    active_journey: Optional[Dict[str, Any]] = None

    # === INTERNAL VOICE TRACKING ===
    # Recent internal voice lines for debugging continuity contradictions.
    # Each entry: {"voice": str, "user_action": str, "timestamp": str}
    recent_internal_voices: List[Dict[str, Any]] = field(default_factory=list)

    # === CONTINUITY FACTS (Ground truth anchors) ===
    # List of small, explicit facts to prevent narrative contradictions.
    # Each entry: {"fact": str, "confidence": float (0-1), "source": str, "timestamp": str}
    continuity_facts: List[Dict[str, Any]] = field(default_factory=list)

    mentioned_actors: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PersistentContext':
        """Create from dictionary loaded from JSON"""
        return cls(**data)


class PersistentContextManager:
    """
    Manages persistent context with aggressive saving and loading.
    
    Key Features:
    - Saves after EVERY update
    - Loads on EVERY access
    - Multiple backup files (never lose data)
    - Automatic recovery from corruption
    - Context validation and repair
    """
    
    def __init__(self, storage_dir: str = "simulation_data/context", session_id: str = None):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = session_id or datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # File paths
        self.primary_file = self.storage_dir / f"context_{self.session_id}.json"
        self.backup_file = self.storage_dir / f"context_{self.session_id}_backup.json"
        self.history_dir = self.storage_dir / "history"
        self.history_dir.mkdir(exist_ok=True)
        
        # In-memory context (always synced with disk)
        self.context = PersistentContext(session_id=self.session_id)
        
        # Load existing context if available
        self._load_or_create()
        
        print(f"[CONTEXT] Persistent Context Manager initialized")
        print(f"[CONTEXT] Session ID: {self.session_id}")
        print(f"[CONTEXT] Storage: {self.primary_file}")
    
    def _load_or_create(self):
        """Load existing context or create new one"""
        # Try primary file
        if self.primary_file.exists():
            try:
                with open(self.primary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.context = PersistentContext.from_dict(data)
                    print(f"[CONTEXT] Loaded existing context (v{self.context.context_version})")
                    print(f"[CONTEXT] Location: {self.context.current_location}")
                    print(f"[CONTEXT] NPCs: {', '.join(self.context.present_nuas) if self.context.present_nuas else 'None'}")
                    return
            except Exception as e:
                print(f"[CONTEXT] WARNING: Failed to load primary file: {e}")
        
        # Try backup file
        if self.backup_file.exists():
            try:
                with open(self.backup_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.context = PersistentContext.from_dict(data)
                    print(f"[CONTEXT] Recovered from backup file")
                    self._save(increment_update_count=False)  # Restore primary file
                    return
            except Exception as e:
                print(f"[CONTEXT] WARNING: Failed to load backup file: {e}")
        
        # Create new context
        print(f"[CONTEXT] Creating new context")
        self._save(increment_update_count=False)
    
    def _save(self, increment_update_count: bool = True):
        """Save context to disk IMMEDIATELY"""
        try:
            # Update metadata
            self.context.last_updated = datetime.now().isoformat()
            if increment_update_count:
                self.context.update_count += 1
            
            # Convert to JSON
            data = self.context.to_dict()
            json_str = json.dumps(data, indent=2, ensure_ascii=False)
            
            # Save to primary file
            with open(self.primary_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            # Save to backup file
            with open(self.backup_file, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            # Save to history (every 10 updates)
            if self.context.update_count % 10 == 0:
                history_file = self.history_dir / f"context_{self.session_id}_{self.context.update_count}.json"
                with open(history_file, 'w', encoding='utf-8') as f:
                    f.write(json_str)
            
        except Exception as e:
            print(f"[CONTEXT] ERROR: Failed to save context: {e}")
            raise  # This is critical - we must know if saving fails
    
    def _reload(self):
        """Reload context from disk (in case external changes)"""
        if self.primary_file.exists():
            try:
                with open(self.primary_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.context = PersistentContext.from_dict(data)
            except Exception as e:
                print(f"[CONTEXT] WARNING: Failed to reload: {e}")
    
    # === CRITICAL CONTEXT UPDATES ===
    
    def update_location(self, location: str, scene_description: str, location_label: str = "", 
                        skip_npc_restore: bool = False):
        """Update location - CRITICAL, save immediately
        
        Args:
            location: The new location name
            scene_description: Scene description for the new location
            location_label: Optional label for the location
            skip_npc_restore: If True, don't restore NPCs from saved state (use when regenerating population)
        """
        print(f"[CONTEXT] Updating location: {location}")
        
        # 1. Snapshot current location state before leaving
        # NOTE: Only save if we don't already have a saved state for this location
        # (The NPC list is saved BEFORE clearing in the main loop, so we don't want to overwrite it)
        if self.context.current_location and self.context.current_location != "unknown":
            # Use label if available, else full name
            key = self.context.location_label or self.context.current_location
            
            # Only save if it's a real location AND we don't already have saved NUAs for it
            # (NUAs are saved explicitly before clearing, so don't overwrite with empty list)
            if key and key != "unknown":
                existing_state = self.context.location_states.get(key, {})
                existing_nuas = existing_state.get('present_nuas', [])
                
                # Only update NUAs if we have some to save (don't overwrite with empty)
                nuas_to_save = list(self.context.present_nuas) if self.context.present_nuas else existing_nuas
                
                self.context.location_states[key] = {
                    'present_nuas': nuas_to_save,
                    'scene_description': self.context.current_scene_description,
                    'location_atmosphere': self.context.location_atmosphere,
                    'last_visited': datetime.now().isoformat()
                }
                print(f"[CONTEXT] Saved state for '{key}': {len(nuas_to_save)} NUAs")

        # 2. Switch to new location (save previous for instant return)
        if self.context.current_location and self.context.current_location != "unknown":
            self.context.previous_location = self.context.current_location
            print(f"[CONTEXT] Previous location saved: {self.context.previous_location}")
        self.context.current_location = location
        self.context.location_label = location_label
        
        # 3. Attempt to restore state if visiting a known location
        restore_key = location_label or location
        if restore_key in self.context.location_states:
            saved_state = self.context.location_states[restore_key]
            print(f"[CONTEXT] Restoring state for '{restore_key}'...")
            
            # Restore NUAs (unless skip_npc_restore is True - used when regenerating population)
            if not skip_npc_restore:
                self.context.present_nuas = saved_state.get('present_nuas', [])
            else:
                print(f"[CONTEXT] Skipping NPC restore (regenerating population)")
                self.context.present_nuas = []
            # Restore Atmosphere
            self.context.location_atmosphere = saved_state.get('location_atmosphere', 'neutral')
            # Ideally restore scene description, but the caller usually provides a new one (location move)
            # We'll keep the caller's description unless it's empty
            if not scene_description and saved_state.get('scene_description'):
                 self.context.current_scene_description = saved_state.get('scene_description')
            else:
                 self.context.current_scene_description = scene_description
                 
            print(f"[CONTEXT] Restored {len(self.context.present_nuas)} NUAs")
        else:
            # New location - clear state
            self.context.current_scene_description = scene_description
            self.context.present_nuas = []
            self.context.available_nua_ids = []
            self.context.opportunities = []
            self.context.visible_objects = []
            self.context.accessible_paths = []
        
        self._save()
        print(f"[CONTEXT] ✓ Location saved: {location}")
    
    def update_scene_description(self, scene_description: str):
        """Update scene description - CRITICAL, save immediately"""
        try:
            if scene_description is None:
                scene_description = ""
        except Exception:
            scene_description = ""
        try:
            scene_description = str(scene_description)
        except Exception:
            scene_description = ""
        print(f"[CONTEXT] Updating scene description ({len(scene_description)} chars)")
        self.context.current_scene_description = scene_description
        self._save()
        print(f"[CONTEXT] ✓ Scene description saved")
    
    def set_nuas(self, nua_names: List[str], nua_ids: List[str] = None):
        """Set current NUAs (Non-User Actors) - CRITICAL, save immediately"""
        print(f"[CONTEXT] Setting NUAs: {', '.join(nua_names) if nua_names else 'None'}")
        self.context.present_nuas = nua_names
        self.context.available_nua_ids = nua_ids or []
        self._save()
        print(f"[CONTEXT] ✓ NUAs saved: {len(nua_names)} present")
    
    def add_nua(self, nua_name: str, nua_id: str = None):
        """Add NUA (Non-User Actor) to scene - CRITICAL, save immediately"""
        if nua_name not in self.context.present_nuas:
            print(f"[CONTEXT] Adding NUA: {nua_name}")
            self.context.present_nuas.append(nua_name)
            if nua_id:
                self.context.available_nua_ids.append(nua_id)
            self._save()
            print(f"[CONTEXT] ✓ NUA added: {nua_name}")
    
    def remove_nua(self, nua_name: str):
        """Remove NUA (Non-User Actor) from scene - CRITICAL, save immediately"""
        if nua_name in self.context.present_nuas:
            print(f"[CONTEXT] Removing NUA: {nua_name}")
            self.context.present_nuas.remove(nua_name)
            self._save()
            print(f"[CONTEXT] ✓ NUA removed: {nua_name}")
    
    # === HIGH PRIORITY CONTEXT UPDATES ===
    
    def add_event(self, event: str):
        """Add event to history - HIGH priority, save immediately"""
        self.context.recent_events.append(event)
        # Keep only last 10 events
        self.context.recent_events = self.context.recent_events[-10:]
        self._save()
    
    def add_narrative(self, narrative: str):
        """Add narrative to history - HIGH priority, save immediately"""
        self.context.recent_narratives.append(narrative)
        # Keep only last 5 narratives
        self.context.recent_narratives = self.context.recent_narratives[-5:]
        self._save()
    
    def set_opportunities(self, opportunities: List[str]):
        """Set available opportunities - HIGH priority"""
        self.context.opportunities = opportunities
        self._save()
    
    def set_visible_inuas(self, inua_names: List[str]):
        """Set visible INUAs (Inanimate Non-User Actors) - HIGH priority"""
        self.context.visible_objects = inua_names
        self._save()
    
    def set_accessible_paths(self, paths: List[str]):
        """Set accessible paths - HIGH priority"""
        self.context.accessible_paths = paths
        self._save()
    
    def add_unresolved_thread(self, thread: str):
        """Add unresolved thread"""
        if thread not in self.context.unresolved_threads:
            self.context.unresolved_threads.append(thread)
            self._save()
    
    def resolve_thread(self, thread: str):
        """Mark thread as resolved"""
        if thread in self.context.unresolved_threads:
            self.context.unresolved_threads.remove(thread)
            self._save()
    
    # === MEDIUM PRIORITY CONTEXT UPDATES ===
    
    def update_atmosphere(self, location_atmosphere: str = None, social_atmosphere: str = None):
        """Update atmosphere"""
        if location_atmosphere:
            self.context.location_atmosphere = location_atmosphere
        if social_atmosphere:
            self.context.social_atmosphere = social_atmosphere
        self._save()
    
    def update_time_context(self, time_of_day: str = None, weather: str = None, season: str = None):
        """Update time/weather context"""
        if time_of_day:
            self.context.time_of_day = time_of_day
        if weather:
            self.context.weather = weather
        if season:
            self.context.season = season
        self._save()
    
    # === NARRATIVE STATE UPDATES ===
    
    def update_narrative_mode(self, mode: str, tone: str = None):
        """Update narrative mode and tone"""
        if self.context.narrative_mode != mode:
            self.context.last_mode_change = f"{self.context.narrative_mode} → {mode}"
            self.context.narrative_mode = mode
            self.context.turns_in_current_mode = 0
        else:
            self.context.turns_in_current_mode += 1
        
        if tone:
            self.context.narrative_tone = tone
        
        self._save()
    
    # === USER STATE UPDATES ===
    
    def update_user_action(self, action: str, intent: str = None, confidence: float = 0.0):
        """Update user's last action and intent"""
        self.context.user_last_action = action
        if intent:
            self.context.user_last_intent = intent
            self.context.user_intent_confidence = confidence
        self._save()
    
    def update_user_goal(self, goal: str):
        """Update user's current goal"""
        self.context.user_current_goal = goal
        self._save()
    
    def update_user_task(self, task: str):
        """Update user's current task"""
        self.context.user_current_task = task
        self._save()
    
    # === CONTEXT RETRIEVAL ===
    
    def get_context(self) -> PersistentContext:
        """Get current context (always fresh from disk)"""
        self._reload()
        return self.context
    
    def get_location(self) -> str:
        """Get current location"""
        self._reload()
        return self.context.current_location
    
    def get_scene_description(self) -> str:
        """Get current scene description"""
        self._reload()
        return self.context.current_scene_description
    
    def get_nuas(self) -> List[str]:
        """Get current NUAs (Non-User Actors)"""
        self._reload()
        return self.context.present_nuas
    
    def get_recent_events(self, count: int = 5) -> List[str]:
        """Get recent events"""
        self._reload()
        return self.context.recent_events[-count:]
    
    def get_recent_narratives(self, count: int = 3) -> List[str]:
        """Get recent narratives"""
        self._reload()
        return self.context.recent_narratives[-count:]
    
    def get_context_summary(self) -> str:
        """Get human-readable context summary"""
        self._reload()
        c = self.context
        
        summary = f"""
=== CURRENT CONTEXT ===
Location: {c.current_location}
NUAs Present: {', '.join(c.present_nuas) if c.present_nuas else 'None'}
Visible INUAs: {', '.join(c.visible_objects) if c.visible_objects else 'None'}
Atmosphere: {c.location_atmosphere}
Time: {c.time_of_day}, {c.weather}
Mode: {c.narrative_mode} ({c.narrative_tone})

Recent Events:
{chr(10).join(f'  - {e}' for e in c.recent_events[-3:])}

Opportunities:
{chr(10).join(f'  - {o}' for o in c.opportunities)}

Last Updated: {c.last_updated}
Updates: {c.update_count}
"""
        return summary
    
    def get_context_for_llm(self) -> str:
        """Get context formatted for LLM prompts"""
        self._reload()
        c = self.context

        facts_block = ""
        try:
            facts_block = self.get_continuity_facts_for_llm(max_facts=8)
        except Exception:
            facts_block = ""

        mentioned_block = ""
        try:
            mentioned_block = self.get_mentioned_actors_for_llm(max_items=10)
        except Exception:
            mentioned_block = ""
        
        context_text = f"""
**CURRENT CONTEXT (NEVER FORGET THIS):**

**Location:** {c.current_location}
**Scene:** {c.current_scene_description[:500]}...

**Present NUAs (Non-User Actors):** {', '.join(c.present_nuas) if c.present_nuas else 'None'}
**Visible INUAs (Inanimate Non-User Actors):** {', '.join(c.visible_objects) if c.visible_objects else 'None'}
**Atmosphere:** {c.location_atmosphere}
**Time:** {c.time_of_day}, {c.weather}

**Recent Events:**
{chr(10).join(f'- {e}' for e in c.recent_events[-3:])}

**Available Opportunities:**
{chr(10).join(f'- {o}' for o in c.opportunities)}

**User's Last Action:** {c.user_last_action}
**User's Intent:** {c.user_last_intent} (confidence: {c.user_intent_confidence:.1f})
**User's Current Goal:** {c.user_current_goal}
**User's Current Task:** {c.user_current_task}

{facts_block}

{mentioned_block}

**CRITICAL: Use this context for ALL responses. Do not revert to initial scene.**
"""
        return context_text

    def add_continuity_fact(self, fact: str, *, confidence: float = 0.7, source: str = "system") -> None:
        """Add a single continuity fact to persistent context.

        Facts are short anchors (e.g., "Matteo was last seen near the archive").
        Higher confidence means the narrator/internal voice may state it directly.
        Lower confidence means it must be framed as uncertain.
        """
        try:
            f = str(fact or '').strip()
            if not f:
                return

            try:
                conf = float(confidence)
            except Exception:
                conf = 0.7
            conf = max(0.0, min(1.0, conf))

            now = datetime.now().isoformat()
            entry = {
                'fact': f,
                'confidence': conf,
                'source': str(source or 'system'),
                'timestamp': now,
            }

            # De-dupe by exact fact text
            existing = []
            try:
                existing = list(self.context.continuity_facts or [])
            except Exception:
                existing = []
            existing = [e for e in existing if isinstance(e, dict) and str(e.get('fact', '')).strip()]
            if any(str(e.get('fact', '')).strip().lower() == f.lower() for e in existing):
                return

            existing.append(entry)
            # Keep the most recent N facts
            self.context.continuity_facts = existing[-25:]
            self._save()
        except Exception:
            return

    def get_continuity_facts_for_llm(self, max_facts: int = 8) -> str:
        """Return a formatted continuity facts block for prompt grounding."""
        self._reload()
        facts = []
        try:
            facts = list(self.context.continuity_facts or [])
        except Exception:
            facts = []
        facts = [f for f in facts if isinstance(f, dict) and str(f.get('fact', '')).strip()]
        if not facts:
            return ""

        try:
            # Prefer higher confidence, then most recent
            facts.sort(key=lambda x: (-float(x.get('confidence', 0.0) or 0.0), str(x.get('timestamp', ''))))
        except Exception:
            pass

        lines = []
        for f in facts[:max_facts]:
            txt = str(f.get('fact', '')).strip()
            if not txt:
                continue
            try:
                conf = float(f.get('confidence', 0.0) or 0.0)
            except Exception:
                conf = 0.0
            src = str(f.get('source', '') or '').strip()
            tag = f"conf={conf:.2f}" + (f", src={src}" if src else "")
            lines.append(f"- {txt} ({tag})")

        if not lines:
            return ""
        return "\n".join([
            "**CONTINUITY FACTS (authoritative anchors):**",
            *lines,
            "",
            "**FACT RULE:** Only state a fact as certain if its confidence is high. Otherwise hedge (maybe/might/unclear).",
            "**GROUNDING RULE:** Do NOT invent new supporting details to justify a fact. If a detail is not explicitly in these facts (or clearly present in the current scene / retrieved memories), treat it as unknown and do not state it as true.",
        ])

    def add_mentioned_actor(
        self,
        name: str,
        *,
        source: str = "system",
        location_tags: Optional[List[str]] = None,
        hint: str = "",
    ) -> None:
        try:
            n = str(name or '').strip()
            if not n:
                return
            tags = []
            try:
                tags = [str(t).strip() for t in (location_tags or []) if str(t).strip()]
            except Exception:
                tags = []
            
            # If no tags, infer plausible location from name/role
            # This handles ROLE:father -> 'home', ROLE:guard -> 'police station', etc.
            if not tags:
                nl = n.lower()
                if any(k in nl for k in ['father', 'mother', 'parent', 'sister', 'brother', 'family']):
                    tags.append('home')
                elif any(k in nl for k in ['friend', 'best friend']):
                    tags.append('bar')
                    tags.append('cafe')
                elif any(k in nl for k in ['coffee', 'tea', 'cafe']):
                    tags.append('cafe')
                elif any(k in nl for k in ['read', 'book', 'library', 'scholar']):
                    tags.append('library')
                elif any(k in nl for k in ['guard', 'police', 'cop', 'security']):
                    tags.append('police station')
                elif any(k in nl for k in ['doctor', 'nurse', 'medic']):
                    tags.append('hospital')
                elif any(k in nl for k in ['student', 'teacher', 'professor']):
                    tags.append('school')
                elif any(k in nl for k in ['bartender', 'barkeep', 'drunk']):
                    tags.append('bar')
                elif any(k in nl for k in ['cook', 'chef', 'waiter', 'waitress']):
                    tags.append('restaurant')
                elif any(k in nl for k in ['priest', 'nun', 'monk', 'pastor']):
                    tags.append('church')
                elif any(k in nl for k in ['clerk', 'shopkeeper', 'merchant']):
                    tags.append('market')
                    tags.append('shop')

            # Secondary inference: check hint text for explicit location cues
            # This catches "Sam is at the library" patterns that weren't captured upstream
            if not tags and hint:
                import re
                hint_lower = str(hint or '').lower()
                # Pattern: "at the [location]" or "in the [location]"
                loc_match = re.search(r'(?:at|in)\s+(?:the\s+)?([a-z]+(?:\s+[a-z]+)?)\b', hint_lower)
                if loc_match:
                    inferred_from_hint = loc_match.group(1).strip()
                    # Validate it looks like a location (not a pronoun or verb)
                    non_locations = {'the', 'a', 'an', 'him', 'her', 'them', 'it', 'me', 'us', 'you',
                                     'moment', 'time', 'end', 'start', 'beginning', 'same', 'all'}
                    if inferred_from_hint and inferred_from_hint not in non_locations:
                        tags.append(inferred_from_hint)

            tags = list(dict.fromkeys(tags))

            src = str(source or 'system')
            now = datetime.now().isoformat()
            h = str(hint or '').strip()

            existing = []
            try:
                existing = list(self.context.mentioned_actors or [])
            except Exception:
                existing = []
            existing = [e for e in existing if isinstance(e, dict) and str(e.get('name', '')).strip()]

            idx = None
            for i, e in enumerate(existing):
                try:
                    if str(e.get('name', '')).strip().lower() == n.lower():
                        idx = i
                        break
                except Exception:
                    continue

            if idx is None:
                entry = {
                    'name': n,
                    'sources': [src] if src else [],
                    'location_tags': tags,
                    'hint': h,
                    'timestamp': now,
                }
                existing.append(entry)
            else:
                cur = existing[idx]
                try:
                    sources = list(cur.get('sources') or [])
                except Exception:
                    sources = []
                if src and src not in sources:
                    sources.append(src)

                try:
                    cur_tags = list(cur.get('location_tags') or [])
                except Exception:
                    cur_tags = []
                merged_tags = [str(t).strip() for t in (cur_tags + tags) if str(t).strip()]
                merged_tags = list(dict.fromkeys(merged_tags))

                cur['sources'] = sources
                cur['location_tags'] = merged_tags
                if h and not str(cur.get('hint', '') or '').strip():
                    cur['hint'] = h
                cur['timestamp'] = now
                existing[idx] = cur

            self.context.mentioned_actors = existing[-50:]
            self._save()
        except Exception:
            return

    def get_mentioned_actors(self) -> List[Dict[str, Any]]:
        self._reload()
        try:
            items = list(self.context.mentioned_actors or [])
        except Exception:
            items = []
        items = [e for e in items if isinstance(e, dict) and str(e.get('name', '')).strip()]
        return items

    def get_mentioned_actors_for_llm(self, max_items: int = 10) -> str:
        self._reload()
        items = []
        try:
            items = list(self.context.mentioned_actors or [])
        except Exception:
            items = []
        items = [e for e in items if isinstance(e, dict) and str(e.get('name', '')).strip()]
        if not items:
            return ""

        try:
            items.sort(key=lambda x: str(x.get('timestamp', '')))
        except Exception:
            pass

        lines = []
        for e in items[-max_items:]:
            nm = str(e.get('name', '')).strip()
            if not nm:
                continue
            try:
                tags = list(e.get('location_tags') or [])
            except Exception:
                tags = []
            tags = [str(t).strip() for t in tags if str(t).strip()]
            tags_text = ", ".join(tags) if tags else "unknown"
            lines.append(f"- {nm} (where: {tags_text})")

        if not lines:
            return ""
        return "\n".join([
            "**MENTIONED ACTORS (not currently present; leads to incorporate later):**",
            *lines,
        ])

    def add_internal_voice(self, voice: str, *, user_action: str = "") -> None:
        """Persist an internal voice line for debugging (best-effort)."""
        try:
            v = str(voice or '').strip()
            if not v:
                return
            entry = {
                'voice': v,
                'user_action': str(user_action or '').strip(),
                'timestamp': datetime.now().isoformat(),
            }
            existing = []
            try:
                existing = list(self.context.recent_internal_voices or [])
            except Exception:
                existing = []
            existing = [e for e in existing if isinstance(e, dict) and str(e.get('voice', '')).strip()]
            existing.append(entry)
            self.context.recent_internal_voices = existing[-15:]
            self._save()
        except Exception:
            return

    def get_recent_internal_voices(self, count: int = 5) -> List[Dict[str, Any]]:
        """Return recent internal voice entries."""
        self._reload()
        try:
            items = list(self.context.recent_internal_voices or [])
        except Exception:
            items = []
        items = [e for e in items if isinstance(e, dict) and str(e.get('voice', '')).strip()]
        return items[-count:]
    
    # === VALIDATION & REPAIR ===
    
    def validate_context(self) -> List[str]:
        """Validate context and return list of issues"""
        issues = []
        
        if not self.context.current_location or self.context.current_location == "unknown":
            issues.append("Location is unknown or not set")
        
        if not self.context.current_scene_description:
            issues.append("Scene description is empty")
        
        if self.context.update_count == 0:
            issues.append("Context has never been updated")
        
        return issues
    
    def repair_context(self):
        """Attempt to repair corrupted context"""
        print(f"[CONTEXT] Attempting context repair...")
        
        # Try to load from history
        history_files = sorted(self.history_dir.glob(f"context_{self.session_id}_*.json"))
        if history_files:
            latest_history = history_files[-1]
            try:
                with open(latest_history, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.context = PersistentContext.from_dict(data)
                    self._save()
                    print(f"[CONTEXT] ✓ Repaired from history: {latest_history.name}")
                    return True
            except Exception as e:
                print(f"[CONTEXT] Failed to repair from history: {e}")
        
        print(f"[CONTEXT] ✗ Could not repair context")
        return False
    
    # === DEBUGGING ===
    
    def dump_context(self, filepath: str = None):
        """Dump full context to file for debugging"""
        if not filepath:
            filepath = self.storage_dir / f"context_dump_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.context.to_dict(), f, indent=2, ensure_ascii=False)
        
        print(f"[CONTEXT] Context dumped to: {filepath}")
        return filepath


# === GLOBAL INSTANCE ===
_global_context_manager: Optional[PersistentContextManager] = None


def get_context_manager(session_id: str = None) -> PersistentContextManager:
    """Get or create global context manager.
    
    IMPORTANT: If session_id is provided and differs from the current instance,
    the manager will be reset to use the new session_id. This ensures we always
    use the correct session's context file.
    """
    global _global_context_manager
    
    # If we have an existing manager but with a DIFFERENT session_id, reset it
    if _global_context_manager is not None and session_id is not None:
        if _global_context_manager.session_id != session_id:
            print(f"[CONTEXT] Session ID changed: {_global_context_manager.session_id} → {session_id}")
            print(f"[CONTEXT] Resetting context manager to use correct session")
            _global_context_manager = None
    
    if _global_context_manager is None:
        _global_context_manager = PersistentContextManager(session_id=session_id)
    
    return _global_context_manager


def reset_context_manager():
    """Reset global context manager (for testing)"""
    global _global_context_manager
    _global_context_manager = None


def sync_context_with_tracker(tracker) -> bool:
    """
    Synchronize PersistentContextManager with TrackerAgent data.
    
    This ensures that if the tracker has scene/location data that the context
    manager is missing, we restore it. This is critical for session resumption.
    
    Returns True if sync was successful, False otherwise.
    """
    global _global_context_manager
    
    if _global_context_manager is None:
        print("[CONTEXT SYNC] No context manager to sync")
        return False
    
    if tracker is None:
        print("[CONTEXT SYNC] No tracker to sync from")
        return False
    
    ctx = _global_context_manager.context
    synced = False
    
    try:
        # Sync scene description from tracker if context is empty
        if not ctx.current_scene_description:
            tracker_scene = getattr(tracker, 'current_scene_description', None)
            if not tracker_scene and hasattr(tracker, 'session_data'):
                tracker_scene = tracker.session_data.get('current_scene_description', '')
            
            if tracker_scene:
                ctx.current_scene_description = tracker_scene
                print(f"[CONTEXT SYNC] Restored scene description from tracker ({len(tracker_scene)} chars)")
                synced = True
        
        # Sync location from tracker if context is empty
        if not ctx.current_location or ctx.current_location == "unknown":
            tracker_location = getattr(tracker, 'current_location', None)
            if not tracker_location and hasattr(tracker, 'session_data'):
                tracker_location = tracker.session_data.get('current_location', '')
            
            if tracker_location:
                ctx.current_location = tracker_location
                print(f"[CONTEXT SYNC] Restored location from tracker: {tracker_location}")
                synced = True

        # Derive location from spatial system if still unknown
        if not ctx.current_location or ctx.current_location == "unknown":
            try:
                from spatial_context_system import get_spatial_manager
                session_id = getattr(tracker, 'session_id', None) if tracker else None
                spatial = get_spatial_manager(session_id=session_id)
                spatial_loc = getattr(spatial, 'current_location', None) if spatial else None
                if spatial_loc:
                    ctx.current_location = str(spatial_loc)
                    print(f"[CONTEXT SYNC] Restored location from spatial system: {spatial_loc}")
                    synced = True
            except Exception:
                pass

        # Derive location from world map tracker if still unknown
        if not ctx.current_location or ctx.current_location == "unknown":
            try:
                from location_distance_tracker import get_location_tracker
                session_id = getattr(tracker, 'session_id', None) if tracker else None
                w = get_location_tracker(session_id)
                wl = getattr(w, 'current_location', None) if w else None
                if wl:
                    ctx.current_location = str(wl)
                    print(f"[CONTEXT SYNC] Restored location from world map: {wl}")
                    synced = True
            except Exception:
                pass
        
        # Sync NUAs from tracker if context is empty
        if not ctx.present_nuas:
            tracker_npcs = getattr(tracker, 'available_npcs', None)
            if tracker_npcs:
                npc_names = [getattr(npc, 'name', str(npc)) for npc in tracker_npcs if npc]
                if npc_names:
                    ctx.present_nuas = npc_names
                    print(f"[CONTEXT SYNC] Restored {len(npc_names)} NUAs from tracker")
                    synced = True
        
        if synced:
            _global_context_manager._save()
            print("[CONTEXT SYNC] ✓ Context synchronized and saved")
        else:
            print("[CONTEXT SYNC] No sync needed - context already populated")
        
        return True
        
    except Exception as e:
        print(f"[CONTEXT SYNC] Error during sync: {e}")
        return False


def get_context_health_report() -> dict:
    """
    Generate a health report for the current context state.
    Useful for debugging context issues.
    """
    global _global_context_manager
    
    report = {
        "status": "unknown",
        "issues": [],
        "warnings": [],
        "stats": {}
    }
    
    if _global_context_manager is None:
        report["status"] = "error"
        report["issues"].append("No context manager initialized")
        return report
    
    ctx = _global_context_manager.context
    
    # Check critical fields
    if not ctx.current_location or ctx.current_location == "unknown":
        report["issues"].append("Location is unknown or not set")
    
    if not ctx.current_scene_description:
        report["issues"].append("Scene description is empty")
    elif len(ctx.current_scene_description) < 50:
        report["warnings"].append(f"Scene description is very short ({len(ctx.current_scene_description)} chars)")
    
    if ctx.update_count == 0:
        report["warnings"].append("Context has never been updated")
    
    # Stats
    report["stats"] = {
        "session_id": ctx.session_id,
        "location": ctx.current_location,
        "scene_length": len(ctx.current_scene_description) if ctx.current_scene_description else 0,
        "nuas_present": len(ctx.present_nuas),
        "recent_events": len(ctx.recent_events),
        "recent_narratives": len(ctx.recent_narratives),
        "update_count": ctx.update_count,
        "last_updated": ctx.last_updated,
        "saved_locations": len(ctx.location_states)
    }
    
    # Determine overall status
    if report["issues"]:
        report["status"] = "degraded"
    elif report["warnings"]:
        report["status"] = "warning"
    else:
        report["status"] = "healthy"
    
    return report
