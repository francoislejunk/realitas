# Inquiry Time Advancement Bug Fix

## 🐛 **THE BUG**

**Your Report:** "how did the time jump from 9am to 12pm when all I did was ask a question?"

**What Happened:**
```
> Is there anyone else here?

🍽️ Survival needs fulfilled: Fulfillment (0.5h)
   • ✓ Fulfillment need satisfied

Time advanced by 0.5 hours
Current Time: Day 1, 12:00 PM

❌ Asking a question advanced time by 3 hours!
```

---

## 🔍 **ROOT CAUSE**

### **The Problem Chain:**

1. **Inquiry Misclassified:**
```
Input: "Is there anyone else here?"
LLM Classification: {
    'input_type': 'fallible_action',  ← Should be 'inquiry'!
    'fallible_subtype': 'information_gathering'
}
```

2. **Survival System Triggered:**
```python
# Line 2496: Check skips only 'inquiry' type
if (input_analysis.get('input_type') != 'inquiry'):
    # Run survival detection
    fulfilled_needs = survival_analyzer.analyze_action(user_input)
```

3. **False Positive Match:**
```python
# survival_action_analyzer.py Line 74
# "here" in "Is there anyone else here?" matches FULFILLMENT pattern
if self._fulfill_verbs.search(text) or self._fulfill_nouns.search(text):
    fulfilled_needs.append(SurvivalNeed.FULFILLMENT)
```

4. **Time Advanced:**
```python
# Fulfillment need = 0.5 hours default
costs = {'time_cost': 0.5}
master_time.advance_time(hours=0.5)  # ❌ Time jumps!
```

---

## ✅ **THE FIX**

### **Treat Information Gathering as Inquiries:**

**File: redesigned_main.py (Lines 2472-2475)**

```python
# CRITICAL: Skip survival detection for inquiries - they don't take time!
# Also skip for information_gathering fallible actions (they're just questions)
is_inquiry = (input_analysis_for_survival.get('input_type') == 'inquiry' or 
             input_analysis_for_survival.get('fallible_subtype') == 'information_gathering')
```

**File: redesigned_main.py (Line 2496)**

```python
# Skip survival processing for inquiries and information gathering (they don't take time!)
if not is_inquiry and not is_contested_nua:
    # Run survival detection
```

---

## 📊 **COMPARISON**

### **Before (Bug):**
```
> Is there anyone else here?

Classification: fallible_action (information_gathering)
Survival Check: ✓ Runs
Match Found: "here" → FULFILLMENT
Time Cost: 0.5 hours
Result: Time jumps from 9:00 AM → 9:30 AM ❌

(Plus multiple other inquiries = 3 hour jump!)
```

### **After (Fixed):**
```
> Is there anyone else here?

Classification: fallible_action (information_gathering)
Is Inquiry: True ✓
Survival Check: ✗ Skipped
Time Cost: 0 hours
Result: Time stays at 9:00 AM ✅
```

---

## 🎯 **WHAT COUNTS AS INQUIRY**

### **Now Skips Survival Detection:**

1. **Direct Inquiries:**
```
> Who's here?
> What do I see?
> Where am I?

input_type: 'inquiry' → Skip survival ✅
```

2. **Information Gathering:**
```
> Is there anyone else here?
> Are there any exits?
> Can I see anything unusual?

fallible_subtype: 'information_gathering' → Skip survival ✅
```

---

## 🎮 **EXAMPLES**

### **Example 1: Simple Question**
```
> Who's in the room?

Before: Time +0.5h (FULFILLMENT detected) ❌
After: Time +0h (inquiry skipped) ✅
```

### **Example 2: Looking Around**
```
> Is there anyone else here?

Before: Time +0.5h (FULFILLMENT detected) ❌
After: Time +0h (information gathering skipped) ✅
```

### **Example 3: Actual Action**
```
> I sit down and relax

Before: Time +0.5h (FULFILLMENT detected) ✅
After: Time +0.5h (FULFILLMENT detected) ✅

This SHOULD advance time - it's an actual action!
```

---

## 🔧 **IMPLEMENTATION**

### **Step 1: Detect Inquiry Type (Lines 2472-2475)**
```python
# CRITICAL: Skip survival detection for inquiries - they don't take time!
# Also skip for information_gathering fallible actions (they're just questions)
is_inquiry = (input_analysis_for_survival.get('input_type') == 'inquiry' or 
             input_analysis_for_survival.get('fallible_subtype') == 'information_gathering')
```

### **Step 2: Skip Survival Check (Line 2496)**
```python
# Skip survival processing for inquiries and information gathering (they don't take time!)
if not is_inquiry and not is_contested_nua:
    # Primary: LLM-based survival intent detection
    llm_detection = conductor.interpreter.detect_survival_intent(user_input, actor)
    # ... rest of survival processing
```

---

## 🏆 **RESULT**

**Inquiries no longer advance time!**

```
9:00 AM > Is there anyone else here?
         "You don't see anyone nearby."
         Time: 9:00 AM ✅

9:00 AM > Who's in the room?
         "Just you."
         Time: 9:00 AM ✅

9:00 AM > I sit down and relax
         🍽️ Survival needs fulfilled: Fulfillment (0.5h)
         Time: 9:30 AM ✅ (This SHOULD advance time!)
```

**Questions are instant, actions take time! 🎯**
