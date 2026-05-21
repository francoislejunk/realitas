# Actor Sheet Year Display Feature

## Overview

The actor sheet now displays the current simulation year next to the location, creating a more immersive sense of time and place.

**Example Display:**
```
📍 Location: Berlin 1999
```

## Implementation

### 1. Class-Level Year Variable

Added a class-level `current_year` variable to `ActorSheet`:

```python
class ActorSheet:
    current_year: int = 1999  # Default year for the simulation
```

### 2. Updated Display Method

Modified `display_detailed()` to show year alongside location:

**Before:**
```python
print(f"📍 Location: {self.location}")
```

**After:**
```python
print(f"📍 Location: {self.location} {self.current_year}")
```

### 3. Global Year Setting Method

Added a class method to set the year globally for all actors:

```python
@classmethod
def set_simulation_year(cls, year: int):
    """Set the current simulation year globally for all actor sheets."""
    cls.current_year = year
```

## Usage

### Automatic Year Extraction from RAG

The year is **automatically extracted from the RAG worldbuilding system** during initialization. No manual configuration needed!

The system:
1. Loads worldbuilding from `WORLD_BUILDER/universal_lore.py`
2. Searches for "CURRENT YEAR: XXXX" in temporal documents
3. Automatically sets the year for all actor sheets

**In `redesigned_main.py`:**
```python
# Extract and set simulation year from RAG worldbuilding
from worldbuilding_helpers import extract_current_year_from_rag
from actor_sheet import ActorSheet

current_year = extract_current_year_from_rag(rag_system)
if current_year:
    ActorSheet.set_simulation_year(current_year)
    print(f"✓ Simulation year set to {current_year} from worldbuilding context")
else:
    ActorSheet.set_simulation_year(1999)  # Fallback default
```

### Changing the Year

To change the simulation year, edit `WORLD_BUILDER/universal_lore.py`:

```python
{
    "title": "Current Year and Timeline",
    "content": """CURRENT YEAR: 1972  # <-- Change this!

It's 1972, the height of the Cold War...
    """,
    "category": WorldbuildingCategory.TEMPORAL,
    "tags": ["1972", "current_year", "history"],
    "importance": 10
}
```

Then reload the lore:
```bash
python WORLD_BUILDER/universal_lore.py
```

### Manual Override (Optional)

You can still manually set the year if needed:

```python
from actor_sheet import ActorSheet
ActorSheet.set_simulation_year(1972)  # Manual override
```

### Changing Year Mid-Simulation

If your simulation spans multiple years, you can update it dynamically:

```python
# Advance to next year
ActorSheet.set_simulation_year(2000)
```

## Examples

### Berlin 1972
```python
ActorSheet.set_simulation_year(1972)
actor.sheet.location = "Berlin"
# Display shows: 📍 Location: Berlin 1972
```

### New York 1999
```python
ActorSheet.set_simulation_year(1999)
actor.sheet.location = "New York"
# Display shows: 📍 Location: New York 1999
```

### Tokyo 2045
```python
ActorSheet.set_simulation_year(2045)
actor.sheet.location = "Tokyo"
# Display shows: 📍 Location: Tokyo 2045
```

## Benefits

1. **Immersion** - Reinforces the time period setting
2. **Context** - Players immediately see when the story takes place
3. **Consistency** - All actor sheets show the same year
4. **Flexibility** - Easy to change for different campaigns or time jumps

## Technical Details

- **Type**: Class variable (shared across all instances)
- **Default**: 1999 (matches current worldbuilding context)
- **Scope**: Global to all `ActorSheet` instances
- **Thread-safe**: Yes (single-threaded simulation)

## Worldbuilding Integration

The default year (1999) aligns with the current worldbuilding context:

```
Time Period: Mid-to-late 1990s (1995-1999)
Technology Level: Pre-smartphone, early internet era
Cultural Vibe: Grunge, alternative rock, early hip-hop
```

To change the setting period, update both:
1. The worldbuilding RAG documents
2. The `ActorSheet.current_year` value
