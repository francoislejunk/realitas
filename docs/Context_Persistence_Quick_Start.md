# Context Persistence - Quick Start Guide

## 🚀 **Get Started in 5 Minutes**

### **Step 1: Run the Integration Script**

```bash
cd "c:/Users/darre/OneDrive/Desktop/Realitas Neo"
python integrate_context_persistence.py
```

This automatically adds the necessary imports and initialization to `redesigned_main.py`.

---

### **Step 2: Add Context Updates to Key Functions**

#### **A. Update Scene Descriptions**

Find everywhere `scene_description` is assigned and add:

```python
# After: scene_description = new_scene
from persistent_context_manager import get_context_manager
context_manager = get_context_manager()
context_manager.update_scene_description(scene_description)
```

**Quick Find:** Search for `scene_description =` in `redesigned_main.py`

#### **B. Update Location Changes**

In `_apply_location_move()` function (around line 810):

```python
# After generating new scene
new_scene = conductor.generate_scene_description(...)

# ADD THIS:
from persistent_context_manager import get_context_manager
context_manager = get_context_manager()
context_manager.update_location(
    location=move_label,
    scene_description=new_scene,
    location_label=move_label
)
```

#### **C. Update NPC Changes**

When NPCs are added (around line 5108):

```python
# After: available_npcs.append(spark_nua)
context_manager = get_context_manager()
context_manager.add_npc(spark_nua.sheet.name)
```

When NPCs are removed (around line 1251):

```python
# After: removed_names = _prune_npcs_by_outcome_text(...)
context_manager = get_context_manager()
for name in removed_names:
    context_manager.remove_npc(name)
```

When location changes (clears NPCs):

```python
# After moving to new location
context_manager = get_context_manager()
context_manager.set_npcs([])
```

#### **D. Update After Narratives**

After every narrative generation:

```python
# After: narrative = narrator.narrate_action(...)
context_manager = get_context_manager()
context_manager.add_narrative(narrative)
context_manager.add_event(f"User: {user_input}")
```

---

### **Step 3: Inject Context into LLM Prompts**

#### **Option A: Use Helper Functions (Recommended)**

```python
from context_injection_helper import (
    get_context_for_narrator,
    get_context_for_interpreter,
    get_context_for_conductor
)

# In narrator
context_text = get_context_for_narrator()
prompt = f"{context_text}\n\n{your_prompt}"

# In interpreter
context_text = get_context_for_interpreter()
prompt = f"{context_text}\n\n{your_prompt}"

# In conductor
context_text = get_context_for_conductor()
prompt = f"{context_text}\n\n{your_prompt}"
```

#### **Option B: Manual Injection**

```python
from persistent_context_manager import get_context_manager

context_manager = get_context_manager()
context_text = context_manager.get_context_for_llm()

prompt = f"{context_text}\n\n{your_prompt}"
```

---

### **Step 4: Test It**

1. **Start simulation**
2. **Move to a location:** "I go to the diner"
3. **Check context file:** `simulation_data/context/context_*.json`
4. **Verify location is saved**
5. **Restart simulation**
6. **Verify it resumes from diner, not initial scene**

---

## 📍 **Where to Add Context Updates**

### **Critical Locations (Must Update):**

| Location | Line | What to Add |
|----------|------|-------------|
| `_apply_location_move()` | ~810 | `context_manager.update_location()` |
| After scene generation | ~1733 | `context_manager.update_scene_description()` |
| After spark NPC creation | ~5108 | `context_manager.add_npc()` |
| After NPC pruning | ~1251 | `context_manager.remove_npc()` |
| After narrative generation | ~2550 | `context_manager.add_narrative()` |

### **LLM Prompt Locations (Must Inject):**

| File | Method | What to Add |
|------|--------|-------------|
| `narrator_agent.py` | `_call_llm()` | `get_context_for_narrator()` |
| `interpreter_agent.py` | `detect_inquiry_or_action()` | `get_context_for_interpreter()` |
| `conductor_agent.py` | `generate_scene_description()` | `get_context_for_conductor()` |

---

## 🧪 **Quick Test Script**

```python
from persistent_context_manager import get_context_manager

# Initialize
context_manager = get_context_manager(session_id="test_001")

# Test location update
context_manager.update_location(
    location="Test Diner",
    scene_description="A cozy diner with red booths.",
    location_label="diner"
)

# Test NPC addition
context_manager.add_npc("Lena", "actor_lena")

# Test narrative
context_manager.add_narrative("You enter the diner.")
context_manager.add_event("User: I enter the diner")

# Check context
print(context_manager.get_context_summary())

# Verify file exists
import os
assert os.path.exists("simulation_data/context/context_test_001.json")
print("✓ Context file created successfully")
```

---

## ⚠️ **Common Issues**

### **Issue 1: Context Not Saving**

**Symptom:** Changes don't persist after restart

**Solution:** Make sure you're calling `_save()` methods:
- `update_location()` - saves automatically
- `add_npc()` - saves automatically
- `update_scene_description()` - saves automatically

All update methods save automatically. If context isn't saving, check for exceptions.

### **Issue 2: Context Not Loading**

**Symptom:** Always starts from initial scene

**Solution:** Check session ID matches:
```python
# Use tracker's session ID
context_manager = get_context_manager(session_id=tracker.session_id)
```

### **Issue 3: NPCs Not Tracked**

**Symptom:** NPCs disappear after restart

**Solution:** Make sure to call `add_npc()` when NPCs are created:
```python
available_npcs.append(new_npc)
context_manager.add_npc(new_npc.sheet.name)  # ← Don't forget this
```

### **Issue 4: Narrator Forgets Location**

**Symptom:** Narrator describes wrong location

**Solution:** Inject context into narrator prompts:
```python
from context_injection_helper import get_context_for_narrator

context_text = get_context_for_narrator()
prompt = f"{context_text}\n\n{your_narration_prompt}"
```

---

## 📊 **Verification Checklist**

After integration, verify:

- [ ] Context file is created: `simulation_data/context/context_*.json`
- [ ] Location is saved when moving
- [ ] NPCs are tracked when added/removed
- [ ] Scene description is updated
- [ ] Narratives are saved
- [ ] Context persists after restart
- [ ] Narrator uses correct location
- [ ] Narrator mentions correct NPCs
- [ ] No reversion to initial scene

---

## 🎯 **Success Criteria**

You'll know it's working when:

1. ✅ **File exists:** `simulation_data/context/context_*.json` is created
2. ✅ **Location persists:** Moving to diner saves "diner" in context file
3. ✅ **NPCs tracked:** Adding NPC saves their name in `present_npcs`
4. ✅ **Restart works:** Restarting simulation resumes from saved location
5. ✅ **Narrator remembers:** Narrator describes current location, not initial scene
6. ✅ **No context loss:** Never reverts to initial scene unexpectedly

---

## 🚨 **Emergency Recovery**

If context gets corrupted:

```python
from persistent_context_manager import get_context_manager

context_manager = get_context_manager()

# Check for issues
issues = context_manager.validate_context()
print(f"Issues found: {issues}")

# Attempt repair
if issues:
    context_manager.repair_context()
    print("Context repaired from history")

# Or dump for debugging
context_manager.dump_context()
print("Context dumped for inspection")
```

---

## 📚 **Full Documentation**

For complete details, see:
- `DOCS/Context_Persistence_Integration.md` - Full integration guide
- `DOCS/Spatial_Context_System.md` - How spatial context works
- `persistent_context_manager.py` - Source code with comments
- `context_injection_helper.py` - Helper functions

---

## 💡 **Pro Tips**

1. **Save Often:** Context saves automatically on every update - don't batch
2. **Load Always:** Context reloads on every `get_context()` - always fresh
3. **Inject Everywhere:** Add context to ALL LLM prompts - no exceptions
4. **Check Files:** Monitor `simulation_data/context/` directory
5. **Use Helpers:** Use `context_injection_helper.py` functions for consistency

**Remember: Context is SACRED. Save it religiously. Inject it everywhere. Never lose it.**
