from pathlib import Path
from tempfile import TemporaryDirectory

from src.data_io.dataset_loader import (
    load_sections,
    load_rooms,
    load_timeslots,
    load_instructors,
)
from src.reporting.feasibility_report import (
    find_feasibility_violations,
    export_feasibility_report,
)


def run_tests():
    data_dir = Path("data")

    sections = load_sections(data_dir / "sections.csv")
    rooms = load_rooms(data_dir / "rooms.csv")
    timeslots = load_timeslots(data_dir / "timeslots.csv")
    instructors = load_instructors(data_dir / "instructors.csv")

    # Construct a known feasible timetable for the sample dataset.
    timetable = {
        "S1": ("T2", "R1"),
        "S2": ("T1", "R2"),
        "S3": ("T1", "R3"),
        "S4": ("T3", "R1"),
        "S5": ("T6", "R4"),
        "S6": ("T6", "R1"),
        "S7": ("T1", "R1"),
        "S8": ("T6", "R2"),
    }

    # Test A: The known feasible timetable has no violations.
    violations = find_feasibility_violations(
        timetable, sections, rooms, timeslots, instructors
    )
    assert violations == [], violations
    print("Test A passed: Feasible timetable accepted.")

    # Test B: A missing section is detected.
    incomplete = timetable.copy()
    del incomplete["S8"]

    violations = find_feasibility_violations(
        incomplete, sections, rooms, timeslots, instructors
    )
    assert any("not scheduled" in item for item in violations)
    print("Test B passed: Missing section detected.")

    # Test C: An invalid room reference is detected.
    invalid_room = timetable.copy()
    invalid_room["S1"] = ("T2", "UNKNOWN")

    violations = find_feasibility_violations(
        invalid_room, sections, rooms, timeslots, instructors
    )
    assert any("unknown room" in item for item in violations)
    print("Test C passed: Unknown room detected.")

    # Test D: A room collision is detected.
    collision = timetable.copy()
    collision["S2"] = ("T2", "R1")

    violations = find_feasibility_violations(
        collision, sections, rooms, timeslots, instructors
    )
    assert any("Room conflict" in item for item in violations)
    print("Test D passed: Room conflict detected.")

    # Test E: A room-capacity violation is detected.
    insufficient_capacity = timetable.copy()
    insufficient_capacity["S5"] = ("T6", "R1")

    violations = find_feasibility_violations(
        insufficient_capacity, sections, rooms, timeslots, instructors
    )
    assert any("exceeds" in item for item in violations)
    print("Test E passed: Capacity violation detected.")

    # Test F: A valid Markdown report is created.
    with TemporaryDirectory() as temp_dir:
        report_path = Path(temp_dir) / "out" / "feasibility_report.md"

        feasible = export_feasibility_report(
            timetable,
            sections,
            rooms,
            timeslots,
            instructors,
            report_path,
        )

        assert feasible
        assert report_path.exists()

        content = report_path.read_text(encoding="utf-8")
        assert "Overall status: **PASS**" in content
        assert "Violations detected: 0" in content

        print("Test F passed: Feasible report exported.")

        # Test G: An invalid timetable produces a FAIL report.
        feasible = export_feasibility_report(
            collision,
            sections,
            rooms,
            timeslots,
            instructors,
            report_path,
        )

        assert not feasible

        content = report_path.read_text(encoding="utf-8")
        assert "Overall status: **FAIL**" in content
        assert "Room conflict" in content

        print("Test G passed: Infeasible report exported.")

    print("\nAll 7 feasibility-report tests passed.")


if __name__ == "__main__":
    run_tests()
