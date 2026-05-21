class Color:
    """A class to hold ANSI color codes for terminal output."""
    RESET = '\033[0m'
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

    NARRATIVE = MAGENTA
    NARRATIVE_ITALIC = CYAN + BOLD  # For internal voice (same as INTERNAL_VOICE)
    SYSTEM = CYAN
    PROMPT = WHITE + BOLD
    SUCCESS = GREEN
    FAILURE = RED
    INFO = YELLOW
    ACTOR_NAME = BOLD + YELLOW
    STATUS = BLUE
    HEADER = BOLD + CYAN
    WARNING = YELLOW
    ERROR = RED
    INPUT = WHITE
    SCENE = BOLD + MAGENTA
    INTERNAL_VOICE = CYAN + BOLD  # Distinctive color for internal thoughts
