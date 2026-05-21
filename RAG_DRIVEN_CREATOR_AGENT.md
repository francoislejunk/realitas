# RAG-Driven CreatorAgent Refactor

## Overview

Successfully refactored `CreatorAgent` to be **setting-agnostic** by replacing all hardcoded world context with dynamic RAG (Retrieval-Augmented Generation) queries.

## Problem Solved

**Before:** CreatorAgent was hardcoded for 1990s Earth setting
- Hardcoded references to "1980s/1990s" throughout prompts
- Hardcoded examples with specific technology (cassette players, manual typewriters)
- Required code changes to support different settings
- Imported static `world_context.py` with 1990s-specific lore

**After:** CreatorAgent is setting-agnostic
- All world context retrieved dynamically from RAG system
- No hardcoded time period references
- Works with ANY setting loaded in RAG database
- Change setting by updating lore files, not code

## Architecture Changes

### **New RAG Helper Methods**

Added to `CreatorAgent` class:

```python
def _get_rag_context(query, max_tokens, category_filter) -> str
    """Generic RAG query method"""

def _get_setting_context() -> str
    """Get time period and setting context"""
    
def _get_location_context(occupation, goals) -> str
    """Get location-appropriate context"""
    
def _get_occupation_context(occupation) -> str
    """Get occupation-specific context"""
    
def _get_cultural_context() -> str
    """Get cultural and atmospheric context"""
```

### **Updated Methods**

**1. `_get_initial_scene_prompt()`**
- **Before:** Used `get_world_context_for_scene_generation()` (hardcoded 1990s)
- **After:** Queries RAG for setting, location, occupation, and cultural context
- **Result:** Scene generation adapts to whatever lore is in RAG

**2. `_generate_nua_profile()`**
- **Before:** Used `get_world_context_for_nua_generation()` (hardcoded 1990s)
- **After:** Queries RAG for setting, cultural, and occupation context
- **Result:** NPCs match the world setting dynamically

**3. `_generate_user_actor_profile()`**
- **Before:** Used `get_world_context_for_ua_generation()` (hardcoded 1990s)
- **After:** Queries RAG for setting, cultural, and occupation context
- **Result:** Player characters fit the world automatically

### **Removed Hardcoded Elements**

**Prompt Changes:**
- ❌ "The year is 1980-something"
- ❌ "emphasizing 1980s atmosphere"
- ❌ "1990s Setting" in examples
- ✅ "using the world setting details above"
- ✅ "Reference specific details from the world setting context"

**Example Changes:**
- ❌ Hardcoded 1990s scene examples (14 sentences each)
- ✅ Generic format guidance: "You [establish location]. [Sensory detail from world context]..."
- ✅ Instruction to use RAG context details

**Import Changes:**
- ❌ `from WORLD_BUILDER.world_context import get_world_context_*`
- ✅ Comment: "RAG system will provide all world context dynamically"

## How It Works

### **Scene Generation Flow:**

```
1. User requests new scene
2. CreatorAgent queries RAG:
   - "time period setting year era technology culture" → Setting context
   - "locations places {occupation} {goals}" → Location context
   - "occupation work job {occupation}" → Occupation context
   - "culture atmosphere music fashion social issues" → Cultural context
3. All RAG results combined into world_context string
4. LLM receives world_context in prompt
5. LLM generates scene using retrieved lore
6. Scene matches whatever setting is in RAG
```

### **Example RAG Query Results:**

**For 1990s Setting (current lore):**
```
Setting: "Mid-to-late 1990s, pre-smartphone era, grunge culture..."
Locations: "Dive bars, coffee shops, video rental stores..."
Technology: "Landline phones, pagers, early cell phones..."
Culture: "Grunge, hip-hop, alternative rock..."
```

**For Cyberpunk Setting (if lore changed):**
```
Setting: "2077, megacorporation-dominated dystopia..."
Locations: "Neon-lit streets, underground clubs, corporate towers..."
Technology: "Neural implants, holographic displays, flying cars..."
Culture: "Techno-punk, corporate warfare, street gangs..."
```

**For Medieval Fantasy Setting (if lore changed):**
```
Setting: "Medieval kingdom, age of knights and magic..."
Locations: "Taverns, castles, market squares, forests..."
Technology: "Swords, bows, basic alchemy, no gunpowder..."
Culture: "Feudal society, honor codes, guild systems..."
```

## Benefits

### **1. Setting Flexibility**
- Support multiple campaigns/settings without code changes
- Switch settings by updating RAG database
- Run parallel campaigns in different settings

### **2. Maintainability**
- One place to update world details (RAG lore files)
- No need to refactor code for setting changes
- Consistent lore across all agents

### **3. Consistency**
- All agents can query same RAG system
- Narrator, Interpreter, Decider all use same lore
- No conflicting world details

### **4. Scalability**
- Add new lore categories without code changes
- Expand world details incrementally
- Support community-created settings

### **5. Quality Preservation**
- Same output quality as before
- LLM still receives rich context
- 4-6 sentence constraint maintained

## Usage

### **Changing Settings:**

**Option 1: Update Existing Lore**
```python
# In WORLD_BUILDER/universal_lore.py or similar
rag_system.add_lore_document(
    title="Cyberpunk 2077 Setting",
    content="In 2077, megacorporations rule...",
    category=LoreCategory.WORLD_HISTORY,
    tags=["cyberpunk", "2077", "dystopia"],
    importance=10
)
```

**Option 2: Load Different Lore Database**
```python
# Initialize with different lore directory
rag_system = initialize_lore_rag(
    storage_directory=Path("./cyberpunk_lore"),
    load_defaults=False
)
```

**Option 3: Multiple RAG Systems**
```python
# Different RAG for each campaign
rag_1990s = initialize_lore_rag(Path("./lore_1990s"))
rag_cyberpunk = initialize_lore_rag(Path("./lore_cyberpunk"))
rag_fantasy = initialize_lore_rag(Path("./lore_fantasy"))

# Pass appropriate RAG to CreatorAgent
creator = CreatorAgent(logger, rag_system=rag_cyberpunk)
```

### **No Code Changes Needed:**

The CreatorAgent code remains the same. Only the lore data changes.

## Testing

### **Verify RAG Integration:**

1. **Check RAG is initialized:**
   ```python
   # In main.py
   from WORLD_BUILDER.lore_rag_system import initialize_lore_rag, get_lore_rag
   rag_system = initialize_lore_rag(storage_dir, load_defaults=True)
   ```

2. **Pass RAG to CreatorAgent:**
   ```python
   creator = CreatorAgent(logger, rag_system=rag_system)
   ```

3. **Verify context retrieval:**
   - CreatorAgent will log warnings if RAG queries fail
   - Check logs for "Retrieved RAG context" messages
   - Empty context = RAG not working

### **Test Different Settings:**

1. Update lore in `WORLD_BUILDER/lore_database.json`
2. Run simulation
3. Verify scenes/NPCs match new lore
4. No code changes required

## Migration Notes

### **Backward Compatibility:**

- If RAG system not provided, CreatorAgent logs warning
- Empty context strings returned (graceful degradation)
- System still works but with minimal world context

### **Existing Lore:**

- Current 1990s lore already in RAG system
- Default lore loaded automatically
- No immediate changes to output

### **Future Enhancements:**

1. **Category-Specific Queries:**
   ```python
   from WORLD_BUILDER.lore_rag_system import LoreCategory
   context = self._get_rag_context(
       query="technology",
       category_filter=LoreCategory.TECHNOLOGY
   )
   ```

2. **Dynamic Example Generation:**
   - Query RAG for example scenes
   - Use actual lore examples instead of generic format

3. **Multi-Setting Support:**
   - Tag lore by setting/campaign
   - Filter RAG queries by active campaign

## Files Modified

1. **`agents/creator_agent.py`**
   - Added RAG helper methods (lines 913-963)
   - Updated `_get_initial_scene_prompt()` (lines 965-1050)
   - Updated `_generate_nua_profile()` (lines 1333-1363)
   - Updated `_generate_user_actor_profile()` (lines 290-311)
   - Removed hardcoded world_context imports (line 6-7)

## Result

CreatorAgent is now **truly setting-agnostic**. Change the world by changing lore files, not code. Support infinite settings with zero refactoring.

**Example:**
- Want 1990s? Load 1990s lore.
- Want cyberpunk? Load cyberpunk lore.
- Want medieval fantasy? Load fantasy lore.
- Want space opera? Load sci-fi lore.

Same code. Different worlds.
