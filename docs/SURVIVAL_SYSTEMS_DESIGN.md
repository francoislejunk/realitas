# Survival Systems Design Document

> **Status:** Design Phase - Requires careful thought before implementation
> **Created:** November 28, 2025
> **Purpose:** Document survival-related systems that affect player sustainability

---

## Overview

These systems introduce **biological and economic pressure** to the simulation, creating stakes beyond immediate narrative. They require careful balancing to enhance immersion without becoming tedious.

---

## 1. Circadian System

### Concept
Time-of-day affects cognitive and physical performance. The body has natural rhythms.

### Performance Modifiers by Time

| Time Block | Hours | Cognitive | Physical | Mood | Notes |
|------------|-------|-----------|----------|------|-------|
| Early Morning | 05:00-07:00 | -1 | -1 | Neutral | Waking up, groggy |
| Morning Peak | 07:00-12:00 | +1 | +1 | +1 | Peak alertness |
| Post-Lunch Dip | 12:00-14:00 | -1 | 0 | 0 | The afternoon slump |
| Afternoon | 14:00-17:00 | 0 | +1 | 0 | Second wind |
| Evening | 17:00-21:00 | 0 | 0 | 0 | Winding down |
| Night | 21:00-00:00 | -1 | -1 | 0 | Should be resting |
| Late Night | 00:00-03:00 | -2 | -2 | -1 | Body wants sleep |
| Pre-Dawn | 03:00-05:00 | -2 | -2 | -2 | Lowest point |

### Sleep Debt Mechanics

```
sleep_debt = hours_awake - 16  # Debt starts after 16 hours awake

if sleep_debt > 0:
    cognitive_penalty = -floor(sleep_debt / 4)  # -1 per 4 hours over
    physical_penalty = -floor(sleep_debt / 6)   # -1 per 6 hours over
    
if sleep_debt > 24:
    # Microsleep risk - involuntary brief unconsciousness
    microsleep_chance = (sleep_debt - 24) * 5%  # 5% per hour over 40 awake
```

### Recovery

| Sleep Duration | Debt Recovered | Quality Modifier |
|----------------|----------------|------------------|
| 1-3 hours | 2 hours | Poor - still tired |
| 4-6 hours | 5 hours | Partial - functional |
| 7-9 hours | Full reset | Good - refreshed |
| 10+ hours | Full + buffer | Excellent - energized |

### Narrative Flavor

```
Early Morning: "The world has that quiet, not-quite-awake quality."
Morning Peak: "Your mind feels sharp, ready for anything."
Post-Lunch Dip: "A heaviness settles behind your eyes."
Late Night: "Everything feels distant, slightly unreal."
Pre-Dawn: "Your body screams for rest. Every blink is a battle."
```

### Integration Points
- Modify dice pools based on time
- Affect NPC availability (they sleep too)
- Influence narrative descriptions
- Create pressure to find safe rest locations

---

## 2. Hunger/Thirst Cycles

### Concept
The body needs fuel. Going without creates escalating penalties.

### Hunger States

| State | Hours Since Eating | Effects | Narrative |
|-------|-------------------|---------|-----------|
| Satisfied | 0-4 | None | - |
| Peckish | 4-8 | None | Stomach rumbles occasionally |
| Hungry | 8-16 | -1 Cognitive | Hard to focus, thinking about food |
| Very Hungry | 16-24 | -1 Cog, -1 Phys | Weakness, irritability |
| Starving | 24-48 | -2 Cog, -2 Phys | Shaking, desperate |
| Critical | 48+ | -3 all, health loss | Body consuming itself |

### Thirst States (Faster Progression)

| State | Hours Since Drinking | Effects | Narrative |
|-------|---------------------|---------|-----------|
| Hydrated | 0-2 | None | - |
| Thirsty | 2-6 | None | Dry mouth |
| Dehydrated | 6-12 | -1 Cognitive | Headache, fatigue |
| Very Dehydrated | 12-24 | -2 Cog, -1 Phys | Dizziness, confusion |
| Critical | 24+ | -3 all, health loss | Organ stress |

### Food/Drink Quality

| Quality | Hunger Satisfied | Notes |
|---------|------------------|-------|
| Full Meal | 8-12 hours | Proper nutrition |
| Snack | 2-4 hours | Temporary relief |
| Junk Food | 4-6 hours | Quick but crashes |
| Emergency Rations | 6-8 hours | Unpleasant but functional |

### Integration Points
- Track last_ate and last_drank timestamps
- Apply penalties to relevant dice pools
- Create need to find food/water sources
- Social opportunities (sharing meals)
- Economic pressure (food costs money)

---

## 3. Fatigue Accumulation

### Concept
Actions have a cost. You can't go forever without rest.

### Fatigue Sources

| Activity | Fatigue Points/Hour | Notes |
|----------|---------------------|-------|
| Light activity | 1 | Walking, talking |
| Moderate activity | 2 | Searching, climbing |
| Heavy activity | 4 | Running, fighting |
| Mental strain | 2 | Complex problem-solving |
| Emotional stress | 3 | Confrontations, fear |
| Sleep | -8 | Recovery |
| Rest (awake) | -2 | Sitting, relaxing |

### Fatigue Thresholds

| Fatigue Points | State | Effects |
|----------------|-------|---------|
| 0-20 | Fresh | None |
| 21-40 | Tired | -1 Physical |
| 41-60 | Exhausted | -1 Phys, -1 Cog |
| 61-80 | Depleted | -2 Phys, -2 Cog |
| 81-100 | Collapse Risk | -3 all, collapse chance |
| 100+ | Forced Rest | Body shuts down |

### Collapse Mechanics

```
if fatigue > 80:
    collapse_chance = (fatigue - 80) * 5%  # 5% per point over 80
    
on_collapse:
    - Fall unconscious for 1-4 hours
    - Vulnerable to environment/enemies
    - Wake with fatigue reduced to 60
```

### Integration Points
- Track fatigue as a resource
- Heavy actions cost more
- Create need for rest periods
- Tactical consideration in conflicts
- Environmental hazards (heat increases fatigue)

---

## 4. Physical Exhaustion (Stamina Depletion)

### Concept
Short-term physical capacity that depletes quickly during exertion.

### Stamina Pool

```
max_stamina = 10 + (Physical_stat * 2)  # Typically 14-20

# Costs
sprint: 2 stamina/round
fight: 1 stamina/round  
climb: 1 stamina/action
swim: 2 stamina/round
carry_heavy: 1 stamina/minute
```

### Recovery Rates

| Activity | Stamina Recovery |
|----------|------------------|
| Standing still | 1/round |
| Walking slowly | 0.5/round |
| Sitting | 2/round |
| Lying down | 3/round |

### Low Stamina Effects

| Stamina | State | Effects |
|---------|-------|---------|
| 50%+ | Normal | None |
| 25-50% | Winded | -1 Physical actions |
| 10-25% | Gasping | -2 Physical, half movement |
| <10% | Spent | Cannot take physical actions |
| 0 | Collapse | Fall prone, cannot move |

### Integration Points
- Separate from Fatigue (short vs long term)
- Combat resource management
- Chase/escape mechanics
- Environmental challenges

---

## 5. Economic Pressure

### Concept
Money is finite. Life costs money. Create need for income.

### Daily Costs

| Expense | Cost/Day | Notes |
|---------|----------|-------|
| Basic food | $15-25 | Cheap meals |
| Good food | $40-60 | Restaurants |
| Lodging (cheap) | $30-50 | Hostel, motel |
| Lodging (decent) | $80-150 | Hotel |
| Transportation | $10-30 | Bus, subway |
| Phone/utilities | $5 | Daily average |

**Minimum daily survival: ~$50-80**

### Income Sources

| Source | Pay | Frequency | Risk |
|--------|-----|-----------|------|
| Day labor | $80-150 | Daily | Low |
| Gig work | $50-200 | Variable | Low |
| Regular job | $100-300 | Daily | None |
| Skilled work | $200-500 | Daily | None |
| Criminal activity | Variable | Variable | High |
| Favors/debts | Variable | Situational | Social |

### Debt Mechanics

```
if money < 0:
    debt_interest = 10% per week
    
    # Consequences escalate
    week_1: Creditors call
    week_2: Services cut off
    week_3: Eviction notice
    week_4: Collectors arrive
```

### Integration Points
- Track money as resource
- Jobs take time (opportunity cost)
- Economic motivation for actions
- Social class affects options
- Desperation creates drama

---

## Implementation Considerations

### Balance Concerns

1. **Tedium vs. Stakes**
   - Too punishing = frustrating micromanagement
   - Too lenient = meaningless systems
   - Sweet spot: Pressure without constant attention

2. **Time Scale**
   - Real-time tracking can be overwhelming
   - Consider "significant time" triggers
   - Batch updates during scene transitions

3. **Player Agency**
   - Always provide options to address needs
   - Multiple solutions at different costs
   - Failure should create drama, not dead ends

### Suggested Implementation Order

1. **Circadian System** - Easiest, most narrative impact
2. **Fatigue Accumulation** - Creates rest pressure
3. **Hunger/Thirst** - Biological stakes
4. **Economic Pressure** - Long-term motivation
5. **Physical Exhaustion** - Combat/action depth

### Testing Questions

- Does this enhance immersion or create busywork?
- Are there always viable options to address needs?
- Does failure create interesting situations?
- Is the cognitive load on the player acceptable?
- Do NPCs follow the same rules (consistency)?

---

## Future Considerations

### Potential Expansions

- **Addiction mechanics** - Substances create dependency
- **Injury recovery** - Wounds need time to heal
- **Illness/disease** - Environmental health risks
- **Aging effects** - Long-term campaigns
- **Psychological needs** - Social contact, purpose

### Integration with Existing Systems

- Weather affects fatigue (heat/cold)
- NPC schedules include eating/sleeping
- Economic pressure motivates NPC behavior
- Circadian affects NPC availability
- Reputation affects job opportunities

---

## Notes for Future Implementation

*Add notes here as design evolves*

- Consider a "survival mode" toggle for players who want this depth
- May need UI/display system for tracking multiple resources
- Could tie into the existing STAMINA stat on actor sheets
- Economic system could integrate with inventory/item system

