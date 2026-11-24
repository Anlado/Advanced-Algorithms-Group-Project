
from src.heuristic.tabu_search import (
    add_tabu_assignments,
    is_tabu,
    remove_expired_tabu_entries,
)


# ============================================================
# TABU MEMORY TESTS
# ============================================================

previous_timetable = {
    "S1": ("T1", "R1"),
    "S2": ("T2", "R2"),
    "S3": ("T3", "R3"),
}

reassigned_timetable = {
    "S1": ("T4", "R1"),
    "S2": ("T2", "R2"),
    "S3": ("T3", "R3"),
}

tabu_memory = {}


# Test A: A reassignment records the old assignment.
add_tabu_assignments(
    previous_timetable,
    reassigned_timetable,
    tabu_memory,
    current_iteration=3,
    tabu_tenure=5,
)

assert tabu_memory == {
    ("S1", "T1", "R1"): 8,
}

print("Test A passed: Reassignment records one old assignment.")


# Test B: Returning to the old assignment is tabu.
assert is_tabu(
    reassigned_timetable,
    previous_timetable,
    tabu_memory,
    current_iteration=4,
)

print("Test B passed: Returning to the old assignment is tabu.")


# Test C: An unrelated assignment is not tabu.
another_timetable = reassigned_timetable.copy()
another_timetable["S1"] = ("T5", "R1")

assert not is_tabu(
    reassigned_timetable,
    another_timetable,
    tabu_memory,
    current_iteration=4,
)

print("Test C passed: Unrestricted assignments remain admissible.")


# Test D: A restriction remains active before expiration.
assert is_tabu(
    reassigned_timetable,
    previous_timetable,
    tabu_memory,
    current_iteration=7,
)

print("Test D passed: Tabu restriction remains active before expiration.")


# Test E: A restriction expires at its expiration iteration.
assert not is_tabu(
    reassigned_timetable,
    previous_timetable,
    tabu_memory,
    current_iteration=8,
)

print("Test E passed: Tabu restriction expires at iteration 8.")


# Test F: Expired entries are removed.
remove_expired_tabu_entries(tabu_memory, current_iteration=8)

assert tabu_memory == {}

print("Test F passed: Expired tabu entries are removed.")


# Test G: A swap records two old assignments.
swapped_timetable = {
    "S1": ("T2", "R2"),
    "S2": ("T1", "R1"),
    "S3": ("T3", "R3"),
}

swap_memory = {}

add_tabu_assignments(
    previous_timetable,
    swapped_timetable,
    swap_memory,
    current_iteration=10,
    tabu_tenure=5,
)

assert swap_memory == {
    ("S1", "T1", "R1"): 15,
    ("S2", "T2", "R2"): 15,
}

print("Test G passed: Swap records two old assignments.")


# Test H: Reversing a swap is tabu.
assert is_tabu(
    swapped_timetable,
    previous_timetable,
    swap_memory,
    current_iteration=11,
)

print("Test H passed: Reversing a swap is tabu.")


# Test I: Unchanged timetables add no tabu entries.
unchanged_memory = {}

add_tabu_assignments(
    previous_timetable,
    previous_timetable.copy(),
    unchanged_memory,
    current_iteration=10,
    tabu_tenure=5,
)

assert unchanged_memory == {}

print("Test I passed: Unchanged timetables add no tabu entries.")


# Test J: Cleanup preserves unexpired entries.
mixed_memory = {
    ("S1", "T1", "R1"): 5,
    ("S2", "T2", "R2"): 10,
    ("S3", "T3", "R3"): 15,
}

remove_expired_tabu_entries(mixed_memory, current_iteration=10)

assert mixed_memory == {
    ("S3", "T3", "R3"): 15,
}

print("Test J passed: Cleanup preserves active restrictions.")


print("\nAll 10 tabu-memory tests passed.")
