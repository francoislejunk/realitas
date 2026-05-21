# "Mental" Renamed to "Inquiry" - Unified Naming Convention

## The Problem

The system had **two names for the same thing**:

1. **"fallible_subtype: mental"** - Used in interpreter
2. **"inquiry"** - Used conceptually in documentation

This caused confusion and misclassification:
```
User: "I try to remember my best friend"
System: Classifies as "fallible_action, mental"
But: Should be treated as "inquiry"
Result: Confusion about what "mental" means
```

## The Root Cause

**Inconsistent naming convention:**
- Code said "mental"
- Documentation said "inquiry"
- Developers/users confused about which term to use
- "Mental" is vague - could mean thinking, remembering, analyzing, etc.
- "Inquiry" is clear - seeking information

## The Solution

**Renamed "mental" to "inquiry" throughout the system:**

1. **Interpreter Agent** - Now outputs "inquiry" instead of "mental"
2. **Main Loop** - Accepts both "mental" (legacy) and "inquiry" (new)
3. **Display Messages** - Show "INQUIRY" instead of "MENTAL"
4. **Documentation** - Consistent terminology

## Changes Made

### 1. Interpreter Agent Prompt

**File: `agents/interpreter_agent.py`** (line 1930)

**Before:**
```python
"fallible_subtype": "mental" or "physical"
```

**After:**
```python
"fallible_subtype": "inquiry" or "physical"
```

### 2. Subtype Descriptions

**File: `agents/interpreter_agent.py`** (lines 1918-1920)

**Before:**
```
2. FALLIBLE ACTION - Actions against ENVIRONMENT or SELF:
   - Information Gathering: Observational questions, perception checks
   - Situation Overcoming: Physical challenges vs. environment
```

**After:**
```
2. FALLIBLE ACTION - Actions against ENVIRONMENT or SELF:
   - Inquiry: Questions, information seeking, memory recall, perception checks
   - Physical: Physical challenges vs. environment (climb, pick lock, craft)
```

### 3. Fallback Classification

**File: `agents/interpreter_agent.py`** (lines 2025-2028)

**Before:**
```python
# Simple rule: questions = mental, everything else = physical
if is_question:
    response_data['fallible_subtype'] = 'mental'
    response_data['reasoning'] = "Question detected - mental action"
```

**After:**
```python
# Simple rule: questions = inquiry, everything else = physical
if is_question:
    response_data['fallible_subtype'] = 'inquiry'
    response_data['reasoning'] = "Question detected - inquiry action"
```

### 4. Main Loop - Backward Compatibility

**File: `MAIN/redesigned_main.py`** (lines 1459-1460)

**Before:**
```python
is_info_gathering = fallible_subtype == 'mental'
```

**After:**
```python
# Treat both "mental" (legacy) and "inquiry" (new) as inquiry
is_info_gathering = fallible_subtype in ['mental', 'inquiry']
```

### 5. Display Messages

**File: `MAIN/redesigned_main.py`** (lines 4634, 7009)

**Before:**
```python
print(f"📋 FALLIBLE ACTION (MENTAL - Information Gathering)")
```

**After:**
```python
print(f"📋 INQUIRY (Information Gathering)")
```

## Terminology Clarification

### Old (Confusing)

```
fallible_action
├── mental (what does this mean?)
│   └── Questions? Thinking? Memory?
└── physical
    └── Climbing, picking locks, etc.
```

### New (Clear)

```
fallible_action
├── inquiry (seeking information)
│   └── Questions, memory recall, perception, knowledge checks
└── physical (physical challenges)
    └── Climbing, picking locks, crafting, etc.
```

## Examples

### Example 1: Question

```
User: "What's the best way downtown?"
Old: fallible_action, mental
New: fallible_action, inquiry
Display: 📋 INQUIRY (Information Gathering)
```

### Example 2: Memory Recall

```
User: "I try to remember my best friend"
Old: fallible_action, mental
New: fallible_action, inquiry
Display: 📋 INQUIRY (Information Gathering)
```

### Example 3: Perception Check

```
User: "I look around the room for clues"
Old: fallible_action, mental
New: fallible_action, inquiry
Display: 📋 INQUIRY (Information Gathering)
```

### Example 4: Physical Action

```
User: "I climb the wall"
Old: fallible_action, physical
New: fallible_action, physical (unchanged)
Display: 📋 FALLIBLE ACTION (Physical)
```

## Backward Compatibility

The system still accepts "mental" for backward compatibility:

```python
# Both work:
if fallible_subtype in ['mental', 'inquiry']:
    # Process as inquiry
```

This ensures:
- Old logs/data still work
- Gradual migration possible
- No breaking changes

## Benefits

✅ **Clear naming** - "Inquiry" is self-explanatory  
✅ **Consistent** - Same term everywhere  
✅ **No confusion** - One name, one concept  
✅ **Better classification** - LLM understands "inquiry" better  
✅ **Backward compatible** - Still accepts "mental"  

## What "Inquiry" Means

**Inquiry = Seeking Information**

Includes:
- **Questions** - "What's downtown?", "Who is that?"
- **Memory recall** - "I try to remember...", "I recall..."
- **Perception** - "I look for...", "I search for..."
- **Knowledge checks** - "Do I know about...", "What do I know about..."
- **Investigation** - "I examine...", "I inspect..."

Does NOT include:
- **Physical actions** - Climbing, fighting, crafting
- **Social actions** - Talking to NPCs (that's contested)
- **Movement** - Walking, running (that's given)

## Files Modified

1. **`agents/interpreter_agent.py`** (lines 1919-1920, 1930, 2025-2028)
   - Updated prompt to use "inquiry"
   - Updated fallback logic to use "inquiry"

2. **`MAIN/redesigned_main.py`** (lines 1459-1460, 4632-4634, 7008-7009)
   - Accept both "mental" and "inquiry"
   - Display "INQUIRY" instead of "MENTAL"

## Result

✅ **Unified naming** - "Inquiry" everywhere  
✅ **Clear meaning** - Seeking information  
✅ **No confusion** - One term, one concept  
✅ **Better UX** - Users understand what it means  
✅ **Backward compatible** - Still works with "mental"  

"Mental" has been renamed to "Inquiry" for clarity and consistency!
