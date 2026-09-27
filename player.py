"""Модель игрока: характеристики, ресурсы, журнал событий."""

STATS = ["concentration", "athletics", "guile", "luck"]

STAT_NAMES = {
    "concentration": "Концентрация",
    "athletics": "Физ. подготовка",
    "guile": "Хитрость",
    "luck": "Удача",
}

STAT_ICONS = {
    "concentration": "🔥",
    "athletics": "🦿",
    "guile": "🎭",
    "luck": "🍀",
}


class Player:
    def __init__(self, name: str):
        self.name = name
        self.stats = {s: 10 for s in STATS}
        self.energy = 100
        self.max_energy = 100
        self.log = []          # список строк — журнал событий/действий
        self.alive_in_tournament = True
        self.battle_hp = 0
        self.battle_max_hp = 0

    def change_stat(self, stat: str, amount: int):
        self.stats[stat] = max(0, self.stats[stat] + amount)

    def change_energy(self, amount: int):
        self.energy = max(0, min(self.max_energy, self.energy + amount))

    def power_score(self) -> int:
        """Суммарная мощь для итогового подсчёта (если не доходит до финала)."""
        return sum(self.stats.values())

    def add_log(self, day: int, text: str):
        self.log.append(f"День {day}: {text}")

    def init_battle_stats(self):
        self.battle_max_hp = 50 + self.stats["athletics"] * 3
        self.battle_hp = self.battle_max_hp
