"""Presentation-only helpers for drawing panels, cards and the event log."""

from __future__ import annotations

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
    PANEL_RADIUS,
    SCHOOL_COLORS,
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


def draw_school_icon(
    surface: pygame.Surface, color: tuple[int, int, int], center: tuple[int, int], radius: int
) -> None:
    """Draw a simple colored disc standing in for a school's emblem.

    Emoji glyphs are not reliably available in every font pygame can find
    across platforms, so schools are identified by their accent color plus
    their written name instead of a pictograph.
    """
    pygame.draw.circle(surface, color, center, radius)
    pygame.draw.circle(surface, COLOR_TEXT_PRIMARY, center, radius, width=2)


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, active: bool = False) -> None:
    """Draw a rounded panel background with a border."""
    pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=PANEL_RADIUS)
    border_color = COLOR_PANEL_BORDER_ACTIVE if active else COLOR_PANEL_BORDER
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

    name_line = f"{player.name} · {player.school.display_name}"
    draw_text(surface, name_line, fonts["body"], accent, (rect.x + 16, rect.y + 12))

    if player.sabotaged:
        draw_text(
            surface,
            "⚠ Саботаж",
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
    y = rect.y + 44
    for message in messages:
        draw_text(surface, f"• {message}", fonts["small"], COLOR_TEXT_SECONDARY, (rect.x + 16, y))
        y += 22