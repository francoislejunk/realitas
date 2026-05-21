# Memory System - When Memories Are Saved

## Two Memory Systems in UTAS

### 1. **Actor Sheet Memories** (Simple List)
**File:** `actor_sheet.py`

**What:** Simple string list on each actor's sheet
```python
self.memories = []  # List of strings
```

**When Added:**
```python
actor.sheet.add_memory("I threatened the guard")
# Prints: "* System: Player now remembers: 'I threatened the guard'"
```

**When Saved to Disk:**
Automatically saved by **TrackerAgent** at:

1. **Session Start** - Initial actor state snapshot
2. **Turn Start** - Pre-turn snapshot (before action)
3. **Turn End** - Post-turn snapshot (after action)

**Storage Location:**
`./simulation_data/sessions/{session_id}/session_data.json`

**Serialization:**
```python
# tracker_agent.py line 133
"memories": list(sheet.memories) if sheet.memories else []
```

**Restoration:**
```python
# tracker_agent.py line 1086
memories=list(sheet_data.get('memories', []))
```

---

### 2. **NUA Memory System** (Rich Event Tracking)
**File:** `npc_memory_system.py`

**What:** Sophisticated memory system for NPCs with:
- Memory type categorization
- Importance levels (1-5)
- Emotional impact tracking
- Timestamp recording
- Actor involvement tracking
- Special memory types (threats, help, witnessed events)

**Structure:**
```python
memory = {
    'type': 'threat',
    'description': 'Player threatened: Give me your wallet',
    'actors_involved': ['Player'],
    'importance': 4,  # 1-5 scale
    'emotional_impact': 'fearful',
    'timestamp': datetime.now(),
    'turn_number': 5
}
```

**When Added:**
```python
# Generic event
nua_memory_manager.record_event(
    nua_name="Guard",
    event_type="interaction",
    description="Player asked about the vault",
    actors_involved=["Player"],
    importance=3,
    emotional_impact="suspicious"
)

# Specific event types
nua_memory_manager.record_threat(
    nua_name="Guard",
    threatener_name="Player",
    threat_description="Give me your wallet"
)

nua_memory_manager.record_help(
    nua_name="Guard",
    helper_name="Player",
    help_description="Helped me up after I fell"
)

nua_memory_manager.record_witnessed_violence(
    nua_name="Bystander",
    perpetrator_name="Player",
    victim_name="Guard",
    violence_description="Player attacked Guard with a knife"
)
```

**When Saved to Disk:**

**Auto-save by default** (can be disabled with `auto_save=False`):
```python
# After EVERY memory recording
def record_event(..., auto_save: bool = True):
    memory.add_memory(...)
    
    # Display if important
    if importance >= 4:
        print(f"🧠 {nua_name} remembers: {description[:60]}...")
    
    # Auto-save to disk
    if auto_save:
        self._save_memories()  # ← Saves immediately
```

**Storage Location:**
`./simulation_data/narrative_context/nua_memories/nua_memories.json`

**Format:**
```json
{
  "Guard": {
    "nua_name": "Guard",
    "memories": [
      {
        "type": "threat",
        "description": "Player threatened: Give me your wallet",
        "actors_involved": ["Player"],
        "importance": 4,
        "emotional_impact": "fearful",
        "timestamp": "2025-10-21T22:07:00.123456",
        "turn_number": 5
      }
    ],
    "important_events": [...],
    "threats_received": [...],
    "help_received": [...],
    "witnessed_events": [...]
  }
}
```

---

## Summary: When Memories Save

### Actor Sheet Memories (Simple)
✅ **Session start** - Initial snapshot  
✅ **Every turn start** - Pre-turn snapshot  
✅ **Every turn end** - Post-turn snapshot  
📁 **Location:** `./simulation_data/sessions/{session_id}/session_data.json`

### NUA Memory System (Rich)
✅ **Immediately after recording** - Auto-saves by default  
✅ **Every `record_event()` call**  
✅ **Every `record_threat()` call**  
✅ **Every `record_help()` call**  
✅ **Every `record_witnessed_violence()` call**  
✅ **Every `record_conversation()` call**  
📁 **Location:** `./simulation_data/narrative_context/nua_memories/nua_memories.json`

---

## Key Differences

| Feature | Actor Sheet Memories | NUA Memory System |
|---------|---------------------|-------------------|
| **Type** | Simple string list | Rich event objects |
| **Who** | All actors (UA + NUA) | NPCs only |
| **When Saved** | Turn snapshots | Immediately on record |
| **Structure** | `["string1", "string2"]` | Complex dict with metadata |
| **Importance** | No tracking | 1-5 scale |
| **Emotional Impact** | No tracking | Tracked (fearful, grateful, etc.) |
| **Timestamps** | No | Yes |
| **Actor Involvement** | No | Yes |
| **Special Types** | No | Threats, help, witnessed events |
| **Querying** | Manual list search | Built-in query methods |

---

## Usage Examples

### Simple Memory (Actor Sheet)
```python
# Add
actor.sheet.add_memory("I saw a strange symbol on the wall")

# Access
for memory in actor.sheet.memories:
    print(memory)

# Automatically saved at turn end
```

### Rich Memory (NUA System)
```python
# Initialize
nua_memory_manager = NUAMemoryManager(storage_dir)

# Record threat
nua_memory_manager.record_threat(
    nua_name="Guard",
    threatener_name="Player",
    threat_description="Pointed gun at me"
)
# → Saves immediately to disk
# → Prints: "🧠 Guard remembers: Player threatened: Pointed gun at me..."

# Query later
if nua_memory_manager.has_been_threatened_by("Guard", "Player"):
    print("Guard remembers being threatened!")

# Get memory summary for LLM context
summary = nua_memory_manager.get_memory_summary("Guard", "Player")
# → "Guard's MEMORIES:
#      - Player threatened: Pointed gun at me (Turn 5, fearful)"
```

---

## When to Use Which System

### Use Actor Sheet Memories When:
- Simple narrative notes
- Player character memories
- Quick reminders
- Don't need timestamps or importance

### Use NUA Memory System When:
- NPC relationship tracking
- Threat/help tracking
- Witnessed events
- Need to query by actor
- Need importance levels
- Need emotional context
- Want automatic categorization

---

## Current Integration Status

### ✅ Implemented:
- Actor sheet memory storage
- TrackerAgent serialization
- NUA memory system
- Auto-save on record
- Memory querying
- Special event types

### ❓ Unknown:
- Whether main loop actually calls `record_event()` during gameplay
- Integration with LLM context for NPC behavior
- Memory cleanup/pruning for old events

### 📋 Recommendation:
Check if the NUA memory system is being called during actual gameplay events (threats, help, violence). If not, add integration points in the main loop where these events occur.
