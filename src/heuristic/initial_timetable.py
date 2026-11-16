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


# Order candidate assignments using Least Constraining Value (LCV).
# Prefer assignments that preserve the most valid options
# for the remaining unassigned sections.
# Precondition: section is not already assigned in timetable.
# Temporary assignments are undone after each candidate is evaluated.
def order_assignments_lcv(
    section,
    validAssignments,
    sections,
    rooms,
    timeslots,
    timetable,
    instructors,
):
    scored_assignments = []

    for assignment in validAssignments:
        # Temporarily assign the selected section.
        timetable[section.id] = assignment

        remaining_options = 0
        dead_end = False

        try:
            for other_section_id, other_section in sections.items():
                # Only evaluate sections that remain unassigned.
                if other_section_id not in timetable:
                    other_assignments = get_valid_assignments(
                        other_section,
                        rooms,
                        timeslots,
                        timetable,
                        instructors,
                        sections,
                    )

                    # Detect an immediate dead end.
                    if len(other_assignments) == 0:
                        dead_end = True
                        break

                    remaining_options += len(other_assignments)

        finally:
            # Undo the temporary assignment.
            del timetable[section.id]

        scored_assignments.append(
            (dead_end, remaining_options, assignment)
        )

    # Prioritize non-dead-end assignments.
    # Then prefer higher scores (least constraining first).
    scored_assignments.sort(
        key=lambda item: (item[0], -item[1])
    )

    return [
        assignment
        for _, _, assignment in scored_assignments
    ]


# Recursively construct a feasible timetable using backtracking.
# MRV selects the next section, while LCV determines the order
# in which its valid assignments are attempted.
# Return True when every section has been assigned.
# Return False when the current partial timetable leads to a dead end.
def backtrack(
    sections,
    rooms,
    timeslots,
    timetable,
    instructors,
):
    # Base case: every section has an assignment.
    if len(timetable) == len(sections):
        return True

    # Select the most constrained unassigned section.
    selected_section, valid_assignments = select_section_mrv(
        sections,
        rooms,
        timeslots,
        timetable,
        instructors,
    )

    # No valid assignment means this branch cannot succeed.
    if selected_section is None:
        return False

    # Try the least constraining assignments first.
    ordered_assignments = order_assignments_lcv(
        selected_section,
        valid_assignments,
        sections,
        rooms,
        timeslots,
        timetable,
        instructors,
    )

    for assignment in ordered_assignments:
        # Make a tentative assignment.
        timetable[selected_section.id] = assignment

        # Recursively schedule the remaining sections.
        if backtrack(
            sections,
            rooms,
            timeslots,
            timetable,
            instructors,
        ):
            return True

        # Undo the assignment if the recursive attempt failed.
        del timetable[selected_section.id]

    # Every candidate failed.
    return False


# Generate an initial timetable satisfying all hard constraints.
# Return the completed timetable if successful, or None otherwise.
def generate_initial_timetable(
    sections,
    rooms,
    timeslots,
    instructors,
):
    timetable = {}

    success = backtrack(
        sections,
        rooms,
        timeslots,
        timetable,
        instructors,
    )

    if success:
        return timetable

    return None