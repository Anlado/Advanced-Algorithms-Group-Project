
import csv
from pathlib import Path
from tempfile import TemporaryDirectory

from src.data_io.dataset_loader import (
    load_sections,
    load_rooms,
    load_timeslots,
)

from src.reporting.schedule_report import export_schedule


def run_tests():
    sections = load_sections("data/sections.csv")
    rooms = load_rooms("data/rooms.csv")
    timeslots = load_timeslots("data/timeslots.csv")

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

    with TemporaryDirectory() as directory:
        output_path = Path(directory) / "nested" / "schedule.csv"

        result = export_schedule(
            timetable, sections, rooms, timeslots, output_path
        )

        # Test A: The CSV file was created.
        assert result == output_path
        assert output_path.is_file()
        print("Test A passed: Schedule CSV created.")

        with output_path.open(newline="", encoding="utf-8") as file:
            rows = list(csv.DictReader(file))

        # Test B: Every scheduled section appears exactly once.
        assert len(rows) == len(timetable)
        assert {row["section_id"] for row in rows} == set(timetable)
        print("Test B passed: All sections exported.")

        # Test C: Course and instructor information is correct.
        first_row = rows[0]
        assert first_row["course_id"] == "CS101"
        assert first_row["instructor_id"] == "I1"
        print("Test C passed: Course and instructor exported.")

        # Test D: Timeslot and room are human-readable.
        assert first_row["day"] == "Mon"
        assert first_row["start_time"] == "10:00"
        assert first_row["end_time"] == "11:00"
        assert first_row["room"] == "ENG-R1"
        print("Test D passed: Time and room formatted correctly.")

        # Test E: The original timetable remains unchanged.
        assert timetable["S1"] == ("T2", "R1")
        print("Test E passed: Original timetable preserved.")

    print("\nAll 5 schedule-report tests passed.")


if __name__ == "__main__":
    run_tests()
