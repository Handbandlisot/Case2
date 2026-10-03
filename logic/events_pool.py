"""The six uncontrollable preparation events (E1-E6) and their resolution."""

from __future__ import annotations

import random

from config import EVENT_POSITIVE_CHANCE, PREP_MIN_HEALTH, SABOTAGE_DAMAGE
from models.event import PrepEvent
from models.player import Player

_TRIPLE_STATS: tuple[str, str, str] = ("strength", "intellect", "charisma")
_STAT_LABEL: dict[str, str] = {
    "strength": "силу",
    "intellect": "интеллект",
    "charisma": "харизму",
}


def _library_positive(player: Player) -> str:
    player.change_stat("intellect", 1)
    return "повысил(а) интеллект на 1"


def _library_negative(player: Player) -> str:
    player.change_stat("intellect", -1)
    return "потерял(а) 1 интеллекта"


def _training_positive(player: Player) -> str:
    player.change_stat("strength", 1)
    return "повысил(а) силу на 1"


def _training_negative(player: Player) -> str:
    player.change_health(-5, floor=PREP_MIN_HEALTH)
    return "неудачная тренировка — здоровье -5"


def _crowd_positive(player: Player) -> str:
    player.change_stat("charisma", 1)
    return "повысил(а) харизму на 1"


def _crowd_negative(player: Player) -> str:
    player.change_stat("charisma", -1)
    return "потерял(а) 1 харизмы"


def _spring_positive(player: Player) -> str:
    player.change_health(5)
    return "восстановил(а) 5 здоровья"


def _spring_negative(player: Player) -> str:
    player.change_health(-5, floor=PREP_MIN_HEALTH)
    return "потерял(а) 5 здоровья"


def _pick_extreme_stat(player: Player, want_lowest: bool) -> str:
    values = {stat: getattr(player, stat) for stat in _TRIPLE_STATS}
    target_value = min(values.values()) if want_lowest else max(
        values.values())
    candidates = [stat for stat, value in values.items() if
                  value == target_value]
    return random.choice(candidates)


def _mentor_positive(player: Player) -> str:
    stat = _pick_extreme_stat(player, want_lowest=True)
    player.change_stat(stat, 1)
    return f"совет наставника — {_STAT_LABEL[stat]} +1"


def _mentor_negative(player: Player) -> str:
    stat = _pick_extreme_stat(player, want_lowest=False)
    player.change_stat(stat, -1)
    return f"неудачный совет — {_STAT_LABEL[stat]} -1"


def _helper_positive(player: Player) -> str:
    if player.sabotaged:
        player.sabotaged = False
        return "загадочный помощник снял саботаж"
    player.change_health(5)
    return "загадочный помощник — здоровье +5"


def _helper_negative(player: Player) -> str:
    if player.sabotaged:
        return "загадочный помощник — саботаж уже наложен, эффекта нет"
    player.sabotaged = True
    return f"загадочный помощник наложил саботаж (−{SABOTAGE_DAMAGE} перед боем)"


EVENTS: tuple[PrepEvent, ...] = (
    PrepEvent(
        "E1",
        "Тайная библиотека",
        "+1 интеллект",
        "−1 интеллект",
        _library_positive,
        _library_negative,
    ),
    PrepEvent(
        "E2",
        "Показательная тренировка",
        "+1 сила",
        "−5 здоровья",
        _training_positive,
        _training_negative,
    ),
    PrepEvent(
        "E3",
        "Встреча со зрителями",
        "+1 харизма",
        "−1 харизма",
        _crowd_positive,
        _crowd_negative,
    ),
    PrepEvent(
        "E4",
        "Волшебный источник",
        "+5 здоровья",
        "−5 здоровья",
        _spring_positive,
        _spring_negative,
    ),
    PrepEvent(
        "E5",
        "Совет наставника",
        "+1 к самой низкой характеристике",
        "−1 от самой высокой характеристики",
        _mentor_positive,
        _mentor_negative,
    ),
    PrepEvent(
        "E6",
        "Загадочный помощник",
        "Снимает саботаж или +5 здоровья",
        "Накладывает саботаж",
        _helper_positive,
        _helper_negative,
    ),
)


def draw_random_event() -> PrepEvent:
    """Pick one of the six preparation events uniformly at random."""
    return random.choice(EVENTS)


def resolve_event(player: Player, event: PrepEvent) -> tuple[bool, str]:
    """Apply an event to ``player``, deciding the outcome by a coin flip.

    Returns:
        A tuple of (is_positive, log_message). The message already includes
        the player's school as a prefix, e.g. "Школа Огня: ...".
    """
    is_positive = random.random() < EVENT_POSITIVE_CHANCE
    effect = event.apply_positive if is_positive else event.apply_negative
    detail = effect(player)
    outcome = "удача" if is_positive else "неудача"
    message = f"{player.log_tag}: {event.name} ({outcome}) — {detail}"
    return is_positive, message
