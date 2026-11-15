import csv
from pathlib import Path

from src.model.instructor import Instructor
from src.model.room import Room
from src.model.section import Section
from src.model.timeslot import Timeslot

def parse_set(value: str) -> set[str]:
    return {
        item.strip()
        for item in value.split(";")
        if item.strip()
    }


def load_instructors(file_path: Path) -> dict[str, Instructor]:
    instructors = {}

    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            instructor = Instructor(
                id=row["id"],
                domains=parse_set(row["domains"]),
                unavailable_slots=parse_set(row["unavailable_slots"]),
                required_no_teach_slots=parse_set(row["required_no_teach_slots"]),
                preferred_slots=parse_set(row["preferred_slots"]),
            )
            instructors[instructor.id] = instructor

    return instructors

def load_rooms(file_path: Path) -> dict[str, Room]:
    rooms = {}

    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            room = Room(
                id=row["id"],
                capacity=int(row["capacity"]),
                is_lab=row["is_lab"].strip().lower() == "true",
                building=row["building"],
            )
            rooms[room.id] = room

    return rooms

def load_timeslots(file_path: Path) -> dict[str, Timeslot]:
    timeslots = {}

    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            timeslot = Timeslot(
                id=row["id"],
                day=row["day"],
                start_time=row["start_time"],
                duration_min=int(row["duration_min"]),
            )
            timeslots[timeslot.id] = timeslot

    return timeslots

def load_sections(file_path: Path) -> dict[str, Section]:
    sections = {}

    with open(file_path, newline="", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            section = Section(
                id=row["id"],
                course_id=row["course_id"],
                subject_area=row["subject_area"],
                enrollment=int(row["enrollment"]),
                instructor_id=row["instructor_id"],
                needs_lab=row["needs_lab"].strip().lower() == "true",
                cohort_id=row["cohort_id"],
                building_pref=row["building_pref"],
            )
            sections[section.id] = section

    return sections

# Validate references, qualifications, and basic room suitability.
# Passing validation does not guarantee a feasible timetable.
def validate_dataset(
    sections: dict[str, Section],
    instructors: dict[str, Instructor],
    rooms: dict[str, Room],
    timeslots: dict[str, Timeslot],
) -> None:

    for section in sections.values():

        # 1. Verify that the assigned instructor exists.
        if section.instructor_id not in instructors:
            raise ValueError(
                f"Section {section.id} references unknown "
                f"instructor {section.instructor_id}"
            )

        instructor = instructors[section.instructor_id]

        # 2. Verify that the instructor is qualified.
        if section.subject_area not in instructor.domains:
            raise ValueError(
                f"Instructor {instructor.id} is not qualified "
                f"to teach section {section.id} "
                f"({section.subject_area})"
            )

        # 3. Verify that at least one room is suitable.
        suitable_room_exists = any(
            room.capacity >= section.enrollment
            and (not section.needs_lab or room.is_lab)
            for room in rooms.values()
        )

        if not suitable_room_exists:
            raise ValueError(
                f"Section {section.id} has no suitable room "
                f"for {section.enrollment} students"
            )
    for instructor in instructors.values():
        referenced_slots = (
            instructor.unavailable_slots
            | instructor.required_no_teach_slots
            | instructor.preferred_slots
        )

        for slot_id in referenced_slots:
            if slot_id not in timeslots:
                raise ValueError(
                    f"Instructor {instructor.id} references "
                    f"unknown timeslot {slot_id}"
                )

if __name__ == "__main__":
    instructors = load_instructors(Path("data/instructors.csv"))
    rooms = load_rooms(Path("data/rooms.csv"))
    timeslots = load_timeslots(Path("data/timeslots.csv"))
    sections = load_sections(Path("data/sections.csv"))

    validate_dataset(sections, instructors, rooms, timeslots)
    print("Dataset validation passed.")

    print(f"Loaded {len(instructors)} instructors")

    for instructor_id, instructor in instructors.items():
        print(instructor_id, instructor)

    print(f"Loaded {len(rooms)} rooms")
    
    for room_id, room in rooms.items():
        print(room_id, room)

    print(f"Loaded {len(timeslots)} timeslots")
        
    for timeslot_id, timeslot in timeslots.items():
        print(timeslot_id, timeslot)

    print(f"Loaded {len(sections)} sections")
            
    for section_id, section in sections.items():
        print(section_id, section)
