# Investigation Report: Exchange System Inquiry vs Exchange Boundary

## Issue Summary
Inquiries (questions, information gathering) incorrectly trigger exchange/encounter mode when they should be handled as simple inquiries without time pressure or contested mechanics.

## Root Cause Analysis

### Problem Location
**agents/interpreter_agent.py:2951** in the `detect_inquiry_or_action()` function prompt.

### The Issue
The classification prompt provides this example:
```
**CONTESTED ACTION**: ... Examples: ... "Ask the bartender", "Buy a drink".
```

This conflates two fundamentally different action types:
1. **Information-seeking inquiries** ("Ask the bartender about the menu")
2. **Transactional contested actions** ("Buy a drink from the bartender")

### Current Classification Logic
```python
- **CONTESTED ACTION**: Targets/affects another actor (NUA/INUA) with an explicit
  interaction intent (dialogue, persuasion, threat, attack, transaction, etc.).
  Examples: "Attack him", "Talk to her", "Persuade guard", "Ask the bartender",
  "Buy a drink".

- **INQUIRY**: Pure information seeking. Examples: "Where is it?", "I try to remember",
  "What do I see?".
```

### Why This is Wrong

**Inquiry Types:**
- **Environmental inquiries**: "Where am I?", "What do I see?"
  - Current: ✅ Correctly classified as `inquiry`

- **Memory inquiries**: "What do I know about X?", "I try to remember"
  - Current: ✅ Correctly classified as `inquiry`

- **Social inquiries**: "Ask bartender about the menu", "What's your name?"
  - Current: ❌ **Incorrectly** classified as `contested_action`
  - Should be: `inquiry` or special `social_inquiry` subtype

**Exchange Actions:**
- **Social contests**: "Persuade the guard", "Intimidate him", "Seduce her"
  - Current: ✅ Correctly `contested_action`

- **Transactions**: "Buy a drink", "Sell my gun", "Trade items"
  - Current: ✅ Correctly `contested_action`

- **Hostile actions**: "Attack", "Steal from", "Tackle"
  - Current: ✅ Correctly `contested_action`

## Impact

When social inquiries are misclassified as contested_action:

1. **Triggers encounter mode** unnecessarily
2. **Applies time pressure** (reactor_time_manager)
3. **Requires exchange resolution** (success rolls, contested mechanics)
4. **Limits inquiry budget** during reactions
5. **Creates narrative confusion** (why does asking a question start a "contest"?)

## Correct Behavior

### Information-Seeking Questions (Pure Inquiry)
```
User: "Ask the bartender what's on tap"
User: "What's your name?"
User: "Do you know where Marcus went?"
```
**Should:**
- Classify as `inquiry`
- Use `handle_inquiry()` path
- Generate immediate response via narrator
- No time pressure, no contest mechanics
- Can happen during exploration or as reactor inquiry

### Social Action with Stakes (Contested)
```
User: "Persuade the bartender to tell me about the back room"
User: "Intimidate him into revealing information"
User: "Charm her into giving me a discount"
```
**Should:**
- Classify as `contested_action`
- Enter exchange/encounter mode
- Apply contest mechanics
- Has success/failure stakes that affect relationship

### Transaction (Contested)
```
User: "Buy a drink"
User: "Sell my gun"
User: "Trade my keycard for information"
```
**Should:**
- Classify as `contested_action`
- Trigger monetary/exchange mechanics
- Has resource exchange stakes

## Proposed Fix

### Option 1: Add Social Inquiry Examples to INQUIRY Section
**Location:** agents/interpreter_agent.py:2953

**Current:**
```
- **INQUIRY**: Pure information seeking. Examples: "Where is it?", "I try to remember", "What do I see?".
```

**Fixed:**
```
- **INQUIRY**: Pure information seeking (includes asking NPCs simple questions). Examples:
  "Where is it?", "I try to remember", "What do I see?", "Ask bartender what's on tap",
  "What's your name?", "Do you know Marcus?".
```

### Option 2: Clarify CONTESTED ACTION Boundary
**Location:** agents/interpreter_agent.py:2951

**Current:**
```
- **CONTESTED ACTION**: Targets/affects another actor (NUA/INUA) with an explicit interaction intent
  (dialogue, persuasion, threat, attack, transaction, etc.). Examples: "Attack him", "Talk to her",
  "Persuade guard", "Ask the bartender", "Buy a drink".
```

**Fixed:**
```
- **CONTESTED ACTION**: Targets/affects another actor (NUA/INUA) with **social pressure, coercion,
  or transactional stakes** (persuasion, threat, attack, transaction, etc.). Examples: "Attack him",
  "Persuade guard to let me in", "Intimidate her", "Buy a drink", "Trade items".
  - NOTE: Simple questions/information requests are INQUIRY, not contested. "Ask bartender about menu" = INQUIRY.
```

### Option 3: Add Clarifying Rule (Recommended)
Add after line 2955 (before CRITICAL MOVEMENT rule):

```
**CRITICAL INQUIRY VS CONTESTED RULE:**
- Simple questions asking for information = **INQUIRY** (e.g., "Ask about X", "What's your name?", "Do you know Y?")
- Social pressure/manipulation = **CONTESTED ACTION** (e.g., "Persuade", "Intimidate", "Convince", "Charm")
- Transactions/exchanges = **CONTESTED ACTION** (e.g., "Buy", "Sell", "Trade")
```

## Testing Recommendations

After implementing fix, test these cases:

### Should Classify as INQUIRY:
1. "Ask the bartender what's on the menu"
2. "What's your name?"
3. "Do you know where Marcus went?"
4. "Ask about the back room"
5. "What time does this place close?"

### Should Classify as CONTESTED_ACTION:
1. "Persuade the bartender to tell me about the back room"
2. "Intimidate him into revealing the password"
3. "Charm her into giving me a discount"
4. "Buy a drink"
5. "Convince the guard to let me pass"

## Files Affected
- **agents/interpreter_agent.py** (lines 2951-2955, prompt modification)

## Related Systems
- **handle_inquiry()** at agents/conductor_agent.py:221
- **Exchange system** (should NOT trigger for inquiries)
- **Reactor time management** (should NOT apply time pressure to inquiries in exploration)

## Status
**INVESTIGATION COMPLETE** - Ready for implementation

## Recommended Action
Implement **Option 3** (add clarifying rule) + modify line 2951 to remove "Ask the bartender" from contested_action examples.
