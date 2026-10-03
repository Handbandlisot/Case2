"""Player and school data models for the tournament."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from config import (
    BASE_CHARISMA,
    BASE_HEALTH,
    BASE_INTELLECT,
    BASE_STRENGTH,
    EARTH_BASE_HEALTH,
    MAX_STAT,
    MIN_HEALTH,
    MIN_STAT,
    SCHOOL_ABILITY_NAME,
    SCHOOL_CHARISMA_BONUS,
    SCHOOL_DISPLAY_NAME,
    SCHOOL_HEALTH_BONUS,
    SCHOOL_INTELLECT_BONUS,
    SCHOOL_STRENGTH_BONUS,
)


class School(Enum):
    """The four magic schools a champion can belong to."""

    FIRE = "fire"
    WATER = "water"
    EARTH = "earth"
    AIR = "air"

    @property
    def display_name(self) -> str:
        """Return the human-readable Russian name of the school."""
        return SCHOOL_DISPLAY_NAME[self.value]

    @property
    def ability_name(self) -> str:
        """Return the name of the school's unique ability."""
        return SCHOOL_ABILITY_NAME[self.value]




def _clamp_stat(value: int) -> int:
    """Clamp a strength/intellect/charisma value into the allowed range."""
    return max(MIN_STAT, min(MAX_STAT, value))


@dataclass
class Player:
    """A tournament champion controlled by one hot-seat player.

    Attributes:
        name: Display name entered by the player.
        school: The magic school the player picked.
        health: Current health points.
        max_health: Maximum health points.
        strength: Determines normal attack damage.
        intellect: Boosts the school ability.
        charisma: Affects sabotage eligibility and turn order.
        sabotaged: Whether the player carries an active sabotage mark.
        block_active: Whether a block is currently armed for the next hit.
        blocked_last_turn: Whether the player blocked on their previous
            combat turn (blocking two turns in a row is forbidden).
        armor_active: Whether Каменная броня is currently armed.
        ability_used: Whether the school ability was already used in the
            current fight.
        eliminated: Whether the player has lost a fight and left the
            tournament.
    """

    name: str
    school: School
    health: int = 0
    max_health: int = 0
    strength: int = BASE_STRENGTH
    intellect: int = BASE_INTELLECT
    charisma: int = BASE_CHARISMA
    sabotaged: bool = False
    block_active: bool = False
    blocked_last_turn: bool = False
    armor_active: bool = False
    ability_used: bool = False
    eliminated: bool = False
    log_tag: str = field(init=False, default="")

    def __post_init__(self) -> None:
        self.log_tag = self.school.display_name

    @staticmethod
    def create(name: str, school: School) -> Player:
        """Build a champion with base stats plus the school's starting bonus."""
        health = EARTH_BASE_HEALTH if school is School.EARTH else BASE_HEALTH
        strength = BASE_STRENGTH + (
            SCHOOL_STRENGTH_BONUS if school is School.FIRE else 0
        )
        intellect = BASE_INTELLECT + (
            SCHOOL_INTELLECT_BONUS if school is School.WATER else 0
        )
        charisma = BASE_CHARISMA + (
            SCHOOL_CHARISMA_BONUS if school is School.AIR else 0
        )
        return Player(
            name=name,
            school=school,
            health=health,
            max_health=health,
            strength=strength,
            intellect=intellect,
            charisma=charisma,
        )

    @property
    def is_alive(self) -> bool:
        """Return whether the champion still has health left in a fight."""
        return self.health > MIN_HEALTH

    def change_stat(self, stat_name: str, delta: int) -> int:
        """Change strength/intellect/charisma and return the applied delta.

        The value is clamped to [MIN_STAT, MAX_STAT]; the returned delta is
        the actual change that was applied (may be 0 at the bounds).
        """
        current = getattr(self, stat_name)
        new_value = _clamp_stat(current + delta)
        setattr(self, stat_name, new_value)
        return new_value - current

    def change_health(self, delta: int, floor: int = MIN_HEALTH) -> int:
        """Change health, clamped to [floor, max_health]; return applied delta."""
        new_value = max(floor, min(self.max_health, self.health + delta))
        applied = new_value - self.health
        self.health = new_value
        return applied

    def increase_max_health(self, delta: int) -> None:
        """Increase max health and current health by the same amount."""
        self.max_health += delta
        self.health += delta

    def reset_for_fight(self) -> None:
        """Reset per-fight flags before a new semifinal/final bout."""
        self.block_active = False
        self.blocked_last_turn = False
        self.armor_active = False
        self.ability_used = False

    def restore_full_health(self) -> None:
        """Fully heal the champion (used before the final)."""
        self.health = self.max_health

if __name__ == "__main__":
    school = School("fire")
    player1 = Player.create(name="", school=school)
    player2 = Player(name="", school=school)
    print(player1)
    print(player2)
