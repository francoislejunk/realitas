# Dialogue as Full UTAS Action

## Core Philosophy

**Dialogue is NOT just metadata** - it's a full contested UTAS action when there are conversational stakes. This system maintains natural conversational flow while integrating speech into the same mechanical framework as physical actions.

## Key Principles

### 1. **Dialogue IS a Contested Action (When Stakes Exist)**

Dialogue uses the same UTAS mechanics as punching, shooting, or any other action:

**Persuasion Example:**
- **UA:** "You should help me break into that warehouse - we'll split the loot 50/50"
- **Mechanics:** SPIRIT or SYMPATHY exchange
  - **S-Trait:** SOCIABILITY (charm, persuasion)
  - **Skill:** Persuasion, Negotiation, or Social Fortitude
  - **Status Target:** SPIRIT (changing their mind) or SYMPATHY (building trust)
  - **Shift Polarity:** Additive (trying to gain cooperation)
  - **Success:** NUA agrees or is swayed
  - **Failure:** NUA resists, unconvinced

**Deception Example:**
- **UA:** "I'm just a delivery guy, nothing suspicious here"
- **Mechanics:** SHADOW vs. SMARTS/SOCIABILITY exchange
  - **S-Trait:** SHADOW (deception, misdirection)
  - **Skill:** Deception, Acting
  - **Status Target:** SPIRIT (their confidence in detecting lies)
  - **Shift Polarity:** Subtractive (undermining their certainty)
  - **Success:** They believe you
  - **Failure:** They see through the lie

**Interrogation Example:**
- **UA:** "Where were you on the night of the 15th?"
- **Mechanics:** SMARTS or SOCIABILITY vs. SPIRIT exchange
  - **S-Trait:** SMARTS (logical pressure) or SOCIABILITY (social pressure)
  - **Skill:** Interrogation, Investigation
  - **Status Target:** SPIRIT (their will to withhold information)
  - **Shift Polarity:** Subtractive (breaking down resistance)
  - **Success:** They reveal information
  - **Failure:** They stay silent or deflect

### 2. **Trivial Dialogue (Phatic Communication) Has No Stakes**

**Examples:**
- "Hello"
- "How's your day?"
- "Nice weather we're having"
- "See you later"

**Mechanics:**
- `apply_shift: false` - No contested exchange
- Still generates UTAS factors (for consistency)
- NUA responds naturally based on personality and sympathy
- No success/failure calculation needed

### 3. **NPCs Have Conversational Agency**

NPCs are not passive responders - they have their own:

**Conversational Goals:**
- Extract information from the UA
- Steer conversation toward their interests
- Build or damage rapport
- Achieve their own objectives through dialogue

**Personality-Driven Speech:**
- Talkative vs. taciturn
- Formal vs. casual
- Direct vs. evasive
- Friendly vs. hostile

**Sympathy-Based Cooperation:**
- **High Sympathy (4-5):** Helpful, engaged, willing to share, asks follow-up questions
- **Neutral Sympathy (3):** Professional, transactional, measured responses
- **Low Sympathy (1-2):** Guarded, brief, may redirect or end conversation

### 4. **Natural Conversational Flow**

**Multi-Turn Conversations:**
- NPCs reference previous exchanges
- Topics evolve organically
- NPCs can introduce new subjects
- Conversations build on established rapport

**Example Flow:**
```
UA: "Hey, have you seen anyone suspicious around here?"
NUA: "Suspicious? Depends on what you mean. This neighborhood's full of characters. What are you looking for?"

UA: "Someone who might be dealing in stolen tech."
NUA: "Ah, tech. Yeah, I might know something. But information's valuable, you know? What's in it for me?"

UA: "I can pay you 50 credits."
NUA: "50? That's insulting. Make it 200 and we'll talk."
```

Each exchange is a UTAS action with stakes, but the conversation flows naturally.

## UTAS Mechanics for Dialogue

### Status Targets for Dialogue Actions

| Dialogue Type | Primary Status | Secondary Status | Shift Polarity |
|--------------|----------------|------------------|----------------|
| Persuasion | SPIRIT | SYMPATHY | Additive |
| Intimidation | SPIRIT | - | Subtractive |
| Deception | SPIRIT | - | Subtractive |
| Encouragement | SPIRIT | SYMPATHY | Additive |
| Insult | SYMPATHY | SPIRIT | Subtractive |
| Negotiation | SUPPLY | SYMPATHY | Additive/Subtractive |
| Interrogation | SPIRIT | - | Subtractive |
| Rapport Building | SYMPATHY | - | Additive |
| Information Sharing | SPIRIT | SYMPATHY | Additive |

### S-Traits for Dialogue

- **SOCIABILITY:** Persuasion, charm, leadership, public speaking, negotiation
- **SMARTS:** Logical arguments, technical explanations, interrogation, debate
- **SHADOW:** Deception, misdirection, subtle manipulation, reading between lines
- **SWIFTNESS:** Quick wit, verbal sparring, rapid-fire responses (rare)
- **STURDINESS:** Verbal intimidation through physical presence (rare)

### Skills for Dialogue

- **Persuasion:** Convincing others, negotiation, sales
- **Deception:** Lying, misdirection, acting
- **Interrogation:** Extracting information, questioning
- **Social Fortitude:** Resisting social pressure, maintaining composure
- **Investigation:** Asking probing questions, detective work
- **Performance:** Acting, dramatic delivery, storytelling
- **Etiquette:** Formal conversations, diplomatic exchanges

## Implementation Details

### Interpreter Agent Guidance

The InterpreterAgent now provides:
- **Dialogue weight estimation** (sentences counted as units)
- **Conversational stakes detection** (persuasion vs. phatic)
- **Full UTAS factor generation** for dialogue actions
- **apply_shift flag** (false for trivial dialogue)

### Decider Agent Guidance

The DeciderAgent now provides NPCs with:
- **Conversational goals** based on character objectives
- **Sympathy-based cooperation levels**
- **Natural flow principles** (reference previous topics, ask questions)
- **Dialogue weight matching** (tennis ball analogy)
- **Agency to steer conversations** toward their interests

### Exchange System Integration

- **Contested exchanges** for dialogue with stakes
- **Success/failure** determines conversational outcomes
- **Status shifts** reflect persuasion, rapport changes, etc.
- **No shifts** for trivial/phatic dialogue (apply_shift=false)

## Examples

### Example 1: Persuasion (Contested)

**UA Input:** "You should trust me - I've never let you down before, have I?"

**Interpretation:**
```json
{
  "action_noun": "persuade",
  "narrative_description": "attempts to persuade them by appealing to past reliability",
  "utas_factors": {
    "exchange_type": "Spirit",
    "status_to_shift": "SPIRIT",
    "s_trait_to_use": "SOCIABILITY",
    "s_trait_value": 3,
    "skill": {"name": "Persuasion", "value": 2},
    "stress_level": 2,
    "shift_polarity": "Additive"
  },
  "dialogue_metadata": {
    "dialogue_detected": true,
    "dialogue_intent": "Persuasion",
    "dialogue_weight": 2,
    "can_affect_status": true,
    "apply_shift": true
  }
}
```

**NUA Reaction (High Sympathy):**
"You know what? You're right. I'll help you out - but this better not blow up in my face like last time."

**NUA Reaction (Low Sympathy):**
"Never let me down? Are you kidding? You still owe me from that botched job in Sector 7. Get lost."

### Example 2: Trivial Greeting (Non-Contested)

**UA Input:** "Hey, how's it going?"

**Interpretation:**
```json
{
  "action_noun": "greet",
  "narrative_description": "casually greets them",
  "utas_factors": {
    "exchange_type": "Spirit",
    "status_to_shift": "SPIRIT",
    "s_trait_to_use": "SOCIABILITY",
    "s_trait_value": 3,
    "skill": {"name": "None", "value": 0},
    "stress_level": 1,
    "shift_polarity": "Additive"
  },
  "dialogue_metadata": {
    "dialogue_detected": true,
    "dialogue_intent": "SmallTalk",
    "dialogue_weight": 1,
    "can_affect_status": false,
    "apply_shift": false
  }
}
```

**NUA Reaction:**
"Not bad. You?"

(No status shift, natural conversational flow)

### Example 3: Insult (Contested, Negative)

**UA Input:** "Your mom's a bitch"

**Interpretation:**
```json
{
  "action_noun": "insult",
  "narrative_description": "delivers a crude insult about their mother",
  "utas_factors": {
    "exchange_type": "Sympathy",
    "status_to_shift": "SYMPATHY",
    "s_trait_to_use": "SOCIABILITY",
    "s_trait_value": 3,
    "skill": {"name": "None", "value": 0},
    "stress_level": 2,
    "shift_polarity": "Subtractive"
  },
  "dialogue_metadata": {
    "dialogue_detected": true,
    "dialogue_intent": "Insult",
    "dialogue_weight": 1,
    "can_affect_status": true,
    "apply_shift": true
  }
}
```

**NUA Reaction:**
"What did you just say? You better watch your mouth before I shut it for you."

(Sympathy shifts Subtractive, escalation likely)

### Example 4: Multi-Turn Negotiation

**Turn 1:**
- **UA:** "I need information about the warehouse break-in."
- **NUA:** "Information costs money. What's it worth to you?"

**Turn 2:**
- **UA:** "I can pay 100 credits."
- **NUA (Success):** "Alright, deal. Here's what I know..."
- **NUA (Failure):** "100? That's pocket change. Come back when you're serious."

**Turn 3 (if failed):**
- **UA:** "Fine, 200 credits."
- **NUA:** "Now we're talking. The break-in happened around midnight..."

Each turn is a contested UTAS exchange, but the conversation flows naturally.

## Benefits of This Approach

1. **Mechanical Consistency:** Dialogue uses the same rules as physical actions
2. **Natural Flow:** NPCs have agency and conversational goals
3. **Meaningful Stakes:** Persuasion, deception, and negotiation have real consequences
4. **Character Expression:** Personality and sympathy affect conversational style
5. **No Separate System:** Dialogue integrates seamlessly into existing UTAS mechanics
6. **Trivial Dialogue Handled:** Greetings don't require contested rolls
7. **Multi-Turn Support:** Conversations can develop over multiple exchanges

## Testing Checklist

- [ ] Trivial greeting ("Hello") → No status shift, brief NUA response
- [ ] Persuasion attempt → Contested SPIRIT exchange, success/failure affects outcome
- [ ] Insult → Contested SYMPATHY exchange, relationship damage
- [ ] Multi-turn conversation → NPCs reference previous topics, show personality
- [ ] NPC-initiated topics → NPCs steer conversation toward their goals
- [ ] Sympathy-based cooperation → High sympathy = helpful, low = guarded
- [ ] Deception → SHADOW vs. SMARTS exchange, success = believed
- [ ] Negotiation → SUPPLY/SYMPATHY exchange, back-and-forth offers

## Summary

Dialogue is now a **first-class UTAS action** that:
- Uses full UTAS mechanics when conversational stakes exist
- Maintains natural flow through NPC agency and personality
- Respects sympathy levels for cooperation
- Allows multi-turn conversations to develop organically
- Skips mechanical resolution for trivial/phatic communication
- Integrates seamlessly with existing combat, exploration, and social systems
