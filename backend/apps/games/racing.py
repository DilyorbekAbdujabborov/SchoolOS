"""Neon Racing — the rules, and a replay of a session's race from its
recorded answers.

The race runs on question time: each question is one stretch of track that
every racer drives. How far the student gets on a stretch depends only on
the answer the server locked in (and whether nitro was fired, which is
checked against the replayed nitro meter before it's accepted); the AI
racers' stretches are deterministic per session, so a reload replays the
exact same race. Nothing about distance, position, nitro or combo is ever
taken from the client.
"""

import random

from .models import GameSession

Difficulty = GameSession.Difficulty

# Everything difficulty changes — tuned by simulation so a student wins about
# every other race at ~70% accuracy on EASY, ~80% on MEDIUM and ~90% on HARD,
# and a perfect run always wins.
DIFFICULTIES = {
    Difficulty.EASY: {"questions": 10, "laps": 2, "ai_scale": 1.1, "nitro_fill": 34},
    Difficulty.MEDIUM: {"questions": 12, "laps": 3, "ai_scale": 1.22, "nitro_fill": 25},
    Difficulty.HARD: {"questions": 14, "laps": 3, "ai_scale": 1.34, "nitro_fill": 20},
}
DEFAULT_DIFFICULTY = Difficulty.MEDIUM

# The AI field. `early`/`late` shape a racer's pace over the race (a fast
# starter vs. a strong finisher); `spread` is how erratic it is.
AI_RACERS = [
    {"id": "volt", "name": "VOLT", "style": "Balanced", "early": 1.0, "late": 1.0, "spread": 0.1},
    {"id": "blaze", "name": "BLAZE", "style": "High acceleration", "early": 1.16, "late": 0.88, "spread": 0.1},
    {"id": "apex", "name": "APEX", "style": "High top speed", "early": 0.86, "late": 1.15, "spread": 0.1},
    {"id": "rogue", "name": "ROGUE", "style": "Aggressive rival", "early": 1.04, "late": 1.04, "spread": 0.25},
]
RIVALS_PER_RACE = 3
AI_BASE_GAIN = 9.0

# The student's stretch: a correct answer drives on, a combo adds pace, a
# wrong one crawls; nitro adds a burst on the stretch it's fired.
CORRECT_GAIN = 10.0
COMBO_GAIN = 0.75
MAX_COMBO_BONUS_STEPS = 4
WRONG_GAIN = 4.5
NITRO_GAIN = 8.0
NITRO_FULL = 100
COMBO_NITRO_BONUS = 10  # extra meter per correct answer from combo ×3 up

XP_PER_QUESTION = 3


def config_for(difficulty: str) -> dict:
    return DIFFICULTIES.get(difficulty) or DIFFICULTIES[DEFAULT_DIFFICULTY]


def rivals_for(session: GameSession) -> list[dict]:
    """Three of the four AI racers, rotated per session so races differ."""
    start = (session.pk or 0) % len(AI_RACERS)
    return [AI_RACERS[(start + i) % len(AI_RACERS)] for i in range(RIVALS_PER_RACE)]


def _ai_gain(session: GameSession, racer: dict, index: int, total: int, scale: float) -> float:
    rng = random.Random(f"{session.pk}-{racer['id']}-{index}")
    phase = racer["early"] if index < total / 2 else racer["late"]
    return AI_BASE_GAIN * scale * phase * (1 + rng.uniform(-racer["spread"], racer["spread"]))


def race_state(session: GameSession) -> dict | None:
    if session.game_type != GameSession.GameType.NEON_RACING:
        return None

    config = config_for(session.difficulty)
    total = len(session.questions) or config["questions"]
    answers = {int(index): selected for index, selected in (session.answers or {}).items()}
    nitro_rounds = set(session.nitro_rounds or [])
    rivals = rivals_for(session)

    player = 0.0
    ai = {racer["id"]: 0.0 for racer in rivals}
    combo = max_combo = nitro_used = 0
    meter = 0
    answered = 0
    last = None

    for index, question in enumerate(session.questions):
        if index not in answers:
            break
        answered += 1
        fired = index in nitro_rounds and meter >= NITRO_FULL
        if fired:
            meter = 0
            nitro_used += 1
        correct = answers[index] == question.get("correct_index")
        if correct:
            combo += 1
            max_combo = max(max_combo, combo)
            gain = CORRECT_GAIN + COMBO_GAIN * min(combo - 1, MAX_COMBO_BONUS_STEPS)
            meter = min(NITRO_FULL, meter + config["nitro_fill"] + (COMBO_NITRO_BONUS if combo >= 3 else 0))
        else:
            combo = 0
            gain = WRONG_GAIN
        if fired:
            gain += NITRO_GAIN
        player += gain
        for racer in rivals:
            ai[racer["id"]] += _ai_gain(session, racer, index, total, config["ai_scale"])
        last = {"correct": correct, "gain": round(gain, 2), "nitro": fired}

    laps = config["laps"]
    sectors = laps * 2
    position = 1 + sum(1 for distance in ai.values() if distance > player)
    finished = answered >= total
    racers = [{"id": "player", "name": "SIZ", "style": "", "distance": round(player, 2), "is_player": True}] + [
        {
            "id": racer["id"],
            "name": racer["name"],
            "style": racer["style"],
            "distance": round(ai[racer["id"]], 2),
            "is_player": False,
        }
        for racer in rivals
    ]
    return {
        "difficulty": session.difficulty or DEFAULT_DIFFICULTY,
        "laps": laps,
        # Laps and checkpoints run on race time (questions), the same clock for everyone.
        "lap": min(laps, answered * laps // total + 1) if total else 1,
        "final_lap": answered * laps // total + 1 >= laps if total else False,
        "checkpoints_total": sectors - 1,
        "checkpoints_passed": sum(1 for k in range(1, sectors) if answered >= round(k * total / sectors)),
        "racers": racers,
        "position": position,
        "field_size": len(racers),
        "combo": combo,
        "max_combo": max_combo,
        "nitro": meter,
        "nitro_ready": meter >= NITRO_FULL,
        "nitro_used": nitro_used,
        "answered": answered,
        "finished": finished,
        "last": last,
        "score": round(player * 10) + max_combo * 20 + (len(racers) - position) * 100,
    }
