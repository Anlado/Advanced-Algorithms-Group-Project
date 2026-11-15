from src.model.constraints import validate_section_assignment

# Return all feasible (timeslot_id, room_id) assignments for a section
# given the current partial timetable.
# Each candidate must satisfy the implemented hard constraints.
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

# Select the next unassigned section using Minimum Remaining Values (MRV).
# Choose the section with the fewest valid assignments.
# Break ties by choosing the section with the highest unassigned degree.
# Return (selected_section, valid_assignments).
# Return (None, []) if an unassigned section has no valid assignments.
def select_section_mrv(
    sections,
    rooms,
    timeslots,
    timetable,
    instructors,
):
    selected_section = None
    smallest_valid_assignments = []
    smallest_size = -1
    highest_degree = -1

    for section_id, section in sections.items():

        # Already scheduled sections are not candidates for selection.
        if section_id not in timetable:
            validAssignments = get_valid_assignments(
                section, 
                rooms, 
                timeslots, 
                timetable, 
                instructors, 
                sections,
            )
            
            current_size = len(validAssignments)

            # An empty domain means the current partial timetable
            # cannot be extended into a complete feasible timetable.
            if current_size == 0:
                return None, []

            current_degree = getUnassignedDegree(section, sections, timetable)

            # MRV: prefer the smallest domain.
            # Degree tie-breaker: prefer more unassigned conflicts.
            if (smallest_size == -1 
                or current_size < smallest_size
                or (current_size == smallest_size and current_degree > highest_degree)):
                selected_section = section
                smallest_size = current_size
                highest_degree = current_degree
                smallest_valid_assignments = validAssignments

    return selected_section, smallest_valid_assignments

# Count the unassigned sections that conflict with the given section.
# Two sections conflict if they share an instructor or cohort.
# Assigned sections and the section itself are excluded.
def getUnassignedDegree(section, sections, timetable):
    degree = 0

    for other_section_id, other_section in sections.items():
        isSection = other_section.id == section.id
        inTimeTable = other_section.id in timetable
        shareInstructor = other_section.instructor_id == section.instructor_id
        shareCohort = other_section.cohort_id == section.cohort_id
        if not isSection and not inTimeTable:
            # Sharing both an instructor and cohort still counts
            # as only one neighboring section.
            if shareInstructor or shareCohort:
                degree += 1

    return degree