from pathlib import Path

from src.model.time_utils import timeslots_overlap


# Check the timetable against the project's hard constraints.
# Return a list describing every detected violation.
# An empty list means the timetable is feasible.
def find_feasibility_violations(
    timetable, sections, rooms, timeslots, instructors
):
    violations = []

    # Check for assignments to sections that do not exist.
    for section_id in timetable:
        if section_id not in sections:
            violations.append(
                f"Unknown section {section_id} appears in the timetable."
            )

    valid_assignments = {}

    # Check each section's assignment and individual constraints.
    for section_id, section in sections.items():
        if section_id not in timetable:
            violations.append(f"Section {section_id} is not scheduled.")
            continue

        assignment = timetable[section_id]

        if not isinstance(assignment, (tuple, list)) or len(assignment) != 2:
            violations.append(
                f"Section {section_id} has an invalid assignment format."
            )
            continue

        timeslot_id, room_id = assignment

        if timeslot_id not in timeslots:
            violations.append(
                f"Section {section_id} references unknown timeslot {timeslot_id}."
            )

        if room_id not in rooms:
            violations.append(
                f"Section {section_id} references unknown room {room_id}."
            )

        if section.instructor_id not in instructors:
            violations.append(
                f"Section {section_id} references unknown instructor "
                f"{section.instructor_id}."
            )

        if (
            timeslot_id not in timeslots
            or room_id not in rooms
            or section.instructor_id not in instructors
        ):
            continue

        room = rooms[room_id]
        timeslot = timeslots[timeslot_id]
        instructor = instructors[section.instructor_id]

        valid_assignments[section_id] = (timeslot_id, room_id)

        # Check room capacity.
        if section.enrollment > room.capacity:
            violations.append(
                f"Section {section_id}: enrollment {section.enrollment} "
                f"exceeds room {room_id} capacity {room.capacity}."
            )

        # Check laboratory requirements.
        if section.needs_lab and not room.is_lab:
            violations.append(
                f"Section {section_id} requires a lab, "
                f"but room {room_id} is not a lab."
            )

        # Check instructor availability.
        if timeslot.id in instructor.unavailable_slots:
            violations.append(
                f"Section {section_id}: instructor {instructor.id} "
                f"is unavailable during {timeslot_id}."
            )

        if timeslot.id in instructor.required_no_teach_slots:
            violations.append(
                f"Section {section_id}: instructor {instructor.id} "
                f"cannot teach during required no-teach slot {timeslot_id}."
            )

        # Check instructor qualifications.
        if section.subject_area not in instructor.domains:
            violations.append(
                f"Section {section_id}: instructor {instructor.id} "
                f"is not qualified for {section.subject_area}."
            )

    # Check conflicts between distinct scheduled sections.
    # Each pair is examined only once to avoid duplicate reports.
    section_ids = list(valid_assignments)

    for i in range(len(section_ids) - 1):
        for j in range(i + 1, len(section_ids)):
            first_id = section_ids[i]
            second_id = section_ids[j]

            first = sections[first_id]
            second = sections[second_id]

            first_timeslot_id, first_room_id = valid_assignments[first_id]
            second_timeslot_id, second_room_id = valid_assignments[second_id]

            first_timeslot = timeslots[first_timeslot_id]
            second_timeslot = timeslots[second_timeslot_id]

            if not timeslots_overlap(first_timeslot, second_timeslot):
                continue

            if first_room_id == second_room_id:
                violations.append(
                    f"Room conflict: sections {first_id} and {second_id} "
                    f"overlap in room {first_room_id}."
                )

            if first.instructor_id == second.instructor_id:
                violations.append(
                    f"Instructor conflict: sections {first_id} and "
                    f"{second_id} overlap for instructor "
                    f"{first.instructor_id}."
                )

            if first.cohort_id == second.cohort_id:
                violations.append(
                    f"Cohort conflict: sections {first_id} and "
                    f"{second_id} overlap for cohort {first.cohort_id}."
                )

    return violations


# Generate a Markdown report describing timetable feasibility.
# Create the output directory if necessary.
# Return True when the timetable satisfies all hard constraints.
def export_feasibility_report(
    timetable, sections, rooms, timeslots, instructors, output_path
):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    violations = find_feasibility_violations(
        timetable, sections, rooms, timeslots, instructors
    )

    scheduled_count = sum(
        section_id in timetable for section_id in sections
    )
    unscheduled_count = len(sections) - scheduled_count

    feasible = len(violations) == 0
    status = "PASS" if feasible else "FAIL"

    lines = [
        "# Timetable Feasibility Report",
        "",
        "## Dataset Summary",
        "",
        f"- Sections: {len(sections)}",
        f"- Rooms: {len(rooms)}",
        f"- Timeslots: {len(timeslots)}",
        f"- Instructors: {len(instructors)}",
        "",
        "## Schedule Completeness",
        "",
        f"- Scheduled sections: {scheduled_count}",
        f"- Unscheduled sections: {unscheduled_count}",
        "",
        "## Hard Constraint Verification",
        "",
        f"- Overall status: **{status}**",
        f"- Violations detected: {len(violations)}",
        "",
        "Constraints checked:",
        "",
        "- Room capacity",
        "- Laboratory requirements",
        "- Instructor availability and required no-teach slots",
        "- Instructor qualifications",
        "- Room scheduling conflicts",
        "- Instructor scheduling conflicts",
        "- Cohort scheduling conflicts",
        "- Missing and invalid assignments",
        "",
        "## Violation Details",
        "",
    ]

    if feasible:
        lines.append(
            "No hard-constraint violations detected. "
            "The timetable is feasible under the implemented constraints."
        )
    else:
        for index, violation in enumerate(violations, start=1):
            lines.append(f"{index}. {violation}")

    lines.append("")

    output_path.write_text("\n".join(lines), encoding="utf-8")

    return feasible
