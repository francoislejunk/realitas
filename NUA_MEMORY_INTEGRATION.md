# NUA Memory System Integration

## Overview

Integrated the NUA Memory System into the main simulation loop to enable **persistent relationship building** and **meaningful NUA reactions** based on past interactions. NUAs now remember everything you do and use those memories when deciding how to react.

---

## What Was Integrated

### 1. **Memory Recording (Main Loop)**

**File: `MAIN/redesigned_main.py` (lines 8532-8614)**

Added automatic memory recording after every contested exchange:

#### **Threat Detection**
- **Trigger**: SPIRIT/Subtractive exchange with threatening keywords
- **Keywords**: threaten, intimidate, weapon, gun, knife, hurt, kill, attack
- **Condition**: Proactor wins the exchange
- **Records**: `nua_memory_system.record_threat()`
- **Importance**: 4 (🟡 Important)

```python
# Example: "I threaten the guard with my gun"
→ Exchange: SPIRIT/Subtractive
→ Winner: Player
→ Memory: "🟡 Guard remembers: Player threatened with gun..."
→ Auto-saved to disk
```

#### **Help Detection**
- **Trigger**: Any Additive exchange with helpful keywords
- **Keywords**: help, heal, give, assist, support, aid, protect, save
- **Condition**: Proactor wins the exchange
- **Records**: `nua_memory_system.record_help()`
- **Importance**: 3 (🔵 Notable)

```python
# Example: "I give the merchant food"
→ Exchange: SUPPLY/Additive
→ Winner: Player
→ Memory: "🔵 Merchant remembers: Player gave food..."
→ Auto-saved to disk
```

#### **Violence Detection**
- **Trigger**: STAMINA/Subtractive exchange (physical attack)
- **Condition**: Proactor wins the exchange
- **Records**: 
  - `nua_memory_system.record_event()` for victim
  - `nua_memory_system.record_witnessed_violence()` for bystanders
- **Importance**: 4-5 (🟡-🔴 Important/Critical)

```python
# Example: "I attack the guard" (Bartender is present)
→ Exchange: STAMINA/Subtractive
→ Winner: Player
→ Memory (Guard): "🟡 Guard remembers: Player attacked..."
→ Memory (Bartender): "🔴 Bartender remembers: Witnessed Player attack Guard..."
→ Auto-saved to disk
```

#### **Conversation Detection**
- **Trigger**: Dialogue with significant intent
- **Intents**: Inquiry, Persuasion, Negotiation, Story, Command
- **Excludes**: SmallTalk (trivial conversations)
- **Records**: `nua_memory_system.record_conversation()`
- **Importance**: 2 (⚪ Minor - saved but not displayed)

```python
# Example: "I ask the bartender about local rumors"
→ Dialogue Intent: Inquiry
→ Memory: Saved but not displayed (minor importance)
→ Auto-saved to disk
```

---

### 2. **Memory Retrieval (DeciderAgent)**

**File: `agents/decider_agent.py` (lines 1018-1052)**

Added memory retrieval when NUAs decide how to react:

#### **What It Does**
- Retrieves memories about the proactor before generating reaction
- Injects memory context into the LLM prompt
- Instructs LLM to use memories to inform emotional state and reaction choice

#### **Memory Context Injection**
```
**🧠 MEMORY CONTEXT - What [NUA] Remembers About [Player]:**
[Memory details from past interactions]

**CRITICAL: Use these memories to inform your reaction:**
- If they threatened you before → Be cautious, defensive, or fearful
- If they helped you before → Be grateful, cooperative, or friendly
- If you witnessed them commit violence → Be wary or traumatized
- If you had significant conversations → Reference past topics or build on them
- Memories should DIRECTLY influence your emotional state and reaction choice
```

---

## How It Works (Full Flow)

### **Example 1: Building Trust Through Help**

**Session 1 - First Meeting:**
```
You: "I help the merchant with their cart"
→ Exchange: Additive
→ Winner: Player
→ Memory: "🔵 Merchant remembers: Player helped with cart..."
→ Sympathy: 0 → +1
→ Saved to disk
```

**Session 1 - Later:**
```
You: "I give the merchant money"
→ Exchange: SUPPLY/Additive
→ Winner: Player
→ Memory: "🔵 Merchant remembers: Player gave money..."
→ Sympathy: +1 → +2
→ Saved to disk
```

**Session 2 - Next Day (after restart):**
```
You: "I talk to the merchant"
→ DeciderAgent retrieves memories:
  - "Player helped with cart"
  - "Player gave money"
→ Merchant's reaction: Grateful, cooperative, friendly
→ Dialogue: "Hey friend! Good to see you again. After everything you've done for me..."
```

---

### **Example 2: Creating Fear Through Threats**

**Session 1:**
```
You: "I threaten the guard with my gun"
→ Exchange: SPIRIT/Subtractive
→ Winner: Player
→ Memory: "🟡 Guard remembers: Player threatened with gun..."
→ Sympathy: 0 → -1
→ Saved to disk
```

**Session 2 - Days Later:**
```
You: "I approach the guard"
→ DeciderAgent retrieves memory: "Player threatened with gun"
→ Guard's reaction: Cautious, defensive, fearful
→ Dialogue: "Stay back! I remember what you did last time..."
→ May flee or call for backup
```

---

### **Example 3: Witness Trauma**

**Session 1:**
```
You: "I attack the merchant" (Guard is watching)
→ Exchange: STAMINA/Subtractive
→ Winner: Player
→ Memory (Merchant): "🟡 Merchant remembers: Player attacked..."
→ Memory (Guard): "🔴 Guard remembers: Witnessed Player attack Merchant..."
→ Both saved to disk
```

**Session 2:**
```
You: "I talk to the guard"
→ DeciderAgent retrieves memory: "Witnessed Player attack Merchant"
→ Guard's reaction: Wary, traumatized, hostile
→ Dialogue: "I saw what you did to that merchant. Get away from me!"
→ May report to authorities or attack preemptively
```

---

## Memory Importance Levels

```
5 = 🔴 CRITICAL   - Witnessed violence, death (always saved, always displayed)
4 = 🟡 IMPORTANT  - Threats, violence received (always saved, always displayed)
3 = 🔵 NOTABLE    - Help received, important events (saved and displayed)
2 = ⚪ MINOR      - Conversations (saved but not displayed)
1 = ⚫ TRIVIAL    - Small talk (NOT saved)
```

---

## Integration Points

### **Recording (Main Loop)**
- **Location**: `MAIN/redesigned_main.py` lines 8532-8614
- **Trigger**: After every contested exchange
- **Auto-save**: Yes (every recording saves to disk)
- **Error handling**: Silently fails (won't break simulation)

### **Retrieval (DeciderAgent)**
- **Location**: `agents/decider_agent.py` lines 1018-1052
- **Trigger**: Before every NUA reaction decision
- **Fallback**: Empty string if no memories (won't break decision)
- **Error handling**: Silently fails (decision continues without memories)

---

## Storage

**File**: `./simulation_data/nua_memories/nua_memories.json`

**Format**:
```json
{
  "nua_memories": {
    "Guard": {
      "nua_name": "Guard",
      "memories": [
        {
          "event_type": "threat",
          "description": "Player threatened with gun",
          "actors_involved": ["Player"],
          "importance": 4,
          "emotional_impact": "fearful",
          "timestamp": "2024-01-15T10:30:00"
        }
      ],
      "threats_received": [...],
      "help_received": [...],
      "witnessed_events": [...]
    }
  },
  "last_updated": "2024-01-15T10:30:00"
}
```

---

## Benefits

### **1. Persistent Relationships**
- ✅ NUAs remember everything across sessions
- ✅ Relationships evolve based on your actions
- ✅ Trust builds over time through repeated help
- ✅ Fear accumulates through repeated threats

### **2. Meaningful Consequences**
- ✅ Threatening someone has lasting effects
- ✅ Helping someone creates gratitude
- ✅ Violence creates trauma and witnesses
- ✅ Conversations build rapport

### **3. Realistic NUA Behavior**
- ✅ NUAs react based on history, not just current action
- ✅ Emotional states influenced by past experiences
- ✅ Relationship context affects cooperation
- ✅ Characters feel alive and remember

### **4. Emergent Storytelling**
- ✅ Long-term relationship arcs
- ✅ Reputation systems (witnesses spread word)
- ✅ Redemption arcs (helping after threatening)
- ✅ Betrayal impact (breaking trust)

---

## Example Scenarios

### **Scenario 1: The Redeemed Thief**
```
Day 1: Threaten merchant → Merchant fears you
Day 2: Help merchant → Merchant confused but grateful
Day 3: Help merchant again → Merchant trusts you
Day 5: Ask merchant for favor → Merchant helps willingly
```

### **Scenario 2: The Witnessed Crime**
```
Day 1: Attack guard (bartender watches)
→ Guard traumatized
→ Bartender traumatized
→ Both remember

Day 2: Enter bar
→ Bartender: "I saw what you did! Get out!"
→ May call guards or refuse service

Day 3: Approach guard
→ Guard: "Stay back! I know what you're capable of!"
→ May flee or attack preemptively
```

### **Scenario 3: The Trusted Ally**
```
Day 1: Help NPC with task
Day 2: Give NPC resources
Day 3: Protect NPC from danger
Day 5: NPC volunteers to help you
Day 10: NPC trusts you with secrets
Day 20: NPC considers you a close friend
```

---

## Technical Details

### **Memory Detection Keywords**

**Threats:**
- threaten, intimidate, weapon, gun, knife, hurt, kill, attack

**Help:**
- help, heal, give, assist, support, aid, protect, save

**Violence:**
- Detected by exchange type (STAMINA/Subtractive)

**Conversations:**
- Detected by dialogue_intent (Inquiry, Persuasion, Negotiation, Story, Command)

### **Error Handling**
- All memory operations wrapped in try-except
- Failures are silent (won't break simulation)
- Warnings displayed for debugging
- Simulation continues even if memory system fails

### **Performance**
- Memory retrieval is fast (single file read)
- Auto-save after each recording (minimal overhead)
- No impact on exchange calculation speed
- Memories filtered by relevance (only shows related memories)

---

## Testing Checklist

### **Test 1: Threat Memory**
- [ ] Threaten an NUA
- [ ] See "🟡 [NUA] remembers: [threat]..." message
- [ ] Restart simulation
- [ ] Interact with same NUA
- [ ] NUA should be cautious/fearful

### **Test 2: Help Memory**
- [ ] Help an NUA
- [ ] See "🔵 [NUA] remembers: [help]..." message
- [ ] Restart simulation
- [ ] Interact with same NUA
- [ ] NUA should be grateful/cooperative

### **Test 3: Violence Witness**
- [ ] Attack NUA with another NUA present
- [ ] See "🔴 [Witness] remembers: Witnessed..." message
- [ ] Restart simulation
- [ ] Interact with witness
- [ ] Witness should be wary/traumatized

### **Test 4: Conversation Memory**
- [ ] Have significant conversation (Inquiry/Persuasion)
- [ ] Memory saved (not displayed - importance 2)
- [ ] Restart simulation
- [ ] Continue conversation
- [ ] NUA should reference past topics

---

## Future Enhancements

### **Potential Additions:**
1. **Memory Decay** - Old memories fade over time
2. **Memory Sharing** - NUAs tell each other about you
3. **Reputation System** - Word spreads about your actions
4. **Memory Triggers** - Specific events trigger flashbacks
5. **Emotional Intensity** - Stronger memories have more impact
6. **Forgiveness Mechanics** - Ability to repair damaged relationships

---

## Summary

✅ **Memory Recording**: Automatically tracks threats, help, violence, and conversations  
✅ **Memory Retrieval**: NUAs remember past interactions when deciding reactions  
✅ **Persistent Storage**: All memories saved to disk and persist across sessions  
✅ **Meaningful Impact**: Memories directly influence NUA emotional states and behavior  
✅ **Error Resilient**: System fails gracefully without breaking simulation  

**Result**: NUAs now feel alive, remember your actions, and build meaningful relationships over time. Your choices have lasting consequences that persist across sessions.
