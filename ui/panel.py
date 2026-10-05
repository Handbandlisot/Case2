"""Presentation-only helpers for drawing panels, cards and the event log."""

from __future__ import annotations

import math

import pygame

from config import (
    COLOR_HEALTH_BAR,
    COLOR_HEALTH_BAR_BG,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_PANEL_BORDER_ACTIVE,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    LOG_LINE_HEIGHT,
    LOG_PANEL_BOTTOM_PADDING,
    LOG_PANEL_HEADER_OFFSET,
    LOG_MAX_MESSAGES,
    PANEL_RADIUS,
    SCHOOL_COLORS,
    SCHOOL_ICON_PATHS,
    SCHOOL_ICON_SIZE,
)
from models.player import Player


def draw_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    pos: tuple[int, int],
    center: bool = False,
) -> pygame.Rect:
    """Render one line of text and blit it; return the blitted rect."""
    text_surface = font.render(text, True, color)
    rect = text_surface.get_rect(center=pos) if center else text_surface.get_rect(topleft=pos)
    surface.blit(text_surface, rect)
    return rect


_SCHOOL_ICON_CACHE: dict[tuple[str, int], pygame.Surface] = {}


def _fallback_school_icon(school_key: str, size: int) -> pygame.Surface:
    """Draw a small vector icon if the binary Twemoji asset is unavailable."""
    image = pygame.Surface((size, size), pygame.SRCALPHA)
    cx = size // 2
    color = SCHOOL_COLORS[school_key]

    if school_key == "fire":
        pygame.draw.polygon(image, color, [
            (cx, 2), (size - 4, size // 3), (size - 7, size - 5),
            (cx, size - 1), (5, size - 7), (size // 4, size // 2),
        ])
        pygame.draw.polygon(image, (255, 190, 85), [
            (cx, size // 2 - 2), (cx + size // 5, size - 5),
            (cx, size - 8), (cx - size // 5, size - 5),
        ])
    elif school_key == "water":
        pygame.draw.polygon(image, color, [
            (cx, 2), (size - 4, size // 2), (size - 7, size - 8),
            (cx, size - 2), (7, size - 8), (4, size // 2),
        ])
        pygame.draw.circle(image, (150, 215, 255), (cx - size // 7, size // 2), max(2, size // 10))
    elif school_key == "earth":
        pygame.draw.polygon(image, color, [
            (size // 4, size // 4), (size * 3 // 5, 3),
            (size - 3, size // 3), (size * 4 // 5, size - 4),
            (size // 5, size - 5), (3, size // 2),
        ])
        pygame.draw.line(image, (190, 165, 125), (size // 4, size * 2 // 3), (size * 3 // 4, size // 3), max(1, size // 12))
    elif school_key == "air":
        for inset in (size // 6, size // 3, size // 2):
            rect = pygame.Rect(inset, inset, size - inset * 2, size - inset * 2)
            pygame.draw.arc(image, color, rect, math.pi * 0.15, math.pi * 1.75, max(1, size // 12))
        pygame.draw.circle(image, color, (size - 5, size // 2), max(2, size // 10))
    return image


def draw_school_icon(
    surface: pygame.Surface,
    school_key: str,
    center: tuple[int, int],
    size: int = SCHOOL_ICON_SIZE,
    enabled: bool = True,
) -> None:
    """Draw a school icon loaded from the assets directory."""
    cache_key = (school_key, size)

    if cache_key not in _SCHOOL_ICON_CACHE:
        icon_path = SCHOOL_ICON_PATHS[school_key]
        if icon_path.is_file():
            image = pygame.image.load(str(icon_path)).convert_alpha()
        else:
            image = _fallback_school_icon(school_key, size)

        _SCHOOL_ICON_CACHE[cache_key] = pygame.transform.smoothscale(
            image,
            (size, size),
        )

    icon = _SCHOOL_ICON_CACHE[cache_key]

    if not enabled:
        icon = icon.copy()
        icon.set_alpha(90)

    icon_rect = icon.get_rect(center=center)
    surface.blit(icon, icon_rect)



def wrap_text(text: str, font: pygame.font.Font, max_width: int) -> list[str]:
    """Split ``text`` into lines that each fit within ``max_width`` pixels."""
    words = text.split(" ")
    lines: list[str] = []
    line = ""
    for word in words:
        candidate = f"{line} {word}".strip()
        if font.size(candidate)[0] > max_width and line:
            lines.append(line)
            line = word
        else:
            line = candidate
    if line:
        lines.append(line)
    return lines


def wrapped_text_height(
    text: str, font: pygame.font.Font, max_width: int, line_spacing: int = 4
) -> int:
    """Return the total pixel height ``text`` will take when wrapped."""
    lines = wrap_text(text, font, max_width)
    line_height = font.get_height()
    return len(lines) * line_height + max(0, len(lines) - 1) * line_spacing


def draw_wrapped_text(
    surface: pygame.Surface,
    text: str,
    font: pygame.font.Font,
    color: tuple[int, int, int],
    top_left: tuple[int, int],
    max_width: int,
    line_spacing: int = 4,
) -> int:
    """Draw ``text`` word-wrapped to ``max_width``; return the bottom y."""
    x, y = top_left
    line_height = font.get_height()
    for line in wrap_text(text, font, max_width):
        draw_text(surface, line, font, color, (x, y))
        y += line_height + line_spacing
    return y


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, active: bool = False, border_color: tuple[int, int, int] | None = None) -> None:
    """Draw a rounded panel background with a border."""
    pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=PANEL_RADIUS)
    if border_color is None:
        border_color = (
            COLOR_PANEL_BORDER_ACTIVE
            if active
            else COLOR_PANEL_BORDER
        )
    pygame.draw.rect(surface, border_color, rect, width=2, border_radius=PANEL_RADIUS)


def draw_health_bar(
    surface: pygame.Surface, rect: pygame.Rect, current: int, maximum: int
) -> None:
    """Draw a horizontal health bar with a centered "current/max" label."""
    pygame.draw.rect(surface, COLOR_HEALTH_BAR_BG, rect, border_radius=6)
    ratio = 0.0 if maximum <= 0 else max(0.0, min(1.0, current / maximum))
    if ratio > 0:
        fill_rect = pygame.Rect(rect.x, rect.y, int(rect.width * ratio), rect.height)
        pygame.draw.rect(surface, COLOR_HEALTH_BAR, fill_rect, border_radius=6)
    font = pygame.font.Font(None, 16)
    label = f"{current}/{maximum}"
    text_surface = font.render(label, True, COLOR_TEXT_PRIMARY)
    surface.blit(text_surface, text_surface.get_rect(center=rect.center))


def draw_stat_chips(
    surface: pygame.Surface,
    font: pygame.font.Font,
    top_left: tuple[int, int],
    labels: list[str],
) -> None:
    """Draw a horizontal row of small rounded stat chips."""
    x, y = top_left
    for label in labels:
        text_surface = font.render(label, True, COLOR_TEXT_SECONDARY)
        chip_rect = pygame.Rect(x, y, text_surface.get_width() + 16, 26)
        pygame.draw.rect(surface, COLOR_PANEL_BORDER, chip_rect, border_radius=13)
        surface.blit(text_surface, text_surface.get_rect(center=chip_rect.center))
        x += chip_rect.width + 8


def player_stat_labels(player: Player) -> list[str]:
    """Return the standard "Здоровье N" / "Сила N" ... chip label set."""
    return [
        f"Здоровье {player.health}/{player.max_health}",
        f"Сила {player.strength}",
        f"Интеллект {player.intellect}",
        f"Харизма {player.charisma}",
    ]


def draw_player_card(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    rect: pygame.Rect,
    player: Player,
    active: bool = False,
    show_ability_status: bool = False,
) -> None:
    """Draw one champion's info card (used on prep and fight screens)."""
    draw_panel(surface, rect, active=active)
    accent = SCHOOL_COLORS[player.school.value]

    draw_school_icon(
        surface,
        player.school.value,
        (rect.x + 28, rect.y + 23),
        24,
    )

    name_line = f"{player.name} · {player.school.display_name}"
    draw_text(surface, name_line, fonts["body"], accent, (rect.x + 48, rect.y + 12))

    if player.sabotaged:
        draw_text(
            surface,
            "Саботаж",
            fonts["small"],
            COLOR_TEXT_MUTED,
            (rect.right - 16, rect.y + 14),
            center=False,
        )

    bar_rect = pygame.Rect(rect.x + 16, rect.y + 42, rect.width - 32, 18)
    draw_health_bar(surface, bar_rect, player.health, player.max_health)

    draw_stat_chips(
        surface,
        fonts["small"],
        (rect.x + 16, rect.y + 68),
        [
            f"Сила {player.strength}",
            f"Интеллект {player.intellect}",
            f"Харизма {player.charisma}",
        ],
    )

    if show_ability_status:
        status = "недоступна" if player.ability_used else "доступна"
        draw_text(
            surface,
            f"{player.school.ability_name}: {status}",
            fonts["small"],
            COLOR_TEXT_MUTED,
            (rect.x + 16, rect.y + 100),
        )


def log_panel_height() -> int:
    """Height needed to show up to LOG_MAX_MESSAGES lines with no clipping."""
    return LOG_PANEL_HEADER_OFFSET + LOG_MAX_MESSAGES * LOG_LINE_HEIGHT + LOG_PANEL_BOTTOM_PADDING


def draw_log_panel(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    rect: pygame.Rect,
    messages: list[str],
    title: str = "Хроника турнира",
) -> None:
    """Draw the scrolling-less last-N-messages log panel."""
    draw_panel(surface, rect)
    draw_text(surface, title, fonts["body"], COLOR_TEXT_PRIMARY, (rect.x + 16, rect.y + 12))
    y = rect.y + LOG_PANEL_HEADER_OFFSET
    for message in messages:
        draw_text(surface, f"• {message}", fonts["small"], COLOR_TEXT_SECONDARY, (rect.x + 16, y))
        y += LOG_LINE_HEIGHT
