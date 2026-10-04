"""The central state machine for a full tournament playthrough."""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional

from config import LOG_MAX_MESSAGES, PLAYER_COUNT, PREP_ROUNDS, \
    PREP_TURN_ORDER, SABOTAGE_DAMAGE
from logic import combat
from logic.actions_pool import ACTIONS, can_be_sabotaged
from logic.events_pool import draw_random_event, resolve_event
from models.action import PrepAction
from models.event import PrepEvent
from models.player import Player, School


class Stage(Enum):
    """Every screen the game can be in."""

    INTRO = auto()
    SCHOOL_SELECT = auto()
    PREP_HANDOFF = auto()
    PREP_EVENT = auto()
    PREP_ACTION = auto()
    SEMIFINAL_1 = auto()
    SEMIFINAL_1_RESULT = auto()
    SEMIFINAL_2 = auto()
    SEMIFINAL_2_RESULT = auto()
    FINAL = auto()
    VICTORY = auto()


@dataclass
class GameState:
    """Owns every mutable piece of tournament data and stage transitions.

    The UI layer only ever reads this object's public attributes/properties
    and calls its methods in reaction to input; it never mutates players or
    stats directly.
    """

    stage: Stage = Stage.INTRO
    players: list[Optional[Player]] = field(
        default_factory=lambda: [None] * PLAYER_COUNT)
    log: deque[str] = field(
        default_factory=lambda: deque(maxlen=LOG_MAX_MESSAGES))

    # -- school selection -------------------------------------------------
    available_schools: list[School] = field(
        default_factory=lambda: list(School))
    school_pick_order: list[int] = field(default_factory=list)
    school_pick_index: int = 0

    # -- preparation --------------------------------------------------------
    prep_round: int = 1
    prep_turn_index: int = 0
    current_event: Optional[PrepEvent] = None
    current_event_message: str = ""
    current_event_positive: bool = True
    pending_action: Optional[PrepAction] = None

    # -- fights -------------------------------------------------------------
    fight_participants: tuple[Optional[Player], Optional[Player]] = (None,
                                                                     None)
    fight_current_index: int = 0
    finalists: list[Player] = field(default_factory=list)
    champion: Optional[Player] = None


    def start_new_game(self) -> None:
        """Reset all state and move to the school-selection screen."""
        self.players = [None] * PLAYER_COUNT
        self.log = deque(maxlen=LOG_MAX_MESSAGES)
        self.available_schools = list(School)
        self.school_pick_order = list(range(PLAYER_COUNT))
        random.shuffle(self.school_pick_order)
        self.school_pick_index = 0
        self.prep_round = 1
        self.prep_turn_index = 0
        self.current_event = None
        self.pending_action = None
        self.fight_participants = (None, None)
        self.finalists = []
        self.champion = None
        self.stage = Stage.SCHOOL_SELECT


    # -- school selection -----------------------------------------------------
    @property
    def current_picker_position(self) -> int:
        """Board position (0-3) of the player currently choosing a school."""
        return self.school_pick_order[self.school_pick_index]


    def choose_school(self, school: School) -> None:
        """Assign ``school`` to the current picker and advance the draft."""
        position = self.current_picker_position
        self.players[position] = Player.create(f"Игрок {position + 1}", school)
        self.available_schools.remove(school)
        self.school_pick_index += 1
        if self.school_pick_index >= PLAYER_COUNT:
            self._begin_preparation()


    # -- preparation ------------------------------------------------------
    def _begin_preparation(self) -> None:
        self.prep_round = 1
        self.prep_turn_index = 0
        self.stage = Stage.PREP_HANDOFF


    @property
    def current_prep_position(self) -> int:
        """Board position of the player whose preparation turn it is."""
        return PREP_TURN_ORDER[self.prep_round][self.prep_turn_index]


    @property
    def current_player(self) -> Player:
        """The champion currently acting (preparation or combat)."""
        if self.stage in (Stage.PREP_HANDOFF, Stage.PREP_EVENT,
                          Stage.PREP_ACTION):
            player = self.players[self.current_prep_position]
            assert player is not None
            return player
        fighter = self.fight_participants[self.fight_current_index]
        assert fighter is not None
        return fighter


    @property
    def prep_opponents(self) -> list[Player]:
        """The three champions who are not currently taking a prep turn."""
        return [p for p in self.players if
                p is not None and p is not self.current_player]


    def continue_from_handoff(self) -> None:
        """Player pressed "Продолжить": roll and apply the random event."""
        event = draw_random_event()
        is_positive, message = resolve_event(self.current_player, event)
        self.current_event = event
        self.current_event_positive = is_positive
        self.current_event_message = message
        self.log.append(message)
        self.stage = Stage.PREP_EVENT


    def continue_from_event(self) -> None:
        """Player pressed "Далее: действия": open the action picker."""
        self.pending_action = None
        self.stage = Stage.PREP_ACTION


    def available_prep_actions(self) -> list[tuple[PrepAction, bool]]:
        """Return every prep action paired with whether it is enabled."""
        opponents = self.prep_opponents
        return [
            (action, action.is_available(self.current_player, opponents))
            for action in ACTIONS
        ]


    def select_prep_action(self, action: PrepAction) -> None:
        """Handle a click on an action button.

        Non-targeted actions resolve immediately; the sabotage action first
        waits for an opponent to be picked via :meth:`select_sabotage_target`.
        """
        if action.requires_target:
            self.pending_action = action
            return
        message = action.apply(self.current_player, None)
        self._finish_prep_action(message)


    def valid_sabotage_targets(self) -> list[Player]:
        """Opponents that may legally be sabotaged right now."""
        actor = self.current_player
        return [p for p in self.prep_opponents if can_be_sabotaged(actor, p)]


    def select_sabotage_target(self, target: Player) -> None:
        """Resolve the pending sabotage action against ``target``."""
        assert self.pending_action is not None
        message = self.pending_action.apply(self.current_player, target)
        self._finish_prep_action(message)


    def cancel_pending_action(self) -> None:
        """Back out of the sabotage target picker without spending the turn."""
        self.pending_action = None


    def _finish_prep_action(self, message: str) -> None:
        self.log.append(message)
        self.pending_action = None
        self.current_event = None
        self.prep_turn_index += 1
        if self.prep_turn_index >= PLAYER_COUNT:
            self.prep_turn_index = 0
            self.prep_round += 1
        if self.prep_round > PREP_ROUNDS:
            self._begin_semifinal_1()
        else:
            self.stage = Stage.PREP_HANDOFF


    # -- fights -------------------------------------------------------------
    def _start_fight(self, first: Player, second: Player) -> None:
        for fighter in (first, second):
            fighter.reset_for_fight()
        for fighter in (first, second):
            if fighter.sabotaged:
                fighter.change_health(-SABOTAGE_DAMAGE, floor=1)
                self.log.append(
                    f"{fighter.log_tag} начал(а) бой с потерей {SABOTAGE_DAMAGE} здоровья"
                )
            fighter.sabotaged = False
        if first.charisma > second.charisma:
            self.fight_current_index = 0
        elif second.charisma > first.charisma:
            self.fight_current_index = 1
        else:
            self.fight_current_index = random.choice([0, 1])
        self.fight_participants = (first, second)


    def _begin_semifinal_1(self) -> None:
        first, second = self.players[0], self.players[1]
        assert first is not None and second is not None
        self._start_fight(first, second)
        self.stage = Stage.SEMIFINAL_1


    def _begin_semifinal_2(self) -> None:
        first, second = self.players[2], self.players[3]
        assert first is not None and second is not None
        self._start_fight(first, second)
        self.stage = Stage.SEMIFINAL_2


    def continue_after_semifinal_1(self) -> None:
        """Advance from the first semifinal's result screen to the second."""
        self._begin_semifinal_2()


    def continue_after_semifinal_2(self) -> None:
        """Advance from the second semifinal's result screen to the final."""
        for finalist in self.finalists:
            finalist.restore_full_health()
        first, second = self.finalists
        self._start_fight(first, second)
        self.stage = Stage.FINAL


    @property
    def fight_attacker(self) -> Player:
        """The champion whose turn it currently is in the active fight."""
        fighter = self.fight_participants[self.fight_current_index]
        assert fighter is not None
        return fighter


    @property
    def fight_defender(self) -> Player:
        """The champion on the receiving end of the current fight turn."""
        fighter = self.fight_participants[1 - self.fight_current_index]
        assert fighter is not None
        return fighter


    def perform_combat_action(self, kind: str,
                              target: Optional[Player] = None) -> None:
        """Resolve one combat action ("attack", "block" or "ability")."""
        attacker, defender = self.fight_attacker, self.fight_defender
        if kind == "attack":
            message = combat.perform_attack(attacker, defender)
        elif kind == "block":
            message = combat.perform_block(attacker)
        elif kind == "ability":
            message = combat.perform_ability(attacker, defender)
        else:
            raise ValueError(f"Unknown combat action: {kind}")
        self.log.append(message)
        self._check_fight_outcome(attacker, defender)


    def _check_fight_outcome(self, attacker: Player, defender: Player) -> None:
        if not attacker.is_alive:
            winner, loser = defender, attacker
        elif not defender.is_alive:
            winner, loser = attacker, defender
        else:
            self.fight_current_index = 1 - self.fight_current_index
            return
        loser.eliminated = True
        self.log.append(f"{winner.log_tag} победил(а) в бою")
        if self.stage is Stage.SEMIFINAL_1:
            self.finalists.append(winner)
            self.stage = Stage.SEMIFINAL_1_RESULT
        elif self.stage is Stage.SEMIFINAL_2:
            self.finalists.append(winner)
            self.stage = Stage.SEMIFINAL_2_RESULT
        elif self.stage is Stage.FINAL:
            self.champion = winner
            self.log.append(f"{winner.log_tag} победил(а) в финале")
            self.stage = Stage.VICTORY
