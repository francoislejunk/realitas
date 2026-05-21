# RAG Editing Guide - How to Add, Edit, and Delete Content

## Overview

The new RAG system has two parts:
1. **Content Sections** - Where you write your worldbuilding (easy to edit)
2. **Auto-Generation Function** - Converts content to RAG entries (only edit when adding new sections)

## Quick Reference

| Task | Difficulty | Steps |
|------|-----------|-------|
| Edit existing content | ⭐ Easy | Find section, edit string, run file |
| Add content to existing section | ⭐ Easy | Add to existing string, run file |
| Delete content from section | ⭐ Easy | Remove from string, run file |
| Add new section | ⭐⭐ Medium | Create variable + add to function |
| Delete entire section | ⭐⭐ Medium | Remove variable + remove from function |
| Change categories/tags | ⭐⭐⭐ Advanced | Edit auto-generation function |

---

## Part 1: Editing Existing Content (EASY)

### **Example: Change Communication Technology**

**Step 1: Find the section**
```python
# ============================================================================
# TECHNOLOGY - Edit these to change tech level in your world
# ============================================================================

TECHNOLOGY_COMMUNICATION = """
Communication in the 1990s:

**Landline Phones:**
- Primary communication method
- Answering machines for messages
...
"""
```

**Step 2: Edit the content**
```python
TECHNOLOGY_COMMUNICATION = """
Communication in the 1990s:

**Landline Phones:**
- Primary communication method
- Answering machines for messages
- Caller ID emerging (new technology)
- Call waiting, three-way calling
- Long distance charges (expensive)
- Phone books and directory assistance (411)
- ROTARY PHONES still common in older homes  # ← ADDED THIS

**Pagers (Beepers):**
- For urgent contact
- Numeric pagers (just numbers)
- Text pagers (short messages)
...
"""
```

**Step 3: Save and run**
```bash
cd WORLD_BUILDER
python universal_lore_restructured.py
```

**Done!** The RAG system now includes rotary phones.

---

## Part 2: Adding Content to Existing Section (EASY)

### **Example: Add More Urban Locations**

**Step 1: Find the section**
```python
LOCATIONS_URBAN = """
Typical Urban Locations in 1990s Cities:

**Entertainment & Social:**
- Dive bars and nightclubs with live music
- Coffee shops and diners (pre-Starbucks era, independent shops)
- Video rental stores (Blockbuster, local shops) and record shops
- Arcade game rooms and pool halls
- Bowling alleys and movie theaters
"""
```

**Step 2: Add your content**
```python
LOCATIONS_URBAN = """
Typical Urban Locations in 1990s Cities:

**Entertainment & Social:**
- Dive bars and nightclubs with live music
- Coffee shops and diners (pre-Starbucks era, independent shops)
- Video rental stores (Blockbuster, local shops) and record shops
- Arcade game rooms and pool halls
- Bowling alleys and movie theaters
- Comic book shops and hobby stores  # ← ADDED
- Tattoo parlors and piercing studios  # ← ADDED
- Underground fight clubs  # ← ADDED

**Daily Life:**
- Laundromats and corner stores (bodegas, convenience stores)
...
"""
```

**Step 3: Save and run**
```bash
python universal_lore_restructured.py
```

**Done!** New locations added.

---

## Part 3: Deleting Content from Section (EASY)

### **Example: Remove Pagers from Technology**

**Step 1: Find the section**
```python
TECHNOLOGY_COMMUNICATION = """
Communication in the 1990s:

**Landline Phones:**
- Primary communication method
...

**Pagers (Beepers):**
- For urgent contact
- Numeric pagers (just numbers)
- Text pagers (short messages)
- Drug dealers and doctors use them
- Calling back from pay phones

**Early Cell Phones:**
- Bulky, expensive ($1000+)
...
"""
```

**Step 2: Delete the content**
```python
TECHNOLOGY_COMMUNICATION = """
Communication in the 1990s:

**Landline Phones:**
- Primary communication method
...

**Early Cell Phones:**
- Bulky, expensive ($1000+)
...
"""
```

**Step 3: Save and run**
```bash
python universal_lore_restructured.py
```

**Done!** Pagers removed from the world.

---

## Part 4: Adding a New Section (MEDIUM)

### **Example: Add "LOCATIONS_INDUSTRIAL" Section**

**Step 1: Create the content variable**

Find the LOCATIONS section and add your new variable:

```python
# ============================================================================
# LOCATIONS - Edit these to add/change places in your world
# ============================================================================

LOCATIONS_URBAN = """
Typical Urban Locations in 1990s Cities:
...
"""

LOCATIONS_SUBURBAN = """
Typical Suburban Locations in 1990s America:
...
"""

LOCATIONS_SPECIFIC = """
Key Locations in the City:
...
"""

# ← ADD YOUR NEW SECTION HERE
LOCATIONS_INDUSTRIAL = """
Industrial District Locations:

**Active Industry:**
- Manufacturing plants (textiles, electronics, auto parts)
- Shipping warehouses and distribution centers
- Food processing facilities
- Chemical plants and refineries

**Abandoned/Declining:**
- Closed factories with broken windows
- Empty warehouses (used for raves and squatting)
- Rusted machinery and equipment
- Overgrown rail yards

**Infrastructure:**
- Loading docks and freight elevators
- Industrial rail lines
- Power substations
- Water treatment facilities

**Atmosphere:**
- Smell of oil, chemicals, and rust
- Sounds of machinery, trains, and trucks
- Graffiti on walls and train cars
- Few people during off-hours
"""
```

**Step 2: Add to auto-generation function**

Scroll down to `def create_lore_entries()` and add your entry:

```python
def create_lore_entries() -> List[Dict[str, Any]]:
    """
    Automatically generate lore entries from the sections above.
    """
    
    entries = []
    
    # ... existing entries ...
    
    # LOCATIONS entries
    entries.append({
        "title": "Urban Locations - Comprehensive List",
        "content": LOCATIONS_URBAN,
        "category": WorldbuildingCategory.PLACES,
        "tags": ["urban", "city", "locations", "buildings", "1990s"],
        "importance": 9
    })
    
    entries.append({
        "title": "Suburban Locations - Comprehensive List",
        "content": LOCATIONS_SUBURBAN,
        "category": WorldbuildingCategory.PLACES,
        "tags": ["suburban", "neighborhoods", "locations", "1990s"],
        "importance": 7
    })
    
    entries.append({
        "title": "Key Locations in the City",
        "content": LOCATIONS_SPECIFIC,
        "category": WorldbuildingCategory.PLACES,
        "tags": ["locations", "venues", "geography", "connections"],
        "importance": 8
    })
    
    # ← ADD YOUR NEW ENTRY HERE
    entries.append({
        "title": "Industrial District Locations",
        "content": LOCATIONS_INDUSTRIAL,  # ← Use your variable
        "category": WorldbuildingCategory.PLACES,
        "tags": ["industrial", "factories", "warehouses", "1990s"],
        "importance": 7
    })
    
    # ... rest of entries ...
    
    return entries
```

**Step 3: Save and run**
```bash
python universal_lore_restructured.py
```

**Done!** New section added to RAG.

---

## Part 5: Deleting an Entire Section (MEDIUM)

### **Example: Remove "FACTION_MUSIC_SCENE" Section**

**Step 1: Delete the content variable**

Find and delete:
```python
# ============================================================================
# FACTIONS - Edit these to add/change groups in your world
# ============================================================================

FACTION_MUSIC_SCENE = """
The Underground Music Scene:
...
"""
```

Delete the entire variable (or comment it out with `#`).

**Step 2: Remove from auto-generation function**

Find and delete this entry:
```python
def create_lore_entries():
    entries = []
    
    # ... other entries ...
    
    # FACTIONS entries
    entries.append({
        "title": "Underground Music Scene",
        "content": FACTION_MUSIC_SCENE,  # ← DELETE THIS ENTIRE BLOCK
        "category": WorldbuildingCategory.FACTIONS_ORGANIZATIONS,
        "tags": ["music", "underground", "rave", "community", "faction"],
        "importance": 8
    })
    
    return entries
```

**Step 3: Save and run**
```bash
python universal_lore_restructured.py
```

**Done!** Section removed from RAG.

---

## Part 6: Changing Categories or Tags (ADVANCED)

### **Example: Change Category of Music Scene**

**Find the entry in auto-generation function:**
```python
entries.append({
    "title": "1990s Music Scene - Comprehensive",
    "content": CULTURE_MUSIC_SCENE,
    "category": WorldbuildingCategory.CULTURE,  # ← Current category
    "tags": ["music", "grunge", "hip-hop", "rave", "punk", "indie", "1990s"],
    "importance": 9
})
```

**Change to different category:**
```python
entries.append({
    "title": "1990s Music Scene - Comprehensive",
    "content": CULTURE_MUSIC_SCENE,
    "category": WorldbuildingCategory.FACTIONS_ORGANIZATIONS,  # ← Changed
    "tags": ["music", "grunge", "hip-hop", "rave", "punk", "indie", "1990s"],
    "importance": 9
})
```

**Available categories:**
- `WorldbuildingCategory.WORLD_STRUCTURE`
- `WorldbuildingCategory.TEMPORAL`
- `WorldbuildingCategory.BEINGS`
- `WorldbuildingCategory.SUPERNATURAL`
- `WorldbuildingCategory.CIVILIZATION`
- `WorldbuildingCategory.FACTIONS_ORGANIZATIONS`
- `WorldbuildingCategory.RELATIONSHIP_MATRICES`
- `WorldbuildingCategory.CONFLICT_GENERATORS`
- `WorldbuildingCategory.CULTURE`
- `WorldbuildingCategory.NARRATION_STYLE_TONE`
- `WorldbuildingCategory.EXPANSION_SEEDS`
- `WorldbuildingCategory.MECHANICS`
- `WorldbuildingCategory.PLACES`
- `WorldbuildingCategory.OCCUPATIONS`

---

## Complete Example: Adding "Magic System" to Fantasy Setting

Let's say you want to change from 1990s to fantasy and add magic.

### **Step 1: Change supernatural section**

```python
# ============================================================================
# CORE SETTING - Edit these to change your world's fundamentals
# ============================================================================

# OLD (1990s):
SETTING_SUPERNATURAL = """
This world has NO magic, supernatural powers, or paranormal elements.
...
"""

# NEW (Fantasy):
SETTING_SUPERNATURAL = """
Magic System - The Weave:

**How Magic Works:**
- Magic flows through ley lines in the earth
- Mages can tap into these lines to cast spells
- Requires verbal incantations and hand gestures
- Drains physical stamina based on spell power

**Types of Magic:**
- Elemental (fire, water, earth, air)
- Healing and restoration
- Illusion and enchantment
- Necromancy (forbidden in most kingdoms)

**Limitations:**
- Cannot create matter from nothing
- Cannot raise the truly dead (only recent corpses)
- Overuse causes magical exhaustion
- Some people are born without magical ability

**Social Impact:**
- Mages are respected but feared
- Magic academies train young mages
- Anti-magic factions exist
- Magical items are rare and valuable
"""
```

### **Step 2: Add magic items section**

```python
# ============================================================================
# CULTURE - Edit these to change cultural elements
# ============================================================================

# ... existing sections ...

# NEW SECTION:
CULTURE_MAGIC_ITEMS = """
Common Magical Items:

**Everyday Magic:**
- Everburning torches (never go out)
- Self-heating cooking pots
- Water purification stones
- Minor healing salves

**Rare Items:**
- Enchanted weapons (+1 to damage)
- Rings of protection
- Boots of speed
- Bags of holding

**Legendary Artifacts:**
- The Crown of Kings (grants leadership)
- The Staff of Storms (controls weather)
- The Amulet of Souls (speaks with dead)

**Availability:**
- Everyday items: Common in cities, expensive
- Rare items: Only in major cities, very expensive
- Legendary: Unique, priceless, quest objectives
"""
```

### **Step 3: Add to auto-generation**

```python
def create_lore_entries():
    entries = []
    
    # Update supernatural entry
    entries.append({
        "title": "Magic System - The Weave",  # ← Changed title
        "content": SETTING_SUPERNATURAL,
        "category": WorldbuildingCategory.SUPERNATURAL,
        "tags": ["magic", "weave", "spells", "mages"],  # ← Changed tags
        "importance": 10
    })
    
    # Add new magic items entry
    entries.append({
        "title": "Common Magical Items",
        "content": CULTURE_MAGIC_ITEMS,
        "category": WorldbuildingCategory.CULTURE,
        "tags": ["magic", "items", "artifacts", "equipment"],
        "importance": 8
    })
    
    # ... rest of entries ...
    
    return entries
```

### **Step 4: Run**

```bash
python universal_lore_restructured.py
```

**Result:** Your world now has magic instead of being grounded 1990s!

---

## Testing Your Changes

After making changes, always test:

### **1. Check the output**
```bash
python universal_lore_restructured.py
```

Look for:
```
📥 Loading X lore entries into RAG system...
✅ Successfully loaded X lore entries!
📊 Total documents in RAG: X
```

### **2. Test search**

The script automatically tests search:
```
Testing RAG system with sample search...
[Result 1] Title
Category: category_name
Relevance: 0.XXX
Content: ...
```

### **3. Run simulation**

```bash
cd ../MAIN
python redesigned_main.py
```

Check that it loads your lore:
```
📚 Initializing Enhanced Worldbuilding RAG System...
✓ Loaded X lore documents from universal_lore.py
```

### **4. Generate a scene**

Create a character and see if the scene references your new content.

---

## Common Mistakes

### **❌ Mistake 1: Forgetting to add to auto-generation**

```python
# You added this:
LOCATIONS_INDUSTRIAL = """..."""

# But forgot to add this:
entries.append({
    "title": "Industrial Locations",
    "content": LOCATIONS_INDUSTRIAL,  # ← Must add this!
    ...
})
```

**Result:** Content exists but doesn't get loaded into RAG.

### **❌ Mistake 2: Syntax errors in content**

```python
# Bad - unescaped quotes:
CONTENT = """
He said "hello" and left.  # ← This is fine in triple quotes
"""

# Bad - missing closing quotes:
CONTENT = """
Some content...
# ← Missing closing """
```

**Fix:** Use triple quotes `"""` for multi-line strings, they handle quotes automatically.

### **❌ Mistake 3: Wrong variable name**

```python
# You created:
LOCATIONS_INDUSTRIAL = """..."""

# But used wrong name:
entries.append({
    "content": LOCATION_INDUSTRIAL,  # ← Typo! Missing 'S'
})
```

**Result:** `NameError: name 'LOCATION_INDUSTRIAL' is not defined`

### **❌ Mistake 4: Forgetting to run the file**

You edited the content but didn't run:
```bash
python universal_lore_restructured.py
```

**Result:** Changes not loaded into RAG, simulation uses old content.

---

## Quick Checklist

When adding/editing content:

- [ ] Edit content variable (the string)
- [ ] Add/update entry in `create_lore_entries()` function (if new section)
- [ ] Save file
- [ ] Run `python universal_lore_restructured.py`
- [ ] Check output for errors
- [ ] Test in simulation

---

## Summary

**Easy Tasks (Just Edit Strings):**
- ✅ Edit existing content
- ✅ Add to existing section
- ✅ Delete from existing section

**Medium Tasks (Edit String + Function):**
- ✅ Add new section
- ✅ Delete entire section

**Advanced Tasks (Edit Function):**
- ✅ Change categories
- ✅ Change tags
- ✅ Change importance

**Remember:**
1. Content goes in **variables** (top of file)
2. Variables go in **function** (bottom of file)
3. Always **run the file** after editing
4. **Test** in simulation

That's it! The new system makes worldbuilding as easy as editing a text file.
