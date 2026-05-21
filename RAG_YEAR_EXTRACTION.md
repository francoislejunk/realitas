# RAG-Based Year Extraction for Actor Sheets

## Overview

The simulation year is now **automatically extracted from the RAG worldbuilding system** instead of being hardcoded. This ensures the year displayed in actor sheets (e.g., "Berlin 1999") always matches the worldbuilding context.

## How It Works

### 1. Worldbuilding Definition

The year is defined in `WORLD_BUILDER/universal_lore.py`:

```python
{
    "title": "Current Year and Timeline",
    "content": """CURRENT YEAR: 1999

It's 1999, the final year of the 1990s...
    """,
    "category": WorldbuildingCategory.TEMPORAL,
    "tags": ["1999", "current_year", "history"],
    "importance": 10
}
```

**Key Pattern:** `CURRENT YEAR: XXXX` - This is what the extraction looks for.

### 2. Extraction Function

Created `worldbuilding_helpers.py` with `extract_current_year_from_rag()`:

```python
def extract_current_year_from_rag(rag_system: WorldbuildingRAGSystem) -> Optional[int]:
    """Extract the current year from RAG worldbuilding."""
    # Query RAG for temporal information
    context = rag_system.get_context_for_llm(
        query="current year timeline temporal date",
        max_tokens=500
    )
    
    # Look for "CURRENT YEAR: XXXX" pattern
    year_match = re.search(r'CURRENT YEAR:\s*(\d{4})', context, re.IGNORECASE)
    if year_match:
        return int(year_match.group(1))
    
    # Fallback: Find most common 4-digit year in context
    # ...
```

### 3. Automatic Initialization

In `redesigned_main.py`, after RAG system loads:

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

## Benefits

1. **Single Source of Truth** - Year defined once in worldbuilding, used everywhere
2. **Consistency** - Actor sheets always match worldbuilding context
3. **Easy Updates** - Change year in one place, affects entire simulation
4. **Automatic** - No manual configuration needed
5. **Fallback Safe** - Defaults to 1999 if extraction fails

## Changing the Year

### Method 1: Edit Configuration Variable (Recommended)

1. Open `WORLD_BUILDER/universal_lore.py`
2. Change the `CURRENT_YEAR` variable at the top:
   ```python
   # Current year for the simulation - change this to set the time period
   CURRENT_YEAR = 1972  # Change from 1999 to 1972
   ```
3. Run: `python WORLD_BUILDER/universal_lore.py`
4. Restart simulation

**That's it!** The year will automatically update in:
- All lore content (via f-string interpolation)
- RAG extraction
- Actor sheet displays

### Method 2: Manual Override

```python
from actor_sheet import ActorSheet
ActorSheet.set_simulation_year(1972)
```

## Files Modified

1. **`WORLD_BUILDER/universal_lore.py`**
   - Added "CURRENT YEAR: 1999" to temporal lore
   - Changed title to "Current Year and Timeline"
   - Added "current_year" tag
   - Increased importance to 10

2. **`worldbuilding_helpers.py`** (NEW)
   - Created `extract_current_year_from_rag()` function
   - Regex pattern matching for year extraction
   - Fallback logic for finding years

3. **`MAIN/redesigned_main.py`**
   - Removed hardcoded year setting
   - Added RAG-based year extraction after RAG initialization
   - Added success/warning messages

4. **`actor_sheet.py`**
   - Already had `current_year` class variable
   - Already had `set_simulation_year()` method
   - Display already shows year next to location

## Example Output

```
📚 Initializing Enhanced Worldbuilding RAG System...
✓ Loaded 21 lore documents from universal_lore.py
✓ Simulation year set to 1999 from worldbuilding context

📋 Lena Voss - Character Sheet
🎂 Age: 28 • 📍 Location: Berlin 1999
```

## Testing

To verify it works:

1. Check startup messages for year confirmation
2. Type `ua` or `sheet` in simulation
3. Verify location shows: `📍 Location: [City] [Year]`

## Future Enhancements

Possible improvements:
- Support for year ranges (e.g., "1995-1999")
- Automatic year advancement over time
- Multiple timeline support
- Historical event tracking
