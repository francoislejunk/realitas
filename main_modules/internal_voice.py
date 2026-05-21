"""Auto-extracted from redesigned_main.py"""

import sys
import os
import time
import re
import json
import random
import threading
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

# These imports will need to be adjusted based on what's actually used in each module

def process_internal_voice_cue(actor, context: str, narrative_result: str = "") -> str:
    """
    Process internal voice cue based on context and personality/goals.
    
    Returns internal voice string or empty string if not triggered.
    """
    try:
        actor_id = getattr(actor, 'id', None) or getattr(actor.sheet, 'name', 'ua')
        actor_sheet = getattr(actor, 'sheet', None)
        
        # Combine context
        full_context = f"{context}\n{narrative_result}" if narrative_result else context
        
        # Get internal voice cue
        voice_cue = get_internal_voice_cue(actor_id, full_context, actor_sheet)
        
        return voice_cue or ""
    except Exception:
        return ""




def init_new_voice_systems(storage_dir: Path, rag_system=None):
    """
    Initialize the new internal voice and storyteller systems.
    
    Called during simulation startup.
    
    Args:
        storage_dir: Path to storage directory
        rag_system: Optional RAG system for worldbuilding context
    """
    global _voice_interpreter, _voice_creator, _storyteller, _reputation_system
    
    if not NEW_VOICE_SYSTEM_AVAILABLE:
        print(f"{Color.WARNING}⚠️ New voice systems not available - using legacy system{Color.RESET}")
        return False
    
    try:
        print(f"{Color.INFO}🧠 Initializing Internal Voice System...{Color.RESET}")
        _voice_interpreter = InternalVoiceInterpreterAgent()
        _voice_creator = InternalVoiceCreatorAgent(storage_directory=storage_dir, rag_system=rag_system)
        print(f"{Color.SUCCESS}✓ Internal Voice Interpreter & Creator ready{Color.RESET}")
        
        print(f"{Color.INFO}📖 Initializing Storyteller Agent...{Color.RESET}")
        _storyteller = StorytellerAgent(storage_directory=storage_dir)
        print(f"{Color.SUCCESS}✓ Storyteller Agent ready{Color.RESET}")
        
        print(f"{Color.INFO}🏆 Initializing Reputation System...{Color.RESET}")
        _reputation_system = ReputationSystem(storage_directory=storage_dir, rag_system=rag_system)
        print(f"{Color.SUCCESS}✓ Reputation System ready{Color.RESET}")
        
        # Disable legacy internal voice in NarratorAgent
        try:
            NarratorAgent.disable_internal_voice()
            print(f"{Color.SUCCESS}✓ Legacy NarratorAgent internal voice disabled{Color.RESET}")
        except Exception:
            pass

        return True
        
    except Exception as e:
        print(f"{Color.ERROR}❌ Failed to initialize new voice systems: {e}{Color.RESET}")
        return False




def generate_new_internal_voice(
    actor,
    scene_description: str,
    user_action: str,
    action_outcome: str,
    current_goal: str = "",
    current_task: str = "",
    available_memories: List[str] = None,
    max_retries: int = 3
) -> Optional[Dict[str, Any]]:
    """
    Generate internal voice using the new agent system with retry handling.
    
    Returns voice result dict or None on failure.
    """
    if not NEW_VOICE_SYSTEM_AVAILABLE or _voice_interpreter is None or _voice_creator is None:
        return None
    
    for attempt in range(max_retries):
        try:
            # Get actor info
            actor_name = actor.sheet.name if hasattr(actor, 'sheet') else str(actor)
            personality_prompt = ""
            if hasattr(actor, 'sheet') and hasattr(actor.sheet, 'get_personality_prompt_section'):
                personality_prompt = actor.sheet.get_personality_prompt_section()
            elif hasattr(actor, 'sheet') and hasattr(actor.sheet, 'personality_traits'):
                traits = actor.sheet.personality_traits
                personality_prompt = f"Internal: {traits.get('internal', '')}\nExternal: {traits.get('external', '')}"
            
            # Step 1: Interpret what type of voice is needed
            interpretation = _voice_interpreter.interpret_situation(
                scene_description=scene_description,
                user_action=user_action,
                action_outcome=action_outcome,
                actor_goals=[current_goal] if current_goal else [],
                actor_personality=personality_prompt,
                available_memories=available_memories or []
            )
            
            if not interpretation:
                continue
            
            # Step 2: Generate the actual voice content
            voice_result = _voice_creator.generate_voice(
                interpretation=interpretation,
                scene_description=scene_description,
                user_action=user_action,
                action_outcome=action_outcome,
                personality_prompt=personality_prompt,
                actor_name=actor_name,
                current_goal=current_goal,
                current_task=current_task,
                available_memories=available_memories,
                session_id=getattr(getattr(failure_tracker, 'tracker', None), 'session_id', None) if failure_tracker else getattr(tracker, 'session_id', None) if 'tracker' in globals() else None,
            )
            
            if voice_result and voice_result.get('voice_text'):
                return voice_result
                
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"{Color.WARNING}⚠️ Internal voice generation attempt {attempt + 1} failed: {e}{Color.RESET}")
                time.sleep(0.5 * (attempt + 1))  # Exponential backoff
            else:
                print(f"{Color.ERROR}❌ Internal voice generation failed after {max_retries} attempts{Color.RESET}")
    
    return None




def generate_unified_internal_voice(
    actor,
    narrator,
    scene_description: str,
    user_action: str,
    action_outcome: str,
    function_hint: str = "comment",  # "information", "memory", "solution", "comment"
    question_content: str = None,
    memory_trigger: str = None,
    predicament: str = None,
    urgency: str = "normal",
    failure_tracker = None,
    narrative_context_manager = None,
    available_memories: List[str] = None,
    time_context: Dict[str, Any] = None
) -> Optional[str]:
    """
    Unified internal voice generation using InternalVoiceCreatorAgent + InterpreterAgent.
    Falls back to NarratorAgent if the new system fails.
    
    This is the STANDARD way to generate internal voice across ROAM and EXCHANGE modes.
    
    Args:
        actor: The UserActor
        narrator: NarratorAgent instance for fallback
        scene_description: Current scene
        user_action: What the user did/asked
        action_outcome: Result of the action
        function_hint: Which voice function to use (information, memory, solution, comment)
        question_content: For INFORMATION function - the question being asked
        memory_trigger: For MEMORY function - what triggered the memory
        predicament: For SOLUTION function - the problem to solve
        urgency: Voice urgency level (calm, normal, urgent, frantic)
        failure_tracker: For NarratorAgent fallback
        narrative_context_manager: For NarratorAgent fallback context
        available_memories: List of relevant memory strings to inform the voice
        time_context: Current time info (time_string, day, period, etc.)
        
    Returns:
        Internal voice text string, or None if generation fails
    """
    internal_voice = None

    def _is_ungrounded_hook(voice_text: str) -> bool:
        try:
            v = str(voice_text or '').strip().lower()
        except Exception:
            return False
        if not v:
            return False
        hook_words = ['meeting', 'contact', 'rendezvous', 'appointment']
        if not any(w in v for w in hook_words):
            return False
        try:
            ctx = []
            ctx.append(str(scene_description or ''))
            ctx.append(str(user_action or ''))
            ctx.append(str(action_outcome or ''))
            if available_memories:
                try:
                    ctx.extend([str(m or '') for m in (available_memories or [])])
                except Exception:
                    pass
            ctx_text = ('\n'.join(ctx)).lower()
        except Exception:
            return False
        return not any(w in ctx_text for w in hook_words)

    try:
        qc = str(question_content or '').strip().lower()
    except Exception:
        qc = ''
    if function_hint == 'information' and qc:
        try:
            import re
            is_name_q = bool(re.search(r"\bwhat\s+is\s+my\s+name\b", qc)) or qc in ['my name?', 'name?']
        except Exception:
            is_name_q = ('what is my name' in qc)

        if is_name_q:
            try:
                nm = ''
                if hasattr(actor, 'sheet') and getattr(actor.sheet, 'name', None):
                    nm = str(actor.sheet.name or '').strip()
                if nm and nm.lower() not in ['unknown', 'n/a', 'none']:
                    return f"My name is {nm}."
            except Exception:
                pass

    def _normalize_voice_text(v: str) -> str:
        try:
            import re
        except Exception:
            re = None
        s = str(v or '').strip().lower()
        if not s:
            return ''
        try:
            if re is not None:
                s = re.sub(r"[^a-z0-9\s']+", ' ', s)
                s = re.sub(r"\s+", ' ', s).strip()
        except Exception:
            pass
        return s

    def _similarity(a: str, b: str) -> float:
        aa = _normalize_voice_text(a)
        bb = _normalize_voice_text(b)
        if not aa or not bb:
            return 0.0
        try:
            aset = set(aa.split())
            bset = set(bb.split())
            if not aset or not bset:
                return 0.0
            inter = len(aset.intersection(bset))
            union = max(1, len(aset.union(bset)))
            return float(inter) / float(union)
        except Exception:
            return 0.0

    def _should_block_repetitive_voice(candidate: str) -> bool:
        """Return True if the candidate is too similar to recent internal voices."""
        try:
            from persistent_context_manager import get_context_manager
            cm = get_context_manager()
            if cm is None or not hasattr(cm, 'get_recent_internal_voices'):
                return False
            recent = cm.get_recent_internal_voices(count=4) or []
        except Exception:
            return False

        cand = str(candidate or '').strip()
        if not cand:
            return False

        sims = []
        for e in (recent or []):
            try:
                prev = str((e or {}).get('voice', '') or '').strip()
                if not prev:
                    continue
                sims.append(_similarity(cand, prev))
            except Exception:
                continue

        if not sims:
            return False

        # Block if we are repeating essentially the same thought multiple times.
        # Threshold is intentionally conservative.
        try:
            high = [s for s in sims[:3] if s >= 0.78]
            if len(high) >= 2:
                return True
        except Exception:
            pass

        # Extra guard: same-topic hammering (e.g., repeated 'mentor name' recall attempts)
        try:
            ua = _normalize_voice_text(user_action)
            if ua:
                topic_words = set([w for w in ua.split() if len(w) >= 4])
                if topic_words:
                    recent_actions = []
                    for e in (recent or []):
                        try:
                            recent_actions.append(_normalize_voice_text((e or {}).get('user_action', '') or ''))
                        except Exception:
                            continue
                    overlap_hits = 0
                    for ra in recent_actions[:3]:
                        if not ra:
                            continue
                        ra_words = set([w for w in ra.split() if len(w) >= 4])
                        if len(topic_words.intersection(ra_words)) >= 2:
                            overlap_hits += 1
                    if overlap_hits >= 2 and max(sims) >= 0.65:
                        return True
        except Exception:
            pass

        return False

    def _diegetic_repetition_fallback(
        *,
        voice_creator=None,
        personality_prompt: str = "",
        actor_name: str = "Unknown",
    ) -> str:
        # Keep it short and in-world; avoid instructing the player.
        try:
            if voice_creator is None:
                from agents.internal_voice_creator_agent import get_voice_creator
                voice_creator = get_voice_creator(Path("./simulation_data/memories"))
        except Exception:
            voice_creator = None

        if voice_creator is not None:
            try:
                from agents.internal_voice_interpreter_agent import VoiceInterpretation, InternalVoiceFunction
                interpretation = VoiceInterpretation(
                    primary_function=InternalVoiceFunction.COMMENT,
                    urgency="calm",
                    reasoning="Repetition guard: collapsing repeated thought into a diegetic futility/closure line."
                )

                voice_result = voice_creator.generate_voice(
                    interpretation=interpretation,
                    scene_description=scene_description,
                    user_action=str(user_action or '').strip(),
                    action_outcome="Nothing new surfaces; the thought stalls in the same place.",
                    personality_prompt=str(personality_prompt or ''),
                    actor_name=str(actor_name or 'Unknown'),
                    available_memories=available_memories,
                    time_context=time_context,
                    session_id=(
                        getattr(getattr(failure_tracker, 'tracker', None), 'session_id', None)
                        if failure_tracker
                        else (getattr(tracker, 'session_id', None) if 'tracker' in globals() else None)
                    ),
                )
                if voice_result and voice_result.get("voice_text"):
                    v = str(voice_result.get("voice_text") or '').strip()
                    if v:
                        return v
            except Exception:
                pass

        return "The thought keeps circling back on itself. Whatever answer we want, it refuses to rise, and forcing it only leaves us with the same emptiness."
    
    # Auto-fetch time context if not provided
    if time_context is None:
        try:
            from master_time_coordinator import get_master_time_coordinator
            master_time = get_master_time_coordinator()
            if master_time:
                time_context = master_time.get_current_time_context()
        except Exception:
            pass  # Time context is optional
    
    # Try the new InternalVoiceCreatorAgent system first
    try:
        from agents.internal_voice_creator_agent import get_voice_creator
        from agents.internal_voice_interpreter_agent import VoiceInterpretation, InternalVoiceFunction, QuestionType
        
        # Map function hint to enum
        function_map = {
            "information": InternalVoiceFunction.INFORMATION,
            "memory": InternalVoiceFunction.MEMORY,
            "solution": InternalVoiceFunction.SOLUTION,
            "comment": InternalVoiceFunction.COMMENT
        }
        primary_function = function_map.get(function_hint, InternalVoiceFunction.COMMENT)
        
        # Build interpretation
        interpretation = VoiceInterpretation(
            primary_function=primary_function,
            question_type=QuestionType.CONCEPTUAL if primary_function == InternalVoiceFunction.INFORMATION else None,
            question_content=question_content,
            memory_trigger=memory_trigger,
            predicament_description=predicament,
            urgency=urgency,
            reasoning=f"Action: {user_action}"
        )
        
        # Get the voice creator agent
        voice_creator = get_voice_creator(Path("./simulation_data/memories"))
        
        # Build personality prompt from actor
        personality_prompt = ""
        if hasattr(actor, 'sheet') and hasattr(actor.sheet, 'personality_profile') and actor.sheet.personality_profile:
            personality_prompt = actor.sheet.personality_profile.get_voice_prompt_section()
        
        # Generate voice
        voice_result = voice_creator.generate_voice(
            interpretation=interpretation,
            scene_description=scene_description,
            user_action=user_action,
            action_outcome=action_outcome,
            personality_prompt=personality_prompt,
            actor_name=actor.sheet.name if hasattr(actor, 'sheet') else "Unknown",
            available_memories=available_memories,
            time_context=time_context,
            session_id=(
                getattr(getattr(failure_tracker, 'tracker', None), 'session_id', None)
                if failure_tracker
                else (getattr(tracker, 'session_id', None) if 'tracker' in globals() else None)
            ),
        )
        
        if voice_result and voice_result.get("voice_text"):
            internal_voice = voice_result.get("voice_text")

            try:
                if _is_ungrounded_hook(internal_voice):
                    internal_voice = "Meeting? No. Just a stray thought trying to make patterns out of damp stone and old fear. Focus on what we actually know."
            except Exception:
                pass

            try:
                if _should_block_repetitive_voice(internal_voice):
                    internal_voice = _diegetic_repetition_fallback(
                        voice_creator=voice_creator,
                        personality_prompt=personality_prompt,
                        actor_name=actor.sheet.name if hasattr(actor, 'sheet') else "Unknown",
                    )
            except Exception:
                pass
            
    except Exception as creator_error:
        if not SUPPRESS_DEBUG:
            print(f"{Color.WARNING}InternalVoiceCreatorAgent failed: {creator_error}{Color.RESET}")
    
    # Fallback to NarratorAgent if new system failed
    if not internal_voice and narrator:
        try:
            recent_narrative = ""
            if narrative_context_manager:
                recent_narrative = narrative_context_manager.get_context_for_llm(
                    lookback_events=5,
                    importance_threshold="routine"
                )
            
            internal_voice = narrator.generate_internal_voice(
                ua_actor=actor,
                action_description=user_action,
                scene_description=scene_description,
                narrative_context=recent_narrative,
                success_level=3,
                outcome_description=action_outcome,
                failure_tracker=failure_tracker
            )

            try:
                if internal_voice and _should_block_repetitive_voice(internal_voice):
                    internal_voice = _diegetic_repetition_fallback(
                        personality_prompt=getattr(getattr(actor, 'sheet', None), 'personality_profile', None).get_voice_prompt_section()
                        if getattr(getattr(actor, 'sheet', None), 'personality_profile', None)
                        else "",
                        actor_name=actor.sheet.name if hasattr(actor, 'sheet') else "Unknown",
                    )
            except Exception:
                pass
        except Exception as narrator_error:
            if not SUPPRESS_DEBUG:
                print(f"{Color.WARNING}NarratorAgent fallback also failed: {narrator_error}{Color.RESET}")

    # Persist internal voice with the associated user_action (best-effort) so repetition checks have context
    try:
        if internal_voice:
            from persistent_context_manager import get_context_manager
            cm = get_context_manager()
            if cm is not None and hasattr(cm, 'add_internal_voice'):
                cm.add_internal_voice(internal_voice, user_action=str(user_action or ''))
    except Exception:
        pass
    
    return internal_voice




def display_internal_voice_box(internal_voice: str):
    """Display internal voice with consistent formatting."""
    if internal_voice:
        raw_text = internal_voice
        try:
            # Strip Strategy C mention markers from user-visible text
            import re
            internal_voice = re.sub(r'@\{([^\}]{1,64})\}', r'\1', internal_voice)
            internal_voice = re.sub(r'@(?=\w)', '', internal_voice)
        except Exception:
            pass
        print(f"\n{Color.SYSTEM}{'═' * 70}{Color.RESET}")
        print(f"{Color.SYSTEM}💭 INTERNAL VOICE{Color.RESET}")
        print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}")
        print(f"{Color.INTERNAL_VOICE}{internal_voice}{Color.RESET}")
        print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}")

        try:
            _capture_mentioned_actors_from_text(raw_text, source="internal_voice")
        except Exception:
            pass

        # Best-effort: persist internal voice for debugging/continuity tooling
        try:
            from persistent_context_manager import get_context_manager
            cm = get_context_manager()
            if cm is not None and hasattr(cm, 'add_internal_voice'):
                cm.add_internal_voice(internal_voice)
        except Exception:
            pass

        try:
            _trace_continuity_fact_capture(internal_voice, source="internal_voice", base_confidence=0.45)
        except Exception:
            pass

        try:
            _promote_world_destinations_from_text(internal_voice, source='internal_voice')
        except Exception:
            pass




def display_perceptual_description(perceptual_description: str):
    """Display perceptual description with consistent formatting."""
    if perceptual_description:
        try:
            # Strip Strategy C mention markers from user-visible text
            import re
            perceptual_description = re.sub(r'@\{([^\}]{1,64})\}', r'\1', perceptual_description)
            perceptual_description = re.sub(r'@(?=\w)', '', perceptual_description)
        except Exception:
            pass
        print(f"\n{Color.SYSTEM}{'=' * 8}{Color.RESET}")
        print(f"{Color.SYSTEM}Perceptual Decription{Color.RESET}")
        print(f"{Color.SYSTEM}{'=' * 8}{Color.RESET}")
        print(f"{Color.NARRATIVE}{perceptual_description}{Color.RESET}")

        try:
            if isinstance(_vis_context, dict):
                _vis_context['last_spoken_line'] = str(perceptual_description or '')
        except Exception:
            pass

        try:
            if (
                _vis_autogen_enabled
                and _vis_context
                and _vis_context.get('ua_actor')
                and _vis_context.get('scene_description')
            ):
                _trigger_realtime_video(
                    ua_actor=_vis_context.get('ua_actor'),
                    scene_description=_vis_context.get('scene_description') or "",
                    current_location=_vis_context.get('current_location') or "",
                    time_context=_vis_context.get('time_context') or {},
                    spoken_line=str(perceptual_description or ''),
                    creator_agent=_vis_context.get('creator_agent'),
                    seed=_vis_context.get('seed'),
                )
        except Exception as e:
            try:
                if _env_bool("VIS_IMAGE_DEBUG", False):
                    print(f"{Color.WARNING}🖼️ VIS: perceptual image autogen hook failed: {e}{Color.RESET}")
            except Exception:
                pass

        # Optional: generate an image from perceptual descriptions.
        try:
            if (
                _env_bool("VIS_IMAGE_AUTOGEN_PERCEPTUAL", False)
                and _vis_context
                and _vis_context.get('ua_actor')
                and _vis_context.get('scene_description')
            ):
                _trigger_realtime_image(
                    ua_actor=_vis_context.get('ua_actor'),
                    scene_description=_vis_context.get('scene_description') or "",
                    current_location=_vis_context.get('current_location') or "",
                    time_context=_vis_context.get('time_context') or {},
                    creator_agent=_vis_context.get('creator_agent'),
                    seed=_vis_context.get('seed'),
                    spoken_line=str(perceptual_description or ''),
                    source="perceptual",
                    reason="perceptual_description",
                )
        except Exception as e:
            try:
                if _env_bool("VIS_IMAGE_DEBUG", False):
                    print(f"{Color.WARNING}🖼️ VIS: perceptual image autogen hook failed: {e}{Color.RESET}")
            except Exception:
                pass

        try:
            _trace_continuity_fact_capture(perceptual_description, source="perceptual", base_confidence=0.65)
        except Exception:
            pass

        try:
            _promote_world_destinations_from_text(perceptual_description, source='perceptual')
        except Exception:
            pass


_vis_viewer_server = None
_vis_context = {}
_vis_autogen_enabled = True
_vis_video_worker = None
_vis_video_pending = None
_vis_video_lock = threading.Lock()




def display_perceptual_description_box(perceptual_description: str):
    """Backwards-compatible alias for older call sites."""
    return display_perceptual_description(perceptual_description)



