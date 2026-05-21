# Feature Integration Guide - Four New Systems

This guide explains how to integrate the four new features into the Realitas Neo simulation.

## 📚 **1. RAG System for Lore Data**

### **Purpose**
Provides semantic search and retrieval of world lore, including Empcog history, factions, vessel archetypes, and mission types.

### **Files Created**
- `lore_rag_system.py` - Core RAG implementation with vector embeddings

### **Integration Steps**

#### **1.1 Initialize in Main**
```python
# In MAIN/redesigned_main.py, add to imports:
from lore_rag_system import initialize_lore_rag, get_lore_rag

# In initialization section (around line 1900):
print(f"{Color.INFO}📚 Initializing Lore RAG System...{Color.RESET}")
lore_rag = initialize_lore_rag(storage_dir, load_defaults=True)
```

#### **1.2 Use in LLM Prompts**
```python
# When generating scenes or narratives, inject lore context:
def _get_scene_with_lore_context(self, user_input: str):
    # Get relevant lore
    lore_context = get_lore_rag().get_context_for_llm(
        query=user_input,
        max_tokens=500,
        category_filter=None  # or specific category
    )
    
    # Add to LLM prompt
    prompt = f"""
{lore_context}

Scene Description: {scene_description}
User Action: {user_input}
...
"""
```

#### **1.3 Add Lore Documents**
```python
# Add custom lore at runtime:
from lore_rag_system import get_lore_rag, LoreCategory

get_lore_rag().add_lore_document(
    title="The Shadow Protocol",
    content="A secret Empcog operation to harvest consciousness...",
    category=LoreCategory.EMPCOG_SECRETS,
    tags=["secret", "conspiracy", "harvest"],
    importance=9
)
```

### **Usage Examples**

**Search for relevant lore:**
```python
results = get_lore_rag().search_lore(
    query="What are vessel archetypes?",
    top_k=3
)

for doc, similarity in results:
    print(f"{doc.title}: {similarity:.2f}")
```

**Get lore by category:**
```python
faction_lore = get_lore_rag().get_by_category(LoreCategory.FACTIONS)
```

---

## 🎭 **2. Vessel Selection System**

### **Purpose**
Provides three vessel archetype options at simulation start: Drifter, Anchor, and Weaver.

### **Files Created**
- `vessel_selection_system.py` - Vessel selection with archetype definitions

### **Integration Steps**

#### **2.1 Replace Character Creation**
```python
# In MAIN/redesigned_main.py, replace _create_dynamic_user_actor():

from vessel_selection_system import create_vessel_selection_system

def _create_user_actor_with_selection(scene_creator, storage_dir):
    """Create user actor with vessel selection"""
    vessel_system = create_vessel_selection_system(scene_creator, storage_dir)
    selected_vessel = vessel_system.select_vessel()
    return selected_vessel

# In main initialization (around line 1470):
# OLD: user_actor = _create_dynamic_user_actor(scene_creator)
# NEW:
user_actor = _create_user_actor_with_selection(scene_creator, storage_dir)
```

#### **2.2 Display Flow**
The system automatically:
1. Generates 3 vessel options with archetype-specific stats
2. Displays detailed comparison with visual bars
3. Gets user selection with confirmation
4. Returns the selected UserActor

### **Archetype Details**

**The Drifter:**
- High Swiftness (4) and Shadow (4)
- Best for stealth and exploration
- Skills: Stealth, Survival, Acrobatics, Perception

**The Anchor:**
- High Sturdiness (4) and Smarts (4)
- Best for direct combat and tanking
- Skills: Endurance, Tactics, First Aid, Heavy Weapons

**The Weaver:**
- High Smarts (5) with unique Supers
- Best for reality manipulation and problem-solving
- Skills: Reality Theory, Manipulation, Persuasion, Occult Knowledge

---

## ⚔️ **3. Outlier NUA Stats Display**

### **Purpose**
Highlights exceptional or unusual stats when introducing NPCs, making their capabilities immediately clear.

### **Files Created**
- `outlier_stats_display.py` - Outlier detection and display

### **Integration Steps**

#### **3.1 Import in Main**
```python
# In MAIN/redesigned_main.py:
from outlier_stats_display import display_nua_outliers, get_compact_outlier_summary
```

#### **3.2 Display on NUA Introduction**
```python
# When a new NUA is created/introduced:
def introduce_new_nua(nua_actor, context=None):
    # Display full outlier stats
    display_nua_outliers(nua_actor.sheet, context)
    
    # Or get compact summary for inline display:
    summary = get_compact_outlier_summary(nua_actor.sheet)
    print(f"{nua_actor.sheet.name} {summary}")
```

#### **3.3 Integration Points**

**Dynamic Actor Creation:**
```python
# In dynamic_actor_system.py or main loop:
if newly_created_nua:
    context = f"Encountered during: {current_action}"
    display_nua_outliers(newly_created_nua.sheet, context)
```

**Scene Transitions:**
```python
# When entering new scene with NPCs:
for nua in scene_npcs:
    if not previously_met(nua):
        display_nua_outliers(nua.sheet)
```

### **Display Features**

- **Exceptional Capabilities**: S-factors ≥ 4
- **Notable Weaknesses**: S-factors = 0
- **Key Skills**: Top 3 skills with value ≥ 3
- **Supernatural Abilities**: All Supers
- **Threat Assessment**: CRITICAL/HIGH/MODERATE/LOW/MINIMAL

---

## 📖 **4. Key Memories System**

### **Purpose**
Friends & Fables-style memory highlighting and access. Users can mark important moments and recall them at will.

### **Files Created**
- `key_memories_system.py` - Memory creation, storage, and retrieval

### **Integration Steps**

#### **4.1 Initialize in Main**
```python
# In MAIN/redesigned_main.py:
from key_memories_system import initialize_key_memories, get_key_memories, handle_memory_command

# In initialization (around line 1920):
print(f"{Color.INFO}📖 Initializing Key Memories System...{Color.RESET}")
key_memories = initialize_key_memories(session_id, storage_dir)
```

#### **4.2 Auto-Create Memories**
```python
# After significant events:
from key_memories_system import get_key_memories, MemoryCategory, MemoryImportance

def create_memory_for_event(title, description, narrative, category, importance):
    memory_id = get_key_memories().create_memory(
        title=title,
        description=description,
        full_narrative=narrative,
        category=category,
        importance=importance,
        location=current_location,
        actors_involved=[actor.sheet.name for actor in present_actors],
        tags=extract_tags(narrative),
        turn_number=current_turn,
        scene_id=current_scene_id
    )
    
    # Highlight for user
    get_key_memories().highlight_memory_prompt(memory_id)
```

#### **4.3 Handle Memory Commands**
```python
# In main input loop:
user_input = input("What do you want to do? ").strip()

# Check for memory commands first
if handle_memory_command(user_input):
    continue  # Command handled, skip to next input

# Otherwise process as normal action
```

### **Memory Commands**

- `memories` or `list memories` - List all memories
- `pinned` or `pinned memories` - List pinned memories only
- `search memories [query]` - Search memories by text
- `recall [number]` - View specific memory in detail

### **Auto-Highlight Triggers**

Create memories automatically for:

**CRITICAL Importance:**
- Major revelations about Empcogs
- Character deaths
- Reality-bending events
- Mission completions

**IMPORTANT Importance:**
- First meeting with key NPCs
- Significant combat victories/defeats
- Important decisions made
- New location discoveries

**NOTABLE Importance:**
- Interesting dialogue exchanges
- Item acquisitions
- Minor revelations

#### **4.4 Integration with LLM Context**
```python
# Add to LLM prompts for continuity:
def build_llm_prompt_with_memories(base_prompt):
    memory_context = get_key_memories().get_context_for_llm(max_memories=5)
    
    return f"""
{memory_context}

{base_prompt}
"""
```

---

## 🔗 **Complete Integration Example**

Here's a complete example of all four systems working together:

```python
# In MAIN/redesigned_main.py

from lore_rag_system import initialize_lore_rag, get_lore_rag
from vessel_selection_system import create_vessel_selection_system
from outlier_stats_display import display_nua_outliers
from key_memories_system import initialize_key_memories, get_key_memories, handle_memory_command, MemoryCategory, MemoryImportance

def initialize_new_systems(session_id, storage_dir, scene_creator):
    """Initialize all four new systems"""
    print(f"\n{Color.HEADER}{'═' * 70}{Color.RESET}")
    print(f"{Color.HEADER}           🚀 INITIALIZING REALITAS NEO SYSTEMS 🚀{Color.RESET}")
    print(f"{Color.HEADER}{'═' * 70}{Color.RESET}\n")
    
    # 1. RAG System
    print(f"{Color.INFO}📚 Initializing Lore RAG System...{Color.RESET}")
    lore_rag = initialize_lore_rag(storage_dir, load_defaults=True)
    print(f"{Color.SUCCESS}✓ Loaded {len(lore_rag.documents)} lore documents{Color.RESET}\n")
    
    # 2. Vessel Selection
    print(f"{Color.INFO}🎭 Preparing Vessel Selection...{Color.RESET}")
    vessel_system = create_vessel_selection_system(scene_creator, storage_dir)
    user_actor = vessel_system.select_vessel()
    print(f"{Color.SUCCESS}✓ Vessel selected and ready{Color.RESET}\n")
    
    # 3. Key Memories
    print(f"{Color.INFO}📖 Initializing Key Memories System...{Color.RESET}")
    key_memories = initialize_key_memories(session_id, storage_dir)
    print(f"{Color.SUCCESS}✓ Memory system ready{Color.RESET}\n")
    
    # 4. Create initial memory
    memory_id = key_memories.create_memory(
        title="Awakening",
        description=f"Your consciousness inhabits the vessel {user_actor.sheet.name}, a {user_actor.vessel_archetype}.",
        full_narrative=f"You awaken in your new vessel. The world feels different, yet familiar. You are {user_actor.sheet.name}, and your journey in this realita begins now.",
        category=MemoryCategory.DISCOVERY,
        importance=MemoryImportance.CRITICAL,
        location="Unknown",
        actors_involved=[user_actor.sheet.name],
        tags=["awakening", "vessel", "start"]
    )
    key_memories.highlight_memory_prompt(memory_id)
    
    print(f"{Color.HEADER}{'═' * 70}{Color.RESET}\n")
    
    return user_actor

# In main loop - handle NUA introductions
def handle_new_nua_introduction(nua_actor, context):
    """Handle new NUA with outlier display and memory creation"""
    # Display outlier stats
    display_nua_outliers(nua_actor.sheet, context)
    
    # Get lore context about this type of NUA
    lore_context = get_lore_rag().get_context_for_llm(
        query=f"{nua_actor.sheet.occupation} {nua_actor.sheet.name}",
        max_tokens=200
    )
    
    # Create memory if significant
    if is_significant_nua(nua_actor):
        get_key_memories().create_memory(
            title=f"First Encounter: {nua_actor.sheet.name}",
            description=f"Met {nua_actor.sheet.name}, a {nua_actor.sheet.occupation}. {context}",
            full_narrative=generate_encounter_narrative(nua_actor, context, lore_context),
            category=MemoryCategory.RELATIONSHIP,
            importance=MemoryImportance.IMPORTANT,
            location=current_location,
            actors_involved=[user_actor.sheet.name, nua_actor.sheet.name],
            tags=["first_meeting", nua_actor.sheet.occupation]
        )

# In main input loop
while True:
    user_input = input(f"\n{Color.INFO}What do you want to do? {Color.RESET}").strip()
    
    # Handle memory commands
    if handle_memory_command(user_input):
        continue
    
    # Check for lore queries
    if user_input.lower().startswith("what is ") or user_input.lower().startswith("tell me about "):
        query = user_input[8:] if "what is" in user_input.lower() else user_input[13:]
        results = get_lore_rag().search_lore(query, top_k=3)
        
        if results:
            print(f"\n{Color.SUCCESS}📚 LORE INFORMATION:{Color.RESET}\n")
            for doc, similarity in results:
                print(f"{Color.WARNING}{doc.title}{Color.RESET}")
                print(f"{doc.content}\n")
        else:
            print(f"{Color.WARNING}No lore found for: {query}{Color.RESET}")
        continue
    
    # Normal action processing...
```

---

## 📊 **Testing the Systems**

### **Test RAG System**
```python
python -c "
from lore_rag_system import initialize_lore_rag
from pathlib import Path

rag = initialize_lore_rag(Path('./simulation_data'), load_defaults=True)
results = rag.search_lore('What are vessel archetypes?', top_k=3)

for doc, score in results:
    print(f'{doc.title}: {score:.2f}')
"
```

### **Test Vessel Selection**
```python
# Run main.py and observe the vessel selection screen
# Should show 3 options with detailed stats
```

### **Test Outlier Display**
```python
from outlier_stats_display import display_nua_outliers
from actors import NonUserActor
from actor_sheet import ActorSheet, SFactors, SFactorType

# Create test NUA with outlier stats
sheet = ActorSheet(
    name="Test Warrior",
    occupation="Elite Fighter",
    s_factors=SFactors(swiftness=5, sturdiness=5, smarts=1),
    skills={"Combat": 5, "Tactics": 4},
    goals=["Test"]
)
nua = NonUserActor(sheet)

display_nua_outliers(nua.sheet, "Testing outlier display")
```

### **Test Key Memories**
```python
from key_memories_system import initialize_key_memories, get_key_memories, MemoryCategory, MemoryImportance
from pathlib import Path

memories = initialize_key_memories("test_session", Path('./simulation_data'))

# Create test memory
memories.create_memory(
    title="Test Memory",
    description="This is a test",
    full_narrative="Full narrative here",
    category=MemoryCategory.DISCOVERY,
    importance=MemoryImportance.IMPORTANT,
    location="Test Location"
)

# List memories
memories.list_memories()
```

---

## 🎯 **Summary**

All four systems are now ready for integration:

1. ✅ **RAG System** - Semantic lore retrieval for world-building
2. ✅ **Vessel Selection** - Three archetype choices at start
3. ✅ **Outlier Stats Display** - Clear NUA capability visualization
4. ✅ **Key Memories** - Friends & Fables-style memory system

Each system is:
- **Modular** - Can be integrated independently
- **Persistent** - Saves data between sessions
- **User-friendly** - Clear visual feedback
- **Integrated** - Works with existing UTAS systems

Next steps:
1. Add initialization calls to `redesigned_main.py`
2. Hook up auto-memory creation for significant events
3. Add lore context to LLM prompts
4. Test complete integration
