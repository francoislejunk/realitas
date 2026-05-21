# SPARK Types and Urgency System

## Three SPARK Categories

### 1. **ACTOR ARRIVAL**
**What**: A new NUA arrives on scene with goal-relevant purpose

**Examples by Urgency:**

#### LOW Urgency (Gentle Opportunity)
```
A street vendor you recognize waves at you from his cart. He mentioned 
last week he might have information about your sister's case.
```
- **Persistence**: 1 turn, 0.1 hours
- **Behavior**: Fades quickly if ignored
- **Tone**: Casual, non-pressing
- **UA can**: Talk to him, wave back, ignore completely

#### MEDIUM Urgency (Notable Opportunity)
```
A nervous informant approaches you at the diner, glancing at the door. 
'Detective,' he whispers, 'I have information about your sister, but 
I can't stay long.'
```
- **Persistence**: 2 turns, 0.25 hours
- **Behavior**: Lingers but won't force interaction
- **Tone**: Anxious, time-sensitive but not critical
- **UA can**: Talk to him, ask questions, tell him to wait, ignore

#### HIGH Urgency (Urgent Situation)
```
A bloodied man stumbles toward you from an alley. 'You're looking for 
Emily Chen, right?' he gasps. 'They're moving her tonight. You have 
to—' He collapses.
```
- **Persistence**: 3+ turns, 0.5+ hours
- **Behavior**: Demands attention, may escalate if ignored
- **Tone**: Critical, immediate stakes
- **UA can**: Help him, question him, call for help, walk away

---

### 2. **INCIDENT**
**What**: An event or situation happens nearby that relates to the UA's goal

**Examples by Urgency:**

#### LOW Urgency (Subtle Clue)
```
Through the warehouse window, you notice the same black van that 
witnesses mentioned. It's parked but empty.
```
- **Persistence**: 1 turn, 0.1 hours
- **Behavior**: Static observation, easily missed
- **Tone**: Ambient detail, investigative hook
- **UA can**: Investigate van, note it down, ignore it

#### MEDIUM Urgency (Active Situation)
```
Two figures argue near a black van outside - the same model from 
witness reports. One pulls out a briefcase and checks his watch 
impatiently.
```
- **Persistence**: 2 turns, 0.25 hours
- **Behavior**: Ongoing activity, window of opportunity
- **Tone**: Developing situation, time-limited
- **UA can**: Watch them, approach, follow them, ignore

#### HIGH Urgency (Crisis Event)
```
Gunshots echo from the warehouse across the street. You see figures 
dragging someone toward a van - the same model from your sister's case.
```
- **Persistence**: 3+ turns, 0.5+ hours
- **Behavior**: Escalating crisis, may worsen if ignored
- **Tone**: Emergency, high stakes
- **UA can**: Intervene, call police, observe, flee

---

### 3. **EUREKA**
**What**: A realization, discovery, or connection the UA makes over time

**Examples by Urgency:**

#### LOW Urgency (Interesting Pattern)
```
As you review your notes, you notice the disappearances all happened 
on the 15th of each month. Your sister vanished March 15th.
```
- **Persistence**: 1 turn, 0.1 hours
- **Behavior**: Intellectual observation, can be filed away
- **Tone**: Curious discovery, investigative insight
- **UA can**: Investigate pattern, note it, dismiss it

#### MEDIUM Urgency (Actionable Insight)
```
The dates suddenly click - all disappearances on the 15th. Your sister: 
March 15th. The next 15th is in three days, and you remember the 
informant mentioning 'the next shipment.'
```
- **Persistence**: 2 turns, 0.25 hours
- **Behavior**: Meaningful connection with time pressure
- **Tone**: Breakthrough moment, window to act
- **UA can**: Plan for the 15th, investigate now, ignore

#### HIGH Urgency (Critical Realization)
```
The pattern hits you like ice water - all on the 15th. Your sister: 
March 15th. Today is the 14th. The warehouse receipt in your hand is 
dated for tomorrow night.
```
- **Persistence**: 3+ turns, 0.5+ hours
- **Behavior**: Urgent revelation, immediate action window
- **Tone**: Race against time, critical deadline
- **UA can**: Act immediately, prepare for tomorrow, ignore

---

## Urgency Level Mechanics

### Purpose
**Urgency determines PERSISTENCE, not FORCE**

- Urgency affects how long the SPARK remains active if ignored
- It does NOT force the UA to engage
- Even HIGH urgency SPARKs are completely optional

### Persistence Behavior

| Urgency | Turns | Hours | Behavior | Escalation |
|---------|-------|-------|----------|------------|
| **LOW** | 1 | 0.1 | Fades quickly, gentle opportunity | No |
| **MEDIUM** | 2 | 0.25 | Lingers moderately, notable event | No |
| **HIGH** | 3+ | 0.5+ | Persists strongly, may escalate | Yes |

### What "Escalation" Means

**HIGH urgency SPARKs may escalate if ignored:**

**Example - Actor Arrival:**
```
Turn 1: Bloodied man collapses, gasping about your sister
[UA ignores, continues searching warehouse]

Turn 2: Man's breathing becomes labored, he's losing consciousness
[UA still ignores]

Turn 3: Man stops breathing. Opportunity lost.
```

**Example - Incident:**
```
Turn 1: Gunshots from warehouse, figures dragging someone
[UA ignores, walks away]

Turn 2: Van speeds off, tires screeching
[UA still ignoring]

Turn 3: Van is gone. Lead lost.
```

**Example - Eureka:**
```
Turn 1: Realize today is the 14th, warehouse receipt for tomorrow
[UA ignores, continues other investigation]

Turn 2: Time passes, it's now late evening on the 14th
[UA still not acting]

Turn 3: It's the 15th. Whatever was planned may have already happened.
```

**Key Point**: Escalation creates **consequences for inaction**, not **forced engagement**. The UA can still choose to let the SPARK resolve without them.

---

## Goal Relevance

**All SPARKs must relate to the UA's GOAL, regardless of category or urgency:**

### Detective Finding Missing Sister

**ACTOR ARRIVAL SPARKs:**
- Informant with information ✅
- Witness who saw something ✅
- Kidnapper's associate ✅
- Random tourist asking directions ❌ (no goal relevance)

**INCIDENT SPARKs:**
- Suspicious van matching description ✅
- Argument mentioning kidnapping ✅
- Police raid on trafficking ring ✅
- Car accident nearby ❌ (no goal relevance)

**EUREKA SPARKs:**
- Pattern in disappearance dates ✅
- Connection between locations ✅
- Realization about suspect's motive ✅
- Memory of childhood ❌ (no goal relevance unless directly tied)

---

## Design Philosophy

### Always Optional
- SPARKs are **offers**, not **demands**
- UA can ignore any SPARK, even HIGH urgency
- Urgency affects persistence, not agency

### Diegetic Presentation
- SPARKs feel like natural world events
- No meta-game language ("This is a SPARK!")
- Integrated into narrative flow

### Goal-Focused
- Every SPARK advances, complicates, or tests the GOAL
- Not about immediate tasks (finding food, resting)
- Strategic opportunities, not tactical actions

### Consequence-Aware
- HIGH urgency SPARKs may have consequences if ignored
- Consequences are diegetic (man dies, van escapes, deadline passes)
- Consequences don't punish - they create realistic outcomes

---

## Implementation Status

✅ **Three SPARK types defined** (actor_arrival/incident/eureka)
✅ **Urgency system clarified** (persistence, not force)
✅ **Examples provided** for all 9 combinations (3 types × 3 urgency levels)
✅ **Goal-focus emphasized** in all SPARKs
✅ **Optional nature preserved** even at HIGH urgency

The SPARK system now provides:
- Clear categorization for LLM generation
- Meaningful urgency that affects persistence
- Goal-relevant strategic opportunities
- Complete player agency
- Diegetic, immersive presentation
