# Diegetic NUA Introduction During ROAM - Analysis & Implementation

## 🎯 **YOUR QUESTION**

**"How does the simulation handle introducing NUA diegetically during ROAM outside of spark since let's say that we are following someone's fresh footprints that would mean that eventually if we follow enough we will get to a point where a NUA is introduced correct is this understood by the system already or we still need to implement this logic?"**

---

## 📊 **CURRENT STATE**

### **What the System HAS:**

**1. Dynamic Actor Detection (enhanced_dynamic_actor_system.py)**

```python
class EnhancedDynamicActorDetector:
    def detect_new_actor_mention(self, user_input: str):
        # Detects when user mentions a new actor
        # Examples:
        # - "I talk to the guard" → Creates guard NUA
        # - "I approach the bartender" → Creates bartender NUA
        # - "I follow the stranger" → Creates stranger NUA
```

**Detection Methods:**
- ✅ **Keyword-based**: "guard", "merchant", "stranger", "person"
- ✅ **Pattern-based**: "talk to X", "follow X", "approach X"
- ✅ **Action-triggered**: User explicitly mentions interacting with someone

**Integration Point (redesigned_main.py Lines 3001-3071):**
```python
# DYNAMIC ACTOR DETECTION: Check narrative for new actor mentions
detection = main._dynamic_actor_detector.detect_new_actor_mention(
    f"{user_input} {contextual_result}",
    existing_actors
)

if detection:
    actor_type = detection.get('type')
    actor_name = detection.get('name')
    
    if actor_type == 'NUA':
        # Create NUA using CreatorAgent
        new_nua = scene_creator.create_dynamic_nua(...)
        actor_manager.add_actor(new_nua, ActorRole.NUA)
```

---

## ❌ **WHAT THE SYSTEM LACKS**

### **Diegetic Clue-Based NUA Introduction:**

**Your Scenario:**
```
Turn 1: "I examine the ground"
Narrative: "You notice fresh footprints leading north..."

Turn 2: "I follow the footprints"
Narrative: "The trail continues, growing fresher..."

Turn 3: "I continue following"
Narrative: "You round a corner and spot a figure ahead..."
                    ↓
              ❌ NO NUA CREATED!
              
System doesn't understand that following clues should eventually
lead to discovering the source (a NUA).
```

**Missing Logic:**
1. **Clue Tracking**: System doesn't track that "footprints" imply a person
2. **Progressive Discovery**: No understanding that following clues → eventual encounter
3. **Diegetic Timing**: No logic for "when should the NUA appear?"
4. **Narrative Coherence**: Doesn't connect clues to their sources

---

## 🔧 **WHAT NEEDS TO BE IMPLEMENTED**

### **1. Clue-to-Actor Mapping System**

**Concept:**
```python
class DiegeticClueTracker:
    """
    Tracks environmental clues that imply the presence of actors.
    """
    
    clue_types = {
        'footprints': {
            'implies': 'NUA',
            'discovery_threshold': 2-3 actions,
            'keywords': ['footprints', 'tracks', 'trail', 'footsteps']
        },
        'voices': {
            'implies': 'NUA',
            'discovery_threshold': 1-2 actions,
            'keywords': ['voices', 'talking', 'conversation', 'shouting']
        },
        'fresh_blood': {
            'implies': 'NUA (injured)',
            'discovery_threshold': 2-3 actions,
            'keywords': ['blood trail', 'fresh blood', 'bleeding']
        },
        'smoke': {
            'implies': 'NUA (campfire/cooking)',
            'discovery_threshold': 2-3 actions,
            'keywords': ['smoke', 'campfire', 'cooking smell']
        }
    }
```

### **2. Progressive Discovery System**

**Concept:**
```python
class ProgressiveDiscoveryTracker:
    """
    Tracks how many times player has followed a clue.
    Introduces NUA when threshold reached.
    """
    
    def __init__(self):
        self.active_clues = {}  # {clue_id: {type, follow_count, threshold}}
    
    def register_clue(self, clue_type: str, narrative: str):
        """
        Called when narrative mentions a clue.
        Example: "fresh footprints leading north"
        """
        clue_id = f"{clue_type}_{timestamp}"
        self.active_clues[clue_id] = {
            'type': clue_type,
            'follow_count': 0,
            'threshold': self._get_threshold(clue_type),
            'first_mentioned': narrative
        }
    
    def track_follow_action(self, user_input: str, clue_id: str):
        """
        Called when player follows a clue.
        Example: "I follow the footprints"
        """
        if clue_id in self.active_clues:
            self.active_clues[clue_id]['follow_count'] += 1
            
            # Check if threshold reached
            if self._should_introduce_actor(clue_id):
                return self._create_introduction_context(clue_id)
        
        return None
    
    def _should_introduce_actor(self, clue_id: str) -> bool:
        """Determine if it's time to introduce the NUA."""
        clue = self.active_clues[clue_id]
        return clue['follow_count'] >= clue['threshold']
    
    def _create_introduction_context(self, clue_id: str) -> dict:
        """
        Create context for NUA introduction.
        """
        clue = self.active_clues[clue_id]
        return {
            'trigger': 'progressive_discovery',
            'clue_type': clue['type'],
            'follow_count': clue['follow_count'],
            'introduction_style': 'gradual_reveal',  # vs 'sudden_encounter'
            'suggested_nua_type': self._infer_nua_type(clue['type'])
        }
```

### **3. Narrative Integration**

**Concept:**
```python
# In narrator_agent.py or new diegetic_introduction_agent.py

def generate_progressive_discovery_narrative(
    clue_type: str,
    follow_count: int,
    threshold: int,
    introduce_now: bool
) -> str:
    """
    Generate narrative that builds tension toward NUA introduction.
    """
    
    if follow_count == 1:
        # First follow: Establish the trail
        return f"The {clue_type} lead deeper into the area, still fresh..."
    
    elif follow_count < threshold:
        # Middle follows: Build tension
        progress = follow_count / threshold
        if progress < 0.5:
            return f"The {clue_type} continue, growing more distinct..."
        else:
            return f"The {clue_type} are very fresh now. You sense you're getting close..."
    
    else:
        # Threshold reached: Introduce NUA
        if introduce_now:
            return f"You round a corner and spot the source of the {clue_type}: a figure ahead..."
        else:
            return f"The {clue_type} lead around a corner. You hear movement nearby..."
```

---

## 🎮 **EXAMPLE FLOW**

### **Scenario: Following Footprints**

```
Turn 1: "I examine the ground"
Narrative: "You notice fresh footprints in the dust, leading toward the warehouse."

[SYSTEM] DiegeticClueTracker.register_clue('footprints', narrative)
         → clue_id: "footprints_001"
         → threshold: 3 actions
         → follow_count: 0

---

Turn 2: "I follow the footprints"
Narrative: "The trail continues through the debris, still fresh. Whoever made these 
           tracks passed through here recently."

[SYSTEM] ProgressiveDiscoveryTracker.track_follow_action('footprints_001')
         → follow_count: 1 / 3
         → Status: Continue tracking

---

Turn 3: "I keep following the trail"
Narrative: "The footprints grow more distinct, the dust barely settled. You sense 
           you're getting close to whoever left them."

[SYSTEM] ProgressiveDiscoveryTracker.track_follow_action('footprints_001')
         → follow_count: 2 / 3
         → Status: Almost there...

---

Turn 4: "I continue following"
Narrative: "You round a corner and spot a figure crouched near a stack of crates, 
           their back to you. They haven't noticed you yet."

[SYSTEM] ProgressiveDiscoveryTracker.track_follow_action('footprints_001')
         → follow_count: 3 / 3 ✅ THRESHOLD REACHED!
         → create_introduction_context()
         → EnhancedDynamicActorDetector.create_nua_from_context()
         → NUA Created: "Mysterious Figure"
         → Mode: Still ROAM (not SPARK yet - just discovered)

---

Turn 5: "I approach them"
[SYSTEM] Now transitions to SPARK mode (player initiated contact)
```

---

## 🔧 **IMPLEMENTATION PLAN**

### **Phase 1: Clue Detection**

**File: diegetic_clue_tracker.py (NEW)**

```python
class DiegeticClueTracker:
    """Detects and tracks environmental clues in narratives."""
    
    def analyze_narrative_for_clues(self, narrative: str) -> List[Dict]:
        """
        Scan narrative for clues that imply actor presence.
        Returns list of detected clues with metadata.
        """
        detected_clues = []
        
        for clue_type, config in self.clue_types.items():
            for keyword in config['keywords']:
                if keyword in narrative.lower():
                    detected_clues.append({
                        'type': clue_type,
                        'keyword': keyword,
                        'implies': config['implies'],
                        'threshold': config['discovery_threshold'],
                        'narrative_context': narrative
                    })
        
        return detected_clues
```

### **Phase 2: Progressive Discovery**

**File: progressive_discovery_system.py (NEW)**

```python
class ProgressiveDiscoverySystem:
    """Manages the progression from clue to actor introduction."""
    
    def __init__(self):
        self.active_discoveries = {}
        self.clue_tracker = DiegeticClueTracker()
    
    def process_turn(self, user_input: str, narrative: str):
        """
        Called each turn to check for clue progression.
        """
        # 1. Detect new clues in narrative
        new_clues = self.clue_tracker.analyze_narrative_for_clues(narrative)
        for clue in new_clues:
            self.register_new_clue(clue)
        
        # 2. Check if user is following an active clue
        for discovery_id, discovery in self.active_discoveries.items():
            if self._is_following_clue(user_input, discovery):
                discovery['follow_count'] += 1
                
                # 3. Check if threshold reached
                if discovery['follow_count'] >= discovery['threshold']:
                    return self._trigger_actor_introduction(discovery)
        
        return None
```

### **Phase 3: Integration with Main Loop**

**File: redesigned_main.py**

```python
# After dynamic actor detection (around line 3071)

# PROGRESSIVE DISCOVERY: Check if following clues leads to NUA
try:
    if not hasattr(main, '_progressive_discovery'):
        from progressive_discovery_system import ProgressiveDiscoverySystem
        main._progressive_discovery = ProgressiveDiscoverySystem()
    
    introduction_context = main._progressive_discovery.process_turn(
        user_input, contextual_result
    )
    
    if introduction_context:
        print(f"{Color.SYSTEM}[DISCOVERY] Clue trail leads to actor introduction!{Color.RESET}")
        
        # Create NUA based on discovery context
        nua_hint = introduction_context.get('suggested_nua_type', 'mysterious figure')
        new_nua = scene_creator.create_dynamic_nua(
            {'name': nua_hint},
            scene_description,
            introduction_context
        )
        
        if new_nua:
            actor_manager.add_actor(new_nua, ActorRole.NUA)
            print(f"{Color.SUCCESS}✓ Discovered: {new_nua.sheet.name}{Color.RESET}")

except Exception as e:
    print(f"{Color.WARNING}[DISCOVERY] Progressive discovery failed: {e}{Color.RESET}")
```

---

## 🏆 **RESULT**

### **Current System:**
```
✅ Detects explicit actor mentions ("I talk to the guard")
❌ Doesn't understand clue-based discovery
❌ No progressive revelation mechanics
❌ Can't track "following footprints → find person"
```

### **After Implementation:**
```
✅ Detects explicit actor mentions
✅ Tracks environmental clues (footprints, voices, etc.)
✅ Progressive discovery with thresholds
✅ Diegetic NUA introduction based on player investigation
✅ Natural story flow from clue → discovery → interaction
```

---

## 📝 **ANSWER TO YOUR QUESTION**

**"is this understood by the system already or we still need to implement this logic?"**

**Answer:** **We still need to implement this logic!**

**Current State:**
- ✅ System CAN create NPCs when explicitly mentioned
- ❌ System CANNOT track clues that lead to NPCs
- ❌ System CANNOT do progressive discovery
- ❌ System CANNOT understand "following footprints eventually leads to finding someone"

**What's Needed:**
1. **DiegeticClueTracker** - Detect clues in narratives
2. **ProgressiveDiscoverySystem** - Track follow actions and trigger introductions
3. **Integration** - Connect to main loop and dynamic actor system

**This would enable truly diegetic NUA introduction during ROAM mode, where players discover NPCs through investigation rather than random spawns! 🎯**
