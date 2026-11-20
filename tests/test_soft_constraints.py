
import csv
from pathlib import Path

from src.data_io.dataset_loader import (
    load_instructors,
    load_rooms,
    load_sections,
    load_timeslots,
)

from src.model.soft_constraints import (
    calculate_cohort_idle_time_penalty,
    calculate_instructor_preference_penalty,
    calculate_total_penalty,
)


instructors = load_instructors(Path("data/instructors.csv"))
rooms = load_rooms(Path("data/rooms.csv"))
timeslots = load_timeslots(Path("data/timeslots.csv"))
sections = load_sections(Path("data/sections.csv"))


# Load a known feasible timetable.
known_feasible_timetable = {}

with open(
    "data/known_feasible_timetable.csv",
    newline="",
    encoding="utf-8"
) as file:
    reader = csv.DictReader(file)

    for row in reader:
        section_id = row["section_id"]
        timeslot_id = row["timeslot_id"]
        room_id = row["room_id"]

        known_feasible_timetable[section_id] = (
            timeslot_id,
            room_id
        )


# Unit test: Instructor preference penalty
# Verify that a single section assigned to a preferred
# timeslot receives no preference penalty.

test_sections = [sections["S1"]]

test_timetable = {
    "S1": known_feasible_timetable["S1"]
}

unit_penalty = calculate_instructor_preference_penalty(
    test_timetable,
    test_sections,
    instructors
)

assert unit_penalty == 0, (
    f"Expected S1 preference penalty of 0, got {unit_penalty}"
)

print("Unit test: Instructor preference penalty passed.")


# Integration test: Instructor preference penalty
# Verify the total number of preference violations
# across all sections in the known feasible timetable.

integration_penalty = calculate_instructor_preference_penalty(
    known_feasible_timetable,
    sections.values(),
    instructors
)

assert integration_penalty == 4, (
    f"Expected total preference penalty of 4, got {integration_penalty}"
)

print("Integration test: Instructor preference penalty passed.")


# Unit test: Cohort idle-time penalty
# Verify that consecutive classes produce no idle time,
# while a one-hour gap produces a 60-minute penalty.

test_sections = [sections["S1"], sections["S2"]]
test_cohorts = ["C1"]


# Test A: No gap between classes (9 AM and 10 AM).
test_timetable_a = {
    "S1": ("T1", "R1"),
    "S2": ("T2", "R2")
}

idle_penalty_a = calculate_cohort_idle_time_penalty(
    test_timetable_a,
    test_sections,
    timeslots,
    test_cohorts
)

assert idle_penalty_a == 0, (
    f"Expected 0 minutes, got {idle_penalty_a}"
)

print("Cohort idle-time test A passed.")


# Test B: One-hour gap between classes (9 AM and 11 AM).
test_timetable_b = {
    "S1": ("T1", "R1"),
    "S2": ("T3", "R2")
}

idle_penalty_b = calculate_cohort_idle_time_penalty(
    test_timetable_b,
    test_sections,
    timeslots,
    test_cohorts
)

assert idle_penalty_b == 60, (
    f"Expected 60 minutes, got {idle_penalty_b}"
)

print("Cohort idle-time test B passed.")


# Integration test: Total weighted penalty
# Verify that calculate_total_penalty combines cohort
# idle time and instructor preference penalties using
# the configured weights.

idle_weight = 1
preference_weight = 45

cohort_ids = ["C1", "C2", "C3", "C4"]


# Calculate the individual penalties independently.
expected_idle = calculate_cohort_idle_time_penalty(
    known_feasible_timetable,
    sections.values(),
    timeslots,
    cohort_ids
)

expected_preference = calculate_instructor_preference_penalty(
    known_feasible_timetable,
    sections.values(),
    instructors
)


# Calculate the expected weighted penalty.
expected_total = (
    idle_weight * expected_idle
    + preference_weight * expected_preference
)


# Calculate the total penalty using the function being tested.
actual_total = calculate_total_penalty(
    known_feasible_timetable,
    sections.values(),
    instructors,
    timeslots,
    cohort_ids,
    idle_weight,
    preference_weight
)

assert actual_total == expected_total, (
    f"Expected total penalty {expected_total}, "
    f"got {actual_total}"
)

print("Total penalty integration test passed.")
print(f"Cohort idle-time penalty: {expected_idle}")
print(f"Instructor preference penalty: {expected_preference}")
print(f"Total weighted penalty: {actual_total}")
