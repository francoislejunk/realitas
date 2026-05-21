# NPCs Now Generated with Built-In Memories

## The Feature

NPCs are now automatically generated with **2-4 background memories** that define their character, providing depth and context for interactions.

## Implementation

### 1. Updated NPC Generation Prompt

**File: `agents/creator_agent.py`** (line 733)

Added memories to requirements:
```python
**Requirements:**
- Name: Appropriate for the context
- Age: Character's age
- Location: Geographic location
- Pronouns: Character's pronouns
- Occupation: Role/job
- Goals: 1-3 objectives
- Skills: MINIMUM 5 skills
- Inventory: 2-4 items
- Personality: Internal and external traits
- Memories: 2-4 background memories that define this character  # NEW
```

### 2. Example Memory Format

```json
{
    "memories": [
        "Grew up in Brooklyn, learned street smarts early",
        "Lost father at age 12, had to help support family",
        "Worked various odd jobs before finding current occupation",
        "Has a younger sister who looks up to them"
    ]
}
```

### 3. Memory Extraction and Assignment

**File: `agents/creator_agent.py`** (lines 875-897)

```python
# Extract memories from generated data
memories = nua_data.get('memories', [])

# Build actor sheet
nua_sheet = ActorSheet(
    name=nua_data['name'],
    ...
    memories=memories  # Add built-in memories
)
```

## Types of Memories Generated

### 1. Childhood/Background
```
"Grew up in a small fishing village on the coast"
"Raised by a single mother who worked three jobs"
"Spent childhood helping in family restaurant"
```

### 2. Formative Experiences
```
"Lost father at age 12, had to help support family"
"Survived a car accident that changed their perspective"
"Witnessed a crime that made them want to become a cop"
```

### 3. Relationships
```
"Has a younger sister who looks up to them"
"Estranged from brother after family dispute"
"Married young, divorced after 5 years"
```

### 4. Career/Skills
```
"Worked various odd jobs before finding current occupation"
"Learned hacking from online forums as a teenager"
"Trained as a mechanic by their grandfather"
```

### 5. Knowledge/Expertise
```
"Knows the city's underground network like the back of their hand"
"Expert in vintage electronics from years of collecting"
"Fluent in three languages from traveling extensively"
```

## Example Generated NPC

```json
{
    "name": "Marcus Chen",
    "age": 34,
    "location": "Downtown",
    "pronouns": "he/him",
    "occupation": "Street Vendor",
    "goals": [
        "Save enough money to open a proper restaurant",
        "Keep his sister out of trouble"
    ],
    "skills": {
        "Cooking": 3,
        "Street Smarts": 3,
        "Negotiation": 2,
        "Local Knowledge": 3,
        "Quick Thinking": 2
    },
    "inventory": [
        {
            "name": "Food Cart Keys",
            "description": "Keys to his mobile food cart",
            "supplement_bonus": 1
        }
    ],
    "personality_traits": {
        "internal": "Protective and resourceful",
        "external": "Friendly but cautious"
    },
    "memories": [
        "Immigrated from Hong Kong at age 15 with his family",
        "Lost parents in a fire, now takes care of younger sister",
        "Learned cooking from his grandmother's traditional recipes",
        "Knows every street vendor and shop owner in the district"
    ]
}
```

## How Memories Are Used

### 1. Conversation Context
When talking to Marcus, the system can reference his memories:
```
User: "Tell me about yourself"
Marcus: "I came here from Hong Kong when I was 15. My grandmother 
taught me everything I know about cooking. Now I'm trying to save 
up to open a real restaurant."
```

### 2. Relationship Building
Memories provide hooks for deeper connections:
```
User: "Do you have family here?"
Marcus: "Just my younger sister. I've been taking care of her since 
we lost our parents. She's all I have left."
```

### 3. Character Consistency
Memories ensure NPCs act consistently with their background:
```
User: "Can you help me with something illegal?"
Marcus: (Cautious due to memories) "I've got my sister to think about. 
I can't risk getting in trouble with the law."
```

### 4. World Building
Memories add depth to the world:
```
Marcus's memories mention:
- Hong Kong immigration
- Fire that killed parents
- Grandmother's recipes
- District vendor network

These create a richer, more believable world.
```

## Benefits

✅ **Character Depth** - NPCs feel like real people with histories  
✅ **Conversation Hooks** - Memories provide topics for dialogue  
✅ **Consistent Behavior** - Background informs decisions  
✅ **World Building** - Memories add texture to the setting  
✅ **Automatic** - Generated during NPC creation  
✅ **Contextual** - Memories fit the scene and role  

## Memory Guidelines for LLM

The LLM generates memories that:
1. **Fit the role** - Bartender has bar-related memories
2. **Explain skills** - How they learned their expertise
3. **Create relationships** - Family, friends, enemies
4. **Provide motivation** - Why they do what they do
5. **Add flavor** - Unique details that make them memorable

## Example Scenarios

### Scenario 1: Bartender

```json
{
    "name": "Mike Sullivan",
    "occupation": "Bartender",
    "memories": [
        "Inherited the bar from his father who ran it for 30 years",
        "Served in the Navy for 8 years before coming home",
        "Knows every regular's drink order by heart",
        "Lost his wife to cancer three years ago"
    ]
}
```

### Scenario 2: Security Guard

```json
{
    "name": "Sarah Martinez",
    "occupation": "Security Guard",
    "memories": [
        "Former police officer who left the force after corruption scandal",
        "Trained in martial arts since childhood",
        "Has a photographic memory for faces",
        "Supporting her elderly mother on this salary"
    ]
}
```

### Scenario 3: Street Musician

```json
{
    "name": "Alex Rivers",
    "occupation": "Street Musician",
    "memories": [
        "Dropped out of Juilliard to pursue their own sound",
        "Busked across Europe for two years",
        "Lost their hearing in one ear from a stage accident",
        "Writing songs about people they meet on the streets"
    ]
}
```

## Files Modified

1. **`agents/creator_agent.py`** (lines 733, 753-758, 875-897)
   - Added memories to generation prompt
   - Added memory examples in JSON template
   - Extract and assign memories to ActorSheet

## Result

✅ **Every NPC has background memories** - Automatically generated  
✅ **Memories fit the character** - Contextual and relevant  
✅ **Adds depth** - NPCs feel more real and believable  
✅ **Enables richer interactions** - More conversation topics  
✅ **No extra work** - Happens automatically during creation  

NPCs now come with rich backstories that make them feel like real people with histories, not just stat blocks!
