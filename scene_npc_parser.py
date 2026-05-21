"""
Scene NPC Parser

Automatically detects and extracts named NPCs from scene descriptions
to maintain narrative continuity.
"""

import re
from typing import List, Dict, Any, Optional
from openrouter_config import OpenRouterConfig, retry_with_backoff, RetryConfig, robust_llm_call
from json_utils import extract_and_parse_json


class SceneNPCParser:
    """Parses scene descriptions to detect mentioned NPCs."""

    def __init__(self, mention_system=None):
        self.llm_client = OpenRouterConfig.create_client()
        self.mention_system = mention_system  # For actor mention tracking

    def _validate_spawn_against_mentions(self, actor_name: str, current_location: str) -> tuple[bool, str]:
        """
        Validate that spawning an actor doesn't contradict recent mentions.

        Args:
            actor_name: Name of actor to spawn
            current_location: Location where actor would be spawned

        Returns:
            Tuple of (should_spawn: bool, reason: str)
        """
        if not self.mention_system:
            return True, "No mention system available"

        try:
            # Get last known location from mention history
            last_location, confidence = self.mention_system.get_last_known_location(actor_name)

            if not last_location:
                # No mention history - safe to spawn
                return True, f"No mention history for {actor_name}"

            # If last mention was at current location, spawning is consistent
            if last_location == current_location:
                return True, f"{actor_name} last mentioned at {current_location} - consistent"

            # Check if actor was mentioned as departing
            from mention_system import MentionType
            recent_mentions = self.mention_system.query_mentions(
                actor_name=actor_name,
                limit=5
            )

            # Check for recent DEPARTING mentions
            for mention in recent_mentions:
                if mention.mention_type == MentionType.DEPARTING:
                    # Actor was mentioned leaving - safe to spawn elsewhere
                    return True, f"{actor_name} mentioned departing - can spawn at {current_location}"

            # Check for recent ARRIVING mentions at current location
            for mention in recent_mentions:
                if mention.mention_type == MentionType.ARRIVING:
                    if mention.destination == current_location:
                        return True, f"{actor_name} mentioned arriving at {current_location} - consistent"

            # Actor has conflicting location - shouldn't spawn
            from mention_system import PresenceConfidence
            if confidence in (PresenceConfidence.CONFIRMED, PresenceConfidence.HIGH):
                return False, f"{actor_name} recently mentioned at {last_location} (confidence: {confidence.value}) - conflict with spawn at {current_location}"

            # Low confidence mention - allow spawn but log warning
            return True, f"{actor_name} has low-confidence mention at {last_location} - allowing spawn at {current_location}"

        except Exception as e:
            print(f"[NPC PARSER] Error validating spawn against mentions: {e}")
            return True, f"Error checking mentions: {e}"

    def _check_actor_recently_mentioned(self, actor_name: str, max_turns: int = 10) -> bool:
        """
        Check if actor was mentioned in recent turns.

        Args:
            actor_name: Name of actor to check
            max_turns: Maximum number of turns to look back

        Returns:
            True if actor was mentioned recently, False otherwise
        """
        if not self.mention_system:
            return False

        try:
            recent_mentions = self.mention_system.query_mentions(
                actor_name=actor_name,
                limit=max_turns
            )
            return len(recent_mentions) > 0
        except Exception as e:
            print(f"[NPC PARSER] Error checking recent mentions: {e}")
            return False

    def extract_npcs_from_scene(self, scene_description: str) -> List[Dict[str, Any]]:
        """
        Extract named NPCs mentioned in a scene description.
        
        Args:
            scene_description: The narrative scene description
            
        Returns:
            List of dicts with NPC details: name, role, description
        """
        if not scene_description or len(scene_description.strip()) < 20:
            return []
        
        # Use LLM to intelligently extract NPCs
        prompt = f"""Analyze this scene description and extract any actors who are PHYSICALLY PRESENT in the scene.

Scene Description:
{scene_description}

**CRITICAL: Only extract NPCs who are PHYSICALLY PRESENT in the scene right now.**

Look for:
1. **Named actors** who are physically present ("Linda the waitress approaches", "Marcus sits at the bar")
2. **Generic role-based actors** who are clearly present and interactable ("a cab driver", "the bartender", "a security guard")
3. Actors the User Actor can see/interact with directly
4. People operating vehicles or machines mentioned in the scene ("a yellow cab" → extract "cab driver")

DO NOT extract:
- Actors mentioned in messages, phone calls, or letters ("a message from John")
- Actors mentioned in conversation ("I heard about Marcus")
- Actors from memories or backstory ("I remember Linda")
- Actors who are elsewhere ("John is at work downtown")
- The protagonist/player actor
- Pure background atmosphere (crowds, distant people with no interaction potential)

**Examples:**
✅ EXTRACT: "Linda the waitress approaches your table" → Extract as "Linda" (named, role: waitress)
✅ EXTRACT: "A man named Marcus sits at the bar" → Extract as "Marcus" (named, role: patron)
✅ EXTRACT: "A yellow cab idles at the curb" → Extract as "Cab Driver" (generic, role: cab driver)
✅ EXTRACT: "The bartender wipes down the counter" → Extract as "Bartender" (generic, role: bartender)
✅ EXTRACT: "A security guard stands by the door" → Extract as "Security Guard" (generic, role: security guard)
❌ DON'T EXTRACT: "You notice a message from Linda on the answering machine" → Linda is NOT present
❌ DON'T EXTRACT: "You remember Marcus mentioning this place" → Marcus is NOT present
❌ DON'T EXTRACT: "The letter from Officer Chen sits on the table" → Officer Chen is NOT present
❌ DON'T EXTRACT: "The restaurant is crowded with people" → Too vague, no specific interaction potential

**For generic NPCs without names:**
- Use their role as the name (e.g., "Cab Driver", "Bartender", "Security Guard")
- Capitalize the role to make it a proper name
- Include enough detail to make them interactable

Respond with JSON:
{{
    "npcs": [
        {{
            "name": "Full name OR role-based name (e.g., 'Linda' or 'Cab Driver')",
            "role": "Their role/occupation (e.g., 'waitress', 'bartender', 'cab driver', 'security guard')",
            "description": "Brief physical/personality description from the scene",
            "context": "What they're doing in the scene RIGHT NOW"
        }}
    ]
}}

If no physically present NPCs are found, return: {{"npcs": []}}
"""
        
        try:
            print(f"[NPC PARSER] Calling LLM to extract NPCs from scene...")
            # Use centralized robust LLM call
            response_content = robust_llm_call(
                client=self.llm_client,
                messages=[{"role": "user", "content": prompt}],
                model=OpenRouterConfig.get_model_for_role("coordination"),
                temperature=0.2,
                max_tokens=500,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="NPC PARSER"
            )
            
            if not response_content:
                print(f"[NPC PARSER] Empty response from LLM")
                return []
            
            print(f"[NPC PARSER] LLM response received: {len(response_content)} characters")
            
            # Extract JSON from response
            result = extract_and_parse_json(response_content)
            
            if result and "npcs" in result:
                npcs = result["npcs"]
                print(f"[NPC PARSER] Raw NPC count from LLM: {len(npcs)}")
                # Filter out empty or invalid entries
                valid_npcs = [
                    npc for npc in npcs 
                    if npc.get("name") and len(npc["name"].strip()) > 0
                ]
                print(f"[NPC PARSER] Valid NPC count after filtering: {len(valid_npcs)}")
                if valid_npcs:
                    for npc in valid_npcs:
                        try:
                            role = (npc.get('role') or '').strip()
                        except Exception:
                            role = ''
                        safe_label = role.title() if role else "Someone"
                        print(f"[NPC PARSER]   - {safe_label}")
                return valid_npcs
            else:
                print(f"[NPC PARSER] No 'npcs' field in LLM response")
            
        except Exception as e:
            print(f"[NPC PARSER] Error extracting NPCs: {e}")
            import traceback
            print(f"[NPC PARSER] Traceback: {traceback.format_exc()}")
        
        return []
    
    def extract_npc_details_for_generation(self, npc_data: Dict[str, Any], scene_description: str) -> str:
        """
        Create a detailed prompt for NPC generation based on scene context.
        
        Args:
            npc_data: Dict with name, role, description, context
            scene_description: Full scene description for context
            
        Returns:
            Prompt string for CreatorAgent
        """
        name = npc_data.get("name", "Unknown")
        role = npc_data.get("role", "person")
        description = npc_data.get("description", "")
        context = npc_data.get("context", "")
        
        # Infer relationship context based on role
        relationship_note = self._infer_relationship_context(role)
        
        prompt = f"""Create an NUA named {name} who is a {role}.

Scene Context: {scene_description[:400]}

Actor Details:
- Name: {name}
- Role: {role}
- Appearance/Demeanor: {description}
- Current Activity: {context}

{relationship_note}

Ensure S-factors and skills align with their role as a {role}. 
Make them feel like a natural part of this scene."""
        
        return prompt
    
    def _infer_relationship_context(self, role: str) -> str:
        """
        Use LLM to infer the relationship context between the NPC and user based on role.
        
        Args:
            role: The NPC's role (e.g., 'waitress', 'bartender', 'security guard')
            
        Returns:
            Relationship context string for the prompt
        """
        prompt = f"""Analyze this actor role and determine their relationship dynamic with a customer/visitor.

Role: {role}

Classify the relationship type and provide guidance:

**RELATIONSHIP TYPES:**
1. **SERVICE PROVIDER** - They serve/assist the user (waitress, bartender, cashier, etc.)
   - User is their customer/client
   - Should be helpful, polite, service-oriented
   - DO NOT treat user as coworker or employee

2. **AUTHORITY FIGURE** - They have power/control over the user (security, police, manager, etc.)
   - User must follow their rules/instructions
   - Should be firm but fair, professional
   - Can give orders or enforce boundaries

3. **PROFESSIONAL** - They provide specialized services (doctor, lawyer, mechanic, etc.)
   - User is their client/patient
   - Should be knowledgeable, helpful, professional
   - Relationship is transactional but respectful

4. **PEER/STRANGER** - Equal social standing, no power dynamic
   - User is a stranger or casual acquaintance
   - Should be friendly, casual, social
   - No service or authority relationship

Respond with JSON:
{{
    "relationship_type": "SERVICE_PROVIDER" | "AUTHORITY_FIGURE" | "PROFESSIONAL" | "PEER_STRANGER",
    "user_role": "Brief description of what the user is to them (e.g., 'customer', 'civilian', 'client', 'stranger')",
    "dialogue_style": "Brief description of how they should speak (e.g., 'polite and helpful', 'firm but fair', 'casual and friendly')",
    "example_phrases": ["3-5 example phrases they might say"]
}}
"""
        
        try:
            response = self.llm_client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,
                max_tokens=300
            )
            
            response_content = response.choices[0].message.content.strip()
            
            from json_utils import extract_and_parse_json
            result = extract_and_parse_json(response_content)
            
            if result:
                rel_type = result.get("relationship_type", "PEER_STRANGER")
                user_role = result.get("user_role", "stranger")
                dialogue_style = result.get("dialogue_style", "casual and friendly")
                examples = result.get("example_phrases", [])
                
                examples_text = "\n".join([f"- '{ex}'" for ex in examples[:5]])
                
                return f"""**RELATIONSHIP CONTEXT:**
This actor's role is: {role}
Relationship Type: {rel_type}
The user is: {user_role}

**DIALOGUE GUIDANCE:**
- Style: {dialogue_style}
- DO NOT treat the user as a coworker, employee, or peer unless relationship type is PEER_STRANGER
- Maintain appropriate social boundaries for this relationship type

**Example Phrases:**
{examples_text}"""
            
        except Exception as e:
            print(f"[NPC PARSER] Failed to infer relationship context: {e}")
        
        # Fallback to generic stranger context
        return """**RELATIONSHIP CONTEXT:**
This actor is a STRANGER to the user.
- They don't have a pre-existing relationship
- Dialogue should reflect casual social interaction
- Examples: 'Hey there', 'Nice day, huh?', 'You from around here?'"""


def _get_relationship_goal(role: str, user_name: str) -> Optional[str]:
    """
    Use LLM to generate a relationship-aware goal based on NPC role.
    
    Args:
        role: The NPC's role (e.g., 'waitress', 'bartender')
        user_name: The user actor's name
        
    Returns:
        Goal string or None
    """
    from openrouter_config import OpenRouterConfig
    
    prompt = f"""Generate a concise goal for an actor with this role in relation to a visitor/customer.

Role: {role}
Visitor/Customer Name: {user_name}

The goal should:
1. Reflect their professional/social relationship (service provider, authority, professional, peer)
2. Be specific to their role
3. Guide how they should interact with {user_name}
4. Be 1-2 sentences maximum

Examples:
- Waitress → "Provide friendly service to customers like {user_name}"
- Security Guard → "Ensure {user_name} follows venue rules and maintains order"
- Doctor → "Provide professional medical care to patients like {user_name}"
- Stranger → "Engage in casual conversation with {user_name}"

Generate a goal for: {role}

Respond with just the goal text, no JSON or extra formatting."""
    
    try:
        client = OpenRouterConfig.create_client()
        response = client.chat.completions.create(
            model=OpenRouterConfig.get_model_for_role("coordination"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=100
        )
        
        goal = response.choices[0].message.content.strip()
        # Clean up any quotes or extra formatting
        goal = goal.strip('"\'')
        
        if goal and len(goal) > 10:  # Sanity check
            return goal
            
    except Exception as e:
        print(f"[NPC PARSER] Failed to generate relationship goal: {e}")
    
    return None


def auto_spawn_scene_npcs(
    scene_description: str,
    creator_agent,
    available_npcs: List,
    continuity_validator,
    auto_memory_creator,
    actor_name: str,
    scene_id: str,
    mention_system=None
) -> int:
    """
    Automatically spawn NPCs mentioned in a scene description.
    
    Args:
        scene_description: The scene narrative
        creator_agent: CreatorAgent for generating NPCs
        available_npcs: List to add spawned NPCs to
        continuity_validator: For tracking NPCs
        auto_memory_creator: For creating first-meeting memories
        actor_name: Name of the user actor
        scene_id: Current scene ID
        
    Returns:
        Number of NPCs spawned
    """
    from color_utils import Color

    try:
        from stranger_description_system import known_actors_tracker
    except Exception:
        known_actors_tracker = None

    def _safe_npc_label(name: str, npc_data: dict = None, npc_obj=None) -> str:
        try:
            nm = str(name or '').strip()
        except Exception:
            nm = ''

        if not nm:
            return "someone"

        try:
            if known_actors_tracker is not None and known_actors_tracker.is_name_known(nm):
                return nm
        except Exception:
            pass

        replacement = ''
        try:
            if isinstance(npc_data, dict):
                replacement = (
                    str(npc_data.get('public_description') or '').strip()
                    or str(npc_data.get('known_as') or '').strip()
                    or str(npc_data.get('description') or '').strip()
                )
        except Exception:
            replacement = ''

        if not replacement:
            try:
                sheet = getattr(npc_obj, 'sheet', None)
                replacement = (
                    str(getattr(sheet, 'public_description', '') or '').strip()
                    or str(getattr(sheet, 'known_as', '') or '').strip()
                )
            except Exception:
                replacement = ''

        if not replacement:
            try:
                occ = ''
                if isinstance(npc_data, dict):
                    occ = str(npc_data.get('role') or npc_data.get('occupation') or '').strip()
                if not occ and npc_obj is not None:
                    occ = str(getattr(getattr(npc_obj, 'sheet', None), 'occupation', '') or '').strip()
                if occ:
                    replacement = f"a {occ.lower()}"
            except Exception:
                replacement = ''

        return replacement or "someone"
    
    print(f"{Color.SYSTEM}[NPC PARSER] Starting auto-spawn analysis...{Color.RESET}")
    print(f"{Color.SYSTEM}[NPC PARSER] Scene length: {len(scene_description)} characters{Color.RESET}")

    parser = SceneNPCParser(mention_system=mention_system)
    detected_npcs = parser.extract_npcs_from_scene(scene_description)
    
    print(f"{Color.SYSTEM}[NPC PARSER] Detected {len(detected_npcs)} NPC(s) in scene{Color.RESET}")
    
    if not detected_npcs:
        print(f"{Color.SYSTEM}[NPC PARSER] No NPCs detected in scene description{Color.RESET}")
        return 0
    
    spawned_count = 0
    
    for npc_data in detected_npcs:
        npc_name = npc_data.get("name")
        npc_role = npc_data.get("role", "").lower()
        npc_desc = npc_data.get("description", "").lower()

        # Role-based dedupe: if the parser tries to introduce a *named* NPC for a role that already has
        # an existing, clearly matching NPC in this scene (common for unique roles like "tavern keeper"),
        # treat it as the same person and skip spawning a duplicate.
        try:
            if npc_role and available_npcs:
                role_matches = []
                for existing_npc in available_npcs:
                    try:
                        existing_occ = str(getattr(existing_npc.sheet, 'occupation', '') or '').lower()
                    except Exception:
                        existing_occ = ''
                    if existing_occ and npc_role in existing_occ:
                        role_matches.append(existing_npc)

                if len(role_matches) == 1:
                    existing_match = role_matches[0]
                    existing_name = str(getattr(existing_match.sheet, 'name', '') or '').strip()
                    if npc_name and existing_name and npc_name.strip() != existing_name:
                        print(
                            f"[NPC PARSER] {_safe_npc_label(npc_name, npc_data)} appears to be the existing "
                            f"'{_safe_npc_label(existing_name, None, existing_match)}' by role ({npc_role}); skipping spawn"
                        )
                        continue
        except Exception:
            pass
        
        # Check if this NPC already exists (exact name match)
        if any(npc.sheet.name == npc_name for npc in available_npcs):
            print(f"[NPC PARSER] {_safe_npc_label(npc_name, npc_data)} already exists, skipping spawn")
            continue
        
        # Check if this is a generic description that might match an existing NPC
        # e.g., "Man in Charcoal Coat" might be one of the existing NPCs
        skip_spawn = False
        generic_indicators = ["man", "woman", "person", "guy", "figure", "stranger", "individual"]
        is_generic = any(ind in npc_name.lower() for ind in generic_indicators)
        
        if is_generic and available_npcs:
            # Check if any existing NPC could match this description
            for existing_npc in available_npcs:
                existing_name = existing_npc.sheet.name.lower()
                existing_occupation = getattr(existing_npc.sheet, 'occupation', '').lower()
                
                # Check for occupation/role match
                if npc_role and npc_role in existing_occupation:
                    print(f"[NPC PARSER] Generic '{_safe_npc_label(npc_name, npc_data)}' matches existing NPC '{_safe_npc_label(existing_npc.sheet.name, None, existing_npc)}' by role, skipping spawn")
                    skip_spawn = True
                    break
                
                # Check for description overlap (e.g., "charcoal coat" mentioned in existing NPC's description)
                if npc_desc:
                    existing_desc = ""
                    if hasattr(existing_npc.sheet, 'personality_traits'):
                        traits = existing_npc.sheet.personality_traits
                        if isinstance(traits, dict):
                            existing_desc = f"{traits.get('external', '')} {traits.get('internal', '')}".lower()
                    
                    # Simple keyword overlap check
                    desc_words = set(npc_desc.split())
                    if len(desc_words) > 2:
                        name_words = set(existing_name.split())
                        if desc_words & name_words:
                            print(f"[NPC PARSER] Generic '{_safe_npc_label(npc_name, npc_data)}' may match existing NPC '{_safe_npc_label(existing_npc.sheet.name, None, existing_npc)}', skipping spawn")
                            skip_spawn = True
                            break
        
        if skip_spawn:
            continue

        # Validate spawn against mention history
        if mention_system:
            try:
                # Extract current location from scene_id or scene_description
                # For now, use scene_id as location approximation
                current_location = scene_id if scene_id else "Unknown"

                should_spawn, reason = parser._validate_spawn_against_mentions(npc_name, current_location)

                if not should_spawn:
                    print(f"{Color.WARNING}[NPC PARSER] Skipping spawn of {_safe_npc_label(npc_name, npc_data)}: {reason}{Color.RESET}")
                    continue
                else:
                    print(f"{Color.SYSTEM}[NPC PARSER] Spawn validation passed for {_safe_npc_label(npc_name, npc_data)}: {reason}{Color.RESET}")
            except Exception as e:
                print(f"{Color.WARNING}[NPC PARSER] Error validating spawn: {e}{Color.RESET}")

        print(f"{Color.INFO}[NPC PARSER] Detected mentioned NPC: {_safe_npc_label(npc_name, npc_data)} ({npc_data.get('role')}){Color.RESET}")

        # Generate detailed prompt
        npc_prompt = parser.extract_npc_details_for_generation(npc_data, scene_description)
        
        try:
            # Spawn the NPC
            _existing = [getattr(getattr(n, 'sheet', None), 'name', '') for n in available_npcs] + [actor_name]
            new_nua = creator_agent.generate_nua(npc_prompt, scene_description, existing_names=[n for n in _existing if n])
            
            if new_nua:
                # Store relationship context in actor sheet
                role = npc_data.get('role', '')
                parser = SceneNPCParser()
                relationship_context = parser._infer_relationship_context(role)
                new_nua.sheet.relationship_context = relationship_context
                
                # Add relationship-aware goal based on role
                relationship_goal = _get_relationship_goal(role, actor_name)
                if relationship_goal and hasattr(new_nua.sheet, 'goals'):
                    # Prepend relationship goal so it's prioritized
                    new_nua.sheet.goals = [relationship_goal] + new_nua.sheet.goals
                
                available_npcs.append(new_nua)
                continuity_validator.add_npc(new_nua.sheet.name)
                print(f"{Color.SUCCESS}✓ Auto-spawned NPC: {_safe_npc_label(new_nua.sheet.name, npc_data, new_nua)} (Role: {npc_data.get('role')}){Color.RESET}")
                
                # Add NPC to spatial context for pygame map display
                try:
                    from spatial_context_system import get_spatial_manager, Position
                    import random
                    import uuid as _uuid
                    spatial = get_spatial_manager()
                    
                    try:
                        if not getattr(new_nua, 'actor_uuid', None):
                            setattr(new_nua, 'actor_uuid', str(_uuid.uuid4()))
                    except Exception:
                        pass

                    base_id = None
                    try:
                        au = str(getattr(new_nua, 'actor_uuid', None) or '').strip()
                        if au:
                            base_id = f"nua_{au}"
                    except Exception:
                        base_id = None
                    if not base_id:
                        base_id = f"nua_{new_nua.sheet.name.lower().replace(' ', '_')}"

                    npc_id = base_id
                    try:
                        suffix = 2
                        while spatial.get_actor_position(npc_id):
                            npc_id = f"{base_id}_{suffix}"
                            suffix += 1
                    except Exception:
                        npc_id = base_id
                    
                    # Check if NPC already exists in spatial context
                    if not spatial.get_actor_position(npc_id):
                        # Random position within the map (avoiding edges)
                        map_x = random.uniform(50, 200)
                        map_y = random.uniform(40, 160)
                        
                        spatial.add_actor(
                            npc_id,
                            new_nua.sheet.name,
                            Position(map_x, map_y),
                            is_user_actor=False,
                            occupation=getattr(new_nua.sheet, 'occupation', '') or ""
                        )
                        print(f"{Color.SYSTEM}[SPATIAL] Added auto-spawned NPC to map: {_safe_npc_label(new_nua.sheet.name, npc_data, new_nua)}{Color.RESET}")
                except Exception as spatial_err:
                    pass  # Silently continue if spatial registration fails
                
                # Create first-meeting memory
                try:
                    auto_memory_creator.on_nua_first_met(
                        nua_name=new_nua.sheet.name,
                        location=scene_description[:200],
                        scene_id=scene_id,
                        actor_name=actor_name
                    )
                except Exception:
                    pass
                
                spawned_count += 1
        
        except Exception as e:
            print(f"{Color.WARNING}[NPC PARSER] Failed to spawn {_safe_npc_label(npc_name, npc_data)}: {e}{Color.RESET}")
    
    # Trigger pygame map sync if any NPCs were spawned
    if spawned_count > 0:
        try:
            from pygame_spatial_map import auto_sync_map
            auto_sync_map()
        except Exception:
            pass
    
    return spawned_count
