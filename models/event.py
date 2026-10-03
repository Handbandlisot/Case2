"""Data model for uncontrollable preparation-stage events."""

from dataclasses import dataclass
from typing import Callable

from models.player import Player


@dataclass(frozen=True)
class PrepEvent:
    """A single random event that can occur during preparation.

    Attributes:
        event_id: Short identifier (E1-E6) matching the design document.
        name: Display name shown in the event modal.
        positive_summary: One-line description of the positive outcome.
        negative_summary: One-line description of the negative outcome.
        apply_positive: Function applying the positive outcome to a player.
        apply_negative: Function applying the negative outcome to a player.
    """

    event_id: str
    name: str
    positive_summary: str
    negative_summary: str
    apply_positive: Callable[[Player], str]
    apply_negative: Callable[[Player], str]