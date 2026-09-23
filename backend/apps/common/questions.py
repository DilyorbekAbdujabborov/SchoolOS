import random


def shuffle_options(question: dict) -> dict:
    """A copy of a multiple-choice question `{"text", "options", "correct_index", ...}`
    with its options in a fresh random order and `correct_index` remapped to
    follow the right answer — so the same question served again doesn't keep
    its answer in the same slot (and an AI's habit of always putting the
    right answer first doesn't show through). Any other keys are kept as-is.
    """
    options = list(question["options"])
    order = list(range(len(options)))
    random.shuffle(order)
    return {
        **question,
        "options": [options[i] for i in order],
        "correct_index": order.index(question["correct_index"]),
    }
