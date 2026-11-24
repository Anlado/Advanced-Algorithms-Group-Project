import csv
from pathlib import Path
from src.data_io.dataset_loader import load_instructors, load_rooms,load_timeslots, load_sections
from src.model.constraints import validate_section_assignment
from src.heuristic.initial_timetable import generate_initial_timetable, get_valid_assignments
from src.heuristic.initial_timetable import (
    select_section_mrv,
    getUnassignedDegree,
)

from src.heuristic.initial_timetable import (
    get_valid_assignments,
    select_section_mrv,
    getUnassignedDegree,
    order_assignments_lcv,
)


instructors = load_instructors(Path("data/instructors.csv"))
rooms = load_rooms(Path("data/rooms.csv"))
timeslots = load_timeslots(Path("data/timeslots.csv"))
sections = load_sections(Path("data/sections.csv"))

# Positive test:
# Verify that a known feasible timetable satisfies all implemented
# hard constraints and schedules every section exactly once.

known_feasible_timetable = {}

with open("data/known_feasible_timetable.csv", newline="", encoding="utf-8") as file:
    reader = csv.DictReader(file)

    for row in reader:
        section_id = row["section_id"]
        timeslot_id = row["timeslot_id"]
        room_id = row["room_id"]

        known_feasible_timetable[section_id] = (timeslot_id, room_id)

print(known_feasible_timetable)

validated_timetable = {}

for section_id, assignment in known_feasible_timetable.items():
    timeslot_id, room_id = assignment

    section = sections[section_id]
    room = rooms[room_id]
    timeslot = timeslots[timeslot_id]
    instructor = instructors[section.instructor_id]

    isValid = validate_section_assignment(
        section, 
        room, 
        timeslot, 
        validated_timetable, 
        instructor, 
        sections, 
        timeslots,
    )

    assert isValid, f"Invalid assignment for section {section_id}: {assignment}"
    validated_timetable[section_id] = assignment

assert set(validated_timetable) == set(sections)
print("Known feasible timetable passed all hard constraints.")

# Negative test:
# Verify that two sections belonging to the same cohort cannot
# occupy overlapping timeslots, even when assigned different rooms.

partial_timetable = {
    "S1": ("T1", "R1")
}

section = sections["S2"]
room = rooms["R2"]
timeslot = timeslots["T1"]
instructor = instructors[section.instructor_id]

isValid = validate_section_assignment(
    section,
    room,
    timeslot,
    partial_timetable,
    instructor,
    sections,
    timeslots,
)

assert not isValid, "Expected S2 to be rejected due to cohort conflict"
print("Cohort conflict test passed: S2 was correctly rejected.")


# Positive test:
# Verify that S1 has 20 valid room-timeslot assignments
# when the timetable is empty.

assignments = get_valid_assignments(
    sections["S1"],
    rooms,
    timeslots,
    {},
    instructors,
    sections,
)

assert len(assignments) == 20, (
    f"Expected 20 valid assignments for S1, got {len(assignments)}"
)

assert all(timeslot_id != "T6" for timeslot_id, room_id in assignments)

print("S1 valid assignments test passed.")


# Verify that MRV selects an unassigned section with valid assignments.
selected_section, valid_assignments = select_section_mrv(
    sections,
    rooms,
    timeslots,
    {},
    instructors,
)

assert selected_section is not None
assert len(valid_assignments) > 0

# Verify that the selected section's degree is nonnegative.
degree = getUnassignedDegree(selected_section, sections, {})
assert degree >= 0

print("MRV selection and degree sanity tests passed.")


# Positive test:
# Verify that LCV returns every valid assignment exactly once
# and does not modify the original timetable.

partial_timetable = {}

section = sections["S1"]

valid_assignments = get_valid_assignments(
    section,
    rooms,
    timeslots,
    partial_timetable,
    instructors,
    sections,
)

original_timetable = partial_timetable.copy()

ordered_assignments = order_assignments_lcv(
    section,
    valid_assignments,
    sections,
    rooms,
    timeslots,
    partial_timetable,
    instructors,
)

assert len(ordered_assignments) == len(valid_assignments)
assert set(ordered_assignments) == set(valid_assignments)
assert partial_timetable == original_timetable

print("LCV assignment preservation test passed.")


# Ordering test:
# Verify that LCV prioritizes assignments that leave more
# valid options for the remaining sections.
def lcv_score(section, assignment):
    candidate_timetable = {section.id: assignment}
    remaining_options = 0
    dead_end = False

    for other_section_id, other_section in sections.items():
        if other_section_id not in candidate_timetable:
            options = get_valid_assignments(
                other_section,
                rooms,
                timeslots,
                candidate_timetable,
                instructors,
                sections,
            )

            if len(options) == 0:
                dead_end = True
                break

            remaining_options += len(options)

    return (dead_end, -remaining_options)

scores = [
    lcv_score(section, assignment)
    for assignment in ordered_assignments
]

assert scores == sorted(scores), (
    "LCV assignments are not ordered from least "
    "constraining to most constraining."
)

print("LCV ordering test passed.")

# Integration test:
# Generate a complete timetable using MRV, LCV, and backtracking.
# Verify that every section is scheduled and all assignments
# satisfy the implemented hard constraints.
generated_timetable = generate_initial_timetable(
    sections,
    rooms,
    timeslots,
    instructors,
)

assert generated_timetable is not None, (
    "Expected a feasible timetable to be generated."
)

assert set(generated_timetable) == set(sections), (
    "Generated timetable does not contain every section."
)

validated_timetable = {}

for section_id, assignment in generated_timetable.items():
    timeslot_id, room_id = assignment

    section = sections[section_id]

    is_valid = validate_section_assignment(
        section,
        rooms[room_id],
        timeslots[timeslot_id],
        validated_timetable,
        instructors[section.instructor_id],
        sections,
        timeslots,
    )

    assert is_valid, (
        f"Invalid generated assignment for {section_id}: {assignment}"
    )

    validated_timetable[section_id] = assignment

print("Initial timetable generation test passed.")
print("Generated timetable:", generated_timetable)