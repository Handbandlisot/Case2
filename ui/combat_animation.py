"""Animated combat arena, adapted from the stick-figure example in ``пв.txt``.

This module is presentation-only. It draws stick-figure fighters and schedules
an action's existing game-rule callback at the impact point of a short,
non-blocking animation timeline.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable

import pygame

from config import (
    COLOR_ACCENT,
    COLOR_BACKGROUND,
    COLOR_DAMAGE_NUMBER,
    COLOR_HEAL_NUMBER,
    COLOR_NEGATIVE,
    COLOR_PANEL_BG,
    COLOR_PANEL_BORDER,
    COLOR_TEXT_MUTED,
    COMBAT_ANIM_BASE_DURATION,
    COMBAT_ANIM_BLOCK_DURATION,
    COMBAT_ANIM_BLOCK_IMPACT_TIME,
    COMBAT_ANIM_CAST_DURATION,
    COMBAT_ANIM_CAST_IMPACT_TIME,
    COMBAT_ANIM_HIT_FLASH_DURATION,
    COMBAT_ANIM_IMPACT_TIME,
    COMBAT_ANIM_KO_DURATION,
    COMBAT_ANIM_KO_FALL_DELAY,
    COMBAT_ANIM_POPUP_DURATION,
    COMBAT_ANIM_RETURN_TIME,
    COMBAT_ANIM_WINDUP_TIME,
    COMBAT_ARENA_FIGURE_OFFSET,
    PANEL_RADIUS,
    SCHOOL_COLORS,
)
from models.player import Player, School

ResolveCallback = Callable[[], None]
Point = tuple[int, int]


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _ease_out(value: float) -> float:
    value = _clamp01(value)
    return 1.0 - (1.0 - value) ** 3


def _blend(a: tuple[int, int, int], b: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
    amount = _clamp01(amount)
    return tuple(round(a[i] * (1.0 - amount) + b[i] * amount) for i in range(3))


def _point(x: float, y: float) -> Point:
    return round(x), round(y)


@dataclass
class CombatAnimation:
    """A small action timeline which resolves game logic exactly once at impact."""

    active: bool = False
    kind: str = ""
    title: str = ""
    attacker: Player | None = None
    defender: Player | None = None
    elapsed: float = 0.0
    impact_at: float = 0.0
    duration: float = 0.0
    resolved: bool = False
    damage_to_attacker: int = 0
    damage_to_defender: int = 0
    healing_to_attacker: int = 0
    _attacker_health_before: int = 0
    _defender_health_before: int = 0
    _attacker_shield_before: bool = False
    _defender_shield_before: bool = False
    _resolver: ResolveCallback | None = field(default=None, repr=False)

    def start(
        self,
        kind: str,
        attacker: Player,
        defender: Player,
        title: str,
        resolver: ResolveCallback,
    ) -> None:
        """Begin an animation; ``resolver`` is called at the animated impact."""
        if self.active:
            return
        if kind not in {"attack", "block", "ability"}:
            raise ValueError(f"Unknown combat animation: {kind}")

        self.active = True
        self.kind = kind
        self.title = title
        self.attacker = attacker
        self.defender = defender
        self.elapsed = 0.0
        self.resolved = False
        self.damage_to_attacker = 0
        self.damage_to_defender = 0
        self.healing_to_attacker = 0
        self._attacker_health_before = attacker.health
        self._defender_health_before = defender.health
        self._attacker_shield_before = attacker.block_active or attacker.armor_active
        self._defender_shield_before = defender.block_active or defender.armor_active
        self._resolver = resolver

        if kind == "block":
            self.impact_at = COMBAT_ANIM_BLOCK_IMPACT_TIME
            self.duration = COMBAT_ANIM_BLOCK_DURATION
        elif kind == "ability" and attacker.school in (School.WATER, School.EARTH):
            self.impact_at = COMBAT_ANIM_CAST_IMPACT_TIME
            self.duration = COMBAT_ANIM_CAST_DURATION
        else:
            self.impact_at = COMBAT_ANIM_IMPACT_TIME
            self.duration = COMBAT_ANIM_BASE_DURATION

    def update(self, dt: float) -> None:
        """Advance the timeline and apply the combat action at its impact."""
        if not self.active:
            return
        self.elapsed += max(0.0, dt)

        if not self.resolved and self.elapsed >= self.impact_at:
            self._resolve_at_impact()

        if self.resolved and self.elapsed >= self.duration:
            self.active = False
            self._resolver = None

    def _resolve_at_impact(self) -> None:
        attacker, defender = self.attacker, self.defender
        if attacker is None or defender is None:
            self.active = False
            return

        if self._resolver is not None:
            self._resolver()

        self.damage_to_attacker = max(0, self._attacker_health_before - attacker.health)
        self.damage_to_defender = max(0, self._defender_health_before - defender.health)
        self.healing_to_attacker = max(0, attacker.health - self._attacker_health_before)
        self.resolved = True

        if not attacker.is_alive or not defender.is_alive:
            self.duration = max(self.duration, COMBAT_ANIM_KO_DURATION)

    @property
    def is_offensive(self) -> bool:
        if self.kind == "attack":
            return True
        return (
            self.kind == "ability"
            and self.attacker is not None
            and self.attacker.school in (School.FIRE, School.AIR)
        )

    def lunge_for(self, player: Player) -> float:
        """Return a 0..1 forward-lunge amount, mirroring the reference helper."""
        if not self.active or player is not self.attacker or not self.is_offensive:
            return 0.0
        if self.elapsed <= COMBAT_ANIM_WINDUP_TIME:
            return 0.0
        if self.elapsed <= self.impact_at:
            span = max(0.001, self.impact_at - COMBAT_ANIM_WINDUP_TIME)
            return _ease_out((self.elapsed - COMBAT_ANIM_WINDUP_TIME) / span)
        return 1.0 - _ease_out((self.elapsed - self.impact_at) / COMBAT_ANIM_RETURN_TIME)

    def pose_for(self, player: Player) -> str:
        if not self.active or player is not self.attacker:
            return "idle"
        if self.is_offensive:
            return "attack" if self.elapsed < self.impact_at + 0.16 else "idle"
        return "cast" if self.elapsed < self.impact_at + 0.26 else "idle"

    def hit_intensity_for(self, player: Player) -> float:
        if not self.active or not self.resolved or not self.is_offensive:
            return 0.0
        if player is self.defender or (player is self.attacker and self.damage_to_attacker > 0):
            age = max(0.0, self.elapsed - self.impact_at)
            return _clamp01(1.0 - age / COMBAT_ANIM_HIT_FLASH_DURATION)
        return 0.0

    def shield_flash_for(self, player: Player) -> bool:
        """Briefly retain a just-consumed shield ring for its impact frame."""
        if not self.active or not self.resolved or not self.is_offensive:
            return False
        if player is not self.defender or not self._defender_shield_before:
            return False
        if player.block_active or player.armor_active:
            return False
        return self.elapsed - self.impact_at <= COMBAT_ANIM_HIT_FLASH_DURATION * 0.7

    def fallen_for(self, player: Player) -> bool:
        if player.is_alive:
            return False
        if not self.active:
            return True
        return self.resolved and self.elapsed >= self.impact_at + COMBAT_ANIM_KO_FALL_DELAY

    def popup_for(self, player: Player) -> tuple[int, bool] | None:
        """Return (magnitude, is_healing) for a floating HP number."""
        if not self.active or not self.resolved or self.elapsed < self.impact_at:
            return None
        if player is self.defender and self.damage_to_defender:
            return self.damage_to_defender, False
        if player is self.attacker:
            if self.damage_to_attacker:
                return self.damage_to_attacker, False
            if self.healing_to_attacker:
                return self.healing_to_attacker, True
        return None

    def popup_age(self) -> float:
        return max(0.0, self.elapsed - self.impact_at)

    def projectile_progress(self) -> float | None:
        if not self.active or self.kind != "ability" or not self.is_offensive:
            return None
        if self.elapsed < COMBAT_ANIM_WINDUP_TIME or self.elapsed > self.impact_at:
            return None
        span = max(0.001, self.impact_at - COMBAT_ANIM_WINDUP_TIME)
        return _ease_out((self.elapsed - COMBAT_ANIM_WINDUP_TIME) / span)


def figure_offset(facing: int, lunge: float, hit: float) -> float:
    """Shared stick-figure offset: forward motion plus a small hit recoil."""
    return facing * lunge * 42 - facing * hit * 16


def draw_stick_figure(
    surface: pygame.Surface,
    x: float,
    y: int,
    facing: int = 1,
    color: tuple[int, int, int] = (235, 238, 245),
    pose: str = "idle",
    lunge: float = 0.0,
    hit: float = 0.0,
    shield: bool = False,
    fallen: bool = False,
) -> None:
    """Draw a simple fighter; ``(x, y)`` is the feet point."""
    cx = x + figure_offset(facing, lunge, hit)
    draw_color = _blend(color, COLOR_NEGATIVE, hit)

    if fallen:
        gy = y - 8
        pygame.draw.circle(surface, draw_color, _point(cx - facing * 32, gy), 12)
        pygame.draw.line(surface, draw_color, _point(cx - facing * 20, gy), _point(cx + facing * 34, gy), 5)
        pygame.draw.line(surface, draw_color, _point(cx + facing * 10, gy), _point(cx + facing * 22, gy - 14), 4)
        pygame.draw.line(surface, draw_color, _point(cx + facing * 20, gy), _point(cx + facing * 32, gy + 10), 4)
        return

    head_radius = 14
    hip_y = y - 55
    head_y = y - 100
    body_top = head_y + head_radius
    shoulder_y = body_top + 10

    pygame.draw.circle(surface, draw_color, _point(cx, head_y), head_radius)
    pygame.draw.line(surface, draw_color, _point(cx, body_top), _point(cx, hip_y), 5)
    pygame.draw.line(surface, draw_color, _point(cx, hip_y), _point(cx - 14, y), 5)
    pygame.draw.line(surface, draw_color, _point(cx, hip_y), _point(cx + 14, y), 5)

    if pose == "attack":
        pygame.draw.line(surface, draw_color, _point(cx, shoulder_y), _point(cx + facing * 34, shoulder_y - 6), 5)
        pygame.draw.line(surface, draw_color, _point(cx + facing * 34, shoulder_y - 6), _point(cx + facing * 56, shoulder_y - 18), 4)
        pygame.draw.line(surface, draw_color, _point(cx, shoulder_y), _point(cx - facing * 10, shoulder_y + 16), 5)
    elif pose == "victory":
        pygame.draw.line(surface, draw_color, _point(cx, shoulder_y), _point(cx - 16, shoulder_y - 28), 5)
        pygame.draw.line(surface, draw_color, _point(cx, shoulder_y), _point(cx + 16, shoulder_y - 28), 5)
    elif pose == "cast":
        pygame.draw.line(surface, draw_color, _point(cx, shoulder_y), _point(cx + facing * 24, shoulder_y - 16), 5)
        pygame.draw.line(surface, draw_color, _point(cx + facing * 24, shoulder_y - 16), _point(cx + facing * 34, shoulder_y - 24), 4)
        pygame.draw.line(surface, draw_color, _point(cx, shoulder_y), _point(cx - facing * 12, shoulder_y - 12), 5)
    else:
        pygame.draw.line(surface, draw_color, _point(cx, shoulder_y), _point(cx + facing * 14, shoulder_y + 16), 5)
        pygame.draw.line(surface, draw_color, _point(cx, shoulder_y), _point(cx - facing * 14, shoulder_y + 16), 5)

    if shield:
        shield_x = cx + facing * 22
        pygame.draw.circle(surface, COLOR_ACCENT, _point(shield_x, shoulder_y + 6), 17, width=3)


def draw_school_flourish(
    surface: pygame.Surface,
    cx: float,
    head_y: float,
    feet_y: float,
    school_id: str,
    color: tuple[int, int, int],
    phase: float = 0.0,
) -> None:
    """Subtle animated fire, water, earth or air marks around the fighter."""
    if school_id == "fire":
        for index, dx in enumerate((-9, 0, 9)):
            fy = head_y - 20 - 3 * math.sin(phase * 3 + index)
            points = [
                _point(cx + dx, fy - 10),
                _point(cx + dx - 6, fy + 8),
                _point(cx + dx + 6, fy + 8),
            ]
            pygame.draw.polygon(surface, color, points)
    elif school_id == "water":
        for index, dx in enumerate((-18, 18)):
            dy = 5 * math.sin(phase * 2 + index * 2)
            pygame.draw.circle(surface, color, _point(cx + dx, head_y - 6 + dy), 4)
    elif school_id == "earth":
        for dx in (-20, -4, 14):
            stone = pygame.Rect(round(cx + dx), round(feet_y - 6), 9, 7)
            pygame.draw.rect(surface, color, stone, border_radius=2)
    elif school_id == "air":
        radius = 28
        mid_y = (head_y + feet_y) / 2
        for index in range(3):
            angle = phase * 2 + index * 2.1
            px = cx + math.cos(angle) * radius
            py = mid_y + math.sin(angle) * radius * 0.5
            pygame.draw.circle(surface, color, _point(px, py), 3)


def _draw_projectile(
    surface: pygame.Surface,
    attacker: Player,
    start_x: float,
    target_x: float,
    y: int,
    progress: float,
    facing: int,
) -> None:
    x = start_x + (target_x - start_x) * progress
    arc_y = y - math.sin(progress * math.pi) * 16
    center = _point(x, arc_y)

    if attacker.school is School.FIRE:
        pygame.draw.circle(surface, (255, 123, 56), center, 15)
        pygame.draw.circle(surface, (255, 207, 111), center, 9)
        pygame.draw.circle(surface, (255, 245, 198), center, 4)
        tail = _point(x - facing * 19, arc_y + 4)
        pygame.draw.line(surface, (224, 92, 45), tail, center, 4)
    elif attacker.school is School.AIR:
        for index in range(3):
            trail_x = x - facing * (14 + index * 10)
            trail_y = arc_y + (index - 1) * 7
            pygame.draw.line(
                surface,
                _blend(SCHOOL_COLORS["air"], COLOR_BACKGROUND, index * 0.18),
                _point(trail_x, trail_y),
                _point(trail_x + facing * 22, trail_y - 2),
                3,
            )
        pygame.draw.circle(surface, SCHOOL_COLORS["air"], center, 6, width=2)


def _draw_hit_spark(
    surface: pygame.Surface,
    center: Point,
    intensity: float,
    color: tuple[int, int, int],
) -> None:
    if intensity <= 0.0:
        return
    x, y = center
    radius = 9 + round(17 * (1.0 - intensity))
    spark_color = _blend(color, COLOR_BACKGROUND, 0.35 * (1.0 - intensity))
    pygame.draw.circle(surface, spark_color, center, radius, width=2)
    for index in range(8):
        angle = index * math.tau / 8
        inner = radius * 0.35
        outer = radius + (7 if index % 2 == 0 else 2)
        p1 = _point(x + math.cos(angle) * inner, y + math.sin(angle) * inner)
        p2 = _point(x + math.cos(angle) * outer, y + math.sin(angle) * outer)
        pygame.draw.line(surface, spark_color, p1, p2, 2)
    pygame.draw.circle(surface, (255, 245, 215), center, max(2, round(5 * intensity)))


def _draw_heal_orbit(
    surface: pygame.Surface,
    cx: float,
    feet_y: int,
    elapsed: float,
    color: tuple[int, int, int],
) -> None:
    for index in range(5):
        angle = elapsed * 4.0 + index * math.tau / 5
        radius = 24 + 5 * math.sin(elapsed * 5 + index)
        px = cx + math.cos(angle) * radius
        py = feet_y - 55 + math.sin(angle) * 23
        pygame.draw.circle(surface, color, _point(px, py), 4 + index % 2)


def _draw_earth_guard(
    surface: pygame.Surface,
    cx: float,
    feet_y: int,
    elapsed: float,
    color: tuple[int, int, int],
) -> None:
    pulse = 1.0 + 0.08 * math.sin(elapsed * 6.0)
    radius_x = round(34 * pulse)
    rect = pygame.Rect(round(cx - radius_x), feet_y - 88, radius_x * 2, 78)
    pygame.draw.arc(surface, color, rect, math.pi * 0.08, math.pi * 0.92, 3)
    for index, dx in enumerate((-27, 0, 27)):
        bob = round(3 * math.sin(elapsed * 4 + index))
        y = feet_y - (22 + (index % 2) * 8) + bob
        points = [
            _point(cx + dx, y - 8),
            _point(cx + dx + 7, y),
            _point(cx + dx, y + 7),
            _point(cx + dx - 7, y),
        ]
        pygame.draw.polygon(surface, color, points)


def _draw_floating_number(
    surface: pygame.Surface,
    font: pygame.font.Font,
    text: str,
    center: Point,
    color: tuple[int, int, int],
    age: float,
) -> None:
    progress = _clamp01(age / COMBAT_ANIM_POPUP_DURATION)
    alpha = round(255 * (1.0 - progress))
    rect = font.render(text, True, color).get_rect(
        center=(center[0], center[1] - round(28 * _ease_out(progress)))
    )
    shadow = font.render(text, True, COLOR_BACKGROUND)
    shadow.set_alpha(alpha)
    surface.blit(shadow, rect.move(2, 2))
    rendered = font.render(text, True, color)
    rendered.set_alpha(alpha)
    surface.blit(rendered, rect)


def draw_combat_arena(
    surface: pygame.Surface,
    rect: pygame.Rect,
    left: Player,
    right: Player,
    animation: CombatAnimation,
    fonts: dict[str, pygame.font.Font],
    ambient_time: float,
) -> None:
    """Draw the compact arena and animated figures between cards and journal."""
    pygame.draw.rect(surface, COLOR_PANEL_BG, rect, border_radius=PANEL_RADIUS)
    pygame.draw.rect(surface, COLOR_PANEL_BORDER, rect, width=1, border_radius=PANEL_RADIUS)

    floor_y = rect.bottom - 18
    pygame.draw.line(surface, COLOR_PANEL_BORDER, (rect.x + 20, floor_y), (rect.right - 20, floor_y), 2)

    left_x = rect.centerx - COMBAT_ARENA_FIGURE_OFFSET
    right_x = rect.centerx + COMBAT_ARENA_FIGURE_OFFSET
    figures = (
        (left, left_x, 1),
        (right, right_x, -1),
    )
    positions: dict[int, tuple[float, int, int, float]] = {}
    for player, x, facing in figures:
        lunge = animation.lunge_for(player)
        hit = animation.hit_intensity_for(player)
        draw_x = x + figure_offset(facing, lunge, hit)
        head_y = floor_y - 100
        positions[id(player)] = (draw_x, facing, floor_y, head_y)
        pygame.draw.ellipse(
            surface,
            _blend(COLOR_BACKGROUND, SCHOOL_COLORS[player.school.value], 0.22),
            pygame.Rect(round(draw_x - 28), floor_y - 3, 56, 8),
        )

    # Elemental projectile is drawn behind the figures, travelling toward the target.
    projectile = animation.projectile_progress()
    if projectile is not None and animation.attacker is not None and animation.defender is not None:
        actor_pos = positions[id(animation.attacker)]
        target_pos = positions[id(animation.defender)]
        start_x = actor_pos[0] + actor_pos[1] * 30
        target_x = target_pos[0] + target_pos[1] * 23
        _draw_projectile(
            surface,
            animation.attacker,
            start_x,
            target_x,
            floor_y - 65,
            projectile,
            actor_pos[1],
        )

    for player, x, facing in figures:
        draw_x, _, feet_y, head_y = positions[id(player)]
        flourish_color = SCHOOL_COLORS[player.school.value]
        draw_school_flourish(
            surface,
            draw_x,
            head_y,
            feet_y,
            player.school.value,
            flourish_color,
            ambient_time,
        )

        if animation.active and animation.kind == "ability" and player is animation.attacker:
            if player.school is School.WATER:
                _draw_heal_orbit(surface, draw_x, feet_y, animation.elapsed, SCHOOL_COLORS["water"])

        shield_active = player.block_active or player.armor_active
        shield_flash = animation.shield_flash_for(player)
        show_shield = shield_active or shield_flash
        fallen = animation.fallen_for(player)
        pose = animation.pose_for(player)
        hit = animation.hit_intensity_for(player)
        draw_stick_figure(
            surface,
            x,
            feet_y,
            facing=facing,
            color=flourish_color,
            pose=pose,
            lunge=animation.lunge_for(player),
            hit=hit,
            shield=show_shield,
            fallen=fallen,
        )

        if player.armor_active and not fallen:
            _draw_earth_guard(surface, draw_x, feet_y, ambient_time, SCHOOL_COLORS["earth"])
        elif shield_flash and not fallen:
            flash_center = _point(draw_x + facing * 22, feet_y - 74)
            _draw_hit_spark(surface, flash_center, hit or 0.7, COLOR_ACCENT)

    # A small impact flash, plus the floating HP delta (including reflected damage/healing).
    if animation.active and animation.resolved and animation.defender is not None:
        age = animation.elapsed - animation.impact_at
        defender_pos = positions[id(animation.defender)]
        hit_center = _point(defender_pos[0] + defender_pos[1] * 18, floor_y - 70)
        school_color = SCHOOL_COLORS[animation.attacker.school.value] if animation.attacker else COLOR_ACCENT
        _draw_hit_spark(surface, hit_center, animation.hit_intensity_for(animation.defender), school_color)

        for player, _, facing in figures:
            popup = animation.popup_for(player)
            if popup is None:
                continue
            amount, healing = popup
            p_x, _, p_feet, _ = positions[id(player)]
            text = f"+{amount}" if healing else f"−{amount}"
            color = COLOR_HEAL_NUMBER if healing else COLOR_DAMAGE_NUMBER
            _draw_floating_number(
                surface,
                fonts["body"],
                text,
                _point(p_x, p_feet - 122),
                color,
                age,
            )

    vs_font = fonts["small"]
    vs_surface = vs_font.render("VS", True, COLOR_ACCENT)
    surface.blit(vs_surface, vs_surface.get_rect(center=(rect.centerx, floor_y - 58)))
    arena_label = fonts["small"].render("АРЕНА", True, COLOR_TEXT_MUTED)
    surface.blit(arena_label, (rect.x + 14, rect.y + 8))
