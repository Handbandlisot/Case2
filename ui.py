"""Общие UI-утилиты: кнопки, отрисовка текста, панели статов."""
import math
import pygame

WIDTH, HEIGHT = 960, 640

BG = (24, 26, 38)
PANEL = (36, 39, 56)
PANEL_LIGHT = (48, 52, 74)
TEXT = (235, 235, 240)
TEXT_DIM = (160, 163, 180)
ACCENT = (240, 196, 90)
GOOD = (110, 200, 130)
BAD = (210, 90, 90)
BORDER = (70, 74, 100)


class Button:
    def __init__(self, rect, text, callback, subtitle="", enabled=True):
        self.rect = pygame.Rect(rect)
        self.text = text
        self.subtitle = subtitle
        self.callback = callback
        self.enabled = enabled
        self.hovered = False

    def handle_event(self, event):
        if not self.enabled:
            return
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.callback()

    def draw(self, surf, font, font_small):
        color = PANEL_LIGHT if self.enabled else (32, 34, 46)
        if self.hovered and self.enabled:
            color = (60, 64, 92)
        pygame.draw.rect(surf, color, self.rect, border_radius=10)
        border_col = ACCENT if (self.hovered and self.enabled) else BORDER
        pygame.draw.rect(surf, border_col, self.rect, width=2, border_radius=10)

        text_col = TEXT if self.enabled else TEXT_DIM
        label = font.render(self.text, True, text_col)
        label_rect = label.get_rect(center=(self.rect.centerx, self.rect.centery - (8 if self.subtitle else 0)))
        surf.blit(label, label_rect)
        if self.subtitle:
            sub = font_small.render(self.subtitle, True, TEXT_DIM)
            sub_rect = sub.get_rect(center=(self.rect.centerx, self.rect.centery + 14))
            surf.blit(sub, sub_rect)


def wrap_text(text, font, max_width):
    words = text.split(" ")
    lines = []
    current = ""
    for w in words:
        test = (current + " " + w).strip()
        if font.size(test)[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = w
    if current:
        lines.append(current)
    return lines


def draw_text_block(surf, text, font, pos, max_width, color=TEXT, line_gap=6):
    x, y = pos
    for line in wrap_text(text, font, max_width):
        rendered = font.render(line, True, color)
        surf.blit(rendered, (x, y))
        y += rendered.get_height() + line_gap
    return y


def draw_stat_bar(surf, x, y, w, h, ratio, color, bg=PANEL_LIGHT):
    pygame.draw.rect(surf, bg, (x, y, w, h), border_radius=h // 2)
    fill_w = int(w * max(0.0, min(1.0, ratio)))
    if fill_w > 0:
        pygame.draw.rect(surf, color, (x, y, fill_w, h), border_radius=h // 2)


def draw_stick_figure(surf, x, y, facing=1, color=TEXT, pose="idle",
                       lunge=0.0, hit=0.0, shield=False, fallen=False):
    """Рисует простого человечка палка-палка-огуречик в точке (x, y) — координата стоп.
    facing: 1 = смотрит вправо, -1 = смотрит влево.
    lunge: 0..1 — смещение вперёд (выпад атаки).
    hit: 0..1 — интенсивность отдачи/вспышки при попадании.
    shield: рисовать щит перед фигурой.
    fallen: фигура лежит (повержена).
    """
    cx = x + figure_offset(facing, lunge, hit)

    draw_col = color
    if hit > 0:
        draw_col = tuple(int(color[i] * (1 - hit) + BAD[i] * hit) for i in range(3))

    if fallen:
        gy = y - 8
        pygame.draw.circle(surf, draw_col, (int(cx - facing * 32), gy), 12)
        pygame.draw.line(surf, draw_col, (cx - facing * 20, gy), (cx + facing * 34, gy), 5)
        pygame.draw.line(surf, draw_col, (cx + facing * 10, gy), (cx + facing * 22, gy - 14), 4)
        pygame.draw.line(surf, draw_col, (cx + facing * 20, gy), (cx + facing * 32, gy + 10), 4)
        return

    head_r = 14
    hip_y = y - 55
    head_y = y - 100
    body_top = head_y + head_r
    shoulder_y = body_top + 10

    pygame.draw.circle(surf, draw_col, (int(cx), int(head_y)), head_r)
    pygame.draw.line(surf, draw_col, (cx, body_top), (cx, hip_y), 5)
    pygame.draw.line(surf, draw_col, (cx, hip_y), (cx - 14, y), 5)
    pygame.draw.line(surf, draw_col, (cx, hip_y), (cx + 14, y), 5)

    if pose == "attack":
        pygame.draw.line(surf, draw_col, (cx, shoulder_y), (cx + facing * 34, shoulder_y - 6), 5)
        pygame.draw.line(surf, draw_col, (cx + facing * 34, shoulder_y - 6),
                          (cx + facing * 56, shoulder_y - 18), 4)
        pygame.draw.line(surf, draw_col, (cx, shoulder_y), (cx - facing * 10, shoulder_y + 16), 5)
    elif pose == "victory":
        pygame.draw.line(surf, draw_col, (cx, shoulder_y), (cx - 16, shoulder_y - 28), 5)
        pygame.draw.line(surf, draw_col, (cx, shoulder_y), (cx + 16, shoulder_y - 28), 5)
    else:
        pygame.draw.line(surf, draw_col, (cx, shoulder_y), (cx + facing * 14, shoulder_y + 16), 5)
        pygame.draw.line(surf, draw_col, (cx, shoulder_y), (cx - facing * 14, shoulder_y + 16), 5)

    if shield:
        shield_x = cx + facing * 22
        pygame.draw.circle(surf, ACCENT, (int(shield_x), int(shoulder_y + 6)), 17, width=4)


def figure_offset(facing, lunge, hit):
    """Смещение фигуры вдоль направления взгляда — используется и для тела, и для ауры стихии."""
    return facing * lunge * 42 - facing * hit * 16


def draw_school_flourish(surf, cx, head_y, feet_y, school_id, color, phase=0.0):
    """Небольшие декоративные элементы стихии вокруг фигуры: огонь/вода/земля/воздух."""
    if school_id == "fire":
        for i, dx in enumerate((-9, 0, 9)):
            fy = head_y - 20 - 3 * math.sin(phase * 3 + i)
            pygame.draw.polygon(surf, color, [
                (cx + dx, fy - 10), (cx + dx - 6, fy + 8), (cx + dx + 6, fy + 8),
            ])
    elif school_id == "water":
        for i, dx in enumerate((-18, 18)):
            dy = 5 * math.sin(phase * 2 + i * 2)
            pygame.draw.circle(surf, color, (int(cx + dx), int(head_y - 6 + dy)), 4)
    elif school_id == "earth":
        for dx in (-20, -4, 14):
            pygame.draw.rect(surf, color, (cx + dx, feet_y - 6, 9, 7), border_radius=2)
    elif school_id == "air":
        radius = 28
        mid_y = (head_y + feet_y) / 2
        for i in range(3):
            ang = phase * 2 + i * 2.1
            px = cx + math.cos(ang) * radius
            py = mid_y + math.sin(ang) * radius * 0.5
            pygame.draw.circle(surf, color, (int(px), int(py)), 3)


def draw_player_panel(surf, player, x, y, w, font, font_small, highlight=False):
    from player import STAT_NAMES, STAT_ICONS
    h = 150
    pygame.draw.rect(surf, PANEL_LIGHT if highlight else PANEL, (x, y, w, h), border_radius=10)
    pygame.draw.rect(surf, ACCENT if highlight else BORDER, (x, y, w, h), width=2, border_radius=10)
    name = font.render(player.name, True, TEXT)
    surf.blit(name, (x + 12, y + 8))

    energy_label = font_small.render(f"Энергия: {player.energy}/{player.max_energy}", True, TEXT_DIM)
    surf.blit(energy_label, (x + 12, y + 34))
    draw_stat_bar(surf, x + 12, y + 54, w - 24, 10, player.energy / player.max_energy, GOOD)

    yy = y + 72
    for i, s in enumerate(player.stats):
        col = x + 12 + (i % 2) * (w // 2 - 6)
        row_y = yy + (i // 2) * 34
        icon = STAT_ICONS[s]
        txt = font_small.render(f"{icon} {STAT_NAMES[s]}: {player.stats[s]}", True, TEXT)
        surf.blit(txt, (col, row_y))
