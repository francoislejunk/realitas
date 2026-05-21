"""
LLM Agents Module

This module contains specialized LLM-powered analysis and detection systems
for the UTAS simulation. These systems provide intelligent interpretation
and decision-making capabilities.

Core Systems:
- TargetDetector: NUA/INUA target classification
- EncounterChecker: Dynamic encounter detection
- SceneManager: Scene synthesis and management
- NarrativeLoop: Four-mode narrative analysis
- NUAContextSystem: Action classification and escalation
- SympathyInitialization: Relationship generation
- UTASNarrativeFormula: Formula-based outcomes

Note: SparkGenerator moved to TRASH BIN - superseded by agents/storyteller_agent.py
"""

from .target_detection_system import TargetDetector
from .encounter_checker import EncounterChecker, EncounterContext, SimulationMode
from .scene_manager import SceneManager
from .narrative_loop_system import FourModeNarrativeLoop
from .nua_context_system import NUAContextManager
from .sympathy_initialization import assign_initial_sympathies
from .utas_narrative_formula import UTASNarrativeFormula

__all__ = [
    'TargetDetector',
    'EncounterChecker', 
    'EncounterContext',
    'SimulationMode',
    'SceneManager',
    'FourModeNarrativeLoop',
    'NUAContextManager',
    'assign_initial_sympathies',
    'UTASNarrativeFormula'
]
