"""Duel rules — timing, the AI opponents, and the replay that turns both
sides' answer logs into HP, combo, abilities, the speed bonus and a score.

The replay walks every answer from both sides in the order the server
received them, so things that depend on timing between the two players
(a shield blocking the next incoming hit, who was quicker on a question they
both got right) come out the same on every read. Knowledge decides the
match: a correct answer is worth 10 points, being the quicker of two
correct answers only 1.
"""

import random

HP_MAX = 100
QUESTION_COUNTS = (5, 10, 15)
SECONDS_PER_QUESTION = {"EASY": 30, "MEDIUM": 20, "HARD": 15}
# Network slack on top of the visible timer before an answer counts as late.
GRACE_MS = 2500
COUNTDOWN_SECONDS = 3

POINTS_CORRECT = 10
POINTS_QUICK = 1
HIT_DAMAGE = 12
COMBO_DAMAGE = 2  # extra per combo step…
MAX_COMBO_STEPS = 4  # …up to this many steps
WRONG_SELF_DAMAGE = 4

# Combo milestones → a one-off ability.
ABILITIES = {3: "SPEED_BOOST", 5: "SHIELD", 7: "POWER_ATTACK"}

# XP (through apps.gamification.award_xp — no separate economy).
MAX_ANSWER_XP = 40  # scaled by accuracy, as before
RESULT_XP = {"WIN": 10, "DRAW": 5, "LOSS": 0}
STREAK_BONUS_AT = 3
STREAK_BONUS_XP = 15

AI_OPPONENTS = {
    "NOVICE": {
        "name": "BITTY",
        "title": "AI Novice",
        "difficulty": "EASY",
        "personality": "Doim quvnoq, ba'zan shoshilib xato qiladi.",
        "accuracy": 0.55,
        "seconds": (7.0, 15.0),
    },
    "SCHOLAR": {
        "name": "PROF. OWLBERT",
        "title": "AI Scholar",
        "difficulty": "MEDIUM",
        "personality": "Tez fikrlaydi, qiyin savollarni yaxshi ko'radi.",
        "accuracy": 0.72,
        "seconds": (4.5, 11.0),
    },
    "MASTER": {
        "name": "ZENITH",
        "title": "AI Master",
        "difficulty": "HARD",
        "personality": "Sokin, aniq va juda tez. Uni yengish — haqiqiy yutuq.",
        "accuracy": 0.88,
        "seconds": (3.0, 7.5),
    },
}


def limit_ms(difficulty: str) -> int:
    return SECONDS_PER_QUESTION.get(difficulty, SECONDS_PER_QUESTION["MEDIUM"]) * 1000


def ai_answer(duel_pk: int, index: int, question: dict, level: str) -> tuple[int, int]:
    """The AI's (selected option, elapsed ms) for one question — deterministic
    per duel, so a reload replays the same opponent."""
    profile = AI_OPPONENTS[level]
    rng = random.Random(f"duel-{duel_pk}-{index}")
    correct = rng.random() < profile["accuracy"]
    key = question["correct_index"]
    if correct:
        selected = key
    else:
        wrong = [i for i in range(len(question["options"])) if i != key]
        selected = rng.choice(wrong) if wrong else key
    elapsed = int(rng.uniform(*profile["seconds"]) * 1000)
    return selected, elapsed


def _new_side() -> dict:
    return {
        "hp": HP_MAX,
        "answered": 0,
        "correct": 0,
        "quick": 0,
        "combo": 0,
        "max_combo": 0,
        "shield": False,
        "power": False,
        "abilities": [],
        "last": None,
    }


def battle_state(questions: list[dict], logs: dict[str, dict], difficulty: str) -> dict:
    """Replays both sides. `logs` is {"challenger": log, "opponent": log}, each
    log {"answers": {"<i>": [selected, elapsed_ms, at_ms]}}."""
    limit = limit_ms(difficulty) + GRACE_MS
    sides = {role: _new_side() for role in ("challenger", "opponent")}
    outcome: dict[str, dict[int, tuple[bool, int]]] = {"challenger": {}, "opponent": {}}

    events = []
    for role, log in logs.items():
        for index, (selected, elapsed, at) in (log.get("answers") or {}).items():
            events.append((at, role, int(index), selected, elapsed))
    events.sort()

    for _at, role, index, selected, elapsed in events:
        if index >= len(questions):
            continue
        me, other_role = sides[role], ("opponent" if role == "challenger" else "challenger")
        other = sides[other_role]
        correct = selected == questions[index]["correct_index"] and elapsed <= limit
        outcome[role][index] = (correct, elapsed)
        me["answered"] += 1
        event = {"index": index, "correct": correct, "timed_out": elapsed > limit}

        if correct:
            me["correct"] += 1
            me["combo"] += 1
            me["max_combo"] = max(me["max_combo"], me["combo"])
            ability = ABILITIES.get(me["combo"])
            if ability:
                me["abilities"].append(ability)
                event["ability"] = ability
                if ability == "SPEED_BOOST":
                    me["quick"] += POINTS_QUICK
                elif ability == "SHIELD":
                    me["shield"] = True
                elif ability == "POWER_ATTACK":
                    me["power"] = True
            damage = HIT_DAMAGE + COMBO_DAMAGE * min(me["combo"] - 1, MAX_COMBO_STEPS)
            if me["power"] and ability != "POWER_ATTACK":
                damage *= 2
                me["power"] = False
                event["power_used"] = True
            if other["shield"]:
                other["shield"] = False
                event["blocked"] = True
                damage = 0
            other["hp"] = max(0, other["hp"] - damage)
            event["damage"] = damage
        else:
            me["combo"] = 0
            me["hp"] = max(0, me["hp"] - WRONG_SELF_DAMAGE)

        # Both sides have now answered this question — reward the quicker correct one.
        if index in outcome[other_role]:
            other_correct, other_elapsed = outcome[other_role][index]
            if correct and other_correct and elapsed != other_elapsed:
                winner = role if elapsed < other_elapsed else other_role
                sides[winner]["quick"] += POINTS_QUICK
                event["quick_to"] = winner
        me["last"] = event

    for side in sides.values():
        side["score"] = side["correct"] * POINTS_CORRECT + side["quick"]
    return sides


def result_of(sides: dict) -> str:
    challenger, opponent = sides["challenger"]["score"], sides["opponent"]["score"]
    if challenger > opponent:
        return "CHALLENGER"
    if opponent > challenger:
        return "OPPONENT"
    return "DRAW"
