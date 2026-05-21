# Intelligent Location Inference System

## Problem Solved

Users saying "I leave my apartment" or "I exit the door" without specifying a destination were not triggering location changes because the system required explicit destination names.

## Solution

Enhanced `_detect_location_move()` function to use LLM intelligence to **infer logical destinations** when users express movement intent without specifying where they're going.

## How It Works

### 1. Context Analysis
The system first determines the current location type:
- **interior_room**: apartment, room, bedroom, office, shop
- **building**: building, house, structure  
- **exterior_street**: street, road, alley, sidewalk
- **interior_passage**: hallway, corridor, lobby

### 2. Intelligent Inference Rules

When user says "I leave", "I exit", "I go outside" WITHOUT destination:

| Current Location Type | Inferred Destination |
|----------------------|---------------------|
| apartment/room | Hallway or Corridor |
| building/house | Street or Outside |
| shop/store | Street or Outside |
| hallway | Street or Building Entrance |
| street | Nearby Area or Another Street |

### 3. Examples

**Inference Examples:**
- Current: "My Apartment" + "I leave" → **NEW location: "Hallway"**
- Current: "Office Building" + "I exit" → **NEW location: "Street"**
- Current: "Shop" + "I go outside" → **NEW location: "Street"**
- Current: "My Apartment" + "I exit the door" → **NEW location: "Hallway"**

**Explicit Destination (no inference needed):**
- "I go to the diner" → **NEW location: "Diner"**
- "I enter the bar" → **NEW location: "Bar"**

**NOT Location Changes:**
- "What do I see?" → NO (question/inquiry)
- "I look around" → NO (observation)
- "I walk across the room" → NO (within-location movement)

## Technical Implementation

### File Modified
`MAIN/redesigned_main.py` - Function `_detect_location_move()` (lines 921-1051)

### Key Changes

1. **Added Current Location Context**
   - Extracts current location name and type from spatial manager
   - Classifies location type for intelligent inference

2. **Enhanced LLM Prompt**
   - Includes current location context
   - Provides inference rules and examples
   - Returns `inferred: true/false` flag

3. **Inference Logging**
   - System logs when destination is inferred vs explicit
   - Helps debugging and transparency

### LLM Configuration
- **Model**: Coordination role model
- **Temperature**: 0.2 (slightly higher for creative inference)
- **Max Tokens**: 150

## Response Format

```json
{
  "location_change": true,
  "location_name": "Hallway",
  "inferred": true
}
```

OR

```json
{
  "location_change": false
}
```

## Benefits

1. **Natural Language Support**: Users can say "I leave" naturally without specifying every destination
2. **Contextual Intelligence**: System understands spatial relationships (apartment → hallway → street)
3. **Maintains Immersion**: No need for meta-level destination specification
4. **Flexible**: Still supports explicit destinations when provided
5. **Safe**: Only infers when movement intent is clear

## Testing Scenarios

- ✅ "I leave my apartment" → Infers "Hallway"
- ✅ "I exit the door" → Infers logical destination based on current location
- ✅ "I go outside" → Infers "Street" from indoor locations
- ✅ "I go to the bar" → Uses explicit destination "Bar"
- ❌ "I look around" → No location change (observation only)
- ❌ "What do I see?" → No location change (inquiry)

## Design Philosophy

**The system should understand user intent, not require perfect specification.**

- Movement verbs + no destination = intelligent inference
- Movement verbs + explicit destination = use that destination
- No movement verbs = no location change
- Questions/observations = no location change

The LLM acts as an intelligent interpreter of spatial relationships and user intent, making the simulation feel more natural and responsive.
