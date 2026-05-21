# Perception-Based Narration System

## Overview
Converted all UA (User Actor) narration to perception-based description that focuses on what the UA perceives through their five senses.

## Philosophy
- **Old Approach**: "The alleyway's concrete stretches ahead as the morning sun warms your shoulders."
- **New Approach**: "You push through the back door, as you see the alleyway's concrete stretching ahead as you feel the warmth of the sun on your shoulders."

## Key Principles

### 1. Sensory Perception Language
Use explicit sensory verbs:
- **You see** - Visual perception
- **You feel** - Tactile/emotional perception  
- **You hear** - Auditory perception
- **You smell** - Olfactory perception
- **You taste** - Gustatory perception

### 2. NUA Actions Through UA Perception
When describing NUA actions to UA:
- **Old**: "Guard swings his baton at you"
- **New**: "You see Guard swing his baton toward you"

Focus on what UA PERCEIVES, not what objectively happens.

### 3. Movement and Attention
Use phrases like:
- "Movement catches your eyes"
- "In the peripheral of your eye"
- "Your attention is drawn to"

## Changes Made

### 1. Scene Descriptions (`generate_scene_description`)
**Updated Requirements:**
- Use sensory perception language ("you see", "you feel", "you hear", "you smell", "you taste")
- Focus on what the UA PERCEIVES through their five senses
- Use second-person perspective ("you") with sensory verbs

**Example:**
```
OLD: "The fire escape overlooks a narrow alley. Below, a black Trans Am sits with its engine off."

NEW: "You see the fire escape overlooks a narrow alley. Below, you spot a black Trans Am with its engine off. You feel the rough texture of the metal railing under your hands."
```

### 2. Exchange Narratives

#### A. Reaction Narratives (`_build_reaction_narrative`)
**When Reactor is UA:**
- Added PERCEPTION-BASED NARRATION section
- Describe how UA SEES, HEARS, FEELS the opponent's action
- Use phrases like "you see {proactor_name}...", "you feel the impact...", "you hear..."
- Focus on sensory experience of the threat/action

**Example:**
```
OLD: "As your opponent lunges, you react with lightning speed."

NEW: "You see your opponent lunge toward you, and you react with lightning speed. You feel the rush of adrenaline as you draw upon your Adept 'Dodge' skill, weaving effortlessly out of harm's way."
```

#### B. Proactor Narratives (`_build_action_narrative`)
**Already uses sensory language for UA:**
- "Your heart pounds as you grip the blade tighter"
- "Your foot slips slightly on the wet floor"
- Maintained existing sensory-focused approach

### 3. Exploration Narratives (To Be Updated)
**Target Methods:**
- `generate_exploration_action_result_narrative` - Add perception language
- `generate_given_action_narrative` - Add perception language  
- `generate_inquiry_response` - Already uses "you" perspective

## Implementation Status

### ✅ Completed
1. Scene description prompts updated with perception requirements
2. Reaction narratives updated for UA perception of NUA actions
3. Documentation created

### 🔄 In Progress
1. Exploration action narratives
2. Given action narratives
3. Inquiry response narratives

### ⏳ Pending
1. Testing and verification
2. Integration testing with full simulation

## Examples

### Scene Description
```
You push through the back door, as you see the alleyway's concrete stretching ahead as you feel the warmth of the sun on your shoulders. You see the diner's neon sign flickers weakly, and beneath it, a handwritten note on the window catches your eye—"Band Night: Thursdays, 9 PM. Free with flyer." In the peripheral of your eye, a rusted fire escape clatters in the breeze, its bottom rung dangling just out of reach. Movement catches your eyes, a punk show flyer flutters against the dumpster, its torn edge revealing a scribbled address in Sharpie.
```

### Exchange - UA Reacting to NUA
```
You see Guard swing his baton toward your head. You feel your muscles tense as you duck, hearing the whoosh of air as the weapon passes overhead. Your heart pounds as you weave to the side, the rush of adrenaline sharpening your senses.
```

### Exchange - UA Proacting
```
Your grip tightens on the knife. You feel the weight of it in your hand as you lunge forward, stabbing toward his guard. Your foot catches on something—damn—but you push through, driving the point home.
```

## Benefits

1. **Immersion**: Player experiences the world through their character's senses
2. **Clarity**: Explicit about what is perceived vs. what objectively happens
3. **Consistency**: All UA narration uses same perception-based approach
4. **Realism**: Matches how humans actually experience the world

## Technical Notes

### File Modified
- `c:\Users\darre\OneDrive\Desktop\Realitas Neo\agents\narrator_agent.py`

### Methods Updated
1. `generate_scene_description` (lines 259-351)
2. `_build_reaction_narrative` (lines 550-672)

### Methods To Update
1. `generate_exploration_action_result_narrative`
2. `generate_given_action_narrative`
3. `generate_inquiry_response` (minor updates)

## Next Steps

1. Update exploration action narratives with perception language
2. Update given action narratives with perception language
3. Test with full simulation
4. Verify all UA narration uses sensory perception verbs
5. Document any edge cases or special handling needed
