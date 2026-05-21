# Memory Display Design

## Overview
The memory system provides immersive, importance-based visual displays for both listing and viewing memories.

---

## Memory List Display (`/mem` or `memories`)

### Example Output:

```
══════════════════════════════════════════════════════════════════════
💭 YOUR MEMORIES (8)
══════════════════════════════════════════════════════════════════════

🔴 CRITICAL MOMENTS:
  📌 [1] DEATH OF MARCUS CALLAHAN
       loss • Dec 15, 2024
       Marcus was killed in a confrontation with the Syndicate. His last words were a warning about the truth you were seeking.

   [2] DISCOVERED: THE TRUTH ABOUT REALITAS
       revelation • Dec 10, 2024
       You uncovered the shocking reality behind the simulation - nothing is what it seems. The entire world is a construct.

🟡 IMPORTANT EVENTS:
   [3] MET SARAH CHEN
       relationship • Dec 08, 2024
       First meeting with Sarah Chen, a hacker. She offered to help you investigate the Syndicate in exchange for protection.

  📌 [4] COMPLETED: FIX THE ENGINE
       achievement • Dec 07, 2024
       Successfully repaired the Chevy's engine after hours of work. The car runs perfectly now.

🔵 NOTABLE MOMENTS:
   [5] FOUND STRANGE DEVICE
       discovery • Dec 06, 2024
       Discovered an unusual electronic device hidden in the garage. It appears to be some kind of tracking beacon.

   [6] CONVERSATION WITH OLD MAN
       relationship • Dec 05, 2024
       Had a meaningful conversation with an elderly mechanic about the old days and the changes in the neighborhood.

⚪ ROUTINE EVENTS:
   [7] EXPLORED GARAGE
       location • Dec 04, 2024
       Looked around the garage bay, familiarizing yourself with the tools and equipment available.

   [8] BOUGHT COFFEE
       item • Dec 03, 2024
       Purchased coffee from the corner store to stay alert during the long night shift.

══════════════════════════════════════════════════════════════════════
💡 Type 'recall [number]' or '/mem [number]' to view full memory
💡 Type '/mem help' for more commands

```

### Features:
- **Grouped by Importance** - Critical → Important → Notable → Routine
- **Color-Coded** - Red (critical), Yellow (important), Blue (notable), White (routine)
- **Pin Indicators** - 📌 shows pinned memories
- **Numbered** - Sequential numbering for easy recall
- **Metadata** - Category and date for each memory
- **Full Descriptions** - Complete description text (no truncation)

---

## Detailed Memory View (`/mem 1` or `recall 1`)

### Example Output:

```
══════════════════════════════════════════════════════════════════════
📌 🔴 DEATH OF MARCUS CALLAHAN
══════════════════════════════════════════════════════════════════════

📍 Downtown Alley • December 15, 2024 at 23:45
🏷️  Loss • Critical importance
👥 Present: Marcus Callahan, Sarah Chen, You
💫 Emotional tone: tragic

──────────────────────────────────────────────────────────────────────

What Happened:
Marcus was killed in a confrontation with the Syndicate. His last words 
were a warning about the truth you were seeking.

──────────────────────────────────────────────────────────────────────

The Memory:
The rain hammered down as Marcus stumbled backward, clutching his chest. 
Blood seeped between his fingers, dark against the neon-lit alley. Sarah 
screamed, but you couldn't move—frozen as Marcus locked eyes with you.

"They know," he gasped, each word a struggle. "They know what you're 
looking for. The Realitas... it's not what you think. Nothing is."

He collapsed, and the last thing you saw was his hand reaching toward 
you, trembling, before going still. The Syndicate operatives melted into 
the shadows, leaving only the sound of rain and Sarah's sobs.

You would never forget the look in his eyes—not fear, but urgency. A 
desperate need to tell you something he'd never get the chance to say.

──────────────────────────────────────────────────────────────────────

📝 Your Note:
This changed everything. Marcus knew something about Realitas that got 
him killed. I need to find out what.

──────────────────────────────────────────────────────────────────────

🔖 Tags: syndicate, realitas, warning, death
⏱️  Turn #47

══════════════════════════════════════════════════════════════════════

```

### Features:
- **Importance-Based Colors** - Title color matches importance
- **Emoji Indicators** - 🔴🟡🔵⚪ for importance, 📌 for pinned
- **Rich Metadata** - Location, date/time, actors, emotional tone
- **Clear Sections** - "What Happened" (summary) vs "The Memory" (full narrative)
- **User Notes** - Personal reflections you can add
- **Tags & Turn Number** - Additional context at bottom

---

## Memory Save Notifications

### When Memories Are Created:

```
🔴 Memory Saved: Death of Marcus Callahan [critical]
🟡 Memory Saved: Met Sarah Chen [important]
🔵 Memory Saved: Found Strange Device [notable]
⚪ Memory Saved: Explored Garage [routine]
```

### When NPCs Remember You:

```
🔴 Marcus remembers: You saved his life during the ambush...
   💾 NUA memory saved to disk

🟡 Sarah remembers: You helped her hack the security system...
   💾 NUA memory saved to disk

🔵 Merchant remembers: You bought supplies from him...
```

---

## Available Commands

### Quick Meta Commands:
- `/mem` - List all memories
- `/mem [number]` - View specific memory (e.g., `/mem 3`)
- `/mem pinned` - Show only pinned memories
- `/mem search [query]` - Search memories (e.g., `/mem search combat`)
- `/mem help` - Show help

### Natural Language:
- `memories` - List all memories
- `recall 3` - View memory #3
- `pinned memories` - Show pinned memories
- `search memories combat` - Search for combat memories

---

## Design Philosophy

### Visual Hierarchy
- **Importance First** - Critical memories stand out immediately
- **Color Psychology** - Red = danger/critical, Yellow = important, Blue = notable
- **Progressive Disclosure** - List shows summary, detail view shows full narrative

### Immersion
- **Narrative Language** - "What Happened" vs "The Memory"
- **Emotional Context** - Tone and actors present
- **Personal Touch** - User notes for reflection

### Usability
- **Quick Access** - Numbered list for easy recall
- **Search & Filter** - Find specific memories fast
- **Pin Important** - Keep critical memories at top

### Consistency
- **Emoji System** - Same emojis across all displays
- **Color Coding** - Consistent importance colors
- **Format** - Predictable structure for all memories

---

## Example User Flow

```
> /mem
[Shows grouped list of all memories]

> /mem 1
[Shows detailed view of memory #1]

> /mem search Marcus
[Shows all memories mentioning Marcus]

> /mem pinned
[Shows only pinned memories]
```

---

## Technical Implementation

**Files:**
- `key_memories_system.py` - Core memory display logic
- `npc_memory_system.py` - NUA memory notifications
- `color_utils.py` - Color definitions

**Key Methods:**
- `list_memories()` - Grouped, importance-based list
- `display_memory()` - Detailed, immersive view
- `create_memory()` - Shows save notification

**Storage:**
- `./simulation_data/memories/{session_id}_memories.json`
- `./simulation_data/nua_memories/nua_memories.json`
