"""Финальная мини-игра турнира: бои 1x1 в формате атака/защита,
визуализированные как анимированная схватка двух человечков.
Логика урона/шансов не отличается от предыдущей версии — изменена только визуализация.
Полуфинал (2 боя из 4 игроков) -> финал (1 бой) -> чемпион.
"""
import math
import random
import pygame

from ui import (Button, draw_stat_bar, draw_stick_figure, WIDTH, HEIGHT,
                 BG, PANEL, PANEL_LIGHT, TEXT, TEXT_DIM, ACCENT, GOOD, BAD, BORDER)
from game_data import success_chance

GROUND_Y = 430
POS_A = (240, GROUND_Y)
POS_B = (720, GROUND_Y)


def ease_out(t):
    return 1 - (1 - t) ** 2


class BattleState:
    def __init__(self, game, player_a, player_b, title, on_finish):
        self.game = game
        player_a.init_battle_stats()
        player_b.init_battle_stats()
        self.a = player_a
        self.b = player_b
        self.title = title
        self.on_finish = on_finish

        luck_a, luck_b = player_a.stats["luck"], player_b.stats["luck"]
        self.attacker_idx = 0 if random.uniform(0, luck_a + luck_b + 1) < luck_a + 0.5 else 1

        self.a_defending = False
        self.b_defending = False
        self.log = [f"⚔️ {title}: {player_a.name} против {player_b.name}!"]
        self.finished = False
        self.winner = None

        self.vis_a = {"lunge": 0.0, "hit": 0.0, "shield": False, "fallen": False}
        self.vis_b = {"lunge": 0.0, "hit": 0.0, "shield": False, "fallen": False}
        self.bob_phase = 0.0
        self.popups = []

        self.anim_phase = None
        self.anim_timer = 0.0
        self._pending = None

        self.buttons = []
        self._build_action_buttons()

    def fighters(self):
        return [self.a, self.b]

    def current(self):
        return self.fighters()[self.attacker_idx]

    def opponent(self):
        return self.fighters()[1 - self.attacker_idx]

    def _vis(self, player):
        return self.vis_a if player is self.a else self.vis_b

    def _pos(self, player):
        return POS_A if player is self.a else POS_B

    def _add_popup(self, player, text, color):
        px, py = self._pos(player)
        self.popups.append({"text": text, "x": px, "y": py - 110, "t": 0.0, "color": color})

    def _build_action_buttons(self):
        self.buttons = [
            Button((WIDTH // 2 - 220, 560, 200, 56), "⚔️ Атаковать", self.do_attack),
            Button((WIDTH // 2 + 20, 560, 200, 56), "🛡️ Защититься", self.do_defend),
        ]

    def _build_continue_button(self):
        self.buttons = [Button((WIDTH // 2 - 130, 560, 260, 56), "Продолжить", self._finish)]

    def do_attack(self):
        if self.anim_phase is not None or self.finished:
            return
        attacker, defender = self.current(), self.opponent()
        chance = success_chance(attacker.stats["luck"])
        crit = random.randint(1, 100) <= chance
        dmg = 8 + attacker.stats["athletics"] // 2 + random.randint(0, 6)
        if crit:
            dmg = int(dmg * 1.6)
        defending = self.b_defending if defender is self.b else self.a_defending
        if defending:
            dmg = dmg // 2

        self._pending = {"attacker": attacker, "defender": defender, "dmg": dmg,
                          "crit": crit, "blocked": defending}
        self.buttons = []
        self.anim_phase = "lunge_out"
        self.anim_timer = 0.0

    def do_defend(self):
        if self.anim_phase is not None or self.finished:
            return
        attacker = self.current()
        if attacker is self.a:
            self.a_defending = True
        else:
            self.b_defending = True

        heal_chance = success_chance(attacker.stats["guile"]) // 3
        healed = 0
        if random.randint(1, 100) <= heal_chance:
            healed = 6
            attacker.battle_hp = min(attacker.battle_max_hp, attacker.battle_hp + healed)
            self._add_popup(attacker, f"+{healed}", GOOD)

        heal_txt = f", восстановлено {healed} HP" if healed else ""
        self._push_log(f"{attacker.name} занимает защитную стойку{heal_txt}")
        self._vis(attacker)["shield"] = True

        self.buttons = []
        self.anim_phase = "defend_pose"
        self.anim_timer = 0.0

    def _push_log(self, text):
        self.log.append(text)
        self.log = self.log[-6:]

    def _apply_impact(self):
        p = self._pending
        attacker, defender, dmg, crit, blocked = p["attacker"], p["defender"], p["dmg"], p["crit"], p["blocked"]

        defender.battle_hp = max(0, defender.battle_hp - dmg)
        self._vis(defender)["hit"] = 1.0
        self._add_popup(defender, f"-{dmg}", BAD if not crit else ACCENT)

        if defender is self.b:
            self.b_defending = False
        else:
            self.a_defending = False
        self._vis(defender)["shield"] = False

        crit_txt = " — КРИТИЧЕСКИЙ УДАР!" if crit else ""
        block_txt = " (частично заблокировано)" if blocked else ""
        self._push_log(f"{attacker.name} атакует {defender.name}: {dmg} урона{crit_txt}{block_txt}")

        if defender.battle_hp <= 0:
            self.finished = True
            self.winner = attacker
            self._vis(defender)["fallen"] = True
            self._push_log(f"🏆 {self.winner.name} побеждает в поединке!")

    def _end_turn_switch(self):
        self.attacker_idx = 1 - self.attacker_idx
        self._build_action_buttons()

    def handle_event(self, event):
        for btn in self.buttons:
            btn.handle_event(event)

    def update(self, dt):
        self.bob_phase += dt * 2.2
        for pop in self.popups:
            pop["y"] -= 42 * dt
            pop["t"] += dt
        self.popups = [p for p in self.popups if p["t"] < 0.9]

        if self.anim_phase == "lunge_out":
            self.anim_timer += dt
            t = min(1.0, self.anim_timer / 0.22)
            self._vis(self._pending["attacker"])["lunge"] = ease_out(t)
            if t >= 1.0:
                self._apply_impact()
                self.anim_phase = "impact"
                self.anim_timer = 0.0

        elif self.anim_phase == "impact":
            self.anim_timer += dt
            defender = self._pending["defender"]
            self._vis(defender)["hit"] = max(0.0, 1.0 - self.anim_timer / 0.3)
            if self.anim_timer >= 0.3:
                if self.finished:
                    self.anim_phase = "victory"
                    self.anim_timer = 0.0
                else:
                    self.anim_phase = "lunge_back"
                    self.anim_timer = 0.0

        elif self.anim_phase == "lunge_back":
            self.anim_timer += dt
            t = min(1.0, self.anim_timer / 0.18)
            self._vis(self._pending["attacker"])["lunge"] = ease_out(1.0 - t)
            if t >= 1.0:
                self.anim_phase = None
                self._end_turn_switch()

        elif self.anim_phase == "defend_pose":
            self.anim_timer += dt
            if self.anim_timer >= 0.35:
                self.anim_phase = None
                self._end_turn_switch()

        elif self.anim_phase == "victory":
            self.anim_timer += dt
            self._vis(self.winner)["lunge"] = 0.0
            if self.anim_timer >= 0.5:
                self.anim_phase = None
                self._build_continue_button()

    def _finish(self):
        self.on_finish(self.winner)

    def draw(self, surf, font_big, font, font_small):
        surf.fill(BG)
        title = font.render(self.title, True, ACCENT)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 34)))

        pygame.draw.line(surf, BORDER, (60, GROUND_Y + 4), (WIDTH - 60, GROUND_Y + 4), 3)

        for player, pos, facing in ((self.a, POS_A, 1), (self.b, POS_B, -1)):
            self._draw_fighter_info(surf, player, pos, font, font_small)
            vis = self._vis(player)
            bob = math.sin(self.bob_phase + (0 if player is self.a else 1.6)) * 3
            is_winner_pose = self.finished and player is self.winner and self.anim_phase == "victory"
            pose = "attack" if vis["lunge"] > 0.05 else ("victory" if is_winner_pose else "idle")
            draw_stick_figure(
                surf, pos[0], pos[1] + bob, facing=facing, color=TEXT, pose=pose,
                lunge=vis["lunge"], hit=vis["hit"], shield=vis["shield"], fallen=vis["fallen"],
            )

        if not self.finished and self.anim_phase is None:
            turn_txt = font_small.render(f"Ход: {self.current().name}", True, TEXT)
            surf.blit(turn_txt, turn_txt.get_rect(center=(WIDTH // 2, 270)))

        for pop in self.popups:
            alpha_t = max(0.0, 1.0 - pop["t"] / 0.9)
            col = tuple(int(c * alpha_t + BG[i] * (1 - alpha_t)) for i, c in enumerate(pop["color"]))
            r = font.render(pop["text"], True, col)
            surf.blit(r, r.get_rect(center=(pop["x"], pop["y"])))

        y = 320
        for line in self.log:
            r = font_small.render(line, True, TEXT_DIM)
            surf.blit(r, r.get_rect(center=(WIDTH // 2, y)))
            y += 24

        for btn in self.buttons:
            btn.draw(surf, font, font_small)

    def _draw_fighter_info(self, surf, fighter, pos, font, font_small):
        x, y = pos
        w = 220
        box_x = x - w // 2
        box_y = y - 200
        name = font_small.render(fighter.name, True, TEXT)
        surf.blit(name, name.get_rect(center=(x, box_y)))
        hp_txt = font_small.render(f"{fighter.battle_hp}/{fighter.battle_max_hp} HP", True, TEXT_DIM)
        surf.blit(hp_txt, hp_txt.get_rect(center=(x, box_y + 18)))
        ratio = fighter.battle_hp / fighter.battle_max_hp if fighter.battle_max_hp else 0
        color = GOOD if ratio > 0.4 else BAD
        draw_stat_bar(surf, box_x, box_y + 32, w, 12, ratio, color)


class TournamentState:
    """Организует полуфиналы и финал турнира."""

    def __init__(self, game):
        self.game = game
        players = list(game.players)
        random.shuffle(players)
        self.pair1 = (players[0], players[1])
        self.pair2 = (players[2], players[3])
        self.semi_winners = []
        self.stage = "intro"
        self.buttons = [Button((WIDTH // 2 - 150, 500, 300, 56), "Начать полуфинал 1", self._start_semi1)]

    def _start_semi1(self):
        self.stage = "semi1"
        self.game.set_state(BattleState(self.game, self.pair1[0], self.pair1[1],
                                         "Полуфинал 1", self._after_semi1))

    def _after_semi1(self, winner):
        self.semi_winners.append(winner)
        self.stage = "semi1_done"
        self.buttons = [Button((WIDTH // 2 - 150, 500, 300, 56), "Начать полуфинал 2", self._start_semi2)]
        self.game.set_state(self)

    def _start_semi2(self):
        self.stage = "semi2"
        self.game.set_state(BattleState(self.game, self.pair2[0], self.pair2[1],
                                         "Полуфинал 2", self._after_semi2))

    def _after_semi2(self, winner):
        self.semi_winners.append(winner)
        self.stage = "final_intro"
        self.buttons = [Button((WIDTH // 2 - 150, 500, 300, 56), "Начать финал", self._start_final)]
        self.game.set_state(self)

    def _start_final(self):
        self.stage = "final"
        f1, f2 = self.semi_winners
        self.game.set_state(BattleState(self.game, f1, f2, "ФИНАЛ", self._after_final))

    def _after_final(self, champion):
        from states import ResultsState
        self.game.set_state(ResultsState(self.game, champion=champion))

    def handle_event(self, event):
        for b in self.buttons:
            b.handle_event(event)

    def update(self, dt):
        pass

    def draw(self, surf, font_big, font, font_small):
        surf.fill(BG)
        title = font_big.render("Турнир начинается!", True, ACCENT)
        surf.blit(title, title.get_rect(center=(WIDTH // 2, 100)))

        if self.stage == "intro":
            lines = [f"Полуфинал 1: {self.pair1[0].name} vs {self.pair1[1].name}",
                     f"Полуфинал 2: {self.pair2[0].name} vs {self.pair2[1].name}"]
        elif self.stage == "semi1_done":
            lines = [f"Победитель полуфинала 1: {self.semi_winners[0].name}",
                     f"Далее: {self.pair2[0].name} vs {self.pair2[1].name}"]
        elif self.stage == "final_intro":
            lines = [f"Финалисты: {self.semi_winners[0].name} vs {self.semi_winners[1].name}"]
        else:
            lines = []

        y = 220
        for line in lines:
            r = font.render(line, True, TEXT)
            surf.blit(r, r.get_rect(center=(WIDTH // 2, y)))
            y += 40

        for b in self.buttons:
            b.draw(surf, font, font_small)
