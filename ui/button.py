"""A simple reusable clickable button. Presentation only."""

from __future__ import annotations

from dataclasses import dataclass

import pygame

from config import (
    COLOR_BUTTON_ABILITY_BG,
    COLOR_BUTTON_BG,
    COLOR_BUTTON_DISABLED,
    COLOR_BUTTON_HOVER,
    COLOR_BUTTON_PRIMARY_BG,
    COLOR_BUTTON_PRIMARY_TEXT,
    COLOR_BUTTON_TEXT,
    COLOR_BUTTON_TEXT_DISABLED,
    COLOR_BUTTON_ABILITY_HOVER,
    COLOR_BUTTON_PRIMARY_HOVER,
)

Variant = str  # "default" | "primary" | "ability"

_BG_COLORS: dict[Variant, tuple[int, int, int]] = {
    "default": COLOR_BUTTON_BG,
    "primary": COLOR_BUTTON_PRIMARY_BG,
    "ability": COLOR_BUTTON_ABILITY_BG,
}

_HOVER_COLORS: dict[Variant, tuple[int, int, int]] = {
    "default": COLOR_BUTTON_HOVER,
    "primary": COLOR_BUTTON_PRIMARY_HOVER,
    "ability": COLOR_BUTTON_ABILITY_HOVER,
}


@dataclass
class Button:
    """A clickable rectangle with a label.

    Attributes:
        rect: Screen-space rectangle occupied by the button.
        label: Text drawn centered on the button.
        enabled: Whether the button reacts to clicks and is drawn active.
        variant: Visual style key ("default", "primary" or "ability").
    """

    rect: pygame.Rect
    label: str
    enabled: bool = True
    variant: Variant = "default"

    def is_clicked(self, mouse_pos: tuple[int, int], mouse_down: bool) -> bool:
        """Return True if this click event should trigger the button."""
        return self.enabled and mouse_down and self.rect.collidepoint(mouse_pos)

    def draw(self, surface: pygame.Surface, font: pygame.font.Font) -> None:
        """Draw the button, reflecting hover and enabled state."""
        mouse_pos = pygame.mouse.get_pos()
        hovered = self.enabled and self.rect.collidepoint(mouse_pos)

        if not self.enabled:
            bg_color = COLOR_BUTTON_DISABLED
            text_color = COLOR_BUTTON_TEXT_DISABLED
        else:
            base = _BG_COLORS.get(self.variant, COLOR_BUTTON_BG)
            hover_color = _HOVER_COLORS.get(self.variant, COLOR_BUTTON_HOVER)
            bg_color = hover_color if hovered else base
            text_color = (
                COLOR_BUTTON_PRIMARY_TEXT if self.variant == "primary" else COLOR_BUTTON_TEXT
            )

        pygame.draw.rect(surface, bg_color, self.rect, border_radius=8)
        text_surface = font.render(self.label, True, text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)