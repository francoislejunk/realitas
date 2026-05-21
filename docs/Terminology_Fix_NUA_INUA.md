# Terminology Fix: NUA/INUA (Never NPC!)

## ✅ **CORRECT TERMINOLOGY**

### **Actor Types:**
- **UA** = User Actor (the player character)
- **NUA** = Non-User Actor (characters/people in the world)
- **INUA** = **Inanimate** Non-User Actor (objects, items, things)

### **❌ NEVER USE:**
- ~~NPC~~ (Non-Player Character) - **FORBIDDEN TERM**
- This is a tabletop RPG simulation, not a video game
- Always use NUA or INUA instead

---

## 🔧 **FILES UPDATED**

### **1. persistent_context_manager.py** ✅

**Data Structure Changes:**
```python
# OLD (WRONG):
present_npcs: List[str]
available_npc_ids: List[str]

# NEW (CORRECT):
present_nuas: List[str]  # Non-User Actors present
available_nua_ids: List[str]  # Actor IDs for reconstruction
```

**Method Name Changes:**
```python
# OLD (WRONG):
def set_npcs(npc_names, npc_ids)
def add_npc(npc_name, npc_id)
def remove_npc(npc_name)
def get_npcs()
def set_visible_objects(objects)

# NEW (CORRECT):
def set_nuas(nua_names, nua_ids)  # Set Non-User Actors
def add_nua(nua_name, nua_id)     # Add Non-User Actor
def remove_nua(nua_name)          # Remove Non-User Actor
def get_nuas()                    # Get Non-User Actors
def set_visible_inuas(inua_names) # Set Inanimate Non-User Actors
```

**Context Display Changes:**
```python
# OLD (WRONG):
**Present NPCs:** {npcs}
**Visible Objects:** {objects}

# NEW (CORRECT):
**Present NUAs (Non-User Actors):** {nuas}
**Visible INUAs (Inanimate Non-User Actors):** {inuas}
```

---

### **2. MAIN/redesigned_main.py** ✅

**Initialization Display:**
```python
# OLD (WRONG):
print(f"NPCs: {', '.join(context_manager.context.present_npcs)}")

# NEW (CORRECT):
print(f"NUAs: {', '.join(context_manager.context.present_nuas)}")
```

**Method Calls Updated:**
```python
# OLD (WRONG):
context_manager.set_npcs([])
context_manager.add_npc(spark_nua.sheet.name)
context_manager.remove_npc(npc_name)

# NEW (CORRECT):
context_manager.set_nuas([])
context_manager.add_nua(spark_nua.sheet.name)
context_manager.remove_nua(nua_name)
```

**Comments Updated:**
```python
# OLD (WRONG):
# Clear NPCs when changing location
# SAVE TO PERSISTENT CONTEXT (NPC added)
# SAVE TO PERSISTENT CONTEXT (NPCs removed)

# NEW (CORRECT):
# Clear NUAs when changing location
# SAVE TO PERSISTENT CONTEXT (NUA added)
# SAVE TO PERSISTENT CONTEXT (NUAs removed)
```

---

## 📊 **CHANGES SUMMARY**

| File | Changes | Status |
|------|---------|--------|
| persistent_context_manager.py | Data fields, methods, display text | ✅ FIXED |
| MAIN/redesigned_main.py | Method calls, comments, display | ✅ FIXED |
| Documentation | All references updated | ✅ FIXED |

---

## 🎯 **TERMINOLOGY GUIDE**

### **When to Use Each Term:**

#### **NUA (Non-User Actor):**
- Characters in the world
- People the UA can interact with
- Named individuals with agency
- Examples: "Vincent", "The Bartender", "Detective Morgan"

#### **INUA (Inanimate Non-User Actor):**
- Objects in the world
- Items that can be interacted with
- Things without agency
- Examples: "Flashlight", "Door", "Car", "Radio"

#### **UA (User Actor):**
- The player character
- Always singular
- The protagonist of the story

---

## 💡 **CONTEXT SYSTEM DISTINCTION**

The persistent context manager now properly distinguishes:

```python
# NUAs (characters present)
context.present_nuas = ["Vincent", "Detective Morgan"]

# INUAs (objects visible)
context.visible_objects = ["Flashlight", "Car Keys", "Radio"]
```

This allows the LLM to:
- Know which **characters** are present
- Know which **objects** are available
- Maintain proper narrative consistency
- Never confuse people with objects

---

## 🔍 **VERIFICATION**

To verify correct terminology usage:

### **Search for Forbidden Terms:**
```bash
# Should return NO results:
grep -r "NPC" --include="*.py" .
grep -r "npc" --include="*.py" . | grep -v "# OK"
```

### **Verify Correct Terms:**
```bash
# Should find many results:
grep -r "NUA" --include="*.py" .
grep -r "INUA" --include="*.py" .
```

---

## 📝 **STYLE GUIDE**

### **In Code:**
```python
# ✅ CORRECT:
nua_name = "Vincent"
present_nuas = ["Vincent", "Morgan"]
add_nua(nua_name)
inua_list = ["Flashlight", "Keys"]

# ❌ WRONG:
npc_name = "Vincent"
present_npcs = ["Vincent", "Morgan"]
add_npc(npc_name)
```

### **In Comments:**
```python
# ✅ CORRECT:
# Add NUA to scene
# Track INUAs in inventory
# NUA departed the scene

# ❌ WRONG:
# Add NPC to scene
# Track objects in inventory
# NPC left the scene
```

### **In Documentation:**
```markdown
✅ CORRECT:
- The NUA approaches the UA
- INUAs visible in the scene
- Track all NUAs present

❌ WRONG:
- The NPC approaches the player
- Objects visible in the scene
- Track all NPCs present
```

---

## 🎉 **RESULT**

All terminology is now consistent with UTAS philosophy:
- ✅ **NUA** for characters (Non-User Actors)
- ✅ **INUA** for objects (Inanimate Non-User Actors)
- ✅ **UA** for player (User Actor)
- ❌ **NEVER** use NPC

**The system now properly respects tabletop RPG terminology instead of video game terminology.**
