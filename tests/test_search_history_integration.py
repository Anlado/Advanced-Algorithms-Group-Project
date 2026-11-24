
from src.data_io.dataset_loader import (
    load_sections,
    load_rooms,
    load_timeslots,
    load_instructors,
)
from src.heuristic.tabu_search import tabu_search
from src.model.soft_constraints import calculate_total_penalty


def run_tests():
    # Load the project's sample dataset.
    sections = load_sections("data/sections.csv")
    rooms = load_rooms("data/rooms.csv")
    timeslots = load_timeslots("data/timeslots.csv")
    instructors = load_instructors("data/instructors.csv")

    cohort_ids = {section.cohort_id for section in sections.values()}

    # Use the feasible timetable from our earlier integration tests.
    initial_timetable = {
        "S1": ("T2", "R1"),
        "S2": ("T1", "R2"),
        "S3": ("T1", "R3"),
        "S4": ("T3", "R1"),
        "S5": ("T6", "R4"),
        "S6": ("T6", "R1"),
        "S7": ("T1", "R1"),
        "S8": ("T6", "R2"),
    }

    idle_weight = 1
    preference_weight = 45

    initial_penalty = calculate_total_penalty(
        initial_timetable,
        sections,
        instructors,
        timeslots,
        cohort_ids,
        idle_weight,
        preference_weight,
    )

    history = []

    best_timetable = tabu_search(
        initial_timetable,
        sections,
        rooms,
        timeslots,
        instructors,
        cohort_ids,
        idle_weight,
        preference_weight,
        tabu_tenure=5,
        max_iterations=100,
        no_improvement_max_iterations=20,
        history=history,
    )

    final_penalty = calculate_total_penalty(
        best_timetable,
        sections,
        instructors,
        timeslots,
        cohort_ids,
        idle_weight,
        preference_weight,
    )

    # Test A: History contains the initial timetable.
    assert len(history) >= 1
    assert history[0]["iteration"] == 0
    assert history[0]["current_penalty"] == initial_penalty
    assert history[0]["best_penalty"] == initial_penalty

    print("Test A passed: Initial timetable recorded.")

    # Test B: Iterations are recorded consecutively.
    iterations = [entry["iteration"] for entry in history]

    assert iterations == list(range(len(history)))

    print("Test B passed: Iterations recorded consecutively.")

    # Test C: Best-known penalty never increases.
    best_penalties = [entry["best_penalty"] for entry in history]

    assert all(
        best_penalties[i] <= best_penalties[i - 1]
        for i in range(1, len(best_penalties))
    )

    print("Test C passed: Best-known penalty never increases.")

    # Test D: Best penalty never exceeds current penalty.
    assert all(
        entry["best_penalty"] <= entry["current_penalty"]
        for entry in history
    )

    print("Test D passed: Best penalty is never worse than current.")

    # Test E: Final history agrees with returned solution.
    assert history[-1]["best_penalty"] == final_penalty

    print("Test E passed: Final history matches returned solution.")

    # Test F: Optimization preserves or improves the initial penalty.
    assert final_penalty <= initial_penalty

    print("Test F passed: Optimization does not worsen best solution.")

    # Test G: Search respects maximum iteration limit.
    assert len(history) <= 101

    print("Test G passed: Maximum iteration limit respected.")

    print("\nAll 7 search-history integration tests passed.")
    print(f"Initial penalty: {initial_penalty}")
    print(f"Final penalty: {final_penalty}")
    print(f"Recorded iterations: {len(history) - 1}")


if __name__ == "__main__":
    run_tests()
