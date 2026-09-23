"""Tower Defense — the rules, and a replay of a session's battle from its
recorded answers.

Like Jang maydoni, nothing about the fight is ever taken from the client:
every wave, enemy HP, shield, base HP, combo and the victory/defeat outcome
is recomputed here from the answers the server itself locked in, in order.
A correct answer is the tower's shot at the front enemy of the current wave;
a wrong one lets that enemy strike the base.
"""

from .models import GameSession

Difficulty = GameSession.Difficulty

# Per enemy type: HP, a shield that soaks damage before HP, and the damage it
# deals the base when a question is missed.
ENEMY_TYPES = {
    "scout": {"hp": 25, "shield": 0, "attack": 10},
    "shield": {"hp": 40, "shield": 20, "attack": 12},
    "tank": {"hp": 70, "shield": 0, "attack": 18},
    "boss": {"hp": 0, "shield": 0, "attack": 25},  # HP comes from the difficulty
}

# Everything difficulty changes — tuned by simulation so a student wins about
# 2 in 3 games at ~70% accuracy on EASY, ~80% on MEDIUM and ~90% on HARD.
# `speed` is presentation only (how briskly the enemies march on screen);
# every number that decides the outcome is here.
DIFFICULTIES = {
    Difficulty.EASY: {
        "questions": 10,
        "base_hp": 100,
        "tower_damage": 40,
        "enemy_hp_scale": 1.0,
        "enemy_attack_scale": 1.0,
        "boss_hp": 100,
        "speed": 1.0,
        "waves": [["scout", "scout"], ["shield"], ["boss"]],
    },
    Difficulty.MEDIUM: {
        "questions": 12,
        "base_hp": 100,
        "tower_damage": 42,
        "enemy_hp_scale": 1.0,
        "enemy_attack_scale": 1.25,
        "boss_hp": 110,
        "speed": 1.3,
        "waves": [["scout", "scout"], ["shield"], ["tank"], ["boss"]],
    },
    Difficulty.HARD: {
        "questions": 14,
        "base_hp": 100,
        "tower_damage": 44,
        "enemy_hp_scale": 1.15,
        "enemy_attack_scale": 1.6,
        "boss_hp": 130,
        "speed": 1.6,
        "waves": [["scout", "scout"], ["shield", "tank"], ["scout", "shield"], ["boss"]],
    },
}
DEFAULT_DIFFICULTY = Difficulty.MEDIUM

# Combo thresholds → tower damage multiplier.
POWER_BOOST_COMBO = 5
OVERCHARGE_COMBO = 10
POWER_BOOST_MULTIPLIER = 1.5
OVERCHARGE_MULTIPLIER = 2.0

XP_PER_QUESTION = 3


def config_for(difficulty: str) -> dict:
    return DIFFICULTIES.get(difficulty) or DIFFICULTIES[DEFAULT_DIFFICULTY]


def boost_for(combo: int) -> tuple[str | None, float]:
    if combo >= OVERCHARGE_COMBO:
        return "OVERCHARGE", OVERCHARGE_MULTIPLIER
    if combo >= POWER_BOOST_COMBO:
        return "POWER_BOOST", POWER_BOOST_MULTIPLIER
    return None, 1.0


def _spawn_wave(types: list[str], config: dict) -> list[dict]:
    enemies = []
    for enemy_type in types:
        base = ENEMY_TYPES[enemy_type]
        hp = config["boss_hp"] if enemy_type == "boss" else round(base["hp"] * config["enemy_hp_scale"])
        shield = round(base["shield"] * config["enemy_hp_scale"])
        enemies.append({"type": enemy_type, "hp": hp, "max_hp": hp, "shield": shield, "max_shield": shield})
    return enemies


def defense_state(session: GameSession) -> dict | None:
    if session.game_type != GameSession.GameType.TOWER_DEFENSE:
        return None

    config = config_for(session.difficulty)
    waves = [_spawn_wave(types, config) for types in config["waves"]]
    answers = {int(index): selected for index, selected in (session.answers or {}).items()}
    total = len(session.questions) or config["questions"]

    wave_index = 0
    base_hp = config["base_hp"]
    combo = max_combo = 0
    enemies_defeated = waves_cleared = rounds = 0
    victory = False
    last_event = None

    for index, question in enumerate(session.questions):
        if index not in answers:
            break
        rounds += 1
        enemies = waves[wave_index]
        front_index = next(i for i, enemy in enumerate(enemies) if enemy["hp"] > 0)
        front = enemies[front_index]

        if answers[index] == question.get("correct_index"):
            combo += 1
            max_combo = max(max_combo, combo)
            boost, multiplier = boost_for(combo)
            damage = round(config["tower_damage"] * multiplier)
            absorbed = min(front["shield"], damage)
            front["shield"] -= absorbed
            front["hp"] = max(0, front["hp"] - (damage - absorbed))
            killed = front["hp"] == 0
            enemies_defeated += killed
            wave_done = all(enemy["hp"] == 0 for enemy in enemies)
            last_event = {
                "kind": "hit",
                "target": front_index,
                "damage": damage,
                "shield_hit": absorbed > 0,
                "killed": killed,
                "wave_cleared": wave_done,
                "boost": boost,
            }
            if wave_done:
                waves_cleared += 1
                if wave_index + 1 == len(waves):
                    victory = True
                    break
                wave_index += 1
        else:
            combo = 0
            attack = round(ENEMY_TYPES[front["type"]]["attack"] * config["enemy_attack_scale"])
            base_hp = max(0, base_hp - attack)
            last_event = {"kind": "base_hit", "source": front_index, "damage": attack}
            if base_hp == 0:
                break

    boost, _ = boost_for(combo)
    score = (
        enemies_defeated * 100
        + waves_cleared * 250
        + max_combo * 50
        + (base_hp * 5 if victory else 0)
    )
    return {
        "difficulty": session.difficulty or DEFAULT_DIFFICULTY,
        "base_hp": base_hp,
        "max_base_hp": config["base_hp"],
        "combo": combo,
        "max_combo": max_combo,
        "boost": boost,
        "wave": wave_index + 1,
        "waves_total": len(waves),
        "boss_wave": waves[wave_index][0]["type"] == "boss",
        "enemies": waves[wave_index],
        "enemies_defeated": enemies_defeated,
        "enemies_total": sum(len(wave) for wave in waves),
        "waves_cleared": waves_cleared,
        "rounds_played": rounds,
        "over": victory or base_hp == 0 or rounds >= total,
        "victory": victory,
        "score": score,
        "last_event": last_event,
        "speed": config["speed"],
        "tower_damage": config["tower_damage"],
    }
