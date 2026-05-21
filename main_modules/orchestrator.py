"""Main orchestrator - imports from modules.

This is a slimmed-down version of redesigned_main.py that imports
from the main_modules package.
"""

# Import all the modules
from main_modules.mention_system import *
from main_modules.narrative_context import *
from main_modules.visualizer import *
from main_modules.internal_voice import *
from main_modules.ui_display import *
from main_modules.spark_generation import *
from main_modules.reputation_social import *
from main_modules.dialogue import *
from main_modules.location_travel import *
from main_modules.main_loop import *
from main_modules.misc import *

if __name__ == "__main__":
    main()
