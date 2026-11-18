from src.model.constraints import validate_section_assignment


def generate_reassignment_neighbors(timetable, sections, rooms, timeslots, instructors):
    neighborhood = []
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
                        neighborhood.append(candidate)
    return neighborhood

def generate_swap_neighbors(
    timetable, 
    sections, 
    rooms, 
    timeslots, 
    instructors,
    ):
    neighborhood = []

    sections_ids = [section_id for section_id in timetable]

    length= len(sections_ids)

    for i in range(length - 1):
        for j in range(i + 1,length):
            section_id_1 = sections_ids[i]
            section_id_2 = sections_ids[j]
            section_1 = sections[section_id_1]
            section_2 = sections[section_id_2]

            assignment_1 = timetable[section_id_1]
            assignment_2 = timetable[section_id_2]

            # Skip identical assignments
            if assignment_1 != assignment_2:
                # Copy the timetable to preserve the original
                candidate = timetable.copy()

                # Remove both sections' existing assignments
                del candidate[section_id_1]
                del candidate[section_id_2]

                timeslot_1_id, room_1_id = assignment_1
                timeslot_2_id, room_2_id = assignment_2

                # Check whether s1 can take s2's assignment
                if not validate_section_assignment(
                    sections[section_id_1],
                    rooms[room_2_id],
                    timeslots[timeslot_2_id],
                    candidate,
                    instructors[section_1.instructor_id],
                    sections,
                    timeslots,
                ):
                    continue
                
                # Apply the first assignment
                candidate[section_id_1] = assignment_2

                # Check whether s2 can take s1's assignment
                if not validate_section_assignment(
                    sections[section_id_2],
                    rooms[room_1_id],
                    timeslots[timeslot_1_id],
                    candidate,
                    instructors[section_2.instructor_id],
                    sections,
                    timeslots,
                ):
                    continue
                # Apply the second assignment
                candidate[section_id_2] = assignment_1
                
                neighborhood.append(candidate)

    return neighborhood

                
                    

