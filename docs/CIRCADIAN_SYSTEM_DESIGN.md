# Circadian System: Design Document

## Overview

The circadian system models how **time of day affects human performance, mood, and behavior**. It's one of the most fundamental aspects of reality that games typically ignore.

## The Science (Simplified)

Humans have a ~24-hour biological clock that affects:
- **Alertness** - Peaks mid-morning, dips after lunch, crashes late night
- **Cognitive Performance** - Best for complex tasks 10am-12pm
- **Physical Performance** - Peaks late afternoon (4-6pm)
- **Mood** - Generally better in morning, can dip evening
- **Reaction Time** - Worst 3-5am (accident peak)

```
ALERTNESS CURVE (typical person)

High  │          ╭──╮
      │         ╱    ╲         ╭──╮
      │        ╱      ╲       ╱    ╲
      │       ╱        ╲     ╱      ╲
      │      ╱          ╲   ╱        ╲
      │     ╱            ╲ ╱          ╲
Low   │────╱              ╳            ╲────
      └────┬────┬────┬────┬────┬────┬────┬────
          6am  9am  12pm 3pm  6pm  9pm  12am 3am
                    
           Wake Peak  Dip  2nd   Wind  Sleep
                     (lunch) Peak  Down  Zone
```

## Performance Modifiers by Time

| Time Block | Alertness | Cognitive | Physical | Mood |
|------------|-----------|-----------|----------|------|
| 6-9am (Wake) | Rising | Low→Med | Low | Neutral |
| 9am-12pm (Peak) | **High** | **High** | Medium | Good |
| 12-3pm (Post-Lunch) | **Dip** | Low | Medium | Neutral |
| 3-6pm (2nd Peak) | High | Medium | **High** | Good |
| 6-9pm (Evening) | Declining | Medium | Medium | Variable |
| 9pm-12am (Wind Down) | Low | Low | Low | Tired |
| 12-6am (Sleep Zone) | **Crash** | **Very Low** | **Very Low** | Impaired |

## Implementation Components

### 1. Time-of-Day Modifiers

```python
def get_circadian_modifier(hour: int, skill_type: str) -> int:
    """
    Returns modifier (-2 to +1) based on time and skill type.
    
    skill_type: 'cognitive', 'physical', 'social', 'perception'
    """
    
    if skill_type == 'cognitive':
        # Best: 9am-12pm, Worst: 2-5am
        if 9 <= hour < 12:
            return +1  # Peak mental performance
        elif 12 <= hour < 15:
            return -1  # Post-lunch dip
        elif 2 <= hour < 6:
            return -2  # Sleep deprivation zone
        else:
            return 0
            
    elif skill_type == 'physical':
        # Best: 3-6pm, Worst: 3-6am
        if 15 <= hour < 18:
            return +1  # Peak physical performance
        elif 3 <= hour < 6:
            return -2  # Body at lowest
        else:
            return 0
```

### 2. Sleep Debt Tracker

```python
class SleepDebtTracker:
    """
    Tracks sleep debt and its effects on performance.
    
    Humans need ~7-8 hours of sleep per 24-hour period.
    Missing sleep accumulates as "debt" that impairs function.
    """
    
    def __init__(self):
        self.hours_awake: float = 0.0
        self.sleep_debt_hours: float = 0.0
        self.last_sleep_quality: str = "normal"
    
    def get_fatigue_level(self) -> str:
        """
        Returns fatigue level based on hours awake + sleep debt.
        
        0-12 hours awake: Alert
        12-16 hours: Tired
        16-20 hours: Exhausted (equivalent to 0.05% BAC)
        20-24 hours: Severely Impaired (equivalent to 0.10% BAC)
        24+ hours: Dangerous (hallucinations possible)
        """
        effective_hours = self.hours_awake + (self.sleep_debt_hours * 0.5)
        
        if effective_hours < 12:
            return "alert"
        elif effective_hours < 16:
            return "tired"
        elif effective_hours < 20:
            return "exhausted"
        elif effective_hours < 24:
            return "severely_impaired"
        else:
            return "dangerous"
    
    def get_performance_modifier(self) -> int:
        """Modifier to all checks based on fatigue."""
        fatigue = self.get_fatigue_level()
        return {
            "alert": 0,
            "tired": -1,
            "exhausted": -2,
            "severely_impaired": -3,
            "dangerous": -4
        }.get(fatigue, 0)
```

### 3. Narrative Integration

```python
def get_circadian_narrative_flavor(hour: int, fatigue_level: str) -> dict:
    """Get narrative elements based on time and fatigue."""
    
    flavor = {
        "perception_quality": "normal",
        "internal_voice_tone": "neutral",
        "physical_sensations": [],
        "cognitive_effects": []
    }
    
    # Time-based perception
    if 2 <= hour < 6:
        flavor["perception_quality"] = "hazy"
        flavor["physical_sensations"].append("The world has that 3am unreality to it")
        
    # Fatigue effects
    if fatigue_level == "tired":
        flavor["physical_sensations"].append("Your eyelids feel heavy")
        flavor["internal_voice_tone"] = "sluggish"
        
    elif fatigue_level == "exhausted":
        flavor["perception_quality"] = "tunneled"
        flavor["physical_sensations"].extend([
            "Your eyes burn",
            "Everything feels slightly distant"
        ])
        flavor["cognitive_effects"].append("Thoughts come slower")
        
    elif fatigue_level == "severely_impaired":
        flavor["perception_quality"] = "fragmented"
        flavor["physical_sensations"].extend([
            "Your body aches for sleep",
            "Micro-sleeps threaten at the edges"
        ])
        flavor["cognitive_effects"].extend([
            "You keep losing your train of thought",
            "Simple decisions feel monumental"
        ])
    
    return flavor
```

## Example Gameplay Impact

**Morning (9am, well-rested):**
```
🎬 SCENE DESCRIPTION:
The morning light cuts sharp through the warehouse windows. Your mind 
feels clear, focused. The coffee's still hot.

📊 Status: Alert | Cognitive +1 | Physical +0
```

**Afternoon (2pm, post-lunch):**
```
🎬 SCENE DESCRIPTION:
The afternoon sun beats down. There's that familiar post-lunch heaviness 
settling in. The paperwork blurs slightly.

📊 Status: Alert | Cognitive -1 (post-lunch dip) | Physical +0
💭 Could use another coffee...
```

**Late Night (3am, been awake 20 hours):**
```
🎬 SCENE DESCRIPTION:
The fluorescent lights hum. Everything has that 3am unreality—sounds too 
loud, shadows too deep. Your eyes burn. You keep losing your train of 
thought mid-sentence.

📊 Status: Exhausted | All checks -2
⚠️ Fatigue is impairing your judgment. Consider resting.
💭 Just need to... what was I doing?
```

## Integration Points

1. **Time System** - Hook into existing time tracker
2. **Skill Checks** - Apply circadian modifiers
3. **Scene Descriptions** - Inject fatigue-aware narrative
4. **NPC Schedules** - People aren't always available
5. **Internal Voice** - Fatigue-aware thoughts
6. **Recovery System** - Sleep quality affects debt payoff
7. **Stimulants** - Coffee/drugs temporarily mask fatigue (with crash)

## Future Enhancements

- Individual chronotypes (morning person vs night owl)
- Jet lag simulation for time zone changes
- Seasonal variation (shorter days = earlier fatigue)
- Age-based differences in sleep needs
- Medication/substance interactions
