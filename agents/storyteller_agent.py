"""
Storyteller Agent - Silent Orchestrator with Spark System

This agent exists in the background and interprets the potential of situations.
It takes over the job of the Four-Mode Narrative Loop (enhanced) and triggers
based on location changes.

Key Responsibilities:
1. Analyze situation potential when entering new locations
2. Generate Sparks (narrative hooks) based on context, RAG, and goals
3. Maintain balance between light and heavy situations
4. Prioritize actor recurrence over creation
5. Track callbacks for long-term story effects

Spark Types:
1. MOMENTUM SPARKS - Open possibilities for new goals/tasks
2. EXCHANGE SPARKS - Lead to encounters (light or heavy)
3. CALLBACK SPARKS - Long-term effects of past actions

Design Philosophy:
- Silent orchestrator - should not be visible to user
- Drop hints with narrative engagement flavor
- Cannot manipulate situations, only present opportunities
- User action trumps everything
- Balance light and heavy (1:1 ratio long-term)
- Callback sparks should be RARE and feel natural
"""

import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field

from openrouter_config import create_role_client, OpenRouterConfig, robust_llm_call, RetryConfig
from json_utils import extract_and_parse_json
from color_utils import Color

try:
    from stranger_description_system import known_actors_tracker
except Exception:
    known_actors_tracker = None


class SparkType(Enum):
    """Types of narrative sparks"""
    MOMENTUM = "momentum"   # Goal/task opportunities
    EXCHANGE = "exchange"   # Encounter opportunities
    CALLBACK = "callback"   # Long-term action effects


class SparkWeight(Enum):
    """Weight/stakes of a spark"""
    LIGHT = "light"   # Low stakes (shopping, cooking, sleeping)
    HEAVY = "heavy"   # High stakes (shootouts, danger, conflict)


class ExchangeType(Enum):
    """Types of exchanges sparks can lead to"""
    FIGHT = "fight"
    FLIRT = "flirt"
    CONVINCE = "convince"
    HELP = "help"
    HEAL = "heal"
    THREATEN = "threaten"
    NEGOTIATE = "negotiate"


@dataclass
class ExchangeOutcome:
    """Potential outcome of an exchange spark"""
    success_reward: str          # What UA gains on success
    success_relationship: str    # How relationship changes on success (+sympathy, ally, etc.)
    failure_punishment: str      # What UA loses on failure
    failure_relationship: str    # How relationship changes on failure (-sympathy, enemy, etc.)
    ignore_consequence: str      # What happens if UA ignores the spark
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success_reward": self.success_reward,
            "success_relationship": self.success_relationship,
            "failure_punishment": self.failure_punishment,
            "failure_relationship": self.failure_relationship,
            "ignore_consequence": self.ignore_consequence
        }


@dataclass
class Spark:
    """A narrative spark - a hook for potential story development"""
    spark_type: SparkType
    weight: SparkWeight
    description: str                    # The narrative description
    trigger_description: str            # What the user sees/hears
    
    # For MOMENTUM sparks
    potential_goal: Optional[str] = None
    potential_task: Optional[str] = None
    potential_reward: Optional[str] = None
    potential_punishment: Optional[str] = None
    
    # For EXCHANGE sparks
    exchange_type: Optional[ExchangeType] = None
    involved_nua: Optional[str] = None  # NUA name if involves existing actor
    is_nua_initiated: bool = False      # Does NUA approach UA?
    exchange_outcomes: Optional[ExchangeOutcome] = None  # Clear outcomes for the exchange
    
    # For CALLBACK sparks
    original_action: Optional[str] = None
    time_since_action: Optional[str] = None
    callback_effect: Optional[str] = None
    
    # Metadata
    location: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    was_engaged: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "spark_type": self.spark_type.value,
            "weight": self.weight.value,
            "description": self.description,
            "trigger_description": self.trigger_description,
            "potential_goal": self.potential_goal,
            "potential_task": self.potential_task,
            "potential_reward": self.potential_reward,
            "potential_punishment": self.potential_punishment,
            "exchange_type": self.exchange_type.value if self.exchange_type else None,
            "involved_nua": self.involved_nua,
            "is_nua_initiated": self.is_nua_initiated,
            "exchange_outcomes": self.exchange_outcomes.to_dict() if self.exchange_outcomes else None,
            "original_action": self.original_action,
            "time_since_action": self.time_since_action,
            "callback_effect": self.callback_effect,
            "location": self.location,
            "created_at": self.created_at.isoformat(),
            "was_engaged": self.was_engaged
        }


@dataclass
class PastAction:
    """Record of a past action for callback tracking"""
    action_description: str
    outcome: str
    location: str
    involved_actors: List[str]
    timestamp: datetime
    severity: str  # minor, moderate, major, extreme
    callback_potential: float  # 0-1, how likely to generate callback
    has_generated_callback: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_description": self.action_description,
            "outcome": self.outcome,
            "location": self.location,
            "involved_actors": self.involved_actors,
            "timestamp": self.timestamp.isoformat(),
            "severity": self.severity,
            "callback_potential": self.callback_potential,
            "has_generated_callback": self.has_generated_callback
        }


class StorytellerAgent:
    """
    Silent orchestrator that generates narrative sparks.
    
    Triggers on location changes to drop 0-3 sparks that create
    narrative opportunities without forcing player engagement.
    """
    
    def __init__(self, storage_directory: Path = None):
        self.client = create_role_client("narration")
        self.logger = logging.getLogger(__name__)
        self.storage_directory = storage_directory or Path("./simulation_data")

        # Use a dedicated RNG so other systems calling random.seed(...) don't affect spark frequency.
        self._rng = random.Random()
        
        # Track light/heavy balance
        self.light_count: int = 0
        self.heavy_count: int = 0
        
        # Track past actions for callbacks
        self.past_actions: List[PastAction] = []
        self.max_past_actions = 50
        
        # Track known NUAs for recurrence
        self.known_nuas: Dict[str, Dict[str, Any]] = {}
        
        # Track active sparks
        self.active_sparks: List[Spark] = []
        
        # Track current goal/task status
        self.has_active_goal: bool = False
        self.has_active_task: bool = False
        
        # Time context for temporal awareness
        self.time_context = None
        
        # Load state
        self._load_state()
    
    def set_time_context(self, time_context):
        """Set the current time context for spark generation."""
        self.time_context = time_context
    
    def _format_time_context(self, time_context=None) -> str:
        """Format time context for inclusion in prompts."""
        tc = time_context or self.time_context
        
        # Auto-fetch from MasterTimeCoordinator if not set
        if not tc:
            try:
                from master_time_coordinator import get_master_time_coordinator
                master_time = get_master_time_coordinator()
                if master_time:
                    tc = master_time.get_current_time_context()
            except Exception:
                pass
        
        if not tc:
            return ""
        
        time_str = tc.get('time_string', '') or tc.get('formatted_time', '')
        period = tc.get('time_of_day', '') or tc.get('period', '')
        
        parts = []
        if time_str:
            parts.append(f"Current Time: {time_str}")
        if period:
            parts.append(f"Time of Day: {period}")
        
        if parts:
            return f"""
**TIME CONTEXT (Generate time-appropriate sparks):**
{chr(10).join(parts)}
"""
        return ""
    
    def on_location_change(self,
                          new_location: str,
                          location_description: str,
                          actor_goal: str,
                          actor_task: str,
                          available_nuas: List[Dict[str, Any]],
                          recent_narrative: List[str],
                          rag_context: str = "") -> List[Spark]:
        """
        Called when UA enters a new location.
        
        Generates 0-3 sparks based on context.
        
        Args:
            new_location: Name of new location
            location_description: Description of the location
            actor_goal: UA's current goal
            actor_task: UA's current task
            available_nuas: NUAs present or known
            recent_narrative: Recent story events
            rag_context: Relevant worldbuilding context
            
        Returns:
            List of generated Sparks
        """
        # Update goal/task status
        self.has_active_goal = bool(actor_goal and actor_goal != "None")
        self.has_active_task = bool(actor_task and actor_task != "None")
        
        # Determine how many sparks to generate (0-3)
        num_sparks = self._determine_spark_count()
        
        if num_sparks == 0:
            return []
        
        # Determine spark composition based on balance and context
        spark_types = self._determine_spark_composition(num_sparks)
        
        # Generate sparks
        sparks = []
        for spark_type in spark_types:
            spark = self._generate_spark(
                spark_type=spark_type,
                location=new_location,
                location_description=location_description,
                actor_goal=actor_goal,
                actor_task=actor_task,
                available_nuas=available_nuas,
                recent_narrative=recent_narrative,
                rag_context=rag_context
            )
            if spark:
                sparks.append(spark)
                self.active_sparks.append(spark)
                
                # Update balance tracking
                if spark.weight == SparkWeight.LIGHT:
                    self.light_count += 1
                else:
                    self.heavy_count += 1
        
        self._save_state()
        return sparks
    
    def _determine_spark_count(self) -> int:
        """Determine how many sparks to generate (0-3)"""
        # Base probabilities
        # 20% chance of 0 sparks (quiet location)
        # 40% chance of 1 spark
        # 30% chance of 2 sparks
        # 10% chance of 3 sparks
        
        roll = self._rng.random()
        if roll < 0.20:
            return 0
        elif roll < 0.60:
            return 1
        elif roll < 0.90:
            return 2
        else:
            return 3
    
    def _determine_spark_composition(self, num_sparks: int) -> List[SparkType]:
        """Determine what types of sparks to generate"""
        spark_types = []
        
        # Check if we need to balance light/heavy
        need_heavy = self.light_count > self.heavy_count + 2
        need_light = self.heavy_count > self.light_count + 2
        
        for i in range(num_sparks):
            # Callback sparks are rare (10% chance, max 1 per location)
            if i == 0 and self._rng.random() < 0.10 and self._has_callback_potential():
                spark_types.append(SparkType.CALLBACK)
                continue
            
            # If goal/task slots are full, prefer EXCHANGE over MOMENTUM
            if self.has_active_goal and self.has_active_task:
                # 70% EXCHANGE, 30% MOMENTUM (that doesn't add goal/task)
                if self._rng.random() < 0.70:
                    spark_types.append(SparkType.EXCHANGE)
                else:
                    spark_types.append(SparkType.MOMENTUM)
            else:
                # 50/50 split
                if self._rng.random() < 0.50:
                    spark_types.append(SparkType.MOMENTUM)
                else:
                    spark_types.append(SparkType.EXCHANGE)
        
        return spark_types

    def _sanitize_spark_text(self, text: str, available_nuas: Optional[List[Dict[str, Any]]] = None) -> str:
        try:
            t = str(text or '')
        except Exception:
            return text

        if not t:
            return t

        if not available_nuas or known_actors_tracker is None:
            return t

        for nua in (available_nuas or []):
            try:
                name = str(nua.get('name') or '').strip()
                if not name:
                    continue
                if known_actors_tracker.is_name_known(name):
                    continue

                replacement = (
                    str(nua.get('public_description') or '').strip()
                    or str(nua.get('known_as') or '').strip()
                    or str(nua.get('description') or '').strip()
                )

                if not replacement:
                    occ = str(nua.get('occupation') or '').strip()
                    if occ:
                        replacement = f"a {occ.lower()}"
                    else:
                        replacement = "someone"

                if replacement and replacement != name:
                    t = t.replace(name, replacement)
            except Exception:
                continue

        return t
    
    def _has_callback_potential(self) -> bool:
        """Check if there are past actions that could generate callbacks"""
        for action in self.past_actions:
            if not action.has_generated_callback and action.callback_potential > 0.3:
                # Check if enough time has passed (at least a few turns)
                time_diff = (datetime.now() - action.timestamp).total_seconds()
                if time_diff > 300:  # At least 5 minutes of play time
                    return True
        return False
    
    def _generate_spark(self,
                       spark_type: SparkType,
                       location: str,
                       location_description: str,
                       actor_goal: str,
                       actor_task: str,
                       available_nuas: List[Dict[str, Any]],
                       recent_narrative: List[str],
                       rag_context: str) -> Optional[Spark]:
        """Generate a single spark"""
        
        if spark_type == SparkType.MOMENTUM:
            return self._generate_momentum_spark(
                location=location,
                location_description=location_description,
                actor_goal=actor_goal,
                actor_task=actor_task,
                rag_context=rag_context,
                available_nuas=available_nuas,
            )
        elif spark_type == SparkType.EXCHANGE:
            return self._generate_exchange_spark(
                location, location_description, available_nuas,
                recent_narrative, rag_context
            )
        else:  # CALLBACK
            return self._generate_callback_spark(
                location=location,
                location_description=location_description,
                recent_narrative=recent_narrative,
                rag_context=rag_context,
                available_nuas=available_nuas,
            )

    def _violates_no_people_rule(self, text: str) -> bool:
        try:
            t = str(text or '').strip().lower()
        except Exception:
            return False

        if not t:
            return False

        banned_markers = [
            " a figure",
            "the figure",
            "someone ",
            "someone's",
            " a stranger",
            "the stranger",
            " a man",
            " a woman",
            " a person",
            "people ",
            "patrons",
            "bartender",
            "waitress",
            "server",
            "customer",
            "merchant",
            "guard",
            "driver",
        ]

        return any(m in t for m in banned_markers)
    
    def _generate_momentum_spark(self,
                                location: str,
                                location_description: str,
                                actor_goal: str,
                                actor_task: str,
                                rag_context: str,
                                available_nuas: Optional[List[Dict[str, Any]]] = None) -> Optional[Spark]:
        """Generate a MOMENTUM spark (goal/task opportunity)"""
        
        # Determine weight based on balance
        weight = self._get_balanced_weight()
        
        # Get time context
        time_section = self._format_time_context()
        
        # Build worldbuilding enforcement section
        worldbuilding_section = ""
        if rag_context:
            worldbuilding_section = f"""
**WORLDBUILDING CONTEXT (CRITICAL - MUST FOLLOW):**
{rag_context[:500]}

**SETTING ENFORCEMENT:** All details MUST be appropriate for the time period and setting specified above. ANACHRONISMS ARE FORBIDDEN.
"""
        else:
            worldbuilding_section = "**WORLDBUILDING CONTEXT:** None available - use only details already established in the scene and actor context"
        
        nua_context = ""
        if available_nuas:
            nua_list = "\n".join(
                f"- {n.get('name', 'Unknown')}: {n.get('occupation', 'Unknown')}" for n in (available_nuas or [])[:8]
            )
            nua_context = f"""\
**AVAILABLE NUAs (EXISTING PEOPLE YOU MAY REFERENCE):**
{nua_list}

**CRITICAL - ACTOR GROUNDING:**
- If you mention a person speaking/acting, you MUST choose ONE of the AVAILABLE NUAs above and use their EXACT name.
- Do NOT invent new people (no "hooded woman", "stranger", etc.) unless it is one of the AVAILABLE NUAs.
- If there are no available NUAs, do NOT use a person at all; use a notice, a sound, a sign, or an environmental hint instead.
"""
        else:
            nua_context = """\
**AVAILABLE NUAs (EXISTING PEOPLE YOU MAY REFERENCE):**
NONE

**CRITICAL - GROUNDED POPULATION RULE (MANDATORY):**
- There are NO available NUAs.
- You MUST NOT mention or imply any people or person-like entities.
- Do NOT describe: "a figure", "a stranger", "someone", "a man", "a woman", "patrons", "bartender", etc.
- Use ONLY environment/objects/sounds/signs/omens.
"""

        prompt = f"""Generate a MOMENTUM SPARK - a narrative hook that opens a possibility for a new goal or task.

**LOCATION:** {location}
**DESCRIPTION:** {location_description}
{time_section}
**CURRENT GOAL:** {actor_goal or 'None'}
**CURRENT TASK:** {actor_task or 'None'}
{worldbuilding_section}
{nua_context}

**WEIGHT:** {weight.value}
- LIGHT: Low stakes (hearing about an opportunity, seeing a notice, noticing something interesting)
- HEAVY: High stakes (overhearing dangerous plans, witnessing an incident, discovering something perilous)

**MOMENTUM SPARK GUIDELINES:**

A momentum spark is something the UA perceives that COULD lead to a new goal or task:
- Overheard conversation
- Written notice or sign (use era-appropriate format from worldbuilding context)
- Environmental detail that hints at opportunity
- Someone mentioning something in passing
- Public announcement (use era-appropriate method from worldbuilding context)

**🚨 CRITICAL: SENTENCE STRUCTURE - START WITH "You [perception verb]..." 🚨**

Every trigger_description sentence MUST begin with "You" + a perception verb.
This places the reader in the act of perceiving BEFORE describing what is perceived.

✓ CORRECT: "You see a notice advertising work for able hands."
✗ WRONG: "A notice advertises work for able hands."

**EXAMPLES (generic - adapt ALL details to match the worldbuilding context era):**

LIGHT:
- "You see a notice advertising work for able hands."
- "You overhear someone mention a place nearby is hiring."
- "You spot a posted message offering payment for information."

HEAVY:
- "You catch a snippet of conversation: '...the shipment arrives at midnight...'"
- "You see scrawled words on the wall: 'THEY'RE WATCHING FROM THE TOWER'"
- "You hear a public announcement: 'Third disappearance this week!'"

**REWARDS/PUNISHMENTS:**

Every momentum spark should have clear potential outcomes:
- REWARD: What the UA gains if they pursue this (information, money, ally, item, progress toward goal)
- PUNISHMENT: What they miss/lose if they ignore it (missed opportunity, danger, regret)

**Response Format:**
Return JSON:

{{
    "trigger_description": "What the UA perceives (1-2 sentences, sensory)",
    "description": "Internal description of the spark",
    "potential_goal": "What goal this could lead to (or null if just a task)",
    "potential_task": "What task this could lead to",
    "potential_reward": "What pursuing this could gain",
    "potential_punishment": "What ignoring this could cost",
    "weight": "{weight.value}"
}}
"""
        
        try:
            response = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=OpenRouterConfig.get_model_for_role("narration"),
                temperature=0.8,
                max_tokens=500,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="MOMENTUM_SPARK"
            )
            
            result = extract_and_parse_json(response)
            
            if not result:
                return None

            trigger_text = self._sanitize_spark_text(result.get("trigger_description", ""), available_nuas)

            if not (available_nuas or []) and self._violates_no_people_rule(trigger_text):
                return None

            result["trigger_description"] = trigger_text
            
            return Spark(
                spark_type=SparkType.MOMENTUM,
                weight=weight,
                description=result.get("description", ""),
                trigger_description=trigger_text,
                potential_goal=result.get("potential_goal"),
                potential_task=result.get("potential_task"),
                potential_reward=result.get("potential_reward"),
                potential_punishment=result.get("potential_punishment"),
                location=location
            )
            
        except Exception as e:
            self.logger.error(f"Error generating momentum spark: {e}")
            return None
    
    def _generate_exchange_spark(self,
                                location: str,
                                location_description: str,
                                available_nuas: List[Dict[str, Any]],
                                recent_narrative: List[str],
                                rag_context: str = "") -> Optional[Spark]:
        """Generate an EXCHANGE spark (encounter opportunity)"""
        
        weight = self._get_balanced_weight()
        
        # Check for recurring NUAs to prioritize
        recurring_nua = self._get_recurring_nua(available_nuas)
        
        # Build NUA context
        nua_context = ""
        if recurring_nua:
            nua_context = f"**RECURRING NUA (PRIORITIZE):** {recurring_nua['name']} - {recurring_nua.get('description', 'Known character')}\n"
        
        if available_nuas:
            nua_list = "\n".join(
                f"- {n.get('name', 'Unknown')}: {n.get('occupation', 'Unknown')}" for n in available_nuas[:5]
            )
            nua_context += f"**AVAILABLE NUAs:**\n{nua_list}\n"
            nua_context += (
                "**CRITICAL - ACTOR GROUNDING:**\n"
                "- If you mention a person speaking/acting, you MUST choose ONE of the AVAILABLE NUAs above and use their EXACT name.\n"
                "- Do NOT invent new people.\n"
            )
        else:
            nua_context += (
                "**AVAILABLE NUAs:** NONE\n\n"
                "**CRITICAL - GROUNDED POPULATION RULE (MANDATORY):**\n"
                "- There are NO available NUAs, so you MUST NOT mention or imply any people or person-like entities.\n"
                "- Use ONLY environment/objects/sounds/signs/omens.\n"
            )
        
        # Build worldbuilding context section
        worldbuilding_section = ""
        if rag_context:
            worldbuilding_section = f"""
**WORLDBUILDING CONTEXT (CRITICAL - MUST FOLLOW):**
{rag_context[:500]}

**SETTING ENFORCEMENT:** All NPCs, dialogue, technology, and situations MUST be appropriate for the time period and setting specified above. ANACHRONISMS ARE FORBIDDEN.
"""
        
        # Get time context
        time_section = self._format_time_context()
        
        prompt = f"""Generate an EXCHANGE SPARK - a narrative hook that could lead to an encounter.

**LOCATION:** {location}
**DESCRIPTION:** {location_description}
{time_section}{worldbuilding_section}
{nua_context}

**RECENT EVENTS:**
{chr(10).join(recent_narrative[-3:]) if recent_narrative else 'None'}

**WEIGHT:** {weight.value}
- LIGHT: Low stakes encounter (friendly chat, simple request, casual interaction)
- HEAVY: High stakes encounter (confrontation, danger, intense situation)

**EXCHANGE SPARK GUIDELINES:**

An exchange spark presents an NUA situation that COULD lead to interaction:

**🚨 CRITICAL: SENTENCE STRUCTURE - START WITH "You [perception verb]..." 🚨**

Every trigger_description sentence MUST begin with "You" + a perception verb.
This places the reader in the act of perceiving BEFORE describing what is perceived.

✓ CORRECT: "You see a woman arguing with a street vendor."
✗ WRONG: "A woman is arguing with a street vendor."

**Two Types:**
1. **OBSERVATIONAL (50%)**: NUA does something interesting nearby
   - UA can choose to engage or just watch
   - Example: "You see a woman arguing with a street vendor."

2. **FORCED (50%)**: NUA directly approaches/confronts UA
   - UA must respond somehow
   - Example: "You see a man in a suit walk up to you. 'Hey, you look like someone who can help me.'"

**EXCHANGE TYPES:**
- fight: Physical confrontation
- flirt: Romantic/attraction interaction
- convince: Persuasion/negotiation
- help: Assistance request/offer
- heal: Medical/emotional support
- threaten: Intimidation
- negotiate: Deal-making

**PRIORITIZE RECURRENCE:**
If a recurring NUA is available, use them instead of creating a new character.
Bringing back known characters creates richer storytelling.

**CRITICAL: CLEAR OUTCOMES (REWARD & PUNISHMENT)**

Every exchange MUST have clear potential outcomes. The UA should understand what's at stake:

**SUCCESS OUTCOMES (if UA engages and succeeds):**
- Reward: Tangible gain (money, item, information, favor owed)
- Relationship: How sympathy/standing changes (+1 to +3 sympathy, new ally, trust gained)

**FAILURE OUTCOMES (if UA engages but fails):**
- Punishment: Tangible loss (money, item, injury, reputation damage)
- Relationship: How sympathy/standing changes (-1 to -3 sympathy, enemy made, trust lost)

**IGNORE OUTCOMES (if UA doesn't engage at all):**
- Consequence: What happens if they walk away (missed opportunity, NUA remembers, situation escalates later)

**EXAMPLES BY WEIGHT:**

LIGHT Exchange (help):
- Success: "Gains $20 and the vendor's gratitude" / "+1 sympathy, potential discount later"
- Failure: "Wastes time, vendor annoyed" / "-1 sympathy"
- Ignore: "Vendor struggles alone, no consequence"

HEAVY Exchange (fight):
- Success: "Defeats attacker, gains their weapon" / "Attacker fears you, won't return"
- Failure: "Takes injury (-2 Stamina), loses wallet" / "Attacker becomes recurring enemy"
- Ignore: "Attacker targets someone else, guilt lingers" OR "Attacker follows you"

**Response Format:**
Return JSON:

{{
    "trigger_description": "What the UA perceives (1-2 sentences, sensory)",
    "description": "Internal description of the spark",
    "exchange_type": "fight/flirt/convince/help/heal/threaten/negotiate",
    "involved_nua": "Name of NUA involved (use existing if possible, or 'NEW: description')",
    "is_nua_initiated": true/false,
    "weight": "{weight.value}",
    "outcomes": {{
        "success_reward": "Tangible gain on success (item, money, information, favor)",
        "success_relationship": "Relationship change on success (+X sympathy, ally gained, etc.)",
        "failure_punishment": "Tangible loss on failure (injury, money, item, reputation)",
        "failure_relationship": "Relationship change on failure (-X sympathy, enemy made, etc.)",
        "ignore_consequence": "What happens if UA doesn't engage (missed opportunity, escalation, nothing)"
    }}
}}
"""
        
        try:
            response = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=OpenRouterConfig.get_model_for_role("narration"),
                temperature=0.8,
                max_tokens=500,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="EXCHANGE_SPARK"
            )
            
            result = extract_and_parse_json(response)
            
            if not result:
                return None

            trigger_text = self._sanitize_spark_text(result.get("trigger_description", ""), available_nuas)
            involved_nua = self._sanitize_spark_text(result.get("involved_nua"), available_nuas)

            if not (available_nuas or []) and self._violates_no_people_rule(trigger_text):
                return None
            
            # Parse exchange type
            exchange_type_str = result.get("exchange_type", "help")
            try:
                exchange_type = ExchangeType(exchange_type_str)
            except ValueError:
                exchange_type = ExchangeType.HELP
            
            # Parse outcomes
            outcomes_data = result.get("outcomes", {})
            exchange_outcomes = None
            if outcomes_data:
                exchange_outcomes = ExchangeOutcome(
                    success_reward=outcomes_data.get("success_reward", "Unknown reward"),
                    success_relationship=outcomes_data.get("success_relationship", "+1 sympathy"),
                    failure_punishment=outcomes_data.get("failure_punishment", "Unknown consequence"),
                    failure_relationship=outcomes_data.get("failure_relationship", "-1 sympathy"),
                    ignore_consequence=outcomes_data.get("ignore_consequence", "No immediate consequence")
                )
            else:
                # Fallback to old format if outcomes not provided
                exchange_outcomes = ExchangeOutcome(
                    success_reward=result.get("potential_reward", "Unknown reward"),
                    success_relationship="+1 sympathy",
                    failure_punishment=result.get("potential_punishment", "Unknown consequence"),
                    failure_relationship="-1 sympathy",
                    ignore_consequence="Missed opportunity"
                )
            
            return Spark(
                spark_type=SparkType.EXCHANGE,
                weight=weight,
                description=result.get("description", ""),
                trigger_description=trigger_text,
                exchange_type=exchange_type,
                involved_nua=involved_nua,
                is_nua_initiated=result.get("is_nua_initiated", False),
                exchange_outcomes=exchange_outcomes,
                location=location
            )
            
        except Exception as e:
            self.logger.error(f"Error generating exchange spark: {e}")
            return None
    
    def _generate_callback_spark(self,
                                location: str,
                                location_description: str,
                                recent_narrative: List[str],
                                rag_context: str = "",
                                available_nuas: Optional[List[Dict[str, Any]]] = None) -> Optional[Spark]:
        """Generate a CALLBACK spark (long-term effect of past action)"""
        
        # Find a suitable past action
        callback_action = self._select_callback_action()
        if not callback_action:
            return None
        
        # Build worldbuilding context section
        worldbuilding_section = ""
        if rag_context:
            worldbuilding_section = f"""
**WORLDBUILDING CONTEXT (CRITICAL - MUST FOLLOW):**
{rag_context[:400]}

**SETTING ENFORCEMENT:** Callbacks MUST be appropriate for this setting's technology and culture.
"""
        
        # Get time context
        time_section = self._format_time_context()
        
        nua_context = ""
        if available_nuas:
            nua_list = "\n".join(
                f"- {n.get('name', 'Unknown')}: {n.get('occupation', 'Unknown')}" for n in (available_nuas or [])[:8]
            )
            nua_context = f"""\
**AVAILABLE NUAs (EXISTING PEOPLE YOU MAY REFERENCE):**
{nua_list}

**CRITICAL - ACTOR GROUNDING:**
- If you mention a person speaking/acting, you MUST choose ONE of the AVAILABLE NUAs above and use their EXACT name.
- Do NOT invent new people.
"""

        prompt = f"""Generate a CALLBACK SPARK - a long-term consequence of a past action.

**LOCATION:** {location}
**DESCRIPTION:** {location_description}
{time_section}{worldbuilding_section}
{nua_context}

**ORIGINAL ACTION:**
{callback_action.action_description}

**OUTCOME:**
{callback_action.outcome}

**INVOLVED ACTORS:**
{', '.join(callback_action.involved_actors) if callback_action.involved_actors else 'None'}

**TIME SINCE ACTION:** Several days/weeks have passed

**CALLBACK SPARK GUIDELINES:**

A callback spark shows the ripple effects of past actions:
- NOT immediate consequences (those happen right away)
- Long-term effects that emerge later
- Should feel natural, not forced
- Can be positive or negative based on original action

**🚨 CRITICAL: SENTENCE STRUCTURE - START WITH "You [perception verb]..." 🚨**

Every trigger_description sentence MUST begin with "You" + a perception verb.
This places the reader in the act of perceiving BEFORE describing what is perceived.

✓ CORRECT: "You overhear whispers about a killer matching your description."
✗ WRONG: "Whispers circulate about a killer matching your description."

**EXAMPLES (generic - adapt ALL details to match the worldbuilding context era):**

Original: "You killed someone in front of a witness"
Callback: "You overhear whispers - someone describing a killer who matches your appearance. You hear mention of a reward being offered."

Original: "You helped someone in need"
Callback: "You see someone approach you. 'You helped my family member recently. They won't stop talking about you. Thanks.'"

Original: "You stole from a merchant"
Callback: "You notice your description on a wanted notice. You see the reward is surprisingly high."

**Response Format:**
Return JSON:

{{
    "trigger_description": "What the UA perceives (1-2 sentences, sensory)",
    "description": "Internal description of the callback",
    "original_action": "{callback_action.action_description[:100]}",
    "time_since_action": "days/weeks ago",
    "callback_effect": "What this callback means for the UA",
    "weight": "light/heavy"
}}
"""
        
        try:
            response = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=OpenRouterConfig.get_model_for_role("narration"),
                temperature=0.7,
                max_tokens=400,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="CALLBACK_SPARK"
            )
            
            result = extract_and_parse_json(response)
            
            if not result:
                return None
            
            # Mark action as having generated callback
            callback_action.has_generated_callback = True
            
            weight_str = result.get("weight", "light")
            weight = SparkWeight.HEAVY if weight_str == "heavy" else SparkWeight.LIGHT

            trigger_text = self._sanitize_spark_text(result.get("trigger_description", ""), available_nuas)

            if not (available_nuas or []) and self._violates_no_people_rule(trigger_text):
                return None
            
            return Spark(
                spark_type=SparkType.CALLBACK,
                weight=weight,
                description=result.get("description", ""),
                trigger_description=trigger_text,
                original_action=result.get("original_action"),
                time_since_action=result.get("time_since_action"),
                callback_effect=result.get("callback_effect"),
                location=location
            )
            
        except Exception as e:
            self.logger.error(f"Error generating callback spark: {e}")
            return None
    
    def _get_balanced_weight(self) -> SparkWeight:
        """Get weight that helps balance light/heavy ratio"""
        # If significantly unbalanced, correct
        if self.light_count > self.heavy_count + 3:
            return SparkWeight.HEAVY
        elif self.heavy_count > self.light_count + 3:
            return SparkWeight.LIGHT
        
        # Otherwise 50/50
        return SparkWeight.LIGHT if self._rng.random() < 0.5 else SparkWeight.HEAVY
    
    def _get_recurring_nua(self, available_nuas: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Get a recurring NUA if available"""
        for nua in available_nuas:
            nua_name = nua.get("name", "")
            if nua_name in self.known_nuas:
                return nua
        return None
    
    def _select_callback_action(self) -> Optional[PastAction]:
        """Select a past action suitable for callback"""
        candidates = [
            a for a in self.past_actions
            if not a.has_generated_callback and a.callback_potential > 0.3
        ]
        
        if not candidates:
            return None
        
        # Weight by callback potential
        weights = [a.callback_potential for a in candidates]
        return self._rng.choices(candidates, weights=weights, k=1)[0]
    
    def record_action(self,
                     action_description: str,
                     outcome: str,
                     location: str,
                     involved_actors: List[str],
                     severity: str = "minor"):
        """
        Record an action for potential future callbacks.
        
        Args:
            action_description: What happened
            outcome: How it turned out
            location: Where it happened
            involved_actors: Who was involved
            severity: minor/moderate/major/extreme
        """
        # Calculate callback potential based on severity
        potential_map = {
            "minor": 0.1,
            "moderate": 0.3,
            "major": 0.6,
            "extreme": 0.9
        }
        callback_potential = potential_map.get(severity, 0.2)
        
        action = PastAction(
            action_description=action_description,
            outcome=outcome,
            location=location,
            involved_actors=involved_actors,
            timestamp=datetime.now(),
            severity=severity,
            callback_potential=callback_potential
        )
        
        self.past_actions.append(action)
        
        # Trim if too many
        if len(self.past_actions) > self.max_past_actions:
            # Remove oldest low-potential actions first
            self.past_actions.sort(key=lambda a: (a.callback_potential, a.timestamp))
            self.past_actions = self.past_actions[-self.max_past_actions:]
        
        self._save_state()
    
    def register_nua(self, nua_name: str, nua_data: Dict[str, Any]):
        """Register an NUA for potential recurrence"""
        self.known_nuas[nua_name] = {
            **nua_data,
            "first_met": datetime.now().isoformat(),
            "encounter_count": self.known_nuas.get(nua_name, {}).get("encounter_count", 0) + 1
        }
        self._save_state()
    
    def mark_spark_engaged(self, spark: Spark):
        """Mark a spark as having been engaged by the user"""
        spark.was_engaged = True
        self._save_state()
    
    def update_goal_task_status(self, has_goal: bool, has_task: bool):
        """Update tracking of goal/task status"""
        self.has_active_goal = has_goal
        self.has_active_task = has_task
    
    def get_balance_status(self) -> Dict[str, Any]:
        """Get current light/heavy balance status"""
        total = self.light_count + self.heavy_count
        return {
            "light_count": self.light_count,
            "heavy_count": self.heavy_count,
            "total": total,
            "light_ratio": self.light_count / total if total > 0 else 0.5,
            "heavy_ratio": self.heavy_count / total if total > 0 else 0.5,
            "is_balanced": abs(self.light_count - self.heavy_count) <= 3
        }
    
    def _save_state(self):
        """Save storyteller state to disk"""
        try:
            import json
            state_file = self.storage_directory / "storyteller" / "state.json"
            state_file.parent.mkdir(parents=True, exist_ok=True)
            
            state = {
                "light_count": self.light_count,
                "heavy_count": self.heavy_count,
                "past_actions": [a.to_dict() for a in self.past_actions],
                "known_nuas": self.known_nuas,
                "active_sparks": [s.to_dict() for s in self.active_sparks[-20:]],
                "has_active_goal": self.has_active_goal,
                "has_active_task": self.has_active_task
            }
            
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save storyteller state: {e}")
    
    def _load_state(self):
        """Load storyteller state from disk"""
        try:
            import json
            state_file = self.storage_directory / "storyteller" / "state.json"
            
            if state_file.exists():
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                
                self.light_count = state.get("light_count", 0)
                self.heavy_count = state.get("heavy_count", 0)
                self.known_nuas = state.get("known_nuas", {})
                self.has_active_goal = state.get("has_active_goal", False)
                self.has_active_task = state.get("has_active_task", False)
                
                # Reconstruct past actions
                for action_data in state.get("past_actions", []):
                    self.past_actions.append(PastAction(
                        action_description=action_data["action_description"],
                        outcome=action_data["outcome"],
                        location=action_data["location"],
                        involved_actors=action_data["involved_actors"],
                        timestamp=datetime.fromisoformat(action_data["timestamp"]),
                        severity=action_data["severity"],
                        callback_potential=action_data["callback_potential"],
                        has_generated_callback=action_data.get("has_generated_callback", False)
                    ))
                    
        except Exception as e:
            self.logger.warning(f"Could not load storyteller state: {e}")


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def display_spark(spark: Spark, show_outcomes: bool = False):
    """Display a spark to the user (just the trigger, not the metadata)"""
    # The spark should feel natural, not like a game prompt
    # Just show what the character perceives
    print(f"\n{Color.STATUS}{spark.trigger_description}{Color.RESET}")
    
    # Optionally show outcomes for exchange sparks (for debugging or explicit display)
    if show_outcomes and spark.spark_type == SparkType.EXCHANGE and spark.exchange_outcomes:
        display_exchange_outcomes(spark)


def display_exchange_outcomes(spark: Spark):
    """Display the potential outcomes of an exchange spark"""
    if not spark.exchange_outcomes:
        return
    
    outcomes = spark.exchange_outcomes
    weight_icon = "⚡" if spark.weight == SparkWeight.HEAVY else "💫"
    
    print(f"\n{Color.INFO}┌─────────────────────────────────────────────────────────┐{Color.RESET}")
    print(f"{Color.INFO}│{Color.RESET} {weight_icon} {Color.ACTOR_NAME}POTENTIAL OUTCOMES{Color.RESET} ({spark.weight.value.upper()}) {Color.INFO}│{Color.RESET}")
    print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
    
    # Success outcomes
    print(f"{Color.INFO}│{Color.RESET} {Color.SUCCESS}✓ SUCCESS:{Color.RESET}")
    print(f"{Color.INFO}│{Color.RESET}   💰 {outcomes.success_reward}")
    print(f"{Color.INFO}│{Color.RESET}   💚 {outcomes.success_relationship}")
    
    # Failure outcomes
    print(f"{Color.INFO}│{Color.RESET} {Color.WARNING}✗ FAILURE:{Color.RESET}")
    print(f"{Color.INFO}│{Color.RESET}   💸 {outcomes.failure_punishment}")
    print(f"{Color.INFO}│{Color.RESET}   💔 {outcomes.failure_relationship}")
    
    # Ignore outcomes
    print(f"{Color.INFO}│{Color.RESET} {Color.STATUS}○ IGNORE:{Color.RESET}")
    print(f"{Color.INFO}│{Color.RESET}   🚶 {outcomes.ignore_consequence}")
    
    print(f"{Color.INFO}└─────────────────────────────────────────────────────────┘{Color.RESET}")


def display_sparks(sparks: List[Spark], show_outcomes: bool = False):
    """Display multiple sparks"""
    for spark in sparks:
        display_spark(spark, show_outcomes)


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global instance
_storyteller: Optional[StorytellerAgent] = None


def get_storyteller(storage_directory: Path = None) -> StorytellerAgent:
    """Get or create the global storyteller agent"""
    global _storyteller
    if _storyteller is None:
        _storyteller = StorytellerAgent(storage_directory)
    return _storyteller


def generate_location_sparks(new_location: str,
                            location_description: str,
                            actor_goal: str,
                            actor_task: str,
                            available_nuas: List[Dict[str, Any]] = None,
                            recent_narrative: List[str] = None) -> List[Spark]:
    """Convenience function to generate sparks for a new location"""
    storyteller = get_storyteller()
    return storyteller.on_location_change(
        new_location=new_location,
        location_description=location_description,
        actor_goal=actor_goal,
        actor_task=actor_task,
        available_nuas=available_nuas or [],
        recent_narrative=recent_narrative or []
    )


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Storyteller Agent Test\n")
    
    storyteller = StorytellerAgent(Path("./test_data"))
    
    # Test location change
    print("=== Testing Location Change Sparks ===\n")
    
    sparks = storyteller.on_location_change(
        new_location="Downtown Supermarket",
        location_description="A busy supermarket with fluorescent lights and crowded aisles. The smell of fresh bread wafts from the bakery section.",
        actor_goal="Find out who killed my brother",
        actor_task="Talk to witnesses",
        available_nuas=[
            {"name": "Store Manager", "occupation": "Manager"},
            {"name": "Security Guard", "occupation": "Security"}
        ],
        recent_narrative=[
            "You left your apartment this morning",
            "You took the bus downtown",
            "You arrived at the supermarket"
        ]
    )
    
    print(f"Generated {len(sparks)} sparks:\n")
    
    for i, spark in enumerate(sparks, 1):
        print(f"Spark {i}:")
        print(f"  Type: {spark.spark_type.value}")
        print(f"  Weight: {spark.weight.value}")
        print(f"  Trigger: {spark.trigger_description}")
        if spark.potential_reward:
            print(f"  Potential Reward: {spark.potential_reward}")
        if spark.potential_punishment:
            print(f"  Potential Punishment: {spark.potential_punishment}")
        print()
    
    # Test balance
    print("=== Balance Status ===")
    balance = storyteller.get_balance_status()
    print(f"Light: {balance['light_count']} | Heavy: {balance['heavy_count']}")
    print(f"Balanced: {balance['is_balanced']}")
    
    print("\n✅ Storyteller Agent ready!")
