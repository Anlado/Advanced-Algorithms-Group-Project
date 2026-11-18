from src.model.constraints import validate_section_assignment


def generate_reassignment_neighbors(timetable, sections, rooms, timeslots, instructors):
    neighboring_timetables = []
    for section in sections.values():
        current_timeslot_id, current_room_id = timetable[section.id]
        for timeslot in timeslots.values():
            for room in rooms.values():
                # Skip the section's current assignment
                if (timeslot.id, room.id) != (current_timeslot_id, current_room_id):
                    # Copy the timetable to preserve the original
                    candidate = timetable.copy()
                    # Remove the section's existing assignment
                    del candidate[section.id]

                    # Check whether the proposed assignment is feasible
                    if validate_section_assignment(
                        section, 
                        room, 
                        timeslot, 
                        candidate, 
                        instructors[section.instructor_id], 
                        sections, 
                        timeslots,
                    ):
                        # Apply the proposed assignment
                        candidate[section.id] = (timeslot.id, room.id)
                        # Add the feasible timetable to the neighborhood
                        neighboring_timetables.append(candidate)
    return neighboring_timetables