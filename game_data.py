"""
Таблицы событий и действий из концепта.
Каждая запись — данные, не код: добавление новых строк не требует правки логики.

Механика броска:
  chance = min(90, 20 + stat_value * 4)   # шанс "хорошего" исхода в %
  Позитивное событие: удача -> крит-эффект, неудача -> обычный эффект.
  Негативное событие: удача -> эффект избежан (avoid_effect), неудача -> полный штраф (fail_effect).
  Действие (тренировка/саботаж): удача -> крит-эффект, неудача -> обычный эффект.
"""

EVENTS = [
    {
        "id": "E1", "desc": "Плохо выспался перед тренировкой", "kind": "negative",
        "stat": "athletics", "placeholder": "🛌",
        "fail_effect": {"energy": -25}, "avoid_effect": {"energy": 0},
    },
    {
        "id": "E2", "desc": "Гулял по окрестностям и нашёл редкое место для медитации",
        "kind": "positive", "stat": "concentration", "placeholder": "🌌",
        "normal_effect": {"concentration": 1}, "crit_effect": {"concentration": 3},
    },
    {
        "id": "E3", "desc": "Потянул лодыжку на разминке", "kind": "negative",
        "stat": "athletics", "placeholder": "🤕",
        "fail_effect": {"energy": -15, "athletics": -1}, "avoid_effect": {"energy": -5},
    },
    {
        "id": "E4", "desc": "Нашёл редкий эликсир концентрации", "kind": "positive",
        "stat": "concentration", "placeholder": "🧪",
        "normal_effect": {"concentration": 1}, "crit_effect": {"concentration": 3},
    },
    {
        "id": "E5", "desc": "Поссорился с соперником из другой школы", "kind": "negative",
        "stat": "guile", "placeholder": "😠",
        "fail_effect": {"concentration": -1, "energy": -10}, "avoid_effect": {"energy": -5},
    },
    {
        "id": "E6", "desc": "Удачная тренировка со случайным наставником", "kind": "positive",
        "stat": "luck", "placeholder": "🍀",
        "normal_effect": {"luck": 1}, "crit_effect": {"luck": 3},
    },
]

TRAININGS = [
    {"id": "T1", "desc": "Тренировка тела", "stat": "athletics", "placeholder": "🏋️",
     "cost": 20, "normal_effect": {"athletics": 1}, "crit_effect": {"athletics": 3}},
    {"id": "T2", "desc": "Медитация и изучение заклинаний", "stat": "concentration", "placeholder": "🧘",
     "cost": 20, "normal_effect": {"concentration": 1}, "crit_effect": {"concentration": 3}},
    {"id": "T3", "desc": "Тренировка скрытности", "stat": "guile", "placeholder": "🥷",
     "cost": 20, "normal_effect": {"guile": 1}, "crit_effect": {"guile": 3}},
    {"id": "T4", "desc": "Испытание удачи (азартные игры, риск)", "stat": "luck", "placeholder": "🎲",
     "cost": 20, "normal_effect": {"luck": 1}, "crit_effect": {"luck": 3}},
]

# Действия-саботажи — требуют цель (другого игрока)
SABOTAGE_ACTIONS = [
    {"id": "AC5", "desc": "Подлить яд сопернику", "stat": "guile", "placeholder": "🧪",
     "cost": 15, "target_effect_normal": {"energy": -15}, "target_effect_crit": {"energy": -30},
     "self_fail_effect": {"energy": -10}},
    {"id": "AC6", "desc": "Поставить подножку на тренировке", "stat": "guile", "placeholder": "🦵",
     "cost": 10, "target_effect_normal": {"energy": -10}, "target_effect_crit": {"athletics": -1, "energy": -10},
     "self_fail_effect": {"energy": -5}},
]


def success_chance(stat_value: int) -> int:
    return min(90, 20 + stat_value * 4)
