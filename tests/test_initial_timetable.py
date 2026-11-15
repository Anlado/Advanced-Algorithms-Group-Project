import csv
from pathlib import Path
from src.data_io.dataset_loader import load_instructors, load_rooms,load_timeslots, load_sections
from src.model.constraints import validate_section_assignment

instructors = load_instructors(Path("data/instructors.csv"))
rooms = load_rooms(Path("data/rooms.csv"))
timeslots = load_timeslots(Path("data/timeslots.csv"))
sections = load_sections(Path("data/sections.csv"))

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