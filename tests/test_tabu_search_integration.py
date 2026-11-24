
import csv
from pathlib import Path
from unittest.mock import patch

from src.data_io.dataset_loader import (
    load_instructors,
    load_rooms,
    load_sections,
    load_timeslots,
)
from src.heuristic.tabu_search import tabu_search
from src.model.constraints import validate_section_assignment
from src.model.soft_constraints import calculate_total_penalty


# ============================================================
# TEST DATA
# ============================================================

sections = load_sections(Path("data/sections.csv"))
rooms = load_rooms(Path("data/rooms.csv"))
timeslots = load_timeslots(Path("data/timeslots.csv"))
instructors = load_instructors(Path("data/instructors.csv"))

cohort_ids = {section.cohort_id for section in sections.values()}

initial_timetable = {}

with open("data/known_feasible_timetable.csv", newline="", encoding="utf-8") as file:
    for row in csv.DictReader(file):
        initial_timetable[row["section_id"]] = (
            row["timeslot_id"],
            row["room_id"],
        )

original_timetable = initial_timetable.copy()

idle_weight = 1
preference_weight = 45


def run_search(max_iterations=20, no_improvement_limit=10):
    return tabu_search(
        initial_timetable,
        sections,
        rooms,
        timeslots,
        instructors,
        cohort_ids,
        idle_weight,
        preference_weight,
        tabu_tenure=5,
        max_iterations=max_iterations,
        no_improvement_max_iterations=no_improvement_limit,
    )


def penalty(timetable):
    return calculate_total_penalty(
        timetable,
        sections,
        instructors,
        timeslots,
        cohort_ids,
        idle_weight,
        preference_weight,
    )


def is_feasible(timetable):
    validated = {}

    for section_id, (timeslot_id, room_id) in timetable.items():
        section = sections[section_id]

        if not validate_section_assignment(
            section,
            rooms[room_id],
            timeslots[timeslot_id],
            validated,
            instructors[section.instructor_id],
            sections,
            timeslots,
        ):
            return False

        validated[section_id] = (timeslot_id, room_id)

    return True


# ============================================================
# REAL-DATASET INTEGRATION TESTS
# ============================================================

result = run_search()


# Test A: The original timetable is preserved.
assert initial_timetable == original_timetable

print("Test A passed: Initial timetable preserved.")


# Test B: The result contains exactly the required sections.
assert set(result) == set(sections)

print("Test B passed: Result contains all sections.")


# Test C: The result satisfies all hard constraints.
assert is_feasible(result)

print("Test C passed: Result satisfies all hard constraints.")


# Test D: The returned solution is no worse than the initial solution.
initial_penalty = penalty(initial_timetable)
final_penalty = penalty(result)

assert final_penalty <= initial_penalty

print("Test D passed: Best penalty is no worse than initial penalty.")


# Test E: Zero maximum iterations returns the initial timetable.
zero_iteration_result = run_search(max_iterations=0)

assert zero_iteration_result == initial_timetable

print("Test E passed: Zero iterations returns initial timetable.")


# Test F: Zero allowed non-improving iterations prevents the search.
zero_stagnation_result = run_search(no_improvement_limit=0)

assert zero_stagnation_result == initial_timetable

print("Test F passed: Zero stagnation limit prevents search.")



# ============================================================
# BOUNDED TABU SEARCH TESTS
# ============================================================

import random


# Test G: Search history starts with the initial penalty
# and never reports a worsening best-known penalty.

random.seed(42)
history = []

result = tabu_search(
    initial_timetable,
    sections,
    rooms,
    timeslots,
    instructors,
    cohort_ids,
    idle_weight,
    preference_weight,
    tabu_tenure=5,
    max_iterations=10,
    no_improvement_max_iterations=5,
    history=history,
)

assert history
assert history[0]["iteration"] == 0
assert history[0]["current_penalty"] == initial_penalty
assert history[0]["best_penalty"] == initial_penalty

best_scores = [
    entry["best_penalty"]
    for entry in history
]

assert all(
    later <= earlier
    for earlier, later in zip(
        best_scores,
        best_scores[1:],
    )
)

assert penalty(result) == history[-1]["best_penalty"]

print("Test G passed: Best-known penalty history is consistent.")


# Test H: Maximum iteration limit is respected.

random.seed(42)
short_history = []

tabu_search(
    initial_timetable,
    sections,
    rooms,
    timeslots,
    instructors,
    cohort_ids,
    idle_weight,
    preference_weight,
    tabu_tenure=5,
    max_iterations=2,
    no_improvement_max_iterations=10,
    history=short_history,
)

assert len(short_history) <= 3
assert short_history[-1]["iteration"] <= 2

print("Test H passed: Maximum iteration limit respected.")


# Test I: Search never exceeds its stagnation limit.

random.seed(42)
stagnation_history = []

tabu_search(
    initial_timetable,
    sections,
    rooms,
    timeslots,
    instructors,
    cohort_ids,
    idle_weight,
    preference_weight,
    tabu_tenure=5,
    max_iterations=20,
    no_improvement_max_iterations=1,
    history=stagnation_history,
)

consecutive_non_improvements = 0

for previous, current in zip(
    stagnation_history,
    stagnation_history[1:],
):
    if current["best_penalty"] < previous["best_penalty"]:
        consecutive_non_improvements = 0
    else:
        consecutive_non_improvements += 1

    assert consecutive_non_improvements <= 1

print("Test I passed: Stagnation limit respected.")


# Test J: Returned timetable remains feasible, and the
# full penalty agrees with the recorded best-known penalty.

random.seed(42)
verification_history = []

verified_result = tabu_search(
    initial_timetable,
    sections,
    rooms,
    timeslots,
    instructors,
    cohort_ids,
    idle_weight,
    preference_weight,
    tabu_tenure=5,
    max_iterations=10,
    no_improvement_max_iterations=5,
    history=verification_history,
)

assert set(verified_result) == set(sections)
assert is_feasible(verified_result)
assert penalty(verified_result) == (
    verification_history[-1]["best_penalty"]
)

print("Test J passed: Feasibility and final penalty verified.")

print("\nAll bounded Tabu Search integration checks passed.")
print(f"Initial timetable penalty: {initial_penalty}")
print(f"Best timetable penalty: {penalty(verified_result)}")
