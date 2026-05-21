# Internal Voice Exchange System - Implementation Guide

## Overview

The Internal Voice has been redesigned as a **morality compass** based on the actor's internal personality. It now:

1. **Appears in exchanges** during extreme scenarios (when actions go against or for personality)
2. **Shifts spirit positively and negatively** (removed from self-effects)
3. **Engages in dialogue** with the UA as an entity
4. **Triggers based on personality conflicts** - Example: "fear of becoming a monster again" triggers when actions risk that outcome

## Key Components

### 1. Internal Voice Exchange System (`internal_voice_exchange_system.py`)

**Core Classes:**
- `PersonalityConflictType` - Types of conflicts (AGAINST_INTERNAL, FOR_INTERNAL, etc.)
- `SpiritImpactDirection` - POSITIVE, NEGATIVE, NEUTRAL
- `PersonalityConflict` - Represents a detected conflict
- `InternalVoiceExchange` - An exchange between UA and Internal Voice
- `SpiritState` - Tracks the UA's spirit level (-10 to +10)
- `InternalVoiceExchangeSystem` - Main system manager

**Key Methods:**
- `detect_personality_conflict()` - Detects when actions conflict with personality
- `should_trigger_internal_voice_exchange()` - Determines if exchange should trigger
- `generate_internal_voice_exchange()` - Creates the exchange dialogue
- `process_ua_response()` - Handles UA's response and applies spirit impact

### 2. Integration Module (`internal_voice_exchange_integration.py`)

**Main Functions:**
- `check_and_trigger_internal_voice_exchange()` - Check if action triggers exchange
- `display_internal_voice_exchange()` - Display the exchange UI
- `process_internal_voice_exchange_response()` - Process UA response
- `run_internal_voice_exchange_flow()` - Complete flow function
- `generate_internal_voice_morality_compass()` - Drop-in replacement for old function

## How It Works

### Trigger Conditions

The Internal Voice exchange triggers during **extreme scenarios** when:

1. **Action severity >= 0.6** (high impact actions)
2. **Personality conflict detected** (action goes against/for internal personality)
3. **Explicitly marked as extreme scenario**

### Example Flow

**Scenario:** UA's internal personality is "fear of becoming a monster again"

**Trigger:** UA takes a violent action (e.g., "I attack the innocent person")

**Exchange:**
```
🗣️  INTERNAL VOICE - MORALITY COMPASS
══════════════════════════════════════════════════════════════════════

💭 'That path... it leads back to what we fear most. fear of becoming 
    a monster again - remember?'

How do you respond to your Internal Voice?
[1] Acknowledge the warning and reconsider
[2] Press forward despite the internal resistance
[3] Question why this feels wrong
[4] Ignore the voice and proceed

══════════════════════════════════════════════════════════════════════
```

**Response Processing:**
- Choice 1: Spirit impact NEUTRAL/POSITIVE (affirms self-control)
- Choice 2: Spirit impact NEGATIVE (ignoring conscience)
- Choice 3: Spirit impact POSITIVE (self-reflection)
- Choice 4: Spirit impact NEGATIVE (rejection of morality)

**Result:**
```
💔 Spirit Fractured | Spirit Level: -2.4
Status: Conflicted - Internal struggle evident
```

## Spirit System

### Spirit Levels

- **+7 to +10**: Transcendent - Deeply aligned with true self
- **+4 to +7**: Resolute - Strong sense of identity
- **+1 to +4**: Centered - At peace with oneself
- **-1 to +1**: Uncertain - Searching for clarity
- **-4 to -1**: Conflicted - Internal struggle evident
- **-7 to -4**: Fragmented - Identity under stress
- **-10 to -7**: Broken - Severe misalignment with self

### Spirit Impact

- **POSITIVE**: Actions that affirm internal personality (+magnitude)
- **NEGATIVE**: Actions that contradict internal personality (-magnitude)
- **NEUTRAL**: Contemplative moments (stabilizes)

## Integration Steps

### Step 1: Remove Old Internal Voice from Self-Effects

The old Internal Voice system should no longer appear in self-effects. It's now a separate exchange system.

### Step 2: Add Integration to Action Processing

In your action processing loop (before main exchanges):

```python
from internal_voice_exchange_integration import (
    run_internal_voice_exchange_flow,
    get_spirit_status_display
)

# After action interpretation, before main exchange processing
exchange_result = run_internal_voice_exchange_flow(
    actor=ua_actor,
    action_description=interpreted_action,
    scene_context=current_scene,
    is_extreme_scenario=is_extreme_scenario  # flag from interpreter
)

if exchange_result:
    narrative, spirit_impact = exchange_result
    # Include narrative in scene context
    # Spirit impact is already applied

# Display spirit status periodically
print(get_spirit_status_display(ua_actor))
```

### Step 3: Mark Extreme Scenarios

The interpreter should flag extreme scenarios in its interpretation:

```python
interpretation = {
    # ... other fields ...
    "is_extreme_scenario": True,  # For personality-threatening actions
    "personality_conflict_severity": 0.8  # 0.0 to 1.0
}
```

## Personality Examples

### Example 1: Fear of Becoming a Monster

**Internal Personality:** "Hidden fear of becoming a monster again"

**Triggering Actions:**
- Violence against innocents (AGAINST_INTERNAL, severity: 0.8)
- Ruthless behavior (AGAINST_INTERNAL, severity: 0.7)
- Protecting the vulnerable (FOR_INTERNAL, severity: 0.6)

### Example 2: Seeking Redemption

**Internal Personality:** "Deep need for redemption from past sins"

**Triggering Actions:**
- Selfless sacrifice (FOR_INTERNAL, severity: 0.9)
- Selfish behavior (AGAINST_INTERNAL, severity: 0.7)
- Acts of service (FOR_INTERNAL, severity: 0.6)

### Example 3: Hidden Compassion

**Internal Personality:** "Tough exterior hiding genuine compassion"

**Triggering Actions:**
- Showing vulnerability (FOR_INTERNAL, severity: 0.7)
- Cold cruelty (AGAINST_INTERNAL, severity: 0.8)
- Helping others despite risk (FOR_INTERNAL, severity: 0.8)

## Migration from Old System

### What Changes

| Old System | New System |
|------------|------------|
| Internal Voice as comment/thought | Internal Voice as exchange participant |
| Passive display | Interactive dialogue |
| Affects stress/self-effects | Affects spirit state (separate system) |
| Always appears after actions | Only appears during extreme scenarios |
| Information/memory/solution functions | Morality compass only |

### What Stays the Same

- Still triggered by actions
- Still based on personality
- Still provides narrative flavor
- Still uses LLM for generation (optional enhancement)

## Future Enhancements

### Planned Features

1. **LLM-Powered Generation**: Use LLM to generate more nuanced Internal Voice dialogue
2. **Exchange History**: Track how spirit evolves over time
3. **Spirit-Locked Content**: Unlock special interactions based on spirit level
4. **Personality Evolution**: Spirit state could eventually shift personality traits
5. **NPC Spirit Sensing**: Perceptive NPCs might sense UA's spirit state

## Files Created

1. `internal_voice_exchange_system.py` - Core system
2. `internal_voice_exchange_integration.py` - Integration functions
3. `INTERNAL_VOICE_EXCHANGE_GUIDE.md` - This guide

## Testing

To test the new system:

```python
from internal_voice_exchange_system import (
    get_internal_voice_exchange_system,
    SpiritState
)

# Create a mock actor with internal personality
class MockActor:
    class sheet:
        name = "Test Actor"
        class personality_profile:
            internal = "fear of becoming a monster again"
            external = "tough mercenary"

actor = MockActor()

# Test conflict detection
iv_system = get_internal_voice_exchange_system()
conflict = iv_system.detect_personality_conflict(
    actor=actor,
    action_description="I kill the innocent bystander",
    internal_personality=actor.sheet.personality_profile.internal,
    external_personality=actor.sheet.personality_profile.external
)

if conflict:
    print(f"Conflict detected: {conflict.conflict_type.value}")
    print(f"Severity: {conflict.severity}")
    print(f"Reason: {conflict.trigger_reason}")
```
