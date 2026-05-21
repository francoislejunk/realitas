# Age & Location Implementation

## Summary
Added **Age** and **Location** as new fields to actor creation and actor sheets for both User Actors (UA) and Non-User Actors (NUA).

## Changes Made

### 1. ActorSheet Core (actor_sheet.py)

**Added Parameters:**
```python
def __init__(self, ..., age: Optional[int] = None, location: Optional[str] = None):
    self.age = age if age is not None else 30  # Default age
    self.location = location if location is not None else "Unknown"  # Default location
```

**Display Integration:**
- Added age and location display in `display_detailed()` method
- Shows as: `🎂 Age: 35 • 📍 Location: New York`
- Positioned right after name and occupation in the actor sheet header

### 2. User Actor Generation (creator_agent.py)

**Updated Prompt:**
```
**Requirements:**
- Name: A distinctive character name
- Age: Character's age (18-70 years old, appropriate for their background)
- Location: Geographic location (e.g., New York, Manila, Beijing, Los Angeles, Tokyo, London)
- Occupation: Their profession, role, or background
...
```

**JSON Example:**
```json
{
    "name": "Character Name",
    "age": 35,
    "location": "New York",
    "occupation": "Character Background",
    ...
}
```

**ActorSheet Creation:**
```python
ua_sheet = ActorSheet(
    ...
    age=ua_data.get('age', 30),
    location=ua_data.get('location', 'Unknown')
)
```

### 3. NUA Generation (creator_agent.py)

**Dynamic NUA Generation:**
- Updated `generate_nua()` prompt with age and location requirements
- Added to JSON example structure
- Integrated into `_build_nua_from_data()` ActorSheet creation

**Main NUA Generation:**
- Updated `_generate_nua_profile()` prompt with age and location
- Added to JSON example structure
- Integrated into main `generate_nua()` ActorSheet creation

**INUA Generation:**
- Added age (optional, can be None) and location to INUA creation
- INUAs may not have meaningful ages (e.g., a door doesn't have an age)

### 4. Example Locations

**Geographic Diversity:**
- New York (USA)
- Manila (Philippines)
- Beijing (China)
- Los Angeles (USA)
- Tokyo (Japan)
- London (UK)
- Any other real-world city appropriate to the 1990s setting

### 5. Age Guidelines

**Age Range:** 18-70 years old
- Should be appropriate for the character's occupation and background
- Young Adult (18-25): Students, entry-level workers
- Adult (26-45): Professionals, established workers
- Middle-Aged (46-60): Experienced professionals, managers
- Senior (61-70): Retired or senior positions

## Display Format

**Actor Sheet Header:**
```
┌─────────────────────────────────────────────────────────┐
│ 🎭 Vincent Cross        │ 💼 Private Investigator         │
│ 🎂 Age: 42 • 📍 Location: New York                       │
│ ═══════════════════════════════════════════════════════ │
│ 🧠 Cynical (Internal) • 🎯 Determined (External)         │
...
```

## Benefits

1. **Character Depth:** Age adds realism and context to character backgrounds
2. **Geographic Context:** Location grounds characters in the world setting
3. **Narrative Consistency:** Helps maintain consistent character details
4. **World Building:** Supports the 1990s Earth setting with real locations
5. **Relationship Context:** Age and location can inform character interactions

## Default Values

- **Age:** 30 (if not specified)
- **Location:** "Unknown" (if not specified)

These defaults ensure backward compatibility with existing code that doesn't provide these fields.

## Integration Points

All actor creation paths now include age and location:
1. User Actor generation via `generate_user_actor()`
2. NUA generation via `generate_nua()`
3. Dynamic NUA creation via `generate_nua(context, scene_description)`
4. INUA generation via `generate_inua()`

## Notes

- Age and location are now part of the core actor identity
- LLM prompts guide appropriate age selection based on occupation
- Location should be geographically accurate within the 1990s world setting
- These fields appear prominently in the actor sheet display
- Both fields are stored persistently with the actor data
