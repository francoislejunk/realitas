# Scene Description Length Constraints

## Problem
Scene descriptions were becoming excessively long and detailed, reading like exhaustive inventories rather than evocative narratives.

**Example of TOO LONG (original):**
> "You stand in the open bay of The Rusty Wrench Auto Shop, the mid-morning sunlight streaming through the grimy windows and casting long shadows across the concrete floor. The air smells of oil, grease, and the faint metallic tang of cooling engines. The shop is empty—no customers, no other mechanics—just the hum of the overhead fluorescent lights and the occasional drip of a faucet in the corner. A classic rock station plays softly from an old AM radio perched on a workbench, the static occasionally cutting through the music. The two service bays are cluttered with tools, rags, and half-finished jobs. A grease-stained calendar from 1996 hangs on the wall, its corners curled. The far wall is lined with shelves stocked with spare parts, wrenches, and carburetor kits. A rusted-out 1972 Chevy Nova sits on the lift in the first bay, its hood propped open, while a second bay holds a pile of tires and a lonely tool cart. The waiting area is sparse—a few plastic chairs, a coffee pot that looks like it hasn't been cleaned in weeks, and a stack of dog-eared car magazines from the early '90s. A TV mounted in the corner plays a muted baseball game. The back door is slightly ajar, leading to a small fenced lot littered with junk cars and scrap metal. Your fingertips brush the edge of a wrench in your pocket, a nervous habit when you're thinking."

**This is 14 sentences and reads like a room inventory, not a narrative.**

## Solution

### **Target Length: 4-6 Sentences**

Scene descriptions should be **concise and evocative**, not exhaustive catalogs. They should:
- **Suggest** details, don't **inventory** everything
- **Evoke** atmosphere, don't **catalog** objects
- Give enough to ground the player, then let them explore

**Example of GOOD LENGTH (revised):**
> "You stand in the open bay of The Rusty Wrench Auto Shop, mid-morning sunlight cutting through grimy windows. The air smells of oil and grease, and a classic rock station plays from an old radio on the workbench. Two service bays hold half-finished jobs - a '72 Chevy Nova on the lift, tools scattered around. The back door is ajar, leading to a fenced lot of junk cars. Your fingers brush the wrench in your pocket, a nervous habit when you're thinking."

**This is 5 sentences and gives the same essential information with better pacing.**

## Implementation

### 1. CreatorAgent (Initial Scene Generation)
**File:** `agents/creator_agent.py`

**Changes:**
- Added explicit length constraint: `**LENGTH CONSTRAINT: 4-6 SENTENCES MAXIMUM**`
- Updated JSON field description: `"setting": "A concise description (4-6 sentences)..."`
- Replaced verbose example scenes with concise 4-6 sentence versions
- Added guidance: "Be evocative, not exhaustive. Suggest details, don't inventory everything."

**Lines Modified:** 963, 992, 972-984 (examples)

### 2. NarratorAgent (Scene Transitions)
**File:** `agents/narrator_agent.py`

**Changes:**
- Strengthened existing constraint: `**CRITICAL LENGTH: 4-6 sentences MAXIMUM**`
- Added anti-inventory guidance: "Suggest details, don't inventory everything. Evoke atmosphere, don't catalog objects."
- Reinforced conciseness in narrative structure

**Lines Modified:** 278, 285

## Writing Guidelines

### DO:
✅ Focus on **atmosphere** and **key details**
✅ Use **sensory language** (smell, sound, sight, touch)
✅ Suggest **exploration opportunities** without listing everything
✅ Include **1-2 character details** (thoughts, habits, reactions)
✅ Create **mood** and **tone** efficiently

### DON'T:
❌ List every object in the room
❌ Describe every piece of furniture
❌ Catalog all available items
❌ Mention every detail of the environment
❌ Write more than 6 sentences

## Examples

### Mechanic (5 sentences - GOOD)
> "You stand in the open bay of The Rusty Wrench Auto Shop, mid-morning sunlight cutting through grimy windows. The air smells of oil and grease, and a classic rock station plays from an old radio on the workbench. Two service bays hold half-finished jobs - a '72 Chevy Nova on the lift, tools scattered around. The back door is ajar, leading to a fenced lot of junk cars. Your fingers brush the wrench in your pocket, a nervous habit when you're thinking."

### Private Investigator (5 sentences - GOOD)
> "You step into the lobby of the Riverside Apartments on a foggy October evening. A flickering fluorescent bulb casts harsh shadows across worn linoleum. Mailboxes line one wall, a narrow staircase leads up, and a door marked 'Superintendent' stands at the far end. The building is eerily quiet except for a muffled TV somewhere above. Your hand moves to the notepad in your jacket - three days since Sarah Chen vanished."

### Urban Explorer (4 sentences - GOOD)
> "The abandoned Hartwell Manufacturing Plant looms in pale moonlight, broken windows reflecting distant city lights. You can make out a loading dock with a partially open door, a side entrance with a broken lock, and a fire escape leading to upper floors. Your camera equipment feels heavy in your backpack. The question is where to start documenting this industrial relic."

## Benefits

1. **Better Pacing** - Players aren't overwhelmed with information
2. **More Immersive** - Suggests rather than tells everything
3. **Encourages Exploration** - Players discover details through actions
4. **Easier to Read** - Concise descriptions are more engaging
5. **Faster Generation** - LLM produces shorter, focused content

## Testing

When testing scene generation:
- Count sentences in generated descriptions
- Flag anything over 6 sentences for revision
- Ensure examples in prompts match the 4-6 sentence target
- Check that descriptions evoke rather than inventory
