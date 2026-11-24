
from collections import defaultdict
import random

from src.model.constraints import validate_section_assignment
from src.model.soft_constraints import calculate_total_penalty
from src.model.time_utils import time_to_minutes


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


# Record the current and best-known penalty at a search iteration.
# This history is used to generate the Tabu Search quality curve.
def record_search_history(history, iteration, current_penalty, best_penalty):
    if history is not None:
        history.append({
            "iteration": iteration,
            "current_penalty": current_penalty,
            "best_penalty": best_penalty,
        })


# Optimize an initial feasible timetable using Tabu Search.
# Generate reassignment and swap neighbors, then evaluate their soft penalties.
# Select the best admissible neighbor using tabu memory and aspiration.
# Allow worsening moves to escape local optima while preserving the best solution.
# Stop when an iteration limit, stagnation limit, or zero penalty is reached.
# Return the best feasible timetable found.
def tabu_search(
    timetable,
    sections,
    rooms,
    timeslots,
    instructors,
    cohort_ids,
    idle_weight,
    preference_weight,
    tabu_tenure,
    max_iterations,
    no_improvement_max_iterations,
    history=None,
    reassignment_attempts=200,
    swap_attempts=100,
):
    """
    Bounded-neighborhood Tabu Search.

    Preserves:
      - Reassignment and swap moves
      - Hard-constraint feasibility
      - Tabu memory and aspiration
      - Best admissible neighbor selection
      - Worsening moves
      - Search history and stopping criteria

    Uses exact incremental penalty evaluation.
    """

    current_timetable = timetable.copy()
    best_timetable = timetable.copy()

    section_ids = list(current_timetable.keys())
    slot_ids = list(timeslots.keys())
    room_ids = list(rooms.keys())

    # --------------------------------------------------------
    # 1. Precompute cohort membership and slot information
    # --------------------------------------------------------

    cohort_sections = defaultdict(list)

    for section in sections.values():
        cohort_sections[section.cohort_id].append(
            section.id
        )

    slot_info = {}

    for slot_id, slot in timeslots.items():
        start = time_to_minutes(slot.start_time)

        slot_info[slot_id] = (
            slot.day,
            start,
            start + slot.duration_min,
        )

    # --------------------------------------------------------
    # 2. Calculate one cohort's idle-time penalty
    # --------------------------------------------------------

    def cohort_idle_penalty(schedule, cohort_id):
        daily_schedule = defaultdict(list)

        for section_id in cohort_sections[cohort_id]:
            slot_id, _ = schedule[section_id]

            day, start, end = slot_info[slot_id]

            daily_schedule[day].append(
                (start, end)
            )

        total_idle = 0

        for meetings in daily_schedule.values():
            meetings.sort()

            for index in range(len(meetings) - 1):
                current_end = meetings[index][1]
                next_start = meetings[index + 1][0]

                total_idle += max(
                    0,
                    next_start - current_end,
                )

        return total_idle

    # --------------------------------------------------------
    # 3. Calculate instructor preference contribution
    # --------------------------------------------------------

    def section_preference_penalty(
        schedule,
        section_id,
    ):
        section = sections[section_id]
        instructor = instructors[section.instructor_id]

        slot_id, _ = schedule[section_id]

        if (
            instructor.preferred_slots
            and slot_id not in instructor.preferred_slots
        ):
            return 1

        return 0

    # --------------------------------------------------------
    # 4. Calculate exact penalty change for a move
    # --------------------------------------------------------

    def calculate_move_delta(
        old_schedule,
        new_schedule,
        changed_section_ids,
    ):
        affected_cohorts = {
            sections[section_id].cohort_id
            for section_id in changed_section_ids
        }

        old_idle = sum(
            cohort_idle_penalty(
                old_schedule,
                cohort_id,
            )
            for cohort_id in affected_cohorts
        )

        new_idle = sum(
            cohort_idle_penalty(
                new_schedule,
                cohort_id,
            )
            for cohort_id in affected_cohorts
        )

        old_preference = sum(
            section_preference_penalty(
                old_schedule,
                section_id,
            )
            for section_id in changed_section_ids
        )

        new_preference = sum(
            section_preference_penalty(
                new_schedule,
                section_id,
            )
            for section_id in changed_section_ids
        )

        return (
            idle_weight * (new_idle - old_idle)
            + preference_weight
            * (new_preference - old_preference)
        )

    # --------------------------------------------------------
    # 5. Initialize search
    # --------------------------------------------------------

    current_penalty = calculate_total_penalty(
        current_timetable,
        sections,
        instructors,
        timeslots,
        cohort_ids,
        idle_weight,
        preference_weight,
    )

    best_penalty = current_penalty

    tabu_memory = {}
    iteration = 0
    no_improvement = 0

    record_search_history(
        history,
        iteration,
        current_penalty,
        best_penalty,
    )

    print("\nStarting bounded Tabu Search...", flush=True)
    print(f"Initial penalty: {current_penalty}", flush=True)

    # --------------------------------------------------------
    # 6. Evaluate one candidate move
    # --------------------------------------------------------

    def evaluate_candidate(
        candidate,
        changed_section_ids,
        current_iteration,
        selected,
    ):
        selected_schedule, selected_penalty = selected

        delta = calculate_move_delta(
            current_timetable,
            candidate,
            changed_section_ids,
        )

        candidate_penalty = current_penalty + delta

        tabu = is_tabu(
            current_timetable,
            candidate,
            tabu_memory,
            current_iteration,
        )

        aspiration = meets_aspiration_criterion(
            candidate_penalty,
            best_penalty,
        )

        if tabu and not aspiration:
            return selected

        if candidate_penalty < selected_penalty:
            return candidate, candidate_penalty

        return selected

    # --------------------------------------------------------
    # 7. Main Tabu Search loop
    # --------------------------------------------------------

    while (
        iteration < max_iterations
        and no_improvement < no_improvement_max_iterations
        and best_penalty > 0
    ):
        iteration += 1

        remove_expired_tabu_entries(
            tabu_memory,
            iteration,
        )

        selected_neighbor = None
        selected_penalty = float("inf")

        feasible_moves = 0

        # ----------------------------------------------------
        # 7A. Sample reassignment moves
        # ----------------------------------------------------

        for _ in range(reassignment_attempts):
            section_id = random.choice(section_ids)
            section = sections[section_id]

            slot_id = random.choice(slot_ids)
            room_id = random.choice(room_ids)

            new_assignment = (slot_id, room_id)

            if (
                new_assignment
                == current_timetable[section_id]
            ):
                continue

            candidate = current_timetable.copy()
            del candidate[section_id]

            if not validate_section_assignment(
                section,
                rooms[room_id],
                timeslots[slot_id],
                candidate,
                instructors[section.instructor_id],
                sections,
                timeslots,
            ):
                continue

            candidate[section_id] = new_assignment

            feasible_moves += 1

            selected_neighbor, selected_penalty = (
                evaluate_candidate(
                    candidate,
                    [section_id],
                    iteration,
                    (
                        selected_neighbor,
                        selected_penalty,
                    ),
                )
            )

        # ----------------------------------------------------
        # 7B. Sample swap moves
        # ----------------------------------------------------

        for _ in range(swap_attempts):
            section_id_1, section_id_2 = (
                random.sample(section_ids, 2)
            )

            section_1 = sections[section_id_1]
            section_2 = sections[section_id_2]

            assignment_1 = current_timetable[
                section_id_1
            ]

            assignment_2 = current_timetable[
                section_id_2
            ]

            if assignment_1 == assignment_2:
                continue

            candidate = current_timetable.copy()

            del candidate[section_id_1]
            del candidate[section_id_2]

            slot_2, room_2 = assignment_2

            if not validate_section_assignment(
                section_1,
                rooms[room_2],
                timeslots[slot_2],
                candidate,
                instructors[section_1.instructor_id],
                sections,
                timeslots,
            ):
                continue

            candidate[section_id_1] = assignment_2

            slot_1, room_1 = assignment_1

            if not validate_section_assignment(
                section_2,
                rooms[room_1],
                timeslots[slot_1],
                candidate,
                instructors[section_2.instructor_id],
                sections,
                timeslots,
            ):
                continue

            candidate[section_id_2] = assignment_1

            feasible_moves += 1

            selected_neighbor, selected_penalty = (
                evaluate_candidate(
                    candidate,
                    [section_id_1, section_id_2],
                    iteration,
                    (
                        selected_neighbor,
                        selected_penalty,
                    ),
                )
            )

        # ----------------------------------------------------
        # 7C. Select best admissible sampled neighbor
        # ----------------------------------------------------

        if selected_neighbor is None:
            print(
                f"Iteration {iteration}: "
                "No admissible sampled move found.",
                flush=True,
            )
            break

        add_tabu_assignments(
            current_timetable,
            selected_neighbor,
            tabu_memory,
            iteration,
            tabu_tenure,
        )

        current_timetable = selected_neighbor
        current_penalty = selected_penalty

        # ----------------------------------------------------
        # 7D. Verify exact penalty calculation
        # ----------------------------------------------------

        full_penalty = calculate_total_penalty(
            current_timetable,
            sections,
            instructors,
            timeslots,
            cohort_ids,
            idle_weight,
            preference_weight,
        )

        if abs(current_penalty - full_penalty) > 1e-9:
            raise AssertionError(
                "Incremental penalty mismatch: "
                f"{current_penalty} != {full_penalty}"
            )

        # ----------------------------------------------------
        # 7E. Update best solution
        # ----------------------------------------------------

        if current_penalty < best_penalty:
            best_timetable = current_timetable.copy()
            best_penalty = current_penalty
            no_improvement = 0
        else:
            no_improvement += 1

        record_search_history(
            history,
            iteration,
            current_penalty,
            best_penalty,
        )

        print(
            f"Iteration {iteration}/{max_iterations} | "
            f"Current: {current_penalty} | "
            f"Best: {best_penalty} | "
            f"Feasible sampled moves: {feasible_moves}",
            flush=True,
        )

    print("\nTabu Search completed.", flush=True)
    print(f"Iterations executed: {iteration}")
    print(f"Best penalty: {best_penalty}")

    return best_timetable
