"""Финальная мини-игра турнира: бои 1x1 — атака/защита + уникальная способность школы,
обе тратящие боевую энергию. Визуализация — анимированная схватка двух человечков,
стилизованных под стихию (цвет + декоративные элементы).
Полуфинал (2 боя из 4 игроков) -> финал (1 бой) -> чемпион.
"""
import math
import random
import pygame

from ui import (Button, draw_stat_bar, draw_stick_figure, draw_school_flourish, figure_offset,
                 WIDTH, HEIGHT, BG, PANEL, PANEL_LIGHT, TEXT, TEXT_DIM, ACCENT, GOOD, BAD, BORDER)
from game_data import success_chance

GROUND_Y = 430
POS_A = (240, GROUND_Y)
POS_B = (720, GROUND_Y)

BATTLE_ENERGY_REGEN = 20   # восстановление боевой энергии в начале каждого хода бойца

BTN_W, BTN_H, BTN_GAP = 190, 56, 16
BTN_Y = 560


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
        self.a_reflect = 0
        self.b_reflect = 0
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

    # ---------- вспомогательное ----------
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

    def _push_log(self, text):
        self.log.append(text)
        self.log = self.log[-6:]

    def _build_action_buttons(self):
        attacker = self.current()
        specs = [("⚔️ Атака", self.do_attack, "", True)]
        specs.append(("🛡️ Защита", self.do_defend, "", True))
        ability = attacker.school["ability"] if attacker.school else None
        if ability:
            can = attacker.battle_energy >= ability["cost"]
            icon = attacker.school["icon"]
            specs.append((f"{icon} {ability['name']}", self.do_ability, f"-{ability['cost']} эн.", can))

        total_w = len(specs) * BTN_W + (len(specs) - 1) * BTN_GAP
        start_x = WIDTH // 2 - total_w // 2
        btns = []
        for i, (label, cb, sub, enabled) in enumerate(specs):
            x = start_x + i * (BTN_W + BTN_GAP)
            btns.append(Button((x, BTN_Y, BTN_W, BTN_H), label, cb, subtitle=sub, enabled=enabled))
        self.buttons = btns

    def _build_continue_button(self):
        self.buttons = [Button((WIDTH // 2 - 130, BTN_Y, 260, 56), "Продолжить", self._finish)]

    # ---------- действия игрока ----------
    def do_attack(self):
        self._start_attack(power_mult=1.0, energy_cost=0, ignore_block=False, ability_name=None)

    def do_defend(self):
        if self.anim_phase is not None or self.finished:
            return
        attacker = self.current()
        heal_chance = success_chance(attacker.stats["guile"]) // 3
        healed = 6 if random.randint(1, 100) <= heal_chance else 0
        self._start_support(heal=healed, shield=True, reflect=0, energy_cost=0, ability_name=None)

    def do_ability(self):
        if self.anim_phase is not None or self.finished:
            return
        attacker = self.current()
        ability = attacker.school["ability"] if attacker.school else None
        if not ability or attacker.battle_energy < ability["cost"]:
            return
        effect = ability["effect"]
        if effect == "burst_damage":
            self._start_attack(power_mult=ability.get("power_mult", 1.5), energy_cost=ability["cost"],
                                ignore_block=False, ability_name=ability["name"])
        elif effect == "pierce_strike":
            self._start_attack(power_mult=ability.get("power_mult", 1.3), energy_cost=ability["cost"],
                                ignore_block=True, ability_name=ability["name"])
        elif effect == "heal":
            healed = min(ability["heal_amount"], attacker.battle_max_hp - attacker.battle_hp)
            self._start_support(heal=healed, shield=False, reflect=0, energy_cost=ability["cost"],
                                 ability_name=ability["name"])
        elif effect == "fortify":
            self._start_support(heal=0, shield=True, reflect=ability.get("reflect", 0), energy_cost=ability["cost"],
                                 ability_name=ability["name"])

    def _start_attack(self, power_mult, energy_cost, ignore_block, ability_name):
        if self.anim_phase is not None or self.finished:
            return
        attacker, defender = self.current(), self.opponent()
        if energy_cost:
            attacker.battle_energy -= energy_cost

        chance = success_chance(attacker.stats["luck"])
        crit = random.randint(1, 100) <= chance
        dmg = int((8 + attacker.stats["athletics"] // 2 + random.randint(0, 6)) * power_mult)
        if crit:
            dmg = int(dmg * 1.6)

        defending = self.b_defending if defender is self.b else self.a_defending
        blocked = defending and not ignore_block
        if blocked:
            dmg = dmg // 2
        reflect_amt = (self.b_reflect if defender is self.b else self.a_reflect) if defending else 0

        self._pending = {"attacker": attacker, "defender": defender, "dmg": dmg, "crit": crit,
                          "blocked": blocked, "reflect": reflect_amt, "ability_name": ability_name}
        self.buttons = []
        self.anim_phase = "lunge_out"
        self.anim_timer = 0.0

    def _start_support(self, heal, shield, reflect, energy_cost, ability_name):
        if self.anim_phase is not None or self.finished:
            return
        attacker = self.current()
        if energy_cost:
            attacker.battle_energy -= energy_cost
        if heal > 0:
            attacker.battle_hp = min(attacker.battle_max_hp, attacker.battle_hp + heal)
            self._add_popup(attacker, f"+{heal}", GOOD)
        if shield:
            if attacker is self.a:
                self.a_defending = True
                self.a_reflect = reflect
            else:
                self.b_defending = True
                self.b_reflect = reflect
            self._vis(attacker)["shield"] = True

        heal_txt = f", +{heal} HP" if heal > 0 else ""
        verb = f"использует «{ability_name}»" if ability_name else "занимает защитную стойку"
        self._push_log(f"{attacker.name} {verb}{heal_txt}")

        self.buttons = []
        self.anim_phase = "defend_pose"
        self.anim_timer = 0.0

    # ---------- разрешение анимации ----------
    def _apply_impact(self):
        p = self._pending
        attacker, defender = p["attacker"], p["defender"]
        dmg, crit, blocked, reflect_amt, ability_name = p["dmg"], p["crit"], p["blocked"], p["reflect"], p["ability_name"]

        defender.battle_hp = max(0, defender.battle_hp - dmg)
        self._vis(defender)["hit"] = 1.0
        self._add_popup(defender, f"-{dmg}", ACCENT if crit else BAD)

        if defender is self.b:
            self.b_defending = False
            used_reflect = self.b_reflect
            self.b_reflect = 0
        else:
            self.a_defending = False
            used_reflect = self.a_reflect
            self.a_reflect = 0
        self._vis(defender)["shield"] = False

        crit_txt = " — КРИТИЧЕСКИЙ УДАР!" if crit else ""
        block_txt = " (частично заблокировано)" if blocked else ""
        verb = f"использует «{ability_name}» против" if ability_name else "атакует"
        self._push_log(f"{attacker.name} {verb} {defender.name}: {dmg} урона{crit_txt}{block_txt}")

        reflect_applied = used_reflect if blocked else 0
        if reflect_applied:
            attacker.battle_hp = max(0, attacker.battle_hp - reflect_applied)
            self._add_popup(attacker, f"-{reflect_applied}", BAD)
            self._push_log(f"Каменная броня {defender.name} отражает {reflect_applied} урона!")

        if defender.battle_hp <= 0:
            self.finished = True
            self.winner = attacker
            self._vis(defender)["fallen"] = True
            self._push_log(f"🏆 {self.winner.name} побеждает в поединке!")
        elif attacker.battle_hp <= 0:
            self.finished = True
            self.winner = defender
            self._vis(attacker)["fallen"] = True
            self._push_log(f"🏆 {self.winner.name} побеждает — соперник погиб от отдачи!")

    def _end_turn_switch(self):
        self.attacker_idx = 1 - self.attacker_idx
        new_attacker = self.current()
        new_attacker.battle_energy = min(new_attacker.battle_max_energy,
                                          new_attacker.battle_energy + BATTLE_ENERGY_REGEN)
        self._build_action_buttons()

    def _finish(self):
        self.on_finish(self.winner)

    # ---------- игровой цикл ----------
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
                self.anim_phase = "victory" if self.finished else "lunge_back"
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

    # ---------- отрисовка ----------
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

            color = player.school["color"] if player.school else TEXT
            fy = pos[1] + bob
            draw_stick_figure(surf, pos[0], fy, facing=facing, color=color, pose=pose,
                               lunge=vis["lunge"], hit=vis["hit"], shield=vis["shield"], fallen=vis["fallen"])

            if player.school and not vis["fallen"]:
                cx = pos[0] + figure_offset(facing, vis["lunge"], vis["hit"])
                head_y = fy - 100
                draw_school_flourish(surf, cx, head_y, fy, player.school["id"], color, self.bob_phase)

        if not self.finished and self.anim_phase is None:
            turn_txt = font_small.render(f"Ход: {self.current().name}", True, TEXT)
            surf.blit(turn_txt, turn_txt.get_rect(center=(WIDTH // 2, 270)))

        for pop in self.popups:
            alpha_t = max(0.0, 1.0 - pop["t"] / 0.9)
            col = tuple(int(c * alpha_t + BG[i] * (1 - alpha_t)) for i, c in enumerate(pop["color"]))
            r = font.render(pop["text"], True, col)
            surf.blit(r, r.get_rect(center=(pop["x"], pop["y"])))

        y = 300
        for line in self.log:
            r = font_small.render(line, True, TEXT_DIM)
            surf.blit(r, r.get_rect(center=(WIDTH // 2, y)))
            y += 22

        for btn in self.buttons:
            btn.draw(surf, font, font_small)

    def _draw_fighter_info(self, surf, fighter, pos, font, font_small):
        x, y = pos
        w = 220
        box_x = x - w // 2
        box_y = y - 210
        icon = f"{fighter.school['icon']} " if fighter.school else ""
        name = font_small.render(f"{icon}{fighter.name}", True, TEXT)
        surf.blit(name, name.get_rect(center=(x, box_y)))

        hp_txt = font_small.render(f"{fighter.battle_hp}/{fighter.battle_max_hp} HP", True, TEXT_DIM)
        surf.blit(hp_txt, hp_txt.get_rect(center=(x, box_y + 18)))
        ratio = fighter.battle_hp / fighter.battle_max_hp if fighter.battle_max_hp else 0
        color = GOOD if ratio > 0.4 else BAD
        draw_stat_bar(surf, box_x, box_y + 32, w, 11, ratio, color)

        en_ratio = fighter.battle_energy / fighter.battle_max_energy if fighter.battle_max_energy else 0
        draw_stat_bar(surf, box_x, box_y + 47, w, 8, en_ratio, (90, 140, 220))
        en_txt = font_small.render(f"⚡ {fighter.battle_energy}/{fighter.battle_max_energy}", True, TEXT_DIM)
        surf.blit(en_txt, en_txt.get_rect(center=(x, box_y + 62)))


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
