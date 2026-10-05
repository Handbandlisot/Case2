"""Global configuration and constants for "Турнир Четырёх Стихий".

Every magic number used by the game lives in this module. Nothing outside
this file should hard-code colors, sizes, stat bounds or balance numbers.
"""

from __future__ import annotations
from pathlib import Path

# --------------------------------------------------------------------------- #
# Window / engine
# --------------------------------------------------------------------------- #
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
FPS: int = 60
WINDOW_TITLE: str = "Турнир Четырёх Стихий"

PROJECT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_DIR / "assets"

SCHOOL_ICON_PATHS = {
    "fire": ASSETS_DIR / "fire.png",
    "water": ASSETS_DIR / "water.png",
    "earth": ASSETS_DIR / "earth.png",
    "air": ASSETS_DIR / "air.png",
}

SCHOOL_ICON_SIZE = 32
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
COLOR_DAMAGE_NUMBER: tuple[int, int, int] = (255, 177, 153)
COLOR_HEAL_NUMBER: tuple[int, int, int] = (158, 255, 189)
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
COLOR_BUTTON_PRIMARY_HOVER: tuple[int, int, int] = (248, 202, 110)
COLOR_BUTTON_ABILITY_HOVER: tuple[int, int, int] = (225, 105, 95)

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
SCHOOL_ABILITY_DESCRIPTION: dict[str, str] = {
    "fire": "Наносит противнику усиленный урон",
    "water": "Лечит чемпиона, возвращая часть потерянного здоровья",
    "earth": "Блокирует следующую атаку и отражает урон, равный интеллекту",
    "air": "Наносит урон здоровью противника сквозь обычный блок и снимает его",
}
SCHOOL_ABILITY_BATTLE_HINT: dict[str, str] = {
    "fire": "Наносит противнику усиленный урон",
    "water": "Возвращает часть потерянного здоровья",
    "earth": "Блокирует следующую атаку и отражает урон, равный интеллекту",
    "air": "Наносит урон здоровью сквозь обычный блок и снимает его",
}
SCHOOL_BONUS_DESCRIPTION: dict[str, str] = {
    "fire": "+2 к силе",
    "water": "+3 к интеллекту",
    "earth": "+6 к текущему и максимальному здоровью",
    "air": "+2 к харизме",
}

# --------------------------------------------------------------------------- #
# Base stats (before school bonuses)
# --------------------------------------------------------------------------- #
BASE_HEALTH: int = 40
BASE_STRENGTH: int = 5
BASE_INTELLECT: int = 5
BASE_CHARISMA: int = 5

MIN_STAT: int = 1
MAX_STAT: int = 10
MIN_HEALTH: int = 0
PREP_MIN_HEALTH: int = 1  # health may not drop below this during preparation

SCHOOL_STRENGTH_BONUS: int = 2
SCHOOL_INTELLECT_BONUS: int = 3
SCHOOL_CHARISMA_BONUS: int = 2
SCHOOL_HEALTH_BONUS: int = 6
# Earth champion starts with BASE_HEALTH + bonus (46/46) instead of 40.
EARTH_BASE_HEALTH: int = BASE_HEALTH + SCHOOL_HEALTH_BONUS

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
ARMOR_REFLECT_DIVISOR: int = 1  # reflected damage = intellect // ARMOR_REFLECT_DIVISOR

# Combat-animation timing (seconds). The game rules still resolve in
# ``logic.combat``; these values only control the presentation timeline.
COMBAT_ANIM_WINDUP_TIME: float = 0.10
COMBAT_ANIM_IMPACT_TIME: float = 0.44
COMBAT_ANIM_BLOCK_IMPACT_TIME: float = 0.08
COMBAT_ANIM_CAST_IMPACT_TIME: float = 0.32
COMBAT_ANIM_BASE_DURATION: float = 0.96
COMBAT_ANIM_BLOCK_DURATION: float = 0.72
COMBAT_ANIM_CAST_DURATION: float = 0.98
COMBAT_ANIM_KO_DURATION: float = 1.28
COMBAT_ANIM_RETURN_TIME: float = 0.23
COMBAT_ANIM_HIT_FLASH_DURATION: float = 0.34
COMBAT_ANIM_POPUP_DURATION: float = 0.80
COMBAT_ANIM_KO_FALL_DELAY: float = 0.18

# --------------------------------------------------------------------------- #
# Layout
# --------------------------------------------------------------------------- #
PADDING: int = 24
BUTTON_HEIGHT: int = 48
BUTTON_SPACING: int = 16
PANEL_RADIUS: int = 10
SECTION_GAP: int = 14  # vertical gap between stacked panels on prep/fight screens

# Preparation-screen roster (the 4 player cards above the log/action panels).
ROSTER_TOP: int = 104
ROSTER_CARD_HEIGHT: int = 100
ROSTER_ROW_GAP: int = 10

# Shared journal metrics. Preparation shows LOG_MAX_MESSAGES; combat uses a
# shorter three-message slice to make room for the animated arena.
LOG_PANEL_HEADER_OFFSET: int = 44
LOG_LINE_HEIGHT: int = 20
LOG_PANEL_BOTTOM_PADDING: int = 10

# Fight screen: a short journal leaves room for the animated arena and actions.
FIGHT_TITLE_Y: int = 42
FIGHT_TURN_Y: int = 82
FIGHT_CARDS_TOP: int = 110
FIGHT_CARD_HEIGHT: int = 138
COMBAT_ARENA_HEIGHT: int = 150
COMBAT_ARENA_GAP: int = 12
COMBAT_LOG_MESSAGES: int = 3
COMBAT_LOG_HEIGHT: int = (
    LOG_PANEL_HEADER_OFFSET
    + COMBAT_LOG_MESSAGES * LOG_LINE_HEIGHT
    + LOG_PANEL_BOTTOM_PADDING
)
COMBAT_ARENA_FIGURE_OFFSET: int = 198
COMBAT_LOG_GAP: int = 12
FIGHT_BUTTON_GAP: int = 16

# Preparation action grid (up to 5 action buttons, wrapped onto rows of 3).
ACTION_GRID_COLUMNS: int = 3
ACTION_PANEL_HEADER_OFFSET: int = 44
ACTION_ROW_HEIGHT: int = BUTTON_HEIGHT + 28  # button + its description line below it
ACTION_DESCRIPTION_HEIGHT: int = 18
ACTION_PANEL_BOTTOM_PADDING: int = 12
