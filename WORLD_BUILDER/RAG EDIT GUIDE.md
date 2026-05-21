# RAG EDIT GUIDE

This file explains every `WorldbuildingCategory` used by Realitas Neo’s Worldbuilding RAG system:

- what each category is for
- where it is used in code (which systems/agents typically query it)
- recommended content format per category
- what edits are **safe** vs **risky**
- exactly when you must **rebuild the RAG database** vs when you only need a **simulation restart**

> Important: **Categories do not “do” anything by themselves.** They only matter because code/agents query them. So “how risky” a category is depends on:
>
>- whether code parses it with regex/structure expectations (high risk)
>- whether it is pure narrative flavor (lower risk)

---

## 0) Mental model: two separate layers

### A) Category + RAG engine layer
Lives in:

- `WORLD_BUILDER/worldbuilding_rag.py`
  - `WorldbuildingCategory` enum
  - `WorldbuildingRAGSystem` storage + embedding + retrieval (`get_context_for_llm`)

Edits here affect:

- what categories exist
- how documents are stored and searched
- what retrieval returns

This layer is **high risk**.

### B) Lore document content layer
Lives in:

- `WORLD_BUILDER/realitas_lore.py`
  - lots of triple-quoted content strings
  - `create_lore_entries()` which converts strings to RAG docs

Edits here affect:

- what text is embedded into the RAG
- what the LLM “knows” when it asks for context

This is your normal editing surface.

---

## 1) How changes “take effect”

### If you edit `WORLD_BUILDER/realitas_lore.py` (RAG content)
Your change does **not** affect the active worldbuilding RAG database until you rebuild it:

- Run: `python WORLD_BUILDER/realitas_lore.py`

This regenerates:

- `simulation_data/worldbuilding_rag/worldbuilding/worldbuilding_database.json`

### If you edit runtime code (behavior)
Examples:

- `agents/creator_agent.py`
- `vessel_selection_system.py`
- `worldbuilding_helpers.py`
- `WORLD_BUILDER/worldbuilding_rag.py`

Those changes take effect when you **restart the simulation** (`python MAIN/redesigned_main.py`).

### If you edit both
Do both:

- rebuild DB (`python WORLD_BUILDER/realitas_lore.py`)
- restart sim

---

## 2) What “lore entry generation” means here

`WORLD_BUILDER/realitas_lore.py` contains the authoritative list of entries in `create_lore_entries()`:

- each entry has: `title`, `content`, `category`, `tags`, `importance`

So:

- Changing a **content string** changes the content of its entry on next rebuild.
- Changing `create_lore_entries()` changes:
  - which docs exist
  - their category
  - their tags/importance

---

## 3) Quick “safe vs risky” cheat sheet

- **Safest edits**: wording, examples, extra detail, clarifications.
- **Medium risk**: renaming canonical terms that the rest of the lore references.
- **High risk**:
  - edits that break formatting that code depends on (e.g. cities list formatting)
  - edits that change a structured “whitelist” category (goals/factions) without keeping bullet structure
  - edits to `WorldbuildingCategory` or retrieval logic

---

# 4) Category-by-category guide

Below is every `WorldbuildingCategory` in `WORLD_BUILDER/worldbuilding_rag.py`, grouped roughly by how it’s used.

For each category:

- **Purpose**
- **Typical consumers**
- **Recommended format**
- **Safe edits**
- **Risky edits**
- **When you must rebuild**

> Unless stated otherwise: if you edit the content in `realitas_lore.py`, you must rebuild the DB.

---

## CORE WORLD

### `WORLD_STRUCTURE`
- **Purpose**
  - Big-picture world constraints (geography rules, travel constraints, domain logic).
- **Typical consumers**
  - narrator grounding
  - scene generation grounding
- **Recommended format**
  - headings + bullet “rules” + examples.
- **Safe edits**
  - add constraints, clarify tone, expand descriptions.
- **Risky edits**
  - contradictions with `CITIES`, `PLACES`, `CIVILIZATION`.
- **Rebuild required?**
  - Yes (content edit requires DB rebuild).

### `TEMPORAL`
- **Purpose**
  - Defines the canonical time period / timeline.
- **Typical consumers**
  - `worldbuilding_helpers.extract_year_range_from_rag()`
  - vessel generation year enforcement
  - any prompt needing era grounding
- **Recommended format (IMPORTANT)**
  - Keep a machine-readable range line somewhere:
    - `TIME PERIOD: <label>, 1230-1250`
  - Then narrative timeline below.
- **Safe edits**
  - expand timeline beats, add historical texture.
- **Risky edits**
  - removing/renaming the `TIME PERIOD:` line or changing it so it no longer contains two 4-digit years separated by `-` or `–`.
- **Rebuild required?**
  - Yes for content changes.

### `BEINGS`
- **Purpose**
  - Taxonomy of what entities exist.
- **Consumers**
  - NPC generation constraints
  - narrator grounding
- **Recommended format**
  - headings per being type + capabilities/vulnerabilities.
- **Safe edits**
  - add detail.
- **Risky edits**
  - adding/removing entire being types (cascades to everything).
- **Rebuild required?**
  - Yes.

### `SUPERNATURAL`
- **Purpose**
  - Magic/power system lore.
- **Consumers**
  - ability references
  - narrator and conflict generation
- **Recommended format**
  - grouped lists, clear names.
- **Safe edits**
  - additions, examples.
- **Risky edits**
  - renaming canonical powers if other docs reference them.
- **Rebuild required?**
  - Yes.

---

## SOCIETY

### `CIVILIZATION`
- **Purpose**
  - Tech level, economy, information flow.
- **Consumers**
  - plausibility grounding (items, travel, communication)
- **Recommended format**
  - sections by domain: economy, governance, literacy, medicine.
- **Safe edits**
  - expand texture.
- **Risky edits**
  - introducing out-of-era tech.
- **Rebuild required?**
  - Yes.

### `FACTIONS_ORGANIZATIONS`
- **Purpose**
  - lists major orgs/power blocs.
- **Consumers**
  - story arcs, NPC motivations.
- **Recommended format**
  - faction blocks: identity, goals, methods, enemies/allies.
- **Safe edits**
  - add factions, detail.
- **Risky edits**
  - renaming factions used elsewhere.
- **Rebuild required?**
  - Yes.

### `RELATIONSHIP_MATRICES`
- **Purpose**
  - high-level “how groups relate” rules.
- **Consumers**
  - relationship reasoning
  - conflict/social simulation grounding
- **Recommended format**
  - matrix tables or bullet rules.
- **Safe edits**
  - clarify rules.
- **Risky edits**
  - embedding generation instructions that belong in `*_GENERATION` (causes duplication/confusion).
- **Rebuild required?**
  - Yes.

### `NUA_RELATIONSHIP_MATRICES`
### `MNUA_RELATIONSHIP_MATRICES`
- **Purpose**
  - same concept as `RELATIONSHIP_MATRICES`, but tuned for common vs major NPCs.
- **Consumers**
  - NPC relationship generation.
- **Format**
  - keep relationship logic; avoid actor-generation duplication.
- **Rebuild required?**
  - Yes.

### `CONFLICT_GENERATORS`
- **Purpose**
  - sources of tension and conflict seeds.
- **Consumers**
  - narrator conflict injection
  - plot escalation
- **Format**
  - bullet lists of conflicts + triggers.
- **Safe edits**
  - very safe.
- **Risky edits**
  - low risk.
- **Rebuild required?**
  - Yes.

---

## NARRATIVE

### `CULTURE`
- **Purpose**
  - tone, customs, slang, sensory anchors.
- **Consumers**
  - narrator voice
  - NPC speech patterns
  - scene texture
- **Recommended format**
  - “do/don’t” + jargon lists + short examples.
- **Safe edits**
  - extremely safe (mostly flavor).
- **Risky edits**
  - introducing modern language/objects; contradicting `CIVILIZATION`.
- **How it affects lore entry generation**
  - The *entry structure* does not change.
  - The **content embedded in the CULTURE docs changes**, so retrieval results change.
- **Rebuild required?**
  - Yes, to update the stored doc content & embeddings.

### `NARRATION_STYLE_TONE`
- **Purpose**
  - narrator style rules.
- **Consumers**
  - narrator agent.
- **Format**
  - bullet rules + examples.
- **Safe edits**
  - safe but high impact on “feel”.
- **Rebuild required?**
  - Yes.

### `EXPANSION_SEEDS`
- **Purpose**
  - seeds for procedural expansion.
- **Consumers**
  - world expansion flows.
- **Format**
  - prompt seeds, constraints.
- **Rebuild required?**
  - Yes.

---

## SYSTEMS / REFERENCE

### `MECHANICS`
- **Purpose**
  - skills/statuses/rules reference.
- **Consumers**
  - creator agent, narrator, validation rules.
- **Format**
  - stable vocab lists/dicts.
- **Safe edits**
  - clarifying text.
- **Risky edits**
  - renaming skill names if code expects exact names.
- **Rebuild required?**
  - Yes.

### `PLACES`
- **Purpose**
  - generic POIs/archetypal locations.
- **Consumers**
  - scene setting.
- **Format**
  - headings + sensory anchors + threats.
- **Rebuild required?**
  - Yes.

### `CITIES`
- **Purpose**
  - canon major cities used for location grounding.
- **Consumers (IMPORTANT)**
  - `CreatorAgent` and `VesselSelectionSystem` parse allowed city names from RAG.
- **Recommended format (IMPORTANT)**
  - city names on their own line in bold:

```text
**Constantinople**
- ...

**Prague**
- ...
```

- **Safe edits**
  - add cities, expand city details.
- **Risky edits**
  - changing the bold city-name pattern may break allowed-city extraction.
- **Rebuild required?**
  - Yes.

---

## GENERATION GUIDELINES

### `UA_GENERATION`
### `NUA_GENERATION`
### `MNUA_GENERATION`
### `INUA_GENERATION`
- **Purpose**
  - “how to generate” rules per actor type.
- **Consumers**
  - `CreatorAgent` uses these as RAG context.
  - Some rules are parsed (UA age range).
- **Recommended format**
  - bold headings + bullet rules.
  - if you want code to parse something, keep a stable line like:
    - `AGE RANGE: 18-55`
- **Safe edits**
  - clarify style and constraints.
- **Risky edits**
  - removing parseable lines if code depends on them.
- **Rebuild required?**
  - Yes.

---

## ROLE DATA / WHITELISTS

### `UA_OCCUPATIONS`, `NUA_OCCUPATIONS`, `MNUA_OCCUPATIONS`
- **Purpose**
  - lists of plausible roles.
- **Consumers**
  - creator agent grounding
  - vessel generation constraints
- **Format**
  - bulleted lists + clear headings.
- **Risky edits**
  - making everything prose-only (harder for model + any extractors).
- **Rebuild required?**
  - Yes.

### `UA_GOALS`, `NUA_GOALS`, `MNUA_GOALS`
- **Purpose**
  - goal “patterns” (how to think about goals).
- **Consumers**
  - creator grounding.
- **Format**
  - patterns, examples.
- **Rebuild required?**
  - Yes.

### `GOALS_UA`, `GOALS_NUA`, `GOALS_MNUA`
- **Purpose**
  - explicit goal whitelists.
- **Consumers**
  - Mode A goal selection: model must pick by ID.
- **Format (IMPORTANT)**
  - one goal per bullet line.
- **Risky edits**
  - changing to paragraphs (breaks whitelist usefulness).
- **Rebuild required?**
  - Yes.

### `FACTION_UA`, `FACTION_NUA`, `FACTION_MNUA`
- **Purpose**
  - faction/clan options by actor type.
- **Consumers**
  - creator agent faction grounding + whitelist extraction.
- **Format recommendation**
  - keep a clean bullet list of faction names somewhere (even if you also include prose descriptions).
- **Safe edits**
  - add factions, detail.
- **Risky edits**
  - inconsistent naming across docs.
- **Rebuild required?**
  - Yes.

---

## WORLD SIMULATION

### `ENVIRONMENTAL_HAZARDS`
- **Purpose**
  - hazards/status exchanges.
- **Consumers**
  - scene consequences, survival mechanics.
- **Format**
  - structured entries (type/condition/effects).
- **Rebuild required?**
  - Yes.

### `WORLD_EVENTS`
- **Purpose**
  - ambient events + interaction triggers.
- **Consumers**
  - narrator escalation and texture.
- **Format**
  - event lists grouped by place/faction.
- **Rebuild required?**
  - Yes.

---

# 5) Practical editing workflow

## Edit RAG content
1) Edit `WORLD_BUILDER/realitas_lore.py`
2) Rebuild DB:
   - `python WORLD_BUILDER/realitas_lore.py`
3) Restart sim:
   - `python MAIN/redesigned_main.py`

## Edit runtime rules
1) Edit code (e.g. `CreatorAgent`, `VesselSelectionSystem`)
2) Restart sim

---

# 6) What edits require a full rebuild vs not

- **Needs rebuild**
  - any changes to the content strings in `realitas_lore.py`
  - any changes to `create_lore_entries()` (titles/categories/tags)

- **Does not need rebuild**
  - changes to:
    - prompt templates
    - extraction logic
    - validation logic
    - year enforcement logic

---

# 7) Known “format-sensitive” areas (important)

- `TEMPORAL`
  - keep `TIME PERIOD: ..., YYYY-YYYY` somewhere.
- `CITIES`
  - keep city names as `**City Name**` lines.
- `GOALS_*` / `FACTION_*`
  - keep clean bullet lists for whitelists / extractors.
- `UA_GENERATION` age parsing
  - keep `AGE RANGE: X-Y` line if you want code-driven range.

---

# 8) Plain-English summary (simple version)

This is the simplest way to think about the RAG.

The RAG is just a library of world documents that the AI can look up while it is generating characters and scenes. Each document is stored under a category, like `CULTURE` or `TEMPORAL`. The category is basically a label that helps the system find the right document when it searches.

When you edit the worldbuilding text in `WORLD_BUILDER/realitas_lore.py`, you are editing the “source text” for those documents. The running game does not automatically see those edits. You must rebuild the RAG database by running `python WORLD_BUILDER/realitas_lore.py` so the documents and embeddings get updated.

When you edit Python code (like `creator_agent.py`, `vessel_selection_system.py`, or `worldbuilding_helpers.py`), you are changing how the game behaves. These changes usually only require a simulation restart, because the code is loaded when the program starts.

Changing `CULTURE` changes what the AI thinks is normal for people, language, customs, and atmosphere. It does not change the list of lore entries that exist. It just changes the content inside the existing CULTURE documents. You still need a rebuild to make the RAG database store the new CULTURE text.

Changing `TEMPORAL` changes what years the simulation can use and what the era feels like. If you want the year-range system to keep working, you must keep a line that clearly includes two four-digit years, like `TIME PERIOD: ..., 1230-1250`. If you remove that pattern, the code may not be able to detect the range.

Some categories are “format sensitive.” This means code expects the text to follow a specific shape. For example, the cities list is easiest for the system when each city name is on its own bold line, like `**Prague**`. The safest edits in these categories are edits that keep the same structure and only change wording.

Some categories act like “whitelists.” For example, the explicit goal libraries and explicit faction libraries are meant to be lists the AI can pick from. The safest way to edit these is to keep one item per bullet line. If you turn them into paragraphs, it becomes harder for the AI to follow and harder for any list parsing.

If you want to know whether a change requires a rebuild, ask yourself one question. Did I change `realitas_lore.py` content or `create_lore_entries()`? If yes, rebuild the RAG database. If not, and you only changed Python behavior code, you usually just restart the simulation.

## Simple category cheat sheet (one or two sentences each)

This section is intentionally repetitive and simple. It is meant to help you decide what to edit without thinking about code.

### `WORLD_STRUCTURE`
This category describes the physical and logical structure of the world. If you change it, you change what locations and travel rules the AI will assume.

### `TEMPORAL`
This category describes the timeline and the year range. If you keep the `TIME PERIOD: ..., YYYY-YYYY` line, the year-range system will keep working.

### `BEINGS`
This category lists what kinds of beings exist (humans, monsters, etc.). If you remove or rename a being type, the whole simulation can start behaving differently.

### `SUPERNATURAL`
This category explains supernatural powers and rules. It mainly affects what the AI thinks is possible in scenes.

### `CIVILIZATION`
This category explains everyday life, tech level, economy, and social structure. It controls whether the AI generates believable medieval details or accidentally drifts modern.

### `FACTIONS_ORGANIZATIONS`
This category explains major organizations and power groups. It affects politics, alliances, and recurring enemies or allies.

### `RELATIONSHIP_MATRICES`
This category tells the AI how groups tend to relate to each other. It helps the AI produce consistent hostility, alliances, fear, and sympathy.

### `NUA_RELATIONSHIP_MATRICES`
This category is the relationship logic for normal NPCs. Editing it changes how common NPCs treat each other and the player.

### `MNUA_RELATIONSHIP_MATRICES`
This category is the relationship logic for major NPCs. Editing it changes how major recurring figures form alliances and rivalries.

### `CONFLICT_GENERATORS`
This category is a list of “things that cause trouble.” Editing it changes what kinds of problems show up in scenes.

### `CULTURE`
This category controls vibe, customs, slang, taboos, and sensory detail. Editing it mostly changes the “feel” of the world and dialogue.

### `NARRATION_STYLE_TONE`
This category controls how the narrator writes. Editing it changes the writing style without changing the world facts.

### `EXPANSION_SEEDS`
This category gives the AI ideas for how to expand the world. Editing it changes what kinds of new lore the system tends to generate.

### `MECHANICS`
This category defines the rules vocabulary (skills, statuses, etc.). If you rename skills here, you might cause mismatches if other parts of the system expect exact names.

### `PLACES`
This category is for location archetypes and points of interest. Editing it changes where scenes can plausibly happen.

### `CITIES`
This category is for major city entries. Keep city names formatted like `**City Name**` so the system can reliably treat them as allowed locations.

### `UA_GENERATION`
This category tells the AI how to generate the player character. If you keep a simple `AGE RANGE: X-Y` line, the code can enforce the age range automatically.

### `NUA_GENERATION`
This category tells the AI how to generate common NPCs. It mainly affects how “normal people” get created.

### `MNUA_GENERATION`
This category tells the AI how to generate major recurring NPCs. Editing it changes the strength, menace, and story role of major characters.

### `INUA_GENERATION`
This category tells the AI how to generate inanimate actors (objects, structures, hazards). Editing it changes what kind of interactable objects appear.

### `UA_OCCUPATIONS`
This category provides the allowed occupation pool for the player. If you add or remove entries here, you change what kinds of player characters are likely.

### `NUA_OCCUPATIONS`
This category provides the allowed occupation pool for normal NPCs. It affects background population roles.

### `MNUA_OCCUPATIONS`
This category provides the allowed “roles of leverage” for major NPCs. It affects what kinds of recurring power figures exist.

### `UA_GOALS`, `NUA_GOALS`, `MNUA_GOALS`
These categories explain goal patterns, meaning they teach the AI how to think about motivations. They are usually safe to edit because they are guidance, not strict lists.

### `GOALS_UA`, `GOALS_NUA`, `GOALS_MNUA`
These categories are explicit goal libraries. If you want reliable behavior, keep one goal per bullet line so the AI can select goals cleanly.

### `FACTION_UA`, `FACTION_NUA`, `FACTION_MNUA`
These categories describe faction options. If you want factions to be reliably selectable, keep a clean bullet list of faction names somewhere in the document.

### `ENVIRONMENTAL_HAZARDS`
This category describes hazards and how they affect statuses. Editing it changes what kinds of danger appear and what costs they apply.

### `WORLD_EVENTS`
This category describes events that can happen in the world. Editing it changes the kinds of background activity and interaction prompts the AI can draw from.

## Simple action checklist

If you only remember one thing, remember this.

If you changed `WORLD_BUILDER/realitas_lore.py`, you should rebuild the RAG database by running `python WORLD_BUILDER/realitas_lore.py`. After that, restart the simulation so the running program loads the updated database.

If you changed a Python behavior file (like the creator agent, vessel selection, year extraction, validation rules, or display), you only need to restart the simulation.

If you are unsure, do both. Rebuilding and restarting is always safe, it just takes longer.

---

# Lore Entries Guide

This section explains when you only need to change the lore text, and when you also need to edit `create_lore_entries()`.

## The simplest way to think about it

`create_lore_entries()` is the “table of contents” for your RAG database.

The big triple-quoted strings in `realitas_lore.py` are the actual “pages.”

If you change the pages but keep the same table of contents, you usually do not need to edit `create_lore_entries()`.

If you change what the table of contents should contain, you do need to edit `create_lore_entries()`.

## You do NOT need to edit `create_lore_entries()` when

You are only rewriting, expanding, or clarifying text inside an existing lore block that is already referenced by an entry.

You are adding more bullets or examples inside an existing block, and you are not changing the variable name.

You are keeping any required formatting patterns that code expects (for example, keeping `**City Name**` lines in `CITIES`, or keeping a clear `TIME PERIOD: ..., YYYY-YYYY` line in `TEMPORAL`).

## You DO need to edit `create_lore_entries()` when

You create a new lore string and you want it to be retrievable as a separate RAG document. If a string is never referenced in `create_lore_entries()`, it will never become a stored RAG document.

You rename or delete a lore string that `create_lore_entries()` currently references. In that case the old entry will point to nothing, and the content will not be generated correctly.

You want to change a document’s metadata, because metadata lives in `create_lore_entries()`. This includes the document’s `title`, `category`, `tags`, and `importance`.

You want to split one big lore document into multiple smaller documents (or merge multiple docs into one). That is a table-of-contents change, so it must be done in `create_lore_entries()`.

You want a new “whitelist-style” document (like explicit goal libraries or explicit faction libraries). Those usually require:

- a new entry in `create_lore_entries()`
- a stable list format in the content
- sometimes new parsing/validation logic in code

## A practical decision test

Ask yourself: “Is the thing I changed still inside the same document as before?” If yes, you probably do not need to change `create_lore_entries()`.

Ask yourself: “Would I want the AI to retrieve this as a separate chunk?” If yes, you probably need to add a new entry in `create_lore_entries()`.

Ask yourself: “Did I create a new variable that is not referenced anywhere?” If yes, you must add it to `create_lore_entries()` or it will not exist in the RAG database.

## Examples

If you add three new medieval customs to the `CULTURE` text, you do not need to edit `create_lore_entries()`.

If you add a new document called `CULTURE_FOOD_AND_FEASTS` and you want the AI to retrieve it specifically when it needs food-related details, you do need to add a new `entries.append({...})` for it in `create_lore_entries()`.

If you decide that “Major Cities” should be separated into three documents (East, Central, West), you need to edit `create_lore_entries()` to create three docs instead of one.

---

# RAG Content Formatting Rules (so you don’t break the system)

This section explains what formatting is “allowed” and what formatting is “dangerous.” The RAG system can store any text, but some parts of your code also *parse* specific patterns out of that text. If you break those patterns, the simulation can lose features like year-range detection, allowed-city filtering, and whitelist selection.

## General rule

You can write anything you want as normal prose, headings, and bullet points. The system will still embed it.

However, when a category is used as a **structured source** (a whitelist, or something code parses with regex), you must keep the structure stable.

## Safe formatting you can always use

These are safe across basically all categories:

- Plain paragraphs
- Section headings like `**HEADING**` or `# Heading` or `## Heading`
- Bullet lists starting with `-` or `•`
- Short example blocks

If you stay within those patterns, you almost never break anything.

## Format-sensitive patterns you must preserve

### 1) `TEMPORAL` year range detection

Your code looks for a year range using a pattern like:

```text
TIME PERIOD: Anything here, 1230-1250
```

To keep it working:

- Keep the words `TIME PERIOD:`
- Keep two 4-digit years
- Keep a hyphen between them (`-` or `–`)

You can add as much text as you want above or below this line.

### 2) `CITIES` allowed-city extraction

Parts of the system extract allowed city names by looking for lines like:

```text
**Prague**
**Vienna**
**Venice**
```

To keep it working:

- Put the city name by itself on a line
- Wrap it in double asterisks exactly like `**City Name**`

You can still add bullets and descriptions below each city.

### 3) `UA_GENERATION` age range parsing

The CreatorAgent can parse the UA age range from the UA generation guidelines using a line like:

```text
AGE RANGE: 18-55
```

To keep it working:

- Keep the words `AGE RANGE:`
- Keep two integers with a hyphen between them

You can add extra words after it (like “years old”), but the cleanest format is exactly `AGE RANGE: 18-55`.

### 4) Explicit whitelists (Goals and Factions)

Some parts of the system treat certain docs like a list the model must select from.

The safest whitelist format is one item per bullet line:

```text
- Goal 1 text
- Goal 2 text
- Goal 3 text
```

For factions, it helps to also include a clean bullet list of just the names somewhere:

```text
- Ashwood Abbey
- The Long Night
- ...
```

You can still include prose descriptions, but keep a clean list present if you want reliable selection.

## Common ways people accidentally break things

### Problem: turning lists into paragraphs

If you take a whitelist category and turn it into a long paragraph, the model has a harder time selecting items consistently, and any extraction logic that expects bullet lines becomes weaker.

### Problem: hiding the key line

If you remove the `TIME PERIOD:` line or change it so it no longer contains two 4-digit years, the year-range system cannot detect the range.

If you remove the `**City Name**` pattern, the system may stop treating cities as an allowed list.

### Problem: adding extra data into structured fields

Avoid embedding extra data into fields that are meant to be simple labels.

For example, do not put the year inside the city name like `Prague, 1324`. The system expects location strings to be just the location.

## Quick editing checklist

Before you rebuild:

- Did I keep `TIME PERIOD: ..., YYYY-YYYY` intact?
- Did I keep major cities formatted as `**City Name**` lines?
- Did I keep any whitelist documents as one-item-per-bullet?
- Did I keep `AGE RANGE: X-Y` intact if I want the code to enforce UA age?

If all answers are yes, your formatting is almost certainly safe.
