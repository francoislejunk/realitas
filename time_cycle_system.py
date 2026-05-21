#!/usr/bin/env python3
"""
Day/Night Cycle and Time Tracking System for UTAS Simulation

This module implements a time tracking system that advances based on Rule of 3's
temporal categories to create a sense of time passage within scenes.
"""

from enum import Enum
from typing import Dict, Optional, Tuple
from dataclasses import dataclass
import json
from rule_of_3s import RuleOf3Category

class TimeOfDay(Enum):
    """Time of day periods with atmospheric descriptions"""
    DAWN = "dawn"
    MORNING = "morning"
    MIDDAY = "midday"
    AFTERNOON = "afternoon"
    DUSK = "dusk"
    EVENING = "evening"
    NIGHT = "night"
    LATE_NIGHT = "late_night"

@dataclass
class GameTime:
    """Represents the current time in the simulation"""
    hour: int
    minute: int
    day: int
    
    def __post_init__(self):
        """Normalize time values"""
        if self.minute >= 60:
            self.hour += self.minute // 60
            self.minute = self.minute % 60
        
        if self.hour >= 24:
            self.day += self.hour // 24
            self.hour = self.hour % 24
    
    def get_time_of_day(self) -> TimeOfDay:
        """Determine the current time of day period"""
        if 5 <= self.hour < 7:
            return TimeOfDay.DAWN
        elif 7 <= self.hour < 11:
            return TimeOfDay.MORNING
        elif 11 <= self.hour < 14:
            return TimeOfDay.MIDDAY
        elif 14 <= self.hour < 18:
            return TimeOfDay.AFTERNOON
        elif 18 <= self.hour < 20:
            return TimeOfDay.DUSK
        elif 20 <= self.hour < 22:
            return TimeOfDay.EVENING
        elif 22 <= self.hour < 24 or 0 <= self.hour < 2:
            return TimeOfDay.NIGHT
        else:
            return TimeOfDay.LATE_NIGHT
    
    def format_time(self) -> str:
        """Format time as readable string"""
        period = "AM" if self.hour < 12 else "PM"
        display_hour = self.hour if self.hour <= 12 else self.hour - 12
        if display_hour == 0:
            display_hour = 12
        return f"{display_hour}:{self.minute:02d} {period}"
    
    def format_full(self) -> str:
        """Format full time with day"""
        return f"Day {self.day}, {self.format_time()}"

class TimeCycleTracker:
    """Tracks time passage based on Rule of 3's temporal categories"""
    
    def __init__(self, starting_hour: int = 9, starting_minute: int = 0, starting_day: int = 1):
        """Initialize time tracker with starting time"""
        self.current_time = GameTime(starting_hour, starting_minute, starting_day)
        self.last_time_of_day = self.current_time.get_time_of_day()
        
        self.time_advancement = {
            RuleOf3Category.THREE_SECOND: 1,  # 1 minute (minimum time cost)
            RuleOf3Category.THREE_MINUTE: 3,  # 3 minutes
            RuleOf3Category.SLEEP: 120  # 2 hours minimum (nap), can be longer for full sleep
        }
    
    def advance_time(self, rule_of_3s_category: RuleOf3Category) -> Tuple[GameTime, bool]:
        """
        Advance time based on Rule of 3's category
        
        Args:
            rule_of_3s_category: The temporal category of the action
            
        Returns:
            Tuple of (new_time, time_of_day_changed)
        """
        minutes_to_add = self.time_advancement[rule_of_3s_category]
        
        previous_time_of_day = self.current_time.get_time_of_day()
        
        self.current_time.minute += minutes_to_add
        
        self.current_time = GameTime(
            self.current_time.hour,
            self.current_time.minute,
            self.current_time.day
        )
        
        new_time_of_day = self.current_time.get_time_of_day()
        time_of_day_changed = previous_time_of_day != new_time_of_day
        
        if time_of_day_changed:
            self.last_time_of_day = new_time_of_day
        
        return self.current_time, time_of_day_changed
    
    def get_current_time(self) -> GameTime:
        """Get the current game time"""
        return self.current_time
    
    def get_atmospheric_description(self) -> str:
        """Get atmospheric description for current time of day"""
        time_of_day = self.current_time.get_time_of_day()
        
        descriptions = {
            TimeOfDay.DAWN: "The sky lightens with the first hints of dawn, painting the horizon in soft pastels",
            TimeOfDay.MORNING: "The morning sun climbs higher, casting long shadows and warming the air",
            TimeOfDay.MIDDAY: "The sun reaches its zenith, bathing everything in bright, clear light",
            TimeOfDay.AFTERNOON: "The afternoon sun begins its descent, creating a golden warmth",
            TimeOfDay.DUSK: "Twilight approaches as the sun sinks low, painting the sky in brilliant oranges and purples",
            TimeOfDay.EVENING: "Evening settles in with deepening shadows and the first stars appearing",
            TimeOfDay.NIGHT: "Night has fallen, with darkness broken only by moonlight and artificial illumination",
            TimeOfDay.LATE_NIGHT: "The deep hours of night when most of the world sleeps in darkness"
        }
        
        return descriptions[time_of_day]
    
    def get_lighting_condition(self) -> str:
        """Get lighting condition for current time"""
        time_of_day = self.current_time.get_time_of_day()
        
        lighting = {
            TimeOfDay.DAWN: "Dim natural light",
            TimeOfDay.MORNING: "Bright natural light",
            TimeOfDay.MIDDAY: "Full daylight",
            TimeOfDay.AFTERNOON: "Good natural light",
            TimeOfDay.DUSK: "Fading light",
            TimeOfDay.EVENING: "Low light",
            TimeOfDay.NIGHT: "Darkness",
            TimeOfDay.LATE_NIGHT: "Deep darkness"
        }
        
        return lighting[time_of_day]
    
    def get_time_transition_narrative(self, previous_time_of_day: TimeOfDay, new_time_of_day: TimeOfDay) -> str:
        """Generate narrative for time of day transitions"""
        transitions = {
            (TimeOfDay.NIGHT, TimeOfDay.DAWN): "The darkness slowly gives way to the first light of dawn",
            (TimeOfDay.DAWN, TimeOfDay.MORNING): "Dawn blossoms into full morning as the sun rises",
            (TimeOfDay.MORNING, TimeOfDay.MIDDAY): "The morning advances into the bright heat of midday",
            (TimeOfDay.MIDDAY, TimeOfDay.AFTERNOON): "Midday passes into the golden hours of afternoon",
            (TimeOfDay.AFTERNOON, TimeOfDay.DUSK): "Afternoon fades as dusk begins to paint the sky",
            (TimeOfDay.DUSK, TimeOfDay.EVENING): "Dusk deepens into the quiet of evening",
            (TimeOfDay.EVENING, TimeOfDay.NIGHT): "Evening surrenders to the embrace of night",
            (TimeOfDay.NIGHT, TimeOfDay.LATE_NIGHT): "Night deepens into the small hours",
            (TimeOfDay.LATE_NIGHT, TimeOfDay.DAWN): "The darkest hour passes as dawn approaches"
        }
        
        return transitions.get(
            (previous_time_of_day, new_time_of_day),
            f"Time passes from {previous_time_of_day.value} to {new_time_of_day.value}"
        )
    
    def set_time(self, hour: int, minute: int = 0, day: Optional[int] = None) -> None:
        """Manually set the current time"""
        if day is None:
            day = self.current_time.day
        
        self.current_time = GameTime(hour, minute, day)
        self.last_time_of_day = self.current_time.get_time_of_day()
    
    def export_state(self) -> Dict:
        """Export time tracker state for saving"""
        return {
            "hour": self.current_time.hour,
            "minute": self.current_time.minute,
            "day": self.current_time.day,
            "last_time_of_day": self.last_time_of_day.value
        }
    
    def import_state(self, state: Dict) -> None:
        """Import time tracker state from save data"""
        self.current_time = GameTime(
            state["hour"],
            state["minute"],
            state["day"]
        )
        self.last_time_of_day = TimeOfDay(state["last_time_of_day"])

def get_time_display_name(time_of_day: TimeOfDay) -> str:
    """Get display-friendly name for time of day"""
    display_names = {
        TimeOfDay.DAWN: "Dawn",
        TimeOfDay.MORNING: "Morning", 
        TimeOfDay.MIDDAY: "Midday",
        TimeOfDay.AFTERNOON: "Afternoon",
        TimeOfDay.DUSK: "Dusk",
        TimeOfDay.EVENING: "Evening",
        TimeOfDay.NIGHT: "Night",
        TimeOfDay.LATE_NIGHT: "Late Night"
    }
    return display_names[time_of_day]

if __name__ == "__main__":
    tracker = TimeCycleTracker(9, 0, 1)
    
    print(f"Starting time: {tracker.get_current_time().format_full()}")
    print(f"Time of day: {get_time_display_name(tracker.get_current_time().get_time_of_day())}")
    print(f"Atmosphere: {tracker.get_atmospheric_description()}")
    print()
    
    actions = [
        ("I talk to the merchant", RuleOf3Category.THREE_MINUTE),
        ("I attack the bandit", RuleOf3Category.THREE_SECOND),
        ("I travel to the next city", RuleOf3Category.THREE_HOUR),
        ("I negotiate with the guard", RuleOf3Category.THREE_MINUTE),
        ("I set up camp", RuleOf3Category.THREE_HOUR)
    ]
    
    for action, category in actions:
        print(f"Action: {action} ({category.value})")
        new_time, time_changed = tracker.advance_time(category)
        print(f"Time: {new_time.format_full()}")
        
        if time_changed:
            print(f"🌅 TIME OF DAY CHANGED: {get_time_display_name(new_time.get_time_of_day())}")
            print(f"   {tracker.get_atmospheric_description()}")
        
        print(f"Lighting: {tracker.get_lighting_condition()}")
        print()
