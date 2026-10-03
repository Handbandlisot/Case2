"""Data model for controllable preparation-stage actions (A1-A5)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

from models.player import Player

# is_available(actor, opponents) -> True if the action can currently be used.
AvailabilityFn = Callable[[Player, list[Player]], bool]
# apply(actor, target) -> log message describing the effect. Target is only
# meaningful for the sabotage action.
ApplyFn = Callable[[Player, Player | None], str]


@dataclass(frozen=True)
class PrepAction:
    """A controllable action a player may take once per preparation turn.

    Attributes:
        action_id: Short identifier (A1-A5) matching the design document.
        name: Display name shown on the action button.
        description: One-line explanation of the effect.
        requires_target: Whether choosing this action requires picking one
            of the three opponents (only true for sabotage).
        is_available: Predicate deciding whether the button is enabled.
        apply: Function applying the effect and returning a log message.
    """

    action_id: str
    name: str
    description: str
    requires_target: bool
    is_available: AvailabilityFn
    apply: ApplyFn