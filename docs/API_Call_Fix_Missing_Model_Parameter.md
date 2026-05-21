# API Call Fix: Missing Model Parameter

## 🐛 **BUG IDENTIFIED**

**Error Messages:**
```
Failed to extract context: Missing required arguments; Expected either ('messages' and 'model') or ('messages', 'model' and 'stream') arguments to be given
Failed to interpret user intent: Missing required arguments; Expected either ('messages' and 'model') or ('messages', 'model' and 'stream') arguments to be given
```

**Root Cause:**
Multiple LLM API calls in the enhanced narrative loop system were missing the required `model` parameter.

---

## ✅ **SOLUTION IMPLEMENTED**

### **Files Fixed:**

#### **1. llm_agents/enhanced_narrative_loop.py** ✅

**Two API calls fixed:**

##### **UserIntentInterpreter._interpret_user_intent() - Line 193-201:**
```python
# BEFORE (BROKEN):
response = self.llm_client.chat.completions.create(
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},
    temperature=0.3,
    max_tokens=300
)

# AFTER (FIXED):
from openrouter_config import OpenRouterConfig
model = OpenRouterConfig.get_model_for_role("interpretation")
response = self.llm_client.chat.completions.create(
    model=model,  # ← ADDED
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},
    temperature=0.3,
    max_tokens=300
)
```

##### **ContextTracker._extract_context_from_scene() - Line 399-407:**
```python
# BEFORE (BROKEN):
response = self.llm_client.chat.completions.create(
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},
    temperature=0.2,
    max_tokens=300
)

# AFTER (FIXED):
from openrouter_config import OpenRouterConfig
model = OpenRouterConfig.get_model_for_role("interpretation")
response = self.llm_client.chat.completions.create(
    model=model,  # ← ADDED
    messages=[{"role": "user", "content": prompt}],
    response_format={"type": "json_object"},
    temperature=0.2,
    max_tokens=300
)
```

---

#### **2. llm_agents/diegetic_momentum_tracker.py** ✅

**Three API calls fixed:**

##### **DiegeticMomentumTracker._analyze_scene_energy() - Line 134-142:**
```python
# BEFORE (BROKEN):
from openrouter_config import create_role_client
client = create_role_client("analysis")
response = client.chat.completions.create(
    messages=[{"role": "user", "content": prompt}],
    max_tokens=10,
    temperature=0.3
)

# AFTER (FIXED):
from openrouter_config import create_role_client, OpenRouterConfig
client = create_role_client("analysis")
model = OpenRouterConfig.get_model_for_role("analysis")  # ← ADDED
response = client.chat.completions.create(
    model=model,  # ← ADDED
    messages=[{"role": "user", "content": prompt}],
    max_tokens=10,
    temperature=0.3
)
```

##### **DiegeticMomentumTracker._analyze_user_motivation() - Line 186-195:**
```python
# BEFORE (BROKEN):
from openrouter_config import create_role_client
client = create_role_client("analysis")

response = client.chat.completions.create(
    messages=[{"role": "user", "content": prompt}],
    max_tokens=10,
    temperature=0.3
)

# AFTER (FIXED):
from openrouter_config import create_role_client, OpenRouterConfig
client = create_role_client("analysis")
model = OpenRouterConfig.get_model_for_role("analysis")  # ← ADDED

response = client.chat.completions.create(
    model=model,  # ← ADDED
    messages=[{"role": "user", "content": prompt}],
    max_tokens=10,
    temperature=0.3
)
```

##### **DiegeticMomentumTracker._analyze_social_momentum() - Line 249-258:**
```python
# BEFORE (BROKEN):
from openrouter_config import create_role_client
client = create_role_client("analysis")

response = client.chat.completions.create(
    messages=[{"role": "user", "content": prompt}],
    max_tokens=10,
    temperature=0.3
)

# AFTER (FIXED):
from openrouter_config import create_role_client, OpenRouterConfig
client = create_role_client("analysis")
model = OpenRouterConfig.get_model_for_role("analysis")  # ← ADDED

response = client.chat.completions.create(
    model=model,  # ← ADDED
    messages=[{"role": "user", "content": prompt}],
    max_tokens=10,
    temperature=0.3
)
```

---

## 📊 **SUMMARY**

### **Total Fixes: 5 API calls**

| File | Method | Line | Role |
|------|--------|------|------|
| enhanced_narrative_loop.py | _interpret_user_intent() | 193-201 | interpretation |
| enhanced_narrative_loop.py | _extract_context_from_scene() | 399-407 | interpretation |
| diegetic_momentum_tracker.py | _analyze_scene_energy() | 134-142 | analysis |
| diegetic_momentum_tracker.py | _analyze_user_motivation() | 186-195 | analysis |
| diegetic_momentum_tracker.py | _analyze_social_momentum() | 249-258 | analysis |

---

## 🎯 **WHY THIS HAPPENED**

The OpenRouter API requires **both** `messages` and `model` parameters for all API calls. These methods were:
1. Creating the client correctly
2. Passing messages correctly
3. **BUT** forgetting to specify which model to use

The error was silent in development but caused runtime failures when these specific code paths were executed.

---

## ✅ **VERIFICATION**

### **How to Test:**
1. Run the simulation in ROAM mode
2. Perform exploration actions
3. Check for these error messages (should NOT appear):
   - ❌ "Failed to extract context"
   - ❌ "Failed to interpret user intent"

### **Expected Behavior:**
- ✅ User intent interpretation works
- ✅ Context extraction from scenes works
- ✅ Scene energy analysis works
- ✅ User motivation analysis works
- ✅ Social momentum analysis works

---

## 🔍 **PATTERN TO AVOID**

### **❌ WRONG (Missing model):**
```python
response = client.chat.completions.create(
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3
)
```

### **✅ CORRECT (With model):**
```python
from openrouter_config import OpenRouterConfig
model = OpenRouterConfig.get_model_for_role("role_name")
response = client.chat.completions.create(
    model=model,  # ← REQUIRED
    messages=[{"role": "user", "content": prompt}],
    temperature=0.3
)
```

---

## 🎉 **RESULT**

**All API calls now properly include the `model` parameter!**

The enhanced narrative loop system should now work without errors:
- ✅ User intent interpretation functional
- ✅ Context extraction functional
- ✅ Momentum tracking functional
- ✅ All LLM-based analysis systems operational

**The simulation should run without "Missing required arguments" errors! 🚀**
