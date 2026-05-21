# Realitas Neo: Investigation Summary
**Date:** 2026-02-11

## Overview
Comprehensive investigation of 4 pending implementation issues and 3 missing systems.

---

## ✅ COMPLETED INVESTIGATIONS

### 1. **UA/NUA Role Confusion** ⚠️ CRITICAL BUG
**Status:** READY FOR FIX
**Priority:** CRITICAL
**File:** INVESTIGATION_REPORT_UA_NUA_ROLE_CONFUSION.md

**Issue:**
When UA reacts to NUA's proaction in encounter mode, the role parameters are passed **backwards** to `detect_inquiry_or_action()`.

**Location:** MAIN/redesigned_main.py:17618

**Current (WRONG):**
```python
det = _strict_detect_inquiry_or_action(ua_react_input, reactor, proactor, _retries=3)
```

**Fixed (CORRECT):**
```python
det = _strict_detect_inquiry_or_action(ua_react_input, actor, proactor, _retries=3)
```

**Impact:**
- Incorrect action classification
- Wrong addressed_to/addressed_type detection
- Movement target confusion
- Exchange resolution errors

**Complexity:** Simple one-line fix

---

### 2. **Inquiry vs Exchange Boundary** ⚠️ DESIGN FLAW
**Status:** READY FOR FIX
**Priority:** HIGH
**File:** INVESTIGATION_REPORT_INQUIRY_EXCHANGE_BOUNDARY.md

**Issue:**
Social inquiries (asking questions) incorrectly trigger contested exchange mode when they should be simple inquiries.

**Location:** agents/interpreter_agent.py:2951

**Problem Examples:**
- ❌ "Ask the bartender what's on tap" → classified as contested_action
- ❌ "What's your name?" → triggers encounter mode
- ✅ Should be: inquiry (immediate response, no time pressure)

**Root Cause:**
Prompt explicitly lists "Ask the bartender" as contested_action example.

**Fix Required:**
1. Remove "Ask the bartender" from contested_action examples
2. Add clarifying rule distinguishing:
   - **Simple questions** = INQUIRY
   - **Social pressure/manipulation** = CONTESTED_ACTION
   - **Transactions** = CONTESTED_ACTION

**Complexity:** Prompt modification + testing

---

### 3. **Actor Creation from Mentions** ✅ WORKING WELL
**Status:** NO IMMEDIATE FIX NEEDED
**Priority:** LOW (enhancement opportunities)
**File:** INVESTIGATION_REPORT_ACTOR_CREATION_FROM_MENTIONS.md

**Finding:**
System is **well-implemented** with robust detection, deduplication, and integration.

**Existing Features:**
- ✅ LLM-based NPC extraction from scene descriptions
- ✅ Deduplication (name match, role match, generic matching)
- ✅ Relationship context inference
- ✅ Spatial map integration
- ✅ Auto-memory creation
- ✅ Multiple trigger points throughout main loop

**Enhancement Opportunities:**
1. **Dialogue-triggered spawning** (when NPC says "Here comes Marcus!")
2. **Better mention tracking** (→ feeds into Task #5: Mention System)
3. **Narrative context scanning** (optional, lower priority)

**Verdict:** Solid foundation, focus on enhancement rather than fixes.

---

### 4. **Wake Up Description Hardcoded** ⚠️ IMMERSION ISSUE
**Status:** NEEDS DYNAMIC SYSTEM
**Priority:** MEDIUM-HIGH
**File:** INVESTIGATION_REPORT_WAKE_UP_HARDCODED.md

**Issue:**
Wake-up scenes always use generic "Your eyes [verb] open..." regardless of character personality, S-factors, or physical state.

**Location:** agents/creator_agent.py:3178

**Current Behavior:**
Template-based opening with no personality variation:
```
"Your eyes shoot open..." (every character, every time)
```

**Missing:**
- Personality-driven variation
- S-factor influence (Swiftness → alert, Sturdiness → sluggish)
- Status effects (exhausted → struggles to wake)
- Internal voice integration

**Solution Needed:**
Create `generate_scene_opening_narration()` in NarratorAgent:
- Uses personality traits
- Considers S-factors
- Reflects current status
- Integrates internal voice system

**Complexity:** Medium (new system needed)

---

## 📋 MISSING SYSTEMS TO CREATE

### 5. **Mention System** 🆕 NEW SYSTEM
**Status:** DESIGN NEEDED
**Priority:** HIGH
**Dependencies:** Builds on Actor Creation system

**Purpose:**
Track all actor mentions with metadata to maintain narrative consistency and enable location queries.

**Features Needed:**
- Track WHO mentioned an actor
- Track WHEN and WHERE actors were mentioned
- Track CONTEXT (present, elsewhere, past, arriving, etc.)
- Query interface: "Where was Marcus last mentioned?"
- Integration with SceneNPCParser for spawning decisions

**Use Cases:**
- "I go to find Marcus" → Check last mentioned location
- Dialogue: "Marcus just left" → Don't spawn, update location tag
- Dialogue: "Here comes Marcus!" → DO spawn
- Continuity validation

---

### 6. **Continuous Map Population** 🆕 NEW SYSTEM
**Status:** DESIGN NEEDED
**Priority:** MEDIUM
**Dependencies:** Spatial system, Population manager

**Purpose:**
Dynamically spawn appropriate NPCs as UA explores new areas, maintaining consistent population density.

**Features Needed:**
- Location-based NPC templates (bar → bartender, patron, etc.)
- Population density by location type
- Spawn rate limiting (don't spam NPCs)
- Persistence (spawned NPCs remain unless they leave)
- Integration with Mention System (check if known NPCs should appear)

**Integration Points:**
- Use SceneNPCParser for role-appropriate spawning
- Use Spatial system for positioning
- Use Population manager for crowd simulation
- Use Architect for spawn positions

---

### 7. **Fact System** 🆕 NEW SYSTEM
**Status:** DESIGN NEEDED
**Priority:** HIGH
**Dependencies:** Key Memories system, Narrative Context

**Purpose:**
Establish and track canonical world facts to prevent contradictions and maintain simulation consistency.

**Features Needed:**
- Fact types:
  - Actor facts (Marcus is a studio engineer)
  - Location facts (The bar is on Main Street)
  - Relationship facts (Linda is Marcus's sister)
  - Event facts (The power went out last night)
  - World facts (It's 2026, cyberpunk setting)
- Fact validation (check for contradictions)
- Fact querying (LLM can ask "Is Marcus a doctor?")
- Fact sourcing (track where facts came from)
- Fact priority (user-established > system-inferred)

**Integration Points:**
- Query during action interpretation
- Validate during scene generation
- Update from dialogue/narrative
- Link to Key Memories for persistence

---

## 🎯 RECOMMENDED IMPLEMENTATION ORDER

### Phase 1: Critical Bugs (Immediate)
1. ✅ **Fix UA/NUA Role Confusion** (1 line fix)
2. ✅ **Fix Inquiry vs Exchange Boundary** (prompt modification)

### Phase 2: Core Systems (Next Sprint)
3. 🔨 **Implement Fact System** (foundation for consistency)
4. 🔨 **Implement Mention System** (builds on existing Actor Creation)

### Phase 3: Enhancement Systems (Future)
5. 🔨 **Implement Continuous Map Population**
6. 🔨 **Implement Dynamic Wake-Up Narration**

---

## 📊 IMPACT ASSESSMENT

| Issue | Priority | Impact | Complexity | Risk |
|-------|----------|--------|------------|------|
| UA/NUA Role Confusion | CRITICAL | High | Trivial | Very Low |
| Inquiry/Exchange Boundary | HIGH | Medium | Low | Low |
| Actor Creation | LOW | Low | N/A | None |
| Wake Up Hardcoded | MEDIUM-HIGH | Medium | Medium | Low |
| Mention System | HIGH | High | Medium | Medium |
| Map Population | MEDIUM | Medium | High | Medium |
| Fact System | HIGH | High | High | Medium |

---

## 📝 NOTES

### Quick Wins (Do First)
- Fix UA/NUA role confusion (1 line)
- Fix inquiry boundary (prompt edit)

### Architectural Improvements
- Fact System provides foundation for consistency
- Mention System enhances continuity
- Both enable better emergence/simulation quality

### Enhancement Opportunities
- Dynamic wake-up narration improves immersion
- Map population improves world feel
- Both are "nice to have" rather than critical

---

## 🔗 RELATED DOCUMENTS

- INVESTIGATION_REPORT_UA_NUA_ROLE_CONFUSION.md
- INVESTIGATION_REPORT_INQUIRY_EXCHANGE_BOUNDARY.md
- INVESTIGATION_REPORT_ACTOR_CREATION_FROM_MENTIONS.md
- INVESTIGATION_REPORT_WAKE_UP_HARDCODED.md

---

**Investigation completed:** 2026-02-11
**Investigator:** Claude Sonnet 4.5
**Status:** All 4 investigations complete, 3 systems designed
**Next Action:** Implement Phase 1 critical bug fixes
