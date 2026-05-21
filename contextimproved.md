# Context & World/Map Improvements (contextimproved)

This document summarizes the new features added during the recent “context system + universal pygame map” improvements, along with the purpose of each change.

---

## 1) Everlasting Context (Debuggable long-term continuity)

### Feature
- An “everlasting context” pipeline that can retrieve:
  - **Recent world events** (e.g., actor added, location changes)
  - **Recalled long-term memories** relevant to the current moment

### Purpose
- Prevent “blank continuity” problems by ensuring the narrative system can always access:
  - what just happened in the world
  - what the system already knows (memories, details)

### User-facing tooling
- **`/everlasting`** / **`/ever`**
  - Prints the current assembled everlasting context text.
- **`/ctxstats`** / **`/everstats`**
  - Prints counts and a short list of recent events/memory recall.

---

## 1.1) ContextStore (SQLite persistence layer)

### Feature
`ContextStore` is a SQLite-backed “authoritative log” used to persist:

- **World events** (append-only log rows)
- **Actor long-term memory items** (decay + pinned)
- **Position snapshots** (latest-known position per entity in a location)

The DB lives at:

- `simulation_data/context/context.db`

SQLite is configured for safe concurrent usage:

- `PRAGMA journal_mode=WAL`
- `PRAGMA synchronous=NORMAL`

### Schema (tables)

#### `world_events`
Used for “what happened” logging.

- **Keys/identity**
  - `event_id` (autoincrement primary key)
  - `session_id` (required)
  - `location_id` (optional)
- **Event description**
  - `event_type` (string)
  - `summary` (string)
  - `importance` (int)
  - `tags_json` (JSON list)
  - `payload_json` (JSON object)
- **World-time indexing**
  - `world_day`, `world_hour`, `world_minute`
  - `world_minutes_since_start`

Index:

- `idx_world_events_lookup(session_id, location_id, world_minutes_since_start, created_at)`

#### `actor_memory_items`
Used for long-term memory that can be recalled later.

- **Keys/identity**
  - `memory_id` (autoincrement primary key)
  - `session_id`, `actor_id` (required)
- **Memory content**
  - `memory_type` (string)
  - `content` (string)
  - `source_event_id` (optional FK-ish pointer to `world_events.event_id`)
  - `importance` (int)
  - `pinned` (0/1)
- **Decay model**
  - `initial_strength` (float)
  - `decay_rate` (float)
  - `world_minutes_first_seen`
  - `world_minutes_last_recalled`

Index:

- `idx_actor_memory_lookup(session_id, actor_id, memory_type, importance)`

#### `position_snapshots`
Used for “where everyone/thing is” persistence.

- **Keys/identity**
  - `snapshot_id` (autoincrement primary key)
  - `session_id`, `location_id`, `entity_id`
- **Spatial data**
  - `x`, `y`, `facing_direction`, `zone_id`, `is_active`
  - `entity_name`, `entity_type`
- **World-time indexing**
  - `world_day`, `world_hour`, `world_minute`, `world_minutes_since_start`

Index:

- `idx_position_snapshots_lookup(session_id, location_id, entity_id, created_at)`

### Event logging behavior (dedupe + noise reduction)

When `log_world_event()` is called, it applies multiple best-effort filters to reduce spam:

- **INFO_LEARNED normalized-summary de-dupe** in a short time window
- **Time-window de-dupe** for noisy event types (examples):
  - `CLUE_DETECTED`
  - `SITUATION_ACTIVE`
  - `INVENTORY_UPDATED`
- **Consecutive identical event de-dupe** (same summary + tags + payload)

### Auto memory seeding from world events

After inserting into `world_events`, `ContextStore.log_world_event()` can automatically create memories via `remember()`.

- High-signal event types auto-seed by default (examples):
  - `INFO_LEARNED`
  - `DETAIL_ESTABLISHED`
  - `STATUS_CHANGED`
  - `ITEM_GAINED` / `ITEM_LOST`
  - `SITUATION_ACTIVE`
- Opt-outs/controls via payload flags:
  - `disable_auto_memory_seed: true`
  - `force_auto_memory_seed: true` (for certain types)
  - `pinned_memory: true`
  - `decay_rate: <float>`
  - `actor_ids: [ ... ]` (critical: which actors receive seeded memory)

### Memory recall model

`recall()` returns memories ranked by:

- pinned first
- then importance
- then a calculated “effective strength”

Effective strength decays exponentially:

- `effective_strength = initial_strength * exp(-decay_rate * dt_minutes)`
- pinned memories are always treated as strength 1.0

It also updates `world_minutes_last_recalled` for returned items.

---

## 1.2) How session/location/actor identity is resolved

### Session ID
The system attempts to use the active session’s `session_id`.

- The spatial context manager (`SpatialContextManager`) stores `self.session_id`.
- `ExtendedWorldStateManager.get_everlasting_context()` attempts to discover the current spatial manager and reuse its `session_id`.

### Location ID
Location scoping is primarily done using `SpatialContextManager.current_location`.

- Most event logging in spatial uses `location_id=self.current_location`.
- Everlasting context retrieval can be filtered to the current location.

### Actor ID
We attempt to use **stable actor IDs from the spatial system** when possible.

- `world_persistence_system._wps_try_resolve_actor_id(name)` attempts to map actor names to spatial IDs.
- `ExtendedWorldStateManager.get_everlasting_context()` gathers actor IDs from:
  - UA actor id in spatial context (if available)
  - present NPC names (best-effort mapped)

This lets the DB store/retrieve memory per actual actor instead of just by name.

---

## 1.3) Everlasting context assembly (how /everlasting is built)

### Source
`ExtendedWorldStateManager.get_everlasting_context()` is side-effect-free and constructs a dict containing:

- `everlasting_recent_world_events`: results of `ContextStore.get_recent_world_events(...)`
- `everlasting_recalled_memories`: per-actor results of `ContextStore.recall(...)`
- `everlasting_context_text`: a markdown-like concatenation of both sections

### Time window
Recent events can be filtered by “max age minutes”:

- `min_world_minutes_since_start = now - max_age_minutes`

### Output contract
The output is designed to be injected into scene context for LLM prompts and/or shown via `/everlasting`.

---

## 1.4) ContextStore producers (who writes what)

This table lists the main subsystems that write to `ContextStore` and the kinds of records they produce.

Notes:

- Many producers include `actor_ids` in the event payload. This is important because it enables automatic memory seeding and per-actor recall.
- Most producers try to best-effort resolve `actor_id` via the spatial context manager (so IDs are stable even when names repeat).

| Producer (file/module) | What it writes | Event types (examples) | Purpose | Key payload fields (typical) |
|---|---|---|---|---|
| `spatial_context_system.py` (`SpatialContextManager._log_world_event`) | World events + (optional) seeded memories + position snapshots | `SCENE_TRANSITION`, `ZONE_ADDED`, `OBSTACLE_ADDED`, `ACTOR_ADDED`, `ZONE_ENTERED`, `ZONE_EXITED`, `ACTOR_MOVED` | Make spatial state “authoritative” and replayable; provide context for everlasting system | `actor_ids`, `actor_name(s)`, `zone_name`, `obstacle_name`, `x/y`, `distance`, `from_zone/to_zone` |
| `world_persistence_system.py` (`_wps_log_world_event`) | World events + seeded memories | `AFTERMATH_CREATED`, `AFTERMATH_RESOLVED`, `SITUATION_ACTIVE`, `RUMOR_CREATED`, `FACTION_REPUTATION_CHANGED`, `OBLIGATION_CREATED`, `INFO_LEARNED` | Persist off-screen world state changes (rumors, schedules, aftermath, reputation) into everlasting context | `actor_ids`, `actor_names`, plus per-system fields like `faction`, `rep_delta`, `obligation`, `rumor`, `location` |
| `narrative_context_system.py` (`add_concrete_detail`) | World events + pinned memories | `DETAIL_ESTABLISHED` | Lock in “concrete details” that must remain consistent across future narration | `detail_category`, `detail_text`, `keywords`, `scene_id`, `actor_ids` |
| `inventory_manager.py` (`_log_inventory_event`) | World events + memories | `ITEM_GAINED`, `ITEM_LOST`, `INVENTORY_UPDATED` | Persist inventory changes from intent parsing and inventory operations | `change_type`, `item_name`, `item_description`, `actor_ids` |
| `enhanced_monetary_system.py` | World events + memories | `INVENTORY_UPDATED` | Persist inventory gain/loss produced by monetary/transaction flow | `transaction_type`, `amount`, `item_name`, `supplement_bonus`, `change_type`, `actor_ids` |
| `progression_tracker.py` | World events + memories | `SYMPATHY_SHIFT` | Persist relationship/sympathy changes and seed recallable memories | `actor_ids`, `actor_names`, `delta`, `reason` |
| `enhanced_sympathy_system.py` | World events + memories | `SYMPATHY_SHIFT` | Same goal as above but for the enhanced sympathy pipeline | `actor_ids`, `actor_names`, `delta`, `reason` |
| `skill_revelation_system.py` | World events + memories | `INFO_LEARNED` | Persist “skill reveal” observations (UA noticing abilities/skills) | `observer_id`, `target_actor_name`, `kind`, `ability_name`, `ability_level`, `actor_ids` |
| `progressive_discovery_system.py` | World events + memories | `CLUE_DETECTED`, `INFO_LEARNED` | Persist clues and “lead uncovered” milestones | `clue_type`, `implies`, `keyword`, `context`, `actor_ids` |
| `intent_based_memory_creation.py` | World events + memories | various “memory creation” event types (implementation-specific) | Persist explicit memory creation/resurfacing outcomes into the everlasting store | `memory_type`, `title`, `desc`, `internal_voice`, `actor_ids` |
| `exchange_system.py` | World events + memories | `STATUS_SHIFT`, `DEATH` | Persist high-signal exchange outcomes (status shifts, death) | `status_shifts`, `winner`, `dead`, `proactor_id`, `reactor_id`, `actor_ids` |
| `actors.py` (identity updates) | World events + memories | `INFO_LEARNED` | Persist identity updates / revealed details as “learned info” | `actor_id`, `actor_ids`, `old_name`, `new_name` |
| `actor_sheet.py` (status changes) | World events + memories | `STATUS_CHANGED` | Persist UA/NPC status deltas with reason text | `status_type`, `old_value`, `new_value`, `change`, `reason`, `actor_ids` |
| `agents/decider_agent.py` (read-only) | Reads recent events (doesn’t write) | N/A | Uses `get_recent_world_events()` to inform NUA decisions | N/A |

If you want, we can further refine this table into:

- **Confirmed event types** (from grep + code inspection)
- **Payload schema** per event type
- **Which events auto-seed memories** and which are intentionally “log-only”

---

## 2) “Non-turn” command behavior (no time, no BG sim)

### Feature
- Commands that are UI/debug should not behave like in-world actions.
- We established “strict non-turn” behavior:
  - **No time advancement**
  - **No background simulation tick** (no NPCs acting)
  - **No world-event simulation**
  - **No LLM inquiry/action classification**

### Purpose
- Keep commands like maps, UI, or debugging from changing the simulation state.

### Implemented
- **`/ctxstats`** and **`/everlasting`** are strict non-turn.
- **`worldmap`** and related commands are strict non-turn, matching `/pmap` behavior.

---

## 3) Universal Pygame Map (single window, multiple modes)

### Feature
- A single pygame map window that can toggle between:
  - **LOCAL**: current spatial location map (rooms/zones/obstacles/actors)
  - **WORLD**: global travel graph (locations as nodes, routes as edges)

### Purpose
- One “authoritative” map UI instead of multiple map UIs.
- Supports both micro (room-scale) and macro (world-scale) navigation.

### Controls
- **`TAB`** toggles **LOCAL/WORLD**.

---

## 4) WORLD map graph rendering (with unknown placeholders)

### Feature
- WORLD mode shows:
  - Known locations from the world graph
  - Known routes between locations
  - **Unknown placeholder nodes** to visually scaffold early-game navigation

### Purpose
- The WORLD map stays useful even when only a few locations are discovered.

### Interaction
- Click a node to select.
- Selected node is highlighted.

---

## 5) WORLD map layout improvements (force-directed “real map” feel)

### Feature
- Replaced the early simple radial/cross layout with a deterministic **force-directed (spring) layout** for known nodes.
- Unknown placeholders are placed around the perimeter to avoid the “plus sign” artifact.

### Purpose
- Make the world graph look like an organic “world map” graph rather than a rigid cross.

---

## 6) Click-to-travel (WORLD → Journey system integration)

### Feature
- In WORLD mode:
  - Click a **known** node
  - Press **ENTER** to confirm travel
  - Emits a `travel_request` event to the main simulation loop

### Purpose
- Makes travel a first-class UI action.
- Uses existing travel systems rather than teleporting.

### Behavior
- If travel time is very short: immediate move.
- Otherwise: starts the existing **chunked travel** journey.

---

## 7) Windows console input unblocking (pygame actions while prompt waits)

### Problem
- On Windows, the sim was blocked waiting for console input, preventing pygame-originated actions (like WORLD travel confirm) from being processed.

### Feature
- While the prompt waits for input, the Windows input reader polls the pygame outbox.
- If a travel request arrives, it is handled immediately (without requiring the user to type in the terminal).

### Purpose
- Makes pygame UI interactions responsive and reliable.

---

## 8) Key handling improvement (Keypad ENTER)

### Feature
- WORLD confirmation accepts both:
  - `ENTER`
  - `Keypad ENTER`

### Purpose
- Fix “ENTER doesn’t work” reports caused by different keyboards / keypad usage.

---

## 9) Background simulation consistency when a NUA departs

### Problem
- A NUA could “leave the location” but other systems (initiative/turn order/background sim) could still try to generate actions for them, causing contradictions and retry spam.

### Feature
- Background sim now skips any actor not present in the active `available_nuas` list even if they still appear in stored turn order.
- Turn order pruning was added where applicable to remove departed actors.

### Purpose
- Keep systems consistent:
  - if an actor has departed, they should not continue to act in roam/exchange contexts.

---

## 10) Route/command routing toward the pygame map

### Feature
- World map commands are routed to pygame (WORLD mode) rather than textual “world map” output.

### Purpose
- Establish pygame as the universal map UI.

---

## Notes / Known follow-ups

- Some map-related command routing and departure consistency can still be tightened further (e.g., centralizing “remove departed actor everywhere by stable ID” across roam and exchange subsystems).
- The WORLD map is a graph visualization (nodes/edges). True geographic styling (district clustering, persistent coordinates, region grouping) can be added later.
