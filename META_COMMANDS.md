# Meta Commands for UTAS Simulation

Meta commands are special commands that don't advance time or trigger normal action processing. They're useful for testing, debugging, and quick information access.

## Available Meta Commands

### Information Commands

- **`ua` / `sheet`** - Display your character sheet
- **`npc` / `npcs` / `people` / `who`** - List all NPCs in the current area
- **`look` / `l` / `examine scene` / `scan`** - Display full scene description
- **`map` / `show map` / `view map`** - Show spatial map
- **`compact map` / `small map` / `mini map`** - Show compact spatial map

### Testing Commands

- **`/spawn [description]`** - Spawn a new NUA for testing
  - **Usage:** `/spawn` - Creates a random NUA appropriate for the scene
  - **Usage:** `/spawn a nervous bartender` - Creates a specific NUA based on description
  - **Purpose:** Quick NUA creation for testing interactions without natural language
  - **Features:**
    - Automatically adds NUA to available NPCs list
    - Initializes sympathy relationship
    - Adds to actor manager and context systems
    - Displays NPC summary after creation

### System Commands

- **`quit` / `exit` / `q`** - Exit the simulation (saves progress)

## Implementation Details

### Slash Commands
All commands starting with `/` are treated as meta commands and:
- Skip intent availability checks
- Don't advance simulation time
- Don't trigger normal action processing
- Bypass manifestation prevention systems

### Testing Workflow

**Quick NPC Testing:**
```
> /spawn
🧪 TEST MODE: Spawning NUA...
✓ Spawned NUA: Marcus Chen (Security Guard)
[NPC summary displayed]

> I talk to Marcus
[Normal interaction proceeds]
```

**Specific NPC Testing:**
```
> /spawn a grumpy mechanic with a wrench
🧪 TEST MODE: Spawning NUA...
✓ Spawned NUA: Tony Russo (Mechanic)
[NPC summary displayed]

> I ask Tony about fixing my car
[Normal interaction proceeds]
```

## Benefits

1. **Faster Testing** - No need to phrase natural language for NPC creation
2. **Controlled Spawning** - Create specific NPCs on demand
3. **No Time Cost** - Meta commands don't advance simulation time
4. **Full Integration** - Spawned NPCs work exactly like naturally created ones
5. **Debug Friendly** - Error messages and stack traces for troubleshooting

## Future Meta Commands

Potential additions:
- `/despawn [name]` - Remove an NPC
- `/teleport [location]` - Jump to a location
- `/time [hours]` - Advance time
- `/save` - Manual save
- `/load` - Load saved state
- `/debug` - Toggle debug mode
