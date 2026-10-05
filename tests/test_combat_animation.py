"""Presentation timeline tests for combat animations."""

from __future__ import annotations

from logic.game_state import GameState, Stage
from models.player import Player, School
from ui.combat_animation import CombatAnimation


def make_fight() -> tuple[GameState, Player, Player]:
    state = GameState()
    attacker = Player.create("Игрок 1", School.FIRE)
    defender = Player.create("Игрок 2", School.WATER)
    state.players = [
        attacker,
        defender,
        Player.create("Игрок 3", School.EARTH),
        Player.create("Игрок 4", School.AIR),
    ]
    state.fight_participants = (attacker, defender)
    state.fight_current_index = 0
    state.stage = Stage.SEMIFINAL_1
    return state, attacker, defender


def test_attack_resolves_once_at_impact_and_tracks_damage() -> None:
    state, attacker, defender = make_fight()
    animation = CombatAnimation()
    animation.start(
        "attack",
        attacker,
        defender,
        "Первый полуфинал",
        lambda: state.perform_combat_action("attack"),
    )

    animation.update(animation.impact_at - 0.02)
    assert defender.health == defender.max_health
    assert not animation.resolved

    animation.update(0.03)
    assert defender.health == defender.max_health - 12
    assert animation.resolved
    assert animation.damage_to_defender == 12

    animation.update(0.01)
    assert defender.health == defender.max_health - 12


def test_block_arms_during_its_short_animation() -> None:
    state, attacker, defender = make_fight()
    animation = CombatAnimation()
    animation.start(
        "block",
        attacker,
        defender,
        "Первый полуфинал",
        lambda: state.perform_combat_action("block"),
    )

    animation.update(animation.impact_at / 2)
    assert not attacker.block_active
    animation.update(animation.impact_at)
    assert attacker.block_active
    assert animation.resolved


def test_knockout_keeps_arena_open_long_enough_for_fall() -> None:
    state, attacker, defender = make_fight()
    defender.health = 4
    animation = CombatAnimation()
    animation.start(
        "attack",
        attacker,
        defender,
        "Первый полуфинал",
        lambda: state.perform_combat_action("attack"),
    )

    animation.update(animation.impact_at + 0.01)
    assert not defender.is_alive
    assert animation.duration > animation.impact_at
    assert not animation.fallen_for(defender)

    animation.update(0.2)
    assert animation.fallen_for(defender)
