"""Turn-resolution logic for a single fight (semifinal or final).

All functions here are pure with respect to the UI: they only take and
mutate :class:`~models.player.Player` instances and return a log message.
"""

from __future__ import annotations

from config import (
    ARMOR_REFLECT_DIVISOR,
    ATTACK_BASE_DAMAGE,
    FIREBALL_BASE_DAMAGE,
    FIREBALL_INTELLECT_MULTIPLIER,
    HEAL_BASE_AMOUNT,
    HEAL_INTELLECT_MULTIPLIER,
    MIN_HEALTH,
    WIND_BASE_DAMAGE,
    WIND_INTELLECT_MULTIPLIER,
)
from models.player import Player, School


def attack_damage_preview(player: Player) -> int:
    """Return how much damage a normal attack currently deals."""
    return ATTACK_BASE_DAMAGE + player.strength


def ability_damage_preview(player: Player) -> int:
    """Return the numeric preview shown on the ability button, if any.

    Returns 0 for Каменная броня, which has no direct damage/heal number.
    """
    if player.school is School.FIRE:
        return FIREBALL_BASE_DAMAGE + player.intellect * FIREBALL_INTELLECT_MULTIPLIER
    if player.school is School.WATER:
        return HEAL_BASE_AMOUNT + player.intellect * HEAL_INTELLECT_MULTIPLIER
    if player.school is School.AIR:
        return WIND_BASE_DAMAGE + player.intellect * WIND_INTELLECT_MULTIPLIER
    return 0


def is_block_available(player: Player) -> bool:
    """Block is available unless it would be redundant or forbidden.

    It is disabled if the player blocked on their previous turn, if a block
    is already armed, or if Каменная броня is armed (they do not stack).
    """
    return not (
        player.blocked_last_turn or player.block_active or player.armor_active
    )


def is_ability_available(player: Player) -> bool:
    """An ability is usable once per fight.

    Water also requires missing HP; Earth requires that no block or armor
    is already armed (they do not stack).
    """
    if player.ability_used:
        return False
    if player.school is School.WATER:
        return player.health < player.max_health
    if player.school is School.EARTH:
        return not (player.block_active or player.armor_active)
    return True


def _resolve_incoming(
    defender: Player, raw_damage: int, ignores_block: bool
) -> tuple[int, int, str]:
    """Apply armor/block mitigation for one incoming hit.

    Returns (final_damage_to_defender, reflected_damage_to_attacker, note).
    """
    if defender.armor_active:
        defender.armor_active = False
        reflected = defender.intellect // ARMOR_REFLECT_DIVISOR
        return 0, reflected, "заблокировано Каменной бронёй"
    if defender.block_active:
        defender.block_active = False
        if ignores_block:
            # Порыв ветра ignores the block's damage reduction but still
            # consumes it, per the rulebook.
            return raw_damage, 0, "блок не спас от Порыва ветра"
        return raw_damage // 2, 0, "урон уменьшен блоком вдвое"
    return raw_damage, 0, ""


def _apply_hit(attacker: Player, defender: Player, final: int, reflected: int) -> None:
    if final:
        defender.change_health(-final, floor=MIN_HEALTH)
    if reflected:
        attacker.change_health(-reflected, floor=MIN_HEALTH)


def perform_attack(attacker: Player, defender: Player) -> str:
    """Resolve a normal attack action and return a log message."""
    raw = attack_damage_preview(attacker)
    final, reflected, note = _resolve_incoming(defender, raw, ignores_block=False)
    _apply_hit(attacker, defender, final, reflected)
    attacker.blocked_last_turn = False
    message = f"{attacker.log_tag} атаковал(а) и нанёс(ла) {final} урона"
    if reflected:
        message += f", получил(а) {reflected} отражённого урона"
    elif note:
        message += f" ({note})"
    return message


def perform_block(attacker: Player) -> str:
    """Arm a block for the attacker's next incoming hit."""
    if not is_block_available(attacker):
        raise ValueError("Block is not available right now")
    attacker.block_active = True
    attacker.blocked_last_turn = True
    return f"{attacker.log_tag} поставил(а) блок"


def _perform_fireball(attacker: Player, defender: Player) -> str:
    raw = ability_damage_preview(attacker)
    final, reflected, note = _resolve_incoming(defender, raw, ignores_block=False)
    _apply_hit(attacker, defender, final, reflected)
    message = f"{attacker.log_tag} применил(а) Огненный шар и нанёс(ла) {final} урона"
    if reflected:
        message += f", получил(а) {reflected} отражённого урона"
    elif note:
        message += f" ({note})"
    return message


def _perform_heal(attacker: Player, _defender: Player) -> str:
    amount = ability_damage_preview(attacker)
    applied = attacker.change_health(amount)
    return f"{attacker.log_tag} применил(а) Целебный поток и восстановил(а) {applied} здоровья"


def _perform_armor(attacker: Player, _defender: Player) -> str:
    attacker.armor_active = True
    return f"{attacker.log_tag} поднял(а) Каменную броню"


def _perform_wind(attacker: Player, defender: Player) -> str:
    raw = ability_damage_preview(attacker)
    final, reflected, note = _resolve_incoming(defender, raw, ignores_block=True)
    _apply_hit(attacker, defender, final, reflected)
    message = f"{attacker.log_tag} применил(а) Порыв ветра и нанёс(ла) {final} урона"
    if reflected:
        message += f", получил(а) {reflected} отражённого урона"
    elif note:
        message += f" ({note})"
    return message


_ABILITY_HANDLERS = {
    School.FIRE: _perform_fireball,
    School.WATER: _perform_heal,
    School.EARTH: _perform_armor,
    School.AIR: _perform_wind,
}


def perform_ability(attacker: Player, defender: Player) -> str:
    """Resolve the attacker's school ability and return a log message."""
    if not is_ability_available(attacker):
        raise ValueError("Ability is not available right now")
    handler = _ABILITY_HANDLERS[attacker.school]
    message = handler(attacker, defender)
    attacker.ability_used = True
    attacker.blocked_last_turn = False
    return message
