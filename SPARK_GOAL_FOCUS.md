# SPARK System - Goal-Focused Design ✅

## Core Principle

**SPARKs focus on GOALS (strategic), not TASKS (tactical)**

## What This Means

### ✅ SPARKs Should Relate To:

**GOALS** - Long-term, life-defining objectives:
- "Find my missing sister"
- "Avenge my family's death"
- "Build a successful business"
- "Escape from the cult"

**Example SPARK for Goal "Find my missing sister":**
```
A nervous informant approaches you at the diner, claiming to have 
information about your sister's whereabouts. He keeps glancing at 
the door, clearly afraid of being seen talking to you.
```

This SPARK:
- ✅ Directly relates to the GOAL
- ✅ Offers strategic opportunity (information)
- ✅ Creates meaningful choice (trust him? ignore him?)
- ✅ Could advance goal progress

### ❌ SPARKs Should NOT Focus On:

**TASKS** - Immediate, tactical needs:
- "Find food"
- "Get some rest"
- "Search the room"
- "Talk to the bartender"

**Bad SPARK (task-focused):**
```
You notice the diner has a special on burgers today.
```

This is task-focused:
- ❌ Only addresses immediate need (hunger)
- ❌ No strategic value
- ❌ Doesn't advance goals
- ❌ Just a tactical action

## Implementation

### Updated Spark Generator (`spark_generator.py`)

**1. Goals Included in Prompt** (line 102):
```python
Goals: {self._format_ua_goals(ua_actor)}
```

**Example Output:**
```
Goals: Find my missing sister [life_defining, 35% progress]; 
       Survive in the city [major, 60% progress]
```

**2. Goal-Focused Guidelines** (lines 116-122):
```
**CREATIVE GUIDELINES:**
- **GOAL-FOCUSED**: SPARKs should relate to the UA's long-term GOALS, not immediate tasks
- Analyze the UA's goals and create SPARKs that could advance, complicate, or test those goals
- **STRATEGIC OPPORTUNITIES**: SPARKs should offer meaningful choices related to goals, 
  not just tactical actions
```

**3. Helper Method** (lines 164-189):
```python
def _format_ua_goals(self, ua_actor: Any) -> str:
    """
    Format UA's long-term GOALS for SPARK generation.
    SPARKs should focus on GOALS (strategic), not tasks (tactical).
    """
    # Returns formatted goals with importance and progress
    # Example: "Find my sister [life_defining, 35% progress]"
```

## SPARK Types and Goal Relevance

### High Goal Relevance

**1. Goal Advancement SPARKs**
- Provide information about the goal
- Introduce allies who can help
- Reveal obstacles to overcome
- Example: "Informant with sister's location"

**2. Goal Complication SPARKs**
- Create moral dilemmas related to the goal
- Introduce competing priorities
- Test character's commitment
- Example: "Helping someone else delays finding sister"

**3. Goal Testing SPARKs**
- Challenge the character's methods
- Question their motivations
- Force difficult choices
- Example: "Sister's kidnapper offers deal"

### Medium Goal Relevance

**4. Indirect Goal SPARKs**
- Build resources needed for goal
- Develop relationships that might help later
- Gather skills or knowledge
- Example: "Detective offers to teach investigation skills"

### Low Goal Relevance (Avoid)

**5. Pure Survival/Maintenance**
- Just addressing basic needs
- No strategic value
- Example: "Restaurant has food" ❌

**6. Random Events**
- No connection to goals
- Just "something happening"
- Example: "Car drives by" ❌

## Examples

### Character: Detective Sarah Chen
**Goal**: "Find my kidnapped sister Emily" [LIFE_DEFINING, 35% progress]

#### ✅ GOOD SPARKs (Goal-Focused)

**SPARK 1: Information Opportunity**
```
A street informant you recognize from your beat approaches cautiously. 
"Detective Chen," he whispers, "I heard you're looking for your sister. 
I might know something, but it's dangerous to talk here."
```
- Directly advances goal
- Strategic choice: trust him or not?
- Could increase progress

**SPARK 2: Moral Dilemma**
```
You spot a young girl being harassed by thugs in an alley. She reminds 
you painfully of Emily. Helping her would delay your investigation by 
hours, but leaving her feels wrong.
```
- Tests commitment to goal
- Moral complexity
- Meaningful choice

**SPARK 3: Resource Opportunity**
```
A retired FBI agent recognizes you from the news coverage of Emily's case. 
"I worked trafficking cases for 20 years," he says. "I might be able to 
help, if you're willing to share what you know."
```
- Builds resources for goal
- Strategic alliance
- Long-term value

#### ❌ BAD SPARKs (Task-Focused)

**BAD SPARK 1: Pure Survival**
```
You notice a diner advertising a lunch special. Your stomach growls.
```
- Only addresses hunger (task)
- No goal relevance
- Purely tactical

**BAD SPARK 2: Random Event**
```
A street performer is juggling nearby, drawing a small crowd.
```
- No connection to finding sister
- Just environmental detail
- No strategic value

**BAD SPARK 3: Trivial Interaction**
```
The bartender asks if you want another drink.
```
- Immediate/tactical only
- Doesn't advance goal
- No meaningful choice

## LLM Prompt Strategy

The Spark Generator now tells the LLM:

1. **Here are the UA's GOALS** (with importance and progress)
2. **Create SPARKs that relate to these GOALS**
3. **Focus on strategic opportunities, not tactical actions**
4. **Advance, complicate, or test the goals**

This ensures SPARKs are:
- ✅ Meaningful to the character's journey
- ✅ Strategically valuable
- ✅ Worth the player's attention
- ✅ Advance the story, not just fill time

## Goal Progress Through SPARKs

SPARKs can affect goal progress:

```
Goal: "Find my missing sister" [35% progress]
    ↓
SPARK: Informant provides lead
    ↓
UA chooses to follow the lead
    ↓
Investigation advances
    ↓
Goal: "Find my missing sister" [45% progress]
```

**Tasks don't affect goal progress:**
```
Goal: "Find my missing sister" [35% progress]
    ↓
Task: "Find food"
    ↓
UA eats at diner
    ↓
Goal: "Find my missing sister" [35% progress]  ← No change
```

## Summary

### The Distinction

**GOALS** (SPARKs focus here):
- Strategic, long-term
- Life-defining
- Resistant to change
- Progress tracked
- **SPARKs should advance, complicate, or test these**

**TASKS** (SPARKs ignore these):
- Tactical, immediate
- Everyday needs
- Change constantly
- Completion tracked
- **SPARKs should NOT focus on these**

### Implementation Status

✅ **Spark Generator updated** to include goals in prompt
✅ **Guidelines added** emphasizing goal-focus
✅ **Helper method created** to format goals with importance/progress
✅ **Creative direction** explicitly states "focus on GOALS, not tasks"

SPARKs will now generate meaningful, goal-relevant encounters that advance the character's strategic objectives rather than just addressing immediate tactical needs!
