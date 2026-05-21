# Do Nothing Action - User Guide

## Philosophy

**In real life, you can choose to do nothing.** This is a valid choice that:
- Lets time pass naturally
- Allows you to observe without acting
- Gives you moments to think and reflect
- Lets the world continue around you
- Provides rest and recovery

**The simulation should reflect this reality.**

---

## How to Do Nothing

Simply type any of these commands:

### **Explicit Nothing:**
- `I do nothing`
- `I'm doing nothing`

### **Waiting:**
- `I wait`
- `I wait here`
- `waiting`

### **Observing:**
- `I observe`
- `I watch`
- `I just look around`
- `I take it in`

### **Resting:**
- `I rest`
- `I take a break`
- `I catch my breath`
- `I pause`

### **Thinking:**
- `I think`
- `I reflect`
- `I contemplate`
- `I ponder`
- `I gather my thoughts`
- `I consider my options`

### **Staying Still:**
- `I stand still`
- `I sit still`
- `I stay still`
- `I don't move`
- `I stay put`

---

## What Happens

### **1. Time Advances**
Doing nothing still takes time (typically 3-MINUTE category):
```
You: "I wait"
System: "Time flows by as you wait. Nothing urgent demands your attention."
⏰ Time: Day 1, 9:05 AM
```

### **2. World Continues**
The world doesn't pause just because you do:
```
While you do nothing, the world continues around you...
```

**NPCs might:**
- Continue their activities
- Talk to each other
- Move around
- React to the environment

**Events might:**
- Unfold naturally
- Trigger based on time
- Happen in the background

### **3. Observation Opportunities**
Doing nothing gives you a chance to notice things:
```
You: "I observe"
System: "You take a moment to simply observe your surroundings. 
         Details you hadn't noticed before catch your eye."
```

### **4. Recovery (for some types)**
Certain types of doing nothing allow recovery:
- **Rest** - May recover stamina/spirit slightly
- **Think** - May provide mental clarity

---

## Use Cases

### **1. Waiting for Something**
```
Scenario: You're early for a meeting
You: "I wait"
Result: Time passes until the meeting time
```

### **2. Observing a Situation**
```
Scenario: NPCs are arguing, you want to see how it plays out
You: "I observe"
Result: You watch the argument unfold without interfering
```

### **3. Catching Your Breath**
```
Scenario: Just finished a chase, need a moment
You: "I rest"
Result: You take a breather, possibly recovering some stamina
```

### **4. Thinking Things Through**
```
Scenario: Multiple options, need to consider
You: "I think about my options"
Result: Time to reflect on your situation
```

### **5. Letting Events Unfold**
```
Scenario: Waiting to see if someone shows up
You: "I wait and watch"
Result: Time passes, events may or may not occur
```

---

## Comparison with Other Actions

### **Do Nothing vs Meta Commands**

**Meta Commands** (don't advance time):
- `look` - Reprint scene
- `ua` - View character sheet
- `people` - List NPCs
- `map` - View map

**Do Nothing** (DOES advance time):
- `wait` - Time passes
- `observe` - Time passes
- `rest` - Time passes

### **Do Nothing vs Active Actions**

**Active Actions:**
- `I search the room` - You actively do something
- `I talk to the guard` - You initiate interaction
- `I walk to the door` - You move

**Do Nothing:**
- `I wait` - You passively let time flow
- `I observe` - You watch without acting
- `I rest` - You pause without moving

---

## Strategic Uses

### **1. Time Management**
```
Scenario: Restaurant opens at 11am, it's 10:45am
You: "I wait"
Result: Time advances to 11am, restaurant is now open
```

### **2. Stealth/Patience**
```
Scenario: Guard patrol, waiting for them to pass
You: "I stay still"
Result: You remain motionless as the guard walks by
```

### **3. Information Gathering**
```
Scenario: Eavesdropping on a conversation
You: "I listen and observe"
Result: You passively gather information
```

### **4. Recovery**
```
Scenario: Low stamina, need to recover
You: "I rest for a bit"
Result: Brief recovery period
```

### **5. Letting NPCs Act**
```
Scenario: Want to see what NPCs do on their own
You: "I do nothing"
Result: NPCs continue their activities, you observe
```

---

## For NPCs and INUAs

**NPCs can also do nothing!** This creates a more realistic world:

### **NPC Doing Nothing:**
- Guard standing watch (doing nothing)
- Shopkeeper waiting for customers (doing nothing)
- Person sitting on a bench (doing nothing)

### **INUA Doing Nothing:**
- Tree standing in the wind (doing nothing)
- Rock sitting in place (doing nothing)
- Door remaining closed (doing nothing)

**This is realistic** - not everything is always in motion.

---

## Technical Details

### **Time Cost:**
- Default: 3-MINUTE category
- Approximately 3 minutes of in-game time pass

### **Events Allowed:**
- Random encounters can trigger
- NPCs can act
- Environmental changes can occur
- Sparks can appear

### **Recovery Potential:**
- `rest` type: May allow minor stamina/spirit recovery
- `think` type: May provide mental clarity
- Other types: No direct recovery

### **Integration:**
- Checked after Intent Availability
- Processed before normal action interpretation
- Advances time through master time coordinator
- Updates time context automatically

---

## Examples in Practice

### **Example 1: Simple Wait**
```
You: "I wait"

System: "Time flows by as you wait. Nothing urgent demands your attention."
⏰ Time: Day 1, 9:05 AM

[Next turn begins]
```

### **Example 2: Observing**
```
You: "I observe my surroundings"

System: "You take a moment to simply observe your surroundings. 
         Details you hadn't noticed before catch your eye."
⏰ Time: Day 1, 9:05 AM

[You might notice new details in the scene]
```

### **Example 3: Resting**
```
You: "I rest for a moment"

System: "You take a moment to catch your breath. The brief respite is welcome."
⏰ Time: Day 1, 9:05 AM

[Possible minor stamina recovery]
```

### **Example 4: World Continues**
```
You: "I do nothing"

System: "You do nothing in particular. Time passes."
⏰ Time: Day 1, 9:05 AM

While you do nothing, the world continues around you...

[NPCs might act, events might trigger]
```

---

## Benefits

### **1. Realism**
- Reflects real-life option to do nothing
- Not every moment requires action
- Sometimes patience is the best choice

### **2. Player Agency**
- Choice to act or not act
- Control over pacing
- Strategic waiting

### **3. Living World**
- World doesn't pause for you
- NPCs continue their lives
- Events unfold naturally

### **4. Tactical Options**
- Wait for right moment
- Observe before acting
- Recover before next action
- Let situations develop

### **5. Immersion**
- Natural flow of time
- Realistic behavior
- No forced action

---

## Summary

**Doing nothing is a valid action.**

You can:
- ✅ Wait for time to pass
- ✅ Observe without acting
- ✅ Rest and recover
- ✅ Think and reflect
- ✅ Let the world continue

**The simulation respects your choice to do nothing, just like real life.**

Time will pass. The world will continue. Events may unfold. And you'll have chosen to simply be, rather than do.

**Sometimes, doing nothing is exactly the right thing to do.**
