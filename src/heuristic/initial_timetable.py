
from collections import defaultdict
import time

from src.model.constraints import validate_section_assignment
from src.model.time_utils import time_to_minutes


# ============================================================
# FAST INITIAL TIMETABLE CONSTRUCTION
# ============================================================

def generate_initial_timetable(
    sections,
    rooms,
    timeslots,
    instructors,
):
    """
    Construct a feasible timetable using:

    - Precomputed static assignment domains
    - Occupancy indexes
    - Minimum Remaining Values (MRV)
    - Degree tie-breaking
    - Approximate Least Constraining Value (LCV)
    - Recursive backtracking

    The final timetable is checked against the original
    hard-constraint validator.
    """

    start_time = time.perf_counter()

    section_ids = list(sections.keys())
    slot_ids = list(timeslots.keys())

    timetable = {}

    # --------------------------------------------------------
    # 1. Precompute timeslot overlaps
    # --------------------------------------------------------

    overlap_map = {}

    for slot_id, slot in timeslots.items():
        start = time_to_minutes(slot.start_time)
        end = start + slot.duration_min

        overlapping = set()

        for other_id, other in timeslots.items():
            if slot.day != other.day:
                continue

            other_start = time_to_minutes(other.start_time)
            other_end = other_start + other.duration_min

            if start < other_end and other_start < end:
                overlapping.add(other_id)

        overlap_map[slot_id] = overlapping

    # --------------------------------------------------------
    # 2. Precompute static domains
    # --------------------------------------------------------

    compatible_rooms = {}
    allowed_slots = {}
    static_domain_size = {}

    for section_id, section in sections.items():
        instructor = instructors[section.instructor_id]

        if section.subject_area not in instructor.domains:
            print(
                f"Unqualified instructor for {section_id}"
            )
            return None

        section_rooms = [
            room_id
            for room_id, room in rooms.items()
            if room.capacity >= section.enrollment
            and (not section.needs_lab or room.is_lab)
        ]

        section_slots = [
            slot_id
            for slot_id in slot_ids
            if slot_id not in instructor.unavailable_slots
            and slot_id not in instructor.required_no_teach_slots
        ]

        if not section_rooms or not section_slots:
            print(
                f"No static assignments available for "
                f"{section_id}"
            )
            return None

        compatible_rooms[section_id] = section_rooms
        allowed_slots[section_id] = section_slots

        static_domain_size[section_id] = (
            len(section_rooms) * len(section_slots)
        )

    # --------------------------------------------------------
    # 3. Build conflict-neighbor indexes
    # --------------------------------------------------------

    instructor_sections = defaultdict(set)
    cohort_sections = defaultdict(set)

    for section_id, section in sections.items():
        instructor_sections[
            section.instructor_id
        ].add(section_id)

        cohort_sections[
            section.cohort_id
        ].add(section_id)

    neighbors = {}

    for section_id, section in sections.items():
        neighbors[section_id] = (
            instructor_sections[section.instructor_id]
            | cohort_sections[section.cohort_id]
        ) - {section_id}

    # --------------------------------------------------------
    # 4. Maintain occupancy indexes
    # --------------------------------------------------------

    # These sets include all timeslots that overlap an
    # assigned section, not only its exact slot ID.

    occupied_rooms = defaultdict(set)
    occupied_instructors = defaultdict(set)
    occupied_cohorts = defaultdict(set)

    def assign(section_id, slot_id, room_id):
        section = sections[section_id]

        timetable[section_id] = (slot_id, room_id)

        for overlapping_slot in overlap_map[slot_id]:
            occupied_rooms[overlapping_slot].add(room_id)

            occupied_instructors[
                overlapping_slot
            ].add(section.instructor_id)

            occupied_cohorts[
                overlapping_slot
            ].add(section.cohort_id)

    def unassign(section_id):
        section = sections[section_id]
        slot_id, room_id = timetable.pop(section_id)

        for overlapping_slot in overlap_map[slot_id]:
            occupied_rooms[overlapping_slot].remove(room_id)

            occupied_instructors[
                overlapping_slot
            ].remove(section.instructor_id)

            occupied_cohorts[
                overlapping_slot
            ].remove(section.cohort_id)

    # --------------------------------------------------------
    # 5. Fast dynamic feasibility checks
    # --------------------------------------------------------

    def slot_is_available(section_id, slot_id):
        section = sections[section_id]

        if (
            section.instructor_id
            in occupied_instructors[slot_id]
        ):
            return False

        if (
            section.cohort_id
            in occupied_cohorts[slot_id]
        ):
            return False

        return True

    def available_rooms_for(section_id, slot_id):
        if not slot_is_available(section_id, slot_id):
            return []

        occupied = occupied_rooms[slot_id]

        return [
            room_id
            for room_id in compatible_rooms[section_id]
            if room_id not in occupied
        ]

    # --------------------------------------------------------
    # 6. MRV with degree tie-breaking
    # --------------------------------------------------------

    def select_next_section():
        selected_id = None
        selected_key = None

        for section_id in section_ids:
            if section_id in timetable:
                continue

            remaining_values = 0

            for slot_id in allowed_slots[section_id]:
                if not slot_is_available(
                    section_id, slot_id
                ):
                    continue

                occupied = occupied_rooms[slot_id]

                for room_id in compatible_rooms[section_id]:
                    if room_id not in occupied:
                        remaining_values += 1

            if remaining_values == 0:
                return None, True

            unassigned_degree = sum(
                neighbor not in timetable
                for neighbor in neighbors[section_id]
            )

            # MRV: smallest domain first.
            # Degree: highest unassigned degree first.
            key = (
                remaining_values,
                -unassigned_degree,
                static_domain_size[section_id],
            )

            if selected_key is None or key < selected_key:
                selected_id = section_id
                selected_key = key

        return selected_id, False

    # --------------------------------------------------------
    # 7. Approximate Least Constraining Value
    # --------------------------------------------------------

    def order_assignments_lcv(section_id):
        section = sections[section_id]
        candidates = []

        unassigned_neighbors = [
            neighbor
            for neighbor in neighbors[section_id]
            if neighbor not in timetable
        ]

        for slot_id in allowed_slots[section_id]:
            available_rooms = available_rooms_for(
                section_id, slot_id
            )

            if not available_rooms:
                continue

            # Estimate how many related sections would
            # lose this timeslot.
            neighbor_impact = 0

            for neighbor_id in unassigned_neighbors:
                if any(
                    candidate_slot in overlap_map[slot_id]
                    for candidate_slot
                    in allowed_slots[neighbor_id]
                ):
                    neighbor_impact += 1

            # Prefer rooms that are less useful to other
            # sections, preserving scarce room capacity.
            for room_id in available_rooms:
                room = rooms[room_id]

                room_flexibility = sum(
                    room_id in compatible_rooms[other_id]
                    for other_id in section_ids
                    if other_id not in timetable
                    and other_id != section_id
                )

                score = (
                    neighbor_impact,
                    room_flexibility,
                    room.capacity - section.enrollment,
                )

                candidates.append(
                    (score, slot_id, room_id)
                )

        candidates.sort(key=lambda item: item[0])

        return [
            (slot_id, room_id)
            for _, slot_id, room_id in candidates
        ]

    # --------------------------------------------------------
    # 8. Backtracking
    # --------------------------------------------------------

    nodes_visited = 0
    deepest_assignment = 0

    def backtrack():
        nonlocal nodes_visited, deepest_assignment

        if len(timetable) == len(sections):
            return True

        nodes_visited += 1

        selected_id, dead_end = select_next_section()

        if dead_end or selected_id is None:
            return False

        assignments = order_assignments_lcv(
            selected_id
        )

        for slot_id, room_id in assignments:
            assign(selected_id, slot_id, room_id)

            if len(timetable) > deepest_assignment:
                deepest_assignment = len(timetable)

                if deepest_assignment % 25 == 0:
                    elapsed = (
                        time.perf_counter() - start_time
                    )

                    print(
                        f"Scheduled "
                        f"{deepest_assignment}/{len(sections)} "
                        f"sections | "
                        f"{elapsed:.2f}s elapsed",
                        flush=True,
                    )

            if backtrack():
                return True

            unassign(selected_id)

        return False

    # --------------------------------------------------------
    # 9. Execute construction
    # --------------------------------------------------------

    print(
        "\nConstructing initial university timetable...",
        flush=True,
    )

    success = backtrack()

    elapsed = time.perf_counter() - start_time

    if not success:
        print(
            "\nUnable to construct a feasible timetable."
        )
        print(f"Search nodes visited: {nodes_visited}")
        print(f"Runtime: {elapsed:.2f}s")
        return None

    # --------------------------------------------------------
    # 10. Verify against original hard constraints
    # --------------------------------------------------------

    # Rebuild the schedule incrementally to validate each
    # assignment without including the section itself.

    verified_timetable = {}

    for section_id, assignment in timetable.items():
        slot_id, room_id = assignment
        section = sections[section_id]

        is_valid = validate_section_assignment(
            section,
            rooms[room_id],
            timeslots[slot_id],
            verified_timetable,
            instructors[section.instructor_id],
            sections,
            timeslots,
        )

        if not is_valid:
            raise RuntimeError(
                f"Hard-constraint validation failed "
                f"for section {section_id}"
            )

        verified_timetable[section_id] = assignment

    print("\nInitial timetable constructed.")
    print(f"Sections scheduled: {len(timetable)}")
    print(f"Search nodes visited: {nodes_visited}")
    print(f"Construction runtime: {elapsed:.2f}s")
    print("Original hard-constraint validation: PASS")

    return timetable


# ============================================================
# ORIGINAL PUBLIC HEURISTIC HELPERS
# Retained for compatibility with existing tests and callers.
# The optimized university-scale constructor uses its own
# indexed MRV and approximate LCV implementations.
# ============================================================

def get_valid_assignments(
    section,
    rooms,
    timeslots,
    timetable,
    instructors,
    sections,
):
    assignments = []

    for timeslot in timeslots.values():
        for room in rooms.values():
            if validate_section_assignment(
                section,
                room,
                timeslot,
                timetable,
                instructors[section.instructor_id],
                sections,
                timeslots,
            ):
                assignments.append((timeslot.id, room.id))

    return assignments


def getUnassignedDegree(section, sections, timetable):
    degree = 0

    for other_id, other_section in sections.items():
        if other_id == section.id or other_id in timetable:
            continue

        if (
            other_section.instructor_id == section.instructor_id
            or other_section.cohort_id == section.cohort_id
        ):
            degree += 1

    return degree


def select_section_mrv(
    sections,
    rooms,
    timeslots,
    timetable,
    instructors,
):
    selected_section = None
    selected_assignments = []
    selected_key = None

    for section_id, section in sections.items():
        if section_id in timetable:
            continue

        assignments = get_valid_assignments(
            section,
            rooms,
            timeslots,
            timetable,
            instructors,
            sections,
        )

        degree = getUnassignedDegree(
            section,
            sections,
            timetable,
        )

        key = (len(assignments), -degree)

        if selected_key is None or key < selected_key:
            selected_key = key
            selected_section = section
            selected_assignments = assignments

    return selected_section, selected_assignments


def order_assignments_lcv(
    section,
    valid_assignments,
    sections,
    rooms,
    timeslots,
    timetable,
    instructors,
):
    scored_assignments = []

    for assignment in valid_assignments:
        candidate = timetable.copy()
        candidate[section.id] = assignment

        remaining_options = 0
        dead_end = False

        for other_id, other_section in sections.items():
            if other_id in candidate:
                continue

            options = get_valid_assignments(
                other_section,
                rooms,
                timeslots,
                candidate,
                instructors,
                sections,
            )

            if not options:
                dead_end = True
                break

            remaining_options += len(options)

        scored_assignments.append(
            (
                (dead_end, -remaining_options),
                assignment,
            )
        )

    scored_assignments.sort(key=lambda item: item[0])

    return [
        assignment
        for _, assignment in scored_assignments
    ]
