"""
Enhanced Dynamic Actor System for Multi-Actor UTAS Simulation

This system extends the original dynamic actor detection to work seamlessly
with unlimited actors through the MultiActorManager.
"""

import re
from typing import Optional, Dict, Any, List, Tuple, Set
from actors import NonUserActor, InanimateNonUserActor, Actor, UserActor
from agents.creator_agent import CreatorAgent
from multi_actor_manager import MultiActorManager, ActorRole
from color_utils import Color


class EnhancedDynamicActorDetector:
    """
    Enhanced detector for new actor mentions that works with unlimited actors.
    
    Features:
    - Scalable existing actor reference detection
    - Context-aware new actor classification
    - Support for complex multi-actor scenarios
    - Performance optimized for large actor counts
    """
    
    def __init__(self, actor_manager: MultiActorManager):
        self.actor_manager = actor_manager
        
        # Enhanced INUA patterns for better detection
        self.inua_patterns = [
            r'\b(?:pick|hack|break|open|disable|bypass|unlock|force)\s+(?:the\s+)?(\w+(?:\s+\w+)*)',
            r'\b(?:interact|examine|use|manipulate|operate|activate)\s+(?:with\s+)?(?:the\s+)?(\w+(?:\s+\w+)*)',
            r'\b(?:try|attempt)\s+to\s+\w+\s+(?:the\s+)?(\w+(?:\s+\w+)*)',
            r'\b(?:climb|jump\s+over|crawl\s+under|go\s+through)\s+(?:the\s+)?(\w+(?:\s+\w+)*)'
        ]
        
        # Enhanced NUA patterns for better detection
        self.nua_patterns = [
            r'\b(?:talk|speak|converse|approach|ask|tell|greet|address)\s+(?:to\s+)?(?:the\s+)?(\w+(?:\s+\w+)*)',
            r'\b(?:attack|fight|challenge|threaten|intimidate)\s+(?:the\s+)?(\w+(?:\s+\w+)*)',
            r'\b(?:follow|chase|pursue|track)\s+(?:the\s+)?(\w+(?:\s+\w+)*)',
            r'\b(?:help|assist|aid|support)\s+(?:the\s+)?(\w+(?:\s+\w+)*)'
        ]
        
        # Expanded INUA keywords
        self.inua_keywords = {
            # Security & Access
            'lock', 'door', 'gate', 'barrier', 'wall', 'fence', 'checkpoint',
            # Technology
            'terminal', 'computer', 'machine', 'device', 'system', 'console',
            'panel', 'keypad', 'scanner', 'sensor', 'camera', 'monitor',
            # Furniture & Objects
            'stool', 'chair', 'table', 'desk', 'counter', 'bar', 'shelf',
            'cabinet', 'drawer', 'box', 'container', 'barrel', 'crate',
            'chest', 'safe', 'vault', 'locker',
            # Mechanisms & Traps
            'mechanism', 'trap', 'puzzle', 'lever', 'switch', 'button',
            'wheel', 'handle', 'knob', 'dial',
            # Vehicles & Transport
            'car', 'truck', 'vehicle', 'bike', 'motorcycle', 'boat', 'ship',
            # Environmental
            'fire', 'water', 'cliff', 'pit', 'hole', 'bridge', 'ladder'
        }
        
        # Expanded NUA keywords
        self.nua_keywords = {
            # Generic People
            'guard', 'merchant', 'stranger', 'person', 'people', 'individual',
            'character', 'someone', 'anyone', 'everybody', 'nobody', 'citizen',
            # Occupations
            'soldier', 'officer', 'clerk', 'assistant', 'worker', 'employee',
            'doctor', 'nurse', 'teacher', 'student', 'pilot', 'driver',
            'bartender', 'waiter', 'chef', 'cook', 'janitor', 'cleaner',
            # Authority Figures
            'captain', 'commander', 'sergeant', 'lieutenant', 'chief',
            'supervisor', 'manager', 'boss', 'leader', 'director',
            # Specialists
            'technician', 'engineer', 'scientist', 'researcher', 'analyst',
            'hacker', 'spy', 'agent', 'operative', 'specialist'
        }
        
        # Performance optimization
        self._existing_actor_cache = {}
        self._cache_valid = False
    
    def detect_existing_actor_reference(self, user_input: str, existing_actors: list = None) -> Optional[Dict[str, Any]]:
        """
        Detect if user input refers to an existing actor.
        
        Args:
            user_input: The user's input text
            existing_actors: Legacy parameter for compatibility (ignored - uses actor_manager)
            
        Returns:
            Dict with existing actor info if found, None otherwise
        """
        user_input_lower = user_input.lower()
        
        # Get all actors from manager
        all_actors = self.actor_manager.get_all_actors()
        
        if not all_actors:
            return None
        
        # Check for direct name matches first (most reliable)
        for actor in all_actors:
            actor_name_lower = actor.sheet.name.lower()
            
            # Exact name match
            if actor_name_lower in user_input_lower:
                return {
                    'existing_actor': actor,
                    'reference_type': 'direct_name',
                    'type': self._classify_actor_type(actor),
                    'confidence': 'high'
                }
        
        # Check for OCCUPATION matches (e.g., "the waitress", "the guard", "the cook")
        for actor in all_actors:
            if hasattr(actor, 'sheet') and hasattr(actor.sheet, 'occupation'):
                occupation = actor.sheet.occupation.lower() if actor.sheet.occupation else ''
                if occupation and len(occupation) > 2:
                    # Check for occupation reference patterns
                    occupation_patterns = [
                        rf'\b(?:the|a|that)\s+{re.escape(occupation)}\b',
                        rf'\b{re.escape(occupation)}\b',
                    ]
                    # Also check singular/plural variations
                    if occupation.endswith('s'):
                        occupation_patterns.append(rf'\b(?:the|a|that)\s+{re.escape(occupation[:-1])}\b')
                    else:
                        occupation_patterns.append(rf'\b(?:the|a|that)\s+{re.escape(occupation)}s?\b')
                    
                    for pattern in occupation_patterns:
                        if re.search(pattern, user_input_lower):
                            print(f"[DYNAMIC ACTOR] Found existing {actor.sheet.name} by occupation '{occupation}'")
                            return {
                                'existing_actor': actor,
                                'reference_type': 'occupation_match',
                                'type': self._classify_actor_type(actor),
                                'confidence': 'high',
                                'matched_occupation': occupation
                            }
        
        # Check for partial name matches with context
        for actor in all_actors:
            name_words = actor.sheet.name.lower().split()
            
            for word in name_words:
                if len(word) > 3:  # Only check meaningful words
                    # Look for contextual references like "talk to guard" when "Security Guard" exists
                    patterns = [
                        rf'\b(?:talk\s+to|speak\s+with|approach|address)\s+(?:the\s+)?{re.escape(word)}\b',
                        rf'\b(?:attack|fight|challenge)\s+(?:the\s+)?{re.escape(word)}\b',
                        rf'\b(?:follow|chase|help)\s+(?:the\s+)?{re.escape(word)}\b',
                        rf'\b(?:interact\s+with|use|examine)\s+(?:the\s+)?{re.escape(word)}\b'
                    ]
                    
                    for pattern in patterns:
                        if re.search(pattern, user_input_lower):
                            return {
                                'existing_actor': actor,
                                'reference_type': 'contextual_partial',
                                'type': self._classify_actor_type(actor),
                                'confidence': 'medium',
                                'matched_word': word
                            }
        
        return None
    
    def detect_new_actor_mention(self, user_input: str, existing_actors: list = None) -> Optional[Dict[str, Any]]:
        """
        Detect mentions of new actors that should be created.
        
        Args:
            user_input: The user's input text
            existing_actors: Legacy parameter for compatibility (ignored - uses actor_manager)
            
        Returns:
            Dict with new actor info if detected, None otherwise
        """
        user_input_lower = user_input.lower()
        
        # First check if this might be referring to an existing actor
        existing_ref = self.detect_existing_actor_reference(user_input)
        if existing_ref:
            return None  # Don't create new actor if existing one matches
        
        # Check for INUA patterns
        inua_detection = self._detect_inua_mention(user_input_lower)
        if inua_detection:
            return inua_detection
        
        # Check for NUA patterns
        nua_detection = self._detect_nua_mention(user_input_lower)
        if nua_detection:
            return nua_detection
        
        return None
    
    def _detect_inua_mention(self, user_input_lower: str) -> Optional[Dict[str, Any]]:
        """Detect INUA (object/mechanism) mentions."""
        # Check keyword-based detection first
        for keyword in self.inua_keywords:
            if keyword in user_input_lower:
                # Extract potential name from context
                name = self._extract_inua_name(user_input_lower, keyword)
                return {
                    'type': 'INUA',
                    'name': name,
                    'detection_method': 'keyword',
                    'keyword': keyword,
                    'confidence': 'high'
                }
        
        # Check pattern-based detection
        for pattern in self.inua_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                potential_name = match.group(1) if match.groups() else "Unknown Object"
                
                # Validate that this looks like an object name
                if self._validate_inua_name(potential_name):
                    return {
                        'type': 'INUA',
                        'name': potential_name.title(),
                        'detection_method': 'pattern',
                        'pattern': pattern,
                        'confidence': 'medium'
                    }
        
        return None
    
    def _detect_nua_mention(self, user_input_lower: str) -> Optional[Dict[str, Any]]:
        """Detect NUA (character) mentions."""
        # Check keyword-based detection first
        for keyword in self.nua_keywords:
            if keyword in user_input_lower:
                # Extract potential name from context
                name = self._extract_nua_name(user_input_lower, keyword)
                return {
                    'type': 'NUA',
                    'name': name,
                    'detection_method': 'keyword',
                    'keyword': keyword,
                    'confidence': 'high'
                }
        
        # Check pattern-based detection
        for pattern in self.nua_patterns:
            match = re.search(pattern, user_input_lower)
            if match:
                potential_name = match.group(1) if match.groups() else "Unknown Person"
                
                # Validate that this looks like a person name
                if self._validate_nua_name(potential_name):
                    return {
                        'type': 'NUA',
                        'name': potential_name.title(),
                        'detection_method': 'pattern',
                        'pattern': pattern,
                        'confidence': 'medium'
                    }
        
        return None
    
    def _extract_inua_name(self, user_input_lower: str, keyword: str) -> str:
        """Extract a meaningful name for an INUA based on context."""
        # Look for descriptive words before the keyword
        pattern = rf'(?:the\s+)?(\w+\s+)?{re.escape(keyword)}'
        match = re.search(pattern, user_input_lower)
        
        if match and match.group(1):
            descriptor = match.group(1).strip()
            return f"{descriptor.title()} {keyword.title()}"
        else:
            return keyword.title()
    
    def _extract_nua_name(self, user_input_lower: str, keyword: str) -> str:
        """Extract a meaningful name for a NUA based on context."""
        # Look for descriptive words before the keyword
        pattern = rf'(?:the\s+)?(\w+\s+)?{re.escape(keyword)}'
        match = re.search(pattern, user_input_lower)
        
        if match and match.group(1):
            descriptor = match.group(1).strip()
            return f"{descriptor.title()} {keyword.title()}"
        else:
            return keyword.title()
    
    def _validate_inua_name(self, name: str) -> bool:
        """Validate that a detected name is appropriate for an INUA."""
        name_lower = name.lower()
        
        # Reject if it contains person-like words
        person_words = {'person', 'people', 'someone', 'anyone', 'he', 'she', 'they', 'him', 'her', 'them'}
        if any(word in name_lower for word in person_words):
            return False
        
        # Reject very short or generic names
        if len(name.strip()) < 3:
            return False
        
        return True
    
    def _validate_nua_name(self, name: str) -> bool:
        """Validate that a detected name is appropriate for a NUA."""
        name_lower = name.lower()
        
        # Reject if it contains object-like words
        object_words = {'door', 'lock', 'terminal', 'computer', 'machine', 'device', 'system'}
        if any(word in name_lower for word in object_words):
            return False
        
        # Reject very short or generic names
        if len(name.strip()) < 3:
            return False
        
        return True
    
    def _classify_actor_type(self, actor: Actor) -> str:
        """Classify an actor's type for reporting."""
        if isinstance(actor, UserActor):
            return "USER"
        elif isinstance(actor, InanimateNonUserActor):
            return "INUA"
        elif isinstance(actor, NonUserActor):
            return "NUA"
        else:
            return "UNKNOWN"
    
    def get_detection_statistics(self) -> Dict[str, Any]:
        """Get statistics about actor detection performance."""
        all_actors = self.actor_manager.get_all_actors()
        
        stats = {
            'total_actors': len(all_actors),
            'user_actors': len([a for a in all_actors if isinstance(a, UserActor)]),
            'nuas': len([a for a in all_actors if isinstance(a, NonUserActor) and not isinstance(a, InanimateNonUserActor)]),
            'inuas': len([a for a in all_actors if isinstance(a, InanimateNonUserActor)]),
            'active_actors': len(self.actor_manager.get_active_actors()),
            'inua_keywords_count': len(self.inua_keywords),
            'nua_keywords_count': len(self.nua_keywords)
        }
        
        return stats


class EnhancedDynamicActorSystem:
    """
    Enhanced system that coordinates actor detection and creation for unlimited actors.
    
    Features:
    - Seamless integration with MultiActorManager
    - Intelligent actor role assignment
    - Context-aware actor activation/deactivation
    - Performance optimized for large actor counts
    """
    
    def __init__(self, creator_agent: CreatorAgent, actor_manager: MultiActorManager):
        self.creator = creator_agent
        self.actor_manager = actor_manager
        self.detector = EnhancedDynamicActorDetector(actor_manager)
        
        # Creation statistics
        self.creation_stats = {
            'total_created': 0,
            'nuas_created': 0,
            'inuas_created': 0,
            'creation_failures': 0
        }
    
    def process_user_input(self, user_input: str, scene_description: str) -> Dict[str, Any]:
        """
        Process user input for actor references and creation needs.
        
        Args:
            user_input: The user's input text
            scene_description: Current scene description for context
            
        Returns:
            Dict containing processing results and any new actors created
        """
        result = {
            'existing_reference': None,
            'new_actor_created': None,
            'target_actor': None,
            'action_type': 'no_actor_interaction'
        }
        
        # First check for existing actor references
        existing_ref = self.detector.detect_existing_actor_reference(user_input)
        if existing_ref:
            result['existing_reference'] = existing_ref
            result['target_actor'] = existing_ref['existing_actor']
            result['action_type'] = 'existing_actor_interaction'
            
            # Ensure the referenced actor is active
            actor_id = self.actor_manager.get_actor_id_by_name(existing_ref['existing_actor'].sheet.name)
            if actor_id:
                self.actor_manager.activate_actor(actor_id)
            
            return result
        
        # Check for new actor mentions
        new_actor_info = self.detector.detect_new_actor_mention(user_input)
        if new_actor_info:
            new_actor = self.create_dynamic_actor(new_actor_info, scene_description)
            if new_actor:
                result['new_actor_created'] = new_actor
                result['target_actor'] = new_actor
                result['action_type'] = 'new_actor_interaction'
                
                # Add to actor manager with appropriate role
                role = ActorRole.SCENE_PRIMARY if new_actor_info['confidence'] == 'high' else ActorRole.SCENE_SECONDARY
                self.actor_manager.add_actor(new_actor, role)
        
        return result
    
    def create_dynamic_actor(self, actor_info: Dict[str, Any], scene_description: str) -> Optional[Actor]:
        """
        Create a new actor based on detection info.
        
        Args:
            actor_info: Information about the actor to create
            scene_description: Current scene context
            
        Returns:
            Created actor or None if creation failed
        """
        try:
            actor_type = actor_info['type']
            actor_name = actor_info['name']
            
            print(f"{Color.INFO}🎭 Creating {actor_type}: {actor_name}...{Color.RESET}")
            
            # Create the actor using the existing creator agent
            new_actor = self.creator.create_dynamic_actor(actor_info, scene_description, self.actor_manager)
            
            if new_actor:
                self.creation_stats['total_created'] += 1
                if actor_type == 'NUA':
                    self.creation_stats['nuas_created'] += 1
                elif actor_type == 'INUA':
                    self.creation_stats['inuas_created'] += 1
                
                print(f"{Color.SUCCESS}✓ Successfully created {actor_name}{Color.RESET}")
                return new_actor
            else:
                self.creation_stats['creation_failures'] += 1
                print(f"{Color.ERROR}✗ Failed to create {actor_name}{Color.RESET}")
                return None
                
        except Exception as e:
            self.creation_stats['creation_failures'] += 1
            print(f"{Color.ERROR}✗ Error creating actor: {e}{Color.RESET}")
            return None
    
    def get_system_statistics(self) -> Dict[str, Any]:
        """Get comprehensive system statistics."""
        detection_stats = self.detector.get_detection_statistics()
        
        return {
            'detection': detection_stats,
            'creation': self.creation_stats.copy(),
            'actor_manager': self.actor_manager.get_simulation_summary()
        }
    
    def display_system_status(self):
        """Display current system status for debugging."""
        stats = self.get_system_statistics()
        
        print(f"\n{Color.SYSTEM}=== DYNAMIC ACTOR SYSTEM STATUS ==={Color.RESET}")
        
        print(f"\n{Color.INFO}Detection Statistics:{Color.RESET}")
        detection = stats['detection']
        print(f"  Total Actors: {detection['total_actors']}")
        print(f"  Active Actors: {detection['active_actors']}")
        print(f"  NUAs: {detection['nuas']}")
        print(f"  INUAs: {detection['inuas']}")
        
        print(f"\n{Color.INFO}Creation Statistics:{Color.RESET}")
        creation = stats['creation']
        print(f"  Total Created: {creation['total_created']}")
        print(f"  NUAs Created: {creation['nuas_created']}")
        print(f"  INUAs Created: {creation['inuas_created']}")
        print(f"  Creation Failures: {creation['creation_failures']}")
        
        if creation['total_created'] > 0:
            success_rate = ((creation['total_created'] - creation['creation_failures']) / 
                          (creation['total_created'] + creation['creation_failures'])) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
