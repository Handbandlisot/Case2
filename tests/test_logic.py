"""Unit tests for the tournament rules (variant A balance).

Run with:  python -m pytest tests -q
"""

from __future__ import annotations

import random
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from logic import combat
from logic.actions_pool import ACTIONS, can_be_sabotaged
from logic.events_pool import EVENTS
from logic.game_state import GameState, Stage
from models.player import Player, School

ACTION = {a.action_id: a for a in ACTIONS}
EVENT = {e.event_id: e for e in EVENTS}


def mk(school: School, **kw) -> Player:
    p = Player.create(school.value, school)
    for k, v in kw.items():
        setattr(p, k, v)
    return p


# --------------------------------------------------------------------------- #
# Start stats (variant A)
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "school,hp,st,it,ch",
    [
        (School.FIRE, 40, 7, 5, 5),
        (School.WATER, 40, 5, 8, 5),
        (School.EARTH, 46, 5, 5, 5),
        (School.AIR, 40, 5, 5, 7),
    ],
)
def test_start_stats(school, hp, st, it, ch):
    p = Player.create("x", school)
    assert (p.health, p.max_health, p.strength, p.intellect, p.charisma) == (hp, hp, st, it, ch)


def test_earth_health_derived_from_bonus():
    assert config.EARTH_BASE_HEALTH == config.BASE_HEALTH + config.SCHOOL_HEALTH_BONUS == 46


def test_stat_bounds():
    p = mk(School.FIRE, strength=10, intellect=1)
    assert p.change_stat("strength", 1) == 0 and p.strength == 10
    assert p.change_stat("intellect", -1) == 0 and p.intellect == 1


# --------------------------------------------------------------------------- #
# Events E1-E6
# --------------------------------------------------------------------------- #
def test_e1():
    p = mk(School.FIRE)
    EVENT["E1"].apply_positive(p); assert p.intellect == 6
    EVENT["E1"].apply_negative(p); EVENT["E1"].apply_negative(p); assert p.intellect == 4
    p.intellect = 1; EVENT["E1"].apply_negative(p); assert p.intellect == 1
    p.intellect = 10; EVENT["E1"].apply_positive(p); assert p.intellect == 10


def test_e2():
    p = mk(School.FIRE)
    EVENT["E2"].apply_positive(p); assert p.strength == 8
    q = mk(School.AIR); EVENT["E2"].apply_negative(q); assert q.health == 35
    q.health = 3; EVENT["E2"].apply_negative(q); assert q.health == 1  # prep floor


def test_e3_bounds():
    p = mk(School.AIR, charisma=10); EVENT["E3"].apply_positive(p); assert p.charisma == 10
    p.charisma = 1; EVENT["E3"].apply_negative(p); assert p.charisma == 1


def test_e4_health_cap_and_floor():
    p = mk(School.FIRE, health=38); EVENT["E4"].apply_positive(p); assert p.health == 40
    e = mk(School.EARTH, health=43); EVENT["E4"].apply_positive(e); assert e.health == 46
    p.health = 4; EVENT["E4"].apply_negative(p); assert p.health == 1


def test_e5_lowest_and_highest():
    p = mk(School.FIRE, strength=7, intellect=4, charisma=6, health=30)
    EVENT["E5"].apply_positive(p); assert (p.strength, p.intellect, p.charisma, p.health) == (7, 5, 6, 30)
    q = mk(School.FIRE, strength=8, intellect=5, charisma=6)
    EVENT["E5"].apply_negative(q); assert (q.strength, q.intellect, q.charisma) == (7, 5, 6)


def test_e5_ties_only_among_equals():
    seen = set()
    for seed in range(60):
        random.seed(seed)
        p = mk(School.FIRE, strength=7, intellect=5, charisma=5)
        EVENT["E5"].apply_positive(p)
        assert p.strength == 7
        seen.add("int" if p.intellect == 6 else "cha")
    assert seen == {"int", "cha"}


def test_e5_extremes_do_not_crash():
    p = mk(School.FIRE, strength=10, intellect=10, charisma=10); EVENT["E5"].apply_positive(p)
    assert max(p.strength, p.intellect, p.charisma) == 10
    q = mk(School.FIRE, strength=1, intellect=1, charisma=1); EVENT["E5"].apply_negative(q)
    assert min(q.strength, q.intellect, q.charisma) == 1


def test_e6():
    p = mk(School.FIRE, sabotaged=True, health=30)
    EVENT["E6"].apply_positive(p); assert not p.sabotaged and p.health == 30
    q = mk(School.FIRE, health=30)
    EVENT["E6"].apply_positive(q); assert q.health == 35
    r = mk(School.FIRE)
    EVENT["E6"].apply_negative(r); assert r.sabotaged
    EVENT["E6"].apply_negative(r); assert r.sabotaged  # still a single mark


# --------------------------------------------------------------------------- #
# Prep actions A1-A5
# --------------------------------------------------------------------------- #
def test_a1_a2_a3_effects_and_limits():
    p = mk(School.FIRE, health=30)
    for aid, stat in (("A1", "strength"), ("A2", "intellect"), ("A3", "charisma")):
        before = getattr(p, stat)
        assert ACTION[aid].is_available(p, [])
        ACTION[aid].apply(p, None)
        assert getattr(p, stat) == before + 1
        setattr(p, stat, 10)
        assert not ACTION[aid].is_available(p, [])


def test_a4_heal():
    p = mk(School.FIRE, health=25); ACTION["A4"].apply(p, None); assert p.health == 35
    ACTION["A4"].apply(p, None); assert p.health == 40
    assert not ACTION["A4"].is_available(p, [])
    e = mk(School.EARTH, health=40)
    assert ACTION["A4"].is_available(e, [])
    ACTION["A4"].apply(e, None); assert e.health == 46
    assert not ACTION["A4"].is_available(e, [])


def test_sabotage_rules():
    a = mk(School.AIR)                   # charisma 7
    fire = mk(School.FIRE)               # charisma 5
    assert can_be_sabotaged(a, fire)
    assert not can_be_sabotaged(fire, a)  # higher charisma target
    assert can_be_sabotaged(fire, mk(School.WATER))  # equal charisma allowed
    assert not can_be_sabotaged(a, a)
    fire.sabotaged = True
    assert not can_be_sabotaged(a, fire)  # already marked
    assert not ACTION["A5"].is_available(a, [fire])


# --------------------------------------------------------------------------- #
# Combat: attack and block
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("strength,expected", [(1, 6), (5, 10), (7, 12), (10, 15)])
def test_attack_damage(strength, expected):
    a, d = mk(School.FIRE, strength=strength), mk(School.WATER)
    combat.perform_attack(a, d)
    assert d.health == 40 - expected


@pytest.mark.parametrize("strength,expected", [(5, 5), (6, 5), (7, 6), (10, 7), (1, 3)])
def test_block_halves_rounding_down(strength, expected):
    a, d = mk(School.FIRE, strength=strength), mk(School.WATER)
    combat.perform_block(d)
    combat.perform_attack(a, d)
    assert 40 - d.health == expected


def test_block_single_use_and_cleared():
    a, d = mk(School.FIRE), mk(School.WATER)
    combat.perform_block(d)
    combat.perform_attack(a, d); assert not d.block_active and d.health == 40 - 6   # 12 // 2
    combat.perform_attack(a, d); assert d.health == 40 - 6 - 12


def test_block_restrictions():
    p = mk(School.FIRE)
    assert combat.is_block_available(p)
    combat.perform_block(p)
    assert not combat.is_block_available(p)           # already armed + last turn
    with pytest.raises(ValueError):
        combat.perform_block(p)
    p.block_active = False                              # consumed, but blocked last turn
    assert not combat.is_block_available(p)
    p.blocked_last_turn = False
    assert combat.is_block_available(p)


def test_block_stays_until_hit_and_does_not_stack():
    p = mk(School.FIRE)
    combat.perform_block(p)
    p.blocked_last_turn = False       # opponent acted, p attacked
    assert not combat.is_block_available(p)  # block still armed
    a = mk(School.FIRE, strength=10)
    combat.perform_attack(a, p)
    assert p.health == 40 - 7         # a single 50% reduction


def test_health_never_below_zero():
    a, d = mk(School.FIRE), mk(School.WATER, health=4)
    combat.perform_attack(a, d); assert d.health == 0 and not d.is_alive


# --------------------------------------------------------------------------- #
# Abilities
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize("it,expected", [(5, 18), (7, 22), (10, 28)])
def test_fireball_formula(it, expected):
    a, d = mk(School.FIRE, intellect=it), mk(School.EARTH, max_health=60, health=60)
    combat.perform_ability(a, d); assert 60 - d.health == expected


def test_fireball_vs_block():
    a, d = mk(School.FIRE), mk(School.WATER)
    combat.perform_block(d); combat.perform_ability(a, d); assert d.health == 40 - 9


@pytest.mark.parametrize("it,expected", [(5, 15), (7, 19), (10, 25)])
def test_wind_formula(it, expected):
    a, d = mk(School.AIR, intellect=it), mk(School.EARTH, max_health=60, health=60)
    combat.perform_ability(a, d); assert 60 - d.health == expected


def test_wind_ignores_and_removes_block():
    a, d = mk(School.AIR), mk(School.FIRE)
    combat.perform_block(d); combat.perform_ability(a, d)
    assert d.health == 40 - 15 and not d.block_active


@pytest.mark.parametrize("it,expected", [(5, 18), (8, 24), (10, 28)])
def test_heal_formula_and_cap(it, expected):
    p = mk(School.WATER, intellect=it, max_health=60, health=1)
    combat.perform_ability(p, mk(School.FIRE)); assert p.health == 1 + expected
    q = mk(School.WATER, health=30)
    combat.perform_ability(q, mk(School.FIRE)); assert q.health == 40


def test_heal_unavailable_at_full_health():
    p = mk(School.WATER)
    assert not combat.is_ability_available(p)
    with pytest.raises(ValueError):
        combat.perform_ability(p, mk(School.FIRE))
    assert not p.ability_used
    p.health = 39; assert combat.is_ability_available(p)


def test_ability_once_per_fight():
    a, d = mk(School.FIRE), mk(School.WATER)
    combat.perform_ability(a, d)
    assert not combat.is_ability_available(a)
    with pytest.raises(ValueError):
        combat.perform_ability(a, d)
    a.reset_for_fight(); assert combat.is_ability_available(a)


@pytest.mark.parametrize("it,expected", [(1, 1), (5, 5), (7, 7), (10, 10)])
def test_armor_reflects_full_intellect(it, expected):
    e, a = mk(School.EARTH, intellect=it), mk(School.FIRE)
    combat.perform_ability(e, a)
    combat.perform_attack(a, e)
    assert e.health == 46 and 40 - a.health == expected and not e.armor_active


@pytest.mark.parametrize("attacker_school,ability_it", [(School.FIRE, 10), (School.AIR, 10)])
def test_armor_blocks_abilities(attacker_school, ability_it):
    e, a = mk(School.EARTH), mk(attacker_school, intellect=ability_it)
    combat.perform_ability(e, a)
    combat.perform_ability(a, e)
    assert e.health == 46 and a.health == 35 and not e.armor_active


def test_armor_and_block_are_mutually_exclusive():
    e = mk(School.EARTH)
    combat.perform_block(e)
    assert not combat.is_ability_available(e)         # cannot raise armor over block
    with pytest.raises(ValueError):
        combat.perform_ability(e, mk(School.FIRE))
    e2 = mk(School.EARTH)
    combat.perform_ability(e2, mk(School.FIRE))
    assert not combat.is_block_available(e2)          # cannot block over armor
    e2.blocked_last_turn = False
    with pytest.raises(ValueError):
        combat.perform_block(e2)


# --------------------------------------------------------------------------- #
# Game state: flow, sabotage, fights
# --------------------------------------------------------------------------- #
def new_game(seed=0) -> GameState:
    random.seed(seed)
    gs = GameState(); gs.start_new_game()
    while gs.stage is Stage.SCHOOL_SELECT:
        gs.choose_school(gs.available_schools[0])
    return gs


def same(pair, expected) -> bool:
    """Compare two players by identity, ignoring order."""
    return {id(x) for x in pair} == {id(x) for x in expected}


def play_prep_turn(gs: GameState, aid: str = "A2"):
    pos = gs.current_prep_position
    gs.continue_from_handoff(); gs.continue_from_event()
    avail = {a.action_id: ok for a, ok in gs.available_prep_actions()}
    if not avail[aid]:
        aid = next(k for k, ok in avail.items() if ok and k != "A5")
    gs.select_prep_action(ACTION[aid])
    return pos


def test_school_draft_unique_and_all_assigned():
    for seed in range(20):
        gs = new_game(seed)
        assert sorted(p.school.value for p in gs.players) == ["air", "earth", "fire", "water"]
        assert gs.stage is Stage.PREP_HANDOFF


def test_prep_order_and_length():
    gs = new_game()
    order = []
    while gs.stage is Stage.PREP_HANDOFF:
        order.append(play_prep_turn(gs))
    assert order == [0, 1, 2, 3, 1, 2, 3, 0, 2, 3, 0, 1]
    assert gs.stage is Stage.SEMIFINAL_1


def test_semifinal_pairs_and_final():
    gs = new_game()
    while gs.stage is Stage.PREP_HANDOFF:
        play_prep_turn(gs)
    assert same(gs.fight_participants, (gs.players[0], gs.players[1]))
    p = gs.players
    for pl in p:
        pl.health = pl.max_health
    # force winners: kill players[1] and players[3]
    def finish(loser):
        while gs.stage in (Stage.SEMIFINAL_1, Stage.SEMIFINAL_2):
            loser.health = 1
            gs.perform_combat_action("attack") if gs.fight_defender is loser else gs.perform_combat_action("block" if combat.is_block_available(gs.fight_attacker) else "attack")
    finish(p[1]); assert gs.stage is Stage.SEMIFINAL_1_RESULT
    gs.continue_after_semifinal_1(); assert same(gs.fight_participants, (p[2], p[3]))
    finish(p[3]); assert gs.stage is Stage.SEMIFINAL_2_RESULT and p[1].eliminated
    for w in (p[0], p[2]):
        w.health = 5; w.armor_active = True; w.ability_used = True
    gs.continue_after_semifinal_2()
    assert gs.stage is Stage.FINAL and same(gs.fight_participants, (p[0], p[2]))
    for w in (p[0], p[2]):
        assert w.health == w.max_health and not w.armor_active and not w.ability_used


def test_sabotage_penalty_floor_and_clear():
    gs = new_game()
    a, b = gs.players[0], gs.players[1]
    a.sabotaged = True; a.health = 40
    b.sabotaged = True; b.health = 3
    gs._start_fight(a, b)
    assert a.health == 35 and b.health == 1 and not a.sabotaged and not b.sabotaged


def test_sabotage_applies_only_in_own_fight():
    gs = new_game()
    third = gs.players[2]; third.sabotaged = True
    gs._begin_semifinal_1()
    assert third.health == third.max_health and third.sabotaged
    gs._begin_semifinal_2()
    assert third.health == third.max_health - 5 and not third.sabotaged


def test_first_move_by_charisma_and_ties():
    gs = new_game()
    hi, lo = mk(School.AIR), mk(School.FIRE)
    gs._start_fight(lo, hi); assert gs.fight_current_index == 1
    gs._start_fight(hi, lo); assert gs.fight_current_index == 0
    results = set()
    for seed in range(40):
        random.seed(seed)
        gs._start_fight(mk(School.FIRE), mk(School.WATER)); results.add(gs.fight_current_index)
    assert results == {0, 1}


def test_death_by_reflect_gives_win_to_armor_owner():
    gs = new_game()
    earth, fire = mk(School.EARTH), mk(School.FIRE, health=3)
    gs.players = [earth, fire, mk(School.AIR), mk(School.WATER)]
    gs._begin_semifinal_1()
    gs.fight_current_index = 0
    earth.armor_active = True; earth.ability_used = True
    gs.fight_current_index = 1                       # fire attacks
    gs.perform_combat_action("attack")
    assert fire.health == 0 and fire.eliminated
    assert gs.finalists == [earth] and gs.stage is Stage.SEMIFINAL_1_RESULT


def test_turn_passes_after_each_action():
    gs = new_game()
    while gs.stage is Stage.PREP_HANDOFF:
        play_prep_turn(gs)
    first = gs.fight_current_index
    gs.perform_combat_action("attack")
    assert gs.fight_current_index == 1 - first


# --------------------------------------------------------------------------- #
# Fuzz: full games must finish and keep invariants
# --------------------------------------------------------------------------- #
def test_random_full_games_keep_invariants():
    for seed in range(150):
        random.seed(seed)
        gs = GameState(); gs.start_new_game()
        fight_turns = 0
        while gs.stage is not Stage.VICTORY:
            st = gs.stage
            if st is Stage.SCHOOL_SELECT:
                gs.choose_school(random.choice(gs.available_schools))
            elif st is Stage.PREP_HANDOFF:
                gs.continue_from_handoff()
            elif st is Stage.PREP_EVENT:
                gs.continue_from_event()
            elif st is Stage.PREP_ACTION:
                a = random.choice([x for x, ok in gs.available_prep_actions() if ok])
                gs.select_prep_action(a)
                if a.requires_target:
                    gs.select_sabotage_target(random.choice(gs.valid_sabotage_targets()))
            elif st is Stage.SEMIFINAL_1_RESULT:
                gs.continue_after_semifinal_1()
            elif st is Stage.SEMIFINAL_2_RESULT:
                gs.continue_after_semifinal_2()
            else:
                at = gs.fight_attacker
                opts = ["attack"]
                if combat.is_block_available(at): opts.append("block")
                if combat.is_ability_available(at): opts.append("ability")
                gs.perform_combat_action(random.choice(opts))
                fight_turns += 1
                assert fight_turns < 1000
            for p in (q for q in gs.players if q is not None):
                assert 0 <= p.health <= p.max_health
                assert 1 <= p.strength <= 10 and 1 <= p.intellect <= 10 and 1 <= p.charisma <= 10
                assert not (p.armor_active and p.block_active)
        assert gs.champion is not None
