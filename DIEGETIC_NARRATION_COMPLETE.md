# ✅ Diegetic Narration System - COMPLETE!

## 🎯 What is Diegetic Narration?

**Diegetic** = Experienced from within the world, not told from outside

Instead of a narrator telling you about the world, you **experience** the world directly through sensory details and immediate actions.

---

## ❌ Before (Non-Diegetic):

```
The newsroom is eerily empty at this hour—most reporters won't trickle in 
until after the morning editorial meeting, which won't start until the clock 
strikes nine. The only sounds are the distant clatter of the night shift 
janitor and the occasional buzz of a dying lightbulb. Whoever you're looking 
for isn't here yet, but they will be soon.
```

**Problems:**
- Narrator tells you facts ("most reporters won't trickle in")
- External knowledge ("which won't start until the clock strikes nine")
- Narrator knows your intent ("Whoever you're looking for")
- Future predictions ("but they will be soon")

---

## ✅ After (Diegetic):

```
The newsroom stretches before you, empty. Rows of desks sit abandoned, 
typewriters silent. You hear the distant clatter of a janitor somewhere 
down the hall, the buzz of a dying lightbulb overhead. A wall clock reads 
7:43 AM—the morning editorial meeting doesn't start until nine. You scan 
the room. No one's here yet.
```

**Better because:**
- ✅ You observe the empty room (not told it's empty)
- ✅ You see the clock (not told the time)
- ✅ You scan for someone (not told they're not here)
- ✅ Everything is what YOU experience NOW

---

## 📋 The 5 Diegetic Rules

### **1. SHOW, DON'T TELL**
Describe what you SEE, HEAR, FEEL, DO - not abstract states

❌ **Non-Diegetic:** "The room is empty"
✅ **Diegetic:** "You scan the room. No one's here."

❌ **Non-Diegetic:** "You feel confident"
✅ **Diegetic:** "Your hands are steady, your breathing calm."

---

### **2. IMMEDIATE SENSORY**
Focus on what's happening RIGHT NOW in this moment

❌ **Non-Diegetic:** "This will be difficult"
✅ **Diegetic:** "Your muscles tense as you prepare"

❌ **Non-Diegetic:** "The room was once grand"
✅ **Diegetic:** "Faded wallpaper peels from the walls"

---

### **3. NO NARRATOR COMMENTARY**
You are experiencing this, not being told about it

❌ **Non-Diegetic:** "You are skilled at this"
✅ **Diegetic:** "The movement comes naturally"

❌ **Non-Diegetic:** "They are experienced fighters"
✅ **Diegetic:** "They move with practiced ease"

---

### **4. PRESENT TENSE, ACTIVE VOICE**
Everything happens NOW

❌ **Non-Diegetic:** "You were going to attack"
✅ **Diegetic:** "You lunge forward"

❌ **Non-Diegetic:** "The door had been locked"
✅ **Diegetic:** "The door won't budge. Locked."

---

### **5. CONCRETE ACTIONS**
Physical, tangible, observable actions and sensations

❌ **Non-Diegetic:** "You attempt to strike them"
✅ **Diegetic:** "You swing your fist toward their jaw"

❌ **Non-Diegetic:** "They seem nervous"
✅ **Diegetic:** "Their hands shake, eyes darting to the door"

---

## 🎮 Combat Example

### **Non-Diegetic (Old):**
```
The situation is challenging, but you act with purpose. Drawing upon your 
Adept 'Blade' skill and 'Precise' nature, you lunge forward, stabbing at 
your opponent's defenses. A bit of bad luck nearly throws you off balance, 
but you press the attack.
```

### **Diegetic (New):**
```
Your heart pounds as you grip the blade tighter. Drawing on muscle memory, 
you lunge forward, stabbing toward their guard. Your foot slips slightly 
on the wet floor—damn—but you push through, driving the point home.
```

**What Changed:**
- ✅ "Your heart pounds" (physical sensation) vs "challenging situation" (abstract)
- ✅ "muscle memory" (concrete) vs "Adept skill" (game mechanic)
- ✅ "foot slips on wet floor" (specific) vs "bad luck" (abstract)
- ✅ "damn" (internal thought) vs narrator commentary

---

## 🔧 Implementation

### **File Modified:** `agents/narrator_agent.py`

**Lines 453-471:** User Actor (second person) prompt
**Lines 497-515:** NUA (third person) prompt

### **What Was Added:**

```python
**CRITICAL - DIEGETIC NARRATION RULES:**
1. **SHOW, DON'T TELL:** Describe what you SEE, HEAR, FEEL, DO
2. **IMMEDIATE SENSORY:** Focus on what's happening RIGHT NOW
3. **NO NARRATOR COMMENTARY:** You are experiencing this
4. **PRESENT TENSE, ACTIVE VOICE:** Everything happens NOW
5. **CONCRETE ACTIONS:** Physical, tangible, observable
```

---

## 📊 Before vs After Comparison

| Aspect | Non-Diegetic | Diegetic |
|--------|--------------|----------|
| **Perspective** | Narrator tells you | You experience |
| **Time** | Past/Future references | Present moment only |
| **Knowledge** | Omniscient narrator | Limited to senses |
| **Tone** | Explanatory | Immersive |
| **Focus** | Abstract concepts | Concrete details |

---

## 🎯 Examples Across Scenarios

### **Exploration:**

❌ **Non-Diegetic:**
"The warehouse is abandoned and dangerous. You should be careful."

✅ **Diegetic:**
"Broken glass crunches under your boots. The warehouse stretches into darkness ahead, rusted machinery looming like sleeping giants."

---

### **Social Interaction:**

❌ **Non-Diegetic:**
"The bartender seems friendly but is actually suspicious of you."

✅ **Diegetic:**
"The bartender flashes a smile as he slides your drink across the bar. But his eyes linger on you a beat too long, and his hand stays near the phone."

---

### **Investigation:**

❌ **Non-Diegetic:**
"You find clues that suggest someone was here recently."

✅ **Diegetic:**
"A coffee cup sits on the desk, still warm to the touch. Cigarette ash dusts the keyboard. The chair is pulled back, as if someone just stood up."

---

### **Stealth:**

❌ **Non-Diegetic:**
"You successfully sneak past the guard using your high Shadow stat."

✅ **Diegetic:**
"You press against the wall, holding your breath. The guard's footsteps echo closer—closer—then fade as he turns the corner. You exhale slowly and move."

---

## 💡 Writing Tips

### **Use Sensory Details:**
- **Sight:** Colors, shapes, movement
- **Sound:** Volume, pitch, rhythm
- **Touch:** Texture, temperature, pressure
- **Smell:** Scents, odors, aromas
- **Taste:** Flavors (when relevant)

### **Use Internal Sensations:**
- Heart pounding
- Muscles tensing
- Breath catching
- Hands shaking
- Stomach dropping

### **Use Concrete Verbs:**
- ❌ "move" → ✅ "lunge, creep, stumble, dash"
- ❌ "look" → ✅ "scan, peer, squint, glance"
- ❌ "hit" → ✅ "punch, slash, slam, strike"

### **Use Specific Details:**
- ❌ "a weapon" → ✅ "a rusted crowbar"
- ❌ "the room" → ✅ "the cramped office"
- ❌ "someone" → ✅ "a wiry man with a cigarette"

---

## 🎬 Scene Comparison

### **Non-Diegetic Scene:**
```
You enter the diner. It's a typical 1980s establishment with a jukebox 
and vinyl booths. There are a few customers inside. The waitress will 
probably come over soon to take your order. You notice a suspicious 
character in the back who might be important to your investigation.
```

### **Diegetic Scene:**
```
The diner door swings shut behind you with a jingle. Neon light from the 
jukebox bathes the vinyl booths in pink and blue. A couple nurses their 
coffee at the counter. The smell of bacon grease hangs thick in the air.

A waitress glances up from wiping down a table, catching your eye.

In the back corner, a man in a worn leather jacket hunches over his plate, 
eyes flicking to you before dropping back to his food.
```

---

## ✅ Benefits

### **For Immersion:**
- ✅ Feels like you're THERE
- ✅ No "narrator voice" breaking immersion
- ✅ Direct sensory experience

### **For Agency:**
- ✅ You discover things yourself
- ✅ You interpret what you see
- ✅ No hand-holding

### **For Atmosphere:**
- ✅ More cinematic
- ✅ More immediate
- ✅ More visceral

---

## 🚀 Status: COMPLETE

**Diegetic narration rules are now enforced in all turn narratives!**

- ✅ User Actor (second person) prompts updated
- ✅ NUA (third person) prompts updated
- ✅ 5 core rules integrated
- ✅ Examples provided to LLM
- ✅ Show vs Tell enforced

**Your simulation now generates immersive, experiential narration!** 🎬✨

---

## 📝 Quick Reference

**When writing/reviewing narration, ask:**

1. ❓ Am I SHOWING or TELLING?
2. ❓ Is this happening NOW or being explained?
3. ❓ Would the character know this?
4. ❓ Is this concrete or abstract?
5. ❓ Can I make this more sensory?

**If any answer is wrong → Revise to be more diegetic!**
