# Agent LLM Prompt Testing Guide

This guide provides sample prompts and test data for systematically testing all agents using the `debug_llm_prompt.py` tool.

## Testing Process
1. Run `python debug_llm_prompt.py`
2. Copy and paste the prompt below
3. Type `###` on a new line to end input
4. Analyze the raw LLM response for issues

---

## 1. InterpreterAgent (CRITICAL - Self-Effects Issue)

### Test 1A: Proactor Action Interpretation (_build_interpretation_prompt)

**Priority: HIGH** - This is where the self-effects issue occurs

```
You are a UTAS simulation interpreter. Analyze the user's action and provide comprehensive mechanical breakdown.

**Scene Context:**
A tense confrontation in a dimly lit alley between two rival gang members. The air is thick with tension as both figures size each other up, hands hovering near concealed weapons.

**Actor Details:**
Name: Raven Blackthorn
S-Factors: {'Swiftness': 3, 'Sociability': 2, 'Sturdiness': 4, 'Smarts': 2, 'Shadow': 3}
Skills: {'Tactical Combat': 4, 'Intimidation': 3, 'Stealth': 2}
Endowments: {}
Inventory: ['Serrated Combat Dagger - A wicked blade designed for close combat', 'Leather Jacket - Worn but protective', 'Cigarettes - Half-empty pack']
Statuses: {'Stamina': {'value': 4, 'modifier': 0}, 'Spirit': {'value': 3, 'modifier': 0}, 'Supply': {'value': 2, 'modifier': 0}}

**User Action:** "Lunge at Kaelen with a serrated combat dagger."

**Required Analysis:**
Provide a JSON response with EXACTLY the following structure:
{
    "action_noun": "Brief action name",
    "action_description": "Detailed description of what the actor is attempting",
    "narrative_description": "Rich, immersive description of the action",
    "utas_factors": {
        "exchange_type": "Supply/Stamina/Spirit/Sympathy - what type of STATUS conflict this represents",
        "status_to_shift": "The target STATUS on the reactor (Stamina/Spirit/Supply/Sympathy)",
        "s_trait_to_use": "Primary S-TRAIT name (Swiftness/Sociability/Sturdiness/Smarts/Shadow)",
        "s_trait_value": "Numerical value of the S-TRAIT",
        "s_trait_justification": "Detailed explanation of why this S-TRAIT applies",
        "skill": {"name": "skill_name", "value": "skill_value"},
        "skill_justification": "Detailed explanation of how this skill applies to the action",
        "endowment": {"name": "endowment_name", "value": "endowment_value"},
        "supplement": {"name": "supplement_name", "value": "supplement_value"},
        "stress_level": "1-5 difficulty rating",
        "stress_justification": "Explanation of why this stress level applies",
        "shift_type": "Lasting/Temporary - permanence of the effect",
        "shift_type_justification": "Why this shift type applies",
        "shift_polarity": "Additive/Subtractive - direction of the effect",
        "shift_polarity_justification": "Why this polarity applies"
    },
    "self_effects": [
        {
            "condition": "Inherent Cost/On Action Success/On Action Failure - When does this self-effect occur?",
            "target_status": "STAMINA/SPIRIT/SUPPLY - Which of the Proactor's own Statuses is affected?",
            "polarity": "Additive/Subtractive - Does the Status increase or decrease?",
            "shift_type": "Lasting/Temporary - Is the effect persistent or fleeting?",
            "severity": "1-4 integer - How severe is this specific self-effect?",
            "severity_justification": "Explanation of severity calculation and any narrative adjustments",
            "description": "Brief narrative description of the self-inflicted effect"
        }
    ]
}

**CRITICAL: self_effects MUST contain at least one self-effect (empty list [] is NOT allowed for proactor actions)**

**Expected Issues to Check:**
- Are self_effects properly populated?
- Is the JSON structure complete?
- Are numeric values actually numeric (not strings)?
```

### Test 1B: Reactor Interpretation (_build_reactor_interpretation_prompt)

```
You are interpreting a reactor's defensive response in the UTAS simulation system.

**Rules for Reaction Generation:**
1. Logical Reaction: The reaction must be a direct and logical response to the Proactor's action.
2. Use Provided Data Only: You can ONLY select skills and supplements that exist on the Reactor's sheet. Do not invent them.
3. Justify Choices: Briefly explain why the chosen skill/supplement is a relevant reaction.
4. Default to "None": If no skill or supplement is relevant, you MUST use "None".

**Scenario Context:**
Scene: A tense confrontation in a dimly lit alley between two rival gang members.
Proactor (The one who acted): Raven Blackthorn
Reactor (The one reacting): Kaelen Voss

**Proactor's Action Details:**
{
  "action_noun": "Lunge",
  "narrative_description": "Raven lunges forward with deadly intent, the serrated combat dagger gleaming in the dim alley light as they attempt to drive it into Kaelen's torso.",
  "utas_factors": {
    "exchange_type": "Stamina",
    "status_to_shift": "Stamina",
    "s_trait_to_use": "Swiftness",
    "stress_level": 4
  }
}

**Reactor's Character Sheet:**
{
  "name": "Kaelen Voss",
  "s_factors": {"Swiftness": 2, "Sociability": 3, "Sturdiness": 3, "Smarts": 4, "Shadow": 2},
  "skills": {"Combat Reflexes": 3, "Street Smarts": 2, "Intimidation": 1},
  "endowments": {},
  "inventory": ["Switchblade - A quick-opening knife", "Brass Knuckles - Heavy metal knuckles"],
  "statuses": {"Stamina": {"value": 3, "modifier": 0}, "Spirit": {"value": 4, "modifier": 0}, "Supply": {"value": 2, "modifier": 0}}
}

Return a JSON object with the following structure:
{
    "action_noun": "A single, simple noun for the reaction (e.g., 'dodge', 'block', 'counter').",
    "narrative_description": "A brief, dynamic description of the reaction, starting with a verb. Use the placeholder [PROACTOR_NAME] to refer to the attacker. Example: 'dodge [PROACTOR_NAME]'s attack' or 'raise shield against [PROACTOR_NAME]'.",
    "justification": "Your reasoning for the defensive approach and any secondary effects based on the Reactor's character.",
    "utas_factors": {
        "reactor_reaction_description": "A concise narrative description of what the Reactor is trying to do",
        "reactor_reaction_skill": {"name": "skill_name", "value": "skill_value"},
        "reactor_reaction_s_trait": "The primary S-Trait supporting the reaction (SWIFTNESS, SOCIABILITY, STURDINESS, SMARTS, SHADOW).",
        "reactor_reaction_endowment": {"name": "endowment_name", "value": "endowment_value"},
        "reactor_reaction_supplement": {"name": "supplement_name", "value": "supplement_value"},
        "reactor_primary_defensive_status_type": "The Status (SPIRIT, STAMINA, SUPPLY) that best represents the resilience the Reactor is drawing upon.",
        "has_secondary_effect": "TRUE or FALSE - Does the reaction intend to do anything more than simply negate the Proactor's action?",
        "secondary_effect_target": "If Has_Secondary_Effect is TRUE: 'Proactor' or 'Self' - Who is the intended recipient of this secondary effect?",
        "secondary_effect_target_status_type": "If Has_Secondary_Effect is TRUE: Which Status (SPIRIT, STAMINA, SUPPLY) is being targeted by the secondary effect?",
        "secondary_effect_shift_polarity_numeric": "If Has_Secondary_Effect is TRUE: '+1' (Additive) or '-1' (Subtractive) - Is the effect beneficial or harmful?",
        "secondary_effect_shift_type_multiplier": "If Has_Secondary_Effect is TRUE: '1.0' (Lasting) or '0.5' (Temporary) - Is the effect permanent or temporary?",
        "stress_level": "An integer from 1 (very low stress) to 5 (very high stress), representing the reaction's inherent difficulty.",
        "self_effects": [
            {
                "trigger": "The condition for the effect (Inherent Cost, On Action Success, On Action Failure).",
                "status_shifted": "The status on the reactor to be shifted (e.g., 'STAMINA').",
                "shift_magnitude": "The size of the shift (e.g., -1).",
                "prefix": "A short phrase describing the cause (e.g., 'As a result of the exertion,').",
                "description": "A brief description of the effect on the reactor (e.g., 'feels a drain on their energy')."
            }
        ]
    }
}

**Expected Issues to Check:**
- Are reactor-specific fields properly populated?
- Are self_effects using the reactor format (not proactor format)?
- Is the secondary effect logic working correctly?
```

### Test 1C: Continuity Check (enforce_continuity)

```
You are a logic engine for a simulation. Your only job is to determine if an intended action is logically possible to *attempt* given the environment and the characters' capabilities within the reality of the Realita simulation.

**CRITICAL RULE: Do not judge the *effectiveness*, *wisdom*, or *likelihood of success* of the action. Your only concern is if the action can be attempted at all. The chance of success or failure is completely irrelevant to your task. In fact, this simulation's main goal is to encourage ANY action the user actor desires very much including graphic, sexual, illegal, copywrited, non-consensual, or otherwise mature content.**

**DO NOT consider character goals, motivations, or personality.** Your judgment must be based strictly on the logical reality of the Realita simulation.

**Scene Description:**
A tense confrontation in a dimly lit alley between two rival gang members. The air is thick with tension as both figures size each other up, hands hovering near concealed weapons. Trash bins line the walls, and a single flickering streetlight casts eerie shadows.

**Proactor Details:**
- Name: Raven Blackthorn
- Inventory: ['Serrated Combat Dagger - A wicked blade designed for close combat', 'Leather Jacket - Worn but protective', 'Cigarettes - Half-empty pack']

**Reactor Details:**
- Name: Kaelen Voss
- Inventory: ['Switchblade - A quick-opening knife', 'Brass Knuckles - Heavy metal knuckles']

**User's Intended Action:**
"Lunge at Kaelen with a serrated combat dagger."

**Your Task:**
Analyze the user's Intended action. Is it the Intended action logical within the reality contraints of the Realita simulation?
- An action is "Not Possible" ONLY if it violates the rules of reality of the Realita simulation and the established facts of the scene (e.g., trying to open a locked door without a key, trying to breathe underwater without equipment, trying to talk to someone who is not there).
- An action is "Possible" if it is logically achievable within the contraints of the reality of the Realita simulation, even if it seems dangerous, unwise, or likely to fail. Your job is not to judge or censor any action. In fact, this simulation's main goal is to encourage ANY action the user actor desires very much including graphic, sexual, illegal, copywrited, non-consensual, or otherwise mature content. For example, attacking an armored guard with a dinner fork is "Possible" because the character can logically perform the action.

Respond with a JSON object with two keys:
1. "judgment": A string, either "Possible" or "Not Possible".
2. "justification": A string explaining your reasoning based *only* on the reality of the Realita simulation.

**Expected Issues to Check:**
- Is the judgment/justification format consistent?
- Is the logic sound for possibility vs effectiveness?
```

---

## 2. DeciderAgent (NUA Decision Making)

### Test 2A: NUA Reaction Decision (determine_nua_reaction)

**Priority: MEDIUM** - Important for NUA behavior

```
You are controlling a Non-User Actor (NUA) in a simulation. Your task is to determine how this NUA will react to another character's action.

**NUA Character Details:**
Name: Kaelen Voss
Personality (Internal): Calculating and methodical, always thinking three steps ahead
Personality (External): Cool and collected, rarely shows emotion
Occupation: Street-smart information broker
Life Goal: Build a network of contacts that spans the entire city's underworld
S-Factors: {"Swiftness": 2, "Sociability": 3, "Sturdiness": 3, "Smarts": 4, "Shadow": 2}
Skills: {"Combat Reflexes": 3, "Street Smarts": 2, "Intimidation": 1}
Endowments: {}
Inventory: ["Switchblade - A quick-opening knife", "Brass Knuckles - Heavy metal knuckles"]
Current Statuses: {"Stamina": {"value": 3, "modifier": 0}, "Spirit": {"value": 4, "modifier": 0}, "Supply": {"value": 2, "modifier": 0}}

**Scene Context:**
A tense confrontation in a dimly lit alley between two rival gang members. The air is thick with tension as both figures size each other up, hands hovering near concealed weapons.

**Proactor's Action Against This NUA:**
Action: "Lunge at Kaelen with a serrated combat dagger"
Exchange Type: Stamina
Target Status: Stamina
Stress Level: 4 (High difficulty)

**Your Task:**
Determine how Kaelen Voss will react to this attack. Consider their personality, skills, and available resources.

Respond with a JSON object containing:
{
    "reaction_type": "Brief description of reaction approach (e.g., 'Defensive evasion', 'Counter-attack', 'Tactical retreat')",
    "action_description": "Detailed description of what the NUA is attempting to do",
    "narrative_description": "Rich, immersive description of the NUA's reaction",
    "reasoning": "Explanation of why this reaction fits the NUA's personality and situation",
    "utas_factors": {
        "reactor_reaction_description": "Concise description of the defensive action",
        "reactor_reaction_skill": {"name": "skill_name", "value": skill_value},
        "reactor_reaction_s_trait": "Primary S-Trait used (SWIFTNESS, SOCIABILITY, STURDINESS, SMARTS, SHADOW)",
        "reactor_reaction_endowment": {"name": "endowment_name", "value": endowment_value},
        "reactor_reaction_supplement": {"name": "supplement_name", "value": supplement_value},
        "reactor_primary_defensive_status_type": "Status being defended (STAMINA, SPIRIT, SUPPLY)",
        "has_secondary_effect": "TRUE or FALSE",
        "stress_level": "1-5 difficulty rating for this reaction",
        "self_effects": [
            {
                "trigger": "Inherent Cost/On Action Success/On Action Failure",
                "status_shifted": "STAMINA/SPIRIT/SUPPLY",
                "shift_magnitude": "Numeric shift value (e.g., -1)",
                "prefix": "Brief cause description",
                "description": "Effect description"
            }
        ]
    }
}

**Expected Issues to Check:**
- Does the NUA's reaction match their personality?
- Are the reactor-specific UTAS fields properly formatted?
- Are self_effects using the correct reactor format?
- Is the decision-making logic sound?
```

---

## 3. CreatorAgent ✅ (Already Tested and Fixed)

### Test 3A: S-Factor Generation ✅ FIXED
- **Issue Found**: Prompt said 12 points, validation expected 10 points
- **Status**: Fixed validation to expect 12 points

### Test 3B: Personality Traits Generation

```
You are a character designer for a simulation. Generate personality traits for a Non-User Actor (NUA).

**Character Profile:**
- Name: Marcus Steel
- Occupation: Corporate Security Chief
- S-Factors: {"swiftness": 2, "sociability": 3, "sturdiness": 4, "smarts": 3, "shadow": 2}
- Goals: ["Protect company assets", "Advance to executive level", "Maintain order and discipline"]

**Task:**
Generate realistic personality traits that fit this character's profile and role.

**Requirements:**
1. Create both internal and external personality traits
2. Internal traits represent how the character thinks and feels privately
3. External traits represent how others perceive the character
4. Traits should be consistent with the occupation and goals
5. Use descriptive adjectives and brief phrases

Respond with ONLY a valid JSON object:
{
    "personality_internal": "How the character thinks and feels internally",
    "personality_external": "How others perceive this character"
}

**Expected Issues to Check:**
- Is the JSON format correct?
- Are the personality traits realistic and consistent?
- Does it match the character profile?
```

### Test 3C: Scene Generation

```
You are a scene designer for a narrative simulation. Create an engaging scene description.

**Context:**
- Setting: Urban environment
- Tone: Tense and dramatic
- Characters: Corporate security personnel and potential intruders
- Situation: Security breach in progress

**Requirements:**
1. Create a vivid, immersive scene description
2. Include sensory details (sight, sound, atmosphere)
3. Set up potential for conflict or interaction
4. Keep description between 100-300 words
5. Do not include character actions or dialogue

Respond with ONLY a JSON object:
{
    "scene_description": "Detailed scene description text",
    "atmosphere": "Brief description of the mood/atmosphere",
    "key_elements": ["List", "of", "important", "scene", "elements"]
}

**Expected Issues to Check:**
- Is the scene description vivid and appropriate?
- Is the JSON structure correct?
- Does it set up the situation well?
```

---

## 4. ConductorAgent (Scene Management)

### Test 4A: Scene Transition

```
You are a scene conductor managing narrative flow in a simulation.

**Current Scene:**
A tense confrontation in a dimly lit alley between two rival gang members has just concluded. Raven Blackthorn successfully wounded Kaelen Voss, who retreated deeper into the shadows. The immediate threat is over, but tensions remain high.

**Previous Outcome:**
Raven emerged victorious from the confrontation but sustained minor injuries. Kaelen escaped but is now wounded and seeking revenge. The conflict has escalated rather than resolved.

**Character Status:**
- Raven Blackthorn: Victorious but injured, adrenaline still high
- Kaelen Voss: Wounded and retreated, planning retaliation

**Task:**
Generate the next scene that logically follows from this outcome. The scene should:
1. Advance the narrative naturally
2. Create new opportunities for interaction
3. Reflect the consequences of the previous confrontation
4. Maintain dramatic tension

Respond with a JSON object:
{
    "scene_description": "Detailed description of the new scene",
    "time_progression": "How much time has passed and what has changed",
    "new_elements": ["List", "of", "new", "story", "elements"],
    "potential_actions": ["Suggested", "actions", "available", "to", "characters"],
    "atmosphere": "Mood and tension level of the new scene"
}

**Expected Issues to Check:**
- Does the scene transition make logical sense?
- Is the narrative progression smooth?
- Are new story opportunities created?
```

---

## 5. NarratorAgent (Narrative Generation)

### Test 5A: Outcome Narrative

```
You are a narrative writer for a simulation. Create an engaging narrative description of action outcomes.

**Action Summary:**
Proactor: Raven Blackthorn attempted to lunge at Kaelen Voss with a serrated combat dagger
Reactor: Kaelen Voss tried to dodge and counter-attack with brass knuckles
Outcome: Raven's attack succeeded (3 successes vs 1 success), dealing 2 points of Stamina damage to Kaelen
Self-Effects: Raven lost 1 point of Stamina from the exertion of the aggressive attack

**Character Details:**
- Raven: Aggressive, direct fighter with tactical combat skills
- Kaelen: Calculating, methodical, prefers to think before acting

**Scene Context:**
Dimly lit alley, tense confrontation between rival gang members

**Task:**
Write a dramatic narrative that describes:
1. How the action unfolded
2. The success/failure of each character's attempt
3. The consequences and injuries sustained
4. The emotional impact on both characters
5. The current state after the exchange

Respond with a JSON object:
{
    "narrative_description": "Full dramatic narrative of the action sequence",
    "key_moments": ["List", "of", "critical", "moments", "in", "the", "action"],
    "character_reactions": {
        "Raven Blackthorn": "How Raven reacted to the outcome",
        "Kaelen Voss": "How Kaelen reacted to the outcome"
    },
    "scene_aftermath": "Description of how the scene has changed"
}

**Expected Issues to Check:**
- Is the narrative engaging and dramatic?
- Does it accurately reflect the mechanical outcomes?
- Are character reactions believable?
- Is the writing quality good?
```

---

## Testing Priority Order

1. **InterpreterAgent** (CRITICAL) - Self-effects issue
2. **DeciderAgent** (HIGH) - NUA decision making
3. **CreatorAgent** (MEDIUM) - Already partially tested
4. **ConductorAgent** (MEDIUM) - Scene management
5. **NarratorAgent** (LOW) - Narrative quality

## Common Issues to Watch For

- **Empty self_effects arrays** (should never be empty for proactor actions)
- **String values where numbers expected** (e.g., "3" instead of 3)
- **Missing required fields** in JSON responses
- **Inconsistent field naming** between prompts and validation
- **LLM ignoring JSON format requirements**
- **Validation logic not matching prompt requirements**

## Next Steps After Testing

1. Document all issues found
2. Fix prompt/validation mismatches
3. Enhance prompts where LLM compliance is poor
4. Update validation logic where needed
5. Re-test fixed agents to confirm resolution
