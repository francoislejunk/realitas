# Context Persistence Integration Guide

## 🎯 **Problem Solved**

**BEFORE:** Context was lost between turns, causing the narrator to forget:
- Where we are
- Who's present
- What just happened
- What we were doing

**AFTER:** Every piece of context is saved to disk immediately and loaded on every access. Context is NEVER lost.

---

## 📦 **What Was Created**

### **File:** `persistent_context_manager.py`

A comprehensive context persistence system that:
- ✅ Saves EVERY context update to disk IMMEDIATELY
- ✅ Loads context on EVERY access (always fresh)
- ✅ Multiple backup files (never lose data)
- ✅ Automatic recovery from corruption
- ✅ History tracking (every 10 updates)
- ✅ Context validation and repair

---

## 🔧 **How to Integrate**

### **Step 1: Import in `redesigned_main.py`**

Add at the top of the file:

```python
from persistent_context_manager import (
    PersistentContextManager,
    get_context_manager
)
```

### **Step 2: Initialize Context Manager**

Replace the current context initialization with:

```python
# Initialize persistent context manager (NEVER LOSE CONTEXT)
context_manager = get_context_manager(session_id=tracker.session_id)

# Load existing context if resuming session
if context_manager.context.current_location != "unknown":
    print(f"\n{Color.SUCCESS}📍 Resuming from: {context_manager.context.current_location}{Color.RESET}")
    scene_description = context_manager.get_scene_description()
    available_npcs = []  # Will be reconstructed from context
    print(context_manager.get_context_summary())
```

### **Step 3: Update Context on Scene Changes**

**Location:** Wherever `scene_description` is updated

```python
# OLD
scene_description = new_scene

# NEW
scene_description = new_scene
context_manager.update_scene_description(scene_description)
```

### **Step 4: Update Context on Location Changes**

**Location:** In `_apply_location_move()`

```python
def _apply_location_move(conductor, move_label, time_context, actor, prev_desc, 
                        narrative_context_manager, tracker):
    # ... existing code ...
    
    # Generate new scene
    new_scene = conductor.generate_scene_description(scene_data, ...)
    
    # SAVE TO PERSISTENT CONTEXT
    context_manager = get_context_manager()
    context_manager.update_location(
        location=move_label,
        scene_description=new_scene,
        location_label=move_label
    )
    
    return new_scene
```

### **Step 5: Update Context on NPC Changes**

**Location:** Wherever NPCs are added/removed

```python
# When NPC is added
spark_nua = spark_generator.create_nua_from_spark(spark_data)
available_npcs.append(spark_nua)

# SAVE TO PERSISTENT CONTEXT
context_manager = get_context_manager()
context_manager.add_npc(spark_nua.sheet.name, npc_id=str(id(spark_nua)))

# When NPC is removed
removed_names = _prune_npcs_by_outcome_text(available_npcs, recent_texts)
for name in removed_names:
    context_manager.remove_npc(name)

# When location changes (clear all NPCs)
context_manager.set_npcs([])
```

### **Step 6: Update Context on Narrative Events**

**Location:** After every narrative generation

```python
# After narrator generates narrative
last_action_narrative = narrator.narrate_action(...)

# SAVE TO PERSISTENT CONTEXT
context_manager = get_context_manager()
context_manager.add_narrative(last_action_narrative)
context_manager.add_event(f"User: {user_input}")
```

### **Step 7: Update Context on User Actions**

**Location:** After user input is processed

```python
# After interpreting user action
input_analysis = interpreter.detect_inquiry_or_action(user_input, actor, reactor)

# SAVE TO PERSISTENT CONTEXT
context_manager = get_context_manager()
context_manager.update_user_action(
    action=user_input,
    intent=input_analysis.get('reasoning', ''),
    confidence=0.8 if input_analysis.get('confidence') == 'high' else 0.5
)
```

### **Step 8: Inject Context into LLM Prompts**

**Location:** In narrator, interpreter, and conductor prompts

```python
# Get persistent context
context_manager = get_context_manager()
context_text = context_manager.get_context_for_llm()

# Add to prompt
prompt = f"""
{context_text}

**YOUR TASK:**
Generate a narrative response that respects the current context above.

**CRITICAL RULES:**
- Use the current location: {context_manager.get_location()}
- Only mention NPCs who are present: {', '.join(context_manager.get_npcs())}
- Reference recent events to maintain continuity
- DO NOT revert to the initial scene
- DO NOT forget where we are

{rest_of_prompt}
"""
```

---

## 🔄 **Integration Points**

### **1. Scene Description Updates**

```python
# Anywhere scene_description is modified
context_manager.update_scene_description(scene_description)
```

**Locations to update:**
- `_apply_location_move()` - Line ~810
- After conductor generates scene - Line ~1733
- After spark integration - Line ~5113
- After encounter resolution - Line ~162

### **2. NPC Management**

```python
# When adding NPC
context_manager.add_npc(npc_name, npc_id)

# When removing NPC
context_manager.remove_npc(npc_name)

# When clearing all NPCs (location change)
context_manager.set_npcs([])
```

**Locations to update:**
- Spark generation - Line ~5108
- Dynamic actor spawning
- Location changes - Line ~810
- NPC pruning - Line ~1251

### **3. Narrative Events**

```python
# After every narrative generation
context_manager.add_narrative(narrative_text)
context_manager.add_event(f"User: {user_input}")
```

**Locations to update:**
- After narrator.narrate_action() - Line ~2550
- After narrator.narrate_given_action() - Line ~2399
- After encounter narratives - Line ~3938

### **4. Context Extraction**

```python
# After enhanced narrative loop extracts context
framing = narrative_loop.process_turn(...)
context = framing.get('context', {})

# Save extracted context
context_manager.set_opportunities(context.get('opportunities', []))
context_manager.set_visible_objects(context.get('visible_objects', []))
context_manager.update_atmosphere(
    location_atmosphere=context.get('atmosphere'),
    social_atmosphere=context.get('social_atmosphere')
)
```

**Locations to update:**
- After narrative_loop.process_turn() - Line ~2549, 2398, 2049, etc.

### **5. LLM Prompt Enhancement**

```python
# In narrator_agent.py, interpreter_agent.py, conductor_agent.py
context_manager = get_context_manager()
context_text = context_manager.get_context_for_llm()

prompt = f"""
{context_text}

{original_prompt}
"""
```

**Files to update:**
- `agents/narrator_agent.py` - All narration methods
- `agents/interpreter_agent.py` - Action interpretation
- `agents/conductor_agent.py` - Scene generation

---

## 📊 **Context File Structure**

### **Primary File:** `simulation_data/context/context_<session_id>.json`

```json
{
  "session_id": "20251014_065400",
  "current_location": "Rusty's Diner",
  "current_scene_description": "The diner hums with the low buzz...",
  "location_label": "diner",
  "present_npcs": ["Lena", "Vince 'Grease' Morrison"],
  "available_npc_ids": ["actor_lena", "actor_vince"],
  "recent_events": [
    "User: I enter the diner",
    "User: I talk to the waitress",
    "User: I ask about the garage"
  ],
  "recent_narratives": [
    "You step into the diner...",
    "Lena approaches with a warm smile...",
    "She points toward the window..."
  ],
  "opportunities": ["order food", "talk to Lena", "talk to Vince"],
  "visible_objects": ["jukebox", "counter", "booths", "bulletin board"],
  "location_atmosphere": "peaceful",
  "time_of_day": "morning",
  "weather": "clear",
  "narrative_mode": "spark",
  "narrative_tone": "calm",
  "user_last_action": "I ask about the garage",
  "user_last_intent": "Find information about garage location",
  "user_intent_confidence": 0.8,
  "last_updated": "2025-10-14T06:54:23.123456",
  "update_count": 47
}
```

### **Backup File:** `simulation_data/context/context_<session_id>_backup.json`

Identical to primary file, updated simultaneously.

### **History Files:** `simulation_data/context/history/context_<session_id>_<update_count>.json`

Saved every 10 updates for recovery.

---

## 🛡️ **Safety Features**

### **1. Dual File System**
- Primary file + Backup file
- If primary corrupts, loads from backup
- Both updated simultaneously

### **2. History Tracking**
- Saves snapshot every 10 updates
- Can recover from any historical state
- Useful for debugging context loss

### **3. Automatic Reload**
- Reloads from disk on every `get_context()` call
- Ensures always using latest data
- Protects against stale in-memory state

### **4. Validation & Repair**
```python
# Check for issues
issues = context_manager.validate_context()
if issues:
    print(f"Context issues: {issues}")
    context_manager.repair_context()
```

### **5. Context Dumping**
```python
# For debugging
context_manager.dump_context()
# Creates timestamped dump file
```

---

## 🎮 **Usage Examples**

### **Example 1: Scene Transition**

```python
# User moves to diner
user_input = "I go to the diner"

# Detect location move
move_label = _detect_location_move(user_input)  # Returns "diner"

# Generate new scene
new_scene = conductor.generate_scene_description(...)

# SAVE CONTEXT IMMEDIATELY
context_manager = get_context_manager()
context_manager.update_location(
    location="Rusty's Diner",
    scene_description=new_scene,
    location_label="diner"
)

# Context is now saved to disk
# If simulation crashes, we can resume from "Rusty's Diner"
```

### **Example 2: NPC Arrival**

```python
# SPARK generates new NPC
spark_data = spark_generator.generate_spark(...)
spark_nua = spark_generator.create_nua_from_spark(spark_data)
available_npcs.append(spark_nua)

# SAVE CONTEXT IMMEDIATELY
context_manager = get_context_manager()
context_manager.add_npc(
    npc_name=spark_nua.sheet.name,
    npc_id=f"actor_{spark_nua.sheet.name.lower().replace(' ', '_')}"
)

# Context now knows this NPC is present
# Narrator will include them in descriptions
```

### **Example 3: Narrative Generation with Context**

```python
# Get current context
context_manager = get_context_manager()
context_text = context_manager.get_context_for_llm()

# Build narrator prompt
prompt = f"""
{context_text}

**NARRATION TASK:**
Describe the result of the user's action: "{user_input}"

**CRITICAL CONSTRAINTS:**
- Location: {context_manager.get_location()}
- NPCs Present: {', '.join(context_manager.get_npcs())}
- Recent Events: {context_manager.get_recent_events(3)}

Generate a narrative that maintains continuity with the above context.
"""

# Generate narrative
narrative = narrator._call_llm(prompt)

# SAVE NARRATIVE TO CONTEXT
context_manager.add_narrative(narrative)
context_manager.add_event(f"User: {user_input}")
```

### **Example 4: Resuming Session**

```python
# On simulation start
context_manager = get_context_manager(session_id="20251014_065400")

# Check if we have existing context
if context_manager.context.update_count > 0:
    print("Resuming existing session...")
    print(context_manager.get_context_summary())
    
    # Restore scene
    scene_description = context_manager.get_scene_description()
    
    # Restore NPCs (would need to reconstruct Actor objects)
    npc_names = context_manager.get_npcs()
    print(f"NPCs present: {', '.join(npc_names)}")
    
    # Continue from where we left off
else:
    print("Starting new session...")
```

---

## ⚠️ **Critical Integration Points**

### **Must Update These Functions:**

1. **`_apply_location_move()`** - Save location changes
2. **`_prune_npcs_by_outcome_text()`** - Save NPC removals
3. **`narrator.narrate_action()`** - Save narratives
4. **`narrative_loop.process_turn()`** - Save extracted context
5. **All LLM prompts** - Inject context

### **Must Add Context Injection To:**

1. **`NarratorAgent._call_llm()`**
2. **`InterpreterAgent.detect_inquiry_or_action()`**
3. **`ConductorAgent.generate_scene_description()`**
4. **`DeciderAgent` (NUA actions)**

---

## 🧪 **Testing the Integration**

### **Test 1: Context Persistence**

```python
# Start simulation
# Move to diner
# Check: simulation_data/context/context_*.json exists
# Verify: current_location = "diner"

# Restart simulation
# Check: Loads from diner, not initial scene
```

### **Test 2: NPC Tracking**

```python
# SPARK generates NPC
# Check: present_npcs includes new NPC
# Move to different location
# Check: present_npcs is cleared
```

### **Test 3: Narrative Continuity**

```python
# Perform action
# Check: recent_events includes action
# Check: recent_narratives includes result
# Next narration should reference recent events
```

### **Test 4: Context Recovery**

```python
# Simulate crash (kill process)
# Restart simulation
# Check: Context is restored from backup
# Check: Can continue from last known state
```

---

## 📝 **Implementation Checklist**

- [ ] Import `persistent_context_manager` in `redesigned_main.py`
- [ ] Initialize context manager with session ID
- [ ] Update `_apply_location_move()` to save location
- [ ] Update scene description assignments to save context
- [ ] Update NPC additions to save context
- [ ] Update NPC removals to save context
- [ ] Update narrative generation to save narratives
- [ ] Inject context into narrator prompts
- [ ] Inject context into interpreter prompts
- [ ] Inject context into conductor prompts
- [ ] Add context summary display on startup
- [ ] Test context persistence across restarts
- [ ] Test NPC tracking
- [ ] Test narrative continuity
- [ ] Test context recovery from backup

---

## 🎯 **Expected Results**

After integration, you should see:

✅ **No more context loss** - System always knows where you are
✅ **No more reverting to initial scene** - Current scene is always saved
✅ **No more forgetting NPCs** - Who's present is always tracked
✅ **No more broken continuity** - Recent events are always remembered
✅ **Crash recovery** - Can resume from last saved state
✅ **Better narration** - LLMs have full context in prompts

---

## 🚨 **Critical Success Factors**

1. **Save IMMEDIATELY** - Don't batch updates, save after every change
2. **Load ALWAYS** - Reload from disk on every access
3. **Inject EVERYWHERE** - Add context to ALL LLM prompts
4. **Validate CONSTANTLY** - Check context integrity
5. **Backup EVERYTHING** - Multiple files, history tracking

**Remember: Context is SACRED. Losing it destroys immersion. Save it religiously.**
