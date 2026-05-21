# RAG Quick Reference Card

## File Location
`WORLD_BUILDER/universal_lore_restructured.py`

## Basic Workflow

```
1. Edit content → 2. Save file → 3. Run file → 4. Test
```

## Common Tasks

### ✏️ Edit Existing Content
```python
# Find section
TECHNOLOGY_COMMUNICATION = """
Old content here
"""

# Change to
TECHNOLOGY_COMMUNICATION = """
New content here
"""

# Run
python universal_lore_restructured.py
```

### ➕ Add New Section

**Step 1: Create variable**
```python
MY_NEW_SECTION = """
Your content here
"""
```

**Step 2: Add to function**
```python
def create_lore_entries():
    entries = []
    
    entries.append({
        "title": "My New Section",
        "content": MY_NEW_SECTION,
        "category": WorldbuildingCategory.CULTURE,
        "tags": ["tag1", "tag2"],
        "importance": 7
    })
    
    return entries
```

**Step 3: Run**
```bash
python universal_lore_restructured.py
```

### ❌ Delete Section

**Step 1: Delete variable**
```python
# Delete or comment out
# MY_SECTION = """..."""
```

**Step 2: Delete from function**
```python
# Delete this block:
# entries.append({
#     "title": "...",
#     "content": MY_SECTION,
#     ...
# })
```

**Step 3: Run**
```bash
python universal_lore_restructured.py
```

## Available Categories

```python
WorldbuildingCategory.WORLD_STRUCTURE      # Geography, environment
WorldbuildingCategory.TEMPORAL             # History, timeline
WorldbuildingCategory.BEINGS               # Character types
WorldbuildingCategory.SUPERNATURAL         # Magic/powers
WorldbuildingCategory.CIVILIZATION         # Technology, society
WorldbuildingCategory.FACTIONS_ORGANIZATIONS  # Groups
WorldbuildingCategory.RELATIONSHIP_MATRICES   # Social dynamics
WorldbuildingCategory.CONFLICT_GENERATORS     # Tension sources
WorldbuildingCategory.CULTURE              # Customs, language
WorldbuildingCategory.NARRATION_STYLE_TONE    # Storytelling
WorldbuildingCategory.EXPANSION_SEEDS      # Future content
WorldbuildingCategory.MECHANICS            # Game integration
WorldbuildingCategory.PLACES               # Locations
WorldbuildingCategory.OCCUPATIONS          # Jobs
```

## Importance Scale

```
10 = Critical (core setting, tone)
9  = Very Important (major systems)
8  = Important (key details)
7  = Useful (supporting info)
6  = Nice to Have (flavor)
5  = Optional (minor details)
```

## Testing

```bash
# Load lore
cd WORLD_BUILDER
python universal_lore_restructured.py

# Run simulation
cd ../MAIN
python redesigned_main.py

# Check output
✓ Loaded X lore documents from universal_lore.py
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Content not showing up | Did you add to `create_lore_entries()`? |
| NameError | Check variable name spelling |
| SyntaxError | Check quotes and brackets |
| Old content still showing | Did you run the file? |

## File Structure

```
# Top: Content Variables (EDIT THESE)
SETTING_TIME_PERIOD = """..."""
LOCATIONS_URBAN = """..."""
TECHNOLOGY_COMMUNICATION = """..."""

# Bottom: Auto-Generation (ONLY EDIT WHEN ADDING NEW SECTIONS)
def create_lore_entries():
    entries = []
    entries.append({...})
    return entries
```

## Remember

✅ Edit content in variables (top of file)
✅ Add variables to function (bottom of file)  
✅ Always run file after editing
✅ Test in simulation

❌ Don't edit RAG integration code
❌ Don't forget to save
❌ Don't skip running the file
