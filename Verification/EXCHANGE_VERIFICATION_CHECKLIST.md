# Exchange System Verification Checklist

## Quick Test Setup

Run: `python QUICK_EXCHANGE_TEST.py`

This drops you directly into an exchange scenario with:
- **User Actor:** Test User (ready for exchanges)
- **NPC:** Vince 'Grease' Morrison (mechanic)
- **Scene:** Bar confrontation

---

## Critical Exchange Verifications

### ✅ **1. NPC Detection/Parsing**

**Test Input:** `I try to convince Vince to help me`

**Verify:**
- [ ] System detects "Vince" as NPC name
- [ ] Maps to full name: "Vince 'Grease' Morrison"
- [ ] Classifies as `contested_action`
- [ ] Sets `addressed_to: "Vince 'Grease' Morrison"`
- [ ] No parsing errors with apostrophes in name

**Expected Output:**
```
🔍 Analyzing action...
📋 Action Type: contested_action
✅ CONTESTED ACTION DETECTED!
Target: Vince 'Grease' Morrison
```

---

### ✅ **2. Time Advancement During Exchange**

**Test Input:** `I punch Vince`

**Verify:**
- [ ] Time recorded BEFORE exchange
- [ ] Exchange processes
- [ ] Time advances by **3 seconds** (combat exchange)
- [ ] Time recorded AFTER exchange
- [ ] Display shows time change

**Expected Output:**
```
⏰ Time before: [timestamp]
PROCESSING EXCHANGE
⏰ Time after: [timestamp + 3 seconds]
✅ Time advanced: 3 seconds
```

---

### ✅ **3. Self-Effects Application**

**Test Input:** `I shove Vince`

**Verify:**
- [ ] Proactor (you) has self-effects
- [ ] Self-effects NOT "N/A"
- [ ] Severity between 1-4
- [ ] Magnitude appropriate
- [ ] Status changes applied to proactor
- [ ] Reactor (Vince) has self-effects
- [ ] Both actors show status changes

**Expected Output:**
```
PROACTOR SELF-EFFECTS:
- Condition: Inherent Cost
- Target: STAMINA
- Severity: 2
- Description: [effort cost]

REACTOR SELF-EFFECTS:
- Condition: [defensive effort]
- Target: STAMINA
- Severity: 1
```

---

### ✅ **4. Sympathy Modifiers**

**Setup:** Establish relationship first

**Test Input 1:** `I help Vince up` (after establishing positive sympathy)

**Verify:**
- [ ] Sympathy modifier shown in calculation
- [ ] Positive sympathy makes helping EASIER (negative modifier)
- [ ] Explanation provided

**Test Input 2:** `I punch Vince` (with positive sympathy)

**Verify:**
- [ ] Sympathy modifier shown
- [ ] Positive sympathy makes attacking HARDER (positive penalty)
- [ ] Explanation provided

---

### ✅ **5. Exchange Type Detection**

**Test Different Exchange Types:**

**Social Exchange:**
```
Input: I try to convince Vince to help me
Verify: Exchange Type = SPIRIT
```

**Combat Exchange:**
```
Input: I punch Vince
Verify: Exchange Type = STAMINA
```

**Intimidation Exchange:**
```
Input: I threaten Vince
Verify: Exchange Type = SPIRIT (social pressure)
```

---

### ✅ **6. Success Calculation Transparency**

**Test Input:** `I punch Vince`

**Verify:**
- [ ] **PROACTOR CALCULATION SHOWN:**
  - S-Trait (Sturdiness) + value
  - Skill (Brawling) + value
  - Serendipity roll shown (e.g., "2D6-7 = +1")
  - Stress modifier
  - Status modifier
  - Sympathy modifier (if applicable)
  - **Total Success = [number]**

- [ ] **REACTOR CALCULATION SHOWN:**
  - S-Trait (Swiftness for defense) + value
  - Skill (Dodge/Defense) + value
  - Serendipity roll shown
  - Stress modifier
  - Status modifier
  - Sympathy modifier
  - **Total Success = [number]**

- [ ] **WINNER DETERMINED:**
  - Higher total wins
  - Margin calculated
  - Outcome narrative matches margin

---

### ✅ **7. Status Changes Applied**

**Test Input:** `I punch Vince` (successful hit)

**Verify:**
- [ ] Damage = margin of success
- [ ] Vince's Stamina reduced by damage
- [ ] Your Stamina reduced by self-effect cost
- [ ] Status changes displayed:
  ```
  Vince 'Grease' Morrison:
  - Stamina: 4 → 2 (-2 from punch)
  
  Test User:
  - Stamina: 3 → 2 (-1 from effort)
  ```

---

### ✅ **8. Knockout Detection**

**Test Input:** Keep attacking until Vince's Stamina ≤ 0

**Verify:**
- [ ] 💀 KNOCKOUT! displayed
- [ ] Vince loses initiative
- [ ] Vince can't act next turn
- [ ] Recovery system activates (+1 per turn)
- [ ] Consciousness regained when Stamina > 0

---

### ✅ **9. Multiple NPCs**

**Scenario:** Add second NPC to scene

**Test Input:** `I talk to Vince` (with multiple NPCs present)

**Verify:**
- [ ] System correctly identifies "Vince" from multiple NPCs
- [ ] Doesn't confuse with other NPCs
- [ ] Targets correct reactor
- [ ] No ambiguity errors

---

### ✅ **10. Pronoun Resolution**

**Test Input:** `I punch him` (after Vince is established as context)

**Verify:**
- [ ] System resolves "him" to "Vince 'Grease' Morrison"
- [ ] Exchange targets correct NPC
- [ ] No pronoun resolution errors

---

## Common Failure Modes to Check

### ❌ **NPC Name Parsing Failures:**
- [ ] Apostrophes in names (Vince 'Grease' Morrison)
- [ ] Nicknames in quotes
- [ ] Multiple word names
- [ ] Special characters

### ❌ **Time System Failures:**
- [ ] Time not advancing
- [ ] Time advancing by wrong amount
- [ ] Time advancing multiple times
- [ ] Time display not updating

### ❌ **Self-Effects Failures:**
- [ ] Self-effects showing "N/A"
- [ ] Empty self-effects array
- [ ] Missing self-effects for proactor
- [ ] Missing self-effects for reactor

### ❌ **Sympathy Failures:**
- [ ] Sympathy modifier not calculated
- [ ] Sympathy modifier wrong direction
- [ ] Sympathy not affecting difficulty

---

## Quick Test Commands

```bash
# Run quick exchange test
python QUICK_EXCHANGE_TEST.py

# Test social exchange
> I try to convince Vince to help me

# Test combat exchange
> I punch Vince

# Check status changes
> ua
> people

# Test multiple exchanges
> I shove Vince
> I punch Vince again
> I help Vince up

# Exit
> quit
```

---

## Expected Test Duration

- **Setup:** < 5 seconds
- **Single exchange test:** ~30 seconds
- **Complete verification:** ~5 minutes
- **Full exchange suite:** ~10 minutes

---

## Success Criteria

✅ **ALL of the following must pass:**

1. NPC detection works with complex names
2. Time advances correctly (3 seconds per exchange)
3. Self-effects always present (never "N/A")
4. Sympathy modifiers affect difficulty
5. Status changes applied to both actors
6. Knockout system triggers correctly
7. Success calculations shown transparently
8. Winner determined correctly
9. Margin affects outcome narrative
10. Multiple exchanges work consecutively

---

## If Any Test Fails

1. **Note the exact input** that caused failure
2. **Copy the error message** (if any)
3. **Check the terminal output** for debug info
4. **Verify the system components:**
   - ConductorAgent
   - InterpreterAgent
   - Exchange system
   - Time coordinator
   - Status system

---

## Integration with Main Simulation

Once all quick tests pass, verify in full simulation:

```bash
python MAIN/redesigned_main.py
```

1. Create new session
2. Select character
3. Wait for NPC to appear (or use scene with NPC)
4. Test same exchange actions
5. Verify all systems work in full context

---

## Status

- [ ] Quick test script created
- [ ] NPC detection verified
- [ ] Time advancement verified
- [ ] Self-effects verified
- [ ] Sympathy verified
- [ ] Status changes verified
- [ ] Knockout verified
- [ ] Full simulation verified

**Last Updated:** 2025-10-31
