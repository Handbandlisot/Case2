"""Entry point for "Турнир Четырёх Стихий".

Run with: python main.py

This module only wires pygame's event loop to the pure game-state machine
in ``logic.game_state`` and to the drawing helpers in ``ui``. It contains no
tournament rules itself.
"""

from __future__ import annotations

import sys

import pygame

from config import (
    ACTION_DESCRIPTION_HEIGHT,
    ACTION_GRID_COLUMNS,
    ACTION_PANEL_BOTTOM_PADDING,
    ACTION_PANEL_HEADER_OFFSET,
    ACTION_ROW_HEIGHT,
    BUTTON_HEIGHT,
    BUTTON_SPACING,
    COLOR_ACCENT,
    COLOR_BACKGROUND,
    COLOR_TEXT_MUTED,
    COLOR_TEXT_PRIMARY,
    COLOR_TEXT_SECONDARY,
    FONT_SIZE_BODY,
    FONT_SIZE_BUTTON,
    FONT_SIZE_HEADING,
    FONT_SIZE_SMALL,
    FONT_SIZE_SUBTITLE,
    FONT_SIZE_TITLE,
    FPS,
    PADDING,
    ROSTER_CARD_HEIGHT,
    ROSTER_ROW_GAP,
    ROSTER_TOP,
    SCHOOL_ABILITY_BATTLE_HINT,
    SCHOOL_ABILITY_DESCRIPTION,
    SCHOOL_BONUS_DESCRIPTION,
    SCHOOL_COLORS,
    SCREEN_HEIGHT,
    SCREEN_WIDTH,
    SECTION_GAP,
    WINDOW_TITLE,
)
from logic import combat
from logic.actions_pool import can_be_sabotaged
from logic.game_state import GameState, Stage
from models.player import Player, School
from ui.button import Button
from ui.event_modal import draw_event_modal
from ui.panel import (
    draw_log_panel,
    draw_panel,
    draw_player_card,
    draw_school_icon,
    draw_text,
    draw_wrapped_text,
    log_panel_height,
)

FontMap = dict[str, pygame.font.Font]
ClickTarget = tuple[Button, "callable"]


def load_fonts() -> FontMap:
    """Load a Cyrillic-capable font family in every size the UI needs."""
    family = "dejavusans,arial,freesans,notosans"
    return {
        "title": pygame.font.SysFont(family, FONT_SIZE_TITLE, bold=True),
        "subtitle": pygame.font.SysFont(family, FONT_SIZE_SUBTITLE),
        "heading": pygame.font.SysFont(family, FONT_SIZE_HEADING, bold=True),
        "body": pygame.font.SysFont(family, FONT_SIZE_BODY),
        "small": pygame.font.SysFont(family, FONT_SIZE_SMALL),
        "button": pygame.font.SysFont(family, FONT_SIZE_BUTTON),
    }


# --------------------------------------------------------------------------- #
# Stage: intro
# --------------------------------------------------------------------------- #
def draw_intro(screen: pygame.Surface, fonts: FontMap, state: GameState) -> list[ClickTarget]:
    draw_text(
        screen, WINDOW_TITLE, fonts["title"], COLOR_TEXT_PRIMARY,
        (SCREEN_WIDTH // 2, 90), center=True,
    )
    draw_text(
        screen, "Четыре чемпиона, три боя, ОДИН победитель", fonts["subtitle"],
        COLOR_TEXT_SECONDARY, (SCREEN_WIDTH // 2, 145), center=True,
    )

    panel_rect = pygame.Rect(0, 0, 680, 220)
    panel_rect.center = (SCREEN_WIDTH // 2, 300)
    draw_panel(screen, panel_rect)

    icons_y = panel_rect.y + 36
    spacing = panel_rect.width // 4
    for index, school in enumerate(School):
        x = panel_rect.x + spacing * index + spacing // 2
        draw_school_icon(screen, school.value, (x, icons_y), 32)

    lines = [
        "Раз в сто лет четыре школы выбирают лучших учеников.",
        "Развивайте чемпиона, переживите полуфинал и выиграйте финал.",
        "Игра для четырёх человек за одним компьютером.",
    ]
    y = panel_rect.y + 96
    for line in lines:
        draw_text(screen, line, fonts["body"], COLOR_TEXT_SECONDARY, (SCREEN_WIDTH // 2, y), center=True)
        y += 28

    button = Button(
        pygame.Rect(0, 0, 220, BUTTON_HEIGHT),
        "Начать турнир",
        variant="primary",
    )
    button.rect.center = (SCREEN_WIDTH // 2, panel_rect.bottom + 60)
    button.draw(screen, fonts["button"])
    return [(button, state.start_new_game)]


# --------------------------------------------------------------------------- #
# Stage: school select
# --------------------------------------------------------------------------- #
def draw_school_select(screen: pygame.Surface, fonts: FontMap, state: GameState) -> list[ClickTarget]:
    position = state.current_picker_position
    draw_text(
        screen, f"Игрок {position + 1}, выберите школу", fonts["title"], COLOR_TEXT_PRIMARY,
        (SCREEN_WIDTH // 2, 72), center=True,
    )
    draw_text(
        screen,
        f"Выбор {state.school_pick_index + 1} из 4 · школы не повторяются",
        fonts["subtitle"], COLOR_TEXT_SECONDARY, (SCREEN_WIDTH // 2, 114), center=True,
    )

    card_w, card_h = 300, 240
    gap = 24
    grid_w = card_w * 2 + gap
    origin_x = SCREEN_WIDTH // 2 - grid_w // 2
    origin_y = 160
    text_width = card_w - 32 - 24  # leave room for the icon on the name line

    targets: list[ClickTarget] = []
    for index, school in enumerate(School):
        col, row = index % 2, index // 2
        rect = pygame.Rect(origin_x + col * (card_w + gap), origin_y + row * (card_h + gap), card_w, card_h)
        available = school in state.available_schools
        school_border_color = (SCHOOL_COLORS[school.value] if available else None)

        draw_panel(screen, rect, border_color=school_border_color)

        name_color = SCHOOL_COLORS[school.value] if available else COLOR_TEXT_SECONDARY
        icon_center = (rect.x + 28, rect.y + 28)
        draw_school_icon(screen, school.value, icon_center, 24, enabled=available)
        draw_text(screen, school.display_name, fonts["body"], name_color, (rect.x + 44, rect.y + 16))

        bonus_y = draw_wrapped_text(
            screen, f"Бонус: {SCHOOL_BONUS_DESCRIPTION[school.value]}", fonts["small"],
            COLOR_TEXT_SECONDARY, (rect.x + 16, rect.y + 56), text_width,
        )
        ability_bottom = draw_wrapped_text(
            screen, f"Способность: {school.ability_name}", fonts["small"],
            COLOR_TEXT_SECONDARY, (rect.x + 16, bonus_y + 6), text_width,
        )
        draw_wrapped_text(
            screen,
            SCHOOL_ABILITY_DESCRIPTION[school.value],
            fonts["small"],
            COLOR_TEXT_MUTED,
            (rect.x + 16, ability_bottom + 4),
            text_width,
        )

        button = Button(
            pygame.Rect(rect.x + 16, rect.bottom - 46, card_w - 32, 34),
            "Выбрать" if available else "Занято",
            enabled=available,
            variant="primary" if available else "default",
        )
        button.draw(screen, fonts["button"])
        if available:
            targets.append((button, lambda s=school: state.choose_school(s)))
    return targets


# --------------------------------------------------------------------------- #
# Stage: preparation
# --------------------------------------------------------------------------- #
def _draw_prep_roster(screen: pygame.Surface, fonts: FontMap, state: GameState) -> pygame.Rect:
    """Draw the header + all four player cards; return the log panel rect."""
    draw_text(
        screen, f"Подготовка · раунд {state.prep_round} из 3", fonts["title"], COLOR_TEXT_PRIMARY,
        (SCREEN_WIDTH // 2, 42), center=True,
    )
    current = state.current_player
    draw_text(
        screen, f"Ход: {current.name} ({current.school.display_name})", fonts["subtitle"],
        COLOR_TEXT_SECONDARY, (SCREEN_WIDTH // 2, 84), center=True,
    )

    card_w = (SCREEN_WIDTH - PADDING * 3) // 2
    card_h = ROSTER_CARD_HEIGHT
    top = ROSTER_TOP
    for index, player in enumerate(state.players):
        assert player is not None
        col, row = index % 2, index // 2
        rect = pygame.Rect(
            PADDING + col * (card_w + PADDING), top + row * (card_h + ROSTER_ROW_GAP), card_w, card_h
        )
        draw_player_card(screen, fonts, rect, player, active=(player is current))

    log_top = top + 2 * (card_h + ROSTER_ROW_GAP) + SECTION_GAP
    return pygame.Rect(PADDING, log_top, SCREEN_WIDTH - 2 * PADDING, log_panel_height())


def draw_prep_handoff(screen: pygame.Surface, fonts: FontMap, state: GameState) -> list[ClickTarget]:
    player = state.current_player
    panel_rect = pygame.Rect(0, 0, 520, 220)
    panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 20)
    draw_panel(screen, panel_rect, active=True)

    draw_text(
        screen, f"Передайте устройство: {player.name}", fonts["heading"], COLOR_TEXT_PRIMARY,
        (panel_rect.centerx, panel_rect.y + 50), center=True,
    )
    draw_text(
        screen, player.school.display_name, fonts["body"], SCHOOL_COLORS[player.school.value],
        (panel_rect.centerx, panel_rect.y + 88), center=True,
    )
    draw_text(
        screen, "Нажмите «Продолжить», когда будете готовы.", fonts["small"], COLOR_TEXT_SECONDARY,
        (panel_rect.centerx, panel_rect.y + 130), center=True,
    )

    button = Button(pygame.Rect(0, 0, 220, BUTTON_HEIGHT), "Продолжить", variant="primary")
    button.rect.center = (panel_rect.centerx, panel_rect.bottom - 40)
    button.draw(screen, fonts["button"])
    return [(button, state.continue_from_handoff)]


def draw_prep_event(screen: pygame.Surface, fonts: FontMap, state: GameState) -> list[ClickTarget]:
    log_rect = _draw_prep_roster(screen, fonts, state)
    draw_log_panel(screen, fonts, log_rect, list(state.log))

    assert state.current_event is not None
    button = Button(pygame.Rect(0, 0, 220, BUTTON_HEIGHT), "Далее: действия", variant="primary")
    draw_event_modal(
        screen, fonts, state.current_event, state.current_event_positive,
        state.current_event_message, button,
    )
    return [(button, state.continue_from_event)]


def _action_panel_height(action_count: int) -> int:
    """Panel height needed to fit every action button in its grid, with no clipping."""
    rows = -(-action_count // ACTION_GRID_COLUMNS)  # ceil division
    return (
        ACTION_PANEL_HEADER_OFFSET
        + (rows - 1) * ACTION_ROW_HEIGHT
        + BUTTON_HEIGHT
        + ACTION_DESCRIPTION_HEIGHT
        + ACTION_PANEL_BOTTOM_PADDING
    )


def draw_prep_action(screen: pygame.Surface, fonts: FontMap, state: GameState) -> list[ClickTarget]:
    log_rect = _draw_prep_roster(screen, fonts, state)

    action_count = len(state.available_prep_actions())
    panel_height = _action_panel_height(action_count)
    action_panel = pygame.Rect(log_rect.x, log_rect.bottom + SECTION_GAP, log_rect.width, panel_height)
    draw_panel(screen, action_panel)

    targets: list[ClickTarget] = []

    if state.pending_action is not None:
        draw_text(
            screen, f"{state.pending_action.name}: выберите цель", fonts["body"],
            COLOR_TEXT_PRIMARY, (action_panel.x + 16, action_panel.y + 14),
        )
        valid_targets = state.valid_sabotage_targets()
        x = action_panel.x + 16
        y = action_panel.y + 50
        for opponent in state.prep_opponents:
            ok = opponent in valid_targets
            button = Button(pygame.Rect(x, y, 260, BUTTON_HEIGHT), opponent.name, enabled=ok)
            button.draw(screen, fonts["button"])
            if ok:
                targets.append((button, lambda o=opponent: state.select_sabotage_target(o)))
            x += 280
        cancel = Button(pygame.Rect(action_panel.x + 16, action_panel.bottom - 56, 160, 40), "Отмена")
        cancel.draw(screen, fonts["button"])
        targets.append((cancel, state.cancel_pending_action))
        draw_log_panel(screen, fonts, log_rect, list(state.log))
        return targets

    draw_text(
        screen, "Выберите одно действие", fonts["body"], COLOR_TEXT_PRIMARY,
        (action_panel.x + 16, action_panel.y + 14),
    )
    x = action_panel.x + 16
    y = action_panel.y + ACTION_PANEL_HEADER_OFFSET
    col_w = (action_panel.width - 32 - (ACTION_GRID_COLUMNS - 1) * 12) // ACTION_GRID_COLUMNS
    for index, (action, available) in enumerate(state.available_prep_actions()):
        col, row = index % ACTION_GRID_COLUMNS, index // ACTION_GRID_COLUMNS
        rect = pygame.Rect(x + col * (col_w + 12), y + row * ACTION_ROW_HEIGHT, col_w, BUTTON_HEIGHT)
        button = Button(rect, action.name, enabled=available)
        button.draw(screen, fonts["button"])
        draw_text(
            screen, action.description, fonts["small"], COLOR_TEXT_SECONDARY,
            (rect.x, rect.bottom + 4),
        )
        if available:
            targets.append((button, lambda a=action: state.select_prep_action(a)))

    draw_log_panel(screen, fonts, log_rect, list(state.log))
    return targets


# --------------------------------------------------------------------------- #
# Stage: fights
# --------------------------------------------------------------------------- #
def draw_fight(screen: pygame.Surface, fonts: FontMap, state: GameState, title: str) -> list[ClickTarget]:
    title_y = 70
    turn_y = 112
    cards_top = 145

    draw_text(
        screen,
        title,
        fonts["title"],
        COLOR_TEXT_PRIMARY,
        (SCREEN_WIDTH // 2, title_y),
        center=True,
    )
    attacker = state.fight_attacker
    draw_text(
        screen, f"Ход · действует {attacker.name} ({attacker.school.display_name})",
        fonts["subtitle"], COLOR_TEXT_SECONDARY,
        (SCREEN_WIDTH // 2, turn_y), center=True,
    )

    card_w = (SCREEN_WIDTH - PADDING * 3) // 2
    card_h = 150
    left, right = state.fight_participants
    assert left is not None and right is not None
    left_rect = pygame.Rect(PADDING, cards_top, card_w, card_h)
    right_rect = pygame.Rect(PADDING * 2 + card_w, cards_top, card_w, card_h)
    draw_player_card(screen, fonts, left_rect, left, active=(left is attacker), show_ability_status=True)
    draw_player_card(screen, fonts, right_rect, right, active=(right is attacker), show_ability_status=True)
    draw_text(
        screen,
        "VS",
        fonts["body"],
        COLOR_ACCENT,
        (SCREEN_WIDTH // 2, cards_top + card_h // 2),
        center=True,
    )

    log_rect = pygame.Rect(PADDING, left_rect.bottom + 16, SCREEN_WIDTH - 2 * PADDING, 170)
    draw_log_panel(screen, fonts, log_rect, list(state.log))

    button_w = (SCREEN_WIDTH - 2 * PADDING - 2 * BUTTON_SPACING) // 3
    y = log_rect.bottom + 24

    attack_rect = pygame.Rect(PADDING, y, button_w, BUTTON_HEIGHT)
    attack_button = Button(attack_rect, f"Атака · {combat.attack_damage_preview(attacker)}")
    attack_button.draw(screen, fonts["button"])

    block_rect = pygame.Rect(PADDING + button_w + BUTTON_SPACING, y, button_w, BUTTON_HEIGHT)
    block_enabled = combat.is_block_available(attacker)
    block_button = Button(block_rect, "Блок · 50%", enabled=block_enabled)
    block_button.draw(screen, fonts["button"])

    ability_rect = pygame.Rect(PADDING + 2 * (button_w + BUTTON_SPACING), y, button_w, BUTTON_HEIGHT)
    ability_enabled = combat.is_ability_available(attacker)
    preview = combat.ability_damage_preview(attacker)
    value = f"+{preview}" if attacker.school is School.WATER else str(preview)
    label = attacker.school.ability_name + (f" · {value}" if preview else "")
    ability_button = Button(ability_rect, label, enabled=ability_enabled, variant="ability")
    ability_button.draw(screen, fonts["button"])
    draw_text(
        screen,
        SCHOOL_ABILITY_BATTLE_HINT[attacker.school.value],
        fonts["small"],
        COLOR_TEXT_SECONDARY,
        (ability_rect.centerx, ability_rect.bottom + 16),
        center=True,
    )

    return [
        (attack_button, lambda: state.perform_combat_action("attack")),
        (block_button, lambda: state.perform_combat_action("block")),
        (ability_button, lambda: state.perform_combat_action("ability")),
    ]


# --------------------------------------------------------------------------- #
# Stage: results
# --------------------------------------------------------------------------- #
def draw_result_screen(
    screen: pygame.Surface,
    fonts: FontMap,
    title: str,
    winner: Player,
    button_label: str,
    on_continue,
    trophy: bool = False,
) -> list[ClickTarget]:
    draw_text(screen, title, fonts["title"], COLOR_TEXT_PRIMARY, (SCREEN_WIDTH // 2, 90), center=True)

    panel_rect = pygame.Rect(0, 0, 340, 200)
    panel_rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 30)
    draw_panel(screen, panel_rect, active=True)

    draw_school_icon(screen, winner.school.value, (panel_rect.centerx, panel_rect.y + 40), 40)
    draw_text(screen, winner.name, fonts["heading"], COLOR_TEXT_PRIMARY, (panel_rect.centerx, panel_rect.y + 76), center=True)
    draw_text(
        screen, winner.school.display_name, fonts["body"], SCHOOL_COLORS[winner.school.value],
        (panel_rect.centerx, panel_rect.y + 102), center=True,
    )
    stats_line = f"HP {winner.health}/{winner.max_health} · СИЛ {winner.strength} · ИНТ {winner.intellect} · ХАР {winner.charisma}"
    draw_text(screen, stats_line, fonts["small"], COLOR_TEXT_SECONDARY, (panel_rect.centerx, panel_rect.y + 132), center=True)

    if trophy:
        draw_text(screen, "Чемпион Стихий!", fonts["heading"], COLOR_ACCENT, (panel_rect.centerx, panel_rect.y + 166), center=True)

    button = Button(pygame.Rect(0, 0, 240, BUTTON_HEIGHT), button_label, variant="primary")
    button.rect.center = (SCREEN_WIDTH // 2, panel_rect.bottom + 60)
    button.draw(screen, fonts["button"])
    return [(button, on_continue)]


# --------------------------------------------------------------------------- #
# Dispatch
# --------------------------------------------------------------------------- #
def draw_stage(screen: pygame.Surface, fonts: FontMap, state: GameState) -> list[ClickTarget]:
    if state.stage is Stage.INTRO:
        return draw_intro(screen, fonts, state)
    if state.stage is Stage.SCHOOL_SELECT:
        return draw_school_select(screen, fonts, state)
    if state.stage is Stage.PREP_HANDOFF:
        return draw_prep_handoff(screen, fonts, state)
    if state.stage is Stage.PREP_EVENT:
        return draw_prep_event(screen, fonts, state)
    if state.stage is Stage.PREP_ACTION:
        return draw_prep_action(screen, fonts, state)
    if state.stage is Stage.SEMIFINAL_1:
        return draw_fight(screen, fonts, state, "Первый полуфинал")
    if state.stage is Stage.SEMIFINAL_2:
        return draw_fight(screen, fonts, state, "Второй полуфинал")
    if state.stage is Stage.FINAL:
        return draw_fight(screen, fonts, state, "Финал")
    if state.stage is Stage.SEMIFINAL_1_RESULT:
        return draw_result_screen(
            screen, fonts, "Победитель полуфинала", state.finalists[0],
            "К следующему бою", state.continue_after_semifinal_1,
        )
    if state.stage is Stage.SEMIFINAL_2_RESULT:
        return draw_result_screen(
            screen, fonts, "Победитель полуфинала", state.finalists[1],
            "К финалу", state.continue_after_semifinal_2,
        )
    if state.stage is Stage.VICTORY:
        assert state.champion is not None
        return draw_result_screen(
            screen, fonts, "Финал завершён", state.champion,
            "Новый турнир", state.start_new_game, trophy=True,
        )
    return []


def main() -> None:
    """Initialise pygame and run the main loop until the window is closed."""
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption(WINDOW_TITLE)
    clock = pygame.time.Clock()
    fonts = load_fonts()
    state = GameState()

    running = True
    while running:
        clicked = False
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked = True

        screen.fill(COLOR_BACKGROUND)
        targets = draw_stage(screen, fonts, state)

        if clicked:
            mouse_pos = pygame.mouse.get_pos()
            for button, callback in targets:
                if button.is_clicked(mouse_pos, True):
                    callback()
                    break

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
