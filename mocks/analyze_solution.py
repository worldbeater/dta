import random


def analyze_solution(task, code):
    rnd = random.randint(0, 2)
    if rnd == 0:
        return True, (0, [0.9, 0.1])
    if rnd == 1:
        return True, (1, [0.1, 0.9])
    return False, (0, [])
