# Exchange System - Comprehensive Tests

## Overview

Exchange system tests for SPARK/PRESSURE mode (contested actions between proactor and reactor).

---

## Test 1: Basic Social Exchange

### Setup
**Scenario:** Persuading a guard to let you pass

**Input:** `I try to convince the guard to let me pass`

### Expected Flow

**1. Classification**
```
✅ Detected as contested_action
✅ Reactor identified: Guard
✅ Exchange system activated
```

**2. Proactor Calculation**
```
📊 PROACTOR (Your Character)
S-Trait: Sociability (X)
Skill: Persuasion (X)
Endowment: None (0)
Supplement: None (0)
Serendipity: X
Stress: X
Status: X
Sympathy Modifier: X
─────────────────
Total Success: X
```

**3. Reactor Calculation**
```
📊 REACTOR (Guard)
S-Trait: Sturdiness (X)
Skill: Resist Persuasion (X)
Endowment: None (0)
Supplement: None (0)
Serendipity: X
Stress: X
Status: X
Sympathy Modifier: X
─────────────────
Total Success: X
```

**4. Winner Determination**
```
🎯 EXCHANGE RESULT
Proactor: X vs Reactor: X
Winner: [Proactor/Reactor]
Margin: X
```

**5. Self-Effects Applied**
```
💫 SELF-EFFECTS
Proactor:
- [Effect 1]: Severity X, Magnitude X
- [Effect 2]: Severity X, Magnitude X

Reactor:
- [Effect 1]: Severity X, Magnitude X
```

**6. Outcome Narrative**
```
📖 OUTCOME
[Narrative describing the result based on winner and margin]
```

### Verification Checklist
- [ ] Both actors' calculations shown
- [ ] All factors included (S-trait, skill, serendipity, stress, status, sympathy)
- [ ] Winner correctly determined
- [ ] Self-effects mandatory for both actors
- [ ] Self-effects follow severity table (1-4)
- [ ] Narrative reflects winner and margin
- [ ] Status changes applied to actor sheets

---

## Test 2: Combat Exchange (Physical Attack)

### Setup
**Scenario:** Punching a guard

**Input:** `I punch the guard`

### Expected Flow

**1. Classification**
```
✅ Detected as contested_action
✅ Combat type: Physical attack
✅ Reactor: Guard
```

**2. Calculations**
```
📊 PROACTOR
S-Trait: Sturdiness (for physical)
Skill: Brawling/Combat
[... full calculation ...]

📊 REACTOR
S-Trait: Swiftness (for defense)
Skill: Dodge/Block
[... full calculation ...]
```

**3. Damage Calculation**
```
💥 DAMAGE
Proactor Success: X
Reactor Success: Y
Margin: X - Y = Z

Damage to Reactor: Z points
Reactor Stamina: [Before] → [After]
```

**4. Self-Effects**
```
💫 SELF-EFFECTS
Proactor:
- Stamina Cost: Severity 2, Magnitude 1 (attacking is tiring)
- Knuckle Bruising: Severity 1, Magnitude 1

Reactor (if hit):
- Physical Damage: Severity [based on margin], Magnitude [based on margin]
- Pain: Severity X, Magnitude X
```

**5. Knockout Check**
```
If Reactor Stamina ≤ 0:
💀 KNOCKOUT!
Reactor is knocked out
Initiative lost
Recovery begins next turn
```

### Verification Checklist
- [ ] Combat-appropriate S-traits used
- [ ] Damage = margin of success
- [ ] Stamina reduced by damage
- [ ] Self-effects include stamina cost for attacker
- [ ] Knockout triggers if stamina ≤ 0
- [ ] Status recovery begins next turn
- [ ] Narrative describes physical impact

---

## Test 3: Sympathy Modifier in Exchange

### Setup
**Scenario:** Helping a friend vs attacking an enemy

### Test 3A: Helping Friend (Positive Sympathy)
**Input:** `I help Marcus up` (Marcus sympathy: +3)

**Expected:**
```
📊 PROACTOR
[... calculation ...]
Sympathy Modifier: -3 (positive sympathy makes helping EASIER)
─────────────────
Total Success: X
```

**Verification:**
- [ ] Positive sympathy → negative modifier (easier)
- [ ] Additive action (helping) benefits from friendship
- [ ] Explanation shown: "Helping a friend is easier"

### Test 3B: Attacking Enemy (Negative Sympathy)
**Input:** `I punch the thug` (Thug sympathy: -2)

**Expected:**
```
📊 PROACTOR
[... calculation ...]
Sympathy Modifier: -2 (negative sympathy makes attacking EASIER)
─────────────────
Total Success: X
```

**Verification:**
- [ ] Negative sympathy → stays negative (easier)
- [ ] Subtractive action (harming) benefits from hostility
- [ ] Explanation shown: "Attacking an enemy is easier"

### Test 3C: Attacking Friend (Positive Sympathy)
**Input:** `I punch Marcus` (Marcus sympathy: +3)

**Expected:**
```
📊 PROACTOR
[... calculation ...]
Sympathy Modifier: +3 (positive sympathy makes attacking HARDER)
─────────────────
Total Success: X
```

**Verification:**
- [ ] Positive sympathy → stays positive (harder)
- [ ] Subtractive action against friend is difficult
- [ ] Explanation shown: "Attacking a friend is harder"

---

## Test 4: Multi-Turn Exchange

### Setup
**Scenario:** Extended negotiation over multiple turns

**Turn 1:** `I try to convince the merchant to lower the price`
**Turn 2:** `I offer to buy in bulk`
**Turn 3:** `I mention my connections in the trade guild`

### Expected Flow

**Turn 1:**
```
Exchange Result: Reactor wins (merchant resists)
Sympathy: 0 → 0 (neutral)
Status: Both actors gain stress from negotiation
```

**Turn 2:**
```
Exchange Result: Proactor wins (merchant interested)
Sympathy: 0 → +1 (merchant warms up)
Status: Stress continues to accumulate
```

**Turn 3:**
```
Exchange Result: Proactor wins decisively
Sympathy: +1 → +2 (merchant friendly now)
Outcome: Deal made, price lowered
```

### Verification Checklist
- [ ] Each exchange is independent calculation
- [ ] Sympathy changes based on outcomes
- [ ] Stress accumulates across turns
- [ ] Status recovery happens at turn start
- [ ] Narrative reflects relationship progression
- [ ] Final outcome considers all exchanges

---

## Test 5: Self-Effects Severity Validation

### Setup
**Scenario:** Various exchanges to test severity table

### Test 5A: Low Stress, Good Condition
**Stress Level:** 1, **Condition:** Healthy

**Expected Self-Effects:**
```
Severity: 1 (Minor)
Examples:
- "Slight fatigue"
- "Minor distraction"
- "Momentary doubt"
```

### Test 5B: High Stress, Poor Condition
**Stress Level:** 5, **Condition:** Wounded

**Expected Self-Effects:**
```
Severity: 4 (Critical)
Examples:
- "Severe exhaustion"
- "Overwhelming pain"
- "Critical injury"
```

### Verification Checklist
- [ ] Severity follows UTAS table (stress + condition)
- [ ] Severity range: 1-4 (never 0 or 5+)
- [ ] Magnitude 4 only for exceptional cases
- [ ] Self-effects always present (never empty)
- [ ] Descriptions match severity level

---

## Test 6: Exchange with Supplements

### Setup
**Scenario:** Using items in exchange

**Input:** `I use my lockpick to open the door while the guard watches`

### Expected Flow

**1. Proactor Calculation**
```
📊 PROACTOR
S-Trait: Smarts (3)
Skill: Lockpicking (2)
Endowment: None (0)
Supplement: Lockpick Set (+2)  ← BONUS
Serendipity: 4
Stress: 1
Status: 0
Sympathy: 0
─────────────────
Total Success: 10
```

**2. Supplement Consumption**
```
⚠️ Lockpick Set durability: 5 → 4
(Supplements degrade with use)
```

### Verification Checklist
- [ ] Supplement bonus applied
- [ ] Supplement identified from inventory
- [ ] Durability decreases after use
- [ ] Supplement removed if durability reaches 0
- [ ] Narrative mentions using the item

---

## Test 7: Exchange with Endowments (Special Abilities)

### Setup
**Scenario:** Character with special ability

**Input:** `I use my enhanced strength to intimidate the bouncer`

### Expected Flow

**1. Proactor Calculation**
```
📊 PROACTOR
S-Trait: Sturdiness (4)
Skill: Intimidation (2)
Endowment: Enhanced Strength (+3)  ← BONUS
Serendipity: 5
Stress: 2
Status: 0
Sympathy: -1
─────────────────
Total Success: 11
```

### Verification Checklist
- [ ] Endowment bonus applied
- [ ] Endowment identified from character sheet
- [ ] Narrative describes special ability use
- [ ] Endowment doesn't degrade (unlike supplements)

---

## Test 8: Knockout and Recovery

### Setup
**Scenario:** Combat leading to knockout

**Turn 1:** `I punch the thug`
**Expected:** Thug stamina: 10 → 3

**Turn 2:** `I punch the thug again`
**Expected:** Thug stamina: 3 → -2 (KNOCKOUT)

### Expected Flow

**Knockout Moment:**
```
💀 KNOCKOUT!
Thug has been knocked out!
Stamina: -2
Status: Unconscious
Initiative: Lost
```

**Next Turn (Thug's Initiative):**
```
🔄 STATUS RECOVERY
Thug is recovering...
Stamina: -2 → -1 (+1 recovery)
Still unconscious (stamina ≤ 0)
```

**Turn After (Thug's Initiative):**
```
🔄 STATUS RECOVERY
Thug is recovering...
Stamina: -1 → 0 (+1 recovery)
Still unconscious (stamina = 0)
```

**Turn After (Thug's Initiative):**
```
🔄 STATUS RECOVERY
Thug is recovering...
Stamina: 0 → 1 (+1 recovery)
✅ Regains consciousness!
```

### Verification Checklist
- [ ] Knockout triggers at stamina ≤ 0
- [ ] Initiative lost immediately
- [ ] Recovery +1 per turn (at initiative roll)
- [ ] Consciousness regained when stamina > 0
- [ ] Narrative describes recovery process

---

## Test 9: Exchange Outcome Narratives

### Setup
Test different margin levels

### Test 9A: Narrow Victory (Margin 1-2)
**Expected Narrative:**
```
"You barely manage to convince the guard. He hesitates, 
then reluctantly steps aside, still watching you suspiciously."
```

### Test 9B: Clear Victory (Margin 3-5)
**Expected Narrative:**
```
"Your argument is compelling. The guard nods and steps aside, 
convinced by your reasoning."
```

### Test 9C: Decisive Victory (Margin 6+)
**Expected Narrative:**
```
"Your words strike home with undeniable force. The guard 
immediately steps aside, thoroughly convinced and even 
apologetic for the delay."
```

### Test 9D: Narrow Loss (Margin -1 to -2)
**Expected Narrative:**
```
"The guard almost wavers, but ultimately holds his ground. 
'Sorry, no entry,' he says firmly."
```

### Test 9E: Clear Loss (Margin -3 to -5)
**Expected Narrative:**
```
"The guard shakes his head decisively. 'Not a chance. 
Move along.'"
```

### Test 9F: Decisive Loss (Margin -6 or worse)
**Expected Narrative:**
```
"The guard's expression hardens. 'Get out of here before 
I throw you out,' he growls menacingly."
```

### Verification Checklist
- [ ] Narrative tone matches margin
- [ ] Close margins show uncertainty
- [ ] Large margins show decisiveness
- [ ] Winner's perspective emphasized
- [ ] Loser's reaction described

---

## Test 10: Complex Exchange Chain

### Setup
**Scenario:** Social exchange → Combat → Negotiation

**Turn 1:** `I try to talk my way past the guard`
- Exchange: Social (Persuasion vs Resist)
- Result: Proactor loses
- Sympathy: 0 → -1 (guard annoyed)

**Turn 2:** `I shove the guard aside`
- Exchange: Combat (Sturdiness vs Swiftness)
- Result: Proactor wins
- Sympathy: -1 → -2 (guard hostile)
- Guard stamina reduced

**Turn 3:** `I apologize and offer money`
- Exchange: Social (Negotiation vs Resist)
- Sympathy modifier: +2 (harder due to hostility)
- Result: Depends on roll

### Verification Checklist
- [ ] Each exchange type handled correctly
- [ ] Sympathy changes persist across exchanges
- [ ] Status effects accumulate
- [ ] Narrative reflects relationship history
- [ ] Final outcome considers all interactions

---

## Quick Test Checklist

### Basic Exchange Mechanics
- [ ] Proactor calculation shown
- [ ] Reactor calculation shown
- [ ] Winner determined correctly
- [ ] Self-effects mandatory
- [ ] Narrative generated

### Advanced Features
- [ ] Sympathy modifiers work
- [ ] Supplements applied and consumed
- [ ] Endowments applied (no consumption)
- [ ] Damage calculation correct
- [ ] Knockout system works
- [ ] Status recovery works

### Edge Cases
- [ ] Tie handling (equal success)
- [ ] Zero/negative success values
- [ ] Missing skills (default to 0)
- [ ] Invalid reactor (error handling)
- [ ] Multiple exchanges in one turn

---

## Status

✅ Comprehensive exchange tests defined
✅ Covers all exchange types
✅ Includes edge cases
✅ Ready for systematic testing
