# Narrative vs Internal Voice - Visual Guide

## How to Tell Them Apart

### 🎭 Regular Narrative (External Description)
**Color:** Magenta  
**Format:** Plain text, no separators  
**Perspective:** 3rd person or 2nd person singular ("you")  
**Purpose:** Describes what's happening externally

**Example:**
```
You push through the door of Vinyl Revival, the morning air sharp with the 
scent of exhaust and fresh asphalt. The sidewalk hums with the distant 
chatter of passersby, but something catches your eye—a crumpled flyer near 
the curb, its black ink bleeding under the sun.
```

---

### 💭 Internal Voice (Character's Thoughts)
**Color:** Bold Cyan  
**Format:** Separated by lines above and below  
**Perspective:** 2nd person plural ("we", "us", "our")  
**Purpose:** Character's internal thoughts and reactions

**Example:**
```
──────────────────────────────────────────────────────────────────────
💭 We've seen places like this before. Reminds us of that ice cream 
   store Dad used to take us to.
──────────────────────────────────────────────────────────────────────
```

---

## Side-by-Side Comparison

### Scenario: Entering a Record Store

**Regular Narrative (Magenta, no separators):**
```
You push through the door of Vinyl Revival. The morning air is sharp with 
exhaust and fresh asphalt. A crumpled flyer lies near the curb, its black 
ink bleeding under the sun. The back room door creaks slightly.
```

**Internal Voice (Bold Cyan, with separators):**
```
──────────────────────────────────────────────────────────────────────
💭 We know this place. Used to come here every Saturday before the rent 
   got too damn high.
──────────────────────────────────────────────────────────────────────
```

---

## Quick Recognition Guide

| Feature | Regular Narrative | Internal Voice |
|---------|------------------|----------------|
| **Color** | Magenta | Bold Cyan |
| **Separators** | None | Lines above & below |
| **Emoji** | None | 💭 |
| **Pronouns** | "you" | "we", "us", "our" |
| **Content** | External events | Internal thoughts |
| **When** | Always | ROAM mode only |

---

## Full Example in Context

```
[Regular Narrative - Magenta]
You step into the dimly lit arcade. Neon lights flicker overhead, casting 
colored shadows across rows of vintage cabinets. The air smells of popcorn 
and old electronics.

[Internal Voice - Bold Cyan with separators]
──────────────────────────────────────────────────────────────────────
💭 We remember this place. Dad brought us here every weekend before he 
   left. That Pac-Man machine in the corner—we got the high score once.
──────────────────────────────────────────────────────────────────────

[Regular Narrative - Magenta]
A teenager glances up from the Street Fighter cabinet, then returns to 
his game. The sounds of digital combat fill the space.
```

---

## Why the Distinction Matters

### Regular Narrative
- **What you see/hear/experience** in the world
- **Objective description** of events
- **Always present** regardless of mode

### Internal Voice
- **What your character thinks/feels** about it
- **Subjective interpretation** based on personality
- **Only in ROAM mode** (disappears during conversations)

---

## Design Philosophy

**Regular Narrative** = The camera showing you the scene  
**Internal Voice** = Your character's commentary on the scene

The visual separation (lines + bold cyan color) makes it immediately obvious when you're reading your character's thoughts versus experiencing the world.

---

## Technical Details

**Color Codes:**
- Regular Narrative: `Color.NARRATIVE` (Magenta)
- Internal Voice: `Color.INTERNAL_VOICE` (Bold Cyan)

**Display Format:**
```python
# Regular narrative
print(f"{Color.NARRATIVE}{narrative_text}{Color.RESET}")

# Internal voice
print(f"\n{Color.SYSTEM}{'─' * 70}{Color.RESET}")
print(f"{Color.INTERNAL_VOICE}💭 {internal_voice}{Color.RESET}")
print(f"{Color.SYSTEM}{'─' * 70}{Color.RESET}")
```

---

## When Internal Voice Appears

✅ **ROAM Mode (SimulationMode.ROAM):**
- Exploring locations alone
- Examining objects
- Moving around solo
- Any activity when no NPCs are present
- Solo activities and observations

❌ **Not During ENCOUNTER Mode (SimulationMode.ENCOUNTER):**
- Conversations with NPCs
- Combat/encounters
- Social interactions
- Any time you're talking to someone
- When NPCs are present and active

**Reason:** Your internal monologue naturally quiets when you're engaged with others. This prevents "schizophrenic" narration where you're thinking while talking.

**Technical:** The system checks `current_mode == SimulationMode.ROAM` (not `NarrativeMode.ROAM`). SimulationMode determines whether you're alone (ROAM) or with NPCs (ENCOUNTER).
