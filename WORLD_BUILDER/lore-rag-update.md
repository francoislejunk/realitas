---
description: Edit lore + regenerate RAG (Realitas Neo)
---

# Goal
Keep `WORLD_BUILDER/realitas_lore.py` and the worldbuilding RAG database in sync, while making edits safely (especially to `create_lore_entries()`), and provide a repeatable “ask Cascade” template.

# Files involved
- `WORLD_BUILDER/realitas_lore.py`
- `WORLD_BUILDER/worldbuilding_rag.py`
- RAG DB output directory: `simulation_data/worldbuilding_rag/`
  - Notably: `simulation_data/worldbuilding_rag/worldbuilding/worldbuilding_database.json`

# Safety rules (do these every time)
- Do **NOT** edit large unrelated blocks of lore content when you only intend to change metadata.
- Prefer **small, targeted edits** to avoid accidentally breaking `create_lore_entries()` dict blocks.
- After any edit to `create_lore_entries()`, ensure every `entries.append({ ... })` has:
  - matching `{}` braces
  - matching `()` parentheses
  - a trailing `})`
  - no duplicated keys inside a dict (e.g., two `"tags"` keys)

# Step-by-step workflow

## 1) Decide what kind of change you’re making
Choose one:
- **A. Era/time period change** (e.g., medieval -> modern)
- **B. Lore content change** (changing the big string blocks like `SETTING_*`, factions, etc.)
- **C. Metadata change** (titles/tags/categories/importance in `create_lore_entries()`)
- **D. Entry set change** (adding/removing/reordering entries in `create_lore_entries()`)

## 2A) Era/time period change (recommended approach)
1. In `WORLD_BUILDER/realitas_lore.py`, update:
   - `TIME_PERIOD_START_YEAR`
   - `TIME_PERIOD_END_YEAR`
   - `TIME_PERIOD` string
2. Update the **era profile** variables near the `TIME_PERIOD` config (if present):
   - `SETTING_ERA_LABEL`
   - `SETTING_ERA_SLUG`
   - `SETTING_ERA_EXTRA_TAGS`
   - `SETTING_MAJOR_CONFLICT_SLUG`
3. Confirm key `create_lore_entries()` items use helper functions (if present):
   - `_era_title(...)`
   - `_setting_tags(...)`

## 2B) Lore content change
1. Edit only the relevant content section(s), e.g. `SETTING_TIME_PERIOD`, `UA_GENERATION`, `MNUA_GENERATION`, etc.
2. Do **not** change the JSON/dict structure in `create_lore_entries()` unless you mean to.

## 2C) Metadata change (titles/tags/categories/importance)
1. Find the relevant entry inside `create_lore_entries()`.
2. Make minimal edits:
   - `title` (string)
   - `tags` (list of strings)
   - `category` (must be a valid `WorldbuildingCategory`)
   - `importance` (int)
3. Keep tags consistent:
   - use snake_case where possible
   - avoid embedding “example year” tags unless they’re intended to be stable

### 2C.1) Metadata across ALL entries (recommended conventions)
When you say “adapt all the entries”, treat metadata as a system:

- **Title convention (recommended)**
  - Use a predictable prefix for the era when appropriate:
    - `_era_title("Timeline")` → `"Dark Medieval Timeline"` / `"Modern Timeline"`
  - Keep titles human-readable; titles are for retrieval/display, not strictly for parsing.

- **Tag convention (recommended)**
  - Keep tags short, stable, and snake_case.
  - Prefer **category/role tags** over volatile story details.
  - Recommended baseline tags for most entries:
    - era tags via `_setting_tags(...)` (if present in the code)
    - plus 2-8 “what is this?” tags (e.g., `"cities"`, `"hazards"`, `"occupations"`, `"dialogue"`).

- **Category convention**
  - Categories should be stable. Only change category if:
    - you changed the meaning of the entry
    - you changed which subsystem should retrieve it

- **Importance convention**
  - 10: must-have grounding/system rules
  - 8-9: strong guidance used frequently
  - 6-7: situational or secondary
  - <=5: nice-to-have flavor

### 2C.2) Using helper functions (when present)
If `realitas_lore.py` contains helpers like these:
- `_era_title(...)`
- `_setting_tags(...)`

Prefer them for *every* entry where the era should be reflected (not just setting entries).

## 2D) Entry set change (adding/removing/reordering entries)
1. Add or remove exactly one `entries.append({ ... })` block at a time.
2. Ensure:
   - The dict has required keys: `title`, `content`, `category`.
   - Optional keys: `tags`, `importance`, `subcategory`, `related_docs`.
3. Avoid duplicate `title` values (it hurts retrieval and debugging).
4. After adding/removing entries, rebuild the DB (step 3).

# 3) Regenerate the RAG database (required)
When `realitas_lore.py` changes, regenerate the DB by running `realitas_lore.py`.

## Default behavior
- Running `python WORLD_BUILDER/realitas_lore.py` will:
  - clear existing lore (unless `--add` is used)
  - re-add all docs
  - write updated DB into the storage directory

## Storage directory override (optional)
If needed, set:
- `REALITAS_RAG_STORAGE_DIR`

# 4) Verify the change
Pick at least one verification path:
- Confirm the DB file timestamp updated: `simulation_data/worldbuilding_rag/worldbuilding/worldbuilding_database.json`
- Do a quick in-game spot check:
  - Generate a UA and verify relevant lore is reflected.
  - If you changed endowments/whitelists, verify the UA/MNUA sheet outputs match expectations.
- (Optional) Add a temporary debug print in the code path that retrieves from RAG.

# 5) “Ask Cascade” template (copy/paste)
Use this message when you want Cascade to update lore generation safely:

```
Task: Update Realitas Neo lore generation + RAG.

What changed in the setting:
- Era/time period: <e.g., Modern 2015-2025>
- Core tone keywords: <comma-separated>
- Major conflict slug/name: <e.g., cold_war, street_wars>

What I want updated:
- Update `WORLD_BUILDER/realitas_lore.py` so `create_lore_entries()` titles/tags automatically match the new era.
- Apply the same metadata logic across ALL entries that should be era-aware (not just the setting section).
- Keep lore content intact unless explicitly requested.
- After changes, tell me exactly how to rebuild the RAG DB and what file(s) should change.

Constraints:
- Do not make broad rewrites.
- Make small patches.
- Ensure the file remains syntactically valid.

Files:
- `WORLD_BUILDER/realitas_lore.py`
```

# Troubleshooting
- If you see old lore in-game after edits:
  - You probably didn’t rebuild the DB (step 3)
  - Or the runtime is reading a different `REALITAS_RAG_STORAGE_DIR`
- If you get Python syntax errors:
  - Inspect the last edited `entries.append({ ... })` block for missing `})`
  - Check for stray dict lines outside an `entries.append(...)`
