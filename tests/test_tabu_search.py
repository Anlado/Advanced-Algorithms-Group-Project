
import csv
from pathlib import Path

from src.data_io.dataset_loader import (
    load_instructors,
    load_rooms,
    load_sections,
    load_timeslots,
)
from src.model.constraints import validate_section_assignment
from src.heuristic.tabu_search import (
    generate_reassignment_neighbors,
    generate_swap_neighbors,
)


# Load the dataset.
instructors = load_instructors(Path("data/instructors.csv"))
rooms = load_rooms(Path("data/rooms.csv"))
timeslots = load_timeslots(Path("data/timeslots.csv"))
sections = load_sections(Path("data/sections.csv"))


# Load the known feasible timetable.
known_feasible_timetable = {}

with open(
    "data/known_feasible_timetable.csv",
    newline="",
    encoding="utf-8",
) as file:
    reader = csv.DictReader(file)

    for row in reader:
        known_feasible_timetable[row["section_id"]] = (
            row["timeslot_id"],
            row["room_id"],
        )


# ============================================================
# REASSIGNMENT NEIGHBORHOOD TESTS
# ============================================================

original_timetable = known_feasible_timetable.copy()

neighbors = generate_reassignment_neighbors(
    known_feasible_timetable,
    sections,
    rooms,
    timeslots,
    instructors,
)


# Test A: Original timetable preservation.
assert known_feasible_timetable == original_timetable, (
    "Neighborhood generation modified the original timetable."
)

print("Test A passed: Original timetable preserved.")


# Test B: Neighborhood is nonempty.
assert len(neighbors) > 0, (
    "Expected at least one feasible reassignment neighbor."
)

print("Test B passed: Reassignment neighborhood is nonempty.")


# Test C: Every neighbor schedules all sections.
for neighbor in neighbors:
    assert set(neighbor) == set(sections), (
        "A neighboring timetable does not contain exactly the required sections."
    )

print("Test C passed: Every neighbor contains all sections.")


# Test D: Every neighbor differs by exactly one assignment.
for neighbor in neighbors:
    changed_sections = [
        section_id
        for section_id in original_timetable
        if neighbor[section_id] != original_timetable[section_id]
    ]

    assert len(changed_sections) == 1, (
        f"Expected exactly one changed section, got {changed_sections}"
    )

print("Test D passed: Every neighbor changes exactly one section.")


# Test E: Every neighboring timetable satisfies all hard constraints.
for neighbor_index, neighbor in enumerate(neighbors):
    validated_timetable = {}

    for section_id, assignment in neighbor.items():
        timeslot_id, room_id = assignment

        section = sections[section_id]
        room = rooms[room_id]
        timeslot = timeslots[timeslot_id]
        instructor = instructors[section.instructor_id]

        is_valid = validate_section_assignment(
            section,
            room,
            timeslot,
            validated_timetable,
            instructor,
            sections,
            timeslots,
        )

        assert is_valid, (
            f"Neighbor {neighbor_index} violates a hard constraint "
            f"at section {section_id}: {assignment}"
        )

        validated_timetable[section_id] = assignment

print("Test E passed: All neighbors satisfy hard constraints.")


# Test F: No duplicate neighboring timetables.
neighbor_signatures = [
    tuple(sorted(neighbor.items()))
    for neighbor in neighbors
]

assert len(neighbor_signatures) == len(set(neighbor_signatures)), (
    "Duplicate neighboring timetables were generated."
)

print("Test F passed: No duplicate neighbors.")


# Test G: No neighbor is identical to the original timetable.
for neighbor in neighbors:
    assert neighbor != original_timetable, (
        "Neighborhood contains the original timetable."
    )

print("Test G passed: Every neighbor differs from the original.")

print(f"\nTotal feasible reassignment neighbors: {len(neighbors)}")
print("All reassignment neighborhood tests passed.")


# ============================================================
# SWAP NEIGHBORHOOD TESTS
# ============================================================

original_timetable = known_feasible_timetable.copy()

swap_neighbors = generate_swap_neighbors(
    known_feasible_timetable,
    sections,
    rooms,
    timeslots,
    instructors,
)


# Test H: Original timetable preservation.
assert known_feasible_timetable == original_timetable, (
    "Swap neighborhood generation modified the original timetable."
)

print("\nTest H passed: Original timetable preserved.")


# Test I: Neighborhood is nonempty.
assert len(swap_neighbors) > 0, (
    "Expected at least one feasible swap neighbor."
)

print("Test I passed: Swap neighborhood is nonempty.")


# Test J: Every neighbor schedules all sections.
for neighbor in swap_neighbors:
    assert set(neighbor) == set(sections), (
        "A swap neighbor does not contain exactly the required sections."
    )

print("Test J passed: Every swap neighbor contains all sections.")


# Test K: Every neighbor swaps exactly two assignments.
for neighbor in swap_neighbors:
    changed_sections = [
        section_id
        for section_id in original_timetable
        if neighbor[section_id] != original_timetable[section_id]
    ]

    assert len(changed_sections) == 2, (
        f"Expected exactly two changed sections, got {changed_sections}"
    )

    section_id_1, section_id_2 = changed_sections

    assert neighbor[section_id_1] == original_timetable[section_id_2], (
        "First section did not receive the second section's assignment."
    )

    assert neighbor[section_id_2] == original_timetable[section_id_1], (
        "Second section did not receive the first section's assignment."
    )

print("Test K passed: Every neighbor swaps exactly two assignments.")


# Test L: Every swap neighbor satisfies all hard constraints.
for neighbor_index, neighbor in enumerate(swap_neighbors):
    validated_timetable = {}

    for section_id, assignment in neighbor.items():
        timeslot_id, room_id = assignment

        section = sections[section_id]
        room = rooms[room_id]
        timeslot = timeslots[timeslot_id]
        instructor = instructors[section.instructor_id]

        is_valid = validate_section_assignment(
            section,
            room,
            timeslot,
            validated_timetable,
            instructor,
            sections,
            timeslots,
        )

        assert is_valid, (
            f"Swap neighbor {neighbor_index} violates a hard constraint "
            f"at section {section_id}: {assignment}"
        )

        validated_timetable[section_id] = assignment

print("Test L passed: All swap neighbors satisfy hard constraints.")


# Test M: No duplicate or unchanged swap neighbors.
swap_signatures = [
    tuple(sorted(neighbor.items()))
    for neighbor in swap_neighbors
]

assert len(swap_signatures) == len(set(swap_signatures)), (
    "Duplicate swap neighbors were generated."
)

for neighbor in swap_neighbors:
    assert neighbor != original_timetable, (
        "Swap neighborhood contains the original timetable."
    )

print("Test M passed: No duplicate or unchanged swap neighbors.")


# Test N: Every possible pair is either rejected or generated correctly.
# There are n(n-1)/2 unique pairs of sections.
section_ids = list(original_timetable)
total_pairs = len(section_ids) * (len(section_ids) - 1) // 2

assert len(swap_neighbors) <= total_pairs, (
    "Generated more swap neighbors than possible unique section pairs."
)

# Build all distinct swap candidates without filtering by feasibility.
all_swap_candidates = []

for i in range(len(section_ids) - 1):
    for j in range(i + 1, len(section_ids)):
        s1 = section_ids[i]
        s2 = section_ids[j]

        if original_timetable[s1] == original_timetable[s2]:
            continue

        candidate = original_timetable.copy()
        candidate[s1] = original_timetable[s2]
        candidate[s2] = original_timetable[s1]
        all_swap_candidates.append(candidate)

# Check each candidate independently against all hard constraints.
feasible_signatures = set()
infeasible_count = 0

for candidate in all_swap_candidates:
    validated_timetable = {}
    feasible = True

    for section_id, (timeslot_id, room_id) in candidate.items():
        section = sections[section_id]

        if not validate_section_assignment(
            section,
            rooms[room_id],
            timeslots[timeslot_id],
            validated_timetable,
            instructors[section.instructor_id],
            sections,
            timeslots,
        ):
            feasible = False
            break

        validated_timetable[section_id] = candidate[section_id]

    if feasible:
        feasible_signatures.add(tuple(sorted(candidate.items())))
    else:
        infeasible_count += 1

assert set(swap_signatures) == feasible_signatures, (
    "Generated swap neighbors do not match the independently "
    "validated feasible swap candidates."
)

print(
    "Test N passed: All feasible swaps generated and "
    "all infeasible swaps rejected."
)


print(f"\nTotal possible section pairs: {total_pairs}")
print(f"Total infeasible swap candidates: {infeasible_count}")
print(f"Total feasible swap neighbors: {len(swap_neighbors)}")
print("All swap neighborhood tests passed.")
