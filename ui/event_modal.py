"""Drawing helper for the modal shown after a preparation-stage event."""

from __future__ import annotations

import pygame

from config import (
    COLOR_NEGATIVE,
    COLOR_PANEL_BG,
    COLOR_POSITIVE,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    PANEL_RADIUS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
)
from models.event import PrepEvent
from ui.button import Button
from ui.panel import draw_text

MODAL_WIDTH = 460
MODAL_HEIGHT = 220


def draw_event_modal(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    event: PrepEvent,
    positive: bool,
    message: str,
    continue_button: Button,
) -> None:
    """Draw the darkened overlay plus the event-result modal box."""
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    rect = pygame.Rect(0, 0, MODAL_WIDTH, MODAL_HEIGHT)
    rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    accent = COLOR_POSITIVE if positive else COLOR_NEGATIVE

    pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=PANEL_RADIUS)
    pygame.draw.rect(surface, accent, rect, width=2, border_radius=PANEL_RADIUS)

    tag_rect = pygame.Rect(rect.x + 20, rect.y + 18, 150, 26)
    pygame.draw.rect(surface, accent, tag_rect, border_radius=13)
    tag_text = "Положительный исход" if positive else "Отрицательный исход"
    draw_text(surface, tag_text, fonts["small"], (15, 18, 26), tag_rect.center, center=True)

    draw_text(
        surface, event.name, fonts["heading"], COLOR_TEXT_PRIMARY, (rect.x + 20, rect.y + 56)
    )
    summary = event.positive_summary if positive else event.negative_summary
    draw_text(surface, summary, fonts["body"], COLOR_TEXT_SECONDARY, (rect.x + 20, rect.y + 92))
    draw_text(surface, message, fonts["small"], COLOR_TEXT_SECONDARY, (rect.x + 20, rect.y + 126))

    continue_button.draw(surface, fonts["button"])