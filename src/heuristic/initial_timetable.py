from src.model.constraints import validate_section_assignment

def get_valid_assignments(
    section,
    rooms,
    timeslots,
    timetable,
    instructors,
    sections,
):
    valid_assignments = []
    section_instructor = instructors[section.instructor_id]

    for room in rooms.values():
        for timeslot in timeslots.values():
            isValid = validate_section_assignment(
                section,
                room, 
                timeslot, 
                timetable, 
                section_instructor, 
                sections, 
                timeslots,
            )
            if isValid:
                valid_assignments.append((timeslot.id, room.id))
    return valid_assignments
