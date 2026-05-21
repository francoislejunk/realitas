"""
Outlier NUA Stats Display System

Highlights exceptional or unusual stats when introducing NUAs (Non-User Actors), 
making their capabilities immediately clear to the player. Shows outlier S-factors, 
skills, and supernatural abilities.
"""

from typing import Dict, List, Tuple, Optional
from actor_sheet import ActorSheet, SFactorType, StatusType
from color_utils import Color
from narrative_utils import get_narrative_descriptor


class OutlierStatsAnalyzer:
    """Analyzes actor stats to identify outliers and exceptional capabilities"""
    
    # Thresholds for outlier detection
    OUTLIER_HIGH_THRESHOLD = 4  # S-factors/skills >= 4 are exceptional
    OUTLIER_LOW_THRESHOLD = 0   # S-factors/skills = 0 are notable weaknesses
    
    def __init__(self):
        pass
    
    def analyze_s_factors(self, actor_sheet: ActorSheet) -> Dict[str, List[Tuple[str, int, str]]]:
        """
        Analyze S-factors for outliers
        
        Returns dict with 'strengths' and 'weaknesses' lists of (name, value, descriptor) tuples
        """
        strengths = []
        weaknesses = []
        
        for s_factor_type in SFactorType:
            value = actor_sheet.s_factors.get_factor(s_factor_type)
            descriptor = get_narrative_descriptor(value)
            
            if value >= self.OUTLIER_HIGH_THRESHOLD:
                strengths.append((s_factor_type.name.capitalize(), value, descriptor))
            elif value <= self.OUTLIER_LOW_THRESHOLD:
                weaknesses.append((s_factor_type.name.capitalize(), value, descriptor))
        
        return {
            'strengths': strengths,
            'weaknesses': weaknesses
        }
    
    def analyze_skills(self, actor_sheet: ActorSheet, top_n: int = 3) -> List[Tuple[str, int, str]]:
        """
        Get top N skills
        
        Returns list of (skill_name, value, descriptor) tuples
        """
        if not actor_sheet.skills:
            return []
        
        # Sort skills by value
        sorted_skills = sorted(actor_sheet.skills.items(), key=lambda x: x[1], reverse=True)
        
        # Get top N exceptional skills (value >= 3)
        exceptional_skills = [
            (name, value, get_narrative_descriptor(value))
            for name, value in sorted_skills[:top_n]
            if value >= 3
        ]
        
        return exceptional_skills
    
    def analyze_supers(self, actor_sheet: ActorSheet) -> List[Tuple[str, int, str]]:
        """
        Get all endowment abilities
        
        Returns list of (endowment_name, value, descriptor) tuples
        """
        endowments = getattr(actor_sheet, 'endowments', {})
        
        res = []
        if endowments:
            from narrative_utils import get_narrative_descriptor
            for name, val in endowments.items():
                if val > 0:
                    res.append((name, val, get_narrative_descriptor(val)))
        return res
    
    def get_threat_level(self, actor_sheet: ActorSheet) -> Tuple[str, str]:
        """
        Calculate overall threat level based on stats
        
        Returns (threat_level, description) tuple
        """
        # Calculate average combat-relevant stats
        combat_factors = [
            actor_sheet.s_factors.get_factor(SFactorType.SWIFTNESS),
            actor_sheet.s_factors.get_factor(SFactorType.STURDINESS),
            actor_sheet.s_factors.get_factor(SFactorType.SHADOW)
        ]
        
        avg_combat = sum(combat_factors) / len(combat_factors)
        
        # Check for endowments
        has_endowments = bool(getattr(actor_sheet, 'endowments', {}))
        
        # Calculate threat level
        if avg_combat >= 4.0 or has_endowments:
            return ("CRITICAL", "Extremely dangerous opponent")
        elif avg_combat >= 3.5:
            return ("HIGH", "Formidable adversary")
        elif avg_combat >= 2.5:
            return ("MODERATE", "Capable combatant")
        elif avg_combat >= 1.5:
            return ("LOW", "Average threat")
        else:
            return ("MINIMAL", "Limited combat capability")


class OutlierStatsDisplay:
    """Displays outlier stats in a visually appealing format"""
    
    def __init__(self):
        self.analyzer = OutlierStatsAnalyzer()
    
    def display_nua_introduction(self, actor_sheet: ActorSheet, context: Optional[str] = None):
        """
        Display NUA introduction with outlier stats highlighted
        
        Args:
            actor_sheet: The NUA's actor sheet
            context: Optional narrative context for the introduction
        """
        name = actor_sheet.name
        occupation = getattr(actor_sheet, 'occupation', 'Unknown')
        
        print(f"\n{Color.HEADER}{'═' * 70}{Color.RESET}")
        print(f"{Color.SUCCESS}⚔️  NEW ACTOR DETECTED: {name.upper()}{Color.RESET}")
        print(f"{Color.HEADER}{'═' * 70}{Color.RESET}\n")
        
        # Basic info
        print(f"{Color.INFO}Occupation:{Color.RESET} {occupation}")
        
        if context:
            print(f"{Color.INFO}Context:{Color.RESET} {context}\n")
        else:
            print()
        
        # Analyze stats
        s_factor_analysis = self.analyzer.analyze_s_factors(actor_sheet)
        exceptional_skills = self.analyzer.analyze_skills(actor_sheet, top_n=3)
        supers = self.analyzer.analyze_supers(actor_sheet)
        threat_level, threat_desc = self.analyzer.get_threat_level(actor_sheet)
        
        # Display outlier S-factors
        if s_factor_analysis['strengths']:
            print(f"{Color.SUCCESS}💪 EXCEPTIONAL CAPABILITIES:{Color.RESET}")
            for name, value, descriptor in s_factor_analysis['strengths']:
                bar = "█" * value + "░" * (5 - value)
                print(f"  {name:12} [{bar}] {descriptor} ({value})")
            print()
        
        if s_factor_analysis['weaknesses']:
            print(f"{Color.ERROR}⚠️  NOTABLE WEAKNESSES:{Color.RESET}")
            for name, value, descriptor in s_factor_analysis['weaknesses']:
                bar = "█" * value + "░" * (5 - value)
                print(f"  {name:12} [{bar}] {descriptor} ({value})")
            print()
        
        # Display exceptional skills
        if exceptional_skills:
            print(f"{Color.WARNING}🎯 KEY SKILLS:{Color.RESET}")
            for skill_name, value, descriptor in exceptional_skills:
                bar = "█" * value + "░" * (5 - value)
                print(f"  {skill_name:20} [{bar}] {descriptor} ({value})")
            print()
        
        # Display endowment abilities
        if endowments:
            print(f"{Color.HEADER}✨ ENDOWMENT ABILITIES:{Color.RESET}")
            for endowment_name, value, descriptor in endowments:
                bar = "█" * value + "░" * (5 - value)
                print(f"  {endowment_name:20} [{bar}] {descriptor} ({value})")
            print()
        
        # Display threat assessment
        threat_color = {
            "CRITICAL": Color.ERROR,
            "HIGH": Color.WARNING,
            "MODERATE": Color.INFO,
            "LOW": Color.SUCCESS,
            "MINIMAL": Color.SYSTEM
        }.get(threat_level, Color.INFO)
        
        print(f"{threat_color}⚔️  THREAT ASSESSMENT: {threat_level}{Color.RESET}")
        print(f"{Color.INFO}   {threat_desc}{Color.RESET}\n")
        
        print(f"{Color.HEADER}{'═' * 70}{Color.RESET}\n")
    
    def display_compact_outliers(self, actor_sheet: ActorSheet) -> str:
        """
        Generate a compact one-line summary of outlier stats
        
        Returns formatted string for inline display
        """
        s_factor_analysis = self.analyzer.analyze_s_factors(actor_sheet)
        supers = self.analyzer.analyze_supers(actor_sheet)
        
        parts = []
        
        # Add exceptional S-factors
        if s_factor_analysis['strengths']:
            strength_names = [name for name, _, _ in s_factor_analysis['strengths']]
            parts.append(f"High {', '.join(strength_names)}")
        
        # Add endowments
        if endowments:
            endowment_names = [name for name, _, _ in endowments]
            parts.append(f"Endowments: {', '.join(endowment_names)}")
        
        # Add weaknesses
        if s_factor_analysis['weaknesses']:
            weakness_names = [name for name, _, _ in s_factor_analysis['weaknesses']]
            parts.append(f"Low {', '.join(weakness_names)}")
        
        if parts:
            return f"[{' | '.join(parts)}]"
        else:
            return "[Balanced stats]"
    
    def display_comparison(self, actor1_sheet: ActorSheet, actor2_sheet: ActorSheet):
        """
        Display a comparison between two actors' outlier stats
        
        Useful for showing how a new NUA compares to the UA
        """
        print(f"\n{Color.HEADER}{'═' * 70}{Color.RESET}")
        print(f"{Color.INFO}📊 COMPARATIVE ANALYSIS{Color.RESET}")
        print(f"{Color.HEADER}{'═' * 70}{Color.RESET}\n")
        
        print(f"{Color.SUCCESS}{actor1_sheet.name:30}{Color.RESET} vs {Color.WARNING}{actor2_sheet.name}{Color.RESET}\n")
        
        # Compare S-factors
        print(f"{Color.INFO}S-FACTOR COMPARISON:{Color.RESET}")
        for s_factor_type in SFactorType:
            value1 = actor1_sheet.s_factors.get_factor(s_factor_type)
            value2 = actor2_sheet.s_factors.get_factor(s_factor_type)
            
            bar1 = "█" * value1 + "░" * (5 - value1)
            bar2 = "█" * value2 + "░" * (5 - value2)
            
            diff = value2 - value1
            diff_str = f"+{diff}" if diff > 0 else str(diff) if diff < 0 else "="
            diff_color = Color.SUCCESS if diff > 0 else Color.ERROR if diff < 0 else Color.INFO
            
            print(f"  {s_factor_type.name.capitalize():12} [{bar1}] {value1}  vs  [{bar2}] {value2}  {diff_color}({diff_str}){Color.RESET}")
        
        print()
        
        # Threat comparison
        threat1, _ = self.analyzer.get_threat_level(actor1_sheet)
        threat2, _ = self.analyzer.get_threat_level(actor2_sheet)
        
        print(f"{Color.INFO}THREAT LEVELS:{Color.RESET}")
        print(f"  {actor1_sheet.name}: {threat1}")
        print(f"  {actor2_sheet.name}: {threat2}")
        
        print(f"\n{Color.HEADER}{'═' * 70}{Color.RESET}\n")


# Global instance
_outlier_display: Optional[OutlierStatsDisplay] = None


def get_outlier_display() -> OutlierStatsDisplay:
    """Get or create the global outlier display instance"""
    global _outlier_display
    if _outlier_display is None:
        _outlier_display = OutlierStatsDisplay()
    return _outlier_display


def display_nua_outliers(actor_sheet: ActorSheet, context: Optional[str] = None):
    """Convenience function to display NUA outlier stats"""
    display = get_outlier_display()
    display.display_nua_introduction(actor_sheet, context)


def get_compact_outlier_summary(actor_sheet: ActorSheet) -> str:
    """Convenience function to get compact outlier summary"""
    display = get_outlier_display()
    return display.display_compact_outliers(actor_sheet)
