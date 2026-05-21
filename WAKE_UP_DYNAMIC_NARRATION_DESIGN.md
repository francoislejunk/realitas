# Dynamic Wake-Up Narration Design Document

**Date:** 2026-02-12
**Task #22:** Implement dynamic wake-up scene narration with personality
**Status:** Design Phase

---

## Problem Statement

**Current Issue (agents/creator_agent.py:3377-3396):**
All characters wake with generic template:
```
"Your eyes [shoot/slowly/flutter] open [immediate sensory detail]..."
```

**Problems:**
1. Same template for all personalities (angry person wakes same as calm person)
2. No S-factor consideration (low perception character sees same details as high perception)
3. No emotional state integration (anxious vs. confident waking)
4. No occupation/context awareness (soldier wakes same as artist)
5. Missed immersion opportunity - no character differentiation

---

## Solution Design

### Approach: Dynamic Wake-Up Template Generation

Create `_generate_dynamic_wake_up_opening()` method that:
1. Analyzes UA personality traits (internal + external)
2. Considers S-factors (Perception, Sociability, Smarts, Shadow, Strength)
3. Integrates emotional state and occupation
4. Generates varied, personality-appropriate opening phrases

### Implementation Location

**File:** `agents/creator_agent.py`
**Line:** Add new method after `_get_cultural_context()` (around line 3115)
**Integration:** Call from `_get_initial_scene_prompt()` to replace hardcoded template

---

## Wake-Up Variations by Personality

### 1. Internal Personality Traits

| Trait | Wake-Up Style | Example Opening |
|-------|---------------|-----------------|
| Determined / Focused | Immediate alertness | "Your eyes snap open with sudden clarity..." |
| Anxious / Worried | Gradual, hesitant | "Your eyes slowly flutter open as uncertainty creeps in..." |
| Calm / Peaceful | Smooth, natural | "Your eyes gently open as consciousness returns..." |
| Aggressive / Angry | Abrupt, harsh | "Your eyes shoot open with a  sharp intake of breath..." |
| Paranoid / Suspicious | Alert, scanning | "Your eyes dart open, already scanning for threats..." |
| Depressed / Melancholic | Reluctant, heavy | "Your eyes drag open, heavy with exhaustion..." |
| Confident / Bold | Authoritative, immediate | "Your eyes flash open, ready to face whatever comes..." |

### 2. External Personality Traits

| Trait | Environmental Awareness | Example Follow-Up |
|-------|------------------------|-------------------|
| Observant / Perceptive | Notices fine details | "...You immediately notice the dust motes drifting in the light..." |
| Cautious / Careful | Checks surroundings first | "...You take a moment to assess your surroundings before moving..." |
| Social / Friendly | Awareness of people presence | "...You sense the absence of others in the space..." |
| Withdrawn / Isolated | Focuses on self first | "...Your first thought is cataloging your own state..." |
| Impulsive / R eckless | Immediate action | "...You're already reaching for your gear before fully awake..." |

### 3. S-Factor Integration

| S-Factor | Influence on Wake-Up | Example Modification |
|----------|---------------------|----------------------|
| **Perception** High (4-5) | Notices subtle details | "...picking up the faint scent of ozone and distant traffic..." |
| **Perception** Low (1-2) | Basic awareness only | "...the room blurry until your vision adjusts..." |
| **Strength** High (4-5) | Physical vitality | "...muscles coiled and ready..." |
| **Strength** Low (1-2) | Physical weakness | "...your body protesting the movement..." |
| **Smarts** High (4-5) | Analytical waking | "...your mind immediately categorizing the environment..." |
| **Smarts** Low (1-2) | Disoriented waking | "...taking a moment to orient yourself..." |
| **Shadow** High (4-5) | Suspicious waking | "...instinctively checking for hidden observers..." |
| **Sociability** High (4-5) | Social awareness | "...listening for signs of nearby company..." |

### 4. Occupation Context

| Occupation Type | Wake-Up Flavor | Example |
|----------------|----------------|---------|
| Military / Security | Combat-ready | "Your eyes snap open, instantly alert, hand reaching instinctively toward where your sidearm would be..." |
| Medical / Healer | Clinical awareness | "Your eyes open methodically, automatically cataloging your physical state - pulse steady, breathing normal..." |
| Artist / Creative | Sensory focus | "Your eyes drift open, drawn first to the play of morning light across the ceiling..." |
| Criminal / Shadow | Paranoid vigilance | "Your eyes slit open cautiously, checking the room for changes before fully waking..." |
| Laborer / Physical | Body-first | "Your eyes open as your muscles remind you of yesterday's exertions..." |
| Academic / Scholar | Mental first | "Your eyes open, mind already churning through the problems you fell asleep considering..." |

---

## Template Structure

### Base Template Formula

```
[EYE_OPENING_VERB] + [IMMEDIATE_REACTION] + [SENSORY_DETAIL_1] + [PERCEPTUAL_ACTION] + [SENSORY_DETAIL_2] + [CHARACTER_DETAIL] + [ATMOSPHERIC_TOUCH]
```

### Component Generation Rules

1. **EYE_OPENING_VERB** (influenced by Internal Personality)
   - Determined/Confident: "snap open", "flash open", "shoot open"
   - Calm/Peaceful: "gently open", "slowly open", "drift open"
   - Anxious/Fearful: "flutter open", "hesitantly open", "crack open"
   - Aggressive/Angry: " burst open", "jolt open", "slam open"

2. **IMMEDIATE_REACTION** (influenced by Perception + Internal Personality)
   - High Perception + Analytical: "with sudden clarity"
   - High Perception + Cautious: "already scanning for threats"
   - Low Perception: "blurry and unfocused at first"
   - Anxious: "as uncertainty creeps in"
   - Peaceful: "as consciousness gently returns"

3. **SENSORY_DETAIL_1** (influenced by Perception S-Factor)
   - High Perception (4-5): 2-3 specific sensory details (visual + audio/smell)
   - Medium Perception (3): 1-2 basic details (visual + audio OR smell)
   - Low Perception (1-2): 1 obvious detail only

4. **PERCEPTUAL_ACTION** (influenced by External Personality)
   - Observant: "You notice...", "You immediately see..."
   - Cautious: "You carefully scan...", "You check..."
   - Impulsive: "You're already reaching for...", "You sit up quickly..."
   - Withdrawn: "You take stock of...", "You assess your own state..."

5. **CHARACTER_DETAIL** (influenced by Occupation + Personality)
   - ONE subtle action/thought that shows character
   - NEVER explain WHY (avoid "due to", "because", "reflecting")
   - Show, don't tell

6. **ATMOSPHERIC_TOUCH** (influenced by World Context + Setting)
   - Use RAG worldbuilding context
   - Period-appropriate technology/culture
   - Sets mood for exploration

---

## Implementation Pseudocode

```python
def _generate_dynamic_wake_up_opening(
    self,
    actor: UserActor,
    world_context: str,
    setting_hints: str = ""
) -> str:
    """
    Generate personality-specific wake-up opening.

    Args:
        actor: UserActor with personality, S-factors, occupation
        world_context: RAG-generated world setting details
        setting_hints: Optional location hints (interior vs. exterior)

    Returns:
        Personality-tailored opening paragraph (2-4 sentences)
    """
    # 1. Extract personality traits
    personality_internal = actor.sheet.personality_traits.get('internal', 'Determined and focused')
    personality_external = actor.sheet.personality_traits.get('external', 'Calm and observant')

    # 2. Get S-factor values
    perception = actor.sheet.s_factors.get_factor(SFactorType.PERCEPTION)
    smarts = actor.sheet.s_factors.get_factor(SFactorType.SMARTS)
    shadow = actor.sheet.s_factors.get_factor(SFactorType.SHADOW)
    strength = actor.sheet.s_factors.get_factor(SFactorType.STRENGTH)

    # 3. Classify personality type for wake-up style
    wake_up_style = _classify_wake_up_style(personality_internal)
    # Returns: "alert", "gradual", "aggressive", "cautious", "reluctant", "peaceful"

    # 4. Generate eye-opening verb
    eye_verb = _get_eye_opening_verb(wake_up_style, personality_internal)

    # 5. Generate immediate reaction
    immediate_reaction = _get_immediate_reaction(
        wake_up_style,
        perception,
        personality_internal,
        shadow
    )

    # 6. Generate sensory details (count based on Perception)
    sensory_count = 3 if perception >= 4 else (2 if perception >= 3 else 1)
    sensory_details = _generate_sensory_details(
        world_context,
        sensory_count,
        perception,
        setting_hints
    )

    # 7. Generate perceptual action
    perceptual_action = _get_perceptual_action(
        personality_external,
        perception,
        wake_up_style
    )

    # 8. Generate character detail (subtle action, no explanation)
    character_detail = _generate_character_detail(
        actor.sheet.occupation,
        personality_internal,
        strength,
        smarts
    )

    # 9. Assemble template
    opening = f"Your eyes {eye_verb} {immediate_reaction}. {sensory_details} {perceptual_action}. {character_detail}"

    return opening
```

---

## Example Outputs

### Example 1: Confident Military Character
**Profile:**
- Occupation: Former soldier
- Internal: Determined, confident
- External: Observant, cautious
- Perception: 4, Strength: 4, Shadow: 3

**Generated Opening:**
```
Your eyes snap open with sudden clarity, instinctively scanning for threats. The acrid smell of gun oil and metal fills the cramped workshop, fluorescent lights buzzing overhead casting harsh shadows across scattered tools. You immediately notice three exits - the main door to your left, a narrow window above the workbench, and a service hatch in the floor partially obscured by crates.  Your hand moves automatically to check for your sidearm before you fully register your surroundings.
```

### Example 2: Anxious Artist with Low Perception
**Profile:**
- Occupation: Struggling painter
- Internal: Anxious, worried
- External: Withdrawn, introspective
- Perception: 2, Smarts: 4, Shadow: 1

**Generated Opening:**
```
Your eyes flutter open hesitantly, vision blurry at first as shapes slowly resolve into focus. The familiar clutter of your studio gradually emerges - canvases stacked against walls, tubes of paint scattered across the floor, afternoon light filtering through grimy windows. You take a moment to orient yourself, your mind still tangled in half-remembered dreams. Your fingers unconsciously twist the paint-stained rag you fell asleep clutching.
```

### Example 3: Paranoid Criminal
**Profile:**
- Occupation: Fence / Black market dealer
- Internal: Paranoid, suspicious
- External: Cautious, defensive
- Perception: 5, Shadow: 5, Sociability: 1

**Generated Opening:**
```
Your eyes crack open, already scanning the room for changes - the door still barred, window intact, security monitor still displaying its four green feeds. You catch the faint scent of rain-soaked asphalt drifting through the ventilation grate, mixing with stale cigarette smoke. You notice the slight displacement of the chair you'd wedged against the door - someone tried it while you slept. Your pulse quickens as you reach beneath the thin mattress, fingers confirming your knife is still there.
```

### Example 4: Peaceful Scholar
**Profile:**
- Occupation: Librarian / Archivist
- Internal: Calm, thoughtful
- External: Friendly, helpful
- Perception: 3, Smarts: 5, Sociability: 4

**Generated Opening:**
```
Your eyes gently open as consciousness returns, the familiar scent of old paper and dust bringing comfort. Soft morning light filters through the archive's high windows, illuminating thousands of spines arranged in careful  rows stretching into shadow. You notice the reference desk where you left your reading glasses, the cart of unshelved volumes waiting for attention, and the narrow staircase spiraling up to the rare books collection. Your mind immediately returns to the manuscript puzzle you were working on yesterday.
```

---

## Integration Steps

### Step 1: Create Helper Methods

Add to `agents/creator_agent.py` after `_get_cultural_context()`:

```python
def _classify_wake_up_style(self, personality_internal: str) -> str:
    """Classify personality into wake-up style category."""
    # LLM call or keyword mapping
    # Returns: "alert", "gradual", "aggressive", "cautious", "reluctant", "peaceful"

def _get_eye_opening_verb(self, wake_up_style: str, personality_internal: str) -> str:
    """Get personality-appropriate eye-opening verb."""
    # Returns verb phrase like "snap open", "flutter open", etc.

def _get_immediate_reaction(self, wake_up_style: str, perception: int,
                           personality_internal: str, shadow: int) -> str:
    """Generate immediate reaction after eyes open."""
    # Returns reaction phrase

def _generate_sensory_details(self, world_context: str, count: int,
                             perception: int, setting_hints: str) -> str:
    """Generate sensory details based on perception level."""
    # Returns 1-3 sensory details

def _get_perceptual_action(self, personality_external: str,
                          perception: int, wake_up_style: str) -> str:
    """Get perceptual action verb (look, notice, scan, etc.)."""
    # Returns action phrase

def _generate_character_detail(self, occupation: str, personality_internal: str,
                               strength: int, smarts: int) -> str:
    """Generate ONE subtle character-revealing action."""
    # Returns brief action (no explanation of why)

def _generate_dynamic_wake_up_opening(self, actor: UserActor,
                                      world_context: str) -> str:
    """Main method - generates full opening paragraph."""
    # Orchestrates above helpers
```

### Step 2: Modify `_get_initial_scene_prompt()`

Replace hardcoded template at lines 3377-3396 with call to new method:

```python
# Generate personality-specific wake-up opening
dynamic_wake_up = self._generate_dynamic_wake_up_opening(actor, world_context)

# Update the prompt template
wake_up_examples = f"""
**Dynamic Opening Example (Generated from Character Personality):**
{dynamic_wake_up}

**Your Task:**
Create a similar personality-driven opening that reflects {actor.name}'s traits:
- Internal: {personality_internal}
- External: {personality_external}
- Perception: {perception}
- Notable attributes: {s_factors_note}

Use the dynamic approach above, not a generic template.
"""
```

### Step 3: Update JSON Schema Instructions

Change from:
```json
"setting": "A concise description (4-6 sentences) that MUST START with 'Your eyes [shoot/slowly/flutter] open...'"
```

To:
```json
"setting": "A concise description (4-6 sentences) with a personality-appropriate opening that shows how {actor.name} wakes based on their traits. Use the example above as a guide - vary the verb, details, and style based on character."
```

---

## Testing Strategy

### Test Cases

1. **High Perception Character** - Should notice 3+ sensory details
2. **Low Perception Character** - Should notice 1 basic detail
3. **Anxious Character** - Should have hesitant, cautious waking
4. **Confident Character** - Should have immediate, alert waking
5. **Military Occupation** - Should show combat awareness
6. **Artist Occupation** - Should show sensory focus
7. **High Shadow Character** - Should show paranoia/vigilance
8. **Low Strength Character** - Should show physical weakness

### Success Criteria

- ✅ No two characters with different personalities wake the same way
- ✅ S-factors influence description depth and style
- ✅ Occupation flavors the character detail
- ✅ No "explaining" character actions (show, don't tell)
- ✅ Maintains active voice and present tense
- ✅ 4-6 sentence length maintained
- ✅ Integrates world context appropriately

---

## Potential Challenges

### Challenge 1: LLM Call Performance
**Issue:** Each wake-up generation requires parsing personality, making decisions
**Solution:** Use structured template generation, not full LLM call for every component

### Challenge 2: Over-Engineering
**Issue:** Too many variations could become repetitive or formulaic
**Solution:** Keep it simple - focus on 5-7 key personality/S-factor combinations

### Challenge 3: Consistency
**Issue:** Generated openings might vary too much in quality
**Solution:** Provide strong examples in prompts, use temperature=0.3 for consistency

---

## Implementation Priority

### Phase 1: Core Method (HIGH PRIORITY)
- Create `_generate_dynamic_wake_up_opening()` method
- Implement basic personality mapping (alert/gradual/cautious/aggressive/peaceful)
- Integrate with `_get_initial_scene_prompt()`

### Phase 2: S-Factor Integration (MEDIUM PRIORITY)
- Add Perception-based sensory detail count
- Add Shadow-based vigilance
- Add Strength-based physical state

### Phase 3: Occupation Integration (LOW PRIORITY)
- Add occupation-specific character details
- Refine based on user feedback

---

## Code Files to Modify

1. **agents/creator_agent.py**
   - Add helper methods (lines 3115-3200)
   - Modify `_get_initial_scene_prompt()` (lines 3375-3400)
   - Update JSON schema instructions (line 3396)

2. **Test File (NEW): test_wake_up_dynamic.py**
   - Test personality classification
   - Test S-factor influence
   - Test occupation integration
   - Test output variety

---

## Expected Impact

### User Experience
- **Before:** "All my characters wake up exactly the same way"
- **After:** "My anxious artist wakes differently than my confident soldier!"

### Immersion
- Characters feel more distinct from  the first moment
- Personality traits have immediate mechanical impact
- S-factors influence narrative perception

### Emergence
- Players discover character personality through narration
- Subtle hints about character state without exposition
- Natural integration of character sheet into fiction

---

**Next Step:** Implement Phase 1 (Core Method)
**Estimated Time:** 2-3 hours
**Files to Create:** 1 new method set, 1 test file
**Files to Modify:** 1 (creator_agent.py)
