# Actor Sheet Now Displays Built-In Memories

## The Problem

NPCs were generated with built-in memories, but they weren't visible anywhere:

```
User: "ua" (to view character sheet)
Result: ❌ No memories section

User: "memories" (to view memories)
Result: ❌ "No memories found matching criteria."
```

The memories existed in `ActorSheet.memories` but weren't being displayed.

## The Root Cause

There are **two separate memory systems**:

1. **ActorSheet.memories** - Simple list of strings, set during character creation
2. **Key Memories System** - Global memory database for discovered/created memories

The built-in memories were in `ActorSheet.memories`, but:
- The `"ua"` command didn't display them
- The `"memories"` command only shows Key Memories System entries

## The Solution

Added a **BACKGROUND MEMORIES** section to the actor sheet display:

```python
if self.memories:
    print("│ 📚 BACKGROUND MEMORIES: │")
    for idx, memory in enumerate(self.memories, 1):
        print(f"│   {idx}. {memory}")
```

## Example Output

### Before (Memories Hidden)

```
┌─────────────────────────────────────────────────────────┐
│ 🎭 Marcus Chen       │ 💼 Street Vendor                  │
│ 🎂 Age: 34 • 📍 Location: Downtown                      │
│ ═══════════════════════════════════════════════════════ │
│ 🧠 Protective and resourceful (Internal) • 🎯 Friendly but cautious (External) │
│ 🎯 Goal: Save enough money to open a proper restaurant
│    Progress: 45% [major]
│ 📋 Current Task: Serve customers at food cart
├─────────────────────────────────────────────────────────┤
│ ⚡ CORE ATTRIBUTES │
...
├─────────────────────────────────────────────────────────┤
│ 📋 ADDITIONAL INFO │
│ Inventory: Food Cart Keys, Apron, Cash Box              │
└─────────────────────────────────────────────────────────┘
❌ No memories visible!
```

### After (Memories Displayed)

```
┌─────────────────────────────────────────────────────────┐
│ 🎭 Marcus Chen       │ 💼 Street Vendor                  │
│ 🎂 Age: 34 • 📍 Location: Downtown                      │
│ ═══════════════════════════════════════════════════════ │
│ 🧠 Protective and resourceful (Internal) • 🎯 Friendly but cautious (External) │
│ 🎯 Goal: Save enough money to open a proper restaurant
│    Progress: 45% [major]
│ 📋 Current Task: Serve customers at food cart
├─────────────────────────────────────────────────────────┤
│ ⚡ CORE ATTRIBUTES │
...
├─────────────────────────────────────────────────────────┤
│ 📋 ADDITIONAL INFO │
│ 📚 BACKGROUND MEMORIES: │
│   1. Immigrated from Hong Kong at age 15 with his family
│   2. Lost parents in a fire, now takes care of younger sister
│   3. Learned cooking from his grandmother's traditional recipes
│   4. Knows every street vendor and shop owner in the district
│ Inventory: Food Cart Keys, Apron, Cash Box              │
└─────────────────────────────────────────────────────────┘
✓ Memories now visible!
```

## Where Memories Appear

### 1. User Actor Sheet (`ua` command)

```
(What do you want to do?): ua

┌─────────────────────────────────────────────────────────┐
│ 🎭 Lena Kovač        │ 💼 Underground Music Promoter    │
...
├─────────────────────────────────────────────────────────┤
│ 📋 ADDITIONAL INFO │
│ 📚 BACKGROUND MEMORIES: │
│   1. Started DJing in underground clubs at age 18
│   2. Built a reputation for discovering new talent
│   3. Lost her best friend in a club fire three years ago
│   4. Determined to create safer, better underground events
└─────────────────────────────────────────────────────────┘
```

### 2. NPC Sheet (`people` then select NPC)

```
(What do you want to do?): people

Available NPCs:
1. Marcus Chen (Street Vendor)

(What do you want to do?): 1

┌─────────────────────────────────────────────────────────┐
│ 🎭 Marcus Chen       │ 💼 Street Vendor                  │
...
├─────────────────────────────────────────────────────────┤
│ 📋 ADDITIONAL INFO │
│ 📚 BACKGROUND MEMORIES: │
│   1. Immigrated from Hong Kong at age 15 with his family
│   2. Lost parents in a fire, now takes care of younger sister
│   3. Learned cooking from his grandmother's traditional recipes
│   4. Knows every street vendor and shop owner in the district
└─────────────────────────────────────────────────────────┘
```

## Two Types of Memories

### 1. Built-In Memories (ActorSheet.memories)
- **Created during character generation**
- **Static background** - doesn't change
- **Displayed in actor sheet** (`ua` command)
- **Examples:**
  - "Grew up in Brooklyn"
  - "Lost father at age 12"
  - "Trained as a mechanic by grandfather"

### 2. Discovered Memories (Key Memories System)
- **Created during gameplay** via inquiries, actions, narration
- **Dynamic** - grows as you play
- **Displayed via `memories` command**
- **Examples:**
  - "You learned Joe's Diner is open 24/7"
  - "You discovered the subway runs until midnight"
  - "You remember your best friend Sarah lives across town"

## How They Work Together

```
Character Creation:
↓
Built-In Memories → ActorSheet.memories
  - "Immigrated from Hong Kong at age 15"
  - "Lost parents in a fire"
  - "Learned cooking from grandmother"
↓
Display via: "ua" command

During Gameplay:
↓
Discovered Memories → Key Memories System
  - "Learned about Joe's Diner location"
  - "Discovered subway schedule"
  - "Remembered best friend Sarah"
↓
Display via: "memories" command
```

## Benefits

✅ **Background visible** - Can see character history  
✅ **Context for RP** - Know character's past  
✅ **Informs decisions** - Background affects choices  
✅ **Enriches interactions** - NPCs have depth  
✅ **Always accessible** - Via `ua` command  

## Example Scenarios

### Scenario 1: Meeting an NPC

```
User: "I talk to the street vendor"
→ NPC: Marcus Chen appears
→ User: "people" → Select Marcus → View sheet
→ See memories:
  - "Lost parents in a fire, now takes care of younger sister"
→ User can reference this in conversation
```

### Scenario 2: Understanding Your Character

```
User: "ua" (view own sheet)
→ See memories:
  - "Started DJing in underground clubs at age 18"
  - "Lost best friend in a club fire three years ago"
→ Understand why character is cautious about safety
→ Roleplay accordingly
```

### Scenario 3: NPC Behavior Makes Sense

```
NPC: Marcus refuses to get involved in illegal activity
User: "Why is he so cautious?"
→ View Marcus's sheet
→ See memory: "Takes care of younger sister"
→ Understand: He can't risk getting in trouble
```

## Files Modified

**`actor_sheet.py`** (lines 689-692)
- Added BACKGROUND MEMORIES section
- Displays each memory with numbering
- Shows in ADDITIONAL INFO section

## Result

✅ **Built-in memories now visible** - In actor sheet  
✅ **Easy to access** - Via `ua` command  
✅ **Clear display** - Numbered list format  
✅ **Enriches characters** - Background is visible  
✅ **Informs roleplay** - Know character history  

Users can now see the built-in memories that were generated during character creation!
