"""Экраны подготовки к турниру: меню -> 10 дней (событие + действие на игрока) -> результаты."""
import random
import pygame

from ui import (Button, draw_text_block, draw_player_panel, WIDTH, HEIGHT,
                 BG, PANEL, PANEL_LIGHT, TEXT, TEXT_DIM, ACCENT, GOOD, BAD, BORDER)
from player import Player, STAT_NAMES
from game_data import EVENTS, TRAININGS, SABOTAGE_ACTIONS, success_chance

TOTAL_DAYS = 1


def apply_effect(player: Player, effect: dict):
    parts = []
    for key, val in effect.items():
        if key == "energy":
            player.change_energy(val)
        else:
            player.change_stat(key, val)
        sign = "+" if val >= 0 else ""
        label = "Энергия" if key == "energy" else STAT_NAMES.get(key, key)
        parts.append(f"{label} {sign}{val}")
    return ", ".join(parts) if parts else "без эффекта"


class MenuState:
    def __init__(self, game):
        self.game = game
        self.buttons = [
            Button((WIDTH // 2 - 140, 440, 280, 56), "Начать турнир", self.start),
        ]

    def start(self):
        names = ["Игрок 1", "Игрок 2", "Игрок 3", "Игрок 4"]
        self.game.players = [Player(n) for n in names]
        self.game.set_state(PreparationState(self.game))

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, surf, font_big, font, font_small):
        surf.fill(BG)
        title = font_big.render("Турнир школ стихий", True, ACCENT)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 160)))
        sub = ("4 игрока по очереди готовятся 10 дней: пассивные события и активные\n"
               "действия (тренировки/саботаж), затем турнирные бои 1×1.")
        y = 240
        for line in sub.split("\n"):
            r = font.render(line, True, TEXT_DIM)
            surf.blit(r, r.get_rect(center=(WIDTH // 2, y)))
            y += 30
        for b in self.buttons:
            b.draw(surf, font, font_small)


class PreparationState:
    """Управляет циклом: pass_device -> event -> action -> (target) -> result -> следующий игрок/день."""

    def __init__(self, game):
        self.game = game
        self.day = 1
        self.turn_index = 0
        self.phase = "pass_device"
        self.event_result_text = ""
        self.action_result_text = ""
        self.pending_sabotage = None
        self.buttons = []
        self._build_pass_device()

    # ---------- helpers ----------
    @property
    def current_player(self):
        return self.game.players[self.turn_index]

    def _roll(self, stat_value):
        return random.randint(1, 100) <= success_chance(stat_value)

    # ---------- phase builders ----------
    def _build_pass_device(self):
        self.phase = "pass_device"
        self.buttons = [Button((WIDTH // 2 - 130, 480, 260, 56), "Продолжить", self._enter_event)]

    def _enter_event(self):
        player = self.current_player
        ev = random.choice(EVENTS)
        self.current_event = ev
        good = self._roll(player.stats[ev["stat"]])
        if ev["kind"] == "positive":
            effect = ev["crit_effect"] if good else ev["normal_effect"]
            headline = "✨ Критический успех!" if good else "Обычный результат."
        else:
            effect = ev["avoid_effect"] if good else ev["fail_effect"]
            headline = "🛡️ Штраф почти избежан!" if good else "Не повезло."
        applied = apply_effect(player, effect)
        self.event_result_text = f"{headline} ({applied})"
        self.phase = "event"
        self.buttons = [Button((WIDTH // 2 - 130, 560, 260, 56), "Далее: действие", self._enter_action)]

    def _enter_action(self):
        self.phase = "action"
        player = self.current_player
        btns = []
        x, y, w, h, gap = 60, 220, 400, 46, 10
        row = 0
        for t in TRAININGS:
            can = player.energy >= t["cost"]
            btns.append(Button(
                (x, y + row * (h + gap), w, h),
                f"{t['placeholder']} {t['desc']} (-{t['cost']} эн.)",
                (lambda tt=t: self._do_training(tt)),
                subtitle=f"{STAT_NAMES[t['stat']]}", enabled=can,
            ))
            row += 1
        x2 = 520
        row2 = 0
        for a in SABOTAGE_ACTIONS:
            can = player.energy >= a["cost"] and self._has_target(player)
            btns.append(Button(
                (x2, y + row2 * (h + gap), w, h),
                f"{a['placeholder']} {a['desc']} (-{a['cost']} эн.)",
                (lambda aa=a: self._start_target_select(aa)),
                subtitle="Хитрость / саботаж", enabled=can,
            ))
            row2 += 1
        btns.append(Button((x2, y + row2 * (h + gap), w, h), "Пропустить ход", self._resolve_no_action))
        self.buttons = btns

    def _has_target(self, player):
        return any(p is not player for p in self.game.players)

    def _do_training(self, t):
        player = self.current_player
        player.change_energy(-t["cost"])
        good = self._roll(player.stats[t["stat"]])
        effect = t["crit_effect"] if good else t["normal_effect"]
        applied = apply_effect(player, effect)
        headline = "✨ Отличная тренировка!" if good else "Тренировка прошла в обычном темпе."
        self.action_result_text = f"{headline} ({applied})"
        self._go_action_result()

    def _start_target_select(self, action):
        self.pending_sabotage = action
        self.phase = "target"
        player = self.current_player
        btns = []
        y = 240
        for p in self.game.players:
            if p is player:
                continue
            btns.append(Button((WIDTH // 2 - 150, y, 300, 50), p.name, (lambda pp=p: self._do_sabotage(pp))))
            y += 60
        self.buttons = btns

    def _do_sabotage(self, target):
        player = self.current_player
        action = self.pending_sabotage
        player.change_energy(-action["cost"])
        good = self._roll(player.stats[action["stat"]])
        if good:
            applied = apply_effect(target, action["target_effect_crit"])
            self.action_result_text = f"✨ Саботаж удался в полной мере! {target.name}: {applied}"
        else:
            roll_partial = random.random() < 0.5
            if roll_partial:
                applied = apply_effect(target, action["target_effect_normal"])
                self.action_result_text = f"Саботаж частично удался. {target.name}: {applied}"
            else:
                applied = apply_effect(player, action["self_fail_effect"])
                self.action_result_text = f"⚠️ Саботаж провалился и раскрыт! Вы: {applied}"
        self._go_action_result()

    def _resolve_no_action(self):
        self.action_result_text = "Игрок решил отдохнуть и не тратить энергию."
        self._go_action_result()

    def _go_action_result(self):
        self.phase = "action_result"
        self.buttons = [Button((WIDTH // 2 - 130, 560, 260, 56), "Далее", self._advance_turn)]

    def _advance_turn(self):
        self.turn_index += 1
        if self.turn_index >= len(self.game.players):
            self.turn_index = 0
            self.day += 1
            if self.day > TOTAL_DAYS:
                from battle import TournamentState
                self.game.set_state(TournamentState(self.game))
                return
        self._build_pass_device()

    # ---------- pygame hooks ----------
    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, surf, font_big, font, font_small):
        surf.fill(BG)
        header = f"День {min(self.day, TOTAL_DAYS)} / {TOTAL_DAYS}"
        surf.blit(font_small.render(header, True, TEXT_DIM), (20, 16))

        if self.phase == "pass_device":
            msg = f"Передайте устройство игроку:"
            r = font.render(msg, True, TEXT_DIM)
            surf.blit(r, r.get_rect(center=(WIDTH // 2, 240)))
            name = font_big.render(self.current_player.name, True, ACCENT)
            surf.blit(name, name.get_rect(center=(WIDTH // 2, 300)))

        elif self.phase == "event":
            ev = self.current_event
            icon = font_big.render(ev["placeholder"], True, TEXT)
            surf.blit(icon, icon.get_rect(center=(WIDTH // 2, 180)))
            title = font.render(ev["desc"], True, TEXT)
            surf.blit(title, title.get_rect(center=(WIDTH // 2, 250)))
            draw_text_block(surf, self.event_result_text, font, (WIDTH // 2 - 300, 320), 600, color=ACCENT)

        elif self.phase == "action":
            name = font.render(f"{self.current_player.name} — выберите действие", True, TEXT)
            surf.blit(name, (60, 170))
            draw_player_panel(surf, self.current_player, 60, 40, 840, font_small, font_small)

        elif self.phase == "target":
            title = font.render(f"{self.pending_sabotage['desc']} — выберите цель", True, TEXT)
            surf.blit(title, title.get_rect(center=(WIDTH // 2, 190)))

        elif self.phase == "action_result":
            draw_text_block(surf, self.action_result_text, font, (WIDTH // 2 - 300, 300), 600, color=ACCENT)

        for b in self.buttons:
            b.draw(surf, font, font_small)


class ResultsState:
    def __init__(self, game, champion=None):
        self.game = game
        self.champion = champion
        self.buttons = [Button((WIDTH // 2 - 130, 560, 260, 56), "Новая игра", self.restart)]

    def restart(self):
        self.game.set_state(MenuState(self.game))

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, surf, font_big, font, font_small):
        surf.fill(BG)
        title = font_big.render("Итоги турнира", True, ACCENT)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 90)))

        if self.champion is not None:
            champ = font.render(f"🏆 Чемпион: {self.champion.name}", True, GOOD)
            surf.blit(champ, champ.get_rect(center=(WIDTH // 2, 150)))

        ranked = sorted(self.game.players, key=lambda p: p.power_score(), reverse=True)
        y = 210
        for i, p in enumerate(ranked, start=1):
            line = f"{i}. {p.name} — суммарная мощь: {p.power_score()} (энергия: {p.energy})"
            r = font_small.render(line, True, TEXT)
            surf.blit(r, (WIDTH // 2 - 260, y))
            y += 30

        for b in self.buttons:
            b.draw(surf, font, font_small)
