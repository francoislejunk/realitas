import logging
import os
from typing import Dict, Any
from color_utils import Color

class UTASLogger:
    """
    A dedicated logger for the UTAS system that handles setup and provides
    structured logging methods for different game events.
    """
    def __init__(self, log_file: str = "logs/utas_exchange.log"):
        """
        Initializes the logger, creating the log directory and configuring the logger.
        """
        log_dir = os.path.dirname(log_file)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        self.logger = logging.getLogger("UTASLogger")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            # File handler with UTF-8 encoding
            file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
            file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)

            # Console handler with UTF-8 encoding
            import sys
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.INFO)
            # Set UTF-8 encoding for console output
            if hasattr(sys.stdout, 'reconfigure'):
                try:
                    sys.stdout.reconfigure(encoding='utf-8')
                except Exception:
                    pass
            console_formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)

    def _log(self, level, message, exc_info=False):
        """Helper method to log messages."""
        self.logger.log(level, message, exc_info=exc_info)

    def log_continuity(self, report: str):
        self._log(logging.INFO, f"\n{Color.SYSTEM}--- CONTINUITY REPORT ---{Color.RESET}\n{report}")

    def log_system(self, message: str):
        self._log(logging.INFO, f"{Color.SYSTEM}SYSTEM: {message}{Color.RESET}")

    def log_error(self, message: str, exc_info: bool = False):
        self._log(logging.ERROR, f"{Color.WARNING}ERROR: {message}{Color.RESET}", exc_info=exc_info)

    def log_warning(self, message: str):
        self._log(logging.WARNING, f"{Color.WARNING}WARNING: {message}{Color.RESET}")

    def log_action_interpretation(self, actor_type: str, report: str):
        self._log(logging.INFO, f"\n{Color.INFO}--- INTERPRETED ACTION ({actor_type.upper()}) ---{Color.RESET}\n{report}")

    def log_exchange(self, proactor_name: str, reactor_name: str, proactor_action: Dict[str, Any], reactor_action: Dict[str, Any], proactor_success: int, reactor_success: int, outcome: str):
        log_message = (
            f"\n{Color.INFO}--- EXCHANGE RESOLUTION ---{Color.RESET}\n"
            f"  - Proactor: {Color.ACTOR_NAME}{proactor_name}{Color.RESET}\n"
            f"    - Action: {proactor_action.get('narrative_description', 'N/A')}\n"
            f"    - Success: {Color.SUCCESS}{proactor_success}{Color.RESET}\n"
            f"  - Reactor: {Color.ACTOR_NAME}{reactor_name}{Color.RESET}\n"
            f"    - Action: {reactor_action.get('narrative_description', 'N/A')}\n"
            f"    - Success: {Color.SUCCESS}{reactor_success}{Color.RESET}\n"
            f"  - Outcome: {Color.INFO}{outcome}{Color.RESET}"
        )
        self._log(logging.INFO, log_message)

    def log_narrative(self, narrative: str):
        self._log(logging.INFO, narrative)

