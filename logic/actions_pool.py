"""The five controllable preparation actions (A1-A5).

Kept as a sibling of ``events_pool`` so ``game_state`` can treat the random
and the chosen part of a preparation turn symmetrically.
"""

from __future__ import annotations

from typing import Optional

from config import HEALER_ACTION_HEAL, MAX_STAT
from models.action import PrepAction
from models.player import Player


def _can_raise(stat_name: str):
    def check(actor: Player, _opponents: list[Player]) -> bool:
        return getattr(actor, stat_name) < MAX_STAT

    return check


def _raise_strength(actor: Player, _target: Optional[Player]) -> str:
    actor.change_stat("strength", 1)
    return f"{actor.log_tag}: силовая тренировка — сила +1"


def _raise_intellect(actor: Player, _target: Optional[Player]) -> str:
    actor.change_stat("intellect", 1)
    return f"{actor.log_tag}: изучение магии — интеллект +1"


def _raise_charisma(actor: Player, _target: Optional[Player]) -> str:
    actor.change_stat("charisma", 1)
    return f"{actor.log_tag}: выступление перед зрителями — харизма +1"


def _heal_available(actor: Player, _opponents: list[Player]) -> bool:
    return actor.health < actor.max_health


def _heal(actor: Player, _target: Optional[Player]) -> str:
    actor.change_health(HEALER_ACTION_HEAL)
    return f"{actor.log_tag}: посещение целителя — здоровье +{HEALER_ACTION_HEAL}"


def can_be_sabotaged(actor: Player, target: Player) -> bool:
    """Return whether ``actor`` is allowed to sabotage ``target``."""
    return (
        target is not actor
        and not target.sabotaged
        and target.charisma <= actor.charisma
    )


def _sabotage_available(actor: Player, opponents: list[Player]) -> bool:
    return any(can_be_sabotaged(actor, opponent) for opponent in opponents)


def _sabotage(actor: Player, target: Optional[Player]) -> str:
    if target is None:
        raise ValueError("Sabotage requires a target player")
    target.sabotaged = True
    return f"{actor.log_tag}: саботировал(а) {target.log_tag}"


ACTIONS: tuple[PrepAction, ...] = (
    PrepAction(
        "A1",
        "Силовая тренировка",
        "+1 к силе",
        requires_target=False,
        is_available=_can_raise("strength"),
        apply=_raise_strength,
    ),
    PrepAction(
        "A2",
        "Изучение магии",
        "+1 к интеллекту",
        requires_target=False,
        is_available=_can_raise("intellect"),
        apply=_raise_intellect,
    ),
    PrepAction(
        "A3",
        "Выступление перед зрителями",
        "+1 к харизме",
        requires_target=False,
        is_available=_can_raise("charisma"),
        apply=_raise_charisma,
    ),
    PrepAction(
        "A4",
        "Посещение целителя",
        f"+{HEALER_ACTION_HEAL} здоровья",
        requires_target=False,
        is_available=_heal_available,
        apply=_heal,
    ),
    PrepAction(
        "A5",
        "Саботаж",
        "Наложить саботаж на соперника",
        requires_target=True,
        is_available=_sabotage_available,
        apply=_sabotage,
    ),
)