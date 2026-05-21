# Character Generation Parameters in RAG

## Overview

Added a new **CHARACTER GENERATION PARAMETERS** section to `universal_lore_restructured.py` that defines all possible values for actor sheets. This guides the LLM when creating characters to ensure consistency with the worldbuilding.

## What Was Added

### 6 New Sections:

1. **CHARACTER_NAMES** - Name types and conventions
2. **CHARACTER_AGES** - Age ranges and implications
3. **CHARACTER_SKILLS** - All possible skill types
4. **CHARACTER_SUPERS** - Exceptional abilities (no supernatural)
5. **CHARACTER_STATUS_DISTRIBUTIONS** - Status value guidelines
6. **CHARACTER_PERSONALITY_TRAITS** - Internal/external trait combinations

## Content Details

### 1. Names (CHARACTER_NAMES)
- **German/European names**: Klaus, Werner, Ingrid, Petra, etc.
- **Surnames**: Müller, Schmidt, Fischer, Weber, etc.
- **Working class**: Traditional, often shortened
- **Bureaucratic**: Formal, with middle initials
- **Age distribution guidance**

### 2. Ages (CHARACTER_AGES)
- **20-25**: Entry-level, naive, lower skills
- **26-35**: Established, peak condition, most common
- **36-50**: Experienced, cynical, higher skills
- **51+**: Rare survivors, very high skills, supervisory

### 3. Skills (CHARACTER_SKILLS)
**Physical**: Manual Labor, Precision Work, Endurance, Combat
**Technical**: Equipment Operation, Maintenance, Medical, Computing
**Social**: Bureaucracy, Negotiation, Intimidation, Empathy
**Knowledge**: Accord Law, System Knowledge, Street Smarts, History
**Specialized**: HEM Extraction, Neuro-Suppression, Biomechatronics, Psychometric Analysis

### 4. Supers (CHARACTER_SUPERS)
**NOTE**: NO supernatural powers - only exceptional human abilities

**Physical**: Strength, Speed, Endurance, Dexterity
**Mental**: Memory, Analysis, Focus, Learning
**Social**: Charisma, Intimidation, Empathy, Deception
**Technical**: Repair, Operation, Improvisation, Precision

**Rarity**: Most characters have 0-1 supers

### 5. Status (CHARACTER_STATUS_DISTRIBUTIONS)
**Stamina**: 5 (peak) → 0 (exhausted)
**Spirit**: 5 (confident) → 0 (depressed)
**Supply**: 5 (wealthy) → 0 (destitute)
**Sympathy**: +5 (loved) → -5 (hated)

**Typical starting values**:
- Stamina: 3-4 (healthy workers)
- Spirit: 2-4 (varies)
- Supply: 2-3 (working class struggles)

### 6. Personality (CHARACTER_PERSONALITY_TRAITS)
**Internal** (how they think):
- Idealistic, Cynical, Pragmatic, Resigned
- Ambitious, Fearful, Curious, Obedient

**External** (how they act):
- Assertive, Submissive, Friendly, Aloof
- Professional, Casual, Aggressive, Gentle

**Common combinations**:
- Cynical + Professional
- Idealistic + Assertive
- Resigned + Submissive
- Pragmatic + Friendly

## RAG Integration

All 6 sections are loaded into RAG with:
- **Category**: BEINGS or MECHANICS
- **Tags**: `character_generation`, specific type tags
- **Importance**: 10 (highest priority)

When the LLM generates characters, it can query:
```
"character generation names ages skills"
```

And get all the relevant parameters for creating period-appropriate, consistent characters.

## How to Update

### To Change Name Types:
Edit `CHARACTER_NAMES` section (lines 249-271)

### To Change Age Ranges:
Edit `CHARACTER_AGES` section (lines 273-296)

### To Add/Remove Skills:
Edit `CHARACTER_SKILLS` section (lines 298-330)

### To Modify Supers:
Edit `CHARACTER_SUPERS` section (lines 332-362)

### To Adjust Status Values:
Edit `CHARACTER_STATUS_DISTRIBUTIONS` section (lines 364-399)

### To Change Personality Options:
Edit `CHARACTER_PERSONALITY_TRAITS` section (lines 401-429)

### After Editing:
```bash
python WORLD_BUILDER/universal_lore_restructured.py
```

This reloads the RAG database with your changes.

## Benefits

1. **Consistency**: All characters follow the same guidelines
2. **Period-Appropriate**: Names, skills, tech match 1970s setting
3. **Easy Editing**: Change values in one place, affects all character generation
4. **LLM Guidance**: CreatorAgent queries these when making characters
5. **No Hardcoding**: Values live in worldbuilding, not in code

## Example Usage

When CreatorAgent generates a character, it queries RAG:
```python
context = rag_system.get_context_for_llm(
    query="character generation names skills personality",
    max_tokens=500
)
```

RAG returns:
- German/European names appropriate for 1970s
- Skills like "HEM Extraction", "Neuro-Suppression"
- Personality combinations like "Cynical + Professional"
- Age ranges with implications
- Status value guidelines

Result: Characters that fit the world perfectly!

## Files Modified

**`WORLD_BUILDER/universal_lore_restructured.py`**:
- Added CHARACTER GENERATION PARAMETERS section (lines 245-429)
- Added 6 character generation entries to lore loading (lines 853-900)
- Updated header documentation (line 31)

Total: **+6 lore entries, ~185 lines of character generation parameters**
