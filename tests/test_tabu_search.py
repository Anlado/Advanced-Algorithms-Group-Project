
import csv
from pathlib import Path

from src.data_io.dataset_loader import (
    load_instructors,
    load_rooms,
    load_sections,
    load_timeslots,
)
from src.model.constraints import validate_section_assignment
from src.heuristic.tabu_search import generate_reassignment_neighbors


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


# Generate the reassignment neighborhood.
original_timetable = known_feasible_timetable.copy()

neighbors = generate_reassignment_neighbors(
    known_feasible_timetable,
    sections,
    rooms,
    timeslots,
    instructors,
)


# Test A: Original timetable preservation.
# Verify that generating neighbors does not modify the original timetable.
assert known_feasible_timetable == original_timetable, (
    "Neighborhood generation modified the original timetable."
)

print("Test A passed: Original timetable preserved.")


# Test B: Neighborhood is nonempty.
# Verify that at least one feasible reassignment exists.
assert len(neighbors) > 0, (
    "Expected at least one feasible reassignment neighbor."
)

print("Test B passed: Reassignment neighborhood is nonempty.")


# Test C: Every neighbor schedules all sections.
# Verify that no section is missing or added.
for neighbor in neighbors:
    assert set(neighbor) == set(sections), (
        "A neighboring timetable does not contain exactly the required sections."
    )

print("Test C passed: Every neighbor contains all sections.")


# Test D: Every neighbor differs by exactly one assignment.
# Verify that the reassignment operation changes one section only.
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
# Validate each neighbor from an empty partial timetable so that
# each section is checked against previously validated assignments.
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
# Verify that each generated neighbor represents a unique assignment.
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
