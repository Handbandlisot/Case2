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
from ui.panel import draw_text, draw_wrapped_text, wrapped_text_height

MODAL_WIDTH = 460
MODAL_PADDING = 20
# Fixed vertical offset of the detail message, before we know how tall it is.
_MESSAGE_TOP_OFFSET = 126
_BUTTON_GAP_ABOVE = 24
_BOTTOM_PADDING = 24


def draw_event_modal(
    surface: pygame.Surface,
    fonts: dict[str, pygame.font.Font],
    event: PrepEvent,
    positive: bool,
    message: str,
    continue_button: Button,
) -> None:
    """Draw the darkened overlay plus the event-result modal box.

    The box height (and therefore the button's position) is computed from
    the wrapped height of ``message``, so a long log line never overlaps
    the "Далее: действия" button.
    """
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    text_width = MODAL_WIDTH - 2 * MODAL_PADDING
    message_height = wrapped_text_height(message, fonts["small"], text_width)
    modal_height = _MESSAGE_TOP_OFFSET + message_height + _BUTTON_GAP_ABOVE + continue_button.rect.height + _BOTTOM_PADDING

    rect = pygame.Rect(0, 0, MODAL_WIDTH, modal_height)
    rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
    accent = COLOR_POSITIVE if positive else COLOR_NEGATIVE

    pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=PANEL_RADIUS)
    pygame.draw.rect(surface, accent, rect, width=2, border_radius=PANEL_RADIUS)

    tag_text = "Положительный исход" if positive else "Отрицательный исход"
    tag_width = fonts["small"].size(tag_text)[0] + 24
    tag_rect = pygame.Rect(rect.x + 20, rect.y + 18, tag_width, 26)
    pygame.draw.rect(surface, accent, tag_rect, border_radius=13)
    draw_text(surface, tag_text, fonts["small"], (15, 18, 26), tag_rect.center, center=True)

    draw_text(
        surface, event.name, fonts["heading"], COLOR_TEXT_PRIMARY, (rect.x + 20, rect.y + 56)
    )
    summary = event.positive_summary if positive else event.negative_summary
    draw_text(surface, summary, fonts["body"], COLOR_TEXT_SECONDARY, (rect.x + 20, rect.y + 92))
    message_bottom = draw_wrapped_text(
        surface, message, fonts["small"], COLOR_TEXT_SECONDARY,
        (rect.x + MODAL_PADDING, rect.y + _MESSAGE_TOP_OFFSET), text_width,
    )

    continue_button.rect.centerx = rect.centerx
    continue_button.rect.y = message_bottom + _BUTTON_GAP_ABOVE
    continue_button.draw(surface, fonts["button"])
