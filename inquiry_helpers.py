"""
Inquiry System Helper Functions

Provides memory checking, success rolling, and memory management
for the 3-phase inquiry system.
"""

import random
from typing import Optional, Dict, Any, List
from datetime import datetime
from key_memories_system import KeyMemoriesSystem, MemoryCategory, MemoryImportance, KeyMemory


def extract_inquiry_keywords(text: str, answer: Optional[str] = None) -> List[str]:
    """
    Extract relevant keywords from inquiry text and optionally from the answer.
    
    Args:
        text: The inquiry text
        answer: Optional answer text to extract additional keywords from
        
    Returns:
        List of keywords (max 10)
    """
    # Remove question words and common words
    stop_words = {
        'what', 'where', 'when', 'how', 'who', 'why', 'can', 'should', 
        'is', 'are', 'the', 'a', 'an', 'to', 'from', 'in', 'on', 'at',
        'i', 'you', 'we', 'they', 'do', 'does', 'get', 'find', 'have',
        'try', 'remember', 'recall', 'think', 'know', 'learned', 'about',
        'was', 'were', 'been', 'has', 'had', 'that', 'this', 'with', 'for'
    }
    
    # Handle None text
    if not text:
        return []
    
    # Extract from question
    words = text.lower().split()
    keywords = [w.strip('.,!?;:') for w in words if w.lower() not in stop_words and len(w) > 2]
    
    # Extract from answer if provided (to capture names, places, etc.)
    if answer:
        answer_words = answer.lower().split()
        answer_keywords = [w.strip('.,!?;:') for w in answer_words if w.lower() not in stop_words and len(w) > 2]
        # Prioritize proper nouns (capitalized words in original)
        proper_nouns = [w.strip('.,!?;:').lower() for w in answer.split() if w and w[0].isupper() and w.lower() not in stop_words]
        keywords.extend(proper_nouns[:5])  # Add up to 5 proper nouns first
        keywords.extend(answer_keywords[:5])  # Then add other answer keywords
    
    # Remove duplicates while preserving order
    seen = set()
    unique_keywords = []
    for k in keywords:
        if k not in seen and len(k) > 2:
            seen.add(k)
            unique_keywords.append(k)
    
    return unique_keywords[:10]  # Top 10 keywords


def extract_inquiry_subject(question: str) -> str:
    """
    Extract the main subject of the inquiry for memory title.
    
    Args:
        question: The inquiry question
        
    Returns:
        Short subject string
    """
    # Simple extraction - take first few meaningful words
    keywords = extract_inquiry_keywords(question)
    if keywords:
        return " ".join(keywords[:3]).title()
    return "Information"


def check_inquiry_memory(
    user_question: str,
    key_memories_system: KeyMemoriesSystem,
    ua_actor
) -> Optional[Dict[str, Any]]:
    """
    Check if character already knows the answer from memories.
    
    Args:
        user_question: The question being asked
        key_memories_system: The key memories system
        ua_actor: The User Actor
        
    Returns:
        Memory dict if found, None if no relevant memory
    """
    # Extract keywords from question to match against memory tags
    question_keywords = extract_inquiry_keywords(user_question)
    
    # DEBUG: Print what we're searching for
    print(f"[MEMORY SEARCH] Question: '{user_question}'")
    print(f"[MEMORY SEARCH] Keywords extracted: {question_keywords}")
    
    # Search memories for relevant information
    relevant_memories = key_memories_system.search_memories(
        query=user_question,
        limit=10  # Increased to find more candidates
    )
    
    print(f"[MEMORY SEARCH] Found {len(relevant_memories)} total memories")
    
    # Filter for DISCOVERY category (learned information)
    info_memories = [
        m for m in relevant_memories 
        if m.category == MemoryCategory.DISCOVERY
    ]
    
    print(f"[MEMORY SEARCH] Found {len(info_memories)} DISCOVERY memories")
    
    if info_memories:
        # Score memories by tag overlap (prioritize exact keyword matches)
        scored_memories = []
        for memory in info_memories:
            score = 0
            memory_tags = [tag.lower() for tag in (memory.tags or [])]
            memory_title_lower = memory.title.lower()
            
            print(f"[MEMORY SEARCH] Checking memory: '{memory.title}'")
            print(f"[MEMORY SEARCH]   Tags: {memory_tags}")
            
            # Check keyword overlap
            for keyword in question_keywords:
                if keyword.lower() in memory_tags:
                    score += 3  # Strong match for tag overlap
                    print(f"[MEMORY SEARCH]   ✓ Tag match: '{keyword}' (+3)")
                # Check if keyword appears in title (very relevant)
                if keyword.lower() in memory_title_lower:
                    score += 2  # Title match is strong signal
                    print(f"[MEMORY SEARCH]   ✓ Title match: '{keyword}' (+2)")
                # Check if keyword appears in description (weakest signal)
                elif keyword.lower() in memory.description.lower():
                    score += 1  # Weaker match for description mention
                    print(f"[MEMORY SEARCH]   ✓ Description match: '{keyword}' (+1)")
            
            print(f"[MEMORY SEARCH]   Final score: {score}")
            
            # Require minimum score of 2 to filter out weak/irrelevant matches
            if score >= 2:
                scored_memories.append((score, memory))
            else:
                print(f"[MEMORY SEARCH]   ✗ Score too low (< 2), filtering out")
        
        # Sort by score (highest first)
        scored_memories.sort(key=lambda x: x[0], reverse=True)
        
        if scored_memories:
            # Return best match
            best_match = scored_memories[0][1]
            print(f"[MEMORY SEARCH] ✓ FOUND! Returning memory: '{best_match.title}' (score: {scored_memories[0][0]})")
            return {
                'found': True,
                'memory': best_match,
                'answer': best_match.description,
                'source': 'memory_recall'
            }
        else:
            print(f"[MEMORY SEARCH] ✗ No scored memories (all scores were 0)")
    else:
        print(f"[MEMORY SEARCH] ✗ No DISCOVERY memories found")
    
    return None


def determine_inquiry_difficulty(question: str, scene_context: str) -> int:
    """
    Determine difficulty of inquiry based on complexity.
    
    Args:
        question: The inquiry question
        scene_context: Current scene description
        
    Returns:
        Difficulty value (3-10)
    """
    question_lower = question.lower()
    
    # Simple questions (location, time, basic info)
    simple_patterns = ['where is', 'what time', 'how far', 'which way', 'how do i get']
    if any(pattern in question_lower for pattern in simple_patterns):
        return 3  # Easy
    
    # Medium questions (requires thinking)
    medium_patterns = ['how do', 'what should', 'can i', 'is there', 'where can']
    if any(pattern in question_lower for pattern in medium_patterns):
        return 5  # Medium
    
    # Complex questions (requires deep knowledge)
    complex_patterns = ['why did', 'what caused', 'how does', 'what if', 'who is']
    if any(pattern in question_lower for pattern in complex_patterns):
        return 7  # Hard
    
    return 5  # Default medium


def roll_inquiry_success(
    user_question: str,
    ua_actor,
    scene_context: str,
    difficulty: int = 3
) -> Dict[str, Any]:
    """
    Roll to determine if character successfully learns the information.
    
    Uses standard UTAS formula:
    (s_trait + skill + endowment + supplement + serendipity) - (stress + status + sympathy)
    
    Args:
        user_question: The question being asked
        ua_actor: The User Actor
        scene_context: Current scene
        difficulty: Difficulty value (3-10)
        
    Returns:
        Success data with roll breakdown
    """
    from actor_sheet import SFactorType, StatusType
    from unified_formula import calculate_unified_result
    
    # Use unified formula with Smarts-based inquiry
    # Mental actions use Smarts (intelligence/reasoning)
    # No target actor (inquiries are self-directed)
    # No targeted status (not affecting a status)
    # Stress level based on difficulty
    result = calculate_unified_result(
        actor=ua_actor,
        s_trait=SFactorType.SMARTS,  # Mental action uses Smarts
        skill_name=None,  # No specific skill for general inquiries
        target_actor=None,  # No target for inquiries
        shift_polarity='Subtractive',  # Not relevant for inquiries
        targeted_status=None,  # Not targeting a status
        supplement_val=0,  # No supplement bonus for mental actions
        serendipity_override=None,  # Let it roll naturally
        stress_level_override=difficulty  # Difficulty maps to stress level
    )
    
    # Extract values for display
    positive = result['positive_components']
    negative = result['negative_components']
    total = result['final_result']
    success = total >= 0  # Success if result is non-negative
    
    return {
        'success': success,
        'total': total,
        'breakdown': {
            's_trait': positive['s_trait'],
            'skill': positive['skill'],
            'endowment': positive['endowment'],
            'supplement': positive['supplement'],
            'serendipity': positive['serendipity'],
            'stress_modifier': negative['stress_modifier'],
            'status_modifier': negative['status_modifier'],
            'sympathy_modifier': negative['sympathy_modifier'],
            'difficulty': difficulty
        }
    }


def check_duplicate_inquiry_memory(
    question: str,
    answer: str,
    key_memories_system: KeyMemoriesSystem
) -> Optional[KeyMemory]:
    """
    Check if similar information already exists in memories.
    
    Args:
        question: The inquiry question
        answer: The answer that would be stored
        key_memories_system: The key memories system
        
    Returns:
        Existing memory if duplicate found, None otherwise
    """
    # Handle None answer
    if not answer:
        return None
    
    # Extract keywords from question and answer
    question_keywords = set(extract_inquiry_keywords(question))
    answer_keywords = set(extract_inquiry_keywords(answer))
    all_keywords = question_keywords | answer_keywords
    
    # Search existing DISCOVERY memories
    existing_memories = [
        m for m in key_memories_system.memories.values()
        if m.category == MemoryCategory.DISCOVERY
    ]
    
    # Check for semantic similarity
    for memory in existing_memories:
        # Get memory keywords from tags and title
        memory_keywords = set(memory.tags + memory.title.lower().split())
        
        # Calculate overlap
        overlap = len(memory_keywords & all_keywords)
        if not memory_keywords or not all_keywords:
            continue
            
        similarity = overlap / max(len(memory_keywords), len(all_keywords))
        
        if similarity > 0.5:  # 50% keyword overlap
            return memory
    
    return None


def process_failed_inquiry(
    user_question: str,
    ua_actor,
    scene_context: str,
    narrator
) -> str:
    """
    Generate perceptual response for failed inquiry (NO suggestions - that's internal voice's job).
    
    Args:
        user_question: The question being asked
        ua_actor: The User Actor
        scene_context: Current scene
        narrator: NarratorAgent instance
        
    Returns:
        Narrative expressing lack of perception/knowledge
    """
    ua_name = ua_actor.sheet.name
    
    prompt = f"""Generate a brief PERCEPTUAL narrative showing {ua_name} doesn't perceive/know the answer.

**QUESTION:** "{user_question}"
**SCENE:** {scene_context[:200]}

**CRITICAL:** ONLY describe what is perceived/not perceived. NO suggestions or advice!

**GOOD EXAMPLES (perceptions only):**
- "You look around. Nothing familiar. You don't recognize this area."
- "You scan the surroundings. No clear landmarks. Nothing you've seen before."
- "You try to focus. The details won't come. Your mind draws a blank."
- "You don't see anything that answers the question."

**BAD EXAMPLES (contain suggestions - DON'T DO THIS):**
- "You'd need to ask someone or check a map." ❌ (Suggestion!)
- "You should look for a sign." ❌ (Advice!)
- "Maybe try asking around." ❌ (Suggestion!)

**REQUIREMENTS:**
- 1-2 sentences
- Use "you" perspective
- ONLY describe lack of perception/knowledge
- ABSOLUTELY NO suggestions or advice

Respond with ONLY the perceptual narrative."""
    
    try:
        response = narrator.client.chat.completions.create(
            model=narrator.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=100,
            timeout=15
        )
        
        if response and response.choices and response.choices[0].message.content:
            uncertainty = response.choices[0].message.content.strip()
            uncertainty = uncertainty.strip('"').strip("'")
            return uncertainty if uncertainty else "You don't know."
    
    except Exception:
        pass
    
    # Fallback (perceptions only, no suggestions)
    return "You try to focus. Nothing comes to mind. You don't know."
