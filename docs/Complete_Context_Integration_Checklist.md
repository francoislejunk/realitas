# Complete Context Integration Checklist

## 🎯 **GOAL: Perfect Context Persistence Forever**

Every piece of information must be:
1. ✅ **SAVED** to disk immediately
2. ✅ **LOADED** on every access
3. ✅ **INJECTED** into every LLM prompt
4. ✅ **TRACKED** across all systems

---

## 📋 **COMPLETE INTEGRATION CHECKLIST**

### **PHASE 1: Core Context Saving** 🔴

#### **A. Scene & Location Context**

**Where to Save:**
```python
from persistent_context_manager import get_context_manager

# 1. When scene description changes
context_manager = get_context_manager()
context_manager.update_scene_description(scene_description)

# 2. When location changes
context_manager.update_location(
    location=location_name,
    scene_description=new_scene,
    location_label=location_label
)
```

**Integration Points in `redesigned_main.py`:**

| Line/Function | What to Save | Code to Add |
|---------------|--------------|-------------|
| `_apply_location_move()` ~810 | Location change | `context_manager.update_location(move_label, new_scene, move_label)` |
| After conductor scene gen ~1733 | Scene description | `context_manager.update_scene_description(scene_description)` |
| After spark scene update ~5113 | Scene description | `context_manager.update_scene_description(scene_description)` |
| After encounter scene refresh ~162 | Scene description | `context_manager.update_scene_description(scene_description)` |

---

#### **B. NPC Tracking Context**

**Where to Save:**
```python
# 1. When NPC is added
context_manager.add_npc(npc_name, npc_id)

# 2. When NPC is removed
context_manager.remove_npc(npc_name)

# 3. When location changes (clear all)
context_manager.set_npcs([])

# 4. Bulk update
npc_names = [npc.sheet.name for npc in available_npcs]
npc_ids = [f"actor_{npc.sheet.name}" for npc in available_npcs]
context_manager.set_npcs(npc_names, npc_ids)
```

**Integration Points in `redesigned_main.py`:**

| Line/Function | What to Save | Code to Add |
|---------------|--------------|-------------|
| After SPARK NPC creation ~5108 | Add NPC | `context_manager.add_npc(spark_nua.sheet.name)` |
| After dynamic actor creation | Add NPC | `context_manager.add_npc(new_actor.sheet.name)` |
| After NPC pruning ~1251 | Remove NPCs | `for name in removed: context_manager.remove_npc(name)` |
| After location change ~810 | Clear NPCs | `context_manager.set_npcs([])` |
| Start of encounter | Set NPCs | `context_manager.set_npcs([npc.sheet.name for npc in available_npcs])` |

---

#### **C. Narrative & Event Context**

**Where to Save:**
```python
# 1. After every narrative generation
context_manager.add_narrative(narrative_text)

# 2. After every user action
context_manager.add_event(f"User: {user_input}")

# 3. After every NPC action
context_manager.add_event(f"NPC ({npc_name}): {action_description}")

# 4. Combined update
context_manager.update_user_action(
    action=user_input,
    intent=interpreted_intent,
    confidence=0.8
)
```

**Integration Points in `redesigned_main.py`:**

| Line/Function | What to Save | Code to Add |
|---------------|--------------|-------------|
| After narrator.narrate_action() ~2550 | Narrative + Event | `context_manager.add_narrative(narrative)` + `context_manager.add_event(f"User: {user_input}")` |
| After narrator.narrate_given_action() ~2399 | Narrative + Event | Same as above |
| After encounter narratives ~3938 | Narrative + Event | Same as above |
| After inquiry response ~1900 | Event only | `context_manager.add_event(f"Inquiry: {user_input}")` |
| After NPC action resolution | Event | `context_manager.add_event(f"NPC ({npc}): {action}")` |

---

#### **D. Extracted Context from Enhanced Narrative Loop**

**Where to Save:**
```python
# After narrative_loop.process_turn()
framing = narrative_loop.process_turn(...)
context = framing.get('context', {})

# Save extracted context
context_manager.set_opportunities(context.get('opportunities', []))
context_manager.set_visible_objects(context.get('visible_objects', []))
context_manager.set_accessible_paths(context.get('accessible_paths', []))
context_manager.update_atmosphere(
    location_atmosphere=context.get('atmosphere'),
    social_atmosphere=context.get('social_atmosphere')
)
```

**Integration Points in `redesigned_main.py`:**

| Line/Function | What to Save | Code to Add |
|---------------|--------------|-------------|
| After process_turn() ~2549 | Extracted context | Code block above |
| After process_turn() ~2398 | Extracted context | Code block above |
| After process_turn() ~2049 | Extracted context | Code block above |

---

#### **E. Time & Mode Context**

**Where to Save:**
```python
# 1. Time context
context_manager.update_time_context(
    time_of_day=time_context.get('time_of_day'),
    weather=time_context.get('weather'),
    season=time_context.get('season')
)

# 2. Narrative mode
context_manager.update_narrative_mode(
    mode=current_mode.value,
    tone=narrative_tone
)

# 3. User goals/tasks
context_manager.update_user_goal(current_goal)
context_manager.update_user_task(current_task)
```

**Integration Points in `redesigned_main.py`:**

| Line/Function | What to Save | Code to Add |
|---------------|--------------|-------------|
| After time updates | Time context | `context_manager.update_time_context(...)` |
| After mode transitions | Mode context | `context_manager.update_narrative_mode(...)` |
| After goal updates | Goal context | `context_manager.update_user_goal(...)` |

---

### **PHASE 2: Context Injection into LLM Prompts** 🟡

#### **A. Narrator Agent**

**File:** `agents/narrator_agent.py`

**Every LLM call must inject context:**

```python
from persistent_context_manager import get_context_manager

def _call_llm(self, prompt: str, ...):
    # INJECT CONTEXT
    context_manager = get_context_manager()
    context_text = context_manager.get_context_for_llm()
    
    enhanced_prompt = f"""
{context_text}

{prompt}

**CRITICAL REMINDER:**
- Current location: {context_manager.get_location()}
- Present NPCs: {', '.join(context_manager.get_npcs())}
- DO NOT revert to initial scene
- DO NOT forget where we are
"""
    
    # Then call LLM with enhanced_prompt
    response = self.client.chat.completions.create(...)
```

**Methods to Update:**
- `_call_llm()` - Line 36
- `generate_inquiry_response()` - Line 297
- `generate_exploration_action_result_narrative()` - Line 1723
- `generate_encounter_dialogue()` - Line 2022 (NEW)

---

#### **B. Interpreter Agent**

**File:** `agents/interpreter_agent.py`

**Inject context for action interpretation:**

```python
from persistent_context_manager import get_context_manager

def detect_inquiry_or_action(self, user_input, actor, reactor=None):
    context_manager = get_context_manager()
    
    prompt = f"""
**CURRENT CONTEXT:**
- Location: {context_manager.get_location()}
- Present NPCs: {', '.join(context_manager.get_npcs())}
- Recent Events: {context_manager.get_recent_events(3)}

**USER INPUT:** {user_input}

Analyze this input in the context above...
"""
```

**Methods to Update:**
- `detect_inquiry_or_action()` - Add context to prompt
- `interpret_action()` - Add context to prompt
- All LLM calls - Inject context

---

#### **C. Conductor Agent**

**File:** `agents/conductor_agent.py`

**Inject context for scene generation:**

```python
from persistent_context_manager import get_context_manager

def generate_scene_description(self, scene_data, ...):
    context_manager = get_context_manager()
    
    prompt = f"""
**CONTINUITY CONTEXT:**
- Previous Location: {context_manager.get_location()}
- Previous Scene: {context_manager.get_scene_description()[:200]}...
- Recent Events: {context_manager.get_recent_events(2)}

**NEW SCENE TO GENERATE:**
{scene_data}

CRITICAL: Maintain continuity with the context above.
"""
```

**Methods to Update:**
- `generate_scene_description()` - Add context to prompt
- All scene generation methods - Inject context

---

#### **D. Decider Agent**

**File:** `agents/decider_agent.py`

**Inject context for NPC decisions:**

```python
from persistent_context_manager import get_context_manager

def determine_nua_proaction(self, proactor, reactor, ...):
    context_manager = get_context_manager()
    
    prompt = f"""
**CURRENT SITUATION:**
- Location: {context_manager.get_location()}
- Scene: {context_manager.get_scene_description()[:300]}...
- Present NPCs: {', '.join(context_manager.get_npcs())}
- Recent Events: {context_manager.get_recent_events(3)}

**NPC DECISION:**
What does {proactor.sheet.name} do?
"""
```

**Methods to Update:**
- `determine_nua_proaction()` - Add context
- `determine_nua_reaction()` - Add context
- All decision methods - Inject context

---

### **PHASE 3: Context Loading & Verification** 🟢

#### **A. On Simulation Start**

**In `redesigned_main.py` initialization:**

```python
# Initialize context manager
from persistent_context_manager import get_context_manager

context_manager = get_context_manager(session_id=tracker.session_id)

# Check if resuming
if context_manager.context.update_count > 0:
    print(f"\n{Color.SUCCESS}📍 RESUMING FROM SAVED CONTEXT:{Color.RESET}")
    print(context_manager.get_context_summary())
    
    # Restore scene
    scene_description = context_manager.get_scene_description()
    
    # Restore NPCs (reconstruct Actor objects if needed)
    npc_names = context_manager.get_npcs()
    print(f"{Color.INFO}NPCs Present: {', '.join(npc_names) if npc_names else 'None'}{Color.RESET}")
    
    # Restore mode
    current_mode = SimulationMode(context_manager.context.narrative_mode.upper())
    
else:
    print(f"\n{Color.INFO}Starting new session{Color.RESET}")
```

---

#### **B. Periodic Validation**

**Add validation checks every 10 turns:**

```python
# Every 10 turns
if turn_count % 10 == 0:
    context_manager = get_context_manager()
    issues = context_manager.validate_context()
    
    if issues:
        print(f"{Color.WARNING}⚠️ Context issues detected: {issues}{Color.RESET}")
        context_manager.repair_context()
```

---

#### **C. Context Display Commands**

**Add user commands to view context:**

```python
# In main loop
if user_input.lower() == 'context':
    context_manager = get_context_manager()
    print(context_manager.get_context_summary())
    continue

if user_input.lower() == 'context dump':
    context_manager = get_context_manager()
    filepath = context_manager.dump_context()
    print(f"Context dumped to: {filepath}")
    continue
```

---

## 🔧 **IMPLEMENTATION SCRIPT**

Here's a script to add context saving to all critical points:

```python
# add_context_saving.py
"""
Adds context saving calls to all critical points in redesigned_main.py
"""

def add_context_imports():
    """Add imports at top of file"""
    return """
from persistent_context_manager import get_context_manager
from context_injection_helper import (
    update_context_after_action,
    update_context_after_scene_change,
    update_context_npcs
)
"""

def add_after_scene_update(scene_var_name):
    """Add after scene_description is updated"""
    return f"""
# SAVE CONTEXT
context_manager = get_context_manager()
context_manager.update_scene_description({scene_var_name})
"""

def add_after_location_change(location, scene, label):
    """Add after location changes"""
    return f"""
# SAVE CONTEXT
context_manager = get_context_manager()
context_manager.update_location(
    location={location},
    scene_description={scene},
    location_label={label}
)
"""

def add_after_npc_change(npc_list):
    """Add after NPC list changes"""
    return f"""
# SAVE CONTEXT
context_manager = get_context_manager()
npc_names = [npc.sheet.name for npc in {npc_list}]
context_manager.set_npcs(npc_names)
"""

def add_after_narrative(narrative_var, user_input_var):
    """Add after narrative generation"""
    return f"""
# SAVE CONTEXT
context_manager = get_context_manager()
context_manager.add_narrative({narrative_var})
context_manager.add_event(f"User: {{{user_input_var}}}")
"""

# Usage:
# 1. Add imports at top
# 2. Add context saving after each critical operation
# 3. Inject context into all LLM prompts
```

---

## 📊 **VERIFICATION CHECKLIST**

After integration, verify:

### **Context Saving:**
- [ ] Scene description saved on every change
- [ ] Location saved on every move
- [ ] NPCs saved when added/removed
- [ ] Narratives saved after generation
- [ ] Events saved after actions
- [ ] Time context saved on updates
- [ ] Mode saved on transitions
- [ ] Opportunities/objects saved from extraction

### **Context Loading:**
- [ ] Context loads on simulation start
- [ ] Context loads before every LLM call
- [ ] Context reloads on every access
- [ ] Backup files created
- [ ] History snapshots created (every 10 updates)

### **Context Injection:**
- [ ] Narrator prompts include context
- [ ] Interpreter prompts include context
- [ ] Conductor prompts include context
- [ ] Decider prompts include context
- [ ] All LLM calls include context

### **Context Persistence:**
- [ ] Context file exists: `simulation_data/context/context_*.json`
- [ ] Backup file exists: `simulation_data/context/context_*_backup.json`
- [ ] History files exist: `simulation_data/context/history/`
- [ ] Context survives restart
- [ ] Context survives crash
- [ ] No reversion to initial scene

---

## 🎯 **PRIORITY ORDER**

### **CRITICAL (Do First):**
1. ✅ Add context manager initialization
2. ✅ Save scene description on every change
3. ✅ Save location on every move
4. ✅ Save NPCs on every change
5. ✅ Inject context into narrator prompts

### **HIGH (Do Second):**
6. ✅ Save narratives after generation
7. ✅ Save events after actions
8. ✅ Inject context into interpreter prompts
9. ✅ Inject context into conductor prompts
10. ✅ Add context loading on startup

### **MEDIUM (Do Third):**
11. ✅ Save extracted context from narrative loop
12. ✅ Save time/mode context
13. ✅ Inject context into decider prompts
14. ✅ Add validation checks

### **LOW (Do Last):**
15. ✅ Add context display commands
16. ✅ Add periodic validation
17. ✅ Optimize context file size
18. ✅ Add context compression

---

## 🚨 **CRITICAL RULES**

### **ALWAYS:**
1. ✅ Save IMMEDIATELY after change
2. ✅ Load BEFORE every LLM call
3. ✅ Inject into EVERY prompt
4. ✅ Validate PERIODICALLY
5. ✅ Backup AUTOMATICALLY

### **NEVER:**
1. ❌ Batch updates (save immediately)
2. ❌ Skip context injection
3. ❌ Assume context is current (reload)
4. ❌ Ignore validation errors
5. ❌ Delete context files manually

---

## 📝 **EXAMPLE: Complete Integration**

```python
# In redesigned_main.py

# 1. INITIALIZE
context_manager = get_context_manager(session_id=tracker.session_id)

# 2. LOAD ON START
if context_manager.context.update_count > 0:
    scene_description = context_manager.get_scene_description()
    print(f"Resuming from: {context_manager.get_location()}")

# 3. SAVE ON CHANGE
scene_description = conductor.generate_scene_description(...)
context_manager.update_scene_description(scene_description)  # ← SAVE

# 4. INJECT INTO PROMPT
context_text = context_manager.get_context_for_llm()
prompt = f"{context_text}\n\n{your_prompt}"
narrative = narrator._call_llm(prompt)

# 5. SAVE RESULT
context_manager.add_narrative(narrative)  # ← SAVE
context_manager.add_event(f"User: {user_input}")  # ← SAVE

# 6. VALIDATE
if turn_count % 10 == 0:
    issues = context_manager.validate_context()
    if issues:
        context_manager.repair_context()
```

---

## ✅ **SUCCESS CRITERIA**

You'll know it's working when:

1. ✅ Context file updates after every action
2. ✅ Restarting simulation resumes from correct location
3. ✅ NPCs persist across restarts
4. ✅ Narrator never reverts to initial scene
5. ✅ All LLM responses reference current context
6. ✅ No context loss after 100+ turns
7. ✅ No context loss after crash/restart
8. ✅ Validation shows no issues

---

## 🎉 **FINAL RESULT**

After complete integration:
- **EVERY** piece of information is saved
- **EVERY** LLM call has full context
- **EVERY** restart resumes perfectly
- **NEVER** lose context again
- **PERFECT** consistency forever

**Context is SACRED. Save it EVERYWHERE. Inject it ALWAYS. Validate it CONSTANTLY.**
