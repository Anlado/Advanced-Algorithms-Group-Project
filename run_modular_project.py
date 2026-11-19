
import json
import random
import time
from pathlib import Path

from src.data_io.dataset_loader import (
    load_instructors,
    load_rooms,
    load_sections,
    load_timeslots,
    validate_dataset,
)
from src.heuristic.initial_timetable import generate_initial_timetable
from src.heuristic.tabu_search import tabu_search
from src.model.soft_constraints import calculate_total_penalty
from src.reporting.feasibility_report import export_feasibility_report
from src.reporting.quality_curve import export_quality_curve
from src.reporting.schedule_report import export_schedule
from src.reporting.metrics_report import export_metrics
from src.reporting.feasibility_report import find_feasibility_violations


# Resolve paths relative to this script, regardless of the working directory.
PROJECT_ROOT = Path(__file__).resolve().parent


# Load the dataset and verify its basic references and suitability.
# Return the four dictionaries used throughout the timetabling system.
def load_dataset(data_directory):
    instructors = load_instructors(data_directory / "instructors.csv")
    rooms = load_rooms(data_directory / "rooms.csv")
    timeslots = load_timeslots(data_directory / "timeslots.csv")
    sections = load_sections(data_directory / "sections.csv")

    validate_dataset(sections, instructors, rooms, timeslots)

    return sections, rooms, timeslots, instructors


# Calculate the weighted soft-constraint penalty of a timetable.
# Use the same objective function for initial and optimized schedules.
def evaluate_timetable(
    timetable, sections, instructors, timeslots, cohort_ids, parameters
):
    return calculate_total_penalty(
        timetable,
        sections,
        instructors,
        timeslots,
        cohort_ids,
        parameters["idle_weight"],
        parameters["preference_weight"],
    )



# Display a human-readable university timetable.
# Resolve stored IDs into course information, day, time, room, and instructor.
# Keep the underlying timetable representation unchanged.
def display_timetable(title, timetable, sections, rooms, timeslots, instructors):
    print(f"\n{title}")
    print("-" * 92)

    print(
        f"{'Course':<12}"
        f"{'Section':<10}"
        f"{'Day':<10}"
        f"{'Time':<16}"
        f"{'Room':<14}"
        f"{'Instructor':<12}"
    )

    print("-" * 92)

    for section_id in sorted(timetable):
        timeslot_id, room_id = timetable[section_id]

        section = sections[section_id]
        timeslot = timeslots[timeslot_id]
        room = rooms[room_id]
        instructor = instructors[section.instructor_id]
        instructor_label = f"{instructor.id} - {instructor.full_name}"

        # Convert the start time into minutes since midnight.
        hour, minute = map(int, timeslot.start_time.split(":"))
        start_minutes = hour * 60 + minute

        # Calculate the ending time from the slot duration.
        end_minutes = start_minutes + timeslot.duration_min

        start_time = (
            f"{start_minutes // 60:02d}:"
            f"{start_minutes % 60:02d}"
        )
        end_time = (
            f"{end_minutes // 60:02d}:"
            f"{end_minutes % 60:02d}"
        )

        time_range = f"{start_time}-{end_time}"
        room_label = f"{room.building}-{room.id}"

        print(
            f"{section.course_id:<12}"
            f"{section.id:<10}"
            f"{timeslot.day:<10}"
            f"{time_range:<16}"
            f"{room_label:<14}"
            f"{instructor_label:<28}"
        )


# Execute the complete construction and optimization pipeline.
# Measure each phase independently and report the penalty improvement.
def run_modular_project(
    config_path=PROJECT_ROOT / "config.json",
    construction_only=False,
):
    with open(config_path, encoding="utf-8") as file:
        config = json.load(file)

    random.seed(config["random_seed"])

    data_directory = PROJECT_ROOT / config["data_directory"]
    parameters = config["tabu_search"]

    sections, rooms, timeslots, instructors = load_dataset(data_directory)

    cohort_ids = {section.cohort_id for section in sections.values()}

    print("Dataset loaded and validated.")
    print(f"Sections: {len(sections)}")
    print(f"Rooms: {len(rooms)}")
    print(f"Timeslots: {len(timeslots)}")
    print(f"Instructors: {len(instructors)}")
    print(f"Cohorts: {len(cohort_ids)}")

    # Phase 1: Construct an initial feasible timetable.
    construction_start = time.perf_counter()

    initial_timetable = generate_initial_timetable(
        sections,
        rooms,
        timeslots,
        instructors,
    )

    construction_time = time.perf_counter() - construction_start

    if initial_timetable is None:
        print("\nNo feasible initial timetable could be constructed.")
        return None
    
    # Optional: evaluate initial construction without Tabu Search.
    if construction_only:
        violations = find_feasibility_violations(
            initial_timetable,
            sections,
            rooms,
            timeslots,
            instructors,
        )

        print("\nINITIAL CONSTRUCTION RESULTS")
        print("-" * 42)
        print(f"Sections scheduled: {len(initial_timetable)} / {len(sections)}")
        print(f"Construction runtime: {construction_time:.6f} seconds")
        print(f"Hard-constraint violations: {len(violations)}")
        print(
            "Hard-constraint feasibility: "
            f"{'PASS' if not violations else 'FAIL'}"
        )

        return initial_timetable

    initial_penalty = evaluate_timetable(
        initial_timetable,
        sections,
        instructors,
        timeslots,
        cohort_ids,
        parameters,
    )

    # Phase 2: Optimize the initial timetable using Tabu Search.
    optimization_start = time.perf_counter()

    search_history = []

    best_timetable = tabu_search(
        initial_timetable,
        sections,
        rooms,
        timeslots,
        instructors,
        cohort_ids,
        parameters["idle_weight"],
        parameters["preference_weight"],
        parameters["tabu_tenure"],
        parameters["max_iterations"],
        parameters["no_improvement_max_iterations"],
        history=search_history
    )

    optimization_time = time.perf_counter() - optimization_start

    final_penalty = evaluate_timetable(
        best_timetable,
        sections,
        instructors,
        timeslots,
        cohort_ids,
        parameters,
    )

    improvement = (
        100 * (initial_penalty - final_penalty) / initial_penalty
        if initial_penalty > 0
        else 0
    )

    # Display the two timetables and measured results.
    display_timetable(
        "INITIAL TIMETABLE",
        initial_timetable,
        sections,
        rooms,
        timeslots,
        instructors,
    )

    display_timetable(
        "OPTIMIZED TIMETABLE",
        best_timetable,
        sections,
        rooms,
        timeslots,
        instructors,
    )

    # Export the optimized timetable as a human-readable CSV schedule.
    output_directory = PROJECT_ROOT / config["output_directory"]

    schedule_path = export_schedule(
        best_timetable,
        sections,
        rooms,
        timeslots,
        instructors,
        output_directory / "schedule.csv",
    )

    print(f"\nOptimized schedule exported to: {schedule_path}")

    # Verify the optimized timetable and export its feasibility report.
    feasibility_report_path = output_directory / "feasibility_report.md"

    is_feasible = export_feasibility_report(
        best_timetable,
        sections,
        rooms,
        timeslots,
        instructors,
        feasibility_report_path,
    )

    # Export the dataset, optimization, feasibility, and runtime metrics.
    metrics_path = export_metrics(
        sections=sections,
        rooms=rooms,
        timeslots=timeslots,
        instructors=instructors,
        initial_penalty=initial_penalty,
        final_penalty=final_penalty,
        is_feasible=is_feasible,
        construction_runtime=construction_time,
        optimization_runtime=optimization_time,
        output_path=output_directory / "metrics.json",
        hard_constraint_violations=len(
            find_feasibility_violations(
                best_timetable,
                sections,
                rooms,
                timeslots,
                instructors,
            )
        ),
    )

    # Export the Tabu Search optimization history as a quality curve.
    quality_curve_path = export_quality_curve(
        search_history,
        output_directory / "plots" / "quality_curve.png",
    )

    print(f"Quality curve exported to: {quality_curve_path}")

    print(f"Evaluation metrics exported to: {metrics_path}")

    print(f"Feasibility report exported to: {feasibility_report_path}")
    print(f"Hard-constraint feasibility: {'PASS' if is_feasible else 'FAIL'}")

    print("\nEVALUATION METRICS")
    print("-" * 42)
    print(f"Initial penalty:       {initial_penalty}")
    print(f"Final penalty:         {final_penalty}")
    print(f"Penalty reduction:     {initial_penalty - final_penalty}")
    print(f"Improvement:           {improvement:.2f}%")
    print(f"Construction runtime:  {construction_time:.6f} seconds")
    print(f"Optimization runtime:  {optimization_time:.6f} seconds")
    print(
        f"Total algorithm time:  "
        f"{construction_time + optimization_time:.6f} seconds"
    )

    return best_timetable


if __name__ == "__main__":
    run_modular_project()
