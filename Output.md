# UTAS Simulation Output Format (Proposed)

This document specifies the desired, structured turn-by-turn output for the UTAS simulation. It aligns with the legacy Reporter while preserving new features in the EnhancedReporter.

The flow is:

- Encounter begins → Turn Queue printed (with any round-start recovery)
- For each turn → Steps 1–6 printed in detail
- After Step 6 → a consolidated end-of-turn summary (single, compact recap)

---

## Encounter Start: Turn Queue

Printed once when a round is started.

Header:

```
🎯 TURN QUEUE (queue_size/max_queue_size)
```

If any recovery occurred at round start, print immediately:

```
🔄 TEMPORARY RECOVERY:
  <Actor>'s <STATUS> recovers +<amount> (<old> → <new>) [FULLY RECOVERED]
    Source: <optional source description>
  <Narrative line for recovery, if any>
```

Then the queue listing:

Default listing:

```
  1. <Actor Name> (UA|NUA|INUA, Initiative: <score>)
  2. <Actor Name> (UA|NUA|INUA, Initiative: <score>)
  ...
```

Optionally, label the top two entries and show initiative math breakdown (when flags are enabled):

```
  1. <Actor A> (PROACTOR) (UA|NUA|INUA, Initiative: <score>)
     └─ <Swiftness> + <Status Avg> + (<2D6 detail → serendipity>) [+ Role +<bonus>] = <total>
        Swiftness + Status Avg(<stamina>+<spirit>)/2 + Serendipity[ + Role Bonus]
  2. <Actor B> (PRIMARY REACTOR) (UA|NUA|INUA, Initiative: <score>)
     └─ <Swiftness> + <Status Avg> + (<2D6 detail → serendipity>) [+ Role +<bonus>] = <total>
        Swiftness + Status Avg(<stamina>+<spirit>)/2 + Serendipity[ + Role Bonus]
  3. <Actor C> (UA|NUA|INUA, Initiative: <score>)
```

If any actors were excluded:

```
⚠️ EXCLUDED ACTORS:
  • <Actor Name> (Initiative: <score>, Reason: <reason>)
```

If any tie-breakers were resolved:

```
🎲 TIE-BREAKERS RESOLVED:
  • <Actor A> vs <Actor B> tied at Initiative <score>
    Resolution: <how> → Winner: <Actor>
```

---

## Per Turn: Detailed Steps

These are printed during a turn in this order.

### Step 1 – Proactor Action Interpretation

Header:

```
STEP 1 - Proactor Action Interpretation (In this case, the Proactor is the <Name>)
```

Content (examples; fields are printed if present):

```
User Action: <raw_input.>
LLM Action: <raw_action.>
Target Type: <TYPE> (<confidence> confidence) - <detected_target>

Continuity Check: (Repeat until the action is valid)
Judgement: <Possible|Not Possible>
Continuity Narrative Justification: <text>

Proactor: <Name>
Interpreted Action: <narrative_description>

UTAS Factors:
Exchange Type: <type>.
Targeted Reactor Status: <status>.
S-Trait: <name> (<value>). <justification>
Skill: <name> (<value>).
Justification: <text>
Endowment: <name> (<value>).
Supplement: <name> (<value>).
Stress Level: <level>. <justification>

💰 Self-Inflicted Action Effects (Proactor Costs):
Effect 1:
Possible Self-Effect Condition: <trigger>.
Possible Self-Inflicted Target Status: <status>.
Possible Proactor Polarity Shift: <Additive|Subtractive> (<+N|-N>).
Possible Proactor Type Shift: Temporary.
Self-Effect Severity: <severity>. <justification>
```

### Step 2 – Proactor Success Calculation & Narrative

Header:

```
STEP 2 - Calculate Proactor's Success & Narrate
```

If a prebuilt calc string exists, print it. Otherwise, print the fallback formula:

```
Success Calculation:
(S-Trait: <X> + Skill: <Y> + Endowment: <Z> + Supplement: <W> + Serendipity: +<S>) - (Stress Modifier: +<A> + Status Modifier: +<B> + Sympathy Modifier: +<C>) = <Total>
Success Threshold: <T>
Result: <SUCCESS|FAILURE> (<Total> ≥|< <T>)

Factors Used:
  • S-Trait: <name> (<value>, <descriptor>)
  • Skill: <name> (<value>, <descriptor>)
  • Endowment: <name> (<value>)
  • Supplement: <name> (<value>)
  • Serendipity: +<S> (<descriptor>)
Modifiers:
  • Stress: +<A>
  • Status: +<B>
  • Sympathy: +<C>

Narrative of Proactor's Attempt:
<Attempt Summary + Success Line>
```

### Step 3 – Reactor Action Interpretation

Header:

```
STEP 3 - Reactor Action Interpretation (In this case, the Reactor is <Name>)
```

- Prints the proactor summary line for context
- Prints reactor sheet snippet (current statuses) if provided
- Prints Reactor UTAS Factors in the same style as Step 1

### Step 4 – Reactor Success Calculation & Narrative

Header:

```
STEP 4 - Calculate Reactor's Success & Narrate
```

- Same calculation line rules and factor printouts as Step 2.
- Narrative of Reactor's Attempt is printed similarly.

### Step 5 – Final Outcome & Status Updates

Header:

```
STEP 5 - Calculate Final Outcome & Update Statuses
```

Content:

```
Final Outcome Calculation:
Proactor Successes (<Proactor>): <N>
Reactor Successes (<Reactor>): <M>
Raw Success Difference: <N> - <M> = +<D> (<Proactor Wins|Reactor Wins|Tie>).
Status Shift Calculation: <formula, if available>

Status Shift Calculation (<Actor>):
<Shift description lines as computed>
Your <Status> of <old> is reduced|increased by <abs(shift)> [...].
Your new <Status> is <new> (<descriptor>).

[Self-Effects, if any triggered]
```

### Step 6 – Narrative Turn Outcome

Header:

```
STEP 6 - NARRATIVE TURN OUTCOME
```

- Deterministic UTAS formula narrative (from `llm_agents/utas_narrative_formula.py`).
- A brief pure-resolution line may precede it for readability.

---

## End-of-Turn: Consolidated Summary (Printed After Step 6)

Header:

```
============================================================
  TURN SUMMARY
============================================================
```

Sections:

```
Turn Queue Snapshot:
  1. <Actor A> (PROACTOR) (Init: <score>)
  2. <Actor B> (PRIMARY REACTOR)  (Init: <score>)
  3. <Actor C>                    (Init: <score>)
  ... # include additional actors as needed

Roles this turn: Proactor: <Actor A>  •  Primary Reactor: <Actor B>

Continuity Check:
  Judgment: <Possible|Not Possible>
  Justification: <...>   # if present

Action Interpretations:
  <Proactor>: <narrative_description>
  <Reactor>:  <narrative_description>

Success Overview:
  <Proactor>: <N> successes
  <Reactor>:  <M> successes

Status Shifts:
  <Actor>: <Status> +|-<shift> → <old> (<desc>) → <new> (<desc>)

<Final Narrative line(s)>
```

---

## Notes

- Actor sheets for NUAs are shown around Steps 1/3 only; UA sheets are hidden by default to reduce redundancy.
- Recovery occurs at the start of each round and is bundled with the Turn Queue report.
- Tie-breakers and excluded actors are only shown when applicable.
- The deterministic Step 6 narrative is the source of truth for the outcome description; LLM content never changes mechanics.
 - Actor cards use shorthand S-Factor labels: Swift, Social, Sturdy, Smart, Shadow.
 - When enabled, the Turn Queue can label the first two entries as (PROACTOR) and (PRIMARY REACTOR), and include initiative math breakdown lines per actor.
