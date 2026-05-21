"""
Journey Chunking System - Prevents Teleportation

This system breaks long actions into multiple 3-minute narrative segments
to maintain temporal realism and prevent instant teleportation.

RULE OF 3's PRINCIPLE:
- If an action takes 10 minutes, narrate it in ~3 chunks (3min + 3min + 3min + 1min)
- If an action takes 30 minutes, narrate it in ~10 chunks
- NEVER teleport - always show the journey

EXAMPLES:
- "I head to a nearby restaurant" (10 min walk)
  → Chunk 1: Leave current location, start walking
  → Chunk 2: Walking through streets, observations
  → Chunk 3: Approaching destination area
  → Chunk 4: Arrive at restaurant

- "I drive across town" (30 min drive)
  → 10 chunks of 3 minutes each showing the drive
"""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum
import json
from openrouter_config import create_role_client


class JourneyType(Enum):
    """Types of journeys that need chunking"""
    WALKING = "walking"
    DRIVING = "driving"
    RUNNING = "running"
    CYCLING = "cycling"
    PUBLIC_TRANSIT = "public_transit"  # Bus, subway, metro
    TRAIN = "train"  # Long-distance train
    PLANE = "plane"  # Air travel
    CLIMBING = "climbing"
    SWIMMING = "swimming"
    OTHER = "other"


@dataclass
class JourneyChunk:
    """A single 3-minute segment of a journey"""
    chunk_number: int
    total_chunks: int
    duration_minutes: float
    chunk_type: str  # "departure", "transit", "arrival"
    narrative_focus: str
    location_context: str
    time_elapsed: float  # Total time elapsed so far
    progress_percentage: int  # How far along the journey (0-100%)
    distance_remaining: str  # Descriptive distance remaining


class JourneyChunkingSystem:
    """Breaks long actions into realistic 3-minute narrative segments"""
    
    def __init__(self, key_memories_system=None):
        self.client = create_role_client("analysis")
        self.chunk_duration = 3.0  # minutes per chunk
        self.key_memories_system = key_memories_system  # For checking established travel times
        
        # Distance/time estimates (in minutes)
        self.travel_time_estimates = {
            "nearby": 5,      # 5 min walk
            "close": 5,
            "short walk": 5,
            "across street": 2,
            "few blocks": 10,
            "several blocks": 15,
            "across town": 30,
            "far": 45,
            "other side of city": 60,
            "subway": 10,     # Default subway travel time
            "metro": 10,
            "train station": 10
        }
    
    def should_chunk_action(self, user_input: str, action_description: str) -> bool:
        """
        Determine if an action should be chunked into multiple segments.
        
        Returns True if:
        - Action involves travel/movement to a different location
        - Estimated duration > 5 minutes
        - Action is not already at destination
        """
        travel_keywords = [
            "head to", "go to", "walk to", "drive to", "travel to",
            "move to", "run to", "bike to", "cycle to",
            "head towards", "make my way", "journey to"
        ]
        
        # Check if action involves travel
        input_lower = user_input.lower()
        has_travel = any(keyword in input_lower for keyword in travel_keywords)
        
        if not has_travel:
            return False
        
        # Estimate duration
        estimated_duration = self._estimate_duration(user_input, action_description)
        
        # Chunk if duration > 5 minutes
        return estimated_duration > 5.0
    
    def _detect_transportation_method(self, user_input: str, action_description: str) -> JourneyType:
        """
        Detect what transportation method the user is using.
        
        Returns JourneyType enum based on keywords in input.
        """
        input_lower = user_input.lower()
        desc_lower = action_description.lower()
        combined = f"{input_lower} {desc_lower}"
        
        # Check for specific transportation keywords (order matters - check specific before general)
        if any(word in combined for word in ["plane", "airplane", "aircraft", "fly", "flight", "airport", "jet"]):
            return JourneyType.PLANE
        elif any(word in combined for word in ["train", "railway", "railroad", "locomotive", "amtrak"]):
            return JourneyType.TRAIN
        elif any(word in combined for word in ["bus", "subway", "metro", "transit", "public transport", "tram", "trolley"]):
            return JourneyType.PUBLIC_TRANSIT
        elif any(word in combined for word in ["drive", "car", "vehicle", "truck", "van", "automobile", "sedan", "suv"]):
            return JourneyType.DRIVING
        elif any(word in combined for word in ["bike", "bicycle", "cycle", "pedal", "cycling"]):
            return JourneyType.CYCLING
        elif any(word in combined for word in ["motorcycle", "motorbike", "bike", "harley", "chopper"]):
            return JourneyType.CYCLING  # Treat motorcycles like bikes for speed
        elif any(word in combined for word in ["run", "sprint", "jog", "dash", "running"]):
            return JourneyType.RUNNING
        elif any(word in combined for word in ["climb", "scale", "ascend", "climbing"]):
            return JourneyType.CLIMBING
        elif any(word in combined for word in ["swim", "wade", "cross water", "swimming"]):
            return JourneyType.SWIMMING
        elif any(word in combined for word in ["walk", "head", "go", "move", "stroll", "walking"]):
            return JourneyType.WALKING
        else:
            return JourneyType.OTHER
    
    def _estimate_duration(self, user_input: str, action_description: str) -> float:
        """
        Estimate how long an action will take in minutes.
        
        Priority:
        1. Check memories for established travel times
        2. Use LLM analysis
        3. Fallback to keyword matching
        """
        # PRIORITY 1: Check memories for established travel times
        if self.key_memories_system:
            try:
                from key_memories_system import MemoryImportance
                # Access memories dictionary directly and filter
                all_memories = self.key_memories_system.memories.values()
                
                # Filter by importance (ROUTINE and above)
                importance_order = [MemoryImportance.ROUTINE, MemoryImportance.NOTABLE, 
                                  MemoryImportance.IMPORTANT, MemoryImportance.CRITICAL]
                filtered_memories = []
                for memory in all_memories:
                    try:
                        if memory.importance in importance_order:
                            filtered_memories.append(memory)
                    except AttributeError:
                        continue
                
                # Sort by timestamp and limit
                filtered_memories.sort(key=lambda m: m.timestamp, reverse=True)
                memories = filtered_memories[:50]
                
                # Extract destination from user input
                destination_keywords = []
                input_lower = user_input.lower()
                if " to " in input_lower:
                    parts = input_lower.split(" to ", 1)
                    if len(parts) > 1:
                        dest = parts[1].strip().rstrip('.,!?')
                        destination_keywords.append(dest)
                        # Also add individual words
                        destination_keywords.extend(dest.split())
                
                # Search memories for travel time information
                for memory in memories:
                    memory_text = f"{memory.title} {memory.description}".lower()
                    
                    # Check if memory mentions this destination
                    if any(keyword in memory_text for keyword in destination_keywords):
                        # Look for time indicators
                        import re
                        time_patterns = [
                            r'(\d+)\s*(?:minute|min)',
                            r'(\d+)\s*(?:hour|hr)',
                            r'(\d+)-(\d+)\s*(?:minute|min)'
                        ]
                        
                        for pattern in time_patterns:
                            matches = re.findall(pattern, memory_text)
                            if matches:
                                if isinstance(matches[0], tuple):
                                    # Range like "10-15 minutes"
                                    duration = float(matches[0][0])
                                else:
                                    duration = float(matches[0])
                                
                                # Convert hours to minutes if needed
                                if 'hour' in memory_text or 'hr' in memory_text:
                                    duration *= 60
                                
                                print(f"[CHUNKING] ✅ Found travel time in memory: {duration} minutes")
                                return duration
            except Exception as e:
                print(f"[CHUNKING] Memory check failed: {e}")
        
        # PRIORITY 2: Use LLM analysis
        try:
            return self._llm_estimate_duration(user_input, action_description)
        except Exception as e:
            print(f"[CHUNKING] LLM estimation failed, using fallback: {e}")
            
        # PRIORITY 3: Fallback to keyword matching
        return self._fallback_estimate_duration(user_input, action_description)
    
    def _llm_estimate_duration(self, user_input: str, action_description: str) -> float:
        """Use LLM to estimate action duration"""
        prompt = f"""
Estimate how long this action will take in MINUTES.

User Input: {user_input}
Action Description: {action_description}

Consider TRANSPORTATION METHOD and DISTANCE:

**Walking speeds:**
- Nearby/close: 5 minutes
- Few blocks: 10 minutes
- Across town: 60+ minutes

**Driving speeds (car/truck/van):**
- Nearby: 3 minutes
- Few blocks: 5 minutes
- Across town: 15-30 minutes

**Cycling speeds (bike/bicycle/motorcycle):**
- Nearby: 3 minutes
- Few blocks: 7 minutes
- Across town: 20-40 minutes

**Running speeds:**
- Nearby: 3 minutes
- Few blocks: 5 minutes
- Across town: 30+ minutes

**Public transit (bus/subway/metro):**
- Nearby: 5 minutes (includes waiting)
- Few blocks: 10 minutes
- Across town: 20-40 minutes

**Train (long-distance):**
- Short trip: 30 minutes
- Medium trip: 60-120 minutes
- Long trip: 180+ minutes

**Plane (air travel):**
- Include boarding, taxi, flight, deplaning
- Short flight: 60-90 minutes total
- Medium flight: 120-180 minutes total
- Long flight: 240+ minutes total

Respond with ONLY a number (the estimated minutes). Examples:
- "I walk to the nearby diner" → 5
- "I drive across town" → 20
- "I bike to the store" → 7
- "I take the train downtown" → 45
- "I fly to the next city" → 120

Estimated minutes:"""

        response = self.client.chat.completions.create(
            model="deepseek/deepseek-r1",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50,
            temperature=0.3
        )
        
        duration_text = response.choices[0].message.content.strip()
        
        # Extract number
        import re
        match = re.search(r'\d+', duration_text)
        if match:
            return float(match.group())
        
        return 5.0  # Default fallback
    
    def _fallback_estimate_duration(self, user_input: str, action_description: str = "") -> float:
        """Fallback keyword-based duration estimation with transportation awareness"""
        input_lower = user_input.lower()
        
        # Detect transportation method
        transport = self._detect_transportation_method(user_input, action_description)
        
        # Check for distance keywords first
        base_duration = None
        for keyword, duration in self.travel_time_estimates.items():
            if keyword in input_lower:
                base_duration = duration
                break
        
        # If no distance keyword, use defaults
        if base_duration is None:
            base_duration = 10.0  # Default 10 minutes
        
        # Adjust based on transportation method
        speed_multipliers = {
            JourneyType.PLANE: 0.1,      # Planes are MUCH faster (but include boarding/taxi time)
            JourneyType.TRAIN: 0.4,      # Trains are faster than cars
            JourneyType.DRIVING: 0.5,    # Cars are 2x faster than walking
            JourneyType.CYCLING: 0.7,    # Bikes are ~1.5x faster than walking
            JourneyType.PUBLIC_TRANSIT: 0.6,  # Buses/subway similar to cars
            JourneyType.RUNNING: 0.5,    # Running is 2x faster than walking
            JourneyType.WALKING: 1.0,    # Baseline
            JourneyType.CLIMBING: 2.0,   # Climbing is 2x slower than walking
            JourneyType.SWIMMING: 3.0,   # Swimming is 3x slower than walking
            JourneyType.OTHER: 1.0
        }
        
        multiplier = speed_multipliers.get(transport, 1.0)
        adjusted_duration = base_duration * multiplier
        
        # Minimum 3 minutes (one chunk)
        return max(3.0, adjusted_duration)
    
    def create_journey_chunks(
        self,
        user_input: str,
        action_description: str,
        estimated_duration: float,
        current_location: str,
        destination: str
    ) -> List[JourneyChunk]:
        """
        Break a journey into 3-minute narrative chunks.
        
        Args:
            user_input: Original user input
            action_description: Interpreted action
            estimated_duration: Total journey time in minutes
            current_location: Where they're starting from
            destination: Where they're going
            
        Returns:
            List of JourneyChunk objects
        """
        # Calculate number of chunks (round up)
        import math
        num_chunks = max(2, math.ceil(estimated_duration / self.chunk_duration))
        
        chunks = []
        time_elapsed = 0.0
        
        for i in range(num_chunks):
            chunk_num = i + 1
            
            # Calculate progress percentage
            progress_pct = int((chunk_num / num_chunks) * 100)
            
            # Calculate descriptive distance remaining
            remaining_chunks = num_chunks - chunk_num
            if remaining_chunks == 0:
                distance_remaining = "at destination"
            elif remaining_chunks == 1:
                distance_remaining = "very close"
            elif remaining_chunks <= 3:
                distance_remaining = "approaching"
            elif remaining_chunks <= num_chunks // 2:
                distance_remaining = "halfway there"
            else:
                distance_remaining = "still far"
            
            # Determine chunk type
            if chunk_num == 1:
                chunk_type = "departure"
                narrative_focus = f"Leaving {current_location}"
                location_context = current_location
                distance_remaining = "just started"
            elif chunk_num == num_chunks:
                chunk_type = "arrival"
                narrative_focus = f"Arriving at {destination}"
                location_context = destination
                distance_remaining = "at destination"
            else:
                chunk_type = "transit"
                narrative_focus = f"In transit ({progress_pct}% of journey)"
                location_context = f"Between {current_location} and {destination}"
            
            # Calculate chunk duration (last chunk may be shorter)
            if chunk_num == num_chunks:
                chunk_duration = estimated_duration - time_elapsed
            else:
                chunk_duration = self.chunk_duration
            
            time_elapsed += chunk_duration
            
            chunk = JourneyChunk(
                chunk_number=chunk_num,
                total_chunks=num_chunks,
                duration_minutes=chunk_duration,
                chunk_type=chunk_type,
                narrative_focus=narrative_focus,
                location_context=location_context,
                time_elapsed=time_elapsed,
                progress_percentage=progress_pct,
                distance_remaining=distance_remaining
            )
            
            chunks.append(chunk)
        
        return chunks
    
    def generate_chunk_narrative_prompt(
        self,
        chunk: JourneyChunk,
        user_input: str,
        action_description: str,
        actor_name: str,
        scene_description: str,
        destination: str = "destination"
    ) -> str:
        """
        Generate a narrative prompt for a specific journey chunk.
        
        This prompt will be used by NarratorAgent to generate the narrative
        for this segment of the journey.
        """
        chunk_context = f"""
**JOURNEY IN PROGRESS: Heading to {destination}**

**JOURNEY CHUNK {chunk.chunk_number} of {chunk.total_chunks}**
Type: {chunk.chunk_type.upper()}
Focus: {chunk.narrative_focus}
Duration: {chunk.duration_minutes:.1f} minutes
Time Elapsed: {chunk.time_elapsed:.1f} minutes total

**PROGRESS TRACKING:**
- Progress: {chunk.progress_percentage}% complete
- Distance Status: {chunk.distance_remaining}
- Destination: {destination}

**ORIGINAL ACTION:** {user_input}
**INTERPRETED ACTION:** {action_description}
**ACTOR:** {actor_name}
**CURRENT CONTEXT:** {scene_description[:300]}

**NARRATIVE REQUIREMENTS:**
"""
        
        if chunk.chunk_type == "departure":
            chunk_context += f"""
- Show {actor_name} LEAVING the current location to head toward {destination}
- Describe the transition from inside → outside (or current space → next space)
- Set the tone for the journey - they are heading to {destination}
- 2-3 sentences maximum
- DO NOT arrive at {destination} yet - this is just the beginning
- Focus on: Exiting, first steps, initial observations, sense of purpose toward destination
"""
        elif chunk.chunk_type == "transit":
            # Customize transit narrative based on progress
            if chunk.distance_remaining == "very close":
                progress_hint = f"You're very close to {destination} now - it should be visible ahead"
            elif chunk.distance_remaining == "approaching":
                progress_hint = f"You're approaching {destination} - getting closer with each step"
            elif chunk.distance_remaining == "halfway there":
                progress_hint = f"You're about halfway to {destination}"
            else:
                progress_hint = f"You're making steady progress toward {destination}"
            
            chunk_context += f"""
- Show {actor_name} IN TRANSIT, making progress toward {destination}
- Progress Status: {chunk.distance_remaining} ({chunk.progress_percentage}% complete)
- {progress_hint}
- Describe what they see/hear/experience during travel
- Include environmental details (streets, buildings, people, weather)
- Subtly reference progress toward {destination} based on distance status
- 2-3 sentences maximum
- DO NOT arrive at {destination} yet - still in transit
- Focus on: Movement, observations, journey experience, sense of progress
"""
        else:  # arrival
            chunk_context += f"""
- Show {actor_name} ARRIVING at {destination}
- Describe approaching and entering {destination}
- Transition from outside → inside (or previous space → new space)
- 2-3 sentences maximum
- This is the FINAL chunk - they have REACHED {destination}
- Focus on: Approach, entrance, first impression of {destination}
"""
        
        chunk_context += f"""
**CRITICAL RULES:**
- This is chunk {chunk.chunk_number}/{chunk.total_chunks} - narrate ONLY this segment
- DO NOT skip ahead to later chunks
- DO NOT narrate the entire journey at once
- Keep it concise (2-3 sentences)
- Maintain the setting's tone and technology level
- Use second person ("you") for user actor

Generate the narrative for THIS CHUNK ONLY:
"""
        
        return chunk_context


# Global instance
_journey_chunking_system = None

def get_journey_chunking_system(key_memories_system=None) -> JourneyChunkingSystem:
    """Get or create the global journey chunking system instance"""
    global _journey_chunking_system
    if _journey_chunking_system is None:
        _journey_chunking_system = JourneyChunkingSystem(key_memories_system=key_memories_system)
    elif key_memories_system and not _journey_chunking_system.key_memories_system:
        # Update existing instance with key memories system if not already set
        _journey_chunking_system.key_memories_system = key_memories_system
    return _journey_chunking_system
