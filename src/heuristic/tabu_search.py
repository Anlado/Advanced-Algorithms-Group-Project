
from src.model.constraints import validate_section_assignment


# Generate feasible neighboring timetables using single-section reassignment.
# For each section, try alternative timeslot and room combinations.
# Keep only assignments that satisfy all implemented hard constraints.
# Return the list of feasible neighbors without modifying the original timetable.
def generate_reassignment_neighbors(timetable, sections, rooms, timeslots, instructors):
    neighborhood = []

    for section in sections.values():
        current_timeslot_id, current_room_id = timetable[section.id]

        for timeslot in timeslots.values():
            for room in rooms.values():
                # Skip the section's current assignment.
                if (timeslot.id, room.id) != (current_timeslot_id, current_room_id):
                    # Copy the timetable to preserve the original.
                    candidate = timetable.copy()

                    # Remove the section's existing assignment so it does not
                    # conflict with the proposed assignment during validation.
                    del candidate[section.id]

                    # Check whether the proposed assignment is feasible.
                    if validate_section_assignment(
                        section,
                        room,
                        timeslot,
                        candidate,
                        instructors[section.instructor_id],
                        sections,
                        timeslots,
                    ):
                        # Apply the proposed assignment.
                        candidate[section.id] = (timeslot.id, room.id)

                        # Add the feasible timetable to the neighborhood.
                        neighborhood.append(candidate)

    return neighborhood


# Generate feasible neighboring timetables by swapping two sections' assignments.
# Consider each unique pair of sections exactly once.
# A swap is accepted only if both sections satisfy all hard constraints
# after exchanging their timeslot and room assignments.
# Return the list of feasible neighbors without modifying the original timetable.
def generate_swap_neighbors(
    timetable,
    sections,
    rooms,
    timeslots,
    instructors,
):
    neighborhood = []

    sections_ids = [section_id for section_id in timetable]
    length = len(sections_ids)

    # Generate each unique pair without repeating reversed pairs.
    for i in range(length - 1):
        for j in range(i + 1, length):
            section_id_1 = sections_ids[i]
            section_id_2 = sections_ids[j]
            section_1 = sections[section_id_1]
            section_2 = sections[section_id_2]

            assignment_1 = timetable[section_id_1]
            assignment_2 = timetable[section_id_2]

            # Skip identical assignments because swapping them
            # would not produce a different timetable.
            if assignment_1 != assignment_2:
                # Copy the timetable to preserve the original.
                candidate = timetable.copy()

                # Remove both sections' existing assignments before validation.
                del candidate[section_id_1]
                del candidate[section_id_2]

                timeslot_1_id, room_1_id = assignment_1
                timeslot_2_id, room_2_id = assignment_2

                # Check whether the first section can take
                # the second section's original assignment.
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

                # Apply the first assignment before validating the second,
                # so conflicts between the new assignments are detected.
                candidate[section_id_1] = assignment_2

                # Check whether the second section can take
                # the first section's original assignment.
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

                # Apply the second assignment only if it is feasible.
                candidate[section_id_2] = assignment_1

                # Both assignments are valid, so accept the complete swap.
                neighborhood.append(candidate)

    return neighborhood


# Record the previous assignments of sections changed by an accepted move.
# Store each old assignment as (section_id, timeslot_id, room_id).
# The dictionary value is the iteration at which the restriction expires.
# A reassignment records one entry, while a swap records two entries.
# Return the updated tabu memory.
def add_tabu_assignments(
    previous_timetable,
    new_timetable,
    tabu_memory,
    current_iteration,
    tabu_tenure,
):
    for section_id in previous_timetable:
        if previous_timetable[section_id] != new_timetable[section_id]:
            timeslot_id, room_id = previous_timetable[section_id]

            # Prohibit restoring the previous assignment for tabu_tenure
            # iterations. Existing entries are updated if encountered again.
            tabu_memory[(section_id, timeslot_id, room_id)] = current_iteration + tabu_tenure

    return tabu_memory


# Determine whether a candidate move violates an active tabu restriction.
# Compare the current timetable with the candidate to identify changed sections.
# A move is tabu if any changed section receives a prohibited assignment.
# Return True if the candidate is tabu, or False otherwise.
# Expired restrictions are ignored even if they remain in the dictionary.
def is_tabu(
    current_timetable,
    candidate_timetable,
    tabu_memory,
    current_iteration,
):
    for section_id in current_timetable:
        if current_timetable[section_id] != candidate_timetable[section_id]:
            timeslot_id, room_id = candidate_timetable[section_id]

            # Check whether the candidate restores a prohibited assignment.
            if (section_id, timeslot_id, room_id) in tabu_memory:
                # A restriction is active only before its expiration iteration.
                if current_iteration < tabu_memory[(section_id, timeslot_id, room_id)]:
                    return True

    return False


# Remove tabu restrictions that have reached their expiration iteration.
# An entry expires when current_iteration is greater than or equal to
# its stored expiration value.
# Iterate over a copy so entries can safely be deleted from the dictionary.
# Return the updated tabu memory.
def remove_expired_tabu_entries(tabu_memory, current_iteration):
    for entry in tabu_memory.copy():
        if tabu_memory[entry] <= current_iteration:
            del tabu_memory[entry]

    return tabu_memory

# Determine whether a candidate satisfies the aspiration criterion.
# A candidate satisfies aspiration if its penalty is strictly lower
# than the best penalty found across all previous search iterations.
# This allows an otherwise tabu move to be considered for selection.
# Return True if aspiration is satisfied, or False otherwise.
def meets_aspiration_criterion(candidate_penalty, best_penalty):
    return candidate_penalty < best_penalty
