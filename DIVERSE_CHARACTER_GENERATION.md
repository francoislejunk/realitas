# Diverse Character Generation System

## Overview

Enhanced the vessel selection system to ensure each character option has a **different occupation**, providing varied gameplay experiences instead of generating multiple similar characters.

## Problem

Previously, the system could generate three characters with very similar or identical occupations:
- All three could be DJs/music-related
- All three could be mechanics
- No guarantee of variety in character experiences

**Example of Poor Diversity:**
```
[1] ROXY VEX - Underground Music Promoter / DJ
[2] DEXTER "DEEJAY" CRUZ - Underground DJ & Record Collector
[3] JACE VEXLEY - Underground DJ / Music Journalist
```

All three are DJ/music industry characters - no variety!

## Solution

### 1. Occupation Tracking
- System now tracks used occupations
- Rejects characters with duplicate or too-similar occupations
- Retries generation until unique occupation is found

### 2. RAG-Based World Context Generation
System dynamically queries the worldbuilding RAG database for ALL relevant world information:

**Single Comprehensive Query:**
```python
world_context = rag_system.query(
    "occupations professions jobs working class service industry temporal timeline setting",
    max_results=6,    # Get multiple documents (occupations + temporal)
    max_tokens=1000   # Comprehensive context
)
```

**What Gets Retrieved:**
- **Occupation Documents:**
  - "Service Industry Occupations - Detailed"
  - "Blue Collar Occupations - Detailed"  
  - "White Collar Occupations - Detailed"
  - "Urban Character Types"
- **Temporal Context:**
  - "1990s Timeline Context" (or whatever time period exists)
  - Technology level, cultural context
  - Economic conditions, social structure
- **Any other relevant lore**

**How It Works:**
1. Query RAG **once** at start of character generation
2. Get comprehensive world context (1000 tokens)
3. **Assign explicit category to each character:**
   - Character 1: Blue collar / skilled trades
   - Character 2: Service industry
   - Character 3: White collar / office work
4. Pass world context + specific category requirement to LLM
5. LLM generates character from assigned category only
6. Duplicate detection ensures variety within categories

**Six Occupation Categories:**
1. **Blue Collar / Skilled Trades**: mechanic, construction, factory, warehouse, electrician, plumber
2. **Service Industry**: bartender, waiter, retail, security guard, janitor, cook, cashier
3. **White Collar / Office**: office worker, data entry, telemarketer, insurance, receptionist
4. **Creative / Artistic**: musician, artist, photographer, writer, designer, DJ
5. **Night Shift / Late Hours**: taxi driver, night security, diner cook, gas station attendant
6. **Street Level / Hustler**: small-time dealer, pawn shop, street vendor, bouncer, courier

**Benefits of Category Assignment System:**
- ✅ **Guaranteed variety** - each character from different category
- ✅ **No duplicate types** - blue collar, service, white collar always different
- ✅ **RAG-informed** - categories populated from world lore
- ✅ **Explicit control** - LLM can't ignore variety requirement
- ✅ **Lore consistency** - characters still match world's structure
- ✅ **Period authenticity** - pulled from temporal lore
- ✅ **Scalable** - works with any setting/time period

### 3. Duplicate Detection
Smart occupation comparison:
```python
# Checks if occupations share key words
used_words = set(used_occ.lower().split())
new_words = set(occupation_lower.split())

# "DJ" appears in both → duplicate
# "Mechanic" vs "Bartender" → unique
```

### 4. Increased Retries
- Raised from 2 to 5 retries per character
- Ensures system finds unique occupations
- Falls back gracefully if all retries exhausted

## Expected Results

**Example of Good Diversity:**
```
[1] MARCUS STONE - Auto Mechanic
[2] LISA CHEN - Freelance Photographer  
[3] TONY DELUCA - Night Shift Security Guard
```

Three completely different occupations = three different gameplay experiences!

**Another Example:**
```
[1] JAKE MORRISON - Warehouse Forklift Operator
[2] SARAH VEGA - Struggling Artist / Street Muralist
[3] RICK PALMER - Graveyard Shift Gas Station Attendant
```

## Implementation Details

### File Modified
`vessel_selection_system.py` - `generate_vessel_options()` method

### Key Changes

**1. Added RAG System Integration:**
```python
def __init__(self, creator_agent, storage_directory: Path, rag_system=None):
    self.rag_system = rag_system  # RAG system for occupation queries
```

**2. Added Single Comprehensive World Context Query:**
```python
# Query RAG ONCE for all world information (occupations + temporal + setting)
world_context = self.rag_system.query(
    "occupations professions jobs working class service industry temporal timeline setting",
    max_results=6,    # Get multiple documents
    max_tokens=1000   # Comprehensive context
)

# Pass same comprehensive context to all character generations
context_hint = f"""Create a character with a realistic occupation based on the world context below.

**WORLD CONTEXT FROM LORE:**
{world_context}

**REQUIREMENTS:**
- Choose a DIFFERENT type of occupation from the context above
- Make it specific and grounded in the world's time period and setting
- Ensure variety - avoid similar occupations to previously generated characters"""
```

**3. Added Occupation Tracking:**
```python
used_occupations = set()  # Track occupations to ensure diversity
```

**3. Added Duplicate Detection:**
```python
# Check if occupations share key words
is_duplicate = False
for used_occ in used_occupations:
    used_words = set(used_occ.lower().split())
    new_words = set(occupation_lower.split())
    if len(used_words & new_words) > 0:
        is_duplicate = True
        break

if is_duplicate and retry < max_retries_per_option - 1:
    self.logger.info(f"Occupation '{occupation}' too similar. Retrying...")
    continue
```

**4. Increased Retry Count:**
```python
max_retries_per_option = 5  # More retries to find unique occupations
```

## Benefits

### 1. Varied Gameplay Experiences
Each character offers a different:
- Starting location potential
- Skill set
- Social connections
- Daily routine
- Story opportunities

### 2. Replayability
Players can experience:
- Blue-collar struggles (mechanic, warehouse worker)
- Creative pursuits (artist, musician)
- Service industry grind (bartender, security)
- Street-level survival (hustler, bouncer)
- Corporate drudgery (temp, telemarketer)
- Night shift atmosphere (taxi, diner cook)

### 3. Character Identity
Each occupation provides:
- Clear character identity
- Distinct worldview
- Unique challenges
- Different social circles
- Varied story hooks

### 4. 1990s Authenticity
Occupations reflect:
- Pre-gig economy reality
- Working-class struggles
- Economic pressure
- Period-appropriate jobs
- Grounded, realistic backgrounds

## Example Character Variety

### Mechanic (Working-Class Trade)
```
MARCUS STONE - Auto Mechanic
- Skills: Engine Repair, Welding, Negotiation
- Starting location: Garage/workshop
- Story hooks: Car culture, racing, repair jobs
- Social circle: Other mechanics, car enthusiasts
```

### Photographer (Creative/Artistic)
```
LISA CHEN - Freelance Photographer
- Skills: Photography, Darkroom Work, Networking
- Starting location: Studio/apartment
- Story hooks: Art scene, exhibitions, commissions
- Social circle: Artists, gallery owners, subjects
```

### Security Guard (Service Industry)
```
TONY DELUCA - Night Shift Security Guard
- Skills: Observation, Conflict Resolution, First Aid
- Starting location: Office building/warehouse
- Story hooks: Night shift mysteries, theft, danger
- Social circle: Other guards, building tenants
```

### Bartender (Service Industry)
```
SARAH MARTINEZ - Dive Bar Bartender
- Skills: Mixology, Reading People, Conflict Management
- Starting location: Bar/tavern
- Story hooks: Bar drama, regulars, late-night incidents
- Social circle: Regulars, other service workers
```

### Warehouse Worker (Working-Class Trade)
```
JAKE MORRISON - Warehouse Forklift Operator
- Skills: Forklift Operation, Inventory, Physical Labor
- Starting location: Warehouse/loading dock
- Story hooks: Union issues, workplace accidents, theft
- Social circle: Co-workers, truckers, supervisors
```

### Street Artist (Creative/Artistic)
```
ALEX RIVERA - Street Muralist / Graffiti Artist
- Skills: Spray Painting, Urban Navigation, Stealth
- Starting location: Alley/urban area
- Story hooks: Art vs vandalism, turf, commissions
- Social circle: Other artists, cops, property owners
```

## Technical Notes

### Graceful Degradation
- If all retries fail, accepts last generated character
- Logs warnings about duplicate occupations
- Doesn't break character generation flow

### Category Rotation
- Uses modulo to cycle through categories
- Ensures first three characters hit different categories
- Additional characters continue cycling

### Word-Based Matching
- Simple but effective duplicate detection
- Catches obvious duplicates ("DJ" in multiple occupations)
- Allows similar but distinct occupations ("Mechanic" vs "Mechanical Engineer")

### Context Hints
- Guides LLM toward specific occupation types
- Maintains 1990s authenticity requirement
- Encourages specific, grounded professions

## Future Enhancements

### Possible Improvements
1. **Skill Set Diversity**: Ensure different skill focuses
2. **Personality Diversity**: Vary internal/external traits more
3. **S-Factor Diversity**: Ensure different stat distributions
4. **Background Diversity**: Vary socioeconomic backgrounds
5. **Location Diversity**: Different starting location types

### Advanced Duplicate Detection
- Semantic similarity checking
- Occupation category classification
- More sophisticated word matching

## Summary

The vessel selection system now guarantees diverse character options by:
1. Tracking used occupations
2. Guiding generation with category hints
3. Detecting and rejecting duplicates
4. Retrying until unique occupations are found

**Result:** Players get three genuinely different character options, each offering a unique gameplay experience in the 1990s world of Realitas Neo.

No more "three DJs" - now you get a mechanic, a photographer, and a security guard!
