# --------------------------------------------------------------------------- #
# Window / engine
# --------------------------------------------------------------------------- #
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
FPS: int = 60
WINDOW_TITLE: str = "Турнир Четырёх Стихий"

# --------------------------------------------------------------------------- #
# Fonts
# --------------------------------------------------------------------------- #
FONT_NAME: str | None = None  # None -> pygame default font
FONT_SIZE_TITLE: int = 40
FONT_SIZE_SUBTITLE: int = 20
FONT_SIZE_HEADING: int = 24
FONT_SIZE_BODY: int = 18
FONT_SIZE_SMALL: int = 15
FONT_SIZE_BUTTON: int = 20

# --------------------------------------------------------------------------- #
# Colors (RGB)
# --------------------------------------------------------------------------- #
COLOR_BACKGROUND: tuple[int, int, int] = (15, 18, 26)
COLOR_PANEL_BG: tuple[int, int, int] = (26, 31, 43)
COLOR_PANEL_BORDER: tuple[int, int, int] = (45, 52, 68)
COLOR_PANEL_BORDER_ACTIVE: tuple[int, int, int] = (240, 90, 70)

COLOR_TEXT_PRIMARY: tuple[int, int, int] = (235, 238, 245)
COLOR_TEXT_SECONDARY: tuple[int, int, int] = (150, 158, 176)
COLOR_TEXT_MUTED: tuple[int, int, int] = (105, 112, 130)

COLOR_ACCENT: tuple[int, int, int] = (240, 180, 70)
COLOR_POSITIVE: tuple[int, int, int] = (70, 190, 120)
COLOR_NEGATIVE: tuple[int, int, int] = (220, 90, 90)
COLOR_HEALTH_BAR: tuple[int, int, int] = (70, 190, 120)
COLOR_HEALTH_BAR_BG: tuple[int, int, int] = (45, 52, 68)

COLOR_BUTTON_BG: tuple[int, int, int] = (58, 66, 88)
COLOR_BUTTON_HOVER: tuple[int, int, int] = (78, 88, 114)
COLOR_BUTTON_DISABLED: tuple[int, int, int] = (38, 43, 56)
COLOR_BUTTON_TEXT: tuple[int, int, int] = (235, 238, 245)
COLOR_BUTTON_TEXT_DISABLED: tuple[int, int, int] = (95, 101, 116)
COLOR_BUTTON_PRIMARY_BG: tuple[int, int, int] = (240, 180, 70)
COLOR_BUTTON_PRIMARY_TEXT: tuple[int, int, int] = (25, 20, 10)
COLOR_BUTTON_ABILITY_BG: tuple[int, int, int] = (200, 70, 60)

SCHOOL_COLORS: dict[str, tuple[int, int, int]] = {
    "fire": (224, 92, 45),
    "water": (60, 140, 220),
    "earth": (130, 110, 90),
    "air": (190, 195, 205),
}
SCHOOL_EMOJI: dict[str, str] = {
    "fire": "🔥",
    "water": "💧",
    "earth": "🪨",
    "air": "🌪",
}
SCHOOL_DISPLAY_NAME: dict[str, str] = {
    "fire": "Школа Огня",
    "water": "Школа Воды",
    "earth": "Школа Земли",
    "air": "Школа Воздуха",
}
SCHOOL_ABILITY_NAME: dict[str, str] = {
    "fire": "Огненный шар",
    "water": "Целебный поток",
    "earth": "Каменная броня",
    "air": "Порыв ветра",
}
SCHOOL_BONUS_DESCRIPTION: dict[str, str] = {
    "fire": "+2 к силе",
    "water": "+2 к интеллекту",
    "earth": "+5 к текущему и максимальному здоровью",
    "air": "+2 к харизме",
}

# --------------------------------------------------------------------------- #
# Base stats (before school bonuses)
# --------------------------------------------------------------------------- #
BASE_HEALTH: int = 40
EARTH_BASE_HEALTH: int = 45  # earth champion starts with 45/45 instead of 40
BASE_STRENGTH: int = 5
BASE_INTELLECT: int = 5
BASE_CHARISMA: int = 5

MIN_STAT: int = 1
MAX_STAT: int = 10
MIN_HEALTH: int = 0
PREP_MIN_HEALTH: int = 1  # health may not drop below this during preparation

SCHOOL_STRENGTH_BONUS: int = 2
SCHOOL_INTELLECT_BONUS: int = 2
SCHOOL_CHARISMA_BONUS: int = 2
SCHOOL_HEALTH_BONUS: int = 5

# --------------------------------------------------------------------------- #
# Preparation stage
# --------------------------------------------------------------------------- #
PREP_ROUNDS: int = 3
PLAYER_COUNT: int = 4
# Turn order per round (0-indexed player positions), see rulebook section 6.
PREP_TURN_ORDER: dict[int, tuple[int, int, int, int]] = {
    1: (0, 1, 2, 3),
    2: (1, 2, 3, 0),
    3: (2, 3, 0, 1),
}

EVENT_POSITIVE_CHANCE: float = 0.5
SABOTAGE_DAMAGE: int = 5
HEALER_ACTION_HEAL: int = 10

LOG_MAX_MESSAGES: int = 5

# --------------------------------------------------------------------------- #
# Combat
# --------------------------------------------------------------------------- #
ATTACK_BASE_DAMAGE: int = 5  # damage = ATTACK_BASE_DAMAGE + strength
BLOCK_REDUCTION: float = 0.5
FIREBALL_BASE_DAMAGE: int = 8
FIREBALL_INTELLECT_MULTIPLIER: int = 2
HEAL_BASE_AMOUNT: int = 8
HEAL_INTELLECT_MULTIPLIER: int = 2
WIND_BASE_DAMAGE: int = 5
WIND_INTELLECT_MULTIPLIER: int = 2
ARMOR_REFLECT_DIVISOR: int = 2  # reflected damage = intellect // ARMOR_REFLECT_DIVISOR

# --------------------------------------------------------------------------- #
# Layout
# --------------------------------------------------------------------------- #
PADDING: int = 24
BUTTON_HEIGHT: int = 48
BUTTON_SPACING: int = 16
PANEL_RADIUS: int = 10