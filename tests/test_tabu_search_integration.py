
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
# CONTROLLED SEARCH TESTS
# ============================================================

# These tests replace the neighborhood generators and penalty function
# temporarily so that we can examine the search's decisions precisely.
# The real-dataset tests above already exercise the actual components.

X0 = {"S1": ("T1", "R1")}
X1 = {"S1": ("T2", "R1")}
X2 = {"S1": ("T3", "R1")}

scores = {
    "T1": 100,
    "T2": 80,
    "T3": 120,
}


def fake_penalty(timetable, *args):
    return scores[timetable["S1"][0]]


def fake_reassignment(timetable, *args):
    current = timetable["S1"][0]

    if current == "T1":
        return [X1.copy()]
    if current == "T2":
        return [X2.copy()]
    return []


def fake_swap(timetable, *args):
    return []


# Test G: The search may accept a worsening move but returns the best.
accepted_moves = []

def record_move(previous, new, memory, iteration, tenure):
    accepted_moves.append(new.copy())
    return memory


with (
    patch(
        "src.heuristic.tabu_search.generate_reassignment_neighbors",
        side_effect=fake_reassignment,
    ),
    patch(
        "src.heuristic.tabu_search.generate_swap_neighbors",
        side_effect=fake_swap,
    ),
    patch(
        "src.heuristic.tabu_search.calculate_total_penalty",
        side_effect=fake_penalty,
    ),
    patch(
        "src.heuristic.tabu_search.add_tabu_assignments",
        side_effect=record_move,
    ),
):
    controlled_result = tabu_search(
        X0, {}, {}, {}, {}, set(),
        1, 45, 5, 10, 5,
    )

assert accepted_moves == [X1, X2], (
    f"Expected moves to X1 and X2, got {accepted_moves}"
)
assert controlled_result == X1

print("Test G passed: Worsening move accepted while best solution preserved.")


# Test H: Maximum iteration limit is respected.
accepted_moves.clear()

with (
    patch(
        "src.heuristic.tabu_search.generate_reassignment_neighbors",
        side_effect=fake_reassignment,
    ),
    patch(
        "src.heuristic.tabu_search.generate_swap_neighbors",
        side_effect=fake_swap,
    ),
    patch(
        "src.heuristic.tabu_search.calculate_total_penalty",
        side_effect=fake_penalty,
    ),
    patch(
        "src.heuristic.tabu_search.add_tabu_assignments",
        side_effect=record_move,
    ),
):
    tabu_search(X0, {}, {}, {}, {}, set(), 1, 45, 5, 1, 5)

assert accepted_moves == [X1]

print("Test H passed: Maximum iteration limit respected.")


# Test I: Consecutive non-improvement limit is respected.
accepted_moves.clear()

with (
    patch(
        "src.heuristic.tabu_search.generate_reassignment_neighbors",
        side_effect=fake_reassignment,
    ),
    patch(
        "src.heuristic.tabu_search.generate_swap_neighbors",
        side_effect=fake_swap,
    ),
    patch(
        "src.heuristic.tabu_search.calculate_total_penalty",
        side_effect=fake_penalty,
    ),
    patch(
        "src.heuristic.tabu_search.add_tabu_assignments",
        side_effect=record_move,
    ),
):
    tabu_search(X0, {}, {}, {}, {}, set(), 1, 45, 5, 10, 1)

assert accepted_moves == [X1, X2]

print("Test I passed: Consecutive non-improvement limit respected.")


# Test J: Aspiration overrides a tabu restriction when the candidate
# improves on the best penalty found so far.

A0 = {"S1": ("T1", "R1")}
A1 = {"S1": ("T2", "R1")}
A2 = {"S1": ("T3", "R1")}

aspiration_scores = {
    "T1": 100,
    "T2": 80,
    "T3": 60,
}

aspiration_moves = []


def aspiration_penalty(timetable, *args):
    return aspiration_scores[timetable["S1"][0]]


def aspiration_neighbors(timetable, *args):
    current = timetable["S1"][0]

    if current == "T1":
        return [A1.copy()]

    if current == "T2":
        return [A2.copy()]

    return []


def aspiration_tabu(current, candidate, memory, iteration):
    # Simulate A2 being prohibited by tabu memory.
    return candidate == A2


def record_aspiration_move(previous, new, memory, iteration, tenure):
    aspiration_moves.append(new.copy())
    return memory


with (
    patch(
        "src.heuristic.tabu_search.generate_reassignment_neighbors",
        side_effect=aspiration_neighbors,
    ),
    patch(
        "src.heuristic.tabu_search.generate_swap_neighbors",
        return_value=[],
    ),
    patch(
        "src.heuristic.tabu_search.calculate_total_penalty",
        side_effect=aspiration_penalty,
    ),
    patch(
        "src.heuristic.tabu_search.is_tabu",
        side_effect=aspiration_tabu,
    ),
    patch(
        "src.heuristic.tabu_search.add_tabu_assignments",
        side_effect=record_aspiration_move,
    ),
):
    aspiration_result = tabu_search(
        A0,
        {},
        {},
        {},
        {},
        set(),
        1,
        45,
        5,
        10,
        5,
    )

assert aspiration_moves == [A1, A2], (
    f"Expected both moves to be accepted, got {aspiration_moves}"
)

assert aspiration_result == A2, (
    f"Expected aspiration to allow the best timetable A2, got {aspiration_result}"
)

print("Test J passed: Aspiration overrides tabu for a new best solution.")


print("\nAll 10 Tabu Search integration tests passed.")
print(f"Initial timetable penalty: {initial_penalty}")
print(f"Best timetable penalty: {final_penalty}")
print(f"Penalty reduction: {initial_penalty - final_penalty}")
